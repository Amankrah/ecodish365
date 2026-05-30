"""Lab Test — Preparation-state accuracy at the decomposer's Stage-2 matcher.

Runs prep-state-sensitive dishes through the FULL ``CNFRecipeDecomposer``
pipeline and asks: for each ingredient the Stage-1 LLM extracts, does the
Stage-2 matcher resolve it to a CNF FoodID whose description encodes the
RIGHT preparation state?

Concretely — for "carrot soup, 250 g":
  Stage 1 LLM produces ingredients including "carrot, cooked, 80 g".
  Stage 2 matcher resolves the name to a CNF FoodID.
  We check: does the matched description regex-extract to thermal=cooked?

The matcher accuracy lab already showed dish_context queries hit only ~50%
prep-state correctness in isolation. This probe measures whether the
decomposer's Stage-1 prompt ("pick CNF entries in their COOKED/PREPARED
form...") actually rescues the Stage-2 matcher, or whether the prompt
guidance evaporates by the time the matcher sees the text.

Pattern mirrors ``_lab_test_prep_state_matcher.py``: capture / verify modes,
JSON baseline beside the scenarios file. Cost ~$0.40 per run (12 dishes x
Stage-1 LLM + ~5 matcher calls).
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SECRET_KEY', 'lab-prep-state-decomposer')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.services.cnf_recipe_decomposer import get_default_decomposer  # noqa: E402
from api.services.prep_state_extract import (  # noqa: E402
    extract_prep_state,
    thermal_states_equivalent,
    preservation_states_equivalent,
)


SCENARIOS_PATH = os.path.join(_HERE, '_lab_prep_state_decomposer_scenarios.json')
BASELINE_PATH = os.path.join(_HERE, '_lab_test_prep_state_decomposer_baseline.json')


@dataclass
class CheckOutcome:
    dish: str
    keyword: str
    expected_thermal_state: str
    expected_preservation_state: str
    matched_ingredient_found: bool
    matched_food_id: Optional[int]
    matched_food_description: str
    matched_mass_g: Optional[float]
    matched_resolution_confidence: Optional[float]
    extracted_thermal_state: str
    extracted_preservation_state: str
    thermal_correct: bool
    preservation_correct: bool
    both_correct: bool

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioOutcome:
    dish: str
    total_mass_g: float
    matched: bool
    fallback_reason: Optional[str]
    decomposition_confidence: float
    n_ingredients: int
    ingredient_list: List[Dict[str, Any]]
    checks: List[CheckOutcome]
    latency_seconds: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            'dish': self.dish,
            'total_mass_g': self.total_mass_g,
            'matched': self.matched,
            'fallback_reason': self.fallback_reason,
            'decomposition_confidence': self.decomposition_confidence,
            'n_ingredients': self.n_ingredients,
            'ingredient_list': self.ingredient_list,
            'checks': [c.as_dict() for c in self.checks],
            'latency_seconds': self.latency_seconds,
        }


def _run_one(decomposer, scenario: Dict[str, Any]) -> ScenarioOutcome:
    import time
    t0 = time.time()
    dish = scenario['dish']
    mass = float(scenario['total_mass_g'])
    try:
        recipe = decomposer.decompose(dish, mass)
    except Exception as exc:  # noqa: BLE001
        return ScenarioOutcome(
            dish=dish, total_mass_g=mass, matched=False,
            fallback_reason=f'exception: {exc!r}'[:200],
            decomposition_confidence=0.0,
            n_ingredients=0, ingredient_list=[], checks=[],
            latency_seconds=round(time.time() - t0, 2),
        )

    ingredient_list = [
        {
            'food_id': i.food_id,
            'food_description': i.food_description,
            'food_group': i.food_group,
            'mass_g': round(i.mass_g, 1),
            'resolution_confidence': round(i.resolution_confidence, 3),
            'food_type': i.food_type,
        }
        for i in recipe.ingredients
    ]

    checks: List[CheckOutcome] = []
    for check in scenario.get('prep_state_checks', []):
        kw = (check.get('ingredient_keyword') or '').lower().strip()
        exp_thermal = check.get('expected_thermal_state', 'unknown')
        exp_pres = check.get('expected_preservation_state', 'unknown')

        match_ing = None
        for ing in recipe.ingredients:
            if kw and kw in (ing.food_description or '').lower():
                match_ing = ing
                break

        if match_ing is None:
            checks.append(CheckOutcome(
                dish=dish, keyword=kw,
                expected_thermal_state=exp_thermal,
                expected_preservation_state=exp_pres,
                matched_ingredient_found=False,
                matched_food_id=None, matched_food_description='',
                matched_mass_g=None, matched_resolution_confidence=None,
                extracted_thermal_state='unknown',
                extracted_preservation_state='unknown',
                thermal_correct=False,
                preservation_correct=False,
                both_correct=False,
            ))
            continue

        ext = extract_prep_state(match_ing.food_description)
        t_ok = thermal_states_equivalent(ext.thermal_state, exp_thermal)
        p_ok = preservation_states_equivalent(ext.preservation_state, exp_pres)
        checks.append(CheckOutcome(
            dish=dish, keyword=kw,
            expected_thermal_state=exp_thermal,
            expected_preservation_state=exp_pres,
            matched_ingredient_found=True,
            matched_food_id=match_ing.food_id,
            matched_food_description=match_ing.food_description,
            matched_mass_g=round(match_ing.mass_g, 1),
            matched_resolution_confidence=round(match_ing.resolution_confidence, 3),
            extracted_thermal_state=ext.thermal_state,
            extracted_preservation_state=ext.preservation_state,
            thermal_correct=t_ok,
            preservation_correct=p_ok,
            both_correct=t_ok and p_ok,
        ))

    return ScenarioOutcome(
        dish=dish, total_mass_g=mass,
        matched=recipe.matched,
        fallback_reason=recipe.fallback_reason,
        decomposition_confidence=round(recipe.decomposition_confidence, 3),
        n_ingredients=len(recipe.ingredients),
        ingredient_list=ingredient_list,
        checks=checks,
        latency_seconds=round(time.time() - t0, 2),
    )


def _summarise(outcomes: List[ScenarioOutcome]) -> Dict[str, Any]:
    all_checks: List[CheckOutcome] = []
    for s in outcomes:
        all_checks.extend(s.checks)
    n = len(all_checks)
    if n == 0:
        return {'n_checks': 0}

    n_found = sum(c.matched_ingredient_found for c in all_checks)
    thermal_ok = sum(c.thermal_correct for c in all_checks)
    pres_ok = sum(c.preservation_correct for c in all_checks)
    both_ok = sum(c.both_correct for c in all_checks)

    confusion = Counter()
    for c in all_checks:
        if c.expected_thermal_state != 'unknown':
            confusion[(c.expected_thermal_state, c.extracted_thermal_state)] += 1
    confusion_list = sorted(
        ({'expected': k[0], 'got': k[1], 'count': v}
         for k, v in confusion.items()),
        key=lambda r: -r['count'],
    )

    return {
        'n_scenarios': len(outcomes),
        'n_checks': n,
        'ingredient_found_rate': round(n_found / n, 3),
        'thermal_acc': round(thermal_ok / n, 3),
        'preservation_acc': round(pres_ok / n, 3),
        'both_acc': round(both_ok / n, 3),
        'thermal_confusion': confusion_list,
    }


def _print_scorecard(outcomes: List[ScenarioOutcome], summary: Dict[str, Any]) -> None:
    print('=' * 100)
    print(f'PREP-STATE DECOMPOSER LAB — {summary["n_scenarios"]} scenarios, '
          f'{summary["n_checks"]} ingredient checks')
    print('=' * 100)
    print(f'OVERALL  ingredient_found={summary["ingredient_found_rate"]*100:5.1f}%   '
          f'thermal={summary["thermal_acc"]*100:5.1f}%   '
          f'preservation={summary["preservation_acc"]*100:5.1f}%   '
          f'both={summary["both_acc"]*100:5.1f}%')
    print('-' * 100)
    print('Thermal confusion (expected → got):')
    for row in summary['thermal_confusion'][:20]:
        mark = '  ' if row['expected'] == row['got'] else 'XX'
        print(f'  {mark}  {row["expected"]:<10} -> {row["got"]:<10} x{row["count"]}')
    print('-' * 100)
    print('Per-scenario results:')
    for s in outcomes:
        print(f'  DISH "{s.dish}" ({s.total_mass_g}g, n_ing={s.n_ingredients}, '
              f'conf={s.decomposition_confidence}, lat={s.latency_seconds}s)')
        for c in s.checks:
            if not c.matched_ingredient_found:
                print(f'    [---] keyword={c.keyword!r}: INGREDIENT NOT FOUND  '
                      f'exp=({c.expected_thermal_state}/{c.expected_preservation_state})')
                continue
            marks = ''.join([
                'T' if c.thermal_correct else 't',
                'P' if c.preservation_correct else 'p',
            ])
            print(f'    [{marks}] keyword={c.keyword!r} -> id={c.matched_food_id} '
                  f'({c.extracted_thermal_state}/{c.extracted_preservation_state})  '
                  f'exp=({c.expected_thermal_state}/{c.expected_preservation_state})  '
                  f'desc={c.matched_food_description[:55]!r}')


def capture() -> int:
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set. Aborting.')
        return 2
    with open(SCENARIOS_PATH, encoding='utf-8') as f:
        sx = json.load(f)
    scenarios = sx['scenarios']

    decomposer = get_default_decomposer()
    outcomes: List[ScenarioOutcome] = []
    print(f'Running {len(scenarios)} prep-state decomposer scenarios...')
    for i, sc in enumerate(scenarios, 1):
        out = _run_one(decomposer, sc)
        outcomes.append(out)
        print(f'  [{i:>2}/{len(scenarios)}] "{sc["dish"]}" — '
              f'n_ing={out.n_ingredients} conf={out.decomposition_confidence}')

    summary = _summarise(outcomes)
    baseline_payload = {
        'scenarios_version': sx.get('version'),
        'summary': summary,
        'per_scenario': [o.as_dict() for o in outcomes],
    }
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(baseline_payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    print()
    _print_scorecard(outcomes, summary)
    print()
    print(f'Wrote {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set. Aborting.')
        return 2
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    with open(SCENARIOS_PATH, encoding='utf-8') as f:
        sx = json.load(f)
    scenarios = sx['scenarios']

    decomposer = get_default_decomposer()
    outcomes: List[ScenarioOutcome] = []
    print(f'Verifying {len(scenarios)} prep-state decomposer scenarios...')
    for sc in scenarios:
        outcomes.append(_run_one(decomposer, sc))

    summary = _summarise(outcomes)
    _print_scorecard(outcomes, summary)
    print()
    base = baseline['summary']
    delta = lambda k: (summary[k] - base[k]) * 100
    print('Deltas vs baseline (percentage points):')
    for k in ('ingredient_found_rate', 'thermal_acc', 'preservation_acc', 'both_acc'):
        print(f'  {k:<22}  {base[k]*100:5.1f}% → {summary[k]*100:5.1f}%  ({delta(k):+5.1f}pp)')
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'capture'
    if mode == 'capture':
        return capture()
    if mode in ('verify', 'verify_fixed'):
        return verify()
    print(f'Unknown mode: {mode!r}. Use "capture" or "verify".')
    return 2


if __name__ == '__main__':
    sys.exit(main())
