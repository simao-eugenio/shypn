# Example 2: Phosphoglucose Isomerase - Reversible Equilibrium

## Biological Context

Phosphoglucose isomerase (PGI) catalyzes the second step of glycolysis, converting glucose-6-phosphate (G6P) to fructose-6-phosphate (F6P). Unlike the irreversible ATP-consuming step before it, this reaction is freely reversible and operates near equilibrium in cells.

**Reaction**:
```
Glucose-6-phosphate ⇌ Fructose-6-phosphate
```

This is a classic example of an isomerization reaction where the substrate and product have the same molecular formula but different structures.

## Learning Objectives

1. **Bidirectional reactions**: Understand reversible processes
2. **Equilibrium constant (Keq)**: Learn how forward and reverse rates determine equilibrium
3. **Steady-state behavior**: Observe approach to equilibrium
4. **Net flux direction**: Understand when forward vs. reverse dominates

## Biochemical Parameters

### Enzyme: Phosphoglucose Isomerase (PGI)
- **EC number**: 5.3.1.9
- **k_forward**: 0.41 s⁻¹ (G6P → F6P)
- **k_reverse**: 0.14 s⁻¹ (F6P → G6P)
- **Keq**: k_forward / k_reverse = 2.93 (favors F6P)

### Initial Conditions (Scenario 1 - Forward direction)
- **[G6P]**: 2.0 mM (starting substrate)
- **[F6P]**: 0.0 mM (no product initially)

### Initial Conditions (Scenario 2 - Reverse direction)
- **[G6P]**: 0.0 mM
- **[F6P]**: 2.0 mM

### Thermodynamics
- **ΔG°'**: -2.92 kJ/mol (slightly exergonic, favors F6P)
- **Keq = [F6P]eq / [G6P]eq = 2.93**

## Model Structure

### Places (Species)
1. **G6P**: Glucose-6-phosphate (substrate/product)
2. **F6P**: Fructose-6-phosphate (product/substrate)

### Transitions (Reactions)
1. **PGI_forward**: G6P → F6P
   - Rate law: k_forward × [G6P] = 0.41 × [G6P]
   
2. **PGI_reverse**: F6P → G6P
   - Rate law: k_reverse × [F6P] = 0.14 × [F6P]

### Arcs (Stoichiometry)
- G6P → PGI_forward (stoichiometry: 1)
- PGI_forward → F6P (stoichiometry: 1)
- F6P → PGI_reverse (stoichiometry: 1)
- PGI_reverse → G6P (stoichiometry: 1)

## Expected Behavior

### Scenario 1: Starting from G6P = 2.0 mM

**Equilibrium Calculation**:
```
Keq = [F6P]eq / [G6P]eq = 2.93
[G6P]eq + [F6P]eq = 2.0 mM (conservation)

Solving:
[F6P]eq = 2.93 × [G6P]eq
[G6P]eq + 2.93 × [G6P]eq = 2.0
[G6P]eq = 2.0 / 3.93 = 0.51 mM
[F6P]eq = 2.93 × 0.51 = 1.49 mM
```

**Net flux direction**: Forward (G6P → F6P) initially, then approaches zero at equilibrium

### Scenario 2: Starting from F6P = 2.0 mM

**Equilibrium**: Same as Scenario 1
- [G6P]eq = 0.51 mM
- [F6P]eq = 1.49 mM

**Net flux direction**: Reverse (F6P → G6P) initially, then approaches zero

### Conservation Law
At all times: **[G6P] + [F6P] = 2.0 mM** (constant total hexose-phosphate)

### At Equilibrium
The forward and reverse rates are equal:
```
v_forward = v_reverse
0.41 × [G6P]eq = 0.14 × [F6P]eq
0.41 × 0.51 = 0.14 × 1.49
0.209 ≈ 0.209 mM/s ✓
```

## SHYpn Features Demonstrated

- [x] **Bidirectional arcs**: Two transitions for forward and reverse
- [x] **Equilibrium analysis**: Observing steady-state concentrations
- [x] **Reversibility detection**: Topology analysis identifies reversible pair
- [x] **Net flux calculation**: v_net = v_forward - v_reverse
- [x] **Conservation laws**: G6P + F6P invariant
- [x] **Alternative representation**: Could use single reversible transition

## Validation

### Manual Calculation (Equilibrium)

At equilibrium: v_forward = v_reverse
```
0.41 × [G6P]eq = 0.14 × [F6P]eq
[F6P]eq / [G6P]eq = 0.41 / 0.14 = 2.93 (matches Keq ✓)
```

**At t = 0** (Scenario 1):
- v_forward = 0.41 × 2.0 = 0.82 mM/s
- v_reverse = 0.14 × 0.0 = 0 mM/s
- v_net = 0.82 mM/s (forward direction)

**At equilibrium** (t → ∞):
- v_forward = 0.41 × 0.51 = 0.209 mM/s
- v_reverse = 0.14 × 1.49 = 0.209 mM/s
- v_net = 0 mM/s (detailed balance ✓)

### Topology Analysis
- **P-invariants**: {G6P, F6P} (hexose-phosphate conservation)
- **T-invariants**: {PGI_forward, PGI_reverse} (reversible cycle)
- **Reversible pairs**: PGI_forward ↔ PGI_reverse
- **Deadlock**: None (always at least one transition enabled)
- **Liveness**: Live (system continues to exchange between states)

## Tutorial Steps

### Building the Model

1. **Create Places**:
   - Add place "G6P" with initial marking 2000 (2.0 mM)
   - Add place "F6P" with initial marking 0

2. **Create Transitions**:
   - Add transition "PGI_forward"
   - Set rate law: `0.41 * G6P`
   - Add transition "PGI_reverse"
   - Set rate law: `0.14 * F6P`

3. **Connect with Arcs**:
   - Draw arc from G6P to PGI_forward (weight: 1)
   - Draw arc from PGI_forward to F6P (weight: 1)
   - Draw arc from F6P to PGI_reverse (weight: 1)
   - Draw arc from PGI_reverse to G6P (weight: 1)

4. **Run Simulation (Scenario 1)**:
   - Set simulation time: 20 seconds
   - Run continuous simulation
   - Observe approach to equilibrium
   - Note final concentrations

5. **Run Simulation (Scenario 2)**:
   - Reset model
   - Set G6P initial = 0, F6P initial = 2000
   - Run simulation
   - Verify same equilibrium reached

6. **Analyze Equilibrium**:
   - Calculate Keq from final concentrations
   - Compare with k_forward/k_reverse ratio
   - Verify conservation law

## Extensions

Try these modifications:
1. Change initial conditions to [G6P] = [F6P] = 1.0 mM (already at equilibrium)
2. Implement as single reversible transition instead of two
3. Add enzyme concentration as a catalyst (TestArc)
4. Explore effect of different Keq values

## References

1. **Berg, J.M., et al.** "Biochemistry" (8th ed.)
   - Chapter 16: Glycolysis and Gluconeogenesis
2. **BRENDA**: EC 5.3.1.9 (Glucose-6-phosphate isomerase)
   - Kinetic parameters for human enzyme
3. **Teusink et al. (2000)** "Can yeast glycolysis be understood in terms of in vitro kinetics?"
   - PMID: 10692304 (source of rate constants)

---
**Difficulty**: ⭐⭐☆☆☆ (Beginner-Intermediate)
**Time**: 20-25 minutes
**Prerequisites**: Example 1 (ATP Hydrolysis)
