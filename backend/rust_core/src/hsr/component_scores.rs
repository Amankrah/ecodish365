//! HSR baseline + modifying points — mirrors `HSRCalculator._calculate_components`.

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

    let baseline_points =
        energy_points + saturated_fat_points + sugar_points + sodium_points;

    let protein_points = calculate_hsr_points_inner(protein, bundle.protein) as i32;
    let fiber_points =
        calculate_hsr_points_inner(fibre_total_dietary, bundle.fiber) as i32;
    let fvnl_points = calculate_hsr_points_inner(fvnl_percent, bundle.fvnl) as i32;

    let modifying_points = protein_points + fiber_points + fvnl_points;

    let final_score = (baseline_points - modifying_points).max(0);

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
    use super::*;
    use super::super::threshold_data::CATEGORY_2;

    #[test]
    fn sample_food_category2() {
        let s = compute_component_scores(
            &CATEGORY_2,
            1000.0,
            5.0,
            10.0,
            400.0,
            8.0,
            3.0,
            50.0,
        );
        assert!(s.baseline_points > 0);
        assert!(s.modifying_points > 0);
        assert_eq!(
            s.final_score,
            (s.baseline_points - s.modifying_points).max(0)
        );
    }

    #[test]
    fn beverage_sat_fat_na_zero_risk_points() {
        use super::super::threshold_data::CATEGORY_1;
        let s = compute_component_scores(
            &CATEGORY_1,
            50.0,
            99.0,
            5.0,
            100.0,
            1.0,
            0.0,
            50.0,
        );
        assert_eq!(s.saturated_fat_points, 0);
    }
}
