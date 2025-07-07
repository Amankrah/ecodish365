import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from heni_calculator import CNFDatabase, Ingredient, HENICalculator, LLM_API_KEY, CNF_FOLDER
from api.seo_utils import seo_metadata

logger = logging.getLogger(__name__)

@api_view(['POST'])
@seo_metadata(
    title="Health and Nutritional Impact (HENI) Calculator | DISH Research",
    description="Calculate the Health and Nutritional Impact (HENI) score for your meals. Analyze the health benefits of your food choices.",
    keywords="HENI, health impact, nutritional impact, meal analysis, healthy eating"
)
def heni_calculate(request):
    try:
        cnf_db = CNFDatabase(CNF_FOLDER)
        heni_calculator = HENICalculator(cnf_db, LLM_API_KEY)

        meal_data = request.data.get('meal', [])

        meal = [Ingredient(food_id=item['food_id'], amount=item['amount'], unit=item['unit'], cnf_db=cnf_db) for item in meal_data]
        
        heni_score, total_kcal, total_heni, ingredient_categories = heni_calculator.calculate_heni(meal)
        
        result = {
            "data": {
                "heni_score": heni_score,
                "total_kcal": total_kcal,
                "total_heni": total_heni,
                "ingredient_categories": ingredient_categories
            },
            "seo_metadata": {
                "title": "Health and Nutritional Impact (HENI) Calculator | DISH Research",
                "description": "Calculate the Health and Nutritional Impact (HENI) score for your meals. Analyze the health benefits of your food choices.",
                "keywords": "HENI, health impact, nutritional impact, meal analysis, healthy eating"
            }
        }
        
        return Response(result)
    
    except Exception as e:
        logger.exception(f"An error occurred in HENI calculation: {str(e)}")
        return Response({"error": str(e)}, status=500)