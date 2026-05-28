"""24-hour dietary recall orchestrator (AI-MATCH-2, 2026-05-24).

Composes the existing single-dish ``CNFRecipeDecomposer`` across a user's
six standard meal occasions (breakfast / AM snack / lunch / PM snack /
dinner / evening snack), then aggregates the per-meal CNF ingredient lists
into a single daily ingredient list — deduped by FoodID with masses summed
— ready to feed any of the 5 scoring endpoints (HEFI / HENI / HSR / FCS /
Environmental).

Why a daily recall is the unlock for HEFI / HENI:
  - HEFI-2019 is *explicitly designed for 24-h recall data*. Brassard
    2022b's whole evaluation paper uses CCHS-Nutrition 24-h recall data.
    The single-day caveat already shipped in `hefi_explanations.py:97-108`
    surfaces automatically when recall data routes to HEFI.
  - HENI's healthy-life-minutes impact sums marginal per-serving impacts
    across a real day's eating.
  - FCS's diet-level metric (i.FCS, O'Hearn 2022 Nat Comm 13:7066) is the
    energy-weighted mean FCS across daily intake.

Reuses primitives — no new ML, no new validation logic, no new caching
machinery:
  - ``CNFRecipeDecomposer`` per-meal (all 7 gates + ThreadPoolExecutor
    Stage-2 + LRU cache unchanged)
  - ``api.cnf_cache.get_api_cnf_pipeline`` for kcal lookup on the
    aggregated list
  - Same audience-aware contract as the rest of the platform; researcher
    mode surfaces per-meal audit, individual mode hides it

Caching is per-process LRU on the tuple of normalised meals (size 100;
recalls cost more to compute than dishes but are also less repeated).
"""
from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# --- Tunables -------------------------------------------------------------

OCCASIONS: Tuple[str, ...] = (
    'breakfast',
    'am_snack',
    'lunch',
    'pm_snack',
    'dinner',
    'evening_snack',
)
MAIN_OCCASIONS: Tuple[str, ...] = ('breakfast', 'lunch', 'dinner')

# Sanity bounds on aggregate kcal/day. Surfaced as warnings, never block.
# 800 kcal / day = below clinically reasonable for an adult (likely
# incomplete recall); 5000 kcal / day = above plausible (likely double-
# counted). Athletes / IF-OMAD eaters may legitimately fall outside; we
# surface this as amber warning, not as an error.
KCAL_LOW_BOUND = 800.0
KCAL_HIGH_BOUND = 5000.0

# Max parallel meal decompositions. The per-dish decomposer itself uses
# up to 8 workers internally for its Stage-2 ingredient resolution; we cap
# meal-level parallelism at 6 (= one per occasion) so we don't pile 48
# concurrent OpenAI HTTP calls onto the gpt-4.1-mini tier-1 quota when
# multiple users run recalls simultaneously.
MAX_PARALLEL_MEALS = 6

# Per-occasion mass-sanity defaults (UI hints only; backend never blocks).
# Used by the wizard frontend to set sensible defaults.
DEFAULT_MAIN_MASS_G = 200.0
DEFAULT_SNACK_MASS_G = 50.0

# Recall-level cache size — recalls are more expensive than dishes but
# also more variable, so keep this smaller than the dish cache.
DEFAULT_CACHE_SIZE = 100


# --- Input / output payloads ----------------------------------------------

@dataclass
class MealEntry:
    """One meal-occasion the user logged in their 24-h recall."""
    occasion: str
    dish_name: str
    total_mass_g: float
    # PKG-RECALL-1 (2026-05-26): packaged-food rows arrive pre-decomposed
    # from /packaged-food/decompose-ingredients/ (scan-product flow inlined
    # into the recall wizard). The orchestrator skips the LLM dish
    # decomposer for these and folds them straight into aggregation.
    entry_type: str = 'text'          # 'text' | 'packaged'
    pre_decomposed: Optional[Dict[str, Any]] = None


@dataclass
class CNFRecall24hResult:
    """Aggregated 24-h recall — ready to route to any scoring endpoint."""

    matched: bool
    # Per-meal trace: (occasion, decomposed_recipe). Preserves attribution
    # before the dedup-by-FoodID aggregation so researcher-mode UIs and
    # the audit harness can see which occasion contributed what.
    meals: List[Tuple[str, Any]] = field(default_factory=list)
    # Deduped daily ingredient list — one entry per CNF FoodID, masses
    # summed across all meals (e.g. coffee at breakfast + coffee at the
    # AM snack collapses to one row). This is the payload the scoring
    # endpoints consume.
    aggregated_daily_ingredients: List[Dict[str, Any]] = field(default_factory=list)
    total_resolved_mass_g: float = 0.0
    total_unresolved_mass_g: float = 0.0
    occasions_count: int = 0
    estimated_daily_kcal: float = 0.0
    aggregate_warnings: List[str] = field(default_factory=list)
    fallback_reason: Optional[str] = None
    timing_ms: float = 0.0
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        # Per-meal payloads carry their full CNFDecomposedRecipe.to_dict()
        # (already audience-stripped downstream by the view if individual
        # mode).
        return {
            'matched': self.matched,
            'meals': [
                {'occasion': occ, 'decomposition': dec.to_dict()}
                for occ, dec in self.meals
            ],
            'aggregated_daily_ingredients': self.aggregated_daily_ingredients,
            'total_resolved_mass_g': round(self.total_resolved_mass_g, 2),
            'total_unresolved_mass_g': round(self.total_unresolved_mass_g, 2),
            'occasions_count': self.occasions_count,
            'estimated_daily_kcal': round(self.estimated_daily_kcal, 1),
            'aggregate_warnings': self.aggregate_warnings,
            'fallback_reason': self.fallback_reason,
            'timing_ms': round(self.timing_ms, 1),
            'cache_hit': self.cache_hit,
        }


# --- Helpers --------------------------------------------------------------

def _normalise_dish_name(name: str) -> str:
    return ' '.join((name or '').strip().lower().split())


def _packaged_ingredient_key(pre: Optional[Dict[str, Any]]) -> Tuple[Tuple[int, float], ...]:
    """Stable cache fingerprint for a pre-decomposed packaged meal."""
    if not pre:
        return ()
    rows: List[Tuple[int, float]] = []
    for ing in pre.get('ingredients') or []:
        if not isinstance(ing, dict):
            continue
        try:
            rows.append((int(ing['food_id']), round(float(ing['mass_g']), 1)))
        except (KeyError, TypeError, ValueError):
            continue
    rows.sort()
    return tuple(rows)


def _meals_cache_key(meals: List[MealEntry]) -> Tuple[Tuple[str, str, float, str, Tuple], ...]:
    """Cache key — tuple of normalised (occasion, dish_name, rounded_mass,
    entry_type, packaged-ingredient fingerprint) sorted by occasion order."""
    occasion_rank = {occ: idx for idx, occ in enumerate(OCCASIONS)}
    rows = [
        (
            m.occasion,
            _normalise_dish_name(m.dish_name),
            round(m.total_mass_g, 1),
            m.entry_type or 'text',
            _packaged_ingredient_key(m.pre_decomposed),
        )
        for m in meals
    ]
    rows.sort(key=lambda r: (occasion_rank.get(r[0], 999), r[1]))
    return tuple(rows)


# --- Orchestrator class ---------------------------------------------------

class CNFRecall24h:
    """Walk the user occasion-by-occasion, decompose each meal, aggregate."""

    def __init__(self, decomposer, *, cache_size: int = DEFAULT_CACHE_SIZE):
        self.decomposer = decomposer
        self._cache_size = cache_size
        self._cache: 'dict[Tuple, CNFRecall24hResult]' = {}
        self._cache_order: List[Tuple] = []
        self._cache_lock = threading.Lock()

    # --- public ----------------------------------------------------------

    def recall(
        self,
        meals: List[MealEntry],
        user_type: str = 'individual',
        parallel_meals: bool = True,
        source: Optional[str] = None,
        force_decompose: bool = False,
    ) -> CNFRecall24hResult:
        """Decompose each meal, aggregate into a single daily ingredient list.

        ``parallel_meals=True`` runs every meal's ``decompose()`` call
        concurrently via a ThreadPoolExecutor (capped at MAX_PARALLEL_MEALS
        workers). Mirrors the same threading pattern the dish decomposer
        already uses internally for its Stage-2 ingredient resolution.

        WAFCT-EXTEND (2026-05-24): `source` ∈ {None, 'cnf', 'wafct'} is
        forwarded into every per-meal `decompose()` call, so every
        ingredient in the daily aggregate comes from the chosen food
        database. None (default) searches both. Cache key includes source.
        """
        t0 = time.perf_counter()

        # Input validation: at least one meal, every meal has a non-empty
        # dish_name and a positive mass.
        if not meals:
            return CNFRecall24hResult(
                matched=False,
                fallback_reason='no_meals_provided',
                timing_ms=(time.perf_counter() - t0) * 1000,
            )
        cleaned: List[MealEntry] = []
        for m in meals:
            occ = (m.occasion or '').strip().lower()
            if occ not in OCCASIONS:
                return CNFRecall24hResult(
                    matched=False,
                    fallback_reason=f'invalid_occasion:{m.occasion!r}',
                    timing_ms=(time.perf_counter() - t0) * 1000,
                )
            dn = (m.dish_name or '').strip()
            if not dn:
                return CNFRecall24hResult(
                    matched=False,
                    fallback_reason='empty_dish_name',
                    timing_ms=(time.perf_counter() - t0) * 1000,
                )
            try:
                mass = float(m.total_mass_g)
            except (TypeError, ValueError):
                return CNFRecall24hResult(
                    matched=False,
                    fallback_reason=f'non_numeric_mass:{m.total_mass_g!r}',
                    timing_ms=(time.perf_counter() - t0) * 1000,
                )
            if mass <= 0 or mass > 5000.0:
                return CNFRecall24hResult(
                    matched=False,
                    fallback_reason=f'mass_out_of_bounds:{mass:.1f}',
                    timing_ms=(time.perf_counter() - t0) * 1000,
                )
            entry_type = getattr(m, 'entry_type', None) or 'text'
            pre_decomposed = getattr(m, 'pre_decomposed', None)
            if entry_type in ('packaged', 'direct') and not pre_decomposed:
                return CNFRecall24hResult(
                    matched=False,
                    fallback_reason=f'{entry_type}_missing_pre_decomposed:{occ}',
                    timing_ms=(time.perf_counter() - t0) * 1000,
                )
            cleaned.append(MealEntry(
                occasion=occ,
                dish_name=dn,
                total_mass_g=mass,
                entry_type=entry_type,
                pre_decomposed=pre_decomposed,
            ))

        # Cache lookup — include source in the key so cnf-only / wafct-only
        # / both recalls cache independently.
        src_norm = source if source in ('cnf', 'wafct') else 'both'
        key = (_meals_cache_key(cleaned), src_norm, bool(force_decompose))
        cached = self._cache_get(key)
        if cached is not None:
            return CNFRecall24hResult(
                **{**cached.__dict__,
                   'cache_hit': True,
                   'timing_ms': (time.perf_counter() - t0) * 1000},
            )

        # --- Decompose each meal -----------------------------------------
        # Per-meal flow:
        #   1. Try `decomposer.decompose(name, mass)` for compound dishes.
        #   2. If that fails specifically because the dish is a single food
        #      (`too_few_ingredients` gate, fires for "banana", "almonds",
        #      "apple", etc.), retry as a single-FoodID match via the
        #      matcher and synthesise a 1-ingredient CNFDecomposedRecipe.
        #      The recall surface SHOULD handle "user logged a banana"
        #      gracefully; the per-dish decomposer was deliberately built
        #      to reject single-ingredient inputs (it's the matcher's job
        #      for those), so the orchestrator bridges the two.
        # WAFCT-EXTEND (2026-05-24): forward source to every per-meal
        # decompose so every aggregated ingredient comes from the chosen
        # food database. None = both sources.
        meal_source = source if source in ('cnf', 'wafct') else None
        meal_results: List[Tuple[str, Any]] = []
        text_meals = [m for m in cleaned if (m.entry_type or 'text') not in ('packaged', 'direct')]
        precomposed_meals = [m for m in cleaned if (m.entry_type or 'text') in ('packaged', 'direct')]
        if parallel_meals and len(text_meals) > 1:
            max_workers = min(MAX_PARALLEL_MEALS, len(text_meals))
            with ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix='cnf-recall-24h',
            ) as ex:
                text_decompositions = list(ex.map(
                    lambda m: self._decompose_meal(m, source=meal_source,
                                                   force_decompose=force_decompose),
                    text_meals,
                ))
            text_results = list(zip([m.occasion for m in text_meals], text_decompositions))
        else:
            text_results = [
                (m.occasion, self._decompose_meal(m, source=meal_source,
                                                  force_decompose=force_decompose))
                for m in text_meals
            ]
        precomposed_results = [
            (m.occasion, self._packaged_to_decomposition(m))
            for m in precomposed_meals
        ]
        # Preserve user occasion order for downstream attribution.
        by_occ = {occ: dec for occ, dec in text_results + precomposed_results}
        meal_results = [(m.occasion, by_occ[m.occasion]) for m in cleaned]

        # --- Aggregate ----------------------------------------------------
        agg = self._aggregate(meal_results)
        agg.timing_ms = (time.perf_counter() - t0) * 1000
        self._cache_put(key, agg)
        return agg

    # --- per-meal decompose + single-food fallback -----------------------

    def _decompose_meal(self, meal: MealEntry, source: Optional[str] = None,
                        force_decompose: bool = False):
        """Decompose one meal, falling back to a single-FoodID match if the
        per-dish decomposer rejects the input as too few ingredients (the
        common case for snack entries like "banana", "almonds", "apple").

        WAFCT-EXTEND (2026-05-24): `source` forwards to both the compound
        decompose path AND the snack-fallback matcher call. `force_decompose`
        (2026-05-28) forwards to the per-dish decomposer to bypass catalog
        preference (used by the recall golden smoke).
        """
        dec = self.decomposer.decompose(meal.dish_name, meal.total_mass_g, source=source,
                                        force_decompose=force_decompose)
        # If matched OR failed for any reason OTHER than the single-food gate,
        # return as-is — the orchestrator's aggregation handles partial
        # decompositions cleanly.
        fr = dec.fallback_reason or ''
        if dec.matched or not fr.startswith('too_few_ingredients'):
            return dec
        # Single-food fallback: route the dish_name through the matcher
        # directly (filtered to the same source). If it matches with adequate
        # confidence, synthesise a 1-ingredient CNFDecomposedRecipe so the
        # aggregation step credits the snack into the daily list.
        try:
            m = self.decomposer.cnf_matcher.match(meal.dish_name, source=source)
        except Exception as exc:  # noqa: BLE001
            logger.warning('CNFRecall24h snack-fallback matcher failed for %r: %s',
                           meal.dish_name, exc)
            return dec
        if not m.matched or m.food_id is None or m.confidence < self.decomposer.ingredient_resolution_floor:
            return dec
        # Build a 1-ingredient decomposition that mirrors what the per-dish
        # decomposer would have produced if min_ingredients had been 1.
        from .cnf_recipe_decomposer import CNFDecomposedRecipe, CNFIngredient
        return CNFDecomposedRecipe(
            dish_name=meal.dish_name,
            normalised_dish_name=_normalise_dish_name(meal.dish_name),
            total_mass_g=meal.total_mass_g,
            matched=True,
            ingredients=[CNFIngredient(
                food_id=int(m.food_id),
                food_description=m.food_description or '',
                food_group=m.food_group or '',
                mass_g=meal.total_mass_g,
                rationale='single-food snack fallback (CNFMatcher direct match)',
                resolution_confidence=float(m.confidence),
            )],
            resolved_mass_g=meal.total_mass_g,
            unresolved_mass_g=0.0,
            unresolved_description='',
            decomposition_confidence=float(m.confidence),
            fallback_reason='single_food_fallback',
            unresolved_ingredients_audit=[],
            raw_llm_response=None,
            timing_ms=0.0,
        )

    def _packaged_to_decomposition(self, meal: MealEntry):
        """Convert a pre-decomposed packaged-food payload into a
        CNFDecomposedRecipe so aggregation treats it like any other meal."""
        from .cnf_recipe_decomposer import CNFDecomposedRecipe, CNFIngredient

        pre = meal.pre_decomposed or {}
        raw_ings = pre.get('ingredients') or []
        if not raw_ings:
            return CNFDecomposedRecipe(
                dish_name=meal.dish_name,
                normalised_dish_name=_normalise_dish_name(meal.dish_name),
                total_mass_g=meal.total_mass_g,
                matched=False,
                ingredients=[],
                resolved_mass_g=0.0,
                unresolved_mass_g=meal.total_mass_g,
                unresolved_description='',
                decomposition_confidence=0.0,
                fallback_reason='packaged_no_ingredients',
                unresolved_ingredients_audit=[],
                raw_llm_response=None,
                timing_ms=0.0,
            )

        dec_conf = float(pre.get('decomposition_confidence', 0.5) or 0.5)
        entry_type = getattr(meal, 'entry_type', None) or 'text'
        if entry_type == 'direct':
            ing_rationale = 'user-selected CNF food(s)'
            fallback = 'direct_food_entry'
        else:
            ing_rationale = 'packaged food label decomposition (inferred)'
            fallback = 'packaged_food_inferred'
        ingredients: List[CNFIngredient] = []
        for ing in raw_ings:
            if not isinstance(ing, dict):
                continue
            try:
                ingredients.append(CNFIngredient(
                    food_id=int(ing['food_id']),
                    food_description=str(ing.get('food_description') or ''),
                    food_group=str(ing.get('food_group') or ''),
                    mass_g=float(ing['mass_g']),
                    rationale=ing_rationale,
                    resolution_confidence=float(
                        ing.get('confidence', dec_conf) or dec_conf,
                    ),
                ))
            except (KeyError, TypeError, ValueError):
                continue

        if not ingredients:
            return CNFDecomposedRecipe(
                dish_name=meal.dish_name,
                normalised_dish_name=_normalise_dish_name(meal.dish_name),
                total_mass_g=meal.total_mass_g,
                matched=False,
                ingredients=[],
                resolved_mass_g=0.0,
                unresolved_mass_g=meal.total_mass_g,
                unresolved_description='',
                decomposition_confidence=0.0,
                fallback_reason='packaged_invalid_ingredients',
                unresolved_ingredients_audit=[],
                raw_llm_response=None,
                timing_ms=0.0,
            )

        resolved = sum(float(i.mass_g) for i in ingredients)
        return CNFDecomposedRecipe(
            dish_name=meal.dish_name,
            normalised_dish_name=_normalise_dish_name(meal.dish_name),
            total_mass_g=meal.total_mass_g,
            matched=True,
            ingredients=ingredients,
            resolved_mass_g=resolved,
            unresolved_mass_g=max(0.0, meal.total_mass_g - resolved),
            unresolved_description='',
            decomposition_confidence=dec_conf,
            fallback_reason=fallback,
            unresolved_ingredients_audit=[],
            raw_llm_response=None,
            timing_ms=0.0,
        )

    # --- aggregation -----------------------------------------------------

    def _aggregate(
        self,
        meal_results: List[Tuple[str, Any]],
    ) -> CNFRecall24hResult:
        """Apply the 5 aggregation rules from the AI-MATCH-2 plan."""

        # 1. Concatenate every meal's ingredients.
        # 2. Dedupe by food_id — sum mass_g.
        by_food: Dict[int, Dict[str, Any]] = {}
        total_resolved = 0.0
        total_unresolved = 0.0
        partial_meals = 0
        failed_meals = 0
        occasions_seen: List[str] = []

        for occasion, dec in meal_results:
            occasions_seen.append(occasion)
            # The decomposer returns a CNFDecomposedRecipe; failed meals
            # have matched=False AND no ingredients we want to credit. A
            # partial-resolution meal still has matched=True so its
            # ingredients still aggregate.
            if not dec.matched:
                # Decomposition truly failed — log, skip ingredients, do
                # NOT credit unresolved (we have no idea what it was).
                failed_meals += 1
                continue
            if dec.fallback_reason and 'partial_resolution' in dec.fallback_reason:
                partial_meals += 1
            for ing in dec.ingredients:
                fid = int(ing.food_id)
                existing = by_food.get(fid)
                if existing is None:
                    by_food[fid] = {
                        'food_id': fid,
                        'food_description': ing.food_description,
                        'food_group': ing.food_group,
                        'mass_g': float(ing.mass_g),
                        # Per-occasion attribution — preserved so the
                        # researcher-mode UI can show "coffee: 250g
                        # (breakfast 150g + AM snack 100g)".
                        'occasions': {occasion: float(ing.mass_g)},
                    }
                else:
                    existing['mass_g'] += float(ing.mass_g)
                    existing['occasions'][occasion] = (
                        existing['occasions'].get(occasion, 0.0) + float(ing.mass_g)
                    )
                total_resolved += float(ing.mass_g)
            # 3. Sum unresolved_mass_g across meals.
            total_unresolved += float(dec.unresolved_mass_g)

        # Round mass to 2 dp and pack the aggregated list. Sorted by
        # descending mass — stable across re-runs and matches what a user
        # would scan first.
        aggregated = sorted(
            by_food.values(), key=lambda r: r['mass_g'], reverse=True,
        )
        for row in aggregated:
            row['mass_g'] = round(row['mass_g'], 2)
            row['occasions'] = {
                occ: round(m, 2) for occ, m in row['occasions'].items()
            }

        # 5. Compute estimated_daily_kcal from the CNF nutrient table.
        # `nutrients_for()` returns kcal-per-100g, so scale by mass/100.
        estimated_kcal = 0.0
        try:
            from api.cnf_cache import get_api_cnf_pipeline
            pipeline = get_api_cnf_pipeline()
            for row in aggregated:
                nutrients = pipeline.nutrients_for(row['food_id'])
                # CNF stores 'ENERGY (KILOCALORIES)' per 100g of food.
                kcal_per_100g = float(nutrients.get('ENERGY (KILOCALORIES)', 0.0) or 0.0)
                estimated_kcal += kcal_per_100g * (row['mass_g'] / 100.0)
        except Exception as exc:  # noqa: BLE001
            # Kcal estimation is informational — never block the response
            # if the CNF pipeline misbehaves.
            logger.warning('CNFRecall24h kcal estimation failed: %s', exc)

        # 4. Aggregate warnings.
        warnings: List[str] = []
        # 4a — missing major occasions
        for required in MAIN_OCCASIONS:
            if required not in occasions_seen:
                warnings.append(f'no_{required}_logged')
        # 4b — kcal sanity bounds
        if estimated_kcal > 0 and estimated_kcal < KCAL_LOW_BOUND:
            warnings.append(
                f'daily_kcal_below_{int(KCAL_LOW_BOUND)}:'
                f'{estimated_kcal:.0f}_kcal_recall_may_be_incomplete'
            )
        if estimated_kcal > KCAL_HIGH_BOUND:
            warnings.append(
                f'daily_kcal_above_{int(KCAL_HIGH_BOUND)}:'
                f'{estimated_kcal:.0f}_kcal_may_be_double_counted'
            )
        # 4c — single occasion days
        if len(occasions_seen) <= 1:
            warnings.append('single_occasion_day_aggregation_unreliable')
        # 4d — partial / failed meals
        if partial_meals:
            warnings.append(f'{partial_meals}_meal(s)_resolved_only_partially')
        if failed_meals:
            warnings.append(f'{failed_meals}_meal(s)_failed_to_decompose')
        # 4e — packaged-food occasions (inferred composition caveat)
        packaged_occasions = [
            occ for occ, dec in meal_results
            if (dec.fallback_reason or '') == 'packaged_food_inferred'
        ]
        if packaged_occasions:
            warnings.append(
                f'packaged_food_inferred_at_{len(packaged_occasions)}_occasion(s):'
                + ','.join(packaged_occasions),
            )

        # `matched` = all meals decomposed (none failed) AND kcal in the
        # plausible bound. Partial meals are still a "matched" recall.
        all_meals_matched = (failed_meals == 0)
        kcal_in_bounds = (
            estimated_kcal == 0.0  # informational unavailable — don't penalise
            or (KCAL_LOW_BOUND <= estimated_kcal <= KCAL_HIGH_BOUND)
        )
        matched = all_meals_matched and kcal_in_bounds

        fallback_reason: Optional[str] = None
        if not all_meals_matched:
            fallback_reason = f'partial_meals_failed:{failed_meals}_of_{len(meal_results)}'
        elif not kcal_in_bounds:
            fallback_reason = (
                f'kcal_outside_sanity_bound:{estimated_kcal:.0f}'
                f'_not_in_[{int(KCAL_LOW_BOUND)},{int(KCAL_HIGH_BOUND)}]'
            )

        return CNFRecall24hResult(
            matched=matched,
            meals=meal_results,
            aggregated_daily_ingredients=aggregated,
            total_resolved_mass_g=total_resolved,
            total_unresolved_mass_g=total_unresolved,
            occasions_count=len(occasions_seen),
            estimated_daily_kcal=estimated_kcal,
            aggregate_warnings=warnings,
            fallback_reason=fallback_reason,
        )

    # --- LRU cache --------------------------------------------------------

    def _cache_get(self, key: Tuple) -> Optional[CNFRecall24hResult]:
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

    def _cache_put(self, key: Tuple, value: CNFRecall24hResult) -> None:
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


# --- Factory --------------------------------------------------------------

@lru_cache(maxsize=1)
def get_default_recall_24h() -> CNFRecall24h:
    """Process-wide singleton wired to the same decomposer (and via that,
    the same matcher + chat client + caches) as everything else."""
    from .cnf_recipe_decomposer import get_default_decomposer
    return CNFRecall24h(decomposer=get_default_decomposer())
