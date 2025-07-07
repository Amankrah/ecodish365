import os
import pandas as pd
from chardet import detect
import time
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class CNFDataLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        logger.info(f"Initializing CNFDataLoader with data directory: {self.data_dir}")
        self.load_all_dataframes()

    def load_all_dataframes(self):
        csv_files = [
            'FOOD_NAME', 'NUTRIENT_AMOUNT', 'CONVERSION_FACTOR', 'FOOD_GROUP',
            'FOOD_SOURCE', 'NUTRIENT_NAME', 'NUTRIENT_SOURCE', 'MEASURE_NAME',
            'REFUSE_AMOUNT', 'YIELD_AMOUNT', 'REFUSE_NAME', 'YIELD_NAME'
        ]
        for file in csv_files:
            df_name = f"{file.lower()}_df"
            try:
                setattr(self, df_name, self._load_csv(f"{file}.csv"))
            except FileNotFoundError:
                logger.warning(f"File not found: {file}.csv")
            except Exception as e:
                logger.exception(f"Error loading {file}.csv")

    def _detect_encoding(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                return detect(f.read())['encoding']
        except Exception:
            logger.exception(f"Error detecting encoding for {file_path}")
            return 'utf-8'

    def _load_csv(self, file_name):
        file_path = os.path.join(self.data_dir, file_name)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No such file or directory: '{file_path}'")
        
        encoding = self._detect_encoding(file_path)
        
        dtypes = {
            'FoodID': 'Int64',
            'FoodCode': 'str',
            'FoodGroupID': 'Int64',
            'FoodSourceID': 'Int64',
            'NutrientID': 'Int64',
            'NutrientSourceID': 'Int64',
            'MeasureID': 'Int64',
            'RefuseID': 'Int64',
            'YieldID': 'Int64'
        }
        
        df = pd.read_csv(file_path, encoding=encoding, low_memory=False, dtype=dtypes)
        
        date_columns = [col for col in df.columns if 'Date' in col]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df

    def save_csv(self, df, file_name, max_retries=3, retry_delay=1):
        file_path = os.path.join(self.data_dir, file_name)
        encoding = self._detect_encoding(file_path)
        
        for attempt in range(max_retries):
            try:
                df.to_csv(file_path, index=False, encoding=encoding)
                self.reload_dataframe(file_name)
                return
            except PermissionError:
                if attempt < max_retries - 1:
                    logger.warning(f"Unable to save {file_name}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to save {file_name} after {max_retries} attempts. Please ensure the file is not open in another program.")

    def reload_dataframe(self, file_name):
        df_name = file_name.replace('.csv', '').lower()
        try:
            setattr(self, f"{df_name}_df", self._load_csv(file_name))
        except Exception:
            logger.exception(f"Error reloading {file_name}")