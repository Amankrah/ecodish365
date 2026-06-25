"""Research-grade meal and 24h-recall deep-dive endpoint.

POST /api/research/meal-deep-dive/
    Body: {
        "scope": "meal" | "day",
        "meals": [{"label": "lunch", "foods": [{"food_id": 27, "mass_g": 240}, ...]}, ...],
        "life_stage": {"age_years": 34, "sex": "female",
                       "pregnancy_status": null, "lactation_status": null} | null,
        "options": {
            "nutrient_set": "research_canonical" | "all",
            "include_per_meal_breakdown": true,
            "include_top_contributors": true,
            "top_k": 5
        }
    }
    Returns a nested JSON: nutrient panel with DRI flags by life-stage,
    composition deep-dive (FPED + NOVA + macronutrient distribution),
    per-nutrient top contributors, and a coverage and provenance block.

POST /api/research/meal-deep-dive/export.csv/
    Same body. Returns a tidy long-format CSV with one row per
    (dimension, key) cell.

The endpoint is deterministic, runs no LLM calls, applies no rate limit,
and reads the shared CNF + FPED + NOVA + DRI compendium artefacts.
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.services import dri_compendium
from api.services.derived_nutrient_metrics import compute_derived_metrics
from api.services.meal_composition_deep_dive import (
    composition_deep_dive,
)
from api.services.meal_contribution_analyser import (
    DEFAULT_CONTRIBUTION_NUTRIENT_IDS,
    top_contributors,
    top_contributors_to_dict,
)
from api.services.meal_nutrient_aggregator import (
    RESEARCH_CANONICAL_NUTRIENT_IDS,
    aggregate_meal_nutrients,
    all_nutrient_meta,
)

logger = logging.getLogger(__name__)


def _clean_foods(foods_raw) -> List[Dict[str, Any]]:
    if not isinstance(foods_raw, list):
        return []
    cleaned = []
    for f in foods_raw:
        if not isinstance(f, dict):
            continue
        try:
            fid = int(f.get('food_id'))
            mass = float(f.get('mass_g'))
        except (TypeError, ValueError):
            continue
        if fid > 0 and mass > 0:
            cleaned.append({'food_id': fid, 'mass_g': mass})
    return cleaned


def _resolve_life_stage(life_stage_raw) -> Tuple[Optional[str], Dict[str, Any]]:
    """Map a request `life_stage` block to (canonical_code, echo_dict).
    Echo dict surfaces the resolved inputs to the response for transparency."""
    if not isinstance(life_stage_raw, dict):
        return None, {'supplied': False}
    age = life_stage_raw.get('age_years')
    sex = life_stage_raw.get('sex')
    preg = life_stage_raw.get('pregnancy_status')
    lact = life_stage_raw.get('lactation_status')
    try:
        age_v = None if age is None else float(age)
    except (TypeError, ValueError):
        age_v = None
    code = dri_compendium.get_life_stage(age_v, sex, preg, lact)
    return code, {
        'supplied': True,
        'age_years': age_v,
        'sex': sex,
        'pregnancy_status': preg,
        'lactation_status': lact,
        'resolved_code': code,
    }


def _build_payload(request_body: Dict[str, Any]) -> Tuple[Dict[str, Any], int, Optional[str]]:
    """Compute the deep-dive payload. Returns (data, http_status, error)."""
    scope = str(request_body.get('scope', 'meal')).lower()
    if scope not in ('meal', 'day'):
        scope = 'meal'

    meals_raw = request_body.get('meals')
    if not isinstance(meals_raw, list) or not meals_raw:
        return {}, status.HTTP_400_BAD_REQUEST, (
            'Field "meals" is required (non-empty list of {label, foods}).'
        )

    # Per-meal cleaning. Each meal carries an optional label plus a foods list.
    cleaned_meals: List[Dict[str, Any]] = []
    for idx, m in enumerate(meals_raw):
        if not isinstance(m, dict):
            continue
        label = str(m.get('label') or f'meal_{idx + 1}')
        foods = _clean_foods(m.get('foods'))
        if foods:
            cleaned_meals.append({'label': label, 'foods': foods})

    if not cleaned_meals:
        return {}, status.HTTP_400_BAD_REQUEST, (
            'No meals with positive food_id and mass_g.'
        )

    options = request_body.get('options') or {}
    if not isinstance(options, dict):
        options = {}
    nutrient_set_kw = str(options.get('nutrient_set', 'research_canonical'))
    include_per_meal = bool(options.get('include_per_meal_breakdown', True))
    include_top_contrib = bool(options.get('include_top_contributors', True))
    try:
        top_k = int(options.get('top_k', 5))
    except (TypeError, ValueError):
        top_k = 5
    top_k = max(1, min(50, top_k))

    if nutrient_set_kw == 'all':
        nutrient_filter = None
    else:
        nutrient_filter = list(RESEARCH_CANONICAL_NUTRIENT_IDS)

    life_stage_code, life_stage_echo = _resolve_life_stage(request_body.get('life_stage'))

    # Optional anthropometry for the derived-metrics block (Phase B, 2026-06-26).
    # Body weight enables protein g/kg and EER computation; PAL category +
    # height refine the EER. All fields are optional — derived_metrics
    # gracefully reports "not computed" when missing.
    anthro = request_body.get('anthropometry') or {}
    if not isinstance(anthro, dict):
        anthro = {}
    def _float_or_none(v):
        try:
            f = float(v)
            return f if f > 0 else None
        except (TypeError, ValueError):
            return None
    body_weight_kg = _float_or_none(anthro.get('body_weight_kg'))
    height_cm      = _float_or_none(anthro.get('height_cm'))
    pal_category   = anthro.get('pal_category')
    if pal_category not in ('sedentary', 'low_active', 'active', 'very_active'):
        pal_category = None

    # Compose all meals' foods into one day-level food list for the
    # day-level aggregation, then optionally aggregate each meal separately.
    day_foods: List[Dict[str, Any]] = []
    for m in cleaned_meals:
        day_foods.extend(m['foods'])

    if scope == 'meal' and len(cleaned_meals) == 1:
        # Single-meal scope: the meal foods ARE the day foods.
        day_foods = cleaned_meals[0]['foods']

    # === Day-level deep-dive ===
    day_nutrient_agg = aggregate_meal_nutrients(
        day_foods,
        nutrient_set=nutrient_filter,
    )
    day_nutrient_amounts = {
        nid: nv.amount for nid, nv in day_nutrient_agg.nutrient_totals.items()
    }
    day_composition = composition_deep_dive(day_foods)
    day_dri_rows = dri_compendium.dri_panel_for_meal(
        day_nutrient_amounts, life_stage_code,
    )

    contribution_nutrient_ids = (
        list(DEFAULT_CONTRIBUTION_NUTRIENT_IDS)
        if nutrient_filter is not None
        else 'all'
    )
    day_contributions: Dict[str, List[Dict[str, Any]]] = {}
    if include_top_contrib:
        contribs = top_contributors(
            day_foods,
            nutrient_ids=contribution_nutrient_ids,
            top_k=top_k,
        )
        day_contributions = top_contributors_to_dict(contribs)

    nutrient_panel: List[Dict[str, Any]] = _build_nutrient_panel(
        day_nutrient_agg, day_dri_rows,
    )

    per_meal_block: Optional[List[Dict[str, Any]]] = None
    if include_per_meal and len(cleaned_meals) > 1:
        per_meal_block = []
        for m in cleaned_meals:
            sub_agg = aggregate_meal_nutrients(m['foods'], nutrient_set=nutrient_filter)
            sub_amounts = {nid: nv.amount for nid, nv in sub_agg.nutrient_totals.items()}
            sub_composition = composition_deep_dive(m['foods'])
            sub_dri = dri_compendium.dri_panel_for_meal(sub_amounts, life_stage_code)
            sub_panel = _build_nutrient_panel(sub_agg, sub_dri)
            per_meal_block.append({
                'label': m['label'],
                'n_foods': len(m['foods']),
                'total_mass_g': round(sum(f['mass_g'] for f in m['foods']), 2),
                'nutrient_panel': sub_panel,
                'macronutrient_distribution':
                    sub_composition.macronutrient_distribution.to_dict(),
                'food_groups': sub_composition.fped_aggregate,
                'processing': {
                    'per_food': [r.to_dict() for r in sub_composition.nova_per_food],
                    'share_by_mass': sub_composition.nova_share.by_mass_pct,
                    'share_by_energy': sub_composition.nova_share.by_energy_pct,
                },
            })

    # Coverage union of nutrient and composition.
    composition_coverage = day_composition.coverage
    nutrient_coverage = day_nutrient_agg.coverage.to_dict()
    coverage_block = {
        'n_foods_total': nutrient_coverage['n_foods'],
        'n_foods_in_cnf': nutrient_coverage['n_foods_in_cnf'],
        'n_foods_unknown': nutrient_coverage['n_foods_unknown'],
        'unknown_food_ids': nutrient_coverage['unknown_food_ids'],
        'n_foods_with_fped': composition_coverage.get('n_foods_with_fped', 0),
        'n_foods_with_nova': composition_coverage.get('n_foods_with_nova', 0),
        'mass_g_total': nutrient_coverage['total_mass_g'],
        'mass_g_with_fped': composition_coverage.get('mass_g_with_fped', 0.0),
        'warnings': _coverage_warnings(
            nutrient_coverage, composition_coverage,
            life_stage_echo, life_stage_code,
        ),
    }

    provenance = {
        'cnf_revision': '2026-05-24 + WAFCT 2019',
        'fped_revision': 'FPED 1718',
        'nova_classifier': 'Monteiro 2019 4-group, deterministic dispatch',
        'dri_compendium': dri_compendium.get_compendium_meta(),
        'response_contract_version': '2026-06-09',
    }

    # Methodology caveats — academic-rigor surface (2026-06-26). The DRI
    # cut-point method (Beaton 1986; IOM 2000 Ch. 4) is for usual intake,
    # not single-day intake; AMDR is a habitual recommendation; NOVA has
    # documented inter-rater disagreement. Frontend renders these as a
    # persistent banner so single-meal / single-day flags ("below_ear",
    # "above_amdr") are read in the right interpretive context.
    is_single_day = scope == 'meal' or len(cleaned_meals) <= 1
    methodology_caveats = {
        'single_day_cutpoint': (
            "EAR cut-point method (IOM 2000 'Dietary Reference Intakes: "
            "Applications in Dietary Assessment', Ch. 4) requires usual intake "
            "distributions, typically ≥2 non-consecutive 24-h recalls adjusted "
            "for within-person variability (NCI Method, Tooze 2010 Stat Med). "
            "Applied here to a single day of intake — flags conflate random "
            "day-to-day variation with chronic inadequacy. Interpret as "
            "'single-day intake vs reference', not as a chronic adequacy verdict."
        ) if is_single_day else None,
        'amdr_habitual': (
            "AMDR (IOM 2005 'DRIs for Energy, Carbohydrate, Fiber, Fat, Fatty "
            "Acids, Cholesterol, Protein, and Amino Acids', Ch. 11) is a "
            "habitual % energy recommendation. A single low-carb meal is not "
            "'below AMDR' if the day balances out. Flags here are informational "
            "for this single observation."
        ),
        'nova_reliability': (
            "NOVA classification inter-rater agreement is moderate (κ ≈ 0.45; "
            "Braesco et al. 2022 Eur J Clin Nutr) with ~25 % misclassification "
            "between trained raters (Bleiweiss-Sande 2019 Curr Dev Nutr). "
            "Per-food classifier confidence is reported alongside each food."
        ),
    }

    data = {
        'meta': {
            'scope': scope,
            'n_meals': len(cleaned_meals),
            'n_foods_in_request': len(day_foods),
            'n_distinct_foods': len(day_nutrient_agg.food_id_map),
            'total_mass_g': round(day_nutrient_agg.coverage.total_mass_g, 2),
            'life_stage': life_stage_echo,
            'options_resolved': {
                'nutrient_set': ('all' if nutrient_filter is None
                                 else 'research_canonical'),
                'include_per_meal_breakdown': include_per_meal,
                'include_top_contributors': include_top_contrib,
                'top_k': top_k,
            },
            'methodology_caveats': methodology_caveats,
        },
        'nutrient_panel': nutrient_panel,
        'macronutrient_distribution':
            day_composition.macronutrient_distribution.to_dict(),
        'food_groups': day_composition.fped_aggregate,
        'processing': {
            'per_food': [r.to_dict() for r in day_composition.nova_per_food],
            'share_by_mass': day_composition.nova_share.by_mass_pct,
            'share_by_energy': day_composition.nova_share.by_energy_pct,
            'median_confidence': day_composition.nova_share.median_confidence,
        },
        'contributions': day_contributions,
        'per_meal': per_meal_block,
        'coverage': coverage_block,
        'provenance': provenance,
        # Phase B (2026-06-26): bioavailability splits + WHO/AHA thresholds +
        # body-weight-anchored protein adequacy + IOM 2002 EER vs Goldberg
        # cutoff. See `api.services.derived_nutrient_metrics`.
        'derived_metrics': compute_derived_metrics(
            nutrient_totals=day_nutrient_amounts,
            foods=day_foods,
            energy_kcal=float(day_nutrient_amounts.get(208, 0.0) or 0.0),
            body_weight_kg=body_weight_kg,
            age_years=(life_stage_echo or {}).get('age_years'),
            sex=(life_stage_echo or {}).get('sex'),
            pal_category=pal_category,
            height_cm=height_cm,
        ),
    }
    return data, status.HTTP_200_OK, None


def _build_nutrient_panel(nutrient_agg, dri_rows) -> List[Dict[str, Any]]:
    """Combine the nutrient panel (amounts) with the DRI rows (references)
    into a single rowset that the UI tables directly."""
    meta_by_nid = all_nutrient_meta()
    dri_by_nid = {r.nutrient_id: r for r in dri_rows}
    out: List[Dict[str, Any]] = []
    for nid, nv in sorted(nutrient_agg.nutrient_totals.items()):
        row = nv.to_dict()
        dri = dri_by_nid.get(nid)
        if dri is not None:
            row['dri'] = dri.to_dict()
        else:
            row['dri'] = None
        # Surface a few static reference fields for the UI.
        meta = meta_by_nid.get(nid, {})
        row['cnf_metadata'] = {
            'decimals': meta.get('decimals', 2),
            'tagname': meta.get('tagname', ''),
        }
        out.append(row)
    return out


def _coverage_warnings(
    nutrient_coverage: Dict[str, Any],
    composition_coverage: Dict[str, Any],
    life_stage_echo: Dict[str, Any],
    life_stage_code: Optional[str],
) -> List[str]:
    warnings: List[str] = []
    if nutrient_coverage.get('n_foods_unknown', 0) > 0:
        warnings.append(
            f'{nutrient_coverage["n_foods_unknown"]} foods are absent from the '
            'CNF / WAFCT registry and contribute zero to every nutrient.'
        )
    total = nutrient_coverage['n_foods_in_cnf'] or 1
    if composition_coverage.get('n_foods_with_fped', 0) < total:
        warnings.append(
            f'{total - composition_coverage["n_foods_with_fped"]} foods lack an '
            'FPED profile; food-group totals understate reality. See coverage block.'
        )
    if not life_stage_echo.get('supplied'):
        warnings.append(
            'No life_stage supplied; DRI references not computed for any nutrient.'
        )
    elif life_stage_code is None:
        warnings.append(
            'Supplied life_stage tuple did not resolve to a published code; '
            'check (age_years, sex) inputs.'
        )
    return warnings


@api_view(['POST'])
@permission_classes([AllowAny])
def research_meal_deep_dive(request):
    """POST /api/research/meal-deep-dive/: JSON deep-dive payload."""
    data, code, error = _build_payload(request.data or {})
    if error is not None:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': error,
        }, status=code)
    return Response({'success': True, 'data': data}, status=code)


@api_view(['POST'])
@permission_classes([AllowAny])
def research_meal_deep_dive_export_csv(request):
    """POST /api/research/meal-deep-dive/export.csv/: long-format CSV.

    Same request body as the JSON endpoint. Returns one CSV file with
    one row per (dimension, key, life_stage) cell, in tidy long format
    so a researcher can ingest it directly into R, Stata, or pandas.

    Dimensions emitted:
      * nutrient_panel : one row per nutrient
      * food_groups    : one row per FPED component or guideline gap
      * processing     : one row per NOVA level (mass and energy shares)
      * macronutrients : one row per macronutrient (CHO, PRO, FAT, alcohol)
      * contributions  : one row per (nutrient, contributor)
    """
    data, code, error = _build_payload(request.data or {})
    if error is not None:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': error,
        }, status=code)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'dimension', 'key', 'subkey', 'metric', 'value', 'unit',
        'life_stage', 'meal_label',
    ])
    life_stage = data['meta']['life_stage'].get('resolved_code') or ''

    # Nutrient panel rows.
    for row in data['nutrient_panel']:
        nid = row['nutrient_id']
        writer.writerow(['nutrient', nid, row['name'], 'amount',
                         row['amount'], row['unit'], life_stage, 'day'])
        writer.writerow(['nutrient', nid, row['name'], 'amount_per_100g_meal',
                         row['amount_per_100g_meal'], row['unit'], life_stage, 'day'])
        dri = row.get('dri')
        if dri:
            for ref_key in ('ear', 'rda', 'ai', 'ul'):
                if dri.get(ref_key) is not None:
                    writer.writerow(['nutrient', nid, row['name'],
                                     f'reference_{ref_key.upper()}',
                                     dri[ref_key], row['unit'], life_stage, 'day'])
            for pct_key in ('pct_ear', 'pct_rda', 'pct_ai', 'pct_ul'):
                if dri.get(pct_key) is not None:
                    writer.writerow(['nutrient', nid, row['name'],
                                     pct_key, dri[pct_key], 'percent',
                                     life_stage, 'day'])
            writer.writerow(['nutrient', nid, row['name'], 'adequacy_flag',
                             dri.get('adequacy_flag', ''), '',
                             life_stage, 'day'])
            if dri.get('cdrr_value') is not None:
                writer.writerow(['nutrient', nid, row['name'], 'cdrr_value',
                                 dri['cdrr_value'], row['unit'], life_stage, 'day'])
                writer.writerow(['nutrient', nid, row['name'], 'cdrr_flag',
                                 dri.get('cdrr_flag', ''), '', life_stage, 'day'])

    # Food-group rows.
    fg = data['food_groups']
    for k, v in fg.get('component_totals', {}).items():
        unit = (fg.get('component_units') or {}).get(k, '')
        writer.writerow(['food_group', k, '', 'intake', v, unit, life_stage, 'day'])
    for gap in fg.get('gaps', []):
        comp = gap.get('component')
        writer.writerow(['food_group_gap', comp, gap.get('label', ''),
                         'myplate_target', gap.get('myplate_target', 0),
                         gap.get('unit', ''), life_stage, 'day'])
        writer.writerow(['food_group_gap', comp, gap.get('label', ''),
                         'cfg_target', gap.get('cfg_target', 0),
                         gap.get('unit', ''), life_stage, 'day'])
        writer.writerow(['food_group_gap', comp, gap.get('label', ''),
                         'myplate_pct_of_target',
                         gap.get('myplate_pct_of_target') or '', 'percent',
                         life_stage, 'day'])
        writer.writerow(['food_group_gap', comp, gap.get('label', ''),
                         'cfg_pct_of_target',
                         gap.get('cfg_pct_of_target') or '', 'percent',
                         life_stage, 'day'])

    # Processing rows.
    for level, pct in (data['processing'].get('share_by_mass') or {}).items():
        writer.writerow(['nova', str(level), '', 'share_by_mass_pct',
                         pct, 'percent', life_stage, 'day'])
    for level, pct in (data['processing'].get('share_by_energy') or {}).items():
        writer.writerow(['nova', str(level), '', 'share_by_energy_pct',
                         pct, 'percent', life_stage, 'day'])

    # Macronutrients.
    mac = data['macronutrient_distribution']
    for k, v in (mac.get('grams') or {}).items():
        writer.writerow(['macro', k, '', 'grams', v, 'g', life_stage, 'day'])
    for k, v in (mac.get('kcal_from') or {}).items():
        writer.writerow(['macro', k, '', 'kcal', v, 'kcal', life_stage, 'day'])
    for k, v in (mac.get('pct_energy') or {}).items():
        writer.writerow(['macro', k, '', 'pct_energy', v, 'percent',
                         life_stage, 'day'])
    for k, v in (mac.get('amdr_status') or {}).items():
        writer.writerow(['macro', k, '', 'amdr_status', v, '',
                         life_stage, 'day'])

    # Contributions.
    for nid_str, rows in (data.get('contributions') or {}).items():
        for r in rows:
            writer.writerow(['contribution', nid_str, r.get('food_id'),
                             'nutrient_amount', r.get('nutrient_amount', 0),
                             '', life_stage, 'day'])
            writer.writerow(['contribution', nid_str, r.get('food_id'),
                             'share_of_total', r.get('share_of_total', 0),
                             'fraction', life_stage, 'day'])
            writer.writerow(['contribution', nid_str, r.get('food_id'),
                             'cumulative_share', r.get('cumulative_share', 0),
                             'fraction', life_stage, 'day'])

    csv_bytes = buf.getvalue().encode('utf-8')
    resp = HttpResponse(csv_bytes, content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="meal-deep-dive.csv"'
    return resp
