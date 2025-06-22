import unittest
import sys
import os

# Add parent directory to sys.path to allow imports from markdown_enhancer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from markdown_enhancer import EnhancedMarkdownConverter

class TestBasicConversion(unittest.TestCase):
    def setUp(self):
        self.converter = EnhancedMarkdownConverter()

    def test_simple_paragraph(self):
        html = '<p>Hello world</p>'
        expected_md = 'Hello world\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_basic_formatting(self):
        html = '<p>This is <strong>bold</strong> and <em>italic</em> text.</p>'
        expected_md = 'This is **bold** and *italic* text.\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_attribute_stripping(self):
        html = '<p style="color: blue;" class="important">Content with attributes</p><a href="https://example.com" class="link-style">Link</a>'
        # Expected: attributes like style and class (on p) are stripped, href is preserved on a
        expected_md = 'Content with attributes\n\n[Link](https://example.com)'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_tag_removal(self):
        html = "<p>Visible text</p><script>alert('invisible');</script><style>.hide {display:none;}</style>"
        expected_md = "Visible text\n\n"
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_tag_unwrapping(self):
        html = "<p>Text <span>inside span</span> and <div>inside div</div></p>"
        # Spans and divs should be unwrapped, their content merged with parent.
        # The current converter._convert_node for NavigableString uses re.sub(r'\s+', ' ', text).strip()
        # This might lead to "Text inside span and inside div" if spaces are not handled carefully
        # between unwrapped elements. Let's assume a simple concatenation for now.
        # The preprocessing step in EnhancedMarkdownConverter first removes script/style, then unwraps, then cleans attributes.
        # The convert method gets the string representation of the children.
        expected_md = "Text inside span and inside div\n\n"
        # Need to be careful about how spaces are handled by `get_text()` or by string joining in `_convert_node`
        # For now, let's test the expected output based on current implementation.
        # A more robust solution might involve adding spaces when unwrapping if necessary.
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())


    def test_headings(self):
        html = '<h1>Title 1</h1><h2>Title 2</h2>'
        expected_md = '# Title 1\n\n## Title 2\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_unordered_list(self):
        html = '<ul><li>Item 1</li><li>Item 2</li></ul>'
        # Current output adds extra newlines due to how li content might be processed.
        # Let's adjust expected to match likely current output or refine converter later.
        # The list items themselves will have their content processed, which might add \n\n if they contain <p>
        # For simple text li, it should be cleaner.
        expected_md = '* Item 1\n* Item 2\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_ordered_list(self):
        html = '<ol><li>First</li><li>Second</li></ol>'
        expected_md = '1. First\n2. Second\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_links(self):
        html = '<a href="http://example.com">Example Link</a>'
        expected_md = '[Example Link](http://example.com)'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_image(self):
        html = '<img src="image.jpg" alt="Sample Image" style="width:100px;">'
        expected_md = '![Sample Image](image.jpg)'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_line_break(self):
        html = '<p>Line one<br>Line two</p>'
        # Markdown for <br> can be two spaces at the end of the line or a literal newline.
        # Current converter returns '\n' for <br>.
        expected_md = 'Line one\nLine two\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_blockquote(self):
        html = '<blockquote>This is a quote.</blockquote>'
        expected_md = '> This is a quote.\n\n' # Current converter might add extra \n
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_inline_code(self):
        html = '<p>Use <code>myVar</code> variable.</p>'
        expected_md = 'Use `myVar` variable.\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_code_block_with_language(self):
        html = '<pre><code class="language-python">def hello():\n  print("world")</code></pre>'
        expected_md = '```python\ndef hello():\n  print("world")\n```\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_code_block_no_language(self):
        html = '<pre><code>def test():\n  return 1</code></pre>'
        expected_md = '```\ndef test():\n  return 1\n```\n\n'
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

    def test_empty_tags_handling(self):
        html = "<p></p><ul><li></li></ul>"
        # Expected: empty paragraphs might become just newlines, empty list items might be omitted.
        # Current converter for <p> returns content + '\n\n'. If content is empty, it's '\n\n'.
        # Current ul/ol filters out empty items.
        expected_md = '\n\n\n\n' # Two newlines from <p>, then two from <ul> (as it's empty after filtering)
        self.assertEqual(self.converter.convert(html).strip(), expected_md.strip())

if __name__ == '__main__':
    unittest.main()
