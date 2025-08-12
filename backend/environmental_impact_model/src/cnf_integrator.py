import os
import pandas as pd
import logging
from typing import Dict, Any, Optional, List
from chardet import detect
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class CNFIntegrator:
    """
    Singleton class for integrating Canadian Nutrient File data with environmental impact calculations.
    This class provides centralized access to CNF data following the singleton pattern used in FCS calculators.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CNFIntegrator, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.data_dir = None
        self.logger = logging.getLogger(__name__)
        self._dataframes = {}
        self._nutrient_mappings = {}
        self._initialized = False
        
    def initialize(self, data_dir: str):
        """Initialize the integrator with data directory path"""
        if self._initialized:
            self.logger.info("CNF Integrator already initialized")
            return
            
        self.data_dir = data_dir
        self._load_all_dataframes()
        self._create_mappings()
        self._initialized = True
        self.logger.info(f"CNF Integrator initialized with data directory: {data_dir}")
    
    def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding using chardet"""
        try:
            with open(file_path, 'rb') as f:
                result = detect(f.read(10000))
                return result.get('encoding', 'utf-8')
        except Exception as e:
            self.logger.warning(f"Could not detect encoding for {file_path}, using utf-8: {e}")
            return 'utf-8'
    
    def _load_csv(self, file_name: str) -> pd.DataFrame:
        """Load CSV file with proper encoding detection and error handling"""
        file_path = os.path.join(self.data_dir, file_name)
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"CNF data file not found: {file_path}")
        
        if os.path.getsize(file_path) == 0:
            self.logger.warning(f"File is empty: {file_path}")
            return pd.DataFrame()
        
        encoding = self._detect_encoding(file_path)
        
        # Define dtypes for columns that might have mixed types
        dtypes = {
            'FoodID': 'Int64',
            'FoodCode': 'str',
            'FoodGroupID': 'Int64',
            'FoodSourceID': 'Int64',
            'NutrientID': 'Int64',
            'NutrientSourceID': 'Int64',
            'MeasureID': 'Int64',
            'RefuseID': 'Int64',
            'YieldID': 'Int64'
        }
        
        try:
            # Read CSV with low_memory=False and specified dtypes
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False, dtype=dtypes)
            
            # Convert date columns to datetime
            date_columns = [col for col in df.columns if 'Date' in col]
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            self.logger.info(f"Loaded {len(df)} rows from {file_name}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading {file_name}: {str(e)}")
            raise
    
    def _load_all_dataframes(self):
        """Load all required CNF dataframes"""
        csv_files = [
            'FOOD_NAME', 'NUTRIENT_AMOUNT', 'CONVERSION_FACTOR', 'FOOD_GROUP',
            'FOOD_SOURCE', 'NUTRIENT_NAME', 'NUTRIENT_SOURCE', 'MEASURE_NAME',
            'REFUSE_AMOUNT', 'YIELD_AMOUNT', 'REFUSE_NAME', 'YIELD_NAME'
        ]
        
        for file in csv_files:
            try:
                df = self._load_csv(f"{file}.csv")
                self._dataframes[file.lower()] = df
                self.logger.debug(f"Loaded dataframe for {file}")
            except FileNotFoundError:
                self.logger.warning(f"Optional file {file}.csv not found, skipping")
                self._dataframes[file.lower()] = pd.DataFrame()
            except Exception as e:
                self.logger.error(f"Failed to load {file}.csv: {e}")
                self._dataframes[file.lower()] = pd.DataFrame()
    
    def _create_mappings(self):
        """Create nutrient and food mappings for efficient lookups"""
        try:
            # Nutrient mappings
            if not self._dataframes['nutrient_name'].empty:
                nutrient_df = self._dataframes['nutrient_name']
                if 'NutrientID' in nutrient_df.columns and 'NutrientName' in nutrient_df.columns:
                    self._nutrient_mappings['id_to_name'] = dict(
                        zip(nutrient_df['NutrientID'], nutrient_df['NutrientName'])
                    )
                    self._nutrient_mappings['name_to_id'] = dict(
                        zip(nutrient_df['NutrientName'], nutrient_df['NutrientID'])
                    )
            
            # Food group mappings
            if not self._dataframes['food_group'].empty:
                food_group_df = self._dataframes['food_group']
                if 'FoodGroupID' in food_group_df.columns and 'FoodGroupName' in food_group_df.columns:
                    self._nutrient_mappings['group_id_to_name'] = dict(
                        zip(food_group_df['FoodGroupID'], food_group_df['FoodGroupName'])
                    )
                    
        except Exception as e:
            self.logger.error(f"Error creating mappings: {e}")
    
    def get_food_data(self, food_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive food data for a given food ID"""
        if not self._initialized:
            raise RuntimeError("CNF Integrator not initialized. Call initialize() first.")
        
        try:
            # Get food info
            food_name_df = self._dataframes.get('food_name', pd.DataFrame())
            if food_name_df.empty:
                return None
                
            food_info = food_name_df[food_name_df['FoodID'] == food_id]
            if food_info.empty:
                return None
                
            food_info = food_info.iloc[0].to_dict()
            
            # Get nutrient data
            nutrient_amount_df = self._dataframes.get('nutrient_amount', pd.DataFrame())
            nutrients = []
            if not nutrient_amount_df.empty:
                nutrient_data = nutrient_amount_df[nutrient_amount_df['FoodID'] == food_id]
                nutrients = nutrient_data.to_dict('records')
            
            # Get food group info
            food_group_df = self._dataframes.get('food_group', pd.DataFrame())
            food_group = {}
            if not food_group_df.empty and 'FoodGroupID' in food_info:
                group_info = food_group_df[food_group_df['FoodGroupID'] == food_info['FoodGroupID']]
                if not group_info.empty:
                    food_group = group_info.iloc[0].to_dict()
            
            # Get conversion factors
            conversion_factor_df = self._dataframes.get('conversion_factor', pd.DataFrame())
            conversion_factors = []
            if not conversion_factor_df.empty:
                conv_data = conversion_factor_df[conversion_factor_df['FoodID'] == food_id]
                conversion_factors = conv_data.to_dict('records')
            
            return {
                'food_info': food_info,
                'nutrients': nutrients,
                'food_group': food_group,
                'conversion_factors': conversion_factors
            }
            
        except Exception as e:
            self.logger.error(f"Error getting food data for ID {food_id}: {e}")
            return None
    
    def get_nutrient_amount(self, food_id: int, nutrient_name: str) -> float:
        """Get nutrient amount for a specific food and nutrient"""
        nutrient_id = self.get_nutrient_id(nutrient_name)
        if nutrient_id is None:
            return 0.0
        
        nutrient_amount_df = self._dataframes.get('nutrient_amount', pd.DataFrame())
        if nutrient_amount_df.empty:
            return 0.0
        
        nutrient_data = nutrient_amount_df[
            (nutrient_amount_df['FoodID'] == food_id) & 
            (nutrient_amount_df['NutrientID'] == nutrient_id)
        ]
        
        if nutrient_data.empty:
            return 0.0
        
        return float(nutrient_data.iloc[0]['NutrientValue'])
    
    def get_nutrient_id(self, nutrient_name: str) -> Optional[int]:
        """Get nutrient ID from nutrient name"""
        return self._nutrient_mappings.get('name_to_id', {}).get(nutrient_name.upper())
    
    def get_nutrient_name(self, nutrient_id: int) -> str:
        """Get nutrient name from nutrient ID"""
        return self._nutrient_mappings.get('id_to_name', {}).get(nutrient_id, "Unknown")
    
    def get_food_group_name(self, food_group_id: int) -> str:
        """Get food group name from food group ID"""
        return self._nutrient_mappings.get('group_id_to_name', {}).get(food_group_id, "Unknown")
    
    def get_conversion_factor(self, food_id: int, measure_id: int) -> float:
        """Get conversion factor for a specific food and measure"""
        conversion_factor_df = self._dataframes.get('conversion_factor', pd.DataFrame())
        if conversion_factor_df.empty:
            return 1.0
        
        conversion_data = conversion_factor_df[
            (conversion_factor_df['FoodID'] == food_id) & 
            (conversion_factor_df['MeasureID'] == measure_id)
        ]
        
        if conversion_data.empty:
            return 1.0
        
        return float(conversion_data.iloc[0]['ConversionFactorValue'])
    
    def search_foods(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for foods using the query string"""
        food_name_df = self._dataframes.get('food_name', pd.DataFrame())
        if food_name_df.empty or 'FoodDescription' not in food_name_df.columns:
            return []
        
        # Simple text search - can be enhanced with fuzzy matching
        mask = food_name_df['FoodDescription'].str.contains(query, case=False, na=False)
        results = food_name_df[mask].head(limit)
        
        return results.to_dict('records')
    
    def get_environmental_impact_factors(self, food_id: int) -> Dict[str, float]:
        """
        Get environmental impact factors for a specific food.
        This method provides updated impact factors based on current LCA best practices.
        """
        food_data = self.get_food_data(food_id)
        if not food_data:
            return {}
        
        food_group_name = food_data.get('food_group', {}).get('FoodGroupName', 'Unknown')
        
        # Updated impact factors based on ReCiPe 2016 methodology and recent LCA studies
        # Values are per 100g of food product
        impact_factors_by_group = {
            'Dairy and Egg Products': {
                'Global warming': 4.2,  # kg CO2 eq
                'Land use': 9.1,  # m2a crop eq
                'Water consumption': 628,  # L
                'Freshwater eutrophication': 0.0032,  # kg P eq
                'Marine eutrophication': 0.041,  # kg N eq
                'Terrestrial acidification': 0.048,  # kg SO2 eq
                'Fine particulate matter formation': 0.024,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.78,  # kg oil eq
                'Mineral resource scarcity': 0.0021,  # kg Cu eq
            },
            'Beef Products': {
                'Global warming': 99.5,  # kg CO2 eq
                'Land use': 164,  # m2a crop eq
                'Water consumption': 1847,  # L
                'Freshwater eutrophication': 0.0089,  # kg P eq
                'Marine eutrophication': 0.135,  # kg N eq
                'Terrestrial acidification': 0.124,  # kg SO2 eq
                'Fine particulate matter formation': 0.067,  # kg PM2.5 eq
                'Fossil resource scarcity': 2.8,  # kg oil eq
                'Mineral resource scarcity': 0.0041,  # kg Cu eq
            },
            'Pork Products': {
                'Global warming': 12.1,  # kg CO2 eq
                'Land use': 17.4,  # m2a crop eq
                'Water consumption': 1796,  # L
                'Freshwater eutrophication': 0.0056,  # kg P eq
                'Marine eutrophication': 0.089,  # kg N eq
                'Terrestrial acidification': 0.087,  # kg SO2 eq
                'Fine particulate matter formation': 0.042,  # kg PM2.5 eq
                'Fossil resource scarcity': 1.2,  # kg oil eq
                'Mineral resource scarcity': 0.0028,  # kg Cu eq
            },
            'Poultry Products': {
                'Global warming': 9.9,  # kg CO2 eq
                'Land use': 8.9,  # m2a crop eq
                'Water consumption': 660,  # L
                'Freshwater eutrophication': 0.0047,  # kg P eq
                'Marine eutrophication': 0.068,  # kg N eq
                'Terrestrial acidification': 0.061,  # kg SO2 eq
                'Fine particulate matter formation': 0.032,  # kg PM2.5 eq
                'Fossil resource scarcity': 1.1,  # kg oil eq
                'Mineral resource scarcity': 0.0024,  # kg Cu eq
            },
            'Finfish and Shellfish Products': {
                'Global warming': 13.6,  # kg CO2 eq
                'Land use': 0.2,  # m2a crop eq
                'Water consumption': 3.5,  # L
                'Freshwater eutrophication': 0.0031,  # kg P eq
                'Marine eutrophication': 0.024,  # kg N eq
                'Terrestrial acidification': 0.034,  # kg SO2 eq
                'Fine particulate matter formation': 0.019,  # kg PM2.5 eq
                'Fossil resource scarcity': 3.2,  # kg oil eq
                'Mineral resource scarcity': 0.0018,  # kg Cu eq
            },
            'Vegetables and Vegetable Products': {
                'Global warming': 0.42,  # kg CO2 eq
                'Land use': 0.51,  # m2a crop eq
                'Water consumption': 322,  # L
                'Freshwater eutrophication': 0.00041,  # kg P eq
                'Marine eutrophication': 0.0049,  # kg N eq
                'Terrestrial acidification': 0.0032,  # kg SO2 eq
                'Fine particulate matter formation': 0.0018,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.12,  # kg oil eq
                'Mineral resource scarcity': 0.00024,  # kg Cu eq
            },
            'Fruits and fruit juices': {
                'Global warming': 0.89,  # kg CO2 eq
                'Land use': 1.15,  # m2a crop eq
                'Water consumption': 721,  # L
                'Freshwater eutrophication': 0.00062,  # kg P eq
                'Marine eutrophication': 0.0071,  # kg N eq
                'Terrestrial acidification': 0.0041,  # kg SO2 eq
                'Fine particulate matter formation': 0.0024,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.21,  # kg oil eq
                'Mineral resource scarcity': 0.00031,  # kg Cu eq
            },
            'Cereals, Grains and Pasta': {
                'Global warming': 2.5,  # kg CO2 eq
                'Land use': 1.6,  # m2a crop eq
                'Water consumption': 1644,  # L
                'Freshwater eutrophication': 0.0012,  # kg P eq
                'Marine eutrophication': 0.014,  # kg N eq
                'Terrestrial acidification': 0.0089,  # kg SO2 eq
                'Fine particulate matter formation': 0.0045,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.42,  # kg oil eq
                'Mineral resource scarcity': 0.00067,  # kg Cu eq
            },
            'Legumes and Legume Products': {
                'Global warming': 0.43,  # kg CO2 eq
                'Land use': 2.53,  # m2a crop eq
                'Water consumption': 501,  # L
                'Freshwater eutrophication': 0.00089,  # kg P eq
                'Marine eutrophication': 0.0021,  # kg N eq
                'Terrestrial acidification': 0.0034,  # kg SO2 eq
                'Fine particulate matter formation': 0.0021,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.18,  # kg oil eq
                'Mineral resource scarcity': 0.00041,  # kg Cu eq
            },
            'Nuts and Seeds': {
                'Global warming': 0.26,  # kg CO2 eq
                'Land use': 7.29,  # m2a crop eq
                'Water consumption': 9063,  # L
                'Freshwater eutrophication': 0.00021,  # kg P eq
                'Marine eutrophication': 0.0012,  # kg N eq
                'Terrestrial acidification': 0.0016,  # kg SO2 eq
                'Fine particulate matter formation': 0.00098,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.089,  # kg oil eq
                'Mineral resource scarcity': 0.00018,  # kg Cu eq
            }
        }
        
        # Default factors for unknown food groups
        default_factors = {
            'Global warming': 2.1,  # kg CO2 eq
            'Land use': 2.5,  # m2a crop eq
            'Water consumption': 500,  # L
            'Freshwater eutrophication': 0.001,  # kg P eq
            'Marine eutrophication': 0.01,  # kg N eq
            'Terrestrial acidification': 0.01,  # kg SO2 eq
            'Fine particulate matter formation': 0.005,  # kg PM2.5 eq
            'Fossil resource scarcity': 0.5,  # kg oil eq
            'Mineral resource scarcity': 0.001,  # kg Cu eq
        }
        
        return impact_factors_by_group.get(food_group_name, default_factors)
    
    def is_initialized(self) -> bool:
        """Check if the integrator has been initialized"""
        return self._initialized
    
    def get_dataframe(self, df_name: str) -> pd.DataFrame:
        """Get a specific dataframe by name"""
        return self._dataframes.get(df_name.lower(), pd.DataFrame())
    
    def __str__(self) -> str:
        return f"CNFIntegrator(initialized={self._initialized}, data_dir='{self.data_dir}')"
    
    def __repr__(self) -> str:
        return self.__str__()

# Global singleton instance
_cnf_integrator = None

def get_cnf_integrator() -> CNFIntegrator:
    """Get the global CNF integrator instance"""
    global _cnf_integrator
    if _cnf_integrator is None:
        _cnf_integrator = CNFIntegrator()
    return _cnf_integrator