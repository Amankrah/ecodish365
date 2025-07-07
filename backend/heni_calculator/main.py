import os
import sys
import time

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from heni.database.cnf_database import CNFDatabase
from heni.models.ingredient import Ingredient
from heni.calculator.heni_calculator import HENICalculator
from heni.config import LLM_API_KEY, CNF_FOLDER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        start_time = time.time()
        
        cnf_db = CNFDatabase(CNF_FOLDER)
        heni_calculator = HENICalculator(cnf_db, LLM_API_KEY)

        meal = [
            Ingredient(food_id=2003, amount=150, unit="g", cnf_db=cnf_db),
            Ingredient(food_id=3580, amount=100, unit="g", cnf_db=cnf_db),
            Ingredient(food_id=2892, amount=10, unit="ml", cnf_db=cnf_db)
        ]

        heni_score, ingredient_categories = heni_calculator.calculate_heni(meal)
        if heni_score == 0:
            print("HENI Score for the meal: Minimal impact on health (0 μDALYs per 100 kcal)")
        else:
            print(f"HENI Score for the meal: {heni_score} μDALYs per 100 kcal")

        print("\nDetailed ingredient breakdown:")
        for ingredient in meal:
            food_description = cnf_db.get_food_description(ingredient.food_id)
            categories = ingredient_categories[ingredient.food_id]
            print(f"\n{food_description} ({ingredient.amount}{ingredient.unit}):")
            
            if any(score > 0 for score in categories.values()):
                for category, score in categories.items():
                    if score > 0:
                        print(f"  - {category}: {score}")
            else:
                print("  No significant categories")
                    
        print("\nSummary of scores:")
        total_scores = {}
        for categories in ingredient_categories.values():
            for category, score in categories.items():
                if score > 0:
                    total_scores[category] = total_scores.get(category, 0) + score

        for category, total_score in total_scores.items():
            print(f"  - {category}: {total_score}")
            
        end_time = time.time()
        print(f"Execution Time: {end_time - start_time:.6f} seconds")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()