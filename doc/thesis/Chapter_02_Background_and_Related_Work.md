# Chapter 2: Background and Related Work

## 2.1 Petri Net Fundamentals

### 2.1.1 Classical Petri Nets

**Petri nets**, introduced by Carl Adam Petri in 1962, are a mathematical formalism for modeling concurrent systems. A **classical Petri net** is a 5-tuple:

$$
PN = (P, T, F, W, M_0)
$$

Where:
- **P**: Finite set of **places** (circles, represent conditions or resources)
- **T**: Finite set of **transitions** (rectangles, represent events or actions)
- **F ⊆ (P × T) ∪ (T × P)**: **Flow relation** (arcs connecting places to transitions and vice versa)
- **W: F → ℕ⁺**: **Weight function** (arc multiplicities, stoichiometric coefficients)
- **M₀: P → ℕ**: **Initial marking** (token distribution at time t=0)

**Graphical notation**:
- **Places**: Circles containing tokens (black dots)
- **Transitions**: Rectangles or bars
- **Arcs**: Arrows with weights (omitted if weight = 1)

**Example** (Simple chemical reaction A + B → C):
```
   (A)●●     (B)●
    │  ╲    ╱
    │   ╲  ╱
    │    T1
    │   ╱  ╲
    │  ╱    ╲
   (C)       
```
- Places: P = {A, B, C}
- Transitions: T = {T1}
- Arcs: F = {(A,T1), (B,T1), (T1,C)}
- Weights: W(A,T1)=1, W(B,T1)=1, W(T1,C)=1
- Initial marking: M₀(A)=2, M₀(B)=1, M₀(C)=0

### 2.1.2 Petri Net Semantics

**Enabling**: Transition t is **enabled** at marking M if:
$$
\forall p \in \bullet t: M(p) \geq W(p,t)
$$

Where $\bullet t$ denotes the **preset** (input places) of t.

**Firing**: When enabled transition t fires:
1. **Consume tokens** from input places: $M'(p) = M(p) - W(p,t)$ for all $p \in \bullet t$
2. **Produce tokens** at output places: $M'(p) = M(p) + W(t,p)$ for all $p \in t\bullet$

Where $t\bullet$ denotes the **postset** (output places) of t.

**Example** (A + B → C):
- **Before firing**: M = {A:2, B:1, C:0}
- **T1 enabled?** Yes (M(A)=2 ≥ 1, M(B)=1 ≥ 1)
- **T1 fires**: Consume 1 token from A, 1 from B, produce 1 at C
- **After firing**: M' = {A:1, B:0, C:1}

### 2.1.3 Petri Net Properties

**Behavioral properties**:
- **Reachability**: Can marking M' be reached from M₀?
- **Boundedness**: Is there a maximum token count per place?
- **Liveness**: Can all transitions eventually fire?
- **Deadlock-freedom**: Does the net avoid states where no transition is enabled?

**Structural properties** (independent of M₀):
- **P-invariants** (place invariants): Token-conserving sets of places
  - Linear combination: $y^T \cdot M = y^T \cdot M_0$ (constant sum)
  - Example: Enzyme conservation (E_free + E_bound = constant)
- **T-invariants** (transition invariants): Firing sequences returning to same marking
  - Example: Catalytic cycles (net effect = 0)

**Complexity**:
- **Reachability**: EXPSPACE-complete (decidable but computationally hard)
- **Boundedness**: EXPSPACE-complete
- **Liveness**: EXPSPACE-complete

### 2.1.4 Limitations for Biological Modeling

**Classical Petri nets have fundamental limitations**:

1. **No regulatory arcs**: Cannot represent catalysis (enzyme unchanged) or inhibition (threshold blocking) without encoding in external code
2. **Homogeneous transitions**: All transitions fire instantaneously (no continuous kinetics) or all are timed (no stochastic bursts)
3. **Strong independence only**: Parallelism requires disjoint neighborhoods (no shared places)
4. **Token abstraction**: Tokens are abstract units (not molecules with formulas)
5. **No rate semantics**: Firing frequency is non-deterministic or requires external rate assignment

**These gaps motivate extensions** for systems biology.

---

## 2.2 Petri Net Extensions

### 2.2.1 Colored Petri Nets (CPN)

**Jensen (1981)** introduced **colored Petri nets** where tokens have **data types** (colors):
- Places hold **multisets of colored tokens** (e.g., {glucose:5, fructose:2})
- Transitions have **guards** (boolean predicates) and **arc expressions** (token transformations)
- Enables modeling complex data structures (proteins with phosphorylation states)

**Advantages**:
- **Compactness**: One place can represent multiple species (different colors)
- **Data manipulation**: Arc expressions compute token transformations

**Limitations for biology**:
- **Complexity**: Guards and expressions are code (not visual arcs)
- **Analysis difficulty**: Structural properties (P-invariants) are harder to compute
- **No heterogeneous dynamics**: Still lacks native continuous/stochastic/burst transitions

### 2.2.2 Timed Petri Nets

**Ramchandani (1974)** added **time delays** to transitions:
- Transitions fire after a **deterministic delay** (e.g., 5 seconds)
- Models sequential processes with known durations

**Merlin (1974)** introduced **time intervals**:
- Transitions fire within a time window [tₘᵢₙ, tₘₐₓ]
- Non-deterministic timing

**Limitations**:
- **Still discrete**: No continuous state evolution (ODEs)
- **Homogeneous**: All transitions timed (cannot mix with stochastic)

### 2.2.3 Stochastic Petri Nets (SPN)

**Molloy (1981)** introduced **stochastic Petri nets**:
- Transitions fire after **exponentially distributed delays** (rate λ)
- Equivalent to continuous-time Markov chains (CTMC)
- Enables performance analysis (throughput, mean response time)

**Generalized Stochastic Petri Nets (GSPN)** (Ajmone Marsan et al., 1984):
- **Immediate transitions** (fire instantly, priority 0)
- **Timed transitions** (exponential delays)

**Applications to biology**:
- **Gene expression**: Transcription/translation as stochastic events
- **Molecular interactions**: Binding/unbinding with rate constants

**Limitations**:
- **Exponential assumption**: Not all biological processes are memoryless
- **State space explosion**: Large models (>100 places) are intractable
- **No continuous kinetics**: Cannot model enzyme saturation (Michaelis-Menten)

### 2.2.4 Hybrid Petri Nets

**David & Alla (1992)** introduced **continuous and hybrid Petri nets**:
- **Continuous places**: Hold real-valued token counts (not integers)
- **Continuous transitions**: Fire continuously with rate dM/dt = v(M)
- **Hybrid nets**: Mix discrete and continuous places/transitions

**Semantics**:
- Continuous transitions: $\frac{dM(p)}{dt} = \sum_{t} v_t \cdot W(t,p) - \sum_{t} v_t \cdot W(p,t)$
- Rate function v_t depends on marking (e.g., mass action: v = k·M(substrate))

**Advantages for biology**:
- **Enzyme kinetics**: Continuous transitions model Michaelis-Menten rates
- **Multi-scale**: Proteins (discrete) + metabolites (continuous) in one model

**Limitations**:
- **No weak independence theory**: Parallel execution with shared places undefined
- **Limited arc types**: No explicit test/inhibitor arc semantics
- **No biochemical formulas**: Tokens are still abstract (no elemental composition)

### 2.2.5 Comparison Summary

| Feature | Classical | Colored | Timed | Stochastic | Hybrid |
|---------|-----------|---------|-------|------------|--------|
| Token types | Abstract | Data types | Abstract | Abstract | Real-valued |
| Dynamics | Discrete | Discrete | Timed | Stochastic | Continuous + Discrete |
| Regulation | No | Guards (code) | No | No | Rate functions |
| Parallelism | Strong independence | Strong independence | Strong independence | Strong independence | Undefined |
| Biological fit | Low | Medium | Medium | Medium | High |

**Gap**: No existing extension provides **weak independence**, **arc-level regulation**, **biochemical formulas**, and **heterogeneous transition coexistence**.

---

## 2.3 Biological Petri Nets (Bio-PN)

### 2.3.1 Early Work (1990s)

**Reddy et al. (1993)**: "Petri Net Representations in Metabolic Pathways"
- First formal application of Petri nets to biochemistry
- Modeled glycolysis (10 reactions) as classical Petri net
- **Contribution**: Showed Petri nets can represent metabolic stoichiometry
- **Limitation**: No kinetics (only qualitative), no regulation

**Hofestädt (1994)**: "A Petri Net Application to Model Metabolic Processes"
- Extended Reddy's work with enzyme catalysis
- Used **colored tokens** to distinguish substrates/products
- **Limitation**: Still no quantitative kinetics

### 2.3.2 Qualitative Bio-PNs (2000s)

**Heiner et al. (2008)**: "Petri Nets for Systems and Synthetic Biology"
- Developed **qualitative Bio-PNs** for signaling networks
- Encoded regulatory logic (activation, inhibition) as arc types
- **Tool**: Snoopy software (still actively maintained)
- **Contribution**: Standardized notation for biological arcs
- **Limitation**: Qualitative only (no kinetic parameters)

**Koch et al. (2011)**: "Modeling Threshold Effects in Biological Systems"
- Introduced **read arcs** (test arcs) and **inhibitor arcs**
- Threshold values for inhibition (e.g., M(p) < 5 blocks transition)
- **Limitation**: Thresholds are constants (not Hill equations), no heterogeneous transitions

### 2.3.3 Quantitative Bio-PNs

**Matsuno et al. (2003)**: "Hybrid Petri Net Representation of Gene Regulatory Networks"
- Hybrid Petri nets for gene regulation
- Continuous places (protein concentrations) + discrete places (gene states)
- **Tool**: Cell Illustrator (commercial)
- **Contribution**: First hybrid Bio-PN with kinetics
- **Limitation**: Proprietary formalism, no weak independence theory

**Gilbert & Heiner (2006)**: "From Petri Nets to Differential Equations"
- Automatic translation of continuous Petri nets to ODE systems
- Mass action kinetics assumed
- **Contribution**: Formalized PN→ODE mapping
- **Limitation**: Only mass action (no Michaelis-Menten, Hill), no stochastic bursts

### 2.3.4 Recent Developments (2010s-2020s)

**Blätke et al. (2015)**: "BioModel Engineering with Petri Nets"
- Comprehensive survey of Bio-PN tools and applications
- Case studies: Signaling (MAPK), metabolism (TCA), gene circuits
- **Contribution**: Unified terminology, best practices
- **Gap identified**: "No tool integrates metabolic kinetics with gene regulation"

**Liu & Heiner (2013)**: "Multiscale Modeling with Hybrid Petri Nets"
- Proposed framework for enzyme-catalyzed reactions + gene expression
- **Limitation**: Still requires two separate models (metabolism PN + regulation PN)

**Marwan et al. (2011)**: "Petri Nets in Snoopy: A Unifying Framework"
- Extended Snoopy with stochastic and hybrid PNs
- **Contribution**: Tool supporting multiple PN classes
- **Limitation**: No biochemical formula tracking, no weak independence analysis

### 2.3.5 Gap Analysis

**What existing Bio-PNs provide**:
- ✅ Stoichiometric modeling (metabolic pathways)
- ✅ Qualitative regulation (activation/inhibition arcs)
- ✅ Hybrid dynamics (continuous + discrete)
- ✅ Stochastic simulation (Gillespie algorithm)

**What is missing** (addressed by this thesis):
- ❌ **Weak independence theory**: Parallel execution with shared catalysts/outputs
- ❌ **Heterogeneous coexistence**: Continuous + stochastic + timed + burst in single model
- ❌ **Arc-level regulatory semantics**: Hill equations on inhibitor arcs (not just constants)
- ❌ **Biochemical formula tracking**: Elemental composition, atomic conservation
- ❌ **Integrated metabolic-genetic models**: Single formalism spanning both layers

---

## 2.4 Multi-Scale Biological Modeling

### 2.4.1 Genome-Scale Metabolic Models (GSMM)

**Flux Balance Analysis (FBA)** (Varma & Palsson, 1994):
- Models metabolism as **stoichiometric matrix** S (metabolites × reactions)
- **Steady-state assumption**: S · v = 0 (no accumulation)
- **Optimization**: Maximize biomass flux subject to constraints
- **Databases**: BiGG Models (7000+ curated GSMMs for bacteria, yeast, human)

**Advantages**:
- **Scalability**: Models 1000+ reactions (entire metabolism)
- **Predictive power**: Predicts growth rates, gene essentiality

**Limitations**:
- **No regulation**: Enzyme expression levels ignored (assumes all enzymes present)
- **No kinetics**: Flux directions but not rates (no time dynamics)
- **Steady-state only**: Cannot model transient responses

### 2.4.2 Gene Regulatory Networks (GRN)

**Boolean networks** (Kauffman, 1969):
- Genes are binary (on/off)
- Update rules: Gene_i(t+1) = f(Gene_j(t), Gene_k(t), ...)
- **Applications**: Cell differentiation, synthetic circuits

**Limitations**:
- **No concentrations**: Cannot represent "high vs. low ATP"
- **Discrete time**: Cannot model continuous dynamics
- **No metabolism**: Genes regulate each other, but metabolites absent

**Differential equation models**:
- Genes/proteins as continuous variables
- Example: $\frac{d[X]}{dt} = k_{synth} - k_{deg} \cdot [X]$
- **Advantages**: Quantitative, captures kinetics

**Limitations**:
- **Not compositional**: Adding genes requires rewriting equations
- **No visual topology**: Regulatory structure hidden in code
- **Separate from metabolism**: Metabolites not integrated

### 2.4.3 Integrated Approaches

**E-Cell** (Tomita et al., 1999):
- Software platform simulating whole-cell models
- Combines multiple formalisms (ODEs, Gillespie, rule-based)
- **Contribution**: Demonstrated feasibility of multi-scale simulation
- **Limitation**: Not a formal modeling language (software tool, not formalism)

**Virtual Cell** (Schaff et al., 1997):
- Spatial models with reaction-diffusion PDEs
- Compartments (cytoplasm, nucleus, membrane)
- **Contribution**: Spatial resolution
- **Limitation**: Computationally expensive, no formal analysis (P-invariants)

**Rule-based modeling** (BioNetGen, Kappa):
- Molecular interactions as rewrite rules
- Compactly represents protein complexes with many states
- **Contribution**: Handles combinatorial complexity (phosphorylation sites)
- **Limitation**: Not Petri nets (different formalism), no elemental balance

### 2.4.4 Why Current Approaches Fall Short

**Fundamental issue**: Existing multi-scale approaches either:
1. **Separate models**: Build metabolism model + regulation model, integrate ad-hoc (no formal semantics)
2. **Software-specific**: Tools provide integration (E-Cell, Virtual Cell) but no underlying formalism
3. **Limited scope**: Focus on one layer (GSMM for metabolism, GRN for regulation)

**This thesis provides**: A **formal Petri net extension** enabling integrated modeling with well-defined semantics, analyzability, and visual topology.

---

## 2.5 Systems Biology Standards and Databases

### 2.5.1 SBML (Systems Biology Markup Language)

**Hucka et al. (2003)**: XML format for biochemical models
- **Core**: Species, reactions, compartments, parameters
- **Extensions**: SBML-qual (qualitative GRNs), SBML-comp (model composition)
- **Support**: 300+ tools read/write SBML

**Advantages**:
- **Interoperability**: Exchange models between tools
- **Standardization**: Widely adopted (>10,000 models)

**Limitations**:
- **Not a formalism**: SBML is a data format, not a modeling language
- **Separate qualitative/quantitative**: SBML (kinetics) vs. SBML-qual (Boolean logic) are disconnected
- **No formal semantics**: Tool-dependent interpretation

### 2.5.2 KEGG (Kyoto Encyclopedia of Genes and Genomes)

**Kanehisa et al. (2000)**: Database of biological pathways
- **KEGG COMPOUND**: 18,000+ metabolites (formulas, structures)
- **KEGG REACTION**: 11,000+ reactions (stoichiometry, EC numbers)
- **KEGG PATHWAY**: 500+ reference pathways (glycolysis, TCA, etc.)
- **REST API**: Programmatic access (Chapter 9 uses this)

**Usage in modeling**:
- Import pathways (reaction stoichiometry)
- Fetch compound formulas (C₆H₁₂O₆ for glucose)
- Link to enzymes (EC numbers)

**Limitations**:
- **Incomplete stoichiometry**: Often omits cofactors (H₂O, H⁺)
- **No kinetics**: Reaction topology only, no rate constants

### 2.5.3 BRENDA (Enzyme Database)

**Schomburg et al. (2004)**: Comprehensive enzyme kinetics
- **2.7 million** parameter entries (Km, kcat, Ki, pH optima)
- **83,000+ enzymes** classified by EC number
- **Organism-specific**: Data from bacteria, yeast, human, etc.
- **SOAP API**: Programmatic access (Chapter 10 uses this)

**Applications**:
- Parameter inference for models (Km for glucose ≈ 0.1 mM)
- Organism-specific parameterization (yeast vs. human kinetics)

**Challenges**:
- **High variance**: Same enzyme, different labs → 10× differences
- **Incomplete coverage**: Not all enzymes have kinetic data

### 2.5.4 Other Databases

**ChEBI** (Chemical Entities of Biological Interest):
- Molecular structures, formulas, synonyms
- More detailed than KEGG (includes protonation states)

**SABIO-RK** (Reaction Kinetics Database):
- Curated kinetic laws (full rate equations, not just Km)
- Smaller than BRENDA (50,000 entries) but higher quality

**BiGG Models**:
- Genome-scale metabolic reconstructions
- Flux constraints, gene-protein-reaction associations

**Integration in this thesis**:
- **KEGG**: Formula retrieval (Chapter 9)
- **BRENDA**: Parameter inference (Chapter 10)
- **ChEBI**: Fallback for formulas (future work)

---

## 2.6 Related Tools

### 2.6.1 Snoopy (Brandenburg University of Technology)

**Heiner et al. (2012)**: "Snoopy - A Unifying Petri Net Tool"
- **Supports**: Classical, timed, stochastic, hybrid Petri nets
- **Features**:
  - Graphical editor (drag-and-drop)
  - Simulation (ODE, Gillespie, hybrid)
  - Model checking (CTL properties)
  - SBML import/export
- **Biological focus**: Signaling networks, metabolic pathways

**Strengths**:
- Open-source, actively maintained
- Excellent visualization
- Structural analysis (P-invariants, reachability graph)

**Limitations**:
- **No weak independence analysis**: Parallelism not exploited
- **No biochemical formulas**: Tokens are abstract
- **Limited regulation**: Inhibitor arcs have constant thresholds (no Hill equations)
- **Separate models for metabolism/regulation**: No unified formalism

### 2.6.2 Cell Illustrator (University of Tokyo)

**Nagasaki et al. (2010)**: Hybrid Petri net tool
- **Hybrid dynamics**: Continuous + discrete + stochastic
- **Biological templates**: Gene expression, signaling cascades
- **3D visualization**: Network layout algorithms

**Strengths**:
- Powerful hybrid simulation
- Large library of biological models

**Limitations**:
- **Proprietary**: Commercial license required (not open-source)
- **Custom formalism**: Not standard Petri nets (tool-specific notation)
- **No KEGG/BRENDA integration**: Manual parameter entry

### 2.6.3 COPASI (Complex Pathway Simulator)

**Hoops et al. (2006)**: Biochemical system simulator
- **ODE simulation**: Deterministic, stochastic (Gillespie), hybrid
- **Parameter estimation**: Fit models to experimental data
- **Optimization**: Metabolic flux optimization
- **SBML support**: Import/export

**Strengths**:
- Widely used (5000+ citations)
- Parameter fitting (least-squares, genetic algorithms)
- Sensitivity analysis

**Limitations**:
- **Not Petri nets**: Reaction network formalism (different from PNs)
- **No regulation arcs**: Inhibition encoded in rate laws (not topology)
- **Single-scale**: Metabolism-focused (gene regulation requires separate SBML-qual model)

### 2.6.4 CellDesigner (Systems Biology Institute)

**Funahashi et al. (2003)**: Visual SBML editor
- **Graphical notation**: Process diagrams (SBGN standard)
- **SBML generation**: Automatically creates SBML from diagrams
- **Simulation**: Integrates with COPASI, CellML

**Strengths**:
- User-friendly visual editor
- SBML standardization

**Limitations**:
- **Not Petri nets**: Process diagrams (different semantics)
- **No formal analysis**: Cannot compute P-invariants, reachability
- **Separate regulation**: Metabolic and regulatory diagrams disconnected

### 2.6.5 Charlie (Model Checker)

**Heiner et al. (2015)**: Verification tool for Petri nets
- **Model checking**: CTL, LTL temporal logic properties
- **Symbolic methods**: BDDs for state space exploration
- **Biological properties**: Verifies liveness, boundedness, reachability

**Strengths**:
- Formal verification (prove properties hold)
- Handles large state spaces (symbolic encoding)

**Limitations**:
- **Verification only**: Not a modeling tool (requires Snoopy for model creation)
- **No kinetics**: Qualitative properties only (not quantitative simulation)

### 2.6.6 Comparison Summary

| Tool | Type | Hybrid | Regulation | KEGG/BRENDA | Weak Independence | Formula Tracking |
|------|------|--------|------------|-------------|-------------------|------------------|
| Snoopy | Petri net | Yes | Limited | No | No | No |
| Cell Illustrator | Hybrid PN | Yes | Yes | No | No | No |
| COPASI | ODE/Gillespie | Yes | Rate laws | No | N/A | No |
| CellDesigner | SBML editor | Via tools | Process diagrams | No | N/A | No |
| Charlie | Model checker | Yes | Yes | No | No | No |
| **SHYpn (this thesis)** | Extended Bio-PN | Yes | Arc-level | Yes | Yes | Yes |

**Key differentiator**: SHYpn is the **first tool** providing:
1. Weak independence-based parallelism
2. Arc-level regulation (Hill equations on inhibitor arcs)
3. Biochemical formula tracking (elemental balance)
4. Automated KEGG/BRENDA integration

---

## 2.7 Theoretical Foundations

### 2.7.1 Concurrency Theory

**Independence of transitions** (classical definition):
- Transitions t₁, t₂ are **independent** if:
  - $(\bullet t_1 \cup t_1\bullet) \cap (\bullet t_2 \cup t_2\bullet) = \emptyset$
  - (No shared places in neighborhoods)
- **Consequence**: Can fire **concurrently** without conflict

**Diamond property** (Mazurkiewicz, 1987):
- If t₁, t₂ are independent and both enabled at M:
  - M →^{t₁} M₁ →^{t₂} M₁₂
  - M →^{t₂} M₂ →^{t₁} M₁₂
  - (Same final state M₁₂ regardless of order)

**Limitation for biology**:
- Enzymes catalyze multiple reactions (shared place) → Not independent by classical definition
- But **biologically**, these reactions don't conflict (enzyme is preserved)

**This thesis contribution**: Weak independence relaxes the condition to allow shared test arcs and outputs while preserving diamond property.

### 2.7.2 Process Calculi

**CCS** (Calculus of Communicating Systems, Milner 1980):
- Algebraic formalism for concurrent processes
- Composition operator (P | Q) runs P, Q in parallel

**π-calculus** (Milner et al., 1992):
- Extends CCS with mobile processes (channels can be passed)

**Stochastic π-calculus** (Priami, 1995):
- Adds stochastic rates to reactions
- Used in computational biology (BioAmbients, Beta-binders)

**Relation to Petri nets**:
- Process calculi and Petri nets are **equivalent in expressiveness** (both Turing-complete)
- Petri nets are **graphical** (visual topology), process calculi are **textual** (algebraic)
- Choice: Petri nets preferred in systems biology for **visual reasoning**

### 2.7.3 Chemical Reaction Network Theory

**Feinberg (1987)**: Deficiency theory
- Analyzes steady states of reaction networks
- **Deficiency zero theorem**: Networks with deficiency δ=0 have unique positive steady state

**Relationship to Petri nets**:
- Reaction networks are **continuous Petri nets** with mass action kinetics
- Stoichiometric matrix S corresponds to PN incidence matrix

**Limitation**:
- Mass action only (no Michaelis-Menten, Hill)
- No gene regulation (reactions among metabolites only)

### 2.7.4 Stochastic Simulation

**Gillespie (1977)**: Stochastic Simulation Algorithm (SSA)
- **Exact algorithm** for simulating chemical master equation (CME)
- Two random numbers per step:
  1. When does next reaction occur? (τ ~ Exponential)
  2. Which reaction fires? (Weighted choice by propensity)

**τ-leaping** (Gillespie, 2001):
- Approximate method: Fire multiple reactions per step
- Faster but loses exactness

**Hybrid methods** (Haseltine & Rawlings, 2002):
- Fast reactions: Continuous (ODE)
- Slow reactions: Stochastic (Gillespie)
- **Challenge**: Partitioning (which reactions are fast?)

**This thesis contribution**: Hybrid scheduler coordinates ODE + Gillespie + Timed + Burst engines without manual partitioning (user specifies transition type explicitly).

---

## 2.8 Gap Summary

**Existing work provides**:
- ✅ Petri net theory (classical, timed, stochastic, hybrid)
- ✅ Biological applications (metabolic pathways, signaling networks)
- ✅ Tools (Snoopy, COPASI, CellDesigner)
- ✅ Databases (KEGG, BRENDA, SBML)
- ✅ Simulation algorithms (ODE, Gillespie, hybrid)

**What is missing** (this thesis addresses):
1. **Weak independence theory**: Formal framework for parallel execution with shared catalysts/outputs
2. **Heterogeneous transition coexistence**: Continuous + stochastic + timed + burst in single model with unified semantics
3. **Arc-level regulatory semantics**: Hill equations, threshold formulas on arcs (not external code)
4. **Biochemical formula tracking**: Elemental composition, atomic conservation verification
5. **Integrated metabolic-genetic formalism**: Single framework spanning biochemistry and gene regulation
6. **Tool integration**: Automated KEGG (formulas) + BRENDA (parameters) enrichment

**Positioning**: This thesis is the **first** to provide all six capabilities in a unified Petri net formalism.

---

## 2.9 Summary

**This chapter surveyed foundational concepts and related work**:

**Section 2.1**: Classical Petri nets (5-tuple, enabling, firing, properties)
**Section 2.2**: Extensions (colored, timed, stochastic, hybrid)
**Section 2.3**: Biological Petri nets (Reddy 1993 → present, Snoopy tool)
**Section 2.4**: Multi-scale modeling (GSMM, GRN, E-Cell, Virtual Cell)
**Section 2.5**: Standards and databases (SBML, KEGG, BRENDA)
**Section 2.6**: Tools comparison (Snoopy, COPASI, CellDesigner, Charlie)
**Section 2.7**: Theoretical foundations (concurrency, process calculi, Gillespie)
**Section 2.8**: Gap analysis (what is missing)

**Key findings**:
- Petri nets are **well-suited** for biological modeling (visual, compositional, analyzable)
- Existing Bio-PNs model **metabolism or regulation, not both** in integrated way
- **No formalism** provides weak independence, arc-level regulation, and formula tracking together
- **Tools** (Snoopy, COPASI) are powerful but lack these features

**Next chapter** (Chapter 3) presents the **integration challenge** in depth, deriving formal requirements from the lac operon system.

**Transition**: Background established → Now define the problem precisely.
