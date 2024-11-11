import sys
import re

def remove_bom(content):
    # Define BOMs for various encodings
    boms = {
        '\ufeff': 1,               # UTF-8 BOM (1 character)
        '\ufffe': 1,               # UTF-16 BOM (1 character)
        '\ufeff\ufffe': 2,         # UTF-32 BOM (2 characters)
        '\ufffe\ufeff': 2,         # UTF-32 (Little Endian) BOM (2 characters)
        '\xff\xfe': 1,             # UTF-16 Little Endian BOM (1 character)
        '\xfe\xff': 1,             # UTF-16 Big Endian BOM (1 character)
    }

    for bom, length in boms.items():
        if content.startswith(bom):
            # Remove the BOM
            content = content[length:]
            break
    return content

def count_leading_hashes(line):
    """Count the number of consecutive '#' characters at start of line."""
    count = 0
    for char in line:
        if char == '#':
            count += 1
        else:
            break

    return count

def process_section_markers(line):
    """Replace section markers with appropriate symbols."""

    if line.startswith('### '):
        return line.replace('###', 'TODO', 1)
    elif line.startswith('#### ') or line.startswith('## ') or line.startswith('# '):
        return line.replace('#### ', '', 1).replace('## ', '', 1).replace('# ', '', 1)
    return line

def process_brackets(line, prior_line_was_table):
    """Process bracketed content according to specified rules."""
    # Replace [ ] with - TODO
    line = re.sub(r'\[ \]', 'TODO', line)
    # Replace [x] with - DONE
    line = re.sub(r'\[x\]', 'DONE', line)
    # Replace [digits] with empty string
    line = re.sub(r'\[\d+\] ', '', line)
    # Make each line a bullet for Logseq
    # However, ensure it doesn't already have a bullet
    # or that it isn't a table line
    # not re.match(r"^\s*-", line) 
    if not bool(re.match(r"^\s*-{1,}\s*", line)):
        if not bool(re.match(r"^\s*\|.*\|", line)):
            prior_line_was_table[0] = False
            line = '- ' + line
        else: # so it is a table, only the first line can have a dash
            if prior_line_was_table[0] == False:
                line = '- ' + line
                prior_line_was_table[0] = True

    return line

def process_file(input_file, output_file):
    try:
        with open(input_file, 'r') as f:
            content = f.readlines()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)

    # Remove BOM from beginning of file if there
    if len(content) > 0:
        content[0] = remove_bom(content[0])

    # Process the content
    processed_lines = []
    current_section = []
    current_hash_count = 0
    prior_line_was_table = [False]

    for line in content:

        # Check if line contains only spaces (or is empty)
        if line.strip() == "":
            continue  # Skip to the next line

        # Descriptions should be treated like sections and be indented
        # To achieve this replace "**Description:**" with "#### Description"
        line = re.sub(r"\*\*Description:\*\*", "#### Description", line)

        line = line.rstrip()
        hash_count = count_leading_hashes(line)

        if hash_count > 0:  # New section header found
            # Process previous section if it exists
            if current_section:
                # Indent the section contents
                indent = '\t' * (current_hash_count - 1)
                header = indent + process_brackets(process_section_markers(current_section[0]), prior_line_was_table)
                indent = '\t' * current_hash_count
                body = [indent + process_brackets(line, prior_line_was_table) for line in current_section[1:]]
                processed_lines.extend([header] + body)
                current_section = []

            current_hash_count = hash_count
            current_section = [line]
        else:
            if current_section:  # Add to current section
                current_section.append(line)
            else:  # Standalone line
                processed_lines.append(process_brackets(process_section_markers(line), prior_line_was_table))

    # Process the last section
    if current_section:
        indent = '\t' * (current_hash_count - 1)
        header = indent + process_brackets(process_section_markers(current_section[0]), prior_line_was_table)
        indent = '\t' * current_hash_count
        body = [indent + process_brackets(line, prior_line_was_table) for line in current_section[1:]]
        processed_lines.extend([header] + body)

    # Write to output file
    try:
        with open(output_file, 'w') as f:
            for line in processed_lines:
                f.write(line + '\n')
    except IOError:
        print(f"Error: Cannot write to output file '{output_file}'.")
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    process_file(input_file, output_file)

if __name__ == "__main__":
    main()
