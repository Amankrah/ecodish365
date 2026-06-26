"""CNF FoodID → BNS subgroup bridge loader (PLATFORM-CODE-1.m m.B, 2026-06-26).

Singleton loader for the LLM-built `cnf_to_bns_subgroup_bridge.json`
artifact plus a hand-curated overrides sidecar. Overrides win over LLM
ranks so a researcher can lock high-stakes subgroups (the 30-or-so
driving HEFI / HENI weights) by editing a JSON without re-running the
$1-2 LLM build.

Same `threading.Lock` singleton idiom as [`cchs_fct_loader.py`](backend/api/services/cchs_fct_loader.py)
and [`dri_compendium.py:44-67`](backend/api/services/dri_compendium.py).

Public API:

* `bns_subgroup_for_cnf(food_id) → {bns_code, confidence, source, rationale} | None`
* `cnf_food_ids_for_bns(bns_code) → List[int]`
* `bridge_coverage_stats() → {n_bridged, n_unbridged, n_overrides, mean_confidence, by_source, n_per_main_group}`
* `get_bridge_meta() → provenance dict`
"""
from __future__ import annotations

import json
import logging
import threading
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
_BRIDGE_PATH = _DATA_DIR / 'cnf_to_bns_subgroup_bridge.json'
_OVERRIDES_PATH = _DATA_DIR / 'cnf_to_bns_subgroup_bridge_overrides.json'

_lock = threading.Lock()
_cache: Optional[Dict[str, Any]] = None
_inverted: Optional[Dict[str, List[int]]] = None


def _load_overrides() -> Dict[str, Dict[str, Any]]:
    """Read the hand-curated overrides sidecar. Returns
    `{food_id_str: {bns_code, confidence, source='manual', rationale}}`."""
    if not _OVERRIDES_PATH.exists():
        return {}
    try:
        raw = json.loads(_OVERRIDES_PATH.read_text(encoding='utf-8'))
        out: Dict[str, Dict[str, Any]] = {}
        for k, v in (raw.get('overrides') or {}).items():
            if not isinstance(v, dict):
                continue
            code = v.get('bns_code')
            if not code:
                continue
            out[str(k)] = {
                'bns_code':   str(code),
                'confidence': float(v.get('confidence', 1.0)),
                'rationale':  str(v.get('rationale', '')),
                'source':     'manual',
            }
        return out
    except Exception as exc:  # noqa: BLE001
        logger.warning('CNF→BNS overrides unreadable: %s', exc)
        return {}


def _load() -> Dict[str, Any]:
    """Read the LLM-built bridge JSON, then merge overrides on top.
    Overrides win. Returns the merged `bridges` dict + provenance."""
    bridges: Dict[str, Dict[str, Any]] = {}
    unbridged: List[int] = []
    meta: Dict[str, Any] = {}
    if not _BRIDGE_PATH.exists():
        logger.warning('CNF→BNS bridge artifact missing at %s; '
                       'bridge_subgroup_for_cnf will return None for every food '
                       '(except manual overrides). Run '
                       '`python -m api.services.etl.build_cnf_to_bns_bridge` to build.',
                       _BRIDGE_PATH)
    else:
        try:
            raw = json.loads(_BRIDGE_PATH.read_text(encoding='utf-8'))
            meta = raw.get('_provenance', {})
            for k, v in (raw.get('bridges') or {}).items():
                if not isinstance(v, dict) or not v.get('bns_code'):
                    continue
                bridges[str(k)] = {
                    'bns_code':   str(v['bns_code']),
                    'confidence': float(v.get('confidence', 0.0)),
                    'rationale':  str(v.get('rationale', '')),
                    'source':     str(v.get('source', 'llm')),
                }
            unbridged = list(raw.get('unbridged') or [])
        except Exception as exc:  # noqa: BLE001
            logger.warning('CNF→BNS bridge unreadable: %s', exc)

    overrides = _load_overrides()
    for k, v in overrides.items():
        bridges[k] = v   # manual wins
    logger.info('CNF→BNS bridge loaded: %d bridged (%d overrides), %d unbridged',
                len(bridges), len(overrides), len(unbridged))
    return {'meta': meta, 'bridges': bridges, 'unbridged': unbridged,
            'n_overrides': len(overrides)}


def _ensure() -> Dict[str, Any]:
    global _cache, _inverted
    if _cache is not None:
        return _cache
    with _lock:
        if _cache is None:
            _cache = _load()
            inv: Dict[str, List[int]] = {}
            for fid_str, info in _cache['bridges'].items():
                try:
                    fid = int(fid_str)
                except (TypeError, ValueError):
                    continue
                inv.setdefault(info['bns_code'], []).append(fid)
            _inverted = {k: sorted(v) for k, v in inv.items()}
    return _cache


# ---------- Public API ----------------------------------------------------

def bns_subgroup_for_cnf(food_id: int) -> Optional[Dict[str, Any]]:
    """Return the bridged BNS subgroup for one CNF FoodID, or None if the
    food was not bridged at or above the confidence floor + has no
    manual override. The dict shape is
    `{bns_code, confidence, source ∈ {'llm','manual'}, rationale}`."""
    cache = _ensure()
    return cache['bridges'].get(str(int(food_id)))


def cnf_food_ids_for_bns(bns_code: str) -> List[int]:
    """Inverted lookup: every CNF FoodID currently bridged to this BNS
    subgroup. Useful for the population-reference browse page so each
    subgroup can show the CNF candidate list with clickable links.

    Parent-code roll-up: BNS codes follow a `<digits>[<letter>]` shape
    where bare-digit codes (`2`, `10`, `16`) are parent buckets and
    digit+letter codes (`2A`, `10D`, `16A`) are leaves. The bridge always
    targets the most specific leaf, so a researcher who clicks the
    parent `16 EGGS` would otherwise see zero foods even when 16A is
    fully populated. This helper rolls up every leaf under a parent
    when the supplied code is bare-digit; leaf codes return only their
    direct matches as before. Compound published roll-ups like
    `"1 to 8"` GRAIN PRODUCTS-OVERALL return only their direct matches
    (which are always zero — they're FCT-side aggregates, not bridge
    targets).
    """
    _ensure()
    inv = _inverted or {}
    code = str(bns_code).strip()
    direct = list(inv.get(code, []))
    # Detect a bare-digit parent code. Roll up every leaf `<code><letter>`.
    if code.isdigit():
        rolled: List[int] = list(direct)
        seen = set(rolled)
        for k, ids in inv.items():
            if len(k) > len(code) and k.startswith(code) and k[len(code):].isalpha():
                for fid in ids:
                    if fid not in seen:
                        rolled.append(fid)
                        seen.add(fid)
        return sorted(rolled)
    return direct


def bridge_coverage_stats() -> Dict[str, Any]:
    """Summary stats for diagnostics + the population-reference response
    provenance block."""
    cache = _ensure()
    bridges = cache['bridges']
    if not bridges:
        return {
            'n_bridged':         0,
            'n_unbridged':       len(cache['unbridged']),
            'n_overrides':       cache.get('n_overrides', 0),
            'mean_confidence':   None,
            'by_source':         {},
            'top_subgroups':     [],
        }
    confs = [v['confidence'] for v in bridges.values()]
    src = Counter(v.get('source', 'llm') for v in bridges.values())
    sg = Counter(v['bns_code'] for v in bridges.values())
    return {
        'n_bridged':       len(bridges),
        'n_unbridged':     len(cache['unbridged']),
        'n_overrides':     cache.get('n_overrides', 0),
        'mean_confidence': round(sum(confs) / len(confs), 3) if confs else None,
        'by_source':       dict(src),
        'top_subgroups':   sg.most_common(10),
    }


def get_bridge_meta() -> Dict[str, Any]:
    """Provenance block from the LLM build (model, top-k, dates)."""
    cache = _ensure()
    return dict(cache.get('meta', {}))


def reset_cache_for_tests() -> None:
    """Clear the cache so the next call re-reads from disk. Test helper."""
    global _cache, _inverted
    with _lock:
        _cache = None
        _inverted = None
