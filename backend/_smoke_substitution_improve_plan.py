#!/usr/bin/env python
"""Smoke test for POST /api/substitution/improve-plan/ orchestration.

Run from backend/:
    python _smoke_substitution_improve_plan.py

Uses fixtures/recall_improve_plan_sample.json (two recall days from user export).
"""
from __future__ import annotations

import json
import os
import sys
import time

import dish_project.env_bootstrap  # noqa: F401 — load backend/.env before Django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402

django.setup()

from api.services.substitution_improve_plan import (  # noqa: E402
    build_improve_plan,
    combine_recall_days,
)

_FIXTURE = os.path.join(
    os.path.dirname(__file__), 'fixtures', 'recall_improve_plan_sample.json',
)


def _load_fixture() -> dict:
    with open(_FIXTURE, encoding='utf-8') as f:
        return json.load(f)


def _metric_val(sc: dict, key: str):
    block = (sc or {}).get(key) or {}
    return block.get('value')


def _print_plan(label: str, result: dict) -> None:
    print(f'\n=== {label} ===')
    print(result.get('summary', ''))
    baseline = result.get('baseline') or {}
    sc = baseline.get('scorecard') or {}
    print(
        f"  ingredients={baseline.get('ingredient_count')} "
        f"mass={baseline.get('total_mass_g')}g "
        f"HEFI={_metric_val(sc, 'hefi')} "
        f"HENI={_metric_val(sc, 'heni')}min "
        f"FCS={_metric_val(sc, 'fcs')} "
        f"env={_metric_val(sc, 'environmental')}",
    )
    pop = baseline.get('population_context')
    if pop and pop.get('hefi'):
        print(f"  population: {pop['hefi'].get('band_phrase')}")

    print('  priority targets:')
    for t in (result.get('priority_targets') or [])[:5]:
        rule = t.get('swap_rule_id') or '—'
        print(
            f"    - {t['food_description'][:50]} "
            f"({t['mass_g']}g, {t['mass_pct']}%, rule={rule}, "
            f"flags={t.get('flags')})",
        )

    n_sug = len(result.get('suggestions') or [])
    n_par = len(result.get('pareto_frontier') or [])
    print(f'  suggestions: {n_sug} pareto={n_par}')
    for s in (result.get('suggestions') or [])[:5]:
        deltas = (s.get('scorecard_full') or {}).get('deltas') or {}
        hefi_d = (deltas.get('hefi') or {}).get('delta')
        fcs_d = (deltas.get('fcs') or {}).get('delta')
        on_p = (s.get('pareto') or {}).get('on_frontier')
        print(
            f"    * {s.get('label', s.get('id'))[:60]} "
            f"dHEFI={hefi_d} dFCS={fcs_d} pareto={on_p}",
        )
    print(f"  elapsed_ms={result.get('metadata', {}).get('elapsed_ms')}")


def main() -> int:
    fixture = _load_fixture()
    days = fixture['days']
    day1_id = days[0]['id']

    gates = []

    # G1 — combine_recall_days matches frontend combineDays
    combined = combine_recall_days(days)
    gates.append(('G1 combine days', len(combined) >= 20))

    # G2 — single day improve plan
    t0 = time.perf_counter()
    r_day1 = build_improve_plan(
        recall_export=fixture,
        day_ids=[day1_id],
        max_suggestions=5,
    )
    gates.append(('G2 day1 success', r_day1.get('success') is True))
    gates.append(('G2 day1 has scorecard', 'hefi' in (r_day1.get('baseline') or {}).get('scorecard', {})))
    gates.append(('G2 day1 has suggestions', len(r_day1.get('suggestions') or []) >= 1))
    _print_plan('Day 1 only', r_day1)

    # G3 — two-day combined usual-eating proxy
    r_both = build_improve_plan(
        recall_export=fixture,
        max_suggestions=5,
    )
    gates.append(('G3 both days success', r_both.get('success') is True))
    gates.append(('G3 more ingredients than day1', (
        (r_both.get('baseline') or {}).get('ingredient_count', 0)
        >= (r_day1.get('baseline') or {}).get('ingredient_count', 0)
    )))
    _print_plan('Both days combined', r_both)

    # G4 — top-5 ingredients only (quick subset)
    top5 = days[0]['aggregated_daily_ingredients'][:5]
    r_top5 = build_improve_plan(composition=top5, max_suggestions=5)
    gates.append(('G4 top5 success', r_top5.get('success') is True))
    gates.append(('G4 top5 count', (r_top5.get('baseline') or {}).get('ingredient_count') == 5))
    _print_plan('Top 5 ingredients (day1)', r_top5)

    # G5 — sugary drink flagged in priority targets (OJ on day1)
    flags_flat = [
        f for t in (r_day1.get('priority_targets') or []) for f in (t.get('flags') or [])
    ]
    gates.append(('G5 sugary_drink flagged', 'sugary_drink' in flags_flat))

    print('\n--- Gates ---')
    passed = 0
    for name, ok in gates:
        status = 'PASS' if ok else 'FAIL'
        print(f'  [{status}] {name}')
        if ok:
            passed += 1
    print(f'\n{passed}/{len(gates)} PASS ({time.perf_counter() - t0:.1f}s wall)')
    return 0 if passed == len(gates) else 1


if __name__ == '__main__':
    sys.exit(main())
