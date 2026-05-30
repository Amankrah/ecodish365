"""Compute per-100 g nutrient distortion between an expected CNF match and the
returned match. Used by the prep-state lab probes to quantify *how wrong* a
matcher pick is in nutrient units, not just match counts.

A wrong-prep match like "Carrot, raw" (FoodID 2380) instead of
"Carrot, boiled, drained, with salt" (FoodID 6396) reports:
  kcal_per_100g          41  →   35    Δ  -6 kcal  (-15%)
  sodium_mg_per_100g     69  →  302    Δ +233 mg  (+338%)
  vitamin_c_mg_per_100g 5.9  →  3.6    Δ -2.3 mg  (-39%)

This is the actual user-facing harm — it feeds straight into FCS sodium scoring,
HEFI sodium guideline, HSR baseline-points, and the substitution endpoint's
"lower_sodium" suggestion logic. Without this helper we'd only know the matcher
got the wrong FoodID; with it we know the score-grade impact.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional


# Canonical CNF NutrientName strings (from raw_cnf/NUTRIENT_NAME.csv).
NUTRIENT_KEYS = {
    'kcal': 'ENERGY (KILOCALORIES)',
    'sodium_mg': 'SODIUM',
    'vitamin_c_mg': 'VITAMIN C',
    'sat_fat_g': 'FATTY ACIDS, SATURATED, TOTAL',
    'fibre_g': 'FIBRE, TOTAL DIETARY',
}


@dataclass(frozen=True)
class NutrientPoint:
    expected_per_100g: Optional[float]
    returned_per_100g: Optional[float]
    delta_abs: Optional[float]            # returned − expected
    delta_pct: Optional[float]            # delta / expected (None if expected is 0 or absent)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class NutrientDelta:
    expected_food_id: int
    returned_food_id: int
    kcal: NutrientPoint
    sodium_mg: NutrientPoint
    vitamin_c_mg: NutrientPoint
    sat_fat_g: NutrientPoint
    fibre_g: NutrientPoint

    def as_dict(self) -> dict:
        return {
            'expected_food_id': self.expected_food_id,
            'returned_food_id': self.returned_food_id,
            'kcal': self.kcal.as_dict(),
            'sodium_mg': self.sodium_mg.as_dict(),
            'vitamin_c_mg': self.vitamin_c_mg.as_dict(),
            'sat_fat_g': self.sat_fat_g.as_dict(),
            'fibre_g': self.fibre_g.as_dict(),
        }


def _point(expected: Optional[float], returned: Optional[float]) -> NutrientPoint:
    if expected is None or returned is None:
        return NutrientPoint(expected, returned, None, None)
    delta_abs = returned - expected
    if expected == 0:
        delta_pct = None
    else:
        delta_pct = delta_abs / expected
    return NutrientPoint(expected, returned, delta_abs, delta_pct)


def _get_nutrient(nutrients: Dict[str, float], key: str) -> Optional[float]:
    if not nutrients:
        return None
    v = nutrients.get(key)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compute_nutrient_delta(expected_food_id: int, returned_food_id: int) -> Optional[NutrientDelta]:
    """Per-100 g nutrient deltas between two CNF FoodIDs.

    Returns None when either food can't be resolved (caller should treat as
    "no data, skip"). Otherwise returns a NutrientDelta with 5 per-nutrient
    points; each point's delta_abs / delta_pct may still be None if the
    underlying nutrient isn't reported in the CNF row.

    Designed for in-process lab use only — assumes the api.cnf_cache pipeline
    is already initialised by django.setup().
    """
    # Lazy import — keeps this module importable without Django.
    from api.cnf_cache import get_api_cnf_pipeline
    pipe = get_api_cnf_pipeline()

    expected_nutr = pipe.nutrients_for(int(expected_food_id))
    returned_nutr = pipe.nutrients_for(int(returned_food_id))
    if not expected_nutr and not returned_nutr:
        return None

    return NutrientDelta(
        expected_food_id=int(expected_food_id),
        returned_food_id=int(returned_food_id),
        kcal=_point(
            _get_nutrient(expected_nutr, NUTRIENT_KEYS['kcal']),
            _get_nutrient(returned_nutr, NUTRIENT_KEYS['kcal']),
        ),
        sodium_mg=_point(
            _get_nutrient(expected_nutr, NUTRIENT_KEYS['sodium_mg']),
            _get_nutrient(returned_nutr, NUTRIENT_KEYS['sodium_mg']),
        ),
        vitamin_c_mg=_point(
            _get_nutrient(expected_nutr, NUTRIENT_KEYS['vitamin_c_mg']),
            _get_nutrient(returned_nutr, NUTRIENT_KEYS['vitamin_c_mg']),
        ),
        sat_fat_g=_point(
            _get_nutrient(expected_nutr, NUTRIENT_KEYS['sat_fat_g']),
            _get_nutrient(returned_nutr, NUTRIENT_KEYS['sat_fat_g']),
        ),
        fibre_g=_point(
            _get_nutrient(expected_nutr, NUTRIENT_KEYS['fibre_g']),
            _get_nutrient(returned_nutr, NUTRIENT_KEYS['fibre_g']),
        ),
    )


def summarise_distortion(deltas: list) -> dict:
    """Aggregate stats across multiple NutrientDelta records.

    For each nutrient axis, reports the mean of |delta_abs| and |delta_pct|
    (treating missing as 0 for the count denominator) — the bigger these are,
    the more damaging the wrong-prep matches are to downstream scoring.

    deltas: list of NutrientDelta records (or None — None entries skipped).
    """
    valid = [d for d in deltas if d is not None]
    n = len(valid)
    if n == 0:
        return {'n': 0}
    keys = ('kcal', 'sodium_mg', 'vitamin_c_mg', 'sat_fat_g', 'fibre_g')
    out = {'n': n}
    for k in keys:
        abs_sum, abs_count = 0.0, 0
        pct_sum, pct_count = 0.0, 0
        for d in valid:
            p = getattr(d, k)
            if p.delta_abs is not None:
                abs_sum += abs(p.delta_abs)
                abs_count += 1
            if p.delta_pct is not None:
                pct_sum += abs(p.delta_pct)
                pct_count += 1
        out[k] = {
            'mean_abs_delta': round(abs_sum / abs_count, 2) if abs_count else None,
            'mean_abs_pct_delta': round(pct_sum / pct_count * 100, 1) if pct_count else None,
            'n_abs': abs_count,
            'n_pct': pct_count,
        }
    return out
