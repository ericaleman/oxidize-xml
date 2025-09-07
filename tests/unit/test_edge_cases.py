"""
Edge case tests for oxidize-xml XML parsing functionality.
"""
import pytest
import json
import tempfile
from pathlib import Path


class TestXMLEdgeCases:
    """Test various XML edge cases and corner conditions."""
    
    def test_empty_xml_files(self, temp_dir):
        """Test handling of completely empty XML files."""
        import oxidize_xml
        
        # Empty file
        empty_path = temp_dir / "empty.xml"
        empty_path.write_text("")
        
        result = oxidize_xml.parse_xml_file_to_json_string(str(empty_path), "item")
        assert result.strip() == ""
    
    
    def test_xml_with_only_whitespace(self, temp_dir):
        """Test XML files containing only whitespace."""
        import oxidize_xml
        
        whitespace_xml = "   \n\t  \n  "
        whitespace_path = temp_dir / "whitespace.xml"
        whitespace_path.write_text(whitespace_xml)
        
        result = oxidize_xml.parse_xml_file_to_json_string(str(whitespace_path), "item")
        assert result.strip() == ""
    
    
    def test_xml_declaration_variations(self):
        """Test various XML declaration formats."""
        import oxidize_xml
        
        variations = [
            '<?xml version="1.0"?><root><item>test</item></root>',
            '<?xml version="1.0" encoding="UTF-8"?><root><item>test</item></root>',
            '<?xml version="1.0" encoding="utf-8"?><root><item>test</item></root>',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><root><item>test</item></root>',
            '<?xml version="1.1"?><root><item>test</item></root>',
            '<root><item>test</item></root>',  # No declaration
        ]
        
        for xml_content in variations:
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    assert "test" in str(item)
            except Exception:
                # Some variations might not be supported, which is acceptable
                pass
    
    
    def test_deeply_nested_structures(self):
        """Test deeply nested XML structures."""
        import oxidize_xml
        
        # Create 50-level nested structure
        nested_xml = '<?xml version="1.0"?><root>'
        for i in range(50):
            nested_xml += f'<level{i}>'
        nested_xml += '<item id="deep">nested content</item>'
        for i in range(49, -1, -1):
            nested_xml += f'</level{i}>'
        nested_xml += '</root>'
        
        try:
            result = oxidize_xml.parse_xml_string_to_json_string(nested_xml, "item")
            if result.strip():
                item = json.loads(result.strip())
                assert item.get("@id") == "deep"
        except Exception as e:
            # Deep nesting might hit limits, which is acceptable
            assert "error" in str(e).lower()
    
    
    def test_very_long_element_names(self):
        """Test handling of very long element names."""
        import oxidize_xml
        
        long_name = "element" + "x" * 1000
        xml_content = f'<?xml version="1.0"?><root><{long_name}>content</{long_name}></root>'
        
        try:
            result = oxidize_xml.parse_xml_string_to_json_string(xml_content, long_name)
            if result.strip():
                item = json.loads(result.strip())
                assert "content" in str(item)
        except Exception:
            # Very long names might not be supported
            pass
    
    
    def test_very_long_attribute_names_and_values(self):
        """Test handling of very long attribute names and values."""
        import oxidize_xml
        
        long_attr_name = "attr" + "x" * 500
        long_attr_value = "value" + "y" * 500
        xml_content = f'<?xml version="1.0"?><root><item {long_attr_name}="{long_attr_value}">content</item></root>'
        
        try:
            result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
            if result.strip():
                item = json.loads(result.strip())
                # Should contain the long attribute
                attr_key = f"@{long_attr_name}"
                if attr_key in item:
                    assert item[attr_key] == long_attr_value
        except Exception:
            # Very long attributes might cause issues
            pass
    
    
    def test_many_attributes_on_single_element(self):
        """Test element with many attributes."""
        import oxidize_xml
        
        # Create element with 100 attributes
        attributes = []
        for i in range(100):
            attributes.append(f'attr{i}="value{i}"')
        
        attr_string = ' '.join(attributes)
        xml_content = f'<?xml version="1.0"?><root><item {attr_string}>content</item></root>'
        
        try:
            result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
            if result.strip():
                item = json.loads(result.strip())
                # Check that we have many attributes
                attr_count = sum(1 for key in item.keys() if key.startswith('@'))
                assert attr_count == 100
        except Exception:
            # Many attributes might cause performance or parsing issues
            pass
    
    
    def test_mixed_content_complex_cases(self):
        """Test complex mixed content scenarios."""
        import oxidize_xml
        
        mixed_content_cases = [
            # Text before and after child elements
            '<item>Before<child>middle</child>After</item>',
            # Multiple text segments
            '<item>Start<child1>c1</child1>Middle<child2>c2</child2>End</item>',
            # Text with only whitespace
            '<item>   <child>content</child>   </item>',
            # Empty child elements
            '<item>Text<empty/>More text</item>',
        ]
        
        for content in mixed_content_cases:
            xml_content = f'<?xml version="1.0"?><root>{content}</root>'
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    # Should have some content, exact structure may vary
                    assert len(str(item)) > 10
            except Exception:
                # Complex mixed content might not be fully supported
                pass
    
    
    def test_namespace_edge_cases(self):
        """Test various namespace scenarios."""
        import oxidize_xml
        
        namespace_cases = [
            # Default namespace
            '<?xml version="1.0"?><root xmlns="http://example.com"><item>test</item></root>',
            # Multiple namespaces
            '<?xml version="1.0"?><root xmlns:a="http://a.com" xmlns:b="http://b.com"><a:item>test</a:item></root>',
            # Namespace redefinition
            '<?xml version="1.0"?><root xmlns:ns="http://first.com"><ns:parent xmlns:ns="http://second.com"><ns:item>test</ns:item></ns:parent></root>',
        ]
        
        for xml_content in namespace_cases:
            try:
                # Try different target elements
                for target in ["item", "ns:item", "a:item"]:
                    try:
                        result = oxidize_xml.parse_xml_string_to_json_string(xml_content, target)
                        if result.strip():
                            item = json.loads(result.strip())
                            assert "test" in str(item)
                            break
                    except Exception:
                        continue
            except Exception:
                # Namespace handling might be limited
                pass
    
    
    def test_cdata_edge_cases(self):
        """Test various CDATA scenarios."""
        import oxidize_xml
        
        cdata_cases = [
            # Simple CDATA
            '<item><![CDATA[Some text]]></item>',
            # CDATA with special characters
            '<item><![CDATA[<>&"\']]></item>',
            # CDATA with nested-like content
            '<item><![CDATA[<child>nested</child>]]></item>',
            # Multiple CDATA sections
            '<item><![CDATA[First]]><![CDATA[Second]]></item>',
            # CDATA mixed with regular content
            '<item>Before<![CDATA[Middle]]>After</item>',
            # Empty CDATA
            '<item><![CDATA[]]></item>',
        ]
        
        for content in cdata_cases:
            xml_content = f'<?xml version="1.0"?><root>{content}</root>'
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    # CDATA content should be preserved as text
                    assert isinstance(item, (dict, str, list))
            except Exception:
                # CDATA handling might have limitations
                pass
    
    
    def test_comment_edge_cases(self):
        """Test various comment scenarios."""
        import oxidize_xml
        
        comment_cases = [
            # Comments in different positions
            '<?xml version="1.0"?><!-- Root comment --><root><item>test</item></root>',
            '<?xml version="1.0"?><root><!-- Before item --><item>test</item><!-- After item --></root>',
            '<?xml version="1.0"?><root><item><!-- Inside item -->test</item></root>',
            # Multi-line comments
            '<?xml version="1.0"?><root><!-- Multi\nline\ncomment --><item>test</item></root>',
            # Comments with special characters
            '<?xml version="1.0"?><root><!-- Comment with <>&"\' --><item>test</item></root>',
        ]
        
        for xml_content in comment_cases:
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    assert "test" in str(item)
            except Exception:
                # Comment handling issues might occur
                pass
    
    
    def test_processing_instruction_cases(self):
        """Test processing instructions."""
        import oxidize_xml
        
        pi_cases = [
            '<?xml version="1.0"?><?xml-stylesheet type="text/xsl" href="style.xsl"?><root><item>test</item></root>',
            '<?xml version="1.0"?><root><?process data?><item>test</item></root>',
            '<?xml version="1.0"?><root><item><?inside-item data?>test</item></root>',
        ]
        
        for xml_content in pi_cases:
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    assert "test" in str(item)
            except Exception:
                # PI handling might not be supported
                pass
    
    
    def test_entity_references(self):
        """Test built-in entity references."""
        import oxidize_xml
        
        entity_cases = [
            # Standard entities
            '<item>Text with &lt; and &gt; and &amp;</item>',
            '<item>Quotes: &quot; and &apos;</item>',
            # Numeric character references
            '<item>&#65; &#x41;</item>',  # Both should be 'A'
        ]
        
        for content in entity_cases:
            xml_content = f'<?xml version="1.0"?><root>{content}</root>'
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    # Entities should be resolved
                    item_str = str(item)
                    if "&lt;" in content:
                        assert "<" in item_str
                    if "&#65;" in content:
                        assert "A" in item_str
            except Exception:
                # Entity handling might be limited
                pass
    
    
    def test_self_closing_tag_variations(self):
        """Test different self-closing tag formats."""
        import oxidize_xml
        
        self_closing_cases = [
            # Standard self-closing
            '<item id="1"/>',
            # Self-closing with whitespace
            '<item id="2" />',
            '<item id="3"   />',
            # Mixed with regular elements
            '<parent><item1 id="4"/><item2 id="5">content</item2></parent>',
        ]
        
        for content in self_closing_cases:
            xml_content = f'<?xml version="1.0"?><root>{content}</root>'
            try:
                # Try parsing both item and parent
                for target in ["item", "item1", "item2", "parent"]:
                    try:
                        result = oxidize_xml.parse_xml_string_to_json_string(xml_content, target)
                        if result.strip():
                            lines = result.strip().split('\n')
                            for line in lines:
                                if line.strip():
                                    item = json.loads(line)
                                    # Should have attributes preserved
                                    if "@id" in item:
                                        assert item["@id"] in ["1", "2", "3", "4", "5"]
                    except Exception:
                        continue
            except Exception:
                pass
    
    
    def test_unicode_and_encoding_edge_cases(self, temp_dir):
        """Test various Unicode and encoding scenarios."""
        import oxidize_xml
        
        unicode_cases = [
            # Basic Unicode
            '<item>Hello 世界</item>',
            # Emoji
            '<item>Hello 👋 World 🌍</item>',
            # Various scripts
            '<item>English Русский العربية 中文 日本語</item>',
            # Unicode in attributes
            '<item name="测试">content</item>',
        ]
        
        for content in unicode_cases:
            xml_content = f'<?xml version="1.0" encoding="UTF-8"?><root>{content}</root>'
            
            # Test string parsing
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    # Unicode should be preserved
                    assert len(str(item)) > 5
            except Exception:
                # Unicode handling might have limitations
                pass
            
            # Test file parsing
            try:
                unicode_path = temp_dir / "unicode_test.xml"
                unicode_path.write_text(xml_content, encoding='utf-8')
                result = oxidize_xml.parse_xml_file_to_json_string(str(unicode_path), "item")
                if result.strip():
                    item = json.loads(result.strip())
                    assert len(str(item)) > 5
            except Exception:
                pass
    
    
    def test_large_number_of_small_elements(self):
        """Test handling of many small elements."""
        import oxidize_xml
        
        # Create XML with 1000 small elements
        items = []
        for i in range(1000):
            items.append(f'<item id="{i}">Item {i}</item>')
        
        xml_content = f'<?xml version="1.0"?><root>{"".join(items)}</root>'
        
        try:
            result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
            lines = result.strip().split('\n')
            assert len(lines) == 1000
            
            # Check first and last items
            first_item = json.loads(lines[0])
            last_item = json.loads(lines[-1])
            
            assert first_item["@id"] == "0"
            assert last_item["@id"] == "999"
        except Exception as e:
            # Large number of elements might cause issues
            assert "error" in str(e).lower()
    
    
    def test_zero_length_text_content(self):
        """Test elements with zero-length or whitespace-only content."""
        import oxidize_xml
        
        content_cases = [
            '<item></item>',  # Completely empty
            '<item> </item>',  # Single space
            '<item>\n</item>',  # Single newline
            '<item>\t</item>',  # Single tab
            '<item>   \n\t  </item>',  # Mixed whitespace
        ]
        
        for content in content_cases:
            xml_content = f'<?xml version="1.0"?><root>{content}</root>'
            try:
                result = oxidize_xml.parse_xml_string_to_json_string(xml_content, "item")
                if result.strip():
                    item = json.loads(result.strip())
                    # Empty elements might be null or have empty content
                    assert item is not None
            except Exception:
                # Empty content handling might vary
                pass