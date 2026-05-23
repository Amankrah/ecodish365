"""One-shot discovery helper to find CNF food_id candidates for the HENI
literature panel (Stylianou et al. 2021 Fig 2-4 + SI worked examples).

Run once to see candidates, then hand-curate the picks into
`_smoke_heni_literature_panel.py`'s `HENI_LITERATURE_PANEL` fixture.

For each Stylianou reference food, prints up to 5 CNF candidates by
sub-string match against `FoodDescription`. The reviewer then picks the
best-matched food_id and records the rationale in the panel fixture.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-heni-discovery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from environmental_impact_model.src.cnf_integrator import get_cnf_integrator  # noqa: E402


# Each row: (label, list of search substrings — first hit wins).
# Use multiple substrings to broaden the search; each substring is tried
# independently and the top 5 unique matches across all substrings are
# printed.
SEARCH_TARGETS = [
    ('Chicken wing (Stylianou §S2.2 worked example, 85 g)',
     ['Chicken, wing, meat and skin', 'chicken wing']),
    ('Frankfurter sandwich (Stylianou Fig 2-4 categorical median)',
     ['frankfurter', 'hot dog', 'hotdog']),
    ('Beef hotdog on bun (Stylianou Fig 4 extremum)',
     ['frankfurter, beef', 'beef frankfurter', 'hot dog, beef']),
    ('Vegetable pizza (Stylianou Fig 4)',
     ['pizza, vegetable', 'pizza, with vegetables']),
    ('Apple pie (Stylianou Fig 4)',
     ['pie, apple', 'apple pie']),
    ('Sardines in tomato sauce (Stylianou Fig 4 extremum +82 min)',
     ['sardine', 'sardines, canned']),
    ('Corned beef with tomato sauce (Stylianou Fig 4 extremum -71 min)',
     ['corned beef', 'beef, cured, corned']),
    ('White bread (sentinel, low-DRF dynamic-range anchor)',
     ['bread, white', 'bread, white, commercial']),
]


def main() -> int:
    ig = get_cnf_integrator()
    ig.initialize()
    fn = ig.get_dataframe('food_name')

    print(f"CNF FoodName table loaded: {len(fn):,} rows")
    print()

    for label, substrings in SEARCH_TARGETS:
        print(f"=== {label}")
        seen: set[int] = set()
        for substr in substrings:
            hits = fn[fn['FoodDescription'].str.contains(substr, case=False, na=False)]
            for _, row in hits.head(8).iterrows():
                fid = int(row['FoodID'])
                if fid in seen:
                    continue
                seen.add(fid)
                desc = str(row['FoodDescription'])
                print(f"   {fid:>5}  {desc[:90]}")
                if len(seen) >= 5:
                    break
            if len(seen) >= 5:
                break
        if not seen:
            print("   (no matches)")
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
