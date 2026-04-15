# Signal Hierarchical Petri Net (SHYPN) 13-Tuple Formalism - Reference Standard

**Version:** 1.0  
**Date:** January 12, 2026  
**Status:** Normalized reference for all manuscripts

---

## Complete 13-Tuple Definition

```
SHYPN = ⟨P, T, Pre, Post, m₀, k, S, Φ, Σ, Reg, Ψ, E, A⟩
```

---

## Component Definitions

### Core Petri Net Components (1-6)

1. **P** - Places  
   - **Type:** Finite set  
   - **Definition:** $P = \{p_1, \ldots, p_n\}$  
   - **Biological Meaning:** Molecular species, compartments, regulatory states  
   - **Examples:** ATP, Glucose-6-P, Cytoplasm, σ-factor states

2. **T** - Transitions  
   - **Type:** Finite set  
   - **Definition:** $T = \{t_1, \ldots, t_m\}$  
   - **Biological Meaning:** Biochemical reactions, regulatory events  
   - **Examples:** Phosphorylation, transcription, compartment transport

3. **Pre** - Pre-incidence matrix  
   - **Type:** Matrix $|P| \times |T|$  
   - **Definition:** $\text{Pre}: P \times T \to \mathbb{R}^+ \cup \{0\}$  
   - **Biological Meaning:** Stoichiometric coefficients of consumed substrates  
   - **Examples:** $\text{Pre}(\text{ATP}, t_{\text{hexokinase}}) = 1$

4. **Post** - Post-incidence matrix  
   - **Type:** Matrix $|T| \times |P|$  
   - **Definition:** $\text{Post}: T \times P \to \mathbb{R}^+ \cup \{0\}$  
   - **Biological Meaning:** Stoichiometric coefficients of produced products  
   - **Examples:** $\text{Post}(t_{\text{hexokinase}}, \text{ADP}) = 1$

5. **m₀** - Initial marking  
   - **Type:** Function  
   - **Definition:** $m_0: P \to \mathbb{R}^+ \cup \{0\}$  
   - **Biological Meaning:** Initial concentrations (nM, μM, mM) or copy numbers  
   - **Examples:** $m_0(\text{ATP}) = 5000~\text{μM}$, $m_0(\text{mRNA}) = 10~\text{copies}$

6. **k** - Rate constants  
   - **Type:** Function  
   - **Definition:** $k: T \to \mathbb{R}^+$  
   - **Biological Meaning:** Catalytic rate constants, transcription rates  
   - **Units:** $\text{s}^{-1}$ (first-order), $\text{M}^{-1}\text{s}^{-1}$ (second-order)  
   - **Examples:** $k(t_{\text{hexokinase}}) = 0.05~\text{s}^{-1}$

---

### SHYPN Extensions (7-13)

7. **S** - Transition types  
   - **Type:** Function  
   - **Definition:** $S: T \to \{\text{stochastic, continuous, timed, immediate}\}$  
   - **Biological Meaning:** Simulation semantics for different biological processes  
   - **Examples:**  
     - $S(t_{\text{transcription}}) = \text{stochastic}$ (low-copy gene expression)  
     - $S(t_{\text{metabolism}}) = \text{continuous}$ (high-concentration metabolic flux)  
     - $S(t_{\text{commitment}}) = \text{timed}$ (delayed regulatory decision)

8. **Φ** - Rate functions  
   - **Type:** Function  
   - **Definition:** $\Phi: T \to \text{RateExpr}$  
   - **Biological Meaning:** Kinetic laws (mass action, Michaelis-Menten, Hill, custom)  
   - **Examples:**  
     - $\Phi(t) = k \cdot [S]$ (mass action)  
     - $\Phi(t) = \frac{V_{\max} \cdot [S]}{K_m + [S]}$ (Michaelis-Menten)  
     - $\Phi(t) = k \cdot \frac{[A]^n}{K^n + [A]^n}$ (Hill cooperativity)

9. **Σ** - Regulatory places  
   - **Type:** Function  
   - **Definition:** $\Sigma: T \to 2^P$  
   - **Biological Meaning:** Places appearing in rate formulas via test/inhibitor arcs (non-consumptive)  
   - **Examples:**  
     - $\Sigma(t_{\text{hexokinase}}) = \{\text{Enzyme}\}$ (catalyst)  
     - $\Sigma(t_{\text{PFK}}) = \{\text{ATP}_{\text{high}}\}$ (allosteric inhibitor)

10. **Reg** - Regulatory modulation functions  
    - **Type:** Function  
    - **Definition:** $\text{Reg}: T \times P \to \text{RegExpr}$  
    - **Biological Meaning:** How regulatory places modulate rates (activation, inhibition)  
    - **Examples:**  
      - $\text{Reg}(t, p_{\text{catalyst}}) = [p_{\text{catalyst}}]$ (linear activation)  
      - $\text{Reg}(t, p_{\text{inhibitor}}) = \frac{K_i}{K_i + [p_{\text{inhibitor}}]}$ (competitive inhibition)  
      - $\text{Reg}(t, p_{\text{allosteric}}) = \frac{K_a^n}{K_a^n + [p_{\text{allosteric}}]^n}$ (Hill inhibition)

11. **Ψ** - Signal places  
    - **Type:** Subset of places  
    - **Definition:** $\Psi \subseteq P$  
    - **Biological Meaning:** Places representing hierarchical layer information (environmental/regulatory signals)  
    - **Key Innovation:** Enable **information flux** (non-consumptive sensing) vs. **mass flux** (consumptive)  
    - **Examples:**  
      - $\Psi = \{\text{ATP}, \text{GTP}\}$ (energy signals, Layer 0)  
      - $\Psi = \{\text{AHL}_{\text{external}}\}$ (quorum sensing signal, Layer 1)  
      - $\Psi = \{\text{σ-factor}\}$ (regulatory master switch, Layer 2)

12. **E** - Signal type classification  
    - **Type:** Function  
    - **Definition:** $E: \Psi \to \{\text{ENERGY, SPATIAL, QUORUM, REGULATORY}\}$  
    - **Biological Meaning:** Semantic category of hierarchical signals  
    - **Signal Types:**  
      - **ENERGY:** ATP, GTP, NAD(P)H (Layer 0, environmental constraints)  
      - **SPATIAL:** Membrane area, compartment capacity, diffusion barriers  
      - **QUORUM:** Autoinducers, population density signals (cell-cell communication)  
      - **REGULATORY:** Transcription factors, σ-factors (decision layer coordinators)

13. **A** - Arc type classification  
    - **Type:** Function  
    - **Definition:** $A: (P \times T) \cup (T \times P) \to \{\text{normal, test, signal\_flow, inhibitor}\}$  
    - **Biological Meaning:** Semantics of place-transition connections  
    - **Arc Types:**  
      - **normal:** Stoichiometric consumption/production (mass flux)  
      - **test:** Non-consumptive read (e.g., catalyst, $A(p_{\text{enzyme}}, t) = \text{test}$)  
      - **signal\_flow:** Consuming read from signal place (information → mass coupling)  
      - **inhibitor:** Non-consumptive repression (threshold-based disabling)

---

## Information Flux vs. Mass Flux

### Classical Petri Nets (5-tuple)
```
Classical PN = ⟨P, T, F, W, M₀⟩
```
- **Limitation:** Only mass transfer (token consumption/production)
- **All arcs:** Normal arcs (consume input tokens, produce output tokens)
- **Independence:** Two transitions independent ⟺ share no places

### Signal Hierarchical Petri Nets (13-tuple)
```
SHYPN = ⟨P, T, Pre, Post, m₀, k, S, Φ, Σ, Reg, Ψ, E, A⟩
```
- **Innovation:** Information flux via signal places ($\Psi$) and specialized arcs ($A$)
- **Signal places ($\Psi$):** Can be sensed without depletion (test arcs, signal flow arcs)
- **Hierarchical control:** Higher layers (regulatory) gate lower layers (metabolic) via energy signals (L0)

### Place Partition
```
P = P_m ∪ Ψ  (disjoint union)
```
- **Material places ($P_m$):** Biochemical compounds with mass conservation
  - Connected via **normal arcs** ($A(p,t) = \text{normal}$)
  - Tokens consumed/produced according to stoichiometry
  - Example: Glucose, ATP (when treated as metabolite)

- **Signal places ($\Psi$):** Environmental/regulatory information
  - Connected via **test arcs** ($A(p,t) = \text{test}$) or **signal flow arcs** ($A(p,t) = \text{signal\_flow}$)
  - Enable non-consumptive sensing or hierarchical gating
  - Example: ATP (when treated as L0 energy signal), AHL (quorum sensing)

---

## Hierarchical Layer Architecture

### Layer 0 (L0): Environmental Signals
- **Signal Type:** ENERGY
- **Examples:** ATP pools, nutrient availability, oxygen tension
- **Role:** Physical/thermodynamic constraints on system
- **Dynamics:** Typically continuous (high-abundance metabolites)
- **Function:** Gate activation of upper layers when resources insufficient

### Layer 1 (L1): Metabolic Coordination
- **Signal Type:** SPATIAL, QUORUM
- **Examples:** Compartment capacity, autoinducer concentration, metabolic intermediates
- **Role:** Coordinate pathway activation across cells or compartments
- **Dynamics:** Hybrid (continuous flux + stochastic sensing)
- **Function:** Integrate environmental signals (L0) with regulatory logic (L2)

### Layer 2 (L2): Regulatory Decisions
- **Signal Type:** REGULATORY
- **Examples:** Transcription factors, σ-factors, master regulators
- **Role:** Binary or multi-stable decision-making
- **Dynamics:** Stochastic (low-copy number regulators)
- **Function:** Commit cell to specific pathway/phenotype based on L0-L1 inputs

---

## Example: Bacillus subtilis Sporulation

### Signal Place Assignments
```
Ψ = {ATP, GTP}
E(ATP) = ENERGY
E(GTP) = ENERGY
Σ(ATP) = L0
Σ(GTP) = L0
```

### Hierarchical Preemption Mechanism
1. **L0 Constraint:** ATP depletion (300 μM → 18 μM, 94% drop) creates energy crisis
2. **L0 Signal Flow:** Inhibitor arcs disable energy-intensive vegetative transitions  
   - $A(\text{ATP}, t_{\text{growth}}) = \text{inhibitor}$ with threshold $\theta = 300~\mu\text{M}$
3. **L1 Buffer:** GTP accumulation (300 μM → 1750 μM, 483% increase) maintains regulatory capacity
4. **L2 Decision:** Sporulation commitment enabled despite ATP crisis

### 16-Fold Efficiency Gain
- **Mechanism:** Hierarchical layer collapse routes resources to commitment pathway
- **Without hierarchy:** Futile metabolic cycles deplete ATP faster (T_commitment = 900 s)
- **With hierarchy:** Preemption stops vegetative processes (T_commitment = 56 s)
- **Thermodynamic validation:** 98.8% efficiency approaching theoretical optimum

---

## Usage Guidelines for Manuscripts

### When to Use Full 13-Tuple
1. **Foundation papers** establishing SHYPN formalism
2. **Methods sections** requiring complete mathematical specification
3. **Cross-referencing** to unify weak independence + signal hierarchy theories

### When to Use Simplified Notation
1. **Application papers** demonstrating SHYPN on specific biological systems
2. **After establishing** full formalism in introduction/methods
3. **Common simplifications:**
   - Omit $\text{Reg}$ if regulatory modulation implicit in $\Phi$
   - Combine $\text{Pre}$ and $\text{Post}$ into stoichiometry matrix $N = \text{Post} - \text{Pre}$
   - Use hybrid notation: $(P, T_s, T_c, \ldots)$ instead of $(P, T, \ldots)$ with $S: T \to \{\text{stochastic, continuous}\}$

### Citation Template
```latex
Signal Hierarchical Petri Nets (SHYPN) employ the 13-tuple formalism 
\citep{simao2025unified}:
\begin{equation}
\text{SHYPN} = \langle P, T, \text{Pre}, \text{Post}, m_0, k, S, \Phi, 
               \Sigma, \text{Reg}, \Psi, E, A \rangle
\end{equation}
where signal places $\Psi \subseteq P$ enable information flux—non-consumptive 
sensing of environmental conditions (e.g., ATP as Layer 0 ENERGY signal)—
distinguishing SHYPN from classical Petri nets that capture only mass transfer.
```

---

## Validation in Published Work

### Paper 1: Weak Independence (Foundation)
- **Focus:** Distinguishing competitive coupling from convergent coupling
- **Formalism:** 10-tuple Bio-PN (precursor to SHYPN)
- **Key Innovation:** $\Delta: T \times T \to \{\text{independent, competitive, convergent, regulatory}\}$

### Paper 2: Signal Hierarchy (Foundation)
- **Focus:** Hierarchical information flow via signal place partitioning
- **Formalism:** Full 13-tuple SHYPN
- **Key Innovation:** $\Psi, E, A$ enabling information flux vs. mass flux

### Paper 3: MAPK Cascade (Application)
- **Title:** "Signal Hierarchical Petri Nets Capture Emergent Nonlinear Dynamics in MAPK Cascades"
- **Status:** Submitted arXiv (January 12, 2026)
- **Formalism Used:** Full 13-tuple in Methods, simplified in Results
- **Demonstrates:** Environmental sensing ($\Psi$), thermodynamic constraints ($\Delta G$), regulatory coupling ($\Sigma$)

### Paper 4: Thermodynamics (Application)
- **Title:** "Signal Hierarchical Petri Nets Capture Energy-Driven Pathway Orchestration in Bacterial Sporulation"
- **Status:** Under revision (January 12, 2026)
- **Formalism Used:** Full 13-tuple + hybrid specialization
- **Demonstrates:** ATP/GTP as L0 ENERGY signals, hierarchical preemption, 16-fold efficiency gain

---

## Conversion Between Formalisms

### Classical PN → SHYPN
```
Given: Classical PN = ⟨P, T, F, W, M₀⟩

Convert to:
  P (same)
  T (same)
  Pre(p,t) = W(p,t) if (p,t) ∈ F, else 0
  Post(t,p) = W(t,p) if (t,p) ∈ F, else 0
  m₀ = M₀
  k: T → ℝ⁺ (user-defined rate constants)
  S: T → {stochastic} (all stochastic by default)
  Φ: T → RateExpr (mass action: k·∏[p] for p ∈ •t)
  Σ: T → ∅ (no regulatory arcs)
  Reg: undefined (no regulation)
  Ψ = ∅ (no signal places)
  E: undefined (no signals)
  A: all normal arcs
```

### Hybrid PN → SHYPN
```
Given: Hybrid PN = ⟨P, T_s, T_c, F, W, M₀, h, v⟩

Convert to:
  T = T_s ∪ T_c
  S(t) = stochastic if t ∈ T_s, continuous if t ∈ T_c
  Φ(t) = h(t) if t ∈ T_s, v(t) if t ∈ T_c
  (other components follow Classical PN → SHYPN)
```

---

## Implementation Notes

### Software Support
- **Tool:** SHYPN v1.0 (Python 3.x)
- **File Format:** `.shy` (JSON with SHYPN schema)
- **Simulation:** Hybrid tau-leaping + continuous ODE integration
- **Repository:** https://github.com/simao-eugenio/shypn

### Signal Place Detection (Automated)
```python
from shypn.analysis.quorum_sensing import QuorumSensingDetector

detector = QuorumSensingDetector(model)
signal_places = detector.detect_signal_places()
# Returns: {place_name: signal_type} dictionary
```

### Weak Independence Analysis
```python
from shypn.diagnostic.locality_detector import LocalityDetector

detector = LocalityDetector(model)
dependencies = detector.classify_dependencies()
# Returns: {(t1, t2): dependency_type} where 
# dependency_type ∈ {independent, competitive, convergent, regulatory}
```

---

## References

1. **Weak Independence:** Simão Eugénio (2024). "Weak Independence in Biological Petri Nets: Formalizing Non-Conflicting Coupling." [Under review]

2. **Signal Hierarchy:** Simão Eugénio (2025). "Unifying Weak Independence and Signal Hierarchy Theory: Extended Bio-PN Formalism." arXiv preprint arXiv:[ID].

3. **MAPK Application:** Simão Eugénio (2026). "Signal Hierarchical Petri Nets Capture Emergent Nonlinear Dynamics in MAPK Cascades." arXiv preprint arXiv:[ID]. [Submitted January 12, 2026]

4. **Thermodynamics Application:** Simão Eugénio (2026). "Signal Hierarchical Petri Nets Capture Energy-Driven Pathway Orchestration in Bacterial Sporulation: 16-Fold Efficiency Through Hierarchical Preemption." [Under revision]

---

## Version History

- **v1.0 (January 12, 2026):** Initial normalized reference standard
  - Confirmed 13-tuple component count (Pre and Post are separate components)
  - Established consistent terminology across manuscripts
  - Defined signal types (ENERGY, SPATIAL, QUORUM, REGULATORY)
  - Documented hierarchical layer architecture (L0, L1, L2)
