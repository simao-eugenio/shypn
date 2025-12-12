# Lambda Phage Lysogeny-Lysis Decision Circuit

## 🧬 Biological Context

The **λ (lambda) bacteriophage** is one of the most studied examples of gene regulation and bistable genetic switches in molecular biology. When λ phage infects *E. coli*, it faces a critical decision:

- **Lysogenic pathway**: Integrate into host genome and remain dormant (prophage state)
- **Lytic pathway**: Replicate rapidly, lyse the host cell, and release new phage particles

This decision is controlled by a **genetic switch** involving two key transcription factors that mutually repress each other.

## 🔬 Regulatory Architecture

### Key Players

1. **CI (λ repressor)**:
   - Maintains lysogenic state
   - Represses lytic genes (including *cro*)
   - **Autoregulates**: CI dimers activate their own transcription (positive feedback)
   - Binds cooperatively to operators OR1, OR2, OR3

2. **Cro protein**:
   - Drives lytic development
   - Represses CI transcription
   - Prevents lysogeny establishment

3. **Bistable Switch**:
   - High CI, low Cro → **Lysogenic state** (stable)
   - Low CI, high Cro → **Lytic state** (stable)
   - Mutual repression creates two stable equilibria

### Environmental Sensing

- **UV damage** triggers CI degradation via RecA-mediated cleavage
- Low CI allows Cro expression → switch to lytic cycle
- This is the **SOS response** mechanism

## 🎯 Model Features

This Petri net model captures:

### 1. **Stochastic Gene Expression**
- **Discrete molecular counts**: CI and Cro proteins are low-copy (0-100 molecules)
- **Stochastic transitions**: Transcription and translation use Gillespie/tau-leaping
- **Intrinsic noise**: Fluctuations drive stochastic switching

### 2. **Regulatory Coupling** (Test & Inhibitor Arcs)
- **CI autoregulation**: CI_Dimer → CI_Transcription (test arc, positive feedback)
- **Mutual repression**:
  - Cro_Dimer ⊣ CI_Transcription (inhibitor arc, threshold=10)
  - CI_Dimer ⊣ Cro_Transcription (inhibitor arc, threshold=10)
- **Energy requirement**: ATP required for transcription (test arcs)
- **State enforcement**:
  - Lysogenic_State ⊣ Cro_Transcription (prevents lytic during lysogeny)
  - Lytic_Genes_Active ⊣ CI_Transcription (prevents lysogenic during lysis)

### 3. **Cooperative Dimerization**
- **2 CI → CI_Dimer**: Nonlinear rate (quadratic in CI concentration)
- **2 Cro → Cro_Dimer**: Same cooperative binding
- Dimers are the active regulatory forms

### 4. **UV-Induced Switching**
- **UV_Damage** place accumulates during stress
- UV triggers **CI_Protein_Decay** (RecA-mediated cleavage)
- CI degradation → Cro derepression → lytic switch
- CI dimers inhibit their own degradation (stability when high CI)

### 5. **Bistability**
- **Two stable states**:
  - Lysogenic: High CI_Dimer (~50), Low Cro (~0), Lysogenic_State=1
  - Lytic: Low CI (~0), High Cro_Dimer (~30), Lytic_Genes_Active=1
- **Hysteresis**: Requires significant perturbation to switch states

## 🔢 Transition Types

**Stochastic (12 transitions)**:
- Gene transcription (CI, Cro)
- mRNA translation
- Protein dimerization
- mRNA/protein degradation
- State transitions (lysogeny/lysis entry)

All transitions use **tau-leaping** for efficient stochastic simulation.

## 📊 Initial Conditions

**Default: Race to decision**
- CI_Gene = 1, Cro_Gene = 1 (both available)
- All proteins/mRNA = 0 (starting from infection)
- ATP = 100 mM (sufficient energy)
- UV_Damage = 0 (no stress)

**The model will stochastically choose lysogeny or lysis based on:**
- Random fluctuations in early CI vs Cro expression
- Whichever protein dominates first will suppress the other
- Demonstrates **symmetry breaking** via stochasticity

## 🎮 Simulation Scenarios

### Scenario 1: Normal Infection (Race Condition)
```
Initial: CI=0, Cro=0, UV=0
Expected: ~50% lysogeny, ~50% lysis (stochastic decision)
```

### Scenario 2: UV-Induced Lytic Switch
```
Initial: Set CI_Protein=50, CI_Dimer=25, Lysogenic_State=1
Then add: UV_Damage=5
Expected: CI degradation → Cro expression → lytic switch
```

### Scenario 3: Forced Lysogeny
```
Initial: Set CI_Protein=40, CI_Dimer=20
Expected: CI autoregulation locks in lysogeny
```

### Scenario 4: Forced Lysis
```
Initial: Set Cro_Protein=30, Cro_Dimer=15
Expected: Cro repression blocks CI → lytic development
```

## 🧮 Mathematical Properties

### Weak Independence Analysis
- **Convergent coupling**: CI and Cro pathways converge at state decision
- **Regulatory coupling**: Extensive mutual inhibition (test/inhibitor arcs)
- **Competitive coupling**: CI_Protein and Cro_Protein compete for dominance
- Expected weak independence: ~60-70% (moderate due to regulatory complexity)

### Nonlinear Dynamics
- **Positive feedback**: CI autoregulation (Hill coefficient ~2)
- **Negative feedback**: Mutual repression (inhibitor arcs)
- **Bistability**: f(CI, Cro) has two stable fixed points
- **Stochastic switching**: Noise can induce transitions between states

## 🔗 Connection to Paper Theory

This model demonstrates:

1. **Heterogeneous dynamics** (τ): All stochastic transitions (discrete low-copy molecules)
2. **Regulatory coupling** (Σ): 9 test/inhibitor arcs for gene regulation
3. **Competitive coupling**: CI vs Cro competition for dominance
4. **Stochastic decision-making**: Noise-driven symmetry breaking
5. **Biochemical realism**: Cooperative binding, degradation, state transitions

## 📚 References

- Ptashne, M. (2004). *A Genetic Switch: Phage Lambda Revisited*. Cold Spring Harbor Laboratory Press.
- Arkin, A., Ross, J., & McAdams, H. H. (1998). Stochastic kinetic analysis of developmental pathway bifurcation in phage λ-infected *Escherichia coli* cells. *Genetics*, 149(4), 1633-1648.
- Little, J. W. (2006). Gene regulatory circuitry of phage λ. *Current Opinion in Microbiology*, 9(6), 588-594.

## 🚀 Usage

1. Open `model.shy` in SHYpn
2. Run simulation for 1000-5000 time units
3. Observe stochastic decision:
   - Monitor CI_Dimer vs Cro_Dimer trajectories
   - Check final state: Lysogenic_State vs Lytic_Genes_Active
4. Repeat simulation multiple times to see probabilistic outcomes
5. Test UV-induced switching by manually adding UV_Damage during lysogeny

**Expected output**: Trajectory will show one protein rapidly dominating while the other is suppressed, demonstrating the winner-take-all bistable switch dynamics.
