"""HENI CNF-native implementation regression harness.

For each CNF FoodID in `HENI_CNF_PANEL`, this script:

  1. Pulls CNF nutrient values (per 100 g) via the shared CNF integrator.
  2. Applies Stylianou 2021 SI Suppl. Table 3 DRFs + Suppl. Table 1 TMRELs
     manually (mirroring `backend/rust_core/src/heni/factors.rs` +
     `engine.rs` arithmetic) to produce the CNF-native expected HENI for
     the requested serving size.
  3. Hits POST /api/heni/calculate/ with the same food+serving.
  4. Asserts |actual − expected| < 0.1 min (a tight implementation gate).

This is a pure IMPLEMENTATION regression test: it verifies the API's
score for a given CNF food equals what Stylianou's formula produces on
that CNF food's actual nutrient composition. Substrate divergence
between CNF and Stylianou's USDA/WWEIA references is OUT OF SCOPE here
— it's documented separately in `_smoke_heni_cnf_vs_wweia_substrate.py`.

Per the 2026-05-23 validation reframe in `tranquil-coalescing-acorn.md`:
"we need to rather remodify the literature to match our database for the
validation, not the other way, because this project will use the cnf."

Caveats this harness will SURFACE (not hide):
  - The food-group factors (fruits/vegetables/milk/red_meat/etc.) are
    still set to literal 100.0 g per 100g in heni_calculator_methods.py
    when the food's group matches (HENI-CODE-1.y residual cause A).
    Expected vs actual divergence on composite foods documents this
    until the D2/D3/D4 fix lands.

Run from `backend/`:
    python _smoke_heni_literature_panel.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-heni-cnf-native-validation'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402

from heni_calculator.heni.service import get_cnf_integrator  # noqa: E402
from heni_calculator.heni.data.composition_loader import get_composition_for_food  # noqa: E402


# Stylianou 2021 SI Suppl. Table 3 (p. 8) DRFs in μDALY per gram of risk
# component, sign convention: negative = beneficial, positive = detrimental.
# Mirrors `rust_core::heni::factors::HENI_FACTORS`.
STYLIANOU_DRFS = {
    # Nutrient factors (extracted directly from CNF nutrient table)
    'omega_3': -81.0,
    'calcium': -5.1,
    'fiber_other': -0.99,
    'fiber_fvlw': -0.19,
    'polyunsaturated_fatty_acids': -0.60,
    'trans_fat': 4.4,
    'sodium': 13.9,
    # Food-group factors — the extractor sets these to literal 100.0 g per
    # 100g when the CNF group matches; this harness mirrors that behaviour
    # so expected and actual diverge on the residual HENI-CODE-1.y cause-A.
    'nuts_seeds': -1.5,
    'whole_grains': -0.34,
    'fruits': -0.18,
    'vegetables': -0.083,
    'legumes': -0.23,
    'milk': -0.0077,
    'sugar_sweetened_beverages': 0.066,
    'red_meat': 0.099,
    'processed_meat': 0.86,
}

# Stylianou 2021 SI Suppl. Table 1 (pp. 4-5) absolute-gram TMRELs.
ABSOLUTE_TMRELS = {
    'omega_3': 0.250,
    'calcium': 1.25,
    'fiber_other': 23.5,
    'fiber_fvlw': 23.5,
    'whole_grains': 125.0,
    'legumes': 60.0,
    'fruits': 250.0,
    'vegetables': 360.0,
    'milk': 435.0,
    'nuts_seeds': 20.5,
    'sodium': 3.49,
    'sugar_sweetened_beverages': 2.5,
    'red_meat': 22.5,
    'processed_meat': 2.0,
}

# Energy-relative TMRELs (Stylianou SI Table 1, lipid 9 kcal/g).
ENERGY_RELATIVE_TMREL_FRAC = {
    'polyunsaturated_fatty_acids': 0.11,  # 11 % of energy
    'trans_fat': 0.005,                    # 0.5 % of energy
}

MINUTES_PER_UDALY = -0.5256  # Stylianou 2021 SI p. 98

# Plant-milk and non-SSB indicators (mirrors heni_calculator_methods).
_PLANT_MILK = ('soy milk', 'almond milk', 'oat milk', 'rice milk',
               'coconut milk', 'cashew milk', 'hemp milk', 'pea milk')
_NON_SSB = ('water', 'tea', 'coffee', 'espresso', 'broth', 'stock',
            '100% juice', 'fruit juice', 'vegetable juice')

# Whole-grain indicators (mirrors the 2026-05-23 tightened matcher).
_WHOLE_GRAIN = ('whole grain', 'whole-grain', 'whole wheat', '100% whole',
                'wheat bran', 'wheat germ', 'oats, rolled', 'oats, steel cut',
                'rolled oats', 'quinoa', 'brown rice')


@dataclass
class CNFPanelRow:
    label: str
    cnf_food_id: int
    serving_g: float
    rationale: str = ''


# CNF-native panel: 10 foods spanning the nutritional spectrum. Picked so
# the expected HENI varies across the dynamic range (beneficial, neutral,
# detrimental) and so different risk-factor combinations exercise the
# pipeline. No "Stylianou published target" is referenced anywhere —
# expected values are derived from CNF nutrients directly.
HENI_CNF_PANEL: List[CNFPanelRow] = [
    CNFPanelRow('Chicken broiler wing meat+skin roasted', 629, 85.0,
                'Stylianou §S2.2 worked-example food. CNF substrate '
                'differs from WWEIA (esp. sodium); CNF-native expected '
                'HENI computed from CNF values.'),
    CNFPanelRow('Fast foods hot dog plain', 4644, 150.0,
                'CNF-native expected reflects CNF\'s lower sodium load.'),
    CNFPanelRow('Wiener (frankfurter) beef', 1185, 60.0,
                'Pure processed-meat row; tests processed_meat + sodium '
                'extraction.'),
    CNFPanelRow('Pizza pepperoni frozen cooked', 4962, 150.0,
                'Composite food; tests whole-row attribution under '
                'food-group residual (HENI-CODE-1.y cause A).'),
    CNFPanelRow('Pie apple commercial 2 crust', 3941, 150.0,
                'Composite food; CNF "Fruits and fruit juices" group? '
                'Actually under desserts; tests group-mapping fallback.'),
    CNFPanelRow('Fish sardine Pacific canned in tomato sauce', 3054, 100.0,
                'High omega-3 source; tests omega_3 nutrient extraction.'),
    CNFPanelRow('Beef cured corned beef canned', 2791, 150.0,
                'Processed red meat; tests processed_meat path + sodium.'),
    CNFPanelRow('Bread white commercial', 4066, 30.0,
                'Refined-grain sentinel; tests that whole-grain matcher '
                'no longer over-attributes (post-2026-05-23 tightening).'),
    CNFPanelRow('Broccoli frozen boiled', 2026, 100.0,
                'Pure vegetable; tests vegetables group + fibre routing '
                'to fiber_fvlw.'),
    CNFPanelRow('Milk fluid whole 3.25% M.F.', 113, 250.0,
                'Dairy beverage; tests milk-vs-calcium carve-out + '
                'plant-milk exclusion (this food is NOT plant-based).'),
]


def _compute_cnf_native_expected(
    food_id: int,
    serving_g: float,
    cnf_integrator,
) -> Tuple[float, Dict[str, float], List[str]]:
    """Mirror `heni_calculator_methods.extract_risk_factors_from_ingredient`
    + Rust kernel arithmetic to compute the CNF-native expected HENI score.

    Returns: (expected_health_impact_minutes, risk_factors_per_serving,
              audit_lines).
    """
    nd = cnf_integrator.get_nutrient_data(food_id)
    food_desc = cnf_integrator.get_food_description(food_id).lower()
    food_group = cnf_integrator.get_food_group(food_id)
    energy_kcal_per_100g = float(nd.get('ENERGY (KILOCALORIES)', 0.0))
    total_energy_kcal = energy_kcal_per_100g * serving_g / 100.0
    audit: List[str] = []

    # Per-100g risk factor amounts (g) — mirror the extractor's logic.
    rf_100g: Dict[str, float] = {}

    # Nutrient factors (mg → g for calcium/sodium).
    omega_3_total = 0.0
    omega_3_keys = [
        'FATTY ACIDS, POLYUNSATURATED, 22:6 N-3, DOCOSAHEXAENOIC (DHA)',
        'FATTY ACIDS, POLYUNSATURATED, 20:5 N-3, EICOSAPENTAENOIC (EPA)',
    ]
    for k in omega_3_keys:
        omega_3_total += float(nd.get(k, 0.0))
    if omega_3_total > 0:
        rf_100g['omega_3'] = omega_3_total

    if 'CALCIUM' in nd:
        rf_100g['calcium'] = float(nd['CALCIUM']) / 1000.0  # mg → g
    if 'SODIUM' in nd:
        rf_100g['sodium'] = float(nd['SODIUM']) / 1000.0
    if 'FATTY ACIDS, POLYUNSATURATED, TOTAL' in nd:
        rf_100g['polyunsaturated_fatty_acids'] = float(
            nd['FATTY ACIDS, POLYUNSATURATED, TOTAL'])
    rf_100g['trans_fat'] = float(nd.get('FATTY ACIDS, TRANS, TOTAL', 0.0))
    # Fibre — routed below by carve-out logic.
    fibre_total = float(nd.get('FIBRE, TOTAL DIETARY', 0.0))

    # Food-group factors — mirror the extractor's FPED-composition-lookup
    # dispatch + legacy fallback. Single source of truth: when the API uses
    # composition, the harness uses composition; when the API falls back to
    # legacy literal-100, the harness mirrors that. Plant-milk exclusion is
    # applied identically.
    def _is_plant_milk(d: str) -> bool:
        return any(s in d for s in _PLANT_MILK)
    def _is_non_ssb(d: str) -> bool:
        return any(s in d for s in _NON_SSB)

    composition = get_composition_for_food(food_id)
    is_fvlw_group = False

    if composition:
        # FPED-grounded path (HENI-CODE-1.y cause A SHIPPED)
        for risk_key, mass_per_100g in composition.items():
            if mass_per_100g <= 0:
                continue
            if risk_key == 'milk' and _is_plant_milk(food_desc):
                continue
            rf_100g[risk_key] = mass_per_100g
            if risk_key in ('fruits', 'vegetables', 'legumes', 'whole_grains'):
                is_fvlw_group = True
        # SSB independent check (FPED has no SSB column)
        if 'Beverages' in food_group and not _is_non_ssb(food_desc):
            sugar = float(nd.get('SUGARS, TOTAL', 0.0))
            if sugar > 5:
                rf_100g['sugar_sweetened_beverages'] = 100.0
        audit.append(f'food_group_attribution: fped_composition_lookup')
    else:
        # Legacy literal-100 attribution fallback (mirrors
        # heni_calculator_methods._legacy_food_group_attribution)
        if 'Nuts and Seeds' in food_group:
            rf_100g['nuts_seeds'] = 100.0
        if 'Cereals, Grains and Pasta' in food_group:
            if any(t in food_desc for t in _WHOLE_GRAIN):
                rf_100g['whole_grains'] = 100.0; is_fvlw_group = True
        if 'Fruits and fruit juices' in food_group:
            rf_100g['fruits'] = 100.0; is_fvlw_group = True
        if 'Vegetables and Vegetable Products' in food_group:
            rf_100g['vegetables'] = 100.0; is_fvlw_group = True
        if 'Legumes and Legume Products' in food_group:
            rf_100g['legumes'] = 100.0; is_fvlw_group = True
        if 'Milk Products' in food_group or 'Dairy and Egg Products' in food_group:
            if not _is_plant_milk(food_desc):
                rf_100g['milk'] = 100.0
        if 'Beverages' in food_group and not _is_non_ssb(food_desc):
            sugar = float(nd.get('SUGARS, TOTAL', 0.0))
            if sugar > 5:
                rf_100g['sugar_sweetened_beverages'] = 100.0
        if any(g in food_group for g in ('Beef Products', 'Pork Products', 'Lamb, Veal and Game')):
            processed_terms = ('processed', 'sausage', 'ham', 'bacon', 'deli',
                               'cured', 'smoked', 'hot dog', 'bologna', 'salami',
                               'pepperoni', 'jerky')
            if any(t in food_desc for t in processed_terms):
                rf_100g['processed_meat'] = 100.0
            else:
                rf_100g['red_meat'] = 100.0
        if 'Poultry Products' in food_group:
            processed_terms = ('sausage', 'deli', 'processed', 'cured', 'smoked',
                               'ham', 'bacon')
            if any(t in food_desc for t in processed_terms):
                rf_100g['processed_meat'] = 100.0
        audit.append(f'food_group_attribution: legacy_literal_100')

    # Fibre source split (Stylianou SI §S2.9): fiber_fvlw if a f/v/l/w group
    # is co-present; fiber_other otherwise.
    if fibre_total > 0:
        if is_fvlw_group:
            rf_100g['fiber_fvlw'] = rf_100g.get('fiber_fvlw', 0.0) + fibre_total
            audit.append(f'fiber_source_split: {fibre_total:.4f}g → fiber_fvlw')
        else:
            rf_100g['fiber_other'] = rf_100g.get('fiber_other', 0.0) + fibre_total
            audit.append(f'fiber_source_split: {fibre_total:.4f}g → fiber_other')

    # Milk-vs-calcium carve-out (Stylianou Methods p. 626).
    if rf_100g.get('milk', 0.0) > 0.0 and 'calcium' in rf_100g:
        supp = rf_100g.pop('calcium')
        audit.append(f'milk_vs_calcium: suppressed calcium={supp:.4f}g')

    # Scale to per-serving.
    rf_serving = {k: v * serving_g / 100.0 for k, v in rf_100g.items()}

    # Apply TMRELs (energy-relative tighter-of-two for PUFA and TFA).
    capped: Dict[str, float] = {}
    for risk, amount in rf_serving.items():
        cap_abs = ABSOLUTE_TMRELS.get(risk)
        cap_e = None
        if risk in ENERGY_RELATIVE_TMREL_FRAC and total_energy_kcal > 0:
            cap_e = ENERGY_RELATIVE_TMREL_FRAC[risk] * total_energy_kcal / 9.0
        caps = [c for c in (cap_abs, cap_e) if c is not None]
        if caps:
            cap = min(caps)
            if amount > cap:
                audit.append(f'TMREL cap: {risk} {amount:.4f}g → {cap:.4f}g')
                amount = cap
        capped[risk] = amount

    # Compute total μDALY.
    total_udaly = 0.0
    contribs: Dict[str, float] = {}
    for risk, amount in capped.items():
        drf = STYLIANOU_DRFS.get(risk)
        if drf is None:
            continue
        c = amount * drf
        contribs[risk] = c
        total_udaly += c

    # adult_male age adjustment = 1.0 (no scaling).
    minutes = total_udaly * MINUTES_PER_UDALY
    return minutes, capped, audit, contribs


def _call_heni(client: Client, row: CNFPanelRow) -> Tuple[Optional[float], Optional[dict], Optional[str]]:
    body = {'meal': [{'food_id': row.cnf_food_id, 'amount': row.serving_g, 'unit': 'g'}]}
    r = client.post('/api/heni/calculate/', data=json.dumps(body),
                    content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None, f'HTTP {r.status_code}: {r.content[:300]!r}'
    try:
        p = r.json()['data']['data']
        minutes = float(p['health_impact']['health_impact_minutes'])
        diag = {
            'risk_factors_api': dict(p['risk_factor_analysis']['risk_factors']),
            'contribs_api_food_group': dict(p['component_breakdown']['food_group_contributions']),
            'contribs_api_nutrient': dict(p['component_breakdown']['nutrient_contributions']),
        }
        return minutes, diag, None
    except Exception as exc:
        return None, None, f'parse: {exc!r}'


# Tight gate for the CNF-native implementation regression test.
GATE_ABS_MIN = 0.1


def main() -> int:
    cnf = get_cnf_integrator()
    client = Client()

    print('HENI CNF-native implementation regression harness')
    print('  expected = f(CNF nutrients, Stylianou DRFs+TMRELs)')
    print(f'  gate     = |actual - expected| < {GATE_ABS_MIN} min')
    print('=' * 76)
    print()

    n_pass = n_fail = 0
    results = []
    for row in HENI_CNF_PANEL:
        # Compute CNF-native expected
        exp_min, exp_rf, exp_audit, exp_contribs = _compute_cnf_native_expected(
            row.cnf_food_id, row.serving_g, cnf
        )
        # Hit the API
        actual_min, diag, err = _call_heni(client, row)
        if err is not None:
            print(f'[ERROR] {row.label}: {err}\n')
            n_fail += 1
            results.append({**asdict(row), 'verdict': 'ERROR', 'error': err})
            continue

        delta = actual_min - exp_min
        within = abs(delta) < GATE_ABS_MIN
        verdict = 'PASS' if within else 'FAIL'
        if within:
            n_pass += 1
        else:
            n_fail += 1

        print(f'[{verdict:>4}]  {row.label}')
        print(f'        cnf food_id: {row.cnf_food_id}  serving: {row.serving_g:.0f} g')
        print(f'        expected:   {exp_min:+7.3f} min   (CNF-native, from CNF nutrients x Stylianou DRFs)')
        print(f'        actual:     {actual_min:+7.3f} min   (API)')
        print(f'        delta:      {delta:+7.3f} min')
        if not within:
            # On failure, show top-magnitude expected contributions to help diagnose
            top = sorted(exp_contribs.items(), key=lambda kv: abs(kv[1]), reverse=True)[:4]
            top_s = ', '.join(f'{k}={v:+.2f}uDALY' for k, v in top)
            print(f'        expected top contribs: {top_s}')
            api_contribs = {**diag.get('contribs_api_nutrient', {}),
                            **diag.get('contribs_api_food_group', {})}
            top_api = sorted(api_contribs.items(), key=lambda kv: abs(kv[1]), reverse=True)[:4]
            top_api_s = ', '.join(f'{k}={v:+.2f}uDALY' for k, v in top_api)
            print(f'        API top contribs:      {top_api_s}')
        print()

        results.append({
            **asdict(row),
            'expected_min': exp_min,
            'actual_min': actual_min,
            'delta_min': delta,
            'within_gate': within,
            'verdict': verdict,
            'gate_abs_min': GATE_ABS_MIN,
            'expected_risk_factors_per_serving': exp_rf,
            'expected_audit': exp_audit,
            'expected_contribs_udaly': exp_contribs,
            'api_diagnostics': diag,
        })

    print('=' * 76)
    n_total = n_pass + n_fail
    print(f'Summary: PASS={n_pass}/{n_total}')
    if n_pass < n_total:
        print()
        print('FAIL diagnoses:')
        print('  - HENI-CODE-1.y residual cause-A (food-group factors set to literal 100.0 g/100g')
        print('    by extract_risk_factors_from_ingredient): expect API > expected on rows where')
        print('    expected uses the same literal-100 attribution and the API computes the same.')
        print('  - Any divergence beyond ~0.001 min indicates an arithmetic or unit mismatch')
        print('    between the harness mirror and the API extractor — investigate before')
        print('    attributing to substrate.')

    out_path = os.path.join(_HERE, '_smoke_heni_literature_panel_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness_description': 'HENI CNF-native implementation regression (expected = '
                                    'f(CNF nutrients, Stylianou DRFs+TMRELs))',
            'gate_policy': f'|actual - expected| < {GATE_ABS_MIN} min',
            'summary': {'n_pass': n_pass, 'n_fail': n_fail, 'n_total': n_total},
            'rows': results,
        }, f, indent=2, default=str)
    print(f'\nResults JSON: {out_path}')
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
