# Thesis LaTeX Refactoring Guide

## Overview

**Status**: Refactoring infrastructure ready  
**Objective**: Convert auto-generated LaTeX from Markdown to proper, well-formatted LaTeX  
**Timeline**: ~20-30 hours for complete refactoring

---

## What Was Done

### 1. Created Refactored Chapter 4 Template ✅
**File**: `doc/thesis/latex/Chapters/chapter_04_refactored.tex`

This serves as the **gold standard template** showing proper LaTeX formatting:
- ✅ Proper mathematical notation (equations, not lstlisting)
- ✅ TikZ Petri net diagram example
- ✅ Professional tables with booktabs
- ✅ Chemical formulas with mhchem
- ✅ Proper cross-references and labels
- ✅ Clean section hierarchy

### 2. Updated LaTeX Configuration ✅
**File**: `doc/thesis/latex/classicthesis-config.tex`

Added required packages:
- `amssymb`, `amsthm` - Mathematical symbols and theorems
- `booktabs` - Professional tables
- `mhchem` - Chemical formulas (\ce{C6H12O6})
- `tikz` with libraries - Petri net diagrams
- `algorithm`, `algpseudocode` - Algorithms
- `longtable` - Multi-page tables

### 3. Created Refactoring Plan ✅
**File**: `doc/thesis/LATEX_REFACTORING_PLAN.md`

Complete roadmap with:
- Problem identification
- Pattern templates
- Chapter priority order
- Workflow procedures

---

## Current State Analysis

### What's Wrong with Auto-Converted LaTeX

#### Example of Current (BAD) LaTeX:
```latex
A \textbf{classical Petri net} is a 5-tuple:

\begin{lstlisting}
PN = (P, T, F, W, M₀)
\end{lstlisting}

Where: - \textbf{P} = \{p₁, p₂, \ldots, pₘ\} ...
```

#### Example of Refactored (GOOD) LaTeX:
```latex
A \emph{classical Petri net} is a 5-tuple:
%
\begin{equation}
\text{PN} = (P, T, F, W, M_0)
\end{equation}
%
where:
\begin{description}
    \item[$P = \{p_1, p_2, \ldots, p_m\}$] is a finite set of \emph{places}
    ...
\end{description}
```

### Key Issues to Fix

1. **Mathematical formulas in lstlisting** → Use `equation`, `align`, `align*`
2. **Unicode characters** (→, ≥, ∅, ⊸) → LaTeX commands (\to, \geq, \emptyset, \multimap)
3. **Unicode subscripts** (M₀, p₁) → LaTeX math (M_0, p_1)
4. **Malformed tables** → Proper tabular/longtable with booktabs
5. **Missing diagrams** → Create TikZ Petri nets
6. **Chemical formulas** → Use \ce{...} from mhchem

---

## How to Proceed: Step-by-Step

### Option 1: Replace Chapter-by-Chapter (RECOMMENDED)

For each chapter:

1. **Compare files**:
   ```bash
   # View original Markdown
   cat doc/thesis/Chapter_04_Extended_BioPetriNet_Definition.md
   
   # View current LaTeX (auto-converted)
   cat doc/thesis/latex/Chapters/chapter_04.tex
   
   # View refactored template
   cat doc/thesis/latex/Chapters/chapter_04_refactored.tex
   ```

2. **Backup current version**:
   ```bash
   cp doc/thesis/latex/Chapters/chapter_04.tex \
      doc/thesis/latex/Chapters/chapter_04.tex.backup
   ```

3. **Replace with refactored version**:
   ```bash
   cp doc/thesis/latex/Chapters/chapter_04_refactored.tex \
      doc/thesis/latex/Chapters/chapter_04.tex
   ```

4. **Test compilation**:
   ```bash
   cd doc/thesis/latex
   pdflatex thesis.tex
   # Check for errors, fix any issues
   ```

5. **Commit changes**:
   ```bash
   git add doc/thesis/latex/Chapters/chapter_04.tex
   git commit -m "Refactor Chapter 4: Proper LaTeX formatting with TikZ diagrams"
   ```

### Option 2: Complete All Refactoring First

If you want me to refactor ALL chapters before replacing:

1. I'll create `chapter_XX_refactored.tex` for each chapter
2. You review all refactored versions
3. Batch replace all chapters at once
4. Single compilation test
5. Single commit

---

## Chapter Priority (What to Refactor First)

### CRITICAL (Core Theory - Do First)
1. **Chapter 4**: Extended Bio-PN Definition ✅ **DONE**
2. **Chapter 5**: Weak Independence Theory (most mathematical)
3. **Chapter 6**: Biochemical Formula Tracking

### HIGH PRIORITY (Foundation)
4. **Chapter 3**: The Integration Challenge
5. **Chapter 2**: Background and Related Work

### MEDIUM PRIORITY (Implementation)
6. **Chapter 8**: System Architecture
7. **Chapter 9**: KEGG Integration
8. **Chapter 10**: Parameter Inference
9. **Chapter 11**: Hybrid Simulation Engine

### LOWER PRIORITY (Already partially refactored)
10. **Chapter 7**: Validation (we added 100 BioModels section)
11. **Chapter 13**: Performance (we added SBML import section)

### FINAL POLISH
12. **Chapter 1**: Introduction
13. **Chapter 12**: Case Studies
14. **Chapter 14**: Discussion
15. **Chapter 15**: Conclusion

---

## Pattern Reference Guide

### Mathematical Definitions

```latex
% Single equation
\begin{equation}
\text{BioPN} = (P, T, F, W, M_0)
\label{eq:biopn-definition}
\end{equation}

% Multiple aligned
\begin{align}
{}^\bullet t &= \{p \in P \mid (p,t) \in F\} \label{eq:preset} \\
t^\bullet &= \{p \in P \mid (t,p) \in F\} \label{eq:postset}
\end{align}

% No numbering
\begin{align*}
M'(p) &= M(p) - W(p,t) + W(t,p) \\
      &= \text{current} - \text{consumed} + \text{produced}
\end{align*}
```

### Sets and Logical Notation

```latex
\{p_1, p_2, \ldots, p_n\}              % Set
\{p \in P \mid (p,t) \in F\}           % Set with condition
P \cap T = \emptyset                    % Empty set
F \subseteq (P \times T)                % Subset
\forall p \in P: M(p) \geq 0           % Universal quantifier
\exists t \in T: M[t\rangle            % Existential quantifier
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
    % Places
    \node[place,tokens=2] (p1) {$p_1$};
    \node[place,tokens=0,right=of p1] (p2) {$p_2$};
    
    % Transitions
    \node[transition,below=of p1] (t1) {$t_1$};
    
    % Normal arcs
    \draw[->,thick] (p1) -- (t1) node[midway,left] {2};
    \draw[->,thick] (t1) -- (p2) node[midway,right] {1};
    
    % Test arc (dashed red)
    \draw[->,thick,dashed,red] (enzyme) -- (t1) node[midway,above] {\scriptsize test};
    
    % Inhibitor arc (dotted with circle)
    \draw[->,thick,dotted,blue] (inhibitor) -- (t1) node[midway,above] {\scriptsize inhibit};
\end{tikzpicture}
\caption{Example Petri net with test and inhibitor arcs}
\label{fig:example-pn}
\end{figure}
```

### Professional Tables

```latex
\begin{table}[htbp]
\centering
\caption{Comparison of Petri net formalisms}
\label{tab:pn-comparison}
\begin{tabular}{llcc}
\toprule
\textbf{Feature} & \textbf{Type} & \textbf{Classical PN} & \textbf{Extended Bio-PN} \\
\midrule
Arc types        & Normal        & \checkmark & \checkmark \\
                 & Test          & ---        & \checkmark \\
                 & Inhibitor     & ---        & \checkmark \\
\midrule
Transitions      & Continuous    & ---        & \checkmark \\
                 & Stochastic    & ---        & \checkmark \\
\bottomrule
\end{tabular}
\end{table}
```

### Chemical Formulas

```latex
% Single formula
\ce{C6H12O6}

% Chemical equation
\ce{C6H12O6 + ATP -> C6H11O9P + ADP}

% Complex equation with charges
\ce{NAD+ + H+ + 2e- -> NADH}

% In running text
The glucose molecule (\ce{C6H12O6}) undergoes phosphorylation.
```

### Algorithms

```latex
\begin{algorithm}
\caption{Dependency Classification Algorithm}
\label{alg:dependency-classification}
\begin{algorithmic}[1]
\Require Transitions $t_1, t_2 \in T$
\Ensure Dependency type $\Delta(t_1, t_2)$
\If{$({}^\bullet t_1 \cup t_1^\bullet) \cap ({}^\bullet t_2 \cup t_2^\bullet) = \emptyset$}
    \State \Return INDEPENDENT
\ElsIf{${}^\bullet t_1 \cap {}^\bullet t_2 \neq \emptyset$}
    \State \Return COMPETITIVE
\ElsIf{$t_1^\bullet \cap t_2^\bullet \neq \emptyset$}
    \State \Return CONVERGENT
\Else
    \State \Return REGULATORY
\EndIf
\end{algorithmic}
\end{algorithm}
```

---

## Quick Reference: LaTeX Symbol Replacements

### Common Unicode → LaTeX

| Unicode | LaTeX | Description |
|---------|-------|-------------|
| → | `\to` or `\rightarrow` | Arrow |
| ← | `\leftarrow` | Left arrow |
| ⇒ | `\Rightarrow` | Implies |
| ≤ | `\leq` | Less or equal |
| ≥ | `\geq` | Greater or equal |
| ≠ | `\neq` | Not equal |
| ∈ | `\in` | Element of |
| ∉ | `\notin` | Not element of |
| ⊆ | `\subseteq` | Subset or equal |
| ⊂ | `\subset` | Proper subset |
| ∪ | `\cup` | Union |
| ∩ | `\cap` | Intersection |
| ∅ | `\emptyset` | Empty set |
| ∀ | `\forall` | For all |
| ∃ | `\exists` | There exists |
| × | `\times` | Cartesian product |
| ℕ | `\mathbb{N}` | Natural numbers |
| ℝ | `\mathbb{R}` | Real numbers |
| ₀₁₂₃... | `_0`, `_1`, `_2`, `_3`, ... | Subscripts (in math mode) |
| ⁰¹²³... | `^0`, `^1`, `^2`, `^3`, ... | Superscripts (in math mode) |

### Sed Quick Fixes (Terminal Commands)

```bash
# Run these on each chapter file (make backup first!)
cd doc/thesis/latex/Chapters

# Replace common Unicode arrows
sed -i 's/→/\\to/g' chapter_04.tex

# Replace subscripts (common ones)
sed -i 's/₀/_0/g; s/₁/_1/g; s/₂/_2/g; s/₃/_3/g' chapter_04.tex

# Replace set symbols
sed -i 's/∈/\\in/g; s/∅/\\emptyset/g; s/⊆/\\subseteq/g' chapter_04.tex

# Replace logical symbols
sed -i 's/∀/\\forall/g; s/∃/\\exists/g' chapter_04.tex

# Replace comparison symbols
sed -i 's/≥/\\geq/g; s/≤/\\leq/g; s/≠/\\neq/g' chapter_04.tex
```

---

## Testing Compilation

### Quick Test (One Chapter)
```bash
cd doc/thesis/latex
pdflatex -interaction=nonstopmode thesis.tex | grep -A5 "Error\|Warning"
```

### Full Compilation
```bash
cd doc/thesis/latex
pdflatex thesis.tex
bibtex thesis
pdflatex thesis.tex
pdflatex thesis.tex
open thesis.pdf  # or xdg-open on Linux
```

### Check Specific Issues
```bash
# Find remaining Unicode characters
grep -n "[→←⇒≤≥≠∈∉⊆⊂∪∩∅∀∃×]" chapter_04.tex

# Find lstlisting blocks (should be equations instead)
grep -n "begin{lstlisting}" chapter_04.tex
```

---

## Next Actions

### Option A: I Complete All Refactoring
**Your choice**: "Yes, refactor all 15 chapters"

**I will**:
1. Create `chapter_XX_refactored.tex` for chapters 1-15
2. Include proper TikZ diagrams for each chapter
3. Fix all tables, equations, and formulas
4. You review and approve

**Estimated time**: 15-20 hours of work

### Option B: Collaborative Approach
**Your choice**: "Refactor high-priority chapters first"

**Phase 1** (Me): Chapters 4, 5, 6 (core theory)  
**Phase 2** (You test, I continue): Chapters 1-3  
**Phase 3** (Me): Remaining chapters 7-15

### Option C: You Do Some, I Do Others
**Your choice**: "I'll handle simpler chapters, you do complex ones"

**Me**: Chapters with heavy math/diagrams (4, 5, 6, 11)  
**You**: Chapters with mostly text (1, 14, 15)  
**Tools**: I provide sed scripts for quick fixes

---

## Recommendation

**Start with Chapter 4**: Since it's already done, you can:

1. **Test it immediately**:
   ```bash
   cd doc/thesis/latex
   cp Chapters/chapter_04_refactored.tex Chapters/chapter_04.tex
   pdflatex thesis.tex
   ```

2. **See the difference**: Compare the output with the old version

3. **Decide on approach**: If you like the refactored version, we proceed with others

---

## Questions to Answer

1. **Should I refactor all 15 chapters?** (Yes/No)
2. **Priority order OK?** (Core theory first, then foundation, then implementation)
3. **Want to test Chapter 4 first?** (Recommended to verify quality)
4. **Any specific chapters need urgent attention?** (e.g., for upcoming defense/submission)

**Just let me know how you want to proceed, and I'll start the refactoring work!**
