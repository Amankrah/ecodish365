#!/usr/bin/env python
"""HTTP-level test of /api/substitution/analyze/ against the user's saved-days
export. Times every meal + every aggregated daily composition in both
reformulation modes (singles, greedy max_swaps=3 — the 'Multi-step plan' UI)."""
from __future__ import annotations

import io
import json
import sys
import time
from typing import Any, Dict, List

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

ENDPOINT = 'http://127.0.0.1:8000/api/substitution/analyze/'


CASES: List[Dict[str, Any]] = [
    # ---- Day 1 individual meals -----------------------------------------
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
    # ---- Day 2 individual meals -----------------------------------------
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
        'label': 'D2 dinner — fufu + groundnut soup (WAFCT)',
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
    # ---- Aggregated daily compositions (the production hot path) --------
    {
        'label': 'D1 AGGREGATED (14 ing)',
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
        'label': 'D2 AGGREGATED (11 ing, matches prod screenshot)',
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


def call(case: Dict[str, Any], mode: str, max_swaps: int) -> Dict[str, Any]:
    payload = {
        'composition': case['composition'],
        'purpose': 'general_health',
        'max_suggestions': 3,
        'include_scorecard': True,
        'dish_name': case['dish_name'],
        'reformulation_mode': mode,
        'constraints': {'max_swaps': max_swaps},
    }
    t0 = time.perf_counter()
    r = requests.post(ENDPOINT, json=payload, timeout=180)
    wall_ms = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    body = r.json()
    return {
        'wall_ms': wall_ms,
        'server_ms': body.get('metadata', {}).get('elapsed_ms'),
        'candidates': body.get('metadata', {}).get('candidates_found', 0),
        'n_suggestions': len(body.get('suggestions', [])),
        'n_plans': body.get('metadata', {}).get('reformulation_plans', 0),
        'top': (body.get('suggestions') or [None])[0],
    }


def main() -> int:
    # Probe the server first.
    try:
        requests.get('http://127.0.0.1:8000/', timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f'Local Django server not reachable at 127.0.0.1:8000 — {exc}')
        print('Start it first: cd backend && python manage.py runserver')
        return 1

    print(f'{"meal":<50} {"mode":>8} {"swaps":>5} {"ings":>4} {"cands":>5} '
          f'{"sugg":>4} {"plans":>5} {"wall ms":>9} {"srv ms":>8}  top swap')
    print('-' * 150)
    rows = []
    for mode, max_swaps in (('singles', 1), ('greedy', 3)):
        for case in CASES:
            try:
                r = call(case, mode, max_swaps)
            except Exception as exc:  # noqa: BLE001
                print(f'{case["label"][:50]:<50} {mode:>8} {max_swaps:>5}  ERROR: {exc}')
                continue
            top_desc = ''
            if r['top']:
                o = r['top']['original']['food_description'][:22]
                rp = r['top']['replacement']['food_description'][:22]
                fcs_d = (r['top'].get('fcs') or {}).get('delta', 0)
                top_desc = f'[{o} -> {rp}] dFCS={fcs_d:+.2f}'
            print(f'{case["label"][:50]:<50} {mode:>8} {max_swaps:>5} '
                  f'{len(case["composition"]):>4} {r["candidates"]:>5} '
                  f'{r["n_suggestions"]:>4} {r["n_plans"]:>5} '
                  f'{r["wall_ms"]:>9.0f} {(r["server_ms"] or 0):>8.0f}  {top_desc}')
            rows.append({'mode': mode, 'case': case['label'],
                         'wall_ms': r['wall_ms'], 'server_ms': r['server_ms']})

    print('-' * 150)
    singles = [r for r in rows if r['mode'] == 'singles']
    greedy = [r for r in rows if r['mode'] == 'greedy']
    if singles:
        avg_s = sum(r['wall_ms'] for r in singles) / len(singles)
        max_s = max(r['wall_ms'] for r in singles)
        print(f'SINGLES  avg={avg_s:>7.0f} ms   max={max_s:>7.0f} ms')
    if greedy:
        avg_g = sum(r['wall_ms'] for r in greedy) / len(greedy)
        max_g = max(r['wall_ms'] for r in greedy)
        print(f'GREEDY   avg={avg_g:>7.0f} ms   max={max_g:>7.0f} ms')
    return 0


if __name__ == '__main__':
    sys.exit(main())
