
"""Process-wide singleton loader for the CNF single-vs-mixed food-type label.

The JSON at api/data/cnf_food_type.json is built once by
`api.services.etl.build_cnf_food_type` (a one-time LLM classification). This
module loads it lazily on first access and exposes whether a catalog food is a
*single ingredient* (apple, milk, a plain cut of meat, raw flour) or a *mixed
dish* (soup, pizza, casserole, sausage).

The decomposer uses this to keep its reconstruction-gated catalog override safe:
a free-text dish is only ever collapsed onto a food that is itself a measured
*mixed* dish, never onto a single ingredient ("chicken soup" -> a measured
chicken-noodle soup is fine; "beef stew" -> "Beef, ground" is not).

`is_mixed(food_id)` returns None when a food has no label — e.g. an unknown id. The
classification pass covers both CNF and WAFCT (FoodID >= 700000) foods; callers must
still treat None as "don't know" (the override simply does not fire), which is the
safe default for anything unlabeled.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent          # api/services
_LABELS_PATH = _THIS_DIR.parent / 'data' / 'cnf_food_type.json'

_lock = threading.Lock()
_cache: Optional[Dict[int, Dict]] = None


def _load_all() -> Dict[int, Dict]:
    """Parse cnf_food_type.json once into {food_id: {food_type, confidence, rationale}}."""
    if not _LABELS_PATH.exists():
        logger.info('No CNF food-type file at %s; single/mixed labels unavailable', _LABELS_PATH)
        return {}
    try:
        raw = json.loads(_LABELS_PATH.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('CNF food-type file unreadable: %s', exc)
        return {}
    labels: Dict[int, Dict] = {}
    for fid_str, rec in raw.get('labels', {}).items():
        try:
            fid = int(fid_str)
        except Exception:  # noqa: BLE001
            continue
        ftype = rec.get('food_type')
        if ftype not in ('single', 'mixed'):
            continue
        labels[fid] = {
            'food_type': ftype,
            'confidence': float(rec.get('confidence', 0.0) or 0.0),
            'rationale': str(rec.get('rationale', '')),
        }
    logger.info('Loaded CNF food-type labels: %d foods (%s)', len(labels), _LABELS_PATH.name)
    return labels


def _ensure_loaded() -> None:
    global _cache
    if _cache is not None:
        return
    with _lock:
        if _cache is None:
            _cache = _load_all()


def get_food_type(food_id: int) -> Optional[Dict]:
    """Return {food_type, confidence, rationale} for a labeled food, or None.

    None means the food has no label (e.g. an unknown id). Both CNF and WAFCT foods
    are covered by the classification pass.
    """
    _ensure_loaded()
    assert _cache is not None
    return _cache.get(int(food_id))


def is_mixed(food_id: int) -> Optional[bool]:
    """True if the food is a mixed dish, False if a single ingredient, None if unlabeled.

    Callers must treat None as "don't know" and fall back to the safe default
    (e.g. the decomposer does not override onto an unlabeled food).
    """
    rec = get_food_type(food_id)
    if rec is None:
        return None
    return rec['food_type'] == 'mixed'


def reset_for_test() -> None:
    """Reset the singleton cache (test-helper; not for production use)."""
    global _cache
    with _lock:
        _cache = None
