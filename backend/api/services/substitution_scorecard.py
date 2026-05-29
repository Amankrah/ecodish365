"""Full six-metric scorecard for SUBST-1 Phase 3 substitution deltas."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from api.services.substitution_discovery import sustainability_proxy_score

logger = logging.getLogger(__name__)

# Substitution scoring is FCS-only: the per-candidate hot loop dominated
# wall-clock at ~145 s/request (nginx 504s). HEFI/HENI/HSR/LCA/dietary_pattern
# scorers were retained in this module (still callable via _SCORERS_FULL) but
# the substitution path no longer invokes them. To re-enable for substitution,
# add the keys back to SCORECARD_METRICS and _SCORERS.
SCORECARD_METRICS = ('fcs',)


def _composition_foods(composition: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{'food_id': r['food_id'], 'mass_g': r['mass_g']} for r in composition]


def _score_hefi(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from hefi_calculator.hefi.models import HEFIInputs
    from hefi_calculator.hefi.algorithm import compute_hefi
    from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
    from django.conf import settings

    food_data = [(r['food_id'], r['mass_g']) for r in composition]
    integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
    agg = integrator.aggregate_inputs(food_data)
    result = compute_hefi(HEFIInputs(**agg))
    return {'value': float(result.total_score), 'unit': 'points', 'max': 80.0}


def _score_fcs(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from fcs_calculator.fcs.service import extract_and_score

    ids = [r['food_id'] for r in composition]
    amounts = [r['mass_g'] for r in composition]
    _, summary = extract_and_score(ids, 'scorecard', amounts_g=amounts)
    return {
        'value': float(summary.get('fcs', 0.0)),
        'unit': 'points',
        'max': 100.0,
        'nova_category': summary.get('nova_category'),
    }


def _score_heni(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from heni_calculator.heni.service import (
        calculate_meal_heni_response,
        meal_api_rows_to_ingredients,
    )

    meal = [{'food_id': r['food_id'], 'amount': r['mass_g'], 'unit': 'g'} for r in composition]
    ingredients = meal_api_rows_to_ingredients(meal)
    resp = calculate_meal_heni_response(ingredients)
    scores = resp.get('heni_scores') or {}
    # Negative minutes = health gain; we expose raw minutes for delta interpretation.
    minutes = float(scores.get('health_impact_minutes', scores.get('total_heni_score', 0.0)))
    return {'value': minutes, 'unit': 'minutes', 'invert': True}


def _score_hsr(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from api.views.hsr_views_consolidated import (
        _build_per_food_ratings,
        _summarise_per_food_ratings,
    )

    ids = [r['food_id'] for r in composition]
    sizes = [r['mass_g'] for r in composition]
    ratings = _build_per_food_ratings(ids, sizes)
    summary = _summarise_per_food_ratings(ratings)
    if not summary.get('available'):
        return {'value': 0.0, 'unit': 'stars', 'max': 5.0, 'available': False}
    return {
        'value': float(summary.get('energy_weighted_avg', 0.0)),
        'unit': 'stars',
        'max': 5.0,
        'available': True,
    }


def _score_environmental(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
        from environmental_impact_model.src.meal import Food as EnvFood, Meal as EnvMeal
        from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment

        loader = EnvDataLoader()
        foods = [
            EnvFood(food_id=r['food_id'], quantity=r['mass_g'], data_loader=loader)
            for r in composition
        ]
        meal = EnvMeal(foods)
        lca = LifeCycleAssessment(
            meal, methodology='recipe2016', perspective='H', basis='per_100_kcal',
        )
        lca.perform_lcia()
        single = float(lca.calculate_single_score())
        return {'value': single, 'unit': 'LCA points', 'invert': True, 'proxy': False}
    except Exception as exc:  # noqa: BLE001
        logger.debug('LCA score fallback to proxy: %s', exc)
        proxy = sustainability_proxy_score(composition)
        return {'value': proxy, 'unit': 'proxy', 'invert': True, 'proxy': True}


def _score_dietary_pattern(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from api.services.dietary_pattern import get_default_pattern_matcher

    foods = [{'food_id': r['food_id'], 'mass_g': r['mass_g']} for r in composition]
    matcher = get_default_pattern_matcher()
    result = matcher.classify(foods, include_distinctive_foods=False)
    top_id = result.top_pattern
    top_label = None
    if result.resemblances:
        for r in result.resemblances:
            if r.pattern_id == top_id:
                top_label = r.display_name
                break
    return {
        'value': float(result.resemblances[0].cosine) if result.resemblances else 0.0,
        'unit': 'cosine',
        'top_pattern_id': top_id,
        'top_pattern_label': top_label,
    }


# Full scorer registry — preserved so a future caller can opt back in by
# referencing _SCORERS_FULL instead of _SCORERS.
_SCORERS_FULL = {
    'hefi': _score_hefi,
    'fcs': _score_fcs,
    'heni': _score_heni,
    'hsr': _score_hsr,
    'environmental': _score_environmental,
    'dietary_pattern': _score_dietary_pattern,
}

# Active scorers for substitution. Must match SCORECARD_METRICS.
_SCORERS = {'fcs': _score_fcs}


def score_composition(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score all six metrics for a composition. Partial failures are captured per metric."""
    out: Dict[str, Any] = {}
    for key, fn in _SCORERS.items():
        try:
            out[key] = fn(composition)
        except Exception as exc:  # noqa: BLE001
            logger.warning('Scorecard metric %s failed: %s', key, exc)
            out[key] = {'value': None, 'error': str(exc)}
    return out


def _metric_delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    b = before.get('value')
    a = after.get('value')
    if b is None or a is None:
        return {'before': b, 'after': a, 'delta': None, 'improved': None}
    diff = round(float(a) - float(b), 4)
    invert = bool(before.get('invert') or after.get('invert'))
    improved = (diff < 0) if invert else (diff > 0)
    if abs(diff) < 1e-6:
        improved = None
    return {'before': b, 'after': a, 'delta': diff, 'improved': improved}


def scorecard_deltas(
    baseline: Dict[str, Any],
    modified: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    deltas = {}
    for key in SCORECARD_METRICS:
        deltas[key] = _metric_delta(baseline.get(key, {}), modified.get(key, {}))
    return deltas


def enrich_scorecard_deltas(
    baseline_composition: List[Dict[str, Any]],
    modified_composition: List[Dict[str, Any]],
    baseline_sc: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Score the modified composition and diff it against the baseline.

    `baseline_sc` lets callers pass a baseline scorecard computed once and reused
    across many suggestions, instead of re-scoring the (unchanged) baseline on every
    call. The result is identical either way.
    """
    if baseline_sc is None:
        baseline_sc = score_composition(baseline_composition)
    modified_sc = score_composition(modified_composition)
    return {
        'baseline': baseline_sc,
        'modified': modified_sc,
        'deltas': scorecard_deltas(baseline_sc, modified_sc),
    }
