import pandas as pd
import logging
from typing import List, Tuple, Optional
from fuzzywuzzy import fuzz
import re

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
            
            # Preprocess food descriptions
            df['FoodDescription_processed'] = df['FoodDescription'].apply(preprocess_text)
            logger.info("Added 'FoodDescription_processed' column")
            logger.info(f"Final columns: {df.columns}")
            
            # Verify the column was added
            if 'FoodDescription_processed' not in df.columns:
                logger.error("Failed to add 'FoodDescription_processed' column")
                return None
            
            return df
    except FileNotFoundError:
        logger.error("FOOD_NAME.csv file not found. Please ensure it's in the 'raw_cnf' directory.")
        return None
    except Exception as e:
        logger.error(f"Error loading food data: {str(e)}")
        return None

def preprocess_text(text: str) -> str:
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', str(text).lower())
    # Remove extra spaces
    return ' '.join(text.split())

def relevance_score(food_name: str, processed_food_name: str, processed_query: str) -> int:
    ratio = fuzz.ratio(processed_query, processed_food_name)
    partial_ratio = fuzz.partial_ratio(processed_query, processed_food_name)
    token_set_ratio = fuzz.token_set_ratio(processed_query, processed_food_name)
    
    query_words = processed_query.split()
    word_match = sum(word in processed_food_name for word in query_words)
    
    # Check for exact word matches
    exact_matches = sum(1 for word in query_words if f' {word} ' in f' {processed_food_name} ')
    
    # Prioritize matches at the beginning of the food name
    starts_with_bonus = 50 if processed_food_name.startswith(processed_query) else 0
    
    # Weighted score
    return (ratio * 1 + partial_ratio * 2 + token_set_ratio * 3 + 
            word_match * 10 + exact_matches * 30 + starts_with_bonus)

def search_food(query: str, food_df: pd.DataFrame, limit: int = 50) -> List[Tuple[int, str, int]]:
    logger.debug(f"Searching for: {query}")
    logger.debug(f"DataFrame columns: {food_df.columns}")
    
    if 'FoodDescription' not in food_df.columns or 'FoodDescription_processed' not in food_df.columns:
        logger.error("Required columns are missing from the DataFrame")
        return []
    
    if len(query.strip()) < 2:
        return []
    
    processed_query = preprocess_text(query)
    logger.debug(f"Processed query: {processed_query}")
    
    try:
        food_df['relevance_score'] = food_df.apply(
            lambda row: relevance_score(row['FoodDescription'], row['FoodDescription_processed'], processed_query), axis=1
        )
    except KeyError as e:
        logger.error(f"KeyError during relevance score calculation: {str(e)}")
        logger.error(f"DataFrame columns: {food_df.columns}")
        return []
    except Exception as e:
        logger.error(f"Error during relevance score calculation: {str(e)}")
        return []

    # Sort by relevance score and get top matches
    top_matches = food_df.nlargest(limit, 'relevance_score')
    
    logger.debug(f"Found {len(top_matches)} matches")
    return [(row['FoodID'], row['FoodDescription'], row['relevance_score']) 
            for _, row in top_matches.iterrows() if row['relevance_score'] > 50]

