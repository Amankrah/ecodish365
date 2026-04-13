//! Health and Nutrition Index (HENI) — DALY core exposed as `rust_core.heni`.

mod engine;
mod factors;

use engine::compute_heni_score;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

fn py_to_f64(v: &Bound<'_, PyAny>) -> PyResult<f64> {
    if let Ok(x) = v.extract::<f64>() {
        return Ok(x);
    }
    if let Ok(i) = v.extract::<i64>() {
        return Ok(i as f64);
    }
    Err(PyValueError::new_err("expected a numeric value"))
}

fn parse_risk_factors(d: &Bound<'_, PyDict>) -> PyResult<HashMap<String, f64>> {
    let mut out = HashMap::new();
    for (k, v) in d.iter() {
        let key: String = k.extract()?;
        out.insert(key, py_to_f64(&v)?);
    }
    Ok(out)
}

fn hashmap_to_pydict<'py>(py: Python<'py>, m: &HashMap<String, f64>) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new_bound(py);
    for (k, v) in m {
        d.set_item(k, v)?;
    }
    Ok(d)
}

/// HENI DALY aggregation from meal-level **aggregated** risk-factor grams (Python builds this map).
#[pyfunction]
#[pyo3(signature = (
    risk_factors,
    total_energy_kcal,
    total_weight_grams,
    serving_size_grams = 100.0,
    age_group = "adult_male",
    apply_age_adjustment = true
))]
fn compute_heni<'py>(
    py: Python<'py>,
    risk_factors: &Bound<'py, PyDict>,
    total_energy_kcal: f64,
    total_weight_grams: f64,
    serving_size_grams: f64,
    age_group: &str,
    apply_age_adjustment: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let rf = parse_risk_factors(risk_factors)?;
    let h = compute_heni_score(
        rf,
        total_energy_kcal,
        total_weight_grams,
        serving_size_grams,
        age_group,
        apply_age_adjustment,
    );

    let out = PyDict::new_bound(py);
    out.set_item("total_heni_score", h.total_heni_score)?;
    out.set_item("heni_per_100_kcal", h.heni_per_100_kcal)?;
    out.set_item("heni_per_100_grams", h.heni_per_100_grams)?;
    out.set_item("heni_per_serving", h.heni_per_serving)?;
    out.set_item(
        "food_group_contributions",
        hashmap_to_pydict(py, &h.food_group_contributions)?,
    )?;
    out.set_item(
        "nutrient_contributions",
        hashmap_to_pydict(py, &h.nutrient_contributions)?,
    )?;
    out.set_item(
        "disease_burden_breakdown",
        hashmap_to_pydict(py, &h.disease_burden_breakdown)?,
    )?;

    let warns = PyList::empty_bound(py);
    for w in &h.effective_range_warnings {
        warns.append(w)?;
    }
    out.set_item("effective_range_warnings", warns)?;

    out.set_item("health_impact_minutes", h.health_impact_minutes)?;
    out.set_item("health_impact_description", h.health_impact_description)?;

    Ok(out)
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_heni, m)?)?;
    Ok(())
}
