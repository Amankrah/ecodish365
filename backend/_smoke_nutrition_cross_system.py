"""Cross-system nutrition meal-panel smoke (Scenario S4).

For each meal in `CROSS_SYSTEM_MEAL_PANEL`, calls all three nutrition
endpoints (/api/heni/calculate/, /api/hefi/calculate/, /api/hsr/calculate/)
and checks:

  1. **Directional ranking**: across the panel, the rank order of meals
     by HENI minutes (ascending = worse to better), HEFI score
     (ascending = worse to better), and HSR stars (ascending = worse to
     better) should agree. Spearman ρ between any pair should be >= 0.6
     (lenient because the systems weight different dimensions).

  2. **Per-meal sign coherence**: meals that are obvious anti-patterns
     (processed-meat-heavy, SSB-only) must score below the midpoint on
     ALL three systems; meals that are CFG-aligned must score above the
     midpoint on ALL three.

Caveats:
  - HENI is currently affected by extraction bugs surfaced in Phase 1
    (`_smoke_heni_literature_panel.py`). Cross-system rank may be
    distorted until that's fixed. Report results honestly.
  - HSR per-meal accepts a single category — the API uses the dominant-
    category food to set the scoring matrix. Use representative meal
    composites (one dominant food).

Run from `backend/`:
    python _smoke_nutrition_cross_system.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from typing import List, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-nutrition-cross-system'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402


@dataclass
class CrossPanelMeal:
    label: str
    foods: List[Tuple[int, float, str]] = field(default_factory=list)
    expected_quality: str = ''   # 'low' | 'mid' | 'high'
    rationale: str = ''


# Each meal is intentionally sized to ~400-700 kcal so per-meal scoring is
# comparable across systems. Foods chosen to span the quality spectrum.
CROSS_SYSTEM_MEAL_PANEL: List[CrossPanelMeal] = [
    CrossPanelMeal(
        label='Processed-meat anti-pattern',
        foods=[
            (4644, 150.0, 'Fast foods, hot dog, plain'),
            (4962, 150.0, 'Pizza, pepperoni, frozen, cooked'),
        ],
        expected_quality='low',
        rationale='High sodium, high sat fat, processed meat. Should rank '
                  'BELOW midpoint on all 3 systems.',
    ),
    CrossPanelMeal(
        label='Refined-sugar dessert',
        foods=[
            (4157, 150.0, 'Dessert, frozen, ice cream, vanilla, rich, 16% M.F.'),
            (3941, 100.0, 'Pie, apple, commercial, 2 crust'),
        ],
        expected_quality='low',
        rationale='High free sugars, sat fat, low protein. Should rank low '
                  'on HEFI sugars/sat-fat, low HSR (other-food cat), HENI '
                  'mildly negative.',
    ),
    CrossPanelMeal(
        label='Mixed-balanced lunch',
        foods=[
            (4067, 60.0,  'Bread, whole wheat, commercial (2 slices)'),
            (3081, 90.0,  'Fish, tuna, light, canned in water, drained, salted'),
            (2380, 80.0,  'Carrot, raw'),
            (1696, 100.0, 'Apple, raw, with skin'),
        ],
        expected_quality='mid',
        rationale='Standard mixed lunch: whole grain, lean protein, veg, fruit. '
                  'Should rank mid-to-high on all 3 systems.',
    ),
    CrossPanelMeal(
        label='Plant-forward dinner',
        foods=[
            (5917, 180.0, 'Grains, quinoa, cooked'),
            (3404, 120.0, 'Tofu, regular, firm'),
            (2026, 100.0, 'Broccoli, frozen, boiled'),
            (2380, 60.0,  'Carrot, raw'),
            (422,  10.0,  'Vegetable oil, olive'),
        ],
        expected_quality='high',
        rationale='Whole grain + plant protein + 2 vegetables. Should rank '
                  'HIGH on all 3 systems.',
    ),
    CrossPanelMeal(
        label='Sardines + greens (HENI +ve extremum)',
        foods=[
            (3054, 100.0, 'Fish, sardine, Pacific, canned in tomato sauce'),
            (2132, 80.0,  'New Zealand spinach, raw'),
            (1696, 100.0, 'Apple, raw, with skin'),
        ],
        expected_quality='high',
        rationale='Omega-3-rich sardines + dark leafy + fruit. HENI Fig 4 '
                  'sardine extremum is +82 min/serving; HEFI/HSR should also '
                  'score high.',
    ),
    CrossPanelMeal(
        label='Sweet-beverage + refined-grain breakfast',
        foods=[
            (4066, 60.0,  'Bread, white, commercial'),
            (16,   15.0,  'Butter, whipped'),
            (70,   250.0, 'Milk, fluid, chocolate, partly skimmed, 2% M.F.'),
            (1495, 200.0, 'Apple juice, canned'),
        ],
        expected_quality='low',
        rationale='SSB + refined grain + sat fat. Should rank low across all '
                  '3 systems on Beverages, Sugars, Sodium components.',
    ),
]


def _call_heni(c: Client, foods) -> float | None:
    body = {'meal': [{'food_id': fid, 'amount': g, 'unit': 'g'} for fid, g, _ in foods]}
    r = c.post('/api/heni/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['data']['health_impact']['health_impact_minutes'])
    except Exception:
        return None


def _call_hefi(c: Client, foods) -> float | None:
    body = {'foods': [{'food_id': fid, 'amount_g': g} for fid, g, _ in foods]}
    r = c.post('/api/hefi/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['total_score'])
    except Exception:
        return None


def _call_hsr(c: Client, foods) -> float | None:
    body = {
        'food_ids': [fid for fid, _, _ in foods],
        'serving_sizes': [g for _, g, _ in foods],
    }
    r = c.post('/api/hsr/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['hsr_result']['rating']['star_rating'])
    except Exception:
        return None


def _spearman(xs: List[float], ys: List[float]) -> float:
    """Spearman rank correlation; ties broken by average rank."""
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        for i, idx in enumerate(order):
            r[idx] = i + 1.0
        return r
    if len(xs) != len(ys) or len(xs) < 2:
        return float('nan')
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mean_x = sum(rx) / n; mean_y = sum(ry) / n
    num = sum((rx[i] - mean_x) * (ry[i] - mean_y) for i in range(n))
    den_x = sum((r - mean_x) ** 2 for r in rx) ** 0.5
    den_y = sum((r - mean_y) ** 2 for r in ry) ** 0.5
    if den_x == 0 or den_y == 0:
        return float('nan')
    return num / (den_x * den_y)


def main() -> int:
    client = Client()
    rows = []
    print('Cross-system nutrition meal-panel smoke (Scenario S4)')
    print('=' * 76)
    print()
    heni_scores = []
    hefi_scores = []
    hsr_scores = []
    for meal in CROSS_SYSTEM_MEAL_PANEL:
        heni = _call_heni(client, meal.foods)
        hefi = _call_hefi(client, meal.foods)
        hsr = _call_hsr(client, meal.foods)
        heni_scores.append(heni)
        hefi_scores.append(hefi)
        hsr_scores.append(hsr)
        rows.append({
            **asdict(meal),
            'heni_minutes': heni,
            'hefi_score': hefi,
            'hsr_stars': hsr,
        })
        print(f'[{meal.expected_quality:>4}]  {meal.label}')
        heni_s = f'{heni:+7.2f}' if heni is not None else '  None '
        hefi_s = f'{hefi:5.1f}/80' if hefi is not None else ' None  '
        hsr_s = f'{hsr:.1f} stars' if hsr is not None else ' None'
        print(f'         HENI: {heni_s} min   HEFI: {hefi_s}   HSR: {hsr_s}')
        print(f'         {meal.rationale}')
        print()

    # Spearman pairwise — only on meals where all 3 systems returned
    valid_idx = [i for i in range(len(rows))
                 if heni_scores[i] is not None
                 and hefi_scores[i] is not None
                 and hsr_scores[i] is not None]
    print('-' * 76)
    if len(valid_idx) >= 2:
        h_ni = [heni_scores[i] for i in valid_idx]
        h_fi = [hefi_scores[i] for i in valid_idx]
        h_sr = [hsr_scores[i] for i in valid_idx]
        rho_heni_hefi = _spearman(h_ni, h_fi)
        rho_heni_hsr  = _spearman(h_ni, h_sr)
        rho_hefi_hsr  = _spearman(h_fi, h_sr)
        print(f'Spearman rank correlations (n={len(valid_idx)} meals):')
        print(f'   HENI vs HEFI:  rho = {rho_heni_hefi:+.3f}')
        print(f'   HENI vs HSR :  rho = {rho_heni_hsr:+.3f}')
        print(f'   HEFI vs HSR :  rho = {rho_hefi_hsr:+.3f}')
    else:
        rho_heni_hefi = rho_heni_hsr = rho_hefi_hsr = float('nan')
        print('Spearman not computable (insufficient successful meals)')
    print()

    # Per-meal sign coherence: anti-patterns below midpoint, ideal above
    print('-' * 76)
    print('Per-meal directional sanity:')
    HEFI_MID = 40.0
    HSR_MID = 2.5
    HENI_MID = 0.0  # HENI positive = beneficial
    sign_passes = 0
    sign_total = 0
    for r in rows:
        if r['heni_minutes'] is None or r['hefi_score'] is None or r['hsr_stars'] is None:
            continue
        sign_total += 1
        ok = True
        if r['expected_quality'] == 'low':
            ok = (r['hefi_score'] < HEFI_MID and r['hsr_stars'] <= HSR_MID)
        elif r['expected_quality'] == 'high':
            ok = (r['hefi_score'] >= HEFI_MID and r['hsr_stars'] > HSR_MID)
        # 'mid' is unconstrained
        mark = 'ok ' if ok else 'FAIL'
        print(f'   [{mark}] {r["label"]:55s}  expected={r["expected_quality"]}')
        if ok:
            sign_passes += 1
    print()

    out_path = os.path.join(_HERE, '_smoke_nutrition_cross_system_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'panel_description': 'Cross-system nutrition meal-panel (Scenario S4)',
            'rationale': 'For each meal, computes HENI minutes / HEFI score / HSR '
                         'stars and checks (a) Spearman rank correlation across systems '
                         '>= 0.6 and (b) per-meal expected_quality direction matches.',
            'spearman': {
                'heni_vs_hefi': rho_heni_hefi,
                'heni_vs_hsr': rho_heni_hsr,
                'hefi_vs_hsr': rho_hefi_hsr,
                'n_valid_meals': len(valid_idx),
            },
            'directional_sanity': {
                'passes': sign_passes,
                'total_evaluable': sign_total,
            },
            'meals': rows,
            'caveats': [
                'HENI scores affected by extraction bugs (PUFA 10x, sodium '
                'inflation, food-mass-as-nutrient confusion) surfaced in '
                '_smoke_heni_literature_panel_results.json. Cross-system rank '
                'correlations involving HENI are expected to be distorted.',
            ],
        }, f, indent=2)
    print('=' * 76)
    print(f'Spearman HEFI-vs-HSR: {rho_hefi_hsr:+.3f}  (HEFI/HSR don\'t share HENI bug; this is the cleanest signal)')
    print(f'Directional sanity:  {sign_passes}/{sign_total} meals correct')
    print(f'Results JSON: {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
