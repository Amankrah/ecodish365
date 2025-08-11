from .database.cnf_integrator import HENICNFIntegrator, create_heni_cnf_integrator
from .models.ingredient import Ingredient
from .calculator.heni_calculator import HENICalculator
from .config.heni_factors import HENI_FACTORS
import os

# For backward compatibility
CNFDatabase = HENICNFIntegrator  # Alias for legacy code
LLM_API_KEY = os.getenv('OPENAI_API_KEY', '')
CNF_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'raw_cnf')