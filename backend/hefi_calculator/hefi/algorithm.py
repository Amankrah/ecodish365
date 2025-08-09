from typing import Dict

from .config import HEFIConfig
from .models import HEFIInputs, HEFIComponentScores, HEFIResult


def _linear_score(value: float, min_threshold: float, max_threshold: float, min_points: float, max_points: float) -> float:
    if value <= min_threshold:
        return min_points
    if value >= max_threshold:
        return max_points
    # Linear interpolation
    return min_points + ((value - min_threshold) / (max_threshold - min_threshold)) * (max_points - min_points)


def compute_ratios(inputs: HEFIInputs) -> Dict[str, float]:
    ratios: Dict[str, float] = {}

    # Guard zeros
    tf = max(inputs.total_foods_ra, 0.0)
    tb = max(inputs.total_beverages_g, 0.0)
    kcal = max(inputs.energy_kcal, 0.0)

    # Food-based
    ratios['RATIO_VF'] = (inputs.vf_ra / tf) if tf > 0 else 0.0
    ratios['RATIO_WGTOT'] = (inputs.whole_grains_ra / tf) if tf > 0 else 0.0
    ratios['RATIO_WGGR'] = (inputs.whole_grains_ra / max(inputs.total_grains_ra, 0.0)) if inputs.total_grains_ra > 0 else 0.0
    ratios['RATIO_PRO'] = (inputs.protein_foods_ra / tf) if tf > 0 else 0.0
    ratios['RATIO_PLANT'] = (inputs.plant_protein_foods_ra / tf) if tf > 0 else 0.0

    # Beverages
    ratios['RATIO_BEV'] = (inputs.recommended_beverages_g / tb) if tb > 0 else 0.0

    # Fatty acids
    sfa = inputs.sfa_g
    mufa = inputs.mufa_g
    pufa = inputs.pufa_g
    ratios['RATIO_UNSFAT'] = (mufa + pufa) / sfa if sfa > 0 else 0.0

    # Nutrient percentages/densities
    ratios['SFA_PERC'] = (inputs.sfa_g * 9.0) / kcal * 100.0 if kcal > 0 else 0.0
    ratios['SUG_PERC'] = (inputs.free_sugars_g * 4.0) / kcal * 100.0 if kcal > 0 else 0.0
    ratios['SODDEN'] = inputs.sodium_mg / kcal * 1000.0 if kcal > 0 else 0.0

    return ratios


def score_components(ratios: Dict[str, float], config: HEFIConfig) -> HEFIComponentScores:
    t = config.thresholds

    # Adequacy components: linear interpolation from 0 to max threshold
    c1_vf = _linear_score(ratios['RATIO_VF'], 0.0, t.vf_ratio_max, 0.0, t.c1_vf_max)
    c2_wholegr = _linear_score(ratios['RATIO_WGTOT'], 0.0, t.whole_grain_ratio_max, 0.0, t.c2_wholegr_max)
    c3_grratio = _linear_score(ratios['RATIO_WGGR'], 0.0, t.grain_ratio_max, 0.0, t.c3_grratio_max)
    c4_profoods = _linear_score(ratios['RATIO_PRO'], 0.0, t.protein_ratio_max, 0.0, t.c4_profoods_max)
    c5_plantpro = _linear_score(ratios['RATIO_PLANT'], 0.0, t.plant_protein_ratio_max, 0.0, t.c5_plantpro_max)
    c6_beverages = _linear_score(ratios['RATIO_BEV'], 0.0, t.beverages_ratio_max, 0.0, t.c6_beverages_max)
    c7_fattyacid = _linear_score(ratios['RATIO_UNSFAT'], 0.0, t.fa_ratio_max, 0.0, t.c7_fattyacid_max)

    # Moderation components: max points at/below threshold, decreasing to 0 at high values
    # For SFA: max points at <= 10%, 0 points at >= 20%
    c8_sfat = _linear_score(ratios['SFA_PERC'], t.sfa_percent_max, 20.0, t.c8_sfat_max, 0.0)
    
    # For free sugars: max points at <= 10%, 0 points at >= 20%  
    c9_freesugars = _linear_score(ratios['SUG_PERC'], t.free_sugars_percent_max, 20.0, t.c9_freesugars_max, 0.0)
    
    # For sodium: max points at <= 1 mg/kcal, 0 points at >= 2 mg/kcal
    c10_sodium = _linear_score(ratios['SODDEN'], t.sodium_density_min, 2.0, t.c10_sodium_max, 0.0)

    return HEFIComponentScores(
        c1_vf=c1_vf,
        c2_wholegr=c2_wholegr,
        c3_grratio=c3_grratio,
        c4_profoods=c4_profoods,
        c5_plantpro=c5_plantpro,
        c6_beverages=c6_beverages,
        c7_fattyacid=c7_fattyacid,
        c8_sfat=c8_sfat,
        c9_freesugars=c9_freesugars,
        c10_sodium=c10_sodium,
    )


def compute_hefi(inputs: HEFIInputs, config: HEFIConfig = HEFIConfig()) -> HEFIResult:
    # Handle zero-intake edge case as per documentation
    if inputs.total_foods_ra == 0 or inputs.energy_kcal == 0:
        zero_scores = HEFIComponentScores(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        return HEFIResult(inputs=inputs, ratios={}, component_scores=zero_scores, total_score=0.0)

    ratios = compute_ratios(inputs)
    component_scores = score_components(ratios, config)
    total = component_scores.total
    return HEFIResult(inputs=inputs, ratios=ratios, component_scores=component_scores, total_score=total)


