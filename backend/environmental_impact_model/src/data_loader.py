import pandas as pd
import logging
import os
from django.conf import settings
import chardet
from typing import Dict, Any

class DataLoader:
    def __init__(self):
        self.data_dir = settings.ENVIRONMENTAL_IMPACT_DATA_DIR
        self.logger = logging.getLogger(__name__)
        self._load_all_data()

    def _load_all_data(self) -> None:
        required_files = [
            'FOOD_GROUP.csv', 
            'FOOD_NAME.csv', 
            'NUTRIENT_AMOUNT.csv',
            'NUTRIENT_NAME.csv', 
            'CONVERSION_FACTOR.csv',
            'MEASURE_NAME.csv'
        ]
        for file in required_files:
            attr_name = file.split('.')[0].lower()
            setattr(self, attr_name, self._load_csv(file))

        self._create_nutrient_mappings()

    def _load_csv(self, filename: str) -> pd.DataFrame:
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            self.logger.error(f"File not found: {filepath}")
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if os.path.getsize(filepath) == 0:
            self.logger.warning(f"File is empty: {filepath}")
            raise pd.errors.EmptyDataError(f"File is empty: {filepath}")

        try:
            with open(filepath, 'rb') as file:
                raw_data = file.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            return pd.read_csv(filepath, encoding=encoding)
        except pd.errors.ParserError:
            self.logger.error(f"Parser error in file: {filepath}")
            raise

    def _create_nutrient_mappings(self):
        self.nutrient_id_to_name = dict(zip(self.nutrient_name['NutrientID'], self.nutrient_name['NutrientName']))
        self.nutrient_name_to_id = dict(zip(self.nutrient_name['NutrientName'], self.nutrient_name['NutrientID']))

    def get_food_data(self, food_id: int) -> Dict[str, Any]:
        try:
            food_info = self.food_name[self.food_name['FoodID'] == food_id].iloc[0].to_dict()
            nutrients = self.nutrient_amount[self.nutrient_amount['FoodID'] == food_id].to_dict('records')
            food_group = self.food_group[self.food_group['FoodGroupID'] == food_info['FoodGroupID']].iloc[0].to_dict()
            
            return {
                'food_info': food_info,
                'nutrients': nutrients,
                'food_group': food_group
            }
        except IndexError:
            self.logger.error(f"Food ID {food_id} not found")
            raise ValueError(f"Food ID {food_id} not found")
        
    def get_food_group(self, food_id: int) -> str:
        try:
            food_info = self.get_food_data(food_id)
            return food_info['food_group']['FoodGroupName']
        except ValueError:
            return "Unknown"

    def get_nutrient_amount(self, food_id: int, nutrient_name: str) -> float:
        nutrient_id = self.get_nutrient_id(nutrient_name)
        if nutrient_id is None:
            return 0.0
        
        nutrient_data = self.nutrient_amount[
            (self.nutrient_amount['FoodID'] == food_id) & 
            (self.nutrient_amount['NutrientID'] == nutrient_id)
        ]
        
        if nutrient_data.empty:
            return 0.0
        
        return nutrient_data.iloc[0]['NutrientValue']

    def get_conversion_factor(self, food_id: int, measure_id: int) -> float:
        conversion_data = self.conversion_factor[
            (self.conversion_factor['FoodID'] == food_id) & 
            (self.conversion_factor['MeasureID'] == measure_id)
        ]
        
        if conversion_data.empty:
            return 1.0
        
        return conversion_data.iloc[0]['ConversionFactorValue']

    def get_nutrient_id(self, nutrient_name: str) -> int:
        return self.nutrient_name_to_id.get(nutrient_name.upper())

    def get_nutrient_name(self, nutrient_id: int) -> str:
        return self.nutrient_id_to_name.get(nutrient_id, "Unknown")
    
    def get_cpi(self, year: int) -> float:
        base_cpi = 100.0
        annual_inflation_rate = 0.02
        years_since_base = year - 2015
        return base_cpi * (1 + annual_inflation_rate) ** years_since_base

    def __str__(self) -> str:
        return f"DataLoader(data_dir='{self.data_dir}')"

    def __repr__(self) -> str:
        return self.__str__()