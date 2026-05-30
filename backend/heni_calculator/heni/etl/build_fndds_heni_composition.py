"""One-time ETL: CNF FoodID -> FNDDS-substrate HENI composition (15 keys / 100 g).

This is the FNDDS-substrate parallel to `build_cnf_heni_composition.py`. The
food-group factors come from the same FPED 2017-2018 attribution that the CNF
substrate uses, joined through the existing CNF -> FNDDS bridge. The nutrient
factors come from USDA FoodData Central's `food_nutrient.csv`, which is the
per-100 g nutrient profile that Stylianou et al. 2021 used to derive their
published per-food HENI values.

Joins:
    cnf_to_fndds_bridge.json (CNF FoodID -> {food_code, fdc_id, confidence})
    -> FoodData Central food_nutrient.csv keyed on fdc_id (per-100 g nutrients)
    -> FPED_1718.xls keyed on FOODCODE (per-100 g food-group cup/oz equivalents)
    -> combine into a single 15-key risk-factor composition per CNF FoodID

Output:
    backend/heni_calculator/data/fndds_heni_composition.json

The output schema matches `cnf_heni_composition.json` but adds the seven
nutrient keys that the CNF file omits, because under FNDDS substrate the
nutrient values are taken from FoodData Central rather than from CNF's
own nutrient table. Validation harnesses can then call the substrate-aware
composition loader to retrieve either substrate for the same CNF food.

Nutrient ID lookups in FoodData Central nutrient.csv:
    1087 Calcium, Ca                              (mg)
    1093 Sodium, Na                               (mg)
    1079 Fiber, total dietary                     (g)
    1257 Fatty acids, total trans                 (g)
    1293 Fatty acids, total polyunsaturated       (g)
    1278 PUFA 20:5 n-3 (EPA)                      (g)
    1272 PUFA 22:6 n-3 (DHA)                      (g)

omega_3 in the HENI composition is EPA + DHA (Stylianou 2021 SI Table 3 p. 8
defines omega_3 as the marine long-chain n-3 sum, not ALA). The HENI calculator
later applies the Stylianou SI S2.9 carve-outs (milk vs calcium, fiber source
split into fiber_fvlw / fiber_other), which are substrate-independent.

Usage:
    cd backend
    python -m heni_calculator.heni.etl.build_fndds_heni_composition
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


_THIS_DIR = Path(__file__).resolve().parent
_DATA_DIR = _THIS_DIR.parent.parent / 'data'
_BACKEND_ROOT = _THIS_DIR.parents[2]
_FNDDS_DIR = _BACKEND_ROOT / 'raw_fndds' / 'FoodData_Central_survey_food_csv_2024-10-31'
_FPED_PATH = _BACKEND_ROOT / 'raw_fped' / 'FPED_1718.xls'

BRIDGE_PATH = _DATA_DIR / 'cnf_to_fndds_bridge.json'
COMPOSITION_PATH = _DATA_DIR / 'fndds_heni_composition.json'
COMPOSITION_META_PATH = _DATA_DIR / 'fndds_heni_composition_meta.json'


# FoodData Central nutrient_nbr lookups for the seven HENI nutrient risk
# factors. The survey food_nutrient.csv keys on the 3-digit legacy
# `nutrient_nbr`, not the 4-digit modern `id`. omega_3 is the EPA + DHA
# sum (Stylianou SI Table 3 p. 8).
_NUTRIENT_IDS = {
    'calcium': 301,             # mg per 100 g
    'sodium': 307,              # mg per 100 g
    'fiber': 291,               # g per 100 g (total dietary; later split by fvlw/other)
    'trans_fat': 605,           # g per 100 g
    'polyunsaturated': 646,     # g per 100 g (total PUFA)
    'epa': 629,                 # g per 100 g
    'dha': 621,                 # g per 100 g
}


def _load_fped() -> pd.DataFrame:
    """Load FPED_1718.xls keyed on FOODCODE. Identical to the CNF ETL helper
    so the food-group attribution is bit-equivalent across substrates."""
    df = pd.read_excel(_FPED_PATH, sheet_name='FPED_1718', header=0)
    df['FOODCODE'] = df['FOODCODE'].astype('int64')
    logger.info('Loaded FPED 1718: %d rows', len(df))
    return df.set_index('FOODCODE')


def _load_fndds_nutrient_pivot() -> pd.DataFrame:
    """Load FoodData Central food_nutrient.csv and pivot to one row per fdc_id
    with the seven HENI-relevant columns. Missing nutrients are filled with 0
    so the downstream HENI computation is consistent with the calculator's
    treatment of absent nutrients (zero contribution, with a TFA imputation
    warning surfaced separately when relevant).
    """
    keep_ids = set(_NUTRIENT_IDS.values())
    logger.info('Reading food_nutrient.csv (large; only keeping %d nutrient ids)',
                len(keep_ids))
    fn = pd.read_csv(_FNDDS_DIR / 'food_nutrient.csv',
                     usecols=['fdc_id', 'nutrient_id', 'amount'])
    fn = fn[fn['nutrient_id'].isin(keep_ids)].copy()
    logger.info('Filtered food_nutrient rows to %d HENI-relevant entries', len(fn))
    # Pivot to fdc_id x nutrient_id, sum-aggregating in the rare case of
    # duplicate rows for the same fdc_id and nutrient.
    pivot = fn.pivot_table(index='fdc_id', columns='nutrient_id',
                            values='amount', aggfunc='sum', fill_value=0.0)
    # Rename columns to our short names.
    name_by_id = {v: k for k, v in _NUTRIENT_IDS.items()}
    pivot.columns = [name_by_id[c] for c in pivot.columns]
    # Ensure every HENI column is present even when no foods carry it.
    for col in _NUTRIENT_IDS:
        if col not in pivot.columns:
            pivot[col] = 0.0
    logger.info('Pivoted to %d fdc_ids with HENI nutrient columns', len(pivot))
    return pivot


# Reuse the CNF ETL's food-group attribution helpers so we get exactly the
# same FPED column mapping and cup / oz equivalent gram conversions. Keeping
# food-group attribution substrate-invariant is what allows the per-food
# substrate comparison in Phase 4 to attribute divergence cleanly to the
# nutrient factors.
from heni_calculator.heni.etl.build_cnf_heni_composition import (  # noqa: E402
    _compute_composition_for_fped_row,
)


def _compute_nutrient_factors(nut_row: pd.Series) -> Dict[str, float]:
    """Convert the seven raw FoodData Central nutrient amounts into the
    HENI risk-factor schema, applying the same unit normalisations the
    HENI calculator's runtime extractor applies (mg -> g for calcium and
    sodium; omega_3 = EPA + DHA; PUFA is the umbrella total).

    Returns g per 100 g for every key.
    """
    epa = float(nut_row.get('epa', 0.0) or 0.0)
    dha = float(nut_row.get('dha', 0.0) or 0.0)
    return {
        'omega_3': round(epa + dha, 6),
        'calcium': round(float(nut_row.get('calcium', 0.0) or 0.0) / 1000.0, 6),
        'sodium': round(float(nut_row.get('sodium', 0.0) or 0.0) / 1000.0, 6),
        'polyunsaturated_fatty_acids': round(
            float(nut_row.get('polyunsaturated', 0.0) or 0.0), 6),
        'trans_fat': round(float(nut_row.get('trans_fat', 0.0) or 0.0), 6),
        'fiber': round(float(nut_row.get('fiber', 0.0) or 0.0), 6),
    }


def _content_hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def main() -> int:
    if not BRIDGE_PATH.exists():
        logger.error('Bridge JSON not found at %s; run build_cnf_to_fndds_bridge first',
                     BRIDGE_PATH)
        return 1
    bridge = json.loads(BRIDGE_PATH.read_text(encoding='utf-8'))
    bridges: Dict[str, Dict] = bridge.get('bridges', {})
    logger.info('Loaded bridge: %d bridged CNF entries', len(bridges))

    fped = _load_fped()
    fndds_nut = _load_fndds_nutrient_pivot()

    compositions: Dict[str, Dict] = {}
    no_fped_row: list = []
    no_fdc_nutrient: list = []

    for cnf_id_str, br in bridges.items():
        try:
            food_code = int(br['food_code'])
            fdc_id = int(br['fdc_id'])
            confidence = float(br['confidence'])
        except (TypeError, ValueError, KeyError):
            continue
        if food_code not in fped.index:
            no_fped_row.append(cnf_id_str)
            continue
        # Food-group factors from FPED (substrate-invariant)
        comp = _compute_composition_for_fped_row(fped.loc[food_code])
        # Nutrient factors from FoodData Central (FNDDS substrate)
        if fdc_id in fndds_nut.index:
            comp.update(_compute_nutrient_factors(fndds_nut.loc[fdc_id]))
            comp['_nutrients_source'] = 'fndds_food_nutrient_csv'
        else:
            # No FDC nutrient profile for this fdc_id; emit zeros with a
            # provenance flag so the downstream harness can skip or surface
            # the gap.
            comp.update({
                'omega_3': 0.0, 'calcium': 0.0, 'sodium': 0.0,
                'polyunsaturated_fatty_acids': 0.0, 'trans_fat': 0.0,
                'fiber': 0.0,
            })
            comp['_nutrients_source'] = 'missing_fdc_nutrient_profile'
            no_fdc_nutrient.append(cnf_id_str)
        comp['_method'] = 'fndds_substrate'
        comp['_fdc_id'] = fdc_id
        comp['_food_code'] = food_code
        comp['_bridge_confidence'] = confidence
        compositions[cnf_id_str] = comp

    logger.info('Computed %d FNDDS-substrate compositions', len(compositions))
    logger.info('  no FPED row: %d', len(no_fped_row))
    logger.info('  no FDC nutrient profile: %d', len(no_fdc_nutrient))

    out = {
        '_provenance': {
            'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'fped_source': 'USDA FPED 1718',
            'fndds_source': 'FoodData Central Survey Foods 2024-10-31',
            'bridge_source': BRIDGE_PATH.name,
            'substrate': 'fndds_for_cnf',
            'compositions_computed': len(compositions),
            'compositions_no_fped_row': len(no_fped_row),
            'compositions_no_fdc_nutrient': len(no_fdc_nutrient),
            'nutrient_id_lookups': _NUTRIENT_IDS,
            'unit_normalisation': {
                'calcium_mg_to_g': 'value / 1000',
                'sodium_mg_to_g': 'value / 1000',
                'omega_3': 'epa + dha (Stylianou SI Table 3)',
                'polyunsaturated_fatty_acids': 'NutrientID 1293 umbrella total',
                'trans_fat': 'NutrientID 1257 total trans (Stylianou TFA proxy '
                             'for the regression imputation he applied; '
                             'FoodData Central reports measured values where '
                             'available, zero otherwise)',
                'fiber': 'NutrientID 1079 total dietary; runtime carve-out '
                         'splits into fiber_fvlw and fiber_other.',
            },
            'cup_oz_eq_to_grams': {
                'fruits_cup_eq_g': 154.0,
                'vegetables_cup_eq_g': 165.0,
                'legumes_cup_eq_g': 172.0,
                'dairy_milk_cup_eq_g': 244.0,
                'dairy_yogurt_cup_eq_g': 244.0,
                'dairy_cheese_cup_eq_g': 42.5,
                'grains_oz_eq_g': 28.35,
                'protein_oz_eq_g': 28.35,
                'nuts_seeds_oz_eq_g': 28.35,
            },
        },
        'compositions': compositions,
        'no_fped_row_food_ids': sorted(int(c) for c in no_fped_row),
        'no_fdc_nutrient_food_ids': sorted(int(c) for c in no_fdc_nutrient),
    }
    serialised = json.dumps(out, indent=2, ensure_ascii=False)
    COMPOSITION_PATH.write_text(serialised, encoding='utf-8')
    meta = {
        'date_utc': out['_provenance']['date_utc'],
        'content_sha256_16': _content_hash_str(serialised),
        'compositions_count': len(compositions),
        'substrate': 'fndds_for_cnf',
    }
    COMPOSITION_META_PATH.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    logger.info('Wrote %s (sha256:%s)', COMPOSITION_PATH, meta['content_sha256_16'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
