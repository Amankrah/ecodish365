import os
import sys
import json
from typing import Dict, FrozenSet, List, Tuple
import pandas as pd

try:
    from rust_core import hefi as _rust_hefi
except ImportError as exc:  # pragma: no cover - environment error
    raise ImportError(
        "rust_core.hefi is not available. Build the Rust extension with:\n"
        "    cd backend/rust_core && maturin develop --release\n"
        f"Underlying error: {exc}"
    ) from exc


# Use the single process-wide CNF pipeline. See backend/api/cnf_cache.py.
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # -> backend
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
from api.cnf_cache import get_api_cnf_pipeline
from api.cnf_data_pipeline import CNFDataPipeline  # re-exported for type annotations


def get_shared_cnf_pipeline(cnf_dir: str) -> CNFDataPipeline:
    """Backwards-compatible shim that returns the shared pipeline.

    The `cnf_dir` argument is ignored — the shared instance is bound to
    `settings.CNF_FOLDER` at first use. Kept so older call sites still work.
    """
    return get_api_cnf_pipeline()


class HEFICNFIntegrator:
    """
    Extracts HEFI-relevant totals and nutrients from CNF for a list of FoodIDs with amounts.
    This provides RA-based totals for food categories and beverage grams, plus nutrients and energy.
    Uses Health Canada's official Reference Amounts from nutrition_reference_amounts.json.
    """

    # The CNF food-group constants that used to live here are now encoded
    # in Rust (`backend/rust_core/src/hefi/aggregator.rs::groups`), which
    # is the only place they're consumed.

    # Nutrients HEFI cares about — exact CNF `NutrientName` strings. Used to
    # filter the nutrient dataframe before handing it to Rust. The Rust
    # aggregator looks them up by these exact keys.
    HEFI_NUTRIENTS: FrozenSet[str] = frozenset({
        'ENERGY (KILOCALORIES)',
        'FATTY ACIDS, SATURATED, TOTAL',
        'FATTY ACIDS, MONOUNSATURATED, TOTAL',
        'FATTY ACIDS, POLYUNSATURATED, TOTAL',
        'SUGARS, TOTAL',
        'SODIUM',
    })

    def __init__(self, cnf_dir: str):
        self.pipeline = get_shared_cnf_pipeline(cnf_dir)
        self.cnf_dir = cnf_dir

        # Load CNF reference data
        self._load_cnf_reference_data()
        
        # Load Health Canada Reference Amounts
        self._load_reference_amounts()

        # Normalize the RA lookup once: collapse the `equivalent_to_4g_sugar`
        # sentinel and float-cast every value. The result never changes after
        # load, so callers hand this dict straight to Rust without rebuilding
        # it per request.
        self._ra_lookup_numeric: Dict[str, float] = {
            k: (4.0 if v == 'equivalent_to_4g_sugar' else float(v))
            for k, v in self.ra_lookup.items()
        }

    def _load_cnf_reference_data(self):
        """Expose the shared pipeline's conversion_factor and measure_name frames.

        Both are guaranteed to be loaded by `CNFDataPipeline.load_all_dataframes`
        now, so no per-instance reloading is needed.
        """
        self.conversion_factors_df = self.pipeline.conversion_factor_df
        self.measure_names_df = self.pipeline.measure_name_df
    
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
        """Classify a food item to its appropriate RA category.

        Delegates to `rust_core.hefi.classify_food_to_ra_category` — the
        340-line pattern-matching chain was ported mechanically to Rust
        and diff-tested against all 5,691 CNF rows (0 mismatches).
        """
        return _rust_hefi.classify_food_to_ra_category(food_description, int(food_group_id))

    
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
        """Aggregate HEFI inputs from list of (food_id, amount_grams) tuples.

        The pandas I/O (food + nutrient table lookups) stays here. The actual
        per-food loop — nutrient summation, RA classification, bucketing — runs
        in Rust via `rust_core.hefi.aggregate_inputs`. Pandas is indexed once
        with a groupby instead of an O(F*N) nested filter.
        """
        if not food_data:
            return {
                'total_foods_ra': 0.0, 'vf_ra': 0.0, 'whole_grains_ra': 0.0,
                'total_grains_ra': 0.0, 'protein_foods_ra': 0.0,
                'plant_protein_foods_ra': 0.0, 'total_beverages_g': 0.0,
                'recommended_beverages_g': 0.0, 'energy_kcal': 0.0,
                'sfa_g': 0.0, 'mufa_g': 0.0, 'pufa_g': 0.0,
                'free_sugars_g': 0.0, 'sodium_mg': 0.0,
            }

        # Food row lookup: single pass over food_name_df, no per-food filter.
        foods_df = self._get_food_rows([food_id for food_id, _ in food_data])
        food_lookup: Dict[int, Tuple[int, str]] = {
            int(row.FoodID): (int(row.FoodGroupID), str(row.FoodDescription))
            for row in foods_df.itertuples(index=False)
        }

        # Nutrient lookup comes from the shared, pre-indexed
        # `CNFDataPipeline.nutrients_by_food` built once at pipeline load.
        # Per-request work is reduced to slicing the six HEFI nutrients out
        # of the already-materialized food-level sub-dict.
        global_nutrients = self.pipeline.nutrients_by_food
        nutrients_by_food: Dict[int, Dict[str, float]] = {}
        batch: List[Tuple[int, float, int, str]] = []
        for food_id, amount_g in food_data:
            food_row = food_lookup.get(int(food_id))
            if food_row is None:
                # Matches the old `if food_row.empty: continue`.
                continue
            gid, desc = food_row
            batch.append((int(food_id), float(amount_g), gid, desc))

            food_nutrients = global_nutrients.get(int(food_id))
            if food_nutrients:
                # Only forward the six HEFI-relevant nutrients across the FFI
                # boundary. Rebuilt per food_id seen (not per entry in
                # food_data), so duplicate food_ids in one meal cost nothing.
                if int(food_id) not in nutrients_by_food:
                    nutrients_by_food[int(food_id)] = {
                        name: food_nutrients[name]
                        for name in self.HEFI_NUTRIENTS
                        if name in food_nutrients
                    }

        return dict(_rust_hefi.aggregate_inputs(batch, nutrients_by_food, self._ra_lookup_numeric))

