"""Ingredient-level USDA Food Pattern (FPID) attribution for a finished food.

FPED tells you a finished food's food-group profile; FPID tells you which *ingredient*
contributes each food group. This module turns a catalog FoodID into an ingredient-level
breakdown ("the red meat in this dish comes from the beef; the dairy from the cheese")
using USDA's authoritative FNDDS recipe + FPID — no LLM.

Path: FoodID -> (food_code, fdc_id, bridge_confidence) via the FPED bridge meta
(`fped_profile_loader.get_food_meta`) -> FNDDS recipe ingredients (input_food.csv) ->
each SR ingredient's FPID pattern row (`fpid_loader`).

Two consumers:
  fpid_breakdown(food_id)        ingredient -> food-group attribution (the headline use case)
  fpid_reconstruction(food_id)   QC: does the FPID ingredient rollup reconstruct the food's
                                 own FPED profile? (coverage + cosine integrity check)

Honest about coverage: ingredients whose SR code has no FPID row, and recipe-within-recipe
references the loader doesn't expand, are surfaced as unmapped recipe mass — never hidden.
The breakdown describes the bridged FNDDS *analog's* recipe (gated by bridge confidence),
not a teardown of the exact catalog food, so it is a research/clinical lens, not a label.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from .fped_aggregator import FPED_MAJOR_GROUPS
from .fped_profile_loader import (
    FPED_COMPONENT_UNITS,
    get_fped_profile_for_food,
    get_food_meta,
)

# Raw FPID column -> our normalized component key. FPID's columns are byte-identical to
# FPED's (verified against raw_fpid/FPID_1718.xls), so this mirrors the ETL's
# _FPED_COLUMN_MAP — kept local to avoid importing the one-time ETL module, which
# reconfigures logging at import time.
_FPID_COLUMN_TO_KEY: Dict[str, str] = {
    'F_TOTAL (cup eq.)': 'fruit_total_cup',
    'F_CITMLB (cup eq.)': 'fruit_citrus_melon_berry_cup',
    'F_OTHER (cup eq.)': 'fruit_other_cup',
    'F_JUICE (cup eq.)': 'fruit_juice_cup',
    'V_TOTAL (cup eq.)': 'veg_total_cup',
    'V_DRKGR (cup eq.)': 'veg_dark_green_cup',
    'V_REDOR_TOTAL (cup eq.)': 'veg_red_orange_total_cup',
    'V_REDOR_TOMATO (cup eq.)': 'veg_red_orange_tomato_cup',
    'V_REDOR_OTHER (cup eq.)': 'veg_red_orange_other_cup',
    'V_STARCHY_TOTAL (cup eq.)': 'veg_starchy_total_cup',
    'V_STARCHY_POTATO (cup eq.)': 'veg_starchy_potato_cup',
    'V_STARCHY_OTHER (cup eq.)': 'veg_starchy_other_cup',
    'V_OTHER (cup eq.)': 'veg_other_cup',
    'V_LEGUMES (cup eq.)': 'veg_legumes_cup',
    'G_TOTAL (oz. eq.)': 'grain_total_oz',
    'G_WHOLE (oz. eq.)': 'grain_whole_oz',
    'G_REFINED (oz. eq.)': 'grain_refined_oz',
    'PF_TOTAL (oz. eq.)': 'protein_total_oz',
    'PF_MPS_TOTAL (oz. eq.)': 'protein_meat_poultry_seafood_oz',
    'PF_MEAT (oz. eq.)': 'protein_meat_oz',
    'PF_CUREDMEAT (oz. eq.)': 'protein_cured_meat_oz',
    'PF_ORGAN (oz. eq.)': 'protein_organ_oz',
    'PF_POULT (oz. eq.)': 'protein_poultry_oz',
    'PF_SEAFD_HI (oz. eq.)': 'protein_seafood_high_omega3_oz',
    'PF_SEAFD_LOW (oz. eq.)': 'protein_seafood_low_omega3_oz',
    'PF_EGGS (oz. eq.)': 'protein_eggs_oz',
    'PF_SOY (oz. eq.)': 'protein_soy_oz',
    'PF_NUTSDS (oz. eq.)': 'protein_nuts_seeds_oz',
    'PF_LEGUMES (oz. eq.)': 'protein_legumes_oz',
    'D_TOTAL (cup eq.)': 'dairy_total_cup',
    'D_MILK (cup eq.)': 'dairy_milk_cup',
    'D_YOGURT (cup eq.)': 'dairy_yogurt_cup',
    'D_CHEESE (cup eq.)': 'dairy_cheese_cup',
    'OILS (grams)': 'oils_g',
    'SOLID_FATS (grams)': 'solid_fats_g',
    'ADD_SUGARS (tsp. eq.)': 'added_sugars_tsp',
    'A_DRINKS (no. of drinks)': 'alcoholic_drinks',
}

_BASE_COMPONENTS = list(FPED_COMPONENT_UNITS.keys())  # 37 base keys (no derived seafood total)
_DEFAULT_CONFIDENCE_FLOOR = 0.5


def _ingredient_components_per_100g(pattern_equivalents: Dict[str, float]) -> Dict[str, float]:
    """One ingredient's raw FPID columns -> our component keys, per 100 g of ingredient."""
    out = {k: 0.0 for k in _BASE_COMPONENTS}
    for col, val in pattern_equivalents.items():
        key = _FPID_COLUMN_TO_KEY.get(col)
        if key is not None:
            out[key] = float(val or 0.0)
    out['protein_seafood_total_oz'] = (
        out.get('protein_seafood_high_omega3_oz', 0.0)
        + out.get('protein_seafood_low_omega3_oz', 0.0)
    )
    return out


def _recipe(food_id: int, confidence_floor: float) -> Optional[Tuple[Dict, List, float]]:
    """(bridge meta, FNDDS ingredient list, total recipe grams) or None when unreachable.

    None when the food never bridged, the analog match is below `confidence_floor`, the
    FNDDS analog has no SR ingredient rows, or the recipe has zero mass.
    """
    meta = get_food_meta(int(food_id))
    if meta is None or float(meta.get('bridge_confidence', 0.0) or 0.0) < confidence_floor:
        return None
    from heni_calculator.heni.data.fpid_loader import get_fpid_ingredients_for_fndds
    ings = get_fpid_ingredients_for_fndds(int(meta['food_code']))
    if not ings:
        return None
    total_g = sum(float(i.gram_weight or 0.0) for i in ings)
    if total_g <= 0:
        return None
    return meta, ings, total_g


def fpid_breakdown(
    food_id: int,
    mass_g: float = 100.0,
    confidence_floor: float = _DEFAULT_CONFIDENCE_FLOOR,
) -> Optional[Dict]:
    """Ingredient-level food-group attribution for a finished/composite food.

    For each of the everyday major food groups (`FPED_MAJOR_GROUPS`), reports the total
    contributed across `mass_g` of the food and which ingredients drive it (with % share).
    Returns None when the food has no reliable FNDDS recipe analog (see `_recipe`).
    """
    rec = _recipe(int(food_id), confidence_floor)
    if rec is None:
        return None
    meta, ings, total_recipe_g = rec
    scale = float(mass_g) / 100.0

    group_totals: Dict[str, float] = {comp: 0.0 for comp in FPED_MAJOR_GROUPS}
    group_sources: Dict[str, List[Dict]] = {comp: [] for comp in FPED_MAJOR_GROUPS}
    ing_rows: List[Dict] = []
    n_with_fpid = 0
    mapped_mass = 0.0

    for ing in ings:
        gw = float(ing.gram_weight or 0.0)
        has_fpid = bool(ing.pattern_equivalents)
        if has_fpid:
            n_with_fpid += 1
            mapped_mass += gw
        comp100 = _ingredient_components_per_100g(ing.pattern_equivalents)
        recipe_share = gw / total_recipe_g
        for comp in FPED_MAJOR_GROUPS:
            amt = comp100.get(comp, 0.0) * recipe_share * scale
            if amt > 1e-9:
                group_totals[comp] += amt
                group_sources[comp].append({'sr_description': ing.sr_description, 'amount': amt})
        ing_rows.append({
            'sr_description': ing.sr_description,
            'gram_weight': round(gw, 1),
            'share_of_recipe': round(recipe_share, 4),
            'has_fpid': has_fpid,
        })

    by_group: List[Dict] = []
    for comp, total in group_totals.items():
        if total < 0.05:
            continue
        label, unit = FPED_MAJOR_GROUPS[comp]
        srcs = sorted(group_sources[comp], key=lambda s: -s['amount'])
        sources = [{
            'sr_description': s['sr_description'],
            'amount': round(s['amount'], 2),
            'pct': round(100.0 * s['amount'] / total, 0) if total > 0 else 0.0,
        } for s in srcs if s['amount'] >= 0.01][:5]
        by_group.append({
            'component': comp, 'label': label, 'unit': unit,
            'amount': round(total, 2), 'sources': sources,
        })
    by_group.sort(key=lambda g: -g['amount'])

    unmapped_pct = (round(100.0 * (total_recipe_g - mapped_mass) / total_recipe_g, 1)
                    if total_recipe_g > 0 else 0.0)
    conf = float(meta['bridge_confidence'])
    return {
        'available': True,
        'food_id': int(food_id),
        'fdc_id': int(meta['fdc_id']),
        'food_code': int(meta['food_code']),
        'bridge_confidence': round(conf, 2),
        'mass_g': round(float(mass_g), 1),
        'by_group': by_group,
        'ingredients': ing_rows,
        'coverage': {
            'n_ingredients': len(ings),
            'n_with_fpid': n_with_fpid,
            'unmapped_pct': unmapped_pct,
        },
        'note': (
            "Ingredient-level food-group attribution from this food's closest US FNDDS "
            f"recipe analog (USDA FPID 2017-18), matched at {round(conf * 100):.0f}% "
            "confidence. Ingredients with no FPID row (and any sub-recipe references) are "
            "counted as unmapped recipe mass, so attribution can understate when coverage "
            "is low."
        ),
    }


def fpid_reconstruction(
    food_id: int,
    cosine_floor: float = 0.70,
    confidence_floor: float = _DEFAULT_CONFIDENCE_FLOOR,
) -> Optional[Dict]:
    """Independent QC: does the FPID ingredient rollup reconstruct the food's FPED profile?

    Builds the FPID ingredient rollup per 100 g of the food and cosine-compares it to the
    food's own FPED twin profile. High cosine = USDA's ingredient-level pattern data
    reproduces the food's known food-group profile (a reproducible, non-black-box check);
    a low cosine usually reflects recipe ingredients lacking FPID rows (see `unmapped_pct`),
    not a data error. Returns None when there is no FPED twin or no reliable recipe analog.
    """
    twin = get_fped_profile_for_food(int(food_id))
    if twin is None:
        return None
    rec = _recipe(int(food_id), confidence_floor)
    if rec is None:
        return None
    _meta, ings, total_recipe_g = rec

    recon = {k: 0.0 for k in _BASE_COMPONENTS}
    n_with_fpid = 0
    mapped_mass = 0.0
    for ing in ings:
        gw = float(ing.gram_weight or 0.0)
        if ing.pattern_equivalents:
            n_with_fpid += 1
            mapped_mass += gw
        comp100 = _ingredient_components_per_100g(ing.pattern_equivalents)
        share = gw / total_recipe_g
        for k in _BASE_COMPONENTS:
            recon[k] += comp100.get(k, 0.0) * share

    du = [float(twin.get(k, 0.0)) for k in _BASE_COMPONENTS]
    rv = [recon.get(k, 0.0) for k in _BASE_COMPONENTS]
    dot = sum(a * b for a, b in zip(du, rv))
    na = math.sqrt(sum(a * a for a in du))
    nb = math.sqrt(sum(b * b for b in rv))
    cosine = (dot / (na * nb)) if na > 0 and nb > 0 else None

    divergences = []
    for k in _BASE_COMPONENTS:
        d = recon.get(k, 0.0) - float(twin.get(k, 0.0))
        if abs(d) >= 0.1:
            divergences.append({
                'component': k, 'unit': FPED_COMPONENT_UNITS.get(k, ''),
                'twin_per_100g': round(float(twin.get(k, 0.0)), 2),
                'reconstructed_per_100g': round(recon.get(k, 0.0), 2),
                'delta': round(d, 2),
            })
    divergences.sort(key=lambda x: -abs(x['delta']))
    unmapped_pct = (round(100.0 * (total_recipe_g - mapped_mass) / total_recipe_g, 1)
                    if total_recipe_g > 0 else 0.0)

    return {
        'available': True,
        'food_id': int(food_id),
        'cosine': (round(cosine, 3) if cosine is not None else None),
        'plausible': bool(cosine is not None and cosine >= cosine_floor),
        'cosine_floor': cosine_floor,
        'coverage': {
            'n_ingredients': len(ings),
            'n_with_fpid': n_with_fpid,
            'unmapped_pct': unmapped_pct,
        },
        'top_divergences': divergences[:5],
        'note': (
            "Independent QC: the FPID ingredient rollup (per 100 g) vs the food's own FPED "
            "profile. Higher cosine = USDA's ingredient-level pattern data reconstructs the "
            "food's known food-group profile. A low cosine usually means recipe ingredients "
            "lack FPID rows (see unmapped_pct), not a data error."
        ),
    }
