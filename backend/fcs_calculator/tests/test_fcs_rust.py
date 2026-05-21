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
        """Golden FCS for food_id 29. Recomputed 2026-05-21 under FCS-CODE-1
        (Mozaffarian 2021 SI Table S3 rescaling). Pre-audit value was 48.41
        under the incorrect [-70, +70] linear stretch; the new value is the
        Mozaffarian formula applied to the same upstream raw score (-2.96):
        100 - ((26.1 - (-2.96)) / 36.7) × 99 ≈ 21.60.
        (36.7 is the denominator Mozaffarian publishes verbatim, rounded from
        the derived range 26.1 - (-10.7) = 36.8.)

        Update expected values only when FCS methodology intentionally changes.
        """
        food_item = FoodItem("Golden test")
        create_cnf_integrator().extract_nutrients_enhanced([29], food_item)
        result = FoodAnalyzer().analyze_food_item(food_item)

        self.assertEqual(result["original_score"], -2.96)
        self.assertEqual(result["fcs"], 21.61)
        self.assertEqual(result["nova_category"], "PROCESSED_FOODS")
