import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from api.food_id_finder import load_food_data, search_food

logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100

@api_view(['GET'])
def search_food_api(request):
    query = request.GET.get('query', '').strip()
    
    if not query:
        return Response({"error": "Query parameter is required"}, status=400)
    
    if len(query) < 2:
        return Response({"error": "Query must be at least 2 characters long"}, status=400)
    
    # Try to get the food data from cache
    food_df = cache.get('food_df')
    
    # If not in cache, load it and cache it
    if food_df is None:
        food_df = load_food_data()
        if food_df is not None:
            cache.set('food_df', food_df, timeout=3600)  # Cache for 1 hour
        else:
            logger.error("Failed to load food data")
            return Response({"error": "Food data could not be loaded"}, status=500)
    
    try:
        results = search_food(query, food_df)
        
        if not results:
            return Response({"results": [], "count": 0})
        
        paginator = CustomPagination()
        paginated_results = paginator.paginate_queryset(results, request)
        
        return paginator.get_paginated_response(paginated_results)
    
    except Exception as e:
        logger.error(f"Error searching food: {str(e)}")
        return Response({"error": "An error occurred while searching for food"}, status=500)
