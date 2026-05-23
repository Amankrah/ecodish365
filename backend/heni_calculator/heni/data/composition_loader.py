"""Process-wide singleton loader for the CNF -> HENI risk-factor composition table.

The JSON at backend/heni_calculator/data/cnf_heni_composition.json is built once
by `etl.build_cnf_heni_composition` (see HENI-CODE-1.y cause A resolution).
This module loads it lazily on first access and exposes a single function
`get_composition_for_food(food_id)` returning a dict of risk-factor -> g/100g
food, or None when the food has no FPED-grounded composition (in which case
the legacy literal-100 attribution path applies).
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent
_COMPOSITION_PATH = _THIS_DIR.parent.parent / 'data' / 'cnf_heni_composition.json'

_lock = threading.Lock()
_cache: Optional[Dict[int, Dict[str, float]]] = None
_loaded_from: Optional[str] = None


def _load_compositions() -> Dict[int, Dict[str, float]]:
    """Load and return {food_id -> {risk_factor: g_per_100g}} from disk.

    Strips the `_method`, `_fdc_id`, `_food_code`, `_bridge_confidence`
    metadata keys (they're audit-only) and keeps just the risk-factor masses.
    Returns an empty dict if the composition file doesn't exist (legacy path
    runs unchanged in that case).
    """
    if not _COMPOSITION_PATH.exists():
        logger.info('No composition file at %s; HENI uses legacy literal-100 attribution only',
                    _COMPOSITION_PATH)
        return {}
    try:
        raw = json.loads(_COMPOSITION_PATH.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('Composition file unreadable, falling back to legacy: %s', exc)
        return {}
    out: Dict[int, Dict[str, float]] = {}
    for cnf_id_str, comp in raw.get('compositions', {}).items():
        try:
            fid = int(cnf_id_str)
        except Exception:  # noqa: BLE001
            continue
        out[fid] = {k: float(v) for k, v in comp.items()
                    if not k.startswith('_') and isinstance(v, (int, float))}
    logger.info('Loaded HENI composition lookup: %d CNF foods covered (%s)',
                len(out), _COMPOSITION_PATH.name)
    return out


def get_compositions() -> Dict[int, Dict[str, float]]:
    """Return the full lookup table (lazy-loaded, cached process-wide)."""
    global _cache, _loaded_from
    if _cache is not None:
        return _cache
    with _lock:
        if _cache is None:
            _cache = _load_compositions()
            _loaded_from = str(_COMPOSITION_PATH)
    return _cache


def get_composition_for_food(food_id: int) -> Optional[Dict[str, float]]:
    """Return {risk_factor: g_per_100g_food} or None if the food isn't in the table."""
    return get_compositions().get(food_id)


def reset_for_test() -> None:
    """Reset the singleton cache (test-helper; not for production use)."""
    global _cache, _loaded_from
    with _lock:
        _cache = None
        _loaded_from = None
