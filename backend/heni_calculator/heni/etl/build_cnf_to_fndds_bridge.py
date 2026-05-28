"""One-time ETL: CNF FoodID -> FNDDS fdc_id bridge via retrieval + LLM ranking.

Mirrors the LCAMatcher pattern (text-embedding-3-small retrieval + gpt-4.1-mini
constrained-JSON ranking) used in section 3.5 for CNF -> AGRIBALYSE, but here
the target is FNDDS 2017-2018 survey foods. The bridge enables the FPED-grounded
HENI composition lookup that closes HENI-CODE-1.y cause A.

Usage (one-time, requires OPENAI_API_KEY):
    cd backend
    python -m heni_calculator.heni.etl.build_cnf_to_fndds_bridge

Inputs:
    backend/raw_fndds/FoodData_Central_survey_food_csv_2024-10-31/  (raw FNDDS)

Outputs (derived artifacts, kept next to the consuming module):
    backend/heni_calculator/data/fndds_embeddings.npz      (~30 MB; cached)
    backend/heni_calculator/data/cnf_to_fndds_bridge.json  (the bridge)

Resumable: saves progress every 100 CNF foods so a crashed run can be re-started.
Idempotent: re-running with the existing bridge JSON in place skips already-
bridged CNF foods.

Cost (estimated, 2026-05-23):
    Embedding ~7,000 FNDDS descriptions x ~50 tokens = ~350k tokens = ~$0.007
    LLM ranking: 5,691 CNF foods x ~700 tokens prompt + ~100 tokens response
                 ~= ~4.5M tokens = ~$1 (gpt-4.1-mini at $0.15 / $0.60 per 1M)
    Total: ~$1 one-time.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


_THIS_DIR = Path(__file__).resolve().parent
# Derived artifacts live next to the consuming HENI module.
_DATA_DIR = _THIS_DIR.parent.parent / 'data'
# Immutable raw inputs sit at backend/raw_* alongside raw_cnf / raw_wafct.
# _THIS_DIR is backend/heni_calculator/heni/etl; parents[2] is backend/.
_BACKEND_ROOT = _THIS_DIR.parents[2]
_FNDDS_DIR = _BACKEND_ROOT / 'raw_fndds' / 'FoodData_Central_survey_food_csv_2024-10-31'

FNDDS_EMBEDDINGS_PATH = _DATA_DIR / 'fndds_embeddings.npz'
CNF_TO_FNDDS_BRIDGE_PATH = _DATA_DIR / 'cnf_to_fndds_bridge.json'

EMBEDDING_MODEL = 'text-embedding-3-small'  # 1536-dim
RANKING_MODEL = 'gpt-4.1-mini'
TOP_K = 20
MIN_BRIDGE_CONFIDENCE = 0.5
EMBED_BATCH_SIZE = 256
RANKING_TEMPERATURE = 0.0

# Pricing snapshot used for the cost projection at --checkpoint-at. Update
# alongside OpenAI rate changes. USD per 1M tokens.
_PRICE_EMBED_PER_1M = 0.020   # text-embedding-3-small
_PRICE_RANK_PROMPT_PER_1M = 0.150
_PRICE_RANK_COMPLETION_PER_1M = 0.600

# Cumulative token usage across the run (filled by _embed_batch + _rank_with_llm).
_TOKEN_USAGE: Dict[str, int] = {
    'embed_prompt': 0,
    'rank_prompt': 0,
    'rank_completion': 0,
}


def _accumulated_cost_usd() -> float:
    """USD spent so far on this run, based on cumulative token usage."""
    return (
        _TOKEN_USAGE['embed_prompt'] / 1_000_000 * _PRICE_EMBED_PER_1M
        + _TOKEN_USAGE['rank_prompt'] / 1_000_000 * _PRICE_RANK_PROMPT_PER_1M
        + _TOKEN_USAGE['rank_completion'] / 1_000_000 * _PRICE_RANK_COMPLETION_PER_1M
    )


def _log_cost_projection(processed: int, remaining: int) -> float:
    """Log spend so far + projection for the full remaining queue. Returns
    projected total USD."""
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
    return projected_total


def _load_fndds_catalog() -> pd.DataFrame:
    """Load FNDDS survey foods with their food_code + WWEIA category.

    Returns columns: [fdc_id, food_code, wweia_category_number,
                      wweia_category_description, description].
    """
    food = pd.read_csv(_FNDDS_DIR / 'food.csv', dtype={'fdc_id': 'int64'})
    food = food[food['data_type'] == 'survey_fndds_food']
    sf = pd.read_csv(_FNDDS_DIR / 'survey_fndds_food.csv',
                     dtype={'fdc_id': 'int64', 'food_code': 'int64',
                            'wweia_category_number': 'int64'})
    wweia = pd.read_csv(_FNDDS_DIR / 'wweia_food_category.csv',
                        dtype={'wweia_food_category': 'int64'})
    df = food.merge(sf, on='fdc_id', how='inner')
    df = df.merge(wweia.rename(columns={'wweia_food_category': 'wweia_category_number',
                                          'wweia_food_category_description': 'wweia_category_description'}),
                  on='wweia_category_number', how='left')
    logger.info('Loaded %d FNDDS survey foods', len(df))
    return df[['fdc_id', 'food_code', 'wweia_category_number',
                'wweia_category_description', 'description']].reset_index(drop=True)


def _build_query_string(cnf_food_id: int, cnf_desc_en: str,
                        cnf_desc_fr: Optional[str], food_group: str) -> str:
    """Bilingual CNF query string for retrieval + ranking."""
    parts = [f'CNF FoodID {cnf_food_id}']
    parts.append(f'EN: {cnf_desc_en}')
    if cnf_desc_fr and cnf_desc_fr != cnf_desc_en:
        parts.append(f'FR: {cnf_desc_fr}')
    parts.append(f'CNF group: {food_group}')
    return '\n'.join(parts)


def _load_cnf_foods() -> List[Dict]:
    """Load every CNF FoodID with English + French descriptions + group."""
    import dish_project.env_bootstrap  # noqa: F401 -- ensure .env is loaded
    os.environ.setdefault('DJANGO_SECRET_KEY', 'etl-bridge')
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
            'food_group': str(row.get('FoodGroupName', '')),
        })
    logger.info('Loaded %d CNF foods', len(rows))
    return rows


def _embed_batch(client, texts: List[str]) -> np.ndarray:
    """Embed a batch of strings via OpenAI."""
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    try:
        _TOKEN_USAGE['embed_prompt'] += int(getattr(resp.usage, 'prompt_tokens', 0) or 0)
    except Exception:  # noqa: BLE001
        pass
    return np.array([d.embedding for d in resp.data], dtype=np.float32)


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    """L2-normalize rows of v so cosine sim is just a dot product."""
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return v / n


def _build_or_load_fndds_embeddings(client, fndds: pd.DataFrame) -> np.ndarray:
    """Embed all FNDDS descriptions (cached on disk)."""
    if FNDDS_EMBEDDINGS_PATH.exists():
        d = np.load(FNDDS_EMBEDDINGS_PATH)
        if d['embeddings'].shape[0] == len(fndds):
            logger.info('Loaded cached FNDDS embeddings (%d x %d)',
                        *d['embeddings'].shape)
            return d['embeddings']
        logger.warning('Cached FNDDS embeddings shape mismatch (%d vs %d); re-embedding',
                       d['embeddings'].shape[0], len(fndds))

    logger.info('Embedding %d FNDDS descriptions in batches of %d...',
                len(fndds), EMBED_BATCH_SIZE)
    parts = []
    for start in range(0, len(fndds), EMBED_BATCH_SIZE):
        batch = fndds['description'].iloc[start:start + EMBED_BATCH_SIZE].tolist()
        emb = _embed_batch(client, batch)
        parts.append(emb)
        if (start // EMBED_BATCH_SIZE) % 5 == 0:
            logger.info('  embedded %d / %d', start + len(batch), len(fndds))
    embeddings = np.vstack(parts)
    embeddings = _l2_normalize(embeddings)
    np.savez(FNDDS_EMBEDDINGS_PATH, embeddings=embeddings)
    logger.info('Cached FNDDS embeddings to %s', FNDDS_EMBEDDINGS_PATH)
    return embeddings


def _retrieve_top_k(query_emb: np.ndarray, fndds_emb: np.ndarray, k: int) -> np.ndarray:
    """Cosine-sim top-k indices (assumes L2-normalised inputs)."""
    sims = fndds_emb @ query_emb
    return np.argpartition(-sims, k)[:k][np.argsort(-sims[np.argpartition(-sims, k)[:k]])]


def _rank_with_llm(client, cnf_query: str, candidates: pd.DataFrame) -> Optional[Dict]:
    """Ask the LLM to pick the best FNDDS analog from candidates.

    Returns {'fdc_id', 'confidence', 'rationale'} or None on failure.
    """
    candidate_block = '\n'.join(
        f'  [{i}] fdc_id={row.fdc_id}  food_code={row.food_code}  '
        f'wweia="{row.wweia_category_description}"  desc="{row.description}"'
        for i, row in candidates.iterrows()
    )
    system_msg = (
        'You are bridging a Canadian Nutrient File (CNF) food to its best '
        'analog in the USDA FNDDS 2017-2018 survey food catalog. Pick the '
        'FNDDS entry whose composition is closest to the CNF food. Respond '
        'with JSON only.'
    )
    user_msg = (
        f'CNF food:\n{cnf_query}\n\n'
        f'Candidate FNDDS analogs (top {len(candidates)} by embedding similarity):\n'
        f'{candidate_block}\n\n'
        'Pick the single best analog and report your confidence. JSON schema:\n'
        '{"fdc_id": <int>, "confidence": <float in [0,1]>, "rationale": "<one short sentence>"}\n\n'
        'Confidence anchors:\n'
        '  0.90 = direct equivalent (same preparation, same ingredients)\n'
        '  0.70 = close analog (same food, minor variant — fat content, fortification)\n'
        '  0.50 = plausible analog (same category, possibly different recipe / proportions)\n'
        '  0.30 = stretched match (similar category but key composition differs)\n'
        '  0.10 = no good analog in candidates\n'
        'Do not default to 0.40 — vary your estimate. If no candidate is good, set confidence < 0.5.'
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
            _TOKEN_USAGE['rank_prompt'] += int(getattr(resp.usage, 'prompt_tokens', 0) or 0)
            _TOKEN_USAGE['rank_completion'] += int(getattr(resp.usage, 'completion_tokens', 0) or 0)
        except Exception:  # noqa: BLE001
            pass
        parsed = json.loads(resp.choices[0].message.content)
        fdc = int(parsed.get('fdc_id'))
        conf = float(parsed.get('confidence', 0.0))
        rationale = str(parsed.get('rationale', ''))[:300]
        # Validate fdc_id is in the candidate set
        valid_fdcs = set(candidates['fdc_id'].tolist())
        if fdc not in valid_fdcs:
            return {'fdc_id': None, 'confidence': 0.0,
                    'rationale': f'LLM hallucinated fdc_id={fdc} not in candidates'}
        return {'fdc_id': fdc, 'confidence': conf, 'rationale': rationale}
    except Exception as exc:  # noqa: BLE001
        logger.warning('LLM ranking failed: %s', exc)
        return None


def _load_existing_bridge() -> Tuple[Dict[str, Dict], List[int]]:
    """Resume support: return (bridges_dict, unbridged_list) if a partial
    bridge JSON exists, else ({}, [])."""
    if not CNF_TO_FNDDS_BRIDGE_PATH.exists():
        return {}, []
    try:
        d = json.loads(CNF_TO_FNDDS_BRIDGE_PATH.read_text(encoding='utf-8'))
        return d.get('bridges', {}), d.get('unbridged', [])
    except Exception as exc:  # noqa: BLE001
        logger.warning('Existing bridge JSON unreadable, starting fresh: %s', exc)
        return {}, []


def _save_bridge(bridges: Dict[str, Dict], unbridged: List[int],
                 cnf_total: int, fndds_total: int) -> None:
    out = {
        '_provenance': {
            'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'embedding_model': EMBEDDING_MODEL,
            'ranking_model': RANKING_MODEL,
            'top_k': TOP_K,
            'min_bridge_confidence': MIN_BRIDGE_CONFIDENCE,
            'cnf_total': cnf_total,
            'fndds_total': fndds_total,
            'cnf_bridged': len(bridges),
            'cnf_unbridged': len(unbridged),
        },
        'bridges': bridges,
        'unbridged': sorted(unbridged),
    }
    CNF_TO_FNDDS_BRIDGE_PATH.write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')


def main(limit: Optional[int] = None,
         food_ids: Optional[List[int]] = None,
         checkpoint_at: Optional[int] = None) -> int:
    # Load .env first so OPENAI_API_KEY is populated. env_bootstrap is also
    # imported inside _load_cnf_foods() but that's after the key check.
    _here = Path(__file__).resolve()
    backend_dir = _here.parent.parent.parent.parent  # heni_calculator/heni/etl/ -> backend
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
    fndds = _load_fndds_catalog()
    if food_ids:
        wanted = set(food_ids)
        cnf_foods = [c for c in cnf_foods if c['food_id'] in wanted]
        logger.info('food_ids filter: bridging %d targeted CNF foods', len(cnf_foods))
    elif limit:
        cnf_foods = cnf_foods[:limit]
        logger.info('limit=%d: bridging first %d CNF foods only', limit, len(cnf_foods))

    fndds_emb = _build_or_load_fndds_embeddings(client, fndds)

    bridges, unbridged = _load_existing_bridge()
    skip_set = set(int(k) for k in bridges.keys()) | set(unbridged)
    to_process = [c for c in cnf_foods if c['food_id'] not in skip_set]
    logger.info('Resuming: %d already bridged, %d already unbridged; %d to process',
                len(bridges), len(unbridged), len(to_process))

    save_interval = 50  # save every N foods
    for i, cnf in enumerate(to_process, start=1):
        query = _build_query_string(cnf['food_id'], cnf['desc_en'], cnf['desc_fr'],
                                     cnf['food_group'])
        # Embed query, retrieve top-K
        try:
            q_emb = _embed_batch(client, [cnf['desc_en']])[0]
            q_emb = q_emb / (np.linalg.norm(q_emb) or 1.0)
        except Exception as exc:  # noqa: BLE001
            logger.warning('Query embedding failed for food_id=%d: %s',
                           cnf['food_id'], exc)
            unbridged.append(cnf['food_id'])
            continue
        top_idx = _retrieve_top_k(q_emb, fndds_emb, TOP_K)
        candidates = fndds.iloc[top_idx].reset_index(drop=True)

        result = _rank_with_llm(client, query, candidates)
        if result is None or result['fdc_id'] is None or result['confidence'] < MIN_BRIDGE_CONFIDENCE:
            unbridged.append(cnf['food_id'])
            reason = (result.get('rationale', '') if result else 'llm_failed')[:80]
            logger.info('[unbridged] cnf=%d (%s) conf=%.2f %s',
                        cnf['food_id'], cnf['desc_en'][:40],
                        result['confidence'] if result else 0.0, reason)
        else:
            fdc = int(result['fdc_id'])
            fcode = int(fndds[fndds['fdc_id'] == fdc].iloc[0]['food_code'])
            bridges[str(cnf['food_id'])] = {
                'fdc_id': fdc,
                'food_code': fcode,
                'confidence': result['confidence'],
                'rationale': result['rationale'],
            }
            if i <= 10 or i % 25 == 0:
                logger.info('[bridged] cnf=%d "%s" -> fdc=%d fcode=%d conf=%.2f',
                            cnf['food_id'], cnf['desc_en'][:40],
                            fdc, fcode, result['confidence'])

        if i % save_interval == 0:
            _save_bridge(bridges, unbridged, len(cnf_foods), len(fndds))
            logger.info('progress: %d / %d processed (%d bridged, %d unbridged)',
                        i, len(to_process), len(bridges), len(unbridged))

        if checkpoint_at is not None and i >= checkpoint_at:
            _save_bridge(bridges, unbridged, len(cnf_foods), len(fndds))
            _log_cost_projection(processed=i, remaining=len(to_process) - i)
            logger.info(
                '--checkpoint-at %d reached; exiting cleanly. '
                'Re-run without the flag to resume from the saved bridge.',
                checkpoint_at,
            )
            return 0

    _save_bridge(bridges, unbridged, len(cnf_foods), len(fndds))
    _log_cost_projection(processed=len(to_process), remaining=0)
    logger.info('DONE. bridged=%d unbridged=%d out=%s',
                len(bridges), len(unbridged), CNF_TO_FNDDS_BRIDGE_PATH)
    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=None,
                   help='Bridge only the first N CNF foods (for smoke testing)')
    p.add_argument('--food-ids', type=str, default=None,
                   help='Bridge only these CNF FoodIDs (comma-separated)')
    p.add_argument('--checkpoint-at', type=int, default=None,
                   help='Exit cleanly after processing N newly-bridged foods and '
                        'log a cost projection. Re-run without the flag to resume.')
    args = p.parse_args()
    fids = None
    if args.food_ids:
        fids = [int(x.strip()) for x in args.food_ids.split(',') if x.strip()]
    sys.exit(main(limit=args.limit, food_ids=fids, checkpoint_at=args.checkpoint_at))
