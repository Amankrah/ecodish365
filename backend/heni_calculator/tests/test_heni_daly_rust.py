"""HENI DALY core: ``rust_core.heni`` parity via ``DALYCalculator``.

Tests pin the canonical Stylianou et al. 2021 SI Table 3 (p. 8) factor table
and Suppl. §S2.2 worked example. After HENI-CODE-1 (2026-05-21), factor signs
match Stylianou's published convention (negative DRF = beneficial, positive =
detrimental); user-facing `health_impact_minutes` remains positive = beneficial
via `MINUTES_PER_UDALY = -0.5256`.
"""

import unittest

from heni_calculator.heni.core.daly_calculator import DALYCalculator


class HeniRustDalycoreTests(unittest.TestCase):
    def test_compute_matches_direct_rust_dict(self):
        """Python wrapper and direct Rust call must produce identical scores."""
        from rust_core import heni as _rust_heni

        rf = {"fiber_other": 10.0, "fruits": 50.0, "sodium": 1.0}
        raw = _rust_heni.compute_heni(rf, 500.0, 200.0, 200.0, "adult_male", True)
        calc = DALYCalculator(age_group="adult_male", gender_adjustment=True)
        r = calc.calculate_heni_score(rf, 500.0, 200.0, 200.0)
        self.assertAlmostEqual(r.total_heni_score, raw["total_heni_score"], places=9)
        self.assertAlmostEqual(r.heni_per_100_kcal, raw["heni_per_100_kcal"], places=9)
        self.assertEqual(r.risk_factor_amounts, rf)

    def test_omega3_is_beneficial_under_stylianou_sign(self):
        """A beneficial-factor-only meal must yield POSITIVE health_impact_minutes
        (food adds healthy life) and NEGATIVE μDALY total (Stylianou published
        sign convention: negative DRF = beneficial)."""
        # 0.20 g omega_3 — under TMREL 0.250, no cap.
        rf = {"omega_3": 0.20}
        r = DALYCalculator(age_group="adult_male").calculate_heni_score(
            rf, 500.0, 200.0, 200.0
        )
        self.assertAlmostEqual(r.total_heni_score, 0.20 * -81.0, places=9)
        self.assertGreater(r.health_impact_minutes, 0.0,
                           "beneficial food must yield positive minutes")
        self.assertAlmostEqual(
            r.health_impact_minutes, 0.20 * -81.0 * -0.5256, places=6,
        )

    def test_sodium_is_detrimental_under_stylianou_sign(self):
        """A detrimental-factor-only meal must yield NEGATIVE
        health_impact_minutes (food shortens healthy life) and POSITIVE μDALY
        total (Stylianou published convention: positive DRF = detrimental)."""
        rf = {"sodium": 1.0}  # under TMREL 3.49 g
        r = DALYCalculator(age_group="adult_male").calculate_heni_score(
            rf, 500.0, 200.0, 200.0
        )
        self.assertAlmostEqual(r.total_heni_score, 1.0 * 13.9, places=9)
        self.assertLess(r.health_impact_minutes, 0.0,
                        "detrimental food must yield negative minutes")
        self.assertAlmostEqual(r.health_impact_minutes, 1.0 * 13.9 * -0.5256,
                               places=6)

    def test_stylianou_2021_chicken_wing_worked_example(self):
        """Canonical worked example from Stylianou 2021 SI §S2.2 (p. 13).

        85 g chicken-wing serving = 1.85 g PUFA + 0.0281 g calcium + 0.492 g
        sodium + 0.139 g TFA → HENI ≈ -3.3 min/serving. Allow ±0.3 min for
        published rounding of the factor values.
        """
        rf = {
            "polyunsaturated_fatty_acids": 1.85,
            "calcium": 0.0281,
            "sodium": 0.492,
            "trans_fat": 0.139,
        }
        r = DALYCalculator(age_group="adult_male").calculate_heni_score(
            rf, 85.0 * 2.5, 85.0, 85.0
        )
        # Expected: 1.85×-0.60 + 0.0281×-5.1 + 0.492×13.9 + 0.139×4.4
        #         ≈ -1.11 - 0.143 + 6.839 + 0.612
        #         ≈ +6.20 μDALY
        # health_impact_minutes ≈ 6.20 × -0.5256 ≈ -3.26 min (detrimental).
        self.assertAlmostEqual(r.health_impact_minutes, -3.3, delta=0.3)

    def test_tmrel_hard_cap_applied(self):
        """Above the TMREL the contribution is hard-capped (no soft taper)."""
        # 0.50 g omega_3 with TMREL 0.250 g → effective 0.250 g.
        rf = {"omega_3": 0.50}
        r = DALYCalculator(age_group="adult_male").calculate_heni_score(
            rf, 100.0, 100.0, 100.0
        )
        self.assertAlmostEqual(r.total_heni_score, 0.250 * -81.0, places=9)
        self.assertEqual(len(r.effective_range_warnings), 1)
        self.assertIn("TMREL", r.effective_range_warnings[0])

    def test_female_adjustment_dampens_magnitude(self):
        """Female age adjustment (0.95) dampens absolute magnitude regardless of
        which sign convention the factor is in. Stylianou-signed omega_3 is
        negative, so |female| < |male|."""
        rf = {"omega_3": 0.20}  # under TMREL
        male = DALYCalculator(age_group="adult_male").calculate_heni_score(
            rf, 100.0, 100.0, 100.0
        )
        female = DALYCalculator(age_group="adult_female").calculate_heni_score(
            rf, 100.0, 100.0, 100.0
        )
        self.assertLess(abs(female.total_heni_score), abs(male.total_heni_score))

    def test_disable_age_adjustment(self):
        """Disabling age adjustment recovers the un-scaled magnitude."""
        rf = {"omega_3": 0.20}
        adj = DALYCalculator(
            age_group="adult_female", gender_adjustment=True,
        ).calculate_heni_score(rf, 100.0, 100.0, 100.0)
        noadj = DALYCalculator(
            age_group="adult_female", gender_adjustment=False,
        ).calculate_heni_score(rf, 100.0, 100.0, 100.0)
        # Under Stylianou sign omega_3 is negative; noadj has the full
        # un-scaled magnitude so |noadj| > |adj|.
        self.assertGreater(abs(noadj.total_heni_score), abs(adj.total_heni_score))

    def test_disease_breakdown_sums_to_total(self):
        """disease_breakdown apportions Σ DRF × g equally across each risk's
        outcome set; the across-disease sum must equal `total_heni_score`
        (within fp tolerance, ignoring age_adjustment which is 1.0 for male)."""
        rf = {
            "polyunsaturated_fatty_acids": 1.85,
            "calcium": 0.0281,
            "sodium": 0.492,
            "trans_fat": 0.139,
        }
        r = DALYCalculator(age_group="adult_male").calculate_heni_score(
            rf, 85.0 * 2.5, 85.0, 85.0
        )
        sum_disease = sum(r.disease_burden_breakdown.values())
        self.assertAlmostEqual(sum_disease, r.total_heni_score, places=9)
