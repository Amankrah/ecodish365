"""Health Canada % Daily Value (%DV) reference, loaded from the committed JSON.

api/data/cnf_daily_values.json is the canonical table; it is byte-mirrored by the
frontend's cnfDailyValues.data.json so %DV display (frontend) and %DV-threshold
filtering (this module, used by the nutrient-discovery endpoint) can never drift. A
parity test pins the two `values` maps equal.

Keyed by CNF NutrientID; each id fixes the unit, so an amount and its DV are always in
the same unit. %DV = amount / dv * 100, computed on the per-100 g amount. Saturated fat
(606) sums with trans fat (605) via sum_with_nutrient_id.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

_PATH = Path(__file__).resolve().parent.parent / 'data' / 'cnf_daily_values.json'

_lock = threading.Lock()
_cache: Optional[Dict[int, Dict]] = None


def _load() -> Dict[int, Dict]:
    if not _PATH.exists():
        logger.warning('No daily-values file at %s; %%DV unavailable', _PATH)
        return {}
    try:
        raw = json.loads(_PATH.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('Daily-values file unreadable: %s', exc)
        return {}
    out: Dict[int, Dict] = {}
    for nid_str, rec in raw.get('values', {}).items():
        try:
            nid = int(nid_str)
        except (TypeError, ValueError):
            continue
        out[nid] = {
            'dv': float(rec['dv']),
            'unit': str(rec.get('unit', '')),
            'label': str(rec.get('label', '')),
            'sum_with_nutrient_id': (int(rec['sum_with_nutrient_id'])
                                     if rec.get('sum_with_nutrient_id') is not None else None),
        }
    return out


def _ensure() -> None:
    global _cache
    if _cache is not None:
        return
    with _lock:
        if _cache is None:
            _cache = _load()


def get_daily_value(nutrient_id: int) -> Optional[Dict]:
    """Return {dv, unit, label, sum_with_nutrient_id} for a nutrient, or None if it has no DV."""
    _ensure()
    assert _cache is not None
    return _cache.get(int(nutrient_id))


def has_daily_value(nutrient_id: int) -> bool:
    return get_daily_value(nutrient_id) is not None


def all_daily_values() -> Dict[int, Dict]:
    """Full {nutrient_id: {dv, unit, label, sum_with_nutrient_id}} table."""
    _ensure()
    assert _cache is not None
    return dict(_cache)


def percent_dv(
    nutrient_id: int,
    amount: float,
    lookup_other: Optional[Callable[[int], Optional[float]]] = None,
) -> Optional[float]:
    """%DV for one amount, or None when the nutrient has no DV. `lookup_other` supplies
    the trans-fat amount when summing saturated + trans (NutrientID 606)."""
    entry = get_daily_value(nutrient_id)
    if entry is None or not (entry['dv'] > 0):
        return None
    try:
        numerator = float(amount)
    except (TypeError, ValueError):
        return None
    other_id = entry.get('sum_with_nutrient_id')
    if other_id is not None and lookup_other is not None:
        other = lookup_other(int(other_id))
        if other is not None:
            try:
                numerator += float(other)
            except (TypeError, ValueError):
                pass
    return numerator / entry['dv'] * 100.0


def reset_for_test() -> None:
    global _cache
    with _lock:
        _cache = None
