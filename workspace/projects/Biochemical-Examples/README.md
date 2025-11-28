# Biochemical Examples - Progressive Learning Series

This project contains a series of progressively complex biochemical examples demonstrating SHYpn's capabilities in modeling human glycolysis and its regulatory mechanisms.

## Organization

### Phase 1: Foundation - Simple Reactions
- **01_ATP_Hydrolysis**: Basic irreversible reaction
- **02_PGI_Equilibrium**: Reversible reaction with equilibrium
- **03_Hexokinase_MM**: Michaelis-Menten enzyme kinetics

### Phase 2: Regulation Mechanisms
- **04_Allosteric_Inhibition_PFK**: Phosphofructokinase with ATP feedback
- **05_Competitive_Inhibition**: Succinate dehydrogenase with malonate
- **06_Feedback_Loop**: Threonine to isoleucine pathway

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

For complete plan details, see: `doc/foundation/BIOCHEMICAL_EXAMPLES_PLAN.md`

---
**Project Status**: Phase 1 complete, Phase 2 complete
**Last Updated**: November 18, 2025
