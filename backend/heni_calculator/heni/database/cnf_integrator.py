"""
HENI CNF Data Integrator
Uses the shared CNF pipeline to avoid expensive reinitialization and maintain consistency
with HEFI and FCS implementations.
"""

import os
import sys
import logging
from typing import Dict, List, Optional
import pandas as pd

# Use the same CNF pipeline wiring as the FCS and HEFI integrators
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
api_dir = os.path.join(backend_dir, 'api')
sys.path.append(api_dir)
from cnf_data_pipeline import CNFDataPipeline  # type: ignore

# Global pipeline instance to avoid expensive reinitialization
_cnf_pipeline_instance = None

def get_shared_cnf_pipeline(cnf_dir: str) -> CNFDataPipeline:
    """Get shared CNF pipeline instance to avoid expensive reinitialization"""
    global _cnf_pipeline_instance
    if _cnf_pipeline_instance is None:
        _cnf_pipeline_instance = CNFDataPipeline(cnf_dir)
    return _cnf_pipeline_instance

logger = logging.getLogger(__name__)

class HENICNFIntegrator:
    """
    HENI CNF Data Integrator that uses the shared CNF pipeline
    for consistent database loading across all calculators.
    """
    
    def __init__(self, cnf_dir: str):
        self.cnf_dir = cnf_dir
        self.pipeline = get_shared_cnf_pipeline(cnf_dir)
        
        # Nutrient mapping for HENI calculations
        self.nutrient_lookup = {
            'ENERGY (KILOCALORIES)': 'energy_kcal',
            'CALCIUM': 'calcium',
            'FATTY ACIDS, SATURATED, TOTAL': 'saturated_fat',
            'FATTY ACIDS, POLYUNSATURATED, TOTAL': 'polyunsaturated_fat',
            'FIBRE, TOTAL DIETARY': 'fiber',
            'FATTY ACIDS, TRANS, TOTAL': 'trans_fat',
            'SODIUM': 'sodium',
            'SUGARS, TOTAL': 'total_sugars',
        }
        
        # Food group mappings for HENI dietary risk factors
        self.food_group_risk_mapping = {
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
    
    def get_kcal(self, food_id: int) -> float:
        """Get energy content in kilocalories for a food item"""
        try:
            nutrients = self._get_nutrients([food_id])
            energy_rows = nutrients[nutrients['NutrientName'] == 'ENERGY (KILOCALORIES)']
            if not energy_rows.empty:
                return float(energy_rows['NutrientValue'].iloc[0])
            return 0.0
        except Exception as e:
            logger.warning(f"Could not get kcal for food ID {food_id}: {e}")
            return 0.0
    
    def get_food_description(self, food_id: int) -> str:
        """Get food description for a food item"""
        try:
            food_row = self.pipeline.food_name_df[
                self.pipeline.food_name_df['FoodID'] == food_id
            ]
            if not food_row.empty:
                return str(food_row['FoodDescription'].iloc[0])
            return "Unknown"
        except Exception as e:
            logger.warning(f"Could not get description for food ID {food_id}: {e}")
            return "Unknown"
    
    def get_food_group(self, food_id: int) -> str:
        """Get food group name for a food item"""
        try:
            food_row = self.pipeline.food_name_df[
                self.pipeline.food_name_df['FoodID'] == food_id
            ]
            if not food_row.empty:
                group_id = food_row['FoodGroupID'].iloc[0]
                group_row = self.pipeline.food_group_df[
                    self.pipeline.food_group_df['FoodGroupID'] == group_id
                ]
                if not group_row.empty:
                    return str(group_row['FoodGroupName'].iloc[0])
            return "Unknown"
        except Exception as e:
            logger.warning(f"Could not get food group for food ID {food_id}: {e}")
            return "Unknown"
    
    def get_nutrient_data(self, food_id: int) -> Dict[str, float]:
        """Get all nutrient data for a food item"""
        try:
            nutrients = self._get_nutrients([food_id])
            nutrient_data = {}
            
            for _, row in nutrients.iterrows():
                nutrient_name = row['NutrientName']
                nutrient_value = float(row['NutrientValue'])
                if nutrient_value > 0:
                    nutrient_data[nutrient_name] = nutrient_value
            
            return nutrient_data
        except Exception as e:
            logger.warning(f"Could not get nutrient data for food ID {food_id}: {e}")
            return {}
    
    def get_dietary_risks(self, food_id: int) -> Dict[str, float]:
        """Calculate dietary risk factors for HENI scoring"""
        try:
            food_group = self.get_food_group(food_id)
            nutrient_data = self.get_nutrient_data(food_id)
            food_description = self.get_food_description(food_id).lower()
            risks = {}
            
            # Food group based risks
            for group, risk in self.food_group_risk_mapping.items():
                if group in food_group:
                    risks[risk] = 1.0
            
            # Nutrient based risks
            nutrient_risk_mapping = {
                "CALCIUM": "calcium",
                "FATTY ACIDS, SATURATED, TOTAL": "saturated_fatty_acids", 
                "FATTY ACIDS, POLYUNSATURATED, TOTAL": "polyunsaturated_fatty_acids",
                "FIBRE, TOTAL DIETARY": "fiber",
                "FATTY ACIDS, TRANS, TOTAL": "trans_fatty_acids",
                "SODIUM": "sodium"
            }
            
            for nutrient_name, risk_name in nutrient_risk_mapping.items():
                amount = nutrient_data.get(nutrient_name, 0)
                if amount > 0:
                    risks[risk_name] = amount
            
            # Special processing for processed meat detection
            if any(meat_group in food_group for meat_group in ["Beef Products", "Pork Products", "Poultry Products"]):
                if any(term in food_description for term in ["processed", "sausage", "ham", "bacon", "deli", "cured", "smoked"]):
                    risks["processed_meat"] = 1.0
                else:
                    risks["red_meat"] = 1.0
            
            # Sugar-sweetened beverages detection
            if "Beverages" in food_group:
                sugar_content = nutrient_data.get("SUGARS, TOTAL", 0)
                if sugar_content > 5:  # More than 5g sugar per 100g
                    risks["sugar_sweetened_beverages"] = 1.0
            
            return risks
            
        except Exception as e:
            logger.warning(f"Could not calculate dietary risks for food ID {food_id}: {e}")
            return {}
    
    def _get_nutrients(self, food_ids: List[int]) -> pd.DataFrame:
        """Get nutrient data for food items using shared pipeline"""
        try:
            # Get nutrient amounts for the specified foods
            food_nutrients = self.pipeline.nutrient_amount_df[
                self.pipeline.nutrient_amount_df['FoodID'].isin(food_ids)
            ]
            
            # Merge with nutrient names
            merged = pd.merge(
                food_nutrients,
                self.pipeline.nutrient_name_df,
                on='NutrientID',
                how='left'
            )
            
            return merged
        except Exception as e:
            logger.error(f"Error getting nutrients: {e}")
            return pd.DataFrame()


def create_heni_cnf_integrator(cnf_dir: str = None) -> HENICNFIntegrator:
    """
    Factory function to create HENI CNF integrator using shared data directory
    """
    if cnf_dir is None:
        # Use the same default as other calculators
        from django.conf import settings
        cnf_dir = settings.CNF_FOLDER
    
    return HENICNFIntegrator(cnf_dir)