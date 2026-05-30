"""Substitution analyzer API — SUBST-1 Phases 1–3."""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.services.substitution_analyzer import (
    analyze_substitutions,
    batch_analyze_substitutions,
    score_modified_composition,
)
from api.services.substitution_improve_plan import build_improve_plan

logger = logging.getLogger(__name__)

_VALID_PURPOSES = frozenset({
    'general_health',
    'lower_sodium',
    'higher_fibre',
    'higher_protein',
    'lower_sat_fat',
    'diabetes_friendly',
    'sustainability',
})


def _parse_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes')


@api_view(['POST'])
@permission_classes([AllowAny])
def substitution_analyze(request):
    """Analyze a CNF composition and return ranked substitution suggestions.

    Request body::

        {
          "composition": [...],
          "purpose": "general_health",
          "max_suggestions": 3,
          "include_scorecard": true,
          "constraints": {
            "exclude_food_ids": [1234],
            "source_filter": "cnf",
            "max_swaps": 2,
            "vegetarian": false,
            "same_functional_role": false,
            "exclude_allergens": ["milk", "peanut"]
          }
        }
    """
    composition = request.data.get('composition')
    if not composition or not isinstance(composition, list):
        return Response(
            {'success': False, 'message': "'composition' must be a non-empty array"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    purpose = str(request.data.get('purpose', 'general_health'))
    if purpose not in _VALID_PURPOSES:
        purpose = 'general_health'

    try:
        max_suggestions = int(request.data.get('max_suggestions', 3))
    except (TypeError, ValueError):
        max_suggestions = 3

    constraints = request.data.get('constraints')
    if constraints is not None and not isinstance(constraints, dict):
        return Response(
            {'success': False, 'message': "'constraints' must be an object"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    include_scorecard = _parse_bool(request.data.get('include_scorecard'), True)
    dish_name = request.data.get('dish_name')
    if dish_name is not None:
        dish_name = str(dish_name).strip() or None
    reformulation_mode = str(request.data.get('reformulation_mode', 'singles'))
    if reformulation_mode not in ('singles', 'greedy'):
        reformulation_mode = 'singles'

    try:
        result = analyze_substitutions(
            composition,
            purpose=purpose,
            max_suggestions=max_suggestions,
            constraints=constraints,
            include_scorecard=include_scorecard,
            dish_name=dish_name,
            reformulation_mode=reformulation_mode,
        )
        return Response(result)
    except ValueError as exc:
        return Response(
            {'success': False, 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('substitution_analyze failed')
        return Response(
            {'success': False, 'message': f'Analysis failed: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def substitution_apply(request):
    """Re-score a modified composition after the client applies a suggestion.

    Request body::

        {
          "modified_composition": [{ "food_id": 3392, "mass_g": 100 }]
        }
    """
    composition = request.data.get('modified_composition')
    if not composition or not isinstance(composition, list):
        return Response(
            {'success': False, 'message': "'modified_composition' must be a non-empty array"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = score_modified_composition(composition)
        return Response(result)
    except ValueError as exc:
        return Response(
            {'success': False, 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('substitution_apply failed')
        return Response(
            {'success': False, 'message': f'Apply failed: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def substitution_batch(request):
    """Batch analyze multiple compositions (researcher automation).

    Request body::

        {
          "items": [
            { "label": "S5 beef", "composition": [...], "purpose": "general_health" }
          ],
          "purpose": "general_health",
          "max_suggestions": 3,
          "include_scorecard": true,
          "constraints": { ... }
        }
    """
    items = request.data.get('items')
    if not items or not isinstance(items, list):
        return Response(
            {'success': False, 'message': "'items' must be a non-empty array"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    purpose = str(request.data.get('purpose', 'general_health'))
    if purpose not in _VALID_PURPOSES:
        purpose = 'general_health'

    try:
        max_suggestions = int(request.data.get('max_suggestions', 3))
    except (TypeError, ValueError):
        max_suggestions = 3

    constraints = request.data.get('constraints')
    if constraints is not None and not isinstance(constraints, dict):
        return Response(
            {'success': False, 'message': "'constraints' must be an object"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    include_scorecard = _parse_bool(request.data.get('include_scorecard'), True)

    try:
        result = batch_analyze_substitutions(
            items,
            purpose=purpose,
            max_suggestions=max_suggestions,
            constraints=constraints,
            include_scorecard=include_scorecard,
        )
        return Response(result)
    except ValueError as exc:
        return Response(
            {'success': False, 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('substitution_batch failed')
        return Response(
            {'success': False, 'message': f'Batch analysis failed: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def substitution_improve_plan(request):
    """Orchestrate recall/day composition → full scorecard → ranked improvement plan.

    Accept either a flat ``composition`` list or a ``recall_export`` blob from
    recall-history JSON export (same shape as localStorage).

    Request body::

        {
          "recall_export": { "version": 1, "days": [...] },
          "day_ids": ["optional-filter"],
          "purpose": "general_health",
          "max_suggestions": 5,
          "max_swaps": 3,
          "reformulation_mode": "greedy",
          "include_population_benchmark": true
        }
    """
    composition = request.data.get('composition')
    recall_export = request.data.get('recall_export')
    day_ids = request.data.get('day_ids')
    if day_ids is not None and not isinstance(day_ids, list):
        return Response(
            {'success': False, 'message': "'day_ids' must be an array of day UUIDs"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    purpose = str(request.data.get('purpose', 'general_health'))
    if purpose not in _VALID_PURPOSES:
        purpose = 'general_health'

    try:
        max_suggestions = int(request.data.get('max_suggestions', 5))
    except (TypeError, ValueError):
        max_suggestions = 5

    try:
        max_swaps = int(request.data.get('max_swaps', 3))
    except (TypeError, ValueError):
        max_swaps = 3

    reformulation_mode = str(request.data.get('reformulation_mode', 'greedy'))
    if reformulation_mode not in ('singles', 'greedy'):
        reformulation_mode = 'greedy'

    include_population_benchmark = _parse_bool(
        request.data.get('include_population_benchmark'), True,
    )
    dish_name = request.data.get('dish_name')
    if dish_name is not None:
        dish_name = str(dish_name).strip() or None

    if not composition and not recall_export:
        return Response(
            {
                'success': False,
                'message': "Provide 'composition' or 'recall_export'",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = build_improve_plan(
            composition=composition,
            recall_export=recall_export,
            day_ids=day_ids,
            purpose=purpose,
            max_suggestions=max_suggestions,
            max_swaps=max_swaps,
            reformulation_mode=reformulation_mode,
            include_population_benchmark=include_population_benchmark,
            dish_name=dish_name,
        )
        return Response(result)
    except ValueError as exc:
        return Response(
            {'success': False, 'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('substitution_improve_plan failed')
        return Response(
            {'success': False, 'message': f'Improve plan failed: {exc}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
