"""Scenario S2 — EF-vs-ReCiPe per-category divergence panel.

Operationalises the manuscript §4.2 claim. For each food in a representative
CNF panel, hits the live API with matcher ON, extracts:
  - The ReCiPe 2016 H side: the 3 v1 consumed midpoints + the 5 matcher-overlaid
    EF-direct keys (climate change + 3 sub-cols + stratospheric ozone).
  - The EF 3.1 side: the full 20-indicator block from the per-meal
    `recipe2016_h_ef31_sensitivity` audit field.

Computes per-category divergence in 3 partitions:

  A. DIRECTLY COMPARABLE (5 pairs, same units, same family):
     EF "Changement climatique"          ⇄ ReCiPe "Global warming"        (kg CO2 eq)
     EF "...émissions fossiles"          ⇄ ReCiPe "Global warming (fossil)"
     EF "...émissions biogéniques"       ⇄ ReCiPe "Global warming (biogenic)"
     EF "...changement d'affectation..." ⇄ ReCiPe "Global warming (LUC)"
     EF "Appauvrissement de la couche d'ozone" ⇄ ReCiPe "Stratospheric ozone depletion"
       (both kg CFC11 eq)
     → numerical ratio + log-ratio (Bland-Altman x = log mean, y = log ratio).

  B. UNIT-INCOMPATIBLE (14 EF cols vs ReCiPe categories with different units):
     EF "Particules fines" (disease inc./kg) ⇄ ReCiPe "Fine particulate matter formation" (kg PM2.5 eq)
     ...etc. Report both numerically; flag as "unit-incompatible" — no
     coercion. The 14 categories from §3.2.

  C. EF SCORE-ONLY:
     EF "Score unique EF 3.1" — no ReCiPe equivalent (PEF single-score). Tabulate alone.

Outputs:
  - JSON artefact at `backend/environmental_impact_model/data/s2_divergence_panel.json`
    with per-food per-category data + per-food-group aggregation.
  - Markdown summary table to stdout.
"""
from __future__ import annotations

import json, math, os, sys, statistics
from collections import defaultdict

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-s2-divergence'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django; django.setup()
from django.test import Client


# --- The five directly-comparable EF↔ReCiPe pairs (same units). ---
DIRECT_PAIRS = [
    ('Changement climatique',                                           'Global warming',                'kg CO2 eq'),
    ('Changement climatique - émissions fossiles',                      'Global warming (fossil)',       'kg CO2 eq'),
    ('Changement climatique - émissions biogéniques',                   'Global warming (biogenic)',     'kg CO2 eq'),
    ("Changement climatique - émissions liées au changement d'affectation des sols",
                                                                        'Global warming (LUC)',          'kg CO2 eq'),
    ("Appauvrissement de la couche d'ozone",                            'Stratospheric ozone depletion', 'kg CFC11 eq'),
]

# --- The 14 unit-incompatible EF↔ReCiPe cross-mappings (different units). ---
UNIT_INCOMPATIBLE_PAIRS = [
    ('Particules fines',                                                'Fine particulate matter formation', 'EF disease inc./kg  vs  ReCiPe kg PM2.5 eq'),
    ('Acidification terrestre et eaux douces',                          'Terrestrial acidification',         'EF mol H+ eq        vs  ReCiPe kg SO2 eq'),
    ('Eutrophisation eaux douces',                                      'Freshwater eutrophication',         'EF kg P eq (different fate model)'),
    ('Eutrophisation marine',                                           'Marine eutrophication',             'EF kg N eq (different fate model)'),
    ('Eutrophisation terrestre',                                        '(no ReCiPe equivalent)',            'EF mol N eq        no ReCiPe slot'),
    ("Écotoxicité pour écosystèmes aquatiques d'eau douce",             'Freshwater ecotoxicity (+terr +marine in ReCiPe)', 'EF CTUe (FW only)  vs  ReCiPe 3 ecotox cats'),
    ('Utilisation du sol',                                              'Land use',                          'EF Pt (LANCA score) vs  ReCiPe m2a crop-eq'),
    ('Épuisement des ressources eau',                                   'Water consumption',                 'EF m3 deprivation (AWARE) vs ReCiPe m3 blue'),
    ('Épuisement des ressources énergétiques',                          '(rolled into Fossil resource scarcity)', 'EF MJ  no ReCiPe slot'),
    ('Épuisement des ressources minéraux',                              'Mineral resource scarcity',         'EF kg Sb eq        vs  ReCiPe kg Cu eq'),
    ('Rayonnements ionisants',                                          'Ionizing radiation',                'EF kBq U-235 eq    vs  ReCiPe kBq Co-60 eq'),
    ("Formation photochimique d'ozone",                                 'Ozone formation (HH + Terrestrial in ReCiPe)', 'EF kg NMVOC eq vs ReCiPe 2 ozone cats'),
    ('Effets toxicologiques sur la santé humaine : substances cancérogènes',
                                                                        'Human carcinogenic toxicity',       'EF CTUh           vs  ReCiPe kg 1,4-DCB eq'),
    ('Effets toxicologiques sur la santé humaine : substances non-cancérogènes',
                                                                        'Human non-carcinogenic toxicity',   'EF CTUh           vs  ReCiPe kg 1,4-DCB eq'),
]

# Panel of CNF foods spanning multiple FoodGroupName buckets. Each entry:
# (food_id, label, serving_g, expected_food_group).
PANEL = [
    (7,    'Beef pot roast w/ veg',  150, 'Mixed Dishes'),
    (2650, 'Beef brain raw',         100, 'Beef Products'),
    (1755, 'Pork shoulder raw',      150, 'Pork Products'),
    (555,  'Chicken broiler raw',    150, 'Poultry Products'),
    (461,  'Fish oil salmon',         30, 'Fats and Oils'),
    (51,   'Processed cheddar',       50, 'Dairy and Egg Products'),
    (61,   'Milk 2% fluid',          244, 'Dairy and Egg Products'),
    (2380, 'Carrot raw',             100, 'Vegetables and Vegetable Products'),
    (1696, 'Apple raw with skin',    150, 'Fruits and fruit juices'),
    (219,  'Barley grain',           100, 'Cereals, Grains and Pasta'),
]


def safe_ratio(ef_val, recipe_val):
    if ef_val is None or recipe_val is None: return None
    if recipe_val == 0: return float('inf') if ef_val != 0 else None
    return ef_val / recipe_val


def safe_log10_ratio(ef_val, recipe_val):
    r = safe_ratio(ef_val, recipe_val)
    if r is None or r <= 0 or not math.isfinite(r): return None
    return math.log10(r)


def main() -> int:
    client = Client()
    out: dict = {'per_food': [], 'aggregated_per_group': {}, 'aggregated_overall': {}}

    print("Scenario S2 — EF-vs-ReCiPe per-category divergence panel")
    print(f"Panel: {len(PANEL)} CNF foods\n")

    for food_id, label, serving_g, expected_group in PANEL:
        body = {
            'foods': [{'food_id': food_id, 'quantity': serving_g}],
            'user_type': 'researcher',
            'enable_lca_matcher': True,
        }
        r = client.post('/api/environmental-impact/', data=json.dumps(body),
                        content_type='application/json', secure=True)
        if r.status_code != 200:
            print(f"[skip] food_id={food_id} HTTP {r.status_code}")
            continue
        p = r.json()
        ei = p['data']['data']['environmental_impacts']
        ef_block = ei.get('recipe2016_h_ef31_sensitivity') or {}
        ef_per_meal = ef_block.get('ef31_aggregated_per_meal') or {}
        recipe_per_100kcal = ei.get('all_impacts') or {}
        kcal = p['data']['meal_info']['total_calories']

        # Convert ReCiPe per-100-kcal back to per-meal for like-for-like comparison
        # with EF (which is per-meal in the sensitivity block).
        recipe_per_meal = {k: v * (kcal / 100.0) for k, v in recipe_per_100kcal.items()}

        # For matcher-overlaid extra keys (e.g. 'Global warming (fossil)'),
        # those live in the matcher_decisions block per-food, not in
        # all_impacts. The sensitivity block doesn't expose them aggregated;
        # we approximate by reading from the matcher_decisions[0]'s
        # midpoint_factors when matched=True.
        # Matcher-supplied values for keys NOT in v1's consumed vector live in
        # matcher_decisions[].midpoint_factors. The v1 trim drops Stratospheric
        # ozone depletion AND the 3 climate sub-cols from all_impacts, so we
        # have to read them from there. Only Global warming is in all_impacts.
        ds = ei.get('lca_matcher_decisions') or []
        matched = [d for d in ds if d.get('matched')]
        recipe_subkeys_per_meal: dict = {}
        for d in matched:
            mf = d.get('midpoint_factors') or {}
            for k, v in mf.items():
                if k == 'Global warming':
                    continue  # already in recipe_per_meal (the only consumed midpoint among the 5 matcher keys)
                if isinstance(v, (int, float)):
                    recipe_subkeys_per_meal[k] = recipe_subkeys_per_meal.get(k, 0.0) + v * (serving_g / 100.0)

        # Build rows for the 3 partitions
        direct_rows = []
        for ef_col, recipe_key, unit in DIRECT_PAIRS:
            ef_val = ef_per_meal.get(ef_col)
            recipe_val = (recipe_per_meal.get(recipe_key)
                          if recipe_key in recipe_per_meal
                          else recipe_subkeys_per_meal.get(recipe_key))
            direct_rows.append({
                'ef_col': ef_col,
                'recipe_key': recipe_key,
                'unit': unit,
                'ef_value': ef_val,
                'recipe_value': recipe_val,
                'ratio_ef_over_recipe': safe_ratio(ef_val, recipe_val),
                'log10_ratio': safe_log10_ratio(ef_val, recipe_val),
            })

        unit_incompat_rows = []
        for ef_col, recipe_key, unit_note in UNIT_INCOMPATIBLE_PAIRS:
            unit_incompat_rows.append({
                'ef_col': ef_col,
                'recipe_key': recipe_key,
                'unit_note': unit_note,
                'ef_value': ef_per_meal.get(ef_col),
                'recipe_value': recipe_per_meal.get(recipe_key) if recipe_key in recipe_per_meal else None,
            })

        food_record = {
            'food_id': food_id,
            'label': label,
            'expected_group': expected_group,
            'serving_g': serving_g,
            'kcal': kcal,
            'direct_pairs': direct_rows,
            'unit_incompatible_pairs': unit_incompat_rows,
            'ef_single_score_per_meal': ef_per_meal.get('Score unique EF 3.1'),
        }
        out['per_food'].append(food_record)

        # Print per-food summary line for the directly-comparable pairs.
        # Use 'NA' for missing values (foods where matcher didn't fire or
        # Agribalyse row has no value for that EF column).
        def fmt(v, spec='.3g'):
            if v is None or not isinstance(v, (int, float)):
                return 'NA'
            try:
                return format(v, spec)
            except Exception:
                return str(v)
        gw_pair = direct_rows[0]
        oz_pair = direct_rows[4]
        print(f"food_id={food_id:>5}  {label:<28}  kcal={kcal:>6.0f}  "
              f"GW: EF={fmt(gw_pair['ef_value'], '.4g')} ReCiPe={fmt(gw_pair['recipe_value'], '.4g')} "
              f"ratio={fmt(gw_pair['ratio_ef_over_recipe'], '.2f')}  |  "
              f"OD: EF={fmt(oz_pair['ef_value'])} ReCiPe={fmt(oz_pair['recipe_value'])} "
              f"ratio={fmt(oz_pair['ratio_ef_over_recipe'], '.2f')}")

    # ---- Aggregate per-food-group (median log-ratio across foods) ---------
    print()
    print("=" * 100)
    print("Per-group aggregated divergence (median log10 ratio across foods)")
    print("=" * 100)

    by_group: dict = defaultdict(lambda: defaultdict(list))
    for fr in out['per_food']:
        grp = fr['expected_group']
        for dp in fr['direct_pairs']:
            lr = dp['log10_ratio']
            if lr is not None and math.isfinite(lr):
                by_group[grp][dp['recipe_key']].append(lr)

    for grp, cat_dict in sorted(by_group.items()):
        n_foods = len([fr for fr in out['per_food'] if fr['expected_group'] == grp])
        print(f"\n  {grp}  (n={n_foods})")
        out['aggregated_per_group'][grp] = {}
        for cat in sorted(cat_dict.keys()):
            vals = cat_dict[cat]
            med = statistics.median(vals)
            ratio = 10 ** med
            tag = ('EF > ReCiPe' if ratio > 1.05 else
                   ('EF ~= ReCiPe (transfer-identity)' if 0.95 <= ratio <= 1.05 else 'EF < ReCiPe'))
            print(f"    {cat:<35}  median_ratio={ratio:6.2f}x   ({tag})")
            out['aggregated_per_group'][grp][cat] = {
                'median_log10_ratio': med,
                'median_ratio': ratio,
                'n': len(vals),
                'tag': tag,
            }

    # ---- Aggregate overall (across all foods) -----------------------------
    print()
    print("=" * 100)
    print("Overall divergence (median log10 ratio across the full panel)")
    print("=" * 100)
    overall: dict = defaultdict(list)
    for fr in out['per_food']:
        for dp in fr['direct_pairs']:
            lr = dp['log10_ratio']
            if lr is not None and math.isfinite(lr):
                overall[dp['recipe_key']].append(lr)
    for cat in sorted(overall.keys()):
        vals = overall[cat]
        med = statistics.median(vals)
        ratio = 10 ** med
        print(f"  {cat:<35}  n={len(vals):>2}  median_ratio={ratio:6.2f}x")
        out['aggregated_overall'][cat] = {
            'median_log10_ratio': med,
            'median_ratio': ratio,
            'n': len(vals),
        }

    # ---- Save artefact -----------------------------------------------------
    artefact_path = os.path.join(
        _HERE, 'environmental_impact_model', 'data', 's2_divergence_panel.json'
    )
    with open(artefact_path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\nArtefact saved: {artefact_path}")

    # ---- Unit-incompatible categories: report data presence only ----------
    print()
    print("=" * 100)
    print("Unit-incompatible categories (numerical comparison NOT performed)")
    print("=" * 100)
    print("These 14 EF columns have no unit-compatible ReCiPe equivalent in the")
    print("current open-release pipeline. Both values are saved to the JSON")
    print("artefact for SI tabulation; numerical ratios are intentionally omitted")
    print("to honour section 3.2's 'no silent unit coercion across methods' policy.")
    print()
    print("Resolution requires either:")
    print("  - TODO-CODE-LCA-2 (licensed AGRIBALYSE-LCI re-scored under ReCiPe CFs), or")
    print("  - Raw SimaPro outputs from Dekker et al. 2020 (see section 7.5).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
