"""Canonical food-category bridge — single source of truth for scorers
(FDC-MULTI-SOURCE, 2026-06-26).

Maps every CNF / WAFCT / FDC `FoodGroupID` in the multi-source catalogue
to a canonical category enum (see `_CANONICAL_CATEGORIES`) plus a
`cnf_equivalent_group_id` shim used by:

  - the Rust HSR kernel (which hard-codes CNF group IDs 1, 4, 14)
  - the environmental-LCA per-group lookup (keyed on CNF group names)

So each scorer's hard-coded CNF-id branches keep working unchanged for
WAFCT and FDC foods — Python translates the source-specific group ID to
its CNF equivalent before delegating. Scorers that want to branch on the
canonical concept (HENI risk-factor attribution, FCS NOVA defaults, HSR
FVNL highlights) read `canonical_category_for(food_id)` directly.

Mirrors the singleton-loader pattern of
[`cnf_food_type.py`](backend/api/services/cnf_food_type.py) and
[`cnf_prep_state.py`](backend/api/services/cnf_prep_state.py).
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_THIS_DIR    = Path(__file__).resolve().parent           # api/services
_BRIDGE_PATH = _THIS_DIR.parent / 'data' / 'food_group_canonical_category.json'

_CANONICAL_CATEGORIES: frozenset[str] = frozenset({
    'dairy', 'eggs', 'dairy_egg_combined',
    'fats_oils', 'fruits', 'vegetables', 'legumes', 'nuts_seeds',
    'cereals_grains', 'breakfast_cereals',
    'beef', 'pork', 'lamb_veal_game', 'poultry', 'fish',
    'sausages_luncheon',
    'beverages', 'alcoholic_beverages',
    'sweets', 'babyfoods', 'baked_products',
    'fast_foods', 'mixed_dishes', 'snacks',
    'soups_sauces', 'spices_herbs',
    'unknown',
})

# CNF FoodGroupName strings (matching CNF's NUTRIENT_GROUP.csv `FoodGroupName`
# column) that the environmental_impact_model `impact_factors_by_group` dict
# expects. Used by Phase 5 to translate canonical category → CNF group name
# for foods that don't carry a CNF-native name.
_CNF_GROUP_NAME_BY_ID: Dict[int, str] = {
    1:  'Dairy and Egg Products',
    2:  'Spices and Herbs',
    3:  'Babyfoods',
    4:  'Fats and Oils',
    5:  'Poultry Products',
    6:  'Soups, Sauces and Gravies',
    7:  'Sausages and Luncheon meats',
    8:  'Breakfast cereals',
    9:  'Fruits and fruit juices',
    10: 'Pork Products',
    11: 'Vegetables and Vegetable Products',
    12: 'Nuts and Seeds',
    13: 'Beef Products',
    14: 'Beverages',
    15: 'Finfish and Shellfish Products',
    16: 'Legumes and Legume Products',
    17: 'Lamb, Veal and Game',
    18: 'Baked Products',
    19: 'Sweets',
    20: 'Cereals, Grains and Pasta',
    21: 'Fast Foods',
    22: 'Mixed Dishes',
    25: 'Snacks',
}


_lock = threading.Lock()
_by_group_id:           Optional[Dict[int, Dict]] = None        # FoodGroupID -> {canonical, cnf_equiv, name}
_by_source_and_group:   Optional[Dict[tuple, Dict]] = None      # ('cnf'|'wafct'|'fdc', group_id) -> entry


def _load_bridge() -> tuple[Dict[int, Dict], Dict[tuple, Dict]]:
    """Parse the bridge JSON into two indexes — by FoodGroupID and by
    (source, native_group_id). Both are returned because callers reach
    the bridge from two angles: pipeline returns a FoodGroupID directly
    (primary case), and some callers (the smoke probe, the analytics
    page) work in source-native space."""
    if not _BRIDGE_PATH.exists():
        logger.warning('Bridge JSON not found at %s; canonical_category_for() will return "unknown"', _BRIDGE_PATH)
        return {}, {}
    try:
        raw = json.loads(_BRIDGE_PATH.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('Bridge JSON unreadable (%s); canonical_category_for() will return "unknown"', exc)
        return {}, {}
    by_gid: Dict[int, Dict] = {}
    by_src: Dict[tuple, Dict] = {}
    for source in ('cnf', 'wafct', 'fdc', 'ciqual'):
        block = raw.get(source, {})
        if not isinstance(block, dict):
            continue
        for gid_str, entry in block.items():
            try:
                gid = int(gid_str)
            except (TypeError, ValueError):
                continue
            if not isinstance(entry, dict):
                continue
            canonical = str(entry.get('canonical', 'unknown'))
            if canonical not in _CANONICAL_CATEGORIES:
                logger.warning('Bridge JSON: unknown canonical %r at %s/%s — coercing to "unknown"',
                               canonical, source, gid_str)
                canonical = 'unknown'
            cnf_eq = entry.get('cnf_equivalent_group_id')
            if cnf_eq is not None:
                try:
                    cnf_eq = int(cnf_eq)
                except (TypeError, ValueError):
                    cnf_eq = None
            normalised = {
                'canonical': canonical,
                'cnf_equivalent_group_id': cnf_eq,
                'source': source,
                'name': str(entry.get('name', '')),
            }
            by_gid[gid] = normalised
            by_src[(source, gid)] = normalised
    return by_gid, by_src


def _ensure_loaded() -> tuple[Dict[int, Dict], Dict[tuple, Dict]]:
    global _by_group_id, _by_source_and_group
    if _by_group_id is None or _by_source_and_group is None:
        with _lock:
            if _by_group_id is None or _by_source_and_group is None:
                _by_group_id, _by_source_and_group = _load_bridge()
    return _by_group_id, _by_source_and_group


# --- Primary public API --------------------------------------------------

def canonical_category_for_group(food_group_id: int) -> str:
    """Return the canonical category string for an ecodish365 `FoodGroupID`.

    Returns `'unknown'` if the group is not in the bridge (synthetic
    test IDs, future ingest before bridge update, etc.). Never raises."""
    if food_group_id is None:
        return 'unknown'
    by_gid, _ = _ensure_loaded()
    entry = by_gid.get(int(food_group_id))
    if entry is None:
        return 'unknown'
    return entry['canonical']


def canonical_category_for_food(food_id: int, pipeline=None) -> str:
    """Return the canonical category for a `FoodID`. Looks the food up in
    the CNF pipeline to find its `FoodGroupID`, then dispatches to
    `canonical_category_for_group`.

    `pipeline` is the optional explicit pipeline (e.g. for unit tests);
    when omitted, fetches the shared instance via `api.cnf_cache`.
    Returns `'unknown'` on any error or unknown food."""
    if food_id is None:
        return 'unknown'
    if pipeline is None:
        try:
            from api.cnf_cache import get_api_cnf_pipeline
            pipeline = get_api_cnf_pipeline()
        except Exception as exc:  # noqa: BLE001
            logger.debug('canonical_category_for_food: pipeline unavailable (%s)', exc)
            return 'unknown'
    try:
        df = pipeline.food_name_df
        rows = df[df['FoodID'] == int(food_id)]
        if rows.empty:
            return 'unknown'
        gid = rows.iloc[0]['FoodGroupID']
        if gid is None or (isinstance(gid, float) and gid != gid):  # NaN check
            return 'unknown'
        return canonical_category_for_group(int(gid))
    except Exception as exc:  # noqa: BLE001
        logger.debug('canonical_category_for_food(%s): %s', food_id, exc)
        return 'unknown'


def cnf_equivalent_group_id_for_group(food_group_id: int) -> Optional[int]:
    """Return the CNF FoodGroupID a non-CNF group maps to. Identity for CNF
    groups (1-25). Used by the HSR Rust kernel shim — by translating
    `(wafct, 50) → (cnf, 20)` before calling Rust, the existing word-boundary
    keyword overrides in the Rust kernel still fire correctly."""
    if food_group_id is None:
        return None
    by_gid, _ = _ensure_loaded()
    entry = by_gid.get(int(food_group_id))
    if entry is None:
        return None
    return entry['cnf_equivalent_group_id']


def cnf_equivalent_group_id_for_food(food_id: int, pipeline=None) -> Optional[int]:
    """Round-trip: FoodID -> FoodGroupID -> cnf_equivalent_group_id."""
    if food_id is None:
        return None
    if pipeline is None:
        try:
            from api.cnf_cache import get_api_cnf_pipeline
            pipeline = get_api_cnf_pipeline()
        except Exception:  # noqa: BLE001
            return None
    try:
        df = pipeline.food_name_df
        rows = df[df['FoodID'] == int(food_id)]
        if rows.empty:
            return None
        gid = rows.iloc[0]['FoodGroupID']
        if gid is None or (isinstance(gid, float) and gid != gid):
            return None
        return cnf_equivalent_group_id_for_group(int(gid))
    except Exception:  # noqa: BLE001
        return None


def cnf_group_name_for_food(food_id: int, pipeline=None) -> Optional[str]:
    """Return the CNF-canonical FoodGroupName for any source's food. Used by
    `environmental_impact_model.cnf_integrator.get_environmental_impact_factors`
    so WAFCT and FDC foods get the same per-group LCA centrals as their CNF
    equivalents (instead of the default-band fallback)."""
    cnf_eq = cnf_equivalent_group_id_for_food(food_id, pipeline=pipeline)
    if cnf_eq is None:
        return None
    return _CNF_GROUP_NAME_BY_ID.get(cnf_eq)


def canonical_categories() -> frozenset[str]:
    """Expose the canonical-category enum for callers (scorers and tests)
    that want to validate their hard-coded category strings."""
    return _CANONICAL_CATEGORIES


def reset_cache_for_tests() -> None:
    """Test helper — clears the loaded indexes so the next call re-reads
    the JSON. Do not call from production code."""
    global _by_group_id, _by_source_and_group
    with _lock:
        _by_group_id = None
        _by_source_and_group = None
