"""Bland-Altman limits-of-agreement across the four nutrition indicators.

Plan B (Tier 1 statistical analyses). Loads the existing S4-lite 25-day
per-day score artefact (`_smoke_s4_lite_panel_results.json`), rescales each
indicator (HENI / HEFI / HSR / FCS) to a common percentile axis on [0, 100]
across the 25 days, and reports per-pair:

  - mean bias        : mean of (a - b) on percentile-rescaled scores
  - SD of differences
  - LoA              : bias +/- 1.96 * SD
  - pct_outside_loa  : share of days outside [LoA_lo, LoA_hi]
                       (expected ~5 % if differences are Gaussian)

Why a separate script from `_smoke_nutrition_cross_system.py`:
Bland-Altman wants n >= 25 for meaningful limits. The 6-meal cross-system
panel is too small; the 25-day S4-lite panel is the right substrate.

Why percentile-rescaling: HEFI 0-80, HSR 0-5, HENI continuous in minutes,
FCS 0-100. Bland-Altman on raw scales would be meaningless; percentile
puts every indicator on a common 0-100 axis where "0 = worst day in
panel" and "100 = best day in panel", so a non-zero bias means one
indicator systematically ranks days higher (or lower) than the other.

Run from `backend/`:
    python _smoke_indicator_bland_altman.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Tuple


_HERE = os.path.abspath('.')
_S4_LITE_RESULTS = os.path.join(_HERE, '_smoke_s4_lite_panel_results.json')
_OUTPUT_JSON = os.path.join(_HERE, '_smoke_indicator_bland_altman_results.json')


# Indicators that share the same rank semantics: higher = better nutrition.
# HENI minutes positive = beneficial; HEFI score higher = better; HSR stars
# higher = better; FCS score higher = better. All four agree on direction
# after percentile-rescaling, so bias reflects systematic generosity.
INDICATORS: List[Tuple[str, str]] = [
    ('HENI', 'heni_minutes'),
    ('HEFI', 'hefi_score'),
    ('HSR',  'hsr_stars'),
    ('FCS',  'fcs_score'),
]


def _percentile_rescale(values: List[float]) -> List[float]:
    """Average-rank percentile rescaling to [0, 100]. Ties get mean rank.

    A value at the kth-of-n rank (1-indexed) maps to 100 * (rank - 1) / (n - 1).
    A pure-Python implementation matching the rank-averaging convention
    used by the Spearman helper in `_smoke_nutrition_cross_system.py`.
    """
    n = len(values)
    if n < 2:
        return [50.0] * n
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        # tied block i..j -> average rank = (i + j) / 2 + 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1
    return [100.0 * (r - 1.0) / (n - 1.0) for r in ranks]


def _bland_altman_pair(a: List[float], b: List[float]) -> Dict[str, float]:
    """One indicator pair: bias, SD, LoA, pct outside LoA."""
    diffs = [a[i] - b[i] for i in range(len(a))]
    bias = sum(diffs) / len(diffs)
    var = sum((d - bias) ** 2 for d in diffs) / max(1, len(diffs) - 1)
    sd = math.sqrt(var)
    loa_lo = bias - 1.96 * sd
    loa_hi = bias + 1.96 * sd
    n_outside = sum(1 for d in diffs if d < loa_lo or d > loa_hi)
    pct_outside = 100.0 * n_outside / len(diffs)
    return {
        'n': len(diffs),
        'bias': bias,
        'sd_diff': sd,
        'loa_lo': loa_lo,
        'loa_hi': loa_hi,
        'pct_outside_loa': pct_outside,
    }


def main() -> int:
    if not os.path.exists(_S4_LITE_RESULTS):
        print(f'ERROR: S4-lite results not found at {_S4_LITE_RESULTS}')
        print('Run `python _smoke_s4_lite_panel.py` first to generate it.')
        return 1

    with open(_S4_LITE_RESULTS, 'r', encoding='utf-8') as f:
        s4lite = json.load(f)

    days = s4lite.get('days', [])
    if len(days) < 5:
        print(f'ERROR: only {len(days)} days in S4-lite artefact; need >= 5.')
        return 1

    print('Bland-Altman limits-of-agreement (4 nutrition indicators on S4-lite)')
    print(f'  Panel: {len(days)}-day curated diets from {_S4_LITE_RESULTS}')
    print(f'  Rescaling: average-rank percentile to [0, 100] across the panel')
    print('=' * 80)
    print()

    raw_scores: Dict[str, List[float]] = {}
    for ind_label, field in INDICATORS:
        vals: List[float] = []
        missing = 0
        for d in days:
            v = d.get(field)
            if v is None:
                missing += 1
                vals.append(float('nan'))
            else:
                vals.append(float(v))
        raw_scores[ind_label] = vals
        if missing:
            print(f'  WARN: {ind_label} missing {missing}/{len(vals)} day rows')

    # Drop any day where any indicator is missing.
    valid_idx = [i for i in range(len(days))
                 if all(raw_scores[lab][i] == raw_scores[lab][i]
                        for lab, _ in INDICATORS)]
    if len(valid_idx) < 5:
        print(f'ERROR: only {len(valid_idx)} days have all four indicators.')
        return 1

    rescaled: Dict[str, List[float]] = {}
    for lab, _ in INDICATORS:
        col = [raw_scores[lab][i] for i in valid_idx]
        rescaled[lab] = _percentile_rescale(col)

    pairs = []
    for i, (lab_a, _) in enumerate(INDICATORS):
        for j in range(i + 1, len(INDICATORS)):
            lab_b = INDICATORS[j][0]
            pairs.append((lab_a, lab_b))

    print(f'   pair          n   bias    SD    LoA_lo    LoA_hi    %outside')
    print(f'   {"-"*4:14}{"-":>3} {"-"*5} {"-"*5} {"-"*8} {"-"*8} {"-"*8}')
    pair_results: Dict[str, Dict[str, float]] = {}
    for lab_a, lab_b in pairs:
        a = rescaled[lab_a]
        b = rescaled[lab_b]
        stats = _bland_altman_pair(a, b)
        key = f'{lab_a}_vs_{lab_b}'
        pair_results[key] = stats
        print(f'   {lab_a:>4} vs {lab_b:<4}   {stats["n"]:>2} '
              f'{stats["bias"]:+6.2f} {stats["sd_diff"]:5.2f} '
              f'{stats["loa_lo"]:+8.2f} {stats["loa_hi"]:+8.2f} '
              f'{stats["pct_outside_loa"]:6.1f}%')
    print()

    # Per-pair per-day mean/diff table for SI figure plotting later.
    pair_series: Dict[str, List[Dict[str, float]]] = {}
    for lab_a, lab_b in pairs:
        a = rescaled[lab_a]
        b = rescaled[lab_b]
        series = []
        for k, i in enumerate(valid_idx):
            mean_ab = (a[k] + b[k]) / 2.0
            diff_ab = a[k] - b[k]
            series.append({
                'day_id': days[i].get('day_id', f'idx_{i}'),
                'mean': mean_ab,
                'diff': diff_ab,
            })
        pair_series[f'{lab_a}_vs_{lab_b}'] = series

    out = {
        'panel_description': 'Bland-Altman limits-of-agreement on percentile-'
                             'rescaled scores (HENI, HEFI, HSR, FCS) across '
                             'the S4-lite 25-day curated panel.',
        'source_panel': _S4_LITE_RESULTS,
        'n_days_used': len(valid_idx),
        'rescaling': 'average-rank percentile to [0, 100]',
        'loa_z': 1.96,
        'pairs': pair_results,
        'pair_series_for_si_figure': pair_series,
        'raw_scores_by_indicator': {
            lab: [raw_scores[lab][i] for i in valid_idx] for lab, _ in INDICATORS
        },
        'rescaled_scores_by_indicator': rescaled,
        'caveats': [
            'Bias is identically 0 by construction under average-rank '
            'percentile rescaling, because both indicators map to a common '
            '[0, 100] axis with the same panel-level mean. The substantive '
            'quantity is LoA WIDTH (= 1.96 * 2 * SD_diff = 3.92 * SD_diff), '
            'which captures day-by-day disagreement and ranks the pairs '
            'by how tightly they agree at the per-day level.',
            'LoA is the 95 %% interval of per-day differences. Days outside '
            'LoA are candidates for "indicators disagree most strongly" '
            'narrative in SI.',
            'Percentile-rescaling normalises units but is itself bounded to '
            '[0, 100]; LoA cannot exceed +/-100. Interpret the absolute '
            'numbers in percentile-points, not in indicator-native units.',
            'For raw-units Bland-Altman against a published reference '
            'distribution (e.g. HEFI 43.1/80 from Brassard CCHS), pair-level '
            'bias would be informative but would require licensed reference '
            'panels; deferred to v2 alongside Scenario S4 RDC access.',
        ],
    }
    with open(_OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print('=' * 80)
    print(f'Pairs evaluated: {len(pair_results)} | n = {len(valid_idx)} days')
    # Bias is identically 0 by construction under percentile rescaling
    # (both indicators map to the same [0, 100] axis), so the interpretable
    # quantity is LoA WIDTH = 1.96 * 2 * SD = 3.92 * SD. Narrower LoA =
    # tighter day-by-day agreement.
    widths = [(k, 3.92 * v['sd_diff']) for k, v in pair_results.items()]
    widths.sort(key=lambda x: x[1])
    print('LoA WIDTH ranking (tightest day-by-day agreement first):')
    for k, w in widths:
        print(f'   {k:<14}  +/- {w / 2:.1f} percentile pts '
              f'(width {w:.1f})')
    print()
    print(f'Tightest pair:  {widths[0][0]} (LoA width {widths[0][1]:.1f} pp)')
    print(f'Widest  pair:  {widths[-1][0]} (LoA width {widths[-1][1]:.1f} pp)')
    print(f'Results JSON:  {_OUTPUT_JSON}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
