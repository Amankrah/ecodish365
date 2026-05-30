"""
HSR Calculator - Scientifically-improved Health Star Rating calculations
Addresses fundamental issues in the original HSR algorithm with evidence-based improvements.
"""

import logging
import math
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from ..models.meal import Meal
from ..models.food import Food
from ..models.category import Category
from ..models.hsr_result import (
    MealHSRResult, NutrientAnalysis,
    HealthInsight, HSRLevel, NutrientImpact
)
from ..providers.threshold_provider import (
    ThresholdProvider,
    NutritionalContext,
    rust_hsr_backend,
)

logger = logging.getLogger(__name__)


# HSR-CODE-1.x-A — Cat 1 name overrides per HSRAC v9 Table 7. Plain water and
# unsweetened flavoured water map to 5.0 / 4.5 stars BY NAME, bypassing the
# score-based path. The Rust Cat 1 star_thresholds pad the top two bins with
# NEG_INFINITY because they're not numerically reachable; this hook restores
# them by name.
_RE_PLAIN_WATER = re.compile(
    r'(?i)^\s*water,\s*(?:municipal|bottled|spring|tap|mineral|distilled|carbonated|natural)\b',
)
_RE_UNSWEETENED_FLAVOURED_WATER = re.compile(
    r'(?i)\bwater\b.*\b(?:flavou?red?|flavou?r)\b.*\bunsweetened\b'
    r'|\bunsweetened\b.*\bflavou?red?\b.*\bwater\b',
)

# HSR-CODE-1.x-B — Cat 2 fruit/vegetable name override per HSRAC v9 Table 7.
# Eligible foods: fresh / frozen / canned (in juice or water) / dried whole
# fruit and vegetables, plus sweet corn. Override fires regardless of the
# calculator's category routing — the Cat 1/Cat 2 split misclassifies
# "Fruit cocktail, canned, juice pack" as Cat 1 because of the "juice"
# keyword, but the v9 override still applies.
_RE_ELIGIBLE_FRUIT_VEG = re.compile(
    r'(?ix)'
    # Whole-food fruit / vegetable nouns
    r'\b(?:fruit\s+cocktail|fruit\s+salad|fruit|vegetables?|peach(?:es)?|pear(?:s)?|'
    r'pineapple|cherry|cherries|grape(?:s)?|apricot(?:s)?|plum(?:s)?|berry|berries|'
    r'apple(?:s)?|banana(?:s)?|orange(?:s)?|mango(?:es)?|strawberr(?:y|ies)|'
    r'blueberr(?:y|ies)|raspberr(?:y|ies)|cranberr(?:y|ies)|raisin(?:s)?|prune(?:s)?|'
    r'dates?|fig(?:s)?|sweet\s+corn|corn,\s*sweet|tomato(?:es)?|carrot(?:s)?|'
    r'broccoli|spinach|kale|lettuce|cabbage|cucumber|zucchini|cauliflower|'
    r'mushroom(?:s)?|onion(?:s)?|pepper(?:s)?|pea(?:s)?|bean(?:s)?|asparagus|'
    r'celery|squash|pumpkin|sweet\s+potato(?:es)?|potato(?:es)?)\b'
    r'.*?'
    # …with a v9-eligible processing/state qualifier
    r'\b(?:canned|frozen|dried|dehydrated|fresh|raw|cooked|boiled|steamed|'
    r'roasted|drained|in\s+juice|juice\s+pack|water\s+pack|syrup\s+pack|'
    r'heavy\s+syrup|light\s+syrup|extra\s+light\s+syrup|brine|kernels?)\b',
)
# Cat 2 v9 override is INTENTIONALLY broad on processing state — v9 keeps
# fruit/veg at 5.0 stars even with added sugar in the syrup pack, because the
# whole-fruit nature of the product is what the rating recognises.


# Beverages whose PRIMARY identity is "{noun} juice|nectar|drink|beverage|smoothie".
# Excluded from the Cat 2 fruit/veg override: v9 keeps whole fruit/veg at
# 5.0 stars by name, but juices / nectars / drinks are NOT whole-food and are
# already covered by Cat 1's score-based path. "Cocktail" is allowed because
# CNF uses "Fruit cocktail" to denote canned mixed fruit (not an alcoholic
# beverage).
_RE_IS_BEVERAGE_FORM = re.compile(
    r'(?ix) ^ \s* \w+ \s+ (?: juice | nectar | drink | beverage | smoothie | punch )\b',
)

# Flavoured / sweetened water disqualifier for the plain-water override.
_RE_FLAVOURED_OR_SWEETENED = re.compile(
    r'(?i)\bflavou?red?\b|\bsweetened\b|\bflavou?r\b',
)


def _name_override_stars(food_names: List[str]) -> Optional[float]:
    """HSR-CODE-1.x-A + B. Return the v9 Table 7 name-override star rating
    when the (single-food) meal qualifies, else None.

    Multi-food meals: the override fires only on single-food meals — the v9
    spec is per-product, not per-meal."""
    if not food_names or len(food_names) != 1:
        return None
    name = (food_names[0] or '').strip()
    if not name:
        return None

    # A: Unsweetened flavoured water → 4.5
    if _RE_UNSWEETENED_FLAVOURED_WATER.search(name):
        return 4.5

    # A: Plain water → 5.0. Must NOT be flavoured or sweetened; the
    # _RE_PLAIN_WATER prefix alone matches "Water, mineral" which could be
    # part of "Water, mineral, lemon-flavored, sweetened" — gate accordingly.
    if _RE_PLAIN_WATER.match(name) and not _RE_FLAVOURED_OR_SWEETENED.search(name):
        return 5.0

    # B: Eligible whole fruit / vegetable → 5.0. Must NOT be primarily a
    # juice / nectar / drink / smoothie (those are processed beverages, not
    # whole-food fruit / veg under v9).
    if _RE_IS_BEVERAGE_FORM.match(name):
        return None
    if _RE_ELIGIBLE_FRUIT_VEG.search(name):
        return 5.0

    return None


@dataclass
class HSRConfig:
    """Configuration for HSR calculations"""
    use_scientific_thresholds: bool = True
    differentiate_sugar_sources: bool = True
    apply_satiety_adjustments: bool = True
    use_unified_energy_approach: bool = True
    consider_processing_level: bool = True
    include_confidence_metrics: bool = True
    detailed_explanations: bool = True


@dataclass
class SugarAnalysis:
    """Analysis of sugar sources in food/meal"""
    total_sugars: float
    natural_sugars: float
    added_sugars: float
    natural_percentage: float
    sources: List[str] = field(default_factory=list)


@dataclass
class HSRComponentScore:
    """HSR component score with detailed breakdown"""
    # Traditional components
    baseline_points: int
    energy_points: int
    saturated_fat_points: int
    sugar_points: int
    sodium_points: int
    modifying_points: int
    protein_points: int
    fiber_points: int
    fvnl_points: int
    final_score: int
    star_rating: float
    
    # Scientific components
    sugar_natural_points: int = 0
    sugar_added_points: int = 0
    satiety_adjustment: float = 0.0
    processing_penalty: float = 0.0
    naturalness_bonus: float = 0.0
    scientific_confidence: float = 1.0


class HSRCalculator:
    """
    HSR calculator implementing scientific improvements to address
    fundamental issues in the original algorithm.
    """
    
    def __init__(self, meal: Meal, config: Optional[HSRConfig] = None):
        self.meal = meal
        self.config = config or HSRConfig()
        
        # Get official HSR thresholds for category
        self.thresholds = ThresholdProvider.get_thresholds(meal.category)
        
        # Cache for expensive calculations
        self._scores = None

    def calculate_hsr(self) -> MealHSRResult:
        """
        Calculate HSR using official HSR algorithm.

        Returns:
            MealHSRResult with standard HSR analysis
        """
        # Calculate component scores using official HSR methodology
        component_score = self._calculate_components()

        # Convert to star rating using official approach
        star_rating = ThresholdProvider.convert_score_to_stars(
            component_score.final_score,
            self.thresholds.star_thresholds
        )

        # HSR-CODE-1.x-A + B: HSRAC v9 Table 7 name override. Plain water /
        # unsweetened flavoured water (Cat 1) and eligible whole fruit /
        # vegetables incl. sweet corn (Cat 2) map to 5.0 or 4.5 stars BY NAME,
        # regardless of the score-based path. Single-food meals only — v9 is
        # per-product, not per-meal.
        food_names = [
            (getattr(f, 'food_name', '') or '') for f in self.meal.foods
        ]
        override = _name_override_stars(food_names)
        if override is not None:
            component_score.star_rating = override
            star_rating = override

        # Create result
        result = MealHSRResult(
            star_rating=star_rating,
            level=self._determine_level(star_rating),
            category=self.meal.category,
            component_score=component_score,
            total_weight=self.meal.total_weight,
            total_energy_kj=self.meal.energy_kj,
            total_energy_kcal=self.meal.energy_kilocalories
        )
        
        # Add basic nutrient analysis
        self._add_nutrient_analysis(result)
        
        # Add realistic confidence
        result.confidence_score = self._calculate_confidence()
        
        return result




    def _calculate_components(self) -> HSRComponentScore:
        """Calculate component scores using official HSR methodology (Rust)."""
        rust = rust_hsr_backend()
        category_value = (
            self.meal.category.value
            if self.meal.category is not None
            else Category.FOOD.value
        )
        # HSR-CODE-1.x-E: HSRAC v9 Table 5 (Cat 1 V points) uses ≥ semantics,
        # while the Rust kernel encodes them as > with thresholds reduced by 1
        # (exact under integer FVNL%; off by ≤ 1 V-point at the boundary under
        # non-integer FVNL%). Flooring the FVNL value here BEFORE the Rust
        # call makes the > comparison behave like ≥ for Cat 1 specifically,
        # without rebuilding rust_core. All other categories use v9's standard
        # > semantics, so their thresholds and inputs are left untouched.
        fvnl_percent = float(self.meal.fvnl_percent)
        if category_value == Category.BEVERAGE.value:
            fvnl_percent = float(math.floor(fvnl_percent))
        d = rust.calculate_component_scores(
            category_value,
            float(self.meal.energy_kj),
            float(self.meal.fatty_acids_saturated_total),
            float(self.meal.sugars_total),
            float(self.meal.sodium),
            float(self.meal.protein),
            float(self.meal.fibre_total_dietary),
            fvnl_percent,
        )
        return HSRComponentScore(
            baseline_points=int(d["baseline_points"]),
            energy_points=int(d["energy_points"]),
            saturated_fat_points=int(d["saturated_fat_points"]),
            sugar_points=int(d["sugar_points"]),
            sodium_points=int(d["sodium_points"]),
            modifying_points=int(d["modifying_points"]),
            protein_points=int(d["protein_points"]),
            fiber_points=int(d["fiber_points"]),
            fvnl_points=int(d["fvnl_points"]),
            final_score=int(d["final_score"]),
            star_rating=0.0,
            scientific_confidence=self._calculate_confidence(),
        )










    def _calculate_confidence(self) -> float:
        """Calculate realistic confidence in the calculation"""
        confidence = 0.85  # Start with realistic base confidence
        
        # Reduce confidence for incomplete nutritional data
        missing_nutrients = 0
        if self.meal.protein == 0:
            missing_nutrients += 1
        if self.meal.fibre_total_dietary == 0:
            missing_nutrients += 1
        if self.meal.sodium == 0:
            missing_nutrients += 1
        if self.meal.fatty_acids_saturated_total == 0:
            missing_nutrients += 1
        
        # Reduce confidence by 5% for each missing key nutrient
        confidence -= (missing_nutrients * 0.05)
        
        # Reduce confidence for processed foods (common data quality issues)
        food_names = [food.food_name.lower() for food in self.meal.foods]
        processed_indicators = ['frozen', 'packaged', 'instant', 'processed', 'prepared']
        
        if any(indicator in name for name in food_names for indicator in processed_indicators):
            confidence -= 0.1
        
        # Reduce confidence for unusual combinations
        if self.meal.category == Category.BEVERAGE and self.meal.protein > 10:
            confidence -= 0.15
        
        return max(0.5, min(0.95, confidence))


    def _determine_level(self, star_rating: float) -> HSRLevel:
        """Determine HSR level with criteria"""
        if star_rating >= 4.5:
            return HSRLevel.EXCELLENT
        elif star_rating >= 3.5:
            return HSRLevel.GOOD
        elif star_rating >= 2.5:
            return HSRLevel.AVERAGE
        elif star_rating >= 1.5:
            return HSRLevel.BELOW_AVERAGE
        else:
            return HSRLevel.POOR


    def _add_nutrient_analysis(self, result: MealHSRResult):
        """Add basic nutrient analysis"""
        analyses = []
        
        # Basic nutrient analyses without complex explanations
        nutrients_data = [
            ('Energy', self.meal.energy_kj, 'kJ', result.component_score.energy_points),
            ('Sugars', self.meal.sugars_total, 'g', result.component_score.sugar_points),
            ('Saturated Fat', self.meal.fatty_acids_saturated_total, 'g', result.component_score.saturated_fat_points),
            ('Sodium', self.meal.sodium, 'mg', result.component_score.sodium_points),
            ('Protein', self.meal.protein, 'g', result.component_score.protein_points),
            ('Fiber', self.meal.fibre_total_dietary, 'g', result.component_score.fiber_points),
            ('FVNL', self.meal.fvnl_percent, '%', result.component_score.fvnl_points)
        ]
        
        for nutrient_name, value, unit, points in nutrients_data:
            analysis = NutrientAnalysis(
                nutrient_name=nutrient_name,
                value=value,
                unit=unit,
                points=points,
                impact=self._determine_basic_impact(nutrient_name, points),
                threshold_position=f"{points} points",
                recommendation=self._get_basic_recommendation(nutrient_name, points)
            )
            analyses.append(analysis)
        
        result.nutrient_analyses = analyses




    def _determine_basic_impact(self, nutrient: str, points: int) -> NutrientImpact:
        """Determine basic nutrient impact based on HSR points"""
        if nutrient in ['Energy', 'Sugars', 'Saturated Fat', 'Sodium']:
            # Risk nutrients - higher points = worse
            if points >= 8:
                return NutrientImpact.NEGATIVE_HIGH
            elif points >= 5:
                return NutrientImpact.NEGATIVE_MEDIUM
            elif points >= 2:
                return NutrientImpact.NEGATIVE_LOW
            else:
                return NutrientImpact.NEUTRAL
        else:
            # Beneficial nutrients - higher points = better
            if points >= 6:
                return NutrientImpact.POSITIVE_HIGH
            elif points >= 4:
                return NutrientImpact.POSITIVE_MEDIUM
            elif points >= 2:
                return NutrientImpact.POSITIVE_LOW
            else:
                return NutrientImpact.NEUTRAL

    def _get_basic_recommendation(self, nutrient: str, points: int) -> str:
        """Get basic recommendations based on nutrient points"""
        if nutrient in ['Energy', 'Sugars', 'Saturated Fat', 'Sodium']:
            if points >= 5:
                return f"High {nutrient.lower()} content - consider moderation"
            elif points >= 2:
                return f"Moderate {nutrient.lower()} content"
            else:
                return f"Low {nutrient.lower()} content"
        else:
            if points >= 4:
                return f"Good source of {nutrient.lower()}"
            elif points >= 2:
                return f"Some {nutrient.lower()} contribution"
            else:
                return f"Low {nutrient.lower()} content" 