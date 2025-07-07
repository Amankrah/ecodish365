from environmental_impact_model.src.meal import Meal
from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment

class LCAWrapper:
    def __init__(self):
        pass

    def calculate_lca(self, meal: Meal) -> float:
        lca = LifeCycleAssessment(meal)
        endpoint_impacts = lca.calculate_endpoint_impacts()
        return endpoint_impacts['Human Health']  # This is in DALYs