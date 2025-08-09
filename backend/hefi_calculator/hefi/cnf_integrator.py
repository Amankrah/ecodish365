import os
import sys
from typing import Dict, List, Optional
import pandas as pd


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
    Extracts HEFI-relevant totals and nutrients from CNF for a list of FoodIDs.
    This provides RA-based totals for foods categories and beverage grams, plus nutrients and energy.
    NOTE: CNF does not provide official Reference Amounts; we approximate by using 100 g as 1 RA
    unless a measure is present. This can be replaced with Health Canada's RA database when available.
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

        # Nutrient name -> canonical mapping
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
            
        # Merge with measure descriptions to get meaningful names
        # The CONVERSION_FACTOR.csv has empty MeasureDescription column,
        # so we need to join with MEASURE_NAME.csv using MeasureID
        if not self.measure_names_df.empty:
            food_factors = food_factors.merge(
                self.measure_names_df[['MeasureID', 'MeasureDescription']], 
                on='MeasureID', 
                how='left',
                suffixes=('', '_from_measure')
            )
            
            # Use the MeasureDescription from MEASURE_NAME.csv, not CONVERSION_FACTOR.csv
            if 'MeasureDescription_from_measure' in food_factors.columns:
                food_factors['MeasureDescription'] = food_factors['MeasureDescription_from_measure']
        
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
        ]
        
        if food_factors.empty:
            return "Unknown measure"
            
        # Merge with measure descriptions - same logic as _get_best_conversion_factor
        food_factors = food_factors.merge(
            self.measure_names_df[['MeasureID', 'MeasureDescription']], 
            on='MeasureID', 
            how='left',
            suffixes=('', '_from_measure')
        )
        
        # Use the MeasureDescription from MEASURE_NAME.csv, not CONVERSION_FACTOR.csv
        if 'MeasureDescription_from_measure' in food_factors.columns:
            food_factors['MeasureDescription'] = food_factors['MeasureDescription_from_measure']
        
        # Find the measure that matches the conversion factor
        for _, row in food_factors.iterrows():
            if abs(float(row['ConversionFactorValue']) - conversion_factor) < 0.001:
                measure_desc = row.get('MeasureDescription', '')
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

    def aggregate_inputs(self, food_ids: List[int]) -> Dict[str, float]:
        foods = self._get_food_rows(food_ids)
        nutrients = self._get_nutrients(food_ids)

        def sum_nutr_with_portions(name_substr: str) -> float:
            total = 0.0
            for food_id in food_ids:
                food_nutrients = nutrients[nutrients['FoodID'] == food_id]
                rows = food_nutrients[food_nutrients['NutrientName'].str.contains(name_substr, case=False, na=False)]
                if not rows.empty:
                    # Get dynamic conversion factor from CNF database
                    factor = self._get_best_conversion_factor(food_id)
                    total += float(rows['NutrientValue'].iloc[0]) * factor
            return total

        # Energy and nutrients with proper portion control
        energy_kcal = sum_nutr_with_portions('ENERGY.*KILOCALORIES')
        sfa_g = sum_nutr_with_portions('FATTY ACIDS, SATURATED, TOTAL')
        mufa_g = sum_nutr_with_portions('FATTY ACIDS, MONOUNSATURATED, TOTAL')
        pufa_g = sum_nutr_with_portions('FATTY ACIDS, POLYUNSATURATED, TOTAL')
        total_sugars_g = sum_nutr_with_portions('SUGARS, TOTAL')
        sodium_mg = sum_nutr_with_portions('SODIUM')

        # Approximated free sugars: default to total sugars due to lack of database; can be improved later
        free_sugars_g = total_sugars_g

        # Compute RA approximations by counting items and using 100 g as 1 RA proxy
        # If/when RA database is available, replace with category-specific RAs.
        def count_group(group_id) -> int:
            if isinstance(group_id, set):
                return int(foods['FoodGroupID'].isin(group_id).sum())
            else:
                return int((foods['FoodGroupID'] == group_id).sum())

        vf_ra = count_group(self.GROUP_FRUITS) + count_group(self.GROUP_VEGETABLES)
        whole_grains_ra = 0
        total_grains_ra = count_group(self.GROUP_CEREALS_GRAINS_PASTA)
        protein_foods_ra = (
            sum(int((foods['FoodGroupID'] == gid).sum()) for gid in self.GROUP_MEAT_PORK_BEEF_POULTRY)
            + count_group(self.GROUP_FINISH_SHELLFISH) + count_group(self.GROUP_DAIRY_EGGS) + count_group(self.GROUP_LEGUMES)
        )
        plant_protein_foods_ra = count_group(self.GROUP_LEGUMES) + count_group(self.GROUP_NUTS_SEEDS)

        # Heuristic whole grain detection inside cereals/grains: check description keywords
        cereals = foods[foods['FoodGroupID'].isin(self.GROUP_CEREALS_GRAINS_PASTA)]
        if not cereals.empty:
            whole_keywords = ['WHOLE', 'BROWN', 'BRAN', 'WHEAT GERM', 'OATS']
            whole_mask = cereals['FoodDescription'].str.upper().str.contains('|'.join(whole_keywords), na=False)
            whole_grains_ra = int(whole_mask.sum())
            total_grains_ra = int(len(cereals))

        # Beverages grams: sum an assumed 250 g per beverage record as a placeholder
        beverages = foods[foods['FoodGroupID'] == self.GROUP_BEVERAGES]
        total_beverages_g = float(len(beverages) * 250.0)
        # Recommended beverages: water, plain milk, fortified soy; approximate via keywords
        recommended_keywords = ['WATER', 'MILK', 'SOY DRINK', 'SOY MILK', 'UNSWEETENED']
        recommended_mask = beverages['FoodDescription'].str.upper().str.contains('|'.join(recommended_keywords), na=False)
        recommended_beverages_g = float(recommended_mask.sum() * 250.0)

        # Total foods RA proxy: sum of all food items excluding culinary ingredients (oils/spreads) and beverages w/o protein
        excluded_groups = {self.GROUP_BEVERAGES, 4}  # Beverages and fats/oils not counted as foods per doc
        total_foods_ra = int((~foods['FoodGroupID'].isin(excluded_groups)).sum())

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


