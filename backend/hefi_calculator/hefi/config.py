from dataclasses import dataclass, field


@dataclass
class HEFIThresholds:
    # Max points for components
    c1_vf_max: float = 20.0
    c2_wholegr_max: float = 5.0
    c3_grratio_max: float = 5.0
    c4_profoods_max: float = 5.0
    c5_plantpro_max: float = 5.0
    c6_beverages_max: float = 10.0
    c7_fattyacid_max: float = 5.0
    c8_sfat_max: float = 5.0
    c9_freesugars_max: float = 10.0
    c10_sodium_max: float = 10.0

    # Adequacy component thresholds (max points at these values) - HEFI-2019 official
    vf_ratio_max: float = 0.50  # 50% of total foods RAs - official HEFI-2019 threshold
    whole_grain_ratio_max: float = 0.25  # Estimated from CFG-2019 recommendations  
    grain_ratio_max: float = 1.0  # 100% whole grains - official HEFI-2019
    protein_ratio_max: float = 0.25  # Estimated from CFG-2019 recommendations
    plant_protein_ratio_max: float = 0.25  # Estimated from CFG-2019 recommendations  
    beverages_ratio_max: float = 1.0  # 100% recommended beverages - official HEFI-2019
    fa_ratio_max: float = 2.6   # unsat:sat fat >= 2.6 gets max points - official HEFI-2019
    
    # Moderation component thresholds (max points at/below these values) - HEFI-2019 official
    sfa_percent_max: float = 10.0  # <= 10% of energy from SFA gets max points - official HEFI-2019
    free_sugars_percent_max: float = 10.0  # <= 10% of energy from free sugars gets max points - official HEFI-2019  
    sodium_density_min: float = 1.0  # <= 1 mg/kcal gets max points - official HEFI-2019 (2300mg/2300kcal)


@dataclass
class HEFIConfig:
    thresholds: HEFIThresholds = field(default_factory=HEFIThresholds)


