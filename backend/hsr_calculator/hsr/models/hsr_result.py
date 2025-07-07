"""
HSR Result Models for detailed analysis and user insights
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
from .category import Category


class HSRLevel(Enum):
    """HSR rating levels with descriptive names"""
    POOR = "poor"           # 0.5-1.5 stars
    BELOW_AVERAGE = "below_average"  # 2.0-2.5 stars  
    AVERAGE = "average"     # 3.0-3.5 stars
    GOOD = "good"          # 4.0-4.5 stars
    EXCELLENT = "excellent" # 5.0 stars


class NutrientImpact(Enum):
    """Impact of nutrients on HSR score"""
    NEGATIVE_HIGH = "negative_high"    # Major negative impact
    NEGATIVE_MEDIUM = "negative_medium" # Moderate negative impact
    NEGATIVE_LOW = "negative_low"      # Minor negative impact
    NEUTRAL = "neutral"                # No significant impact
    POSITIVE_LOW = "positive_low"      # Minor positive impact
    POSITIVE_MEDIUM = "positive_medium" # Moderate positive impact
    POSITIVE_HIGH = "positive_high"    # Major positive impact


@dataclass
class NutrientAnalysis:
    """Detailed analysis of individual nutrient contributions"""
    nutrient_name: str
    value: float
    unit: str
    points: int
    impact: NutrientImpact
    threshold_position: str  # e.g., "Above 80th percentile"
    recommendation: Optional[str] = None
    
    
@dataclass
class ComponentScore:
    """Breakdown of HSR score components"""
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


@dataclass
class HealthInsight:
    """Health insights and recommendations"""
    category: str  # 'strength', 'concern', 'recommendation'
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    actionable: bool = False
    action_text: Optional[str] = None


@dataclass
class AlternativeSuggestion:
    """Suggested healthier alternatives"""
    food_id: int
    food_name: str
    food_group: str
    current_hsr: float
    alternative_hsr: float
    improvement: float
    reason: str


@dataclass
class HSRResult:
    """Comprehensive HSR calculation result with detailed insights"""
    
    # Basic results
    star_rating: float
    level: HSRLevel
    category: Category
    
    # Detailed scoring breakdown
    component_score: ComponentScore
    
    # Nutrient analysis
    nutrient_analyses: List[NutrientAnalysis] = field(default_factory=list)
    
    # Health insights
    strengths: List[HealthInsight] = field(default_factory=list)
    concerns: List[HealthInsight] = field(default_factory=list)
    recommendations: List[HealthInsight] = field(default_factory=list)
    
    # Alternatives
    alternatives: List[AlternativeSuggestion] = field(default_factory=list)
    
    # Summary metrics
    total_weight: float = 0.0
    total_energy_kj: float = 0.0
    total_energy_kcal: float = 0.0
    
    # Validation
    confidence_score: float = 1.0
    warnings: List[str] = field(default_factory=list)
    
    def get_summary(self) -> Dict[str, Union[str, float, int]]:
        """Get a summary of the HSR result"""
        return {
            'star_rating': self.star_rating,
            'level': self.level.value,
            'category': self.category.value,
            'final_score': self.component_score.final_score,
            'baseline_points': self.component_score.baseline_points,
            'modifying_points': self.component_score.modifying_points,
            'total_weight': self.total_weight,
            'total_energy_kcal': self.total_energy_kcal,
            'strengths_count': len(self.strengths),
            'concerns_count': len(self.concerns),
            'recommendations_count': len(self.recommendations),
            'confidence_score': self.confidence_score
        }
    
    def get_rating_description(self) -> str:
        """Get descriptive text for the rating level"""
        descriptions = {
            HSRLevel.POOR: "This food has a low nutritional quality. Consider choosing healthier alternatives.",
            HSRLevel.BELOW_AVERAGE: "This food has below-average nutritional quality. There are healthier options available.",
            HSRLevel.AVERAGE: "This food has average nutritional quality. Good as part of a balanced diet.",
            HSRLevel.GOOD: "This food has good nutritional quality. A healthy choice for regular consumption.",
            HSRLevel.EXCELLENT: "This food has excellent nutritional quality. An ideal choice for healthy eating."
        }
        return descriptions.get(self.level, "Rating level unknown")
    
    def get_priority_recommendations(self, max_items: int = 3) -> List[HealthInsight]:
        """Get top priority recommendations"""
        high_priority = [r for r in self.recommendations if r.priority == 'high']
        medium_priority = [r for r in self.recommendations if r.priority == 'medium']
        
        result = high_priority[:max_items]
        if len(result) < max_items:
            result.extend(medium_priority[:max_items - len(result)])
        
        return result


@dataclass 
class MealHSRResult(HSRResult):
    """HSR result for meals with additional meal-specific insights"""
    
    # Meal composition
    food_contributions: Dict[int, float] = field(default_factory=dict)  # food_id -> % contribution to total weight
    dominant_food_groups: List[str] = field(default_factory=list)
    
    # Meal balance insights
    macronutrient_balance: Dict[str, float] = field(default_factory=dict)
    meal_type_suggestion: Optional[str] = None  # breakfast, lunch, dinner, snack
    
    def get_meal_composition_summary(self) -> Dict[str, Union[str, List, Dict]]:
        """Get summary of meal composition"""
        return {
            'total_foods': len(self.food_contributions),
            'dominant_food_groups': self.dominant_food_groups,
            'macronutrient_balance': self.macronutrient_balance,
            'meal_type_suggestion': self.meal_type_suggestion,
            'largest_contributor': max(self.food_contributions.items(), 
                                     key=lambda x: x[1]) if self.food_contributions else None
        } 