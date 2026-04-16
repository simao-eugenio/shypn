# Paper Outline

**Paper:** Signal Partition Theory: Disentangling Material and Information Flow in Biochemical Petri Nets

---

## Structure (Target: 6-8 pages)

### 1. Introduction (~2 pages)

#### 1.1 The Problem: Embedded Regulation
- Traditional Bio-PNs mix material + information in rate functions
- Example: `rate = basal * feedback / repression`
- Consequences: Hidden architecture, non-compositional, hard to visualize

#### 1.2 Prior Work
- Bio-PN formalism evolution (Reddy 1993, Hardy 2004)
- 12-tuple extension with weak independence (arXiv:2512.17106)
- Regulatory arcs (test/inhibitor) exist but underutilized
- SBML qualifiers vs. formal semantics

#### 1.3 Our Contribution
- **Signal Partition Theory:** P = P_m ∪ P_s, P_m ∩ P_s = ∅
- **Case study:** Lambda phage lysogeny decision
- **Validation:** Behavioral equivalence + architectural clarity
- **Implementation:** SHYpn software

---

### 2. Theory (~3 pages)

#### 2.1 Signal Partition Definition
```
Definition 1: Signal places (P_s ⊆ Ψ) carry regulatory information without mass transfer.
Constraint: ∀p ∈ P_s, ∀t ∈ T: p ∉ •t and p ∉ t• (no consuming/producing arcs)
```

#### 2.2 Arc Semantics
- **Material arcs** (F_m): Token consumption/production
- **Signal arcs** (F_s ⊆ Σ): Read-only sensing (test/inhibitor)
- Visual coding: Black (material), Orange (signal)

#### 2.3 Refactoring Procedure
1. Identify regulatory dependencies in rate functions
2. Mark regulatory species as signal places (P_s)
3. Extract regulation terms → inhibitor/test arcs
4. Simplify rate functions (remove extracted terms)
5. Verify behavioral equivalence

#### 2.4 Architectural Patterns
- **Pattern A:** Mutual repression (lambda phage)
- **Pattern B:** Cascade activation (MAPK)
- **Pattern C:** Feedback loops (quorum sensing)

**Figure 1: Theory Overview**
- Panel A: Embedded regulation (formula with repression term)
- Panel B: Signal hierarchy (inhibitor arc diagram)
- Panel C: Visual comparison table

---

### 3. Methods (~2 pages)

#### 3.1 Lambda Phage Model
- **12 places:** genes, mRNAs, proteins, dimers, RecA
- **17 transitions:** transcription, translation, degradation, cleavage
- **Symmetric rate functions:** T1 and T6 use identical form

**Equation 1:** Original T1 (CI transcription)
```
rate = 2.0 × (1 + 0.5 × [CI_Dimer] / (5 + [CI_Dimer])) / (1 + ([Cro_Dimer] / 15)²)
       ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^
       basal  positive feedback (material loop)          repression (SIGNAL)
```

#### 3.2 Refactoring Procedure
1. **Identify signals:** CI_Dimer, Cro_Dimer → P_s (Ψ_regulatory)
2. **Extract repression:** 1/(1+(x/Ki)^n) → inhibitor arc (threshold=Ki, hill=n)
3. **Simplify rates:** Remove repression denominators
4. **Add arcs:** CI_Dimer ⊣ T6, Cro_Dimer ⊣ T1

**Equation 2:** Refactored T1
```
rate = 2.0 × (1 + 0.5 × [CI_Dimer] / (5 + [CI_Dimer]))
       ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
       basal  positive feedback only (material)
```

#### 3.3 Simulation Protocol
- **Algorithm:** Gillespie tau-leaping (ε=0.03)
- **Replicates:** n=100 per condition
- **Duration:** 3000 seconds
- **Classification:** Lysogenic if [CI_Dimer] > [Cro_Dimer] at t=3000s

**Figure 2: Model Comparison**
- Panel A: Original model (embedded repression)
- Panel B: Refactored model (inhibitor arcs visible)
- Panel C: Rate function comparison
- Panel D: Visual coding legend

---

### 4. Results (~3 pages)

#### 4.1 Behavioral Equivalence
| Model | Lysogenic | Lytic | Undecided | Chi-square |
|-------|-----------|-------|-----------|------------|
| Original | 42% | 48% | 10% | - |
| Refactored | 43% | 47% | 10% | p=0.89 |

**Interpretation:** No statistically significant difference (p > 0.05)

#### 4.2 Architectural Clarity
**Advantages:**
1. **Visible regulation:** Inhibitor arcs shown in diagram
2. **No formula inspection:** Regulatory topology evident
3. **Modular composition:** Add/remove arcs without editing functions

**Example:** Adding CII regulation
- Original: Edit T1 and T6 rate formulas (error-prone)
- Refactored: Add CII signal place + 2 test arcs (compositional)

#### 4.3 Rate Function Simplification
- **Original T1:** 3 terms (basal, feedback, repression)
- **Refactored T1:** 2 terms (basal, feedback)
- **Reduction:** 33% fewer mathematical operations

#### 4.4 Visual Semantics
- Orange borders identify signal places (2 of 12)
- Orange arcs show information flow (2 inhibitor arcs)
- Clear separation from material (black, 29 arcs)

**Figure 3: Validation Results**
- Panel A: Outcome distribution comparison (bar chart)
- Panel B: Time course overlays (lysogenic + lytic)
- Panel C: Phase portrait (CI vs Cro final states)
- Panel D: Statistical tests (chi-square, KS test)

---

### 5. Generalization (~1.5 pages)

#### 5.1 Additional Examples

**Example 1: Quorum Sensing**
- Extracellular AHL → signal place (Ψ_environmental)
- Transcription rates sense AHL without consumption
- Already implemented (workspace/examples/19/)

**Example 2: Metabolic Integration**
- ATP/ADP ratio → signal places (Ψ_energetic)
- Glycolysis ↔ TCA coordination via energy sensing
- No mass transfer between pathways, only information

**Example 3: Compartmentalization**
- Nucleus/cytoplasm as separate material networks
- Nuclear export signals → P_s (Ψ_spatial)
- Compartment coupling via signal sensing

**Figure 4: Generalization Examples**
- Panel A: Quorum sensing (multi-cellular)
- Panel B: Metabolic integration (energy signals)
- Panel C: Compartmentalization (spatial signals)

---

### 6. Discussion (~2 pages)

#### 6.1 Comparison to Prior Work
- **SBML qualifiers:** Annotation only, no formal semantics
- **BioNetGen:** Rule-based, different paradigm
- **Test arcs:** Signal partition theory provides unifying framework

#### 6.2 Advantages
1. **Visual clarity:** Architecture visible in diagram
2. **Modularity:** Compositional reasoning
3. **Biological fidelity:** Matches intuition (proteins = info carriers)
4. **Tool support:** Explicit thresholds, Hill coefficients

#### 6.3 Limitations
- Requires explicit signal identification (manual or automated)
- Visual complexity increases with many signals
- Not beneficial for simple linear pathways
- Rate function simplification may obscure kinetic details

#### 6.4 Future Work
- Automated signal detection from rate function analysis
- Hierarchical signal organization (cascades)
- Integration with spatial models (compartments)
- Large-scale pathway refactoring (KEGG, BioModels)

---

### 7. Conclusion (~0.5 pages)

Signal Partition Theory provides a principled architecture for biological network modeling. By enforcing P_m ∩ P_s = ∅, we separate material transformation from information control, achieving visual clarity, modular composition, and biological fidelity. 

The lambda phage case study demonstrates feasibility: behavioral equivalence is maintained while regulatory architecture becomes explicit. This pattern generalizes to metabolic integration, compartmentalization, and multi-cellular systems.

Our SHYpn implementation proves practical viability. Signal hierarchy emerges as a foundational design pattern for systems biology, complementing weak independence theory (parallel execution) with architectural clarity (explicit information flow).

---

## Figures Summary (5 figures)

1. **Theory Overview** - Embedded vs signal hierarchy comparison
2. **Model Comparison** - Lambda phage before/after refactoring
3. **Validation Results** - Behavioral equivalence demonstration
4. **Generalization Examples** - Quorum sensing, metabolism, compartments
5. **Visual Coding System** - Color legend and example networks

---

## Target Length

- **PLOS Comp Bio:** 10-15 pages typical (flexible)
- **Bioinformatics:** 6 pages (strict limit for Original Papers)
- **BMC Bioinformatics:** No page limit

**Strategy:** Write full version for PLOS, condense for Bioinformatics if needed

---

## Key Messages

**For reviewers:**
- NOT just visualization—formal architectural principle
- Behavioral equivalence proves correctness
- Generalizes beyond single example

**For readers:**
- Signal places make regulation explicit
- Material/information separation is biologically meaningful
- Practical tool available (SHYpn)
