"""One-time ETL: classify every CNF FoodID as a single ingredient vs a mixed dish.

The recipe decomposer needs to know whether a catalog food is a *single
ingredient* (apple, milk, a plain cut of meat, raw flour) or a *mixed dish*
(soup, pizza, casserole, sausage). That distinction is what makes the
reconstruction-gated catalog override safe: a dish should only ever be
collapsed onto a *measured mixed-dish* food, never onto a single ingredient
(so "chicken soup" can fall back to a measured chicken-noodle soup, but
"beef stew" must never be flattened onto "Beef, ground").

There is no clean data-driven signal for this (FNDDS ingredient counts mislabel
~61 % — cooking additions inflate them; the CNF `FoodSourceID = 35` "recipe
compilation" flag covers only 134 of 5,993 foods). So we classify with the LLM
once, mirroring the resumable/idempotent pattern of `build_cnf_to_fndds_bridge`:
each CNF FoodID's bilingual description + food group + recipe-compilation hint
goes to gpt-4.1-mini (temp 0, JSON-only) which returns
`{food_type: "single"|"mixed", confidence, rationale}`.

Reads (via the shared CNF pipeline):
    food_name_df (FoodID, FoodDescription, FoodDescriptionF, FoodGroupID, FoodSourceID)
    food_group_df (FoodGroupID -> FoodGroupName)

Writes (api-level shared artifact, alongside cnf_fped_profile.json):
    api/data/cnf_food_type.json       {food_id: {food_type, confidence, rationale}}
    api/data/cnf_food_type_meta.json  (sha, counts, provenance)

Resumable: saves every 100 foods so a crashed run can be re-started.
Idempotent: re-running with the existing JSON in place skips already-labeled foods.

Cost (estimated): ~5,993 CNF foods x ~450-token prompt + ~60-token response
    ~= ~3M tokens = ~$1-2 one-time (gpt-4.1-mini at $0.15 / $0.60 per 1M).

Usage (one-time, requires OPENAI_API_KEY; from backend/):
    python -m api.services.etl.build_cnf_food_type
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

_BACKEND_ROOT = Path(__file__).resolve().parents[3]  # api/services/etl -> backend
_OUT_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cnf_food_type.json'
_META_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cnf_food_type_meta.json'

CLASSIFY_MODEL = 'gpt-4.1-mini'
CLASSIFY_TEMPERATURE = 0.0

# CNF FoodSourceID for recipe-compiled foods — a strong "mixed" prior.
_RECIPE_COMPILATION_SOURCE_ID = 35

# Per-group prior. These are gentle hints passed to the LLM as context, NOT hard
# rules: the model still decides per food (a single juice lives in a single-leaning
# group; a plain cracker can sit in a mixed-leaning one). Derived from the 24 CNF
# food groups in raw_cnf/FOOD_GROUP.csv.
_GROUP_LEAN: Dict[str, str] = {
    'Fruits and fruit juices': 'usually single',
    'Vegetables and Vegetable Products': 'usually single',
    'Nuts and Seeds': 'usually single',
    'Beef Products': 'usually single',
    'Pork Products': 'usually single',
    'Poultry Products': 'usually single',
    'Finfish and Shellfish Products': 'usually single',
    'Lamb, Veal and Game': 'usually single',
    'Legumes and Legume Products': 'usually single',
    'Fats and Oils': 'usually single',
    'Spices and Herbs': 'usually single',
    'Dairy and Egg Products': 'usually single',
    'Beverages': 'usually single',
    'Cereals, Grains and Pasta': 'usually single (plain grains/pasta)',
    'Soups, Sauces and Gravies': 'usually mixed',
    'Sausages and Luncheon meats': 'usually mixed',
    'Fast Foods': 'usually mixed',
    'Mixed Dishes': 'almost always mixed',
    'Baked Products': 'usually mixed',
    'Sweets': 'usually mixed',
    'Breakfast cereals': 'usually mixed (processed)',
    'Babyfoods': 'mixed dinners vs single purees — judge per item',
    'Snacks': 'usually mixed',
    # WAFCT 2019 groups (West African foods, FoodID >= 700000). Many entries in the
    # ingredient-named groups are actually composite local dishes (porridges, balls,
    # stews), so several leans are "judge per item" — the description is the real signal.
    'WAFCT — Cereals and their products': 'raw grains single; porridges/local cereal dishes mixed — judge per item',
    'WAFCT — Legumes and their products': 'plain legumes single; bean dishes mixed — judge per item',
    'WAFCT — Vegetables and their products': 'plain vegetables single; vegetable dishes mixed — judge per item',
    'WAFCT — Meat, poultry and their products': 'plain cuts single; meat dishes/stews mixed — judge per item',
    'WAFCT — Fish and its products': 'plain fish single; fish dishes mixed — judge per item',
    'WAFCT — Starchy roots, tubers and their products': 'plain roots/tubers single; tuber dishes mixed — judge per item',
    'WAFCT — Fruits and their products': 'usually single',
    'WAFCT — Fats and oils': 'usually single',
    'WAFCT — Nuts, seeds and their products': 'usually single',
    'WAFCT — Soups and sauces': 'usually mixed',
    'WAFCT — Milk and its products': 'plain milk single; milk-based dishes mixed — judge per item',
    'WAFCT — Beverages': 'usually single',
    'WAFCT — Eggs and their products': 'plain eggs single; egg dishes mixed — judge per item',
    'WAFCT — Miscellaneous': 'judge per item',
}

# Pricing snapshot (USD per 1M tokens) for the cost projection. Update with rate changes.
_PRICE_PROMPT_PER_1M = 0.150
_PRICE_COMPLETION_PER_1M = 0.600
_TOKEN_USAGE: Dict[str, int] = {'prompt': 0, 'completion': 0}
# Guards the shared label/fail dicts + token counters when classifying concurrently
# (OpenAI HTTP calls release the GIL, so threads give real throughput).
_RESULTS_LOCK = threading.Lock()


def _accumulated_cost_usd() -> float:
    return (
        _TOKEN_USAGE['prompt'] / 1_000_000 * _PRICE_PROMPT_PER_1M
        + _TOKEN_USAGE['completion'] / 1_000_000 * _PRICE_COMPLETION_PER_1M
    )


def _log_cost_projection(processed: int, remaining: int) -> float:
    spent = _accumulated_cost_usd()
    per_food = spent / max(1, processed)
    projected_total = spent + per_food * remaining
    logger.info(
        'COST CHECKPOINT: processed=%d, spent=$%.4f, per-food=$%.6f, remaining=%d, '
        'projected-additional=$%.4f, projected-total=$%.4f (prompt=%d, completion=%d tokens)',
        processed, spent, per_food, remaining, per_food * remaining, projected_total,
        _TOKEN_USAGE['prompt'], _TOKEN_USAGE['completion'],
    )
    return projected_total


_SYSTEM_MSG = (
    'You label a Canadian Nutrient File (CNF) food as either a SINGLE ingredient '
    'or a MIXED dish, for a recipe-decomposition pipeline.\n'
    'SINGLE = one food/ingredient as eaten, including cooked or minimally-processed '
    'forms: apple, roasted chicken breast, boiled carrot, whole milk, plain yogurt, '
    'raw flour, table sugar, a single beverage (coffee, orange juice, cola), a plain '
    'cut or ground form of one meat or fish. Adding only salt, water, or cooking fat '
    'does NOT make a food mixed. One-ingredient foods stay single even when cooked.\n'
    'MIXED = a composite dish or multi-ingredient manufactured product: soup, stew, '
    'sauce, gravy, casserole, pizza, sandwich, burger, sausage / luncheon meat / hot '
    'dog, baked goods made from several ingredients (bread, cake, cookie, pie), '
    'granola, candy / chocolate bars, flavoured or sweetened multi-ingredient products, '
    'baby-food dinners (but a plain single-fruit/vegetable baby puree is single), and '
    'most fast foods.\n'
    'Respond with JSON only.'
)


def _build_user_msg(desc_en: str, desc_fr: Optional[str], food_group: str,
                    is_recipe_compilation: bool) -> str:
    lean = _GROUP_LEAN.get(food_group)
    ctx = [f'EN: {desc_en}']
    if desc_fr and desc_fr != desc_en:
        ctx.append(f'FR: {desc_fr}')
    ctx.append(f'CNF food group: {food_group}'
               + (f' (foods in this group are {lean})' if lean else ''))
    if is_recipe_compilation:
        ctx.append('SOURCE FLAG: this food is a "CNF recipe compilation" — a strong '
                   'signal it is a MIXED dish (its nutrients were computed from a recipe).')
    return (
        'Food to classify:\n' + '\n'.join(ctx) + '\n\n'
        'Decide single vs mixed. JSON schema:\n'
        '{"food_type": "single"|"mixed", "confidence": <float in [0,1]>, '
        '"rationale": "<one short sentence>"}\n\n'
        'Confidence anchors (vary your estimate; do not default to 0.5 or 0.8):\n'
        '  0.97 = unambiguous (a raw apple; a pepperoni pizza)\n'
        '  0.85 = clear, with a minor wrinkle (cooked seasoned chicken breast = single; '
        'a plain bread roll = mixed)\n'
        '  0.65 = a real judgment call (a flavoured yogurt; a seasoned rice mix)\n'
        '  0.50 = genuinely ambiguous from the description alone\n'
    )


def _load_cnf_foods() -> List[Dict]:
    """Load every CNF FoodID with EN/FR descriptions, group name, and source id."""
    import dish_project.env_bootstrap  # noqa: F401 -- ensure .env is loaded
    os.environ.setdefault('DJANGO_SECRET_KEY', 'etl-food-type')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
    import django
    django.setup()
    from api.cnf_cache import get_api_cnf_pipeline
    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    fg = pipe.food_group_df
    merged = fn.merge(fg[['FoodGroupID', 'FoodGroupName']], on='FoodGroupID', how='left')
    fr_col = 'FoodDescriptionF' if 'FoodDescriptionF' in merged.columns else None
    has_source = 'FoodSourceID' in merged.columns
    rows = []
    for _, row in merged.iterrows():
        try:
            src = int(row['FoodSourceID']) if has_source and pd.notna(row['FoodSourceID']) else None
        except Exception:  # noqa: BLE001
            src = None
        rows.append({
            'food_id': int(row['FoodID']),
            'desc_en': str(row['FoodDescription']),
            'desc_fr': str(row[fr_col]) if fr_col and pd.notna(row[fr_col]) else None,
            'food_group': str(row.get('FoodGroupName', '') or ''),
            'is_recipe_compilation': src == _RECIPE_COMPILATION_SOURCE_ID,
        })
    logger.info('Loaded %d CNF foods', len(rows))
    return rows


def _classify_with_llm(client, food: Dict) -> Optional[Dict]:
    """Return {'food_type', 'confidence', 'rationale'} or None on failure."""
    user_msg = _build_user_msg(food['desc_en'], food['desc_fr'], food['food_group'],
                               food['is_recipe_compilation'])
    try:
        resp = client.chat.completions.create(
            model=CLASSIFY_MODEL,
            messages=[{'role': 'system', 'content': _SYSTEM_MSG},
                      {'role': 'user', 'content': user_msg}],
            temperature=CLASSIFY_TEMPERATURE,
            response_format={'type': 'json_object'},
            max_tokens=150,
        )
        try:
            _TOKEN_USAGE['prompt'] += int(getattr(resp.usage, 'prompt_tokens', 0) or 0)
            _TOKEN_USAGE['completion'] += int(getattr(resp.usage, 'completion_tokens', 0) or 0)
        except Exception:  # noqa: BLE001
            pass
        parsed = json.loads(resp.choices[0].message.content)
        ftype = str(parsed.get('food_type', '')).strip().lower()
        if ftype not in ('single', 'mixed'):
            logger.warning('food_id=%d got invalid food_type=%r', food['food_id'], ftype)
            return None
        conf = float(parsed.get('confidence', 0.0))
        conf = max(0.0, min(1.0, conf))
        rationale = str(parsed.get('rationale', ''))[:300]
        return {'food_type': ftype, 'confidence': round(conf, 3), 'rationale': rationale}
    except Exception as exc:  # noqa: BLE001
        logger.warning('LLM classification failed for food_id=%d: %s', food['food_id'], exc)
        return None


def _content_hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def _load_existing() -> Tuple[Dict[str, Dict], List[int]]:
    """Resume support: (labels_dict, failed_list) from a partial JSON, else ({}, [])."""
    if not _OUT_PATH.exists():
        return {}, []
    try:
        d = json.loads(_OUT_PATH.read_text(encoding='utf-8'))
        return d.get('labels', {}), d.get('failed', [])
    except Exception as exc:  # noqa: BLE001
        logger.warning('Existing food-type JSON unreadable, starting fresh: %s', exc)
        return {}, []


def _save(labels: Dict[str, Dict], failed: List[int], cnf_total: int) -> None:
    n_single = sum(1 for v in labels.values() if v.get('food_type') == 'single')
    n_mixed = sum(1 for v in labels.values() if v.get('food_type') == 'mixed')
    n_low_conf = sum(1 for v in labels.values() if float(v.get('confidence', 1.0)) < 0.6)
    out = {
        '_provenance': {
            'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'classify_model': CLASSIFY_MODEL,
            'temperature': CLASSIFY_TEMPERATURE,
            'recipe_compilation_source_id': _RECIPE_COMPILATION_SOURCE_ID,
            'cnf_total': cnf_total,
            'labeled': len(labels),
            'single': n_single,
            'mixed': n_mixed,
            'low_confidence': n_low_conf,
            'failed': len(failed),
            'note': (
                'food_type is "single" (one ingredient as eaten, incl. cooked/minimally '
                'processed) or "mixed" (composite dish / multi-ingredient product). '
                'Consumed by api.services.cnf_food_type and the recipe decomposer to gate '
                'the catalog-override onto measured mixed dishes only. Covers both CNF and '
                'WAFCT (FoodID >= 700000) foods unless built with --cnf-only.'
            ),
        },
        'labels': labels,
        'failed': sorted(failed),
    }
    serialised = json.dumps(out, indent=2, ensure_ascii=False)
    _OUT_PATH.write_text(serialised, encoding='utf-8')
    _META_PATH.write_text(json.dumps({
        'date_utc': out['_provenance']['date_utc'],
        'content_sha256_16': _content_hash(serialised),
        'labeled': len(labels),
        'single': n_single,
        'mixed': n_mixed,
        'low_confidence': n_low_conf,
        'failed': len(failed),
    }, indent=2), encoding='utf-8')


def main(limit: Optional[int] = None,
         food_ids: Optional[List[int]] = None,
         workers: int = 8,
         cnf_only: bool = False) -> int:
    _here = Path(__file__).resolve()
    backend_dir = _here.parents[3]  # api/services/etl -> backend
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    import dish_project.env_bootstrap  # noqa: F401 -- loads backend/.env

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error('OPENAI_API_KEY not set; aborting')
        return 1
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    cnf_foods = _load_cnf_foods()
    # By default label BOTH CNF and WAFCT (FoodID >= 700000): West African composite
    # dishes (porridges, stews, sauces) are exactly the foods the catalog-override gate
    # should be allowed to fire on, so they need labels too. --cnf-only restores the
    # original CNF-only pass (leaving WAFCT unlabeled -> override never fires on them).
    if cnf_only:
        cnf_foods = [c for c in cnf_foods if c['food_id'] < 700000]
        logger.info('cnf-only: WAFCT foods (>=700000) excluded')
    if food_ids:
        wanted = set(food_ids)
        cnf_foods = [c for c in cnf_foods if c['food_id'] in wanted]
        logger.info('food_ids filter: classifying %d targeted CNF foods', len(cnf_foods))
    elif limit:
        cnf_foods = cnf_foods[:limit]
        logger.info('limit=%d: classifying first %d CNF foods only', limit, len(cnf_foods))

    labels, failed = _load_existing()
    skip_set = set(int(k) for k in labels.keys()) | set(failed)
    to_process = [c for c in cnf_foods if c['food_id'] not in skip_set]
    logger.info('Resuming: %d already labeled, %d already failed; %d to process',
                len(labels), len(failed), len(to_process))

    save_interval = 100
    workers = max(1, int(workers))
    logger.info('Classifying with %d concurrent worker(s)', workers)
    i = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_classify_with_llm, client, food): food for food in to_process}
        for fut in as_completed(futs):
            food = futs[fut]
            result = fut.result()
            with _RESULTS_LOCK:
                i += 1
                if result is None:
                    failed.append(food['food_id'])
                else:
                    labels[str(food['food_id'])] = result
                    if i <= 10 or i % 200 == 0:
                        logger.info('[%s] cnf=%d "%s" conf=%.2f — %s',
                                    result['food_type'], food['food_id'], food['desc_en'][:40],
                                    result['confidence'], result['rationale'][:60])
                if i % save_interval == 0:
                    _save(labels, failed, len(cnf_foods))
                    logger.info('progress: %d / %d processed (%d labeled, %d failed); spent=$%.4f',
                                i, len(to_process), len(labels), len(failed),
                                _accumulated_cost_usd())

    _save(labels, failed, len(cnf_foods))
    _log_cost_projection(processed=len(to_process), remaining=0)
    logger.info('DONE. labeled=%d failed=%d out=%s', len(labels), len(failed), _OUT_PATH)
    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None,
                   help='Classify only the first N CNF foods (for smoke testing)')
    p.add_argument('--food-ids', type=str, default=None,
                   help='Classify only these CNF FoodIDs (comma-separated)')
    p.add_argument('--workers', type=int, default=8,
                   help='Concurrent OpenAI workers (default 8; calls release the GIL)')
    p.add_argument('--cnf-only', action='store_true',
                   help='Label only CNF foods, leaving WAFCT (>=700000) unlabeled '
                        '(default labels both)')
    args = p.parse_args()
    fids = None
    if args.food_ids:
        fids = [int(x.strip()) for x in args.food_ids.split(',') if x.strip()]
    sys.exit(main(limit=args.limit, food_ids=fids, workers=args.workers,
                  cnf_only=args.cnf_only))
