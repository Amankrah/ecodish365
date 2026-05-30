"""Ground-truth pre-check — assert the prep-state GT is internally consistent.

For every probe in ``_lab_prep_state_groundtruth.json``, runs the regex
extractor on ``expected_food_ids[0]``'s CNF/WAFCT FoodDescription and
asserts:
  1. The extracted thermal matches expected_thermal (via the same asymmetric
     equivalence the matcher probe uses).
  2. The extracted preservation matches expected_preservation.

When a probe FAILS this pre-check, one of two things is true:
  a. The GT row is wrong (most common — the curator picked a FoodID whose
     description doesn't encode the asserted prep state).
  b. The extractor still has a regex gap on that description.

Either way the lab can't trust matcher accuracy numbers on that probe until
the inconsistency is fixed. This script must pass before the Phase 2 tagger
eval runs against the same GT.

Run:
  python _lab_test_prep_state_gt_precheck.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from typing import Any, Dict, List

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
os.environ.setdefault('DJANGO_SECRET_KEY', 'lab-gt-precheck')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.cnf_cache import get_api_cnf_pipeline  # noqa: E402
from api.services.prep_state_extract import (  # noqa: E402
    extract_prep_state,
    thermal_states_equivalent,
    preservation_states_equivalent,
)

GROUNDTRUTH_PATH = os.path.join(_HERE, '_lab_prep_state_groundtruth.json')


def _hydrate_descriptions(food_ids: List[int]) -> Dict[int, str]:
    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    sub = fn[fn['FoodID'].isin(food_ids)][['FoodID', 'FoodDescription']]
    return {int(r['FoodID']): str(r['FoodDescription']) for _, r in sub.iterrows()}


def main() -> int:
    with open(GROUNDTRUTH_PATH, encoding='utf-8') as f:
        gt = json.load(f)
    probes = gt['probes']

    all_fids = [p['expected_food_ids'][0] for p in probes if p['expected_food_ids']]
    desc_by_fid = _hydrate_descriptions(all_fids)

    n_pass = n_fail = 0
    failures: List[Dict[str, Any]] = []
    print(f'Pre-checking {len(probes)} probes against extract_prep_state(...)')
    print('-' * 100)
    for p in probes:
        if not p['expected_food_ids']:
            print(f'  [SKIP] {p["label"]}: no expected_food_ids')
            continue
        fid = p['expected_food_ids'][0]
        desc = desc_by_fid.get(fid, '')
        if not desc:
            print(f'  [SKIP] {p["label"]}: FoodID {fid} not found in CNF/WAFCT')
            continue

        ext = extract_prep_state(desc)
        exp_t = p['expected_thermal_state']
        exp_p = p['expected_preservation_state']
        t_ok = thermal_states_equivalent(ext.thermal_state, exp_t)
        p_ok = preservation_states_equivalent(ext.preservation_state, exp_p)

        if t_ok and p_ok:
            n_pass += 1
        else:
            n_fail += 1
            failures.append({
                'label': p['label'],
                'food_id': fid,
                'description': desc,
                'expected': (exp_t, exp_p),
                'extracted': (ext.thermal_state, ext.preservation_state),
                'thermal_ok': t_ok,
                'preservation_ok': p_ok,
                'reason': p.get('notes', ''),
            })
            marks = ('T' if t_ok else 't') + ('P' if p_ok else 'p')
            print(f'  [{marks}] {p["label"]:<32}  fid={fid:<6}  '
                  f'exp=({exp_t}/{exp_p})  got=({ext.thermal_state}/{ext.preservation_state})  '
                  f'desc={desc[:55]!r}')

    print('-' * 100)
    print(f'PASS {n_pass}/{n_pass + n_fail}  FAIL {n_fail}/{n_pass + n_fail}')
    print()
    if failures:
        print('Resolution paths:')
        print('  - GT row is wrong: update expected_food_ids[0] to a FoodID whose description encodes the asserted prep.')
        print('  - Extractor gap: add the missing vocabulary to prep_state_extract._THERMAL_PATTERNS / _PRESERVATION_PATTERNS.')
        print()
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
