"""Tests for the HENI categorizer's S1 instrumentation (GROUP-D-RECONCILIATION
Step 7): provider routing + categorize_food_with_audit method.

Verifies the new `provider` arg accepts openai/anthropic/gemini and routes
correctly via lazy imports, and that the audit dict returned by
`categorize_food_with_audit` matches the documented schema.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from heni_calculator.heni.categorization.llm_categorizer import LLMFoodCategorizer


def _make_mock_cnf_integrator(
    description="Beef, ground, raw, 80% lean",
    food_group="Beef Products",
    nutrient_data=None,
):
    integrator = MagicMock()
    integrator.get_food_description.return_value = description
    integrator.get_food_group.return_value = food_group
    integrator.get_nutrient_data.return_value = nutrient_data or {
        "PROTEIN": 17.0,
        "FAT (TOTAL LIPIDS)": 20.0,
        "SUGARS, TOTAL": 0.0,
        "CALCIUM": 18.0,
        "SODIUM": 66.0,
    }
    return integrator


class ProviderRoutingTests(unittest.TestCase):
    def test_provider_openai_default(self):
        cat = LLMFoodCategorizer(
            cnf_integrator=_make_mock_cnf_integrator(),
            api_key="sk-test",
        )
        self.assertEqual(cat.provider, "openai")
        self.assertEqual(cat.model, "gpt-4o-mini")

    def test_provider_unknown_raises(self):
        with self.assertRaises(ValueError) as ctx:
            LLMFoodCategorizer(
                cnf_integrator=_make_mock_cnf_integrator(),
                api_key="x", provider="invalid",
            )
        self.assertIn("Unknown provider", str(ctx.exception))

    def test_model_override(self):
        cat = LLMFoodCategorizer(
            cnf_integrator=_make_mock_cnf_integrator(),
            api_key="sk-test", model="gpt-4o",
        )
        self.assertEqual(cat.model, "gpt-4o")

    def test_anthropic_lazy_import_missing(self):
        """If anthropic is not installed, a clear ImportError must be raised."""
        # Simulate the missing dep by hiding it from importlib briefly.
        import sys
        original = sys.modules.pop("anthropic", None)
        # Block re-import by inserting None
        sys.modules["anthropic"] = None  # type: ignore[assignment]
        try:
            with self.assertRaises(ImportError) as ctx:
                LLMFoodCategorizer(
                    cnf_integrator=_make_mock_cnf_integrator(),
                    api_key="x", provider="anthropic",
                )
            self.assertIn("anthropic", str(ctx.exception))
            self.assertIn("pip install", str(ctx.exception))
        finally:
            # Restore module state
            if original is not None:
                sys.modules["anthropic"] = original
            else:
                sys.modules.pop("anthropic", None)


class CategorizeFoodWithAuditTests(unittest.TestCase):
    """Verify the audit-dict schema returned by categorize_food_with_audit()."""

    AUDIT_KEYS = {
        "food_id", "rule_confidence_per_factor", "llm_invoked", "llm_provider",
        "llm_model", "llm_factors_queried", "llm_response_raw",
        "merge_strategy", "final_scores",
    }

    def test_audit_dict_shape_rule_only(self):
        # Use a clear food (beef → confident rule output) so LLM is not invoked.
        cat = LLMFoodCategorizer(
            cnf_integrator=_make_mock_cnf_integrator(),
            api_key=None,  # no client → LLM cannot run regardless
        )
        scores, audit = cat.categorize_food_with_audit(food_id=42)
        self.assertEqual(set(audit.keys()), self.AUDIT_KEYS)
        self.assertEqual(audit["food_id"], 42)
        self.assertFalse(audit["llm_invoked"])
        self.assertIsNone(audit["llm_provider"])
        self.assertEqual(audit["llm_factors_queried"], [])
        self.assertEqual(audit["merge_strategy"], "rule_only")
        self.assertIsInstance(audit["final_scores"], dict)
        # final_scores in audit must equal what the public API returns.
        self.assertEqual(audit["final_scores"], scores)

    def test_audit_records_provider_when_llm_invoked(self):
        # Force the categorizer to want an LLM call by stubbing _should_use_llm
        # to True and providing a mock OpenAI client.
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(
            content='{"red_meat": 0.9, "processed_meat": 0.1}'
        ))]
        mock_client.chat.completions.create.return_value = mock_response

        cat = LLMFoodCategorizer(
            cnf_integrator=_make_mock_cnf_integrator(
                description="something obscure and ambiguous mixed prepared",
            ),
            api_key="sk-test",
        )
        cat.client = mock_client  # inject our mock past the real openai.OpenAI()

        scores, audit = cat.categorize_food_with_audit(food_id=123)
        self.assertTrue(audit["llm_invoked"])
        self.assertEqual(audit["llm_provider"], "openai")
        self.assertEqual(audit["llm_model"], "gpt-4o-mini")
        self.assertIsNotNone(audit["llm_response_raw"])
        self.assertEqual(audit["merge_strategy"], "llm_fills_gaps")

    def test_categorize_food_signature_unchanged(self):
        """Public categorize_food() must still return Dict[str, float] only —
        no audit leak into the existing callers."""
        cat = LLMFoodCategorizer(
            cnf_integrator=_make_mock_cnf_integrator(),
            api_key=None,
        )
        result = cat.categorize_food(food_id=7)
        self.assertIsInstance(result, dict)
        for value in result.values():
            self.assertIsInstance(value, float)


if __name__ == "__main__":
    unittest.main()
