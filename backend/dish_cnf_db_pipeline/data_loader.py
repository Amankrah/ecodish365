import os
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Every CNF CSV in `raw_cnf/` is either ASCII or ISO-8859-1. latin-1
# decodes every possible byte without error and is a strict superset of
# ASCII, so it's the safe universal choice. Running `chardet.detect` on
# every CSV per load (~1-2 s of work) was superstition — encodings don't
# change.
CNF_CSV_ENCODING = 'ISO-8859-1'

class CNFDataLoader:
    # Canonical list of CNF CSV files. Kept at class level so callers
    # borrowing shared frames (see `shared_source`) can enumerate the
    # exact DataFrame attributes this loader is expected to expose.
    CSV_FILES = (
        'FOOD_NAME', 'NUTRIENT_AMOUNT', 'CONVERSION_FACTOR', 'FOOD_GROUP',
        'FOOD_SOURCE', 'NUTRIENT_NAME', 'NUTRIENT_SOURCE', 'MEASURE_NAME',
        'REFUSE_AMOUNT', 'YIELD_AMOUNT', 'REFUSE_NAME', 'YIELD_NAME',
    )

    def __init__(self, data_dir, *, shared_source=None):
        """Load CNF CSVs, or borrow already-loaded frames from another object.

        When `shared_source` is provided, no file I/O is performed: each
        `*_df` attribute is set by reference to the corresponding attribute
        on `shared_source`. This is how `api.cnf_cache.get_dish_cnf_pipeline`
        avoids loading 12 CSVs a second time — the dish pipeline wraps the
        same pandas frames as the api pipeline.
        """
        self.data_dir = data_dir
        if shared_source is not None:
            logger.info("CNFDataLoader borrowing shared dataframes (no file I/O)")
            for name in self.CSV_FILES:
                attr = f"{name.lower()}_df"
                setattr(self, attr, getattr(shared_source, attr, None))
        else:
            logger.info(f"Initializing CNFDataLoader with data directory: {self.data_dir}")
            self.load_all_dataframes()

    def load_all_dataframes(self):
        for file in self.CSV_FILES:
            df_name = f"{file.lower()}_df"
            try:
                setattr(self, df_name, self._load_csv(f"{file}.csv"))
            except FileNotFoundError:
                logger.warning(f"File not found: {file}.csv")
            except Exception as e:
                logger.exception(f"Error loading {file}.csv")

    def _detect_encoding(self, file_path):
        """Legacy shim — always returns the hard-coded encoding."""
        return CNF_CSV_ENCODING

    def _load_csv(self, file_name):
        file_path = os.path.join(self.data_dir, file_name)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No such file or directory: '{file_path}'")

        encoding = CNF_CSV_ENCODING
        
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
        encoding = CNF_CSV_ENCODING

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