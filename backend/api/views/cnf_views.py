import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.core.paginator import Paginator
from dish_cnf_db_pipeline.cnf_pipeline import CNFDataPipeline
from dish_cnf_db_pipeline.user_input import (
    get_food_groups, get_nutrient_info, 
    get_conversion_factors, get_food_sources, get_nutrient_sources, 
    FoodInputValidator
)

logger = logging.getLogger(__name__)

# Single process-wide CNF pipeline — see backend/api/cnf_cache.py.
from api.cnf_cache import get_dish_cnf_pipeline as get_cnf_pipeline

_food_input_validator = None

def get_food_input_validator():
    global _food_input_validator
    if _food_input_validator is None:
        _food_input_validator = FoodInputValidator(get_cnf_pipeline())
    return _food_input_validator

def handle_exceptions(view_func):
    """Decorator for consistent error handling across views."""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {view_func.__name__}: {str(e)}")
            return Response({
                "error": "Validation failed",
                "details": e.messages if hasattr(e, 'messages') else [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.warning(f"Value error in {view_func.__name__}: {str(e)}")
            return Response({
                "error": "Invalid data",
                "details": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {str(e)}", exc_info=True)
            return Response({
                "error": "An unexpected error occurred",
                "details": "Please try again later or contact support"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper

# =============================================================================
# Food Management Endpoints
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def add_food_to_cnf(request):
    """Add a single food item to the CNF database."""
    food_data = request.data
    validated_food_data = get_food_input_validator().process_new_food_input(food_data)
    food_id = get_cnf_pipeline().add_food(validated_food_data)
    
    return Response({
        "success": True,
        "message": f"Food added successfully",
        "data": {
            "food_id": food_id,
            "food_description": validated_food_data.get('FoodDescription')
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def add_foods_batch(request):
    """Add multiple foods in a batch operation."""
    foods_data = request.data
    
    if not isinstance(foods_data, list):
        return Response({
            "error": "Invalid data format",
            "details": "Expected a list of food objects"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(foods_data) > 100:
        return Response({
            "error": "Batch size too large",
            "details": "Maximum 100 foods can be added in a single batch"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate all foods first
    validated_foods = []
    for i, food_data in enumerate(foods_data):
        try:
            validated_food = get_food_input_validator().process_new_food_input(food_data)
            validated_foods.append(validated_food)
        except ValidationError as e:
            return Response({
                "error": f"Validation error in food #{i+1}",
                "details": str(e),
                "food_description": food_data.get('FoodDescription', 'Unknown')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Add all foods in batch
    food_ids = get_cnf_pipeline().add_foods_batch(validated_foods)
    
    return Response({
        "success": True,
        "message": f"Successfully added {len(food_ids)} foods",
        "data": {
            "food_ids": food_ids,
            "count": len(food_ids)
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
@handle_exceptions
def manage_cnf_food(request, food_id):
    """Get, update, or delete a specific food item."""
    try:
        food_id = int(food_id)
    except ValueError:
        return Response({
            "error": "Invalid food ID",
            "details": "Food ID must be a valid integer"
        }, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        food_details = get_cnf_pipeline().get_food_details(food_id)
        if food_details is None:
            return Response({
                "error": "Food not found",
                "details": f"No food found with ID {food_id}"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "success": True,
            "data": food_details
        })

    elif request.method == 'PUT':
        updated_food_data = request.data
        validated_food_data = get_food_input_validator().process_new_food_input(updated_food_data)
        updated_food = get_cnf_pipeline().update_food(food_id, validated_food_data)
        
        return Response({
            "success": True,
            "message": "Food updated successfully",
            "data": updated_food
        })

    elif request.method == 'DELETE':
        success = get_cnf_pipeline().delete_food(food_id)
        if success:
            return Response({
                "success": True,
                "message": f"Food {food_id} deleted successfully"
            })
        else:
            return Response({
                "error": "Deletion failed",
                "details": f"Could not delete food with ID {food_id}"
            }, status=status.HTTP_400_BAD_REQUEST)

# =============================================================================
# Search and Exploration Endpoints
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def search_cnf_foods(request):
    """Advanced food search with pagination and relevance scoring.

    WAFCT-EXTEND (2026-05-24): optional `source` query param filters the
    response to one food database:
      ?source=cnf   — Health Canada CNF only
      ?source=wafct — FAO/INFOODS WAFCT 2019 only
      ?source=both  — both (default)
    """
    query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 results
    offset = int(request.GET.get('offset', 0))
    source = request.GET.get('source', 'both').lower()
    if source not in ('cnf', 'wafct', 'both'):
        source = 'both'

    if not query:
        return Response({
            "error": "Missing search query",
            "details": "Please provide a search query using the 'q' parameter"
        }, status=status.HTTP_400_BAD_REQUEST)

    results = get_cnf_pipeline().search_foods(
        query,
        limit,
        offset,
        source if source in ('cnf', 'wafct') else 'both',
    )

    return Response({
        "success": True,
        "data": results
    })

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def search_foods_by_nutrient(request):
    """Search foods by nutrient content."""
    nutrient_id = request.GET.get('nutrient_id')
    min_value = request.GET.get('min_value')
    max_value = request.GET.get('max_value')
    limit = min(int(request.GET.get('limit', 50)), 100)
    
    if not nutrient_id:
        return Response({
            "error": "Missing nutrient ID",
            "details": "Please provide a nutrient_id parameter"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        nutrient_id = int(nutrient_id)
        min_value = float(min_value) if min_value else None
        max_value = float(max_value) if max_value else None
    except ValueError:
        return Response({
            "error": "Invalid parameter values",
            "details": "nutrient_id must be an integer, min_value and max_value must be numbers"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    foods = get_cnf_pipeline().search_foods_by_nutrient(nutrient_id, min_value, max_value, limit)
    
    return Response({
        "success": True,
        "data": {
            "foods": foods,
            "search_criteria": {
                "nutrient_id": nutrient_id,
                "min_value": min_value,
                "max_value": max_value,
                "limit": limit
            }
        }
    })

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def discover_foods(request):
    """Multi-criteria nutrient discovery for the research workbench.

    Body (JSON):
      criteria: [{nutrient_id, min?, max?}, ...]  (AND; thresholds in the chosen basis)
      basis: 'per_100g' | 'per_100kcal'
      food_group_id: int (optional scope)
      source: 'cnf' | 'wafct' (optional; default both)
      ratio: {numerator_id, denominator_id} (optional; reported + sortable)
      dv_threshold: {nutrient_id, min_pct?, max_pct?} (optional; %DV on per-100 g amount)
      sort: {key, direction}   key = NutrientID | 'ratio' | 'energy'; direction 'asc'|'desc'
      limit: int (<= 200)
    """
    body = request.data or {}

    raw_criteria = body.get('criteria', [])
    if not isinstance(raw_criteria, list):
        return Response({"error": "criteria must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    criteria = []
    for c in raw_criteria:
        try:
            item = {'nutrient_id': int(c['nutrient_id'])}
        except (KeyError, TypeError, ValueError):
            return Response({"error": "each criterion needs an integer nutrient_id"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            for k in ('min', 'max'):
                if c.get(k) is not None:
                    item[k] = float(c[k])
        except (TypeError, ValueError):
            return Response({"error": "criterion min/max must be numbers"},
                            status=status.HTTP_400_BAD_REQUEST)
        criteria.append(item)

    basis = body.get('basis', 'per_100g')
    if basis not in ('per_100g', 'per_100kcal'):
        basis = 'per_100g'

    food_group_id = body.get('food_group_id')
    try:
        food_group_id = int(food_group_id) if food_group_id not in (None, '') else None
    except (TypeError, ValueError):
        food_group_id = None

    source = body.get('source')
    if source not in ('cnf', 'wafct'):
        source = None

    ratio = body.get('ratio')
    if ratio:
        try:
            ratio = {'numerator_id': int(ratio['numerator_id']),
                     'denominator_id': int(ratio['denominator_id'])}
        except (KeyError, TypeError, ValueError):
            return Response({"error": "ratio needs integer numerator_id and denominator_id"},
                            status=status.HTTP_400_BAD_REQUEST)

    dv_threshold = body.get('dv_threshold')
    if dv_threshold:
        try:
            dvt = {'nutrient_id': int(dv_threshold['nutrient_id'])}
            for k in ('min_pct', 'max_pct'):
                if dv_threshold.get(k) is not None:
                    dvt[k] = float(dv_threshold[k])
            dv_threshold = dvt
        except (KeyError, TypeError, ValueError):
            return Response({"error": "dv_threshold needs an integer nutrient_id and numeric pct"},
                            status=status.HTTP_400_BAD_REQUEST)

    sort = body.get('sort') if isinstance(body.get('sort'), dict) else None

    try:
        limit = int(body.get('limit', 100))
    except (TypeError, ValueError):
        limit = 100

    if not criteria and not ratio and not dv_threshold:
        return Response(
            {"error": "Provide at least one criterion, a ratio, or a %DV threshold"},
            status=status.HTTP_400_BAD_REQUEST)

    result = get_cnf_pipeline().discover_foods(
        criteria=criteria, basis=basis, food_group_id=food_group_id, source=source,
        ratio=ratio, dv_threshold=dv_threshold, sort=sort, limit=limit)
    return Response({"success": True, "data": result})


@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_foods_by_group(request, food_group_id):
    """Get foods in a food group with optional filters, sort, and pagination."""
    try:
        food_group_id = int(food_group_id)
    except ValueError:
        return Response({
            "error": "Invalid food group ID",
            "details": "Food group ID must be a valid integer"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        limit = min(int(request.GET.get('limit', 100)), 500)
        offset = max(0, int(request.GET.get('offset', 0)))
    except (TypeError, ValueError):
        return Response({
            "error": "Invalid pagination",
            "details": "limit and offset must be integers"
        }, status=status.HTTP_400_BAD_REQUEST)

    q = (request.GET.get('q') or '').strip() or None
    sort = (request.GET.get('sort') or 'name').strip().lower()
    sort_dir = (request.GET.get('sort_dir') or 'asc').strip().lower()
    food_type = (request.GET.get('food_type') or '').strip().lower() or None
    thermal = (request.GET.get('thermal') or '').strip().lower() or None
    preservation = (request.GET.get('preservation') or '').strip().lower() or None
    source = (request.GET.get('source') or '').strip().lower() or None
    if source == 'both':
        source = None
    include_summary = request.GET.get('summary', '').lower() in ('1', 'true', 'yes')

    if food_type not in (None, 'single', 'mixed'):
        food_type = None
    if source not in (None, 'cnf', 'wafct'):
        source = None
    if sort not in ('name', 'kcal', 'food_id'):
        sort = 'name'

    result = get_cnf_pipeline().get_foods_by_group(
        food_group_id,
        limit=limit,
        offset=offset,
        q=q,
        sort=sort,
        sort_dir=sort_dir,
        food_type=food_type,
        thermal=thermal,
        preservation=preservation,
        source=source,
        include_summary=include_summary,
    )

    return Response({"success": True, "data": result})

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def compare_foods(request):
    """Compare nutritional content of multiple foods."""
    food_ids = request.data.get('food_ids', [])
    nutrient_ids = request.data.get('nutrient_ids', [])
    
    if not food_ids or not isinstance(food_ids, list):
        return Response({
            "error": "Invalid food IDs",
            "details": "Please provide a list of food_ids to compare"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(food_ids) < 2:
        return Response({
            "error": "Insufficient foods",
            "details": "At least 2 foods are required for comparison"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        food_ids = [int(fid) for fid in food_ids]
        nutrient_ids = [int(nid) for nid in nutrient_ids] if nutrient_ids else None
    except ValueError:
        return Response({
            "error": "Invalid ID format",
            "details": "All IDs must be valid integers"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    comparison_data = get_cnf_pipeline().compare_foods(food_ids, nutrient_ids)
    
    return Response({
        "success": True,
        "data": comparison_data
    })

# =============================================================================
# Reference Data Endpoints
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_food_groups_view(request):
    """Get all available food groups."""
    food_groups = get_food_groups(get_cnf_pipeline().data_loader.food_group_df)
    return Response({
        "success": True,
        "data": food_groups,
        "count": len(food_groups)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_food_sources_view(request):
    """Get all available food sources."""
    food_sources = get_food_sources(get_cnf_pipeline().data_loader.food_source_df)
    return Response({
        "success": True,
        "data": food_sources,
        "count": len(food_sources)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_nutrient_sources_view(request):
    """Get all available nutrient sources."""
    nutrient_sources = get_nutrient_sources(get_cnf_pipeline().data_loader.nutrient_source_df)
    return Response({
        "success": True,
        "data": nutrient_sources,
        "count": len(nutrient_sources)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_nutrients_view(request):
    """Get all available nutrients."""
    nutrients = get_nutrient_info(get_cnf_pipeline().data_loader.nutrient_name_df)
    return Response({
        "success": True,
        "data": nutrients,
        "count": len(nutrients)
    })

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_measures_view(request):
    """Get all available measures."""
    measures = get_conversion_factors(get_cnf_pipeline().data_loader.measure_name_df)
    return Response({
        "success": True,
        "data": measures,
        "count": len(measures)
    })

# =============================================================================
# Reference Data Management Endpoints
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def add_food_source(request):
    """Add a new food source."""
    description = request.data.get('description')
    if not description:
        return Response({
            "error": "Missing description",
            "details": "Food source description is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_source = get_cnf_pipeline().add_food_source(description)
    return Response({
        "success": True,
        "message": "Food source added successfully",
        "data": new_source
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def add_nutrient_source(request):
    """Add a new nutrient source."""
    description = request.data.get('description')
    if not description:
        return Response({
            "error": "Missing description",
            "details": "Nutrient source description is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_source = get_cnf_pipeline().add_nutrient_source(description)
    return Response({
        "success": True,
        "message": "Nutrient source added successfully",
        "data": new_source
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def add_new_measure(request):
    """Add a new measure."""
    description = request.data.get('description')
    if not description:
        return Response({
            "error": "Missing description",
            "details": "Measure description is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_measure = get_cnf_pipeline().add_measure(description)
    return Response({
        "success": True,
        "message": "Measure added successfully",
        "data": new_measure
    }, status=status.HTTP_201_CREATED)

# =============================================================================
# Data Quality and Analytics Endpoints
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def check_data_integrity(request):
    """Perform comprehensive data integrity check."""
    integrity_results = get_cnf_pipeline().check_data_integrity()
    
    if integrity_results['overall_status'] == 'passed':
        return Response({
            "success": True,
            "message": "Data integrity check passed",
            "data": integrity_results
        })
    else:
        return Response({
            "success": False,
            "message": f"Data integrity check {integrity_results['overall_status']}",
            "data": integrity_results
        }, status=status.HTTP_200_OK)  # Still 200 as it's not an error in the request

@api_view(['GET'])
@permission_classes([AllowAny])
@handle_exceptions
def get_database_statistics(request):
    """Get comprehensive database statistics."""
    stats = get_cnf_pipeline().get_database_statistics()
    return Response({
        "success": True,
        "data": stats
    })

# =============================================================================
# Bulk Export Endpoints
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exceptions
def export_foods_data(request):
    """Export food data in various formats."""
    food_ids = request.data.get('food_ids', [])
    export_format = request.data.get('format', 'json').lower()
    include_nutrients = request.data.get('include_nutrients', True)
    include_conversions = request.data.get('include_conversions', True)
    
    if not food_ids or not isinstance(food_ids, list):
        return Response({
            "error": "Invalid food IDs",
            "details": "Please provide a list of food_ids to export"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(food_ids) > 1000:
        return Response({
            "error": "Export size too large",
            "details": "Maximum 1000 foods can be exported at once"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if export_format not in ['json', 'csv']:
        return Response({
            "error": "Invalid export format",
            "details": "Supported formats: json, csv"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        food_ids = [int(fid) for fid in food_ids]
    except ValueError:
        return Response({
            "error": "Invalid food ID format",
            "details": "All food IDs must be valid integers"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Collect food data
    exported_foods = []
    for food_id in food_ids:
        food_details = get_cnf_pipeline().get_food_details(food_id)
        if food_details:
            # Optionally exclude large datasets
            if not include_nutrients:
                food_details.pop('NutrientValues', None)
            if not include_conversions:
                food_details.pop('ConversionFactors', None)
            exported_foods.append(food_details)
    
    return Response({
        "success": True,
        "data": {
            "foods": exported_foods,
            "export_info": {
                "total_requested": len(food_ids),
                "total_exported": len(exported_foods),
                "format": export_format,
                "include_nutrients": include_nutrients,
                "include_conversions": include_conversions,
                "export_date": get_cnf_pipeline().get_database_statistics()['timestamp']
            }
        }
    })

# =============================================================================
# Deprecated endpoints (for backward compatibility)
# =============================================================================

@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
@handle_exceptions
def get_cnf_food(request, food_id):
    """
    DEPRECATED: Use manage_cnf_food instead.
    Maintained for backward compatibility.
    """
    return manage_cnf_food(request, food_id)