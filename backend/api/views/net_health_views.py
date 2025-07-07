import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from heni_calculator import CNFDatabase, Ingredient, HENICalculator, LLM_API_KEY, CNF_FOLDER
from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
from environmental_impact_model.src.food import Food as EnvFood
from environmental_impact_model.src.meal import Meal as EnvMeal
from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment
from environmental_impact_model.src.monetization import Monetization
from net_health_impact_calculator.src.net_health_impact import NetHealthImpactCalculator
from api.seo_utils import seo_metadata

logger = logging.getLogger(__name__)

@api_view(['POST'])
@seo_metadata(
    title="Net Health Impact Calculator | DISH Research",
    description="Calculate the combined health and environmental impact of your meals. Get a holistic view of your food choices' effects on personal and planetary health.",
    keywords="net health impact, environmental impact, health impact, sustainable eating, holistic food analysis"
)
def calculate_net_health_impact(request):
    try:
        cnf_db = CNFDatabase(CNF_FOLDER)
        heni_calculator = HENICalculator(cnf_db, LLM_API_KEY)
        env_data_loader = EnvDataLoader()

        meal_data = request.data.get('meal', [])

        heni_ingredients = [Ingredient(food_id=item['food_id'], amount=item['amount'], unit=item['unit'], cnf_db=cnf_db) for item in meal_data]
        env_foods = [EnvFood(food_id=item['food_id'], quantity=item['amount'], data_loader=env_data_loader) for item in meal_data]
        env_meal = EnvMeal(env_foods)

        net_calculator = NetHealthImpactCalculator(heni_calculator, LifeCycleAssessment, Monetization)
        result = net_calculator.calculate_net_impact(heni_ingredients, env_meal)

        return Response(result)

    except Exception as e:
        logger.exception(f"An error occurred in net health impact calculation: {str(e)}")
        return Response({"error": str(e)}, status=500)