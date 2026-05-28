#!/usr/bin/env python
"""S5-subst — canonical diet-shift substitution panel for manuscript §5.2.

Runs four Scenario S5 swaps (beef→legumes, milk→soy, cola→water,
white→whole wheat) through the production substitution stack and records
full scorecard deltas for manuscript Table 4 / Figure 8.

Outputs (repo root):
  results/S5-subst/s5_delta_table.csv
  results/S5-subst/s5_results.json
  results/S5-subst/analyzer_fidelity.json
  results/S5-subst/run_manifest.json
  backend/_smoke_substitution_s5_panel_results.json

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_substitution_s5_panel.py
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402

django.setup()

from api.services.substitution_analyzer import (  # noqa: E402
    analyze_substitutions,
    score_modified_composition,
)

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_OUT = os.path.join(_REPO, 'results', 'S5-subst')


@dataclass
class S5Case:
    swap_id: str
    label: str
    baseline_food_id: int
    baseline_description: str
    replacement_food_id: int
    replacement_description: str
    mass_g: float
    expect_rule: str
    literature_note: str
    expected: Dict[str, str] = field(default_factory=dict)


S5_CASES: List[S5Case] = [
    S5Case(
        swap_id='beef_to_legumes',
        label='Beef → lentils',
        baseline_food_id=2683,
        baseline_description='Beef, ground, lean, raw',
        replacement_food_id=3392,
        replacement_description='Lentils, raw',
        mass_g=100.0,
        expect_rule='beef_to_legumes',
        literature_note='Stylianou 2021 S5 mix; Poore 2018 animal vs legume footprint',
        expected={'hefi': 'up', 'heni': 'up', 'fcs': 'up', 'environmental': 'up'},
    ),
    S5Case(
        swap_id='milk_to_soy',
        label="Cow's milk → fortified soy",
        baseline_food_id=113,
        baseline_description='Milk, fluid, whole, pasteurized, homogenized, 3.25% M.F.',
        replacement_food_id=6331,
        replacement_description='Plant-based beverage, soy beverage, all flavours, low fat, fortified',
        mass_g=250.0,
        expect_rule='milk_to_soy',
        literature_note='Dairy shift counterfactual (S5 #2); HEFI may drop on single-item swap (see §7)',
        expected={'heni': 'up', 'environmental': 'neutral_or_down'},
    ),
    S5Case(
        swap_id='cola_to_water',
        label='Cola → water',
        baseline_food_id=2920,
        baseline_description='Carbonated drinks, cola, fast-food cola',
        replacement_food_id=2933,
        replacement_description='Water, municipal',
        mass_g=355.0,
        expect_rule='cola_to_water',
        literature_note='SSB reduction (GBD SSB risk; Stylianou red-zone SSBs)',
        expected={'hefi': 'neutral_or_up', 'heni': 'up', 'fcs': 'up', 'environmental': 'neutral_or_down'},
    ),
    S5Case(
        swap_id='white_to_whole_wheat',
        label='White bread → whole wheat bread',
        baseline_food_id=3732,
        baseline_description='Bread, white, commercial, toasted',
        replacement_food_id=4067,
        replacement_description='Bread, whole wheat, commercial',
        mass_g=80.0,
        expect_rule='white_to_whole_wheat',
        literature_note='Whole-grain shift (S5 #4; HEFI whole-grain component)',
        expected={'hefi': 'up', 'heni': 'up', 'fcs': 'up', 'environmental': 'neutral_or_down'},
    ),
]


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=_REPO, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return 'unknown'


def _score_val(sc: Dict[str, Any], key: str) -> Optional[float]:
    block = sc.get(key) or {}
    v = block.get('value')
    return float(v) if v is not None else None


def _direction(delta: Optional[float], invert: bool = False) -> str:
    if delta is None:
        return 'missing'
    if abs(delta) < 1e-4:
        return 'flat'
    improved = delta < 0 if invert else delta > 0
    return 'up' if improved else 'down'


def _check_expected(actual: str, expected: str) -> bool:
    if expected == 'neutral_or_up':
        return actual in ('up', 'flat')
    if expected == 'neutral_or_down':
        return actual in ('down', 'flat')
    return actual == expected


def _run_case(case: S5Case) -> Dict[str, Any]:
    baseline_comp = [{
        'food_id': case.baseline_food_id,
        'mass_g': case.mass_g,
        'food_description': case.baseline_description,
    }]
    modified_comp = [{
        'food_id': case.replacement_food_id,
        'mass_g': case.mass_g,
        'food_description': case.replacement_description,
    }]

    t0 = time.perf_counter()
    analyze = analyze_substitutions(
        baseline_comp,
        purpose='general_health',
        max_suggestions=3,
        include_scorecard=True,
    )
    baseline_sc = score_modified_composition(baseline_comp)['scorecard']
    modified_sc = score_modified_composition(modified_comp)['scorecard']

    hefi_d = (_score_val(modified_sc, 'hefi') or 0) - (_score_val(baseline_sc, 'hefi') or 0)
    heni_d = (_score_val(modified_sc, 'heni') or 0) - (_score_val(baseline_sc, 'heni') or 0)
    fcs_d = (_score_val(modified_sc, 'fcs') or 0) - (_score_val(baseline_sc, 'fcs') or 0)
    hsr_d = (_score_val(modified_sc, 'hsr') or 0) - (_score_val(baseline_sc, 'hsr') or 0)
    env_d = (_score_val(modified_sc, 'environmental') or 0) - (_score_val(baseline_sc, 'environmental') or 0)

    dirs = {
        'hefi': _direction(hefi_d),
        'heni': _direction(heni_d, invert=True),  # lower minutes = better
        'fcs': _direction(fcs_d),
        'hsr': _direction(hsr_d),
        'environmental': _direction(env_d, invert=True),
    }

    top_rule = analyze['suggestions'][0]['rule_id'] if analyze.get('suggestions') else None
    rule_ok = top_rule == case.expect_rule

    from api.services.substitution_analyzer import _normalize_composition, _rule_candidates
    from api.services.substitution_constraints import parse_extended_constraints
    norm = _normalize_composition(baseline_comp)
    rule_cands = _rule_candidates(norm, 'general_health', parse_extended_constraints(None))
    rule_candidate_ok = any(c['rule_id'] == case.expect_rule for c in rule_cands)

    direction_ok = all(
        _check_expected(dirs[k], case.expected[k])
        for k in case.expected
        if k in dirs
    )

    return {
        'swap_id': case.swap_id,
        'expect_rule': case.expect_rule,
        'label': case.label,
        'mass_g': case.mass_g,
        'literature_note': case.literature_note,
        'baseline': {
            'food_id': case.baseline_food_id,
            'description': case.baseline_description,
            'hefi': _score_val(baseline_sc, 'hefi'),
            'heni_min': _score_val(baseline_sc, 'heni'),
            'fcs': _score_val(baseline_sc, 'fcs'),
            'hsr': _score_val(baseline_sc, 'hsr'),
            'environmental': _score_val(baseline_sc, 'environmental'),
        },
        'replacement': {
            'food_id': case.replacement_food_id,
            'description': case.replacement_description,
            'hefi': _score_val(modified_sc, 'hefi'),
            'heni_min': _score_val(modified_sc, 'heni'),
            'fcs': _score_val(modified_sc, 'fcs'),
            'hsr': _score_val(modified_sc, 'hsr'),
            'environmental': _score_val(modified_sc, 'environmental'),
        },
        'delta': {
            'hefi': round(hefi_d, 3),
            'heni_min': round(heni_d, 3),
            'fcs': round(fcs_d, 3),
            'hsr': round(hsr_d, 3),
            'environmental': round(env_d, 4),
        },
        'direction': dirs,
        'expected_direction': case.expected,
        'direction_check_pass': direction_ok,
        'analyzer_top_rule': top_rule,
        'analyzer_rule_pass': rule_ok,
        'rule_candidate_pass': rule_candidate_ok,
        'analyzer_hefi_delta': (
            analyze['suggestions'][0]['hefi']['delta'] if analyze.get('suggestions') else None
        ),
        'elapsed_ms': round((time.perf_counter() - t0) * 1000, 1),
    }


def main() -> int:
    os.makedirs(_OUT, exist_ok=True)
    print('S5-subst panel — canonical diet-shift substitutions')
    print('=' * 60)

    results = [_run_case(c) for c in S5_CASES]
    failed_dir = [r for r in results if not r['direction_check_pass']]
    failed_rule = [r for r in results if not r['rule_candidate_pass']]

    for r in results:
        status = 'PASS' if r['direction_check_pass'] and r['rule_candidate_pass'] else 'FAIL'
        rule_disp = r['analyzer_top_rule'] or (r.get('expect_rule') if r['rule_candidate_pass'] else 'none')
        print(
            f"{status} {r['swap_id']:22s}  "
            f"ΔHEFI {r['delta']['hefi']:+.1f}  "
            f"ΔHENI {r['delta']['heni_min']:+.1f} min  "
            f"rule={rule_disp}"
        )

    manifest = {
        'harness': 'S5-subst substitution panel',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'git_sha': _git_sha(),
        'seed': 20260520,
        'cases': len(S5_CASES),
        'direction_pass': len(S5_CASES) - len(failed_dir),
        'analyzer_rule_pass': len(S5_CASES) - len(failed_rule),
    }

    payload = {
        'manifest': manifest,
        'cases': results,
        'summary': {
            'all_directions_pass': len(failed_dir) == 0,
            'all_rule_candidates_pass': len(failed_rule) == 0,
            'failed_direction': [r['swap_id'] for r in failed_dir],
            'failed_rule_candidates': [r['swap_id'] for r in failed_rule],
            'analyzer_rank_failures': [
                r['swap_id'] for r in results
                if not r['analyzer_rule_pass'] and r['rule_candidate_pass']
            ],
        },
    }

    json_path = os.path.join(_OUT, 's5_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    csv_path = os.path.join(_OUT, 's5_delta_table.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'swap_id', 'label', 'mass_g',
            'baseline_hefi', 'replacement_hefi', 'delta_hefi', 'dir_hefi',
            'baseline_heni_min', 'replacement_heni_min', 'delta_heni_min', 'dir_heni',
            'baseline_fcs', 'replacement_fcs', 'delta_fcs', 'dir_fcs',
            'baseline_env', 'replacement_env', 'delta_env', 'dir_env',
            'analyzer_top_rule', 'direction_pass', 'analyzer_pass',
        ])
        for r in results:
            w.writerow([
                r['swap_id'], r['label'], r['mass_g'],
                r['baseline']['hefi'], r['replacement']['hefi'], r['delta']['hefi'], r['direction']['hefi'],
                r['baseline']['heni_min'], r['replacement']['heni_min'], r['delta']['heni_min'], r['direction']['heni'],
                r['baseline']['fcs'], r['replacement']['fcs'], r['delta']['fcs'], r['direction']['fcs'],
                r['baseline']['environmental'], r['replacement']['environmental'], r['delta']['environmental'], r['direction']['environmental'],
                r['analyzer_top_rule'], r['direction_check_pass'], r['analyzer_rule_pass'],
            ])

    fidelity_path = os.path.join(_OUT, 'analyzer_fidelity.json')
    with open(fidelity_path, 'w', encoding='utf-8') as f:
        json.dump({
            'cases': [{
                'swap_id': r['swap_id'],
                'expect_rule': next(c.expect_rule for c in S5_CASES if c.swap_id == r['swap_id']),
                'top_rule': r['analyzer_top_rule'],
                'rule_candidate_pass': r['rule_candidate_pass'],
                'analyzer_rank_pass': r['analyzer_rule_pass'],
            } for r in results],
        }, f, indent=2)

    with open(os.path.join(_OUT, 'run_manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    backend_copy = os.path.join(os.path.dirname(__file__), '_smoke_substitution_s5_panel_results.json')
    with open(backend_copy, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    print(f'\nWrote {csv_path}')
    print(f'Wrote {json_path}')
    failed = len(failed_dir) + len(failed_rule)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
