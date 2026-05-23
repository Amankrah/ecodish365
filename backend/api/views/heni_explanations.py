"""Audience-aware explanation pack for HENI (Stylianou et al. 2021, Nature Food).

Mirrors the `get_user_explanations()` pattern from `environmental_views.py`:
returns a per-audience dict of interpretive prose grounded in Stylianou et al.
2021 source-paper guidance. Three audiences: 'individual' | 'researcher' |
'policy' (the project's existing UserType convention; see
`frontend/src/lib/api.ts`).

The MANDATORY caveat for HENI is the marginality scope-limit: Stylianou 2021
Discussion p. 622 states the HENI index "is not applicable to substantial
changes in diet" because the DRFs are derived from marginal-effect
epidemiology against current US-adult intake. This caveat MUST be visible in
individual mode (the audience most likely to over-interpret) and is logged
verbatim in researcher mode for documentation.

Score-band labels follow Stylianou 2021 SI Table 11 (pp. 63-64) qualitative
descriptors — not absolute thresholds, since HENI is a continuous score.

NO MATH IS QUOTED to the individual audience: μDALY values, DRF coefficients,
the -0.5256 min/μDALY conversion, per-disease breakdowns are researcher- and
policy-mode only.
"""
from __future__ import annotations

from typing import Dict


def _score_band(health_impact_minutes: float) -> str:
    """Qualitative band from Stylianou 2021 SI Table 11 semantics.

    Continuous-score banding only used to drive interpretive prose; the
    underlying score is reported continuously to all audiences.
    """
    if health_impact_minutes >= 20.0:
        return 'highly_beneficial'
    if health_impact_minutes >= 5.0:
        return 'moderately_beneficial'
    if health_impact_minutes > 0.0:
        return 'mildly_beneficial'
    if health_impact_minutes >= -5.0:
        return 'neutral'
    if health_impact_minutes >= -20.0:
        return 'mildly_detrimental'
    return 'highly_detrimental'


def _band_phrase(band: str) -> str:
    """Human-readable band label."""
    return {
        'highly_beneficial':       'Highly beneficial',
        'moderately_beneficial':   'Moderately beneficial',
        'mildly_beneficial':       'Mildly beneficial',
        'neutral':                 'Neutral',
        'mildly_detrimental':      'Mildly detrimental',
        'highly_detrimental':      'Highly detrimental',
    }.get(band, 'Neutral')


def get_explanations(
    health_impact_minutes: float,
    user_type: str = 'individual',
) -> Dict[str, Dict[str, str]]:
    """Return audience-appropriate HENI explanation pack.

    Returns Dict keyed by 'score_summary' (headline + interpretation +
    mandatory caveat) plus optional 'methodology' / 'citations' /
    'action_tips' sections, gated by user_type.
    """
    band = _score_band(health_impact_minutes)
    band_label = _band_phrase(band)
    abs_minutes = abs(health_impact_minutes)
    sign_phrase = (
        'adds approximately' if health_impact_minutes > 0
        else ('reduces approximately' if health_impact_minutes < 0
              else 'has minimal effect on')
    )

    if user_type == 'researcher':
        return {
            'score_summary': {
                'title': 'HENI (Health Nutritional Index) — Stylianou et al. 2021',
                'headline': (
                    f'{health_impact_minutes:+.2f} min of healthy life per '
                    f'serving (continuous score; qualitative band: {band_label}).'
                ),
                'units': (
                    'Minutes of healthy life gained (+) or lost (−) per '
                    'reference serving, attributable to the marginal addition '
                    'of one serving of this food to the current US-adult '
                    'baseline diet (Stylianou et al. 2021 Results p. 617).'
                ),
                'interpretation': (
                    f'This score derives from the 16-component dietary-risk-'
                    f'factor table (Stylianou 2021 SI Suppl. Table 3 p. 8) '
                    f'convolved with the food\'s risk-component composition '
                    f'(in our pipeline: FPED 2017-2018 cup/oz-equivalents '
                    f'matching the dataset Stylianou used for WWEIA foods). '
                    f'The −0.5256 min/μDALY conversion follows Stylianou 2021 '
                    f'SI p. 98 (1 μDALY = 1 yr × 365 × 24 × 60 × 10⁻⁶ ≈ '
                    f'0.5256 min, sign-flipped so positive minutes = '
                    f'beneficial).'
                ),
                'mandatory_caveat': (
                    'MARGINALITY SCOPE LIMIT: per Stylianou 2021 Discussion '
                    'p. 622, "[HENI] is not applicable to substantial changes '
                    'in diet" because the DRFs are derived from marginal-'
                    'effect epidemiology against current US-adult intake. '
                    'Scores are valid for adding or removing one serving from '
                    'an otherwise-unchanged diet; do not aggregate them to '
                    'estimate the effect of wholesale dietary patterns.'
                ),
            },
            'methodology': {
                'title': 'Methodology Provenance',
                'drf_source': (
                    'DRF μDALY/g coefficients pinned to Stylianou 2021 SI '
                    'Suppl. Table 3 p. 8 (GBD 2016 vintage). 16 risk '
                    'components = 15 GBD 2017 dietary risks with fibre split '
                    'by source (Stylianou SI §S2.9 pp. 35-36).'
                ),
                'tmrels': (
                    'Theoretical-minimum-risk effective intakes (TMRELs) from '
                    'Stylianou SI Table 1 pp. 4-5. Energy-relative TMRELs '
                    '(PUFA 11 %E, trans-fat 0.5 %E) shipped 2026-05-23.'
                ),
                'composition_layer': (
                    'Per-CNF-food risk-component masses derived via the FPED '
                    'composition bridge (HENI-CODE-1.y cause A, shipped '
                    '2026-05-23); see §3.6 of manuscript for the CNF→FNDDS→'
                    'FPED chain. Foods not yet bridged fall back to legacy '
                    'literal-100 attribution with an explicit audit tag.'
                ),
                'carve_outs': (
                    'Stylianou 2021 SI §S2.9 double-counting carve-outs: (1) '
                    'milk-vs-calcium (milk DRF carries the colorectal-cancer '
                    'benefit, calcium suppressed when milk is present); '
                    '(2) fibre-source split (fiber_fvlw if f/v/l/w '
                    'co-present, fiber_other otherwise).'
                ),
            },
            'citations': {
                'primary': (
                    'Stylianou KS, Fulgoni VL III, Jolliet O. Small targeted '
                    'dietary changes can yield substantial gains for human '
                    'health and the environment. Nat Food. 2021;2(8):616-627. '
                    'doi:10.1038/s43016-021-00343-4.'
                ),
                'epidemiology': (
                    'GBD 2017 Diet Collaborators. Health effects of dietary '
                    'risks in 195 countries, 1990-2017. Lancet. 2019;393:'
                    '1958-1972.'
                ),
                'portability_precedent': (
                    'Cardinaals RPM et al. The complementarity of nutrient '
                    'density and disease burden for nLCA. Front Sustain Food '
                    'Syst. 2024;8:1304752 — establishes HENI + ReCiPe 2016 '
                    'combination + Dutch-burden portability procedure.'
                ),
            },
            'action_tips': {
                'reporting': (
                    'When citing HENI scores in publications, report the '
                    'continuous value (not the qualitative band), pair with '
                    'the marginality scope-limit caveat, and disclose the '
                    'composition layer (FPED-bridge vs legacy) per food.'
                ),
            },
        }

    if user_type == 'policy':
        return {
            'score_summary': {
                'title': 'HENI — Population-Level Disease-Burden Indicator',
                'headline': (
                    f'{health_impact_minutes:+.1f} min of healthy life per '
                    f'serving (band: {band_label}).'
                ),
                'units': (
                    'Minutes of healthy life gained or lost per serving, '
                    'derived from Global Burden of Disease 2017 epidemiology '
                    'on 15 dietary risk factors.'
                ),
                'interpretation': (
                    f'At the population level, a 1-minute shift per serving '
                    f'across a Canadian-scale dietary intervention compounds '
                    f'into measurable population-DALY changes. Stylianou 2021 '
                    f'Figure 4-5 quantifies the dynamic range across 5,853 '
                    f'WWEIA foods (-74 to +80 min/serving).'
                ),
                'mandatory_caveat': (
                    'MARGINALITY SCOPE LIMIT: HENI quantifies the effect of '
                    'marginal serving substitutions, not wholesale dietary-'
                    'pattern changes. Use for policy on specific food '
                    'substitutions (e.g. SSB→water, processed-meat→legume), '
                    'NOT for predicting outcomes of population-level diet '
                    'overhauls — the underlying GBD RRs are calibrated on '
                    'current intake distributions.'
                ),
            },
            'policy_context': {
                'title': 'Policy Applications',
                'use_cases': (
                    'Suitable for: (a) front-of-pack labelling support for '
                    'individual products, (b) ranking foods within a category '
                    'for procurement decisions (school meals, hospitals), '
                    '(c) cost-effectiveness analysis for targeted '
                    'substitution interventions, (d) educational tools '
                    'pairing health and environmental impacts (Cardinaals '
                    'et al. 2024 precedent).'
                ),
                'population_range': (
                    'Across 5,853 NHANES/WWEIA reference foods, HENI ranged '
                    '−74 to +80 min/serving (Stylianou 2021 Results p. 619). '
                    'Frankfurter sandwiches (-35 median IQR 31-41) and corned '
                    'beef + tomato sauce (-71) are the canonical detrimental '
                    'extrema; sardines in tomato sauce (+82) is the '
                    'beneficial extremum.'
                ),
            },
            'citations': {
                'primary': (
                    'Stylianou KS et al. Nat Food 2021;2:616-627.'
                ),
                'portability': (
                    'Cardinaals et al. Front Sustain Food Syst 2024;8:1304752 '
                    '— Dutch-burden HENI recompute procedure.'
                ),
            },
            'action_tips': {
                'procurement': (
                    'For institutional menu design, target meal-level HENI '
                    '≥ 0 net across the menu day; treat individual-food '
                    'HENI < -20 min/serving as candidates for reformulation '
                    'or substitution.'
                ),
            },
        }

    # Default: individual audience (consumer-facing)
    return {
        'score_summary': {
            'title': 'Health Impact (HENI)',
            'headline': (
                f'{band_label}: this food {sign_phrase} {abs_minutes:.1f} min '
                f'to your healthy life per serving.'
            ),
            'units': (
                'HENI measures the estimated minutes of healthy life gained '
                'or lost from eating one serving of this food, based on the '
                'evidence linking 16 nutrients and food groups to long-term '
                'disease risk.'
            ),
            'interpretation': (
                'A positive number means the food adds healthy minutes; a '
                'negative number means it subtracts. The bigger the absolute '
                'number, the stronger the effect per serving.'
            ),
            'mandatory_caveat': (
                'This score applies to ADDING OR REMOVING ONE SERVING from '
                'your current eating pattern. It is NOT a prediction of what '
                'would happen if you radically changed your whole diet. Use '
                'it to compare individual foods, not whole diets.'
            ),
        },
        'action_tips': {
            'simple_guidance': (
                'Use HENI to compare similar foods (e.g. two breakfast '
                'options) and lean toward the ones with higher HENI scores. '
                'Small consistent swaps add up over time.'
            ),
        },
    }
