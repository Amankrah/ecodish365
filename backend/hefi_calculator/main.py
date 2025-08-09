import os
import time
import pandas as pd
from hefi.cnf_integrator import HEFICNFIntegrator
from hefi.models import HEFIInputs
from hefi.algorithm import compute_hefi


def main():
    print("=== HEFI CALCULATION PERFORMANCE TEST ===")
    
    # Start total timing
    total_start = time.time()
    
    # Time pipeline initialization
    init_start = time.time()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cnf_dir = os.path.join(base_dir, 'raw_cnf')
    integrator = HEFICNFIntegrator(cnf_dir)
    init_time = time.time() - init_start
    print(f"Pipeline initialization: {init_time:.3f} seconds")

    # Example food data with amounts (food_id, amount_in_grams)
    food_data = [
        (3049, 100.0),  # Salmon, 100g
        (3725, 75.0),   # Rice bran bread, 75g (1 RA)
        (3580, 100.0)   # Venison, 100g
    ]
    
    food_ids = [food_id for food_id, _ in food_data]
    
    # Time food data lookup
    lookup_start = time.time()
    foods_df = integrator._get_food_rows(food_ids)
    lookup_time = time.time() - lookup_start
    print(f"Food data lookup: {lookup_time:.3f} seconds")
    
    print("\n=== FOODS BEING ANALYZED ===")
    for i, (food_id, amount) in enumerate(food_data):
        food_row = foods_df[foods_df['FoodID'] == food_id]
        if not food_row.empty:
            desc = food_row['FoodDescription'].iloc[0]
            group = int(food_row['FoodGroupID'].iloc[0])
            
            # Show RA classification with improved details
            ra_category = integrator._classify_food_to_ra_category(desc, group)
            ra_amount = integrator._get_ra_amount(ra_category)
            calculated_ra = amount / ra_amount
            
            # Get conversion factor and measure info
            conversion_factor = integrator._get_best_conversion_factor(food_id)
            measure_desc = integrator.get_measure_description(food_id, conversion_factor)
            
            print(f"ID {food_id}: {desc} (Group: {group})")
            print(f"  Amount: {amount}g, RA Category: {ra_category}, RA Amount: {ra_amount}g")
            print(f"  Calculated RAs: {calculated_ra:.3f}, Conversion Factor: {conversion_factor}")
            print(f"  Best Measure: {measure_desc}")
            
            # Show classification confidence
            confidence = 'HIGH' if ra_category != 'default' else 'LOW (using default)'
            print(f"  Classification Confidence: {confidence}")
    
    # Time data aggregation (the main computation)
    agg_start = time.time()
    agg = integrator.aggregate_inputs(food_data)
    agg_time = time.time() - agg_start
    print(f"\nData aggregation: {agg_time:.3f} seconds")
    
    print("\n=== AGGREGATED INPUTS ===")
    for key, value in agg.items():
        print(f"{key}: {value}")

    # Time HEFI computation
    hefi_start = time.time()
    inputs = HEFIInputs(**agg)
    result = compute_hefi(inputs)
    hefi_time = time.time() - hefi_start
    print(f"\nHEFI computation: {hefi_time:.3f} seconds")
    
    print("\n=== HEFI RESULTS ===")
    print("HEFI total:", result.total_score)
    print("Ratios:", result.ratios)
    print("Components:", result.component_scores)
    
    # Print total time
    total_time = time.time() - total_start
    print(f"\n=== PERFORMANCE SUMMARY ===")
    print(f"Pipeline initialization: {init_time:.3f}s")
    print(f"Food data lookup: {lookup_time:.3f}s")
    print(f"Data aggregation: {agg_time:.3f}s")
    print(f"HEFI computation: {hefi_time:.3f}s")
    print(f"TOTAL TIME: {total_time:.3f} seconds")


def test_subsequent_calculations():
    """Test performance of subsequent calculations after pipeline is loaded"""
    print("\n=== TESTING SUBSEQUENT CALCULATIONS ===")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cnf_dir = os.path.join(base_dir, 'raw_cnf')
    integrator = HEFICNFIntegrator(cnf_dir)  # Should use cached pipeline
    
    # Test different food combinations with amounts
    test_cases = [
        ([(3049, 100.0)], "Single food: Salmon 100g"),
        ([(3725, 75.0)], "Single food: Rice bran bread 75g"),  
        ([(3049, 100.0), (3725, 75.0)], "Two foods: Salmon + Bread"),
        ([(3049, 100.0), (3725, 75.0), (3580, 100.0)], "Three foods: Salmon + Bread + Venison")
    ]
    
    for food_data, description in test_cases:
        start_time = time.time()
        
        agg = integrator.aggregate_inputs(food_data)
        inputs = HEFIInputs(**agg)
        result = compute_hefi(inputs)
        
        calc_time = time.time() - start_time
        print(f"{description}: {calc_time:.3f}s (Score: {result.total_score:.1f}/80)")
        
        # Show key inputs for the combination
        print(f"  Total Foods RA: {agg['total_foods_ra']:.2f}, VF RA: {agg['vf_ra']:.2f}")
        print(f"  Energy: {agg['energy_kcal']:.0f} kcal, Sodium: {agg['sodium_mg']:.0f} mg")


def test_ra_categories():
    """Test the new RA classification system with various food types"""
    print("\n=== TESTING RA CLASSIFICATION SYSTEM ===")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cnf_dir = os.path.join(base_dir, 'raw_cnf')
    integrator = HEFICNFIntegrator(cnf_dir)
    
    # Test foods from different categories
    test_foods = [
        (3049, "Fish/Protein"),      # Salmon
        (3725, "Bread/Grains"),      # Rice bran bread  
        (3580, "Meat/Protein"),      # Venison
        # Add more test foods if available
    ]
    
    print("Food ID | Group | Description | RA Category | RA Amount | Confidence")
    print("-" * 80)
    
    for food_id, expected_category in test_foods:
        try:
            food_rows = integrator._get_food_rows([food_id])
            if not food_rows.empty:
                food_row = food_rows.iloc[0]
                desc = food_row['FoodDescription']
                group_id = int(food_row['FoodGroupID'])
                
                ra_category = integrator._classify_food_to_ra_category(desc, group_id)
                ra_amount = integrator._get_ra_amount(ra_category)
                confidence = 'HIGH' if ra_category != 'default' else 'LOW'
                
                print(f"{food_id:7} | {group_id:5} | {desc[:25]:25} | {ra_category:15} | {ra_amount:9.1f} | {confidence}")
        except Exception as e:
            print(f"{food_id:7} | ERROR: {str(e)}")

if __name__ == '__main__':
    main()
    test_subsequent_calculations()
    test_ra_categories()


