import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
from environmental_impact_model.src.food import Food as EnvFood
from environmental_impact_model.src.meal import Meal as EnvMeal
from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment
from environmental_impact_model.src.monetization import Monetization
from environmental_impact_model.src.reference_meals import ReferenceMeals
from api.seo_utils import seo_metadata

logger = logging.getLogger(__name__)

@api_view(['POST'])
@seo_metadata(
    title="Environmental Impact Calculator | DISH Research",
    description="Calculate the environmental impact of your meals with our advanced LCA tool. Compare your meal's impact to reference meals and get monetized results.",
    keywords="environmental impact, LCA, food sustainability, carbon footprint, meal comparison"
)
def environmental_impact(request):
    try:
        food_data = request.data.get('foods', [])
        
        data_loader = EnvDataLoader()
        foods = [EnvFood(food_id=item['food_id'], quantity=item['quantity'], data_loader=data_loader) for item in food_data]
        meal = EnvMeal(foods)
        
        lca = LifeCycleAssessment(meal)
        lca_results = lca.perform_lcia()
        endpoint_impacts = lca.calculate_endpoint_impacts()
        
        monetization = Monetization(lca_results, data_loader)
        monetized_impacts = monetization.monetize_impacts()
        total_monetized_impact = monetization.get_total_monetized_impact()
        
        reference_meals = ReferenceMeals(data_loader)
        sustainable_lunch = reference_meals.create_sustainable_meal('lunch')
        unsustainable_lunch = reference_meals.create_unsustainable_meal('lunch')
        ultra_processed_lunch = reference_meals.create_ultra_processed_meal('lunch')
        
        meal_impact = sum(meal.calculate_environmental_impact().values())
        sustainable_impact = sum(sustainable_lunch.calculate_environmental_impact().values())
        unsustainable_impact = sum(unsustainable_lunch.calculate_environmental_impact().values())
        ultra_processed_impact = sum(ultra_processed_lunch.calculate_environmental_impact().values())
        
        comparisons = {
            "sustainable_lunch": meal_impact / sustainable_impact,
            "unsustainable_lunch": meal_impact / unsustainable_impact,
            "ultra_processed_lunch": meal_impact / ultra_processed_impact
        }
        
        result = {
            "data": {
                "meal_composition": str(meal),
                "midpoint_impacts": lca_results,
                "endpoint_impacts": endpoint_impacts,
                "monetized_impacts": monetized_impacts,
                "total_monetized_impact": total_monetized_impact,
                "meal_comparisons": comparisons
            },
            "seo_metadata": {
                "title": "Environmental Impact Calculator | DISH Research",
                "description": "Calculate the environmental impact of your meals with our advanced LCA tool. Compare your meal's impact to reference meals and get monetized results.",
                "keywords": "environmental impact, LCA, food sustainability, carbon footprint, meal comparison"
            }
        }
        
        return Response(result)
    
    except Exception as e:
        logger.error(f"Error in environmental impact calculation: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred during the environmental impact calculation."}, status=500)