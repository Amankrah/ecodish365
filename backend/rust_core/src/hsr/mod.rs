//! HSR helpers exposed as `rust_core.hsr`.

mod component_scores;
mod food_group_mapper;
mod fvnl;
mod meal_categorizer;
mod threshold_data;

use component_scores::compute_component_scores;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple};
use pyo3::IntoPy;
use std::collections::HashMap;
use threshold_data::bundle_for_category_value;

/// Calculate HSR points for a nutrient value against an ordered threshold array.
///
/// Mirrors `ThresholdProvider.calculate_hsr_points` in
/// `backend/hsr_calculator/hsr/providers/threshold_provider.py`.
///
/// Semantics: points = number of leading thresholds the value *strictly
/// exceeds*, stopping at the first miss. This implements v9's standard
/// "≤X earns N points, >X earns N+1 points" convention (HSRC v9 Tables 1–6,
/// HSRAC 10 December 2025).
///
/// Two sentinel handlings:
/// - **Positive-infinity first threshold** (e.g. saturated fat for Cat 1):
///   returns 0 unconditionally — the nutrient is "not applicable" for this
///   category.
/// - **Negative-infinity first threshold** (used for Cat 1 baseline energy
///   per v9 Table 3, which has no zero-point bucket): always counts as
///   exceeded, ensuring minimum 1 point even at energy = 0.
pub(crate) fn calculate_hsr_points_inner(value: f64, thresholds: &[f64]) -> u32 {
    if thresholds.is_empty() {
        return 0;
    }
    // Sentinel: "not applicable" — first threshold = +∞.
    if thresholds[0].is_infinite() && thresholds[0].is_sign_positive() {
        return 0;
    }
    let mut points: u32 = 0;
    for &t in thresholds.iter() {
        if value > t {
            points += 1;
        } else {
            break;
        }
    }
    points
}

#[pyfunction]
fn calculate_hsr_points(value: f64, thresholds: Vec<f64>) -> u32 {
    calculate_hsr_points_inner(value, &thresholds)
}

/// Convert a final HSR score to a star rating using category-specific
/// star thresholds.
///
/// Mirrors `ThresholdProvider.convert_score_to_stars`. Lower score → more stars.
/// Walks `star_thresholds` in order; the first threshold the score does not
/// exceed yields `5.0 - i * 0.5`. Result clamped to [0.5, 5.0].
pub(crate) fn convert_score_to_stars_inner(final_score: i64, star_thresholds: &[f64]) -> f64 {
    let score = final_score as f64;
    let mut stars = 0.5_f64;
    for (i, &t) in star_thresholds.iter().enumerate() {
        if score <= t {
            stars = 5.0 - (i as f64) * 0.5;
            break;
        }
    }
    stars.clamp(0.5, 5.0)
}

#[pyfunction]
fn convert_score_to_stars(final_score: i64, star_thresholds: Vec<f64>) -> f64 {
    convert_score_to_stars_inner(final_score, &star_thresholds)
}

fn f64_slice_to_pylist<'py>(py: Python<'py>, s: &[f64]) -> PyResult<Bound<'py, PyList>> {
    Ok(PyList::new_bound(py, s.iter().copied().collect::<Vec<_>>()))
}

/// Official HSR threshold rows for a category.
///
/// `category` must be the string value of `Category` (`'1'`, `'1D'`, `'2'`, `'2D'`, `'3'`, `'3D'`).
/// Returns a dict with keys: `energy`, `sugar`, `saturated_fat`, `sodium`, `fvnl`, `protein`,
/// `fiber`, `star_thresholds` — same layout as `ThresholdProvider.get_thresholds` sources.
#[pyfunction]
fn get_thresholds<'py>(py: Python<'py>, category: &str) -> PyResult<Bound<'py, PyDict>> {
    let b = bundle_for_category_value(category);
    let d = PyDict::new_bound(py);
    d.set_item("energy", f64_slice_to_pylist(py, b.energy)?)?;
    d.set_item("sugar", f64_slice_to_pylist(py, b.sugar)?)?;
    d.set_item("saturated_fat", f64_slice_to_pylist(py, b.saturated_fat)?)?;
    d.set_item("sodium", f64_slice_to_pylist(py, b.sodium)?)?;
    d.set_item("fvnl", f64_slice_to_pylist(py, b.fvnl)?)?;
    d.set_item("protein", f64_slice_to_pylist(py, b.protein)?)?;
    d.set_item("fiber", f64_slice_to_pylist(py, b.fiber)?)?;
    d.set_item(
        "star_thresholds",
        f64_slice_to_pylist(py, b.star_thresholds)?,
    )?;
    Ok(d)
}

/// Core HSR points from per-100g nutrients and category (`Category.value`).
///
/// Mirrors `HSRCalculator._calculate_components` nutrient math only. Does not compute
/// `scientific_confidence` or `star_rating` (Python sets `star_rating` after this).
#[pyfunction]
#[pyo3(
    signature = (
        category,
        energy_kj,
        fatty_acids_saturated_total,
        sugars_total,
        sodium,
        protein,
        fibre_total_dietary,
        fvnl_percent,
    )
)]
fn calculate_component_scores<'py>(
    py: Python<'py>,
    category: &str,
    energy_kj: f64,
    fatty_acids_saturated_total: f64,
    sugars_total: f64,
    sodium: f64,
    protein: f64,
    fibre_total_dietary: f64,
    fvnl_percent: f64,
) -> PyResult<Bound<'py, PyDict>> {
    let bundle = bundle_for_category_value(category);
    let s = compute_component_scores(
        bundle,
        energy_kj,
        fatty_acids_saturated_total,
        sugars_total,
        sodium,
        protein,
        fibre_total_dietary,
        fvnl_percent,
    );
    let d = PyDict::new_bound(py);
    d.set_item("baseline_points", s.baseline_points)?;
    d.set_item("energy_points", s.energy_points)?;
    d.set_item("saturated_fat_points", s.saturated_fat_points)?;
    d.set_item("sugar_points", s.sugar_points)?;
    d.set_item("sodium_points", s.sodium_points)?;
    d.set_item("modifying_points", s.modifying_points)?;
    d.set_item("protein_points", s.protein_points)?;
    d.set_item("fiber_points", s.fiber_points)?;
    d.set_item("fvnl_points", s.fvnl_points)?;
    d.set_item("final_score", s.final_score)?;
    Ok(d)
}

/// FVNL % from food name + CNF group code/id (Python loads CNF row first).
#[pyfunction]
fn nuanced_fvnl_percent(food_name: &str, food_group_code: i32, food_group_id: i32) -> f64 {
    fvnl::nuanced_fvnl_percent(food_name, food_group_code, food_group_id)
}

/// HSR `Category.value` from CNF food group id + name (`FoodGroupMapper.get_category`).
#[pyfunction]
fn food_group_category(food_group_id: i32, food_name: &str) -> &'static str {
    food_group_mapper::food_group_category_value(food_group_id, food_name)
}

/// Scientific meal category for multiple foods (CNF data already on each ``Food``).
///
/// Returns a dict with keys matching ``ScientificCategorizationResult`` fields:
/// ``recommended_category``, ``confidence``, ``reasoning``, ``nutritional_rationale``,
/// ``alternative_categories`` (list of ``[category_value, score, reason]``),
/// ``scientific_factors`` (flat dict of numbers and strings).
#[pyfunction]
fn determine_scientific_category_meal<'py>(
    py: Python<'py>,
    foods: &Bound<'py, PyList>,
) -> PyResult<Bound<'py, PyDict>> {
    let mut inputs = Vec::new();
    for item in foods.iter() {
        let food_name: String = item.getattr("food_name")?.extract()?;
        let serving_size: f64 = item.getattr("serving_size")?.extract()?;
        let nutrients_obj = item.getattr("nutrients")?;
        let mut nutrients = HashMap::new();
        if let Ok(dict) = nutrients_obj.downcast::<PyDict>() {
            for (k, v) in dict.iter() {
                if let Ok(key) = k.extract::<String>() {
                    let val = v
                        .extract::<f64>()
                        .or_else(|_| v.extract::<i64>().map(|i| i as f64))
                        .unwrap_or(0.0);
                    nutrients.insert(key, val);
                }
            }
        }
        let cat_obj = item.getattr("category")?;
        let category_value: Option<String> = if cat_obj.is_none() {
            None
        } else {
            cat_obj.getattr("value")?.extract().ok()
        };
        inputs.push(meal_categorizer::FoodInput {
            food_name,
            serving_size,
            nutrients,
            category_value,
        });
    }
    let out = meal_categorizer::determine_scientific_category(&inputs);
    let d = PyDict::new_bound(py);
    d.set_item("recommended_category", out.recommended_category.as_str())?;
    d.set_item("confidence", out.confidence)?;
    d.set_item("reasoning", out.reasoning)?;
    d.set_item("nutritional_rationale", out.nutritional_rationale.as_str())?;
    let alts = PyList::empty_bound(py);
    for (c, s, r) in &out.alternative_categories {
        let row = PyTuple::new_bound(
            py,
            [
                c.as_str().into_py(py),
                (*s).into_py(py),
                r.as_str().into_py(py),
            ],
        );
        alts.append(row)?;
    }
    d.set_item("alternative_categories", alts)?;
    let fact = PyDict::new_bound(py);
    for (k, v) in &out.scientific_factors {
        match v {
            meal_categorizer::FactorValue::Num(x) => fact.set_item(k.as_str(), *x)?,
            meal_categorizer::FactorValue::Str(s) => fact.set_item(k.as_str(), s.as_str())?,
        }
    }
    d.set_item("scientific_factors", fact)?;
    Ok(d)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn calculate_hsr_points_strict_greater_semantics() {
        // v9 convention: "≤X earns N points, >X earns N+1 points".
        // For thresholds [0, 2, 4, 6, 8]:
        //   value 5 → 5>0 yes, 5>2 yes, 5>4 yes, 5>6 no → 3 pts
        //   value 4 → 4>0 yes, 4>2 yes, 4>4 NO         → 2 pts (was 3 under >=)
        //   value 0 → 0>0 NO                            → 0 pts (was 1 under >=)
        //   value 10 → 10>0,2,4,6,8 all yes              → 5 pts
        //   value 1 → 1>0 yes, 1>2 no                   → 1 pt
        assert_eq!(calculate_hsr_points_inner(5.0, &[0.0, 2.0, 4.0, 6.0, 8.0]), 3);
        assert_eq!(calculate_hsr_points_inner(4.0, &[0.0, 2.0, 4.0]), 2);
        assert_eq!(calculate_hsr_points_inner(0.0, &[0.0, 2.0, 4.0]), 0);
        assert_eq!(calculate_hsr_points_inner(10.0, &[0.0, 2.0, 4.0, 6.0, 8.0]), 5);
        assert_eq!(calculate_hsr_points_inner(1.0, &[0.0, 2.0, 4.0]), 1);
    }

    #[test]
    fn calculate_hsr_points_v9_sodium_boundary() {
        // v9 Cat 2 sodium: ≤90 → 0 pts, >90 → 1 pt, >180 → 2 pts.
        let sod = &[90.0, 180.0, 270.0, 360.0];
        assert_eq!(calculate_hsr_points_inner(0.0, sod), 0);
        assert_eq!(calculate_hsr_points_inner(89.0, sod), 0);
        assert_eq!(calculate_hsr_points_inner(90.0, sod), 0);  // ≤90 → 0 pts
        assert_eq!(calculate_hsr_points_inner(91.0, sod), 1);  // >90 → 1 pt
        assert_eq!(calculate_hsr_points_inner(180.0, sod), 1); // ≤180 → 1 pt
        assert_eq!(calculate_hsr_points_inner(181.0, sod), 2); // >180 → 2 pts
        assert_eq!(calculate_hsr_points_inner(500.0, sod), 4); // > all → 4 pts
    }

    #[test]
    fn calculate_hsr_points_neg_infinity_first_always_counts() {
        // Cat 1 energy uses NEG_INFINITY for the "no zero-point bucket" rule:
        // any energy ≥ 0 still earns at least 1 point.
        let energy_cat1 = &[f64::NEG_INFINITY, 31.0, 61.0, 91.0];
        assert_eq!(calculate_hsr_points_inner(0.0, energy_cat1), 1);
        assert_eq!(calculate_hsr_points_inner(31.0, energy_cat1), 1);
        assert_eq!(calculate_hsr_points_inner(32.0, energy_cat1), 2);
        assert_eq!(calculate_hsr_points_inner(100.0, energy_cat1), 4);
    }

    #[test]
    fn calculate_hsr_points_empty_or_positive_infinite_first_returns_zero() {
        assert_eq!(calculate_hsr_points_inner(100.0, &[]), 0);
        // Positive infinity = "not applicable" sentinel (sat fat for Cat 1, etc.).
        assert_eq!(calculate_hsr_points_inner(100.0, &[f64::INFINITY, 0.0]), 0);
    }

    #[test]
    fn convert_score_to_stars_matches_v9_cat1d() {
        // v9 Table 7 Cat 1D: score ≤-2 → 5.0, -1 → 4.5, 0 → 4.0, 1 → 3.5,
        //                    2 → 3.0, 3 → 2.5, 4 → 2.0, 5 → 1.5, 6 → 1.0, ≥7 → 0.5.
        let stars = [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0];
        assert!((convert_score_to_stars_inner(-3, &stars) - 5.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(-2, &stars) - 5.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(-1, &stars) - 4.5).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(0, &stars) - 4.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(6, &stars) - 1.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(7, &stars) - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn convert_score_to_stars_v9_cat2_reaches_5_stars() {
        // v9 Table 7 Cat 2: score ≤ -11 → 5.0 stars (the top band, reachable
        // numerically by foods like raw chia, plain rolled oats, vegetables).
        let stars = [-11.0, -7.0, -2.0, 2.0, 6.0, 11.0, 15.0, 20.0, 24.0];
        assert!((convert_score_to_stars_inner(-15, &stars) - 5.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(-11, &stars) - 5.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(-10, &stars) - 4.5).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(24, &stars) - 1.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(25, &stars) - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn convert_score_to_stars_cat1_neg_inf_padding_unreachable_numerically() {
        // v9 Table 7 Cat 1: 5.0 and 4.5 reserved for name overrides (Water /
        // Unsweetened Flavoured water). Numeric scoring can never reach 5.0/4.5.
        let stars = [f64::NEG_INFINITY, f64::NEG_INFINITY, 0.0, 1.0, 3.0, 5.0, 7.0, 9.0, 11.0];
        // Any score below -∞ is impossible, so 4.0 is the highest numeric star.
        assert!((convert_score_to_stars_inner(-100, &stars) - 4.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(0, &stars) - 4.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(1, &stars) - 3.5).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(11, &stars) - 1.0).abs() < f64::EPSILON);
        assert!((convert_score_to_stars_inner(12, &stars) - 0.5).abs() < f64::EPSILON);
    }

    #[test]
    fn component_scores_matches_manual_category2() {
        use super::compute_component_scores;
        use super::threshold_data::CATEGORY_2;
        let s = compute_component_scores(
            &CATEGORY_2,
            1500.0,
            3.0,
            12.0,
            200.0,
            10.0,
            5.0,
            30.0,
        );
        let e = calculate_hsr_points_inner(1500.0, CATEGORY_2.energy) as i32;
        assert_eq!(s.energy_points, e);
        // Final score after HSR-CODE-1 is no longer clamped at 0 — beneficial
        // foods (high P/F/V) can yield strongly negative scores → 5.0 stars.
        let final_exp = s.baseline_points - s.modifying_points;
        assert_eq!(s.final_score, final_exp);
    }
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_hsr_points, m)?)?;
    m.add_function(wrap_pyfunction!(convert_score_to_stars, m)?)?;
    m.add_function(wrap_pyfunction!(get_thresholds, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_component_scores, m)?)?;
    m.add_function(wrap_pyfunction!(nuanced_fvnl_percent, m)?)?;
    m.add_function(wrap_pyfunction!(food_group_category, m)?)?;
    m.add_function(wrap_pyfunction!(determine_scientific_category_meal, m)?)?;
    Ok(())
}
