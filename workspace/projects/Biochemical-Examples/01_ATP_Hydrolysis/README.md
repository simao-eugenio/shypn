# Example 1: ATP Hydrolysis - Basic Irreversible Reaction

## Biological Context

ATP (adenosine triphosphate) hydrolysis is one of the most fundamental reactions in cellular biochemistry. It represents the "energy currency" of the cell being spent to perform work. This reaction is catalyzed by various ATPases throughout the cell.

**Reaction**:
```
ATP + H₂O → ADP + Pi + Energy
```

In this simplified model, we focus on the core transformation without explicitly modeling water.

## Learning Objectives

1. **Single transition firing**: Understand how a transition represents a chemical reaction
2. **Mass action kinetics**: Learn basic rate laws
3. **Token conservation**: Verify that matter is conserved in the network
4. **Immediate vs. continuous behavior**: Compare discrete and continuous simulation modes

## Biochemical Parameters

### Enzyme: ATPase (generic)
- **k_cat**: 100 s⁻¹ (turnover number)
- **Initial [ATP]**: 3 mM (typical cellular concentration)
- **Initial [ADP]**: 0.1 mM
- **Initial [Pi]**: 1 mM

### Thermodynamics
- **ΔG°'**: -30.5 kJ/mol (standard free energy)
- **ΔG** (cellular): ~-50 kJ/mol (highly favorable, essentially irreversible)

## Model Structure

### Places (Species)
1. **ATP**: Substrate (initial: 3000 tokens = 3 mM)
2. **ADP**: Product (initial: 100 tokens = 0.1 mM)
3. **Pi**: Product (initial: 1000 tokens = 1 mM)

### Transitions (Reactions)
1. **ATPase**: Catalyzes ATP → ADP + Pi
   - Rate law: k_cat × [ATP]
   - Stochastic rate: k_cat (when using molecular counts)

### Arcs (Stoichiometry)
- ATP → ATPase (stoichiometry: 1)
- ATPase → ADP (stoichiometry: 1)
- ATPase → Pi (stoichiometry: 1)

## Expected Behavior

### Immediate Mode (Token-based)
- Each firing consumes 1 ATP token
- Produces 1 ADP token and 1 Pi token
- Discrete step-by-step behavior
- Firing stops when ATP = 0

### Continuous Mode (Concentration-based)
- Exponential decay of [ATP]
- Exponential rise of [ADP] and [Pi]
- Smooth curves
- Approaches equilibrium (complete conversion)

### Conservation Law
At all times: **[ATP] + [ADP] = 3.1 mM** (constant total adenylate pool)

## SHYpn Features Demonstrated

- [x] **Place creation**: Representing chemical species
- [x] **Transition creation**: Representing reactions
- [x] **Arc creation**: Representing stoichiometry
- [x] **Initial marking**: Setting initial concentrations/token counts
- [x] **Simulation modes**: Immediate vs. Continuous
- [x] **Token conservation**: P-invariant analysis
- [x] **Rate laws**: Mass action kinetics

## Validation

### Manual Calculation
Using continuous approximation with rate = k × [ATP]:

**At t = 0.01 s**:
- [ATP] ≈ 3.0 × exp(-100 × 0.01) = 3.0 × exp(-1) ≈ 1.10 mM
- [ADP] ≈ 0.1 + (3.0 - 1.10) = 2.00 mM

**At steady state** (t → ∞):
- [ATP] → 0
- [ADP] → 3.1 mM
- [Pi] → 4.0 mM

### Topology Analysis
- **P-invariants**: {ATP, ADP} (adenylate conservation)
- **T-invariants**: {ATPase} (single reaction pathway)
- **Deadlock**: None (transition fires until ATP depleted)
- **Liveness**: Non-live (system halts at steady state)

## Tutorial Steps

### Building the Model

1. **Create Places**:
   - Add place "ATP" with initial marking 3000
   - Add place "ADP" with initial marking 100
   - Add place "Pi" with initial marking 1000

2. **Create Transition**:
   - Add transition "ATPase"
   - Set rate law: `100 * ATP` (for continuous mode)

3. **Connect with Arcs**:
   - Draw arc from ATP to ATPase (weight: 1)
   - Draw arc from ATPase to ADP (weight: 1)
   - Draw arc from ATPase to Pi (weight: 1)

4. **Run Simulation**:
   - Switch to Immediate mode
   - Click "Step" to fire transition manually
   - Observe token changes
   - Switch to Continuous mode
   - Run simulation for 0.05 seconds
   - Observe concentration curves

5. **Analyze Topology**:
   - Open Topology panel
   - Check P-invariants (should find ATP + ADP conservation)
   - Verify T-invariants
   - Check for deadlocks

## Extensions

Try modifying the model:
1. Change k_cat to 50 s⁻¹ (slower reaction)
2. Add reverse reaction (ADP + Pi → ATP) with small rate constant
3. Add enzyme (ATPase) as a catalyst place with TestArc
4. Implement Michaelis-Menten kinetics instead of mass action

## References

1. **Berg, J.M., et al.** "Biochemistry" (8th ed.), W.H. Freeman, 2015
   - Chapter 15: Metabolism - Basic Concepts and Design
2. **BRENDA Enzyme Database**: EC 3.6.1.3 (Adenosinetriphosphatase)
   - https://www.brenda-enzymes.org/
3. **Alberty, R.A.** "Thermodynamics of Biochemical Reactions", Wiley, 2003
   - Table of standard free energies

---
**Difficulty**: ⭐☆☆☆☆ (Beginner)
**Time**: 15-20 minutes
**Prerequisites**: None
