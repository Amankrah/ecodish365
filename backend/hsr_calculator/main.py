import logging
import time
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hsr.utils.data_loader import load_cnf_data
from hsr.models.food import Food
from hsr.models.meal import Meal
from hsr.models.category import Category
from hsr.calculators.unified_hsr_calculator import UnifiedHSRCalculator
from hsr.calculators.fvnl_calculator import calculate_fvnl_content

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def map_food_group_to_category(food_group_id: int) -> Category:
    beverage_groups = [14]  # Beverages
    dairy_groups = [1]  # Dairy and Egg Products
    oils_groups = [4]  # Fats and Oils
    cheese_groups = [1]  # Assuming cheese is part of Dairy and Egg Products

    if food_group_id in beverage_groups:
        return Category.BEVERAGE
    elif food_group_id in dairy_groups:
        return Category.DAIRY_FOOD
    elif food_group_id in oils_groups:
        return Category.OILS_AND_SPREADS
    elif food_group_id in cheese_groups:
        # You may need additional logic to differentiate cheese from other dairy products
        return Category.CHEESE
    else:
        return Category.FOOD

def get_food_data(food_id: int, serving_size: float) -> Food:
    food_name_df, nutrient_name_df, nutrient_amount_df, food_group_df = load_cnf_data()
    
    food_data = food_name_df[food_name_df['FoodID'] == food_id].iloc[0]
    category = map_food_group_to_category(food_data['FoodGroupID'])
    
    nutrients = {}
    nutrient_data = nutrient_amount_df[nutrient_amount_df['FoodID'] == food_id]
    
    for _, row in nutrient_data.iterrows():
        nutrient_name = nutrient_name_df[nutrient_name_df['NutrientID'] == row['NutrientID']]['NutrientName'].iloc[0]
        nutrients[nutrient_name] = row['NutrientValue']

    fvnl_percent = calculate_fvnl_content(food_id)

    return Food(
        food_id=food_id,
        food_name=food_data['FoodDescription'],
        category=category,
        serving_size=serving_size,
        nutrients=nutrients,
        fvnl_percent=fvnl_percent
    )

def calculate_hsr_for_meal(food_ids: list[int], serving_sizes: list[float]) -> float:
    if len(food_ids) != len(serving_sizes):
        raise ValueError("The number of food IDs must match the number of serving sizes")

    foods = [get_food_data(food_id, serving_size) for food_id, serving_size in zip(food_ids, serving_sizes)]
    
    meal_category = max(set(food.category for food in foods), key=lambda x: [food.category for food in foods].count(x))
    
    meal = Meal(foods=foods, category=meal_category)
    calculator = UnifiedHSRCalculator(meal)
    return calculator.calculate_hsr()

def main():
    start_time = time.time()

    food_ids = [2003, 3580, 2892]  # Example food IDs
    serving_sizes = [150, 100, 10]  # Example serving sizes in grams
    
    try:
        # Load CNF data to verify it's working
        food_name_df, nutrient_name_df, nutrient_amount_df, food_group_df = load_cnf_data()
        logger.info("CNF data loaded successfully")

        hsr = calculate_hsr_for_meal(food_ids, serving_sizes)
        
        logger.info(f"Health Star Rating (HSR): {hsr:.1f}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())

    end_time = time.time()
    logger.info(f"Execution Time: {end_time - start_time:.3f} seconds")

if __name__ == "__main__":
    main()