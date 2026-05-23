"""Audience-aware explanation pack for HEFI-2019 (Brassard et al. 2022 a/b, APNM).

Replaces the previously-hardcoded `hefi_interpretation` block in `hefi_views.py`
with literature-cited copy per the existing UserType convention
('individual' | 'researcher' | 'policy').

The MANDATORY caveat for HEFI is the single-day caveat: Brassard et al. 2022b
Discussion p. 588 states explicitly that "a single individual HEFI-2019 from
one 24-h recall does NOT reflect usual adherence and must be interpreted with
great caution". This MUST be visible in individual mode where users are most
likely to over-interpret a single recall as their habitual diet.

Population benchmarks (Brassard 2022b Table A2): Canadian mean 43.1/80;
p1=22.1, p50=43.4, p99=62.9. By age-sex stratum: children 2-18 = 39.5;
males ≥19 = 43.3; females ≥19 = 46.0.

HEFI is explicitly NOT health-validated (Brassard 2022b Discussion p. 589:
"link between HEFI-2019 and disease endpoints is undetermined"); this is a
guideline-adherence index, not a disease-prediction score.

NO COMPONENT-LEVEL POINT BREAKDOWNS or RAW INPUT VALUES are quoted to the
individual audience.
"""
from __future__ import annotations

from typing import Dict


# Brassard 2022b Table A2 (Canadian population, ≥2 years, 2015 CCHS-Nutrition)
_POPULATION_BENCHMARKS = {
    'mean': 43.1, 'p1': 22.1, 'p25': 35.0, 'p50': 43.4, 'p75': 51.0,
    'p99': 62.9, 'std': 11.0,
}


def _score_band(total_score: float) -> str:
    """Band relative to Brassard 2022b Canadian population percentiles."""
    if total_score >= _POPULATION_BENCHMARKS['p99']:
        return 'top_1_percent'           # ≥ 62.9
    if total_score >= _POPULATION_BENCHMARKS['p75']:
        return 'top_quartile'            # 51-62
    if total_score >= _POPULATION_BENCHMARKS['p50']:
        return 'above_median'            # 43-51
    if total_score >= _POPULATION_BENCHMARKS['p25']:
        return 'below_median'            # 35-43
    if total_score >= _POPULATION_BENCHMARKS['p1']:
        return 'bottom_quartile'         # 22-35
    return 'extreme_low'                 # < 22


def _band_phrase(band: str) -> str:
    return {
        'top_1_percent':    'Top 1% of Canadian adults',
        'top_quartile':     'Top quartile of Canadians',
        'above_median':     'Above the Canadian median',
        'below_median':     'Below the Canadian median',
        'bottom_quartile':  'Bottom quartile of Canadians',
        'extreme_low':      'Well below typical Canadian intake',
    }.get(band, 'Within typical range')


def get_explanations(
    total_score: float,
    user_type: str = 'individual',
) -> Dict[str, Dict[str, str]]:
    """Return audience-appropriate HEFI-2019 explanation pack."""
    band = _score_band(total_score)
    band_label = _band_phrase(band)
    percentage = (total_score / 80.0) * 100.0

    if user_type == 'researcher':
        return {
            'score_summary': {
                'title': 'HEFI-2019 (Brassard et al. 2022) — Guideline-Adherence Index',
                'headline': (
                    f'Total {total_score:.1f} / 80 ({percentage:.1f}%); '
                    f'band: {band_label} (Brassard 2022b Table A2 reference '
                    f'distribution).'
                ),
                'units': (
                    'Out of 80 points across 10 components, scored from '
                    'Health Canada\'s 2019 Canada\'s Food Guide-2019 '
                    'recommendations (Brassard et al. 2022a Table 2 p. 600). '
                    'Linear interpolation between minimum and maximum '
                    'standards per component.'
                ),
                'interpretation': (
                    f'The 2015 CCHS-Nutrition Canadian-population mean is '
                    f'43.1/80 (95% CI 42.7-43.6, n=20,103 ≥2 yr); 1st pct '
                    f'22.1; 99th pct 62.9. By age-sex stratum: children 2-18 '
                    f'= 39.5; males ≥19 = 43.3; females ≥19 = 46.0. '
                    f'Brassard 2022b reports Cronbach α = 0.66 indicating '
                    f'multidimensionality — the index spans ≥4 PCA '
                    f'dimensions; total + per-component scores must be '
                    f'reported together per Brassard 2022b Conclusion p. 589.'
                ),
                'mandatory_caveat': (
                    'SINGLE-DAY CAVEAT (Brassard 2022b Discussion p. 588): '
                    '"A single individual HEFI-2019 from one 24-h recall '
                    'does NOT reflect usual adherence and must be interpreted '
                    'with great caution." For individual-level reporting, '
                    'apply NCI multivariate MCMC usual-intake modelling '
                    '(Zhang et al. 2011) on ≥ 2 recall days. Additionally, '
                    'HEFI-2019 is NOT health-outcome-validated (Brassard '
                    '2022b Discussion p. 589: "link between HEFI-2019 and '
                    'disease endpoints is undetermined"); do not interpret '
                    'as a disease-burden predictor.'
                ),
            },
            'methodology': {
                'title': 'Methodology Provenance',
                'components': (
                    '10 components (Brassard 2022a Table 2 p. 600): '
                    '(1) Vegetables & fruits (20 pts), (2) Whole-grain foods '
                    '(5), (3) Grain ratio (5), (4) Protein foods (5), '
                    '(5) Plant-based protein (5), (6) Beverages (10), '
                    '(7) Fatty-acids ratio (5), (8) Saturated fats (5), '
                    '(9) Free sugars (10), (10) Sodium (10).'
                ),
                'imputation_notes': (
                    'C9 (free sugars) currently uses CNF SUGARS, TOTAL as '
                    'proxy because the Rana et al. 2021 Nutrients free-sugars '
                    'supplement is not yet integrated; an explicit '
                    'c9_imputation_note is returned in the API response '
                    'per Brassard 2022a Discussion p. 603.'
                ),
                'population_distribution': (
                    f'Brassard 2022b Table A2 (2015 CCHS-Nutrition, ≥2 yr, '
                    f'n=20,103): mean {_POPULATION_BENCHMARKS["mean"]:.1f}; '
                    f'p1 {_POPULATION_BENCHMARKS["p1"]:.1f}; '
                    f'p25 {_POPULATION_BENCHMARKS["p25"]:.1f}; '
                    f'p50 {_POPULATION_BENCHMARKS["p50"]:.1f}; '
                    f'p75 {_POPULATION_BENCHMARKS["p75"]:.1f}; '
                    f'p99 {_POPULATION_BENCHMARKS["p99"]:.1f}/80.'
                ),
            },
            'citations': {
                'development': (
                    'Brassard D, Elvidge Munene LA, St-Pierre S, Gonzalez A, '
                    'Guenther PM, Jessri M, Black JL, Olstad DL, Vatanparast '
                    'H, Kirkpatrick SI, Vena JE, Bedard B, Bélanger M, Hutchinson '
                    'JM. Development of the Healthy Eating Food Index (HEFI)-'
                    '2019 measuring adherence to Canada\'s Food Guide 2019 '
                    'recommendations on healthy food choices. Appl Physiol '
                    'Nutr Metab. 2022;47(5):595-610. doi:10.1139/apnm-2021-'
                    '0415.'
                ),
                'evaluation': (
                    'Brassard D, Elvidge Munene LA, St-Pierre S, Guenther PM, '
                    'Kirkpatrick SI, Slater J, Vatanparast H, Bedard B, '
                    'Bélanger M, Jessri M, Black JL, Olstad DL, Vena JE, '
                    'Hutchinson JM. Evaluation of the Healthy Eating Food '
                    'Index (HEFI)-2019 measuring adherence to Canada\'s Food '
                    'Guide 2019 recommendations on healthy food choices. Appl '
                    'Physiol Nutr Metab. 2022;47(5):582-594. doi:10.1139/'
                    'apnm-2021-0416.'
                ),
            },
            'action_tips': {
                'reporting': (
                    'When reporting individual-level HEFI-2019 in '
                    'publications: pair with NCI MCMC usual-intake estimates, '
                    'report total + 10 component scores together, and apply '
                    'Balanced Repeated Replication on Stats Canada bootstrap '
                    'weights per Brassard 2022b Methods pp. 583-585.'
                ),
            },
        }

    if user_type == 'policy':
        return {
            'score_summary': {
                'title': 'HEFI-2019 — Canadian Dietary Guideline Adherence',
                'headline': (
                    f'{total_score:.1f} / 80 ({percentage:.1f}% of maximum); '
                    f'population position: {band_label}.'
                ),
                'units': (
                    'Out of 80 points measuring adherence to Canada\'s Food '
                    'Guide 2019. Population benchmarks: Canadian mean 43.1, '
                    'p99 62.9 (Brassard 2022b, n=20,103).'
                ),
                'interpretation': (
                    f'No absolute "healthy threshold" exists for HEFI-2019; '
                    f'the index supports relative comparisons within '
                    f'populations. The low p99 (62.9/80) shows full CFG-2019 '
                    f'adherence is difficult to achieve even in the top 1% '
                    f'of Canadians. By age-sex stratum, children 2-18 '
                    f'(mean 39.5) consistently score lower than female '
                    f'adults ≥19 (mean 46.0).'
                ),
                'mandatory_caveat': (
                    'SINGLE-DAY CAVEAT: individual one-day scores from 24-h '
                    'recalls are NOT habitual-intake estimates. For policy '
                    'reporting on individual outcomes, require ≥ 2 recall '
                    'days + NCI MCMC usual-intake modelling (Brassard 2022b '
                    'Methods pp. 583-585). HEFI-2019 is a CFG-2019 adherence '
                    'index, NOT a health-outcome predictor — disease-burden '
                    'claims require separate epidemiology (e.g. HENI).'
                ),
            },
            'policy_context': {
                'title': 'Policy Applications',
                'use_cases': (
                    'Suitable for: (a) population dietary monitoring per CCHS '
                    'wave-on-wave changes, (b) intervention evaluation '
                    '(school meals, food banks, retail nudges), (c) sub-'
                    'population disparity assessment (age × sex × income × '
                    'province), (d) dietary guideline revision evidence '
                    'base. Manual dietitian-derived HEFI scoring previously '
                    'cost >75 hours of registered-dietitian time per CFIS '
                    'validation study (Hutchinson et al. 2023 Discussion '
                    'p. 630) — automated scoring is the prerequisite for '
                    'population-scale analysis.'
                ),
                'stratum_benchmarks': (
                    'By age-sex stratum (Brassard 2022b Table 5): children '
                    '2-18 = 39.5/80; males ≥19 = 43.3; females ≥19 = 46.0. '
                    'Children\'s lower scores are driven by Fatty Acids Ratio '
                    '(low PUFA:SFA), Plant-based Protein, and Free Sugars '
                    'components (Brassard 2022b Results p. 587).'
                ),
            },
            'citations': {
                'primary': (
                    'Brassard et al. APNM 2022;47:595-610 (development); '
                    '47:582-594 (evaluation).'
                ),
            },
            'action_tips': {
                'targeting': (
                    'Use population-mean shifts as policy targets (not '
                    'absolute thresholds); intervention success measured as '
                    'percentage-point improvement vs control, NOT against an '
                    'absolute "healthy" cutoff.'
                ),
            },
        }

    # Default: individual audience (consumer-facing)
    return {
        'score_summary': {
            'title': 'Diet Quality (HEFI-2019)',
            'headline': (
                f'{total_score:.1f} out of 80 — {band_label} for adherence to '
                f'Canada\'s Food Guide 2019.'
            ),
            'units': (
                'HEFI-2019 measures how well your food choices align with '
                'Canada\'s Food Guide 2019 recommendations. Out of 80 points '
                'across 10 components (vegetables/fruits, whole grains, '
                'protein, beverages, sugars, sodium, etc.).'
            ),
            'interpretation': (
                f'For context, the typical Canadian adult scores about 43/80 '
                f'on this index. Scores above the median (43-51) show better-'
                f'than-average alignment with the Food Guide; scores above 62 '
                f'are in the top 1%.'
            ),
            'mandatory_caveat': (
                'IMPORTANT: a HEFI score from ONE day of eating does NOT '
                'reflect your usual eating pattern. Use this as a snapshot, '
                'not a verdict. The score also measures Food Guide '
                'alignment — it has not been directly linked to specific '
                'health outcomes.'
            ),
        },
        'action_tips': {
            'simple_guidance': (
                'Pay attention to which components scored lowest — those are '
                'the easiest wins. Common low-scoring areas: plant-based '
                'protein, whole grains, and Free Sugars / Sodium when '
                'eating processed foods.'
            ),
        },
    }
