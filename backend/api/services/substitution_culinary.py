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
_OIL = re.compile(
    r'\b(oil|shortening|margarine|butter|ghee|clarified butter|palm oil|lard)\b',
    re.I,
)
_LOW_FAT_LABEL = re.compile(r'\b(low fat|low-fat|nonfat|non-fat|fat free|fat-free)\b', re.I)
_FISH = re.compile(r'\b(fish|eel|salmon|tuna|cod|haddock|sardine|tilapia)\b', re.I)
_RICE = re.compile(r'\b(rice|couscous|bulgur|quinoa|millet|maize meal)\b', re.I)

_RX_EGG = re.compile(r'\begg\b', re.I)
_RX_EGG_YOLK = re.compile(r'\byolk\b', re.I)
_RX_EGG_WHITE = re.compile(r'\begg white\b|\bwhites,\s', re.I)
_RX_EGG_WHOLE = re.compile(r'\bwhole\b', re.I)
_RX_MEAT_AND_SKIN = re.compile(r'meat and skin|with skin', re.I)
_RX_MEAT_LEAN = re.compile(r',\s*meat,\s*|,\s*meat\s+cooked', re.I)

_RX_YOGURT = re.compile(r'yog(?:ourt|urt)', re.I)
_RX_FLAVOURED_YOGURT = re.compile(
    r'fruit flavou?red|flavou?red.*yog|yog.*flavou?red|vanilla|strawberr|peach|blueberr',
    re.I,
)
_RX_PLAIN_DAIRY = re.compile(r'\bplain\b|unflavou?red|\bnatural\b', re.I)


def dairy_yogurt_swap_plausible(original_description: str, replacement_description: str) -> bool:
    """Plain yogurt is not swapped for sweetened/flavoured variants at equal mass."""
    orig = original_description or ''
    repl = replacement_description or ''
    if not _RX_YOGURT.search(orig) or not _RX_YOGURT.search(repl):
        return True
    orig_plain = bool(_RX_PLAIN_DAIRY.search(orig)) and not _RX_FLAVOURED_YOGURT.search(orig)
    repl_flavoured = bool(_RX_FLAVOURED_YOGURT.search(repl))
    if orig_plain and repl_flavoured:
        return False
    return True


def _egg_form(description: str) -> Optional[str]:
    """whole | yolk | white | None."""
    d = description or ''
    if not _RX_EGG.search(d):
        return None
    if _RX_EGG_YOLK.search(d):
        return 'yolk'
    if _RX_EGG_WHITE.search(d):
        return 'white'
    if _RX_EGG_WHOLE.search(d):
        return 'whole'
    return 'whole'


def _poultry_leanness(description: str) -> Optional[str]:
    """lean | with_skin | None for poultry cuts."""
    d = (description or '').lower()
    if not re.search(r'\b(chicken|turkey|broiler|thigh|breast|poultry)\b', d):
        return None
    if _RX_MEAT_AND_SKIN.search(d):
        return 'with_skin'
    if _RX_MEAT_LEAN.search(d):
        return 'lean'
    return None


def anatomical_swap_plausible(original_description: str, replacement_description: str) -> bool:
    """Block part/cut mismatches that are not 1:1 culinary substitutes at equal mass."""
    orig = original_description or ''
    repl = replacement_description or ''

    o_egg = _egg_form(orig)
    r_egg = _egg_form(repl)
    if o_egg and r_egg and o_egg != r_egg:
        return False

    o_bird = _poultry_leanness(orig)
    r_bird = _poultry_leanness(repl)
    if o_bird == 'lean' and r_bird == 'with_skin':
        return False

    return True


def _is_dried(description: str) -> bool:
    return bool(_DRIED.search(description or ''))


def _is_fresh_prep(description: str) -> bool:
    return bool(_FRESH_PREP.search(description or ''))


# Strategy D — structured prep-state gate. Thermal classes for the raw↔cooked
# block; preservation pairs that count as a hard cross.
_RAW_THERMAL = frozenset({'raw'})
_COOKED_THERMAL = frozenset({
    'boiled', 'fried', 'baked', 'roasted', 'stewed', 'grilled',
    'steamed', 'poached', 'scrambled', 'heated', 'cooked',
    'braised', 'toasted', 'sauteed', 'microwaved', 'blanched',
    'barbecued', 'stir_fried', 'broiled', 'reheated',
})
# Preservation pairs that are NOT 1:1 culinary substitutes at equal mass
# (the existing dried↔fresh regex covers some of these; the structured
# tag also catches cases where the regex misses, e.g. "Sweets, pie
# fillings, canned apple").
_PRESERVATION_HARD_CROSSES = frozenset({
    ('fresh', 'canned'), ('canned', 'fresh'),
    ('fresh', 'dried'), ('dried', 'fresh'),
    ('fresh', 'dehydrated'), ('dehydrated', 'fresh'),
    ('fresh', 'condensed'), ('condensed', 'fresh'),
    ('fresh', 'fermented'), ('fermented', 'fresh'),
})


def _prep_state_swap_plausible(
    original_food_id: Optional[int],
    replacement_food_id: Optional[int],
) -> bool:
    """Structured prep-state gate (Strategy D).

    Returns True (= "swap is allowed") when:
      - either id is missing (caller has no FoodID context),
      - either id is unlabeled (the tagger hasn't classified it — don't
        block; let the existing regex gates decide),
      - the structured tag shows no cross-axis conflict.

    Returns False ONLY when both FoodIDs are labeled AND the tags show a
    raw↔cooked or fresh↔(canned/dried/dehydrated/condensed/fermented) cross.
    """
    if original_food_id is None or replacement_food_id is None:
        return True
    # Lazy import — cnf_prep_state requires Django setup; guard against
    # import-time crashes in lightweight contexts (e.g. unit tests that
    # don't load Django).
    try:
        from api.services.cnf_prep_state import prep_state_of
    except Exception:  # noqa: BLE001
        return True

    orig_tag = prep_state_of(int(original_food_id))
    repl_tag = prep_state_of(int(replacement_food_id))
    if orig_tag is None or repl_tag is None:
        return True

    # Thermal-axis cross: raw ↔ any cooked verb.
    if (orig_tag.thermal_state in _RAW_THERMAL and repl_tag.thermal_state in _COOKED_THERMAL) \
            or (orig_tag.thermal_state in _COOKED_THERMAL and repl_tag.thermal_state in _RAW_THERMAL):
        return False

    # Preservation-axis hard crosses.
    if (orig_tag.preservation_state, repl_tag.preservation_state) in _PRESERVATION_HARD_CROSSES:
        return False

    return True


def culinary_swap_plausible(
    original_description: str,
    replacement_description: str,
    *,
    original_mass_g: Optional[float] = None,
    original_food_id: Optional[int] = None,
    replacement_food_id: Optional[int] = None,
) -> bool:
    """Return False when a swap is clearly not a realistic culinary substitute.

    Strategy D (2026-05-30): when ``original_food_id`` and ``replacement_food_id``
    are provided AND both have a structured prep-state tag from
    ``api.services.cnf_prep_state``, additionally reject crosses on the
    thermal and preservation axes that the existing regex-on-description
    gate doesn't catch:
      - raw thermal swapped against any cooked verb → BLOCKED (food safety:
        the Phase 1 substitution probe surfaced fried-chicken → raw-chicken
        as a real production behaviour).
      - fresh ↔ canned/dried/dehydrated/condensed → BLOCKED (mass density
        and Na/sugar profiles diverge; "lower_sodium" purpose for canned
        carrot → raw celeriac is a real defect).
      - fermented ↔ non-fermented → BLOCKED (yogurt ≠ unfermented milk).
    Falls back to the existing regex behaviour when either id is missing or
    unlabeled.
    """
    orig = original_description or ''
    repl = replacement_description or ''

    # Strategy D: structured prep-state gate (uses the tagger output when
    # both foods have FoodIDs that the tagger has labeled).
    if not _prep_state_swap_plausible(original_food_id, replacement_food_id):
        return False

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
        if not _LOW_FAT_LABEL.search(repl):
            return False
    if _OIL.search(repl) and not _OIL.search(orig):
        if not _LOW_FAT_LABEL.search(orig):
            return False

    if not anatomical_swap_plausible(orig, repl):
        return False

    if not dairy_yogurt_swap_plausible(orig, repl):
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
