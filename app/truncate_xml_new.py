#!/usr/bin/env python3
"""
Truncate XML file to first 100 lines while maintaining valid XML structure.
Uses lxml to ensure the output is well-formed.
"""

from lxml import etree
from io import StringIO
import sys


def truncate_xml_to_lines(input_file, max_lines=100, priority_prefixes=None):
    """
    Truncate an XML file to a maximum number of lines while keeping valid XML.
    Uses smart boundary detection for <class> elements to avoid splitting them.
    Priority classes (matching prefixes) are included first with their methods.

    Args:
        input_file: Path to input XML file
        max_lines: Maximum number of lines to keep (default: 100)
        priority_prefixes: List of class name prefixes to prioritize (e.g., ['TaskRepos', 'Task'])

    Returns:
        str: Valid XML string truncated to approximately max_lines
    """
    import re

    if priority_prefixes is None:
        priority_prefixes = []

    # First pass: identify all classes and methods sections
    all_lines = []
    class_ranges = []  # List of (start, end, class_name) tuples
    methods_ranges = []  # List of (start, end, class_id) tuples

    with open(input_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

    # Parse to find class and methods boundaries
    i = 0
    while i < len(all_lines):
        line = all_lines[i]

        # Found a class element
        if re.search(r'<class[>\s]', line):
            class_start = i
            class_name = None
            class_depth = 1
            i += 1

            # Find class name and closing tag
            while i < len(all_lines) and class_depth > 0:
                if '<name>' in all_lines[i]:
                    # Extract class name
                    name_match = re.search(r'<name>([^<]+)</name>', all_lines[i])
                    if name_match:
                        class_name = name_match.group(1)

                if re.search(r'<class[>\s]', all_lines[i]):
                    class_depth += 1
                if '</class>' in all_lines[i]:
                    class_depth -= 1
                    if class_depth == 0:
                        class_ranges.append((class_start, i, class_name))
                        break
                i += 1

        # Found a methods element
        elif '<methods>' in line:
            methods_start = i
            class_id = None
            i += 1

            # Find class-id and closing tag
            while i < len(all_lines):
                if '<class-id>' in all_lines[i]:
                    id_match = re.search(r'<class-id>([^<]+)</class-id>', all_lines[i])
                    if id_match:
                        class_id = id_match.group(1)

                if '</methods>' in all_lines[i]:
                    methods_ranges.append((methods_start, i, class_id))
                    break
                i += 1

        i += 1

    # Categorize classes by priority
    priority_class_names = []
    priority_ranges = []
    other_ranges = []

    for start, end, class_name in class_ranges:
        if class_name and any(class_name.startswith(prefix) for prefix in priority_prefixes):
            priority_class_names.append(class_name)
            priority_ranges.append(('class', start, end, class_name))
        else:
            other_ranges.append(('class', start, end, class_name))

    # Add methods for priority classes
    for start, end, class_id in methods_ranges:
        if class_id in priority_class_names:
            priority_ranges.append(('methods', start, end, class_id))

    # Sort priority ranges by start line
    priority_ranges.sort(key=lambda x: x[1])

    # Build output: header + priority content + other content up to max_lines
    output_lines = []
    used_lines = set()

    # Find XML header and root element
    header_end = 0
    for i, line in enumerate(all_lines):
        if re.search(r'<[a-zA-Z]', line) and '<?xml' not in line:
            header_end = i
            break

    # Add header
    for i in range(header_end + 1):
        output_lines.append(all_lines[i])
        used_lines.add(i)

    # Add priority classes and methods (respecting max_lines)
    for elem_type, start, end, name in priority_ranges:
        if len(output_lines) >= max_lines:
            break
        for i in range(start, end + 1):
            if i not in used_lines:
                output_lines.append(all_lines[i])
                used_lines.add(i)
                if len(output_lines) >= max_lines:
                    break

    # Add other content up to max_lines
    for i in range(header_end + 1, len(all_lines)):
        if len(output_lines) >= max_lines:
            break
        if i not in used_lines:
            output_lines.append(all_lines[i])
            used_lines.add(i)

    # Join lines into a single string
    truncated_content = ''.join(output_lines)

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
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'TodoCore.sou')
    output_file = os.path.join(script_dir, 'TodoCore_truncated.xml')

    # Truncate the XML with priority prefixes
    # Classes starting with these prefixes will be included first with all their methods
    priority_prefixes = ['HttpSyncProxy']
    truncated_xml = truncate_xml_to_lines(input_file, max_lines=100, priority_prefixes=priority_prefixes)

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
