"""WAFCT integration smoke harness (WAFCT-EXTEND, 2026-05-24).

6 directional gates verifying the Option B integration end-to-end:

  G1 Ingest succeeds                 — pipeline gains 1,028 WAFCT foods
  G2 Source column populated          — value counts cnf=5691 + wafct=1028
  G3 Nutrient lookup works            — `nutrients_for(food_id)` returns
                                        CNF-keyed names for WAFCT FoodIDs
  G4 Matcher returns WAFCT foods      — query "fonio porridge" hits source='wafct'
  G5 Source filter respected          — query "milk" with source='cnf' returns
                                        only CNF; with source='wafct' only WAFCT
  G6 End-to-end HEFI + HENI scoring   — WAFCT-only meal returns finite scores
                                        AND surfaces the WAFCT caveat block

Bypasses the HTTP layer so the integration is what's measured (no rate-
limit / circuit-breaker overhead). Exits 0 if all 6 hard gates pass.

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_wafct_integration.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-wafct-integration'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass


# Sample WAFCT FoodIDs (700,000+) with expected per-100g kcal values
# pinned from the WAFCT-EXPLORE per-100g study + spot-check.
# FoodID -> (name fragment, expected kcal, tolerance kcal)
WAFCT_NUTRIENT_PROBES: List[tuple] = [
    # Boalboal (Burkina Faso): millet balls — first WAFCT food, FoodID 700004
    (700004, 'Boalboal',                  252,   2.0),
    # Bambara groundnut, raw — verified from earlier per-100g study run
    (700004 + 0, 'wafct food', None, None),     # placeholder; resolved below
]


@dataclass
class GateResult:
    gate:    str
    passed:  bool
    detail:  str
    metrics: Dict[str, Any] = field(default_factory=dict)


def _print(gate: GateResult) -> None:
    mark = '[ OK ]' if gate.passed else '[FAIL]'
    print(f'  {mark}  {gate.gate}  — {gate.detail}')
    for k, v in gate.metrics.items():
        print(f'         {k}: {v}')


# --- Gate 1 ----------------------------------------------------------------

def gate_1_ingest(pipeline) -> GateResult:
    n_total = len(pipeline.food_name_df)
    n_wafct = len(pipeline.filter_by_source('wafct'))
    n_cnf   = len(pipeline.filter_by_source('cnf'))
    ok = n_wafct >= 1000 and n_cnf >= 5000 and n_total == n_wafct + n_cnf
    return GateResult(
        gate='G1 Ingest succeeds',
        passed=ok,
        detail=f'pipeline has {n_total} foods ({n_cnf} CNF + {n_wafct} WAFCT)',
        metrics={'n_total': n_total, 'n_cnf': n_cnf, 'n_wafct': n_wafct},
    )


# --- Gate 2 ----------------------------------------------------------------

def gate_2_source_column(pipeline) -> GateResult:
    if 'source' not in pipeline.food_name_df.columns:
        return GateResult(
            gate='G2 Source column populated',
            passed=False,
            detail='food_name_df has no `source` column',
        )
    counts = pipeline.food_name_df['source'].value_counts().to_dict()
    ok = counts.get('cnf', 0) > 5000 and counts.get('wafct', 0) > 1000
    return GateResult(
        gate='G2 Source column populated',
        passed=ok,
        detail=f'value_counts={counts}',
        metrics={'value_counts': counts},
    )


# --- Gate 3 ----------------------------------------------------------------

def gate_3_nutrient_lookup(pipeline) -> GateResult:
    # Pick 5 WAFCT FoodIDs at the start of the offset range. Each should
    # have at least ENERGY (KILOCALORIES) populated. Don't pin exact values
    # (the Excel row order isn't bit-stable across openpyxl versions);
    # require non-zero, > 0, and < 1000 (per 100g sanity).
    sample_ids = [700000, 700004, 700100, 700500, 701000]
    rows = []
    fails = []
    for fid in sample_ids:
        n = pipeline.nutrients_for(fid)
        kcal = n.get('ENERGY (KILOCALORIES)')
        ok_row = (kcal is not None and isinstance(kcal, (int, float))
                  and 0 < float(kcal) < 1000)
        rows.append({'food_id': fid, 'kcal_per_100g': kcal, 'ok': ok_row,
                     'n_nutrients': len(n)})
        if not ok_row:
            fails.append(fid)
    overall = len(fails) == 0
    return GateResult(
        gate='G3 Nutrient lookup works for WAFCT foods',
        passed=overall,
        detail=(f'all {len(sample_ids)} WAFCT FoodIDs return CNF-keyed '
                f'nutrients with sensible per-100g kcal'
                if overall else f'{len(fails)} fails: {fails}'),
        metrics={'samples': rows},
    )


# --- Gate 4 ----------------------------------------------------------------

def gate_4_matcher_returns_wafct(matcher) -> GateResult:
    # Soft assertion per plan: top match for an obviously-WAFCT query
    # should have source='wafct'. The matcher's `sources` array on the
    # corpus is the authoritative resolver.
    queries = ['fonio porridge', 'baobab leaves', 'dawadawa fermented locust bean']
    results = []
    all_ok = True
    for q in queries:
        r = matcher.match(q)
        if not r.matched or r.food_id is None:
            results.append({'query': q, 'matched': False, 'food_id': r.food_id})
            all_ok = False
            continue
        # Source: derive via the corpus food_ids → sources mapping
        idx = next((i for i, fid in enumerate(matcher.corpus.food_ids)
                    if int(fid) == int(r.food_id)), None)
        src = matcher.corpus.sources[idx] if idx is not None else 'unknown'
        results.append({'query': q, 'food_id': r.food_id,
                        'food_description': r.food_description[:50],
                        'source': src, 'confidence': round(r.confidence, 2)})
        if src != 'wafct':
            all_ok = False
    return GateResult(
        gate='G4 Matcher returns WAFCT foods for WAFCT-only queries',
        passed=all_ok,
        detail=('all 3 WAFCT-only queries resolved to a WAFCT FoodID'
                if all_ok else 'one or more queries did not hit a WAFCT source'),
        metrics={'queries': results},
    )


# --- Gate 5 ----------------------------------------------------------------

def gate_5_source_filter(matcher) -> GateResult:
    rows: List[Dict[str, Any]] = []
    all_ok = True
    # "milk" exists in both → with source filter should narrow accordingly
    for src in ('cnf', 'wafct'):
        r = matcher.match('whole milk', source=src)
        if not r.matched or r.food_id is None:
            rows.append({'src_filter': src, 'matched': False})
            all_ok = False
            continue
        idx = next((i for i, fid in enumerate(matcher.corpus.food_ids)
                    if int(fid) == int(r.food_id)), None)
        actual_src = matcher.corpus.sources[idx] if idx is not None else 'unknown'
        rows.append({'src_filter': src, 'food_id': r.food_id,
                     'food_description': r.food_description[:60],
                     'actual_source': actual_src})
        if actual_src != src:
            all_ok = False
    return GateResult(
        gate='G5 Source filter respected',
        passed=all_ok,
        detail=('both source filters returned the correct source'
                if all_ok else 'one or more filtered queries crossed source boundary'),
        metrics={'queries': rows},
    )


# --- Gate 6 ----------------------------------------------------------------

def gate_6_end_to_end_scoring(pipeline) -> GateResult:
    """WAFCT-only meal → HEFI + HENI score + WAFCT caveat surfaces."""
    rows: Dict[str, Any] = {}
    all_ok = True
    # Pick 3 known WAFCT food_ids
    wafct_meal = [(700000, 100.0), (700004, 100.0), (700100, 100.0)]
    food_ids_only = [fid for fid, _ in wafct_meal]

    # HEFI
    try:
        from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
        from hefi_calculator.hefi.models import HEFIInputs
        from hefi_calculator.hefi.algorithm import compute_hefi
        from django.conf import settings
        integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
        agg = integrator.aggregate_inputs(wafct_meal)
        inputs = HEFIInputs(**agg)
        result = compute_hefi(inputs)
        hefi_score = float(getattr(result, 'total_score', 0.0) or 0.0)
        rows['hefi_score'] = round(hefi_score, 2)
        if not (0 < hefi_score < 80):
            all_ok = False
    except Exception as exc:  # noqa: BLE001
        rows['hefi_error'] = repr(exc)[:100]
        all_ok = False

    # HENI
    try:
        from heni_calculator.heni.service import (
            calculate_meal_heni_response, get_cnf_integrator,
        )
        from heni_calculator.heni.models.ingredient import Ingredient
        integrator = get_cnf_integrator()
        ingredients = [
            Ingredient(food_id=fid, amount=mass, unit='g',
                       cnf_integrator=integrator)
            for fid, mass in wafct_meal
        ]
        heni_result = calculate_meal_heni_response(
            ingredients, llm_api_key=None, cnf_integrator=integrator,
        )
        hp = heni_result.get('health_impact') or {}
        heni_min = hp.get('health_impact_minutes')
        rows['heni_impact_minutes'] = round(heni_min, 2) if isinstance(heni_min, (int, float)) else heni_min
        if heni_min is None or not isinstance(heni_min, (int, float)):
            all_ok = False
    except Exception as exc:  # noqa: BLE001
        rows['heni_error'] = repr(exc)[:100]
        all_ok = False

    # WAFCT caveat surface
    try:
        from api.views.wafct_caveat import build_wafct_caveat
        caveat = build_wafct_caveat(food_ids_only, indicator='hefi', user_type='researcher')
        if 'wafct_caveat' in caveat:
            rows['caveat_surfaced'] = True
            rows['caveat_food_count'] = caveat['wafct_caveat'].get('wafct_food_count_in_meal')
        else:
            rows['caveat_surfaced'] = False
            all_ok = False
    except Exception as exc:  # noqa: BLE001
        rows['caveat_error'] = repr(exc)[:100]
        all_ok = False

    return GateResult(
        gate='G6 End-to-end scoring + caveat for WAFCT-only meal',
        passed=all_ok,
        detail='HEFI + HENI score finite AND wafct_caveat surfaced' if all_ok else 'one of {HEFI, HENI, caveat} failed',
        metrics=rows,
    )


# --- Main ------------------------------------------------------------------

def main() -> int:
    print('WAFCT integration smoke harness (WAFCT-EXTEND, 6 gates)')
    print('=' * 80)

    print('\nLoading pipeline + matcher …')
    t0 = time.perf_counter()
    from api.cnf_cache import get_api_cnf_pipeline
    pipeline = get_api_cnf_pipeline()
    print(f'  Pipeline loaded ({len(pipeline.food_name_df)} foods)')
    from api.services.cnf_matcher import get_default_matcher
    matcher = get_default_matcher()
    print(f'  Matcher loaded ({len(matcher.corpus.food_ids)} corpus rows; '
          f'{sum(1 for s in matcher.corpus.sources if s == "wafct")} WAFCT)')
    print(f'  Cold-start: {time.perf_counter() - t0:.1f} s\n')

    gates: List[GateResult] = []
    print('Running gates …\n')
    gates.append(gate_1_ingest(pipeline));               _print(gates[-1])
    gates.append(gate_2_source_column(pipeline));        _print(gates[-1])
    gates.append(gate_3_nutrient_lookup(pipeline));      _print(gates[-1])
    gates.append(gate_4_matcher_returns_wafct(matcher)); _print(gates[-1])
    gates.append(gate_5_source_filter(matcher));         _print(gates[-1])
    gates.append(gate_6_end_to_end_scoring(pipeline));   _print(gates[-1])

    n_pass = sum(1 for g in gates if g.passed)
    print()
    print('=' * 80)
    print(f'WAFCT integration: PASS={n_pass}/{len(gates)}')

    out_path = os.path.join(_HERE, '_smoke_wafct_integration_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness':    'WAFCT-EXTEND integration smoke (2026-05-24)',
            'pass':       n_pass,
            'total':      len(gates),
            'gates':      [{'gate': g.gate, 'passed': g.passed,
                            'detail': g.detail, 'metrics': g.metrics}
                           for g in gates],
        }, f, indent=2, ensure_ascii=False)
    print(f'Results JSON: {out_path}')

    return 0 if n_pass == len(gates) else 1


if __name__ == '__main__':
    sys.exit(main())
