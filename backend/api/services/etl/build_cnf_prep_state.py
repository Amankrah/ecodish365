"""One-time ETL: classify every CNF + WAFCT FoodID with a two-axis
preparation-state tag (thermal_state, preservation_state).

Mirrors ``build_cnf_food_type.py`` exactly — same loader, same resumable
JSON pattern, same provenance meta — but the classification axis is
preparation state instead of single/mixed.

This is the **hybrid** tagger the lab plan calls for:
  1. Regex prior (``api.services.prep_state_extract.extract_prep_state``)
     resolves any row whose CNF description text encodes both axes
     explicitly. ~50% of foods at confidence 1.0 — no LLM call needed.
  2. LLM fallback (gpt-4.1-mini, JSON-only) handles the rest. The regex
     partial is passed as a HINT, but the LLM is free to override it
     when description context suggests otherwise (e.g. "Sweets, pie
     fillings, canned apple" → thermal=cooked, not the regex-default
     'unknown').

Output schema per food:
  {
    "thermal_state":      one of THERMAL_STATES,
    "preservation_state": one of PRESERVATION_STATES,
    "confidence":         float 0-1,
    "source":             "regex" | "llm" | "llm_overrode_regex",
    "rationale":          short string (LLM-supplied or "regex:<terms>"),
  }

Reads (via the shared CNF pipeline):
    food_name_df (FoodID, FoodDescription, FoodDescriptionF, FoodGroupID)
    food_group_df (FoodGroupID -> FoodGroupName)

Writes:
    api/data/cnf_prep_state.json       {labels: {food_id: {...}}, failed: [...]}
    api/data/cnf_prep_state_meta.json  (sha, counts, provenance)

Cost (estimated):
  ~7,021 foods total
  ~50% regex-conf-1.0 → ~3,500 skip LLM (free)
  ~3,500 × ~500 tokens × $0.40 / 1M ≈ ~$0.70

Usage (one-time, requires OPENAI_API_KEY; from backend/):
    python -m api.services.etl.build_cnf_prep_state
    python -m api.services.etl.build_cnf_prep_state --limit 50  # smoke test
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

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_OUT_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cnf_prep_state.json'
_META_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cnf_prep_state_meta.json'

CLASSIFY_MODEL = 'gpt-4.1-mini'
CLASSIFY_TEMPERATURE = 0.0

# Pricing snapshot (USD per 1M tokens). Match build_cnf_food_type.py.
_PRICE_PROMPT_PER_1M = 0.150
_PRICE_COMPLETION_PER_1M = 0.600
_TOKEN_USAGE: Dict[str, int] = {'prompt': 0, 'completion': 0}
_RESULTS_LOCK = threading.Lock()


def _accumulated_cost_usd() -> float:
    return (
        _TOKEN_USAGE['prompt'] / 1_000_000 * _PRICE_PROMPT_PER_1M
        + _TOKEN_USAGE['completion'] / 1_000_000 * _PRICE_COMPLETION_PER_1M
    )


# Allowed values exposed for the LLM prompt. Mirrors PrepState enums in
# prep_state_extract. The LLM MUST pick one of these.
_THERMAL_VALUES_PROMPT = (
    'raw, boiled, fried, baked, roasted, stewed, grilled, steamed, poached, '
    'scrambled, heated, cooked, braised, toasted, sauteed, microwaved, '
    'blanched, barbecued, stir_fried, broiled, reheated, unknown'
)
_PRESERVATION_VALUES_PROMPT = (
    'fresh, canned, dried, dehydrated, frozen, salted, smoked, cured, '
    'pickled, fermented, condensed, ready_to_eat, unknown'
)


_SYSTEM_MSG = (
    "You label a Canadian Nutrient File / WAFCT food with its preparation "
    "state along two axes — thermal_state (how it was cooked, if at all) and "
    "preservation_state (how it was stored / processed) — for a "
    "substitution / decomposition pipeline that needs to know whether two "
    "foods are nutritionally interchangeable.\n\n"
    "thermal_state must be EXACTLY one of: " + _THERMAL_VALUES_PROMPT + "\n"
    "preservation_state must be EXACTLY one of: " + _PRESERVATION_VALUES_PROMPT + "\n\n"
    "Rules:\n"
    "  - thermal=raw means the food was not heated (or 'unheated', 'uncooked', or never cooked).\n"
    "  - thermal=cooked is the generic fallback when the description implies cooking "
    "but doesn't specify how (use a more specific verb if the description names one).\n"
    "  - thermal=unknown is correct for ingredients with no thermal context "
    "(e.g. fresh fluid milk, plain herbs, bread without a specific verb).\n"
    "  - preservation=fresh is the default for foods that are neither preserved "
    "nor explicitly canned/dried/frozen — including pasteurized fluid dairy.\n"
    "  - preservation=fermented covers yogurt, kefir, fermented cassava (fufu), "
    "kenkey, ogi, kombucha — even when fresh.\n"
    "  - preservation=condensed covers evaporated milk / condensed milk / "
    "concentrated juice (water-removed but still wet).\n"
    "  - preservation=ready_to_eat covers ready-to-eat cereals and similar "
    "shelf-stable processed packaged foods.\n"
    "  - composite dishes (soup, stew, pie, sandwich) almost always have "
    "thermal=cooked even when the description doesn't name a verb.\n"
    "Respond with JSON only."
)


def _build_user_msg(desc_en: str, desc_fr: Optional[str], food_group: str,
                    regex_thermal: str, regex_preservation: str,
                    regex_confidence: float) -> str:
    ctx = [f'EN: {desc_en}']
    if desc_fr and desc_fr != desc_en:
        ctx.append(f'FR: {desc_fr}')
    ctx.append(f'CNF food group: {food_group}')
    ctx.append(
        f'Regex prior (may be wrong, you decide): '
        f'thermal_state={regex_thermal}, preservation_state={regex_preservation} '
        f'(prior confidence {regex_confidence:.2f})'
    )
    return (
        'Food to classify:\n' + '\n'.join(ctx) + '\n\n'
        'Return JSON: {"thermal_state": "...", "preservation_state": "...", '
        '"confidence": <float 0-1>, "rationale": "<one short sentence>"}.\n\n'
        'Confidence anchors (vary your estimate; do not default to a single value):\n'
        '  0.97 = unambiguous (a raw apple; canned tuna)\n'
        '  0.85 = clear with a minor wrinkle (sliced cooked apple; smoked salmon)\n'
        '  0.65 = a real judgment call (a generic cereal name; a fast-food item without verb)\n'
        '  0.50 = genuinely ambiguous from the description alone\n'
    )


def _load_cnf_foods() -> List[Dict]:
    """Load every CNF + WAFCT FoodID with bilingual description and group name."""
    import dish_project.env_bootstrap  # noqa: F401
    os.environ.setdefault('DJANGO_SECRET_KEY', 'etl-prep-state')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
    import django
    django.setup()
    from api.cnf_cache import get_api_cnf_pipeline
    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    fg = pipe.food_group_df
    merged = fn.merge(fg[['FoodGroupID', 'FoodGroupName']], on='FoodGroupID', how='left')
    fr_col = 'FoodDescriptionF' if 'FoodDescriptionF' in merged.columns else None
    rows = []
    for _, row in merged.iterrows():
        rows.append({
            'food_id': int(row['FoodID']),
            'desc_en': str(row['FoodDescription']),
            'desc_fr': str(row[fr_col]) if fr_col and pd.notna(row[fr_col]) else None,
            'food_group': str(row.get('FoodGroupName', '') or ''),
        })
    logger.info('Loaded %d CNF+WAFCT foods', len(rows))
    return rows


def _classify_with_llm(client, food: Dict, regex_thermal: str, regex_preservation: str,
                       regex_confidence: float) -> Optional[Dict]:
    """Return the LLM tag dict or None on failure."""
    from api.services.prep_state_extract import THERMAL_STATES, PRESERVATION_STATES
    user_msg = _build_user_msg(
        food['desc_en'], food['desc_fr'], food['food_group'],
        regex_thermal, regex_preservation, regex_confidence,
    )
    try:
        resp = client.chat.completions.create(
            model=CLASSIFY_MODEL,
            messages=[{'role': 'system', 'content': _SYSTEM_MSG},
                      {'role': 'user', 'content': user_msg}],
            temperature=CLASSIFY_TEMPERATURE,
            response_format={'type': 'json_object'},
            max_tokens=180,
        )
        try:
            _TOKEN_USAGE['prompt'] += int(getattr(resp.usage, 'prompt_tokens', 0) or 0)
            _TOKEN_USAGE['completion'] += int(getattr(resp.usage, 'completion_tokens', 0) or 0)
        except Exception:  # noqa: BLE001
            pass
        parsed = json.loads(resp.choices[0].message.content)
        t = str(parsed.get('thermal_state', '')).strip().lower()
        p = str(parsed.get('preservation_state', '')).strip().lower()
        # Synonym remap for common LLM near-misses on the enum lists. Keeps the
        # tagger robust to model variance without bloating the canonical enums.
        _THERMAL_SYNONYMS = {'puffed': 'popped', 'infused': 'brewed'}
        _PRESERVATION_SYNONYMS = {
            'dry': 'dried', 'powdered': 'dried', 'powder': 'dried',
            'raw': 'fresh',           # raw is thermal, not preservation
            'aged_cured': 'aged',
        }
        t = _THERMAL_SYNONYMS.get(t, t)
        p = _PRESERVATION_SYNONYMS.get(p, p)
        if t not in THERMAL_STATES:
            logger.warning('food_id=%d invalid thermal_state=%r', food['food_id'], t)
            return None
        if p not in PRESERVATION_STATES:
            logger.warning('food_id=%d invalid preservation_state=%r', food['food_id'], p)
            return None
        conf = float(parsed.get('confidence', 0.0))
        conf = max(0.0, min(1.0, conf))
        rationale = str(parsed.get('rationale', ''))[:300]
        return {
            'thermal_state': t,
            'preservation_state': p,
            'confidence': round(conf, 3),
            'rationale': rationale,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning('LLM classification failed for food_id=%d: %s', food['food_id'], exc)
        return None


def _classify_one(client, food: Dict, llm_threshold: float) -> Tuple[int, Optional[Dict]]:
    """Hybrid classify. Returns (food_id, tag_dict or None)."""
    from api.services.prep_state_extract import extract_prep_state
    desc = food['desc_en'] or ''
    rps = extract_prep_state(desc)

    if rps.confidence >= llm_threshold:
        # Regex prior is strong (both axes resolved by explicit terms).
        return food['food_id'], {
            'thermal_state': rps.thermal_state,
            'preservation_state': rps.preservation_state,
            'confidence': round(rps.confidence, 3),
            'source': 'regex',
            'rationale': 'regex:' + ','.join(rps.matched_terms),
        }

    # LLM fallback. Pass regex partial as a hint.
    llm = _classify_with_llm(
        client, food,
        regex_thermal=rps.thermal_state,
        regex_preservation=rps.preservation_state,
        regex_confidence=rps.confidence,
    )
    if llm is None:
        return food['food_id'], None
    overrode = (rps.thermal_state != 'unknown' and llm['thermal_state'] != rps.thermal_state) \
        or (rps.preservation_state != 'unknown' and llm['preservation_state'] != rps.preservation_state)
    return food['food_id'], {
        'thermal_state': llm['thermal_state'],
        'preservation_state': llm['preservation_state'],
        'confidence': llm['confidence'],
        'source': 'llm_overrode_regex' if overrode else 'llm',
        'rationale': llm['rationale'],
    }


def _content_hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def _load_existing() -> Tuple[Dict[str, Dict], List[int]]:
    if not _OUT_PATH.exists():
        return {}, []
    try:
        d = json.loads(_OUT_PATH.read_text(encoding='utf-8'))
        return d.get('labels', {}), d.get('failed', [])
    except Exception as exc:  # noqa: BLE001
        logger.warning('Existing prep-state JSON unreadable, starting fresh: %s', exc)
        return {}, []


def _save(labels: Dict[str, Dict], failed: List[int], cnf_total: int) -> None:
    # Counts by source
    n_regex = sum(1 for v in labels.values() if v.get('source') == 'regex')
    n_llm = sum(1 for v in labels.values() if v.get('source') == 'llm')
    n_llm_over = sum(1 for v in labels.values() if v.get('source') == 'llm_overrode_regex')
    # Axis coverage
    n_both_known = sum(1 for v in labels.values()
                       if v.get('thermal_state') != 'unknown'
                       and v.get('preservation_state') != 'unknown')
    n_low_conf = sum(1 for v in labels.values()
                     if float(v.get('confidence', 1.0)) < 0.6)
    out = {
        '_provenance': {
            'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'classify_model': CLASSIFY_MODEL,
            'temperature': CLASSIFY_TEMPERATURE,
            'cnf_total': cnf_total,
            'labeled': len(labels),
            'by_source': {'regex': n_regex, 'llm': n_llm, 'llm_overrode_regex': n_llm_over},
            'both_axes_known': n_both_known,
            'low_confidence': n_low_conf,
            'failed': len(failed),
            'note': (
                'Two-axis preparation-state tag per CNF/WAFCT FoodID. Hybrid '
                'classification: regex prior at confidence 1.0 takes precedence; '
                'gpt-4.1-mini LLM handles the rest (with regex partial as a hint). '
                'Consumed by api.services.cnf_prep_state and the substitution '
                'culinary gate (Strategy D).'
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
        'by_source': out['_provenance']['by_source'],
        'both_axes_known': n_both_known,
        'low_confidence': n_low_conf,
        'failed': len(failed),
    }, indent=2), encoding='utf-8')


def main(limit: Optional[int] = None,
         food_ids: Optional[List[int]] = None,
         workers: int = 8,
         llm_threshold: float = 1.0) -> int:
    """Run the hybrid tagger.

    Args:
      limit: process only the first N foods (for smoke tests).
      food_ids: process only these explicit FoodIDs.
      workers: concurrent OpenAI threads.
      llm_threshold: regex confidence at-or-above which we skip the LLM.
                     1.0 is strict (only both-axes-resolved rows skip LLM);
                     0.7 would also skip rows where one axis was resolved by
                     regex (more LLM savings, more chance of regex mis-prior).
    """
    _here = Path(__file__).resolve()
    backend_dir = _here.parents[3]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    import dish_project.env_bootstrap  # noqa: F401

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error('OPENAI_API_KEY not set; aborting')
        return 1
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    foods = _load_cnf_foods()
    if food_ids:
        wanted = set(food_ids)
        foods = [c for c in foods if c['food_id'] in wanted]
        logger.info('food_ids filter: tagging %d targeted foods', len(foods))
    elif limit:
        foods = foods[:limit]
        logger.info('limit=%d: tagging first %d foods only', limit, len(foods))

    labels, failed = _load_existing()
    skip_set = set(int(k) for k in labels.keys()) | set(failed)
    to_process = [c for c in foods if c['food_id'] not in skip_set]
    logger.info('Resuming: %d already labeled, %d already failed; %d to process',
                len(labels), len(failed), len(to_process))

    save_interval = 100
    workers = max(1, int(workers))
    logger.info('Tagging with %d concurrent worker(s) (llm_threshold=%.2f)',
                workers, llm_threshold)
    i = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_classify_one, client, food, llm_threshold): food
                for food in to_process}
        for fut in as_completed(futs):
            food = futs[fut]
            food_id, result = fut.result()
            with _RESULTS_LOCK:
                i += 1
                if result is None:
                    failed.append(food_id)
                else:
                    labels[str(food_id)] = result
                    if i <= 10 or i % 250 == 0:
                        logger.info('[%s] cnf=%d "%s" t=%s p=%s conf=%.2f',
                                    result['source'], food_id, food['desc_en'][:40],
                                    result['thermal_state'], result['preservation_state'],
                                    result['confidence'])
                if i % save_interval == 0:
                    _save(labels, failed, len(foods))
                    logger.info('progress: %d / %d (%d labeled, %d failed); spent=$%.4f',
                                i, len(to_process), len(labels), len(failed),
                                _accumulated_cost_usd())

    _save(labels, failed, len(foods))
    n_regex = sum(1 for v in labels.values() if v.get('source') == 'regex')
    n_llm = sum(1 for v in labels.values() if v.get('source') in ('llm', 'llm_overrode_regex'))
    logger.info('DONE. labeled=%d (regex=%d, llm=%d) failed=%d cost=$%.4f',
                len(labels), n_regex, n_llm, len(failed), _accumulated_cost_usd())
    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--food-ids', type=str, default=None,
                   help='Comma-separated FoodIDs to tag')
    p.add_argument('--workers', type=int, default=8)
    p.add_argument('--llm-threshold', type=float, default=1.0,
                   help='Regex confidence at-or-above which to skip the LLM (default 1.0)')
    args = p.parse_args()
    fids = None
    if args.food_ids:
        fids = [int(x.strip()) for x in args.food_ids.split(',') if x.strip()]
    sys.exit(main(limit=args.limit, food_ids=fids, workers=args.workers,
                  llm_threshold=args.llm_threshold))
