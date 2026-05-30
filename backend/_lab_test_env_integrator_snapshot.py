#!/usr/bin/env python
"""Lab Test A — low-level environmental CNF integrator snapshot.

Captures every per-food integrator output that the cache will affect:
  - get_food_data(food_id)
  - get_environmental_impact_factors(food_id)
  - get_nutrient_amount(food_id, nutrient_name) for a panel of nutrients
  - get_conversion_factor(food_id, measure_id) for a panel of measure_ids
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

from environmental_impact_model.src.cnf_integrator import get_cnf_integrator  # noqa: E402


PANEL: List[int] = [
    61, 118, 133, 423, 648, 851, 1465, 1620, 1662, 1704,
    2091, 2394, 2401, 2460, 2933, 3399, 4473, 5960, 6205,
    6961, 6971, 7829,
    29, 3392, 3732, 2683,
    700194,
]

# Nutrients that hit get_nutrient_amount on the env LCA path.
NUTRIENT_PANEL = ['PROTEIN', 'FIBRE, TOTAL DIETARY', 'VITAMIN A', 'VITAMIN C',
                  'ENERGY (KILOCALORIES)', 'CALCIUM', 'IRON']

# A few common MeasureIDs covering serving / cup / piece scales.
MEASURE_PANEL = [1, 2, 3, 100, 200, 341]

BASELINE_PATH = os.path.join(
    os.path.dirname(__file__), '_lab_test_env_integrator_baseline.json',
)
FLOAT_TOL = 1e-9


_DROP_KEYS = (
    # WAFCT ingest stamps datetime.now() into FoodDate* / NutrientDate* on
    # every Django reload, so these fields are NOT stable across process
    # restarts — and they have no bearing on any environmental computation.
    'FoodDateOfEntry', 'FoodDateOfPublication',
    'NutrientDateOfEntry', 'NutrientDateOfPublication',
    'NutrientUpdated', 'NutrientCreated',
)


def _coerce(v: Any) -> Any:
    """Make pandas/numpy values plain Python types so the JSON snapshot is
    byte-stable across runs."""
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return 'NaN'
        return v
    if isinstance(v, (int, str, bool)):
        return v
    # numpy scalars
    try:
        import numpy as np
        if isinstance(v, np.generic):
            return _coerce(v.item())
    except Exception:
        pass
    if isinstance(v, dict):
        return {str(k): _coerce(val) for k, val in v.items() if k not in _DROP_KEYS}
    if isinstance(v, (list, tuple)):
        return [_coerce(x) for x in v]
    # Fallback — stringify anything exotic
    return str(v)


def _digest_food_data(food_data) -> Any:
    if food_data is None:
        return None
    out: Dict[str, Any] = {}
    out['food_info'] = _coerce(food_data.get('food_info') or {})
    out['food_group'] = _coerce(food_data.get('food_group') or {})
    # Sort lists of records by FoodID/NutrientID/MeasureID-like key for stable diff
    nutrients = food_data.get('nutrients') or []
    out['nutrients'] = sorted(
        (_coerce(n) for n in nutrients),
        key=lambda r: (str(r.get('FoodID', '')), str(r.get('NutrientID', ''))),
    )
    conv = food_data.get('conversion_factors') or []
    out['conversion_factors'] = sorted(
        (_coerce(c) for c in conv),
        key=lambda r: (str(r.get('FoodID', '')), str(r.get('MeasureID', ''))),
    )
    return out


def _snapshot_food(integrator, food_id: int) -> Dict[str, Any]:
    try:
        fd = integrator.get_food_data(food_id)
    except Exception as exc:  # noqa: BLE001
        return {'error': f'get_food_data failed: {exc!r}'}
    try:
        factors = integrator.get_environmental_impact_factors(food_id)
    except Exception as exc:  # noqa: BLE001
        return {
            'food_data': _digest_food_data(fd),
            'error': f'get_environmental_impact_factors failed: {exc!r}',
        }

    nutrient_amounts = {
        n: _coerce(integrator.get_nutrient_amount(food_id, n))
        for n in NUTRIENT_PANEL
    }
    conversion_factors = {
        str(m): _coerce(integrator.get_conversion_factor(food_id, m))
        for m in MEASURE_PANEL
    }
    return {
        'food_data': _digest_food_data(fd),
        'environmental_impact_factors': _coerce(factors),
        'nutrient_amounts': nutrient_amounts,
        'conversion_factors': conversion_factors,
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


def _ensure_initialized(integrator) -> None:
    if not integrator.is_initialized():
        integrator.initialize()


def capture() -> int:
    integrator = get_cnf_integrator()
    _ensure_initialized(integrator)
    snapshot: Dict[str, Any] = {}
    for fid in PANEL:
        snapshot[str(fid)] = _snapshot_food(integrator, fid)
        ok = 'error' not in snapshot[str(fid)]
        print(f'  fid={fid:<7} {"ok " if ok else "ERR"}')
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, sort_keys=True)
    print(f'\nWrote env integrator baseline ({len(PANEL)} foods) → {BASELINE_PATH}')
    return 0


def verify() -> int:
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    integrator = get_cnf_integrator()
    _ensure_initialized(integrator)
    total_diffs = 0
    failed = []
    for fid in PANEL:
        current = _snapshot_food(integrator, fid)
        b = baseline.get(str(fid))
        if b is None:
            print(f'  fid={fid}: NEW (no baseline)')
            failed.append(fid)
            continue
        diffs = _diff(current, b, 'root')
        if diffs:
            failed.append(fid)
            print(f'  fid={fid}: DRIFT ({len(diffs)} diffs)')
            for d in diffs[:8]:
                print(d)
            total_diffs += len(diffs)
        else:
            print(f'  fid={fid}: ok')
    print()
    if total_diffs:
        print(f'FAIL: {len(failed)}/{len(PANEL)} foods drifted ({total_diffs} field diffs)')
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
