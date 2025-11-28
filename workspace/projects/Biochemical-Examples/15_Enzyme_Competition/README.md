# Example 15: Enzyme Competition - Multiple Pathways for Glucose-6-Phosphate

## Overview

This example demonstrates **enzyme competition** where multiple enzymes compete for the same substrate. We model the metabolic branch point where **Glucose-6-Phosphate (G6P)** can enter either:
1. **Glycolysis** (via Phosphofructokinase, PFK)
2. **Pentose Phosphate Pathway** (via Glucose-6-Phosphate Dehydrogenase, G6PDH)

This is a fundamental concept in metabolic regulation showing how cells partition resources between ATP production (glycolysis) and biosynthetic precursors (pentose phosphate pathway).

## Novel Features Demonstrated

### 1. **Test Arcs (Catalyst Semantics)** ⭐
- **Enzymes modeled as catalysts**: PFK and G6PDH are connected via **test arcs**
- **Non-consuming behavior**: Enzyme tokens are NOT consumed during reactions
- **Visual distinction**: Dashed lines with hollow diamonds (test arcs)
- **Biological accuracy**: Enzymes enable reactions but remain available for multiple catalytic cycles

### 2. **Race Firing Policy** ⭐
- **Kinetic competition**: Both transitions use `firing_policy = 'race'`
- **Rate-weighted selection**: Faster enzyme (higher Vmax) fires more frequently
- **Stochastic branching**: Probability proportional to enzyme rates
- **Biological realism**: Matches Gillespie algorithm for molecular competition

### 3. **Competing Transitions**
- Both transitions consume the same substrate (G6P)
- Enzymes compete for substrate molecules
- Branching ratio reflects kinetic parameters (Vmax, Km)
- Demonstrates metabolic flux partitioning

## Biological Background

### The Glucose-6-Phosphate Branch Point

**Glucose-6-Phosphate (G6P)** is a central metabolite at a critical branch point:

```
        Glucose
           ↓ (Hexokinase)
    Glucose-6-Phosphate (G6P)
           ↓
    ┌──────┴──────┐
    ↓             ↓
 Glycolysis   Pentose Phosphate
 (Energy)     (Biosynthesis)
```

### Pathway 1: Glycolysis (Energy Production)

**Enzyme**: **Phosphofructokinase (PFK)**
- **Function**: Commits G6P to glycolytic pathway
- **Product**: Fructose-6-Phosphate → Fructose-1,6-bisphosphate
- **Purpose**: ATP generation
- **Regulation**: Inhibited by ATP (negative feedback), activated by AMP
- **Vmax**: ~70 μM/s (higher - glycolysis is the major pathway)
- **Km**: 0.1 mM (high affinity)

### Pathway 2: Pentose Phosphate Pathway (Biosynthesis)

**Enzyme**: **Glucose-6-Phosphate Dehydrogenase (G6PDH)**
- **Function**: First committed step of pentose phosphate pathway
- **Product**: 6-Phosphogluconolactone
- **Purpose**: Generate NADPH for biosynthesis, produce ribose-5-phosphate for nucleotide synthesis
- **Regulation**: Inhibited by NADPH (product inhibition)
- **Vmax**: ~49 μM/s (lower - pentose phosphate is secondary)
- **Km**: 0.05 mM (very high affinity)

### Metabolic Partitioning

Under normal conditions:
- **~70% of G6P → Glycolysis** (higher Vmax, ATP needs)
- **~30% of G6P → Pentose Phosphate** (NADPH needs, biosynthesis)

This ratio changes based on cellular state:
- **High energy demand**: More glycolysis (ATP production)
- **High biosynthetic demand**: More pentose phosphate (NADPH, ribose-5-P)
- **Oxidative stress**: More pentose phosphate (NADPH for antioxidant defense)

## Petri Net Structure

### Places (7 total)
1. **G6P**: Glucose-6-Phosphate (substrate, shared by both pathways)
2. **PFK_enzyme**: Phosphofructokinase enzyme (catalyst)
3. **G6PDH_enzyme**: Glucose-6-Phosphate Dehydrogenase enzyme (catalyst)
4. **F6P**: Fructose-6-Phosphate (product of glycolysis pathway)
5. **6PGL**: 6-Phosphogluconolactone (product of pentose phosphate pathway)
6. **ATP**: Energy currency (inhibits PFK when high)
7. **NADPH**: Reducing power (inhibits G6PDH when high)

### Transitions (2 competing)
1. **T1_PFK**: Phosphofructokinase reaction
   - **Type**: Continuous
   - **Rate**: Michaelis-Menten kinetics with ATP inhibition
   - **Firing Policy**: **race** (competes with T2)
   - **Formula**: `(70.0 * (G6P/1000.0) / (0.1 + G6P/1000.0)) / (1.0 + ATP/5000.0)`
   
2. **T2_G6PDH**: Glucose-6-Phosphate Dehydrogenase reaction
   - **Type**: Continuous
   - **Rate**: Michaelis-Menten kinetics with NADPH inhibition
   - **Firing Policy**: **race** (competes with T1)
   - **Formula**: `(49.0 * (G6P/1000.0) / (0.05 + G6P/1000.0)) / (1.0 + NADPH/200.0)`

### Arcs (9 total)

**Normal Arcs (substrate consumption/production):**
- A1: G6P → T1_PFK (weight: 1, substrate consumed by glycolysis)
- A2: T1_PFK → F6P (weight: 1, product of glycolysis)
- A3: G6P → T2_G6PDH (weight: 1, substrate consumed by pentose phosphate)
- A4: T2_G6PDH → 6PGL (weight: 1, product of pentose phosphate)

**Test Arcs (enzyme catalysts - non-consuming):**
- TA1: PFK_enzyme → T1_PFK (weight: 1, enzyme enables glycolysis)
- TA2: G6PDH_enzyme → T2_G6PDH (weight: 1, enzyme enables pentose phosphate)

**Inhibitor Arcs (feedback regulation):**
- I1: ATP ⊣ T1_PFK (weight: 5000 μM = 5 mM, high ATP inhibits glycolysis)
- I2: NADPH ⊣ T2_G6PDH (weight: 200 μM, high NADPH inhibits pentose phosphate)

**Production Arcs (cofactor generation):**
- A5: T2_G6PDH → NADPH (weight: 1, pentose phosphate produces NADPH)

## Key Parameters

### Initial Concentrations (Fed State)
- **G6P**: 100 μM (moderate substrate availability)
- **PFK_enzyme**: 10 μM (enzyme concentration)
- **G6PDH_enzyme**: 5 μM (lower than PFK, limiting factor)
- **F6P**: 0 μM (initially empty)
- **6PGL**: 0 μM (initially empty)
- **ATP**: 3000 μM = 3 mM (moderate energy state)
- **NADPH**: 50 μM (low, needs regeneration)

### Kinetic Parameters

**Phosphofructokinase (PFK):**
- **Vmax**: 70 μM/s (high capacity)
- **Km**: 0.1 mM = 100 μM (moderate affinity)
- **Ki_ATP**: 5 mM = 5000 μM (inhibited by ATP above this)

**Glucose-6-Phosphate Dehydrogenase (G6PDH):**
- **Vmax**: 49 μM/s (moderate capacity)
- **Km**: 0.05 mM = 50 μM (high affinity)
- **Ki_NADPH**: 200 μM (inhibited by NADPH above this)

### Expected Flux Ratio
```
Rate_PFK / Rate_G6PDH ≈ 70/49 × (Km_G6PDH/Km_PFK) ≈ 1.43 × 0.5 ≈ 0.7

Expected: ~58% glycolysis, ~42% pentose phosphate
(Modified from typical 70/30 due to lower G6PDH enzyme concentration)
```

## Expected Behavior

### Time Course (0-100 seconds)

1. **Initial Phase (0-10s)**: Rapid G6P consumption
   - Both pathways active
   - G6P depletes from 100 μM toward equilibrium

2. **Competition Phase (10-50s)**: Stochastic branching
   - **Race policy in action**: Transitions compete for each G6P molecule
   - **Probability**: PFK fires ~58% of time, G6PDH ~42%
   - **Flux partitioning**: Observable in product accumulation rates

3. **Regulatory Phase (50-100s)**: Product inhibition effects
   - NADPH accumulates → inhibits G6PDH → more flux to glycolysis
   - If ATP accumulates → inhibits PFK → more flux to pentose phosphate
   - **Dynamic rebalancing**: System self-regulates based on cofactor levels

### Observable Patterns

**Product Accumulation:**
- **F6P** (glycolysis product): Accumulates faster initially (higher Vmax)
- **6PGL** (pentose phosphate product): Slower accumulation (lower Vmax)
- **Ratio**: Should reflect branching probability (~60:40)

**Substrate Depletion:**
- **G6P**: Exponential decay toward steady state
- **Depletion rate**: Sum of both pathway rates

**Enzyme Concentrations:**
- **PFK_enzyme**: Constant at 10 μM (test arc = non-consuming)
- **G6PDH_enzyme**: Constant at 5 μM (test arc = non-consuming)
- **Verification**: Confirms test arc semantics working correctly

**Cofactor Dynamics:**
- **NADPH**: Rises from 50 μM, inhibits G6PDH when >200 μM
- **ATP**: Decreases slowly (glycolysis consumes to produce), inhibits PFK when >5 mM

## Learning Objectives

### Biological Concepts
1. **Metabolic branch points**: How cells partition resources
2. **Enzyme competition**: Kinetic basis for flux distribution
3. **Feedback regulation**: Product inhibition maintains homeostasis
4. **Pathway coordination**: Glycolysis vs biosynthesis balance

### Petri Net Concepts
1. **Test arcs**: Non-consuming arcs for catalysts
2. **Race firing policy**: Stochastic competition based on rates
3. **Competing transitions**: Multiple transitions consuming same place
4. **Inhibitor arcs**: Negative regulation mechanisms

### SHYPN Features
1. **Test arc semantics**: Verify enzymes NOT consumed
2. **Firing policy effects**: Compare race vs random vs priority
3. **Continuous transitions**: Michaelis-Menten kinetics
4. **Rate-based competition**: Probability ∝ rate

## Simulation Instructions

### Basic Simulation
1. Load model in SHYPN
2. Set simulation time: **100 seconds**
3. Time step (dt): **0.1 seconds**
4. Run simulation
5. Observe G6P depletion and product accumulation

### Analysis Tasks

**Task 1: Verify Test Arc Behavior**
- Plot enzyme concentrations (PFK_enzyme, G6PDH_enzyme)
- **Expected**: Both remain constant (non-consuming)
- **Interpretation**: Test arcs working correctly

**Task 2: Measure Flux Partitioning**
- Plot F6P and 6PGL accumulation
- Calculate ratio: F6P/6PGL at t=100s
- **Expected**: ~60:40 (glycolysis favored)
- **Interpretation**: Race policy creating rate-weighted branching

**Task 3: Observe Product Inhibition**
- Plot NADPH concentration over time
- Identify when NADPH > 200 μM (inhibition threshold)
- Observe reduction in 6PGL production rate
- **Interpretation**: Feedback regulation working

**Task 4: Compare Firing Policies**
- Run simulation with different policies:
  - **race**: Rate-weighted (default)
  - **random**: Equal probability
  - **priority**: Set PFK priority=10, G6PDH priority=5
- Compare flux ratios
- **Interpretation**: Policy dramatically affects pathway usage

### Advanced Analysis

**Experiment 1: Change Enzyme Ratio**
- Set PFK_enzyme = 5 μM, G6PDH_enzyme = 10 μM
- Observe flux reversal toward pentose phosphate

**Experiment 2: Metabolic Stress**
- Increase initial ATP to 6000 μM (energy surplus)
- Observe PFK inhibition, increased pentose phosphate flux

**Experiment 3: Oxidative Stress**
- Increase NADPH consumption (add NADPH → sink transition)
- Observe compensatory increase in G6PDH activity

## Clinical Relevance

### Glucose-6-Phosphate Dehydrogenase Deficiency
- **Most common enzyme deficiency**: Affects 400+ million people worldwide
- **Cause**: Mutations in G6PDH gene
- **Effect**: Reduced pentose phosphate pathway activity
- **Consequence**: NADPH deficiency → oxidative stress → hemolytic anemia
- **Model prediction**: 6PGL production reduced, more G6P diverted to glycolysis

### Cancer Metabolism (Warburg Effect)
- **Observation**: Cancer cells increase both glycolysis AND pentose phosphate pathways
- **Mechanism**: Upregulation of both PFK and G6PDH enzymes
- **Purpose**: ATP for proliferation + NADPH/ribose for biosynthesis
- **Model relevance**: Demonstrates metabolic reprogramming at branch points

### Diabetes
- **Hyperglycemia**: Elevated glucose → elevated G6P
- **Effect**: Both pathways saturated (Km << [G6P])
- **Consequence**: Excessive NADPH production → oxidative stress complications
- **Model prediction**: Product inhibition becomes critical regulatory mechanism

## Mathematical Notes

### Race Policy Algorithm

When both T1_PFK and T2_G6PDH are enabled:

1. **Sample exponential delays**:
   ```
   delay_1 = -ln(U₁) / rate_1
   delay_2 = -ln(U₂) / rate_2
   where U₁, U₂ ~ Uniform(0,1)
   ```

2. **Select minimum delay**:
   ```
   if delay_1 < delay_2:
       fire T1_PFK
   else:
       fire T2_G6PDH
   ```

3. **Probability analysis**:
   ```
   P(T1 fires) = rate_1 / (rate_1 + rate_2)
   P(T2 fires) = rate_2 / (rate_1 + rate_2)
   ```

### Michaelis-Menten with Inhibition

**PFK Rate (ATP inhibition):**
```
v_PFK = (Vmax_PFK × [G6P] / (Km_PFK + [G6P])) / (1 + [ATP]/Ki_ATP)

At [G6P]=100 μM, [ATP]=3000 μM:
v_PFK = (70 × 0.1 / (0.1 + 0.1)) / (1 + 3.0/5.0)
      = (70 × 0.5) / 1.6
      = 21.9 μM/s
```

**G6PDH Rate (NADPH inhibition):**
```
v_G6PDH = (Vmax_G6PDH × [G6P] / (Km_G6PDH + [G6P])) / (1 + [NADPH]/Ki_NADPH)

At [G6P]=100 μM, [NADPH]=50 μM:
v_G6PDH = (49 × 0.1 / (0.05 + 0.1)) / (1 + 0.05/0.2)
        = (49 × 0.667) / 1.25
        = 26.1 μM/s
```

### Flux Ratio
```
Flux_ratio = v_PFK / v_G6PDH = 21.9 / 26.1 ≈ 0.84

Expected distribution: ~46% glycolysis, ~54% pentose phosphate
(Changes as NADPH accumulates and inhibits G6PDH)
```

## References

### Biochemistry
1. **Garrett & Grisham** (2017). *Biochemistry*. 6th Ed. - Glucose-6-phosphate branch point
2. **Voet & Voet** (2016). *Biochemistry*. 4th Ed. - Enzyme kinetics and regulation
3. **Lehninger Principles** (Nelson & Cox, 2021) - Metabolic pathway integration

### Enzyme Kinetics
4. **Michaelis & Menten** (1913). *Die Kinetik der Invertinwirkung* - Original enzyme kinetics
5. **Cornish-Bowden** (2012). *Fundamentals of Enzyme Kinetics* - Modern enzyme kinetics theory

### G6PDH Deficiency
6. **Cappellini & Fiorelli** (2008). *Glucose-6-phosphate dehydrogenase deficiency*. Lancet.
7. **Luzzatto et al.** (2016). *Glucose-6-phosphate dehydrogenase deficiency*. Hematology.

### Stochastic Simulation
8. **Gillespie** (1977). *Exact stochastic simulation of coupled chemical reactions*. J. Phys. Chem.
9. **Gibson & Bruck** (2000). *Efficient exact stochastic simulation*. J. Phys. Chem. A.

### Cancer Metabolism
10. **Warburg** (1956). *On the origin of cancer cells*. Science.
11. **Vander Heiden et al.** (2009). *Understanding the Warburg effect*. Nat. Rev. Cancer.

---

**Model Type**: Biological Petri Net with Test Arcs and Race Policy  
**Scale**: 1 token = 1 μM (micromolar)  
**Time Units**: seconds  
**Complexity**: Intermediate (competing pathways, feedback regulation)  
**Educational Level**: Advanced undergraduate / Graduate biochemistry  
**Created**: November 2025  
**Purpose**: Demonstrate enzyme competition, test arcs, and race firing policy
