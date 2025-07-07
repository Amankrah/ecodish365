import os
import sys
import time
import logging

# Add necessary paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

from heni_calculator.heni.database.cnf_database import CNFDatabase
from heni_calculator.heni.models.ingredient import Ingredient
from heni_calculator.heni.calculator.heni_calculator import HENICalculator
from heni_calculator.heni.config import LLM_API_KEY, CNF_FOLDER

from environmental_impact_model.src.data_loader import DataLoader
from environmental_impact_model.src.food import Food
from environmental_impact_model.src.meal import Meal
from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment
from environmental_impact_model.src.monetization import Monetization

from net_health_impact_calculator.src.net_health_impact import NetHealthImpactCalculator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        start_time = time.time()

        # Initialize HENI calculator
        cnf_db = CNFDatabase(CNF_FOLDER)
        heni_calculator = HENICalculator(cnf_db, LLM_API_KEY)

        # Initialize environmental impact calculator
        data_loader = DataLoader()

        # Create meal
        heni_ingredients = [
            Ingredient(food_id=2003, amount=150, unit="g", cnf_db=cnf_db),
            Ingredient(food_id=3580, amount=100, unit="g", cnf_db=cnf_db),
            Ingredient(food_id=2892, amount=10, unit="ml", cnf_db=cnf_db)
        ]
        env_foods = [
            Food(food_id=2003, quantity=150, data_loader=data_loader),
            Food(food_id=3580, quantity=100, data_loader=data_loader),
            Food(food_id=2892, quantity=10, data_loader=data_loader)
        ]
        meal = Meal(env_foods)

        # Calculate net health impact
        net_calculator = NetHealthImpactCalculator(heni_calculator, LifeCycleAssessment, Monetization)
        net_impact = net_calculator.calculate_net_impact(heni_ingredients, meal)

        # Print results
        print(f"\nNet Health Impact: {net_impact:.2f} minutes of healthy life")

        end_time = time.time()
        print(f"Execution Time: {end_time - start_time:.6f} seconds")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise  # This will print the full traceback

if __name__ == "__main__":
    main()