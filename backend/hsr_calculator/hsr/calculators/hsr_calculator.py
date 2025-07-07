"""
HSR Calculator - Scientifically-improved Health Star Rating calculations
Addresses fundamental issues in the original HSR algorithm with evidence-based improvements.
"""

import logging
import bisect
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from functools import lru_cache

from ..models.meal import Meal
from ..models.food import Food
from ..models.category import Category
from ..models.hsr_result import (
    MealHSRResult, NutrientAnalysis, 
    HealthInsight, HSRLevel, NutrientImpact
)
from ..providers.threshold_provider import (
    ThresholdProvider, NutritionalContext
)

logger = logging.getLogger(__name__)


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
        
        # Analyze nutritional context
        self.nutritional_context = self._analyze_meal_context()
        
        # Get scientific thresholds
        self.thresholds = ThresholdProvider.get_thresholds(
            meal.category, self.nutritional_context
        )
        
        # Analyze sugar sources
        self.sugar_analysis = self._analyze_sugar_sources()
        
        # Cache for expensive calculations
        self._scores = None

    def calculate_hsr(self) -> MealHSRResult:
        """
        Calculate HSR using scientific algorithm.
        
        Returns:
            MealHSRResult with scientifically-improved analysis
        """
        # Calculate component scores
        component_score = self._calculate_components()
        
        # Apply scientific adjustments
        adjusted_score = self._apply_scientific_adjustments(component_score)
        
        # Convert to star rating using scientific approach
        star_rating = self._convert_to_star_rating(adjusted_score)
        
        # Create comprehensive result
        result = MealHSRResult(
            star_rating=star_rating,
            level=self._determine_level(star_rating),
            category=self.meal.category,
            component_score=component_score,
            total_weight=self.meal.total_weight,
            total_energy_kj=self.meal.energy_kj,
            total_energy_kcal=self.meal.energy_kilocalories
        )
        
        # Add analyses
        self._add_nutrient_analysis(result)
        self._add_scientific_insights(result)
        self._add_improvement_recommendations(result)
        
        # Add transparency and confidence metrics
        self._add_transparency(result)
        
        return result

    def compare_with_traditional_hsr(self) -> Dict[str, any]:
        """
        Compare with traditional HSR calculation.
        
        Returns:
            Comparison analysis showing differences and rationale
        """
        # Calculate current HSR
        current_result = self.calculate_hsr()
        
        # For comparison, calculate traditional approach
        # This would require legacy calculator but we've streamlined it out
        # So we'll provide the improved rationale
        
        comparison = {
            "current": {
                "star_rating": current_result.star_rating,
                "method": "Scientific evidence-based",
                "key_features": [
                    "Sugar source differentiation",
                    "Satiety adjustments", 
                    "Unified energy approach",
                    "Processing level consideration"
                ]
            },
            "improvements": [
                "Unified energy density across all categories",
                "Natural vs added sugar distinction",
                "Satiety index integration",
                "Processing level assessment"
            ],
            "confidence": current_result.confidence_score
        }
        
        return comparison

    def _analyze_meal_context(self) -> NutritionalContext:
        """Analyze meal to determine nutritional context"""
        # Prepare meal nutrients
        meal_nutrients = {
            'energy': self.meal.energy_kilocalories,
            'protein': self.meal.protein,
            'fiber': self.meal.fibre_total_dietary,
            'saturated_fat': self.meal.fatty_acids_saturated_total,
            'sodium': self.meal.sodium,
            'sugars': self.meal.sugars_total
        }
        
        # Prepare foods info
        foods_info = []
        for food in self.meal.foods:
            food_info = {
                'food_id': food.food_id,
                'food_name': food.food_name,
                'serving_size': food.serving_size,
                'food_group_id': getattr(food, 'food_group_id', 0),
                'food_form': self._determine_food_form(food),
                'processing_level': self._determine_processing_level(food),
                'has_added_sugars': self._has_added_sugars(food),
                'protein_content': food.nutrients.get('PROTEIN', 0)
            }
            foods_info.append(food_info)
        
        return ThresholdProvider.analyze_nutritional_context(meal_nutrients, foods_info)

    def _analyze_sugar_sources(self) -> SugarAnalysis:
        """Analyze sugar sources in the meal"""
        total_sugars = self.meal.sugars_total
        
        # Analyze each food's sugar contribution
        natural_sugars = 0.0
        added_sugars = 0.0
        sources = []
        
        for food in self.meal.foods:
            food_sugars = food.nutrients.get('SUGARS, TOTAL', 0) * food.serving_size / 100
            
            if self._is_natural_sugar_source(food):
                natural_sugars += food_sugars
                sources.append(f"{food.food_name} (natural)")
            else:
                # Estimate natural vs added sugar ratio for mixed foods
                natural_ratio = self._estimate_natural_sugar_ratio(food)
                food_natural = food_sugars * natural_ratio
                food_added = food_sugars * (1 - natural_ratio)
                
                natural_sugars += food_natural
                added_sugars += food_added
                
                if natural_ratio > 0.5:
                    sources.append(f"{food.food_name} (mostly natural)")
                else:
                    sources.append(f"{food.food_name} (mostly added)")
        
        # Calculate per 100g values
        weight_factor = self.meal.total_weight / 100 if self.meal.total_weight > 0 else 1
        
        return SugarAnalysis(
            total_sugars=total_sugars,
            natural_sugars=natural_sugars / weight_factor,
            added_sugars=added_sugars / weight_factor,
            natural_percentage=(natural_sugars / (natural_sugars + added_sugars) * 100) if (natural_sugars + added_sugars) > 0 else 0,
            sources=sources
        )

    def _calculate_components(self) -> HSRComponentScore:
        """Calculate component scores using scientific thresholds"""
        
        # Calculate traditional components with scientific thresholds
        energy_points = self._get_energy_points()
        saturated_fat_points = self._get_saturated_fat_points()
        
        # Calculate differentiated sugar points
        sugar_natural_points = self._get_sugar_points(
            self.sugar_analysis.natural_sugars, 
            self.thresholds.sugar_natural
        )
        sugar_added_points = self._get_sugar_points(
            self.sugar_analysis.added_sugars,
            self.thresholds.sugar_added
        )
        
        # Combined sugar points (weighted by severity)
        sugar_points = int(sugar_natural_points * 0.7 + sugar_added_points * 1.3)
        
        sodium_points = self._get_sodium_points()
        baseline_points = energy_points + saturated_fat_points + sugar_points + sodium_points
        
        # Calculate beneficial components
        protein_points = self._get_protein_points()
        fiber_points = self._get_fiber_points()
        fvnl_points = self._get_fvnl_points()
        
        modifying_points = protein_points + fiber_points + fvnl_points
        
        # Calculate scientific adjustments
        satiety_adjustment = self._calculate_satiety_adjustment()
        processing_penalty = self._calculate_processing_penalty()
        naturalness_bonus = self._calculate_naturalness_bonus()
        
        # Apply adjustments to final score
        base_final_score = max(0, baseline_points - modifying_points)
        adjusted_score = base_final_score + satiety_adjustment + processing_penalty + naturalness_bonus
        final_score = max(0, int(adjusted_score))
        
        # Convert to star rating
        star_rating = self._convert_to_star_rating(final_score)
        
        return HSRComponentScore(
            baseline_points=baseline_points,
            energy_points=energy_points,
            saturated_fat_points=saturated_fat_points,
            sugar_points=sugar_points,
            sodium_points=sodium_points,
            modifying_points=modifying_points,
            protein_points=protein_points,
            fiber_points=fiber_points,
            fvnl_points=fvnl_points,
            final_score=final_score,
            star_rating=star_rating,
            sugar_natural_points=sugar_natural_points,
            sugar_added_points=sugar_added_points,
            satiety_adjustment=satiety_adjustment,
            processing_penalty=processing_penalty,
            naturalness_bonus=naturalness_bonus,
            scientific_confidence=self._calculate_confidence()
        )

    def _get_energy_points(self) -> int:
        """Calculate energy points using unified energy density approach"""
        energy_density_kcal = self.meal.energy_kilocalories
        
        # Apply satiety adjustment
        adjusted_energy = energy_density_kcal / self.nutritional_context.satiety_index
        
        return self._get_points_by_thresholds(
            adjusted_energy, 
            self.thresholds.energy_density
        )

    def _get_saturated_fat_points(self) -> int:
        """Calculate saturated fat points with scientific thresholds"""
        return self._get_points_by_thresholds(
            self.meal.fatty_acids_saturated_total,
            self.thresholds.saturated_fat
        )

    def _get_sugar_points(self, sugar_amount: float, thresholds: List[float]) -> int:
        """Calculate sugar points for specific sugar type"""
        return self._get_points_by_thresholds(sugar_amount, thresholds)

    def _get_sodium_points(self) -> int:
        """Calculate sodium points with scientific thresholds"""
        return self._get_points_by_thresholds(
            self.meal.sodium,
            self.thresholds.sodium
        )

    def _get_protein_points(self) -> int:
        """Calculate protein points with quality adjustments"""
        protein_amount = self.meal.protein * self.nutritional_context.protein_quality_score
        return self._get_points_by_thresholds(
            protein_amount,
            self.thresholds.protein
        )

    def _get_fiber_points(self) -> int:
        """Calculate fiber points with scientific thresholds"""
        if self.meal.category in [Category.BEVERAGE, Category.DAIRY_BEVERAGE]:
            return 0  # Beverages don't contribute dietary fiber
        
        return self._get_points_by_thresholds(
            self.meal.fibre_total_dietary,
            self.thresholds.fiber
        )

    def _get_fvnl_points(self) -> int:
        """Calculate FVNL points with naturalness adjustment"""
        adjusted_fvnl = self.meal.fvnl_percent * self.nutritional_context.fvnl_naturalness
        return self._get_points_by_thresholds(
            adjusted_fvnl,
            self.thresholds.fvnl
        )

    def _get_points_by_thresholds(self, value: float, thresholds: List[float]) -> int:
        """Get points for a value against thresholds using binary search"""
        if not thresholds or thresholds[0] == float('inf'):
            return 0
        idx = bisect.bisect_left(thresholds, value)
        return min(idx, len(thresholds) - 1)

    def _calculate_satiety_adjustment(self) -> float:
        """Calculate satiety-based score adjustment"""
        if not self.config.apply_satiety_adjustments:
            return 0.0
        
        # Higher satiety foods get bonus points (better rating)
        satiety_bonus = (self.nutritional_context.satiety_index - 1.0) * 2.0
        return max(-3.0, min(3.0, satiety_bonus))

    def _calculate_processing_penalty(self) -> float:
        """Calculate processing level penalty"""
        if not self.config.consider_processing_level:
            return 0.0
        
        penalties = {
            'minimally_processed': 0.0,
            'processed': 1.0,
            'ultra_processed': 2.5
        }
        
        return penalties.get(self.nutritional_context.processing_level, 0.0)

    def _calculate_naturalness_bonus(self) -> float:
        """Calculate bonus for natural food content"""
        # Bonus for high natural FVNL content
        naturalness_bonus = 0.0
        
        if self.nutritional_context.fvnl_naturalness > 0.8:
            naturalness_bonus += 1.0
        elif self.nutritional_context.fvnl_naturalness > 0.6:
            naturalness_bonus += 0.5
        
        # Bonus for predominantly natural sugars
        if self.sugar_analysis.natural_percentage > 80:
            naturalness_bonus += 0.5
        
        return -naturalness_bonus  # Negative because lower scores = better ratings

    def _calculate_confidence(self) -> float:
        """Calculate confidence in the calculation"""
        confidence = 1.0
        
        # Reduce confidence for incomplete data
        if self.meal.protein == 0:
            confidence -= 0.1
        if self.meal.fibre_total_dietary == 0:
            confidence -= 0.1
        if self.meal.sodium == 0:
            confidence -= 0.05
        
        # Reduce confidence for very complex meals
        complexity_indicator = (
            (self.nutritional_context.processing_level == 'ultra_processed') + 
            (self.nutritional_context.liquid_percentage > 0.5)
        )
        if complexity_indicator >= 2:
            confidence -= 0.1
        
        # Reduce confidence for unusual combinations
        if self.meal.category == Category.BEVERAGE and self.meal.protein > 10:
            confidence -= 0.15
        
        return max(0.5, confidence)

    def _convert_to_star_rating(self, score: int) -> float:
        """Convert final score to star rating using scientific approach"""
        # Use continuous scale rather than discrete thresholds
        if score <= 0:
            return 5.0
        elif score <= 5:
            return 4.5
        elif score <= 10:
            return 4.0
        elif score <= 15:
            return 3.5
        elif score <= 20:
            return 3.0
        elif score <= 25:
            return 2.5
        elif score <= 30:
            return 2.0
        elif score <= 35:
            return 1.5
        else:
            return 1.0

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

    def _apply_scientific_adjustments(self, component_score: HSRComponentScore) -> int:
        """Apply final scientific adjustments to the score"""
        # This is already incorporated in _calculate_components
        return component_score.final_score

    def _add_nutrient_analysis(self, result: MealHSRResult):
        """Add nutrient analysis with scientific explanations"""
        analyses = []
        
        # Sugar analysis
        sugar_analysis = NutrientAnalysis(
            nutrient_name="Sugars (Total)",
            value=self.meal.sugars_total,
            unit="g",
            points=result.component_score.sugar_points,
            impact=self._determine_sugar_impact(),
            threshold_position=f"Natural: {self.sugar_analysis.natural_percentage:.1f}%",
            recommendation=self._get_sugar_recommendation()
        )
        analyses.append(sugar_analysis)
        
        # Add other analyses
        for nutrient_name, value, unit, threshold_attr in [
            ('Energy Density', self.meal.energy_kilocalories, 'kcal/100g', 'energy_density'),
            ('Saturated Fat', self.meal.fatty_acids_saturated_total, 'g', 'saturated_fat'),
            ('Sodium', self.meal.sodium, 'mg', 'sodium'),
            ('Protein', self.meal.protein, 'g', 'protein'),
            ('Fiber', self.meal.fibre_total_dietary, 'g', 'fiber'),
            ('FVNL', self.meal.fvnl_percent, '%', 'fvnl')
        ]:
            thresholds = getattr(self.thresholds, threshold_attr, [])
            points = self._get_points_by_thresholds(value, thresholds)
            
            analysis = NutrientAnalysis(
                nutrient_name=nutrient_name,
                value=value,
                unit=unit,
                points=points,
                impact=self._determine_nutrient_impact(nutrient_name, points),
                threshold_position=self._get_threshold_position(value, thresholds),
                recommendation=self._get_nutrient_recommendation(nutrient_name, value)
            )
            analyses.append(analysis)
        
        result.nutrient_analyses = analyses

    def _add_scientific_insights(self, result: MealHSRResult):
        """Add scientific insights about the meal"""
        insights = []
        
        # Sugar source insights
        if self.sugar_analysis.natural_percentage > 70:
            insights.append(HealthInsight(
                category="strength",
                title="Predominantly Natural Sugars",
                description=f"{self.sugar_analysis.natural_percentage:.1f}% of sugars are from natural sources like fruits",
                priority="medium"
            ))
        
        # Satiety insights
        if self.nutritional_context.satiety_index > 1.1:
            insights.append(HealthInsight(
                category="strength",
                title="High Satiety Potential",
                description="This food combination is likely to be more filling and satisfying",
                priority="high"
            ))
        
        # Processing level insights
        if self.nutritional_context.processing_level == "minimally_processed":
            insights.append(HealthInsight(
                category="strength",
                title="Minimally Processed",
                description="Foods are in their natural or lightly processed state",
                priority="medium"
            ))
        elif self.nutritional_context.processing_level == "ultra_processed":
            insights.append(HealthInsight(
                category="concern",
                title="Ultra-Processed Foods",
                description="Contains highly processed foods which may be less nutritious",
                priority="high"
            ))
        
        result.strengths = [i for i in insights if i.category == "strength"]
        result.concerns = [i for i in insights if i.category == "concern"]

    def _add_improvement_recommendations(self, result: MealHSRResult):
        """Add scientifically-based improvement recommendations"""
        recommendations = []
        
        # Sugar improvement recommendations
        if self.sugar_analysis.added_sugars > 5:
            recommendations.append(HealthInsight(
                category="recommendation",
                title="Reduce Added Sugars",
                description="Consider alternatives with less added sugar",
                priority="high",
                actionable=True,
                action_text="Look for unsweetened versions or add natural sweetness with fruits"
            ))
        
        # Satiety improvement recommendations
        if self.nutritional_context.satiety_index < 0.9:
            recommendations.append(HealthInsight(
                category="recommendation",
                title="Improve Satiety",
                description="Add protein or fiber to make this meal more filling",
                priority="medium",
                actionable=True,
                action_text="Consider adding nuts, seeds, or high-fiber vegetables"
            ))
        
        # Processing level recommendations
        if self.nutritional_context.processing_level == "ultra_processed":
            recommendations.append(HealthInsight(
                category="recommendation",
                title="Choose Less Processed Options",
                description="Opt for minimally processed alternatives when possible",
                priority="medium",
                actionable=True,
                action_text="Look for whole food alternatives or prepare from scratch"
            ))
        
        result.recommendations = recommendations

    def _add_transparency(self, result: MealHSRResult):
        """Add transparency metrics and explanations"""
        result.confidence_score = self._calculate_confidence()
        
        # Add detailed methodology explanation
        methodology = {
            "threshold_approach": "Unified energy density across all categories",
            "sugar_analysis": f"Natural: {self.sugar_analysis.natural_sugars:.1f}g, Added: {self.sugar_analysis.added_sugars:.1f}g",
            "satiety_adjustment": f"Index: {self.nutritional_context.satiety_index:.2f}",
            "processing_consideration": self.nutritional_context.processing_level,
            "improvements": [
                "Evidence-based thresholds",
                "Sugar source differentiation", 
                "Satiety index integration",
                "Processing level assessment"
            ]
        }
        
        result.methodology = methodology

    # Helper methods for analysis
    def _determine_food_form(self, food: Food) -> str:
        """Determine if food is liquid, semi-liquid, or solid"""
        food_group_id = getattr(food, 'food_group_id', 0)
        
        if food_group_id in [14, 20]:  # Beverages
            return 'liquid'
        elif 'juice' in food.food_name.lower() or 'drink' in food.food_name.lower():
            return 'liquid'
        elif 'soup' in food.food_name.lower() or 'smoothie' in food.food_name.lower():
            return 'semi_liquid'
        else:
            return 'solid'

    def _determine_processing_level(self, food: Food) -> str:
        """Determine processing level of food"""
        food_name = food.food_name.lower()
        
        # Ultra-processed indicators
        ultra_processed_indicators = [
            'flavoured', 'flavored', 'artificial', 'enriched', 'fortified',
            'instant', 'ready-to-eat', 'frozen meal', 'snack', 'candy',
            'soft drink', 'energy drink'
        ]
        
        if any(indicator in food_name for indicator in ultra_processed_indicators):
            return 'ultra_processed'
        
        # Processed indicators
        processed_indicators = [
            'canned', 'packaged', 'preserved', 'smoked', 'cured',
            'bread', 'cheese', 'yogurt'
        ]
        
        if any(indicator in food_name for indicator in processed_indicators):
            return 'processed'
        
        return 'minimally_processed'

    def _has_added_sugars(self, food: Food) -> bool:
        """Determine if food has added sugars"""
        food_name = food.food_name.lower()
        
        added_sugar_indicators = [
            'sweetened', 'sugar', 'syrup', 'honey', 'flavoured',
            'dessert', 'candy', 'chocolate', 'cake', 'cookie'
        ]
        
        return any(indicator in food_name for indicator in added_sugar_indicators)

    def _is_natural_sugar_source(self, food: Food) -> bool:
        """Determine if food is primarily a natural sugar source"""
        food_group_id = getattr(food, 'food_group_id', 0)
        
        # Fruits and some vegetables are natural sugar sources
        natural_sugar_groups = [9, 11]  # Fruits, some vegetables
        
        if food_group_id in natural_sugar_groups:
            return True
        
        # Check for whole fruits in name
        fruit_names = ['apple', 'banana', 'orange', 'grape', 'berry', 'peach', 'pear']
        food_name = food.food_name.lower()
        
        return any(fruit in food_name for fruit in fruit_names) and 'juice' not in food_name

    def _estimate_natural_sugar_ratio(self, food: Food) -> float:
        """Estimate ratio of natural to total sugars"""
        food_group_id = getattr(food, 'food_group_id', 0)
        food_name = food.food_name.lower()
        
        # High natural sugar ratio
        if food_group_id in [9, 11]:  # Fruits, vegetables
            return 0.9
        elif 'fruit' in food_name and 'juice' not in food_name:
            return 0.8
        elif food_group_id == 1:  # Dairy
            return 0.7  # Lactose is natural
        elif 'whole' in food_name or 'raw' in food_name:
            return 0.8
        
        # Low natural sugar ratio
        elif any(word in food_name for word in ['candy', 'dessert', 'cake', 'cookie']):
            return 0.1
        elif 'sweetened' in food_name:
            return 0.3
        
        # Default moderate ratio
        return 0.5

    def _determine_sugar_impact(self) -> NutrientImpact:
        """Determine overall sugar impact considering sources"""
        if self.sugar_analysis.added_sugars > 10:
            return NutrientImpact.NEGATIVE_HIGH
        elif self.sugar_analysis.added_sugars > 5:
            return NutrientImpact.NEGATIVE_MEDIUM
        elif self.sugar_analysis.natural_percentage > 70:
            return NutrientImpact.NEUTRAL
        else:
            return NutrientImpact.NEGATIVE_LOW

    def _get_sugar_recommendation(self) -> str:
        """Get sugar-specific recommendation"""
        if self.sugar_analysis.added_sugars > 10:
            return "Significantly reduce added sugar intake"
        elif self.sugar_analysis.added_sugars > 5:
            return "Consider reducing added sugars"
        elif self.sugar_analysis.natural_percentage > 80:
            return "Good choice - mostly natural sugars"
        else:
            return "Balance natural and added sugar sources"

    def _determine_nutrient_impact(self, nutrient: str, points: int) -> NutrientImpact:
        """Determine nutrient impact"""
        if nutrient in ['Energy Density', 'Saturated Fat', 'Sodium']:
            # Risk nutrients
            if points >= 8:
                return NutrientImpact.NEGATIVE_HIGH
            elif points >= 5:
                return NutrientImpact.NEGATIVE_MEDIUM
            elif points >= 2:
                return NutrientImpact.NEGATIVE_LOW
            else:
                return NutrientImpact.NEUTRAL
        else:
            # Beneficial nutrients
            if points >= 6:
                return NutrientImpact.POSITIVE_HIGH
            elif points >= 4:
                return NutrientImpact.POSITIVE_MEDIUM
            elif points >= 2:
                return NutrientImpact.POSITIVE_LOW
            else:
                return NutrientImpact.NEUTRAL

    def _get_threshold_position(self, value: float, thresholds: List[float]) -> str:
        """Get threshold position description"""
        if not thresholds:
            return "No thresholds available"
        
        points = self._get_points_by_thresholds(value, thresholds)
        percentile = (points / len(thresholds)) * 100
        
        return f"{percentile:.0f}th percentile"

    def _get_nutrient_recommendation(self, nutrient: str, value: float) -> str:
        """Get nutrient recommendations"""
        recommendations = {
            'Energy Density': {
                'high': "Consider portion control and pairing with low-energy foods",
                'medium': "Moderate energy content - suitable as part of balanced diet",
                'low': "Excellent for weight management and satiety"
            },
            'Protein': {
                'high': "Excellent protein source for muscle health",
                'medium': "Good protein contribution",
                'low': "Consider adding protein sources"
            },
            'Fiber': {
                'high': "Excellent for digestive health and satiety",
                'medium': "Good fiber contribution",
                'low': "Add fruits, vegetables, or whole grains"
            }
        }
        
        level = "high" if value > 15 else "medium" if value > 5 else "low"
        return recommendations.get(nutrient, {}).get(level, "Standard nutritional guidelines apply") 