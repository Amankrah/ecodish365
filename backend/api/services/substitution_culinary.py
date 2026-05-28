"""Culinary plausibility guards for SUBST-1 substitution discovery.

Nutrient-range search can surface foods in the same CNF group that are not
realistic substitutes (e.g. tomato → dried cloud-ear mushroom). These checks
filter obvious mismatches before ranking.
"""
from __future__ import annotations

import re
from typing import Optional

from api.services.substitution_roles import (
    ROLE_SEASONING,
    ROLE_SWEETENER,
    infer_functional_role,
    is_primary_seasoning,
)

_DRIED = re.compile(
    r'\b(dried|dehydrated|powder|flour|meal\b|flakes\b)\b',
    re.IGNORECASE,
)
_FRESH_PREP = re.compile(
    r'\b(boiled|ripe|raw|fresh|cooked|drained|baked|broiled|steamed|'
    r'roasted|grilled|fried|stewed|simmered|without salt)\b',
    re.IGNORECASE,
)
_MUSHROOM = re.compile(r'\b(mushroom|fungi|cloud ear|shiitake|oyster mushroom)\b', re.I)
_VEG_FRUIT = re.compile(
    r'\b(tomato|onion|eggplant|aubergine|pepper|squash|cucumber|lettuce|'
    r'carrot|celery|zucchini|courgette|garden egg|okra|baobab)\b',
    re.IGNORECASE,
)
_OIL = re.compile(r'\b(oil|fat|shortening|margarine|butter)\b', re.I)
_FISH = re.compile(r'\b(fish|eel|salmon|tuna|cod|haddock|sardine|tilapia)\b', re.I)
_RICE = re.compile(r'\b(rice|couscous|bulgur|quinoa|millet|maize meal)\b', re.I)


def _is_dried(description: str) -> bool:
    return bool(_DRIED.search(description or ''))


def _is_fresh_prep(description: str) -> bool:
    return bool(_FRESH_PREP.search(description or ''))


def culinary_swap_plausible(
    original_description: str,
    replacement_description: str,
    *,
    original_mass_g: Optional[float] = None,
) -> bool:
    """Return False when a swap is clearly not a realistic culinary substitute."""
    orig = original_description or ''
    repl = replacement_description or ''

    # Dried ↔ fresh/boiled is almost never a 1:1 mass swap.
    orig_dried = _is_dried(orig)
    repl_dried = _is_dried(repl)
    if orig_dried != repl_dried:
        return False

    if _is_fresh_prep(orig) and repl_dried:
        return False

    # Mushrooms are not stand-ins for fresh vegetables in a stew.
    if _MUSHROOM.search(repl) and _VEG_FRUIT.search(orig) and not _MUSHROOM.search(orig):
        return False

    # Leafy/powder WAFCT items are not stand-ins for whole boiled vegetables.
    if repl_dried and _VEG_FRUIT.search(orig):
        if re.search(r'\b(leaves|leaf|baobab|powder)\b', repl, re.I):
            return False

    # Oils can swap with oils; not with non-oils (matcher handles most cases).
    if _OIL.search(orig) and not _OIL.search(repl):
        return False
    if _OIL.search(repl) and not _OIL.search(orig):
        return False

    # Fish swaps should stay in finfish/shellfish space.
    if _FISH.search(orig) and not _FISH.search(repl):
        return False

    # Rice/grain staples should stay in the grain category.
    if _RICE.search(orig) and not _RICE.search(repl):
        return False

    # Seasonings/sweeteners must not swap into whole foods (or vice versa).
    orig_role = infer_functional_role(orig)
    repl_role = infer_functional_role(repl)
    _CLOSED_ROLES = {ROLE_SEASONING, ROLE_SWEETENER}
    if orig_role in _CLOSED_ROLES and repl_role != orig_role:
        return False
    if repl_role in _CLOSED_ROLES and orig_role != repl_role:
        return False
    # Extra guard: primary salt/spice rows never become non-seasonings.
    if is_primary_seasoning(orig) and not is_primary_seasoning(repl):
        return False

    return True


def extreme_nutrient_swing(
    nutrient_delta: dict,
    swapped_mass_g: float,
) -> bool:
    """True when nutrient deltas are implausible for the swapped mass (g)."""
    if swapped_mass_g <= 0:
        return False
    fibre = abs(nutrient_delta.get('fibre_g', {}).get('diff', 0.0))
    sodium = abs(nutrient_delta.get('sodium_mg', {}).get('diff', 0.0))
    # >25% fibre by mass, or >3 mg Na per gram swapped, suggests wrong food form.
    if fibre / swapped_mass_g > 0.25:
        return True
    if sodium / swapped_mass_g > 3.0:
        return True
    return False
