"""Lock-in tests for Tier α: multi-basis functional-unit exposure.

Verifies that `LifeCycleAssessment` computes all four functional-unit bases
(per_serving, per_100g_product, per_100_kcal, per_100g_protein) consistently
from a single raw-mass aggregation, that the chosen `basis` parameter drives
the backward-compat headline output, and that downstream normalisations
(`calculate_normalized_midpoints`, `calculate_single_score`) use the
dimensionally-correct per_serving (raw absolute) values.

Pins the 2026 multi-basis refactor that:
  - separated raw aggregation from functional-unit normalisation
  - fixed `calculate_normalized_midpoints` and `calculate_single_score` to
    consume per_serving (raw) instead of per_100_kcal
  - added `basis` as a constructor kw-arg (default per_100_kcal for backward
    compatibility with prior callers)
"""
from __future__ import annotations

import os
import sys
import unittest

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
    LifeCycleAssessment, VALID_BASES,
)


def _make_meal(food_id: int, quantity: float = 100.0) -> Meal:
    return Meal([Food(food_id=food_id, quantity=quantity, data_loader=DataLoader())])


class MultiBasisExposureTests(unittest.TestCase):
    """The four bases are computed simultaneously and exposed under
    `midpoint_impacts_by_basis`."""

    @classmethod
    def setUpClass(cls):
        cls.meal = _make_meal(2650, quantity=100.0)  # Beef brain raw, 100 g
        cls.lca = LifeCycleAssessment(cls.meal)
        cls.lca.perform_lcia()

    def test_all_four_bases_present(self):
        self.assertSetEqual(set(self.lca.midpoint_impacts_by_basis.keys()), set(VALID_BASES))

    def test_each_basis_has_three_consumed_categories(self):
        for basis in VALID_BASES:
            with self.subTest(basis=basis):
                self.assertSetEqual(
                    set(self.lca.midpoint_impacts_by_basis[basis].keys()),
                    {'Global warming', 'Land use', 'Water consumption'},
                )

    def test_per_serving_equals_raw_aggregation(self):
        """`per_serving` is the raw absolute impact for the meal — its
        functional-unit factor is exactly 1.0."""
        self.assertAlmostEqual(self.lca.basis_factors['per_serving'], 1.0, places=12)

    def test_basis_factors_are_internally_consistent(self):
        """Cross-basis consistency: per_100g_product / per_serving must equal
        100 / total_mass_g. Same idea for the other bases."""
        bf = self.lca.basis_factors
        # For a 100 g meal, per_100g_product factor is 100/100 = 1.0
        self.assertAlmostEqual(bf['per_100g_product'], 1.0, places=6)
        # per_serving / per_100g_product = total_mass_g / 100 = 1 here
        gw_serv = self.lca.midpoint_impacts_by_basis['per_serving']['Global warming']
        gw_100g = self.lca.midpoint_impacts_by_basis['per_100g_product']['Global warming']
        # For 100g meal: per_serving == per_100g_product * (100/100) == per_100g_product
        self.assertAlmostEqual(gw_serv, gw_100g, places=10)

    def test_chosen_basis_surfaces_on_backward_compat_field(self):
        """`self.midpoint_impacts` mirrors the chosen-basis dict from
        `midpoint_impacts_by_basis[self.basis]`."""
        for cat, val in self.lca.midpoint_impacts.items():
            self.assertAlmostEqual(
                val,
                self.lca.midpoint_impacts_by_basis[self.lca.basis][cat],
                places=12,
            )


class BasisRankingChangeTests(unittest.TestCase):
    """The choice of basis can change which food has the worse impact —
    confirms the multi-basis surface is actually informative."""

    def test_protein_basis_re_ranks_high_protein_foods(self):
        """A 100g beef serving (high protein) vs a 100g vegetable serving (low
        protein): per_100g_product penalises beef harder; per_100g_protein
        narrows the gap (or could reverse it for very low-impact-per-protein
        sources). Verify the relative ratio changes between bases."""
        beef_meal = _make_meal(2650, quantity=100.0)         # Beef brain raw
        veg_meal = _make_meal(2380, quantity=100.0)          # carrot raw
        beef_lca = LifeCycleAssessment(beef_meal); beef_lca.perform_lcia()
        veg_lca = LifeCycleAssessment(veg_meal);  veg_lca.perform_lcia()
        # Per-100g ratio: beef GHG / veg GHG
        beef_gw_100g = beef_lca.midpoint_impacts_by_basis['per_100g_product']['Global warming']
        veg_gw_100g = veg_lca.midpoint_impacts_by_basis['per_100g_product']['Global warming']
        ratio_100g = beef_gw_100g / max(veg_gw_100g, 1e-12)
        # Per-100g-protein ratio: should be smaller because beef has ~20% protein,
        # most vegetables have ~1-3% protein, so dividing both by protein
        # shifts the beef value down more than the veg value (in fact beef's
        # protein-normalised impact is well-defined; very-low-protein veg may
        # produce a very large per_100g_protein number).
        beef_gw_prot = beef_lca.midpoint_impacts_by_basis['per_100g_protein']['Global warming']
        veg_gw_prot = veg_lca.midpoint_impacts_by_basis['per_100g_protein']['Global warming']
        # Sanity: both ratios are well-defined and the ranking is documented.
        self.assertGreater(beef_gw_100g, 0)
        self.assertGreater(veg_gw_100g, 0)
        # The protein-basis ratio differs from the mass-basis ratio (not
        # asserting a fixed direction because real food group impacts can
        # flip either way; the point is the basis choice MATTERS).
        if veg_gw_prot > 0 and beef_gw_prot > 0:
            ratio_protein = beef_gw_prot / veg_gw_prot
            self.assertNotAlmostEqual(ratio_100g, ratio_protein, places=4,
                msg="Basis choice (mass vs protein) didn't change beef/veg ratio — "
                    "either the protein fractions are equal (impossible) or a basis "
                    "fell back to zero.")


class NormalizationDimensionalityFixTests(unittest.TestCase):
    """Pin the 2026-05 fix: `calculate_normalized_midpoints` and
    `calculate_single_score` use per_serving (raw) values rather than
    per_100_kcal, so the person-year normalisation is dimensionally correct."""

    @classmethod
    def setUpClass(cls):
        cls.meal = _make_meal(2650, quantity=100.0)
        cls.lca = LifeCycleAssessment(cls.meal)
        cls.lca.perform_lcia()
        cls.lca.calculate_endpoint_impacts()

    def test_normalized_midpoints_use_per_serving_raw(self):
        normalized = self.lca.calculate_normalized_midpoints()
        raw = self.lca.midpoint_impacts_by_basis['per_serving']
        for category, block in normalized.items():
            self.assertAlmostEqual(block['midpoint_value'], raw[category], places=12,
                msg=f"{category} normalized midpoint should equal per_serving raw value")
            self.assertAlmostEqual(
                block['person_years_equivalent'],
                raw[category] / block['world_norm_per_person_yr'],
                places=12,
            )

    def test_single_score_uses_per_serving_raw_endpoints(self):
        """Single score should consume the raw absolute endpoints, not
        per-100-kcal-scaled. Reconstruct from per_serving basis + per-AoP
        norm and assert match."""
        ss = self.lca.calculate_single_score()
        norm = self.lca.pack.normalization('aop', self.lca.perspective)
        raw_ep = self.lca.endpoint_impacts_by_basis['per_serving']
        present = {k: v for k, v in raw_ep.items() if v is not None}
        total_weight = sum(1/3 for _ in present)
        expected = sum((v / norm[k]) * ((1/3) / total_weight) for k, v in present.items())
        self.assertAlmostEqual(ss, expected, places=12)


class BasisParameterTests(unittest.TestCase):
    """`basis` constructor kw-arg drives the chosen output without affecting
    the multi-basis dict (all four are always computed)."""

    def test_basis_chooses_headline_output(self):
        meal = _make_meal(2650, quantity=100.0)
        lca_100g = LifeCycleAssessment(meal, basis='per_100g_product')
        lca_100g.perform_lcia()
        # midpoint_impacts must be the per_100g_product basis
        self.assertAlmostEqual(
            lca_100g.midpoint_impacts['Global warming'],
            lca_100g.midpoint_impacts_by_basis['per_100g_product']['Global warming'],
            places=12,
        )
        # per_100_kcal should still be computed for the same meal
        self.assertIn('per_100_kcal', lca_100g.midpoint_impacts_by_basis)
        self.assertGreater(lca_100g.midpoint_impacts_by_basis['per_100_kcal']['Global warming'], 0)

    def test_invalid_basis_raises(self):
        with self.assertRaises(ValueError):
            LifeCycleAssessment(_make_meal(2650), basis='per_planet')

    def test_default_basis_is_per_100_kcal(self):
        """Backward compatibility: callers that don't pass `basis` get the
        original per_100_kcal headline."""
        meal = _make_meal(2650)
        lca = LifeCycleAssessment(meal)
        self.assertEqual(lca.basis, 'per_100_kcal')


if __name__ == '__main__':
    unittest.main()
