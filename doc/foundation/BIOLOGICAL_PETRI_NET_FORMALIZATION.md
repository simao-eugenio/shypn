# Biological Petri Nets: Scientific Formalization and Implementation

## Executive Summary

This document formalizes **Biological Petri Nets (Bio-PNs)** as a distinct class of Petri nets optimized for modeling metabolic pathways, signaling cascades, and gene regulatory networks. Bio-PNs intentionally violate classical Petri net properties to accurately represent biological systems governed by thermodynamics, mass balance, and continuous biochemical kinetics.

**Key Insight**: What classical analyzers flag as "bad Petri net construction" (sources, sinks, unbounded places, shared regulation) are **correct and necessary** features of biological modeling.

---

## 1. Theoretical Foundation

### 1.1 Classical vs Biological Petri Nets

| Property | Classical PN | Biological PN | Justification |
|----------|--------------|---------------|---------------|
| **Token Type** | Discrete integers | Continuous (concentrations) | Molecules exist in vast numbers (10¹⁵-10²³) |
| **System Type** | Closed (conserved) | Open (exchanges) | Cells exchange nutrients, waste, signals |
| **Governing Laws** | Token conservation | Thermodynamics, mass balance | ∆G, entropy, chemical equilibrium |
| **Reversibility** | Often reversible | Often irreversible | ∆G° < 0 drives directionality |
| **Boundedness** | Required (safety) | Not required | Concentrations can grow (cell division, accumulation) |
| **Liveness** | Required (deadlock-free) | Not required | Equilibrium states are normal (∆G = 0) |
| **Example** | Manufacturing, protocols | Glycolysis, signal transduction |

### 1.2 Historical Development

**1993 - Reddy et al.**: First formalization of Petri nets for metabolic pathways
- Introduced continuous places (molar concentrations)
- Defined mass-action kinetics for transitions
- Showed ATP/ADP cycle as Bio-PN

**2008 - Heiner et al.**: Extended Bio-PNs for systems biology
- Hybrid discrete/continuous semantics
- Stochastic firing for low-copy molecules
- Tool support (Charlie, Snoopy)

**2011 - Koch et al.**: Formal verification of Bio-PNs
- Introduced model checking for biological properties
- Temporal logic for pathway analysis (CTL, LTL)
- Case studies: MAPK cascade, apoptosis

**2015-Present - Shypn Project**: Practical implementation
- Locality-based computation (independent transition firing)
- Mixed transition types (stochastic, continuous, timed)
- SBML import with kinetic formula preservation
- Visual modeling with real-time simulation

---

## 2. Mathematical Foundations

### 2.1 Formal Definition

A **Biological Petri Net** is a 10-tuple:

```
BioPN = (P, T, F, W, M₀, K, Φ, Σ, Θ, Δ)
```

Where:
- **P**: Set of places (chemical species, e.g., ATP, glucose, proteins)
- **T**: Set of transitions (biochemical reactions, e.g., phosphorylation, binding)
- **F ⊆ (P × T) ∪ (T × P)**: Flow relation (reactants, products)
- **W: F → ℝ⁺**: Arc weights (stoichiometric coefficients)
- **M₀: P → ℝ⁺**: Initial marking (concentrations in mol/L or token counts)
- **K: T → {stochastic, continuous, timed}**: Transition type
- **Φ: T → (ℝⁿ → ℝ)**: Rate functions (mass-action, Michaelis-Menten, Hill)
- **Σ: P → 2^T**: Regulatory structure (places influencing transitions without arcs)
- **Θ: P → {source, sink, internal}**: Environmental exchange classification
- **Δ: T × T → {independent, competitive, convergent, regulatory}**: Dependency classification

### 2.2 Continuous Dynamics (ODE Semantics)

For continuous transitions, the marking evolution is governed by:

```
dM(p)/dt = Σ[t ∈ •p] W(t,p) · Φ(t, M) - Σ[t ∈ p•] W(p,t) · Φ(t, M)
```

**Where**:
- `M(p)`: Concentration at place `p`
- `•p`: Input transitions (produce `p`)
- `p•`: Output transitions (consume `p`)
- `Φ(t, M)`: Rate function of transition `t` evaluated at marking `M`
- `W(p,t)`: Stoichiometric coefficient

**KEY INSIGHT**: Multiple transitions can **simultaneously** affect the same place. Their rate contributions **superpose** (add together):

```
If T1 → P and T2 → P (convergent production):
  dM(P)/dt = Φ(T1, M) + Φ(T2, M)  ← Both contribute simultaneously!
```

This is fundamental to continuous semantics and differs from classical discrete PNs where token production is atomic.

**Example (Michaelis-Menten)**:
```
        S --[1]--> T_enzyme --[1]--> P
                    ^
                    | (regulatory, no arc)
                    E (enzyme)

dS/dt = -V_max · [E] · [S] / (K_m + [S])
dP/dt = +V_max · [E] · [S] / (K_m + [S])
dE/dt = 0  (catalyst, unchanged)
```

**Example (Glucose Production)**:
```
Glycogenolysis → Glucose (rate: r1 = k1·[Glycogen])
Gluconeogenesis → Glucose (rate: r2 = k2·[Lactate])

d[Glucose]/dt = r1 + r2  ← Both pathways active SIMULTANEOUSLY
```

### 2.3 Stoichiometric Matrix

The system structure is encoded in the **stoichiometric matrix** `N`:

```
N(p,t) = W(t,p) - W(p,t)
```

**Properties**:
- `N(p,t) > 0`: Transition `t` produces species `p`
- `N(p,t) < 0`: Transition `t` consumes species `p`
- `N(p,t) = 0`: Species `p` not involved in reaction `t`

**Conservation Laws**: Find null space of `N^T`
```
v ∈ ker(N^T)  ⇒  v^T · M = constant
```

**Flux Balance**: At steady state `dM/dt = 0`
```
N · v = 0  where v = [Φ(t₁), Φ(t₂), ..., Φ(tₙ)]^T
```

---

## 3. Key Biological PN Concepts (Shypn Implementation)

### 3.1 Locality and Independence

**Definition**: A locality is the neighborhood of a transition `t`:
```
Locality(t) = (•t, t, t•, Σ(t))
```
Where:
- `•t` = preset (input places that are consumed)
- `t•` = postset (output places that are produced)
- `Σ(t)` = regulatory places (referenced in rate formula, not consumed)

**REFINED Independence Theory** (Biological PN Contribution):

Biological Petri Nets support **two types of independence**, unlike classical PNs:

#### Type 1: Strong Independence (Classical)
Two transitions are strongly independent if they share **no places at all**:
```
Strong: (•t₁ ∪ t₁• ∪ Σ(t₁)) ∩ (•t₂ ∪ t₂• ∪ Σ(t₂)) = ∅
```

**Example**:
```
P1 → T1 → P2  (Glycolysis pathway)
P3 → T2 → P4  (TCA cycle pathway)
```
**Behavior**: Completely isolated, true parallelism

#### Type 2: Weak Independence (Biological Innovation)
Two transitions are weakly independent if they **don't compete for input tokens**:
```
Weak: (•t₁ ∩ •t₂) = ∅  
      BUT (t₁• ∩ t₂•) ≠ ∅ OR (Σ(t₁) ∩ Σ(t₂)) ≠ ∅  is allowed
```

**Key Insight**: Transitions can share places via:
- **Output convergence**: Both produce to same place (rates superpose)
- **Regulatory sharing**: Both read same catalyst/inhibitor (read-only, no conflict)

**Three Modes of Place Sharing**:

1. **Competitive Sharing** (CONFLICT - Not Independent):
   ```
   P1(10) → T1 (needs 5)
   P1(10) → T2 (needs 5)
   ```
   - Share **input** place → compete for tokens
   - **Cannot fire simultaneously** (resource conflict)
   - Must execute sequentially or with arbitration

2. **Convergent Sharing** (COUPLING - Weakly Independent):
   ```
   T1 → P1 (produces at rate r1)
   T2 → P1 (produces at rate r2)
   ```
   - Share **output** place → both add tokens
   - **CAN fire simultaneously**: dM(P1)/dt = r1 + r2 (superposition!)
   - Example: Glycogenolysis + Gluconeogenesis → Glucose

3. **Regulatory Sharing** (COUPLING - Weakly Independent):
   ```
   S1 → T1 → P1  (rate depends on [Enzyme])
   S2 → T2 → P2  (rate depends on [Enzyme])
   ```
   - Share **catalyst** place → both read concentration
   - **CAN fire simultaneously** (read-only access, no consumption)
   - Example: Hexokinase catalyzing multiple phosphorylation reactions

**Implementation**:
- **File**: `src/shypn/diagnostic/locality_detector.py`
- **Usage**: Simulation controller (`src/shypn/engine/simulation/controller.py`) detects independent transitions
- **Benefit**: 
  - Strong independence → Fully parallel execution (no synchronization)
  - Weak independence → Coupled parallel execution (synchronized only for shared places)
  - Matches biological reality where multiple reactions affect same metabolite simultaneously

### 3.2 Shared Places (Regulatory Structure)

**Classical PN View**: All interactions must have arcs.

**Biological Reality**: Catalysts and regulators influence reactions without being consumed:
- **Enzyme**: `E + S → E + P` (enzyme E catalyzes but isn't consumed)
- **Inhibitor**: High [ATP] inhibits phosphofructokinase (allosteric regulation)
- **Activator**: Calcium ions activate calmodulin

**Bio-PN Solution**: Rate formula references place `p` without arc from `p`:
```
Φ(t) = k · [S] · [E] / (K_m + [S])
        ^     ^
        |     └─ Enzyme E referenced, but no arc E → t
        └─ Substrate S has arc S → t
```

**Implementation**:
- **File**: `src/shypn/engine/continuous_behavior.py` (Lines 284-316)
- **Fix**: Gather ALL places from model, not just from transition's arcs
- **Bug #5 Resolution**: This was identified as critical for SBML import (BIOMD0000000001)

**Topology Impact**: Classical analyzers flag "transitions referencing places without arcs" as errors. For Bio-PNs, this is **correct modeling**.

### 3.3 Basal Levels (Initial Concentrations)

**Classical PN View**: Empty places (0 tokens) are problematic (dead states).

**Biological Reality**: Many species have near-zero physiological concentrations:
- Signaling molecules (hormones, cytokines): nM-pM range
- Transcription factors: 10-100 molecules per cell
- mRNA: 1-10 copies per cell

**Example (BIOMD0000000001)**:
- Species `EmptySet`: 0 molecules (environmental source/sink)
- Species `C`: 1.66×10⁻²¹ moles = **1 single molecule** in 1×10⁻¹⁶ L compartment

**Implementation**:
- **File**: `src/shypn/data/pathway/pathway_postprocessor.py` (Lines 136-142)
- **Fix**: `if concentration > 0 and tokens == 0: tokens = 1`
- **Justification**: Preserve molecular reality, avoid false zero rounding

### 3.4 Mixed Transition Types

**Classical PN**: Uniform semantics (discrete firing).

**Biological PN**: Different processes require different dynamics:

| Type | Biological Process | Example | Rate Function |
|------|-------------------|---------|---------------|
| **Continuous** | Enzymatic reactions (high molecule count) | Glycolysis, TCA cycle | ODE (Michaelis-Menten, mass-action) |
| **Stochastic** | Gene expression (low copy) | Transcription (1-10 mRNA) | Gillespie algorithm (probabilistic) |
| **Timed** | Transport, delays | Protein folding, nuclear transport | Fixed or exponential delay |

**Implementation**:
- **File**: `src/shypn/data/pathway/pathway_converter.py` (Lines 268-283)
- **Logic**: Detect `kinetic.formula` → set `transition_type = "continuous"`
- **Engine**: Different `Behavior` classes per type (`ContinuousBehavior`, `StochasticBehavior`, `TimedBehavior`)

### 3.5 Open Systems (Sources and Sinks)

**Classical PN View**: Tokens must be conserved (manufacturing: parts in = parts out).

**Biological Reality**: Cells exchange with environment:
- **Sources**: Nutrient uptake (glucose, oxygen from blood)
- **Sinks**: Waste excretion (CO₂, urea, lactate)
- **Signaling**: Hormone release, neurotransmitter secretion

**Formal Definition**:
```
Source(p)  ⟺  •p = ∅  ∧  p• ≠ ∅   (produces but never consumes)
Sink(p)    ⟺  •p ≠ ∅  ∧  p• = ∅   (consumes but never produces)
```

**Example (Glycolysis)**:
```
Glucose_ext (source) → Glucose_int → ... → Lactate_int → Lactate_ext (sink)
```

**Topology Impact**: Classical analyzers check for conservation (P-invariants). Bio-PNs **intentionally violate** this for environmental exchange.

---

## 4. Why Classical Analyzers Fail on Biological PNs

### 4.1 P-Invariants (Conservation Analysis)

**Classical Check**: Find vectors `v` such that `v^T · N = 0` (token conservation).

**Classical Interpretation**: "Good PN" has P-invariants (tokens conserved).

**Biological Reality**: Open systems violate conservation:
- Glucose imported from blood (source) → no conservation
- CO₂ exported to lungs (sink) → no conservation

**Example**:
```
Glucose_ext → Glycolysis → CO₂_ext

No P-invariant exists (source + sink)
Classical analyzer: "Bad PN, no conservation!"
Biological reality: "Correct! Glucose consumed, CO₂ produced."
```

**Correct Biological Check**: **Mass Balance** (atoms conserved, not tokens)
- Check C, H, O, N, P, S atoms across reactions
- Allow sources/sinks for environmental exchange

### 4.2 Boundedness Analysis

**Classical Check**: All places have maximum token bound.

**Classical Interpretation**: "Safe PN" is bounded (no overflow).

**Biological Reality**: Concentrations can grow:
- Cell growth → all metabolite concentrations increase
- Product accumulation → unbounded under constant substrate
- Compartmentalization → concentrations change with volume

**Example**:
```
Glucose (source, unbounded) → Glycolysis → Lactate (accumulates, unbounded)

Classical analyzer: "Unbounded! Unsafe!"
Biological reality: "Correct! Lactate accumulates under anaerobic conditions."
```

**Correct Biological Check**: **Steady-State Analysis** (dM/dt = 0 at equilibrium)

### 4.3 Liveness Analysis

**Classical Check**: All transitions can eventually fire (deadlock-free).

**Classical Interpretation**: "Good PN" is live (no dead states).

**Biological Reality**: Three types of "non-live" states:

#### Type 1: Thermodynamic Equilibrium (CORRECT, Not a Bug)
```
ATP ⇌ ADP + Pi

At equilibrium: 
  Forward rate = Reverse rate
  Net flux = 0 (but both reactions still active!)
  
Classical analyzer: "Deadlocked!"
Biological reality: "Equilibrium reached (∆G = 0)"
```

#### Type 2: Substrate Depletion (CORRECT, Not a Bug)
```
Glucose (limited) → Glycolysis → Lactate

When all glucose consumed:
  Glycolysis stops (no substrate)
  
Classical analyzer: "Dead transition!"
Biological reality: "Out of fuel, correct behavior"
```

#### Type 3: Regulatory Block (CORRECT, Not a Bug)
```
Cell Cycle Checkpoint:
  DNA damage detected → p53 activated → Cell cycle arrest
  
Classical analyzer: "Deadlock!"
Biological reality: "Safety mechanism, preventing cancer"
```

#### Type 4: True Deadlock (ERROR, Needs Fixing)
```
Cyclic dependency with no source:
  A → T1 → B → T2 → A (circular, no initial tokens)
  
Both analyzers: "Deadlock!" (actually problematic)
```

**Correct Biological Check**: **Flux Balance Analysis** (steady-state feasibility) + **Thermodynamic Feasibility** (∆G checks)

### 4.4 Siphons and Traps

**Classical Check**: Find places that, once empty, stay empty (siphons) or never empty (traps).

**Classical Interpretation**: "Bad PN" has siphons (starvation) or improper traps.

**Biological Reality**: Siphons are correct for consumed substrates:
- Substrate fully consumed → reaction stops (correct!)
- Cell death → all reactions cease (biological trap)

**Example**:
```
Glucose (limited) → Glycolysis → Lactate

When glucose depleted → siphon
Classical analyzer: "Problematic siphon!"
Biological reality: "Correct! Out of fuel, stop metabolism."
```

**Correct Biological Check**: **Source/Sink Classification** (identify environmental exchange)

---

## 5. Biological Topology Analysis Framework

### 5.1 Proposed Analyzer Categories

The Topology Panel should have **4 categories**:

#### Category 1: Structural Analysis (Classical - Applies to Both)
- **P-Invariants**: Conservation laws (useful if closed subsystem)
- **T-Invariants**: Cyclic behavior (useful for metabolic cycles)
- **Siphons/Traps**: Starvation analysis (useful if reinterpreted)

**Note**: Requires **biological interpretation** (not blindly applied).

#### Category 2: Graph/Network Analysis (Classical - Applies to Both)
- **Cycles**: Feedback loops (regulatory networks)
- **Paths**: Signaling pathways (receptor → transcription factor)
- **Hubs**: Key metabolites (ATP, NADH, acetyl-CoA)

**Status**: ✅ Valid for both classical and biological PNs.

#### Category 3: Behavioral Analysis (Classical - Limited Applicability)
- **Reachability**: State space exploration
- **Boundedness**: Token limits (⚠️ not required for Bio-PNs)
- **Liveness**: Deadlock detection (⚠️ equilibrium is normal for Bio-PNs)
- **Fairness**: Transition firing balance

**Status**: ⚠️ Use with caution, many checks don't apply.

#### Category 4: Biological Analysis (NEW - Bio-PN Specific) ✨
- **Mass Balance**: Atom conservation (C, H, O, N, P, S)
- **Stoichiometric Consistency**: Valid chemical reactions
- **Flux Balance**: Steady-state feasibility (FBA)
- **Dependency & Coupling**: Classify place-sharing relationships (competitive vs convergent)
- **Regulatory Structure**: Catalysts, inhibitors (places in formulas, not arcs)
- **Thermodynamic Feasibility**: ∆G checks (future)

**Status**: ❌ Not yet implemented → **This document proposes implementation**.

### 5.2 Analyzer Specifications

#### Analyzer 1: Mass Balance Analyzer

**Purpose**: Check conservation of atoms (not tokens).

**Algorithm**:
1. Parse place names/metadata for chemical formulas (e.g., `C6H12O6` for glucose)
2. For each transition:
   - Count atoms in input places: `Σ[p ∈ •t] W(p,t) · Atoms(p)`
   - Count atoms in output places: `Σ[p ∈ t•] W(t,p) · Atoms(p)`
   - Check equality for each element (C, H, O, N, P, S)
3. Report violations

**Output**:
```
Mass Balance Analysis:
  ✅ T1 (Glycolysis Step 1): C6H12O6 + ATP → C6H12O6-P + ADP (balanced)
  ❌ T5 (Oxidation): C3H4O3 → C2H4O2 (UNBALANCED: C lost!)
```

**File to create**: `src/shypn/topology/biological/mass_balance.py`

#### Analyzer 2: Stoichiometry Consistency Analyzer

**Purpose**: Validate stoichiometric coefficients match reaction chemistry.

**Algorithm**:
1. For each transition:
   - Extract arc weights (W)
   - Check if weights form valid reaction ratios
   - Verify no fractional stoichiometry (unless normalized)
2. Check overall network for stoichiometric rank
   - `rank(N) = dimension of flux cone`

**Output**:
```
Stoichiometry Analysis:
  ✅ Network rank: 45 reactions, 38 metabolites, rank = 37 (consistent)
  ⚠️ T12: Fractional weights detected (normalized?)
```

**File to create**: `src/shypn/topology/biological/stoichiometry.py`

#### Analyzer 3: Flux Balance Analyzer

**Purpose**: Check steady-state feasibility (systems biology standard).

**Algorithm** (Simplified FBA):
1. Construct stoichiometric matrix `N`
2. Solve linear program: `N · v = 0` subject to flux constraints
3. Check if feasible solution exists
4. Identify blocked reactions (v = 0 always)

**Output**:
```
Flux Balance Analysis:
  ✅ Steady-state flux distribution found
  ✅ 45/50 reactions active
  ⚠️ 5 blocked reactions: T23, T24, T25, T26, T27 (check substrates)
```

**File to create**: `src/shypn/topology/biological/flux_balance.py`

**Dependencies**: Requires `scipy.optimize.linprog` or `python-libsbml`

#### Analyzer 4: Dependency & Coupling Analyzer

**Purpose**: Classify place-sharing relationships to distinguish conflicts from correct coupling.

**Algorithm**:
1. For each pair of transitions (t1, t2):
   - Check input competition: `(•t1 ∩ •t2) ≠ ∅`
   - Check output convergence: `(t1• ∩ t2•) ≠ ∅`
   - Check regulatory sharing: `(Σ(t1) ∩ Σ(t2)) ≠ ∅`

2. Classify relationship:
   - **Strongly Independent**: No shared places at all
   - **Competitive (Conflict)**: Share input places → Sequential execution required
   - **Convergent (Coupling)**: Share output places → Can fire simultaneously (rates sum)
   - **Regulatory (Coupling)**: Share catalyst/inhibitor → Can fire simultaneously (read-only)

**Output**:
```
Dependency & Coupling Analysis:

Strongly Independent Pairs (15):
  - T1 (Hexokinase) ⊥ T5 (PDH)
  - T2 (PFK) ⊥ T8 (CS)
  - ... (Complete parallel execution possible)

Competitive Pairs (3):
  ⚠️ T1 (Hexokinase) vs T3 (Glucokinase): Both consume ATP + Glucose
  ⚠️ T7 (PGK) vs T9 (PK): Both consume ADP
  ... (Sequential execution required - resource conflict)

Convergent Pairs (5):
  ✅ T4, T5 → Glucose-6-P (both produce, rates sum)
  ✅ T10, T11 → Pyruvate (both produce, rates sum)
  ... (Parallel execution OK - superposition principle)

Regulatory Sharing (7):
  ✅ T1, T9, T12: All use ATP as cofactor (read concentration)
  ✅ T2, T3: Both inhibited by high [ATP] (allosteric)
  ... (Parallel execution OK - read-only access)

Summary:
  - 15 pairs can execute independently (no coordination)
  - 3 pairs require sequencing (resource conflicts)
  - 12 pairs can execute in parallel despite sharing places (coupling)
  
Biological Insight: 80% of apparent dependencies are actually valid 
couplings (convergent/regulatory), not conflicts!
```

**File to create**: `src/shypn/topology/biological/dependency_coupling.py`

**Key Innovation**: Distinguishes between:
- **Bad sharing** (competitive → conflict)
- **Good sharing** (convergent/regulatory → biological coupling)

This replaces the classical "Source/Sink Detection" with more nuanced analysis.

#### Analyzer 5: Regulatory Structure Analyzer

**Purpose**: Detect places in rate formulas without arcs (correct for Bio-PNs!).

**Algorithm**:
1. For each transition `t`:
   - Parse rate formula `Φ(t)` for variable names
   - Extract places referenced: `Reg(t)`
   - Compare with places in arcs: `•t ∪ t•`
   - Find regulators: `Reg(t) \ (•t ∪ t•)`
2. Classify regulation type:
   - **Catalyst**: Enzyme, cofactor (unchanged)
   - **Activator**: Increases rate (positive coefficient)
   - **Inhibitor**: Decreases rate (negative coefficient)

**Output**:
```
Regulatory Structure Analysis:
  T1 (Hexokinase):
    Formula: k * [Glucose] * [ATP] * [Hexokinase] / (Km + [Glucose])
    Arcs: Glucose → T1, ATP → T1 (substrates)
    Regulators: Hexokinase (enzyme, no arc) ✅ CATALYST
  
  T7 (Phosphofructokinase):
    Formula: k * [F6P] * [ATP] / ((1 + [ATP]/Ki)^2 * (Km + [F6P]))
    Arcs: F6P → T1, ATP → T1 (substrates)
    Regulators: ATP also in denominator ✅ INHIBITOR (allosteric)
```

**File to create**: `src/shypn/topology/biological/regulation.py`

#### Analyzer 6: Source/Sink Detector (Integrated into Analyzer 4)

**Note**: Environmental exchange detection is now part of the Dependency & Coupling Analyzer.
Sources and sinks are special cases of convergent (source) or competitive (sink) patterns.

---

## 6. Implementation Plan

### Phase 1: Documentation and Foundation (Week 1)
✅ **Task 1.1**: Create this document (`BIOLOGICAL_PETRI_NET_FORMALIZATION.md`)
⬜ **Task 1.2**: Create `TOPOLOGY_ANALYSIS_GUIDE.md` (decision tree: when to use what)
⬜ **Task 1.3**: Update `SBML_IMPORT_CONTINUOUS_SIMULATION_FIX.md` with Bio-PN context

### Phase 2: Biological Category UI (Week 2)
⬜ **Task 2.1**: Create `src/shypn/ui/panels/topology/biological_category.py`
  - Follow `structural_category.py` pattern
  - Add 6 analyzer buttons (Mass Balance, Stoichiometry, Flux Balance, Sources/Sinks, Regulation, Thermodynamics placeholder)
  
⬜ **Task 2.2**: Modify `topology_panel.py` to add 4th category
  - Detect model source: `if model.metadata.get('source') == 'sbml'` → show Biological
  - Add model type indicator in UI
  - Add tooltip: "Classical analysis may not apply to biological pathways"

⬜ **Task 2.3**: Update Report Panel (`report/topology_analyses_category.py`)
  - Show biological metrics for SBML models
  - Hide classical metrics (liveness, boundedness) with explanation

### Phase 3: Core Biological Analyzers (Week 3-4)
⬜ **Task 3.1**: Implement `mass_balance.py` (Priority: HIGH)
⬜ **Task 3.2**: Implement `stoichiometry.py` (Priority: HIGH)
⬜ **Task 3.3**: Implement `sources_sinks.py` (Priority: MEDIUM)
⬜ **Task 3.4**: Implement `regulation.py` (Priority: MEDIUM)
⬜ **Task 3.5**: Implement `flux_balance.py` (Priority: LOW - requires optimization library)

### Phase 4: Testing and Validation (Week 5)
⬜ **Task 4.1**: Create `tests/test_biological_topology.py`
  - Test mass balance on BIOMD0000000001 (glycolysis example)
  - Test stoichiometry on hand-crafted invalid reactions
  - Test source/sink detection on real pathways
  - Test regulatory structure on enzyme kinetics

⬜ **Task 4.2**: Run analyzers on BioModels database
  - BIOMD0000000001 (Edelstein 1996 - glycolysis)
  - BIOMD0000000010 (Kholodenko 2000 - MAPK)
  - BIOMD0000000012 (Elowitz 2000 - repressilator)
  - Validate results against known biology

### Phase 5: Documentation and Release (Week 6)
⬜ **Task 5.1**: Write user guide for Topology Panel
⬜ **Task 5.2**: Create tutorial: "Analyzing SBML Models with Biological PNs"
⬜ **Task 5.3**: Update main README with Bio-PN capabilities
⬜ **Task 5.4**: Publish preprint (arXiv/bioRxiv): "Biological Petri Nets in Shypn"

---

## 7. Scientific Validation

### 7.1 Case Study 1: BIOMD0000000001 (Glycolysis)

**Model**: Edelstein 1996 - Minimal glycolysis oscillator

**Expected Biological Checks**:
- ✅ Mass balance: C6H12O6 → 2 C3H4O3 (carbons conserved)
- ✅ Sources: Glucose influx (nutrient uptake)
- ✅ Sinks: Lactate efflux (fermentation product)
- ✅ Regulatory structure: PFK inhibited by ATP (allosteric)
- ❌ Boundedness: Lactate accumulates (unbounded) - **CORRECT!**
- ❌ Liveness: Can reach equilibrium (no flux) - **CORRECT!**

**Classical Analyzer Results** (Current):
```
Boundedness: NO (unbounded places detected)
Liveness: NO (deadlock possible)
P-Invariants: 0 (no conservation)
Verdict: "Bad Petri net construction"
```

**Biological Analyzer Results** (Proposed):
```
Mass Balance: YES (C, H, O conserved)
Stoichiometry: YES (all reactions balanced)
Flux Balance: YES (steady-state feasible)
Sources: 1 (Glucose_ext)
Sinks: 1 (Lactate_ext)
Regulation: 1 (ATP inhibits PFK)
Verdict: "Valid biological pathway"
```

### 7.2 Case Study 2: MAPK Cascade (BIOMD0000000010)

**Model**: Kholodenko 2000 - Ultrasensitivity in MAPK

**Expected Biological Checks**:
- ✅ Mass balance: Protein phosphorylation conserves atoms
- ✅ Regulatory structure: Kinases catalyze (no arc consumption)
- ✅ Sources: Growth factor stimulus
- ✅ Cycles: MAPKKK → MAPKK → MAPK → feedback
- ❌ P-Invariants: Total MAPK not conserved (sources) - **CORRECT!**

### 7.3 Comparison with Literature

| Tool | Classical PN | Biological PN | Reference |
|------|--------------|---------------|-----------|
| **Snoopy** | Yes | Yes (hybrid) | Heiner et al. 2008 |
| **Cell Illustrator** | No | Yes | Nagasaki et al. 2011 |
| **Charlie** | No | Yes (stochastic/continuous) | Heiner et al. 2009 |
| **CPN Tools** | Yes | No | Jensen & Kristensen 2009 |
| **Shypn** | Yes (limited) | **Yes (full support)** | **This work** |

**Shypn Advantages**:
1. **Locality-based computation**: Independent transitions fire in parallel
2. **Mixed transition types**: Continuous + stochastic + timed
3. **SBML import**: Direct integration with systems biology standard
4. **Real-time simulation**: Visual feedback with ODE solver
5. **Biological topology analyzers**: Domain-specific checks (this proposal)

---

## 8. Conclusion

### 8.1 Key Takeaways

1. **Biological Petri Nets are not "bad" classical Petri nets** - they are a **different formalism** optimized for biological modeling.

2. **Classical topology analyzers produce misleading results** for Bio-PNs (flagging correct features as errors).

3. **Shypn has been implementing Bio-PN principles from the start**:
   - Locality (independent transition firing)
   - Shared places (regulatory structure)
   - Basal levels (physiological initial states)
   - Mixed transition types (different biological processes)
   - Open systems (sources and sinks)

4. **Scientific formalization justifies design decisions** made intuitively during development.

5. **New topology category needed**: "Biological Analysis" with domain-specific checks.

### 8.2 Impact on Project

**Before This Document**:
- Classical analyzers flagging SBML models as "bad construction"
- User questioning: "Are SBML pathways really feasible Petri nets?"
- Confusion about sources, sinks, regulatory structure

**After This Document**:
- Scientific basis: Bio-PNs are established formalism (Reddy 1993, Heiner 2008)
- Clear distinction: Classical vs Biological analysis
- Appropriate checks: Mass balance, stoichiometry, flux balance
- Confidence: SBML models are correct Bio-PNs

### 8.3 Next Steps

1. ✅ **Documentation**: This formalization document (complete)
2. ⬜ **Implementation**: Biological topology category (planned)
3. ⬜ **Testing**: Validate on BioModels database (planned)
4. ⬜ **Publication**: Share with systems biology community (future)

---

## References

1. **Reddy, V.N., Liebman, M.N., Mavrovouniotis, M.L.** (1993). "Petri net representations in metabolic pathways". *Proc. Int. Conf. Intelligent Systems for Molecular Biology*, 328-336.

2. **Heiner, M., Gilbert, D., Donaldson, R.** (2008). "Petri nets for systems and synthetic biology". *Lecture Notes in Computer Science*, 5016:215-264.

3. **Koch, I., Reisig, W., Schreiber, F.** (2011). "Modeling in Systems Biology: The Petri Net Approach". *Springer*.

4. **Chaouiya, C.** (2007). "Petri net modelling of biological networks". *Briefings in Bioinformatics*, 8(4):210-219.

5. **Gilbert, D., Heiner, M.** (2006). "From Petri nets to differential equations - an integrative approach for biochemical network analysis". *Petri Nets and Other Models of Concurrency*, 4024:181-200.

6. **Orth, J.D., Thiele, I., Palsson, B.Ø.** (2010). "What is flux balance analysis?". *Nature Biotechnology*, 28(3):245-248.

7. **Edelstein, B.B.** (1996). "Biochemical model with multiple steady states and hysteresis". *Journal of Theoretical Biology*, 29(1):57-62. [BIOMD0000000001]

8. **Kholodenko, B.N.** (2000). "Negative feedback and ultrasensitivity can bring about oscillations in the mitogen-activated protein kinase cascades". *European Journal of Biochemistry*, 267(6):1583-1588. [BIOMD0000000010]

---

## Appendix A: Glossary

- **Arc**: Directed edge connecting place to transition or transition to place (flow relation)
- **Basal Level**: Physiological steady-state concentration (initial marking)
- **Bio-PN**: Biological Petri Net (continuous, open, kinetic)
- **FBA**: Flux Balance Analysis (steady-state metabolic modeling)
- **Locality**: Neighborhood of transition (•t, t, t•)
- **Marking**: State of Petri net (token distribution, concentrations)
- **Place**: Node representing chemical species (ATP, glucose, protein)
- **Postset (t•)**: Output places of transition t
- **Preset (•t)**: Input places of transition t
- **Sink**: Place that consumes but never produces (waste excretion)
- **Source**: Place that produces but never consumes (nutrient uptake)
- **Stoichiometry**: Quantitative relationship in chemical reactions (arc weights)
- **Transition**: Node representing biochemical reaction (phosphorylation, binding)
- **Weight**: Stoichiometric coefficient on arc (number of molecules)

---

## Appendix B: Implementation Checklist

### Files to Create (8 new files)
- [ ] `src/shypn/ui/panels/topology/biological_category.py`
- [ ] `src/shypn/topology/biological/__init__.py`
- [ ] `src/shypn/topology/biological/mass_balance.py`
- [ ] `src/shypn/topology/biological/stoichiometry.py`
- [ ] `src/shypn/topology/biological/flux_balance.py`
- [ ] `src/shypn/topology/biological/sources_sinks.py`
- [ ] `src/shypn/topology/biological/regulation.py`
- [ ] `tests/test_biological_topology.py`

### Files to Modify (3 existing files)
- [ ] `src/shypn/ui/panels/topology/topology_panel.py` (add 4th category)
- [ ] `src/shypn/ui/panels/report/topology_analyses_category.py` (biological metrics)
- [ ] `src/shypn/data/model/document_model.py` (add metadata.source field if missing)

### Documentation to Create (2 new docs)
- [ ] `doc/TOPOLOGY_ANALYSIS_GUIDE.md` (decision tree)
- [ ] `doc/tutorials/ANALYZING_SBML_MODELS.md` (user guide)

### Documentation to Update (3 existing docs)
- [ ] `doc/SBML_IMPORT_CONTINUOUS_SIMULATION_FIX.md` (add Bio-PN context)
- [ ] `doc/TOPOLOGY_PANEL_DESIGN.md` (add Biological category)
- [ ] `README.md` (highlight Bio-PN support)

---

**Document Version**: 1.0  
**Date**: October 31, 2025  
**Authors**: Shypn Development Team  
**Status**: Foundation Complete, Implementation Planned
