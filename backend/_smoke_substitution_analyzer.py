#!/usr/bin/env python
"""Smoke test for SUBST-1 substitution analyzer — Phase 1 golden cases."""
from __future__ import annotations

import json
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from api.services.substitution_analyzer import analyze_substitutions

CASES = [
    {
        'name': 'beef_only',
        'composition': [{'food_id': 2683, 'mass_g': 100.0}],
        'expect_rule': 'beef_to_legumes',
    },
    {
        'name': 'white_bread',
        'composition': [{'food_id': 3732, 'mass_g': 80.0, 'food_description': 'Bread, white, commercial, toasted'}],
        'expect_rule': 'white_to_whole_wheat',
    },
]


def main() -> int:
    results = []
    failed = 0
    for case in CASES:
        out = analyze_substitutions(case['composition'], purpose='general_health', max_suggestions=3)
        top_rule = out['suggestions'][0]['rule_id'] if out['suggestions'] else None
        ok = top_rule == case['expect_rule']
        if not ok:
            failed += 1
        results.append({
            'case': case['name'],
            'ok': ok,
            'top_rule': top_rule,
            'hefi_delta': out['suggestions'][0]['hefi']['delta'] if out['suggestions'] else None,
        })
        print(f"{'PASS' if ok else 'FAIL'} {case['name']} -> {top_rule}")

    out_path = os.path.join(os.path.dirname(__file__), '_smoke_substitution_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f'Wrote {out_path}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
