# Selective Signal Places Test for Bacillus Sporulation

**Date**: January 31, 2026  
**Purpose**: Test if using only essential signal places (Ψ ⊂ P) reproduces thesis results, validating Chapter 3's principle that ANY compound can be chosen as signal place when biologically justified.

## Background

Chapter 5 thesis states that the Bacillus model uses **Ψ = P** (all 26 places are signal places). However, Chapter 3's architectural principle states that signal places should be chosen based on **biological evidence of regulatory gating role**. This test investigates whether selecting only essential signal places reproduces the same commitment threshold prediction.

## Essential Signal Places Selection

Based on Chapter 5 validation analysis, the following places are essential for normal model investigation:

### 1. **ATP_pool** (Layer 3)
- **Role**: Energy threshold gating
- **Justification**: Phosphorelay activation requires ATP > 2.5 mM (experimentally measured)
- **Mechanism**: KinA phosphorylation exhibits concentration-dependent activation
- **Prediction**: Enables commitment threshold computation via signal consumption

### 2. **Spo0A_P** (Layer 1)
- **Role**: Master regulator for commitment decision
- **Justification**: Commitment occurs when [Spo0A-P] > 0.6·[Spo0A]_total (ChIP-seq data)
- **Mechanism**: Transcriptional control of sigma factors
- **Prediction**: Determines sporulation vs competence pathway selection

### 3. **SigmaF** (Layer 0)
- **Role**: Sporulation pathway execution
- **Justification**: σF activation creates irreversible commitment
- **Mechanism**: Forespore-specific gene expression
- **Prediction**: Observable output for pathway selection

### 4. **SigmaH** (Layer 3)
- **Role**: Early sporulation gene activation
- **Justification**: σH initiates sporulation cascade under normal conditions
- **Mechanism**: Transcriptional activation of early sporulation genes
- **Prediction**: Canonical pathway progression marker

## Places Changed to Normal (22 places)

The following places are changed from signal to normal places:

### Metabolic Places (3)
- **GTP_pool**: Secondary energy metabolite (not directly involved in commitment threshold)
- **ADP_pool**: Depleted energy marker (inverse of ATP, redundant for threshold)
- **GDP_pool**: Secondary depleted marker

### Environmental/Quorum Sensing (2)
- **Nutrients**: External resource availability (upstream of ATP)
- **Cell_density**: Quorum sensing signal (modulates but doesn't determine threshold)

### Phosphorelay Intermediates (6)
- **KinA_kinase**: Sensor kinase (upstream, ATP-gated)
- **KinA_P**: Phosphorylated kinase (transient intermediate)
- **Spo0F**: Phosphorelay intermediate (transient)
- **Spo0F_P**: Phosphorylated intermediate (transient)
- **Spo0B**: Phosphotransferase (transient)
- **Spo0A**: Unphosphorylated regulator (Spo0A_P is the active form, kept as signal)

### Regulatory Components (1)
- **RapA**: Phosphatase (negative regulator, modulates but doesn't determine threshold)

### Execution Machinery (4)
- **SigmaE**: Mother cell sigma factor (downstream of commitment)
- **SigmaG**: Late forespore sigma factor (downstream)
- **SigmaK**: Late mother cell sigma factor (downstream)
- **Septum**: Physical structure (downstream consequence)

### Structural/Output Places (6)
- **Forespore**: Compartment marker (downstream)
- **Mother_cell**: Compartment marker (downstream)
- **Cortex**: Spore structure (downstream)
- **Inner_coat**: Coat layer (downstream)
- **Outer_coat**: Coat layer (downstream)
- **Mature_spore**: Final output (downstream)

## Rationale for Selection

### Why ATP_pool but not ADP_pool?
- **ATP_pool**: Directly gates KinA via threshold θ = 2500 mM
- **ADP_pool**: Inverse marker (when ATP decreases, ADP increases)
- **Redundancy**: M(ADP) ≈ [ATP]_total - M(ATP), so only one needed as signal
- **Biological evidence**: KinA activity studies measure ATP concentration, not ADP

### Why Spo0A_P but not Spo0F_P or phosphorelay intermediates?
- **Spo0A_P**: Direct transcriptional activator with measured threshold (60%)
- **Intermediates**: Transient species in cascade, no independent gating role
- **Architecture**: Spo0A_P is the information output of phosphorelay integration
- **Biological evidence**: ChIP-seq shows Spo0A-P binding, not intermediate binding

### Why SigmaF and SigmaH but not SigmaE/G/K?
- **SigmaF**: Commitment marker (θ = 0, ATP-independent)
- **SigmaH**: Early activation marker (normal conditions)
- **SigmaE/G/K**: Downstream of commitment, no independent threshold
- **Biological evidence**: σF/σH timing studies show hierarchical activation

## Hypothesis

**H0 (Null)**: Only essential signal places are sufficient to reproduce thesis results:
- Commitment threshold prediction: 2.38 ± 0.15 mM (model) vs 2.21 ± 0.18 mM (experimental)
- Hierarchical preemption: σF (t=0.03s) before phosphorelay (t>5s) under stress
- Irreversibility: ATP recovery cannot reverse commitment

**H1 (Alternative)**: All places must be signal places (Ψ = P) for correct prediction

## Models Generated

1. **bacillus_sporulation_normal.shy** (original)
   - Ψ = P (26 signal places)
   - Baseline for comparison

2. **bacillus_sporulation_normal_selective_signals.shy** (new)
   - Ψ = {ATP_pool, Spo0A_P, SigmaF, SigmaH} (4 signal places)
   - Test condition

3. **bacillus_sporulation_stress.shy** (original)
   - Ψ = P (26 signal places)
   - Baseline for stress conditions

4. **bacillus_sporulation_stress_selective_signals.shy** (new)
   - Ψ = {ATP_pool, Spo0A_P, SigmaF, SigmaH} (4 signal places)
   - Test condition under stress

## Expected Outcomes

### If H0 is correct (selective signals sufficient):
- ✓ Threshold prediction: ~2.38 mM (unchanged)
- ✓ Prediction error: ~7.7% vs experimental
- ✓ Hierarchical preemption: σF before phosphorelay under stress
- ✓ Basin boundaries: Distinct attractor basins above/below threshold
- **Conclusion**: Chapter 3 principle validated - signal place selection is biology-driven

### If H1 is correct (all places needed):
- ✗ Threshold prediction: Different from 2.38 mM
- ✗ Prediction error: >10% vs experimental
- ✗ Hierarchical preemption: Altered timing or no preemption
- ✗ Basin boundaries: Loss of commitment irreversibility
- **Conclusion**: Ψ = P design was necessary, not a choice

## Validation Metrics

1. **Quantitative threshold**
   - Original: [ATP]_threshold = 2.38 ± 0.15 mM
   - Target: Within ±0.2 mM of original

2. **Prediction accuracy**
   - Original: 7.7% error vs experimental 2.21 mM
   - Target: Within ±2% of original error

3. **Hierarchical preemption timing (stress)**
   - Original: σF (t=0.03s), σE (t=0.44s), Septum (t=5.3s)
   - Target: Same activation sequence and timing order

4. **Sporulation probability sigmoid**
   - Original: P_spor = 1/(1 + e^(-4.2(ATP - 2.38)))
   - Target: Inflection point within ±0.15 mM, steepness within ±0.5 mM^(-1)

5. **Basin boundary sharpness**
   - Original: P_spor < 0.06 for ATP < 2.0 mM, P_spor > 0.94 for ATP > 2.6 mM
   - Target: Similar bifurcation sharpness

## Implementation Status

✅ **Original models copied**
- bacillus_sporulation_normal.shy (67K)
- bacillus_sporulation_stress.shy (64K)

✅ **Selective signal models generated**
- bacillus_sporulation_normal_selective_signals.shy (67K)
- bacillus_sporulation_stress_selective_signals.shy (64K)

✅ **Signal place modifications**
- 4 places kept as signal places
- 22 places changed to normal places
- Metadata updated with modification note

## Next Steps

1. **Run simulations**
   - Load selective signal models in SHYpn
   - Execute normal and stress scenarios
   - Collect threshold and timing data

2. **Compare results**
   - Threshold predictions (original vs selective)
   - Sigmoid curve parameters
   - Hierarchical preemption timing
   - Basin boundary structure

3. **Statistical validation**
   - Quantify prediction differences
   - Assess significance of deviations
   - Document which metrics are preserved

4. **Interpret findings**
   - If H0: Confirms architecture principle, ANY compound can be signal when justified
   - If H1: Requires investigation of why all places needed
   - Update thesis if necessary based on findings

## Files

- `bacillus_sporulation_normal.shy` - Original normal model (Ψ = P)
- `bacillus_sporulation_normal_selective_signals.shy` - Test normal model (Ψ ⊂ P)
- `bacillus_sporulation_stress.shy` - Original stress model (Ψ = P)
- `bacillus_sporulation_stress_selective_signals.shy` - Test stress model (Ψ ⊂ P)
- `update_signal_places.py` - Script for generating selective models
- This document: `SELECTIVE_SIGNAL_PLACES_TEST.md`

## References

- Chapter 3, Principle 3.1: Vertical-Horizontal Separation
- Chapter 3, Definition 3.1: Signal places as interface nodes
- Chapter 5, Section 5.2: Prediction Goals
- Chapter 5, Section 5.3: Model Instantiation
- Chapter 5, Section 5.6: Experimental Validation
