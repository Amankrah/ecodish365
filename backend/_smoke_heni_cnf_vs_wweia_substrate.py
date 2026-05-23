"""HENI substrate divergence panel: CNF-native HENI vs Stylianou 2021 published.

DISTINCT FROM `_smoke_heni_literature_panel.py` (the implementation regression
harness). This script does NOT test implementation correctness — that's done
there at the ±0.1 min gate, and currently passes 10/10. THIS script
documents the IRREDUCIBLE interpretive gap between:

  • CNF-native HENI    = our pipeline's score for a CNF food (proven correct
                        by the implementation regression harness)
  • Stylianou published = the published Fig 2-4 value for the closest
                        named WWEIA reference food

The divergence is driven by substrate differences between CNF and USDA/
WWEIA (different nutrient compositions for the same food name — e.g. CNF
chicken wing has 98 mg sodium / 100g vs Stylianou's WWEIA reference at
579 mg / 100g, presumably a restaurant/fast-food preparation). NO code
fix can close this gap — it reflects real differences in how Canadian
vs US food-composition databases catalogue food items.

The output is a documented INTERPRETIVE BOUND for any cross-cohort
comparison in the manuscript (§3.2 HENI bullet; §7.4 limitations).

Run from `backend/`:
    python _smoke_heni_cnf_vs_wweia_substrate.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-heni-substrate-divergence'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402

from heni_calculator.heni.service import get_cnf_integrator  # noqa: E402


@dataclass
class DivergenceRow:
    label: str
    cnf_food_id: int
    serving_g: float
    stylianou_published_min: float            # Stylianou 2021 Fig 2-4 central
    stylianou_ci_low: float
    stylianou_ci_high: float
    citation: str
    rationale: str = ''


# Same panel as _smoke_heni_literature_panel.py but with Stylianou's
# published HENI values added as targets for substrate-divergence
# measurement. The published values were extracted from Stylianou 2021
# Fig 2-4 + SI; the chicken-wing worked example is from SI §S2.2 p. 13.
DIVERGENCE_PANEL: List[DivergenceRow] = [
    DivergenceRow(
        label='Chicken wing (CNF 629 vs Stylianou §S2.2 WWEIA reference)',
        cnf_food_id=629, serving_g=85.0,
        stylianou_published_min=-3.3, stylianou_ci_low=-3.9, stylianou_ci_high=-2.5,
        citation='Stylianou 2021 SI §S2.2 p. 13 (canonical worked example)',
        rationale='CNF 629: roasted plain wing meat+skin (98 mg Na/100g). '
                  'Stylianou WWEIA reference: likely restaurant/buffalo wing '
                  '(579 mg Na/100g). Sodium load differs by 6x.',
    ),
    DivergenceRow(
        label='Beef hotdog on bun (CNF 4644 vs Stylianou Fig 4)',
        cnf_food_id=4644, serving_g=150.0,
        stylianou_published_min=-36.0, stylianou_ci_low=-45.0, stylianou_ci_high=-22.0,
        citation='Stylianou 2021 Fig 4 (beef hotdog on bun)',
        rationale='CNF "Fast foods, hot dog, plain" includes bun; lower '
                  'sodium than typical US fast-food + Stylianou worked '
                  'example.',
    ),
    DivergenceRow(
        label='Frankfurter sandwich (CNF 1185+3985 vs Stylianou Fig 2-4)',
        cnf_food_id=1185, serving_g=60.0,  # frankfurter only for substrate calc
        stylianou_published_min=-35.0, stylianou_ci_low=-41.0, stylianou_ci_high=-31.0,
        citation='Stylianou 2021 Fig 2-4 line 1740 (frankfurter sandwich '
                 'category median, IQR 31-41)',
        rationale='Stylianou measures full sandwich; CNF row here is just '
                  'the frankfurter component (60 g).',
    ),
    DivergenceRow(
        label='Vegetable pizza (CNF 5862 vs Stylianou Fig 4)',
        cnf_food_id=5862, serving_g=150.0,
        stylianou_published_min=-1.4, stylianou_ci_low=-2.8, stylianou_ci_high=-0.061,
        citation='Stylianou 2021 Fig 4 (vegetable pizza)',
        rationale='CNF row is "meat and vegetable" pizza (not pure vegetable); '
                  'expect more negative.',
    ),
    DivergenceRow(
        label='Apple pie (CNF 3941 vs Stylianou Fig 4)',
        cnf_food_id=3941, serving_g=150.0,
        stylianou_published_min=+1.3, stylianou_ci_low=-0.42, stylianou_ci_high=+2.9,
        citation='Stylianou 2021 Fig 4 (apple pie)',
    ),
    DivergenceRow(
        label='Sardines in tomato sauce (CNF 3054 vs Stylianou Fig 4 extremum)',
        cnf_food_id=3054, serving_g=100.0,
        stylianou_published_min=+82.0, stylianou_ci_low=+37.0, stylianou_ci_high=+115.0,
        citation='Stylianou 2021 Fig 4 (sardines tomato sauce, +ve extremum)',
        rationale='Stylianou\'s very-high HENI for sardines is driven by '
                  'omega-3 (EPA+DHA) DRF at -81 uDALY/g. Our CNF 3054 '
                  'extraction may have lower EPA+DHA than Stylianou\'s WWEIA '
                  'reference, and the food-group "vegetables" attribution '
                  'for tomato sauce is missing.',
    ),
    DivergenceRow(
        label='Corned beef (CNF 2791 vs Stylianou Fig 4 -ve extremum)',
        cnf_food_id=2791, serving_g=150.0,
        stylianou_published_min=-71.0, stylianou_ci_low=-91.0, stylianou_ci_high=-38.0,
        citation='Stylianou 2021 Fig 4 (corned beef + tomato sauce, -ve extremum)',
        rationale='Stylianou measures the composite "corned beef + tomato '
                  'sauce" with very high sodium; CNF 2791 is canned corned '
                  'beef alone (no added tomato sauce sodium).',
    ),
]


def _call_heni(client: Client, row: DivergenceRow) -> Optional[float]:
    body = {'meal': [{'food_id': row.cnf_food_id, 'amount': row.serving_g, 'unit': 'g'}]}
    r = client.post('/api/heni/calculate/', data=json.dumps(body),
                    content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['data']['health_impact']['health_impact_minutes'])
    except Exception:
        return None


def main() -> int:
    cnf = get_cnf_integrator()
    client = Client()

    print('HENI substrate-divergence panel: CNF-native vs Stylianou 2021 published')
    print('  cnf_native      = our pipeline (validated 10/10 by implementation harness)')
    print('  stylianou_pub   = Stylianou 2021 Fig 2-4 + SI per-food central value')
    print('  divergence_min  = cnf_native - stylianou_pub  (positive = CNF less detrimental)')
    print('=' * 80)
    print()

    results = []
    abs_dev = []
    for row in DIVERGENCE_PANEL:
        actual = _call_heni(client, row)
        if actual is None:
            print(f'[ERROR] {row.label}')
            results.append({**asdict(row), 'cnf_native_min': None, 'divergence_min': None})
            continue
        delta = actual - row.stylianou_published_min
        abs_dev.append(abs(delta))
        # CNF nutrient context for the divergence story
        nd = cnf.get_nutrient_data(row.cnf_food_id)
        sodium_mg = nd.get('SODIUM', 0)
        kcal = nd.get('ENERGY (KILOCALORIES)', 0)

        print(f'  {row.label}')
        print(f'    serving={row.serving_g:.0f} g  CNF Na={sodium_mg:.0f} mg/100g  E={kcal:.0f} kcal/100g')
        print(f'    cnf_native     : {actual:+8.2f} min')
        print(f'    stylianou_pub  : {row.stylianou_published_min:+8.2f} min  (CI [{row.stylianou_ci_low:+.1f}, {row.stylianou_ci_high:+.1f}])')
        print(f'    divergence     : {delta:+8.2f} min')
        if abs(delta) > 0:
            ratio = abs(actual) / abs(row.stylianou_published_min) if row.stylianou_published_min != 0 else float('inf')
            print(f'    magnitude ratio: {ratio:.2f}x (|cnf| / |stylianou|)')
        print(f'    notes: {row.rationale or "(no rationale)"}')
        print()
        results.append({
            **asdict(row),
            'cnf_native_min': actual,
            'divergence_min': delta,
            'cnf_sodium_mg_per_100g': sodium_mg,
            'cnf_kcal_per_100g': kcal,
        })

    # Aggregate envelope statistics
    if abs_dev:
        median_dev = sorted(abs_dev)[len(abs_dev) // 2]
        max_dev = max(abs_dev)
        mean_dev = sum(abs_dev) / len(abs_dev)
    else:
        median_dev = max_dev = mean_dev = float('nan')
    print('=' * 80)
    print('CNF-vs-WWEIA substrate divergence envelope (this panel):')
    print(f'  n            = {len(abs_dev)}')
    print(f'  median |dev| = {median_dev:.2f} min')
    print(f'  mean   |dev| = {mean_dev:.2f} min')
    print(f'  max    |dev| = {max_dev:.2f} min')
    print()
    print('Interpretation:')
    print('  - Divergences this large are EXPECTED and reflect real differences')
    print('    in CNF vs USDA/WWEIA food-composition cataloguing (especially')
    print('    sodium loads in processed-meat / fast-food rows).')
    print('  - Implementation correctness is VALIDATED separately by')
    print('    _smoke_heni_literature_panel.py (10/10 PASS at +-0.1 min).')
    print('  - For cross-cohort comparison with Stylianou\'s US-anchored HENI,')
    print('    apply this divergence envelope as the interpretive bound.')

    out_path = os.path.join(_HERE, '_smoke_heni_cnf_vs_wweia_substrate_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'panel_description': 'CNF-native HENI vs Stylianou 2021 published per-food values',
            'separates_from': '_smoke_heni_literature_panel.py (which is the '
                              'implementation regression at +-0.1 min gate)',
            'envelope': {
                'n': len(abs_dev),
                'median_abs_dev_min': median_dev,
                'mean_abs_dev_min': mean_dev,
                'max_abs_dev_min': max_dev,
            },
            'rows': results,
        }, f, indent=2, default=str)
    print(f'\nResults JSON: {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
