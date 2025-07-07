import logging
from typing import Dict
import openai
from ..database.cnf_database import CNFDatabase
from ..config import DRF_TABLE
from .rule_based_categorizer import RuleBasedCategorizer

class LLMFoodCategorizer:
    def __init__(self, cnf_db: CNFDatabase, api_key: str):
        self.cnf_db = cnf_db
        self.client = openai.OpenAI(api_key=api_key)
        self.categories = list(DRF_TABLE.keys())
        self.categorization_cache = {}
        self.logger = logging.getLogger(__name__)
    
    def _create_prompt(self, food_description: str, nutrient_data: Dict, food_group: str, initial_categories: Dict[str, float]) -> str:
        prompt = f"""
        Given the following food description, nutritional information, food group, and initial categorization, please refine and complete the categorization of this food item into the following categories: {', '.join(self.categories)}.
        Provide a score from 0 to 1 for each category, where 0 means not applicable and 1 means strongly applicable.
        Multiple categories can apply to a single food item.

        Food Description: {food_description}
        Food Group: {food_group}

        Nutritional Information (per 100g):
        """
        for nutrient, value in nutrient_data.items():
            prompt += f"{nutrient}: {value}\n"

        prompt += "\nInitial Categorization:\n"
        for category, score in initial_categories.items():
            prompt += f"{category}: {score}\n"

        prompt += "\nPlease provide the refined and completed categorization in the following format:\n"
        prompt += "Category1: score\nCategory2: score\n...\n"
        prompt += "Provide a brief explanation for each non-zero score AND for any zero scores on initially categorized items."
        prompt += "\nEnsure all relevant categories are included, even if not in the initial categorization."
        prompt += "\nConsider trace amounts of nutrients, which might be relevant for processed foods or concentrates."

        return prompt

    def categorize_food(self, food_id: int) -> Dict[str, float]:
        if food_id in self.categorization_cache:
            return self.categorization_cache[food_id]

        food_description = self.cnf_db.get_food_description(food_id)
        nutrient_data = self.cnf_db.get_nutrient_data(food_id)
        food_group = self.cnf_db.get_food_group(food_id)
        
        # First, apply rule-based categorization
        categories = RuleBasedCategorizer.categorize(food_group, nutrient_data, food_description)
        
        # If rule-based categorization didn't yield results, use LLM
        if not categories:
            self.logger.info(f"Using LLM for categorization of {food_description}")
            prompt = self._create_prompt(food_description, nutrient_data, food_group, {})
            response = self._query_llm(prompt)
            llm_categories = self._parse_llm_response(response)
            categories = self._validate_and_adjust_categories(llm_categories, food_group, nutrient_data, categories)
        else:
            categories = self._validate_and_adjust_categories(categories, food_group, nutrient_data, categories)
        
        self.categorization_cache[food_id] = categories
        return categories

    def _validate_and_adjust_categories(self, categories: Dict[str, float], food_group: str, nutrient_data: Dict, initial_categories: Dict[str, float]) -> Dict[str, float]:
        if any(meat in food_group for meat in ["Beef Products", "Pork Products", "Lamb, Veal and Game"]) and "red_meat" not in categories and "processed_meat" not in categories:
            categories["red_meat"] = 1.0
            self.logger.warning(f"Forced 'red_meat' categorization for {food_group}")
        
        if "Finfish and Shellfish Products" in food_group:
            categories["seafood"] = max(categories.get("seafood", 0), 0.8)
        
        if "Beverages" in food_group and nutrient_data.get("SUGARS, TOTAL", 0) > 5:
            categories["sugar_sweetened_beverages"] = max(categories.get("sugar_sweetened_beverages", 0), 0.8)
        
        if nutrient_data.get("CALCIUM", 0) > 200:
            categories["calcium"] = max(categories.get("calcium", 0), 0.8)
        
        # Remove fiber from beverages
        if "Beverages" in food_group and "fiber" in categories:
            del categories["fiber"]
            self.logger.info(f"Removed 'fiber' category from beverage: {food_group}")
        
        # Ensure initially categorized items are not lost
        for category, score in initial_categories.items():
            if category not in categories:
                categories[category] = score
                self.logger.warning(f"Restored initial category {category} with score {score}")
        
        return {k: v for k, v in categories.items() if v >= 0.1}

    def _query_llm(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "You are a nutritionist expert in food categorization for health impact assessment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content

    def _parse_llm_response(self, response: str) -> Dict[str, float]:
        categories = {}
        for line in response.split('\n'):
            if ':' in line:
                category, score_and_explanation = line.split(':', 1)
                category = category.strip().lower()
                if category in self.categories:
                    score = float(score_and_explanation.split()[0])
                    categories[category] = score
        return categories