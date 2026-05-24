"""WAFCT-aware audience caveats for the 4 nutrition indicators
(WAFCT-EXTEND, 2026-05-24).

When any food in a scoring request comes from WAFCT (`source='wafct'`), each
indicator should surface a per-audience caveat explaining the per-nutrient
bias the WAFCT-EXPLORE 2026-05-24 study documented + the implications for
that specific indicator (HEFI's missing free-sugars, HSR's sodium method
difference, HENI's un-modelled phytate bioavailability, FCS's generic
mineral bias). The Environmental scorer is LCA-based and unit-agnostic to
nutrient analytical method — no caveat needed.

Callers (`hefi_views.py`, `heni_views.py`, `hsr_views_consolidated.py`,
`fcs_views.py`) pass the food_id list + indicator + user_type; this module
returns a small dict the caller MERGES INTO the existing explanations
block from the indicator-specific `*_explanations.py` module.

Per-100g bias numbers are pinned to the WAFCT-EXPLORE 2026-05-24 study
(`WAFCT_EXPLORATION.md` §3) — 9 paired foods across Panels A + B.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Literal

logger = logging.getLogger(__name__)

Indicator = Literal['hefi', 'heni', 'hsr', 'fcs']
UserType  = Literal['individual', 'researcher', 'policy']


def _count_wafct_foods(food_ids: Iterable[int]) -> int:
    """Count how many of the given FoodIDs came from WAFCT. Uses the
    cached pipeline (`api.cnf_cache.get_api_cnf_pipeline`) for the source
    lookup so this is free after the first pipeline access."""
    try:
        from api.cnf_cache import get_api_cnf_pipeline
        pipeline = get_api_cnf_pipeline()
    except Exception as exc:  # noqa: BLE001
        logger.warning('wafct_caveat: pipeline lookup failed: %s', exc)
        return 0
    n = 0
    for fid in food_ids:
        try:
            if pipeline.food_source(int(fid)) == 'wafct':
                n += 1
        except Exception:  # noqa: BLE001
            continue
    return n


_INDICATOR_RESEARCHER_BLURB = {
    'hefi': (
        'For HEFI specifically: WAFCT lacks SUGAR / SUGARS_FREE in its '
        '39-set; the HEFI free-sugars component (`RATIO_SUG_PERC`) for '
        'WAFCT-only foods evaluates against missing data and may be biased '
        'low. Sodium also picks up the +23.5 % mineral bias.'
    ),
    'heni': (
        'For HENI specifically: WAFCT carries phytate (`PHYTCPP`, `IP3-6`) '
        'in its 57-set but the v1 integration drops these tags at ingest. '
        'Iron / zinc bioavailability discounting is therefore un-modelled '
        'for WAFCT foods, even though phytate inhibition is a clinically '
        'meaningful concern in cereal-heavy West African diets.'
    ),
    'hsr': (
        'For HSR specifically: WAFCT sodium values come from FAO INFOODS '
        'analytical methods and are systematically ~24 % higher than CNF '
        'equivalents on average. HSR\'s sodium baseline-points component is '
        'directly sensitive to this bias.'
    ),
    'fcs': (
        'For FCS specifically: the 10-attribute FCS-10 composite includes '
        'mineral attributes (Ca, Fe) for which WAFCT runs systematically '
        'higher than CNF (median Δ% +23.5 % Ca, +67.7 % Fe).'
    ),
}


_INDICATOR_INDIVIDUAL_BLURB = {
    'hefi': (
        'Sugar information isn\'t available for WAFCT foods, so the '
        'free-sugars portion of your HEFI score may be incomplete.'
    ),
    'heni': (
        'Some West African foods (cereals, legumes) carry compounds that '
        'reduce how much iron and zinc your body actually absorbs. This '
        'effect is not yet modelled in HENI for WAFCT foods.'
    ),
    'hsr': (
        'WAFCT sodium values are measured differently than Canadian foods. '
        'The HSR sodium component may run slightly higher than for '
        'equivalent Canadian foods.'
    ),
    'fcs': (
        'WAFCT and Canadian databases measure iron and calcium differently. '
        'Your FCS may differ slightly from what you\'d see for equivalent '
        'Canadian foods.'
    ),
}


def build_wafct_caveat(
    food_ids: Iterable[int],
    indicator: Indicator,
    user_type: UserType = 'individual',
) -> Dict[str, Any]:
    """Return a caveat dict to merge into the indicator's explanations block.

    Empty dict if no WAFCT foods are present in the meal — caller can safely
    `**` it into the existing explanations and noop in the CNF-only case.

    Researcher / policy mode get the full per-nutrient bias table + per-
    indicator nuance + citation to WAFCT_EXPLORATION.md. Individual mode
    gets a plain-language one-liner.
    """
    if indicator not in ('hefi', 'heni', 'hsr', 'fcs'):
        return {}
    food_id_list: List[int] = [int(f) for f in food_ids]
    n_wafct = _count_wafct_foods(food_id_list)
    if n_wafct == 0:
        return {}

    if user_type == 'individual':
        return {
            'wafct_caveat': {
                'title': 'About West African foods in your meal',
                'message': (
                    f'{n_wafct} food(s) in this meal come from the West '
                    f'African Food Composition Table (WAFCT 2019). '
                    + _INDICATOR_INDIVIDUAL_BLURB[indicator]
                ),
            },
        }

    # researcher / policy
    return {
        'wafct_caveat': {
            'title': (
                f'WAFCT cross-database caveat ({n_wafct} WAFCT food'
                f'{"s" if n_wafct != 1 else ""} in this meal)'
            ),
            'message': (
                'WAFCT-EXTEND 2026-05-24 integrated FAO/INFOODS West African '
                'Food Composition Table 2019 (1,028 foods) alongside CNF '
                '(5,691 foods) via Option B — per-source provenance '
                'preserved by the `source` column. The WAFCT-EXPLORE '
                '2026-05-24 study (WAFCT_EXPLORATION.md §3) found '
                'macronutrients agree well (median |Δ%| ≤ 13 % across '
                'Energy / Water / Protein / Fat / Carbs / Fibre, no '
                'systematic bias) but minerals show a consistent '
                'WAFCT-higher pattern: Ca +23.5 %, Fe +67.7 %, Mg +15.6 %, '
                'K +10.8 % (median Δ% across 9 paired foods). The bias '
                'reflects soil composition, traditional cookware effects, '
                'and analytical-method differences between FAO INFOODS '
                'protocols and Health Canada methods. '
                + _INDICATOR_RESEARCHER_BLURB[indicator]
            ),
            'citation': (
                'Vincent, A., Grande, F., et al. (2019). FAO/INFOODS Food '
                'Composition Table for Western Africa (WAFCT 2019). Rome: '
                'FAO. CC BY-NC-SA 3.0 IGO. See WAFCT_EXPLORATION.md §3 for '
                'the per-100g empirical comparison underlying the bias '
                'numbers cited above.'
            ),
            'wafct_food_count_in_meal': n_wafct,
        },
    }
