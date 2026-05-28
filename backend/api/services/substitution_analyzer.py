"""Ingredient substitution analyzer — SUBST-1 Phases 1–4."""
from __future__ import annotations

import copy
import itertools
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Set, Tuple

from api.cnf_cache import get_api_cnf_pipeline, get_dish_cnf_pipeline
from api.services.substitution_constraints import (
    parse_extended_constraints,
    replacement_allowed,
)
from api.services.substitution_culinary import culinary_swap_plausible, extreme_nutrient_swing
from api.services.substitution_quality import swap_passes_quality_gate
from api.services.substitution_fped_ranking import fped_gap_fill_bonus
from api.services.substitution_discovery import (
    discover_candidates_for_ingredient,
    sustainability_proxy_score,
)
from api.services.substitution_pareto import compute_pareto_frontier
from api.services.substitution_rules import (
    PURPOSE_LABELS,
    SubstitutionRule,
    ingredient_matches_rule,
    rules_for_purpose,
)
from api.services.wafct_recipes import recipe_swap_candidates
from api.services.substitution_scorecard import enrich_scorecard_deltas, score_composition

logger = logging.getLogger(__name__)

_NUTRIENT_KEYS: Tuple[Tuple[str, str], ...] = (
    ('ENERGY (KILOCALORIES)', 'energy_kcal'),
    ('PROTEIN', 'protein_g'),
    ('FIBRE, TOTAL DIETARY', 'fibre_g'),
    ('SODIUM', 'sodium_mg'),
    ('FATTY ACIDS, SATURATED, TOTAL', 'sat_fat_g'),
    ('SUGARS, TOTAL', 'total_sugars_g'),
)

_hefi_integrator = None


def _parse_constraints(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return parse_extended_constraints(raw)


def _get_hefi_integrator():
    global _hefi_integrator
    if _hefi_integrator is None:
        from django.conf import settings
        from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
        _hefi_integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
    return _hefi_integrator


def _food_meta(food_id: int) -> Dict[str, Any]:
    pipeline = get_dish_cnf_pipeline()
    details = pipeline.get_food_details(int(food_id))
    if not details:
        return {
            'food_id': int(food_id),
            'food_description': f'Food ID {food_id}',
            'food_group': '',
            'food_group_id': None,
        }
    src = 'cnf'
    df = pipeline.data_loader.food_name_df
    row = df[df['FoodID'] == int(food_id)]
    if not row.empty:
        src = str(row.iloc[0].get('source', 'cnf') or 'cnf')
    return {
        'food_id': int(food_id),
        'food_description': details.get('FoodDescription', f'Food ID {food_id}'),
        'food_group': details.get('FoodGroupName', ''),
        'food_group_id': details.get('FoodGroupID'),
        'source': src,
    }


def _normalize_composition(composition: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not composition:
        raise ValueError('composition must be a non-empty list')

    rows: List[Dict[str, Any]] = []
    for i, raw in enumerate(composition):
        food_id = raw.get('food_id')
        mass_g = raw.get('mass_g')
        if food_id is None:
            raise ValueError(f'composition[{i}].food_id is required')
        if mass_g is None or float(mass_g) <= 0:
            raise ValueError(f'composition[{i}].mass_g must be > 0')

        meta = _food_meta(int(food_id))
        rows.append({
            'food_id': int(food_id),
            'mass_g': float(mass_g),
            'food_description': raw.get('food_description') or meta['food_description'],
            'food_group': raw.get('food_group') or meta['food_group'],
            'food_group_id': raw.get('food_group_id') if raw.get('food_group_id') is not None else meta['food_group_id'],
            'source': meta.get('source', 'cnf'),
            'label_name': raw.get('label_name'),
            'position': raw.get('position'),
        })
    return rows


def _to_food_data(composition: List[Dict[str, Any]]) -> List[Tuple[int, float]]:
    return [(r['food_id'], r['mass_g']) for r in composition]


def _score_hefi(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from hefi_calculator.hefi.models import HEFIInputs
    from hefi_calculator.hefi.algorithm import compute_hefi

    integrator = _get_hefi_integrator()
    agg = integrator.aggregate_inputs(_to_food_data(composition))
    result = compute_hefi(HEFIInputs(**agg))
    return {
        'total_score': float(result.total_score),
        'max_score': 80.0,
        'components': {
            k: float(v) for k, v in (result.components or {}).items()
        } if hasattr(result, 'components') and result.components else {},
    }


def _score_fcs(composition: List[Dict[str, Any]]) -> Dict[str, Any]:
    from fcs_calculator.fcs.service import extract_and_score

    food_ids = [r['food_id'] for r in composition]
    amounts = [r['mass_g'] for r in composition]
    _, summary = extract_and_score(food_ids, 'substitution composition', amounts_g=amounts)
    return {
        'total_score': float(summary.get('fcs', 0.0)),
        'max_score': 100.0,
        'nova_category': summary.get('nova_category'),
    }


def _aggregate_nutrients(composition: List[Dict[str, Any]]) -> Dict[str, float]:
    pipeline = get_api_cnf_pipeline()
    totals: Dict[str, float] = {key: 0.0 for _, key in _NUTRIENT_KEYS}

    for row in composition:
        mass = row['mass_g']
        nutrients = pipeline.nutrients_for(row['food_id'])
        if not nutrients:
            continue
        factor = mass / 100.0
        for cnf_name, out_key in _NUTRIENT_KEYS:
            val = nutrients.get(cnf_name)
            if val is not None:
                totals[out_key] += float(val) * factor

    return {k: round(v, 2) for k, v in totals.items()}


def _nutrient_delta(
    before: Dict[str, float],
    after: Dict[str, float],
) -> Dict[str, Dict[str, float]]:
    delta: Dict[str, Dict[str, float]] = {}
    for key in before:
        b = before.get(key, 0.0)
        a = after.get(key, 0.0)
        diff = round(a - b, 2)
        pct = round((diff / b * 100.0), 1) if b else (100.0 if a else 0.0)
        delta[key] = {'before': b, 'after': a, 'diff': diff, 'pct': pct}
    return delta


def _purpose_score(
    purpose: str,
    hefi_delta: float,
    fcs_delta: float,
    nutrient_delta: Dict[str, Dict[str, float]],
    sustainability_delta: float,
) -> float:
    if purpose == 'lower_sodium':
        return -(nutrient_delta.get('sodium_mg', {}).get('diff', 0.0))
    if purpose == 'higher_fibre':
        return nutrient_delta.get('fibre_g', {}).get('diff', 0.0)
    if purpose == 'higher_protein':
        return nutrient_delta.get('protein_g', {}).get('diff', 0.0)
    if purpose == 'lower_sat_fat':
        return -(nutrient_delta.get('sat_fat_g', {}).get('diff', 0.0))
    if purpose == 'diabetes_friendly':
        return -(nutrient_delta.get('total_sugars_g', {}).get('diff', 0.0))
    if purpose == 'sustainability':
        return -sustainability_delta
    # general_health: blend HEFI + FCS
    return hefi_delta * 0.6 + fcs_delta * 0.4


def _apply_swap_at(
    composition: List[Dict[str, Any]],
    index: int,
    target_food_id: int,
    target_description: Optional[str] = None,
) -> List[Dict[str, Any]]:
    modified = copy.deepcopy(composition)
    original = modified[index]
    meta = _food_meta(target_food_id)
    modified[index] = {
        **original,
        'food_id': target_food_id,
        'food_description': target_description or meta['food_description'],
        'food_group': meta['food_group'],
        'food_group_id': meta['food_group_id'],
        'source': meta.get('source', 'cnf'),
    }
    return modified


def _apply_swap_rule(
    composition: List[Dict[str, Any]],
    index: int,
    rule: SubstitutionRule,
) -> List[Dict[str, Any]]:
    return _apply_swap_at(
        composition, index, rule.target_food_id, rule.target_food_description,
    )


def _serialize_composition(composition: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            'food_id': r['food_id'],
            'mass_g': r['mass_g'],
            'food_description': r['food_description'],
            'food_group': r['food_group'],
            'label_name': r.get('label_name'),
            'position': r.get('position'),
        }
        for r in composition
    ]


def _evaluate_modification(
    *,
    baseline_hefi: Dict[str, Any],
    baseline_fcs: Dict[str, Any],
    baseline_nutrients: Dict[str, float],
    baseline_sustain: float,
    modified: List[Dict[str, Any]],
    purpose: str,
) -> Dict[str, Any]:
    mod_hefi = _score_hefi(modified)
    mod_fcs = _score_fcs(modified)
    mod_nutrients = _aggregate_nutrients(modified)
    mod_sustain = sustainability_proxy_score(modified)

    hefi_delta = round(mod_hefi['total_score'] - baseline_hefi['total_score'], 2)
    fcs_delta = round(mod_fcs['total_score'] - baseline_fcs['total_score'], 2)
    sustain_delta = round(mod_sustain - baseline_sustain, 3)
    nd = _nutrient_delta(baseline_nutrients, mod_nutrients)
    rank_score = _purpose_score(purpose, hefi_delta, fcs_delta, nd, sustain_delta)

    return {
        'modified_composition': modified,
        'hefi': {
            'before': baseline_hefi['total_score'],
            'after': mod_hefi['total_score'],
            'delta': hefi_delta,
        },
        'fcs': {
            'before': baseline_fcs['total_score'],
            'after': mod_fcs['total_score'],
            'delta': fcs_delta,
        },
        'sustainability_proxy': {
            'before': baseline_sustain,
            'after': mod_sustain,
            'delta': sustain_delta,
            'note': 'Group-level proxy; Phase 3 adds full LCA single-score delta.',
        },
        'nutrients': nd,
        'rank_score': rank_score,
    }


def _build_suggestion(
    *,
    suggestion_id: str,
    rule_id: str,
    suggestion_type: str,
    candidate_source: str,
    label: str,
    rationale: str,
    ingredient_indices: List[int],
    swaps: List[Dict[str, Any]],
    baseline_hefi: Dict[str, Any],
    baseline_fcs: Dict[str, Any],
    baseline_nutrients: Dict[str, float],
    baseline_sustain: float,
    modified: List[Dict[str, Any]],
    purpose: str,
    baseline_composition: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    ev = _evaluate_modification(
        baseline_hefi=baseline_hefi,
        baseline_fcs=baseline_fcs,
        baseline_nutrients=baseline_nutrients,
        baseline_sustain=baseline_sustain,
        modified=modified,
        purpose=purpose,
    )
    swapped_mass = swaps[0]['original']['mass_g'] if swaps else 0.0
    if extreme_nutrient_swing(ev['nutrients'], swapped_mass):
        return None

    fped_deltas = None
    try:
        from api.services.fped_aggregator import fped_swap_delta
        baseline_foods = [{'food_id': sw['original']['food_id'],
                           'mass_g': sw['original']['mass_g']} for sw in swaps]
        replacement_foods = [{'food_id': sw['replacement']['food_id'],
                              'mass_g': sw['replacement']['mass_g']} for sw in swaps]
        fped_deltas = fped_swap_delta(baseline_foods, replacement_foods)
    except Exception:  # noqa: BLE001
        fped_deltas = None

    if not swap_passes_quality_gate(
        ev,
        purpose=purpose,
        candidate_source=candidate_source,
        swaps=swaps,
        fped_deltas=fped_deltas,
    ):
        return None
    if ev['rank_score'] <= 0.01:
        return None

    rank_score = ev['rank_score']
    if candidate_source == 'curated_rule':
        rank_score += 10.0
    elif candidate_source == 'wafct_recipe':
        rank_score += 7.0
    elif candidate_source == 'matcher_alternative':
        rank_score += 5.0

    fped_gap_fill = None
    if baseline_composition:
        try:
            baseline_foods_full = [
                {'food_id': r['food_id'], 'mass_g': r['mass_g']}
                for r in baseline_composition
            ]
            modified_foods_full = [
                {'food_id': r['food_id'], 'mass_g': r['mass_g']}
                for r in modified
            ]
            fped_gap_fill = fped_gap_fill_bonus(baseline_foods_full, modified_foods_full)
            if fped_gap_fill.get('bonus', 0.0) > 0:
                rank_score += fped_gap_fill['bonus']
        except Exception:  # noqa: BLE001
            fped_gap_fill = None

    return {
        'id': suggestion_id,
        'rule_id': rule_id,
        'suggestion_type': suggestion_type,
        'candidate_source': candidate_source,
        'label': label,
        'rationale': rationale,
        'ingredient_index': ingredient_indices[0],
        'ingredient_indices': ingredient_indices,
        'swaps': swaps,
        'original': swaps[0]['original'],
        'replacement': swaps[0]['replacement'],
        **ev,
        'rank_score': rank_score,
        'fped_deltas': fped_deltas,
        'fped_gap_fill': fped_gap_fill,
        'modified_composition': _serialize_composition(ev['modified_composition']),
    }


def _rule_candidates(
    rows: List[Dict[str, Any]],
    purpose: str,
    constraints: Dict[str, Any],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    exclude = constraints['exclude_food_ids']
    source_filter = constraints['source_filter']

    for idx, ing in enumerate(rows):
        for rule in rules_for_purpose(purpose):
            if rule.target_food_id in exclude:
                continue
            if source_filter:
                target_src = _food_meta(rule.target_food_id).get('source', 'cnf')
                if target_src != source_filter:
                    continue
            if not ingredient_matches_rule(
                food_id=ing['food_id'],
                food_description=ing['food_description'],
                food_group=ing['food_group'],
                food_group_id=ing.get('food_group_id'),
                rule=rule,
            ):
                continue
            if not replacement_allowed(
                replacement_food_id=rule.target_food_id,
                replacement_description=rule.target_food_description,
                replacement_group_id=_food_meta(rule.target_food_id).get('food_group_id'),
                original_group_id=ing.get('food_group_id'),
                original_description=ing['food_description'],
                constraints=constraints,
            ):
                continue
            if not culinary_swap_plausible(
                ing['food_description'],
                rule.target_food_description,
                original_mass_g=ing['mass_g'],
            ):
                continue
            modified = _apply_swap_rule(rows, idx, rule)
            out.append({
                'suggestion_id': f'rule:{rule.id}:{idx}',
                'rule_id': rule.id,
                'suggestion_type': 'single_swap',
                'candidate_source': 'curated_rule',
                'label': rule.label,
                'rationale': rule.rationale,
                'ingredient_indices': [idx],
                'swaps': [{
                    'original': {
                        'food_id': ing['food_id'],
                        'food_description': ing['food_description'],
                        'food_group': ing['food_group'],
                        'mass_g': ing['mass_g'],
                        'label_name': ing.get('label_name'),
                    },
                    'replacement': {
                        'food_id': rule.target_food_id,
                        'food_description': rule.target_food_description,
                        'mass_g': ing['mass_g'],
                    },
                }],
                'modified': modified,
            })
    return out


def _use_wafct_recipes(
    dish_name: Optional[str],
    constraints: Dict[str, Any],
    rows: List[Dict[str, Any]],
) -> bool:
    ctx = constraints.get('cultural_context')
    if ctx == 'west_africa':
        return True
    if ctx == 'north_america':
        return False
    if dish_name and any(k in dish_name.lower() for k in (
        'stew', 'jollof', 'garden egg', 'fufu', 'banku', 'waakye', 'egusi', 'groundnut',
    )):
        return True
    return any(r.get('source') == 'wafct' for r in rows)


def _discovery_candidates(
    rows: List[Dict[str, Any]],
    purpose: str,
    constraints: Dict[str, Any],
    *,
    dish_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    comp_ids = {r['food_id'] for r in rows}
    exclude = constraints['exclude_food_ids'] | comp_ids
    source_filter = constraints['source_filter']

    for idx, ing in enumerate(rows):
        # Pure seasonings (salt, spice) are not 1:1 mass food swaps — skip discovery.
        from api.services.substitution_roles import is_primary_seasoning
        if is_primary_seasoning(ing.get('food_description', '')):
            continue

        discovered = discover_candidates_for_ingredient(
            food_id=ing['food_id'],
            food_description=ing['food_description'],
            food_group_id=ing.get('food_group_id'),
            purpose=purpose,
            exclude_ids=exclude,
            source_filter=source_filter,
        )
        for cand in discovered:
            if cand.food_id == ing['food_id']:
                continue
            if not replacement_allowed(
                replacement_food_id=cand.food_id,
                replacement_description=cand.food_description,
                replacement_group_id=cand.food_group_id,
                original_group_id=ing.get('food_group_id'),
                original_description=ing['food_description'],
                constraints=constraints,
            ):
                continue
            if not culinary_swap_plausible(
                ing['food_description'],
                cand.food_description,
                original_mass_g=ing['mass_g'],
            ):
                continue
            modified = _apply_swap_at(rows, idx, cand.food_id, cand.food_description)
            out.append({
                'suggestion_id': f'{cand.origin}:{cand.food_id}:{idx}',
                'rule_id': f'{cand.origin}_{cand.food_id}',
                'suggestion_type': 'single_swap',
                'candidate_source': cand.origin,
                'label': cand.label,
                'rationale': cand.rationale,
                'ingredient_indices': [idx],
                'swaps': [{
                    'original': {
                        'food_id': ing['food_id'],
                        'food_description': ing['food_description'],
                        'food_group': ing['food_group'],
                        'mass_g': ing['mass_g'],
                        'label_name': ing.get('label_name'),
                    },
                    'replacement': {
                        'food_id': cand.food_id,
                        'food_description': cand.food_description,
                        'mass_g': ing['mass_g'],
                    },
                }],
                'modified': modified,
            })

        if _use_wafct_recipes(dish_name, constraints, rows):
            for wafct in recipe_swap_candidates(
                dish_name=dish_name or '',
                ingredient_description=ing['food_description'],
                exclude_ids=exclude,
            ):
                fid = int(wafct['food_id'])
                if fid == ing['food_id']:
                    continue
                meta = _food_meta(fid)
                if not replacement_allowed(
                    replacement_food_id=fid,
                    replacement_description=wafct['food_description'],
                    replacement_group_id=meta.get('food_group_id'),
                    original_group_id=ing.get('food_group_id'),
                    original_description=ing['food_description'],
                    constraints=constraints,
                ):
                    continue
                if not culinary_swap_plausible(
                    ing['food_description'],
                    wafct['food_description'],
                    original_mass_g=ing['mass_g'],
                ):
                    continue
                modified = _apply_swap_at(rows, idx, fid, wafct['food_description'])
                out.append({
                    'suggestion_id': f'wafct_recipe:{fid}:{idx}',
                    'rule_id': f'wafct_recipe_{fid}',
                    'suggestion_type': 'single_swap',
                    'candidate_source': 'wafct_recipe',
                    'label': wafct['label'],
                    'rationale': wafct['rationale'],
                    'ingredient_indices': [idx],
                    'swaps': [{
                        'original': {
                            'food_id': ing['food_id'],
                            'food_description': ing['food_description'],
                            'food_group': ing['food_group'],
                            'mass_g': ing['mass_g'],
                            'label_name': ing.get('label_name'),
                        },
                        'replacement': {
                            'food_id': fid,
                            'food_description': wafct['food_description'],
                            'mass_g': ing['mass_g'],
                        },
                    }],
                    'modified': modified,
                })
    return out


def _multi_swap_candidates(
    single_specs: List[Dict[str, Any]],
    max_swaps: int,
) -> List[Dict[str, Any]]:
    if max_swaps < 2 or len(single_specs) < 2:
        return []

    out: List[Dict[str, Any]] = []
    # Combine top singles with distinct ingredient indices (cap pairs for perf).
    top = single_specs[:12]
    for a, b in itertools.combinations(top, 2):
        ia = a['ingredient_indices'][0]
        ib = b['ingredient_indices'][0]
        if ia == ib:
            continue
        modified = copy.deepcopy(a['modified'])
        # Apply second swap on top of first modification
        rep_b = b['swaps'][0]['replacement']
        modified[ib] = {
            **modified[ib],
            'food_id': rep_b['food_id'],
            'food_description': rep_b['food_description'],
            'food_group': _food_meta(rep_b['food_id'])['food_group'],
            'food_group_id': _food_meta(rep_b['food_id'])['food_group_id'],
        }
        out.append({
            'suggestion_id': f'multi:{a["suggestion_id"]}+{b["suggestion_id"]}',
            'rule_id': 'multi_swap',
            'suggestion_type': 'multi_swap',
            'candidate_source': 'combined',
            'label': f"{a['label']} + {b['label']}",
            'rationale': 'Combines two single-ingredient swaps into one plan.',
            'ingredient_indices': sorted([ia, ib]),
            'swaps': a['swaps'] + b['swaps'],
            'modified': modified,
        })
        if len(out) >= 8:
            break
    return out


def _greedy_reformulation_plans(
    rows: List[Dict[str, Any]],
    *,
    purpose: str,
    parsed_constraints: Dict[str, Any],
    dish_name: Optional[str],
    baseline_hefi: Dict[str, Any],
    baseline_fcs: Dict[str, Any],
    baseline_nutrients: Dict[str, float],
    baseline_sustain: float,
    max_swaps: int,
) -> List[Dict[str, Any]]:
    """Phase 4: stepwise reformulation by applying the best swap at each stage."""
    if max_swaps < 2:
        return []

    current = copy.deepcopy(rows)
    used_indices: Set[int] = set()
    step_suggestions: List[Dict[str, Any]] = []

    for _ in range(max_swaps):
        specs = _rule_candidates(current, purpose, parsed_constraints)
        specs.extend(_discovery_candidates(
            current, purpose, parsed_constraints, dish_name=dish_name,
        ))
        specs = [s for s in specs if s['ingredient_indices'][0] not in used_indices]

        best: Optional[Dict[str, Any]] = None
        for spec in specs:
            sug = _build_suggestion(
                suggestion_id=spec['suggestion_id'],
                rule_id=spec.get('rule_id', spec['suggestion_id']),
                suggestion_type=spec['suggestion_type'],
                candidate_source=spec['candidate_source'],
                label=spec['label'],
                rationale=spec['rationale'],
                ingredient_indices=spec['ingredient_indices'],
                swaps=spec['swaps'],
                baseline_hefi=baseline_hefi,
                baseline_fcs=baseline_fcs,
                baseline_nutrients=baseline_nutrients,
                baseline_sustain=baseline_sustain,
                modified=spec['modified'],
                purpose=purpose,
                baseline_composition=rows,
            )
            if sug and (best is None or sug['rank_score'] > best['rank_score']):
                best = sug

        if best is None or best['rank_score'] <= 0.01:
            break

        step_suggestions.append(best)
        used_indices.add(best['ingredient_index'])
        current = _normalize_composition(best['modified_composition'])

    if len(step_suggestions) < 2:
        return []

    combined_swaps = []
    for s in step_suggestions:
        combined_swaps.extend(s.get('swaps') or [])

    plan_ev = _evaluate_modification(
        baseline_hefi=baseline_hefi,
        baseline_fcs=baseline_fcs,
        baseline_nutrients=baseline_nutrients,
        baseline_sustain=baseline_sustain,
        modified=current,
        purpose=purpose,
    )
    plan_fped_deltas = None
    try:
        from api.services.fped_aggregator import fped_swap_delta
        plan_baseline_foods = [
            {'food_id': sw['original']['food_id'], 'mass_g': sw['original']['mass_g']}
            for sw in combined_swaps
        ]
        plan_replacement_foods = [
            {'food_id': sw['replacement']['food_id'], 'mass_g': sw['replacement']['mass_g']}
            for sw in combined_swaps
        ]
        plan_fped_deltas = fped_swap_delta(plan_baseline_foods, plan_replacement_foods)
    except Exception:  # noqa: BLE001
        plan_fped_deltas = None

    if not swap_passes_quality_gate(
        plan_ev,
        purpose=purpose,
        candidate_source='reformulation',
        swaps=combined_swaps,
        fped_deltas=plan_fped_deltas,
    ):
        return []

    total_rank = sum(s['rank_score'] for s in step_suggestions)
    fped_gap_fill = None
    try:
        baseline_foods_full = [{'food_id': r['food_id'], 'mass_g': r['mass_g']} for r in rows]
        modified_foods_full = [{'food_id': r['food_id'], 'mass_g': r['mass_g']} for r in current]
        fped_gap_fill = fped_gap_fill_bonus(baseline_foods_full, modified_foods_full)
        if fped_gap_fill.get('bonus', 0.0) > 0:
            total_rank += fped_gap_fill['bonus']
    except Exception:  # noqa: BLE001
        fped_gap_fill = None

    return [{
        'id': f'reformulation:{len(step_suggestions)}',
        'rule_id': 'greedy_reformulation',
        'suggestion_type': 'reformulation_plan',
        'candidate_source': 'reformulation',
        'label': f'Multi-step plan ({len(step_suggestions)} swaps)',
        'rationale': (
            'Applies the strongest swap at each step while keeping earlier changes in place. '
            'Useful when several ingredients could be improved together.'
        ),
        'ingredient_index': step_suggestions[0]['ingredient_index'],
        'ingredient_indices': sorted(used_indices),
        'swaps': combined_swaps,
        'original': step_suggestions[0]['original'],
        'replacement': step_suggestions[-1]['replacement'],
        'modified_composition': _serialize_composition(plan_ev['modified_composition']),
        'hefi': plan_ev['hefi'],
        'fcs': plan_ev.get('fcs'),
        'sustainability_proxy': plan_ev.get('sustainability_proxy'),
        'nutrients': plan_ev['nutrients'],
        'rank_score': total_rank,
        'fped_deltas': plan_fped_deltas,
        'fped_gap_fill': fped_gap_fill,
        'reformulation_steps': len(step_suggestions),
    }]


def analyze_substitutions(
    composition: List[Dict[str, Any]],
    *,
    purpose: str = 'general_health',
    max_suggestions: int = 3,
    constraints: Optional[Dict[str, Any]] = None,
    include_scorecard: bool = True,
    dish_name: Optional[str] = None,
    reformulation_mode: str = 'singles',
) -> Dict[str, Any]:
    """Analyze a composition and return ranked substitution suggestions."""
    t0 = time.perf_counter()
    purpose = purpose if purpose in PURPOSE_LABELS else 'general_health'
    max_suggestions = max(1, min(int(max_suggestions), 10))
    parsed_constraints = _parse_constraints(constraints)

    rows = _normalize_composition(composition)
    total_mass = sum(r['mass_g'] for r in rows)

    baseline_hefi = _score_hefi(rows)
    baseline_fcs = _score_fcs(rows)
    baseline_nutrients = _aggregate_nutrients(rows)
    baseline_sustain = sustainability_proxy_score(rows)

    specs = _rule_candidates(rows, purpose, parsed_constraints)
    specs.extend(_discovery_candidates(
        rows, purpose, parsed_constraints, dish_name=dish_name,
    ))

    evaluated_singles: List[Dict[str, Any]] = []
    for spec in specs:
        sug = _build_suggestion(
            suggestion_id=spec['suggestion_id'],
            rule_id=spec.get('rule_id', spec['suggestion_id']),
            suggestion_type=spec['suggestion_type'],
            candidate_source=spec['candidate_source'],
            label=spec['label'],
            rationale=spec['rationale'],
            ingredient_indices=spec['ingredient_indices'],
            swaps=spec['swaps'],
            baseline_hefi=baseline_hefi,
            baseline_fcs=baseline_fcs,
            baseline_nutrients=baseline_nutrients,
            baseline_sustain=baseline_sustain,
            modified=spec['modified'],
            purpose=purpose,
            baseline_composition=rows,
        )
        if sug:
            evaluated_singles.append(sug)

    # De-dupe singles by (indices, replacement food ids)
    best_singles: Dict[str, Dict[str, Any]] = {}
    for s in evaluated_singles:
        key = (
            tuple(s['ingredient_indices']),
            tuple(sw['replacement']['food_id'] for sw in s['swaps']),
        )
        key_str = str(key)
        if key_str not in best_singles or s['rank_score'] > best_singles[key_str]['rank_score']:
            best_singles[key_str] = s

    singles = sorted(best_singles.values(), key=lambda x: x['rank_score'], reverse=True)

    # Score the (unchanged) baseline ONCE and reuse it for every suggestion's scorecard
    # below. Re-scoring the baseline inside each enrich_scorecard_deltas call was the
    # dominant redundant cost (N+1 baseline scorings for N suggestions).
    baseline_scorecard = score_composition(rows) if include_scorecard else None

    multi: List[Dict[str, Any]] = []
    if parsed_constraints['max_swaps'] >= 2:
        multi_specs = _multi_swap_candidates(specs, parsed_constraints['max_swaps'])
        for spec in multi_specs:
            sug = _build_suggestion(
                suggestion_id=spec['suggestion_id'],
                rule_id=spec.get('rule_id', spec['suggestion_id']),
                suggestion_type=spec['suggestion_type'],
                candidate_source=spec['candidate_source'],
                label=spec['label'],
                rationale=spec['rationale'],
                ingredient_indices=spec['ingredient_indices'],
                swaps=spec['swaps'],
                baseline_hefi=baseline_hefi,
                baseline_fcs=baseline_fcs,
                baseline_nutrients=baseline_nutrients,
                baseline_sustain=baseline_sustain,
                modified=spec['modified'],
                purpose=purpose,
                baseline_composition=rows,
            )
            if sug:
                multi.append(sug)

    reformulation: List[Dict[str, Any]] = []
    if reformulation_mode == 'greedy' and parsed_constraints['max_swaps'] >= 2:
        reformulation = _greedy_reformulation_plans(
            rows,
            purpose=purpose,
            parsed_constraints=parsed_constraints,
            dish_name=dish_name,
            baseline_hefi=baseline_hefi,
            baseline_fcs=baseline_fcs,
            baseline_nutrients=baseline_nutrients,
            baseline_sustain=baseline_sustain,
            max_swaps=parsed_constraints['max_swaps'],
        )
        if include_scorecard and reformulation:
            for r in reformulation:
                mod_rows = _normalize_composition(r['modified_composition'])
                r['scorecard'] = enrich_scorecard_deltas(rows, mod_rows, baseline_sc=baseline_scorecard)

    combined = sorted(singles + multi + reformulation, key=lambda x: x['rank_score'], reverse=True)
    suggestions = combined[:max_suggestions]

    pareto_frontier: List[Dict[str, Any]] = []

    if include_scorecard and suggestions:
        # Each suggestion's scorecard is independent and reuses the shared baseline
        # (computed once above), so only score_composition(modified) runs here. Compute
        # them concurrently — same numbers as the serial loop, just off the critical path.
        def _attach_scorecard(s: Dict[str, Any]) -> None:
            mod_rows = _normalize_composition(s['modified_composition'])
            s['scorecard'] = enrich_scorecard_deltas(rows, mod_rows, baseline_sc=baseline_scorecard)

        if len(suggestions) > 1:
            with ThreadPoolExecutor(
                    max_workers=min(6, len(suggestions)),
                    thread_name_prefix='subst-scorecard',
            ) as ex:
                list(ex.map(_attach_scorecard, suggestions))
        else:
            _attach_scorecard(suggestions[0])
        pareto_frontier = compute_pareto_frontier(suggestions)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    constraints_out = {
        'exclude_food_ids': sorted(parsed_constraints['exclude_food_ids']),
        'source_filter': parsed_constraints['source_filter'] or 'both',
        'max_swaps': parsed_constraints['max_swaps'],
        'vegetarian': parsed_constraints.get('vegetarian', False),
        'same_functional_role': parsed_constraints.get('same_functional_role', False),
        'exclude_allergens': parsed_constraints.get('exclude_allergens', []),
        'cultural_context': parsed_constraints.get('cultural_context') or 'auto',
    }

    return {
        'success': True,
        'purpose': purpose,
        'purpose_label': PURPOSE_LABELS.get(purpose, purpose),
        'dish_name': dish_name,
        'baseline': {
            'composition': rows,
            'total_mass_g': round(total_mass, 1),
            'hefi': baseline_hefi,
            'fcs': baseline_fcs,
            'nutrients': baseline_nutrients,
            'sustainability_proxy': baseline_sustain,
            'scorecard': baseline_scorecard,
        },
        'suggestions': suggestions,
        'pareto_frontier': pareto_frontier,
        'metadata': {
            'phase': 4,
            'rules_evaluated': len(rules_for_purpose(purpose)),
            'candidates_found': len(specs),
            'single_suggestions': len(singles),
            'multi_suggestions': len(multi),
            'reformulation_plans': len(reformulation),
            'reformulation_mode': reformulation_mode,
            'include_scorecard': include_scorecard,
            'constraints': constraints_out,
            'elapsed_ms': elapsed_ms,
        },
    }


def score_modified_composition(
    composition: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Re-score a modified composition (apply endpoint / client handoff)."""
    rows = _normalize_composition(composition)
    total_mass = sum(r['mass_g'] for r in rows)
    return {
        'success': True,
        'composition': _serialize_composition(rows),
        'total_mass_g': round(total_mass, 1),
        'hefi': _score_hefi(rows),
        'fcs': _score_fcs(rows),
        'nutrients': _aggregate_nutrients(rows),
        'sustainability_proxy': sustainability_proxy_score(rows),
        'scorecard': score_composition(rows),
    }


def batch_analyze_substitutions(
    items: List[Dict[str, Any]],
    *,
    purpose: str = 'general_health',
    max_suggestions: int = 3,
    constraints: Optional[Dict[str, Any]] = None,
    include_scorecard: bool = True,
) -> Dict[str, Any]:
    """Analyze multiple compositions (researcher batch mode)."""
    if not items:
        raise ValueError('items must be a non-empty list')

    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for i, item in enumerate(items):
        comp = item.get('composition') if isinstance(item, dict) else None
        if not comp:
            errors.append({'index': i, 'message': 'composition is required'})
            continue
        item_purpose = str(item.get('purpose', purpose))
        if item_purpose not in PURPOSE_LABELS:
            item_purpose = purpose
        try:
            max_s = int(item.get('max_suggestions', max_suggestions))
        except (TypeError, ValueError):
            max_s = max_suggestions
        item_constraints = item.get('constraints', constraints)
        try:
            results.append({
                'index': i,
                'label': item.get('label'),
                **analyze_substitutions(
                    comp,
                    purpose=item_purpose,
                    max_suggestions=max_s,
                    constraints=item_constraints,
                    include_scorecard=include_scorecard,
                ),
            })
        except ValueError as exc:
            errors.append({'index': i, 'message': str(exc)})

    return {
        'success': len(errors) == 0,
        'results': results,
        'errors': errors,
        'metadata': {
            'phase': 4,
            'count': len(items),
            'succeeded': len(results),
            'failed': len(errors),
        },
    }
