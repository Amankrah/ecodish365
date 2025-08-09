import time
import logging
from fcs.models.food_item import FoodItem
from fcs.utils.cnf_data_integrator import create_cnf_integrator
from fcs.analyzers.food_analyzer import FoodAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        print("=== FCS CALCULATION PERFORMANCE TEST ===")
        
        # Start total timing
        total_start = time.time()

        # Time food item creation
        item_start = time.time()
        food_item = FoodItem("Example Food")
        item_time = time.time() - item_start
        print(f"Food item creation: {item_time:.3f} seconds")
        
        # Example food IDs ([Fish, salmon, atlantic, wild, raw], [Rice, spanish rice mix, unprepared])
        food_ids = [3049, 3725]  
        
        # Time integrator initialization
        integrator_start = time.time()
        cnf_integrator = create_cnf_integrator()
        integrator_time = time.time() - integrator_start
        print(f"CNF integrator initialization: {integrator_time:.3f} seconds")
        
        # Time nutrient extraction (the main heavy operation)
        extraction_start = time.time()
        cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)
        extraction_time = time.time() - extraction_start
        print(f"Nutrient extraction: {extraction_time:.3f} seconds")
        
        # Debug: Show what nutrients were extracted
        print(f"\nDEBUG: Food item '{food_item.name}' after nutrient extraction:")
        for domain, attributes in food_item.attributes.items():
            non_zero_attrs = {k: v for k, v in attributes.items() if v != 0}
            if non_zero_attrs:
                print(f"  {domain}: {non_zero_attrs}")
        
        # Time analyzer creation
        analyzer_start = time.time()
        analyzer = FoodAnalyzer()
        analyzer_time = time.time() - analyzer_start
        print(f"\nFood analyzer creation: {analyzer_time:.3f} seconds")
        
        # Time food analysis (FCS computation)
        analysis_start = time.time()
        result = analyzer.analyze_food_item(food_item)
        analysis_time = time.time() - analysis_start
        print(f"Food analysis (FCS computation): {analysis_time:.3f} seconds")

        # Display the analysis results
        total_time = time.time() - total_start
        
        print(f"\n=== FCS RESULTS ===")
        print(f"Analysis for {result['name']}:")
        print(f"Original Score: {result['original_score']}")
        print(f"Food Compass Score (FCS): {result['fcs']}")
        print(f"NOVA Category: {result['nova_category']}")
        
        print(f"\n=== PERFORMANCE SUMMARY ===")
        print(f"Food item creation: {item_time:.3f}s")
        print(f"CNF integrator initialization: {integrator_time:.3f}s")
        print(f"Nutrient extraction: {extraction_time:.3f}s")
        print(f"Food analyzer creation: {analyzer_time:.3f}s")
        print(f"Food analysis (FCS computation): {analysis_time:.3f}s")
        print(f"TOTAL TIME: {total_time:.3f} seconds")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

def test_subsequent_calculations():
    """Test performance of subsequent calculations after pipeline is loaded"""
    print("\n=== TESTING SUBSEQUENT CALCULATIONS ===")
    
    cnf_integrator = create_cnf_integrator()  # Should use cached pipeline
    analyzer = FoodAnalyzer()
    
    # Test different food combinations
    test_cases = [
        ([3049], "Single food: Salmon"),
        ([3725], "Single food: Rice bran bread"),
        ([3049, 3725], "Two foods: Salmon + Bread"),
        ([3049, 3725, 3580], "Three foods: Salmon + Bread + Venison")
    ]
    
    for food_ids, description in test_cases:
        start_time = time.time()
        
        # Create food item and extract nutrients
        food_item = FoodItem(f"Test: {description}")
        cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)
        
        # Analyze food item
        result = analyzer.analyze_food_item(food_item)
        
        calc_time = time.time() - start_time
        print(f"{description}: {calc_time:.3f}s (FCS: {result['fcs']:.1f}, NOVA: {result['nova_category']})")

if __name__ == "__main__":
    main()
    test_subsequent_calculations()