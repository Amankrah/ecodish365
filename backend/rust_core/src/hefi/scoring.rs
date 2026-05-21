//! HEFI-2019 ratio computation and component scoring.
//!
//! Implements Brassard et al. (2022a) APNM 47:595-610 Table 2 (p. 600) and
//! the linear-interpolation scoring of Results p. 599. Component-by-component
//! threshold values live in `thresholds.rs::DEFAULT`. After the 2026-05-21
//! HEFI-CODE-1 audit, sodium density (SODDEN) is in mg/kcal — the Brassard
//! published unit — and the max-score threshold is 0.9 mg/kcal (pre-audit:
//! mg/1000-kcal with a 1.0 max threshold, which produced 0 sodium points for
//! every realistic meal).

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

    // Brassard 2022a Table 2 p. 600 unit conventions:
    //   sfa_perc   = (SFA_g × 9 kcal/g) / energy_kcal × 100   (% energy from SFA)
    //   sug_perc   = (free_sugars_g × 4 kcal/g) / energy_kcal × 100  (% energy)
    //   sodden     = sodium_mg / energy_kcal                  (mg/kcal)
    //
    // Pre-audit the SODDEN ratio multiplied by 1000 (yielding mg/1000-kcal),
    // which was inherited from a transcription error in
    // `hefi_technical_report.md` and incompatible with the thresholds in
    // `thresholds.rs`. The ×1000 has been removed (HEFI-CODE-1A, 2026-05-21).
    let (sfa_perc, sug_perc, sodden) = if kcal > 0.0 {
        (
            (inputs.sfa_g * 9.0) / kcal * 100.0,
            (inputs.free_sugars_g * 4.0) / kcal * 100.0,
            inputs.sodium_mg / kcal,
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

    /// Perfect-diet inputs with a REALISTIC sodium load. Pre-HEFI-CODE-1 this
    /// test used `sodium_mg = 1.0` (one milligram per 2000-kcal day — an
    /// impossible value) to dodge the SODDEN ×1000 unit bug. With the audit
    /// fix in place, a realistic 1500 mg / 2000 kcal = 0.75 mg/kcal (below
    /// the Brassard 2022a 0.9 mg/kcal max-score threshold) yields the full
    /// 10/10 sodium component and total = 80/80.
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
            sfa_g: 10.0,         // 10×9/2000×100 = 4.5 %E  (≤ 10 %E max)
            mufa_g: 20.0,
            pufa_g: 10.0,        // (MUFA+PUFA)/SFA = 30/10 = 3.0  (≥ 2.6 max)
            free_sugars_g: 20.0, // 20×4/2000×100 = 4 %E  (≤ 10 %E max)
            sodium_mg: 1500.0,   // 1500/2000 = 0.75 mg/kcal  (< 0.9 max)
        };
        let r = compute_hefi(&inputs);
        approx(r.total, 80.0);
        // Component-by-component: every one must be at max.
        approx(r.scores.c1_vf, 20.0);
        approx(r.scores.c2_wholegr, 5.0);
        approx(r.scores.c3_grratio, 5.0);
        approx(r.scores.c4_profoods, 5.0);
        approx(r.scores.c5_plantpro, 5.0);
        approx(r.scores.c6_beverages, 10.0);
        approx(r.scores.c7_fattyacid, 5.0);
        approx(r.scores.c8_sfat, 5.0);
        approx(r.scores.c9_freesugars, 10.0);
        approx(r.scores.c10_sodium, 10.0);
    }

    /// Brassard 2022a Table 2 p. 600: C10 sodium component interpolates linearly
    /// between 10 pts at < 0.9 mg/kcal and 0 pts at ≥ 2.0 mg/kcal. Verify the
    /// curve at seven canonical points. Pre-HEFI-CODE-1 (×1000 SODDEN bug),
    /// every one of these points returned 0.0 because the ratio was 1000×
    /// too large.
    #[test]
    fn brassard_sodium_scoring_curve() {
        let cases: [(f64, f64); 7] = [
            (0.5, 10.0),
            (0.8, 10.0),
            (0.9, 10.0),
            (0.95, 10.0 * (2.0 - 0.95) / (2.0 - 0.9)), // ≈ 9.545
            (1.0, 10.0 * (2.0 - 1.0) / (2.0 - 0.9)),   // ≈ 9.091
            (1.5, 10.0 * (2.0 - 1.5) / (2.0 - 0.9)),   // ≈ 4.545
            (2.0, 0.0),
        ];
        for (mg_per_kcal, expected) in cases {
            let inputs = HefiInputs {
                total_foods_ra: 10.0,
                energy_kcal: 2000.0,
                sodium_mg: mg_per_kcal * 2000.0,
                ..HefiInputs::default()
            };
            let r = compute_hefi(&inputs);
            let actual = r.scores.c10_sodium;
            assert!(
                (actual - expected).abs() < 1e-3,
                "sodium {mg_per_kcal} mg/kcal: expected {expected:.3}, got {actual:.3}"
            );
        }
    }

    /// Brassard 2022b Table A2 p. 591 reports a national HEFI mean of 43.1/80
    /// with a 1st-99th percentile range of [22.1, 62.9] across Canadians
    /// aged ≥ 2 y. A meal panel sized to the national means must score inside
    /// this range. Approximate inputs derived from Table A2 component means.
    #[test]
    fn national_mean_in_brassard_published_range() {
        let inputs = HefiInputs {
            total_foods_ra: 10.0,
            vf_ra: 2.3,
            whole_grains_ra: 0.6,
            total_grains_ra: 2.0,
            protein_foods_ra: 2.2,
            plant_protein_foods_ra: 0.7,
            total_beverages_g: 1000.0,
            recommended_beverages_g: 750.0,
            energy_kcal: 2000.0,
            sfa_g: 24.5,
            mufa_g: 27.0,
            pufa_g: 10.0,
            free_sugars_g: 50.0,
            sodium_mg: 2400.0, // 1.2 mg/kcal — between max (0.9) and min (2.0) thresholds
        };
        let r = compute_hefi(&inputs);
        assert!(
            (22.1..=62.9).contains(&r.total),
            "expected national 1-99 pctl range [22.1, 62.9], got {}",
            r.total
        );
    }
}
