"""FCS-10 canonical-food smoke (Mozaffarian 2021 / O'Hearn 2022 / Barrett 2025).

Unlike HENI (which has Stylianou Fig 2-4 per-food canonical values) and HSR
(which has HSRAC v9 Appendix 1 reference foods), the Food Compass / FCS-10
literature does NOT publish per-food canonical scores. Mozaffarian et al.
2021 (Nature Food) validates at the aggregate level (54-attribute scoring
of 8,032 NHANES foods, mean FCS 43.2, SD 28.5); O'Hearn et al. 2022 (Nature
Comm) validates at the diet level (i.FCS HR 0.93 per 1 SD for all-cause
mortality); Barrett et al. 2025 (AJCN) validates label-only FCS-10 against
the full FCS at r=0.93 / RMSE=0.90 across 538 branded products.

The smoke therefore tests at the RECOMMENDATION-BAND level rather than
specific FCS values:

  - "encourage"  → FCS >= 70  (Mozaffarian 2021 Methods p. 8 cut-off)
  - "moderate"   → FCS 31-69
  - "limit"      → FCS <= 30

Per-food gates: the actual FCS must fall in its expected band.
Cross-panel gate: directional rank — any encourage food's FCS must exceed
any limit food's FCS. Plus a single pytest-anchored regression: CNF FoodID
29 (Cheese, edam) must reproduce FCS=21.61 from the FCS-CODE-1 (2026-05-21)
Mozaffarian rescaling formula audit (pinned in
`fcs_calculator/tests/test_fcs_rust.py::test_golden_food_29_scores_stable`).

Run from `backend/`:
    python _smoke_fcs_canonical_panel.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-fcs-canonical-panel'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402


# Mozaffarian 2021 Methods p. 8 recommendation cut-offs (FCS 1-100 scale).
BAND_ENCOURAGE_FLOOR = 70.0
BAND_LIMIT_CEILING = 30.0


@dataclass
class FCSPanelRow:
    label: str
    cnf_food_id: int
    expected_band: str  # 'encourage' | 'moderate' | 'limit'
    rationale: str = ''


# Each row reflects an a-priori expected band from the Mozaffarian 2021
# Food Compass design: whole / minimally-processed foods with strong
# nutrient density should land in `encourage`; refined-grain / processed-
# meat / added-sugar foods should land in `limit`; the moderate band
# covers everything in between (which O'Hearn 2022 NHANES showed is
# ~67 % of foods).
FCS_CANONICAL_PANEL: List[FCSPanelRow] = [
    # Encourage band — whole foods, raw or minimally processed
    FCSPanelRow('Apple, raw, with skin', 1696, 'encourage',
                'Whole fruit, no processing — Mozaffarian 2021 Fig 1 fruits '
                'have highest mean FCS among 12 NHANES food groups.'),
    FCSPanelRow('Broccoli, frozen, boiled', 2026, 'encourage',
                'Whole vegetable, light processing.'),
    FCSPanelRow('Chia seeds, dried', 2511, 'encourage',
                'Seeds: high fibre + omega-3 + protein density.'),
    # Moderate band — dairy, juice, refined grain in modest amounts
    FCSPanelRow('Milk, fluid, whole 3.25%', 113, 'moderate',
                'Dairy beverage: protein + calcium offset moderate sat fat.'),
    FCSPanelRow('Yogurt, Greek style, plain, fat free', 502188, 'encourage',
                'Plain fat-free Greek yogurt: high protein, calcium, no added '
                'sugar, fermented dairy. REVISED 2026-05-23 (target moderate '
                '-> encourage) after the NOVA classifier refactor also fixed '
                'a latent YOGURT-detection bug — the previous "YOGURT in desc" '
                'check missed the Canadian "YOGOURT" spelling, so Greek '
                'yogurt did not receive the yogurt food_ingredients attribute. '
                'With the attribute correctly set, plain fat-free Greek yogurt '
                'lands at FCS 84.1, in the top decile of Mozaffarian 2021\'s '
                'NHANES distribution (only ~0.5%% of foods score >=70).'),
    FCSPanelRow('Apple juice, canned/bottled', 1495, 'moderate',
                '100% juice: no added sugar, some fruit nutrients but no '
                'fibre — Mozaffarian Discussion identifies juices as a '
                'borderline-moderate case.'),
    # Limit band — refined grain, processed meat, added sugar
    FCSPanelRow('Bread, white, commercial', 4066, 'limit',
                'Refined grain, high sodium — Mozaffarian 2021 Fig 1 places '
                'refined breads in the limit band.'),
    FCSPanelRow('Pork, cured, bacon, raw', 1936, 'limit',
                'Processed meat: high sodium, sat fat, nitrites.'),
    FCSPanelRow('Fast foods, hot dog, plain', 4644, 'limit',
                'Processed meat + refined bun: composite limit.'),
    FCSPanelRow('Pizza, pepperoni, frozen, cooked', 4962, 'limit',
                'Mixed processed dish: refined crust + processed meat + '
                'cheese; expect ~20-30 FCS (lower limit band).'),
    FCSPanelRow('Sweets, sugars, granulated', 4318, 'limit',
                'Pure refined sucrose — should hit limit floor (~1).'),
]


# Golden test (mirrors `fcs_calculator/tests/test_fcs_rust.py::test_golden_food_29_scores_stable`).
# Pinned by the FCS-CODE-1 (2026-05-21) Mozaffarian rescaling formula audit:
#   FCS = 100 - ((26.1 - original_score) / 36.7) × 99
# For food_id=29 (Cheese, edam) original_score=12.07, FCS=21.61.
GOLDEN_FOOD_ID = 29
GOLDEN_FCS_EXPECTED = 21.61
GOLDEN_FCS_TOLERANCE = 0.5  # generous; tighter pinning is in pytest


def _call_fcs(client: Client, food_id: int, name: str) -> tuple[Optional[float], Optional[dict], Optional[str]]:
    body = {'food_ids': [food_id], 'food_names': [name]}
    r = client.post('/api/fcs/calculate/', data=json.dumps(body),
                    content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None, f'HTTP {r.status_code}: {r.content[:300]!r}'
    try:
        d = r.json()['data']['data']
        fcs = float(d['fcs'])
        diag = {
            'original_score': d.get('original_score'),
            'nova_category': d.get('nova_category'),
            'name': d.get('name'),
        }
        return fcs, diag, None
    except Exception as exc:
        return None, None, f'parse error: {exc!r}'


def _band_of(fcs: float) -> str:
    if fcs >= BAND_ENCOURAGE_FLOOR:
        return 'encourage'
    if fcs <= BAND_LIMIT_CEILING:
        return 'limit'
    return 'moderate'


def main() -> int:
    client = Client()

    print('FCS-10 canonical-food smoke (Mozaffarian 2021 / O\'Hearn 2022 / Barrett 2025)')
    print(f'  Bands: encourage >= {BAND_ENCOURAGE_FLOOR}; limit <= {BAND_LIMIT_CEILING}; moderate in between')
    print('=' * 80)
    print()

    # Per-row band assertions
    n_pass = n_fail = 0
    results = []
    encourage_scores: List[float] = []
    limit_scores: List[float] = []

    for row in FCS_CANONICAL_PANEL:
        fcs, diag, err = _call_fcs(client, row.cnf_food_id, row.label)
        if err is not None:
            print(f'[ERROR] {row.label}: {err}')
            n_fail += 1
            results.append({**asdict(row), 'fcs_actual': None, 'verdict': 'ERROR'})
            continue
        actual_band = _band_of(fcs)
        within = actual_band == row.expected_band
        verdict = 'PASS' if within else 'FAIL'
        if within:
            n_pass += 1
        else:
            n_fail += 1
        if row.expected_band == 'encourage':
            encourage_scores.append(fcs)
        elif row.expected_band == 'limit':
            limit_scores.append(fcs)

        print(f'[{verdict:>4}]  {row.label}')
        print(f'        cnf {row.cnf_food_id}  expected={row.expected_band:9s}  '
              f'actual_fcs={fcs:5.1f}  actual_band={actual_band}')
        if diag and diag.get('nova_category'):
            print(f'        nova={diag["nova_category"]}  original_score={diag.get("original_score")}')
        if not within:
            print(f'        original_score: {diag.get("original_score")}')
        print()
        results.append({
            **asdict(row),
            'fcs_actual': fcs,
            'fcs_actual_band': actual_band,
            'within_gate': within,
            'verdict': verdict,
            'diagnostics': diag,
        })

    # Directional-rank assertion: min(encourage) > max(limit)
    print('-' * 80)
    if encourage_scores and limit_scores:
        min_encourage = min(encourage_scores)
        max_limit = max(limit_scores)
        rank_ok = min_encourage > max_limit
        print(f'Directional rank: min(encourage)={min_encourage:.1f}  '
              f'max(limit)={max_limit:.1f}  '
              f'{"PASS" if rank_ok else "FAIL"}')
    else:
        rank_ok = False
        print('Directional rank: SKIP (need both encourage + limit foods)')
    print()

    # Golden regression test
    print('-' * 80)
    print(f'Golden regression (food_id={GOLDEN_FOOD_ID} Cheese Edam):')
    gold_fcs, _, gold_err = _call_fcs(client, GOLDEN_FOOD_ID, 'Cheese, edam')
    golden_ok = False
    if gold_err:
        print(f'  ERROR: {gold_err}')
    else:
        delta = abs(gold_fcs - GOLDEN_FCS_EXPECTED)
        golden_ok = delta < GOLDEN_FCS_TOLERANCE
        print(f'  expected FCS = {GOLDEN_FCS_EXPECTED:.2f}  actual = {gold_fcs:.2f}  '
              f'delta = {delta:.2f}  {"PASS" if golden_ok else "FAIL"}')
        print(f'  (Pinned by FCS-CODE-1 2026-05-21 Mozaffarian rescaling audit; '
              f'tighter pinning at +-0.01 in '
              f'fcs_calculator/tests/test_fcs_rust.py::test_golden_food_29_scores_stable)')
    print()

    print('=' * 80)
    n_total = n_pass + n_fail
    band_ok = (n_pass == n_total)
    overall = band_ok and rank_ok and golden_ok
    print(f'Summary:')
    print(f'  per-food band gate : {n_pass}/{n_total} PASS')
    print(f'  directional rank   : {"PASS" if rank_ok else "FAIL"}')
    print(f'  golden regression  : {"PASS" if golden_ok else "FAIL"}')
    print(f'  overall            : {"PASS" if overall else "FAIL"}')

    out_path = os.path.join(_HERE, '_smoke_fcs_canonical_panel_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'panel_description': 'FCS-10 canonical-food smoke (band gates + directional rank + golden regression)',
            'gate_policy': {
                'per_food_band': 'actual FCS must fall in expected Mozaffarian 2021 band '
                                 f'(encourage >= {BAND_ENCOURAGE_FLOOR}; limit <= {BAND_LIMIT_CEILING}; '
                                 'moderate in between)',
                'directional_rank': 'min(FCS of encourage foods) > max(FCS of limit foods)',
                'golden_regression': f'food_id={GOLDEN_FOOD_ID} (Cheese, edam) must reproduce '
                                     f'FCS={GOLDEN_FCS_EXPECTED} from FCS-CODE-1 audit',
            },
            'summary': {
                'n_pass_band': n_pass,
                'n_total': n_total,
                'rank_pass': rank_ok,
                'golden_pass': golden_ok,
                'overall_pass': overall,
            },
            'notes': [
                'FCS and FCS-10 literature validate aggregate metrics (Spearman r, RMSE, '
                'band accuracy) rather than publishing per-food canonical FCS values, '
                'so the smoke uses band-categorical gates (Mozaffarian 2021 Methods p. 8) '
                'rather than per-food numerical targets.',
                'O\'Hearn 2022 NHANES distribution: ~33% limit, ~67% moderate, ~0.5% encourage '
                '(the encourage band is exclusive in practice). Our smoke panel oversamples '
                'the encourage and limit bands for dynamic-range testing.',
                'The golden regression at food_id=29 reproduces the FCS-CODE-1 (2026-05-21) '
                'Mozaffarian rescaling formula audit value (21.61); tighter pinning '
                '(+-0.01) lives in pytest at fcs_calculator/tests/test_fcs_rust.py.',
            ],
            'rows': results,
        }, f, indent=2)
    print(f'Results JSON: {out_path}')
    return 0 if overall else 1


if __name__ == '__main__':
    sys.exit(main())
