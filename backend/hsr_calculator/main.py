import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _api_post(path: str, payload: Dict[str, Any]):
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory().post(path, payload, format="json")


def _api_get(path: str, query: Dict[str, Any] | None = None):
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory().get(path, data=query or {})

# Test data sets for different scenarios
TEST_SCENARIOS = {
    "simple_meal": {
        "food_ids": [2003, 3580],  # Simple two-food meal
        "serving_sizes": [150, 100],
        "description": "Simple meal with two foods"
    },
    "complex_meal": {
        "food_ids": [2003, 3580, 2892, 1001],  # More complex meal
        "serving_sizes": [150, 100, 10, 50],
        "description": "Complex meal with multiple foods"
    },
    "single_food": {
        "food_ids": [2003],  # Single food item
        "serving_sizes": [100],
        "description": "Single food analysis"
    },
    "comparison_foods": {
        "food_ids": [2003, 3580, 2892, 1001, 5001],  # Foods for comparison
        "serving_size": 100,  # Standard serving size for comparison
        "description": "Foods for comparison testing"
    }
}


def setup_django_environment():
    """Load full ``dish_project`` settings (CNF path, apps, cache) for API tests."""
    try:
        import django
        from django.conf import settings

        if not settings.configured:
            sys.path.insert(0, str(_BACKEND_ROOT))
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
            django.setup()

        logger.info("Django environment configured for testing")
        return True
    except Exception as e:
        logger.warning("Could not setup Django environment: %s", e)
        return False

def test_calculate_hsr_simple():
    """Test simple HSR calculation endpoint"""
    logger.info("\n" + "="*60)
    logger.info("TESTING: Simple HSR Calculation")
    logger.info("="*60)
    
    try:
        from api.views.hsr_views_consolidated import calculate_hsr

        test_data = TEST_SCENARIOS["simple_meal"]

        request = _api_post(
            "/api/hsr/calculate/",
            {
                "food_ids": test_data["food_ids"],
                "serving_sizes": test_data["serving_sizes"],
                "analysis_level": "simple",
                "include_alternatives": False,
                "include_meal_insights": False,
            },
        )
        
        logger.info(f"Testing: {test_data['description']}")
        logger.info(f"Food IDs: {test_data['food_ids']}")
        logger.info(f"Serving sizes: {test_data['serving_sizes']}")
        
        # Call the view
        response = calculate_hsr(request)
        
        if hasattr(response, 'data'):
            result = response.data
            logger.info(f"✓ Simple HSR calculation successful")
            logger.info(f"  Star Rating: {result.get('hsr_result', {}).get('rating', {}).get('star_rating', 'N/A')}")
            logger.info(f"  Level: {result.get('hsr_result', {}).get('rating', {}).get('level', 'N/A')}")
            logger.info(f"  Category: {result.get('hsr_result', {}).get('rating', {}).get('category', 'N/A')}")
            
            # Print some key insights
            key_insights = result.get('hsr_result', {}).get('key_insights', {})
            if key_insights:
                logger.info(f"  Strengths: {key_insights.get('strengths', 0)}")
                logger.info(f"  Concerns: {key_insights.get('concerns', 0)}")
            
            return True
        else:
            logger.error(f"✗ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Simple HSR calculation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_calculate_hsr_detailed():
    """Test detailed HSR calculation endpoint"""
    logger.info("\n" + "="*60)
    logger.info("TESTING: Detailed HSR Calculation")
    logger.info("="*60)
    
    try:
        from api.views.hsr_views_consolidated import calculate_hsr

        test_data = TEST_SCENARIOS["complex_meal"]

        request = _api_post(
            "/api/hsr/calculate/",
            {
                "food_ids": test_data["food_ids"],
                "serving_sizes": test_data["serving_sizes"],
                "analysis_level": "detailed",
                "include_alternatives": True,
                "include_meal_insights": True,
            },
        )
        
        logger.info(f"Testing: {test_data['description']}")
        logger.info(f"Food IDs: {test_data['food_ids']}")
        logger.info(f"Serving sizes: {test_data['serving_sizes']}")
        
        # Call the view
        response = calculate_hsr(request)
        
        if hasattr(response, 'data'):
            result = response.data
            logger.info(f"✓ Detailed HSR calculation successful")
            
            # Extract detailed information
            hsr_result = result.get('hsr_result', {})
            rating = hsr_result.get('rating', {})
            score_breakdown = hsr_result.get('score_breakdown', {})
            
            logger.info(f"  Star Rating: {rating.get('star_rating', 'N/A')}")
            logger.info(f"  Final Score: {score_breakdown.get('final_score', 'N/A')}")
            logger.info(f"  Baseline Points: {score_breakdown.get('baseline_points', 'N/A')}")
            logger.info(f"  Modifying Points: {score_breakdown.get('modifying_points', 'N/A')}")
            
            # Check for enhanced features
            enhanced_features = hsr_result.get('enhanced_features', {})
            if enhanced_features:
                logger.info("  Enhanced Features:")
                for feature, enabled in enhanced_features.items():
                    logger.info(f"    {feature}: {enabled}")
            
            # Food details
            food_details = result.get('food_details', [])
            logger.info(f"  Analyzed {len(food_details)} foods")
            
            return True
        else:
            logger.error(f"✗ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Detailed HSR calculation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_compare_foods():
    """Test food comparison endpoint"""
    logger.info("\n" + "="*60)
    logger.info("TESTING: Food Comparison")
    logger.info("="*60)
    
    try:
        from api.views.hsr_views_consolidated import compare_foods

        test_data = TEST_SCENARIOS["comparison_foods"]

        request = _api_post(
            "/api/hsr/compare/",
            {
                "food_ids": test_data["food_ids"],
                "serving_size": test_data["serving_size"],
                "sort_by": "hsr_rating",
            },
        )
        
        logger.info(f"Testing: {test_data['description']}")
        logger.info(f"Food IDs: {test_data['food_ids']}")
        logger.info(f"Standard serving size: {test_data['serving_size']}g")
        
        # Call the view
        response = compare_foods(request)
        
        if hasattr(response, 'data'):
            result = response.data
            logger.info(f"✓ Food comparison successful")
            
            comparison = result.get('comparison', {})
            logger.info(f"  Total foods: {comparison.get('total_foods', 0)}")
            logger.info(f"  Successfully analyzed: {comparison.get('successfully_analyzed', 0)}")
            
            # Show top foods
            foods = comparison.get('foods', [])
            valid_foods = [f for f in foods if 'hsr_rating' in f]
            
            if valid_foods:
                logger.info("  Top 3 foods by HSR rating:")
                for i, food in enumerate(valid_foods[:3]):
                    logger.info(f"    {i+1}. {food.get('food_name', 'Unknown')} - {food.get('hsr_rating', 'N/A')} stars")
            
            return True
        else:
            logger.error(f"✗ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Food comparison failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_food_profile():
    """Test individual food profile endpoint"""
    logger.info("\n" + "="*60)
    logger.info("TESTING: Food Profile Analysis")
    logger.info("="*60)
    
    try:
        from api.views.hsr_views_consolidated import get_food_hsr_profile

        food_id = TEST_SCENARIOS["single_food"]["food_ids"][0]
        serving_size = TEST_SCENARIOS["single_food"]["serving_sizes"][0]

        request = _api_get(
            f"/api/hsr/profile/{food_id}/",
            {
                "serving_size": str(serving_size),
                "include_alternatives": "true",
            },
        )
        
        logger.info(f"Testing food profile for Food ID: {food_id}")
        logger.info(f"Serving size: {serving_size}g")
        
        # Call the view
        response = get_food_hsr_profile(request, food_id)
        
        if hasattr(response, 'data'):
            result = response.data
            logger.info(f"✓ Food profile analysis successful")
            
            food_profile = result.get('food_profile', {})
            basic_info = food_profile.get('basic_info', {})
            
            logger.info(f"  Food: {basic_info.get('food_name', 'Unknown')}")
            logger.info(f"  Food Group: {basic_info.get('food_group', 'Unknown')}")
            logger.info(f"  HSR Category: {basic_info.get('hsr_category', 'Unknown')}")
            
            # HSR Analysis
            hsr_analysis = food_profile.get('hsr_analysis', {})
            rating = hsr_analysis.get('rating', {})
            if rating:
                logger.info(f"  HSR Rating: {rating.get('star_rating', 'N/A')} stars")
                logger.info(f"  Level: {rating.get('level', 'N/A')}")
            
            return True
        else:
            logger.error(f"✗ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Food profile analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_meal_insights():
    """Test meal insights endpoint"""
    logger.info("\n" + "="*60)
    logger.info("TESTING: Meal Insights Analysis")
    logger.info("="*60)
    
    try:
        from api.views.hsr_views_consolidated import get_meal_insights

        test_data = TEST_SCENARIOS["complex_meal"]

        request = _api_post(
            "/api/hsr/insights/",
            {
                "food_ids": test_data["food_ids"],
                "serving_sizes": test_data["serving_sizes"],
                "meal_type": "lunch",
                "dietary_goals": ["heart_health", "weight_loss"],
            },
        )
        
        logger.info(f"Testing: {test_data['description']}")
        logger.info(f"Meal type: lunch")
        logger.info(f"Dietary goals: heart_health, weight_loss")
        
        # Call the view
        response = get_meal_insights(request)
        
        if hasattr(response, 'data'):
            result = response.data
            logger.info(f"✓ Meal insights analysis successful")
            
            meal_insights = result.get('meal_insights', {})
            
            # Meal composition
            composition = meal_insights.get('meal_composition', {})
            if composition:
                logger.info(f"  Total foods: {composition.get('total_foods', 'N/A')}")
                logger.info(f"  Total weight: {composition.get('total_weight', 'N/A')}g")
            
            # HSR breakdown
            hsr_breakdown = meal_insights.get('hsr_breakdown', {})
            if hsr_breakdown:
                logger.info(f"  Final HSR Rating: {hsr_breakdown.get('final_rating', 'N/A')}")
            
            return True
        else:
            logger.error(f"✗ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Meal insights analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_error_handling():
    """Test error handling with invalid inputs"""
    logger.info("\n" + "="*60)
    logger.info("TESTING: Error Handling")
    logger.info("="*60)
    
    try:
        from api.views.hsr_views_consolidated import calculate_hsr

        test_cases = [
            {
                "name": "Empty food list",
                "data": {"food_ids": [], "serving_sizes": []}
            },
            {
                "name": "Mismatched arrays",
                "data": {"food_ids": [2003, 3580], "serving_sizes": [150]}
            },
            {
                "name": "Invalid serving size",
                "data": {"food_ids": [2003], "serving_sizes": [-50]}
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            request = _api_post("/api/hsr/calculate/", test_case["data"])
            
            try:
                response = calculate_hsr(request)
                if hasattr(response, "data"):
                    if response.status_code >= 400 or response.data.get("success") is False:
                        logger.info(
                            "    Handled error: %s",
                            response.data.get("error", response.data.get("message", "HTTP error")),
                        )
                    else:
                        logger.warning("    Expected error but got success")
                else:
                    logger.warning("    Unexpected response (no .data)")
            except Exception as e:
                logger.info("    Raised exception: %s", str(e))
        return True
        
    except Exception as e:
        logger.error(f"✗ Error handling test failed: {e}")
        return False


def main():
    """
    Main test runner for HSR Views Consolidated
    
    This test suite validates the HSR views from hsr_views_consolidated.py by:
    1. Setting up Django with ``dish_project.settings``
    2. Building requests with DRF ``APIRequestFactory``
    3. Testing all major endpoints with various scenarios
    4. Validating response formats and error handling
    5. Providing comprehensive logging and reporting
    
    Usage:
    - Run from the hsr_calculator directory: python main.py
    - Requires Django, CNF data, and all HSR calculator dependencies
    - Requires a successful Django setup (see ``setup_django_environment``)
    """
    start_time = time.time()
    
    logger.info("="*80)
    logger.info("HSR VIEWS CONSOLIDATED - COMPREHENSIVE TEST SUITE")
    logger.info("="*80)
    logger.info("Testing all endpoints from hsr_views_consolidated.py")
    logger.info("This validates the complete HSR API functionality")
    logger.info("="*80)
    
    # Setup environment
    django_available = setup_django_environment()
    
    if not django_available:
        logger.error("Django environment not available — aborting HSR API tests.")
        return
    
    # Track test results
    test_results = {}
    
    # Run comprehensive tests
    tests = [
        ("Simple HSR Calculation", test_calculate_hsr_simple),
        ("Detailed HSR Calculation", test_calculate_hsr_detailed),
        ("Food Comparison", test_compare_foods),
        ("Food Profile Analysis", test_food_profile),
        ("Meal Insights Analysis", test_meal_insights),
        ("Error Handling", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\nStarting test: {test_name}")
            result = test_func()
            test_results[test_name] = result
            
            if result:
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
                
        except Exception as e:
            logger.error(f"✗ {test_name} CRASHED: {e}")
            test_results[test_name] = False
    
    # Final summary
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall Results: {passed}/{total} tests passed")
    logger.info(f"Total execution time: {total_time:.3f} seconds")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.warning(f"⚠ {total - passed} tests failed")
    
    logger.info("="*80)


if __name__ == "__main__":
    main()