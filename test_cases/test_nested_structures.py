import unittest
import sys
import os

# Add parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from markdown_enhancer import EnhancedMarkdownConverter

class TestNestedStructures(unittest.TestCase):
    def setUp(self):
        self.converter = EnhancedMarkdownConverter()
        # For cleaner test comparison, remove trailing newlines from converter output
        # and expected outputs. Actual converter produces trailing \n\n for block elements.
        self.original_convert = self.converter.convert
        self.converter.convert = lambda html: self.original_convert(html).strip()


    def tearDown(self):
        # Restore original convert method
        self.converter.convert = self.original_convert

    def test_nested_unordered_lists(self):
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2
                <ul>
                    <li>Item 2.1</li>
                    <li>Item 2.2
                        <ul>
                            <li>Item 2.2.1</li>
                        </ul>
                    </li>
                </ul>
            </li>
            <li>Item 3</li>
        </ul>
        """
        expected_md = """
* Item 1
* Item 2
    * Item 2.1
    * Item 2.2
        * Item 2.2.1
* Item 3
        """.strip()
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_nested_ordered_lists(self):
        html = """
        <ol>
            <li>First main</li>
            <li>Second main
                <ol>
                    <li>Second sub 1</li>
                    <li>Second sub 2</li>
                </ol>
            </li>
        </ol>
        """
        expected_md = """
1. First main
2. Second main
    1. Second sub 1
    2. Second sub 2
        """.strip()
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_mixed_nested_lists(self):
        html = """
        <ul>
            <li>Point A</li>
            <li>Point B
                <ol>
                    <li>Numbered B1</li>
                    <li>Numbered B2
                        <ul>
                            <li>Sub-point B2a</li>
                        </ul>
                    </li>
                </ol>
            </li>
        </ul>
        """
        expected_md = """
* Point A
* Point B
    1. Numbered B1
    2. Numbered B2
        * Sub-point B2a
        """.strip()
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_list_with_paragraph_and_blockquote(self):
        html = """
        <ul>
            <li>
                <p>This is a paragraph in a list item.</p>
                <blockquote>This is a quote inside a list item.
                Another line for the quote.</blockquote>
                <p>Another paragraph.</p>
            </li>
            <li>Simple item</li>
        </ul>
        """
        # Note: Markdown for block elements inside lists requires careful indentation.
        # The exact output depends on how aggressively the converter handles newlines inside list items.
        expected_md = """
* This is a paragraph in a list item.

    > This is a quote inside a list item.
    > Another line for the quote.

    Another paragraph.
* Simple item
        """.strip()
        # The converter might produce slightly different spacing or indent for blockquotes/paras in lists.
        # This test will verify the current behavior.
        self.assertEqual(self.converter.convert(html), expected_md)


    def test_blockquote_in_list(self):
        html = """
        <ul>
            <li>Item 1</li>
            <li>
                <blockquote>Quote in LI</blockquote>
            </li>
            <li>Item 3</li>
        </ul>
        """
        expected_md = """
* Item 1
* > Quote in LI
* Item 3
        """.strip()
        # Adjusting expectation based on how blockquotes in LIs are typically rendered (indent the >)
        # My current logic might produce:
        # * Item 1
        # * > Quote in LI  <-- if blockquote itself is not further indented by the list item marker logic
        # Let's assume the ">" is indented:
        # * Item 1
        #     > Quote in LI
        # * Item 3
        # The provided `expected_md` seems to imply the `>` is not further indented by the list item marker.
        # Let's refine the expectation to match typical GFM for blockquotes in lists.
        # GFM:
        # * Item 1
        # * > Quote in LI
        # * Item 3
        # This means the blockquote content itself starts with `>` at the list item's text alignment.
        # My code's `indent_prefix` for blockquote is `self.indent_char * nesting_level`.
        # If `ul` calls `li` with `nesting_level=0`, and `li` calls `blockquote` with `nesting_level=1`,
        # then `blockquote` will have `indent_prefix = "    "` before the `>`. This is too much.
        # `blockquote`'s `nesting_level` should be that of its parent `li`.
        # The `child_nesting_level` for `li`'s children (like `blockquote`) is `li_level + 1`.
        # The `blockquote`'s `_convert_node` uses its *own* `nesting_level` for `indent_prefix`.
        # So if `li` is at level 0, `blockquote` is at level 1. `indent_prefix` for `>` is `    `.
        # *    > Quote in LI
        # This needs to be fixed in blockquote or how nesting_level is passed to it from li.
        # For now, the test will likely fail and guide the fix.
        #
        # Simpler GFM expectation:
        # * Item 1
        # * > Quote in LI
        # * Item 3
        # This means the blockquote's ">" should align with the text of "Item 1".
        # The converter's current behavior for blockquote: `prefix = indent_prefix + '> '`
        # If `li` calls its children with `nesting_level + 1`, then `blockquote` gets this as its `nesting_level`.
        # `indent_prefix` for blockquote becomes `self.indent_char * (li_nesting_level + 1)`.
        # This will over-indent.
        #
        # Corrected expectation based on how GFM handles it (block element starts on new line, indented):
        # *   Item 1
        # *   > Quote in LI
        # *   Item 3
        # The list item provides the indent for the line. Blockquote starts on that line.
        # The converter might produce:
        # * Item 1
        # *
        #     > Quote in LI  (if it treats blockquote as a block needing its own space)
        # This is a common area of ambiguity in converters.
        # Let's use a more standard GFM output as the target:
        expected_md_gfm = """
* Item 1
* > Quote in LI
* Item 3
        """.strip()
        # My logic for blockquote: `quote_marker_line_prefix = indent_prefix + '> '`
        # `indent_prefix` for blockquote is `self.indent_char * blockquote_nesting_level`.
        # If `ul` (level 0) -> `li` (level 0 for its own _convert_node call) -> `blockquote` (level 1 from li's child_nesting_level).
        # Then `indent_prefix` for blockquote is "    ". So output is `    > Quote in LI`.
        # This is more indented than GFM.
        # For now, I'll test against GFM and see if my code produces it.
        # If not, the `blockquote` or `li` logic for passing `nesting_level` needs adjustment.
        # The current `blockquote` logic: `return "\n".join(quoted_lines) + '\n\n'`
        # `quoted_lines = [quote_marker_line_prefix + line for line in lines]`
        # `quote_marker_line_prefix = indent_prefix + '> '`
        # `indent_prefix = self.indent_char * nesting_level` (for blockquote)
        # If `ul` is level 0, `li` is passed level 0. `li` calls children (blockquote) with level 1.
        # So `blockquote` gets `nesting_level=1`. `indent_prefix` = "    ".
        # Output: `*     > Quote in LI` (star, then 4 spaces, then ">") - This is standard.
        # The key is how the `*` and the `    >` combine.
        # `ul` handler: `md_items.append(current_li_marker_indent + '* ' + (item_lines[0]...))`
        # `current_li_marker_indent` is `self.indent_char * ul_nesting_level`.
        # `item_lines[0]` will be `    > Quote in LI`.
        # Result: `*     > Quote in LI` if `ul_nesting_level` is 0. This is correct.
        self.assertEqual(self.converter.convert(html), expected_md_gfm)


    def test_code_block_in_list(self):
        html = """
        <ul>
            <li>Item with code:
                <pre><code class="language-python">def foo():
  return "bar"</code></pre>
            </li>
        </ul>
        """
        # GFM standard for code blocks in lists:
        # * Item with code:
        #     ```python
        #     def foo():
        #       return "bar"
        #     ```
        # The code block is indented one level beyond the list item's text.
        # My `pre` handler:
        # `indented_fences_and_code.extend([current_pre_indent + line for line in final_code_content.split('\n')])`
        # `current_pre_indent` is `self.indent_char * pre_nesting_level`.
        # `ul` (level 0) -> `li` (level 0 for its _convert_node) -> `pre` (level 1 from `li`'s children).
        # So `pre_nesting_level` = 1. `current_pre_indent` = "    ".
        # `ul` handler prefixes with `* `.
        # So, the first line of `pre` content (`    ```python`) gets `* ` before it.
        # `*     ```python`
        # This is the standard, correct behavior.
        expected_md = """
* Item with code:
    ```python
    def foo():
      return "bar"
    ```
        """.strip()
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_simple_table(self):
        html = """
        <table>
            <thead>
                <tr><th>Header 1</th><th>Header 2</th></tr>
            </thead>
            <tbody>
                <tr><td>Cell 1.1</td><td>Cell 1.2</td></tr>
                <tr><td>Cell 2.1</td><td>Cell 2.2</td></tr>
            </tbody>
        </table>
        """
        expected_md = """
| Header 1 | Header 2 |
| --- | --- |
| Cell 1.1 | Cell 1.2 |
| Cell 2.1 | Cell 2.2 |
        """.strip()
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_table_with_code_in_cell(self):
        html = """
        <table>
            <tr><th>Description</th><th>Code</th></tr>
            <tr>
                <td>Python Hello</td>
                <td><pre><code class="language-python">print("Hello")</code></pre></td>
            </tr>
            <tr>
                <td>Inline</td>
                <td><code>my_var</code></td>
            </tr>
        </table>
        """
        # My current `tr` handler replaces newlines with `<br>` unless it's a fenced code block.
        # The `pre` handler produces a fenced code block.
        # `tr` handler's logic for `is_fenced_code_block`:
        # `cell_text_for_join = "<br>".join(fenced_lines)` which is not ideal.
        # It should be just the multi-line code block.
        #
        # GFM table with code block:
        # | Description | Code |
        # |---|---|
        # | Python Hello | ```python<br>print("Hello")<br>``` |  <-- This is one way if newlines not allowed directly
        # OR (more modern GFM might allow direct newlines if table is structured carefully, but <br> is safer)
        #
        # The current `tr` logic for `is_fenced_code_block` is:
        # `cell_text_for_join = lang_line + '\n' + '\n'.join(escaped_code_lines) + '\n' + end_fence`
        # This was before the `<br>` join attempt. This is better.
        # The test will show if this is correctly implemented.
        # The `tr` handler then joins `cell_text_for_join` with ` | `.
        # If `cell_text_for_join` is multi-line, the `| ` ` | ` join will break.
        # This means the `cell_text_for_join` for `tr` *must* be single line.
        # So, `is_fenced_code_block` path in `tr` must use `<br>` for newlines within the code block.
        #
        # Let's assume the TR handler for `is_fenced_code_block` now correctly uses `<br>` for internal newlines
        # of the code block string before joining cells.
        expected_md = """
| Description | Code |
| --- | --- |
| Python Hello | ```python<br>print("Hello")<br>``` |
| Inline | `my_var` |
        """.strip()
        # The previous version of TR handler was:
        # cell_text = cell_text_raw.replace('|', '\\|').replace('\n', '<br>') (if not code block)
        # The `is_fenced_code_block` logic I added was:
        # cell_text = lang_line + '\n' + '\n'.join(escaped_code_lines) + '\n' + end_fence
        # This is good, but this multi-line `cell_text` will break the `return "| " + " | ".join(cell_contents) + " |\n";`
        # So, the `is_fenced_code_block` path in `tr` needs to make `cell_text` single-line using `<br>`.
        # The `replace_with_git_merge_diff` for `tr` that was last applied:
        # `cell_text_for_join = "<br>".join(fenced_lines)` -- this is correct for making it single line.
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_table_empty_cells_and_header(self):
        html = "<table><thead><tr><th></th><th>H2</th></tr></thead><tbody><tr><td>C1</td><td></td></tr></tbody></table>"
        expected_md = """
|  | H2 |
| --- | --- |
| C1 |  |
        """.strip() # Note: double space for empty cell in Markdown source
        self.assertEqual(self.converter.convert(html), expected_md)

    def test_blockquote_with_paragraph_and_list(self):
        html = """
        <blockquote>
            <p>This is a paragraph in a blockquote.</p>
            <ul>
                <li>List item in quote</li>
                <li>Another item
                    <ol><li>Nested ordered</li></ol>
                </li>
            </ul>
            <p>Final para in quote.</p>
        </blockquote>
        """
        # Expected GFM:
        # > This is a paragraph in a blockquote.
        # >
        # > * List item in quote
        # > * Another item
        # >     1. Nested ordered
        # >
        # > Final para in quote.
        # My converter should produce this if `blockquote` correctly prefixes each line from its children.
        expected_md = """
> This is a paragraph in a blockquote.
>
> * List item in quote
> * Another item
>     1. Nested ordered
>
> Final para in quote.
        """.strip()
        # The converter's `blockquote` logic: `quoted_lines = [quote_marker_line_prefix + line for line in lines]`
        # `processed_content` for blockquote has its children converted.
        # If `p` returns `Text\n\n`, then `lines` for blockquote will be `["Text", ""]`.
        # This will result in `> Text\n> `. This is good.
        # If `ul` returns `* Item\n* Item2\n\n`, lines will be `["* Item", "* Item2", ""]`.
        # This will result in `> * Item\n> * Item2\n> `. This is also good.
        self.assertEqual(self.converter.convert(html), expected_md)

if __name__ == '__main__':
    unittest.main()

# TODO: Add tests for:
# - Code blocks within blockquotes.
# - Code blocks within nested lists.
# - Tables within list items or blockquotes.
# - More complex table cell content (links, bold, etc.)
# - Empty table (<table></table>)
# - Table with only thead or only tbody
# - Table with th in tbody or td in thead (if supported/makes sense)
# - Paragraphs followed immediately by lists/blockquotes without intervening newlines in HTML
#   (to ensure correct Markdown spacing)
# - Lists with very long items that wrap, to check subsequent line indentation.
# - Blockquotes with multiple paragraphs.
# - Consecutive list items that contain complex blocks, to ensure spacing between LIs is correct.
# - List item containing only a sub-list.
#   e.g. <ul><li><ul><li>Nested</li></ul></li></ul>
#   Expected: * \n    * Nested (or similar, needs GFM check)
#   GFM:
#   *
#       * Nested
#   This requires the outer LI to render something even if its direct text content is empty.
#   My current list logic might skip the outer LI's bullet if `item_lines[0]` is empty.
#   The `if not li_element.find(['ul', 'ol'], recursive=False): continue` might handle this.
#   If `li_element.find` is true, it won't `continue`. Then `item_lines[0]` might be empty.
#   `md_items.append(current_li_marker_indent + '* ' + (item_lines[0] if item_lines and item_lines[0] else ""))`
#   This would output `* ` if `item_lines[0]` is empty. This is correct for GFM.
