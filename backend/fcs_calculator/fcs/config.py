import os

# Constants for FCS calculation
MIN_FCS = 1
MAX_FCS = 100

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CNF data file paths
CNF_NUTRIENT_NAME_PATH = os.path.join(BASE_DIR, '..', 'raw_cnf', 'NUTRIENT_NAME.csv')
CNF_NUTRIENT_AMOUNT_PATH = os.path.join(BASE_DIR, '..', 'raw_cnf', 'NUTRIENT_AMOUNT.csv')