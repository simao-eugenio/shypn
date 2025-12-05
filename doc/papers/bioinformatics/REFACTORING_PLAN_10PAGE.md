# Bioinformatics Paper Refactoring Plan (10-Page Maximum)

**Date**: November 28, 2025  
**Location**: `doc/papers/bioinformatics/weak_independence_biopn_bioinformatics.tex`  
**Current Status**: 10 pages (single-column) → **Target: 10 pages (two-column) - STRICT LIMIT**  
**Constraint**: Bioinformatics journal enforces 10-page maximum for Research Articles  
**Strategy**: Compact writing + high-density figures from SHYpn/thesis + integrate Lac Operon into Methods

---

## Overview

Refactor current paper to meet **Bioinformatics 10-page strict limit** while addressing user requirements:

1. ✅ **Two-column format** (Bioinformatics standard)
2. ✅ **Expand introduction** (compact: biological motivation + computational challenge)
3. ✅ **Expand state of the art** (compact: historical perspective + gap analysis)
4. ✅ **Extend formalism** (compact: classical PN review + extended 12-tuple)
5. ✅ **Maintain SBML focus** (central to Methods section)
6. ✅ **Lac Operon central example** (integrated into Methods, not standalone)
7. ✅ **Expand results** (compact: 4 tables + 2 figures)
8. ✅ **Expand future work** (compact: bullet points, not paragraphs)
9. ✅ **35 references** (reduced from 40+, essential citations only)
10. ✅ **Reuse SHYpn/thesis figures** (no new figure creation)

---

## 1. Layout Changes

### Two-Column Format
```latex
\documentclass[twocolumn,11pt]{article}
\usepackage[margin=2cm,columnsep=0.5cm]{geometry}
\usepackage{balance}  % Balance last page columns
```

### Figure Strategy
**Reuse from SHYpn/thesis** (PNG exports from GUI):
- Figure 1: Motivating example (glucose homeostasis) - **from thesis Chapter 3**
- Figure 2: Lac Operon model (PN diagram) - **generate from SHYpn GUI**
- Figure 3: Speedup plot (performance results) - **from thesis Chapter 5**
- Figure 4: Dependency distribution (pie chart) - **from thesis Chapter 5**

**All figures already exist** - no LaTeX TikZ drawing needed.

---

## 2. Page Budget (10 Pages Total)

```
Section                          Pages    Content Density
-----------------------------------------------------------
Abstract                         0.25     250 words (Bioinformatics limit)
Introduction                     1.0      Biological motivation + challenge
Background & Related Work        0.75     Historical + tools + gap analysis
Methods                          3.0      Formalism + Weak Indep + Lac Operon
  - Extended 12-tuple            1.2      (compact notation)
  - Weak Independence Theory     0.8      (Definition + Theorem)
  - Lac Operon Example           0.6      (integrated, not standalone)
  - Algorithm                    0.4      (Algorithm 1 box)
Results                          2.5      4 tables + 2 figures
  - SBML Import Validation       0.4      (Table 1)
  - Dependency Distribution      0.6      (Table 2 + Figure 4)
  - Performance                  0.8      (Figure 3 + scalability)
  - Validation Accuracy          0.7      (Table 3 + case studies)
Discussion                       0.8      Significance + limitations
Future Work                      0.5      Bullet points (stochastic + thermo)
Conclusion                       0.2      Key findings summary
References                       1.0      35 citations (compact format)
-----------------------------------------------------------
Total                           10.0      Maximum allowed by Bioinformatics
```

**Critical Compression Strategies:**
1. **Integrate Lac Operon into Methods** (not separate 1.5-page section)
2. **Compact tables** (small fonts, tight spacing, `\small`)
3. **Multi-panel figures** (4 subplots per figure)
4. **Bullet points for future work** (not prose paragraphs)
5. **Compact bibliography** (`\bibliographystyle{unsrt}` or `ieeetr`)
6. **Balance last page** (avoid half-empty columns)

---

## 3. Introduction (1 page)

### Structure (4 paragraphs + contributions list)

**Para 1: Biological Motivation** (0.2 pages)
- Metabolic pathways exhibit convergence (central metabolism example: glycolysis + gluconeogenesis → glucose)
- Classical PN theory treats all shared places as conflicts
- **Need**: Distinguish biological coupling modes

**Para 2: Computational Challenge** (0.2 pages)
- BioModels: 1,000+ models, average 50-200 species
- Simulation bottleneck: unnecessary serialization
- **Gap**: No formal theory of biological parallelism

**Para 3: Motivating Example** (0.3 pages)
- Figure 1: Glucose homeostasis (4 pathways → glucose)
- All transitions share glucose place → classical: all conflicts
- **Reality**: Convergent production (weakly independent)

**Para 4: Our Contribution** (0.3 pages)
```
1. Weak independence theory for Bio-PNs
2. Extended 12-tuple formalism (Σ, Θ, τ, ρ)
3. Dependency classification algorithm (O(|T|² · |P|))
4. Validation: 100 BioModels, 65% weakly independent, 3.9× speedup
```

---

## 4. Background and Related Work (0.75 pages)

### Structure (compact, essential only)

**4.1 Classical Petri Nets** (0.15 pages)
- 5-tuple definition (one sentence)
- Limitation: Structural conflict ≠ biological conflict

**4.2 Biological Petri Nets** (0.2 pages)
- Pioneering: Reddy (1993), Hofestädt (1994), Matsuno (1998)
- Continuous places + rate functions
- Tools: Snoopy, Cell Illustrator (brief mention)

**4.3 SBML Standard** (0.15 pages)
- Hucka et al., BioModels database
- Our focus: SBML import fidelity

**4.4 Gap Analysis** (0.25 pages)
```
| Feature                  | Classical PN | Bio-PN Tools | SHYpn      |
|--------------------------|--------------|--------------|------------|
| Regulatory arcs          | ✗            | ✓            | ✓          |
| Weak independence        | ✗            | ✗            | ✓          |
| SBML import              | ✗            | Partial      | 100%       |
| Parallel simulation      | ✗            | ✗            | ✓          |
```

**Compression**: No historical timeline, no detailed tool comparison (moved to table).

---

## 5. Methods (3 pages)

### 5.1 Extended Bio-PN Definition (1.2 pages)

**5.1.1 Classical Review** (0.3 pages - COMPACT)
```
Classical PN: 5-tuple (P, T, F, W, M₀)
- Places P, Transitions T, Flow F ⊆ (P×T) ∪ (T×P)
- Weights W: F → ℕ, Initial marking M₀: P → ℕ
Limitation: No biological semantics
```

**5.1.2 Extended 12-tuple** (0.9 pages - COMPACT)
```
Bio-PN: (P, T, F, W, M₀, K, Φ, Σ, Θ, Δ, τ, ρ)

Novel components (compact notation):
- Σ: Regulatory arcs (TEST/INHIBITOR) - Example: (enzyme, reaction)_TEST
- Θ: Environmental exchange - Example: Θ(glucose) = SOURCE
- τ: Transition types - Example: τ(transcription) = STOCHASTIC
- ρ: Biochemical formulas - Example: ρ(lactose) = C₁₂H₂₂O₁₁
```

**Compression**: Table instead of paragraphs for each component.

### 5.2 Weak Independence Theory (0.8 pages)

**Definition 1 (Strong Independence)**: t₁ ⊥ t₂ iff (•t₁ ∪ t₁•) ∩ (•t₂ ∪ t₂•) = ∅

**Definition 2 (Weak Independence)**: t₁ ⊥_w t₂ iff •t₁ ∩ •t₂ = ∅ (no input competition)

**Coupling Modes** (compact list):
1. **Competitive**: •t₁ ∩ •t₂ ≠ ∅ (shared input → conflict)
2. **Convergent**: t₁• ∩ t₂• ≠ ∅, •t₁ ∩ •t₂ = ∅ (shared output → parallel)
3. **Regulatory**: (p, t)_TEST or (p, t)_INHIB (catalyst → parallel)

**Theorem 1 (Correctness)**: Weakly independent transitions commute (proof sketch: 2 lines).

### 5.3 Lac Operon Example (0.6 pages - INTEGRATED, NOT STANDALONE)

**Biological Context** (2 sentences):
- Jacob & Monod (1961): Lactose metabolism regulated by glucose
- Demonstrates all three coupling modes

**Figure 2**: Lac Operon PN (exported from SHYpn GUI)
- 10 places (genes, mRNA, enzymes, metabolites)
- 15 transitions (transcription, translation, metabolism)
- Annotations: COMPETITIVE (RNA pol), CONVERGENT (products), REGULATORY (catalysts)

**Dependency Results** (compact):
- 37% weakly independent (lower due to stochastic gene expression)
- 2.1× speedup (8 cores)

**Compression**: No separate section, integrated into Methods as running example.

### 5.4 Algorithm (0.4 pages)

**Algorithm 1**: Dependency Classification (compact pseudocode box)
- Input: Bio-PN (P, T, F, Σ)
- Output: Classification matrix C[T×T]
- Complexity: O(|T|² · |P|)

---

## 6. Results (2.5 pages)

### 6.1 Dataset (0.2 pages)
- 100 models from BioModels (BIOMD0000000001-BIOMD0000000100)
- Size range: 5-312 species, 3-458 reactions

### 6.2 SBML Import Validation (0.4 pages)
**Table 1**: Import Fidelity (compact)
```
| Metric            | Count | Fidelity |
|-------------------|-------|----------|
| Species imported  | 2,495 | 100%     |
| Reactions         | 2,952 | 100%     |
| Rate laws         | 2,952 | 98.3%    |
| Stoichiometry     | 8,764 | 99.8%    |
```

### 6.3 Dependency Distribution (0.6 pages)
**Table 2**: Classification Results (compact)
```
| Category      | Count | Percentage |
|---------------|-------|------------|
| Strong Indep  | 7,821 | 15.2%      |
| Convergent    | 27,341| 53.1%      |
| Regulatory    | 6,198 | 12.0%      |
| Competitive   | 10,141| 19.7%      |
| Total         | 51,501| 100%       |
Weakly Indep Total: 65.2%
```

**Figure 4**: Pie chart (from thesis) - 4 slices with percentages

### 6.4 Performance (0.8 pages)
**Figure 3**: Speedup plot (from thesis)
- X-axis: Cores (1-16), Y-axis: Speedup (1-8×)
- Average: 3.9× on 8 cores
- Amdahl's law fit (brief analysis)

**Scalability** (compact paragraph):
- Sequential fraction: ~25% (from Amdahl fit)
- Overhead: 10-15% (dependency classification)

### 6.5 Validation Accuracy (0.7 pages)
**Table 3**: False Positive Rates (compact)
```
| Approach         | False Positives | Accuracy |
|------------------|-----------------|----------|
| Classical        | 72%             | 28%      |
| Biological (ours)| 5%              | 95%      |
```

**Case Study** (compact, 1 example only):
- BIOMD0000000010 (MAPK cascade): Classical detects 89 conflicts, biological detects 7 → 82 false positives eliminated

---

## 7. Discussion (0.8 pages)

### 7.1 Significance (0.4 pages)
- **Theoretical**: First formal theory of biological parallelism in PNs
- **Practical**: 3.9× speedup on real BioModels
- **Validation**: 95% accuracy (vs 28% classical)

### 7.2 Limitations (0.4 pages)
- **Stochastic**: Current weak independence for ODEs only (extension proposed in Future Work)
- **Thermodynamics**: No ΔG feasibility checking (future)
- **Parameter estimation**: Manual (automation future)

---

## 8. Future Work (0.5 pages - BULLET POINTS)

### 8.1 Stochastic Weak Independence
- **Biological motivation**: Molecular collisions occur simultaneously in solution (not sequential)
- **Approach**: τ-leaping + weak independence
- **Hypothesis**: Convergent/regulatory transitions → independent Poisson processes
- **Expected speedup**: 2-4× for hybrid models

### 8.2 Thermodynamic Analyzer
- Integrate eQuilibrator (Flamholz et al.)
- Check ΔG feasibility of reaction directions
- Reject thermodynamically infeasible pathways

### 8.3 Automated Parameter Estimation
- Parallel PSO leveraging weak independence
- Target: 10-100× faster than sequential optimization

### 8.4 Distributed Simulation
- MPI for whole-cell models (10,000+ species)
- GPU acceleration (CUDA kernels)

**Compression**: Bullet points only, no detailed paragraphs.

---

## 9. References (35 Citations - COMPACT)

### Categories (reduced from 40+)

**Historical Biology** (5):
1. Jacob & Monod (1961) - Lac operon
2. Alberts et al. - Molecular Biology of the Cell
3. Nelson & Cox - Lehninger Biochemistry
4. Fell - Understanding the Control of Metabolism
5. Palsson - Systems Biology

**Petri Net Theory** (5):
6. Reisig - Petri Nets
7. Murata (1989) - PN survey
8. Peterson - Petri Net Theory
9. Desel & Esparza - Free Choice PNs
10. Chaouiya - PN modeling of biological networks

**Bio-PN Tools** (5):
11. Reddy (1993) - Petri nets in biochemistry
12. Hofestädt (1994) - Metabolic pathways
13. Matsuno (1998) - Hybrid PNs
14. Heiner et al. - Snoopy
15. Nagasaki et al. - Cell Illustrator

**SBML** (5):
16. Hucka et al. (2003) - SBML Level 1
17. Malik-Sheriff et al. (2020) - BioModels 2020
18. Keating et al. (2020) - SBML Level 3
19. Le Novère et al. (2009) - BioModels database
20. Finney & Hucka (2003) - SBML specification

**Simulation** (5):
21. Gillespie (1977) - SSA
22. Gillespie (2001) - τ-leaping
23. Cao et al. (2006) - Efficient SSA
24. Higham (2008) - Stochastic simulation review
25. Hoops et al. - COPASI

**Metabolic Analysis** (5):
26. Orth et al. - FBA
27. Varma & Palsson (1994) - FBA method
28. Schellenberger et al. - COBRApy
29. Edwards & Palsson (2000) - Metabolic capabilities
30. Kauffman et al. (2003) - FBA applications

**Parallel Computing** (3):
31. Amdahl (1967) - Amdahl's law
32. Gustafson (1988) - Reevaluation
33. Wilkinson & Allen - Parallel Programming

**Thermodynamics** (2):
34. Flamholz et al. (2012) - eQuilibrator
35. Noor et al. (2013) - Thermodynamics of metabolic networks

**Total**: 35 references (vs 15 current, 40+ original plan)

---

## 10. Implementation Plan (8 Phases)

### Phase 1: Layout Conversion (1 hour)
- Change to two-column format
- Update geometry settings
- Test compilation

### Phase 2: Introduction Expansion (1.5 hours)
- Add biological motivation paragraph
- Add computational challenge paragraph
- Enhance motivating example

### Phase 3: Background Compression (1 hour)
- Convert tool comparison to table
- Remove detailed timeline
- Keep gap analysis

### Phase 4: Formalism Compression (1.5 hours)
- Add compact classical PN review
- Convert 12-tuple to table format
- Remove verbose explanations

### Phase 5: Lac Operon Integration (1 hour)
- Move Lac Operon into Methods (not standalone)
- Export Figure 2 from SHYpn GUI
- Add compact dependency results

### Phase 6: Results Expansion (2 hours)
- Add per-model breakdown (Table 2 enhancement)
- Add scalability analysis
- Export Figure 3 & 4 from thesis

### Phase 7: Future Work Compression (0.5 hours)
- Convert to bullet points
- Remove verbose paragraphs
- Keep stochastic detail (key innovation)

### Phase 8: References & Final Polish (0.5 hours)
- Add 20 new references (35 total)
- Balance last page columns
- Check 10-page limit

**Total Time**: 8.5 hours (reduced from 18 hours)

---

## 11. Figure Extraction from SHYpn/Thesis

### Figure 1: Glucose Homeostasis
**Source**: Thesis Chapter 3, Figure 3.4  
**Action**: Export PNG from thesis PDF (page 47)  
**Size**: 2-column width (180mm)  
**Caption**: "Motivating example: Four pathways converge to produce glucose..."

### Figure 2: Lac Operon Model
**Source**: Generate from SHYpn GUI  
**Action**:
1. Open `examples/03_lac_operon_regulation.py` in SHYpn
2. GUI → Export → PNG (high resolution)
3. Annotate coupling modes (COMP/CONV/REG)
**Size**: 2-column width (180mm)  
**Caption**: "Lac operon Petri net model with 10 places, 15 transitions..."

### Figure 3: Speedup Plot
**Source**: Thesis Chapter 5, Figure 5.8  
**Action**: Export PNG from thesis PDF (page 103)  
**Size**: Single column width (85mm)  
**Caption**: "Parallel simulation speedup vs number of cores..."

### Figure 4: Dependency Distribution
**Source**: Thesis Chapter 5, Figure 5.6  
**Action**: Export PNG from thesis PDF (page 98)  
**Size**: Single column width (85mm)  
**Caption**: "Distribution of dependency types across 100 BioModels..."

**Total**: 4 figures, all reused (no LaTeX drawing needed)

---

## 12. Success Criteria

### Page Limit Check
```bash
pdflatex weak_independence_biopn_bioinformatics.tex
pdfinfo weak_independence_biopn_bioinformatics.pdf | grep Pages
# Output must be: Pages: 10 (or fewer)
```

### Content Density
- Abstract: 250 words (Bioinformatics limit)
- References: 35 citations (essential only)
- Figures: 4 (all from SHYpn/thesis)
- Tables: 4 (compact formatting)

### Bioinformatics Compliance
- Two-column format: ✓
- 11pt font: ✓
- Balanced last page: ✓
- Compact bibliography: ✓

---

## 13. Next Steps

1. **Start Phase 1**: Convert to two-column layout
2. **Compile**: Check page count after each phase
3. **Iterate**: If exceeds 10 pages, compress further
4. **Extract figures**: From thesis PDF and SHYpn GUI
5. **Final review**: Ensure all 10 requirements met within limit

**Critical**: Monitor page count continuously. Bioinformatics **strictly enforces** 10-page limit.
