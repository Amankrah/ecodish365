from typing import List, Dict, Any, Optional
import logging
from .food import Food
from .cnf_integrator import get_cnf_integrator

class Meal:
    """
    Enhanced Meal class that integrates with the CNF system for comprehensive 
    nutritional and environmental impact analysis.
    """
    
    def __init__(self, foods: List[Food]):
        self.logger = logging.getLogger(__name__)
        if not foods:
            self.logger.error("Attempted to create a meal with no foods")
            raise ValueError("A meal must contain at least one food item")
        self.foods = foods
        self.data_loader = foods[0].data_loader if foods else None
        self.cnf_integrator = get_cnf_integrator()

    def calculate_total_calories(self) -> float:
        """
        Calculate and return the total calories of the meal.
        
        :return: Total calories in the meal
        """
        try:
            # Try multiple common energy nutrient names in CNF
            energy_names = ['ENERGY (KILOCALORIES)', 'ENERGY', 'KILOCALORIES', 'KCAL']
            total_calories = 0
            
            for food in self.foods:
                food_calories = 0
                for energy_name in energy_names:
                    calories = food.get_nutrient_amount(energy_name)
                    if calories > 0:
                        food_calories = calories
                        break
                
                # Fallback: estimate from macronutrients if no direct energy value
                if food_calories == 0:
                    protein = food.get_nutrient_amount('PROTEIN') or 0
                    fat = food.get_nutrient_amount('FAT') or 0
                    carbs = food.get_nutrient_amount('CARBOHYDRATE') or 0
                    food_calories = (protein * 4) + (fat * 9) + (carbs * 4)
                
                total_calories += food_calories
            
            return total_calories
        except Exception as e:
            self.logger.error(f"Error calculating total calories: {str(e)}")
            raise

    def calculate_nutrient_profile(self) -> Dict[str, float]:
        """
        Calculate and return the overall nutrient profile of the meal.
        
        :return: Dictionary with nutrient names as keys and total amounts as values
        """
        try:
            nutrient_profile = {}
            for food in self.foods:
                for nutrient_name, amount in food.nutrients.items():
                    nutrient_profile[nutrient_name] = nutrient_profile.get(nutrient_name, 0) + food.get_nutrient_amount(nutrient_name)
            return nutrient_profile
        except Exception as e:
            self.logger.error(f"Error calculating nutrient profile: {str(e)}")
            raise

    def get_nutrient_amount(self, nutrient_name: str) -> float:
        """
        Get the total amount of a specific nutrient in the meal.
        
        :param nutrient_name: Name of the nutrient
        :return: Total amount of the nutrient in the meal
        """
        return sum(food.get_nutrient_amount(nutrient_name) for food in self.foods)

    def calculate_environmental_impact(self) -> Dict[str, float]:
        """
        Calculate and return the total environmental impact of the meal.
        
        :return: Dictionary with impact categories as keys and total impact values as values
        """
        try:
            total_impact = {}
            for food in self.foods:
                food_impact = food.get_environmental_impact()
                for category, impact in food_impact.items():
                    if category in total_impact:
                        total_impact[category] += impact
                    else:
                        total_impact[category] = impact
            return total_impact
        except Exception as e:
            self.logger.error(f"Error calculating environmental impact: {str(e)}")
            raise

    def get_total_weight(self) -> float:
        """
        Calculate the total weight of the meal including waste.
        
        :return: Total weight of the meal in grams
        """
        return sum(food.get_total_quantity() for food in self.foods)

    def get_total_weight_without_waste(self) -> float:
        """
        Calculate the total weight of the meal excluding waste (raw input quantities).

        :return: Total input weight of the meal in grams
        """
        return sum(food.quantity for food in self.foods)

    def get_food_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get a breakdown of foods in the meal.
        
        :return: List of dictionaries containing food details
        """
        return [{"id": food.food_id, "name": food.food_name, "quantity": food.quantity, "group": food.food_group} for food in self.foods]

    def get_energy_density(self) -> float:
        """
        Calculate the energy density of the meal (calories per gram).
        
        :return: Energy density in calories per gram
        """
        total_weight = sum(food.quantity for food in self.foods)
        if total_weight == 0:
            return 0
        return self.calculate_total_calories() / total_weight
    
    def get_sustainability_score(self) -> Dict[str, float]:
        """
        Calculate overall sustainability score for the meal.
        """
        try:
            sustainability_scores = []
            for food in self.foods:
                food_score = food.get_sustainability_score()
                if 'overall' in food_score:
                    # Weight by food quantity
                    weight = food.quantity / sum(f.quantity for f in self.foods)
                    sustainability_scores.append(food_score['overall'] * weight)
            
            overall_score = sum(sustainability_scores) if sustainability_scores else 50
            
            return {
                'overall_sustainability_score': overall_score,
                'sustainability_rating': self._get_sustainability_rating(overall_score),
                'individual_food_scores': [food.get_sustainability_score() for food in self.foods]
            }
        except Exception as e:
            self.logger.error(f"Error calculating sustainability score: {str(e)}")
            return {'overall_sustainability_score': 50, 'sustainability_rating': 'Unknown'}
    
    def _get_sustainability_rating(self, score: float) -> str:
        """Convert numerical sustainability score to rating.

        Bands harmonised with `LifeCycleAssessment._sustainability_rating`
        so the same score produces the same label regardless of which entry
        point (meal vs LCA) computed it.
        """
        if score >= 80: return "Excellent"
        if score >= 65: return "Good"
        if score >= 50: return "Moderate"
        if score >= 35: return "Poor"
        return "Very Poor"
    
    def get_nutritional_quality_score(self) -> Dict[str, float]:
        """
        Calculate nutritional quality score based on key nutrients.
        """
        try:
            # Get key nutrients per 100 kcal
            calories = self.calculate_total_calories()
            if calories == 0:
                return {'nutritional_quality_score': 0, 'rating': 'No Data'}
            
            factor = 100 / calories  # Normalize to per 100 kcal
            
            # Key nutrients with their recommended daily values (RDV)
            key_nutrients = {
                'PROTEIN': {'value': self.get_nutrient_amount('PROTEIN') * factor, 'rdv': 50, 'weight': 0.2},
                'FIBRE': {'value': self.get_nutrient_amount('FIBRE') * factor, 'rdv': 25, 'weight': 0.15},
                'VITAMIN A': {'value': self.get_nutrient_amount('VITAMIN A') * factor, 'rdv': 900, 'weight': 0.1},
                'VITAMIN C': {'value': self.get_nutrient_amount('VITAMIN C') * factor, 'rdv': 90, 'weight': 0.1},
                'CALCIUM': {'value': self.get_nutrient_amount('CALCIUM') * factor, 'rdv': 1000, 'weight': 0.1},
                'IRON': {'value': self.get_nutrient_amount('IRON') * factor, 'rdv': 18, 'weight': 0.1},
                'POTASSIUM': {'value': self.get_nutrient_amount('POTASSIUM') * factor, 'rdv': 4700, 'weight': 0.1},
            }
            
            # Calculate weighted nutrient density score
            nutrient_score = 0
            total_weight = 0
            
            for nutrient, info in key_nutrients.items():
                if info['value'] > 0 and info['rdv'] > 0:
                    # Nutrient density score (capped at 100 for individual nutrients)
                    density = min(100, (info['value'] / info['rdv']) * 100)
                    nutrient_score += density * info['weight']
                    total_weight += info['weight']
            
            # Penalties for negative nutrients
            sodium = self.get_nutrient_amount('SODIUM') * factor
            sugar = self.get_nutrient_amount('SUGARS') * factor
            saturated_fat = self.get_nutrient_amount('SATURATED FAT') * factor
            
            # Apply penalties (reduce score for high negative nutrients)
            penalty = 0
            if sodium > 600:  # mg per 100 kcal
                penalty += min(20, (sodium - 600) / 100 * 5)
            if sugar > 10:  # g per 100 kcal  
                penalty += min(15, (sugar - 10) * 2)
            if saturated_fat > 3:  # g per 100 kcal
                penalty += min(15, (saturated_fat - 3) * 3)
            
            final_score = max(0, (nutrient_score / total_weight if total_weight > 0 else 0) - penalty)
            
            return {
                'nutritional_quality_score': final_score,
                'rating': self._get_nutritional_rating(final_score),
                'nutrient_breakdown': key_nutrients,
                'penalties_applied': penalty
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating nutritional quality: {str(e)}")
            return {'nutritional_quality_score': 0, 'rating': 'Error'}
    
    def _get_nutritional_rating(self, score: float) -> str:
        """Convert numerical nutrition score to rating."""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        elif score >= 35:
            return "Poor"
        else:
            return "Very Poor"
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive meal analysis including nutrition, sustainability, and environmental impact.
        """
        return {
            'meal_composition': self.get_food_breakdown(),
            'nutritional_analysis': {
                'total_calories': self.calculate_total_calories(),
                'nutrient_profile': self.calculate_nutrient_profile(),
                'nutritional_quality': self.get_nutritional_quality_score(),
                'energy_density': self.get_energy_density()
            },
            'environmental_analysis': {
                'environmental_impacts': self.calculate_environmental_impact(),
                'sustainability_score': self.get_sustainability_score(),
                'total_weight_with_waste': self.get_total_weight()
            }
        }

    def __str__(self) -> str:
        food_names = ", ".join(food.food_name for food in self.foods)
        return f"Meal with {len(self.foods)} food items: {food_names}"

    def __repr__(self) -> str:
        return self.__str__()