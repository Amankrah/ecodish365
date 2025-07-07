import os
import pandas as pd
import logging
from functools import lru_cache
from typing import Dict
from ..utils.file_utils import detect_encoding
from ..models.nutrient_info import NutrientInfo

logger = logging.getLogger(__name__)

class CNFDatabase:
    def __init__(self, cnf_folder: str):
        self.cnf_folder = cnf_folder
        self._encoding = None
        self._load_data()
        self._create_mappings()

    def _detect_and_cache_encoding(self, file_path: str) -> str:
        """Detect and cache the file encoding for reuse."""
        if self._encoding is None:
            self._encoding = detect_encoding(file_path)
        return self._encoding

    def _load_data(self):
        """Load all necessary data files."""
        try:
            encoding = self._detect_and_cache_encoding(os.path.join(self.cnf_folder, 'FOOD_NAME.csv'))

            self.food_group_df = pd.read_csv(os.path.join(self.cnf_folder, 'FOOD_GROUP.csv'), encoding=encoding)
            self.food_name_df = pd.read_csv(os.path.join(self.cnf_folder, 'FOOD_NAME.csv'), encoding=encoding)
            self.nutrient_amount_df = pd.read_csv(os.path.join(self.cnf_folder, 'NUTRIENT_AMOUNT.csv'), encoding=encoding)
            self.nutrient_name_df = pd.read_csv(os.path.join(self.cnf_folder, 'NUTRIENT_NAME.csv'), encoding=encoding)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def _create_mappings(self):
        """Create mappings between food IDs and groups, and nutrient information."""
        self.food_to_group_mapping = dict(zip(self.food_name_df['FoodID'], self.food_name_df['FoodGroupID']))
        self.nutrient_info = {row['NutrientID']: NutrientInfo(row['NutrientID'], row['NutrientName'], row['NutrientUnit']) 
                              for _, row in self.nutrient_name_df.iterrows()}

    @lru_cache(maxsize=1000)
    def get_kcal(self, food_id: int) -> float:
        """Retrieve kcal for a given food."""
        kcal_nutrient_id = self.nutrient_name_df[self.nutrient_name_df['NutrientName'] == 'ENERGY (KILOCALORIES)']['NutrientID'].values[0]
        kcal_row = self.nutrient_amount_df[
            (self.nutrient_amount_df['FoodID'] == food_id) & 
            (self.nutrient_amount_df['NutrientID'] == kcal_nutrient_id)
        ]
        if kcal_row.empty:
            logger.warning(f"Could not find Energy (kcal) value for Food ID {food_id}")
            return 0.0
        return float(kcal_row['NutrientValue'].values[0])

    @lru_cache(maxsize=1000)
    def get_food_group(self, food_id: int) -> str:
        """Retrieve food group name for a given food ID."""
        group_id = self.food_to_group_mapping.get(food_id)
        if group_id is None:
            return "Unknown"
        group_name = self.food_group_df[self.food_group_df['FoodGroupID'] == group_id]['FoodGroupName'].values
        return group_name[0] if len(group_name) > 0 else "Unknown"

    @lru_cache(maxsize=1000)
    def get_nutrient_amount(self, food_id: int, nutrient_id: int) -> float:
        """Retrieve nutrient amount for a given food and nutrient."""
        nutrient_row = self.nutrient_amount_df[
            (self.nutrient_amount_df['FoodID'] == food_id) &
            (self.nutrient_amount_df['NutrientID'] == nutrient_id)
        ]
        return float(nutrient_row['NutrientValue'].values[0]) if not nutrient_row.empty else 0.0

    def get_food_description(self, food_id: int) -> str:
        """Retrieve food description for a given food ID."""
        description = self.food_name_df[self.food_name_df['FoodID'] == food_id]['FoodDescription'].values
        return description[0] if len(description) > 0 else "Unknown"

    def get_nutrient_data(self, food_id: int) -> Dict[str, float]:
        """Retrieve all nutrient data for a given food ID."""
        nutrient_data = {}
        for nutrient_id, nutrient_info in self.nutrient_info.items():
            amount = self.get_nutrient_amount(food_id, nutrient_id)
            if amount > 0:
                nutrient_data[nutrient_info.name] = amount
        return nutrient_data
    
    @lru_cache(maxsize=1000)
    def get_dietary_risks(self, food_id: int) -> Dict[str, float]:
        """Calculate dietary risks based on food group and nutrient content."""
        food_group = self.get_food_group(food_id)
        nutrient_data = self.get_nutrient_data(food_id)
        risks = {}

        # Food group based risks
        group_risk_mapping = {
            "Finfish and Shellfish Products": "seafood",
            "Nuts and Seeds": "nuts_seeds",
            "Cereals, Grains and Pasta": "whole_grains",
            "Legumes and Legume Products": "legumes",
            "Fruits and fruit juices": "fruits",
            "Vegetables and Vegetable Products": "vegetables",
            "Milk Products": "milk",
            "Beverages": "sugar_sweetened_beverages",
            "Beef Products": "red_meat",
            "Pork Products": "red_meat",
            "Poultry Products": "poultry"
        }

        # Assign DRF based on food group
        for group, risk in group_risk_mapping.items():
            if group in food_group:
                risks[risk] = 1.0  # Presence indicator for food group risks

        # Nutrient based risks
        nutrient_risk_mapping = {
            "CALCIUM": "calcium",
            "FATTY ACIDS, SATURATED, TOTAL": "saturated_fatty_acids",
            "FATTY ACIDS, POLYUNSATURATED, TOTAL": "polyunsaturated_fatty_acids",
            "FIBRE, TOTAL DIETARY": "fiber",
            "FATTY ACIDS, TRANS, TOTAL": "trans_fatty_acids",
            "SODIUM": "sodium"
        }

        # Calculate risks based on nutrient content
        for nutrient_name, risk_name in nutrient_risk_mapping.items():
            amount = nutrient_data.get(nutrient_name, 0)
            if amount > 0:
                risks[risk_name] = amount

        # Special case for processed meat
        if "Meat and Poultry" in food_group:
            food_description = self.get_food_description(food_id).lower()
            if "processed" in food_description or "sausage" in food_description or "ham" in food_description:
                risks["processed_meat"] = 1.0
            else:
                risks["red_meat"] = 1.0

        return risks

    def get_food_description(self, food_id: int) -> str:
        """Retrieve food description for a given food ID."""
        description = self.food_name_df[self.food_name_df['FoodID'] == food_id]['FoodDescription'].values
        return description[0] if len(description) > 0 else "Unknown"

    def get_nutrient_data(self, food_id: int) -> Dict[str, float]:
        """Retrieve all nutrient data for a given food ID."""
        nutrient_data = {}
        for nutrient_id, nutrient_info in self.nutrient_info.items():
            amount = self.get_nutrient_amount(food_id, nutrient_id)
            if amount > 0:
                nutrient_data[nutrient_info.name] = amount
        return nutrient_data