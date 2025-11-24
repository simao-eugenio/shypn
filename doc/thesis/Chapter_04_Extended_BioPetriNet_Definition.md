# Chapter 4: Formal Definition of Extended Biological Petri Nets

## 4.1 Classical Petri Net Review

### 4.1.1 Basic Definitions

A **classical Petri net** is a 5-tuple:

```
PN = (P, T, F, W, M₀)
```

Where:
- **P** = {p₁, p₂, ..., pₘ} is a finite set of **places** (represented as circles)
- **T** = {t₁, t₂, ..., tₙ} is a finite set of **transitions** (represented as rectangles or bars)
- **F ⊆ (P × T) ∪ (T × P)** is the **flow relation** (directed arcs)
- **W: F → ℕ⁺** is the **arc weight function** (positive integers, default W = 1)
- **M₀: P → ℕ₀** is the **initial marking** (token distribution)

With the constraint: **P ∩ T = ∅** (places and transitions are disjoint)

### 4.1.2 Neighborhood Notation

For a transition t ∈ T:
- **•t** = {p ∈ P | (p,t) ∈ F} : **preset** (input places)
- **t•** = {p ∈ P | (t,p) ∈ F} : **postset** (output places)

For a place p ∈ P:
- **•p** = {t ∈ T | (t,p) ∈ F} : transitions producing tokens in p
- **p•** = {t ∈ T | (p,t) ∈ F} : transitions consuming tokens from p

### 4.1.3 Enabling Rule

A transition **t is enabled** at marking M, written **M[t⟩**, if and only if:

```
∀p ∈ •t: M(p) ≥ W(p,t)
```

All input places must contain at least W(p,t) tokens.

### 4.1.4 Firing Rule

When enabled transition t fires, the new marking M' is computed as:

```
∀p ∈ P: M'(p) = M(p) - W(p,t) + W(t,p)
```

Where:
- **W(p,t) = 0** if (p,t) ∉ F (no arc from p to t)
- **W(t,p) = 0** if (t,p) ∉ F (no arc from t to p)

**Notation**: M[t⟩M' denotes "transition t is enabled at M and produces M'"

### 4.1.5 Reachability

The **reachability set** R(M₀) is the set of all markings reachable from M₀:

```
R(M₀) = {M | ∃σ = t₁t₂...tₖ: M₀[σ⟩M}
```

Where σ is a **firing sequence** of transitions.

### 4.1.6 Limitations for Biological Modeling

Classical Petri nets face fundamental limitations when modeling biological systems:

1. **All arcs are consumptive**: Tokens are always removed from input places
   - **Problem**: Enzymes catalyze reactions without being consumed
   - **Example**: Hexokinase phosphorylates glucose but remains unchanged
   - If modeled with normal arcs: Enzyme would deplete after first reaction

2. **No regulatory inhibition**: Transitions fire whenever inputs are available
   - **Problem**: Biological reactions can be blocked by inhibitors
   - **Example**: High ATP inhibits phosphofructokinase (energy feedback)
   - Classical PNs cannot express threshold-based blocking

3. **Strong independence requirement**: Parallel execution requires disjoint neighborhoods
   - **Problem**: Biological reactions share places (metabolites, enzymes)
   - **Example**: Multiple reactions produce same metabolite (superposition)
   - Classical parallelism rejects most biological networks

4. **Homogeneous transitions**: All transitions follow same firing semantics
   - **Problem**: Biology exhibits multiple temporal scales
   - **Example**: Enzyme kinetics (continuous) vs gene expression (stochastic bursts)
   - Classical PNs cannot mix continuous and discrete dynamics natively

5. **Abstract tokens**: No semantic meaning beyond quantity
   - **Problem**: Biochemistry requires elemental composition tracking
   - **Example**: C₆H₁₂O₆ + ATP → C₆H₁₁O₉P + ADP (atoms must balance)
   - Classical PNs cannot validate stoichiometric correctness

These limitations motivate the **Extended Biological Petri Net** formalism presented in this chapter.

---

## 4.2 Extended Bio-PN: The 12-Tuple Definition

An **Extended Biological Petri Net** is a 12-tuple:

```
BioPN = (P, T, F, W, M₀, K, Φ, Σ, Θ, Δ, τ, ρ)
```

### 4.2.1 Core Components (From Classical PN)

**P: Places** (Biochemical Species)
- Metabolites: Glucose, ATP, NAD⁺, Pyruvate
- Enzymes: Hexokinase, Phosphofructokinase, Pyruvate Kinase
- Genes: lacZ, lacY, lacA (structural genes)
- Transcription Factors: CRP, cAMP-CRP complex, LacI repressor
- mRNA: lacZ_mRNA, lacY_mRNA
- Proteins: β-galactosidase, Permease, Transacetylase

Each place p has attributes:
- **p.id**: Unique identifier (e.g., "P001")
- **p.name**: Human-readable name (e.g., "Glucose", "ATP")
- **p.formula**: Biochemical formula (e.g., "C6H12O6", "C10H16N5O13P3")
- **p.type**: {metabolite, enzyme, gene, mRNA, protein, complex}

**T: Transitions** (Biochemical Reactions)
- Enzymatic reactions: Hexokinase, PGI, PFK, Aldolase, etc.
- Transcription: Gene → mRNA
- Translation: mRNA → Protein
- Complex formation: cAMP + CRP → cAMP-CRP
- Degradation: mRNA → ∅, Protein → ∅

Each transition t has attributes:
- **t.id**: Unique identifier (e.g., "T001")
- **t.name**: Reaction name (e.g., "Hexokinase", "lacZ_transcription")
- **t.ec_number**: Enzyme Commission number (e.g., "2.7.1.1" for hexokinase)
- **t.reversible**: Boolean (true for reversible reactions)

**F ⊆ (P × T) ∪ (T × P): Normal Arcs** (Consumption/Production)
- Directed arcs representing stoichiometric flow
- (p,t) ∈ F: place p is substrate (consumed by t)
- (t,p) ∈ F: place p is product (produced by t)

**W: F → ℕ⁺: Arc Weights** (Stoichiometric Coefficients)
- W(p,t) = number of tokens consumed from p when t fires
- W(t,p) = number of tokens produced in p when t fires
- Default: W = 1 (one molecule consumed/produced)
- Example: Hexokinase consumes 1 Glucose + 1 ATP, produces 1 G6P + 1 ADP

**M₀: P → ℕ₀ ∪ ℝ₀⁺: Initial Marking**
- Discrete (ℕ₀): Integer token counts for stochastic models
  - Example: M₀(Glucose) = 1000 molecules
- Continuous (ℝ₀⁺): Real-valued concentrations for ODE models
  - Example: M₀(Glucose) = 5.0 mM (millimolar)
- Hybrid: Some places discrete, others continuous
  - Metabolites: Continuous (high copy number)
  - Genes: Discrete (low copy number, typically 1 or 2)

### 4.2.2 Capacity Constraint

**K: P → ℕ ∪ {∞}: Place Capacity**
- Maximum number of tokens allowed in place p
- K(p) = ∞: unbounded (default)
- K(p) < ∞: bounded (e.g., limited enzyme concentration)
- Biological interpretation: Spatial constraints, crowding effects
- Firing rule modified: t can fire only if M'(p) ≤ K(p) for all p ∈ t•

### 4.2.3 Rate Functions

**Φ: T → RateFunction: Kinetic Rate Assignment**

Associates each transition with a mathematical function describing its firing rate.

**For continuous transitions** (τ(t) = Continuous):

1. **Mass Action Kinetics**:
   ```
   Φ(t) = k · ∏(M(p) for p ∈ •t)
   ```
   - k: rate constant (units: [conc]¹⁻ⁿ · [time]⁻¹, n = |•t|)
   - Example: A + B → C, Φ = k·[A]·[B]

2. **Michaelis-Menten Kinetics** (single substrate):
   ```
   Φ(t) = (Vmax · [S]) / (Km + [S])
   ```
   - Vmax: maximum velocity
   - Km: Michaelis constant (substrate concentration at half Vmax)
   - [S]: substrate concentration (M(p) for p ∈ •t)

3. **Multi-Substrate Michaelis-Menten**:
   ```
   Φ(t) = (Vmax · ∏[Si]) / (Km + ∏[Si])
   ```
   - Product of all substrate concentrations
   - Example: Hexokinase: Φ = (Vmax · [Glucose] · [ATP]) / (Km + [Glucose]·[ATP])

4. **Hill Equation** (cooperative binding):
   ```
   Φ(t) = (Vmax · [S]ⁿ) / (K₀.₅ⁿ + [S]ⁿ)
   ```
   - n: Hill coefficient (cooperativity, n > 1 positive, n < 1 negative)
   - K₀.₅: concentration at half-maximal activity
   - Example: Hemoglobin oxygen binding (n ≈ 2.8)

**For stochastic transitions** (τ(t) = Stochastic):

**Propensity function** (Gillespie algorithm):
```
a(t) = k · ∏(M(p) for p ∈ •t ∪ Σ(t))
```
- Includes both input places (•t) and test arc places (Σ(t))
- Stochastic rate constant k (units: [time]⁻¹)
- Example: Gene transcription a = k_transcription · M(gene) · M(polymerase)

**For timed transitions** (τ(t) = Timed):
```
Φ(t) = Delay(τ_delay)
```
- Deterministic delay τ_delay
- Example: Cell cycle checkpoint (fires exactly 30 minutes after enabling)

**For burst transitions** (τ(t) = Burst):
```
Φ(t) = Burst(λ_burst, μ_size)
```
- λ_burst: inter-burst interval rate (exponential distribution)
- μ_size: burst size (geometric distribution)
- Example: mRNA transcriptional bursts

### 4.2.4 Test Arcs (Catalysis)

**Σ ⊆ P × T: Test Arcs** (Read-Only, Non-Consumptive)

Test arcs enable transitions without consuming tokens.

**Semantics**:
- (p,t) ∈ Σ: place p is a **catalyst** for transition t
- **Pre-condition**: M(p) > 0 (catalyst must be present)
- **Post-condition**: M'(p) = M(p) (catalyst unchanged after firing)

**Biological Interpretation**:
1. **Enzymes**: Catalyze reactions without being consumed
   - Example: Hexokinase (enzyme) ⤏ Hexokinase_reaction
   - M(Hexokinase) remains constant

2. **Transcription Factors**: Regulate gene expression without degradation
   - Example: cAMP-CRP ⤏ lacZ_transcription
   - cAMP-CRP enables transcription but is not consumed

3. **Ribosomes**: Catalyze translation without being consumed
   - Example: Ribosome ⤏ Translation_lacZ
   - Ribosome reads mRNA, produces protein, remains free

**Formal Constraint**:
```
Σ ∩ F = ∅  (test arcs and normal arcs are disjoint)
```
- A place cannot be both substrate (consumed) and catalyst (non-consumptive) for the same transition

**Graphical Notation**:
- Dashed arrow: p ⤏ t
- Often with hollow arrowhead to distinguish from normal arcs

### 4.2.5 Inhibitor Arcs (Regulation)

**Θ ⊆ P × T: Inhibitor Arcs** (Threshold-Based Blocking)

Inhibitor arcs block transitions when inhibitor concentration exceeds threshold.

**Semantics**:
- (p,t) ∈ Θ: place p is an **inhibitor** of transition t
- **Pre-condition**: M(p) < Δ(p,t) (inhibitor below threshold)
- **Blocking condition**: If M(p) ≥ Δ(p,t), transition t is **disabled**
- **Post-condition**: M'(p) = M(p) (inhibitor unchanged after firing)

**Biological Interpretation**:
1. **Allosteric Feedback Inhibition**:
   - Example: ATP ⊸ PFK (threshold Δ = 5.0 mM)
   - When M(ATP) ≥ 5.0 mM, PFK is inhibited (energy sufficient)
   - When M(ATP) < 5.0 mM, PFK is active (energy needed)

2. **Transcriptional Repression**:
   - Example: LacI ⊸ lacZ_transcription (threshold Δ = 1.0 molecules)
   - When M(LacI) ≥ 1.0, lacZ transcription blocked (repressor bound)
   - When M(LacI) < 1.0, lacZ transcription allowed (repressor absent)

3. **Competitive Inhibition**:
   - Example: Glucose ⊸ Lactose_uptake (threshold Δ = 0.1 mM)
   - High glucose blocks lactose metabolism (catabolite repression)

**Formal Constraint**:
```
Θ ∩ F = ∅  and  Θ ∩ Σ = ∅
```
- Inhibitor arcs are disjoint from normal arcs and test arcs
- A place cannot be substrate, catalyst, AND inhibitor for same transition

**Graphical Notation**:
- Circle-headed arrow: p ⊸ t
- Often annotated with threshold value Δ(p,t)

### 4.2.6 Inhibition Threshold Functions

**Δ: Θ → ThresholdFormula: Inhibition Threshold**

Maps each inhibitor arc to a threshold formula or value.

**Simple Threshold** (constant):
```
Δ(p,t) = θ ∈ ℝ⁺
```
- Transition t is disabled if M(p) ≥ θ
- Example: Δ(ATP, PFK) = 5.0 mM

**Dynamic Threshold** (formula):
```
Δ(p,t) = f(M) : (P → ℝ₀⁺) → ℝ⁺
```
- Threshold depends on current marking M
- Example: Δ(ATP, PFK) = "2.0 * M(AMP)" (relative ATP/AMP ratio)

**Hill Equation** (cooperative inhibition):
```
Δ(p,t) = K₀.₅ⁿ / (K₀.₅ⁿ + M(p)ⁿ)
```
- K₀.₅: half-inhibitory concentration
- n: Hill coefficient (cooperativity)
- Returns value in [0,1], interpreted as "effective threshold"
- n = 1: Non-cooperative (hyperbolic)
- n > 1: Positive cooperativity (sigmoidal, ultrasensitive)
- n < 1: Negative cooperativity

**Example** (PFK allosteric inhibition by ATP):
```
Δ(ATP, PFK) = 5.0⁴ / (5.0⁴ + M(ATP)⁴)
```
- K₀.₅ = 5.0 mM, n = 4 (highly cooperative)
- When M(ATP) = 2.0 mM: Δ ≈ 0.975 (almost no inhibition)
- When M(ATP) = 5.0 mM: Δ = 0.5 (half-maximal inhibition)
- When M(ATP) = 10.0 mM: Δ ≈ 0.06 (strong inhibition)

**Implementation Note**: Threshold formulas are stored as strings and evaluated at runtime:
```python
threshold_formula = "5.0**4 / (5.0**4 + M_ATP**4)"
delta_value = eval(threshold_formula, {"M_ATP": current_marking["ATP"]})
if current_marking["ATP"] >= delta_value:
    transition_enabled = False
```

### 4.2.7 Transition Type Classification

**τ: T → {Continuous, Stochastic, Timed, Burst}: Transition Type**

Assigns each transition to one of four execution modes.

**1. Continuous Transitions** (τ(t) = Continuous)
- **Semantics**: Ordinary Differential Equations (ODE)
- **Dynamics**: dM/dt = Φ(t, M)
- **Rate**: Real-valued, positive (e.g., 0.5 mM/s)
- **Time**: Continuous, smooth evolution
- **Integration**: Euler, Runge-Kutta, adaptive step size
- **Biological Examples**:
  - Enzyme-catalyzed reactions (Michaelis-Menten)
  - Metabolic fluxes (glycolysis, TCA cycle)
  - Fast protein-protein interactions

**2. Stochastic Transitions** (τ(t) = Stochastic)
- **Semantics**: Gillespie Stochastic Simulation Algorithm (SSA)
- **Dynamics**: Discrete events, exponentially distributed inter-event times
- **Propensity**: a(t) = k · ∏M(p)
- **Time**: Continuous, but fires at discrete time points
- **Algorithm**: 
  1. Compute propensities a(t) for all enabled transitions
  2. Total propensity: a₀ = Σa(t)
  3. Time to next event: τ ~ Exp(a₀)
  4. Select transition with probability a(t)/a₀
- **Biological Examples**:
  - Gene transcription (low copy number)
  - Gene translation (mRNA → protein)
  - Binding/unbinding events (TF + DNA)
  - Degradation (mRNA decay, protein degradation)

**3. Timed Transitions** (τ(t) = Timed)
- **Semantics**: Deterministic delay
- **Dynamics**: Fires exactly τ_delay time units after becoming enabled
- **Delay**: Fixed duration (e.g., 30 minutes)
- **Time**: Scheduled, predictable
- **Biological Examples**:
  - Cell cycle checkpoints (G1/S, G2/M transitions)
  - Circadian rhythm oscillations (24-hour period)
  - Developmental stages (timed differentiation)

**4. Burst Transitions** (τ(t) = Burst)
- **Semantics**: Random bursts with two-parameter model
- **Inter-burst interval**: Exponentially distributed, rate λ_burst
- **Burst size**: Geometrically distributed, mean μ_size
- **Time**: Discrete bursts at random times
- **Biological Examples**:
  - Transcriptional bursting (mRNA produced in pulses)
  - Promoter switching (ON/OFF states)
  - Bursty protein production

**Heterogeneity**: A single model can contain transitions of all four types simultaneously. This enables **multi-scale temporal modeling**:
- Fast reactions (continuous, milliseconds to seconds)
- Medium reactions (stochastic, seconds to minutes)
- Slow reactions (timed, minutes to hours)
- Pulsatile events (burst, irregular)

**Example** (Energy Sensing Motif):
```
τ(PFK_reaction) = Continuous         # Enzyme kinetics (fast)
τ(PK_reaction) = Continuous          # Enzyme kinetics (fast)
τ(PFK_gene_transcription) = Burst   # mRNA bursts (slow, pulsatile)
τ(PFK_mRNA_translation) = Stochastic # Protein synthesis (medium)
τ(Cell_division) = Timed             # Fixed 90-minute cycle
```

### 4.2.8 Biochemical Reaction Formulas

**ρ: T → BiochemicalFormula: Stoichiometry with Elemental Composition**

Maps each transition to a reaction formula specifying elemental composition.

**Format**:
```
ρ(t) = "reactant1 + reactant2 + ... → product1 + product2 + ..."
```

Where each reactant/product is a biochemical formula (e.g., C6H12O6).

**Example** (Hexokinase):
```
ρ(Hexokinase) = "C6H12O6 + C10H16N5O13P3 → C6H11O9P + C10H16N5O10P2 + H"
```
Expands to: Glucose + ATP → Glucose-6-phosphate + ADP + H⁺

**Elemental Decomposition**:
Each formula is parsed into elemental counts:
```
Glucose:     C6H12O6      → {C: 6, H: 12, O: 6}
ATP:         C10H16N5O13P3 → {C: 10, H: 16, N: 5, O: 13, P: 3}
G6P:         C6H11O9P     → {C: 6, H: 11, O: 9, P: 1}
ADP:         C10H16N5O10P2 → {C: 10, H: 16, N: 5, O: 10, P: 2}
H⁺:          H            → {H: 1}
```

**Elemental Balance Check**:
For each element e ∈ {C, H, O, N, P, S}:
```
Σ(atoms[e] in reactants) = Σ(atoms[e] in products)
```

For hexokinase:
- Carbon: 6 + 10 = 16 (left), 6 + 10 = 16 (right) ✓
- Hydrogen: 12 + 16 = 28 (left), 11 + 16 + 1 = 28 (right) ✓
- Oxygen: 6 + 13 = 19 (left), 9 + 10 = 19 (right) ✓
- Nitrogen: 0 + 5 = 5 (left), 0 + 5 = 5 (right) ✓
- Phosphorus: 0 + 3 = 3 (left), 1 + 2 = 3 (right) ✓

**If unbalanced**: Flag as **stoichiometry error**

**Elemental Balance Matrix** S_e:
- Rows: Transitions t ∈ T
- Columns: Elements e ∈ {C, H, O, N, P, S}
- Entry S_e[t,e]: Net element change for transition t
  ```
  S_e[t,e] = Σ(atoms[e] in products) - Σ(atoms[e] in reactants)
  ```
- **Well-balanced network**: S_e[t,e] = 0 for all t, e

**Source/Sink Detection**:
- **Elemental source**: Transition t where S_e[t,e] > 0 (creates atoms)
- **Elemental sink**: Transition t where S_e[t,e] < 0 (destroys atoms)
- **Valid**: Transport across system boundary (import/export)
- **Invalid**: Internal reaction violates conservation laws

---

## 4.3 Arc Type Semantics and Firing Rules

### 4.3.1 Composite Enabling Condition

A transition **t is enabled** at marking M if and only if **ALL** of the following hold:

**Condition 1**: **Normal arcs** (substrates available)
```
∀p ∈ •t: M(p) ≥ W(p,t)
```
All input places have sufficient tokens.

**Condition 2**: **Test arcs** (catalysts present)
```
∀(p,t) ∈ Σ: M(p) > 0
```
All catalyst places are non-empty.

**Condition 3**: **Inhibitor arcs** (inhibitors below threshold)
```
∀(p,t) ∈ Θ: M(p) < Δ(p,t)
```
All inhibitor places are below their respective thresholds.

**Condition 4**: **Capacity constraint** (outputs not full)
```
∀p ∈ t•: M(p) + W(t,p) ≤ K(p)
```
Firing would not exceed place capacities.

**Notation**: **M[t⟩** means "transition t is enabled at marking M"

### 4.3.2 Firing Semantics by Arc Type

When enabled transition t fires (M[t⟩M'), the new marking M' is computed as follows:

**Normal arcs** (F):
```
If (p,t) ∈ F: M'(p) = M(p) - W(p,t)    # Consume tokens
If (t,p) ∈ F: M'(p) = M(p) + W(t,p)    # Produce tokens
```

**Test arcs** (Σ):
```
If (p,t) ∈ Σ: M'(p) = M(p)             # Unchanged (read-only)
```

**Inhibitor arcs** (Θ):
```
If (p,t) ∈ Θ: M'(p) = M(p)             # Unchanged (regulation only)
```

**All other places**:
```
M'(p) = M(p)                            # Unchanged
```

**Summary**: Only places connected by **normal arcs** change their marking. Test arcs and inhibitor arcs are **non-consumptive**.

### 4.3.3 Firing Semantics by Transition Type

**Continuous transitions** (τ(t) = Continuous):
- **Dynamics**: dM/dt = Φ(t, M) · (consumption and production vectors)
- **Interpretation**: Rate of change proportional to rate function
- **Example**: dM(Glucose)/dt = -Φ(Hexokinase) (glucose consumed)

**Stochastic transitions** (τ(t) = Stochastic):
- **Dynamics**: Discrete firing at exponentially distributed times
- **Inter-event time**: τ ~ Exp(a(t))
- **Tokens updated**: Instantaneous change (M → M')

**Timed transitions** (τ(t) = Timed):
- **Dynamics**: Fires exactly Delay(τ_delay) after becoming enabled
- **Example**: G1/S checkpoint fires 30 minutes after conditions met

**Burst transitions** (τ(t) = Burst):
- **Dynamics**: Exponential inter-burst interval, geometric burst size
- **Tokens updated**: Batch production (e.g., 5 mRNA molecules at once)

### 4.3.4 Example: Hexokinase Reaction

**Biological reaction**:
```
Glucose + ATP --[Hexokinase]--> Glucose-6-phosphate + ADP
```

**Extended Bio-PN representation**:
```
Places:
  P1: Glucose (C6H12O6), M₀ = 5.0 mM
  P2: ATP (C10H16N5O13P3), M₀ = 2.5 mM
  P3: Glucose-6-phosphate (C6H11O9P), M₀ = 0.0 mM
  P4: ADP (C10H16N5O10P2), M₀ = 0.5 mM
  P5: Hexokinase (enzyme), M₀ = 0.1 mM

Transition:
  T1: Hexokinase_reaction
  τ(T1) = Continuous
  Φ(T1) = (Vmax · [Glucose] · [ATP]) / (Km + [Glucose]·[ATP])
    where Vmax = 70 mM/s, Km = 0.1 mM²

Arcs:
  Normal arcs (F):
    (P1, T1) with W = 1  # Glucose consumed
    (P2, T1) with W = 1  # ATP consumed
    (T1, P3) with W = 1  # G6P produced
    (T1, P4) with W = 1  # ADP produced
  
  Test arc (Σ):
    (P5, T1)  # Hexokinase catalyzes (not consumed)

Biochemical formula:
  ρ(T1) = "C6H12O6 + C10H16N5O13P3 → C6H11O9P + C10H16N5O10P2 + H"
```

**Enabling condition**:
```
M(Glucose) ≥ 1  AND  M(ATP) ≥ 1  AND  M(Hexokinase) > 0
```

**Firing** (continuous semantics):
```
dM(Glucose)/dt = -Φ(T1)
dM(ATP)/dt = -Φ(T1)
dM(G6P)/dt = +Φ(T1)
dM(ADP)/dt = +Φ(T1)
dM(Hexokinase)/dt = 0  # Enzyme conserved
```

**Elemental balance**:
- C: 6 + 10 = 6 + 10 ✓
- H: 12 + 16 = 11 + 16 + 1 ✓
- O: 6 + 13 = 9 + 10 ✓
- N: 5 = 5 ✓
- P: 3 = 1 + 2 ✓

### 4.3.5 Example: PFK with ATP Feedback Inhibition

**Biological reaction**:
```
Fructose-6-phosphate + ATP --[PFK]--> Fructose-1,6-bisphosphate + ADP
  (Inhibited by high ATP via allosteric site)
```

**Extended Bio-PN representation**:
```
Places:
  P1: Fructose-6-phosphate (F6P), M₀ = 2.0 mM
  P2: ATP, M₀ = 3.0 mM
  P3: Fructose-1,6-bisphosphate (F-1,6-BP), M₀ = 0.5 mM
  P4: ADP, M₀ = 1.0 mM
  P5: PFK (enzyme), M₀ = 0.05 mM

Transition:
  T1: PFK_reaction
  τ(T1) = Continuous
  Φ(T1) = (Vmax · [F6P] · [ATP]) / (Km + [F6P]·[ATP])
    where Vmax = 90 mM/s, Km = 0.2 mM²

Arcs:
  Normal arcs (F):
    (P1, T1) with W = 1  # F6P consumed
    (P2, T1) with W = 1  # ATP consumed (catalytic site)
    (T1, P3) with W = 1  # F-1,6-BP produced
    (T1, P4) with W = 1  # ADP produced
  
  Test arc (Σ):
    (P5, T1)  # PFK enzyme catalyzes
  
  Inhibitor arc (Θ):
    (P2, T1)  # ATP inhibits (allosteric site)
    Δ(P2, T1) = 5.0⁴ / (5.0⁴ + M(ATP)⁴)  # Hill equation, K₀.₅=5.0 mM, n=4

Biochemical formula:
  ρ(T1) = "C6H10O9P + C10H16N5O13P3 → C6H10O12P2 + C10H16N5O10P2 + H"
```

**Enabling condition**:
```
M(F6P) ≥ 1  AND  M(ATP) ≥ 1  AND  M(PFK) > 0  AND  M(ATP) < Δ(ATP, PFK)
```

**Scenarios**:

1. **Low ATP** (M(ATP) = 2.0 mM):
   ```
   Δ(ATP, PFK) = 5.0⁴/(5.0⁴+2.0⁴) = 625/(625+16) ≈ 0.975
   M(ATP) = 2.0 < 0.975? NO (wait, this is normalized)
   
   Correct interpretation:
   Inhibition strength = M(ATP)⁴/(5.0⁴ + M(ATP)⁴) = 16/641 ≈ 0.025 (2.5% inhibited)
   → PFK is ACTIVE (97.5% activity)
   ```

2. **Medium ATP** (M(ATP) = 5.0 mM):
   ```
   Inhibition strength = 5.0⁴/(5.0⁴ + 5.0⁴) = 0.5 (50% inhibited)
   → PFK is MODERATELY ACTIVE (50% activity)
   ```

3. **High ATP** (M(ATP) = 10.0 mM):
   ```
   Inhibition strength = 10.0⁴/(5.0⁴ + 10.0⁴) = 10000/10625 ≈ 0.941 (94% inhibited)
   → PFK is INHIBITED (6% activity remaining)
   ```

**Biological interpretation**: 
- When energy is LOW (ATP < 5 mM): Glycolysis proceeds (PFK active, produce more ATP)
- When energy is HIGH (ATP > 5 mM): Glycolysis slows (PFK inhibited, conserve glucose)

---

## 4.4 Well-Formedness Constraints

An Extended Bio-PN must satisfy the following structural constraints:

**C1: Disjointness of Arc Types**
```
F ∩ Σ = ∅  AND  F ∩ Θ = ∅  AND  Σ ∩ Θ = ∅
```
Arc types are mutually exclusive. A place cannot be simultaneously:
- Substrate (normal arc) and catalyst (test arc) for same transition
- Substrate (normal arc) and inhibitor (inhibitor arc) for same transition
- Catalyst (test arc) and inhibitor (inhibitor arc) for same transition

**C2: No Self-Loops via Test/Inhibitor Arcs**
```
∀(p,t) ∈ Σ: p ∉ t•  (test arc source not in postset)
∀(p,t) ∈ Θ: p ∉ t•  (inhibitor arc source not in postset)
```
Prevents circular dependencies where transition affects its own enabling condition.

**C3: Positive Arc Weights**
```
∀f ∈ F: W(f) > 0
```
All normal arcs have positive integer weights (stoichiometry must be ≥ 1).

**C4: Positive Thresholds**
```
∀(p,t) ∈ Θ: Δ(p,t) > 0
```
All inhibitor thresholds are positive (zero threshold = always inhibited, meaningless).

**C5: Non-Negative Initial Marking**
```
∀p ∈ P: M₀(p) ≥ 0
```
Token counts and concentrations cannot be negative.

**C6: Place Capacity Consistency**
```
∀p ∈ P: M₀(p) ≤ K(p)
```
Initial marking must respect place capacities.

**C7: Biochemical Formula Validity**
```
∀t ∈ T: ElementalBalance(ρ(t)) = True
```
All reaction formulas must conserve atoms (C, H, O, N, P, S).

**C8: Rate Function Compatibility**
```
∀t ∈ T: Φ(t) is compatible with τ(t)
```
- Continuous transitions: Rate function returns ℝ⁺
- Stochastic transitions: Propensity function returns ℝ⁺
- Timed transitions: Delay function returns ℝ⁺
- Burst transitions: Burst parameters (λ, μ) ∈ ℝ⁺

---

## 4.5 Comparison with Classical Petri Nets

| Feature | Classical PN | Extended Bio-PN | Biological Benefit |
|---------|-------------|-----------------|-------------------|
| **Arc Types** | 1 (normal, consumptive) | 3 (normal, test, inhibitor) | Enzymes (catalysis), Repressors (inhibition) |
| **Enabling** | Input tokens ≥ weights | + Catalysts present + Inhibitors below threshold | Regulatory control visible in topology |
| **Firing** | Consumes all inputs | Test/inhibitor arcs non-consumptive | Enzyme conservation, feedback loops |
| **Transition Types** | Homogeneous (all same) | 4 types (continuous, stochastic, timed, burst) | Multi-scale temporal dynamics |
| **Token Semantics** | Abstract (counts only) | Biochemical formulas (C6H12O6) | Elemental balance validation |
| **Regulation** | External (in code) | Embedded (threshold formulas on arcs) | Visually analyzable, topology-encoded |
| **Parallelism** | Strong independence (disjoint neighborhoods) | Weak independence (disjoint inputs, shared outputs/catalysts) | Biological cooperativity, 2-4× speedup |
| **Stoichiometry** | Integer weights | + Elemental composition | Atomic-level mass balance |

---

## 4.6 Graphical Notation

**Places** (circles):
- **○** Metabolite, enzyme, mRNA, protein (standard circle)
- **◎** Gene (double circle, typically discrete marking)
- Label: Place name (e.g., "Glucose", "ATP")
- Inside: Token count or concentration (e.g., "5.0 mM" or "●●●" for 3 tokens)

**Transitions** (rectangles or bars):
- **▬** Continuous transition (solid bar)
- **▭** Stochastic transition (dotted rectangle)
- **▬◷** Timed transition (clock symbol)
- **▬⚡** Burst transition (lightning symbol)
- Label: Transition name (e.g., "Hexokinase", "lacZ_transcription")

**Arcs**:
- **→** Normal arc (solid arrow): Consumption/production
  - Weight label: Integer (e.g., "2" for 2 ATP consumed)
- **⤏** Test arc (dashed arrow): Catalysis, non-consumptive
- **⊸** Inhibitor arc (circle-headed arrow): Threshold-based blocking
  - Threshold label: Value or formula (e.g., "≥ 5.0 mM" or "Hill(K=5, n=4)")

**Example Diagram** (Hexokinase):
```
          [Enzyme]
     Hexokinase (0.1 mM)
             |
             | (test arc, dashed)
             ⤏
Glucose ──→ [Hexokinase] ──→ Glucose-6-P
(5.0 mM)  ▬ Continuous ▬   (0.0 mM)
ATP ──────→ [Hexokinase] ──→ ADP
(2.5 mM)                    (0.5 mM)

Rate: Vmax·[Glc]·[ATP]/(Km+[Glc]·[ATP])
```

**Example Diagram** (PFK with inhibition):
```
              [Enzyme]
         PFK (0.05 mM)
               |
               | (test arc)
               ⤏
F6P ──→ [PFK_reaction] ──→ F-1,6-BP
        ▬ Continuous ▬
ATP ──→ [PFK_reaction] ──→ ADP
  |
  |
  ⊸ (inhibitor arc, threshold: K₀.₅=5.0 mM, n=4)

When M(ATP) > 5.0 mM: PFK strongly inhibited
When M(ATP) < 5.0 mM: PFK active
```

---

## 4.7 Summary

The **Extended Biological Petri Net** formalism extends classical Petri nets with:

1. **Three arc types**: Normal (consumption), test (catalysis), inhibitor (regulation)
2. **Four transition types**: Continuous, stochastic, timed, burst
3. **Biochemical formulas**: Elemental composition tracking (C/H/O/N/P/S)
4. **Threshold formulas**: Hill equations, dynamic thresholds on inhibitor arcs
5. **Weak independence**: Shared outputs/catalysts allowed (cooperativity + parallelism)

These extensions enable:
- ✅ **Enzyme conservation**: Test arcs preserve catalyst levels
- ✅ **Multi-scale dynamics**: Continuous kinetics + stochastic bursts + timed events
- ✅ **Topology-embedded regulation**: Thresholds visible on arcs, not hidden in code
- ✅ **Atomic-level validation**: Stoichiometry checked via elemental balance
- ✅ **Biological cooperativity**: Shared places allowed (weak independence theory)

**Next chapter** (Chapter 5) formalizes **weak independence theory**, the primary theoretical contribution enabling parallel execution with shared places.
