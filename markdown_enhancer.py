import re
from bs4 import BeautifulSoup, NavigableString, Tag

class EnhancedMarkdownConverter:
    def __init__(self):
        self.allowed_attrs = {
            'a': ['href'],
            'img': ['src', 'alt'],
            'code': ['class']
        }
        self.tags_to_remove = ['script', 'style', 'meta', 'link', 'head']
        self.tags_to_unwrap = ['span', 'div']
        self.indent_char = "    "

    def _clean_attributes(self, soup):
        for tag in soup.find_all(True):
            allowed_tag_attrs = self.allowed_attrs.get(tag.name, [])
            current_attrs = list(tag.attrs.keys())
            for attr_name in current_attrs:
                if attr_name not in allowed_tag_attrs:
                    del tag[attr_name]
        return soup

    def _remove_tags(self, soup):
        for tag_name in self.tags_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        return soup

    def _unwrap_tags(self, soup):
        for _ in range(5):
            unwrapped_in_pass = 0
            for tag_name in self.tags_to_unwrap:
                for tag in soup.find_all(tag_name): # Re-find in each pass
                    tag.unwrap()
                    unwrapped_in_pass +=1
            if unwrapped_in_pass == 0:
                break
        return soup

    def _preprocess_html(self, html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, 'html.parser')
        soup = self._remove_tags(soup)
        soup = self._unwrap_tags(soup)
        soup = self._clean_attributes(soup)
        return soup

    def convert(self, html: str) -> str:
        soup = self._preprocess_html(html)
        if soup.name in ['html', 'body'] and hasattr(soup, 'contents'):
             return self._convert_node(soup.contents, nesting_level=0)
        return self._convert_node(soup, nesting_level=0)

    def _convert_node(self, element, nesting_level=0):
        # 1. Handle Text Nodes
        if isinstance(element, NavigableString):
            text = str(element)
            if element.parent and element.parent.name == 'pre':
                return text
            if text.isspace():
                return ' '
            return re.sub(r'\s+', ' ', text)

        # 2. Handle Lists of Nodes
        if isinstance(element, list) or isinstance(element, type(BeautifulSoup().contents)):
             return ''.join([self._convert_node(child, nesting_level) for child in element])

        # 3. Handle Non-Tag Elements
        if not isinstance(element, Tag):
            return ''

        # 4. Determine Nesting Level for Children
        child_content_nesting_level = nesting_level
        if element.name in ['blockquote', 'li', 'td', 'th']:
            child_content_nesting_level = nesting_level + 1

        # 5. Process Children
        processed_children_content = ""
        if element.name not in ['pre', 'ul', 'ol', 'table', 'thead', 'tbody', 'tr']:
            processed_children_content = ''.join([self._convert_node(child, child_content_nesting_level) for child in element.contents])

        # 6. Tag-Specific Conversion Logic
        current_element_indent_prefix = self.indent_char * nesting_level

        if element.name == 'p':
            stripped_content = processed_children_content.strip()
            if not stripped_content: return "\n\n"
            parent = element.parent
            if parent and parent.name in ['li', 'blockquote', 'td', 'th']:
                 return stripped_content + '\n\n'
            else:
                 lines = stripped_content.split('\n')
                 actual_indent = current_element_indent_prefix if nesting_level > 0 else ""
                 indented_lines = [actual_indent + line for line in lines]
                 return "\n".join(indented_lines) + '\n\n'

        elif element.name in ['strong', 'b']:
            return f'**{processed_children_content.strip()}**'
        elif element.name in ['em', 'i']:
            return f'*{processed_children_content.strip()}*' # Corrected: single asterisk for italic

        elif element.name.startswith('h') and len(element.name) == 2 and element.name[1].isdigit():
            level = int(element.name[1])
            return '#' * level + ' ' + processed_children_content.strip() + '\n\n'

        elif element.name == 'blockquote':
            stripped_content = processed_children_content.strip()
            if not stripped_content: return "\n\n"
            lines = stripped_content.split('\n')
            quote_marker_line_prefix = current_element_indent_prefix + '> '
            quoted_lines = [quote_marker_line_prefix + line for line in lines]
            return "\n".join(quoted_lines) + "\n\n"

        elif element.name == 'li':
            return processed_children_content

        elif element.name == 'ul':
            md_items = []
            for li_element in element.find_all('li', recursive=False):
                li_content_markdown = self._convert_node(li_element, nesting_level)
                item_lines = li_content_markdown.strip().split('\n')
                is_empty_li_content = not item_lines or (not item_lines[0].strip() and len(item_lines) == 1)
                has_sublist = li_element.find(['ul', 'ol'], recursive=False)
                if is_empty_li_content and not has_sublist:
                    is_truly_empty_text_nodes = not any(c.strip() for c in li_element.contents if isinstance(c, NavigableString))
                    is_truly_empty_tags = not li_element.find(True, recursive=False)
                    if is_truly_empty_text_nodes and is_truly_empty_tags:
                        md_items.append( current_element_indent_prefix + '* ' )
                        continue
                first_line_content = item_lines[0] if item_lines and item_lines[0] else ""
                first_child_tag = li_element.find(True, recursive=False)
                bullet_on_own_line = False
                if first_child_tag and first_child_tag.name in ['ul', 'ol', 'pre', 'blockquote']:
                    no_text_before = True; prev_sibling = first_child_tag.previous_sibling
                    while prev_sibling:
                        if (isinstance(prev_sibling, NavigableString) and prev_sibling.strip()) or isinstance(prev_sibling, Tag):
                            no_text_before = False; break
                        prev_sibling = prev_sibling.previous_sibling
                    if no_text_before: bullet_on_own_line = True
                if bullet_on_own_line:
                     md_items.append(current_element_indent_prefix + '*')
                     md_items.append(first_line_content)
                else:
                     md_items.append(current_element_indent_prefix + '* ' + first_line_content)
                subsequent_line_text_indent = current_element_indent_prefix + self.indent_char
                for k in range(1, len(item_lines)): md_items.append(subsequent_line_text_indent + item_lines[k])
            return "\n".join(md_items) + "\n\n" if md_items else "\n\n"

        elif element.name == 'ol':
            md_items = []
            for i, li_element in enumerate(element.find_all('li', recursive=False)):
                li_content_markdown = self._convert_node(li_element, nesting_level)
                item_lines = li_content_markdown.strip().split('\n')
                is_empty_li_content = not item_lines or (not item_lines[0].strip() and len(item_lines) == 1)
                has_sublist = li_element.find(['ul', 'ol'], recursive=False)
                if is_empty_li_content and not has_sublist:
                    is_truly_empty_text_nodes = not any(c.strip() for c in li_element.contents if isinstance(c, NavigableString))
                    is_truly_empty_tags = not li_element.find(True, recursive=False)
                    if is_truly_empty_text_nodes and is_truly_empty_tags:
                        md_items.append( current_element_indent_prefix + f"{i+1}. ")
                        continue
                marker = f"{i + 1}. "; first_line_content = item_lines[0] if item_lines and item_lines[0] else ""
                first_child_tag = li_element.find(True, recursive=False)
                bullet_on_own_line = False
                if first_child_tag and first_child_tag.name in ['ul', 'ol', 'pre', 'blockquote']:
                    no_text_before = True; prev_sibling = first_child_tag.previous_sibling
                    while prev_sibling:
                        if (isinstance(prev_sibling, NavigableString) and prev_sibling.strip()) or isinstance(prev_sibling, Tag):
                            no_text_before = False; break
                        prev_sibling = prev_sibling.previous_sibling
                    if no_text_before: bullet_on_own_line = True
                if bullet_on_own_line:
                    md_items.append(current_element_indent_prefix + marker.strip())
                    md_items.append(first_line_content)
                else:
                    md_items.append(current_element_indent_prefix + marker + first_line_content)
                subsequent_line_text_indent = current_element_indent_prefix + ' ' * len(marker)
                for k in range(1, len(item_lines)): md_items.append(subsequent_line_text_indent + item_lines[k])
            return "\n".join(md_items) + "\n\n" if md_items else "\n\n"

        elif element.name == 'a':
            href = element.get('href', '')
            return f'[{processed_children_content.strip()}]({href})'

        elif element.name == 'table':
            header_md = ""; tbody_md = ""
            thead = element.find('thead')
            if thead: header_md = self._convert_node(thead, nesting_level)
            tbody = element.find('tbody')
            if tbody: tbody_md = self._convert_node(tbody, nesting_level)
            if not header_md.strip() and not tbody_md.strip(): return "\n\n"
            return (header_md + tbody_md).strip('\n') + "\n\n"

        elif element.name == 'thead':
            rows = [self._convert_node(tr, nesting_level) for tr in element.find_all('tr', recursive=False)]
            if not any(row.strip() for row in rows): return ""
            num_cols = 0; tr_elements = element.find_all('tr', recursive=False)
            if tr_elements: num_cols = len(tr_elements[0].find_all(['th', 'td'], recursive=False))
            if num_cols == 0 and element.parent and element.parent.name == 'table':
                tbody = element.parent.find('tbody')
                if tbody and tbody.find('tr'): num_cols = len(tbody.find('tr').find_all('td', recursive=False))
            separator = "| " + " | ".join(["---"] * num_cols) + " |\n" if num_cols > 0 else "|\n"
            return "".join(rows) + separator

        elif element.name == 'tbody':
            return "".join([self._convert_node(tr, nesting_level) for tr in element.find_all('tr', recursive=False)])

        elif element.name == 'tr':
            cells = []
            for cell_el in element.find_all(['th', 'td'], recursive=False):
                content = self._convert_node(cell_el, nesting_level)
                is_code = content.strip().startswith('```') and content.strip().endswith('```')
                if is_code:
                    lines = content.strip().split('\n')
                    if len(lines) >= 2:
                        code_lines = lines[1:-1]
                        escaped_code = [l.replace('|', '\\|') for l in code_lines]
                        text = lines[0] + '\n' + '\n'.join(escaped_code) + '\n' + lines[-1]
                        text = text.replace('\n', '<br>')
                    else: text = content.strip().replace('|', '\\|').replace('\n', '<br>')
                else: text = content.strip().replace('|', '\\|').replace('\n', '<br>')
                cells.append(text if text.strip() else " ")
            return "| " + " | ".join(cells) + " |\n" if cells else ""

        elif element.name in ['th', 'td']:
            return processed_children_content

        elif element.name == 'pre':
            raw_text = ""; lang = ""
            code_tag = element.find('code')
            indent_str = current_element_indent_prefix
            if code_tag:
                for cls in code_tag.get('class', []):
                    if cls.startswith('language-'): lang = cls[len('language-'):]; break
                raw_text = code_tag.get_text(strip=False)
            else:
                raw_text = element.get_text(strip=False)
            lines = [l.rstrip() for l in raw_text.splitlines()]
            min_indent = float('inf')
            for l in lines:
                if l.strip(): min_indent = min(min_indent, len(l) - len(l.lstrip()))
            if min_indent == float('inf'): min_indent = 0
            dedented = [l[min_indent:] for l in lines] if min_indent > 0 else lines
            start = 0;
            while start < len(dedented) and not dedented[start].strip(): start += 1
            end = len(dedented)
            while end > start and not dedented[end-1].strip(): end -=1
            final_lines = dedented[start:end]
            content = "\n".join(final_lines)
            return f"{indent_str}```{lang}\n" + \
                   "\n".join([indent_str + l for l in final_lines]) + \
                   f"\n{indent_str}```\n\n"

        elif element.name == 'code':
            if element.find_parent('pre'): return processed_children_content
            text = processed_children_content.strip()
            if '`' not in text: return f'`{text}`'
            ticks = '``'; padding = " " if text.startswith('`') or text.endswith('`') or ' ' not in text else ""
            while f'{ticks}{padding}{text}{padding}{ticks}'.count('`') % 2 != 0 or ticks in text : ticks += '`' ; padding = " "
            return f"{ticks}{padding}{text}{padding}{ticks}"

        elif element.name == 'br': return '\n'
        elif element.name == 'img': return f"![{element.get('alt','')}]({element.get('src','')})"
        elif element.name in ['html', 'body', 'title']: return processed_children_content
        return processed_children_content.strip() if processed_children_content.strip() else ""

if __name__ == '__main__':
    # ... (examples remain the same)
    converter = EnhancedMarkdownConverter()

    print("--- Basic P, B, I ---")
    print(converter.convert("<p> Hello  <b>  bold  </b> and  <i>  italic  </i>  world.  </p>"))

    print("\n--- Tag Unwrapping ---")
    print(converter.convert("<p>Text <span>  inside span  </span> and <div>  inside div  </div>.</p>"))

    print("\n--- Inline Code ---")
    print(converter.convert("<p>Use <code>  myVar  </code> variable.</p>"))
    print(converter.convert("<p><code>`code with backtick`</code></p>"))
    print(converter.convert("<p><code>  `code with backtick and spaces`  </code></p>"))
    print(converter.convert("<p><code> ``many`` `backticks` </code></p>"))


    print("\n--- Nested Lists ---")
    html_nested_list_para_quote = """
    <ul>
        <li>Item 1</li>
        <li><p>Para in item 2</p>
            <blockquote><p>Quote in item 2, para 1.</p><p>Quote para 2.</p></blockquote>
            <p>Another para in item 2.</p>
            <ul><li>Sub item 2.1<ul><li>Sub-sub 2.1.1</li></ul></li></ul>
        </li>
        <li>Item 3</li>
    </ul>
    """
    print(converter.convert(html_nested_list_para_quote))

    print("\n--- Table with Code ---")
    html_table_with_code = """
        <table>
            <thead><tr><th>Description</th><th>Code Sample</th></tr></thead>
            <tbody>
                <tr>
                    <td>Python Hello World</td>
                    <td><pre><code class="language-python">def main():
    print("Hello") # A comment
    # Another comment line
print("Done") # This is outside</code></pre></td>
                </tr>
                <tr><td>Just text</td><td>Some `inline_code`</td></tr>
            </tbody>
        </table>
    """
    print(converter.convert(html_table_with_code))

    print("\n--- Blockquote with List ---")
    html_blockquote_list = """
        <blockquote>
            <p>This is a paragraph in a blockquote.</p>
            <ul>
                <li>List item in quote</li>
                <li>Another item
                    <ol><li>Nested ordered list item</li></ol>
                </li>
            </ul>
            <p>Final para in quote.</p>
        </blockquote>
    """
    print(converter.convert(html_blockquote_list))

    print("\n--- Empty LI Handling and Complex List ---")
    html_empty_li_handling = """
    <ol>
        <li></li>
        <li>Item Two</li>
        <li><ul><li>Sub List Item A (UL)</li><li></li><li>Sub List Item B (UL)</li></ul></li>
        <li>Item Four</li>
        <li><ol><li>Sub List Item C (OL)</li></ol></li>
        <li></li>
    </ol>
    """
    print(converter.convert(html_empty_li_handling))

    print("\n--- Code block in list ---")
    html_code_in_list = """
    <ul>
        <li>Item 1</li>
        <li>Here is some code:
            <pre><code class="language-javascript">  // JS code
  function greet() {
      console.log("Hello from list!");
  }
            </code></pre>
        </li>
        <li>Item 3</li>
    </ul>"""
    print(converter.convert(html_code_in_list))

    print("\n--- Paragraphs in list items ---")
    html_para_in_li = """
    <ul>
      <li><p>First paragraph in LI.</p><p>Second paragraph in LI.</p></li>
      <li><p>Another item with a para.</p></li>
    </ul>"""
    print(converter.convert(html_para_in_li))

    print("\n--- Table with various content ---")
    html_table_complex_cells = """
    <table>
      <tr><th>Name</th><th>Details</th><th>Status</th></tr>
      <tr><td>Item A</td><td>Contains <b>bold</b> and <i>italic</i> and <a href="#">link</a></td><td>OK</td></tr>
      <tr><td>Item B</td><td><p>Paragraph in cell.</p><ul><li>List in cell</li></ul></td><td><pre><code>raw text pre</code></pre></td></tr>
    </table>
    """
    print(converter.convert(html_table_complex_cells))
