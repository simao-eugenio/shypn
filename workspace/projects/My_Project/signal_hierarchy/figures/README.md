# Figures Directory

Publication-quality figures for signal hierarchy paper.

---

## Figure List

### Figure 1: Theory Overview
**Location:** `figure1_theory/`

**Panels:**
- A: Embedded regulation (rate formula with repression)
- B: Signal hierarchy (inhibitor arc diagram)
- C: Comparison table (formula vs arc semantics)

**Format:** PDF (vector) + PNG (300 dpi)

---

### Figure 2: Model Comparison
**Location:** `figure2_lambda/`

**Panels:**
- A: Original lambda phage (embedded repression in formulas)
- B: Refactored lambda phage (inhibitor arcs shown)
- C: Rate function before/after
- D: Visual coding legend

**Format:** PDF + PNG

---

### Figure 3: Validation Results
**Location:** `figure3_validation/`

**Panels:**
- A: Outcome distribution (original vs refactored)
- B: Time course overlays (lysogenic + lytic examples)
- C: Phase portrait (CI vs Cro final states)
- D: Statistical tests (chi-square, KS test results)

**Format:** PDF + PNG

**Data source:** `../data/lambda_phage/`

---

### Figure 4: Generalization Examples
**Location:** `figure4_examples/`

**Panels:**
- A: Quorum sensing (bacterial communication)
- B: Metabolic integration (ATP signal coupling)
- C: Compartmentalization (nuclear/cytoplasmic)

**Format:** PDF + PNG

---

### Figure 5: Visual Coding System
**Location:** `figure5_visual_coding/`

**Content:**
- Color legend (black=material, orange=signal)
- Arc type legend (solid, dashed, hollow circle)
- Example networks with annotations

**Format:** PDF + PNG

---

## Generation Scripts

**Location:** `scripts/`

- `generate_figure1.py` - Theory diagrams
- `generate_figure2.py` - Lambda phage comparison
- `generate_figure3.py` - Validation plots
- `generate_figure4.py` - Generalization examples
- `generate_figure5.py` - Visual coding legend
- `generate_all.sh` - Batch generation

---

## Style Guidelines

**Colors:**
- Material: Black (0, 0, 0)
- Signal: Orange (1.0, 0.6, 0.0)
- Background: White
- Accent: Gray (0.5, 0.5, 0.5) for annotations

**Fonts:**
- Main text: Arial 10pt
- Labels: Arial 8pt
- Equations: Computer Modern (LaTeX style)

**Dimensions:**
- Single column: 3.5 inches width
- Double column: 7 inches width
- DPI: 300 minimum for raster elements

---

## TODO

- [ ] Generate Figure 1 (theory diagrams)
- [ ] Generate Figure 2 (lambda comparison from actual models)
- [ ] Generate Figure 3 (validation from simulation data)
- [ ] Generate Figure 4 (generalization examples)
- [ ] Generate Figure 5 (visual coding legend)
- [ ] Verify all figures meet journal requirements
- [ ] Create supplementary figures if needed
