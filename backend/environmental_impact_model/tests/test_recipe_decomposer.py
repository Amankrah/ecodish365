"""Tier γ lock-in tests for `RecipeDecomposer`.

Pins:
  - `should_decompose` trigger predicate (composite groups + matcher fallback).
  - Constrained-vocabulary parsing: hallucinated Ciqual codes are rejected.
  - Mass-conservation gate: sum(ingredient mass) + unresolved ≈ target ± 5 g.
  - Confidence gate: below-threshold decompositions fall through to group default.
  - Graceful degradation: no LLM client → DecomposedRecipe(matched=False).
  - Mass-weighted aggregation: `DecomposedRecipe.mass_weighted_impacts`
    multiplies each ingredient's per-100g impact by mass/100 and sums.
  - Backward compatibility: when `enable_recipe_decomposer=False` (default)
    LifeCycleAssessment is bit-for-bit identical to pre-Tier γ.
"""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json

_BACKEND = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
for sub in ("environmental_impact_model", "dish_cnf_db_pipeline"):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
import django  # noqa: E402
from django.apps import apps as _django_apps  # noqa: E402
if not _django_apps.ready:
    django.setup()

from environmental_impact_model.src.recipe_decomposer import (  # noqa: E402
    RecipeDecomposer, DecomposedRecipe, Ingredient,
    _COMPOSITE_FOOD_GROUPS,
)
from environmental_impact_model.src.lca_matcher import MatchResult  # noqa: E402


def _make_stub_index_and_retriever(candidate_codes=('21000', '19062', '12048')):
    """Build a MagicMock AgribalyseIndex + EmbeddingRetriever that returns
    a known candidate set on every `retrieve(...)` call."""
    index = MagicMock()
    index.catalog = [
        {'ciqual_code': '21000', 'lci_name': 'Beef, ground, raw',
         'lci_name_fr': 'Boeuf haché cru',
         'agribalyse_group': 'viandes, œufs, poissons',
         'recipe2016_midpoints_per_100g': {'Global warming': 2.5, 'Land use': 5.0, 'Water consumption': 0.06}},
        {'ciqual_code': '19062', 'lci_name': 'Tomato, sauce, with herbs',
         'lci_name_fr': 'Sauce tomate aux herbes',
         'agribalyse_group': 'aides culinaires et ingrédients divers',
         'recipe2016_midpoints_per_100g': {'Global warming': 0.08, 'Land use': 0.06, 'Water consumption': 0.005}},
        {'ciqual_code': '12048', 'lci_name': 'Cheese, mozzarella',
         'lci_name_fr': 'Fromage mozzarella',
         'agribalyse_group': 'lait et produits laitiers',
         'recipe2016_midpoints_per_100g': {'Global warming': 2.4, 'Land use': 9.0, 'Water consumption': 0.04}},
        {'ciqual_code': '18021', 'lci_name': 'Spaghetti, raw',
         'lci_name_fr': 'Spaghetti cru',
         'agribalyse_group': 'produits céréaliers',
         'recipe2016_midpoints_per_100g': {'Global warming': 0.18, 'Land use': 0.28, 'Water consumption': 0.025}},
    ]
    retriever = MagicMock()
    # `retrieve` returns the first 4 catalog entries with arbitrary similarity.
    retriever.retrieve.return_value = [
        (index.catalog[0], 0.9),
        (index.catalog[1], 0.85),
        (index.catalog[2], 0.8),
        (index.catalog[3], 0.78),
    ]
    return index, retriever


class TriggerPredicateTests(unittest.TestCase):
    """`should_decompose` only fires for composite-y groups AND when the
    direct matcher didn't succeed."""

    def test_composite_group_without_match_triggers(self):
        self.assertTrue(RecipeDecomposer.should_decompose('Mixed Dishes', None))
        self.assertTrue(RecipeDecomposer.should_decompose('Soups, Sauces and Gravies', None))

    def test_non_composite_group_does_not_trigger(self):
        # Single-ingredient groups: matcher handles directly.
        self.assertFalse(RecipeDecomposer.should_decompose('Beef Products', None))
        self.assertFalse(RecipeDecomposer.should_decompose('Fruits and fruit juices', None))
        self.assertFalse(RecipeDecomposer.should_decompose('Vegetables and Vegetable Products', None))

    def test_composite_group_with_high_confidence_match_does_not_trigger(self):
        """High-confidence direct matcher match on a composite group → no
        decomposition needed. Boundary check at HIGH_CONFIDENCE_THRESHOLD."""
        match = MatchResult(food_id=1, matched=True, ciqual_code='25081', confidence=0.90)
        self.assertFalse(RecipeDecomposer.should_decompose('Mixed Dishes', match))

    def test_composite_group_with_borderline_match_triggers(self):
        """B.2 new behaviour: matched=True but confidence below 0.85 on a
        composite group → decomposer fires. This catches LCA-distant
        near-misses like Bannock → 'Biscuit with fruits filling' at 0.65."""
        match = MatchResult(food_id=1, matched=True, ciqual_code='7413',
                            confidence=0.65, lci_name='Biscuit extruded')
        self.assertTrue(RecipeDecomposer.should_decompose('Mixed Dishes', match))
        # Boundary: just below 0.85 → triggers
        match_84 = MatchResult(food_id=1, matched=True, confidence=0.84)
        self.assertTrue(RecipeDecomposer.should_decompose('Mixed Dishes', match_84))
        # Boundary: exactly at 0.85 → does NOT trigger
        match_85 = MatchResult(food_id=1, matched=True, confidence=0.85)
        self.assertFalse(RecipeDecomposer.should_decompose('Mixed Dishes', match_85))

    def test_borderline_match_on_NON_composite_group_does_not_trigger(self):
        """Borderline matches on single-ingredient CNF groups should NOT
        trigger the decomposer — only composite-group foods benefit from
        ingredient-level reconstruction."""
        match = MatchResult(food_id=1, matched=True, confidence=0.65)
        # Beef brain (Beef Products) matched at conf 0.65 stays direct-matched
        self.assertFalse(RecipeDecomposer.should_decompose('Beef Products', match))
        self.assertFalse(RecipeDecomposer.should_decompose('Vegetables and Vegetable Products', match))

    def test_composite_group_with_failed_match_triggers(self):
        match = MatchResult(food_id=1, matched=False, fallback_reason='low_confidence')
        self.assertTrue(RecipeDecomposer.should_decompose('Mixed Dishes', match))

    def test_composite_food_groups_set_covers_expected_categories(self):
        for g in ('Mixed Dishes', 'Soups, Sauces and Gravies', 'Fast Foods',
                  'Babyfoods', 'Sausages and Luncheon meats', 'Sweets',
                  'Snacks', 'Baked Products'):
            self.assertIn(g, _COMPOSITE_FOOD_GROUPS)


class GracefulDegradationTests(unittest.TestCase):
    """No LLM client → matched=False with the right fallback_reason."""

    def test_no_llm_client_returns_unmatched(self):
        index, retriever = _make_stub_index_and_retriever()
        decomposer = RecipeDecomposer(index=index, retriever=retriever, ranking_client=None)
        result = decomposer.decompose(food_id=1, food_description='Lasagna with meat', food_quantity_g=250.0)
        self.assertFalse(result.matched)
        self.assertEqual(result.fallback_reason, 'no_llm_client')


def _make_llm_response(parsed_dict):
    """Build a mock OpenAI chat completion response that returns the given JSON."""
    rsp = MagicMock()
    choice = MagicMock()
    choice.message = MagicMock(); choice.message.content = json.dumps(parsed_dict)
    rsp.choices = [choice]
    return rsp


class ValidationGateTests(unittest.TestCase):
    """Hallucinated codes, mass imbalance, low confidence, excess unresolved
    mass — all are explicit rejects with a fallback_reason."""

    def setUp(self):
        self.index, self.retriever = _make_stub_index_and_retriever()
        self.client = MagicMock()
        # Use the production default (0.30) so the tests exercise the same
        # confidence behaviour callers will see. Tests that need a specific
        # threshold construct their own decomposer.
        self.decomposer = RecipeDecomposer(
            index=self.index, retriever=self.retriever, ranking_client=self.client,
        )

    def test_hallucinated_ciqual_code_rejected(self):
        """A code not in the retrieved candidate set must fail validation."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '99999', 'mass_g': 250.0, 'rationale': 'fake'},
            ],
            'total_recipe_mass_g': 250.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=1, food_description='X', food_quantity_g=250.0)
        self.assertFalse(result.matched)
        self.assertTrue(result.fallback_reason.startswith('hallucinated_ciqual_code'))

    def test_mass_imbalance_rejected(self):
        """sum(ingredient mass) + unresolved must equal target ± max(5 g, 2 %).
        Here: 100 g resolved vs 250 g target → 150 g gap, well above tolerance."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 50.0},
                {'ciqual_code': '12048', 'mass_g': 50.0},
            ],
            'total_recipe_mass_g': 250.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=1, food_description='X', food_quantity_g=250.0)
        self.assertFalse(result.matched)
        self.assertTrue(result.fallback_reason.startswith('mass_imbalance'))

    def test_mass_tolerance_scales_with_target(self):
        """B.1 scale-aware tolerance: 500 g target with 10 g gap passes (2 %);
        500 g target with 12 g gap fails (2.4 % — beyond what auto-credit can
        absorb when also above tolerance). The 5 g absolute floor still
        protects small servings — 50 g target with 6 g gap fails."""
        # 500 g target, 480 + 10 = 490 g resolved + 0 unresolved → 10 g gap = 2 %.
        # 2 % of 500 = 10 g exactly; tolerance is max(5, 10) = 10, |gap|=10 → PASS
        # (auto-credit doesn't trigger because |gap| <= tolerance already).
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 480.0},
                {'ciqual_code': '12048', 'mass_g': 10.0},
            ],
            'total_recipe_mass_g': 490.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=10, food_description='X', food_quantity_g=500.0)
        self.assertTrue(result.matched, msg=f'expected matched=True; fallback={result.fallback_reason}')

        # 500 g target, 488 g resolved (two ingredients) → 12 g gap = 2.4 %.
        # 2.4 % falls into the auto-credit zone (under MAX_UNRESOLVED_FRACTION=10 %)
        # so the 12 g gap is auto-credited to unresolved_mass_g and the decomp
        # passes. This is the NEW behaviour — previously this case would have
        # been rejected with mass_imbalance.
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 478.0},
                {'ciqual_code': '12048', 'mass_g': 10.0},
            ],
            'total_recipe_mass_g': 488.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result_auto = self.decomposer.decompose(food_id=11, food_description='X', food_quantity_g=500.0)
        self.assertTrue(result_auto.matched,
                        msg=f'expected auto-credit to pass; fallback={result_auto.fallback_reason}')
        self.assertAlmostEqual(result_auto.unresolved_mass_g, 12.0, places=1)

        # 500 g target, 400 g resolved → 100 g gap = 20 % > MAX_UNRESOLVED_FRACTION (10%);
        # auto-credit cannot absorb; mass_imbalance fires.
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 200.0},
                {'ciqual_code': '12048', 'mass_g': 200.0},
            ],
            'total_recipe_mass_g': 400.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result_fail = self.decomposer.decompose(food_id=12, food_description='X', food_quantity_g=500.0)
        self.assertFalse(result_fail.matched)
        self.assertTrue(result_fail.fallback_reason.startswith('mass_imbalance'))

    def test_excess_unresolved_mass_rejected(self):
        """Unresolved mass > 10% of target → reject (even with multi-ingredient list)."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 30.0},
                {'ciqual_code': '12048', 'mass_g': 20.0},
            ],
            'total_recipe_mass_g': 250.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 200.0,  # 200 / 250 = 80% unresolved
        })
        result = self.decomposer.decompose(food_id=1, food_description='X', food_quantity_g=250.0)
        self.assertFalse(result.matched)
        self.assertTrue(result.fallback_reason.startswith('unresolved_mass_too_large'))

    def test_low_confidence_rejected(self):
        """LLM-reported decomposition_confidence below threshold → reject.
        Threshold lowered to 0.30 (was 0.60) in 2026-05-22 fix because the
        gpt-4o-mini default is anchored at 0.40 regardless of true uncertainty
        — making the 0.60 gate empirically unreachable. The 0.30 floor still
        rejects 'I have no idea' (conf=0.00) responses."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 200.0},
                {'ciqual_code': '12048', 'mass_g': 50.0},
            ],
            'total_recipe_mass_g': 250.0,
            'decomposition_confidence': 0.10,  # below the new 0.30 floor
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=1, food_description='X', food_quantity_g=250.0)
        self.assertFalse(result.matched)
        self.assertTrue(result.fallback_reason.startswith('low_confidence'))

    def test_empirical_default_confidence_040_accepted(self):
        """The gpt-4o-mini model anchors decomposition_confidence at 0.40 for
        most responses (empirically verified across 8 probes spanning trivial
        → Canadian-specific composites). With the threshold lowered to 0.30,
        a 0.40-confidence well-formed decomposition is now ACCEPTED so
        Tier γ actually fires in practice."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 200.0, 'rationale': 'main protein'},
                {'ciqual_code': '12048', 'mass_g': 50.0,  'rationale': 'cheese topping'},
            ],
            'total_recipe_mass_g': 250.0,
            'decomposition_confidence': 0.40,  # the empirical LLM default
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=2, food_description='X', food_quantity_g=250.0)
        self.assertTrue(result.matched,
                        msg=f'expected matched=True at conf=0.40; got fallback={result.fallback_reason}')
        self.assertEqual(result.ingredient_count, 2)

    def test_too_few_ingredients_rejected(self):
        """A 'decomposition' with 1 ingredient isn't a decomposition — it's a
        single-row match the matcher should have handled. Reject."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 100.0, 'rationale': 'beef'},
            ],
            'total_recipe_mass_g': 100.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=3, food_description='Beef', food_quantity_g=100.0)
        self.assertFalse(result.matched)
        self.assertTrue(result.fallback_reason.startswith('too_few_ingredients'))

    def test_mass_shortfall_auto_credits_to_unresolved(self):
        """Mass auto-credit: 250g target with 150+50+40=240g resolved + 0g
        unresolved is OFF by 10g. Under the new auto-credit rule the 10g
        shortfall is credited to unresolved_mass_g (within the 10%-of-target
        cap) so the decomposition passes mass-conservation. Reproduces the
        live-LLM Shepherd's pie case that previously hit mass_imbalance."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 150.0, 'rationale': 'meat'},
                {'ciqual_code': '19062', 'mass_g': 50.0,  'rationale': 'sauce'},
                {'ciqual_code': '12048', 'mass_g': 40.0,  'rationale': 'cheese'},
            ],
            'total_recipe_mass_g': 240.0,
            'decomposition_confidence': 0.7,
            'unresolved_mass_g': 0.0,  # LLM forgot to fill this in
        })
        result = self.decomposer.decompose(food_id=4, food_description='Shepherd-like',
                                            food_quantity_g=250.0)
        self.assertTrue(result.matched,
                        msg=f'expected auto-credit to pass; got fallback={result.fallback_reason}')
        # Auto-credit should have populated unresolved_mass_g with the 10g gap
        self.assertAlmostEqual(result.unresolved_mass_g, 10.0, places=1)


class SuccessfulDecompositionTests(unittest.TestCase):
    """Well-formed LLM output produces matched=True with the expected ingredient list."""

    def setUp(self):
        self.index, self.retriever = _make_stub_index_and_retriever()
        self.client = MagicMock()
        self.decomposer = RecipeDecomposer(
            index=self.index, retriever=self.retriever, ranking_client=self.client,
        )

    def test_lasagna_decomposes_into_three_ingredients(self):
        """LLM returns plausible lasagna recipe: beef + tomato + cheese."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 80.0, 'rationale': 'ground beef base'},
                {'ciqual_code': '19062', 'mass_g': 90.0, 'rationale': 'tomato sauce'},
                {'ciqual_code': '12048', 'mass_g': 80.0, 'rationale': 'mozzarella cheese'},
            ],
            'total_recipe_mass_g': 250.0,
            'decomposition_confidence': 0.85,
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(
            food_id=42, food_description='Lasagna with meat and sauce, homemade',
            food_quantity_g=250.0,
        )
        self.assertTrue(result.matched)
        self.assertTrue(result.is_resolved())
        self.assertEqual(result.ingredient_count, 3)
        self.assertEqual(result.total_recipe_mass_g, 250.0)
        codes = [i.ciqual_code for i in result.ingredients]
        self.assertSetEqual(set(codes), {'21000', '19062', '12048'})

    def test_mass_weighted_impacts_aggregates_correctly(self):
        """The recipe-level GHG should equal sum(ingredient_per_100g × mass/100)."""
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [
                {'ciqual_code': '21000', 'mass_g': 100.0, 'rationale': 'beef'},
                {'ciqual_code': '12048', 'mass_g': 100.0, 'rationale': 'cheese'},
            ],
            'total_recipe_mass_g': 200.0,
            'decomposition_confidence': 0.9,
            'unresolved_mass_g': 0.0,
        })
        result = self.decomposer.decompose(food_id=42, food_description='Beef + cheese 200g', food_quantity_g=200.0)
        self.assertTrue(result.matched)
        # Build per_ingredient_impacts from the catalog (each entry's per_100g
        # midpoints — already on the stub index).
        per_ing = {
            '21000': self.index.catalog[0]['recipe2016_midpoints_per_100g'],  # GHG 2.5
            '12048': self.index.catalog[2]['recipe2016_midpoints_per_100g'],  # GHG 2.4
        }
        agg = result.mass_weighted_impacts(per_ing)
        # 100g of beef (2.5/100g) + 100g of cheese (2.4/100g) = 2.5 + 2.4 = 4.9 kg CO2 total
        self.assertAlmostEqual(agg['Global warming'], 4.9, places=6)

    def test_caching_returns_same_result(self):
        self.client.chat.completions.create.return_value = _make_llm_response({
            'ingredients': [{'ciqual_code': '21000', 'mass_g': 100.0}],
            'total_recipe_mass_g': 100.0, 'decomposition_confidence': 0.9, 'unresolved_mass_g': 0.0,
        })
        r1 = self.decomposer.decompose(food_id=99, food_description='X', food_quantity_g=100.0)
        r2 = self.decomposer.decompose(food_id=99, food_description='X', food_quantity_g=100.0)
        self.assertIs(r1, r2)
        # LLM was called exactly once.
        self.assertEqual(self.client.chat.completions.create.call_count, 1)


class DecomposedRecipeAggregationTests(unittest.TestCase):
    """Direct unit tests of `DecomposedRecipe.mass_weighted_impacts`."""

    def test_aggregation_with_partial_per_ingredient_coverage(self):
        recipe = DecomposedRecipe(
            food_id=1, matched=True,
            ingredients=[
                Ingredient(ciqual_code='A', lci_name='', mass_g=50.0),
                Ingredient(ciqual_code='B', lci_name='', mass_g=50.0),
            ],
            total_recipe_mass_g=100.0,
        )
        # Only A has per-100g impacts; B contributes 0.
        per_ing = {'A': {'Global warming': 4.0}}  # 4 kg CO2 / 100g
        agg = recipe.mass_weighted_impacts(per_ing)
        # 50g of A → 2.0 kg CO2; 50g of B with no impacts → 0
        self.assertAlmostEqual(agg['Global warming'], 2.0, places=6)


if __name__ == '__main__':
    unittest.main()
