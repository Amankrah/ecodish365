"""LLM-assisted recipe decomposition into CNF ingredients (AI-MATCH-1).

Parallel to ``backend/environmental_impact_model/src/recipe_decomposer.py``
but the target catalog is the 5,691-row CNF (not Agribalyse).

Pipeline is TWO-STAGE — different from the LCA-side decomposer (which uses
constrained vocabulary from a single retrieved pool):

    Stage 1 — LLM decomposes the dish name + total mass into a free-text
              ingredient list with mass proportions (no constraint to a
              specific CNF subset). This lets the LLM reach for the right
              ingredients regardless of which CNF entries the embedding
              search would have surfaced.

    Stage 2 — Each free-text ingredient string is resolved to a CNF FoodID
              via ``CNFMatcher.match()`` (which has its own embedding +
              LLM-rank pipeline with hallucination rejection). Ingredients
              that fail to resolve at ≥ INGREDIENT_RESOLUTION_FLOOR (0.6)
              are dropped; their mass is added to ``unresolved_mass_g``.

Then the 7 validation gates from recipe_decomposer.py apply:
  1. min_ingredients ≥ 2 (single-ingredient direct-match exception via CNF
     matcher path — caller should use AIEnhancedSearch instead, not the decomposer)
  2. mass closure within tolerance = max(5 g, 2 % of target)
  3. decomposition_confidence ≥ 0.30 (calibrated anchors)
  4. unresolved_mass ≤ 10 % of total
  5. each ingredient resolves to a real CNF FoodID (no hallucinations — Stage 2 enforces)
  6. each ingredient's mass > 0
  7. duplicate CNF FoodIDs deduped (sum masses)

Caching: per normalised (dish_name, total_mass_g) tuple. Process-wide LRU,
size 200 (recipes are heavier than search queries, so smaller cap).
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# --- Tunables -------------------------------------------------------------

DEFAULT_DECOMPOSITION_CONFIDENCE_THRESHOLD = 0.30
DEFAULT_MIN_INGREDIENTS = 2
DEFAULT_MAX_INGREDIENTS = 10
DEFAULT_MAX_UNRESOLVED_FRACTION = 0.10
DEFAULT_INGREDIENT_RESOLUTION_FLOOR = 0.6        # per-ingredient CNFMatcher confidence floor
DEFAULT_PARTIAL_RESOLUTION_FLOOR = 0.60          # need ≥60 % of mass resolved to return partial
DEFAULT_AUTO_CREDIT_UNRESOLVED = True
DEFAULT_RANKING_MODEL = 'gpt-4.1-mini'
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 600


_NORMALISE_RE = re.compile(r'\s+')


def _normalise_dish_name(name: str) -> str:
    return _NORMALISE_RE.sub(' ', name.strip().lower())


def _mass_tolerance(target_mass_g: float) -> float:
    """Scale-aware tolerance: max(5 g, 2 % of target)."""
    return max(5.0, target_mass_g * 0.02)


# --- Result payloads ------------------------------------------------------

@dataclass
class CNFIngredient:
    food_id: int
    food_description: str
    food_group: str
    mass_g: float
    rationale: str = ''
    # Stage-2 (CNFMatcher) per-ingredient confidence — researcher / policy
    # mode surfaces this; individual mode hides it.
    resolution_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'food_id': self.food_id,
            'food_description': self.food_description,
            'food_group': self.food_group,
            'mass_g': round(self.mass_g, 2),
            'rationale': self.rationale,
            'resolution_confidence': round(self.resolution_confidence, 3),
        }


@dataclass
class CNFDecomposedRecipe:
    dish_name: str
    normalised_dish_name: str
    total_mass_g: float                              # the input target
    matched: bool = False                            # True iff all gates passed
    ingredients: List[CNFIngredient] = field(default_factory=list)
    resolved_mass_g: float = 0.0                     # sum of ingredient mass_g
    unresolved_mass_g: float = 0.0                   # explicit residual + dropped-low-confidence
    decomposition_confidence: float = 0.0
    fallback_reason: Optional[str] = None
    cache_hit: bool = False
    timing_ms: float = 0.0
    # Stage-2 audit: ingredients the LLM proposed but that failed Stage-2
    # resolution (mass + free-text name + reason). For research-grade
    # defensibility.
    unresolved_ingredients_audit: List[Dict[str, Any]] = field(default_factory=list)
    raw_llm_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'dish_name': self.dish_name,
            'normalised_dish_name': self.normalised_dish_name,
            'total_mass_g': round(self.total_mass_g, 2),
            'matched': self.matched,
            'ingredients': [i.to_dict() for i in self.ingredients],
            'resolved_mass_g': round(self.resolved_mass_g, 2),
            'unresolved_mass_g': round(self.unresolved_mass_g, 2),
            'decomposition_confidence': round(self.decomposition_confidence, 3),
            'fallback_reason': self.fallback_reason,
            'cache_hit': self.cache_hit,
            'timing_ms': round(self.timing_ms, 1),
            'unresolved_ingredients_audit': self.unresolved_ingredients_audit,
        }


# --- Decomposer class -----------------------------------------------------

class CNFRecipeDecomposer:
    """Two-stage recipe decomposer (LLM decompose → CNFMatcher resolve)."""

    SYSTEM_PROMPT = (
        "You are decomposing a user-supplied dish name into its canonical "
        "ingredient list with mass proportions, for nutritional scoring "
        "against the Canadian Nutrient File (CNF). Output free-text "
        "ingredient names (NOT CNF FoodIDs — those are resolved downstream).\n\n"
        "MASS CLOSURE RULE: sum(ingredient.mass_g) + unresolved_mass_g MUST "
        "equal the stated total mass within ±2 %. If your explicit "
        "ingredients leave a residual (water, oil for cooking, minor "
        "seasonings, etc.), put that residual in `unresolved_mass_g`. "
        "Do NOT leave the mass unbalanced.\n\n"
        "ING REDIENT NAMES: prefer specific, generic English names that map "
        "well to CNF entries (e.g. \"chicken breast, cooked\" rather than "
        "\"poultry\"; \"olive oil\" rather than \"vegetable fat\"). Avoid "
        "brand names and ultra-specific cuts the CNF won't carry. State "
        "cooked vs raw where it matters.\n\n"
        "CONFIDENCE CALIBRATION: `decomposition_confidence` = P(a "
        "nutrition curator would call this list LCA-equivalent to the dish). "
        "If you ran this 10 times with different proportions within plausible "
        "bounds, what fraction would still be equivalent? Anchors:\n"
        "  - 0.90 = canonical recipe; ingredients + proportions well-established\n"
        "  - 0.70 = ingredients clearly right; proportions approximate\n"
        "  - 0.50 = ingredients plausible; significant proportion uncertainty\n"
        "  - 0.30 = guessing at one or more ingredients\n"
        "  - 0.10 = no canonical recipe; reaching\n"
        "Vary your confidence — do not default to a single value.\n\n"
        "Respond with JSON only:\n"
        "  {\n"
        "    \"ingredients\": [\n"
        "      {\"name\": \"<specific generic name>\", \"mass_g\": <float>, \"rationale\": \"<≤30 words>\"}\n"
        "    ],\n"
        "    \"unresolved_mass_g\": <float>,\n"
        "    \"decomposition_confidence\": <float 0-1>\n"
        "  }"
    )

    def __init__(
        self,
        cnf_matcher,
        chat_json_client: Optional[Any] = None,
        *,
        confidence_threshold: float = DEFAULT_DECOMPOSITION_CONFIDENCE_THRESHOLD,
        max_ingredients: int = DEFAULT_MAX_INGREDIENTS,
        ingredient_resolution_floor: float = DEFAULT_INGREDIENT_RESOLUTION_FLOOR,
        partial_resolution_floor: float = DEFAULT_PARTIAL_RESOLUTION_FLOOR,
        max_unresolved_fraction: float = DEFAULT_MAX_UNRESOLVED_FRACTION,
        auto_credit_unresolved: bool = DEFAULT_AUTO_CREDIT_UNRESOLVED,
        model: str = DEFAULT_RANKING_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        cache_size: int = 200,
    ):
        self.cnf_matcher = cnf_matcher
        self.chat_json_client = chat_json_client
        self.confidence_threshold = confidence_threshold
        self.max_ingredients = max_ingredients
        self.ingredient_resolution_floor = ingredient_resolution_floor
        self.partial_resolution_floor = partial_resolution_floor
        self.max_unresolved_fraction = max_unresolved_fraction
        self.auto_credit_unresolved = auto_credit_unresolved
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._cache_size = cache_size
        self._cache: 'dict[Tuple[str, float], CNFDecomposedRecipe]' = {}
        self._cache_order: List[Tuple[str, float]] = []
        self._cache_lock = threading.Lock()

    # --- public ----------------------------------------------------------

    def decompose(self, dish_name: str, total_mass_g: float) -> CNFDecomposedRecipe:
        t0 = time.perf_counter()
        if not dish_name or not dish_name.strip():
            return CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name='',
                total_mass_g=total_mass_g, matched=False,
                fallback_reason='empty_dish_name',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
        if total_mass_g <= 0:
            return CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name='',
                total_mass_g=total_mass_g, matched=False,
                fallback_reason='non_positive_mass',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )

        ndn = _normalise_dish_name(dish_name)
        key = (ndn, round(total_mass_g, 1))
        cached = self._cache_get(key)
        if cached is not None:
            return CNFDecomposedRecipe(
                **{**cached.__dict__,
                   'dish_name': dish_name,
                   'cache_hit': True,
                   'timing_ms': (time.perf_counter() - t0) * 1000},
            )

        if self.chat_json_client is None:
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                fallback_reason='no_llm_client',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        # Stage 1: LLM decomposition
        try:
            parsed = self._stage1_decompose(dish_name, total_mass_g)
        except Exception as exc:  # noqa: BLE001
            logger.warning('CNFRecipeDecomposer Stage-1 failed for dish=%r: %s', ndn, exc)
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                fallback_reason=f'stage1_exception:{exc!r}',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        raw_llm = json.dumps(parsed) if isinstance(parsed, dict) else str(parsed)

        # Validate Stage 1 shape
        if 'ingredients' not in parsed or not isinstance(parsed['ingredients'], list):
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                fallback_reason='missing_ingredients_field',
                raw_llm_response=raw_llm,
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        raw_ings = parsed['ingredients'][:self.max_ingredients]
        explicit_unresolved = float(parsed.get('unresolved_mass_g', 0.0) or 0.0)
        confidence = float(parsed.get('decomposition_confidence', 0.0) or 0.0)

        # Stage 2: resolve each ingredient → CNF FoodID
        resolved: List[CNFIngredient] = []
        dropped_audit: List[Dict[str, Any]] = []
        dropped_mass = 0.0
        for raw_ing in raw_ings:
            name = str(raw_ing.get('name', '')).strip()
            mass = raw_ing.get('mass_g')
            try:
                mass_f = float(mass)
            except (TypeError, ValueError):
                continue
            if mass_f <= 0 or not name:
                continue
            try:
                m = self.cnf_matcher.match(name)
            except Exception as exc:  # noqa: BLE001
                dropped_audit.append({
                    'name': name, 'mass_g': mass_f,
                    'reason': f'matcher_exception:{exc!r}',
                })
                dropped_mass += mass_f
                continue
            if (not m.matched or m.food_id is None
                    or m.confidence < self.ingredient_resolution_floor):
                dropped_audit.append({
                    'name': name, 'mass_g': mass_f,
                    'matcher_food_id': m.food_id,
                    'matcher_confidence': round(m.confidence, 3),
                    'reason': f'resolution_below_floor:{m.confidence:.2f}<{self.ingredient_resolution_floor:.2f}'
                              if m.matched else (m.fallback_reason or 'matcher_no_match'),
                })
                dropped_mass += mass_f
                continue
            resolved.append(CNFIngredient(
                food_id=int(m.food_id),
                food_description=m.food_description or '',
                food_group=m.food_group or '',
                mass_g=mass_f,
                rationale=str(raw_ing.get('rationale', '')).strip()[:240],
                resolution_confidence=m.confidence,
            ))

        # Deduplicate resolved ingredients (LLM occasionally repeats)
        by_id: Dict[int, CNFIngredient] = {}
        for ing in resolved:
            if ing.food_id in by_id:
                # Sum masses; keep higher confidence
                existing = by_id[ing.food_id]
                existing.mass_g += ing.mass_g
                existing.resolution_confidence = max(existing.resolution_confidence,
                                                     ing.resolution_confidence)
            else:
                by_id[ing.food_id] = ing
        resolved = list(by_id.values())
        resolved_mass = sum(i.mass_g for i in resolved)

        # Combine unresolved-from-LLM + dropped-from-Stage-2
        unresolved_mass = explicit_unresolved + dropped_mass

        # --- Gate validation -------------------------------------------

        # Gate 1: min ingredients (after Stage-2 resolution)
        if len(resolved) < DEFAULT_MIN_INGREDIENTS:
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                ingredients=resolved, resolved_mass_g=resolved_mass,
                unresolved_mass_g=unresolved_mass,
                decomposition_confidence=confidence,
                fallback_reason=f'too_few_ingredients:{len(resolved)}<{DEFAULT_MIN_INGREDIENTS}',
                unresolved_ingredients_audit=dropped_audit,
                raw_llm_response=raw_llm,
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        # Gate 2: mass closure (auto-credit small shortfalls into unresolved)
        tolerance = _mass_tolerance(total_mass_g)
        total = resolved_mass + unresolved_mass
        shortfall = total_mass_g - total
        max_auto_credit = total_mass_g * self.max_unresolved_fraction - unresolved_mass
        if (self.auto_credit_unresolved and shortfall > tolerance
                and shortfall <= max(0.0, max_auto_credit)):
            unresolved_mass += shortfall
            total = total_mass_g

        if abs(total - total_mass_g) > tolerance:
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                ingredients=resolved, resolved_mass_g=resolved_mass,
                unresolved_mass_g=unresolved_mass,
                decomposition_confidence=confidence,
                fallback_reason=(f'mass_imbalance:resolved+unresolved={total:.1f} '
                                 f'vs target={total_mass_g:.1f} (tol={tolerance:.1f})'),
                unresolved_ingredients_audit=dropped_audit,
                raw_llm_response=raw_llm,
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        # Gate 3: unresolved fraction not too large
        if unresolved_mass > total_mass_g * self.max_unresolved_fraction:
            # Partial-success mode (plan §risk #8): if at least
            # PARTIAL_RESOLUTION_FLOOR of mass resolved with adequate
            # confidence, return matched=True with a benign audit tag.
            resolved_frac = resolved_mass / total_mass_g if total_mass_g > 0 else 0.0
            if resolved_frac >= self.partial_resolution_floor:
                result = CNFDecomposedRecipe(
                    dish_name=dish_name, normalised_dish_name=ndn,
                    total_mass_g=total_mass_g, matched=True,
                    ingredients=resolved, resolved_mass_g=resolved_mass,
                    unresolved_mass_g=unresolved_mass,
                    decomposition_confidence=confidence,
                    fallback_reason=f'partial_resolution:{resolved_frac:.2f}_of_mass_resolved',
                    unresolved_ingredients_audit=dropped_audit,
                    raw_llm_response=raw_llm,
                    timing_ms=(time.perf_counter() - t0) * 1000,
                )
                self._cache_put(key, result)
                return result
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                ingredients=resolved, resolved_mass_g=resolved_mass,
                unresolved_mass_g=unresolved_mass,
                decomposition_confidence=confidence,
                fallback_reason=(f'unresolved_mass_too_large:{unresolved_mass:.1f} '
                                 f'(> {self.max_unresolved_fraction:.0%} of {total_mass_g:.1f})'),
                unresolved_ingredients_audit=dropped_audit,
                raw_llm_response=raw_llm,
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        # Gate 4: decomposition confidence threshold
        if confidence < self.confidence_threshold:
            result = CNFDecomposedRecipe(
                dish_name=dish_name, normalised_dish_name=ndn,
                total_mass_g=total_mass_g, matched=False,
                ingredients=resolved, resolved_mass_g=resolved_mass,
                unresolved_mass_g=unresolved_mass,
                decomposition_confidence=confidence,
                fallback_reason=f'low_confidence:{confidence:.2f}<{self.confidence_threshold:.2f}',
                unresolved_ingredients_audit=dropped_audit,
                raw_llm_response=raw_llm,
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
            self._cache_put(key, result)
            return result

        # All gates passed
        result = CNFDecomposedRecipe(
            dish_name=dish_name, normalised_dish_name=ndn,
            total_mass_g=total_mass_g, matched=True,
            ingredients=resolved, resolved_mass_g=resolved_mass,
            unresolved_mass_g=unresolved_mass,
            decomposition_confidence=confidence,
            unresolved_ingredients_audit=dropped_audit,
            raw_llm_response=raw_llm,
            timing_ms=(time.perf_counter() - t0) * 1000,
        )
        self._cache_put(key, result)
        return result

    # --- Stage 1 ---------------------------------------------------------

    def _stage1_decompose(self, dish_name: str, total_mass_g: float) -> Dict[str, Any]:
        user = (
            f'Dish: {dish_name}\n'
            f'Total mass: {total_mass_g:.1f} g\n\n'
            f'Decompose this dish into its canonical ingredient list with '
            f'mass_g values per ingredient, plus an `unresolved_mass_g` '
            f'residual + a `decomposition_confidence` score. Up to '
            f'{self.max_ingredients} ingredients.'
        )
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

    # --- LRU cache -------------------------------------------------------

    def _cache_get(self, key: Tuple[str, float]) -> Optional[CNFDecomposedRecipe]:
        with self._cache_lock:
            r = self._cache.get(key)
            if r is None:
                return r
            try:
                self._cache_order.remove(key)
            except ValueError:
                pass
            self._cache_order.append(key)
            return r

    def _cache_put(self, key: Tuple[str, float], value: CNFDecomposedRecipe) -> None:
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
def get_default_decomposer() -> CNFRecipeDecomposer:
    """Process-wide singleton wired to the same ChatJSONClient as the matcher."""
    from .cnf_matcher import get_default_matcher
    matcher = get_default_matcher()
    return CNFRecipeDecomposer(
        cnf_matcher=matcher,
        chat_json_client=matcher.chat_json_client,
    )
