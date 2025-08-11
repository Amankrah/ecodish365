from typing import Dict
import logging

logger = logging.getLogger(__name__)

class RuleBasedCategorizer:
    @staticmethod
    def categorize_heni_factors(food_group: str, nutrient_data: Dict, food_description: str) -> Dict[str, float]:
        """Efficient rule-based categorization for HENI risk factors."""
        categories = {}
        desc_lower = food_description.lower()
        
        # HENI Food Group Risk Factors (high confidence rules)
        
        # Nuts and Seeds
        if "Nuts and Seeds" in food_group:
            categories["nuts_seeds"] = 1.0
        elif any(nut in desc_lower for nut in ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'peanut', 'seed']):
            categories["nuts_seeds"] = 0.8
        
        # Whole Grains (refined detection)
        if "Cereals, Grains and Pasta" in food_group:
            if any(whole in desc_lower for whole in ['whole', 'brown', 'bran', 'wheat germ', 'quinoa', 'oats']):
                categories["whole_grains"] = 1.0
            else:
                categories["whole_grains"] = 0.2  # Most grains are refined
        
        # Fruits
        if "Fruits and fruit juices" in food_group:
            categories["fruits"] = 1.0
        elif any(fruit in desc_lower for fruit in ['apple', 'banana', 'berry', 'orange', 'grape']):
            categories["fruits"] = 0.9
        
        # Vegetables 
        if "Vegetables and Vegetable Products" in food_group:
            categories["vegetables"] = 1.0
        elif any(veg in desc_lower for veg in ['broccoli', 'spinach', 'carrot', 'tomato', 'pepper']):
            categories["vegetables"] = 0.9
        
        # Milk/Dairy
        if "Dairy and Egg Products" in food_group or "Milk Products" in food_group:
            categories["milk"] = 1.0
        elif any(dairy in desc_lower for dairy in ['milk', 'yogurt', 'cheese', 'dairy']):
            categories["milk"] = 0.9
        
        # Sugar-Sweetened Beverages (precise detection)
        if "Beverages" in food_group:
            sugar_content = nutrient_data.get("SUGARS, TOTAL", 0)
            if sugar_content > 5:  # >5g sugar per 100g
                if any(ssb in desc_lower for ssb in ['soda', 'cola', 'soft drink', 'sweetened', 'punch']):
                    categories["sugar_sweetened_beverages"] = 1.0
                else:
                    categories["sugar_sweetened_beverages"] = 0.7
        
        # Red Meat vs Processed Meat (critical distinction)
        meat_groups = ["Beef Products", "Pork Products", "Lamb, Veal and Game"]
        if any(meat in food_group for meat in meat_groups):
            # Processed meat indicators
            processed_indicators = [
                'sausage', 'bacon', 'ham', 'deli', 'lunch', 'hot dog', 'bologna', 
                'salami', 'pepperoni', 'jerky', 'cured', 'smoked', 'processed'
            ]
            if any(proc in desc_lower for proc in processed_indicators):
                categories["processed_meat"] = 1.0
            else:
                categories["red_meat"] = 1.0
        elif "Poultry Products" in food_group:
            # Most poultry is not red meat in HENI context, but check for processing
            if any(proc in desc_lower for proc in ['sausage', 'deli', 'processed']):
                categories["processed_meat"] = 0.8
        
        # HENI Nutrient Risk Factors (evidence-based thresholds)
        
        # Omega-3 (EPA + DHA from fish, ALA from plants)
        omega_3_total = 0
        for omega_3_nutrient in [
            'FATTY ACIDS, POLYUNSATURATED, 22:6 N-3, DOCOSAHEXAENOIC (DHA)',
            'FATTY ACIDS, POLYUNSATURATED, 20:5 N-3, EICOSAPENTAENOIC (EPA)',
            'FATTY ACIDS, POLYUNSATURATED, 18:3UNDIFFERENTIATED, LINOLENIC, OCTADECATRIENOIC'
        ]:
            omega_3_total += nutrient_data.get(omega_3_nutrient, 0)
        
        if omega_3_total > 0.1:  # Significant omega-3 content
            categories["omega_3"] = min(omega_3_total / 2.0, 1.0)  # Scale to 0-1
        
        # Calcium (mg to g conversion, threshold >200mg)
        calcium_mg = nutrient_data.get("CALCIUM", 0)
        if calcium_mg > 200:
            categories["calcium"] = min(calcium_mg / 1000, 1.0)  # Convert mg to g, cap at 1.0
        
        # Fiber (g, threshold >3g)
        fiber_g = nutrient_data.get("FIBRE, TOTAL DIETARY", 0)
        if fiber_g > 3:
            categories["fiber"] = min(fiber_g / 25, 1.0)  # Scale with 25g as reference
        
        # Polyunsaturated Fatty Acids (g, threshold >2g)
        pufa_g = nutrient_data.get("FATTY ACIDS, POLYUNSATURATED, TOTAL", 0)
        if pufa_g > 2:
            categories["polyunsaturated_fatty_acids"] = min(pufa_g / 15, 1.0)
        
        # Trans Fat (g, any amount is concerning)
        trans_fat_g = nutrient_data.get("FATTY ACIDS, TRANS, TOTAL", 0)
        if trans_fat_g > 0.1:  # Even small amounts matter
            categories["trans_fat"] = min(trans_fat_g / 2, 1.0)  # 2g as severe level
        
        # Sodium (mg to g conversion, threshold >400mg)
        sodium_mg = nutrient_data.get("SODIUM", 0)
        if sodium_mg > 400:
            categories["sodium"] = min(sodium_mg / 2300, 1.0)  # Daily limit as reference
        
        logger.debug(f"Rule-based categorization for '{food_description[:30]}...': {len(categories)} factors identified")
        
        return categories
    
    @staticmethod
    def categorize(food_group: str, nutrient_data: Dict, food_description: str) -> Dict[str, float]:
        """Legacy method for backward compatibility."""
        return RuleBasedCategorizer.categorize_heni_factors(food_group, nutrient_data, food_description)