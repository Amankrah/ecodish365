from typing import List
from heni_calculator.heni.calculator.heni_calculator import HENICalculator
from heni_calculator.heni.models.ingredient import Ingredient

class HENIWrapper:
    def __init__(self, heni_calculator: HENICalculator):
        self.calculator = heni_calculator

    def calculate_heni(self, ingredients: List[Ingredient]) -> float:
        heni_score, _ = self.calculator.calculate_heni(ingredients)
        return heni_score  # This is in μDALYs per 100 kcal