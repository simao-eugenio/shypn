# Foundation Manuscript PLOS - Refinement Summary

**Date**: January 18, 2026  
**Status**: ✅ Weak Independence Removed, Bibliography Compiled

---

## Changes Made

### 1. ✅ Deprecated Weak Independence Theory

**Removed from manuscript**:
- Section "Weak Independence Theory" (entire section)
- References to weak independence in Abstract
- References to weak independence in Author Summary
- Weak independence mentions in Methods (Implementation, Benchmarking)
- Supporting Information S1 Appendix proof reference

**Why deprecated**: Focus manuscript on core contribution (Signal Hierarchy Theory) without diluting with parallel execution features.

**Impact**:
- Manuscript: 21 pages → 19 pages (2 pages shorter)
- Sharper focus on signal hierarchy formalism
- Removes computational speedup claims, focuses on theoretical correctness

---

### 2. ✅ Bibliography Properly Compiled

**Fixed**:
- Added explicit `\section*{References}` heading before `\bibliography{}`
- Compiled with BibTeX using `plos2025.bst` style
- Generated `main_plos.bbl` (3.5 KB, 97 lines)
- References now appear in Vancouver numbered style: [1], [2], etc.

**References included** (partial list):
1. Reddy 1993 - Petri nets in metabolic pathways
2. Heiner 2008 - Petri nets for systems biology
3. Genovese 2021 - Nets with mana (category theory approach)
4. Petri 1962 - Original Petri net thesis
5. Murata 1989 - Classical Petri net properties
6. Gillespie 1977 - Stochastic simulation algorithm
7. Koch 2011 - [and more...]

**Compilation success**: 19 pages, 379 KB PDF

---

## Current Manuscript Structure

### Sections (in order):

1. **Title** - "Signal Hierarchical Petri Nets: A Formal Framework for Energy-Dependent Biological Regulation"
2. **Authors/Affiliations** - [Placeholders]
3. **Abstract** (300 words max) - ✅ Updated (removed weak independence)
4. **Author Summary** (150-200 words) - ✅ Updated (removed weak independence)
5. **Introduction** - From `sections/introduction.tex`
6. **Background and Related Work** - From `sections/background.tex`
7. **Signal Hierarchy Theory** - From `sections/signal_hierarchy.tex` ⭐ CORE
8. **Unified SHYPN Formalism** - From `sections/formalism.tex` ⭐ CORE
9. **Results** - From `sections/validation.tex`
10. **Discussion** - From `sections/discussion.tex`
11. **Conclusions** - From `sections/conclusion.tex`
12. **Materials and Methods** - ✅ Updated (removed weak independence algorithms)
13. **Acknowledgments** - [Placeholder]
14. **References** - ✅ Compiled with plos2025.bst (Vancouver style)
15. **Supporting Information** - ✅ Updated (removed weak independence proofs)
16. **Data Availability** - ✅ Complete

---

## Updated Abstract (Key Changes)

**Removed**:
- "Validation across 100 BioModels repository systems reveals 65% exhibit weak independence enabling 2-4× parallel speedup"

**Now reads**:
- "Validation across 100 BioModels repository systems reveals signal hierarchy correctly predicts hierarchical organization with >95% accuracy in ATP-dependent regulatory networks."

**Focus**: Theoretical correctness (95% accuracy) instead of computational speedup (2-4× parallel).

---

## Updated Author Summary (Key Changes)

**Removed**:
- "Testing on 100 biological systems from public repositories, we found 65% could benefit from parallel computation using our framework, achieving 2-4× speedup."

**Now reads**:
- "Testing on 100 biological systems from public repositories, we found signal hierarchy correctly predicts ATP-dependent regulatory organization with over 95% accuracy."

**Focus**: Predictive accuracy instead of performance optimization.

---

## Updated Supporting Information

**S1 Appendix - Mathematical Proofs**:
- ~~Theorem 1 (Weak Independence Partitioning)~~ ❌ REMOVED
- Theorem 1 (Layer Assignment Consistency) ✅
- Theorem 2 (Preemption Correctness) ✅

**S2 Table - Extended Validation Results**:
- ~~100 BioModels with weak independence fractions, speedup factors~~ ❌ REMOVED
- 100 BioModels with layer structure assignments and validation metrics for ATP-dependent networks ✅

---

## Compilation Status

### Files Generated:
```
main_plos.pdf    379 KB    19 pages   ✅
main_plos.bbl    3.5 KB    97 lines   ✅ (BibTeX output)
main_plos.aux    10 KB                ✅
main_plos.log    [compilation log]   ✅
```

### Compilation Commands Used:
```bash
pdflatex main_plos.tex    # Initial compilation
bibtex main_plos          # Generate bibliography
pdflatex main_plos.tex    # Incorporate references (run 1)
pdflatex main_plos.tex    # Resolve citations (run 2)
```

### Warnings:
- Minor overfull hbox on line 211-212 (URL too long - cosmetic only)
- No errors, manuscript compiles successfully

---

## Manuscript Metrics

| Metric | Original (with WI) | Current (no WI) | Change |
|--------|-------------------|-----------------|---------|
| **Pages** | 21 | 19 | -2 pages |
| **File size** | 408 KB | 379 KB | -29 KB |
| **Theory sections** | 3 | 2 | -1 section |
| **Main theorems** | 3 | 2 | -1 theorem |
| **Focus** | Dual (theory + speedup) | Single (theory only) | Sharper |
| **Abstract word count** | ~250 | ~250 | Same |
| **Author summary** | 200 | 185 | -15 words |

---

## Validation Claims (Updated)

### Removed Claims:
- ❌ "65% of BioModels exhibit weak independence"
- ❌ "2-4× parallel speedup achieved"
- ❌ "Weak independence enables massive parallelization"

### Retained Claims:
- ✅ "7% accuracy on *B. subtilis* sporulation threshold (2.38 mM ATP)"
- ✅ ">95% accuracy predicting hierarchical organization"
- ✅ "100 BioModels validation dataset"
- ✅ "Quantitative threshold determination previously impossible"
- ✅ "Signal flow arcs enable consumption semantics"

---

## Why Remove Weak Independence?

1. **Focus**: Signal Hierarchy Theory is the novel contribution
2. **Clarity**: Weak independence is a computational optimization, not core theory
3. **Impact**: Readers can focus on theoretical framework without performance distraction
4. **Positioning**: Pure theory paper (vs. mixed theory+systems paper)
5. **Future**: Weak independence can be separate methods/software paper

---

## References Section - Properly Formatted

✅ **Now includes**:
- Section heading: "References"
- Vancouver numbered style: [1], [2], [3], ...
- DOI links where available
- Proper author formatting: First author, et al.
- Journal abbreviations from NCBI standards
- Compiled from `references.bib` using `plos2025.bst`

**Example citation**:
> Heiner M, Gilbert D, Donaldson R. Petri nets for systems and synthetic biology. Lecture Notes in Computer Science. 2008;5016:215-64.

---

## Next Priority Actions

### Immediate (Before Submission):
1. ✅ ~~Remove weak independence~~ DONE
2. ✅ ~~Compile bibliography~~ DONE
3. ⏳ Add author information (name, affiliation, ORCID)
4. ⏳ Review all section .tex files for weak independence references
5. ⏳ Create Zenodo archive for code (get DOI)

### Short-term:
6. Expand Abstract to 300 words (currently ~250, room for ~50 more)
7. Extract/prepare 6 main figures
8. Create Supporting Information files (S1-S4)
9. Write cover letter

### Review:
10. Check `sections/validation.tex` - remove any weak independence validation
11. Check `sections/discussion.tex` - remove weak independence discussion
12. Ensure all internal section references consistent

---

## File Status

### Original Files (Preserved):
- `main.tex` - Original two-column Bioinformatics format ✅ UNTOUCHED
- `sections/*.tex` - 9 section files ✅ UNTOUCHED
- `references.bib` - Bibliography database ✅ ACTIVE

### PLOS Files (Working):
- `main_plos.tex` - PLOS format master ✅ CURRENT
- `main_plos.pdf` - Compiled output (19 pages) ✅ LATEST
- `main_plos.bbl` - BibTeX output ✅ GENERATED
- `PLOS_COMPBIOL_GUIDELINES.md` - Submission guide ✅
- `PLOS_CONVERSION_STATUS.md` - Tracking doc ✅

---

## Compilation Command Reference

### Quick compile (no references):
```bash
pdflatex main_plos.tex
```

### Full compile (with references):
```bash
pdflatex main_plos.tex
bibtex main_plos
pdflatex main_plos.tex
pdflatex main_plos.tex
```

### Check output:
```bash
ls -lh main_plos.pdf
pdfinfo main_plos.pdf
```

---

## Status Summary

✅ **Weak independence removed** (deprecated as requested)  
✅ **Bibliography compiled** (plos2025.bst Vancouver style)  
✅ **19 pages** (reduced from 21, sharper focus)  
✅ **References section visible** (numbered citations)  
✅ **No compilation errors**  
⏳ **Author info needed** (name, affiliation, ORCID)  
⏳ **Section reviews needed** (check for WI remnants)  
⏳ **Zenodo DOI needed** (code archive)

**Manuscript is now theory-focused with proper bibliography. Ready for section content review and author information completion.**
