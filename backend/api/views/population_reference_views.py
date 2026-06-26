"""Canadian population-reference endpoints (PLATFORM-CODE-1.m m.C, 2026-06-26).

Three views, all read-only:

* `GET /api/research/population-reference/canada/2015/`
    Index — published strata + every BNS subgroup + body-weight reference.
    Lets the frontend populate a stratum selector + a subgroup tree
    without loading the full 31 MB long-table.

* `GET /api/research/population-reference/canada/2015/intake/?subgroup=10B&sex=female&age_band=31-50&basis=eaters_only&denom=per_person`
    Single-cell intake stats for one subgroup × stratum. Carries
    suppression flag, body-weight reference, and the bridge-resolved
    CNF candidate list (clickable through to `/cnf/food/<id>`).

* `POST /api/research/population-reference/canada/2015/compare-cohort/`
    The headline endpoint. Body: `{cohort_recalls, stratum, basis, denom}`.
    Aggregates the cohort to BNS subgroups via the bridge, compares each
    subgroup's cohort intake distribution to the published national cell,
    and returns per-subgroup deltas + suppression-aware rendering.

Stateless. No persistence. Reuses the loaders + bridge built in
m.A / m.B with no new scoring logic.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.services.bns_aggregator import aggregate_cohort_to_bns
from api.services.cchs_fct_loader import (
    body_weight_for_stratum,
    fct_intake_for_stratum,
    get_fct_meta,
    list_body_weights,
    list_strata,
    list_subgroups,
    subgroup_meta,
)
from api.services.cnf_to_bns_bridge import (
    bns_subgroup_for_cnf,
    bridge_coverage_stats,
    cnf_food_ids_for_bns,
    get_bridge_meta,
)

logger = logging.getLogger(__name__)


_VALID_BASIS = {'all_person', 'eaters_only'}
_VALID_DENOM = {'per_person', 'per_kg_bw'}


def _clean_basis(raw: Any, default: str = 'eaters_only') -> str:
    s = str(raw or default).strip().lower()
    return s if s in _VALID_BASIS else default


def _clean_denom(raw: Any, default: str = 'per_person') -> str:
    s = str(raw or default).strip().lower()
    return s if s in _VALID_DENOM else default


def _provenance_block() -> Dict[str, Any]:
    """Single source of truth for the per-response provenance footer."""
    meta = get_fct_meta()
    bridge_meta = get_bridge_meta()
    bridge_stats = bridge_coverage_stats()
    return {
        'source':             meta.get('source'),
        'base_data':          meta.get('base_data'),
        'weighting':          meta.get('weighting'),
        'n_respondents_total': meta.get('n_respondents_total'),
        'ingestion_date':     meta.get('ingestion_date'),
        'bridge': {
            'embedding_model':       bridge_meta.get('embedding_model'),
            'ranking_model':         bridge_meta.get('ranking_model'),
            'min_confidence':        bridge_meta.get('min_bridge_confidence'),
            'built_date':            bridge_meta.get('date_utc'),
            'n_bridged':             bridge_stats.get('n_bridged'),
            'n_unbridged':           bridge_stats.get('n_unbridged'),
            'n_manual_overrides':    bridge_stats.get('n_overrides'),
            'mean_confidence':       bridge_stats.get('mean_confidence'),
        },
        'platform_item_id':   'PLATFORM-CODE-1.m',
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def population_reference_index(request) -> Response:
    """Index of strata + subgroups + body-weight reference. Lets the
    frontend populate the stratum + subgroup selectors in one round-trip."""
    return Response({
        'strata':       list_strata(),
        'subgroups':    list_subgroups(),
        'body_weights': list_body_weights(),
        'provenance':   _provenance_block(),
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def population_reference_intake(request) -> Response:
    """Single-cell intake stats for one (subgroup × stratum × basis × denom).

    Query params: subgroup, sex, age_band, [basis=eaters_only], [denom=per_person].
    """
    qs = request.query_params
    subgroup = (qs.get('subgroup') or '').strip()
    sex = (qs.get('sex') or '').strip().lower()
    age_band = (qs.get('age_band') or '').strip()
    basis = _clean_basis(qs.get('basis'))
    denom = _clean_denom(qs.get('denom'))
    if not subgroup or not sex or not age_band:
        return Response(
            {'error': 'subgroup, sex, age_band are all required query params'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Health Canada publishes ~180 subgroups × 25 strata × 2 bases × 2 denoms,
    # but the long-format table only carries rows where at least one statistic
    # was released. Combinations where every statistic is suppressed (CV > 33%,
    # n_eaters < 30) or simply not published return None from the loader. That
    # is genuinely meaningful data — "Canadians in this stratum don't eat
    # enough of this food for Health Canada to release a statistic" — so we
    # surface it as a graceful 200 with a synthetic suppressed cell + a
    # `not_published` flag rather than 404'ing the UI into an error banner.
    cell = fct_intake_for_stratum(subgroup, sex, age_band, basis=basis, denom=denom)
    not_published = cell is None
    if cell is None:
        cell = {
            'subgroup_code':    subgroup,
            'subgroup_name':    None,
            'main_group':       None,
            'sex':              sex,
            'age_band':         age_band,
            'basis':            basis,
            'denom':            denom,
            'n_respondents':    None,
            'pct_eaters':       None,
            'suppression_flag': 'F',
            'mean':             None, 'se_mean': None,
            'p50':              None, 'se_p50':  None,
            'p90':              None, 'se_p90':  None,
            'p95':              None, 'se_p95':  None,
        }
    bw = body_weight_for_stratum(sex, age_band)
    meta = subgroup_meta(subgroup) or {}
    if not cell.get('subgroup_name') and meta.get('name'):
        cell['subgroup_name'] = meta.get('name')
        cell['main_group']    = meta.get('main_group')
    # The CNF→BNS bridge intentionally maps both CNF (IDs 1-7021) and WAFCT
    # foods (IDs 700000+), since both can plausibly belong to a Health Canada
    # subgroup (pasta is pasta everywhere). For this Canadian-specific
    # population-reference surface, however, the candidate list should only
    # show Canadian Nutrient File foods — WAFCT entries belong to West
    # African diet surveys and will resurface in a future West African
    # population-reference layer using the same bridge.
    canadian_food_ids = [fid for fid in cnf_food_ids_for_bns(subgroup) if 1 <= fid <= 7021]
    candidates_preview = canadian_food_ids[:200]
    candidates_named = _resolve_food_descriptions(candidates_preview)
    return Response({
        'cell':              cell,
        'not_published':     not_published,
        'subgroup_meta':     meta,
        'body_weight':       bw,
        'cnf_candidates':    candidates_named,
        'n_cnf_candidates':  len(canadian_food_ids),
        'provenance':        _provenance_block(),
    }, status=status.HTTP_200_OK)


def _resolve_food_descriptions(food_ids: List[int]) -> List[Dict[str, Any]]:
    """Look up CNF / WAFCT food descriptions for a list of FoodIDs and
    return `[{food_id, description, source}, ...]` preserving order. Logs
    once on cache load and falls back to a bare `{food_id, description: ''}`
    entry when the pipeline is unavailable or a FoodID is missing — the
    UI chip just shows the numeric ID in that case."""
    if not food_ids:
        return []
    try:
        from api.cnf_cache import get_api_cnf_pipeline
        pipe = get_api_cnf_pipeline()
        df = pipe.food_name_df
        # Build a one-shot id -> (description, source) map for the requested IDs only.
        wanted = set(int(f) for f in food_ids)
        subset = df[df['FoodID'].isin(wanted)]
        lookup: Dict[int, Dict[str, Any]] = {}
        for _, row in subset.iterrows():
            fid = int(row['FoodID'])
            lookup[fid] = {
                'description': str(row.get('FoodDescription') or '').strip(),
                'source':      str(row.get('source') or 'cnf').strip(),
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning('Could not resolve food descriptions: %s', exc)
        lookup = {}
    out: List[Dict[str, Any]] = []
    for fid in food_ids:
        info = lookup.get(int(fid), {'description': '', 'source': 'unknown'})
        out.append({
            'food_id':     int(fid),
            'description': info['description'],
            'source':      info['source'],
        })
    return out


@api_view(['POST'])
@permission_classes([AllowAny])
def population_reference_compare_cohort(request) -> Response:
    """Compare a cohort's per-subgroup intake distribution to the
    published Canadian national distribution.

    Body:
        {
          "cohort_recalls": [
            {"respondent_id": "S1", "day_id": "day_1",
             "foods": [{"food_id": 4067, "mass_g": 60}, ...]},
            ...
          ],
          "stratum": {"sex": "female", "age_band": "31-50 Years"},
          "basis": "eaters_only",
          "denom": "per_person"
        }
    """
    body = request.data if isinstance(request.data, dict) else {}
    recalls_raw = body.get('cohort_recalls')
    if not isinstance(recalls_raw, list) or not recalls_raw:
        return Response(
            {'error': 'cohort_recalls must be a non-empty list of recall objects'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    stratum = body.get('stratum') or {}
    sex = (stratum.get('sex') or '').strip().lower()
    age_band = (stratum.get('age_band') or '').strip()
    if not sex or not age_band:
        return Response(
            {'error': 'stratum.sex and stratum.age_band are both required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    basis = _clean_basis(body.get('basis'))
    denom = _clean_denom(body.get('denom'))

    # Normalise recalls to the food-list shape the aggregator expects.
    food_lists: List[List[Dict[str, Any]]] = []
    for r in recalls_raw:
        if not isinstance(r, dict):
            continue
        foods = r.get('foods')
        if not isinstance(foods, list) or not foods:
            continue
        food_lists.append(foods)
    if not food_lists:
        return Response(
            {'error': 'no recalls with a non-empty foods list'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cohort_agg = aggregate_cohort_to_bns(food_lists)
    bw_national = body_weight_for_stratum(sex, age_band)

    # Per-subgroup join: cohort distribution vs published cell.
    rows: List[Dict[str, Any]] = []
    for sub in cohort_agg['per_subgroup']:
        code = sub['bns_code']
        national = fct_intake_for_stratum(code, sex, age_band, basis=basis, denom=denom)
        meta = subgroup_meta(code) or {}
        # Median / P90 deltas only meaningful when (a) national cell is
        # published, (b) national flag is not 'F' (fully suppressed),
        # and (c) cohort has at least one eater for the subgroup.
        national_suppressed = national is None or (national.get('suppression_flag') == 'F')
        cohort_median_g = sub.get('median_g_eaters') if basis == 'eaters_only' else sub.get('median_g_all')
        cohort_p90_g    = sub.get('p90_g_eaters')    if basis == 'eaters_only' else sub.get('p90_g_all')

        national_median = None if national_suppressed else national.get('p50')
        national_p90    = None if national_suppressed else national.get('p90')
        national_mean   = None if national_suppressed else national.get('mean')

        delta_median = None
        delta_p90 = None
        if cohort_median_g is not None and national_median is not None:
            delta_median = round(float(cohort_median_g) - float(national_median), 2)
        if cohort_p90_g is not None and national_p90 is not None:
            delta_p90 = round(float(cohort_p90_g) - float(national_p90), 2)

        rows.append({
            'bns_code':              code,
            'subgroup_name':         meta.get('name'),
            'main_group':            meta.get('main_group'),
            'cohort_n_eaters':       sub.get('n_eaters'),
            'cohort_pct_eaters':     sub.get('pct_eaters'),
            'cohort_median':         cohort_median_g,
            'cohort_p90':            cohort_p90_g,
            'cohort_mean':           sub.get('mean_g_eaters') if basis == 'eaters_only' else sub.get('mean_g_all'),
            'national_median':       national_median,
            'national_p90':          national_p90,
            'national_mean':         national_mean,
            'national_pct_eaters':   None if national_suppressed else national.get('pct_eaters'),
            'national_n_respondents': None if national is None else national.get('n_respondents'),
            'delta_median':          delta_median,
            'delta_p90':             delta_p90,
            'national_suppression_flag': None if national is None else national.get('suppression_flag'),
            'mean_bridge_confidence': sub.get('mean_bridge_confidence'),
        })

    # Sort by absolute median delta (largest first) so the UI surfaces
    # the most divergent subgroups at the top.
    rows.sort(key=lambda r: abs(r.get('delta_median') or 0), reverse=True)

    return Response({
        'result': {
            'meta': {
                'n_recalls': cohort_agg['n_recalls'],
                'stratum':   {'sex': sex, 'age_band': age_band},
                'basis':     basis,
                'denom':     denom,
            },
            'per_subgroup': rows,
            'coverage':     cohort_agg['coverage'],
            'body_weight_national': bw_national,
            'provenance':   _provenance_block(),
        },
    }, status=status.HTTP_200_OK)


# Defensive cap on batch lookups — same convention as `_MAX_FOODS_PER_RECALL`
# in [`cohort_views.py`](backend/api/views/cohort_views.py:48).
_MAX_FOODS_PER_BATCH = 200


@api_view(['POST'])
@permission_classes([AllowAny])
def population_reference_for_foods(request) -> Response:
    """Batch lookup: for N CNF food_ids + a Canadian stratum, return the
    BNS subgroup + national intake distribution per food. Feeds the
    per-food tooltip on [`/research/nutrient-analysis`](frontend/src/app/research/nutrient-analysis/page.tsx)
    (PLATFORM-CODE-1.m m.D.5).

    Body:
        {
          "food_ids": [4067, 61, 1696, ...],
          "sex":      "female",
          "age_band": "31-50 Years",
          "basis":    "eaters_only",
          "denom":    "per_person"
        }

    Returns `{result: {stratum, basis, denom, per_food: {food_id_str: row | null}, provenance}}`
    where each row carries `bns_code, bns_name, main_group, bridge_confidence,
    bridge_source, national_{median, p90, p95, mean}, se_p50, se_p90,
    n_respondents, pct_eaters, suppression_flag`.

    Null per_food entries flag foods that are unbridged OR whose national
    cell is fully suppressed (`F`). `E`-flagged cells return the value
    with the flag intact so the UI can render the caution badge.
    """
    body = request.data if isinstance(request.data, dict) else {}
    food_ids_raw = body.get('food_ids')
    if not isinstance(food_ids_raw, list) or not food_ids_raw:
        return Response(
            {'error': 'food_ids must be a non-empty list of CNF FoodIDs'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(food_ids_raw) > _MAX_FOODS_PER_BATCH:
        return Response(
            {'error': f'food_ids list too large; limit is {_MAX_FOODS_PER_BATCH} per request',
             'received': len(food_ids_raw)},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    sex = str(body.get('sex') or '').strip().lower()
    age_band = str(body.get('age_band') or '').strip()
    if not sex or not age_band:
        return Response(
            {'error': 'sex and age_band are both required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    basis = _clean_basis(body.get('basis'))
    denom = _clean_denom(body.get('denom'))

    # Coerce inputs to int once. Skip anything that's not parseable rather
    # than 400ing — the frontend may include negative / null food_ids while
    # the user is editing the food list.
    food_ids: List[int] = []
    for raw in food_ids_raw:
        try:
            fid = int(raw)
        except (TypeError, ValueError):
            continue
        if fid > 0:
            food_ids.append(fid)

    per_food: Dict[str, Any] = {}
    for fid in food_ids:
        info = bns_subgroup_for_cnf(fid)
        if info is None:
            per_food[str(fid)] = None
            continue
        bns_code = info['bns_code']
        cell = fct_intake_for_stratum(bns_code, sex, age_band, basis=basis, denom=denom)
        if cell is None or cell.get('suppression_flag') == 'F':
            # Cell unpublished or fully suppressed — surface as null so the
            # UI can render the "—" placeholder uniformly.
            per_food[str(fid)] = None
            continue
        meta = subgroup_meta(bns_code) or {}
        per_food[str(fid)] = {
            'bns_code':          bns_code,
            'bns_name':          meta.get('name') or cell.get('subgroup_name'),
            'main_group':        meta.get('main_group') or cell.get('main_group'),
            'bridge_confidence': info.get('confidence'),
            'bridge_source':     info.get('source'),
            'national_median':   cell.get('p50'),
            'national_p90':      cell.get('p90'),
            'national_p95':      cell.get('p95'),
            'national_mean':     cell.get('mean'),
            'se_p50':            cell.get('se_p50'),
            'se_p90':            cell.get('se_p90'),
            'n_respondents':     cell.get('n_respondents'),
            'pct_eaters':        cell.get('pct_eaters'),
            'suppression_flag':  cell.get('suppression_flag'),
        }

    return Response({
        'result': {
            'stratum':    {'sex': sex, 'age_band': age_band},
            'basis':      basis,
            'denom':      denom,
            'per_food':   per_food,
            'provenance': _provenance_block(),
        },
    }, status=status.HTTP_200_OK)
