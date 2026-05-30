"""Audience-aware explanation pack for FPED food-group exposure.

Turns an `FpedAggregate` (from `api.services.fped_aggregator`) into the
`fped_component_analysis` block surfaced on recall / scorecard responses:

  - researcher : full 37-component totals + dual-guideline (MyPlate + CFG) gap
                 table + coverage caveat + methodology/citation.
  - individual / clinician : the top 3-5 plain-language gap messages only.

Mirrors the audience-aware convention of `heni_explanations.py`.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from api.services.fped_aggregator import FpedAggregate, aggregate_fped

_METHODOLOGY = (
    "Food-group exposure is computed from the USDA Food Patterns Equivalents "
    "Database (FPED 2017-2018) — the dataset NHANES, the Healthy Eating Index, "
    "and HENI-style burden models use. Neither CNF nor WAFCT publishes Food "
    "Pattern equivalents, so each food (Canadian or West African) is mapped to "
    "its closest US analog via the CNF/WAFCT→FNDDS→FPED bridge; per-100 g "
    "component values are scaled by mass and summed. Foods without a close US "
    "analog (some region-specific dishes) have no profile and are flagged. Gaps "
    "are shown against a ~2000 kcal reference for both USDA MyPlate/DGA "
    "(unit-matched) and an approximation of Canada's Food Guide 2019 plate model."
)

_CAVEATS = [
    "Food Pattern equivalents are borrowed from each food's closest US analog "
    "(USDA FNDDS/FPED); they are most reliable for foods with a close US match "
    "and least reliable for region-specific dishes.",
    "Foods that could not be matched to a US analog are left out and flagged.",
    "Targets assume ~2000 kcal/day and are not energy-adjusted to the individual.",
    "Canada's Food Guide 2019 dropped numeric servings; its targets here are a "
    "derived approximation of the plate model, not official Health Canada amounts.",
]


def _coverage_note(cov: Dict) -> str:
    n_missing = int(cov.get('n_no_profile', 0))
    if n_missing == 0:
        return ''
    return (
        f"Food-group totals reflect {cov.get('coverage_pct_by_mass', 0)}% of the "
        f"day's mass; {n_missing} food(s) could not be matched to a US food-pattern "
        f"analog and are not counted."
    )


# Below this mass-coverage %, unmatched foods (no US analog) distort the
# group totals enough that shortfall claims become unreliable — excluding a food
# can only make a group look LOWER, never higher. So below the threshold we
# suppress "eat more" claims (they may be artifacts) and keep only "go easier on"
# claims (which excluding foods makes conservative), led by the limitation note.
_PARTIAL_COVERAGE_THRESHOLD = 90.0

# The food groups everyday users actually recognise. Technical subgroups
# (dark-green veg, seafood, oils, grain-total) stay in the researcher table.
_CONSUMER_ENCOURAGE = {   # aim for more
    'veg_total_cup': 'vegetables',
    'fruit_total_cup': 'fruit',
    'grain_whole_oz': 'whole grains',
    'protein_total_oz': 'protein foods',
    'dairy_total_cup': 'dairy',
}
_CONSUMER_LIMIT = {       # go easier on
    'grain_refined_oz': 'refined grains',
    'added_sugars_tsp': 'added sugars',
}


def _natural_join(items: List[str]) -> str:
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f'{items[0]} and {items[1]}'
    return ', '.join(items[:-1]) + f', and {items[-1]}'


def _consumer_groups(agg: FpedAggregate):
    """Return (eat_more_labels, eat_less_labels) in plain language, from the
    everyday-recognisable food groups only."""
    eat_more, eat_less = [], []
    for g in agg.gaps:
        if g.component in _CONSUMER_ENCOURAGE and g.myplate_status == 'short':
            eat_more.append(_CONSUMER_ENCOURAGE[g.component])
        elif g.component in _CONSUMER_LIMIT and g.myplate_status == 'over':
            eat_less.append(_CONSUMER_LIMIT[g.component])
    return eat_more, eat_less


# Components used as pattern-driver candidates (the food groups that distinguish
# dietary patterns most). Ordered for stable tie-breaking.
_DRIVER_COMPONENTS = [
    ('veg_total_cup', 'vegetables'),
    ('fruit_total_cup', 'fruit'),
    ('grain_whole_oz', 'whole grains'),
    ('grain_refined_oz', 'refined grains'),
    ('protein_cured_meat_oz', 'processed meat'),
    ('protein_meat_oz', 'red/other meat'),
    ('protein_seafood_total_oz', 'seafood'),
    ('protein_legumes_oz', 'legumes'),
    ('protein_nuts_seeds_oz', 'nuts/seeds'),
    ('dairy_total_cup', 'dairy'),
    ('added_sugars_tsp', 'added sugars'),
    ('oils_g', 'oils'),
]


def fped_pattern_drivers(
    user_foods: List[Dict],
    prototype_foods: List[Dict],
    prototype_n_days: int,
    top_n: int = 3,
) -> List[Dict]:
    """Top food-group drivers of a day's resemblance to a prototype.

    Compares the user's daily FPED profile to the prototype's *average* example
    day (prototype totals / n_example_days) and returns the components with the
    largest absolute delta — the explainable story behind the opaque embedding
    cosine. Interpretive overlay only; does not affect classification.
    """
    if not user_foods or not prototype_foods:
        return []
    user_agg = aggregate_fped(user_foods)
    proto_agg = aggregate_fped(prototype_foods)
    n = max(1, prototype_n_days)
    drivers: List[Tuple[float, Dict]] = []
    units = user_agg.to_dict()['component_units']
    for comp, label in _DRIVER_COMPONENTS:
        u = user_agg.component_totals.get(comp, 0.0)
        p = proto_agg.component_totals.get(comp, 0.0) / n
        delta = u - p
        if abs(delta) < 0.05:
            continue
        drivers.append((abs(delta), {
            'component': comp,
            'label': label,
            'delta': round(delta, 2),
            'unit': units.get(comp, ''),
            'direction': 'more' if delta > 0 else 'less',
        }))
    drivers.sort(key=lambda x: -x[0])
    return [d for _sev, d in drivers[:top_n]]


_COHORT_USUALLY_THRESHOLD = 50.0  # below this % of days meeting a target → "usually short/over"


def build_cohort_explanations(cohort: Dict, user_type: str = 'individual') -> Dict:
    """Return {'fped_cohort_analysis': {...}} for food-group exposure across N recalls.

    `cohort` is the dict from `api.services.fped_cohort.aggregate_cohort`. Researcher/policy
    get the full per-component distribution table; individual/clinician get a plain-language
    "across your N days you were usually short on X / over on Y" read plus per-group
    target-adherence rates.
    """
    n = int(cohort.get('n_recalls', 0))
    components = cohort.get('components', [])
    cov = cohort.get('coverage', {})
    by_comp = {c['component']: c for c in components}

    coverage_note = ''
    if int(cov.get('n_recalls_with_unmatched', 0)) > 0:
        coverage_note = (
            f"{cov['n_recalls_with_unmatched']} of {n} recalls contained foods with no "
            f"food-group profile (mean coverage {cov.get('mean_coverage_pct_by_mass', 0)}% "
            "of mass), so some groups may read lower than reality."
        )

    if user_type in ('researcher', 'policy'):
        block = {
            'title': f'Food-group exposure across {n} recalls (USDA FPED 2017-2018)',
            'n_recalls': n,
            'components': components,
            'coverage': cov,
            'methodology': _METHODOLOGY,
            'caveats': _CAVEATS,
        }
        if coverage_note:
            block['coverage_note'] = coverage_note
        return {'fped_cohort_analysis': block}

    # individual / clinician — plain-language adherence across days.
    short_groups, over_groups, adherence = [], [], []
    for comp, label in _CONSUMER_ENCOURAGE.items():
        c = by_comp.get(comp)
        if not c:
            continue
        pct = float(c['pct_meeting_myplate'])
        adherence.append({'label': label, 'pct_meeting': pct, 'goal': 'more'})
        if pct < _COHORT_USUALLY_THRESHOLD:
            short_groups.append(label)
    for comp, label in _CONSUMER_LIMIT.items():
        c = by_comp.get(comp)
        if not c:
            continue
        pct = float(c['pct_meeting_myplate'])
        adherence.append({'label': label, 'pct_meeting': pct, 'goal': 'less'})
        if pct < _COHORT_USUALLY_THRESHOLD:
            over_groups.append(label)

    if short_groups and over_groups:
        headline = (f"Across your {n} saved days, you were usually short on "
                    f"{_natural_join(short_groups)} and over on {_natural_join(over_groups)}.")
    elif short_groups:
        headline = f"Across your {n} saved days, you were usually short on {_natural_join(short_groups)}."
    elif over_groups:
        headline = f"Across your {n} saved days, you were usually over on {_natural_join(over_groups)}."
    elif n == 0:
        headline = "No saved days yet to read a food-group pattern from."
    else:
        headline = f"Across your {n} saved days, your food groups usually lined up with a balanced plate."

    block = {
        'title': f'Your food groups across {n} days',
        'n_recalls': n,
        'headline': headline,
        'adherence': adherence,   # [{label, pct_meeting, goal}] for everyday groups
        'caveat': (
            'How often your saved days met a balanced ~2000-calorie plate, for the foods '
            'we could map. Guidance, not a diagnosis.'
        ),
    }
    if coverage_note:
        block['coverage_note'] = coverage_note
    return {'fped_cohort_analysis': block}


def build_fped_explanations(agg: FpedAggregate, user_type: str = 'individual') -> Dict:
    """Return {'fped_component_analysis': {...}} for the given audience."""
    cov = agg.coverage
    coverage_note = _coverage_note(cov)

    if user_type in ('researcher', 'policy'):
        block = {
            'title': 'Food-group exposure (USDA FPED 2017-2018)',
            'component_totals': {k: round(v, 3) for k, v in agg.component_totals.items()},
            'component_units': agg.to_dict()['component_units'],
            'gaps': [g.to_dict() for g in agg.gaps],
            'coverage': cov,
            'methodology': _METHODOLOGY,
            'caveats': _CAVEATS,
        }
        if coverage_note:
            block['coverage_note'] = coverage_note
        return {'fped_component_analysis': block}

    # individual / clinician — plain-language, grouped, jargon-free.
    eat_more, eat_less = _consumer_groups(agg)
    partial = float(cov.get('coverage_pct_by_mass', 100.0)) < _PARTIAL_COVERAGE_THRESHOLD

    if partial:
        # Unmatched foods understate groups, so "light on X" claims may be artifacts.
        # Keep only the conservative "heavy on" claims; lead with the limitation.
        eat_more = []
        n_excl = int(cov.get('n_no_profile', 0))
        partial_note = (
            f"We couldn't match {n_excl} of your foods to a food group, so "
            f"this view covers about {round(cov.get('coverage_pct_by_mass', 0))}% of "
            "what you ate. Some groups may look lower here than they really are."
        )
    else:
        partial_note = ''

    if eat_more and eat_less:
        headline = (f"Compared with a balanced plate, today was light on "
                    f"{_natural_join(eat_more)} and heavy on {_natural_join(eat_less)}.")
    elif eat_more:
        headline = f"Compared with a balanced plate, today was light on {_natural_join(eat_more)}."
    elif eat_less:
        headline = f"Compared with a balanced plate, today was heavy on {_natural_join(eat_less)}."
    elif partial:
        headline = "We could only map some of your foods, so there's not enough to read the food-group balance."
    else:
        headline = "Today's food groups line up well with a balanced plate."

    block = {
        'title': 'How your day compares to a balanced plate',
        'headline': headline,
        'eat_more': eat_more,   # encouraged groups you were light on
        'eat_less': eat_less,   # groups to go easier on
        'caveat': (
            'A rough food-group read for the foods we could map, against a '
            'balanced ~2000-calorie day. Guidance, not a diagnosis.'
        ),
    }
    if partial_note:
        block['coverage_note'] = partial_note
    elif coverage_note:
        block['coverage_note'] = coverage_note
    return {'fped_component_analysis': block}
