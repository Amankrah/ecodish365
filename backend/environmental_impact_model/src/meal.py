from typing import List, Dict, Any
import logging
from .food import Food

class Meal:
    def __init__(self, foods: List[Food]):
        self.logger = logging.getLogger(__name__)
        if not foods:
            self.logger.error("Attempted to create a meal with no foods")
            raise ValueError("A meal must contain at least one food item")
        self.foods = foods
        self.data_loader = foods[0].data_loader if foods else None

    def calculate_total_calories(self) -> float:
        """
        Calculate and return the total calories of the meal.
        
        :return: Total calories in the meal
        """
        try:
            energy_nutrient_name = 'ENERGY (KILOCALORIES)'
            return sum(food.get_nutrient_amount(energy_nutrient_name) for food in self.foods)
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

    def __str__(self) -> str:
        food_names = ", ".join(food.food_name for food in self.foods)
        return f"Meal with {len(self.foods)} food items: {food_names}"

    def __repr__(self) -> str:
        return self.__str__()