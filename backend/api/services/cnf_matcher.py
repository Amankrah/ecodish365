"""Free-text → CNF FoodID matcher with embedding retrieval + LLM ranking.

Mirrors ``LCAMatcher`` (backend/environmental_impact_model/src/lca_matcher.py)
but the target catalog is the 5,691-row Canadian Nutrient File (CNF) rather
than Agribalyse. The matcher answers questions like:

    "low-fat chocolate milk"   → CNF FoodID 70 (Milk, fluid, chocolate, partly skimmed, 2 % M.F.)
    "aubergine"                → CNF FoodID 2050 (Eggplant, raw)
    "homemade beef stew"       → CNF FoodID 4964 (Beef stew, canned)  + alternatives

Pipeline:
  1. Normalise query (lowercase + collapse whitespace + strip)
  2. LRU cache hit?  return cached result (per-process, size=2000)
  3. Embed query via text-embedding-3-small → cosine vs the pre-built corpus
     ``backend/api/data/cnf_corpus_embeddings.npz`` → top-k=20 indices
  4. If no LLM client available → return top-1 with confidence = cosine sim
  5. LLM rank with constrained JSON output: {food_id, confidence, justification}
  6. Hallucination gate: returned food_id MUST be in the top-k retrieved set
     (Krahmer 2024 LEAF precedent — 19 % hallucination rate on bare LLM)
  7. Confidence gate: < threshold → fallback to fuzzy top-1, mark low_confidence
  8. Cache + return

This mirrors the production LCAMatcher pattern exactly — same 7 gates, same
calibrated-confidence prompt anchors, same multi-provider ChatJSONClient
abstraction — but adapted for CNF as the target catalog.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# Defaults aligned with LCAMatcher (lca_matcher.py:33-42)
DEFAULT_CONFIDENCE_THRESHOLD = 0.6
DEFAULT_TOP_K = 20
DEFAULT_RANKING_MODEL = 'gpt-4.1-mini'
DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'
DEFAULT_MAX_TOKENS = 220
DEFAULT_TEMPERATURE = 0.0


# --- Result payloads ----------------------------------------------------

@dataclass
class AlternativeMatch:
    food_id: int
    food_description: str
    food_group: str
    similarity: float           # cosine sim from retrieval


@dataclass
class CNFMatchResult:
    query: str                                  # original input
    normalised_query: str                       # cache key
    matched: bool                               # True iff all gates passed
    food_id: Optional[int] = None
    food_description: Optional[str] = None
    food_group: Optional[str] = None
    confidence: float = 0.0
    justification: str = ''                     # may be hidden in individual mode at view layer
    alternatives: List[AlternativeMatch] = field(default_factory=list)
    fallback_reason: Optional[str] = None       # 'low_confidence' | 'hallucinated_id' | 'no_llm_client' | 'no_candidates' | 'exception'
    used_ai_ranking: bool = False               # False = degraded retrieval-only path
    cache_hit: bool = False
    timing_ms: float = 0.0
    corpus_version: Optional[str] = None        # build_date_utc from provenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'normalised_query': self.normalised_query,
            'matched': self.matched,
            'food_id': self.food_id,
            'food_description': self.food_description,
            'food_group': self.food_group,
            'confidence': round(self.confidence, 3),
            'justification': self.justification,
            'alternatives': [
                {
                    'food_id': a.food_id,
                    'food_description': a.food_description,
                    'food_group': a.food_group,
                    'similarity': round(a.similarity, 3),
                }
                for a in self.alternatives
            ],
            'fallback_reason': self.fallback_reason,
            'used_ai_ranking': self.used_ai_ranking,
            'cache_hit': self.cache_hit,
            'timing_ms': round(self.timing_ms, 1),
            'corpus_version': self.corpus_version,
        }


# --- Corpus loader (process-wide singleton) ------------------------------

_CORPUS_LOCK = Lock()
_CORPUS_CACHE: Dict[str, 'CNFCorpus'] = {}


@dataclass
class CNFCorpus:
    food_ids: np.ndarray                    # int32[N]
    embeddings: np.ndarray                  # float32[N, 1536] L2-normalised
    text_used: List[str]                    # the embed-text per row (for debug)
    food_descriptions: List[str]            # English description per row
    food_groups: List[str]                  # FoodGroupName per row
    # WAFCT-EXTEND (2026-05-24): per-row source ('cnf' or 'wafct'). Used by
    # `CNFMatcher.match(..., source=)` to filter candidates pre-LLM-rank.
    sources: List[str]
    provenance: Dict[str, Any]
    embedding_dim: int

    @classmethod
    def load(cls, corpus_path: Path) -> 'CNFCorpus':
        key = str(corpus_path.resolve())
        with _CORPUS_LOCK:
            if key in _CORPUS_CACHE:
                return _CORPUS_CACHE[key]
            corpus = cls._load_from_disk(corpus_path)
            _CORPUS_CACHE[key] = corpus
            return corpus

    @classmethod
    def _load_from_disk(cls, corpus_path: Path) -> 'CNFCorpus':
        if not corpus_path.exists():
            raise FileNotFoundError(
                f'CNF corpus embeddings not found at {corpus_path}. '
                f'Run: python -m api.services.etl.build_cnf_corpus_embeddings'
            )
        provenance_path = corpus_path.with_name(
            corpus_path.stem + '_provenance.json'
        )
        if not provenance_path.exists():
            raise FileNotFoundError(
                f'CNF corpus provenance not found at {provenance_path}. '
                f'Run the ETL to regenerate the corpus + provenance together.'
            )
        with open(provenance_path, encoding='utf-8') as f:
            provenance = json.load(f)

        d = np.load(corpus_path, allow_pickle=True)
        food_ids = d['food_ids']
        embeddings = d['embeddings']
        text_used = list(d['text_used'])
        # WAFCT-EXTEND (2026-05-24): `sources` is present in WAFCT-aware
        # builds. Legacy CNF-only npz files lack it — synthesise 'cnf' for
        # every row so we stay backward-compatible until next rebuild.
        if 'sources' in d.files:
            sources = [str(s) for s in d['sources'].tolist()]
        else:
            sources = ['cnf'] * len(food_ids)

        # Hydrate food descriptions + groups from CNF (used for display in
        # API responses). Lazy import so this module loads without Django.
        food_descriptions, food_groups = cls._hydrate_display_fields(
            food_ids.tolist()
        )

        return cls(
            food_ids=food_ids,
            embeddings=embeddings,
            text_used=text_used,
            food_descriptions=food_descriptions,
            food_groups=food_groups,
            sources=sources,
            provenance=provenance,
            embedding_dim=int(embeddings.shape[1]),
        )

    @staticmethod
    def _hydrate_display_fields(food_ids: List[int]) -> 'tuple[List[str], List[str]]':
        """Hydrate FoodID → (description, food-group-name) for display.

        WAFCT-EXTEND (2026-05-24): read from the cached pipeline
        (`api.cnf_cache.get_api_cnf_pipeline()`) rather than re-reading
        FOOD_NAME.csv directly. The pipeline already contains both CNF
        and WAFCT-ingested rows, so WAFCT FoodIDs (700,000+) hydrate
        correctly without any special-casing here.
        """
        import pandas as pd
        from api.cnf_cache import get_api_cnf_pipeline
        pipeline = get_api_cnf_pipeline()
        fn = pipeline.food_name_df
        fg = pipeline.food_group_df
        fg_col = 'FoodGroupName' if 'FoodGroupName' in fg.columns else 'FoodGroup'
        merged = fn.merge(fg[['FoodGroupID', fg_col]], on='FoodGroupID', how='left')
        by_id = {int(r['FoodID']): (str(r['FoodDescription']),
                                     str(r.get(fg_col, '')) if pd.notna(r.get(fg_col, '')) else '')
                 for _, r in merged.iterrows()}
        descs, groups = [], []
        for fid in food_ids:
            d, g = by_id.get(int(fid), ('', ''))
            descs.append(d)
            groups.append(g)
        return descs, groups


# --- Matcher class -------------------------------------------------------

_NORMALISE_RE = re.compile(r'\s+')


def _normalise_query(q: str) -> str:
    """Cache key normalisation: lowercase, collapse whitespace, strip."""
    return _NORMALISE_RE.sub(' ', q.strip().lower())


class CNFMatcher:
    """Free-text query → CNF FoodID matcher.

    Same pattern as ``LCAMatcher`` (CNF FoodID → Agribalyse ciqual_code) but
    inverted: the corpus is now the CNF foods themselves and the input is a
    user-supplied free-text query.
    """

    # Calibration anchors mirror LCAMatcher's prompt (lca_matcher.py:432-448),
    # adapted from "LCA expert" to "nutrition database curator".
    SYSTEM_PROMPT = (
        "You are matching a user's free-text food query to the closest entry "
        "in the Canadian Nutrient File (CNF). Pick exactly ONE candidate from "
        "the provided list (you MUST NOT invent a CNF FoodID). Reason over "
        "the food's composition, processing, form, and the CNF food group.\n\n"
        "CONFIDENCE: report `confidence` as the probability (0.00-1.00) that "
        "a nutrition database curator reviewing your choice would mark it "
        "as the correct match for the user's query — NOT a generic \"how "
        "sure am I\" score. Calibration anchors:\n"
        "  - 0.95 = near-identical (same food, same form, same processing)\n"
        "  - 0.80 = same commodity, minor form/processing differences (e.g. raw vs cooked)\n"
        "  - 0.60 = same broad food group; nutritionally equivalent but not exact\n"
        "  - 0.40 = stretched (different composition; usable as a rough proxy)\n"
        "  - 0.20 = poor match; would prefer no match over this\n"
        "  - 0.00 = no acceptable candidate exists in the provided list\n"
        "Vary your confidence — do not default to a single value.\n\n"
        "Respond with JSON only."
    )

    def __init__(
        self,
        corpus: CNFCorpus,
        chat_json_client: Optional[Any] = None,
        openai_client: Optional[Any] = None,
        *,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        top_k: int = DEFAULT_TOP_K,
        model: str = DEFAULT_RANKING_MODEL,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        cache_size: int = 2000,
        embedding_cache_size: int = 5000,
    ):
        self.corpus = corpus
        self.chat_json_client = chat_json_client
        self.openai_client = openai_client    # for query embedding
        self.confidence_threshold = confidence_threshold
        self.top_k = top_k
        self.model = model
        self.embedding_model = embedding_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        # LRU cache for full match results, keyed by normalised query string
        self._cache_size = cache_size
        self._cache: 'dict[str, CNFMatchResult]' = {}
        self._cache_order: List[str] = []
        self._cache_lock = Lock()
        # AI-MATCH-1.x (2026-05-23): separate LRU for query EMBEDDINGS.
        # The result cache above short-circuits the full pipeline on repeat
        # queries — but the recipe decomposer routes each Stage-1 ingredient
        # name through CNFMatcher independently, and those names ("tomato
        # sauce", "olive oil", "salt") repeat heavily across recipes.
        # Caching just the embedding (without the LLM rank) lets recipe
        # decomposition reuse the embedding even when the full match result
        # isn't cached for the specific (top_k, mode) combination. ~5,000
        # entries × 1,536 × 4 bytes ≈ 30 MB per process — well within budget.
        self._emb_cache_size = embedding_cache_size
        self._emb_cache: 'dict[str, np.ndarray]' = {}
        self._emb_cache_order: List[str] = []
        self._emb_cache_lock = Lock()
        self._emb_cache_hits = 0
        self._emb_cache_misses = 0

    # --- public ----------------------------------------------------------

    def match(
        self,
        query: str,
        top_k: Optional[int] = None,
        source: Optional[str] = None,
        retrieval_only: bool = False,
    ) -> CNFMatchResult:
        """Free-text → CNF / WAFCT FoodID.

        WAFCT-EXTEND (2026-05-24): pass ``source='cnf'`` or ``source='wafct'``
        to restrict the candidate pool to one food database. Default
        ``None`` searches both. Filtering happens AFTER embedding retrieval
        and BEFORE LLM ranking, so the LLM only sees in-scope candidates.

        ``retrieval_only=True`` skips the LLM rank step and returns the
        embedding top-1 with cosine similarity as confidence — used by call
        sites that only consume ``result.alternatives`` (pure cosine), where
        the LLM call is wasted work.
        """
        t0 = time.perf_counter()
        if not query or not query.strip():
            return CNFMatchResult(
                query=query, normalised_query='',
                matched=False, fallback_reason='no_candidates',
                timing_ms=(time.perf_counter() - t0) * 1000,
                corpus_version=self.corpus.provenance.get('build_date_utc'),
            )

        # Source-aware cache key — a 'cnf' query and a 'both' query may
        # return different top matches, so they need independent cache slots.
        # Retrieval-only results have different confidence/justification than
        # full-match results, so they need their own cache slot too.
        source_norm = source if source in ('cnf', 'wafct') else None
        nq = _normalise_query(query)
        cache_key = nq if source_norm is None else f'{nq}|src:{source_norm}'
        if retrieval_only:
            cache_key = f'{cache_key}|ro'
        cached = self._cache_get(cache_key)
        if cached is not None:
            # Return a copy with refreshed timing + cache_hit flag so the
            # cached result isn't mutated in place.
            return CNFMatchResult(
                **{**cached.__dict__,
                   'query': query,
                   'cache_hit': True,
                   'timing_ms': (time.perf_counter() - t0) * 1000},
            )

        k = top_k or self.top_k
        try:
            candidates = self._retrieve(nq, k=k)
        except Exception as exc:  # noqa: BLE001
            logger.warning('CNFMatcher embed/retrieve failed for query=%r: %s', nq, exc)
            result = CNFMatchResult(
                query=query, normalised_query=nq, matched=False,
                fallback_reason='exception',
                justification=f'embed/retrieve exception: {exc!r}',
                timing_ms=(time.perf_counter() - t0) * 1000,
                corpus_version=self.corpus.provenance.get('build_date_utc'),
            )
            self._cache_put(cache_key, result)
            return result

        # WAFCT-EXTEND (2026-05-24): apply source filter to candidates BEFORE
        # LLM ranking. The corpus's `sources` array is indexed alongside
        # `food_ids`, so filtering is O(k) and preserves cosine-sim ranking.
        if source_norm is not None and self.corpus.sources:
            candidates = [
                (idx, sim) for idx, sim in candidates
                if self.corpus.sources[idx] == source_norm
            ]

        if not candidates:
            result = CNFMatchResult(
                query=query, normalised_query=nq, matched=False,
                fallback_reason='no_candidates',
                timing_ms=(time.perf_counter() - t0) * 1000,
                corpus_version=self.corpus.provenance.get('build_date_utc'),
            )
            self._cache_put(cache_key, result)
            return result

        # Build the alternatives list (top-3 excluding the chosen match)
        # AFTER we pick the winner below.

        if retrieval_only or self.chat_json_client is None:
            # Retrieval-only top-1, confidence = cosine sim. Either an
            # intentional skip (caller only consumes `alternatives`) or the
            # degraded "no LLM key configured" path.
            top_idx, top_sim = candidates[0]
            matched = top_sim >= self.confidence_threshold
            justification = (
                'embedding-similarity-only (retrieval_only=True; LLM rank skipped)'
                if retrieval_only else
                'embedding-similarity-only (no LLM key configured)'
            )
            result = self._build_result(
                query=query, normalised_query=nq,
                matched=matched,
                food_idx=top_idx,
                confidence=float(top_sim),
                justification=justification,
                fallback_reason=None if matched else 'low_confidence',
                candidates=candidates,
                used_ai_ranking=False,
                t0=t0,
                max_alternatives=max(0, k - 1),
            )
            self._cache_put(cache_key, result)
            return result

        # LLM ranking
        try:
            parsed = self._llm_rank(query, candidates)
        except Exception as exc:  # noqa: BLE001
            logger.warning('CNFMatcher LLM rank failed for query=%r: %s', nq, exc)
            top_idx, top_sim = candidates[0]
            result = self._build_result(
                query=query, normalised_query=nq,
                matched=False, food_idx=top_idx,
                confidence=float(top_sim),
                justification=f'LLM exception, retrieval-only fallback: {exc!r}',
                fallback_reason='exception',
                candidates=candidates,
                used_ai_ranking=False,
                t0=t0,
                max_alternatives=max(0, k - 1),
            )
            self._cache_put(cache_key, result)
            return result

        proposed_food_id = parsed.get('food_id')
        confidence = float(parsed.get('confidence', 0.0) or 0.0)
        justification = str(parsed.get('justification', '') or '').strip()[:280]

        # Hallucination gate: must be one of the retrieved candidates
        try:
            proposed_food_id_int = int(proposed_food_id)
        except (TypeError, ValueError):
            proposed_food_id_int = -1
        candidate_food_ids = {
            int(self.corpus.food_ids[idx]): idx for idx, _ in candidates
        }
        if proposed_food_id_int not in candidate_food_ids:
            logger.info(
                'CNFMatcher rejected hallucinated food_id=%r for query=%r '
                '(not in top-%d retrieved set)',
                proposed_food_id, nq, k,
            )
            # Fall back to retrieval top-1
            top_idx, top_sim = candidates[0]
            result = self._build_result(
                query=query, normalised_query=nq,
                matched=False, food_idx=top_idx,
                confidence=float(top_sim),
                justification=f'LLM proposed food_id={proposed_food_id!r} not in '
                              f'retrieved set; fell back to retrieval top-1',
                fallback_reason='hallucinated_id',
                candidates=candidates,
                used_ai_ranking=True,
                t0=t0,
                max_alternatives=max(0, k - 1),
            )
            self._cache_put(cache_key, result)
            return result

        chosen_idx = candidate_food_ids[proposed_food_id_int]

        # Confidence gate
        if confidence < self.confidence_threshold:
            result = self._build_result(
                query=query, normalised_query=nq,
                matched=False, food_idx=chosen_idx,
                confidence=confidence,
                justification=justification,
                fallback_reason='low_confidence',
                candidates=candidates,
                used_ai_ranking=True,
                t0=t0,
                max_alternatives=max(0, k - 1),
            )
            self._cache_put(cache_key, result)
            return result

        # Matched
        result = self._build_result(
            query=query, normalised_query=nq,
            matched=True, food_idx=chosen_idx,
            confidence=confidence,
            justification=justification,
            fallback_reason=None,
            candidates=candidates,
            used_ai_ranking=True,
            t0=t0,
            max_alternatives=max(0, k - 1),
        )
        self._cache_put(cache_key, result)
        return result

    # --- internals -------------------------------------------------------

    def prewarm_embeddings(self, queries: List[str]) -> int:
        """Batch-embed a list of free-text queries into the embedding cache.

        OpenAI's embeddings endpoint accepts up to 2048 inputs per request, so
        N queries become 1 round-trip instead of N. Returns the number of
        queries that actually hit the network (cache hits are skipped).

        Used by substitution_discovery to prewarm all ingredient queries
        before the per-ingredient matcher.match() loop — turns N sequential
        HTTPS round-trips into one batched call.
        """
        if not queries:
            return 0

        # Normalise + dedupe; filter out anything already cached.
        wanted: List[str] = []
        seen: set = set()
        with self._emb_cache_lock:
            for q in queries:
                if not q or not q.strip():
                    continue
                nq = _normalise_query(q)
                if nq in seen or nq in self._emb_cache:
                    continue
                seen.add(nq)
                wanted.append(nq)
        if not wanted:
            return 0

        if self.openai_client is None:
            from openai import OpenAI
            import os
            self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))

        resp = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=wanted,
        )
        # OpenAI guarantees order matches the input array.
        with self._emb_cache_lock:
            for nq, item in zip(wanted, resp.data):
                qv = np.array(item.embedding, dtype=np.float32)
                n = np.linalg.norm(qv)
                if n > 0:
                    qv = qv / n
                self._emb_cache[nq] = qv
                self._emb_cache_order.append(nq)
                self._emb_cache_misses += 1
            while len(self._emb_cache_order) > self._emb_cache_size:
                evict = self._emb_cache_order.pop(0)
                self._emb_cache.pop(evict, None)
        return len(wanted)

    def _embed_query(self, normalised_query: str) -> np.ndarray:
        """L2-normalised query vector, with LRU cache. AI-MATCH-1.x."""
        with self._emb_cache_lock:
            cached = self._emb_cache.get(normalised_query)
            if cached is not None:
                # Touch (MRU)
                try:
                    self._emb_cache_order.remove(normalised_query)
                except ValueError:
                    pass
                self._emb_cache_order.append(normalised_query)
                self._emb_cache_hits += 1
                return cached

        if self.openai_client is None:
            from openai import OpenAI
            import os
            self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY', ''))
        resp = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=[normalised_query],
        )
        qv = np.array(resp.data[0].embedding, dtype=np.float32)
        n = np.linalg.norm(qv)
        if n > 0:
            qv = qv / n

        with self._emb_cache_lock:
            self._emb_cache[normalised_query] = qv
            self._emb_cache_order.append(normalised_query)
            while len(self._emb_cache_order) > self._emb_cache_size:
                evict = self._emb_cache_order.pop(0)
                self._emb_cache.pop(evict, None)
            self._emb_cache_misses += 1
        return qv

    def _retrieve(self, normalised_query: str, k: int) -> List['tuple[int, float]']:
        """Embed query (cached), compute cosine vs corpus, return top-k (idx, sim) tuples."""
        qv = self._embed_query(normalised_query)
        sims = self.corpus.embeddings @ qv
        # Top-k via argpartition + argsort within partition
        if k >= len(sims):
            top_idx = np.argsort(-sims)
        else:
            top_idx = np.argpartition(-sims, k)[:k]
            top_idx = top_idx[np.argsort(-sims[top_idx])]
        return [(int(i), float(sims[i])) for i in top_idx]

    def embedding_cache_stats(self) -> Dict[str, int]:
        """Diagnostic — used by smoke harnesses + telemetry."""
        with self._emb_cache_lock:
            return {
                'hits':    self._emb_cache_hits,
                'misses':  self._emb_cache_misses,
                'size':    len(self._emb_cache),
                'max_size': self._emb_cache_size,
            }

    def _llm_rank(
        self,
        query: str,
        candidates: List['tuple[int, float]'],
    ) -> Dict[str, Any]:
        """Build prompt + call ChatJSONClient + return parsed dict."""
        lines = [f'User query: {query}', '']
        lines.append('Candidates (ranked by embedding similarity):')
        for idx, sim in candidates:
            food_id = int(self.corpus.food_ids[idx])
            desc = self.corpus.food_descriptions[idx]
            group = self.corpus.food_groups[idx]
            lines.append(
                f'  food_id={food_id}: {desc} [group: {group}] (sim={sim:.3f})'
            )
        lines.append('')
        lines.append(
            'Respond with JSON: {"food_id": <one of the above integer FoodIDs exactly>, '
            '"confidence": <float 0-1>, "justification": "<≤40 words>"}'
        )
        lines.append(
            'confidence = P(a nutrition database curator would call this the '
            'correct match for the user\'s query). Anchors: 0.95 near-identical '
            '/ 0.80 same commodity / 0.60 same broad group / 0.40 stretched / '
            '0.20 poor / 0.00 no acceptable candidate.'
        )
        user = '\n'.join(lines)
        result = self.chat_json_client.chat_completion_json(
            system=self.SYSTEM_PROMPT,
            user=user,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {}
        return {}

    def _build_result(
        self,
        *,
        query: str,
        normalised_query: str,
        matched: bool,
        food_idx: int,
        confidence: float,
        justification: str,
        fallback_reason: Optional[str],
        candidates: List['tuple[int, float]'],
        used_ai_ranking: bool,
        t0: float,
        max_alternatives: int = 3,
    ) -> CNFMatchResult:
        food_id = int(self.corpus.food_ids[food_idx])
        food_description = self.corpus.food_descriptions[food_idx]
        food_group = self.corpus.food_groups[food_idx]

        # Build alternatives from the retrieval set (excluding the chosen match).
        alts: List[AlternativeMatch] = []
        max_alts = max(0, max_alternatives)
        for idx, sim in candidates:
            if int(self.corpus.food_ids[idx]) == food_id:
                continue
            alts.append(AlternativeMatch(
                food_id=int(self.corpus.food_ids[idx]),
                food_description=self.corpus.food_descriptions[idx],
                food_group=self.corpus.food_groups[idx],
                similarity=float(sim),
            ))
            if len(alts) >= max_alts:
                break

        return CNFMatchResult(
            query=query,
            normalised_query=normalised_query,
            matched=matched,
            food_id=food_id,
            food_description=food_description,
            food_group=food_group,
            confidence=confidence,
            justification=justification,
            alternatives=alts,
            fallback_reason=fallback_reason,
            used_ai_ranking=used_ai_ranking,
            cache_hit=False,
            timing_ms=(time.perf_counter() - t0) * 1000,
            corpus_version=self.corpus.provenance.get('build_date_utc'),
        )

    # --- LRU cache (thread-safe, size-bounded) ---------------------------

    def _cache_get(self, key: str) -> Optional[CNFMatchResult]:
        with self._cache_lock:
            r = self._cache.get(key)
            if r is None:
                return r
            # Touch: move key to MRU position
            try:
                self._cache_order.remove(key)
            except ValueError:
                pass
            self._cache_order.append(key)
            return r

    def _cache_put(self, key: str, value: CNFMatchResult) -> None:
        with self._cache_lock:
            if key in self._cache:
                try:
                    self._cache_order.remove(key)
                except ValueError:
                    pass
            self._cache[key] = value
            self._cache_order.append(key)
            while len(self._cache_order) > self._cache_size:
                evict = self._cache_order.pop(0)
                self._cache.pop(evict, None)


# --- Factory ------------------------------------------------------------

@lru_cache(maxsize=1)
def get_default_matcher() -> CNFMatcher:
    """Process-wide singleton for the API view layer.

    Loads the embedding corpus from
    ``backend/api/data/cnf_corpus_embeddings.npz`` and wires up the OpenAI +
    ChatJSONClient instances using ``LLM_PROVIDER`` / ``CHAT_LLM_MODEL`` /
    ``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY`` from the environment (same
    conventions as LCAMatcher's ``build_default_matcher``).
    """
    from django.conf import settings  # noqa: F401 (ensures Django settings loaded)
    here = Path(__file__).resolve().parent          # backend/api/services
    corpus_path = here.parent / 'data' / 'cnf_corpus_embeddings.npz'
    corpus = CNFCorpus.load(corpus_path)

    # Hash check — refuse to load if FOOD_NAME.csv has changed since the
    # corpus was built (forces an ETL rerun).
    from django.conf import settings as _s
    food_name_csv = Path(_s.CNF_FOLDER) / 'FOOD_NAME.csv'
    if food_name_csv.exists():
        from .etl.build_cnf_corpus_embeddings import _sha256_of_file
        actual = _sha256_of_file(food_name_csv, normalize_newlines=True)
        expected = corpus.provenance.get('source_file_sha256')
        if expected and actual != expected:
            raise RuntimeError(
                f'CNF corpus stale: FOOD_NAME.csv sha256={actual} but '
                f'corpus provenance has {expected}. Rerun: '
                f'python -m api.services.etl.build_cnf_corpus_embeddings --force'
            )

    # OpenAI for query embedding
    import os
    api_key = os.environ.get('OPENAI_API_KEY', '')
    openai_client = None
    if api_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=api_key)
        except ImportError:
            logger.warning('openai package not installed; matcher will fail to embed')

    # ChatJSONClient for LLM ranking
    chat_client = None
    try:
        # Reuse the multi-provider builder from environmental_impact_model
        from environmental_impact_model.src.llm_client import build_chat_json_client
        chat_client = build_chat_json_client()
    except Exception as exc:  # noqa: BLE001
        logger.warning('CNFMatcher: failed to build ChatJSONClient (%s); '
                       'will degrade to retrieval-only top-1.', exc)

    return CNFMatcher(corpus=corpus, chat_json_client=chat_client, openai_client=openai_client)
