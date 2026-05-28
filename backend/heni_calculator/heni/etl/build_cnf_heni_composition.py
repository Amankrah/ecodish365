"""One-time ETL: CNF FoodID -> HENI food-group risk-factor masses (g per 100g food).

Joins:
    cnf_to_fndds_bridge.json  (Phase 1 output)
    -> FNDDS food_code
    -> FPED_1718.xls          (USDA Food Patterns Equivalents per 100g)
    -> per-column cup/oz-equivalent values
    -> gram conversion (per-category constants)
    -> HENI risk-factor masses

Output:
    backend/heni_calculator/data/cnf_heni_composition.json

This is the deterministic data file that replaces the literal-100 food-group
attribution in heni_calculator_methods.py (HENI-CODE-1.y cause A).

Per-100g semantics: every value in the output JSON is "grams of risk-component
category per 100 grams of the CNF food". The HENI calculator scales by
(serving_g / 100) at runtime, so this is the basis the downstream code expects.

Cup/oz-equivalent gram conversion (FPED documentation; USDA Dietary Guidelines):

  Fruits  (cup eq.) = 154 g          (USDA 1 cup fruit reference)
  Vegetables (cup eq.) = 165 g        (USDA 1 cup vegetable reference)
  Legumes  (cup eq.) = 172 g          (USDA 1 cup cooked legume reference)
  Dairy milk (cup eq.) = 244 g        (1 fl-oz cup = 244 g for milk/yogurt)
  Dairy cheese (cup eq.) = 42.5 g     (1.5 oz natural cheese = 1 cup-eq dairy)
  Grain (oz eq.) = 28.35 g            (1 oz = 28.35 g; FPED uses oz-equivalents)
  Protein/meat (oz eq.) = 28.35 g     (same)
  Nuts/seeds (oz eq.) = 28.35 g       (~1 oz = 1 oz-equivalent protein)

Sources: USDA Center for Nutrition Policy and Promotion, MyPlate "What counts as
a cup-equivalent?" tables; FPED 1718 documentation; Stylianou 2021 SI S2.3 pp.
17-21 (HENI exposure derivation from FPED cup/oz-equivalents).

Usage:
    cd backend
    python -m heni_calculator.heni.etl.build_cnf_heni_composition
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


_THIS_DIR = Path(__file__).resolve().parent
# Derived artifacts (bridge + composition JSON + meta) live next to the
# HENI module that consumes them.
_DATA_DIR = _THIS_DIR.parent.parent / 'data'
# Immutable raw inputs sit at backend/raw_* alongside raw_cnf / raw_wafct.
_BACKEND_ROOT = _THIS_DIR.parents[2]
_FNDDS_DIR = _BACKEND_ROOT / 'raw_fndds' / 'FoodData_Central_survey_food_csv_2024-10-31'
_FPED_PATH = _BACKEND_ROOT / 'raw_fped' / 'FPED_1718.xls'

BRIDGE_PATH = _DATA_DIR / 'cnf_to_fndds_bridge.json'
COMPOSITION_PATH = _DATA_DIR / 'cnf_heni_composition.json'
COMPOSITION_META_PATH = _DATA_DIR / 'cnf_heni_composition_meta.json'


# FPED column -> HENI risk-factor key, with the per-cup/oz-eq -> g conversion
# factor. The conversion factor is determined by the FOOD CATEGORY of the
# column (not its unit) — e.g. D_TOTAL is cup-eq but the gram conversion
# depends on whether the source is milk (244g/cup-eq) or cheese (42.5g/cup-eq).
# We handle that ambiguity by using D_CHEESE + D_TOTAL together: D_MILK +
# D_YOGURT contribute at 244 g/cup-eq each, D_CHEESE at 42.5 g/cup-eq.

# Direct mappings (one FPED column -> one HENI factor at a fixed conversion).
# Form: (FPED column, HENI factor, grams per unit-equivalent)
_DIRECT_MAPPINGS = [
    # Fruits — single FPED column, 154 g/cup-eq
    ('F_TOTAL (cup eq.)',          'fruits',           154.0),
    # Vegetables — total covers all (DKGR, RED, STARCHY, OTHER, LEGUMES)
    # but HENI's `vegetables` factor excludes legumes (separate factor).
    # Use V_TOTAL - V_LEGUMES to avoid double-count.
    # Handled as a derived column below.
    # Legumes — both PF_LEGUMES (protein-side) and V_LEGUMES (vegetable-side)
    # describe the same intake; HENI counts legumes ONCE. Use V_LEGUMES as
    # the canonical FPED legume signal (165 g/cup-eq is the cooked-legume
    # USDA reference; using 172 here per FPED documentation).
    ('V_LEGUMES (cup eq.)',         'legumes',          172.0),
    # Whole grains — oz-eq at 28.35 g
    ('G_WHOLE (oz. eq.)',           'whole_grains',     28.35),
    # Red meat — PF_MEAT (beef/pork/lamb/veal; excludes poultry/seafood)
    ('PF_MEAT (oz. eq.)',           'red_meat',         28.35),
    # Processed meat — PF_CUREDMEAT (bacon, sausage, deli, frankfurter, ham)
    ('PF_CUREDMEAT (oz. eq.)',      'processed_meat',   28.35),
    # Nuts and seeds — PF_NUTSDS
    ('PF_NUTSDS (oz. eq.)',         'nuts_seeds',       28.35),
]

# Vegetables: HENI excludes legumes from `vegetables` (separate factor).
# Compute as V_TOTAL minus V_LEGUMES (both cup-eq at 165 g/cup).
_VEG_COL_TOTAL = 'V_TOTAL (cup eq.)'
_VEG_COL_LEGUMES = 'V_LEGUMES (cup eq.)'
_VEG_GRAMS_PER_CUP = 165.0

# Dairy: HENI's `milk` factor covers milk + yogurt + cheese (Stylianou groups
# them as a single dairy intake). FPED has D_MILK, D_YOGURT, D_CHEESE columns
# each in "cup eq." but the gram-per-cup-eq conversion differs:
#   D_MILK   -> 244 g/cup-eq (1 cup fluid milk)
#   D_YOGURT -> 244 g/cup-eq (1 cup yogurt)
#   D_CHEESE -> 42.5 g/cup-eq (1.5 oz natural cheese = 1 cup-eq dairy)
# Sum the three for the milk-factor mass.
_DAIRY_MAPPINGS = [
    ('D_MILK (cup eq.)',    244.0),
    ('D_YOGURT (cup eq.)',  244.0),
    ('D_CHEESE (cup eq.)',  42.5),
]

# SSB attribution: FPED has no direct SSB column. Use ADD_SUGARS as the
# primary signal, conditioned on the FNDDS WWEIA category being a beverage
# (handled at HENI runtime via the existing _NON_SSB_BEVERAGE_INDICATORS
# exclusion list). For Phase 2 we don't try to derive SSB from FPED — leave
# SSB attribution to runtime keyword detection on the CNF description (the
# existing code already handles this and is unaffected by the food-group
# refactor).


def _load_fped() -> pd.DataFrame:
    """Load FPED_1718.xls keyed on FOODCODE."""
    df = pd.read_excel(_FPED_PATH, sheet_name='FPED_1718', header=0)
    df['FOODCODE'] = df['FOODCODE'].astype('int64')
    logger.info('Loaded FPED 1718: %d rows', len(df))
    return df.set_index('FOODCODE')


def _compute_composition_for_fped_row(fped_row: pd.Series) -> Dict[str, float]:
    """Apply the column -> HENI mapping + cup/oz-eq -> g conversion.

    Returns a dict of {risk_factor: g per 100g food}. Zero-valued factors
    are kept (downstream code uses presence as a signal).
    """
    out: Dict[str, float] = {}

    # Direct columns
    for col, factor, g_per_eq in _DIRECT_MAPPINGS:
        v = float(fped_row.get(col, 0.0) or 0.0)
        out[factor] = round(v * g_per_eq, 4)

    # Vegetables (V_TOTAL - V_LEGUMES) to avoid double-count with `legumes`
    v_total = float(fped_row.get(_VEG_COL_TOTAL, 0.0) or 0.0)
    v_legumes = float(fped_row.get(_VEG_COL_LEGUMES, 0.0) or 0.0)
    v_only = max(0.0, v_total - v_legumes)
    out['vegetables'] = round(v_only * _VEG_GRAMS_PER_CUP, 4)

    # Dairy (sum milk + yogurt + cheese at their respective gram-per-cup-eq)
    dairy_g = 0.0
    for col, g_per_eq in _DAIRY_MAPPINGS:
        v = float(fped_row.get(col, 0.0) or 0.0)
        dairy_g += v * g_per_eq
    out['milk'] = round(dairy_g, 4)

    return out


def _content_hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def main() -> int:
    if not BRIDGE_PATH.exists():
        logger.error('Bridge JSON not found at %s — run build_cnf_to_fndds_bridge first',
                     BRIDGE_PATH)
        return 1
    bridge = json.loads(BRIDGE_PATH.read_text(encoding='utf-8'))
    bridges: Dict[str, Dict] = bridge.get('bridges', {})
    unbridged: list = bridge.get('unbridged', [])
    logger.info('Loaded bridge: %d bridged, %d unbridged', len(bridges), len(unbridged))

    fped = _load_fped()

    compositions: Dict[str, Dict] = {}
    no_fped_row = []
    for cnf_id_str, br in bridges.items():
        food_code = int(br['food_code'])
        if food_code not in fped.index:
            no_fped_row.append((cnf_id_str, food_code))
            continue
        comp = _compute_composition_for_fped_row(fped.loc[food_code])
        comp['_method'] = 'direct_fped'
        comp['_fdc_id'] = int(br['fdc_id'])
        comp['_food_code'] = food_code
        comp['_bridge_confidence'] = float(br['confidence'])
        compositions[cnf_id_str] = comp

    logger.info('Computed %d compositions; %d bridged foods had no FPED row',
                len(compositions), len(no_fped_row))
    if no_fped_row[:5]:
        logger.info('Sample no-FPED-row foods: %s', no_fped_row[:5])

    out = {
        '_provenance': {
            'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'fped_source': 'USDA FPED 1718',
            'fndds_source': 'FoodData Central Survey Foods 2024-10-31',
            'bridge_source': str(BRIDGE_PATH.name),
            'bridge_cnf_bridged': len(bridges),
            'compositions_computed': len(compositions),
            'compositions_no_fped_row': len(no_fped_row),
            'compositions_unbridged': len(unbridged),
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
        'no_fped_row_food_ids': sorted(int(c[0]) for c in no_fped_row),
    }

    serialised = json.dumps(out, indent=2, ensure_ascii=False)
    COMPOSITION_PATH.write_text(serialised, encoding='utf-8')

    # Meta with content hash + provenance for ETL determinism tracking.
    meta = {
        'date_utc': out['_provenance']['date_utc'],
        'content_sha256_16': _content_hash_str(serialised),
        'compositions_count': len(compositions),
        'no_fped_row_count': len(no_fped_row),
    }
    COMPOSITION_META_PATH.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    logger.info('Wrote %s (sha256:%s)', COMPOSITION_PATH, meta['content_sha256_16'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
