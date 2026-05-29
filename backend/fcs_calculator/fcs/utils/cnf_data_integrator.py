"""
Enhanced CNF Data Integration utilizing existing CNFDataPipeline
Avoids redundancy by reusing established data loading patterns
"""

import sys
import os
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging
from collections import defaultdict
from functools import lru_cache
from typing import NamedTuple

# Use the single process-wide CNF pipeline. See backend/api/cnf_cache.py.
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
from api.cnf_cache import get_api_cnf_pipeline
from api.cnf_data_pipeline import CNFDataPipeline

from fcs.models.food_item import FoodItem


def get_shared_cnf_pipeline(cnf_data_dir: str) -> CNFDataPipeline:
    """Backwards-compatible shim; `cnf_data_dir` is ignored (bound at first use)."""
    return get_api_cnf_pipeline()

logger = logging.getLogger(__name__)


class _FoodFacts(NamedTuple):
    """Per-food-id facts cached by EnhancedCNFDataIntegrator. All fields are
    pure functions of food_id given the static CNF pipeline DataFrames."""
    food_desc_orig: str        # FoodDescription as stored
    food_desc_upper: str       # .upper() for keyword matching
    group_name_orig: str       # FoodGroupName as stored (may be 'nan' if missing)
    group_name_upper: str      # .upper() for matching
    food_group_id: int         # FoodGroupID (0 if missing)
    nova_level: int            # Rule-based NOVA level (LLM-off path)
    nova_confidence: float
    nova_rationale: str
    found: bool                # False = food_id not in pipeline → caller uses defaults


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

    @staticmethod
    def _normalize_amounts(food_ids: List[int], amounts_g: Optional[List[float]]) -> List[float]:
        """Default 100 g per food when amounts are missing or length-mismatched."""
        if not amounts_g or len(amounts_g) != len(food_ids):
            return [100.0] * len(food_ids)
        return [max(0.1, float(a)) for a in amounts_g]

    @lru_cache(maxsize=8192)
    def _energy_kcal_per_100g(self, food_id: int) -> float:
        """Cached: pure function of food_id; CNF DataFrames are loaded once
        per process and never mutate. Eliminates the 700-call pandas hot
        path on substitution requests."""
        food_nutrients = self.cnf_pipeline.nutrient_amount_df[
            self.cnf_pipeline.nutrient_amount_df['FoodID'] == food_id
        ]
        energy_data = pd.merge(
            food_nutrients,
            self.cnf_pipeline.nutrient_name_df,
            on='NutrientID',
        )
        energy_rows = energy_data[
            energy_data['NutrientName'].str.contains('KILOCALORIES', case=False, na=False)
        ]
        if energy_rows.empty:
            energy_rows = energy_data[
                energy_data['NutrientName'].str.contains('ENERGY', case=False, na=False)
                & ~energy_data['NutrientName'].str.contains('JOULE', case=False, na=False)
            ]
        if energy_rows.empty:
            return 100.0
        return float(energy_rows['NutrientValue'].iloc[0])

    def _portion_energy_kcal(self, food_id: int, amount_g: float) -> float:
        return self._energy_kcal_per_100g(food_id) * amount_g / 100.0

    @lru_cache(maxsize=8192)
    def _nutrient_attrs_per_100g(
        self, food_id: int,
    ) -> Optional[Tuple[Tuple[Tuple[str, float], ...], float]]:
        """Cached: pre-merged per-100g {fcs_attribute → value} for this food.

        Returns (attr_pairs, kcal_per_100g_sum), or None if the food has no
        nutrient rows (the original raised ValueError on that condition;
        `_accumulate_portion_nutrients` now raises on None).

        - attr_pairs preserves the original overwrite-by-last-row semantics:
          when multiple CNF nutrient names map to the same FCS attribute, the
          last-iterated row wins (same as the inline dict assignment in the
          pre-cache version of _accumulate_portion_nutrients).
        - kcal_per_100g_sum sums every KILOCALORIES row (matches the original
          `portion_energy += nutrient_value * scale` accumulation).
        """
        food_nutrients = self.cnf_pipeline.nutrient_amount_df[
            self.cnf_pipeline.nutrient_amount_df['FoodID'] == int(food_id)
        ]
        merged = pd.merge(
            food_nutrients,
            self.cnf_pipeline.nutrient_name_df,
            on='NutrientID',
        )
        if merged.empty:
            return None

        by_attr: Dict[str, float] = {}
        kcal_sum = 0.0
        for _, row in merged.iterrows():
            nutrient_name = str(row['NutrientName'])
            nutrient_value = float(row['NutrientValue'])
            upper = nutrient_name.upper()
            if 'KILOCALORIES' in upper:
                kcal_sum += nutrient_value
                continue
            if 'ENERGY' in upper:
                continue
            fcs_attribute = self._map_cnf_nutrient_to_fcs(nutrient_name)
            if fcs_attribute:
                by_attr[fcs_attribute] = nutrient_value
        return (tuple(by_attr.items()), kcal_sum)

    @lru_cache(maxsize=8192)
    def _food_categorization_facts(self, food_id: int) -> _FoodFacts:
        """Cached: per-food-id facts that _categorize_food_ingredients needs
        per food (description, group, rule-based NOVA level).

        IMPORTANT: NOVA classification is the rule-based path
        (enable_llm=False). When ``self.enable_nova_llm`` is True at runtime,
        callers MUST bypass this cache and run the original inline path so
        the LLM result is not bypassed.
        """
        from .nova_classifier import classify as nova_classify

        fn = self.cnf_pipeline.food_name_df
        rows = fn[fn['FoodID'] == int(food_id)]
        if rows.empty:
            # Mirrors the "rows.empty → NOVA level 1, processing_levels.append(1)"
            # branch in the original loop.
            return _FoodFacts(
                food_desc_orig='', food_desc_upper='',
                group_name_orig='', group_name_upper='',
                food_group_id=0,
                nova_level=1, nova_confidence=0.0, nova_rationale='no food row',
                found=False,
            )

        row = rows.iloc[0]
        food_desc_orig = str(row.get('FoodDescription', ''))
        # Match the original (`int(row.get('FoodGroupID', 0) or 0)`) None/NaN
        # handling — pandas may surface NaN as float('nan'); `or 0` collapses
        # it to 0.
        raw_group_id = row.get('FoodGroupID', 0)
        if pd.isna(raw_group_id):
            food_group_id = 0
        else:
            food_group_id = int(raw_group_id or 0)

        # Group name lookup — replicate the left-merge behaviour of the
        # original `food_with_groups`. If no matching group row exists, the
        # left-merged NaN got turned into the string 'nan' by `str(row.get(...))`,
        # so we do the same here for bit-exact parity with the pre-cache code.
        fg = self.cnf_pipeline.food_group_df
        fg_col = 'FoodGroupName' if 'FoodGroupName' in fg.columns else 'FoodGroup'
        fg_rows = fg[fg['FoodGroupID'] == food_group_id]
        if fg_rows.empty:
            group_name_orig = ''
        else:
            gn = fg_rows.iloc[0].get(fg_col)
            group_name_orig = str(gn) if pd.notna(gn) else 'nan'

        nova_result = nova_classify(
            food_id=int(food_id),
            food_description=food_desc_orig,
            food_group_name=group_name_orig,
            food_group_id=food_group_id,
            chat_json_client=None,
            enable_llm=False,
        )

        return _FoodFacts(
            food_desc_orig=food_desc_orig,
            food_desc_upper=food_desc_orig.upper(),
            group_name_orig=group_name_orig,
            group_name_upper=group_name_orig.upper(),
            food_group_id=food_group_id,
            nova_level=int(nova_result.level),
            nova_confidence=float(nova_result.confidence),
            nova_rationale=str(nova_result.rationale),
            found=True,
        )

    def _map_cnf_nutrient_to_fcs(self, nutrient_name: str) -> Optional[str]:
        upper = nutrient_name.upper()
        for cnf_name, fcs_name in self.nutrient_mapping.items():
            if cnf_name in upper:
                return fcs_name
        return None

    def _accumulate_portion_nutrients(
        self,
        food_id: int,
        amount_g: float,
        meal_totals: Dict[str, float],
    ) -> float:
        """Sum absolute nutrient amounts for one portion into *meal_totals*.

        Uses the cached per-100g attribute map (`_nutrient_attrs_per_100g`)
        so the pandas filter + merge runs ONCE per food_id per process
        instead of once per FCS scoring.
        """
        result = self._nutrient_attrs_per_100g(int(food_id))
        if result is None:
            raise ValueError(f"No nutrient data found for food ID: {food_id}")
        attrs_per_100g, kcal_per_100g = result

        scale = amount_g / 100.0
        for attr, per100g in attrs_per_100g:
            meal_totals[attr] += per100g * scale

        portion_energy = kcal_per_100g * scale
        if portion_energy <= 0:
            portion_energy = self._portion_energy_kcal(food_id, amount_g)
        return portion_energy

    @staticmethod
    def _set_weighted_flag(
        food_item: FoodItem,
        domain: str,
        attribute: str,
        energy_weight: float,
    ) -> None:
        """Energy-fraction presence (0–100), not binary OR across ingredients."""
        weighted = 100.0 * max(0.0, min(1.0, energy_weight))
        current = food_item.attributes[domain][attribute]
        if weighted > current:
            food_item.set_attribute(domain, attribute, weighted)
    
    def extract_nutrients_enhanced(
        self,
        food_ids: List[int],
        food_item: FoodItem,
        amounts_g: Optional[List[float]] = None,
    ) -> FoodItem:
        """
        Enhanced nutrient extraction using existing CNF pipeline infrastructure.
        Multi-food meals aggregate absolute nutrients by portion, then normalize
        to per 100 kcal (FCS / i.FCS methodology).
        """
        try:
            if not food_ids:
                raise ValueError("food_ids is empty")

            amounts = self._normalize_amounts(food_ids, amounts_g)

            domain_lookup: Dict[str, str] = {}
            for domain_name, attributes in food_item.attributes.items():
                for attr_name in attributes:
                    domain_lookup[attr_name] = domain_name

            meal_totals: Dict[str, float] = defaultdict(float)
            total_energy = 0.0
            mapped_count = 0

            for food_id, amount_g in zip(food_ids, amounts):
                portion_energy = self._accumulate_portion_nutrients(
                    int(food_id), amount_g, meal_totals,
                )
                total_energy += portion_energy

            if total_energy <= 0:
                logger.warning("Total meal energy is zero; using 100 kcal fallback")
                total_energy = 100.0

            for fcs_attribute, absolute_total in meal_totals.items():
                normalized_value = (absolute_total / total_energy) * 100.0
                domain_name = domain_lookup.get(fcs_attribute)
                if domain_name:
                    food_item.set_attribute(domain_name, fcs_attribute, normalized_value)
                    mapped_count += 1

            logger.debug(
                "CNF: Mapped %s nutrient attributes for %s foods (%.1f kcal total)",
                mapped_count, len(food_ids), total_energy,
            )

            self._calculate_nutrient_ratios(food_item)
            self._categorize_food_ingredients(food_ids, food_item, amounts)

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
    
    def _categorize_food_ingredients(
        self,
        food_ids: List[int],
        food_item: FoodItem,
        amounts_g: Optional[List[float]] = None,
    ) -> None:
        """
        Enhanced food categorization with comprehensive NOVA classification support.
        Ingredient flags are energy-weighted on multi-food meals (no binary OR-stacking).
        """
        try:
            amounts = self._normalize_amounts(food_ids, amounts_g)
            portion_energies = [
                self._portion_energy_kcal(int(fid), amt)
                for fid, amt in zip(food_ids, amounts)
            ]
            total_energy = sum(portion_energies) or 1.0
            energy_weight_by_id = {
                int(fid): portion_energies[i] / total_energy
                for i, fid in enumerate(food_ids)
            }

            food_info = self.cnf_pipeline.food_name_df[
                self.cnf_pipeline.food_name_df['FoodID'].isin(food_ids)
            ]
            if food_info.empty:
                return

            food_with_groups = pd.merge(
                food_info,
                self.cnf_pipeline.food_group_df,
                on='FoodGroupID',
                how='left',
            )

            detected_processing_levels: List[int] = []
            nova_by_id: Dict[int, int] = {}
            # When LLM-augmented NOVA is enabled, bypass the cache. Otherwise
            # use the cached per-food facts (Cache 3 — eliminates per-call
            # pandas filtering and repeated rule-based nova_classify work).
            use_nova_llm = bool(getattr(self, 'enable_nova_llm', False))

            for food_id_int, amount_g in zip(food_ids, amounts):
                food_id_int = int(food_id_int)
                ew = energy_weight_by_id.get(food_id_int, 1.0 / len(food_ids))

                if use_nova_llm:
                    # LLM-on path: keep the original inline lookup so the
                    # LLM call is exercised (cache returns rule-based only).
                    rows = food_with_groups[food_with_groups['FoodID'] == food_id_int]
                    if rows.empty:
                        detected_processing_levels.append(1)
                        nova_by_id[food_id_int] = 1
                        continue
                    row = rows.iloc[0]
                    food_desc_orig = str(row.get('FoodDescription', ''))
                    food_desc = food_desc_orig.upper()
                    group_name_orig = (
                        str(row.get('FoodGroupName', ''))
                        if 'FoodGroupName' in row else ''
                    )
                    group_name = group_name_orig.upper()
                    food_group_id = int(row.get('FoodGroupID', 0) or 0)
                    from .nova_classifier import classify as nova_classify
                    nova_result = nova_classify(
                        food_id=food_id_int,
                        food_description=food_desc_orig,
                        food_group_name=group_name_orig,
                        food_group_id=food_group_id,
                        chat_json_client=getattr(self, 'nova_llm_client', None),
                        enable_llm=True,
                    )
                    current_processing_level = nova_result.level
                else:
                    facts = self._food_categorization_facts(food_id_int)
                    if not facts.found:
                        detected_processing_levels.append(1)
                        nova_by_id[food_id_int] = 1
                        continue
                    food_desc_orig = facts.food_desc_orig
                    food_desc = facts.food_desc_upper
                    group_name_orig = facts.group_name_orig
                    group_name = facts.group_name_upper
                    food_group_id = facts.food_group_id
                    current_processing_level = facts.nova_level

                nova_by_id[food_id_int] = current_processing_level

                def flag(domain: str, attr: str) -> None:
                    self._set_weighted_flag(food_item, domain, attr, ew)

                logger.debug(
                    f" Categorizing food: '{food_desc}' in group: '{group_name}' "
                    f"(ID: {food_group_id}, energy_wt={ew:.3f})"
                )

                if food_group_id == 9:
                    flag('food_ingredients', 'fruit')
                elif food_group_id == 11:
                    flag('food_ingredients', 'vegetable')
                elif food_group_id == 16:
                    flag('food_ingredients', 'beans')
                elif food_group_id == 12:
                    flag('food_ingredients', 'nuts')
                elif food_group_id == 15:
                    flag('food_ingredients', 'seafood')
                elif food_group_id == 4:
                    flag('food_ingredients', 'plant_oils')
                elif food_group_id == 1:
                    if 'YOGURT' in food_desc or 'YOGHURT' in food_desc or 'YOGOURT' in food_desc:
                        flag('food_ingredients', 'yogurt')

                logger.debug(
                    f" NOVA classifier: food_id={food_id_int} "
                    f"level={current_processing_level}"
                )

                if current_processing_level == 4:
                    flag('food_ingredients', 'added_sugar')
                    self._detect_additives_from_description(
                        food_desc, food_item, processing_level=4, energy_weight=ew,
                    )
                    if 'FRIED' in food_desc:
                        flag('processing', 'frying')
                    if 'CANNED' in food_desc:
                        flag('processing', 'canning')
                elif current_processing_level == 3:
                    if any(t in food_desc for t in ['HAM', 'BACON', 'SAUSAGE', 'DELI', 'LUNCH', 'HOT DOG', 'CURED']):
                        flag('food_ingredients', 'red_or_processed_meat')
                    elif any(t in food_desc for t in ['BREAD', 'ROLL', 'BAGEL']):
                        flag('food_ingredients', 'refined_grains')
                    self._detect_additives_from_description(
                        food_desc, food_item, processing_level=3, energy_weight=ew,
                    )
                    if 'SMOKED' in food_desc or 'SMOKING' in food_desc:
                        flag('processing', 'smoking')
                    if 'CANNED' in food_desc:
                        flag('processing', 'canning')
                    if 'FERMENTED' in food_desc or 'AGED' in food_desc:
                        flag('processing', 'fermentation')
                elif current_processing_level == 2:
                    if any(t in food_desc for t in ['OIL', 'BUTTER', 'MARGARINE', 'SHORTENING']):
                        flag('food_ingredients', 'plant_oils')
                elif current_processing_level == 1:
                    flag('processing', 'minimal_processing')

                if food_group_id == 20:
                    if any(term in food_desc for term in ['WHOLE', 'BROWN', 'BRAN', 'WHEAT GERM']):
                        flag('food_ingredients', 'whole_grains')
                    else:
                        flag('food_ingredients', 'refined_grains')

                logger.debug(f" Food '{food_desc}' categorized as NOVA level {current_processing_level}")

            detected_processing_levels = [nova_by_id.get(int(fid), 1) for fid in food_ids]

            if detected_processing_levels:
                final_processing_level = self._calculate_energy_weighted_processing(
                    food_ids, detected_processing_levels, amounts,
                )
                logger.debug(f" Combined food processing levels: {detected_processing_levels}")
                logger.debug(f" Energy-weighted final processing level: {final_processing_level}")

                processing_details = self._get_processing_details(
                    food_ids, detected_processing_levels, food_with_groups, amounts,
                )
                food_item.set_processing_details(processing_details)
                self._set_final_nova_processing_level(food_item, final_processing_level)

                if len(set(detected_processing_levels)) > 1:
                    logger.debug(" Mixed processing levels detected — using energy weighting")
            else:
                logger.debug(" No processing levels detected, defaulting to NOVA 1 (minimally processed)")
                self._set_final_nova_processing_level(food_item, 1)

        except Exception as e:
            logger.warning(f"Could not fully categorize food ingredients: {e}")
            logger.debug(f" Error in food categorization: {e}")
    
    def _get_processing_details(
        self,
        food_ids: List[int],
        processing_levels: List[int],
        food_with_groups,
        amounts_g: Optional[List[float]] = None,
    ) -> Dict:
        """Detailed processing information for each food component in mixed dishes."""
        try:
            amounts = self._normalize_amounts(food_ids, amounts_g)
            details = {
                "is_mixed_dish": len(set(processing_levels)) > 1,
                "individual_foods": [],
                "energy_weights": [],
                "final_processing_level": None,
            }

            food_energies = [
                self._portion_energy_kcal(int(fid), amt)
                for fid, amt in zip(food_ids, amounts)
            ]
            total_energy = sum(food_energies) or 1.0

            nova_level_names = {
                1: "MINIMALLY_PROCESSED",
                2: "PROCESSED_CULINARY_INGREDIENTS",
                3: "PROCESSED_FOODS",
                4: "ULTRA_PROCESSED_FOODS",
            }

            for i, (food_id, processing_level) in enumerate(zip(food_ids, processing_levels)):
                food_row = food_with_groups[food_with_groups['FoodID'] == food_id]
                food_name = (
                    food_row['FoodDescription'].iloc[0]
                    if not food_row.empty else f"Food ID {food_id}"
                )
                energy_weight = food_energies[i] / total_energy

                food_detail = {
                    "food_id": food_id,
                    "food_name": food_name,
                    "nova_level": processing_level,
                    "nova_category": nova_level_names.get(processing_level, "UNKNOWN"),
                    "energy_kcal": round(food_energies[i], 2),
                    "energy_weight": round(energy_weight, 3),
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
    
    def _detect_additives_from_description(
        self,
        food_desc: str,
        food_item: FoodItem,
        processing_level: int,
        energy_weight: float = 1.0,
    ) -> None:
        """
        Comprehensive additives detection from food descriptions
        Uses pattern matching to identify common food additives and assign penalties
        """
        try:
            def add(attr: str) -> None:
                self._set_weighted_flag(food_item, 'additives', attr, energy_weight)
            # Artificial Sweeteners - Most common and well-documented
            artificial_sweetener_terms = [
                'ASPARTAME', 'SUCRALOSE', 'SACCHARIN', 'ACESULFAME', 'STEVIA', 
                'ARTIFICIAL SWEETENER', 'SUGAR FREE', 'NO SUGAR', 'DIET', 'LIGHT',
                'LOW CALORIE', 'CALORIE REDUCED', 'SUGAR SUBSTITUTE'
            ]
            
            if any(term in food_desc for term in artificial_sweetener_terms):
                self._set_weighted_flag(food_item, 'additives', 'artificial_sweeteners', energy_weight)
            
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
                    add('preservatives')
                
                # Processed meats definitely have preservatives
                if any(term in food_desc for term in ['HAM', 'BACON', 'SAUSAGE', 'DELI', 'CURED', 'SMOKED']):
                    add('preservatives')
                    add('nitrites')  # Nitrites common in processed meats
            
            if any(term in food_desc for term in preservative_terms):
                add('preservatives')
            
            # Artificial Colors - Common in ultra-processed foods
            artificial_color_terms = [
                'ARTIFICIAL COLOR', 'ARTIFICIAL COLOUR', 'FOOD COLORING', 'FOOD COLOURING',
                'RED DYE', 'BLUE DYE', 'YELLOW DYE', 'TARTRAZINE', 'SUNSET YELLOW',
                'BRILLIANT BLUE', 'ALLURA RED'
            ]
            
            if any(term in food_desc for term in artificial_color_terms):
                add('artificial_colors')
                logger.debug(f" Detected artificial colors in '{food_desc}'")
            
            # Infer artificial colors from food types
            if processing_level == 4:  # Ultra-processed
                color_likely_foods = [
                    'CANDY', 'GUMMY', 'JELLO', 'GELATIN', 'SOFT DRINK', 'SODA',
                    'ENERGY DRINK', 'SPORTS DRINK', 'FLAVORED', 'COLOURED'
                ]
                if any(term in food_desc for term in color_likely_foods):
                    add('artificial_colors')
                    logger.debug(f" Inferred artificial colors in colored processed food: '{food_desc}'")
            
            # Hydrogenated Oils - Trans fats
            hydrogenated_terms = [
                'HYDROGENATED', 'PARTIALLY HYDROGENATED', 'TRANS FAT', 'SHORTENING',
                'MARGARINE', 'VEGETABLE SHORTENING'
            ]
            
            if any(term in food_desc for term in hydrogenated_terms):
                add('hydrogenated_oils')
                logger.debug(f" Detected hydrogenated oils in '{food_desc}'")
            
            # High Fructose Corn Syrup
            hfcs_terms = [
                'HIGH FRUCTOSE CORN SYRUP', 'HFCS', 'CORN SYRUP', 'GLUCOSE-FRUCTOSE',
                'FRUCTOSE-GLUCOSE'
            ]
            
            if any(term in food_desc for term in hfcs_terms):
                add('high_fructose_corn_syrup')
                logger.debug(f" Detected HFCS in '{food_desc}'")
            
            # Monosodium Glutamate
            msg_terms = [
                'MONOSODIUM GLUTAMATE', 'MSG', 'GLUTAMATE', 'FLAVOR ENHANCER',
                'FLAVOUR ENHANCER'
            ]
            
            if any(term in food_desc for term in msg_terms):
                add('monosodium_glutamate')
                logger.debug(f" Detected MSG in '{food_desc}'")
            
            # Nitrites/Nitrates - Cured meats
            nitrite_terms = [
                'SODIUM NITRITE', 'SODIUM NITRATE', 'POTASSIUM NITRITE', 'POTASSIUM NITRATE',
                'NITRITE', 'NITRATE', 'CURING SALT'
            ]
            
            if any(term in food_desc for term in nitrite_terms):
                add('nitrites')
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
                    add('preservatives')  # Likely has emulsifiers
                    logger.debug(f" Inferred emulsifiers in gluten-free product: '{food_desc}'")
                
                if any(term in food_desc for term in emulsifier_terms):
                    add('preservatives')
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
    
    def _calculate_energy_weighted_processing(
        self,
        food_ids: List[int],
        processing_levels: List[int],
        amounts_g: Optional[List[float]] = None,
    ) -> float:
        """
        Calculate energy-weighted NOVA processing level for combined foods
        Uses calorie contribution of each food to weight the final processing score
        """
        try:
            amounts = self._normalize_amounts(food_ids, amounts_g)
            food_energies = [
                self._portion_energy_kcal(int(fid), amt)
                for fid, amt in zip(food_ids, amounts)
            ]

            total_energy = sum(food_energies)
            if total_energy == 0:
                return round(sum(processing_levels) / len(processing_levels))

            weighted_sum = sum(
                processing_levels[i] * food_energies[i]
                for i in range(len(processing_levels))
            )
            energy_weighted_level = weighted_sum / total_energy

            logger.debug(f" Energy weights: {[round(e/total_energy, 2) for e in food_energies]}")
            logger.debug(f" Weighted processing calculation: {weighted_sum}/{total_energy} = {energy_weighted_level}")

            return max(1.0, min(4.0, energy_weighted_level))

        except Exception as e:
            logger.warning(f"Error calculating energy-weighted processing: {e}")
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