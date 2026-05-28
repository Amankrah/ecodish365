"""Ground-truth validation lenses for recipe decompositions.

A recipe decomposer turns a composite/dish food into constituent ingredients + masses.
If that split is wrong, every downstream scorer (HEFI/HENI/HSR/FCS/FPED/FPID/LCA) is
silently misleading. These helpers score a decomposition against ground truth:

  nutrient_reconstruction(food_id, ingredients, total_mass_g)
      Lens 1 (primary, deterministic): recompute the dish's per-100 g nutrients from the
      decomposed ingredients and compare to the dish's OWN measured CNF nutrients. Truth =
      the dish's own profile, so it covers every composite and tests exactly what flows to
      the scorers.

  fndds_recipe_comparison(food_id, ingredients, conf_floor)
      Lens 4: for a CNF composite bridged to FNDDS at >= conf_floor, compare the
      decomposition's food-group (FPED) rollup to USDA's AUTHORITATIVE ingredient
      breakdown (FNDDS input_food.csv -> FPID), via cosine + ingredient-count + dominant
      food-group agreement. Truth = USDA's recipe. None when unbridged / below floor.

Lens 2 (FPED twin cosine) reuses `fped_aggregator.decomposition_plausibility`; lens 3
(structural gates) reads the decomposer's own output fields. Both are applied by the
benchmark harness, not here.

All math is deterministic dict arithmetic (no LLM). `ingredients` is a list of
{food_id, mass_g} (the same shape `aggregate_fped` consumes).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

from .fped_aggregator import FPED_MAJOR_GROUPS, aggregate_fped
from .fped_profile_loader import get_food_meta
from .fpid_aggregator import (
    _BASE_COMPONENTS,
    _ingredient_components_per_100g,
    _recipe,
)

# CNF nutrient names (per 100 g) for the reconstruction panel, verified against
# pipeline.nutrients_for() output.
_NUTRIENT_PANEL: Dict[str, str] = {
    'kcal': 'ENERGY (KILOCALORIES)',
    'protein': 'PROTEIN',
    'fat': 'FAT (TOTAL LIPIDS)',
    'carb': 'CARBOHYDRATE, TOTAL (BY DIFFERENCE)',
    'sugars': 'SUGARS, TOTAL',
    'fibre': 'FIBRE, TOTAL DIETARY',
    'sat_fat': 'FATTY ACIDS, SATURATED, TOTAL',
    'sodium': 'SODIUM',
}
_MACRO_KEYS = ('protein', 'fat', 'carb')


def _cosine(a: Dict[str, float], b: Dict[str, float], keys) -> Optional[float]:
    av = [float(a.get(k, 0.0)) for k in keys]
    bv = [float(b.get(k, 0.0)) for k in keys]
    dot = sum(x * y for x, y in zip(av, bv))
    na = math.sqrt(sum(x * x for x in av))
    nb = math.sqrt(sum(y * y for y in bv))
    return (dot / (na * nb)) if na > 0 and nb > 0 else None


def _nutrients(pipe, food_id: int) -> Dict[str, float]:
    try:
        return pipe.nutrients_for(int(food_id)) or {}
    except Exception:  # noqa: BLE001
        return {}


def nutrient_reconstruction(
    food_id: int,
    ingredients: List[Dict],
    total_mass_g: Optional[float] = None,
) -> Optional[Dict]:
    """Lens 1: reconstruct the dish's per-100 g nutrients from its decomposed ingredients
    and compare to the dish's own measured CNF nutrients.

    `total_mass_g` is the decompose target (e.g. 100). Reconstruction is normalised by it,
    so unresolved mass shows up honestly as a nutrient shortfall (matching what downstream
    scorers see). Falls back to the ingredient-mass sum when not given. Returns None when
    the dish has no nutrient profile or the ingredients have no mass.
    """
    from api.cnf_cache import get_api_cnf_pipeline
    pipe = get_api_cnf_pipeline()
    dish = _nutrients(pipe, food_id)
    if not dish:
        return None
    ing_mass_sum = sum(float(i.get('mass_g', 0.0) or 0.0) for i in ingredients)
    if ing_mass_sum <= 0:
        return None
    denom = float(total_mass_g) if (total_mass_g and total_mass_g > 0) else ing_mass_sum

    recon = {k: 0.0 for k in _NUTRIENT_PANEL}
    for i in ingredients:
        n = _nutrients(pipe, int(i['food_id']))
        w = float(i.get('mass_g', 0.0) or 0.0) / denom
        for key, cnf_name in _NUTRIENT_PANEL.items():
            recon[key] += float(n.get(cnf_name, 0.0) or 0.0) * w

    nutrients = {}
    abs_rel_errs = []
    macro_errs = []
    for key, cnf_name in _NUTRIENT_PANEL.items():
        d = float(dish.get(cnf_name, 0.0) or 0.0)
        r = recon[key]
        rel = (abs(r - d) / d) if d > 0 else None
        nutrients[key] = {
            'dish_per100g': round(d, 2),
            'recon_per100g': round(r, 2),
            'rel_error': (round(rel, 3) if rel is not None else None),
        }
        if rel is not None:
            abs_rel_errs.append(rel)
            if key in _MACRO_KEYS:
                macro_errs.append(rel)

    return {
        'available': True,
        'food_id': int(food_id),
        'nutrients': nutrients,
        # Relative-error metrics are the honest discriminators. (A raw nutrient-vector
        # cosine is NOT used: kcal + sodium magnitudes dominate it, making it insensitive
        # to macro composition — a wrong apple+bread split can out-score a faithful one.)
        'kcal_rel_error': nutrients['kcal']['rel_error'],
        'macro_mean_abs_rel_error': (round(sum(macro_errs) / len(macro_errs), 3)
                                     if macro_errs else None),
        'panel_mean_abs_rel_error': (round(sum(abs_rel_errs) / len(abs_rel_errs), 3)
                                     if abs_rel_errs else None),
        'resolved_mass_fraction': round(ing_mass_sum / denom, 3),
    }


def _dominant_major_group(per100g: Dict[str, float]) -> Optional[str]:
    best, best_v = None, 0.0
    for comp in FPED_MAJOR_GROUPS:
        v = float(per100g.get(comp, 0.0) or 0.0)
        if v > best_v:
            best, best_v = comp, v
    return best


def fndds_recipe_comparison(
    food_id: int,
    ingredients: List[Dict],
    conf_floor: float = 0.7,
) -> Optional[Dict]:
    """Lens 4: compare the decomposition's FPED food-group rollup to USDA's authoritative
    FNDDS recipe (input_food.csv -> FPID) for a CNF composite bridged at >= conf_floor.

    Returns cosine over the 37 FPED components, ingredient counts (LLM vs FNDDS), and
    whether the dominant major food group agrees. None when the food has no bridge meeting
    the floor or no FNDDS recipe.
    """
    meta = get_food_meta(int(food_id))
    if meta is None or float(meta.get('bridge_confidence', 0.0) or 0.0) < conf_floor:
        return None
    rec = _recipe(int(food_id), conf_floor)
    if rec is None:
        return None
    _m, fings, total_recipe_g = rec

    # LLM decomposition -> per-100 g-of-dish FPED vector.
    agg = aggregate_fped(ingredients)
    ing_mass = sum(float(i.get('mass_g', 0.0) or 0.0) for i in ingredients)
    if ing_mass <= 0:
        return None
    llm_vec = {k: agg.component_totals.get(k, 0.0) / ing_mass * 100.0 for k in _BASE_COMPONENTS}
    llm_major = {c: agg.component_totals.get(c, 0.0) / ing_mass * 100.0 for c in FPED_MAJOR_GROUPS}

    # FNDDS authoritative recipe -> per-100 g-of-dish FPED vector (FPID ingredient rollup).
    fndds_vec = {k: 0.0 for k in _BASE_COMPONENTS}
    fndds_major = {c: 0.0 for c in FPED_MAJOR_GROUPS}
    for ing in fings:
        comp100 = _ingredient_components_per_100g(ing.pattern_equivalents)
        share = float(ing.gram_weight or 0.0) / total_recipe_g
        for k in _BASE_COMPONENTS:
            fndds_vec[k] += comp100.get(k, 0.0) * share
        for c in FPED_MAJOR_GROUPS:
            fndds_major[c] += comp100.get(c, 0.0) * share

    cos = _cosine(llm_vec, fndds_vec, _BASE_COMPONENTS)
    llm_dom = _dominant_major_group(llm_major)
    fndds_dom = _dominant_major_group(fndds_major)
    return {
        'available': True,
        'food_id': int(food_id),
        'bridge_confidence': round(float(meta['bridge_confidence']), 2),
        'fped_rollup_cosine': (round(cos, 3) if cos is not None else None),
        'llm_n_ingredients': len(ingredients),
        'fndds_n_ingredients': len(fings),
        'llm_dominant_group': (FPED_MAJOR_GROUPS[llm_dom][0] if llm_dom else None),
        'fndds_dominant_group': (FPED_MAJOR_GROUPS[fndds_dom][0] if fndds_dom else None),
        'dominant_group_agree': bool(llm_dom is not None and llm_dom == fndds_dom),
    }
