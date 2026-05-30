"""Unified profile score endpoint — runs all six scorers in parallel on the server."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.test import APIRequestFactory

from api.services.profile_meta import compute_profile_meta

logger = logging.getLogger(__name__)

_factory = APIRequestFactory()

METRIC_KEYS = ('hefi', 'heni', 'hsr', 'fcs', 'environmental', 'dietary_pattern')


def _call_view(view_fn, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    request = _factory.post(path, payload, format='json')
    response = view_fn(request)
    if hasattr(response, 'data'):
        data = response.data
        if isinstance(data, dict) and response.status_code >= 400:
            raise ValueError(data.get('error') or data.get('details') or str(data))
        return data if isinstance(data, dict) else {'data': data}
    raise ValueError(f'Unexpected response from {path}')


def _build_payloads(
    composition: List[Dict[str, Any]],
    user_type: str,
    decomposition_provenance: Optional[str],
    multi_day_label: Optional[str],
    enable_lca: bool,
) -> Dict[str, Dict[str, Any]]:
    foods_hefi = [{'food_id': r['food_id'], 'amount_g': r['mass_g']} for r in composition]
    heni_meal = [{'food_id': r['food_id'], 'amount': r['mass_g'], 'unit': 'g'} for r in composition]
    ids = [r['food_id'] for r in composition]
    masses = [r['mass_g'] for r in composition]
    names = [r.get('food_description') or f"Food {r['food_id']}" for r in composition]
    decomp = {'decomposition_provenance': decomposition_provenance} if decomposition_provenance else {}
    return {
        'hefi': {'foods': foods_hefi, 'user_type': user_type, **decomp},
        'heni': {'meal': heni_meal, 'user_type': user_type, **decomp},
        'hsr': {
            'food_ids': ids,
            'serving_sizes': masses,
            'analysis_level': 'detailed',
            'include_alternatives': False,
            'include_meal_insights': True,
            'from_recall24h': len(ids) > 1,
            'user_type': user_type,
            **decomp,
        },
        'fcs': {
            'food_ids': ids,
            'food_names': names,
            'serving_sizes': masses,
            'user_type': user_type,
            **decomp,
        },
        'environmental': {
            'foods': [{'food_id': i, 'quantity': m} for i, m in zip(ids, masses)],
            'user_type': user_type,
            'enable_lca_matcher': enable_lca,
            **decomp,
        },
        'dietary_pattern': {
            'foods': [{'food_id': i, 'mass_g': m} for i, m in zip(ids, masses)],
            'user_type': user_type,
            'include_narrative': user_type != 'individual',
            **({'meta_label': multi_day_label} if multi_day_label else {}),
            **decomp,
        },
    }


def _run_metrics(
    payloads: Dict[str, Dict[str, Any]],
    metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    from api.views import hefi_views, heni_views, hsr_views_consolidated, fcs_views, environmental_views
    from api.views import cnf_ai_search_views

    runners = {
        'hefi': (hefi_views.hefi_calculate, '/api/hefi/calculate/'),
        'heni': (heni_views.heni_calculate, '/api/heni/calculate/'),
        'hsr': (hsr_views_consolidated.calculate_hsr, '/api/hsr/calculate/'),
        'fcs': (fcs_views.fcs_calculate, '/api/fcs/calculate/'),
        'environmental': (environmental_views.environmental_impact, '/api/environmental-impact/'),
        'dietary_pattern': (cnf_ai_search_views.dietary_pattern_classify, '/api/dietary-pattern/classify/'),
    }
    keys = [k for k in (metrics or METRIC_KEYS) if k in runners]
    out: Dict[str, Any] = {}

    def _one(key: str) -> tuple:
        fn, path = runners[key]
        try:
            data = _call_view(fn, path, payloads[key])
            return key, {'status': 'fulfilled', 'result': data}
        except Exception as exc:  # noqa: BLE001
            logger.warning('Profile metric %s failed: %s', key, exc)
            return key, {'status': 'rejected', 'reason': str(exc)}

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_one, k) for k in keys]
        for fut in as_completed(futures):
            key, val = fut.result()
            out[key] = val
    return out


@api_view(['POST'])
@permission_classes([AllowAny])
def profile_score(request):
    """
    Score a food composition across all (or selected) profile metrics.

    Body:
      foods: [{ food_id, mass_g, food_description? }]
      user_type: individual | researcher | policy
      metrics: optional subset
      decomposition_provenance, multi_day_label, enable_lca_matcher
    """
    foods_raw = request.data.get('foods') or request.data.get('ingredients')
    if not isinstance(foods_raw, list) or len(foods_raw) == 0:
        return Response(
            {'error': 'foods array with food_id and mass_g is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    composition: List[Dict[str, Any]] = []
    for item in foods_raw:
        try:
            fid = int(item['food_id'])
            mass = float(item['mass_g'])
        except (KeyError, TypeError, ValueError):
            return Response({'error': 'Each food needs food_id and mass_g'}, status=status.HTTP_400_BAD_REQUEST)
        if fid <= 0 or mass <= 0:
            continue
        composition.append({
            'food_id': fid,
            'mass_g': mass,
            'food_description': item.get('food_description') or item.get('FoodDescription'),
        })

    if not composition:
        return Response({'error': 'No valid foods in request'}, status=status.HTTP_400_BAD_REQUEST)

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    from api.views.packaged_food_caveat import parse_decomposition_provenance
    decomp = parse_decomposition_provenance(request.data.get('decomposition_provenance'))
    multi_day = request.data.get('multi_day_label')
    enable_lca = bool(request.data.get('enable_lca_matcher', True))
    metrics = request.data.get('metrics')
    if metrics is not None and not isinstance(metrics, list):
        metrics = None

    payloads = _build_payloads(composition, user_type, decomp, multi_day, enable_lca)
    results = _run_metrics(payloads, metrics)
    meta = compute_profile_meta(composition)

    return Response({
        'success': True,
        'data': {
            'metrics': results,
            'meta': meta,
        },
    })
