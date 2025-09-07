//! XML to JSON conversion utilities.
//!
//! Converts XML to JSON format optimized for Polars DataFrame loading with unknown schemas.
//! Use with `infer_schema_length = None` when creating DataFrames from the resulting JSON.
//!
//! ## Key Behaviors
//!
//! - **Uniform arrays**: Both single and repeated elements become arrays for consistent schema inference
//!   - `<item>a</item>` → `{"item": ["a"]}`
//!   - `<item>a</item><item>b</item>` → `{"item": ["a", "b"]}`
//! - **Attributes**: Prefixed with '@' to avoid conflicts with element names
//! - **Mixed content**: Text in elements with children stored as '#text' entries
//! - **Empty elements**: Self-closing/empty tags become null values
//! - **Structure preservation**: Element order maintained via IndexMap
//! - **Namespace handling**: Prefixes kept in element names, declarations treated as attributes
//!
//! ## Ignored XML Features
//! - Processing instructions, DTDs, comments (not relevant for data extraction)
//! - Custom entity definitions (entity references passed through as text)
//! - Character references are automatically unescaped by quick_xml

use quick_xml::reader::Reader;
use quick_xml::events::Event;
use serde_json::{Value, Map};
use indexmap::IndexMap;

// Constants for common strings to reduce allocations
const ATTR_PREFIX: &str = "@";
const TEXT_KEY: &str = "#text";

#[derive(Debug, Clone)]
pub struct XmlNode {
    pub tag: String,
    pub attributes: IndexMap<String, String>,
    pub children: Vec<XmlNode>,
    pub text: Option<String>,
}

impl XmlNode {
    pub fn new(tag: String) -> Self {
        Self { tag, attributes: IndexMap::new(), children: Vec::new(), text: None }
    }

    pub fn to_json(&self) -> Value {
        // Handle self-closing tags with no text as null values
        if self.text.is_none() && self.children.is_empty() && self.attributes.is_empty() {
            return Value::Null;
        }

        // If there's text and no children, return just the text
        if let Some(text) = &self.text {
            let cleaned_text = text.trim();
            if !cleaned_text.is_empty() && self.children.is_empty() {
                if self.attributes.is_empty() {
                    return Value::String(cleaned_text.to_string());
                } else {
                    // Has both text and attributes
                    let mut json = Map::with_capacity(self.attributes.len() + 1);

                    // Add attributes with '@' prefix
                    for (key, value) in &self.attributes {
                        let mut attr_key = String::with_capacity(ATTR_PREFIX.len() + key.len());
                        attr_key.push_str(ATTR_PREFIX);
                        attr_key.push_str(key);
                        json.insert(attr_key, Value::String(value.clone()));
                    }

                    json.insert(TEXT_KEY.to_string(), Value::String(cleaned_text.to_string()));
                    return Value::Object(json);
                }
            }
        }

        // Pre-allocate map (which will grow as needed)
        let mut json = Map::with_capacity(self.attributes.len());

        // Add attributes with '@' prefix
        for (key, value) in &self.attributes {
            let mut attr_key = String::with_capacity(ATTR_PREFIX.len() + key.len());
            attr_key.push_str(ATTR_PREFIX);
            attr_key.push_str(key);
            json.insert(attr_key, Value::String(value.clone()));
        }

        // Group children by tag name
        if !self.children.is_empty() {
            let mut children_groups: IndexMap<&str, Vec<&XmlNode>> = IndexMap::new();
            for child in &self.children {
                children_groups.entry(child.tag.as_str()).or_insert_with(Vec::new).push(child);
            }

            for (tag, children) in children_groups {
                let array: Vec<Value> = children.iter().map(|child| child.to_json()).collect();
                json.insert(tag.to_string(), Value::Array(array));
            }
        }

        Value::Object(json)

    }
}

fn create_node_from_event(e: &quick_xml::events::BytesStart) -> Result<XmlNode, String> {
    // More efficient: avoid intermediate Cow allocation
    let tag = match std::str::from_utf8(e.name().as_ref()) {
        Ok(s) => s.to_string(),
        Err(_) => String::from_utf8_lossy(e.name().as_ref()).into_owned(),
    };
    let mut node = XmlNode::new(tag);
    let attrs = e.attributes();
    node.attributes.reserve(attrs.size_hint().0);

    for attr in attrs {
        match attr {
            Ok(attr) => {
                // More efficient: avoid Cow allocations
                let key = match std::str::from_utf8(attr.key.as_ref()) {
                    Ok(s) => s.to_string(),
                    Err(_) => String::from_utf8_lossy(attr.key.as_ref()).into_owned(),
                };
                let value = match std::str::from_utf8(&attr.value) {
                    Ok(s) => s.to_string(),
                    Err(_) => String::from_utf8_lossy(&attr.value).into_owned(),
                };
                node.attributes.insert(key, value);
            }
            Err(e) => return Err(e.to_string()),
        }
    }

    Ok(node)
}

fn handle_completed_node(node: XmlNode, stack: &mut Vec<XmlNode>, root: &mut Option<XmlNode>) {
    if stack.is_empty() {
        *root = Some(node);
    } else {
        if let Some(parent) = stack.last_mut() {
            parent.children.push(node);
        }
    }
}

pub fn get_xml_node(xml_str: &str) -> Result<XmlNode, String> {
    let mut reader = Reader::from_str(xml_str);
    let mut buf = Vec::new();
    let mut stack: Vec<XmlNode> = Vec::new();
    let mut root: Option<XmlNode> = None;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) => {
                let node = create_node_from_event(e)?;
                stack.push(node);
            }
            Ok(Event::End(_)) => {
                if let Some(node) = stack.pop() {
                    handle_completed_node(node, &mut stack, &mut root);
                }
            }
            Ok(Event::Empty(ref e)) => {
                let node = create_node_from_event(e)?;
                handle_completed_node(node, &mut stack, &mut root);
            }
            Ok(Event::Text(ref e)) => {
                let text = e.unescape().map_err(|e| e.to_string())?;
                let text_str = text.trim();
                if !text_str.is_empty() {
                    if let Some(parent) = stack.last_mut() {
                        parent.text = Some(text_str.to_string());
                    }
                }
            }
            Ok(Event::CData(ref e)) => {
                let text = String::from_utf8_lossy(e.as_ref());
                if let Some(parent) = stack.last_mut() {
                    parent.text = Some(text.to_string());
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(e.to_string()),
            _ => {}
        }
        buf.clear();
    }

    root.ok_or_else(|| "No root element found".to_string())
}
