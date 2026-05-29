#!/usr/bin/env python
"""Lab Test B — end-to-end substitution endpoint snapshot.

POSTs the 8 compositions from the user's saved-days export to the live
`/api/substitution/analyze/` endpoint in both modes (singles, greedy
max_swaps=3) and captures the ranked suggestion set. Run BEFORE and AFTER
the cache change to prove zero behavioural drift.

Usage:
  capture : query endpoint, write _lab_test_endpoint_baseline.json
  verify  : query endpoint, diff suggestions against baseline

The endpoint must be reachable at http://127.0.0.1:8000/api/substitution/analyze/
(`python manage.py runserver` from backend/).
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
from typing import Any, Dict, List

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

ENDPOINT = 'http://127.0.0.1:8000/api/substitution/analyze/'
BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), '_lab_test_endpoint_baseline.json'
)
# Tolerance on rust-side FCS deltas. Float ops on different code paths can
# differ in the last 1-2 bits even when math is identical; 1e-6 is well below
# any value that could change a suggestion's rank or visible UI signal.
FLOAT_TOL = 1e-6


CASES: List[Dict[str, Any]] = [
    {
        'label': 'D1 breakfast — scrambled egg + OJ',
        'dish_name': 'scrambled egg with orange juice',
        'composition': [
            {'food_id': 133, 'mass_g': 200},
            {'food_id': 118, 'mass_g': 8},
            {'food_id': 61, 'mass_g': 15},
            {'food_id': 1620, 'mass_g': 273},
        ],
    },
    {
        'label': 'D1 lunch — chicken biryani',
        'dish_name': 'chicken briyani',
        'composition': [
            {'food_id': 4473, 'mass_g': 320},
            {'food_id': 851, 'mass_g': 200},
            {'food_id': 6971, 'mass_g': 50},
            {'food_id': 5960, 'mass_g': 50},
            {'food_id': 7829, 'mass_g': 30},
            {'food_id': 2460, 'mass_g': 25},
            {'food_id': 2394, 'mass_g': 8},
            {'food_id': 2091, 'mass_g': 7},
        ],
    },
    {
        'label': 'D1 dinner — oat porridge',
        'dish_name': 'oat porridge with milk and banna',
        'composition': [
            {'food_id': 1465, 'mass_g': 250},
            {'food_id': 61, 'mass_g': 130},
            {'food_id': 1704, 'mass_g': 65},
        ],
    },
    {
        'label': 'D2 breakfast — scrambled egg + mango',
        'dish_name': 'scrambled egg with mango juice',
        'composition': [
            {'food_id': 133, 'mass_g': 150},
            {'food_id': 118, 'mass_g': 8},
            {'food_id': 6205, 'mass_g': 240},
        ],
    },
    {
        'label': 'D2 lunch — chicken biryani (partial)',
        'dish_name': 'chicken briyani',
        'composition': [
            {'food_id': 851, 'mass_g': 180},
            {'food_id': 5960, 'mass_g': 60},
            {'food_id': 6961, 'mass_g': 35},
            {'food_id': 2460, 'mass_g': 25},
            {'food_id': 7829, 'mass_g': 20},
        ],
    },
    {
        'label': 'D2 dinner — fufu + groundnut soup',
        'dish_name': 'fufu with groundnut soup',
        'composition': [
            {'food_id': 700194, 'mass_g': 200},
            {'food_id': 1662, 'mass_g': 100},
            {'food_id': 2933, 'mass_g': 160},
            {'food_id': 3399, 'mass_g': 70},
            {'food_id': 648, 'mass_g': 120},
            {'food_id': 2460, 'mass_g': 50},
            {'food_id': 2401, 'mass_g': 30},
            {'food_id': 423, 'mass_g': 15},
        ],
    },
    {
        'label': 'D1 AGGREGATED',
        'dish_name': 'day 1 full day',
        'composition': [
            {'food_id': 4473, 'mass_g': 320},
            {'food_id': 1620, 'mass_g': 273},
            {'food_id': 1465, 'mass_g': 250},
            {'food_id': 133, 'mass_g': 200},
            {'food_id': 851, 'mass_g': 200},
            {'food_id': 61, 'mass_g': 145},
            {'food_id': 1704, 'mass_g': 65},
            {'food_id': 6971, 'mass_g': 50},
            {'food_id': 5960, 'mass_g': 50},
            {'food_id': 7829, 'mass_g': 30},
            {'food_id': 2460, 'mass_g': 25},
            {'food_id': 118, 'mass_g': 8},
            {'food_id': 2394, 'mass_g': 8},
            {'food_id': 2091, 'mass_g': 7},
        ],
    },
    {
        'label': 'D2 AGGREGATED',
        'dish_name': 'day 2 full day',
        'composition': [
            {'food_id': 6205, 'mass_g': 240},
            {'food_id': 700194, 'mass_g': 200},
            {'food_id': 2933, 'mass_g': 160},
            {'food_id': 133, 'mass_g': 150},
            {'food_id': 648, 'mass_g': 120},
            {'food_id': 1662, 'mass_g': 100},
            {'food_id': 3399, 'mass_g': 70},
            {'food_id': 2460, 'mass_g': 50},
            {'food_id': 2401, 'mass_g': 30},
            {'food_id': 423, 'mass_g': 15},
            {'food_id': 118, 'mass_g': 8},
        ],
    },
]


def _digest_suggestion(s: Dict[str, Any]) -> Dict[str, Any]:
    """Extract just the fields whose stability we care about."""
    return {
        'rule_id': s.get('rule_id'),
        'candidate_source': s.get('candidate_source'),
        'suggestion_type': s.get('suggestion_type'),
        'ingredient_index': s.get('ingredient_index'),
        'ingredient_indices': sorted(s.get('ingredient_indices') or []),
        'original_food_id': (s.get('original') or {}).get('food_id'),
        'replacement_food_id': (s.get('replacement') or {}).get('food_id'),
        'rank_score': round(float(s.get('rank_score', 0.0)), 6),
        'fcs_delta': round(float((s.get('fcs') or {}).get('delta', 0.0)), 6),
        'fcs_before': round(float((s.get('fcs') or {}).get('before', 0.0)), 6),
        'fcs_after': round(float((s.get('fcs') or {}).get('after', 0.0)), 6),
    }


def _digest_response(body: Dict[str, Any]) -> Dict[str, Any]:
    baseline = body.get('baseline') or {}
    return {
        'baseline_fcs_total': round(
            float((baseline.get('fcs') or {}).get('total_score', 0.0)), 6,
        ),
        'baseline_fcs_nova': (baseline.get('fcs') or {}).get('nova_category'),
        'candidates_found': (body.get('metadata') or {}).get('candidates_found'),
        'reformulation_plans': (body.get('metadata') or {}).get('reformulation_plans'),
        'suggestions': [_digest_suggestion(s) for s in body.get('suggestions') or []],
    }


def _call(case: Dict[str, Any], mode: str, max_swaps: int) -> Dict[str, Any]:
    payload = {
        'composition': case['composition'],
        'purpose': 'general_health',
        'max_suggestions': 3,
        'include_scorecard': True,
        'dish_name': case['dish_name'],
        'reformulation_mode': mode,
        'constraints': {'max_swaps': max_swaps},
    }
    r = requests.post(ENDPOINT, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def _key(case_label: str, mode: str) -> str:
    return f'{case_label} :: {mode}'


def _run_all() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for mode, max_swaps in (('singles', 1), ('greedy', 3)):
        for case in CASES:
            try:
                body = _call(case, mode, max_swaps)
                out[_key(case['label'], mode)] = _digest_response(body)
            except Exception as exc:  # noqa: BLE001
                out[_key(case['label'], mode)] = {'error': repr(exc)}
            print(f'  {mode:>7} {case["label"][:48]}')
    return out


def _diff_value(a: Any, b: Any, path: str) -> List[str]:
    diffs: List[str] = []
    if isinstance(a, float) or isinstance(b, float):
        try:
            af, bf = float(a), float(b)
        except Exception:
            diffs.append(f'  {path}: types {type(a).__name__} vs {type(b).__name__}')
            return diffs
        if math.isnan(af) and math.isnan(bf):
            return diffs
        if abs(af - bf) > FLOAT_TOL:
            diffs.append(f'  {path}: {af!r} != {bf!r} (delta {af - bf:+g})')
        return diffs
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                diffs.append(f'  {path}.{k}: missing in current (baseline={b[k]!r})')
            elif k not in b:
                diffs.append(f'  {path}.{k}: missing in baseline (current={a[k]!r})')
            else:
                diffs.extend(_diff_value(a[k], b[k], f'{path}.{k}'))
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f'  {path}: list len {len(a)} != {len(b)}')
            return diffs
        for i, (av, bv) in enumerate(zip(a, b)):
            diffs.extend(_diff_value(av, bv, f'{path}[{i}]'))
        return diffs
    if a != b:
        diffs.append(f'  {path}: {a!r} != {b!r}')
    return diffs


def capture() -> int:
    try:
        requests.get('http://127.0.0.1:8000/', timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f'Local server not reachable: {exc}\nStart it with "python manage.py runserver".')
        return 2
    snapshot = _run_all()
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f'\nWrote endpoint baseline ({len(snapshot)} cases) → {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    current = _run_all()
    print()
    total_diffs = 0
    failed: List[str] = []
    for key in sorted(baseline):
        if key not in current:
            print(f'  {key}: MISSING (not produced this run)')
            failed.append(key)
            continue
        diffs = _diff_value(current[key], baseline[key], 'root')
        if diffs:
            failed.append(key)
            print(f'  {key}: DRIFT ({len(diffs)} diffs)')
            for d in diffs[:10]:
                print(d)
            total_diffs += len(diffs)
        else:
            print(f'  {key}: ok')
    print()
    if total_diffs:
        print(f'FAIL: {len(failed)} cases drifted ({total_diffs} field diffs, tol {FLOAT_TOL})')
        return 1
    print(f'PASS: all {len(baseline)} cases match baseline (tol {FLOAT_TOL})')
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'capture'
    if mode == 'capture':
        return capture()
    if mode == 'verify':
        return verify()
    print(f'Unknown mode: {mode!r}. Use "capture" or "verify".')
    return 2


if __name__ == '__main__':
    sys.exit(main())
