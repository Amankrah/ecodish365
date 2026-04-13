"""HENI DALY core: ``rust_core.heni`` parity via ``DALYCalculator``."""

import unittest

from heni_calculator.heni.core.daly_calculator import DALYCalculator


class HeniRustDalycoreTests(unittest.TestCase):
    def test_compute_matches_direct_rust_dict(self):
        from rust_core import heni as _rust_heni

        rf = {"fiber": 10.0, "fruits": 50.0, "sodium": 1.0}
        raw = _rust_heni.compute_heni(rf, 500.0, 200.0, 200.0, "adult_male", True)
        calc = DALYCalculator(age_group="adult_male", gender_adjustment=True)
        r = calc.calculate_heni_score(rf, 500.0, 200.0, 200.0)
        self.assertAlmostEqual(r.total_heni_score, raw["total_heni_score"], places=9)
        self.assertAlmostEqual(r.heni_per_100_kcal, raw["heni_per_100_kcal"], places=9)
        self.assertEqual(r.risk_factor_amounts, rf)

    def test_female_adjustment_lower_total_than_male(self):
        rf = {"omega_3": 1.0}
        male = DALYCalculator(age_group="adult_male").calculate_heni_score(rf, 100.0, 100.0, 100.0)
        female = DALYCalculator(age_group="adult_female").calculate_heni_score(
            rf, 100.0, 100.0, 100.0
        )
        self.assertLess(female.total_heni_score, male.total_heni_score)

    def test_disable_age_adjustment(self):
        rf = {"omega_3": 1.0}
        adj = DALYCalculator(age_group="adult_female", gender_adjustment=True).calculate_heni_score(
            rf, 100.0, 100.0, 100.0
        )
        noadj = DALYCalculator(age_group="adult_female", gender_adjustment=False).calculate_heni_score(
            rf, 100.0, 100.0, 100.0
        )
        self.assertGreater(noadj.total_heni_score, adj.total_heni_score)
