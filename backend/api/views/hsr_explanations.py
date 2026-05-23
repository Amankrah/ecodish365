"""Audience-aware explanation pack for HSR (Health Star Rating, HSRAC v9).

Replaces the previously-hardcoded `rating.description` + ad-hoc `health_insights`
generators with HSRAC-v9-pinned literature-cited copy per the existing UserType
convention.

The MANDATORY caveat for HSR is the **within-category-only comparison rule**:
HSRAC v9 (Shahid et al. 2020 p. 1533) explicitly states "a higher HSR indicates
a healthier product WITHIN ITS CATEGORY". Users CANNOT validly compare a 3-star
apple to a 3-star ice cream if they fall in different HSRAC categories. The
category label MUST accompany every HSR display — this is enforced in BOTH
individual and researcher modes.

Six HSRAC v9 categories:
  1   Non-dairy beverages (Cat 1)
  1D  Dairy beverages
  2   General foods (all other non-dairy)
  2D  Other dairy foods (not cheese)
  3   Oils and spreads (Cat 3)
  3D  Cheese (and processed cheese)

NO BASELINE/MODIFYING POINT BREAKDOWN or PER-NUTRIENT POINT TIERS are quoted to
the individual audience. Star value + category + recommendation are the only
consumer-facing fields.
"""
from __future__ import annotations

from typing import Dict


_CATEGORY_LABELS = {
    '1':  'Non-dairy beverages',
    '1D': 'Dairy beverages',
    '2':  'General foods',
    '2D': 'Other dairy foods',
    '3':  'Oils and spreads',
    '3D': 'Cheese',
}


def _star_band(star_rating: float) -> str:
    """HSR star band — half-star quantized per HSRAC v9."""
    if star_rating >= 4.5:
        return 'excellent'
    if star_rating >= 3.5:
        return 'good'
    if star_rating >= 2.5:
        return 'moderate'
    if star_rating >= 1.5:
        return 'below_average'
    return 'poor'


def _band_phrase(band: str) -> str:
    return {
        'excellent':     'Excellent within its category',
        'good':          'Good within its category',
        'moderate':      'Moderate within its category',
        'below_average': 'Below average within its category',
        'poor':          'Poor within its category',
    }.get(band, 'Within typical range')


def get_explanations(
    star_rating: float,
    category: str,
    user_type: str = 'individual',
) -> Dict[str, Dict[str, str]]:
    """Return audience-appropriate HSR explanation pack.

    `category` must be one of '1', '1D', '2', '2D', '3', '3D' per HSRAC v9.
    """
    band = _star_band(star_rating)
    band_label = _band_phrase(band)
    cat_label = _CATEGORY_LABELS.get(category, f'Category {category}')

    if user_type == 'researcher':
        return {
            'score_summary': {
                'title': 'HSR (Health Star Rating) — HSRAC v9, 10 Dec 2025',
                'headline': (
                    f'{star_rating:.1f} / 5 stars in HSRAC v9 Category {category} '
                    f'({cat_label}); band: {band_label}.'
                ),
                'units': (
                    'Star rating 0.5-5.0 in half-star increments. Final HSR '
                    'score = baseline points (energy, sat fat, sugars, '
                    'sodium per 100 g/mL) − modifying points (FVNL %, '
                    'protein, fibre); mapped to stars via HSRAC v9 '
                    'Appendix 1 Table 7 (category-specific). Algorithm pinned '
                    'to HSRAC v9 in backend/rust_core/src/hsr/threshold_data.rs '
                    'with per-category threshold arrays verified cell-by-cell '
                    'against v9 Tables 1-7.'
                ),
                'interpretation': (
                    f'Per HSRAC v9 Introduction p. 1: "A higher HSR indicates '
                    f'a healthier product within its category." The 6 HSRAC '
                    f'categories (1, 1D, 2, 2D, 3, 3D) use different baseline-'
                    f'and-modifying point tables tuned to the nutritional '
                    f'profile of each category. The protein-eligibility rule '
                    f'(v9 p. 26): "if baseline ≥ 13 and V points < 5, P '
                    f'points = 0" is enforced. Per v9 Appendix 5: v9 ≡ v8 ≡ '
                    f'v7 ≡ v6 functionally; cumulative v5→v9 differences '
                    f'limited to (a) Cat 1 energy rows 0-1 cap added in v4 '
                    f'(29 June 2021) and (b) sweet-corn FVNL eligibility '
                    f'(v8, 21 Sept 2023).'
                ),
                'mandatory_caveat': (
                    'WITHIN-CATEGORY-ONLY COMPARISON RULE (Shahid 2020 p. '
                    '1533; HSRAC v9 Introduction): a 3-star non-dairy '
                    'beverage CANNOT be compared to a 3-star general food — '
                    'they use different baseline/modifying point tables. '
                    'Every HSR display MUST include the category label.'
                ),
            },
            'methodology': {
                'title': 'Methodology Provenance',
                'version': (
                    'HSRAC v9 Implementation Guide, 10 December 2025. '
                    'Appendix 1 Tables 1-7 are the canonical calculator. '
                    'Per Appendix 5, v9 makes no policy changes vs v8.'
                ),
                'fvnl_imputation': (
                    'FVNL (Fruits/Vegetables/Nuts/Legumes) inputs are often '
                    'absent from CNF; we impute via ingredient-list category-'
                    'analogy (Shahid 2020 §2.3 p. 3 precedent — HSR authors '
                    'themselves use this across ~700 subcategories) or '
                    'Vergeer et al. 2020 (Nutrients 12:1417) descending-order '
                    'method (logged as sensitivity-analysis cross-check).'
                ),
                'algorithm_verification': (
                    'Validated empirically in Hu, Ahmed & L\'Abbé 2023 '
                    '(AJCN 117:553-563): computing the FSANZ nutrient-'
                    'profiling score from structured nutrient data reaches '
                    'R² = 0.98 (MSE 2.5) vs R² = 0.84-0.87 (MSE 14.4-17.6) '
                    'from label-text prediction. Our pipeline uses the '
                    'structured-data path.'
                ),
            },
            'citations': {
                'primary': (
                    'Health Star Rating Advisory Committee (HSRAC). Health '
                    'Star Rating System Implementation Guide. Version 9. '
                    'Canberra: Australian Government Department of Health, '
                    'Disability and Ageing; 10 December 2025.'
                ),
                'algorithm_description': (
                    'Shahid M, Neal B, Jones A. Uptake of Australia\'s Health '
                    'Star Rating System 2014-2019. Nutrients. 2020;12(6):'
                    '1791. doi:10.3390/nu12061791.'
                ),
                'canadian_validation': (
                    'Hu G, Ahmed M, L\'Abbé MR. Assessing the nutritional '
                    'composition of branded packaged foods in Canada. AJCN '
                    '2023;117(3):553-563.'
                ),
            },
            'action_tips': {
                'reporting': (
                    'When reporting HSR results, always pair the star value '
                    'with the HSRAC category label. Cite the v9 '
                    'Implementation Guide version. For cross-category '
                    'analyses, use a separate validated indicator (Nutri-'
                    'Score, FCS) — HSR is not designed for cross-category '
                    'comparison.'
                ),
            },
        }

    if user_type == 'policy':
        return {
            'score_summary': {
                'title': 'HSR — Front-of-Pack Nutrient Profiling (HSRAC v9)',
                'headline': (
                    f'{star_rating:.1f} / 5 stars in {cat_label} (HSRAC v9).'
                ),
                'units': (
                    f'Stars on a half-star 0.5-5.0 scale. Within the '
                    f'{cat_label} category, higher stars indicate better '
                    f'nutritional quality per the HSRAC v9 algorithm '
                    f'(baseline minus modifying points).'
                ),
                'interpretation': (
                    'Per Shahid et al. 2020 (Nutrients 12:1791), as of 2019, '
                    '40.7% of eligible Australian packaged products carried '
                    'the HSR label. Selective display bias is real: 76.4% of '
                    'displayed products score ≥ 3 stars, vs ~44% population '
                    'average. Categories with highest uptake: Fish (54.5%), '
                    'Vegetables (51.2%); lowest: Sugars/Honey (19.1%).'
                ),
                'mandatory_caveat': (
                    'WITHIN-CATEGORY-ONLY: HSR is NOT designed for cross-'
                    'category comparison. A policy that targets HSR '
                    'improvements must specify per-category thresholds, NOT '
                    'a global star cutoff. HSRAC v9 is a moving target — '
                    'algorithm may revise with Australian Dietary Guideline '
                    'updates; pin to v9 for current decisions.'
                ),
            },
            'policy_context': {
                'title': 'Policy Applications',
                'use_cases': (
                    'Suitable for: (a) front-of-pack labelling schemes '
                    '(adapted from the Australian model), (b) procurement '
                    'thresholds for school / hospital food contracts (within '
                    'each HSRAC category), (c) reformulation incentives '
                    'targeting specific categories with low average HSR.'
                ),
                'category_specificity': (
                    'Six HSRAC v9 categories with different baseline-modifying '
                    'tables: (1) Non-dairy beverages, (1D) Dairy beverages, '
                    '(2) General foods, (2D) Other dairy, (3) Oils and '
                    'spreads, (3D) Cheese. Policy thresholds MUST be set '
                    'per-category, not globally.'
                ),
            },
            'citations': {
                'primary': (
                    'HSRAC. Health Star Rating System Implementation Guide '
                    'v9. 10 December 2025.'
                ),
                'evaluation': (
                    'Shahid et al. Nutrients 2020;12:1791.'
                ),
            },
            'action_tips': {
                'thresholds': (
                    'Set per-category minimum-star thresholds (e.g. ≥3.5 '
                    'stars within Cat 2 for vending machines, ≥4.0 stars '
                    'within Cat 1 for SSB tax exemptions). Reformulation '
                    'targets should align with the modifying-point levers: '
                    'FVNL %, protein, fibre.'
                ),
            },
        }

    # Default: individual audience (consumer-facing)
    return {
        'score_summary': {
            'title': f'Health Star Rating: {star_rating:.1f} ★ — for {cat_label}',
            'headline': (
                f'{band_label}. This is {star_rating:.1f} out of 5 stars '
                f'within the "{cat_label}" food category.'
            ),
            'units': (
                'The Health Star Rating (HSR) scores packaged foods from 0.5 '
                'to 5 stars (half-star steps). More stars means a healthier '
                'choice within the same food category.'
            ),
            'interpretation': (
                f'For {cat_label}, this product\'s {star_rating:.1f}-star '
                f'rating reflects how its baseline nutrients (energy, sat '
                f'fat, sugars, sodium) compare to its protective ones '
                f'(fruit/veg/nuts/legumes, fibre, protein).'
            ),
            'mandatory_caveat': (
                'IMPORTANT: HSR stars only compare products WITHIN the same '
                f'food category. A 3-star "{cat_label}" food cannot be '
                'compared to a 3-star food in a different category — the '
                'scoring tables differ. Always look at the category label '
                'alongside the stars.'
            ),
        },
        'action_tips': {
            'simple_guidance': (
                f'When shopping for "{cat_label}" products, favour higher-'
                f'star options. Don\'t use HSR to compare across different '
                f'product types (e.g. don\'t compare cereal stars to '
                f'beverage stars — the systems are different).'
            ),
        },
    }
