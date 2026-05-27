import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from api.seo_utils import seo_metadata
from heni_calculator.heni.service import (
    calculate_meal_heni_response,
    get_cnf_integrator,
    resolve_llm_api_key,
)
from heni_calculator.heni.models.ingredient import Ingredient
from .heni_explanations import get_explanations as get_heni_explanations
from .heni_analysis_helpers import (
    _identify_primary_health_drivers,
    _get_epidemiological_context,
    _estimate_population_impact,
    _generate_policy_recommendations,
    _get_comparison_benchmarks,
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Health and Nutritional Impact (HENI) Calculator | DISH Research",
    description="Calculate the Health and Nutritional Impact (HENI) score for your meals. Analyze the health benefits of your food choices.",
    keywords="HENI, health impact, nutritional impact, meal analysis, healthy eating"
)
def heni_calculate(request):
    """Calculate HENI score for meals with specified ingredients and amounts."""
    try:
        meal_data = request.data.get('meal', [])
        user_type = str(request.data.get('user_type', 'individual'))
        if user_type not in ('individual', 'researcher', 'policy'):
            user_type = 'individual'
        from api.views.packaged_food_caveat import (
            parse_decomposition_provenance,
            build_packaged_food_caveat,
        )
        decomposition_provenance = parse_decomposition_provenance(
            request.data.get('decomposition_provenance'),
        )

        if not meal_data:
            return Response({"error": "'meal' array with ingredients is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(meal_data, list) or len(meal_data) == 0:
            return Response({"error": "Meal array cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        integrator = get_cnf_integrator()
        ingredients = []

        for item in meal_data:
            food_id = item.get('food_id')
            amount = item.get('amount')
            unit = item.get('unit', 'g')
            
            if not food_id:
                return Response({"error": "Each ingredient must have a food_id"}, status=status.HTTP_400_BAD_REQUEST)
            
            if amount is None or amount <= 0:
                return Response({"error": "Each ingredient must have a positive amount"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create ingredient using the new integrator
            ingredient = Ingredient(
                food_id=food_id, 
                amount=float(amount), 
                unit=unit, 
                cnf_integrator=integrator
            )
            ingredients.append(ingredient)

        # Match resolve_llm_api_key(): key may live only in os.environ (.env via env_bootstrap),
        # not as a Django setting attribute.
        if not resolve_llm_api_key():
            logger.warning("No OpenAI API key configured, HENI categorization may be limited")

        comprehensive_result = calculate_meal_heni_response(
            ingredients,
            llm_api_key=resolve_llm_api_key(),
            cnf_integrator=integrator,
        )

        # Audience-aware explanations (AUDIENCE-CODE-1 SHIPPED 2026-05-23).
        # The literature-cited interpretive prose lives in heni_explanations.py;
        # the existing comprehensive_result keys are preserved for backward
        # compatibility (researchers still see all internal fields).
        hp = comprehensive_result.get('health_impact') or {}
        try:
            health_min = float(hp.get('health_impact_minutes', 0.0))
        except (TypeError, ValueError):
            health_min = 0.0
        comprehensive_result['explanations'] = get_heni_explanations(
            health_impact_minutes=health_min, user_type=user_type,
        )
        # WAFCT-EXTEND (2026-05-24): per-source caveat — empty dict if no
        # WAFCT foods in the meal, so this merge is a no-op for CNF-only.
        try:
            from api.views.wafct_caveat import build_wafct_caveat
            comprehensive_result['explanations'].update(build_wafct_caveat(
                [item.get('food_id') for item in meal_data if item.get('food_id')],
                indicator='heni', user_type=user_type,
            ))
        except Exception:  # noqa: BLE001
            pass
        try:
            comprehensive_result['explanations'].update(build_packaged_food_caveat(
                'heni', user_type, decomposition_provenance=decomposition_provenance,
            ))
        except Exception:  # noqa: BLE001
            pass
        comprehensive_result['user_type'] = user_type

        result = {
            "success": True,
            "data": comprehensive_result,
            "metadata": {
                "calculation_method": "HENI (Stylianou et al. 2021), Rust kernel via rust_core.heni",
                "factor_source": (
                    "Stylianou KS, Fulgoni VL III, Jolliet O. Nat Food. 2021;2(8):616-627. "
                    "Supplementary Information, Suppl. Table 3 p. 8."
                ),
                "epidemiology_vintage": "GBD 2016 (Stylianou 2021 base)",
                "units": {
                    "total_heni_score": "μDALY (signed; positive = detrimental per Stylianou sign convention)",
                    "heni_per_100_kcal": "μDALY / 100 kcal",
                    "heni_per_100_grams": "μDALY / 100 g",
                    "heni_per_serving": "μDALY / serving",
                    "health_impact_minutes": "minutes of healthy life (positive = beneficial)",
                },
                "conversion_constant": (
                    "-0.5256 min/μDALY (Stylianou 2021 SI p. 98; 1 μDALY = 0.5256 min, "
                    "negative sign flips damage→benefit so positive minutes = good)"
                ),
                "methodology_version": "Stylianou2021-Suppl-Table-3 (HENI-CODE-1 audit, 2026-05-21)",
                "double_counting_carve_outs_applied": [
                    "milk_vs_calcium (Stylianou 2021 Methods p. 626)",
                    "fiber_source_split (Stylianou 2021 SI §S2.9 pp. 35-36)",
                ],
                "known_caveats": [
                    "Marginal index; not valid for radically restructured diets (Stylianou 2021 Discussion pp. 622-624).",
                    "trans_fat is zeroed-with-warning when CNF lacks measured TFA (Stylianou 2021 SI §S2.1 p. 12).",
                    "Disease-breakdown weights are equal-share per outcome from Stylianou 2021 SI Table 1; "
                    "rederivation from 6,195-pair GBD 2016 RR matrix is logged as HENI-CODE-1.x.",
                ],
                "last_updated": "2026-05-21",
            }
        }
        
        return Response(result)
    
    except Exception as e:
        logger.exception(f"An error occurred in HENI calculation: {str(e)}")
        return Response({"error": "An unexpected error occurred during HENI calculation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@seo_metadata(
    title="HENI Food Profile Analysis | DISH Research",
    description="Get detailed HENI profile for a specific food item with comprehensive health impact analysis",
    keywords="HENI, food profile, health impact analysis, nutritional assessment"
)
def get_food_heni_profile(request, food_id):
    """
    Get comprehensive HENI profile for a specific food ID
    Returns detailed breakdown for researchers and policy makers
    """
    try:
        if not food_id:
            return Response({"error": "Food ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get amount from query parameters
        amount_g = request.GET.get('amount_g', 100)  # Default to 100g
        try:
            amount_g = float(amount_g)
            if amount_g <= 0:
                return Response({"error": "Amount must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Amount must be a valid number"}, status=status.HTTP_400_BAD_REQUEST)
        
        integrator = get_cnf_integrator()

        ingredient = Ingredient(
            food_id=food_id,
            amount=amount_g,
            unit='g',
            cnf_integrator=integrator
        )
        
        comprehensive_result = calculate_meal_heni_response(
            [ingredient],
            llm_api_key=resolve_llm_api_key(),
            cnf_integrator=integrator,
        )
        
        # Get food details
        food_name = integrator.get_food_description(food_id)
        food_group = integrator.get_food_group(food_id)
        
        # Enhanced profile data
        profile_data = {
            "food_details": {
                "food_id": food_id,
                "food_name": food_name,
                "food_group": food_group,
                "amount_analyzed_g": amount_g
            },
            "heni_analysis": comprehensive_result,
            "research_insights": {
                "primary_health_drivers": _identify_primary_health_drivers(comprehensive_result),
                "epidemiological_evidence": _get_epidemiological_context(comprehensive_result),
                "population_impact_estimate": _estimate_population_impact(comprehensive_result, amount_g)
            },
            "policy_recommendations": _generate_policy_recommendations(comprehensive_result, food_group),
            "comparison_benchmarks": _get_comparison_benchmarks(comprehensive_result)
        }
        
        return Response({
            "success": True,
            "data": profile_data,
            "metadata": {
                "analysis_type": "Comprehensive HENI Food Profile",
                "methodology": "DALY-based health burden assessment",
                "evidence_base": "Global Burden of Disease epidemiological studies"
            }
        })
    
    except Exception as e:
        logger.exception(f"Error getting HENI profile for food ID {food_id}: {str(e)}")
        return Response({"error": "An unexpected error occurred while retrieving food profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)