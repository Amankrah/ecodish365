"""Per-recall BNS subgroup intake aggregation (PLATFORM-CODE-1.m m.C, 2026-06-26).

Bridges every food in a recall to its CCHS-FCT 2015 BNS subgroup via
[`cnf_to_bns_bridge.bns_subgroup_for_cnf`](backend/api/services/cnf_to_bns_bridge.py)
and sums grams per (recall × subgroup). The output shape mirrors
[`fped_aggregator.aggregate_fped`](backend/api/services/fped_aggregator.py)
+ [`fped_cohort.aggregate_cohort`](backend/api/services/fped_cohort.py) —
distribution stats per subgroup across the cohort + coverage flags so
unbridged mass is never silently zeroed.

Public API:

* `aggregate_recall_to_bns(foods) → {bns_code: total_g_bridged, ...}` +
  per-recall coverage (mass bridged vs total).
* `aggregate_cohort_to_bns(recalls) → per-subgroup distribution +
  coverage report` (used directly by the population-reference compare
  endpoint).

Suppression: the aggregator does not consume FCT suppression flags —
those are applied at the comparison layer when matching a cohort
subgroup intake against the published national cell.
"""
from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from typing import Any, Dict, List, Sequence

from api.services.cnf_to_bns_bridge import bns_subgroup_for_cnf

logger = logging.getLogger(__name__)


def _percentile(sorted_vals: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile. `p` in [0, 100]."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return float(sorted_vals[f]) + (float(sorted_vals[c]) - float(sorted_vals[f])) * (k - f)


def aggregate_recall_to_bns(foods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum food mass per BNS subgroup for one recall. Returns
    `{subgroup_totals: {bns_code: grams}, coverage: {bridged_g, unbridged_g, pct_bridged, n_foods_bridged, n_foods_unbridged}}`."""
    totals: Dict[str, float] = defaultdict(float)
    bridge_confidences: Dict[str, List[float]] = defaultdict(list)
    bridged_g = 0.0
    unbridged_g = 0.0
    n_bridged = 0
    n_unbridged = 0
    for f in foods or []:
        try:
            fid = int(f.get('food_id'))
            mass = float(f.get('mass_g', 0.0))
        except (TypeError, ValueError):
            continue
        if fid <= 0 or mass <= 0:
            continue
        info = bns_subgroup_for_cnf(fid)
        if info is None:
            unbridged_g += mass
            n_unbridged += 1
            continue
        bns_code = info['bns_code']
        totals[bns_code] += mass
        bridge_confidences[bns_code].append(float(info.get('confidence', 0.0)))
        bridged_g += mass
        n_bridged += 1
    total_g = bridged_g + unbridged_g
    return {
        'subgroup_totals':    dict(totals),
        'bridge_confidences': {k: round(sum(v) / len(v), 3) for k, v in bridge_confidences.items()},
        'coverage': {
            'bridged_g':         round(bridged_g, 2),
            'unbridged_g':       round(unbridged_g, 2),
            'pct_bridged':       round(100.0 * bridged_g / max(1e-9, total_g), 1),
            'n_foods_bridged':   n_bridged,
            'n_foods_unbridged': n_unbridged,
        },
    }


def aggregate_cohort_to_bns(recalls: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Per-subgroup distribution stats across N recalls + cohort coverage.

    Output:
        {
          'n_recalls': int,
          'per_subgroup': [
            {
              'bns_code': str,
              'n_eaters': int,                    # recalls with subgroup intake > 0
              'pct_eaters': float,
              'median_g_eaters': float,           # median across eaters only
              'q1_g_eaters': float,
              'q3_g_eaters': float,
              'p90_g_eaters': float,
              'p95_g_eaters': float,
              'mean_g_eaters': float,
              'median_g_all': float,              # median across ALL recalls (zeros included)
              'p90_g_all': float,
              'p95_g_all': float,
              'mean_g_all': float,
              'mean_bridge_confidence': float,
            },
            ...
          ],
          'coverage': {
            'mean_pct_bridged': float,
            'n_recalls_with_unbridged_mass': int,
            'n_recalls_zero_bridge_coverage': int,
          },
        }
    """
    n = len(recalls or [])
    if n == 0:
        return {'n_recalls': 0, 'per_subgroup': [],
                'coverage': {'mean_pct_bridged': 0.0,
                             'n_recalls_with_unbridged_mass': 0,
                             'n_recalls_zero_bridge_coverage': 0}}

    per_recall = [aggregate_recall_to_bns(r) for r in recalls]

    # Collect per-subgroup intake series + bridge confidences.
    subgroup_intakes: Dict[str, List[float]] = defaultdict(list)   # eaters-only
    subgroup_all: Dict[str, List[float]] = defaultdict(list)       # all-recalls incl. zeros
    subgroup_conf: Dict[str, List[float]] = defaultdict(list)
    for r_out in per_recall:
        for bns_code, g in r_out['subgroup_totals'].items():
            subgroup_intakes[bns_code].append(g)
        # Need to track zeros per subgroup across all recalls — build the
        # universe of seen subgroups first.
    seen_subgroups = set(subgroup_intakes.keys())
    for r_out in per_recall:
        seen = set(r_out['subgroup_totals'].keys())
        for code in seen_subgroups:
            subgroup_all[code].append(r_out['subgroup_totals'].get(code, 0.0))
        for code, conf in r_out['bridge_confidences'].items():
            subgroup_conf[code].append(conf)

    per_subgroup: List[Dict[str, Any]] = []
    for code in sorted(seen_subgroups):
        eaters = sorted(v for v in subgroup_intakes[code] if v > 0)
        all_vals = sorted(subgroup_all[code])
        if not all_vals:
            continue
        n_eaters = len(eaters)
        eaters_block = {}
        if eaters:
            eaters_block = {
                'median_g_eaters': round(_percentile(eaters, 50), 2),
                'q1_g_eaters':     round(_percentile(eaters, 25), 2),
                'q3_g_eaters':     round(_percentile(eaters, 75), 2),
                'p90_g_eaters':    round(_percentile(eaters, 90), 2),
                'p95_g_eaters':    round(_percentile(eaters, 95), 2),
                'mean_g_eaters':   round(statistics.fmean(eaters), 2),
            }
        per_subgroup.append({
            'bns_code':                code,
            'n_eaters':                n_eaters,
            'pct_eaters':              round(100.0 * n_eaters / n, 1),
            **eaters_block,
            'median_g_all':            round(_percentile(all_vals, 50), 2),
            'p90_g_all':               round(_percentile(all_vals, 90), 2),
            'p95_g_all':               round(_percentile(all_vals, 95), 2),
            'mean_g_all':              round(statistics.fmean(all_vals), 2),
            'mean_bridge_confidence':  round(statistics.fmean(subgroup_conf[code]), 3)
                                       if subgroup_conf[code] else None,
        })

    pct_bridged_series = [r['coverage']['pct_bridged'] for r in per_recall]
    n_with_unbridged = sum(1 for r in per_recall if r['coverage']['n_foods_unbridged'] > 0)
    n_zero_coverage = sum(1 for r in per_recall if r['coverage']['pct_bridged'] == 0.0)

    return {
        'n_recalls':   n,
        'per_subgroup': per_subgroup,
        'coverage': {
            'mean_pct_bridged':              round(statistics.fmean(pct_bridged_series), 1)
                                              if pct_bridged_series else 0.0,
            'n_recalls_with_unbridged_mass': n_with_unbridged,
            'n_recalls_zero_bridge_coverage': n_zero_coverage,
        },
    }
