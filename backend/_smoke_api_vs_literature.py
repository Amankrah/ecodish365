"""Literature-validation smoke test for the live API.

For each (CNF food, typical serving size, published per-serving literature
value) triple, hits the API and asks two questions:

  1. Does our central value fall within an acceptable range of the literature
     central (loose, since methods differ — P&N vs IMPACT World+ in
     literature_extractions.md C15)?
  2. Does our uncertainty BAND bracket the literature value? This is the
     stronger test: a defensible band MUST contain the published value
     given documented inter-method spreads of 2-4x.

Literature anchors (all from `literature_extractions.md`):

  GW per serving (kg CO2 eq, IMPACT World+ / Stylianou 2021 SI):
    - Beef ~2.5/serving avg (GSD^2 1.4)            -> 85 g typical serving
    - Beef stew ~5.7/serving (worst-case high)     -> ~250 g serving
    - Cheese ~0.3/serving (GSD^2 1.7)              -> 28 g typical
    - Poultry ~0.3/serving (GSD^2 1.7)             -> 85 g typical
    - Fluid milk 0.47/244 g serving (cited)        -> 244 g
"""
from __future__ import annotations

import json, os, sys
_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-literature-validation'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django; django.setup()
from django.test import Client


# Each row:  (label, [(food_id, group_hint, serving_g), ...], lit_kgCO2_per_serving, lit_source)
# Food IDs are chosen for their group membership; smoke test uses real CNF FoodIDs.
LITERATURE_PANEL = [
    # Beef ~2.5 kg CO2/serving avg — Stylianou 2021 line 1754
    ('Beef, real beef-group food (~85 g serving)', 2650, 85, 2.5,
     'Stylianou 2021 SI: beef ~2.5 kg CO2/serving avg, GSD^2 1.4'),
    # Cheese ~0.3 kg CO2/serving — Stylianou 2021 line 1754 cheese/poultry GSD^2 1.7
    ('Cheese (~28 g serving)', 51, 28, 0.30,
     'Stylianou 2021 SI: cheese ~0.3 kg CO2/serving, GSD^2 1.7'),
    # Poultry ~0.3 kg CO2/serving — Stylianou 2021 line 1754
    ('Poultry, look up real poultry food', None, 85, 0.30,
     'Stylianou 2021 SI: poultry ~0.3 kg CO2/serving, GSD^2 1.7'),
    # Fluid milk: 0.47 kg CO2 / 244 g serving — Stylianou 2021 line 1659
    ('Fluid milk (244 g serving)', None, 244, 0.47,
     'Stylianou 2021: 244 g fluid-milk serving = 0.47 kg CO2 eq'),
    # Apple pie ~ 1.3 min HENI gained — corresponds to ~0.1-0.3 kg CO2 for fruit-based
    # Apple raw should be < 0.05 kg CO2 / serving (very low impact)
    # Raw apple (FoodID 1696, not the microwaved 1486 which adds cooking energy)
    ('Apple raw (~150 g serving)', 1696, 150, 0.06,
     'P&N panel F: apples mean 0.4 kg CO2/kg = 0.06 kg/150 g serving'),
]


def gsd_band(central: float, gsd_squared: float) -> tuple[float, float]:
    """95 % CI from a log-normal GSD^2 (Stylianou's distributional spec).
    GSD^2 of 1.4 -> GSD = sqrt(1.4) = 1.18; 95 % CI is central / GSD^1.96
    to central * GSD^1.96."""
    import math
    gsd = math.sqrt(gsd_squared)
    half_width = gsd ** 1.96
    return central / half_width, central * half_width


def _find_food_id(client, query: str) -> int | None:
    """Look up a CNF FoodID via the search API."""
    r = client.get(f'/api/search-food/?query={query}', secure=True)
    if r.status_code == 200:
        try:
            data = r.json()
            results = data.get('results') or data.get('foods') or []
            if results:
                return int(results[0].get('FoodID') or results[0].get('food_id'))
        except Exception:
            pass
    return None


def main() -> int:
    client = Client()
    # Find real food IDs for the rows that need lookup.
    from environmental_impact_model.src.cnf_integrator import get_cnf_integrator
    ig = get_cnf_integrator(); ig.initialize()
    fn = ig.get_dataframe('food_name')
    fg = ig.get_dataframe('food_group')

    def first_id_in_group(group_name: str, exclude_substrings=()) -> int | None:
        fgid_rows = fg[fg['FoodGroupName'] == group_name]
        if fgid_rows.empty: return None
        fgid = int(fgid_rows.iloc[0]['FoodGroupID'])
        candidates = fn[fn['FoodGroupID'] == fgid]
        for substr in exclude_substrings:
            candidates = candidates[~candidates['FoodDescription'].str.contains(substr, case=False, na=False)]
        return int(candidates.iloc[0]['FoodID']) if not candidates.empty else None

    poultry_id = first_id_in_group('Poultry Products')
    dairy_milk_candidates = fn[fn['FoodDescription'].str.contains('Milk, fluid, ', case=False, na=False) |
                                fn['FoodDescription'].str.contains('Milk, partially', case=False, na=False)]
    milk_id = int(dairy_milk_candidates.iloc[0]['FoodID']) if not dairy_milk_candidates.empty else None

    print(f"Using poultry_id={poultry_id}, milk_id={milk_id}")
    print()

    all_results = []
    n_pass = n_partial = n_fail = 0
    for i, (label, food_id, serving_g, lit_central, lit_source) in enumerate(LITERATURE_PANEL):
        # Resolve None food_ids
        if food_id is None:
            if 'oultry' in label.lower():
                food_id = poultry_id
            elif 'milk' in label.lower():
                food_id = milk_id
        if food_id is None:
            print(f"[skip] {label}: no CNF food id resolved")
            continue

        food_desc = fn[fn['FoodID'] == food_id].iloc[0]['FoodDescription'] if not fn[fn['FoodID'] == food_id].empty else "?"
        # Hit the API at the specified serving size
        body = {'foods': [{'food_id': food_id, 'quantity': serving_g}], 'user_type': 'researcher', 'enable_lca_matcher': True}
        r = client.post('/api/environmental-impact/', data=json.dumps(body), content_type='application/json', secure=True)
        if r.status_code != 200:
            print(f"[FAIL HTTP] {label}: status {r.status_code}")
            n_fail += 1
            continue
        p = r.json()
        ei = p['data']['data']['environmental_impacts']
        kcal = p['data']['meal_info']['total_calories']
        # API output is per 100 kcal; convert to per-serving for comparison with literature.
        gw_per_100kcal = ei['all_impacts'].get('Global warming', 0.0)
        gw_per_serving_central = gw_per_100kcal * (kcal / 100.0)
        bands_per_100kcal = ei['all_impacts_bands'].get('Global warming', {})
        gw_low_serving  = bands_per_100kcal.get('low',  0) * (kcal / 100.0)
        gw_high_serving = bands_per_100kcal.get('high', 0) * (kcal / 100.0)

        # Verdicts
        ratio = gw_per_serving_central / lit_central if lit_central > 0 else float('inf')
        within_band = gw_low_serving <= lit_central <= gw_high_serving
        within_2x = 0.5 <= ratio <= 2.0
        within_4x = 0.25 <= ratio <= 4.0
        if within_band and within_2x:
            verdict = 'PASS'; n_pass += 1
        elif within_band or within_4x:
            verdict = 'PARTIAL'; n_partial += 1
        else:
            verdict = 'FAIL'; n_fail += 1

        all_results.append((label, food_desc, food_id, serving_g, kcal, lit_central,
                            gw_per_serving_central, gw_low_serving, gw_high_serving,
                            ratio, within_band, within_2x, verdict))

        print(f"--- [{verdict:<7}] {label}")
        print(f"      CNF food: {food_id} {food_desc[:60]}")
        print(f"      serving: {serving_g} g  ({kcal:.0f} kcal)")
        print(f"      API per-serving GW (central): {gw_per_serving_central:.4f} kg CO2")
        print(f"      API band (per serving)      : [{gw_low_serving:.4f}, {gw_high_serving:.4f}]")
        print(f"      literature target            : {lit_central:.4f} kg CO2  ({lit_source})")
        print(f"      ratio (API / lit)            : {ratio:.2f}x")
        print(f"      band brackets literature?    : {'YES' if within_band else 'NO'}")
        print()

    print("=" * 72)
    print(f"Summary: PASS={n_pass}  PARTIAL={n_partial}  FAIL={n_fail}")
    print()
    print("Interpretation:")
    print("  PASS    : central within 2x AND band brackets literature")
    print("  PARTIAL : central within 4x OR band brackets literature (one of the two)")
    print("  FAIL    : neither (central > 4x off AND band misses literature)")
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
