"""Improve-plan orchestration — recall composition → baseline scorecard → swaps.

Combines recall-history aggregation, full six-metric baseline scoring,
priority-ingredient targeting, and SUBST-1 substitution analysis into one
response suitable for a "what should I change?" user flow.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set

from api.services.substitution_analyzer import (
    _normalize_composition,
    analyze_substitutions,
)
from api.services.substitution_pareto import compute_pareto_frontier
from api.services.substitution_rules import (
    SUBSTITUTION_RULES,
    ingredient_matches_rule,
)
from api.services.substitution_scorecard import (
    SCORECARD_METRICS_FULL,
    enrich_scorecard_deltas,
    score_composition,
)
from api.views.hefi_explanations import _POPULATION_BENCHMARKS, _band_phrase, _score_band

logger = logging.getLogger(__name__)

IMPROVE_PLAN_PARETO_AXES = ('hefi', 'heni', 'fcs', 'environmental')

_SUGARY_DRINK_KEYWORDS = (
    'juice', 'nectar', 'cola', 'soda', 'soft drink', 'punch', 'lemonade',
)
_REFINED_GRAIN_KEYWORDS = (
    'white, long-grain', 'white rice', 'white bread', 'refined',
)


def combine_recall_days(
    days: List[Dict[str, Any]],
    *,
    day_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Mass-sum ingredients across recall days (matches frontend ``combineDays``)."""
    if not days:
        raise ValueError('recall_export.days must be a non-empty list')

    allowed: Optional[Set[str]] = set(day_ids) if day_ids else None
    by_food: Dict[int, Dict[str, Any]] = {}

    for day in days:
        if allowed is not None and day.get('id') not in allowed:
            continue
        for ing in day.get('aggregated_daily_ingredients') or []:
            fid = int(ing['food_id'])
            mass = float(ing['mass_g'])
            if fid in by_food:
                by_food[fid]['mass_g'] += mass
            else:
                by_food[fid] = {
                    'food_id': fid,
                    'mass_g': mass,
                    'food_description': ing.get('food_description', ''),
                    'food_group': ing.get('food_group', ''),
                }

    if not by_food:
        raise ValueError('No recall days matched day_ids filter')

    return sorted(by_food.values(), key=lambda r: r['mass_g'], reverse=True)


def _composition_from_request(
    *,
    composition: Optional[List[Dict[str, Any]]],
    recall_export: Optional[Dict[str, Any]],
    day_ids: Optional[List[str]],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    meta: Dict[str, Any] = {'source': 'composition', 'days_used': []}

    if composition:
        rows = list(composition)
        return rows, meta

    if recall_export and isinstance(recall_export.get('days'), list):
        days = recall_export['days']
        if day_ids:
            meta['days_used'] = [d.get('id') for d in days if d.get('id') in day_ids]
        else:
            meta['days_used'] = [d.get('id') for d in days]
        meta['source'] = 'recall_export'
        meta['day_count'] = len(meta['days_used'])
        meta['export_version'] = recall_export.get('version')
        rows = combine_recall_days(days, day_ids=day_ids)
        return rows, meta

    raise ValueError(
        "Provide either 'composition' or 'recall_export' with aggregated recall days",
    )


def _swap_eligible(ing: Dict[str, Any]) -> Optional[str]:
    for rule in SUBSTITUTION_RULES:
        if ingredient_matches_rule(
            food_id=ing['food_id'],
            food_description=ing.get('food_description', ''),
            food_group=ing.get('food_group', ''),
            food_group_id=ing.get('food_group_id'),
            rule=rule,
        ):
            return rule.id
    return None


def _improvement_flags(description: str, food_group: str) -> List[str]:
    desc = (description or '').lower()
    group = (food_group or '').lower()
    flags: List[str] = []
    if any(k in desc for k in _SUGARY_DRINK_KEYWORDS):
        flags.append('sugary_drink')
    if any(k in desc for k in _REFINED_GRAIN_KEYWORDS):
        flags.append('refined_grain')
    if 'beef' in group or 'beef' in desc:
        flags.append('red_meat')
    if 'poultry' in group:
        flags.append('poultry')
    if food_group.startswith('WAFCT'):
        flags.append('wafct')
    return flags


def rank_priority_ingredients(
    composition: List[Dict[str, Any]],
    *,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """Rank ingredients most worth targeting for swaps."""
    rows = _normalize_composition(composition)
    total_mass = sum(r['mass_g'] for r in rows) or 1.0
    ranked: List[Dict[str, Any]] = []

    for idx, ing in enumerate(rows):
        rule_id = _swap_eligible(ing)
        flags = _improvement_flags(ing['food_description'], ing['food_group'])
        mass_pct = round(100.0 * ing['mass_g'] / total_mass, 1)
        priority = 0.0
        if rule_id:
            priority += 40.0
        priority += min(mass_pct, 30.0)
        if 'sugary_drink' in flags:
            priority += 25.0
        if 'refined_grain' in flags:
            priority += 15.0
        if 'red_meat' in flags:
            priority += 20.0

        ranked.append({
            'ingredient_index': idx,
            'food_id': ing['food_id'],
            'food_description': ing['food_description'],
            'food_group': ing['food_group'],
            'mass_g': ing['mass_g'],
            'mass_pct': mass_pct,
            'swap_rule_id': rule_id,
            'flags': flags,
            'priority_score': round(priority, 1),
        })

    ranked.sort(key=lambda x: x['priority_score'], reverse=True)
    return ranked[:limit]


def _population_context(baseline_scorecard: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    hefi = baseline_scorecard.get('hefi') or {}
    value = hefi.get('value')
    if value is None:
        return None
    score = float(value)
    band = _score_band(score)
    return {
        'hefi': {
            'value': score,
            'max': 80.0,
            'band': band,
            'band_phrase': _band_phrase(band),
            'canadian_population': dict(_POPULATION_BENCHMARKS),
            'caveat': (
                'Single-day HEFI is not usual intake; compare directionally only '
                'unless you averaged multiple recall days.'
            ),
        },
    }


def _attach_full_scorecards(
    baseline_rows: List[Dict[str, Any]],
    baseline_sc: Dict[str, Any],
    suggestions: List[Dict[str, Any]],
) -> None:
    for s in suggestions:
        mod_rows = _normalize_composition(s['modified_composition'])
        s['scorecard_full'] = enrich_scorecard_deltas(
            baseline_rows, mod_rows, baseline_sc=baseline_sc, full=True,
        )


def build_improve_plan(
    *,
    composition: Optional[List[Dict[str, Any]]] = None,
    recall_export: Optional[Dict[str, Any]] = None,
    day_ids: Optional[List[str]] = None,
    purpose: str = 'general_health',
    max_suggestions: int = 5,
    max_swaps: int = 3,
    reformulation_mode: str = 'greedy',
    include_population_benchmark: bool = True,
    dish_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Orchestrate baseline scoring, priority targets, and substitution suggestions."""
    t0 = time.perf_counter()
    raw_rows, input_meta = _composition_from_request(
        composition=composition,
        recall_export=recall_export,
        day_ids=day_ids,
    )
    rows = _normalize_composition(raw_rows)
    total_mass = sum(r['mass_g'] for r in rows)

    baseline_sc = score_composition(rows, full=True)
    priority_targets = rank_priority_ingredients(rows)

    constraints = {'max_swaps': max(1, min(int(max_swaps), 4))}
    analysis = analyze_substitutions(
        rows,
        purpose=purpose,
        max_suggestions=max(1, min(int(max_suggestions), 10)),
        constraints=constraints,
        include_scorecard=False,
        dish_name=dish_name,
        reformulation_mode=reformulation_mode,
    )

    suggestions = analysis.get('suggestions') or []
    _attach_full_scorecards(rows, baseline_sc, suggestions)
    pareto_frontier = compute_pareto_frontier(
        suggestions,
        axes=IMPROVE_PLAN_PARETO_AXES,
    )

    population = (
        _population_context(baseline_sc)
        if include_population_benchmark
        else None
    )

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    summary_lines: List[str] = []
    hefi_val = (baseline_sc.get('hefi') or {}).get('value')
    if hefi_val is not None and population:
        summary_lines.append(
            f"Baseline HEFI {hefi_val:.1f}/80 — {population['hefi']['band_phrase']}.",
        )
    if priority_targets:
        top = priority_targets[0]
        summary_lines.append(
            f"Highest-priority swap target: {top['food_description']} "
            f"({top['mass_pct']}% of total mass).",
        )
    if suggestions:
        summary_lines.append(
            f"{len(suggestions)} ranked improvement option(s); "
            f"{len(pareto_frontier)} on the health–environment Pareto frontier.",
        )

    return {
        'success': True,
        'purpose': purpose,
        'input': input_meta,
        'baseline': {
            'composition': rows,
            'total_mass_g': round(total_mass, 1),
            'ingredient_count': len(rows),
            'scorecard': baseline_sc,
            'population_context': population,
        },
        'priority_targets': priority_targets,
        'suggestions': suggestions,
        'pareto_frontier': pareto_frontier,
        'summary': ' '.join(summary_lines),
        'metadata': {
            'endpoint': 'improve-plan',
            'scorecard_metrics': list(SCORECARD_METRICS_FULL),
            'pareto_axes': list(IMPROVE_PLAN_PARETO_AXES),
            'reformulation_mode': reformulation_mode,
            'constraints': constraints,
            'substitution_metadata': analysis.get('metadata'),
            'elapsed_ms': elapsed_ms,
        },
    }
