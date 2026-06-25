import os
import pandas as pd
import logging
from functools import lru_cache
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Panel-anchored derivation chain for per-CNF-group GHG + Land centrals.
#
# Poore & Nemecek 2018 Fig. 1 publishes panel values in DIFFERENT functional
# units per panel: per 100 g protein (Panel A), per 1 L (Panel B), per 1,000
# kcal (Panel C), per 1 kg (Panels E/F/G), etc. Our pipeline expresses
# everything per 100 g of food product. The conversion requires applying a
# panel-specific factor (protein fraction, density, kcal density, or unit mass
# scaling). These are now made EXPLICIT below — previously they were embedded
# in inline comments alongside hand-typed numerical centrals, which was hard
# to audit and easy to drift.
#
# The shipped per-group dict (`impact_factors_by_group` inside
# `get_environmental_impact_factors`) is COMPUTED from these inputs at module
# load. Tests in `test_lca_v1_trim.py` (CnfIntegratorDerivationTests) recompute
# from the raw inputs and assert match, so any future edit that breaks the
# derivation chain is caught.
#
# Source of raw panel values: literature_extractions.md lines 431-518 (P&N
# 2018 Fig. 1 panels A through I). Water consumption is anchored separately
# on Mekonnen & Hoekstra 2011/2012 blue-water-only values and does not need
# panel-unit conversion.
# ---------------------------------------------------------------------------

_PN_PANEL_CENTRALS: Dict[str, Dict[str, Any]] = {
    # Panel A — per 100 g protein (protein-rich products)
    'beef_herd':       {'ghg': 50,  'land': 164, 'panel': 'A', 'unit': 'per 100g protein'},
    'beef_dairy_herd': {'ghg': 17,  'land': 22,  'panel': 'A', 'unit': 'per 100g protein'},
    'pork':            {'ghg': 7.6, 'land': 11,  'panel': 'A', 'unit': 'per 100g protein'},
    'poultry':         {'ghg': 5.7, 'land': 7.1, 'panel': 'A', 'unit': 'per 100g protein'},
    'farmed_fish':     {'ghg': 6.0, 'land': 3.7, 'panel': 'A', 'unit': 'per 100g protein'},
    'cheese':          {'ghg': 11,  'land': 41,  'panel': 'A', 'unit': 'per 100g protein'},
    'eggs':            {'ghg': 4.2, 'land': 5.7, 'panel': 'A', 'unit': 'per 100g protein'},
    'pulses':          {'ghg': 0.6, 'land': 5.4, 'panel': 'A', 'unit': 'per 100g protein'},  # peas+other pulses avg
    'nuts':            {'ghg': 0.3, 'land': 7.9, 'panel': 'A', 'unit': 'per 100g protein'},
    # Panel B — per 1 L (milks)
    'milk':            {'ghg': 3.2, 'land': 8.9, 'panel': 'B', 'unit': 'per L'},
    # Panel C — per 1,000 kcal (starch-rich)
    'grain_avg':       {'ghg': 0.9, 'land': 1.4, 'panel': 'C', 'unit': 'per 1000 kcal'},
    # Panel E — per 1 kg (vegetables); midpoint of in-panel products
    'veg_midpoint':    {'ghg': 1.0, 'land': 0.55, 'panel': 'E', 'unit': 'per kg'},
    # Panel F — per 1 kg (fruits)
    'fruit_midpoint':  {'ghg': 0.8, 'land': 1.4, 'panel': 'F', 'unit': 'per kg'},
}


# Conversion constants from panel functional units to per-100g-product.
# Edit these when CNF group composition assumptions change (e.g. shift from
# dry-grain to cooked-grain dominance, or revise protein fractions).
_DERIVATION_CONSTANTS: Dict[str, Dict[str, float]] = {
    # Protein mass fraction (g protein / 100 g product)
    'protein_fraction': {
        'beef':    0.20,  # cooked beef 22-26%, raw 20%; conservative mid 20%
        'pork':    0.20,  # pork tenderloin 22%, ground 17%; mid 20%
        'poultry': 0.22,  # chicken breast 23g/100g
        'fish':    0.18,  # mixed fillet 15-20%; mid 18%
        'cheese':  0.22,  # cheddar 25%, mozzarella 22%, soft 10-15%; group mid 22%
        'eggs':    0.12,  # whole egg 12.5 g/100g
        'pulses':  0.09,  # COOKED legumes 8-9 g/100g (dry pulses ~22%)
        'nuts':    0.20,  # mixed nuts 15-25 g/100g
    },
    # Density (kg / L) for Panel B
    'density_kg_per_L': {
        'milk': 1.03,
    },
    # Caloric density (kcal / 100 g) for Panel C
    # CNF "Cereals, Grains and Pasta" mixes cooked rice (~130), cooked pasta
    # (~158), bread (~265), dry flour (~350). The pre-2026-05 value of 350
    # assumed dry-only; revised to 200 to reflect the as-consumed average.
    'kcal_per_100g': {
        'grain_mix': 200,
    },
}


# Water consumption values per 100 g product, ANCHORED on Mekonnen & Hoekstra
# 2011 (Hydrol Earth Syst Sci 15:1577, crops Table 3) and M&H 2012 (Ecosystems
# 15:401, animal Table 3) BLUE-WATER-ONLY consumptive footprints. These align
# with the Hoekstra-Pfister "consumption" definition ReCiPe 2016 Water
# Consumption Potential uses (Huijbregts 2017 Table 1); NOT the green+blue+grey
# total (that over-estimates by 10-30x). Direct per-product values from M&H —
# no panel-unit conversion needed.
_WATER_CENTRALS_PER_100G: Dict[str, float] = {
    'Beef Products':                    0.062,  # M&H 2012 blue-water beef ~620 L/kg
    'Pork Products':                    0.046,  # pork ~459 L/kg
    'Poultry Products':                 0.031,  # chicken ~313 L/kg
    'Finfish and Shellfish Products':   0.005,  # wild ~0, farmed feed-crop small
    'Dairy and Egg Products':           0.020,  # milk 0.009 / egg 0.024 / cheese 0.041 blend
    'Vegetables and Vegetable Products': 0.006, # potato 0.003 / tomato 0.006 / onion 0.008
    'Fruits and fruit juices':          0.005,  # apple 0.001 / banana ~0 mid
    'Cereals, Grains and Pasta':        0.025,  # wheat/rice 0.034 / maize 0.008 mid
    'Legumes and Legume Products':      0.060,  # pulses ~400-800 L/kg mid 600
    'Nuts and Seeds':                   0.80,   # almond 0.3-1.6 m³/100g mixed-nut mid
}


def _derive_group_centrals() -> Dict[str, Dict[str, float]]:
    """Compute per-CNF-group GHG + Land centrals from raw P&N panel values
    and the documented derivation constants.

    Each conversion is annotated with the panel source. The result is the
    single source of truth consumed by `get_environmental_impact_factors`.
    """
    PF = _DERIVATION_CONSTANTS['protein_fraction']
    DENS = _DERIVATION_CONSTANTS['density_kg_per_L']
    KC = _DERIVATION_CONSTANTS['kcal_per_100g']

    def _panel_A(anchor: str, protein_fraction: float) -> Dict[str, float]:
        """Per 100g protein × protein_fraction = per 100g product."""
        raw = _PN_PANEL_CENTRALS[anchor]
        return {'ghg': raw['ghg'] * protein_fraction,
                'land': raw['land'] * protein_fraction}

    def _panel_B(anchor: str, density_kg_per_L: float) -> Dict[str, float]:
        """Per L: per_kg = per_L / density; per_100g = per_kg / 10."""
        raw = _PN_PANEL_CENTRALS[anchor]
        return {'ghg': raw['ghg'] / density_kg_per_L / 10,
                'land': raw['land'] / density_kg_per_L / 10}

    def _panel_C(anchor: str, kcal_per_100g: float) -> Dict[str, float]:
        """Per 1000 kcal × kcal/100g / 1000 = per 100g product."""
        raw = _PN_PANEL_CENTRALS[anchor]
        return {'ghg': raw['ghg'] * kcal_per_100g / 1000,
                'land': raw['land'] * kcal_per_100g / 1000}

    def _panel_per_kg(anchor: str) -> Dict[str, float]:
        """Per 1 kg / 10 = per 100g product."""
        raw = _PN_PANEL_CENTRALS[anchor]
        return {'ghg': raw['ghg'] / 10, 'land': raw['land'] / 10}

    def _arith_blend(*components: Dict[str, float]) -> Dict[str, float]:
        n = len(components)
        return {
            'ghg':  sum(c['ghg']  for c in components) / n,
            'land': sum(c['land'] for c in components) / n,
        }

    # Beef: beef-herd only (CNF "Beef Products" excludes dairy-herd by-product
    # meat). Both GHG and Land use the same anchor for internal consistency.
    beef = _panel_A('beef_herd', PF['beef'])

    pork    = _panel_A('pork',        PF['pork'])
    poultry = _panel_A('poultry',     PF['poultry'])
    fish    = _panel_A('farmed_fish', PF['fish'])

    # Dairy + Egg: arithmetic blend of cheese (Panel A, protein-anchored),
    # milk (Panel B, L-anchored), egg (Panel A). Equal-weight blend — simple
    # and defensible; a consumption-weighted blend would require per-CNF-entry
    # dietary frequency data we do not have at the food-group resolution.
    dairy_egg = _arith_blend(
        _panel_A('cheese', PF['cheese']),
        _panel_B('milk',   DENS['milk']),
        _panel_A('eggs',   PF['eggs']),
    )

    veg     = _panel_per_kg('veg_midpoint')
    fruit   = _panel_per_kg('fruit_midpoint')

    # Cereals: grain-average per 1000 kcal × representative kcal-density of
    # the CNF "Cereals, Grains and Pasta" group as consumed (mid 200).
    cereals = _panel_C('grain_avg', KC['grain_mix'])

    legumes = _panel_A('pulses', PF['pulses'])
    nuts    = _panel_A('nuts',   PF['nuts'])

    return {
        'Beef Products':                     beef,
        'Pork Products':                     pork,
        'Poultry Products':                  poultry,
        'Finfish and Shellfish Products':    fish,
        'Dairy and Egg Products':            dairy_egg,
        'Vegetables and Vegetable Products': veg,
        'Fruits and fruit juices':           fruit,
        'Cereals, Grains and Pasta':         cereals,
        'Legumes and Legume Products':       legumes,
        'Nuts and Seeds':                    nuts,
    }


# Computed once at module load. Single source of truth for the per-group
# GHG + Land centrals consumed by `get_environmental_impact_factors`.
_DERIVED_GROUP_CENTRALS = _derive_group_centrals()


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
        # Land low_ratio raised from 0.11 (cheese-internal 10th/mean) to 0.20
        # to reflect the new 3-component blend central (cheese 9.02, milk 0.86,
        # egg 0.68 → blend 3.5). Lower bound = min component / blend ≈ 0.19.
        'Land use':           {'low_ratio': 0.20, 'high_ratio': 3.0},
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
    Singleton wrapping the Canadian Nutrient File data with per-food-group
    environmental impact factors.

    Scope (v1 trim, see §7.5 of the manuscript and `_smoke_validate_cnf_integrator.py`):
    only three midpoint categories carry literature-anchored numerical defaults
    here — `Global warming`, `Land use`, `Water consumption`. The 15 other
    ReCiPe categories are not shipped from this layer; they re-enter the
    consumed set under TODO-CODE-LCA-2 once licensed AGRIBALYSE-LCI is
    re-scored under ReCiPe characterisation factors.
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
    
    @lru_cache(maxsize=8192)
    def get_food_data(self, food_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive food data for a given food ID.

        Cached: pure function of `food_id` given the static (process-lifetime)
        CNF DataFrames borrowed from the shared pipeline. The returned dict
        and its nested lists are SHARED across callers — treat as read-only
        (no caller in the current codebase mutates them; see file-top audit
        notes).

        Eliminates four separate pandas scalar filters per call from the
        substitution / scorecard / LCA hot paths.
        """
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

    @lru_cache(maxsize=16384)
    def get_nutrient_amount(self, food_id: int, nutrient_name: str) -> float:
        """Get nutrient amount for a specific food and nutrient. Cached: pure
        function of (food_id, nutrient_name); returns an immutable float."""
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
    
    @lru_cache(maxsize=16384)
    def get_conversion_factor(self, food_id: int, measure_id: int) -> float:
        """Get conversion factor for a specific food and measure. Cached:
        pure function of (food_id, measure_id); returns an immutable float."""
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
    
    @lru_cache(maxsize=8192)
    def get_environmental_impact_factors(self, food_id: int) -> Dict[str, float]:
        """
        Per-food-group ReCiPe 2016 H midpoint factors, per 100 g food product.

        Cached: pure function of food_id given static CNF data. The returned
        dict is SHARED across callers — treat as read-only.

        v1 scope (see `_smoke_validate_cnf_integrator.py` audit):

        - **Global warming** — Poore & Nemecek 2018 Fig. 1 panels A-F
          (Science 360:987-992); 10/10 groups within MARE < 0.6 of P&N centrals.
        - **Land use** — same source as above.
        - **Water consumption** — Mekonnen & Hoekstra 2011 (Hydrol Earth Syst
          Sci 15:1577, crops Table 3) and M&H 2012 (Ecosystems 15:401, animal
          Table 3) BLUE-WATER-ONLY consumptive footprints, matching the
          Hoekstra-Pfister "consumption" definition ReCiPe 2016 Water
          Consumption Potential uses (Huijbregts 2017 Table 1). NOT
          green+blue+grey total (that over-estimates by 10-30×).

        The 15 other ReCiPe 2016 midpoint categories are NOT shipped from
        this layer. They re-enter the consumed set under TODO-CODE-LCA-2
        (licensed AGRIBALYSE-LCI re-scoring under ReCiPe characterisation
        factors); see `code_action_items.md` and §7.5 of the manuscript.
        """
        food_data = self.get_food_data(food_id)
        if not food_data:
            return {}

        food_group_name = food_data.get('food_group', {}).get('FoodGroupName', 'Unknown')

        # Per-food-group factors for the v1-consumed categories, COMPUTED from
        # `_DERIVED_GROUP_CENTRALS` (P&N 2018 Fig. 1 panel values + documented
        # protein / density / kcal conversions) and `_WATER_CENTRALS_PER_100G`
        # (M&H 2011/2012 blue-water). See module-scope derivation chain.
        impact_factors_by_group = {
            group: {
                'Global warming':    central['ghg'],
                'Land use':          central['land'],
                'Water consumption': _WATER_CENTRALS_PER_100G.get(group, 0.025),
            }
            for group, central in _DERIVED_GROUP_CENTRALS.items()
        }

        # Default factors for unknown food groups — geometric midpoint across
        # the 10 derived group centrals. Keeps an unmapped CNF food inside
        # the validated band rather than at zero.
        default_factors = {
            'Global warming':    0.40,   # geomean across 10 group GHG centrals
            'Land use':          0.92,   # geomean across 10 group Land centrals
            'Water consumption': 0.025,  # M&H typical mid (unchanged)
        }

        # Select group-specific factors or defaults. FDC-MULTI-SOURCE
        # (2026-06-26): if the food's stored FoodGroupName isn't a CNF
        # canonical name (i.e. it's a WAFCT/FDC food like "WAFCT — Beef..."
        # or "FDC — Beef Products"), translate via the canonical-category
        # bridge to its CNF equivalent name and use that group's factors
        # instead of falling through to the wider default band.
        resolved_group_name = food_group_name
        if food_group_name not in impact_factors_by_group:
            try:
                from api.services.food_group_category import cnf_group_name_for_food
                bridged = cnf_group_name_for_food(food_id)
                if bridged and bridged in impact_factors_by_group:
                    resolved_group_name = bridged
            except Exception:  # noqa: BLE001 — bridge optional in some test paths
                pass

        factors_out = dict(impact_factors_by_group.get(resolved_group_name, default_factors))

        # Per-category data-source metadata (only the 3 consumed categories
        # carry literature grounding; see method docstring).
        in_known_group = resolved_group_name in impact_factors_by_group
        factors_out['_data_source_by_category'] = {
            'Global warming':    'Poore & Nemecek 2018 Fig. 1' if in_known_group else 'P&N-derived geometric midpoint',
            'Land use':          'Poore & Nemecek 2018 Fig. 1' if in_known_group else 'P&N-derived geometric midpoint',
            'Water consumption': 'Mekonnen & Hoekstra 2011/2012 blue-water-only' if in_known_group else 'M&H-derived geometric midpoint',
        }
        factors_out['_confidence_by_category'] = {
            'Global warming':    'High (cited)',
            'Land use':          'High (cited)',
            'Water consumption': 'High (cited)',
        }
        factors_out['_data_source'] = 'P&N 2018 + M&H 2011/2012 (v1 trim: 3 consumed categories)'
        factors_out['_confidence'] = 'High for GHG / Land / Water'
        factors_out['_last_updated'] = '2026-05-22'
        factors_out['_notes'] = 'See _smoke_validate_cnf_integrator.py and §7.5 for per-category defensibility status; v1 trim retains only the 3 literature-anchored categories'

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
    
    def is_initialized(self) -> bool:
        """Check if the integrator has been initialized"""
        return self._initialized
    
    def get_dataframe(self, df_name: str) -> pd.DataFrame:
        """Get a specific dataframe by name"""
        return self._dataframes.get(df_name.lower(), pd.DataFrame())
    
    def __str__(self) -> str:
        return f"CNFIntegrator(initialized={self._initialized}, data_dir='{self.data_dir}', v1_categories=3)"
    
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