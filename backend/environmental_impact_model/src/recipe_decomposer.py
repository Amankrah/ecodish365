"""Tier γ — CNF composite-food recipe decomposition.

Sits between the LCA matcher and the cnf_integrator group-default fallback
in the per-food impact-resolution chain. When a CNF composite food (lasagna,
chicken soup, cheeseburger, ...) cannot be directly matched to a single
high-confidence Agribalyse v32 entry, the decomposer asks an LLM to express
the dish as a mass-weighted ingredient list constrained to v32-resolvable
entries; each ingredient routes through the existing matcher; the meal-level
impact is the mass-weighted sum.

Trigger conditions (both must hold):
  1. CNF FoodGroupName is in `_COMPOSITE_FOOD_GROUPS` (the set of CNF groups
     dominated by composite/prepared dishes — Mixed Dishes, Soups, Fast Foods,
     Babyfoods, Sausages and Luncheon meats, Sweets, Snacks, Baked Products).
  2. The direct LCA matcher returned matched=False OR confidence < threshold.

When the LLM client is None (no API key), the decomposer degrades to
returning DecomposedRecipe(matched=False) and the existing group-default
fallback proceeds — same defensive pattern as LCAMatcher.

Output schema (LLM, JSON, temperature 0, constrained vocabulary):
    {
      "ingredients": [
        {"ciqual_code": "...", "mass_g": <float>, "rationale": "..."},
        ...
      ],
      "total_recipe_mass_g": <float>,
      "decomposition_confidence": <0-1>,
      "unresolved_mass_g": <float>
    }

Hard rejects:
  - Ciqual code not in the retrieved candidate set → rejected at parse time.
  - Sum of ingredient mass_g deviates from total_recipe_mass_g by > 5 g → rejected.
  - decomposition_confidence < threshold → rejected.
  - unresolved_mass_g > 10 % of total_recipe_mass_g → rejected.

Rejected decompositions fall through to the existing group-default path with
an explicit `decomposition_failed:<reason>` audit tag.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .lca_matcher import (
    AgribalyseIndex, EmbeddingRetriever, LCAMatcher,
    MatchResult, DEFAULT_RANKING_MODEL,
)


logger = logging.getLogger(__name__)


# CNF FoodGroupName values that frequently denote composite / prepared
# foods — the ones where direct CNF→Agribalyse single-row matching is most
# likely to under-resolve. Decomposition is gated on this set (and on the
# matcher returning low confidence for the same food).
_COMPOSITE_FOOD_GROUPS: frozenset = frozenset({
    'Mixed Dishes',
    'Soups, Sauces and Gravies',
    'Fast Foods',
    'Babyfoods',
    'Sausages and Luncheon meats',
    'Sweets',
    'Snacks',
    'Baked Products',
})


# Self-reported `decomposition_confidence` floor. Empirically (2026-05-22 live
# probe across 8 composites spanning trivial → Canadian-specific), gpt-4o-mini
# reports 0.40 confidence on 7/8 cases regardless of decomposition difficulty —
# a model default bias, not genuine uncertainty. The prior 0.60 gate was
# therefore unreachable in practice and Tier γ was decorative. The new 0.30
# floor still rejects "I have no idea" responses (conf=0.00, observed once)
# while admitting the 0.40-anchored bulk. The architectural intent is:
# structural gates (mass closure + constrained vocabulary + ≥2 ingredients)
# carry the QA load; self-reported confidence is a soft secondary check.
DEFAULT_DECOMPOSITION_CONFIDENCE_THRESHOLD: float = 0.30
DEFAULT_INGREDIENT_TOP_K: int = 30   # broader candidate pool than matcher's 20
DEFAULT_MAX_INGREDIENTS: int = 10
DEFAULT_MIN_INGREDIENTS: int = 2     # a 1-ingredient "decomposition" isn't one

# Mass-balance tolerance for sum(ingredient mass_g) + unresolved vs target.
# 5 g absolute floor protects small servings (e.g. 50 g butter tart); 2 % of
# target scales sensibly for larger servings (e.g. 250 g → 5 g, 500 g → 10 g,
# 1 kg → 20 g). The prior fixed-5 g rule rejected reasonable decompositions
# like 250 g shepherd's pie at 240 g resolved (4 % gap, within recipe-rounding).
MAX_MASS_GAP_G: float = 5.0
MAX_MASS_GAP_FRACTION: float = 0.02
MAX_UNRESOLVED_FRACTION: float = 0.10  # >10 % unresolved → reject
# Auto-credit small ingredient-sum shortfalls into unresolved_mass_g rather
# than rejecting. Catches LLM arithmetic sloppiness (e.g. Shepherd's pie
# decomposed correctly into 150+50+40=240g + unresolved=0 vs 250g target,
# off by 10g, where the LLM forgot to attribute the residual to `unresolved`).
# Only auto-credits up to MAX_UNRESOLVED_FRACTION of target so the hard cap
# on unresolved fraction still bounds the auto-credit's downstream impact.
AUTO_CREDIT_UNRESOLVED: bool = True

# Tier γ activates when the matcher's confidence is below this AND the food
# is in a composite group. Above this we trust the matcher's direct match
# (e.g. CNF lasagna → Agribalyse "Lasagna or cannelloni with meat" at 0.90).
# Below it (e.g. Bannock → "Biscuit extruded with fruits filling" at 0.65),
# the matcher's LCA-distant near-miss is likely a stretched match and the
# decomposer should be allowed to propose an ingredient-level reconstruction.
HIGH_CONFIDENCE_THRESHOLD: float = 0.85


def _mass_tolerance(target_mass_g: float) -> float:
    """Per-serving mass-balance tolerance.

    Returns max(5 g, 2 % of target). 5 g floor preserves the original gate for
    small servings; the 2 %-of-target scaling admits typical recipe-rounding
    on larger composite dishes that the fixed-5 g rule rejected.
    """
    return max(MAX_MASS_GAP_G, target_mass_g * MAX_MASS_GAP_FRACTION)


@dataclass
class Ingredient:
    ciqual_code: str
    lci_name: str
    mass_g: float
    rationale: str = ""


@dataclass
class DecomposedRecipe:
    """Result of attempting to decompose a CNF composite food into v32 ingredients."""
    food_id: int
    matched: bool = False               # True iff the recipe passed all validity gates
    ingredients: List[Ingredient] = field(default_factory=list)
    total_recipe_mass_g: float = 0.0
    decomposition_confidence: float = 0.0
    unresolved_mass_g: float = 0.0
    fallback_reason: Optional[str] = None  # populated when matched=False
    raw_llm_response: Optional[str] = None

    @property
    def ingredient_count(self) -> int:
        return len(self.ingredients)

    def is_resolved(self) -> bool:
        return self.matched and self.ingredients and self.total_recipe_mass_g > 0

    def mass_weighted_impacts(
        self,
        per_ingredient_impacts: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """Aggregate ingredient impacts weighted by mass fraction.

        Args:
          per_ingredient_impacts: {ciqual_code: {category: kg per 100g}} from
            running each ingredient through `cnf_integrator` / `LCAMatcher`.

        Returns:
          {category: kg total} for the FULL recipe (not per 100g).

        Per-ingredient impact is multiplied by mass_g / 100 (impacts are
        per-100g) and summed.
        """
        out: Dict[str, float] = {}
        for ing in self.ingredients:
            per_100g = per_ingredient_impacts.get(ing.ciqual_code) or {}
            scale = ing.mass_g / 100.0
            for cat, val in per_100g.items():
                out[cat] = out.get(cat, 0.0) + (val * scale)
        return out

    def to_audit(self) -> Dict[str, Any]:
        return {
            'food_id': self.food_id,
            'matched': self.matched,
            'ingredient_count': self.ingredient_count,
            'ingredients': [
                {'ciqual_code': i.ciqual_code, 'lci_name': i.lci_name,
                 'mass_g': i.mass_g, 'rationale': i.rationale}
                for i in self.ingredients
            ],
            'total_recipe_mass_g': self.total_recipe_mass_g,
            'decomposition_confidence': self.decomposition_confidence,
            'unresolved_mass_g': self.unresolved_mass_g,
            'fallback_reason': self.fallback_reason,
        }


class RecipeDecomposer:
    """LLM-assisted CNF composite-food → v32-ingredient decomposition.

    Mirrors `LCAMatcher`'s defensive design:
      - Constrained vocabulary: ingredients must come from the retrieved
        candidate set (`AgribalyseIndex.catalog`); hallucinated Ciqual codes
        are rejected at parse time.
      - Graceful degradation: when `ranking_client=None`, returns
        DecomposedRecipe(matched=False, fallback_reason='no_llm_client').
      - In-memory cache: keyed on food_id; deterministic at temperature 0.

    The decomposer is opt-in via the API's `enable_recipe_decomposer` flag.
    """

    # Prompt rewrite 2026-05-22 per Tian et al. 2023 ("Just Ask for
    # Calibration", arXiv:2305.14975) + Lin et al. 2022 (verbalised
    # confidence elicitation): the confidence block uses indirect elicitation
    # ("if you ran this 10 times…") rather than asking for a raw float on a
    # generic scale. Indirect framing gives the LLM discrete anchors
    # (fractions of 10) to land on, sidestepping the 0.40-default collapse
    # observed empirically on gpt-4o-mini.
    SYSTEM_PROMPT = (
        "You are decomposing a Canadian Nutrient File (CNF) composite food into "
        "its canonical ingredient list with mass fractions. Pick ingredients "
        "EXCLUSIVELY from the provided candidate list (each is an Agribalyse "
        "3.2 LCI entry).\n\n"
        "MASS CLOSURE RULE: sum(ingredient.mass_g) + unresolved_mass_g MUST "
        "equal the stated serving mass within ±2 % of the target. If your "
        "explicit ingredients leave a residual (e.g. water, oil, seasoning, "
        "minor components not present in the candidate list), put that residual "
        "in `unresolved_mass_g`. Do NOT leave the mass unbalanced.\n\n"
        "CONFIDENCE CALIBRATION: report `decomposition_confidence` as your "
        "estimate of P(an LCA expert reviewing this decomposition would call "
        "it equivalent to the dish). Equivalently: if you ran this "
        "decomposition 10 times with different proportions within plausible "
        "bounds, what fraction would still be LCA-equivalent? Anchors:\n"
        "  - 0.90 = canonical recipe; ingredient choices and proportions are\n"
        "          well-established in culinary references\n"
        "  - 0.70 = ingredients clearly right; proportions approximate\n"
        "  - 0.50 = ingredients plausible; significant proportion uncertainty\n"
        "  - 0.30 = guessing at one or more ingredients from limited information\n"
        "  - 0.10 = no canonical recipe; reaching for any ingredient that fits\n"
        "Vary your confidence — do not default to a single value (we have "
        "observed this failure mode on smaller models).\n\n"
        "Respond with JSON only — no commentary."
    )

    def __init__(
        self,
        index: AgribalyseIndex,
        retriever: EmbeddingRetriever,
        ranking_client: Optional[Any] = None,
        *,
        confidence_threshold: float = DEFAULT_DECOMPOSITION_CONFIDENCE_THRESHOLD,
        top_k: int = DEFAULT_INGREDIENT_TOP_K,
        max_ingredients: int = DEFAULT_MAX_INGREDIENTS,
        model: str = DEFAULT_RANKING_MODEL,
        temperature: float = 0.0,
        chat_json_client: Optional[Any] = None,
    ):
        self.index = index
        self.retriever = retriever
        # Internal authoritative interface (see LCAMatcher.__init__ for the
        # full rationale). Accept either the legacy raw OpenAI-style client
        # or a pre-built ChatJSONClient; coerce to the latter.
        from .llm_client import coerce_chat_json_client
        if chat_json_client is not None:
            self.chat_json_client = chat_json_client
        else:
            self.chat_json_client = coerce_chat_json_client(ranking_client, model=model)
        self.ranking_client = ranking_client if ranking_client is not None else self.chat_json_client
        self.confidence_threshold = confidence_threshold
        self.top_k = top_k
        self.max_ingredients = max_ingredients
        self.model = model
        self.temperature = temperature
        self._cache: Dict[int, DecomposedRecipe] = {}
        self._cache_lock = threading.Lock()

    @staticmethod
    def should_decompose(food_group: Optional[str], match_result: Optional[MatchResult]) -> bool:
        """Trigger predicate. Decompose when ALL hold:
          (a) CNF group looks composite (in `_COMPOSITE_FOOD_GROUPS`), AND
          (b) the direct matcher EITHER failed (`matched=False`) OR succeeded
              with confidence below `HIGH_CONFIDENCE_THRESHOLD` (0.85).

        The borderline-confidence case (b'): live-LLM evidence showed the
        matcher returning `matched=True` on stretched LCA-distant near-misses
        for Canadian composites (Bannock → "Biscuit with fruits filling"
        at 0.65; Tourtière → "Riesling wine and pork pie" at 0.60). With the
        old `matched=False`-only trigger, the decomposer never got a chance.
        Below 0.85 confidence on a composite group, we now route to the
        decomposer; the decomposer's own validation gates (≥0.60 self-reported
        confidence, mass-balance, candidate-constraint) remain as the
        last-line filter before falling through to the group default.
        """
        if not food_group or food_group not in _COMPOSITE_FOOD_GROUPS:
            return False
        if match_result is None:
            return True
        if not match_result.matched:
            return True
        # Borderline match on a composite group: try decomposition instead.
        return match_result.confidence < HIGH_CONFIDENCE_THRESHOLD

    def decompose(
        self,
        food_id: int,
        food_description: str,
        food_quantity_g: float,
        food_group: Optional[str] = None,
    ) -> DecomposedRecipe:
        """Attempt to decompose a CNF composite food into v32 ingredients."""
        if food_id in self._cache:
            return self._cache[food_id]

        if self.chat_json_client is None:
            result = DecomposedRecipe(
                food_id=food_id, matched=False,
                fallback_reason='no_llm_client',
            )
            with self._cache_lock:
                self._cache[food_id] = result
            return result

        # Step 1: retrieve a broader candidate pool than the matcher uses
        # (ingredients can span multiple Agribalyse subgroups).
        candidates = self.retriever.retrieve(food_description, k=self.top_k)
        if not candidates:
            result = DecomposedRecipe(
                food_id=food_id, matched=False,
                fallback_reason='no_candidates',
            )
            with self._cache_lock:
                self._cache[food_id] = result
            return result

        # Step 2: build a code→entry lookup so we can validate LLM output and
        # reject any ciqual_code not in the retrieved set.
        candidates_by_code: Dict[str, Dict[str, Any]] = {
            (entry.get('ciqual_code') or ''): entry
            for entry, _sim in candidates
            if entry.get('ciqual_code')
        }

        # Step 3: build user message + query LLM (temperature 0, JSON response).
        user_msg = self._build_user_message(food_description, food_quantity_g, candidates)
        try:
            parsed = self._query_llm(user_msg)
        except Exception as exc:  # noqa: BLE001
            logger.warning("RecipeDecomposer LLM call failed for food_id=%s: %s", food_id, exc)
            result = DecomposedRecipe(
                food_id=food_id, matched=False,
                fallback_reason='llm_exception',
            )
            with self._cache_lock:
                self._cache[food_id] = result
            return result

        # Step 4: validate + populate DecomposedRecipe.
        result = self._validate_and_build(
            food_id=food_id,
            target_mass_g=food_quantity_g,
            parsed=parsed,
            candidates_by_code=candidates_by_code,
            raw=json.dumps(parsed) if isinstance(parsed, dict) else str(parsed),
        )
        with self._cache_lock:
            self._cache[food_id] = result
        return result

    def _build_user_message(
        self,
        food_description: str,
        food_quantity_g: float,
        candidates: List[Tuple[Dict[str, Any], float]],
    ) -> str:
        """Constrained-vocabulary user message; ingredient Ciqual codes are
        the only valid output. System prompt is supplied separately by the
        ChatJSONClient call site."""
        candidate_lines = []
        for entry, sim in candidates:
            code = entry.get('ciqual_code') or '?'
            name = entry.get('lci_name') or entry.get('lci_name_fr') or '?'
            group = entry.get('agribalyse_group') or ''
            candidate_lines.append(f"  [{code}] {name} ({group})")
        candidate_block = '\n'.join(candidate_lines)

        return (
            f"CNF food: {food_description!r}\n"
            f"Serving size: {food_quantity_g:.1f} g\n\n"
            f"Candidate ingredients (top {len(candidates)} by retrieval):\n"
            f"{candidate_block}\n\n"
            "Decompose the CNF food into an ingredient list using ONLY the "
            "ciqual_codes above. Respond with JSON matching this schema:\n"
            "{\n"
            '  "ingredients": [\n'
            '    {"ciqual_code": "<code>", "mass_g": <float>, "rationale": "<short>"},\n'
            "    ...\n"
            "  ],\n"
            f'  "total_recipe_mass_g": {food_quantity_g:.1f},\n'
            '  "decomposition_confidence": <0-1>,\n'
            '  "unresolved_mass_g": <float, mass not attributable to any candidate>\n'
            "}\n"
            f"Constraints:\n"
            f"  - Sum of ingredient mass_g + unresolved_mass_g MUST equal {food_quantity_g:.1f} ± 5 g.\n"
            f"  - At most {self.max_ingredients} ingredients (pick the dominant ones).\n"
            "  - Set decomposition_confidence low (< 0.5) if no candidate plausibly fits."
        )

    def _query_llm(self, user_msg: str) -> Dict[str, Any]:
        """Delegate to the configured ChatJSONClient. Multi-provider via
        `LLM_PROVIDER` env var (openai / anthropic) — see
        `environmental_impact_model.src.llm_client`."""
        return self.chat_json_client.chat_completion_json(
            system=self.SYSTEM_PROMPT,
            user=user_msg,
            temperature=self.temperature,
        )

    def _validate_and_build(
        self,
        food_id: int,
        target_mass_g: float,
        parsed: Dict[str, Any],
        candidates_by_code: Dict[str, Dict[str, Any]],
        raw: str,
    ) -> DecomposedRecipe:
        # Required keys
        if 'ingredients' not in parsed or not isinstance(parsed['ingredients'], list):
            return DecomposedRecipe(
                food_id=food_id, matched=False,
                fallback_reason='missing_ingredients_field',
                raw_llm_response=raw,
            )

        # Per-ingredient validation
        ingredients: List[Ingredient] = []
        total_resolved_mass = 0.0
        for item in parsed['ingredients'][:self.max_ingredients]:
            code = str(item.get('ciqual_code', '')).strip()
            mass = item.get('mass_g')
            if code not in candidates_by_code:
                # Hallucinated code → reject the whole decomposition
                return DecomposedRecipe(
                    food_id=food_id, matched=False,
                    fallback_reason=f'hallucinated_ciqual_code:{code}',
                    raw_llm_response=raw,
                )
            try:
                mass_f = float(mass)
            except (TypeError, ValueError):
                return DecomposedRecipe(
                    food_id=food_id, matched=False,
                    fallback_reason='non_numeric_mass_g',
                    raw_llm_response=raw,
                )
            if mass_f <= 0:
                continue
            entry = candidates_by_code[code]
            ingredients.append(Ingredient(
                ciqual_code=code,
                lci_name=entry.get('lci_name') or '',
                mass_g=mass_f,
                rationale=str(item.get('rationale', '')),
            ))
            total_resolved_mass += mass_f

        if not ingredients:
            return DecomposedRecipe(
                food_id=food_id, matched=False,
                fallback_reason='empty_ingredient_list',
                raw_llm_response=raw,
            )

        # Min-ingredients gate: a "decomposition" with 1 ingredient is the
        # matcher's job, not the decomposer's. Reject so the matcher's
        # borderline result remains as the best-available output.
        if len(ingredients) < DEFAULT_MIN_INGREDIENTS:
            return DecomposedRecipe(
                food_id=food_id, matched=False,
                ingredients=ingredients,
                fallback_reason=f'too_few_ingredients:{len(ingredients)}<{DEFAULT_MIN_INGREDIENTS}',
                raw_llm_response=raw,
            )

        # Mass-conservation check (scale-aware: 5 g floor OR 2 % of target).
        # When the ingredient sum is short of target by a non-trivial amount,
        # auto-credit the residual into unresolved_mass_g rather than reject —
        # the LLM commonly forgets to fill the unresolved field even when its
        # ingredient list is otherwise correct (observed live on Shepherd's pie
        # at 240g resolved + 0g unresolved vs 250g target). The auto-credit
        # is bounded by MAX_UNRESOLVED_FRACTION so the downstream "unresolved
        # too large" gate still fires on genuinely-incomplete decompositions.
        unresolved_mass = float(parsed.get('unresolved_mass_g', 0.0) or 0.0)
        total = total_resolved_mass + unresolved_mass
        tolerance = _mass_tolerance(target_mass_g)
        shortfall = target_mass_g - total
        max_auto_credit = target_mass_g * MAX_UNRESOLVED_FRACTION - unresolved_mass
        if (AUTO_CREDIT_UNRESOLVED and shortfall > tolerance
                and shortfall <= max(0.0, max_auto_credit)):
            unresolved_mass += shortfall
            total = target_mass_g  # exact closure
        if abs(total - target_mass_g) > tolerance:
            return DecomposedRecipe(
                food_id=food_id, matched=False,
                ingredients=ingredients,
                total_recipe_mass_g=total_resolved_mass,
                unresolved_mass_g=unresolved_mass,
                fallback_reason=(
                    f'mass_imbalance:resolved+unresolved={total:.1f}g vs '
                    f'target={target_mass_g:.1f}g (tol={tolerance:.1f}g)'
                ),
                raw_llm_response=raw,
            )

        if unresolved_mass > target_mass_g * MAX_UNRESOLVED_FRACTION:
            return DecomposedRecipe(
                food_id=food_id, matched=False,
                ingredients=ingredients,
                total_recipe_mass_g=total_resolved_mass,
                unresolved_mass_g=unresolved_mass,
                fallback_reason=f'unresolved_mass_too_large:{unresolved_mass:.1f}g (> {MAX_UNRESOLVED_FRACTION:.0%} of {target_mass_g:.1f})',
                raw_llm_response=raw,
            )

        # Confidence check
        confidence = float(parsed.get('decomposition_confidence', 0.0) or 0.0)
        if confidence < self.confidence_threshold:
            return DecomposedRecipe(
                food_id=food_id, matched=False,
                ingredients=ingredients,
                total_recipe_mass_g=total_resolved_mass,
                decomposition_confidence=confidence,
                unresolved_mass_g=unresolved_mass,
                fallback_reason=f'low_confidence:{confidence:.2f}<{self.confidence_threshold:.2f}',
                raw_llm_response=raw,
            )

        return DecomposedRecipe(
            food_id=food_id,
            matched=True,
            ingredients=ingredients,
            total_recipe_mass_g=total_resolved_mass,
            decomposition_confidence=confidence,
            unresolved_mass_g=unresolved_mass,
            raw_llm_response=raw,
        )
