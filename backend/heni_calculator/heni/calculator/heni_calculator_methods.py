"""
Additional methods for HENICalculator
Separated to keep main calculator clean
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def extract_risk_factors_from_ingredient(calculator, ingredient) -> Dict[str, float]:
    """Extract HENI risk factors from ingredient using CNF data and categorization"""
    risk_factors = {}
    
    # Get nutrient data from CNF
    nutrient_data = calculator.cnf_integrator.get_nutrient_data(ingredient.food_id)
    
    # Map CNF nutrients to HENI risk factors
    nutrient_mapping = {
        'FATTY ACIDS, POLYUNSATURATED, 22:6 N-3, DOCOSAHEXAENOIC (DHA)': 'omega_3',
        'FATTY ACIDS, POLYUNSATURATED, 20:5 N-3, EICOSAPENTAENOIC (EPA)': 'omega_3', 
        'CALCIUM': 'calcium',
        'FIBRE, TOTAL DIETARY': 'fiber',
        'FATTY ACIDS, POLYUNSATURATED, TOTAL': 'polyunsaturated_fatty_acids',
        'FATTY ACIDS, TRANS, TOTAL': 'trans_fat',
        'SODIUM': 'sodium'
    }
    
    # Extract nutrient-based risk factors
    omega_3_total = 0.0
    for nutrient_name, nutrient_value in nutrient_data.items():
        if nutrient_name in nutrient_mapping:
            heni_factor = nutrient_mapping[nutrient_name]
            if heni_factor == 'omega_3':
                omega_3_total += nutrient_value
            else:
                # Convert mg to g for sodium and calcium if needed
                if nutrient_name in ['CALCIUM', 'SODIUM']:
                    risk_factors[heni_factor] = nutrient_value / 1000  # mg to g
                else:
                    risk_factors[heni_factor] = nutrient_value
    
    if omega_3_total > 0:
        risk_factors['omega_3'] = omega_3_total
    
    # Get food group classifications
    food_group = calculator.cnf_integrator.get_food_group(ingredient.food_id)
    food_description = calculator.cnf_integrator.get_food_description(ingredient.food_id).lower()
    
    # Map food groups to HENI risk factors (assuming 100g serving if in that group)
    food_group_mapping = {
        "Nuts and Seeds": "nuts_seeds",
        "Cereals, Grains and Pasta": "whole_grains", 
        "Fruits and fruit juices": "fruits",
        "Vegetables and Vegetable Products": "vegetables",
        "Milk Products": "milk",
        "Beverages": "sugar_sweetened_beverages",
        "Beef Products": "red_meat",
        "Pork Products": "red_meat",
        "Poultry Products": "red_meat"  # Poultry often grouped with red meat in studies
    }
    
    # Check for food group matches
    for group_name, heni_factor in food_group_mapping.items():
        if group_name in food_group:
            # Refined logic for specific cases
            if heni_factor == "whole_grains":
                # Only count as whole grains if description contains whole grain indicators
                if any(term in food_description for term in ['whole', 'brown', 'bran', 'wheat germ']):
                    risk_factors[heni_factor] = 100.0  # Assume full serving is whole grain
            elif heni_factor == "sugar_sweetened_beverages":
                # Only count if has significant sugar content
                sugar_content = nutrient_data.get('SUGARS, TOTAL', 0)
                if sugar_content > 5:  # >5g sugar per 100g
                    risk_factors[heni_factor] = 100.0
            elif heni_factor == "red_meat":
                # Check if meat is processed
                if any(term in food_description for term in ['processed', 'sausage', 'ham', 'bacon', 'deli', 'cured']):
                    risk_factors["processed_meat"] = 100.0
                else:
                    risk_factors["red_meat"] = 100.0
            else:
                risk_factors[heni_factor] = 100.0  # Full serving weight
    
    # Use LLM categorizer for complex cases if available
    if calculator.categorizer:
        try:
            llm_categories = calculator.categorizer.categorize_food(ingredient.food_id)
            for category, confidence in llm_categories.items():
                if category in calculator.heni_factor_keys and confidence > 0.1:  # Only high-confidence categorizations
                    risk_factors[category] = confidence * 100.0  # Scale by confidence
        except Exception as e:
            logger.warning(f"LLM categorization failed for food {ingredient.food_id}: {e}")
    
    return risk_factors

def calculate_meal_heni(calculator, ingredients: List) -> Dict:
    """Calculate HENI for a complete meal with detailed breakdown"""
    heni_result = calculator.calculate_heni(ingredients)
    
    # Format comprehensive result for API response
    return {
        "heni_scores": {
            "total_heni_score": round(heni_result.total_heni_score, 2),
            "heni_per_100_kcal": round(heni_result.heni_per_100_kcal, 2),
            "heni_per_100_grams": round(heni_result.heni_per_100_grams, 2),
            "heni_per_serving": round(heni_result.heni_per_serving, 2)
        },
        "health_impact": {
            "health_impact_minutes": round(heni_result.health_impact_minutes, 1),
            "description": heni_result.health_impact_description
        },
        "component_breakdown": {
            "food_group_contributions": {k: round(v, 2) for k, v in heni_result.food_group_contributions.items()},
            "nutrient_contributions": {k: round(v, 2) for k, v in heni_result.nutrient_contributions.items()}
        },
        "disease_burden_analysis": {
            "disease_breakdown": {k: round(v, 2) for k, v in heni_result.disease_burden_breakdown.items()}
        },
        "risk_factor_analysis": {
            "risk_factors": {k: round(v, 3) for k, v in heni_result.risk_factor_amounts.items()},
            "warnings": heni_result.effective_range_warnings
        },
        "meal_composition": {
            "total_energy_kcal": round(heni_result.total_energy_kcal, 1),
            "total_weight_grams": round(heni_result.total_weight_grams, 1),
            "ingredient_count": len(ingredients),
            "ingredient_details": heni_result.ingredient_details
        }
    }