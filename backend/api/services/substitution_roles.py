"""Functional roles for ingredients — SUBST-1 Phase 4."""
from __future__ import annotations

import re
from typing import Optional

ROLE_STAPLE = 'staple'
ROLE_PROTEIN = 'protein'
ROLE_FAT = 'fat'
ROLE_VEGETABLE = 'vegetable'
ROLE_AROMATIC = 'aromatic'
ROLE_SAUCE = 'sauce'
ROLE_BEVERAGE = 'beverage'
ROLE_SWEETENER = 'sweetener'
ROLE_SEASONING = 'seasoning'
ROLE_OTHER = 'other'

_RX_STAPLE = re.compile(
    r'\b(rice|bread|pasta|noodle|couscous|millet|sorghum|maize|corn|flour|'
    r'potato|yam|plantain|cassava|fufu|banku|kenkey)\b', re.I,
)
_RX_PROTEIN = re.compile(
    r'\b(beef|pork|chicken|turkey|lamb|fish|eel|salmon|tuna|shrimp|prawn|'
    r'egg|tofu|lentil|bean|peanut|meat|sausage|bacon)\b', re.I,
)
_RX_FAT = re.compile(
    r'\b(oil|shortening|margarine|butter|lard|ghee|clarified butter|palm oil)\b',
    re.I,
)
_RX_LOW_FAT_FOOD = re.compile(
    r'\b(low fat|low-fat|nonfat|non-fat|fat free|fat-free|0-0\.5%)\b',
    re.I,
)
_RX_AROMATIC = re.compile(r'\b(onion|garlic|ginger|shallot|leek|chive)\b', re.I)
_RX_SAUCE = re.compile(r'\b(tomato|paste|sauce|stock|broth|gravy)\b', re.I)
_RX_BEVERAGE = re.compile(r'\b(water|juice|cola|soda|tea|coffee|milk|beverage)\b', re.I)
_RX_SWEETENER = re.compile(r'\b(sugar|honey|syrup|molasses)\b', re.I)
_RX_SEASONING = re.compile(r'\b(salt|pepper|spice|curry|seasoning)\b', re.I)
# Primary seasonings only — not "Taro, with salt" or "Tomato paste, without salt".
_RX_PRIMARY_SEASONING = re.compile(
    r'^(Salt|Pepper,|Spice|Seasoning|Curry powder|Yeast|Baking powder|Baking soda)\b',
    re.I,
)
_RX_VEG = re.compile(
    r'\b(eggplant|aubergine|garden egg|okra|pepper|carrot|spinach|lettuce|'
    r'cabbage|cucumber|squash|vegetable|tomato)\b', re.I,
)


def is_primary_seasoning(description: str) -> bool:
    """True when the food *is* a seasoning (salt, spice), not a food modified with salt."""
    d = (description or '').strip()
    return bool(_RX_PRIMARY_SEASONING.search(d))


def infer_functional_role(description: str) -> str:
    """Classify an ingredient's culinary role from its food description."""
    d = description or ''
    if is_primary_seasoning(d):
        return ROLE_SEASONING
    if _RX_BEVERAGE.search(d) and not _RX_FAT.search(d):
        return ROLE_BEVERAGE
    if _RX_SWEETENER.search(d):
        return ROLE_SWEETENER
    if _RX_FAT.search(d) and not _RX_LOW_FAT_FOOD.search(d):
        return ROLE_FAT
    if _RX_PROTEIN.search(d):
        return ROLE_PROTEIN
    if _RX_STAPLE.search(d):
        return ROLE_STAPLE
    if _RX_AROMATIC.search(d):
        return ROLE_AROMATIC
    if _RX_SAUCE.search(d):
        return ROLE_SAUCE
    if _RX_VEG.search(d):
        return ROLE_VEGETABLE
    return ROLE_OTHER


def same_functional_role(
    original_description: str,
    replacement_description: str,
) -> bool:
    a = infer_functional_role(original_description)
    b = infer_functional_role(replacement_description)
    if a == ROLE_OTHER or b == ROLE_OTHER:
        return True
    return a == b
