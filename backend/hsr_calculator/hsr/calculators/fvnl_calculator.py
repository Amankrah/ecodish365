import re
from typing import Dict, List
from ..utils.data_loader import load_cnf_data
from ..constants.food_groups import FVNL_GROUPS

def calculate_fvnl_content(food_id: int) -> float:
    """
    Calculate FVNL (Fruits, Vegetables, Nuts, Legumes) content percentage.
    
    Uses a nuanced approach based on Canadian Nutrient File patterns:
    1. Primary food group classification
    2. CNF-specific food name analysis
    3. Processing level adjustments
    4. Mixed food ingredient detection
    
    Returns:
        float: FVNL percentage (0-100)
    """
    food_name_df, _, _, food_group_df = load_cnf_data()
    
    try:
        food_row = food_name_df[food_name_df['FoodID'] == food_id].iloc[0]
        food_name = food_row['FoodDescription'].lower()
        food_group_id = food_row['FoodGroupID']
        
        # Get food group info
        food_group_row = food_group_df[food_group_df['FoodGroupID'] == food_group_id].iloc[0]
        food_group_code = food_group_row['FoodGroupCode']
        
        return _calculate_nuanced_fvnl(food_name, food_group_code, food_group_id)
        
    except (IndexError, KeyError):
        # Fallback for missing data
        return 0.0

def _calculate_nuanced_fvnl(food_name: str, food_group_code: int, food_group_id: int) -> float:
    """
    Calculate nuanced FVNL percentage based on CNF food characteristics.
    
    Args:
        food_name: Lowercase food description
        food_group_code: CNF food group code  
        food_group_id: CNF food group ID
        
    Returns:
        float: FVNL percentage (0-100)
    """
    
    # Base FVNL percentage for pure FVNL food groups
    if food_group_code in FVNL_GROUPS:
        base_fvnl = _get_base_fvnl_for_group(food_group_id, food_name)
        
        # Apply processing penalties
        processing_factor = _get_cnf_processing_factor(food_name)
        
        return base_fvnl * processing_factor
    
    # Check for mixed foods with FVNL content
    mixed_fvnl = _estimate_cnf_mixed_food_fvnl(food_name, food_group_id)
    return mixed_fvnl

def _get_base_fvnl_for_group(food_group_id: int, food_name: str) -> float:
    """Get base FVNL percentage for pure FVNL food groups based on CNF patterns."""
    
    if food_group_id == 9:  # Fruits and fruit juices
        # CNF patterns: "Apple juice, canned" vs "Apple, raw, with skin"
        if any(term in food_name for term in ['juice', 'nectar', 'drink', 'cocktail']):
            if 'concentrate' in food_name:
                return 50.0  # Concentrated juices
            return 67.0  # Regular fruit juices
        elif any(term in food_name for term in ['dried', 'dehydrated']):
            return 90.0  # Dried fruits (concentrated but still whole fruit)
        return 100.0  # Fresh fruits
        
    elif food_group_id == 11:  # Vegetables and Vegetable Products
        return 100.0  # All vegetables get 100%
        
    elif food_group_id == 12:  # Nuts and Seeds  
        return 100.0  # All nuts and seeds get 100%
        
    elif food_group_id == 16:  # Legumes and Legume Products
        return 100.0  # All legumes get 100%
    
    return 0.0

def _get_cnf_processing_factor(food_name: str) -> float:
    """
    Apply processing penalty factor based on CNF processing descriptions.
    
    Returns:
        float: Factor between 0.5-1.0 based on processing level
    """
    
    # CNF High processing patterns (heavy penalty)
    high_processing_patterns = [
        r'\b(battered|breaded|fried|deep.?fried)\b',
        r'\b(candied|sweetened.*syrup|extra heavy syrup)\b',
        r'\b(jam|jelly|preserve|marmalade)\b'
    ]
    
    # CNF Medium processing patterns (moderate penalty)
    medium_processing_patterns = [
        r'\bcanned.*(?:heavy syrup|light syrup|syrup pack)\b',
        r'\b(canned|preserved|pickled)\b',
        r'\b(dried|dehydrated|freeze.?dried)\b',
        r'\b(frozen.*sweetened|frozen.*heated)\b'
    ]
    
    # CNF Light processing patterns (minimal penalty) - Basic cooking methods
    light_processing_patterns = [
        r'\bcanned.*(?:water pack|juice pack|no.*sugar)\b',
        r'\b(frozen.*unsweetened|frozen.*unprepared)\b',
        r'\bunsweetened\b',
        r'\b(cooked|boiled|steamed|baked|roasted|grilled|drained)\b'  # Moved basic cooking here
    ]
    
    # CNF Minimal processing patterns (no penalty)
    minimal_processing_patterns = [
        r'\b(raw|fresh)\b',
        r'\bwith skin\b',
        r'\bunprepared\b'
    ]
    
    # Check patterns in order of severity
    for pattern in high_processing_patterns:
        if re.search(pattern, food_name):
            return 0.5  # 50% penalty for high processing
    
    for pattern in medium_processing_patterns:
        if re.search(pattern, food_name):
            return 0.75  # 25% penalty for medium processing
    
    for pattern in light_processing_patterns:
        if re.search(pattern, food_name):
            return 0.95  # 5% penalty for light processing (basic cooking)
    
    for pattern in minimal_processing_patterns:
        if re.search(pattern, food_name):
            return 1.0  # No penalty for minimal processing
    
    return 0.9  # Default 10% penalty for unknown processing

def _estimate_cnf_mixed_food_fvnl(food_name: str, food_group_id: int) -> float:
    """
    Estimate FVNL content for mixed foods based on CNF naming patterns.
    
    Returns:
        float: Estimated FVNL percentage (0-100)
    """
    
    # CNF-specific FVNL ingredient patterns with weights
    fvnl_patterns = {
        # Specific fruit patterns from CNF
        r'\b(apple|apricot|banana|berry|blueberry|blackberry|cherry|cranberry|grape|grapefruit|lemon|lime|orange|peach|pear|pineapple|plum|strawberry|watermelon|melon)\b': 45,
        r'\bfruit\b': 35,
        
        # Specific vegetable patterns from CNF
        r'\b(tomato|carrot|broccoli|spinach|lettuce|onion|pepper|potato|sweet potato|corn|peas|beans|bean|celery|mushroom|cabbage|cucumber|asparagus)\b': 40,
        r'\bvegetable\b': 35,
        
        # Specific nut patterns from CNF
        r'\b(almond|walnut|peanut|cashew|pecan|hazelnut|pine nut|coconut|sesame|sunflower)\b': 25,
        r'\bnut\b': 20,
        
        # Legume patterns from CNF
        r'\b(lentil|chickpea|kidney bean|lima bean|navy bean|black bean|soy|tofu)\b': 30,
        
        # Mixed dish indicators based on CNF patterns
        r'\bsalad\b': 70,  # "Potato salad", "Coleslaw"
        r'\bsoup.*(?:vegetable|tomato|pea|bean|lentil)\b': 45,
        r'\bstir.?fry\b': 35,
        r'\bchow mein\b': 25,  # "Chinese dish, chow mein, chicken"
        r'\bpot roast.*(?:potato|peas|corn)\b': 30,  # "Beef pot roast, with browned potatoes, peas and corn"
        r'\bsauce.*(?:tomato|onion|pepper|mushroom)\b': 40,  # Various sauces with vegetables
    }
    
    # CNF composite dish patterns (foods explicitly "with" vegetables)
    with_vegetable_patterns = [
        r'\bwith.*(?:potato|peas|corn|carrot|onion|pepper|tomato|mushroom|vegetable)\b',
        r'\band.*(?:potato|peas|corn|carrot|onion|pepper|tomato|mushroom|vegetable)\b'
    ]
    
    max_fvnl = 0.0
    
    # Check main FVNL patterns
    for pattern, fvnl_value in fvnl_patterns.items():
        if re.search(pattern, food_name):
            max_fvnl = max(max_fvnl, fvnl_value)
    
    # Check for "with vegetables" patterns
    for pattern in with_vegetable_patterns:
        if re.search(pattern, food_name):
            max_fvnl = max(max_fvnl, 25.0)
    
    # Food group specific adjustments based on CNF structure
    if food_group_id == 22:  # Mixed Dishes
        if max_fvnl == 0:
            # Assume minimal FVNL content in mixed dishes
            return 5.0
        else:
            # Boost detected FVNL in mixed dishes
            return min(max_fvnl * 1.2, 80.0)
            
    elif food_group_id == 6:  # Soups, Sauces and Gravies
        if any(term in food_name for term in ['vegetable', 'tomato', 'onion', 'mushroom', 'celery']):
            return max(max_fvnl, 35.0)
        elif 'soup' in food_name and max_fvnl == 0:
            return 10.0  # Default soup assumption
            
    elif food_group_id == 18:  # Baked Products
        if max_fvnl > 0:
            # Fruit/nut/vegetable in baked goods
            return min(max_fvnl * 0.7, 60.0)  # Reduce for baked matrix
            
    elif food_group_id == 21:  # Fast Foods
        if max_fvnl > 0:
            return min(max_fvnl * 0.8, 50.0)  # Reduce for fast food processing
    
    return max_fvnl