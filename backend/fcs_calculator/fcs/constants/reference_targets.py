# FCS 2.0 Reference Targets - Updated to align with technical specifications
# Based on 25% of DRI for nutrients with established requirements, or 95th percentile for others
REFERENCE_TARGETS = {
    # Domain 1: Nutrient Ratios (log-linear scaling from 5th to 95th percentile)
    'unsaturated_to_saturated_fat': (0.5, 4.5),
    'fiber_to_carbohydrate': (0.01, 0.35),
    'potassium_to_sodium': (0.8, 8.0),
    
    # Domain 2: Vitamins (25% DRI for maximum points)
    'vitamin_a': (0, 225),  # 25% of 900 μg RAE
    'vitamin_b1': (0, 0.3),  # 25% of 1.2 mg
    'vitamin_b2': (0, 0.325),  # 25% of 1.3 mg
    'vitamin_b3': (0, 4.0),  # 25% of 16 mg
    'vitamin_b6': (0, 0.325),  # 25% of 1.3 mg
    'vitamin_b9': (0, 100),  # 25% of 400 μg DFE
    'vitamin_b12': (0, 0.6),  # 25% of 2.4 μg
    'vitamin_c': (0, 22.5),  # 25% of 90 mg
    'vitamin_d': (0, 3.75),  # 25% of 15 μg
    'vitamin_e': (0, 3.75),  # 25% of 15 mg
    'vitamin_k': (0, 30),  # 25% of 120 μg
    
    # Domain 3: Minerals (25% DRI for maximum points)
    'calcium': (0, 250),  # 25% of 1000 mg
    'phosphorus': (0, 175),  # 25% of 700 mg
    'magnesium': (0, 100),  # 25% of 400 mg
    'iron': (0, 4.5),  # 25% of 18 mg
    'zinc': (0, 2.75),  # 25% of 11 mg
    'copper': (0, 0.225),  # 25% of 0.9 mg
    'selenium': (0, 13.75),  # 25% of 55 μg
    'manganese': (0, 0.575),  # 25% of 2.3 mg
    'chromium': (0, 8.75),  # 25% of 35 μg
    'molybdenum': (0, 11.25),  # 25% of 45 μg
    'sodium': (0, 575),  # 25% of 2300 mg (harmful, negative scoring)
    'potassium': (0, 875),  # 25% of 3500 mg
    
    # Domain 4: Food-based Ingredients (percentage-based)
    'fruit': (0, 100),
    'vegetable': (0, 100),
    'beans': (0, 100),
    'whole_grains': (0, 100),
    'nuts': (0, 100),
    'seafood': (0, 100),
    'yogurt': (0, 100),
    'plant_oils': (0, 100),
    'refined_grains': (0, 100),
    'red_or_processed_meat': (0, 100),
    'added_sugar': (0, 25),  # Updated per FCS 2.0 - moved from additives
    
    # Domain 5: Additives (harmful attributes)
    'nitrites': (0, 10),
    'artificial_sweeteners': (0, 10),
    'partially_hydrated_oils': (0, 10),
    'hydrogenated_oils': (0, 10),
    'high_fructose_corn_syrup': (0, 10),
    'monosodium_glutamate': (0, 10),
    'artificial_colors': (0, 10),
    'preservatives': (0, 10),
    
    # Domain 6: Processing Characteristics (binary and continuous)
    'nova_processing': (-10, 0),  # NOVA classification scoring: -10 (ultra-processed) to 0 (unprocessed)
    'fermentation': (0, 100),
    'frying': (0, 100),
    'minimal_processing': (0, 100),  # Positive scoring for minimally processed
    'pasteurization': (0, 100),
    'smoking': (0, 100),
    'canning': (0, 100),
    
    # Domain 7: Specific Lipids (half weight)
    'cholesterol': (0, 75),  # 25% of 300 mg limit
    'mcfas': (0, 2.5),  # Medium-chain fatty acids
    'alpha_linolenic_acid': (0, 0.4),  # 25% of 1.6g
    'epa_dha': (0, 0.25),  # 25% of 1g recommended
    'transfat': (0, 0.5),  # Harmful, negative scoring
    'oleic_acid': (0, 5.0),  # Beneficial monounsaturated
    'linoleic_acid': (0, 3.5),  # Essential fatty acid
    'total_fat': (0, 20),  # Reference for total fat content
    'saturated_fat': (0, 5),  # Harmful saturated fat (negative scoring)
    'monounsaturated_fat': (0, 10),  # Beneficial monounsaturated fat
    'polyunsaturated_fat': (0, 7),  # Beneficial polyunsaturated fat
    
    # Domain 8: Fiber and Protein (half weight)
    'fiber': (0, 6.25),  # 25% of 25g
    'protein': (0, 12.5),  # 25% of 50g
    'amino_acid_score': (0, 1.0),  # Protein quality score
    'total_carbohydrate': (0, 32.5),  # 25% of 130g
    'total_sugars': (0, 12.5),  # Harmful - added sugars penalty
    
    # Domain 9: Phytochemicals (half weight, 95th percentile targets)
    'total_flavonoids': (0, 150),  # mg per 100 kcal
    'total_carotenoids': (0, 2.5),  # mg per 100 kcal
    'anthocyanins': (0, 50),  # mg per 100 kcal
    'isoflavones': (0, 25),  # mg per 100 kcal
    'proanthocyanidins': (0, 75),  # mg per 100 kcal
    'lignans': (0, 10),  # mg per 100 kcal
    'choline': (0, 125),  # 25% of 500mg adequate intake
    'betaine': (0, 75)  # Beneficial compound target
}