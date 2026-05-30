"""Monte Carlo uncertainty propagation over LCA characterisation factors.

Closes TODO-CODE-LCA-3. The existing pipeline ships a deterministic
low / central / high band per (CNF food group, midpoint category) sourced
from Poore & Nemecek (2018) between-producer variability and Mekonnen &
Hoekstra (2011, 2012) spatial spread (see
`UNCERTAINTY_BAND_RATIOS_BY_GROUP` in cnf_integrator.py). Until now the
bands were propagated as an "everything-low" versus "everything-high"
envelope, which over-states correlated variance and under-states
distributional shape. This module replaces that with a parametric Monte
Carlo sampler over log-normal characterisation-factor distributions
parameterised from the same P&N anchors, returning 5 / 50 / 95
percentile bands per midpoint per meal.

Distribution choice. Poore & Nemecek 2018 Fig 1 reports between-producer
spread as heavily right-skewed (median below mean, long upper tail), which
the log-normal family captures naturally. For each (food, category) we
parameterise log-normal by:

  central = published P&N panel mean (or the cnf_integrator derived central
            value) used as the median anchor
  L       = central * low_ratio                          (5th-percentile proxy)
  H       = central * high_ratio                         (95th-percentile proxy)
  mu      = ln(central)
  sigma   = (ln(H) - ln(L)) / (2 * z_0.95)               with z_0.95 = 1.645

so the sampled CF distribution has median = central and a 90 percent
interval that matches the published band. We sample CFs independently
per (food, midpoint) to avoid imposing a correlation structure we cannot
defend from the panel data; reviewers can argue for a single correlated
draw per food group via the same machinery by introducing a per-group
covariance matrix at the parameter file later.

Output. For each midpoint category in the v1 trim ({Global warming,
Land use, Water consumption}), the runner returns the meal-level
5 / 50 / 95 percentiles plus the sampled distribution mean and standard
deviation. The five-point summary is appended to the API response under
`midpoint_impacts_montecarlo` alongside the existing
`midpoint_impacts_bands` envelope, so reviewers can compare the
distributional reading to the deterministic envelope.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# z-score at the 95th percentile of the standard normal; used to convert a
# 5-to-95 band into a log-normal sigma. (qnorm(0.95) = 1.6449...)
_Z_95 = 1.6449


def _lognormal_params_from_band(
    central: float, low: float, high: float,
) -> Optional[Tuple[float, float]]:
    """Solve for log-normal (mu, sigma) given the median and a 5-to-95 band.

    Returns None if the band is degenerate (central or bounds non-positive,
    or low >= high), in which case the sampler falls back to a delta at
    the central value.
    """
    if central <= 0 or low <= 0 or high <= 0:
        return None
    if high <= low:
        return None
    mu = math.log(central)
    sigma = (math.log(high) - math.log(low)) / (2.0 * _Z_95)
    if sigma <= 0 or not math.isfinite(sigma):
        return None
    return mu, sigma


def sample_meal_midpoint_impacts(
    food_contributions: List[Dict[str, Any]],
    *,
    n_samples: int = 1000,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """Monte Carlo over per-food per-category log-normal CFs.

    Each entry of `food_contributions` is a dict with at least:
        {
          'food_id': int,
          'serving_g': float,
          'central_impacts': {category: per_serving_central_value, ...},
          'low_impacts':      {category: per_serving_low_value, ...},
          'high_impacts':     {category: per_serving_high_value, ...},
        }

    The sampler draws a log-normal CF per food per category from the
    parameters implied by (central, low, high), sums across foods to a
    meal-level value, and returns 5 / 50 / 95 percentiles plus sample
    mean and sample standard deviation per category.
    """
    rng = np.random.default_rng(seed)
    if not food_contributions:
        return {}
    # Gather the set of categories that appear on any food.
    categories: List[str] = sorted({
        k for fc in food_contributions for k in fc.get('central_impacts', {})
    })
    if not categories:
        return {}

    out: Dict[str, Dict[str, float]] = {}
    for cat in categories:
        # Build per-food sample arrays of shape (n_samples,) and sum.
        meal_samples = np.zeros(n_samples)
        for fc in food_contributions:
            central = float(fc.get('central_impacts', {}).get(cat, 0.0) or 0.0)
            low = float(fc.get('low_impacts', {}).get(cat, 0.0) or 0.0)
            high = float(fc.get('high_impacts', {}).get(cat, 0.0) or 0.0)
            if central <= 0:
                continue
            params = _lognormal_params_from_band(central, low, high)
            if params is None:
                meal_samples += central
                continue
            mu, sigma = params
            draws = rng.lognormal(mean=mu, sigma=sigma, size=n_samples)
            meal_samples += draws
        meal_samples_sorted = np.sort(meal_samples)
        p5 = float(np.percentile(meal_samples_sorted, 5))
        p50 = float(np.percentile(meal_samples_sorted, 50))
        p95 = float(np.percentile(meal_samples_sorted, 95))
        out[cat] = {
            'p5': p5,
            'p50': p50,
            'p95': p95,
            'mean': float(meal_samples.mean()),
            'sd': float(meal_samples.std(ddof=1)) if n_samples > 1 else 0.0,
            'n_samples': n_samples,
        }
    return out


def build_food_contributions_from_lca(
    lca, *, basis: str = 'per_serving',
) -> List[Dict[str, Any]]:
    """Reshape a populated `LifeCycleAssessment` instance into the
    food-contributions list the Monte Carlo sampler consumes.

    The LCA's existing `_food_impacts_cache` carries per-food central and
    band values keyed by category; we pull both. The deterministic band
    triples become the (low, central, high) anchors for the log-normal.
    """
    contributions: List[Dict[str, Any]] = []
    cache = getattr(lca, '_food_impacts_cache', {}) or {}
    for food_id, impact_dict in cache.items():
        if not isinstance(impact_dict, dict):
            continue
        central = {}
        low = {}
        high = {}
        # impact_dict shape: {category: {'central': x, 'low': y, 'high': z}}
        # or {category: float} for the deterministic-only path.
        for cat, val in impact_dict.items():
            if isinstance(val, dict):
                central[cat] = float(val.get('central', val.get('value', 0.0)) or 0.0)
                low[cat] = float(val.get('low', central[cat]) or central[cat])
                high[cat] = float(val.get('high', central[cat]) or central[cat])
            elif isinstance(val, (int, float)):
                central[cat] = float(val)
                low[cat] = float(val)
                high[cat] = float(val)
        contributions.append({
            'food_id': food_id,
            'central_impacts': central,
            'low_impacts': low,
            'high_impacts': high,
        })
    return contributions
