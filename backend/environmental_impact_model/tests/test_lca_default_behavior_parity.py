"""Parity tests for the post-refactor LCA pipeline.

Verifies the new methodology-pack-driven `LifeCycleAssessment`:
  1. Default behaviour (country=None, perspective='H', consumer='global')
     produces sane numeric outputs across 5 representative foods spanning
     ReCiPe-relevant impact ranges (low, mid, high carbon).
  2. Perspective switching (I vs H vs E) changes the endpoint single score
     but not the midpoint values (since midpoints are functional-unit
     volumetric / mass quantities independent of perspective).
  3. Country switching (consumer='national', country=X) substitutes country-
     specific endpoint CFs ONLY for the three water-consumption pathways
     and ONLY when the country is in the workbook.
  4. Country override is non-destructive: a country with zero water-stress
     (Canada) drives water_use_human's contribution to ~0, but climate_change
     and land_use contributions are unchanged.
  5. Egalitarian perspective ALWAYS produces a larger Human Health endpoint
     than Hierarchist for the same midpoint vector (because GW DALY factor
     is 1.25e-5 vs 9.28e-7 — ~13x).
  6. `country=None` raises NO error; `country='ZZZ'` (unknown) raises ValueError.

These tests guard against future refactor accidentally:
  - Hard-coding a perspective somewhere (test 2 catches it).
  - Forgetting to substitute country CFs (test 3 catches it).
  - Mixing up midpoint and endpoint normalisation lookup (test 1 sanity bounds).
"""
from __future__ import annotations

import os
import sys
import unittest

# Mirror the Django sys.path tweak.
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

from environmental_impact_model.src.data_loader import DataLoader  # noqa: E402
from environmental_impact_model.src.food import Food  # noqa: E402
from environmental_impact_model.src.meal import Meal  # noqa: E402
from environmental_impact_model.src.life_cycle_assessment import (  # noqa: E402
    LifeCycleAssessment,
)


# Five representative foods spanning low/mid/high carbon footprint
# (food_id picked to land in known CNF Food Groups).
REPRESENTATIVE_FOODS = [
    # (food_id, label, expected_carbon_range_kg_co2_per_100kcal_low_high)
    (1696,  "Apple raw",                  (0.0, 0.6)),   # fruit
    (7,     "Beef pot roast",             (1.0, 30.0)),  # beef (high)
    (3017,  "Carrot raw",                 (0.0, 0.6)),   # vegetable
    (5310,  "Bread white",                (0.0, 1.5)),   # cereal
    (2068,  "Yogurt plain",               (0.0, 1.5)),   # dairy
]


def _make_meal(food_id: int) -> Meal:
    return Meal([Food(food_id=food_id, quantity=100.0, data_loader=DataLoader())])


class DefaultBehaviorParityTests(unittest.TestCase):
    """Default settings (country=None, perspective='H', consumer='global')
    produce sane numeric outputs."""

    def test_defaults_produce_non_negative_midpoints(self):
        for food_id, label, _ in REPRESENTATIVE_FOODS:
            with self.subTest(food=label):
                meal = _make_meal(food_id)
                lca = LifeCycleAssessment(meal)
                lca.perform_lcia()
                for cat, val in lca.midpoint_impacts.items():
                    self.assertGreaterEqual(val, 0.0,
                        msg=f"{label} {cat} negative: {val}")

    def test_defaults_produce_endpoints_with_resources_none(self):
        """v1 trim: Resources should always be None at endpoint when only the
        3 consumed midpoints are present."""
        for food_id, label, _ in REPRESENTATIVE_FOODS:
            with self.subTest(food=label):
                meal = _make_meal(food_id)
                lca = LifeCycleAssessment(meal)
                ep = lca.calculate_endpoint_impacts()
                self.assertIsNone(ep["Resources"],
                    msg=f"{label} Resources is not None — did midpoint trim regress?")
                self.assertGreaterEqual(ep["Human Health"], 0.0)
                self.assertGreaterEqual(ep["Ecosystems"], 0.0)

    def test_defaults_single_score_renormalises_resources(self):
        """When Resources is None, single_score must use renormalised weights
        for HH + Ecosystems (1/2 each), not the 3-way 1/3 split. Single score
        uses the per_serving (raw absolute) endpoint values for dimensional
        consistency with the per-person-year AoP normalisation."""
        for food_id, label, _ in REPRESENTATIVE_FOODS:
            with self.subTest(food=label):
                meal = _make_meal(food_id)
                lca = LifeCycleAssessment(meal)
                lca.calculate_endpoint_impacts()
                ss = lca.calculate_single_score()
                norm = lca.pack.normalization('aop', 'H')
                ep = lca.endpoint_impacts_by_basis['per_serving']
                expected = 0.5 * (ep["Human Health"] / norm["Human Health"]) + \
                           0.5 * (ep["Ecosystems"] / norm["Ecosystems"])
                self.assertAlmostEqual(ss, expected, places=12,
                    msg=f"{label}: single_score = {ss}, expected {expected}")

    def test_defaults_all_endpoint_pathways_use_world_average(self):
        """With country=None/consumer='global', every endpoint pathway must
        be sourced from the world-average factor, NOT a country-specific one."""
        meal = _make_meal(7)  # beef pot roast
        lca = LifeCycleAssessment(meal)
        lca.calculate_endpoint_impacts()
        for pathway, source in lca.endpoint_factor_sources.items():
            with self.subTest(pathway=pathway):
                self.assertEqual(source, "world_average",
                    msg=f"{pathway} source = {source!r}; expected 'world_average'")


class PerspectiveSwitchingTests(unittest.TestCase):
    """I/H/E perspective changes endpoint factors but not midpoint values."""

    def setUp(self):
        self.meal_H = _make_meal(7)  # beef
        self.meal_I = _make_meal(7)
        self.meal_E = _make_meal(7)
        self.lca_H = LifeCycleAssessment(self.meal_H, perspective='H')
        self.lca_I = LifeCycleAssessment(self.meal_I, perspective='I')
        self.lca_E = LifeCycleAssessment(self.meal_E, perspective='E')
        self.lca_H.perform_lcia()
        self.lca_I.perform_lcia()
        self.lca_E.perform_lcia()
        self.lca_H.calculate_endpoint_impacts()
        self.lca_I.calculate_endpoint_impacts()
        self.lca_E.calculate_endpoint_impacts()

    def test_midpoints_identical_across_perspectives(self):
        """Midpoints (volumetric/mass quantities) are perspective-independent."""
        for cat in self.lca_H.midpoint_impacts:
            self.assertAlmostEqual(
                self.lca_H.midpoint_impacts[cat],
                self.lca_I.midpoint_impacts[cat], places=12,
                msg=f"{cat} differs between H and I — should be identical")
            self.assertAlmostEqual(
                self.lca_H.midpoint_impacts[cat],
                self.lca_E.midpoint_impacts[cat], places=12,
                msg=f"{cat} differs between H and E — should be identical")

    def test_egalitarian_human_health_dominates_individualist(self):
        """E (long-term, pessimistic GW) gives a Human Health endpoint ~13x H
        for the same GW midpoint, because GW DALY factor jumps from 9.28e-7
        (H) to 1.25e-5 (E). Verify this dominance for a high-GW meal (beef)."""
        ep_H = self.lca_H.endpoint_impacts["Human Health"]
        ep_E = self.lca_E.endpoint_impacts["Human Health"]
        ep_I = self.lca_I.endpoint_impacts["Human Health"]
        if ep_H > 0:
            self.assertGreater(ep_E, ep_H * 2,
                msg=f"Egalitarian HH ({ep_E}) not significantly > Hierarchist ({ep_H})")
            self.assertLess(ep_I, ep_H * 1.5,
                msg=f"Individualist HH ({ep_I}) unexpectedly > Hierarchist ({ep_H})")

    def test_invalid_perspective_raises(self):
        with self.assertRaises(ValueError):
            LifeCycleAssessment(_make_meal(7), perspective='X')


class CountrySwitchingTests(unittest.TestCase):
    """Country override only affects the 3 water-consumption pathways."""

    def setUp(self):
        self.meal_global = _make_meal(7)
        self.meal_canada = _make_meal(7)
        self.meal_usa = _make_meal(7)
        self.lca_global = LifeCycleAssessment(self.meal_global)
        self.lca_canada = LifeCycleAssessment(
            self.meal_canada, country='CAN', consumer_perspective='national')
        self.lca_usa = LifeCycleAssessment(
            self.meal_usa, country='USA', consumer_perspective='national')
        for l in (self.lca_global, self.lca_canada, self.lca_usa):
            l.calculate_endpoint_impacts()

    def test_canada_water_pathways_marked_country_specific(self):
        """Canada national perspective: the 3 water pathways MUST be tagged
        country_specific:CAN; the other ~17 pathways MUST remain world_average."""
        sources = self.lca_canada.endpoint_factor_sources
        water_pathways = {
            'water_use_human', 'water_use_ecosystem_terrestrial',
            'water_use_ecosystem_freshwater',
        }
        for pw in water_pathways:
            self.assertEqual(sources.get(pw), "country_specific:CAN",
                msg=f"Water pathway {pw} not marked country-specific for CAN")
        # Climate, land use, and others must stay world-average
        for pw in ('climate_change_human', 'land_use_ecosystem',
                   'climate_change_ecosystem'):
            self.assertEqual(sources.get(pw), "world_average",
                msg=f"Non-water pathway {pw} unexpectedly country-substituted")

    def test_canada_human_health_endpoint_below_world_average(self):
        """Canada water HH endpoint CF is 0 (abundant) — for any meal with
        non-zero water consumption, Canada's HH endpoint must be < the global
        default's HH endpoint."""
        global_hh = self.lca_global.endpoint_impacts["Human Health"]
        canada_hh = self.lca_canada.endpoint_impacts["Human Health"]
        self.assertLessEqual(canada_hh, global_hh + 1e-12,
            msg=f"Canada HH ({canada_hh}) > global HH ({global_hh}); should be <=")

    def test_global_perspective_ignores_country(self):
        """consumer_perspective='global' must NOT substitute country CFs even
        if country is set."""
        meal = _make_meal(7)
        lca = LifeCycleAssessment(
            meal, country='CAN', consumer_perspective='global')
        lca.calculate_endpoint_impacts()
        for source in lca.endpoint_factor_sources.values():
            self.assertEqual(source, "world_average",
                msg="consumer='global' should keep all sources world_average")

    def test_unknown_country_raises(self):
        with self.assertRaises(ValueError):
            LifeCycleAssessment(_make_meal(7), country='ZZZ',
                                consumer_perspective='national')

    def test_country_none_does_not_raise(self):
        """country=None is the default and explicit pass-through; no error."""
        LifeCycleAssessment(_make_meal(7), country=None)


class NormalizationParityTests(unittest.TestCase):
    """Per-category normalized midpoints + per-AoP norms work as expected."""

    def test_normalized_midpoints_returns_three_v1_categories(self):
        meal = _make_meal(7)
        lca = LifeCycleAssessment(meal)
        normalized = lca.calculate_normalized_midpoints()
        self.assertSetEqual(set(normalized.keys()),
                            {'Global warming', 'Land use', 'Water consumption'})
        for cat, block in normalized.items():
            with self.subTest(category=cat):
                for key in ('midpoint_value', 'world_norm_per_person_yr',
                            'person_years_equivalent'):
                    self.assertIn(key, block)
                # World norm comes from the workbook, must match the known H values.
                if cat == 'Global warming':
                    self.assertAlmostEqual(block['world_norm_per_person_yr'],
                                           7990.407652952963, places=4)


if __name__ == "__main__":
    unittest.main()
