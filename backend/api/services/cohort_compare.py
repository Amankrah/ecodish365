"""Cohort-vs-cohort comparison (PLATFORM-CODE-1.b Phase D, 2026-06-26).

Computes per-lens distribution deltas + a non-parametric Mann-Whitney U
test for each numeric lens. The U test is the right hammer here: cohort
score distributions are rarely Gaussian (HEFI is bounded 0-80; HSR is
discrete 0.5-5.0 in 0.5 steps; HENI has heavy tails near zero), so a
two-sample t-test would be misleading. Mann-Whitney is rank-based,
makes no normality assumption, and answers the actual question a
researcher wants ("does cohort B systematically score differently from
cohort A on this lens?") in one number.

Effect size: rank-biserial r (Cliff's delta variant) reported alongside
p so the user can distinguish "tiny but statistically significant" from
"meaningfully different." See King & Minium 2008 §11.6 for the formula
used here: r = 1 - 2U / (n1 * n2).

This module is pure compute — no Django imports, no I/O.
"""
from __future__ import annotations

import logging
import statistics
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


_NUMERIC_LENS_FIELDS: List[tuple] = [
    # (lens_key, score_field, unit_label)
    ('hefi',               'hefi_total_score',       '0-80'),
    ('heni',               'heni_minutes',           'min / day'),
    ('hsr',                'hsr_stars',              '0.5-5.0'),
    ('fcs',                'fcs_score',              '1-100'),
    ('env_gw',             'env_gw_per_100kcal',     'kg CO₂e / 100 kcal'),
    ('env_sustainability', 'env_sustainability',     '0-100'),
    ('env_cost',           'env_monetized_cost',     'USD / 100 kcal'),
    ('fped_coverage',      'fped_unmatched_pct',     '%'),
]


def _extract_values(rows: List[Dict[str, Any]], field: str) -> List[float]:
    out: List[float] = []
    for r in rows or []:
        v = r.get(field)
        if v is None:
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _summary(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {'n': 0, 'median': None, 'mean': None, 'sd': None, 'min': None, 'max': None}
    return {
        'n':      len(values),
        'median': statistics.median(values),
        'mean':   statistics.fmean(values),
        'sd':     statistics.stdev(values) if len(values) >= 2 else 0.0,
        'min':    min(values),
        'max':    max(values),
    }


def _mann_whitney(a: List[float], b: List[float]) -> Dict[str, Any]:
    """Two-sided Mann-Whitney U with rank-biserial effect size.
    Returns None for `p` / `effect_r` when either sample has fewer than 3
    observations — the test is underpowered to be reportable."""
    if len(a) < 3 or len(b) < 3:
        return {'u': None, 'p': None, 'effect_r': None, 'n_a': len(a), 'n_b': len(b),
                'note': 'sample too small for MW (need n>=3 in both groups)'}
    try:
        from scipy.stats import mannwhitneyu
    except ImportError:
        return {'u': None, 'p': None, 'effect_r': None, 'n_a': len(a), 'n_b': len(b),
                'note': 'scipy not available'}
    try:
        res = mannwhitneyu(a, b, alternative='two-sided')
        u = float(res.statistic)
        p = float(res.pvalue)
        # Rank-biserial effect size (King & Minium 2008 §11.6):
        # r = 1 - 2U / (n1 * n2). With scipy's U = #{(i,j) : a_i > b_j}:
        #   r = +1 when A is uniformly below B (B higher)
        #   r = -1 when A is uniformly above B (A higher)
        # So r > 0 → B tends higher; r < 0 → A tends higher.
        effect = 1.0 - (2.0 * u / (len(a) * len(b)))
        return {'u': u, 'p': p, 'effect_r': effect, 'n_a': len(a), 'n_b': len(b)}
    except Exception as exc:  # noqa: BLE001
        logger.warning('Mann-Whitney failed: %s', exc)
        return {'u': None, 'p': None, 'effect_r': None, 'n_a': len(a), 'n_b': len(b),
                'note': f'mw_error: {exc}'}


def compare_cohorts(
    a_rows: List[Dict[str, Any]],
    b_rows: List[Dict[str, Any]],
    a_name: str = 'Cohort A',
    b_name: str = 'Cohort B',
    lens_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Per-lens delta + Mann-Whitney U. Returns a dict shaped for the
    frontend table."""
    per_lens: List[Dict[str, Any]] = []
    selected = set(lens_keys) if lens_keys else None
    for lens_key, field, unit in _NUMERIC_LENS_FIELDS:
        if selected is not None and lens_key not in selected:
            continue
        a_vals = _extract_values(a_rows, field)
        b_vals = _extract_values(b_rows, field)
        a_sum = _summary(a_vals)
        b_sum = _summary(b_vals)
        median_delta = None
        if a_sum['median'] is not None and b_sum['median'] is not None:
            median_delta = round(b_sum['median'] - a_sum['median'], 4)
        mw = _mann_whitney(a_vals, b_vals)
        per_lens.append({
            'lens':         lens_key,
            'field':        field,
            'unit':         unit,
            'a':            {k: (None if v is None else (round(v, 4) if isinstance(v, float) else v))
                             for k, v in a_sum.items()},
            'b':            {k: (None if v is None else (round(v, 4) if isinstance(v, float) else v))
                             for k, v in b_sum.items()},
            'median_delta': median_delta,
            'mann_whitney': {
                'u':        None if mw.get('u') is None else round(mw['u'], 2),
                'p':        None if mw.get('p') is None else round(mw['p'], 6),
                'effect_r': None if mw.get('effect_r') is None else round(mw['effect_r'], 4),
                'n_a':      mw.get('n_a'),
                'n_b':      mw.get('n_b'),
                'note':     mw.get('note'),
            },
        })
    return {
        'cohort_a': {'name': a_name, 'n': len(a_rows)},
        'cohort_b': {'name': b_name, 'n': len(b_rows)},
        'per_lens': per_lens,
        'method':   {
            'test':           'Mann-Whitney U, two-sided',
            'effect_size':    'rank-biserial r = 1 - 2U/(n_a*n_b); positive = B higher, negative = A higher',
            'min_sample_n':   3,
            'multiple_testing_note':
                'p-values are unadjusted across the lens panel; apply BH or Bonferroni '
                'if your study design treats all lenses as primary endpoints.',
        },
    }
