"""
Food Group Mapper for HSR Calculator

Maps Canadian Nutrient File food groups to Health Star Rating categories
with comprehensive coverage and intelligent categorization logic.
"""

import re
from typing import Dict, Set
from ..models.category import Category
from ..constants.food_groups import FOOD_GROUPS


class FoodGroupMapper:
    """
    Comprehensive mapper that covers all CNF food groups and provides
    intelligent categorization for HSR calculation.
    """
    
    # Food group mappings based on nutritional profiles and HSR category definitions
    FOOD_GROUP_MAPPINGS: Dict[int, Category] = {
        # Dairy and Egg Products (1) - Split by product type
        1: Category.DAIRY_FOOD,  # Default, but will use intelligent detection
        
        # Spices and Herbs (2) - Minimal nutritional impact
        2: Category.FOOD,
        
        # Baby Foods (3) - Special nutritional requirements
        3: Category.FOOD,
        
        # Fats and Oils (4) - Oils and spreads category
        4: Category.OILS_AND_SPREADS,
        
        # Poultry Products (5) - Regular food
        5: Category.FOOD,
        
        # Soups, Sauces and Gravies (6) - Regular food (may contain dairy)
        6: Category.FOOD,
        
        # Sausages and Luncheon meats (7) - Processed meat
        7: Category.FOOD,
        
        # Breakfast cereals (8) - Regular food
        8: Category.FOOD,
        
        # Fruits and fruit juices (9) - Split between food and beverage
        9: Category.FOOD,  # Default, but juices will be detected as beverages
        
        # Pork Products (10) - Regular food
        10: Category.FOOD,
        
        # Vegetables and Vegetable Products (11) - Regular food
        11: Category.FOOD,
        
        # Nuts and Seeds (12) - High fat content, but nutritious
        12: Category.FOOD,
        
        # Beef Products (13) - Regular food
        13: Category.FOOD,
        
        # Beverages (14) - Beverage category
        14: Category.BEVERAGE,
        
        # Finfish and Shellfish Products (15) - Regular food
        15: Category.FOOD,
        
        # Legumes and Legume Products (16) - Regular food
        16: Category.FOOD,
        
        # Lamb, Veal and Game (17) - Regular food
        17: Category.FOOD,
        
        # Baked Products (18) - Regular food
        18: Category.FOOD,
        
        # Sweets (19) - Regular food (high sugar)
        19: Category.FOOD,
        
        # Cereals, Grains and Pasta (20) - Regular food
        20: Category.FOOD,
        
        # Fast Foods (21) - Regular food (processed)
        21: Category.FOOD,
        
        # Mixed Dishes (22) - Regular food
        22: Category.FOOD,
        
        # Snacks (25) - Regular food
        25: Category.FOOD,
    }
    
    # Keywords for intelligent detection
    CHEESE_KEYWORDS: Set[str] = {
        'cheese', 'cheddar', 'mozzarella', 'parmesan', 'brie', 'camembert',
        'gouda', 'swiss', 'blue', 'feta', 'cottage cheese', 'cream cheese',
        'ricotta', 'provolone', 'gruyere'
    }
    
    BEVERAGE_KEYWORDS: Set[str] = {
        'juice', 'drink', 'beverage', 'soda', 'cola', 'water', 'tea', 'coffee',
        'smoothie', 'shake', 'lemonade', 'cocktail', 'beer', 'wine', 'alcohol'
    }
    
    DAIRY_BEVERAGE_KEYWORDS: Set[str] = {
        'milk', 'yogurt drink', 'kefir', 'buttermilk', 'chocolate milk',
        'flavoured milk', 'milk shake', 'dairy drink'
    }
    
    OIL_SPREAD_KEYWORDS: Set[str] = {
        'oil', 'butter', 'margarine', 'spread', 'shortening', 'lard',
        'ghee', 'cooking fat', 'vegetable oil', 'olive oil'
    }

    @classmethod
    def get_category(cls, food_group_id: int, food_name: str) -> Category:
        """
        Determine HSR category using food group and intelligent name detection.
        
        Args:
            food_group_id: CNF food group ID
            food_name: Food description for intelligent detection
            
        Returns:
            Category: Appropriate HSR category
        """
        food_name_lower = food_name.lower()
        
        # Get base category from food group
        base_category = cls.FOOD_GROUP_MAPPINGS.get(food_group_id, Category.FOOD)
        
        # Apply intelligent detection rules using word boundaries
        
        # 1. Cheese detection (overrides dairy food)
        if food_group_id == 1 and cls._contains_keyword(food_name_lower, cls.CHEESE_KEYWORDS):
            return Category.CHEESE
        
        # 2. Dairy beverage detection
        if food_group_id == 1 and cls._contains_keyword(food_name_lower, cls.DAIRY_BEVERAGE_KEYWORDS):
            return Category.DAIRY_BEVERAGE
        
        # 3. Regular beverage detection (for fruit juices, etc.)
        if food_group_id == 9 and cls._contains_keyword(food_name_lower, cls.BEVERAGE_KEYWORDS):
            return Category.BEVERAGE
        
        # 4. Dairy beverage in beverage group
        if food_group_id == 14 and cls._contains_keyword(food_name_lower, cls.DAIRY_BEVERAGE_KEYWORDS):
            return Category.DAIRY_BEVERAGE
        
        # 5. Oil/spread detection (for mixed products) - now with word boundaries
        if cls._contains_keyword(food_name_lower, cls.OIL_SPREAD_KEYWORDS):
            return Category.OILS_AND_SPREADS
        
        return base_category

    @classmethod
    def _contains_keyword(cls, text: str, keywords: Set[str]) -> bool:
        """
        Check if text contains any of the keywords using word boundaries.
        This prevents false positives like "boiled" matching "oil".
        """
        for keyword in keywords:
            # Use word boundaries to match whole words only
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def get_food_group_info(cls, food_group_id: int) -> Dict[str, str]:
        """
        Get descriptive information about a food group.
        
        Args:
            food_group_id: CNF food group ID
            
        Returns:
            Dict with food group information
        """
        category = cls.FOOD_GROUP_MAPPINGS.get(food_group_id, Category.FOOD)
        
        return {
            'food_group_id': food_group_id,
            'food_group_name': FOOD_GROUPS.get(food_group_id, 'Unknown'),
            'hsr_category': category.value,
            'category_name': category.name
        }

    @classmethod
    def validate_category_assignment(cls, food_group_id: int, food_name: str, 
                                   calculated_category: Category) -> Dict[str, any]:
        """
        Validate and provide confidence score for category assignment.
        
        Args:
            food_group_id: CNF food group ID
            food_name: Food description
            calculated_category: Assigned category
            
        Returns:
            Dict with validation info and confidence score
        """
        confidence = 1.0
        warnings = []
        
        # Check for potential misclassifications
        food_name_lower = food_name.lower()
        
        if food_group_id == 1:  # Dairy products
            if calculated_category == Category.FOOD:
                if not any(keyword in food_name_lower for keyword in ['egg', 'powder', 'substitute']):
                    confidence = 0.7
                    warnings.append("Dairy product classified as regular food")
        
        if calculated_category == Category.BEVERAGE and food_group_id not in [9, 14]:
            confidence = 0.8
            warnings.append("Non-beverage group classified as beverage")
        
        return {
            'confidence': confidence,
            'warnings': warnings,
            'validated': confidence >= 0.8
        } 