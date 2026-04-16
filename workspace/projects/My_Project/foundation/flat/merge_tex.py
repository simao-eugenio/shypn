# Merge all tex files into single file for bioRxiv
import re

def read_section(filename):
    with open(filename, 'r') as f:
        content = f.read()
    # Remove comment headers
    content = re.sub(r'^%[^\n]*\n+', '', content, flags=re.MULTILINE)
    return content.strip()

# Read main template
with open('main.tex', 'r') as f:
    merged = f.read()

# Replace each \input{} with file content
replacements = [
    ('abstract', 'abstract.tex'),
    ('introduction', 'introduction.tex'),
    ('background', 'background.tex'),
    ('signal_hierarchy', 'signal_hierarchy.tex'),
    ('formalism', 'formalism.tex'),
    ('validation', 'validation.tex'),
    ('discussion', 'discussion.tex'),
    ('conclusion', 'conclusion.tex'),
    ('tail_sections', 'tail_sections.tex'),
]

for input_name, filename in replacements:
    section_content = read_section(filename)
    pattern = r'\\input\{' + input_name + r'\}'
    merged = re.sub(pattern, section_content, merged)

# Write single-file version
with open('main_single.tex', 'w') as f:
    f.write(merged)

print("✓ Created main_single.tex (single-file for bioRxiv)")
