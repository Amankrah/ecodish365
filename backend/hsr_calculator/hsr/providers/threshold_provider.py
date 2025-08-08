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
    energy: List[float]          # kJ/100g
    sugar: List[float]           # g/100g (ALL sugars treated identically)
    saturated_fat: List[float]   # g/100g
    sodium: List[float]          # mg/100g
    fvnl: List[float]           # %
    protein: List[float]         # g/100g
    fiber: List[float]           # g/100g
    star_thresholds: List[float] # Score thresholds for star conversion


class ThresholdProvider:
    """
    Provides scientifically-based thresholds that address the core issues
    in the original HSR algorithm.
    """
    
    # Official HSR Category-Specific Thresholds
    
    # Category 1: Non-dairy beverages, fruit/vegetable juices, plain water
    CATEGORY_1_THRESHOLDS = {
        'energy': [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300],  # kJ/100g
        'saturated_fat': [float('inf')] * 11,  # Not applicable
        'sugar': [0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5, 15],  # g/100g
        'sodium': [0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900],  # mg/100g
        'fvnl': [40, 60, 67, 75, 80, 85, 90, 95, 100],  # %
        'protein': [0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.8, 5.6, 6.4, 7.2, 8.0],  # g/100g
        'fiber': [float('inf')] * 11,  # Not applicable for beverages
        'star_thresholds': [4, 5, 6, 7, 8, 9, 10, 11]  # Score to star conversion
    }
    
    # Category 1D: Dairy beverages (including milk, flavored milk, dairy alternatives)
    CATEGORY_1D_THRESHOLDS = {
        'energy': [0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800],  # kJ/100g
        'saturated_fat': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # g/100g
        'sugar': [0, 4.5, 9, 13.5, 18, 22.5, 27, 31.5, 36, 40.5, 45],  # g/100g
        'sodium': [0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900],  # mg/100g
        'fvnl': [40, 60, 67, 75, 80, 85, 90, 95, 100],  # %
        'protein': [0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0],  # g/100g
        'fiber': [float('inf')] * 11,  # Not applicable for beverages
        'star_thresholds': [2, 3, 4, 5, 6, 7, 8, 9]  # Score to star conversion
    }
    
    # Category 2: All other foods except Category 3 (oils, spreads, nuts, seeds)
    CATEGORY_2_THRESHOLDS = {
        'energy': [0, 335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350],  # kJ/100g
        'saturated_fat': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # g/100g
        'sugar': [0, 4.5, 9, 13.5, 18, 22.5, 27, 31.5, 36, 40.5, 45],  # g/100g
        'sodium': [0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900],  # mg/100g
        'fvnl': [40, 60, 67, 75, 80, 85, 90, 95, 100],  # %
        'protein': [0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0],  # g/100g
        'fiber': [0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3],  # g/100g
        'star_thresholds': [-1, 2, 5, 8, 11, 14, 17, 20]  # Score to star conversion
    }
    
    # Category 2D: Dairy products in Category 2 (cheese, yogurt, etc.)
    CATEGORY_2D_THRESHOLDS = {
        'energy': [0, 335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350],  # kJ/100g
        'saturated_fat': [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # g/100g - more lenient for dairy
        'sugar': [0, 4.5, 9, 13.5, 18, 22.5, 27, 31.5, 36, 40.5, 45],  # g/100g
        'sodium': [0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900],  # mg/100g
        'fvnl': [40, 60, 67, 75, 80, 85, 90, 95, 100],  # %
        'protein': [0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0],  # g/100g
        'fiber': [0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3],  # g/100g
        'star_thresholds': [-1, 2, 5, 8, 11, 14, 17, 20]  # Score to star conversion
    }
    
    # Category 3: Oils, spreads, nuts, seeds, nut/seed pastes
    CATEGORY_3_THRESHOLDS = {
        'energy': [0, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000],  # kJ/100g - high energy
        'saturated_fat': [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],  # g/100g
        'sugar': [0, 4.5, 9, 13.5, 18, 22.5, 27, 31.5, 36, 40.5, 45],  # g/100g
        'sodium': [0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900],  # mg/100g
        'fvnl': [40, 60, 67, 75, 80, 85, 90, 95, 100],  # %
        'protein': [0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0],  # g/100g
        'fiber': [0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3],  # g/100g
        'star_thresholds': [0, 3, 6, 9, 12, 15, 18, 21]  # Score to star conversion
    }
    
    # Category 3D: Dairy oils and spreads (butter, dairy-based spreads)
    CATEGORY_3D_THRESHOLDS = {
        'energy': [0, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000],  # kJ/100g
        'saturated_fat': [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40],  # g/100g - very lenient for dairy fats
        'sugar': [0, 4.5, 9, 13.5, 18, 22.5, 27, 31.5, 36, 40.5, 45],  # g/100g
        'sodium': [0, 90, 180, 270, 360, 450, 540, 630, 720, 810, 900],  # mg/100g
        'fvnl': [40, 60, 67, 75, 80, 85, 90, 95, 100],  # %
        'protein': [0, 1.6, 3.2, 4.8, 6.4, 8.0, 9.6, 11.2, 12.8, 14.4, 16.0],  # g/100g
        'fiber': [0, 0.9, 1.9, 2.8, 3.7, 4.7, 5.6, 6.5, 7.4, 8.4, 9.3],  # g/100g
        'star_thresholds': [0, 3, 6, 9, 12, 15, 18, 21]  # Score to star conversion
    }
    
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
    def get_thresholds(cls, category: Category) -> HSRThresholds:
        """
        Get official HSR thresholds based on category.
        
        Args:
            category: HSR category (1, 1D, 2, 2D, 3, 3D)
            
        Returns:
            HSRThresholds object with official category-specific thresholds
        """
        # Map categories to threshold sets
        if category == Category.BEVERAGE:
            thresholds_dict = cls.CATEGORY_1_THRESHOLDS
        elif category == Category.DAIRY_BEVERAGE:
            thresholds_dict = cls.CATEGORY_1D_THRESHOLDS
        elif category == Category.CHEESE:
            thresholds_dict = cls.CATEGORY_2D_THRESHOLDS
        elif category == Category.OILS_AND_SPREADS:
            thresholds_dict = cls.CATEGORY_3_THRESHOLDS
        else:
            # Default to Category 2 for all other foods
            thresholds_dict = cls.CATEGORY_2_THRESHOLDS
        
        return HSRThresholds(
            energy=thresholds_dict['energy'].copy(),
            sugar=thresholds_dict['sugar'].copy(),
            saturated_fat=thresholds_dict['saturated_fat'].copy(),
            sodium=thresholds_dict['sodium'].copy(),
            fvnl=thresholds_dict['fvnl'].copy(),
            protein=thresholds_dict['protein'].copy(),
            fiber=thresholds_dict['fiber'].copy(),
            star_thresholds=thresholds_dict['star_thresholds'].copy()
        )

    @classmethod
    def get_category_from_food(cls, food_name: str, food_group_id: int) -> Category:
        """
        Determine HSR category from food characteristics.
        
        Args:
            food_name: Name of the food
            food_group_id: Food group identifier
            
        Returns:
            Category enum value
        """
        food_name_lower = food_name.lower()
        
        # Category 1: Non-dairy beverages
        if food_group_id in [14, 20] or any(word in food_name_lower for word in ['juice', 'drink', 'beverage', 'soda', 'water']):
            if any(word in food_name_lower for word in ['milk', 'dairy', 'yogurt']):
                return Category.DAIRY_BEVERAGE  # Category 1D
            else:
                return Category.BEVERAGE  # Category 1
        
        # Category 3: Oils, spreads, nuts, seeds  
        if food_group_id in [4, 12] or any(word in food_name_lower for word in ['oil', 'butter', 'spread', 'nut', 'seed', 'paste']):
            return Category.OILS_AND_SPREADS  # Category 3 (includes nuts and seeds)
        
        # Category 2D: Cheese
        if 'cheese' in food_name_lower or food_group_id == 1:
            return Category.CHEESE  # Category 2D
        
        # Default: Category 2 for all other foods
        return Category.FOOD  # Category 2

    @classmethod
    def calculate_hsr_points(cls, value: float, thresholds: List[float]) -> int:
        """
        Calculate HSR points for a nutrient value using standard HSR methodology.
        
        Args:
            value: Nutrient value per 100g
            thresholds: Threshold array for the nutrient
            
        Returns:
            Points scored (0 to number of thresholds)
        """
        if not thresholds or thresholds[0] == float('inf'):
            return 0
        
        points = 0
        for threshold in thresholds:
            if value >= threshold:
                points += 1
            else:
                break
        
        return points

    @classmethod
    def convert_score_to_stars(cls, final_score: int, star_thresholds: List[float]) -> float:
        """
        Convert final HSR score to star rating using official HSR methodology.
        
        Args:
            final_score: Final HSR score (baseline - modifying points)
            star_thresholds: Star conversion thresholds for the category
            
        Returns:
            Star rating (0.5 to 5.0 stars)
        """
        # HSR star rating logic: lower scores = higher stars
        stars = 0.5  # Minimum rating
        
        for i, threshold in enumerate(star_thresholds):
            if final_score <= threshold:
                stars = 5.0 - (i * 0.5)
                break
        
        return max(0.5, min(5.0, stars))


 