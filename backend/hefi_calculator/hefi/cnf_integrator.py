import os
import sys
import json
from typing import Dict, List, Optional, Tuple
import pandas as pd
import re


# Use the same CNF pipeline wiring as the FCS integrator
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # -> backend
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


class HEFICNFIntegrator:
    """
    Extracts HEFI-relevant totals and nutrients from CNF for a list of FoodIDs with amounts.
    This provides RA-based totals for food categories and beverage grams, plus nutrients and energy.
    Uses Health Canada's official Reference Amounts from nutrition_reference_amounts.json.
    """

    # CNF group IDs (from FOOD_GROUP.csv)
    GROUP_FRUITS = 9
    GROUP_VEGETABLES = 11
    GROUP_BEVERAGES = 14
    GROUP_LEGUMES = 16
    GROUP_CEREALS_GRAINS_PASTA = {18, 20}  # Include both bread and cereal groups
    GROUP_FINISH_SHELLFISH = 15
    GROUP_NUTS_SEEDS = 12
    GROUP_DAIRY_EGGS = 1
    GROUP_MEAT_PORK_BEEF_POULTRY = {5, 7, 10, 13, 17}

    def __init__(self, cnf_dir: str):
        self.pipeline = get_shared_cnf_pipeline(cnf_dir)
        self.cnf_dir = cnf_dir

        # Load CNF reference data
        self._load_cnf_reference_data()
        
        # Load Health Canada Reference Amounts
        self._load_reference_amounts()

        # Nutrient name -> canonical mapping (exact match to CNF nutrient names)
        self.nutrient_lookup = {
            'ENERGY (KILOCALORIES)': 'energy_kcal',
            'FATTY ACIDS, SATURATED, TOTAL': 'sfa_g',
            'FATTY ACIDS, MONOUNSATURATED, TOTAL': 'mufa_g',
            'FATTY ACIDS, POLYUNSATURATED, TOTAL': 'pufa_g',
            'SUGARS, TOTAL': 'total_sugars_g',
            'SODIUM': 'sodium_mg',
        }

    def _load_cnf_reference_data(self):
        """Load conversion factors and measure descriptions, preferring pipeline-loaded data."""
        # Prefer already-loaded dataframes from the shared CNF pipeline (they use detected encodings)
        try:
            self.conversion_factors_df = getattr(self.pipeline, 'conversion_factor_df', pd.DataFrame())
            self.measure_names_df = getattr(self.pipeline, 'measure_name_df', pd.DataFrame())
            
            # Dataframes loaded successfully from pipeline
            
        except Exception as e:
            # Could not load pipeline data, will fall back to direct loading
            self.conversion_factors_df = pd.DataFrame()
            self.measure_names_df = pd.DataFrame()

        # If for any reason they are empty/missing, fall back to robust on-disk loading with encoding detection
        if self.conversion_factors_df.empty or self.measure_names_df.empty:
            try:
                conv_path = os.path.join(self.cnf_dir, 'CONVERSION_FACTOR.csv')
                meas_path = os.path.join(self.cnf_dir, 'MEASURE_NAME.csv')

                # Use the pipeline's encoding detector to avoid UTF-8 decode errors on Windows CSVs
                detect_enc = getattr(self.pipeline, '_detect_encoding', None)
                if callable(detect_enc):
                    conv_enc = detect_enc(conv_path)
                    meas_enc = detect_enc(meas_path)
                else:
                    # Reasonable fallbacks if detector is unavailable
                    conv_enc = 'cp1252'
                    meas_enc = 'cp1252'

                self.conversion_factors_df = pd.read_csv(conv_path, encoding=conv_enc, low_memory=False)
                self.measure_names_df = pd.read_csv(meas_path, encoding=meas_enc, low_memory=False)
            except Exception as e:
                print(f"Warning: Could not load CNF reference data: {e}")
                self.conversion_factors_df = pd.DataFrame()
                self.measure_names_df = pd.DataFrame()
    
    def _load_reference_amounts(self):
        """Load Health Canada Reference Amounts from nutrition_reference_amounts.json"""
        try:
            ra_path = os.path.join(os.path.dirname(self.cnf_dir), 'raw_cnf', 'nutrition_reference_amounts.json')
            with open(ra_path, 'r', encoding='utf-8') as f:
                self.reference_amounts = json.load(f)
            
            # Create lookup tables for faster access
            self._build_ra_lookup_tables()
        except Exception as e:
            print(f"Warning: Could not load reference amounts: {e}")
            self.reference_amounts = {}
            self.ra_lookup = {}
    
    def _build_ra_lookup_tables(self):
        """Build comprehensive lookup tables for RA categories and amounts based on Health Canada standards"""
        self.ra_lookup = {}
        
        categories = self.reference_amounts.get('categories', {})
        
        # Bakery products (Category A)
        self.ra_lookup.update({
            'bread': 75,  # A.1
            'rolls_buns': 55,  # A.2
            'bagels': 85,  # A.3
            'brownies_bars': 40,  # A.4
            'cake_heavy': 125,  # A.5
            'cake_medium': 80,  # A.6
            'cake_light': 55,  # A.7
            'sweet_pastries': 55,  # A.8
            'muffins': 110,  # A.9
            'cookies': 30,  # A.10
            'crackers': 20,  # A.11
            'snack_crackers': 30,  # A.12
            'dry_breads': 30,  # A.13
            'toaster_pastries': 55,  # A.14
            'ice_cream_cones': 5,  # A.15
            'croutons': 7,  # A.16
            'pancakes_waffles': 75,  # A.17
            'grain_bars_filled': 40,  # A.18
            'grain_bars_plain': 30,  # A.19
            'energy_bars': 45,  # A.20
            'rice_cakes': 15,  # A.21
            'pies_tarts': 110,  # A.22
            'pie_crust': 21,  # A.23
            'pizza_crust': 55,  # A.24
            'taco_shell': 30,  # A.25
        })
        
        # Beverages (Category B)
        self.ra_lookup.update({
            'beverages': 375,  # B.1 (mL)
            'wine': 188,  # B.2
            'beer': 333,  # B.2
            'alcoholic_mixed': 333,  # B.2
            'coffee': 250,  # B.3
            'espresso': 30,  # B.3
            'tea': 250,  # B.4
            'hot_chocolate': 250,  # B.5
        })
        
        # Cereals and grains (Category C)
        self.ra_lookup.update({
            'hot_cereal_dry': 40,  # C.1
            'hot_cereal_prepared': 250,  # C.1 (mL)
            'ready_cereal_light': 15,  # C.2 (puffed, uncoated)
            'ready_cereal_medium': 30,  # C.3 (flaked, coated)
            'ready_cereal_heavy': 55,  # C.4 (granola, fruit/nut)
            'bran_wheat_germ': 15,  # C.5
            'flours': 30,  # C.6
            'rice_grains_dry': 45,  # C.7
            'rice_grains_cooked': 140,  # C.7
            'pasta_dry': 85,  # C.8
            'pasta_cooked': 215,  # C.8
            'pasta_fried_dry': 25,  # C.9
            'starch': 10,  # C.10
            'stuffing': 100,  # C.11
        })
        
        # Dairy products (Category D)
        self.ra_lookup.update({
            'cheese': 30,  # D.1
            'cottage_cheese': 125,  # D.2
            'cheese_ingredient': 55,  # D.3
            'hard_cheese': 15,  # D.4
            'quark_fresh_cheese': 100,  # D.5
            'cream': 15,  # D.6 (mL)
            'cream_powder': 2,  # D.7
            'whipped_cream': 15,  # D.8
            'eggnog': 125,  # D.9 (mL)
            'condensed_milk': 15,  # D.10 (mL)
            'milk': 250,  # D.11 (mL)
            'fermented_dairy': 188,  # D.12 (mL)
            'shakes': 250,  # D.13 (mL)
            'sour_cream': 30,  # D.14 (mL)
            'yogurt': 175,  # D.15
        })
        
        # Desserts (Category E)
        self.ra_lookup.update({
            'ice_cream_tub': 188,  # E.1 (mL)
            'ice_cream_sandwich': 125,  # E.2 (mL)
            'ice_cream_bar': 75,  # E.3 (mL)
            'sundaes': 250,  # E.4 (mL)
            'custard_pudding': 130,  # E.5
        })
        
        # Eggs (Category G)
        self.ra_lookup.update({
            'egg_mixtures': 110,  # G.1
            'eggs': 100,  # G.2
            'egg_substitutes': 100,  # G.3
        })
        
        # Marine and freshwater animals (Category I)
        self.ra_lookup.update({
            'anchovies_caviar': 15,  # I.1
            'fish_with_sauce': 140,  # I.2 (cooked)
            'fish_raw': 125,  # I.3
            'fish_cooked': 100,  # I.3
            'fish_canned': 55,  # I.4
            'fish_smoked': 55,  # I.5
        })
        
        # Fruits (Category J)
        self.ra_lookup.update({
            'fruit_fresh': 140,  # J.1
            'fruit_canned': 167,  # J.1 (mL)
            'berries': 80,  # J.2
            'melons': 150,  # J.3
            'avocado_ingredient': 30,  # J.4
            'cranberries_ingredient': 55,  # J.5
            'applesauce': 110,  # J.6 or 125mL
            'dried_fruit': 40,  # J.7
            'candied_fruit': 30,  # J.8
            'fruit_garnish': 4,  # J.9
            'fruit_relishes': 60,  # J.10 (mL)
            'fruit_juice': 250,  # J.11 (mL)
            'juice_ingredient': 5,  # J.12 (mL)
        })
        
        # Legumes (Category K)
        self.ra_lookup.update({
            'tofu': 85,  # K.1
            'legumes_dry': 35,  # K.2
            'legumes_cooked': 125,  # K.2 (mL)
        })
        
        # Meat and poultry (Category L)
        self.ra_lookup.update({
            'pork_rinds_uncooked': 54,  # L.1
            'pork_rinds_cooked': 15,  # L.1
            'breakfast_strips_uncooked': 30,  # L.2
            'breakfast_strips_cooked': 15,  # L.2
            'dried_meat': 30,  # L.3
            'luncheon_meat_uncooked': 75,  # L.4
            'luncheon_meat_cooked': 55,  # L.4
            'sausage_uncooked': 75,  # L.5
            'sausage_cooked': 55,  # L.5
            'meat_poultry_raw': 125,  # L.6
            'meat_poultry_cooked': 100,  # L.6
            'patties_raw': 100,  # L.7
            'patties_cooked': 60,  # L.7
            'cured_meat_raw': 85,  # L.8
            'cured_meat_cooked': 55,  # L.8
            'canned_meat': 55,  # L.9
            'meat_with_sauce': 140,  # L.10
        })
        
        # Combination dishes (Category N)
        self.ra_lookup.update({
            'combination_dish_large': 300,  # N.1
            'combination_dish_medium': 200,  # N.2
            'hors_doeuvres': 85,  # N.3 (without sauce)
            'hors_doeuvres_sauce': 120,  # N.3 (with sauce)
        })
        
        # Nuts and seeds (Category O)
        self.ra_lookup.update({
            'nuts_seeds': 30,  # O.1 (shelled)
            'nut_pastes': 30,  # O.2
            'nut_butters': 15,  # O.3
            'nut_flours': 15,  # O.4
        })
        
        # Potatoes (Category P)
        self.ra_lookup.update({
            'french_fries_frozen': 85,  # P.1
            'french_fries_prepared': 70,  # P.1
            'potatoes_prepared': 140,  # P.2
            'potatoes_fresh': 110,  # P.3
            'potatoes_vacuum': 125,  # P.3
            'potatoes_canned': 167,  # P.3 (mL)
        })
        
        # Salads (Category Q)
        self.ra_lookup.update({
            'salads': 100,  # Q.1
            'gelatin_salad': 120,  # Q.2
            'pasta_potato_salad': 140,  # Q.3
        })
        
        # Sauces and condiments (Category R)
        self.ra_lookup.update({
            'dipping_sauce': 30,  # R.1 (mL)
            'dips_spreads': 30,  # R.2
            'main_sauce': 125,  # R.3 (mL)
            'minor_sauce': 60,  # R.4 (mL)
            'major_condiments': 15,  # R.5 (mL)
            'minor_condiments': 5,  # R.6 (mL)
        })
        
        # Snacks (Category S)
        self.ra_lookup.update({
            'chips_snacks': 50,  # S.1
            'nut_snacks': 50,  # S.2 (shelled)
            'meat_sticks': 20,  # S.3
        })
        
        # Soups (Category T)
        self.ra_lookup.update({
            'soups': 250,  # T.1 (mL)
        })
        
        # Sugars and sweets (Category U)
        self.ra_lookup.update({
            'candies': 40,  # U.1
            'after_dinner_mints': 10,  # U.2
            'hard_candies': 15,  # U.3
            'liquid_candies': 15,  # U.3 (mL)
            'baking_candies': 15,  # U.4
            'breath_mints': 2,  # U.5
            'roll_candies': 5,  # U.6
            'icing_sugar': 30,  # U.7
            'honey_molasses': 20,  # U.8
            'jams_jellies': 15,  # U.9 (mL)
            'fruit_leather': 20,  # U.10
            'marshmallows': 30,  # U.11
            'sugars': 4,  # U.12
            'sugar_substitute': 'equivalent_to_4g_sugar',  # U.13
            'syrup_topping': 60,  # U.14 (mL)
            'syrup_ingredient': 30,  # U.15 (mL)
        })
        
        # Vegetables (Category V)
        self.ra_lookup.update({
            'vegetables_fresh': 85,  # V.1
            'vegetables_canned': 125,  # V.1 (mL)
            'vegetables_with_sauce_fresh': 110,  # V.2
            'vegetables_with_sauce_canned': 125,  # V.2 (mL)
            'vegetables_garnish_fresh': 4,  # V.3
            'vegetables_garnish_canned': 5,  # V.3 (mL)
            'chili_pepper': 30,  # V.4
            'seaweed_mushrooms': 15,  # V.5
            'sprouts': 65,  # V.6
            'vegetable_juice': 250,  # V.7 (mL)
            'olives': 15,  # V.8
            'pickled_vegetables': 30,  # V.9
            'relish': 15,  # V.10 (mL)
            'vegetable_paste': 30,  # V.11 (mL)
            'vegetable_sauce': 60,  # V.12 (mL)
        })
        
        # Default fallback
        self.ra_lookup.update({
            'default': 100,  # Default 100g when no specific category matches
        })

    def _get_best_conversion_factor(self, food_id: int) -> float:
        """Get the most appropriate conversion factor for a food item.
        
        Priority order:
        1. Standard serving sizes (slice, fillet, etc.)
        2. Food guide portions
        3. Common household measures
        4. Default to 1.0 (100g)
        """
        if self.conversion_factors_df.empty:
            return 1.0
            
        # Get all conversion factors for this food
        food_factors = self.conversion_factors_df[
            self.conversion_factors_df['FoodID'] == food_id
        ]
        
        if food_factors.empty:
            return 1.0
            
        # Get measure descriptions from MEASURE_NAME.csv using direct lookup
        # The CONVERSION_FACTOR.csv has empty MeasureDescription column,
        # so we need to look up descriptions using MeasureID
        if not self.measure_names_df.empty:
            # Create a copy to avoid SettingWithCopyWarning
            food_factors = food_factors.copy()
            
            # Add measure descriptions using direct lookup instead of merge
            measure_descriptions = []
            measure_names_subset = self.measure_names_df[['MeasureID', 'MeasureDescription']].copy()
            measure_names_subset['MeasureID'] = measure_names_subset['MeasureID'].astype(int)
            
            for _, row in food_factors.iterrows():
                measure_id = int(row['MeasureID'])
                matching_measures = measure_names_subset[
                    measure_names_subset['MeasureID'] == measure_id
                ]
                
                if not matching_measures.empty:
                    desc = matching_measures.iloc[0]['MeasureDescription']
                    measure_descriptions.append(desc if pd.notna(desc) else '')
                else:
                    measure_descriptions.append('')
            
            food_factors['MeasureDescription'] = measure_descriptions
        
        # Define priority keywords for different measure types
        priority_measures = [
            # Standard portions
            ['slice', 'fillet', 'piece', 'serving'],
            # Food guide portions  
            ['food guide', 'portion'],
            # Common household measures
            ['medium', 'small', 'large'],
            # Weight measures
            ['50g', '100g', '125g']
        ]
        
        # Try to find the best match based on priority
        for priority_group in priority_measures:
            for _, row in food_factors.iterrows():
                measure_desc = row.get('MeasureDescription', '')
                if pd.notna(measure_desc) and str(measure_desc).strip():
                    desc = str(measure_desc).lower()
                    if any(keyword in desc for keyword in priority_group):
                        return float(row['ConversionFactorValue'])
        
        # If no priority match, return the first available conversion factor
        if not food_factors.empty:
            return float(food_factors.iloc[0]['ConversionFactorValue'])
            
        return 1.0
    
    def get_measure_description(self, food_id: int, conversion_factor: float) -> str:
        """Get the measure description for a specific food and conversion factor."""
        if self.conversion_factors_df.empty or self.measure_names_df.empty:
            return "Unknown measure"
            
        # Get conversion factors for this food
        food_factors = self.conversion_factors_df[
            self.conversion_factors_df['FoodID'] == food_id
        ].copy()  # Make a copy to avoid SettingWithCopyWarning
        
        if food_factors.empty:
            return "Unknown measure"
        
        # Get measure names and ensure proper data types
        measure_names_subset = self.measure_names_df[['MeasureID', 'MeasureDescription']].copy()
        
        # Ensure both MeasureID columns are int for proper merging
        food_factors['MeasureID'] = food_factors['MeasureID'].astype(int)
        measure_names_subset['MeasureID'] = measure_names_subset['MeasureID'].astype(int)
        
        # Find the measure that matches the conversion factor by direct lookup
        for _, cf_row in food_factors.iterrows():
            row_factor = float(cf_row['ConversionFactorValue'])
            if abs(row_factor - conversion_factor) < 0.001:
                measure_id = int(cf_row['MeasureID'])
                
                # Look up the description directly
                matching_measures = measure_names_subset[
                    measure_names_subset['MeasureID'] == measure_id
                ]
                
                if not matching_measures.empty:
                    measure_desc = matching_measures.iloc[0]['MeasureDescription']
                    if pd.notna(measure_desc) and str(measure_desc).strip():
                        return str(measure_desc).strip()
                    
        # If no exact match found, return the first available measure description
        for _, cf_row in food_factors.iterrows():
            measure_id = int(cf_row['MeasureID'])
            
            # Look up the description directly
            matching_measures = measure_names_subset[
                measure_names_subset['MeasureID'] == measure_id
            ]
            
            if not matching_measures.empty:
                measure_desc = matching_measures.iloc[0]['MeasureDescription']
                if pd.notna(measure_desc) and str(measure_desc).strip():
                    return str(measure_desc).strip()
                
        return "Unknown measure"

    def _get_food_rows(self, food_ids: List[int]) -> pd.DataFrame:
        return self.pipeline.food_name_df[
            self.pipeline.food_name_df['FoodID'].isin(food_ids)
        ]

    def _get_nutrients(self, food_ids: List[int]) -> pd.DataFrame:
        merged = pd.merge(
            self.pipeline.nutrient_amount_df[
                self.pipeline.nutrient_amount_df['FoodID'].isin(food_ids)
            ],
            self.pipeline.nutrient_name_df,
            on='NutrientID',
            how='left'
        )
        return merged

    def _classify_food_to_ra_category(self, food_description: str, food_group_id: int) -> str:
        """Classify a food item to its appropriate RA category based on description and group
        
        Uses comprehensive pattern matching to align with Health Canada RA categories.
        """
        desc = food_description.upper()
        
        # Fruits (Group 9)
        if food_group_id == 9:
            # Check for specific fruit types first
            if any(berry in desc for berry in ['BLUEBERR', 'RASPBERR', 'BLACKBERR', 'STRAWBERR']):
                return 'berries'
            elif any(melon in desc for melon in ['WATERMELON', 'CANTALOUPE', 'HONEYDEW', 'MELON']):
                return 'melons'
            elif any(dried in desc for dried in ['DRIED', 'RAISIN', 'PRUNE', 'DATE', 'FIG', 'APRICOT']):
                return 'dried_fruit'
            elif 'JUICE' in desc and any(drink in desc for drink in ['JUICE', 'NECTAR', 'DRINK']):
                if any(ingredient in desc for ingredient in ['LEMON', 'LIME']):
                    return 'juice_ingredient'
                else:
                    return 'fruit_juice'
            elif any(garnish in desc for garnish in ['MARASCHINO', 'GARNISH', 'FLAVOUR']):
                return 'fruit_garnish'
            elif 'RELISH' in desc:
                return 'fruit_relishes'
            elif any(candied in desc for candied in ['CANDIED', 'PICKLED']):
                return 'candied_fruit'
            elif 'APPLESAUCE' in desc or ('APPLE' in desc and 'SAUCE' in desc):
                return 'applesauce'
            elif 'AVOCADO' in desc and 'INGREDIENT' in desc:
                return 'avocado_ingredient'
            elif any(ingredient in desc for ingredient in ['CRANBERR', 'LEMON', 'LIME']) and 'INGREDIENT' in desc:
                return 'cranberries_ingredient'
            elif 'CANNED' in desc or 'TINNED' in desc:
                return 'fruit_canned'
            else:
                return 'fruit_fresh'
        
        # Vegetables (Group 11)
        elif food_group_id == 11:
            if 'JUICE' in desc:
                return 'vegetable_juice'
            elif any(garnish in desc for garnish in ['PARSLEY', 'GARLIC', 'GARNISH', 'FLAVOUR']) and 'FRESH' in desc:
                return 'vegetables_garnish_fresh'
            elif any(garnish in desc for garnish in ['PARSLEY', 'GARLIC', 'GARNISH', 'FLAVOUR']) and 'CANNED' in desc:
                return 'vegetables_garnish_canned'
            elif any(chili in desc for chili in ['CHILI', 'GREEN ONION']):
                return 'chili_pepper'
            elif any(dried in desc for dried in ['SEAWEED', 'DEHYDRATED', 'DRIED']) and 'MUSHROOM' in desc:
                return 'seaweed_mushrooms'
            elif 'SPROUTS' in desc:
                return 'sprouts'
            elif 'OLIVES' in desc:
                return 'olives'
            elif any(pickled in desc for pickled in ['PICKLED', 'PICKLE', 'SUN-DRIED', 'PACKED IN OIL']):
                return 'pickled_vegetables'
            elif 'RELISH' in desc:
                return 'relish'
            elif 'PASTE' in desc:
                return 'vegetable_paste'
            elif any(sauce in desc for sauce in ['SAUCE', 'PUREE', 'PURÉE']):
                return 'vegetable_sauce'
            elif any(sauce in desc for sauce in ['SAUCE', 'GRAVY', 'CREAM', 'WITH']):
                if 'CANNED' in desc or 'TINNED' in desc:
                    return 'vegetables_with_sauce_canned'
                else:
                    return 'vegetables_with_sauce_fresh'
            elif 'CANNED' in desc or 'TINNED' in desc:
                return 'vegetables_canned'
            else:
                return 'vegetables_fresh'
        
        # Legumes (Group 16)
        elif food_group_id == 16:
            if 'TOFU' in desc or 'TEMPEH' in desc or 'BEAN CURD' in desc:
                return 'tofu'
            elif any(prep in desc for prep in ['COOKED', 'CANNED', 'BOILED', 'PREPARED']):
                return 'legumes_cooked'
            else:
                return 'legumes_dry'
        
        # Cereals/Grains (Groups 18, 20)
        elif food_group_id in [18, 20]:
            # Bakery products first
            if any(bread in desc for bread in ['BREAD', 'LOAF']) and not any(sweet in desc for sweet in ['SWEET', 'QUICK']):
                return 'bread'
            elif any(roll in desc for roll in ['ROLL', 'BUN', 'BISCUIT', 'SCONE', 'ENGLISH MUFFIN', 'CROISSANT', 'TORTILLA', 'PITA']):
                return 'rolls_buns'
            elif any(bagel in desc for bagel in ['BAGEL', 'NAAN', 'FLAT BREAD']):
                return 'bagels'
            elif any(brownie in desc for brownie in ['BROWNIE', 'DESSERT SQUARE', 'BAR']):
                return 'brownies_bars'
            elif 'CAKE' in desc:
                # Determine cake weight category
                if any(heavy in desc for heavy in ['CHEESE CAKE', 'PINEAPPLE', 'POUND']):
                    return 'cake_heavy'
                elif any(light in desc for light in ['ANGEL', 'CHIFFON', 'SPONGE']) and 'ICING' not in desc:
                    return 'cake_light'
                else:
                    return 'cake_medium'
            elif any(sweet in desc for sweet in ['DOUGHNUT', 'DANISH', 'SWEET ROLL', 'COFFEE CAKE', 'PASTRY']):
                return 'sweet_pastries'
            elif 'MUFFIN' in desc:
                return 'muffins'
            elif 'COOKIE' in desc or 'WAFER' in desc or 'GRAHAM' in desc:
                return 'cookies'
            elif 'CRACKER' in desc:
                if 'SNACK' in desc:
                    return 'snack_crackers'
                else:
                    return 'crackers'
            elif any(dry in desc for dry in ['MATZO', 'RUSK', 'DRY BREAD']):
                return 'dry_breads'
            elif 'TOASTER PASTRY' in desc:
                return 'toaster_pastries'
            elif 'ICE CREAM CONE' in desc:
                return 'ice_cream_cones'
            elif 'CROUTON' in desc:
                return 'croutons'
            elif any(pancake in desc for pancake in ['PANCAKE', 'WAFFLE', 'FRENCH TOAST']):
                return 'pancakes_waffles'
            elif any(bar in desc for bar in ['GRAIN BAR', 'GRANOLA BAR']):
                if any(filled in desc for filled in ['FILLING', 'COATING', 'COATED']):
                    return 'grain_bars_filled'
                else:
                    return 'grain_bars_plain'
            elif any(energy in desc for energy in ['ENERGY BAR', 'PROTEIN BAR']):
                return 'energy_bars'
            elif any(rice_cake in desc for rice_cake in ['RICE CAKE', 'CORN CAKE']):
                return 'rice_cakes'
            elif any(pie in desc for pie in ['PIE', 'TART', 'COBBLER', 'TURNOVER']):
                if 'CRUST' in desc:
                    return 'pie_crust'
                else:
                    return 'pies_tarts'
            elif 'PIZZA CRUST' in desc:
                return 'pizza_crust'
            elif 'TACO SHELL' in desc:
                return 'taco_shell'
            
            # Cereals and grains
            elif 'PASTA' in desc or 'NOODLE' in desc or 'SPAGHETTI' in desc or 'MACARONI' in desc:
                if any(fried in desc for fried in ['FRIED', 'CHOW MEIN']) and 'DRY' in desc:
                    return 'pasta_fried_dry'
                elif any(prep in desc for prep in ['COOKED', 'PREPARED', 'BOILED']):
                    return 'pasta_cooked'
                else:
                    return 'pasta_dry'
            elif any(grain in desc for grain in ['RICE', 'BARLEY', 'GRAIN']):
                if any(prep in desc for prep in ['COOKED', 'PREPARED', 'BOILED']):
                    return 'rice_grains_cooked'
                else:
                    return 'rice_grains_dry'
            elif 'CEREAL' in desc:
                if any(hot in desc for hot in ['OATMEAL', 'CREAM OF', 'HOT']):
                    if 'DRY' in desc or 'INSTANT' in desc:
                        return 'hot_cereal_dry'
                    else:
                        return 'hot_cereal_prepared'
                elif any(light in desc for light in ['PUFFED']) and not any(coated in desc for coated in ['COATED', 'GRANOLA']):
                    return 'ready_cereal_light'
                elif any(heavy in desc for heavy in ['GRANOLA', 'MUESLI', 'FRUIT', 'NUT']) or 'BISCUIT' in desc:
                    return 'ready_cereal_heavy'
                else:
                    return 'ready_cereal_medium'
            elif any(bran in desc for bran in ['BRAN', 'WHEAT GERM', 'FLAX', 'HEMP', 'CHIA']):
                return 'bran_wheat_germ'
            elif 'FLOUR' in desc or 'CORNMEAL' in desc:
                return 'flours'
            elif 'STARCH' in desc:
                return 'starch'
            elif 'STUFFING' in desc:
                return 'stuffing'
            else:
                return 'rice_grains_dry'  # Default for grain group
        
        # Dairy (Group 1)
        elif food_group_id == 1:
            if 'MILK' in desc:
                if any(condensed in desc for condensed in ['EVAPORATED', 'CONDENSED']):
                    return 'condensed_milk'
                else:
                    return 'milk'
            elif 'CHEESE' in desc:
                if 'COTTAGE' in desc:
                    return 'cottage_cheese'
                elif any(hard in desc for hard in ['PARMESAN', 'ROMANO', 'GRATED', 'HARD']):
                    return 'hard_cheese'
                elif any(ingredient in desc for ingredient in ['RICOTTA', 'INGREDIENT']):
                    return 'cheese_ingredient'
                else:
                    return 'cheese'
            elif any(yogurt in desc for yogurt in ['YOGURT', 'YOGHURT']):
                return 'yogurt'
            elif 'CREAM' in desc:
                if 'SOUR' in desc:
                    return 'sour_cream'
                elif any(whipped in desc for whipped in ['WHIPPED', 'AEROSOL']):
                    return 'whipped_cream'
                elif 'POWDER' in desc:
                    return 'cream_powder'
                else:
                    return 'cream'
            elif 'EGGNOG' in desc:
                return 'eggnog'
            elif any(fermented in desc for fermented in ['KEFIR', 'FERMENTED']):
                return 'fermented_dairy'
            elif any(shake in desc for shake in ['SHAKE', 'SMOOTHIE']):
                return 'shakes'
            elif any(fresh in desc for fresh in ['QUARK', 'FRESH CHEESE']):
                return 'quark_fresh_cheese'
            elif 'EGG' in desc:
                if any(mixture in desc for mixture in ['SCRAMBLED', 'OMELET', 'EGG FOO']):
                    return 'egg_mixtures'
                elif 'SUBSTITUTE' in desc:
                    return 'egg_substitutes'
                else:
                    return 'eggs'
            else:
                return 'milk'  # Default for dairy
        
        # Meat/Poultry (Groups 5, 7, 10, 13, 17)
        elif food_group_id in [5, 7, 10, 13, 17]:
            if any(processed in desc for processed in ['BACON', 'HAM', 'SAUSAGE', 'WIENER', 'BOLOGNA']):
                if any(breakfast in desc for breakfast in ['BREAKFAST', 'STRIP']):
                    if any(cooked in desc for cooked in ['COOKED', 'FRIED']):
                        return 'breakfast_strips_cooked'
                    else:
                        return 'breakfast_strips_uncooked'
                elif any(dried in desc for dried in ['JERKY', 'DRIED', 'SALAMI']):
                    return 'dried_meat'
                elif any(luncheon in desc for luncheon in ['BOLOGNA', 'LIVER SAUSAGE', 'HAM', 'SANDWICH']):
                    if any(cooked in desc for cooked in ['COOKED', 'SLICED']):
                        return 'luncheon_meat_cooked'
                    else:
                        return 'luncheon_meat_uncooked'
                elif any(sausage in desc for sausage in ['SAUSAGE', 'WIENER', 'BRATWURST', 'KIELBASA']):
                    if any(cooked in desc for cooked in ['COOKED', 'PRE-COOKED']):
                        return 'sausage_cooked'
                    else:
                        return 'sausage_uncooked'
                elif any(cured in desc for cured in ['CURED', 'SMOKED', 'PASTRAMI']):
                    if any(cooked in desc for cooked in ['COOKED', 'SMOKED']):
                        return 'cured_meat_cooked'
                    else:
                        return 'cured_meat_raw'
                elif 'CANNED' in desc:
                    return 'canned_meat'
                else:
                    return 'dried_meat'
            elif any(patty in desc for patty in ['PATTY', 'BURGER', 'MEATBALL', 'GROUND']):
                if any(cooked in desc for cooked in ['COOKED', 'FRIED', 'GRILLED']):
                    return 'patties_cooked'
                else:
                    return 'patties_raw'
            elif 'WITH SAUCE' in desc or 'BARBECUE' in desc or 'GRAVY' in desc:
                return 'meat_with_sauce'
            elif any(cooked in desc for cooked in ['COOKED', 'ROASTED', 'FRIED', 'BAKED', 'GRILLED', 'STEWED']):
                return 'meat_poultry_cooked'
            else:
                return 'meat_poultry_raw'
        
        # Fish/Shellfish (Group 15)
        elif food_group_id == 15:
            if any(small in desc for small in ['ANCHOV', 'CAVIAR']):
                return 'anchovies_caviar'
            elif 'WITH SAUCE' in desc or 'CREAM SAUCE' in desc:
                return 'fish_with_sauce'
            elif 'CANNED' in desc or 'TINNED' in desc:
                return 'fish_canned'
            elif any(smoked in desc for smoked in ['SMOKED', 'PICKLED']):
                return 'fish_smoked'
            elif any(cooked in desc for cooked in ['COOKED', 'BAKED', 'FRIED', 'GRILLED']):
                return 'fish_cooked'
            else:
                return 'fish_raw'
        
        # Nuts/Seeds (Group 12)
        elif food_group_id == 12:
            if any(butter in desc for butter in ['BUTTER', 'PEANUT BUTTER', 'ALMOND BUTTER']):
                return 'nut_butters'
            elif any(paste in desc for paste in ['PASTE', 'CREAM', 'MARZIPAN']):
                return 'nut_pastes'
            elif 'FLOUR' in desc:
                return 'nut_flours'
            elif 'SNACK' in desc:
                return 'nut_snacks'
            else:
                return 'nuts_seeds'
        
        # Beverages (Group 14)
        elif food_group_id == 14:
            if 'COFFEE' in desc:
                if 'ESPRESSO' in desc:
                    return 'espresso'
                else:
                    return 'coffee'
            elif any(tea in desc for tea in ['TEA', 'HERBAL']) and 'ICED' not in desc:
                return 'tea'
            elif any(hot in desc for hot in ['HOT CHOCOLATE', 'COCOA']):
                return 'hot_chocolate'
            elif any(alcoholic in desc for alcoholic in ['WINE', 'SANGRIA']):
                return 'wine'
            elif 'BEER' in desc:
                return 'beer'
            elif any(alcoholic in desc for alcoholic in ['COOLER', 'MIXED DRINK', 'ALCOHOLIC']):
                return 'alcoholic_mixed'
            else:
                return 'beverages'
        
        # Handle other groups that might contain combination dishes or special items
        elif food_group_id in [2, 3, 6, 8, 19]:  # Various processed food groups
            # Check for combination dishes
            if any(combo in desc for combo in ['CASSEROLE', 'STIR FRY', 'CHILI', 'STEW', 'HASH']):
                return 'combination_dish_large'
            elif any(combo in desc for combo in ['PIZZA', 'BURRITO', 'SANDWICH', 'TACO', 'QUICHE']):
                return 'combination_dish_medium'
            elif any(appetizer in desc for appetizer in ['ONION RING', 'EGG ROLL']):
                if 'SAUCE' in desc:
                    return 'hors_doeuvres_sauce'
                else:
                    return 'hors_doeuvres'
            elif 'SOUP' in desc:
                return 'soups'
            elif any(snack in desc for snack in ['CHIP', 'PRETZEL', 'POPCORN']):
                return 'chips_snacks'
            elif any(candy in desc for candy in ['CANDY', 'CHOCOLATE', 'SWEET']):
                if any(hard in desc for hard in ['HARD', 'MINT']):
                    if 'BREATH' in desc:
                        return 'breath_mints'
                    elif 'AFTER DINNER' in desc:
                        return 'after_dinner_mints'
                    else:
                        return 'hard_candies'
                else:
                    return 'candies'
            elif any(sauce in desc for sauce in ['SAUCE', 'DRESSING', 'CONDIMENT']):
                return 'dipping_sauce'
        
        # Default fallback
        return 'default'
    
    def _get_ra_amount(self, ra_category: str) -> float:
        """Get the reference amount in grams for a given RA category
        
        Handles special cases like sugar substitutes and converts mL to grams where needed.
        """
        ra_value = self.ra_lookup.get(ra_category, 100)  # Default 100g
        
        # Handle special cases
        if ra_value == 'equivalent_to_4g_sugar':
            return 4.0  # Sugar substitute equivalent
        
        ra_grams = float(ra_value)
        
        # Convert mL to grams for liquid categories (approximate density of 1 g/mL)
        # Most liquid categories are already specified in mL in Health Canada standards
        liquid_categories = [
            'fruit_juice', 'vegetable_juice', 'milk', 'coffee', 'tea', 'beverages',
            'wine', 'beer', 'alcoholic_mixed', 'hot_chocolate', 'espresso',
            'fruit_canned', 'vegetables_canned', 'vegetables_with_sauce_canned',
            'vegetables_garnish_canned', 'cream', 'condensed_milk', 'fermented_dairy',
            'shakes', 'eggnog', 'hot_cereal_prepared', 'legumes_cooked',
            'potatoes_canned', 'soups', 'dipping_sauce', 'main_sauce', 'minor_sauce',
            'major_condiments', 'minor_condiments', 'juice_ingredient', 'fruit_relishes',
            'relish', 'vegetable_paste', 'vegetable_sauce', 'syrup_topping', 'syrup_ingredient',
            'jams_jellies', 'liquid_candies'
        ]
        
        if ra_category in liquid_categories:
            return ra_grams  # Already accounted for in mL, treat as grams for RA calculation
        
        return ra_grams
    
    def aggregate_inputs(self, food_data: List[Tuple[int, float]]) -> Dict[str, float]:
        """Aggregate HEFI inputs from list of (food_id, amount_grams) tuples"""
        food_ids = [food_id for food_id, _ in food_data]
        amounts = [amount for _, amount in food_data]
        
        foods = self._get_food_rows(food_ids)
        nutrients = self._get_nutrients(food_ids)

        def sum_nutr_with_amounts(nutrient_name: str) -> float:
            """Sum nutrient values across all foods, scaled by amounts"""
            total = 0.0
            for i, (food_id, amount_g) in enumerate(food_data):
                food_nutrients = nutrients[nutrients['FoodID'] == food_id]
                # Use exact match for nutrient names
                rows = food_nutrients[food_nutrients['NutrientName'] == nutrient_name]
                if not rows.empty:
                    # Nutrient per 100g from CNF, scale by actual amount
                    nutrient_per_100g = float(rows['NutrientValue'].iloc[0])
                    total += (nutrient_per_100g * amount_g) / 100.0
            return total

        # Energy and nutrients scaled by actual amounts (using exact CNF nutrient names)
        energy_kcal = sum_nutr_with_amounts('ENERGY (KILOCALORIES)')
        sfa_g = sum_nutr_with_amounts('FATTY ACIDS, SATURATED, TOTAL')
        mufa_g = sum_nutr_with_amounts('FATTY ACIDS, MONOUNSATURATED, TOTAL')
        pufa_g = sum_nutr_with_amounts('FATTY ACIDS, POLYUNSATURATED, TOTAL')
        total_sugars_g = sum_nutr_with_amounts('SUGARS, TOTAL')
        sodium_mg = sum_nutr_with_amounts('SODIUM')

        # Approximated free sugars: default to total sugars due to lack of database; can be improved later
        free_sugars_g = total_sugars_g

        # Calculate proper Reference Amounts using Health Canada standards
        vf_ra = 0.0
        whole_grains_ra = 0.0
        total_grains_ra = 0.0
        protein_foods_ra = 0.0
        plant_protein_foods_ra = 0.0
        total_beverages_g = 0.0
        recommended_beverages_g = 0.0
        total_foods_ra = 0.0
        
        for i, (food_id, amount_g) in enumerate(food_data):
            food_row = foods[foods['FoodID'] == food_id]
            if food_row.empty:
                continue
                
            food_group_id = int(food_row['FoodGroupID'].iloc[0])
            food_description = str(food_row['FoodDescription'].iloc[0])
            
            # Classify food to RA category
            ra_category = self._classify_food_to_ra_category(food_description, food_group_id)
            ra_amount_g = self._get_ra_amount(ra_category)
            
            # Calculate RAs for this food item
            food_ra = amount_g / ra_amount_g
            
            # Vegetables and Fruits
            if food_group_id in [self.GROUP_FRUITS, self.GROUP_VEGETABLES]:
                vf_ra += food_ra
            
            # Grains
            elif food_group_id in self.GROUP_CEREALS_GRAINS_PASTA:
                total_grains_ra += food_ra
                # Whole grain detection
                desc_upper = food_description.upper()
                whole_keywords = ['WHOLE', 'BROWN', 'BRAN', 'WHEAT GERM', 'OAT']
                if any(keyword in desc_upper for keyword in whole_keywords):
                    whole_grains_ra += food_ra
            
            # Protein foods
            elif food_group_id in (list(self.GROUP_MEAT_PORK_BEEF_POULTRY) + 
                                 [self.GROUP_FINISH_SHELLFISH, self.GROUP_DAIRY_EGGS, self.GROUP_LEGUMES]):
                protein_foods_ra += food_ra
            
            # Plant protein foods
            elif food_group_id in [self.GROUP_LEGUMES, self.GROUP_NUTS_SEEDS]:
                plant_protein_foods_ra += food_ra
            
            # Beverages (convert back to grams for HEFI calculation)
            elif food_group_id == self.GROUP_BEVERAGES:
                total_beverages_g += amount_g
                # Recommended beverages detection
                desc_upper = food_description.upper()
                recommended_keywords = ['WATER', 'MILK', 'SOY DRINK', 'SOY MILK', 'UNSWEETENED']
                if any(keyword in desc_upper for keyword in recommended_keywords):
                    recommended_beverages_g += amount_g
            
            # Total foods RA (excluding beverages and fats/oils)
            if food_group_id not in [self.GROUP_BEVERAGES, 4]:  # 4 = fats/oils group
                total_foods_ra += food_ra

        return {
            'total_foods_ra': float(total_foods_ra),
            'vf_ra': float(vf_ra),
            'whole_grains_ra': float(whole_grains_ra),
            'total_grains_ra': float(total_grains_ra),
            'protein_foods_ra': float(protein_foods_ra),
            'plant_protein_foods_ra': float(plant_protein_foods_ra),
            'total_beverages_g': float(total_beverages_g),
            'recommended_beverages_g': float(recommended_beverages_g),
            'energy_kcal': float(energy_kcal),
            'sfa_g': float(sfa_g),
            'mufa_g': float(mufa_g),
            'pufa_g': float(pufa_g),
            'free_sugars_g': float(free_sugars_g),
            'sodium_mg': float(sodium_mg),
        }


