"""Nutrient-discovery and matcher-alternative candidates for SUBST-1 Phase 2.

Complements curated rules (Phase 1) with:
  - CNFMatcher embedding alternatives (no extra LLM calls when cached)
  - CNF pipeline nutrient-range search filtered by purpose + source
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

from api.cnf_cache import get_dish_cnf_pipeline
from api.services.cnf_matcher import get_default_matcher

logger = logging.getLogger(__name__)


# Per-purpose nutrient search returns the same food set regardless of which
# ingredient is being substituted, so cache the raw pipeline result. The
# per-ingredient filtering (exclude_ids, prefer_group_id) is applied to the
# cached list. ~6 entries (one per purpose) × ~20 foods each — tiny.
@lru_cache(maxsize=16)
def _cached_foods_by_nutrient(
    nutrient_id: int,
    min_value: Optional[float],
    max_value: Optional[float],
    limit: int,
) -> Tuple[Tuple[int, str, str, Optional[int]], ...]:
    pipeline = get_dish_cnf_pipeline()
    foods = pipeline.search_foods_by_nutrient(
        nutrient_id,
        min_value=min_value,
        max_value=max_value,
        limit=limit,
    )
    # Tuple-of-tuples so the cached value is immutable + hashable-friendly.
    return tuple(
        (
            int(f['FoodID']),
            str(f.get('FoodDescription', f'Food ID {f["FoodID"]}')),
            str(f.get('FoodGroupName', '') or ''),
            int(f['FoodGroupID']) if f.get('FoodGroupID') is not None else None,
        )
        for f in foods
    )

# Matcher alternatives below this cosine are too weak to show as culinary substitutes.
MIN_MATCHER_COSINE = 0.65

# CNF NutrientID → discovery query per purpose (per 100 g edible).
PURPOSE_NUTRIENT_QUERIES: Dict[str, Dict[str, Any]] = {
    'lower_sodium': {'nutrient_id': 307, 'max_value': 100.0, 'limit': 20},
    'higher_fibre': {'nutrient_id': 291, 'min_value': 4.0, 'limit': 20},
    'higher_protein': {'nutrient_id': 203, 'min_value': 12.0, 'limit': 20},
    'lower_sat_fat': {'nutrient_id': 606, 'max_value': 3.0, 'limit': 20},
    'diabetes_friendly': {'nutrient_id': 269, 'max_value': 5.0, 'limit': 20},
    'general_health': {'nutrient_id': 291, 'min_value': 3.0, 'limit': 15},
    'sustainability': {'nutrient_id': 291, 'min_value': 2.0, 'limit': 15},
}

# Rough group-level carbon proxy (kg CO2-eq / 100 g, ordinal) for sustainability
# ranking when full LCA is too heavy for inline analyze. Phase 3 replaces this.
GROUP_SUSTAINABILITY_PROXY: Dict[str, float] = {
    'Beef Products': 10.0,
    'Lamb, Veal and Game': 9.5,
    'Pork Products': 6.0,
    'Poultry Products': 3.5,
    'Finfish and Shellfish Products': 4.0,
    'Dairy and Egg Products': 4.5,
    'Legumes and Legume Products': 1.0,
    'Vegetables and Vegetable Products': 0.5,
    'Fruits and fruit juices': 0.6,
    'Cereals, Grains and Pasta': 1.2,
    'Baked Products': 1.5,
    'Beverages': 0.3,
    'Nuts and Seeds': 2.0,
}


@dataclass(frozen=True)
class DiscoveryCandidate:
    food_id: int
    food_description: str
    food_group: str
    food_group_id: Optional[int]
    source: str
    origin: str  # 'nutrient_discovery' | 'matcher_alternative'
    label: str
    rationale: str


def _food_source(food_id: int) -> str:
    pipeline = get_dish_cnf_pipeline()
    df = pipeline.data_loader.food_name_df
    row = df[df['FoodID'] == int(food_id)]
    if row.empty:
        return 'cnf'
    src = row.iloc[0].get('source', 'cnf')
    return str(src) if src else 'cnf'


def _passes_source_filter(food_id: int, source_filter: Optional[str]) -> bool:
    if not source_filter or source_filter == 'both':
        return True
    return _food_source(food_id) == source_filter


def _nutrient_discovery_candidates(
    purpose: str,
    *,
    prefer_group_id: Optional[int],
    exclude_ids: Set[int],
    source_filter: Optional[str],
    limit: int = 5,
) -> List[DiscoveryCandidate]:
    query = PURPOSE_NUTRIENT_QUERIES.get(purpose) or PURPOSE_NUTRIENT_QUERIES['general_health']
    foods = _cached_foods_by_nutrient(
        int(query['nutrient_id']),
        query.get('min_value'),
        query.get('max_value'),
        int(query.get('limit', 20)),
    )

    same_group: List[DiscoveryCandidate] = []
    other_group: List[DiscoveryCandidate] = []

    for fid, fdesc, fgroup, gid in foods:
        if fid in exclude_ids:
            continue
        if not _passes_source_filter(fid, source_filter):
            continue
        cand = DiscoveryCandidate(
            food_id=fid,
            food_description=fdesc,
            food_group=fgroup,
            food_group_id=gid,
            source=_food_source(fid),
            origin='nutrient_discovery',
            label=f"Nutrient-targeted: {fdesc[:60]}",
            rationale=(
                f"Discovered via CNF nutrient search for “{purpose.replace('_', ' ')}” "
                f"(nutrient_id {query['nutrient_id']})."
            ),
        )
        if prefer_group_id is not None and gid is not None and gid == prefer_group_id:
            same_group.append(cand)
        else:
            other_group.append(cand)

    # Phase 2: same food group only when the ingredient has a group id.
    if prefer_group_id is not None:
        return same_group[:limit]
    return (same_group + other_group)[:limit]


def _matcher_alternative_candidates(
    food_description: str,
    *,
    exclude_ids: Set[int],
    source_filter: Optional[str],
    limit: int = 3,
) -> List[DiscoveryCandidate]:
    try:
        matcher = get_default_matcher()
        # Discovery only consumes result.alternatives (pure embedding cosine).
        # Skip the LLM rank step — it affects only result.food_id, which we
        # discard here. Halves substitution-analyze latency under load.
        result = matcher.match(
            food_description,
            top_k=10,
            source=source_filter,
            retrieval_only=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning('matcher alternatives failed: %s', exc)
        return []

    out: List[DiscoveryCandidate] = []
    seen: Set[int] = set(exclude_ids)

    if result.matched and result.food_id and result.food_id not in seen:
        seen.add(result.food_id)

    for alt in result.alternatives:
        if alt.food_id in seen:
            continue
        if alt.similarity < MIN_MATCHER_COSINE:
            continue
        if not _passes_source_filter(alt.food_id, source_filter):
            continue
        seen.add(alt.food_id)
        meta = get_dish_cnf_pipeline().get_food_details(alt.food_id) or {}
        out.append(DiscoveryCandidate(
            food_id=alt.food_id,
            food_description=alt.food_description or meta.get('FoodDescription', ''),
            food_group=alt.food_group or meta.get('FoodGroupName', ''),
            food_group_id=meta.get('FoodGroupID'),
            source=_food_source(alt.food_id),
            origin='matcher_alternative',
            label=f"Similar food: {alt.food_description[:60]}",
            rationale=(
                'CNFMatcher embedding alternative — nutritionally related option '
                f'(cosine similarity {alt.similarity:.2f}).'
            ),
        ))
        if len(out) >= limit:
            break
    return out


def discover_candidates_for_ingredient(
    *,
    food_id: int,
    food_description: str,
    food_group_id: Optional[int],
    purpose: str,
    exclude_ids: Set[int],
    source_filter: Optional[str],
    max_per_ingredient: int = 6,
) -> List[DiscoveryCandidate]:
    """Return discovery + matcher candidates for one composition slot."""
    blocked = set(exclude_ids) | {food_id}
    # Matcher alternatives first — more likely to be culinary substitutes.
    matcher = _matcher_alternative_candidates(
        food_description,
        exclude_ids=blocked,
        source_filter=source_filter,
        limit=max(2, max_per_ingredient // 2),
    )
    nutrient = _nutrient_discovery_candidates(
        purpose,
        prefer_group_id=food_group_id,
        exclude_ids=blocked | {c.food_id for c in matcher},
        source_filter=source_filter,
        limit=max(3, max_per_ingredient // 2),
    )

    merged: List[DiscoveryCandidate] = []
    seen: Set[int] = set()
    for cand in matcher + nutrient:
        if cand.food_id in seen:
            continue
        seen.add(cand.food_id)
        merged.append(cand)
        if len(merged) >= max_per_ingredient:
            break
    return merged


def sustainability_proxy_score(composition: List[Dict[str, Any]]) -> float:
    """Lower is better — group-level carbon proxy for ranking."""
    total = 0.0
    for row in composition:
        group = row.get('food_group') or ''
        proxy = GROUP_SUSTAINABILITY_PROXY.get(group, 2.5)
        total += proxy * (row['mass_g'] / 100.0)
    return round(total, 3)
