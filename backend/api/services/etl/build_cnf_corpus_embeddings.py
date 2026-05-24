"""One-time ETL: embed the full CNF corpus for AI-enhanced search (AI-MATCH-1).

Mirrors ``backend/heni_calculator/heni/etl/build_cnf_to_fndds_bridge.py:54-153``
but the OUTPUT is just the embedding matrix (no per-row LLM ranking — that
happens at query time in ``backend/api/services/cnf_matcher.py``).

Reads:    backend/raw_cnf/FOOD_NAME.csv  + FOOD_GROUP.csv
Embeds:   text-embedding-3-small (1536-dim, L2-normalised)
Writes:   backend/api/data/cnf_corpus_embeddings.npz
            { food_ids: int32[5691], embeddings: float32[5691, 1536],
              text_used: object[5691] }
          backend/api/data/cnf_corpus_embeddings_provenance.json
            { model, build_date_utc, source_file_sha256, food_count }

Usage (one-time, requires OPENAI_API_KEY in backend/.env):
    cd backend
    python -m api.services.etl.build_cnf_corpus_embeddings

Re-run rule:
    The matcher checks `source_file_sha256` against the live FOOD_NAME.csv
    on init and refuses to load if mismatched — forcing an ETL rerun.

Cost & runtime:
    ~5,691 CNF foods × ~30 tokens / food = ~170k tokens at text-embedding-3-small.
    Cost: ~$0.005 one-time. Runtime: <2 min.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

_THIS_DIR = Path(__file__).resolve().parent           # backend/api/services/etl
_DATA_DIR = _THIS_DIR.parent.parent / 'data'          # backend/api/data
_DATA_DIR.mkdir(parents=True, exist_ok=True)

CORPUS_EMBEDDINGS_PATH = _DATA_DIR / 'cnf_corpus_embeddings.npz'
CORPUS_PROVENANCE_PATH = _DATA_DIR / 'cnf_corpus_embeddings_provenance.json'

EMBEDDING_MODEL = 'text-embedding-3-small'   # 1536-dim
EMBED_BATCH_SIZE = 256


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _build_embed_text(desc_en: str, desc_fr: Optional[str], food_group: str) -> str:
    """Bilingual + food-group embed text.

    Mirrors ``LCAMatcher._canonicalize_food_state`` precedent (lca_matcher.py:233-250):
    concatenate the English + French (if distinct) + the food group, so the
    embedding captures synonyms across the two CNF languages plus the
    coarse category.
    """
    parts = [desc_en.strip()]
    if desc_fr and desc_fr.strip() and desc_fr.strip() != desc_en.strip():
        parts.append(desc_fr.strip())
    if food_group and food_group.strip():
        parts.append(f'group: {food_group.strip()}')
    return ' | '.join(parts)


def _load_cnf_corpus() -> List[dict]:
    """Load CNF FOOD_NAME + FOOD_GROUP, return list of dicts ready to embed."""
    # Lazy Django bootstrap so this module can also be imported by Django
    # views without re-running ``django.setup()``.
    import dish_project.env_bootstrap  # noqa: F401
    os.environ.setdefault('DJANGO_SECRET_KEY', 'etl-cnf-corpus')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
    import django
    django.setup()
    from django.conf import settings
    import pandas as pd

    cnf_dir = Path(settings.CNF_FOLDER)
    food_name = pd.read_csv(cnf_dir / 'FOOD_NAME.csv', encoding='latin-1',
                            low_memory=False)
    food_group = pd.read_csv(cnf_dir / 'FOOD_GROUP.csv', encoding='latin-1',
                             low_memory=False)

    fg_col = 'FoodGroupName' if 'FoodGroupName' in food_group.columns else 'FoodGroup'
    merged = food_name.merge(
        food_group[['FoodGroupID', fg_col]], on='FoodGroupID', how='left'
    )

    fr_col = 'FoodDescriptionF' if 'FoodDescriptionF' in merged.columns else None

    rows = []
    for _, r in merged.iterrows():
        rows.append({
            'food_id': int(r['FoodID']),
            'desc_en': str(r['FoodDescription']),
            'desc_fr': str(r[fr_col]) if fr_col and pd.notna(r[fr_col]) else None,
            'food_group': str(r.get(fg_col, '')) if pd.notna(r.get(fg_col, '')) else '',
        })
    logger.info('Loaded %d CNF foods (raw_cnf/FOOD_NAME.csv joined to FOOD_GROUP)',
                len(rows))
    return rows


def _embed_batch(client, texts: List[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data], dtype=np.float32)


def _l2_normalise(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return v / n


def build(force: bool = False) -> None:
    rows = _load_cnf_corpus()
    food_ids = np.array([r['food_id'] for r in rows], dtype=np.int32)
    texts = [_build_embed_text(r['desc_en'], r['desc_fr'], r['food_group'])
             for r in rows]

    # Compute the source-file hash for the provenance record (matcher will
    # check this on init).
    from django.conf import settings
    food_name_csv = Path(settings.CNF_FOLDER) / 'FOOD_NAME.csv'
    source_sha256 = _sha256_of_file(food_name_csv)

    # Skip if cache is fresh
    if not force and CORPUS_EMBEDDINGS_PATH.exists() and CORPUS_PROVENANCE_PATH.exists():
        with open(CORPUS_PROVENANCE_PATH, encoding='utf-8') as f:
            prov = json.load(f)
        if prov.get('source_file_sha256') == source_sha256 \
                and prov.get('food_count') == len(rows):
            logger.info('Cached corpus is fresh (sha256 + food_count match); skipping. '
                        'Use --force to rebuild.')
            return
        logger.info('Cache stale (sha256 / food_count mismatch); rebuilding.')

    # OpenAI client
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error('OPENAI_API_KEY not set; cannot build corpus embeddings.')
        sys.exit(1)
    try:
        from openai import OpenAI
    except ImportError:
        logger.error('openai package missing; pip install openai.')
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    # Batch-embed
    logger.info('Embedding %d CNF descriptions via %s in batches of %d...',
                len(texts), EMBEDDING_MODEL, EMBED_BATCH_SIZE)
    t0 = time.time()
    parts = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start:start + EMBED_BATCH_SIZE]
        parts.append(_embed_batch(client, batch))
        if (start // EMBED_BATCH_SIZE) % 5 == 0:
            logger.info('  embedded %d / %d', start + len(batch), len(texts))
    embeddings = _l2_normalise(np.vstack(parts))
    elapsed = time.time() - t0
    logger.info('Embedding complete in %.1fs (shape: %s)', elapsed, embeddings.shape)

    # Persist
    np.savez_compressed(
        CORPUS_EMBEDDINGS_PATH,
        food_ids=food_ids,
        embeddings=embeddings,
        text_used=np.array(texts, dtype=object),
    )
    provenance = {
        'model':                EMBEDDING_MODEL,
        'embedding_dim':        int(embeddings.shape[1]),
        'food_count':           len(rows),
        'build_date_utc':       datetime.now(timezone.utc).isoformat(),
        'source_file':          str(food_name_csv),
        'source_file_sha256':   source_sha256,
        'embed_text_template':  '"<desc_en> | <desc_fr> | group: <food_group>" '
                                '(parts dropped if empty / equal)',
        'l2_normalised':        True,
        'batch_size':           EMBED_BATCH_SIZE,
        'embedding_runtime_s':  round(elapsed, 1),
    }
    with open(CORPUS_PROVENANCE_PATH, 'w', encoding='utf-8') as f:
        json.dump(provenance, f, indent=2)
    logger.info('Wrote %s (%.2f MB)',
                CORPUS_EMBEDDINGS_PATH, CORPUS_EMBEDDINGS_PATH.stat().st_size / 1024 / 1024)
    logger.info('Wrote %s', CORPUS_PROVENANCE_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true',
                        help='rebuild even if cache appears fresh')
    args = parser.parse_args()
    build(force=args.force)
    return 0


if __name__ == '__main__':
    sys.exit(main())
