use pyo3::prelude::*;

mod fcs;
mod heni;
mod hsr;

#[pyfunction]
fn ping() -> &'static str {
    "pong"
}

#[pymodule]
fn rust_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let py = m.py();

    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(ping, m)?)?;

    let hsr_mod = PyModule::new_bound(py, "hsr")?;
    hsr::register(&hsr_mod)?;
    m.add_submodule(&hsr_mod)?;

    py.import_bound("sys")?
        .getattr("modules")?
        .set_item("rust_core.hsr", &hsr_mod)?;

    let fcs_mod = PyModule::new_bound(py, "fcs")?;
    fcs::register(&fcs_mod)?;
    m.add_submodule(&fcs_mod)?;
    py.import_bound("sys")?
        .getattr("modules")?
        .set_item("rust_core.fcs", &fcs_mod)?;

    let heni_mod = PyModule::new_bound(py, "heni")?;
    heni::register(&heni_mod)?;
    m.add_submodule(&heni_mod)?;
    py.import_bound("sys")?
        .getattr("modules")?
        .set_item("rust_core.heni", &heni_mod)?;

    Ok(())
}
