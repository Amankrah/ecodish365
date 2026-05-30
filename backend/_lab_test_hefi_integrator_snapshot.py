#!/usr/bin/env python
"""Lab Test A — low-level HEFI CNF integrator snapshot.

Captures per-food integrator outputs the cache plan will affect:
  - _get_best_conversion_factor(food_id)
  - get_measure_description(food_id, conversion_factor)
  - aggregate_inputs([(food_id, 100.0)]) result for each food in isolation
    (covers RA classification + nutrient slicing per food).
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

from django.conf import settings  # noqa: E402
from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator  # noqa: E402


PANEL: List[int] = [
    61, 118, 133, 423, 648, 851, 1465, 1620, 1662, 1704,
    2091, 2394, 2401, 2460, 2933, 3399, 4473, 5960, 6205,
    6961, 6971, 7829,
    29, 3392, 3732, 2683,
    700194,
]

BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), '_lab_test_hefi_integrator_baseline.json',
)
FLOAT_TOL = 1e-9

_integrator: HEFICNFIntegrator | None = None


def _get_integrator() -> HEFICNFIntegrator:
    global _integrator
    if _integrator is None:
        _integrator = HEFICNFIntegrator(str(settings.CNF_FOLDER))
    return _integrator


def _snapshot_food(integrator: HEFICNFIntegrator, food_id: int) -> Dict[str, Any]:
    try:
        cf = integrator._get_best_conversion_factor(food_id)
        md = integrator.get_measure_description(food_id, cf)
        agg = integrator.aggregate_inputs([(food_id, 100.0)])
    except Exception as exc:  # noqa: BLE001
        return {'error': f'snapshot failed: {exc!r}'}
    return {
        'conversion_factor': float(cf),
        'measure_description': str(md),
        'aggregate_inputs_at_100g': {k: float(v) for k, v in sorted(agg.items())},
    }


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


def capture() -> int:
    integrator = _get_integrator()
    snapshot: Dict[str, Any] = {}
    for fid in PANEL:
        snapshot[str(fid)] = _snapshot_food(integrator, fid)
        ok = 'error' not in snapshot[str(fid)]
        cf = snapshot[str(fid)].get('conversion_factor', '?')
        print(f'  fid={fid:<7} {"ok " if ok else "ERR"} cf={cf}')
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f'\nWrote HEFI integrator baseline ({len(PANEL)} foods) → {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    integrator = _get_integrator()
    total = 0
    failed: List[int] = []
    for fid in PANEL:
        current = _snapshot_food(integrator, fid)
        b = baseline.get(str(fid))
        if b is None:
            print(f'  fid={fid}: NEW')
            failed.append(fid)
            continue
        diffs = _diff(current, b, 'root')
        if diffs:
            failed.append(fid)
            print(f'  fid={fid}: DRIFT ({len(diffs)} diffs)')
            for d in diffs[:8]:
                print(d)
            total += len(diffs)
        else:
            print(f'  fid={fid}: ok')
    print()
    if total:
        print(f'FAIL: {len(failed)}/{len(PANEL)} foods drifted ({total} diffs)')
        return 1
    print(f'PASS: all {len(PANEL)} foods match baseline (tol {FLOAT_TOL})')
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
