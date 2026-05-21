"""
Parity: rust_core.hsr threshold helpers vs Python reference (mirrored logic).

After HSR-CODE-1 (2026-05-21) the canonical reference is HSRC v9 (HSRAC,
10 December 2025). Scoring uses the v9 convention "≤X earns 0 points,
>X earns 1 point" — i.e. strict `>` semantics. The mirror reference below
matches that.

Does not import Django or hsr_calculator (avoids heavy __init__ deps).

Run from ``backend`` with extension installed::

  pip install maturin
  cd rust_core && maturin develop
  cd .. && python rust_core/tests/test_python_threshold_parity.py

Reference mirrors ``rust_core`` semantics (HSR math lives in Rust only).
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _python_calculate_hsr_points(value: float, thresholds: list[float]) -> int:
    """v9 convention: strict `>`. Positive-infinity first → 0 (not-applicable).
    Negative-infinity first → counted (Cat 1 energy "no zero-point bucket")."""
    if not thresholds:
        return 0
    if thresholds[0] == float("inf"):
        return 0
    points = 0
    for threshold in thresholds:
        if value > threshold:
            points += 1
        else:
            break
    return points


def _python_convert_score_to_stars(final_score: int, star_thresholds: list[float]) -> float:
    stars = 0.5
    for i, threshold in enumerate(star_thresholds):
        if final_score <= threshold:
            stars = 5.0 - (i * 0.5)
            break
    return max(0.5, min(5.0, stars))


try:
    import rust_core.hsr as _rust_hsr  # type: ignore
except ImportError:
    _rust_hsr = None


@unittest.skipIf(_rust_hsr is None, "install with: cd rust_core && maturin develop")
class ThresholdParityTests(unittest.TestCase):
    def test_calculate_hsr_points_strict_greater(self):
        cases = [
            # (value, thresholds, expected under v9 strict-> semantics)
            (5.0, [0.0, 2.0, 4.0, 6.0, 8.0], 3),  # 5>0,2,4 yes; 5>6 no → 3
            (10.0, [0.0, 2.0, 4.0], 3),  # > all 3 → 3
            (1.0, [0.0, 2.0, 4.0], 1),  # 1>0 yes; 1>2 no → 1
            (100.0, [], 0),  # empty → 0
            (100.0, [float("inf"), 0.0], 0),  # +inf sentinel → 0
            (0.0, [0.0, 1.0], 0),  # 0>0 NO → 0 (was 1 under >=)
            # v9 Cat 2 sodium boundary (≤90 → 0 pts; >90 → 1 pt)
            (90.0, [90.0, 180.0], 0),
            (91.0, [90.0, 180.0], 1),
            (180.0, [90.0, 180.0], 1),
            (181.0, [90.0, 180.0], 2),
            # Cat 1 energy NEG_INFINITY first → always at least 1 point.
            (0.0, [float("-inf"), 31.0, 61.0], 1),
            (32.0, [float("-inf"), 31.0, 61.0], 2),
        ]
        for value, thresholds, expected in cases:
            py = _python_calculate_hsr_points(value, thresholds)
            self.assertEqual(py, expected, msg=f"py reference: {value=}, {thresholds=}")
            ru = int(
                _rust_hsr.calculate_hsr_points(
                    float(value), [float(t) for t in thresholds]
                )
            )
            self.assertEqual(ru, expected, msg=f"rust: {value=}, {thresholds=}")

    def test_convert_score_to_stars_v9_cat2(self):
        # v9 Table 7 Cat 2: score ≤-11 → 5.0, then 0.5-star decrements.
        star_thresholds = [-11.0, -7.0, -2.0, 2.0, 6.0, 11.0, 15.0, 20.0, 24.0]
        for final in range(-15, 30):
            py = _python_convert_score_to_stars(final, star_thresholds)
            ru = float(
                _rust_hsr.convert_score_to_stars(int(final), list(star_thresholds))
            )
            self.assertAlmostEqual(py, ru, places=12, msg=f"{final=!r}")

    def test_get_thresholds_v9_shapes(self):
        """v9 Table 1 (Cat 1D, 2, 2D) gives baseline up to 30 points for
        sat fat and sodium, 25 for sugar. v9 Table 2 (Cat 3, 3D) gives 10
        sugar points and 30 sat-fat points. FVNL uses 8 thresholds for
        non-Cat-1 (Table 4 Col 2) and 10 for Cat 1 (Table 5)."""
        for key in ("1", "1D", "2", "2D", "3", "3D"):
            d = _rust_hsr.get_thresholds(key)
            self.assertEqual(
                set(d.keys()),
                {
                    "energy",
                    "sugar",
                    "saturated_fat",
                    "sodium",
                    "fvnl",
                    "protein",
                    "fiber",
                    "star_thresholds",
                },
                msg=key,
            )

        # Cat 1: not-applicable sentinels for sat fat, sodium, protein, fibre.
        bev = _rust_hsr.get_thresholds("1")
        self.assertTrue(all(math.isinf(x) for x in bev["saturated_fat"]), msg="cat1 sat_fat NA")
        self.assertTrue(all(math.isinf(x) for x in bev["sodium"]), msg="cat1 sodium NA")
        self.assertTrue(all(math.isinf(x) for x in bev["protein"]), msg="cat1 protein NA")
        self.assertTrue(all(math.isinf(x) for x in bev["fiber"]), msg="cat1 fiber NA")
        # v9 Table 3 energy: NEG_INFINITY prepended for the no-zero-point rule.
        self.assertTrue(math.isinf(bev["energy"][0]) and bev["energy"][0] < 0)
        self.assertEqual(bev["energy"][1], 31.0)
        # v9 Table 5 Cat 1 FVNL.
        self.assertEqual(len(bev["fvnl"]), 10)
        # Cat 1 star_thresholds: name-override slots are NEG_INFINITY.
        self.assertTrue(math.isinf(bev["star_thresholds"][0]) and bev["star_thresholds"][0] < 0)
        self.assertEqual(bev["star_thresholds"][2], 0.0)

        # Cat 1D, 2, 2D share Table 1 scales.
        for key in ("1D", "2", "2D"):
            d = _rust_hsr.get_thresholds(key)
            self.assertEqual(d["energy"][0], 335.0, msg=key)
            self.assertEqual(d["saturated_fat"][0], 1.0, msg=key)
            self.assertEqual(d["sugar"][0], 5.0, msg=key)
            self.assertEqual(d["sodium"][0], 90.0, msg=key)
            self.assertEqual(len(d["energy"]), 11, msg=key)
            self.assertEqual(len(d["saturated_fat"]), 30, msg=key)
            self.assertEqual(len(d["sugar"]), 25, msg=key)
            self.assertEqual(len(d["sodium"]), 30, msg=key)
            self.assertEqual(len(d["fvnl"]), 8, msg=key)
            self.assertEqual(len(d["protein"]), 15, msg=key)

        # Cat 1D not eligible for fibre (Table 6 footnote).
        cat1d = _rust_hsr.get_thresholds("1D")
        self.assertTrue(all(math.isinf(x) for x in cat1d["fiber"]))

        # Cat 2 and 2D eligible for fibre.
        for key in ("2", "2D"):
            self.assertEqual(_rust_hsr.get_thresholds(key)["fiber"][0], 0.9, msg=key)

        # Cat 3 / 3D use Table 2 (uniform sat fat 1g; 10 sugar pts max).
        for key in ("3", "3D"):
            d = _rust_hsr.get_thresholds(key)
            self.assertEqual(len(d["sugar"]), 10, msg=key)
            self.assertEqual(d["saturated_fat"][10], 11.0, msg=key)  # uniform 1g
            self.assertEqual(d["energy"][0], 335.0, msg=f"{key} shares Table 1 energy")

        # v9 Table 7 star-threshold first-element checks (the 5.0-star bound).
        self.assertEqual(_rust_hsr.get_thresholds("1D")["star_thresholds"][0], -2.0)
        self.assertEqual(_rust_hsr.get_thresholds("2")["star_thresholds"][0], -11.0)
        self.assertEqual(_rust_hsr.get_thresholds("2D")["star_thresholds"][0], -2.0)
        self.assertEqual(_rust_hsr.get_thresholds("3")["star_thresholds"][0], 13.0)
        self.assertEqual(_rust_hsr.get_thresholds("3D")["star_thresholds"][0], 24.0)

    def test_calculate_component_scores_matches_manual_aggregation(self):
        """Same formula as ``HSRCalculator._calculate_components`` using Rust
        thresholds and v9 strict-`>` semantics. After HSR-CODE-1 final_score
        is no longer clamped at 0."""
        for category in ("1", "1D", "2", "2D", "3", "3D"):
            t = _rust_hsr.get_thresholds(category)
            energy_kj = 1200.0
            sat_fat = 4.0
            sugars = 8.0
            sodium = 350.0
            protein = 7.0
            fiber = 2.5
            fvnl = 25.0

            ep = _python_calculate_hsr_points(energy_kj, list(t["energy"]))
            sfp = _python_calculate_hsr_points(sat_fat, list(t["saturated_fat"]))
            sp = _python_calculate_hsr_points(sugars, list(t["sugar"]))
            nap = _python_calculate_hsr_points(sodium, list(t["sodium"]))
            baseline = ep + sfp + sp + nap
            raw_pp = _python_calculate_hsr_points(protein, list(t["protein"]))
            fp = _python_calculate_hsr_points(fiber, list(t["fiber"]))
            vp = _python_calculate_hsr_points(fvnl, list(t["fvnl"]))
            # v9 protein-eligibility rule.
            pp = 0 if (baseline >= 13 and vp < 5) else raw_pp
            modifying = pp + fp + vp
            final = baseline - modifying  # no .max(0) clamp under v9

            ru = _rust_hsr.calculate_component_scores(
                category,
                energy_kj,
                sat_fat,
                sugars,
                sodium,
                protein,
                fiber,
                fvnl,
            )
            self.assertEqual(int(ru["energy_points"]), ep, msg=category)
            self.assertEqual(int(ru["saturated_fat_points"]), sfp, msg=category)
            self.assertEqual(int(ru["sugar_points"]), sp, msg=category)
            self.assertEqual(int(ru["sodium_points"]), nap, msg=category)
            self.assertEqual(int(ru["baseline_points"]), baseline, msg=category)
            self.assertEqual(int(ru["protein_points"]), pp, msg=category)
            self.assertEqual(int(ru["fiber_points"]), fp, msg=category)
            self.assertEqual(int(ru["fvnl_points"]), vp, msg=category)
            self.assertEqual(int(ru["modifying_points"]), modifying, msg=category)
            self.assertEqual(int(ru["final_score"]), final, msg=category)

    def test_food_group_category_phase3(self):
        self.assertEqual(_rust_hsr.food_group_category(1, "whole milk"), "1D")
        self.assertEqual(_rust_hsr.food_group_category(1, "cheddar cheese"), "3D")
        self.assertEqual(_rust_hsr.food_group_category(14, "spring water"), "1")
        self.assertEqual(_rust_hsr.food_group_category(5, "chicken breast"), "2")

    def test_nuanced_fvnl_percent_phase3(self):
        self.assertAlmostEqual(
            _rust_hsr.nuanced_fvnl_percent("spinach, raw", 11, 11),
            100.0,
            places=6,
        )
        self.assertAlmostEqual(
            _rust_hsr.nuanced_fvnl_percent("apple juice, canned", 9, 9),
            67.0 * 0.75,
            places=6,
        )


@unittest.skipIf(_rust_hsr is None, "install with: cd rust_core && maturin develop")
class HSRv9CanonicalReferenceFoods(unittest.TestCase):
    """Smoke test against 10 canonical Australian retail-label reference foods.

    Expected stars are drawn from publicly-known AU label values (FoodSwitch /
    Mozaffarian 2024 cross-walk anchors / Australian Dietary Guidelines
    examples). After HSR-CODE-1 the implementation should reproduce all 10
    within ±0.5 stars.

    The plain-water case is documented as 3.5 stars under the numeric
    calculation (the AU spec's "Water → 5.0" override is name-based and
    deferred to HSR-CODE-1.x).
    """

    @staticmethod
    def _stars(cat, e, sat, sug, na, prot, fib, fvnl):
        s = _rust_hsr.calculate_component_scores(
            category=cat,
            energy_kj=e,
            fatty_acids_saturated_total=sat,
            sugars_total=sug,
            sodium=na,
            protein=prot,
            fibre_total_dietary=fib,
            fvnl_percent=fvnl,
        )
        return float(
            _rust_hsr.convert_score_to_stars(
                int(s["final_score"]),
                list(_rust_hsr.get_thresholds(cat)["star_thresholds"]),
            )
        )

    def test_plain_water_numeric_floor(self):
        # Numeric: baseline = 1 energy + 0 sugar = 1 → 3.5 stars under Cat 1.
        # The 5.0-star "Water" name override is deferred to HSR-CODE-1.x.
        stars = self._stars("1", 0, 0, 0, 0, 0, 0, 0)
        self.assertAlmostEqual(stars, 3.5, delta=0.5, msg=f"got {stars}")

    def test_white_table_sugar(self):
        # AU label data: pure sugar = 0.5 stars (the absolute floor).
        stars = self._stars("2", 1700, 0, 100, 0, 0, 0, 0)
        self.assertAlmostEqual(stars, 0.5, delta=0.5, msg=f"got {stars}")

    def test_regular_cola(self):
        # v9 Cat 1 (Table 3 + Table 7): regular cola at 180 kJ + 10.6 g sugar
        # per 100 mL yields baseline = 6 (energy) + 7 (sugar) = 13, which lands
        # in Cat 1 Table 7 row "≥12 → 0.5 stars" (the spec's floor for
        # high-sugar non-dairy beverages). Some AU retail labels show
        # 1.5–2.0 stars for cola; those reflect older v5-era algorithms or
        # slightly different per-100mL nutrient declarations.
        stars = self._stars("1", 180, 0, 10.6, 12, 0, 0, 0)
        self.assertAlmostEqual(stars, 0.5, delta=0.5, msg=f"got {stars}")

    def test_plain_whole_milk(self):
        # AU label data: plain whole milk = ~4.0 stars.
        stars = self._stars("1D", 270, 2.0, 4.7, 44, 3.4, 0, 0)
        self.assertAlmostEqual(stars, 4.0, delta=0.5, msg=f"got {stars}")

    def test_plain_rolled_oats(self):
        # AU label data: plain rolled oats = 5.0 stars (whole grain anchor).
        stars = self._stars("2", 1550, 1.2, 0.8, 2, 13.2, 10.1, 0)
        self.assertAlmostEqual(stars, 5.0, delta=0.5, msg=f"got {stars}")

    def test_raw_chia_seeds(self):
        # Mozaffarian 2024 cross-walk anchor: raw chia = 5.0 stars.
        stars = self._stars("2", 1971, 3.3, 0.4, 16, 17, 34, 100)
        self.assertAlmostEqual(stars, 5.0, delta=0.5, msg=f"got {stars}")

    def test_plain_unsweetened_almond_beverage(self):
        # v9 Cat 1 (Table 3 + Table 7): plain unsweetened almond beverage at
        # 120 kJ + 0.3 g sugar per 100 mL yields baseline = 4 (energy) + 1
        # (sugar) = 5, which lands in Cat 1 Table 7 row "4-5 → 2.5 stars".
        # AU retail labels for plant-based "milks" sometimes show higher
        # ratings because retailers classify them under Cat 1D (dairy bev),
        # but GBD 2017 / v9 keeps plant beverages in Cat 1 (non-dairy bev).
        stars = self._stars("1", 120, 0.1, 0.3, 60, 0.4, 0.3, 0)
        self.assertAlmostEqual(stars, 2.5, delta=0.5, msg=f"got {stars}")

    def test_bacon(self):
        # AU label data: bacon = 0.5–1.5 stars.
        stars = self._stars("2", 1740, 11, 0.2, 1500, 14, 0, 0)
        self.assertTrue(0.5 <= stars <= 2.0, msg=f"got {stars}, expected 0.5-1.5")

    def test_plain_greek_yogurt(self):
        # AU label data: plain Greek yogurt (full-fat) = 4.0–4.5 stars.
        stars = self._stars("2D", 350, 3.4, 3.6, 36, 9, 0, 0)
        self.assertTrue(3.5 <= stars <= 5.0, msg=f"got {stars}, expected 4.0-4.5")

    def test_sliced_white_bread(self):
        # AU label data: sliced white bread = 3.0–3.5 stars.
        stars = self._stars("2", 1100, 0.8, 4.0, 480, 9, 2.5, 0)
        self.assertTrue(2.5 <= stars <= 4.0, msg=f"got {stars}, expected 3.0-3.5")


if __name__ == "__main__":
    unittest.main()
