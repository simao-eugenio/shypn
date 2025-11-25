# Thesis Figures Inventory - SHYpn Model Diagrams

**Purpose**: Complete catalog of Petri net diagrams in thesis chapters that should be generated from .shy models instead of manual TikZ code.

**Status**: Planning phase - models to be created/organized under `workspace/projects/thesis/`

---

## Summary Statistics

- **Total figures identified**: 11 Petri net diagrams
- **Existing .shy models available**: 3 (lac operon, hexokinase, glycolysis)
- **New models needed**: 8 (conceptual examples)
- **Chapters affected**: 3, 4, 5 (theory and foundations)

---

## Chapter 3: Heterogeneous Petri Nets (1 figure)

### Figure 3.1: Lac Operon Network Topology
- **Label**: `fig:lac-topology`
- **Location**: `chapter_03_refactored.tex`, lines 380-424
- **Description**: Complete lac operon regulation showing heterogeneous arc types
  - Places: Glucose, Lactose, cAMP, CRP, CRP-cAMP, gene, Repressor, mRNA, BetaGal
  - Transitions: 9 transitions (T2, T5, T6, T9, etc.)
  - Arc types: Normal (solid), Test/catalytic (dashed green), Inhibitor (dotted red)
- **Biological Context**: Demonstrates arc-level regulation (glucose inhibits cAMP, CRP-cAMP activates transcription, repressor blocks)
- **Model Status**: ✅ **EXISTS** - `workspace/projects/Biochemical-Examples/17_Lac_Operon_Regulation/model.shy`
- **Action Required**: 
  1. Symlink to `workspace/projects/thesis/biological/lac_operon.shy`
  2. Validate layout in GUI for publication quality
  3. Export to PDF

---

## Chapter 4: Computational Model (1 figure)

### Figure 4.1: Enzyme-Catalyzed Reaction with Test Arc
- **Label**: `fig:enzyme-catalyzed-example`
- **Location**: `chapter_04_refactored.tex`, lines 357-386
- **Description**: Hexokinase-catalyzed glucose phosphorylation
  - Places: Glucose, ATP, Hexokinase, G6P, ADP
  - Transition: t1 (glucose + ATP → G6P + ADP)
  - Test arc: Hexokinase → t1 (catalyst, non-consumptive)
- **Pedagogical Purpose**: Introduce test arc semantics (enabling without consumption)
- **Model Status**: ✅ **EXISTS** - `workspace/projects/Biochemical-Examples/03_Hexokinase_MM/model.shy`
- **Action Required**:
  1. Verify this model matches pedagogical figure (may be more complex)
  2. Consider creating simplified version: `workspace/projects/thesis/conceptual/enzyme_catalyzed.shy`
  3. Export to PDF

---

## Chapter 5: Weak Independence Theory (9 figures)

### Figure 5.1: Strong Independence Example
- **Label**: `fig:strong-independence`
- **Location**: `chapter_05_refactored.tex`, lines 74-102
- **Description**: Two completely disjoint subnets
  - Left subnet: P1 → t1 → P2
  - Right subnet: P3 → t2 → P4
  - No shared places (demonstrates classical strong independence)
- **Pedagogical Purpose**: Baseline for independence theory
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/strong_independence.shy`
  - 2 transitions, 4 places
  - Minimal example showing no dependencies

### Figure 5.2: Convergent Synthesis Example
- **Label**: `fig:convergent-example`
- **Location**: `chapter_05_refactored.tex`, lines 117-141
- **Description**: Two reactions producing same metabolite
  - Glucose → t1 → Pyruvate
  - Lactate → t2 → Pyruvate
  - Shared output place (Pyruvate) violates strong independence
- **Pedagogical Purpose**: Show biological convergence pattern
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/convergent_synthesis.shy`
  - 2 transitions, 3 places
  - Demonstrates Mode 2 (convergent coupling)

### Figure 5.3: Shared Catalyst Example
- **Label**: `fig:shared-catalyst-example`
- **Location**: `chapter_05_refactored.tex`, lines 146-176
- **Description**: PGI enzyme catalyzes two reactions
  - S1 → t1 → P1 (with PGI test arc)
  - S2 → t2 → P2 (with PGI test arc)
  - Shared catalyst place (PGI) violates strong independence
- **Pedagogical Purpose**: Enzyme reuse in metabolism
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/shared_catalyst.shy`
  - 2 transitions, 5 places (including enzyme)
  - Test arcs from enzyme to both transitions

### Figure 5.4: Feedback Regulation Example
- **Label**: `fig:feedback-regulation-example`
- **Location**: `chapter_05_refactored.tex`, lines 181-209
- **Description**: ATP has dual role (substrate and inhibitor)
  - Glc → HK → G6P → PFK → F-1,6-BP
  - ATP → HK (substrate, normal arc)
  - ATP ⇢ PFK (inhibitor, dotted arc)
  - Shared place with different arc types
- **Pedagogical Purpose**: Complex regulatory patterns
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/feedback_regulation.shy`
  - 2 transitions, 5 places
  - Demonstrates heterogeneous arc types on same place

### Figure 5.5: Conflict Mode (Mode 1)
- **Label**: `fig:conflict-mode`
- **Location**: `chapter_05_refactored.tex`, lines 349-370
- **Description**: Resource competition pattern
  - ATP → t1 → P1
  - ATP → t2 → P2
  - Shared input place (conflict, mutual exclusion)
- **Pedagogical Purpose**: Define Mode 1 of weak independence
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/conflict_mode.shy`
  - 2 transitions, 3 places
  - Clear conflict visualization with tokens

### Figure 5.6: Convergent Mode (Mode 2)
- **Label**: `fig:convergent-mode`
- **Location**: `chapter_05_refactored.tex`, lines 391-413
- **Description**: Superposition pattern
  - S1 → t1 → P
  - S2 → t2 → P
  - Shared output place (additive effects)
- **Pedagogical Purpose**: Define Mode 2 of weak independence
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/convergent_mode.shy`
  - 2 transitions, 3 places
  - Effects superimpose on output place

### Figure 5.7: Regulatory Mode (Mode 3)
- **Label**: `fig:regulatory-mode`
- **Location**: `chapter_05_refactored.tex`, lines 434-462
- **Description**: Enzyme reuse pattern
  - S1 → t1 → P1 (with Enzyme test arc)
  - S2 → t2 → P2 (with Enzyme test arc)
  - Shared catalyst (non-consumptive)
- **Pedagogical Purpose**: Define Mode 3 of weak independence
- **Model Status**: ❌ **MISSING** - needs creation
- **Action Required**: Create `workspace/projects/thesis/conceptual/regulatory_mode.shy`
  - 2 transitions, 5 places
  - Test arcs demonstrate catalyst reuse

### Figure 5.8: Glycolysis Dependency Graph
- **Label**: `fig:glycolysis-dependency-graph`
- **Location**: `chapter_05_refactored.tex`, lines 658-682
- **Description**: Graph visualization (not Petri net)
  - Shows transition dependencies in glycolysis
  - Nodes: HK, PGI, PFK, etc. (10 transitions)
  - Edges: Dependency relationships
- **Model Status**: ⚠️ **NOT A PETRI NET** - This is a graph diagram, not model
- **Action Required**: Keep as TikZ (not a SHYpn model)

### Figure 5.9: Partition Algorithm
- **Label**: `fig:partition-algorithm`
- **Location**: `chapter_05_refactored.tex`, line 520
- **Description**: Algorithm pseudocode (not a diagram)
- **Model Status**: ⚠️ **NOT A PETRI NET** - Algorithm listing
- **Action Required**: No model needed (keep as algorithm box)

---

## Non-Model Figures (Keep as TikZ/Tables)

The following "figures" are actually tables, pseudocode, or non-Petri-net diagrams:

### Chapter 2: Related Work
- Tables comparing tools/extensions (no models)

### Chapter 5: Weak Independence
- `fig:glycolysis-dependency-graph` - Dependency graph (keep as TikZ)
- Algorithm pseudocode boxes (keep as is)

### Chapter 6-15: Validation & Implementation
- No inline Petri net diagrams found
- Tables with numerical results (keep as is)
- Future work: Add validation example models to Chapter 7

---

## Implementation Plan

### Phase 1: Model Organization (30 minutes)
1. Create directory structure:
   ```bash
   mkdir -p workspace/projects/thesis/conceptual
   mkdir -p workspace/projects/thesis/biological
   mkdir -p workspace/projects/thesis/validation
   ```

2. Symlink existing biological models:
   ```bash
   cd workspace/projects/thesis/biological/
   ln -s ../../Biochemical-Examples/17_Lac_Operon_Regulation/model.shy lac_operon.shy
   ln -s ../../Biochemical-Examples/03_Hexokinase_MM/model.shy hexokinase.shy
   ln -s ../../Biochemical-Examples/09_Complete_Glycolysis/model.shy glycolysis.shy
   ```

### Phase 2: Create Conceptual Models (2-3 hours)
Build minimal pedagogical models in SHYpn GUI:

1. **strong_independence.shy**
   - Places: P1, P2, P3, P4
   - Transitions: t1, t2
   - Arcs: P1→t1→P2, P3→t2→P4 (completely disjoint)

2. **convergent_synthesis.shy**
   - Places: Glucose, Lactate, Pyruvate
   - Transitions: t1, t2
   - Arcs: Glucose→t1→Pyruvate, Lactate→t2→Pyruvate

3. **shared_catalyst.shy**
   - Places: S1, S2, PGI, P1, P2
   - Transitions: t1, t2
   - Arcs: S1→t1→P1, S2→t2→P2, PGI⇢t1 (test), PGI⇢t2 (test)

4. **feedback_regulation.shy**
   - Places: Glc, ATP, G6P, F-1,6-BP
   - Transitions: HK, PFK
   - Arcs: Glc→HK→G6P, ATP→HK (normal), G6P→PFK→F-1,6-BP, ATP⇢PFK (inhibitor)

5. **conflict_mode.shy**
   - Places: ATP, P1, P2
   - Transitions: t1, t2
   - Arcs: ATP→t1→P1, ATP→t2→P2
   - Initial marking: ATP=3 (to show conflict)

6. **convergent_mode.shy**
   - Places: S1, S2, P
   - Transitions: t1, t2
   - Arcs: S1→t1→P, S2→t2→P

7. **regulatory_mode.shy**
   - Places: S1, S2, Enzyme, P1, P2
   - Transitions: t1, t2
   - Arcs: S1→t1→P1, S2→t2→P2, Enzyme⇢t1 (test), Enzyme⇢t2 (test)

### Phase 3: User Validation (1-2 hours)
**👤 USER ACTION REQUIRED**

User opens each model in SHYpn GUI to:
1. Adjust spatial layout for optimal thesis presentation
2. Verify place/transition labels match LaTeX captions
3. Fine-tune visual styling (colors, sizes, fonts)
4. Set appropriate initial markings for pedagogical clarity
5. Save all refined models

**Agent pauses here for user confirmation**

### Phase 4: Batch Export (5 minutes)
```bash
python scripts/export_thesis_figures.py --all \
    --output doc/thesis/latex/gfx/ \
    --format pdf
```

### Phase 5: Update LaTeX Chapters (1 hour)
Replace TikZ code blocks with `\includegraphics`:

**Example transformation:**
```latex
% BEFORE (inline TikZ):
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[...]
  % ... 30 lines of TikZ code ...
\end{tikzpicture}
\caption{Strong independence: $t_1$ and $t_2$ share no places}
\label{fig:strong-independence}
\end{figure}

% AFTER (includegraphics):
\begin{figure}[htbp]
\centering
\includegraphics[width=0.7\textwidth]{gfx/strong_independence.pdf}
\caption{Strong independence: $t_1$ and $t_2$ share no places}
\label{fig:strong-independence}
\end{figure}
% Original TikZ code archived in comments above for reference
```

### Phase 6: Testing & Commit (30 minutes)
```bash
cd doc/thesis/latex
pdflatex thesis.tex
pdflatex thesis.tex  # Second pass for references
# Verify all figures render correctly
git add workspace/projects/thesis/ doc/thesis/latex/gfx/ doc/thesis/latex/Chapters/
git commit -m "Replace thesis TikZ diagrams with SHYpn-generated figures"
git push
```

---

## Model Specifications

### Naming Convention
- **Conceptual models**: lowercase with underscores (e.g., `strong_independence.shy`)
- **Biological models**: lowercase with underscores (e.g., `lac_operon.shy`)
- **Exported PDFs**: match .shy filename (e.g., `strong_independence.pdf`)

### Visual Style Guidelines
- **Place radius**: 30px (default)
- **Transition size**: 15x40px (default)
- **Font size**: 12pt for labels
- **Colors**: Default SHYpn palette (blue places, black transitions)
- **Arc styles**: Normal (solid), Test (dashed), Inhibitor (dotted red)
- **Layout**: Horizontal left-to-right flow preferred
- **Margins**: 20px around diagram edges

### Initial Markings
For pedagogical clarity:
- **Conflict examples**: Set marking=3 on shared input place
- **Convergent examples**: Set marking=0 on output place (to show accumulation)
- **Catalyst examples**: Set marking=1 on enzyme places
- **Independence examples**: Set marking=1 on all input places

---

## Benefits of This Approach

### Reproducibility
- ✅ Version-controlled models (`.shy` files in git)
- ✅ Automated export pipeline
- ✅ No manual screenshot workflow
- ✅ Easy regeneration after model edits

### Consistency
- ✅ Uniform visual style across all figures
- ✅ Same rendering engine as GUI (Cairo)
- ✅ Labels match simulation semantics

### Maintainability
- ✅ Edit models in GUI, re-export automatically
- ✅ LaTeX only references PDFs, not inline diagrams
- ✅ Separate concerns: models (`.shy`) vs presentation (LaTeX)

### Quality
- ✅ Vector PDFs (perfect scaling)
- ✅ Publication-ready resolution
- ✅ Professional appearance

---

## Next Steps

1. ✅ **Document created** - This inventory
2. ⏳ **Create directory structure** - `workspace/projects/thesis/`
3. ⏳ **Symlink existing models**
4. ⏳ **Build 7 conceptual models in GUI**
5. 👤 **User validates all models**
6. ⏳ **Batch export to PDF**
7. ⏳ **Update LaTeX chapters**
8. ⏳ **Test thesis compilation**
9. ⏳ **Git commit and push**

**Estimated total time**: 5-7 hours (including user validation)

---

## Exclusions (Keep as TikZ)

The following figures are **NOT** Petri nets and should remain as TikZ/tables:

- **Chapter 2 tables**: Comparison tables (tool features, extensions)
- **Chapter 5 dependency graph**: Graph diagram (not Petri net topology)
- **Algorithm pseudocode**: Algorithm boxes (not models)
- **All numerical tables**: Performance benchmarks, validation results

---

**Last updated**: 2025-11-25
**Status**: Planning complete, ready for implementation
**Dependencies**: SHYpn GUI available, export script tested
