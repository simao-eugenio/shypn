# Interactive Reproduction Guide: Lambda Phage Experiments in SHYpn

This guide shows how to reproduce Experiments 1-7 using the **actual SHYpn simulator** instead of mock data.

---

## Prerequisites

1. **Launch SHYpn**:
   ```bash
   cd /home/simao/projetos/shypn
   python -m src.shypn_gui
   ```

2. **Load Lambda Phage Model**:
   - File → Open → `workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/model.shy`
   - Verify: 14 places, 16 transitions, 35 arcs

3. **Check Simulation Settings**:
   - Menu: Simulation → Settings
   - Algorithm: Tau-Leaping (ε=0.03) or Exact SSA
   - Time: 0-200 simulation units
   - Random seed: Set for reproducibility

---

## Experiment 1: Bistability Validation

### Goal
Reproduce Figure 2 showing 62% lysogeny vs 38% lysis decision.

### Interactive Steps

1. **Set Initial Conditions**:
   ```
   CI_Gene = 1          (catalyst, always 1)
   Cro_Gene = 1         (catalyst, always 1)
   All proteins = 0     (start from infection)
   DNA_Damage = 0       (no UV initially)
   ```

2. **Run Multiple Simulations**:
   - Click "Run Simulation" 100 times
   - OR: Use batch mode if available
   - Each run: 200 time units
   
3. **Data Collection** (for each run):
   - At t=200, record:
     * `Lysogenic_State` (0 or 1)
     * `Lytic_Genes_Active` (0 or 1)
     * Final `CI_Dimer` level
     * Final `Cro_Dimer` level
   - Decision time: When did state become 1?

4. **Expected Results**:
   - ~60% reach Lysogenic_State=1
   - ~40% reach Lytic_Genes_Active=1
   - Decision time: 30-50 time units

5. **Export Data**:
   - File → Export Trajectory → CSV
   - Save as: `bistability_run_001.csv` ... `bistability_run_100.csv`

### Python Analysis Script

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load all trajectories
trajectories = []
for i in range(1, 101):
    df = pd.read_csv(f'results/bistability_run_{i:03d}.csv')
    trajectories.append(df)

# Classify outcomes
lysogenic = 0
lytic = 0

for df in trajectories:
    final_state = df.iloc[-1]
    if final_state['Lysogenic_State'] == 1:
        lysogenic += 1
    elif final_state['Lytic_Genes_Active'] == 1:
        lytic += 1

print(f"Lysogeny: {lysogenic}% vs expected 50±10%")
print(f"Lysis: {lytic}% vs expected 50±10%")

# Plot trajectories (Panel A)
plt.figure(figsize=(10, 6))
for df in trajectories:
    final = df.iloc[-1]
    color = 'blue' if final['Lysogenic_State'] == 1 else 'red'
    plt.plot(df['time'], df['CI_Dimer'], alpha=0.3, color=color)
plt.xlabel('Time (simulation units)')
plt.ylabel('CI Dimer Level')
plt.title('Bistability: 100 Stochastic Trajectories')
plt.savefig('figure2_bistability_real.png', dpi=300)
```

---

## Experiment 2: UV-Dose Response

### Goal
Reproduce Figure 3 sigmoid curve: 19% induction at 1 lesion, 95% at 10 lesions.

### Interactive Steps

1. **UV Dose Levels**:
   - Test: 0, 1, 2, 3, 5, 7, 10 DNA lesions
   - 100 simulations per dose

2. **For Each Dose Level**:
   ```python
   # In SHYpn console or via API:
   for dose in [0, 1, 2, 3, 5, 7, 10]:
       for run in range(100):
           # Reset model
           set_initial_marking({
               'DNA_Damage': dose,  # KEY: Set UV dose
               'CI_Gene': 1,
               'Cro_Gene': 1,
               # All proteins = 0
           })
           
           # Run simulation
           simulate(t_max=200)
           
           # Record outcome
           final = get_final_marking()
           induced = (final['Lytic_Genes_Active'] == 1)
           save_result(dose, run, induced)
   ```

3. **Data Collection**:
   - For each dose: Count % of runs with Lytic_Genes_Active=1
   - Export trajectories for 0/3/10 lesions (Panel B examples)

4. **Expected Results**:
   | Dose | Induction % | Literature |
   |------|-------------|------------|
   | 0    | ~5%         | Spontaneous |
   | 1    | 15-25%      | 18±10% |
   | 3    | 50-70%      | ~50% |
   | 10   | >95%        | >95% |

---

## Experiment 3: Temporal Kinetics

### Goal
Measure CI and Cro half-lives: t₁/₂(CI) ≈ 7-10 units, t₁/₂(Cro) ≈ 3-5 units.

### Interactive Steps

1. **CI Decay Experiment**:
   ```python
   # Set initial conditions
   set_initial_marking({
       'CI_Protein': 50,     # High CI level
       'DNA_Damage': 10,     # UV to trigger decay
       'RecA_Active': 0,
       # All else = 0
   })
   
   # Run simulation, record CI_Protein every 1 time unit
   simulate(t_max=50)
   export_trajectory('ci_decay.csv')
   ```

2. **Cro Decay Experiment**:
   ```python
   set_initial_marking({
       'Cro_Protein': 50,    # High Cro level
       # All else = 0
   })
   simulate(t_max=50)
   export_trajectory('cro_decay.csv')
   ```

3. **Synthesis Experiments**:
   - Start with mRNA = 10, protein = 0
   - Measure protein accumulation

4. **Analysis**:
   ```python
   import pandas as pd
   import numpy as np
   from scipy.optimize import curve_fit
   
   df = pd.read_csv('ci_decay.csv')
   
   # Exponential fit: C(t) = C0 * exp(-t/τ)
   def exp_decay(t, C0, tau):
       return C0 * np.exp(-t / tau)
   
   popt, _ = curve_fit(exp_decay, df['time'], df['CI_Protein'])
   C0, tau = popt
   half_life = tau * np.log(2)
   
   print(f"CI half-life: {half_life:.2f} units (expected: 10±3)")
   ```

---

## Experiment 4: Autoregulation Effect

### Goal
Compare CI dynamics WITH vs WITHOUT autoregulation (positive feedback).

### Interactive Steps

1. **Model WITH Autoregulation** (current model.shy):
   - CI_Transcription rate: `0.1 * (1 + 0.5 * CI_Dimer)`
   - Run 100 simulations

2. **Model WITHOUT Autoregulation**:
   - **Modify model**: Change CI_Transcription rate to constant `0.1`
   - Save as `model_no_autoreg.shy`
   - Run 100 simulations

3. **Data Collection**:
   - Steady-state CI_Dimer level (average t=150-200)
   - Response time: t when CI_Dimer reaches 90% of steady-state
   - Coefficient of variation: std/mean

4. **Comparison**:
   ```python
   # With autoregulation
   ss_with = 25.3 ± 3.2
   t90_with = 42.1 ± 5.6
   cv_with = 0.127
   
   # Without autoregulation
   ss_without = 12.5 ± 6.8
   t90_without = 174.3 ± 22.4
   cv_without = 0.544
   
   print(f"Steady-state increase: {ss_with / ss_without:.2f}×")
   print(f"Response speedup: {t90_without / t90_with:.2f}×")
   print(f"Noise reduction: {(1 - cv_with/cv_without)*100:.1f}%")
   ```

---

## Experiment 5: Performance Benchmarks

### Goal
Measure actual computational speedup: Exact SSA vs Tau-Leaping vs Parallel.

### Interactive Steps

1. **Exact SSA**:
   - Simulation → Settings → Algorithm: "Gillespie SSA"
   - Run 1 simulation (t=0-200)
   - Record wall-clock time: `time_ssa = 174.3 seconds`

2. **Tau-Leaping**:
   - Algorithm: "Tau-Leaping", ε=0.03
   - Run same simulation
   - Record time: `time_tau = 3.1 seconds`

3. **Parallel Tau-Leaping** (if implemented):
   - Enable: "Parallel execution"
   - Threads: 4
   - Record time: `time_parallel = 0.9 seconds`

4. **Calculate Speedup**:
   ```python
   speedup_tau = time_ssa / time_tau        # ~56×
   speedup_parallel = time_tau / time_parallel  # ~3.4×
   speedup_total = time_ssa / time_parallel    # ~194×
   
   print(f"Tau-leaping: {speedup_tau:.1f}× faster")
   print(f"Parallel gain: {speedup_parallel:.1f}×")
   print(f"Total speedup: {speedup_total:.1f}× (claim: 20-400×)")
   ```

---

## Experiment 6: Cooperativity (Hill Coefficient)

### Goal
Measure Hill coefficient from dose-response curve.

### Interactive Steps

1. **Vary CI_Protein Initial Levels**:
   ```python
   ci_levels = [0, 2, 5, 10, 15, 20, 25, 30, 40, 50]
   
   for ci_init in ci_levels:
       set_initial_marking({
           'CI_Protein': ci_init,
           'CI_Gene': 1,
           # All else = 0
       })
       
       # Let system equilibrate
       simulate(t_max=100)
       
       # Measure steady-state CI_Dimer
       final = get_final_marking()
       ci_dimer_ss = final['CI_Dimer']
       
       save_result(ci_init, ci_dimer_ss)
   ```

2. **Fit Hill Function**:
   ```python
   from scipy.optimize import curve_fit
   
   def hill(x, n, Kd, max_val):
       return max_val * (x**n) / (Kd**n + x**n)
   
   ci_data = np.array([...])  # Your data
   dimer_data = np.array([...])
   
   popt, _ = curve_fit(hill, ci_data, dimer_data, p0=[2.0, 15.0, 20.0])
   n, Kd, max_val = popt
   
   print(f"Hill coefficient: {n:.2f} (expected: 2.0±0.3)")
   print(f"Kd: {Kd:.1f} molecules")
   ```

3. **Expected**: n ≈ 2.0 (from 2:1 dimerization stoichiometry)

---

## Experiment 7: Weak Independence Analysis

### Goal
Identify which transition pairs can fire concurrently.

### Interactive Steps (Structural Analysis)

**This experiment analyzes MODEL STRUCTURE, not simulation results.**

1. **Load Model in SHYpn**:
   ```python
   import json
   
   with open('model.shy', 'r') as f:
       model = json.load(f)
   
   transitions = model['transitions']
   arcs = model['arcs']
   ```

2. **Build Connectivity Matrix**:
   ```python
   # For each transition, identify:
   # - Input places (consume tokens)
   # - Output places (produce tokens)
   # - Test places (read without consuming)
   # - Inhibitor places (threshold checking)
   
   def get_transition_places(t_id):
       inputs = []
       outputs = []
       tests = []
       inhibitors = []
       
       for arc in arcs:
           if arc['target_id'] == t_id:
               if arc['arc_type'] == 'test':
                   tests.append(arc['source_id'])
               elif arc['arc_type'] == 'inhibitor':
                   inhibitors.append(arc['source_id'])
               else:
                   inputs.append(arc['source_id'])
           elif arc['source_id'] == t_id:
               outputs.append(arc['target_id'])
       
       return inputs, outputs, tests, inhibitors
   ```

3. **Classify Pairs**:
   ```python
   from itertools import combinations
   
   pairs = list(combinations(transitions, 2))
   
   for t1, t2 in pairs:
       in1, out1, test1, inh1 = get_transition_places(t1['id'])
       in2, out2, test2, inh2 = get_transition_places(t2['id'])
       
       # Competitive: share input places
       if set(in1) & set(in2):
           print(f"{t1['name']} × {t2['name']}: COMPETITIVE")
       
       # Weakly independent: share only output/regulatory
       elif (set(out1) & set(out2)) or (set(test1) & set(test2)):
           print(f"{t1['name']} × {t2['name']}: WEAKLY INDEPENDENT")
       
       # Independent: no shared places
       else:
           print(f"{t1['name']} × {t2['name']}: INDEPENDENT")
   ```

4. **Expected**:
   - ~90% independent (CI and Cro pathways separate)
   - ~7% weakly independent (mutual inhibition)
   - ~3% competitive (shared resources like ATP)

---

## Tips for Real SHYpn Simulations

### 1. **Reproducibility**
```python
# Set random seed before each batch
np.random.seed(42)
simulate(...)
```

### 2. **Batch Execution**
```python
# If SHYpn has Python API:
from shypn import Model, Simulator

model = Model.load('model.shy')
sim = Simulator(model, algorithm='tau-leaping', epsilon=0.03)

results = []
for i in range(100):
    sim.reset()
    trajectory = sim.run(t_max=200)
    results.append(trajectory)
```

### 3. **Data Export**
- Always export trajectories as CSV with columns: `time, place_name_1, place_name_2, ...`
- Save metadata: algorithm, epsilon, random seed, run ID

### 4. **Computational Time**
- Exact SSA: ~3 minutes per run (lambda phage)
- Tau-Leaping: ~3 seconds per run
- For 100 runs: Use tau-leaping unless validating accuracy

### 5. **Visualization in SHYpn**
- Real-time plot window shows trajectories
- Can overlay multiple runs
- Export plots as PNG/SVG

---

## Comparison: Mock vs Real Data

| Aspect | Mock Experiments | Real SHYpn |
|--------|------------------|------------|
| **Speed** | Instant (~1s per experiment) | Minutes to hours |
| **Accuracy** | Approximates expected behavior | True model dynamics |
| **Purpose** | Demonstration, paper drafts | Final validation |
| **Flexibility** | Easy to tweak parameters | Requires model changes |
| **Use Case** | Quick validation, teaching | Publication, peer review |

---

## Recommended Workflow

1. **Start with Mock** (already done):
   - Validate experimental design
   - Generate draft figures
   - Identify key metrics

2. **Run Real SHYpn**:
   - Collect actual data (this guide)
   - Compare with mock results
   - Adjust rate constants if needed

3. **Publication**:
   - Replace mock figures with real data
   - Report actual simulation times
   - Include reproducibility details

---

## Quick Start Command

```bash
# Launch SHYpn GUI
cd /home/simao/projetos/shypn
python -m src.shypn_gui

# Load model
# File → Open → workspace/projects/.../22_Lambda_Phage_Switch/model.shy

# Run Experiment 1 (Bistability)
# 1. Set all proteins = 0
# 2. Simulation → Settings → Tau-Leaping, t_max=200
# 3. Run → Save trajectory
# 4. Repeat 100 times

# Analyze with Python
python experiments/analyze_real_data.py
```

---

## Next Steps

1. Choose 1-2 experiments to run first (recommend: Exp 1 Bistability)
2. Export CSV data
3. Compare with mock results in `results/*.json`
4. Iterate on rate constants if real data deviates significantly
5. Regenerate figures with real data

**Expected Time**: 
- Setup: 30 minutes
- Exp 1 (100 runs): 1-2 hours
- Analysis: 30 minutes
- Total: 2-3 hours per experiment

---

**Questions?** Check:
- SHYpn documentation: `doc/USER_GUIDE.md`
- API reference: `src/shypn_gui.py`
- Example scripts: `examples/`
