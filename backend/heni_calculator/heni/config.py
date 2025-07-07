import os

# Constants for Dietary Risk Factors (DRF per 100 kcal in μDALYs)
DRF_TABLE = {
    "seafood": -81, "calcium": -5.1, "nuts_seeds": -1.5, "saturated_fatty_acids": 0.7,
    "polyunsaturated_fatty_acids": -0.6, "whole_grains": -0.34, "legumes": -0.23,
    "fiber": -0.19, "fruits": -0.18, "vegetables": -0.083, "milk": -0.0077,
    "sugar_sweetened_beverages": 0.066, "red_meat": 0.099, "processed_meat": 0.86,
    "trans_fatty_acids": 4.4, "sodium": 13.9
}

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use a relative path for CNF_FOLDER
CNF_FOLDER = os.path.join(BASE_DIR, "..", "raw_cnf")

# OpenAI API Key from environment variable
LLM_API_KEY = os.getenv('OPENAI_API_KEY', '')