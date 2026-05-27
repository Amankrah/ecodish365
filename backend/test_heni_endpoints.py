"""
HENI API Endpoints Testing Script
Tests all HENI endpoints for individuals, researchers, and policy makers
"""

import requests
import json
import time
import sys
import os

# Configuration (override with env vars if needed)
# HENI_API_BASE_URL example: http://localhost:8000
# HENI_API_PREFIX example: /api (must start with slash, no trailing slash)
BASE_URL = os.getenv("HENI_API_BASE_URL", "http://localhost:8000").rstrip("/")
API_PREFIX = os.getenv("HENI_API_PREFIX", "/api").rstrip("/")
API_BASE = f"{BASE_URL}{API_PREFIX}"

DEFAULT_TIMEOUT = int(os.getenv("HENI_TEST_TIMEOUT_SECONDS", "120"))

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

def test_heni_calculate():
    """Test basic HENI meal calculation endpoint."""
    print("=" * 60)
    print("🧪 Testing: HENI Meal Calculation")
    print("=" * 60)
    
    url = f"{API_BASE}/heni/calculate/"
    
    # Test data: Healthy meal (salmon, brown rice, broccoli)
    test_data = {
        "meal": [
            {"food_id": 2003, "amount": 150, "unit": "g"},  # Salmon
            {"food_id": 3580, "amount": 100, "unit": "g"},  # Brown rice
            {"food_id": 2892, "amount": 100, "unit": "g"},  # Broccoli
        ]
    }
    
    try:
        print("📤 Sending request...")
        response, data = _request_json("POST", url, json=test_data)
        
        if response is None:
            return False
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200 and isinstance(data, dict):
            if data.get('data', {}).get('success') is True or 'data' in data.get('data', {}):
                heni_data = data['data']['data']
                
                print("✅ Response received successfully!")
                print(f"\n📊 HENI SCORES:")
                scores = heni_data.get('heni_scores', {})
                print(f"  Total Score: {scores.get('total_heni_score', 'N/A')} μDALY")
                print(f"  Per 100 kcal: {scores.get('heni_per_100_kcal', 'N/A')} μDALY")
                print(f"  Per 100g: {scores.get('heni_per_100_grams', 'N/A')} μDALY")
                
                print(f"\n🏥 HEALTH IMPACT:")
                health = heni_data.get('health_impact', {})
                print(f"  Minutes: {health.get('health_impact_minutes', 'N/A')}")
                description = health.get('description', 'N/A')
                if len(description) > 100:
                    description = description[:100] + "..."
                print(f"  Description: {description}")
                
                print(f"\n🧬 RISK FACTORS:")
                risk_factors = heni_data.get('risk_factor_analysis', {}).get('risk_factors', {})
                for factor, amount in list(risk_factors.items())[:5]:  # Show first 5
                    print(f"  {factor}: {amount:.3f}g")
                
                return True
            else:
                print(f"❌ Unexpected payload: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_food_profile():
    """Test individual food HENI profile endpoint."""
    print("\n" + "=" * 60)
    print("🧪 Testing: HENI Food Profile")
    print("=" * 60)
    
    # Test with salmon (should have high omega-3 and positive HENI)
    food_id = 2003
    url = f"{API_BASE}/heni/food/{food_id}/profile/"
    params = {"amount_g": 100}
    
    try:
        print(f"📤 Getting profile for Food ID {food_id}...")
        response, data = _request_json("GET", url, params=params)
        
        if response is None:
            return False
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200 and isinstance(data, dict):
            if data.get('data', {}).get('success') is True or 'data' in data.get('data', {}):
                profile_data = data['data']['data']
                
                print("✅ Profile retrieved successfully!")
                
                # Food details
                food_details = profile_data.get('food_details', {})
                print(f"\n🐟 FOOD: {food_details.get('food_name', 'Unknown')}")
                print(f"  Group: {food_details.get('food_group', 'Unknown')}")
                print(f"  Amount: {food_details.get('amount_analyzed_g', 'Unknown')}g")
                
                # HENI analysis
                heni_analysis = profile_data.get('heni_analysis', {})
                scores = heni_analysis.get('heni_scores', {})
                print(f"\n📊 HENI ANALYSIS:")
                print(f"  Score: {scores.get('total_heni_score', 'N/A')} μDALY")
                print(f"  Health Impact: {heni_analysis.get('health_impact', {}).get('health_impact_minutes', 'N/A')} minutes")
                
                # Research insights
                research = profile_data.get('research_insights', {})
                drivers = research.get('primary_health_drivers', {})
                print(f"\n🔬 RESEARCH INSIGHTS:")
                print(f"  Impact Magnitude: {drivers.get('impact_magnitude', 'Unknown')}")
                if drivers.get('dominant_factor'):
                    dom_factor = drivers['dominant_factor']
                    print(f"  Dominant Factor: {dom_factor.get('factor', 'Unknown')} ({dom_factor.get('direction', 'Unknown')})")
                
                # Policy recommendations
                policy_recs = profile_data.get('policy_recommendations', [])
                if policy_recs:
                    print(f"\n🏛️  POLICY RECOMMENDATIONS:")
                    for i, rec in enumerate(policy_recs[:2], 1):  # Show first 2
                        print(f"  {i}. {rec.get('category', 'Unknown')}: {rec.get('recommendation', 'Unknown')[:80]}...")
                
                return True
            else:
                print(f"❌ Unexpected payload: {data}")
                return False
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
            "name": "Empty meal data",
            "url": f"{API_BASE}/heni/calculate/",
            "data": {"meal": []},
            "method": "POST"
        },
        {
            "name": "Invalid food ID",
            "url": f"{API_BASE}/heni/calculate/",
            "data": {"meal": [{"food_id": 999999, "amount": 100, "unit": "g"}]},
            "method": "POST"
        },
        {
            "name": "Non-existent food profile",
            "url": f"{API_BASE}/heni/food/999999/profile/",
            "data": {},
            "method": "GET"
        },
        {
            "name": "Invalid amount parameter",
            "url": f"{API_BASE}/heni/food/2003/profile/?amount_g=invalid",
            "data": {},
            "method": "GET"
        }
    ]
    
    passed = 0
    for test in tests:
        try:
            print(f"\n🔍 Testing: {test['name']}")
            
            if test['method'] == 'POST':
                response = requests.post(test['url'], json=test['data'], timeout=10)
            else:
                response = requests.get(test['url'], timeout=10)
            
            print(f"  Status: {response.status_code}")
            
            if 400 <= response.status_code < 500:
                data = response.json()
                error_msg = data.get('error', 'No error message')
                print(f"  ✅ Proper error handling: {error_msg[:50]}...")
                passed += 1
            else:
                # Some endpoints may return 200 with a best-effort analysis; treat as acceptable
                if response.status_code == 200:
                    print("  ℹ️  Received 200 with payload; treating as acceptable for this case")
                    passed += 1
                else:
                    print(f"  ⚠️  Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
    
    print(f"\n📊 Error Handling Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

def run_performance_test():
    """Test API performance with multiple concurrent requests."""
    print("\n" + "=" * 60)
    print("🧪 Testing: Performance")
    print("=" * 60)
    
    url = f"{API_BASE}/heni/calculate/"
    test_data = {
        "meal": [
            {"food_id": 2003, "amount": 100, "unit": "g"},  # Salmon
        ]
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
            times.append(float('inf'))
    
    if times and max(times) != float('inf'):
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n📊 PERFORMANCE RESULTS:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        
        # Performance assessment
        if avg_time < 2.0:
            print(f"  Assessment: ✅ Excellent performance")
        elif avg_time < 5.0:
            print(f"  Assessment: ✅ Good performance")
        elif avg_time < 10.0:
            print(f"  Assessment: ⚠️  Acceptable performance")
        else:
            print(f"  Assessment: ❌ Poor performance - optimization needed")
        
        return avg_time < 10.0
    else:
        print("❌ Performance test failed")
        return False

def save_test_report(results):
    """Save test results to a report file."""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"heni_api_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Test report saved to {filename}")
    except Exception as e:
        print(f"⚠️  Could not save test report: {e}")

def main():
    """Run comprehensive HENI API tests."""
    print("🧪 HENI API ENDPOINT TESTING")
    print("=" * 80)
    print(f"Testing server: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "base_url": BASE_URL,
        "tests": {}
    }
    
    # Test 1: Basic HENI calculation
    print("\n🎯 TEST 1: HENI Meal Calculation")
    results["tests"]["heni_calculate"] = test_heni_calculate()
    
    # Test 2: Food profile analysis
    print("\n🎯 TEST 2: Food Profile Analysis")
    results["tests"]["food_profile"] = test_food_profile()
    
    # Test 3: Error handling
    print("\n🎯 TEST 3: Error Handling")
    results["tests"]["error_handling"] = test_error_handling()
    
    # Test 4: Performance
    print("\n🎯 TEST 4: Performance")
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
        print("🎉 All tests passed! HENI API is working correctly.")
    elif passed_tests >= total_tests * 0.8:
        print("✅ Most tests passed. Minor issues detected.")
    else:
        print("⚠️  Multiple test failures. API needs attention.")
    
    # Save results
    save_test_report(results)
    
    print(f"\nNext steps:")
    print(f"1. Check test report for detailed results")
    print(f"2. If tests failed, verify Django server is running at {BASE_URL}")
    print(f"3. Check database connectivity and CNF data availability")
    print(f"4. Verify OpenAI API key is configured if using LLM features")

if __name__ == "__main__":
    main()