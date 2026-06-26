"""One-time ETL: CNF FoodID -> BNS subgroup bridge via retrieval + LLM ranking.

PLATFORM-CODE-1.m m.B (2026-06-26).

Mirrors the [`build_cnf_to_fndds_bridge`](backend/heni_calculator/heni/etl/build_cnf_to_fndds_bridge.py)
shape (text-embedding-3-small retrieval + gpt-4.1-mini constrained-JSON
ranking) but the target space is the ~180 Health Canada BNS subgroup
codes that key the CCHS-FCT 2015 published intake distributions.

Key difference from the FNDDS bridge: we exploit the canonical-category
shim from [`food_group_category`](backend/api/services/food_group_category.py)
to PRE-FILTER candidate BNS subgroups before LLM ranking. A CNF "dairy"
food only ever needs to be ranked against Dairy Products BNS subgroups
(`9A` through `15X`), not the full 180. This cuts LLM token cost ~10x
and tightens accuracy (the LLM cannot accidentally pick a `2A WHITE
BREAD` for a milk product).

Usage (one-time, requires OPENAI_API_KEY):

    cd backend
    python -m api.services.etl.build_cnf_to_bns_bridge
    python -m api.services.etl.build_cnf_to_bns_bridge --limit 50         # smoke / dry-run
    python -m api.services.etl.build_cnf_to_bns_bridge --food-ids 61,4067 # targeted refresh
    python -m api.services.etl.build_cnf_to_bns_bridge --checkpoint-at 100

Inputs:
    backend/api/data/cchs_fct_2015.json                 (built by cchs_fct_ingest.py)
    backend/api/data/food_group_canonical_category.json (existing canonical-category bridge)

Outputs (derived artifact, kept under api/data/ next to the loader):
    backend/api/data/cnf_to_bns_subgroup_bridge.json
    backend/api/data/bns_subgroup_embeddings.npz        (cached for re-runs)

Resumable: saves every 100 CNF foods so a crashed run can resume. Idempotent:
re-running with an existing bridge JSON skips already-bridged CNF foods.

Cost (estimated, 2026-06-26):
    Embedding ~180 BNS subgroup descriptions ≈ <1k tokens, free.
    LLM ranking: ~5,900 CNF foods x ~400 tokens prompt + ~80 tokens response
                 (smaller prompts than FNDDS thanks to pre-filter)
                 ≈ ~2.8M tokens ≈ $0.60 (gpt-4.1-mini at $0.15 / $0.60 per 1M).
    Total: $1-2 one-time.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[3]
_DATA_DIR = _BACKEND_ROOT / 'api' / 'data'
_BRIDGE_PATH = _DATA_DIR / 'cnf_to_bns_subgroup_bridge.json'
_OVERRIDES_PATH = _DATA_DIR / 'cnf_to_bns_subgroup_bridge_overrides.json'
_EMBEDDINGS_PATH = _DATA_DIR / 'bns_subgroup_embeddings.npz'

EMBEDDING_MODEL = 'text-embedding-3-small'
RANKING_MODEL = 'gpt-4.1-mini'
TOP_K = 8
MIN_BRIDGE_CONFIDENCE = 0.5
RANKING_TEMPERATURE = 0.0
EMBED_BATCH_SIZE = 256
PARALLELISM = 8   # concurrent (embed + LLM-rank) jobs; OpenAI handles 8 fine

# Pricing snapshot for cost projection. USD per 1M tokens. Update on rate changes.
_PRICE_EMBED_PER_1M = 0.020
_PRICE_RANK_PROMPT_PER_1M = 0.150
_PRICE_RANK_COMPLETION_PER_1M = 0.600

_TOKEN_USAGE: Dict[str, int] = {
    'embed_prompt': 0,
    'rank_prompt': 0,
    'rank_completion': 0,
}
_TOKEN_USAGE_LOCK = threading.Lock()


# Canonical category -> set of CCHS-FCT main_group labels worth searching.
# Wide is fine — we rely on the LLM rank to pick the precise subgroup;
# the goal of the pre-filter is to cut the candidate set from 180 to
# ~10-25, not to lock the answer.
_CATEGORY_TO_MAIN_GROUPS: Dict[str, Tuple[str, ...]] = {
    'dairy':                ('Dairy Products',),
    'eggs':                 ('Meat alternatives', 'Dairy Products'),
    'dairy_egg_combined':   ('Dairy Products', 'Meat alternatives'),
    'fats_oils':            ('Fats',),
    'fruits':               ('Fruits', 'Babyfood'),
    'vegetables':           ('Vegetables', 'Babyfood'),
    'legumes':              ('Meat alternatives',),
    'nuts_seeds':           ('Meat alternatives',),
    'cereals_grains':       ('Grain Products', 'Babyfood'),
    'breakfast_cereals':    ('Grain Products',),
    'beef':                 ('Meats',),
    'pork':                 ('Meats',),
    'lamb_veal_game':       ('Meats',),
    'poultry':              ('Meats',),
    'fish':                 ('Meats', 'Meat alternatives'),
    'sausages_luncheon':    ('Meats',),
    'beverages':            ('Beverages',),
    'alcoholic_beverages':  ('Beverages',),
    'sweets':               ('Miscellaneous',),
    'babyfoods':            ('Babyfood',),
    'baked_products':       ('Grain Products', 'Miscellaneous'),
    'fast_foods':           ('Miscellaneous', 'Meats', 'Grain Products'),
    'mixed_dishes':         ('Miscellaneous', 'Meats', 'Grain Products'),
    'snacks':               ('Miscellaneous', 'Grain Products'),
    'soups_sauces':         ('Miscellaneous',),
    'spices_herbs':         ('Miscellaneous',),
    'unknown':              ('Grain Products', 'Dairy Products', 'Fats', 'Meats',
                             'Meat alternatives', 'Vegetables', 'Fruits',
                             'Beverages', 'Babyfood', 'Miscellaneous'),
}


def _accumulated_cost_usd() -> float:
    return (
        _TOKEN_USAGE['embed_prompt'] / 1_000_000 * _PRICE_EMBED_PER_1M
        + _TOKEN_USAGE['rank_prompt'] / 1_000_000 * _PRICE_RANK_PROMPT_PER_1M
        + _TOKEN_USAGE['rank_completion'] / 1_000_000 * _PRICE_RANK_COMPLETION_PER_1M
    )


def _log_cost_projection(processed: int, remaining: int) -> None:
    spent = _accumulated_cost_usd()
    per_food = spent / max(1, processed)
    projected_total = spent + per_food * remaining
    logger.info(
        'COST CHECKPOINT: processed=%d, spent=$%.4f, per-food=$%.5f, '
        'remaining=%d, projected-additional=$%.4f, projected-total=$%.4f '
        '(embed=%d, rank-prompt=%d, rank-completion=%d tokens)',
        processed, spent, per_food, remaining, per_food * remaining, projected_total,
        _TOKEN_USAGE['embed_prompt'], _TOKEN_USAGE['rank_prompt'],
        _TOKEN_USAGE['rank_completion'],
    )


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return v / n


def _embed_batch(client, texts: List[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    try:
        with _TOKEN_USAGE_LOCK:
            _TOKEN_USAGE['embed_prompt'] += int(getattr(resp.usage, 'prompt_tokens', 0) or 0)
    except Exception:  # noqa: BLE001
        pass
    return np.array([d.embedding for d in resp.data], dtype=np.float32)


# ---------- BNS subgroup catalogue + embeddings --------------------------

def _load_bns_subgroups() -> List[Dict[str, Any]]:
    """Load every BNS subgroup that is a valid bridge TARGET. Excludes the
    compound OVERALL roll-ups (e.g. `1 to 8 GRAIN PRODUCTS - OVERALL`)
    since those are aggregate rows in the FCT, not bridgeable subgroups."""
    from api.services.cchs_fct_loader import list_subgroups, subgroup_meta
    rows = list_subgroups()
    out: List[Dict[str, Any]] = []
    for r in rows:
        code = r['code']
        meta = subgroup_meta(code)
        if meta is None:
            # Codes in the consumption table without an entry in the
            # subgroup-list sheet are the OVERALL roll-ups. Skip.
            continue
        out.append({
            'code':         code,
            'name':         meta.get('name') or r.get('name'),
            'description':  meta.get('description') or '',
            'notes':        meta.get('notes') or '',
            'main_group':   meta.get('main_group') or r.get('main_group'),
        })
    logger.info('Loaded %d BNS subgroups eligible for bridging (excludes OVERALL rollups)', len(out))
    return out


def _bns_query_string(bns: Dict[str, Any]) -> str:
    parts = [f"[{bns['code']}] {bns['name']}"]
    if bns.get('description'):
        parts.append(bns['description'])
    if bns.get('main_group'):
        parts.append(f"BNS main group: {bns['main_group']}")
    return ' | '.join(parts)


def _build_or_load_bns_embeddings(client, bns_list: List[Dict[str, Any]]) -> np.ndarray:
    """Embed all BNS subgroup descriptions (cached on disk)."""
    if _EMBEDDINGS_PATH.exists():
        d = np.load(_EMBEDDINGS_PATH)
        if d['embeddings'].shape[0] == len(bns_list):
            logger.info('Loaded cached BNS embeddings (%d x %d)', *d['embeddings'].shape)
            return d['embeddings']
        logger.warning('Cached BNS embeddings shape mismatch (%d vs %d); re-embedding',
                       d['embeddings'].shape[0], len(bns_list))
    logger.info('Embedding %d BNS subgroup descriptions...', len(bns_list))
    queries = [_bns_query_string(b) for b in bns_list]
    emb = _embed_batch(client, queries)
    emb = _l2_normalize(emb)
    np.savez(_EMBEDDINGS_PATH, embeddings=emb)
    logger.info('Cached BNS embeddings to %s', _EMBEDDINGS_PATH)
    return emb


# ---------- CNF loader ---------------------------------------------------

def _load_cnf_foods() -> List[Dict[str, Any]]:
    """Load every CNF FoodID with English + French descriptions + group +
    canonical category. Restricts to the loadable CNF + WAFCT ID ranges
    (same convention as build_cnf_to_fndds_bridge)."""
    import dish_project.env_bootstrap  # noqa: F401
    os.environ.setdefault('DJANGO_SECRET_KEY', 'etl-cnf-bns-bridge')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
    import django
    django.setup()
    from api.cnf_cache import get_api_cnf_pipeline
    from api.services.food_group_category import canonical_category_for_food

    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    fg = pipe.food_group_df
    merged = fn.merge(fg[['FoodGroupID', 'FoodGroupName']], on='FoodGroupID', how='left')
    fr_col = 'FoodDescriptionF' if 'FoodDescriptionF' in merged.columns else None

    import pandas as pd
    rows: List[Dict[str, Any]] = []
    for _, row in merged.iterrows():
        try:
            fid = int(row['FoodID'])
        except (TypeError, ValueError):
            continue
        # Skip FDC / CIQUAL — they have their own bridges via shared codes
        # (FDC via FNDDS for the survey subset, CIQUAL via Agribalyse). The
        # BNS bridge is for the CNF + WAFCT IDs the cohort scorer surfaces.
        if not (1 <= fid <= 7021 or 700000 <= fid < 800000):
            continue
        desc_en = str(row.get('FoodDescription') or '').strip()
        if not desc_en:
            continue
        desc_fr = str(row[fr_col]) if (fr_col and pd.notna(row[fr_col])) else ''
        if desc_fr == desc_en:
            desc_fr = ''
        rows.append({
            'food_id':           fid,
            'desc_en':           desc_en,
            'desc_fr':           desc_fr,
            'food_group':        str(row.get('FoodGroupName') or '').strip(),
            'canonical_category': canonical_category_for_food(fid, pipeline=pipe),
        })
    logger.info('Loaded %d CNF/WAFCT foods for bridging', len(rows))
    return rows


def _cnf_query_string(cnf: Dict[str, Any]) -> str:
    parts = [f"CNF FoodID {cnf['food_id']}", f"EN: {cnf['desc_en']}"]
    if cnf['desc_fr']:
        parts.append(f"FR: {cnf['desc_fr']}")
    if cnf.get('food_group'):
        parts.append(f"CNF group: {cnf['food_group']}")
    if cnf.get('canonical_category'):
        parts.append(f"canonical: {cnf['canonical_category']}")
    return '\n'.join(parts)


# ---------- Per-food bridging --------------------------------------------

def _candidate_bns_for_cnf(
    cnf: Dict[str, Any],
    bns_list: List[Dict[str, Any]],
    bns_emb: np.ndarray,
    query_emb: np.ndarray,
) -> List[Dict[str, Any]]:
    """Apply canonical-category pre-filter, then cosine top-K rank.
    Returns the candidate BNS subgroup dicts in similarity-sorted order."""
    allowed_main = set(_CATEGORY_TO_MAIN_GROUPS.get(cnf.get('canonical_category') or 'unknown',
                                                     _CATEGORY_TO_MAIN_GROUPS['unknown']))
    candidate_idx = [i for i, b in enumerate(bns_list)
                     if (b.get('main_group') or '') in allowed_main]
    if not candidate_idx:
        # Pre-filter wiped the candidate list (e.g. unknown category, weird
        # main_group label) — fall back to the full set.
        candidate_idx = list(range(len(bns_list)))
    sub_emb = bns_emb[candidate_idx]
    sims = sub_emb @ query_emb
    k = min(TOP_K, len(candidate_idx))
    top_partial = np.argpartition(-sims, k - 1)[:k]
    top_sorted = top_partial[np.argsort(-sims[top_partial])]
    return [bns_list[candidate_idx[int(j)]] for j in top_sorted]


def _rank_with_llm(client, cnf: Dict[str, Any],
                   candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Ask the LLM to pick the best BNS subgroup. Returns
    `{bns_code, confidence, rationale}` or None on failure."""
    candidate_block = '\n'.join(
        f'  [{i}] code={c["code"]}  name="{c["name"]}"  '
        f'main="{c.get("main_group", "")}"  desc="{c.get("description", "")[:120]}"'
        for i, c in enumerate(candidates)
    )
    system_msg = (
        'You are bridging a Canadian Nutrient File (CNF) food to its best '
        'matching Health Canada BNS food subgroup, used as the bucket in '
        'the CCHS Nutrition 2015 Food Consumption Table. The BNS subgroups '
        'are at a finer granularity than CNF food groups (e.g. milk is '
        'split by fat % into 10A/B/C/D; bread is split by white/whole '
        'wheat into 2A/3A). Pick the most specific subgroup whose form, '
        'composition and preparation match the CNF food. If the CNF food '
        'is a raw ingredient used only in recipes (flour, raw grains, '
        'pure oils, gelatin) and no BNS subgroup represents it as eaten, '
        'return confidence below 0.5 so the food is left unbridged. '
        'Respond with JSON only.'
    )
    user_msg = (
        f'CNF food:\n{_cnf_query_string(cnf)}\n\n'
        f'Candidate BNS subgroups (top {len(candidates)} by embedding similarity):\n'
        f'{candidate_block}\n\n'
        'Pick the single best subgroup and report your confidence. JSON schema:\n'
        '{"bns_code": "<one of the candidate codes>", "confidence": <float in [0,1]>, '
        '"rationale": "<one short sentence>"}\n\n'
        'Confidence anchors:\n'
        '  0.90 = direct match (same food + same form + same composition tier)\n'
        '  0.70 = close match (same subgroup family; minor variant — fat %, salt %, '
        'fortification, preparation method)\n'
        '  0.50 = same broader BNS group but different specific subgroup\n'
        '  0.30 = no good match among the candidates; leave unbridged\n'
        'Pick the SINGLE best match. If two subgroups are equally plausible, prefer '
        'the more specific (the sub-letter code like 10D over the parent 10).'
    )
    try:
        resp = client.chat.completions.create(
            model=RANKING_MODEL,
            messages=[{'role': 'system', 'content': system_msg},
                      {'role': 'user', 'content': user_msg}],
            temperature=RANKING_TEMPERATURE,
            response_format={'type': 'json_object'},
            max_tokens=200,
        )
        try:
            with _TOKEN_USAGE_LOCK:
                _TOKEN_USAGE['rank_prompt'] += int(getattr(resp.usage, 'prompt_tokens', 0) or 0)
                _TOKEN_USAGE['rank_completion'] += int(getattr(resp.usage, 'completion_tokens', 0) or 0)
        except Exception:  # noqa: BLE001
            pass
        parsed = json.loads(resp.choices[0].message.content)
        bns_code = str(parsed.get('bns_code') or '').strip()
        conf = float(parsed.get('confidence', 0.0))
        rationale = str(parsed.get('rationale', ''))[:300]
        valid_codes = {c['code'] for c in candidates}
        if bns_code not in valid_codes:
            return {'bns_code': None, 'confidence': 0.0,
                    'rationale': f'LLM picked code={bns_code!r} not in candidate set'}
        return {'bns_code': bns_code, 'confidence': conf, 'rationale': rationale}
    except Exception as exc:  # noqa: BLE001
        logger.warning('LLM ranking failed for food_id=%s: %s', cnf['food_id'], exc)
        return None


# ---------- Bridge persistence -------------------------------------------

def _load_existing_bridge() -> Tuple[Dict[str, Dict[str, Any]], List[int]]:
    if not _BRIDGE_PATH.exists():
        return {}, []
    try:
        d = json.loads(_BRIDGE_PATH.read_text(encoding='utf-8'))
        return d.get('bridges', {}), d.get('unbridged', [])
    except Exception as exc:  # noqa: BLE001
        logger.warning('Existing bridge JSON unreadable, starting fresh: %s', exc)
        return {}, []


def _save_bridge(bridges: Dict[str, Dict[str, Any]], unbridged: List[int],
                 cnf_total: int, bns_total: int) -> None:
    out = {
        '_provenance': {
            'date_utc':              time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'embedding_model':       EMBEDDING_MODEL,
            'ranking_model':         RANKING_MODEL,
            'top_k':                 TOP_K,
            'min_bridge_confidence': MIN_BRIDGE_CONFIDENCE,
            'cnf_total':             cnf_total,
            'bns_total':             bns_total,
            'cnf_bridged':           len(bridges),
            'cnf_unbridged':         len(unbridged),
            'platform_item_id':      'PLATFORM-CODE-1.m',
        },
        'bridges':   bridges,
        'unbridged': sorted(unbridged),
    }
    _BRIDGE_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


def _ensure_overrides_sidecar() -> None:
    """Create an empty overrides sidecar if absent, so the loader has
    something to read on day one."""
    if _OVERRIDES_PATH.exists():
        return
    _OVERRIDES_PATH.write_text(json.dumps({
        '_doc': (
            'Hand-curated CNF FoodID -> BNS subgroup overrides. Loader gives '
            'these precedence over the LLM-ranked bridge. Format: '
            '{cnf_food_id_str: {"bns_code": "...", "confidence": 1.0, '
            '"rationale": "<reviewer note>", "source": "manual"}}'
        ),
        'overrides': {},
    }, indent=2), encoding='utf-8')
    logger.info('Initialised empty overrides sidecar at %s', _OVERRIDES_PATH)


# ---------- Main ---------------------------------------------------------

def main(limit: Optional[int] = None,
         food_ids: Optional[List[int]] = None,
         checkpoint_at: Optional[int] = None) -> int:
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

    _ensure_overrides_sidecar()
    bns_list = _load_bns_subgroups()
    cnf_foods = _load_cnf_foods()
    if food_ids:
        wanted = set(food_ids)
        cnf_foods = [c for c in cnf_foods if c['food_id'] in wanted]
        logger.info('food_ids filter: bridging %d targeted CNF foods', len(cnf_foods))
    elif limit:
        cnf_foods = cnf_foods[:limit]
        logger.info('limit=%d: bridging first %d CNF foods only', limit, len(cnf_foods))

    bns_emb = _build_or_load_bns_embeddings(client, bns_list)

    existing_bridges, existing_unbridged = _load_existing_bridge()
    bridges: Dict[str, Dict[str, Any]] = dict(existing_bridges)
    unbridged: List[int] = list(existing_unbridged)
    already_done: set = set(int(k) for k in bridges.keys()) | set(unbridged)
    queue = [c for c in cnf_foods if c['food_id'] not in already_done]
    logger.info('Bridging queue: %d remaining (%d previously bridged, %d previously unbridged)',
                len(queue), len(bridges), len(unbridged))

    # Parallel per-food fan-out. Per-food work is (embed query + LLM rank);
    # both API roundtrips are latency-bound, so PARALLELISM workers gives
    # roughly Nx throughput up to OpenAI's rate cap (8 concurrent is well
    # within limits for paid tiers). Results stream in via as_completed;
    # we save the bridge JSON every save_every completions.
    save_every = 100
    bridges_lock = threading.Lock()
    t_start = time.time()

    def _process_one(cnf: Dict[str, Any]) -> Tuple[int, Optional[Dict[str, Any]]]:
        """Embed + rank one CNF food. Returns (food_id, ranked_or_None)."""
        try:
            query_emb_arr = _embed_batch(client, [_cnf_query_string(cnf)])
            query_emb = _l2_normalize(query_emb_arr)[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning('Embed failed for food_id=%s: %s', cnf['food_id'], exc)
            return cnf['food_id'], None
        candidates = _candidate_bns_for_cnf(cnf, bns_list, bns_emb, query_emb)
        ranked = _rank_with_llm(client, cnf, candidates)
        return cnf['food_id'], ranked

    completed = 0
    with ThreadPoolExecutor(max_workers=PARALLELISM) as pool:
        futures = {pool.submit(_process_one, cnf): cnf for cnf in queue}
        for fut in as_completed(futures):
            fid, ranked = fut.result()
            with bridges_lock:
                if ranked is None or ranked['bns_code'] is None or ranked['confidence'] < MIN_BRIDGE_CONFIDENCE:
                    unbridged.append(fid)
                else:
                    bridges[str(fid)] = {
                        'bns_code':   ranked['bns_code'],
                        'confidence': round(ranked['confidence'], 3),
                        'rationale':  ranked['rationale'],
                        'source':     'llm',
                    }
                completed += 1
                if completed % 25 == 0:
                    elapsed = time.time() - t_start
                    rate = completed / max(1e-6, elapsed)
                    eta = (len(queue) - completed) / rate if rate > 0 else 0
                    logger.info('  %d / %d completed (%.1f /s; ETA %ds; bridged=%d, unbridged=%d)',
                                completed, len(queue), rate, int(eta), len(bridges), len(unbridged))
                if completed % save_every == 0:
                    _save_bridge(bridges, unbridged, len(cnf_foods), len(bns_list))
                if checkpoint_at is not None and completed >= checkpoint_at:
                    _log_cost_projection(processed=completed, remaining=len(queue) - completed)
                    _save_bridge(bridges, unbridged, len(cnf_foods), len(bns_list))
                    logger.info('--checkpoint-at reached; pausing. Re-run to resume.')
                    # Cancel remaining futures so the executor exits cleanly.
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    return 0

    _save_bridge(bridges, unbridged, len(cnf_foods), len(bns_list))
    _log_cost_projection(processed=len(queue), remaining=0)
    logger.info('DONE. Bridged %d / %d CNF foods (%.1f %% coverage).',
                len(bridges), len(cnf_foods), 100 * len(bridges) / max(1, len(cnf_foods)))
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None,
                        help='Bridge only the first N CNF foods (dry-run / smoke)')
    parser.add_argument('--food-ids', type=str, default=None,
                        help='Bridge only these CNF FoodIDs (comma-separated)')
    parser.add_argument('--checkpoint-at', type=int, default=None,
                        help='Pause + log cost projection after N processed; '
                             're-run to resume')
    args = parser.parse_args()
    fids = [int(x) for x in args.food_ids.split(',')] if args.food_ids else None
    sys.exit(main(limit=args.limit, food_ids=fids, checkpoint_at=args.checkpoint_at))
