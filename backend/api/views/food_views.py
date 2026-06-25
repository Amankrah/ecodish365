import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from api.cnf_cache import get_dish_cnf_pipeline
from api.food_id_finder import (
    load_food_data,
    get_food_categories,
    get_preparation_methods,
    extract_food_category,
    extract_preparation_method,
)

logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100

def _search_filters_payload(food_df, category_filter, method_filter, source: str):
    """Category/method facets for the explorer UI (still CNF heuristic–based)."""
    applied = {"category": category_filter, "method": method_filter}
    if source and source != 'both':
        applied["source"] = source
    if food_df is None:
        return {
            "available_categories": [],
            "available_methods": [],
            "applied_filters": applied,
        }
    return {
        "available_categories": get_food_categories(food_df),
        "available_methods": get_preparation_methods(food_df),
        "applied_filters": applied,
    }


@api_view(['GET'])
def search_food_api(request):
    """Enhanced substring search (`/api/search-food/`).

    WAFCT-EXTEND fix (2026-05-25): Previously this endpoint used fuzzy search on
    `raw_cnf/FOOD_NAME.csv` only, ignored `source`, and leaked CNF rows when users
    picked WAFCT. It now uses the same merged in-memory corpus as `/api/cnf/search/`
    (CNF + WAFCT append) via `get_dish_cnf_pipeline().search_foods(..., source=)`.
    """
    query = request.GET.get('query', '').strip()
    category_filter = request.GET.get('category', '').strip().lower() or None
    method_filter = request.GET.get('method', '').strip().lower() or None
    source = request.GET.get('source', 'both').strip().lower()
    if source not in ('cnf', 'wafct', 'fdc', 'both'):
        source = 'both'

    if not query:
        return Response({"error": "Query parameter is required"}, status=400)

    if len(query) < 2:
        return Response({"error": "Query must be at least 2 characters long"}, status=400)

    limit = min(int(request.GET.get('limit', 50)), 100)
    offset = int(request.GET.get('offset', 0))

    food_df = cache.get('food_df')
    if food_df is None:
        food_df = load_food_data()
        if food_df is not None:
            cache.set('food_df', food_df, timeout=3600)
        else:
            logger.warning('FOOD_NAME cache miss; filter dropdowns empty (search still OK)')

    pipe_source = source if source in ('cnf', 'wafct', 'fdc') else 'both'

    try:
        pipeline = get_dish_cnf_pipeline()

        # Category/method are heuristic facets from `food_id_finder`: fetch a wider
        # slice before post-filter so matches are not arbitrarily truncated by offset.
        if category_filter or method_filter:
            wide = min(500, max(limit + offset + 50, 120))
            raw = pipeline.search_foods(query, wide, 0, source=pipe_source)
            items = list(raw.get('results') or [])
            if category_filter:
                items = [
                    r for r in items
                    if extract_food_category(r['FoodDescription']).lower()
                    == category_filter
                ]
            if method_filter:
                items = [
                    r for r in items
                    if extract_preparation_method(r['FoodDescription']).lower()
                    == method_filter
                ]
            total = len(items)
            paginated_results = items[offset:offset + limit]
            has_more = offset + limit < total
        else:
            raw = pipeline.search_foods(query, limit, offset, source=pipe_source)
            paginated_results = list(raw.get('results') or [])
            total = int(raw.get('total', len(paginated_results)))
            has_more = bool(raw.get('has_more', False))

        response_data = {
            "results": paginated_results,
            "total": total,
            "query": query,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "filters": _search_filters_payload(food_df, category_filter, method_filter, source),
        }
        if source != 'both':
            response_data['source_filter'] = source

        return Response(response_data)

    except Exception as e:
        logger.exception("Error searching food: %s", e)
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
