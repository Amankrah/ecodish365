"""Packaged-food inferred-composition caveats (PKG-IMG-1 Phase 2.x).

When a scoring request carries ``decomposition_provenance='packaged_food_inferred'``,
merge indicator-specific caveat copy into the existing explanations block —
parallel to ``wafct_caveat.py`` and the dietary-pattern classifier.

Regulation only requires descending-mass-order on labels; per-ingredient masses
are LLM-inferred from ordering + NF panel macros, not measured.
"""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

Indicator = Literal['hefi', 'heni', 'hsr', 'fcs', 'environmental']
UserType = Literal['individual', 'researcher', 'policy']

_VALID_PROVENANCE = frozenset({'packaged_food_inferred'})


def parse_decomposition_provenance(raw: object) -> Optional[str]:
    """Whitelist parser shared by all scorer endpoints."""
    if raw is None:
        return None
    dp = str(raw).strip().lower()
    return dp if dp in _VALID_PROVENANCE else None


_INDIVIDUAL = {
    'hefi': (
        'These foods came from a packaged product read from a nutrition label. '
        'Ingredient amounts are estimated from the label order and nutrition '
        'facts, not weighed. Treat the healthy eating score as a rough guide '
        'for one day, not your usual pattern.'
    ),
    'heni': (
        'These foods came from a packaged product read from a nutrition label. '
        'Ingredient amounts are estimated, not weighed. Health impact minutes '
        'are best used to compare similar products, not as a precise intake '
        'record.'
    ),
    'hsr': (
        'When several packaged ingredients are listed together, each product '
        'is still rated within its own category. A combined average is only a '
        'rough snapshot, not a daily star rating.'
    ),
    'fcs': (
        'Food Compass scores here use estimated ingredient amounts from a '
        'label breakdown. Processing level and ingredient flags may shift if '
        'the breakdown is wrong.'
    ),
    'environmental': (
        'Environmental impacts use estimated ingredient amounts from a label '
        'breakdown. If the breakdown is off, the climate, land, and water '
        'estimates will shift too.'
    ),
}

_RESEARCHER = {
    'hefi': (
        'INFERRED-COMPOSITION CAVEAT (PKG-IMG-1 Phase 2): ingredient masses '
        'originate from LLM label extraction + constrained decomposer '
        '(descending-mass-order, NF macro reconciliation ±10 %, mass '
        'conservation ±5 % of net weight). HEFI C9 still uses CNF total-sugars '
        'proxy where free-sugars supplement is absent. Not a 24-h AMPM recall.'
    ),
    'heni': (
        'INFERRED-COMPOSITION CAVEAT (PKG-IMG-1 Phase 2): HENI risk-factor '
        'masses derive from inferred composition, not FPED-measured WWEIA '
        'servings. Marginality scope limit (Stylianou 2021 Discussion pp. '
        '622–624) still applies.'
    ),
    'hsr': (
        'INFERRED-COMPOSITION CAVEAT (PKG-IMG-1 Phase 2): per-food HSR uses '
        'each food\'s own HSRAC v9 category at recall portion sizes. '
        'Combined-meal HSR is omitted for multi-food recall batches '
        '(SCORECARD-1).'
    ),
    'fcs': (
        'INFERRED-COMPOSITION CAVEAT (PKG-IMG-1 Phase 2): FCS-10 ingredient '
        'flags and NOVA classification inherit decomposition error. Validate '
        'composition table before citing FCS on packaged products.'
    ),
    'environmental': (
        'INFERRED-COMPOSITION CAVEAT (PKG-IMG-1 Phase 2): Tier-α/β/γ LCA '
        'routing uses CNF FoodIDs from inferred composition. Matcher/decomposer '
        'audit trails still apply per ingredient.'
    ),
}


def build_packaged_food_caveat(
    indicator: Indicator,
    user_type: UserType = 'individual',
    *,
    decomposition_provenance: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a caveat dict to merge into explanations. Empty when not inferred."""
    if decomposition_provenance != 'packaged_food_inferred':
        return {}

    msg = _RESEARCHER[indicator] if user_type != 'individual' else _INDIVIDUAL[indicator]
    return {
        'inferred_composition_caveat': {
            'title': 'Scanned packaged product',
            'message': msg,
        },
    }
