"""Smoke harness — PLANETARY-1 (EAT-Lancet 2.0 food-system boundary overlay).

Four directional gates:
  G1: low-carbon vegan day  → climate share < 20 %.
  G2: mixed Western day     → climate share 80-180 %.
  G3: beef-heavy day        → climate share > 200 %.
  G4: response shape — all 9 boundary keys present, 3 with `available: True`,
      6 with `available: False` + populated `reason`. Each available row
      carries the full key contract (meal_value, per_capita_daily_budget,
      share_of_daily_budget_pct, method_note, unit, citation-traceable fields).

Run from backend/:  PYTHONIOENCODING=utf-8 python _smoke_planetary_boundaries.py
"""
from __future__ import annotations

import io
import sys

# Force UTF-8 stdout so the CO₂ / m² glyphs in label strings don't blow up
# under cp1252 (Windows default).
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


# Local imports — kept inside main() so a top-level ImportError doesn't
# kill the print banner.
def main() -> int:
    from environmental_impact_model.src.planetary_boundaries import (
        compute_planetary_boundary_shares,
        build_planetary_explanations,
        get_per_capita_daily_budgets,
    )

    # Reference panel inputs (per-day ReCiPe midpoints, kg CO₂e / m²·yr / m³).
    # Numbers are illustrative day totals consistent with Poore & Nemecek 2018
    # food-group order-of-magnitude figures.
    PANEL = {
        "vegan_low_carbon_day":   {"Global warming": 0.30, "Land use":  2.5, "Water consumption": 0.10},
        "mixed_western_day":      {"Global warming": 2.40, "Land use": 18.0, "Water consumption": 0.55},
        "beef_heavy_day":         {"Global warming": 12.0, "Land use": 45.0, "Water consumption": 0.80},
    }

    print("=" * 70)
    print("PLANETARY-1 smoke harness — 4 gates")
    print("=" * 70)
    print()

    # Print per-capita budgets for context.
    budgets = get_per_capita_daily_budgets()
    print("Per-capita-per-day budgets (E28 Table 2):")
    print(f"  climate:  {budgets['climate_change']:.4f} kg CO₂e/p/day")
    print(f"  land:     {budgets['land_use']:.3f}  m²·yr/p/day")
    print(f"  water:    {budgets['water_consumption']:.4f} m³/p/day")
    print()

    results = {}
    for label, midpoints in PANEL.items():
        results[label] = compute_planetary_boundary_shares(midpoints)

    # ------------------------------------------------------------------
    # G1: low-carbon vegan day — climate share < 20 %
    # ------------------------------------------------------------------
    vegan = next(r for r in results["vegan_low_carbon_day"]["shares"]
                 if r["key"] == "climate_change")
    g1_pass = vegan["share_of_daily_budget_pct"] < 20.0
    print(f"G1 (vegan low-carbon): climate share = {vegan['share_of_daily_budget_pct']:.1f}% "
          f"→ {'PASS' if g1_pass else 'FAIL'} (< 20 %)")

    # ------------------------------------------------------------------
    # G2: mixed Western day — climate share 80-180 %
    # ------------------------------------------------------------------
    western = next(r for r in results["mixed_western_day"]["shares"]
                   if r["key"] == "climate_change")
    g2_pass = 80.0 <= western["share_of_daily_budget_pct"] <= 180.0
    print(f"G2 (mixed Western):    climate share = {western['share_of_daily_budget_pct']:.1f}% "
          f"→ {'PASS' if g2_pass else 'FAIL'} (80-180 %)")

    # ------------------------------------------------------------------
    # G3: beef-heavy day — climate share > 200 %
    # ------------------------------------------------------------------
    beef = next(r for r in results["beef_heavy_day"]["shares"]
                if r["key"] == "climate_change")
    g3_pass = beef["share_of_daily_budget_pct"] > 200.0
    print(f"G3 (beef-heavy):       climate share = {beef['share_of_daily_budget_pct']:.1f}% "
          f"→ {'PASS' if g3_pass else 'FAIL'} (> 200 %)")

    # ------------------------------------------------------------------
    # G4: response shape contract — 9 rows, 3 available, 6 unavailable,
    #     all required keys present.
    # ------------------------------------------------------------------
    shape_errors: list[str] = []
    sample = results["mixed_western_day"]
    if sample["n_total"] != 9:
        shape_errors.append(f"n_total expected 9, got {sample['n_total']}")
    if sample["n_covered"] != 3:
        shape_errors.append(f"n_covered expected 3, got {sample['n_covered']}")
    seen_keys: set[str] = set()
    for row in sample["shares"]:
        for required in ("key", "label", "control_variable", "unit", "available",
                         "global_boundary_per_year", "global_boundary_source",
                         "current_food_system_contribution"):
            if required not in row:
                shape_errors.append(f"row {row.get('key', '?')} missing {required}")
        seen_keys.add(row["key"])
        if row["available"]:
            for required in ("recipe_midpoint_key", "meal_value",
                             "per_capita_daily_budget", "share_of_daily_budget_pct",
                             "method_note"):
                if required not in row:
                    shape_errors.append(
                        f"available row {row['key']} missing {required}")
        else:
            if "reason" not in row:
                shape_errors.append(f"unavailable row {row['key']} missing reason")
    expected_keys = {
        "climate_change", "land_use", "water_consumption",
        "biosphere_integrity_hanpp", "stratospheric_ozone_n2o",
        "ocean_acidification", "nitrogen_surplus", "phosphorus_loss",
        "novel_entities_pesticides",
    }
    missing = expected_keys - seen_keys
    if missing:
        shape_errors.append(f"missing boundary keys: {sorted(missing)}")
    if "citation" not in sample or "method_note" not in sample:
        shape_errors.append("response missing top-level citation/method_note")

    # Explanation builder smoke for all 3 audiences.
    for user_type in ("individual", "researcher", "policy"):
        exp = build_planetary_explanations(sample, user_type)
        for required in ("title", "headline", "message", "mandatory_caveat"):
            if required not in exp:
                shape_errors.append(f"{user_type} explanation missing {required}")

    g4_pass = len(shape_errors) == 0
    print(f"G4 (response shape):   "
          f"{'PASS' if g4_pass else 'FAIL'} "
          f"(n_covered={sample['n_covered']}/{sample['n_total']}, "
          f"shape errors={len(shape_errors)})")
    if shape_errors:
        for err in shape_errors:
            print(f"     - {err}")

    print()
    print("=" * 70)
    n_passed = sum([g1_pass, g2_pass, g3_pass, g4_pass])
    print(f"PLANETARY-1 smoke: {n_passed}/4 gates pass")
    print("=" * 70)
    return 0 if n_passed == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
