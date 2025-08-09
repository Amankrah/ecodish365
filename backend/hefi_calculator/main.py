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

    # Example food IDs
    food_ids = [3049, 3725,3580]
    
    # Time food data lookup
    lookup_start = time.time()
    foods_df = integrator._get_food_rows(food_ids)
    lookup_time = time.time() - lookup_start
    print(f"Food data lookup: {lookup_time:.3f} seconds")
    
    print("\n=== FOODS BEING ANALYZED ===")
    for _, row in foods_df.iterrows():
        print(f"ID {row['FoodID']}: {row['FoodDescription']} (Group: {row['FoodGroupID']})")
    
    # Time conversion factor calculation
    conversion_start = time.time()
    print("\n=== CONVERSION FACTORS ===")
    for food_id in food_ids:
        factor = integrator._get_best_conversion_factor(food_id)
        
        # Get ALL available measures for this food to show options
        if not integrator.conversion_factors_df.empty and not integrator.measure_names_df.empty:
            food_factors = integrator.conversion_factors_df[
                integrator.conversion_factors_df['FoodID'] == food_id
            ].merge(
                integrator.measure_names_df[['MeasureID', 'MeasureDescription']], 
                on='MeasureID', 
                how='left'
            )
            
            # Find the measure that matches our selected factor
            selected_measure_desc = "Unknown measure"
            all_measures = []
            
            for _, row in food_factors.iterrows():
                measure_id = row.get('MeasureID', 'N/A')
                conversion_value = float(row['ConversionFactorValue'])
                measure_desc = integrator.get_measure_description(food_id, conversion_value)
                
                all_measures.append(f"{conversion_value} ({measure_desc})")
                
                # Check if this is the selected measure
                if abs(conversion_value - factor) < 0.001:
                    selected_measure_desc = measure_desc
            
            print(f"ID {food_id}: Selected Factor = {factor} ({selected_measure_desc})")
            print(f"  All available measures: {', '.join(all_measures)}")
        else:
            print(f"ID {food_id}: Factor = {factor} (default - no conversion data)")
    conversion_time = time.time() - conversion_start
    print(f"Conversion factor calculation: {conversion_time:.3f} seconds")

    # Debug: Check whole grain detection
    cereals = foods_df[foods_df['FoodGroupID'].isin(integrator.GROUP_CEREALS_GRAINS_PASTA)]
    if not cereals.empty:
        print("\n=== GRAIN FOODS DETECTED ===")
        whole_keywords = ['WHOLE', 'BROWN', 'BRAN', 'WHEAT GERM', 'OATS']
        for _, row in cereals.iterrows():
            desc_upper = row['FoodDescription'].upper()
            is_whole = any(keyword in desc_upper for keyword in whole_keywords)
            print(f"ID {row['FoodID']}: {row['FoodDescription']} -> Whole grain: {is_whole}")
            print(f"  Keywords found: {[kw for kw in whole_keywords if kw in desc_upper]}")
    
    # Time data aggregation (the main computation)
    agg_start = time.time()
    agg = integrator.aggregate_inputs(food_ids)
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
    print(f"Conversion factors: {conversion_time:.3f}s")
    print(f"Data aggregation: {agg_time:.3f}s")
    print(f"HEFI computation: {hefi_time:.3f}s")
    print(f"TOTAL TIME: {total_time:.3f} seconds")


def test_subsequent_calculations():
    """Test performance of subsequent calculations after pipeline is loaded"""
    print("\n=== TESTING SUBSEQUENT CALCULATIONS ===")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cnf_dir = os.path.join(base_dir, 'raw_cnf')
    integrator = HEFICNFIntegrator(cnf_dir)  # Should use cached pipeline
    
    # Test different food combinations
    test_cases = [
        ([3049], "Single food: Salmon"),
        ([3725], "Single food: Rice bran bread"),  
        ([3049, 3725], "Two foods: Salmon + Bread"),
        ([3049, 3725, 3580], "Three foods: Salmon + Bread + Venison")
    ]
    
    for food_ids, description in test_cases:
        start_time = time.time()
        
        agg = integrator.aggregate_inputs(food_ids)
        inputs = HEFIInputs(**agg)
        result = compute_hefi(inputs)
        
        calc_time = time.time() - start_time
        print(f"{description}: {calc_time:.3f}s (Score: {result.total_score:.1f}/80)")

if __name__ == '__main__':
    main()
    test_subsequent_calculations()


