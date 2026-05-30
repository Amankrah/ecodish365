"""Scenario S4 100-meal medoid panel via stratified k-medoids on NHANES.

Phase 2 of Scenario S4. Loads `nhanes_2017_meal_pool.json` (Phase 1 output),
computes a per-meal nutrient feature vector, stratifies by (age-sex group
x meal occasion x FIPR quintile), runs PAM inside each cell at k_cell
proportional to the cell's population share, and writes the 100 medoid
meals to `s4_panel_meals.json`.

Per-meal feature vector for clustering uses NHANES self-reported macros
(already aggregated in Phase 1) per 100 kcal so meals of different sizes
are placed by composition, not absolute size:

    [kcal_total,                       # absolute size kept as 1 dimension
     protein_pct_kcal, fat_pct_kcal,
     carb_pct_kcal, sugar_pct_kcal,
     sat_fat_pct_kcal,
     sodium_mg_per_100kcal, fibre_g_per_100kcal]

Stratification matches Brassard 2022b Table A2 grouping plus meal occasion
and FIPR quintile (3 x 4 x 5 = 60 cells). The total medoid budget is 100;
per-cell allocation is `round(100 * n_cell / N_total)`; rounding-residual
reallocation ensures we land on exactly 100.

Run from `backend/`:
    python -m api.services.etl.build_s4_panel_medoids

Inputs:
    api/data/nhanes_2017_meal_pool.json

Output:
    api/data/s4_panel_meals.json
"""
from __future__ import annotations

import json
import logging
import math
import os
import sys
from collections import Counter
from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial.distance import pdist, squareform

logger = logging.getLogger(__name__)

_HERE = os.path.abspath(os.path.dirname(__file__))
_BACKEND = os.path.abspath(os.path.join(_HERE, '..', '..', '..'))
_INPUT = os.path.join(_BACKEND, 'api', 'data', 'nhanes_2017_day_pool.json')
_OUTPUT = os.path.join(_BACKEND, 'api', 'data', 's4_panel_meals.json')

_TARGET_PANEL_SIZE = 100
_RANDOM_STATE = 42


def _features_for_meal(m: Dict) -> List[float]:
    """Composition vector. Uses NHANES self-reported macros so the feature
    space is consistent across the pool regardless of whether downstream
    CNF scoring uses different per-100g values for the matched foods.
    """
    mac = m['macros_nhanes_self_reported']
    kcal = max(1.0, mac['kcal'])  # guard against zero
    protein_pct = 4.0 * mac['protein_g'] / kcal * 100
    fat_pct = 9.0 * mac['fat_g'] / kcal * 100
    carb_pct = 4.0 * mac['carb_g'] / kcal * 100
    sugar_pct = 4.0 * mac['sugar_g'] / kcal * 100
    sat_pct = 9.0 * mac['sat_fat_g'] / kcal * 100
    sodium_per_100k = mac['sodium_mg'] / kcal * 100
    fibre_per_100k = mac['fibre_g'] / kcal * 100
    return [
        kcal,
        protein_pct, fat_pct, carb_pct,
        sugar_pct, sat_pct,
        sodium_per_100k, fibre_per_100k,
    ]


def _pam_alternate(X: np.ndarray, k: int, seed: int = 42,
                    max_iter: int = 100) -> np.ndarray:
    """Partitioning Around Medoids ('alternate' method).

    Pure-numpy implementation matching scikit-learn-extra's
    `KMedoids(method='alternate')` shape so the reproducibility prose in
    the manuscript still cites PAM. Returns medoid local indices (length
    k) in row order. Distance metric is Euclidean (the manuscript-level
    standard for nutritional-profile clustering).

    Algorithm:
      1. Compute the full n x n pairwise distance matrix once.
      2. Initialise medoids by k-means++-style seeding on distances.
      3. Repeat until no medoid moves:
         (a) assign each point to its nearest medoid;
         (b) within each cluster, the new medoid is the point with the
             minimum sum of distances to other points in the cluster.
    """
    n = X.shape[0]
    if k >= n:
        return np.arange(n)
    D = squareform(pdist(X, metric='euclidean'))
    rng = np.random.default_rng(seed)
    # k-means++-style seeding for stable convergence
    medoids = np.empty(k, dtype=int)
    medoids[0] = rng.integers(n)
    for j in range(1, k):
        d_min = D[medoids[:j]].min(axis=0)
        probs = d_min ** 2
        s = probs.sum()
        if s <= 0:
            medoids[j] = rng.integers(n)
        else:
            medoids[j] = rng.choice(n, p=probs / s)
    medoids = np.unique(medoids)
    # If seeding produced duplicates (rare on tiny cells) pad with random
    # indices to reach k.
    if medoids.size < k:
        rest = np.setdiff1d(np.arange(n), medoids)
        if rest.size > 0:
            extra = rng.choice(rest, size=k - medoids.size, replace=False)
            medoids = np.concatenate([medoids, extra])
        else:
            return np.arange(n)
    for _ in range(max_iter):
        assignments = D[medoids].argmin(axis=0)
        moved = False
        new_medoids = medoids.copy()
        for cluster_idx in range(k):
            members = np.where(assignments == cluster_idx)[0]
            if members.size == 0:
                continue
            sub = D[np.ix_(members, members)]
            costs = sub.sum(axis=1)
            new = members[costs.argmin()]
            if new != medoids[cluster_idx]:
                new_medoids[cluster_idx] = new
                moved = True
        medoids = new_medoids
        if not moved:
            break
    return medoids


def _zscore_columns(X: np.ndarray) -> np.ndarray:
    """Standardise to zero mean / unit SD per column. Zero-variance columns
    are returned as zeros (avoids div-by-zero on degenerate cells).
    """
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma_safe = np.where(sigma < 1e-9, 1.0, sigma)
    return (X - mu) / sigma_safe


def _allocate_k_per_cell(cell_counts: Dict[Tuple[str, str, int], int],
                          target: int) -> Dict[Tuple[str, str, int], int]:
    """Largest-remainder allocation of `target` medoids across cells in
    proportion to population. Every non-empty cell with at least one meal
    is guaranteed >= 1 medoid; remaining medoids go to the cells with the
    largest fractional shares first. The total is exactly `target`.
    """
    pop_total = sum(cell_counts.values())
    # Floor allocation
    floors: Dict[Tuple[str, str, int], int] = {}
    remainders: List[Tuple[float, Tuple[str, str, int]]] = []
    for cell, n in cell_counts.items():
        if n == 0:
            continue
        raw = target * n / pop_total
        # Reserve at least 1 medoid per cell, since even small strata
        # carry signal we want represented in the panel.
        floor = max(1, int(raw))
        floors[cell] = floor
        remainders.append((raw - floor, cell))
    total_assigned = sum(floors.values())
    surplus = target - total_assigned
    # If surplus < 0 we over-allocated due to the per-cell minimum;
    # peel back from the largest cells.
    if surplus < 0:
        # Sort cells with floor > 1 by floor (largest first) and decrement
        decrementable = sorted(
            ((c, k) for c, k in floors.items() if k > 1),
            key=lambda x: -x[1],
        )
        i = 0
        while surplus < 0 and i < len(decrementable):
            cell = decrementable[i][0]
            floors[cell] -= 1
            surplus += 1
            i = (i + 1) % len(decrementable)
            if i == 0 and surplus < 0:
                # Cycle again from the top
                decrementable = sorted(
                    ((c, k) for c, k in floors.items() if k > 1),
                    key=lambda x: -x[1],
                )
    elif surplus > 0:
        # Distribute the surplus to the largest fractional remainders.
        remainders.sort(reverse=True)
        for _frac, cell in remainders[:surplus]:
            floors[cell] = floors.get(cell, 0) + 1
    return floors


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')
    logger.info('Loading day pool from %s', _INPUT)
    with open(_INPUT, 'r', encoding='utf-8') as f:
        pool = json.load(f)
    meals = pool['days']
    logger.info('Day pool size: %d', len(meals))

    # Group days by stratum cell (agesex x FIPR; day-level, no occasion)
    cells: Dict[Tuple[str, int], List[int]] = {}
    for idx, m in enumerate(meals):
        key = (m['agesex_group'], m['fipr_quintile'])
        cells.setdefault(key, []).append(idx)
    cell_counts = {k: len(v) for k, v in cells.items()}
    logger.info('Stratum cells: %d', len(cells))

    # Allocate medoid budget across cells
    k_alloc = _allocate_k_per_cell(cell_counts, _TARGET_PANEL_SIZE)
    total_k = sum(k_alloc.values())
    logger.info('Total medoids after allocation: %d (target %d)',
                total_k, _TARGET_PANEL_SIZE)

    # Run PAM inside each cell. Features are z-scored within the cell so
    # the distance metric isn't dominated by absolute kcal scale; the
    # cell-level standardisation also keeps small cells well-behaved.
    rng = np.random.default_rng(_RANDOM_STATE)
    chosen: List[Dict] = []
    for cell, indices in cells.items():
        k = k_alloc.get(cell, 0)
        if k == 0:
            continue
        n_cell = len(indices)
        if n_cell <= k:
            # Cell smaller than allocation; use every meal.
            chosen_indices = indices
        else:
            X_cell = np.array([_features_for_meal(meals[i]) for i in indices])
            X_z = _zscore_columns(X_cell)
            try:
                medoid_local_idx = _pam_alternate(X_z, k=k, seed=_RANDOM_STATE)
            except Exception as exc:
                logger.warning('PAM failed for cell %s (n=%d, k=%d): %r',
                               cell, n_cell, k, exc)
                medoid_local_idx = rng.choice(n_cell, size=k, replace=False)
            chosen_indices = [indices[i] for i in medoid_local_idx]

        for local_i, pool_idx in enumerate(chosen_indices):
            src = meals[pool_idx]
            chosen.append({
                'day_id': f'S4-{len(chosen) + 1:03d}',
                'seqn': src['seqn'],
                'stratum': (
                    f'{src["agesex_group"]}|q{src["fipr_quintile"]}'
                ),
                'agesex_group': src['agesex_group'],
                'age_years': src['age_years'],
                'sex': src['sex'],
                'fipr_quintile': src['fipr_quintile'],
                'occasion_mix': src.get('occasion_mix', ''),
                'mass_coverage': src['mass_coverage'],
                'foods': src['foods'],
                'cluster_size_in_cell': n_cell,
                'medoid_rank_in_cell': local_i,
                'macros_nhanes_self_reported': src['macros_nhanes_self_reported'],
                'rationale': (
                    f'NHANES 2017-2018 day medoid; PAM cluster centre in '
                    f'{src["agesex_group"]} / FIPR q{src["fipr_quintile"]} '
                    f'stratum (n={n_cell} pool days; k={k} medoids).'
                ),
            })

    logger.info('S4 panel: %d medoid meals selected', len(chosen))
    if len(chosen) != _TARGET_PANEL_SIZE:
        logger.warning('Panel size mismatch: got %d, expected %d',
                       len(chosen), _TARGET_PANEL_SIZE)

    # Per-stratum coverage summary
    by_agesex = Counter(m['agesex_group'] for m in chosen)
    by_occasion = Counter(m.get('occasion_mix', '') for m in chosen)
    by_fipr = Counter(m['fipr_quintile'] for m in chosen)
    logger.info('Coverage: agesex=%s  occasion=%s  fipr=%s',
                dict(by_agesex), dict(by_occasion), dict(by_fipr))

    out = {
        '_provenance': {
            'source': pool['_provenance'],
            'clustering_method': 'PAM ("alternate" method, k-means++ '
                                 'seeding, pure-numpy / scipy implementation '
                                 '_pam_alternate; matches scikit-learn-extra '
                                 'KMedoids(method="alternate") behaviour); '
                                 'per-cell z-scored features',
            'feature_vector': [
                'kcal_total', 'protein_pct_kcal', 'fat_pct_kcal',
                'carb_pct_kcal', 'sugar_pct_kcal', 'sat_fat_pct_kcal',
                'sodium_mg_per_100kcal', 'fibre_g_per_100kcal',
            ],
            'random_state': _RANDOM_STATE,
            'target_panel_size': _TARGET_PANEL_SIZE,
        },
        'allocation_summary': {
            'n_cells_non_empty': sum(1 for v in cell_counts.values() if v > 0),
            'n_cells_used': sum(1 for v in k_alloc.values() if v > 0),
            'by_agesex_group': dict(by_agesex),
            'by_meal_occasion': dict(by_occasion),
            'by_fipr_quintile': dict(by_fipr),
            'pool_total': sum(cell_counts.values()),
            'panel_total': len(chosen),
        },
        'meals': chosen,
    }
    with open(_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    logger.info('Wrote %s', _OUTPUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
