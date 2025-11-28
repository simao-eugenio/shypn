# Thesis LaTeX Refactoring Plan

## Status: INITIATED
**Date**: November 25, 2025  
**Objective**: Refactor entire thesis from auto-converted Markdown to proper LaTeX

## Problems in Current LaTeX (Auto-Converted)

### 1. Mathematical Notation
- **Issue**: Formulas in `\begin{lstlisting}...\end{lstlisting}` instead of equations
- **Fix**: Use `equation`, `align`, `align*` environments
- **Example**:
  ```latex
  % BAD (current):
  \begin{lstlisting}
  PN = (P, T, F, W, M₀)
  \end{lstlisting}
  
  % GOOD (refactored):
  \begin{equation}
  \text{PN} = (P, T, F, W, M_0)
  \end{equation}
  ```

### 2. Unicode Characters
- **Issue**: Direct Unicode (→, ≥, ∅, ⊸) not properly rendered
- **Fix**: Use LaTeX commands (`\to`, `\geq`, `\emptyset`, `\multimap`)

### 3. Subscripts/Superscripts
- **Issue**: Unicode subscripts (M₀) instead of LaTeX (M_0)
- **Fix**: Replace all with proper LaTeX math mode

### 4. Set Notation
- **Issue**: Poorly formatted set definitions
- **Fix**: Use `\{`, `\}`, `\mid`, `\in`, `\subseteq`, etc.

### 5. Tables
- **Issue**: Malformed longtable structures from Markdown
- **Fix**: Rewrite as proper `tabular` or `longtable` with booktabs

### 6. Diagrams
- **Issue**: Missing or placeholder diagrams
- **Fix**: Create TikZ Petri net diagrams

### 7. Code Listings
- **Issue**: Biological formulas in lstlisting
- **Fix**: Use mhchem package for chemistry: `\ce{C6H12O6}`

## Refactoring Pattern Template

### Standard Chapter Structure
```latex
%************************************************
\chapter{Chapter Title}
\label{ch:chapter-label}
%************************************************

\section{Section Title}
\label{sec:section-label}

\subsection{Subsection Title}
\label{subsec:subsection-label}

Content...
```

### Mathematical Definitions
```latex
% Single equation
\begin{equation}
\text{BioPN} = (P, T, F, W, M_0, K, \Phi, \Sigma, \Theta, \Delta, \tau, \rho)
\end{equation}

% Multiple aligned equations
\begin{align}
{}^\bullet t &= \{p \in P \mid (p,t) \in F\} && \text{(preset)} \\
t^\bullet &= \{p \in P \mid (t,p) \in F\} && \text{(postset)}
\end{align}

% Description lists
\begin{description}
    \item[$P$] Set of places
    \item[$T$] Set of transitions
\end{description}
```

### Petri Net Diagrams (TikZ)
```latex
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
    node distance=2cm,
    place/.style={circle,draw=blue!75,fill=blue!20,thick,minimum size=10mm},
    transition/.style={rectangle,draw=black!75,fill=black!20,thick,minimum size=8mm},
    >=stealth'
]
    \node[place] (p1) {$p_1$};
    \node[transition, right=of p1] (t1) {$t_1$};
    \node[place, right=of t1] (p2) {$p_2$};
    
    \draw[->,thick] (p1) -- (t1);
    \draw[->,thick] (t1) -- (p2);
    \draw[->,thick,dashed,red] (p3) -- (t1) node[midway,above] {\scriptsize test};
\end{tikzpicture}
\caption{Example Petri net diagram}
\label{fig:example-petri-net}
\end{figure}
```

### Tables (booktabs)
```latex
\begin{table}[htbp]
\centering
\caption{Table caption}
\label{tab:table-label}
\begin{tabular}{lrrr}
\toprule
\textbf{Header 1} & \textbf{Header 2} & \textbf{Header 3} \\
\midrule
Row 1 & 100 & 200 \\
Row 2 & 150 & 250 \\
\bottomrule
\end{tabular}
\end{table}
```

### Chemical Formulas (mhchem)
```latex
% Chemical equation
\ce{C6H12O6 + ATP -> C6H11O9P + ADP}

% Chemical formula
\ce{C10H16N5O13P3}
```

## Chapter Priority Order

### Phase 1: Core Theory (CRITICAL)
1. ✅ **Chapter 4**: Extended Bio-PN Definition (DONE - refactored.tex created)
2. **Chapter 5**: Weak Independence Theory
3. **Chapter 6**: Biochemical Formula Tracking

### Phase 2: Foundation & Integration
4. **Chapter 3**: The Integration Challenge
5. **Chapter 2**: Background and Related Work
6. **Chapter 1**: Introduction

### Phase 3: Validation
7. **Chapter 7**: Validation Through Examples (partially done with 100 BioModels)

### Phase 4: Implementation
8. **Chapter 8**: System Architecture
9. **Chapter 9**: KEGG Integration
10. **Chapter 10**: Parameter Inference
11. **Chapter 11**: Hybrid Simulation Engine

### Phase 5: Evaluation & Synthesis
12. **Chapter 12**: Case Studies
13. **Chapter 13**: Performance Evaluation (partially done with SBML import)
14. **Chapter 14**: Discussion
15. **Chapter 15**: Conclusion and Future Work

## Required LaTeX Packages

### Already in classicthesis-config.tex
- amsmath, amssymb (mathematical notation)
- tikz (diagrams)
- booktabs (tables)
- listings (code)

### Need to Add
```latex
\usepackage[version=4]{mhchem}  % Chemical formulas
\usepackage{algorithm}           % Algorithms
\usepackage{algpseudocode}       % Algorithm pseudocode
\usetikzlibrary{petri}          % Petri net specific TikZ
\usetikzlibrary{arrows.meta}    % Better arrows
\usetikzlibrary{positioning}    % Relative positioning
```

## Refactoring Workflow

### For Each Chapter:
1. **Read original Markdown** (Chapter_XX_Name.md)
2. **Read current LaTeX** (chapter_XX.tex)
3. **Identify issues**:
   - Lstlisting blocks that should be equations
   - Unicode characters
   - Malformed tables
   - Missing diagrams
4. **Refactor section by section**:
   - Convert formulas to proper LaTeX math
   - Create TikZ diagrams where needed
   - Fix tables with booktabs
   - Add cross-references (\ref, \label)
5. **Test compilation**:
   ```bash
   cd doc/thesis/latex
   pdflatex thesis.tex
   ```
6. **Replace old chapter** with refactored version
7. **Commit changes**

## Automation Potential

### Sed/Awk Scripts (Quick Fixes)
```bash
# Replace Unicode arrows
sed -i 's/→/\\to/g' chapter.tex

# Replace Unicode subscripts
sed -i 's/₀/_0/g' chapter.tex
sed -i 's/₁/_1/g' chapter.tex

# Replace lstlisting with equation for simple cases
# (Manual review required)
```

### Manual Work Required
- TikZ diagrams (cannot automate)
- Complex table layouts
- Algorithm environments
- Semantic equation formatting

## Progress Tracking

### Completed
- [x] Chapter 4 refactoring template created
- [x] Refactoring plan documented
- [x] Pattern templates defined

### In Progress
- [ ] Chapter 4 full refactoring (partial - first 4 sections done)

### Pending
- [ ] Chapters 1-3, 5-15 (14 chapters remaining)

## Estimated Effort

- **Chapter 4** (template): ~2 hours (DONE)
- **Per chapter average**: ~1-1.5 hours
- **Total**: ~15-20 hours for all 15 chapters
- **Diagrams**: +5-10 hours (20-30 TikZ figures needed)
- **Total estimated**: 20-30 hours

## Next Steps

1. **Complete Chapter 4** (remaining sections)
2. **Review compilation** with chapter_04_refactored.tex
3. **Refactor Chapter 5** (Weak Independence - critical for thesis)
4. **Create TikZ diagram library** (reusable components)
5. **Batch process** remaining chapters

## Notes

- Keep original .tex files as .tex.backup
- Test compilation after each chapter
- Generate PDF after each major section
- Update bibliography references as needed
- Check figure/table numbering consistency
