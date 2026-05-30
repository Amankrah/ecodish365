#!/usr/bin/env python
"""Perf benchmark for /api/hefi/calculate/ — same panel as the HEFI
snapshot. Warmup once, then measure steady-state."""
from __future__ import annotations

import io
import sys
import time
from typing import Any, Dict, List

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

ENDPOINT = 'http://127.0.0.1:8000/api/hefi/calculate/'


CASES: List[Dict[str, Any]] = [
    {'label': 'D1 breakfast (4 foods)', 'foods': [
        {'food_id': 133, 'amount_g': 200},
        {'food_id': 118, 'amount_g': 8},
        {'food_id': 61, 'amount_g': 15},
        {'food_id': 1620, 'amount_g': 273},
    ]},
    {'label': 'D1 biryani (8 foods)', 'foods': [
        {'food_id': 4473, 'amount_g': 320},
        {'food_id': 851, 'amount_g': 200},
        {'food_id': 6971, 'amount_g': 50},
        {'food_id': 5960, 'amount_g': 50},
        {'food_id': 7829, 'amount_g': 30},
        {'food_id': 2460, 'amount_g': 25},
        {'food_id': 2394, 'amount_g': 8},
        {'food_id': 2091, 'amount_g': 7},
    ]},
    {'label': 'D1 porridge (3 foods)', 'foods': [
        {'food_id': 1465, 'amount_g': 250},
        {'food_id': 61, 'amount_g': 130},
        {'food_id': 1704, 'amount_g': 65},
    ]},
    {'label': 'D2 fufu (8 foods)', 'foods': [
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


def call(case: Dict[str, Any]) -> float:
    t0 = time.perf_counter()
    r = requests.post(ENDPOINT, json={'foods': case['foods'], 'user_type': 'individual'}, timeout=180)
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
