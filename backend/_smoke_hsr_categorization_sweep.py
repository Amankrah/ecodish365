"""HSR per-food categoriser STRESS SWEEP (2026-05-23).

Companion to `_smoke_hsr_categorization.py`, which gates the categoriser
against a hand-picked 28-food panel. This sweep instead samples N foods from
EACH CNF FoodGroup (23 groups × N foods) and classifies every one through
`FoodGroupMapper.get_category()` — the same per-food rule chain used by the
HSR API but invoked directly so we don't pay the per-request CNF-load cost.

The point is to surface long-tail edge cases the targeted panel missed:
foods whose name doesn't match any keyword override, foreign-language
variants, novel CNF additions, etc. For each FoodGroup we report the
observed HSR-category distribution and flag any category assignments that
violate the expected distribution for that group (anomaly rules below).

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_hsr_categorization_sweep.py [--sample 25]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Callable, Dict, List, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-hsr-sweep'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

import pandas as pd  # noqa: E402
from django.conf import settings  # noqa: E402

from hsr_calculator.hsr.constants.food_groups import FOOD_GROUPS  # noqa: E402
from hsr_calculator.hsr.utils.food_group_mapper import FoodGroupMapper  # noqa: E402


# --- Anomaly rules --------------------------------------------------------
# Per-FoodGroup expected categories. A "violation" is when a food in that
# group lands in a category outside this set — flagged for manual review.
# Conservative: we mark only assignments that are *obviously* wrong, not
# every category that's merely "interesting".
EXPECTED_CATEGORIES: Dict[int, List[str]] = {
    1:  ['1D', '2', '2D', '3', '3D'],     # Dairy & egg: dairy bev / egg-2 / dairy food / butter→3 / cheese
    2:  ['2'],                             # Spices & herbs
    3:  ['2', '2D'],                       # Baby foods (could be dairy-based)
    4:  ['3'],                             # Fats & oils → Cat 3 unambiguously
    5:  ['2'],                             # Poultry
    6:  ['2'],                             # Soups & sauces (mixed dishes)
    7:  ['2'],                             # Sausages
    8:  ['2'],                             # Breakfast cereals
    9:  ['1', '2'],                        # Fruits + juices (juices → 1, whole fruits → 2)
    10: ['2'],                             # Pork
    11: ['2'],                             # Vegetables
    12: ['2', '3'],                        # Nuts & seeds (could be Cat 3 if oily)
    13: ['2'],                             # Beef
    14: ['1', '1D'],                       # Beverages → 1 or 1D
    15: ['2'],                             # Fish & shellfish
    16: ['2'],                             # Legumes
    17: ['2'],                             # Lamb, veal, game
    18: ['2'],                             # Baked products
    19: ['2'],                             # Sweets
    20: ['2'],                             # Cereals, grains, pasta
    21: ['1', '2'],                        # Fast foods (most → 2; soda → 1)
    22: ['2'],                             # Mixed dishes
    25: ['2'],                             # Snacks
}


def load_food_name_csv() -> pd.DataFrame:
    """Load FOOD_NAME.csv from the configured CNF folder."""
    path = os.path.join(settings.CNF_FOLDER, 'FOOD_NAME.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(
            f'FOOD_NAME.csv not found at {path}. Configure settings.CNF_FOLDER.'
        )
    return pd.read_csv(path, encoding='latin-1', low_memory=False)


def sample_foods(fn: pd.DataFrame, group_id: int, n: int) -> List[Tuple[int, str]]:
    """Return up to `n` (food_id, food_name) tuples from a given FoodGroup,
    deterministically (sorted by FoodID ascending) so the sweep is repeatable."""
    sub = fn[fn['FoodGroupID'] == group_id][['FoodID', 'FoodDescription']]
    sub = sub.sort_values('FoodID').head(n)
    return [(int(r['FoodID']), str(r['FoodDescription'])) for _, r in sub.iterrows()]


def run_sweep(sample_size: int) -> Dict[int, Dict]:
    """Categorise N foods per CNF FoodGroup. Returns per-group results."""
    fn = load_food_name_csv()
    per_group: Dict[int, Dict] = {}

    for group_id, group_name in FOOD_GROUPS.items():
        foods = sample_foods(fn, group_id, sample_size)
        if not foods:
            per_group[group_id] = {
                'group_name': group_name, 'sampled': 0,
                'distribution': {}, 'anomalies': [],
                'note': 'no foods found in CNF for this group',
            }
            continue

        categories: List[str] = []
        anomalies: List[Dict] = []
        expected = EXPECTED_CATEGORIES.get(group_id, [])

        for food_id, food_name in foods:
            try:
                cat = FoodGroupMapper.get_category(group_id, food_name)
                cat_value = cat.value
            except Exception as exc:
                cat_value = f'ERR({exc!r})'
            categories.append(cat_value)
            if expected and cat_value not in expected:
                anomalies.append({
                    'food_id': food_id,
                    'food_name': food_name[:80],
                    'assigned_category': cat_value,
                    'expected_one_of': expected,
                })

        per_group[group_id] = {
            'group_name': group_name,
            'sampled': len(foods),
            'distribution': dict(Counter(categories).most_common()),
            'anomalies': anomalies,
        }

    return per_group


def print_report(per_group: Dict[int, Dict], sample_size: int) -> None:
    print(f'HSR per-food categoriser STRESS SWEEP — {sample_size} foods per CNF FoodGroup')
    print('=' * 100)

    total_sampled = sum(g['sampled'] for g in per_group.values())
    total_anomalies = sum(len(g['anomalies']) for g in per_group.values())
    print(f'Total sampled: {total_sampled} foods across {len(per_group)} groups')
    print(f'Total anomalies (assignment outside expected category set): {total_anomalies}')
    print()

    # Per-group summary table
    print(f'{"FG":>4} {"Group Name":<35} {"N":>4}  Distribution                                    Anomalies')
    print('-' * 100)
    for group_id, g in per_group.items():
        dist_str = ', '.join(f'{c}:{n}' for c, n in g['distribution'].items())
        anom_n = len(g['anomalies'])
        print(f'{group_id:>4} {g["group_name"][:35]:<35} {g["sampled"]:>4}  {dist_str:<48}  {anom_n:>3}'
              + ('  <-- review' if anom_n > 0 else ''))

    # Anomaly detail
    print()
    print('=' * 100)
    print('ANOMALY DETAIL (foods assigned to a category outside the expected set for their FoodGroup)')
    print('=' * 100)
    for group_id, g in per_group.items():
        if not g['anomalies']:
            continue
        print(f'\nFoodGroup {group_id} ({g["group_name"]}):')
        for a in g['anomalies']:
            print(f'  [{a["assigned_category"]:>2}]  CNF {a["food_id"]:>6}  {a["food_name"]}')
            print(f'         expected one of {a["expected_one_of"]}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=int, default=25,
                        help='foods to sample per CNF FoodGroup (default: 25)')
    parser.add_argument('--out', type=str,
                        default='_smoke_hsr_categorization_sweep_results.json',
                        help='output JSON path (default: alongside the script)')
    args = parser.parse_args()

    per_group = run_sweep(args.sample)
    print_report(per_group, args.sample)

    out_path = os.path.join(_HERE, args.out)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness': 'HSR per-food categoriser stress sweep',
            'sample_per_group': args.sample,
            'per_group': per_group,
            'totals': {
                'sampled': sum(g['sampled'] for g in per_group.values()),
                'anomalies': sum(len(g['anomalies']) for g in per_group.values()),
            },
        }, f, indent=2)
    print()
    print(f'Results JSON: {out_path}')
    # Exit non-zero only if anomalies are found — but treat this as a soft
    # gate; the harness is investigative, not strictly correctness-gating.
    return 0


if __name__ == '__main__':
    sys.exit(main())
