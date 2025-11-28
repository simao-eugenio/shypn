# Example 10: Citric Acid Cycle (Krebs Cycle)

## Overview
Complete model of the citric acid cycle (Krebs cycle/TCA cycle), the central metabolic pathway that oxidizes acetyl-CoA to produce NADH and regenerate oxaloacetate.

## Biological Context
The citric acid cycle is the hub of cellular metabolism, connecting glycolysis to oxidative phosphorylation. It:
- Oxidizes acetyl-CoA (from pyruvate, fatty acids, amino acids)
- Produces 3 NADH per turn
- Regenerates oxaloacetate to continue the cycle
- Features multiple regulatory feedback mechanisms

## Model Features

### Metabolites (Places)
1. **P1 - Acetyl-CoA** (0.5 mM): Entry point from glycolysis/β-oxidation
2. **P2 - Citrate** (0.3 mM): 6-carbon intermediate
3. **P3 - Isocitrate** (0.1 mM): Isomer of citrate
4. **P4 - α-Ketoglutarate** (0.2 mM): 5-carbon intermediate
5. **P5 - Succinyl-CoA** (0.05 mM): High-energy intermediate
6. **P6 - Succinate** (0.4 mM): 4-carbon intermediate
7. **P7 - Fumarate** (0.15 mM): Unsaturated intermediate
8. **P8 - Malate** (0.25 mM): Final 4-carbon intermediate
9. **P9 - Oxaloacetate** (0.02 mM): Cycle regeneration (very low concentration)
10. **P10 - NAD⁺** (2.0 mM): Oxidizing cofactor pool
11. **P11 - NADH** (0.1 mM): Reduced cofactor pool

### Enzymes (Transitions)
1. **T1 - Citrate Synthase (CS)**: Acetyl-CoA + Oxaloacetate → Citrate
   - Rate: `1.5 * AcetylCoA * Oxaloacetate`
   - Key regulation point

2. **T2 - Aconitase (ACO)**: Citrate ⇌ Isocitrate
   - Reversible: forward `0.4 * Citrate`, reverse `0.2 * Isocitrate`
   - Near-equilibrium reaction

3. **T3 - Isocitrate Dehydrogenase (IDH)**: Isocitrate + NAD⁺ → α-KG + NADH
   - Rate: `0.8 * Isocitrate * NAD`
   - First NADH production
   - Rate-limiting step

4. **T4 - α-Ketoglutarate Dehydrogenase (KGDH)**: α-KG + NAD⁺ → Succinyl-CoA + NADH
   - Rate: `0.6 * AlphaKG * NAD`
   - Second NADH production
   - Irreversible, highly regulated

5. **T5 - Succinyl-CoA Synthetase (SCS)**: Succinyl-CoA → Succinate
   - Rate: `1.0 * SuccinylCoA`
   - GTP production (not modeled)

6. **T6 - Succinate Dehydrogenase (SDH)**: Succinate → Fumarate
   - Rate: `0.5 * Succinate`
   - FAD reduction (not modeled)

7. **T7 - Fumarase (FH)**: Fumarate ⇌ Malate
   - Reversible: forward `0.6 * Fumarate`, reverse `0.3 * Malate`
   - Near-equilibrium

8. **T8 - Malate Dehydrogenase (MDH)**: Malate + NAD⁺ → Oxaloacetate + NADH
   - Rate: `0.7 * Malate * NAD`
   - Third NADH production
   - Regenerates oxaloacetate

### Regulatory Mechanisms (Inhibitor Arcs)

1. **A28: NADH → IDH** (weight=1.5)
   - Product inhibition of isocitrate dehydrogenase
   - When NADH > 1.5 mM, IDH is blocked

2. **A29: NADH → KGDH** (weight=1.8)
   - Product inhibition of α-ketoglutarate dehydrogenase
   - When NADH > 1.8 mM, KGDH is blocked

3. **A30: Citrate → CS** (weight=2.5)
   - Product inhibition of citrate synthase
   - When citrate > 2.5 mM, CS is blocked
   - Prevents citrate accumulation

4. **A31: Succinyl-CoA → KGDH** (weight=0.15)
   - Product inhibition of KGDH
   - When succinyl-CoA > 0.15 mM, KGDH is blocked
   - Prevents succinyl-CoA accumulation

5. **A32: Succinate → KGDH** (weight=3.0)
   - Competitive inhibition by downstream product
   - When succinate > 3.0 mM, KGDH is blocked

## Key Dynamics

### Cycle Operation
- **Input**: Acetyl-CoA (from pyruvate via PDH complex)
- **Output**: 3 NADH per cycle turn
- **Regeneration**: Oxaloacetate is regenerated to accept next acetyl-CoA
- **Bottleneck**: Very low oxaloacetate concentration (0.02 mM)

### Reversible Steps
Two near-equilibrium reactions:
1. **Aconitase** (Citrate ⇌ Isocitrate)
2. **Fumarase** (Fumarate ⇌ Malate)

### Rate-Limiting Steps
1. **Isocitrate Dehydrogenase (IDH)** - heavily regulated
2. **α-Ketoglutarate Dehydrogenase (KGDH)** - multiple inhibitors

### Energy Sensing
- High NADH/NAD⁺ ratio slows down IDH and KGDH
- Prevents wasteful oxidation when energy is abundant
- Allows cycle to respond to cellular energy state

## Simulation Behavior

### Expected Patterns
1. **NADH accumulation**: NAD⁺ → NADH conversion over time
2. **Cycle slowing**: As NADH rises, inhibition kicks in
3. **Intermediate oscillations**: Some metabolites may oscillate
4. **Oxaloacetate depletion**: Critical limitation if not replenished

### Regulatory Effects
- Start with balanced NAD⁺/NADH ratio (2.0/0.1 mM)
- Watch IDH slow down as NADH approaches 1.5 mM
- Observe KGDH inhibition at higher NADH (>1.8 mM)
- Citrate feedback prevents excessive accumulation

## Biological Significance

### Metabolic Integration
- **Glycolysis connection**: Pyruvate → Acetyl-CoA → Cycle
- **Fatty acid connection**: β-oxidation → Acetyl-CoA
- **Amino acid connection**: Multiple entry points
- **Gluconeogenesis**: Oxaloacetate can exit for glucose synthesis

### ATP Production
While this model focuses on NADH production, the full cycle produces:
- 3 NADH → 7.5 ATP (via electron transport chain)
- 1 FADH₂ → 1.5 ATP (not modeled)
- 1 GTP → 1 ATP (not modeled)
- **Total**: ~10 ATP per acetyl-CoA

### Disease Relevance
- **Cancer metabolism**: Warburg effect bypasses cycle
- **Mitochondrial diseases**: Cycle enzyme deficiencies
- **Diabetes**: Altered cycle flux in insulin resistance
- **Neurodegenerative diseases**: Reduced cycle activity

## Learning Objectives
1. Understand cyclic metabolic pathway structure
2. Observe how product inhibition regulates flux
3. See importance of cofactor balance (NAD⁺/NADH)
4. Appreciate why oxaloacetate is catalytic (very low concentration)
5. Recognize multiple feedback control points

## Simulation Tips
- Run for 10-20 time units to see full dynamics
- Watch how NADH accumulation slows the cycle
- Observe which intermediates accumulate vs deplete
- Try varying initial NAD⁺/NADH ratio
- See effect of removing individual inhibitor arcs

## References
- Berg, Tymoczko, Stryer: "Biochemistry" (Chapter on Citric Acid Cycle)
- Alberts et al.: "Molecular Biology of the Cell" (Energy Metabolism)
- Voet & Voet: "Biochemistry" (Metabolic Pathways)
