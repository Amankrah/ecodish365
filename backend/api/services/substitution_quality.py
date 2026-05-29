"""Post-scoring quality gates for SUBST-1 substitution suggestions.

Candidates pass culinary plausibility first; this module rejects swaps that score
well on FCS but fail basic nutrition coherence (e.g. whole egg → yolk at equal
mass, lean chicken → skin-on thigh).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Purposes where increasing saturated fat is never acceptable.
_SAT_FAT_PURPOSES = frozenset({'general_health', 'lower_sat_fat', 'diabetes_friendly'})

# Discovery sources held to a higher bar than curated S5 rules.
_DISCOVERY_SOURCES = frozenset({
    'matcher_alternative',
    'nutrient_discovery',
    'wafct_recipe',
    'combined',
    'reformulation',
})

# Minimum FCS improvement required of matcher/discovery candidates on
# general_health (curated rules exempt). FCS is 0-100; HEFI's prior bar was
# 0.2/80 ≈ 0.25 % of max — the FCS equivalent is ≈ 0.25 points.
MIN_DISCOVERY_FCS_DELTA = 0.25

_RX_FLAVOURED_YOGURT = re.compile(
    r'fruit flavou?red|flavou?red.*yog|yog.*flavou?red|vanilla|strawberr|peach|blueberr',
    re.I,
)
_RX_YOGURT = re.compile(r'yog(?:ourt|urt)', re.I)
_RX_PLAIN_DAIRY = re.compile(r'\bplain\b|unflavou?red|\bnatural\b', re.I)


def _swap_adds_fped_sugars(fped_deltas: Optional[Dict[str, Any]]) -> bool:
    if not fped_deltas:
        return False
    for ch in fped_deltas.get('changed') or []:
        if ch.get('component') == 'added_sugars_tsp' and float(ch.get('delta', 0.0)) > 0.05:
            return True
    return False


def _is_plain_to_flavoured_yogurt(swaps: List[Dict[str, Any]]) -> bool:
    for sw in swaps:
        orig = (sw.get('original') or {}).get('food_description', '')
        repl = (sw.get('replacement') or {}).get('food_description', '')
        if not _RX_YOGURT.search(orig) or not _RX_YOGURT.search(repl):
            continue
        orig_plain = bool(_RX_PLAIN_DAIRY.search(orig)) and not _RX_FLAVOURED_YOGURT.search(orig)
        repl_flavoured = bool(_RX_FLAVOURED_YOGURT.search(repl))
        if orig_plain and repl_flavoured:
            return True
    return False


def swap_passes_quality_gate(
    evaluation: Dict[str, Any],
    *,
    purpose: str,
    candidate_source: str,
    swaps: List[Dict[str, Any]],
    fped_deltas: Optional[Dict[str, Any]] = None,
) -> bool:
    """Return False when a scored swap should not be shown despite positive rank_score."""
    nutrients = evaluation.get('nutrients') or {}
    sat_d = float(nutrients.get('sat_fat_g', {}).get('diff', 0.0))
    sodium_d = float(nutrients.get('sodium_mg', {}).get('diff', 0.0))
    fcs_d = float((evaluation.get('fcs') or {}).get('delta', 0.0))

    swapped_mass = sum(
        float(sw.get('original', {}).get('mass_g', 0.0) or 0.0)
        for sw in swaps
    ) or 100.0

    if purpose == 'lower_sat_fat' and sat_d > 0.25:
        return False

    if purpose == 'lower_sodium' and sodium_d > 25.0:
        return False

    if purpose in _SAT_FAT_PURPOSES:
        # Absolute cap: >2 g sat fat added on a single-slot swap is not "healthier".
        if sat_d > 2.0:
            return False
        # Scale with portion: >1.5% of swapped mass as added sat fat is implausible.
        if sat_d > max(1.5, swapped_mass * 0.015):
            return False

    if candidate_source in _DISCOVERY_SOURCES:
        if purpose == 'general_health':
            if fcs_d <= 0.0:
                return False
            if fcs_d < MIN_DISCOVERY_FCS_DELTA:
                return False
            # Tiny FCS win bought with substantial sat fat (egg→yolk pattern).
            if sat_d > 1.0 and fcs_d < sat_d * 0.4:
                return False

    if purpose in ('general_health', 'diabetes_friendly'):
        if candidate_source in _DISCOVERY_SOURCES or candidate_source == 'reformulation':
            if _is_plain_to_flavoured_yogurt(swaps):
                return False
            if _swap_adds_fped_sugars(fped_deltas):
                return False

    if candidate_source == 'reformulation' and purpose == 'general_health':
        if sat_d > 1.0 and fcs_d < 1.0:
            return False

    return True
