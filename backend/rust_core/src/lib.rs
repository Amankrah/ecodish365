use pyo3::prelude::*;

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

    Ok(())
}
