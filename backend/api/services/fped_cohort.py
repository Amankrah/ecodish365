"""Cohort food-group exposure: distribution stats across N dietary recalls.

FPED is per-meal/day; researchers and clinicians work at the population level — "across
these N recalls, what's the median oz-eq red meat, and on what % of days is the
whole-grain / legumes target met?" This turns a list of recalls (each a food list) into
per-component distribution statistics + target-adherence rates, reusing the tested
per-recall `aggregate_fped` engine. Stateless: no persistence, no new model.

Each recall is aggregated independently; "meeting the target" reuses the per-recall gap
status (`'met'` = at/above an aim-at-least target, or at/below a keep-at-most limit).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .fped_aggregator import aggregate_fped


def aggregate_cohort(recalls: List[List[Dict]]) -> Dict:
    """Distribution of FPED food-group exposure across N recalls (food lists).

    Returns per food group: median / IQR / range / mean of intake across recalls, the
    MyPlate & CFG targets, and the % of recalls meeting each. `coverage` flags how many
    recalls contained foods with no FPED profile (so partial coverage is never silent).
    """
    n = len(recalls)
    if n == 0:
        return {'n_recalls': 0, 'components': [], 'coverage': {
            'mean_coverage_pct_by_mass': 0.0, 'n_recalls_with_unmatched': 0,
        }}

    aggs = [aggregate_fped(r) for r in recalls]

    comp_meta: Dict[str, tuple] = {}          # component -> (label, unit, direction, mp, cfg)
    intakes: Dict[str, List[float]] = {}
    meet_mp: Dict[str, int] = {}
    meet_cfg: Dict[str, int] = {}
    for agg in aggs:
        for g in agg.gaps:
            c = g.component
            comp_meta.setdefault(c, (g.label, g.unit, g.direction, g.myplate_target, g.cfg_target))
            intakes.setdefault(c, []).append(float(g.intake))
            meet_mp[c] = meet_mp.get(c, 0) + (1 if g.myplate_status == 'met' else 0)
            meet_cfg[c] = meet_cfg.get(c, 0) + (1 if g.cfg_status == 'met' else 0)

    components: List[Dict] = []
    for c, (label, unit, direction, mp, cfg) in comp_meta.items():
        arr = np.asarray(intakes[c], dtype=float)
        components.append({
            'component': c, 'label': label, 'unit': unit, 'direction': direction,
            'myplate_target': mp, 'cfg_target': cfg,
            'median': round(float(np.median(arr)), 2),
            'q1': round(float(np.percentile(arr, 25)), 2),
            'q3': round(float(np.percentile(arr, 75)), 2),
            'min': round(float(arr.min()), 2),
            'max': round(float(arr.max()), 2),
            'mean': round(float(arr.mean()), 2),
            'pct_meeting_myplate': round(100.0 * meet_mp[c] / n, 0),
            'pct_meeting_cfg': round(100.0 * meet_cfg[c] / n, 0),
        })

    cov_pcts = [float(a.coverage.get('coverage_pct_by_mass', 0.0)) for a in aggs]
    n_unmatched = sum(1 for a in aggs if a.coverage.get('n_no_profile', 0) > 0)
    coverage = {
        'mean_coverage_pct_by_mass': round(float(np.mean(cov_pcts)), 1) if cov_pcts else 0.0,
        'n_recalls_with_unmatched': n_unmatched,
    }
    return {'n_recalls': n, 'components': components, 'coverage': coverage}
