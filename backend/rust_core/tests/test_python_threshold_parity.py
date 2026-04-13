"""
Parity: rust_core.hsr threshold helpers vs Python reference (mirrored logic).

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
    if not thresholds or thresholds[0] == float("inf"):
        return 0
    points = 0
    for threshold in thresholds:
        if value >= threshold:
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
    def test_calculate_hsr_points(self):
        cases = [
            (5.0, [0.0, 2.0, 4.0, 6.0, 8.0]),
            (10.0, [0.0, 2.0, 4.0]),
            (1.0, [0.0, 2.0, 4.0]),
            (100.0, []),
            (100.0, [float("inf"), 0.0]),
            (0.0, [0.0, 1.0]),
        ]
        for value, thresholds in cases:
            py = _python_calculate_hsr_points(value, thresholds)
            ru = int(
                _rust_hsr.calculate_hsr_points(
                    float(value), [float(t) for t in thresholds]
                )
            )
            self.assertEqual(py, ru, msg=f"{value=!r} {thresholds=!r}")

    def test_convert_score_to_stars(self):
        star_thresholds = [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
        for final in range(-2, 15):
            py = _python_convert_score_to_stars(final, star_thresholds)
            ru = float(
                _rust_hsr.convert_score_to_stars(int(final), list(star_thresholds))
            )
            self.assertAlmostEqual(py, ru, places=12, msg=f"{final=!r}")

    def test_get_thresholds_key_sets_and_sentinels(self):
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
            self.assertEqual(len(d["energy"]), 11, msg=key)
            self.assertEqual(len(d["fvnl"]), 9, msg=key)

        bev = _rust_hsr.get_thresholds("1")
        self.assertTrue(all(math.isinf(x) for x in bev["saturated_fat"]))
        self.assertTrue(all(math.isinf(x) for x in bev["fiber"]))
        self.assertEqual(bev["energy"][-1], 300.0)

        food = _rust_hsr.get_thresholds("2")
        self.assertEqual(food["energy"][1], 335.0)
        self.assertEqual(food["star_thresholds"][0], -1.0)

        dairy_bev = _rust_hsr.get_thresholds("1D")
        self.assertEqual(dairy_bev["energy"][-1], 800.0)
        self.assertEqual(dairy_bev["star_thresholds"][0], 2.0)

        oils = _rust_hsr.get_thresholds("3")
        self.assertEqual(oils["energy"][1], 2100.0)

        cheese = _rust_hsr.get_thresholds("3D")
        general = _rust_hsr.get_thresholds("2")
        self.assertEqual(cheese["saturated_fat"][1], 2.0)
        self.assertEqual(general["saturated_fat"][1], 1.0)

    def test_calculate_component_scores_matches_manual_aggregation(self):
        """Same formula as ``HSRCalculator._calculate_components`` using Rust thresholds."""
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
            pp = _python_calculate_hsr_points(protein, list(t["protein"]))
            fp = _python_calculate_hsr_points(fiber, list(t["fiber"]))
            vp = _python_calculate_hsr_points(fvnl, list(t["fvnl"]))
            modifying = pp + fp + vp
            final = max(0, baseline - modifying)

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


if __name__ == "__main__":
    unittest.main()
