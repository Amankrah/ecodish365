import logging
from rest_framework.decorators import api_view
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

# Initialize pipeline and validator once
cnf_pipeline = CNFDataPipeline(settings.CNF_FOLDER)
food_input_validator = FoodInputValidator(cnf_pipeline)

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
@handle_exceptions
def add_food_to_cnf(request):
    """Add a single food item to the CNF database."""
    food_data = request.data
    validated_food_data = food_input_validator.process_new_food_input(food_data)
    food_id = cnf_pipeline.add_food(validated_food_data)
    
    return Response({
        "success": True,
        "message": f"Food added successfully",
        "data": {
            "food_id": food_id,
            "food_description": validated_food_data.get('FoodDescription')
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
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
            validated_food = food_input_validator.process_new_food_input(food_data)
            validated_foods.append(validated_food)
        except ValidationError as e:
            return Response({
                "error": f"Validation error in food #{i+1}",
                "details": str(e),
                "food_description": food_data.get('FoodDescription', 'Unknown')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Add all foods in batch
    food_ids = cnf_pipeline.add_foods_batch(validated_foods)
    
    return Response({
        "success": True,
        "message": f"Successfully added {len(food_ids)} foods",
        "data": {
            "food_ids": food_ids,
            "count": len(food_ids)
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'DELETE'])
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
        food_details = cnf_pipeline.get_food_details(food_id)
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
        validated_food_data = food_input_validator.process_new_food_input(updated_food_data)
        updated_food = cnf_pipeline.update_food(food_id, validated_food_data)
        
        return Response({
            "success": True,
            "message": "Food updated successfully",
            "data": updated_food
        })

    elif request.method == 'DELETE':
        success = cnf_pipeline.delete_food(food_id)
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
@handle_exceptions
def search_cnf_foods(request):
    """Advanced food search with pagination and relevance scoring."""
    query = request.GET.get('q', '').strip()
    limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 results
    offset = int(request.GET.get('offset', 0))
    
    if not query:
        return Response({
            "error": "Missing search query",
            "details": "Please provide a search query using the 'q' parameter"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    results = cnf_pipeline.search_foods(query, limit, offset)
    
    return Response({
        "success": True,
        "data": results
    })

@api_view(['GET'])
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
    
    foods = cnf_pipeline.search_foods_by_nutrient(nutrient_id, min_value, max_value, limit)
    
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

@api_view(['GET'])
@handle_exceptions
def get_foods_by_group(request, food_group_id):
    """Get all foods in a specific food group."""
    try:
        food_group_id = int(food_group_id)
    except ValueError:
        return Response({
            "error": "Invalid food group ID",
            "details": "Food group ID must be a valid integer"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    limit = min(int(request.GET.get('limit', 100)), 500)
    foods = cnf_pipeline.get_foods_by_group(food_group_id, limit)
    
    return Response({
        "success": True,
        "data": {
            "foods": foods,
            "food_group_id": food_group_id,
            "count": len(foods),
            "limit": limit
        }
    })

@api_view(['POST'])
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
    
    comparison_data = cnf_pipeline.compare_foods(food_ids, nutrient_ids)
    
    return Response({
        "success": True,
        "data": comparison_data
    })

# =============================================================================
# Reference Data Endpoints
# =============================================================================

@api_view(['GET'])
@handle_exceptions
def get_food_groups_view(request):
    """Get all available food groups."""
    food_groups = get_food_groups(cnf_pipeline.data_loader.food_group_df)
    return Response({
        "success": True,
        "data": food_groups,
        "count": len(food_groups)
    })

@api_view(['GET'])
@handle_exceptions
def get_food_sources_view(request):
    """Get all available food sources."""
    food_sources = get_food_sources(cnf_pipeline.data_loader.food_source_df)
    return Response({
        "success": True,
        "data": food_sources,
        "count": len(food_sources)
    })

@api_view(['GET'])
@handle_exceptions
def get_nutrient_sources_view(request):
    """Get all available nutrient sources."""
    nutrient_sources = get_nutrient_sources(cnf_pipeline.data_loader.nutrient_source_df)
    return Response({
        "success": True,
        "data": nutrient_sources,
        "count": len(nutrient_sources)
    })

@api_view(['GET'])
@handle_exceptions
def get_nutrients_view(request):
    """Get all available nutrients."""
    nutrients = get_nutrient_info(cnf_pipeline.data_loader.nutrient_name_df)
    return Response({
        "success": True,
        "data": nutrients,
        "count": len(nutrients)
    })

@api_view(['GET'])
@handle_exceptions
def get_measures_view(request):
    """Get all available measures."""
    measures = get_conversion_factors(cnf_pipeline.data_loader.measure_name_df)
    return Response({
        "success": True,
        "data": measures,
        "count": len(measures)
    })

# =============================================================================
# Reference Data Management Endpoints
# =============================================================================

@api_view(['POST'])
@handle_exceptions
def add_food_source(request):
    """Add a new food source."""
    description = request.data.get('description')
    if not description:
        return Response({
            "error": "Missing description",
            "details": "Food source description is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_source = cnf_pipeline.add_food_source(description)
    return Response({
        "success": True,
        "message": "Food source added successfully",
        "data": new_source
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@handle_exceptions
def add_nutrient_source(request):
    """Add a new nutrient source."""
    description = request.data.get('description')
    if not description:
        return Response({
            "error": "Missing description",
            "details": "Nutrient source description is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_source = cnf_pipeline.add_nutrient_source(description)
    return Response({
        "success": True,
        "message": "Nutrient source added successfully",
        "data": new_source
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@handle_exceptions
def add_new_measure(request):
    """Add a new measure."""
    description = request.data.get('description')
    if not description:
        return Response({
            "error": "Missing description",
            "details": "Measure description is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    new_measure = cnf_pipeline.add_measure(description)
    return Response({
        "success": True,
        "message": "Measure added successfully",
        "data": new_measure
    }, status=status.HTTP_201_CREATED)

# =============================================================================
# Data Quality and Analytics Endpoints
# =============================================================================

@api_view(['GET'])
@handle_exceptions
def check_data_integrity(request):
    """Perform comprehensive data integrity check."""
    integrity_results = cnf_pipeline.check_data_integrity()
    
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
@handle_exceptions
def get_database_statistics(request):
    """Get comprehensive database statistics."""
    stats = cnf_pipeline.get_database_statistics()
    return Response({
        "success": True,
        "data": stats
    })

# =============================================================================
# Bulk Export Endpoints
# =============================================================================

@api_view(['POST'])
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
        food_details = cnf_pipeline.get_food_details(food_id)
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
                "export_date": cnf_pipeline.get_database_statistics()['timestamp']
            }
        }
    })

# =============================================================================
# Deprecated endpoints (for backward compatibility)
# =============================================================================

@api_view(['GET', 'PUT'])
@handle_exceptions
def get_cnf_food(request, food_id):
    """
    DEPRECATED: Use manage_cnf_food instead.
    Maintained for backward compatibility.
    """
    return manage_cnf_food(request, food_id)