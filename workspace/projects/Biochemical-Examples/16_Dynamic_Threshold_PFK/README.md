# Example 16: Dynamic Threshold Inhibition - PFK with AMP-Modulated ATP Inhibition

## Biological Context

This example demonstrates **three-layer enzyme regulation** combining:
1. **Dynamic inhibitor arc threshold** - Context-dependent ON/OFF switch
2. **Hill equation in rate formula** - Continuous cooperative inhibition
3. **Substrate availability** - Michaelis-Menten kinetics

This models the **Pasteur effect**: high AMP (energy deficit) relieves ATP inhibition of phosphofructokinase (PFK), allowing glycolysis to continue even when ATP levels are elevated. This is a classic example of **metabolic feedback regulation** where the enzyme's sensitivity to one regulator (ATP) is modulated by another regulator (AMP).

### The Pasteur Effect

Louis Pasteur discovered in 1861 that yeast consume less glucose when oxygen is present. The molecular mechanism:
- **Low oxygen** → **Low ATP production** → **High AMP** (from ATP degradation)
- **High AMP** → **Relieves ATP inhibition** of PFK
- **PFK activated** → **Glycolysis continues** to compensate for energy deficit

This example models the molecular mechanism underlying this phenomenon.

---

## Biochemical Reaction

```
F6P + ATP → F1,6BP + ADP
```

**Enzyme**: Phosphofructokinase (EC 2.7.1.11)  
**KEGG Reaction**: R00756  
**Regulation**: Three-layer regulation system

---

## Model Components

### Places (6)

1. **P1 - F6P** (2.0 mM): Substrate - fructose 6-phosphate
2. **P2 - ATP** (4.0 mM): Substrate - provides phosphate group
3. **P3 - F1,6BP** (0.1 mM): Product - fructose 1,6-bisphosphate
4. **P4 - ADP** (1.0 mM): Product - adenosine diphosphate
5. **P5 - ATP_high** (5.0 mM): Allosteric inhibitor pool - cellular ATP
6. **P6 - AMP** (0.05 mM): Allosteric activator - energy deficit signal

### Transitions (1)

- **T1 - PFK**: Phosphofructokinase enzyme with three-layer regulation

### Arcs (6)

- **A1**: P1 (F6P) → T1 - Substrate consumption
- **A2**: P2 (ATP) → T1 - Substrate consumption
- **A3**: T1 → P3 (F1,6BP) - Product formation
- **A4**: T1 → P4 (ADP) - Product formation
- **A5**: P5 (ATP_high) ⊣ T1 - **Dynamic inhibitor arc** (threshold modulated by AMP)
  - **Weight**: 1 (token consumption, not used for inhibitor arcs)
  - **Threshold**: `"4.0 * (1.0 + AMP / 0.1)"` (dynamic expression)
  - **Behavior**: Threshold INCREASES with AMP (relief from inhibition)
- **A6**: P6 (AMP) ⊙ T1 - **Test arc** (classical Petri net sensor)
  - **Weight**: 0.01 (enablement threshold, not consumed)
  - **Purpose**: Makes AMP dependency explicit in topology
  - **Semantics**: T1 requires AMP ≥ 0.01 mM to fire (always satisfied)

---

## Three-Layer Regulation Architecture

### Layer 1: Dynamic Inhibitor Arc Threshold (Emergency Shutdown)

**Expression**: `threshold = 4.0 * (1.0 + AMP / 0.1)`

**Behavior**:

| AMP (mM) | Effective Threshold (mM) | ATP_high = 5.0 mM | Status | Biological State |
|----------|-------------------------|-------------------|---------|------------------|
| **0.00** | 4.0 | 5.0 ≥ 4.0 | ❌ **BLOCKED** | High energy, no demand |
| **0.03** | 5.2 | 5.0 < 5.2 | ✅ **ENABLED** | Rising energy demand |
| **0.05** | 6.0 | 5.0 < 6.0 | ✅ **ENABLED** | Moderate energy deficit |
| **0.10** | 8.0 | 5.0 < 8.0 | ✅ **ENABLED** | Severe energy deficit |
| **0.20** | 12.0 | 5.0 < 12.0 | ✅ **ENABLED** | Extreme deficit (starvation) |

**Key Insight**: At ATP = 5.0 mM (normally inhibitory), the enzyme:
- **Blocked** when AMP = 0.0 (no energy demand)
- **Active** when AMP ≥ 0.03 (energy demand present)

This is the **Pasteur effect** at the molecular level!

### Layer 2: Hill Equation in Rate Formula (Fine-Tuning)

**Expression**: `rate = (numerator) / (1.0 + (ATP_high / 2.5)**4)`

**Behavior** (when Layer 1 passes):

| ATP_high (mM) | Hill Denominator | Rate Factor | Interpretation |
|---------------|------------------|-------------|----------------|
| **0.0** | 1.0 | 100% | No inhibition |
| **1.0** | 1.026 | 97.5% | Minimal inhibition |
| **2.0** | 1.41 | 70.9% | Moderate inhibition |
| **2.5** | 2.0 | 50% | Half-maximal (Ki) |
| **3.0** | 3.13 | 31.9% | Strong inhibition |
| **4.0** | 10.5 | 9.5% | Very strong inhibition |

**Hill Coefficient (n=4)**: Cooperative inhibition - ATP binding at one regulatory site enhances binding at other sites.

### Layer 3: Michaelis-Menten Kinetics (Substrate Saturation)

**Expression**: `numerator = 0.8 * F6P * ATP / (1.0 + F6P + ATP)`

**Behavior**: Enzyme rate increases with substrate concentration until saturation.

---

## Rate Expression Analysis

**Complete Rate**:
```
rate = (0.8 * F6P * ATP / (1.0 + F6P + ATP)) / (1.0 + (ATP_high / 2.5)**4)
```

**At Initial Conditions** (F6P=2.0, ATP=4.0, ATP_high=5.0, AMP=0.05):

1. **Layer 1 Check (Dynamic Inhibitor)**:
   - Threshold = 4.0 * (1.0 + 0.05/0.1) = 4.0 * 1.5 = **6.0 mM**
   - ATP_high (5.0) < threshold (6.0) → **PASS** ✓

2. **Layer 2 Evaluation (Hill Equation)**:
   - Numerator = 0.8 * 2.0 * 4.0 / (1.0 + 2.0 + 4.0) = 6.4 / 7.0 = **0.914**
   - Hill denominator = 1.0 + (5.0/2.5)^4 = 1.0 + 16 = **17**
   - Rate = 0.914 / 17 = **0.054** (5.4% of max)

3. **Layer 3 (Implicit in Numerator)**:
   - Michaelis-Menten terms already included

**Result**: Enzyme enabled but running at 5.4% of maximum rate.

---

## Simulation Scenarios

### Scenario A: High Energy State (AMP = 0.0 mM)

**Initial State**:
- F6P = 2.0 mM
- ATP = 4.0 mM (substrate)
- ATP_high = 5.0 mM (inhibitor)
- AMP = 0.0 mM (no energy demand)

**Behavior**:
1. Dynamic threshold = 4.0 * (1.0 + 0.0/0.1) = **4.0 mM**
2. ATP_high (5.0) ≥ threshold (4.0) → **BLOCKED** ❌
3. Rate formula **NOT EVALUATED** (transition disabled)

**Biological Meaning**: Cell has abundant ATP, no energy demand → glycolysis shutdown prevents ATP waste.

### Scenario B: Moderate Energy Deficit (AMP = 0.05 mM) - **Initial State**

**Initial State**:
- F6P = 2.0 mM
- ATP = 4.0 mM
- ATP_high = 5.0 mM
- AMP = 0.05 mM (moderate demand)

**Behavior**:
1. Dynamic threshold = 4.0 * (1.0 + 0.05/0.1) = **6.0 mM**
2. ATP_high (5.0) < threshold (6.0) → **PASS** ✓
3. Rate = 0.914 / 17 = **0.054** (5.4% of max)

**Biological Meaning**: Energy demand present → AMP relieves inhibition → glycolysis proceeds slowly.

### Scenario C: Severe Energy Deficit (AMP = 0.10 mM)

**Initial State**:
- F6P = 2.0 mM
- ATP = 4.0 mM
- ATP_high = 5.0 mM
- AMP = 0.10 mM (severe deficit)

**Behavior**:
1. Dynamic threshold = 4.0 * (1.0 + 0.10/0.1) = **8.0 mM**
2. ATP_high (5.0) < threshold (8.0) → **PASS** ✓
3. Rate = 0.914 / 17 = **0.054** (5.4% of max, same as Scenario B)

**Biological Meaning**: Higher AMP further relieves inhibitor arc, but Hill equation still limits rate. The enzyme is "unlocked" but rate-limited by ATP concentration in formula.

### Scenario D: Low ATP State (ATP_high = 2.0 mM, AMP = 0.05 mM)

**Modified State** (user can test by changing P5 marking):
- F6P = 2.0 mM
- ATP = 4.0 mM
- ATP_high = 2.0 mM (low cellular ATP)
- AMP = 0.05 mM

**Behavior**:
1. Dynamic threshold = 4.0 * (1.0 + 0.05/0.1) = **6.0 mM**
2. ATP_high (2.0) < threshold (6.0) → **PASS** ✓
3. Hill denominator = 1.0 + (2.0/2.5)^4 = 1.0 + 0.41 = **1.41**
4. Rate = 0.914 / 1.41 = **0.648** (64.8% of max) ⬆️

**Biological Meaning**: Low ATP → minimal Hill inhibition → high glycolytic rate to restore ATP.

---

## Key Learning Points

### 1. Multi-Layer Regulation Hierarchy

**Execution Order**:
```
Check Dynamic Inhibitor Arc (Layer 1)
  ↓ [If PASS]
Evaluate Rate Formula with Hill Equation (Layer 2)
  ↓ [If rate > 0]
Execute Michaelis-Menten Kinetics (Layer 3)
  ↓
Update Token Concentrations
```

### 2. Dynamic Threshold Supersedes Weight

```python
arc_A5.weight = 1          # Token consumption (not used for inhibitor)
arc_A5.threshold = "4.0 * (1.0 + AMP / 0.1)"  # Enablement check (SUPERSEDES weight)
```

**Critical**: The `weight` property is **IGNORED** for enablement when `threshold` is set.

### 3. Context-Dependent Regulation

The same ATP concentration (5.0 mM) has different effects:
- **AMP = 0.0 mM**: Enzyme **blocked** (threshold = 4.0)
- **AMP = 0.05 mM**: Enzyme **active** (threshold = 6.0)

This demonstrates **cross-talk** between metabolic signals.

### 4. Hill Cooperativity (n=4)

The Hill coefficient creates a **sigmoidal** (S-shaped) dose-response curve:
- **Shallow slope** at low/high ATP
- **Steep transition** near Ki (2.5 mM)
- **Switch-like behavior** in physiological range

### 5. Pasteur Effect Mechanism

```
Anaerobic conditions
  ↓
Low ATP production
  ↓
ATP degradation → AMP
  ↓
High AMP relieves ATP inhibition
  ↓
PFK activated
  ↓
Glycolysis increases
  ↓
Compensates for low ATP yield per glucose
```

This example models the **molecular logic** of this metabolic compensation.

---

## Experimental Validation

### Expected Dynamics

**Simulation Duration**: 10 seconds, dt = 0.01

**Phase 1** (0-3 sec): Slow F1,6BP accumulation
- Rate limited by Hill inhibition (~5% max)
- ATP_high decreases slowly (consumed elsewhere in cell)

**Phase 2** (3-7 sec): Accelerating production (if ATP_high drops below ~3 mM)
- Hill inhibition weakens exponentially
- Positive feedback: ATP consumption → lower ATP_high → less inhibition

**Phase 3** (7-10 sec): Near-maximal rate (if ATP_high < 1 mM)
- Minimal Hill inhibition
- Rate limited only by substrate availability

**Try These Experiments**:

1. **Vary AMP** (P6 marking):
   - 0.0 mM → Enzyme blocked (Layer 1 fails)
   - 0.05 mM → Enzyme active, rate-limited (default)
   - 0.1 mM → Enzyme active, higher threshold relief
   - 0.2 mM → Enzyme active, maximum relief

2. **Vary ATP_high** (P5 marking):
   - 3.0 mM → Moderate inhibition (~32% rate)
   - 5.0 mM → Strong inhibition (~5% rate, default)
   - 7.0 mM → Very strong inhibition (~1.5% rate)
   - 10.0 mM → Near-complete inhibition (<0.1% rate)

3. **Combined Effect**:
   - ATP_high = 6.0 mM, AMP = 0.0 → **Blocked** (threshold = 4.0)
   - ATP_high = 6.0 mM, AMP = 0.05 → **Active** (threshold = 6.0)
   - ATP_high = 6.0 mM, AMP = 0.10 → **Active** (threshold = 8.0)
   - Demonstrates dynamic threshold in action!

---

## Comparison with Example 04

| Feature | Example 04 | Example 16 (This) |
|---------|-----------|-------------------|
| **Inhibitor Arc** | Fixed threshold (4.0 mM) | **Dynamic threshold** (4.0 × f(AMP)) |
| **Hill Equation** | Yes (n=4, Ki=2.0) | Yes (n=4, Ki=2.5) |
| **AMP Modulation** | None | **Yes** (Pasteur effect) |
| **Layers** | 2 (inhibitor + Hill) | **3** (dynamic inhibitor + Hill + MM) |
| **ATP at 5.0 mM** | Always blocked | **Depends on AMP** |
| **Biological Realism** | High | **Very high** (context-dependent) |
| **Complexity** | Moderate | High |

**Advantage of Example 16**: Models **metabolic state sensing** where enzyme sensitivity adapts to cellular energy status.

---

## Topology Analysis

### Structural Properties

**Places**:
- **Substrates**: P1 (F6P), P2 (ATP)
- **Products**: P3 (F1,6BP), P4 (ADP)
- **Regulators**: P5 (ATP_high inhibitor), P6 (AMP activator - indirect via threshold)

**Transitions**:
- **T1 (PFK)**: Single enzymatic step

**Arcs**:
- **2 input arcs** (normal): Substrate consumption
- **2 output arcs** (normal): Product formation
- **1 inhibitor arc** (dynamic): Context-dependent regulation
- **1 test arc**: Classical Petri net sensor (makes AMP dependency explicit)

### Behavioral Properties

**Boundedness**: Continuous model (tokens represent concentrations in mM)

**Liveness**: T1 liveness depends on:
1. Substrate availability (F6P, ATP > 0)
2. Dynamic inhibitor threshold (ATP_high < threshold(AMP))
3. Rate function value (must be > 0)

**Deadlock Freedom**: No deadlock possible (single transition, no circular dependencies)

### Regulatory Structure

**Direct Regulation**:
- ATP_high ⊣ PFK (inhibitor arc with dynamic threshold)
- AMP ⊙ PFK (test arc, classical enablement condition)

**Indirect Regulation**:
- AMP modulates ATP_high inhibition threshold (referenced in A5 threshold expression)

**Feedback Loops**: None in this isolated step (but in full glycolysis, F1,6BP feeds back)

---

## Metadata

**Compounds**:
- F6P: KEGG C00085, ChEBI 16084
- ATP: KEGG C00002, ChEBI 15422
- F1,6BP: KEGG C00354, ChEBI 16905
- ADP: KEGG C00008, ChEBI 16761
- AMP: KEGG C00020, ChEBI 16027

**Enzyme**:
- EC: 2.7.1.11
- KEGG Enzyme: K00850
- Name: 6-phosphofructokinase
- KEGG Reaction: R00756

**Regulation**:
- Type: Allosteric inhibition (ATP) with allosteric activation (AMP)
- Mechanism: Dynamic threshold modulation
- Hill Coefficient: 4 (cooperative)
- Ki (ATP): 2.5 mM (half-maximal inhibition)
- Ka (AMP): 0.1 mM (threshold modulation constant)

---

## References

1. **Pasteur, L.** (1861). Mémoire sur la fermentation alcoolique. *Annales de Chimie et de Physique*, 3(58), 323-426.
   - Original discovery of aerobic/anaerobic glycolysis difference

2. **Blangy, D. et al.** (1968). Kinetics of the allosteric interactions of phosphofructokinase from *Escherichia coli*. *Journal of Molecular Biology*, 31(1), 13-35.
   - Detailed kinetic characterization of PFK cooperativity

3. **Ramaiah, A. et al.** (1964). Adenine nucleotide control of phosphofructokinase. *Journal of Biological Chemistry*, 239(9), 3619-3622.
   - Discovery of AMP activation relieving ATP inhibition

4. **Hofmeyr, J.H.S. & Cornish-Bowden, A.** (2000). Regulating the cellular economy of supply and demand. *FEBS Letters*, 476(1-2), 47-51.
   - Metabolic control analysis with multi-level regulation

5. **Berg, J.M., Tymoczko, J.L., & Stryer, L.** (2002). *Biochemistry*, 5th edition. Section 16.2: The Glycolytic Pathway Is Tightly Controlled.
   - Comprehensive description of PFK regulation including Pasteur effect

6. **SHYPN Documentation**: `doc/foundation/DUAL_LAYER_INHIBITION.md`
   - Technical details on dynamic threshold implementation

---

**Document Version**: 1.0  
**Date**: November 21, 2025  
**Status**: Foundation Example - Dynamic Threshold Demonstration
