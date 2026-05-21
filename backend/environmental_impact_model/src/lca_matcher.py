"""LCA matcher (§3.5): CNF food → Agribalyse 3.2 LCI entry via retrieval-augmented
LLM ranking with confidence-scored fallback to Poore & Nemecek group means.

Architecture (per GROUP-D-RECONCILIATION plan, anchored on Zhou et al. 2025
NutriRAG, Krahmer 2024 LEAF, and Furrer et al. 2024):

  food description ──▶ EmbeddingRetriever (cosine sim, top-k=20) ──▶
                       LLM ranking (gpt-4o-mini, T=0, JSON-only, output
                       constrained to retrieved candidates) ──▶
                       MatchResult{ciqual_code, confidence, justification}
                       ──▶ if confidence < threshold OR LLM hallucinates a
                       code not in the retrieved set: fallback to group default

The matcher is a strictly upstream override on top of the existing
`cnf_integrator.get_environmental_impact_factors` group-default path. When
the API flag `enable_lca_matcher` is false (default), this module is not
loaded and the existing behaviour is preserved bit-for-bit.

Citations:
- Zhou et al. 2025 (NutriRAG, doi:10.1101/2025.03.19.25324268): published
  architectural precedent for retrieve-then-rank. k=5-20 retrieval-depth
  sweep; we default to k=20.
- Krahmer 2024 (LEAF, ACL ClimateNLP): observed GPT-3.5 hallucinating
  non-existent Agribalyse class labels at 0.19; motivates constrained-output
  ranking (we reject any LLM response whose ciqual_code is not in the
  retrieved candidate set).
- Furrer et al. 2024 (J Cleaner Prod 470:143198): 3.7% manual-validation
  error rate on single-food EuroFIR ↔ Agribalyse interlinkage; sets the
  benchmark our S7 must approach.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.normpath(os.path.join(_MODULE_DIR, "..", "data"))

DEFAULT_BOOTSTRAP_CATALOG_PATH = os.path.join(_DATA_DIR, "agribalyse_bootstrap.json")
DEFAULT_EMBEDDINGS_CACHE_PATH = os.path.join(_DATA_DIR, "agribalyse_bootstrap_embeddings.npy")

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"  # 1536-dim; $0.02/1M tokens
DEFAULT_RANKING_MODEL = "gpt-4o-mini"  # match HENI categorizer
DEFAULT_CONFIDENCE_THRESHOLD = 0.6  # manuscript §3.5
DEFAULT_TOP_K = 20  # NutriRAG k=5-20 sweep upper end

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Single matcher decision for one CNF food.

    `matched=True` means a high-confidence Agribalyse mapping was made.
    `matched=False` means the matcher fell back to the existing group-default
    LCA pipeline (the audit trail records why).
    """

    food_id: int
    matched: bool
    ciqual_code: Optional[str] = None
    lci_name: Optional[str] = None
    confidence: float = 0.0
    justification: str = ""
    midpoint_factors: Optional[Dict[str, float]] = None
    fallback_reason: Optional[str] = None  # "low_confidence" | "hallucinated_code" | "no_llm_client" | "no_candidates" | "exception"
    candidates_considered: List[Dict[str, Any]] = field(default_factory=list)

    def to_audit(self) -> Dict[str, Any]:
        return {
            "food_id": self.food_id,
            "matched": self.matched,
            "ciqual_code": self.ciqual_code,
            "lci_name": self.lci_name,
            "confidence": self.confidence,
            "justification": self.justification,
            "fallback_reason": self.fallback_reason,
            "n_candidates_considered": len(self.candidates_considered),
        }


class AgribalyseIndex:
    """Bootstrap Agribalyse 3.2 catalog + precomputed sentence embeddings.

    The catalog is loaded from `agribalyse_bootstrap.json` (50–80 entries spanning
    the 10 CNF food groups). Embeddings are loaded from the `.npy` cache if
    present, otherwise computed via `embedding_client.embeddings.create(...)`
    and persisted. Production scale (2,518 entries, full Agribalyse 3.2) is
    deferred to GROUP-D-CODE-1.x-A.
    """

    def __init__(
        self,
        catalog_path: str = DEFAULT_BOOTSTRAP_CATALOG_PATH,
        embeddings_cache_path: str = DEFAULT_EMBEDDINGS_CACHE_PATH,
        embedding_client: Optional[Any] = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.catalog_path = catalog_path
        self.embeddings_cache_path = embeddings_cache_path
        self.embedding_client = embedding_client
        self.embedding_model = embedding_model
        self._catalog: List[Dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None  # (n, dim)
        self._load_catalog()

    def _load_catalog(self) -> None:
        with open(self.catalog_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        # JSON schema: top-level dict with "entries" list (see agribalyse_bootstrap.json).
        # Backwards-compat: also accept a bare list at the top level.
        if isinstance(payload, list):
            self._catalog = payload
        else:
            self._catalog = payload.get("entries", [])
        if not self._catalog:
            raise ValueError(f"Agribalyse catalog at {self.catalog_path} is empty.")

    def ensure_embeddings(self) -> None:
        """Load or compute the embedding matrix. Caches to .npy on first build."""
        if self._embeddings is not None:
            return
        if os.path.exists(self.embeddings_cache_path):
            self._embeddings = np.load(self.embeddings_cache_path)
            if self._embeddings.shape[0] != len(self._catalog):
                logger.warning(
                    "Embeddings cache shape %s does not match catalog size %d; "
                    "rebuilding.",
                    self._embeddings.shape,
                    len(self._catalog),
                )
                self._embeddings = None
            else:
                return
        if self.embedding_client is None:
            raise RuntimeError(
                "AgribalyseIndex needs an OpenAI client to build embeddings on "
                "first use (no .npy cache found). Pass embedding_client=... or "
                "pre-populate the cache."
            )
        texts = [self._embedding_text(e) for e in self._catalog]
        response = self.embedding_client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        # OpenAI SDK 1.x: response.data is a list of objects with .embedding.
        vectors = np.asarray([row.embedding for row in response.data], dtype=np.float32)
        self._embeddings = vectors
        os.makedirs(os.path.dirname(self.embeddings_cache_path), exist_ok=True)
        np.save(self.embeddings_cache_path, vectors)
        logger.info("Persisted %d Agribalyse embeddings to %s", vectors.shape[0], self.embeddings_cache_path)

    @staticmethod
    def _embedding_text(entry: Dict[str, Any]) -> str:
        """Concatenate LCI name + category path for richer retrieval context."""
        return f"{entry.get('lci_name', '')} | {entry.get('agribalyse_category', '')}".strip()

    @property
    def catalog(self) -> List[Dict[str, Any]]:
        return self._catalog

    @property
    def embeddings(self) -> Optional[np.ndarray]:
        return self._embeddings

    def __len__(self) -> int:
        return len(self._catalog)


class EmbeddingRetriever:
    """Cosine-similarity top-k retrieval over an AgribalyseIndex.

    Uses the same OpenAI embedding model as the index for query vectors.
    """

    def __init__(
        self,
        index: AgribalyseIndex,
        embedding_client: Optional[Any] = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.index = index
        self.embedding_client = embedding_client or index.embedding_client
        self.embedding_model = embedding_model

    def retrieve(self, query: str, k: int = DEFAULT_TOP_K) -> List[Tuple[Dict[str, Any], float]]:
        """Return top-k (catalog_entry, cosine_similarity) pairs, ranked descending."""
        self.index.ensure_embeddings()
        embeddings = self.index.embeddings
        if embeddings is None or len(self.index) == 0:
            return []
        if self.embedding_client is None:
            raise RuntimeError(
                "EmbeddingRetriever needs an OpenAI client to embed queries. "
                "Pass embedding_client=... at construction time."
            )
        response = self.embedding_client.embeddings.create(
            model=self.embedding_model,
            input=[query],
        )
        q = np.asarray(response.data[0].embedding, dtype=np.float32)
        # Normalize for cosine (avoid recomputing norm of catalog every call:
        # we accept the per-query cost here for simplicity at bootstrap scale).
        q_norm = q / (np.linalg.norm(q) + 1e-12)
        m_norms = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12)
        sims = m_norms @ q_norm  # (n,)
        k = min(k, len(self.index))
        top_idx = np.argpartition(-sims, k - 1)[:k]
        top_idx_sorted = top_idx[np.argsort(-sims[top_idx])]
        return [(self.index.catalog[i], float(sims[i])) for i in top_idx_sorted]


class LCAMatcher:
    """Orchestrator: retrieve top-k → constrained-output LLM rank →
    confidence-thresholded fallback. Cached per food_id in-memory.

    When `ranking_client` is None (no API key), the matcher degrades gracefully
    to retrieval-only top-1 with `confidence = embedding_similarity` and
    `justification = "embedding-similarity-only (no LLM key configured)"`.
    This lets the test suite run without an API key.
    """

    SYSTEM_PROMPT = (
        "You are matching a Canadian Nutrient File (CNF) food entry to its "
        "closest Agribalyse 3.2 life-cycle inventory (LCI) entry. Pick exactly "
        "ONE candidate from the provided list (you may not invent a Ciqual code). "
        "Reason over food composition, processing route, and provenance. Respond "
        "with JSON only."
    )

    def __init__(
        self,
        index: AgribalyseIndex,
        retriever: EmbeddingRetriever,
        ranking_client: Optional[Any] = None,
        *,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        top_k: int = DEFAULT_TOP_K,
        model: str = DEFAULT_RANKING_MODEL,
        max_tokens: int = 200,
        temperature: float = 0.0,
    ):
        self.index = index
        self.retriever = retriever
        self.ranking_client = ranking_client
        self.confidence_threshold = confidence_threshold
        self.top_k = top_k
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._cache: Dict[int, MatchResult] = {}

    def match(
        self, food_id: int, food_description: str, food_group: Optional[str] = None
    ) -> MatchResult:
        if food_id in self._cache:
            return self._cache[food_id]

        candidates = self.retriever.retrieve(food_description, k=self.top_k)
        if not candidates:
            result = MatchResult(
                food_id=food_id, matched=False, fallback_reason="no_candidates"
            )
            self._cache[food_id] = result
            return result

        candidate_records = [
            {"ciqual_code": c["ciqual_code"], "lci_name": c["lci_name"],
             "agribalyse_category": c.get("agribalyse_category", ""),
             "similarity": sim}
            for c, sim in candidates
        ]

        if self.ranking_client is None:
            # Degraded mode: return retrieval-only top-1 with similarity as
            # confidence. Useful for offline/test environments without an API key.
            top, top_sim = candidates[0]
            result = MatchResult(
                food_id=food_id,
                matched=top_sim >= self.confidence_threshold,
                ciqual_code=top["ciqual_code"],
                lci_name=top.get("lci_name"),
                confidence=top_sim,
                justification="embedding-similarity-only (no LLM key configured)",
                midpoint_factors=top.get("midpoint_factors_per_100g") if top_sim >= self.confidence_threshold else None,
                fallback_reason=None if top_sim >= self.confidence_threshold else "low_confidence",
                candidates_considered=candidate_records,
            )
            self._cache[food_id] = result
            return result

        # LLM ranking with constrained-set output.
        prompt = self._build_prompt(food_description, food_group, candidates)
        try:
            raw_response = self._query_llm(prompt)
            parsed = self._parse_llm_json(raw_response)
        except Exception as exc:  # noqa: BLE001 - log + fallback
            logger.warning("LCAMatcher LLM call failed for food_id=%s: %s", food_id, exc)
            result = MatchResult(
                food_id=food_id, matched=False, fallback_reason="exception",
                justification=f"exception: {exc!r}",
                candidates_considered=candidate_records,
            )
            self._cache[food_id] = result
            return result

        proposed_code = parsed.get("ciqual_code")
        confidence = float(parsed.get("confidence", 0.0))
        justification = str(parsed.get("justification", "")).strip()[:240]

        # Validate that the LLM picked one of the retrieved candidates.
        # Per LEAF (Krahmer 2024) 0.19 hallucination rate on bare GPT-3.5
        # zero-shot — we explicitly reject any free-generated Ciqual code.
        candidate_codes = {c["ciqual_code"]: c for c, _ in candidates}
        if proposed_code not in candidate_codes:
            logger.info(
                "LCAMatcher rejected hallucinated ciqual_code=%r for food_id=%s "
                "(not in retrieved candidate set)",
                proposed_code, food_id,
            )
            result = MatchResult(
                food_id=food_id, matched=False, fallback_reason="hallucinated_code",
                justification=f"LLM proposed {proposed_code!r} not in candidate set",
                candidates_considered=candidate_records,
            )
            self._cache[food_id] = result
            return result

        if confidence < self.confidence_threshold:
            result = MatchResult(
                food_id=food_id, matched=False, fallback_reason="low_confidence",
                ciqual_code=proposed_code,
                lci_name=candidate_codes[proposed_code].get("lci_name"),
                confidence=confidence,
                justification=justification,
                candidates_considered=candidate_records,
            )
            self._cache[food_id] = result
            return result

        matched_entry = candidate_codes[proposed_code]
        result = MatchResult(
            food_id=food_id,
            matched=True,
            ciqual_code=proposed_code,
            lci_name=matched_entry.get("lci_name"),
            confidence=confidence,
            justification=justification,
            midpoint_factors=matched_entry.get("midpoint_factors_per_100g"),
            candidates_considered=candidate_records,
        )
        self._cache[food_id] = result
        return result

    def _build_prompt(
        self,
        food_description: str,
        food_group: Optional[str],
        candidates: List[Tuple[Dict[str, Any], float]],
    ) -> str:
        lines = [
            f"Food: {food_description}",
        ]
        if food_group:
            lines.append(f"CNF food group: {food_group}")
        lines.append("")
        lines.append("Candidates (ranked by embedding similarity):")
        for entry, sim in candidates:
            lines.append(
                f"  {entry['ciqual_code']}: {entry['lci_name']} "
                f"[{entry.get('agribalyse_category', '')}] (sim={sim:.3f})"
            )
        lines.append("")
        lines.append(
            'Respond with JSON: {"ciqual_code": "<one of the above codes exactly>", '
            '"confidence": <float 0-1>, "justification": "<≤30 words>"}'
        )
        lines.append(
            "confidence = your subjective probability this is the correct match "
            "given food composition, processing and provenance."
        )
        return "\n".join(lines)

    def _query_llm(self, prompt: str) -> str:
        """Currently only OpenAI client is supported for the matcher (HENI
        categorizer carries multi-provider routing; matcher follows in
        GROUP-D-CODE-1.x-C as needed)."""
        response = self.ranking_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"

    @staticmethod
    def _parse_llm_json(raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
            return {}


def build_default_matcher(
    api_key: Optional[str] = None,
    *,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    top_k: int = DEFAULT_TOP_K,
) -> LCAMatcher:
    """Convenience constructor used by the API layer and the verification
    snippet in the GROUP-D-RECONCILIATION plan. Reads the OpenAI API key
    from the supplied `api_key` arg or, failing that, the `OPENAI_API_KEY`
    env var. When no key is available, returns a matcher in degraded
    (retrieval-only) mode — useful for offline/test environments.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    client = None
    if key:
        try:
            import openai
            client = openai.OpenAI(api_key=key)
        except ImportError:  # pragma: no cover - openai is in requirements.txt
            logger.warning("openai package not importable; matcher in degraded mode")
            client = None
    index = AgribalyseIndex(embedding_client=client)
    retriever = EmbeddingRetriever(index, embedding_client=client)
    return LCAMatcher(
        index=index,
        retriever=retriever,
        ranking_client=client,
        confidence_threshold=confidence_threshold,
        top_k=top_k,
    )
