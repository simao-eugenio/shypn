# Example 13: Complete Cellular Respiration

## Overview
**Complete metabolic integration**: This example combines glycolysis, citric acid cycle (TCA), and oxidative phosphorylation into a single comprehensive model representing the complete oxidation of glucose to CO₂ and H₂O with ATP production.

**Biological significance**: Cellular respiration is the fundamental energy-generating process in aerobic organisms, converting chemical energy from glucose into ATP with approximately 32 ATP molecules produced per glucose molecule (theoretical maximum: 38 ATP).

**Overall reaction**:
```
C₆H₁₂O₆ + 6 O₂ + ~32 ADP + ~32 Pi → 6 CO₂ + 6 H₂O + ~32 ATP
```

---

## Network Structure

### Compartments
1. **Cytosol**: Glycolysis pathway (10 reactions)
2. **Mitochondrial Matrix**: TCA cycle (8 reactions), NADH production
3. **Inner Membrane**: Electron transport chain (4 complexes) + ATP synthase

### Key Pathway Stages

#### Stage 1: Glycolysis (Cytosol)
```
Glucose → G6P → F6P → F1,6BP → DHAP/G3P → 1,3BPG → 3PG → 2PG → PEP → Pyruvate
```
- **Net yield**: 2 ATP, 2 NADH, 2 Pyruvate
- **Regulation**: PFK inhibited by ATP, activated by AMP

#### Stage 2: Pyruvate Oxidation (Mitochondrial Matrix)
```
Pyruvate + CoA + NAD⁺ → Acetyl-CoA + CO₂ + NADH
```
- **Enzyme**: Pyruvate Dehydrogenase Complex (PDH)
- **Regulation**: Product inhibition by NADH and Acetyl-CoA
- **Yield**: 2 NADH per glucose (2 pyruvate molecules)

#### Stage 3: Citric Acid Cycle (Mitochondrial Matrix)
```
Acetyl-CoA + 3 NAD⁺ + FAD + GDP + Pi → 2 CO₂ + 3 NADH + FADH₂ + GTP + CoA
```
- **Per glucose**: 2 turns × (3 NADH + 1 FADH₂ + 1 GTP) = 6 NADH + 2 FADH₂ + 2 GTP
- **Regulation**: Isocitrate dehydrogenase (NADH feedback), α-ketoglutarate dehydrogenase

#### Stage 4: Oxidative Phosphorylation (Inner Membrane)
```
NADH → Complex I → CoQ → Complex III → Cyt c → Complex IV → O₂
Proton gradient → ATP Synthase → ATP
```
- **Per NADH**: ~2.5 ATP (P/O ratio = 2.5)
- **Per FADH₂**: ~1.5 ATP (enters at CoQ, bypasses Complex I)
- **Total oxidative ATP**: 10 NADH × 2.5 + 2 FADH₂ × 1.5 = 28 ATP

### ATP Balance
| Source | Yield |
|--------|-------|
| Glycolysis (substrate-level) | 2 ATP |
| Glycolysis NADH (2 × 2.5) | 5 ATP |
| Pyruvate → Acetyl-CoA (2 × 2.5) | 5 ATP |
| TCA GTP (2) | 2 ATP |
| TCA NADH (6 × 2.5) | 15 ATP |
| TCA FADH₂ (2 × 1.5) | 3 ATP |
| **Total** | **32 ATP** |

---

## Metabolic States

### State 3 (Phosphorylating)
- **Condition**: High ADP, high Pi, high O₂
- **Characteristics**: Maximum respiration rate, ATP synthesis active
- **RCR = State 3 / State 4**: Typically 5-10 for healthy mitochondria

### State 4 (Resting)
- **Condition**: Low ADP (ATP saturated)
- **Characteristics**: Minimal respiration, proton leak dominant
- **Regulation**: ATP product inhibition of ATP synthase

---

## Regulatory Control Points

### 1. Phosphofructokinase (PFK) - Glycolysis
- **Inhibitors**: ATP (Ki = 0.5 mM), Citrate (feedforward from TCA)
- **Activators**: AMP, ADP (low energy signals)
- **Function**: Master switch for glycolysis rate

### 2. Pyruvate Dehydrogenase (PDH) - Entry to TCA
- **Inhibitors**: NADH (Ki = 50 μM), Acetyl-CoA (Ki = 20 μM)
- **Function**: Prevents TCA overload when energy-rich

### 3. Isocitrate Dehydrogenase (IDH) - TCA Cycle
- **Inhibitor**: NADH (product inhibition)
- **Activator**: ADP (low energy signal)
- **Function**: TCA cycle flux control

### 4. ATP Synthase - Oxidative Phosphorylation
- **Inhibitor**: ATP (Ki = 5 mM)
- **Function**: Prevents excessive proton gradient collapse

---

## Kinetic Parameters

### Glycolysis Enzymes
| Enzyme | Vmax (μM/s) | Km (mM) | References |
|--------|-------------|---------|------------|
| Hexokinase | 5.0 | G6P: 0.1 | PMID: 7043200 |
| PFK | 8.0 | F6P: 0.1, ATP: 0.5 | PMID: 6323425 |
| GAPDH | 12.0 | G3P: 0.05, NAD: 0.5 | PMID: 3304141 |
| PK | 10.0 | PEP: 0.05, ADP: 0.3 | PMID: 6879507 |

### TCA Cycle Enzymes
| Enzyme | Vmax (μM/s) | Km (mM) | References |
|--------|-------------|---------|------------|
| Citrate Synthase | 6.0 | AcCoA: 0.01, OAA: 0.001 | PMID: 6091749 |
| IDH | 8.0 | Isocitrate: 0.05, NAD: 0.5 | PMID: 7390975 |
| α-KGDH | 6.0 | α-KG: 0.1, NAD: 0.5, CoA: 0.02 | PMID: 6325444 |
| SDH | 5.0 | Succinate: 0.5, FAD: 0.01 | PMID: 3304142 |

### Electron Transport Chain
| Complex | Vmax (μM/s) | Km (mM) | H⁺ Pumped | References |
|---------|-------------|---------|-----------|------------|
| Complex I | 10.0 | NADH: 0.02, CoQ: 0.05 | 4 | PMID: 15522862 |
| Complex III | 8.0 | CoQH₂: 0.01, Cyt c: 0.01 | 4 | PMID: 16039586 |
| Complex IV | 6.0 | Cyt c: 0.005, O₂: 0.001 | 2 | PMID: 17310251 |
| ATP Synthase | 5.0 | ADP: 0.025, Pi: 0.5 | -3.33 | PMID: 15866414 |

---

## Model Features

### Network Topology
- **Total Places**: ~35-40 (metabolites across 3 compartments)
- **Total Transitions**: ~25-30 (all enzymatic reactions)
- **Total Arcs**: ~80-100 (substrates, products, inhibitors)

### Demonstrated Concepts
1. **Multi-compartment modeling**: Cytosol vs. mitochondria
2. **Pathway integration**: Sequential coupling of glycolysis → TCA → OxPhos
3. **Cofactor recycling**: NAD⁺/NADH, FAD/FADH₂, ADP/ATP cycling
4. **Respiratory control**: State 3/State 4 transitions
5. **Metabolic flux**: Tracking carbon flow (C6 → C3 → C2 → CO₂)
6. **Energy efficiency**: ATP/glucose ratio calculation

### Validation Criteria
- **Glucose consumption rate**: Should match O₂ consumption (respiratory quotient RQ ≈ 1.0)
- **ATP/O ratio**: ~2.5 for NADH, ~1.5 for FADH₂
- **Steady-state metabolite levels**: Should match experimental values (Berg et al., Biochemistry, 2015)
- **Respiratory control ratio**: State 3/State 4 ≈ 5-10

---

## Educational Value

### For Students
- See complete picture of cellular energy metabolism
- Understand cofactor coupling between pathways
- Learn regulatory principles at multiple levels
- Calculate theoretical vs. actual ATP yields

### For Researchers
- Template for large-scale metabolic modeling
- Framework for disease modeling (mitochondrial disorders)
- Platform for drug effect simulation (ETC inhibitors)
- Basis for metabolic engineering studies

---

## Simplified Model Scope

**Note**: This example presents a simplified version focusing on the core metabolic flow:
- Glycolysis: Key regulatory steps (HK, PFK, PK) + NADH production (GAPDH)
- TCA: Complete 8-step cycle with all cofactor production
- OxPhos: 4 ETC complexes + ATP synthase with realistic stoichiometry

**Omitted for clarity**:
- Cofactor shuttles (malate-aspartate, glycerol-3-phosphate)
- Detailed transport reactions (pyruvate carrier, adenine nucleotide translocator)
- Alternative substrates (fatty acids, amino acids)
- Additional regulatory mechanisms (allosteric modifiers, covalent modifications)

These can be added in advanced versions or specialized examples.

---

## References

1. **Berg JM, et al.** (2015) *Biochemistry*, 8th ed. W.H. Freeman. ISBN: 978-1464126109
2. **Nelson DL & Cox MM** (2017) *Lehninger Principles of Biochemistry*, 7th ed. W.H. Freeman. ISBN: 978-1464126116
3. **Nicholls DG & Ferguson SJ** (2013) *Bioenergetics 4*. Academic Press. ISBN: 978-0123884251
4. **Fell DA** (1997) *Understanding the Control of Metabolism*. Portland Press. ISBN: 978-1855781252
5. **BRENDA Enzyme Database**: https://www.brenda-enzymes.org/

---

## Usage Instructions

1. **Load model**: Open `model.shy` in SHYpn
2. **Set simulation time**: 100-200 seconds for steady-state
3. **Monitor key metabolites**: 
   - Glucose consumption
   - ATP/ADP ratio
   - NADH/NAD⁺ ratio
   - CO₂ production
   - O₂ consumption
4. **Analyze respiratory control**:
   - High ADP → State 3 (fast respiration)
   - Low ADP → State 4 (slow respiration)
5. **Calculate ATP yield**: Track ATP production from t=0 to steady-state

---

**Model Status**: 🔄 Implementation in progress
**Complexity**: ⭐⭐⭐⭐⭐ Advanced (Complete pathway integration)
**Prerequisites**: Examples 9 (Glycolysis), 10 (TCA), 12 (OxPhos)
