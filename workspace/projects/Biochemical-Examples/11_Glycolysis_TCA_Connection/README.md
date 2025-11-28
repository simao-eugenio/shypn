# Example 11: Glycolysis-TCA Connection via Pyruvate Dehydrogenase

## Overview

This example demonstrates the critical metabolic link between glycolysis and the citric acid cycle (TCA cycle) through the **pyruvate dehydrogenase (PDH) complex**. This connection represents the irreversible commitment of pyruvate to complete oxidation and is a major regulatory checkpoint in cellular metabolism.

## Biological Context

### The Pyruvate Dehydrogenase Complex

The PDH complex is one of the largest enzyme complexes in cells, consisting of three enzymatic components:
- **E1** (Pyruvate decarboxylase): TPP-dependent decarboxylation
- **E2** (Dihydrolipoyl transacetylase): Acetyl group transfer to CoA
- **E3** (Dihydrolipoyl dehydrogenase): NAD⁺ reduction

### Overall Reaction

```
Pyruvate + CoA + NAD⁺ → Acetyl-CoA + CO₂ + NADH + H⁺
```

**ΔG°'** = -33.4 kJ/mol (highly exergonic, essentially irreversible)

### Metabolic Significance

1. **Energy Production**: Links glycolysis to TCA cycle for complete glucose oxidation
2. **Regulatory Hub**: Controlled by product inhibition and covalent modification
3. **Compartmentalization**: Located in mitochondrial matrix
4. **Metabolic Switch**: Determines fate of pyruvate (oxidation vs. other pathways)

## Network Topology

### Places (Metabolites)

1. **P1 - Pyruvate** (cytosol): End product of glycolysis
2. **P2 - Pyruvate** (mitochondria): Transported form
3. **P3 - CoA**: Coenzyme A (cofactor)
4. **P4 - NAD⁺**: Oxidized nicotinamide cofactor
5. **P5 - Acetyl-CoA**: Product, enters TCA cycle
6. **P6 - CO₂**: Released (can be transported out)
7. **P7 - NADH**: Reduced cofactor (feeds ETC)
8. **P8 - Oxaloacetate**: TCA cycle component (from Example 10)
9. **P9 - Citrate**: First TCA intermediate

### Transitions (Reactions)

1. **T1 - Pyruvate Transport**: Carrier-mediated transport across mitochondrial membrane
2. **T2 - PDH Complex**: Pyruvate + CoA + NAD⁺ → Acetyl-CoA + CO₂ + NADH
3. **T3 - Citrate Synthase**: Acetyl-CoA + Oxaloacetate → Citrate (first TCA step)

### Regulatory Arcs

**Inhibitor Arcs** (Product Inhibition):
- **A10** (NADH ⊣ PDH): High NADH inhibits PDH
- **A11** (Acetyl-CoA ⊣ PDH): High Acetyl-CoA inhibits PDH

**Rationale**: When energy is abundant (high NADH) or acetyl-CoA accumulates, PDH is inhibited to prevent excessive fuel oxidation.

## Kinetic Parameters

### T1 - Pyruvate Transport (Mitochondrial Pyruvate Carrier - MPC)
- **Km(Pyruvate)** = 0.1 mM
- **Vmax** = 2.0 mM/s
- **Type**: Facilitated diffusion (driven by concentration gradient)

**Rate Expression**:
```
rate = 2.0 * (Pyruvate_cytosol / (0.1 + Pyruvate_cytosol))
```

### T2 - Pyruvate Dehydrogenase Complex
- **Km(Pyruvate)** = 0.025 mM
- **Km(CoA)** = 0.013 mM
- **Km(NAD⁺)** = 0.06 mM
- **Ki(NADH)** = 0.05 mM (competitive with NAD⁺)
- **Ki(Acetyl-CoA)** = 0.02 mM (competitive with CoA)
- **Vmax** = 0.5 mM/s

**Rate Expression** (with product inhibition):
```
rate = 0.5 * (Pyruvate / (0.025 + Pyruvate)) * 
            (CoA / (0.013 + CoA)) * 
            (NAD / (0.06 + NAD)) *
            (0.05 / (0.05 + NADH)) *
            (0.02 / (0.02 + AcetylCoA))
```

### T3 - Citrate Synthase
- **Km(Acetyl-CoA)** = 0.005 mM
- **Km(Oxaloacetate)** = 0.002 mM
- **Vmax** = 0.8 mM/s

**Rate Expression**:
```
rate = 0.8 * (AcetylCoA / (0.005 + AcetylCoA)) * 
            (Oxaloacetate / (0.002 + Oxaloacetate))
```

## Initial Conditions

Based on typical mitochondrial concentrations:

| Metabolite | Concentration | Rationale |
|------------|---------------|-----------|
| Pyruvate (cytosol) | 0.5 mM | From glycolysis steady-state |
| Pyruvate (mito) | 0.1 mM | Lower due to rapid oxidation |
| CoA | 1.0 mM | Abundant cofactor pool |
| NAD⁺ | 2.0 mM | High matrix concentration |
| Acetyl-CoA | 0.05 mM | Low initial, accumulates |
| CO₂ | 0.0 mM | Starts at zero, released |
| NADH | 0.1 mM | NAD⁺/NADH ratio ~20:1 |
| Oxaloacetate | 0.02 mM | Rate-limiting TCA intermediate |
| Citrate | 0.0 mM | Will be produced |

## Expected Behavior

### Steady-State Flux
- **Pyruvate consumption**: ~0.3-0.5 mM/s
- **Acetyl-CoA production**: Matches pyruvate consumption
- **NADH production**: 1:1 with Acetyl-CoA
- **Citrate production**: Limited by oxaloacetate availability

### Regulatory Response

1. **High NADH**: PDH flux decreases due to inhibitor arc A10
2. **High Acetyl-CoA**: PDH flux decreases due to inhibitor arc A11
3. **Low Oxaloacetate**: Acetyl-CoA accumulates, further inhibiting PDH

### Time Course (0-10 seconds)
- **Phase 1** (0-2s): Rapid acetyl-CoA production
- **Phase 2** (2-5s): NADH accumulation begins inhibiting PDH
- **Phase 3** (5-10s): System approaches steady-state with balanced fluxes

## Learning Objectives

1. **Pathway Integration**: Understand how glycolysis connects to TCA cycle
2. **Compartmentalization**: Model cytosolic vs. mitochondrial metabolites
3. **Product Inhibition**: Observe feedback regulation by NADH and Acetyl-CoA
4. **Metabolic Control**: See how one reaction (PDH) controls entire pathway flux
5. **Irreversibility**: ΔG°' = -33 kJ/mol makes this a committed step

## SHYpn Features Demonstrated

- **Transport Reactions**: Pyruvate carrier across membranes
- **Multi-substrate Kinetics**: 3 substrates, 3 products
- **Inhibitor Arcs**: Product feedback (NADH, Acetyl-CoA)
- **Pathway Connection**: Linking two complete pathways
- **Complex Rate Laws**: Competitive inhibition terms
- **Physiological Scaling**: Realistic mitochondrial concentrations

## Validation

### Literature Values
- PDH flux in heart mitochondria: 0.2-0.4 μmol/min/mg protein
- NADH/NAD⁺ ratio control: 2-10 fold inhibition
- Acetyl-CoA inhibition: IC₅₀ ~20 μM

### Expected Results
- ✅ Acetyl-CoA accumulates to ~0.1-0.2 mM at steady-state
- ✅ NADH increases to ~0.3-0.5 mM
- ✅ PDH flux reduced by 50-70% due to product inhibition
- ✅ Citrate production rate matches acetyl-CoA availability

## References

1. Patel MS, Korotchkina LG (2006). "Regulation of the pyruvate dehydrogenase complex." *Biochem Soc Trans* 34(2):217-22. PMID: 16545080
2. Bricker DK et al. (2012). "A mitochondrial pyruvate carrier required for pyruvate uptake in yeast, Drosophila, and humans." *Science* 337(6090):96-100. PMID: 22628558
3. Berg JM, Tymoczko JL, Stryer L (2012). "Biochemistry" 7th edition, Chapter 17: The Citric Acid Cycle
4. Hansford RG (1980). "Control of mitochondrial substrate oxidation." *Curr Top Bioenerg* 10:217-78

## Extensions

### Phase 4 Complete
- Add full TCA cycle (from Example 10)
- Add electron transport chain
- Model complete ATP synthesis

### Phase 5 
- Add pyruvate carboxylase (anaplerotic reaction)
- Include PDH kinase/phosphatase (covalent regulation)
- Model calcium activation of PDH

---

**Status**: 🔄 In Development  
**Phase**: 4 - Metabolic Integration  
**Complexity**: Intermediate-Advanced  
**Prerequisites**: Examples 9 (Glycolysis), 10 (TCA Cycle)
