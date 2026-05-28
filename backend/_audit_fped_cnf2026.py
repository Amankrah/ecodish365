"""Quick audit: CNF 2026 corpus + FPED coverage + composite attribution."""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
os.environ.setdefault('DJANGO_SECRET_KEY', 'audit')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.cnf_cache import get_api_cnf_pipeline
from heni_calculator.heni.data.composition_loader import get_composition_for_food, get_compositions

p = get_api_cnf_pipeline()
cnf = p.food_name_df[p.food_name_df['source'] == 'cnf']
comps = get_compositions()
meta = json.loads(open(_HERE + '/heni_calculator/data/cnf_heni_composition_meta.json').read())
bridge = json.loads(open(_HERE + '/heni_calculator/data/cnf_to_fndds_bridge.json').read())['_provenance']

print('CNF foods in pipeline:', len(cnf))
print('FPED composition lookup:', len(comps))
print('Bridge bridged:', bridge['cnf_bridged'], '| unbridged:', bridge.get('cnf_unbridged'))
print('No FPED row:', meta['no_fped_row_count'])

examples = [(4962, 'Pepperoni pizza'), (3941, 'Apple pie'), (4644, 'Hot dog'), (113, 'Whole milk')]
print('\nFPED g/100g (top factors):')
for fid, label in examples:
    c = get_composition_for_food(fid)
    if not c:
        print(f'  {label} ({fid}): legacy path')
        continue
    top = {k: round(v, 2) for k, v in sorted(c.items(), key=lambda x: -x[1]) if v > 0.01}
    print(f'  {label} ({fid}): {top}')
