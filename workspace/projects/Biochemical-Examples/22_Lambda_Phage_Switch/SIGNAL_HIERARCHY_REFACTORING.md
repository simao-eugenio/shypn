# Lambda Phage Switch - Signal Hierarchy Theory Refactoring

**Date**: December 21, 2025  
**Base Model**: `model_balanced_UV.shy`  
**New Model**: `model_balanced_UV_signal_hierarchy.shy`

## Overview

This refactoring applies **Signal Partition Theory** to the Lambda phage bistable switch model, separating material flow (biochemical reactions) from information flow (regulatory signals).

## Theoretical Foundation

### Signal Partition Architecture

**Place Partition**:
- **P_m** (Material): Genes, mRNAs, monomeric proteins (mass transfer)
- **P_s ⊆ Ψ** (Signal): CI_Dimer (P7), Cro_Dimer (P8) - regulatory information
- **Constraint**: P_m ∩ P_s = ∅ (disjoint partitions)

**Arc Partition**:
- **Black arcs**: Material flow (transcription, translation, degradation)
- **Orange arcs**: Information flow (regulatory inhibition)

### Key Principle

> *"Regulatory control (information) flows through signal arcs, not embedded in rate functions."*

## Changes Made

### 1. Signal Place Marking

**CI_Dimer (P7)**:
```json
{
  "is_signal_place": true,
  "signal_type": "Ψ_regulatory",
  "border_color": [1.0, 0.5, 0.0],  // Orange border
  "metadata": {
    "partition": "signal",
    "function": "regulatory_control"
  }
}
```

**Cro_Dimer (P8)**:
```json
{
  "is_signal_place": true,
  "signal_type": "Ψ_regulatory",
  "border_color": [1.0, 0.5, 0.0],  // Orange border
  "metadata": {
    "partition": "signal",
    "function": "regulatory_control"
  }
}
```

### 2. Rate Function Simplification

**Original T1 (CI_Transcription)**:
```python
rate = 2.0 * (1 + 0.5 * CI_Dimer / (5 + CI_Dimer)) / (1 + (Cro_Dimer / 15)**2)
#      ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^
#      basal  positive feedback (self-activation)      repression (REMOVED)
```

**New T1**:
```python
rate = 2.0 * (1 + 0.5 * CI_Dimer / (5 + CI_Dimer))
#      ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#      basal  positive feedback only
```

**Original T6 (Cro_Transcription)**:
```python
rate = 2.0 * (1 + 0.5 * Cro_Dimer / (5 + Cro_Dimer)) / (1 + (CI_Dimer / 15)**2)
#      ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^
#      basal  positive feedback (self-activation)       repression (REMOVED)
```

**New T6**:
```python
rate = 2.0 * (1 + 0.5 * Cro_Dimer / (5 + Cro_Dimer))
#      ^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#      basal  positive feedback only
```

### 3. Inhibitor Arcs Added

**A51_signal: CI represses Cro**
- Source: P7 (CI_Dimer) - signal place
- Target: T6 (Cro_Transcription)
- Type: Inhibitor arc
- Threshold: 15 (Ki from original rate function)
- Color: Orange (regulatory signal)
- Hill coefficient: n=2 (stored in metadata)

**A53_signal: Cro represses CI**
- Source: P8 (Cro_Dimer) - signal place
- Target: T1 (CI_Transcription)
- Type: Inhibitor arc
- Threshold: 15 (Ki from original rate function)
- Color: Orange (regulatory signal)
- Hill coefficient: n=2 (stored in metadata)

## Visual Coding System

| Color | Arc Type | Meaning |
|-------|----------|---------|
| **Black** | Normal | Material flow (transcription, translation, decay) |
| **Orange** | Inhibitor | Regulatory signal (repression) |
| **Orange dashed** | Test | Catalytic/enabling (genes as templates) |

| Border | Place Type | Meaning |
|--------|------------|---------|
| **Black** | Material | Biochemical compounds (genes, mRNAs, proteins) |
| **Orange** | Signal | Regulatory information (active dimers) |

## Behavioral Equivalence

### Original Model Behavior
Mutual repression embedded in rate functions:
```
T1_rate ∝ 1 / (1 + (Cro_Dimer / 15)^2)  # Cro inhibits CI
T6_rate ∝ 1 / (1 + (CI_Dimer / 15)^2)   # CI inhibits Cro
```

### New Model Behavior
Mutual repression via inhibitor arcs:
```
A53_signal: Cro_Dimer --⊣ T1 (threshold=15)  # Cro inhibits CI
A51_signal: CI_Dimer --⊣ T6 (threshold=15)   # CI inhibits Cro
```

**Expected outcomes**:
- Same bistability (42:48 lysogenic:lytic)
- Same UV response (98% lytic)
- Clearer architectural separation

## Advantages of Signal Hierarchy

1. **Explicit Regulatory Architecture**
   - Inhibitor arcs visible in the diagram
   - No need to inspect rate functions to understand regulation
   - Regulatory topology immediately clear

2. **Compositional Modularity**
   - Regulatory signals can be added/removed without editing rate functions
   - Signal places can regulate multiple transitions
   - Easier to extend model with new regulatory interactions

3. **Theoretical Soundness**
   - Partition constraint (P_m ∩ P_s = ∅) ensures no type confusion
   - Information flow distinct from mass transfer
   - Aligns with biological reality (proteins carry regulatory information)

4. **Visual Clarity**
   - Orange arcs/borders = regulatory/signal
   - Black arcs/borders = biochemical/material
   - Immediate recognition of signal vs material flow

5. **Tool Support**
   - Inhibitor arcs have explicit thresholds (Ki values)
   - Hill coefficients stored in arc metadata
   - Signal places can have special rendering (hexagons, orange fill)

## Implementation Notes

### Inhibitor Arc Semantics

In shypn, inhibitor arcs implement Hill function repression:
```python
inhibition_factor = 1 / (1 + (source_marking / threshold)^hill)
effective_rate = base_rate * inhibition_factor
```

For this model:
- threshold = 15 (Ki, half-maximal inhibition)
- hill = 2 (cooperative binding, stored in metadata)

This exactly matches the original rate function repression term:
```python
1 / (1 + (CI_Dimer / 15)**2)  # Original
```

### Signal Place Properties

Signal places (P7, P8) remain **non-consuming** in transcription:
- Genes (P1, P4) use test arcs (non-consuming templates)
- Dimers (P7, P8) use inhibitor arcs (non-consuming regulators)
- Only mRNAs/proteins are consumed (material flow)

## Validation Strategy

1. **Visual Inspection**
   - Load `model_balanced_UV_signal_hierarchy.shy` in shypn
   - Verify orange borders on P7, P8
   - Verify orange inhibitor arcs: P7→T6, P8→T1

2. **Simulation Comparison**
   - Run 100 replicates with ZERO initial conditions, no UV
   - Compare outcome distribution to original (expect 42:48)
   - Run 100 replicates with BALANCED + UV
   - Compare outcome distribution to original (expect 2:98)

3. **Rate Function Verification**
   - Check that T1, T6 rates are simplified (no embedded repression)
   - Check that inhibitor arcs have threshold=15
   - Verify behavioral equivalence

## Future Extensions

This signal hierarchy architecture enables:

1. **Additional Regulatory Layers**
   - Add RecA signal place (P14) with orange border
   - Make RecA→T25 an orange test arc (RecA activates cleavage)

2. **Metabolic Integration**
   - Add ATP place (material, black border)
   - Transcription consumes ATP (black arc)
   - Energy depletion affects transcription (material constraint)

3. **Population-Level Signaling**
   - Add extracellular signal places (Ψ_environmental)
   - Quorum sensing molecules regulate λ decision
   - Population feedback via signal arcs

## References

- **Signal Partition Theory**: `doc/SIGNAL_PARTITION_THEORY.md`
- **Visual Coding System**: `doc/SIGNAL_VISUAL_CODING.md`
- **Original Model**: `FINAL_MODEL_DOCUMENTATION.md`
- **Inhibitor Arc Semantics**: `src/shypn/netobjs/inhibitor_arc.py`

## Summary

This refactoring demonstrates how **Signal Partition Theory** can clarify gene regulatory networks by:
- Separating information flow (regulatory signals) from material flow (biochemical reactions)
- Externalizing regulatory logic from rate functions to explicit arcs
- Using visual coding (orange) to distinguish signal elements
- Maintaining behavioral equivalence while improving architectural clarity

The Lambda phage switch is now a showcase for signal hierarchy modeling in biochemical Petri nets.
