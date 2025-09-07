//! Error types and handling for the oxidize-xml XML parser.
//!
//! Provides structured error types with detailed context for different failure scenarios.

use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyIOError, PyRuntimeError};

/// Structured error types for better error handling
#[derive(Debug)]
pub enum OxidizeError {
    InvalidInput { message: String, context: String },
    FileError { path: String, error: String },
    XmlParseError { position: Option<usize>, message: String },
    MemoryError { message: String },
    IoError { message: String },
}

impl std::fmt::Display for OxidizeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            OxidizeError::InvalidInput { message, context } => {
                write!(f, "Invalid input: {} (context: {})", message, context)
            }
            OxidizeError::FileError { path, error } => {
                write!(f, "File error for '{}': {}", path, error)
            }
            OxidizeError::XmlParseError { position, message } => {
                match position {
                    Some(pos) => write!(f, "XML parsing error at position {}: {}", pos, message),
                    None => write!(f, "XML parsing error: {}", message),
                }
            }
            OxidizeError::MemoryError { message } => {
                write!(f, "Memory error: {}", message)
            }
            OxidizeError::IoError { message } => {
                write!(f, "I/O error: {}", message)
            }
        }
    }
}

impl std::error::Error for OxidizeError {}

impl From<OxidizeError> for PyErr {
    fn from(err: OxidizeError) -> Self {
        match err {
            OxidizeError::InvalidInput { .. } => PyValueError::new_err(err.to_string()),
            OxidizeError::FileError { .. } => PyIOError::new_err(err.to_string()),
            OxidizeError::XmlParseError { .. } => PyValueError::new_err(err.to_string()),
            OxidizeError::MemoryError { .. } => PyRuntimeError::new_err(err.to_string()),
            OxidizeError::IoError { .. } => PyIOError::new_err(err.to_string()),
        }
    }
}