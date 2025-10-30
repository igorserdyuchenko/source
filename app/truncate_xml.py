#!/usr/bin/env python3
"""
Truncate XML file to first 100 lines while maintaining valid XML structure.
Uses lxml to ensure the output is well-formed.
"""

from lxml import etree
from io import StringIO
import sys


def truncate_xml_to_lines(input_file, max_lines=100):
    """
    Truncate an XML file to a maximum number of lines while keeping valid XML.

    Args:
        input_file: Path to input XML file
        max_lines: Maximum number of lines to keep (default: 100)

    Returns:
        str: Valid XML string truncated to approximately max_lines
    """
    # Read the first max_lines from the file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = []
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line)

    # Join lines into a single string
    truncated_content = ''.join(lines)

    # Try to parse as-is first
    try:
        tree = etree.fromstring(truncated_content.encode('utf-8'))
        # If it parses successfully, return pretty-printed version
        return etree.tostring(tree, encoding='unicode', pretty_print=True)
    except etree.XMLSyntaxError:
        # XML is incomplete, need to close open tags
        pass

    # Parse with recovery to handle incomplete XML
    parser = etree.XMLParser(recover=True)
    try:
        tree = etree.fromstring(truncated_content.encode('utf-8'), parser=parser)
        return etree.tostring(tree, encoding='unicode', pretty_print=True)
    except Exception as e:
        print(f"Error parsing XML even with recovery: {e}", file=sys.stderr)

        # Fallback: manually balance tags
        return balance_xml_tags(truncated_content)


def balance_xml_tags(xml_content):
    """
    Manually balance XML tags by tracking open elements.

    Args:
        xml_content: Incomplete XML string

    Returns:
        str: Balanced XML string
    """
    lines = xml_content.split('\n')
    open_tags = []
    balanced_lines = []

    for line in lines:
        balanced_lines.append(line)

        # Simple tag tracking (not perfect but works for most cases)
        # Find opening tags
        import re

        # Match opening tags like <tag> or <tag attr="value">
        opening_pattern = r'<([a-zA-Z][\w-]*)[^/>]*(?<!/)>'
        for match in re.finditer(opening_pattern, line):
            tag_name = match.group(1)
            # Skip XML declaration and comments
            if tag_name not in ['?xml', '!--']:
                open_tags.append(tag_name)

        # Match self-closing tags like <tag/>
        self_closing_pattern = r'<([a-zA-Z][\w-]*)[^>]*/>'
        for match in re.finditer(self_closing_pattern, line):
            pass  # Self-closing tags don't need tracking

        # Match closing tags like </tag>
        closing_pattern = r'</([a-zA-Z][\w-]*)>'
        for match in re.finditer(closing_pattern, line):
            tag_name = match.group(1)
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()

    # Close remaining open tags in reverse order
    if open_tags:
        balanced_lines.append('\n  <!-- Truncated - closing open tags -->')
        while open_tags:
            tag = open_tags.pop()
            balanced_lines.append(f'</{tag}>')

    return '\n'.join(balanced_lines)


def main():
    """Main function to demonstrate truncation."""
    input_file = '/app/TodoCore.sou'
    output_file = '/app/TodoCore_truncated.xml'


    # Truncate the XML
    truncated_xml = truncate_xml_to_lines(input_file, max_lines=10)

    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(truncated_xml)

    print(f"Truncated XML written to: {output_file}")

    # Verify it's valid XML
    try:
        tree = etree.fromstring(truncated_xml.encode('utf-8'))
        print("✓ Output is valid XML")
        print(f"✓ Root element: <{tree.tag}>")
        print(f"✓ Number of child elements: {len(tree)}")

        # Count lines in output
        line_count = len(truncated_xml.split('\n'))
        print(f"✓ Output line count: {line_count}")

    except etree.XMLSyntaxError as e:
        print(f"✗ Output XML validation failed: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
