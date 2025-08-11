"""
HENI Factors Configuration
Based on Global Burden of Disease epidemiological evidence and DALY calculations
All values in avoided μDALY/gram as specified in the technical report
"""

# HENI factors for food groups (avoided μDALY/g)
# Positive values indicate health benefits, negative values indicate health detriments
FOOD_GROUP_HENI_FACTORS = {
    # Major beneficial food groups
    "nuts_seeds": 25.0,           # High protective effect
    "whole_grains": 1.7,          # Moderate protective effect  
    "fruits": 2.5,                # Moderate protective effect
    "vegetables": 3.2,            # Moderate protective effect
    "milk": 0.15,                 # Small protective effect (colorectal cancer benefit)
    
    # Detrimental food groups
    "sugar_sweetened_beverages": -2.1,  # Metabolic and cardiovascular risks
    "red_meat": -1.5,                   # Cardiovascular risks
    "processed_meat": -14.2,            # High cardiovascular and cancer risks
}

# HENI factors for nutrients (avoided μDALY/g)
NUTRIENT_HENI_FACTORS = {
    # Beneficial nutrients
    "omega_3": 57.0,              # Highest protective effect (from fish/seafood)
    "calcium": 5.1,               # Bone health and cardiovascular benefits
    "fiber": 1.9,                 # Digestive and cardiovascular benefits  
    "polyunsaturated_fatty_acids": 6.0,  # Cardiovascular benefits
    
    # Detrimental nutrients
    "trans_fat": -44.0,           # High cardiovascular risk
    "sodium": -8.0,               # Cardiovascular and stroke risk
}

# Combined HENI factors lookup table for algorithm use
HENI_FACTORS = {
    **FOOD_GROUP_HENI_FACTORS,
    **NUTRIENT_HENI_FACTORS
}

# Disease burden attribution weights (percentage contribution to total DALY burden)
DISEASE_BURDEN_ATTRIBUTION = {
    "cardiovascular_diseases": 0.65,      # Primary contributor (65%)
    "colorectal_cancer": 0.12,            # Secondary contributor (12%)
    "other_cancers": 0.08,                # Other cancers (8%) 
    "metabolic_disorders": 0.10,          # Diabetes, metabolic syndrome (10%)
    "all_cause_mortality": 0.05,          # Other mortality effects (5%)
}

# Risk factor to disease mapping for detailed attribution
RISK_FACTOR_DISEASE_MAPPING = {
    "omega_3": ["cardiovascular_diseases"],
    "calcium": ["colorectal_cancer", "cardiovascular_diseases"], 
    "fiber": ["colorectal_cancer", "cardiovascular_diseases"],
    "polyunsaturated_fatty_acids": ["cardiovascular_diseases"],
    "trans_fat": ["cardiovascular_diseases"],
    "sodium": ["cardiovascular_diseases"],
    "nuts_seeds": ["cardiovascular_diseases", "all_cause_mortality"],
    "whole_grains": ["cardiovascular_diseases", "metabolic_disorders"],
    "fruits": ["cardiovascular_diseases", "other_cancers"],
    "vegetables": ["cardiovascular_diseases", "other_cancers"],
    "milk": ["colorectal_cancer"],
    "sugar_sweetened_beverages": ["metabolic_disorders", "cardiovascular_diseases"],
    "red_meat": ["colorectal_cancer", "cardiovascular_diseases"],
    "processed_meat": ["colorectal_cancer", "cardiovascular_diseases"],
}

# Effective intake ranges for HENI factor validity (g/day)
# HENI factors are valid within these ranges per the technical report
EFFECTIVE_INTAKE_RANGES = {
    "omega_3": (0.0, 5.0),
    "calcium": (0.0, 2.5),
    "fiber": (0.0, 50.0),
    "polyunsaturated_fatty_acids": (0.0, 30.0),
    "trans_fat": (0.0, 10.0), 
    "sodium": (0.0, 10.0),
    "nuts_seeds": (0.0, 50.0),
    "whole_grains": (0.0, 200.0),
    "fruits": (0.0, 500.0),
    "vegetables": (0.0, 500.0), 
    "milk": (0.0, 500.0),
    "sugar_sweetened_beverages": (0.0, 1000.0),
    "red_meat": (0.0, 200.0),
    "processed_meat": (0.0, 100.0),
}

# Conversion factors for different serving bases
SERVING_CONVERSIONS = {
    "per_100_kcal": "energy_normalized",
    "per_100_grams": "weight_normalized", 
    "per_serving": "portion_based"
}

# Age and gender adjustment factors (simplified - could be expanded)
AGE_GENDER_ADJUSTMENTS = {
    "adult_male": 1.0,      # Base reference
    "adult_female": 0.95,   # Slightly lower impact
    "elderly_male": 1.15,   # Higher susceptibility
    "elderly_female": 1.10, # Higher susceptibility
}