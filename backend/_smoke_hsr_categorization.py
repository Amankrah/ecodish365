"""HSR categorisation smoke + stress test (2026-05-23).

HSRAC v9 assigns each food to one of 6 categories — 1 (Non-dairy beverages),
1D (Dairy beverages), 2 (General foods), 2D (Other dairy foods), 3 (Oils and
spreads), 3D (Cheese) — and that category drives which baseline/modifying
threshold table is used. A misclassification yields the wrong star rating, so
the categorizer is the highest-leverage component in the HSR pipeline.

This harness runs three panels against `/api/hsr/calculate/`:

  PANEL A — canonical, single-food.
    20 CNF foods that obviously belong to one of the 6 HSRAC v9 categories
    per the HSRAC v9 Implementation Guide (10 Dec 2025) Introduction. Per-row
    assertion: rating.category matches expected, food.category_confidence ≥
    0.7 (the auto-assigned floor in HSRCategorizer is 0.9 for the rule-based
    path; values below 0.7 indicate fallback or LLM disagreement).

  PANEL B — adversarial, single-food.
    8 CNF foods that probe known edge cases in the keyword-override rules:
    foods whose name contains BOTH "cheese" and "spread"; eggs sitting in the
    Dairy food group (CNF FoodGroup 1); a non-dairy-flavour milkshake
    nominally in the Beverages group; etc. Per-row assertion: documents
    observed category and flags surprises.

  PANEL C — meal-level (multi-food).
    8 multi-food meals. Asserts the per-meal `MealCategorizer` behaviour and
    captures meal_categorization.category_confidence (which several earlier
    probes showed returning 0.0 — see notes in the result JSON).

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_hsr_categorization.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-hsr-categorization'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402


# --- Panels --------------------------------------------------------------

@dataclass
class FoodProbe:
    food_id: int
    name: str
    expected_category: str
    min_confidence: float
    gloss: str


# PANEL A — canonical foods per HSRAC v9 category. Each row should hit its
# expected category with confidence ≥ 0.7.
PANEL_A_CANONICAL: List[FoodProbe] = [
    # Category 1 — Non-dairy beverages
    FoodProbe(1495, 'Apple juice, canned',                '1',  0.7, 'fruit juice (FG9 → 1 via beverage-keyword override)'),
    FoodProbe(1619, 'Orange juice, raw',                  '1',  0.7, 'fruit juice (FG9 → 1)'),
    FoodProbe(2835, 'Beer, light (4% ABV)',               '1',  0.7, 'alcoholic non-dairy beverage (FG14)'),

    # Category 1D — Dairy beverages
    FoodProbe(113,  'Milk, whole (3.25% MF)',             '1D', 0.7, 'pure milk (FG1 + dairy-beverage keyword)'),
    FoodProbe(61,   'Milk, partly skimmed (2% MF)',       '1D', 0.7, 'partly skimmed milk (FG1)'),
    FoodProbe(69,   'Milk, chocolate, whole',             '1D', 0.7, 'flavoured dairy beverage (FG1)'),

    # Category 2 — General foods
    FoodProbe(1696, 'Apple, raw, with skin',              '2',  0.7, 'fresh fruit (FG9)'),
    FoodProbe(4066, 'Bread, white, commercial',           '2',  0.7, 'baked grain (FG18)'),
    FoodProbe(4964, 'Beef stew, canned',                  '2',  0.7, 'mixed dish (FG22)'),
    FoodProbe(1413, 'Cereal, oatmeal, rolled, regular',   '2',  0.7, 'whole grain cereal (FG8)'),
    FoodProbe(555,  'Chicken, broiler, meat, skin, raw',  '2',  0.7, 'raw meat (FG5)'),

    # Category 2D — Other dairy foods
    FoodProbe(6948, 'Yogourt, plain, fat-free',         '2D', 0.7, 'plain yogurt (FG1, non-cheese, non-beverage)'),
    FoodProbe(6979, 'Yogourt, Greek, plain, fat-free',  '2D', 0.7, 'Greek yogurt (FG1)'),

    # Category 3 — Oils and spreads
    FoodProbe(422,    'Vegetable oil, olive',             '3',  0.7, 'vegetable oil (FG4)'),
    FoodProbe(7458, 'Margarine, stick, canola/soybean', '3',  0.7, 'margarine (FG4)'),
    FoodProbe(527,    'Salad dressing, mayonnaise',       '3',  0.7, 'oil-based spread (FG4)'),
    FoodProbe(16,     'Butter, whipped',                  '3',  0.7, 'butter — FG1 but oil/spread keyword override'),

    # Category 3D — Cheese
    FoodProbe(119, 'Cheese, cheddar',                     '3D', 0.7, 'hard cheese (FG1 + cheese keyword)'),
    FoodProbe(20,  'Cheese, brie',                        '3D', 0.7, 'soft cheese (FG1)'),
    FoodProbe(51,  'Cheese, processed cheddar, cold pack', '3D', 0.7, 'processed cheese (FG1)'),
]


# PANEL B — adversarial single-food probes. Per-row expected_category encodes
# the CURRENT pipeline behaviour (documented to detect regressions). Notes
# explain whether the behaviour matches HSRAC v9 strict interpretation.
PANEL_B_ADVERSARIAL: List[FoodProbe] = [
    # Beverage with "milk" in name but in FG14 (Beverages) — should still hit 1D
    FoodProbe(75,     'Milk shake, chocolate, thick (FG14)', '1D', 0.5,
              'FG14 beverage with milk keyword → 1D override (correct)'),

    # Cottage cheese — debatable: 3D per implementation, but HSRAC v9 sometimes
    # treats cottage cheese as Other dairy food (Cat 2D) because of its fat
    # profile. Documenting current behaviour.
    FoodProbe(25,     'Cheese, cottage, creamed (4.5% MF)', '3D', 0.5,
              'cottage cheese — current rule sends "cheese" keyword → 3D; '
              'HSRAC v9 strict reading might prefer 2D for fat ratio reasons'),

    # Cream cheese spread — has both "cheese" AND "spread" keywords.
    FoodProbe(5565,   'Cheese spread, cream cheese base',   '3D', 0.5,
              'has both "cheese" and "spread" — "cheese" wins; '
              'HSRAC v9 might prefer 2D since cream cheese is "Other dairy"'),

    # Ice cream — dairy-fat product sitting in FG19 (Sweets). Routes via the
    # base rule to Cat 2 (General foods), not Cat 2D.
    FoodProbe(4156,   'Dessert, frozen, ice cream, vanilla light', '2', 0.5,
              'ice cream (FG19) — base rule → Cat 2; HSRAC v9 puts ice cream '
              'under general foods or 2D depending on policy'),

    # Egg in CNF FG1 (Dairy and egg products) — HSR-CATEG-1 fix routes the
    # EGG_RE keyword override to Cat 2 (General foods); HSRAC v9 puts eggs in
    # general foods, not dairy.
    FoodProbe(125,    'Egg, chicken, whole, raw',           '2',  0.5,
              'eggs in FG1 → Cat 2 via EGG_RE keyword override (HSR-CATEG-1)'),

    # Almond oil — has "almond" (plant beverage keyword) AND in FG4 (Oils).
    FoodProbe(440,    'Vegetable oil, almond',              '3',  0.5,
              'almond + oil — FG4 base rule + oil/spread keyword → 3 (correct)'),

    # Bagel — could be confused with "bread" category. Lands in Cat 2.
    FoodProbe(3673,   'Bagel, egg',                         '2',  0.5,
              'bagel (FG18) — should land in Cat 2 like other baked goods'),

    # Yogurt parfait with non-dairy components (granola).
    FoodProbe(6821, 'Yogourt parfait, fruit, granola, reduced-fat', '2D', 0.5,
              'parfait — dominant component is yogurt → 2D'),
]


# PANEL C — meal-level (multi-food)
@dataclass
class MealProbe:
    name: str
    foods: List[Tuple[int, float]]   # (food_id, serving_g)
    expected_category: str
    notes: str = ''


PANEL_C_MEALS: List[MealProbe] = [
    MealProbe('Just whole milk',
              [(113, 250.0)], '1D',
              'single-food fallback; conf should be 1.0'),
    MealProbe('Just cheddar',
              [(119, 30.0)], '3D',
              'single-food fallback'),
    MealProbe('Cereal + milk breakfast',
              [(1413, 40.0), (113, 200.0)], '1D',
              'mass-dominant: milk (200 g) vs cereal (40 g) → milk wins (83 % '
              'mass). HSR-CATEG-2 rule picks milk\'s 1D. If users want a '
              '"cereal bowl" classification they should match the dairy portion '
              'to a typical pour (~75 g).'),
    MealProbe('Greek yogurt + apple',
              [(6979, 150.0), (1696, 80.0)], '2D',
              'dairy food + fruit — dairy component dominant'),
    MealProbe('Salad + chicken + olive oil',
              [(1990, 80.0), (555, 100.0), (422, 10.0)], '2',
              'general-foods composite'),
    MealProbe('Pasta + olive oil',
              [(4066, 80.0), (422, 10.0)], '2',
              'general food + small oil — general food dominates'),
    MealProbe('Cheese + bread (sandwich)',
              [(119, 30.0), (4066, 60.0)], '2',
              'mixed cheese + grain — HSRAC v9 would treat as Cat 2 sandwich; '
              'current rule may pick 3D since cheese is high-scoring'),
    MealProbe('Beer + chips snack',
              [(2835, 350.0), (4066, 30.0)], '1',
              'beverage-dominant snack pairing'),
]


# --- Test runner ---------------------------------------------------------

@dataclass
class CategorisationCheck:
    panel: str
    name: str
    food_id: Optional[int]
    expected_category: str
    observed_category: str
    observed_confidence: float
    observed_meal_confidence: Optional[float]
    passed: bool
    detail: str = ''


def _post_hsr(client: Client, food_ids: List[int], serving_sizes: List[float]) -> Dict[str, Any]:
    r = client.post('/api/hsr/calculate/',
                    data=json.dumps({
                        'food_ids': food_ids,
                        'serving_sizes': serving_sizes,
                        'user_type': 'researcher',
                    }),
                    content_type='application/json', secure=True)
    if r.status_code != 200:
        raise RuntimeError(f'HTTP {r.status_code}: {r.content[:200]!r}')
    return r.json()


def run_panel_a(client: Client) -> List[CategorisationCheck]:
    checks: List[CategorisationCheck] = []
    for p in PANEL_A_CANONICAL:
        try:
            j = _post_hsr(client, [p.food_id], [100.0])
            fd = j['food_details'][0]
            rating = j['hsr_result']['rating']
            obs_cat = str(rating['category'])
            obs_conf = float(fd.get('category_confidence', 0))
            cat_ok = obs_cat == p.expected_category
            conf_ok = obs_conf >= p.min_confidence
            passed = cat_ok and conf_ok
            detail = []
            if not cat_ok:
                detail.append(f'expected {p.expected_category!r}, got {obs_cat!r}')
            if not conf_ok:
                detail.append(f'conf {obs_conf:.2f} < {p.min_confidence}')
            checks.append(CategorisationCheck(
                panel='A',
                name=p.name,
                food_id=p.food_id,
                expected_category=p.expected_category,
                observed_category=obs_cat,
                observed_confidence=obs_conf,
                observed_meal_confidence=None,
                passed=passed,
                detail='; '.join(detail) if detail else p.gloss,
            ))
        except Exception as exc:
            checks.append(CategorisationCheck(
                panel='A', name=p.name, food_id=p.food_id,
                expected_category=p.expected_category,
                observed_category='ERR', observed_confidence=0.0,
                observed_meal_confidence=None, passed=False,
                detail=f'exception: {exc!r}'))
    return checks


def run_panel_b(client: Client) -> List[CategorisationCheck]:
    """Adversarial panel — documents observed behaviour with a softer gate."""
    checks: List[CategorisationCheck] = []
    for p in PANEL_B_ADVERSARIAL:
        try:
            j = _post_hsr(client, [p.food_id], [100.0])
            fd = j['food_details'][0]
            rating = j['hsr_result']['rating']
            obs_cat = str(rating['category'])
            obs_conf = float(fd.get('category_confidence', 0))
            cat_ok = obs_cat == p.expected_category
            checks.append(CategorisationCheck(
                panel='B',
                name=p.name,
                food_id=p.food_id,
                expected_category=p.expected_category,
                observed_category=obs_cat,
                observed_confidence=obs_conf,
                observed_meal_confidence=None,
                passed=cat_ok,
                detail=(p.gloss if cat_ok else
                        f'expected {p.expected_category!r}, got {obs_cat!r} — {p.gloss}'),
            ))
        except Exception as exc:
            checks.append(CategorisationCheck(
                panel='B', name=p.name, food_id=p.food_id,
                expected_category=p.expected_category,
                observed_category='ERR', observed_confidence=0.0,
                observed_meal_confidence=None, passed=False,
                detail=f'exception: {exc!r}'))
    return checks


def run_panel_c(client: Client) -> List[CategorisationCheck]:
    checks: List[CategorisationCheck] = []
    for p in PANEL_C_MEALS:
        try:
            food_ids = [fid for fid, _ in p.foods]
            sizes    = [s   for _,   s in p.foods]
            j = _post_hsr(client, food_ids, sizes)
            rating = j['hsr_result']['rating']
            obs_cat = str(rating['category'])
            mc = j.get('meal_categorization') or {}
            meal_conf = float(mc.get('category_confidence', 0.0))
            cat_ok = obs_cat == p.expected_category
            checks.append(CategorisationCheck(
                panel='C',
                name=p.name,
                food_id=None,
                expected_category=p.expected_category,
                observed_category=obs_cat,
                observed_confidence=0.0,
                observed_meal_confidence=meal_conf,
                passed=cat_ok,
                detail=(p.notes if cat_ok else
                        f'expected {p.expected_category!r}, got {obs_cat!r} — {p.notes}'),
            ))
        except Exception as exc:
            checks.append(CategorisationCheck(
                panel='C', name=p.name, food_id=None,
                expected_category=p.expected_category,
                observed_category='ERR', observed_confidence=0.0,
                observed_meal_confidence=None, passed=False,
                detail=f'exception: {exc!r}'))
    return checks


# --- Report ---------------------------------------------------------------

def _format_panel(panel: str, title: str, checks: List[CategorisationCheck]) -> None:
    n_pass = sum(1 for c in checks if c.passed)
    n_total = len(checks)
    print(f'\nPANEL {panel}: {title}  ({n_pass}/{n_total} PASS)')
    print('-' * 100)
    for c in checks:
        mark = '[ OK ]' if c.passed else '[FAIL]'
        fid = f'CNF {c.food_id}' if c.food_id is not None else '— meal —'
        conf_str = f'conf={c.observed_confidence:.2f}' if c.observed_meal_confidence is None \
            else f'meal_conf={c.observed_meal_confidence:.2f}'
        print(f'  {mark}  {fid:<12} cat={c.observed_category:>3}/exp={c.expected_category:<3}  '
              f'{conf_str:<18}  {c.name[:42]:<42}')
        if c.detail:
            print(f'         └─ {c.detail[:90]}')


def main() -> int:
    client = Client()
    print('HSR categorisation smoke + stress test')
    print('  Panel A (canonical):    ', len(PANEL_A_CANONICAL), 'single-food probes')
    print('  Panel B (adversarial):  ', len(PANEL_B_ADVERSARIAL), 'single-food probes')
    print('  Panel C (meal-level):   ', len(PANEL_C_MEALS), 'multi-food probes')
    print('=' * 100)

    a = run_panel_a(client)
    b = run_panel_b(client)
    c = run_panel_c(client)
    _format_panel('A', 'canonical single-food (gate: category match + conf ≥ 0.7)', a)
    _format_panel('B', 'adversarial single-food (gate: category match against current behaviour)', b)
    _format_panel('C', 'meal-level multi-food (gate: category match against current behaviour)', c)

    all_checks = a + b + c
    n_pass = sum(1 for c_ in all_checks if c_.passed)
    n_fail = sum(1 for c_ in all_checks if not c_.passed)
    print()
    print('=' * 100)
    print(f'Overall: PASS={n_pass}  FAIL={n_fail}  TOTAL={n_pass + n_fail}')

    out_path = os.path.join(_HERE, '_smoke_hsr_categorization_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness': 'HSR categorisation smoke + stress test',
            'summary': {'pass': n_pass, 'fail': n_fail, 'total': n_pass + n_fail,
                        'panel_a_pass': sum(1 for x in a if x.passed),
                        'panel_a_total': len(a),
                        'panel_b_pass': sum(1 for x in b if x.passed),
                        'panel_b_total': len(b),
                        'panel_c_pass': sum(1 for x in c if x.passed),
                        'panel_c_total': len(c)},
            'checks': [
                {'panel': x.panel, 'name': x.name, 'food_id': x.food_id,
                 'expected_category': x.expected_category,
                 'observed_category': x.observed_category,
                 'observed_confidence': x.observed_confidence,
                 'observed_meal_confidence': x.observed_meal_confidence,
                 'passed': x.passed, 'detail': x.detail}
                for x in all_checks
            ],
        }, f, indent=2)
    print(f'Results JSON: {out_path}')
    # Gate: Panel A must be 100% PASS (canonical foods are non-negotiable).
    # Panels B and C are descriptive; surface failures but don't gate.
    panel_a_failed = any(not x.passed for x in a)
    return 1 if panel_a_failed else 0


if __name__ == '__main__':
    sys.exit(main())
