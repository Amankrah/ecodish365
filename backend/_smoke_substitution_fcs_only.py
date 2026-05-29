#!/usr/bin/env python
"""End-to-end timing for FCS-only substitution analyzer.

Runs analyze_substitutions on each meal from the user-supplied saved-days
export and reports wall-clock + suggestion counts. Compares to the
production baseline (~145 s/request before, ~90 s before HENI was cut).
"""
from __future__ import annotations

import io
import os
import sys
import time

# Force UTF-8 stdout — Windows cp1252 default chokes on the arrow glyph.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

import django

import dish_project.env_bootstrap  # noqa: F401  — load .env

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from api.services.substitution_analyzer import analyze_substitutions  # noqa: E402


MEALS = [
    {
        'label': 'day1 breakfast — scrambled egg with orange juice',
        'dish_name': 'scrambled egg with orange juice',
        'composition': [
            {'food_id': 133, 'mass_g': 200, 'food_description': 'Egg, chicken, whole, cooked, scrambled or omelet'},
            {'food_id': 118, 'mass_g': 8, 'food_description': 'Butter, regular'},
            {'food_id': 61, 'mass_g': 15, 'food_description': 'Milk, fluid, partly skimmed, 2% M.F.'},
            {'food_id': 1620, 'mass_g': 273, 'food_description': 'Orange juice, chilled, includes from concentrate'},
        ],
    },
    {
        'label': 'day1 lunch — chicken biryani (8 ingredients, worst case)',
        'dish_name': 'chicken briyani',
        'composition': [
            {'food_id': 4473, 'mass_g': 320, 'food_description': 'Grains, rice, white, long-grain, parboiled, cooked'},
            {'food_id': 851, 'mass_g': 200, 'food_description': 'Chicken, broiler, thigh, meat and skin, roasted'},
            {'food_id': 6971, 'mass_g': 50, 'food_description': 'Yogourt (yogurt), Balkan style, 4-6% M.F., plain'},
            {'food_id': 5960, 'mass_g': 50, 'food_description': 'Onion, yellow, sauteed'},
            {'food_id': 7829, 'mass_g': 30, 'food_description': 'Butter, Clarified butter (ghee)'},
            {'food_id': 2460, 'mass_g': 25, 'food_description': 'Tomato, red, ripe, raw, year round average'},
            {'food_id': 2394, 'mass_g': 8, 'food_description': 'Garlic, raw'},
            {'food_id': 2091, 'mass_g': 7, 'food_description': 'Ginger root, raw'},
        ],
    },
    {
        'label': 'day1 dinner — oat porridge with milk and banana',
        'dish_name': 'oat porridge with milk and banna',
        'composition': [
            {'food_id': 1465, 'mass_g': 250, 'food_description': 'Cereal, hot, oats (oatmeal), large flakes, prepared, Quaker'},
            {'food_id': 61, 'mass_g': 130, 'food_description': 'Milk, fluid, partly skimmed, 2% M.F.'},
            {'food_id': 1704, 'mass_g': 65, 'food_description': 'Banana, raw'},
        ],
    },
    {
        'label': 'day2 dinner — fufu with groundnut soup (WAFCT)',
        'dish_name': 'fufu with groundnut soup',
        'composition': [
            {'food_id': 700194, 'mass_g': 200, 'food_description': 'Cassava, tuber, white flesh, boiled* (without salt), drained'},
            {'food_id': 1662, 'mass_g': 100, 'food_description': 'Plantain, yellow cooked'},
            {'food_id': 2933, 'mass_g': 160, 'food_description': 'Water, municipal'},
            {'food_id': 3399, 'mass_g': 70, 'food_description': 'Peanut butter, smooth type, fat, sugar and salt added'},
            {'food_id': 648, 'mass_g': 120, 'food_description': 'Chicken, stewing, meat and skin, stewed'},
            {'food_id': 2460, 'mass_g': 50, 'food_description': 'Tomato, red, ripe, raw, year round average'},
            {'food_id': 2401, 'mass_g': 30, 'food_description': 'Onion, raw'},
            {'food_id': 423, 'mass_g': 15, 'food_description': 'Vegetable oil, palm'},
        ],
    },
]


def main() -> int:
    print(f'{"meal":<60} {"mode":>8} {"ings":>4} {"cands":>5} {"suggs":>5} {"wall ms":>10}  top swap')
    print('-' * 140)
    total_ms = 0.0
    # Run each meal in BOTH modes — singles (default) and greedy (multi-step
    # plan, the slow path matching the production "Multi-step plan" UI).
    for mode in ('singles', 'greedy'):
        for meal in MEALS:
            t0 = time.perf_counter()
            result = analyze_substitutions(
                meal['composition'],
                purpose='general_health',
                max_suggestions=3,
                include_scorecard=True,
                dish_name=meal['dish_name'],
                reformulation_mode=mode,
                constraints={'max_swaps': 3 if mode == 'greedy' else 1},
            )
            wall_ms = (time.perf_counter() - t0) * 1000
            total_ms += wall_ms
            n_ings = len(meal['composition'])
            n_cands = result['metadata']['candidates_found']
            n_sug = len(result['suggestions'])
            top = result['suggestions'][0] if result['suggestions'] else None
            top_desc = ''
            if top:
                o = top['original']['food_description'][:24]
                r = top['replacement']['food_description'][:24]
                fcs_d = top.get('fcs', {}).get('delta', 0)
                top_desc = f'[{o} → {r}] ΔFCS={fcs_d:+.2f}'
            print(f'{meal["label"][:60]:<60} {mode:>8} {n_ings:>4} {n_cands:>5} {n_sug:>5} {wall_ms:>10.1f}  {top_desc}')

    print('-' * 130)
    print(f'{"TOTAL":<60} {"":>4} {"":>5} {"":>5} {total_ms:>10.1f}')
    print()
    print(f'Average per meal: {total_ms / len(MEALS):.1f} ms')
    print()
    print('Reference (production gunicorn log, before changes):')
    print('  Chicken biryani analyze ≈ 145 s wall-clock → nginx 504 at 60 s.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
