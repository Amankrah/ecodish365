import random
import logging
from src.food import Food
from src.meal import Meal


class ReferenceMeals:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        self.food_groups = self._load_food_groups()
        self.logger = logging.getLogger(__name__)

    def _load_food_groups(self):
        return self.data_loader.food_group['FoodGroupName'].unique().tolist()

    def create_sustainable_meal(self, meal_type: str) -> Meal:
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        sustainable_groups = [
            'Vegetables and Vegetable Products',
            'Fruits and fruit juices',
            'Legumes and Legume Products',
            'Nuts and Seeds',
            'Cereals, Grains and Pasta',
            'Finfish and Shellfish Products'
        ]
        foods = []

        for group in sustainable_groups:
            if group in self.food_groups:
                try:
                    food_ids = self.data_loader.food_name[self.data_loader.food_name['FoodGroupID'] == 
                               self.data_loader.food_group[self.data_loader.food_group['FoodGroupName'] == group]['FoodGroupID'].values[0]]['FoodID'].tolist()
                    if food_ids:
                        food_id = random.choice(food_ids)
                        quantity = random.randint(50, 150)  # Adjust quantity as needed
                        foods.append(Food(food_id, quantity, self.data_loader))
                        self.logger.info(f"Added {group} (ID: {food_id}) to sustainable meal")
                except Exception as e:
                    self.logger.warning(f"Failed to add {group} to sustainable meal: {str(e)}")
            else:
                self.logger.warning(f"Food group '{group}' not found in database")

        if not foods:
            self.logger.error("Failed to create any foods for sustainable meal")
            raise ValueError("Could not create a sustainable meal with the available food data")

        return Meal(foods)

    def create_unsustainable_meal(self, meal_type: str) -> Meal:
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        unsustainable_groups = ['Beef Products', 'Pork Products', 'Fast Foods', 'Sweets']
        foods = []

        for group in unsustainable_groups:
            if group in self.food_groups:
                try:
                    food_ids = self.data_loader.food_name[self.data_loader.food_name['FoodGroupID'] == 
                               self.data_loader.food_group[self.data_loader.food_group['FoodGroupName'] == group]['FoodGroupID'].values[0]]['FoodID'].tolist()
                    if food_ids:
                        food_id = random.choice(food_ids)
                        quantity = random.randint(100, 300)  # Larger portions for unsustainable meals
                        foods.append(Food(food_id, quantity, self.data_loader))
                        self.logger.info(f"Added {group} (ID: {food_id}) to unsustainable meal")
                except Exception as e:
                    self.logger.warning(f"Failed to add {group} to unsustainable meal: {str(e)}")
            else:
                self.logger.warning(f"Food group '{group}' not found in database")

        if not foods:
            self.logger.error("Failed to create any foods for unsustainable meal")
            raise ValueError("Could not create an unsustainable meal with the available food data")

        return Meal(foods)

    def create_ultra_processed_meal(self, meal_type: str) -> Meal:
        if meal_type not in self.meal_types:
            raise ValueError(f"Invalid meal type. Choose from {self.meal_types}")

        ultra_processed_groups = ['Fast Foods', 'Sweets', 'Snacks', 'Sausages and Luncheon meats']
        foods = []

        for group in ultra_processed_groups:
            if group in self.food_groups:
                try:
                    food_ids = self.data_loader.food_name[self.data_loader.food_name['FoodGroupID'] == 
                               self.data_loader.food_group[self.data_loader.food_group['FoodGroupName'] == group]['FoodGroupID'].values[0]]['FoodID'].tolist()
                    if food_ids:
                        food_id = random.choice(food_ids)
                        quantity = random.randint(50, 200)
                        foods.append(Food(food_id, quantity, self.data_loader))
                        self.logger.info(f"Added {group} (ID: {food_id}) to ultra-processed meal")
                except Exception as e:
                    self.logger.warning(f"Failed to add {group} to ultra-processed meal: {str(e)}")
            else:
                self.logger.warning(f"Food group '{group}' not found in database")

        if not foods:
            self.logger.error("Failed to create any foods for ultra-processed meal")
            raise ValueError("Could not create an ultra-processed meal with the available food data")

        return Meal(foods)

    def __str__(self) -> str:
        return f"ReferenceMeals(meal_types={self.meal_types})"

    def __repr__(self) -> str:
        return self.__str__()

