#!/usr/bin/env python
"""Perf benchmark for /api/environmental-impact/ — same panel as the
snapshot. Warmup once, then measure steady-state.
"""
from __future__ import annotations

import io
import sys
import time
from typing import Any, Dict, List

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

ENDPOINT = 'http://127.0.0.1:8000/api/environmental-impact/'


CASES: List[Dict[str, Any]] = [
    {'label': 'D1 breakfast (4 foods)', 'foods': [
        {'food_id': 133, 'quantity': 200},
        {'food_id': 118, 'quantity': 8},
        {'food_id': 61, 'quantity': 15},
        {'food_id': 1620, 'quantity': 273},
    ]},
    {'label': 'D1 biryani (8 foods)', 'foods': [
        {'food_id': 4473, 'quantity': 320},
        {'food_id': 851, 'quantity': 200},
        {'food_id': 6971, 'quantity': 50},
        {'food_id': 5960, 'quantity': 50},
        {'food_id': 7829, 'quantity': 30},
        {'food_id': 2460, 'quantity': 25},
        {'food_id': 2394, 'quantity': 8},
        {'food_id': 2091, 'quantity': 7},
    ]},
    {'label': 'D1 porridge (3 foods)', 'foods': [
        {'food_id': 1465, 'quantity': 250},
        {'food_id': 61, 'quantity': 130},
        {'food_id': 1704, 'quantity': 65},
    ]},
    {'label': 'D2 fufu (8 foods)', 'foods': [
        {'food_id': 700194, 'quantity': 200},
        {'food_id': 1662, 'quantity': 100},
        {'food_id': 2933, 'quantity': 160},
        {'food_id': 3399, 'quantity': 70},
        {'food_id': 648, 'quantity': 120},
        {'food_id': 2460, 'quantity': 50},
        {'food_id': 2401, 'quantity': 30},
        {'food_id': 423, 'quantity': 15},
    ]},
    {'label': 'D1 AGGREGATED (14 foods)', 'foods': [
        {'food_id': 4473, 'quantity': 320},
        {'food_id': 1620, 'quantity': 273},
        {'food_id': 1465, 'quantity': 250},
        {'food_id': 133, 'quantity': 200},
        {'food_id': 851, 'quantity': 200},
        {'food_id': 61, 'quantity': 145},
        {'food_id': 1704, 'quantity': 65},
        {'food_id': 6971, 'quantity': 50},
        {'food_id': 5960, 'quantity': 50},
        {'food_id': 7829, 'quantity': 30},
        {'food_id': 2460, 'quantity': 25},
        {'food_id': 118, 'quantity': 8},
        {'food_id': 2394, 'quantity': 8},
        {'food_id': 2091, 'quantity': 7},
    ]},
    {'label': 'D2 AGGREGATED (11 foods)', 'foods': [
        {'food_id': 6205, 'quantity': 240},
        {'food_id': 700194, 'quantity': 200},
        {'food_id': 2933, 'quantity': 160},
        {'food_id': 133, 'quantity': 150},
        {'food_id': 648, 'quantity': 120},
        {'food_id': 1662, 'quantity': 100},
        {'food_id': 3399, 'quantity': 70},
        {'food_id': 2460, 'quantity': 50},
        {'food_id': 2401, 'quantity': 30},
        {'food_id': 423, 'quantity': 15},
        {'food_id': 118, 'quantity': 8},
    ]},
]


def call(case: Dict[str, Any]) -> float:
    t0 = time.perf_counter()
    r = requests.post(ENDPOINT, json={'foods': case['foods'], 'user_type': 'individual'}, timeout=300)
    wall = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    return wall


def main() -> int:
    try:
        requests.get('http://127.0.0.1:8000/', timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f'Server not reachable: {exc}')
        return 1

    print('warmup...')
    call(CASES[0])

    print(f'\n{"meal":<32} {"foods":>5} {"wall ms":>8}')
    print('-' * 50)
    total = 0.0
    for case in CASES:
        ms = call(case)
        total += ms
        print(f'{case["label"][:32]:<32} {len(case["foods"]):>5} {ms:>8.0f}')
    print('-' * 50)
    print(f'{"TOTAL":<32} {"":>5} {total:>8.0f}')
    print(f'avg per meal: {total / len(CASES):.0f} ms')
    return 0


if __name__ == '__main__':
    sys.exit(main())
