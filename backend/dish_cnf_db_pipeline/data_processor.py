import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional, Union
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class CNFDataProcessor:
    """
    Handles all data processing operations for the Canadian Nutrient File.
    Provides CRUD operations with proper error handling and transaction support.
    """
    
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self._backup_data = {}

    def _get_next_unique_id(self, column_name: str, dataframe: pd.DataFrame) -> int:
        """Get the next unique ID for a given column in a dataframe."""
        if pd.api.types.is_integer_dtype(dataframe[column_name]):
            max_id = dataframe[column_name].max()
            return int(max_id + 1 if not pd.isnull(max_id) else 1)
        else:
            raise ValueError(f"Column {column_name} must be of integer type.")

    def get_next_id(self, id_type: str) -> int:
        """
        Get the next available ID for various entity types.
        
        Args:
            id_type: Type of ID to generate (FoodID, NutrientID, etc.)
            
        Returns:
            int: Next available ID
        """
        id_mappings = {
            'FoodID': ('food_name_df', 'FoodID'),
            'NutrientID': ('nutrient_name_df', 'NutrientID'),
            'MeasureID': ('measure_name_df', 'MeasureID'),
            'FoodGroupID': ('food_group_df', 'FoodGroupID'),
            'FoodSourceID': ('food_source_df', 'FoodSourceID'),
            'NutrientSourceID': ('nutrient_source_df', 'NutrientSourceID'),
            'RefuseID': ('refuse_name_df', 'RefuseID'),
            'YieldID': ('yield_name_df', 'YieldID')
        }
        
        if id_type not in id_mappings:
            raise ValueError(f"Unknown ID type: {id_type}")
        
        df_name, column_name = id_mappings[id_type]
        return self._get_next_unique_id(column_name, getattr(self.data_loader, df_name))

    @contextmanager
    def _transaction(self):
        """Context manager for database transactions with rollback capability."""
        try:
            # Create backups of critical dataframes
            self._backup_data = {
                'food_name_df': self.data_loader.food_name_df.copy(),
                'nutrient_amount_df': self.data_loader.nutrient_amount_df.copy(),
                'conversion_factor_df': self.data_loader.conversion_factor_df.copy(),
                'food_source_df': self.data_loader.food_source_df.copy(),
                'nutrient_source_df': self.data_loader.nutrient_source_df.copy(),
                'measure_name_df': self.data_loader.measure_name_df.copy(),
            }
            yield
            # If we get here, commit the transaction
            self._save_all_dataframes()
        except Exception as e:
            # Rollback on any error
            logger.error(f"Transaction failed, rolling back: {str(e)}")
            self._rollback_transaction()
            raise
        finally:
            # Clear backups
            self._backup_data = {}

    def _rollback_transaction(self):
        """Rollback all changes made during the transaction."""
        try:
            for df_name, backup_df in self._backup_data.items():
                setattr(self.data_loader, df_name, backup_df)
            logger.info("Transaction rolled back successfully")
        except Exception as e:
            logger.error(f"Error during rollback: {str(e)}")

    def _prepare_food_entries(self, food_data: Dict) -> tuple:
        """
        Prepare food entries for database insertion.
        
        Args:
            food_data: Dictionary containing food information
            
        Returns:
            tuple: (food_entries, nutrient_entries, conversion_entries)
        """
        food_entries = []
        nutrient_entries = []
        conversion_entries = []
        
        food_id = food_data['FoodID']
        food_code = food_data.get('FoodCode', str(food_id).zfill(8))
        
        # Create food entries for each food group
        for food_group_id in food_data['FoodGroupIDs']:
            food_entry = {
                'FoodID': food_id,
                'FoodCode': food_code,
                'FoodGroupID': food_group_id,
                'FoodSourceID': food_data['FoodSourceID'],
                'FoodDescription': food_data['FoodDescription'],
                'FoodDescriptionF': food_data['FoodDescriptionF'],
                'CountryCode': food_data['CountryCode'],
                'ScientificName': food_data.get('ScientificName', ''),
            }
            food_entries.append(food_entry)
        
        # Create nutrient entries
        for nutrient in food_data['NutrientValues']:
            nutrient_entry = {
                'FoodID': food_id,
                'NutrientID': nutrient['NutrientID'],
                'NutrientValue': nutrient['NutrientValue'],
                'NutrientSourceID': nutrient['NutrientSourceID']
            }
            nutrient_entries.append(nutrient_entry)
        
        # Create conversion factor entries
        for conversion in food_data['ConversionFactors']:
            conversion_entry = {
                'FoodID': food_id,
                'MeasureID': conversion['MeasureID'],
                'ConversionFactorValue': conversion['ConversionFactorValue']
            }
            conversion_entries.append(conversion_entry)
        
        return food_entries, nutrient_entries, conversion_entries

    def add_new_food(self, food_data: Dict, validate: bool = True) -> int:
        """
        Add a single new food item to the database.
        
        Args:
            food_data: Dictionary containing food information
            validate: Whether to validate the input data
            
        Returns:
            int: The FoodID of the newly created food
        """
        try:
            with self._transaction():
                # Assign new FoodID
                food_data['FoodID'] = self.get_next_id('FoodID')
                
                # Validate data if requested
                if validate:
                    self._validate_food_data(food_data)
                
                # Prepare entries
                food_entries, nutrient_entries, conversion_entries = self._prepare_food_entries(food_data)
                
                # Add to dataframes
                self.data_loader.food_name_df = pd.concat([
                    self.data_loader.food_name_df, 
                    pd.DataFrame(food_entries)
                ], ignore_index=True)
                
                self.data_loader.nutrient_amount_df = pd.concat([
                    self.data_loader.nutrient_amount_df, 
                    pd.DataFrame(nutrient_entries)
                ], ignore_index=True)
                
                self.data_loader.conversion_factor_df = pd.concat([
                    self.data_loader.conversion_factor_df, 
                    pd.DataFrame(conversion_entries)
                ], ignore_index=True)
                
                logger.info(f"Successfully added food with ID: {food_data['FoodID']}")
                return food_data['FoodID']
                
        except Exception as e:
            logger.error(f"Error adding new food: {str(e)}")
            raise

    def add_foods_batch(self, foods_data: List[Dict], validate: bool = True) -> List[int]:
        """
        Add multiple foods in a single batch operation.
        
        Args:
            foods_data: List of food dictionaries
            validate: Whether to validate input data
            
        Returns:
            List[int]: List of FoodIDs for the newly created foods
        """
        try:
            with self._transaction():
                all_food_entries = []
                all_nutrient_entries = []
                all_conversion_entries = []
                food_ids = []
                
                for food_data in foods_data:
                    # Assign new FoodID
                    food_data['FoodID'] = self.get_next_id('FoodID')
                    food_ids.append(food_data['FoodID'])
                    
                    # Validate data if requested
                    if validate:
                        self._validate_food_data(food_data)
                    
                    # Prepare entries
                    food_entries, nutrient_entries, conversion_entries = self._prepare_food_entries(food_data)
                    
                    all_food_entries.extend(food_entries)
                    all_nutrient_entries.extend(nutrient_entries)
                    all_conversion_entries.extend(conversion_entries)
                
                # Add all entries to dataframes in batch
                if all_food_entries:
                    self.data_loader.food_name_df = pd.concat([
                        self.data_loader.food_name_df, 
                        pd.DataFrame(all_food_entries)
                    ], ignore_index=True)
                
                if all_nutrient_entries:
                    self.data_loader.nutrient_amount_df = pd.concat([
                        self.data_loader.nutrient_amount_df, 
                        pd.DataFrame(all_nutrient_entries)
                    ], ignore_index=True)
                
                if all_conversion_entries:
                    self.data_loader.conversion_factor_df = pd.concat([
                        self.data_loader.conversion_factor_df, 
                        pd.DataFrame(all_conversion_entries)
                    ], ignore_index=True)
                
                logger.info(f"Successfully added {len(food_ids)} foods in batch")
                return food_ids
                
        except Exception as e:
            logger.error(f"Error adding foods batch: {str(e)}")
            raise

    def update_food(self, food_id: int, updated_data: Dict) -> Dict:
        """
        Update an existing food item.
        
        Args:
            food_id: ID of the food to update
            updated_data: Dictionary containing updated food information
            
        Returns:
            Dict: Updated food details
        """
        try:
            with self._transaction():
                # Check if food exists
                food_exists = not self.data_loader.food_name_df[
                    self.data_loader.food_name_df['FoodID'] == food_id
                ].empty
                
                if not food_exists:
                    raise ValueError(f"No food found with ID: {food_id}")
                
                # Update basic food information
                for key, value in updated_data.items():
                    if key in self.data_loader.food_name_df.columns:
                        self.data_loader.food_name_df.loc[
                            self.data_loader.food_name_df['FoodID'] == food_id, key
                        ] = value
                
                # Update nutrient values if provided
                if 'NutrientValues' in updated_data:
                    # Remove existing nutrient values
                    self.data_loader.nutrient_amount_df = self.data_loader.nutrient_amount_df[
                        self.data_loader.nutrient_amount_df['FoodID'] != food_id
                    ]
                    
                    # Add new nutrient values
                    new_nutrient_values = pd.DataFrame(updated_data['NutrientValues'])
                    if not new_nutrient_values.empty:
                        new_nutrient_values['FoodID'] = food_id
                        self.data_loader.nutrient_amount_df = pd.concat([
                            self.data_loader.nutrient_amount_df, 
                            new_nutrient_values
                        ], ignore_index=True)
                
                # Update conversion factors if provided
                if 'ConversionFactors' in updated_data:
                    # Remove existing conversion factors
                    self.data_loader.conversion_factor_df = self.data_loader.conversion_factor_df[
                        self.data_loader.conversion_factor_df['FoodID'] != food_id
                    ]
                    
                    # Add new conversion factors
                    new_conversion_factors = pd.DataFrame(updated_data['ConversionFactors'])
                    if not new_conversion_factors.empty:
                        new_conversion_factors['FoodID'] = food_id
                        self.data_loader.conversion_factor_df = pd.concat([
                            self.data_loader.conversion_factor_df, 
                            new_conversion_factors
                        ], ignore_index=True)
                
                logger.info(f"Successfully updated food with ID: {food_id}")
                return self.get_food_details(food_id)
                
        except Exception as e:
            logger.error(f"Error updating food: {str(e)}")
            raise

    def delete_food(self, food_id: int) -> bool:
        """
        Delete a food item and all related data.
        
        Args:
            food_id: ID of the food to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            with self._transaction():
                # Check if food exists
                food_exists = not self.data_loader.food_name_df[
                    self.data_loader.food_name_df['FoodID'] == food_id
                ].empty
                
                if not food_exists:
                    raise ValueError(f"No food found with ID: {food_id}")
                
                # Delete from all related tables
                self.data_loader.food_name_df = self.data_loader.food_name_df[
                    self.data_loader.food_name_df['FoodID'] != food_id
                ]
                
                self.data_loader.nutrient_amount_df = self.data_loader.nutrient_amount_df[
                    self.data_loader.nutrient_amount_df['FoodID'] != food_id
                ]
                
                self.data_loader.conversion_factor_df = self.data_loader.conversion_factor_df[
                    self.data_loader.conversion_factor_df['FoodID'] != food_id
                ]
                
                logger.info(f"Successfully deleted food with ID: {food_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting food: {str(e)}")
            raise

    def get_food_details(self, food_id: int) -> Optional[Dict]:
        """
        Get comprehensive details for a specific food.
        
        Args:
            food_id: ID of the food to retrieve
            
        Returns:
            Dict: Food details with all related information
        """
        try:
            # Get basic food information
            food_df = self.data_loader.food_name_df
            food_row = food_df[food_df['FoodID'] == food_id]
            
            if food_row.empty:
                logger.warning(f"No food found with ID: {food_id}")
                return None
            
            # Get the first row (there might be multiple rows for different food groups)
            food = food_row.iloc[0].to_dict()
            
            # Clean up and format basic information
            food['FoodDescription'] = str(food.get('FoodDescription', 'Unknown'))
            food['FoodDescriptionF'] = str(food.get('FoodDescriptionF', 'N/A'))
            food['FoodCode'] = str(food.get('FoodCode', 'Unknown'))
            food['CountryCode'] = str(food.get('CountryCode', 'Unknown'))
            food['ScientificName'] = str(food.get('ScientificName', 'N/A'))
            
            # Get food group information
            food_group_df = self.data_loader.food_group_df
            food_group_row = food_group_df[food_group_df['FoodGroupID'] == food.get('FoodGroupID')]
            food['FoodGroupName'] = str(food_group_row['FoodGroupName'].iloc[0]) if not food_group_row.empty else 'Unknown'
            
            # Get food source information
            food_source_df = self.data_loader.food_source_df
            food_source_row = food_source_df[food_source_df['FoodSourceID'] == food.get('FoodSourceID')]
            food['FoodSourceDescription'] = str(food_source_row['FoodSourceDescription'].iloc[0]) if not food_source_row.empty else 'Unknown'
            
            # Get nutrient values
            nutrient_amount_df = self.data_loader.nutrient_amount_df
            nutrient_values = nutrient_amount_df[nutrient_amount_df['FoodID'] == food_id]
            food['NutrientValues'] = []
            
            for _, nutrient in nutrient_values.iterrows():
                # Get nutrient name and unit
                nutrient_name_df = self.data_loader.nutrient_name_df
                nutrient_name_row = nutrient_name_df[nutrient_name_df['NutrientID'] == nutrient['NutrientID']]
                
                # Get nutrient source
                nutrient_source_df = self.data_loader.nutrient_source_df
                nutrient_source_row = nutrient_source_df[nutrient_source_df['NutrientSourceID'] == nutrient.get('NutrientSourceID', -1)]
                
                nutrient_value = {
                    'NutrientID': int(nutrient['NutrientID']),
                    'NutrientName': str(nutrient_name_row['NutrientName'].iloc[0]) if not nutrient_name_row.empty else 'Unknown',
                    'NutrientValue': float(nutrient['NutrientValue']),
                    'NutrientUnit': str(nutrient_name_row['NutrientUnit'].iloc[0]) if not nutrient_name_row.empty else 'Unknown',
                    'NutrientSourceID': int(nutrient.get('NutrientSourceID', 0)),
                    'NutrientSourceDescription': str(nutrient_source_row['NutrientSourceDescription'].iloc[0]) if not nutrient_source_row.empty else 'Unknown'
                }
                food['NutrientValues'].append(nutrient_value)
            
            # Get conversion factors
            conversion_factor_df = self.data_loader.conversion_factor_df
            conversion_factors = conversion_factor_df[conversion_factor_df['FoodID'] == food_id]
            food['ConversionFactors'] = []
            
            for _, factor in conversion_factors.iterrows():
                # Get measure description
                measure_df = self.data_loader.measure_name_df
                measure_row = measure_df[measure_df['MeasureID'] == factor['MeasureID']]
                
                conversion_factor = {
                    'MeasureID': int(factor['MeasureID']),
                    'MeasureDescription': str(measure_row['MeasureDescription'].iloc[0]) if not measure_row.empty else 'Unknown',
                    'ConversionFactorValue': float(factor['ConversionFactorValue'])
                }
                food['ConversionFactors'].append(conversion_factor)
            
            # Clean up NaN values
            food = self._clean_nan_values(food)
            
            return food
            
        except Exception as e:
            logger.error(f"Error fetching food details: {str(e)}")
            raise

    def _clean_nan_values(self, data: Union[Dict, List, any]) -> Union[Dict, List, any]:
        """Recursively clean NaN values from data structures."""
        if isinstance(data, dict):
            return {k: self._clean_nan_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_nan_values(item) for item in data]
        elif isinstance(data, (int, float)) and pd.isna(data):
            return None
        return data

    def _validate_food_data(self, food_data: Dict) -> bool:
        """
        Validate food data before insertion.
        
        Args:
            food_data: Dictionary containing food information
            
        Returns:
            bool: True if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['FoodDescription', 'FoodDescriptionF', 'FoodGroupIDs', 'FoodSourceID', 'CountryCode']
        
        for field in required_fields:
            if field not in food_data or not food_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate FoodGroupIDs
        if not isinstance(food_data['FoodGroupIDs'], list) or not food_data['FoodGroupIDs']:
            raise ValueError("FoodGroupIDs must be a non-empty list")
        
        # Validate NutrientValues
        if not isinstance(food_data['NutrientValues'], list) or not food_data['NutrientValues']:
            raise ValueError("NutrientValues must be a non-empty list")
        
        # Validate ConversionFactors
        if not isinstance(food_data['ConversionFactors'], list) or not food_data['ConversionFactors']:
            raise ValueError("ConversionFactors must be a non-empty list")
        
        # Validate nutrient values
        for nutrient in food_data['NutrientValues']:
            if not isinstance(nutrient.get('NutrientValue'), (int, float)) or nutrient['NutrientValue'] < 0:
                raise ValueError(f"Invalid nutrient value: {nutrient.get('NutrientValue')}")
        
        return True

    def add_food_source(self, description: str) -> Dict:
        """Add a new food source."""
        try:
            with self._transaction():
                new_source_id = self.get_next_id('FoodSourceID')
                new_source = {
                    'FoodSourceID': new_source_id,
                    'FoodSourceDescription': description
                }
                
                new_source_df = pd.DataFrame([new_source])
                self.data_loader.food_source_df = pd.concat([
                    self.data_loader.food_source_df, 
                    new_source_df
                ], ignore_index=True)
                
                logger.info(f"Successfully added food source: {description}")
                return new_source
                
        except Exception as e:
            logger.error(f"Error adding food source: {str(e)}")
            raise

    def add_nutrient_source(self, description: str) -> Dict:
        """Add a new nutrient source."""
        try:
            with self._transaction():
                new_source_id = self.get_next_id('NutrientSourceID')
                new_source = {
                    'NutrientSourceID': new_source_id,
                    'NutrientSourceDescription': description
                }
                
                new_source_df = pd.DataFrame([new_source])
                self.data_loader.nutrient_source_df = pd.concat([
                    self.data_loader.nutrient_source_df, 
                    new_source_df
                ], ignore_index=True)
                
                logger.info(f"Successfully added nutrient source: {description}")
                return new_source
                
        except Exception as e:
            logger.error(f"Error adding nutrient source: {str(e)}")
            raise

    def add_new_measure(self, description: str) -> Dict:
        """Add a new measure."""
        try:
            with self._transaction():
                new_measure_id = self.get_next_id('MeasureID')
                new_measure = {
                    'MeasureID': new_measure_id,
                    'MeasureDescription': description
                }
                
                new_measure_df = pd.DataFrame([new_measure])
                self.data_loader.measure_name_df = pd.concat([
                    self.data_loader.measure_name_df, 
                    new_measure_df
                ], ignore_index=True)
                
                logger.info(f"Successfully added measure: {description}")
                return new_measure
                
        except Exception as e:
            logger.error(f"Error adding measure: {str(e)}")
            raise

    def _save_all_dataframes(self):
        """Save all dataframes to CSV files."""
        dataframes = [
            ('food_name_df', 'FOOD_NAME.csv'),
            ('nutrient_amount_df', 'NUTRIENT_AMOUNT.csv'),
            ('conversion_factor_df', 'CONVERSION_FACTOR.csv'),
            ('food_source_df', 'FOOD_SOURCE.csv'),
            ('nutrient_source_df', 'NUTRIENT_SOURCE.csv'),
            ('measure_name_df', 'MEASURE_NAME.csv'),
        ]
        
        for df_name, file_name in dataframes:
            try:
                df = getattr(self.data_loader, df_name)
                self.data_loader.save_csv(df, file_name)
            except PermissionError:
                logger.warning(f"Unable to save {file_name}. The file may be open in another program.")
            except Exception as e:
                logger.error(f"Error saving {file_name}: {str(e)}")

    def food_exists(self, food_description: str) -> bool:
        """Check if a food with the given description already exists."""
        return not self.data_loader.food_name_df[
            self.data_loader.food_name_df['FoodDescription'] == food_description
        ].empty
  