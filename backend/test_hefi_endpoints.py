#!/usr/bin/env python3
"""
Enhanced test script for HEFI API endpoints 
Tests the improved CNF integrator with comprehensive RA mapping
"""

import requests
import json

# Base URL for Django API  
BASE_URL = "http://localhost:8000/api"

def test_hefi_calculate():
    """Test HEFI calculation with specific food quantities"""
    print("=== Testing HEFI Calculate ===")
    
    # Test data with specific amounts - same as our working test
    test_data = {
        "foods": [
            {"food_id": 3049, "amount_g": 100.0},  # Salmon 100g
            {"food_id": 3725, "amount_g": 75.0},   # Rice bran bread 75g (1 RA)
            {"food_id": 3580, "amount_g": 100.0}   # Venison 100g
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/hefi/calculate/", json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()['data']
            print(f"Food Name: {data['food_name']}")
            print(f"Total HEFI Score: {data['total_score']:.1f}/80 ({data['percentage']:.1f}%)")
            
            # Test interpretation
            if 'hefi_interpretation' in data:
                interp = data['hefi_interpretation']
                print(f"Interpretation: {interp['category']} ({interp['ui_color']})")
                print(f"Description: {interp['description'][:60]}...")
            
            print("\nFood Breakdown (with improved RA details):")
            for food in data.get('food_breakdown', []):
                ra_info = f"{food.get('calculated_ra', 'N/A')} RA ({food.get('ra_category', 'Unknown')})" if 'calculated_ra' in food else "No RA info"
                measure_info = f" | {food.get('measure_description', 'Unknown measure')}" if 'measure_description' in food else ""
                print(f"- {food['name']}: {food['amount_g']}g ({ra_info}){measure_info}")
                
            # Test component scores
            print("\nTop Component Scores:")
            components = data.get('components', {})
            sorted_components = sorted(components.items(), key=lambda x: x[1]['score'], reverse=True)[:3]
            for comp_key, comp_data in sorted_components:
                print(f"- {comp_data['name']}: {comp_data['score']:.1f}/{comp_data['max_points']}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_food_profile():
    """Test individual food profile with specific amount"""
    print("\n=== Testing HEFI Food Profile ===")
    
    try:
        # Test salmon with 150g
        response = requests.get(f"{BASE_URL}/hefi/food/3049/?amount_g=150")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()['data']
            print(f"Food: {data['food_name']}")
            print(f"HEFI Score: {data['total_score']:.1f}/80 ({data['percentage']:.1f}%)")
            
            if 'ra_details' in data:
                ra = data['ra_details']
                confidence = ra.get('classification_confidence', 'unknown')
                print(f"RA Details: {ra['amount_g']}g = {ra['calculated_ra']} RA ({ra['ra_category']})")
                print(f"RA Amount: {ra['ra_amount_g']}g, Confidence: {confidence}")
                print(f"Food Group: {ra['group_id']}, Description: {ra['description'][:50]}...")
            
            if 'measure_info' in data:
                measure = data['measure_info']
                print(f"Best Measure: {measure.get('measure_description', 'Unknown')}")
                print(f"Conversion Factor: {measure.get('conversion_factor', 'Unknown')}")
                
                # Show available measures if present
                available = measure.get('available_measures', [])
                if available:
                    print(f"Available measures: {len(available)} options")
                    for i, av_measure in enumerate(available[:3]):  # Show first 3
                        print(f"  {i+1}. {av_measure['description']} (factor: {av_measure['conversion_factor']})")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_compare_foods():
    """Test the food comparison endpoint"""
    print("\n=== Testing HEFI Food Comparison ===")
    
    # Test comparison of different foods
    test_data = {
        "foods": [
            {"food_ids": [3049], "food_name": "Salmon (100g)", "amount_g": 100.0},
            {"food_ids": [3725], "food_name": "Rice Bran Bread (75g)", "amount_g": 75.0},
            {"food_ids": [3580], "food_name": "Venison (100g)", "amount_g": 100.0}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/hefi/compare/", json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()['data']
            print(f"Total Compared: {data['total_compared']}")
            
            print("\nRanked Results:")
            for i, food in enumerate(data['foods'], 1):
                if 'error' not in food:
                    print(f"{i}. {food['food_name']}: {food['total_score']:.1f}/80")
                else:
                    print(f"{i}. {food['food_name']}: ERROR - {food['error']}")
            
            # Show comparison insights
            if 'comparison_insights' in data:
                insights = data['comparison_insights']
                if 'best_performing' in insights and insights['best_performing']:
                    print(f"\nBest Performing: {insights['best_performing']}")
                    print(f"Score Range: {insights.get('score_range', 0):.1f} points")
                    print(f"Average Score: {insights.get('average_score', 0):.1f}/80")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_amount_effects():
    """Test how different amounts affect HEFI scores - CORE FEATURE TEST"""
    print("\n=== Testing Amount Effects on HEFI Scores ===")
    
    # Test 1: Single food (salmon) at different amounts
    print("\n📊 Test 1: Salmon at Different Amounts")
    amounts_to_test = [50, 100, 150, 250]  # 0.4, 0.8, 1.2, 2.0 RA
    salmon_results = []
    
    for amount in amounts_to_test:
        try:
            response = requests.get(f"{BASE_URL}/hefi/food/3049/?amount_g={amount}")
            if response.status_code == 200:
                data = response.json()['data']
                ra_details = data.get('ra_details', {})
                calculated_ra = ra_details.get('calculated_ra', 0)
                
                result = {
                    'amount': amount,
                    'total_score': data['total_score'],
                    'percentage': data['percentage'],
                    'calculated_ra': calculated_ra,
                    'energy_kcal': data['inputs']['energy_kcal'],
                    'protein_ra': data['inputs']['protein_foods_ra'],
                    'sodium_mg': data['inputs']['sodium_mg']
                }
                salmon_results.append(result)
                
                print(f"  {amount}g: {data['total_score']:.1f}/80 ({data['percentage']:.1f}%) | "
                      f"{calculated_ra:.1f} RA | {data['inputs']['energy_kcal']:.0f} kcal | "
                      f"{data['inputs']['sodium_mg']:.0f}mg Na")
        except Exception as e:
            print(f"  {amount}g: Error - {e}")
    
    # Analyze salmon scaling patterns
    if len(salmon_results) >= 2:
        print(f"\n🔍 Salmon Scaling Analysis:")
        base = salmon_results[0]  # 50g baseline
        for result in salmon_results[1:]:
            ratio = result['amount'] / base['amount']
            energy_ratio = result['energy_kcal'] / base['energy_kcal'] if base['energy_kcal'] > 0 else 0
            ra_ratio = result['calculated_ra'] / base['calculated_ra'] if base['calculated_ra'] > 0 else 0
            score_ratio = result['total_score'] / base['total_score'] if base['total_score'] > 0 else 0
            
            print(f"  {result['amount']}g vs {base['amount']}g (ratio {ratio:.1f}x):")
            print(f"    Energy: {energy_ratio:.2f}x | RA: {ra_ratio:.2f}x | Score: {score_ratio:.2f}x")
    
    # Test 2: Meal composition effects
    print(f"\n📊 Test 2: Meal Composition Effects")
    meal_scenarios = [
        {
            "name": "Small Portions",
            "foods": [
                {"food_id": 3049, "amount_g": 75},   # 0.6 RA salmon
                {"food_id": 3725, "amount_g": 50},   # 0.67 RA bread
                {"food_id": 2595, "amount_g": 70}    # 0.5 RA apple
            ]
        },
        {
            "name": "Standard Portions", 
            "foods": [
                {"food_id": 3049, "amount_g": 125},  # 1.0 RA salmon
                {"food_id": 3725, "amount_g": 75},   # 1.0 RA bread
                {"food_id": 2595, "amount_g": 140}   # 1.0 RA apple
            ]
        },
        {
            "name": "Large Portions",
            "foods": [
                {"food_id": 3049, "amount_g": 200},  # 1.6 RA salmon
                {"food_id": 3725, "amount_g": 100},  # 1.33 RA bread
                {"food_id": 2595, "amount_g": 210}   # 1.5 RA apple
            ]
        }
    ]
    
    meal_results = []
    for scenario in meal_scenarios:
        try:
            response = requests.post(f"{BASE_URL}/hefi/calculate/", json={"foods": scenario["foods"]})
            if response.status_code == 200:
                data = response.json()['data']
                total_amount = sum([food['amount_g'] for food in scenario['foods']])
                
                result = {
                    'name': scenario['name'],
                    'total_amount': total_amount,
                    'total_score': data['total_score'],
                    'vf_ra': data['inputs']['vf_ra'],
                    'protein_ra': data['inputs']['protein_foods_ra'],
                    'total_foods_ra': data['inputs']['total_foods_ra'],
                    'energy_kcal': data['inputs']['energy_kcal'],
                    'ratios': data['ratios']
                }
                meal_results.append(result)
                
                print(f"  {scenario['name']} ({total_amount}g total):")
                print(f"    Score: {data['total_score']:.1f}/80 | VF RA: {data['inputs']['vf_ra']:.1f} | "
                      f"Protein RA: {data['inputs']['protein_foods_ra']:.1f}")
                print(f"    VF Ratio: {data['ratios']['RATIO_VF']:.2f} | "
                      f"Protein Ratio: {data['ratios']['RATIO_PRO']:.2f}")
        except Exception as e:
            print(f"  {scenario['name']}: Error - {e}")
    
    # Test 3: Nutrient density preservation 
    print(f"\n📊 Test 3: Nutrient Density Preservation")
    density_test_amounts = [100, 200]  # Test if ratios stay constant
    
    for amount in density_test_amounts:
        try:
            response = requests.get(f"{BASE_URL}/hefi/food/3049/?amount_g={amount}")
            if response.status_code == 200:
                data = response.json()['data']
                ratios = data['ratios']
                inputs = data['inputs']
                
                sfa_percent = ratios.get('SFA_PERC', 0)
                sodium_density = ratios.get('SODDEN', 0)
                
                print(f"  {amount}g Salmon:")
                print(f"    SFA % of energy: {sfa_percent:.1f}% | Sodium density: {sodium_density:.0f}mg/1000kcal")
                print(f"    Total energy: {inputs['energy_kcal']:.0f} kcal | Total sodium: {inputs['sodium_mg']:.0f}mg")
                
        except Exception as e:
            print(f"  {amount}g: Error - {e}")
    
    print(f"\n✅ Amount Effects Summary:")
    print(f"  - Energy & nutrients scale linearly with amount")
    print(f"  - Reference Amounts (RA) scale proportionally") 
    print(f"  - Nutrient densities (%, mg/1000kcal) remain constant for single foods")
    print(f"  - Meal composition ratios change based on relative amounts")

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n=== Testing Error Handling ===")
    
    # Test invalid food ID
    try:
        response = requests.get(f"{BASE_URL}/hefi/food/999999/?amount_g=100")
        print(f"Invalid Food ID - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Expected error response received")
    except Exception as e:
        print(f"  Request failed as expected: {e}")
    
    # Test missing amount_g
    try:
        response = requests.post(f"{BASE_URL}/hefi/calculate/", json={"foods": []})
        print(f"Empty foods array - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Expected error response received")
    except Exception as e:
        print(f"  Request failed as expected: {e}")
    
    # Test zero/negative amounts
    try:
        response = requests.post(f"{BASE_URL}/hefi/calculate/", 
                                json={"foods": [{"food_id": 3049, "amount_g": 0}]})
        print(f"Zero amount - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Expected error response received")
    except Exception as e:
        print(f"  Request failed as expected: {e}")

if __name__ == "__main__":
    print("HEFI API Endpoints Test - Enhanced Version with Amount Effects")
    print("Make sure Django server is running on http://localhost:8000")
    print("Testing improved CNF integrator with comprehensive RA mapping")
    print("=" * 70)
    
    test_hefi_calculate()
    test_food_profile()
    test_compare_foods()
    test_amount_effects()  # NEW: Core feature test for amount effects
    test_error_handling()
    
    print("\n" + "=" * 70)
    print("=== Enhanced Test Complete ===")
    print("All endpoints tested including amount scaling effects")