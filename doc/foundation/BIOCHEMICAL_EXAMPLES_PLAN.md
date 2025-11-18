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

## Phase 4: Advanced Topics (Examples 10-12)

### Example 10: Compartmentalization
**Concept**: Cytosol vs. Mitochondria
**Biological Context**: Glycolysis (cytosol) → TCA cycle (mitochondria)

```
Glucose (cytosol) → Pyruvate (cytosol) 
                      ↓ [transport]
                    Pyruvate (mitochondria) → Acetyl-CoA
```

**SHYpn Features Demonstrated**:
- Compartment modeling
- Transport reactions
- Place coloring by compartment
- Spatial organization

---

### Example 11: Crosstalk with Pentose Phosphate Pathway
**Concept**: Branching pathways
**Biological Context**: G6P can enter PPP or glycolysis

```
        ┌─→ PPP → NADPH + Ribose-5-P
Glucose─┤
        └─→ Glycolysis → ATP + Pyruvate
```

**SHYpn Features Demonstrated**:
- Pathway branching
- Flux distribution
- Multi-objective optimization
- Pathway comparison

---

### Example 12: Hormonal Regulation
**Concept**: External signals affecting pathway
**Biological Context**: Insulin stimulates glucose uptake and glycolysis

```
Insulin → [GLUT4 translocation] → ↑ Glucose uptake
       → [PFK-2 activation] → ↑ F-2,6-BP → ⊕ PFK-1
```

**SHYpn Features Demonstrated**:
- Signal transduction
- Time-dependent parameters
- Switching behavior
- Logical regulation (Boolean)

---

## Implementation Strategy

### Directory Structure
```
workspace/projects/Biochemical-Examples/
├── 01_ATP_Hydrolysis/
│   ├── model.shy
│   ├── README.md
│   └── parameters.json
├── 02_PGI_Equilibrium/
├── 03_Hexokinase_MM/
├── 04_G6P_Inhibition/
├── 05_PFK_Allosteric/
├── 06_PGK_Coupling/
├── 07_Upper_Glycolysis/
├── 08_Energy_Sensing/
├── 09_Complete_Glycolysis/
├── 10_Compartments/
├── 11_PPP_Crosstalk/
└── 12_Hormonal_Control/
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

- **Week 1-2**: Examples 1-3 (Foundation)
- **Week 3-4**: Examples 4-6 (Regulation)
- **Week 5-6**: Examples 7-9 (Integration)
- **Week 7-8**: Examples 10-12 (Advanced)
- **Week 9**: Documentation and testing
- **Week 10**: Review and refinement

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
