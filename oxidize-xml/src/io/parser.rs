//! Core XML parsing and streaming functionality.
//!
//! Provides hybrid streaming XML parsing with parallel batch processing for high performance
//! extraction of repeated XML elements.

use quick_xml::Reader;
use quick_xml::events::Event;
use std::io::{BufRead, Write};
use std::collections::VecDeque;
use std::path::PathBuf;
use rayon::prelude::*;
use crate::io::xml_utils::get_xml_node;
use crate::io::error::OxidizeError;

// Constants for magic numbers
pub const DEFAULT_BATCH_SIZE: usize = 1000;
const MAX_BATCH_SIZE: usize = 1_000_000;

// Security limits to prevent XML bomb attacks
const MAX_ELEMENT_DEPTH: usize = 1000;        // Maximum nesting depth
const MAX_ELEMENT_SIZE: usize = 10_000_000;   // Maximum element size (10MB)
const MAX_ATTRIBUTE_COUNT: usize = 1000;      // Maximum attributes per element
const MAX_ATTRIBUTE_SIZE: usize = 65536;      // Maximum attribute value size (64KB)

// Helper function to write tag with attributes to a buffer
fn write_tag_with_attributes(buf: &mut Vec<u8>, e: &quick_xml::events::BytesStart, self_closing: bool) {
    buf.extend_from_slice(b"<");
    buf.extend_from_slice(e.name().as_ref());
    for attr in e.attributes() {
        if let Ok(attr) = attr {
            buf.extend_from_slice(b" ");
            buf.extend_from_slice(attr.key.as_ref());
            buf.extend_from_slice(b"=\"");
            buf.extend_from_slice(&attr.value);
            buf.extend_from_slice(b"\"");
        }
    }
    if self_closing {
        buf.extend_from_slice(b"/>");
    } else {
        buf.extend_from_slice(b">");
    }
}

// Helper function to write opening tag with attributes to a buffer
fn write_opening_tag(buf: &mut Vec<u8>, e: &quick_xml::events::BytesStart) {
    write_tag_with_attributes(buf, e, false);
}

// Helper function to write self-closing tag with attributes to a buffer
fn write_self_closing_tag(buf: &mut Vec<u8>, e: &quick_xml::events::BytesStart) {
    write_tag_with_attributes(buf, e, true);
}

// Helper function to write closing tag to a buffer
fn write_closing_tag(buf: &mut Vec<u8>, e: &quick_xml::events::BytesEnd) {
    buf.extend_from_slice(b"</");
    buf.extend_from_slice(e.name().as_ref());
    buf.extend_from_slice(b">");
}

/// Hybrid streaming parser that uses quick_xml for streaming and parallel processing for batches
pub struct HybridStreamParser {
    batch_size: usize,
    element_queue: VecDeque<String>,
    // Reusable buffer to reduce allocations
    temp_buffer: Vec<u8>,
    // Security tracking
    current_depth: usize,
    max_depth_reached: usize,
}

impl HybridStreamParser {
    pub fn new(batch_size: usize) -> Self {
        Self {
            batch_size,
            element_queue: VecDeque::new(),
            temp_buffer: Vec::new(), // Start small, grow naturally
            current_depth: 0,
            max_depth_reached: 0,
        }
    }

    /// Add a complete element to the queue
    fn queue_element(&mut self, element_xml: String) {
        self.element_queue.push_back(element_xml);
    }
    
    /// Create and queue a self-closing element using reusable buffer
    fn queue_self_closing_element(&mut self, e: &quick_xml::events::BytesStart) -> Result<(), OxidizeError> {
        // Security check: validate attributes
        self.validate_element_security(e)?;
        
        self.temp_buffer.clear();
        write_self_closing_tag(&mut self.temp_buffer, e);
        
        // Security check: element size
        if self.temp_buffer.len() > MAX_ELEMENT_SIZE {
            return Err(OxidizeError::MemoryError {
                message: format!("Element too large: {} bytes exceeds limit of {}", 
                    self.temp_buffer.len(), MAX_ELEMENT_SIZE),
            });
        }
        
        // Use mem::take to avoid clone - takes ownership of buffer contents
        if let Ok(element_str) = String::from_utf8(std::mem::take(&mut self.temp_buffer)) {
            self.queue_element(element_str);
        }
        
        Ok(())
    }
    
    /// Validate element for security concerns
    fn validate_element_security(&self, e: &quick_xml::events::BytesStart) -> Result<(), OxidizeError> {
        // Check attribute count
        let attr_count = e.attributes().size_hint().0;
        if attr_count > MAX_ATTRIBUTE_COUNT {
            return Err(OxidizeError::InvalidInput {
                message: format!("Too many attributes: {} exceeds limit of {}", 
                    attr_count, MAX_ATTRIBUTE_COUNT),
                context: "Potential XML bomb attack detected".to_string(),
            });
        }
        
        // Check individual attribute sizes
        for attr_result in e.attributes() {
            if let Ok(attr) = attr_result {
                if attr.value.len() > MAX_ATTRIBUTE_SIZE {
                    return Err(OxidizeError::InvalidInput {
                        message: format!("Attribute value too large: {} bytes exceeds limit of {}", 
                            attr.value.len(), MAX_ATTRIBUTE_SIZE),
                        context: "Potential XML bomb attack detected".to_string(),
                    });
                }
            }
        }
        
        Ok(())
    }
    
    /// Check and update depth tracking for security
    fn check_depth(&mut self, increment: bool) -> Result<(), OxidizeError> {
        if increment {
            self.current_depth += 1;
            if self.current_depth > self.max_depth_reached {
                self.max_depth_reached = self.current_depth;
            }
            
            if self.current_depth > MAX_ELEMENT_DEPTH {
                return Err(OxidizeError::InvalidInput {
                    message: format!("XML nesting too deep: {} exceeds limit of {}", 
                        self.current_depth, MAX_ELEMENT_DEPTH),
                    context: "Potential XML bomb attack detected".to_string(),
                });
            }
        } else if self.current_depth > 0 {
            self.current_depth -= 1;
        }
        
        Ok(())
    }

    /// Process batch if queue is full and write results
    pub fn process_batch_if_full<W: Write>(&mut self, writer: &mut W, total_count: &mut usize) -> Result<(), OxidizeError> {
        if self.element_queue.len() >= self.batch_size {
            let results = self.process_batch();
            *total_count += results.len();

            // Write results
            for json_line in results {
                writeln!(writer, "{}", json_line)
                    .map_err(|e| OxidizeError::IoError {
                        message: format!("Failed to write JSON output: {}", e),
                    })?;
            }
        }
        Ok(())
    }

    /// Process a batch of elements in parallel
    fn process_batch(&mut self) -> Vec<String> {
        if self.element_queue.is_empty() {
            return Vec::new();
        }

        let batch_size = self.batch_size.min(self.element_queue.len());
        
        // Process elements directly from the queue without intermediate collection
        let batch_elements: Vec<_> = self.element_queue.drain(..batch_size).collect();
        
        // Process in parallel using Rayon
        let results = batch_elements
            .par_iter()
            .filter_map(|xml_str| {
                // Parse each element
                match get_xml_node(xml_str) {
                    Ok(node) => {
                        // Convert XmlNode to serde_json::Value
                        let value = node.to_json();
                        // Serialize to string
                        match serde_json::to_string(&value) {
                            Ok(json) => Some(json),
                            Err(_) => None,
                        }
                    }
                    Err(_) => None,
                }
            })
            .collect();
            
        results
    }

    /// Process remaining elements
    pub fn flush(&mut self) -> Vec<String> {
        // Pre-allocate with remaining queue size to avoid reallocations
        let mut all_results = Vec::with_capacity(self.element_queue.len());

        while !self.element_queue.is_empty() {
            let batch_results = self.process_batch();
            all_results.extend(batch_results);
        }

        all_results
    }

    /// Public method to queue self-closing elements (used by the main parsing function)
    pub fn queue_self_closing_element_public(&mut self, e: &quick_xml::events::BytesStart) -> Result<(), OxidizeError> {
        self.queue_self_closing_element(e)
    }

    /// Public method to validate element security (used by the main parsing function)
    pub fn validate_element_security_public(&self, e: &quick_xml::events::BytesStart) -> Result<(), OxidizeError> {
        self.validate_element_security(e)
    }

    /// Public method to check depth (used by the main parsing function)
    pub fn check_depth_public(&mut self, increment: bool) -> Result<(), OxidizeError> {
        self.check_depth(increment)
    }

    /// Public method to queue element (used by the main parsing function)
    pub fn queue_element_public(&mut self, element_xml: String) {
        self.queue_element(element_xml)
    }
}

/// Sanitize and validate file paths for security
pub fn sanitize_path(path: &str, operation: &str) -> Result<PathBuf, OxidizeError> {
    let path_buf = PathBuf::from(path);
    
    // Check for empty path
    if path.is_empty() {
        return Err(OxidizeError::InvalidInput {
            message: "Path cannot be empty".to_string(),
            context: format!("{} operation requires valid path", operation),
        });
    }
    
    // Check for null bytes (security risk)
    if path.contains('\0') {
        return Err(OxidizeError::InvalidInput {
            message: "Path contains null bytes".to_string(),
            context: "Null bytes in paths are a security risk".to_string(),
        });
    }
    
    // Normalize path to prevent directory traversal
    let canonical_path = match path_buf.canonicalize() {
        Ok(p) => p,
        Err(_) => {
            // If canonicalize fails, validate manually for basic security
            if path.contains("..") {
                return Err(OxidizeError::InvalidInput {
                    message: "Path traversal detected".to_string(),
                    context: "Paths containing '..' are not allowed for security reasons".to_string(),
                });
            }
            path_buf
        }
    };
    
    // Check path length (prevent extremely long paths)
    if path.len() > 4096 {
        return Err(OxidizeError::InvalidInput {
            message: "Path too long".to_string(),
            context: "Paths longer than 4096 characters are not allowed".to_string(),
        });
    }
    
    Ok(canonical_path)
}

/// Validate input parameters
pub fn validate_inputs(target_element: &str, batch_size: usize) -> Result<(), OxidizeError> {
    if target_element.is_empty() {
        return Err(OxidizeError::InvalidInput {
            message: "target_element cannot be empty".to_string(),
            context: "XML element name must be specified".to_string(),
        });
    }
    
    if batch_size == 0 {
        return Err(OxidizeError::InvalidInput {
            message: "batch_size must be greater than 0".to_string(),
            context: format!("Received batch_size: {}", batch_size),
        });
    }
    
    if batch_size > MAX_BATCH_SIZE {
        return Err(OxidizeError::MemoryError {
            message: format!("batch_size {} is too large, maximum is 1,000,000", batch_size),
        });
    }
    
    Ok(())
}

/// Stream parse file using quick_xml and process batches in parallel
pub fn hybrid_stream_parse<R: BufRead, W: Write>(
    reader: R,
    mut writer: W,
    target_element: &str,
    batch_size: usize,
) -> Result<usize, OxidizeError> {
    // Validate inputs first
    validate_inputs(target_element, batch_size)?;
    let mut parser = HybridStreamParser::new(batch_size);
    let mut xml_reader = Reader::from_reader(reader);
    xml_reader.trim_text(true);

    let mut buf = Vec::new();
    let mut element_buf = Vec::new();
    let mut in_target = false;
    let mut depth = 0;
    let mut total_count = 0;

    let target_bytes = target_element.as_bytes();

    loop {
        match xml_reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) => {
                if e.name().as_ref() == target_bytes {
                    // Security check for target element
                    parser.validate_element_security_public(e)?;
                    parser.check_depth_public(true)?;
                    
                    in_target = true;
                    depth = 1;
                    element_buf.clear();
                    write_opening_tag(&mut element_buf, e);
                } else if in_target {
                    parser.check_depth_public(true)?;
                    depth += 1;
                    write_opening_tag(&mut element_buf, e);
                }
            }
            Ok(Event::End(ref e)) => {
                if in_target {
                    write_closing_tag(&mut element_buf, e);

                    depth -= 1;
                    parser.check_depth_public(false)?;
                    
                    if depth == 0 && e.name().as_ref() == target_bytes {
                        // Complete element found - security check size
                        if element_buf.len() > MAX_ELEMENT_SIZE {
                            return Err(OxidizeError::MemoryError {
                                message: format!("Element too large: {} bytes exceeds limit of {}", 
                                    element_buf.len(), MAX_ELEMENT_SIZE),
                            });
                        }
                        
                        in_target = false;

                        // Convert to string and queue - use mem::take to avoid clone
                        if let Ok(element_str) = String::from_utf8(std::mem::take(&mut element_buf)) {
                            parser.queue_element_public(element_str);
                        }

                        // Process batch if queue is full
                        parser.process_batch_if_full(&mut writer, &mut total_count)?;

                        element_buf.clear();
                    }
                }
            }
            Ok(Event::Empty(ref e)) => {
                if e.name().as_ref() == target_bytes {
                    // Use optimized method for self-closing elements with security checks
                    parser.queue_self_closing_element_public(e)?;

                    // Process batch if queue is full
                    parser.process_batch_if_full(&mut writer, &mut total_count)?;
                }
            }
            Ok(Event::Text(ref e)) => {
                if in_target {
                    element_buf.extend_from_slice(e.as_ref());
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(OxidizeError::XmlParseError {
                position: Some(xml_reader.buffer_position()),
                message: format!("Failed to parse XML: {}", e),
            }),
            _ => {} // Ignore other events
        }

        buf.clear();
    }

    // Process remaining elements
    let final_results = parser.flush();
    total_count += final_results.len();

    for json_line in final_results {
        writeln!(writer, "{}", json_line)
            .map_err(|e| OxidizeError::IoError {
                message: format!("Failed to write final JSON output: {}", e),
            })?;
    }

    Ok(total_count)
}

// Constants are already public above

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn test_hybrid_stream_parser_new() {
        let parser = HybridStreamParser::new(100);
        assert_eq!(parser.batch_size, 100);
        assert!(parser.element_queue.is_empty());
    }

    #[test]
    fn test_basic_xml_parsing() {
        let xml = r#"<?xml version="1.0"?>
<root>
    <Item id="1"><Value>100</Value></Item>
    <Item id="2"><Value>200</Value></Item>
</root>"#;

        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 2);

        let output_str = String::from_utf8(output).unwrap();
        assert!(output_str.contains("\"id\":\"1\""));
        assert!(output_str.contains("\"Value\":\"100\""));
        assert!(output_str.contains("\"id\":\"2\""));
    }

    #[test]
    fn test_empty_xml() {
        let xml = "<?xml version=\"1.0\"?><root></root>";
        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 0);
        assert!(output.is_empty());
    }

    #[test]
    fn test_batch_size_variations() {
        let xml = r#"<?xml version="1.0"?>
<root>
    <R id="1"/>
    <R id="2"/>
    <R id="3"/>
    <R id="4"/>
    <R id="5"/>
</root>"#;

        // Test with batch size 1
        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();
        let result = hybrid_stream_parse(reader, &mut output, "R", 1);
        assert_eq!(result.unwrap(), 5);

        // Test with batch size 3
        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();
        let result = hybrid_stream_parse(reader, &mut output, "R", 3);
        assert_eq!(result.unwrap(), 5);

        // Test with batch size 10 (larger than element count)
        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();
        let result = hybrid_stream_parse(reader, &mut output, "R", 10);
        assert_eq!(result.unwrap(), 5);
    }

    #[test]
    fn test_attributes_handling() {
        let xml = r#"<?xml version="1.0"?>
<root>
    <Item id="123" type="test" enabled="true"/>
</root>"#;

        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1);

        let output_str = String::from_utf8(output).unwrap();
        assert!(output_str.contains("\"id\":\"123\""));
        assert!(output_str.contains("\"type\":\"test\""));
        assert!(output_str.contains("\"enabled\":\"true\""));
    }

    #[test]
    fn test_invalid_xml() {
        // Test with malformed XML - the parser may handle some incomplete XML gracefully
        let xml = "<root><Item>Unclosed";
        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        // The parser handles incomplete XML by returning 0 elements
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 0);
    }

    #[test]
    fn test_self_closing_target_elements() {
        // Test that self-closing elements are properly captured when they ARE the target
        let xml = r#"<?xml version="1.0"?>
<root>
    <Item id="1" status="active"/>
    <Item id="2" status="inactive"/>
    <Item id="3"><Name>With Content</Name></Item>
</root>"#;

        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 3); // Should capture all 3 items

        let output_str = String::from_utf8(output).unwrap();
        // Check all items are captured
        assert!(output_str.contains("\"id\":\"1\""));
        assert!(output_str.contains("\"id\":\"2\""));
        assert!(output_str.contains("\"id\":\"3\""));
        assert!(output_str.contains("\"status\":\"active\""));
        assert!(output_str.contains("\"status\":\"inactive\""));
        assert!(output_str.contains("With Content"));
    }

    #[test]
    fn test_special_characters() {
        let xml = r#"<?xml version="1.0"?>
<root>
    <Item>Text&lt;&gt;&amp;&quot;&apos;</Item>
</root>"#;

        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1);

        let output_str = String::from_utf8(output).unwrap();
        // Check that special characters are unescaped in JSON
        assert!(output_str.contains("<>&"));
    }

    #[test]
    fn test_nested_elements() {
        let xml = r#"<?xml version="1.0"?>
<root>
    <Item id="1">
        <Child>
            <GrandChild>Value</GrandChild>
        </Child>
    </Item>
</root>"#;

        let reader = Cursor::new(xml.as_bytes());
        let mut output = Vec::new();

        let result = hybrid_stream_parse(reader, &mut output, "Item", 10);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1);

        let output_str = String::from_utf8(output).unwrap();
        assert!(output_str.contains("\"Child\""));
        assert!(output_str.contains("\"GrandChild\""));
    }
}