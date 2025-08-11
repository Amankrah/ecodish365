"""
HENI Calculator Testing Script
Updated to use the new CNF integrator and comprehensive DALY-based methodology
"""

import os
import sys
import time
import json

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api'))

import logging
from heni.database.cnf_integrator import create_heni_cnf_integrator
from heni.models.ingredient import Ingredient
from heni.calculator.heni_calculator import HENICalculator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_heni_calculation():
    """Test basic HENI calculation with sample foods."""
    print("=" * 60)
    print("HENI Calculator Test - Basic Calculation")
    print("=" * 60)
    
    try:
        start_time = time.time()
        
        # Get CNF folder path (adjust as needed)
        cnf_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'raw_cnf')
        integrator = create_heni_cnf_integrator(cnf_folder)
        
        # Get OpenAI API key from environment
        llm_api_key = os.getenv('OPENAI_API_KEY', '')
        heni_calculator = HENICalculator(integrator, llm_api_key)

        # Test meal: Salmon (high omega-3), Brown rice (whole grains), Broccoli (vegetables)
        meal_ingredients = [
            Ingredient(food_id=2003, amount=150, unit="g", cnf_integrator=integrator),  # Salmon
            Ingredient(food_id=3580, amount=100, unit="g", cnf_integrator=integrator),  # Brown rice
            Ingredient(food_id=2892, amount=100, unit="g", cnf_integrator=integrator),  # Broccoli
        ]

        # Calculate comprehensive HENI result
        comprehensive_result = heni_calculator.calculate_meal_heni(meal_ingredients)
        
        # Display results
        print(f"\n📊 HENI SCORES:")
        heni_scores = comprehensive_result['heni_scores']
        print(f"  Total HENI Score: {heni_scores['total_heni_score']} μDALY")
        print(f"  Per 100 kcal: {heni_scores['heni_per_100_kcal']} μDALY")
        print(f"  Per 100 grams: {heni_scores['heni_per_100_grams']} μDALY")
        print(f"  Per serving: {heni_scores['heni_per_serving']} μDALY")

        print(f"\n🏥 HEALTH IMPACT:")
        health_impact = comprehensive_result['health_impact']
        print(f"  Health Impact: {health_impact['health_impact_minutes']} minutes")
        print(f"  Description: {health_impact['description']}")

        print(f"\n🧬 COMPONENT BREAKDOWN:")
        components = comprehensive_result['component_breakdown']
        
        if components['food_group_contributions']:
            print("  Food Group Contributions:")
            for group, contribution in components['food_group_contributions'].items():
                print(f"    - {group.replace('_', ' ').title()}: {contribution} μDALY")
        
        if components['nutrient_contributions']:
            print("  Nutrient Contributions:")
            for nutrient, contribution in components['nutrient_contributions'].items():
                print(f"    - {nutrient.replace('_', ' ').title()}: {contribution} μDALY")

        print(f"\n🦠 DISEASE BURDEN ANALYSIS:")
        disease_analysis = comprehensive_result['disease_burden_analysis']
        for disease, burden in disease_analysis['disease_breakdown'].items():
            if abs(burden) > 0.1:  # Only show significant contributors
                direction = "reduces" if burden > 0 else "increases"
                print(f"    - {disease.replace('_', ' ').title()}: {direction} burden by {abs(burden):.2f} μDALY")

        print(f"\n⚠️  RISK FACTOR ANALYSIS:")
        risk_analysis = comprehensive_result['risk_factor_analysis']
        if risk_analysis['risk_factors']:
            print("  Detected Risk Factors:")
            for factor, amount in risk_analysis['risk_factors'].items():
                if amount > 0:
                    print(f"    - {factor.replace('_', ' ').title()}: {amount:.3f}g")
        
        if risk_analysis['warnings']:
            print("  Warnings:")
            for warning in risk_analysis['warnings']:
                print(f"    ⚠️  {warning}")

        print(f"\n🍽️  MEAL COMPOSITION:")
        meal_comp = comprehensive_result['meal_composition']
        print(f"  Total Energy: {meal_comp['total_energy_kcal']} kcal")
        print(f"  Total Weight: {meal_comp['total_weight_grams']} g")
        print(f"  Ingredients: {meal_comp['ingredient_count']}")
        
        print("\n📋 INGREDIENT DETAILS:")
        for ingredient_detail in meal_comp['ingredient_details']:
            print(f"  • {ingredient_detail['description']} ({ingredient_detail['amount_g']}g)")
            print(f"    Energy: {ingredient_detail['energy_kcal']:.1f} kcal")
            if ingredient_detail['risk_factors']:
                print(f"    Risk factors: {len(ingredient_detail['risk_factors'])} detected")

        end_time = time.time()
        print(f"\n⏱️  Execution Time: {end_time - start_time:.3f} seconds")
        print("✅ Test completed successfully!")
        
        return comprehensive_result
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        return None

def test_individual_foods():
    """Test HENI calculation for individual foods."""
    print("\n" + "=" * 60)
    print("HENI Calculator Test - Individual Foods")
    print("=" * 60)
    
    try:
        cnf_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'raw_cnf')
        integrator = create_heni_cnf_integrator(cnf_folder)
        llm_api_key = os.getenv('OPENAI_API_KEY', '')
        heni_calculator = HENICalculator(integrator, llm_api_key)
        
        # Test different food categories
        test_foods = [
            (2003, "Salmon (high omega-3)"),
            (1234, "Processed meat (high risk)") if 1234 else None,  # Replace with actual processed meat ID
            (9999, "Soft drink (sugar-sweetened)") if 9999 else None,  # Replace with actual soft drink ID
            (2892, "Broccoli (vegetables)"),
            (3580, "Brown rice (whole grains)"),
        ]
        
        test_foods = [food for food in test_foods if food is not None]
        
        for food_id, description in test_foods:
            try:
                print(f"\n🔍 Testing: {description}")
                
                ingredient = Ingredient(food_id=food_id, amount=100, unit="g", cnf_integrator=integrator)
                result = heni_calculator.calculate_meal_heni([ingredient])
                
                heni_per_100g = result['heni_scores']['heni_per_100_grams']
                health_minutes = result['health_impact']['health_impact_minutes']
                
                print(f"  HENI Score: {heni_per_100g:.2f} μDALY/100g")
                print(f"  Health Impact: {health_minutes:.1f} minutes")
                
                # Show top risk factors
                risk_factors = result['risk_factor_analysis']['risk_factors']
                if risk_factors:
                    top_factors = sorted(risk_factors.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
                    print(f"  Top factors: {', '.join([f'{name}: {value:.2f}g' for name, value in top_factors])}")
                    
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Individual foods test failed: {e}")
        print(f"❌ Individual foods test failed: {e}")

def save_test_results(result, filename="heni_test_results.json"):
    """Save test results to JSON file for analysis."""
    try:
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📄 Results saved to {filename}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")

def main():
    """Run comprehensive HENI tests."""
    print("🧪 Starting HENI Calculator Tests...")
    
    # Test 1: Basic comprehensive calculation
    result = test_heni_calculation()
    
    # Test 2: Individual food analysis
    test_individual_foods()
    
    # Save results for analysis
    if result:
        save_test_results(result)
    
    print("\n🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Run API endpoint tests: python test_heni_endpoints.py")
    print("2. Check results in heni_test_results.json")
    print("3. Verify LLM categorization is working efficiently")

if __name__ == "__main__":
    main()