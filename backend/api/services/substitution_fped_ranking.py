"""FPED gap-aware ranking bonus for substitution suggestions.

When a recall day is short on fruit, vegetables, whole grains, etc., swaps that
close those food-pattern gaps rank higher than cosine-similar matcher noise.
"""
from __future__ import annotations

from typing import Any, Dict, List

from api.services.fped_aggregator import aggregate_fped

# Rank bonus weights — higher for under-consumed produce groups.
_GAP_WEIGHTS: Dict[str, float] = {
    'fruit_total_cup': 8.0,
    'veg_total_cup': 8.0,
    'veg_dark_green_cup': 6.0,
    'grain_whole_oz': 5.0,
    'dairy_total_cup': 4.0,
    'protein_legumes_oz': 5.0,
    'grain_refined_oz': 4.0,
    'added_sugars_tsp': 6.0,
}

_MIN_CLOSURE = 0.02


def fped_gap_fill_bonus(
    baseline_foods: List[Dict],
    modified_foods: List[Dict],
) -> Dict[str, Any]:
    """Return a rank bonus for swaps that close baseline FPED guideline gaps."""
    base = aggregate_fped(baseline_foods)
    mod = aggregate_fped(modified_foods)

    bonus = 0.0
    fills: List[Dict[str, Any]] = []
    gap_by_comp = {g.component: g for g in base.gaps}

    for comp, weight in _GAP_WEIGHTS.items():
        gap = gap_by_comp.get(comp)
        if gap is None:
            continue

        b_val = base.component_totals.get(comp, 0.0)
        m_val = mod.component_totals.get(comp, 0.0)
        delta = m_val - b_val

        if gap.direction == 'aim_at_least':
            if gap.myplate_status != 'short':
                continue
            if delta < _MIN_CLOSURE:
                continue
            remaining = max(gap.myplate_target - b_val, _MIN_CLOSURE)
            fill_frac = min(delta / remaining, 1.0)
            comp_bonus = fill_frac * weight
            bonus += comp_bonus
            fills.append({
                'component': comp,
                'label': gap.label,
                'unit': gap.unit,
                'delta': round(delta, 3),
                'fill_fraction': round(fill_frac, 3),
                'bonus': round(comp_bonus, 2),
            })
        elif gap.direction == 'keep_at_most':
            if gap.myplate_status != 'over':
                continue
            if delta > -_MIN_CLOSURE:
                continue
            excess = max(b_val - gap.myplate_target, _MIN_CLOSURE)
            reduce_frac = min(-delta / excess, 1.0)
            comp_bonus = reduce_frac * weight
            bonus += comp_bonus
            fills.append({
                'component': comp,
                'label': gap.label,
                'unit': gap.unit,
                'delta': round(delta, 3),
                'fill_fraction': round(reduce_frac, 3),
                'bonus': round(comp_bonus, 2),
            })

    fills.sort(key=lambda x: -x['bonus'])
    return {
        'bonus': round(bonus, 2),
        'fills': fills,
        'has_priority_gaps': bool(fills) or any(
            g.component in _GAP_WEIGHTS
            and (
                (g.direction == 'aim_at_least' and g.myplate_status == 'short')
                or (g.direction == 'keep_at_most' and g.myplate_status == 'over')
            )
            for g in base.gaps
        ),
    }
