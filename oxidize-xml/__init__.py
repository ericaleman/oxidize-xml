"""oxidize-xml: High-performance XML to JSON streaming parser built with Rust."""

try:
    from .oxidize_xml import (
        parse_xml_file_to_json_file,
        parse_xml_file_to_json_string,
        parse_xml_string_to_json_file,
        parse_xml_string_to_json_string,
    )
    __all__ = [
        "parse_xml_file_to_json_file",
        "parse_xml_file_to_json_string", 
        "parse_xml_string_to_json_file",
        "parse_xml_string_to_json_string",
    ]
except ImportError:
    # Module not yet built
    __all__ = []

__version__ = "0.1.0"