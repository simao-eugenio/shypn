#!/bin/bash
# Embed bibliography directly in tex file for bioRxiv

# Create temp file with everything before bibliography
sed '/^\\bibliographystyle{plainnat}/,$d' main_single.tex > main_single_embedded.tex

# Add the compiled bibliography from .bbl file
cat main_single.bbl >> main_single_embedded.tex

# Close document
echo "" >> main_single_embedded.tex
echo "\\end{document}" >> main_single_embedded.tex

echo "✓ Created main_single_embedded.tex with embedded bibliography"
