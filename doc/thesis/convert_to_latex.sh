#!/bin/bash
# Script to convert thesis Markdown chapters to LaTeX
# Usage: ./convert_to_latex.sh

set -e  # Exit on error

THESIS_DIR="/home/simao/projetos/shypn/doc/thesis"
LATEX_DIR="$THESIS_DIR/latex"
CHAPTERS_DIR="$LATEX_DIR/chapters"

echo "=== Thesis Markdown to LaTeX Converter ==="
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "Pandoc not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y pandoc texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science biber
    echo "Pandoc installed successfully!"
else
    echo "Pandoc found: $(pandoc --version | head -n 1)"
fi

echo ""
echo "Creating LaTeX directory structure..."
mkdir -p "$LATEX_DIR"
mkdir -p "$CHAPTERS_DIR"
mkdir -p "$LATEX_DIR/figures"
mkdir -p "$LATEX_DIR/tables"

echo ""
echo "Converting chapters to LaTeX..."

# Convert each chapter
for i in {01..15}; do
    CHAPTER_FILE="$THESIS_DIR/Chapter_${i}_*.md"
    
    # Check if file exists (use glob expansion)
    if ls $CHAPTER_FILE 1> /dev/null 2>&1; then
        # Get the actual filename
        ACTUAL_FILE=$(ls $CHAPTER_FILE | head -n 1)
        OUTPUT_FILE="$CHAPTERS_DIR/chapter_${i}.tex"
        
        echo "Converting Chapter ${i}..."
        
        pandoc "$ACTUAL_FILE" \
            -f markdown \
            -t latex \
            --top-level-division=chapter \
            --number-sections \
            --listings \
            -o "$OUTPUT_FILE"
        
        echo "  ✓ Created: $OUTPUT_FILE"
    else
        echo "  ⚠ Warning: Chapter ${i} not found"
    fi
done

echo ""
echo "Creating main thesis LaTeX file..."

cat > "$LATEX_DIR/thesis.tex" << 'EOF'
\documentclass[12pt,a4paper,twoside,openright]{book}

% ============================================================
% PACKAGES
% ============================================================

% Language and encoding
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}

% Mathematics
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}

% Graphics and figures
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{arrows,shapes,positioning,calc}
\usepackage{float}
\usepackage{caption}
\usepackage{subcaption}

% Tables
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{multirow}
\usepackage{array}

% Colors
\usepackage{xcolor}
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

% Code listings
\usepackage{listings}
\lstdefinestyle{pythonstyle}{
    backgroundcolor=\color{backcolour},
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=left,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}
\lstset{style=pythonstyle}

% Algorithms
\usepackage{algorithm}
\usepackage{algpseudocode}

% Bibliography
\usepackage[backend=biber,style=numeric,sorting=none]{biblatex}
\addbibresource{references.bib}

% Hyperlinks and references
\usepackage[hidelinks]{hyperref}
\usepackage{cleveref}

% Page layout
\usepackage{geometry}
\geometry{
    a4paper,
    left=3.5cm,
    right=2.5cm,
    top=2.5cm,
    bottom=2.5cm
}

% Headers and footers
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\leftmark}
\fancyhead[RO]{\rightmark}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% Line spacing
\usepackage{setspace}
\onehalfspacing

% Theorem environments
\newtheorem{theorem}{Theorem}[chapter]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}
\theoremstyle{remark}
\newtheorem{remark}[theorem]{Remark}

% Custom commands
\newcommand{\BioPN}{\textsf{Bio-PN}}
\newcommand{\SHYpn}{\textsf{SHYpn}}
\newcommand{\kegg}{\textsf{KEGG}}
\newcommand{\brenda}{\textsf{BRENDA}}

% ============================================================
% DOCUMENT
% ============================================================

\begin{document}

% Front matter
\frontmatter

% Title page
\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\LARGE\bfseries Extended Biological Petri Nets:\\
    A Formal Framework for Multi-Scale\\
    Systems Biology Modeling\par}
    
    \vspace{2cm}
    
    {\Large Simão Eugénio\par}
    
    \vspace{2cm}
    
    {\large A thesis submitted in partial fulfillment\\
    of the requirements for the degree of\\
    Doctor of Philosophy\par}
    
    \vspace{1cm}
    
    {\large Department of Computer Science\\
    University Name\par}
    
    \vspace{1cm}
    
    {\large November 2025\par}
    
    \vfill
\end{titlepage}

% Abstract
\chapter*{Abstract}
\addcontentsline{toc}{chapter}{Abstract}

Biological systems exhibit complex, multi-scale dynamics spanning molecular interactions (milliseconds) to cellular processes (hours). Integrating these diverse timescales and regulatory mechanisms within a unified computational framework remains a fundamental challenge in systems biology.

This thesis presents the \textbf{Extended Biological Petri Net (Bio-PN)} formalism, introducing four core innovations:

\begin{enumerate}
    \item \textbf{Weak Independence Theory}: A relaxed form of transition independence permitting shared catalysts and convergent pathways while preserving reachability properties. Empirically, 64\% of biological transition pairs exhibit weak independence, enabling up to 3× parallel execution speedup.
    
    \item \textbf{Heterogeneous Transition Types}: Unified formal semantics for four dynamics—continuous (ODE), stochastic (Gillespie SSA), timed (scheduled events), and burst (transcriptional bursting)—coordinated through a hybrid scheduler.
    
    \item \textbf{Arc-Level Regulation}: Test arcs (catalysis) and inhibitor arcs (feedback) with threshold functions, providing compositional, topologically visible regulatory logic superior to global event systems.
    
    \item \textbf{Atomic Conservation}: Automatic verification of elemental balance via biochemical formula tracking, with database-driven cofactor suggestion (KEGG, ChEBI integration).
\end{enumerate}

The formalism is validated through 16 progressive examples and three comprehensive case studies: complete glycolysis (10 transitions, 3 regulatory checkpoints), citric acid cycle (8 transitions, cyclic topology), and integrated cellular respiration (32 transitions, carbon and energy accounting). All models exhibit physiologically realistic steady-state concentrations and regulatory responses.

Implementation in the \SHYpn{} platform demonstrates 85--95\% modeling time reduction through automatic parameter inference from BRENDA (kinetic database). Performance benchmarks show linear time scaling (0.58s per transition) and 3× parallel speedup on 8 cores for weakly independent transitions. The system is competitive with COPASI (1.3× faster) and Snoopy (2× faster) despite Python overhead.

This work advances both Petri net theory (generalizing independence for catalytic systems) and systems biology practice (structured, automated, verifiable modeling). Future directions include spatial dynamics (colored Petri nets), genome-scale models (hierarchical abstraction, GPU acceleration), and machine learning integration (structure and parameter inference from omics data).

\textbf{Keywords:} Biological Petri nets, Multi-scale modeling, Weak independence, Hybrid simulation, Systems biology, Parameter inference

\clearpage

% Table of contents
\tableofcontents
\clearpage

% List of figures
\listoffigures
\clearpage

% List of tables
\listoftables
\clearpage

% Main matter
\mainmatter

% Include chapters
\include{chapters/chapter_01}
\include{chapters/chapter_02}
\include{chapters/chapter_03}
\include{chapters/chapter_04}
\include{chapters/chapter_05}
\include{chapters/chapter_06}
\include{chapters/chapter_07}
\include{chapters/chapter_08}
\include{chapters/chapter_09}
\include{chapters/chapter_10}
\include{chapters/chapter_11}
\include{chapters/chapter_12}
\include{chapters/chapter_13}
\include{chapters/chapter_14}
\include{chapters/chapter_15}

% Back matter
\backmatter

% Bibliography
\printbibliography[heading=bibintoc,title={References}]

% Appendices (optional)
% \appendix
% \include{chapters/appendix_a}

\end{document}
EOF

echo "  ✓ Created: $LATEX_DIR/thesis.tex"

echo ""
echo "Creating empty bibliography file..."
cat > "$LATEX_DIR/references.bib" << 'EOF'
% Bibliography file for thesis
% Add your BibTeX entries here

@article{Reddy1993,
    author = {Reddy, V. N. and Mavrovouniotis, M. L. and Liebman, M. N.},
    title = {Petri Net Representations in Metabolic Pathways},
    journal = {Proceedings of the 1st International Conference on Intelligent Systems for Molecular Biology},
    year = {1993},
    pages = {328--336}
}

@article{Gillespie1977,
    author = {Gillespie, Daniel T.},
    title = {Exact stochastic simulation of coupled chemical reactions},
    journal = {The Journal of Physical Chemistry},
    volume = {81},
    number = {25},
    pages = {2340--2361},
    year = {1977}
}

% Add more references as needed
EOF

echo "  ✓ Created: $LATEX_DIR/references.bib"

echo ""
echo "Creating Makefile for compilation..."
cat > "$LATEX_DIR/Makefile" << 'EOF'
# Makefile for thesis compilation

MAIN = thesis
LATEX = pdflatex
BIBER = biber

.PHONY: all clean cleanall view

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex chapters/*.tex
	$(LATEX) $(MAIN)
	$(BIBER) $(MAIN)
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

clean:
	rm -f *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.bcf *.run.xml
	rm -f chapters/*.aux

cleanall: clean
	rm -f $(MAIN).pdf

view: $(MAIN).pdf
	xdg-open $(MAIN).pdf &

help:
	@echo "Available targets:"
	@echo "  all       - Compile thesis (default)"
	@echo "  clean     - Remove auxiliary files"
	@echo "  cleanall  - Remove all generated files including PDF"
	@echo "  view      - Open PDF with default viewer"
EOF

echo "  ✓ Created: $LATEX_DIR/Makefile"

echo ""
echo "Creating README with instructions..."
cat > "$LATEX_DIR/README.md" << 'EOF'
# Thesis LaTeX Version

This directory contains the LaTeX version of the thesis, converted from Markdown.

## Structure

```
latex/
├── thesis.tex          # Main thesis file
├── references.bib      # Bibliography (BibTeX format)
├── Makefile           # Build automation
├── chapters/          # Individual chapter files
│   ├── chapter_01.tex
│   ├── chapter_02.tex
│   └── ...
├── figures/           # Place figures here
└── tables/            # Place tables here
```

## Compilation

### Using Make (recommended)

```bash
cd latex
make              # Compile thesis
make view         # Open PDF
make clean        # Remove auxiliary files
make cleanall     # Remove all generated files
```

### Manual compilation

```bash
cd latex
pdflatex thesis
biber thesis
pdflatex thesis
pdflatex thesis   # Second pass for references
```

## Requirements

Install required LaTeX packages:

```bash
sudo apt-get install texlive-full biber
```

Or for minimal installation:

```bash
sudo apt-get install texlive-latex-base texlive-latex-extra \
    texlive-fonts-recommended texlive-science biber
```

## Customization

### Title page

Edit the title page section in `thesis.tex`:
- Author name
- University name
- Department
- Date

### Page layout

Adjust margins in the geometry package settings:

```latex
\geometry{
    left=3.5cm,
    right=2.5cm,
    top=2.5cm,
    bottom=2.5cm
}
```

### Bibliography style

Change citation style by modifying the biblatex package:

```latex
\usepackage[backend=biber,style=numeric,sorting=none]{biblatex}
```

Available styles: `numeric`, `alphabetic`, `authoryear`, `apa`, etc.

## Adding Figures

Place figures in `figures/` directory and include them:

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/my_figure.pdf}
    \caption{Figure caption}
    \label{fig:my_figure}
\end{figure}
```

Reference with: `\cref{fig:my_figure}`

## Adding Tables

```latex
\begin{table}[htbp]
    \centering
    \caption{Table caption}
    \label{tab:my_table}
    \begin{tabular}{lcc}
        \toprule
        Column 1 & Column 2 & Column 3 \\
        \midrule
        Data 1   & Data 2   & Data 3 \\
        \bottomrule
    \end{tabular}
\end{table}
```

## Troubleshooting

### Compilation errors

1. Check syntax errors in `.tex` files
2. Ensure all packages are installed
3. Run `make clean` and recompile

### Missing references

Run compilation sequence: `pdflatex → biber → pdflatex → pdflatex`

### Font issues

Install additional fonts: `sudo apt-get install texlive-fonts-extra`
EOF

echo "  ✓ Created: $LATEX_DIR/README.md"

echo ""
echo "==================================================="
echo "✓ Conversion complete!"
echo ""
echo "LaTeX files created in: $LATEX_DIR"
echo ""
echo "Next steps:"
echo "  1. cd $LATEX_DIR"
echo "  2. make              # Compile thesis"
echo "  3. make view         # View PDF"
echo ""
echo "Note: You may need to:"
echo "  - Install LaTeX: sudo apt-get install texlive-full biber"
echo "  - Add citations to references.bib"
echo "  - Add figures to figures/ directory"
echo "  - Fine-tune formatting in individual chapter files"
echo "==================================================="
EOF

chmod +x "$THESIS_DIR/convert_to_latex.sh"
