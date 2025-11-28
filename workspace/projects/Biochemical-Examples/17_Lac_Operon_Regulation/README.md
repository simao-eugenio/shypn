# Example 17: Lac Operon cAMP-CRP Regulation

## Overview

Classic gene regulation model demonstrating **cross-scale coupling** between metabolism, signaling, and gene expression. Shows how bacteria preferentially use glucose over lactose through the cAMP-CRP catabolite repression mechanism.

## Biological System

**Organism**: *Escherichia coli* (E. coli)

**Process**: Lactose metabolism regulation via glucose sensing

**Key Concept**: **Catabolite repression** - glucose represses lactose utilization genes even when lactose is present.

## Model Components

### Places (12 species)

#### Metabolites
1. **Glucose** (5.0 mM) - Preferred carbon source
2. **Lactose** (10.0 mM) - Alternative carbon source
3. **G6P** (0.0 mM) - Glucose-6-phosphate (glycolysis entry)
4. **Galactose** (0.0 mM) - Product of lactose cleavage
5. **ATP/ADP** (10.0/0.0 mM) - Energy currency

#### Signaling Molecules
6. **cAMP** (0.1 μM) - Cyclic AMP, signaling molecule (low when glucose high)
7. **CRP** (10.0 μM) - Catabolite repressor protein
8. **CRP-cAMP** (0.0 μM) - Active transcription factor complex

#### Genetic Components
9. **lac_operon** (1 copy) - DNA template (lacZ, lacY, lacA genes)
10. **lac mRNA** (0 copies) - Polycistronic messenger RNA
11. **β-Galactosidase** (10 molecules) - Enzyme that cleaves lactose

### Transitions (9 reactions)

#### Metabolic Reactions (Continuous)
1. **T1: Glucose consumption** - Glucose + ATP → G6P + ADP
   - Type: Continuous (Michaelis-Menten)
   - Rate: `1.0 * Glucose / (0.5 + Glucose)`
   - Vmax = 1.0 mM/min, Km = 0.5 mM

7. **T7: Lactose cleavage** - Lactose → Glucose + Galactose
   - Type: Continuous (enzyme-catalyzed)
   - Rate: `0.01 * β-Gal * Lactose / (1.0 + Lactose)`
   - Catalyzed by β-galactosidase (test arc)

#### Signaling Reactions (Continuous)
2. **T2: cAMP synthesis** - ATP → cAMP
   - Type: Continuous (inhibited by glucose)
   - Rate: `0.5 / (1.0 + Glucose / 0.5)`
   - **Inhibitor arc**: Glucose ⊸ T2 (threshold = 0.5 mM)
   - **Cross-scale coupling**: Metabolite regulates signaling

8. **T8: cAMP degradation** - cAMP → AMP
   - Type: Continuous (phosphodiesterase)
   - Rate: `0.1 * cAMP`

3. **T3: CRP-cAMP formation** - CRP + cAMP ⇌ CRP-cAMP
   - Type: Continuous (reversible)
   - Rate forward: `2.0 * CRP * cAMP`
   - Rate reverse: `0.5 * CRP-cAMP`
   - Kd = 1 μM (fast equilibrium)

9. **T9: CRP-cAMP dissociation** - CRP-cAMP → CRP + cAMP
   - Type: Continuous (reverse reaction)
   - Rate: `0.5 * CRP-cAMP`

#### Gene Expression (Stochastic)
4. **T4: lac transcription** - lac_operon → mRNA
   - Type: **Stochastic (burst mode)**
   - Rate: `0.01 + 0.5 * CRP-cAMP` (propensity)
   - **Test arc**: lac_operon (DNA template, not consumed)
   - **Test arc**: CRP-cAMP (transcription activator)
   - **Burst**: Produces 7 mRNA copies per event
   - **Cross-scale coupling**: Signaling regulates genetics

5. **T5: mRNA translation** - mRNA → β-Galactosidase
   - Type: Stochastic (ribosome catalysis)
   - Rate: `0.1 * mRNA`
   - **Test arc**: mRNA (template, not consumed)
   - Each mRNA produces ~100 proteins over lifetime

6. **T6: mRNA degradation** - mRNA → ∅
   - Type: Stochastic (RNase degradation)
   - Rate: `0.23 * mRNA`
   - Half-life: 3 minutes (k_deg = ln(2)/3 = 0.23)

## System Dynamics

### Phase 1: Glucose Consumption (t=0 to t≈20 min)

**Initial State:**
- High glucose (5.0 mM) → cAMP low (0.1 μM) → CRP-cAMP low (~0)
- lac operon **repressed** (basal transcription only)
- Lactose present (10.0 mM) but **not utilized**

**Events:**
1. T1 fires continuously: Glucose → G6P (glycolysis)
2. [Glucose] decreases: 5.0 → 0.1 mM
3. As glucose drops, inhibition of T2 weakens
4. T2 (cAMP synthesis) activates: [cAMP] rises 0.1 → 10 μM (100-fold)
5. T3: CRP + cAMP → CRP-cAMP complex forms
6. [CRP-cAMP] increases: 0 → 5 μM

**Result:** Glucose depleted, cAMP high, stage set for lac induction

### Phase 2: Lac Operon Induction (t=20 to t≈40 min)

**Trigger:** High [CRP-cAMP] activates transcription

**Events:**
1. T4 (transcription) propensity increases: `0.01 + 0.5 * 5 = 2.51`
2. **Stochastic bursts**: Each T4 firing produces 7 mRNA copies
3. [mRNA] increases: 0 → 50 molecules (stochastic fluctuations)
4. T5 (translation) fires stochastically: mRNA → β-Gal
5. [β-Gal] increases: 10 → 5000 molecules (**500-fold induction**)

**Stochastic Behavior:**
- mRNA count fluctuates: 45-55 copies (shot noise)
- Protein accumulates smoothly (law of large numbers)

**Result:** lac operon fully induced, β-galactosidase expressed

### Phase 3: Lactose Utilization (t=40 to t≈80 min)

**Trigger:** High [β-Gal] enables lactose cleavage

**Events:**
1. T7 (lactose cleavage) activates: Lactose → Glucose + Galactose
2. [Lactose] decreases: 10.0 → 0 mM
3. [Glucose] increases: 0.1 → 5.0 mM (replenished from lactose)
4. **Feedback**: Rising glucose → [cAMP] drops → transcription reduces
5. [mRNA] decreases: 50 → 5 molecules (degradation + reduced synthesis)
6. [β-Gal] remains high (long protein half-life ~hours)

**Result:** Lactose consumed, glucose restored, operon returns to basal state

### Steady State (t > 80 min)

- [Glucose] = 5.0 mM (maintained by lactose cleavage until lactose depleted)
- [Lactose] = 0 mM (fully consumed)
- [cAMP] = 0.1 μM (low due to high glucose)
- [CRP-cAMP] ≈ 0 (no activation)
- [mRNA] = 5 molecules (basal level)
- [β-Gal] = 5000 molecules (stable, persists even when operon off)

## Key Features Demonstrated

### 1. Cross-Scale Coupling

**Three-layer hierarchy:**
```
Metabolism (Glucose) 
    ↓ (inhibits)
Signaling (cAMP-CRP)
    ↓ (activates)
Gene Expression (lac mRNA → β-Gal)
    ↓ (enables)
Metabolism (Lactose → Glucose)
```

**Information flow:**
- Metabolite levels regulate signaling molecules
- Signaling molecules regulate gene expression
- Gene products regulate metabolic fluxes

**Feedback loop:** Lactose cleavage produces glucose → glucose inhibits cAMP → cAMP required for lac expression → negative feedback

### 2. Heterogeneous Transition Types

**Four types in one model:**
- **Continuous** (6 transitions): T1, T2, T3, T7, T8, T9
  - ODE integration (RK4)
  - Deterministic dynamics
  - Used for: Metabolism, signaling, equilibria

- **Stochastic** (3 transitions): T4, T5, T6
  - Gillespie algorithm
  - Probabilistic firing
  - Used for: Gene expression (low copy numbers)

**Hybrid coordination:** Algorithm 3 (Hybrid Scheduler) coordinates all types

### 3. Arc-Level Regulation

**Inhibitor arc:**
- Glucose ⊸ T2 (cAMP synthesis)
- Threshold: 0.5 mM
- When [Glucose] > 0.5 mM: cAMP synthesis reduced
- **Catabolite repression mechanism**

**Test arcs (catalytic):**
- lac_operon ⤏ T4 (DNA template not consumed)
- CRP-cAMP ⤏ T4 (transcription factor enhances rate)
- mRNA ⤏ T5 (mRNA template not consumed)
- β-Gal ⤏ T7 (enzyme catalysis, not consumed)

### 4. Stochastic Bursts

**Transcription bursts:**
- T4 produces **7 mRNA copies per event** (burst size)
- Biological basis: Processive transcription
  - RNA polymerase binds promoter
  - Transcribes multiple rounds before dissociating
  - Burst = multiple mRNA from single binding event

**Consequence:**
- mRNA count: Discrete, fluctuating (50 ± 10 molecules)
- Protein count: Smooth accumulation (5000 ± 50 molecules)
- **Noise propagation**: Gene expression noise filtered by translation

### 5. Weak Independence Analysis

**Competing transitions:**
- T1 (glucose consumption) vs. T7 (lactose → glucose)
  - Both consume/produce glucose (shared place)
  - **Convergent dependency**: T7 output feeds T1 input
  - **Sequential execution required** (not weakly independent)

**Potential parallelism:**
- T4 (transcription) and T8 (cAMP degradation)
  - Disjoint localities (different places)
  - **Weakly independent**: Can execute in parallel
  - Enables faster simulation on multi-core CPUs

## Biological Significance

### Catabolite Repression (Glucose Effect)

**Evolutionary advantage:**
- Glucose: High ATP yield (38 ATP/glucose via respiration)
- Lactose: Lower efficiency (must be cleaved first, costs energy)
- **Optimal strategy**: Use glucose first, lactose only when glucose depleted

**Molecular mechanism:**
- High glucose → low cAMP → no CRP-cAMP → lac operon repressed
- Low glucose → high cAMP → CRP-cAMP forms → lac operon activated

### Diauxic Growth

**Classic experiment** (Monod, 1947):
- E. coli grown in glucose + lactose medium
- **Phase 1**: Exponential growth on glucose
- **Lag phase**: Lac operon induction (~20 min)
- **Phase 2**: Exponential growth on lactose
- **Biphasic curve** → "diauxic growth"

**This model reproduces the lag phase mechanism.**

### Gene Regulatory Logic

**Boolean logic interpretation:**
```
lac expression = (CRP-cAMP > threshold) AND NOT (Repressor > threshold)
               = (Glucose LOW) AND (Lactose present)
```

**In this simplified model:**
- Repressor omitted (assumes lactose always present to inactivate repressor)
- Focus on positive regulation via cAMP-CRP

## Simulation Recommendations

### Suggested Protocol

1. **Initial run** (100 minutes):
   ```
   t_end = 100.0
   dt = 0.01
   method = "hybrid"
   ```

2. **Observe phases**:
   - t=0-20: Glucose depletion, cAMP rise
   - t=20-40: Lac induction (mRNA/protein synthesis)
   - t=40-80: Lactose consumption
   - t>80: Steady state (lactose depleted)

3. **Plot trajectories**:
   - Glucose (solid line)
   - Lactose (solid line)
   - cAMP (dashed line, secondary axis)
   - CRP-cAMP (dashed line, secondary axis)
   - mRNA (step plot, discrete)
   - β-Galactosidase (solid line)

### Expected Results

**Glucose trajectory:**
```
t=0:   5.0 mM  (high)
t=20:  0.1 mM  (depleted)
t=40:  0.5 mM  (restored from lactose)
t=80:  5.0 mM  (fully restored)
```

**cAMP trajectory:**
```
t=0:   0.1 μM  (low)
t=20:  10 μM   (high, 100-fold increase)
t=40:  8 μM    (still high)
t=80:  0.1 μM  (low again, glucose back)
```

**β-Galactosidase trajectory:**
```
t=0:   10 molecules   (basal)
t=20:  100 molecules  (starting induction)
t=40:  5000 molecules (fully induced, 500×)
t=80:  5000 molecules (persists, long half-life)
```

### Stochasticity Check

**Run 10 replicates:**
- Plot mRNA trajectories (should show variability)
- Plot β-Gal trajectories (should converge)
- Compute coefficient of variation: CV(mRNA) > CV(β-Gal)

**Expected:**
- CV(mRNA) ≈ 20-30% (high noise, low copy number)
- CV(β-Gal) ≈ 2-5% (low noise, high copy number, averaging)

## Extensions

### 1. Add Lactose Repressor (LacI)

**Current model simplification:** Assumes repressor always inactive

**Extension:**
- Add place: LacI (repressor protein)
- Add inhibitor arc: LacI ⊸ T4 (blocks transcription when [Lactose] low)
- Add transition: Lactose + LacI → Lactose-LacI (inactivation)

**Effect:** Model full lac operon logic (glucose AND lactose control)

### 2. Add Permease (LacY)

**Current model simplification:** Assumes lactose import is passive

**Extension:**
- Add place: Lactose_external
- Add place: Permease (product of lacY gene, co-transcribed with β-gal)
- Add transition: Lactose_ext → Lactose (catalyzed by Permease)

**Effect:** Positive feedback (more permease → more lactose import → more induction)

### 3. Glucose Pulse Experiment

**Protocol:**
- Run until t=50 (lac operon fully induced)
- Add glucose pulse: [Glucose] = 0 → 5 mM at t=50
- Observe repression: [cAMP] drops, transcription stops

**Prediction:** Demonstrates **catabolite repression override**

### 4. Parameter Sensitivity

**Vary burst size:**
- burst_size = 1, 3, 7, 15
- Observe effect on mRNA noise and induction time

**Vary cAMP degradation:**
- k_deg = 0.05, 0.1, 0.2
- Observe effect on response time and overshoot

## References

1. **Jacob, F., & Monod, J. (1961)**. "Genetic regulatory mechanisms in the synthesis of proteins". *Journal of Molecular Biology*, 3(3), 318-356.
   - Original lac operon model (Nobel Prize 1965)

2. **Monod, J. (1947)**. "The phenomenon of enzymatic adaptation and its bearings on problems of genetics and cellular differentiation". *Growth*, 11, 223-289.
   - Discovery of diauxic growth

3. **Makman, R. S., & Sutherland, E. W. (1965)**. "Adenosine 3',5'-phosphate in Escherichia coli". *Journal of Biological Chemistry*, 240(3), 1309-1314.
   - Discovery of cAMP in bacteria

4. **Zubay, G., Schwartz, D., & Beckwith, J. (1970)**. "Mechanism of activation of catabolite-sensitive genes: a positive control system". *Proceedings of the National Academy of Sciences*, 66(1), 104-110.
   - CRP-cAMP mechanism

5. **Thesis Chapter 3** (Section 3.2): "The Integration Challenge"
   - Detailed mechanistic model and phase analysis

## Learning Objectives

After working with this example, you should understand:

1. ✅ **Cross-scale coupling**: Metabolism → signaling → genetics → metabolism
2. ✅ **Catabolite repression**: Glucose-mediated gene regulation
3. ✅ **Hybrid modeling**: Continuous + stochastic transitions in one network
4. ✅ **Stochastic bursts**: Gene expression noise and burst kinetics
5. ✅ **Test arcs**: Catalytic roles (DNA templates, enzymes)
6. ✅ **Inhibitor arcs**: Regulatory mechanisms (glucose ⊸ cAMP synthesis)
7. ✅ **Feedback loops**: Product inhibition (glucose → cAMP → lac → glucose)
8. ✅ **Diauxic growth**: Biphasic dynamics in bacterial cultures

---

**Model Status**: ✅ Ready for simulation  
**Complexity**: High (12 places, 9 transitions, 4 transition types)  
**Recommended for**: Advanced users, gene regulation studies, thesis validation
