"""FPID ingredient-level food-group attribution endpoint.

POST /api/fpid/breakdown/
    Body: {"food_id": 994, "mass_g": 200}
    Returns, for a single finished/composite catalog food:
      - breakdown:      which ingredients contribute which major food groups, from the
                        food's closest US FNDDS recipe analog (USDA FPID 2017-18).
      - reconstruction: independent QC — does the FPID ingredient rollup reproduce the
                        food's own FPED profile? (cosine + coverage).
    Either block is null (with a `note`) when the food has no reliable FNDDS analog.

Pure deterministic compute (no LLM, no rate limit): reads the pre-built FPED bridge meta
and the FPID/FNDDS lookups.
"""
from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from api.services.fpid_aggregator import fpid_breakdown, fpid_reconstruction


@api_view(['POST'])
@permission_classes([AllowAny])
def fpid_breakdown_view(request):
    """Ingredient-level food-group attribution (+ reconstruction QC) for one food."""
    try:
        food_id = int(request.data.get('food_id'))
    except (TypeError, ValueError):
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'Field "food_id" (positive integer) is required.',
        }, status=status.HTTP_400_BAD_REQUEST)
    if food_id <= 0:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'Field "food_id" must be a positive integer.',
        }, status=status.HTTP_400_BAD_REQUEST)

    mass_raw = request.data.get('mass_g', 100.0)
    try:
        mass_g = float(mass_raw)
    except (TypeError, ValueError):
        mass_g = 100.0
    if mass_g <= 0:
        mass_g = 100.0

    breakdown = fpid_breakdown(food_id, mass_g=mass_g)
    reconstruction = fpid_reconstruction(food_id)

    return Response({
        'success': True,
        'food_id': food_id,
        'mass_g': round(mass_g, 1),
        'breakdown': breakdown,
        'reconstruction': reconstruction,
        'note': (
            None if breakdown is not None else
            'No ingredient-level breakdown: this food has no reliable US FNDDS recipe '
            'analog (region-specific food, or analog below the bridge confidence floor).'
        ),
    }, status=status.HTTP_200_OK)
