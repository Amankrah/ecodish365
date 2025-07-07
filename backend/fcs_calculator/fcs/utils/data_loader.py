import pandas as pd
from functools import lru_cache
import logging
from typing import Tuple
from fcs.config import CNF_NUTRIENT_NAME_PATH, CNF_NUTRIENT_AMOUNT_PATH
import chardet

logger = logging.getLogger(__name__)

def detect_encoding(file_path: str) -> str:
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

@lru_cache(maxsize=2)
def load_cnf_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    try:
        # Detect encoding for nutrient name file
        nutrient_name_encoding = detect_encoding(CNF_NUTRIENT_NAME_PATH)
        logger.info(f"Detected encoding for nutrient name file: {nutrient_name_encoding}")

        # Detect encoding for nutrient amount file
        nutrient_amount_encoding = detect_encoding(CNF_NUTRIENT_AMOUNT_PATH)
        logger.info(f"Detected encoding for nutrient amount file: {nutrient_amount_encoding}")

        # Load nutrient name data
        nutrient_name_df = pd.read_csv(CNF_NUTRIENT_NAME_PATH, encoding=nutrient_name_encoding)
        logger.info(f"Nutrient name columns: {nutrient_name_df.columns.tolist()}")

        # Load nutrient amount data with specified dtypes
        dtypes = {
            'FoodID': 'Int64',
            'NutrientID': 'Int64',
            'NutrientValue': float,
            'StandardError': float,
            'NumberOfObservations': 'Int64',
            'NutrientSourceID': 'Int64',
        }
        parse_dates = ['NutrientDateOfEntry']

        nutrient_amount_df = pd.read_csv(CNF_NUTRIENT_AMOUNT_PATH, 
                                         encoding=nutrient_amount_encoding,
                                         dtype=dtypes,
                                         parse_dates=parse_dates,
                                         low_memory=False)
        logger.info(f"Nutrient amount columns: {nutrient_amount_df.columns.tolist()}")

        logger.info("CNF data loaded successfully")
        return nutrient_name_df, nutrient_amount_df
    except Exception as e:
        logger.error(f"Error loading CNF data: {e}")
        raise