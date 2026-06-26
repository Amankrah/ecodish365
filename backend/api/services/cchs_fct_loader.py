"""CCHS Nutrition 2015 Food Consumption Table loader (PLATFORM-CODE-1.m, 2026-06-26).

Reads `backend/api/data/cchs_fct_2015.json` (built by
[`cchs_fct_ingest.py`](backend/api/services/etl/cchs_fct_ingest.py)) and
exposes a small documented surface to the population-reference views
and the cohort-vs-national comparator.

Singleton, lazy-loaded; thread-safe via the same `threading.Lock`
idiom used by [`dri_compendium.py:44-67`](backend/api/services/dri_compendium.py).

Public API:

* `get_fct_meta()`                                  → provenance dict
* `list_subgroups()`                                → all (code, name, main_group)
* `list_strata()`                                   → all published (sex, age_band) cells
* `list_body_weights()`                             → all body-weight rows
* `subgroup_meta(code)`                             → description + notes for one code
* `body_weight_for_stratum(sex, age_band)`          → mean / median + 95 % CI
* `cchs_age_band_for_years(age_years)`              → 1-3 / 4-8 / 9-13 / ... bucket
* `fct_intake_for_stratum(...)`                     → one cell's stats + suppression flag

Suppression contract: cells with `suppression_flag == 'F'` always return
`value=None, se=None`; cells with `suppression_flag == 'E'` carry a
numeric value but should be rendered with a caution flag in the UI.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_PATH = Path(__file__).resolve().parent.parent / 'data' / 'cchs_fct_2015.json'

_lock = threading.Lock()
_cache: Optional[Dict[str, Any]] = None
# Derived indexes built on first use. None means "not yet indexed".
_intake_index: Optional[Dict[Tuple[str, str, str, str, str, str], Dict[str, Any]]] = None
_subgroup_meta_index: Optional[Dict[str, Dict[str, Any]]] = None
_bodyweight_index: Optional[Dict[Tuple[str, str], Dict[str, Any]]] = None


# CCHS published age bands (Health Canada FCT 2015). Order matters — the
# numeric resolver picks the first band that contains the age.
_CCHS_AGE_BANDS = [
    (1.0,   3.999, '1-3 Years'),
    (4.0,   8.999, '4-8 Years'),
    (9.0,  13.999, '9-13 Years'),
    (14.0, 18.999, '14-18 Years'),
    (19.0, 30.999, '19-30 Years'),
    (31.0, 50.999, '31-50 Years'),
    (51.0, 70.999, '51-70 Years'),
    (71.0, 200.0,  '71+ Years'),
]


# ---------- Lazy load + indexes ------------------------------------------

def _load() -> Dict[str, Any]:
    if not _PATH.exists():
        logger.warning('CCHS-FCT artifact missing at %s; population-reference unavailable', _PATH)
        return {'meta': {}, 'long_rows': [], 'subgroups': [],
                'subgroup_meta': [], 'strata': [], 'body_weights': []}
    try:
        with _PATH.open('r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.warning('CCHS-FCT artifact unreadable: %s', exc)
        return {'meta': {}, 'long_rows': [], 'subgroups': [],
                'subgroup_meta': [], 'strata': [], 'body_weights': []}


def _ensure() -> Dict[str, Any]:
    global _cache, _intake_index, _subgroup_meta_index, _bodyweight_index
    if _cache is not None:
        return _cache
    with _lock:
        if _cache is None:
            _cache = _load()
            # Index the long rows for O(1) cell lookup. The key is the full
            # (subgroup, sex, age_band, basis, denom, statistic) tuple.
            idx: Dict[Tuple[str, str, str, str, str, str], Dict[str, Any]] = {}
            for r in _cache.get('long_rows', []):
                key = (
                    r['subgroup_code'], r['sex'], r['age_band'],
                    r['basis'], r['denom'], r['statistic'],
                )
                idx[key] = r
            _intake_index = idx
            _subgroup_meta_index = {m['code']: m for m in _cache.get('subgroup_meta', [])}
            _bodyweight_index = {(b['sex'], b['age_band']): b
                                 for b in _cache.get('body_weights', [])}
            logger.info('CCHS-FCT loaded: %d long rows, %d subgroups, %d strata, %d body-weight rows',
                        len(_cache.get('long_rows', [])),
                        len(_cache.get('subgroups', [])),
                        len(_cache.get('strata', [])),
                        len(_cache.get('body_weights', [])))
    return _cache


# ---------- Public API ----------------------------------------------------

def get_fct_meta() -> Dict[str, Any]:
    """Provenance + ingestion metadata. Safe before any other call."""
    return dict(_ensure().get('meta', {}))


def list_subgroups() -> List[Dict[str, Any]]:
    """All published subgroups: `[{code, name, main_group}, ...]`."""
    return list(_ensure().get('subgroups', []))


def list_strata() -> List[Dict[str, Any]]:
    """All published strata: `[{sex, age_band, n_respondents}, ...]`."""
    return list(_ensure().get('strata', []))


def list_body_weights() -> List[Dict[str, Any]]:
    """All body-weight reference rows."""
    return list(_ensure().get('body_weights', []))


def subgroup_meta(code: str) -> Optional[Dict[str, Any]]:
    """Return `{code, name, description, notes, main_group}` for one BNS
    subgroup code, or None when the code is not on Health Canada's
    published subgroup list (e.g. compound "OVERALL" rows)."""
    _ensure()
    if _subgroup_meta_index is None:
        return None
    return _subgroup_meta_index.get(code)


def body_weight_for_stratum(sex: str, age_band: str) -> Optional[Dict[str, Any]]:
    """Mean / median body weight + 95 % CI for one stratum. Returns None
    when the stratum is not published."""
    _ensure()
    if _bodyweight_index is None:
        return None
    return _bodyweight_index.get((sex.strip().lower(), age_band.strip()))


def cchs_age_band_for_years(age_years: Optional[float]) -> Optional[str]:
    """Resolve a numeric age to one of the CCHS-published age bands.
    Returns None for ages below 1 (the FCT begins at 1 year) or when age
    is unknown. Independent of the IOM DRI life-stage codes — the two
    band systems differ; the cross-stratum mapper sits at the API layer."""
    if age_years is None:
        return None
    try:
        a = float(age_years)
    except (TypeError, ValueError):
        return None
    for lo, hi, band in _CCHS_AGE_BANDS:
        if lo <= a <= hi:
            return band
    return None


def fct_intake_for_stratum(
    subgroup_code: str,
    sex: str,
    age_band: str,
    basis: str = 'eaters_only',
    denom: str = 'per_person',
) -> Optional[Dict[str, Any]]:
    """Return the full distribution stats for one (subgroup × stratum × basis × denom).

    Returns `{mean, se, p50, se_p50, p90, se_p90, p95, se_p95,
               n_respondents, pct_eaters, suppression_flag,
               subgroup_code, subgroup_name, main_group, sex, age_band,
               basis, denom}` or None when the cell is not published.

    Suppressed cells (`suppression_flag == 'F'`) carry None for every
    numeric statistic — caller must check the flag before formatting.
    """
    _ensure()
    if _intake_index is None:
        return None
    sex_n = sex.strip().lower()
    age_n = age_band.strip()
    out: Dict[str, Any] = {
        'subgroup_code':    subgroup_code,
        'subgroup_name':    None,
        'main_group':       None,
        'sex':              sex_n,
        'age_band':         age_n,
        'basis':            basis,
        'denom':            denom,
        'n_respondents':    None,
        'pct_eaters':       None,
        'suppression_flag': 'F',
    }
    any_cell_found = False
    # Stitch the four statistics into one cell row.
    for stat in ('mean', 'p50', 'p90', 'p95'):
        row = _intake_index.get((subgroup_code, sex_n, age_n, basis, denom, stat))
        if row is None:
            out[stat] = None
            out[f'se_{stat}'] = None
            continue
        any_cell_found = True
        out[stat] = row.get('value')
        out[f'se_{stat}'] = row.get('se')
        # First non-suppressed flag wins for the cell-level flag.
        if out['suppression_flag'] == 'F' and row.get('suppression_flag') != 'F':
            out['suppression_flag'] = row['suppression_flag']
        if out['n_respondents'] is None:
            out['n_respondents'] = row.get('n_respondents')
        if out['pct_eaters'] is None:
            out['pct_eaters'] = row.get('pct_eaters')
        if out['subgroup_name'] is None:
            out['subgroup_name'] = row.get('subgroup_name')
        if out['main_group'] is None:
            out['main_group'] = row.get('main_group')
    if not any_cell_found:
        return None
    return out


def reset_cache_for_tests() -> None:
    """Clear the cached artifact + indexes so the next call re-reads JSON.
    Do not call from production code."""
    global _cache, _intake_index, _subgroup_meta_index, _bodyweight_index
    with _lock:
        _cache = None
        _intake_index = None
        _subgroup_meta_index = None
        _bodyweight_index = None
