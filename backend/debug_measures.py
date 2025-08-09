#!/usr/bin/env python3
"""
Debug script to check measure description loading
"""

import os
import sys
import pandas as pd

# Add the project path
sys.path.append('.')

from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator

def debug_measures():
    print("=== Debugging Measure Descriptions ===")
    
    cnf_dir = os.path.join('.', 'raw_cnf')
    integrator = HEFICNFIntegrator(cnf_dir)
    
    food_id = 3049  # Salmon
    
    print(f"Testing Food ID: {food_id}")
    print(f"Conversion factors DF shape: {integrator.conversion_factors_df.shape}")
    print(f"Measure names DF shape: {integrator.measure_names_df.shape}")
    
    # Check conversion factors for this food
    cf_food = integrator.conversion_factors_df[
        integrator.conversion_factors_df['FoodID'] == food_id
    ]
    print(f"\nConversion factors for Food {food_id}:")
    print(cf_food[['MeasureID', 'ConversionFactorValue']].head())
    
    if not cf_food.empty:
        measure_ids = cf_food['MeasureID'].tolist()
        print(f"\nMeasureIDs: {measure_ids}")
        print(f"MeasureID types: {[type(mid) for mid in measure_ids[:3]]}")
        
        # Check measure names
        print(f"\nMeasure names DF columns: {integrator.measure_names_df.columns.tolist()}")
        print(f"Sample MeasureIDs in measure_names: {integrator.measure_names_df['MeasureID'].head().tolist()}")
        print(f"MeasureID types in measure_names: {integrator.measure_names_df['MeasureID'].dtype}")
        
        # Look for these specific MeasureIDs
        for measure_id in measure_ids[:3]:
            matches = integrator.measure_names_df[
                integrator.measure_names_df['MeasureID'] == measure_id
            ]
            print(f"\nLooking for MeasureID {measure_id} (type: {type(measure_id)}):")
            print(f"Found {len(matches)} matches")
            if not matches.empty:
                print(f"Description: '{matches.iloc[0]['MeasureDescription']}'")
        
        # Try manual merge
        print(f"\n=== Manual Merge Test ===")
        try:
            # Ensure same types
            cf_food_copy = cf_food.copy()
            measure_names_copy = integrator.measure_names_df.copy()
            
            print(f"Before conversion - CF MeasureID dtype: {cf_food_copy['MeasureID'].dtype}")
            print(f"Before conversion - MN MeasureID dtype: {measure_names_copy['MeasureID'].dtype}")
            
            cf_food_copy['MeasureID'] = cf_food_copy['MeasureID'].astype(int)
            measure_names_copy['MeasureID'] = measure_names_copy['MeasureID'].astype(int)
            
            print(f"After conversion - CF MeasureID dtype: {cf_food_copy['MeasureID'].dtype}")
            print(f"After conversion - MN MeasureID dtype: {measure_names_copy['MeasureID'].dtype}")
            
            merged = cf_food_copy.merge(
                measure_names_copy[['MeasureID', 'MeasureDescription']], 
                on='MeasureID', 
                how='left'
            )
            
            print(f"Merged result shape: {merged.shape}")
            print("Merged results:")
            for _, row in merged.iterrows():
                desc = row.get('MeasureDescription', 'N/A')
                print(f"  MeasureID {row['MeasureID']}: Factor {row['ConversionFactorValue']}, Desc: '{desc}'")
                
        except Exception as e:
            print(f"Merge error: {e}")
    
    # Test the actual method
    print(f"\n=== Testing actual method ===")
    conversion_factor = integrator._get_best_conversion_factor(food_id)
    measure_desc = integrator.get_measure_description(food_id, conversion_factor)
    
    print(f"Best conversion factor: {conversion_factor}")
    print(f"Measure description: '{measure_desc}'")

if __name__ == '__main__':
    debug_measures()