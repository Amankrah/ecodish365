"""WAFCT 2019 ETL ingest (WAFCT-EXTEND, 2026-05-24).

Reads [`backend/raw_wafct/WAFCT_2019.xlsx`](backend/raw_wafct/WAFCT_2019.xlsx) and
appends ~1,028 West African foods into the in-memory CNF DataFrames, using:

  - FoodIDs offset by 700,000 (CNF max is 503,381 → ~200 k headroom)
  - FoodGroupIDs 50-63 for the 14 WAFCT food groups (CNF max is 25)
  - FoodSourceID = 100 (CNF max is 38)
  - NutrientSourceID = 9999 (CNF max is 110)
  - `source = 'wafct'` on the new food_name_df rows; CNF rows stay `'cnf'`

INFOODS → CNF NutrientID bridge is built programmatically from CNF's existing
`nutrient_name_df.Tagname` column (already populated for 144 / 152 CNF
nutrients per WAFCT-EXPLORE 2026-05-24), with a tiny alias-override map for
the ~6 tags where CNF uses non-INFOODS naming.

WAFCT-only nutrients (PHYTCPP, IP3-6, EDIBLE1/2, SOP, XFA, XN) are dropped
in v1 — they are either anti-nutrients (clinically meaningful but not used
by HEFI/HENI/HSR/FCS scoring) or conversion-factor metadata. A future
bioavailability-aware HENI/FCS extension could carry phytate; see
[`WAFCT_EXPLORATION.md`](WAFCT_EXPLORATION.md) §5 follow-ups.

Bracketed-value normalization (`'[10.6]'` → 10.6) is required: WAFCT uses
INFOODS' `[brackets]` convention for analytical-method-specific values (e.g.
egg fat reported via FATCE continuous-flow-extraction). Numerically the
same per-100g value; we strip brackets at ingest.

Called once per process from [`api.cnf_cache.get_api_cnf_pipeline()`](backend/api/cnf_cache.py)
on first pipeline access. Graceful degrade: if the workbook is missing, the
ingest is a no-op and the platform runs CNF-only.

Performance: ~1 s wall-clock cold (openpyxl read + DataFrame construction).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
import pandas as pd

logger = logging.getLogger(__name__)


# --- Constants (allocations are deliberately distant from CNF maxima) ----

WAFCT_FOOD_ID_OFFSET   = 700_000   # CNF max FoodID = 503,381 → ~200k clear
WAFCT_FOOD_GROUP_BASE  = 50        # CNF uses up to FoodGroupID 25
WAFCT_FOOD_SOURCE_ID   = 100       # CNF max FoodSourceID = 38
WAFCT_NUTRIENT_SOURCE_ID = 9999    # CNF max NutrientSourceID = 110
WAFCT_COUNTRY_CODE     = 'WA'      # West Africa (umbrella; specific country per BiblioID)

CNF_MAX_FOOD_ID_GUARD  = 600_000   # if Health Canada ever ships beyond this, fail loud

# WAFCT-only INFOODS tags we deliberately drop in v1 (see file head).
DROP_TAGS = frozenset({
    'EDIBLE1', 'EDIBLE2',           # edible-portion coefficients (metadata)
    'SOP',                          # sum of proximates (QC check column)
    'XFA', 'XN',                    # Atwater conversion factors
    'PHYTCPP', 'PHYTCP',            # phytate (anti-nutrient — v2 candidate)
    'IP3', 'IP4', 'IP5', 'IP6',     # inositol phosphates (phytate degradation)
})

# Tags where WAFCT name == CNF Tagname (the easy majority).
IDENTICAL_TAGS = (
    'WATER', 'FAT', 'FIBTG', 'FIBC', 'ASH', 'ALC',
    'CA', 'FE', 'MG', 'P', 'K', 'ZN', 'CU',
    'CARTA', 'CARTB', 'CRYPXB', 'RETOL',
    'TOCPHA', 'TOCPHB', 'TOCPHG', 'TOCPHD',
    'THIA', 'RIBF', 'NIA', 'NIAEQ', 'TRP', 'VITB12', 'VITC',
    'FOLAC', 'FOLFD', 'FOLDFE',
    'CHOLE', 'FASAT', 'FAMS', 'FAPU', 'F18D2CN6', 'F18D3CN3',
)

# WAFCT tag → CNF Tagname (used when WAFCT and CNF use different INFOODS-tag
# variants for the same underlying nutrient).
WAFCT_TO_CNF_TAG = {
    'PROTCNT':    'PROCNT',         # CNF: PROCNT (PROtein, CONTent)
    'CHOAVLDF':   'CHOCDF',         # CNF: CHOCDF (CHO, CHO_DiF)
    'ENERC_kcal': 'ENERC_KCAL',     # CNF uses uppercase suffix
    'ENERC_kJ':   'ENERC_KJ',
    'FATCE':      'FAT',            # WAFCT method variant — collapse to total FAT
    'VITB6C':     'VITB6A',         # WAFCT uses VITB6C; CNF uses VITB6A
    'FOL':        'FOLDFE',         # WAFCT total folate → CNF DFE (closest)
    'VITE':       'TOCPHA',         # WAFCT VITE → CNF alpha-tocopherol (vitamin-E activity)
}

# WAFCT tag → CNF NutrientID directly (used for nutrients CNF lacks in its
# Tagname column). NutrientIDs verified during plan discovery against
# `nutrient_name_df`.
WAFCT_TO_CNF_NUTRIENT_ID = {
    'NA':       307,   # SODIUM (CNF NutrientID 307 — Tagname is NaN)
    'VITA':     814,   # VITAMIN A → mapped to RAE (NutrientID 814) — best CNF equivalent
    'VITA_RAE': 814,   # RETINOL ACTIVITY EQUIVALENTS
    'VITD':     339,   # VITAMIN D (D2 + D3) — NutrientID 339
    'CARTBEQ':  321,   # BETA CAROTENE — NutrientID 321
}

# WAFCT food-group banding-row labels in sheet 03 order. Each line is the
# "English/French" label as it appears in the workbook; the index is the
# WAFCT group code (01-14). Used to allocate FoodGroupIDs deterministically.
WAFCT_FOOD_GROUPS: List[Tuple[str, str, str]] = [
    # (wafct_group_code, english_name, french_name)
    ('01', 'Cereals and their products',                 'Céréales et produits dérivés'),
    ('02', 'Starchy roots, tubers and their products',   'Racines amylacées, tubercules et produits dérivés'),
    ('03', 'Legumes and their products',                 'Légumineuses et produits dérivés'),
    ('04', 'Vegetables and their products',              'Légumes et produits dérivés'),
    ('05', 'Fruits and their products',                  'Fruits et produits dérivés'),
    ('06', 'Nuts, seeds and their products',             'Noix, graines et produits dérivés'),
    ('07', 'Meat, poultry and their products',           'Viande, volaille et produits dérivés'),
    ('08', 'Eggs and their products',                    'Œufs et produits dérivés'),
    ('09', 'Fish and its products',                      'Poisson et produits dérivés'),
    ('10', 'Milk and its products',                      'Lait et produits dérivés'),
    ('11', 'Fats and oils',                              'Graisses et huiles'),
    ('12', 'Beverages',                                  'Boissons'),
    ('13', 'Miscellaneous',                              'Divers'),
    ('14', 'Soups and sauces',                           'Soupes et sauces'),
]

CODE_RE = re.compile(r'^(\d{2})_(\d+)$')


# --- Result payload ------------------------------------------------------

@dataclass
class WAFCTIngestResult:
    food_name_rows:        pd.DataFrame      # matches CNF food_name_df schema + 'source' col
    nutrient_amount_rows:  pd.DataFrame      # matches CNF nutrient_amount_df schema
    food_group_rows:       pd.DataFrame      # matches CNF food_group_df schema
    food_source_row:       pd.DataFrame      # one row added to food_source_df
    nutrient_source_row:   pd.DataFrame      # one row added to nutrient_source_df
    bridge:                Dict[str, int] = field(default_factory=dict)
    dropped_tags:          List[str]      = field(default_factory=list)
    unmapped_tags:         List[str]      = field(default_factory=list)
    stats:                 Dict[str, Any] = field(default_factory=dict)

    @property
    def food_count(self) -> int:
        return len(self.food_name_rows)

    @property
    def first_food_id(self) -> int:
        return int(self.food_name_rows['FoodID'].min()) if not self.food_name_rows.empty else WAFCT_FOOD_ID_OFFSET


# --- Helpers --------------------------------------------------------------

def _clean_tag(v: Any) -> str:
    """Normalise a raw INFOODS tag cell. Strips whitespace, bracketed
    alternative ('FAT or [FATCE]' → 'FAT'), and outer brackets ('[FOLSUM]'
    → 'FOLSUM'). Returns '' for empty cells."""
    if v is None:
        return ''
    s = str(v).strip()
    if ' or ' in s:
        s = s.split(' or ', 1)[0].strip()
    s = s.strip('[]').strip()
    return s


def _strip_brackets(v: Any) -> Optional[float]:
    """Parse a WAFCT nutrient cell to float. Strips INFOODS' analytical-
    method brackets (`'[10.6]'` → 10.6). Returns None for blank / N/A."""
    if v is None or v == '':
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1].strip()
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _wafct_path() -> Path:
    """Resolve the WAFCT workbook path. Looks first under settings.BASE_DIR;
    falls back to the conventional `backend/raw_wafct/` location."""
    try:
        from django.conf import settings
        candidate = Path(settings.BASE_DIR) / 'raw_wafct' / 'WAFCT_2019.xlsx'
        if candidate.exists():
            return candidate
    except Exception:  # noqa: BLE001 — settings may not be configured for one-off scripts
        pass
    # Fallback: relative to this file (.../backend/api/services/etl/wafct_ingest.py)
    here = Path(__file__).resolve()
    fallback = here.parents[3] / 'raw_wafct' / 'WAFCT_2019.xlsx'
    return fallback


def workbook_present() -> bool:
    """True if WAFCT_2019.xlsx is reachable. Lets callers graceful-degrade."""
    return _wafct_path().exists()


# --- Nutrient-axis bridge -------------------------------------------------

def _build_infoods_bridge(cnf_pipeline) -> Dict[str, int]:
    """Build WAFCT_TAG → CNF NutrientID via three layers:

      1. IDENTICAL_TAGS — WAFCT tag string == CNF Tagname string (the easy case)
      2. WAFCT_TO_CNF_TAG — WAFCT tag → CNF Tagname (alias map)
      3. WAFCT_TO_CNF_NUTRIENT_ID — direct NutrientID override for tags CNF
         lacks in its Tagname column (SODIUM, VITA, VITA_RAE, VITD, CARTBEQ)

    Returns a dict keyed by WAFCT tag (i.e. exactly what `food['nutrients']`
    iteration yields) → integer CNF NutrientID.
    """
    nn = cnf_pipeline.nutrient_name_df
    # CNF Tagname → NutrientID lookup
    cnf_tag_to_id: Dict[str, int] = {}
    for _, r in nn.iterrows():
        t = r.get('Tagname')
        if t is None or pd.isna(t):
            continue
        ts = str(t).strip()
        if ts and ts not in cnf_tag_to_id:
            cnf_tag_to_id[ts] = int(r['NutrientID'])

    bridge: Dict[str, int] = {}
    # Layer 1: identical tags
    for tag in IDENTICAL_TAGS:
        nid = cnf_tag_to_id.get(tag)
        if nid is not None:
            bridge[tag] = nid
    # Layer 2: WAFCT → CNF tag aliases
    for wafct_t, cnf_t in WAFCT_TO_CNF_TAG.items():
        nid = cnf_tag_to_id.get(cnf_t)
        if nid is not None:
            bridge[wafct_t] = nid
    # Layer 3: direct NutrientID overrides (CNF lacks Tagname for these)
    for wafct_t, nid in WAFCT_TO_CNF_NUTRIENT_ID.items():
        bridge[wafct_t] = nid
    return bridge


# --- Sheet loader (sheet 03 NV_sum_39) ------------------------------------

def _load_wafct_sheet_03(
    workbook_path: Path,
) -> List[Dict[str, Any]]:
    """Read sheet 03 → list of dicts, one per food, with parsed nutrient values
    keyed by canonical WAFCT INFOODS tag (e.g. 'ENERC_kcal', 'CA').

    Skips banding rows (food-group headers) and blank rows.
    """
    wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    ws = wb['03 NV_sum_39 (per 100g EP)']
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 4:
        return []

    header_en = rows[0]
    header_tags = rows[2]

    # Build column index → canonical WAFCT tag. ENERC appears twice in the
    # 39-set: disambiguate by header_en unit hint ("Energy (kJ)" vs "Energy (kcal)").
    col_to_tag: Dict[int, str] = {}
    enerc_seen = 0
    for i, raw in enumerate(header_tags):
        if raw is None:
            continue
        tag = _clean_tag(raw)
        if not tag:
            continue
        if tag == 'ENERC':
            unit_hint = str(header_en[i] or '').lower()
            if 'kj' in unit_hint:
                col_to_tag[i] = 'ENERC_kJ'
            elif 'kcal' in unit_hint:
                col_to_tag[i] = 'ENERC_kcal'
            else:
                enerc_seen += 1
                col_to_tag[i] = 'ENERC_kJ' if enerc_seen == 1 else 'ENERC_kcal'
            continue
        col_to_tag[i] = tag

    out: List[Dict[str, Any]] = []
    for row in rows[3:]:
        if not row or row[0] is None:
            continue
        code = str(row[0]).strip()
        m = CODE_RE.match(code)
        if not m:
            continue  # banding row or other text
        group_code = m.group(1)
        name_en = str(row[1]) if row[1] else ''
        name_fr = str(row[2]) if row[2] else ''
        sci_name = str(row[3]) if row[3] else ''
        biblio = str(row[4]) if row[4] else ''

        nutrients: Dict[str, Optional[float]] = {}
        for col_idx, tag in col_to_tag.items():
            if col_idx >= len(row):
                continue
            v = _strip_brackets(row[col_idx])
            if v is not None:
                nutrients[tag] = v

        out.append({
            'code':         code,
            'group_code':   group_code,
            'name_en':      name_en,
            'name_fr':      name_fr,
            'scientific':   sci_name,
            'biblio':       biblio,
            'nutrients':    nutrients,
        })
    return out


# --- Main entry point -----------------------------------------------------

def ingest_wafct(cnf_pipeline) -> WAFCTIngestResult:
    """Read WAFCT_2019.xlsx, build DataFrames keyed for append to CNF schema.

    The caller (typically `api.cnf_cache._maybe_ingest_wafct`) appends the
    returned DataFrames into the live pipeline.
    """
    path = _wafct_path()
    if not path.exists():
        raise FileNotFoundError(f'WAFCT workbook not found at {path}')

    # Guard against future CNF growth colliding with our offset.
    cnf_max = int(cnf_pipeline.food_name_df['FoodID'].max())
    if cnf_max >= CNF_MAX_FOOD_ID_GUARD:
        raise RuntimeError(
            f'CNF max FoodID ({cnf_max}) approaches the WAFCT offset region. '
            f'Raise WAFCT_FOOD_ID_OFFSET above {cnf_max + 100_000} before continuing.'
        )

    logger.info('WAFCT ingest: reading %s', path)
    bridge = _build_infoods_bridge(cnf_pipeline)
    logger.info('WAFCT ingest: nutrient bridge has %d INFOODS→CNF mappings', len(bridge))

    foods = _load_wafct_sheet_03(path)
    logger.info('WAFCT ingest: loaded %d food rows from sheet 03', len(foods))

    # 1. food_group_rows — 14 WAFCT groups at FoodGroupID 50-63
    fg_rows = []
    fg_id_by_code: Dict[str, int] = {}
    for i, (code, name_en, name_fr) in enumerate(WAFCT_FOOD_GROUPS):
        fg_id = WAFCT_FOOD_GROUP_BASE + i
        fg_id_by_code[code] = fg_id
        fg_rows.append({
            'FoodGroupID':    fg_id,
            'FoodGroupCode':  f'WAFCT_{code}',
            'FoodGroupName':  f'WAFCT — {name_en}',
            'FoodGroupNameF': f'TCAAO — {name_fr}',
        })
    food_group_df = pd.DataFrame(fg_rows)

    # 2. food_source_row — single row for "WAFCT 2019"
    food_source_row = pd.DataFrame([{
        'FoodSourceID':           WAFCT_FOOD_SOURCE_ID,
        'FoodSourceCode':         'WAFCT_2019',
        'FoodSourceDescription':  'FAO/INFOODS West African Food Composition Table 2019',
        'FoodSourceDescriptionF': 'TCAAO — Table de composition alimentaire FAO/INFOODS pour l\'Afrique de l\'Ouest 2019',
    }])

    # 3. nutrient_source_row — single row for "Ingested from WAFCT 2019"
    nutrient_source_row = pd.DataFrame([{
        'NutrientSourceID':            WAFCT_NUTRIENT_SOURCE_ID,
        'NutrientSourceCode':          'WAFCT_2019',
        'NutrientSourceDescription':   'Ingested from FAO/INFOODS WAFCT 2019 NV_sum_39',
        'NutrientSourc DescriptionF':  'Importé de FAO/INFOODS TCAAO 2019 NV_sum_39',
    }])

    # 4. food_name_rows — assign FoodIDs deterministically: 700000 + sequential index
    today = datetime.today()
    food_name_records = []
    nutrient_amount_records = []
    used_food_ids = set()
    for idx, food in enumerate(foods):
        food_id = WAFCT_FOOD_ID_OFFSET + idx
        used_food_ids.add(food_id)
        fg_id = fg_id_by_code.get(food['group_code'])
        if fg_id is None:
            # Group code outside our 01-14 map — shouldn't happen but skip safely
            logger.warning('WAFCT food %s has unknown group_code %s — skipping',
                           food['code'], food['group_code'])
            continue
        food_name_records.append({
            'FoodID':                food_id,
            'FoodCode':              f'WAFCT_{food["code"]}',
            'FoodGroupID':           fg_id,
            'FoodSourceID':          WAFCT_FOOD_SOURCE_ID,
            'FoodDescription':       food['name_en'],
            'FoodDescriptionF':      food['name_fr'],
            'FoodDateOfEntry':       today,
            'FoodDateOfPublication': today,
            'CountryCode':           WAFCT_COUNTRY_CODE,
            'ScientificName':        food['scientific'],
            'source':                'wafct',
        })
        # Per-nutrient rows
        for wafct_tag, value in food['nutrients'].items():
            if wafct_tag in DROP_TAGS:
                continue
            nid = bridge.get(wafct_tag)
            if nid is None:
                continue  # unmapped — silently drop in v1
            nutrient_amount_records.append({
                'FoodID':               food_id,
                'NutrientID':           nid,
                'NutrientValue':        value,
                'StandardError':        None,
                'NumberofObservations': None,
                'NutrientSourceID':     WAFCT_NUTRIENT_SOURCE_ID,
                'NutrientDateOfEntry':  today,
            })

    food_name_df = pd.DataFrame(food_name_records)
    nutrient_amount_df = pd.DataFrame(nutrient_amount_records)

    # Stats
    stats = {
        'foods_loaded':           len(foods),
        'foods_emitted':          len(food_name_df),
        'nutrient_rows_emitted':  len(nutrient_amount_df),
        'unique_tags_used':       len({r['NutrientID'] for r in nutrient_amount_records}),
        'bridge_size':            len(bridge),
        'wafct_food_id_min':      int(food_name_df['FoodID'].min()) if not food_name_df.empty else None,
        'wafct_food_id_max':      int(food_name_df['FoodID'].max()) if not food_name_df.empty else None,
    }
    logger.info('WAFCT ingest done: %s', stats)

    # All actually-encountered WAFCT tags that we DROPPED for being unmapped.
    # bridge is keyed by WAFCT tag now (per Layer 1/2/3 in _build_infoods_bridge),
    # so a WAFCT tag is "mapped" iff it's in bridge.
    encountered_tags = {t for f in foods for t in f['nutrients']}
    dropped_known = sorted(encountered_tags & DROP_TAGS)
    unmapped_in_wild = sorted((encountered_tags - set(bridge.keys())) - DROP_TAGS)

    return WAFCTIngestResult(
        food_name_rows=food_name_df,
        nutrient_amount_rows=nutrient_amount_df,
        food_group_rows=food_group_df,
        food_source_row=food_source_row,
        nutrient_source_row=nutrient_source_row,
        bridge=bridge,
        dropped_tags=dropped_known,
        unmapped_tags=unmapped_in_wild,
        stats=stats,
    )


def append_to_pipeline(cnf_pipeline, result: WAFCTIngestResult) -> None:
    """Append WAFCT rows in-place onto the live CNF pipeline DataFrames.

    Safe to call AT MOST ONCE per pipeline instance — the cache singleton
    in `api.cnf_cache` enforces this.
    """
    p = cnf_pipeline
    if 'source' not in p.food_name_df.columns:
        p.food_name_df['source'] = 'cnf'

    # Append (avoid duplicate FoodIDs / FoodGroupIDs / source IDs if called twice)
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
    new_ns = result.nutrient_source_row[
        ~result.nutrient_source_row['NutrientSourceID'].isin(existing_ns_ids)
    ]
    p.nutrient_source_df = pd.concat([p.nutrient_source_df, new_ns], ignore_index=True)

    # Append nutrient amounts
    p.nutrient_amount_df = pd.concat(
        [p.nutrient_amount_df, result.nutrient_amount_rows], ignore_index=True,
    )

    # Rebuild the per-food nutrient index (it was built at CNF-load time;
    # adding WAFCT rows after the fact requires a re-index).
    p.nutrients_by_food = p._build_nutrients_by_food_index()
    logger.info('WAFCT append complete: %d total foods, %d WAFCT foods at IDs %d+',
                len(p.food_name_df), len(new_foods),
                int(new_foods['FoodID'].min()) if not new_foods.empty else WAFCT_FOOD_ID_OFFSET)
