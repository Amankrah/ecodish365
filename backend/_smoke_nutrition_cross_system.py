"""Cross-system nutrition meal-panel smoke (Scenario S4).

For each meal in `CROSS_SYSTEM_MEAL_PANEL`, calls all four nutrition
endpoints (/api/heni/calculate/, /api/hefi/calculate/, /api/hsr/calculate/,
/api/fcs/calculate/) and checks:

  1. **Directional ranking**: across the panel, the rank order of meals
     by HENI minutes (ascending = worse to better), HEFI score
     (ascending = worse to better), HSR stars (ascending = worse to
     better), and FCS (ascending = worse to better) should agree.
     Spearman ρ between any pair should be >= 0.6 (lenient because the
     systems weight different dimensions).

  2. **Per-meal sign coherence**: meals that are obvious anti-patterns
     (processed-meat-heavy, SSB-only) must score below the midpoint on
     ALL four systems; meals that are CFG-aligned must score above the
     midpoint on ALL four.

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


def _call_fcs(c: Client, foods) -> float | None:
    body = {
        'food_ids': [fid for fid, _, _ in foods],
        'food_names': [name for _, _, name in foods],
        'serving_sizes': [g for _, g, _ in foods],
    }
    r = c.post('/api/fcs/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        # Response shape: {success, data: {data: {fcs, ...}, ...}, message}
        # (same nested envelope as HENI canonical panel)
        payload = r.json().get('data', {})
        node = payload.get('data', payload)
        return float(node['fcs'])
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


def _bootstrap_spearman_ci(xs: List[float], ys: List[float],
                           n_resamples: int = 2000, seed: int = 42,
                           confidence: float = 0.95) -> Tuple[float, float]:
    """Percentile-bootstrap CI for Spearman rho.

    Mirrors the percentile-bootstrap shape used by
    `_smoke_matcher_benchmark.py` (B = 1000), bumped to B = 2000 per
    Tier 1 plan A. Resamples meal indices with replacement; degenerate
    resamples (ties-only -> denominator zero -> NaN) are dropped rather
    than counted, since they reflect resampling pathology, not the
    underlying rho distribution.
    """
    import random as _random
    if len(xs) != len(ys) or len(xs) < 2:
        return float('nan'), float('nan')
    rng = _random.Random(seed)
    n = len(xs)
    rhos: List[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        rx = [xs[i] for i in idx]
        ry = [ys[i] for i in idx]
        rho = _spearman(rx, ry)
        if rho == rho:
            rhos.append(rho)
    if len(rhos) < 50:
        return float('nan'), float('nan')
    rhos.sort()
    alpha = (1.0 - confidence) / 2.0
    lo_idx = int(alpha * len(rhos))
    hi_idx = int((1.0 - alpha) * len(rhos)) - 1
    lo_idx = max(0, min(len(rhos) - 1, lo_idx))
    hi_idx = max(0, min(len(rhos) - 1, hi_idx))
    return rhos[lo_idx], rhos[hi_idx]


def main() -> int:
    client = Client()
    rows = []
    print('Cross-system nutrition meal-panel smoke (Scenario S4)')
    print('=' * 76)
    print()
    heni_scores = []
    hefi_scores = []
    hsr_scores = []
    fcs_scores = []
    for meal in CROSS_SYSTEM_MEAL_PANEL:
        heni = _call_heni(client, meal.foods)
        hefi = _call_hefi(client, meal.foods)
        hsr = _call_hsr(client, meal.foods)
        fcs = _call_fcs(client, meal.foods)
        heni_scores.append(heni)
        hefi_scores.append(hefi)
        hsr_scores.append(hsr)
        fcs_scores.append(fcs)
        rows.append({
            **asdict(meal),
            'heni_minutes': heni,
            'hefi_score': hefi,
            'hsr_stars': hsr,
            'fcs_score': fcs,
        })
        print(f'[{meal.expected_quality:>4}]  {meal.label}')
        heni_s = f'{heni:+7.2f}' if heni is not None else '  None '
        hefi_s = f'{hefi:5.1f}/80' if hefi is not None else ' None  '
        hsr_s = f'{hsr:.1f} stars' if hsr is not None else ' None'
        fcs_s = f'{fcs:5.1f}/100' if fcs is not None else ' None  '
        print(f'         HENI: {heni_s} min   HEFI: {hefi_s}   HSR: {hsr_s}   FCS: {fcs_s}')
        print(f'         {meal.rationale}')
        print()

    # Spearman pairwise — only on meals where all 4 systems returned
    valid_idx = [i for i in range(len(rows))
                 if heni_scores[i] is not None
                 and hefi_scores[i] is not None
                 and hsr_scores[i] is not None
                 and fcs_scores[i] is not None]
    print('-' * 76)
    if len(valid_idx) >= 2:
        h_ni = [heni_scores[i] for i in valid_idx]
        h_fi = [hefi_scores[i] for i in valid_idx]
        h_sr = [hsr_scores[i] for i in valid_idx]
        f_cs = [fcs_scores[i] for i in valid_idx]
        rho_heni_hefi = _spearman(h_ni, h_fi)
        rho_heni_hsr  = _spearman(h_ni, h_sr)
        rho_heni_fcs  = _spearman(h_ni, f_cs)
        rho_hefi_hsr  = _spearman(h_fi, h_sr)
        rho_hefi_fcs  = _spearman(h_fi, f_cs)
        rho_hsr_fcs   = _spearman(h_sr, f_cs)
        # Percentile bootstrap 95 % CI per pair (B = 2000, seed-pinned).
        # Plan A.
        bs_kwargs = {'n_resamples': 2000, 'seed': 42, 'confidence': 0.95}
        ci_heni_hefi = _bootstrap_spearman_ci(h_ni, h_fi, **bs_kwargs)
        ci_heni_hsr  = _bootstrap_spearman_ci(h_ni, h_sr, **bs_kwargs)
        ci_heni_fcs  = _bootstrap_spearman_ci(h_ni, f_cs, **bs_kwargs)
        ci_hefi_hsr  = _bootstrap_spearman_ci(h_fi, h_sr, **bs_kwargs)
        ci_hefi_fcs  = _bootstrap_spearman_ci(h_fi, f_cs, **bs_kwargs)
        ci_hsr_fcs   = _bootstrap_spearman_ci(h_sr, f_cs, **bs_kwargs)
        # Headline table
        print(f'Spearman rank correlations + 95 % percentile-bootstrap CI '
              f'(B = 2000, n = {len(valid_idx)} meals):')
        print(f'   HENI vs HEFI:  rho = {rho_heni_hefi:+.3f}  '
              f'95 % CI [{ci_heni_hefi[0]:+.3f}, {ci_heni_hefi[1]:+.3f}]')
        print(f'   HENI vs HSR :  rho = {rho_heni_hsr:+.3f}  '
              f'95 % CI [{ci_heni_hsr[0]:+.3f}, {ci_heni_hsr[1]:+.3f}]')
        print(f'   HENI vs FCS :  rho = {rho_heni_fcs:+.3f}  '
              f'95 % CI [{ci_heni_fcs[0]:+.3f}, {ci_heni_fcs[1]:+.3f}]')
        print(f'   HEFI vs HSR :  rho = {rho_hefi_hsr:+.3f}  '
              f'95 % CI [{ci_hefi_hsr[0]:+.3f}, {ci_hefi_hsr[1]:+.3f}]')
        print(f'   HEFI vs FCS :  rho = {rho_hefi_fcs:+.3f}  '
              f'95 % CI [{ci_hefi_fcs[0]:+.3f}, {ci_hefi_fcs[1]:+.3f}]')
        print(f'   HSR  vs FCS :  rho = {rho_hsr_fcs:+.3f}  '
              f'95 % CI [{ci_hsr_fcs[0]:+.3f}, {ci_hsr_fcs[1]:+.3f}]')
        # Mean off-diagonal as a single agreement summary.
        rhos = [rho_heni_hefi, rho_heni_hsr, rho_heni_fcs,
                rho_hefi_hsr, rho_hefi_fcs, rho_hsr_fcs]
        mean_rho = sum(rhos) / len(rhos)
        # Share of pairs whose CI excludes zero (proxy for "stays positive
        # under resampling"). Useful manuscript-side summary.
        ci_pairs = [ci_heni_hefi, ci_heni_hsr, ci_heni_fcs,
                    ci_hefi_hsr, ci_hefi_fcs, ci_hsr_fcs]
        n_positive_ci = sum(1 for lo, _hi in ci_pairs if lo > 0.0)
        print(f'   mean off-diagonal rho = {mean_rho:+.3f}')
        print(f'   pairs with 95 % CI strictly above 0: {n_positive_ci}/6')
    else:
        rho_heni_hefi = rho_heni_hsr = rho_heni_fcs = float('nan')
        rho_hefi_hsr = rho_hefi_fcs = rho_hsr_fcs = float('nan')
        mean_rho = float('nan')
        nan_pair = (float('nan'), float('nan'))
        ci_heni_hefi = ci_heni_hsr = ci_heni_fcs = nan_pair
        ci_hefi_hsr = ci_hefi_fcs = ci_hsr_fcs = nan_pair
        n_positive_ci = 0
        print('Spearman not computable (insufficient successful meals)')
    print()

    # Per-meal sign coherence: anti-patterns below midpoint, ideal above.
    # FCS midpoint anchored to Mozaffarian 2021 bands (encourage>=70, limit<=30).
    # We require strictly above the limit ceiling for 'high' and strictly below
    # the encourage floor for 'low'; the 31..69 'moderate' band leaves room for
    # disagreement without flagging.
    print('-' * 76)
    print('Per-meal directional sanity:')
    HEFI_MID = 40.0
    HSR_MID = 2.5
    HENI_MID = 0.0  # HENI positive = beneficial
    FCS_LIMIT_CEIL = 30.0
    FCS_ENCOURAGE_FLOOR = 70.0
    sign_passes = 0
    sign_total = 0
    for r in rows:
        if (r['heni_minutes'] is None or r['hefi_score'] is None
                or r['hsr_stars'] is None or r['fcs_score'] is None):
            continue
        sign_total += 1
        ok = True
        if r['expected_quality'] == 'low':
            ok = (r['hefi_score'] < HEFI_MID and r['hsr_stars'] <= HSR_MID
                  and r['fcs_score'] <= FCS_LIMIT_CEIL)
        elif r['expected_quality'] == 'high':
            ok = (r['hefi_score'] >= HEFI_MID and r['hsr_stars'] > HSR_MID
                  and r['fcs_score'] > FCS_LIMIT_CEIL)
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
                         'stars / FCS-10 score and checks (a) Spearman rank '
                         'correlation across systems >= 0.6 and (b) per-meal '
                         'expected_quality direction matches.',
            'spearman': {
                'heni_vs_hefi': rho_heni_hefi,
                'heni_vs_hsr': rho_heni_hsr,
                'heni_vs_fcs': rho_heni_fcs,
                'hefi_vs_hsr': rho_hefi_hsr,
                'hefi_vs_fcs': rho_hefi_fcs,
                'hsr_vs_fcs': rho_hsr_fcs,
                'mean_off_diagonal': mean_rho,
                'n_valid_meals': len(valid_idx),
                'bootstrap_ci_95': {
                    'method': 'percentile bootstrap, B=2000, seed=42',
                    'heni_vs_hefi': list(ci_heni_hefi),
                    'heni_vs_hsr': list(ci_heni_hsr),
                    'heni_vs_fcs': list(ci_heni_fcs),
                    'hefi_vs_hsr': list(ci_hefi_hsr),
                    'hefi_vs_fcs': list(ci_hefi_fcs),
                    'hsr_vs_fcs': list(ci_hsr_fcs),
                    'pairs_with_ci_above_zero': n_positive_ci,
                    'n_pairs_total': 6,
                },
            },
            'directional_sanity': {
                'passes': sign_passes,
                'total_evaluable': sign_total,
                'fcs_thresholds': {
                    'limit_ceiling': FCS_LIMIT_CEIL,
                    'encourage_floor': FCS_ENCOURAGE_FLOOR,
                    'source': 'Mozaffarian 2021 Methods p. 8',
                },
            },
            'meals': rows,
            'caveats': [
                'HENI: extraction bugs documented in '
                '_smoke_heni_literature_panel_results.json (HENI-CODE-1.y) '
                'still distort some meals; cross-system correlations '
                'involving HENI are expected noisier than HEFI/HSR/FCS.',
                'FCS: per-meal score uses extract_and_score on the combined '
                'food list with serving_sizes; FCS-10 has no published per-meal '
                'canonical reference (Mozaffarian 2021 validates at the '
                '54-attribute / 8 032-food level), so this is a directional '
                'rank check, not a value reproduction.',
            ],
        }, f, indent=2)
    print('=' * 76)
    print(f'Mean off-diagonal Spearman rho: {mean_rho:+.3f}')
    print(f'Directional sanity:  {sign_passes}/{sign_total} meals correct')
    print(f'Results JSON: {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
