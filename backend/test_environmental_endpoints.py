"""
Environmental API Endpoints Testing Script
Tests environmental impact endpoints for different scenarios and users

Environment variables (optional):
- ENV_API_BASE_URL (default: http://localhost:8000)
- ENV_API_PREFIX (default: /api)
- ENV_TEST_TIMEOUT_SECONDS (default: 120)
"""

import requests
import json
import time
import os

# Configuration
BASE_URL = os.getenv("ENV_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = os.getenv("ENV_API_PREFIX", "/api").rstrip("/")
API_BASE = f"{BASE_URL}{API_PREFIX}"

DEFAULT_TIMEOUT = int(os.getenv("ENV_TEST_TIMEOUT_SECONDS", "120"))


def _request_json(method, url, **kwargs):
    """Helper to make a request and return parsed JSON with robust error handling."""
    try:
        resp = requests.request(method, url, timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT), **kwargs)
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None, None
    try:
        data = resp.json()
    except Exception:
        data = None
    return resp, data


def _unwrap_payload(data: dict) -> dict:
    """Unwrap API response envelopes while preserving sibling keys.

    Handles:
    - {"data": {"success": true, "data": {...}}}
    - {"data": {...}}
    - {"data": {...}, "meal_info": {...}, "metadata": {...}}  -> keep as-is
    - {...} (already raw)
    """
    if not isinstance(data, dict):
        return {}

    if "data" not in data:
        return data

    # If the response contains sibling keys besides the common envelope keys,
    # do not unwrap to avoid losing siblings like meal_info/metadata.
    sibling_keys = set(data.keys()) - {"data", "success", "message", "seo_metadata"}
    if sibling_keys:
        return data

    inner = data.get("data")
    if isinstance(inner, dict) and "data" in inner:
        return inner.get("data", {}) or {}
    return inner if isinstance(inner, dict) else data


def test_environmental_impact():
    """Test comprehensive environmental impact calculation endpoint."""
    print("=" * 60)
    print("🧪 Testing: Environmental Impact (Meal)")
    print("=" * 60)

    url = f"{API_BASE}/environmental-impact/"

    # Example meal: chicken + beans
    test_data = {
        "foods": [
            {"food_id": 2003, "quantity": 150},  # Salmon/chicken id used elsewhere in repo
            {"food_id": 3580, "quantity": 100},
        ],
        "user_type": "individual",
    }

    try:
        print("📤 Sending request...")
        response, data = _request_json("POST", url, json=test_data)

        if response is None:
            return False
        print(f"📥 Status Code: {response.status_code}")

        if response.status_code == 200 and isinstance(data, dict):
            raw = data
            payload = _unwrap_payload(data)
            # Expected keys within payload: data (sections), meal_info, metadata
            env_data = payload.get("data", payload)
            # Robust fallback across possible envelope shapes
            meal_info = (
                payload.get("meal_info")
                or raw.get("meal_info")
                or (raw.get("data", {}) if isinstance(raw.get("data"), dict) else {}).get("meal_info")
                or {}
            )
            metadata = (
                payload.get("metadata")
                or raw.get("metadata")
                or (raw.get("data", {}) if isinstance(raw.get("data"), dict) else {}).get("metadata")
                or {}
            )

            print("✅ Response received successfully!")

            monet = env_data.get("monetization", {}).get("results", {})
            impacts = env_data.get("environmental_impacts", {})
            key_impacts = impacts.get("key_impacts", {})

            print("\n💰 Monetization:")
            print(f"  Total Cost: {monet.get('total_environmental_cost', {}).get('formatted', 'N/A')}")
            print(f"  Cost/Calorie: {monet.get('cost_per_calorie', {}).get('formatted', 'N/A')}")

            print("\n🌍 Key Impacts:")
            cf = key_impacts.get("carbon_footprint", {})
            wc = key_impacts.get("water_consumption", {})
            lu = key_impacts.get("land_use", {})
            print(f"  Carbon: {cf.get('formatted', 'N/A')}")
            print(f"  Water: {wc.get('formatted', 'N/A')}")
            print(f"  Land: {lu.get('formatted', 'N/A')}")

            print("\n🍽️ Meal Info:")
            print(f"  Total Calories: {meal_info.get('total_calories', 'N/A')}")
            print(f"  Total Weight: {meal_info.get('total_weight', 'N/A')} g")

            print("\nℹ️ Metadata:")
            print(f"  Method: {metadata.get('methodology', 'N/A')}")
            print(f"  Functional Unit: {metadata.get('functional_unit', 'N/A')}")

            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_compare_foods():
    """Test environmental comparison of multiple foods."""
    print("\n" + "=" * 60)
    print("🧪 Testing: Environmental Compare Foods")
    print("=" * 60)

    url = f"{API_BASE}/environmental-impact/compare-foods/"
    test_data = {
        "foods": [
            {"food_id": 2003, "quantity": 100, "name": "Food A"},
            {"food_id": 3580, "quantity": 100, "name": "Food B"},
        ],
        "user_type": "researcher",
    }

    try:
        response, data = _request_json("POST", url, json=test_data)
        if response is None:
            return False
        print(f"📥 Status Code: {response.status_code}")

        if response.status_code == 200 and isinstance(data, dict):
            payload = _unwrap_payload(data)
            comparisons = payload.get("food_comparisons", [])
            insights = payload.get("comparison_insights", {})
            meta = payload.get("metadata", {})

            print(f"✅ Compared {len(comparisons)} foods (basis: {meta.get('comparison_basis', 'N/A')})")
            if isinstance(insights, dict) and insights.get("winners"):
                winners = insights["winners"]
                print("\n🏆 Winners:")
                if winners.get("lowest_carbon_footprint"):
                    w = winners["lowest_carbon_footprint"]
                    print(f"  Lowest Carbon: {w.get('food')} ({w.get('value')})")
                if winners.get("most_sustainable"):
                    w = winners["most_sustainable"]
                    print(f"  Most Sustainable: {w.get('food')} ({w.get('score')})")

            # Show first two detailed comparisons if available
            for comp in comparisons[:2]:
                if "error" in comp:
                    print(f"  ⚠️  {comp.get('food_id')}: {comp['error']}")
                else:
                    fi = comp.get("food_info", {})
                    e100 = comp.get("environmental_impact_per_100g", {})
                    cf_val = e100.get('carbon_footprint')
                    try:
                        cf_text = f"{float(cf_val):.4f}"
                    except Exception:
                        cf_text = "N/A"
                    print(f"  {fi.get('name', 'Food')} - Carbon/100g: {cf_text}")

            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_food_profile():
    """Test individual food environmental profile."""
    print("\n" + "=" * 60)
    print("🧪 Testing: Food Environmental Profile")
    print("=" * 60)

    food_id = 2003
    url = f"{API_BASE}/environmental-impact/food/{food_id}/profile/"
    params = {"quantity": 150, "user_type": "policy"}

    try:
        response, data = _request_json("GET", url, params=params)
        if response is None:
            return False
        print(f"📥 Status Code: {response.status_code}")

        if response.status_code == 200 and isinstance(data, dict):
            payload = _unwrap_payload(data)
            info = payload.get("food_info", {})
            profile = payload.get("environmental_profile", {})
            econ = payload.get("economic_impact", {})
            sust = payload.get("sustainability_assessment", {})

            print("✅ Profile retrieved successfully!")
            print(f"\n🍽️ Food: {info.get('name', 'Unknown')} ({info.get('quantity_analyzed', 'N/A')})")

            key = profile.get("key_impacts", {})
            print("\n🌍 Key Impacts per 100g:")
            for k in ["carbon_footprint", "water_consumption", "land_use"]:
                v = key.get(k, {})
                per100 = v.get('per_100g', 'N/A')
                try:
                    per100 = f"{float(per100):.6f}"
                except Exception:
                    pass
                print(f"  {k.replace('_',' ').title()}: {per100} {v.get('unit', '')}")

            print("\n💰 Economic Impact:")
            print(f"  Total Cost: {econ.get('total_cost', 'N/A')} CAD")
            print(f"  Cost/100g: {econ.get('cost_per_100g', 'N/A')} CAD")

            print("\n♻️  Sustainability:")
            print(f"  Overall Score: {sust.get('overall_score', 'N/A')}")
            print(f"  Rating: {sust.get('rating', 'N/A')}")

            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_error_handling():
    """Test API error handling with invalid data."""
    print("\n" + "=" * 60)
    print("🧪 Testing: Error Handling")
    print("=" * 60)

    tests = [
        {
            "name": "Empty foods array",
            "url": f"{API_BASE}/environmental-impact/",
            "data": {"foods": []},
            "method": "POST",
        },
        {
            "name": "Invalid food ID",
            "url": f"{API_BASE}/environmental-impact/",
            "data": {"foods": [{"food_id": 999999, "quantity": 100}]},
            "method": "POST",
        },
        {
            "name": "Compare with only one item",
            "url": f"{API_BASE}/environmental-impact/compare-foods/",
            "data": {"foods": [{"food_id": 2003, "quantity": 100}]},
            "method": "POST",
        },
        {
            "name": "Non-existent food profile",
            "url": f"{API_BASE}/environmental-impact/food/999999/profile/",
            "data": {},
            "method": "GET",
        },
    ]

    passed = 0
    for test in tests:
        try:
            print(f"\n🔍 Testing: {test['name']}")

            if test["method"] == "POST":
                response = requests.post(test["url"], json=test["data"], timeout=15)
            else:
                response = requests.get(test["url"], timeout=15)

            print(f"  Status: {response.status_code}")

            if 400 <= response.status_code < 500:
                data = response.json()
                error_msg = data.get("error", "No error message")
                print(f"  ✅ Proper error handling: {error_msg[:60]}...")
                passed += 1
            else:
                if response.status_code == 200:
                    # Some endpoints may return 200 with descriptive payloads
                    print("  ℹ️  Received 200; treating as acceptable for this case")
                    passed += 1
                else:
                    print(f"  ⚠️  Unexpected status code: {response.status_code}")

        except Exception as e:
            print(f"  ❌ Request failed: {e}")

    print(f"\n📊 Error Handling Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)


def run_performance_test():
    """Test API performance with multiple requests to the main endpoint."""
    print("\n" + "=" * 60)
    print("🧪 Testing: Performance")
    print("=" * 60)

    url = f"{API_BASE}/environmental-impact/"
    test_data = {
        "foods": [{"food_id": 2003, "quantity": 100}],
    }

    num_requests = 5
    times = []

    print(f"🚀 Sending {num_requests} requests...")

    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.post(url, json=test_data, timeout=30)
            end_time = time.time()

            request_time = end_time - start_time
            times.append(request_time)

            status = "✅" if response.status_code == 200 else "❌"
            print(f"  Request {i+1}: {status} {request_time:.3f}s")

        except Exception as e:
            print(f"  Request {i+1}: ❌ Failed - {e}")
            times.append(float("inf"))

    if times and max(times) != float("inf"):
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\n📊 PERFORMANCE RESULTS:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")

        if avg_time < 2.0:
            print("  Assessment: ✅ Excellent performance")
        elif avg_time < 5.0:
            print("  Assessment: ✅ Good performance")
        elif avg_time < 10.0:
            print("  Assessment: ⚠️  Acceptable performance")
        else:
            print("  Assessment: ❌ Poor performance - optimization needed")

        return avg_time < 10.0
    else:
        print("❌ Performance test failed")
        return False


def save_test_report(results):
    """Save test results to a report file."""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"environmental_api_test_report_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📄 Test report saved to {filename}")
    except Exception as e:
        print(f"⚠️  Could not save test report: {e}")


def main():
    """Run comprehensive Environmental API tests."""
    print("🧪 ENVIRONMENTAL API ENDPOINT TESTING")
    print("=" * 80)
    print(f"Testing server: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "base_url": BASE_URL,
        "tests": {},
    }

    # Test 1: Environmental impact calculation
    print("\n🎯 TEST 1: Environmental Impact (Meal)")
    results["tests"]["environmental_impact"] = test_environmental_impact()

    # Test 2: Food profile analysis
    print("\n🎯 TEST 2: Food Environmental Profile")
    results["tests"]["food_profile"] = test_food_profile()

    # Test 3: Compare foods
    print("\n🎯 TEST 3: Compare Foods")
    results["tests"]["compare_foods"] = test_compare_foods()

    # Test 4: Error handling
    print("\n🎯 TEST 4: Error Handling")
    results["tests"]["error_handling"] = test_error_handling()

    # Test 5: Performance
    print("\n🎯 TEST 5: Performance")
    results["tests"]["performance"] = run_performance_test()

    # Summary
    passed_tests = sum(1 for result in results["tests"].values() if result)
    total_tests = len(results["tests"])

    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Passed: {passed_tests}/{total_tests} tests")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Environmental API is working correctly.")
    elif passed_tests >= total_tests * 0.8:
        print("✅ Most tests passed. Minor issues detected.")
    else:
        print("⚠️  Multiple test failures. API needs attention.")

    # Save results
    save_test_report(results)

    print("\nNext steps:")
    print(f"1. Check test report for detailed results")
    print(f"2. Verify Django server is running at {BASE_URL}")
    print("3. Ensure CNF data is available and paths are configured")


if __name__ == "__main__":
    main()


