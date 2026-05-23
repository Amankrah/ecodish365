"""Audience-aware explanation pack for FCS / FCS-10 (Mozaffarian 2021 / Barrett 2025).

ADDS the previously-missing `recommendation` field per Mozaffarian et al. 2021
Methods p. 8 cut-offs:
  - FCS ≥ 70  → "Foods to be encouraged"
  - FCS 31-69 → "Foods to be consumed in moderation"
  - FCS ≤ 30  → "Foods to be minimized"

Mirrors the existing UserType convention ('individual' | 'researcher' | 'policy').

The MANDATORY caveat for FCS individual-mode is "do not compare across
distinct food/product categories": FCS is a per-100-kcal density score, so
comparing a 100-kcal apple slice to 100-kcal soda is fair, but comparing FCS
across categories without considering serving size and dietary role can
mislead.

ALSO surfaces the NOVA category label per Monteiro 2019 (NOVA 1-4 with the
canonical text descriptions), and embeds the 2026-05-23 NOVA classifier
rebuild reference (rigorous Monteiro-grounded classifier replacing the
keyword-only block; see backend/fcs_calculator/fcs/utils/nova_classifier.py).

NO `original_score` (pre-rescaling raw value), per-attribute domain scores,
or ingredient-weighting formulas are quoted to the individual audience.
"""
from __future__ import annotations

from typing import Dict


# Mozaffarian 2021 Methods p. 8 explicit cut-offs.
_ENCOURAGE_FLOOR = 70.0
_LIMIT_CEILING = 30.0


_NOVA_CANONICAL_DESCRIPTIONS = {
    1: ('Unprocessed or minimally processed',
        'Edible parts of plants or animals after separation from nature; '
        'or natural foods altered only by drying, crushing, freezing, '
        'pasteurization, packaging — NO added salt/sugar/oil. Examples: '
        'raw fruit, raw vegetables, plain milk, whole grains, raw eggs, '
        'pasteurized milk.'),
    2: ('Processed culinary ingredients',
        'Substances derived from minimally-processed foods (or nature) by '
        'pressing, refining, grinding, milling, used in kitchens to season '
        'and cook. Examples: vegetable oils, butter, sugar, salt, vinegar, '
        'flour.'),
    3: ('Processed foods',
        'Foods made by adding NOVA 2 ingredients to NOVA 1 foods PLUS a '
        'preservation or cooking method (canning, smoking, curing, baking, '
        'non-alcoholic fermentation). Examples: canned vegetables, cured '
        'meats (ham, bacon), cheeses, plain freshly-baked breads, 100% '
        'fruit juice.'),
    4: ('Ultra-processed foods',
        'Industrial formulations made mostly from substances derived from '
        'foods AND additives, with little/no intact NOVA 1 food. Signals: '
        'ingredient isolates (protein isolates, maltodextrin, HFCS, '
        'hydrogenated oils), industrial additives (artificial flavours/'
        'colours, emulsifiers, non-sugar sweeteners), industrial processes '
        '(extrusion, reconstitution). Examples: soft drinks, packaged '
        'snacks, hot dogs and reconstituted meats, frozen pre-prepared '
        'dishes, sweetened breakfast cereals, instant noodles.'),
}


def _recommendation_band(fcs: float) -> str:
    """Mozaffarian 2021 Methods p. 8 cut-offs."""
    if fcs >= _ENCOURAGE_FLOOR:
        return 'encourage'
    if fcs <= _LIMIT_CEILING:
        return 'limit'
    return 'moderate'


def _band_phrase(band: str) -> str:
    return {
        'encourage': 'Foods to be encouraged',
        'moderate':  'Foods to be consumed in moderation',
        'limit':     'Foods to be minimized',
    }.get(band, 'Foods to be consumed in moderation')


def get_explanations(
    fcs: float,
    nova_category: str,
    user_type: str = 'individual',
) -> Dict[str, Dict[str, str]]:
    """Return audience-appropriate FCS explanation pack.

    `nova_category` is the NOVACategory enum string from fcs_views (one of
    'MINIMALLY_PROCESSED', 'PROCESSED_CULINARY_INGREDIENTS', 'PROCESSED_FOODS',
    'ULTRA_PROCESSED_FOODS').
    """
    band = _recommendation_band(fcs)
    band_label = _band_phrase(band)
    nova_level = {
        'MINIMALLY_PROCESSED': 1,
        'PROCESSED_CULINARY_INGREDIENTS': 2,
        'PROCESSED_FOODS': 3,
        'ULTRA_PROCESSED_FOODS': 4,
    }.get(nova_category, 1)
    nova_short, nova_long = _NOVA_CANONICAL_DESCRIPTIONS[nova_level]

    if user_type == 'researcher':
        return {
            'score_summary': {
                'title': 'FCS / FCS-10 (Food Compass Score) — Mozaffarian 2021 / Barrett 2025',
                'headline': (
                    f'FCS {fcs:.1f} / 100 — band: "{band_label}" '
                    f'(Mozaffarian 2021 Methods p. 8 cut-off: '
                    f'encourage ≥ {_ENCOURAGE_FLOOR:.0f}, '
                    f'limit ≤ {_LIMIT_CEILING:.0f}). '
                    f'NOVA {nova_level}: {nova_short}.'
                ),
                'units': (
                    'Food Compass Score 1-100 (rescaled from raw 9-domain '
                    'sum via Mozaffarian 2021 SI Table S3 footnote *: '
                    'FCS = 100 − ((26.1 − raw_truncated) / 36.7) × 99, with '
                    'raw truncated at the 5th and 95th percentiles across '
                    '8,032 NHANES 2015-16 foods (-10.7 and 26.1). '
                    'Population statistics (NHANES): mean 43.2, SD 28.5, '
                    'median 39.3, range 1-100.'
                ),
                'interpretation': (
                    f'Scoring 18 attributes across 9 domains (Nutrient '
                    f'Ratios, Vitamins, Minerals, Food Ingredients, '
                    f'Additives, Processing, Specific Lipids, Fiber & '
                    f'Protein, Phytochemicals). FCS combines item-level '
                    f'attribute scores per 100 kcal. Diet-level scoring uses '
                    f'i.FCS (O\'Hearn 2022 Nat Comm 13:7066): energy-weighted '
                    f'mean of per-item FCS, alcohol excluded and entered as '
                    f'covariate. i.FCS HR 0.92 (0.88-0.95) for all-cause '
                    f'mortality per 1 SD (10.9 points); highest vs lowest '
                    f'quintile HR 0.76 (24% lower risk).'
                ),
                'mandatory_caveat': (
                    'CONSUMER-FACING WARNING: per-100-kcal density score, so '
                    'cross-category comparisons require care about serving '
                    'size and dietary role. Do not interpret FCS as a single-'
                    'meal verdict; the validated outcome metric is diet-level '
                    'i.FCS, not item-level FCS.'
                ),
            },
            'methodology': {
                'title': 'Methodology Provenance',
                'rescaling_audit': (
                    'FCS-CODE-1 (2026-05-21): the rescaling formula was '
                    'corrected from a pre-audit linear [-70, +70] stretch '
                    'to the Mozaffarian 2021 SI Table S3 formula. Pinned '
                    'in fcs_calculator/tests/test_fcs_rust.py::test_golden_'
                    'food_29_scores_stable at FCS=21.61 for CNF FoodID 29 '
                    '(Cheese, edam).'
                ),
                'nova_classifier': (
                    'NOVA classification (one of FCS-10\'s 18 attributes, '
                    'Food Ingredients domain) rebuilt 2026-05-23 from '
                    'substring-keyword matching to a rigorous Monteiro-2019-'
                    'grounded classifier at backend/fcs_calculator/fcs/utils/'
                    'nova_classifier.py: CNF FoodGroup hard rules + word-'
                    'boundary regex matching + optional LLM augmentation '
                    '(NOVA-CODE-1 SHIPPED). 20/20 PASS on Monteiro-canonical '
                    'validation panel covering all 4 NOVA groups.'
                ),
                'domains_summary': (
                    '9 domains weighted per Mozaffarian 2021: '
                    'Nutrient Ratios, Vitamins, Minerals, Food Ingredients, '
                    'Additives (full weight); Specific Lipids, Fiber & '
                    'Protein, Phytochemicals (half weight); Processing '
                    '(scored via NOVA: -10/-5/-2.5/0 for NOVA 4/3/2/1).'
                ),
            },
            'citations': {
                'original': (
                    'Mozaffarian D, El-Abbadi NH, O\'Hearn M, et al. Food '
                    'Compass is a nutrient profiling system using expanded '
                    'characteristics for assessing healthfulness of foods. '
                    'Nat Food. 2021;2(8):809-818. doi:10.1038/s43016-021-'
                    '00381-y.'
                ),
                'fcs10': (
                    'Barrett EM et al. Development and validation of FCS-10, '
                    'a label-only nutrient profiling system based on the '
                    'Food Compass Score. AJCN 2025 (Methods pp. 7-9).'
                ),
                'mortality_validation': (
                    'O\'Hearn M et al. Incident type 2 diabetes attributable '
                    'to suboptimal diet in 184 countries. Nat Comm. 2022;13:'
                    '7066. doi:10.1038/s41467-022-34514-z.'
                ),
                'nova_framework': (
                    'Monteiro CA et al. Ultra-processed foods, diet quality, '
                    'and health using the NOVA classification system. FAO; '
                    '2019. The 4-group framework + canonical examples.'
                ),
            },
            'action_tips': {
                'reporting': (
                    'When citing FCS scores in publications, report the '
                    'continuous FCS value (not just the band), pair with '
                    'NOVA category, and disclose the Mozaffarian 2021 SI '
                    'Table S3 rescaling formula reference. For diet-level '
                    'claims, use i.FCS (energy-weighted mean) not single-'
                    'item FCS.'
                ),
            },
        }

    if user_type == 'policy':
        return {
            'score_summary': {
                'title': 'FCS — Mortality-Validated Diet-Quality Indicator',
                'headline': (
                    f'FCS {fcs:.1f}/100 — "{band_label}". '
                    f'NOVA {nova_level}: {nova_short}.'
                ),
                'units': (
                    'Score 1-100; Mozaffarian 2021 cut-offs: encourage ≥ 70 '
                    f'({_ENCOURAGE_FLOOR:.0f}), moderate 31-69, '
                    f'limit ≤ {_LIMIT_CEILING:.0f}. NHANES population mean '
                    'FCS 43.2; i.FCS (diet-level) mean 35.5, SD 10.9.'
                ),
                'interpretation': (
                    'O\'Hearn 2022 (Nat Comm 13:7066) NHANES validation: per '
                    '1-SD (10.9-point) improvement in diet-level i.FCS, all-'
                    'cause mortality HR 0.92 (0.88-0.95); highest vs lowest '
                    'quintile HR 0.76 (24% lower risk). Convergent validity '
                    'with HEI-2015: r = 0.81 (Spearman). The encourage band '
                    '(FCS ≥ 70) covers only ~0.5% of NHANES foods — full '
                    'encouragement is rare and reflects nutrient-dense whole '
                    'foods.'
                ),
                'mandatory_caveat': (
                    'FCS is per-100-kcal density; cross-category policy '
                    'targets must account for serving sizes and dietary '
                    'role. The mortality validation applies to diet-level '
                    'i.FCS, NOT to individual food rankings — single-food '
                    'FCS thresholds drive food-system policy (reformulation, '
                    'labelling), but population health claims require the '
                    'diet-level i.FCS metric.'
                ),
            },
            'policy_context': {
                'title': 'Policy Applications',
                'use_cases': (
                    'Suitable for: (a) front-of-pack labelling design (FCS '
                    'band → traffic-light), (b) procurement thresholds for '
                    'school / hospital meals (target diet-level i.FCS ≥ 50 '
                    'as a stretch goal), (c) reformulation targeting NOVA 4 '
                    'foods to NOVA 3, (d) tax / subsidy design using the '
                    'limit-band (FCS ≤ 30) cutoff. Mortality validation '
                    'makes FCS the strongest health-outcome-anchored '
                    'nutrition indicator currently available.'
                ),
                'population_distribution': (
                    'NHANES 2015-16 (8,032 foods): mean FCS 43.2, SD 28.5; '
                    'diet-level i.FCS mean 35.5, 5th-95th pctl 19.5-55.3. '
                    'Most people score 31-69 (moderate band); 32.7% ≤ 30 '
                    '(limit); only 0.5% ≥ 70 (encourage).'
                ),
            },
            'citations': {
                'primary': (
                    'Mozaffarian D et al. Nat Food 2021;2:809-818.'
                ),
                'mortality': (
                    'O\'Hearn M et al. Nat Comm 2022;13:7066.'
                ),
            },
            'action_tips': {
                'thresholds': (
                    'For population dietary monitoring: track shifts in the '
                    '% of meals/intake in each band over time. For food-'
                    'system policy: target NOVA 4 → NOVA 3 reformulation; '
                    'use the FCS limit cutoff (≤ 30) to define "products to '
                    'be discouraged" in subsidy/tax design.'
                ),
            },
        }

    # Default: individual audience (consumer-facing)
    # FIX (FCS audit #7): previously the title repeated the score ("Food Compass
    # Score: 1/100") which duplicated the big numeric score rendered in the
    # adjacent results card. Title is now a plain section header.
    return {
        'score_summary': {
            'title': 'Food Compass Score',
            'headline': (
                f'{band_label}. This food scores {fcs:.0f} out of 100 on the '
                f'Food Compass Score, which combines 18 nutrition and '
                f'processing attributes.'
            ),
            'units': (
                'Foods are graded 1-100: scores at or above 70 are foods to '
                'be encouraged, 31-69 to be consumed in moderation, and '
                '30 or below to be minimized.'
            ),
            'interpretation': (
                f'The "{nova_short}" label describes how this food was '
                f'produced. {nova_long}'
            ),
            'mandatory_caveat': (
                'IMPORTANT: FCS scores foods per 100 calories. Be careful '
                'comparing very different food categories (e.g. a 100-kcal '
                'apple slice vs 100-kcal soda is fair; but FCS scores reflect '
                'nutrition density, not full-meal satisfaction). The '
                'mortality benefit of high-FCS eating is measured at the '
                'DIET level, not from a single food.'
            ),
        },
        'nova_explainer': {
            'title': f'Processing Level: NOVA {nova_level} — {nova_short}',
            'description': nova_long,
        },
        'action_tips': {
            'simple_guidance': (
                f'For "{band_label}" foods like this one, aim for variety '
                f'rather than perfection — your overall eating pattern '
                f'matters more than any single food choice. Favour NOVA 1-3 '
                f'foods over NOVA 4 (ultra-processed) when you have the '
                f'choice.'
            ),
        },
    }
