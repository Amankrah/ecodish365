"""Curated substitution rules for SUBST-1 Phase 1.

Rules follow Scenario S5 (`scenarios.md`): beef→legumes, milk→soy, cola→water,
white bread→whole wheat. Each rule maps a source ingredient pattern to a
canonical CNF target food with a fixed FoodID resolved at rule-authoring time.

Phase 2 adds nutrient-discovery-driven candidates; Phase 1 is rule-only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional, Pattern, Sequence


@dataclass(frozen=True)
class SubstitutionRule:
    """One curated swap pattern."""

    id: str
    label: str
    rationale: str
    purposes: FrozenSet[str]
    target_food_id: int
    target_food_description: str
    # Match criteria — at least one must be satisfied alongside mass > 0.
    source_group_ids: FrozenSet[int] = field(default_factory=frozenset)
    source_group_names: FrozenSet[str] = field(default_factory=frozenset)
    source_description_patterns: Sequence[Pattern[str]] = field(default_factory=tuple)
    # When set, ingredient description must match one of these (case-insensitive).
    source_description_exclude_patterns: Sequence[Pattern[str]] = field(default_factory=tuple)


def _rx(pattern: str) -> Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# Canonical CNF FoodIDs (resolved against raw_cnf/FOOD_NAME.csv, 2026-05-26).
_LENTILS_RAW = 3392
_SOY_ENRICHED = 501528
_WATER_MUNICIPAL = 2933
_WW_BREAD = 4067

SUBSTITUTION_RULES: List[SubstitutionRule] = [
    SubstitutionRule(
        id='beef_to_legumes',
        label='Replace beef with lentils',
        rationale=(
            'Legumes provide plant protein and fibre with lower saturated fat '
            'than beef — a win-win in HEFI and environmental modelling (S5).'
        ),
        purposes=frozenset({'general_health', 'lower_sat_fat', 'higher_fibre', 'sustainability'}),
        target_food_id=_LENTILS_RAW,
        target_food_description='Lentils, raw',
        source_group_ids=frozenset({13}),
        source_group_names=frozenset({'Beef Products'}),
    ),
    SubstitutionRule(
        id='milk_to_soy',
        label="Replace cow's milk with fortified soy beverage",
        rationale=(
            'Fortified soy beverage offers comparable protein with less '
            'saturated fat — common reformulation path for dairy beverages (S5).'
        ),
        purposes=frozenset({'general_health', 'lower_sat_fat'}),
        target_food_id=_SOY_ENRICHED,
        target_food_description='Plant-based beverage, soy, enriched, all flavours, low fat',
        source_group_ids=frozenset({1}),
        source_group_names=frozenset({'Dairy and Egg Products'}),
        source_description_patterns=(_rx(r'\bmilk\b'),),
        source_description_exclude_patterns=(
            _rx(r'chocolate'),
            _rx(r'plant[- ]based'),
            _rx(r'\bsoy\b'),
            _rx(r'\balmond\b'),
            _rx(r'\boat\b'),
            _rx(r'cheese'),
            _rx(r'cream'),
            _rx(r'yogurt'),
            _rx(r'butter'),
        ),
    ),
    SubstitutionRule(
        id='cola_to_water',
        label='Replace cola with water',
        rationale=(
            'Swapping sugar-sweetened beverages for water removes added sugars '
            'and sodium — one of the strongest single-ingredient HEFI/HSR wins (S5).'
        ),
        purposes=frozenset({'general_health', 'lower_sodium', 'diabetes_friendly'}),
        target_food_id=_WATER_MUNICIPAL,
        target_food_description='Water, municipal',
        source_description_patterns=(
            _rx(r'\bcola\b'),
            _rx(r'carbonated.*cola'),
            _rx(r'soft drink'),
            _rx(r'\bsoda\b'),
            _rx(r'sugar[- ]sweetened'),
        ),
    ),
    SubstitutionRule(
        id='white_to_whole_wheat',
        label='Replace white bread with whole wheat bread',
        rationale=(
            'Whole-grain bread adds dietary fibre and can improve HEFI whole-grain '
            'and fibre components relative to refined white bread (S5).'
        ),
        purposes=frozenset({'general_health', 'higher_fibre'}),
        target_food_id=_WW_BREAD,
        target_food_description='Bread, whole wheat, commercial',
        source_group_ids=frozenset({18}),
        source_group_names=frozenset({'Baked Products'}),
        source_description_patterns=(
            _rx(r'bread.*white'),
            _rx(r'white.*bread'),
        ),
        source_description_exclude_patterns=(
            _rx(r'whole[- ]?wheat'),
            _rx(r'whole[- ]?grain'),
        ),
    ),
]

RULES_BY_ID = {r.id: r for r in SUBSTITUTION_RULES}

PURPOSE_LABELS = {
    'general_health': 'General health (HEFI-weighted)',
    'lower_sodium': 'Lower sodium',
    'higher_fibre': 'Higher fibre',
    'higher_protein': 'Higher protein',
    'lower_sat_fat': 'Lower saturated fat',
    'diabetes_friendly': 'Diabetes-friendly (lower sugars)',
    'sustainability': 'Lower environmental impact',
}


def rules_for_purpose(purpose: str) -> List[SubstitutionRule]:
    """Return rules applicable to a scoring purpose."""
    if purpose == 'general_health':
        return list(SUBSTITUTION_RULES)
    return [r for r in SUBSTITUTION_RULES if purpose in r.purposes]


def ingredient_matches_rule(
    *,
    food_id: int,
    food_description: str,
    food_group: str,
    food_group_id: Optional[int],
    rule: SubstitutionRule,
) -> bool:
    """Return True if this ingredient slot matches the rule source pattern."""
    if food_id == rule.target_food_id:
        return False

    desc = (food_description or '').strip()
    group = (food_group or '').strip()

    group_ok = False
    if rule.source_group_ids and food_group_id is not None:
        group_ok = int(food_group_id) in rule.source_group_ids
    if not group_ok and rule.source_group_names and group:
        group_ok = group in rule.source_group_names

    desc_ok = False
    if rule.source_description_patterns:
        for pat in rule.source_description_patterns:
            if pat.search(desc):
                desc_ok = True
                break
    elif not rule.source_group_ids and not rule.source_group_names:
        desc_ok = True

    if rule.source_description_exclude_patterns:
        for pat in rule.source_description_exclude_patterns:
            if pat.search(desc):
                return False

    # Require group match when groups specified; description match when patterns specified.
    if rule.source_group_ids or rule.source_group_names:
        if rule.source_description_patterns:
            return group_ok and desc_ok
        return group_ok

    return desc_ok
