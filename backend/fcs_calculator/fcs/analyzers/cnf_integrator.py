import pandas as pd
import re
from typing import List
from fcs.models.food_item import FoodItem
from fcs.utils.data_loader import load_cnf_data
import logging

logger = logging.getLogger(__name__)

class CNFIntegrator:
    @staticmethod
    def normalize_nutrient_name(nutrient_name: str) -> str:
        return re.sub(r'[^\w\s]', '', nutrient_name).replace(' ', '_').lower()

    @staticmethod
    def extract_nutrients_from_cnf(food_ids: List[int], food_item: FoodItem) -> FoodItem:
        try:
            nutrient_name_df, nutrient_amount_df = load_cnf_data()
            
            logger.info(f"Nutrient name columns: {nutrient_name_df.columns.tolist()}")
            logger.info(f"Nutrient amount columns: {nutrient_amount_df.columns.tolist()}")
            
            if 'NutrientName' not in nutrient_name_df.columns:
                raise KeyError(f"'NutrientName' column not found in nutrient_name_df. Available columns: {nutrient_name_df.columns.tolist()}")
            
            food_nutrients = nutrient_amount_df[nutrient_amount_df['FoodID'].isin(food_ids)]
            merged_data = pd.merge(food_nutrients, nutrient_name_df, on='NutrientID')
            
            logger.info(f"Merged data columns: {merged_data.columns.tolist()}")
            
            if merged_data.empty:
                raise ValueError(f"No nutrient data found for food IDs: {food_ids}")
            
            # Get energy value (assuming it's in kcal)
            energy_rows = merged_data[merged_data['NutrientName'] == 'ENERGY (KILOCALORIES)']
            if energy_rows.empty:
                raise ValueError("Energy (kilocalories) data not found")
            energy_value = energy_rows['NutrientValue'].iloc[0]
            
            for _, row in merged_data.iterrows():
                nutrient_name = row['NutrientName']
                nutrient_value = row['NutrientValue']
                normalized_nutrient_name = CNFIntegrator.normalize_nutrient_name(nutrient_name)
                
                # Normalize nutrient value to 100 kcal
                normalized_value = (nutrient_value / energy_value) * 100
                
                for domain in food_item.attributes:
                    if normalized_nutrient_name in food_item.attributes[domain]:
                        food_item.set_attribute(domain, normalized_nutrient_name, normalized_value)
                        break
            
            return food_item
        except Exception as e:
            logger.error(f"Error in extract_nutrients_from_cnf: {str(e)}")
            raise