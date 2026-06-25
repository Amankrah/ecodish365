"""
Additional methods for HENICalculator
Separated to keep main calculator clean.

This module performs per-ingredient risk-factor extraction and applies the two
double-counting carve-outs from Stylianou et al. 2021 SI §S2.9 (pp. 35-36)
before passing the aggregated dict to the Rust HENI engine:

  1. Milk-vs-calcium: foods classified as milk emit only the `milk` DRF; their
     calcium is suppressed (the colorectal-cancer benefit is already counted
     via milk).
  2. Fibre-source split: fibre from foods also classified as fruits, vegetables,
     legumes, or whole-grains routes to `fiber_fvlw` (CRC only); fibre from
     other sources routes to `fiber_other` (CRC + IHD).

Source: Stylianou KS, Fulgoni VL III, Jolliet O. Nat Food 2021;2(8):616-627
Supplementary Information, S2.9 pp. 35-36 and Methods p. 626.
"""

from typing import Dict, List, Tuple
import logging

from ..data.composition_loader import get_composition_for_food

logger = logging.getLogger(__name__)


# Plant-based "milks" that must NOT receive the dairy-milk DRF.
# Per GBD 2017 Diet Collaborators table p. 1960 the milk risk factor is
# defined as "non-fat / low-fat / full-fat milk; excludes soy milk and plant
# derivatives". Detection is by description substring.
_PLANT_MILK_INDICATORS = (
    "soy milk", "soy beverage", "almond milk", "almond beverage",
    "oat milk", "oat beverage", "rice milk", "rice beverage",
    "coconut milk", "coconut beverage", "cashew milk", "cashew beverage",
    "hemp milk", "hemp beverage", "pea milk", "pea beverage",
    "plant-based milk", "plant based milk",
)

# Non-SSB beverages that must NOT be routed to sugar_sweetened_beverages even
# when in the CNF "Beverages" food group. 100 % fruit/vegetable juice is
# excluded from SSB per the GBD 2017 SSB definition (p. 1960).
_NON_SSB_BEVERAGE_INDICATORS = (
    "water", "tea", "coffee", "espresso", "broth", "stock", "bouillon",
    "100% juice", "100 % juice", "fruit juice", "vegetable juice",
)

# Food groups that emit one of the f/v/l/w factors. Fibre extracted from a
# food in any of these groups routes to `fiber_fvlw`; fibre from foods not in
# any of these groups routes to `fiber_other` (Stylianou SI §S2.9).
_FVLW_CLASSES = frozenset({"fruits", "vegetables", "legumes", "whole_grains"})


def _is_plant_milk(food_description_lower: str) -> bool:
    return any(ind in food_description_lower for ind in _PLANT_MILK_INDICATORS)


def _is_non_ssb_beverage(food_description_lower: str) -> bool:
    return any(ind in food_description_lower for ind in _NON_SSB_BEVERAGE_INDICATORS)


def _category_food_group_attribution(
    canonical_category: str,
    food_description: str,
    nutrient_data: Dict[str, float],
    risk_factors: Dict[str, float],
) -> None:
    """Canonical-category-driven food-group attribution for foods NOT in the
    FPED-grounded composition lookup. Mutates `risk_factors` in place.

    Replaces the previous CNF-name substring matcher (FDC-MULTI-SOURCE
    2026-06-26) — see `code_action_items.md`. The composition lookup at
    `heni_calculator.heni.data.composition_loader` is still the preferred
    path; this fallback fires only when a food (CNF, WAFCT, or FDC) has no
    FPED-bridged composition entry. Source-agnostic: WAFCT/FDC foods that
    map to the same canonical category get the same attribution as their
    CNF analogs.

    Keyword-gated branches (whole-grain, SSB exclusion, plant-milk,
    processed-meat) preserved verbatim — they read `food_description`
    which is source-agnostic.
    """
    # Canonical category → primary HENI risk-factor key. Several CNF concepts
    # collapse into the same HENI factor (e.g. dairy and dairy_egg_combined
    # both go to 'milk'; beef / pork / lamb_veal_game all go to 'red_meat').
    primary = _CATEGORY_TO_HENI_RISK_FACTOR.get(canonical_category)
    if primary is None:
        return  # category not relevant to HENI risk factors

    if primary == "_poultry_neutral":
        if any(t in food_description for t in
               ("sausage", "deli", "processed", "cured", "smoked", "ham", "bacon")):
            risk_factors["processed_meat"] = 100.0
    elif primary == "whole_grains":
        if any(t in food_description for t in (
            "whole grain", "whole-grain", "whole wheat", "100% whole",
            "wheat bran", "wheat germ", "oats, rolled", "oats, steel cut",
            "rolled oats", "quinoa", "brown rice",
        )):
            risk_factors[primary] = 100.0
    elif primary == "sugar_sweetened_beverages":
        if _is_non_ssb_beverage(food_description):
            return
        if nutrient_data.get("SUGARS, TOTAL", 0) > 5:
            risk_factors[primary] = 100.0
    elif primary == "milk":
        if _is_plant_milk(food_description):
            return
        risk_factors[primary] = 100.0
    elif primary == "red_meat":
        if any(t in food_description for t in (
            "processed", "sausage", "ham", "bacon", "deli", "cured", "smoked",
            "hot dog", "bologna", "salami", "pepperoni", "jerky",
        )):
            risk_factors["processed_meat"] = 100.0
        else:
            risk_factors["red_meat"] = 100.0
    elif primary == "processed_meat":
        risk_factors["processed_meat"] = 100.0
    else:
        risk_factors[primary] = 100.0


# Canonical category → HENI risk-factor name. `_poultry_neutral` is a
# sentinel that means "no attribution unless the food description signals
# processed". CNF FG1 ('dairy_egg_combined') and WAFCT 'dairy' both map
# to milk for the dairy-side attribution; the plant-milk filter inside
# `_category_food_group_attribution` excludes plant-based variants.
_CATEGORY_TO_HENI_RISK_FACTOR: Dict[str, str] = {
    'nuts_seeds':            'nuts_seeds',
    'cereals_grains':        'whole_grains',
    'breakfast_cereals':     'whole_grains',
    'fruits':                'fruits',
    'vegetables':            'vegetables',
    'legumes':               'legumes',
    'dairy':                 'milk',
    'dairy_egg_combined':    'milk',
    'beverages':             'sugar_sweetened_beverages',
    'beef':                  'red_meat',
    'pork':                  'red_meat',
    'lamb_veal_game':        'red_meat',
    'poultry':               '_poultry_neutral',
    'sausages_luncheon':     'processed_meat',
    # eggs, fish, fats_oils, spices_herbs, sweets, babyfoods, baked_products,
    # fast_foods, mixed_dishes, snacks, soups_sauces, alcoholic_beverages,
    # unknown → no fallback attribution; the FPED composition path
    # (preferred) handles ingredient-level decomposition for those.
}


def _apply_double_counting_carve_outs(
    risk_factors: Dict[str, float],
) -> Tuple[Dict[str, float], List[str]]:
    """
    Apply Stylianou 2021 SI §S2.9 (pp. 35-36) double-counting carve-outs:

      1. If `milk` is present, suppress `calcium` (milk DRF already carries
         the colorectal-cancer benefit).
      2. Replace `fiber` with `fiber_fvlw` (if any of fruits/vegetables/
         legumes/whole_grains is co-present) or `fiber_other` otherwise.

    Returns the modified dict and a list of audit-trail strings describing
    which carve-outs were applied (surfaced in the API response).
    """
    audit: List[str] = []

    # 1. Milk-vs-calcium carve-out.
    if risk_factors.get("milk", 0.0) > 0.0 and "calcium" in risk_factors:
        suppressed = risk_factors.pop("calcium")
        audit.append(
            f"milk_vs_calcium: suppressed calcium={suppressed:.4f}g because milk DRF "
            f"already counts the colorectal-cancer benefit (Stylianou 2021 Methods p. 626)."
        )

    # 2. Fibre-source split.
    fibre_total = risk_factors.pop("fiber", 0.0)
    if fibre_total > 0.0:
        has_fvlw = any(
            k in risk_factors and risk_factors[k] > 0.0 for k in _FVLW_CLASSES
        )
        if has_fvlw:
            risk_factors["fiber_fvlw"] = risk_factors.get("fiber_fvlw", 0.0) + fibre_total
            audit.append(
                f"fiber_source_split: routed {fibre_total:.4f}g to fiber_fvlw "
                f"(co-present with f/v/l/w; CRC benefit only)."
            )
        else:
            risk_factors["fiber_other"] = risk_factors.get("fiber_other", 0.0) + fibre_total
            audit.append(
                f"fiber_source_split: routed {fibre_total:.4f}g to fiber_other "
                f"(no f/v/l/w co-present; CRC + IHD benefit)."
            )

    return risk_factors, audit


def extract_risk_factors_from_ingredient(calculator, ingredient) -> Dict[str, float]:
    """
    Extract HENI risk-factor amounts (in grams of risk component, per 100 g of
    food) from a CNF-backed ingredient. Output is later scaled by ingredient
    amount and aggregated across the meal in `HENICalculator.calculate_heni`.

    Implements the Stylianou 2021 SI §S2.9 double-counting carve-outs and the
    GBD 2017 SSB / milk definitional exclusions (plant-based milks; juice/tea/
    coffee/water).
    """
    risk_factors: Dict[str, float] = {}
    # Per-ingredient TFA-imputation warnings, attached to the returned dict
    # under a sentinel key the meal-level aggregator reads then strips.
    imputation_warnings: List[str] = []

    # Get nutrient data from CNF
    nutrient_data = calculator.cnf_integrator.get_nutrient_data(ingredient.food_id)

    # Map CNF nutrients to HENI risk factors
    nutrient_mapping = {
        "FATTY ACIDS, POLYUNSATURATED, 22:6 N-3, DOCOSAHEXAENOIC (DHA)": "omega_3",
        "FATTY ACIDS, POLYUNSATURATED, 20:5 N-3, EICOSAPENTAENOIC (EPA)": "omega_3",
        "CALCIUM": "calcium",
        "FIBRE, TOTAL DIETARY": "fiber",
        "FATTY ACIDS, POLYUNSATURATED, TOTAL": "polyunsaturated_fatty_acids",
        "FATTY ACIDS, TRANS, TOTAL": "trans_fat",
        "SODIUM": "sodium",
    }

    # Extract nutrient-based risk factors
    omega_3_total = 0.0
    for nutrient_name, nutrient_value in nutrient_data.items():
        if nutrient_name in nutrient_mapping:
            heni_factor = nutrient_mapping[nutrient_name]
            if heni_factor == "omega_3":
                omega_3_total += nutrient_value
            else:
                # Convert mg to g for sodium and calcium if needed
                if nutrient_name in ["CALCIUM", "SODIUM"]:
                    risk_factors[heni_factor] = nutrient_value / 1000  # mg to g
                else:
                    risk_factors[heni_factor] = nutrient_value

    if omega_3_total > 0:
        risk_factors["omega_3"] = omega_3_total

    # TFA imputation flag: per Stylianou SI §S2.1 p. 12, ~60% of WWEIA foods
    # have imputed TFA via regression (R² = 0.69). For v1 we zero-with-warning
    # when CNF lacks measured TFA, rather than silently imputing.
    if "trans_fat" not in risk_factors:
        risk_factors["trans_fat"] = 0.0
        imputation_warnings.append(
            f"food_id={ingredient.food_id}: TFA not measured in CNF; "
            f"set to 0.0 g (Stylianou 2021 SI §S2.1 p. 12 imputation regression "
            f"not implemented; flag for review)."
        )

    # FDC-MULTI-SOURCE (2026-06-26): the legacy CNF group-name substring
    # matcher was replaced with the canonical-category bridge, so the
    # `calculator.cnf_integrator.get_food_group(...)` call here was dropped.
    # The canonical category is resolved below.
    food_description = calculator.cnf_integrator.get_food_description(
        ingredient.food_id
    ).lower()

    # 2026-05-23 (HENI-CODE-1.y cause A SHIPPED): food-group risk factors now
    # read from the USDA FPED-grounded composition lookup (built one-time via
    # `heni_calculator.heni.etl.build_cnf_heni_composition`). CNF foods not
    # in the bridge fall back to the legacy literal-100 attribution below.
    # The composition values are grams of risk-component category per 100g
    # of CNF food; the downstream scaler at `heni_calculator.py` multiplies
    # by (ingredient.amount / 100) to get per-serving masses.
    # FDC-MULTI-SOURCE (2026-06-26): resolve the canonical food category
    # once via the bridge — drives both the SSB beverage check below and
    # the fallback attribution for foods missing from the FPED composition
    # bridge. Source-aware: WAFCT/FDC foods get the same attribution as
    # their CNF equivalents.
    try:
        from api.services.food_group_category import canonical_category_for_food
        canonical_category = canonical_category_for_food(ingredient.food_id)
    except Exception:  # noqa: BLE001 — bridge module optional in some test paths
        canonical_category = 'unknown'

    composition = get_composition_for_food(ingredient.food_id)
    if composition:
        for risk_key, mass_per_100g in composition.items():
            if mass_per_100g <= 0:
                continue
            # Plant-milk exclusion (GBD 2017 p. 1960): plant-based "milks"
            # don't count as `milk` even if FPED attributes dairy mass.
            if risk_key == 'milk' and _is_plant_milk(food_description):
                continue
            risk_factors[risk_key] = mass_per_100g
        # SSB attribution is independent of FPED (no SSB column). Still
        # apply the existing keyword-driven SSB rule on beverage-category
        # foods that pass the non-SSB exclusion + sugar threshold. Was
        # `'Beverages' in food_group` (CNF-name substring) → now
        # canonical-category check, so WAFCT/FDC beverage rows are
        # honoured too.
        if canonical_category == 'beverages' and not _is_non_ssb_beverage(food_description):
            sugar_content = nutrient_data.get('SUGARS, TOTAL', 0)
            if sugar_content > 5:
                risk_factors['sugar_sweetened_beverages'] = 100.0
    else:
        # Fallback attribution for foods not bridged to FNDDS/FPED.
        # Canonical-category-driven (FDC-MULTI-SOURCE 2026-06-26) —
        # source-agnostic by construction; the previous CNF-name substring
        # matcher was deleted in this commit.
        _category_food_group_attribution(
            canonical_category, food_description, nutrient_data, risk_factors,
        )

    # 2026-05-23 (HENI-CODE-1.y quick-fix subset): the previous block here
    # invoked `calculator.categorizer.categorize_food()` and treated the
    # returned 0-1 presence scores as gram amounts via `confidence * 100.0`.
    # That was a category error: the LLM categorizer is documented to return
    # `{factor: presence_0_to_1}` ("Score 0 = not present, 1 = strongly present"),
    # not gram amounts. Multiplying a probability by 100 and writing it as
    # g/100g over-extracted PUFA by ~10x on poultry, treated sodium as 100
    # g/100g on processed-meat rows (TMREL-capped downstream but still wrong
    # upstream), and inflated food-group factors. The categorizer's outputs
    # are used correctly inside the categorizer itself; they should never
    # leave that module as a mass.
    _ = calculator  # categorizer intentionally not invoked here

    # Apply Stylianou 2021 SI §S2.9 double-counting carve-outs BEFORE returning.
    risk_factors, carve_out_audit = _apply_double_counting_carve_outs(risk_factors)

    # Attach audit-trail metadata under sentinel keys the aggregator reads then
    # strips before passing the dict to the Rust engine.
    if carve_out_audit or imputation_warnings:
        risk_factors["__audit_carve_outs__"] = carve_out_audit  # type: ignore[assignment]
        risk_factors["__imputation_warnings__"] = imputation_warnings  # type: ignore[assignment]

    return risk_factors


def calculate_meal_heni(calculator, ingredients: List) -> Dict:
    """Calculate HENI for a complete meal with detailed breakdown."""
    heni_result = calculator.calculate_heni(ingredients)

    # Format comprehensive result for API response. Existing key shapes are
    # preserved for frontend compatibility; new fields are additive.
    return {
        "heni_scores": {
            "total_heni_score": round(heni_result.total_heni_score, 2),
            "heni_per_100_kcal": round(heni_result.heni_per_100_kcal, 2),
            "heni_per_100_grams": round(heni_result.heni_per_100_grams, 2),
            "heni_per_serving": round(heni_result.heni_per_serving, 2),
        },
        "health_impact": {
            "health_impact_minutes": round(heni_result.health_impact_minutes, 1),
            "description": heni_result.health_impact_description,
        },
        "component_breakdown": {
            "food_group_contributions": {
                k: round(v, 2) for k, v in heni_result.food_group_contributions.items()
            },
            "nutrient_contributions": {
                k: round(v, 2) for k, v in heni_result.nutrient_contributions.items()
            },
        },
        "disease_burden_analysis": {
            "disease_breakdown": {
                k: round(v, 2) for k, v in heni_result.disease_burden_breakdown.items()
            },
            "methodology": (
                "Equal-share per outcome derived from Stylianou 2021 SI Table 1 "
                "pp. 4-5. Rederivation from the 6,195-pair GBD 2016 RR matrix is "
                "logged as HENI-CODE-1.x in code_action_items.md."
            ),
        },
        "risk_factor_analysis": {
            "risk_factors": {
                k: round(v, 4) for k, v in heni_result.risk_factor_amounts.items()
            },
            "warnings": heni_result.effective_range_warnings,
        },
        "meal_composition": {
            "total_energy_kcal": round(heni_result.total_energy_kcal, 1),
            "total_weight_grams": round(heni_result.total_weight_grams, 1),
            "ingredient_count": len(ingredients),
            "ingredient_details": heni_result.ingredient_details,
        },
    }
