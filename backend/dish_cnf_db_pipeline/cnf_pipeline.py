import logging
from .data_loader import CNFDataLoader
from .data_processor import CNFDataProcessor
import pandas as pd
from functools import lru_cache
from datetime import datetime
from typing import List, Dict, Optional, Union

logger = logging.getLogger(__name__)

class CNFDataPipeline:
    """
    Main pipeline for Canadian Nutrient File data operations.
    Provides a clean interface for food data exploration and management.
    """
    
    def __init__(self, data_dir: str):
        self.data_loader = CNFDataLoader(data_dir)
        self.data_processor = CNFDataProcessor(self.data_loader)
        self._initialize_search_index()

    def _initialize_search_index(self):
        """Initialize search index for better performance."""
        try:
            # Create lowercase search index for food descriptions
            self.data_loader.food_name_df['search_index'] = (
                self.data_loader.food_name_df['FoodDescription'].str.lower() + ' ' +
                self.data_loader.food_name_df['FoodDescriptionF'].str.lower().fillna('')
            )
        except Exception as e:
            logger.warning(f"Failed to initialize search index: {e}")

    # =============================================================================
    # Food Management Operations
    # =============================================================================
    
    def add_food(self, food_data: Dict, validate: bool = True) -> int:
        """
        Add a single food item to the database.
        
        Args:
            food_data: Dictionary containing food information
            validate: Whether to validate the input data
            
        Returns:
            int: The FoodID of the newly created food
        """
        try:
            return self.data_processor.add_new_food(food_data, validate)
        except Exception as e:
            logger.error(f"Error adding food: {str(e)}")
            raise

    def add_foods_batch(self, foods_data: List[Dict], validate: bool = True) -> List[int]:
        """
        Add multiple foods in a single batch operation.
        
        Args:
            foods_data: List of food dictionaries
            validate: Whether to validate the input data
            
        Returns:
            List[int]: List of FoodIDs for the newly created foods
        """
        try:
            return self.data_processor.add_foods_batch(foods_data, validate)
        except Exception as e:
            logger.error(f"Error adding foods batch: {str(e)}")
            raise

    def update_food(self, food_id: int, updated_data: Dict) -> Dict:
        """Update an existing food item."""
        try:
            return self.data_processor.update_food(food_id, updated_data)
        except Exception as e:
            logger.error(f"Error updating food {food_id}: {str(e)}")
            raise

    def delete_food(self, food_id: int) -> bool:
        """Delete a food item and all related data."""
        try:
            return self.data_processor.delete_food(food_id)
        except Exception as e:
            logger.error(f"Error deleting food {food_id}: {str(e)}")
            raise

    def get_food_details(self, food_id: int) -> Optional[Dict]:
        """Get comprehensive details for a specific food."""
        try:
            return self.data_processor.get_food_details(food_id)
        except Exception as e:
            logger.error(f"Error fetching food details for {food_id}: {str(e)}")
            raise

    # =============================================================================
    # Search and Exploration Operations
    # =============================================================================

    @lru_cache(maxsize=1000)
    def search_foods(self, query: str, limit: int = 50, offset: int = 0) -> Dict:
        """
        Advanced food search with pagination and relevance scoring.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            if not query or len(query.strip()) < 2:
                return {"results": [], "total": 0, "query": query}
            
            query_lower = query.lower().strip()
            
            # Search in food descriptions
            mask = self.data_loader.food_name_df['search_index'].str.contains(
                query_lower, case=False, na=False
            )
            
            results_df = self.data_loader.food_name_df[mask].copy()
            
            # Add relevance scoring
            results_df['relevance'] = results_df['FoodDescription'].str.lower().apply(
                lambda x: self._calculate_relevance(x, query_lower)
            )
            
            # Sort by relevance and apply pagination
            results_df = results_df.sort_values('relevance', ascending=False)
            total_results = len(results_df)
            
            paginated_results = results_df.iloc[offset:offset + limit]
            
            # Format results
            formatted_results = []
            for _, row in paginated_results.iterrows():
                formatted_results.append({
                    'FoodID': int(row['FoodID']),
                    'FoodCode': str(row['FoodCode']),
                    'FoodDescription': str(row['FoodDescription']),
                    'FoodDescriptionF': str(row.get('FoodDescriptionF', '')),
                    'FoodGroupID': int(row['FoodGroupID']),
                    'relevance': float(row['relevance'])
                })
            
            return {
                "results": formatted_results,
                "total": total_results,
                "query": query,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_results
            }
            
        except Exception as e:
            logger.error(f"Error searching foods: {str(e)}")
            raise

    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score for search results."""
        if query in text:
            if text.startswith(query):
                return 1.0  # Exact match at start
            elif query in text.split():
                return 0.8  # Word match
            else:
                return 0.6  # Substring match
        return 0.1  # Fuzzy match

    def search_foods_by_nutrient(self, nutrient_id: int, min_value: float = None, 
                                max_value: float = None, limit: int = 50) -> List[Dict]:
        """
        Search foods by nutrient content.
        
        Args:
            nutrient_id: The nutrient ID to search for
            min_value: Minimum nutrient value (optional)
            max_value: Maximum nutrient value (optional)
            limit: Maximum number of results
            
        Returns:
            List of foods matching the nutrient criteria
        """
        try:
            # Get nutrient data
            nutrient_df = self.data_loader.nutrient_amount_df[
                self.data_loader.nutrient_amount_df['NutrientID'] == nutrient_id
            ]
            
            # Apply value filters
            if min_value is not None:
                nutrient_df = nutrient_df[nutrient_df['NutrientValue'] >= min_value]
            if max_value is not None:
                nutrient_df = nutrient_df[nutrient_df['NutrientValue'] <= max_value]
            
            # Sort by nutrient value (descending)
            nutrient_df = nutrient_df.sort_values('NutrientValue', ascending=False)
            
            # Get food details
            food_ids = nutrient_df['FoodID'].head(limit).tolist()
            foods = []
            
            for food_id in food_ids:
                food_details = self.get_food_details(food_id)
                if food_details:
                    # Add the specific nutrient value to the response
                    nutrient_value = nutrient_df[nutrient_df['FoodID'] == food_id]['NutrientValue'].iloc[0]
                    food_details['queried_nutrient_value'] = float(nutrient_value)
                    foods.append(food_details)
            
            return foods
            
        except Exception as e:
            logger.error(f"Error searching foods by nutrient: {str(e)}")
            raise

    def get_foods_by_group(self, food_group_id: int, limit: int = 100) -> List[Dict]:
        """Get all foods in a specific food group."""
        try:
            foods_in_group = self.data_loader.food_name_df[
                self.data_loader.food_name_df['FoodGroupID'] == food_group_id
            ].head(limit)
            
            return foods_in_group[['FoodID', 'FoodCode', 'FoodDescription', 'FoodDescriptionF']].to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting foods by group: {str(e)}")
            raise

    def compare_foods(self, food_ids: List[int], nutrient_ids: List[int] = None) -> Dict:
        """
        Compare nutritional content of multiple foods.
        
        Args:
            food_ids: List of food IDs to compare
            nutrient_ids: List of specific nutrients to compare (optional)
            
        Returns:
            Dictionary containing comparison data
        """
        try:
            if len(food_ids) > 10:
                raise ValueError("Cannot compare more than 10 foods at once")
            
            comparison_data = {
                'foods': [],
                'nutrients': {},
                'comparison_date': datetime.now().isoformat()
            }
            
            # Get food details
            for food_id in food_ids:
                food_details = self.get_food_details(food_id)
                if food_details:
                    comparison_data['foods'].append({
                        'FoodID': food_id,
                        'FoodDescription': food_details['FoodDescription'],
                        'FoodGroup': food_details.get('FoodGroupName', 'Unknown')
                    })
            
            # Get nutrient data for comparison
            if nutrient_ids:
                target_nutrients = nutrient_ids
            else:
                # Get comprehensive nutrients if none specified
                target_nutrients = [
                    # Energy
                    208,  # ENERGY (KILOCALORIES)
                    268,  # ENERGY (KILOJOULES)
                    
                    # Macronutrients
                    203,  # PROTEIN
                    204,  # FAT (TOTAL LIPIDS)
                    205,  # CARBOHYDRATE, TOTAL (BY DIFFERENCE)
                    291,  # FIBRE, TOTAL DIETARY
                    
                    # Minerals
                    301,  # CALCIUM
                    303,  # IRON
                    304,  # MAGNESIUM
                    305,  # PHOSPHORUS
                    306,  # POTASSIUM
                    307,  # SODIUM
                    309,  # ZINC
                    
                    # Vitamins
                    319,  # RETINOL
                    320,  # RETINOL ACTIVITY EQUIVALENTS (Vitamin A)
                    321,  # BETA CAROTENE
                    323,  # ALPHA-TOCOPHEROL (Vitamin E)
                    324,  # VITAMIN D (INTERNATIONAL UNITS)
                    401,  # VITAMIN C
                    404,  # THIAMIN (Vitamin B1)
                    405,  # RIBOFLAVIN (Vitamin B2)
                    406,  # NIACIN (Vitamin B3)
                    417,  # TOTAL FOLACIN (Folate)
                    418,  # VITAMIN B-12
                    430,  # VITAMIN K
                    
                    # Fatty Acids
                    606,  # FATTY ACIDS, SATURATED, TOTAL
                    645,  # FATTY ACIDS, MONOUNSATURATED, TOTAL
                    646,  # FATTY ACIDS, POLYUNSATURATED, TOTAL
                    605,  # FATTY ACIDS, TRANS, TOTAL
                    601,  # CHOLESTEROL
                ]
            
            for nutrient_id in target_nutrients:
                nutrient_data = self.data_loader.nutrient_amount_df[
                    (self.data_loader.nutrient_amount_df['NutrientID'] == nutrient_id) &
                    (self.data_loader.nutrient_amount_df['FoodID'].isin(food_ids))
                ]
                
                if not nutrient_data.empty:
                    # Get nutrient name
                    nutrient_name_row = self.data_loader.nutrient_name_df[
                        self.data_loader.nutrient_name_df['NutrientID'] == nutrient_id
                    ]
                    nutrient_name = nutrient_name_row['NutrientName'].iloc[0] if not nutrient_name_row.empty else f"Nutrient {nutrient_id}"
                    nutrient_unit = nutrient_name_row['NutrientUnit'].iloc[0] if not nutrient_name_row.empty else "unit"
                    
                    comparison_data['nutrients'][nutrient_name] = {
                        'nutrient_id': nutrient_id,
                        'unit': nutrient_unit,
                        'values': {}
                    }
                    
                    for _, row in nutrient_data.iterrows():
                        food_id = row['FoodID']
                        food_name = next((f['FoodDescription'] for f in comparison_data['foods'] if f['FoodID'] == food_id), f"Food {food_id}")
                        comparison_data['nutrients'][nutrient_name]['values'][food_name] = float(row['NutrientValue'])
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"Error comparing foods: {str(e)}")
            raise

    # =============================================================================
    # Reference Data Operations
    # =============================================================================

    def add_food_source(self, description: str) -> Dict:
        """Add a new food source."""
        return self.data_processor.add_food_source(description)

    def add_nutrient_source(self, description: str) -> Dict:
        """Add a new nutrient source."""
        return self.data_processor.add_nutrient_source(description)

    def add_measure(self, description: str) -> Dict:
        """Add a new measure."""
        return self.data_processor.add_new_measure(description)

    # =============================================================================
    # Data Quality and Integrity
    # =============================================================================

    def check_data_integrity(self) -> Dict:
        """
        Comprehensive data integrity check.
        
        Returns:
            Dictionary with integrity check results
        """
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'checks': {},
                'overall_status': 'passed'
            }
            
            # Check for orphaned records
            food_ids = set(self.data_loader.food_name_df['FoodID'])
            nutrient_food_ids = set(self.data_loader.nutrient_amount_df['FoodID'])
            conversion_food_ids = set(self.data_loader.conversion_factor_df['FoodID'])

            orphaned_nutrients = nutrient_food_ids - food_ids
            orphaned_conversions = conversion_food_ids - food_ids
            foods_without_nutrients = food_ids - nutrient_food_ids
            foods_without_conversions = food_ids - conversion_food_ids

            results['checks']['orphaned_nutrient_records'] = {
                'count': len(orphaned_nutrients),
                'status': 'passed' if len(orphaned_nutrients) == 0 else 'warning',
                'details': list(orphaned_nutrients) if orphaned_nutrients else []
            }

            results['checks']['orphaned_conversion_records'] = {
                'count': len(orphaned_conversions),
                'status': 'passed' if len(orphaned_conversions) == 0 else 'warning',
                'details': list(orphaned_conversions) if orphaned_conversions else []
            }

            results['checks']['foods_without_nutrients'] = {
                'count': len(foods_without_nutrients),
                'status': 'passed' if len(foods_without_nutrients) == 0 else 'warning',
                'details': list(foods_without_nutrients) if foods_without_nutrients else []
            }

            results['checks']['foods_without_conversions'] = {
                'count': len(foods_without_conversions),
                'status': 'passed' if len(foods_without_conversions) == 0 else 'warning',
                'details': list(foods_without_conversions) if foods_without_conversions else []
            }

            # Check for duplicate food descriptions
            duplicate_descriptions = self.data_loader.food_name_df[
                self.data_loader.food_name_df.duplicated(subset=['FoodDescription'], keep=False)
            ]
            
            results['checks']['duplicate_food_descriptions'] = {
                'count': len(duplicate_descriptions),
                'status': 'passed' if len(duplicate_descriptions) == 0 else 'warning',
                'details': duplicate_descriptions[['FoodID', 'FoodDescription']].to_dict('records') if not duplicate_descriptions.empty else []
            }

            # Set overall status
            if any(check['status'] == 'failed' for check in results['checks'].values()):
                results['overall_status'] = 'failed'
            elif any(check['status'] == 'warning' for check in results['checks'].values()):
                results['overall_status'] = 'warning'

            return results
            
        except Exception as e:
            logger.error(f"Error checking data integrity: {str(e)}")
            raise

    def get_database_statistics(self) -> Dict:
        """Get comprehensive database statistics."""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'food_count': len(self.data_loader.food_name_df),
                'nutrient_records': len(self.data_loader.nutrient_amount_df),
                'conversion_records': len(self.data_loader.conversion_factor_df),
                'food_groups': len(self.data_loader.food_group_df),
                'food_sources': len(self.data_loader.food_source_df),
                'nutrient_types': len(self.data_loader.nutrient_name_df),
                'nutrient_sources': len(self.data_loader.nutrient_source_df),
                'measures': len(self.data_loader.measure_name_df),
                'foods_by_group': {},
                'top_nutrients': {}
            }
            
            # Foods by group
            foods_by_group = self.data_loader.food_name_df.groupby('FoodGroupID').size()
            for group_id, count in foods_by_group.items():
                group_name = self.data_loader.food_group_df[
                    self.data_loader.food_group_df['FoodGroupID'] == group_id
                ]['FoodGroupName'].iloc[0] if not self.data_loader.food_group_df[
                    self.data_loader.food_group_df['FoodGroupID'] == group_id
                ].empty else f"Group {group_id}"
                stats['foods_by_group'][group_name] = int(count)
            
            # Top nutrients by frequency
            nutrient_counts = self.data_loader.nutrient_amount_df.groupby('NutrientID').size().sort_values(ascending=False)
            for nutrient_id, count in nutrient_counts.head(10).items():
                nutrient_name = self.data_loader.nutrient_name_df[
                    self.data_loader.nutrient_name_df['NutrientID'] == nutrient_id
                ]['NutrientName'].iloc[0] if not self.data_loader.nutrient_name_df[
                    self.data_loader.nutrient_name_df['NutrientID'] == nutrient_id
                ].empty else f"Nutrient {nutrient_id}"
                stats['top_nutrients'][nutrient_name] = int(count)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            raise