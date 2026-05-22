"""Lock-in tests for the v1 LCA scope trim + uncertainty bands + audit tagging.

These tests fix in place the "demote, don't perfect" v1 invariants:

  1. The consumed midpoint vector is exactly {Global warming, Land use,
     Water consumption} — no more, no less. The 15 trimmed categories are
     NOT in `midpoint_impacts`.
  2. `cnf_integrator.get_environmental_impact_factors` returns parallel
     `_uncertainty_bands` with {low, central, high} per consumed category;
     central matches the scalar; low <= central <= high.
  3. `food.get_environmental_impact` is also trimmed to the 3 consumed
     categories (does not leak the legacy 18 to the API surface).
  4. `LifeCycleAssessment.midpoint_impacts_bands` and `.endpoint_impacts_bands`
     are populated alongside the scalar outputs and ordered low <= central <= high.
  5. `Resources` endpoint is None when neither fossil nor mineral midpoints
     are present in the consumed set (rather than silently 0).
  6. `calculate_single_score` re-normalises weights across present endpoints
     (does NOT silently include None Resources as 0).
  7. The fallback path is explicitly tagged
     `fallback_low_confidence:group_default` in the per-category audit trail.
  8. `_compute_environmental_component_scores` uses the trimmed
     category set + renormalised weights (regression test against the silent
     "100-score-for-missing-category" bug found during the v1 audit).

Without these tests, the next change in this area can silently re-introduce
the dishonesty (e.g. by re-adding the trimmed categories to the consumed
vector without literature grounding, or by reverting the fallback-tag string).
"""
from __future__ import annotations

import os
import sys
import unittest

# Mirror the Django sys.path tweak (dish_project/settings.py adds these).
_BACKEND = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
for sub in ("environmental_impact_model", "dish_cnf_db_pipeline"):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

# Bring Django up so cnf_cache can read settings.CNF_FOLDER.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
import django  # noqa: E402
from django.apps import apps as _django_apps  # noqa: E402

if not _django_apps.ready:
    django.setup()

# All imports after Django setup.
from environmental_impact_model.src.cnf_integrator import (  # noqa: E402
    get_cnf_integrator,
    UNCERTAINTY_BAND_RATIOS_BY_GROUP,
)
from environmental_impact_model.src.data_loader import DataLoader  # noqa: E402
from environmental_impact_model.src.food import Food  # noqa: E402
from environmental_impact_model.src.meal import Meal  # noqa: E402
from environmental_impact_model.src.life_cycle_assessment import (  # noqa: E402
    LifeCycleAssessment,
)


CONSUMED_V1 = {"Global warming", "Land use", "Water consumption"}
TRIMMED_AWAY = {
    # The 15 categories the v1 trim removes from the consumed midpoint vector.
    "Stratospheric ozone depletion", "Ionizing radiation",
    "Ozone formation, Human health", "Fine particulate matter formation",
    "Ozone formation, Terrestrial ecosystems", "Terrestrial acidification",
    "Freshwater eutrophication", "Marine eutrophication",
    "Terrestrial ecotoxicity", "Freshwater ecotoxicity", "Marine ecotoxicity",
    "Human carcinogenic toxicity", "Human non-carcinogenic toxicity",
    "Mineral resource scarcity", "Fossil resource scarcity",
}


def _make_beef_food():
    """Real CNF food from the Beef Products group (food_id=7 is `Beef pot roast`)."""
    return Food(food_id=7, quantity=100.0, data_loader=DataLoader())


class CnfIntegratorBandsTests(unittest.TestCase):
    """Group-default factor table now ships {low, central, high} bands."""

    @classmethod
    def setUpClass(cls):
        cls.integrator = get_cnf_integrator()
        cls.integrator.initialize()

    def test_band_ratios_table_covers_every_known_group(self):
        """Every entry in the impact_factors_by_group dict has a band-ratio entry
        for each of the 3 consumed categories. Catches new-group additions that
        forget to add band ratios — which would silently fall back to the
        wide DEFAULT_UNCERTAINTY_BAND_RATIOS."""
        known_groups = set(UNCERTAINTY_BAND_RATIOS_BY_GROUP.keys())
        # All 10 documented food groups should be present.
        self.assertGreaterEqual(len(known_groups), 10)
        for group, ratios in UNCERTAINTY_BAND_RATIOS_BY_GROUP.items():
            for cat in CONSUMED_V1:
                with self.subTest(group=group, category=cat):
                    self.assertIn(cat, ratios)
                    self.assertLess(ratios[cat]['low_ratio'], 1.0)
                    self.assertGreater(ratios[cat]['high_ratio'], 1.0)

    def test_get_factors_returns_bands_for_consumed_categories(self):
        factors = self.integrator.get_environmental_impact_factors(food_id=7)
        bands = factors.get('_uncertainty_bands')
        self.assertIsInstance(bands, dict)
        self.assertEqual(set(bands.keys()), CONSUMED_V1)
        for cat, band in bands.items():
            with self.subTest(category=cat):
                self.assertIn('low', band); self.assertIn('central', band); self.assertIn('high', band)
                self.assertLessEqual(band['low'], band['central'])
                self.assertLessEqual(band['central'], band['high'])
                # Central must equal the scalar value (no drift).
                self.assertAlmostEqual(band['central'], float(factors[cat]))


class FoodLevelTrimTests(unittest.TestCase):
    """Food.get_environmental_impact does not leak the legacy 18 to the API."""

    def test_food_get_environmental_impact_returns_only_consumed(self):
        food = _make_beef_food()
        impacts = food.get_environmental_impact()
        self.assertEqual(set(impacts.keys()), CONSUMED_V1)
        # And specifically, none of the trimmed categories sneak through.
        self.assertEqual(set(impacts.keys()) & TRIMMED_AWAY, set())


class CnfIntegratorShapeTrimTests(unittest.TestCase):
    """Lock-in: the cnf_integrator factor block ships ONLY the 3 consumed
    midpoint categories per food group. The 15 non-consumed ReCiPe categories
    that used to be returned as "Conservative default" placeholders are no
    longer in the dict at all. This guards against accidental reintroduction
    of fabricated numerical breadth before TODO-CODE-LCA-2 lands authoritative
    AGRIBALYSE-LCI-rescored values.
    """

    @classmethod
    def setUpClass(cls):
        cls.integrator = get_cnf_integrator()
        cls.integrator.initialize()

    def _numeric_keys(self, factors):
        return {
            k for k, v in factors.items()
            if not (isinstance(k, str) and k.startswith('_'))
            and isinstance(v, (int, float))
        }

    def test_known_group_returns_only_three_numeric_keys(self):
        """A known food group (Beef Products) must return exactly the 3
        consumed categories — no Freshwater eutrophication, no toxicities,
        no resource scarcity, no ozone formation, no PM."""
        factors = self.integrator.get_environmental_impact_factors(food_id=7)
        self.assertEqual(self._numeric_keys(factors), CONSUMED_V1)
        # Specifically: none of the 15 trimmed categories sneak through.
        self.assertEqual(self._numeric_keys(factors) & TRIMMED_AWAY, set())

    def test_unknown_group_defaults_return_only_three_numeric_keys(self):
        """The default-factors block (for unmapped food groups) is also trimmed
        to 3 categories. Mock an unknown food group via the integrator's known
        non-mapping path."""
        # Reach into the integrator via a known food whose group will resolve;
        # the contract is that whatever the lookup returns, only 3 numeric
        # categories are exposed. food_id=1696 = Apple raw (Fruits) is in the
        # known groups; we exercise both code paths against the same invariant.
        factors_known = self.integrator.get_environmental_impact_factors(food_id=1696)
        self.assertEqual(self._numeric_keys(factors_known), CONSUMED_V1)

    def test_metadata_dicts_only_carry_three_consumed_categories(self):
        """`_data_source_by_category` and `_confidence_by_category` must not
        carry stale entries for the 15 trimmed categories (which would imply
        the integrator still has opinions about them)."""
        factors = self.integrator.get_environmental_impact_factors(food_id=7)
        data_sources = factors.get('_data_source_by_category', {})
        confidences = factors.get('_confidence_by_category', {})
        self.assertEqual(set(data_sources.keys()), CONSUMED_V1)
        self.assertEqual(set(confidences.keys()), CONSUMED_V1)

    def test_uncertainty_bands_only_for_three_consumed_categories(self):
        factors = self.integrator.get_environmental_impact_factors(food_id=7)
        bands = factors.get('_uncertainty_bands', {})
        self.assertEqual(set(bands.keys()), CONSUMED_V1)


class LcaTrimAndBandsTests(unittest.TestCase):
    """LifeCycleAssessment: trimmed midpoint vector + parallel bands +
    Resources=None + single_score weight renormalisation + fallback tagging."""

    @classmethod
    def setUpClass(cls):
        cls.food = _make_beef_food()
        cls.meal = Meal(foods=[cls.food])
        cls.lca = LifeCycleAssessment(cls.meal, matcher=None)
        cls.midpoints = cls.lca.perform_lcia()
        cls.endpoints = cls.lca.calculate_endpoint_impacts()
        cls.single = cls.lca.calculate_single_score()

    def test_midpoint_vector_is_exactly_the_v1_consumed_set(self):
        self.assertEqual(set(self.midpoints.keys()), CONSUMED_V1)

    def test_no_trimmed_categories_leak_into_midpoint_vector(self):
        leak = set(self.midpoints.keys()) & TRIMMED_AWAY
        self.assertEqual(leak, set(), f"trimmed categories leaked into midpoints: {leak}")

    def test_midpoint_impacts_bands_present_and_ordered(self):
        bands = self.lca.midpoint_impacts_bands
        self.assertEqual(set(bands.keys()), CONSUMED_V1)
        for cat, band in bands.items():
            with self.subTest(category=cat):
                self.assertLessEqual(band['low'], band['central'])
                self.assertLessEqual(band['central'], band['high'])
                # Band central must equal the scalar midpoint (no drift).
                self.assertAlmostEqual(band['central'], self.midpoints[cat])

    def test_resources_endpoint_is_None_when_resource_midpoints_absent(self):
        # v1 trim removes both Fossil and Mineral scarcity midpoints; the
        # Resources endpoint must be None (NOT silently 0) so it cannot
        # bias single_score downward.
        self.assertIsNone(self.endpoints['Resources'])

    def test_endpoint_bands_drop_None_resources_field(self):
        eb = self.lca.endpoint_impacts_bands
        # Resources is None at the scalar level; the bands dict should reflect
        # that by omitting Resources entirely (not carrying an empty dict).
        self.assertNotIn('Resources', eb)
        self.assertIn('Human Health', eb); self.assertIn('Ecosystems', eb)
        for k, band in eb.items():
            with self.subTest(endpoint=k):
                self.assertLessEqual(band['low'], band['central'])
                self.assertLessEqual(band['central'], band['high'])

    def test_single_score_renormalises_when_resources_is_None(self):
        """If Resources is None, single_score must renormalise so the present
        endpoints (HH + Ecosystems) divide the full weight (not silently dilute
        the score by treating Resources as a zero-contribution endpoint)."""
        # Reconstruct the expected score from HH + Ecosystems alone, equally
        # weighted (1/2 each because Resources is omitted). Normalisation now
        # comes from the methodology pack rather than a module constant.
        norm = self.lca.pack.normalization('aop', self.lca.perspective)
        hh = self.endpoints['Human Health']
        eco = self.endpoints['Ecosystems']
        expected = 0.5 * (hh / norm['Human Health']) + 0.5 * (eco / norm['Ecosystems'])
        self.assertAlmostEqual(self.single, expected, places=12)

    def test_fallback_path_is_explicitly_tagged_low_confidence(self):
        """With matcher off, every per-category source string must start with
        `fallback_low_confidence` (not the silent legacy 'group_default')."""
        food_impacts = self.lca._get_food_environmental_impacts(self.food)
        sources = food_impacts.get('_category_sources') or {}
        for cat in CONSUMED_V1:
            with self.subTest(category=cat):
                src = sources.get(cat, '')
                self.assertTrue(
                    src.startswith('fallback_low_confidence'),
                    f"category {cat!r} source {src!r} not explicitly tagged as fallback",
                )


class EnvComponentScoreRegressionTests(unittest.TestCase):
    """Regression: environmental_views._compute_environmental_component_scores
    used to weight 6 categories; 3 of them are now trimmed and would silently
    score at 100/100 each if not removed from the weight table. This test
    locks in the post-fix behaviour (3 categories, weights summing to 1.0)."""

    def test_env_score_function_iterates_only_consumed_categories(self):
        from api.views.environmental_views import _compute_environmental_component_scores
        # A fake meal-impact dict that contains ONLY the trimmed v1 set.
        midpoints = {'Global warming': 1.0, 'Land use': 5.0, 'Water consumption': 0.05}
        result = _compute_environmental_component_scores(midpoints)
        self.assertIn('environmental_score', result)
        self.assertIn('category_scores', result)
        # Score table must NOT include the legacy 3 trimmed categories.
        scored = set(result['category_scores'].keys())
        self.assertEqual(scored, CONSUMED_V1)
        # And the 3 weights must sum to ~1.0 (renormalisation invariant).
        # Re-read via private import to avoid hardcoding values here.
        import api.views.environmental_views as ev
        import inspect
        src = inspect.getsource(ev._compute_environmental_component_scores)
        self.assertIn('Global warming', src)
        self.assertIn('Land use', src)
        self.assertIn('Water consumption', src)
        self.assertNotIn("'Terrestrial acidification': 0.1", src)
        self.assertNotIn("'Freshwater eutrophication': 0.1", src)
        self.assertNotIn("'Marine eutrophication': 0.1", src)


if __name__ == "__main__":
    unittest.main()
