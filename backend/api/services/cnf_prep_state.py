"""Process-wide singleton loader for the two-axis preparation-state tag.

Mirrors ``cnf_food_type.py`` pattern: the JSON at
``api/data/cnf_prep_state.json`` is built once by
``api.services.etl.build_cnf_prep_state`` (a one-time hybrid regex+LLM
classification across all CNF + WAFCT foods). This module loads it lazily
on first access.

The substitution culinary gate (``substitution_culinary.culinary_swap_plausible``)
consumes this to block raw↔cooked, fresh↔canned, fresh↔dried swaps that the
existing regex-on-description gate misses — most importantly the
fried-chicken → raw-chicken swap the Phase 1 substitution probe surfaced.

``prep_state_of(food_id)`` returns None when a food has no label — fall back
to "don't constrain" (matches the safe default elsewhere in the codebase).
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Dict, NamedTuple, Optional

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent          # api/services
_LABELS_PATH = _THIS_DIR.parent / 'data' / 'cnf_prep_state.json'

_lock = threading.Lock()
_cache: Optional[Dict[int, 'PrepStateTag']] = None


class PrepStateTag(NamedTuple):
    """Two-axis prep-state tag for a single CNF/WAFCT FoodID."""
    thermal_state: str
    preservation_state: str
    confidence: float
    source: str          # 'regex' | 'llm' | 'llm_overrode_regex'
    rationale: str


def _load_all() -> Dict[int, PrepStateTag]:
    if not _LABELS_PATH.exists():
        logger.info('No CNF prep-state file at %s; prep-state labels unavailable', _LABELS_PATH)
        return {}
    try:
        raw = json.loads(_LABELS_PATH.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('CNF prep-state file unreadable: %s', exc)
        return {}
    labels: Dict[int, PrepStateTag] = {}
    for fid_str, rec in raw.get('labels', {}).items():
        try:
            fid = int(fid_str)
        except Exception:  # noqa: BLE001
            continue
        labels[fid] = PrepStateTag(
            thermal_state=str(rec.get('thermal_state', 'unknown')),
            preservation_state=str(rec.get('preservation_state', 'unknown')),
            confidence=float(rec.get('confidence', 0.0) or 0.0),
            source=str(rec.get('source', '')),
            rationale=str(rec.get('rationale', '')),
        )
    logger.info('Loaded CNF prep-state labels: %d foods (%s)', len(labels), _LABELS_PATH.name)
    return labels


def _ensure_loaded() -> None:
    global _cache
    if _cache is not None:
        return
    with _lock:
        if _cache is None:
            _cache = _load_all()


def prep_state_of(food_id: int) -> Optional[PrepStateTag]:
    """Return the two-axis prep-state tag for a food, or None if unlabeled.

    None means "don't constrain": callers (e.g. the substitution culinary
    gate) should fall back to the existing regex-on-description behaviour
    rather than reject the swap.
    """
    _ensure_loaded()
    assert _cache is not None
    return _cache.get(int(food_id))


def thermal_state_of(food_id: int) -> Optional[str]:
    """Convenience accessor for the thermal axis. None when unlabeled."""
    rec = prep_state_of(food_id)
    return rec.thermal_state if rec is not None else None


def preservation_state_of(food_id: int) -> Optional[str]:
    """Convenience accessor for the preservation axis. None when unlabeled."""
    rec = prep_state_of(food_id)
    return rec.preservation_state if rec is not None else None


def reset_for_test() -> None:
    """Reset the singleton cache (test-helper; not for production use)."""
    global _cache
    with _lock:
        _cache = None
