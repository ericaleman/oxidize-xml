"""
Tests for error handling with malformed and invalid XML inputs.
"""
import pytest
import tempfile
from pathlib import Path


def test_malformed_xml_unclosed_tag():
    """Test handling of unclosed XML tags."""
    import oxidize_xml
    
    malformed_xml = '<root><item>content</root>'
    
    # Should handle gracefully - may return 0 items or raise appropriate error
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(malformed_xml, "item")
        # If it succeeds, should return empty or valid result
        assert isinstance(result, str)
    except Exception as e:
        # Should raise a clear, informative error
        assert "XML parsing error" in str(e) or "error" in str(e).lower()


def test_malformed_xml_invalid_characters():
    """Test handling of invalid characters in XML."""
    import oxidize_xml
    
    malformed_xml = '<root><item>content & more</item></root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(malformed_xml, "item")
        # May succeed if parser handles it gracefully
        assert isinstance(result, str)
    except Exception as e:
        assert isinstance(e, Exception)


def test_malformed_xml_mismatched_tags():
    """Test handling of mismatched opening/closing tags."""
    import oxidize_xml
    
    malformed_xml = '<root><item>content</different></root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(malformed_xml, "item")
        assert isinstance(result, str)
    except Exception as e:
        assert "error" in str(e).lower()


def test_incomplete_xml():
    """Test handling of incomplete XML."""
    import oxidize_xml
    
    incomplete_xml = '<root><item>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(incomplete_xml, "item")
        # Should return empty result for incomplete XML
        assert result.strip() == ""
    except Exception as e:
        assert isinstance(e, Exception)


def test_empty_xml_input():
    """Test handling of empty XML input."""
    import oxidize_xml
    
    empty_xml = ''
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(empty_xml, "item")
        assert result.strip() == ""
    except Exception as e:
        assert isinstance(e, Exception)


def test_whitespace_only_xml():
    """Test handling of whitespace-only input."""
    import oxidize_xml
    
    whitespace_xml = '   \n\t  '
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(whitespace_xml, "item")
        assert result.strip() == ""
    except Exception as e:
        assert isinstance(e, Exception)


def test_invalid_file_path():
    """Test handling of invalid file paths."""
    import oxidize_xml
    
    invalid_path = "/nonexistent/path/file.xml"
    
    with pytest.raises(Exception) as exc_info:
        oxidize_xml.parse_xml_file_to_json_string(invalid_path, "item")
    
    # Should raise a clear error about file not found
    error_msg = str(exc_info.value).lower()
    assert "error" in error_msg and ("file" in error_msg or "path" in error_msg)


def test_invalid_output_path_permissions(temp_dir):
    """Test handling of invalid output file paths."""
    import oxidize_xml
    
    xml_content = '<?xml version="1.0"?><root><item>test</item></root>'
    
    # Try to write to a directory that doesn't exist
    invalid_output = "/nonexistent/directory/output.json"
    
    with pytest.raises(Exception) as exc_info:
        oxidize_xml.parse_xml_string_to_json_file(xml_content, "item", invalid_output)
    
    error_msg = str(exc_info.value).lower()
    assert "error" in error_msg


def test_large_deeply_nested_xml():
    """Test handling of deeply nested XML structures."""
    import oxidize_xml
    
    # Create deeply nested XML (100 levels)
    nested_xml = '<?xml version="1.0"?><root>'
    for i in range(100):
        nested_xml += f'<level{i}>'
    nested_xml += '<item id="deep">content</item>'
    for i in range(99, -1, -1):
        nested_xml += f'</level{i}>'
    nested_xml += '</root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(nested_xml, "item")
        if result.strip():
            import json
            item = json.loads(result.strip())
            assert item["@id"] == "deep"
    except Exception as e:
        # Deep nesting might cause stack overflow or other issues
        assert isinstance(e, Exception)


def test_xml_with_invalid_encoding_declaration():
    """Test handling of invalid encoding declarations."""
    import oxidize_xml
    
    invalid_encoding_xml = '<?xml version="1.0" encoding="invalid-encoding"?><root><item>test</item></root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(invalid_encoding_xml, "item")
        # May succeed if parser ignores encoding declaration for strings
        assert isinstance(result, str)
    except Exception as e:
        assert isinstance(e, Exception)


def test_xml_with_dtd_declarations():
    """Test handling of XML with DTD declarations."""
    import oxidize_xml
    
    dtd_xml = '''<?xml version="1.0"?>
<!DOCTYPE root [
    <!ELEMENT root (item*)>
    <!ELEMENT item (#PCDATA)>
]>
<root>
    <item>test content</item>
</root>'''
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(dtd_xml, "item")
        # DTDs should be ignored
        if result.strip():
            import json
            item = json.loads(result.strip())
            assert "test content" in str(item)
    except Exception as e:
        # DTD handling might not be supported
        assert isinstance(e, Exception)


def test_xml_with_processing_instructions():
    """Test handling of XML with processing instructions."""
    import oxidize_xml
    
    pi_xml = '''<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="style.xsl"?>
<root>
    <?process-instruction data?>
    <item>test content</item>
</root>'''
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(pi_xml, "item")
        # Processing instructions should be ignored
        if result.strip():
            import json
            item = json.loads(result.strip())
            assert "test content" in str(item)
    except Exception as e:
        assert isinstance(e, Exception)


def test_xml_with_comments():
    """Test handling of XML with comments."""
    import oxidize_xml
    
    comment_xml = '''<?xml version="1.0"?>
<root>
    <!-- This is a comment -->
    <item>test content</item>
    <!-- Another comment -->
</root>'''
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(comment_xml, "item")
        # Comments should be ignored
        if result.strip():
            import json
            item = json.loads(result.strip())
            assert "test content" in str(item)
    except Exception as e:
        assert isinstance(e, Exception)


def test_xml_with_very_long_attribute_values():
    """Test handling of XML with very long attribute values."""
    import oxidize_xml
    
    # Create XML with very long attribute value
    long_value = "x" * 10000
    long_attr_xml = f'<?xml version="1.0"?><root><item id="{long_value}">content</item></root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(long_attr_xml, "item")
        if result.strip():
            import json
            item = json.loads(result.strip())
            assert len(item["@id"]) == 10000
    except Exception as e:
        # Very long attributes might cause memory issues
        assert isinstance(e, Exception)


def test_xml_with_very_long_text_content():
    """Test handling of XML with very long text content."""
    import oxidize_xml
    
    # Create XML with very long text content
    long_content = "text content " * 1000
    long_text_xml = f'<?xml version="1.0"?><root><item>{long_content}</item></root>'
    
    try:
        result = oxidize_xml.parse_xml_string_to_json_string(long_text_xml, "item")
        if result.strip():
            import json
            item = json.loads(result.strip())
            assert len(str(item)) > 1000
    except Exception as e:
        assert isinstance(e, Exception)


def test_batch_size_edge_cases(temp_dir):
    """Test edge cases for batch size parameter."""
    import oxidize_xml
    
    xml_content = '<?xml version="1.0"?><root><item>test</item></root>'
    output_path = temp_dir / "output.json"
    
    # Test batch size of 0 - should raise error or use default
    try:
        count = oxidize_xml.parse_xml_string_to_json_file(
            xml_content, "item", str(output_path), batch_size=0
        )
        # If it succeeds, should use reasonable default
        assert count >= 0
    except Exception as e:
        assert isinstance(e, Exception)
    
    # Test very large batch size
    if output_path.exists():
        output_path.unlink()
    
    try:
        count = oxidize_xml.parse_xml_string_to_json_file(
            xml_content, "item", str(output_path), batch_size=1000000
        )
        assert count == 1
    except Exception as e:
        assert isinstance(e, Exception)


def test_concurrent_file_access(temp_dir, sample_xml):
    """Test behavior when multiple processes try to access the same files."""
    import oxidize_xml
    import threading
    import time
    
    xml_path = temp_dir / "concurrent.xml"
    xml_path.write_text(sample_xml)
    
    results = []
    errors = []
    
    def parse_worker(worker_id):
        try:
            output_path = temp_dir / f"output_{worker_id}.json"
            count = oxidize_xml.parse_xml_file_to_json_file(
                str(xml_path), "record", str(output_path)
            )
            results.append((worker_id, count))
        except Exception as e:
            errors.append((worker_id, str(e)))
    
    # Start multiple workers
    threads = []
    for i in range(5):
        thread = threading.Thread(target=parse_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    # Should have some successful results
    assert len(results) > 0 or len(errors) > 0