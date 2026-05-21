//! HEFI-2019 thresholds and max-point constants.
//!
//! Mirrors `backend/hefi_calculator/hefi/config.py::HEFIThresholds`.

pub struct HefiThresholds {
    pub c1_vf_max: f64,
    pub c2_wholegr_max: f64,
    pub c3_grratio_max: f64,
    pub c4_profoods_max: f64,
    pub c5_plantpro_max: f64,
    pub c6_beverages_max: f64,
    pub c7_fattyacid_max: f64,
    pub c8_sfat_max: f64,
    pub c9_freesugars_max: f64,
    pub c10_sodium_max: f64,

    pub vf_ratio_max: f64,
    pub whole_grain_ratio_max: f64,
    pub grain_ratio_max: f64,
    pub protein_ratio_max: f64,
    pub plant_protein_ratio_max: f64,
    pub beverages_ratio_max: f64,
    pub fa_ratio_max: f64,

    pub sfa_percent_max: f64,
    pub free_sugars_percent_max: f64,
    pub sodium_density_min: f64,
}

pub const DEFAULT: HefiThresholds = HefiThresholds {
    c1_vf_max: 20.0,
    c2_wholegr_max: 5.0,
    c3_grratio_max: 5.0,
    c4_profoods_max: 5.0,
    c5_plantpro_max: 5.0,
    c6_beverages_max: 10.0,
    c7_fattyacid_max: 5.0,
    c8_sfat_max: 5.0,
    c9_freesugars_max: 10.0,
    c10_sodium_max: 10.0,

    vf_ratio_max: 0.50,
    whole_grain_ratio_max: 0.25,
    grain_ratio_max: 1.0,
    protein_ratio_max: 0.25,
    plant_protein_ratio_max: 0.25,
    beverages_ratio_max: 1.0,
    fa_ratio_max: 2.6,

    sfa_percent_max: 10.0,
    free_sugars_percent_max: 10.0,
    // Brassard 2022a Table 2 p. 600: max-score threshold for sodium density is
    // < 0.9 mg/kcal (10 pts). Linear-interpolated down to 0 pts at ≥ 2.0
    // mg/kcal. Pre-audit value was 1.0 (HEFI-CODE-1B fix, 2026-05-21).
    sodium_density_min: 0.9,
};
