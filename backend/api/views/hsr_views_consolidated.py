"""
Consolidated HSR Views - Comprehensive Health Star Rating Calculator API
Combines enhanced analysis with clean, user-friendly endpoints for better decision support.
"""

import logging
import time
from typing import List, Dict, Optional, Union
from functools import lru_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings

# HSR Calculator imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../hsr_calculator'))

from hsr_calculator.hsr.models.food import Food as HSRFood
from hsr_calculator.hsr.models.meal import Meal as HSRMeal
from hsr_calculator.hsr.models.category import Category
from hsr_calculator.hsr.calculators.hsr_calculator import HSRCalculator, HSRConfig
from hsr_calculator.hsr.providers.threshold_provider import ThresholdProvider
from hsr_calculator.hsr.calculators.fvnl_calculator import calculate_fvnl_content
from hsr_calculator.hsr.utils.food_group_mapper import FoodGroupMapper

# CNF integration
from dish_cnf_db_pipeline.cnf_pipeline import CNFDataPipeline

logger = logging.getLogger(__name__)


def _log_hsr_timing(view: str, food_ids: List, meta: str = "", **parts_ms: float) -> None:
    """Log wall-clock segments in milliseconds (``time.perf_counter``)."""
    ordered = " ".join(f"{k}={parts_ms[k]:.2f}ms" for k in sorted(parts_ms))
    logger.info(
        "HSR timing view=%s food_ids=%s %s%s",
        view,
        food_ids,
        f"{meta} " if meta else "",
        ordered,
    )


# Single process-wide CNF pipeline — see backend/api/cnf_cache.py.
from api.cnf_cache import get_dish_cnf_pipeline as get_cnf_pipeline

# Audience-aware explanations (AUDIENCE-CODE-1 SHIPPED 2026-05-23).
from .hsr_explanations import (
    get_explanations as get_hsr_explanations,
    build_recall24h_caveat,
)

# Manual meal builder + 24-h recall handoff; calculate and compare share this cap.
HSR_CALCULATE_MAX_FOODS = 100


class HSRAPIError(Exception):
    """Custom exception for HSR API errors"""
    pass


def hsr_error_handler(view_func):
    """Decorator for consistent HSR error handling and logging"""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except HSRAPIError as e:
            logger.warning(f"HSR API error in {view_func.__name__}: {str(e)}")
            return Response({
                "success": False,
                "error": "Invalid request",
                "message": str(e),
                "help": "Please check your input data and try again."
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.warning(f"Value error in {view_func.__name__}: {str(e)}")
            return Response({
                "success": False,
                "error": "Invalid data format",
                "message": str(e),
                "help": "Please ensure all values are valid numbers."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "help": "If this persists, please contact support."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper


@api_view(['POST'])
@permission_classes([AllowAny])
@hsr_error_handler
def calculate_hsr(request):
    """
    Calculate Health Star Rating with comprehensive analysis and insights.
    
    Supports both simple and detailed analysis modes.
    
    Request format:
    {
        "food_ids": [123, 456],
        "serving_sizes": [150, 100],
        "analysis_level": "detailed",  // "simple" or "detailed"
        "include_alternatives": true,
        "include_meal_insights": true,
        "from_recall24h": false
    }
    """
    # Extract and validate request data
    food_ids = request.data.get('food_ids', [])
    serving_sizes = request.data.get('serving_sizes', [])
    analysis_level = request.data.get('analysis_level', 'detailed')
    from_recall24h = _parse_bool_flag(request.data.get('from_recall24h', False))
    include_alternatives = request.data.get('include_alternatives', False)
    if from_recall24h:
        include_alternatives = False
    include_meal_insights = request.data.get('include_meal_insights', True)
    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'
    
    # Validate inputs
    _validate_hsr_input(food_ids, serving_sizes)

    t0 = time.perf_counter()

    # Load and process foods
    foods = []
    for food_id, serving_size in zip(food_ids, serving_sizes):
        try:
            food = _load_food_data(food_id, serving_size)
            foods.append(food)
        except Exception as e:
            raise HSRAPIError(f"Failed to load food {food_id}: {str(e)}")

    t1 = time.perf_counter()
    load_ms = (t1 - t0) * 1000.0

    # FIX (HSR-CATEG-2 follow-up 2026-05-23): the previous logic hardcoded
    # the meal category from the FIRST food in the list, completely bypassing
    # the MealCategorizer. That meant a 30 g cheese + 60 g bread sandwich
    # got Category 3D (because cheese was listed first) regardless of which
    # food was actually dominant by mass / fitness. For single-food calls
    # we keep the per-food category (no ambiguity); for multi-food meals we
    # delegate to HSRMeal._determine_category which calls the MealCategorizer
    # (with the new mass-dominant general-food override). This is the only
    # path that respects the HSRAC v9 "mixed dish → Cat 2" intuition.
    meal = HSRMeal(foods=foods)
    if len(foods) == 1:
        primary_food = foods[0]
        meal.category = ThresholdProvider.get_category_from_food(
            primary_food.food_name,
            getattr(primary_food, "food_group_id", 0),
        )
    # Multi-food meals: HSRMeal.__post_init__ already ran _determine_category,
    # which invokes the MealCategorizer. No override needed here.

    # Use standard HSR configuration
    config = HSRConfig(
        use_scientific_thresholds=False,
        differentiate_sugar_sources=False,
        apply_satiety_adjustments=False,
        use_unified_energy_approach=False,
        consider_processing_level=False,
        include_confidence_metrics=True,
        detailed_explanations=(analysis_level == "detailed"),
    )
    calculator = HSRCalculator(meal, config)

    if analysis_level == "simple":
        result = _calculate_simple_hsr(calculator)
    else:
        result = _calculate_detailed_hsr(calculator, include_alternatives, include_meal_insights)

    t2 = time.perf_counter()
    core_ms = (t2 - t1) * 1000.0

    # Add food details for user context
    result["food_details"] = _get_food_details_summary(foods)

    # Audience-aware explanations (AUDIENCE-CODE-1 SHIPPED 2026-05-23).
    # Star rating + category come from the existing computed result; the
    # explanations block replaces the previously-hardcoded rating.description.
    # FIX (2026-05-23): `meal_category` was never defined → NameError here
    # wiped star_rating in the broad except and showed 0.0 stars for
    # individual-mode users (their UI surfaces explanations ahead of the
    # researcher-only score headline).
    try:
        star_rating = float(result.get('hsr_result', {}).get('rating', {}).get('star_rating', 0.0))
    except (TypeError, ValueError):
        star_rating = 0.0
    meal_cat = meal.category
    category_str = str(meal_cat.value) if meal_cat is not None and hasattr(meal_cat, 'value') else '2'

    result["explanations"] = get_hsr_explanations(
        star_rating=star_rating, category=category_str, user_type=user_type,
    )
    if from_recall24h:
        result["explanations"].update(
            build_recall24h_caveat(user_type=user_type, n_foods=len(food_ids)),
        )
    # WAFCT-EXTEND (2026-05-24): per-source caveat (sodium method delta).
    try:
        from api.views.wafct_caveat import build_wafct_caveat
        result["explanations"].update(build_wafct_caveat(
            food_ids, indicator='hsr', user_type=user_type,
        ))
    except Exception:  # noqa: BLE001
        pass
    result["user_type"] = user_type
    result["from_recall24h"] = from_recall24h
    result["meal_categorization"] = _get_basic_meal_categorization_summary(meal)

    # SCORECARD-1 (2026-05-26): when scoring a 24-h recall (or any multi-food
    # batch coming from the Scorecard), HSR's combined-meal star is
    # methodologically weak — HSRAC v9 rates products WITHIN their category.
    # Surface a per-item breakdown so the Scorecard can show energy-weighted
    # range/anchors/distribution instead of a misleading single number.
    if from_recall24h and len(foods) > 1:
        result["per_food_ratings"] = _build_per_food_ratings(food_ids, serving_sizes)
        result["per_food_summary"] = _summarise_per_food_ratings(result["per_food_ratings"])

    t3 = time.perf_counter()
    assembly_ms = (t3 - t2) * 1000.0
    total_ms = (t3 - t0) * 1000.0

    _log_hsr_timing(
        "calculate_hsr",
        food_ids,
        meta=(
            f"analysis_level={analysis_level} include_alternatives={include_alternatives} "
            f"include_meal_insights={include_meal_insights}"
        ),
        load_foods=load_ms,
        meal_and_hsr=core_ms,
        response_assembly=assembly_ms,
        total=total_ms,
    )

    return Response(result)


@api_view(['POST'])
@permission_classes([AllowAny])
@hsr_error_handler
def compare_foods(request):
    """
    Compare HSR ratings of multiple foods at a standardized serving size.
    
    Request format:
    {
        "food_ids": [123, 456, 789],
        "serving_size": 100,  // Common serving size for fair comparison
        "sort_by": "hsr_rating"  // "hsr_rating", "energy", "protein", etc.
    }
    """
    food_ids = request.data.get('food_ids', [])
    serving_size = request.data.get('serving_size', 100)
    sort_by = request.data.get('sort_by', 'hsr_rating')
    
    if not food_ids:
        raise HSRAPIError("food_ids is required")
    
    if len(food_ids) > HSR_CALCULATE_MAX_FOODS:
        raise HSRAPIError(
            f"Maximum {HSR_CALCULATE_MAX_FOODS} foods can be compared at once"
        )
    
    if not isinstance(serving_size, (int, float)) or serving_size <= 0:
        raise HSRAPIError("serving_size must be a positive number")
    
    # Compare foods using enhanced calculator
    comparisons = []
    for food_id in food_ids:
        try:
            food = _load_food_data(food_id, serving_size)
            
            # Use official HSR categorization for single food
            food_category = ThresholdProvider.get_category_from_food(
                food.food_name, 
                getattr(food, 'food_group_id', 0)
            )
            meal = HSRMeal(foods=[food])
            meal.category = food_category
            
            # Use standard HSR configuration
            config = HSRConfig(
                use_scientific_thresholds=False,
                differentiate_sugar_sources=False,
                apply_satiety_adjustments=False,
                use_unified_energy_approach=False,
                consider_processing_level=False
            )
            calculator = HSRCalculator(meal, config)
            result = calculator.calculate_hsr()
            
            comparison = _format_food_comparison(food, result, serving_size)
            comparisons.append(comparison)
        except Exception as e:
            logger.warning(f"Failed to analyze food {food_id}: {str(e)}")
            comparisons.append({
                "food_id": food_id,
                "error": f"Analysis failed: {str(e)}"
            })
    
    # Sort comparisons
    valid_comparisons = [c for c in comparisons if 'hsr_rating' in c]
    valid_comparisons.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
    
    # Generate comparison summary
    summary = _generate_comparison_summary(valid_comparisons, sort_by)
    
    return Response({
        "success": True,
        "comparison": {
            "serving_size": serving_size,
            "sort_by": sort_by,
            "total_foods": len(food_ids),
            "successfully_analyzed": len(valid_comparisons),
            "foods": comparisons,
            "summary": summary,
            "recommendations": _generate_comparison_recommendations(valid_comparisons)
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@hsr_error_handler
def get_food_hsr_profile(request, food_id):
    """
    Get comprehensive HSR profile for a single food item.
    
    Query parameters:
    - serving_size: Serving size in grams (default: 100)
    - include_alternatives: Include healthier alternatives (default: false)
    """
    serving_size = float(request.GET.get('serving_size', 100))
    include_alternatives = request.GET.get('include_alternatives', 'false').lower() == 'true'
    
    if serving_size <= 0 or serving_size > 2000:
        raise HSRAPIError("serving_size must be between 0 and 2000 grams")
    
    # Load and analyze food using enhanced system
    try:
        food = _load_food_data(food_id, serving_size)
        
        # Use official HSR categorization
        food_category = ThresholdProvider.get_category_from_food(
            food.food_name, 
            getattr(food, 'food_group_id', 0)
        )
        meal = HSRMeal(foods=[food])
        meal.category = food_category
        
        # Use standard HSR configuration
        config = HSRConfig(
            use_scientific_thresholds=False,
            differentiate_sugar_sources=False,
            apply_satiety_adjustments=False,
            use_unified_energy_approach=False,
            consider_processing_level=False,
            detailed_explanations=True
        )
        calculator = HSRCalculator(meal, config)
        result = calculator.calculate_hsr()
        
        # Build comprehensive profile
        profile = {
            "success": True,
            "food_profile": {
                "basic_info": _get_food_basic_info(food),
                "hsr_analysis": _format_detailed_hsr_result(result),
                "nutritional_highlights": _get_nutritional_highlights(food, result),
                "usage_recommendations": _get_usage_recommendations(food, result)
            }
        }
        
        if include_alternatives:
            profile["food_profile"]["healthier_alternatives"] = _get_healthier_alternatives(food)
        
        return Response(profile)
        
    except Exception as e:
        raise HSRAPIError(f"Failed to analyze food {food_id}: {str(e)}")


@api_view(['POST'])
@permission_classes([AllowAny])
@hsr_error_handler
def get_meal_insights(request):
    """
    Get meal-level insights and recommendations for food combinations.
    
    Request format:
    {
        "food_ids": [123, 456],
        "serving_sizes": [150, 100],
        "meal_type": "breakfast",  // optional: breakfast, lunch, dinner, snack
        "dietary_goals": ["weight_loss", "heart_health"]  // optional
    }
    """
    food_ids = request.data.get('food_ids', [])
    serving_sizes = request.data.get('serving_sizes', [])
    meal_type = request.data.get('meal_type')
    dietary_goals = request.data.get('dietary_goals', [])
    
    _validate_hsr_input(food_ids, serving_sizes)

    t0 = time.perf_counter()

    # Load foods and calculate meal HSR using official methodology
    foods = [_load_food_data(fid, size) for fid, size in zip(food_ids, serving_sizes)]

    t1 = time.perf_counter()
    load_ms = (t1 - t0) * 1000.0

    # FIX (HSR-CATEG-2 follow-up 2026-05-23): same fix as calculate_hsr above.
    # Multi-food meals must go through MealCategorizer (via HSRMeal's
    # __post_init__) so the mass-dominant general-food override fires.
    meal = HSRMeal(foods=foods)
    if len(foods) == 1:
        primary_food = foods[0]
        meal.category = ThresholdProvider.get_category_from_food(
            primary_food.food_name,
            getattr(primary_food, "food_group_id", 0),
        )

    # Use standard HSR configuration
    config = HSRConfig(
        use_scientific_thresholds=False,
        differentiate_sugar_sources=False,
        apply_satiety_adjustments=False,
        use_unified_energy_approach=False,
        consider_processing_level=False,
        detailed_explanations=True,
    )
    calculator = HSRCalculator(meal, config)
    result = calculator.calculate_hsr()

    t2 = time.perf_counter()
    core_ms = (t2 - t1) * 1000.0

    # Generate comprehensive meal insights
    insights = {
        "success": True,
        "meal_insights": {
            "meal_composition": _analyze_meal_composition(foods, result),
            "nutritional_balance": _analyze_nutritional_balance(meal, result),
            "hsr_breakdown": _get_hsr_breakdown(result),
            "improvement_opportunities": _identify_improvement_opportunities(foods, result),
            "meal_type_suitability": _assess_meal_type_suitability(meal, meal_type),
            "dietary_goal_alignment": _assess_dietary_goal_alignment(meal, result, dietary_goals),
            # Basic nutritional analysis only
            "nutritional_summary": {
                "total_sugars": meal.sugars_total,
                "energy_per_100g": meal.energy_kj,
                "protein_per_100g": meal.protein,
                "fiber_per_100g": meal.fibre_total_dietary
            }
        },
        "food_details": _get_food_details_summary(foods),
        "meal_categorization": _get_basic_meal_categorization_summary(meal),
    }

    t3 = time.perf_counter()
    assembly_ms = (t3 - t2) * 1000.0
    total_ms = (t3 - t0) * 1000.0

    _log_hsr_timing(
        "get_meal_insights",
        food_ids,
        meta=f"meal_type={meal_type!r} dietary_goals={dietary_goals!r}",
        load_foods=load_ms,
        meal_and_hsr=core_ms,
        response_assembly=assembly_ms,
        total=total_ms,
    )

    return Response(insights)


# Helper functions
def _parse_bool_flag(value: object) -> bool:
    """Coerce JSON booleans and common string forms."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return bool(value)


def _validate_hsr_input(food_ids: List[int], serving_sizes: List[float]):
    """Validate HSR calculation input"""
    if not food_ids or not serving_sizes:
        raise HSRAPIError("Both food_ids and serving_sizes are required")
    
    if len(food_ids) != len(serving_sizes):
        raise HSRAPIError("Number of food IDs must match number of serving sizes")
    
    if len(food_ids) > HSR_CALCULATE_MAX_FOODS:
        raise HSRAPIError(
            f"Maximum {HSR_CALCULATE_MAX_FOODS} foods can be analyzed at once"
        )
    
    for i, serving_size in enumerate(serving_sizes):
        if not isinstance(serving_size, (int, float)) or serving_size <= 0:
            raise HSRAPIError(f"Serving size {i+1} must be a positive number")
        if serving_size > 2000:
            raise HSRAPIError(f"Serving size {i+1} is too large (max 2000g)")


@lru_cache(maxsize=1000)
def _load_food_data(food_id: int, serving_size: float) -> HSRFood:
    """Load and cache food data for HSR calculation with auto-category assignment"""
    # Check cache first
    cache_key = f"hsr_food_{food_id}_{serving_size}"
    cached_food = cache.get(cache_key)
    if cached_food:
        return cached_food
    
    # Load from CNF pipeline
    food_details = get_cnf_pipeline().get_food_details(food_id)
    if not food_details:
        raise ValueError(f"Food with ID {food_id} not found in database")
    
    # Extract nutrients
    nutrients = {}
    for nutrient in food_details.get('NutrientValues', []):
        nutrients[nutrient['NutrientName']] = nutrient['NutrientValue']
    
    # Calculate FVNL content
    fvnl_percent = calculate_fvnl_content(food_id)
    
    # Create food object with auto-category assignment
    food = HSRFood(
        food_id=food_id,
        food_name=food_details['FoodDescription'],
        serving_size=serving_size,
        nutrients=nutrients,
        fvnl_percent=fvnl_percent,
        # Category will be auto-assigned in __post_init__ based on food_group_id
        food_group_id=food_details['FoodGroupID']
    )
    
    # Cache for 1 hour
    cache.set(cache_key, food, 3600)
    return food


def _calculate_simple_hsr(calculator: HSRCalculator) -> Dict:
    """Calculate simple HSR result for basic use cases"""
    result = calculator.calculate_hsr()
    
    # Backward compatible response format
    return {
        "success": True,
        "hsr_result": {
            "rating": {
                "star_rating": result.star_rating,
                "level": result.level.value,
                "description": f"{result.star_rating} star rating",
                "category": result.category.value
            },
            "validation": {
                "confidence_score": getattr(result, 'confidence_score', 0.8),
                "warnings": getattr(result, 'warnings', [])
            },
            "key_insights": {
                "strengths": len(result.strengths or []),
                "concerns": len(result.concerns or []),
                "top_strength": result.strengths[0].title if result.strengths else None,
                "top_concern": result.concerns[0].title if result.concerns else None
            },
            # Enhanced features (additional, doesn't break compatibility)
            "algorithm_info": {
                "uses_official_hsr_algorithm": True,
                "category_specific_thresholds": True,
                "standard_hsr_methodology": True
            }
        }
    }


def _calculate_detailed_hsr(calculator: HSRCalculator, include_alternatives: bool, 
                          include_meal_insights: bool) -> Dict:
    """Calculate detailed HSR result with comprehensive analysis"""
    result = calculator.calculate_hsr()
    
    response = {
        "success": True,
        "hsr_result": _format_detailed_hsr_result(result)
    }
    
    if include_alternatives:
        response["hsr_result"]["healthier_alternatives"] = _get_healthier_alternatives_for_meal(calculator.meal)
    
    if include_meal_insights:
        response["hsr_result"]["meal_insights"] = _get_meal_level_insights(calculator.meal, result)
    
    # Add basic nutritional summary
    response["hsr_result"]["nutritional_summary"] = {
        "total_energy_kj": calculator.meal.energy_kj,
        "total_protein_g": calculator.meal.protein,
        "total_fiber_g": calculator.meal.fibre_total_dietary,
        "total_sodium_mg": calculator.meal.sodium
    }
    
    return response


def _format_detailed_hsr_result(result) -> Dict:
    """Format detailed HSR result for API response"""
    return {
        "rating": {
            "star_rating": result.star_rating,
            "level": result.level.value,
            "description": f"{result.star_rating} star rating",
            "category": result.category.value
        },
        "score_breakdown": {
            "final_score": result.component_score.final_score,
            "baseline_points": result.component_score.baseline_points,
            "modifying_points": result.component_score.modifying_points,
            "components": {
                "energy": result.component_score.energy_points,
                "saturated_fat": result.component_score.saturated_fat_points,
                "sugar": result.component_score.sugar_points,
                "sodium": result.component_score.sodium_points,
                "protein": result.component_score.protein_points,
                "fiber": result.component_score.fiber_points,
                "fvnl": result.component_score.fvnl_points
            },
            # FIX (HSR audit #1 2026-05-23): the previous self-description
            # claimed `final_formula = "max(0, baseline - modifying)"`, which
            # contradicts both HSRAC v9 and the actual kernel output. The Rust
            # kernel returns negative final scores (e.g. apple raw at -7),
            # which is required for foods to reach 5 stars in Category 2
            # (cut-point ≤ -11). HSRAC v9 explicitly allows negative final
            # scores; lower = better. Frontend has been updated to match.
            "calculation_method": {
                "baseline_formula": "energy + saturated_fat + sugar + sodium",
                "modifying_formula": "protein + fiber + fvnl",
                "final_formula": "baseline − modifying (can be negative; lower is better)",
                "protein_eligibility_rule": (
                    "HSRAC v9 p. 26: if baseline ≥ 13 and V points < 5, "
                    "P points = 0."
                ),
                "category_specific": True,
            }
        },
        "nutritional_analysis": [
            {
                "nutrient": na.nutrient_name,
                "value": na.value,
                "unit": na.unit,
                "points": na.points,
                "impact": na.impact.value if hasattr(na.impact, 'value') else str(na.impact),
                "recommendation": na.recommendation
            } for na in (result.nutrient_analyses or [])
        ],
        "health_insights": {
            "strengths": [_format_health_insight(s) for s in (result.strengths or [])],
            "concerns": [_format_health_insight(c) for c in (result.concerns or [])],
            "recommendations": [_format_health_insight(r) for r in (result.recommendations or [])]
        },
        "validation": {
            "confidence_score": getattr(result, 'confidence_score', 0.8),
            "warnings": getattr(result, 'warnings', [])
        },
        # Official HSR algorithm confirmation
        "algorithm_verification": {
            "uses_official_hsr_algorithm": True,
            "category_specific_thresholds": True,
            "standard_hsr_methodology": True,
            "compliant_with_hsr_specification": True
        }
    }


def _format_health_insight(insight) -> Dict:
    """Format health insight for API response"""
    return {
        "title": insight.title,
        "description": insight.description,
        "category": insight.category,
        "priority": insight.priority,
        "actionable": getattr(insight, 'actionable', False),
        "action_text": getattr(insight, 'action_text', None)
    }


def _build_per_food_ratings(food_ids: List[int], serving_sizes: List[float]) -> List[Dict]:
    """SCORECARD-1: score each food individually in its own HSRAC v9 category
    at its actual gram amount (recall portion, not 100 g). This mirrors the
    /hsr/compare/ inner loop but uses the per-food serving size that arrived
    on the recall payload. One entry per food; failures are surfaced as
    {error: ...} so the caller can still summarise the rest."""
    out: List[Dict] = []
    for fid, serving in zip(food_ids, serving_sizes):
        try:
            food = _load_food_data(int(fid), float(serving))
            food_category = ThresholdProvider.get_category_from_food(
                food.food_name,
                getattr(food, 'food_group_id', 0),
            )
            per_meal = HSRMeal(foods=[food])
            per_meal.category = food_category
            per_calc = HSRCalculator(per_meal, HSRConfig(
                use_scientific_thresholds=False,
                differentiate_sugar_sources=False,
                apply_satiety_adjustments=False,
                use_unified_energy_approach=False,
                consider_processing_level=False,
            ))
            per_result = per_calc.calculate_hsr()
            out.append(_format_food_comparison(food, per_result, float(serving)))
        except Exception as exc:  # noqa: BLE001 — surface per-food, don't fail the batch
            out.append({"food_id": int(fid), "serving_size": float(serving),
                        "error": f"Per-food HSR failed: {exc}"})
    return out


def _summarise_per_food_ratings(ratings: List[Dict]) -> Dict:
    """Build the energy-weighted summary the Scorecard renders as the HSR
    card headline + driver. Weighting by energy avoids the "20 g banana
    counts the same as 290 g milk" pitfall of a simple mean. Falls back to
    simple mean when no energy data is available."""
    valid = [r for r in ratings if 'hsr_rating' in r]
    if not valid:
        return {"available": False}
    stars = [float(r['hsr_rating']) for r in valid]
    energies = [float(r.get('energy_kj') or 0.0) for r in valid]
    total_energy = sum(energies)
    if total_energy > 0:
        weighted = sum(s * e for s, e in zip(stars, energies)) / total_energy
    else:
        weighted = sum(stars) / len(stars)
    simple = sum(stars) / len(stars)
    highest = max(valid, key=lambda r: r['hsr_rating'])
    lowest = min(valid, key=lambda r: r['hsr_rating'])
    return {
        "available": True,
        "n_foods": len(valid),
        "n_failed": len(ratings) - len(valid),
        "energy_weighted_avg": round(weighted, 2),
        "simple_avg": round(simple, 2),
        "min": round(min(stars), 1),
        "max": round(max(stars), 1),
        "highest": {"food_id": highest['food_id'], "food_name": highest['food_name'],
                    "star_rating": highest['hsr_rating']},
        "lowest": {"food_id": lowest['food_id'], "food_name": lowest['food_name'],
                   "star_rating": lowest['hsr_rating']},
        "distribution": {
            "excellent":     len([s for s in stars if s >= 4.5]),
            "good":          len([s for s in stars if 3.5 <= s < 4.5]),
            "average":       len([s for s in stars if 2.5 <= s < 3.5]),
            "below_average": len([s for s in stars if 1.5 <= s < 2.5]),
            "poor":          len([s for s in stars if s < 1.5]),
        },
    }


def _format_food_comparison(food: HSRFood, result, serving_size: float) -> Dict:
    """Format food comparison data"""
    # Get proper food group info
    food_group_id = getattr(food, 'food_group_id', 0)
    group_info = FoodGroupMapper.get_food_group_info(food_group_id)
    
    # Category name mapping
    category_name_map = {
        '1': 'Beverage',
        '1D': 'Dairy Beverage', 
        '2': 'Food',
        '2D': 'Dairy Food',
        '3': 'Oils and Spreads',
        '3D': 'Cheese'
    }
    category_name = category_name_map.get(result.category.value, result.category.value)
    
    return {
        "food_id": food.food_id,
        "food_name": food.food_name,
        "serving_size": serving_size,
        "food_group": group_info['food_group_name'],
        "hsr_rating": result.star_rating,
        "hsr_level": result.level.value,
        "category": category_name,
        "energy_kj": result.total_energy_kj,
        "key_nutrients": {
            "protein": food.nutrients.get('PROTEIN', 0),
            "saturated_fat": food.nutrients.get('FATTY ACIDS, SATURATED, TOTAL', 0),
            "sugar": food.nutrients.get('SUGARS, TOTAL', 0),
            "sodium": food.nutrients.get('SODIUM', 0),
            "fiber": food.nutrients.get('FIBRE, TOTAL DIETARY', 0),
            "fvnl_percent": food.fvnl_percent
        },
        "top_strength": result.strengths[0].title if result.strengths else None,
        "top_concern": result.concerns[0].title if result.concerns else None
    }


def _generate_comparison_summary(comparisons: List[Dict], sort_by: str) -> Dict:
    """Generate summary statistics for food comparisons"""
    if not comparisons:
        return {}
    
    ratings = [c['hsr_rating'] for c in comparisons]
    
    return {
        "highest_rated": comparisons[0] if comparisons else None,
        "lowest_rated": comparisons[-1] if comparisons else None,
        "average_rating": sum(ratings) / len(ratings),
        "rating_distribution": {
            "excellent": len([r for r in ratings if r >= 4.5]),
            "good": len([r for r in ratings if 3.5 <= r < 4.5]),
            "average": len([r for r in ratings if 2.5 <= r < 3.5]),
            "below_average": len([r for r in ratings if 1.5 <= r < 2.5]),
            "poor": len([r for r in ratings if r < 1.5])
        }
    }


def _generate_comparison_recommendations(comparisons: List[Dict]) -> List[str]:
    """Generate recommendations based on food comparisons"""
    if not comparisons:
        return []
    
    recommendations = []
    
    # Find best and worst performers
    best = comparisons[0] if comparisons else None
    worst = comparisons[-1] if comparisons else None
    
    if best and worst and best['hsr_rating'] > worst['hsr_rating']:
        recommendations.append(f"Consider choosing {best['food_name']} over {worst['food_name']} for better nutritional value")
    
    # Check for high-rated options
    excellent_foods = [c for c in comparisons if c['hsr_rating'] >= 4.5]
    if excellent_foods:
        food_names = [f['food_name'] for f in excellent_foods[:3]]
        recommendations.append(f"Excellent choices: {', '.join(food_names)}")
    
    return recommendations


def _get_food_details_summary(foods: List[HSRFood]) -> List[Dict]:
    """Get summary of food details for user context.

    FIX (HSR audit #5 2026-05-23): the previous per-food category labels
    ("Beverage", "Food", ...) dropped the HSRAC v9 category code and short-
    formed the label, so the Analyzed Food card rendered just "Food" instead
    of the canonical "General foods (Category 2)". The category label is
    mandatory per HSRAC v9 Introduction (within-category-only comparison rule),
    so the label must be unambiguous and identify the v9 category.
    """
    # HSRAC v9 official 6-category labels — matches _CATEGORY_LABELS in
    # api/views/hsr_explanations.py and is the canonical source for the
    # within-category-only caveat anchor.
    category_name_map = {
        '1':  'Non-dairy beverages (Category 1)',
        '1D': 'Dairy beverages (Category 1D)',
        '2':  'General foods (Category 2)',
        '2D': 'Other dairy foods (Category 2D)',
        '3':  'Oils and spreads (Category 3)',
        '3D': 'Cheese (Category 3D)',
    }

    return [
        {
            "food_id": food.food_id,
            "food_name": food.food_name,
            "serving_size": food.serving_size,
            "category": category_name_map.get(food.category.value, food.category.value) if food.category else "unknown",
            "fvnl_percent": food.fvnl_percent,
            "food_group_id": getattr(food, 'food_group_id', None),
            "category_confidence": getattr(food, 'category_confidence', 0.0),
            "category_source": getattr(food, 'category_source', 'unknown')
        } for food in foods
    ]


def _get_basic_meal_categorization_summary(meal: HSRMeal) -> Dict:
    """Summary of meal categorization for the API response.

    FIX (HSR-CATEG-3 2026-05-23): the previous version only returned 3 fields
    (final_category / category_code / methodology), so the frontend HSR page
    saw `meal_categorization.category_confidence = 0.0` and missing reasoning /
    warnings / alternatives — even though `Meal.category_confidence` and
    `Meal.category_analysis` are correctly populated by `_determine_category`
    in `hsr_calculator/hsr/models/meal.py:82-92`. Now all the fields the
    frontend reads ([hsr/calculate/page.tsx:474-516]) are surfaced.
    """
    category_name_map = {
        Category.BEVERAGE:         'Category 1 - Non-dairy beverages',
        Category.DAIRY_BEVERAGE:   'Category 1D - Dairy beverages',
        Category.FOOD:             'Category 2 - General foods',
        Category.DAIRY_FOOD:       'Category 2D - Other dairy foods',
        Category.OILS_AND_SPREADS: 'Category 3 - Oils and spreads',
        Category.CHEESE:           'Category 3D - Cheese',
    }

    analysis = getattr(meal, 'category_analysis', {}) or {}
    confidence = float(getattr(meal, 'category_confidence', 0.0) or 0.0)
    warnings = list(getattr(meal, 'category_warnings', []) or [])

    # Alternative categories come as a list of (Category, fitness_float, reason_str) tuples
    alt_raw = analysis.get('alternative_categories', []) or []
    alternative_categories = []
    for entry in alt_raw:
        try:
            cat, fitness, reason = entry
            alternative_categories.append({
                'category':   cat.value if hasattr(cat, 'value') else str(cat),
                'fitness':    float(fitness),
                'reason':     str(reason),
            })
        except (ValueError, TypeError):
            # Defensive: if the tuple shape ever changes, skip silently
            continue

    return {
        "final_category": category_name_map.get(meal.category, "Category 2 - General foods") if meal.category else "unknown",
        "category_code": meal.category.value if meal.category else "2",
        "methodology": "Scientific categorisation per HSRAC v9 (FoodGroupMapper + MealCategorizer)",
        "category_confidence": confidence,
        "scientific_method": str(analysis.get('reason', 'scientific_categorization')),
        "reasoning": str(analysis.get('reasoning', '')),
        "nutritional_rationale": str(analysis.get('nutritional_rationale', '')),
        "alternative_categories": alternative_categories,
        "category_warnings": warnings,
    }




def _get_food_basic_info(food: HSRFood) -> Dict:
    """Get basic food information"""
    # Get food group info using the actual food_group_id
    food_group_id = getattr(food, 'food_group_id', 0)
    group_info = FoodGroupMapper.get_food_group_info(food_group_id)
    
    # Get human-readable category name
    category_name_map = {
        '1': 'Beverage',
        '1D': 'Dairy Beverage', 
        '2': 'Food',
        '2D': 'Dairy Food',
        '3': 'Oils and Spreads',
        '3D': 'Cheese'
    }
    category_name = category_name_map.get(food.category.value, food.category.value) if food.category else 'Unknown'
    
    return {
        "food_id": food.food_id,
        "food_name": food.food_name,
        "serving_size": food.serving_size,
        "food_group": group_info['food_group_name'],
        "hsr_category": category_name,
        "fvnl_percent": food.fvnl_percent
    }


def _get_nutritional_highlights(food: HSRFood, result) -> Dict:
    """Get key nutritional highlights for the food"""
    highlights = {
        "high_in": [],
        "low_in": [],
        "good_source_of": []
    }
    
    # Check for high beneficial nutrients
    if food.nutrients.get('PROTEIN', 0) > 15:
        highlights["good_source_of"].append("protein")
    elif food.nutrients.get('PROTEIN', 0) > 10:
        highlights["high_in"].append("protein")
    
    if food.nutrients.get('FIBRE, TOTAL DIETARY', 0) > 8:
        highlights["good_source_of"].append("fiber")
    elif food.nutrients.get('FIBRE, TOTAL DIETARY', 0) > 5:
        highlights["high_in"].append("fiber")
    
    # Specific FVNL categorization based on food group
    if food.fvnl_percent > 67:
        food_group_id = getattr(food, 'food_group_id', 0)
        
        if food_group_id == 9:  # Fruits
            highlights["good_source_of"].append("vitamin C and natural fruit nutrients")
        elif food_group_id == 11:  # Vegetables
            highlights["good_source_of"].append("vitamins, minerals, and fiber")
        elif food_group_id == 12:  # Nuts and Seeds
            highlights["good_source_of"].append("healthy fats and protein")
        elif food_group_id == 16:  # Legumes
            highlights["good_source_of"].append("plant protein and fiber")
        else:
            # Mixed foods with high FVNL content
            highlights["good_source_of"].append("nutrients from plant foods")
    
    # Check for concerning nutrients
    if food.nutrients.get('FATTY ACIDS, SATURATED, TOTAL', 0) > 5:
        highlights["high_in"].append("saturated fat")
    
    if food.nutrients.get('SUGARS, TOTAL', 0) > 15:
        highlights["high_in"].append("sugar")
    
    if food.nutrients.get('SODIUM', 0) > 600:
        highlights["high_in"].append("sodium")
    
    return highlights


def _get_usage_recommendations(food: HSRFood, result) -> List[str]:
    """Get usage recommendations for the food"""
    recommendations = []
    
    if result.star_rating >= 4.0:
        recommendations.append("Great choice for regular consumption")
    elif result.star_rating >= 3.0:
        recommendations.append("Good as part of a balanced diet")
    else:
        recommendations.append("Enjoy in moderation")
    
    # Add specific recommendations based on nutrients
    if food.nutrients.get('SODIUM', 0) > 600:
        recommendations.append("Consider pairing with low-sodium foods")
    
    if food.nutrients.get('FIBRE, TOTAL DIETARY', 0) > 5:
        recommendations.append("Great for digestive health")
    
    return recommendations


def _get_healthier_alternatives(food: HSRFood) -> List[Dict]:
    """Get healthier alternatives for a food (simplified implementation)"""
    # This is a simplified version - in production, you'd use a recommendation engine
    food_group_id = getattr(food, 'food_group_id', 0)
    group_info = FoodGroupMapper.get_food_group_info(food_group_id)
    group_name = group_info['food_group_name']
    
    suggestions = {
        "Dairy and Egg Products": ["Choose low-fat dairy options", "Try plant-based alternatives"],
        "Baked Products": ["Choose whole grain versions", "Look for products with less added sugar"],
        "Sweets": ["Try fresh fruits", "Choose dark chocolate with less sugar"],
        "Fast Foods": ["Prepare homemade versions", "Choose grilled over fried options"],
        "Beverages": ["Choose water or unsweetened drinks", "Try herbal teas"]
    }
    
    return [{
        "category": group_name,
        "suggestions": suggestions.get(group_name, ["Choose less processed alternatives"])
    }]


def _get_healthier_alternatives_for_meal(meal: HSRMeal) -> List[Dict]:
    """Get healthier alternatives for meal components"""
    alternatives = []
    for food in meal.foods:
        alt = _get_healthier_alternatives(food)
        if alt:
            alternatives.extend(alt)
    return alternatives


def _get_meal_level_insights(meal: HSRMeal, result) -> Dict:
    """Get meal-level insights and recommendations"""
    return {
        "meal_composition": {
            "total_foods": len(meal.foods),
            "total_weight": meal.total_weight,
            "dominant_category": meal.category.value,
            "energy_density": meal.energy_kj / meal.total_weight if meal.total_weight > 0 else 0
        },
        "nutritional_balance": {
            "protein_adequate": meal.protein >= 15,
            "fiber_adequate": meal.fibre_total_dietary >= 5,
            "sodium_concern": meal.sodium > 600,
            "sugar_concern": meal.sugars_total > 15
        },
        "meal_suitability": _suggest_meal_timing(meal)
    }


def _suggest_meal_timing(meal: HSRMeal) -> str:
    """Suggest appropriate meal timing based on nutritional profile"""
    if meal.total_weight < 50:
        return "Suitable as a snack"
    elif meal.energy_kilocalories < 200:
        return "Suitable as a light meal or snack"
    elif meal.energy_kilocalories < 400:
        return "Suitable as a light meal"
    else:
        return "Suitable as a main meal"


def _analyze_meal_composition(foods: List[HSRFood], result) -> Dict:
    """Analyze meal composition and balance"""
    total_weight = sum(food.serving_size for food in foods)
    
    # Food group distribution
    group_weights = {}
    for food in foods:
        food_group_id = getattr(food, 'food_group_id', 0)
        group_info = FoodGroupMapper.get_food_group_info(food_group_id)
        group_name = group_info['food_group_name']
        group_weights[group_name] = group_weights.get(group_name, 0) + food.serving_size
    
    # Convert to percentages
    group_percentages = {group: (weight / total_weight) * 100 
                        for group, weight in group_weights.items()}
    
    return {
        "total_foods": len(foods),
        "total_weight": total_weight,
        "food_group_distribution": group_percentages,
        "dominant_groups": sorted(group_percentages.items(), key=lambda x: x[1], reverse=True)[:3]
    }


def _analyze_nutritional_balance(meal: HSRMeal, result) -> Dict:
    """Analyze nutritional balance of the meal"""
    total_kcal = meal.energy_kilocalories
    
    if total_kcal > 0:
        protein_kcal = meal.protein * 4
        carb_kcal = meal.carbohydrate_total * 4
        fat_kcal = meal.fat_total * 9
        
        macronutrient_distribution = {
            'protein_percent': (protein_kcal / total_kcal) * 100,
            'carbohydrate_percent': (carb_kcal / total_kcal) * 100,
            'fat_percent': (fat_kcal / total_kcal) * 100
        }
    else:
        macronutrient_distribution = {}
    
    return {
        "macronutrient_distribution": macronutrient_distribution,
        "nutrient_density": {
            "protein_per_100g": meal.protein,
            "fiber_per_100g": meal.fibre_total_dietary,
            "sodium_per_100g": meal.sodium,
            "fvnl_percent": meal.fvnl_percent
        },
        "nutritional_quality": {
            "high_protein": meal.protein >= 15,
            "high_fiber": meal.fibre_total_dietary >= 5,
            "high_fvnl": meal.fvnl_percent >= 67,
            "low_sodium": meal.sodium <= 400,
            "low_sugar": meal.sugars_total <= 10
        }
    }


def _get_hsr_breakdown(result) -> Dict:
    """Get detailed HSR score breakdown"""
    return {
        "final_rating": result.star_rating,
        "rating_level": result.level.value,
        "score_components": {
            "risk_nutrients": {
                "energy": result.component_score.energy_points,
                "saturated_fat": result.component_score.saturated_fat_points,
                "sugar": result.component_score.sugar_points,
                "sodium": result.component_score.sodium_points,
                "total": result.component_score.baseline_points
            },
            "beneficial_nutrients": {
                "protein": result.component_score.protein_points,
                "fiber": result.component_score.fiber_points,
                "fvnl": result.component_score.fvnl_points,
                "total": result.component_score.modifying_points
            },
            "final_score": result.component_score.final_score
        }
    }


def _identify_improvement_opportunities(foods: List[HSRFood], result) -> List[Dict]:
    """Identify opportunities to improve the meal's nutritional profile"""
    opportunities = []
    
    # Check for low fiber
    total_fiber = sum(food.nutrients.get('FIBRE, TOTAL DIETARY', 0) * food.serving_size / 100 for food in foods)
    if total_fiber < 5:
        opportunities.append({
            "area": "fiber",
            "current": total_fiber,
            "target": 5,
            "suggestion": "Add fruits, vegetables, or whole grains"
        })
    
    # Check for high sodium
    total_sodium = sum(food.nutrients.get('SODIUM', 0) * food.serving_size / 100 for food in foods)
    if total_sodium > 600:
        opportunities.append({
            "area": "sodium",
            "current": total_sodium,
            "target": 400,
            "suggestion": "Choose lower-sodium alternatives"
        })
    
    # Check for low FVNL
    fvnl_percent = sum(food.serving_size * food.fvnl_percent / 100 for food in foods) / sum(food.serving_size for food in foods) * 100
    if fvnl_percent < 40:
        opportunities.append({
            "area": "fvnl",
            "current": fvnl_percent,
            "target": 67,
            "suggestion": "Add more fruits, vegetables, nuts, or legumes"
        })
    
    return opportunities


def _assess_meal_type_suitability(meal: HSRMeal, meal_type: Optional[str]) -> Optional[Dict]:
    """Assess how suitable the meal is for a specific meal type"""
    if not meal_type:
        return None
    
    energy_kcal = meal.energy_kilocalories
    protein_g = meal.protein
    
    suitability_scores = {
        "breakfast": {
            "energy_suitable": 200 <= energy_kcal <= 400,
            "protein_adequate": protein_g >= 15,
            "fiber_good": meal.fibre_total_dietary >= 3,
            "sugar_moderate": meal.sugars_total <= 20
        },
        "lunch": {
            "energy_suitable": 300 <= energy_kcal <= 600,
            "protein_adequate": protein_g >= 20,
            "fiber_good": meal.fibre_total_dietary >= 5,
            "sodium_moderate": meal.sodium <= 800
        },
        "dinner": {
            "energy_suitable": 400 <= energy_kcal <= 700,
            "protein_adequate": protein_g >= 25,
            "fiber_good": meal.fibre_total_dietary >= 5,
            "sodium_moderate": meal.sodium <= 600
        },
        "snack": {
            "energy_suitable": 50 <= energy_kcal <= 200,
            "protein_adequate": protein_g >= 5,
            "portion_appropriate": meal.total_weight <= 100
        }
    }
    
    criteria = suitability_scores.get(meal_type.lower(), {})
    
    # If meal type is not recognized, return null to prompt user
    if not criteria:
        return None
    
    suitable_count = sum(1 for suitable in criteria.values() if suitable)
    total_criteria = len(criteria)
    suitability_ratio = suitable_count / total_criteria if total_criteria > 0 else 0
    
    return {
        "meal_type": meal_type,
        "suitability_score": suitability_ratio,
        "criteria_met": criteria,
        "recommendation": "Excellent fit" if suitability_ratio >= 0.8 else
                          "Good fit" if suitability_ratio >= 0.6 else
                          "Moderate fit" if suitability_ratio >= 0.4 else
                          "Poor fit"
    }


def _assess_dietary_goal_alignment(meal: HSRMeal, result, dietary_goals: List[str]) -> Optional[Dict]:
    """Assess how well the meal aligns with dietary goals"""
    if not dietary_goals:
        return None
    
    goal_assessments = {}
    
    for goal in dietary_goals:
        if goal == "weight_loss":
            energy_ok = meal.energy_kilocalories <= 400
            protein_ok = meal.protein >= 15
            fiber_ok = meal.fibre_total_dietary >= 5
            
            goal_assessments[goal] = {
                "energy_appropriate": energy_ok,
                "protein_adequate": protein_ok,
                "fiber_high": fiber_ok,
                "score": 0.8 if energy_ok and protein_ok else 0.6 if energy_ok or protein_ok else 0.3
            }
        elif goal == "heart_health":
            sat_fat_ok = meal.fatty_acids_saturated_total <= 3
            sodium_ok = meal.sodium <= 400
            fiber_ok = meal.fibre_total_dietary >= 5
            
            goal_assessments[goal] = {
                "low_saturated_fat": sat_fat_ok,
                "low_sodium": sodium_ok,
                "high_fiber": fiber_ok,
                "score": 0.9 if (sat_fat_ok and sodium_ok and fiber_ok) else 
                        0.7 if (sat_fat_ok and sodium_ok) else 
                        0.5 if sat_fat_ok else 0.3
            }
        elif goal == "diabetes_management":
            sugar_ok = meal.sugars_total <= 10
            fiber_ok = meal.fibre_total_dietary >= 5
            carbs_ok = meal.carbohydrate_total <= 30
            
            goal_assessments[goal] = {
                "low_sugar": sugar_ok,
                "high_fiber": fiber_ok,
                "moderate_carbs": carbs_ok,
                "score": 0.8 if (sugar_ok and fiber_ok) else 
                        0.6 if sugar_ok else 
                        0.4 if fiber_ok else 0.2
            }
    
    return goal_assessments if goal_assessments else None 