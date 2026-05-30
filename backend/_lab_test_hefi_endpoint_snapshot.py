#!/usr/bin/env python
"""Lab Test B — end-to-end HEFI endpoint snapshot.

POSTs meals to /api/hefi/calculate/ and digests load-bearing numeric fields.
Run BEFORE and AFTER the cache change to prove zero behavioural drift.
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

ENDPOINT = 'http://127.0.0.1:8000/api/hefi/calculate/'
BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), '_lab_test_hefi_endpoint_baseline.json',
)
FLOAT_TOL = 1e-6


CASES: List[Dict[str, Any]] = [
    {'label': 'D1 breakfast — scrambled egg + OJ', 'foods': [
        {'food_id': 133, 'amount_g': 200},
        {'food_id': 118, 'amount_g': 8},
        {'food_id': 61, 'amount_g': 15},
        {'food_id': 1620, 'amount_g': 273},
    ]},
    {'label': 'D1 lunch — chicken biryani', 'foods': [
        {'food_id': 4473, 'amount_g': 320},
        {'food_id': 851, 'amount_g': 200},
        {'food_id': 6971, 'amount_g': 50},
        {'food_id': 5960, 'amount_g': 50},
        {'food_id': 7829, 'amount_g': 30},
        {'food_id': 2460, 'amount_g': 25},
        {'food_id': 2394, 'amount_g': 8},
        {'food_id': 2091, 'amount_g': 7},
    ]},
    {'label': 'D1 dinner — oat porridge', 'foods': [
        {'food_id': 1465, 'amount_g': 250},
        {'food_id': 61, 'amount_g': 130},
        {'food_id': 1704, 'amount_g': 65},
    ]},
    {'label': 'D2 dinner — fufu + groundnut soup', 'foods': [
        {'food_id': 700194, 'amount_g': 200},
        {'food_id': 1662, 'amount_g': 100},
        {'food_id': 2933, 'amount_g': 160},
        {'food_id': 3399, 'amount_g': 70},
        {'food_id': 648, 'amount_g': 120},
        {'food_id': 2460, 'amount_g': 50},
        {'food_id': 2401, 'amount_g': 30},
        {'food_id': 423, 'amount_g': 15},
    ]},
    {'label': 'D1 AGGREGATED (14 foods)', 'foods': [
        {'food_id': 4473, 'amount_g': 320},
        {'food_id': 1620, 'amount_g': 273},
        {'food_id': 1465, 'amount_g': 250},
        {'food_id': 133, 'amount_g': 200},
        {'food_id': 851, 'amount_g': 200},
        {'food_id': 61, 'amount_g': 145},
        {'food_id': 1704, 'amount_g': 65},
        {'food_id': 6971, 'amount_g': 50},
        {'food_id': 5960, 'amount_g': 50},
        {'food_id': 7829, 'amount_g': 30},
        {'food_id': 2460, 'amount_g': 25},
        {'food_id': 118, 'amount_g': 8},
        {'food_id': 2394, 'amount_g': 8},
        {'food_id': 2091, 'amount_g': 7},
    ]},
    {'label': 'D2 AGGREGATED (11 foods)', 'foods': [
        {'food_id': 6205, 'amount_g': 240},
        {'food_id': 700194, 'amount_g': 200},
        {'food_id': 2933, 'amount_g': 160},
        {'food_id': 133, 'amount_g': 150},
        {'food_id': 648, 'amount_g': 120},
        {'food_id': 1662, 'amount_g': 100},
        {'food_id': 3399, 'amount_g': 70},
        {'food_id': 2460, 'amount_g': 50},
        {'food_id': 2401, 'amount_g': 30},
        {'food_id': 423, 'amount_g': 15},
        {'food_id': 118, 'amount_g': 8},
    ]},
]

# Same strip strategy as the env test — exclude prose / text keys and any
# top-level branches with known non-determinism.
_TEXT_KEY_HINTS = (
    'explanation', 'simple_explanation', 'detailed_explanation', 'what_it_means',
    'action_tips', 'title', 'description', 'rationale', 'notes', 'message',
    '_data_source', '_confidence', '_last_updated', '_notes', 'methodology_info',
    'definition', 'background', 'caveat', 'disclaimer', 'help_text', 'name',
)
_DROP_BRANCH_KEYS: tuple[str, ...] = ()


def _is_text_key(k: str) -> bool:
    kl = str(k).lower()
    return any(hint in kl for hint in _TEXT_KEY_HINTS)


def _round_floats(v: Any) -> Any:
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, dict):
        out = {}
        for k, val in v.items():
            if _is_text_key(k):
                continue
            if k in _DROP_BRANCH_KEYS:
                continue
            if isinstance(val, str) and len(val) > 200:
                continue
            out[k] = _round_floats(val)
        return out
    if isinstance(v, list):
        return [_round_floats(x) for x in v]
    return v


def _call(case: Dict[str, Any]) -> Dict[str, Any]:
    payload = {'foods': case['foods'], 'user_type': 'individual'}
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
                diffs.append(f'  {path}.{k}: missing current')
            elif k not in b:
                diffs.append(f'  {path}.{k}: missing baseline')
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
            out[case['label']] = _round_floats(body)
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
    print(f'\nWrote HEFI endpoint baseline ({len(snapshot)} cases) → {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    current = _run_all()
    print()
    total = 0
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
            total += len(diffs)
        else:
            print(f'  {key}: ok')
    print()
    if total:
        print(f'FAIL: {len(failed)} cases drifted ({total} diffs, tol {FLOAT_TOL})')
        return 1
    print(f'PASS: all {len(baseline)} cases match baseline (tol {FLOAT_TOL})')
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'capture'
    if mode == 'capture':
        return capture()
    if mode == 'verify':
        return verify()
    print(f'Unknown mode: {mode!r}.')
    return 2


if __name__ == '__main__':
    sys.exit(main())
