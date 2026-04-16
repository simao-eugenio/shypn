#!/bin/bash
# Create single-file LaTeX for bioRxiv with proper structure

# Start with main.tex header (up to \begin{document})
sed -n '1,/^\\begin{document}/p' main.tex > main_single.tex

# Add maketitle and abstract structure
echo "" >> main_single.tex
echo "\\maketitle" >> main_single.tex
echo "" >> main_single.tex
echo "\\begin{abstract}" >> main_single.tex
cat abstract.tex | grep -v "^%" >> main_single.tex
echo "\\end{abstract}" >> main_single.tex
echo "" >> main_single.tex
echo "\\vspace{6pt}" >> main_single.tex
echo "\\noindent\\textbf{Keywords:} Systems Biology, Cellular Decision-Making, Metabolic-Regulatory Networks, Signal Hierarchical Petri Nets, Quantitative Biological Modeling, Gene Regulatory Networks, Cell Fate Commitment, Biological Petri Nets, Bioinformatics" >> main_single.tex
echo "" >> main_single.tex

# Add all sections
echo "\\section{Introduction}" >> main_single.tex
cat introduction.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

echo "\\section{Background and Related Work}" >> main_single.tex
cat background.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

echo "\\section{Signal Hierarchy Theory}" >> main_single.tex
cat signal_hierarchy.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

echo "\\section{Unified Formalism}" >> main_single.tex
cat formalism.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

echo "\\section{Validation}" >> main_single.tex
cat validation.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

echo "\\section{Discussion}" >> main_single.tex
cat discussion.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

echo "\\section{Conclusion}" >> main_single.tex
cat conclusion.tex | grep -v "^%" >> main_single.tex
echo "" >> main_single.tex

# Add tail sections (acknowledgments, references, etc.)
cat tail_sections.tex >> main_single.tex
echo "" >> main_single.tex

# Close document
echo "\\end{document}" >> main_single.tex

echo "✓ Created main_single.tex with proper structure"
