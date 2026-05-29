"""Smoke demo for the nutrient research workbench (POST /api/cnf/discover/ backend).

Runs the research questions the workbench is built to answer and prints the top hits,
so the multi-criteria / density / ratio / %DV-threshold capabilities are visible at a
glance. Deterministic (pure pandas over the CNF catalogue; no LLM, no network).

Run:  cd backend && python _smoke_cnf_discover.py
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault('DJANGO_SECRET_KEY', 'smoke-discover')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.cnf_cache import get_dish_cnf_pipeline  # noqa: E402

PROTEIN, FAT, SATFAT, SODIUM, POTASSIUM = 203, 204, 606, 307, 306
CALCIUM, IRON, FIBRE, SUGARS = 301, 303, 291, 269
LEGUMES = 16


def _show(title, out, value_keys):
    print('\n' + '=' * 84)
    print(title)
    print('-' * 84)
    print(f'{out["count"]} foods (basis={out["basis"]})')
    for f in out['foods'][:8]:
        bits = []
        for label, nid in value_keys:
            v = f['basis_values'].get(str(nid)) if out['basis'] == 'per_100kcal' else f['nutrient_values'].get(str(nid))
            if v is not None:
                bits.append(f'{label}={v}')
        if f.get('ratio_value') is not None:
            bits.append(f'ratio={f["ratio_value"]}')
        print(f'  [{f["FoodID"]:>6}] {f["FoodDescription"][:46]:46s} {"  ".join(bits)}')


def main():
    p = get_dish_cnf_pipeline()

    _show('Q1  DASH-friendly: potassium >= 300 mg AND sodium <= 50 mg / 100 g',
          p.discover_foods([{'nutrient_id': POTASSIUM, 'min': 300},
                            {'nutrient_id': SODIUM, 'max': 50}],
                           sort={'key': POTASSIUM, 'direction': 'desc'}, limit=50),
          [('K', POTASSIUM), ('Na', SODIUM)])

    _show('Q2  Lean protein: protein >= 20 g AND saturated fat <= 2 g / 100 g',
          p.discover_foods([{'nutrient_id': PROTEIN, 'min': 20},
                            {'nutrient_id': SATFAT, 'max': 2}],
                           sort={'key': PROTEIN, 'direction': 'desc'}, limit=50),
          [('protein', PROTEIN), ('satfat', SATFAT)])

    _show('Q3  Most CALCIUM per 100 kcal (energy-adjusted density)',
          p.discover_foods([{'nutrient_id': CALCIUM, 'min': 1}], basis='per_100kcal',
                           sort={'key': CALCIUM, 'direction': 'desc'}, limit=50),
          [('Ca/100kcal', CALCIUM)])

    _show('Q4  >= 50% Daily Value of IRON per 100 g',
          p.discover_foods([], dv_threshold={'nutrient_id': IRON, 'min_pct': 50},
                           sort={'key': IRON, 'direction': 'desc'}, limit=50),
          [('Fe', IRON)])

    _show('Q5  Lowest sodium:potassium ratio (best for blood pressure)',
          p.discover_foods([{'nutrient_id': POTASSIUM, 'min': 100}],
                           ratio={'numerator_id': SODIUM, 'denominator_id': POTASSIUM},
                           sort={'key': 'ratio', 'direction': 'asc'}, limit=50),
          [('Na', SODIUM), ('K', POTASSIUM)])

    _show('Q6  Richest IRON within Legumes (food-group scoped)',
          p.discover_foods([{'nutrient_id': IRON, 'min': 1}], food_group_id=LEGUMES,
                           sort={'key': IRON, 'direction': 'desc'}, limit=50),
          [('Fe', IRON), ('fibre', FIBRE)])

    print('\nAll discover demo queries ran.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
