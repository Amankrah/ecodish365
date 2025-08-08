import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from api.food_id_finder import load_food_data, search_food, get_food_categories, get_preparation_methods

logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100

@api_view(['GET'])
def search_food_api(request):
    query = request.GET.get('query', '').strip()
    category_filter = request.GET.get('category', '').strip().lower() or None
    method_filter = request.GET.get('method', '').strip().lower() or None
    
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
        results = search_food(query, food_df, 
                            category_filter=category_filter,
                            method_filter=method_filter)
        
        if not results:
            return Response({
                "results": [], 
                "total": 0, 
                "query": query,
                "limit": 50,
                "offset": 0,
                "has_more": False,
                "filters": {
                    "available_categories": get_food_categories(food_df),
                    "available_methods": get_preparation_methods(food_df),
                    "applied_filters": {
                        "category": category_filter,
                        "method": method_filter
                    }
                }
            })
        
        # Convert search results to the expected format
        formatted_results = []
        for food_id, food_description, relevance_score in results:
            # We need to get additional info like FoodCode and FoodGroupID
            try:
                food_rows = food_df[food_df['FoodID'] == food_id]
                if not food_rows.empty:
                    food_row = food_rows.iloc[0]
                    formatted_results.append({
                        "FoodID": food_id,
                        "FoodCode": food_row.get('FoodCode', ''),
                        "FoodDescription": food_description,
                        "FoodDescriptionF": food_row.get('FoodDescriptionF', ''),
                        "FoodGroupID": food_row.get('FoodGroupID', 0),
                        "relevance": relevance_score
                    })
                else:
                    # Fallback if food not found in DataFrame
                    formatted_results.append({
                        "FoodID": food_id,
                        "FoodCode": '',
                        "FoodDescription": food_description,
                        "FoodDescriptionF": '',
                        "FoodGroupID": 0,
                        "relevance": relevance_score
                    })
            except Exception as e:
                logger.warning(f"Error processing food {food_id}: {e}")
                # Add basic info even if we can't get full details
                formatted_results.append({
                    "FoodID": food_id,
                    "FoodCode": '',
                    "FoodDescription": food_description,
                    "FoodDescriptionF": '',
                    "FoodGroupID": 0,
                    "relevance": relevance_score
                })
        
        # Apply pagination manually since we already have the results
        limit = min(int(request.GET.get('limit', 50)), 100)
        offset = int(request.GET.get('offset', 0))
        
        paginated_results = formatted_results[offset:offset + limit]
        has_more = len(formatted_results) > offset + limit
        
        response_data = {
            "results": paginated_results,
            "total": len(formatted_results),
            "query": query,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "filters": {
                "available_categories": get_food_categories(food_df),
                "available_methods": get_preparation_methods(food_df),
                "applied_filters": {
                    "category": category_filter,
                    "method": method_filter
                }
            }
        }
        
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error searching food: {str(e)}")
        return Response({"error": "An error occurred while searching for food"}, status=500)

@api_view(['GET'])
def get_food_filters_api(request):
    """Get available categories and preparation methods for filtering"""
    try:
        # Try to get the food data from cache
        food_df = cache.get('food_df')
        
        # If not in cache, load it and cache it
        if food_df is None:
            food_df = load_food_data()
            if food_df is not None:
                cache.set('food_df', food_df, timeout=3600)
            else:
                logger.error("Failed to load food data")
                return Response({"error": "Food data could not be loaded"}, status=500)
        
        return Response({
            "categories": get_food_categories(food_df),
            "methods": get_preparation_methods(food_df)
        })
    
    except Exception as e:
        logger.error(f"Error getting food filters: {str(e)}")
        return Response({"error": "An error occurred while getting filters"}, status=500)
