"""FPED food-group exposure endpoint (Phase 3 of the FPED/FPID unlock).

POST /api/fped/analyze/
    Body: {"foods": [{"food_id": 4066, "mass_g": 120}, ...], "user_type": "individual"}
    Returns the aggregated USDA Food Pattern component totals + dual-guideline gaps,
    wrapped in an audience-aware `fped_component_analysis` block.

Pure deterministic compute (no LLM, no rate limit): reads the pre-built FPED profile
lookup and the reference-target table. Reusable by the recall page, the Scorecard
fan-out, and any food list.
"""
from __future__ import annotations

from typing import Any, Dict, List

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from api.services.fped_aggregator import aggregate_fped, decomposition_plausibility
from api.services.fped_cohort import aggregate_cohort
from api.views.fped_explanations import build_cohort_explanations, build_fped_explanations


def _clean_foods(foods_raw) -> List[Dict[str, Any]]:
    """Keep only {food_id>0, mass_g>0} entries from a raw food list."""
    cleaned: List[Dict[str, Any]] = []
    if not isinstance(foods_raw, list):
        return cleaned
    for f in foods_raw:
        if not isinstance(f, dict):
            continue
        try:
            fid = int(f.get('food_id'))
            mass = float(f.get('mass_g'))
        except (TypeError, ValueError):
            continue
        if fid > 0 and mass > 0:
            cleaned.append({'food_id': fid, 'mass_g': mass})
    return cleaned


@api_view(['POST'])
@permission_classes([AllowAny])
def fped_analyze(request):
    """Aggregate a food list into FPED food-group exposure + guideline gaps."""
    foods_raw = request.data.get('foods')
    if not isinstance(foods_raw, list) or not foods_raw:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'Field "foods" is required (non-empty list of {food_id, mass_g}).',
        }, status=status.HTTP_400_BAD_REQUEST)

    cleaned = _clean_foods(foods_raw)

    if not cleaned:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'No foods with positive food_id and mass_g.',
        }, status=status.HTTP_400_BAD_REQUEST)

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    agg = aggregate_fped(cleaned)
    explanations = build_fped_explanations(agg, user_type=user_type)

    body = {
        'success': True,
        'result': agg.to_dict(),
        'explanations': explanations,
    }

    # Phase 5 QC: if the caller passes the catalog FoodID of the composite that `foods`
    # was decomposed FROM (e.g. the environmental/packaged-food decomposer, or a
    # researcher validating a split), attach an FPED-rollup plausibility check —
    # how food-group-consistent the ingredient split is with the dish's own FPED
    # profile. Returns null when the composite has no FPED twin.
    composite_raw = request.data.get('composite_food_id')
    if composite_raw is not None:
        try:
            composite_id = int(composite_raw)
        except (TypeError, ValueError):
            composite_id = 0
        if composite_id > 0:
            body['decomposition_plausibility'] = decomposition_plausibility(composite_id, cleaned)

    return Response(body, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def fped_cohort(request):
    """Food-group exposure distribution across N recalls (each a food list).

    Body: {"recalls": [[{food_id, mass_g}, ...], ...], "user_type": "researcher"}
    Returns per food group the median/IQR/range of intake across recalls + the % of
    recalls meeting the MyPlate/CFG target, wrapped in an audience-aware analysis block.
    """
    recalls_raw = request.data.get('recalls')
    if not isinstance(recalls_raw, list) or not recalls_raw:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'Field "recalls" is required (non-empty list of food lists).',
        }, status=status.HTTP_400_BAD_REQUEST)

    recalls: List[List[Dict[str, Any]]] = []
    for r in recalls_raw:
        cleaned = _clean_foods(r)
        if cleaned:
            recalls.append(cleaned)

    if not recalls:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'No recalls contained foods with positive food_id and mass_g.',
        }, status=status.HTTP_400_BAD_REQUEST)

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    cohort = aggregate_cohort(recalls)
    explanations = build_cohort_explanations(cohort, user_type=user_type)

    return Response({
        'success': True,
        'result': cohort,
        'explanations': explanations,
    }, status=status.HTTP_200_OK)
