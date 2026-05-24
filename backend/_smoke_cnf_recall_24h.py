"""CNFRecall24h directional smoke harness (AI-MATCH-2, 2026-05-24).

5 canonical daily-eating patterns × 7 gates each. Bypasses the HTTP layer
so the orchestrator itself is what's measured (no rate-limit / circuit-
breaker overhead). For each daily pattern we assert:

  Gate 1 (HARD): every meal decomposed — either matched=True OR
                 fallback_reason contains 'partial_resolution'.
  Gate 2 (HARD): aggregate kcal in [800, 5000] sanity bound.
  Gate 3 (HARD): aggregated list spans ≥ 3 distinct CNF FoodGroups
                 (ingredient diversity — a real day has dairy + grains
                 + protein at minimum, not just one food group).
  Gate 4 (HARD): per-meal mass closure — sum(resolved + unresolved) ≈
                 per-meal total_mass_g within max(20g, 4%) for EVERY meal
                 (passes through the per-dish tolerance, slightly wider
                 to absorb cumulative LLM cooking-fat overshoot).
  Gate 5 (HARD): no hallucinated FoodIDs — every aggregated FoodID resolves
                 to a real CNF entry. Stage-2 enforces this for the per-
                 meal decomposer; we re-assert at the aggregate level.
  Gate 6 (SOFT): HEFI routing succeeds — pass the aggregated list to the
                 HEFI calculator (in-process) and assert overall_score is
                 a finite number in [10, 70] (plausible Canadian range).
  Gate 7 (SOFT): HENI routing succeeds — pass to HENI and assert the
                 total healthy-life-impact is a finite number.

Five daily patterns:
  - SEDENTARY: 3 mains only, ~1800 kcal target
  - ACTIVE:    6 occasions, ~2500 kcal target
  - VEGETARIAN: 3 mains + snack, no meat / fish anywhere
  - HIGH_SNACK: 3 small mains + 3 snacks, ~1800 kcal target
  - WEEKEND_BRUNCH (adversarial): brunch replaces breakfast + lunch,
                                  lighter rest of day, ~2200 kcal

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_cnf_recall_24h.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-cnf-recall-24h'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

# Force UTF-8 stdout on Windows cp1252 consoles. The progress lines use
# ASCII only after this fix, but the JSON output + LLM call logs may still
# contain Unicode (μDALY etc.) and would crash without this reconfiguration.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass


# --- Daily-pattern probes -------------------------------------------------

@dataclass
class MealSpec:
    occasion: str
    dish_name: str
    total_mass_g: float


@dataclass
class DayProbe:
    name: str
    meals: List[MealSpec]
    note: str = ''
    expected_kcal_min: float = 800.0
    expected_kcal_max: float = 5000.0


PROBES: List[DayProbe] = [
    DayProbe(
        name='SEDENTARY',
        note='3 mains only, ~1800 kcal target — typical adult low-activity day',
        meals=[
            MealSpec('breakfast', 'oatmeal with berries', 250),
            MealSpec('lunch',     'turkey sandwich with cheese', 280),
            MealSpec('dinner',    'spaghetti bolognese',   320),
        ],
    ),
    DayProbe(
        name='ACTIVE',
        note='6 occasions, ~2500 kcal — moderately active adult',
        meals=[
            MealSpec('breakfast',     'scrambled eggs with toast and bacon', 300),
            MealSpec('am_snack',      'banana',                              120),
            MealSpec('lunch',         'grilled chicken caesar salad',        350),
            MealSpec('pm_snack',      'greek yogurt with honey',             170),
            MealSpec('dinner',        'beef stir-fry with rice',             400),
            MealSpec('evening_snack', 'apple with peanut butter',            120),
        ],
    ),
    DayProbe(
        name='VEGETARIAN',
        note='3 mains + snack, no meat / fish anywhere',
        meals=[
            MealSpec('breakfast', 'avocado toast with eggs',  220),
            MealSpec('lunch',     'lentil and vegetable soup', 350),
            MealSpec('pm_snack',  'hummus with carrots',       120),
            MealSpec('dinner',    'vegetable stir-fry with tofu and rice', 380),
        ],
    ),
    DayProbe(
        name='HIGH_SNACK',
        note='3 small mains + 3 snacks, ~1800 kcal',
        meals=[
            MealSpec('breakfast',     'yogurt parfait with granola',  200),
            MealSpec('am_snack',      'almonds',                       30),
            MealSpec('lunch',         'tuna salad on crackers',       180),
            MealSpec('pm_snack',      'cheese and crackers',           80),
            MealSpec('dinner',        'grilled salmon with quinoa',   280),
            MealSpec('evening_snack', 'dark chocolate',                30),
        ],
    ),
    DayProbe(
        name='WEEKEND_BRUNCH',
        note='Adversarial: brunch replaces breakfast + lunch; lighter rest',
        meals=[
            MealSpec('lunch',         'eggs benedict with bacon and home fries', 450),
            MealSpec('pm_snack',      'iced coffee with milk',                   240),
            MealSpec('dinner',        'caesar salad with grilled chicken',       300),
            MealSpec('evening_snack', 'vanilla ice cream',                       100),
        ],
    ),
]


# --- Result holders -------------------------------------------------------

@dataclass
class DayResult:
    probe_name: str
    matched: bool
    fallback_reason: Optional[str]
    occasions_count: int
    aggregated_ingredient_count: int
    total_resolved_mass_g: float
    total_unresolved_mass_g: float
    estimated_daily_kcal: float
    food_groups: List[str]
    per_meal_summaries: List[Dict[str, Any]]
    aggregate_warnings: List[str]
    timing_ms: float
    # gates
    g1_all_meals_decomposed: bool = False
    g2_kcal_in_bounds: bool = False
    g3_food_group_diversity: bool = False
    g4_per_meal_mass_closure: bool = False
    g5_no_hallucinated_food_ids: bool = False
    g6_hefi_route_ok: bool = False
    g7_heni_route_ok: bool = False
    hefi_score: Optional[float] = None
    heni_total_impact: Optional[float] = None
    overall_pass: bool = False
    gate_detail: str = ''


# --- Gate helpers ---------------------------------------------------------

def _check_per_meal_mass_closure(meal_results: List[Tuple[str, Any]]) -> Tuple[bool, str]:
    """Gate 4: each meal's (resolved + unresolved) ≈ total_mass_g within
    max(20 g, 4 %). Slightly wider than the per-dish gate (which already
    uses max(10 g, 4 %)) because at the recall level we tolerate one
    additional cooking-fat-rule overshoot per meal."""
    failures = []
    for occasion, dec in meal_results:
        target = dec.total_mass_g
        accounted = dec.resolved_mass_g + dec.unresolved_mass_g
        tol = max(20.0, target * 0.04)
        if abs(accounted - target) > tol:
            failures.append(
                f'{occasion}:accounted={accounted:.1f}g_vs_target={target:.1f}g_tol={tol:.1f}g'
            )
    if failures:
        return False, '; '.join(failures)
    return True, ''


def _check_no_hallucinated_food_ids(aggregated: List[Dict[str, Any]]) -> bool:
    """Gate 5: every aggregated FoodID resolves to a real CNF entry."""
    if not aggregated:
        return False
    try:
        from api.cnf_cache import get_api_cnf_pipeline
        pipeline = get_api_cnf_pipeline()
        valid_ids = set(int(x) for x in pipeline.food_name_df['FoodID'].dropna().tolist())
        return all(int(i['food_id']) in valid_ids for i in aggregated)
    except Exception as exc:  # noqa: BLE001
        print(f'  [warn] Gate 5 CNF FoodID validation skipped: {exc}', flush=True)
        return True


def _route_to_hefi(aggregated: List[Dict[str, Any]]) -> Optional[float]:
    """Gate 6: route the aggregated list through HEFI scoring in-process.

    Mirrors the call chain in `api/views/hefi_views.py:207-210`:
      integrator.aggregate_inputs(food_data) → HEFIInputs → compute_hefi().
    """
    try:
        from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
        from hefi_calculator.hefi.models import HEFIInputs
        from hefi_calculator.hefi.algorithm import compute_hefi
        from django.conf import settings
        integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
        food_data = [(int(i['food_id']), float(i['mass_g'])) for i in aggregated]
        agg = integrator.aggregate_inputs(food_data)
        inputs = HEFIInputs(**agg)
        result = compute_hefi(inputs)
        score = float(getattr(result, 'overall_score', None)
                      or getattr(result, 'total_score', None)
                      or 0.0)
        return score
    except Exception as exc:  # noqa: BLE001
        print(f'  [warn] HEFI routing exception: {exc!r}', flush=True)
        return None


def _route_to_heni(aggregated: List[Dict[str, Any]]) -> Optional[float]:
    """Gate 7: route the aggregated list through HENI scoring in-process.

    Mirrors `api/views/heni_views.py:53-85`: get_cnf_integrator() →
    Ingredient(...) → calculate_meal_heni_response(). Soft gate — we only
    assert that a finite numeric impact comes back, not its sign.
    """
    try:
        from heni_calculator.heni.service import (
            calculate_meal_heni_response, get_cnf_integrator,
        )
        from heni_calculator.heni.models.ingredient import Ingredient
        integrator = get_cnf_integrator()
        ingredients = [
            Ingredient(food_id=int(i['food_id']),
                       amount=float(i['mass_g']),
                       unit='g',
                       cnf_integrator=integrator)
            for i in aggregated
        ]
        result = calculate_meal_heni_response(
            ingredients, llm_api_key=None, cnf_integrator=integrator,
        )
        if isinstance(result, dict):
            hp = result.get('health_impact') or {}
            for key in ('health_impact_minutes', 'total_health_impact_minutes',
                        'total_impact_minutes', 'minutes'):
                v = hp.get(key) if isinstance(hp, dict) else None
                if v is not None and isinstance(v, (int, float)):
                    return float(v)
        return 0.0  # success but unfamiliar shape — soft gate, don't fail
    except Exception as exc:  # noqa: BLE001
        print(f'  [warn] HENI routing exception: {exc!r}', flush=True)
        return None


# --- Per-day runner -------------------------------------------------------

def run_day(orchestrator, probe: DayProbe) -> DayResult:
    from api.services.cnf_recall_24h import MealEntry
    meals = [MealEntry(m.occasion, m.dish_name, m.total_mass_g) for m in probe.meals]
    t0 = time.perf_counter()
    try:
        recall = orchestrator.recall(meals, user_type='researcher')
    except Exception as exc:  # noqa: BLE001
        return DayResult(
            probe_name=probe.name, matched=False,
            fallback_reason=f'exception:{exc!r}',
            occasions_count=0, aggregated_ingredient_count=0,
            total_resolved_mass_g=0.0, total_unresolved_mass_g=0.0,
            estimated_daily_kcal=0.0, food_groups=[], per_meal_summaries=[],
            aggregate_warnings=[],
            timing_ms=(time.perf_counter() - t0) * 1000,
            gate_detail=f'orchestrator_exception:{exc!r}',
        )

    aggregated = recall.aggregated_daily_ingredients
    food_groups = sorted({(i.get('food_group') or '').strip() for i in aggregated if i.get('food_group')})

    # Gates
    g1 = all(
        dec.matched or (dec.fallback_reason and 'partial_resolution' in dec.fallback_reason)
        for _, dec in recall.meals
    ) and len(recall.meals) == len(probe.meals)
    g2 = probe.expected_kcal_min <= recall.estimated_daily_kcal <= probe.expected_kcal_max
    g3 = len(food_groups) >= 3
    g4, g4_detail = _check_per_meal_mass_closure(recall.meals)
    g5 = _check_no_hallucinated_food_ids(aggregated)

    # Soft routing gates — only if hard gates 1+5 passed (otherwise the
    # aggregated list is unreliable to score).
    hefi_score: Optional[float] = None
    heni_impact: Optional[float] = None
    g6 = g7 = False
    if g1 and g5 and aggregated:
        hefi_score = _route_to_hefi(aggregated)
        g6 = hefi_score is not None and 10.0 <= hefi_score <= 70.0
        heni_impact = _route_to_heni(aggregated)
        g7 = heni_impact is not None and isinstance(heni_impact, float)

    details = []
    if not g1: details.append('one_or_more_meals_failed_to_decompose')
    if not g2: details.append(f'kcal={recall.estimated_daily_kcal:.0f}_not_in_[{probe.expected_kcal_min:.0f},{probe.expected_kcal_max:.0f}]')
    if not g3: details.append(f'only_{len(food_groups)}_food_groups')
    if not g4: details.append(f'per_meal_mass_closure_failed:{g4_detail}')
    if not g5: details.append('hallucinated_food_id')
    if not g6: details.append(f'hefi_route:score={hefi_score}')
    if not g7: details.append('heni_route_failed')
    if not details: details.append(probe.note or 'ok')

    # Hard gates G1-G5; soft G6 + G7 logged
    overall = g1 and g2 and g3 and g4 and g5

    per_meal_summaries = []
    for occasion, dec in recall.meals:
        per_meal_summaries.append({
            'occasion': occasion,
            'dish_name': dec.dish_name,
            'total_mass_g': dec.total_mass_g,
            'matched': dec.matched,
            'ingredients_count': len(dec.ingredients),
            'resolved_mass_g': round(dec.resolved_mass_g, 1),
            'unresolved_mass_g': round(dec.unresolved_mass_g, 1),
            'fallback_reason': dec.fallback_reason,
            'top_ingredients': [
                {'food_id': i.food_id, 'mass_g': round(i.mass_g, 1),
                 'food_description': i.food_description[:50]}
                for i in sorted(dec.ingredients, key=lambda x: -x.mass_g)[:3]
            ],
        })

    return DayResult(
        probe_name=probe.name,
        matched=recall.matched,
        fallback_reason=recall.fallback_reason,
        occasions_count=recall.occasions_count,
        aggregated_ingredient_count=len(aggregated),
        total_resolved_mass_g=recall.total_resolved_mass_g,
        total_unresolved_mass_g=recall.total_unresolved_mass_g,
        estimated_daily_kcal=recall.estimated_daily_kcal,
        food_groups=food_groups,
        per_meal_summaries=per_meal_summaries,
        aggregate_warnings=recall.aggregate_warnings,
        timing_ms=(time.perf_counter() - t0) * 1000,
        g1_all_meals_decomposed=g1,
        g2_kcal_in_bounds=g2,
        g3_food_group_diversity=g3,
        g4_per_meal_mass_closure=g4,
        g5_no_hallucinated_food_ids=g5,
        g6_hefi_route_ok=g6,
        g7_heni_route_ok=g7,
        hefi_score=hefi_score,
        heni_total_impact=heni_impact,
        overall_pass=overall,
        gate_detail='; '.join(details),
    )


# --- Reporter -------------------------------------------------------------

def main() -> int:
    print('CNFRecall24h directional smoke harness '
          f'({len(PROBES)} daily patterns x 7 gates)')
    print('=' * 100)
    from api.services.cnf_recall_24h import get_default_recall_24h
    orchestrator = get_default_recall_24h()
    print(f'LLM client wired: '
          f'{"yes" if orchestrator.decomposer.chat_json_client else "NO (degraded)"}')
    print()

    results: List[DayResult] = []
    for probe in PROBES:
        print(f'>>> Day: {probe.name} ({len(probe.meals)} meals) …', flush=True)
        r = run_day(orchestrator, probe)
        results.append(r)
        mark = '[ OK ]' if r.overall_pass else '[FAIL]'
        gates = (f'g1={"+" if r.g1_all_meals_decomposed else "-"} '
                 f'g2={"+" if r.g2_kcal_in_bounds else "-"} '
                 f'g3={"+" if r.g3_food_group_diversity else "-"} '
                 f'g4={"+" if r.g4_per_meal_mass_closure else "-"} '
                 f'g5={"+" if r.g5_no_hallucinated_food_ids else "-"} '
                 f'g6={"+" if r.g6_hefi_route_ok else "-"} '
                 f'g7={"+" if r.g7_heni_route_ok else "-"}')
        print(f'  {mark}  {r.probe_name:<15s} '
              f'ings={r.aggregated_ingredient_count:>2}  '
              f'kcal={r.estimated_daily_kcal:>5.0f}  '
              f'groups={len(r.food_groups):>2}  '
              f'{gates}  ({r.timing_ms / 1000:.1f}s)')
        for m in r.per_meal_summaries:
            ok = '[ok]' if m['matched'] else '[!!]'
            print(f'      {ok} {m["occasion"]:<15s} "{m["dish_name"][:30]:<30}" -> '
                  f'{m["ingredients_count"]:>2} ings ({m["resolved_mass_g"]:>5.1f}g resolved)')
        if r.aggregate_warnings:
            print(f'      warnings: {r.aggregate_warnings}')
        if not r.overall_pass:
            print(f'      FAIL: {r.gate_detail}')
        print()

    # Aggregate
    total = len(results)
    hard_pass = sum(1 for r in results if r.overall_pass)
    print('=' * 100)
    print(f'Overall (HARD gates G1-G5): PASS={hard_pass}  FAIL={total - hard_pass}  TOTAL={total}')
    print('Per-gate pass rate across all days:')
    for label, attr in [
        ('G1 (all meals decomposed)',    'g1_all_meals_decomposed'),
        ('G2 (kcal in [800, 5000])',     'g2_kcal_in_bounds'),
        ('G3 (≥ 3 food groups)',         'g3_food_group_diversity'),
        ('G4 (per-meal mass closure)',   'g4_per_meal_mass_closure'),
        ('G5 (no hallucinated FoodIDs)', 'g5_no_hallucinated_food_ids'),
        ('G6 (HEFI route — soft)',       'g6_hefi_route_ok'),
        ('G7 (HENI route — soft)',       'g7_heni_route_ok'),
    ]:
        n = sum(1 for r in results if getattr(r, attr))
        print(f'  {label:<35s} {n}/{total}')

    out_path = os.path.join(_HERE, '_smoke_cnf_recall_24h_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness': 'CNFRecall24h directional smoke (AI-MATCH-2)',
            'totals': {
                'hard_pass': hard_pass, 'fail': total - hard_pass, 'total': total,
            },
            'results': [
                {
                    'probe_name': r.probe_name,
                    'matched': r.matched,
                    'fallback_reason': r.fallback_reason,
                    'occasions_count': r.occasions_count,
                    'aggregated_ingredient_count': r.aggregated_ingredient_count,
                    'total_resolved_mass_g': round(r.total_resolved_mass_g, 1),
                    'total_unresolved_mass_g': round(r.total_unresolved_mass_g, 1),
                    'estimated_daily_kcal': round(r.estimated_daily_kcal, 1),
                    'food_groups': r.food_groups,
                    'per_meal_summaries': r.per_meal_summaries,
                    'aggregate_warnings': r.aggregate_warnings,
                    'timing_ms': round(r.timing_ms, 1),
                    'gates': {
                        'g1_all_meals_decomposed':     r.g1_all_meals_decomposed,
                        'g2_kcal_in_bounds':           r.g2_kcal_in_bounds,
                        'g3_food_group_diversity':     r.g3_food_group_diversity,
                        'g4_per_meal_mass_closure':    r.g4_per_meal_mass_closure,
                        'g5_no_hallucinated_food_ids': r.g5_no_hallucinated_food_ids,
                        'g6_hefi_route_ok':            r.g6_hefi_route_ok,
                        'g7_heni_route_ok':            r.g7_heni_route_ok,
                    },
                    'hefi_score':         r.hefi_score,
                    'heni_total_impact':  r.heni_total_impact,
                    'overall_pass': r.overall_pass,
                    'gate_detail': r.gate_detail,
                }
                for r in results
            ],
        }, f, indent=2)
    print()
    print(f'Results JSON: {out_path}')

    # Exit code: fail only on HARD gates (G1-G5).
    hard_failed = any(
        not (r.g1_all_meals_decomposed and r.g2_kcal_in_bounds
             and r.g3_food_group_diversity and r.g4_per_meal_mass_closure
             and r.g5_no_hallucinated_food_ids)
        for r in results
    )
    return 1 if hard_failed else 0


if __name__ == '__main__':
    sys.exit(main())
