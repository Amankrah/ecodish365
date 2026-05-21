//! HSR baseline + modifying points — pinned to HSRC v9 (HSRAC, 10 Dec 2025).
//!
//! Aggregates the four baseline nutrients (energy, sat fat, sugar, sodium) and
//! the three modifying components (FVNL, protein, fibre) per v9 Appendix 1
//! Tables 1–6. Implements two v9 rules absent from the pre-audit code:
//!
//! 1. **Protein eligibility** (v9 p. 26): "if HSR baseline points are < 13,
//!    can score up to 15 P points. If HSR baseline points are ≥ 13, can score
//!    P points only if the HSR V points are ≥ 5."
//! 2. **No `final_score` floor**: v9 Table 7 Cat 2 maps final_score ≤ −11 →
//!    5.0 stars, so beneficial foods (high FVNL/protein/fibre, low baseline)
//!    *must* be allowed to yield negative final scores. The pre-audit code
//!    clamped final_score at 0, which prevented any food from reaching the
//!    top of the v9 rating scale.

use super::calculate_hsr_points_inner;
use super::threshold_data::ThresholdBundle;

/// Integer breakdown matching `HSRComponentScore` (excluding `star_rating` and scientific fields).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ComponentScores {
    pub baseline_points: i32,
    pub energy_points: i32,
    pub saturated_fat_points: i32,
    pub sugar_points: i32,
    pub sodium_points: i32,
    pub modifying_points: i32,
    pub protein_points: i32,
    pub fiber_points: i32,
    pub fvnl_points: i32,
    pub final_score: i32,
}

pub fn compute_component_scores(
    bundle: &ThresholdBundle,
    energy_kj: f64,
    fatty_acids_saturated_total: f64,
    sugars_total: f64,
    sodium: f64,
    protein: f64,
    fibre_total_dietary: f64,
    fvnl_percent: f64,
) -> ComponentScores {
    let energy_points = calculate_hsr_points_inner(energy_kj, bundle.energy) as i32;
    let saturated_fat_points =
        calculate_hsr_points_inner(fatty_acids_saturated_total, bundle.saturated_fat) as i32;
    let sugar_points = calculate_hsr_points_inner(sugars_total, bundle.sugar) as i32;
    let sodium_points = calculate_hsr_points_inner(sodium, bundle.sodium) as i32;

    let baseline_points = energy_points + saturated_fat_points + sugar_points + sodium_points;

    // Raw modifying-point lookups (before v9 protein-eligibility rule).
    let raw_protein_points = calculate_hsr_points_inner(protein, bundle.protein) as i32;
    let fiber_points = calculate_hsr_points_inner(fibre_total_dietary, bundle.fiber) as i32;
    let fvnl_points = calculate_hsr_points_inner(fvnl_percent, bundle.fvnl) as i32;

    // v9 page 26 protein-eligibility rule. Surface the *effective* P-points
    // (post-rule) to callers so the API response reflects what was actually
    // applied to the final score.
    let protein_points = if baseline_points >= 13 && fvnl_points < 5 {
        0
    } else {
        raw_protein_points
    };

    let modifying_points = protein_points + fiber_points + fvnl_points;

    // v9 Table 7 admits negative final_score (Cat 2 maps ≤ −11 → 5.0 stars).
    // Pre-audit the `.max(0)` clamp here capped every food at 4.0 stars max.
    let final_score = baseline_points - modifying_points;

    ComponentScores {
        baseline_points,
        energy_points,
        saturated_fat_points,
        sugar_points,
        sodium_points,
        modifying_points,
        protein_points,
        fiber_points,
        fvnl_points,
        final_score,
    }
}

#[cfg(test)]
mod tests {
    use super::super::threshold_data::{CATEGORY_1, CATEGORY_2};
    use super::*;

    /// Pre-audit this test asserted `final_score = (baseline - modifying).max(0)`.
    /// After HSR-CODE-1 the clamp is removed; final_score can be negative.
    #[test]
    fn sample_food_category2_unclamped() {
        let s = compute_component_scores(&CATEGORY_2, 1000.0, 5.0, 10.0, 400.0, 8.0, 3.0, 50.0);
        assert!(s.baseline_points > 0);
        assert!(s.modifying_points > 0);
        assert_eq!(s.final_score, s.baseline_points - s.modifying_points);
    }

    /// v9 Table 3 / Table 4 / Table 5 / Table 6 explicitly mark sat fat, sodium,
    /// protein, and fibre as "not applicable" for Cat 1 (non-dairy beverages).
    /// Our threshold_data.rs encodes these as INF11 sentinels →
    /// `calculate_hsr_points_inner` returns 0.
    #[test]
    fn beverage_na_components_return_zero() {
        let s = compute_component_scores(&CATEGORY_1, 50.0, 99.0, 5.0, 100.0, 1.0, 0.0, 50.0);
        assert_eq!(s.saturated_fat_points, 0);
        assert_eq!(s.sodium_points, 0);
        assert_eq!(s.protein_points, 0);
        assert_eq!(s.fiber_points, 0);
    }

    /// v9 Cat 2 worked example: plain rolled oats (energy 1550 kJ, sat fat 1.2,
    /// sugar 0.8, sodium 2 mg, protein 13.2, fibre 10.1, FVNL 0).
    /// Expected:
    ///   energy_pts = >1340, >1675 NO → 4
    ///   sat_fat_pts = >1.0, >2.0 NO → 1
    ///   sugar_pts = >5.0 NO → 0
    ///   sodium_pts = >90 NO → 0
    ///   baseline = 5
    ///   protein_pts (raw) = >11.6, >13.9 NO → 7 (baseline<13 → eligible → 7)
    ///   fibre_pts = >9.7, >11.2 NO → 10
    ///   fvnl_pts = 0
    ///   modifying = 17
    ///   final_score = 5 − 17 = −12 → ≤ −11 (Cat 2 Table 7) → 5.0 stars.
    #[test]
    fn rolled_oats_reaches_v9_top_band() {
        let s =
            compute_component_scores(&CATEGORY_2, 1550.0, 1.2, 0.8, 2.0, 13.2, 10.1, 0.0);
        assert_eq!(s.energy_points, 4);
        assert_eq!(s.saturated_fat_points, 1);
        assert_eq!(s.sugar_points, 0);
        assert_eq!(s.sodium_points, 0);
        assert_eq!(s.baseline_points, 5);
        assert_eq!(s.protein_points, 7);
        assert_eq!(s.fiber_points, 10);
        assert_eq!(s.fvnl_points, 0);
        assert_eq!(s.modifying_points, 17);
        assert_eq!(s.final_score, -12);
    }

    /// v9 page 26 protein-eligibility rule: a high-baseline (≥13) food with
    /// low FVNL points (<5) must receive 0 protein points regardless of
    /// actual protein content. Tests a meat-pie-style input: high sat fat,
    /// high sodium, decent protein, no FVNL.
    #[test]
    fn high_baseline_disqualifies_protein() {
        // Inputs chosen so baseline ≥ 13: high energy, moderate sat fat,
        // moderate sugar, high sodium.
        let s =
            compute_component_scores(&CATEGORY_2, 2200.0, 6.0, 4.0, 700.0, 12.0, 1.0, 0.0);
        assert!(s.baseline_points >= 13);
        assert_eq!(s.fvnl_points, 0); // FVNL < 5
        // Protein eligibility rule: P points zeroed out.
        assert_eq!(s.protein_points, 0);
        // Sanity: raw-protein lookup would have been nonzero, so the rule did
        // actually fire.
        let raw_p =
            calculate_hsr_points_inner(12.0, CATEGORY_2.protein) as i32;
        assert!(raw_p > 0);
    }

    /// Inverse case: baseline ≥ 13 *with* FVNL ≥ 5 → protein eligibility
    /// preserved. (A high-protein, vegetable-rich frozen meal.)
    #[test]
    fn high_baseline_with_high_fvnl_keeps_protein() {
        let s =
            compute_component_scores(&CATEGORY_2, 2200.0, 6.0, 4.0, 700.0, 12.0, 1.0, 85.0);
        assert!(s.baseline_points >= 13);
        assert!(s.fvnl_points >= 5);
        assert!(s.protein_points > 0);
    }
}

