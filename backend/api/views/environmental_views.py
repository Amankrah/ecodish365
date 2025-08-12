import logging
from typing import Dict, Any, List
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
from environmental_impact_model.src.food import Food as EnvFood
from environmental_impact_model.src.meal import Meal as EnvMeal
from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment
from environmental_impact_model.src.monetization import Monetization
from environmental_impact_model.src.reference_meals import ReferenceMeals
from environmental_impact_model.src.cnf_integrator import get_cnf_integrator
from environmental_impact_model.src.utils import format_impact_value, categorize_sustainability_score
from api.seo_utils import seo_metadata

logger = logging.getLogger(__name__)

def get_user_explanations(user_type: str = "individual") -> Dict[str, Dict[str, str]]:
    """
    Get user-friendly explanations tailored to different audience types.
    """
    explanations = {
        "individual": {
            "monetization": {
                "title": "💰 Environmental Cost in Dollars",
                "simple_explanation": "This shows what your meal's environmental impact costs society in Canadian dollars.",
                "detailed_explanation": "Every meal has hidden environmental costs - like climate change from greenhouse gases, health costs from air pollution, and cleanup costs for water contamination. We calculate these real costs in dollars so you can understand the true price of your food choices.",
                "what_it_means": "A higher cost means your meal has a bigger environmental impact on our planet and future generations.",
                "action_tips": "Choose meals with lower environmental costs to save money for society and protect the environment."
            },
            "reference_meals": {
                "title": "📊 How Your Meal Compares",
                "simple_explanation": "We compare your meal to three typical meal types to show you where it stands.",
                "detailed_explanation": "We created three reference meals: (1) Sustainable meals with mostly plants, local foods, and minimal processing, (2) Unsustainable meals with lots of red meat and processed foods, (3) Ultra-processed meals with packaged and fast foods.",
                "what_it_means": "Numbers above 1.0 mean your meal has more environmental impact than that meal type. Numbers below 1.0 mean less impact.",
                "action_tips": "Aim for your meal to be similar to or better than the sustainable meal (ratio close to 1.0 or lower)."
            },
            "lca_results": {
                "title": "🌍 Environmental Impact Categories",
                "simple_explanation": "These show different ways your meal affects the environment.",
                "detailed_explanation": "Life Cycle Assessment (LCA) looks at your meal's environmental impact from farm to plate, including carbon footprint (climate change), water use, land use, and effects on human health and ecosystems.",
                "what_it_means": "Each category shows a different environmental impact. Lower numbers are better for the planet.",
                "action_tips": "Focus on reducing the highest impact categories by choosing different ingredients."
            }
        },
        "researcher": {
            "monetization": {
                "title": "Economic Valuation of Environmental Externalities",
                "simple_explanation": "Monetary valuation of environmental impacts using established economic methods.",
                "detailed_explanation": "Environmental externalities are monetized using peer-reviewed valuation methods including: Social Cost of Carbon (Environment Canada, 2024), health impact valuations (DALY-based), ecosystem service valuations, and resource scarcity costs. Values are adjusted for Canadian context and inflation.",
                "what_it_means": "Represents the economic cost to society of environmental damage caused by food production and consumption.",
                "action_tips": "Use for cost-benefit analysis, policy evaluation, and comparing intervention scenarios."
            },
            "reference_meals": {
                "title": "Standardized Meal Compositions for Scientific Comparison",
                "simple_explanation": "Controlled meal compositions representing different dietary patterns for benchmarking.",
                "detailed_explanation": "Reference meals are constructed using systematic food selection criteria: (1) Sustainable: Plant-forward, minimally processed, local when possible, (2) Unsustainable: Animal product-heavy, resource-intensive foods, (3) Ultra-processed: High degree of processing, packaging, and industrial ingredients. Portions are standardized by meal type and caloric content.",
                "what_it_means": "Provides standardized baselines for comparative analysis across studies and populations.",
                "action_tips": "Use as control groups for intervention studies or population-level dietary pattern analysis."
            },
            "lca_results": {
                "title": "Life Cycle Assessment Using ReCiPe 2016 Methodology",
                "simple_explanation": "Comprehensive environmental impact assessment using internationally recognized LCA standards.",
                "detailed_explanation": "Midpoint impacts calculated using ReCiPe 2016 methodology with Canadian regional factors. Includes 18 impact categories covering climate change, human health, ecosystem quality, and resource depletion. Functional unit normalized to per 100 kcal for nutritional comparability.",
                "what_it_means": "Scientifically robust environmental assessment suitable for peer review and academic publication.",
                "action_tips": "Results are comparable with international LCA databases and can be used in meta-analyses."
            }
        },
        "policy": {
            "monetization": {
                "title": "Policy-Relevant Environmental Cost Estimates",
                "simple_explanation": "Economic estimates of environmental damages for policy analysis and decision-making.",
                "detailed_explanation": "Monetized impacts provide policy-relevant cost estimates for regulatory impact assessment, carbon pricing mechanisms, and public investment decisions. Based on Government of Canada's Social Cost of Carbon ($185/tonne CO2, 2024) and established environmental economics literature with Canadian-specific adjustments.",
                "what_it_means": "Quantifies the economic rationale for environmental policies and interventions in the food system.",
                "action_tips": "Use for policy cost-effectiveness analysis, taxation/subsidy design, and public health investment prioritization."
            },
            "reference_meals": {
                "title": "Policy Scenario Benchmarks",
                "simple_explanation": "Representative dietary patterns for policy scenario modeling and target setting.",
                "detailed_explanation": "Reference meals represent policy-relevant dietary patterns aligned with: (1) Canada's Food Guide recommendations (sustainable), (2) Current average Canadian diet patterns (unsustainable), (3) Worst-case processed food scenarios (ultra-processed). Enable assessment of policy interventions and dietary guideline impacts.",
                "what_it_means": "Provides baseline scenarios for evaluating policy effectiveness and setting environmental targets.",
                "action_tips": "Use for dietary guideline development, food policy evaluation, and environmental target setting."
            },
            "lca_results": {
                "title": "Environmental Performance Indicators for Food Policy",
                "simple_explanation": "Standardized environmental metrics aligned with international climate and sustainability commitments.",
                "detailed_explanation": "Impact categories align with Canada's climate commitments (Net Zero 2050), UN Sustainable Development Goals, and international environmental agreements. Methodology consistent with ISO 14044 LCA standards and UNEP-SETAC guidelines for food system assessment.",
                "what_it_means": "Provides evidence base for food-related environmental policies and regulatory frameworks.",
                "action_tips": "Results support evidence-based policy development, progress monitoring, and international reporting."
            }
        }
    }
    
    return explanations.get(user_type, explanations["individual"])

def format_environmental_results(meal_data: Dict[str, Any], user_type: str = "individual") -> Dict[str, Any]:
    """
    Format environmental results with user-appropriate explanations and context.
    """
    explanations = get_user_explanations(user_type)
    
    # Format monetization results with clear explanations
    monetization_data = meal_data.get('monetization', {})
    # Build monetized_impacts by flattening per-category individual impacts if not explicitly provided
    _flat_monetized_impacts = {}
    try:
        for _info in (monetization_data.get('cost_breakdown_by_category') or {}).values():
            for _impact, _cost in (_info.get('individual_impacts') or {}).items():
                _flat_monetized_impacts[_impact] = _flat_monetized_impacts.get(_impact, 0) + float(_cost or 0)
    except Exception:
        _flat_monetized_impacts = {}

    formatted_monetization = {
        "explanation": explanations["monetization"],
        "results": {
            "total_environmental_cost": {
                "value": monetization_data.get('total_cost', 0),
                "unit": "CAD",
                "formatted": f"${monetization_data.get('total_cost', 0):.3f} CAD",
                "context": "Total cost of environmental damage caused by this meal"
            },
            "cost_per_calorie": {
                "value": monetization_data.get('cost_per_calorie', 0),
                "unit": "CAD/kcal",
                "formatted": f"${monetization_data.get('cost_per_calorie', 0):.5f} CAD per calorie",
                "context": "Environmental cost per calorie consumed"
            },
            "cost_per_protein": {
                "value": monetization_data.get('cost_per_protein', 0),
                "unit": "CAD/g protein",
                "formatted": f"${monetization_data.get('cost_per_protein', 0):.5f} CAD per gram protein",
                "context": "Environmental cost per gram of protein"
            },
            "top_cost_drivers": monetization_data.get('top_cost_drivers', [])[:3],
            "cost_breakdown": monetization_data.get('cost_breakdown_by_category', {}),
            "monetized_impacts": _flat_monetized_impacts,
        },
        "interpretation": _get_cost_interpretation(monetization_data.get('total_cost', 0), user_type)
    }
    
    # Format reference meal comparisons with clear explanations
    reference_data = meal_data.get('reference_comparisons', {})
    formatted_comparisons = {
        "explanation": explanations["reference_meals"],
        "results": {},
        "interpretation": {}
    }
    
    for meal_type, comparison_data in reference_data.items():
        if 'error' not in comparison_data:
            cost_ratio = comparison_data.get('cost_ratio', 1.0)
            carbon_ratio = comparison_data.get('carbon_ratio', 1.0)
            
            formatted_comparisons["results"][meal_type] = {
                "environmental_cost_ratio": {
                    "value": cost_ratio,
                    "formatted": f"{cost_ratio:.2f}x",
                    "meaning": _get_ratio_meaning(cost_ratio)
                },
                "carbon_footprint_ratio": {
                    "value": carbon_ratio,
                    "formatted": f"{carbon_ratio:.2f}x",
                    "meaning": _get_ratio_meaning(carbon_ratio)
                },
                "reference_meal_description": _get_meal_description(meal_type)
            }
            
            formatted_comparisons["interpretation"][meal_type] = _get_comparison_interpretation(cost_ratio, carbon_ratio, meal_type, user_type)
    
    # Format LCA results with explanations
    lca_data = meal_data.get('lca', {})
    formatted_lca = {
        "explanation": explanations["lca_results"],
        "key_impacts": {
            "carbon_footprint": {
                "value": lca_data.get('midpoint_impacts', {}).get('Global warming', 0),
                "unit": "kg CO2-eq",
                "formatted": format_impact_value(lca_data.get('midpoint_impacts', {}).get('Global warming', 0), "kg CO2-eq"),
                "category": "Climate Change",
                "importance": "Primary driver of global warming and climate change"
            },
            "water_consumption": {
                "value": lca_data.get('midpoint_impacts', {}).get('Water consumption', 0),
                "unit": "m³",
                "formatted": format_impact_value(lca_data.get('midpoint_impacts', {}).get('Water consumption', 0), "m³"),
                "category": "Resource Use",
                "importance": "Freshwater resource depletion"
            },
            "land_use": {
                "value": lca_data.get('midpoint_impacts', {}).get('Land use', 0),
                "unit": "m²a crop-eq",
                "formatted": format_impact_value(lca_data.get('midpoint_impacts', {}).get('Land use', 0), "m²a crop-eq"),
                "category": "Ecosystem Impact",
                "importance": "Land conversion and biodiversity impact"
            }
        },
        "summary_score": {
            "value": lca_data.get('single_score', 0),
            "formatted": f"{lca_data.get('single_score', 0):.3e} points",
            "explanation": "Single aggregated score combining all environmental impacts"
        },
        "all_impacts": lca_data.get('midpoint_impacts', {}),
        "endpoint_impacts": lca_data.get('endpoint_impacts', {})
    }
    
    # Surface sustainability scores (numeric) calculated server-side so the UI
    # does not need to infer them. Keep a minimal, stable shape.
    sustainability_raw = meal_data.get('sustainability', {}) or {}
    formatted_sustainability = {
        "overall_sustainability_score": sustainability_raw.get('overall_sustainability_score', 50),
        "sustainability_rating": sustainability_raw.get('sustainability_rating', 'Unknown'),
        # Optional granular scores (if we add them in the future). Keep empty defaults for now.
        "environmental_score": sustainability_raw.get('environmental_score'),
        "nutritional_score": sustainability_raw.get('nutritional_score'),
        "processing_score": sustainability_raw.get('processing_score'),
        "category_scores": sustainability_raw.get('category_scores', {}),
        # Provide a simple recommendation aligned with overall assessment below
        "recommendations": []
    }

    # Add a simple recommendation based on the overall assessment that we compute below
    # (We keep this small coupling to avoid duplicating logic.)
    # This will be filled after overall assessment is computed.

    return {
        "monetization": formatted_monetization,
        "reference_comparisons": formatted_comparisons,
        "environmental_impacts": formatted_lca,
        # Include sustainability block so clients can render numeric score directly
        "sustainability": formatted_sustainability,
        "overall_assessment": _get_overall_assessment(meal_data, user_type)
    }

def _get_cost_interpretation(total_cost: float, user_type: str) -> Dict[str, str]:
    """Get interpretation of environmental cost based on user type."""
    interpretations = {
        "individual": {
            "low": "Great choice! This meal has a low environmental cost.",
            "medium": "This meal has a moderate environmental impact. Consider choosing more plant-based options.",
            "high": "This meal has a high environmental cost. Try reducing meat portions or choosing more sustainable ingredients."
        },
        "researcher": {
            "low": "Below median environmental cost for this meal category.",
            "medium": "Within expected range for mixed dietary patterns.",
            "high": "Above 75th percentile for environmental cost, indicating high-impact food choices."
        },
        "policy": {
            "low": "Aligned with sustainable dietary targets and climate objectives.",
            "medium": "Moderate environmental externalities requiring policy attention.",
            "high": "Significant externalities warranting regulatory consideration or intervention."
        }
    }
    
    if total_cost < 0.05:
        level = "low"
    elif total_cost < 0.20:
        level = "medium" 
    else:
        level = "high"
    
    return {
        "level": level,
        "message": interpretations.get(user_type, interpretations["individual"])[level],
        "context": f"Based on environmental cost of ${total_cost:.3f} CAD"
    }

def _get_ratio_meaning(ratio: float) -> str:
    """Get human-readable meaning of comparison ratios."""
    if ratio < 0.5:
        return "Much better (less than half the impact)"
    elif ratio < 0.8:
        return "Better (lower impact)"
    elif ratio < 1.2:
        return "Similar impact"
    elif ratio < 2.0:
        return "Worse (higher impact)"
    else:
        return "Much worse (more than double the impact)"

def _get_meal_description(meal_type: str) -> str:
    """Get description of reference meal types."""
    descriptions = {
        "sustainable": "Plant-forward meal with legumes, whole grains, vegetables, and minimal animal products - represents environmentally responsible eating",
        "unsustainable": "Meat-heavy meal with beef or lamb, processed foods, and resource-intensive ingredients - represents high-impact eating patterns", 
        "ultra_processed": "Meal dominated by packaged foods, fast food items, and highly processed ingredients - represents convenience-focused eating",
        "balanced": "Mixed meal following dietary guidelines with moderate amounts of animal products, vegetables, and whole grains"
    }
    return descriptions.get(meal_type, "Reference meal for comparison")

def _get_comparison_interpretation(cost_ratio: float, carbon_ratio: float, meal_type: str, user_type: str) -> str:
    """Get interpretation of meal comparison results."""
    if user_type == "individual":
        if meal_type == "sustainable":
            if cost_ratio <= 1.0:
                return "Excellent! Your meal is as sustainable as our eco-friendly reference meal."
            else:
                return f"Your meal has {cost_ratio:.1f}x more environmental impact than a sustainable meal. Try adding more plants!"
        elif meal_type == "unsustainable":
            if cost_ratio < 1.0:
                return f"Good news! Your meal is {1/cost_ratio:.1f}x better than a high-impact meal."
            else:
                return "Your meal has similar or higher impact than an unsustainable meal. Consider healthier choices."
    
    elif user_type == "researcher":
        return f"Environmental cost ratio: {cost_ratio:.2f}, Carbon footprint ratio: {carbon_ratio:.2f} relative to {meal_type} reference scenario."
    
    else:  # policy
        return f"Policy scenario comparison: {cost_ratio:.2f}x cost ratio indicates {'alignment with' if cost_ratio <= 1.0 else 'deviation from'} sustainable dietary targets."
    
    return f"Comparison to {meal_type} meal shows {cost_ratio:.2f}x environmental cost difference."

def _get_overall_assessment(meal_data: Dict[str, Any], user_type: str) -> Dict[str, str]:
    """Get overall assessment and recommendations."""
    sustainability_score = meal_data.get('sustainability', {}).get('overall_sustainability_score', 50)
    cost = meal_data.get('monetization', {}).get('total_cost', 0)
    
    if user_type == "individual":
        if sustainability_score >= 70 and cost < 0.1:
            return {
                "rating": "Excellent Choice! 🌟",
                "message": "Your meal is both environmentally friendly and nutritious. Keep up the great work!",
                "recommendation": "Share your sustainable eating choices with friends and family."
            }
        elif sustainability_score >= 50:
            return {
                "rating": "Good Choice 👍",
                "message": "Your meal has moderate environmental impact with room for improvement.",
                "recommendation": "Try replacing some animal products with plant-based alternatives or choose local, seasonal ingredients."
            }
        else:
            return {
                "rating": "Room for Improvement 🔄",
                "message": "Your meal has significant environmental impact.",
                "recommendation": "Focus on adding more vegetables, reducing meat portions, and choosing less processed foods."
            }
    
    elif user_type == "researcher":
        return {
            "rating": f"Sustainability Score: {sustainability_score:.1f}/100",
            "message": "Quantitative assessment suitable for academic analysis and publication.",
            "recommendation": "Results can be used for comparative studies and meta-analyses with appropriate citations."
        }
    
    else:  # policy
        return {
            "rating": f"Policy Alignment Score: {sustainability_score:.1f}/100",
            "message": "Assessment relative to national dietary and environmental targets.",
            "recommendation": "Results inform policy development for sustainable food system transformation."
        }

@api_view(['POST'])
@seo_metadata(
    title="Environmental Impact Calculator | EcoDish365",
    description="Calculate the comprehensive environmental impact of your meals with our advanced LCA tool. Get clear explanations and compare to reference meals.",
    keywords="environmental impact, LCA, food sustainability, carbon footprint, meal comparison, monetization"
)
def environmental_impact(request):
    """
    Comprehensive environmental impact assessment with user-friendly explanations.
    
    Supports different explanation levels for:
    - individual: Everyday consumers seeking actionable insights
    - researcher: Scientists and academics needing technical details
    - policy: Policymakers requiring evidence-based assessments
    """
    try:
        # Get request parameters
        food_data = request.data.get('foods', [])
        user_type = request.data.get('user_type', 'individual')  # individual, researcher, policy
        
        if not food_data:
            return Response({
                "error": "No food data provided. Please include 'foods' array with food_id and quantity.",
                "example": {
                    "foods": [
                        {"food_id": 2003, "quantity": 150},
                        {"food_id": 3580, "quantity": 100}
                    ],
                    "user_type": "individual"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize data loader and CNF integrator
        cnf_integrator = get_cnf_integrator()
        if not cnf_integrator.is_initialized():
            # Try to initialize with default path
            cnf_integrator.initialize('raw_cnf')
        
        data_loader = EnvDataLoader()
        
        # Create meal
        foods = [EnvFood(food_id=item['food_id'], quantity=item['quantity'], data_loader=data_loader) 
                for item in food_data]
        meal = EnvMeal(foods)
        
        # Perform comprehensive analysis
        comprehensive_analysis = _analyze_meal_comprehensive(meal, data_loader)
        
        # Format results with user-appropriate explanations
        formatted_results = format_environmental_results(comprehensive_analysis, user_type)
        
        # Create final response (reuse enriched meal_info with macronutrient distribution)
        result = {
            "data": formatted_results,
            "meal_info": comprehensive_analysis.get('meal_info', {
                "composition": meal.get_food_breakdown(),
                "total_calories": meal.calculate_total_calories(),
                "total_weight": meal.get_total_weight(),
            }),
            "metadata": {
                "user_type": user_type,
                "methodology": "ReCiPe 2016 LCA with Canadian regional factors",
                "data_source": "Canadian Nutrient File (Health Canada)",
                "currency": "CAD",
                "functional_unit": "per meal",
                "timestamp": "2024"
            },
            "seo_metadata": {
                "title": f"Environmental Impact Assessment - {user_type.title()} View | DISH Research",
                "description": f"Comprehensive environmental impact assessment tailored for {user_type}s. Get clear explanations of your meal's carbon footprint, environmental costs, and sustainability rating.",
                "keywords": f"environmental impact, {user_type}, LCA, food sustainability, carbon footprint, meal assessment"
            }
        }
        
        return Response(result)
        
    except ValueError as e:
        logger.error(f"Validation error in environmental impact calculation: {str(e)}")
        return Response({
            "error": "Invalid input data",
            "details": str(e),
            "help": "Please check that all food_id values exist in the database and quantities are positive numbers."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in environmental impact calculation: {str(e)}", exc_info=True)
        return Response({
            "error": "An unexpected error occurred during the environmental impact calculation.",
            "help": "Please try again or contact support if the problem persists."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _analyze_meal_comprehensive(meal: EnvMeal, data_loader: EnvDataLoader) -> Dict[str, Any]:
    """Perform comprehensive meal analysis including LCA, monetization, and reference comparisons."""
    try:
        # Basic meal info
        # Basic meal info
        total_calories = meal.calculate_total_calories()
        total_weight = meal.get_total_weight()
        composition_list = meal.get_food_breakdown()

        # Macronutrient distribution (% of energy) with robust nutrient name matching
        def _get_nutrient_amount_any(names):
            for n in names:
                val = meal.get_nutrient_amount(n)
                if val and val > 0:
                    return val
            return 0.0

        protein_g = _get_nutrient_amount_any([
            'PROTEIN', 'PROTEINS'
        ])
        fat_g = _get_nutrient_amount_any([
            'FAT', 'TOTAL FAT', 'FAT, TOTAL', 'TOTAL LIPID', 'TOTAL LIPID (G)', 'LIPID (TOTAL)', 'LIPIDS'
        ])
        carbs_g = _get_nutrient_amount_any([
            'CARBOHYDRATE', 'CARBOHYDRATES', 'TOTAL CARBOHYDRATE', 'CARBOHYDRATE, TOTAL',
            'AVAILABLE CARBOHYDRATE', 'CARBOHYDRATE, AVAILABLE'
        ])
        protein_kcal = protein_g * 4.0
        fat_kcal = fat_g * 9.0
        carbs_kcal = carbs_g * 4.0
        kcal_sum = protein_kcal + fat_kcal + carbs_kcal
        if kcal_sum <= 0 and total_calories > 0:
            # Fallback to total calories if macro calories unavailable
            kcal_sum = total_calories
        # Compute initial percentages
        protein_pct = (protein_kcal / kcal_sum * 100.0) if kcal_sum > 0 else 0.0
        carb_pct = (carbs_kcal / kcal_sum * 100.0) if kcal_sum > 0 else 0.0
        fat_pct = (fat_kcal / kcal_sum * 100.0) if kcal_sum > 0 else 0.0

        # If only one macro present and others zero but total_calories > kcal_sum (e.g., measured energy),
        # rescale using total_calories to avoid showing 100% for a single macro.
        if total_calories > 0 and kcal_sum > 0 and (fat_kcal == 0 or carbs_kcal == 0):
            protein_pct = (protein_kcal / total_calories * 100.0)
            carb_pct = (carbs_kcal / total_calories * 100.0)
            fat_pct = (fat_kcal / total_calories * 100.0)

        # Normalize to ensure the sum does not exceed 100 due to rounding
        total_pct = protein_pct + carb_pct + fat_pct
        if total_pct > 0:
            scale = min(1.0, 100.0 / total_pct)
            protein_pct *= scale
            carb_pct *= scale
            fat_pct *= scale

        macronutrient_distribution = {
            'protein_percent': protein_pct,
            'carbohydrate_percent': carb_pct,
            'fat_percent': fat_pct,
        }

        meal_info = {
            'total_calories': total_calories,
            'total_weight': total_weight,
            'composition': composition_list,
            'macronutrient_distribution': macronutrient_distribution,
        }
        
        # Life Cycle Assessment
        lca = LifeCycleAssessment(meal)
        lca_results = lca.perform_lcia()
        endpoint_impacts = lca.calculate_endpoint_impacts()
        single_score = lca.calculate_single_score()
        
        lca_data = {
            'midpoint_impacts': lca_results,
            'endpoint_impacts': endpoint_impacts,
            'single_score': single_score
        }
        
        # Monetization
        monetization = Monetization(lca_results, data_loader)
        total_calories = meal_info['total_calories']
        total_protein = meal.get_nutrient_amount('PROTEIN')
        
        monetization_data = {
            'total_cost': monetization.get_total_monetized_impact(),
            'cost_per_calorie': monetization.calculate_cost_per_calorie(total_calories),
            'cost_per_protein': monetization.calculate_cost_per_gram_protein(total_protein),
            'cost_breakdown_by_category': monetization.get_cost_breakdown_by_category(),
            'top_cost_drivers': monetization.get_top_cost_drivers()
        }
        
        # Reference meal comparisons
        reference_meals = ReferenceMeals(data_loader)
        reference_comparisons = {}
        
        meal_types = ['sustainable', 'unsustainable', 'ultra_processed', 'balanced']
        main_cost = monetization_data['total_cost']
        main_carbon = lca_results.get('Global warming', 0)
        
        for meal_type in meal_types:
            try:
                if meal_type == 'sustainable':
                    ref_meal = reference_meals.create_sustainable_meal('lunch')
                elif meal_type == 'unsustainable':
                    ref_meal = reference_meals.create_unsustainable_meal('lunch')
                elif meal_type == 'ultra_processed':
                    ref_meal = reference_meals.create_ultra_processed_meal('lunch')
                elif meal_type == 'balanced':
                    ref_meal = reference_meals.create_balanced_meal('lunch')
                
                # Calculate reference meal impacts
                ref_lca = LifeCycleAssessment(ref_meal)
                ref_impacts = ref_lca.perform_lcia()
                ref_monetization = Monetization(ref_impacts, data_loader)
                ref_cost = ref_monetization.get_total_monetized_impact()
                ref_carbon = ref_impacts.get('Global warming', 0)
                
                reference_comparisons[meal_type] = {
                    'cost_ratio': main_cost / ref_cost if ref_cost > 0 else float('inf'),
                    'carbon_ratio': main_carbon / ref_carbon if ref_carbon > 0 else float('inf'),
                    'reference_cost': ref_cost,
                    'reference_carbon': ref_carbon
                }
                
            except Exception as e:
                logger.warning(f"Failed to create {meal_type} reference meal: {e}")
                reference_comparisons[meal_type] = {'error': str(e)}
        
        # Sustainability scoring
        # Base overall score (primarily environment-driven from Food/Meal methods)
        base_sustainability = meal.get_sustainability_score()

        # Derive environmental component and per-category scores from meal-level LCA results
        env_component = _compute_environmental_component_scores(lca_results)

        # Nutritional quality score (0-100) from meal nutrition
        nutrition_quality = meal.get_nutritional_quality_score()
        nutritional_score = float(nutrition_quality.get('nutritional_quality_score', 0) or 0)

        # Processing level heuristic score (0-100, higher is better = less processed)
        processing_score = _estimate_processing_score(meal)

        # Compose enhanced sustainability block consumed by the frontend
        sustainability = {
            'overall_sustainability_score': float(base_sustainability.get('overall_sustainability_score', 50) or 50),
            'sustainability_rating': base_sustainability.get('sustainability_rating', 'Unknown'),
            'environmental_score': env_component['environmental_score'],
            'nutritional_score': nutritional_score,
            'processing_score': processing_score,
            'category_scores': env_component['category_scores'],
            'individual_food_scores': base_sustainability.get('individual_food_scores', [])
        }
        
        return {
            'meal_info': meal_info,
            'lca': lca_data,
            'monetization': monetization_data,
            'reference_comparisons': reference_comparisons,
            'sustainability': sustainability
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive meal analysis: {e}")
        raise

def _compute_environmental_component_scores(lca_midpoints: Dict[str, float]) -> Dict[str, Any]:
    """Compute environmental component score and category scores (0-100, higher better) from LCA midpoints.

    Mirrors the normalization approach in `Food.get_sustainability_score` for key categories,
    then aggregates with weights to an overall environmental score.
    """
    # Typical maximum values per 100 kcal used for normalization
    max_values = {
        'Global warming': 100.0,           # kg CO2 eq
        'Land use': 200.0,                # m2a crop eq
        'Water consumption': 20.0,        # m3
        'Terrestrial acidification': 0.5, # kg SO2 eq
        'Freshwater eutrophication': 0.02,# kg P eq
        'Marine eutrophication': 0.2,     # kg N eq
    }

    weights = {
        'Global warming': 0.3,
        'Land use': 0.2,
        'Water consumption': 0.2,
        'Terrestrial acidification': 0.1,
        'Freshwater eutrophication': 0.1,
        'Marine eutrophication': 0.1,
    }

    category_scores: Dict[str, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for category, max_val in max_values.items():
        impact_val = float(lca_midpoints.get(category, 0.0) or 0.0)
        # Normalize to 0-100 where lower impact => higher score
        normalized = min(100.0, (impact_val / max_val) * 100.0) if max_val > 0 else 0.0
        score = max(0.0, 100.0 - normalized)
        category_scores[category] = score
        w = weights.get(category, 0.0)
        if w > 0:
            weighted_sum += score * w
            total_weight += w

    environmental_score = (weighted_sum / total_weight) if total_weight > 0 else 50.0

    return {
        'environmental_score': environmental_score,
        'category_scores': category_scores,
    }

def _estimate_processing_score(meal: EnvMeal) -> float:
    """Estimate a processing score (0-100, higher is better = less processed) heuristically.

    Uses food group heuristics as proxy for processing intensity when NOVA/FCS is unavailable.
    """
    breakdown = meal.get_food_breakdown()
    if not breakdown:
        return 50.0

    # Assign processing quality multipliers (higher is better)
    group_multiplier = {
        # Minimally processed
        'Vegetables and Vegetable Products': 1.0,
        'Legumes and Legume Products': 0.95,
        'Fruits and fruit juices': 0.9,
        'Cereals, Grains and Pasta': 0.85,
        'Nuts and Seeds': 0.85,
        'Finfish and Shellfish Products': 0.8,
        # Moderate processing
        'Dairy and Egg Products': 0.7,
        'Poultry Products': 0.7,
        'Pork Products': 0.6,
        'Beef Products': 0.55,
        # Highly processed
        'Fast Foods': 0.3,
        'Sausages and Luncheon meats': 0.25,
        'Sweets': 0.25,
        'Snacks': 0.25,
        'Breakfast cereals': 0.4,
    }

    total_qty = sum(float(item.get('quantity', 0) or 0) for item in breakdown)
    if total_qty <= 0:
        return 50.0

    # Quantity-weighted average multiplier
    weighted = 0.0
    for item in breakdown:
        qty = float(item.get('quantity', 0) or 0)
        grp = str(item.get('group', ''))
        mult = group_multiplier.get(grp, 0.7)  # default moderate
        weighted += mult * qty

    avg_mult = weighted / total_qty
    # Convert multiplier in ~[0.25..1.0] to a 0-100 score linearly
    score = max(0.0, min(100.0, (avg_mult - 0.25) / (1.0 - 0.25) * 100.0))
    return score

@api_view(['POST'])
@seo_metadata(
    title="Compare Environmental Impact of Foods | DISH Research",
    description="Compare the environmental impact of multiple foods side-by-side with detailed analysis.",
    keywords="food comparison, environmental impact comparison, sustainability comparison"
)
def compare_foods_environmental(request):
    """
    Compare environmental impact of multiple individual foods.
    Input: List of foods with quantities
    Output: Side-by-side comparison with detailed explanations
    """
    try:
        foods_data = request.data.get('foods', [])
        user_type = request.data.get('user_type', 'individual')
        
        if not foods_data or len(foods_data) < 2:
            return Response({
                "error": "Please provide at least 2 foods for comparison",
                "example": {
                    "foods": [
                        {"food_id": 2003, "quantity": 100, "name": "Chicken Breast"},
                        {"food_id": 3580, "quantity": 100, "name": "Black Beans"}
                    ],
                    "user_type": "individual"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data_loader = EnvDataLoader()
        food_comparisons = []
        
        # Analyze each food individually
        for food_data in foods_data:
            try:
                food = EnvFood(
                    food_id=food_data['food_id'], 
                    quantity=food_data['quantity'], 
                    data_loader=data_loader
                )
                
                # Get environmental impact
                environmental_impact = food.get_environmental_impact()
                sustainability_score = food.get_sustainability_score()
                
                # Calculate key metrics per 100g for fair comparison
                quantity_100g = food_data['quantity'] / 100.0
                
                food_comparisons.append({
                    "food_info": {
                        "name": food.food_name,
                        "food_group": food.food_group,
                        "quantity": food_data['quantity'],
                        "food_id": food_data['food_id']
                    },
                    "environmental_impact_per_100g": {
                        "carbon_footprint": environmental_impact.get('Global warming', 0) / quantity_100g,
                        "water_consumption": environmental_impact.get('Water consumption', 0) / quantity_100g,
                        "land_use": environmental_impact.get('Land use', 0) / quantity_100g
                    },
                    "sustainability_score": sustainability_score.get('overall', 50),
                    "all_impacts": {k: v / quantity_100g for k, v in environmental_impact.items()}
                })
                
            except Exception as e:
                food_comparisons.append({
                    "food_id": food_data['food_id'],
                    "error": f"Analysis failed: {str(e)}"
                })
        
        # Create comparison insights
        successful_comparisons = [fc for fc in food_comparisons if 'error' not in fc]
        if len(successful_comparisons) >= 2:
            comparison_insights = _generate_food_comparison_insights(successful_comparisons, user_type)
        else:
            comparison_insights = {"error": "Need at least 2 successful food analyses"}
        
        # Get explanations
        explanations = get_user_explanations(user_type)
        
        result = {
            "food_comparisons": food_comparisons,
            "comparison_insights": comparison_insights,
            "explanations": {
                "title": "🍎 Food Environmental Impact Comparison",
                "description": explanations["lca_results"]["detailed_explanation"],
                "comparison_explanation": "All impacts are shown per 100g for fair comparison between different foods.",
                "sustainability_explanation": "Sustainability scores (0-100) consider both environmental impact and nutritional value."
            },
            "metadata": {
                "user_type": user_type,
                "comparison_basis": "per 100g",
                "total_foods": len(foods_data)
            }
        }
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error in food comparison: {str(e)}")
        return Response({
            "error": "Food comparison failed",
            "help": "Please check that all food_id values exist in the database."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@seo_metadata(
    title="Food Environmental Profile | DISH Research", 
    description="Get detailed environmental profile for a specific food item.",
    keywords="food profile, environmental impact, sustainability profile"
)
def food_environmental_profile(request, food_id):
    """
    Get detailed environmental profile for a single food item.
    Provides comprehensive analysis including all impact categories.
    """
    try:
        user_type = request.GET.get('user_type', 'individual')
        quantity = float(request.GET.get('quantity', 100))  # Default 100g
        
        data_loader = EnvDataLoader()
        food = EnvFood(food_id=food_id, quantity=quantity, data_loader=data_loader)
        
        # Get comprehensive data
        environmental_impact = food.get_environmental_impact()
        sustainability_score = food.get_sustainability_score()
        
        # Create single-food meal for LCA analysis
        meal = EnvMeal([food])
        lca = LifeCycleAssessment(meal)
        lca_results = lca.perform_lcia()
        
        # Monetization
        monetization = Monetization(lca_results, data_loader)
        
        # Format based on user type
        explanations = get_user_explanations(user_type)
        
        profile = {
            "food_info": {
                "name": food.food_name,
                "food_group": food.food_group,
                "quantity_analyzed": f"{quantity}g",
                "food_id": food_id
            },
            "environmental_profile": {
                "explanation": explanations["lca_results"],
                "key_impacts": {
                    "carbon_footprint": {
                        "total": environmental_impact.get('Global warming', 0),
                        "per_100g": environmental_impact.get('Global warming', 0) / (quantity/100),
                        "unit": "kg CO₂-eq",
                        "rating": _get_carbon_rating(environmental_impact.get('Global warming', 0) / (quantity/100))
                    },
                    "water_consumption": {
                        "total": environmental_impact.get('Water consumption', 0),
                        "per_100g": environmental_impact.get('Water consumption', 0) / (quantity/100),
                        "unit": "m³",
                        "rating": _get_water_rating(environmental_impact.get('Water consumption', 0) / (quantity/100))
                    },
                    "land_use": {
                        "total": environmental_impact.get('Land use', 0),
                        "per_100g": environmental_impact.get('Land use', 0) / (quantity/100),
                        "unit": "m²a crop-eq",
                        "rating": _get_land_rating(environmental_impact.get('Land use', 0) / (quantity/100))
                    }
                },
                "all_impact_categories": {k: v / (quantity/100) for k, v in environmental_impact.items()},
                "overall_rating": _get_overall_environmental_rating(environmental_impact, quantity)
            },
            "sustainability_assessment": {
                "explanation": "Sustainability score combines environmental impact with nutritional quality",
                "overall_score": sustainability_score.get('overall', 50),
                "rating": _get_sustainability_rating_text(sustainability_score.get('overall', 50)),
                "individual_scores": sustainability_score
            },
            "economic_impact": {
                "explanation": explanations["monetization"],
                "total_cost": monetization.get_total_monetized_impact(),
                "cost_per_100g": monetization.get_total_monetized_impact() / (quantity/100),
                "cost_per_calorie": monetization.calculate_cost_per_calorie(meal.calculate_total_calories()),
                "currency": "CAD"
            },
            "nutritional_context": {
                "calories_per_100g": meal.calculate_total_calories() / (quantity/100),
                "energy_density": meal.get_energy_density(),
                "food_group_typical_impact": _get_food_group_context(food.food_group)
            },
            "recommendations": _get_food_recommendations(food, sustainability_score.get('overall', 50), user_type)
        }
        
        return Response(profile)
        
    except ValueError as e:
        return Response({
            "error": "Food not found",
            "food_id": food_id,
            "help": "Please check that the food_id exists in our database."
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error getting food profile for {food_id}: {str(e)}")
        return Response({
            "error": "Could not generate food profile",
            "food_id": food_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _generate_food_comparison_insights(comparisons: List[Dict], user_type: str) -> Dict[str, Any]:
    """Generate insights from food comparison analysis."""
    if not comparisons:
        return {}
    
    # Find best and worst performers
    best_carbon = min(comparisons, key=lambda x: x['environmental_impact_per_100g']['carbon_footprint'])
    worst_carbon = max(comparisons, key=lambda x: x['environmental_impact_per_100g']['carbon_footprint'])
    best_sustainability = max(comparisons, key=lambda x: x['sustainability_score'])
    worst_sustainability = min(comparisons, key=lambda x: x['sustainability_score'])
    
    insights = {
        "winners": {
            "lowest_carbon_footprint": {
                "food": best_carbon['food_info']['name'],
                "value": f"{best_carbon['environmental_impact_per_100g']['carbon_footprint']:.2f} kg CO₂-eq per 100g"
            },
            "most_sustainable": {
                "food": best_sustainability['food_info']['name'],
                "score": f"{best_sustainability['sustainability_score']:.0f}/100"
            }
        },
        "environmental_differences": {
            "carbon_footprint_range": {
                "lowest": best_carbon['environmental_impact_per_100g']['carbon_footprint'],
                "highest": worst_carbon['environmental_impact_per_100g']['carbon_footprint'],
                "difference": f"{worst_carbon['environmental_impact_per_100g']['carbon_footprint'] / best_carbon['environmental_impact_per_100g']['carbon_footprint']:.1f}x difference"
            }
        },
        "key_takeaways": []
    }
    
    # Generate user-appropriate takeaways
    if user_type == "individual":
        insights["key_takeaways"] = [
            f"🌱 {best_carbon['food_info']['name']} has the lowest carbon footprint",
            f"⭐ {best_sustainability['food_info']['name']} is the most sustainable overall",
            f"🔄 Swapping {worst_carbon['food_info']['name']} for {best_carbon['food_info']['name']} could reduce your environmental impact"
        ]
    elif user_type == "researcher":
        insights["key_takeaways"] = [
            f"Carbon footprint varies by {worst_carbon['environmental_impact_per_100g']['carbon_footprint'] / best_carbon['environmental_impact_per_100g']['carbon_footprint']:.1f}x across compared foods",
            f"Sustainability scores range from {worst_sustainability['sustainability_score']:.0f} to {best_sustainability['sustainability_score']:.0f}",
            "Results suitable for dietary intervention studies and environmental impact assessments"
        ]
    else:  # policy
        insights["key_takeaways"] = [
            f"Policy interventions could target high-impact foods like {worst_carbon['food_info']['name']}",
            f"Promoting {best_carbon['food_info']['name']} could reduce population-level environmental impact",
            "Results inform evidence-based dietary guidelines and environmental policies"
        ]
    
    return insights

def _get_carbon_rating(carbon_per_100g: float) -> Dict[str, str]:
    """Get carbon footprint rating."""
    if carbon_per_100g <= 0.5:
        return {"rating": "Excellent", "color": "green", "description": "Very low carbon footprint"}
    elif carbon_per_100g <= 2.0:
        return {"rating": "Good", "color": "lightgreen", "description": "Low carbon footprint"}
    elif carbon_per_100g <= 5.0:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate carbon footprint"}
    elif carbon_per_100g <= 10.0:
        return {"rating": "High", "color": "orange", "description": "High carbon footprint"}
    else:
        return {"rating": "Very High", "color": "red", "description": "Very high carbon footprint"}

def _get_water_rating(water_per_100g: float) -> Dict[str, str]:
    """Get water consumption rating."""
    if water_per_100g <= 0.1:
        return {"rating": "Excellent", "color": "green", "description": "Very low water use"}
    elif water_per_100g <= 0.5:
        return {"rating": "Good", "color": "lightgreen", "description": "Low water use"}
    elif water_per_100g <= 2.0:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate water use"}
    elif water_per_100g <= 5.0:
        return {"rating": "High", "color": "orange", "description": "High water use"}
    else:
        return {"rating": "Very High", "color": "red", "description": "Very high water use"}

def _get_land_rating(land_per_100g: float) -> Dict[str, str]:
    """Get land use rating."""
    if land_per_100g <= 1.0:
        return {"rating": "Excellent", "color": "green", "description": "Very low land use"}
    elif land_per_100g <= 5.0:
        return {"rating": "Good", "color": "lightgreen", "description": "Low land use"}
    elif land_per_100g <= 20.0:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate land use"}
    elif land_per_100g <= 50.0:
        return {"rating": "High", "color": "orange", "description": "High land use"}
    else:
        return {"rating": "Very High", "color": "red", "description": "Very high land use"}

def _get_overall_environmental_rating(environmental_impact: Dict, quantity: float) -> Dict[str, str]:
    """Get overall environmental rating."""
    # Normalize impacts per 100g
    carbon = environmental_impact.get('Global warming', 0) / (quantity/100)
    water = environmental_impact.get('Water consumption', 0) / (quantity/100)
    land = environmental_impact.get('Land use', 0) / (quantity/100)
    
    # Simple scoring based on thresholds
    score = 0
    if carbon <= 2.0: score += 1
    if water <= 0.5: score += 1
    if land <= 5.0: score += 1
    
    if score == 3:
        return {"rating": "Excellent", "color": "green", "description": "Low environmental impact across all categories"}
    elif score == 2:
        return {"rating": "Good", "color": "lightgreen", "description": "Good environmental performance"}
    elif score == 1:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate environmental impact"}
    else:
        return {"rating": "High Impact", "color": "orange", "description": "High environmental impact - consider alternatives"}

def _get_sustainability_rating_text(score: float) -> str:
    """Convert sustainability score to text rating."""
    if score >= 80:
        return "Excellent - Highly sustainable choice"
    elif score >= 70:
        return "Very Good - Sustainable with minor improvements possible"
    elif score >= 60:
        return "Good - Reasonably sustainable"
    elif score >= 50:
        return "Fair - Moderate sustainability concerns"
    elif score >= 40:
        return "Poor - Significant sustainability issues"
    else:
        return "Very Poor - Major sustainability concerns"

def _get_food_group_context(food_group: str) -> str:
    """Get context about typical environmental impact for food group."""
    context = {
        "Vegetables and Vegetable Products": "Generally low environmental impact with high nutritional value",
        "Fruits and fruit juices": "Low to moderate impact, higher for out-of-season or imported fruits",
        "Beef Products": "Highest environmental impact due to methane emissions and land use",
        "Pork Products": "High impact but lower than beef, mainly from feed production",
        "Poultry Products": "Moderate impact, more efficient than red meat",
        "Dairy and Egg Products": "Moderate to high impact depending on production system",
        "Legumes and Legume Products": "Low impact and nitrogen-fixing benefits for soil",
        "Nuts and Seeds": "Moderate impact, high water use for some varieties",
        "Cereals, Grains and Pasta": "Low to moderate impact, varies by processing",
        "Fish and Shellfish Products": "Variable impact depending on fishing/farming methods"
    }
    return context.get(food_group, "Impact varies depending on production and processing methods")

def _get_food_recommendations(food, sustainability_score: float, user_type: str) -> List[str]:
    """Generate food-specific recommendations."""
    recommendations = []
    
    if user_type == "individual":
        if sustainability_score >= 70:
            recommendations.extend([
                "✅ Great choice! This food has good environmental performance",
                "💡 Share this sustainable choice with friends and family"
            ])
        elif sustainability_score >= 50:
            recommendations.extend([
                "👍 Decent choice with room for improvement",
                "🌱 Look for organic or local versions when possible"
            ])
        else:
            recommendations.extend([
                "🔄 Consider more sustainable alternatives",
                "📚 Learn about the environmental impact of your food choices"
            ])
        
        # Food group specific recommendations
        if food.food_group in ["Beef Products", "Lamb, Veal and Game"]:
            recommendations.append("🥩 Try reducing portion sizes or choosing grass-fed options")
        elif food.food_group in ["Vegetables and Vegetable Products", "Legumes and Legume Products"]:
            recommendations.append("🌟 Excellent choice! These foods are environmentally friendly")
    
    return recommendations