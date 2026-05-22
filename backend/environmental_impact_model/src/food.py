import logging
from typing import Dict
from .data_loader import DataLoader
from .cnf_integrator import get_cnf_integrator


# Literature-anchored per-serving sustainability-score zone thresholds.
# Replaces the previous arbitrary `max_values` (which made a canned beef stew
# at 2.5 kg CO2/100g score 100/100 because the threshold was 100 kg CO2/100g).
#
# Stylianou et al. 2021, Nat Food 2(8):616-627, Supplementary Information
# Table 11B reports per-serving 50th and 75th percentile environmental impact
# cut-offs across a 5,853-food WWEIA-2011-2016 panel. Verified verbatim
# against `literature_extractions.md` line 1920. We use the per-serving
# values directly because `Food.get_environmental_impact` returns values
# scaled by `food.quantity / 100` — i.e. per the actual user-submitted
# serving size in grams. So food.quantity g IS the serving for the zone test.
#
# Score curve (piecewise linear, anchored at the published percentiles):
#   value = 0        -> 100  (best of best)
#   value = p50      -> 50   (median food in the panel)
#   value = p75      -> 25   (75th-percentile worst)
#   value = 2 * p75  -> 0    (extreme high; saturates at 0 beyond)
LITERATURE_ZONE_THRESHOLDS = {
    'Global warming': {
        'p50': 0.32,   # kg CO2 eq per serving
        'p75': 0.61,
        'unit': 'kg CO2-eq / serving',
        'source': 'Stylianou et al. 2021, Nat Food 2:616-627, SI Table 11B',
    },
    'Water consumption': {
        'p50': 0.020,  # m3 per serving (= 20 L; Stylianou L → m3)
        'p75': 0.045,  # m3 per serving (= 45 L)
        'unit': 'm3 blue water / serving',
        'source': 'Stylianou et al. 2021, Nat Food 2:616-627, SI Table 11B',
    },
    # Land use: Stylianou SI Table 11B reports ha-yr per serving at 0.24 / 0.70,
    # which we could not independently verify (magnitude implies a 2,400 m²-yr
    # 50th-percentile food, two orders of magnitude above the Poore & Nemecek
    # 2018 panel). Conservative fallback derived from P&N 2018 Fig. 1 panel
    # medians: ~0.5 m²a/100g is a mid-impact food (cereal/legume); ~5 m²a/100g
    # is a high-impact food (cheese/poultry); ~30 m²a/100g approaches the
    # beef-herd maximum. Documented as P&N-derived in the per-category source.
    'Land use': {
        'p50': 0.5,    # m2a crop-eq per serving (P&N panel midpoint)
        'p75': 5.0,    # m2a crop-eq per serving (P&N panel upper range)
        'unit': 'm2a crop-eq / serving',
        'source': 'P&N 2018 Fig. 1 panel medians (Stylianou SI Table 11B Land units could not be independently verified)',
    },
}


def _zone_score(value: float, p50: float, p75: float) -> float:
    """Piecewise-linear sustainability score (0-100, higher = better) from a
    per-serving impact value, anchored on the published 50th / 75th
    percentile cut-offs of a population food panel.

    Inverts the impact direction (lower impact => higher score) and uses
    asymmetric zone widths reflecting Stylianou's published Low / Moderate /
    High zoning (50th and 75th percentiles).
    """
    if value is None or value < 0:
        return 50.0
    if value <= 0:
        return 100.0
    if value <= p50:
        # Low zone: linear 100 -> 50
        return 100.0 - (value / p50) * 50.0
    if value <= p75:
        # Moderate zone: linear 50 -> 25
        return 50.0 - ((value - p50) / (p75 - p50)) * 25.0
    # High zone: linear 25 -> 0 across a second p75-width window; saturate at 0.
    return max(0.0, 25.0 - ((value - p75) / p75) * 25.0)


def _zone_label(value: float, p50: float, p75: float) -> str:
    """Return the Stylianou-style Low / Moderate / High label for a value."""
    if value is None or value < 0:
        return 'Unknown'
    if value < p50:
        return 'Low'
    if value < p75:
        return 'Moderate'
    return 'High'

class Food:
    """
    Enhanced Food class that integrates with the CNF singleton for improved data access
    and environmental impact calculations using current LCA best practices.
    """
    
    def __init__(self, food_id: int, quantity: float, data_loader: 'DataLoader'):
        self.logger = logging.getLogger(__name__)
        self.food_id = food_id
        self.quantity = quantity
        self.data_loader = data_loader
        self.cnf_integrator = get_cnf_integrator()
        
        try:
            self.data = self.data_loader.get_food_data(food_id)
        except ValueError as e:
            self.logger.error(f"Failed to initialize Food with ID {food_id}: {str(e)}")
            raise

        self.food_name = self.data['food_info']['FoodDescription']
        self.food_group = self.data['food_group'].get('FoodGroupName', 'Unknown')
        self.nutrients = self._process_nutrients()
        # Build a normalized nutrient map for robust lookups (case/alias tolerant)
        self._nutrients_normalized = self._build_normalized_nutrients(self.nutrients)
        self._nutrient_alias = self._build_nutrient_aliases()
        self.conversion_factors = self._get_conversion_factors()

    def _process_nutrients(self) -> Dict[str, float]:
        return {
            self.data_loader.get_nutrient_name(nutrient['NutrientID']): nutrient['NutrientValue']
            for nutrient in self.data['nutrients']
        }

    def _normalize_name(self, name: str) -> str:
        # Upper-case, strip, remove punctuation except spaces and letters, collapse spaces
        import re
        upper = (name or '').upper()
        cleaned = re.sub(r"[^A-Z0-9\s]", " ", upper)
        collapsed = re.sub(r"\s+", " ", cleaned).strip()
        return collapsed

    def _build_normalized_nutrients(self, nutrients: Dict[str, float]) -> Dict[str, float]:
        normalized: Dict[str, float] = {}
        for key, value in nutrients.items():
            normalized[self._normalize_name(key)] = value
        return normalized

    def _build_nutrient_aliases(self) -> Dict[str, str]:
        # Map common query names to CNF canonical nutrient names (normalized)
        canonical_fat = self._normalize_name('FAT (TOTAL LIPIDS)')
        canonical_carb = self._normalize_name('CARBOHYDRATE, TOTAL (BY DIFFERENCE)')
        canonical_energy = self._normalize_name('ENERGY (KILOCALORIES)')
        aliases = {
            # Protein is already canonical 'PROTEIN'
            self._normalize_name('FAT'): canonical_fat,
            self._normalize_name('TOTAL FAT'): canonical_fat,
            self._normalize_name('FAT TOTAL'): canonical_fat,
            self._normalize_name('LIPID'): canonical_fat,
            self._normalize_name('TOTAL LIPID'): canonical_fat,

            self._normalize_name('CARBOHYDRATE'): canonical_carb,
            self._normalize_name('CARBOHYDRATES'): canonical_carb,
            self._normalize_name('TOTAL CARBOHYDRATE'): canonical_carb,
            self._normalize_name('CARBOHYDRATE TOTAL'): canonical_carb,

            self._normalize_name('ENERGY'): canonical_energy,
            self._normalize_name('KILOCALORIES'): canonical_energy,
            self._normalize_name('KCAL'): canonical_energy,
        }
        return aliases

    def _get_conversion_factors(self) -> Dict[int, float]:
        conversion_factors = {}
        for _, row in self.data_loader.conversion_factor[self.data_loader.conversion_factor['FoodID'] == self.food_id].iterrows():
            conversion_factors[row['MeasureID']] = row['ConversionFactorValue']
        return conversion_factors

    def get_nutrient_amount(self, nutrient_name: str) -> float:
        # Robust, alias-tolerant lookup
        normalized = self._normalize_name(nutrient_name)
        # Direct normalized hit
        base_amount = self._nutrients_normalized.get(normalized)
        if base_amount is None:
            # Alias mapping
            target = self._nutrient_alias.get(normalized)
            if target:
                base_amount = self._nutrients_normalized.get(target, 0.0)
            else:
                # Final attempt: exact original case key
                base_amount = self.nutrients.get(nutrient_name, 0.0)
        # Scale to actual quantity (CNF values are per 100g)
        try:
            return (float(base_amount or 0.0) * float(self.quantity)) / 100.0
        except Exception:
            return 0.0

    def get_total_quantity(self) -> float:
        """Calculate total quantity including waste."""
        #waste_factor = 0.319  # 31.9% waste
        return self.quantity #/ (1 - waste_factor)

    # v1 LCA scope trim: the per-food impact dict returned to consumers
    # contains only the 3 literature-anchored categories. The cnf_integrator
    # factor table itself still carries the legacy 18-category values for
    # backwards compatibility with internal callers, but they MUST NOT leak
    # to the API surface or to per-food consumer outputs — that re-introduces
    # the "fabricated breadth" defect the v1 trim was designed to remove.
    # Consistent with `LifeCycleAssessment._calculate_midpoint_impacts`.
    _V1_CONSUMED_CATEGORIES = frozenset({
        'Global warming', 'Land use', 'Water consumption',
    })

    def get_environmental_impact(self) -> Dict[str, float]:
        """
        Calculate environmental impact using the CNF integrator's improved impact factors.
        Based on current LCA science and Canadian-specific data.

        v1 trim: returns only the 3 literature-anchored categories
        (Global warming, Land use, Water consumption). See
        `Food._V1_CONSUMED_CATEGORIES` and §7.5 of the manuscript.

        :return: Dictionary with impact categories as keys and impact values as values
        """
        try:
            # Get impact factors from the CNF integrator
            impact_factors = self.cnf_integrator.get_environmental_impact_factors(self.food_id)

            # Calculate actual quantity including food waste
            actual_quantity = self.get_total_quantity()
            quantity_factor = actual_quantity / 100.0  # Convert to per 100g basis

            # Scale impacts by quantity; skip metadata and non-numeric factors;
            # apply the v1 consumed-category trim.
            impacts = {}
            for impact_category, factor_per_100g in impact_factors.items():
                if isinstance(impact_category, str) and impact_category.startswith('_'):
                    continue
                if impact_category not in self._V1_CONSUMED_CATEGORIES:
                    continue
                if not isinstance(factor_per_100g, (int, float)):
                    continue
                impacts[impact_category] = float(factor_per_100g) * quantity_factor

            # Apply nutritional density adjustments
            nutritional_adjustments = self._calculate_nutritional_adjustments()
            for impact_category in impacts:
                impacts[impact_category] *= nutritional_adjustments.get(impact_category, 1.0)

            return impacts
            
        except Exception as e:
            self.logger.error(f"Error calculating environmental impact for food ID {self.food_id}: {e}")
            # Return minimal fallback impacts
            return {
                'Global warming': 0.5 * (self.quantity / 100),
                'Land use': 0.3 * (self.quantity / 100),
                'Water consumption': 0.1 * (self.quantity / 100)
            }
    
    def _calculate_nutritional_adjustments(self) -> Dict[str, float]:
        """
        Calculate adjustment factors based on nutritional density.
        Foods with higher nutritional value get lower environmental burden per nutritional unit.
        """
        adjustments = {}
        
        # Get key nutrients
        protein = self.get_nutrient_amount('PROTEIN')
        fiber = self.get_nutrient_amount('FIBRE')
        vitamins = (
            self.get_nutrient_amount('VITAMIN A') +
            self.get_nutrient_amount('VITAMIN C') +
            self.get_nutrient_amount('FOLATE')
        )
        
        # Calculate nutritional density score (higher is better)
        nutritional_score = (protein * 0.4 + fiber * 0.3 + vitamins * 0.3) / 100
        
        # Adjustment factor (1.0 = no adjustment, <1.0 = lower burden per nutrition)
        base_adjustment = max(0.7, min(1.3, 1.0 - (nutritional_score * 0.1)))
        
        # Apply to all impact categories with some variation
        impact_categories = [
            'Global warming', 'Stratospheric ozone depletion', 'Ionizing radiation',
            'Ozone formation, Human health', 'Fine particulate matter formation',
            'Ozone formation, Terrestrial ecosystems', 'Terrestrial acidification',
            'Freshwater eutrophication', 'Marine eutrophication', 'Terrestrial ecotoxicity',
            'Freshwater ecotoxicity', 'Marine ecotoxicity', 'Human carcinogenic toxicity',
            'Human non-carcinogenic toxicity', 'Land use', 'Mineral resource scarcity',
            'Fossil resource scarcity', 'Water consumption'
        ]
        
        for category in impact_categories:
            if category in ['Land use', 'Water consumption']:
                # Land and water use less affected by nutritional density
                adjustments[category] = base_adjustment * 1.2
            elif category in ['Global warming', 'Fossil resource scarcity']:
                # Carbon and energy impacts more affected by processing
                adjustments[category] = base_adjustment * 0.9
            else:
                adjustments[category] = base_adjustment
        
        return adjustments
    
    def get_sustainability_score(self, impacts: Dict[str, float] | None = None) -> Dict[str, float]:
        """
        Calculate a per-category and overall sustainability score using
        literature-anchored zone thresholds.

        Replaces the previous `max_values = {GW: 100, Land: 200, Water: 20}`
        anchors — which were ~10-100x too generous for real food impacts and
        mechanically guaranteed scores of 99-100 for any meal. The new score
        uses Stylianou et al. 2021 (Nat Food 2:616-627) SI Table 11B
        per-serving 50th and 75th percentile cut-offs as anchor points; see
        `LITERATURE_ZONE_THRESHOLDS` at module scope for sources.

        :param impacts: optional pre-computed per-food impacts dict (the
            per-serving values from `get_environmental_impact()`). When
            None (default), this method calls `self.get_environmental_impact()`
            internally — which is the group-default fallback path with NO
            LCA-matcher overlay. To get matcher-aware sustainability scoring,
            pass the per-food impacts dict from
            `LifeCycleAssessment._get_food_environmental_impacts(self)` here,
            which carries Agribalyse-matched values where the matcher fired.

        Returned dict shape:
          - `<category>`        : float 0-100 (per-category score)
          - `<category>_zone`   : str   Low / Moderate / High
          - `overall`           : float 0-100 (weighted average of present categories)
          - `methodology`       : dict  per-category {p50, p75, unit, source}
        """
        if impacts is None:
            impacts = self.get_environmental_impact()

        # Score each consumed category against its literature-anchored zone.
        sustainability_scores: Dict[str, float] = {}
        methodology: Dict[str, Dict] = {}
        for category, value in impacts.items():
            if category.startswith('_'):
                continue
            thresholds = LITERATURE_ZONE_THRESHOLDS.get(category)
            if thresholds is None:
                # No literature zone available for this category (e.g. a
                # trimmed v1 category that snuck through). Skip rather than
                # invent.
                continue
            p50 = thresholds['p50']
            p75 = thresholds['p75']
            sustainability_scores[category] = _zone_score(value, p50, p75)
            sustainability_scores[f'{category}_zone'] = _zone_label(value, p50, p75)
            methodology[category] = {
                'value_at_serving': float(value),
                'p50': p50,
                'p75': p75,
                'unit': thresholds['unit'],
                'source': thresholds['source'],
            }

        # Overall sustainability = weighted average across the present
        # categories. Weights are renormalised across categories that
        # actually have data, so missing categories don't silently inflate
        # or deflate the score (matches the renormalisation pattern used by
        # `LifeCycleAssessment.calculate_single_score` for the v1 trim).
        base_weights = {
            'Global warming':    0.45,
            'Land use':          0.30,
            'Water consumption': 0.25,
        }
        present_weights = {k: w for k, w in base_weights.items() if k in sustainability_scores}
        total_weight = sum(present_weights.values())
        if total_weight > 0:
            overall = sum(sustainability_scores[k] * (w / total_weight)
                          for k, w in present_weights.items())
            sustainability_scores['overall'] = overall
            sustainability_scores['overall_zone'] = _zone_label(
                100 - overall,  # invert: lower score = higher impact = "High" zone
                100 - 50,        # score 50 == median food
                100 - 25,        # score 25 == 75th-percentile worst
            )
        else:
            # No data — neutral default with explicit signal.
            sustainability_scores['overall'] = 50.0
            sustainability_scores['overall_zone'] = 'Unknown'
        sustainability_scores['methodology'] = methodology  # type: ignore[assignment]

        return sustainability_scores
    
    def __str__(self) -> str:
        return f"Food(id={self.food_id}, name='{self.food_name}', quantity={self.quantity}g)"

    def __repr__(self) -> str:
        return self.__str__()