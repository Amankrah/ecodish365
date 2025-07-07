import pandas as pd
from functools import lru_cache
import logging
from typing import Tuple
from ..config import FOOD_NAME_PATH, NUTRIENT_NAME_PATH, NUTRIENT_AMOUNT_PATH, FOOD_GROUP_PATH

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def load_cnf_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    try:
        food_name_df = pd.read_csv(FOOD_NAME_PATH, encoding='ISO-8859-1')
        nutrient_name_df = pd.read_csv(NUTRIENT_NAME_PATH, encoding='ISO-8859-1')
        nutrient_amount_df = pd.read_csv(NUTRIENT_AMOUNT_PATH, encoding='ISO-8859-1')
        food_group_df = pd.read_csv(FOOD_GROUP_PATH, encoding='ISO-8859-1')
        return food_name_df, nutrient_name_df, nutrient_amount_df, food_group_df
    except FileNotFoundError as e:
        logger.error(f"Error loading CNF data: {e}")
        raise