# Examples 3-5 Redesign Specification for Signal Hierarchical Petri Nets

## Pedagogical Progression Strategy

The examples build incrementally toward the full 13-tuple formalism:
```
SPN = (P, T, F, W, M₀, Φ, C, Fₜ, Ψ, Fₛ, Wₛ, λ, θ)
```

---

## Example 3: Signal Places Introduction

### Purpose
Demonstrate **signal places (Ψ)** and **signal arcs (Fₛ)** - places with dual participation

### Model: ATP Dual Role in PFK Reaction

**Reaction**: F6P + ATP → F16BP + ADP

**Places** (4):
1. `F6P` (substrate, 2.0 mM)
2. `ATP` (substrate + signal, 3.0 mM) **← SIGNAL PLACE**
   - `is_signal_place: true`
3. `F16BP` (product, 0.1 mM)
4. `ADP` (product, 0.5 mM)

**Transitions** (1):
1. `PFK` (continuous)
   - Rate: Michaelis-Menten with Hill inhibition

**Arcs**:
- Normal arcs: F6P → PFK, ATP → PFK (consumptive)
- Normal arcs: PFK → F16BP, PFK → ADP (productive)
- **SIGNAL ARC**: ATP → PFK (non-consumptive, weight=1, for sensing)

**Key Innovation**:
- ATP participates in TWO ways:
  1. **Material arc** (F): Consumed as substrate (normal arc)
  2. **Signal arc** (Fₛ): Sensed for feedback inhibition (signal arc)
- Rate function: `v = Vmax * [F6P] / (Km + [F6P]) * [ATP] / (Km + [ATP]) / (1 + ([ATP]/Ki)^4)`
- Signal arc allows ATP concentration to regulate reaction WITHOUT being consumed by that regulatory interaction

**Chapter 4 Description**:
- Focus on dual participation of signal places
- ATP ∈ Ψ (signal place set)
- Compare to Example 2 (inhibitor arc uses separate ATP_high place)
- Here: ONE ATP place, TWO arc types

---

## Example 4: Hierarchy Layers

### Purpose
Demonstrate **layer assignments (λ)** - multi-scale metabolic organization

### Model: Upper Glycolysis with Layers

**Reactions** (3 steps):
1. Glucose + ATP → G6P + ADP (HK)
2. G6P ⇄ F6P (PGI, reversible)
3. F6P + ATP → F16BP + ADP (PFK)

**Places** (6) with layers:
1. `Glucose` (5.0 mM) - `layer: 1` (carbon input)
2. `ATP` (3.0 mM) - `layer: 0, is_signal_place: true` (energy currency)
3. `ADP` (0.5 mM) - `layer: 0, is_signal_place: true` (energy state)
4. `G6P` (0.8 mM) - `layer: 1` (metabolic intermediate)
5. `F6P` (0.2 mM) - `layer: 1` (metabolic intermediate)
6. `F16BP` (0.05 mM) - `layer: 2` (committed product)

**Transitions** (3):
1. `HK` (hexokinase) - `layer: 1`
2. `PGI` (phosphoglucose isomerase) - `layer: 1`
3. `PFK` (phosphofructokinase) - `layer: 2` (checkpoint)

**Layer Semantics**:
- **Layer 0**: Energy metabolism (ATP/ADP) - system-wide resource
- **Layer 1**: Primary carbon flow (glucose → G6P → F6P)
- **Layer 2**: Commitment point (F16BP) - irreversible glycolytic entry

**Key Innovation**:
- Layer assignments organize network by metabolic function
- Signal places (ATP, ADP) in Layer 0 regulate transitions in Layers 1-2
- Cross-layer signal arcs: ATP (Layer 0) → PFK (Layer 2)
- No preemption yet - just organizational hierarchy

**Chapter 4 Description**:
- Focus on layer-based organization
- λ: P → ℕ (layer assignment function)
- ATP/ADP as Layer 0 (fundamental resources)
- Shows how layers partition metabolic network by function
- Prepares for preemption in Example 5

---

## Example 5: Complete Formalism with Preemption

### Purpose
Demonstrate **ALL innovations** including **preemption thresholds (θ)**

### Model: Energy Charge Control with 3 Layers

**Biological Context**: Under energy stress, cells prioritize ATP regeneration over biosynthesis

**Places** (8) with layers:
1. `ADP` (2.0 mM) - `layer: 0, is_signal_place: true` (energy debt)
2. `Pi` (5.0 mM) - `layer: 0` (phosphate)
3. `ATP` (1.0 mM) - `layer: 0, is_signal_place: true` (energy currency)
4. `Glucose` (5.0 mM) - `layer: 1` (fuel)
5. `Pyruvate` (0.1 mM) - `layer: 1` (glycolysis product)
6. `Acetyl-CoA` (0.05 mM) - `layer: 2` (biosynthesis precursor)
7. `Biomass` (0.01 mM) - `layer: 2` (growth)
8. `Enzyme_ATP_synthase` (0.02 mM) - `layer: 0, is_catalyst: true`

**Transitions** (3) with priorities:
1. `ATP_Regeneration` - `layer: 0, priority: 10` (highest)
   - Reaction: ADP + Pi → ATP
   - **ESSENTIAL metabolism**
   - Can preempt Layer 2 transitions
   
2. `Glycolysis` - `layer: 1, priority: 5` (medium)
   - Reaction: Glucose → Pyruvate + 2 ATP
   - **GROWTH metabolism**
   
3. `Biosynthesis` - `layer: 2, priority: 1, preemption_threshold: {"ATP": 1.5}` (lowest)
   - Reaction: Pyruvate + ATP → Biomass
   - **LUXURY function**
   - **PREEMPTED when ATP < 1.5 mM**

**Arc Types**:
- Normal arcs (substrate consumption, product formation)
- Test arcs (enzyme catalysis)
- Signal arcs (ATP, ADP sensing across layers)
- Inhibitor arcs (ATP feedback on Glycolysis)

**Preemption Semantics**:
- When `ATP < 1.5 mM`:
  * `Biosynthesis` transition **BLOCKED** (preempted)
  * `ATP_Regeneration` has priority to fire
  * Cell prioritizes survival over growth
  
- When `ATP ≥ 1.5 mM`:
  * All transitions enabled (normal operation)
  * Biosynthesis can proceed

**Key Innovation - Complete 13-tuple**:
```
P = {ADP, Pi, ATP, Glucose, Pyruvate, Acetyl-CoA, Biomass, Enzyme}
T = {ATP_Regeneration, Glycolysis, Biosynthesis}
F = normal arcs (substrate/product flow)
W = arc weights
M₀ = initial marking
Φ = place capacities
C = arc colors (if needed)
Fₜ = test arcs (enzyme)
Ψ = {ATP, ADP} (signal places)
Fₛ = signal arcs (cross-layer regulation)
Wₛ = signal arc weights
λ = {0: {ADP, Pi, ATP, Enzyme}, 1: {Glucose, Pyruvate}, 2: {Acetyl-CoA, Biomass}}
θ = {Biosynthesis: {"ATP": 1.5}} (preemption thresholds)
```

**Chapter 4 Description**:
- Emphasize **complete formalism** achieved
- Preemption demonstrates **evolutionary prioritization**
- Energy crisis → survival mechanisms activate
- Mimics bacterial stress response (B. subtilis sporulation blocked under starvation)
- All 4 innovations present:
  1. Test arcs (enzyme catalysis)
  2. Inhibitor arcs (feedback)
  3. Signal places + arcs (ATP/ADP dual role)
  4. Hierarchy + preemption (priority scheduling)

---

## Implementation Notes

### For Model Files (.shy JSON):
- Add `is_signal_place: true` to ATP, ADP in Examples 3-5
- Add `layer: N` to all places in Examples 4-5
- Add `priority: N` to transitions in Example 5
- Add `preemption_threshold: {"place_name": value}` to Biosynthesis in Example 5
- Add signal arcs with `arc_type: "signal"` in Examples 3-5

### For Chapter 4:
- Rewrite Example 3: Focus on signal place concept
- Rewrite Example 4: Focus on layer organization
- Rewrite Example 5: Focus on complete formalism + preemption
- Add clear progression narrative connecting examples

### Simulation Data Needed:
- Example 3: Show ATP dual role (consumed + sensed)
- Example 4: Show coordinated multi-layer flux
- Example 5: Show preemption event (biosynthesis blocked when ATP drops)

---

## Validation Criteria

### Example 3:
- ✓ ATP marked as signal place
- ✓ Signal arc present (ATP → PFK)
- ✓ ATP consumed via normal arc
- ✓ ATP concentration affects rate via signal arc

### Example 4:
- ✓ All places have layer assignments
- ✓ 3 distinct layers (0, 1, 2)
- ✓ Layer 0 contains energy currency
- ✓ Cross-layer signal arcs present

### Example 5:
- ✓ All 13 tuple components present
- ✓ Preemption threshold defined
- ✓ Priority values assigned
- ✓ Biosynthesis blocks when ATP < threshold
- ✓ ATP_Regeneration has highest priority

---

## Timeline

1. **Model file modifications** (manual JSON editing or programmatic)
2. **Simulation runs** for new models
3. **Chapter 4 rewrite** for Examples 3-5
4. **Figure generation** for new models
5. **Thesis compilation** and validation
