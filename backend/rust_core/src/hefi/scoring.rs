//! HEFI-2019 ratio computation and component scoring.
//!
//! Byte-for-byte mirror of `backend/hefi_calculator/hefi/algorithm.py`.
//! Behavior is preserved exactly, including quirks in SODDEN scaling,
//! so diff-testing against the Python baseline holds.

use crate::hefi::thresholds::{HefiThresholds, DEFAULT};

#[derive(Clone, Copy, Debug, Default)]
pub struct HefiInputs {
    pub total_foods_ra: f64,
    pub vf_ra: f64,
    pub whole_grains_ra: f64,
    pub total_grains_ra: f64,
    pub protein_foods_ra: f64,
    pub plant_protein_foods_ra: f64,
    pub total_beverages_g: f64,
    pub recommended_beverages_g: f64,
    pub energy_kcal: f64,
    pub sfa_g: f64,
    pub mufa_g: f64,
    pub pufa_g: f64,
    pub free_sugars_g: f64,
    pub sodium_mg: f64,
}

#[derive(Clone, Copy, Debug, Default)]
pub struct HefiRatios {
    pub ratio_vf: f64,
    pub ratio_wgtot: f64,
    pub ratio_wggr: f64,
    pub ratio_pro: f64,
    pub ratio_plant: f64,
    pub ratio_bev: f64,
    pub ratio_unsfat: f64,
    pub sfa_perc: f64,
    pub sug_perc: f64,
    pub sodden: f64,
}

#[derive(Clone, Copy, Debug, Default)]
pub struct HefiComponentScores {
    pub c1_vf: f64,
    pub c2_wholegr: f64,
    pub c3_grratio: f64,
    pub c4_profoods: f64,
    pub c5_plantpro: f64,
    pub c6_beverages: f64,
    pub c7_fattyacid: f64,
    pub c8_sfat: f64,
    pub c9_freesugars: f64,
    pub c10_sodium: f64,
}

impl HefiComponentScores {
    pub fn total(&self) -> f64 {
        self.c1_vf
            + self.c2_wholegr
            + self.c3_grratio
            + self.c4_profoods
            + self.c5_plantpro
            + self.c6_beverages
            + self.c7_fattyacid
            + self.c8_sfat
            + self.c9_freesugars
            + self.c10_sodium
    }
}

#[derive(Clone, Copy, Debug, Default)]
pub struct HefiResult {
    pub ratios: HefiRatios,
    pub scores: HefiComponentScores,
    pub total: f64,
    /// True when the zero-intake short-circuit was hit; ratios are meaningless.
    pub zero_intake: bool,
}

#[inline]
fn linear_score(value: f64, min_t: f64, max_t: f64, min_p: f64, max_p: f64) -> f64 {
    if value <= min_t {
        return min_p;
    }
    if value >= max_t {
        return max_p;
    }
    min_p + ((value - min_t) / (max_t - min_t)) * (max_p - min_p)
}

pub fn compute_ratios(inputs: &HefiInputs) -> HefiRatios {
    let tf = inputs.total_foods_ra.max(0.0);
    let tb = inputs.total_beverages_g.max(0.0);
    let kcal = inputs.energy_kcal.max(0.0);
    let total_grains = inputs.total_grains_ra.max(0.0);

    let ratio_vf = if tf > 0.0 { inputs.vf_ra / tf } else { 0.0 };
    let ratio_wgtot = if tf > 0.0 { inputs.whole_grains_ra / tf } else { 0.0 };
    let ratio_wggr = if total_grains > 0.0 {
        inputs.whole_grains_ra / total_grains
    } else {
        0.0
    };
    let ratio_pro = if tf > 0.0 { inputs.protein_foods_ra / tf } else { 0.0 };
    let ratio_plant = if tf > 0.0 {
        inputs.plant_protein_foods_ra / tf
    } else {
        0.0
    };
    let ratio_bev = if tb > 0.0 {
        inputs.recommended_beverages_g / tb
    } else {
        0.0
    };

    let sfa = inputs.sfa_g;
    let ratio_unsfat = if sfa > 0.0 {
        (inputs.mufa_g + inputs.pufa_g) / sfa
    } else {
        0.0
    };

    // Exactly mirror Python expression precedence:
    //   (sfa_g * 9.0) / kcal * 100.0
    //   (free_sugars_g * 4.0) / kcal * 100.0
    //   sodium_mg / kcal * 1000.0
    let (sfa_perc, sug_perc, sodden) = if kcal > 0.0 {
        (
            (inputs.sfa_g * 9.0) / kcal * 100.0,
            (inputs.free_sugars_g * 4.0) / kcal * 100.0,
            inputs.sodium_mg / kcal * 1000.0,
        )
    } else {
        (0.0, 0.0, 0.0)
    };

    HefiRatios {
        ratio_vf,
        ratio_wgtot,
        ratio_wggr,
        ratio_pro,
        ratio_plant,
        ratio_bev,
        ratio_unsfat,
        sfa_perc,
        sug_perc,
        sodden,
    }
}

pub fn score_components(r: &HefiRatios, t: &HefiThresholds) -> HefiComponentScores {
    HefiComponentScores {
        c1_vf: linear_score(r.ratio_vf, 0.0, t.vf_ratio_max, 0.0, t.c1_vf_max),
        c2_wholegr: linear_score(
            r.ratio_wgtot,
            0.0,
            t.whole_grain_ratio_max,
            0.0,
            t.c2_wholegr_max,
        ),
        c3_grratio: linear_score(r.ratio_wggr, 0.0, t.grain_ratio_max, 0.0, t.c3_grratio_max),
        c4_profoods: linear_score(
            r.ratio_pro,
            0.0,
            t.protein_ratio_max,
            0.0,
            t.c4_profoods_max,
        ),
        c5_plantpro: linear_score(
            r.ratio_plant,
            0.0,
            t.plant_protein_ratio_max,
            0.0,
            t.c5_plantpro_max,
        ),
        c6_beverages: linear_score(
            r.ratio_bev,
            0.0,
            t.beverages_ratio_max,
            0.0,
            t.c6_beverages_max,
        ),
        c7_fattyacid: linear_score(
            r.ratio_unsfat,
            0.0,
            t.fa_ratio_max,
            0.0,
            t.c7_fattyacid_max,
        ),
        c8_sfat: linear_score(r.sfa_perc, t.sfa_percent_max, 20.0, t.c8_sfat_max, 0.0),
        c9_freesugars: linear_score(
            r.sug_perc,
            t.free_sugars_percent_max,
            20.0,
            t.c9_freesugars_max,
            0.0,
        ),
        c10_sodium: linear_score(r.sodden, t.sodium_density_min, 2.0, t.c10_sodium_max, 0.0),
    }
}

pub fn compute_hefi(inputs: &HefiInputs) -> HefiResult {
    // Zero-intake short-circuit matches Python: returns zeroed scores and empty ratios.
    if inputs.total_foods_ra == 0.0 || inputs.energy_kcal == 0.0 {
        return HefiResult {
            ratios: HefiRatios::default(),
            scores: HefiComponentScores::default(),
            total: 0.0,
            zero_intake: true,
        };
    }
    let ratios = compute_ratios(inputs);
    let scores = score_components(&ratios, &DEFAULT);
    let total = scores.total();
    HefiResult {
        ratios,
        scores,
        total,
        zero_intake: false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx(a: f64, b: f64) {
        assert!((a - b).abs() < 1e-9, "{a} != {b}");
    }

    #[test]
    fn zero_intake_short_circuits() {
        let r = compute_hefi(&HefiInputs::default());
        assert!(r.zero_intake);
        assert_eq!(r.total, 0.0);
    }

    #[test]
    fn linear_score_bounds() {
        assert_eq!(linear_score(-1.0, 0.0, 10.0, 0.0, 20.0), 0.0);
        assert_eq!(linear_score(10.0, 0.0, 10.0, 0.0, 20.0), 20.0);
        approx(linear_score(5.0, 0.0, 10.0, 0.0, 20.0), 10.0);
    }

    #[test]
    fn moderation_reverses() {
        // SFA 10% -> full 5 points; 20% -> 0 points; 15% -> 2.5.
        let r = HefiRatios {
            sfa_perc: 15.0,
            ..HefiRatios::default()
        };
        let s = score_components(&r, &DEFAULT);
        approx(s.c8_sfat, 2.5);
    }

    #[test]
    fn perfect_diet_maxes_components() {
        let inputs = HefiInputs {
            total_foods_ra: 10.0,
            vf_ra: 5.0,
            whole_grains_ra: 2.5,
            total_grains_ra: 2.5,
            protein_foods_ra: 2.5,
            plant_protein_foods_ra: 2.5,
            total_beverages_g: 1000.0,
            recommended_beverages_g: 1000.0,
            energy_kcal: 2000.0,
            sfa_g: 10.0,     // 10*9/2000*100 = 4.5%
            mufa_g: 20.0,
            pufa_g: 10.0,    // unsat/sat = 3.0 > 2.6
            free_sugars_g: 20.0, // 20*4/2000*100 = 4%
            sodium_mg: 1.0,  // sodden = 1/2000*1000 = 0.5
        };
        let r = compute_hefi(&inputs);
        approx(r.total, 80.0);
    }
}
