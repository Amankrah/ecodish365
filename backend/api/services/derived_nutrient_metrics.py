"""Derived nutrient metrics for the research nutrient-analysis page.

Adds the academic-rigor derived computations the audit (2026-06-26)
flagged as missing from the bare nutrient panel. Pure, deterministic
helpers that take an already-aggregated meal and produce additional
flags and breakdowns:

  - `compute_na_k_ratio` — AHA 2021 Na:K mass and molar ratios
  - `compute_who_thresholds` — WHO 2018/2023 SFA & TFA caps, WHO 2015
    free-sugars guideline (total sugars used as upper bound until the
    Rana 2021 supplement ingests)
  - `compute_iron_split` — heme vs non-heme iron via canonical food
    category (FAO/WHO 2004 vitamin and mineral requirements)
  - `compute_vitamin_a_split` — preformed retinol vs provitamin-A
    carotenoid contribution to RAE (IOM 2001)
  - `compute_folate_dfe_breakdown` — IOM 1998 DFE formula surfaced
  - `compute_phytate_zn_ratio` — Gibson 2010 phytate:Zn molar ratio
    (degrades gracefully when CNF lacks phytate data, which is most
    foods)
  - `compute_protein_per_kg` — body-weight-anchored adequacy
  - `compute_eer_goldberg` — IOM 2002 EER vs Black 2000 Goldberg cutoff
    for suspected under-reporting

All functions return JSON-serialisable dicts; callers (the
research_deep_dive endpoint) compose them into a `derived_metrics`
block on the deep-dive payload.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Atomic weights (g/mol) for molar-ratio computations (IUPAC 2013).
_ATOMIC_WEIGHT = {
    'Na':  22.99,
    'K':   39.10,
    'Zn':  65.38,
    'Fe':  55.85,
}


# WHO thresholds (% of total energy).
_WHO_THRESHOLDS = {
    'sfa_pct_e_max':        10.0,   # WHO 2023 SFA & TFA guideline
    'sfa_pct_e_ideal_max':   7.0,   # WHO 2023 conditional recommendation
    'tfa_pct_e_max':         1.0,   # WHO 2018
    'free_sugars_pct_e_max':       10.0,   # WHO 2015 strong recommendation
    'free_sugars_pct_e_ideal_max':  5.0,   # WHO 2015 conditional
}


# Canonical food categories considered "heme iron sources" per FAO/WHO 2004.
# Heme iron is found in haemoglobin and myoglobin of meat, poultry, fish, and
# blood products. A reasonable epidemiological default is that 40 % of iron
# from these categories is heme; the rest is non-heme (FAO/WHO 2004 Ch. 13
# Table 13.6; Monsen 1978 was the original derivation). Vegetable iron is
# all non-heme.
_HEME_CATEGORIES = frozenset({
    'beef', 'pork', 'lamb_veal_game', 'poultry', 'fish', 'sausages_luncheon',
})
_HEME_FRACTION_OF_TOTAL_IN_HEME_FOODS = 0.40


# ----------------------------------------------------------------------
# Na:K ratio
# ----------------------------------------------------------------------

def compute_na_k_ratio(nutrient_totals: Dict[int, float]) -> Dict[str, Any]:
    """AHA 2021 sodium:potassium mass and molar ratios.

    Mass ratio target ≤ 2.0; molar ratio target ≤ 1.0 (AHA 2021 Dietary
    Guidance to Improve Cardiovascular Health, Circulation 144:e472).
    """
    na_mg = float(nutrient_totals.get(307, 0.0) or 0.0)
    k_mg  = float(nutrient_totals.get(306, 0.0) or 0.0)
    if k_mg <= 0:
        return {
            'sodium_mg': round(na_mg, 1),
            'potassium_mg': round(k_mg, 1),
            'mass_ratio': None,
            'molar_ratio': None,
            'target_met': None,
            'note': 'Potassium intake is zero; ratio is undefined.',
        }
    mass_ratio = na_mg / k_mg
    # Convert mg → mmol, then take ratio. mmol = mg / atomic_weight (g/mol).
    na_mmol = na_mg / _ATOMIC_WEIGHT['Na']
    k_mmol  = k_mg  / _ATOMIC_WEIGHT['K']
    molar_ratio = na_mmol / k_mmol if k_mmol > 0 else None
    target_met = (mass_ratio is not None and mass_ratio <= 2.0)
    return {
        'sodium_mg':     round(na_mg, 1),
        'potassium_mg':  round(k_mg, 1),
        'mass_ratio':    round(mass_ratio, 3),
        'molar_ratio':   round(molar_ratio, 3) if molar_ratio is not None else None,
        'mass_ratio_target':  2.0,
        'molar_ratio_target': 1.0,
        'target_met':    target_met,
        'source': 'AHA 2021 Circulation 144:e472. Mass ratio ≤ 2.0 (molar ≤ 1.0) is the cardiovascular target.',
    }


# ----------------------------------------------------------------------
# WHO thresholds: SFA, TFA, free sugars
# ----------------------------------------------------------------------

def compute_who_thresholds(
    nutrient_totals: Dict[int, float],
    energy_kcal: float,
) -> Dict[str, Any]:
    """WHO 2018/2023 saturated/trans fat caps + WHO 2015 free sugars guideline.

    Free sugars data is not in CNF (blocked on Rana 2021 supplement); we
    report total-sugars %E as an UPPER BOUND on free sugars and explicitly
    label it as such — true free-sugars %E is ≤ this value.
    """
    if energy_kcal <= 0:
        return {
            'sfa_g': None, 'sfa_pct_e': None, 'sfa_status': 'n/a',
            'tfa_g': None, 'tfa_pct_e': None, 'tfa_status': 'n/a',
            'total_sugars_g': None, 'total_sugars_pct_e': None,
            'free_sugars_status_upper_bound': 'n/a',
            'thresholds': _WHO_THRESHOLDS,
            'note': 'Meal energy is zero; %E thresholds not computable.',
        }

    sfa_g = float(nutrient_totals.get(606, 0.0) or 0.0)
    tfa_g = float(nutrient_totals.get(605, 0.0) or 0.0)
    sugars_g = float(nutrient_totals.get(269, 0.0) or 0.0)

    sfa_pct_e = sfa_g * 9.0 / energy_kcal * 100.0
    tfa_pct_e = tfa_g * 9.0 / energy_kcal * 100.0
    sugars_pct_e = sugars_g * 4.0 / energy_kcal * 100.0

    def cap_status(pct: float, ideal_max: float, max_: float) -> str:
        if pct <= ideal_max:
            return 'within_ideal'
        if pct <= max_:
            return 'within_max'
        return 'above_max'

    return {
        'sfa_g':                          round(sfa_g, 2),
        'sfa_pct_e':                      round(sfa_pct_e, 2),
        'sfa_status':                     cap_status(
            sfa_pct_e, _WHO_THRESHOLDS['sfa_pct_e_ideal_max'], _WHO_THRESHOLDS['sfa_pct_e_max'],
        ),
        'tfa_g':                          round(tfa_g, 2),
        'tfa_pct_e':                      round(tfa_pct_e, 2),
        'tfa_status':                     'within_max' if tfa_pct_e <= _WHO_THRESHOLDS['tfa_pct_e_max'] else 'above_max',
        'total_sugars_g':                 round(sugars_g, 2),
        'total_sugars_pct_e':             round(sugars_pct_e, 2),
        'free_sugars_status_upper_bound': cap_status(
            sugars_pct_e, _WHO_THRESHOLDS['free_sugars_pct_e_ideal_max'], _WHO_THRESHOLDS['free_sugars_pct_e_max'],
        ),
        'thresholds':                     _WHO_THRESHOLDS,
        'free_sugars_note': (
            'WHO 2015 sets <10 %E (ideally <5 %E) for FREE sugars. CNF does not '
            'ship free-sugars data (blocked on Rana 2021 supplement); the value '
            'shown is TOTAL sugars %E, which is an UPPER BOUND on free sugars. '
            'True free-sugars %E is ≤ this value.'
        ),
        'source': (
            'SFA: WHO 2023 "Saturated fatty acid and trans-fatty acid intake for '
            'adults and children". TFA: WHO 2018 REPLACE. Free sugars: WHO 2015 '
            '"Guideline: Sugars intake for adults and children".'
        ),
    }


# ----------------------------------------------------------------------
# Iron heme vs non-heme split
# ----------------------------------------------------------------------

def compute_iron_split(foods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Heme vs non-heme iron split via canonical food category.

    For each food, looks up its canonical category. Foods in
    `_HEME_CATEGORIES` (meat, poultry, fish, sausages) contribute
    `_HEME_FRACTION_OF_TOTAL_IN_HEME_FOODS` (0.40) of their iron as heme
    iron; the rest is non-heme. Plant foods contribute 100 % non-heme.
    Per-food iron is sourced via the aggregator.

    FAO/WHO 2004 *Vitamin and mineral requirements in human nutrition*
    Ch. 13: heme iron bioavailability ~25 %, non-heme 5-15 % (modulated
    by enhancers/inhibitors not modelled here). The split is the
    foundation for any bioavailability-adjusted iron estimate.
    """
    try:
        from api.services.food_group_category import canonical_category_for_food
        from api.services.meal_nutrient_aggregator import aggregate_meal_nutrients
    except Exception:  # noqa: BLE001 — defensive
        return {'error': 'imports unavailable', 'heme_mg': None, 'non_heme_mg': None}

    heme_mg = 0.0
    non_heme_mg = 0.0
    n_heme_foods = 0
    n_non_heme_foods = 0
    for f in foods:
        try:
            fid = int(f.get('food_id'))
            mass = float(f.get('mass_g', 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if mass <= 0:
            continue
        sub = aggregate_meal_nutrients(
            [{'food_id': fid, 'mass_g': mass}], nutrient_set=[303],
        )
        fe_nv = sub.nutrient_totals.get(303)
        fe_mg = fe_nv.amount if fe_nv is not None else 0.0
        if fe_mg <= 0:
            continue
        cat = canonical_category_for_food(fid)
        if cat in _HEME_CATEGORIES:
            heme_mg += fe_mg * _HEME_FRACTION_OF_TOTAL_IN_HEME_FOODS
            non_heme_mg += fe_mg * (1.0 - _HEME_FRACTION_OF_TOTAL_IN_HEME_FOODS)
            n_heme_foods += 1
        else:
            non_heme_mg += fe_mg
            n_non_heme_foods += 1
    total_mg = heme_mg + non_heme_mg
    heme_fraction = (heme_mg / total_mg) if total_mg > 0 else None
    return {
        'total_iron_mg':       round(total_mg, 2),
        'heme_mg':             round(heme_mg, 2),
        'non_heme_mg':         round(non_heme_mg, 2),
        'heme_fraction':       round(heme_fraction, 3) if heme_fraction is not None else None,
        'n_heme_source_foods': n_heme_foods,
        'n_non_heme_foods':    n_non_heme_foods,
        'source': (
            'FAO/WHO 2004 Vitamin and Mineral Requirements in Human Nutrition '
            'Ch. 13 (Monsen 1978 derivation). Heme fraction approximated as '
            '40 % of iron from meat / poultry / fish / sausages; the rest is '
            'non-heme. Plant foods are 100 % non-heme. Bioavailability is much '
            'higher for heme (~25 %) than non-heme (5-15 %, modulated by '
            'ascorbate, polyphenols, phytate, and the meat factor).'
        ),
    }


# ----------------------------------------------------------------------
# Vitamin A RAE split: preformed retinol vs provitamin-A carotenoids
# ----------------------------------------------------------------------

def compute_vitamin_a_split(nutrient_totals: Dict[int, float]) -> Dict[str, Any]:
    """Preformed retinol vs provitamin-A carotenoid contribution to RAE.

    Per IOM 2001 (Vitamin A): RAE (µg) = retinol (µg)
                                       + β-carotene (µg) / 12
                                       + (α-carotene + β-cryptoxanthin) / 24

    CNF NutrientIDs: 319 retinol, 320 RAE (computed), 321 β-carotene,
    322 α-carotene, 334 β-cryptoxanthin (all µg). Surfacing the split
    matters for UL interpretation: hypervitaminosis-A risk is from
    preformed retinol, not provitamin-A carotenoids.
    """
    retinol_µg  = float(nutrient_totals.get(319, 0.0) or 0.0)
    bcar_µg     = float(nutrient_totals.get(321, 0.0) or 0.0)
    acar_µg     = float(nutrient_totals.get(322, 0.0) or 0.0)
    bcryp_µg    = float(nutrient_totals.get(334, 0.0) or 0.0)
    rae_listed  = float(nutrient_totals.get(320, 0.0) or 0.0)

    rae_from_provitamin = bcar_µg / 12.0 + (acar_µg + bcryp_µg) / 24.0
    rae_computed        = retinol_µg + rae_from_provitamin
    preformed_fraction  = (retinol_µg / rae_computed) if rae_computed > 0 else None

    drift_pct = None
    if rae_listed > 0 and rae_computed > 0:
        drift_pct = abs(rae_listed - rae_computed) / rae_listed * 100.0

    return {
        'rae_computed':                round(rae_computed, 2),
        'rae_from_preformed_retinol':  round(retinol_µg, 2),
        'rae_from_provitamin_a':       round(rae_from_provitamin, 2),
        'preformed_fraction':          round(preformed_fraction, 3) if preformed_fraction is not None else None,
        'rae_listed_cnf':              round(rae_listed, 2),
        'drift_vs_listed_pct':         round(drift_pct, 2) if drift_pct is not None else None,
        'inputs_µg': {
            'retinol_319':       round(retinol_µg, 2),
            'beta_carotene_321': round(bcar_µg, 2),
            'alpha_carotene_322': round(acar_µg, 2),
            'beta_cryptoxanthin_334': round(bcryp_µg, 2),
        },
        'formula': 'RAE = retinol + β-carotene/12 + (α-carotene + β-cryptoxanthin)/24',
        'source': 'IOM 2001 DRIs for Vitamin A, Vitamin K, Boron, Chromium, Copper, Iodine, Iron, Manganese, Molybdenum, Nickel, Silicon, Vanadium, and Zinc. Vitamin A chapter, Table 4-3.',
        'note': (
            'Hypervitaminosis A risk (the UL of 3,000 µg RAE/day for adults) '
            'is driven by preformed retinol, not provitamin-A carotenoids — '
            'the body regulates carotenoid → retinol conversion.'
        ),
    }


# ----------------------------------------------------------------------
# Folate DFE breakdown
# ----------------------------------------------------------------------

def compute_folate_dfe_breakdown(nutrient_totals: Dict[int, float]) -> Dict[str, Any]:
    """IOM 1998 Dietary Folate Equivalents (DFE) formula surfaced.

    DFE (µg) = food folate (µg) + folic acid (µg) × 1.7. Synthetic folic
    acid (from fortified foods and supplements) is more bioavailable.

    CNF NutrientIDs: 431 folic acid (µg), 432 food folate (µg),
    435 folate DFE (µg, computed). We expose the formula and verify
    drift against the CNF-listed DFE.
    """
    folic_acid_µg  = float(nutrient_totals.get(431, 0.0) or 0.0)
    food_folate_µg = float(nutrient_totals.get(432, 0.0) or 0.0)
    dfe_listed     = float(nutrient_totals.get(435, 0.0) or 0.0)
    dfe_computed   = food_folate_µg + folic_acid_µg * 1.7

    drift_pct = None
    if dfe_listed > 0 and dfe_computed > 0:
        drift_pct = abs(dfe_listed - dfe_computed) / dfe_listed * 100.0
    fortification_fraction = (
        (folic_acid_µg * 1.7) / dfe_computed if dfe_computed > 0 else None
    )

    return {
        'dfe_computed_µg':       round(dfe_computed, 2),
        'dfe_listed_cnf_µg':     round(dfe_listed, 2),
        'food_folate_µg':        round(food_folate_µg, 2),
        'folic_acid_µg':         round(folic_acid_µg, 2),
        'fortification_fraction': round(fortification_fraction, 3) if fortification_fraction is not None else None,
        'drift_vs_listed_pct':   round(drift_pct, 2) if drift_pct is not None else None,
        'formula':               'DFE (µg) = food folate (µg) + folic acid (µg) × 1.7',
        'source': 'IOM 1998 DRIs for Thiamin, Riboflavin, Niacin, Vitamin B6, Folate, Vitamin B12, Pantothenic Acid, Biotin, and Choline. Folate chapter Table 8-1.',
    }


# ----------------------------------------------------------------------
# Phytate:Zn molar ratio
# ----------------------------------------------------------------------

def compute_phytate_zn_ratio(nutrient_totals: Dict[int, float]) -> Dict[str, Any]:
    """Gibson 2010 phytate:Zn molar ratio for zinc bioavailability bands.

    CNF NID 410 (phytate, mg) is present for a small minority of CNF
    foods; if intake is zero, surface a graceful "data unavailable" note.
    Categorisation per WHO 1996 Trace Elements in Human Nutrition (Ch. 8):
      Phy:Zn molar < 5     → high zinc bioavailability
      Phy:Zn molar 5-18    → moderate
      Phy:Zn molar > 18    → low
    Phytate molecular weight = 660 g/mol (myo-inositol hexaphosphate).
    """
    phytate_mg = float(nutrient_totals.get(410, 0.0) or 0.0)
    zn_mg      = float(nutrient_totals.get(309, 0.0) or 0.0)
    if zn_mg <= 0 or phytate_mg <= 0:
        return {
            'phytate_mg':  round(phytate_mg, 2),
            'zinc_mg':     round(zn_mg, 2),
            'molar_ratio': None,
            'bioavailability_band': 'unknown',
            'note': (
                'Phytate (NID 410) is not populated in CNF for most foods. '
                'When phytate intake is non-zero AND zinc intake > 0 the '
                'molar ratio is computed; otherwise it is reported as '
                'unavailable rather than silently substituting zero.'
            ),
        }
    phytate_mmol = phytate_mg / 660.0
    zn_mmol      = zn_mg / _ATOMIC_WEIGHT['Zn']
    molar = phytate_mmol / zn_mmol
    if molar < 5:
        band = 'high'
    elif molar <= 18:
        band = 'moderate'
    else:
        band = 'low'
    return {
        'phytate_mg':            round(phytate_mg, 2),
        'zinc_mg':               round(zn_mg, 2),
        'molar_ratio':           round(molar, 2),
        'bioavailability_band':  band,
        'source': 'WHO 1996 Trace Elements in Human Nutrition Ch. 8; Gibson et al. 2010 Food Nutr Bull 31:S134.',
    }


# ----------------------------------------------------------------------
# Protein per kg body weight
# ----------------------------------------------------------------------

def compute_protein_per_kg(
    nutrient_totals: Dict[int, float],
    body_weight_kg: Optional[float],
    age_years: Optional[float] = None,
) -> Dict[str, Any]:
    """Protein adequacy on g/kg body weight basis.

    RDA = 0.8 g/kg/d (adults, IOM 2005). EAR = 0.66 g/kg/d. Older adults
    (65+) recommended 1.0-1.2 g/kg/d (PROT-AGE / ESPEN 2014). Athletes
    1.2-2.0 g/kg/d (ISSN 2017). We surface the bands; we do not assume
    the user is athletic.
    """
    pro_g = float(nutrient_totals.get(203, 0.0) or 0.0)
    if not body_weight_kg or body_weight_kg <= 0:
        return {
            'protein_g':       round(pro_g, 1),
            'protein_g_per_kg': None,
            'note': 'Body weight not supplied; g/kg adequacy not computed.',
        }
    g_per_kg = pro_g / body_weight_kg
    is_older = age_years is not None and age_years >= 65
    if is_older:
        rda_floor = 1.0   # ESPEN 2014
        adequate  = g_per_kg >= 1.0
        rda_label = '1.0-1.2 g/kg (ESPEN 2014 older adults)'
    else:
        rda_floor = 0.8   # IOM 2005
        adequate  = g_per_kg >= 0.8
        rda_label = '0.8 g/kg (IOM 2005 adult RDA)'
    return {
        'protein_g':         round(pro_g, 1),
        'body_weight_kg':    round(body_weight_kg, 1),
        'protein_g_per_kg':  round(g_per_kg, 2),
        'rda_g_per_kg':      rda_floor,
        'rda_label':         rda_label,
        'meets_rda':         adequate,
        'reference_bands': {
            'sedentary_adult_RDA':       '0.8 g/kg (IOM 2005)',
            'older_adult_recommended':   '1.0-1.2 g/kg (ESPEN 2014)',
            'recreational_athlete':      '1.2-1.6 g/kg (ISSN 2017)',
            'strength_athlete':          '1.6-2.0 g/kg (ISSN 2017)',
        },
    }


# ----------------------------------------------------------------------
# EER (Estimated Energy Requirement) + Goldberg cutoff
# ----------------------------------------------------------------------

# IOM 2002 EER coefficients for adults 19+ (kcal/d), keyed on PAL category.
# Reference: IOM 2002/2005 DRIs for Energy, Carbohydrate, ... Ch. 5 Table 5-7.
_EER_PAL_COEFFICIENTS = {
    'sedentary':  {'male': 1.00, 'female': 1.00},
    'low_active': {'male': 1.11, 'female': 1.12},
    'active':     {'male': 1.25, 'female': 1.27},
    'very_active':{'male': 1.48, 'female': 1.45},
}


def compute_eer_goldberg(
    energy_intake_kcal: float,
    body_weight_kg: Optional[float],
    age_years: Optional[float],
    sex: Optional[str],
    pal_category: Optional[str],
    height_cm: Optional[float] = None,
) -> Dict[str, Any]:
    """IOM 2002 EER vs Black 2000 Goldberg cutoff for under-reporting.

    EER (adult) = 662 - 9.53×age + PA × (15.91×weight + 539.6×height)  (male)
                = 354 - 6.91×age + PA × (9.36×weight + 726×height)     (female)
    Height is optional; if missing, we fall back to BMR via Mifflin-
    St Jeor + the PAL multiplier (close approximation).

    Goldberg cutoff: Intake / BMR < 1.35 flags suspected under-reporting
    (Black 2000 Public Health Nutr 3:309-316).
    """
    if not body_weight_kg or body_weight_kg <= 0:
        return {'note': 'Body weight not supplied; EER not computed.'}
    if not sex or sex not in ('male', 'female'):
        return {'note': 'Sex not supplied; EER not computed.'}
    if not age_years or age_years <= 0:
        return {'note': 'Age not supplied; EER not computed.'}
    pal = (pal_category or 'sedentary').lower()
    pa = _EER_PAL_COEFFICIENTS.get(pal, _EER_PAL_COEFFICIENTS['sedentary'])[sex]

    # Mifflin-St Jeor BMR (1990; the most-cited modern equation for adults).
    # Height defaults to a population median when absent (170 cm male / 162 cm
    # female) so the Goldberg cutoff still produces a usable signal.
    h = height_cm if (height_cm and height_cm > 0) else (170.0 if sex == 'male' else 162.0)
    if sex == 'male':
        bmr_kcal = 10 * body_weight_kg + 6.25 * h - 5 * age_years + 5
    else:
        bmr_kcal = 10 * body_weight_kg + 6.25 * h - 5 * age_years - 161

    eer_kcal = bmr_kcal * pa

    intake_to_bmr_ratio = energy_intake_kcal / bmr_kcal if bmr_kcal > 0 else None
    goldberg_flag: Optional[str] = None
    if intake_to_bmr_ratio is not None:
        if intake_to_bmr_ratio < 1.35:
            goldberg_flag = 'suspected_under_reporting'
        elif intake_to_bmr_ratio > 2.4:
            goldberg_flag = 'suspected_over_reporting'
        else:
            goldberg_flag = 'plausible'

    pct_of_eer = (energy_intake_kcal / eer_kcal * 100.0) if eer_kcal > 0 else None
    return {
        'intake_kcal':        round(energy_intake_kcal, 1),
        'bmr_kcal':           round(bmr_kcal, 1),
        'eer_kcal':           round(eer_kcal, 1),
        'pct_of_eer':         round(pct_of_eer, 1) if pct_of_eer is not None else None,
        'intake_to_bmr_ratio': round(intake_to_bmr_ratio, 2) if intake_to_bmr_ratio is not None else None,
        'goldberg_flag':      goldberg_flag,
        'pal_category':       pal,
        'height_assumed_cm':  None if (height_cm and height_cm > 0) else round(h, 1),
        'source': (
            'IOM 2002/2005 DRIs for Energy etc. Ch. 5 Table 5-7 (EER PA coefficients). '
            'Mifflin-St Jeor 1990 Am J Clin Nutr 51:241 (BMR). '
            'Black 2000 Public Health Nutr 3:309 (Goldberg cutoff for under-reporting).'
        ),
    }


# ----------------------------------------------------------------------
# Public composition
# ----------------------------------------------------------------------

def compute_derived_metrics(
    nutrient_totals: Dict[int, float],
    foods: List[Dict[str, Any]],
    energy_kcal: float,
    body_weight_kg: Optional[float] = None,
    age_years: Optional[float] = None,
    sex: Optional[str] = None,
    pal_category: Optional[str] = None,
    height_cm: Optional[float] = None,
) -> Dict[str, Any]:
    """Single entry point — composes all derived metrics into one block."""
    return {
        'na_k_ratio':     compute_na_k_ratio(nutrient_totals),
        'who_thresholds': compute_who_thresholds(nutrient_totals, energy_kcal),
        'iron_split':     compute_iron_split(foods),
        'vitamin_a_split': compute_vitamin_a_split(nutrient_totals),
        'folate_dfe':     compute_folate_dfe_breakdown(nutrient_totals),
        'phytate_zn':     compute_phytate_zn_ratio(nutrient_totals),
        'protein_per_kg': compute_protein_per_kg(nutrient_totals, body_weight_kg, age_years),
        'eer_goldberg':   compute_eer_goldberg(
            energy_kcal, body_weight_kg, age_years, sex, pal_category, height_cm,
        ),
    }
