"""Dietary-pattern resemblance via embedding similarity (DIET-PATTERN-1, 2026-05-24).

Given a user's aggregated daily ingredient list (typically from the 24-h
recall wizard's `aggregated_daily_ingredients` output), compute a mass-
weighted "day vector" in the same 1,536-dim embedding space the CNF /
WAFCT matcher uses ([`cnf_corpus_embeddings.npz`](backend/api/data/cnf_corpus_embeddings.npz)),
then cosine-rank it against a library of literature-anchored prototype
patterns (Mediterranean, DASH, Western, Vegetarian, Vegan, CFG-Healthy,
West African Staple, optional EAT-Lancet).

Design choices documented in [`DIETARY_PATTERN_JUSTIFICATION.md`](DIETARY_PATTERN_JUSTIFICATION.md):
- **Descriptive resemblance**, not classification. Top-3 patterns reported
  simultaneously with cosine values; no single binary label.
- **Mass-weighted day vector**, L2-normalised so cosine is invariant to
  total energy / portion scaling.
- **Cosine + softmax** for an interpretable probability-like share.
- **Confidence bands** (high / moderate / low) gate the strength of the
  user-facing claim.
- **Co-leading patterns** within 0.05 cosine of the top are reported
  jointly to avoid spurious tie-breaking.
- **Reuses CNFCorpus** ([`cnf_matcher.py`](backend/api/services/cnf_matcher.py))
  for the embedding source — zero new ETL, zero new model.
- **Per-process LRU cache** (size 100) keyed on the (sorted FoodID, mass)
  tuple of the input — same pattern as the matcher + decomposer.

Audience-aware (see `cnf_ai_search_views.dietary_pattern_classify`):
- Individual mode: top-3 resemblances, blurb per prototype, mandatory
  single-day caveat. EAT-Lancet hidden.
- Researcher / policy: + literature_anchor, outcome_evidence_reused,
  per-prototype distinctive_user_foods. EAT-Lancet visible.

Mandatory caveat (every audience): "Today's day-vector is one snapshot.
For usual-eating-pattern claims, log multiple recall days. Prototype
outcome citations refer to populations following each pattern long-term,
not to single-day resemblance."
"""
from __future__ import annotations

import json
import logging
import math
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# --- Tunables -------------------------------------------------------------

PROTOTYPES_PATH = (Path(__file__).resolve().parents[1]
                   / 'data' / 'dietary_pattern_prototypes.json')

# Softmax temperature — lower = sharper distribution. T=0.1 over cosines in
# [0.3, 0.95] makes a 0.10 cosine gap translate to ~3× softmax share ratio,
# which feels right for "this pattern is clearly the winner" framing while
# still surfacing co-leaders.
SOFTMAX_TEMPERATURE = 0.1

# Confidence-band thresholds. `high` requires both a high absolute cosine
# AND a meaningful gap to the runner-up (so a 0.78/0.77 split is correctly
# called 'moderate' even though both are absolutely high).
CONFIDENCE_HIGH_COSINE = 0.75
CONFIDENCE_HIGH_GAP    = 0.05
CONFIDENCE_MOD_COSINE  = 0.60

# Co-leading band — any pattern within this cosine of the top is reported
# as a joint leader alongside the winner.
CO_LEADING_GAP = 0.05

DEFAULT_CACHE_SIZE = 100


# --- Result payloads ------------------------------------------------------

@dataclass
class PatternResemblance:
    """One prototype's resemblance score for a user's day vector."""
    pattern_id:                str
    display_name:              str
    cosine:                    float
    softmax_share:             float                       # [0, 1], sums to 1 across visible prototypes
    distinctive_user_foods:    List[Dict[str, Any]] = field(default_factory=list)  # researcher-mode
    literature_anchor:         str  = ''                   # researcher-mode
    outcome_evidence_reused:   str  = ''                   # researcher-mode
    individual_mode_blurb:     str  = ''                   # always shown

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id':              self.pattern_id,
            'display_name':            self.display_name,
            'cosine':                  round(self.cosine, 3),
            'softmax_share':           round(self.softmax_share, 3),
            'distinctive_user_foods':  self.distinctive_user_foods,
            'literature_anchor':       self.literature_anchor,
            'outcome_evidence_reused': self.outcome_evidence_reused,
            'individual_mode_blurb':   self.individual_mode_blurb,
        }


@dataclass
class PatternResemblanceResult:
    matched:                   bool
    top_pattern:               Optional[str]                       # winning pattern_id
    top_pattern_confidence:    str                                 # 'high' / 'moderate' / 'low'
    co_leading:                List[str] = field(default_factory=list)
    resemblances:              List[PatternResemblance] = field(default_factory=list)
    n_foods:                   int   = 0
    n_foods_unresolved:        int   = 0          # foods not found in corpus (skipped)
    total_mass_g:              float = 0.0
    fallback_reason:           Optional[str] = None
    timing_ms:                 float = 0.0
    cache_hit:                 bool  = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'matched':                self.matched,
            'top_pattern':            self.top_pattern,
            'top_pattern_confidence': self.top_pattern_confidence,
            'co_leading':             self.co_leading,
            'resemblances':           [r.to_dict() for r in self.resemblances],
            'n_foods':                self.n_foods,
            'n_foods_unresolved':     self.n_foods_unresolved,
            'total_mass_g':           round(self.total_mass_g, 1),
            'fallback_reason':        self.fallback_reason,
            'timing_ms':              round(self.timing_ms, 1),
            'cache_hit':              self.cache_hit,
        }


# --- Helpers --------------------------------------------------------------

def _l2_normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def _cache_key(foods: List[Dict[str, Any]], visible: Set[str]) -> Tuple:
    """Cache key — tuple of normalised (food_id, rounded_mass) sorted, plus
    sorted visible prototypes. Independent caching across audience modes."""
    items = sorted(
        (int(f.get('food_id', 0)), round(float(f.get('mass_g', 0)), 1))
        for f in foods if int(f.get('food_id', 0)) > 0 and float(f.get('mass_g', 0)) > 0
    )
    return (tuple(items), tuple(sorted(visible)))


# --- Matcher class --------------------------------------------------------

class DietaryPatternMatcher:
    """Embedding-space prototype resemblance for a user's daily food list."""

    def __init__(
        self,
        corpus,
        prototypes_path: Path = PROTOTYPES_PATH,
        cache_size: int = DEFAULT_CACHE_SIZE,
    ):
        self.corpus = corpus
        self.prototypes_path = prototypes_path
        self._raw: Dict[str, Any] = {}
        self._prototypes: List[Dict[str, Any]] = []
        # FoodID -> corpus row index. Built once on init.
        self._food_id_to_idx: Dict[int, int] = {
            int(fid): i for i, fid in enumerate(corpus.food_ids)
        }
        # Lazy: built on first classify() call.
        self._prototype_vectors: Optional[Dict[str, np.ndarray]] = None
        self._cache: 'dict[Tuple, PatternResemblanceResult]' = {}
        self._cache_order: List[Tuple] = []
        self._cache_size = cache_size
        self._cache_lock = threading.Lock()
        self._build_lock = threading.Lock()

        self._load_prototypes()

    def _load_prototypes(self) -> None:
        if not self.prototypes_path.exists():
            raise FileNotFoundError(
                f'Dietary pattern prototypes not found at {self.prototypes_path}'
            )
        with open(self.prototypes_path, encoding='utf-8') as f:
            self._raw = json.load(f)
        self._prototypes = self._raw.get('prototypes', [])
        if not self._prototypes:
            raise ValueError(f'No prototypes in {self.prototypes_path}')
        logger.info('DietaryPatternMatcher loaded %d prototypes from %s',
                    len(self._prototypes), self.prototypes_path)

    # --- Vector construction --------------------------------------------

    def _build_day_vector(
        self,
        foods: List[Dict[str, Any]],
    ) -> Tuple[Optional[np.ndarray], int, int, float, List[Tuple[int, float, np.ndarray]]]:
        """Build a mass-weighted L2-normalised day vector from a foods list.

        Returns:
            day_vector: 1,536-dim float32 or None if no foods resolved
            n_resolved: count of foods found in the corpus
            n_unresolved: count of foods skipped (FoodID not in corpus)
            total_mass: sum of resolved foods' masses
            per_food_traces: [(food_id, mass_g, embedding)] for distinctive-foods analysis
        """
        accum: Optional[np.ndarray] = None
        total_mass = 0.0
        n_resolved = 0
        n_unresolved = 0
        per_food_traces: List[Tuple[int, float, np.ndarray]] = []

        for f in foods:
            try:
                fid = int(f.get('food_id', 0))
                mass = float(f.get('mass_g', 0))
            except (TypeError, ValueError):
                n_unresolved += 1
                continue
            if fid <= 0 or mass <= 0:
                n_unresolved += 1
                continue
            idx = self._food_id_to_idx.get(fid)
            if idx is None:
                logger.debug('DietaryPatternMatcher: FoodID %d not in corpus; skipping', fid)
                n_unresolved += 1
                continue
            emb = self.corpus.embeddings[idx]
            weighted = emb * mass
            accum = weighted if accum is None else accum + weighted
            total_mass += mass
            n_resolved += 1
            per_food_traces.append((fid, mass, emb))

        if accum is None or total_mass <= 0:
            return None, n_resolved, n_unresolved, total_mass, per_food_traces
        day_vector = _l2_normalize(accum / total_mass)
        return day_vector, n_resolved, n_unresolved, total_mass, per_food_traces

    # --- Prototype vector cache -----------------------------------------

    def _ensure_prototype_vectors(self) -> Dict[str, np.ndarray]:
        if self._prototype_vectors is not None:
            return self._prototype_vectors
        with self._build_lock:
            if self._prototype_vectors is not None:
                return self._prototype_vectors
            out: Dict[str, np.ndarray] = {}
            for proto in self._prototypes:
                pid = proto['pattern_id']
                example_vectors: List[np.ndarray] = []
                for day in proto.get('example_days', []):
                    vec, n_res, _, _, _ = self._build_day_vector(day.get('foods', []))
                    if vec is not None and n_res >= 1:
                        example_vectors.append(vec)
                    else:
                        logger.warning(
                            'DietaryPatternMatcher: prototype %r example day %r '
                            'failed to build a day vector (resolved %d foods); '
                            'skipping this example day', pid, day.get('name'), n_res,
                        )
                if not example_vectors:
                    logger.error(
                        'DietaryPatternMatcher: prototype %r has 0 valid example days '
                        '— it will not participate in scoring', pid,
                    )
                    continue
                proto_mean = np.mean(np.vstack(example_vectors), axis=0)
                out[pid] = _l2_normalize(proto_mean)
            self._prototype_vectors = out
            logger.info('DietaryPatternMatcher built %d prototype vectors', len(out))
            return out

    # --- Public ----------------------------------------------------------

    def classify(
        self,
        foods: List[Dict[str, Any]],
        prototypes_visible: Optional[Set[str]] = None,
        include_distinctive_foods: bool = True,
    ) -> PatternResemblanceResult:
        """Compute resemblance of the foods' day vector against each
        visible prototype.

        Args:
            foods: list of `{'food_id': int, 'mass_g': float}`. May include
                food_description / food_group / occasions keys — they are
                ignored.
            prototypes_visible: set of pattern_id strings to score against.
                None = all prototypes. The view layer filters this by
                audience mode (e.g. excludes 'eat_lancet' for individual).
            include_distinctive_foods: if True, compute per-prototype top-3
                user foods that contributed most to that prototype's score.
                Slightly more expensive; turn off for individual mode.
        """
        t0 = time.perf_counter()
        prototype_vectors = self._ensure_prototype_vectors()
        visible = set(prototypes_visible) if prototypes_visible else set(prototype_vectors.keys())
        visible &= set(prototype_vectors.keys())
        if not visible:
            return PatternResemblanceResult(
                matched=False, top_pattern=None, top_pattern_confidence='low',
                fallback_reason='no_visible_prototypes',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )

        cache_key = _cache_key(foods, visible)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return PatternResemblanceResult(
                **{**cached.__dict__,
                   'cache_hit': True,
                   'timing_ms': (time.perf_counter() - t0) * 1000},
            )

        day_vector, n_res, n_unres, total_mass, per_food_traces = self._build_day_vector(foods)
        if day_vector is None:
            result = PatternResemblanceResult(
                matched=False, top_pattern=None, top_pattern_confidence='low',
                n_foods=n_res, n_foods_unresolved=n_unres, total_mass_g=total_mass,
                fallback_reason='no_foods_resolved',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(cache_key, result)
            return result

        # Cosine vs each visible prototype
        cosines: Dict[str, float] = {}
        for pid in visible:
            pv = prototype_vectors[pid]
            cosines[pid] = float(np.dot(day_vector, pv))

        # Softmax over visible prototypes
        max_cos = max(cosines.values())
        exps = {pid: math.exp((c - max_cos) / SOFTMAX_TEMPERATURE)
                for pid, c in cosines.items()}
        Z = sum(exps.values())
        shares = {pid: e / Z for pid, e in exps.items()}

        # Build resemblance list, sorted by cosine desc
        proto_lookup = {p['pattern_id']: p for p in self._prototypes}
        resemblances: List[PatternResemblance] = []
        for pid in sorted(cosines.keys(), key=lambda p: -cosines[p]):
            proto = proto_lookup[pid]
            distinctive = (self._distinctive_foods(per_food_traces, prototype_vectors[pid])
                           if include_distinctive_foods else [])
            resemblances.append(PatternResemblance(
                pattern_id=pid,
                display_name=proto.get('display_name', pid),
                cosine=cosines[pid],
                softmax_share=shares[pid],
                distinctive_user_foods=distinctive,
                literature_anchor=proto.get('literature_anchor', ''),
                outcome_evidence_reused=proto.get('outcome_evidence_reused', ''),
                individual_mode_blurb=proto.get('individual_mode_blurb', ''),
            ))

        top = resemblances[0]
        runner_up_cos = resemblances[1].cosine if len(resemblances) > 1 else -1.0
        gap = top.cosine - runner_up_cos

        if top.cosine >= CONFIDENCE_HIGH_COSINE and gap >= CONFIDENCE_HIGH_GAP:
            confidence = 'high'
        elif top.cosine >= CONFIDENCE_MOD_COSINE:
            confidence = 'moderate'
        else:
            confidence = 'low'

        co_leading = [
            r.pattern_id for r in resemblances[1:]
            if (top.cosine - r.cosine) <= CO_LEADING_GAP
        ]

        result = PatternResemblanceResult(
            matched=True,
            top_pattern=top.pattern_id,
            top_pattern_confidence=confidence,
            co_leading=co_leading,
            resemblances=resemblances,
            n_foods=n_res,
            n_foods_unresolved=n_unres,
            total_mass_g=total_mass,
            timing_ms=(time.perf_counter() - t0) * 1000,
        )
        self._cache_put(cache_key, result)
        return result

    # --- Distinctive foods ----------------------------------------------

    @staticmethod
    def _distinctive_foods(
        per_food_traces: List[Tuple[int, float, np.ndarray]],
        prototype_vector: np.ndarray,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Top-k user foods that contribute most to this prototype's cosine.

        Contribution = mass_g × cosine(food_embedding, prototype_vector).
        Captures both "you ate a lot of it" AND "it semantically resembles
        the prototype".
        """
        if not per_food_traces:
            return []
        scored: List[Tuple[int, float, float, float]] = []
        for fid, mass, emb in per_food_traces:
            cos = float(np.dot(emb, prototype_vector))
            scored.append((fid, mass, cos, mass * cos))
        scored.sort(key=lambda r: -r[3])
        return [
            {'food_id': fid, 'mass_g': round(mass, 1),
             'cosine_to_prototype': round(cos, 3),
             'contribution': round(contrib, 3)}
            for fid, mass, cos, contrib in scored[:top_k]
        ]

    # --- LRU cache -------------------------------------------------------

    def _cache_get(self, key: Tuple) -> Optional[PatternResemblanceResult]:
        with self._cache_lock:
            r = self._cache.get(key)
            if r is None:
                return None
            try:
                self._cache_order.remove(key)
            except ValueError:
                pass
            self._cache_order.append(key)
            return r

    def _cache_put(self, key: Tuple, value: PatternResemblanceResult) -> None:
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

    # --- Audience-mode helper -------------------------------------------

    def visible_for(self, user_type: str) -> Set[str]:
        """Per-mode visible prototype IDs (reads from the JSON's
        individual_mode_visible / researcher_mode_visible keys)."""
        key = ('researcher_mode_visible'
               if user_type in ('researcher', 'policy')
               else 'individual_mode_visible')
        return set(self._raw.get(key, [p['pattern_id'] for p in self._prototypes]))


# --- Factory --------------------------------------------------------------

@lru_cache(maxsize=1)
def get_default_pattern_matcher() -> DietaryPatternMatcher:
    """Process-wide singleton wired to the same corpus the CNFMatcher uses."""
    from .cnf_matcher import get_default_matcher
    return DietaryPatternMatcher(corpus=get_default_matcher().corpus)
