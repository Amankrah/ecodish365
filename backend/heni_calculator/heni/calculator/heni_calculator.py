from typing import List, Tuple, Dict
from ..database.cnf_database import CNFDatabase
from ..models.ingredient import Ingredient
from ..categorization.llm_categorizer import LLMFoodCategorizer
from ..config import DRF_TABLE

import logging

logger = logging.getLogger(__name__)

class HENICalculator:
    def __init__(self, cnf_db: CNFDatabase, llm_api_key: str):
        self.cnf_db = cnf_db
        self.drf_table = DRF_TABLE
        self.categorizer = LLMFoodCategorizer(cnf_db, llm_api_key)

    def calculate_heni(self, ingredients: List[Ingredient]) -> Tuple[float, float, float, Dict[int, Dict[str, float]]]:
        total_heni = 0
        total_kcal = 0
        ingredient_categories = {}

        for ingredient in ingredients:
            logger.info(f"Processing ingredient: {ingredient.food_id}, amount: {ingredient.amount}, unit: {ingredient.unit}")
            ingredient_kcal = ingredient.kcal * (float(ingredient.amount) / 100)
            logger.info(f"Ingredient kcal: {ingredient_kcal}")
            total_kcal += ingredient_kcal

            categories = self.categorizer.categorize_food(ingredient.food_id)
            ingredient_categories[ingredient.food_id] = categories
            
            for category, score in categories.items():
                if category in self.drf_table:
                    drf = self.drf_table[category]
                    logger.info(f"Category: {category}, DRF: {drf}, Score: {score}")
                    heni_contribution = float(drf) * float(score) * (ingredient_kcal / 100)
                    logger.info(f"HENI contribution: {heni_contribution}")
                    total_heni += heni_contribution

        logger.info(f"Total HENI: {total_heni}, Total kcal: {total_kcal}")
        heni_per_100kcal = (total_heni / total_kcal) * 100 if total_kcal != 0 else 0
        logger.info(f"HENI per 100kcal: {heni_per_100kcal}")
        return round(heni_per_100kcal, 2), round(total_kcal, 2), round(total_heni, 2), ingredient_categories