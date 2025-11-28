# Example 3: Hexokinase - Michaelis-Menten Enzyme Kinetics

## Biological Context

Hexokinase catalyzes the first step of glycolysis, phosphorylating glucose to glucose-6-phosphate (G6P) using ATP. This is the first irreversible, committed step of glycolysis and a key regulatory point.

**Reaction**:
```
Glucose + ATP → Glucose-6-phosphate + ADP
```

Unlike simple mass action kinetics, hexokinase exhibits **saturable enzyme kinetics** - the reaction rate increases with substrate concentration but plateaus at high concentrations when the enzyme is saturated.

## Learning Objectives

1. **Michaelis-Menten kinetics**: Understand enzyme saturation
2. **Km parameter**: Learn the meaning of half-saturation constant
3. **Vmax parameter**: Understand maximum velocity
4. **Multiple substrates**: Handle reactions requiring two substrates
5. **Physiological conditions**: Use realistic cellular concentrations

## Biochemical Parameters

### Enzyme: Hexokinase (Type II, human muscle)
- **EC number**: 2.7.1.1
- **Vmax**: 0.124 mM/s (in presence of saturating substrates)
- **Km(glucose)**: 0.1 mM (half-saturation for glucose)
- **Km(ATP)**: 0.4 mM (half-saturation for ATP)

### Initial Conditions
- **[Glucose]**: 5.0 mM (normal blood glucose concentration)
- **[ATP]**: 3.0 mM (typical cellular ATP)
- **[G6P]**: 0.0 mM
- **[ADP]**: 0.1 mM

### Thermodynamics
- **ΔG°'**: -16.7 kJ/mol (highly exergonic)
- **Physiological ΔG**: -27 kJ/mol (essentially irreversible)

## Michaelis-Menten Equation

For a two-substrate reaction (ordered bi-bi mechanism):

```
v = Vmax × ([Glucose] / (Km_Glc + [Glucose])) × ([ATP] / (Km_ATP + [ATP]))
```

Simplified form when both substrates are present:
```
v = Vmax × [Glucose] × [ATP] / ((Km_Glc + [Glucose]) × (Km_ATP + [ATP]))
```

### Behavior at Different Concentrations

**Low glucose** ([Glc] << Km_Glc):
- Rate proportional to [Glucose]
- Approximately first-order

**High glucose** ([Glc] >> Km_Glc):
- Rate independent of [Glucose]
- Zero-order (saturated)

**At Km**:
- Rate = Vmax / 2 (half-maximal)

## Model Structure

### Places (Species)
1. **Glucose**: Substrate (initial: 5000 tokens = 5.0 mM)
2. **ATP**: Co-substrate (initial: 3000 tokens = 3.0 mM)
3. **G6P**: Product (initial: 0 tokens)
4. **ADP**: Co-product (initial: 100 tokens = 0.1 mM)

### Transitions (Reactions)
1. **Hexokinase**: Catalyzes Glucose + ATP → G6P + ADP
   - Rate law (Michaelis-Menten):
   ```
   v = 0.124 * (Glucose / (0.1 + Glucose)) * (ATP / (0.4 + ATP))
   ```

### Arcs (Stoichiometry)
- Glucose → Hexokinase (stoichiometry: 1)
- ATP → Hexokinase (stoichiometry: 1)
- Hexokinase → G6P (stoichiometry: 1)
- Hexokinase → ADP (stoichiometry: 1)

## Expected Behavior

### Initial Rate (t = 0)
```
v₀ = 0.124 × (5.0 / (0.1 + 5.0)) × (3.0 / (0.4 + 3.0))
   = 0.124 × (5.0 / 5.1) × (3.0 / 3.4)
   = 0.124 × 0.980 × 0.882
   = 0.107 mM/s
```

**Interpretation**:
- Glucose: 98% saturated (5.0 >> 0.1)
- ATP: 88% saturated (3.0 > 0.4)
- Overall rate: 86% of Vmax

### Time Course
The reaction will show:
1. **Initial phase**: Near-constant rate (enzyme saturated)
2. **Depletion phase**: Rate decreases as substrates consumed
3. **Plateau**: Reaction slows as substrates approach Km

### Substrate Depletion Order
Since ATP is limiting (lower total amount):
- **ATP** depletes first (3.0 mM consumed)
- **Glucose** partially consumed (2.0 mM remains)

### Steady State
Expected final state (ATP limiting):
- [Glucose] ≈ 2.0 mM (excess remains)
- [ATP] ≈ 0 mM (consumed completely)
- [G6P] ≈ 3.0 mM (stoichiometric with ATP consumed)
- [ADP] ≈ 3.1 mM (initial 0.1 + 3.0 produced)

## SHYpn Features Demonstrated

- [x] **Multiple substrates**: Two input arcs to one transition
- [x] **Multiple products**: Two output arcs from one transition
- [x] **Michaelis-Menten rate law**: Non-linear kinetics
- [x] **Saturation behavior**: Rate plateaus at high [substrate]
- [x] **Enzyme kinetics**: More realistic than mass action
- [x] **Parameter estimation**: Km and Vmax from literature

## Validation

### Rate Curve (Glucose Titration)

Hold [ATP] = 3.0 mM constant, vary [Glucose]:

| [Glucose] (mM) | [Glc]/Km | Rate (mM/s) | % Vmax |
|----------------|----------|-------------|--------|
| 0.01           | 0.1      | 0.010       | 8%     |
| 0.05           | 0.5      | 0.046       | 37%    |
| 0.10           | 1.0      | 0.073       | 59%    |
| 0.50           | 5.0      | 0.103       | 83%    |
| 1.00           | 10.0     | 0.106       | 86%    |
| 5.00           | 50.0     | 0.107       | 86%    |

**Km verification**: At [Glc] = 0.1 mM (1 × Km), rate ≈ 59% of plateau

### Topology Analysis
- **P-invariants**: 
  - {Glucose, G6P} (glucose conservation)
  - {ATP, ADP} (adenylate conservation)
- **T-invariants**: {Hexokinase} (single pathway)
- **Deadlock**: When ATP = 0 or Glucose = 0
- **Liveness**: Non-live (stops at steady state)

## Tutorial Steps

### Building the Model

1. **Create Places**:
   - Add place "Glucose" with initial marking 5000
   - Add place "ATP" with initial marking 3000
   - Add place "G6P" with initial marking 0
   - Add place "ADP" with initial marking 100

2. **Create Transition**:
   - Add transition "Hexokinase"
   - Set rate law (Michaelis-Menten):
   ```
   0.124 * (Glucose / (0.1 + Glucose)) * (ATP / (0.4 + ATP))
   ```

3. **Connect with Arcs**:
   - Draw arc from Glucose to Hexokinase (weight: 1)
   - Draw arc from ATP to Hexokinase (weight: 1)
   - Draw arc from Hexokinase to G6P (weight: 1)
   - Draw arc from Hexokinase to ADP (weight: 1)

4. **Run Simulation**:
   - Set simulation time: 30 seconds
   - Run continuous simulation
   - Observe rate decay as ATP depletes
   - Note saturation behavior at start

5. **Analyze Kinetics**:
   - Plot rate vs. time (should decay smoothly)
   - Calculate initial rate (should be ~0.107 mM/s)
   - Verify ATP is limiting substrate
   - Check final state

6. **Explore Parameter Effects**:
   - Reduce initial [Glucose] to 0.1 mM (= Km)
   - Observe slower initial rate
   - Increase Vmax to 0.2 mM/s
   - Observe faster kinetics

## Extensions

Try these modifications:
1. Add **product inhibition**: G6P inhibits hexokinase (TestArc)
   - Ki(G6P) = 0.02 mM (competitive with glucose)
2. Implement **cooperative kinetics** (Hill equation)
   - Some hexokinases show cooperativity
3. Add **enzyme concentration** as a parameter
   - Vmax = kcat × [Enzyme]
4. Model **different hexokinase isoforms**
   - Type I (brain): lower Km_Glc = 0.05 mM
   - Type IV (liver): higher Km_Glc = 10 mM

## References

1. **Berg, J.M., et al.** "Biochemistry" (8th ed.)
   - Chapter 16.1: Glycolysis is an energy-conversion pathway
2. **BRENDA**: EC 2.7.1.1 (Hexokinase)
   - Human hexokinase II kinetic parameters
3. **Wilson, J.E. (2003)** "Isozymes of mammalian hexokinase: structure, subcellular localization and metabolic function"
   - Journal of Experimental Biology 206: 2049-2057
4. **Mulukutla et al. (2015)** "Glucose metabolism in mammalian cell culture"
   - Biotechnology Advances 33(6): 900-915

---
**Difficulty**: ⭐⭐⭐☆☆ (Intermediate)
**Time**: 30-35 minutes
**Prerequisites**: Examples 1 and 2
**Next**: Example 4 (Product Inhibition)
