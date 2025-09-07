use pyo3::prelude::*;

pub mod io;

// Import from the new modular structure
pub use io::python_api::*;

#[pymodule]
fn oxidize_xml(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_xml_file_to_json_file, m)?)?;
    m.add_function(wrap_pyfunction!(parse_xml_file_to_json_string, m)?)?;
    m.add_function(wrap_pyfunction!(parse_xml_string_to_json_file, m)?)?;
    m.add_function(wrap_pyfunction!(parse_xml_string_to_json_string, m)?)?;
    Ok(())
}






