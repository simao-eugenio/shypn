# Biochemical Examples - Progressive Learning Series

This project contains a series of progressively complex biochemical examples demonstrating SHYpn's capabilities in modeling human glycolysis and its regulatory mechanisms, as well as advanced cell communication systems.

**Theoretical Foundation:** [arXiv:2512.17106](https://arxiv.org/abs/2512.17106) - *Weak Independence and Coupled Parallelism in Biological Petri Nets*

## Organization

### Phase 1: Foundation - Simple Reactions
- **01_ATP_Hydrolysis**: Basic irreversible reaction
- **02_PGI_Equilibrium**: Reversible reaction with equilibrium
- **03_Hexokinase_MM**: Michaelis-Menten enzyme kinetics

### Phase 2: Regulation Mechanisms
- **04_Allosteric_Inhibition_PFK**: Phosphofructokinase with ATP feedback
- **05_Competitive_Inhibition**: Succinate dehydrogenase with malonate
- **06_Feedback_Loop**: Threonine to isoleucine pathway

### Phase 3: Pathway Integration
- **07_Upper_Glycolysis_Pathway**: First 5 reactions of glycolysis
- **08_Energy_Sensing_Motif**: ATP/AMP ratio regulation
- **09_Complete_Glycolysis**: Full glucose to pyruvate pathway
- **10_Citric_Acid_Cycle**: TCA cycle (Krebs cycle)
- **11_Glycolysis_TCA_Connection**: Integration of glycolysis and TCA
- **12_Oxidative_Phosphorylation**: Electron transport chain
- **13_Complete_Cellular_Respiration**: Full glucose catabolism
- **14_Glycogen_Metabolism**: Glycogen synthesis and breakdown
- **15_Enzyme_Competition**: Multiple substrates competing for enzymes
- **16_Dynamic_Threshold_PFK**: Dynamic regulation of glycolysis

### Phase 4: Gene Regulation & Advanced Systems
- **17_Lac_Operon_Regulation**: Bacterial gene regulation (lac operon)
- **18_Simple_Gene_Expression**: Basic transcription-translation model
- **19_Bacterial_Quorum_Sensing**: *V. fischeri* cell communication (13-tuple Bio-PN)
- **20_Mammalian_Paracrine_Signaling**: T cell IL-2 immune coordination (13-tuple Bio-PN)

### Phase 5: Hybrid & Complex Systems
- **21_Hybrid_Glucose_Insulin**: Continuous-discrete glucose-insulin dynamics
- **22_Lambda_Phage_Switch**: Bacteriophage genetic switch

### How to Use

1. Start with Example 01 and progress sequentially
2. Each directory contains:
   - `README.md`: Biological background and learning objectives
   - `model.shy`: SHYpn model file
   - `parameters.json`: Kinetic parameters with references
   - `validation.md`: Expected behavior and validation

3. Open models in SHYpn and explore:
   - Network topology
   - Simulation behavior
   - Parameter effects
   - Regulatory mechanisms

### Learning Path

**Beginner**: Start with examples 1-3 to learn basic Petri net concepts and simple kinetics.

**Intermediate**: Progress to examples 4-6 to understand regulatory mechanisms:
- Allosteric inhibition (inhibitor arcs)
- Competitive inhibition (shared catalysts)
- Feedback loops (pathway regulation)

**Advanced**: Explore examples 7-18 for pathway integration and gene regulation:
- Complete metabolic pathways (glycolysis, TCA, respiration)
- Energy sensing and dynamic regulation
- Gene expression and transcriptional control

**Expert**: Study examples 19-22 for cutting-edge modeling:
- **Quorum sensing** (examples 19-20): 13-tuple Bio-PN formalism with signal places (Ψ)
  - Bacterial cell-to-cell communication
  - Mammalian paracrine signaling (immune system)
- **Hybrid systems** (example 21): Continuous-discrete dynamics
- **Genetic switches** (example 22): Bistable systems

### Special Features

#### Examples 19 & 20: Quorum Sensing (13-Tuple Bio-PN)
These examples demonstrate the **signal place** (Ψ) extension to Bio-Petri nets:
- Automatic detection of environment-sensing transitions
- Cross-kingdom applicability (bacteria, mammals, plants, fungi)
- Validated against experimental data

For quorum sensing documentation, see: `doc/quorum_sensing/README.md`

For complete plan details, see: `doc/foundation/BIOCHEMICAL_EXAMPLES_PLAN.md`

---
**Project Status**: Phases 1-4 complete, Phase 5 partial
**Last Updated**: December 18, 2025
