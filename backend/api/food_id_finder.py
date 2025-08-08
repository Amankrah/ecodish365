import pandas as pd
import logging
from typing import List, Tuple, Optional, Dict, Set
from fuzzywuzzy import fuzz
import re
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_food_data() -> Optional[pd.DataFrame]:
    try:
        with open('raw_cnf/FOOD_NAME.csv', 'r', encoding='ISO-8859-1') as file:
            df = pd.read_csv(file)
            logger.info(f"Loaded {len(df)} rows from FOOD_NAME.csv")
            logger.info(f"Initial columns: {df.columns}")
            
            # Ensure required columns are present
            if 'FoodID' not in df.columns or 'FoodDescription' not in df.columns:
                logger.error("Required columns 'FoodID' or 'FoodDescription' are missing from the CSV file")
                return None
            
            # Preprocess food descriptions and extract metadata
            df['FoodDescription_processed'] = df['FoodDescription'].apply(preprocess_text)
            df['food_category'] = df['FoodDescription'].apply(extract_food_category) 
            df['preparation_method'] = df['FoodDescription'].apply(extract_preparation_method)
            logger.info("Added processed columns: FoodDescription_processed, food_category, preparation_method")
            logger.info(f"Final columns: {df.columns}")
            
            # Verify the columns were added
            required_cols = ['FoodDescription_processed', 'food_category', 'preparation_method']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Failed to add required columns: {required_cols}")
                return None
            
            return df
    except FileNotFoundError:
        logger.error("FOOD_NAME.csv file not found. Please ensure it's in the 'raw_cnf' directory.")
        return None
    except Exception as e:
        logger.error(f"Error loading food data: {str(e)}")
        return None

def preprocess_text(text: str) -> str:
    # Convert to lowercase, preserve commas and parentheses for better parsing
    text = re.sub(r'[^a-zA-Z0-9\s,()%-]', '', str(text).lower())
    # Remove extra spaces but preserve structure
    return ' '.join(text.split())

def extract_food_category(description: str) -> str:
    """Extract primary food category from description"""
    description_lower = description.lower()
    
    # Common food categories based on the data structure
    categories = {
        'cheese': ['cheese'],
        'chicken': ['chicken'],
        'turkey': ['turkey'], 
        'beef': ['beef'],
        'pork': ['pork'],
        'fish': ['fish', 'salmon', 'tuna', 'cod', 'sardine'],
        'soup': ['soup'],
        'sauce': ['sauce', 'gravy'],
        'milk': ['milk'],
        'egg': ['egg'],
        'cereal': ['cereal'],
        'bread': ['bread', 'muffin', 'bagel'],
        'vegetable': ['carrot', 'broccoli', 'spinach', 'lettuce', 'tomato'],
        'fruit': ['apple', 'banana', 'orange', 'grape', 'berry'],
        'spice': ['spice', 'salt', 'pepper', 'basil', 'garlic'],
        'oil': ['oil', 'butter', 'margarine'],
        'pasta': ['pasta', 'noodle', 'spaghetti'],
        'rice': ['rice'],
        'bean': ['bean', 'lentil', 'pea']
    }
    
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    
    return 'other'

def extract_preparation_method(description: str) -> str:
    """Extract preparation method from description"""
    description_lower = description.lower()
    
    methods = {
        'raw': ['raw'],
        'cooked': ['cooked', 'boiled', 'steamed'],
        'fried': ['fried', 'deep fried'],
        'baked': ['baked', 'roasted'],
        'grilled': ['grilled'],
        'canned': ['canned', 'conserve'],
        'frozen': ['frozen'],
        'dried': ['dried', 'dry'],
        'fresh': ['fresh'],
        'smoked': ['smoked']
    }
    
    for method, keywords in methods.items():
        if any(keyword in description_lower for keyword in keywords):
            return method
    
    return 'unspecified'

def parse_search_query(query: str) -> Dict[str, str]:
    """Parse search query to extract filters and main search term"""
    result = {'query': query, 'category': None, 'method': None}
    
    # Look for category filters like "category:cheese" or "type:chicken"
    category_match = re.search(r'(?:category|type):([a-zA-Z]+)', query)
    if category_match:
        result['category'] = category_match.group(1).lower()
        query = re.sub(r'(?:category|type):[a-zA-Z]+\s*', '', query)
    
    # Look for preparation method filters like "method:cooked" or "prep:raw" 
    method_match = re.search(r'(?:method|prep):([a-zA-Z]+)', query)
    if method_match:
        result['method'] = method_match.group(1).lower()
        query = re.sub(r'(?:method|prep):[a-zA-Z]+\s*', '', query)
    
    result['query'] = query.strip()
    return result

def calculate_relevance_score(food_name: str, processed_food_name: str, processed_query: str, 
                            category: str, method: str, query_filters: Dict[str, str]) -> int:
    """Enhanced relevance scoring with category and method awareness"""
    
    # Base fuzzy matching scores
    ratio = fuzz.ratio(processed_query, processed_food_name)
    partial_ratio = fuzz.partial_ratio(processed_query, processed_food_name)
    token_set_ratio = fuzz.token_set_ratio(processed_query, processed_food_name)
    
    # Word matching
    query_words = processed_query.split()
    word_match = sum(word in processed_food_name for word in query_words)
    exact_matches = sum(1 for word in query_words if f' {word} ' in f' {processed_food_name} ')
    
    # Position bonuses
    starts_with_bonus = 100 if processed_food_name.startswith(processed_query) else 0
    exact_match_bonus = 200 if processed_query == processed_food_name else 0
    
    # Category and method filtering bonuses
    category_bonus = 0
    method_bonus = 0
    
    if query_filters['category']:
        if category == query_filters['category']:
            category_bonus = 150
        else:
            # Penalize non-matching categories heavily when filter is specified
            return 0
    
    if query_filters['method']:
        if method == query_filters['method']:
            method_bonus = 100
        else:
            # Penalize non-matching methods when filter is specified  
            return max(0, ratio // 2)
    
    # Implicit category matching (when no explicit filter)
    if not query_filters['category'] and processed_query:
        first_word = query_words[0] if query_words else ''
        if first_word == category:
            category_bonus = 75
    
    # Base score calculation
    base_score = (ratio * 1 + partial_ratio * 2 + token_set_ratio * 3 + 
                  word_match * 15 + exact_matches * 40)
    
    total_score = (base_score + starts_with_bonus + exact_match_bonus + 
                   category_bonus + method_bonus)
    
    return total_score

def search_food(query: str, food_df: pd.DataFrame, limit: int = 50, 
                category_filter: str = None, method_filter: str = None) -> List[Tuple[int, str, int]]:
    """Enhanced food search with category and method filtering"""
    logger.debug(f"Searching for: {query}")
    logger.debug(f"DataFrame columns: {food_df.columns}")
    
    required_cols = ['FoodDescription', 'FoodDescription_processed', 'food_category', 'preparation_method']
    if not all(col in food_df.columns for col in required_cols):
        logger.error(f"Required columns are missing from the DataFrame: {required_cols}")
        return []
    
    if len(query.strip()) < 2:
        return []
    
    # Parse query for filters
    query_filters = parse_search_query(query)
    processed_query = preprocess_text(query_filters['query'])
    
    # Override with explicit filters if provided
    if category_filter:
        query_filters['category'] = category_filter
    if method_filter:
        query_filters['method'] = method_filter
    
    logger.debug(f"Processed query: {processed_query}")
    logger.debug(f"Query filters: {query_filters}")
    
    # Pre-filter data if explicit filters are provided
    filtered_df = food_df.copy()
    if query_filters['category']:
        filtered_df = filtered_df[filtered_df['food_category'] == query_filters['category']]
        logger.debug(f"Filtered by category '{query_filters['category']}': {len(filtered_df)} items")
    
    if query_filters['method']:
        filtered_df = filtered_df[filtered_df['preparation_method'] == query_filters['method']]
        logger.debug(f"Filtered by method '{query_filters['method']}': {len(filtered_df)} items")
    
    if filtered_df.empty:
        logger.debug("No items match the filters")
        return []
    
    try:
        filtered_df['relevance_score'] = filtered_df.apply(
            lambda row: calculate_relevance_score(
                row['FoodDescription'], 
                row['FoodDescription_processed'], 
                processed_query,
                row['food_category'],
                row['preparation_method'],
                query_filters
            ), axis=1
        )
    except KeyError as e:
        logger.error(f"KeyError during relevance score calculation: {str(e)}")
        logger.error(f"DataFrame columns: {filtered_df.columns}")
        return []
    except Exception as e:
        logger.error(f"Error during relevance score calculation: {str(e)}")
        return []

    # Filter out very low scores and sort by relevance
    filtered_df = filtered_df[filtered_df['relevance_score'] > 10]
    top_matches = filtered_df.nlargest(limit, 'relevance_score')
    
    logger.debug(f"Found {len(top_matches)} matches")
    return [(row['FoodID'], row['FoodDescription'], row['relevance_score']) 
            for _, row in top_matches.iterrows()]

def get_food_categories(food_df: pd.DataFrame) -> List[str]:
    """Get list of available food categories"""
    if 'food_category' not in food_df.columns:
        return []
    return sorted(food_df['food_category'].unique().tolist())

def get_preparation_methods(food_df: pd.DataFrame) -> List[str]:
    """Get list of available preparation methods"""
    if 'preparation_method' not in food_df.columns:
        return []
    return sorted(food_df['preparation_method'].unique().tolist())

