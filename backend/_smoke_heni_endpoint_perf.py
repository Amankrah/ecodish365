#!/usr/bin/env python
"""Perf benchmark for /api/heni/calculate/ — same panel as the snapshot test.

Times each meal twice (warmup + measured) so the printed numbers reflect
steady-state cost (the first request loads the pipeline and pays cache-miss
tax; the second is what the user sees on every subsequent call).
"""
from __future__ import annotations

import io
import sys
import time
from typing import Any, Dict, List

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

ENDPOINT = 'http://127.0.0.1:8000/api/heni/calculate/'


CASES: List[Dict[str, Any]] = [
    {'label': 'D1 breakfast (4 ing)', 'meal': [
        {'food_id': 133, 'amount': 200, 'unit': 'g'},
        {'food_id': 118, 'amount': 8, 'unit': 'g'},
        {'food_id': 61, 'amount': 15, 'unit': 'g'},
        {'food_id': 1620, 'amount': 273, 'unit': 'g'},
    ]},
    {'label': 'D1 biryani (8 ing)', 'meal': [
        {'food_id': 4473, 'amount': 320, 'unit': 'g'},
        {'food_id': 851, 'amount': 200, 'unit': 'g'},
        {'food_id': 6971, 'amount': 50, 'unit': 'g'},
        {'food_id': 5960, 'amount': 50, 'unit': 'g'},
        {'food_id': 7829, 'amount': 30, 'unit': 'g'},
        {'food_id': 2460, 'amount': 25, 'unit': 'g'},
        {'food_id': 2394, 'amount': 8, 'unit': 'g'},
        {'food_id': 2091, 'amount': 7, 'unit': 'g'},
    ]},
    {'label': 'D1 porridge (3 ing)', 'meal': [
        {'food_id': 1465, 'amount': 250, 'unit': 'g'},
        {'food_id': 61, 'amount': 130, 'unit': 'g'},
        {'food_id': 1704, 'amount': 65, 'unit': 'g'},
    ]},
    {'label': 'D2 fufu (8 ing)', 'meal': [
        {'food_id': 700194, 'amount': 200, 'unit': 'g'},
        {'food_id': 1662, 'amount': 100, 'unit': 'g'},
        {'food_id': 2933, 'amount': 160, 'unit': 'g'},
        {'food_id': 3399, 'amount': 70, 'unit': 'g'},
        {'food_id': 648, 'amount': 120, 'unit': 'g'},
        {'food_id': 2460, 'amount': 50, 'unit': 'g'},
        {'food_id': 2401, 'amount': 30, 'unit': 'g'},
        {'food_id': 423, 'amount': 15, 'unit': 'g'},
    ]},
    {'label': 'D1 AGGREGATED (14 ing)', 'meal': [
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
    ]},
    {'label': 'D2 AGGREGATED (11 ing)', 'meal': [
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
    ]},
]


def call(case: Dict[str, Any]) -> float:
    t0 = time.perf_counter()
    r = requests.post(ENDPOINT, json={'meal': case['meal'], 'user_type': 'individual'}, timeout=180)
    wall = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    return wall


def main() -> int:
    try:
        requests.get('http://127.0.0.1:8000/', timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f'Server not reachable: {exc}')
        return 1

    # Warmup: the process-singleton integrator + pipeline takes a one-time
    # hit on the first request. Measure the SECOND call so timing reflects
    # steady-state, not cold-start.
    print('warmup...')
    call(CASES[0])

    print(f'\n{"meal":<32} {"ings":>4} {"wall ms":>8}')
    print('-' * 50)
    total = 0.0
    for case in CASES:
        ms = call(case)
        total += ms
        print(f'{case["label"][:32]:<32} {len(case["meal"]):>4} {ms:>8.0f}')
    print('-' * 50)
    print(f'{"TOTAL":<32} {"":>4} {total:>8.0f}')
    print(f'avg per meal: {total / len(CASES):.0f} ms')
    return 0


if __name__ == '__main__':
    sys.exit(main())
