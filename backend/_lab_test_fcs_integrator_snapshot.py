#!/usr/bin/env python
"""Lab Test A — low-level FCS integrator snapshot.

Picks a representative panel of food_ids, captures the integrator's per-food
outputs to JSON. Run BEFORE and AFTER the cache change to prove zero numeric
drift.

Modes:
  capture    : run integrator, write _lab_test_integrator_baseline.json
  verify     : run integrator, diff against the baseline file
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
from typing import Any, Dict, List, Tuple

import dish_project.env_bootstrap  # noqa: F401

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import django  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from fcs.models.food_item import FoodItem  # noqa: E402
from fcs.service import get_cnf_integrator  # noqa: E402


# Panel: representative mix across CNF food groups + WAFCT (700000+).
# All food_ids that appear in the user's saved-days export, plus a few extras
# to widen coverage (legume, soy beverage, fish, plant oil, NOVA-4 sample).
PANEL: List[int] = [
    # Day-1 + Day-2 meal ingredients
    61,      # Milk, partly skimmed 2%
    118,     # Butter, regular
    133,     # Egg, scrambled
    423,     # Vegetable oil, palm
    648,     # Chicken, stewing, stewed
    851,     # Chicken, broiler, thigh, roasted
    1465,    # Oats, large flakes, prepared
    1620,    # Orange juice, chilled
    1662,    # Plantain, yellow cooked
    1704,    # Banana, raw
    2091,    # Ginger root, raw
    2394,    # Garlic, raw
    2401,    # Onion, raw
    2460,    # Tomato, raw
    2933,    # Water, municipal
    3399,    # Peanut butter
    4473,    # Rice, white long-grain parboiled, cooked
    5960,    # Onion, yellow, sauteed
    6205,    # Mango nectar, canned
    6961,    # Yogurt, 2-3.9% plain
    6971,    # Yogurt, Balkan style plain
    7829,    # Butter, clarified (ghee)
    # Extra coverage — different food groups
    29,      # Golden-test food (test_fcs_rust regression anchor)
    3392,    # Lentils, raw — legume
    3732,    # Bread, white, commercial, toasted — refined grain
    2683,    # Beef, ground, lean, raw — red meat
    # WAFCT
    700194,  # Cassava, tuber, boiled
]

BASELINE_PATH = os.path.join(os.path.dirname(__file__), '_lab_test_integrator_baseline.json')
FLOAT_TOL = 1e-9


def _snapshot_food(integrator, food_id: int) -> Dict[str, Any]:
    """Capture the per-food values the cache plan affects."""
    # Energy per 100 g (Cache 1 target).
    try:
        energy_per_100g = integrator._energy_kcal_per_100g(food_id)
    except Exception as exc:  # noqa: BLE001
        return {'error': f'energy_per_100g failed: {exc!r}'}

    # Per-100g nutrient attribute map (Cache 2 target).
    # Derived from _accumulate_portion_nutrients(fid, 100.0, totals).
    nutrient_totals: Dict[str, float] = {}
    from collections import defaultdict
    nutrient_totals_dd = defaultdict(float)
    try:
        portion_energy = integrator._accumulate_portion_nutrients(
            food_id, 100.0, nutrient_totals_dd,
        )
    except Exception as exc:  # noqa: BLE001
        return {'error': f'accumulate failed: {exc!r}', 'energy_per_100g': energy_per_100g}
    nutrient_totals = dict(nutrient_totals_dd)

    # Categorization output (Cache 3 target). Run the full
    # _categorize_food_ingredients on a single-food meal and snapshot the
    # resulting FoodItem state.
    food_item = FoodItem(f'panel:{food_id}')
    try:
        integrator._categorize_food_ingredients([food_id], food_item, [100.0])
    except Exception as exc:  # noqa: BLE001
        return {
            'error': f'categorize failed: {exc!r}',
            'energy_per_100g': energy_per_100g,
            'portion_energy_100g': portion_energy,
            'nutrient_attrs_per_100g': nutrient_totals,
        }

    # Strip the 'food_name' (varies by panel suffix) from processing_details
    # so the snapshot is stable across runs.
    pd_details = food_item.get_processing_details()
    if pd_details and pd_details.get('individual_foods'):
        for f in pd_details['individual_foods']:
            f.pop('food_name', None)

    return {
        'energy_per_100g': float(energy_per_100g),
        'portion_energy_100g': float(portion_energy),
        # Per-100g attribute map sorted for stable diffing.
        'nutrient_attrs_per_100g': dict(sorted(nutrient_totals.items())),
        # All FoodItem attribute domains.
        'attributes': {
            domain: dict(sorted(attrs.items()))
            for domain, attrs in sorted(food_item.attributes.items())
        },
        'nova_processing_level': food_item.get_nova_processing_level(),
        'processing_details': pd_details,
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
        print(f'  fid={fid:<7} {"ok " if ok else "ERR"} '
              f'energy={snapshot[str(fid)].get("energy_per_100g", "?")}')
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
