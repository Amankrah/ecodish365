"""Pareto frontier for SUBST-1 Phase 3 trade-off visualization."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

# Metrics to maximize (delta). Substitution is FCS-only (see
# substitution_scorecard.SCORECARD_METRICS); other axes left as keys so
# re-enabling them later just requires re-listing here.
PARETO_AXES = ('fcs',)


def _axis_value(suggestion: Dict[str, Any], metric: str) -> float | None:
    deltas = (suggestion.get('scorecard') or {}).get('deltas') or {}
    d = deltas.get(metric) or {}
    delta = d.get('delta')
    if delta is None:
        return None
    meta = ((suggestion.get('scorecard') or {}).get('baseline') or {}).get(metric) or {}
    if meta.get('invert') or metric == 'environmental':
        return -float(delta)
    return float(delta)


def _dominates(a: Dict[str, float], b: Dict[str, float]) -> bool:
    """True if vector a Pareto-dominates b (all >=, one >)."""
    if not a or not b:
        return False
    keys = set(a) & set(b)
    if not keys:
        return False
    ge_all = all(a[k] >= b[k] for k in keys)
    gt_one = any(a[k] > b[k] for k in keys)
    return ge_all and gt_one


def compute_pareto_frontier(
    suggestions: List[Dict[str, Any]],
    *,
    axes: Optional[tuple] = None,
) -> List[Dict[str, Any]]:
    """Return non-dominated suggestions with trade-off tags."""
    pareto_axes = axes or PARETO_AXES
    if not suggestions:
        return []

    vectors: List[Tuple[int, Dict[str, float]]] = []
    for i, s in enumerate(suggestions):
        vec = {}
        for m in pareto_axes:
            v = _axis_value(s, m)
            if v is not None:
                vec[m] = v
        if vec:
            vectors.append((i, vec))

    frontier_indices: List[int] = []
    for i, vi in vectors:
        dominated = False
        for j, vj in vectors:
            if i != j and _dominates(vj, vi):
                dominated = True
                break
        if not dominated:
            frontier_indices.append(i)

    frontier: List[Dict[str, Any]] = []
    for idx in frontier_indices:
        s = suggestions[idx]
        wins = []
        for m in pareto_axes:
            v = _axis_value(s, m)
            if v is not None and v > 0.01:
                wins.append(m)
        s['pareto'] = {
            'on_frontier': True,
            'wins_on': wins,
        }
        frontier.append(s)

    frontier_ids = {suggestions[i].get('id') for i in frontier_indices}
    for s in suggestions:
        if s.get('id') not in frontier_ids:
            s['pareto'] = {'on_frontier': False, 'wins_on': []}

    return frontier
