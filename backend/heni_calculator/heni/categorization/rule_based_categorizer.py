from typing import Dict

class RuleBasedCategorizer:
    @staticmethod
    def categorize(food_group: str, nutrient_data: Dict, food_description: str) -> Dict[str, float]:
        categories = {}
        
        # Food group based categorization
        if "Finfish and Shellfish Products" in food_group:
            categories["seafood"] = 1.0
        if "Nuts and Seeds" in food_group:
            categories["nuts_seeds"] = 1.0
        if "Cereals, Grains and Pasta" in food_group:
            categories["whole_grains"] = 0.5  # Assume half of grains are whole
        if "Legumes and Legume Products" in food_group:
            categories["legumes"] = 1.0
        if "Fruits and fruit juices" in food_group:
            categories["fruits"] = 1.0
        if "Vegetables and Vegetable Products" in food_group:
            categories["vegetables"] = 1.0
        if "Dairy and Egg Products" in food_group:
            categories["milk"] = 1.0
        if "Beverages" in food_group:
            if nutrient_data.get("SUGARS, TOTAL", 0) > 5:
                categories["sugar_sweetened_beverages"] = 1.0
        if any(meat in food_group for meat in ["Beef Products", "Pork Products", "Poultry Products", "Lamb, Veal and Game"]):
            if "processed" in food_description.lower() or "Sausages and Luncheon meats" in food_group:
                categories["processed_meat"] = 1.0
            else:
                categories["red_meat"] = 1.0
        
        # Nutrient based categorization
        if nutrient_data.get("CALCIUM", 0) > 100:
            categories["calcium"] = min(nutrient_data["CALCIUM"] / 1000, 1.0)  # Normalize to a 0-1 scale
        if nutrient_data.get("FATTY ACIDS, SATURATED, TOTAL", 0) > 1:
            categories["saturated_fatty_acids"] = min(nutrient_data["FATTY ACIDS, SATURATED, TOTAL"] / 20, 1.0)
        if nutrient_data.get("FATTY ACIDS, POLYUNSATURATED, TOTAL", 0) > 1:
            categories["polyunsaturated_fatty_acids"] = min(nutrient_data["FATTY ACIDS, POLYUNSATURATED, TOTAL"] / 20, 1.0)
        if nutrient_data.get("FIBRE, TOTAL DIETARY", 0) > 2:
            categories["fiber"] = min(nutrient_data["FIBRE, TOTAL DIETARY"] / 30, 1.0)  # Assuming 30g as max
        if nutrient_data.get("FATTY ACIDS, TRANS, TOTAL", 0) > 0:
            categories["trans_fatty_acids"] = min(nutrient_data["FATTY ACIDS, TRANS, TOTAL"] / 5, 1.0)  # Assuming 5g as max
        if nutrient_data.get("SODIUM", 0) > 50:
            categories["sodium"] = min(nutrient_data["SODIUM"] / 2300, 1.0)  # Based on daily recommended limit
        
        # Additional nutrient checks
        if nutrient_data.get("FATTY ACIDS, POLYUNSATURATED, TOTAL OMEGA  N-3", 0) > 0:
            categories["seafood"] = max(categories.get("seafood", 0), 
                                        min(nutrient_data["FATTY ACIDS, POLYUNSATURATED, TOTAL OMEGA  N-3"] / 3, 1.0))
        
        return categories