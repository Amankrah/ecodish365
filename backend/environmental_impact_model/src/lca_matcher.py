"""LCA matcher (§3.5): CNF food → Agribalyse 3.2 LCI entry via retrieval-augmented
LLM ranking with confidence-scored fallback to Poore & Nemecek group means.

Architecture (per GROUP-D-RECONCILIATION plan, anchored on Zhou et al. 2025
NutriRAG, Krahmer 2024 LEAF, and Furrer et al. 2024):

  food description ──▶ EmbeddingRetriever (cosine sim, top-k=20) ──▶
                       LLM ranking (gpt-4.1-mini default; multi-provider
                       via ChatJSONClient, T=0, JSON-only, output
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

# Default: the AGRIBALYSE-INGEST v32 catalog (~2,425 entries, deterministically
# generated from the Tableur Aout25 workbook). The bootstrap path is kept
# available as an explicit constructor arg for backwards compatibility and
# offline tests.
DEFAULT_BOOTSTRAP_CATALOG_PATH = os.path.join(_DATA_DIR, "agribalyse_v32_catalog.json")
DEFAULT_EMBEDDINGS_CACHE_PATH = os.path.join(_DATA_DIR, "agribalyse_v32_embeddings.npy")
DEFAULT_META_PATH = os.path.join(_DATA_DIR, "agribalyse_v32_catalog_meta.json")
# Pre-AGRIBALYSE-INGEST bootstrap (54-entry hand-curated; kept for tests).
LEGACY_BOOTSTRAP_CATALOG_PATH = os.path.join(_DATA_DIR, "agribalyse_bootstrap.json")
LEGACY_BOOTSTRAP_EMBEDDINGS_PATH = os.path.join(_DATA_DIR, "agribalyse_bootstrap_embeddings.npy")

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"  # 1536-dim; $0.02/1M tokens
# 2026-05-22: upgraded from "gpt-4o-mini" to "gpt-4.1-mini". gpt-4o-mini
# anchored verbalised confidence at 0.40 on 7/8 probes regardless of
# difficulty — a hard model-default bias. gpt-4.1-mini matches gpt-4o on
# IFEval (84.1 %) at ~83 % lower cost than gpt-4o, has strict JSON Schema
# support, and is the recommended drop-in for constrained-JSON ranking.
DEFAULT_RANKING_MODEL = "gpt-4.1-mini"
DEFAULT_CONFIDENCE_THRESHOLD = 0.6  # manuscript §3.5
DEFAULT_TOP_K = 20  # NutriRAG k=5-20 sweep upper end

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Single matcher decision for one CNF food.

    `matched=True` means a high-confidence Agribalyse mapping was made.
    `matched=False` means the matcher fell back to the existing group-default
    LCA pipeline (the audit trail records why).

    Dual-namespace payload (AGRIBALYSE-INGEST): `midpoint_factors` carries the
    ReCiPe-side subset that the existing pipeline consumes; `ef31_indicators`
    carries the full EF 3.1 set with native units, surfaced as sensitivity
    data in `recipe2016_h_ef31_sensitivity`.
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
    # AGRIBALYSE-INGEST additions:
    ef31_indicators: Optional[Dict[str, float]] = None
    unit_metadata: Optional[Dict[str, str]] = None
    dqr: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    catalog_version: Optional[str] = None

    def to_audit(self) -> Dict[str, Any]:
        audit: Dict[str, Any] = {
            "food_id": self.food_id,
            "matched": self.matched,
            "ciqual_code": self.ciqual_code,
            "lci_name": self.lci_name,
            "confidence": self.confidence,
            "justification": self.justification,
            "fallback_reason": self.fallback_reason,
            "n_candidates_considered": len(self.candidates_considered),
            "dqr": self.dqr,
            "warnings": list(self.warnings),
            "catalog_version": self.catalog_version,
        }
        if self.ef31_indicators:
            # Keep the audit payload light: full EF dict only when matched.
            audit["ef31_indicators"] = self.ef31_indicators
            audit["unit_metadata"] = self.unit_metadata
        if self.midpoint_factors:
            # ReCiPe-side overlay (5 keys: GW + 3 climate sub-cols + Strat-OD).
            # Needed by §4.2 divergence panel to inspect matched ReCiPe values
            # for categories trimmed from the v1 consumed midpoint vector.
            audit["midpoint_factors"] = self.midpoint_factors
        return audit


class AgribalyseIndex:
    """Agribalyse 3.2 catalog + precomputed sentence embeddings.

    Default path is the AGRIBALYSE-INGEST v32 catalog (~2,425 deterministically
    generated entries; see `etl/build_agribalyse_v32_catalog.py`). Pass an
    explicit `catalog_path` to use the legacy bootstrap (54 hand-curated rows).

    Embeddings are loaded from the `.npy` cache if present, otherwise computed
    via `embedding_client.embeddings.create(...)` and persisted.
    """

    def __init__(
        self,
        catalog_path: str = DEFAULT_BOOTSTRAP_CATALOG_PATH,
        embeddings_cache_path: str = DEFAULT_EMBEDDINGS_CACHE_PATH,
        embedding_client: Optional[Any] = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        meta_path: Optional[str] = None,
    ):
        self.catalog_path = catalog_path
        self.embeddings_cache_path = embeddings_cache_path
        self.embedding_client = embedding_client
        self.embedding_model = embedding_model
        # Meta path defaults to the canonical v32 meta when the catalog is the
        # v32 file; otherwise None (bootstrap has no meta).
        if meta_path is None and catalog_path == DEFAULT_BOOTSTRAP_CATALOG_PATH:
            meta_path = DEFAULT_META_PATH
        self.meta_path = meta_path
        self._catalog: List[Dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None  # (n, dim)
        self._meta: Dict[str, Any] = {}
        self._load_catalog()
        self._load_meta()

    def _load_catalog(self) -> None:
        with open(self.catalog_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        # JSON schema: top-level dict with "entries" list (v32 + bootstrap).
        # Backwards-compat: also accept a bare list at the top level.
        if isinstance(payload, list):
            self._catalog = payload
        else:
            self._catalog = payload.get("entries", [])
        if not self._catalog:
            raise ValueError(f"Agribalyse catalog at {self.catalog_path} is empty.")

    def _load_meta(self) -> None:
        if self.meta_path and os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as fh:
                self._meta = json.load(fh)

    @property
    def catalog_version(self) -> str:
        """Human-readable catalog version for audit trails."""
        if self._meta:
            return (
                f"agribalyse_v32:{self._meta.get('mapping_version', '?')}"
                f":{self._meta.get('source_file_sha256', '?')[:12]}"
                f":rows={self._meta.get('total_rows', len(self._catalog))}"
            )
        return f"bootstrap:rows={len(self._catalog)}"

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
        # OpenAI /v1/embeddings caps input array at 2,048 items. Batch.
        all_vectors: List[List[float]] = []
        batch_size = 1024
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=batch,
            )
            all_vectors.extend(row.embedding for row in response.data)
        vectors = np.asarray(all_vectors, dtype=np.float32)
        if vectors.shape[0] != len(self._catalog):
            raise RuntimeError(
                f"Embedding shape mismatch: got {vectors.shape[0]} vectors "
                f"for {len(self._catalog)} catalog entries."
            )
        self._embeddings = vectors
        os.makedirs(os.path.dirname(self.embeddings_cache_path), exist_ok=True)
        np.save(self.embeddings_cache_path, vectors)
        logger.info("Persisted %d Agribalyse embeddings to %s", vectors.shape[0], self.embeddings_cache_path)

    @staticmethod
    def _embedding_text(entry: Dict[str, Any]) -> str:
        """Concatenate English LCI name, French product name, and Agribalyse
        category path for richer retrieval. v32 entries carry separate
        `agribalyse_group`/`agribalyse_subgroup` fields; bootstrap entries
        carry a combined `agribalyse_category` string. Both paths produce
        useful retrieval text."""
        parts = [
            entry.get("lci_name", ""),
            entry.get("lci_name_fr", ""),
        ]
        group = entry.get("agribalyse_group", "")
        subgroup = entry.get("agribalyse_subgroup", "")
        if group or subgroup:
            parts.append(f"{group} / {subgroup}".strip(" /"))
        else:
            parts.append(entry.get("agribalyse_category", ""))
        return " | ".join(p for p in parts if p)

    @property
    def catalog(self) -> List[Dict[str, Any]]:
        return self._catalog

    @property
    def embeddings(self) -> Optional[np.ndarray]:
        return self._embeddings

    def __len__(self) -> int:
        return len(self._catalog)


# ---------------------------------------------------------------------------
# Tier β: text canonicalisation + subgroup routing helpers
# ---------------------------------------------------------------------------

# CNF descriptions encode food state as comma-separated modifiers
# ("Squash, summer, crookneck, frozen, unprepared"). Stripping these tokens
# and surfacing them as a separate state_tag improves both retrieval (the
# base_name has higher overlap with Agribalyse entries) and LLM ranking
# (the state_tag tells the ranker to prefer matching-state candidates).
_STATE_TOKENS = frozenset({
    'raw', 'cooked', 'boiled', 'baked', 'broiled', 'fried', 'roasted',
    'grilled', 'steamed', 'sauteed', 'pan-fried', 'pan fried', 'stir-fried',
    'stir fried', 'microwaved',
    'frozen', 'canned', 'dried', 'dehydrated', 'fresh',
    'prepared', 'unprepared', 'homemade',
    'with skin', 'without skin', 'skin removed', 'skin on',
    'low fat', 'fat free', 'reduced fat', 'whole', 'partly skimmed',
    'salted', 'unsalted', 'sweetened', 'unsweetened',
    'jarred', 'all stages', 'condensed',
    'with bones', 'boneless', 'lean only', 'meat only', 'meat and skin',
    'drained', 'undrained',
})


def _canonicalize_food_state(description: str) -> Tuple[str, str]:
    """Split a CNF food description into (base_name, state_tag).

    Examples:
      "Squash, summer, crookneck, frozen, unprepared"
        -> ("Squash summer crookneck", "frozen unprepared")
      "Beef, brain, pan-fried"
        -> ("Beef brain", "pan-fried")
      "Milk, fluid, partly skimmed, 2% M.F."
        -> ("Milk fluid 2% M.F.", "partly skimmed")

    base_name goes to embedding retrieval; state_tag is appended to the LLM
    ranking prompt so the ranker can prefer matching-state Agribalyse entries.
    Stripping is conservative — tokens not in `_STATE_TOKENS` are preserved
    as part of the base name.
    """
    if not description:
        return "", ""
    parts = [p.strip() for p in description.split(',') if p.strip()]
    base_parts: List[str] = []
    state_parts: List[str] = []
    for p in parts:
        if p.lower() in _STATE_TOKENS:
            state_parts.append(p.lower())
        else:
            base_parts.append(p)
    return " ".join(base_parts), " ".join(state_parts)


# Mapping CNF FoodGroupName -> Agribalyse top-level `agribalyse_group` to
# pre-filter retrieval. When CNF group is in this dict, retrieval is
# constrained to candidates whose v32 `agribalyse_group` matches the value.
# Lifts the worst-coverage groups (babyfoods, soups, mixed dishes, fast foods)
# from competing against all 2,425 entries to competing within their natural
# Agribalyse cohort.
_CNF_TO_AGRIBALYSE_SUBGROUP: Dict[str, str] = {
    'Babyfoods':                       'aliments infantiles',
    'Soups, Sauces and Gravies':       'entrées et plats composés',
    'Fast Foods':                      'entrées et plats composés',
    'Mixed Dishes':                    'entrées et plats composés',
    'Sausages and Luncheon meats':     'viandes, œufs, poissons',
    'Beverages':                       'boissons',
    'Fats and Oils':                   'matières grasses',
    'Sweets':                          'produits sucrés',
    # Note: the remaining ~15 CNF groups are left un-routed because their
    # mapping to a single Agribalyse top-level group would discard relevant
    # candidates (e.g. "Cereals, Grains and Pasta" spans multiple Agribalyse
    # subgroups: cereals, baked goods, ready-meals).
}


def _agribalyse_subgroup_for_cnf(cnf_group: Optional[str]) -> Optional[str]:
    """Return the Agribalyse `agribalyse_group` value to pre-filter on, or
    None when the CNF group has no clean single-group counterpart."""
    if not cnf_group:
        return None
    return _CNF_TO_AGRIBALYSE_SUBGROUP.get(cnf_group)


class EmbeddingRetriever:
    """Cosine-similarity top-k retrieval over an AgribalyseIndex.

    Uses the same OpenAI embedding model as the index for query vectors.
    Supports an optional `agribalyse_group_filter` that restricts retrieval
    to a subset of catalog entries — used by Tier β subgroup routing for
    composite-y CNF groups (babyfoods, soups, mixed dishes, fast foods).
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

    def retrieve(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
        agribalyse_group_filter: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Return top-k (catalog_entry, cosine_similarity) pairs, ranked descending.

        When `agribalyse_group_filter` is set, the search is restricted to
        catalog entries whose `agribalyse_group` exactly matches. The filter
        is silently ignored if it would produce < k candidates (falls back
        to full-catalog retrieval to avoid starving the LLM ranker)."""
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
        # Normalize for cosine
        q_norm = q / (np.linalg.norm(q) + 1e-12)
        m_norms = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12)
        sims = m_norms @ q_norm  # (n,)

        # Tier β subgroup routing: mask to the requested Agribalyse group
        # if at least k candidates remain after filtering; otherwise fall
        # back to full catalog to avoid starving the ranker.
        if agribalyse_group_filter:
            mask = np.array(
                [e.get('agribalyse_group') == agribalyse_group_filter for e in self.index.catalog],
                dtype=bool,
            )
            if mask.sum() >= k:
                # Mask out non-matching candidates by setting sim to -inf
                sims = np.where(mask, sims, -np.inf)

        k = min(k, len(self.index))
        top_idx = np.argpartition(-sims, k - 1)[:k]
        top_idx_sorted = top_idx[np.argsort(-sims[top_idx])]
        return [(self.index.catalog[i], float(sims[i])) for i in top_idx_sorted
                if sims[i] > -np.inf]


class LCAMatcher:
    """Orchestrator: retrieve top-k → constrained-output LLM rank →
    confidence-thresholded fallback. Cached per food_id in-memory.

    When `ranking_client` is None (no API key), the matcher degrades gracefully
    to retrieval-only top-1 with `confidence = embedding_similarity` and
    `justification = "embedding-similarity-only (no LLM key configured)"`.
    This lets the test suite run without an API key.
    """

    # Prompt rewrite 2026-05-22 per Tian et al. 2023 ("Just Ask for
    # Calibration", arXiv:2305.14975): verbalised "probability that it is
    # correct" reduces ECE ~50 % vs generic "confidence" on RLHF-tuned
    # models. Anchors are operational LCA-equivalence bands, not generic
    # uncertainty descriptors, so the LLM has discrete targets to land on
    # rather than collapsing to a single default value.
    SYSTEM_PROMPT = (
        "You are matching a Canadian Nutrient File (CNF) food entry to its "
        "closest Agribalyse 3.2 life-cycle inventory (LCI) entry. Pick exactly "
        "ONE candidate from the provided list (you may not invent a Ciqual code). "
        "Reason over food composition, processing route, and provenance.\n\n"
        "CONFIDENCE: report `confidence` as the probability (0.00–1.00) that "
        "an LCA expert reviewing your choice would mark it as the correct "
        "match — NOT a generic \"how sure am I\" score. Calibration anchors:\n"
        "  - 0.95 = near-identical (same commodity, same processing, same form)\n"
        "  - 0.80 = same commodity family, minor processing/form differences\n"
        "  - 0.60 = same broad food group; ingredient-equivalent but not exact\n"
        "  - 0.40 = stretched (different processing or composition; usable as proxy)\n"
        "  - 0.20 = poor match; would prefer no match over this\n"
        "  - 0.00 = no acceptable candidate exists\n"
        "Vary your confidence — do not default to a single value.\n\n"
        "Respond with JSON only."
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
        chat_json_client: Optional[Any] = None,
    ):
        self.index = index
        self.retriever = retriever
        # Internal authoritative interface: a ChatJSONClient (Protocol) that
        # exposes `chat_completion_json(system, user, ...)`. Callers may pass
        # either a raw OpenAI-style client (`ranking_client`, legacy) or a
        # pre-built ChatJSONClient (`chat_json_client`); we coerce to the
        # latter on the way in so the rest of the class has a single path.
        from .llm_client import coerce_chat_json_client
        if chat_json_client is not None:
            self.chat_json_client = chat_json_client
        else:
            self.chat_json_client = coerce_chat_json_client(ranking_client, model=model)
        # Preserve `ranking_client` attribute for any external callers still
        # reading it (e.g. test fixtures, RecipeDecomposer setup in views).
        self.ranking_client = ranking_client if ranking_client is not None else self.chat_json_client
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

        # Tier β: canonicalise CNF description to (base_name, state_tag).
        # base_name goes to retrieval; state_tag is appended to the LLM prompt
        # so the ranker can prefer matching-state candidates.
        base_name, state_tag = _canonicalize_food_state(food_description)
        retrieval_query = base_name or food_description

        # Tier β: subgroup routing for composite-y CNF groups.
        agribalyse_filter = _agribalyse_subgroup_for_cnf(food_group)

        candidates = self.retriever.retrieve(
            retrieval_query, k=self.top_k,
            agribalyse_group_filter=agribalyse_filter,
        )
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
            matched = top_sim >= self.confidence_threshold
            result = self._build_match_result(
                food_id=food_id,
                matched=matched,
                entry=top if matched else None,
                proposed_code=top["ciqual_code"],
                confidence=top_sim,
                justification="embedding-similarity-only (no LLM key configured)",
                fallback_reason=None if matched else "low_confidence",
                candidate_records=candidate_records,
            )
            self._cache[food_id] = result
            return result

        # LLM ranking with constrained-set output. Append the canonicalised
        # state_tag to the food_description visible to the ranker so it can
        # prefer matching-state Agribalyse candidates.
        ranked_description = (
            f"{food_description}  [state: {state_tag}]" if state_tag else food_description
        )
        prompt = self._build_prompt(ranked_description, food_group, candidates)
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
        result = self._build_match_result(
            food_id=food_id,
            matched=True,
            entry=matched_entry,
            proposed_code=proposed_code,
            confidence=confidence,
            justification=justification,
            fallback_reason=None,
            candidate_records=candidate_records,
        )
        self._cache[food_id] = result
        return result

    def _build_match_result(
        self,
        *,
        food_id: int,
        matched: bool,
        entry: Optional[Dict[str, Any]],
        proposed_code: Optional[str],
        confidence: float,
        justification: str,
        fallback_reason: Optional[str],
        candidate_records: List[Dict[str, Any]],
    ) -> MatchResult:
        """Common MatchResult construction respecting the dual-namespace payload.

        v32 entries carry `recipe2016_midpoints_per_100g` + `ef31_indicators_per_100g`
        + `unit_metadata` + `dqr` + `warnings`. Legacy bootstrap entries carry
        the old `midpoint_factors_per_100g` key — fall back to that for
        backwards compatibility.
        """
        midpoint_factors: Optional[Dict[str, float]] = None
        ef31_indicators: Optional[Dict[str, float]] = None
        unit_metadata: Optional[Dict[str, str]] = None
        dqr: Optional[float] = None
        warnings: List[str] = []
        lci_name: Optional[str] = None
        if matched and entry is not None:
            midpoint_factors = entry.get("recipe2016_midpoints_per_100g") or entry.get("midpoint_factors_per_100g")
            ef31_indicators = entry.get("ef31_indicators_per_100g")
            unit_metadata = entry.get("unit_metadata")
            dqr = entry.get("dqr")
            warnings = list(entry.get("warnings") or [])
            lci_name = entry.get("lci_name")
        elif entry is not None:
            # Even on fallback (low confidence, etc.), surface the candidate's
            # lci_name and dqr so the audit trail is informative.
            lci_name = entry.get("lci_name")
            dqr = entry.get("dqr")
        return MatchResult(
            food_id=food_id,
            matched=matched,
            ciqual_code=proposed_code,
            lci_name=lci_name,
            confidence=confidence,
            justification=justification,
            midpoint_factors=midpoint_factors,
            fallback_reason=fallback_reason,
            candidates_considered=candidate_records,
            ef31_indicators=ef31_indicators,
            unit_metadata=unit_metadata,
            dqr=dqr,
            warnings=warnings,
            catalog_version=self.index.catalog_version,
        )

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
            "confidence = P(an LCA expert would call this the correct match). "
            "Anchors in the system message: 0.95 near-identical / 0.80 same family / "
            "0.60 same broad group / 0.40 stretched / 0.20 poor / 0.00 no acceptable."
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
