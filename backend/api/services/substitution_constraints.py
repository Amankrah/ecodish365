"""Dietary constraints for SUBST-1 Phase 3+ substitution engine."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from api.services.substitution_roles import same_functional_role as roles_match

# CNF FoodGroupIDs treated as non-vegetarian targets.
MEAT_GROUP_IDS: Set[int] = {5, 10, 13, 15, 17, 7, 21}

ALLERGEN_PATTERNS: Dict[str, re.Pattern[str]] = {
    'milk': re.compile(r'\bmilk\b|dairy|casein|whey|lactose', re.I),
    'egg': re.compile(r'\begg\b|albumin|ovalbumin', re.I),
    'peanut': re.compile(r'peanut|groundnut|arachis', re.I),
    'tree_nut': re.compile(r'almond|cashew|walnut|pecan|hazelnut|pistachio|macadamia', re.I),
    'wheat': re.compile(r'\bwheat\b|gluten|semolina|spelt', re.I),
    'soy': re.compile(r'\bsoy\b|soya|tofu|edamame', re.I),
    'fish': re.compile(r'\bfish\b|salmon|tuna|cod|haddock|trout|sardine|anchov', re.I),
    'shellfish': re.compile(r'shrimp|prawn|crab|lobster|scallop|mussel|oyster|clam', re.I),
    'sesame': re.compile(r'sesame|tahini', re.I),
}


def parse_extended_constraints(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge Phase 3 constraint fields into a normalized dict."""
    base = {
        'exclude_food_ids': set(),
        'source_filter': None,
        'max_swaps': 1,
        'vegetarian': False,
        'same_functional_role': False,
        'exclude_allergens': [],
        'cultural_context': None,
    }
    if not raw or not isinstance(raw, dict):
        return base

    exclude = raw.get('exclude_food_ids') or []
    try:
        base['exclude_food_ids'] = {int(x) for x in exclude}
    except (TypeError, ValueError):
        pass

    source = raw.get('source_filter')
    if source in ('cnf', 'wafct'):
        base['source_filter'] = source

    try:
        base['max_swaps'] = max(1, min(int(raw.get('max_swaps', 1)), 4))
    except (TypeError, ValueError):
        pass

    base['vegetarian'] = bool(raw.get('vegetarian', False))
    base['same_functional_role'] = bool(raw.get('same_functional_role', False))

    ctx = raw.get('cultural_context')
    if ctx in ('west_africa', 'north_america', 'any'):
        base['cultural_context'] = ctx

    allergens = raw.get('exclude_allergens') or []
    if isinstance(allergens, list):
        base['exclude_allergens'] = [str(a).lower() for a in allergens if a]

    return base


def _description_matches_allergen(description: str, allergen: str) -> bool:
    pat = ALLERGEN_PATTERNS.get(allergen)
    if not pat:
        return allergen.lower() in (description or '').lower()
    return bool(pat.search(description or ''))


def replacement_allowed(
    *,
    replacement_food_id: int,
    replacement_description: str,
    replacement_group_id: Optional[int],
    original_group_id: Optional[int],
    original_description: str = '',
    constraints: Dict[str, Any],
) -> bool:
    """Return False if the replacement violates Phase 3 constraints."""
    if replacement_food_id in constraints.get('exclude_food_ids', set()):
        return False

    if constraints.get('vegetarian'):
        if replacement_group_id is not None and int(replacement_group_id) in MEAT_GROUP_IDS:
            return False
        desc = (replacement_description or '').lower()
        if re.search(r'\b(beef|pork|chicken|turkey|lamb|bacon|ham|sausage|fish|salmon|tuna)\b', desc):
            return False

    for allergen in constraints.get('exclude_allergens', []):
        if _description_matches_allergen(replacement_description, allergen):
            return False

    if constraints.get('same_functional_role'):
        if not roles_match(original_description, replacement_description):
            return False

    return True
