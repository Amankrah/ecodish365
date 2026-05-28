"""One-time ETL: normalize the CNF 2026 native edition into legacy-schema CSVs.

Health Canada's CNF 2026 release renamed every column, switched to UTF-8, and
merged the old CONVERSION_FACTOR / REFUSE_AMOUNT / YIELD_AMOUNT tables into a
single measure_weight_conversion file. This script is the compatibility boundary
for the upgrade: it reads the 2026 native files from ``backend/raw_cnf_2026_source/``
and writes the legacy-named, legacy-column, ISO-8859-1 CSVs into ``backend/raw_cnf/``
that the existing CNF pipeline and the ~12 hardcoded ``raw_cnf/`` readers expect.
Nothing downstream of ``raw_cnf/`` changes.

Field map: Appendix A of
``canadian-nutrient-file_database-structure-and-file-content-description_2026.pdf``.

Measure model: the 2026 ``measure_weight_conversion.csv`` is partitioned by
``Measure_Type_Code`` (6 = User-defined household measures, 3 = Refuse,
9 = Yield). We split it back into the three legacy tables. Conversion semantics
also changed: the legacy ``ConversionFactorValue`` had to be multiplied by 100 to
get a measure's gram weight, whereas the 2026 ``Measure_Weight_Conversion`` *is*
the gram weight. So legacy ``ConversionFactorValue = Measure_Weight_Conversion / 100``
(verified against the guide example: applesauce food 1700, 250 ml → 257.819 → 2.57819).

Usage (from backend/):
    python -m api.services.etl.build_cnf_2026_legacy_view
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

_BACKEND_ROOT = Path(__file__).resolve().parents[3]  # api/services/etl -> backend
_SOURCE_DIR = _BACKEND_ROOT / 'raw_cnf_2026_source'
_DEST_DIR = _BACKEND_ROOT / 'raw_cnf'

_SOURCE_ENCODING = 'utf-8-sig'   # 2026 files are UTF-8 with BOM
_DEST_ENCODING = 'ISO-8859-1'    # what api.cnf_data_pipeline hardcodes

# Measure_Type_Code partitions (from raw_cnf_2026_source/measure_type.csv).
_MEASURE_TYPE_USER_DEFINED = 6
_MEASURE_TYPE_REFUSE = 3
_MEASURE_TYPE_YIELD = 9


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(_SOURCE_DIR / name, encoding=_SOURCE_ENCODING, low_memory=False)


def _as_int(series: pd.Series) -> pd.Series:
    """Coerce to pandas nullable Int64 so CSV output is '2' not '2.0' and NA is blank."""
    return pd.to_numeric(series, errors='coerce').astype('Int64')


def _sanitize_for_latin1(df: pd.DataFrame) -> int:
    """Replace any char not representable in ISO-8859-1 in object columns.

    CNF text is overwhelmingly Latin-1 (English + French), but a stray curly
    quote or em-dash would crash the ISO-8859-1 write. Returns the count of
    characters replaced so the run is honest about any (rare) loss.
    """
    replaced = 0
    for col in df.columns:
        if df[col].dtype != object:
            continue
        def _fix(v):
            nonlocal replaced
            if not isinstance(v, str):
                return v
            try:
                v.encode('latin-1')
                return v
            except UnicodeEncodeError:
                out = v.encode('latin-1', errors='replace').decode('latin-1')
                replaced += sum(1 for a, b in zip(v, out) if a != b)
                return out
        df[col] = df[col].map(_fix)
    return replaced


def _write(df: pd.DataFrame, name: str) -> None:
    n_replaced = _sanitize_for_latin1(df)
    (_DEST_DIR / name).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(_DEST_DIR / name, index=False, encoding=_DEST_ENCODING)
    msg = f'wrote {name}: {len(df)} rows'
    if n_replaced:
        msg += f' ({n_replaced} non-Latin-1 chars replaced)'
    logger.info(msg)


# ---------------------------------------------------------------------------
# Per-file builders. Each reproduces the exact legacy header (pinned from
# git HEAD of raw_cnf/) so the loader's dtype coercion + the ~12 hardcoded
# readers see byte-compatible inputs.
# ---------------------------------------------------------------------------

def build_food_name() -> None:
    src = _read('food_name.csv')
    out = pd.DataFrame({
        'FoodID': _as_int(src['Food_Code']),
        'FoodCode': _as_int(src['Food_Code']),
        'FoodGroupID': _as_int(src['CNF_Food_Group_Code']),
        'FoodSourceID': _as_int(src['Food_Source_Code']),
        'FoodDescription': src['Food_Description_EN'],
        'FoodDescriptionF': src['Food_Description_FR'],
        'FoodDateOfEntry': src['Food_Last_Updated_Date'],
        'FoodDateOfPublication': '',
        'CountryCode': src.get('USDA_NDB_Code'),
        'ScientificName': src.get('ScientificName'),
    })
    _write(out, 'FOOD_NAME.csv')


def build_food_group() -> None:
    src = _read('cnf_food_group.csv')
    out = pd.DataFrame({
        'FoodGroupID': _as_int(src['CNF_Food_Group_Code']),
        'FoodGroupCode': _as_int(src['CNF_Food_Group_Code']),
        'FoodGroupName': src['CNF_Food_Group_Description_EN'],
        'FoodGroupNameF': src['CNF_Food_Group_Description_FR'],
    })
    _write(out, 'FOOD_GROUP.csv')


def build_food_source() -> None:
    src = _read('food_source.csv')
    out = pd.DataFrame({
        'FoodSourceID': _as_int(src['Food_Source_Code']),
        'FoodSourceCode': _as_int(src['Food_Source_Code']),
        'FoodSourceDescription': src['Food_Source_Description_EN'],
        'FoodSourceDescriptionF': src['Food_Source_Description_FR'],
    })
    _write(out, 'FOOD_SOURCE.csv')


def build_nutrient_amount() -> None:
    src = _read('nutrient_amount.csv')
    out = pd.DataFrame({
        'FoodID': _as_int(src['Food_Code']),
        'NutrientID': _as_int(src['Nutrient_Code']),
        'NutrientValue': src['Nutrient_Amount'],
        'StandardError': src['STD_Error'],
        'NumberofObservations': src['Observations'],
        'NutrientSourceID': _as_int(src['Nutrient_Source_Code']),
        'NutrientDateOfEntry': src['Nutrient_Last_Updated_Date'],
    })
    _write(out, 'NUTRIENT_AMOUNT.csv')


def build_nutrient_name() -> None:
    src = _read('nutrient_name.csv')
    # CRITICAL: the legacy CNF edition stored NutrientName in UPPERCASE
    # ('PROTEIN', 'ENERGY (KILOCALORIES)'), and every calculator looks foods up
    # by those exact uppercase strings via the pipeline's nutrients_by_food
    # index. The 2026 edition switched to sentence case ('Protein', 'Energy
    # (kilocalories)'). Uppercasing Nutrient_Name_EN reproduces the legacy
    # strings for all common nutrients while staying truthful for the handful
    # of fatty-acid codes Health Canada reassigned between editions (a
    # code->legacy-string map would mislabel those). Nutrient codes are stable,
    # so the join in nutrients_by_food still keys correctly on NutrientID.
    out = pd.DataFrame({
        'NutrientID': _as_int(src['Nutrient_Code']),
        'NutrientCode': _as_int(src['Nutrient_Code']),
        'NutrientSymbol': src['Nutrient_Symbol'],
        'NutrientUnit': src['Nutrient_Unit'],
        'NutrientName': src['Nutrient_Name_EN'].astype(str).str.upper(),
        'NutrientNameF': src['Nutrient_Name_FR'],
        'Tagname': src.get('Tagname'),
        'NutrientDecimals': src['Nutrient_Decimals'],
    })
    _write(out, 'NUTRIENT_NAME.csv')


def build_nutrient_source() -> None:
    src = _read('nutrient_source.csv')
    out = pd.DataFrame({
        'NutrientSourceID': _as_int(src['Nutrient_Source_Code']),
        'NutrientSourceCode': _as_int(src['Nutrient_Source_Code']),
        'NutrientSourceDescription': src['Nutrient_Source_Description_EN'],
        # Reproduce the legacy header typo verbatim so byte-level readers match.
        'NutrientSourc DescriptionF': src['Nutrient_Source_Description_FR'],
    })
    _write(out, 'NUTRIENT_SOURCE.csv')


def build_measure_name() -> None:
    src = _read('measure_name.csv')
    out = pd.DataFrame({
        'MeasureID': _as_int(src['Measure_Code']),
        'MeasureDescription': src['Measure_Description_and_Unit_EN'],
        'MeasureDescriptionF': src['Measure_Description_and_Unit_FR'],
    })
    _write(out, 'MEASURE_NAME.csv')


def _measure_name_lookup() -> Dict[int, Dict[str, str]]:
    mn = _read('measure_name.csv')
    return {
        int(r.Measure_Code): {
            'en': str(getattr(r, 'Measure_Description_and_Unit_EN', '') or ''),
            'fr': str(getattr(r, 'Measure_Description_and_Unit_FR', '') or ''),
        }
        for r in mn.itertuples(index=False)
    }


def build_measure_split() -> None:
    """Split measure_weight_conversion into CONVERSION_FACTOR / REFUSE_AMOUNT /
    YIELD_AMOUNT (+ minimal REFUSE_NAME / YIELD_NAME) by Measure_Type_Code."""
    mwc = _read('measure_weight_conversion.csv')
    date_col = 'Measure_Weight_Conversion_Last_Updated_Date'

    # CONVERSION_FACTOR (type 6): legacy ConversionFactorValue = MWC / 100.
    cf = mwc[mwc['Measure_Type_Code'] == _MEASURE_TYPE_USER_DEFINED]
    cf_out = pd.DataFrame({
        'FoodID': _as_int(cf['Food_Code']),
        'MeasureID': _as_int(cf['Measure_Code']),
        'ConversionFactorValue': pd.to_numeric(cf['Measure_Weight_Conversion'], errors='coerce') / 100.0,
        'ConvFactorDateOfEntry': cf[date_col],
        'MeasureDescription': '',
    })
    _write(cf_out, 'CONVERSION_FACTOR.csv')

    # REFUSE_AMOUNT (type 3).
    rf = mwc[mwc['Measure_Type_Code'] == _MEASURE_TYPE_REFUSE]
    rf_out = pd.DataFrame({
        'FoodID': _as_int(rf['Food_Code']),
        'RefuseID': _as_int(rf['Measure_Code']),
        'RefuseAmount': pd.to_numeric(rf['Measure_Weight_Conversion'], errors='coerce'),
        'RefuseDateOfEntry': rf[date_col],
    })
    _write(rf_out, 'REFUSE_AMOUNT.csv')

    # YIELD_AMOUNT (type 9). Note legacy column 'YieldDateofEntry' (lowercase 'of').
    yl = mwc[mwc['Measure_Type_Code'] == _MEASURE_TYPE_YIELD]
    yl_out = pd.DataFrame({
        'FoodID': _as_int(yl['Food_Code']),
        'YieldID': _as_int(yl['Measure_Code']),
        'YieldAmount': pd.to_numeric(yl['Measure_Weight_Conversion'], errors='coerce'),
        'YieldDateofEntry': yl[date_col],
    })
    _write(yl_out, 'YIELD_AMOUNT.csv')

    # REFUSE_NAME / YIELD_NAME: the 2026 release folded these into measure_type,
    # so synthesize minimal id->description tables from the measure_name text of
    # the codes that actually appear in each partition. Nothing in the pipeline
    # computes refuse/yield today; the loader only dropna's these tables.
    mlook = _measure_name_lookup()

    def _name_table(part: pd.DataFrame, id_col: str, desc_col: str, descf_col: str, fname: str) -> None:
        codes = sorted({int(c) for c in part['Measure_Code'].dropna().unique()})
        rows = [{
            id_col: c,
            desc_col: mlook.get(c, {}).get('en', ''),
            descf_col: mlook.get(c, {}).get('fr', ''),
        } for c in codes]
        _write(pd.DataFrame(rows, columns=[id_col, desc_col, descf_col]), fname)

    _name_table(rf, 'RefuseID', 'RefuseDescription', 'RefuseDescriptionF', 'REFUSE_NAME.csv')
    _name_table(yl, 'YieldID', 'YieldDescription', 'YieldDescriptionF', 'YIELD_NAME.csv')


def build_json_helpers() -> None:
    """Regenerate the CNF-derived convenience JSON lists from the normalized data.

    nutrition_reference_amounts.json is edition-independent and is preserved
    separately (restored from git), not touched here.
    """
    import json
    fn = pd.read_csv(_DEST_DIR / 'FOOD_NAME.csv', encoding=_DEST_ENCODING, low_memory=False)
    descs: List[str] = [str(x) for x in fn['FoodDescription'].dropna().tolist()]
    (_DEST_DIR / 'food_descriptions.json').write_text(
        json.dumps(descs, ensure_ascii=False, indent=0), encoding='utf-8')
    logger.info('wrote food_descriptions.json: %d entries', len(descs))

    nn = pd.read_csv(_DEST_DIR / 'NUTRIENT_NAME.csv', encoding=_DEST_ENCODING, low_memory=False)
    names: List[str] = [str(x) for x in nn['NutrientName'].dropna().tolist()]
    (_DEST_DIR / 'nutrient_names.json').write_text(
        json.dumps(names, ensure_ascii=False, indent=0), encoding='utf-8')
    logger.info('wrote nutrient_names.json: %d entries', len(names))


def main() -> int:
    if not _SOURCE_DIR.is_dir():
        logger.error('source dir missing: %s', _SOURCE_DIR)
        return 1
    logger.info('Normalizing CNF 2026 -> legacy view: %s -> %s', _SOURCE_DIR, _DEST_DIR)
    build_food_name()
    build_food_group()
    build_food_source()
    build_nutrient_amount()
    build_nutrient_name()
    build_nutrient_source()
    build_measure_name()
    build_measure_split()
    build_json_helpers()
    logger.info('DONE. Legacy-schema CSVs regenerated in %s', _DEST_DIR)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
