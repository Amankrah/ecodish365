//! HEFI-2019 helpers exposed as `rust_core.hefi`.
//!
//! Phase 1: scoring only. CNF-driven classification and nutrient aggregation
//! still live in Python (`hefi_calculator/hefi/cnf_integrator.py`) and will
//! move here in later phases.

mod aggregator;
mod classifier;
mod scoring;
mod thresholds;

use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use aggregator::{aggregate as aggregate_inner, FoodRow};
use scoring::{compute_hefi as compute_hefi_inner, HefiInputs};

fn extract_f64(d: &Bound<'_, PyDict>, key: &str) -> PyResult<f64> {
    match d.get_item(key)? {
        Some(v) => v
            .extract::<f64>()
            .or_else(|_| v.extract::<i64>().map(|i| i as f64)),
        None => Ok(0.0),
    }
}

fn dict_to_inputs(d: &Bound<'_, PyDict>) -> PyResult<HefiInputs> {
    Ok(HefiInputs {
        total_foods_ra: extract_f64(d, "total_foods_ra")?,
        vf_ra: extract_f64(d, "vf_ra")?,
        whole_grains_ra: extract_f64(d, "whole_grains_ra")?,
        total_grains_ra: extract_f64(d, "total_grains_ra")?,
        protein_foods_ra: extract_f64(d, "protein_foods_ra")?,
        plant_protein_foods_ra: extract_f64(d, "plant_protein_foods_ra")?,
        total_beverages_g: extract_f64(d, "total_beverages_g")?,
        recommended_beverages_g: extract_f64(d, "recommended_beverages_g")?,
        energy_kcal: extract_f64(d, "energy_kcal")?,
        sfa_g: extract_f64(d, "sfa_g")?,
        mufa_g: extract_f64(d, "mufa_g")?,
        pufa_g: extract_f64(d, "pufa_g")?,
        free_sugars_g: extract_f64(d, "free_sugars_g")?,
        sodium_mg: extract_f64(d, "sodium_mg")?,
    })
}

/// Compute HEFI-2019 ratios, component scores, and total from an inputs dict.
///
/// Mirrors `hefi_calculator.hefi.algorithm.compute_hefi`. Input keys match
/// `HEFIInputs` dataclass fields. Returns:
///
/// ```text
/// {
///   "ratios": {RATIO_VF, RATIO_WGTOT, RATIO_WGGR, RATIO_PRO, RATIO_PLANT,
///              RATIO_BEV, RATIO_UNSFAT, SFA_PERC, SUG_PERC, SODDEN},
///   "component_scores": {c1_vf, c2_wholegr, c3_grratio, c4_profoods,
///                        c5_plantpro, c6_beverages, c7_fattyacid,
///                        c8_sfat, c9_freesugars, c10_sodium},
///   "total_score": float,
///   "zero_intake": bool,
/// }
/// ```
///
/// When `zero_intake` is true (total_foods_ra or energy_kcal is zero) the
/// `ratios` dict is empty — matching the Python short-circuit.
#[pyfunction]
fn compute_hefi<'py>(py: Python<'py>, inputs: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let parsed = dict_to_inputs(inputs)?;
    let result = compute_hefi_inner(&parsed);

    let out = PyDict::new_bound(py);

    let ratios = PyDict::new_bound(py);
    if !result.zero_intake {
        ratios.set_item("RATIO_VF", result.ratios.ratio_vf)?;
        ratios.set_item("RATIO_WGTOT", result.ratios.ratio_wgtot)?;
        ratios.set_item("RATIO_WGGR", result.ratios.ratio_wggr)?;
        ratios.set_item("RATIO_PRO", result.ratios.ratio_pro)?;
        ratios.set_item("RATIO_PLANT", result.ratios.ratio_plant)?;
        ratios.set_item("RATIO_BEV", result.ratios.ratio_bev)?;
        ratios.set_item("RATIO_UNSFAT", result.ratios.ratio_unsfat)?;
        ratios.set_item("SFA_PERC", result.ratios.sfa_perc)?;
        ratios.set_item("SUG_PERC", result.ratios.sug_perc)?;
        ratios.set_item("SODDEN", result.ratios.sodden)?;
    }
    out.set_item("ratios", ratios)?;

    let scores = PyDict::new_bound(py);
    scores.set_item("c1_vf", result.scores.c1_vf)?;
    scores.set_item("c2_wholegr", result.scores.c2_wholegr)?;
    scores.set_item("c3_grratio", result.scores.c3_grratio)?;
    scores.set_item("c4_profoods", result.scores.c4_profoods)?;
    scores.set_item("c5_plantpro", result.scores.c5_plantpro)?;
    scores.set_item("c6_beverages", result.scores.c6_beverages)?;
    scores.set_item("c7_fattyacid", result.scores.c7_fattyacid)?;
    scores.set_item("c8_sfat", result.scores.c8_sfat)?;
    scores.set_item("c9_freesugars", result.scores.c9_freesugars)?;
    scores.set_item("c10_sodium", result.scores.c10_sodium)?;
    out.set_item("component_scores", scores)?;

    out.set_item("total_score", result.total)?;
    out.set_item("zero_intake", result.zero_intake)?;
    Ok(out)
}

/// Aggregate a meal batch into the HEFI inputs dict.
///
/// Mechanical port of `HEFICNFIntegrator.aggregate_inputs`. Python pre-indexes
/// the CNF tables once (pandas `groupby`) and passes in:
///
/// - `foods` — list of `(food_id, amount_g, food_group_id, food_description)`
///   tuples, already resolved against `food_name_df`
/// - `nutrients_by_food` — `{food_id: {nutrient_name: value_per_100g}}`
/// - `ra_amounts` — flat `{ra_category: grams}` from
///   `HEFICNFIntegrator.ra_lookup`
///
/// Returns a dict with the 14 HEFIInputs fields, ready to hand straight to
/// `compute_hefi`.
#[pyfunction]
fn aggregate_inputs<'py>(
    py: Python<'py>,
    foods: &Bound<'py, PyList>,
    nutrients_by_food: &Bound<'py, PyDict>,
    ra_amounts: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    // Owned storage for descriptions so FoodRow can borrow &str.
    let mut desc_store: Vec<String> = Vec::with_capacity(foods.len());
    let mut row_store: Vec<(i64, f64, i32)> = Vec::with_capacity(foods.len());
    for item in foods.iter() {
        let tup = item;
        let food_id: i64 = tup.get_item(0)?.extract()?;
        let amount_g: f64 = tup.get_item(1)?.extract()?;
        let group_id: i32 = tup.get_item(2)?.extract()?;
        let desc: String = tup.get_item(3)?.extract()?;
        desc_store.push(desc);
        row_store.push((food_id, amount_g, group_id));
    }
    let rows: Vec<FoodRow> = row_store
        .iter()
        .zip(desc_store.iter())
        .map(|(&(food_id, amount_g, food_group_id), desc)| FoodRow {
            food_id,
            amount_g,
            food_group_id,
            food_description: desc.as_str(),
        })
        .collect();

    // nutrients_by_food: PyDict[int, PyDict[str, float]]
    let mut nutrients: HashMap<i64, HashMap<String, f64>> = HashMap::with_capacity(nutrients_by_food.len());
    for (k, v) in nutrients_by_food.iter() {
        let fid: i64 = k.extract()?;
        let inner = v.downcast::<PyDict>()?;
        let mut m: HashMap<String, f64> = HashMap::with_capacity(inner.len());
        for (nk, nv) in inner.iter() {
            let name: String = nk.extract()?;
            let val: f64 = nv
                .extract::<f64>()
                .or_else(|_| nv.extract::<i64>().map(|i| i as f64))?;
            m.insert(name, val);
        }
        nutrients.insert(fid, m);
    }

    // ra_amounts: PyDict[str, float]
    let mut ra_map: HashMap<String, f64> = HashMap::with_capacity(ra_amounts.len());
    for (k, v) in ra_amounts.iter() {
        let key: String = k.extract()?;
        let val: f64 = v
            .extract::<f64>()
            .or_else(|_| v.extract::<i64>().map(|i| i as f64))?;
        ra_map.insert(key, val);
    }

    let agg = aggregate_inner(&rows, &nutrients, &ra_map);

    let out = PyDict::new_bound(py);
    out.set_item("total_foods_ra", agg.total_foods_ra)?;
    out.set_item("vf_ra", agg.vf_ra)?;
    out.set_item("whole_grains_ra", agg.whole_grains_ra)?;
    out.set_item("total_grains_ra", agg.total_grains_ra)?;
    out.set_item("protein_foods_ra", agg.protein_foods_ra)?;
    out.set_item("plant_protein_foods_ra", agg.plant_protein_foods_ra)?;
    out.set_item("total_beverages_g", agg.total_beverages_g)?;
    out.set_item("recommended_beverages_g", agg.recommended_beverages_g)?;
    out.set_item("energy_kcal", agg.energy_kcal)?;
    out.set_item("sfa_g", agg.sfa_g)?;
    out.set_item("mufa_g", agg.mufa_g)?;
    out.set_item("pufa_g", agg.pufa_g)?;
    out.set_item("free_sugars_g", agg.free_sugars_g)?;
    out.set_item("sodium_mg", agg.sodium_mg)?;
    Ok(out)
}

/// Classify a food description + CNF food group ID into an RA category.
///
/// Mechanical port of
/// `HEFICNFIntegrator._classify_food_to_ra_category`. Return values are
/// the exact category strings used by `HEFICNFIntegrator._get_ra_amount`
/// and the RA lookup table loaded from
/// `nutrition_reference_amounts.json`.
#[pyfunction]
fn classify_food_to_ra_category(food_description: &str, food_group_id: i32) -> &'static str {
    classifier::classify(food_description, food_group_id)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_hefi, m)?)?;
    m.add_function(wrap_pyfunction!(classify_food_to_ra_category, m)?)?;
    m.add_function(wrap_pyfunction!(aggregate_inputs, m)?)?;
    Ok(())
}
