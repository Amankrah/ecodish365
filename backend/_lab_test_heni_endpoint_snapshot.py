#!/usr/bin/env python
"""Lab Test B — end-to-end HENI endpoint snapshot.

POSTs a panel of compositions to /api/heni/calculate/ and captures the
load-bearing numeric fields. Run BEFORE and AFTER the integrator cache
change to prove zero behavioural drift.

Modes:
  capture : POST each case, save digest → _lab_test_heni_endpoint_baseline.json
  verify  : POST each case, diff digest against baseline

The Django dev server must be reachable at 127.0.0.1:8000.
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

ENDPOINT = 'http://127.0.0.1:8000/api/heni/calculate/'
BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), '_lab_test_heni_endpoint_baseline.json',
)
FLOAT_TOL = 1e-6


CASES: List[Dict[str, Any]] = [
    {
        'label': 'D1 breakfast — scrambled egg + OJ',
        'meal': [
            {'food_id': 133, 'amount': 200, 'unit': 'g'},
            {'food_id': 118, 'amount': 8, 'unit': 'g'},
            {'food_id': 61, 'amount': 15, 'unit': 'g'},
            {'food_id': 1620, 'amount': 273, 'unit': 'g'},
        ],
    },
    {
        'label': 'D1 lunch — chicken biryani',
        'meal': [
            {'food_id': 4473, 'amount': 320, 'unit': 'g'},
            {'food_id': 851, 'amount': 200, 'unit': 'g'},
            {'food_id': 6971, 'amount': 50, 'unit': 'g'},
            {'food_id': 5960, 'amount': 50, 'unit': 'g'},
            {'food_id': 7829, 'amount': 30, 'unit': 'g'},
            {'food_id': 2460, 'amount': 25, 'unit': 'g'},
            {'food_id': 2394, 'amount': 8, 'unit': 'g'},
            {'food_id': 2091, 'amount': 7, 'unit': 'g'},
        ],
    },
    {
        'label': 'D1 dinner — oat porridge',
        'meal': [
            {'food_id': 1465, 'amount': 250, 'unit': 'g'},
            {'food_id': 61, 'amount': 130, 'unit': 'g'},
            {'food_id': 1704, 'amount': 65, 'unit': 'g'},
        ],
    },
    {
        'label': 'D2 dinner — fufu + groundnut soup',
        'meal': [
            {'food_id': 700194, 'amount': 200, 'unit': 'g'},
            {'food_id': 1662, 'amount': 100, 'unit': 'g'},
            {'food_id': 2933, 'amount': 160, 'unit': 'g'},
            {'food_id': 3399, 'amount': 70, 'unit': 'g'},
            {'food_id': 648, 'amount': 120, 'unit': 'g'},
            {'food_id': 2460, 'amount': 50, 'unit': 'g'},
            {'food_id': 2401, 'amount': 30, 'unit': 'g'},
            {'food_id': 423, 'amount': 15, 'unit': 'g'},
        ],
    },
    {
        'label': 'D1 AGGREGATED (14 ing)',
        'meal': [
            {'food_id': 4473, 'amount': 320, 'unit': 'g'},
            {'food_id': 1620, 'amount': 273, 'unit': 'g'},
            {'food_id': 1465, 'amount': 250, 'unit': 'g'},
            {'food_id': 133, 'amount': 200, 'unit': 'g'},
            {'food_id': 851, 'amount': 200, 'unit': 'g'},
            {'food_id': 61, 'amount': 145, 'unit': 'g'},
            {'food_id': 1704, 'amount': 65, 'unit': 'g'},
            {'food_id': 6971, 'amount': 50, 'unit': 'g'},
            {'food_id': 5960, 'amount': 50, 'unit': 'g'},
            {'food_id': 7829, 'amount': 30, 'unit': 'g'},
            {'food_id': 2460, 'amount': 25, 'unit': 'g'},
            {'food_id': 118, 'amount': 8, 'unit': 'g'},
            {'food_id': 2394, 'amount': 8, 'unit': 'g'},
            {'food_id': 2091, 'amount': 7, 'unit': 'g'},
        ],
    },
    {
        'label': 'D2 AGGREGATED (11 ing)',
        'meal': [
            {'food_id': 6205, 'amount': 240, 'unit': 'g'},
            {'food_id': 700194, 'amount': 200, 'unit': 'g'},
            {'food_id': 2933, 'amount': 160, 'unit': 'g'},
            {'food_id': 133, 'amount': 150, 'unit': 'g'},
            {'food_id': 648, 'amount': 120, 'unit': 'g'},
            {'food_id': 1662, 'amount': 100, 'unit': 'g'},
            {'food_id': 3399, 'amount': 70, 'unit': 'g'},
            {'food_id': 2460, 'amount': 50, 'unit': 'g'},
            {'food_id': 2401, 'amount': 30, 'unit': 'g'},
            {'food_id': 423, 'amount': 15, 'unit': 'g'},
            {'food_id': 118, 'amount': 8, 'unit': 'g'},
        ],
    },
]


def _round(v: Any, p: int = 6) -> Any:
    try:
        return round(float(v), p)
    except (TypeError, ValueError):
        return v


def _digest_response(body: Dict[str, Any]) -> Dict[str, Any]:
    """Pull just the load-bearing numeric fields so the snapshot is stable
    (top-level metadata like timestamps would otherwise create noise)."""
    hp = body.get('health_impact') or {}
    scores = body.get('heni_scores') or {}
    daly = body.get('daly_breakdown') or {}
    ingredients = body.get('ingredients') or []
    return {
        'health_impact_minutes': _round(hp.get('health_impact_minutes')),
        'total_heni_score': _round(scores.get('total_heni_score')),
        'health_impact_minutes_2': _round(scores.get('health_impact_minutes')),
        'daly_breakdown_keys': sorted((daly or {}).keys()),
        'daly_values': {k: _round(v) for k, v in sorted((daly or {}).items())},
        'risk_factor_contributions': {
            k: _round(v) for k, v in sorted((body.get('risk_factor_contributions') or {}).items())
        },
        'per_ingredient': [
            {
                'food_id': ing.get('food_id'),
                'description': ing.get('description'),
                'amount': _round(ing.get('amount')),
                'health_impact_minutes': _round(ing.get('health_impact_minutes')),
                'total_heni_score': _round(ing.get('total_heni_score')),
            }
            for ing in ingredients
        ],
    }


def _call(case: Dict[str, Any]) -> Dict[str, Any]:
    payload = {'meal': case['meal'], 'user_type': 'individual'}
    r = requests.post(ENDPOINT, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()


def _diff(a: Any, b: Any, path: str) -> List[str]:
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
                diffs.append(f'  {path}.{k}: missing current (baseline={b[k]!r})')
            elif k not in b:
                diffs.append(f'  {path}.{k}: missing baseline (current={a[k]!r})')
            else:
                diffs.extend(_diff(a[k], b[k], f'{path}.{k}'))
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f'  {path}: list len {len(a)} != {len(b)}')
            return diffs
        for i, (av, bv) in enumerate(zip(a, b)):
            diffs.extend(_diff(av, bv, f'{path}[{i}]'))
        return diffs
    if a != b:
        diffs.append(f'  {path}: {a!r} != {b!r}')
    return diffs


def _run_all() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for case in CASES:
        try:
            body = _call(case)
            out[case['label']] = _digest_response(body)
        except Exception as exc:  # noqa: BLE001
            out[case['label']] = {'error': repr(exc)}
        print(f'  {case["label"][:55]}')
    return out


def capture() -> int:
    try:
        requests.get('http://127.0.0.1:8000/', timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f'Server not reachable: {exc}')
        return 2
    snapshot = _run_all()
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f'\nWrote HENI endpoint baseline ({len(snapshot)} cases) → {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    current = _run_all()
    print()
    total_diffs = 0
    failed: List[str] = []
    for key in sorted(baseline):
        if key not in current:
            print(f'  {key}: MISSING')
            failed.append(key)
            continue
        diffs = _diff(current[key], baseline[key], 'root')
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
