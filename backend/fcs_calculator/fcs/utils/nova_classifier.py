"""Rigorous NOVA classifier — Monteiro 2019 4-group framework.

Replaces the inline substring-keyword block previously in
`cnf_data_integrator.py::_categorize_food_ingredients`. That block had three
defects surfaced by the FCS smoke audit (2026-05-23):

  1. Substring matching without word boundaries → `'OIL' in 'BOILED'` produced
     NOVA 2 false-positives on frozen-boiled vegetables.
  2. No CNF FoodGroup auto-routes → "Fast Foods" hot dogs and frozen pizzas
     fell through to NOVA 3 instead of Monteiro's canonical NOVA 4 examples
     (Monteiro 2019 lists "reconstituted meat products" and "pre-prepared
     frozen dishes" as literal NOVA 4 archetypes).
  3. Narrow NOVA 4 lexicon → no detection of ingredient isolates (soy/whey
     protein isolate, maltodextrin), emulsifiers / stabilizers, or industrial
     processes (extrusion, hydrolysation, interesterification).

Architecture (parallels the §3.4 HENI categorizer + §3.5 LCA matcher):

  Stage 1 — CNF FoodGroup hard rules. Monteiro maps certain food categories
            directly to NOVA groups regardless of description (e.g. all of
            "Fast Foods", "Babyfoods", "Snacks" are NOVA 4 by definition).
            Returns (level, conf=1.0, "food_group_rule:…") on match.
  Stage 2 — Word-boundary keyword matching, multi-tier:
            (a) NOVA 4 marker isolates / additives / industrial processes
                (Monteiro's "ingredients with no domestic equivalent"
                criterion) → NOVA 4 immediately.
            (b) NOVA 4 packaged-product keywords (soda, candy, cookies, etc.) → NOVA 4.
            (c) NOVA 3 preservation/processing markers (canned, cured,
                smoked, deli meat, etc.) → NOVA 3.
            (d) NOVA 2 culinary-ingredient markers (oil, butter, sugar,
                etc. — word-boundary) → NOVA 2.
            Returns (level, conf=0.9, "keyword_rule:…") on match.
  Stage 3 — Default to NOVA 1 (minimally processed) with conf=0.7. Monteiro
            assumes any food not matching higher-process criteria is NOVA 1.

Stage 3-bis (OPTIONAL): LLM augmentation for ambiguous cases. When
  `LLMNovaAugmenter` is provided, foods whose Stage-2 rules return no match
  AND whose CNF FoodGroup doesn't carry a strong NOVA-1 prior (e.g. Mixed
  Dishes, Sausages and Luncheon meats — heterogeneous groups) are sent to
  an LLM classifier with Monteiro's 4-group definitions in the system
  prompt. Constrained JSON output: `{nova_group: 1|2|3|4, confidence,
  rationale}`. Multi-provider via ChatJSONClient (matches the §3.5 / §3.6
  pattern). Cached per food_id.

Output: `(level: int 1-4, confidence: float 0-1, rationale: str)`.
"""
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Stage 1: Canonical-category hard rules per Monteiro 2019 + Khandpur 2020
# ----------------------------------------------------------------------

# Canonical food category → default NOVA level (overrides apply if description
# matches an exception; see _foodgroup_hard_rule). Replaces the previous
# CNF-id-keyed table (FDC-MULTI-SOURCE 2026-06-26) — source-agnostic by
# construction: WAFCT and FDC foods that resolve to the same canonical
# category get the same NOVA defaults as their CNF analogs.
_CATEGORY_DEFAULT_NOVA: Dict[str, int] = {
    # NOVA 4 (always — Monteiro's canonical examples)
    'babyfoods':           4,   # Commercial infant foods per Monteiro
    'sausages_luncheon':   4,   # Cured + reconstituted
    'breakfast_cereals':   4,   # Monteiro: "ready-to-eat" packaged
    'fast_foods':          4,   # Literal NOVA 4 per Monteiro
    'snacks':              4,   # Packaged snacks per Monteiro

    # NOVA 4 by default but with exceptions for simple/homemade variants
    'baked_products':      4,   # Commercial baked = NOVA 4; freshly baked plain = NOVA 3 exception
    'sweets':              4,   # Candy/cookies/cake = NOVA 4; honey/maple syrup = NOVA 3 exception
    'mixed_dishes':        4,   # Prepared/frozen = NOVA 4; simple home-style = NOVA 3 exception

    # NOVA 2 culinary ingredients (always)
    'fats_oils':           2,

    # NOVA 1 minimally processed (default; exceptions for cured/processed variants)
    'dairy_egg_combined':  1,   # CNF FG1 (heterogeneous; keyword rules below split out cheese/yogurt/butter)
    'dairy':               1,   # WAFCT/FDC FNDDS milk-only and dairy rows
    'eggs':                1,   # WAFCT/FDC FNDDS egg-only rows
    'poultry':             1,
    'fruits':              1,   # Juice exception → NOVA 3
    'pork':                1,
    'vegetables':          1,
    'nuts_seeds':          1,
    'beef':                1,
    'fish':                1,
    'legumes':             1,
    'lamb_veal_game':      1,
    'cereals_grains':      1,   # Raw = NOVA 1; refined/instant = NOVA 4

    # Heterogeneous — defer to keyword matching, no Stage-1 default fires
    # 'spices_herbs'         (mostly NOVA 1; commercial blends = NOVA 2/4)
    # 'soups_sauces'         (homemade = NOVA 3; commercial = NOVA 4)
    # 'beverages'            (water = NOVA 1; juice = NOVA 3; soda = NOVA 4)
    # 'alcoholic_beverages'  (caught by Stage 2 keyword rules)
}


# Patterns that DEMOTE a default-NOVA-4 food group to NOVA 3 when present in description.
# Used for groups 18 (Baked Products) and 19 (Sweets).
_PLAIN_NOVA3_EXCEPTIONS = [
    r'\bhomemade\b', r'\bfreshly\s+made\b', r'\bfreshly\s+baked\b',
]
_SWEETS_NOVA3_EXCEPTIONS = [
    r'\bhoney\b', r'\bmaple\s+syrup\b', r'\bmolasses\b',
]
# Patterns that PROMOTE a default-NOVA-1 food (Cereals, Grains, Pasta) to NOVA 4.
_GRAIN_NOVA4_PROMOTIONS = [
    r'\binstant\b', r'\bbreakfast\s+cereal\b', r'\bcereal,\s+ready\b',
    r'\bsweetened\b', r'\bflavou?red\b',
]
# Patterns that PROMOTE a default-NOVA-1 meat/poultry to NOVA 3 or NOVA 4.
_MEAT_NOVA3_PROMOTIONS = [
    r'\bcured\b', r'\bsmoked\b', r'\bcanned\b', r'\bjerky\b', r'\bsalted\b',
    r'\bpickled\b', r'\bpastrami\b',
]
_MEAT_NOVA4_PROMOTIONS = [
    r'\breconstituted\b', r'\brestructured\b', r'\breformed\b',
    r'\bsausage\b', r'\bhot\s+dog\b', r'\bfrankfurter\b', r'\bwiener\b',
    r'\bbologna\b', r'\bsalami\b', r'\bpepperoni\b',
    r'\bdeli[\s-]?meat\b', r'\blunch[\s-]?meat\b',
]
# Patterns that PROMOTE fruit-juices group to NOVA 3 (juice) or NOVA 4 (drinks).
_JUICE_NOVA3_PROMOTIONS = [
    r'\bjuice,\s+canned\b', r'\bjuice,\s+bottled\b', r'\bjuice,\s+frozen\b',
    r'\bjuice,\s+raw\b', r'\bjuice,\s+100\b',
]
_FRUIT_NOVA4_PROMOTIONS = [
    r'\bfruit\s+drink\b', r'\bfruit\s+punch\b', r'\bsweetened\b',
    r'\bnectar\b',
]
# Beverages group dispatch.
_BEV_NOVA1_PATTERNS = [r'\bwater,?\s+(tap|bottled|plain)\b', r'\btea,?\s+brewed\b', r'\bcoffee,?\s+brewed\b']
_BEV_NOVA3_PATTERNS = [r'\bjuice\b']
_BEV_NOVA4_PATTERNS = [
    r'\bcola\b', r'\bsoda\b', r'\bsoft\s+drink\b', r'\benergy\s+drink\b',
    r'\bsports\s+drink\b', r'\bsweetened\b', r'\bcarbonated\b',
    r'\binstant\b', r'\bpowder(ed)?\b',
]
# Soups/sauces/gravies (group 6) dispatch.
_SOUP_NOVA4_PATTERNS = [
    r'\bcondensed\b', r'\bdehydrated\b', r'\binstant\b', r'\bdry\s+mix\b',
    r'\bcanned\b',
]


# ----------------------------------------------------------------------
# Stage 2: Word-boundary keyword classifiers (Monteiro 2019 marker sets)
# ----------------------------------------------------------------------

# NOVA 4 markers: ingredients with no domestic kitchen equivalent
# (Monteiro 2019 §4.3 "ingredients of these formulations usually include...
# casein, lactose, whey, gluten ... soya protein isolate, maltodextrin,
# invert sugar, high-fructose corn syrup ... hydrogenated or interesterified
# oils, hydrolysed proteins").
_NOVA4_ISOLATES_RX = [
    r'\bsoy(a)?\s+protein\s+isolate\b',
    r'\bwhey\s+protein\s+isolate\b',
    r'\bcasein(ate)?\b',
    r'\bmaltodextrin\b',
    r'\bhigh[\s-]?fructose\s+corn\s+syrup\b', r'\bhfcs\b',
    r'\binvert\s+sugar\b',
    r'\bhydrolyse?d\s+(vegetable\s+)?protein\b',
    r'\bhydrogenated\b', r'\binteresterified\b',
    r'\bglucose[\s-]?fructose\b',     # Canadian labelling synonym for HFCS
    r'\bmodified\s+(corn\s+)?starch\b',
]
# NOVA 4 markers: industrial additives with no domestic equivalent
# (Monteiro 2019: "dyes, colour stabilizers, flavours, flavour enhancers,
# non-sugar sweeteners; ... emulsifiers, sequestrants, humectants").
_NOVA4_ADDITIVES_RX = [
    r'\baspartame\b', r'\bsucralose\b', r'\bsaccharin\b', r'\bacesulfame\b',
    r'\bmono?sodium\s+glutamate\b', r'\bmsg\b',
    r'\bsodium\s+nitr(it|at)e\b', r'\bpotassium\s+nitr(it|at)e\b',
    r'\bcarrageenan\b', r'\bxanthan\s+gum\b', r'\bguar\s+gum\b',
    r'\blecithin\b', r'\bpolysorbate\b', r'\bcarboxymethyl(cellulose)?\b',
    r'\bartificial\s+(flavou?r|colou?r|sweet)', r'\bfd&c\b',
    r'\bbha\b', r'\bbht\b', r'\btbhq\b',
    r'\benriched\b',  # in cereal/flour context, typical NOVA 4 signal
    r'\bfortified\b',
]
# NOVA 4: industrial processes / packaged-product archetypes
_NOVA4_PROCESSES_RX = [
    r'\bextrud(ed|ing)\b', r'\bmoulded\b', r'\breconstituted\b',
    r'\brestructured\b', r'\bdehydrated\b', r'\bfreeze[\s-]?dried\b',
    r'\bpre[\s-]?fried\b',
]
_NOVA4_PRODUCTS_RX = [
    r'\bsoft\s+drink\b', r'\bsoda\b', r'\bcola\b', r'\bsweetened\s+beverage\b',
    r'\benergy\s+drink\b', r'\bsports\s+drink\b',
    r'\bcandy\b', r'\bcandies\b', r'\bchocolate\s+bar\b', r'\bgranola\s+bar\b',
    r'\bcracker(s)?\b', r'\bchip(s)?\b', r'\bcookie(s)?\b',
    r'\bbreakfast\s+cereal\b', r'\bcereal\s+bar\b',
    r'\bice\s+cream\b', r'\bfrozen\s+dessert\b',
    r'\bfrozen\s+(meal|dinner|entr|pizza)', r'\bpre[\s-]?prepared\b',
    r'\binstant\s+(noodle|soup|meal|coffee)\b',
    r'\bmargarine\b',  # typically interesterified per Monteiro
    r'\bmuffin\b', r'\bdonut\b', r'\bdoughnut\b', r'\bpastr(y|ies)\b',
    r'\bsugary\s+cereal\b',
]

# NOVA 3 preservation/processing markers (Monteiro 2019 §4.2 "bottled
# vegetables, canned fish, fruits in syrup, cheeses and freshly made
# breads ... made by adding salt, oil, sugar ... to Group 1 foods").
_NOVA3_RX = [
    r'\bcured\b', r'\bsmoked\b', r'\bsalted\b', r'\bpickled\b',
    r'\bcanned\b', r'\bjarred\b', r'\bbottled\b', r'\bpreserved\b',
    r'\bin\s+(brine|oil|syrup|sauce)\b',
    r'\bcheese\b', r'\bbread\b', r'\bbagel\b', r'\btortilla\b',
    r'\bham\b', r'\bbacon\b',  # cured pork
    r'\bjerky\b',
]

# NOVA 2 culinary ingredients (Monteiro 2019 §4.1 "oils, butter, sugar
# and salt ... derived from Group 1 foods by pressing, refining, grinding,
# milling and drying").
# CRITICAL: word-boundary regex to avoid the OIL/BOILED bug.
_NOVA2_RX = [
    r'\boil\b', r'\bbutter\b', r'\blard\b', r'\bshortening\b', r'\bghee\b',
    r'\bsalt\b', r'\bsugar(s)?\b', r'\bhoney\b', r'\bmaple\s+syrup\b',
    r'\bmolasses\b', r'\bvinegar\b', r'\bflour\b', r'\bstarch\b',
    r'\bcorn\s+starch\b', r'\bbaking\s+powder\b', r'\byeast\b',
]


def _compile_rx_list(patterns):
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_NOVA4_ISOLATES = _compile_rx_list(_NOVA4_ISOLATES_RX)
_NOVA4_ADDITIVES = _compile_rx_list(_NOVA4_ADDITIVES_RX)
_NOVA4_PROCESSES = _compile_rx_list(_NOVA4_PROCESSES_RX)
_NOVA4_PRODUCTS = _compile_rx_list(_NOVA4_PRODUCTS_RX)
_NOVA3_PATTERNS = _compile_rx_list(_NOVA3_RX)
_NOVA2_PATTERNS = _compile_rx_list(_NOVA2_RX)

_PLAIN_NOVA3_EXC = _compile_rx_list(_PLAIN_NOVA3_EXCEPTIONS)
_SWEETS_NOVA3_EXC = _compile_rx_list(_SWEETS_NOVA3_EXCEPTIONS)
_GRAIN_NOVA4_PROM = _compile_rx_list(_GRAIN_NOVA4_PROMOTIONS)
_MEAT_NOVA3_PROM = _compile_rx_list(_MEAT_NOVA3_PROMOTIONS)
_MEAT_NOVA4_PROM = _compile_rx_list(_MEAT_NOVA4_PROMOTIONS)
_JUICE_NOVA3_PROM = _compile_rx_list(_JUICE_NOVA3_PROMOTIONS)
_FRUIT_NOVA4_PROM = _compile_rx_list(_FRUIT_NOVA4_PROMOTIONS)
_BEV_NOVA1_PAT = _compile_rx_list(_BEV_NOVA1_PATTERNS)
_BEV_NOVA3_PAT = _compile_rx_list(_BEV_NOVA3_PATTERNS)
_BEV_NOVA4_PAT = _compile_rx_list(_BEV_NOVA4_PATTERNS)
_SOUP_NOVA4_PAT = _compile_rx_list(_SOUP_NOVA4_PATTERNS)


def _any_match(text: str, patterns) -> Optional[str]:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(0)
    return None


@dataclass
class NovaClassification:
    level: int                    # 1-4
    confidence: float             # 0-1
    rationale: str                # short string describing the decision path
    matched_patterns: list        # list of matched regex strings (audit trail)


_DAIRY_NOVA2_PATTERNS = _compile_rx_list([r'\bbutter\b', r'\bghee\b'])
_DAIRY_NOVA3_PATTERNS = _compile_rx_list([r'\bcheese\b'])
_DAIRY_NOVA4_PATTERNS = _compile_rx_list([
    r'\byog(o|u)urt,?\s+(sweetened|flavou?red|fruit)',
    r'\bmilkshake\b', r'\bsweetened\s+condensed\b',
])
_SWEETS_NOVA2_PATTERNS = _compile_rx_list([
    r'\bsugar(s)?,?\s+(granulated|brown|icing|powdered|fructose)',
    r'\bmaple\s+sugar\b',
])
# Baked Products: NOVA 3 default if no ultra-processed indicators present
_BAKED_NOVA4_PATTERNS = _compile_rx_list([
    r'\bsweetened\b', r'\bglazed\b', r'\bicing\b', r'\bcream[\s-]?filled\b',
    r'\bchocolate[\s-]?chip\b', r'\binstant\b', r'\bsoft[\s-]?type\b',
    r'\bcookie\b', r'\bcake\b', r'\bdonut\b', r'\bdoughnut\b', r'\bpastr',
    r'\bmuffin\b', r'\bpie\b', r'\btart\b',
])


def _foodgroup_hard_rule(canonical_category: str, food_desc_lower: str) -> Optional[NovaClassification]:
    """Stage 1: Canonical-category-driven hard rules with description-pattern exceptions.

    FDC-MULTI-SOURCE (2026-06-26): was keyed on CNF FoodGroupID (1, 9, 11, 14, ...),
    now keyed on canonical category so the rule fires identically for CNF / WAFCT / FDC
    foods that resolve to the same concept. Keyword-pattern regexes (_DAIRY_NOVA4_PATTERNS,
    _MEAT_NOVA4_PROM, _BEV_NOVA4_PAT, etc.) are unchanged — they operate on the food
    description string which is source-agnostic.
    """
    # Dairy bucket — covers CNF FG1 ('dairy_egg_combined' which is heterogeneous,
    # spanning milk/butter/cheese/sweetened-yogurt) plus the WAFCT/FDC FNDDS
    # finer-grained 'dairy' rows.
    if canonical_category in ('dairy_egg_combined', 'dairy'):
        if _any_match(food_desc_lower, _DAIRY_NOVA4_PATTERNS):
            return NovaClassification(4, 0.9, 'foodgroup_rule:dairy_sweetened_or_milkshake', [])
        if _any_match(food_desc_lower, _DAIRY_NOVA3_PATTERNS):
            return NovaClassification(3, 0.9, 'foodgroup_rule:dairy_cheese_processed', [])
        if _any_match(food_desc_lower, _DAIRY_NOVA2_PATTERNS):
            return NovaClassification(2, 0.9, 'foodgroup_rule:dairy_butter_culinary', [])
        return NovaClassification(1, 0.85, 'foodgroup_rule:dairy_plain_default', [])
    if canonical_category == 'fruits':
        if _any_match(food_desc_lower, _FRUIT_NOVA4_PROM):
            return NovaClassification(4, 0.95, 'foodgroup_rule:fruit_drink_or_punch', [])
        if _any_match(food_desc_lower, _JUICE_NOVA3_PROM):
            return NovaClassification(3, 0.95, 'foodgroup_rule:fruit_juice', [])
        return NovaClassification(1, 0.95, 'foodgroup_rule:fruit_default_raw', [])
    if canonical_category == 'vegetables':
        # Frozen/canned plain veg stays NOVA 1; only promote if ultra-processed
        return None  # Defer to keyword classifier — most veg is NOVA 1 by default
    if canonical_category == 'beverages':
        if _any_match(food_desc_lower, _BEV_NOVA4_PAT):
            return NovaClassification(4, 0.9, 'foodgroup_rule:beverage_ssb', [])
        if _any_match(food_desc_lower, _BEV_NOVA3_PAT):
            return NovaClassification(3, 0.9, 'foodgroup_rule:beverage_juice', [])
        if _any_match(food_desc_lower, _BEV_NOVA1_PAT):
            return NovaClassification(1, 0.9, 'foodgroup_rule:beverage_plain', [])
        return None
    if canonical_category == 'alcoholic_beverages':
        # Beer / wine / liquor — Monteiro classes these as NOVA 1 (wine, beer)
        # to NOVA 4 (cocktails with industrial additives). Conservative default
        # NOVA 1 for plain; keyword Stage 2 catches mixers.
        return NovaClassification(1, 0.85, 'foodgroup_rule:alcoholic_default', [])
    if canonical_category == 'soups_sauces':
        if _any_match(food_desc_lower, _SOUP_NOVA4_PAT):
            return NovaClassification(4, 0.9, 'foodgroup_rule:commercial_soup', [])
        return NovaClassification(3, 0.85, 'foodgroup_rule:simple_soup_default', [])
    # Meat: poultry / pork / beef / lamb_veal_game (CNF FG 5/10/13/17 + WAFCT/FDC analogs)
    if canonical_category in ('poultry', 'pork', 'beef', 'lamb_veal_game'):
        if _any_match(food_desc_lower, _MEAT_NOVA4_PROM):
            return NovaClassification(4, 0.95, 'foodgroup_rule:processed_reconstituted_meat', [])
        if _any_match(food_desc_lower, _MEAT_NOVA3_PROM):
            return NovaClassification(3, 0.9, 'foodgroup_rule:cured_or_canned_meat', [])
        return NovaClassification(1, 0.9, 'foodgroup_rule:meat_default_unprocessed', [])
    if canonical_category == 'cereals_grains':
        if _any_match(food_desc_lower, _GRAIN_NOVA4_PROM):
            return NovaClassification(4, 0.9, 'foodgroup_rule:instant_or_sweetened_grain', [])
        return None  # Most grains/pasta are NOVA 1 raw
    if canonical_category == 'sweets':
        if _any_match(food_desc_lower, _SWEETS_NOVA2_PATTERNS):
            return NovaClassification(2, 0.9, 'foodgroup_rule:sweets_pure_sugar_culinary', [])
        if _any_match(food_desc_lower, _SWEETS_NOVA3_EXC):
            return NovaClassification(3, 0.85, 'foodgroup_rule:sweets_simple_honey_maple', [])
        return NovaClassification(4, 0.85, 'foodgroup_rule:sweets_commercial_candy_dessert', [])
    if canonical_category == 'baked_products':
        if _any_match(food_desc_lower, _PLAIN_NOVA3_EXC):
            return NovaClassification(3, 0.85, 'foodgroup_rule:baked_homemade', [])
        if _any_match(food_desc_lower, _BAKED_NOVA4_PATTERNS):
            return NovaClassification(4, 0.85, 'foodgroup_rule:baked_commercial_pastry_or_sweetened', [])
        return NovaClassification(3, 0.8, 'foodgroup_rule:baked_plain_bread_default', [])
    if canonical_category == 'mixed_dishes':
        if _any_match(food_desc_lower, _PLAIN_NOVA3_EXC):
            return NovaClassification(3, 0.8, 'foodgroup_rule:mixed_dish_homemade', [])
        return NovaClassification(4, 0.85, 'foodgroup_rule:mixed_dish_commercial_default', [])
    if canonical_category in _CATEGORY_DEFAULT_NOVA:
        return NovaClassification(_CATEGORY_DEFAULT_NOVA[canonical_category], 0.9,
                                  f'foodgroup_rule:default_for_{canonical_category}', [])
    return None


def _keyword_rule(food_desc_lower: str) -> Optional[NovaClassification]:
    """Stage 2: word-boundary keyword matching across NOVA 4 → 3 → 2 priority.

    Multi-tier within NOVA 4: isolates + additives + industrial processes are
    the strongest Monteiro signals (any single match → NOVA 4 immediately).
    """
    matched: list = []

    # NOVA 4 — strongest signals first
    m = _any_match(food_desc_lower, _NOVA4_ISOLATES)
    if m:
        matched.append(f'nova4_isolate:{m}')
        return NovaClassification(4, 0.95, 'keyword:ingredient_isolate', matched)
    m = _any_match(food_desc_lower, _NOVA4_ADDITIVES)
    if m:
        matched.append(f'nova4_additive:{m}')
        return NovaClassification(4, 0.9, 'keyword:industrial_additive', matched)
    m = _any_match(food_desc_lower, _NOVA4_PROCESSES)
    if m:
        matched.append(f'nova4_process:{m}')
        return NovaClassification(4, 0.9, 'keyword:industrial_process', matched)
    m = _any_match(food_desc_lower, _NOVA4_PRODUCTS)
    if m:
        matched.append(f'nova4_product:{m}')
        return NovaClassification(4, 0.85, 'keyword:packaged_product_archetype', matched)

    # NOVA 3
    m = _any_match(food_desc_lower, _NOVA3_PATTERNS)
    if m:
        matched.append(f'nova3:{m}')
        return NovaClassification(3, 0.85, 'keyword:preservation_or_processing', matched)

    # NOVA 2
    m = _any_match(food_desc_lower, _NOVA2_PATTERNS)
    if m:
        matched.append(f'nova2:{m}')
        return NovaClassification(2, 0.85, 'keyword:culinary_ingredient', matched)

    return None


# ----------------------------------------------------------------------
# Stage 3-bis: optional LLM augmentation (multi-provider via ChatJSONClient)
# ----------------------------------------------------------------------

# Process-wide cache; deterministic at T=0 so per-food-id is the right cache key.
_LLM_CACHE: Dict[int, NovaClassification] = {}
_LLM_CACHE_LOCK = threading.Lock()

_LLM_SYSTEM_PROMPT = """You are classifying a food into one of the four NOVA groups per Monteiro et al. 2019. Definitions:

NOVA 1 — Unprocessed or minimally processed foods: edible parts of plants/animals after separation from nature; or natural foods altered only by removal of inedible parts, drying, crushing, grinding, fractioning, filtering, roasting, boiling, non-alcoholic fermentation, pasteurization, refrigeration, freezing, packaging, vacuum-packing. NO added salt/sugar/oil.

NOVA 2 — Processed culinary ingredients: substances derived from NOVA 1 foods (or nature) by pressing, refining, grinding, milling, drying, used in kitchens to season/cook. Examples: oils, butter, sugar, salt, vinegar, flour.

NOVA 3 — Processed foods: NOVA 1 foods with added NOVA 2 ingredients (salt, oil, sugar) AND a preservation/cooking method (canning, smoking, curing, fermentation, baking). Examples: canned vegetables, smoked fish, cheeses, freshly-made breads, fruits in syrup, cured meats (ham, bacon).

NOVA 4 — Ultra-processed foods and drinks: industrial formulations made mostly from substances derived from foods AND additives, with little/no intact NOVA 1 food. KEY SIGNALS:
  - Ingredient isolates (soy/whey protein isolate, casein, lactose, maltodextrin, HFCS, glucose-fructose, modified starch, hydrolysed protein, hydrogenated or interesterified oils)
  - Industrial additives (artificial flavours/colours, non-sugar sweeteners, MSG, nitrites/nitrates, emulsifiers, stabilizers, carrageenan, xanthan gum, BHA/BHT)
  - Industrial processes (extrusion, moulding, reconstitution, pre-frying, hydrogenation)
  - Canonical archetypes (soft drinks, packaged snacks, reconstituted meat products like hot dogs/sausages, pre-prepared frozen dishes like frozen pizza/frozen meals, breakfast cereals, packaged cookies/cakes, instant noodles/soups, ice cream, margarine)

Respond with JSON only: {"nova_group": <1|2|3|4>, "confidence": <0.0-1.0>, "rationale": "<one sentence>"}.

Confidence anchors:
  0.95 = unambiguous canonical example (e.g. "raw apple" → 1; "Coca-Cola" → 4)
  0.80 = clear category with some ambiguity (e.g. "white bread, commercial" → 3 or 4 depending on additives)
  0.60 = ambiguous but most-likely
  0.40 = uncertain; multiple plausible
Vary your confidence — do not default to a single value."""


def llm_classify(
    food_id: int,
    food_description: str,
    food_group_name: str,
    chat_json_client,
    model: str = 'gpt-4.1-mini',
) -> Optional[NovaClassification]:
    """Stage 3-bis: LLM augmentation. Returns None on failure (caller falls back to Stage 3 default)."""
    if food_id in _LLM_CACHE:
        return _LLM_CACHE[food_id]
    if chat_json_client is None:
        return None
    user_msg = (
        f"CNF food: {food_description!r}\n"
        f"CNF food group: {food_group_name!r}\n\n"
        "Classify into NOVA 1-4 per Monteiro 2019. JSON only."
    )
    try:
        parsed = chat_json_client.chat_completion_json(
            system=_LLM_SYSTEM_PROMPT, user=user_msg,
            model=model, temperature=0.0, max_tokens=200,
        )
        level = int(parsed.get('nova_group'))
        if level not in (1, 2, 3, 4):
            return None
        conf = float(parsed.get('confidence', 0.5))
        rationale = str(parsed.get('rationale', ''))[:300]
        result = NovaClassification(level, conf, f'llm:{rationale}', [])
        with _LLM_CACHE_LOCK:
            _LLM_CACHE[food_id] = result
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning('NOVA LLM classifier failed for food_id=%s: %s', food_id, exc)
        return None


# ----------------------------------------------------------------------
# Top-level dispatcher
# ----------------------------------------------------------------------

# Canonical categories where Stage 1 doesn't fire and the food is heterogeneous
# enough that LLM augmentation is worthwhile (rather than falling back to NOVA 1
# default). FDC-MULTI-SOURCE (2026-06-26): keyed on canonical category — was CNF
# group IDs 1/2/11/20.
_LLM_AUGMENT_CATEGORIES = frozenset({
    'dairy_egg_combined',  # CNF FG1 (heterogeneous yogurts span 1/3/4)
    'dairy',               # WAFCT/FDC dairy that escapes Stage 1
    'spices_herbs',        # raw spices = 1; commercial blends = 2/4
    'vegetables',          # mostly 1, but commercial preparations vary
    'cereals_grains',      # raw = 1; refined/instant = 4
})


def classify(
    food_id: int,
    food_description: str,
    food_group_name: str,
    food_group_id: int,
    chat_json_client=None,
    enable_llm: bool = True,
) -> NovaClassification:
    """Classify a food into NOVA 1-4 per Monteiro 2019.

    Pipeline:
      Stage 1: Canonical-category hard rule (deterministic) — source-agnostic
               via the food_group_canonical_category bridge.
      Stage 2: Word-boundary keyword classifier (deterministic)
      Stage 3-bis: LLM augmentation when category is heterogeneous (optional)
      Stage 3: Default NOVA 1 (Monteiro's "natural foods" baseline)

    FDC-MULTI-SOURCE (2026-06-26): Stage 1 now resolves canonical category
    once via the bridge (covering CNF / WAFCT / FDC). Backward-compatible
    signature retained — `food_group_id` is read here, not by the rule.
    """
    desc_lower = (food_description or '').lower()

    # Resolve canonical category from FoodGroupID (source-agnostic).
    try:
        from api.services.food_group_category import canonical_category_for_group
        canonical_category = canonical_category_for_group(int(food_group_id))
    except Exception:  # noqa: BLE001 — bridge optional in some test contexts
        canonical_category = 'unknown'

    # Stage 1
    s1 = _foodgroup_hard_rule(canonical_category, desc_lower)
    if s1 is not None:
        return s1

    # Stage 2
    s2 = _keyword_rule(desc_lower)
    if s2 is not None:
        return s2

    # Stage 3-bis
    if enable_llm and chat_json_client is not None and canonical_category in _LLM_AUGMENT_CATEGORIES:
        s3b = llm_classify(food_id, food_description, food_group_name, chat_json_client)
        if s3b is not None:
            return s3b

    # Stage 3 default
    return NovaClassification(1, 0.7, 'default:no_rule_matched_assume_nova1', [])


def reset_llm_cache_for_test() -> None:
    """Test helper — clear the process-wide LLM classification cache."""
    global _LLM_CACHE
    with _LLM_CACHE_LOCK:
        _LLM_CACHE = {}
