import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from fcs_calculator import FoodItem, CNFIntegrator, FoodAnalyzer
from api.seo_utils import seo_metadata

logger = logging.getLogger(__name__)

class InvalidScoreError(ValueError):
    pass

@api_view(['POST'])
@seo_metadata(
    title="Food Compass Score Calculator | DISH Research",
    description="Calculate the Food Compass Score (FCS) for your food items. Analyze nutritional content and get detailed FCS results.",
    keywords="FCS, food compass score, nutritional analysis, food science, DISH Research"
)
def fcs_calculate(request):
    try:
        food_ids = request.data.get('food_ids', [])
        food_names = request.data.get('food_names', [])
        
        if not food_ids:
            return Response({"error": "No food IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the first food name if provided, otherwise use "Example Food"
        food_name = food_names[0] if food_names else "Example Food"
        food_item = FoodItem(food_name)
        
        try:
            CNFIntegrator.extract_nutrients_from_cnf(food_ids, food_item)
        except KeyError as ke:
            logger.error(f"Data inconsistency in extract_nutrients_from_cnf: {str(ke)}")
            return Response({"error": "An error occurred while processing food data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in extract_nutrients_from_cnf: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred while processing food data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        analyzer = FoodAnalyzer()
        try:
            result = analyzer.analyze_food_item(food_item)
        except InvalidScoreError as ise:
            logger.error(f"Invalid score error in analyze_food_item: {str(ise)}")
            return Response({"error": "An error occurred while analyzing the food item"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "data": result,
            "seo_metadata": {
                "title": "Food Composition Score Calculator | DISH Research",
                "description": "Calculate the Food Composition Score (FCS) for your food items. Analyze nutritional content and get detailed FCS results.",
                "keywords": "FCS, food composition score, nutritional analysis, food science, DISH Research"
            }
        })
    
    except Exception as e:
        logger.error(f"Unexpected error in FCS calculation: {str(e)}", exc_info=True)
        return Response({"error": "An unexpected error occurred during FCS calculation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)