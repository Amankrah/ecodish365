"""
Threshold Provider - Evidence-based HSR thresholds
Implements scientifically-rigorous threshold system that addresses issues with the original HSR algorithm.
"""

import logging
from typing import Dict, Union, List, Optional, Tuple
from dataclasses import dataclass
from ..models.category import Category

logger = logging.getLogger(__name__)


@dataclass
class NutritionalContext:
    """Context information for threshold adjustments"""
    is_natural_sugar_dominant: bool = False
    has_added_sugars: bool = False
    satiety_index: float = 1.0  # 1.0 = baseline, <1.0 = less satiating, >1.0 = more satiating
    processing_level: str = "minimally_processed"  # minimally_processed, processed, ultra_processed
    liquid_percentage: float = 0.0  # 0.0-1.0
    fiber_density: float = 0.0  # g/100g
    protein_quality_score: float = 1.0  # Quality of protein sources
    fvnl_naturalness: float = 1.0  # How "natural" the FVNL content is


@dataclass
class HSRThresholds:
    """HSR threshold configuration"""
    energy_density: List[float]  # kcal/100g
    sugar_natural: List[float]   # g/100g for natural sugars
    sugar_added: List[float]     # g/100g for added sugars
    saturated_fat: List[float]   # g/100g
    sodium: List[float]          # mg/100g
    fvnl: List[float]           # %
    protein: List[float]         # g/100g
    fiber: List[float]           # g/100g
    star_rating: List[float]     # Score thresholds for star conversion
    base_stars: float = 0.0      # All categories start from 0


class ThresholdProvider:
    """
    Provides scientifically-based thresholds that address the core issues
    in the original HSR algorithm.
    """
    
    # Unified energy density thresholds (kcal/100g) - same for all categories
    ENERGY_DENSITY_THRESHOLDS = [0, 50, 100, 150, 200, 250, 300, 400, 500, 600, 700]
    
    # Natural sugar thresholds - more lenient based on WHO recommendations
    NATURAL_SUGAR_THRESHOLDS = [0, 5, 8, 12, 15, 18, 22, 25, 28, 32, 35]
    
    # Added sugar thresholds - stricter based on WHO free sugar guidelines  
    ADDED_SUGAR_THRESHOLDS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15]
    
    # Saturated fat thresholds based on dietary guidelines (g/100g)
    SATURATED_FAT_THRESHOLDS = [0, 1, 2, 3, 4, 5, 7, 9, 12, 15, 20]
    
    # Sodium thresholds based on cardiovascular health evidence (mg/100g)
    SODIUM_THRESHOLDS = [0, 100, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500]
    
    # Unified FVNL thresholds - same for all categories
    FVNL_THRESHOLDS = [0, 25, 40, 50, 60, 67, 75, 80, 90, 95, 100]
    
    # Protein thresholds based on nutritional significance (g/100g)
    PROTEIN_THRESHOLDS = [0, 3, 6, 10, 15, 20, 25, 30, 35, 40, 50]
    
    # Fiber thresholds based on dietary guidelines (g/100g)
    FIBER_THRESHOLDS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15]
    
    # Star rating conversion thresholds
    STAR_RATING_THRESHOLDS = [-10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40]
    
    # Satiety multipliers based on food form and composition
    SATIETY_MULTIPLIERS = {
        'liquid': 0.7,          # Liquid calories less satiating
        'semi_liquid': 0.85,    # Smoothies, soups
        'solid': 1.0,           # Baseline
        'high_fiber': 1.2,      # High fiber foods more satiating
        'high_protein': 1.15,   # High protein foods more satiating
        'whole_food': 1.1,      # Minimally processed foods
        'ultra_processed': 0.9   # Ultra-processed foods less satiating
    }

    @classmethod
    def get_thresholds(cls, category: Category, 
                      nutritional_context: Optional[NutritionalContext] = None) -> HSRThresholds:
        """
        Get scientifically-adjusted thresholds based on category and nutritional context.
        
        Args:
            category: HSR category (used for specific adjustments only)
            nutritional_context: Nutritional context for personalized adjustments
            
        Returns:
            HSRThresholds object with adjusted thresholds
        """
        # Start with base scientific thresholds (same for all categories)
        thresholds = HSRThresholds(
            energy_density=cls.ENERGY_DENSITY_THRESHOLDS.copy(),
            sugar_natural=cls.NATURAL_SUGAR_THRESHOLDS.copy(),
            sugar_added=cls.ADDED_SUGAR_THRESHOLDS.copy(),
            saturated_fat=cls.SATURATED_FAT_THRESHOLDS.copy(),
            sodium=cls.SODIUM_THRESHOLDS.copy(),
            fvnl=cls.FVNL_THRESHOLDS.copy(),
            protein=cls.PROTEIN_THRESHOLDS.copy(),
            fiber=cls.FIBER_THRESHOLDS.copy(),
            star_rating=cls.STAR_RATING_THRESHOLDS.copy(),
            base_stars=0.0  # All categories start from 0
        )
        
        # Apply context-specific adjustments
        if nutritional_context:
            thresholds = cls._apply_contextual_adjustments(thresholds, nutritional_context)
        
        # Apply minimal category-specific adjustments (only where scientifically justified)
        thresholds = cls._apply_category_adjustments(thresholds, category)
        
        return thresholds

    @classmethod
    def _apply_contextual_adjustments(cls, thresholds: HSRThresholds, 
                                    context: NutritionalContext) -> HSRThresholds:
        """Apply adjustments based on nutritional context"""
        
        # Adjust energy thresholds based on satiety index
        if context.satiety_index != 1.0:
            # Higher satiety = more lenient energy thresholds
            satiety_factor = context.satiety_index
            thresholds.energy_density = [
                int(threshold * satiety_factor) for threshold in thresholds.energy_density
            ]
            logger.debug(f"Applied satiety adjustment: factor={satiety_factor:.2f}")
        
        # Adjust sugar thresholds based on processing level
        if context.processing_level == "ultra_processed":
            # Stricter thresholds for ultra-processed foods
            thresholds.sugar_added = [
                int(threshold * 0.8) for threshold in thresholds.sugar_added
            ]
            logger.debug("Applied ultra-processed penalty to added sugar thresholds")
        
        # Adjust thresholds based on liquid percentage
        if context.liquid_percentage > 0.3:
            # More liquid = stricter energy and sugar thresholds
            liquid_factor = 1.0 - (context.liquid_percentage * 0.3)  # Up to 30% stricter
            thresholds.energy_density = [
                int(threshold * liquid_factor) for threshold in thresholds.energy_density
            ]
            # Natural sugars in liquids are less beneficial than in whole foods
            thresholds.sugar_natural = [
                int(threshold * liquid_factor) for threshold in thresholds.sugar_natural
            ]
            logger.debug(f"Applied liquid adjustment: factor={liquid_factor:.2f}")
        
        # Boost protein thresholds for high-quality protein
        if context.protein_quality_score > 1.0:
            # High-quality protein gets more credit
            thresholds.protein = [
                int(threshold / context.protein_quality_score) for threshold in thresholds.protein
            ]
            logger.debug(f"Applied protein quality boost: factor={context.protein_quality_score:.2f}")
        
        return thresholds

    @classmethod
    def _apply_category_adjustments(cls, thresholds: HSRThresholds, 
                                  category: Category) -> HSRThresholds:
        """Apply minimal category-specific adjustments (only where scientifically justified)"""
        
        # Only apply adjustments where there's clear scientific rationale
        if category == Category.CHEESE:
            # Cheese products expect higher protein and fat - adjust protein thresholds slightly
            thresholds.protein = [max(0, threshold - 2) for threshold in thresholds.protein]
            logger.debug("Applied cheese-specific protein adjustment")
        
        elif category in [Category.BEVERAGE, Category.DAIRY_BEVERAGE]:
            # Beverages don't contribute dietary fiber - remove fiber scoring
            thresholds.fiber = [float('inf')] * len(thresholds.fiber)  # Effectively disabled
            logger.debug("Disabled fiber scoring for beverages")
        
        elif category == Category.OILS_AND_SPREADS:
            # Oils/spreads are energy-dense by nature - slight energy threshold adjustment
            thresholds.energy_density = [threshold + 50 for threshold in thresholds.energy_density]
            logger.debug("Applied oils/spreads energy adjustment")
        
        return thresholds

    @classmethod
    def analyze_nutritional_context(cls, meal_nutrients: Dict[str, float], 
                                  foods_info: List[Dict]) -> NutritionalContext:
        """
        Analyze meal composition to determine nutritional context for threshold adjustments.
        
        Args:
            meal_nutrients: Combined nutritional values per 100g
            foods_info: List of food information dictionaries
            
        Returns:
            NutritionalContext object with analyzed characteristics
        """
        # Analyze sugar sources
        natural_sugar_foods = cls._count_natural_sugar_foods(foods_info)
        processed_foods = cls._count_processed_foods(foods_info)
        
        is_natural_sugar_dominant = natural_sugar_foods > processed_foods
        has_added_sugars = any(food.get('has_added_sugars', False) for food in foods_info)
        
        # Calculate satiety index
        satiety_index = cls._calculate_satiety_index(meal_nutrients, foods_info)
        
        # Determine processing level
        processing_level = cls._determine_processing_level(foods_info)
        
        # Calculate liquid percentage
        liquid_percentage = cls._calculate_liquid_percentage(foods_info)
        
        # Get fiber density
        fiber_density = meal_nutrients.get('fiber', 0)
        
        # Calculate protein quality score
        protein_quality_score = cls._calculate_protein_quality_score(foods_info)
        
        # Assess FVNL naturalness
        fvnl_naturalness = cls._assess_fvnl_naturalness(foods_info)
        
        return NutritionalContext(
            is_natural_sugar_dominant=is_natural_sugar_dominant,
            has_added_sugars=has_added_sugars,
            satiety_index=satiety_index,
            processing_level=processing_level,
            liquid_percentage=liquid_percentage,
            fiber_density=fiber_density,
            protein_quality_score=protein_quality_score,
            fvnl_naturalness=fvnl_naturalness
        )

    @classmethod
    def _count_natural_sugar_foods(cls, foods_info: List[Dict]) -> int:
        """Count foods with primarily natural sugars"""
        natural_food_groups = [9, 11]  # Fruits, Vegetables
        return sum(1 for food in foods_info 
                  if food.get('food_group_id') in natural_food_groups)

    @classmethod
    def _count_processed_foods(cls, foods_info: List[Dict]) -> int:
        """Count processed foods with added sugars"""
        processed_groups = [1, 2, 3, 19]  # Dairy, Baked Products, etc.
        return sum(1 for food in foods_info 
                  if food.get('food_group_id') in processed_groups)

    @classmethod
    def _calculate_satiety_index(cls, meal_nutrients: Dict[str, float], 
                               foods_info: List[Dict]) -> float:
        """Calculate satiety index based on meal composition"""
        satiety_score = 1.0
        
        # Protein boost
        protein = meal_nutrients.get('protein', 0)
        if protein >= 20:
            satiety_score *= 1.2
        elif protein >= 15:
            satiety_score *= 1.15
        elif protein >= 10:
            satiety_score *= 1.1
        
        # Fiber boost
        fiber = meal_nutrients.get('fiber', 0)
        if fiber >= 10:
            satiety_score *= 1.2
        elif fiber >= 6:
            satiety_score *= 1.15
        elif fiber >= 3:
            satiety_score *= 1.1
        
        # Liquid penalty
        liquid_percentage = cls._calculate_liquid_percentage(foods_info)
        if liquid_percentage > 0.5:
            satiety_score *= 0.7
        elif liquid_percentage > 0.2:
            satiety_score *= 0.85
        
        # Processing level adjustment
        ultra_processed_count = sum(1 for food in foods_info 
                                  if food.get('processing_level') == 'ultra_processed')
        if ultra_processed_count > len(foods_info) / 2:
            satiety_score *= 0.9
        
        return max(0.5, min(1.5, satiety_score))

    @classmethod
    def _determine_processing_level(cls, foods_info: List[Dict]) -> str:
        """Determine overall processing level of meal"""
        processing_scores = {
            'minimally_processed': 1,
            'processed': 2,
            'ultra_processed': 3
        }
        
        if not foods_info:
            return 'minimally_processed'
        
        avg_processing = sum(
            processing_scores.get(food.get('processing_level', 'minimally_processed'), 1)
            for food in foods_info
        ) / len(foods_info)
        
        if avg_processing >= 2.5:
            return 'ultra_processed'
        elif avg_processing >= 1.5:
            return 'processed'
        else:
            return 'minimally_processed'

    @classmethod
    def _calculate_liquid_percentage(cls, foods_info: List[Dict]) -> float:
        """Calculate percentage of meal that is liquid"""
        if not foods_info:
            return 0.0
        
        total_weight = sum(food.get('serving_size', 0) for food in foods_info)
        if total_weight == 0:
            return 0.0
        
        liquid_weight = sum(
            food.get('serving_size', 0) for food in foods_info
            if food.get('food_form') in ['liquid', 'beverage', 'juice']
        )
        
        return liquid_weight / total_weight

    @classmethod
    def _calculate_protein_quality_score(cls, foods_info: List[Dict]) -> float:
        """Calculate protein quality score based on amino acid completeness"""
        if not foods_info:
            return 1.0
        
        # Simplified protein quality scoring
        high_quality_groups = [5, 6, 7, 8, 15, 16]  # Poultry, Fish, Dairy, Eggs, Legumes
        medium_quality_groups = [12, 14]  # Nuts, Seeds
        
        total_protein_weight = sum(
            food.get('serving_size', 0) * food.get('protein_content', 0) / 100
            for food in foods_info
        )
        
        if total_protein_weight == 0:
            return 1.0
        
        high_quality_protein = sum(
            food.get('serving_size', 0) * food.get('protein_content', 0) / 100
            for food in foods_info
            if food.get('food_group_id') in high_quality_groups
        )
        
        quality_ratio = high_quality_protein / total_protein_weight
        return 1.0 + (quality_ratio * 0.2)  # Up to 20% bonus

    @classmethod
    def _assess_fvnl_naturalness(cls, foods_info: List[Dict]) -> float:
        """Assess how 'natural' the FVNL content is"""
        if not foods_info:
            return 1.0
        
        # Whole fruits/vegetables score higher than processed versions
        whole_fvnl_foods = sum(
            1 for food in foods_info
            if food.get('food_group_id') in [9, 11, 12, 16] and  # F, V, N, L groups
               food.get('processing_level') == 'minimally_processed'
        )
        
        total_fvnl_foods = sum(
            1 for food in foods_info
            if food.get('food_group_id') in [9, 11, 12, 16]
        )
        
        if total_fvnl_foods == 0:
            return 1.0
        
        return whole_fvnl_foods / total_fvnl_foods

    @classmethod
    def convert_to_legacy_format(cls, hsr_thresholds: HSRThresholds, 
                                category: Category) -> Dict[str, Union[List[float], float]]:
        """
        Convert scientific thresholds to legacy format for backward compatibility.
        
        Args:
            hsr_thresholds: Scientific threshold object
            category: HSR category
            
        Returns:
            Legacy threshold format dictionary
        """
        # Convert energy density (kcal/100g) to kJ/100g for legacy compatibility
        energy_kj = [kcal * 4.184 for kcal in hsr_thresholds.energy_density]
        
        # For now, use blended sugar thresholds (will be enhanced in calculator)
        sugar_thresholds = hsr_thresholds.sugar_natural  # Default to natural
        
        return {
            'energy': energy_kj,
            'saturated_fat': hsr_thresholds.saturated_fat,
            'sugar': sugar_thresholds,
            'sodium': hsr_thresholds.sodium,
            'fvnl': hsr_thresholds.fvnl,
            'protein': hsr_thresholds.protein,
            'fiber': hsr_thresholds.fiber,
            'star_rating': hsr_thresholds.star_rating,
            'base_stars': hsr_thresholds.base_stars
        }

    @classmethod
    def get_threshold_explanation(cls, nutrient: str, value: float, 
                                thresholds: HSRThresholds) -> Dict[str, any]:
        """
        Get explanation for why a nutrient value received certain points.
        
        Args:
            nutrient: Nutrient name
            value: Nutrient value
            thresholds: Scientific thresholds used
            
        Returns:
            Dictionary with explanation and recommendations
        """
        threshold_list = getattr(thresholds, nutrient, [])
        if not threshold_list:
            return {"explanation": "No thresholds available", "recommendations": []}
        
        # Find position in thresholds
        points = 0
        for i, threshold in enumerate(threshold_list):
            if value >= threshold:
                points = i
            else:
                break
        
        percentile = (points / len(threshold_list)) * 100
        
        explanation = {
            "value": value,
            "points": points,
            "percentile": percentile,
            "threshold_used": threshold_list[points] if points < len(threshold_list) else threshold_list[-1],
            "scientific_rationale": cls._get_rationale(nutrient, percentile),
            "recommendations": cls._get_nutrient_recommendations(nutrient, value, percentile)
        }
        
        return explanation

    @classmethod
    def _get_rationale(cls, nutrient: str, percentile: float) -> str:
        """Get scientific rationale for nutrient threshold placement"""
        rationales = {
            "energy_density": {
                "low": "Low energy density foods promote satiety with fewer calories",
                "medium": "Moderate energy density - balanced nutritional value",
                "high": "High energy density requires portion awareness for weight management"
            },
            "sugar_natural": {
                "low": "Low natural sugar content - minimal impact on blood glucose",
                "medium": "Moderate natural sugars from fruits - provides nutrients and fiber",
                "high": "High natural sugar content - consider portion sizes and pairing with protein/fiber"
            },
            "sugar_added": {
                "low": "Low added sugar aligns with WHO recommendations (<10% of energy)",
                "medium": "Moderate added sugar - monitor daily intake",
                "high": "High added sugar exceeds health guidelines - limit consumption"
            }
        }
        
        level = "high" if percentile >= 70 else "medium" if percentile >= 30 else "low"
        return rationales.get(nutrient, {}).get(level, "Standard nutritional guidelines applied")

    @classmethod
    def _get_nutrient_recommendations(cls, nutrient: str, value: float, percentile: float) -> List[str]:
        """Get specific recommendations based on nutrient value and percentile"""
        recommendations = []
        
        if nutrient == "energy_density" and percentile >= 70:
            recommendations.extend([
                "Consider smaller portions",
                "Pair with low-energy density foods like vegetables",
                "Increase physical activity if consumed regularly"
            ])
        elif nutrient == "sugar_added" and percentile >= 50:
            recommendations.extend([
                "Look for unsweetened alternatives",
                "Consider fresh fruits for natural sweetness",
                "Check ingredient lists for hidden sugars"
            ])
        elif nutrient == "sodium" and percentile >= 60:
            recommendations.extend([
                "Choose low-sodium alternatives when available",
                "Balance with potassium-rich foods",
                "Limit frequency of consumption"
            ])
        elif nutrient == "fiber" and percentile <= 30:
            recommendations.extend([
                "Add fruits or vegetables to increase fiber",
                "Choose whole grain alternatives",
                "Consider legumes or nuts as additions"
            ])
        
        return recommendations 