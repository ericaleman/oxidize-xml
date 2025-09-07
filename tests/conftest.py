"""
Pytest configuration and fixtures for oxidize-xml tests.
"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_xml():
    """Simple XML content for basic tests."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <record id="1">
        <name>John Doe</name>
        <email>john@example.com</email>
        <status>active</status>
    </record>
    <record id="2">
        <name>Jane Smith</name>
        <email>jane@example.com</email>
        <status>inactive</status>
    </record>
</root>"""


@pytest.fixture
def complex_xml():
    """Complex XML with nested elements and attributes."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns:book="http://example.com/book">
    <book:item id="bk101" category="fiction" available="true">
        <author>
            <first>J.K.</first>
            <last>Rowling</last>
        </author>
        <title lang="en">Harry Potter</title>
        <price currency="USD">29.99</price>
        <description><![CDATA[A magical adventure story]]></description>
        <tags>
            <tag>fantasy</tag>
            <tag>adventure</tag>
        </tags>
    </book:item>
    <book:item id="bk102" category="non-fiction" available="false">
        <author>
            <first>Donald</first>
            <last>Knuth</last>
        </author>
        <title lang="en">The Art of Computer Programming</title>
        <price currency="USD">89.99</price>
        <description>Comprehensive computer science text</description>
        <tags>
            <tag>programming</tag>
            <tag>algorithms</tag>
        </tags>
    </book:item>
</catalog>"""


@pytest.fixture
def malformed_xml_samples():
    """Various malformed XML samples for error testing."""
    return {
        'unclosed_tag': '<root><item>content</root>',
        'invalid_chars': '<root><item>content & more</item></root>',
        'mismatched_tags': '<root><item>content</different></root>',
        'incomplete': '<root><item>',
        'empty_file': '',
        'only_whitespace': '   \n\t  ',
        'no_xml_declaration': '<root><item>test</item></root>',
        'invalid_encoding': '<?xml version="1.0" encoding="invalid"?><root><item>test</item></root>',
        'nested_cdata': '<root><item><![CDATA[Some <nested> content]]></item></root>',
    }


@pytest.fixture
def large_xml_generator():
    """Generator function to create large XML files for performance testing."""
    def generate_xml(num_records=1000, record_size='small'):
        """
        Generate XML with specified number of records.
        
        Args:
            num_records: Number of records to generate
            record_size: 'small', 'medium', or 'large'
        """
        if record_size == 'small':
            record_template = """    <record id="{id}">
        <name>User {id}</name>
        <email>user{id}@example.com</email>
    </record>"""
        elif record_size == 'medium':
            record_template = """    <record id="{id}" timestamp="2024-01-{day:02d}T10:00:00Z">
        <name>User {id}</name>
        <email>user{id}@example.com</email>
        <department>Engineering</department>
        <location>New York</location>
        <status>active</status>
        <metadata>
            <created>2024-01-01</created>
            <updated>2024-01-{day:02d}</updated>
        </metadata>
    </record>"""
        else:  # large
            record_template = """    <record id="{id}" timestamp="2024-01-{day:02d}T10:00:00Z" version="1.0">
        <personal>
            <name>User {id}</name>
            <email>user{id}@example.com</email>
            <phone>+1-555-{phone:04d}</phone>
        </personal>
        <professional>
            <department>Engineering</department>
            <title>Software Engineer</title>
            <location>New York</location>
            <salary currency="USD">75000</salary>
        </professional>
        <status>active</status>
        <permissions>
            <role>user</role>
            <access_level>2</access_level>
            <features>
                <feature name="api_access">true</feature>
                <feature name="admin_panel">false</feature>
            </features>
        </permissions>
        <metadata>
            <created>2024-01-01T00:00:00Z</created>
            <updated>2024-01-{day:02d}T10:00:00Z</updated>
            <notes>Auto-generated test user</notes>
        </metadata>
    </record>"""
        
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>\n<root>\n']
        
        for i in range(1, num_records + 1):
            day = (i % 28) + 1
            phone = i % 10000
            xml_parts.append(record_template.format(id=i, day=day, phone=phone))
            xml_parts.append('\n')
        
        xml_parts.append('</root>')
        return ''.join(xml_parts)
    
    return generate_xml


@pytest.fixture
def xml_file(temp_dir, sample_xml):
    """Create a temporary XML file with sample content."""
    xml_path = temp_dir / "test.xml"
    xml_path.write_text(sample_xml, encoding='utf-8')
    return xml_path


@pytest.fixture
def large_xml_file(temp_dir, large_xml_generator):
    """Create a large temporary XML file for performance testing."""
    xml_path = temp_dir / "large_test.xml"
    large_xml_content = large_xml_generator(num_records=10000, record_size='medium')
    xml_path.write_text(large_xml_content, encoding='utf-8')
    return xml_path