# Signal Flow Arc Architecture: Vertical Information Propagation

## Verified Architectural Distinction (Chapter 3 Evidence)

### Core Principle
Signal flow arcs ($F_s$) **broadcast consumption information** vertically across hierarchical layers. They do **NOT** replace or superpose the functionality of normal arcs ($F$) for mass transfer.

---

## Two-Level Architecture

### Layer 0: Metabolic Mass Transfer (Horizontal)
**Normal arcs ($F$)** handle stoichiometric mass transfer:
- Substrate consumption and product formation
- Governed by conservation laws (e.g., ATP + ADP = constant)
- Remains at metabolic level
- Example: Glycolysis produces ATP via normal arc $(t_{\text{glyc}}, \text{ATP}) \in F$

**Evidence (Chapter 3, line 21):**
> "$F \subseteq (P \times T) \cup (T \times P)$ represents normal arcs for **mass transfer**"

---

### Higher Layers: Information Propagation (Vertical)
**Signal flow arcs ($F_s$)** broadcast concentration information hierarchically:
- Reads consumption/concentration at layer 0
- Propagates information upward to layers 1, 2, 3, ...
- Enables hierarchical control and preemption
- Example: KinA consumes ATP signal via signal flow arc $(\text{ATP}, t_{\text{KinA}}) \in F_s$

**Evidence (Chapter 3, line 25):**
> "$F_s \subseteq (\Psi \times T) \cup (T \times \Psi)$ represents signal flow arcs for **information transfer**"

**Evidence (Chapter 3, line 280):**
> "signal flow arcs subtract input signal weights and add output signal weights for **information propagation**"

---

## Signal Places: Dual Connectivity

**Critical insight (Chapter 3, lines 59-62):**
```
ATP is designated as signal place (ATP ∈ Ψ):

• Glycolysis produces ATP: (t_glyc, ATP) ∈ F with W = 2
  → Normal arc: metabolic production (layer 0 mass transfer)

• KinA consumes ATP signal: (ATP, t_KinA) ∈ F_s with W_s = 5
  → Signal flow arc: hierarchical consumption (information propagation)
```

**Architecture:**
A signal place $p_s \in \Psi$ can connect to **BOTH**:
1. **Normal arcs ($F$)**: For metabolic stoichiometry at layer 0
2. **Signal flow arcs ($F_s$)**: For hierarchical information broadcast

**Evidence (Chapter 3, line 53):**
> "$\Psi \subseteq P$ permits places to function simultaneously as both **metabolic species through $F$** and as **signal channels through $F_s$**, enabling dual representation."

---

## Functional Distinction

### Normal Arcs (F): Horizontal Mass Flow
- **Purpose**: Stoichiometric mass transfer
- **Scope**: Within layer 0 (metabolic level)
- **Semantics**: $M'(p) = M(p) - W((p,t)) + W((t,p))$
- **Conservation**: Mass-action kinetics (ATP produced = ATP consumed)
- **Example**: Glycolysis reaction network

### Signal Flow Arcs (F_s): Vertical Information Broadcast
- **Purpose**: Concentration information propagation
- **Scope**: Across hierarchical layers (0 → 1 → 2 → 3)
- **Semantics**: $M'(p_s) = M(p_s) - W_s((p_s,t)) + W_s((t,p_s))$ 
- **Information**: "Layer 0 ATP = 5.0 mM" broadcasts to Layer 1, 2, 3
- **Preemption**: Lower-layer depletion disables higher-layer transitions
- **Example**: ATP depletion at Layer 0 disables phosphorelay (Layer 1), Spo0A~P (Layer 2), sigma factors (Layer 3)

**Evidence (Chapter 3, line 256):**
> "if Layer 0 ATP drops below $\theta_{\min}(0)$, then **all** Layer 3 sigma factor transitions become disabled, regardless of their local Spo0A~P concentrations."

---

## Why Signal Flow Arcs ≠ Normal Arcs

### Misconception to Avoid
❌ Signal flow arcs replace normal arcs for signal places  
❌ Signal flow arcs superpose functionality of normal arcs

### Correct Understanding
✓ Signal flow arcs **ADD broadcasting capability** on top of consumption  
✓ Normal arcs handle **metabolic stoichiometry** (layer 0)  
✓ Signal flow arcs handle **hierarchical information** (vertical propagation)  
✓ Both arc types can connect to the same signal place  

**Evidence (Chapter 3, line 62):**
> "The firing rule handles **both arc types**: metabolic transitions modify $M(\text{ATP})$ via $F$, regulatory transitions consume via $F_s$."

---

## Information Propagation Mechanism

### Step 1: Layer 0 Consumption (via F or F_s)
- Glycolysis produces ATP: $(t_{\text{glyc}}, \text{ATP}) \in F$
- Phosphorelay consumes ATP: $(\text{ATP}, t_{\text{phosphorelay}}) \in F_s$
- **Result**: $M(\text{ATP})$ changes at layer 0

### Step 2: Concentration Reading
- Signal place marking $M(p_s) \in \mathbb{R}_{\geq 0}$ represents **signal concentration** (Chapter 3, line 49)
- This concentration is available to **all layers** for regulation

### Step 3: Vertical Broadcast
- Layer 1 transitions check: $M(\text{ATP}) \geq \theta(t_1)$ ?
- Layer 2 transitions check: $M(\text{ATP}) \geq \theta(t_2)$ ?
- Layer 3 transitions check: $M(\text{ATP}) \geq \theta(t_3)$ ?
- **Information propagates**: Layer 0 concentration controls layers 1-3

### Step 4: Hierarchical Preemption
- If $M(\text{ATP}) < \theta_{\min}(0)$ → ALL higher layers disabled
- Lower layers preempt higher layers (Chapter 3, line 156)
- **Structural enforcement**: Not emergent from parameters

**Evidence (Chapter 3, line 97):**
> "**stoichiometric information transformation** across hierarchical layers, distinct from mass conservation in normal arcs."

---

## Architectural Summary

```
LAYER 3: Gene Expression (σF, σE, σG)
         ↑ Information: [ATP], [Spo0A~P]
         
LAYER 2: Transcriptional Regulation (Spo0A~P)
         ↑ Information: [ATP], [KinA~P]
         
LAYER 1: Signal Transduction (KinA)
         ↑ Information: [ATP]
         │
         │ Signal Flow Arcs (F_s):
         │ Vertical information propagation
         │
LAYER 0: Metabolism (Glycolysis)
         ← → Normal Arcs (F):
         Horizontal mass transfer
```

**Key distinction:**
- **Horizontal (F)**: ATP + Glucose → F6P + ADP (mass transfer)
- **Vertical (F_s)**: [ATP] @ Layer 0 → broadcasts to Layers 1, 2, 3 (information)

---

## Example 3 Alignment Verification

**Current Example 3 statement (line 229):**
> "This topology structure allows ATP concentration to influence the rate while tokens are consumed, enabling saturation-based regulatory modeling."

**Analysis:**
- ✓ Correct emphasis on **concentration information** for regulation
- ✓ Distinguishes token consumption from concentration sensing
- ⚠️ Doesn't explicitly clarify vertical vs horizontal architecture

**Potential clarification for Example 3:**
Signal flow arcs provide **concentration information** that propagates hierarchically. While Example 3 demonstrates single-layer ATP regulation, the formalism enables multi-layer information broadcast: metabolic consumption at layer 0 (via normal arcs $F$) can be sensed by regulatory transitions at higher layers (via signal flow arcs $F_s$).

---

## Formal Summary

### Normal Arcs (F): Metabolic Mass Transfer
$$F \subseteq (P \times T) \cup (T \times P)$$
- **Domain**: Metabolic places (substrates, products, intermediates)
- **Function**: Stoichiometric token transfer
- **Scope**: Intra-layer (horizontal)
- **Example**: $(t_{\text{glycolysis}}, \text{ATP}) \in F$

### Signal Flow Arcs (F_s): Hierarchical Information Broadcast
$$F_s \subseteq (\Psi \times T) \cup (T \times \Psi)$$
- **Domain**: Signal places (energy carriers, regulators, sensors)
- **Function**: Concentration information propagation + consumptive behavior
- **Scope**: Inter-layer (vertical)
- **Example**: $(\text{ATP}, t_{\text{KinA}}) \in F_s$

### Coexistence Guarantee (Chapter 3, line 53)
> "$\Psi \subseteq P$ permits places to function simultaneously as both metabolic species through $F$ and as signal channels through $F_s$"

**Architectural independence:**
- Normal arcs handle **what** is transferred (mass)
- Signal flow arcs handle **how information propagates** (vertically)
- No functional conflict: complementary roles

---

## Biological Interpretation

**ATP as signal place:**
1. **Layer 0 (Mass Transfer)**: 
   - Glycolysis produces ATP via normal arc $(t_{\text{glyc}}, \text{ATP}) \in F$
   - ATP concentration changes stoichiometrically
   - Governed by mass action: ATP + ADP + AMP = constant

2. **Layers 1-3 (Information Broadcast)**:
   - KinA senses ATP via signal flow arc $(\text{ATP}, t_{\text{KinA}}) \in F_s$
   - Information: "Layer 0 ATP = 5.0 mM" propagates to Layer 1
   - Preemption: If ATP < threshold, Layer 1-3 transitions disabled
   - Irreversibility: Consumed signal capacity doesn't regenerate (Chapter 3, line 62)

**Biological significance:**
Energy availability (layer 0 metabolic state) **controls** developmental decisions (layers 1-3 regulatory cascades) through vertical information propagation. This architectural separation mirrors biological reality: metabolism provides resources (horizontal), signaling networks broadcast state information (vertical).

---

## Conclusion: Certified Statements

✓ **Signal flow arcs are consumptive** (Chapter 3, lines 62, 97, 280)  
✓ **Consumption reading done at layer 0 characterizes information** (Chapter 3, line 49: marking = concentration)  
✓ **Information propagates to higher layers** (Chapter 3, lines 156, 171, 256: preemption hierarchy)  
✓ **Mass transfer stays at layer 0** (Chapter 3, line 21: F = mass transfer)  
✓ **Information propagates vertically** (Chapter 3, line 25: F_s = information transfer)  
✓ **Signal flow arcs broadcast signals, NOT superpose normal arc functionality** (Chapter 3, line 62: "handles both arc types" - coexistence)

**Architectural principle:**
Signal flow arcs ($F_s$) extend the formalism to enable **vertical information propagation** across hierarchical layers, complementing—not replacing—normal arcs ($F$) that handle **horizontal mass transfer** at the metabolic level.
