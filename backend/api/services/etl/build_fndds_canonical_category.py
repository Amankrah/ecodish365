"""One-time ETL: map FDC FNDDS WWEIA categories → canonical food categories.

Reads `wweia_food_category.csv` (172 entries in the 2024-10-31 release),
applies an ordered ruleset (regex on description + WWEIA code-prefix
fallback), assigns the same ecodish365 FoodGroupID the FDC ingest will
allocate (FDC_FNDDS_FOOD_GROUP_BASE=100 + sorted-index), and emits a
JSON fragment matching the `fdc` block in
[food_group_canonical_category.json](backend/api/data/food_group_canonical_category.json).

Run:
    cd backend && python -m api.services.etl.build_fndds_canonical_category

The script is idempotent and DESTRUCTIVE on the FDC FNDDS portion of the
bridge JSON — it overwrites entries with FoodGroupID ≥ 100. CNF, WAFCT
and FDC Legacy entries are preserved. Any WWEIA categories that don't
match a regex rule are emitted as canonical="unknown" with a warning,
and listed in the script's stdout so a human can hand-map them.

Reused: standard ETL pattern from
[build_cnf_prep_state.py](backend/api/services/etl/build_cnf_prep_state.py).
"""
from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[3]
FNDDS_CSV   = BACKEND_DIR / 'raw_fndds' / 'FoodData_Central_survey_food_csv_2024-10-31' / 'wweia_food_category.csv'
BRIDGE_JSON = BACKEND_DIR / 'api' / 'data' / 'food_group_canonical_category.json'

FDC_FNDDS_FOOD_GROUP_BASE = 100  # mirrors fdc_ingest.FDC_FNDDS_FOOD_GROUP_BASE


# Ordered ruleset. Each rule is (regex_against_description, canonical, cnf_equivalent_group_id).
# Order matters — earlier rules win. Regexes are case-insensitive and anchored or
# substring-style as documented inline.
_RULES: list[Tuple[re.Pattern, str, Optional[int]]] = [
    # Dairy beverages (milk, flavored milk, dairy drinks, milkshakes, plant milk)
    (re.compile(r'^plant-based\s+(milk|yogurt)', re.I),     'dairy',              1),   # 1902/1904 — categorized with dairy for consumption pattern; HENI plant-milk filter still excludes from SSB
    (re.compile(r'^milk\s+shakes|^milk,', re.I),            'dairy',              1),
    (re.compile(r'^(flavored\s+)?milk\b', re.I),            'dairy',              1),
    (re.compile(r'^cheese|^cottage', re.I),                 'dairy',              1),
    (re.compile(r'^yogurt|^pudding', re.I),                 'dairy',              1),
    (re.compile(r'^ice\s+cream|^frozen\s+dairy', re.I),     'dairy',              1),

    # Eggs
    (re.compile(r'^eggs?\b|^egg\s+rolls', re.I),            'eggs',               1),   # 2502; egg rolls (3406) handled by mixed_dishes rule later — but eggs prefix would catch first
    (re.compile(r'^egg/breakfast', re.I),                   'mixed_dishes',       22),  # 3706 egg breakfast sandwiches

    # Meats
    (re.compile(r'^beef\b|^ground\s+beef', re.I),           'beef',               13),
    (re.compile(r'^pork\b', re.I),                          'pork',               10),
    (re.compile(r'^lamb|^goat|^game', re.I),                'lamb_veal_game',     17),
    (re.compile(r'^liver|^organ', re.I),                    'beef',               13),  # 2010 — fold into beef bucket for HSR/HENI purposes
    (re.compile(r'^chicken\b|^turkey\b|^duck\b|^poultry', re.I), 'poultry',       5),
    (re.compile(r'^fish\b|^shellfish', re.I),               'fish',               15),
    (re.compile(r'^cold\s+cuts|^bacon\b|^frankfurters?\b|^sausages?\b', re.I),
                                                            'sausages_luncheon',  7),

    # Legumes / nuts / soy alternatives
    (re.compile(r'^beans?,?\s+|^peas?\b|^legumes?\b|^bean,', re.I),
                                                            'legumes',            16),
    (re.compile(r'^nuts?\b|^seeds?\b|^peanut\s+butter', re.I),
                                                            'nuts_seeds',         12),
    (re.compile(r'^soy\b|^meat-alternative', re.I),         'legumes',            16),  # soy → legumes per Stylianou

    # Mixed dishes (catch the *_mixed_dishes/sandwich/pizza/burger/dishes families)
    (re.compile(r'\bmixed\s+dishes?\b', re.I),              'mixed_dishes',       22),
    (re.compile(r'^vegetable\s+dishes?|^bean,\s+pea,\s+legume\s+dishes?', re.I),
                                                            'mixed_dishes',       22),
    (re.compile(r'^stir-fry|^egg\s+rolls,\s+dumplings|^fried\s+rice|^macaroni\s+and\s+cheese', re.I),
                                                            'mixed_dishes',       22),
    (re.compile(r'^turnovers|^pasta\s+mixed', re.I),        'mixed_dishes',       22),
    (re.compile(r'^pizza|^burgers?\b', re.I),               'mixed_dishes',       22),
    (re.compile(r'sandwich(es)?\b', re.I),                  'mixed_dishes',       22),
    (re.compile(r'^burritos?|^tacos?|^nachos|^other\s+mexican', re.I),
                                                            'mixed_dishes',       22),

    # Soups
    (re.compile(r'^soups,|^ramen', re.I),                   'soups_sauces',       6),

    # Cereals / grains / pasta
    (re.compile(r'^rice\b|^pasta,\s*noodles', re.I),        'cereals_grains',     20),
    (re.compile(r'^yeast\s+breads|^rolls\s+and\s+buns|^bagels|^tortillas|^biscuits|^pancakes', re.I),
                                                            'baked_products',     18),
    (re.compile(r'^ready-to-eat\s+cereal|^oatmeal|^grits', re.I),
                                                            'breakfast_cereals',  8),

    # Snacks (chips, popcorn, pretzels, crackers, bars)
    (re.compile(r'^potato\s+chips|^tortilla,\s*corn,|^popcorn|^pretzels', re.I),
                                                            'snacks',             25),
    (re.compile(r'^crackers,|^saltine', re.I),              'snacks',             25),
    (re.compile(r'^cereal\s+bars|^nutrition\s+bars', re.I), 'snacks',             25),

    # Sweets (cakes, cookies, doughnuts, candy)
    (re.compile(r'^cakes?\s+and\s+pies|^cookies?\b|^doughnuts?,?', re.I),
                                                            'sweets',             19),
    (re.compile(r'^candy\b', re.I),                         'sweets',             19),
    (re.compile(r'^gelatins?,|^sugars?\s+and\s+honey|^sugar\s+substitutes|^jams,', re.I),
                                                            'sweets',             19),

    # Fruits
    (re.compile(r'^apples?\b|^bananas?\b|^grapes?\b|^peaches?\b|^strawberries|^blueberries|^citrus\s+fruits?|^melons?\b|^dried\s+fruits?|^pears?\b|^pineapple|^mango|^papaya|^other\s+fruits?\s+and\s+fruit\s+salads', re.I),
                                                            'fruits',             9),

    # Vegetables
    (re.compile(r'^tomatoes?\b|^carrots?\b|^broccoli|^spinach|^lettuce|^string\s+beans|^cabbage|^onions?|^corn\b|^other\s+(red\s+and\s+orange|dark\s+green|starchy)?\s*vegetables?', re.I),
                                                            'vegetables',         11),
    (re.compile(r'^vegetables?,|^fried\s+vegetables|^coleslaw|^vegetables\s+on\s+a\s+sandwich', re.I),
                                                            'vegetables',         11),
    (re.compile(r'^white\s+potatoes|^french\s+fries|^mashed\s+potatoes', re.I),
                                                            'vegetables',         11),  # potatoes → vegetables per CNF FG11 convention

    # Juices
    (re.compile(r'\bjuice\b', re.I),                        'fruits',             9),   # juices → fruits (CNF FG9 is "Fruits AND fruit juices")

    # Beverages — order matters, alcoholic first
    (re.compile(r'^beer\b|^wine\b|^liquor|^cocktails?', re.I),
                                                            'alcoholic_beverages',14),
    (re.compile(r'^coffee\b|^tea\b', re.I),                 'beverages',          14),
    (re.compile(r'^tap\s+water|^bottled\s+water|^flavored\s+or\s+carbonated\s+water|^enhanced\s+water', re.I),
                                                            'beverages',          14),
    (re.compile(r'^diet\s+(soft\s+drinks|sport\s+and\s+energy|drinks)|^other\s+diet\s+drinks', re.I),
                                                            'beverages',          14),
    (re.compile(r'^soft\s+drinks|^fruit\s+drinks|^sport\s+and\s+energy\s+drinks|^nutritional\s+beverages|^smoothies', re.I),
                                                            'beverages',          14),

    # Fats / oils / condiments / spreads
    (re.compile(r'^butter\s+and\s+animal\s+fats|^margarine|^cream\s+cheese,\s+sour\s+cream|^cream\s+and\s+cream\s+substitutes|^mayonnaise|^salad\s+dressings', re.I),
                                                            'fats_oils',          4),
    (re.compile(r'-based\s+condiments|^mustard|^olives,|^pasta\s+sauces|^dips,', re.I),
                                                            'soups_sauces',       6),

    # Baby foods (any "Baby" prefix)
    (re.compile(r'^baby\b|^formula,|^human\s+milk', re.I),  'babyfoods',          3),

    # Misc / fallback
    (re.compile(r'^protein\s+and\s+nutritional\s+powders', re.I),
                                                            'beverages',          14),  # protein shakes → beverages bucket
    (re.compile(r'^not\s+included\s+in\s+a\s+food\s+category', re.I),
                                                            'unknown',            None),
]


def classify(description: str) -> Tuple[str, Optional[int]]:
    """Return (canonical_category, cnf_equivalent_group_id) for one WWEIA name."""
    for pat, canonical, cnf_eq in _RULES:
        if pat.search(description):
            return canonical, cnf_eq
    return 'unknown', None


def _load_wweia_csv() -> list[Tuple[int, str]]:
    """Read wweia_food_category.csv into (wweia_code, description) tuples."""
    out: list[Tuple[int, str]] = []
    with FNDDS_CSV.open('r', encoding='utf-8', newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                code = int(row['wweia_food_category'])
            except (TypeError, ValueError):
                continue
            desc = (row.get('wweia_food_category_description') or '').strip()
            if not desc:
                continue
            out.append((code, desc))
    return out


def build_fndds_block() -> dict:
    """Return the `fdc` JSON block of FNDDS entries (FoodGroupID ≥ 100)."""
    rows = _load_wweia_csv()
    rows.sort(key=lambda r: r[0])  # mirror fdc_ingest sorted-index allocation
    out: dict = {}
    unmapped: list[Tuple[int, int, str]] = []
    for i, (wweia_code, desc) in enumerate(rows):
        ecodish_id = FDC_FNDDS_FOOD_GROUP_BASE + i
        canonical, cnf_eq = classify(desc)
        out[str(ecodish_id)] = {
            'name':                    f'FDC FNDDS — {desc}',
            'canonical':               canonical,
            'cnf_equivalent_group_id': cnf_eq,
            'wweia_code':              wweia_code,
        }
        if canonical == 'unknown':
            unmapped.append((ecodish_id, wweia_code, desc))
    return out, unmapped


def main() -> None:
    bridge = json.loads(BRIDGE_JSON.read_text(encoding='utf-8'))
    fdc_block = bridge.get('fdc', {})
    # Preserve existing FDC Legacy entries (FoodGroupID 70-97); discard any
    # FoodGroupID >= 100 (FNDDS slot) — we rebuild that block from WWEIA.
    legacy = {k: v for k, v in fdc_block.items() if int(k) < 100}

    fndds_block, unmapped = build_fndds_block()
    fdc_combined = {**legacy, **fndds_block}
    # Sort keys numerically for deterministic JSON output.
    fdc_sorted = dict(sorted(fdc_combined.items(), key=lambda kv: int(kv[0])))
    bridge['fdc'] = fdc_sorted

    BRIDGE_JSON.write_text(json.dumps(bridge, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print('=' * 78)
    print('FDC FNDDS WWEIA -> canonical category ETL')
    print('=' * 78)
    print(f'WWEIA rows processed:    {len(fndds_block)}')
    print(f'Bridged successfully:    {len(fndds_block) - len(unmapped)}')
    print(f'Unmapped (-> "unknown"): {len(unmapped)}')
    if unmapped:
        print('\nUnmapped entries (hand-map these in the bridge JSON):')
        for ecodish_id, wweia_code, desc in unmapped:
            print(f'  FoodGroupID={ecodish_id:>4}  wweia={wweia_code:>5}  {desc}')
    canonical_counts: dict[str, int] = {}
    for v in fndds_block.values():
        canonical_counts[v['canonical']] = canonical_counts.get(v['canonical'], 0) + 1
    print('\nCanonical category counts (FNDDS only):')
    for cat, n in sorted(canonical_counts.items(), key=lambda kv: -kv[1]):
        print(f'  {cat:<24} {n:>3}')
    print(f'\nBridge written to {BRIDGE_JSON}')


if __name__ == '__main__':
    main()
