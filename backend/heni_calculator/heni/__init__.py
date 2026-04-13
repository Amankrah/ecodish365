from .calculator.heni_calculator import HENICalculator
from .config.heni_factors import HENI_FACTORS, HENI_RISK_FACTOR_KEYS
from .database.cnf_integrator import HENICNFIntegrator, create_heni_cnf_integrator
from .models.ingredient import Ingredient
from .service import (
    calculate_meal_heni_response,
    get_cnf_integrator,
    ingredients_from_meal_food_items,
    meal_api_rows_to_ingredients,
    resolve_llm_api_key,
)
import os

CNFDatabase = HENICNFIntegrator
LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")
CNF_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "raw_cnf")
