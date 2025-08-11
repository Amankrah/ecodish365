import os
import sys
import logging
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Add heni_calculator to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../heni_calculator'))

from heni_calculator.heni.database.cnf_integrator import create_heni_cnf_integrator
from heni_calculator.heni.models.ingredient import Ingredient
from heni_calculator.heni.calculator.heni_calculator import HENICalculator
from api.seo_utils import seo_metadata
from .heni_analysis_helpers import (
    _identify_primary_health_drivers,
    _get_epidemiological_context, 
    _estimate_population_impact,
    _generate_policy_recommendations,
    _get_comparison_benchmarks,
    _classify_dietary_pattern,
    _assess_intervention_priority,
    _identify_target_food_groups,
    _calculate_serving_impact,
    _aggregate_disease_burdens,
    _aggregate_risk_factors
)

logger = logging.getLogger(__name__)

# Global integrator instance to avoid initialization overhead
_heni_integrator = None

def get_heni_integrator():
    global _heni_integrator
    if _heni_integrator is None:
        cnf_dir = settings.CNF_FOLDER
        _heni_integrator = create_heni_cnf_integrator(cnf_dir)
    return _heni_integrator

@api_view(['POST'])
@seo_metadata(
    title="Health and Nutritional Impact (HENI) Calculator | DISH Research",
    description="Calculate the Health and Nutritional Impact (HENI) score for your meals. Analyze the health benefits of your food choices.",
    keywords="HENI, health impact, nutritional impact, meal analysis, healthy eating"
)
def heni_calculate(request):
    """Calculate HENI score for meals with specified ingredients and amounts."""
    try:
        meal_data = request.data.get('meal', [])
        
        if not meal_data:
            return Response({"error": "'meal' array with ingredients is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(meal_data, list) or len(meal_data) == 0:
            return Response({"error": "Meal array cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate input data
        ingredients = []
        integrator = get_heni_integrator()
        
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
        
        # Get LLM API key from settings
        llm_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not llm_api_key:
            logger.warning("No OpenAI API key configured, HENI categorization may be limited")
            llm_api_key = ""  # Use empty string as fallback
        
        # Calculate HENI using the comprehensive methodology
        heni_calculator = HENICalculator(integrator, llm_api_key)
        comprehensive_result = heni_calculator.calculate_meal_heni(ingredients)
        
        result = {
            "success": True,
            "data": comprehensive_result,
            "metadata": {
                "calculation_method": "DALY-based HENI scoring",
                "reference": "Global Burden of Disease epidemiological evidence",
                "last_updated": "2024",
                "units": "μDALY (micro-Disability Adjusted Life Years)"
            }
        }
        
        return Response(result)
    
    except Exception as e:
        logger.exception(f"An error occurred in HENI calculation: {str(e)}")
        return Response({"error": "An unexpected error occurred during HENI calculation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
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
        
        integrator = get_heni_integrator()
        
        # Create ingredient and calculate HENI
        ingredient = Ingredient(
            food_id=food_id,
            amount=amount_g,
            unit='g',
            cnf_integrator=integrator
        )
        
        llm_api_key = getattr(settings, 'OPENAI_API_KEY', "")
        heni_calculator = HENICalculator(integrator, llm_api_key)
        
        comprehensive_result = heni_calculator.calculate_meal_heni([ingredient])
        
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


@api_view(['POST'])
@seo_metadata(
    title="HENI Diet Pattern Analysis | DISH Research", 
    description="Analyze complete dietary patterns for population health impact assessment",
    keywords="HENI, diet analysis, population health, dietary patterns, epidemiology"
)
def analyze_dietary_pattern(request):
    """
    Comprehensive dietary pattern analysis for population health studies
    Designed for researchers and policy makers analyzing dietary interventions
    """
    try:
        pattern_data = request.data.get('dietary_pattern', {})
        meals = pattern_data.get('meals', [])
        analysis_parameters = pattern_data.get('parameters', {})
        
        if not meals:
            return Response({"error": "At least one meal is required for dietary pattern analysis"}, status=status.HTTP_400_BAD_REQUEST)
        
        integrator = get_heni_integrator()
        llm_api_key = getattr(settings, 'OPENAI_API_KEY', "")
        
        # Analyze each meal
        meal_analyses = []
        total_daily_heni = 0
        total_daily_kcal = 0
        
        for i, meal in enumerate(meals):
            meal_ingredients = []
            meal_name = meal.get('meal_name', f'Meal {i+1}')
            
            for item in meal.get('foods', []):
                ingredient = Ingredient(
                    food_id=item['food_id'],
                    amount=float(item['amount']),
                    unit=item.get('unit', 'g'),
                    cnf_integrator=integrator
                )
                meal_ingredients.append(ingredient)
            
            # Calculate meal HENI
            heni_calculator = HENICalculator(integrator, llm_api_key)
            meal_analysis = heni_calculator.calculate_meal_heni(meal_ingredients)
            
            meal_analysis['meal_name'] = meal_name
            meal_analyses.append(meal_analysis)
            
            total_daily_heni += meal_analysis['heni_scores']['total_heni_score']
            total_daily_kcal += meal_analysis['meal_composition']['total_energy_kcal']
        
        # Population analysis
        population_size = analysis_parameters.get('population_size', 100000)
        time_horizon_years = analysis_parameters.get('time_horizon_years', 10)
        
        # Calculate population impact
        from heni_calculator.heni.core.daly_calculator import DALYCalculator
        daly_calc = DALYCalculator()
        
        # Simulate population results (simplified for API)
        mock_individual_results = []
        for _ in range(min(1000, population_size // 100)):  # Sample for efficiency
            # Create mock HENIResult with current analysis
            class MockResult:
                def __init__(self, total_heni, health_minutes):
                    self.total_heni_score = total_heni
                    self.health_impact_minutes = health_minutes
            
            mock_individual_results.append(MockResult(total_daily_heni, total_daily_heni * 0.5256))
        
        population_impact = daly_calc.calculate_population_impact(mock_individual_results, population_size)
        
        # Comprehensive analysis result
        analysis_result = {
            "dietary_pattern_summary": {
                "total_meals_analyzed": len(meals),
                "daily_heni_score": round(total_daily_heni, 2),
                "daily_energy_kcal": round(total_daily_kcal, 1),
                "daily_health_impact_minutes": round(total_daily_heni * 0.5256, 1),
                "pattern_classification": _classify_dietary_pattern(total_daily_heni)
            },
            "meal_breakdowns": meal_analyses,
            "population_health_impact": {
                **population_impact,
                "time_horizon_years": time_horizon_years,
                "projected_dalys_avoided": population_impact.get('total_dalys_avoided', 0) * time_horizon_years,
                "health_economic_value": population_impact.get('economic_value_usd', 0) * time_horizon_years
            },
            "policy_insights": {
                "intervention_priority": _assess_intervention_priority(meal_analyses),
                "target_food_groups": _identify_target_food_groups(meal_analyses),
                "expected_impact_per_serving_change": _calculate_serving_impact(meal_analyses)
            },
            "epidemiological_context": {
                "primary_disease_burdens": _aggregate_disease_burdens(meal_analyses),
                "risk_factor_contributions": _aggregate_risk_factors(meal_analyses),
                "evidence_strength": "High (based on Global Burden of Disease meta-analyses)"
            }
        }
        
        return Response({
            "success": True,
            "data": analysis_result,
            "metadata": {
                "analysis_type": "Comprehensive Dietary Pattern Assessment",
                "population_scope": f"{population_size:,} individuals over {time_horizon_years} years",
                "methodology": "DALY-based population health impact modeling"
            }
        })
    
    except Exception as e:
        logger.exception(f"Error in dietary pattern analysis: {str(e)}")
        return Response({"error": "An unexpected error occurred during dietary pattern analysis"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)