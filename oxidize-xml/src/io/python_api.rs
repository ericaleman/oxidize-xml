//! Python API bindings for the oxidize-xml XML parser.
//!
//! Provides high-level Python functions that handle different input/output combinations
//! with proper error handling and parameter validation.

use pyo3::prelude::*;
use std::io::{BufRead, BufReader};
use std::fs::File;
use crate::io::error::OxidizeError;
use crate::io::parser::{hybrid_stream_parse, sanitize_path, DEFAULT_BATCH_SIZE};

// Input/output handling is now done through specific functions rather than enums

/// Helper function to create a buffered reader from file path
fn create_file_reader(path: &str) -> Result<Box<dyn BufRead>, OxidizeError> {
    let safe_path = sanitize_path(path, "read")?;
    let file = File::open(&safe_path)
        .map_err(|e| OxidizeError::FileError {
            path: path.to_string(),
            error: format!("Cannot open input file: {}", e),
        })?;
    Ok(Box::new(BufReader::new(file)))
}

/// Helper function to create a buffered reader from string content
fn create_string_reader(content: &str) -> Box<dyn BufRead + '_> {
    Box::new(std::io::Cursor::new(content.as_bytes()))
}

/// Helper function to create a file writer
fn create_file_writer(path: &str) -> Result<std::io::BufWriter<File>, OxidizeError> {
    let safe_path = sanitize_path(path, "write")?;
    let file = File::create(&safe_path)
        .map_err(|e| OxidizeError::FileError {
            path: path.to_string(),
            error: format!("Cannot create output file: {}", e),
        })?;
    Ok(std::io::BufWriter::new(file))
}

/// Helper function to convert Vec<u8> output to String with proper error handling
fn vec_to_string(output: Vec<u8>) -> Result<String, OxidizeError> {
    String::from_utf8(output)
        .map_err(|e| OxidizeError::IoError {
            message: format!("Failed to convert output to UTF-8 string: {}", e),
        })
}

/// Common validation and setup for all Python functions
fn setup_parsing_params(target_element: &str, batch_size: Option<usize>) -> Result<usize, OxidizeError> {
    let batch_size = batch_size.unwrap_or(DEFAULT_BATCH_SIZE);
    crate::io::parser::validate_inputs(target_element, batch_size)?;
    Ok(batch_size)
}

/// Core parsing function for file input, file output
fn parse_file_to_file(input_path: &str, output_path: &str, target_element: &str, batch_size: usize) -> Result<usize, OxidizeError> {
    let reader = create_file_reader(input_path)?;
    let mut writer = create_file_writer(output_path)?;
    hybrid_stream_parse(reader, &mut writer, target_element, batch_size)
}

/// Core parsing function for file input, string output
fn parse_file_to_string(input_path: &str, target_element: &str, batch_size: usize) -> Result<String, OxidizeError> {
    let reader = create_file_reader(input_path)?;
    let mut output_vec = Vec::new();
    hybrid_stream_parse(reader, &mut output_vec, target_element, batch_size)?;
    vec_to_string(output_vec)
}

/// Core parsing function for string input, file output  
fn parse_string_to_file(content: &str, output_path: &str, target_element: &str, batch_size: usize) -> Result<usize, OxidizeError> {
    let reader = create_string_reader(content);
    let mut writer = create_file_writer(output_path)?;
    hybrid_stream_parse(reader, &mut writer, target_element, batch_size)
}

/// Core parsing function for string input, string output
fn parse_string_to_string(content: &str, target_element: &str, batch_size: usize) -> Result<String, OxidizeError> {
    let reader = create_string_reader(content);
    let mut output_vec = Vec::new();
    hybrid_stream_parse(reader, &mut output_vec, target_element, batch_size)?;
    vec_to_string(output_vec)
}

/// Python-exposed function: file input -> file output
#[pyfunction]
#[pyo3(signature = (input_path, target_element, output_path, batch_size=None))]
pub fn parse_xml_file_to_json_file(
    input_path: &str,
    target_element: &str,
    output_path: &str,
    batch_size: Option<usize>,
) -> PyResult<usize> {
    let batch_size = setup_parsing_params(target_element, batch_size).map_err(PyErr::from)?;
    parse_file_to_file(input_path, output_path, target_element, batch_size).map_err(PyErr::from)
}

/// Python-exposed function: file input -> string output
#[pyfunction]
#[pyo3(signature = (input_path, target_element, batch_size=None))]
pub fn parse_xml_file_to_json_string(
    input_path: &str,
    target_element: &str,
    batch_size: Option<usize>,
) -> PyResult<String> {
    let batch_size = setup_parsing_params(target_element, batch_size).map_err(PyErr::from)?;
    parse_file_to_string(input_path, target_element, batch_size).map_err(PyErr::from)
}

/// Python-exposed function: string input -> file output
#[pyfunction]
#[pyo3(signature = (xml_content, target_element, output_path, batch_size=None))]
pub fn parse_xml_string_to_json_file(
    xml_content: &str,
    target_element: &str,
    output_path: &str,
    batch_size: Option<usize>,
) -> PyResult<usize> {
    let batch_size = setup_parsing_params(target_element, batch_size).map_err(PyErr::from)?;
    parse_string_to_file(xml_content, output_path, target_element, batch_size).map_err(PyErr::from)
}

/// Python-exposed function: string input -> string output
#[pyfunction]
#[pyo3(signature = (xml_content, target_element, batch_size=None))]
pub fn parse_xml_string_to_json_string(
    xml_content: &str,
    target_element: &str,
    batch_size: Option<usize>,
) -> PyResult<String> {
    let batch_size = setup_parsing_params(target_element, batch_size).map_err(PyErr::from)?;
    parse_string_to_string(xml_content, target_element, batch_size).map_err(PyErr::from)
}