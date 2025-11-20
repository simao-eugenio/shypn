# SHYpn Biochemical Examples - Progressive Learning Plan

**Target Domain**: Human Glycolysis Pathway
**Goal**: Demonstrate SHYpn's capabilities from simple reactions to complex regulatory mechanisms

## Overview

This plan presents a progressive series of biochemical examples, starting from basic chemical reactions with known kinetics and building up to sophisticated regulatory networks in human glycolysis. Each example introduces new modeling concepts while maintaining biological accuracy.

---

## Phase 1: Foundation - Simple Reactions (Examples 1-3)

### Example 1: Basic Irreversible Reaction
**Concept**: Simple substrate → product conversion
**Biological Context**: ATP hydrolysis

```
ATP --[ATPase]--> ADP + Pi
```

**Learning Objectives**:
- Single transition firing
- Mass action kinetics
- Conservation of matter

**Parameters** (known values):
- k_cat (ATPase) = 100 s⁻¹
- [ATP] initial = 3 mM (typical cellular)

**SHYpn Features Demonstrated**:
- Place (species)
- Transition (reaction)
- Arc (stoichiometry)
- Immediate behavior
- Token conservation

---

### Example 2: Reversible Reaction with Equilibrium
**Concept**: Bidirectional reaction reaching equilibrium
**Biological Context**: Phosphoglucose isomerase (Glycolysis step 2)

```
Glucose-6-phosphate ⇌ Fructose-6-phosphate
```

**Learning Objectives**:
- Forward and reverse reactions
- Equilibrium constant (Keq)
- Steady-state behavior

**Parameters** (human muscle):
- k_forward = 0.41 s⁻¹
- k_reverse = 0.14 s⁻¹
- Keq = 0.34 (favors G6P)

**SHYpn Features Demonstrated**:
- Bidirectional arcs
- Equilibrium analysis
- Continuous behavior
- Topology: reversibility detection

---

### Example 3: Michaelis-Menten Enzyme Kinetics
**Concept**: Saturable enzyme kinetics
**Biological Context**: Hexokinase (Glycolysis step 1)

```
Glucose + ATP --[Hexokinase]--> Glucose-6-phosphate + ADP
```

**Learning Objectives**:
- Enzyme saturation
- Km and Vmax parameters
- Substrate competition

**Parameters** (human hexokinase):
- Vmax = 0.124 mM/s
- Km(glucose) = 0.1 mM
- Km(ATP) = 0.4 mM
- [Glucose] initial = 5 mM (blood glucose)

**SHYpn Features Demonstrated**:
- Multiple substrates
- Michaelis-Menten rate law
- SBML kinetic law import
- Parameter estimation

---

## Phase 2: Regulation - Control Mechanisms (Examples 4-6)

### Example 4: Competitive Inhibition
**Concept**: Product inhibition
**Biological Context**: Glucose-6-phosphate inhibits Hexokinase

```
Glucose + ATP --[HK]--> G6P + ADP
                 ⊣ G6P (inhibitor)
```

**Learning Objectives**:
- Feedback inhibition
- Ki parameter
- Regulatory arc (TestArc)

**Parameters**:
- Ki(G6P) = 0.02 mM
- Inhibition type: competitive

**SHYpn Features Demonstrated**:
- Inhibitor arc (dashed line)
- TestArc (non-consuming)
- Catalyst arc representation
- Regulatory network visualization

---

### Example 5: Allosteric Activation
**Concept**: Cooperativity and activation
**Biological Context**: Phosphofructokinase-1 (PFK-1) - Key regulatory step

```
F6P + ATP --[PFK-1]--> F-1,6-BP + ADP
              ⊕ AMP (activator)
              ⊣ ATP (inhibitor)
              ⊣ Citrate (inhibitor)
```

**Learning Objectives**:
- Hill coefficient (cooperativity)
- Multiple regulatory inputs
- Allosteric site modeling

**Parameters** (human muscle PFK-1):
- Vmax = 0.094 mM/s
- Km(F6P) = 0.1 mM
- Hill coefficient = 2.5
- Ka(AMP) = 0.02 mM (activator)
- Ki(ATP) = 0.5 mM (high [ATP] inhibits)
- Ki(Citrate) = 0.1 mM

**SHYpn Features Demonstrated**:
- Multiple inhibitor arcs
- Activator arcs
- Hill equation rate law
- Complex regulatory logic
- Energy charge sensing (ATP/AMP ratio)

---

### Example 6: Substrate-Level Phosphorylation
**Concept**: Energy conservation - ATP generation
**Biological Context**: Phosphoglycerate kinase (Glycolysis step 7)

```
1,3-bisphosphoglycerate + ADP ⇌ 3-phosphoglycerate + ATP
```

**Learning Objectives**:
- Energy coupling
- Reversible ATP synthesis
- Thermodynamic driving force

**Parameters**:
- ΔG°' = -18.8 kJ/mol (highly favorable)
- Keq = 3200
- k_forward = 1.2 × 10³ M⁻¹s⁻¹
- k_reverse = 0.05 s⁻¹

**SHYpn Features Demonstrated**:
- Coupled reactions
- Energy flow tracking
- Thermodynamic analysis
- Net ATP production calculation

---

## Phase 3: Integration - Complete Pathways (Examples 7-9)

### Example 7: Mini-Pathway - Upper Glycolysis
**Concept**: Sequential reactions with shared intermediates
**Biological Context**: Glucose → Fructose-1,6-bisphosphate (3 steps)

```
Glucose → G6P → F6P → F-1,6-BP
  (HK)   (PGI)  (PFK)
```

**Learning Objectives**:
- Pathway connectivity
- Metabolite channeling
- Flux analysis

**Parameters**: Combined from Examples 1-5

**SHYpn Features Demonstrated**:
- Graph layout (hierarchical)
- Pathway topology analysis
- P-invariants (conservation laws)
- Deadlock detection
- Source/sink analysis

---

### Example 8: Regulatory Motif - ATP/AMP Energy Sensing
**Concept**: Coordinated regulation by energy charge
**Biological Context**: PFK-1 and Pyruvate Kinase co-regulation

```
         ⊕ AMP
         ⊣ ATP
          ↓
F6P → F-1,6-BP → ... → PEP → Pyruvate
(PFK-1)                 (PK)
                         ↑
                        ⊕ F-1,6-BP (feed-forward)
                        ⊣ ATP
```

**Learning Objectives**:
- Feed-forward activation
- Coordinated regulation
- Regulatory motif detection

**SHYpn Features Demonstrated**:
- Motif detection (feed-forward loop)
- Regulatory network analysis
- Energy charge calculation
- Multi-level control

---

### Example 9: Complete Glycolysis with Regulation
**Concept**: Full pathway with all 10 steps + regulation
**Biological Context**: Human erythrocyte glycolysis

**Components**:
- 10 enzymatic steps
- 3 irreversible steps (HK, PFK, PK)
- 7 reversible near-equilibrium steps
- Multiple regulatory points:
  - HK: inhibited by G6P
  - PFK-1: activated by AMP, F-2,6-BP; inhibited by ATP, citrate
  - PK: activated by F-1,6-BP; inhibited by ATP, alanine

**Learning Objectives**:
- Systems-level behavior
- Flux control coefficients
- Metabolic control analysis
- Oscillations and stability

**SHYpn Features Demonstrated**:
- KEGG pathway import
- SBML model import (e.g., BIOMD0000000064 - Glycolysis)
- Complete topology analysis
- Simulation modes:
  - Stochastic (low molecule numbers)
  - Continuous (ODE, high concentrations)
  - Hybrid (mixed)
- Viability analysis
- Regulatory network extraction
- Time-series analysis
- Parameter sensitivity

---

## Phase 4: Metabolic Integration (Examples 10-13)

### Example 10: Citric Acid Cycle (TCA Cycle)
**Concept**: Central metabolic hub with reversible reactions
**Biological Context**: Acetyl-CoA → CO₂ + NADH/FADH₂ (8 steps)

```
Acetyl-CoA + Oxaloacetate → Citrate → Isocitrate → α-Ketoglutarate
→ Succinyl-CoA → Succinate → Fumarate → Malate → Oxaloacetate
```

**Learning Objectives**:
- Cyclic pathways
- NAD⁺/NADH cycling
- Reversible vs. irreversible steps
- Multiple inhibitor arcs

**Parameters** (mitochondrial matrix):
- 8 enzymatic steps with literature kinetics
- Cofactor cycling (NAD⁺/NADH)
- Allosteric regulation by ATP, NADH

**SHYpn Features Demonstrated**:
- Cyclic topology
- Curved arcs for visual clarity
- Inhibitor arcs (5 regulatory points)
- Reversible transitions (ACO, FH)
- Complex rate expressions

**Status**: ✅ Implemented and tested

---

### Example 11: Glycolysis-TCA Connection
**Concept**: Pathway integration via pyruvate dehydrogenase
**Biological Context**: Glycolysis → Pyruvate → Acetyl-CoA → TCA

```
Glucose → ... → Pyruvate --[PDH]--> Acetyl-CoA → TCA Cycle
                              ↑
                              ⊣ (NADH, Acetyl-CoA)
```

**Learning Objectives**:
- Pathway connectivity
- Compartmentalization (cytosol → mitochondria)
- Pyruvate dehydrogenase complex regulation
- Metabolite transport

**SHYpn Features Demonstrated**:
- Inter-pathway connections
- Transport reactions
- Multi-step enzyme complexes
- Compartment boundaries (visual grouping)

**Status**: 🔄 Next to implement

---

### Example 12: Oxidative Phosphorylation
**Concept**: Electron transport chain + ATP synthase
**Biological Context**: NADH/FADH₂ → O₂ + H₂O → ATP

```
NADH → Complex I → CoQ → Complex III → Cytochrome c 
→ Complex IV → O₂ + H₂O

Proton gradient → ATP Synthase → ATP
```

**Learning Objectives**:
- Electron transport
- Chemiosmotic coupling
- P/O ratio
- Respiratory control

**SHYpn Features Demonstrated**:
- Coupled reactions (redox + phosphorylation)
- Stoichiometric coefficients (10 H⁺ per NADH)
- Energy transduction
- Inhibitor modeling (oligomycin, rotenone)

**Status**: 📋 Planned

---

### Example 13: Complete Cellular Respiration
**Concept**: Glucose → CO₂ + H₂O + 30-32 ATP
**Biological Context**: Glycolysis + TCA + OxPhos integrated

**Components**:
- Glycolysis (10 steps, cytosol)
- Pyruvate transport
- TCA cycle (8 steps, mitochondria)
- Electron transport chain (4 complexes)
- ATP synthase
- Cofactor shuttles (malate-aspartate, glycerol-3-phosphate)

**Learning Objectives**:
- Complete metabolic integration
- ATP yield calculation
- Respiratory control ratio
- Metabolic states (State 3, State 4)

**SHYpn Features Demonstrated**:
- Large-scale pathway modeling
- Multi-compartment simulation
- Flux balance analysis
- Metabolic control analysis
- Energy efficiency calculation

**Status**: 📋 Planned

---

## Phase 5: Advanced Regulation (Examples 14-16)

### Example 14: Pentose Phosphate Pathway
**Concept**: Branching pathway from glycolysis
**Biological Context**: G6P can enter PPP or continue glycolysis

```
        ┌─→ PPP (Oxidative) → NADPH + Ribose-5-P
Glucose─┤        (Non-oxidative) ⇌ Glycolytic intermediates
        └─→ Glycolysis → ATP + Pyruvate
```

**Learning Objectives**:
- Pathway branching and flux distribution
- NADPH production for biosynthesis
- Metabolic flexibility

**SHYpn Features Demonstrated**:
- Multi-pathway models
- Flux distribution analysis
- Pathway comparison
- Optimization (maximize NADPH vs. ATP)

**Status**: 📋 Planned

---

### Example 15: Gluconeogenesis
**Concept**: Reverse glycolysis with bypass reactions
**Biological Context**: Lactate/Amino acids → Glucose

```
Pyruvate --[PC + PEPCK]--> PEP → ... → F-1,6-BP --[FBPase]--> 
F6P → G6P --[G6Pase]--> Glucose
```

**Learning Objectives**:
- Reciprocal regulation (glycolysis vs. gluconeogenesis)
- Futile cycles prevention
- Hormonal control (insulin vs. glucagon)

**SHYpn Features Demonstrated**:
- Pathway antagonism
- Conditional activation/inhibition
- Metabolic switching
- Energy cost analysis

**Status**: 📋 Planned

---

### Example 16: Fed vs. Fasted Metabolic States
**Concept**: Global metabolic regulation by hormones
**Biological Context**: Insulin (anabolic) vs. Glucagon (catabolic)

```
Fed State (Insulin):
  ↑ Glucose uptake → ↑ Glycolysis → ↑ TCA → ↓ Gluconeogenesis

Fasted State (Glucagon):
  ↓ Glucose uptake → ↓ Glycolysis → ↓ TCA → ↑ Gluconeogenesis
```

**Learning Objectives**:
- Systems-level regulation
- Hormonal signal transduction
- Metabolic state transitions
- Enzyme phosphorylation cascades

**SHYpn Features Demonstrated**:
- Time-dependent parameter changes
- Boolean logic (AND/OR gates)
- State machines
- Dynamic pathway activation/deactivation

**Status**: 📋 Planned

---

## Implementation Strategy

### Directory Structure
```
workspace/projects/Biochemical-Examples/
├── 01_ATP_Hydrolysis/            [✅ Phase 1]
│   ├── model.shy
│   ├── README.md
│   └── parameters.json
├── 02_PGI_Equilibrium/           [✅ Phase 1]
├── 03_Hexokinase_MM/             [✅ Phase 1]
├── 04_Allosteric_Inhibition_PFK/ [✅ Phase 2]
├── 05_Competitive_Inhibition/    [✅ Phase 2]
├── 06_Feedback_Loop/             [✅ Phase 2]
├── 07_Upper_Glycolysis_Pathway/  [✅ Phase 3]
├── 08_Energy_Sensing_Motif/      [✅ Phase 3]
├── 09_Complete_Glycolysis/       [✅ Phase 3]
├── 10_Citric_Acid_Cycle/         [✅ Phase 4]
├── 11_Glycolysis_TCA_Connection/ [🔄 Phase 4 - Next]
├── 12_Oxidative_Phosphorylation/ [📋 Phase 4]
├── 13_Complete_Respiration/      [📋 Phase 4]
├── 14_Pentose_Phosphate_Pathway/ [📋 Phase 5]
├── 15_Gluconeogenesis/           [📋 Phase 5]
└── 16_Fed_Fasted_States/         [📋 Phase 5]
```

### Documentation for Each Example
- **README.md**: Biological background, learning objectives
- **model.shy**: SHYpn model file
- **parameters.json**: Kinetic parameters with literature references
- **validation.md**: Expected behavior, comparison with experimental data
- **tutorial.md**: Step-by-step modeling guide

### Testing Checklist
For each example:
- [ ] Model loads without errors
- [ ] Parameters are biologically realistic
- [ ] Simulation produces expected steady-state
- [ ] Topology analysis shows expected properties
- [ ] Regulatory logic is correct
- [ ] Documentation is complete

---

## Learning Path

**Beginner** (Examples 1-3):
- Basic Petri net concepts
- Simple kinetics
- Simulation basics

**Intermediate** (Examples 4-6):
- Regulatory mechanisms
- Complex rate laws
- Control analysis

**Advanced** (Examples 7-9):
- Complete pathways
- Systems analysis
- Model import/export

**Expert** (Examples 10-12):
- Multi-compartment systems
- Pathway integration
- Signal transduction

---

## Data Sources

### Kinetic Parameters
- **BRENDA**: Enzyme kinetics database
- **SABIO-RK**: Biochemical reactions and kinetics
- **BioModels**: SBML models (e.g., BIOMD0000000064 for glycolysis)

### Pathway Information
- **KEGG**: hsa00010 (Glycolysis / Gluconeogenesis)
- **Reactome**: R-HSA-70171 (Glycolysis)
- **MetaCyc**: Glycolysis pathways

### Literature References
- Berg et al., "Biochemistry" (8th ed.) - Standard textbook values
- Teusink et al. (2000) - Yeast glycolysis model (PMID: 10692304)
- Mulukutla et al. (2015) - Human cell glycolysis review (PMID: 26355030)

---

## Success Metrics

1. **Educational Value**: 
   - Each example teaches 2-3 new concepts
   - Progressive difficulty
   - Clear learning objectives

2. **Biological Accuracy**:
   - Parameters from literature
   - Physiologically realistic conditions
   - Validated against experimental data

3. **SHYpn Features Coverage**:
   - All major features demonstrated
   - Realistic use cases
   - Best practices illustrated

4. **Reproducibility**:
   - Complete documentation
   - Automated testing
   - Version controlled

---

## Timeline

- **Week 1-2**: Examples 1-3 (Foundation) ✅
- **Week 3-4**: Examples 4-6 (Regulation) ✅
- **Week 5-6**: Examples 7-9 (Integration) ✅
- **Week 7**: Example 10 (Citric Acid Cycle) ✅
- **Week 8-9**: Examples 11-13 (Metabolic Integration) 🔄
- **Week 10-11**: Examples 14-16 (Advanced Regulation) 📋
- **Week 12**: Documentation and comprehensive testing
- **Week 13**: Review, validation, and refinement

---

## Next Steps

1. Create project structure in workspace
2. Implement Example 1 (ATP Hydrolysis) as template
3. Develop parameter database
4. Create testing framework
5. Write tutorial documentation
6. Validate models against literature

---

**Document Version**: 1.0
**Date**: November 18, 2025
**Branch**: Foundation-Testing
