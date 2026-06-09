"""Per-nutrient food-contribution attribution.

For any nutrient and meal, returns the ranked list of contributing foods
plus cumulative share, so a researcher can read the Pareto frontier
directly. The standard nutrition-epidemiology follow-up question to
"sodium = 2,340 mg, %DV = 102 percent" is "which two foods drove it",
and this analyser answers it.

The default `nutrient_ids` covers the canonical research-relevant subset
(energy, protein, fat, saturated fat, total carb, total sugars, fiber,
sodium, potassium, calcium, iron, magnesium, zinc, vitamin A RAE,
vitamin C, vitamin D, vitamin B12, folate). The full 174-nutrient call
is available with `nutrient_ids='all'`.

The analyser uses the shared meal nutrient aggregator (Phase 1) under
the hood, so foods that are missing a nutrient entry are tracked
honestly in `n_foods_with_value` rather than imputed silently to zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


# Default canonical subset for ranked contribution. Reused across the
# deep-dive endpoint default and the population harness.
DEFAULT_CONTRIBUTION_NUTRIENT_IDS: Tuple[int, ...] = (
    208,   # ENERGY KCAL
    203,   # PROTEIN
    204,   # FAT TOTAL
    606,   # SATURATED FAT
    605,   # TRANS FAT
    205,   # CARBOHYDRATE
    269,   # SUGARS, TOTAL
    291,   # FIBRE
    307,   # SODIUM
    306,   # POTASSIUM
    301,   # CALCIUM
    303,   # IRON
    304,   # MAGNESIUM
    309,   # ZINC
    320,   # VITAMIN A RAE
    401,   # VITAMIN C
    328,   # VITAMIN D
    418,   # VITAMIN B12
    435,   # FOLATE DFE
)


@dataclass
class ContributorRow:
    food_id: int
    food_description: str
    mass_g: float
    nutrient_amount: float
    share_of_total: float       # this food's contribution / meal total, in [0, 1]
    cumulative_share: float     # running sum of share_of_total down the ranked list

    def to_dict(self) -> Dict[str, Any]:
        return {
            'food_id': self.food_id,
            'food_description': self.food_description,
            'mass_g': round(self.mass_g, 2),
            'nutrient_amount': round(self.nutrient_amount, 4),
            'share_of_total': round(self.share_of_total, 4),
            'cumulative_share': round(self.cumulative_share, 4),
        }


def top_contributors(
    foods: List[Dict],
    *,
    nutrient_ids: Union[List[int], Tuple[int, ...], str] = DEFAULT_CONTRIBUTION_NUTRIENT_IDS,
    top_k: int = 5,
) -> Dict[int, List[ContributorRow]]:
    """Return the ranked Pareto frontier per nutrient.

    Parameters
    ----------
    foods : List[{food_id, mass_g}]
        The meal's food list. The same dedup convention as the shared
        meal nutrient aggregator: multiple entries for the same food_id
        sum their masses.
    nutrient_ids : list of CNF NutrientID, or the literal string 'all'
        Subset of nutrients to rank. The 'all' literal returns every
        nutrient that appeared in the meal.
    top_k : int
        Number of top contributors to return per nutrient. Use a large
        value (e.g. 50) to recover the full ranked list per nutrient.

    Returns
    -------
    Dict[int, List[ContributorRow]]
        Per CNF NutrientID, the top-k contributing foods sorted by
        descending share_of_total, plus a cumulative_share column so a
        Pareto-frontier plot can be read directly without a second
        aggregation pass.
    """
    from api.services.meal_nutrient_aggregator import (
        aggregate_meal_nutrients,
    )

    # Same dedup as the aggregator so labels match by FoodID.
    mass_by_food: Dict[int, float] = {}
    for f in foods:
        try:
            fid = int(f.get('food_id'))
            m = float(f.get('mass_g', 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if m <= 0:
            continue
        mass_by_food[fid] = mass_by_food.get(fid, 0.0) + m

    if not mass_by_food:
        return {}

    deduped_foods = [{'food_id': fid, 'mass_g': m} for fid, m in mass_by_food.items()]

    # Meal-level totals (denominator for share_of_total).
    if isinstance(nutrient_ids, str) and nutrient_ids == 'all':
        meal_agg = aggregate_meal_nutrients(deduped_foods)
        target_nids = list(meal_agg.nutrient_totals.keys())
    else:
        target_nids = [int(n) for n in nutrient_ids]
        meal_agg = aggregate_meal_nutrients(deduped_foods, nutrient_set=target_nids)

    # Per-food per-nutrient amounts: walk each food independently through
    # the aggregator restricted to the target NutrientIDs. The aggregator
    # already scales by mass and tracks coverage; this is the simplest
    # honest way to get a per-food per-nutrient cell without rolling our
    # own CNF lookup.
    per_food_nutrients: Dict[int, Dict[int, float]] = {}
    for fid, m in mass_by_food.items():
        agg = aggregate_meal_nutrients(
            [{'food_id': fid, 'mass_g': m}],
            nutrient_set=target_nids,
        )
        per_food_nutrients[fid] = {
            nid: nv.amount for nid, nv in agg.nutrient_totals.items()
        }

    food_id_map = meal_agg.food_id_map

    out: Dict[int, List[ContributorRow]] = {}
    for nid in target_nids:
        meal_total_nv = meal_agg.nutrient_totals.get(nid)
        meal_total = meal_total_nv.amount if meal_total_nv is not None else 0.0
        rows: List[Tuple[int, float]] = []  # (food_id, contribution)
        for fid, by_nid in per_food_nutrients.items():
            contrib = by_nid.get(nid, 0.0)
            rows.append((fid, contrib))

        # Sort descending by contribution (largest absolute contributor first).
        rows.sort(key=lambda kv: -kv[1])

        running = 0.0
        contributor_rows: List[ContributorRow] = []
        for fid, contrib in rows[:top_k]:
            share = (contrib / meal_total) if meal_total > 0 else 0.0
            running += share
            contributor_rows.append(ContributorRow(
                food_id=fid,
                food_description=food_id_map.get(fid, ''),
                mass_g=mass_by_food.get(fid, 0.0),
                nutrient_amount=contrib,
                share_of_total=share,
                cumulative_share=min(1.0, running),
            ))
        out[nid] = contributor_rows
    return out


def top_contributors_to_dict(
    contributions: Dict[int, List[ContributorRow]],
) -> Dict[str, List[Dict[str, Any]]]:
    """JSON-ready shape for the deep-dive endpoint response."""
    return {
        str(nid): [r.to_dict() for r in rows]
        for nid, rows in sorted(contributions.items())
    }
