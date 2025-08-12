import pandas as pd
import logging
import os
from django.conf import settings
import chardet
from typing import Dict, Any, Optional
from .cnf_integrator import get_cnf_integrator

class DataLoader:
    """
    Updated DataLoader that uses the central singleton CNF integrator.
    Maintains backward compatibility while leveraging centralized data access.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cnf_integrator = get_cnf_integrator()
        
        # Initialize the CNF integrator if not already done
        if not self.cnf_integrator.is_initialized():
            data_dir = getattr(settings, 'ENVIRONMENTAL_IMPACT_DATA_DIR', 'raw_cnf')
            self.cnf_integrator.initialize(data_dir)
        
        # Create backward compatibility attributes
        self._create_backward_compatibility_attributes()

    def _create_backward_compatibility_attributes(self):
        """Create attributes for backward compatibility with existing code"""
        try:
            # Map CNF integrator dataframes to old attribute names
            self.food_group = self.cnf_integrator.get_dataframe('food_group')
            self.food_name = self.cnf_integrator.get_dataframe('food_name')
            self.nutrient_amount = self.cnf_integrator.get_dataframe('nutrient_amount')
            self.nutrient_name = self.cnf_integrator.get_dataframe('nutrient_name')
            self.conversion_factor = self.cnf_integrator.get_dataframe('conversion_factor')
            self.measure_name = self.cnf_integrator.get_dataframe('measure_name')
            
            # Create nutrient mappings for backward compatibility
            if not self.nutrient_name.empty:
                self.nutrient_id_to_name = dict(zip(self.nutrient_name['NutrientID'], self.nutrient_name['NutrientName']))
                self.nutrient_name_to_id = dict(zip(self.nutrient_name['NutrientName'], self.nutrient_name['NutrientID']))
            else:
                self.nutrient_id_to_name = {}
                self.nutrient_name_to_id = {}
                
        except Exception as e:
            self.logger.error(f"Error creating backward compatibility attributes: {e}")
            # Create empty DataFrames as fallback
            self.food_group = pd.DataFrame()
            self.food_name = pd.DataFrame()
            self.nutrient_amount = pd.DataFrame()
            self.nutrient_name = pd.DataFrame()
            self.conversion_factor = pd.DataFrame()
            self.measure_name = pd.DataFrame()
            self.nutrient_id_to_name = {}
            self.nutrient_name_to_id = {}

    def get_food_data(self, food_id: int) -> Dict[str, Any]:
        """Get comprehensive food data using the CNF integrator"""
        try:
            # Use the CNF integrator for more robust data retrieval
            food_data = self.cnf_integrator.get_food_data(food_id)
            if food_data is None:
                raise ValueError(f"Food ID {food_id} not found")
            return food_data
        except Exception as e:
            self.logger.error(f"Error getting food data for ID {food_id}: {e}")
            raise ValueError(f"Food ID {food_id} not found")
        
    def get_food_group(self, food_id: int) -> str:
        try:
            food_info = self.get_food_data(food_id)
            return food_info['food_group']['FoodGroupName']
        except ValueError:
            return "Unknown"

    def get_nutrient_amount(self, food_id: int, nutrient_name: str) -> float:
        """Get nutrient amount using the CNF integrator"""
        return self.cnf_integrator.get_nutrient_amount(food_id, nutrient_name)

    def get_conversion_factor(self, food_id: int, measure_id: int) -> float:
        """Get conversion factor using the CNF integrator"""
        return self.cnf_integrator.get_conversion_factor(food_id, measure_id)

    def get_nutrient_id(self, nutrient_name: str) -> Optional[int]:
        """Get nutrient ID using the CNF integrator"""
        return self.cnf_integrator.get_nutrient_id(nutrient_name)

    def get_nutrient_name(self, nutrient_id: int) -> str:
        """Get nutrient name using the CNF integrator"""
        return self.cnf_integrator.get_nutrient_name(nutrient_id)
    
    def get_cpi(self, year: int) -> float:
        base_cpi = 100.0
        annual_inflation_rate = 0.02
        years_since_base = year - 2015
        return base_cpi * (1 + annual_inflation_rate) ** years_since_base

    def __str__(self) -> str:
        return f"DataLoader(data_dir='{self.data_dir}')"

    def __repr__(self) -> str:
        return self.__str__()