"""CNFRecall24h GOLDEN regression harness (AI-MATCH-2, 2026-05-24).

Companion to ``_smoke_cnf_recall_24h.py`` (the directional 5-pattern smoke).
This harness pins a SPECIFIC aggregated 24-h recall captured against
gpt-4.1-mini at temperature=0 on 2026-05-24. It catches silent LLM drift
that the directional panels would miss (e.g. OpenAI quietly updates the
snapshot, or someone tweaks the SYSTEM_PROMPT of the per-meal decomposer).

Pin choice rationale (per AI-MATCH-2 plan §risk #9):
  - 3-meal pinned day (breakfast + lunch + dinner), NOT 6 meals — less
    LLM surface area for drift to accumulate.
  - All three meals are also pinned in
    `_smoke_cnf_recipe_decomposer_golden.py` so the per-meal anchors are
    already independently stable. This harness pins the AGGREGATE of those
    three meals.
  - Slightly looser tolerances than the per-dish golden harness:
    - per-FoodID mass drift ±15 g (vs ±10 g per dish) — accumulated
      cooking-fat-rule overshoot across 3 meals
    - count drift ±2 (vs ±1 per dish) — same reason
    - kcal drift ±15 % — robust against per-ingredient kcal-density
      variation when the LLM picks a slightly different CNF variant

GATES (at the recall / aggregate level):
  G1 matched=True at the recall level (all 3 meals decomposed)
  G2 aggregated FoodID-set overlap ≥ 70 % of baseline FoodIDs
  G3 aggregated ingredient-count drift   |observed - baseline| ≤ 2
  G4 aggregated resolved-mass drift       |observed - baseline| ≤ 15 g
  G5 per-FoodID mass drift                |observed - baseline| ≤ 15 g per overlapping FoodID
  G6 estimated_daily_kcal drift           |observed - baseline| / baseline ≤ 15 %

If this fails after an LLM model update, the appropriate response is to
investigate (re-pin if the new output is equally reasonable, or treat as a
regression). Pin updates require explicit human review; don't auto-bump.

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_cnf_recall_24h_golden.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-cnf-recall-24h-golden'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass


# --- Pinned baseline ------------------------------------------------------
# Captured 2026-05-24 against gpt-4.1-mini at temperature=0 + AI-MATCH-1.x
# system prompt + AI-MATCH-2 orchestrator with snack-fallback active.
# DO NOT modify without explicit human review.

@dataclass
class GoldenMeal:
    occasion: str
    dish_name: str
    total_mass_g: float


@dataclass
class GoldenRecall:
    name: str
    meals: List[GoldenMeal]
    # Aggregated daily ingredient list — CNF FoodID → mass_g summed across meals.
    expected_aggregate: Dict[int, float] = field(default_factory=dict)
    expected_resolved_mass_g: float = 0.0
    expected_daily_kcal: float = 0.0
    captured_at: str = '2026-05-24'


GOLDEN: GoldenRecall = GoldenRecall(
    name='breakfast_lunch_dinner_canonical_350g',
    meals=[
        GoldenMeal('breakfast', 'peanut butter sandwich',    80),
        GoldenMeal('lunch',     'scrambled eggs with toast', 150),
        GoldenMeal('dinner',    'grilled cheese sandwich',   120),
    ],
    # FoodID → aggregated mass_g across all three meals.
    # Re-baselined 2026-05-28 after the cooked-form prompt + force_decompose: the
    # cooked-form rule now resolves scrambled eggs to the COOKED entry (133, was raw
    # 125), and peanut butter to 3399 (was 3414). Food-id set + kcal are stable;
    # the toasted-vs-untoasted bread mass split (3732 / 4066) is mildly LLM-noisy.
    expected_aggregate={
        3732:   120.0,   # Bread, white, commercial, toasted
        133:     90.0,   # Egg, chicken, whole, cooked, scrambled or omelet
        4066:    50.0,   # Bread, white, commercial
        7005:    40.0,   # Cheese, processed product, cheddar, slices
        3399:    28.0,   # Peanut butter, smooth type
        118:     14.0,   # Butter, regular
    },
    expected_resolved_mass_g=342.0,
    expected_daily_kcal=986.0,
)


# --- Gate tolerances -----------------------------------------------------

INGREDIENT_OVERLAP_MIN  = 0.70    # G2: ≥ 70 % of baseline FoodIDs present
COUNT_DRIFT_MAX         = 2       # G3: ±2 ingredients (looser than per-dish)
TOTAL_MASS_DRIFT_G_MAX  = 15.0    # G4: ±15 g total resolved (looser than per-dish ±10)
PER_FOOD_MASS_DRIFT_G   = 15.0    # G5: ±15 g per overlapping FoodID
KCAL_DRIFT_FRAC_MAX     = 0.15    # G6: ±15 % of baseline kcal


# --- Runner ---------------------------------------------------------------

@dataclass
class GoldenCheck:
    expected_count: int
    observed_count: int
    expected_food_ids: Set[int]
    observed_food_ids: Set[int]
    overlap: float
    expected_resolved_mass_g: float
    observed_resolved_mass_g: float
    expected_kcal: float
    observed_kcal: float
    g1_recall_matched: bool
    g2_overlap: bool
    g3_count: bool
    g4_total_mass: bool
    g5_per_food_mass: bool
    g6_kcal_drift: bool
    overall_pass: bool
    detail: str


def run_golden(orchestrator) -> GoldenCheck:
    from api.services.cnf_recall_24h import MealEntry
    meals = [MealEntry(m.occasion, m.dish_name, m.total_mass_g) for m in GOLDEN.meals]
    try:
        # force_decompose: pin the DECOMPOSITION path, not the catalog shortcut.
        r = orchestrator.recall(meals, user_type='researcher', force_decompose=True)
    except Exception as exc:  # noqa: BLE001
        return GoldenCheck(
            expected_count=len(GOLDEN.expected_aggregate), observed_count=0,
            expected_food_ids=set(GOLDEN.expected_aggregate), observed_food_ids=set(),
            overlap=0.0,
            expected_resolved_mass_g=GOLDEN.expected_resolved_mass_g,
            observed_resolved_mass_g=0.0,
            expected_kcal=GOLDEN.expected_daily_kcal, observed_kcal=0.0,
            g1_recall_matched=False, g2_overlap=False, g3_count=False,
            g4_total_mass=False, g5_per_food_mass=False, g6_kcal_drift=False,
            overall_pass=False, detail=f'exception:{exc!r}',
        )

    obs_aggregate = {int(i['food_id']): float(i['mass_g'])
                     for i in r.aggregated_daily_ingredients}
    exp_ids: Set[int] = set(GOLDEN.expected_aggregate)
    obs_ids: Set[int] = set(obs_aggregate)
    overlap = len(exp_ids & obs_ids) / len(exp_ids) if exp_ids else 1.0

    # Gates
    g1 = r.matched
    g2 = overlap >= INGREDIENT_OVERLAP_MIN
    g3 = abs(len(obs_aggregate) - len(GOLDEN.expected_aggregate)) <= COUNT_DRIFT_MAX
    g4 = abs(r.total_resolved_mass_g - GOLDEN.expected_resolved_mass_g) <= TOTAL_MASS_DRIFT_G_MAX
    overlaps = exp_ids & obs_ids
    g5 = all(
        abs(obs_aggregate[fid] - GOLDEN.expected_aggregate[fid]) <= PER_FOOD_MASS_DRIFT_G
        for fid in overlaps
    ) if overlaps else False
    kcal_drift = (
        abs(r.estimated_daily_kcal - GOLDEN.expected_daily_kcal)
        / GOLDEN.expected_daily_kcal
        if GOLDEN.expected_daily_kcal > 0 else 1.0
    )
    g6 = kcal_drift <= KCAL_DRIFT_FRAC_MAX

    overall = g1 and g2 and g3 and g4 and g5 and g6
    details = []
    if not g1: details.append(f'recall not matched (fallback={r.fallback_reason})')
    if not g2: details.append(f'overlap={overlap:.2f}<{INGREDIENT_OVERLAP_MIN}')
    if not g3: details.append(f'count drift {abs(len(obs_aggregate)-len(GOLDEN.expected_aggregate))}>{COUNT_DRIFT_MAX}')
    if not g4: details.append(f'mass drift {abs(r.total_resolved_mass_g - GOLDEN.expected_resolved_mass_g):.1f}g>{TOTAL_MASS_DRIFT_G_MAX}g')
    if not g5: details.append(f'per-food mass drift exceeds {PER_FOOD_MASS_DRIFT_G}g')
    if not g6: details.append(f'kcal drift {kcal_drift:.1%}>{KCAL_DRIFT_FRAC_MAX:.0%}')
    if not details: details.append('ok')

    return GoldenCheck(
        expected_count=len(GOLDEN.expected_aggregate),
        observed_count=len(obs_aggregate),
        expected_food_ids=exp_ids,
        observed_food_ids=obs_ids,
        overlap=overlap,
        expected_resolved_mass_g=GOLDEN.expected_resolved_mass_g,
        observed_resolved_mass_g=r.total_resolved_mass_g,
        expected_kcal=GOLDEN.expected_daily_kcal,
        observed_kcal=r.estimated_daily_kcal,
        g1_recall_matched=g1, g2_overlap=g2, g3_count=g3,
        g4_total_mass=g4, g5_per_food_mass=g5, g6_kcal_drift=g6,
        overall_pass=overall,
        detail='; '.join(details),
    )


def main() -> int:
    print('CNFRecall24h GOLDEN regression harness '
          f'(AI-MATCH-2, 1 pinned daily-eating pattern)')
    print('=' * 100)
    from api.services.cnf_recall_24h import get_default_recall_24h
    orchestrator = get_default_recall_24h()
    print(f'LLM client wired: '
          f'{"yes" if orchestrator.decomposer.chat_json_client else "NO (degraded)"}')
    print(f'Pin date: {GOLDEN.captured_at}; pinned day: {GOLDEN.name}')
    print()

    c = run_golden(orchestrator)
    mark = '[ OK ]' if c.overall_pass else '[FAIL]'
    gates = (f'g1={"+" if c.g1_recall_matched else "-"} '
             f'g2={"+" if c.g2_overlap else "-"} '
             f'g3={"+" if c.g3_count else "-"} '
             f'g4={"+" if c.g4_total_mass else "-"} '
             f'g5={"+" if c.g5_per_food_mass else "-"} '
             f'g6={"+" if c.g6_kcal_drift else "-"}')
    print(f'  {mark}  {GOLDEN.name:<48s}')
    print(f'         overlap={c.overlap:.0%}  '
          f'count={c.observed_count}/{c.expected_count}  '
          f'mass={c.observed_resolved_mass_g:.0f}/{c.expected_resolved_mass_g:.0f}g  '
          f'kcal={c.observed_kcal:.0f}/{c.expected_kcal:.0f}')
    print(f'         {gates}')
    if not c.overall_pass:
        print(f'         FAIL: {c.detail}')
        new_ids = c.observed_food_ids - c.expected_food_ids
        missing_ids = c.expected_food_ids - c.observed_food_ids
        if new_ids:
            print(f'         new FoodIDs: {sorted(new_ids)}')
        if missing_ids:
            print(f'         missing FoodIDs: {sorted(missing_ids)}')

    print()
    print('=' * 100)
    print(f'Golden recall pin: PASS={1 if c.overall_pass else 0}/1')

    out_path = os.path.join(_HERE, '_smoke_cnf_recall_24h_golden_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness': 'CNFRecall24h golden regression (AI-MATCH-2)',
            'pin_date': GOLDEN.captured_at,
            'pin_model': 'gpt-4.1-mini @ temperature=0',
            'pin_name':  GOLDEN.name,
            'totals': {'pass': 1 if c.overall_pass else 0, 'total': 1},
            'result': {
                'overlap': round(c.overlap, 2),
                'observed_count': c.observed_count,
                'expected_count': c.expected_count,
                'observed_resolved_mass_g': round(c.observed_resolved_mass_g, 1),
                'expected_resolved_mass_g': round(c.expected_resolved_mass_g, 1),
                'observed_kcal': round(c.observed_kcal, 1),
                'expected_kcal': round(c.expected_kcal, 1),
                'observed_food_ids': sorted(c.observed_food_ids),
                'expected_food_ids': sorted(c.expected_food_ids),
                'gates': {
                    'g1_recall_matched': c.g1_recall_matched,
                    'g2_overlap':        c.g2_overlap,
                    'g3_count':          c.g3_count,
                    'g4_total_mass':     c.g4_total_mass,
                    'g5_per_food_mass':  c.g5_per_food_mass,
                    'g6_kcal_drift':     c.g6_kcal_drift,
                },
                'overall_pass': c.overall_pass,
                'detail': c.detail,
            },
        }, f, indent=2)
    print(f'Results JSON: {out_path}')
    return 0 if c.overall_pass else 1


if __name__ == '__main__':
    sys.exit(main())
