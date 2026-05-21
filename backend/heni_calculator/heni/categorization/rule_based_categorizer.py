from typing import Dict
import logging

logger = logging.getLogger(__name__)


# Plant-based "milks" excluded from the dairy-milk DRF (GBD 2017 definition
# p. 1960). Detection by description substring.
_PLANT_MILK_INDICATORS = (
    "soy milk", "soy beverage", "almond milk", "almond beverage",
    "oat milk", "oat beverage", "rice milk", "rice beverage",
    "coconut milk", "coconut beverage", "cashew milk", "cashew beverage",
    "hemp milk", "hemp beverage", "pea milk", "pea beverage",
    "plant-based milk", "plant based milk",
)

# Non-SSB beverages excluded from the sugar_sweetened_beverages DRF
# (GBD 2017 definition: excludes 100 % fruit/veg juice; water/tea/coffee
# are not energy-bearing beverages).
_NON_SSB_INDICATORS = (
    "water", "tea", "coffee", "espresso", "broth", "stock", "bouillon",
    "100% juice", "100 % juice", "fruit juice", "vegetable juice",
)


class RuleBasedCategorizer:
    @staticmethod
    def categorize_heni_factors(food_group: str, nutrient_data: Dict, food_description: str) -> Dict[str, float]:
        """
        Rule-based confidence-score categorisation for HENI risk factors.

        Output is a dict ``{factor_name: confidence ∈ [0, 1]}``. Final per-meal
        gram amounts are computed in `heni_calculator_methods.py`; this
        function only emits coarse confidence scores used by the LLM
        categorizer to decide where it needs to augment.

        Implements the GBD 2017 definitional exclusions (plant-based "milks",
        non-SSB beverages) so the LLM fallback sees a clean baseline.
        """
        categories: Dict[str, float] = {}
        desc_lower = food_description.lower()

        # ------------------------------------------------------------------
        # Food-group factors (Stylianou 2021 Results pp. 617-618)
        # ------------------------------------------------------------------

        # Nuts and Seeds
        if "Nuts and Seeds" in food_group:
            categories["nuts_seeds"] = 1.0
        elif any(nut in desc_lower for nut in ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'peanut', 'seed']):
            categories["nuts_seeds"] = 0.8

        # Whole Grains (GBD 2017 definition: bran/germ/endosperm in natural
        # proportion. Refined grains are not counted.)
        if "Cereals, Grains and Pasta" in food_group:
            if any(whole in desc_lower for whole in ['whole', 'brown', 'bran', 'wheat germ', 'quinoa', 'oats']):
                categories["whole_grains"] = 1.0
            else:
                categories["whole_grains"] = 0.2  # most grains are refined; LLM may refine

        # Fruits (excludes fruit juices, salted/pickled per GBD 2017)
        if "Fruits and fruit juices" in food_group:
            # Juices are excluded from the fruits DRF; check for juice keyword.
            if "juice" in desc_lower:
                # 100% fruit juice: not an SSB but also not a fruit DRF target.
                pass
            else:
                categories["fruits"] = 1.0
        elif any(fruit in desc_lower for fruit in ['apple', 'banana', 'berry', 'orange', 'grape']):
            categories["fruits"] = 0.9

        # Vegetables (excludes legumes, salted/pickled, juices, starchy veg
        # per GBD 2017 — potatoes/corn handled below)
        if "Vegetables and Vegetable Products" in food_group:
            categories["vegetables"] = 1.0
        elif any(veg in desc_lower for veg in ['broccoli', 'spinach', 'carrot', 'tomato', 'pepper']):
            categories["vegetables"] = 0.9

        # Legumes (new in Stylianou-aligned 16-component schema)
        if "Legumes and Legume Products" in food_group:
            categories["legumes"] = 1.0
        elif any(leg in desc_lower for leg in [
            "lentil", "chickpea", "bean", "soybean", "edamame", "kidney bean",
            "black bean", "pinto bean", "navy bean", "split pea", "tofu", "tempeh",
        ]):
            categories["legumes"] = 0.8

        # Milk/Dairy (excludes soy milk and plant derivatives per GBD 2017
        # definition p. 1960)
        is_plant_milk = any(ind in desc_lower for ind in _PLANT_MILK_INDICATORS)
        if not is_plant_milk:
            if "Dairy and Egg Products" in food_group or "Milk Products" in food_group:
                categories["milk"] = 1.0
            elif any(dairy in desc_lower for dairy in ['milk', 'yogurt', 'cheese', 'dairy']):
                categories["milk"] = 0.9

        # Sugar-Sweetened Beverages (GBD 2017: ≥ 50 kcal per 226.8 g serving,
        # excludes 100% fruit/veg juice, water, tea, coffee)
        if "Beverages" in food_group:
            is_non_ssb = any(ind in desc_lower for ind in _NON_SSB_INDICATORS)
            if not is_non_ssb:
                sugar_content = nutrient_data.get("SUGARS, TOTAL", 0)
                if sugar_content > 5:  # > 5 g sugar per 100 g
                    if any(ssb in desc_lower for ssb in ['soda', 'cola', 'soft drink', 'sweetened', 'punch']):
                        categories["sugar_sweetened_beverages"] = 1.0
                    else:
                        categories["sugar_sweetened_beverages"] = 0.7

        # Red Meat vs Processed Meat (critical distinction per Stylianou —
        # separate DRFs with different magnitudes)
        meat_groups = ["Beef Products", "Pork Products", "Lamb, Veal and Game"]
        if any(meat in food_group for meat in meat_groups):
            processed_indicators = [
                'sausage', 'bacon', 'ham', 'deli', 'lunch', 'hot dog', 'bologna',
                'salami', 'pepperoni', 'jerky', 'cured', 'smoked', 'processed'
            ]
            if any(proc in desc_lower for proc in processed_indicators):
                categories["processed_meat"] = 1.0
            else:
                categories["red_meat"] = 1.0
        elif "Poultry Products" in food_group:
            # Poultry is health-neutral in HENI; only flag processed cuts.
            if any(proc in desc_lower for proc in ['sausage', 'deli', 'processed', 'bacon', 'ham']):
                categories["processed_meat"] = 0.8

        # ------------------------------------------------------------------
        # Nutrient factors (Stylianou 2021 Results pp. 617-618)
        # ------------------------------------------------------------------

        # Omega-3 (EPA + DHA from seafood per Stylianou; ALA is technically
        # PUFA in GBD 2017 — kept here for backwards compatibility with the
        # CNF nutrient mapping which sums all listed omega-3 forms.)
        omega_3_total = 0
        for omega_3_nutrient in [
            'FATTY ACIDS, POLYUNSATURATED, 22:6 N-3, DOCOSAHEXAENOIC (DHA)',
            'FATTY ACIDS, POLYUNSATURATED, 20:5 N-3, EICOSAPENTAENOIC (EPA)',
            'FATTY ACIDS, POLYUNSATURATED, 18:3UNDIFFERENTIATED, LINOLENIC, OCTADECATRIENOIC',
        ]:
            omega_3_total += nutrient_data.get(omega_3_nutrient, 0)
        if omega_3_total > 0.1:
            categories["omega_3"] = min(omega_3_total / 2.0, 1.0)

        # Calcium (mg → g, threshold > 200 mg)
        calcium_mg = nutrient_data.get("CALCIUM", 0)
        if calcium_mg > 200:
            categories["calcium"] = min(calcium_mg / 1000, 1.0)

        # Fibre: split by source per Stylianou SI §S2.9. The categorizer
        # tags fibre with a source qualifier here; the methods layer respects
        # this routing or, if absent, decides at meal-aggregation time.
        fiber_g = nutrient_data.get("FIBRE, TOTAL DIETARY", 0)
        if fiber_g > 3:
            confidence = min(fiber_g / 25, 1.0)
            # Route based on whether this ingredient is itself f/v/l/w.
            is_fvlw = any(k in categories for k in ("fruits", "vegetables", "legumes", "whole_grains"))
            if is_fvlw:
                categories["fiber_fvlw"] = confidence
            else:
                categories["fiber_other"] = confidence

        # Polyunsaturated Fatty Acids (g, threshold > 2 g)
        pufa_g = nutrient_data.get("FATTY ACIDS, POLYUNSATURATED, TOTAL", 0)
        if pufa_g > 2:
            categories["polyunsaturated_fatty_acids"] = min(pufa_g / 15, 1.0)

        # Trans Fat (g, any amount above noise floor matters; > 0.1 g)
        trans_fat_g = nutrient_data.get("FATTY ACIDS, TRANS, TOTAL", 0)
        if trans_fat_g > 0.1:
            categories["trans_fat"] = min(trans_fat_g / 2, 1.0)

        # Sodium (mg → g, threshold > 400 mg)
        sodium_mg = nutrient_data.get("SODIUM", 0)
        if sodium_mg > 400:
            categories["sodium"] = min(sodium_mg / 2300, 1.0)

        logger.debug(
            f"Rule-based categorization for '{food_description[:30]}...': "
            f"{len(categories)} factors identified"
        )
        return categories

    @staticmethod
    def categorize(food_group: str, nutrient_data: Dict, food_description: str) -> Dict[str, float]:
        """Legacy method for backward compatibility."""
        return RuleBasedCategorizer.categorize_heni_factors(food_group, nutrient_data, food_description)
