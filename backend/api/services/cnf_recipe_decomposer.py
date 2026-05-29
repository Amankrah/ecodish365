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
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .cnf_food_type import get_food_type, is_mixed

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

# Catalog preference (2026-05-28): when the dish name itself matches a CNF food that
# has its own measured nutrients, prefer that food over an LLM decomposition.
CATALOG_SHORTCIRCUIT_CONF = 0.88   # use the catalog food directly, skip decomposition
CATALOG_OVERRIDE_CONF = 0.70       # override a bad decomposition with the catalog food
RECON_OVERRIDE_KCAL = 0.25         # |kcal recon error| above this -> override to catalog
RECON_OVERRIDE_MACRO = 0.30        # macro mean-abs-rel error above this -> override


_NORMALISE_RE = re.compile(r'\s+')


def _normalise_dish_name(name: str) -> str:
    return _NORMALISE_RE.sub(' ', name.strip().lower())


def _mass_tolerance(target_mass_g: float) -> float:
    """Scale-aware tolerance: max(10 g, 4 % of target).

    AI-MATCH-1.x (2026-05-23): tolerance widened twice during the prompt
    refinement round:
      - From 5 g → 10 g floor: COOKING-FAT INCLUSION RULE pushes the LLM
        to add 5-15 g of explicit cooking fat without re-balancing other
        ingredients
      - From 2 % → 4 %: complex multi-ingredient dishes (pad thai 320 g,
        jambalaya 350 g) consistently overshoot by 10-14 g once the
        cooking-fat rule is active

    At 4 % the gate still catches genuine LLM failure modes (spelling
    errors that drop major ingredients, mass arithmetic > 4 % off) without
    flaking on the cooking-fat overshoot. Tablespoon ≈ 15 g for context.
    """
    return max(10.0, target_mass_g * 0.04)


def _should_override_with_catalog(
    recon: Optional[Dict[str, Any]],
    decomp_matched: bool,
    kcal_thresh: float = RECON_OVERRIDE_KCAL,
    macro_thresh: float = RECON_OVERRIDE_MACRO,
) -> bool:
    """Decide whether to replace a decomposition with a confidently-matched catalog food.

    Pure (no I/O) so the gate logic is unit-testable without an LLM.
      - failed decomposition  -> override (the confident catalog food is better)
      - no reconstruction      -> keep the decomposition (can't assess; don't second-guess)
      - reconstruction diverges (kcal or macro error over threshold) -> override
    """
    if not decomp_matched:
        return True
    if recon is None:
        return False
    kcal = recon.get('kcal_rel_error')
    macro = recon.get('macro_mean_abs_rel_error')
    return ((kcal is not None and kcal > kcal_thresh)
            or (macro is not None and macro > macro_thresh))


def _catalog_food_is_overridable(food_id: int) -> bool:
    """Food-type guard on the catalog override: only collapse a dish onto a catalog
    food that is itself a MIXED dish (so "chicken soup" -> a measured soup is allowed,
    but "beef stew" -> "Beef, ground" is not). Unlabeled (None, e.g. WAFCT) -> not
    overridable, which keeps the decomposition. Pure (no I/O beyond the cached label
    lookup) so the gate is unit-testable."""
    return is_mixed(int(food_id)) is True


# A dish whose name names MULTIPLE eaten items — a main plus a separate drink or side
# ("beef patty with a glass of orange juice", "burger and a coke") — must be decomposed,
# never collapsed onto a single catalog food (which would silently drop the second item).
# We target explicit second-item signals (portioned beverages/sides, "and a/an/some",
# "plus", "&", "+"), NOT bare "with"/"and" — so single dishes that merely use those words
# as recipe descriptors ("split pea soup with ham", "macaroni and cheese", "fish and
# chips", "chicken with rice") keep the catalog-preference accuracy benefit.
_COMPOUND_MEAL_RE = re.compile(
    r'\b(?:glass|cup|mug|bottle|can|bowl|plate|side|serving|order|scoop|slice|piece)\s+of\b'
    r'|\band\s+(?:a|an|some)\b'
    r'|\bwith\s+(?:a|an)\s+(?:glass|cup|mug|bottle|can|side|drink|soda|pop|juice|coffee|'
    r'tea|smoothie|shake|water|beer|wine|milk)\b'
    r'|\bplus\b'
    r'|\s[&+]\s',
    re.IGNORECASE,
)


def _is_compound_meal(dish_name: str) -> bool:
    """True when the dish name denotes multiple eaten items (main + drink/side)."""
    return bool(_COMPOUND_MEAL_RE.search(dish_name or ''))


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
    # 'single' | 'mixed' | None: whether this resolved CNF food is itself a single
    # ingredient or a mixed dish (None when unlabeled, e.g. WAFCT). A resolved
    # ingredient that is itself a mixed dish means Stage-1 handed back a dish rather
    # than an ingredient — surfaced via the recipe's dish_as_ingredient_count so the
    # lab can see that failure mode instead of it being silent.
    food_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'food_id': self.food_id,
            'food_description': self.food_description,
            'food_group': self.food_group,
            'mass_g': round(self.mass_g, 2),
            'rationale': self.rationale,
            'resolution_confidence': round(self.resolution_confidence, 3),
            'food_type': self.food_type,
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
    # AI-MATCH-1.x (2026-05-23): free-text description of what the
    # unresolved residual IS. Sourced from the Stage-1 LLM's new
    # `unresolved_description` field. Prevents the silent-residual problem
    # (a "5 g unresolved" could be negligible seasoning OR a material
    # 45-kcal oil residue — the description disambiguates).
    unresolved_description: str = ''
    decomposition_confidence: float = 0.0
    fallback_reason: Optional[str] = None
    cache_hit: bool = False
    timing_ms: float = 0.0
    # Stage-2 audit: ingredients the LLM proposed but that failed Stage-2
    # resolution (mass + free-text name + reason). For research-grade
    # defensibility.
    unresolved_ingredients_audit: List[Dict[str, Any]] = field(default_factory=list)
    raw_llm_response: Optional[str] = None
    # Count of resolved ingredients that are themselves mixed dishes (Stage-1 handed
    # back a dish, not an ingredient). Informational — does not change matched/
    # confidence; surfaced so the compound-meal lab can flag degenerate decompositions.
    dish_as_ingredient_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'dish_name': self.dish_name,
            'normalised_dish_name': self.normalised_dish_name,
            'total_mass_g': round(self.total_mass_g, 2),
            'matched': self.matched,
            'ingredients': [i.to_dict() for i in self.ingredients],
            'resolved_mass_g': round(self.resolved_mass_g, 2),
            'unresolved_mass_g': round(self.unresolved_mass_g, 2),
            'unresolved_description': self.unresolved_description,
            'decomposition_confidence': round(self.decomposition_confidence, 3),
            'fallback_reason': self.fallback_reason,
            'cache_hit': self.cache_hit,
            'timing_ms': round(self.timing_ms, 1),
            'unresolved_ingredients_audit': self.unresolved_ingredients_audit,
            'dish_as_ingredient_count': self.dish_as_ingredient_count,
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
        "seasonings, etc.), put that residual in `unresolved_mass_g` AND "
        "describe what the residual is in `unresolved_description` (e.g. "
        "\"salt, pepper, and herbs\" or \"cooking water drained off pasta\" "
        "or \"olive oil residue in the pan\"). Do NOT leave the mass "
        "unbalanced. If unresolved_mass_g is 0, set unresolved_description "
        "to an empty string.\n\n"
        "INGREDIENT NAMES: prefer specific, generic English names that map "
        "well to CNF entries (e.g. \"chicken breast, cooked\" rather than "
        "\"poultry\"; \"olive oil\" rather than \"vegetable fat\"). Avoid "
        "brand names and ultra-specific cuts the CNF won't carry. State "
        "cooked vs raw where it matters.\n\n"
        "EXPLICIT COMPOUND-DISH RULE (2026-05-23 AI-MATCH-1.x): if the dish "
        "name uses a compound construction — \"X with Y\", \"X and Y\", "
        "\"X plus Y\", \"X on Y\", \"X over Y\" — BOTH X and Y MUST appear "
        "as explicit ingredients with non-zero mass. Don't bundle the "
        "secondary into unresolved_mass even if its proportion is small "
        "(e.g. \"oatmeal with berries\" needs both oatmeal AND berries; "
        "\"chicken on rice\" needs both chicken AND rice). The user named "
        "both because both matter to their nutrition picture.\n\n"
        "SPECIFICITY RULE (avoid unresolvable collectives): the downstream "
        "CNF database has entries for specific foods (\"blueberry, raw\", "
        "\"spinach, raw\", \"almond, dry roasted\") but NOT for collective "
        "categories (\"mixed berries\", \"leafy greens\", \"mixed nuts\"). "
        "When you'd reach for a collective, pick the MOST REPRESENTATIVE "
        "single instance instead: berries → blueberry; leafy greens → "
        "spinach; mixed nuts → almonds; mixed beans → kidney beans; root "
        "vegetables → carrot. This keeps Stage-2 resolution above the "
        "0.6 confidence floor.\n\n"
        "COOKING-FAT INCLUSION RULE: cooking fats that DEFINE the dish — "
        "butter on grilled cheese, oil in stir-fry, oil in pad thai, "
        "olive oil in pesto, butter in scrambled eggs, mayonnaise in tuna "
        "salad — MUST appear as EXPLICIT ingredients at their typical "
        "proportion (usually 3-10 % of total mass; up to 20 % for "
        "deep-fried items). These fats carry meaningful kcal and saturated "
        "fat and would distort the nutrition picture if dropped. "
        "Relegate to unresolved_mass ONLY for genuinely incidental cooking "
        "residue (e.g. \"thin film of pan-spray oil after most was "
        "absorbed\").\n\n"
        "VARIANT SELECTION (cautious-defaults rule, 2026-05-23 AI-MATCH-1.x): "
        "For ingredients with multiple CNF entries differing in salt content, "
        "fat content, or processing level (e.g. \"low-sodium\" vs unqualified, "
        "\"fat-free\" vs regular, \"unsalted\" vs salted, \"unenriched\" vs "
        "enriched), prefer the GENERIC unqualified entry that reflects what "
        "most people actually use — UNLESS the dish name explicitly calls "
        "for the variant (\"low-sodium chicken soup\" → low-sodium broth; "
        "\"unsalted peanut butter sandwich\" → unsalted peanut butter). "
        "Don't gratuitously pick the lowest-sodium or fat-free CNF entry "
        "when the user said \"chicken soup\" or \"peanut butter sandwich\".\n\n"
        "COOKED / AS-SERVED + WATER RULE (2026-05-28): decompose into "
        "ingredients in their AS-SERVED form and density, so the mass-weighted "
        "nutrients reproduce the dish as eaten — NOT raw/dry-ingredient density. "
        "For dishes that are cooked, hydrated, reconstituted, or diluted (soups, "
        "broths, stews, porridges/oatmeal, sauces, gravies, casseroles, "
        "rehydrated mixes, purées and baby foods, cooked rice/pasta/grains), (a) "
        "pick CNF entries in their COOKED/PREPARED form (\"rice, cooked\" not "
        "\"rice, dry\"; \"chicken, roasted\" not \"chicken, raw\"), and (b) "
        "explicitly represent the dish's WATER — either add a \"water\" "
        "ingredient for the absorbed/added water, or choose the prepared/diluted "
        "CNF entry. A 100 g serving of soup is mostly water (~20-40 kcal), a "
        "cooked grain has absorbed 2-3x its dry weight in water; if you list dry/"
        "raw ingredients at the cooked total mass you will overstate calories ~2x. "
        "Make the explicit water/cooked-form choice so the energy density is right.\n\n"
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
        "    \"unresolved_description\": \"<what the residual is, or empty>\",\n"
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

    def decompose(
        self,
        dish_name: str,
        total_mass_g: float,
        source: Optional[str] = None,
        force_decompose: bool = False,
    ) -> CNFDecomposedRecipe:
        """Decompose a free-text dish into CNF / WAFCT ingredients.

        WAFCT-EXTEND (2026-05-24): `source` ∈ {None, 'cnf', 'wafct'}
        restricts Stage-2 ingredient resolution to one food database.
        None (default) searches both. Source is included in the cache
        key so a CNF-only query and a both-query for the same dish
        cache independently.

        `force_decompose` (2026-05-28) bypasses catalog preference (fix 3) and
        the reconstruction-gated override (fix 2), forcing the raw LLM
        decomposition path. Used by the validation harnesses + golden smokes so
        they keep measuring decomposition quality rather than the catalog shortcut.
        """
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
        # WAFCT-EXTEND (2026-05-24): include source in the cache key so
        # cnf-only / wafct-only / both queries cache independently for the
        # same dish + mass.
        src_key = source if source in ('cnf', 'wafct') else 'both'
        key = (ndn, round(total_mass_g, 1), src_key, bool(force_decompose))
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

        # Skip catalog preference and just decompose when (a) a harness forces it, or
        # (b) the dish names multiple eaten items (a main plus a separate drink/side):
        # collapsing a compound meal onto one catalog food would silently drop the
        # second item (e.g. "... with a glass of orange juice" losing the juice).
        if force_decompose or _is_compound_meal(dish_name):
            return self._decompose_via_llm(dish_name, ndn, total_mass_g, source, t0, key)

        # --- Catalog preference (fix 2/3): match the dish name to a catalog food
        # WHILE the LLM decomposition runs concurrently, so the extra match call is
        # hidden under the decompose latency instead of adding to it. Both are OpenAI
        # HTTP calls (the GIL is released during the network wait), so they truly
        # overlap. The speculative decompose is launched with key=None so it never
        # writes the shared cache — decompose() caches the single chosen result.
        ex = ThreadPoolExecutor(max_workers=2, thread_name_prefix='cnf-decompose-stage0')
        cm_future = ex.submit(self._catalog_match, dish_name, source)
        decomp_future = ex.submit(
            self._decompose_via_llm, dish_name, ndn, total_mass_g, source, t0, None)
        cm = cm_future.result()

        # If the dish strongly matches a catalog food with measured nutrients, return
        # it directly (most accurate + cheapest); the speculative decompose finishes
        # in the background and is discarded.
        if (cm is not None and cm.matched and cm.food_id is not None
                and cm.confidence >= CATALOG_SHORTCIRCUIT_CONF
                and self._has_nutrients(int(cm.food_id))):
            ex.shutdown(wait=False)
            return self._cache_and_return(key, self._catalog_recipe(
                cm, dish_name, ndn, total_mass_g, reason='catalog_direct_match', t0=t0))

        decomp = decomp_future.result()
        ex.shutdown(wait=False)

        # --- Reconstruction-gated catalog override (fix 2): for a weaker catalog
        # match, replace a decomposition whose reconstructed nutrients diverge from
        # the catalog food's own measured profile (or that failed outright).
        #
        # GATED ON FOOD TYPE (2026-05-29): only override onto a catalog food that is
        # itself a MIXED dish. This keeps the correct "chicken soup -> measured
        # chicken-noodle soup" behaviour (a mixed dish) while preventing a dish from
        # being collapsed onto a single ingredient ("beef stew" -> "Beef, ground").
        # Unlabeled (None, e.g. WAFCT) -> do not override; keep the decomposition.
        if (cm is not None and cm.matched and cm.food_id is not None
                and cm.confidence >= CATALOG_OVERRIDE_CONF
                and _catalog_food_is_overridable(int(cm.food_id))
                and self._has_nutrients(int(cm.food_id))):
            recon = None
            if decomp.matched and decomp.ingredients:
                try:
                    from .decomposition_validation import nutrient_reconstruction
                    recon = nutrient_reconstruction(
                        int(cm.food_id),
                        [{'food_id': i.food_id, 'mass_g': i.mass_g} for i in decomp.ingredients],
                        total_mass_g=total_mass_g,
                    )
                except Exception:  # noqa: BLE001
                    recon = None
            if _should_override_with_catalog(recon, decomp.matched):
                if recon and recon.get('kcal_rel_error') is not None:
                    detail = f"kcal_err={recon['kcal_rel_error']}"
                elif not decomp.matched:
                    detail = f'decomp_failed:{decomp.fallback_reason}'
                else:
                    detail = 'recon_unavailable'
                return self._cache_and_return(key, self._catalog_recipe(
                    cm, dish_name, ndn, total_mass_g, reason=f'catalog_override:{detail}', t0=t0))

        return self._cache_and_return(key, decomp)

    def _decompose_via_llm(
        self,
        dish_name: str,
        ndn: str,
        total_mass_g: float,
        source: Optional[str],
        t0: float,
        key: Tuple,
    ) -> CNFDecomposedRecipe:
        """Stage 1 (LLM decompose) + Stage 2 (CNFMatcher resolve) + the 7 gates.

        Returns (and caches under `key`) a CNFDecomposedRecipe. Split out of
        `decompose()` so catalog preference + the reconstruction gate can wrap it.
        """
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
        unresolved_description = str(parsed.get('unresolved_description', '') or '').strip()[:240]
        confidence = float(parsed.get('decomposition_confidence', 0.0) or 0.0)

        # AI-MATCH-1.x (2026-05-23): Stage 2 runs each ingredient through
        # CNFMatcher.match() concurrently via a ThreadPoolExecutor. Each
        # match call is ~1 embedding + 1 chat-completion HTTP round-trip;
        # six sequential calls dominate the wall-clock (10-13 s for a
        # 6-ingredient recipe). Parallelising drops a 6-ingredient recipe
        # from ~12 s → ~4 s without changing the total LLM token spend.
        # Threads (not asyncio) because:
        #   - The OpenAI SDK is documented thread-safe
        #   - CNFMatcher._cache_lock + _emb_cache_lock already use threading.Lock
        #   - No async-view conversion needed in the Django request path
        # max_workers capped at 8 to stay well inside gpt-4.1-mini's tier-1
        # rate limit even when several users decompose simultaneously.
        resolved: List[CNFIngredient] = []
        dropped_audit: List[Dict[str, Any]] = []
        dropped_mass = 0.0
        if raw_ings:
            max_workers = min(8, len(raw_ings))
            # WAFCT-EXTEND (2026-05-24): forward source to each Stage-2
            # ingredient resolution so the matcher filters candidates to
            # the chosen food database (None = both).
            matcher_source = source if source in ('cnf', 'wafct') else None
            with ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix='cnf-decomp-stage2',
            ) as ex:
                stage2_results = list(ex.map(
                    lambda raw: self._resolve_one_ingredient(raw, source=matcher_source),
                    raw_ings,
                ))
            for ingredient, audit, mass in stage2_results:
                if ingredient is not None:
                    resolved.append(ingredient)
                elif audit is not None:
                    dropped_audit.append(audit)
                    dropped_mass += mass

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
                unresolved_description=unresolved_description,
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
                unresolved_description=unresolved_description,
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
                unresolved_description=unresolved_description,
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
                unresolved_description=unresolved_description,
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
                unresolved_description=unresolved_description,
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
            unresolved_description=unresolved_description,
            decomposition_confidence=confidence,
            unresolved_ingredients_audit=dropped_audit,
            raw_llm_response=raw_llm,
            timing_ms=(time.perf_counter() - t0) * 1000,
        )
        self._cache_put(key, result)
        return result

    # --- Catalog preference helpers --------------------------------------

    def _catalog_match(self, dish_name: str, source: Optional[str]):
        """Match the whole dish name to a CNF food (None on matcher failure)."""
        try:
            return self.cnf_matcher.match(dish_name, source=source)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _has_nutrients(food_id: int) -> bool:
        """True if the CNF food has a positive measured energy value."""
        try:
            from api.cnf_cache import get_api_cnf_pipeline
            n = get_api_cnf_pipeline().nutrients_for(int(food_id)) or {}
            return float(n.get('ENERGY (KILOCALORIES)', 0.0) or 0.0) > 0
        except Exception:  # noqa: BLE001
            return False

    def _catalog_recipe(self, cm, dish_name: str, ndn: str, total_mass_g: float,
                        reason: str, t0: float) -> CNFDecomposedRecipe:
        """Build a single-ingredient recipe = the matched catalog food at full mass."""
        ft = get_food_type(int(cm.food_id))
        ing = CNFIngredient(
            food_id=int(cm.food_id),
            food_description=cm.food_description or '',
            food_group=cm.food_group or '',
            mass_g=total_mass_g,
            rationale='Dish matched a CNF catalog food directly; using its measured profile.',
            resolution_confidence=float(cm.confidence),
            food_type=(ft['food_type'] if ft else None),
        )
        return CNFDecomposedRecipe(
            dish_name=dish_name, normalised_dish_name=ndn,
            total_mass_g=total_mass_g, matched=True,
            ingredients=[ing], resolved_mass_g=total_mass_g,
            unresolved_mass_g=0.0, unresolved_description='',
            decomposition_confidence=float(cm.confidence),
            fallback_reason=reason,
            timing_ms=(time.perf_counter() - t0) * 1000,
        )

    # --- Stage 2 (per-ingredient resolution, runs concurrently) ----------

    def _resolve_one_ingredient(
        self,
        raw_ing: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Tuple[Optional[CNFIngredient], Optional[Dict[str, Any]], float]:
        """Resolve one Stage-1-proposed ingredient name → CNF / WAFCT FoodID
        via the matcher. Returns a (ingredient, dropped_audit_entry,
        dropped_mass_g) triple — exactly one of `ingredient` /
        `dropped_audit_entry` is non-None (or both are None for skipped
        invalid inputs).

        WAFCT-EXTEND (2026-05-24): `source` ∈ {None, 'cnf', 'wafct'}
        forwards to `CNFMatcher.match(source=...)` so the matcher's
        candidate pool is filtered to one food database before LLM ranking.

        Called from ``decompose()``'s ``ThreadPoolExecutor.map(...)`` so all
        ingredients of a recipe resolve concurrently rather than sequentially.
        Thread-safe: the underlying ``CNFMatcher`` already uses
        ``threading.Lock`` on both its result + embedding LRU caches.
        """
        name = str(raw_ing.get('name', '')).strip()
        mass = raw_ing.get('mass_g')
        try:
            mass_f = float(mass)
        except (TypeError, ValueError):
            return None, None, 0.0
        if mass_f <= 0 or not name:
            return None, None, 0.0
        try:
            m = self.cnf_matcher.match(name, source=source)
        except Exception as exc:  # noqa: BLE001
            return None, {
                'name': name, 'mass_g': mass_f,
                'reason': f'matcher_exception:{exc!r}',
            }, mass_f
        if (not m.matched or m.food_id is None
                or m.confidence < self.ingredient_resolution_floor):
            return None, {
                'name': name, 'mass_g': mass_f,
                'matcher_food_id': m.food_id,
                'matcher_confidence': round(m.confidence, 3),
                'reason': (f'resolution_below_floor:{m.confidence:.2f}<'
                           f'{self.ingredient_resolution_floor:.2f}'
                           if m.matched else (m.fallback_reason or 'matcher_no_match')),
            }, mass_f
        ft = get_food_type(int(m.food_id))
        return CNFIngredient(
            food_id=int(m.food_id),
            food_description=m.food_description or '',
            food_group=m.food_group or '',
            mass_g=mass_f,
            rationale=str(raw_ing.get('rationale', '')).strip()[:240],
            resolution_confidence=m.confidence,
            food_type=(ft['food_type'] if ft else None),
        ), None, 0.0

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

    def _cache_put(self, key, value: CNFDecomposedRecipe) -> None:
        # key=None is used by the speculative concurrent decompose (whose result is
        # discarded on a catalog short-circuit); it must never touch the shared cache.
        if key is None:
            return
        # Informational stamp (single point every real-key return path flows through):
        # how many resolved DECOMPOSITION ingredients are themselves mixed dishes — i.e.
        # Stage-1 handed back a dish rather than an ingredient. Derived from per-ingredient
        # food_type labels; idempotent, no effect on matched/confidence. Skipped for catalog
        # recipes (a direct catalog match is one food == the whole dish, not a decomposition).
        if str(value.fallback_reason or '').startswith('catalog_'):
            value.dish_as_ingredient_count = 0
        else:
            value.dish_as_ingredient_count = sum(
                1 for i in value.ingredients if i.food_type == 'mixed')
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

    def _cache_and_return(self, key, value: CNFDecomposedRecipe) -> CNFDecomposedRecipe:
        self._cache_put(key, value)
        return value


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
