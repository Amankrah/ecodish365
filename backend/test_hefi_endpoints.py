#!/usr/bin/env python3
"""
Test script for HEFI endpoints
Run this after starting the Django server to test the new HEFI API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_hefi_calculate():
    """Test the basic HEFI calculation endpoint"""
    print("\n=== Testing HEFI Calculate ===")
    
    url = f"{BASE_URL}/hefi/calculate/"
    data = {
        "food_ids": [3049, 3725]  # Salmon and rice bran bread
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Total Score: {result['data']['total_score']}/80")
            print(f"Percentage: {result['data']['percentage']:.1f}%")
            print(f"Food Name: {result['data']['food_name']}")
            print(f"Components breakdown:")
            for comp, details in result['data']['components'].items():
                print(f"  {details['name']}: {details['score']:.1f}/{details['max_points']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

def test_hefi_food_profile():
    """Test the HEFI food profile endpoint"""
    print("\n=== Testing HEFI Food Profile ===")
    
    food_id = 3049  # Salmon
    url = f"{BASE_URL}/hefi/food/{food_id}/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Food: {result['data']['food_name']}")
            print(f"HEFI Score: {result['data']['total_score']}/80")
            print(f"Grade: {result['data']['hefi_interpretation']['grade']}")
            print(f"Description: {result['data']['hefi_interpretation']['description']}")
            print(f"Measure: {result['data']['measure_info']['conversion_factor']} ({result['data']['measure_info'].get('measure_description', 'Unknown')})")
            print(f"Energy: {result['data']['inputs']['energy_kcal']:.1f} kcal")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

def test_hefi_compare():
    """Test the HEFI compare endpoint"""
    print("\n=== Testing HEFI Compare ===")
    
    url = f"{BASE_URL}/hefi/compare/"
    data = {
        "foods": [
            {"food_ids": [3049], "food_name": "Salmon"},
            {"food_ids": [3725], "food_name": "Rice Bran Bread"},
            {"food_ids": [3049, 3725], "food_name": "Salmon & Bread Meal"}
        ]
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Compared {result['data']['total_compared']} items")
            print(f"Best performing: {result['data']['comparison_insights']['best_performing']}")
            print(f"Score range: {result['data']['comparison_insights']['score_range']:.1f}")
            
            print("\nRankings:")
            for i, food in enumerate(result['data']['foods'], 1):
                if 'error' not in food:
                    print(f"{i}. {food['food_name']}: {food['total_score']:.1f}/80 ({food['percentage']:.1f}%)")
                else:
                    print(f"{i}. {food['food_name']}: Error - {food['error']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    print("HEFI API Endpoints Test")
    print("Make sure Django server is running on http://localhost:8000")
    
    test_hefi_calculate()
    test_hefi_food_profile() 
    test_hefi_compare()
    
    print("\n=== Test Complete ===")