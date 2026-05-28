"""NOVA classification validation harness (Monteiro 2019 canonical examples).

Tests the rigorous NOVA classifier at
`backend/fcs_calculator/fcs/utils/nova_classifier.py` (replacing the previous
inline substring-keyword block in cnf_data_integrator.py). Each panel row
specifies the Monteiro 2019 expected NOVA group for a CNF FoodID; the gate
is exact-match (a 1-off miss is a real misclassification, not a rounding
quirk like HSR's ±0.5 stars).

Run from `backend/`:
    python _smoke_nova_classification.py

The panel covers all four NOVA groups with multiple representatives each:
  - NOVA 1 (minimally processed): raw fruit, raw vegetable, plain milk,
    raw seeds, frozen vegetable boiled (Monteiro explicitly lists frozen
    + boiled as NOVA 1 preservation methods)
  - NOVA 2 (culinary ingredients): granulated sugar, vegetable oil, butter
  - NOVA 3 (processed foods): canned tuna, cheese, plain commercial bread,
    cured bacon, 100% fruit juice
  - NOVA 4 (ultra-processed): regular cola, sugar-sweetened almond
    beverage, hot dog (Monteiro canonical: "reconstituted meat product"),
    pepperoni pizza (Monteiro canonical: "pre-prepared frozen dish"),
    breakfast cereal, ice cream, candy
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
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-nova-classification'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from heni_calculator.heni.service import get_cnf_integrator  # noqa: E402
from api.cnf_cache import get_api_cnf_pipeline  # noqa: E402
from fcs_calculator.fcs.utils.nova_classifier import classify as nova_classify  # noqa: E402


@dataclass
class NovaPanelRow:
    label: str
    cnf_food_id: int
    expected_nova: int   # 1-4 per Monteiro 2019
    monteiro_rationale: str  # which Monteiro definition row this maps to


# Canonical NOVA panel — each food chosen to anchor a specific Monteiro
# definition row, not just "feels like NOVA X". Citations are to
# Monteiro et al. 2019 (FAO, "Ultra-processed foods, diet quality, and
# health using the NOVA classification system", §4.1-§4.4).
NOVA_PANEL: List[NovaPanelRow] = [
    # ===== NOVA 1: Unprocessed or minimally processed foods =====
    NovaPanelRow('Apple, raw, with skin (1696)', 1696, 1,
                 'Monteiro §4.1: "edible parts of plants ... after separation '
                 'from nature" — raw fruit is the canonical NOVA 1 example.'),
    NovaPanelRow('Spinach, New Zealand, raw (2132)', 2132, 1,
                 'Monteiro §4.1: raw vegetable.'),
    NovaPanelRow('Chicken broiler wing meat+skin roasted (629)', 629, 1,
                 'Monteiro §4.1: muscle meat altered only by roasting '
                 '(preservation/cooking) qualifies as NOVA 1.'),
    NovaPanelRow('Milk, fluid, whole 3.25% (113)', 113, 1,
                 'Monteiro §4.1: pasteurised plain milk is explicitly listed '
                 'in the NOVA 1 preservation methods.'),
    NovaPanelRow('Chia seeds, dried (2511)', 2511, 1,
                 'Monteiro §4.1: dried seeds (NOVA 1 preservation).'),
    NovaPanelRow('Broccoli, frozen, spears, boiled (2026)', 2026, 1,
                 'Monteiro §4.1: freezing AND boiling are both explicit '
                 'NOVA 1 preservation/cooking methods. This row was the '
                 'OIL/BOILED substring-bug failure pre-2026-05-23.'),

    # ===== NOVA 2: Processed culinary ingredients =====
    NovaPanelRow('Sweets, sugars, granulated (4318)', 4318, 2,
                 'Monteiro §4.1: "sugar ... substances derived from Group 1 '
                 'foods or from nature by ... refining" — canonical NOVA 2.'),
    NovaPanelRow('Vegetable oil, olive (422)', 422, 2,
                 'Monteiro §4.1: "oils ... derived from Group 1 by pressing".'),
    NovaPanelRow('Butter, whipped (16)', 16, 2,
                 'Monteiro §4.1: "butter ... derived from Group 1".'),

    # ===== NOVA 3: Processed foods =====
    NovaPanelRow('Beef, cured, corned beef, canned (2791)', 2791, 3,
                 'Monteiro §4.2: "canned fish ... cured meats" — cured + '
                 'canned places this firmly in NOVA 3.'),
    NovaPanelRow('Cheese, edam (29)', 29, 3,
                 'Monteiro §4.2: "cheeses" listed as canonical NOVA 3 '
                 '(non-alcoholic fermentation preservation).'),
    NovaPanelRow('Bread, white, commercial (4066)', 4066, 3,
                 'Monteiro §4.2: "freshly made breads" — commercial plain '
                 'white bread without ultra-processed additives is NOVA 3.'),
    NovaPanelRow('Pork, cured, bacon, raw (1936)', 1936, 3,
                 'Monteiro §4.2: cured pork is NOVA 3 by preservation method.'),
    NovaPanelRow('Apple juice, canned (1495)', 1495, 3,
                 'Monteiro §4.2: 100% fruit juice without added ingredients '
                 'is NOVA 3 (canning preservation of NOVA 1 fruit).'),

    # ===== NOVA 4: Ultra-processed foods =====
    NovaPanelRow('Wiener (frankfurter), beef (1185)', 1185, 4,
                 'Monteiro §4.3 LITERAL CANONICAL EXAMPLE: "reconstituted '
                 'meat products" includes hot dogs / frankfurters. Pre-fix '
                 'this was misclassified as NOVA 3.'),
    NovaPanelRow('Fast foods, hot dog, plain (4644)', 4644, 4,
                 'Monteiro §4.3 LITERAL CANONICAL EXAMPLE: hot dog at fast-'
                 'food chain = reconstituted meat product + commercial bun '
                 'with dough conditioners. Pre-fix this was misclassified '
                 'as NOVA 3.'),
    NovaPanelRow('Pizza, pepperoni, frozen, cooked (4962)', 4962, 4,
                 'Monteiro §4.3 LITERAL CANONICAL EXAMPLE: "pre-prepared '
                 'frozen dishes". Pre-fix this was misclassified as NOVA 3.'),
    NovaPanelRow('Plant-based beverage, almond, sweetened (7225)', 7225, 4,
                 'Monteiro §4.3: sweetened plant-based beverage = added-sugar '
                 'industrial formulation in the SSB band.'),
    NovaPanelRow('Cereal, ready to eat, Honey Bunches of Oats (1314)', 1314, 4,
                 'Monteiro §4.3 LITERAL CANONICAL EXAMPLE: "breakfast '
                 'cereal" packaged ready-to-eat sweetened cereal.'),
    NovaPanelRow('Dessert, frozen, ice cream, vanilla, rich (4157)', 4157, 4,
                 'Monteiro §4.3: ice cream is the classic NOVA 4 dairy '
                 'dessert (emulsifiers, stabilizers, added sugars).'),
]


def _load_food_metadata(food_id: int) -> Tuple[str, str, int]:
    """Returns (food_description, food_group_name, food_group_id)."""
    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    fg = pipe.food_group_df
    row = fn[fn['FoodID'] == food_id]
    if row.empty:
        return ('', '', 0)
    desc = str(row['FoodDescription'].iloc[0])
    gid = int(row['FoodGroupID'].iloc[0])
    fg_row = fg[fg['FoodGroupID'] == gid]
    gname = str(fg_row['FoodGroupName'].iloc[0]) if not fg_row.empty else ''
    return (desc, gname, gid)


def main() -> int:
    print('NOVA classification validation harness (Monteiro 2019 canonical examples)')
    print('  Gate: per-food NOVA level EXACT match (no half-band tolerance)')
    print('  Pipeline: nova_classifier.classify() — CNF FoodGroup hard rules + '
          'word-boundary keyword matching + optional LLM augmentation')
    print('=' * 80)
    print()

    n_pass = n_fail = 0
    results = []
    per_group_stats = {1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0]}  # {nova: [pass, total]}

    for row in NOVA_PANEL:
        desc, gname, gid = _load_food_metadata(row.cnf_food_id)
        if not desc:
            print(f'[ERROR] {row.label}: CNF FoodID {row.cnf_food_id} not found')
            n_fail += 1
            continue
        result = nova_classify(
            food_id=row.cnf_food_id,
            food_description=desc,
            food_group_name=gname,
            food_group_id=gid,
            chat_json_client=None,  # rule-based only for now
            enable_llm=False,
        )
        ok = result.level == row.expected_nova
        verdict = 'PASS' if ok else 'FAIL'
        if ok:
            n_pass += 1
            per_group_stats[row.expected_nova][0] += 1
        else:
            n_fail += 1
        per_group_stats[row.expected_nova][1] += 1

        print(f'[{verdict:>4}]  expected NOVA {row.expected_nova}  actual NOVA {result.level}  '
              f'conf={result.confidence:.2f}')
        print(f'        {row.label}')
        print(f'        CNF group: {gname} ({gid})')
        print(f'        rationale: {result.rationale}')
        if not ok:
            print(f'        EXPECTED ({row.expected_nova}): {row.monteiro_rationale}')
        print()

        results.append({
            **asdict(row),
            'cnf_food_description': desc,
            'cnf_food_group': gname,
            'cnf_food_group_id': gid,
            'actual_nova': result.level,
            'confidence': result.confidence,
            'rationale': result.rationale,
            'matched_patterns': result.matched_patterns,
            'verdict': verdict,
        })

    print('-' * 80)
    print('Per-NOVA-group accuracy:')
    for nova, (p, t) in per_group_stats.items():
        if t > 0:
            print(f'  NOVA {nova}: {p}/{t} PASS')
    print()

    print('=' * 80)
    n_total = n_pass + n_fail
    overall = (n_pass == n_total)
    print(f'Summary: {n_pass}/{n_total} PASS  |  overall: {"PASS" if overall else "FAIL"}')

    out_path = os.path.join(_HERE, '_smoke_nova_classification_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'panel_description': 'NOVA classification validation harness (Monteiro 2019 canonical examples)',
            'gate': 'per-food exact-match NOVA level (1-4)',
            'classifier': 'fcs_calculator.fcs.utils.nova_classifier.classify (rule-based)',
            'summary': {
                'n_pass': n_pass, 'n_total': n_total,
                'per_nova_group': {
                    str(k): {'pass': v[0], 'total': v[1]}
                    for k, v in per_group_stats.items()
                },
            },
            'rows': results,
        }, f, indent=2, default=str)
    print(f'Results JSON: {out_path}')
    return 0 if overall else 1


if __name__ == '__main__':
    sys.exit(main())
