import random
import logging
from typing import List, Dict, Optional
from src.food import Food
from src.meal import Meal
from .cnf_integrator import get_cnf_integrator


class ReferenceMeals:
    """
    Enhanced ReferenceMeals class using CNF integrator for improved meal generation
    with better sustainability classifications and nutritional balance.
    """
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.cnf_integrator = get_cnf_integrator()
        self.meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        self.food_groups = self._load_food_groups()
        self.logger = logging.getLogger(__name__)

    def _load_food_groups(self):
        """Load available food groups from the data loader."""
        try:
            if hasattr(self.data_loader, 'food_group') and not self.data_loader.food_group.empty:
                return self.data_loader.food_group['FoodGroupName'].unique().tolist()
            else:
                # Fallback to CNF integrator
                food_group_df = self.cnf_integrator.get_dataframe('food_group')
                if not food_group_df.empty and 'FoodGroupName' in food_group_df.columns:
                    return food_group_df['FoodGroupName'].unique().tolist()
                else:
                    # Default food groups if data unavailable
                    return [
                        'Vegetables and Vegetable Products', 'Fruits and fruit juices',
                        'Legumes and Legume Products', 'Nuts and Seeds',
                        'Cereals, Grains and Pasta', 'Dairy and Egg Products',
                        'Poultry Products', 'Beef Products', 'Pork Products',
                        'Finfish and Shellfish Products'
                    ]
        except Exception as e:
            self.logger.error(f"Error loading food groups: {e}")
            return []

    def create_sustainable_meal(self, meal_type: str) -> Meal:
        """
        Create a sustainable meal with low environmental impact foods.
        Prioritizes plant-based foods with good nutritional profiles.
        """
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        # Updated sustainable groups with better environmental profiles
        sustainable_groups = {
            'Vegetables and Vegetable Products': {'priority': 1, 'min_qty': 80, 'max_qty': 150},
            'Fruits and fruit juices': {'priority': 1, 'min_qty': 60, 'max_qty': 120},
            'Legumes and Legume Products': {'priority': 1, 'min_qty': 50, 'max_qty': 100},
            'Nuts and Seeds': {'priority': 2, 'min_qty': 15, 'max_qty': 30},
            'Cereals, Grains and Pasta': {'priority': 2, 'min_qty': 40, 'max_qty': 80},
            'Finfish and Shellfish Products': {'priority': 3, 'min_qty': 60, 'max_qty': 100}
        }
        
        foods = self._create_meal_from_groups(sustainable_groups, meal_type, "sustainable")
        
        if not foods:
            raise ValueError("Could not create a sustainable meal with the available food data")

        return Meal(foods)

    def create_unsustainable_meal(self, meal_type: str) -> Meal:
        """
        Create an unsustainable meal with high environmental impact foods.
        Focuses on resource-intensive animal products and processed foods.
        """
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        unsustainable_groups = {
            'Beef Products': {'priority': 1, 'min_qty': 100, 'max_qty': 200},
            'Lamb, Veal and Game': {'priority': 1, 'min_qty': 100, 'max_qty': 180},
            'Pork Products': {'priority': 2, 'min_qty': 80, 'max_qty': 150},
            'Fast Foods': {'priority': 2, 'min_qty': 150, 'max_qty': 300},
            'Dairy and Egg Products': {'priority': 3, 'min_qty': 100, 'max_qty': 200},
            'Sweets': {'priority': 3, 'min_qty': 50, 'max_qty': 100}
        }
        
        foods = self._create_meal_from_groups(unsustainable_groups, meal_type, "unsustainable")
        
        if not foods:
            raise ValueError("Could not create an unsustainable meal with the available food data")

        return Meal(foods)

    def create_ultra_processed_meal(self, meal_type: str) -> Meal:
        """
        Create a meal focused on ultra-processed foods.
        High in processing, packaging, and typically low nutritional quality.
        """
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        ultra_processed_groups = {
            'Fast Foods': {'priority': 1, 'min_qty': 200, 'max_qty': 350},
            'Sweets': {'priority': 1, 'min_qty': 50, 'max_qty': 120},
            'Snacks': {'priority': 1, 'min_qty': 40, 'max_qty': 80},
            'Sausages and Luncheon meats': {'priority': 2, 'min_qty': 60, 'max_qty': 120},
            'Beverages': {'priority': 2, 'min_qty': 250, 'max_qty': 500},
            'Breakfast cereals': {'priority': 3, 'min_qty': 40, 'max_qty': 80}
        }
        
        foods = self._create_meal_from_groups(ultra_processed_groups, meal_type, "ultra-processed")
        
        if not foods:
            raise ValueError("Could not create an ultra-processed meal with the available food data")

        return Meal(foods)
    
    def create_balanced_meal(self, meal_type: str) -> Meal:
        """
        Create a nutritionally balanced meal with moderate environmental impact.
        Includes a mix of food groups following dietary guidelines.
        """
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        balanced_groups = {
            'Vegetables and Vegetable Products': {'priority': 1, 'min_qty': 100, 'max_qty': 150},
            'Fruits and fruit juices': {'priority': 1, 'min_qty': 80, 'max_qty': 120},
            'Cereals, Grains and Pasta': {'priority': 1, 'min_qty': 60, 'max_qty': 100},
            'Poultry Products': {'priority': 2, 'min_qty': 80, 'max_qty': 120},
            'Legumes and Legume Products': {'priority': 2, 'min_qty': 40, 'max_qty': 80},
            'Dairy and Egg Products': {'priority': 3, 'min_qty': 60, 'max_qty': 100},
            'Nuts and Seeds': {'priority': 3, 'min_qty': 15, 'max_qty': 25}
        }
        
        foods = self._create_meal_from_groups(balanced_groups, meal_type, "balanced")
        
        if not foods:
            raise ValueError("Could not create a balanced meal with the available food data")

        return Meal(foods)
    
    def _create_meal_from_groups(self, food_groups_config: Dict, meal_type: str, meal_style: str) -> List[Food]:
        """
        Helper method to create meals from food group configurations.
        
        :param food_groups_config: Dictionary with food group names as keys and config as values
        :param meal_type: Type of meal (breakfast, lunch, dinner, snack)
        :param meal_style: Style of meal for logging
        :return: List of Food objects
        """
        foods = []
        
        # Adjust number of food items based on meal type
        meal_size_limits = {
            'breakfast': (2, 4),
            'lunch': (3, 5), 
            'dinner': (3, 6),
            'snack': (1, 2)
        }
        min_foods, max_foods = meal_size_limits.get(meal_type, (3, 5))
        
        # Sort groups by priority
        sorted_groups = sorted(food_groups_config.items(), key=lambda x: x[1]['priority'])
        
        foods_added = 0
        target_foods = random.randint(min_foods, max_foods)
        
        for group_name, config in sorted_groups:
            if foods_added >= target_foods:
                break
                
            if group_name in self.food_groups:
                try:
                    # Get foods from this group
                    food_ids = self._get_food_ids_for_group(group_name)
                    if food_ids:
                        # Randomly select a food from the group
                        food_id = random.choice(food_ids)
                        quantity = random.randint(config['min_qty'], config['max_qty'])
                        
                        # Adjust quantity based on meal type
                        if meal_type == 'snack':
                            quantity = int(quantity * 0.6)
                        elif meal_type == 'dinner':
                            quantity = int(quantity * 1.2)
                            
                        foods.append(Food(food_id, quantity, self.data_loader))
                        foods_added += 1
                        self.logger.info(f"Added {group_name} (ID: {food_id}, {quantity}g) to {meal_style} {meal_type}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to add {group_name} to {meal_style} meal: {str(e)}")
            else:
                self.logger.warning(f"Food group '{group_name}' not found in database")
        
        return foods
    
    def _get_food_ids_for_group(self, group_name: str) -> List[int]:
        """
        Get food IDs for a specific food group.
        """
        try:
            # Try using data_loader first
            if hasattr(self.data_loader, 'food_name') and hasattr(self.data_loader, 'food_group'):
                if not self.data_loader.food_name.empty and not self.data_loader.food_group.empty:
                    group_id = self.data_loader.food_group[
                        self.data_loader.food_group['FoodGroupName'] == group_name
                    ]['FoodGroupID'].values
                    
                    if len(group_id) > 0:
                        food_ids = self.data_loader.food_name[
                            self.data_loader.food_name['FoodGroupID'] == group_id[0]
                        ]['FoodID'].tolist()
                        return food_ids
            
            # Fallback to CNF integrator
            food_name_df = self.cnf_integrator.get_dataframe('food_name')
            food_group_df = self.cnf_integrator.get_dataframe('food_group')
            
            if not food_name_df.empty and not food_group_df.empty:
                group_id = food_group_df[
                    food_group_df['FoodGroupName'] == group_name
                ]['FoodGroupID'].values
                
                if len(group_id) > 0:
                    food_ids = food_name_df[
                        food_name_df['FoodGroupID'] == group_id[0]
                    ]['FoodID'].tolist()
                    return food_ids
                    
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting food IDs for group {group_name}: {e}")
            return []

    def __str__(self) -> str:
        return f"ReferenceMeals(meal_types={self.meal_types})"

    def __repr__(self) -> str:
        return self.__str__()

