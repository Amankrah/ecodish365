"""Scenario S4 -- PCA biplot + Pareto frontier in (HENI gained, -GW) space.

Phase 4 of Scenario S4. Loads `_smoke_s4_panel_results.json` (Phase 3
output), runs PCA on the 4-indicator score matrix, computes the Pareto
frontier of `(heni_minutes, -env_gw_per_100kcal)` over the 100 medoid
days, and writes plotting-ready JSON artefacts.

Outputs:
    results/S4/pca_biplot.json
    results/S4/pareto_frontier.json

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_s4_pca_pareto.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.decomposition import PCA


_HERE = os.path.abspath('.')
_REPO = os.path.abspath(os.path.join(_HERE, '..'))
_INPUT = os.path.join(_HERE, '_smoke_s4_panel_results.json')
_RESULTS_DIR = os.path.join(_REPO, 'results', 'S4')

# Indicator columns the PCA operates on. We exclude GW from the diet-quality
# PCA (PCA #1) so PC1 captures the dominant nutrition-quality axis; GW is
# carried separately as a coloring variable in the SI biplot.
_PCA_INDICATORS = [
    ('HEFI', 'hefi_score'),
    ('HENI', 'heni_minutes'),
    ('HSR',  'hsr_stars'),
    ('FCS',  'fcs_score'),
]


def _is_finite_number(x) -> bool:
    return isinstance(x, (int, float)) and not (math.isnan(x) or math.isinf(x))


def _dominates_2d(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    """True if a dominates b in 2-D (a >= b on both, a > b on at least one).

    Both axes are 'higher = better' after sign convention is applied by
    the caller; for S4 we use (heni_minutes, -env_gw_per_100kcal), so
    larger is better on each axis.
    """
    ge_all = a[0] >= b[0] and a[1] >= b[1]
    gt_one = a[0] > b[0] or a[1] > b[1]
    return ge_all and gt_one


def _pareto_frontier_2d(points: List[Tuple[int, Tuple[float, float]]]) -> List[int]:
    """Return list of indices on the Pareto frontier (non-dominated set).

    Points are `(panel_idx, (x, y))` tuples; both axes are 'higher = better'.
    Implementation: standard O(n^2) dominance check. For n = 100 this is
    instant; no need for the sweep-line variant.
    """
    on_frontier: List[int] = []
    for i, ai in points:
        dominated = False
        for j, aj in points:
            if i != j and _dominates_2d(aj, ai):
                dominated = True
                break
        if not dominated:
            on_frontier.append(i)
    return on_frontier


def main() -> int:
    with open(_INPUT, 'r', encoding='utf-8') as f:
        s4 = json.load(f)
    rows = s4['meals']
    print(f'S4 PCA + Pareto: loaded {len(rows)} meals from {_INPUT}')
    print('=' * 80)

    os.makedirs(_RESULTS_DIR, exist_ok=True)

    # ---- PCA on the 4-indicator matrix --------------------------------------
    keep_idx: List[int] = []
    M: List[List[float]] = []
    for idx, r in enumerate(rows):
        vec = [r.get(field) for _label, field in _PCA_INDICATORS]
        if all(_is_finite_number(v) for v in vec):
            keep_idx.append(idx)
            M.append([float(v) for v in vec])
    X = np.array(M)
    n, p = X.shape
    if n < 5:
        print(f'ERROR: only {n} complete rows; cannot run PCA.')
        return 1

    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma_safe = np.where(sigma < 1e-9, 1.0, sigma)
    Xz = (X - mu) / sigma_safe

    pca = PCA(n_components=p, random_state=42)
    scores = pca.fit_transform(Xz)
    loadings = pca.components_  # shape (p, p): loadings[k, j] = PCj contribution
    var_explained = pca.explained_variance_ratio_

    print('PCA on standardized HEFI/HENI/HSR/FCS scores:')
    print(f'   n rows used = {n} / {len(rows)} (rows with all four indicators)')
    for k in range(p):
        cum = var_explained[:k+1].sum() * 100
        print(f'   PC{k+1}: variance explained = {var_explained[k]*100:5.2f} %   '
              f'cumulative = {cum:5.2f} %')
    print()
    print('Loadings (rows = indicators, cols = PCs):')
    print(f'   {"":<6}', end='')
    for k in range(p):
        print(f'PC{k+1:<5}', end='')
    print()
    for j, (label, _) in enumerate(_PCA_INDICATORS):
        print(f'   {label:<6}', end='')
        for k in range(p):
            print(f'{loadings[k, j]:+6.3f}', end=' ')
        print()
    print()

    # ---- Pareto frontier in (HENI gained, -GW per 100 kcal) space -----------
    pareto_idx: List[Tuple[int, Tuple[float, float]]] = []
    for r in rows:
        heni = r.get('heni_minutes')
        gw = r.get('env_gw_per_100kcal')
        if _is_finite_number(heni) and _is_finite_number(gw):
            # Convert to "higher = better" on both axes
            pareto_idx.append((rows.index(r), (float(heni), -float(gw))))
    if len(pareto_idx) < 5:
        print(f'WARN: only {len(pareto_idx)} rows have both HENI and GW.')

    frontier = _pareto_frontier_2d(pareto_idx)
    print(f'Pareto frontier in (HENI minutes, -GW per 100 kcal):')
    print(f'   n evaluated = {len(pareto_idx)} / {len(rows)}')
    print(f'   n on frontier = {len(frontier)}')
    print()
    print(f'   {"day_id":<10} {"stratum":<24} '
          f'{"HEFI":>5}  {"HENI":>7}  {"HSR":>4}  {"FCS":>5}  {"GW/100k":>8}')
    for idx in frontier:
        r = rows[idx]
        print(f'   {r["day_id"]:<10} '
              f'{r.get("agesex_group", "")[:10]}/q{r.get("fipr_quintile", "")}'.ljust(28),
              end='')
        print(f'{r.get("hefi_score") or 0:>5.1f}  '
              f'{r.get("heni_minutes") or 0:+7.1f}  '
              f'{r.get("hsr_stars") or 0:>4.1f}  '
              f'{r.get("fcs_score") or 0:>5.1f}  '
              f'{r.get("env_gw_per_100kcal") or 0:>8.3f}')
    print()

    # ---- Persist artefacts ---------------------------------------------------
    pca_out = {
        'panel_description': 'PCA biplot of HEFI/HENI/HSR/FCS '
                             'on the 100-day S4 NHANES medoid panel.',
        'n_rows_used': n,
        'n_rows_total': len(rows),
        'indicators': [label for label, _ in _PCA_INDICATORS],
        'standardisation': 'z-score per indicator across the panel',
        'variance_explained_ratio': var_explained.tolist(),
        'cumulative_variance_explained': np.cumsum(var_explained).tolist(),
        'loadings': {
            f'PC{k+1}': {
                label: float(loadings[k, j])
                for j, (label, _) in enumerate(_PCA_INDICATORS)
            }
            for k in range(p)
        },
        'per_day_scores_pc1_pc2': [
            {
                'day_id': rows[keep_idx[i]]['day_id'],
                'agesex_group': rows[keep_idx[i]]['agesex_group'],
                'fipr_quintile': rows[keep_idx[i]]['fipr_quintile'],
                'PC1': float(scores[i, 0]),
                'PC2': float(scores[i, 1]),
            }
            for i in range(n)
        ],
    }
    pca_path = os.path.join(_RESULTS_DIR, 'pca_biplot.json')
    with open(pca_path, 'w', encoding='utf-8') as f:
        json.dump(pca_out, f, indent=2)

    pareto_out = {
        'panel_description': 'Pareto frontier in (HENI minutes, -GW per '
                             '100 kcal) space for the 100-day S4 panel. '
                             'Both axes are higher-is-better after the GW '
                             'sign convention.',
        'axes': {
            'x': {'metric': 'heni_minutes',
                  'direction': 'maximise',
                  'unit': 'health-impact minutes per day'},
            'y': {'metric': '-env_gw_per_100kcal',
                  'direction': 'maximise (i.e. minimise GW)',
                  'unit': '-kg CO2 eq / 100 kcal'},
        },
        'n_rows_total': len(rows),
        'n_rows_evaluated': len(pareto_idx),
        'n_on_frontier': len(frontier),
        'frontier': [
            {
                'day_id': rows[idx]['day_id'],
                'seqn': rows[idx]['seqn'],
                'agesex_group': rows[idx]['agesex_group'],
                'fipr_quintile': rows[idx]['fipr_quintile'],
                'occasion_mix': rows[idx].get('occasion_mix', ''),
                'hefi_score': rows[idx]['hefi_score'],
                'heni_minutes': rows[idx]['heni_minutes'],
                'hsr_stars': rows[idx]['hsr_stars'],
                'fcs_score': rows[idx]['fcs_score'],
                'env_gw_per_100kcal': rows[idx]['env_gw_per_100kcal'],
            }
            for idx in frontier
        ],
        'all_days_with_frontier_flag': [
            {
                'day_id': r['day_id'],
                'on_frontier': i in frontier,
                'heni_minutes': r.get('heni_minutes'),
                'env_gw_per_100kcal': r.get('env_gw_per_100kcal'),
            }
            for i, r in enumerate(rows)
        ],
    }
    pareto_path = os.path.join(_RESULTS_DIR, 'pareto_frontier.json')
    with open(pareto_path, 'w', encoding='utf-8') as f:
        json.dump(pareto_out, f, indent=2)

    print('=' * 80)
    print(f'PC1 + PC2 variance explained: '
          f'{(var_explained[0] + var_explained[1]) * 100:.1f} %')
    print(f'Wrote {pca_path}')
    print(f'      {pareto_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
