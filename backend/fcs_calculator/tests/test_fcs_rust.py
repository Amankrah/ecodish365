"""FCS tests: rust_core.fcs integration and golden stability."""

from django.test import TestCase

from fcs.analyzers.food_analyzer import FoodAnalyzer
from fcs.models.enums import AttributeType
from fcs.models.food_item import FoodItem
from fcs.utils.cnf_data_integrator import create_cnf_integrator


class FCSRustIntegrationTests(TestCase):
    """Requires ``rust_core`` + CNF under ``settings.CNF_FOLDER``."""

    def test_attribute_kind_matches_enum(self):
        self.assertEqual(
            FoodAnalyzer.get_attribute_type("vitamin_c"), AttributeType.BENEFICIAL
        )
        self.assertEqual(FoodAnalyzer.get_attribute_type("sodium"), AttributeType.HARMFUL)
        self.assertEqual(
            FoodAnalyzer.get_attribute_type("fiber_to_carbohydrate"), AttributeType.RATIO
        )

    def test_score_attribute_sodium_harmful(self):
        t = FoodAnalyzer.get_attribute_type("sodium")
        s = FoodAnalyzer.score_attribute(100.0, "sodium", t)
        self.assertLess(s, 0)

    def test_analyze_food_id_29_structure_and_range(self):
        food_item = FoodItem("Golden test")
        create_cnf_integrator().extract_nutrients_enhanced([29], food_item)
        result = FoodAnalyzer().analyze_food_item(food_item)

        self.assertIn("fcs", result)
        self.assertIn("original_score", result)
        self.assertIn("nova_category", result)
        self.assertGreaterEqual(result["fcs"], 1.0)
        self.assertLessEqual(result["fcs"], 100.0)

    def test_golden_food_29_scores_stable(self):
        """Golden FCS for food_id 29. Rebaselined 2026-05-28 against the CNF 2026
        edition (food 29 = "Cheese, edam, mini wheel"; the 2015 edition called it
        "Cheese, edam" with different nutrient values). Under CNF 2026 the upstream
        raw score is -4.86, so the Mozaffarian 2021 SI Table S3 rescaling gives
        100 - ((26.1 - (-4.86)) / 36.7) × 99 ≈ 16.49. The methodology is unchanged;
        only the underlying nutrient data moved with the edition upgrade.
        (36.7 is the denominator Mozaffarian publishes verbatim, rounded from
        the derived range 26.1 - (-10.7) = 36.8.)

        Update expected values only when FCS methodology or the CNF edition changes.
        """
        food_item = FoodItem("Golden test")
        create_cnf_integrator().extract_nutrients_enhanced([29], food_item)
        result = FoodAnalyzer().analyze_food_item(food_item)

        self.assertEqual(result["original_score"], -4.86)
        self.assertEqual(result["fcs"], 16.49)
        self.assertEqual(result["nova_category"], "PROCESSED_FOODS")

    def test_multi_food_wafct_combo_not_inflated_to_100(self):
        """Regression: equal 100 g portions must not OR-stack ingredient flags to FCS 100."""
        combo_ids = [700153, 700479, 3005, 700532, 2402, 423]
        amounts = [100.0] * len(combo_ids)
        food_item = FoodItem("WAFCT combo regression")
        create_cnf_integrator().extract_nutrients_enhanced(
            combo_ids, food_item, amounts_g=amounts,
        )
        result = FoodAnalyzer().analyze_food_item(food_item)

        self.assertLess(result["fcs"], 85.0)
        self.assertGreater(result["fcs"], 40.0)
        flags = food_item.attributes["food_ingredients"]
        self.assertLess(flags["vegetable"], 50.0)
        self.assertLess(flags["seafood"], 50.0)
        self.assertGreater(flags["plant_oils"], 30.0)
