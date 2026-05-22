"""Defensibility audit v2 — per-cell MARE against P&N + M&H blue-water.

What changed from v1 (per user critique):
  1. PASS / WEAK / FAIL replaced by per-cell MARE = |actual - target|/target
     against a single literature CENTRAL VALUE (not a 10x-wide band). A 12x
     band "passes" almost anything and won't survive a reviewer who knows
     beef LCA; MARE forces the comparison to be quantitative.
  2. Water re-grounded against MEKONNEN & HOEKSTRA 2012 BLUE-WATER-ONLY
     CONSUMPTIVE values, not the green+blue+grey total footprint. ReCiPe
     "Water consumption" is consumptive blue water (Hoekstra–Pfister
     lineage); using the total footprint inflates the target ~10-20x and
     was a real grounding error in v1.
  3. Acidification + eutrophication EXPLICITLY marked as
     UNIT_INCOMPATIBLE: P&N reports a single kg SO2-eq aggregate
     (acidification) and a single kg PO4-eq aggregate (eutrophication),
     whereas ReCiPe wants terrestrial acidification (kg SO2-eq, different
     model) and split freshwater-P / marine-N. Magnitude-OOM check only;
     not a unit-correct target.
  4. The remaining 13 ReCiPe categories (toxicities, ecotoxicities, both
     ozone-formation pathways, ionising radiation, PM, resource scarcity)
     stay UNGROUNDED — no per-food-group numerical literature target in
     our `literature_extractions.md`; defensible source would be licensed
     Agribalyse-LCI-re-scored-under-ReCiPe group aggregates (v2 work).

Grading by per-cell MARE:
  EXCELLENT   MARE < 0.25  (within 25%)
  ACCEPTABLE  MARE < 0.50
  WEAK        MARE < 1.0   (factor 2)
  FAIL        MARE >= 1.0  (>2x off)
"""
from __future__ import annotations

import os, sys, collections
_HERE = os.path.abspath('.')
for sub in ("environmental_impact_model", "dish_cnf_db_pipeline"):
    p = os.path.join(_HERE, sub)
    if p not in sys.path: sys.path.insert(0, p)
import dish_project.env_bootstrap  # noqa
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_project.settings")
import django; django.setup()

from environmental_impact_model.src.cnf_integrator import get_cnf_integrator
integrator = get_cnf_integrator(); integrator.initialize()


# --- Central-value targets --------------------------------------------------
# Per-100g-food. Each entry is (target_central, source_note). MARE is computed
# as |actual - target|/target.

# GWP central values: P&N Fig. 1 panel means × protein-conversion factor
# (Poore & Nemecek, Science 360:987-992, 2018, Fig. 1 panels A-F).
GWP_TARGETS = {
    # P&N Panel A: beef-herd mean 50, dairy-herd mean 17 (kg CO2-eq/100g protein).
    # CNF beef products span lean cooked beef (~26 g protein/100 g food), ground
    # beef (~20), processed beef (~12). Use representative 0.20 mid-blend.
    # Beef-herd-weighted (Canada beef is ~50/50 cow-calf/dairy-cull): mean of
    # 50 and 17 = ~33.5/100g protein × 0.20 = ~6.7 kg CO2-eq/100g food.
    "Beef Products":                    (6.7,  "P&N beef mean 33.5/100g protein x 0.20"),
    "Pork Products":                    (1.5,  "P&N pig mean 7.6/100g protein x 0.20"),
    "Poultry Products":                 (1.3,  "P&N poultry mean 5.7/100g protein x 0.22"),
    # Fish farmed mean 6.0/100g protein × 0.18 protein = 1.08.
    "Finfish and Shellfish Products":   (1.1,  "P&N farmed fish mean 6.0/100g protein x 0.18"),
    # Cheese mean 11 × 0.22 = ~2.4 (cheese) blended with milk 3.2/L = 0.32/100g
    # and egg 4.2 × 0.13 = 0.55 → group-weighted central ~1.0.
    "Dairy and Egg Products":           (1.0,  "P&N cheese 2.4 / milk 0.32 / egg 0.55 blended"),
    # Veg panel: tomato mean 2.1, brassica 0.5, root 0.4 (per kg) → midpoint
    # ~1.0/kg = 0.10/100g.
    "Vegetables and Vegetable Products":(0.10, "P&N veg panel midpoint ~1.0/kg"),
    # Fruit panel: berries 1.5, banana 0.9, apple 0.4, citrus 0.4 → ~0.8/kg.
    "Fruits and fruit juices":          (0.08, "P&N fruit panel midpoint ~0.8/kg"),
    # Grain panel per 1000 kcal: wheat 0.6, rice 1.2, oat 0.9 → ~0.9/1000 kcal.
    # Cereals ~350 kcal/100g → 0.9 × 0.35 = 0.32.
    "Cereals, Grains and Pasta":        (0.32, "P&N grain panel 0.9/1000 kcal x 350 kcal/100g"),
    # Legumes per 100g protein: peas 0.4, other pulses 0.8, lentils ~0.9 → ~0.6.
    # Cooked legumes ~9g protein/100g → 0.6 × 0.09 = 0.054.
    "Legumes and Legume Products":      (0.054, "P&N pulses 0.6/100g protein x 0.09"),
    # Nuts: P&N mean 0.3/100g protein, but very wide variance (-2.2 to 0.3);
    # nuts ~20g protein/100g → 0.06.
    "Nuts and Seeds":                   (0.06, "P&N nuts mean 0.3/100g protein x 0.20"),
}

# Land use central values: P&N Fig. 1 panel means × protein-conversion factor.
LAND_TARGETS = {
    "Beef Products":                    (33.0,  "P&N beef-herd 164/100g protein x 0.20"),
    "Pork Products":                    (2.2,   "P&N pig 11/100g protein x 0.20"),
    "Poultry Products":                 (1.6,   "P&N poultry 7.1/100g protein x 0.22"),
    "Finfish and Shellfish Products":   (0.67,  "P&N farmed fish 3.7/100g protein x 0.18"),
    "Dairy and Egg Products":           (9.0,   "P&N cheese 41 x 0.22 (cheese) / milk 8.9/L blended"),
    "Vegetables and Vegetable Products":(0.055, "P&N veg panel 0.4-0.8/kg midpoint = 0.055/100g"),
    "Fruits and fruit juices":          (0.14,  "P&N fruit panel 1.4/kg midpoint"),
    "Cereals, Grains and Pasta":        (0.49,  "P&N wheat 1.4/1000 kcal x 350 kcal/100g"),
    "Legumes and Legume Products":      (0.49,  "P&N pulses 5.4/100g protein x 0.09"),
    "Nuts and Seeds":                   (1.58,  "P&N nuts 7.9/100g protein x 0.20"),
}

# WATER CONSUMPTION central values — RE-GROUNDED against Mekonnen & Hoekstra
# 2012 (Ecosystems 15:401-415) BLUE-WATER-ONLY consumptive footprints, NOT
# the green+blue+grey total. ReCiPe 2016 "Water consumption" uses the
# Hoekstra-Pfister consumptive blue-water definition (Huijbregts 2017
# Table 1; uses Döll & Siebert 2002 and Hoekstra & Mekonnen 2012 = the
# BLUE component of M&H total footprint).
#
# M&H 2012 Table 3 (animal) and M&H 2011 (Hydrol Earth Syst Sci 15:1577,
# Table 3, crops) blue-water global averages, in L blue / kg product:
#   Beef cattle (mixed)      550-683        => 0.055-0.068 m3/100g food
#   Pork                     459            => 0.046
#   Chicken                  313            => 0.031
#   Sheep/goat               522            => 0.052
#   Milk                      86            => 0.009
#   Eggs                     244            => 0.024
#   Cheese                   413            => 0.041
#   Wheat                    342            => 0.034
#   Rice                     341            => 0.034
#   Maize                     81            => 0.008
#   Potato                    33            => 0.003
#   Apple                     13            => 0.001
#   Tomato                    63            => 0.006
#   Onion                     78            => 0.008
#   Pulses (mixed)           ~400-800       => 0.040-0.080
#   Almonds (atypical)       ~3,000-16,000  => 0.30-1.60 (almonds are an outlier)
WATER_TARGETS = {
    "Beef Products":                    (0.062, "M&H 2012 blue-water beef cattle ~620 L/kg"),
    "Pork Products":                    (0.046, "M&H 2012 blue-water pork ~459 L/kg"),
    "Poultry Products":                 (0.031, "M&H 2012 blue-water chicken ~313 L/kg"),
    # Wild marine fish ~0; farmed fish blue water mostly feed-crop blue water,
    # small per 100g. Use mid 0.005.
    "Finfish and Shellfish Products":   (0.005, "Wild fish near 0; farmed feed-crop blue water small"),
    # Dairy mix: milk 0.009, cheese 0.041, egg 0.024 → blended ~0.020.
    "Dairy and Egg Products":           (0.020, "M&H 2012 blue: milk 0.009 / egg 0.024 / cheese 0.041 blended"),
    # Veg mix: 0.003-0.010 → ~0.006.
    "Vegetables and Vegetable Products":(0.006, "M&H 2011 blue: potato 0.003 / tomato 0.006 / onion 0.008"),
    # Fruit: apple 0.001, banana ~0, mid ~0.005 (citrus, berries higher).
    "Fruits and fruit juices":          (0.005, "M&H 2011 blue: apple 0.001 / banana ~0, mid ~0.005"),
    # Grain mix: wheat 0.034 / rice 0.034 / maize 0.008 → ~0.025.
    "Cereals, Grains and Pasta":        (0.025, "M&H 2011 blue: wheat 0.034 / rice 0.034 / maize 0.008 mid"),
    # Pulses blue ~0.04-0.08 → mid 0.060.
    "Legumes and Legume Products":      (0.060, "M&H 2011 blue: pulses ~400-800 L/kg mid 600"),
    # Nuts: almonds are extreme; mixed nut basket ~0.5-1.0 m3/100g blue.
    "Nuts and Seeds":                   (0.80,  "M&H blue: almond ~0.3-1.6 m3/100g; mixed nuts ~0.5-1.0"),
}

# ReCiPe categories that are UNIT-INCOMPATIBLE with P&N's aggregate
# acidification (kg SO2-eq) and aggregate eutrophication (kg PO4-eq).
# We keep them in the report as a magnitude-OOM cross-check only.
P_AND_N_UNIT_INCOMPATIBLE_CATEGORIES = {
    "Terrestrial acidification",
    "Freshwater eutrophication",
    "Marine eutrophication",
}

# ReCiPe categories with NO per-food-group numerical target available in
# `literature_extractions.md` on any basis (P&N or otherwise). Defensible
# source: licensed Agribalyse-LCI-re-scored-under-ReCiPe (v2).
UNGROUNDED_CATEGORIES = [
    "Fine particulate matter formation",
    "Fossil resource scarcity",
    "Mineral resource scarcity",
    "Human carcinogenic toxicity",
    "Human non-carcinogenic toxicity",
    "Terrestrial ecotoxicity",
    "Freshwater ecotoxicity",
    "Marine ecotoxicity",
    "Ionizing radiation",
    "Stratospheric ozone depletion",
    "Ozone formation, Human health",
    "Ozone formation, Terrestrial ecosystems",
]


def mare(actual, target):
    if actual is None or target is None or target == 0: return float("inf")
    return abs(actual - target) / target


def grade(m):
    if m < 0.25: return "EXCELLENT"
    if m < 0.50: return "ACCEPTABLE"
    if m < 1.00: return "WEAK"
    return "FAIL"


def find_representative_food(food_group: str):
    fn = integrator.get_dataframe("food_name")
    fg = integrator.get_dataframe("food_group")
    if fn.empty or fg.empty: return None
    matches = fg[fg["FoodGroupName"] == food_group]
    if matches.empty: return None
    fgid = int(matches.iloc[0]["FoodGroupID"])
    foods = fn[fn["FoodGroupID"] == fgid]
    if foods.empty: return None
    return int(foods.iloc[0]["FoodID"])


def main() -> int:
    target_tables = {
        "Global warming":    GWP_TARGETS,
        "Land use":          LAND_TARGETS,
        "Water consumption": WATER_TARGETS,
    }

    food_groups = list(GWP_TARGETS.keys())
    print(f"Defensibility audit v2 (per-cell MARE)")
    print(f"Food groups under test: {len(food_groups)}")
    print()
    summary = collections.Counter()
    grounded_rows: list = []

    for group in food_groups:
        food_id = find_representative_food(group)
        if food_id is None:
            print(f"[skip] No CNF food found for: {group}")
            continue
        factors = integrator.get_environmental_impact_factors(food_id)
        print(f"=== {group}  (representative CNF FoodID={food_id}) ===")
        for category, targets in target_tables.items():
            actual = factors.get(category)
            target, note = targets[group]
            m = mare(actual, target)
            verdict = grade(m)
            summary[verdict] += 1
            actual_str = f"{actual:.5g}" if isinstance(actual, (int, float)) else str(actual)
            print(f"  [{verdict:<10}] {category:<22} actual={actual_str:<10} target={target:<10} MARE={m:.2f}  ({note})")
            grounded_rows.append((group, category, actual, target, m, verdict, note))
        # P&N unit-incompatible (acidification + eutrophications) — show only.
        for category in sorted(P_AND_N_UNIT_INCOMPATIBLE_CATEGORIES):
            actual = factors.get(category)
            actual_str = f"{actual:.5g}" if isinstance(actual, (int, float)) else str(actual)
            summary["UNIT_INCOMPATIBLE"] += 1
            print(f"  [UNIT_INC ] {category:<42} actual={actual_str}  (P&N unit aggregate differs from ReCiPe)")
        # Truly ungrounded categories.
        for category in UNGROUNDED_CATEGORIES:
            actual = factors.get(category)
            actual_str = f"{actual:.5g}" if isinstance(actual, (int, float)) else str(actual)
            summary["UNGROUNDED"] += 1
            print(f"  [UNGROUND ] {category:<42} actual={actual_str}")
        print()

    print("=" * 72)
    print("Summary across cells:")
    for verdict, count in sorted(summary.items()):
        print(f"  {verdict:<18}: {count}")
    print()

    # Tabular view of grounded MAREs by category for the §4.2 reframe.
    print("Grounded-cell MARE table (lower = better):")
    print(f"  {'Group':<35} {'GWP':>8} {'Land':>8} {'Water':>8}")
    by_group_cat: dict = {}
    for g, c, a, t, m, v, n in grounded_rows:
        by_group_cat[(g, c)] = (m, v)
    for group in food_groups:
        gwp_m = by_group_cat.get((group, "Global warming"), (None, ""))[0]
        land_m = by_group_cat.get((group, "Land use"), (None, ""))[0]
        water_m = by_group_cat.get((group, "Water consumption"), (None, ""))[0]
        def fmt(x): return f"{x:>8.2f}" if x is not None and x != float('inf') else f"{'inf':>8}"
        print(f"  {group:<35} {fmt(gwp_m)} {fmt(land_m)} {fmt(water_m)}")
    print()

    # FAIL / WEAK cells worth attention.
    print("Cells with MARE >= 0.5 (ACCEPTABLE / WEAK / FAIL):")
    any_off = False
    for g, c, a, t, m, v, n in grounded_rows:
        if m >= 0.5:
            any_off = True
            print(f"  [{v}] {g:<35} {c:<22} actual={a}  target={t}  MARE={m:.2f}")
    if not any_off:
        print("  (none)")

    # ---------------------------------------------------------------------- #
    # INDEPENDENT CROSS-CHECK against Stylianou et al. 2021 (Nat Food         #
    # 2:616-627), IMPACT World+ method, per-serving means (lit. extractions   #
    # C15 lines 1659, 1754). Different LCIA method + different LCI database  #
    # (WFLDB / Agri-footprint) from P&N. Disagreement here flags METHOD gap, #
    # not a code bug, but should be reported so reviewers can see it.        #
    # ---------------------------------------------------------------------- #
    print()
    print("=" * 72)
    print("INDEPENDENT cross-check: Stylianou 2021 GWP per serving (IMPACT World+)")
    print("=" * 72)
    # (food_group, stylianou_per_100g_food, derivation_note)
    stylianou_gwp = [
        ("Beef Products",                  2.94,
         "S2021 'beef ~2.5 kg CO2-eq/serving' / 85g serving = 2.94/100g"),
        ("Poultry Products",               0.35,
         "S2021 'poultry ~0.3 kg CO2-eq/serving' / 85g = 0.35/100g"),
        ("Dairy and Egg Products",         1.07,
         "S2021 'cheese ~0.3 kg CO2-eq/serving' / 28g cheese = 1.07/100g (cheese-specific)"),
        ("Dairy and Egg Products",         0.19,
         "S2021 'fluid milk 0.47/244g serving' = 0.19/100g (milk-specific; very different from cheese)"),
    ]
    for group, sty_target, note in stylianou_gwp:
        food_id = find_representative_food(group)
        actual = integrator.get_environmental_impact_factors(food_id).get("Global warming")
        m = mare(actual, sty_target)
        v = grade(m)
        actual_str = f"{actual:.4g}" if isinstance(actual, (int, float)) else str(actual)
        print(f"  [{v:<10}] {group:<35} actual={actual_str:<6} sty_target={sty_target:<6} MARE={m:.2f}")
        print(f"             {note}")
    print()
    print("Note: Stylianou uses IMPACT World+ / WFLDB; P&N uses meta-analysis of >570")
    print("studies. Cross-method disagreement of 2-4x is normal (the same EF-vs-ReCiPe gap")
    print("of §3.2). Values that fail this check are NOT necessarily wrong — they are")
    print("anchored to P&N rather than Stylianou. Reviewers should expect this; document")
    print("the lineage in §3.2 / §7 so the choice is explicit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
