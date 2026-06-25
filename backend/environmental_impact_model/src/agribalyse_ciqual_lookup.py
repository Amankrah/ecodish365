"""Agribalyse 3.2 direct lookup by Ciqual code (CIQUAL-AGRIBALYSE-DIRECT, 2026-06-26).

CIQUAL foods carry their `alim_code` in `FoodCode` (e.g. `CIQUAL_24999`) —
the same integer Agribalyse keys its 2,425-entry catalogue on. This module
provides an O(1) lookup that bypasses the embedding+LLM `LCAMatcher` for
French foods: an identity-match against the shared Ciqual code is both
faster and strictly more precise than fuzzy matching.

Coverage: CIQUAL ships ~3,484 foods, Agribalyse ~2,425; ~2,300+ should
match by Ciqual code (~67 %). The remainder (mostly fast-food and very
specific recipes that Agribalyse does not model) fall through to the
existing CNF group-mean fallback at
[`cnf_integrator.get_environmental_impact_factors`](backend/environmental_impact_model/src/cnf_integrator.py).

Singleton, lazy-loaded; thread-safe via the standard threading.Lock idiom
mirroring [`food_group_category.py`](backend/api/services/food_group_category.py).
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent / 'data' / 'agribalyse_v32_catalog.json'
)

_lock = threading.Lock()
_index: Optional[Dict[int, Dict[str, Any]]] = None
_meta: Optional[Dict[str, Any]] = None


def _load() -> tuple[Dict[int, Dict[str, Any]], Dict[str, Any]]:
    """Parse the Agribalyse catalog once into `{ciqual_code: entry}` plus a
    small `_meta` dict (provenance, total rows, schema version). Returns
    empty structures if the file is unreadable so the lookup degrades
    gracefully to None on miss (and the caller falls back to group means).
    """
    if not _CATALOG_PATH.exists():
        logger.warning(
            'Agribalyse catalog not present at %s; CIQUAL-direct LCA lookup '
            'will return None for all calls.',
            _CATALOG_PATH,
        )
        return {}, {}
    try:
        with _CATALOG_PATH.open('r', encoding='utf-8') as fh:
            raw = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.warning('Agribalyse catalog unreadable: %s', exc)
        return {}, {}

    entries = raw.get('entries', [])
    idx: Dict[int, Dict[str, Any]] = {}
    skipped = 0
    for e in entries:
        ccode_raw = e.get('ciqual_code')
        if ccode_raw is None:
            skipped += 1
            continue
        try:
            ccode = int(ccode_raw)
        except (TypeError, ValueError):
            skipped += 1
            continue
        # Last-write-wins on duplicates (Agribalyse 3.2 ships unique ciqual_code
        # per entry in the released catalogue, but be defensive against future
        # release shape changes).
        idx[ccode] = e
    meta = {
        'schema_version':       raw.get('_schema_version'),
        'provenance_file':      raw.get('_provenance_file'),
        'meta_summary':         raw.get('_meta_summary', {}),
        'index_size':           len(idx),
        'skipped_entries':      skipped,
    }
    logger.info(
        'Agribalyse-Ciqual index loaded: %d entries indexed by ciqual_code (skipped %d).',
        len(idx), skipped,
    )
    return idx, meta


def _ensure_loaded() -> tuple[Dict[int, Dict[str, Any]], Dict[str, Any]]:
    global _index, _meta
    if _index is not None and _meta is not None:
        return _index, _meta
    with _lock:
        if _index is None or _meta is None:
            _index, _meta = _load()
    return _index, _meta


# ---------- Public API ----------------------------------------------------

def agribalyse_for_ciqual_code(alim_code: int) -> Optional[Dict[str, Any]]:
    """Return the raw Agribalyse entry for a given Ciqual `alim_code`.

    Caller-side semantics:
      - returns `None` if Agribalyse has no entry for this Ciqual code
        (~33 % of CIQUAL foods; consumer should fall back to its existing
        group-mean path).
      - returns the raw entry dict otherwise — the caller is responsible
        for selecting which fields to surface and for applying any unit
        conversions or methodology gating.
    """
    if alim_code is None:
        return None
    idx, _m = _ensure_loaded()
    return idx.get(int(alim_code))


def ciqual_alim_code_from_food_code(food_code: Any) -> Optional[int]:
    """Extract the integer Ciqual `alim_code` from a CIQUAL FoodCode string
    like `"CIQUAL_24999"`. Returns None for any non-conforming input —
    callers must treat that as "not a CIQUAL food" rather than an error.
    """
    if not food_code:
        return None
    s = str(food_code)
    if not s.startswith('CIQUAL_'):
        return None
    try:
        return int(s.split('_', 1)[1])
    except (ValueError, IndexError):
        return None


def get_index_meta() -> Dict[str, Any]:
    """Return the index's provenance + size metadata for surfacing in
    response provenance blocks."""
    _idx, meta = _ensure_loaded()
    return dict(meta)


def reset_cache_for_tests() -> None:
    """Test helper — clears the loaded index so the next call re-reads
    the JSON. Do not call from production code."""
    global _index, _meta
    with _lock:
        _index = None
        _meta = None
