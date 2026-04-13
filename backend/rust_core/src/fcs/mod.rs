//! Food Compass Score (FCS) 2.0 — numeric core exposed as `rust_core.fcs`.

mod engine;
mod kind;
mod targets;

use engine::{fcs_from_original, nova_category_display, original_score_from_attributes, score_attribute_value};
use kind::AttrKind;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
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

fn parse_nested_attributes(d: &Bound<'_, PyDict>) -> PyResult<HashMap<String, HashMap<String, f64>>> {
    let mut out = HashMap::new();
    for (ko, vo) in d.iter() {
        let domain: String = ko.extract()?;
        let inner = vo
            .downcast::<PyDict>()
            .map_err(|_| PyValueError::new_err(format!("domain '{}' must map to a dict", domain)))?;
        let mut im = HashMap::new();
        for (ka, va) in inner.iter() {
            let attr: String = ka.extract()?;
            im.insert(attr, py_to_f64(&va)?);
        }
        out.insert(domain, im);
    }
    Ok(out)
}

/// Full FCS pipeline: nested `attributes` dict (same layout as `FoodItem.attributes`) and CNF `processing_level`.
#[pyfunction]
fn compute_fcs<'py>(
    py: Python<'py>,
    attributes: &Bound<'py, PyDict>,
    processing_level: i32,
) -> PyResult<Bound<'py, PyDict>> {
    let attrs = parse_nested_attributes(attributes)?;
    let original = original_score_from_attributes(&attrs);
    let fcs = fcs_from_original(original);
    let d = PyDict::new_bound(py);
    d.set_item("original_score", original)?;
    d.set_item("fcs", fcs)?;
    d.set_item("nova_category", nova_category_display(processing_level))?;
    Ok(d)
}

/// Returns ``"BENEFICIAL"``, ``"HARMFUL"``, or ``"RATIO"`` (matches ``AttributeType.name``).
#[pyfunction]
fn fcs_attribute_kind(attribute: &str) -> PyResult<String> {
    match kind::attribute_kind(attribute) {
        Some(AttrKind::Beneficial) => Ok("BENEFICIAL".to_string()),
        Some(AttrKind::Harmful) => Ok("HARMFUL".to_string()),
        Some(AttrKind::Ratio) => Ok("RATIO".to_string()),
        None => Err(PyValueError::new_err(format!(
            "Unknown attribute type for attribute: {}",
            attribute
        ))),
    }
}

#[pyfunction]
fn fcs_score_attribute(value: f64, attribute: &str) -> PyResult<f64> {
    score_attribute_value(value, attribute).ok_or_else(|| {
        PyValueError::new_err(format!("No reference targets or unknown attribute: {}", attribute))
    })
}

pub fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_fcs, m)?)?;
    m.add_function(wrap_pyfunction!(fcs_attribute_kind, m)?)?;
    m.add_function(wrap_pyfunction!(fcs_score_attribute, m)?)?;
    Ok(())
}
