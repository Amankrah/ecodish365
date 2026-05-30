#!/usr/bin/env python
"""Lab Test A — low-level HENI CNF integrator snapshot.

Same shape as the FCS lab test: picks a representative panel of food_ids,
captures each public per-food helper's output to JSON. Run BEFORE and AFTER
the cache change to prove zero numeric drift.

Modes:
  capture : run integrator, write _lab_test_heni_integrator_baseline.json
  verify  : run integrator, diff against the baseline
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
from typing import Any, Dict, List

import dish_project.env_bootstrap  # noqa: F401

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import django  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from heni_calculator.heni.service import get_cnf_integrator  # noqa: E402


# Same panel as the FCS lab test for cross-comparison + tight WAFCT coverage.
PANEL: List[int] = [
    61, 118, 133, 423, 648, 851, 1465, 1620, 1662, 1704,
    2091, 2394, 2401, 2460, 2933, 3399, 4473, 5960, 6205,
    6961, 6971, 7829,
    # Different food groups for risk-factor mapping coverage
    29, 3392, 3732, 2683,
    # WAFCT
    700194,
]

BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), '_lab_test_heni_integrator_baseline.json',
)
FLOAT_TOL = 1e-9


def _snapshot_food(integrator, food_id: int) -> Dict[str, Any]:
    """Capture every public per-food helper output."""
    try:
        kcal = integrator.get_kcal(food_id)
        desc = integrator.get_food_description(food_id)
        group = integrator.get_food_group(food_id)
        nutrients = integrator.get_nutrient_data(food_id)
        risks = integrator.get_dietary_risks(food_id)
    except Exception as exc:  # noqa: BLE001
        return {'error': f'snapshot failed: {exc!r}'}

    # WAFCT food rows can carry NaN (float) NutrientName values when a
    # nutrient_id has no entry in nutrient_name_df. Coerce keys to str so
    # sort comparisons + JSON serialisation are stable.
    def _stringify_keys(d: Dict[Any, float]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k, v in d.items():
            sk = str(k)
            out[sk] = float(v)
        return dict(sorted(out.items()))

    return {
        'kcal': float(kcal),
        'description': str(desc),
        'food_group': str(group),
        'nutrient_data': _stringify_keys(nutrients),
        'dietary_risks': _stringify_keys(risks),
    }


def _floats_match(a: Any, b: Any, path: str) -> List[str]:
    diffs: List[str] = []
    if isinstance(a, float) or isinstance(b, float):
        try:
            af, bf = float(a), float(b)
        except Exception:
            diffs.append(f'  {path}: type mismatch {type(a).__name__} vs {type(b).__name__}')
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
                diffs.extend(_floats_match(a[k], b[k], f'{path}.{k}'))
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f'  {path}: list len {len(a)} != {len(b)}')
            return diffs
        for i, (av, bv) in enumerate(zip(a, b)):
            diffs.extend(_floats_match(av, bv, f'{path}[{i}]'))
        return diffs
    if a != b:
        diffs.append(f'  {path}: {a!r} != {b!r}')
    return diffs


def capture() -> int:
    integrator = get_cnf_integrator()
    snapshot: Dict[str, Any] = {}
    for fid in PANEL:
        snapshot[str(fid)] = _snapshot_food(integrator, fid)
        ok = 'error' not in snapshot[str(fid)]
        kcal = snapshot[str(fid)].get('kcal', '?')
        print(f'  fid={fid:<7} {"ok " if ok else "ERR"} kcal={kcal}')
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f'\nWrote baseline for {len(PANEL)} foods → {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    integrator = get_cnf_integrator()
    total_diffs = 0
    failed_fids: List[int] = []
    for fid in PANEL:
        current = _snapshot_food(integrator, fid)
        b = baseline.get(str(fid))
        if b is None:
            print(f'  fid={fid}: NEW (not in baseline)')
            failed_fids.append(fid)
            continue
        diffs = _floats_match(current, b, 'root')
        if diffs:
            failed_fids.append(fid)
            print(f'  fid={fid}: DRIFT ({len(diffs)} diffs)')
            for d in diffs[:8]:
                print(d)
            total_diffs += len(diffs)
        else:
            print(f'  fid={fid}: ok')
    print()
    if total_diffs:
        print(f'FAIL: {len(failed_fids)}/{len(PANEL)} foods drifted ({total_diffs} field diffs)')
        return 1
    print(f'PASS: all {len(PANEL)} foods match baseline (tol {FLOAT_TOL})')
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
