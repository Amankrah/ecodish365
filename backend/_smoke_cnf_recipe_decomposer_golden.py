"""CNFRecipeDecomposer GOLDEN regression harness (AI-MATCH-1.x, 2026-05-23).

Companion to ``_smoke_cnf_recipe_decomposer.py`` (the directional 15-recipe
panel). This harness pins SPECIFIC ingredient sets + masses for 3 stable
recipes captured against gpt-4.1-mini at temperature=0 on 2026-05-23. It
catches silent LLM drift (e.g. OpenAI quietly updates the snapshot, or
someone tweaks the system prompt) that the directional panels would miss.

GATES (per recipe):
  G1 ingredient-set overlap   ≥ 70 % of baseline FoodIDs present
  G2 ingredient-count drift   |observed - baseline| ≤ 1
  G3 resolved-mass drift      |observed - baseline| ≤ 10 g
  G4 per-FoodID mass drift    |observed - baseline| ≤ 10 g per overlapping ingredient
  G5 matched=True             ALL gates above + the recipe must report matched=True
  G6 unresolved_description present (non-empty)  — verifies AI-MATCH-1.x field landed

If this fails after an LLM model update, the appropriate response is to
investigate (re-pin if the new output is equally reasonable, or treat as a
regression). Pin updates require explicit human review; don't auto-bump.

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_cnf_recipe_decomposer_golden.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-cnf-recipe-decomposer-golden'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()


# --- Pinned baselines ---------------------------------------------------
# Captured 2026-05-23 against gpt-4.1-mini at temperature=0 + AI-MATCH-1.x
# system prompt (cautious-defaults nudge active). DO NOT modify without
# explicit human review — these are the golden anchors against drift.

@dataclass
class GoldenRecipe:
    dish_name: str
    total_mass_g: float
    expected_ingredients: Dict[int, float]   # CNF FoodID → mass_g (baseline)
    expected_resolved_mass_g: float          # sum of expected ingredient masses
    expected_unresolved_mass_g: float
    min_confidence: float = 0.7
    captured_at: str = '2026-05-23'


GOLDEN_PANEL: List[GoldenRecipe] = [
    GoldenRecipe(
        dish_name='peanut butter sandwich',
        total_mass_g=80.0,
        expected_ingredients={
            4066: 50.0,    # Bread, white, commercial
            3399: 25.0,    # Peanut butter, smooth type, fat, sugar and salt added
                           # (rebaselined 2026-05-28: the CNF 2026 embeddings rank this
                           #  interchangeable smooth peanut butter above 3414)
        },
        expected_resolved_mass_g=75.0,
        expected_unresolved_mass_g=5.0,
        min_confidence=0.8,
    ),
    GoldenRecipe(
        dish_name='scrambled eggs with toast',
        total_mass_g=150.0,
        expected_ingredients={
            125:  90.0,    # Egg, chicken, whole, fresh or frozen, raw
            3732: 50.0,    # Bread, white, commercial, toasted
        },
        expected_resolved_mass_g=140.0,
        expected_unresolved_mass_g=10.0,
        min_confidence=0.7,
    ),
    GoldenRecipe(
        dish_name='grilled cheese sandwich',
        total_mass_g=120.0,
        expected_ingredients={
            4066:    70.0, # Bread, white, commercial
            7005:  30.0, # Cheese, processed product, cheddar, slices
            118:     10.0, # Butter, regular
        },
        expected_resolved_mass_g=110.0,
        expected_unresolved_mass_g=10.0,
        min_confidence=0.8,
    ),
]


# Gate tolerances
INGREDIENT_OVERLAP_MIN = 0.70          # G1: ≥ 70 % of baseline FoodIDs present
COUNT_DRIFT_MAX        = 1             # G2: ±1 ingredient
TOTAL_MASS_DRIFT_G_MAX = 10.0          # G3: ±10 g of resolved mass
PER_FOOD_MASS_DRIFT_G  = 10.0          # G4: ±10 g per overlapping ingredient


# --- Runner -------------------------------------------------------------

@dataclass
class GoldenCheck:
    dish_name: str
    expected_count: int
    observed_count: int
    expected_food_ids: Set[int]
    observed_food_ids: Set[int]
    overlap: float
    expected_resolved_mass_g: float
    observed_resolved_mass_g: float
    g1_overlap: bool
    g2_count: bool
    g3_total_mass: bool
    g4_per_food_mass: bool
    g5_matched: bool
    g6_has_unresolved_description: bool
    overall_pass: bool
    detail: str


def run_golden(decomposer) -> List[GoldenCheck]:
    out: List[GoldenCheck] = []
    for r in GOLDEN_PANEL:
        try:
            d = decomposer.decompose(r.dish_name, r.total_mass_g)
        except Exception as exc:  # noqa: BLE001
            out.append(GoldenCheck(
                dish_name=r.dish_name,
                expected_count=len(r.expected_ingredients), observed_count=0,
                expected_food_ids=set(r.expected_ingredients), observed_food_ids=set(),
                overlap=0.0,
                expected_resolved_mass_g=r.expected_resolved_mass_g,
                observed_resolved_mass_g=0.0,
                g1_overlap=False, g2_count=False, g3_total_mass=False,
                g4_per_food_mass=False, g5_matched=False,
                g6_has_unresolved_description=False,
                overall_pass=False, detail=f'exception: {exc!r}',
            ))
            continue
        obs_ings = {i.food_id: i.mass_g for i in d.ingredients}
        exp_ids: Set[int] = set(r.expected_ingredients)
        obs_ids: Set[int] = set(obs_ings)
        overlap = len(exp_ids & obs_ids) / len(exp_ids) if exp_ids else 1.0

        # Gates
        g1 = overlap >= INGREDIENT_OVERLAP_MIN
        g2 = abs(len(obs_ings) - len(r.expected_ingredients)) <= COUNT_DRIFT_MAX
        g3 = abs(d.resolved_mass_g - r.expected_resolved_mass_g) <= TOTAL_MASS_DRIFT_G_MAX
        # G4: for every overlapping ingredient, mass within ±10g of baseline
        g4_overlaps = exp_ids & obs_ids
        g4 = all(
            abs(obs_ings[fid] - r.expected_ingredients[fid]) <= PER_FOOD_MASS_DRIFT_G
            for fid in g4_overlaps
        ) if g4_overlaps else False
        g5 = d.matched
        g6 = bool(d.unresolved_description.strip()) if d.unresolved_mass_g > 0 else True

        overall = g1 and g2 and g3 and g4 and g5 and g6
        details = []
        if not g1: details.append(f'overlap={overlap:.2f}<{INGREDIENT_OVERLAP_MIN}')
        if not g2: details.append(f'count drift {abs(len(obs_ings) - len(r.expected_ingredients))}>{COUNT_DRIFT_MAX}')
        if not g3: details.append(f'mass drift {abs(d.resolved_mass_g - r.expected_resolved_mass_g):.1f}g>{TOTAL_MASS_DRIFT_G_MAX}g')
        if not g4: details.append(f'per-food mass drift exceeds {PER_FOOD_MASS_DRIFT_G}g')
        if not g5: details.append(f'matched=False (fallback={d.fallback_reason})')
        if not g6: details.append('unresolved_description missing despite unresolved_mass > 0')
        if not details: details.append('ok')

        out.append(GoldenCheck(
            dish_name=r.dish_name,
            expected_count=len(r.expected_ingredients),
            observed_count=len(obs_ings),
            expected_food_ids=exp_ids, observed_food_ids=obs_ids,
            overlap=overlap,
            expected_resolved_mass_g=r.expected_resolved_mass_g,
            observed_resolved_mass_g=d.resolved_mass_g,
            g1_overlap=g1, g2_count=g2, g3_total_mass=g3,
            g4_per_food_mass=g4, g5_matched=g5,
            g6_has_unresolved_description=g6,
            overall_pass=overall,
            detail='; '.join(details),
        ))
    return out


def _format(results: List[GoldenCheck]) -> None:
    print('\nGolden recipe pin test (catches silent LLM drift):')
    print('-' * 100)
    for r in results:
        mark = '[ OK ]' if r.overall_pass else '[FAIL]'
        gates = (f'g1={r.g1_overlap and "+" or "-"} '
                 f'g2={r.g2_count and "+" or "-"} '
                 f'g3={r.g3_total_mass and "+" or "-"} '
                 f'g4={r.g4_per_food_mass and "+" or "-"} '
                 f'g5={r.g5_matched and "+" or "-"} '
                 f'g6={r.g6_has_unresolved_description and "+" or "-"}')
        print(f'  {mark}  {r.dish_name:<32s}  overlap={r.overlap:.0%}  '
              f'count={r.observed_count}/{r.expected_count}  '
              f'mass={r.observed_resolved_mass_g:.0f}/{r.expected_resolved_mass_g:.0f}g  {gates}')
        if not r.overall_pass:
            print(f'         FAIL: {r.detail}')
            new_ids = r.observed_food_ids - r.expected_food_ids
            missing_ids = r.expected_food_ids - r.observed_food_ids
            if new_ids:
                print(f'         new FoodIDs: {sorted(new_ids)}')
            if missing_ids:
                print(f'         missing FoodIDs: {sorted(missing_ids)}')


def main() -> int:
    print('CNFRecipeDecomposer GOLDEN regression harness '
          f'(AI-MATCH-1.x, {len(GOLDEN_PANEL)} pinned recipes)')
    print('=' * 100)
    from api.services.cnf_recipe_decomposer import get_default_decomposer
    decomposer = get_default_decomposer()
    print(f'LLM ranking: {"yes" if decomposer.chat_json_client else "NO (degraded)"}')

    results = run_golden(decomposer)
    _format(results)

    n_pass = sum(1 for r in results if r.overall_pass)
    print()
    print('=' * 100)
    print(f'Golden tests: PASS={n_pass}/{len(results)}')

    out_path = os.path.join(_HERE, '_smoke_cnf_recipe_decomposer_golden_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness': 'CNFRecipeDecomposer golden regression (AI-MATCH-1.x)',
            'pin_date': '2026-05-23',
            'pin_model': 'gpt-4.1-mini @ temperature=0',
            'totals': {'pass': n_pass, 'total': len(results)},
            'results': [
                {
                    'dish_name': r.dish_name,
                    'overlap': round(r.overlap, 2),
                    'observed_count': r.observed_count,
                    'expected_count': r.expected_count,
                    'observed_resolved_mass_g': round(r.observed_resolved_mass_g, 1),
                    'expected_resolved_mass_g': round(r.expected_resolved_mass_g, 1),
                    'observed_food_ids': sorted(r.observed_food_ids),
                    'expected_food_ids': sorted(r.expected_food_ids),
                    'gates': {
                        'g1_overlap': r.g1_overlap,
                        'g2_count': r.g2_count,
                        'g3_total_mass': r.g3_total_mass,
                        'g4_per_food_mass': r.g4_per_food_mass,
                        'g5_matched': r.g5_matched,
                        'g6_has_unresolved_description': r.g6_has_unresolved_description,
                    },
                    'overall_pass': r.overall_pass,
                    'detail': r.detail,
                }
                for r in results
            ],
        }, f, indent=2)
    print(f'Results JSON: {out_path}')
    return 0 if n_pass == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
