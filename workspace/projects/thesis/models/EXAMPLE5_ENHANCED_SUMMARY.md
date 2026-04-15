# Example 5: Enhanced Multi-Compartment Energy Management

## Model Summary

**File**: `example5_energy_sensing.shy`  
**Type**: Signal Hierarchical Petri Net (SHYpn) with complete formalism  
**Version**: Enhanced with multi-compartment signals, source/sink transitions, spatial hierarchy

## Model Components

### Places (13 total, 6 signal places)

#### Layer 0: Energy Currency (Signal Places)
- **P1**: ATP_cytoplasm (3.0 mM) [SIGNAL] - Cytoplasmic ATP pool
- **P2**: ATP_mitochondria (5.0 mM) [SIGNAL] - Mitochondrial ATP pool (higher concentration)
- **P3**: ADP_cytoplasm (0.5 mM) [SIGNAL] - Cytoplasmic ADP pool
- **P4**: ADP_mitochondria (0.2 mM) [SIGNAL] - Mitochondrial ADP pool
- **P5**: Ca2+ (0.0001 mM) [SIGNAL] - Calcium ion regulatory signal

#### Layer 1: Metabolic Substrates
- **P6**: Glucose (5.0 mM) - Cytoplasmic glucose (from uptake)
- **P7**: Pyruvate_cyto (0.1 mM) - Cytoplasmic pyruvate (glycolysis product)
- **P8**: Pyruvate_mito (0.05 mM) - Mitochondrial pyruvate (oxidative fuel)
- **P9**: O2 (0.2 mM) - Oxygen for respiration (from diffusion)

#### Layer 2: Biosynthetic Products
- **P10**: Protein_cyto (0.01 mM) - Cytoplasmic proteins
- **P11**: Protein_mito (0.005 mM) - Mitochondrial proteins
- **P12**: Lipids (0.001 mM) - Membrane lipids

#### Layer 3: Growth/Quorum
- **P13**: Biomass (1.0 AU) [SIGNAL] - Cell size/density sensor

### Transitions (12 total)

#### Layer 0: Energy Maintenance (Priority 10-9)
- **T1**: MitochondrialATP (Priority 10) - Oxidative phosphorylation
  * Rate: `8.0 * (Pyruvate_mito/(0.1+Pyruvate_mito)) * (O2/(0.05+O2)) * (ADP_mito/(0.1+ADP_mito))`
  * Consumes: Pyruvate_mito, O2, ADP_mito [signal_flow]
  * Produces: ATP_mito [signal_flow]
  * Regulated by: Ca2+ [test arc]

- **T2**: ATPase_Translocase (Priority 9) - ATP export from mitochondria
  * Rate: `5.0 * (ATP_mito - ATP_cyto)` (concentration gradient)
  * Consumes: ATP_mito [signal_flow]
  * Produces: ATP_cyto [signal_flow]

- **T12**: O2_Diffusion (Priority 9) **[SOURCE]** - Oxygen supply
  * Rate: `3.0 * (1.0 - O2/0.5)` (saturation at 0.5 mM)
  * Produces: O2 (unbounded)

#### Layer 1: Essential Metabolism (Priority 8-5)
- **T3**: GlucoseUptake (Priority 8) **[SOURCE]** - Nutrient supply
  * Rate: `2.0 * (1.0 - Glucose/10.0)` (saturation at 10 mM)
  * Produces: Glucose (unbounded)

- **T4**: ATPase_Maintenance (Priority 7) **[SINK]** - Basal ATP consumption
  * Rate: `0.5 * ATP_cytoplasm` (proportional drain)
  * Consumes: ATP_cyto [signal_flow] (unbounded sink)
  * Produces: ADP_cyto [signal_flow]

- **T5**: PyruvateCarrier (Priority 6) - Transport to mitochondria
  * Rate: `2.0 * Pyruvate_cyto/(0.2+Pyruvate_cyto)`
  * Consumes: Pyruvate_cyto
  * Produces: Pyruvate_mito

- **T6**: Glycolysis (Priority 5) - Glucose catabolism
  * Rate: `10.0 * (Glucose/(1.0+Glucose)) * (ATP_cyto/(0.5+ATP_cyto))`
  * Consumes: Glucose, ATP_cyto [signal_flow]
  * Produces: Pyruvate_cyto (×2), ADP_cyto [signal_flow]

#### Layer 2: Biosynthesis (Priority 4-2)
- **T7**: ProteinSynthesis_Cyto (Priority 4) - Cytoplasmic translation
  * Rate: `1.5 * (ATP_cyto/(0.3+ATP_cyto)) * (Pyruvate_cyto/(0.1+Pyruvate_cyto))`
  * Consumes: ATP_cyto [signal_flow], Pyruvate_cyto
  * Produces: Protein_cyto, ADP_cyto [signal_flow]

- **T8**: ProteinSynthesis_Mito (Priority 3) - Mitochondrial translation
  * Rate: `1.0 * (ATP_mito/(0.3+ATP_mito)) * (Pyruvate_mito/(0.1+Pyruvate_mito))`
  * Consumes: ATP_mito [signal_flow], Pyruvate_mito
  * Produces: Protein_mito, ADP_mito [signal_flow]

- **T9**: ProteinDegradation (Priority 2) **[SINK]** - Protein turnover
  * Rate: `0.1 * Protein_cyto` (first-order decay)
  * Consumes: Protein_cyto (unbounded sink)

- **T10**: LipidSynthesis (Priority 2) - Membrane biogenesis
  * Rate: `0.8 * (ATP_cyto/(0.4+ATP_cyto)) * (Pyruvate_cyto/(0.15+Pyruvate_cyto))`
  * Consumes: ATP_cyto [signal_flow] (×2), Pyruvate_cyto
  * Produces: Lipids, ADP_cyto [signal_flow] (×2)

#### Layer 3: Growth/Division (Priority 1)
- **T11**: BiomassGrowth (Priority 1) - Cell growth
  * Rate: `0.5 * Protein_cyto * Protein_mito * Lipids * (ATP_cyto/(1.0+ATP_cyto))`
  * Consumes: Protein_cyto (×0.1), Protein_mito (×0.1), Lipids (×0.1), ATP_cyto [signal_flow]
  * Produces: Biomass [signal_flow] (×0.1), ADP_cyto [signal_flow]
  * **Preemption Threshold**: θ(BiomassGrowth, ATP_cyto) = 2.0 mM
  * When ATP_cyto < 2.0 mM, this transition is BLOCKED even if substrates available

### Arc Types (36 total)

- **Normal arcs (22)**: Consumptive flow for metabolites
- **Signal_flow arcs (13)**: Consumptive flow for signal places (ATP/ADP/Ca2+/Biomass)
- **Test arcs (1)**: Non-consumptive test of Ca2+ for MitochondrialATP regulation

## Formalism Demonstrations

### 1. Multi-Compartment Signals (Spatial Hierarchy)
**Feature**: Signal places with compartment-specific pools at different concentrations

- ATP_cytoplasm (3.0 mM) vs ATP_mitochondria (5.0 mM)
- ADP_cytoplasm (0.5 mM) vs ADP_mitochondria (0.2 mM)
- Connected via **T2 (ATPase_Translocase)** with signal_flow arcs
- Demonstrates: Spatial organization, concentration gradients, cross-compartment transport

### 2. Source Transitions (Unbounded Influx)
**Feature**: Transitions that produce tokens without consuming inputs

- **T3 (GlucoseUptake)**: Models continuous nutrient supply from environment
- **T12 (O2_Diffusion)**: Models continuous oxygen diffusion
- Rate saturates at upper limit (homeostatic feedback)
- Demonstrates: Open system modeling, external reservoirs

### 3. Sink Transitions (Unbounded Efflux)
**Feature**: Transitions that consume tokens without producing stoichiometric outputs

- **T4 (ATPase_Maintenance)**: Models basal ATP hydrolysis (housekeeping metabolism)
- **T9 (ProteinDegradation)**: Models continuous protein turnover
- Rate proportional to substrate concentration (first-order)
- Demonstrates: Open system modeling, continuous losses

### 4. Quorum Sensing Signals (Population-Level)
**Feature**: Signal place representing collective cellular state

- **P13 (Biomass)**: Accumulates as cell grows
- Regulates growth-related transitions (density-dependent feedback)
- Produced by **T11 (BiomassGrowth)** via signal_flow arc
- Demonstrates: Population-level coordination, quorum regulation

### 5. Regulatory Signals (Cross-Layer Coordination)
**Feature**: Signal place modulating multiple transitions via test arcs

- **P5 (Ca2+)**: Second messenger signal
- Test arc to **T1 (MitochondrialATP)** - activates ATP regeneration when Ca2+ present
- Demonstrates: Non-consumptive regulation, stress response coordination

### 6. Preemption Thresholds (Priority-Driven Blocking)
**Feature**: Transition blocking when signal place below threshold

- **T11 (BiomassGrowth)**: θ(BiomassGrowth, ATP_cyto) = 2.0 mM
- When ATP_cyto < 2.0 mM → BiomassGrowth DISABLED (even if substrates available)
- Higher priority transitions (T1-T10) continue → ATP recovers → Growth resumes
- Demonstrates: Smart resource allocation, metabolic prioritization

### 7. Complete 13-Tuple SHYpn Formalism
**SPN = (P, T, F, W, M₀, Φ, C, Fₜ, Ψ, Fₛ, Wₛ, λ, θ)**

- **P**: 13 places
- **T**: 12 transitions
- **F**: 22 normal arcs (consumptive flow)
- **W**: Normal arc weights [0.1, 1.0, 2.0]
- **M₀**: Initial markings {ATP_cyto: 3.0, ATP_mito: 5.0, ...}
- **Φ**: Rate laws (mass-action + Michaelis-Menten kinetics)
- **C**: No catalyst places (all consumptive)
- **Fₜ**: 1 test arc (Ca2+ → MitochondrialATP)
- **Ψ**: 6 signal places {ATP_cyto, ATP_mito, ADP_cyto, ADP_mito, Ca2+, Biomass}
- **Fₛ**: 13 signal_flow arcs (consumptive for signal places)
- **Wₛ**: Signal_flow weights [0.1, 1.0, 2.0]
- **λ**: 4 hierarchy layers {0: energy, 1: metabolism, 2: biosynthesis, 3: growth}
- **θ**: 1 preemption threshold {(T11, ATP_cyto): 2.0 mM}

## Expected Dynamics

### Phase 1: Initial Growth (0-50s)
- ATP_cyto = 3.0 mM (above threshold)
- All transitions active
- Glycolysis produces pyruvate
- Protein/lipid synthesis active
- Biomass accumulates

### Phase 2: ATP Depletion (~50s)
- ATP_cyto drops below 2.0 mM threshold
- **Preemption triggered**: T11 (BiomassGrowth) BLOCKED
- T4 (Maintenance) continues (Priority 7, no preemption)
- Lower priority biosynthesis (T7, T10) compete for remaining ATP

### Phase 3: ATP Recovery (50-100s)
- High priority T1 (MitochondrialATP, Priority 10) dominates
- T2 (Translocase) shuttles ATP_mito → ATP_cyto
- ATP_cyto recovers toward 2.0 mM

### Phase 4: Growth Resumption (>100s)
- ATP_cyto exceeds 2.0 mM threshold
- T11 (BiomassGrowth) reactivated
- Biomass continues accumulating
- Cycles repeat (oscillatory dynamics possible)

## Validation Metrics (Predicted)

### Signal Place Ranges
- ATP_cyto: 0.5-3.5 mM (oscillates around preemption threshold)
- ATP_mito: 3.0-5.5 mM (reservoir maintained higher)
- ADP_cyto: 0.3-2.0 mM (inverse of ATP_cyto)
- ADP_mito: 0.1-0.5 mM (inverse of ATP_mito)
- Ca2+: 0.0001 mM (baseline, spikes to 0.001 mM if stress module added)
- Biomass: 1.0 → 2.5 AU (monotonic growth with pauses during ATP depletion)

### Transition Firing Frequencies
- T1 (MitochondrialATP): Highest cumulative firings (~150-200)
- T6 (Glycolysis): High firings (~120-150)
- T4 (Maintenance): Continuous baseline (~80-100)
- T11 (BiomassGrowth): Intermittent, pauses during preemption (~20-30)

### Source/Sink Balance
- Glucose uptake (T3) ≈ Glycolysis consumption (T6) at steady state
- O2 diffusion (T12) ≈ MitochondrialATP consumption (T1) at steady state
- ATP maintenance drain (T4) balances regeneration (T1) during stress

### Preemption Events
- Expected 2-4 preemption episodes (ATP_cyto < 2.0 mM)
- Duration: 10-30s per episode
- Recovery time: 5-15s after preemption ends

## Biological Interpretation

This enhanced model captures **realistic cellular energy management**:

1. **Compartmentalization**: ATP generated in mitochondria (high [ATP]), exported to cytoplasm
2. **Priority hierarchy**: Energy maintenance (Layer 0) > Metabolism (Layer 1) > Biosynthesis (Layer 2) > Growth (Layer 3)
3. **Preemption ensures survival**: When ATP scarce, luxury growth halts but essential processes continue
4. **Source/sink realism**: Open system with continuous glucose/O2 supply and maintenance costs
5. **Quorum sensing**: Biomass signal could trigger cell division (not yet implemented)
6. **Regulatory coordination**: Ca2+ activates energy regeneration during stress

## Comparison to Simple Example 5

| Feature | Simple | Enhanced |
|---------|--------|----------|
| Places | 5 | 13 (+160%) |
| Signal Places | 2 (ATP, ADP) | 6 (+200%) |
| Transitions | 3 | 12 (+300%) |
| Arcs | 10 | 36 (+260%) |
| Layers | 3 | 4 |
| Compartments | 1 (implicit) | 2 (cytoplasm, mitochondria) |
| Source transitions | 0 | 2 (GlucoseUptake, O2_Diffusion) |
| Sink transitions | 0 | 2 (ATPase_Maintenance, ProteinDegradation) |
| Transport transitions | 0 | 2 (ATPase_Translocase, PyruvateCarrier) |
| Test arcs | 0 | 1 (Ca2+ regulation) |
| Preemption thresholds | 1 | 1 (same ATP threshold) |

## Files

- **Model**: `example5_energy_sensing.shy` (enhanced version)
- **Backup**: `example5_energy_sensing_simple_backup.shy` (original simple version)
- **Validation data** (to be generated): `example5.csv`
- **Thesis description**: `chapter_04_validation_examples.tex` (Section 4.5, to be updated)

## Next Steps

1. ✅ Model structure created
2. ⏳ Run simulation to generate validation data
3. ⏳ Analyze dynamics (preemption events, source/sink balance, compartment gradients)
4. ⏳ Update Chapter 4 Example 5 description with enhanced model details
5. ⏳ Add figures showing multi-compartment organization
6. ⏳ Compare simple vs enhanced Example 5 results
