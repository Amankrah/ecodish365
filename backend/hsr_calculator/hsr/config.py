import os

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CNF data file paths
CNF_FOLDER = os.path.join(BASE_DIR, '..', 'raw_cnf')
FOOD_NAME_PATH = os.path.join(CNF_FOLDER, 'FOOD_NAME.csv')
NUTRIENT_NAME_PATH = os.path.join(CNF_FOLDER, 'NUTRIENT_NAME.csv')
NUTRIENT_AMOUNT_PATH = os.path.join(CNF_FOLDER, 'NUTRIENT_AMOUNT.csv')
FOOD_GROUP_PATH = os.path.join(CNF_FOLDER, 'FOOD_GROUP.csv')