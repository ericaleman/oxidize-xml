# oxidize-xml

High-performance XML to JSON streaming parser built with Rust and PyO3. Specialized for extracting repeated elements from large XML files like API responses, log files, and data exports, particularly for engineers and analysts working in DuckDB, Polars, and Pandas.

## Key Features

- **High Performance**: 2-3x faster than lxml, built with Rust's quick-xml parser with batch processing in Rayon
- **Low Memory Usage**: Streaming architecture processes files larger than available RAM
- **Specialized Design**: Opinionated API and schema design for common data engineering and data analysis workflows

## Use Cases

Perfect for extracting structured data from XML files containing repeated elements into newline JSON
- **API responses**: Extract `<record>`, `<item>`, or `<entry>` elements from REST API responses
- **Log files**: Parse `<event>` or `<log>` entries from XML-formatted logs
- **Data exports**: Process `<row>`, `<product>`, or `<transaction>` elements from database exports
- **Configuration files**: Extract `<server>`, `<user>`, or similar repeated configuration blocks

## Installation

```bash
pip install oxidize-xml
```

## Development Setup

```bash
# Install dependencies
poetry install

# Build the extension
./build.sh

# Run tests
pytest tests/
```

## Usage

Extract specific elements from XML and convert to JSON-Lines:

```python
import oxidize_xml

# File to file
count = oxidize_xml.parse_xml_file_to_json_file("data.xml", "book", "books.json")

# File to string  
json_lines = oxidize_xml.parse_xml_file_to_json_string("data.xml", "book")

# String to string
result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "book")

# String to file
result = oxidize_xml.parse_xml_string_to_json_file(xml_content, "book")
```

## Conversion Rules

**Uniform arrays**: All elements become arrays for consistent schema inference:

```xml
<book id="bk101">
    <author>J.K. Rowling</author>
    <title>Harry Potter</title>
</book>
```

```json
{
  "@id": "bk101",
  "author": ["J.K. Rowling"], 
  "title": ["Harry Potter"]
}
```

**Key behaviors:**
- **Attributes**: Prefixed with `@` to avoid conflicts with element names
- **Mixed content**: Text in elements with children stored as `#text` entries
- **Empty elements**: Self-closing/empty tags become `null` values
- **Structure preservation**: Element order maintained via IndexMap
- **Namespace handling**: Prefixes kept in element names, declarations treated as attributes

**Ignored features:**
- Processing instructions, DTDs, comments (not relevant for data extraction)
- Custom entity definitions (entity references passed through as text)
- Character references automatically unescaped by quick_xml


## API

```python
parse_xml_file_to_json_file(input_path, target_element, output_path, batch_size=1000) -> int
parse_xml_file_to_json_string(input_path, target_element, batch_size=1000) -> str  
parse_xml_string_to_json_file(xml_content, target_element, output_path, batch_size=1000) -> int
parse_xml_string_to_json_string(xml_content, target_element, batch_size=1000) -> str
```

**Parameters:**
- `batch_size`: Number of elements to process per batch (default: 1000, min: 1)
- Returns the number of elements processed, or raises `ValueError` for invalid inputs


## Testing

Run the test suite:

```bash
# All tests
pytest tests/

# Integration tests only  
pytest tests/integration/

# Performance benchmarks
pytest tests/performance/ --benchmark-only

# With coverage
pytest --cov=oxidize_xml --cov-report=html
```

Test coverage includes:
- Core functionality validation
- Error handling with malformed XML
- Performance regression detection
- Memory usage monitoring
- Edge cases and concurrent operations

## Architecture

```
oxidize-xml/src/io/
├── error.rs         # Centralized error handling and Python conversions
├── parser.rs        # Core XML streaming parser with security validations  
├── python_api.rs    # Clean Python function wrappers with shared logic
├── xml_utils.rs     # XML-to-JSON conversion utilities
└── mod.rs          # Module organization and exports
```


## Security

oxidize-xml includes various security protections against XML-based attacks:

### File Path Security
- **Path sanitization**: Prevents directory traversal attacks (`../` sequences)
- **Null byte protection**: Rejects paths containing null bytes
- **Path length limits**: Maximum 4096 character paths
- **Canonical path validation**: Uses system path normalization

### XML Bomb Protection
- **Element nesting limit**: Maximum 1000 levels of nesting depth
- **Element size limit**: Maximum 10MB per element
- **Attribute limits**: Maximum 1000 attributes per element
- **Attribute size limit**: Maximum 64KB per attribute value

### Security Limits
```rust
MAX_ELEMENT_DEPTH: 1000        // Maximum XML nesting depth
MAX_ELEMENT_SIZE: 10_000_000   // Maximum element size (10MB)
MAX_ATTRIBUTE_COUNT: 1000      // Maximum attributes per element  
MAX_ATTRIBUTE_SIZE: 65536      // Maximum attribute size (64KB)
```

These limits prevent:
- **Billion laughs attacks**: Exponential entity expansion
- **Quadratic blowup attacks**: Deeply nested structures
- **Memory exhaustion**: Oversized elements or attributes
- **Directory traversal**: Path-based security vulnerabilities
