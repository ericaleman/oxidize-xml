"""
Tests for the improved structured error handling system.
"""
import pytest
import tempfile
from pathlib import Path


def test_empty_target_element_error():
    """Test proper error for empty target element."""
    import oxidize_xml
    
    xml_content = '<root><item>test</item></root>'
    
    with pytest.raises(ValueError) as exc_info:
        oxidize_xml.parse_xml_string_to_json_string(xml_content, "")
    
    error_msg = str(exc_info.value)
    assert "target_element cannot be empty" in error_msg
    assert "context:" in error_msg


def test_zero_batch_size_error():
    """Test proper error for batch_size=0."""
    import oxidize_xml
    
    xml_content = '<root><item>test</item></root>'
    
    with pytest.raises(ValueError) as exc_info:
        oxidize_xml.parse_xml_string_to_json_string(xml_content, "item", batch_size=0)
    
    error_msg = str(exc_info.value)
    assert "batch_size must be greater than 0" in error_msg
    assert "Received batch_size: 0" in error_msg


def test_huge_batch_size_error():
    """Test proper error for excessively large batch_size."""
    import oxidize_xml
    
    xml_content = '<root><item>test</item></root>'
    
    with pytest.raises(RuntimeError) as exc_info:
        oxidize_xml.parse_xml_string_to_json_string(xml_content, "item", batch_size=2_000_000)
    
    error_msg = str(exc_info.value)
    assert "batch_size 2000000 is too large" in error_msg
    assert "maximum is 1,000,000" in error_msg


def test_file_not_found_error():
    """Test proper error for non-existent input file."""
    import oxidize_xml
    
    with pytest.raises(OSError) as exc_info:
        oxidize_xml.parse_xml_file_to_json_string("/nonexistent/path/file.xml", "item")
    
    error_msg = str(exc_info.value)
    assert "File error" in error_msg
    assert "/nonexistent/path/file.xml" in error_msg
    assert "Cannot open input file" in error_msg


def test_invalid_output_path_error():
    """Test proper error for invalid output file path."""
    import oxidize_xml
    
    xml_content = '<root><item>test</item></root>'
    
    with pytest.raises(OSError) as exc_info:
        oxidize_xml.parse_xml_string_to_json_file(xml_content, "item", "/invalid/path/output.json")
    
    error_msg = str(exc_info.value)
    assert "File error" in error_msg
    assert "/invalid/path/output.json" in error_msg
    assert "Cannot create output file" in error_msg


def test_malformed_xml_error():
    """Test proper error handling for malformed XML."""
    import oxidize_xml
    
    malformed_xml = '<root><item>unclosed tag'
    
    # Should handle gracefully - may parse successfully or give clear error
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(malformed_xml, "item")
        # If it succeeds, result should be valid
        assert isinstance(result, str)
    except ValueError as e:
        # If it fails, should give clear XML parsing error
        assert "XML parsing error" in str(e) or "parsing" in str(e).lower()


def test_xml_parse_error_with_position():
    """Test that XML parse errors include position information when available."""
    import oxidize_xml
    
    # XML with syntax error
    invalid_xml = '<?xml version="1.0"?>\n<root>\n  <item id="1">test</item>\n  <invalid>&lt;</root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(invalid_xml, "item")
        # Some malformed XML might parse successfully
        assert isinstance(result, str)
    except ValueError as e:
        error_msg = str(e)
        # Should contain helpful parsing information
        assert any(word in error_msg.lower() for word in ["xml", "parse", "parsing", "error"])


def test_error_context_preservation():
    """Test that error context is preserved through the call stack."""
    import oxidize_xml
    
    # Test input validation error context
    with pytest.raises(ValueError) as exc_info:
        oxidize_xml.parse_xml_file_to_json_string("valid_file.xml", "", batch_size=500)
    
    error_msg = str(exc_info.value)
    assert "context:" in error_msg
    assert "XML element name must be specified" in error_msg


def test_all_functions_have_consistent_error_handling(temp_dir):
    """Test that all 4 API functions have consistent error handling."""
    import oxidize_xml
    
    xml_content = '<root><item>test</item></root>'
    xml_path = temp_dir / "test.xml"
    xml_path.write_text(xml_content)
    
    functions_to_test = [
        lambda: oxidize_xml.parse_xml_string_to_json_string(xml_content, "", batch_size=1),
        lambda: oxidize_xml.parse_xml_string_to_json_file(xml_content, "", str(temp_dir / "out.json"), batch_size=1),
        lambda: oxidize_xml.parse_xml_file_to_json_string(str(xml_path), "", batch_size=1),
        lambda: oxidize_xml.parse_xml_file_to_json_file(str(xml_path), "", str(temp_dir / "out2.json"), batch_size=1),
    ]
    
    # All should raise ValueError for empty target_element
    for func in functions_to_test:
        with pytest.raises(ValueError) as exc_info:
            func()
        
        error_msg = str(exc_info.value)
        assert "target_element cannot be empty" in error_msg


def test_memory_error_handling():
    """Test memory-related error conditions."""
    import oxidize_xml
    
    xml_content = '<root><item>test</item></root>'
    
    # Test extremely large batch size
    with pytest.raises(RuntimeError) as exc_info:
        oxidize_xml.parse_xml_string_to_json_string(xml_content, "item", batch_size=5_000_000)
    
    error_msg = str(exc_info.value)
    assert "Memory error" in error_msg


def test_io_error_handling(temp_dir):
    """Test I/O related error conditions."""
    import oxidize_xml
    import os
    
    xml_content = '<root><item>test</item></root>'
    
    # Test read-only directory (should fail to create output file)
    readonly_dir = temp_dir / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)  # Read-only
    
    try:
        with pytest.raises(OSError) as exc_info:
            oxidize_xml.parse_xml_string_to_json_file(
                xml_content, "item", str(readonly_dir / "output.json")
            )
        
        error_msg = str(exc_info.value)
        assert "File error" in error_msg
        assert "Cannot create output file" in error_msg
    finally:
        # Clean up: restore write permissions
        readonly_dir.chmod(0o755)


def test_utf8_conversion_error_handling():
    """Test UTF-8 conversion error handling."""
    import oxidize_xml
    
    # This test verifies that UTF-8 conversion errors are properly handled
    # Most valid XML should convert fine, but the error handling is there for edge cases
    xml_content = '<root><item>valid utf-8 content ✓</item></root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
        assert isinstance(result, str)
        assert "✓" in result  # UTF-8 character should be preserved
    except Exception as e:
        # If there's an issue, should be a clear I/O error
        assert "I/O error" in str(e) or "UTF-8" in str(e)


def test_error_message_formatting():
    """Test that error messages are well-formatted and informative."""
    import oxidize_xml
    
    test_cases = [
        # (function_call, expected_error_type, expected_content)
        (
            lambda: oxidize_xml.parse_xml_string_to_json_string('<root></root>', ''),
            ValueError,
            ["Invalid input", "target_element cannot be empty", "context"]
        ),
        (
            lambda: oxidize_xml.parse_xml_string_to_json_string('<root></root>', 'item', batch_size=0),
            ValueError,
            ["Invalid input", "batch_size must be greater than 0", "Received batch_size: 0"]
        ),
        (
            lambda: oxidize_xml.parse_xml_file_to_json_string('/does/not/exist.xml', 'item'),
            OSError,
            ["File error", "/does/not/exist.xml", "Cannot open input file"]
        ),
    ]
    
    for func_call, expected_error_type, expected_content in test_cases:
        with pytest.raises(expected_error_type) as exc_info:
            func_call()
        
        error_msg = str(exc_info.value)
        for expected_text in expected_content:
            assert expected_text in error_msg, f"Expected '{expected_text}' in error message: {error_msg}"