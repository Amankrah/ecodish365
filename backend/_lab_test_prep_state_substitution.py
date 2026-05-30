"""Lab Test — Preparation-state behavior of the substitution swap pipeline.

Hits ``/api/analyze/substitution`` with a small panel of real meal
compositions and, for every suggestion the endpoint returns, asks: does the
replacement food share the original's preparation state, or did the swap
silently cross raw↔cooked, fresh↔canned, fresh↔dried, etc.?

The substitution_culinary.py gate already blocks dried↔fresh swaps via regex.
This probe quantifies what slips through (raw beef → grilled chicken? canned
tomato → fresh tomato? frozen veg → fresh veg?), which is the failure mode
the lab plan's Strategy D (culinary-gate upgrade with structured prep tag)
will target.

Pattern mirrors ``_lab_test_prep_state_matcher.py``: capture / verify modes,
JSON baseline. Cost ~$1-3 per run depending on candidate-pool sizes.
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SECRET_KEY', 'lab-prep-state-substitution')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from django.test import Client  # noqa: E402
from api.services.prep_state_extract import extract_prep_state  # noqa: E402


BASELINE_PATH = os.path.join(_HERE, '_lab_test_prep_state_substitution_baseline.json')


# Each meal is a list of (food_id, mass_g, free-text description for context).
# Purposes mirror what production users select.
PANEL: List[Dict[str, Any]] = [
    {
        'label': 'raw_carrot_apple_snack',
        'composition': [
            {'food_id': 2380, 'mass_g': 80.0, 'description': 'Carrot, raw'},
            {'food_id': 1696, 'mass_g': 80.0, 'description': 'Apple, raw, with skin'},
        ],
        'purposes': ['lower_sodium', 'sustainability'],
    },
    {
        'label': 'boiled_egg_breakfast',
        'composition': [
            {'food_id': 130, 'mass_g': 100.0, 'description': 'Egg, chicken, whole, cooked, boiled in shell, hard-cooked'},
            {'food_id': 4066, 'mass_g': 60.0, 'description': 'Bread, white, commercial'},
        ],
        'purposes': ['lower_sodium', 'higher_fibre'],
    },
    {
        'label': 'fried_chicken_meal',
        'composition': [
            {'food_id': 561, 'mass_g': 150.0, 'description': 'Chicken, broiler, meat and skin, batter dipped, fried'},
            {'food_id': 2381, 'mass_g': 100.0, 'description': 'Carrot, boiled, drained'},
        ],
        'purposes': ['lower_sat_fat', 'sustainability'],
    },
    {
        'label': 'canned_tomato_pasta',
        'composition': [
            {'food_id': 2382, 'mass_g': 120.0, 'description': 'Carrot, canned, drained solids'},
            {'food_id': 4066, 'mass_g': 80.0, 'description': 'Bread, white, commercial'},
        ],
        'purposes': ['lower_sodium', 'higher_fibre'],
    },
    {
        'label': 'frozen_broccoli_stirfry',
        'composition': [
            {'food_id': 2025, 'mass_g': 120.0, 'description': 'Broccoli, frozen, spears, unprepared'},
            {'food_id': 560, 'mass_g': 100.0, 'description': 'Chicken, broiler, meat and skin, raw'},
        ],
        'purposes': ['lower_sat_fat', 'sustainability'],
    },
    {
        'label': 'dried_apricot_snack',
        'composition': [
            {'food_id': 1507, 'mass_g': 60.0, 'description': 'Apricot, dried, sulphured, uncooked'},
        ],
        'purposes': ['diabetes_friendly', 'higher_fibre'],
    },
    {
        'label': 'raw_plantain_meal',
        'composition': [
            {'food_id': 1661, 'mass_g': 200.0, 'description': 'Plantain, yellow raw'},
            {'food_id': 560, 'mass_g': 120.0, 'description': 'Chicken, broiler, meat and skin, raw'},
        ],
        'purposes': ['sustainability', 'lower_sat_fat'],
    },
    {
        'label': 'cooked_plantain_meal',
        'composition': [
            {'food_id': 1662, 'mass_g': 200.0, 'description': 'Plantain, yellow cooked'},
            {'food_id': 561, 'mass_g': 120.0, 'description': 'Chicken, broiler, meat and skin, batter dipped, fried'},
        ],
        'purposes': ['sustainability', 'lower_sat_fat'],
    },
    # Phase 1.5: packaged-food meals — these come through the decomposer
    # first, so any cross-prep error compounds.
    {
        'label': 'corn_flakes_milk',
        'composition': [
            {'food_id': 1301, 'mass_g': 30.0, 'description': "Cereal, ready to eat, Corn Flakes, President's Choice"},
            {'food_id': 113, 'mass_g': 200.0, 'description': 'Milk, fluid, whole, pasteurized, homogenized, 3.25% M.F.'},
        ],
        'purposes': ['higher_fibre', 'lower_sodium'],
    },
    {
        'label': 'frozen_entree_heated',
        'composition': [
            {'food_id': 8, 'mass_g': 300.0, 'description': 'Frozen entree, fried chicken with mashed potatoes and vegetables, heated'},
        ],
        'purposes': ['lower_sodium', 'lower_sat_fat'],
    },
    {
        'label': 'evaporated_milk_dessert',
        'composition': [
            {'food_id': 140, 'mass_g': 100.0, 'description': 'Milk, evaporated, whole, canned, undiluted, 7.8% M.F.'},
            {'food_id': 68, 'mass_g': 50.0, 'description': 'Milk, condensed, sweetened, canned'},
        ],
        'purposes': ['lower_sodium', 'lower_sat_fat'],
    },
    {
        'label': 'dried_egg_powder_recipe',
        'composition': [
            {'food_id': 83, 'mass_g': 25.0, 'description': 'Egg, chicken, dried, whole'},
            {'food_id': 4066, 'mass_g': 60.0, 'description': 'Bread, white, commercial'},
        ],
        'purposes': ['higher_fibre', 'sustainability'],
    },
]


@dataclass
class SwapOutcome:
    meal_label: str
    purpose: str
    suggestion_index: int
    original_food_id: int
    original_description: str
    original_thermal_state: str
    original_preservation_state: str
    replacement_food_id: int
    replacement_description: str
    replacement_thermal_state: str
    replacement_preservation_state: str
    crosses_thermal_axis: bool
    crosses_preservation_axis: bool
    crosses_any_axis: bool

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _extract_swap_pair(suggestion: Dict[str, Any]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """A suggestion can contain multiple swaps (some recipes substitute several
    components). Return all (original, replacement) pairs."""
    pairs = []
    swaps = suggestion.get('swaps') or []
    if swaps:
        for s in swaps:
            orig = s.get('original') or {}
            repl = s.get('replacement') or {}
            if orig and repl:
                pairs.append((orig, repl))
        return pairs
    # Some payload shapes flatten the single-swap case to top-level keys.
    orig = suggestion.get('original') or {}
    repl = suggestion.get('replacement') or {}
    if orig and repl:
        pairs.append((orig, repl))
    return pairs


def _run_one_meal(client: Client, meal: Dict[str, Any], purpose: str) -> Tuple[List[SwapOutcome], Optional[str]]:
    body = {
        'composition': [
            {'food_id': c['food_id'], 'mass_g': c['mass_g']}
            for c in meal['composition']
        ],
        'purpose': purpose,
    }
    r = client.post('/api/substitution/analyze/',
                    data=json.dumps(body),
                    content_type='application/json',
                    secure=True)
    if r.status_code != 200:
        return [], f'HTTP {r.status_code}: {r.content[:200]!r}'
    try:
        payload = r.json()
    except Exception as exc:  # noqa: BLE001
        return [], f'json parse: {exc!r}'

    suggestions = payload.get('suggestions') or []
    outcomes: List[SwapOutcome] = []
    for i, sug in enumerate(suggestions):
        for orig, repl in _extract_swap_pair(sug):
            orig_desc = orig.get('food_description') or orig.get('description') or ''
            repl_desc = repl.get('food_description') or repl.get('description') or ''
            o_ps = extract_prep_state(orig_desc)
            r_ps = extract_prep_state(repl_desc)
            t_cross = (
                o_ps.thermal_state != 'unknown'
                and r_ps.thermal_state != 'unknown'
                and o_ps.thermal_state != r_ps.thermal_state
                and not (
                    o_ps.thermal_state in {'boiled', 'fried', 'baked', 'roasted', 'stewed',
                                            'grilled', 'steamed', 'poached', 'scrambled',
                                            'heated', 'cooked'}
                    and r_ps.thermal_state in {'boiled', 'fried', 'baked', 'roasted', 'stewed',
                                                'grilled', 'steamed', 'poached', 'scrambled',
                                                'heated', 'cooked'}
                )
            )
            p_cross = (
                o_ps.preservation_state != 'unknown'
                and r_ps.preservation_state != 'unknown'
                and o_ps.preservation_state != r_ps.preservation_state
            )
            outcomes.append(SwapOutcome(
                meal_label=meal['label'],
                purpose=purpose,
                suggestion_index=i,
                original_food_id=int(orig.get('food_id') or 0),
                original_description=orig_desc,
                original_thermal_state=o_ps.thermal_state,
                original_preservation_state=o_ps.preservation_state,
                replacement_food_id=int(repl.get('food_id') or 0),
                replacement_description=repl_desc,
                replacement_thermal_state=r_ps.thermal_state,
                replacement_preservation_state=r_ps.preservation_state,
                crosses_thermal_axis=t_cross,
                crosses_preservation_axis=p_cross,
                crosses_any_axis=t_cross or p_cross,
            ))
    return outcomes, None


def _summarise(swaps: List[SwapOutcome]) -> Dict[str, Any]:
    n = len(swaps)
    if n == 0:
        return {'n_swaps': 0}
    n_t = sum(s.crosses_thermal_axis for s in swaps)
    n_p = sum(s.crosses_preservation_axis for s in swaps)
    n_any = sum(s.crosses_any_axis for s in swaps)

    # Crosses by transition (e.g. raw->cooked, fresh->canned)
    transitions = Counter()
    for s in swaps:
        if s.crosses_thermal_axis:
            transitions[(s.original_thermal_state, s.replacement_thermal_state, 'thermal')] += 1
        if s.crosses_preservation_axis:
            transitions[(s.original_preservation_state, s.replacement_preservation_state, 'preservation')] += 1
    transitions_list = sorted(
        ({'from': k[0], 'to': k[1], 'axis': k[2], 'count': v}
         for k, v in transitions.items()),
        key=lambda r: -r['count'],
    )

    return {
        'n_swaps': n,
        'thermal_cross_rate': round(n_t / n, 3),
        'preservation_cross_rate': round(n_p / n, 3),
        'any_axis_cross_rate': round(n_any / n, 3),
        'transitions': transitions_list,
    }


def _print_scorecard(swaps: List[SwapOutcome], summary: Dict[str, Any]) -> None:
    print('=' * 100)
    print(f'PREP-STATE SUBSTITUTION LAB — {summary["n_swaps"]} (meal, purpose, suggestion) swaps')
    print('=' * 100)
    if summary['n_swaps'] == 0:
        print('  No swaps emitted — substitution endpoint returned nothing.')
        return
    print(f'OVERALL  any_cross={summary["any_axis_cross_rate"]*100:5.1f}%   '
          f'thermal_cross={summary["thermal_cross_rate"]*100:5.1f}%   '
          f'preservation_cross={summary["preservation_cross_rate"]*100:5.1f}%')
    print('-' * 100)
    print('Cross-prep transitions (orig → replacement):')
    for row in summary['transitions'][:20]:
        print(f'  {row["axis"]:<12}  {row["from"]:<10} -> {row["to"]:<10} x{row["count"]}')
    print('-' * 100)
    print('Per-swap detail:')
    for s in swaps:
        marks = ('X' if s.crosses_thermal_axis else '.') + ('X' if s.crosses_preservation_axis else '.')
        print(f'  [{marks}] {s.meal_label:<26} purpose={s.purpose:<22} '
              f'id {s.original_food_id} ({s.original_thermal_state}/{s.original_preservation_state}) '
              f'-> {s.replacement_food_id} ({s.replacement_thermal_state}/{s.replacement_preservation_state})')


def capture() -> int:
    client = Client()
    all_swaps: List[SwapOutcome] = []
    errors: List[Dict[str, Any]] = []
    print(f'Running {len(PANEL)} meal compositions through /api/analyze/substitution ...')
    for meal in PANEL:
        for purpose in meal['purposes']:
            outcomes, err = _run_one_meal(client, meal, purpose)
            if err:
                errors.append({'meal': meal['label'], 'purpose': purpose, 'error': err})
                print(f'  ERR {meal["label"]:<28} purpose={purpose:<22} — {err[:80]}')
            else:
                all_swaps.extend(outcomes)
                print(f'  ok  {meal["label"]:<28} purpose={purpose:<22} — {len(outcomes)} swap(s)')

    summary = _summarise(all_swaps)
    baseline_payload = {
        'summary': summary,
        'per_swap': [s.as_dict() for s in all_swaps],
        'errors': errors,
    }
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(baseline_payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    print()
    _print_scorecard(all_swaps, summary)
    print()
    print(f'Wrote {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    client = Client()
    all_swaps: List[SwapOutcome] = []
    for meal in PANEL:
        for purpose in meal['purposes']:
            outcomes, _err = _run_one_meal(client, meal, purpose)
            all_swaps.extend(outcomes)
    summary = _summarise(all_swaps)
    _print_scorecard(all_swaps, summary)
    print()
    base = baseline['summary']
    print('Deltas vs baseline (percentage points):')
    for k in ('thermal_cross_rate', 'preservation_cross_rate', 'any_axis_cross_rate'):
        delta = (summary.get(k, 0) - base.get(k, 0)) * 100
        print(f'  {k:<25}  {base.get(k,0)*100:5.1f}% → {summary.get(k,0)*100:5.1f}%  ({delta:+5.1f}pp)')
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
