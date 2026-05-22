"""
Utility functions for the environmental impact model.
Enhanced with additional helper functions for calculations and data processing.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# Global constants
# Canadian household + retail + food-service food waste rate: ~31.9% of
# purchased food never eaten (Statistics Canada / Second Harvest 2023).
# Global FAO 2011 average is closer to 30%; per-country numbers vary widely
# (UK: 22%, US: 32%, India: 18%). Use `get_food_waste_factor(country)` for
# country-aware code paths; the bare constant preserves prior behaviour.
FOOD_WASTE_FACTOR = 0.319
MACRONUTRIENT_CALORIES = {
    'protein': 4.0,  # kcal/g
    'carbohydrate': 4.0,  # kcal/g
    'fat': 9.0,  # kcal/g
    'alcohol': 7.0  # kcal/g
}

# Per-country food-waste factors. None falls back to the Canadian default. Add
# entries as authoritative data lands (e.g. UNEP Food Waste Index 2024).
_FOOD_WASTE_BY_COUNTRY: Dict[str, float] = {
    "CAN": 0.319,  # StatCan 2023 / Second Harvest
}
_FAO_GLOBAL_MEAN_WASTE = 0.30  # FAO 2011 global post-production-loss mean


def get_food_waste_factor(country: Optional[str] = None) -> float:
    """Return the food-waste factor for an ISO-3 country, or the Canadian
    default when country is None. Unknown countries fall back to the FAO 2011
    global mean with an informational log message."""
    if country is None:
        return FOOD_WASTE_FACTOR
    if country in _FOOD_WASTE_BY_COUNTRY:
        return _FOOD_WASTE_BY_COUNTRY[country]
    logger.info(
        "No per-country food-waste factor for %s; using FAO 2011 global mean (%.3f).",
        country, _FAO_GLOBAL_MEAN_WASTE,
    )
    return _FAO_GLOBAL_MEAN_WASTE


def calculate_waste(meal_weight: float, country: Optional[str] = None) -> float:
    """Calculate food waste based on country-specific (default: Canadian) statistics.

    :param meal_weight: Weight of meal in grams
    :param country:     ISO-3 code; None = Canadian default
    :return: Weight of waste in grams
    """
    return meal_weight * get_food_waste_factor(country)

def calculate_total_quantity_with_waste(base_quantity: float, country: Optional[str] = None) -> float:
    """Calculate total food quantity needed including waste.

    :param base_quantity: Base food quantity in grams
    :param country:       ISO-3 code; None = Canadian default
    :return: Total quantity including waste in grams
    """
    factor = get_food_waste_factor(country)
    return base_quantity / (1 - factor)

def estimate_calories_from_macronutrients(protein: float, carbs: float, 
                                        fat: float, alcohol: float = 0) -> float:
    """
    Estimate total calories from macronutrient content.
    
    :param protein: Protein content in grams
    :param carbs: Carbohydrate content in grams  
    :param fat: Fat content in grams
    :param alcohol: Alcohol content in grams (optional)
    :return: Estimated calories
    """
    try:
        calories = (
            protein * MACRONUTRIENT_CALORIES['protein'] +
            carbs * MACRONUTRIENT_CALORIES['carbohydrate'] +
            fat * MACRONUTRIENT_CALORIES['fat'] +
            alcohol * MACRONUTRIENT_CALORIES['alcohol']
        )
        return max(0, calories)
    except (TypeError, ValueError) as e:
        logger.warning(f"Error calculating calories from macronutrients: {e}")
        return 0.0

def normalize_impact_per_functional_unit(impact_value: float, functional_unit: str,
                                       current_amount: float, target_amount: float = 100) -> float:
    """
    Normalize environmental impact per functional unit.
    
    :param impact_value: Impact value to normalize
    :param functional_unit: Type of functional unit ('kcal', 'protein', 'weight')
    :param current_amount: Current amount of the functional unit
    :param target_amount: Target amount for normalization (default 100)
    :return: Normalized impact value
    """
    try:
        if current_amount <= 0:
            return 0.0
        return impact_value * (target_amount / current_amount)
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.warning(f"Error normalizing impact per {functional_unit}: {e}")
        return 0.0

def calculate_nutrient_density_score(nutrients: Dict[str, float], 
                                   calories: float) -> Dict[str, float]:
    """
    Calculate nutrient density scores for key nutrients per 100 kcal.
    
    :param nutrients: Dictionary of nutrient amounts
    :param calories: Total calories
    :return: Dictionary of nutrient density scores
    """
    if calories <= 0:
        return {}
    
    # Key nutrients and their reference daily values (RDV)
    nutrient_rdvs = {
        'PROTEIN': 50,  # g
        'FIBRE': 25,   # g
        'VITAMIN A': 900,  # mcg
        'VITAMIN C': 90,   # mg
        'CALCIUM': 1000,   # mg
        'IRON': 18,        # mg
        'POTASSIUM': 4700, # mg
        'FOLATE': 400,     # mcg
    }
    
    factor = 100 / calories  # Normalize to per 100 kcal
    density_scores = {}
    
    for nutrient, rdv in nutrient_rdvs.items():
        nutrient_amount = nutrients.get(nutrient, 0) * factor
        if rdv > 0:
            # Calculate percentage of RDV per 100 kcal
            density_scores[nutrient] = min(100, (nutrient_amount / rdv) * 100)
        
    return density_scores

def categorize_sustainability_score(score: float) -> Dict[str, str]:
    """
    Categorize sustainability score into rating and description.
    
    :param score: Sustainability score (0-100)
    :return: Dictionary with rating and description
    """
    if score >= 90:
        return {'rating': 'Exceptional', 'description': 'Excellent sustainability profile'}
    elif score >= 80:
        return {'rating': 'Excellent', 'description': 'Very good sustainability profile'}
    elif score >= 70:
        return {'rating': 'Good', 'description': 'Good sustainability profile with room for improvement'}
    elif score >= 60:
        return {'rating': 'Fair', 'description': 'Moderate sustainability concerns'}
    elif score >= 40:
        return {'rating': 'Poor', 'description': 'Significant sustainability issues'}
    elif score >= 20:
        return {'rating': 'Very Poor', 'description': 'Major sustainability concerns'}
    else:
        return {'rating': 'Critical', 'description': 'Severe sustainability issues'}

def calculate_carbon_footprint_rating(co2_per_100kcal: float) -> Dict[str, str]:
    """
    Rate carbon footprint based on CO2 emissions per 100 kcal.
    
    :param co2_per_100kcal: CO2 emissions in kg per 100 kcal
    :return: Dictionary with rating and description
    """
    if co2_per_100kcal <= 0.5:
        return {'rating': 'Excellent', 'color': 'green'}
    elif co2_per_100kcal <= 1.0:
        return {'rating': 'Good', 'color': 'lightgreen'}
    elif co2_per_100kcal <= 2.0:
        return {'rating': 'Fair', 'color': 'yellow'}
    elif co2_per_100kcal <= 4.0:
        return {'rating': 'Poor', 'color': 'orange'}
    else:
        return {'rating': 'Very Poor', 'color': 'red'}

def format_impact_value(value: float, unit: str, precision: int = 3) -> str:
    """
    Format impact value for display with appropriate precision.
    
    :param value: Impact value to format
    :param unit: Unit of measurement
    :param precision: Number of decimal places
    :return: Formatted string
    """
    try:
        if value == 0:
            return f"0 {unit}"
        elif abs(value) >= 1000:
            return f"{value:,.{precision-3}f} {unit}"
        elif abs(value) >= 1:
            return f"{value:.{precision}f} {unit}"
        elif abs(value) >= 0.001:
            return f"{value:.{precision+2}f} {unit}"
        else:
            # Scientific notation for very small values
            return f"{value:.2e} {unit}"
    except (TypeError, ValueError):
        return f"-- {unit}"

def convert_currency(value: float, from_currency: str, to_currency: str, 
                    exchange_rate: Optional[float] = None) -> Optional[float]:
    """
    Convert currency values with exchange rate.
    
    :param value: Value to convert
    :param from_currency: Source currency code
    :param to_currency: Target currency code  
    :param exchange_rate: Exchange rate (optional, defaults to 1.0 if same currency)
    :return: Converted value or None if conversion fails
    """
    try:
        if from_currency == to_currency:
            return value
        
        if exchange_rate is None:
            logger.warning(f"No exchange rate provided for {from_currency} to {to_currency}")
            return None
            
        return value * exchange_rate
    except (TypeError, ValueError) as e:
        logger.error(f"Error converting currency: {e}")
        return None

def validate_meal_composition(foods: List[Any]) -> Dict[str, Any]:
    """
    Validate meal composition and provide recommendations.
    
    :param foods: List of Food objects
    :return: Dictionary with validation results and recommendations
    """
    if not foods:
        return {'valid': False, 'issues': ['Meal contains no foods']}
    
    issues = []
    recommendations = []
    
    # Check food group diversity
    food_groups = [food.food_group for food in foods if hasattr(food, 'food_group')]
    unique_groups = len(set(food_groups))
    
    if unique_groups < 2:
        issues.append('Low food group diversity')
        recommendations.append('Include foods from multiple food groups')
    
    # Check portion sizes
    total_weight = sum(food.quantity for food in foods if hasattr(food, 'quantity'))
    if total_weight < 100:
        issues.append('Very small meal size')
        recommendations.append('Consider increasing portion sizes')
    elif total_weight > 1000:
        issues.append('Very large meal size')  
        recommendations.append('Consider reducing portion sizes')
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'recommendations': recommendations,
        'food_group_diversity': unique_groups,
        'total_weight': total_weight
    }

def get_seasonal_adjustment_factor(month: int, food_group: str) -> float:
    """
    Get seasonal adjustment factor for environmental impact.
    
    :param month: Month number (1-12)
    :param food_group: Food group name
    :return: Seasonal adjustment factor
    """
    # Canadian seasonal factors
    seasonal_factors = {
        'Fruits and fruit juices': {
            'summer': 0.8,    # June-August (6-8)
            'fall': 0.9,      # September-November (9-11)
            'winter': 1.3,    # December-February (12,1,2)
            'spring': 1.1     # March-May (3-5)
        },
        'Vegetables and Vegetable Products': {
            'summer': 0.7,
            'fall': 0.8, 
            'winter': 1.4,
            'spring': 1.0
        }
    }
    
    # Determine season
    if month in [12, 1, 2]:
        season = 'winter'
    elif month in [3, 4, 5]:
        season = 'spring'
    elif month in [6, 7, 8]:
        season = 'summer'
    else:  # 9, 10, 11
        season = 'fall'
    
    return seasonal_factors.get(food_group, {}).get(season, 1.0)