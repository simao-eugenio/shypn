# Example 12: Oxidative Phosphorylation

## Biological Context

Oxidative phosphorylation is the final stage of cellular respiration, where the electron transport chain (ETC) oxidizes NADH and FADH₂ to generate a proton gradient across the inner mitochondrial membrane. This gradient drives ATP synthase to produce ATP, the cell's energy currency.

**Key Components**:
1. **Complex I** (NADH-CoQ reductase): NADH → NAD⁺ + CoQ (4 H⁺ pumped)
2. **Complex II** (Succinate-CoQ reductase): FADH₂ → FAD + CoQ (no protons pumped)
3. **Complex III** (CoQ-cytochrome c reductase): CoQH₂ → cytochrome c (4 H⁺ pumped)
4. **Complex IV** (Cytochrome c oxidase): Cytochrome c + O₂ → H₂O (2 H⁺ pumped)
5. **ATP Synthase** (Complex V): H⁺ gradient → ATP (3-4 H⁺ per ATP)

## Network Topology

**Places (13 metabolites)**:
- P1: NADH (substrate, 0.1 mM)
- P2: NAD⁺ (product, 2.0 mM)
- P3: CoQ (ubiquinone, oxidized, 1.0 mM)
- P4: CoQH₂ (ubiquinol, reduced, 0.1 mM)
- P5: Cytochrome c (oxidized, 0.5 mM)
- P6: Cytochrome c (reduced, 0.05 mM)
- P7: O₂ (oxygen, 0.2 mM)
- P8: H₂O (water, product)
- P9: H⁺ (matrix, pH 7.8)
- P10: H⁺ (intermembrane space, pH 7.0)
- P11: ADP (1.0 mM)
- P12: Pi (inorganic phosphate, 5.0 mM)
- P13: ATP (product, 3.0 mM)

**Transitions (5 reactions)**:
- T1: Complex I (NADH dehydrogenase)
- T2: Complex II (Succinate dehydrogenase) - optional for FADH₂ entry
- T3: Complex III (bc₁ complex)
- T4: Complex IV (Cytochrome c oxidase)
- T5: ATP Synthase (Complex V)

**Arc Topology**:
```
NADH → T1 → NAD⁺
       T1 → CoQH₂  (+ 4 H⁺ to IMS)
       
CoQH₂ → T3 → CoQ
        T3 → Cyt c (red)  (+ 4 H⁺ to IMS)
        
Cyt c (red) → T4 → Cyt c (ox)
O₂ → T4 → H₂O  (+ 2 H⁺ to IMS)

H⁺ (IMS) → T5 → H⁺ (matrix)
ADP + Pi → T5 → ATP
```

**Inhibitor Arcs**:
- ATP ⊣ T5 (product inhibition, Ki = 5.0 mM)

## Kinetic Parameters

### Complex I (T1)
- **Vmax**: 10.0 μM/s
- **Km(NADH)**: 0.02 mM (20 μM)
- **Km(CoQ)**: 0.05 mM (50 μM)
- **H⁺/2e⁻**: 4 protons pumped per NADH oxidized
- **Reference**: PMID: 15766527

### Complex III (T3)
- **Vmax**: 8.0 μM/s
- **Km(CoQH₂)**: 0.01 mM (10 μM)
- **Km(Cyt c ox)**: 0.01 mM (10 μM)
- **H⁺/2e⁻**: 4 protons pumped (Q cycle)
- **Reference**: PMID: 11290750

### Complex IV (T4)
- **Vmax**: 6.0 μM/s
- **Km(Cyt c red)**: 0.005 mM (5 μM)
- **Km(O₂)**: 0.001 mM (1 μM)
- **H⁺/2e⁻**: 2 protons pumped
- **Reference**: PMID: 12668659

### ATP Synthase (T5)
- **Vmax**: 5.0 μM/s
- **Km(ADP)**: 0.025 mM (25 μM)
- **Km(Pi)**: 0.5 mM (500 μM)
- **H⁺/ATP**: 3.33 protons per ATP (assuming 10 c-subunits)
- **Ki(ATP)**: 5.0 mM (5000 μM) - product inhibition
- **Reference**: PMID: 9662403

### Proton Gradient
- **ΔpH**: 0.8 units (matrix pH 7.8, IMS pH 7.0)
- **Membrane potential (Δψ)**: -150 mV
- **Proton-motive force (Δp)**: ~200 mV

## Rate Equations

### T1 (Complex I)
```
rate = 10.0 * (NADH/1000 / (0.02 + NADH/1000)) * (CoQ/1000 / (0.05 + CoQ/1000))
```

### T3 (Complex III)
```
rate = 8.0 * (CoQH2/1000 / (0.01 + CoQH2/1000)) * (Cyt_c_ox/1000 / (0.01 + Cyt_c_ox/1000))
```

### T4 (Complex IV)
```
rate = 6.0 * (Cyt_c_red/1000 / (0.005 + Cyt_c_red/1000)) * (O2/1000 / (0.001 + O2/1000))
```

### T5 (ATP Synthase)
```
rate = 5.0 * (ADP/1000 / (0.025 + ADP/1000)) * (Pi/1000 / (0.5 + Pi/1000)) * (H_IMS/1000 / (0.01 + H_IMS/1000))
```
(Product inhibition by ATP is handled via inhibitor arc)

## Expected Behavior

### P/O Ratio
- **NADH**: ~2.5 ATP per NADH (10 H⁺ pumped ÷ 4 H⁺ per ATP)
- **Theoretical**: 10 H⁺ (4+4+2) ÷ 3.33 H⁺/ATP = 3.0 ATP
- **Actual**: ~2.5 ATP (accounting for proton leak and ATP/ADP exchange)

### Respiratory States
1. **State 3** (active phosphorylation): High ADP, high O₂ consumption
2. **State 4** (resting): Low ADP, low O₂ consumption
3. **RCR** (Respiratory Control Ratio): State 3 / State 4 ≈ 5-10

### Time Evolution
- **0-10s**: Initial electron flow establishes gradient
- **10-30s**: ATP synthesis ramps up
- **30-60s**: Steady state achieved
- **Key observation**: Tight coupling between electron transport and ATP synthesis

### Validation Criteria
- NADH oxidation rate: 0.5-2.0 μM/s (State 3)
- ATP production rate: 1.0-5.0 μM/s (State 3)
- P/O ratio: 2.0-3.0
- Proton gradient: Maintained throughout simulation
- Respiratory control: RCR > 3

## Educational Objectives

1. **Electron Transport Chain**: Understand sequential electron transfer
2. **Chemiosmotic Coupling**: Proton gradient drives ATP synthesis
3. **Energy Transduction**: Chemical energy → electrochemical gradient → phosphorylation
4. **Respiratory Control**: ADP availability controls respiration rate
5. **Stoichiometry**: H⁺ pumping and ATP yield calculations

## SHYpn Features Demonstrated

- **Stoichiometric Coefficients**: Multiple H⁺ per electron pair
- **Coupled Reactions**: ETC creates gradient that drives ATP synthesis
- **Product Inhibition**: ATP ⊣ T5
- **Multi-step Pathways**: 4 complexes in series
- **Energy Conservation**: Efficiency analysis

## References

1. **Complex I Structure**: Sazanov & Hinchliffe (2006) PMID: 15766527
2. **Complex III Q-cycle**: Hunte et al. (2000) PMID: 11290750
3. **Complex IV Mechanism**: Yoshikawa et al. (2002) PMID: 12668659
4. **ATP Synthase**: Boyer (1997) PMID: 9662403
5. **Bioenergetics**: Nicholls & Ferguson (2013) "Bioenergetics 4"

## Notes

- This simplified model omits Complex II (succinate pathway)
- Proton concentrations are represented abstractly (not true H⁺ molarities)
- Membrane potential contribution to proton-motive force is implicit in rate equations
- For educational purposes, stoichiometry is slightly simplified
