"""
Sample XML files and content for testing.
"""

# Small sample XMLs for basic testing
SIMPLE_BOOKS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<catalog>
    <book id="bk101">
        <author>J.K. Rowling</author>
        <title>Harry Potter and the Philosopher's Stone</title>
        <genre>Fantasy</genre>
        <price>29.99</price>
        <publish_date>2001-06-23</publish_date>
        <description>A young wizard's first year at Hogwarts.</description>
    </book>
    <book id="bk102">
        <author>George R.R. Martin</author>
        <title>A Game of Thrones</title>
        <genre>Fantasy</genre>
        <price>39.99</price>
        <publish_date>1996-08-01</publish_date>
        <description>Political intrigue in the Seven Kingdoms.</description>
    </book>
    <book id="bk103">
        <author>Isaac Asimov</author>
        <title>Foundation</title>
        <genre>Science Fiction</genre>
        <price>24.99</price>
        <publish_date>1951-05-01</publish_date>
        <description>The collapse and rebirth of a galactic empire.</description>
    </book>
</catalog>"""

API_RESPONSE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<response status="success">
    <record id="001" timestamp="2024-01-15T10:30:00Z">
        <user_id>12345</user_id>
        <action>login</action>
        <ip_address>192.168.1.100</ip_address>
        <user_agent>Mozilla/5.0</user_agent>
        <status>success</status>
    </record>
    <record id="002" timestamp="2024-01-15T10:31:15Z">
        <user_id>67890</user_id>
        <action>purchase</action>
        <ip_address>192.168.1.101</ip_address>
        <item_id>ABC123</item_id>
        <amount currency="USD">99.99</amount>
        <status>completed</status>
    </record>
    <record id="003" timestamp="2024-01-15T10:32:30Z">
        <user_id>12345</user_id>
        <action>logout</action>
        <ip_address>192.168.1.100</ip_address>
        <session_duration>120</session_duration>
        <status>success</status>
    </record>
</response>"""

NESTED_STRUCTURE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<company>
    <department name="Engineering">
        <employee id="emp001">
            <personal>
                <first_name>John</first_name>
                <last_name>Doe</last_name>
                <email>john.doe@company.com</email>
            </personal>
            <professional>
                <title>Senior Developer</title>
                <salary currency="USD">95000</salary>
                <start_date>2020-03-15</start_date>
            </professional>
            <skills>
                <skill level="expert">Python</skill>
                <skill level="advanced">JavaScript</skill>
                <skill level="intermediate">Rust</skill>
            </skills>
        </employee>
        <employee id="emp002">
            <personal>
                <first_name>Jane</first_name>
                <last_name>Smith</last_name>
                <email>jane.smith@company.com</email>
            </personal>
            <professional>
                <title>DevOps Engineer</title>
                <salary currency="USD">105000</salary>
                <start_date>2019-08-01</start_date>
            </professional>
            <skills>
                <skill level="expert">Docker</skill>
                <skill level="expert">Kubernetes</skill>
                <skill level="advanced">AWS</skill>
            </skills>
        </employee>
    </department>
</company>"""

MIXED_CONTENT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<document>
    <article id="art001">
        <title>Mixed Content Example</title>
        <content>
            This is a paragraph with <emphasis>emphasized text</emphasis> and
            <link href="http://example.com">a link</link> in the middle.
            <br/>
            This is another line with <code>inline code</code> elements.
        </content>
        <metadata>
            <author>Content Writer</author>
            <created>2024-01-15</created>
            <tags>
                <tag>example</tag>
                <tag>mixed-content</tag>
                <tag>xml</tag>
            </tags>
        </metadata>
    </article>
</document>"""

NAMESPACE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:book="http://example.com/book" 
      xmlns:author="http://example.com/author">
    <book:catalog>
        <book:item id="1" category="fiction">
            <book:title lang="en">The Great Novel</book:title>
            <author:info>
                <author:name>Famous Writer</author:name>
                <author:birth_year>1970</author:birth_year>
            </author:info>
            <book:price currency="USD">29.99</book:price>
        </book:item>
        <book:item id="2" category="science">
            <book:title lang="en">Scientific Discovery</book:title>
            <author:info>
                <author:name>Research Scientist</author:name>
                <author:birth_year>1965</author:birth_year>
            </author:info>
            <book:price currency="EUR">35.50</book:price>
        </book:item>
    </book:catalog>
</root>"""

CDATA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<documents>
    <document id="doc001">
        <title>Document with CDATA</title>
        <content><![CDATA[
            This is CDATA content that can contain <tags> and & symbols
            without XML parsing issues. It can span multiple lines
            and include "quotes" and 'apostrophes' freely.
            
            Even HTML-like content: <div class="example">Hello</div>
        ]]></content>
        <html_snippet><![CDATA[<p>HTML paragraph</p>]]></html_snippet>
    </document>
    <document id="doc002">
        <title>Another Document</title>
        <content><![CDATA[More CDATA content here]]></content>
        <code_example><![CDATA[
            function example() {
                return "Hello, World!";
            }
        ]]></code_example>
    </document>
</documents>"""

SELF_CLOSING_XML = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <server id="web01" type="apache" enabled="true"/>
    <server id="web02" type="nginx" enabled="false"/>
    <database id="db01" type="postgresql" port="5432"/>
    <cache id="redis01" type="redis" port="6379"/>
    <service name="api" version="1.2.3" status="running">
        <endpoint path="/health" method="GET"/>
        <endpoint path="/users" method="POST"/>
        <setting key="timeout" value="30"/>
        <setting key="retries" value="3"/>
    </service>
</configuration>"""

UNICODE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<international>
    <greeting lang="en">Hello World</greeting>
    <greeting lang="es">Hola Mundo</greeting>
    <greeting lang="fr">Bonjour le Monde</greeting>
    <greeting lang="de">Hallo Welt</greeting>
    <greeting lang="ja">こんにちは世界</greeting>
    <greeting lang="zh">你好世界</greeting>
    <greeting lang="ru">Привет мир</greeting>
    <greeting lang="ar">مرحبا بالعالم</greeting>
    <greeting lang="hi">हैलो वर्ल्ड</greeting>
    <emoji>🌍 🌎 🌏 👋 🎉 ✨</emoji>
</international>"""

MALFORMED_SAMPLES = {
    'unclosed_root': '<root><item>content',
    'mismatched_tags': '<root><item>content</different></root>',
    'invalid_chars': '<root><item>AT&T Corporation</item></root>',
    'nested_quotes': '<root><item attr="value with "nested" quotes">content</item></root>',
    'incomplete_tag': '<root><item attr="value"',
    'malformed_comment': '<root><!--- Invalid comment --><item>content</item></root>',
    'invalid_cdata': '<root><item><![CDATA[Unclosed CDATA</item></root>',
}

def get_sample_xml(name):
    """Get a sample XML by name."""
    samples = {
        'simple_books': SIMPLE_BOOKS_XML,
        'api_response': API_RESPONSE_XML,
        'nested_structure': NESTED_STRUCTURE_XML,
        'mixed_content': MIXED_CONTENT_XML,
        'namespace': NAMESPACE_XML,
        'cdata': CDATA_XML,
        'self_closing': SELF_CLOSING_XML,
        'unicode': UNICODE_XML,
    }
    return samples.get(name)

def get_malformed_xml(name):
    """Get a malformed XML sample by name."""
    return MALFORMED_SAMPLES.get(name)