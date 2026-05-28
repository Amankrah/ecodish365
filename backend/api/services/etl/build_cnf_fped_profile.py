"""One-time ETL: bridged FoodID (CNF + WAFCT) -> full 37-component USDA FPED profile.

The CNF/WAFCT -> FNDDS -> FPED bridge already exists (built by
`heni_calculator.heni.etl.build_cnf_to_fndds_bridge` + cached at
`heni_calculator/data/cnf_to_fndds_bridge.json`). The HENI composition ETL joins it
to FPED but collapses the result to 8 risk-factor buckets. This ETL persists the
*full* FPED profile — all 37 USDA Food Pattern components per 100 g of catalog food,
in their native cup / oz / tsp / gram / drink equivalents — so food-group exposure
can be surfaced as a first-class research/clinical layer (recall totals, guideline
gaps, dietary-pattern drivers, decomposition QC).

Reads:
    heni_calculator/data/cnf_to_fndds_bridge.json   (FoodID -> FNDDS food_code)
    raw_fped/FPED_1718.xls                           (food_code -> 37 components / 100 g)

Writes (api-level shared artifact, alongside cnf_corpus_embeddings):
    api/data/cnf_fped_profile.json
    api/data/cnf_fped_profile_meta.json

Deterministic — no LLM, no network. Re-run after any bridge refresh.

Usage (from backend/):
    python -m api.services.etl.build_cnf_fped_profile
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

_BACKEND_ROOT = Path(__file__).resolve().parents[3]  # api/services/etl -> backend
_FPED_PATH = _BACKEND_ROOT / 'raw_fped' / 'FPED_1718.xls'
_BRIDGE_PATH = _BACKEND_ROOT / 'heni_calculator' / 'data' / 'cnf_to_fndds_bridge.json'
_OUT_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cnf_fped_profile.json'
_META_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cnf_fped_profile_meta.json'

# FPED raw column -> (normalized key, display unit). Values are per 100 g of food in
# their native USDA Food Pattern units; we persist them as-is (no gram conversion —
# the cup/oz/tsp equivalents ARE the currency we want to expose).
_FPED_COLUMN_MAP: Dict[str, tuple] = {
    'F_TOTAL (cup eq.)':           ('fruit_total_cup', 'cup eq.'),
    'F_CITMLB (cup eq.)':          ('fruit_citrus_melon_berry_cup', 'cup eq.'),
    'F_OTHER (cup eq.)':           ('fruit_other_cup', 'cup eq.'),
    'F_JUICE (cup eq.)':           ('fruit_juice_cup', 'cup eq.'),
    'V_TOTAL (cup eq.)':           ('veg_total_cup', 'cup eq.'),
    'V_DRKGR (cup eq.)':           ('veg_dark_green_cup', 'cup eq.'),
    'V_REDOR_TOTAL (cup eq.)':     ('veg_red_orange_total_cup', 'cup eq.'),
    'V_REDOR_TOMATO (cup eq.)':    ('veg_red_orange_tomato_cup', 'cup eq.'),
    'V_REDOR_OTHER (cup eq.)':     ('veg_red_orange_other_cup', 'cup eq.'),
    'V_STARCHY_TOTAL (cup eq.)':   ('veg_starchy_total_cup', 'cup eq.'),
    'V_STARCHY_POTATO (cup eq.)':  ('veg_starchy_potato_cup', 'cup eq.'),
    'V_STARCHY_OTHER (cup eq.)':   ('veg_starchy_other_cup', 'cup eq.'),
    'V_OTHER (cup eq.)':           ('veg_other_cup', 'cup eq.'),
    'V_LEGUMES (cup eq.)':         ('veg_legumes_cup', 'cup eq.'),
    'G_TOTAL (oz. eq.)':           ('grain_total_oz', 'oz eq.'),
    'G_WHOLE (oz. eq.)':           ('grain_whole_oz', 'oz eq.'),
    'G_REFINED (oz. eq.)':         ('grain_refined_oz', 'oz eq.'),
    'PF_TOTAL (oz. eq.)':          ('protein_total_oz', 'oz eq.'),
    'PF_MPS_TOTAL (oz. eq.)':      ('protein_meat_poultry_seafood_oz', 'oz eq.'),
    'PF_MEAT (oz. eq.)':           ('protein_meat_oz', 'oz eq.'),
    'PF_CUREDMEAT (oz. eq.)':      ('protein_cured_meat_oz', 'oz eq.'),
    'PF_ORGAN (oz. eq.)':          ('protein_organ_oz', 'oz eq.'),
    'PF_POULT (oz. eq.)':          ('protein_poultry_oz', 'oz eq.'),
    'PF_SEAFD_HI (oz. eq.)':       ('protein_seafood_high_omega3_oz', 'oz eq.'),
    'PF_SEAFD_LOW (oz. eq.)':      ('protein_seafood_low_omega3_oz', 'oz eq.'),
    'PF_EGGS (oz. eq.)':           ('protein_eggs_oz', 'oz eq.'),
    'PF_SOY (oz. eq.)':            ('protein_soy_oz', 'oz eq.'),
    'PF_NUTSDS (oz. eq.)':         ('protein_nuts_seeds_oz', 'oz eq.'),
    'PF_LEGUMES (oz. eq.)':        ('protein_legumes_oz', 'oz eq.'),
    'D_TOTAL (cup eq.)':           ('dairy_total_cup', 'cup eq.'),
    'D_MILK (cup eq.)':            ('dairy_milk_cup', 'cup eq.'),
    'D_YOGURT (cup eq.)':          ('dairy_yogurt_cup', 'cup eq.'),
    'D_CHEESE (cup eq.)':          ('dairy_cheese_cup', 'cup eq.'),
    'OILS (grams)':                ('oils_g', 'g'),
    'SOLID_FATS (grams)':          ('solid_fats_g', 'g'),
    'ADD_SUGARS (tsp. eq.)':       ('added_sugars_tsp', 'tsp eq.'),
    'A_DRINKS (no. of drinks)':    ('alcoholic_drinks', 'drinks'),
}


def _load_fped() -> pd.DataFrame:
    df = pd.read_excel(_FPED_PATH, sheet_name='FPED_1718', header=0)
    df['FOODCODE'] = df['FOODCODE'].astype('int64')
    logger.info('Loaded FPED 1718: %d rows', len(df))
    return df.set_index('FOODCODE')


def _content_hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def main() -> int:
    if not _BRIDGE_PATH.exists():
        logger.error('Bridge JSON not found at %s — run build_cnf_to_fndds_bridge first', _BRIDGE_PATH)
        return 1
    bridge = json.loads(_BRIDGE_PATH.read_text(encoding='utf-8'))
    bridges: Dict[str, Dict] = bridge.get('bridges', {})
    logger.info('Loaded bridge: %d bridged CNF foods', len(bridges))

    fped = _load_fped()

    # Neither CNF nor WAFCT publishes USDA Food Pattern equivalents — both get them by
    # bridging to the closest US FNDDS analog. So inclusion is gated by *bridge
    # confidence* (the analog-match quality the bridge already scores), NOT by source
    # table: a 0.9-confidence "rice, boiled" match yields a valid grain profile whether
    # the row came from CNF or WAFCT. Foods that never bridged (region-specific dishes
    # with no US analog) simply have no profile and are caveated downstream.
    profiles: Dict[str, Dict] = {}
    no_fped_row = []
    for cnf_id_str, br in bridges.items():
        food_code = int(br['food_code'])
        if food_code not in fped.index:
            no_fped_row.append(int(cnf_id_str))
            continue
        row = fped.loc[food_code]
        prof = {key: round(float(row.get(col, 0.0) or 0.0), 4)
                for col, (key, _unit) in _FPED_COLUMN_MAP.items()}
        prof['_food_code'] = food_code
        prof['_fdc_id'] = int(br['fdc_id'])
        prof['_bridge_confidence'] = float(br['confidence'])
        profiles[cnf_id_str] = prof

    logger.info('Computed %d FPED profiles (CNF + bridged WAFCT); %d bridged foods had no FPED row',
                len(profiles), len(no_fped_row))

    out = {
        '_provenance': {
            'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'fped_source': 'USDA FPED 1718',
            'bridge_source': str(_BRIDGE_PATH.name),
            'components': {key: unit for _col, (key, unit) in _FPED_COLUMN_MAP.items()},
            'profiles_computed': len(profiles),
            'no_fped_row': len(no_fped_row),
            'units_note': (
                'Values are USDA Food Pattern equivalents per 100 g of the catalog food '
                '(borrowed from its bridged US FNDDS analog; cup eq. / oz eq. / tsp eq. '
                '/ grams / drinks), persisted in native units. Scale by mass_g/100 to '
                'get a serving total.'
            ),
        },
        'profiles': profiles,
        'no_fped_row_food_ids': sorted(no_fped_row),
    }
    serialised = json.dumps(out, indent=2, ensure_ascii=False)
    _OUT_PATH.write_text(serialised, encoding='utf-8')
    _META_PATH.write_text(json.dumps({
        'date_utc': out['_provenance']['date_utc'],
        'content_sha256_16': _content_hash(serialised),
        'profiles_count': len(profiles),
        'no_fped_row_count': len(no_fped_row),
        'component_count': len(_FPED_COLUMN_MAP),
    }, indent=2), encoding='utf-8')
    logger.info('Wrote %s (%d profiles, %d components each)',
                _OUT_PATH, len(profiles), len(_FPED_COLUMN_MAP))
    return 0


if __name__ == '__main__':
    sys.exit(main())
