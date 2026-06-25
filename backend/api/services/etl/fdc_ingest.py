"""USDA FoodData Central ETL ingest (FDC-INGEST, 2026-06-25).

Reads three FDC bulk-download datasets sitting on disk and appends them
into the in-memory CNF DataFrames, in the same shape as
[`wafct_ingest.py`](backend/api/services/etl/wafct_ingest.py) (2026-05-24):

  - Foundation Foods (~395 finished foods)  → FoodIDs 800,000+
  - SR Legacy (~7,793 foods)                → FoodIDs 810,000+
  - Survey FNDDS (~5,432 foods)             → FoodIDs 820,000+
  - All three carry `source='fdc'` on `food_name_df`; the more specific
    `data_type` column (added by this ingest) distinguishes the three
    sub-sources for downstream filtering.

FDC nutrient bridge: FDC's `nutrient.nutrient_nbr` aligns with CNF
`NutrientID` numerically (both inherit USDA's nutrient numbering). For
Foundation and SR Legacy, `food_nutrient.nutrient_id` is the FDC `id`
(1001-2069) and we hop through `nutrient.csv` to recover the
`nutrient_nbr`. For FNDDS, `food_nutrient.nutrient_id` is ALREADY the
`nutrient_nbr` (legacy from pre-FDC FNDDS); we use it directly. The
probe at [`backend/_explore_fdc_nutrient_bridge.py`](backend/_explore_fdc_nutrient_bridge.py)
documents both paths and reports ~96 % row coverage overall.

Foundation's `food.csv` carries ~88 k rows of sample / market-acquisition
/ sub-sample provenance interleaved with the 395 finished foods; we
filter by membership in `foundation_food.csv` to keep only the published
finished items.

Called once per process from [`api.cnf_cache.get_api_cnf_pipeline()`](backend/api/cnf_cache.py)
right after the WAFCT ingest. Graceful degrade: if any of the three FDC
folders is missing the ingest is a no-op for that source.

Performance: ~3 s wall-clock cold (1.17 M food_nutrient rows across the
three datasets parsed via pandas, then filtered to ~1.12 M bridged
rows).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# --- Constants (allocations are deliberately distant from CNF + WAFCT) ----

FDC_FOUNDATION_OFFSET             = 800_000
FDC_SR_LEGACY_OFFSET              = 810_000
FDC_FNDDS_OFFSET                  = 820_000

FDC_FOOD_SOURCE_ID                = 101    # CNF max 38, WAFCT uses 100

FDC_FOUNDATION_NUTRIENT_SOURCE_ID = 10000  # WAFCT uses 9999
FDC_SR_LEGACY_NUTRIENT_SOURCE_ID  = 10001
FDC_FNDDS_NUTRIENT_SOURCE_ID      = 10002

# FoodGroupID allocation: CNF uses 1-25, WAFCT uses 50-63.
# - Foundation+SR Legacy share USDA's food_category table (28 entries)
#   → IDs 70-97
# - FNDDS uses WWEIA category numbers (~165 codes)
#   → IDs 100-264 (allocated sequentially from sorted WWEIA list)
FDC_LEGACY_FOOD_GROUP_BASE        = 70
FDC_FNDDS_FOOD_GROUP_BASE         = 100

FDC_COUNTRY_CODE                  = 'US'

# Subdirectory layout under backend/ (set after the 2026-06-25 folder move).
FOUNDATION_SUBDIR = 'raw_fdc_foundation/FoodData_Central_foundation_food_csv_2026-04-30'
SR_LEGACY_SUBDIR  = 'raw_fdc_sr_legacy/FoodData_Central_sr_legacy_food_csv_2018-04'
FNDDS_SUBDIR      = 'raw_fndds/FoodData_Central_survey_food_csv_2024-10-31'

CNF_MAX_FOOD_ID_GUARD = 790_000   # if CNF ever grows past this, raise our offsets


# --- Result payload ------------------------------------------------------

@dataclass
class FDCIngestResult:
    food_name_rows:       pd.DataFrame
    nutrient_amount_rows: pd.DataFrame
    food_group_rows:      pd.DataFrame
    food_source_row:      pd.DataFrame
    nutrient_source_rows: pd.DataFrame
    bridge_by_dataset:    Dict[str, Dict[int, int]] = field(default_factory=dict)
    dropped_nutrients:    Dict[str, List[int]]      = field(default_factory=dict)
    stats:                Dict[str, Any]            = field(default_factory=dict)

    @property
    def food_count(self) -> int:
        return len(self.food_name_rows)


# --- Path resolution ------------------------------------------------------

def _backend_dir() -> Path:
    """Resolve backend/ from settings or this file's location."""
    try:
        from django.conf import settings
        bd = Path(settings.BASE_DIR)
        if bd.exists():
            return bd
    except Exception:  # noqa: BLE001 — settings may not be configured for one-off scripts
        pass
    # Fallback: .../backend/api/services/etl/fdc_ingest.py → backend/
    return Path(__file__).resolve().parents[3]


def _dataset_dir(subdir: str) -> Path:
    return _backend_dir() / subdir


def data_present() -> Dict[str, bool]:
    """Per-dataset existence check. Lets the caller log which sub-sources
    are missing without preventing partial ingest."""
    return {
        'foundation': (_dataset_dir(FOUNDATION_SUBDIR) / 'food.csv').exists(),
        'sr_legacy':  (_dataset_dir(SR_LEGACY_SUBDIR)  / 'food.csv').exists(),
        'fndds':      (_dataset_dir(FNDDS_SUBDIR)      / 'food.csv').exists(),
    }


def any_data_present() -> bool:
    return any(data_present().values())


# --- Nutrient bridge ------------------------------------------------------

def _build_fdc_nutrient_bridge(
    dataset_dir: Path,
    cnf_nutrient_ids: set[int],
) -> Tuple[Dict[int, int], Dict[int, int]]:
    """Build two bridge dicts from a single FDC dataset's nutrient.csv:

      - by_id:   FDC `id` (1001-2069)   → CNF NutrientID  (Foundation, SR Legacy)
      - by_nbr:  FDC `nutrient_nbr` int → CNF NutrientID  (FNDDS)

    Both use the same underlying rule: `int(nutrient_nbr)` must be present
    in the CNF NutrientID set. Non-integer subcategory variants (e.g.
    293.1, 269.3, 338.1) are dropped — their integer parents are bridged
    and downstream scorers don't consume the sub-decompositions.
    """
    nut = pd.read_csv(dataset_dir / 'nutrient.csv', dtype=str, keep_default_na=False)
    by_id: Dict[int, int] = {}
    by_nbr: Dict[int, int] = {}
    for _, row in nut.iterrows():
        try:
            fdc_id = int(row['id'])
        except (TypeError, ValueError):
            continue
        nbr_str = str(row.get('nutrient_nbr', '') or '').strip()
        if not nbr_str:
            continue
        try:
            nbr_float = float(nbr_str)
        except ValueError:
            continue
        nbr_int = int(nbr_float)
        if abs(nbr_float - nbr_int) > 1e-9:
            continue  # subcategory variant (e.g. 293.1) — drop
        if nbr_int not in cnf_nutrient_ids:
            continue
        by_id[fdc_id] = nbr_int
        by_nbr[nbr_int] = nbr_int
    return by_id, by_nbr


# --- Per-dataset ingestion ------------------------------------------------

def _ingest_one(
    dataset_name: str,
    dataset_dir: Path,
    food_id_offset: int,
    nutrient_source_id: int,
    food_group_id_by_native: Dict[int, int],
    cnf_nutrient_ids: set[int],
    today: datetime,
    fk_system: str,                    # 'fdc_id' (Foundation, SR Legacy) or 'nutrient_nbr' (FNDDS)
    food_filter_fdc_ids: Optional[set[int]] = None,  # Foundation: restrict to foundation_food.csv membership
    food_code_prefix: str = 'FDC_',
    foodcode_from_col: Optional[str] = None,   # FNDDS: 'food_code' column from survey_fndds_food.csv
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[int, int], List[int], Dict[str, Any]]:
    """Ingest a single FDC dataset → (food_name_rows, nutrient_amount_rows,
    bridge_used, dropped_nutrient_ids, stats)."""
    food_csv = pd.read_csv(dataset_dir / 'food.csv', dtype=str)
    food_csv['fdc_id_int'] = pd.to_numeric(food_csv['fdc_id'], errors='coerce').astype('Int64')

    if food_filter_fdc_ids is not None:
        food_csv = food_csv[food_csv['fdc_id_int'].isin(food_filter_fdc_ids)].copy()

    if foodcode_from_col is not None:
        # FNDDS: join survey_fndds_food.csv to pull in the FNDDS 8-digit food_code.
        survey = pd.read_csv(dataset_dir / 'survey_fndds_food.csv', dtype=str)
        survey['fdc_id_int'] = pd.to_numeric(survey['fdc_id'], errors='coerce').astype('Int64')
        food_csv = food_csv.merge(
            survey[['fdc_id_int', foodcode_from_col]],
            on='fdc_id_int', how='left',
        )

    bridge_by_id, bridge_by_nbr = _build_fdc_nutrient_bridge(dataset_dir, cnf_nutrient_ids)
    bridge_used = bridge_by_nbr if fk_system == 'nutrient_nbr' else bridge_by_id

    # Allocate ecodish365 FoodIDs deterministically by sorted fdc_id.
    food_csv = food_csv.dropna(subset=['fdc_id_int']).sort_values('fdc_id_int').reset_index(drop=True)
    food_csv['ecodish_food_id'] = food_csv.index + food_id_offset

    food_name_records = []
    for _, r in food_csv.iterrows():
        fdc_id_val = int(r['fdc_id_int'])
        food_id = int(r['ecodish_food_id'])
        native_cat = pd.to_numeric(r.get('food_category_id'), errors='coerce')
        fg_id = food_group_id_by_native.get(int(native_cat)) if pd.notna(native_cat) else None
        if foodcode_from_col is not None and pd.notna(r.get(foodcode_from_col)):
            food_code = f'{food_code_prefix}{r[foodcode_from_col]}'
        else:
            food_code = f'{food_code_prefix}{fdc_id_val}'
        food_name_records.append({
            'FoodID':                food_id,
            'FoodCode':              food_code,
            'FoodGroupID':           fg_id,
            'FoodSourceID':          FDC_FOOD_SOURCE_ID,
            'FoodDescription':       r.get('description', '') or '',
            'FoodDescriptionF':      '',  # FDC ships English only
            'FoodDateOfEntry':       today,
            'FoodDateOfPublication': r.get('publication_date') or today,
            'CountryCode':           FDC_COUNTRY_CODE,
            'ScientificName':        '',
            'source':                'fdc',
            'data_type':             dataset_name,
            'fdc_id':                fdc_id_val,
        })
    food_name_df = pd.DataFrame(food_name_records)

    # Stream food_nutrient.csv (largest file). Pandas read_csv with usecols
    # keeps memory bounded; we filter by bridge membership immediately.
    fn = pd.read_csv(
        dataset_dir / 'food_nutrient.csv',
        usecols=['fdc_id', 'nutrient_id', 'amount'],
        dtype={'fdc_id': 'Int64', 'nutrient_id': 'Int64', 'amount': 'float64'},
    )
    fn = fn.dropna(subset=['fdc_id', 'nutrient_id', 'amount'])
    fn['nutrient_id'] = fn['nutrient_id'].astype(int)
    fn['fdc_id'] = fn['fdc_id'].astype(int)

    # Filter to bridged nutrients only.
    fn['cnf_nutrient_id'] = fn['nutrient_id'].map(bridge_used)
    bridged_rows_total = len(fn)
    fn = fn.dropna(subset=['cnf_nutrient_id'])
    fn['cnf_nutrient_id'] = fn['cnf_nutrient_id'].astype(int)
    bridged_rows_kept = len(fn)
    dropped_nutrient_ids = sorted({
        int(nid) for nid in pd.read_csv(
            dataset_dir / 'food_nutrient.csv',
            usecols=['nutrient_id'],
            dtype={'nutrient_id': 'Int64'},
        )['nutrient_id'].dropna().astype(int).unique()
        if int(nid) not in bridge_used
    })

    # Join the FDC fdc_id → ecodish FoodID so we attach to the right row.
    fdc_to_food_id = dict(zip(food_csv['fdc_id_int'].astype(int), food_csv['ecodish_food_id']))
    fn = fn[fn['fdc_id'].isin(fdc_to_food_id)]
    fn['FoodID'] = fn['fdc_id'].map(fdc_to_food_id).astype(int)

    nutrient_amount_records = pd.DataFrame({
        'FoodID':               fn['FoodID'],
        'NutrientID':           fn['cnf_nutrient_id'].astype(int),
        'NutrientValue':        fn['amount'].astype(float),
        'StandardError':        None,
        'NumberofObservations': None,
        'NutrientSourceID':     nutrient_source_id,
        'NutrientDateOfEntry':  today,
    })

    stats = {
        'foods_emitted':                int(len(food_name_df)),
        'food_nutrient_rows_total':     int(bridged_rows_total),
        'food_nutrient_rows_kept':      int(bridged_rows_kept),
        'food_nutrient_rows_dropped':   int(bridged_rows_total - bridged_rows_kept),
        'bridge_size':                  int(len(bridge_used)),
        'food_id_min':                  int(food_name_df['FoodID'].min()) if not food_name_df.empty else None,
        'food_id_max':                  int(food_name_df['FoodID'].max()) if not food_name_df.empty else None,
    }
    logger.info('FDC ingest [%s]: %s', dataset_name, stats)

    return food_name_df, nutrient_amount_records, bridge_used, dropped_nutrient_ids, stats


# --- Food-group plumbing --------------------------------------------------

def _build_legacy_food_group_rows(
    dataset_dir: Path,
) -> Tuple[pd.DataFrame, Dict[int, int]]:
    """Foundation + SR Legacy share food_category.csv (id, code, description).
    Allocate ecodish365 FoodGroupIDs at FDC_LEGACY_FOOD_GROUP_BASE."""
    fc = pd.read_csv(dataset_dir / 'food_category.csv', dtype=str)
    fc['id_int'] = pd.to_numeric(fc['id'], errors='coerce').astype('Int64')
    fc = fc.dropna(subset=['id_int']).sort_values('id_int').reset_index(drop=True)

    native_to_ecodish: Dict[int, int] = {}
    rows = []
    for i, r in fc.iterrows():
        native_id = int(r['id_int'])
        new_id = FDC_LEGACY_FOOD_GROUP_BASE + i
        native_to_ecodish[native_id] = new_id
        rows.append({
            'FoodGroupID':    new_id,
            'FoodGroupCode':  f'FDC_{r.get("code", str(native_id))}',
            'FoodGroupName':  f'FDC — {r.get("description", "")}',
            'FoodGroupNameF': '',
        })
    return pd.DataFrame(rows), native_to_ecodish


def _build_fndds_food_group_rows(
    dataset_dir: Path,
) -> Tuple[pd.DataFrame, Dict[int, int]]:
    """FNDDS uses WWEIA categories (wweia_food_category.csv). Allocate
    FoodGroupIDs starting at FDC_FNDDS_FOOD_GROUP_BASE."""
    wf = pd.read_csv(dataset_dir / 'wweia_food_category.csv', dtype=str)
    # Column names vary slightly across releases; normalise.
    code_col = next((c for c in wf.columns if 'category_number' in c.lower() or c.lower() == 'wweia_food_category'), None)
    name_col = next((c for c in wf.columns if 'category_description' in c.lower() or c.lower() == 'wweia_food_category_description'), None)
    if code_col is None or name_col is None:
        # Fall back to positional (FNDDS 2024-10-31 release shape:
        # wweia_food_category, wweia_food_category_description).
        cols = list(wf.columns)
        code_col, name_col = cols[0], cols[1]
    wf['code_int'] = pd.to_numeric(wf[code_col], errors='coerce').astype('Int64')
    wf = wf.dropna(subset=['code_int']).sort_values('code_int').reset_index(drop=True)

    native_to_ecodish: Dict[int, int] = {}
    rows = []
    for i, r in wf.iterrows():
        native_id = int(r['code_int'])
        new_id = FDC_FNDDS_FOOD_GROUP_BASE + i
        native_to_ecodish[native_id] = new_id
        rows.append({
            'FoodGroupID':    new_id,
            'FoodGroupCode':  f'FDC_WWEIA_{native_id}',
            'FoodGroupName':  f'FDC FNDDS — {r.get(name_col, "") or ""}',
            'FoodGroupNameF': '',
        })
    return pd.DataFrame(rows), native_to_ecodish


# --- Main entry point -----------------------------------------------------

def ingest_fdc(cnf_pipeline) -> FDCIngestResult:
    """Read all three FDC datasets present on disk and produce
    appendable DataFrames keyed for the CNF schema. Missing datasets are
    silently skipped (warning-logged)."""
    present = data_present()
    if not any(present.values()):
        raise FileNotFoundError('No FDC datasets found on disk')

    cnf_max = int(cnf_pipeline.food_name_df['FoodID'].max())
    if cnf_max >= CNF_MAX_FOOD_ID_GUARD:
        raise RuntimeError(
            f'CNF max FoodID ({cnf_max}) approaches FDC offset region. '
            f'Raise FDC_*_OFFSET above {cnf_max + 50_000} before continuing.'
        )

    today = datetime.today()
    cnf_nutrient_ids: set[int] = set(
        int(x) for x in cnf_pipeline.nutrient_name_df['NutrientID'].dropna().astype(int).tolist()
    )

    food_name_chunks: List[pd.DataFrame] = []
    nutrient_amount_chunks: List[pd.DataFrame] = []
    food_group_chunks: List[pd.DataFrame] = []
    bridges: Dict[str, Dict[int, int]] = {}
    dropped: Dict[str, List[int]] = {}
    per_dataset_stats: Dict[str, Dict[str, Any]] = {}

    # === Foundation Foods ===
    if present['foundation']:
        ddir = _dataset_dir(FOUNDATION_SUBDIR)
        # Filter food.csv to fdc_ids present in foundation_food.csv (the
        # ~395 finished foods; the other ~88 k rows are sample / sub-
        # sample / market-acquisition provenance).
        ff = pd.read_csv(ddir / 'foundation_food.csv', dtype=str)
        finished_ids = set(pd.to_numeric(ff['fdc_id'], errors='coerce').dropna().astype(int).tolist())
        # Build (or reuse) Foundation+SR-Legacy shared FoodGroup mapping.
        fg_rows, legacy_native_to_ecodish = _build_legacy_food_group_rows(ddir)
        food_group_chunks.append(fg_rows)
        fn_df, na_df, br, dr, st = _ingest_one(
            dataset_name='foundation_food',
            dataset_dir=ddir,
            food_id_offset=FDC_FOUNDATION_OFFSET,
            nutrient_source_id=FDC_FOUNDATION_NUTRIENT_SOURCE_ID,
            food_group_id_by_native=legacy_native_to_ecodish,
            cnf_nutrient_ids=cnf_nutrient_ids,
            today=today,
            fk_system='fdc_id',
            food_filter_fdc_ids=finished_ids,
            food_code_prefix='FDC_FND_',
        )
        food_name_chunks.append(fn_df)
        nutrient_amount_chunks.append(na_df)
        bridges['foundation_food'] = br
        dropped['foundation_food'] = dr
        per_dataset_stats['foundation_food'] = st
    else:
        logger.info('FDC Foundation dataset not present; skipping')
        legacy_native_to_ecodish = {}

    # === SR Legacy ===
    if present['sr_legacy']:
        ddir = _dataset_dir(SR_LEGACY_SUBDIR)
        # SR Legacy shares food_category.csv with Foundation. If Foundation
        # already built the mapping, reuse it; otherwise build from SR Legacy.
        if not legacy_native_to_ecodish:
            fg_rows, legacy_native_to_ecodish = _build_legacy_food_group_rows(ddir)
            food_group_chunks.append(fg_rows)
        fn_df, na_df, br, dr, st = _ingest_one(
            dataset_name='sr_legacy_food',
            dataset_dir=ddir,
            food_id_offset=FDC_SR_LEGACY_OFFSET,
            nutrient_source_id=FDC_SR_LEGACY_NUTRIENT_SOURCE_ID,
            food_group_id_by_native=legacy_native_to_ecodish,
            cnf_nutrient_ids=cnf_nutrient_ids,
            today=today,
            fk_system='fdc_id',
            food_filter_fdc_ids=None,
            food_code_prefix='FDC_SR_',
        )
        food_name_chunks.append(fn_df)
        nutrient_amount_chunks.append(na_df)
        bridges['sr_legacy_food'] = br
        dropped['sr_legacy_food'] = dr
        per_dataset_stats['sr_legacy_food'] = st
    else:
        logger.info('FDC SR Legacy dataset not present; skipping')

    # === FNDDS ===
    if present['fndds']:
        ddir = _dataset_dir(FNDDS_SUBDIR)
        fg_rows, fndds_native_to_ecodish = _build_fndds_food_group_rows(ddir)
        food_group_chunks.append(fg_rows)
        fn_df, na_df, br, dr, st = _ingest_one(
            dataset_name='survey_fndds_food',
            dataset_dir=ddir,
            food_id_offset=FDC_FNDDS_OFFSET,
            nutrient_source_id=FDC_FNDDS_NUTRIENT_SOURCE_ID,
            food_group_id_by_native=fndds_native_to_ecodish,
            cnf_nutrient_ids=cnf_nutrient_ids,
            today=today,
            fk_system='nutrient_nbr',
            food_filter_fdc_ids=None,
            food_code_prefix='FDC_FNDDS_',
            foodcode_from_col='food_code',
        )
        food_name_chunks.append(fn_df)
        nutrient_amount_chunks.append(na_df)
        bridges['survey_fndds_food'] = br
        dropped['survey_fndds_food'] = dr
        per_dataset_stats['survey_fndds_food'] = st
    else:
        logger.info('FDC FNDDS dataset not present; skipping')

    food_name_df       = pd.concat(food_name_chunks, ignore_index=True) if food_name_chunks else pd.DataFrame()
    nutrient_amount_df = pd.concat(nutrient_amount_chunks, ignore_index=True) if nutrient_amount_chunks else pd.DataFrame()
    food_group_df      = pd.concat(food_group_chunks, ignore_index=True) if food_group_chunks else pd.DataFrame()

    food_source_row = pd.DataFrame([{
        'FoodSourceID':            FDC_FOOD_SOURCE_ID,
        'FoodSourceCode':          'FDC',
        'FoodSourceDescription':   'USDA FoodData Central (Foundation, SR Legacy, FNDDS)',
        'FoodSourceDescriptionF':  '',
    }])

    nutrient_source_rows = pd.DataFrame([
        {'NutrientSourceID': FDC_FOUNDATION_NUTRIENT_SOURCE_ID,
         'NutrientSourceCode': 'FDC_FND',
         'NutrientSourceDescription': 'USDA FoodData Central — Foundation Foods (2026-04-30)',
         'NutrientSourceDescriptionF': ''},
        {'NutrientSourceID': FDC_SR_LEGACY_NUTRIENT_SOURCE_ID,
         'NutrientSourceCode': 'FDC_SR',
         'NutrientSourceDescription': 'USDA FoodData Central — SR Legacy (2018-04)',
         'NutrientSourceDescriptionF': ''},
        {'NutrientSourceID': FDC_FNDDS_NUTRIENT_SOURCE_ID,
         'NutrientSourceCode': 'FDC_FNDDS',
         'NutrientSourceDescription': 'USDA FoodData Central — Survey FNDDS (2024-10-31)',
         'NutrientSourceDescriptionF': ''},
    ])

    total_stats = {
        'present': present,
        'per_dataset': per_dataset_stats,
        'total_foods_emitted': int(len(food_name_df)),
        'total_nutrient_rows_emitted': int(len(nutrient_amount_df)),
        'food_id_min': int(food_name_df['FoodID'].min()) if not food_name_df.empty else None,
        'food_id_max': int(food_name_df['FoodID'].max()) if not food_name_df.empty else None,
    }
    logger.info('FDC ingest combined: %s', total_stats)

    return FDCIngestResult(
        food_name_rows=food_name_df,
        nutrient_amount_rows=nutrient_amount_df,
        food_group_rows=food_group_df,
        food_source_row=food_source_row,
        nutrient_source_rows=nutrient_source_rows,
        bridge_by_dataset=bridges,
        dropped_nutrients=dropped,
        stats=total_stats,
    )


def append_to_pipeline(cnf_pipeline, result: FDCIngestResult) -> None:
    """Append FDC rows in-place onto the live CNF pipeline DataFrames.

    Safe to call AT MOST ONCE per pipeline instance — the cache singleton
    in `api.cnf_cache` enforces this.
    """
    p = cnf_pipeline
    if 'source' not in p.food_name_df.columns:
        p.food_name_df['source'] = 'cnf'
    if 'data_type' not in p.food_name_df.columns:
        p.food_name_df['data_type'] = None
    if 'fdc_id' not in p.food_name_df.columns:
        p.food_name_df['fdc_id'] = pd.NA

    existing_food_ids = set(p.food_name_df['FoodID'].dropna().astype(int).tolist())
    new_foods = result.food_name_rows[
        ~result.food_name_rows['FoodID'].isin(existing_food_ids)
    ]
    p.food_name_df = pd.concat([p.food_name_df, new_foods], ignore_index=True)

    existing_group_ids = set(p.food_group_df['FoodGroupID'].dropna().astype(int).tolist())
    new_groups = result.food_group_rows[
        ~result.food_group_rows['FoodGroupID'].isin(existing_group_ids)
    ]
    p.food_group_df = pd.concat([p.food_group_df, new_groups], ignore_index=True)

    existing_fs_ids = set(p.food_source_df['FoodSourceID'].dropna().astype(int).tolist())
    new_fs = result.food_source_row[
        ~result.food_source_row['FoodSourceID'].isin(existing_fs_ids)
    ]
    p.food_source_df = pd.concat([p.food_source_df, new_fs], ignore_index=True)

    existing_ns_ids = set(p.nutrient_source_df['NutrientSourceID'].dropna().astype(int).tolist())
    new_ns = result.nutrient_source_rows[
        ~result.nutrient_source_rows['NutrientSourceID'].isin(existing_ns_ids)
    ]
    p.nutrient_source_df = pd.concat([p.nutrient_source_df, new_ns], ignore_index=True)

    p.nutrient_amount_df = pd.concat(
        [p.nutrient_amount_df, result.nutrient_amount_rows], ignore_index=True,
    )

    # Rebuild the per-food nutrient index now that FDC rows are appended.
    p.nutrients_by_food = p._build_nutrients_by_food_index()
    logger.info(
        'FDC append complete: %d total foods (+%d FDC at IDs %d-%d), %d total nutrient rows',
        len(p.food_name_df), len(new_foods),
        int(new_foods['FoodID'].min()) if not new_foods.empty else 0,
        int(new_foods['FoodID'].max()) if not new_foods.empty else 0,
        len(p.nutrient_amount_df),
    )
