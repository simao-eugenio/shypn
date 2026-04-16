# Innovation Analysis: CBD-AD Neuroprotection Model in SHYpn

## 1. Innovation Line

This project proposes the first computational Petri net model that captures
CBD's **polypharmacological intervention** across the multi-pathway landscape
of Alzheimer's Disease neurodegeneration. The innovation lies in three pillars:

### 1.1 Mirror-Image Convergence
AD drug discovery failed for 30 years on single-target (amyloid-only) approaches
and is now shifting to multi-target. CBD enters with native multi-target activity
across 65+ receptors. This model is the first to formalize this convergence:
CBD as a natural multi-target compound hitting the exact pathways AD research
has identified as essential.

### 1.2 Hybrid Stochastic-Continuous Dynamics
The model necessarily operates in two regimes:
- **Low-copy stochastic**: Receptor-level events (GPR3 binding, PPARγ activation,
  5-HT1A engagement) involve few molecules per cell
- **High-copy continuous**: Downstream cascades (ROS production, cytokine release,
  Aβ accumulation) are bulk phenomena

SHYpn's **adaptive hybrid behavior** (automatic ODE↔SSA switching based on
molecule count) is uniquely suited to capture this biological reality.

### 1.3 Information-Theoretic Control
CBD doesn't just participate in mass-transfer reactions. It acts as an
**information channel** (signal place) that modulates transition rates across
multiple pathways simultaneously — a natural fit for SHYpn's signal hierarchy
and signal flow arc formalism.


## 2. Biological Phenomena Detectable by SHYpn

### 2.1 BISTABILITY: Microglial Polarization Switch

**Biology**: Microglia exist in two stable states:
- M1 (pro-inflammatory): activated by Aβ oligomers, produce TNFα, IL-1β, ROS
- M2 (anti-inflammatory/neuroprotective): produce BDNF, IL-10, phagocytose debris

This is a classic bistable toggle: once committed to M1, positive feedback
(TNFα → NFκB → more TNFα) locks the cell in the inflammatory state.
CBD's PPARγ agonism can potentially tip the balance toward M2.

**SHYpn detection**:
- **P-invariants** reveal conservation: M1 + M2 = total microglia (conserved quantity)
- **Siphon analysis** detects if M2 can be permanently emptied (irreversible commitment)
- **Trap analysis** reveals if M1 accumulates tokens irreversibly
- **Simulation replicates** with stochastic noise show bimodal distribution of
  final states → bistability signature

**Model structure**: Mutual inhibition between M1 and M2 pathways with
Hill-coefficient nonlinearity, analogous to the Lambda phage CI/Cro switch
already validated in SHYpn (Example 22).


### 2.2 BISTABILITY: NFκB Activation Threshold

**Biology**: NFκB pathway exhibits switch-like behavior:
- Below threshold Aβ: IκB sequesters p65, NFκB stays cytoplasmic (OFF)
- Above threshold Aβ: IKK phosphorylates IκB → degradation → p65 nuclear entry (ON)
- Once ON, transcription of IκBα creates negative feedback → oscillations

CBD (via PPARγ) targets p65 ubiquitination — a direct intervention on this switch.

**SHYpn detection**:
- **Inhibitor arcs** (from IκB to NFκB activation transition) model threshold
- **Reachability analysis** identifies the critical marking where the switch flips
- **Stochastic simulation** reveals the Aβ concentration threshold for switching


### 2.3 CHAINS OF PREEMPTION: Signal Hierarchy

**Biology**: CBD operates via a natural signal hierarchy:
- **Layer 3 (highest)**: CBD concentration (external input, pharmacokinetic)
- **Layer 2**: Receptor activation states (GPR3, PPARγ, 5-HT1A, A2A)
- **Layer 1**: Intracellular signaling (NFκB, Nrf2, γ-secretase)
- **Layer 0**: Effector outputs (Aβ production, cytokines, ROS, BDNF)

Each layer exerts **preemptive control** over the layer below. Higher-priority
signals (CBD present → receptor bound) override lower-level behaviors
(Aβ-driven inflammation). This is the "hierarchical preemption mechanism"
formalized in SHYpn's signal hierarchy theory (Simão, 2025).

**SHYpn detection**:
- **Signal places** (is_signal_place=true) for CBD, receptor states
- **Signal flow arcs** connect signal places to transitions in lower layers
- **SignalHierarchyAnalyzer** detects layers, validates acyclicity,
  quantifies preemption relationships
- **Preemption count** measures the degree of CBD's control over pathology


### 2.4 PREEMPTION: GPR3/γ-Secretase Competition

**Biology**: γ-secretase processes APP to produce Aβ. GPR3 is a constitutive
activator of γ-secretase. CBD as GPR3 inverse agonist competes for control:
- Without CBD: GPR3 active → γ-secretase high → Aβ production high
- With CBD: GPR3 inhibited → γ-secretase low → Aβ production low

This is a classical **preemption** where CBD's signal preempts the default
pathogenic pathway.

**SHYpn detection**:
- **Conflict resolution** between CBD-inhibition and GPR3-activation transitions
  competing for the γ-secretase enabling condition
- **Maximal concurrent set computation** determines which transitions fire
  when both CBD and Aβ precursors are present


### 2.5 STABILITY: Nrf2/Keap1 Redox Homeostasis

**Biology**: Under basal conditions, Keap1 ubiquitinates Nrf2 for degradation
(steady state: low Nrf2). Under oxidative stress, ROS modify Keap1 cysteines →
Nrf2 escapes → enters nucleus → transcribes HO-1, SOD, catalase.
CBD activates Nrf2 independently, adding a parallel input.

The question: does CBD + ROS create a **new stable steady state** with
constitutively elevated antioxidant defense, or does the system oscillate?

**SHYpn detection**:
- **Flux Balance Analysis** determines if elevated Nrf2 + antioxidant
  production is a feasible steady state
- **T-invariants** identify cyclic behaviors (Nrf2 → antioxidants → ↓ROS →
  Keap1 recovery → ↓Nrf2 → ... cycle)
- **P-invariants** reveal conservation laws (total Nrf2 = free + Keap1-bound
  + nuclear, if modeled explicitly)
- **Steady-state detection** in simulation confirms whether the system settles


### 2.6 SIPHON: Neuronal Death as Irreversible Token Drain

**Biology**: Once neurons die (apoptosis from sustained Aβ + ROS + inflammation),
they cannot regenerate. This is a one-way process.

**SHYpn detection**:
- **Siphon analysis**: {Neuron_health} forms a siphon — once empty, it stays
  empty forever. No transition can restore it.
- **Deadlock detection**: If Neuron_health reaches zero, any transitions
  depending on it (BDNF signaling, synaptic activity) become permanently dead
- This reveals the **point of no return** in AD progression — the critical
  neuron count below which neuroprotection is futile


### 2.7 TRAP: Aβ Plaque Accumulation

**Biology**: Aβ oligomers aggregate into fibrils and plaques. Once aggregated,
plaques are extremely stable and resistant to clearance. Tokens (Aβ mass)
flow in but rarely flow out.

**SHYpn detection**:
- **Trap analysis**: {Aβ_oligomer, Aβ_plaque} would form a trap — once
  marked, tokens accumulate indefinitely
- **Boundedness analysis**: Is the plaque place unbounded? If yes, the model
  predicts unlimited accumulation (pathological)
- CBD's intervention upstream (reducing Aβ production) is the only way to
  prevent the trap from growing


### 2.8 LIVENESS: Therapeutic Window Detection

**Biology**: The key clinical question — at what point can CBD still rescue
the system? If neuroinflammation is self-sustaining (live cycle) and
neuroprotection transitions become dead, CBD intervention is too late.

**SHYpn detection**:
- **Liveness analysis** classifies transitions into L0-L4 levels
  - L0 (dead) transitions indicate permanently lost capabilities
  - L3+ (live) transitions indicate sustained processes
- If anti-inflammatory transitions (PPARγ→NFκB inhibition) become L0 while
  pro-inflammatory transitions (NFκB→cytokines) are L3, the system has
  crossed the therapeutic threshold
- **Response time analysis** estimates how quickly CBD effects propagate
  through the network


### 2.9 ADAPTIVE HYBRID: Stochastic Receptor Binding → Deterministic Cascade

**Biology**: The "two-regime" nature of this system:
- **Stochastic regime**: CBD binds to a few receptor molecules per cell
  (low copy number, discrete events, significant noise)
- **Deterministic regime**: Once signal transduction activates NFκB or Nrf2,
  thousands of downstream molecules participate (continuous ODE valid)

**SHYpn detection**:
- **Adaptive transitions** automatically switch between SSA (stochastic) and
  ODE (continuous) based on molecule count thresholds
- This captures reality: stochastic noise at the receptor level can cause
  **cell-to-cell variability** in CBD response — some cells respond while
  others don't — which is a known pharmacological phenomenon


## 3. Summary: What Makes This Model Unique

| SHYpn Capability | Biological Phenomenon | Innovation |
|---|---|---|
| P-invariants | Microglial M1+M2 conservation | Conservation law for neuroinflammation |
| Siphons | Neuronal death as irreversible drain | Formalizes "point of no return" in AD |
| Traps | Aβ plaque accumulation | Predicts irreversible pathology |
| Bistability (simulation) | M1/M2 microglial switch | CBD as pharmacological switch-flipper |
| Signal hierarchy | CBD → receptor → signaling layers | Preemption chains across 4 layers |
| Conflict resolution | GPR3 vs CBD competition for γ-secretase | Formal preemption at molecular level |
| Liveness analysis | Therapeutic window | Identifies when CBD can no longer rescue |
| Flux balance | Nrf2/antioxidant steady state | Tests if CBD creates new homeostasis |
| T-invariants | Redox cycling | Detects oscillatory antioxidant response |
| Adaptive hybrid | Receptor stochasticity → bulk cascade | Cell-to-cell variability in CBD response |
| Deadlock detection | System collapse post-neuronal death | Predicts cascade failure |

## 4. Thermodynamic Properties: New Discoveries

SHYpn integrates a full thermodynamics engine that goes beyond kinetics to
validate and constrain the model from first principles. This is where genuinely
**new discoveries** can emerge — predictions that no purely kinetic model can make.

### 4.1 Gibbs Free Energy Feasibility: Reaction Directionality

**Engine**: `GibbsCalculator` computes ΔG°' from compound formation energies,
applies pH corrections, and derives K_eq = exp(−ΔG°/RT).

**CBD-AD discoveries**:
- **Aβ aggregation thermodynamics**: Aβ₄₂ monomer → oligomer → fibril is
  thermodynamically downhill (ΔG < 0 at each step). The Gibbs calculator can
  quantify *how* downhill: if ΔG_aggregation ≈ −40 kJ/mol, the K_eq ≈ 10⁷,
  meaning disaggregation is effectively impossible without energy input.
  This formalizes why anti-amyloid antibodies are the only current approach —
  the thermodynamic landscape forbids spontaneous reversal.
- **CBD-PPARγ binding**: The ΔG of CBD-PPARγ complex formation determines
  whether CBD occupancy is thermodynamically competitive with endogenous PPARγ
  ligands (15-deoxy-PGJ₂). If ΔG_CBD < ΔG_endogenous, CBD can displace; if
  not, the model predicts dose-dependent limitation.
- **NFκB-IκB sequestration**: The equilibrium constant K_eq of the IκB-p65
  complex determines the threshold Aβ concentration needed to free p65.
  Gibbs calculation predicts this threshold quantitatively.

### 4.2 Equilibrium Validation: k_f/k_r vs K_eq Consistency

**Engine**: `EquilibriumValidator` checks that kinetic rate constants
(k_forward/k_reverse) match the thermodynamic K_eq within tolerance.

**CBD-AD discoveries**:
- **Detecting thermodynamically impossible rate assignments**: If a literature
  k_forward/k_reverse ratio for the Nrf2-Keap1 dissociation implies K_eq = 10⁶
  but the Gibbs-calculated K_eq = 10², the validator flags this as a
  **thermodynamic inconsistency** — the rate constants violate the second law.
  This catches a common error in systems biology models where kinetic
  parameters are fit to data without thermodynamic constraints.
- **Reversibility enforcement**: Every reaction in the model can be checked:
  is the assigned directionality consistent with ΔG? The validator can
  discover that a reaction modeled as irreversible is actually reversible
  (or vice versa), changing the model's qualitative behavior.

### 4.3 pH-Dependent Thermodynamics: Compartment-Specific Chemistry

**Engine**: `ThermodynamicCorrector` applies pH, temperature, and ionic
strength corrections. `ThermodynamicContext` supports per-compartment conditions
read from dynamic spatial places during simulation.

**CBD-AD discoveries**:
- **Lysosomal pH trap**: Aβ processing occurs partly in lysosomes (pH ~4.5)
  and partly in cytoplasm (pH ~7.2). The pH correction formula:
  ΔG'(pH) = ΔG°(pH_std) + n_H⁺ · RT · ln(10) · (pH_actual − pH_std)
  means that proton-consuming reactions that are unfavorable at pH 7 may
  become favorable at pH 4.5. This can reveal that **γ-secretase cleavage of
  APP is thermodynamically favored in endosomes** (pH 5-6) but not at the
  cell surface (pH 7.4) — a prediction about where Aβ production actually
  occurs, testable experimentally.
- **Neuroinflammatory acidification**: Activated microglia create local
  acidic microenvironments (~pH 6.0). The corrector can predict whether
  CBD's PPARγ-mediated anti-inflammatory action has altered efficacy in these
  acidic conditions (ΔG changes with pH shift).
- **Mitochondrial membrane potential**: Mitochondrial dysfunction in AD creates
  a different electrochemical context. Temperature/ionic strength corrections
  can model the bioenergetic collapse that accompanies neurodegeneration.

### 4.4 Compound Database & Cross-Reference: Automatic ΔG°_f Lookup

**Engine**: `MultiSourceProvider` chains `StaticDataProvider` → `CacheProvider`
→ `EquilibratorProvider` (eQuilibrator API). `CompoundResolver` maps KEGG/ChEBI
IDs from place metadata to thermodynamic data.

**CBD-AD discoveries**:
- **Automated thermodynamic annotation**: Since model places carry KEGG IDs
  (e.g., D10915 for CBD, C00002 for ATP), the compound resolver can
  automatically look up ΔG°_f values for every metabolite in the model.
  This transforms a purely kinetic model into a thermodynamically grounded one
  without manual data entry.
- **Energy budget of neuroprotection**: By summing ΔG across all transitions
  in the neuroprotective arm (Nrf2 → HO-1 → ↓ROS), the energy cost of
  sustained antioxidant defense can be computed. If this exceeds available
  cellular ATP, the model predicts that **neuroprotection fails not from
  lack of signal but from bioenergetic exhaustion** — a genuine novel hypothesis.

### 4.5 Simulation-Integrated Validation: Runtime Thermodynamic Checks

**Engine**: `ThermodynamicSimulationValidator` validates all reversible
reactions at simulation initialization and can flag violations during runtime.
`RateFunctionParser` extracts k_f/k_r from diverse rate function formats.

**CBD-AD discoveries**:
- **Dynamic feasibility checking**: As Aβ accumulates during simulation, local
  concentrations change. The actual ΔG = ΔG° + RT·ln(Q) becomes increasingly
  negative for aggregation (Q shifts as oligomers accumulate), confirming the
  thermodynamic trap. The validator tracks this in real time.
- **CBD dose-response thermodynamics**: At low CBD concentrations, Q for
  receptor binding is far from equilibrium (ΔG << 0, reaction proceeds).
  At high CBD, Q → K_eq and the reaction approaches equilibrium — additional
  CBD provides diminishing returns. This naturally models the **inverted
  U-shaped dose-response** reported clinically, but from thermodynamic first
  principles rather than empirical curve fitting.

### 4.6 Thermodynamics × Topology: Cross-Analysis Discoveries

The most innovative insights come from combining thermodynamics with
structural topology analysis:

| Combined Analysis | Discovery Potential |
|---|---|
| ΔG + Siphon (neuronal death) | Energy cost of crossing the "point of no return" — is there a ΔG barrier that delays neuronal commitment to apoptosis? |
| ΔG + Trap (Aβ plaque) | Quantify the thermodynamic depth of the aggregation trap — how much energy would be needed to reverse it? |
| ΔG + Bistability (M1/M2) | Is the M1→M2 switch endergonic or exergonic? If endergonic, CBD must supply energy (via ATP-coupled signaling) |
| K_eq + Flux Balance | Do the thermodynamic equilibria permit the steady-state flux distribution? Infeasible combinations reveal impossible homeostatic states |
| pH correction + Liveness | Does pH change in inflamed tissue render neuroprotective transitions thermodynamically dead (not just kinetically slow)? |
| T-invariants + ΔG cycle | For cyclic pathways, total ΔG around the cycle must be ≤ 0 (second law). T-invariants identify cycles; Gibbs checks feasibility |

### 4.7 Summary of Thermodynamic Discovery Potential

1. **Irreversibility quantification**: ΔG proves Aβ aggregation is a
   thermodynamic trap, not just a kinetic one — fundamentally different
   therapeutic implications
2. **Compartment-dependent drug action**: pH corrections predict CBD efficacy
   varies by subcellular location (lysosomal vs cytoplasmic vs extracellular)
3. **Bioenergetic limits on neuroprotection**: Energy budget analysis may
   reveal that sustained Nrf2 activation is unsustainable, explaining why
   antioxidant therapies show short-term but not long-term benefit
4. **Thermodynamic basis for inverted U dose-response**: Equilibrium
   approach at high CBD concentrations provides a physical explanation for the
   empirically observed phenomenon
5. **Second-law validation**: Every cycle in the model must satisfy ΔG ≤ 0;
   violations expose impossible parameter combinations that kinetics alone
   would not catch
6. **Automatic grounding**: KEGG/ChEBI-linked compounds get ΔG°_f from
   eQuilibrator, transforming a qualitative pathway model into a
   quantitatively constrained thermodynamic model


## 5. Conclusion

This is not merely a pathway diagram translated into Petri net notation.
SHYpn's formal analysis tools can answer questions that no other modeling
approach combines in one framework:

1. **Is microglial polarization bistable?** (P-invariants + stochastic simulation)
2. **Can CBD flip the switch?** (reachability + preemption analysis)
3. **When is it too late?** (siphons + liveness + deadlock detection)
4. **Does CBD create a new homeostasis?** (flux balance + T-invariants)
5. **Why do patients respond differently?** (adaptive hybrid stochasticity)

These are the fundamental open questions in CBD-AD drug discovery, and SHYpn
is uniquely equipped to formalize and explore them computationally.
