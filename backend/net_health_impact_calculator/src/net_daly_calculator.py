from .heni_wrapper import HENIWrapper
from .lca_wrapper import LCAWrapper
from typing import List
from heni_calculator.heni.models.ingredient import Ingredient
from environmental_impact_model.src.meal import Meal

class NetDALYCalculator:
    def __init__(self, heni_wrapper: HENIWrapper, lca_wrapper: LCAWrapper):
        self.heni_wrapper = heni_wrapper
        self.lca_wrapper = lca_wrapper

    def calculate_net_daly(self, ingredients: List[Ingredient], meal: Meal) -> float:
        heni_score = self.heni_wrapper.calculate_heni(ingredients)
        lca_impact = self.lca_wrapper.calculate_lca(meal)
        
        # Convert HENI score from μDALYs to DALYs
        heni_dalys = heni_score / 1_000_000
        
        # Calculate net DALYs
        net_dalys = heni_dalys - lca_impact
        
        return net_dalys