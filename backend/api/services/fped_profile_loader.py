"""Process-wide singleton loader for the full 37-component bridged FoodID -> FPED profile table.

The JSON at api/data/cnf_fped_profile.json is built once by
`api.services.etl.build_cnf_fped_profile`. This module loads it lazily on first
access and exposes `get_fped_profile_for_food(food_id)` returning a dict of
{component_key: value_per_100g_food} in native USDA Food Pattern units
(cup eq. / oz eq. / tsp eq. / g / drinks), or None when the food has no FPED-grounded
profile — i.e. it never bridged to a US FNDDS analog, or its analog has no FPED row
(region-specific dishes with no close US match). Callers must caveat None.

This is the shared data layer for FPED food-group exposure: the aggregator, recall /
scorecard researcher surfaces, dietary-pattern drivers, and decomposition QC all
read from here.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent          # api/services
_PROFILE_PATH = _THIS_DIR.parent / 'data' / 'cnf_fped_profile.json'

# Display units per component key (mirrors the ETL's _FPED_COLUMN_MAP). Exposed so
# frontend/explanation layers render "1.3 cup eq." without re-deriving units.
FPED_COMPONENT_UNITS: Dict[str, str] = {
    'fruit_total_cup': 'cup eq.', 'fruit_citrus_melon_berry_cup': 'cup eq.',
    'fruit_other_cup': 'cup eq.', 'fruit_juice_cup': 'cup eq.',
    'veg_total_cup': 'cup eq.', 'veg_dark_green_cup': 'cup eq.',
    'veg_red_orange_total_cup': 'cup eq.', 'veg_red_orange_tomato_cup': 'cup eq.',
    'veg_red_orange_other_cup': 'cup eq.', 'veg_starchy_total_cup': 'cup eq.',
    'veg_starchy_potato_cup': 'cup eq.', 'veg_starchy_other_cup': 'cup eq.',
    'veg_other_cup': 'cup eq.', 'veg_legumes_cup': 'cup eq.',
    'grain_total_oz': 'oz eq.', 'grain_whole_oz': 'oz eq.', 'grain_refined_oz': 'oz eq.',
    'protein_total_oz': 'oz eq.', 'protein_meat_poultry_seafood_oz': 'oz eq.',
    'protein_meat_oz': 'oz eq.', 'protein_cured_meat_oz': 'oz eq.',
    'protein_organ_oz': 'oz eq.', 'protein_poultry_oz': 'oz eq.',
    'protein_seafood_high_omega3_oz': 'oz eq.', 'protein_seafood_low_omega3_oz': 'oz eq.',
    'protein_eggs_oz': 'oz eq.', 'protein_soy_oz': 'oz eq.',
    'protein_nuts_seeds_oz': 'oz eq.', 'protein_legumes_oz': 'oz eq.',
    'dairy_total_cup': 'cup eq.', 'dairy_milk_cup': 'cup eq.',
    'dairy_yogurt_cup': 'cup eq.', 'dairy_cheese_cup': 'cup eq.',
    'oils_g': 'g', 'solid_fats_g': 'g', 'added_sugars_tsp': 'tsp eq.',
    'alcoholic_drinks': 'drinks',
}

_lock = threading.Lock()
_cache: Optional[Dict[int, Dict[str, float]]] = None


def _load_profiles() -> Dict[int, Dict[str, float]]:
    if not _PROFILE_PATH.exists():
        logger.info('No FPED profile file at %s; food-group exposure unavailable', _PROFILE_PATH)
        return {}
    try:
        raw = json.loads(_PROFILE_PATH.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('FPED profile file unreadable: %s', exc)
        return {}
    out: Dict[int, Dict[str, float]] = {}
    for cnf_id_str, prof in raw.get('profiles', {}).items():
        try:
            fid = int(cnf_id_str)
        except Exception:  # noqa: BLE001
            continue
        out[fid] = {k: float(v) for k, v in prof.items()
                    if not k.startswith('_') and isinstance(v, (int, float))}
    logger.info('Loaded FPED profile lookup: %d bridged foods covered (%s)',
                len(out), _PROFILE_PATH.name)
    return out


def get_profiles() -> Dict[int, Dict[str, float]]:
    """Full lookup table (lazy-loaded, cached process-wide)."""
    global _cache
    if _cache is not None:
        return _cache
    with _lock:
        if _cache is None:
            _cache = _load_profiles()
    return _cache


def get_fped_profile_for_food(food_id: int) -> Optional[Dict[str, float]]:
    """Return {component_key: value_per_100g} or None if the food has no FPED profile.

    A profile exists for any food (CNF or WAFCT) that bridged to a US FNDDS/FPED
    analog. None means the food never bridged — a region-specific food with no close
    US analog, or one whose match had no FPED row — and the caller must caveat it.
    """
    return get_profiles().get(int(food_id))


def reset_for_test() -> None:
    """Reset the singleton cache (test-helper; not for production use)."""
    global _cache
    with _lock:
        _cache = None
