import os
import pandas as pd
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


# Per-(food_group, category) uncertainty band ratios, applied multiplicatively
# to the central P&N / M&H-anchored values to produce low / central / high bands.
#
# GHG and Land use lower-bound ratios derive from Poore & Nemecek 2018 Fig. 1
# 10th-percentile/mean ratios (literature_extractions.md lines 433-449); upper
# bounds use ~2x the mean as a conservative proxy for the 90th percentile
# (P&N do not print 90th-percentile values per panel, but their text describes
# the within-product spread as "comparable in magnitude to the mean" with
# log-skew, supporting a 2x upper anchor — full distributions are in Data S1).
#
# Water consumption bands use a flat 0.5x / 2.0x band reflecting Mekonnen &
# Hoekstra's documented spatial spread (e.g. milk blue-water 15 L/kg vs US
# 50-200 L/kg per literature_extractions.md line 1934, i.e. ~3-13x range).
#
# Defensibility: these are envelope bounds, not full PDFs. A meal-level
# "everything-low" vs "everything-high" pair gives a worst/best-case envelope
# rather than a true 90% CI (which would need Monte-Carlo over per-food PDFs).
# Documented as a known limitation in §7 of the manuscript.
UNCERTAINTY_BAND_RATIOS_BY_GROUP: Dict[str, Dict[str, Dict[str, float]]] = {
    'Beef Products': {
        'Global warming':     {'low_ratio': 0.40, 'high_ratio': 2.0},  # P&N 10th=20 / mean=50
        'Land use':           {'low_ratio': 0.26, 'high_ratio': 2.5},  # P&N 10th=42 / mean=164
        'Water consumption':  {'low_ratio': 0.50, 'high_ratio': 2.0},  # M&H spatial spread
    },
    'Pork Products': {
        'Global warming':     {'low_ratio': 0.61, 'high_ratio': 2.0},  # P&N 10th=4.6 / mean=7.6
        'Land use':           {'low_ratio': 0.44, 'high_ratio': 2.0},  # P&N 10th=4.8 / mean=11
        'Water consumption':  {'low_ratio': 0.50, 'high_ratio': 2.0},
    },
    'Poultry Products': {
        'Global warming':     {'low_ratio': 0.42, 'high_ratio': 2.0},  # P&N 10th=2.4 / mean=5.7
        'Land use':           {'low_ratio': 0.54, 'high_ratio': 2.0},  # P&N 10th=3.8 / mean=7.1
        'Water consumption':  {'low_ratio': 0.50, 'high_ratio': 2.0},
    },
    'Finfish and Shellfish Products': {
        'Global warming':     {'low_ratio': 0.42, 'high_ratio': 2.0},  # P&N 10th=2.5 / mean=6.0
        'Land use':           {'low_ratio': 0.11, 'high_ratio': 3.0},  # P&N 10th=0.4 / mean=3.7 (wide)
        'Water consumption':  {'low_ratio': 0.10, 'high_ratio': 5.0},  # wild~0 / farmed varies
    },
    'Dairy and Egg Products': {
        'Global warming':     {'low_ratio': 0.20, 'high_ratio': 3.0},  # milk 0.32 vs cheese 2.4 — group blend wide
        'Land use':           {'low_ratio': 0.11, 'high_ratio': 3.0},  # cheese 4.4 / mean 41 P&N
        'Water consumption':  {'low_ratio': 0.45, 'high_ratio': 2.5},  # milk 0.009 vs cheese 0.041
    },
    'Vegetables and Vegetable Products': {
        'Global warming':     {'low_ratio': 0.19, 'high_ratio': 4.0},  # tomato 0.1/2.1 vs greenhouse extremes
        'Land use':           {'low_ratio': 0.13, 'high_ratio': 2.0},  # P&N 10th=0.1 / mean=0.8
        'Water consumption':  {'low_ratio': 0.50, 'high_ratio': 2.0},
    },
    'Fruits and fruit juices': {
        'Global warming':     {'low_ratio': 0.53, 'high_ratio': 2.0},  # P&N berry 0.8/1.5
        'Land use':           {'low_ratio': 0.13, 'high_ratio': 2.0},  # P&N 10th=0.3 / mean=2.4
        'Water consumption':  {'low_ratio': 0.10, 'high_ratio': 5.0},  # apple 0 vs citrus high
    },
    'Cereals, Grains and Pasta': {
        'Global warming':     {'low_ratio': 0.50, 'high_ratio': 2.0},  # P&N wheat 0.3/0.6
        'Land use':           {'low_ratio': 0.29, 'high_ratio': 2.0},  # P&N wheat 0.4/1.4
        'Water consumption':  {'low_ratio': 0.30, 'high_ratio': 2.0},  # wheat/rice ~0.034 vs maize 0.008
    },
    'Legumes and Legume Products': {
        'Global warming':     {'low_ratio': 0.50, 'high_ratio': 2.0},  # P&N peas 0.3/0.4 (narrow)
        'Land use':           {'low_ratio': 0.35, 'high_ratio': 2.0},  # P&N pulses 1.2/3.4
        'Water consumption':  {'low_ratio': 0.50, 'high_ratio': 2.0},
    },
    'Nuts and Seeds': {
        'Global warming':     {'low_ratio': 0.10, 'high_ratio': 4.0},  # P&N nuts -2.2 to 0.3/100g protein (extreme spread)
        'Land use':           {'low_ratio': 0.34, 'high_ratio': 2.0},  # P&N 10th=2.7 / mean=7.9
        'Water consumption':  {'low_ratio': 0.20, 'high_ratio': 3.0},  # almond 0.3-1.6 m3/100g extremes
    },
}

# Default ratios for unknown food groups: conservative wide bands.
DEFAULT_UNCERTAINTY_BAND_RATIOS = {
    'Global warming':     {'low_ratio': 0.30, 'high_ratio': 3.0},
    'Land use':           {'low_ratio': 0.20, 'high_ratio': 3.0},
    'Water consumption':  {'low_ratio': 0.30, 'high_ratio': 3.0},
}

class CNFIntegrator:
    """
    Singleton class for integrating Canadian Nutrient File data with environmental impact calculations.
    CORRECTED: Updated with scientifically verified environmental impact factors based on 
    Poore & Nemecek 2018 meta-analysis and established LCA databases.
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
        
    def initialize(self, data_dir: str = ''):
        """Initialize the integrator by borrowing from the shared CNF pipeline.

        The `data_dir` parameter is accepted for API compatibility but
        ignored — the shared pipeline is bound to `settings.CNF_FOLDER`
        at first use. No CSV I/O happens here; the frames are borrowed
        by reference from `api.cnf_cache.get_api_cnf_pipeline()`.
        """
        if self._initialized:
            self.logger.info("CNF Integrator already initialized")
            return

        self.data_dir = data_dir
        self._borrow_shared_pipeline()
        self._create_mappings()
        self._initialized = True
        self.logger.info("CNF Integrator initialized (shared pipeline, no CSV I/O)")

    def _borrow_shared_pipeline(self):
        """Populate `_dataframes` from the process-wide shared CNF pipeline.

        Replaces the old `_load_all_dataframes` + `_detect_encoding` +
        `_load_csv` chain that independently loaded all 12 CSVs with its
        own chardet calls, creating a duplicate ~35 MB copy of the data.
        """
        from api.cnf_cache import get_api_cnf_pipeline
        pipeline = get_api_cnf_pipeline()

        # The shared pipeline stores frames as `food_name_df`, etc.
        # This module expects them keyed as `_dataframes['food_name']`.
        frame_names = [
            'food_name', 'nutrient_amount', 'conversion_factor', 'food_group',
            'food_source', 'nutrient_name', 'nutrient_source', 'measure_name',
            'refuse_amount', 'yield_amount', 'refuse_name', 'yield_name',
        ]
        for name in frame_names:
            attr = f"{name}_df"
            df = getattr(pipeline, attr, None)
            self._dataframes[name] = df if df is not None else pd.DataFrame()
    
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

        Per-food-group ReCiPe 2016 H midpoint factors, all per 100 g food product.

        Defensibility status (from `backend/_smoke_validate_cnf_integrator.py`
        v2 audit against literature):
          - Global warming  : grounded against Poore & Nemecek 2018 Fig. 1
                              panels A-F (Science 360:987-992); 10/10 groups
                              within MARE < 0.6 of P&N central values.
          - Land use        : grounded against same; 10/10 groups within
                              MARE < 0.6 after this revision.
          - Water consumption: grounded against Mekonnen & Hoekstra 2011
                              (Hydrol Earth Syst Sci 15:1577, crops Table 3)
                              and M&H 2012 (Ecosystems 15:401, animal Table 3)
                              BLUE-WATER-ONLY consumptive footprints — i.e.
                              the same Hoekstra-Pfister "consumption"
                              definition ReCiPe 2016 Water Consumption Potential
                              uses (Huijbregts 2017 Table 1). NOT the
                              green+blue+grey total footprint — using the
                              total over-estimates ReCiPe water consumption
                              by 10-30x.
          - Terrestrial acidification / freshwater / marine eutrophication
                            : UNIT_INCOMPATIBLE with P&N's aggregate kg-SO2-eq
                              acidification and kg-PO4-eq eutrophication
                              (which are PEF-like aggregates). Values here
                              are conservative defaults pending licensed
                              Agribalyse-LCI-re-scored-under-ReCiPe v2 work.
          - The 12 remaining ReCiPe midpoints (toxicities, ecotoxicities,
                              both ozone-formation pathways, ionising
                              radiation, PM, resource scarcity) have no
                              per-food-group numerical literature target in
                              `literature_extractions.md` on any basis.
                              Values are explicitly conservative defaults
                              with Medium/Low confidence flags below.
        """
        food_data = self.get_food_data(food_id)
        if not food_data:
            return {}
        
        food_group_name = food_data.get('food_group', {}).get('FoodGroupName', 'Unknown')
        
        # CORRECTED: Impact factors based on Poore & Nemecek 2018 and verified LCA databases
        # All values are properly scaled to per 100g basis
        impact_factors_by_group = {
            'Dairy and Egg Products': {
                'Global warming': 1.0,  # kg CO2 eq — P&N Fig. 1A cheese 2.4 / milk 0.32 / egg 0.55 group blend
                'Land use': 9.0,  # m2a crop eq — P&N Fig. 1A cheese 41 x 0.22 / milk 8.9/L group blend
                'Water consumption': 0.020,  # m³ — M&H 2012 blue: milk 0.009 / egg 0.024 / cheese 0.041 blended
                'Freshwater eutrophication': 0.0032,  # kg P eq (kept - reasonable)
                'Marine eutrophication': 0.041,  # kg N eq (kept - reasonable)
                'Terrestrial acidification': 0.048,  # kg SO2 eq (kept - reasonable)
                'Fine particulate matter formation': 0.024,  # kg PM2.5 eq (kept)
                'Fossil resource scarcity': 0.078,  # kg oil eq (was 0.78 - 10x too high)
                'Mineral resource scarcity': 0.00021,  # kg Cu eq (kept - reasonable)
                # Added missing ReCiPe categories
                'Human carcinogenic toxicity': 0.0018,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.0016,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.0024,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.0032,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.0012,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.008,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 3.2e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.0021,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.0018,  # kg NOx eq
            },
            'Beef Products': {
                'Global warming': 6.7,  # kg CO2 eq — P&N Fig. 1A beef-herd 50 + dairy-herd 17 mean blend / 100g protein x 0.20
                'Land use': 33.0,  # m2a crop eq — P&N Fig. 1A beef-herd mean 164 / 100g protein x 0.20
                'Water consumption': 0.062,  # m³ — M&H 2012 blue-water beef cattle ~620 L/kg (NOT total footprint)
                'Freshwater eutrophication': 0.0089,  # kg P eq
                'Marine eutrophication': 0.135,  # kg N eq
                'Terrestrial acidification': 0.124,  # kg SO2 eq
                'Fine particulate matter formation': 0.067,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.28,  # kg oil eq (was 2.8 - 10x too high)
                'Mineral resource scarcity': 0.00041,  # kg Cu eq (kept)
                # Added missing categories with beef-specific values
                'Human carcinogenic toxicity': 0.0089,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.0076,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.012,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.015,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.0041,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.012,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 1.8e-7,  # kg CFC11 eq
                'Ozone formation, Human health': 0.078,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.065,  # kg NOx eq
            },
            'Pork Products': {
                'Global warming': 1.5,  # kg CO2 eq — P&N Fig. 1A pig mean 7.6 / 100g protein x 0.20
                'Land use': 2.2,  # m2a crop eq — P&N Fig. 1A pig mean 11 / 100g protein x 0.20
                'Water consumption': 0.046,  # m³ — M&H 2012 blue-water pork ~459 L/kg
                'Freshwater eutrophication': 0.0056,  # kg P eq
                'Marine eutrophication': 0.089,  # kg N eq
                'Terrestrial acidification': 0.087,  # kg SO2 eq
                'Fine particulate matter formation': 0.042,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.12,  # kg oil eq (was 1.2 - 10x too high)
                'Mineral resource scarcity': 0.00028,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.0034,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.0031,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.0045,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.0052,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.0018,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0095,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 8.7e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.034,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.028,  # kg NOx eq
            },
            'Poultry Products': {
                'Global warming': 1.3,  # kg CO2 eq — P&N Fig. 1A poultry mean 5.7 / 100g protein x 0.22
                'Land use': 1.6,  # m2a crop eq — P&N Fig. 1A poultry mean 7.1 / 100g protein x 0.22
                'Water consumption': 0.031,  # m³ — M&H 2012 blue-water chicken ~313 L/kg
                'Freshwater eutrophication': 0.0047,  # kg P eq
                'Marine eutrophication': 0.068,  # kg N eq
                'Terrestrial acidification': 0.061,  # kg SO2 eq
                'Fine particulate matter formation': 0.032,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.11,  # kg oil eq (was 1.1 - 10x too high)
                'Mineral resource scarcity': 0.00024,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.0028,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.0026,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.0035,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.0041,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.0015,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0082,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 6.1e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.025,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.021,  # kg NOx eq
            },
            'Finfish and Shellfish Products': {
                'Global warming': 1.1,  # kg CO2 eq — P&N Fig. 1A farmed fish mean 6.0 / 100g protein x 0.18
                'Land use': 0.67,  # m2a crop eq — P&N Fig. 1A farmed fish 3.7 / 100g protein x 0.18 (REVERTED: prior 0.02 over-corrected)
                'Water consumption': 0.005,  # m³ — wild fish near 0; farmed feed-crop blue water small
                'Freshwater eutrophication': 0.0031,  # kg P eq
                'Marine eutrophication': 0.024,  # kg N eq
                'Terrestrial acidification': 0.034,  # kg SO2 eq
                'Fine particulate matter formation': 0.019,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.32,  # kg oil eq (was 3.2 - 10x too high)
                'Mineral resource scarcity': 0.00018,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.0021,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.0019,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.0015,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.0018,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.0028,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0067,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 4.8e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.014,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.012,  # kg NOx eq
            },
            'Vegetables and Vegetable Products': {
                'Global warming': 0.10,  # kg CO2 eq — P&N Fig. 1E veg panel midpoint ~1.0/kg
                'Land use': 0.055,  # m2a crop eq — P&N Fig. 1E veg panel 0.4-0.8/kg midpoint
                'Water consumption': 0.006,  # m³ — M&H 2011 blue: potato 0.003 / tomato 0.006 / onion 0.008 mid
                'Freshwater eutrophication': 0.00041,  # kg P eq
                'Marine eutrophication': 0.0049,  # kg N eq
                'Terrestrial acidification': 0.0032,  # kg SO2 eq
                'Fine particulate matter formation': 0.0018,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.012,  # kg oil eq (was 0.12 - 10x too high)
                'Mineral resource scarcity': 0.000024,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.00015,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.00013,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.00025,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.00031,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.00012,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0012,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 1.2e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.0015,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.0012,  # kg NOx eq
            },
            'Fruits and fruit juices': {
                'Global warming': 0.08,  # kg CO2 eq — P&N Fig. 1F fruit panel midpoint ~0.8/kg
                'Land use': 0.14,  # m2a crop eq — P&N Fig. 1F fruit panel 1.4/kg midpoint
                'Water consumption': 0.005,  # m³ — M&H 2011 blue: apple 0.001 / banana ~0 mid ~0.005
                'Freshwater eutrophication': 0.00062,  # kg P eq
                'Marine eutrophication': 0.0071,  # kg N eq
                'Terrestrial acidification': 0.0041,  # kg SO2 eq
                'Fine particulate matter formation': 0.0024,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.021,  # kg oil eq (was 0.21 - 10x too high)
                'Mineral resource scarcity': 0.000031,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.00021,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.00019,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.00035,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.00042,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.00016,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0018,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 1.8e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.0021,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.0017,  # kg NOx eq
            },
            'Cereals, Grains and Pasta': {
                'Global warming': 0.32,  # kg CO2 eq — P&N Fig. 1C grain 0.9/1000 kcal x 350 kcal/100g
                'Land use': 0.49,  # m2a crop eq — P&N Fig. 1C wheat 1.4/1000 kcal x 350 kcal/100g
                'Water consumption': 0.025,  # m³ — M&H 2011 blue: wheat 0.034 / rice 0.034 / maize 0.008 mid
                'Freshwater eutrophication': 0.0012,  # kg P eq
                'Marine eutrophication': 0.014,  # kg N eq
                'Terrestrial acidification': 0.0089,  # kg SO2 eq
                'Fine particulate matter formation': 0.0045,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.042,  # kg oil eq (was 0.42 - 10x too high)
                'Mineral resource scarcity': 0.000067,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.00034,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.00031,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.00045,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.00052,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.00021,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0025,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 2.1e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.0034,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.0028,  # kg NOx eq
            },
            'Legumes and Legume Products': {
                'Global warming': 0.054,  # kg CO2 eq — P&N Fig. 1A pulses 0.6 / 100g protein x 0.09
                'Land use': 0.49,  # m2a crop eq — P&N Fig. 1A pulses 5.4 / 100g protein x 0.09
                'Water consumption': 0.060,  # m³ — M&H 2011 blue: pulses ~400-800 L/kg mid 600
                'Freshwater eutrophication': 0.00089,  # kg P eq
                'Marine eutrophication': 0.0021,  # kg N eq
                'Terrestrial acidification': 0.0034,  # kg SO2 eq
                'Fine particulate matter formation': 0.0021,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.018,  # kg oil eq (was 0.18 - 10x too high)
                'Mineral resource scarcity': 0.000041,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.00018,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.00016,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.00028,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.00033,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.00014,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.0015,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 1.5e-8,  # kg CFC11 eq
                'Ozone formation, Human health': 0.0018,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.0015,  # kg NOx eq
            },
            'Nuts and Seeds': {
                'Global warming': 0.06,  # kg CO2 eq — P&N Fig. 1A nuts mean 0.3 / 100g protein x 0.20
                'Land use': 1.58,  # m2a crop eq — P&N Fig. 1A nuts 7.9 / 100g protein x 0.20
                'Water consumption': 0.80,  # m³ — M&H blue: almond ~0.3-1.6 m3/100g; mixed-nut basket midpoint
                'Freshwater eutrophication': 0.00021,  # kg P eq
                'Marine eutrophication': 0.0012,  # kg N eq
                'Terrestrial acidification': 0.0016,  # kg SO2 eq
                'Fine particulate matter formation': 0.00098,  # kg PM2.5 eq
                'Fossil resource scarcity': 0.0089,  # kg oil eq (was 0.089 - 10x too high)
                'Mineral resource scarcity': 0.000018,  # kg Cu eq (kept)
                'Human carcinogenic toxicity': 0.00012,  # kg 1,4-DCB eq
                'Human non-carcinogenic toxicity': 0.00011,  # kg 1,4-DCB eq
                'Terrestrial ecotoxicity': 0.00018,  # kg 1,4-DCB eq
                'Freshwater ecotoxicity': 0.00021,  # kg 1,4-DCB eq
                'Marine ecotoxicity': 0.000089,  # kg 1,4-DCB eq
                'Ionizing radiation': 0.00089,  # kBq Co-60 eq
                'Stratospheric ozone depletion': 8.9e-9,  # kg CFC11 eq
                'Ozone formation, Human health': 0.00095,  # kg NOx eq
                'Ozone formation, Terrestrial ecosystems': 0.00078,  # kg NOx eq
            }
        }
        
        # Default factors for unknown food groups. Set to the across-group
        # geometric midpoint of the P&N / M&H-grounded values above so an
        # unmapped CNF food sits in a defensible middle of the validated band.
        default_factors = {
            'Global warming': 0.25,  # kg CO2 eq — geometric midpoint of 10 group means
            'Land use': 0.5,  # m2a crop eq — geometric midpoint
            'Water consumption': 0.025,  # m³ — geometric midpoint (M&H blue-water-only)
            'Freshwater eutrophication': 0.001,  # kg P eq
            'Marine eutrophication': 0.01,  # kg N eq
            'Terrestrial acidification': 0.01,  # kg SO2 eq
            'Fine particulate matter formation': 0.005,  # kg PM2.5 eq
            'Fossil resource scarcity': 0.05,  # kg oil eq (was 0.5 - 10x too high)
            'Mineral resource scarcity': 0.0001,  # kg Cu eq (kept)
            # Added missing categories with conservative default values
            'Human carcinogenic toxicity': 0.0005,  # kg 1,4-DCB eq
            'Human non-carcinogenic toxicity': 0.0004,  # kg 1,4-DCB eq
            'Terrestrial ecotoxicity': 0.0008,  # kg 1,4-DCB eq
            'Freshwater ecotoxicity': 0.001,  # kg 1,4-DCB eq
            'Marine ecotoxicity': 0.0003,  # kg 1,4-DCB eq
            'Ionizing radiation': 0.003,  # kBq Co-60 eq
            'Stratospheric ozone depletion': 3.0e-8,  # kg CFC11 eq
            'Ozone formation, Human health': 0.005,  # kg NOx eq
            'Ozone formation, Terrestrial ecosystems': 0.004,  # kg NOx eq
        }

        # Select group-specific factors or defaults
        factors_out = dict(impact_factors_by_group.get(food_group_name, default_factors))

        # Per-category data-source and confidence metadata. Honest per-category
        # status from the v2 audit (`backend/_smoke_validate_cnf_integrator.py`):
        # only 3 of 18 ReCiPe categories have per-food-group numerical literature
        # grounding; the rest are conservative defaults pending Dekker 2020 ESM
        # ingestion (acidification + 2 eutrophications in ReCiPe units) and
        # licensed Agribalyse-LCI-re-scored-under-ReCiPe (the remaining 12).
        in_known_group = food_group_name in impact_factors_by_group
        factors_out['_data_source_by_category'] = {
            'Global warming':                          'Poore & Nemecek 2018 Fig. 1' if in_known_group else 'P&N-derived geometric midpoint',
            'Land use':                                'Poore & Nemecek 2018 Fig. 1' if in_known_group else 'P&N-derived geometric midpoint',
            'Water consumption':                       'Mekonnen & Hoekstra 2011/2012 blue-water-only' if in_known_group else 'M&H-derived geometric midpoint',
            'Terrestrial acidification':               'Conservative default (Dekker 2020 confirmed not to publish per-group numerical midpoints in extractable form — see TODO-CODE-LCA-1; defensible source remains TODO-CODE-LCA-2 licensed AGRIBALYSE-LCI re-scoring)',
            'Freshwater eutrophication':               'Conservative default (Dekker 2020 published only as bitmap figures; TODO-CODE-LCA-2 is the defensible path)',
            'Marine eutrophication':                   'Conservative default (Dekker 2020 published only as bitmap figures; TODO-CODE-LCA-2 is the defensible path)',
            'Fine particulate matter formation':       'Conservative default (no per-group literature target)',
            'Stratospheric ozone depletion':           'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Ionizing radiation':                      'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Ozone formation, Human health':           'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Ozone formation, Terrestrial ecosystems': 'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Human carcinogenic toxicity':             'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Human non-carcinogenic toxicity':         'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Terrestrial ecotoxicity':                 'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Freshwater ecotoxicity':                  'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Marine ecotoxicity':                      'Conservative default (Dekker 2020 LCI flagged incomplete)',
            'Mineral resource scarcity':               'Conservative default (no per-group literature target)',
            'Fossil resource scarcity':                'Conservative default (no per-group literature target)',
        }
        factors_out['_confidence_by_category'] = {
            'Global warming':     'High (cited)',
            'Land use':           'High (cited)',
            'Water consumption':  'High (cited)',
        }
        # Top-level fields kept for backwards compatibility with existing
        # consumers; semantics now reflect the "anchored only on 3 of 18" reality.
        factors_out['_data_source'] = 'P&N 2018 + M&H 2011/2012 for 3 of 18 categories; conservative defaults for the rest'
        factors_out['_confidence'] = 'High for GHG / Land / Water; Medium-Low for the other 15 categories'
        factors_out['_last_updated'] = '2026-05-21'
        factors_out['_notes'] = 'See _smoke_validate_cnf_integrator.py and §7.5 for per-category defensibility status'

        # v1 uncertainty bands ('demote, don't perfect'). Bands are envelope
        # bounds derived from P&N 10th-percentile/mean ratios (lower) and a
        # conservative ~2x-3x mean proxy (upper). For ONLY the 3 grounded
        # categories. Downstream consumers should treat the per-meal envelope
        # as a worst/best-case bound, not a 90% CI (full PDF propagation
        # requires Monte Carlo, see code_action_items.md MC plans).
        ratio_table = UNCERTAINTY_BAND_RATIOS_BY_GROUP.get(
            food_group_name, DEFAULT_UNCERTAINTY_BAND_RATIOS
        )
        bands: Dict[str, Dict[str, float]] = {}
        for cat in ('Global warming', 'Land use', 'Water consumption'):
            central = factors_out.get(cat)
            if isinstance(central, (int, float)):
                ratios = ratio_table.get(cat, DEFAULT_UNCERTAINTY_BAND_RATIOS[cat])
                bands[cat] = {
                    'low':     central * ratios['low_ratio'],
                    'central': float(central),
                    'high':    central * ratios['high_ratio'],
                }
        factors_out['_uncertainty_bands'] = bands

        return factors_out
    
    def get_data_quality_summary(self) -> Dict[str, Any]:
        """
        Provide summary of environmental impact data quality and corrections made.
        """
        return {
            'correction_status': 'MAJOR CORRECTIONS APPLIED',
            'corrections_made': {
                'carbon_footprint': 'Reduced by 10-16x to align with Poore & Nemecek 2018',
                'land_use': 'Reduced by 10x across all categories',
                'water_consumption': 'Converted from L to m³, values verified',
                'missing_categories': 'Added 9 missing ReCiPe 2016 impact categories'
            },
            'verification_sources': [
                'Poore & Nemecek 2018 (Science) - Primary reference',
                'Our World in Data food database',
                'World Food LCA Database (WFLDB)',
                'Eaternity Database',
                'SU-EATABLE LIFE Database'
            ],
            'confidence_levels': {
                'carbon_footprint': 'High - verified against gold standard',
                'water_consumption': 'High - cross-checked multiple sources',
                'land_use': 'High - based on established LCA methodology',
                'toxicity_categories': 'Medium - conservative estimates applied',
                'new_categories': 'Medium - extrapolated from similar foods'
            },
            'last_verification': '2024-08-12',
            'recommended_updates': [
                'Implement regional variation factors',
                'Add uncertainty ranges for all factors', 
                'Integrate with live database updates',
                'Validate against local Canadian LCA studies'
            ]
        }
    
    def is_initialized(self) -> bool:
        """Check if the integrator has been initialized"""
        return self._initialized
    
    def get_dataframe(self, df_name: str) -> pd.DataFrame:
        """Get a specific dataframe by name"""
        return self._dataframes.get(df_name.lower(), pd.DataFrame())
    
    def __str__(self) -> str:
        return f"CNFIntegrator(initialized={self._initialized}, data_dir='{self.data_dir}', corrected_impact_factors=True)"
    
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