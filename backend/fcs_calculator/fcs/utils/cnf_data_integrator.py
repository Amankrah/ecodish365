"""
Enhanced CNF Data Integration utilizing existing CNFDataPipeline
Avoids redundancy by reusing established data loading patterns
"""

import sys
import os
import pandas as pd
from typing import List, Dict, Optional
import logging

# Add the parent directories to path to import CNFDataPipeline
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
api_dir = os.path.join(backend_dir, 'api')
sys.path.append(api_dir)
from api.cnf_data_pipeline import CNFDataPipeline

from fcs.models.food_item import FoodItem

# Global pipeline instance to avoid expensive reinitialization
_cnf_pipeline_instance = None

def get_shared_cnf_pipeline(cnf_data_dir: str) -> CNFDataPipeline:
    """Get shared CNF pipeline instance to avoid expensive reinitialization"""
    global _cnf_pipeline_instance
    if _cnf_pipeline_instance is None:
        _cnf_pipeline_instance = CNFDataPipeline(cnf_data_dir)
    return _cnf_pipeline_instance

logger = logging.getLogger(__name__)

class EnhancedCNFDataIntegrator:
    """
    Enhanced integration layer that reuses existing CNFDataPipeline infrastructure
    while providing FCS-specific nutrient extraction and mapping
    """
    
    def __init__(self, cnf_data_dir: str):
        """Initialize with existing CNF data pipeline"""
        self.cnf_pipeline = get_shared_cnf_pipeline(cnf_data_dir)
        self.nutrient_mapping = self._create_nutrient_mapping()
    
    def _create_nutrient_mapping(self) -> Dict[str, str]:
        """
        Create mapping from CNF nutrient names to FCS attribute names
        Reuses CNF normalization patterns but maps to FCS 2.0 structure
        """
        return {
            # Vitamins (Domain 2) - Exact CNF nutrient names from NUTRIENT_NAME.csv
            'RETINOL ACTIVITY EQUIVALENTS': 'vitamin_a',
            'THIAMIN': 'vitamin_b1', 
            'RIBOFLAVIN': 'vitamin_b2',
            'NIACIN (NICOTINIC ACID) PREFORMED': 'vitamin_b3',
            'TOTAL NIACIN EQUIVALENT': 'vitamin_b3',
            'VITAMIN B-6': 'vitamin_b6',
            'TOTAL FOLACIN': 'vitamin_b9',
            'NATURALLY OCCURRING FOLATE': 'vitamin_b9',
            'DIETARY FOLATE EQUIVALENTS': 'vitamin_b9',
            'VITAMIN B-12': 'vitamin_b12',
            'VITAMIN C': 'vitamin_c',
            'VITAMIN D (D2 + D3)': 'vitamin_d',
            'VITAMIN D (INTERNATIONAL UNITS)': 'vitamin_d',
            'ALPHA-TOCOPHEROL': 'vitamin_e',
            'VITAMIN K': 'vitamin_k',
            
            # Minerals (Domain 3) - Exact CNF names
            'CALCIUM': 'calcium',
            'PHOSPHORUS': 'phosphorus', 
            'MAGNESIUM': 'magnesium',
            'IRON': 'iron',
            'ZINC': 'zinc',
            'COPPER': 'copper',
            'SELENIUM': 'selenium',
            'SODIUM': 'sodium',
            'POTASSIUM': 'potassium',
            'MANGANESE': 'manganese',
            
            # Macronutrients and fiber (Domain 8) - Exact CNF names
            'FIBRE, TOTAL DIETARY': 'fiber',
            'PROTEIN': 'protein',
            
            # Critical missing macronutrients for ratios and scoring
            'FAT (TOTAL LIPIDS)': 'total_fat',  # CRITICAL - needed for ratios
            'CARBOHYDRATE, TOTAL (BY DIFFERENCE)': 'total_carbohydrate',  # CRITICAL
            'SUGARS, TOTAL': 'total_sugars',  # CRITICAL - for added sugar penalties
            'FATTY ACIDS, SATURATED, TOTAL': 'saturated_fat',  # CRITICAL - for ratios
            'FATTY ACIDS, MONOUNSATURATED, TOTAL': 'monounsaturated_fat',  # For ratios
            'FATTY ACIDS, POLYUNSATURATED, TOTAL': 'polyunsaturated_fat',  # For ratios
            
            # Lipids (Domain 7) - Exact CNF fatty acid names
            'CHOLESTEROL': 'cholesterol',
            # Omega-3 fatty acids (CRITICAL for salmon scoring)
            'FATTY ACIDS, POLYUNSATURATED, 22:6 N-3, DOCOSAHEXAENOIC (DHA)': 'epa_dha',
            'FATTY ACIDS, POLYUNSATURATED, 20:5 N-3, EICOSAPENTAENOIC (EPA)': 'epa_dha',
            'FATTY ACIDS, POLYUNSATURATED, 18:3UNDIFFERENTIATED, LINOLENIC, OCTADECATRIENOIC': 'alpha_linolenic_acid',
            'FATTY ACIDS, POLYUNSATURATED, 18:3 C,C,C N-3  LINOLENIC, OCTADECATRIENOIC': 'alpha_linolenic_acid',
            # Other important fatty acids - exact CNF names
            'FATTY ACIDS, POLYUNSATURATED, 18:2UNDIFFERENTIATED, LINOLEIC, OCTADECADIENOIC': 'linoleic_acid',
            'FATTY ACIDS, MONOUNSATURATED, 18:1UNDIFFERENTIATED, OCTADECENOIC': 'oleic_acid',
            'FATTY ACIDS, TRANS, TOTAL': 'transfat',
            
            # Phytochemicals (Domain 9) - Available in CNF
            'BETA CAROTENE': 'total_carotenoids',
            'ALPHA CAROTENE': 'total_carotenoids', 
            'BETA CRYPTOXANTHIN': 'total_carotenoids',
            'LYCOPENE': 'total_carotenoids',
            'LUTEIN AND ZEAXANTHIN': 'total_carotenoids',
            
            # Additional beneficial compounds
            'CHOLINE, TOTAL': 'choline',  # Important for brain health
            'BETAINE': 'betaine',  # Beneficial compound
            
            # Additives (Domain 5) - Limited data in CNF, mostly detected from food descriptions
            'ASPARTAME': 'artificial_sweeteners',  # Only additive tracked as nutrient in CNF
            
            # Calculated ratios (Domain 1) - computed from the above nutrients
            # Food ingredients and processing - require additional food categorization
        }
    
    def extract_nutrients_enhanced(self, food_ids: List[int], food_item: FoodItem) -> FoodItem:
        """
        Enhanced nutrient extraction using existing CNF pipeline infrastructure
        Leverages established data loading while mapping to FCS 2.0 structure
        """
        try:
            # Get nutrient data using existing pipeline structure
            food_nutrients = self.cnf_pipeline.nutrient_amount_df[
                self.cnf_pipeline.nutrient_amount_df['FoodID'].isin(food_ids)
            ]
            
            # Merge with nutrient names using existing pipeline
            merged_data = pd.merge(
                food_nutrients, 
                self.cnf_pipeline.nutrient_name_df, 
                on='NutrientID'
            )
            
            if merged_data.empty:
                raise ValueError(f"No nutrient data found for food IDs: {food_ids}")
            
            # Get energy value for normalization to 100 kcal
            energy_rows = merged_data[merged_data['NutrientName'].str.contains('ENERGY', case=False, na=False)]
            if energy_rows.empty:
                logger.warning("Energy data not found, using default normalization")
                energy_value = 100  # Default fallback
            else:
                energy_value = energy_rows['NutrientValue'].iloc[0]
            
            # Extract and map nutrients to FCS domains
            mapped_count = 0
            total_nutrients = len(merged_data)
            
            # Convert to numpy arrays for faster processing
            nutrient_names = merged_data['NutrientName'].str.upper().values
            nutrient_values = merged_data['NutrientValue'].values
            
            # Pre-compile nutrient mapping for faster lookup
            nutrient_lookup = {}
            for cnf_name, fcs_name in self.nutrient_mapping.items():
                nutrient_lookup[cnf_name] = fcs_name
            
            # Pre-compile domain attribute lookup for faster search
            domain_lookup = {}
            for domain_name, attributes in food_item.attributes.items():
                for attr_name in attributes:
                    domain_lookup[attr_name] = domain_name
            
            # Vectorized processing
            for i, (nutrient_name, nutrient_value) in enumerate(zip(nutrient_names, nutrient_values)):
                # Fast mapping lookup
                fcs_attribute = None
                for cnf_name, fcs_name in nutrient_lookup.items():
                    if cnf_name in nutrient_name:
                        fcs_attribute = fcs_name
                        break
                
                if not fcs_attribute:
                    continue  # Skip unmapped nutrients
                
                # Normalize to 100 kcal as per FCS 2.0 methodology
                normalized_value = (nutrient_value / energy_value) * 100 if energy_value > 0 else 0
                
                # Fast domain lookup and set attribute
                domain_name = domain_lookup.get(fcs_attribute)
                if domain_name:
                    food_item.set_attribute(domain_name, fcs_attribute, normalized_value)
                    mapped_count += 1
            
            logger.debug(f"CNF: Mapped {mapped_count} out of {total_nutrients} nutrients")
            
            # Calculate nutrient ratios using extracted values
            self._calculate_nutrient_ratios(food_item)
            
            # Apply food categorization for ingredients and processing domains
            self._categorize_food_ingredients(food_ids, food_item)
            
            return food_item
            
        except Exception as e:
            logger.error(f"Error in enhanced CNF extraction: {str(e)}")
            raise
    
    def _calculate_nutrient_ratios(self, food_item: FoodItem) -> None:
        """Calculate nutrient ratios for Domain 1 using extracted values"""
        try:
            # Potassium to Sodium ratio
            sodium = food_item.attributes['minerals']['sodium']
            potassium = food_item.attributes['minerals']['potassium'] 
            
            if sodium > 0:
                potassium_sodium_ratio = potassium / sodium
                food_item.set_attribute('nutrient_ratios', 'potassium_to_sodium', potassium_sodium_ratio)
            
            # Unsaturated to Saturated Fat ratio
            saturated_fat = food_item.attributes['specific_lipids']['saturated_fat']
            monounsaturated_fat = food_item.attributes['specific_lipids']['monounsaturated_fat']
            polyunsaturated_fat = food_item.attributes['specific_lipids']['polyunsaturated_fat']
            
            if saturated_fat > 0:
                unsaturated_fat = monounsaturated_fat + polyunsaturated_fat
                unsat_sat_ratio = unsaturated_fat / saturated_fat
                food_item.set_attribute('nutrient_ratios', 'unsaturated_to_saturated_fat', unsat_sat_ratio)
            
            # Fiber to Carbohydrate ratio
            fiber = food_item.attributes['fiber_protein']['fiber']
            total_carbs = food_item.attributes['fiber_protein']['total_carbohydrate']
            
            if total_carbs > 0:
                fiber_carb_ratio = fiber / total_carbs
                food_item.set_attribute('nutrient_ratios', 'fiber_to_carbohydrate', fiber_carb_ratio)
            
        except Exception as e:
            logger.warning(f"Could not calculate all nutrient ratios: {e}")
    
    def _categorize_food_ingredients(self, food_ids: List[int], food_item: FoodItem) -> None:
        """
        Enhanced food categorization with comprehensive NOVA classification support
        Uses existing CNF food group and description data
        """
        try:
            # Get food information using existing pipeline
            food_info = self.cnf_pipeline.food_name_df[
                self.cnf_pipeline.food_name_df['FoodID'].isin(food_ids)
            ]
            
            if food_info.empty:
                return
            
            # Merge with food group information
            food_with_groups = pd.merge(
                food_info,
                self.cnf_pipeline.food_group_df,
                on='FoodGroupID',
                how='left'
            )
            
            # Track processing levels for combined foods (use worst case)
            detected_processing_levels = []
            
            # Enhanced food categorization using CNF food groups and descriptions
            for _, row in food_with_groups.iterrows():
                food_desc = row.get('FoodDescription', '').upper()
                group_name = row.get('FoodGroupName', '').upper() if 'FoodGroupName' in row else ''
                food_group_id = row.get('FoodGroupID', 0)
                
                logger.debug(f" Categorizing food: '{food_desc}' in group: '{group_name}' (ID: {food_group_id})")
                
                # Use CNF food group structure for better categorization
                if food_group_id == 9:  # Fruits and Fruit Juices
                    food_item.set_attribute('food_ingredients', 'fruit', 100)
                elif food_group_id == 11:  # Vegetables and Vegetable Products
                    food_item.set_attribute('food_ingredients', 'vegetable', 100)
                elif food_group_id == 16:  # Legumes and Legume Products
                    food_item.set_attribute('food_ingredients', 'beans', 100)
                elif food_group_id == 12:  # Nuts and Seeds
                    food_item.set_attribute('food_ingredients', 'nuts', 100)
                elif food_group_id == 15:  # Finfish and Shellfish Products
                    food_item.set_attribute('food_ingredients', 'seafood', 100)
                elif food_group_id == 4:  # Fats and Oils
                    food_item.set_attribute('food_ingredients', 'plant_oils', 100)
                elif food_group_id == 1:  # Dairy and Egg Products
                    if 'YOGURT' in food_desc or 'YOGHURT' in food_desc:
                        food_item.set_attribute('food_ingredients', 'yogurt', 100)
                
                # Enhanced processing level detection with comprehensive keyword matching
                
                # NOVA 4 (Ultra-processed) indicators - expanded list
                ultra_processed_terms = [
                    # Packaged/processed indicators
                    'INSTANT', 'MIX', 'POWDER', 'CONCENTRATE', 'SYRUP', 'EXTRACT',
                    'SWEETENED', 'FLAVORED', 'FLAVOURED', 'ARTIFICIAL', 'IMITATION', 'SUBSTITUTE',
                    # Manufacturing indicators  
                    'ENRICHED', 'FORTIFIED', 'MODIFIED', 'RESTRUCTURED', 'REFORMED',
                    # Specific ultra-processed foods
                    'BREAKFAST CEREAL', 'READY TO EAT', 'CANDY', 'SODA', 'SOFT DRINK', 'ENERGY DRINK',
                    'CHIPS', 'CRACKERS', 'COOKIES', 'CAKE', 'PIE', 'PASTRY', 'DONUT', 'MUFFIN',
                    'ICE CREAM', 'FROZEN DESSERT', 'PUDDING', 'JELLO', 'GELATIN',
                    # Chemical indicators
                    'HYDROGENATED', 'HIGH FRUCTOSE', 'CORN SYRUP', 'ASPARTAME', 'SUCRALOSE',
                    'MONOSODIUM GLUTAMATE', 'MSG', 'SODIUM NITRITE', 'NITRATE',
                    # Processing methods
                    'EXTRUDED', 'PUFFED', 'RECONSTITUTED', 'DEHYDRATED'
                ]
                
                # NOVA 3 (Processed foods) indicators - expanded list
                processed_terms = [
                    # Preservation methods
                    'CURED', 'SMOKED', 'SALTED', 'PICKLED', 'FERMENTED', 'AGED',
                    # Canned products
                    'CANNED', 'JARRED', 'BOTTLED', 'PRESERVED',
                    # Processed meats
                    'HAM', 'BACON', 'SAUSAGE', 'DELI MEAT', 'LUNCH MEAT', 'HOT DOG', 'BRATWURST',
                    'PEPPERONI', 'SALAMI', 'BOLOGNA', 'PASTRAMI',
                    # Dairy processing
                    'CHEESE', 'PROCESSED CHEESE',
                    # Baked goods
                    'BREAD', 'BAGUETTE', 'ROLL', 'BAGEL', 'TORTILLA'
                ]
                
                # NOVA 2 (Culinary ingredients) indicators
                culinary_terms = [
                    'OIL', 'BUTTER', 'LARD', 'SHORTENING', 'MARGARINE', 'GHEE',
                    'SALT', 'SUGAR', 'HONEY', 'MAPLE SYRUP', 'MOLASSES',
                    'VINEGAR', 'FLOUR', 'STARCH', 'CORN STARCH', 'BAKING POWDER', 'YEAST'
                ]
                
                # Determine processing level for this food item
                current_processing_level = 1  # Default to minimally processed
                
                # Check for ultra-processed characteristics
                if any(term in food_desc for term in ultra_processed_terms):
                    current_processing_level = 4
                    detected_processing_levels.append(4)
                    
                    # Set food ingredients for ultra-processed
                    food_item.set_attribute('food_ingredients', 'added_sugar', 100)
                    
                    # Enhanced additive detection for ultra-processed foods
                    self._detect_additives_from_description(food_desc, food_item, processing_level=4)
                    
                    # Set processing methods
                    if any(term in food_desc for term in ['FRIED', 'DEEP FRIED']):
                        food_item.set_attribute('processing', 'frying', 100)
                    if 'CANNED' in food_desc:
                        food_item.set_attribute('processing', 'canning', 100)
                    
                    logger.debug(f" Detected NOVA 4 (ultra-processed) food: '{food_desc}'")
                
                # Check for processed foods
                elif any(term in food_desc for term in processed_terms):
                    current_processing_level = 3
                    detected_processing_levels.append(3)
                    
                    # Set appropriate food ingredients
                    if any(meat_term in food_desc for meat_term in ['HAM', 'BACON', 'SAUSAGE', 'DELI', 'LUNCH', 'HOT DOG', 'CURED']):
                        food_item.set_attribute('food_ingredients', 'red_or_processed_meat', 100)
                    elif 'CHEESE' in food_desc:
                        # Cheese is processed but not necessarily refined grains
                        pass
                    elif any(grain_term in food_desc for grain_term in ['BREAD', 'ROLL', 'BAGEL']):
                        food_item.set_attribute('food_ingredients', 'refined_grains', 100)
                    
                    # Detect additives for processed foods
                    self._detect_additives_from_description(food_desc, food_item, processing_level=3)
                    
                    # Set processing methods
                    if any(term in food_desc for term in ['SMOKED', 'SMOKING']):
                        food_item.set_attribute('processing', 'smoking', 100)
                    if 'CANNED' in food_desc:
                        food_item.set_attribute('processing', 'canning', 100)
                    if any(term in food_desc for term in ['FERMENTED', 'AGED']):
                        food_item.set_attribute('processing', 'fermentation', 100)
                    
                    logger.debug(f" Detected NOVA 3 (processed) food: '{food_desc}'")
                
                # Check for culinary ingredients
                elif any(term in food_desc for term in culinary_terms):
                    current_processing_level = 2
                    detected_processing_levels.append(2)
                    
                    if any(oil_term in food_desc for oil_term in ['OIL', 'BUTTER', 'MARGARINE', 'SHORTENING']):
                        food_item.set_attribute('food_ingredients', 'plant_oils', 100)
                    
                    logger.debug(f" Detected NOVA 2 (culinary ingredient): '{food_desc}'")
                
                else:
                    # Minimally processed
                    detected_processing_levels.append(1)
                    food_item.set_attribute('processing', 'minimal_processing', 100)
                    logger.debug(f" Detected NOVA 1 (minimally processed): '{food_desc}'")
                
                # Detect whole grains vs refined grains
                if food_group_id == 20:  # Cereals, Grains and Pasta
                    if any(term in food_desc for term in ['WHOLE', 'BROWN', 'BRAN', 'WHEAT GERM']):
                        food_item.set_attribute('food_ingredients', 'whole_grains', 100)
                    else:
                        food_item.set_attribute('food_ingredients', 'refined_grains', 100)
                
                logger.debug(f" Food '{food_desc}' categorized as NOVA level {current_processing_level}")
            
            # For combined foods, use energy-weighted processing level
            if detected_processing_levels:
                final_processing_level = self._calculate_energy_weighted_processing(food_ids, detected_processing_levels)
                logger.debug(f" Combined food processing levels: {detected_processing_levels}")
                logger.debug(f" Energy-weighted final processing level: {final_processing_level}")
                
                # Store detailed processing information for mixed dishes
                processing_details = self._get_processing_details(food_ids, detected_processing_levels, food_with_groups)
                food_item.set_processing_details(processing_details)
                
                # Store the final NOVA processing level in the food item for the analyzer to use
                self._set_final_nova_processing_level(food_item, final_processing_level)
                
                # Set a flag to indicate this is a combined food with mixed processing levels
                if len(set(detected_processing_levels)) > 1:
                    logger.debug(f" Mixed processing levels detected in combined food - using energy weighting")
            else:
                # Default to minimally processed if no processing levels detected
                logger.debug(f" No processing levels detected, defaulting to NOVA 1 (minimally processed)")
                self._set_final_nova_processing_level(food_item, 1)
                    
        except Exception as e:
            logger.warning(f"Could not fully categorize food ingredients: {e}")
            logger.debug(f" Error in food categorization: {e}")
    
    def _get_processing_details(self, food_ids: List[int], processing_levels: List[int], food_with_groups) -> Dict:
        """
        Get detailed processing information for each food component in mixed dishes
        """
        try:
            details = {
                "is_mixed_dish": len(set(processing_levels)) > 1,
                "individual_foods": [],
                "energy_weights": [],
                "final_processing_level": None
            }
            
            # Get energy values for weighting calculation
            food_energies = []
            for food_id in food_ids:
                food_nutrients = self.cnf_pipeline.nutrient_amount_df[
                    self.cnf_pipeline.nutrient_amount_df['FoodID'] == food_id
                ]
                energy_data = pd.merge(food_nutrients, self.cnf_pipeline.nutrient_name_df, on='NutrientID')
                energy_rows = energy_data[energy_data['NutrientName'].str.contains('ENERGY', case=False, na=False)]
                
                if not energy_rows.empty:
                    energy_value = energy_rows['NutrientValue'].iloc[0]
                    food_energies.append(energy_value)
                else:
                    food_energies.append(100)  # Default fallback
            
            total_energy = sum(food_energies)
            
            # Map NOVA levels to category names
            nova_level_names = {
                1: "MINIMALLY_PROCESSED",
                2: "PROCESSED_CULINARY_INGREDIENTS", 
                3: "PROCESSED_FOODS",
                4: "ULTRA_PROCESSED_FOODS"
            }
            
            # Collect details for each food
            for i, (food_id, processing_level) in enumerate(zip(food_ids, processing_levels)):
                # Get food name
                food_row = food_with_groups[food_with_groups['FoodID'] == food_id]
                food_name = food_row['FoodDescription'].iloc[0] if not food_row.empty else f"Food ID {food_id}"
                
                energy_weight = food_energies[i] / total_energy if total_energy > 0 else 0
                
                food_detail = {
                    "food_id": food_id,
                    "food_name": food_name,
                    "nova_level": processing_level,
                    "nova_category": nova_level_names.get(processing_level, "UNKNOWN"),
                    "energy_kcal": food_energies[i],
                    "energy_weight": round(energy_weight, 3)
                }
                
                details["individual_foods"].append(food_detail)
                details["energy_weights"].append(round(energy_weight, 3))
            
            return details
            
        except Exception as e:
            logger.warning(f"Error getting processing details: {e}")
            return {
                "is_mixed_dish": False,
                "individual_foods": [],
                "energy_weights": [],
                "final_processing_level": None
            }
    
    def _detect_additives_from_description(self, food_desc: str, food_item: FoodItem, processing_level: int) -> None:
        """
        Comprehensive additives detection from food descriptions
        Uses pattern matching to identify common food additives and assign penalties
        """
        try:
            
            # Artificial Sweeteners - Most common and well-documented
            artificial_sweetener_terms = [
                'ASPARTAME', 'SUCRALOSE', 'SACCHARIN', 'ACESULFAME', 'STEVIA', 
                'ARTIFICIAL SWEETENER', 'SUGAR FREE', 'NO SUGAR', 'DIET', 'LIGHT',
                'LOW CALORIE', 'CALORIE REDUCED', 'SUGAR SUBSTITUTE'
            ]
            
            if any(term in food_desc for term in artificial_sweetener_terms):
                food_item.set_attribute('additives', 'artificial_sweeteners', 100)
            
            # Preservatives - Common in processed foods
            preservative_terms = [
                'PRESERVATIVE', 'SODIUM BENZOATE', 'POTASSIUM SORBATE', 'CALCIUM PROPIONATE',
                'SODIUM PROPIONATE', 'SORBIC ACID', 'BENZOIC ACID', 'CITRIC ACID',
                'ASCORBIC ACID', 'TOCOPHEROL', 'BHA', 'BHT', 'TBHQ'
            ]
            
            # Detect preservatives from processing context
            if processing_level >= 3:  # Processed or ultra-processed
                # Baked goods likely have preservatives
                if any(term in food_desc for term in ['BREAD', 'CAKE', 'MUFFIN', 'COOKIE', 'CRACKER']):
                    food_item.set_attribute('additives', 'preservatives', 100)
                
                # Processed meats definitely have preservatives
                if any(term in food_desc for term in ['HAM', 'BACON', 'SAUSAGE', 'DELI', 'CURED', 'SMOKED']):
                    food_item.set_attribute('additives', 'preservatives', 100)
                    food_item.set_attribute('additives', 'nitrites', 100)  # Nitrites common in processed meats
            
            if any(term in food_desc for term in preservative_terms):
                food_item.set_attribute('additives', 'preservatives', 100)
            
            # Artificial Colors - Common in ultra-processed foods
            artificial_color_terms = [
                'ARTIFICIAL COLOR', 'ARTIFICIAL COLOUR', 'FOOD COLORING', 'FOOD COLOURING',
                'RED DYE', 'BLUE DYE', 'YELLOW DYE', 'TARTRAZINE', 'SUNSET YELLOW',
                'BRILLIANT BLUE', 'ALLURA RED'
            ]
            
            if any(term in food_desc for term in artificial_color_terms):
                food_item.set_attribute('additives', 'artificial_colors', 100)
                logger.debug(f" Detected artificial colors in '{food_desc}'")
            
            # Infer artificial colors from food types
            if processing_level == 4:  # Ultra-processed
                color_likely_foods = [
                    'CANDY', 'GUMMY', 'JELLO', 'GELATIN', 'SOFT DRINK', 'SODA',
                    'ENERGY DRINK', 'SPORTS DRINK', 'FLAVORED', 'COLOURED'
                ]
                if any(term in food_desc for term in color_likely_foods):
                    food_item.set_attribute('additives', 'artificial_colors', 100)
                    logger.debug(f" Inferred artificial colors in colored processed food: '{food_desc}'")
            
            # Hydrogenated Oils - Trans fats
            hydrogenated_terms = [
                'HYDROGENATED', 'PARTIALLY HYDROGENATED', 'TRANS FAT', 'SHORTENING',
                'MARGARINE', 'VEGETABLE SHORTENING'
            ]
            
            if any(term in food_desc for term in hydrogenated_terms):
                food_item.set_attribute('additives', 'hydrogenated_oils', 100)
                logger.debug(f" Detected hydrogenated oils in '{food_desc}'")
            
            # High Fructose Corn Syrup
            hfcs_terms = [
                'HIGH FRUCTOSE CORN SYRUP', 'HFCS', 'CORN SYRUP', 'GLUCOSE-FRUCTOSE',
                'FRUCTOSE-GLUCOSE'
            ]
            
            if any(term in food_desc for term in hfcs_terms):
                food_item.set_attribute('additives', 'high_fructose_corn_syrup', 100)
                logger.debug(f" Detected HFCS in '{food_desc}'")
            
            # Monosodium Glutamate
            msg_terms = [
                'MONOSODIUM GLUTAMATE', 'MSG', 'GLUTAMATE', 'FLAVOR ENHANCER',
                'FLAVOUR ENHANCER'
            ]
            
            if any(term in food_desc for term in msg_terms):
                food_item.set_attribute('additives', 'monosodium_glutamate', 100)
                logger.debug(f" Detected MSG in '{food_desc}'")
            
            # Nitrites/Nitrates - Cured meats
            nitrite_terms = [
                'SODIUM NITRITE', 'SODIUM NITRATE', 'POTASSIUM NITRITE', 'POTASSIUM NITRATE',
                'NITRITE', 'NITRATE', 'CURING SALT'
            ]
            
            if any(term in food_desc for term in nitrite_terms):
                food_item.set_attribute('additives', 'nitrites', 100)
                logger.debug(f" Detected nitrites from description: '{food_desc}'")
            
            # Additional ultra-processed indicators
            if processing_level == 4:
                # Emulsifiers, stabilizers, thickeners (grouped under preservatives)
                emulsifier_terms = [
                    'LECITHIN', 'MONO AND DIGLYCERIDES', 'POLYSORBATE', 'CARRAGEENAN',
                    'XANTHAN GUM', 'GUAR GUM', 'CELLULOSE GUM', 'MODIFIED STARCH',
                    'SODIUM STEAROYL LACTYLATE', 'CALCIUM STEAROYL LACTYLATE'
                ]
                
                # For gluten-free bread (like rice bran bread), emulsifiers are very common
                if 'GLUTEN FREE' in food_desc or 'GLUTEN-FREE' in food_desc:
                    food_item.set_attribute('additives', 'preservatives', 100)  # Likely has emulsifiers
                    logger.debug(f" Inferred emulsifiers in gluten-free product: '{food_desc}'")
                
                if any(term in food_desc for term in emulsifier_terms):
                    food_item.set_attribute('additives', 'preservatives', 100)
                    logger.debug(f" Detected emulsifiers/stabilizers in '{food_desc}'")
            
        except Exception as e:
            logger.warning(f"Error detecting additives for '{food_desc}': {e}")
    
    def _set_final_nova_processing_level(self, food_item: FoodItem, processing_level: float) -> None:
        """
        Set the final NOVA processing level determined by CNF analysis
        This eliminates the need for duplicate classification in the Food Analyzer
        
        Args:
            food_item: The FoodItem to update
            processing_level: NOVA level (1=minimally processed, 2=culinary ingredients, 
                            3=processed foods, 4=ultra-processed foods)
        """
        # Map processing level to NOVA score according to Food Compass methodology
        nova_score_mapping = {
            1: 0,    # NOVA 1: Minimally processed (best score)
            2: -5,   # NOVA 2: Processed culinary ingredients  
            3: -7,   # NOVA 3: Processed foods
            4: -10   # NOVA 4: Ultra-processed foods (worst score)
        }
        
        # For mixed dishes with fractional processing levels, interpolate the score
        if processing_level == int(processing_level):
            # Single food or uniform processing level
            nova_score = nova_score_mapping.get(int(processing_level), -5)
            food_item.set_nova_processing_level(int(processing_level))
        else:
            # Mixed dish - interpolate the processing penalty
            lower_level = int(processing_level)
            upper_level = lower_level + 1
            fraction = processing_level - lower_level
            
            lower_score = nova_score_mapping.get(lower_level, -5)
            upper_score = nova_score_mapping.get(upper_level, -10)
            nova_score = lower_score + fraction * (upper_score - lower_score)
            
            # For mixed dishes, store a special flag instead of a single NOVA level
            food_item.set_nova_processing_level(-1)  # Special flag for mixed dishes
        
        # Set the NOVA processing score directly in Domain 6
        food_item.set_attribute('processing', 'nova_processing', nova_score)
        
        logger.debug(f" Set processing level {processing_level} with interpolated score {nova_score:.2f}")
        if processing_level != int(processing_level):
            logger.debug(f" Mixed dish detected - using energy-weighted processing penalty instead of single NOVA category")
    
    def _calculate_energy_weighted_processing(self, food_ids: List[int], processing_levels: List[int]) -> float:
        """
        Calculate energy-weighted NOVA processing level for combined foods
        Uses calorie contribution of each food to weight the final processing score
        """
        try:
            # Get energy values for each food
            food_energies = []
            for food_id in food_ids:
                # Get energy data from CNF pipeline
                food_nutrients = self.cnf_pipeline.nutrient_amount_df[
                    self.cnf_pipeline.nutrient_amount_df['FoodID'] == food_id
                ]
                energy_data = pd.merge(food_nutrients, self.cnf_pipeline.nutrient_name_df, on='NutrientID')
                energy_rows = energy_data[energy_data['NutrientName'].str.contains('ENERGY', case=False, na=False)]
                
                if not energy_rows.empty:
                    energy_value = energy_rows['NutrientValue'].iloc[0]
                    food_energies.append(energy_value)
                    logger.debug(f" Food ID {food_id} has {energy_value} kcal")
                else:
                    food_energies.append(100)  # Default fallback
                    logger.debug(f" Food ID {food_id} - no energy data, using 100 kcal default")
            
            # Calculate energy weights
            total_energy = sum(food_energies)
            if total_energy == 0:
                # Fallback to simple average if no energy data
                return round(sum(processing_levels) / len(processing_levels))
            
            # Calculate weighted processing level
            weighted_sum = sum(processing_levels[i] * food_energies[i] for i in range(len(processing_levels)))
            energy_weighted_level = weighted_sum / total_energy
            
            logger.debug(f" Energy weights: {[round(e/total_energy, 2) for e in food_energies]}")
            logger.debug(f" Weighted processing calculation: {weighted_sum}/{total_energy} = {energy_weighted_level}")
            
            # Keep fractional level for mixed dishes - don't round to integer
            final_level = max(1.0, min(4.0, energy_weighted_level))
            return final_level
            
        except Exception as e:
            logger.warning(f"Error calculating energy-weighted processing: {e}")
            # Fallback to worst-case approach if energy weighting fails
            return max(processing_levels) if processing_levels else 1

# Factory function to create integrator using existing CNF data directory
def create_cnf_integrator(cnf_data_dir: str = None) -> EnhancedCNFDataIntegrator:
    """
    Factory to create CNF integrator reusing existing data directory structure
    """
    if cnf_data_dir is None:
        # Default to the same directory used by existing CNF pipeline
        # From fcs/utils/cnf_data_integrator.py -> backend/raw_cnf
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        cnf_data_dir = os.path.join(base_dir, 'raw_cnf')
    
    return EnhancedCNFDataIntegrator(cnf_data_dir)