# Interactive Reproduction Guide: Lambda Phage Experiments in SHYpn

This guide shows how to reproduce Experiments 1-7 using the **actual SHYpn simulator** with the new **Batch Mode** functionality for automated experiment replication.

---

## Prerequisites

1. **Launch SHYpn**:
   ```bash
   cd /home/simao/projetos/shypn
   source .venv/bin/activate
   python src/shypn.py
   ```

2. **Load Lambda Phage Model**:
   - File → Open → `workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/model.shy`
   - Verify: 14 places, 16 transitions, 35 arcs

3. **Access Simulation Settings**:
   - Swiss Palette → Simulate → Click **Settings** button
   - You'll see three expandable categories:
     * **SIMULATION PARAMETERS** (expanded by default)
     * **STOCHASTIC ACCELERATION** (collapsed)
     * **BATCH MODE (EXPERIMENT REPLICATION)** (collapsed)

---

## Using Batch Mode for Automated Experiments

### Overview

Batch Mode allows you to automatically run multiple independent simulations (replicates) with the same initial conditions to study stochastic variability. Instead of clicking "Run" 100 times, you can:

1. **Mark objects for recording** (right-click places/transitions → "📊 Mark for Recording")
2. **Enable Batch Mode** and set number of replicates
3. **Run once** - SHYpn automatically executes all replicates in the background
4. **Get organized results** - CSV files with statistics automatically saved

### Setting Up Batch Mode

1. **Expand BATCH MODE section** in Settings panel

2. **Check "Enable Batch Mode"**
   - Replicates spinner becomes active
   - Output folder chooser becomes active

3. **Set Number of Replicates** (e.g., 100 for experiments)

4. **Choose Output Folder** (default: project's results directory)

---

## Experiment 1: Bistability Validation (With Batch Mode)

### Goal
Reproduce Figure 2 showing 62% lysogeny vs 38% lysis decision using automated batch execution.

### Interactive Steps

1. **Set Initial Conditions**:
   ```
   CI_Gene = 1          (catalyst, always 1)
   Cro_Gene = 1         (catalyst, always 1)
   All proteins = 0     (start from infection)
   DNA_Damage = 0       (no UV initially)
   ```

2. **Mark Objects for Recording**:
   - Right-click `CI_Dimer` → **"📊 Mark for Recording"** (checkmark appears)
   - Right-click `Cro_Dimer` → **"📊 Mark for Recording"**
   - Right-click `Lysogenic_State` → **"📊 Mark for Recording"**
   - Right-click `Lytic_Genes_Active` → **"📊 Mark for Recording"**
   
   *Note: Only marked objects will be recorded in batch results for efficiency*

3. **Configure Batch Mode**:
   - Settings → Expand **BATCH MODE (EXPERIMENT REPLICATION)**
   - ✓ **Enable Batch Mode**
   - **Replicates:** 100
   - **Output:** `workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/results/bistability/`
   
4. **Configure Simulation Parameters**:
   - Expand **SIMULATION PARAMETERS**
   - Duration: 200 time units
   - Time Step: Auto (recommended)
   - Playback Speed: 1000× (for faster execution)
   
5. **Run Batch Simulation**:
   - Click **"Run"** button in Swiss Palette
   - Progress dialog appears: "Running replicate 1/100..."
   - Shows elapsed time and ETA
   - Can cancel gracefully (finishes current replicate)

6. **Results Automatically Saved**:
   ```
   results/batch_2025-12-13_18-30-45/
   ├── config.json              # Simulation settings + recorded objects
   ├── run_001.csv             # Time, CI_Dimer, Cro_Dimer, Lysogenic_State, Lytic_Genes_Active
   ├── run_002.csv
   ├── ...
   ├── run_100.csv
   └── summary.json            # Statistics: mean, std, min, max per object
   ```

7. **Expected Results**:
   - ~60% reach Lysogenic_State=1
   - ~40% reach Lytic_Genes_Active=1
   - Decision time: 30-50 time units

### Python Analysis Script (Updated for Batch Results)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

# Load batch results
batch_dir = Path('results/batch_2025-12-13_18-30-45')

# Load configuration
with open(batch_dir / 'config.json', 'r') as f:
    config = json.load(f)
print(f"Replicates: {config['replicates']}")
print(f"Recorded objects: {config['recorded_objects']}")

# Load summary statistics
with open(batch_dir / 'summary.json', 'r') as f:
    summary = json.load(f)
print(f"CI_Dimer final mean: {summary['CI_Dimer']['mean']:.2f} ± {summary['CI_Dimer']['std']:.2f}")

# Load all trajectories
trajectories = []
for i in range(1, 101):
    df = pd.read_csv(batch_dir / f'run_{i:03d}.csv')
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
plt.title('Bistability: 100 Stochastic Trajectories (Batch Mode)')
plt.savefig('figure2_bistability_batch.png', dpi=300)
plt.show()
```
```

---

## Experiment 2: UV-Dose Response (With Batch Mode)

### Goal
Reproduce Figure 3 sigmoid curve: 19% induction at 1 lesion, 95% at 10 lesions.

### Interactive Steps

1. **UV Dose Levels to Test**:
   - Test: 0, 1, 2, 3, 5, 7, 10 DNA lesions
   - 100 simulations per dose (7 batch runs total)

2. **Mark Objects for Recording**:
   - Right-click `Lytic_Genes_Active` → **"📊 Mark for Recording"**
   - Right-click `CI_Dimer` → **"📊 Mark for Recording"**
   - Right-click `Cro_Dimer` → **"📊 Mark for Recording"**

3. **For Each Dose Level** (repeat 7 times):
   
   **Set DNA_Damage** (in canvas):
   - Click `DNA_Damage` place
   - Set tokens: 0, then 1, then 2, etc.
   
   **Set Other Initial Conditions**:
   ```
   CI_Gene = 1
   Cro_Gene = 1
   All proteins = 0
   ```
   
   **Configure Batch Mode**:
   - Settings → **BATCH MODE (EXPERIMENT REPLICATION)**
   - ✓ **Enable Batch Mode**
   - **Replicates:** 100
   - **Output:** `results/uv_dose_response/dose_0/` (change number for each dose)
   
   **Run Batch**:
   - Click **Run** button
   - Wait for 100 replicates to complete
   - Results auto-saved with statistics
   
   **Repeat** for doses 1, 2, 3, 5, 7, 10

4. **Data Collection** (automated by batch mode):
   - Each batch folder contains:
     * `run_001.csv` ... `run_100.csv` (time, Lytic_Genes_Active, CI_Dimer, Cro_Dimer)
     * `summary.json` (mean, std, min, max for each object)
     * `config.json` (DNA_Damage = dose recorded)

5. **Expected Results**:
   | Dose | Induction % | Literature |
   |------|-------------|------------|
   | 0    | ~5%         | Spontaneous |
   | 1    | 15-25%      | 18±10% |
   | 3    | 50-70%      | ~50% |
   | 10   | >95%        | >95% |

6. **Python Analysis** (aggregate batch results):
   ```python
   import pandas as pd
   import numpy as np
   import matplotlib.pyplot as plt
   from pathlib import Path
   
   doses = [0, 1, 2, 3, 5, 7, 10]
   induction_rates = []
   
   for dose in doses:
       batch_dir = Path(f'results/uv_dose_response/dose_{dose}')
       induced_count = 0
       
       # Count how many runs reached lytic state
       for i in range(1, 101):
           df = pd.read_csv(batch_dir / f'run_{i:03d}.csv')
           final = df.iloc[-1]
           if final['Lytic_Genes_Active'] == 1:
               induced_count += 1
       
       induction_rates.append(induced_count)
   
   # Plot dose-response curve
   plt.figure(figsize=(8, 6))
   plt.plot(doses, induction_rates, 'o-', markersize=10)
   plt.xlabel('DNA Lesions (UV dose)')
   plt.ylabel('% Induction (Lytic)')
   plt.title('UV Dose-Response Curve (Batch Mode)')
   plt.grid(True, alpha=0.3)
   plt.savefig('figure3_dose_response_batch.png', dpi=300)
   plt.show()
   ```

---

## Experiment 3: Temporal Kinetics (With Batch Mode)

### Goal
Measure CI and Cro half-lives: t₁/₂(CI) ≈ 7-10 units, t₁/₂(Cro) ≈ 3-5 units.

### Interactive Steps

1. **CI Decay Experiment** (stochastic replicates):
   
   **Mark Objects**:
   - Right-click `CI_Protein` → **"📊 Mark for Recording"**
   - Right-click `CI_Dimer` → **"📊 Mark for Recording"**
   
   **Set Initial Conditions**:
   ```
   CI_Protein = 50     # High CI level
   CI_Dimer = 10
   DNA_Damage = 10     # UV to trigger RecA-mediated decay
   All else = 0
   ```
   
   **Configure Batch Mode**:
   - Settings → **BATCH MODE (EXPERIMENT REPLICATION)**
   - ✓ **Enable Batch Mode**
   - **Replicates:** 50 (multiple trajectories to measure stochastic decay)
   - **Output:** `results/kinetics/ci_decay/`
   
   **Run Batch**:
   - Duration: 50 time units
   - Click **Run**
   - Results auto-saved

2. **Cro Decay Experiment**:
   
   **Mark Objects**:
   - Unmark CI_Protein/CI_Dimer (right-click → uncheck)
   - Right-click `Cro_Protein` → **"📊 Mark for Recording"**
   - Right-click `Cro_Dimer` → **"📊 Mark for Recording"**
   
   **Set Initial Conditions**:
   ```
   Cro_Protein = 50    # High Cro level
   Cro_Dimer = 10
   All else = 0
   ```
   
   **Configure Batch Mode**:
   - **Replicates:** 50
   - **Output:** `results/kinetics/cro_decay/`
   
   **Run Batch**:
   - Duration: 50 time units
   - Click **Run**

3. **Analysis** (fit exponential decay):
   ```python
   import pandas as pd
   import numpy as np
   import matplotlib.pyplot as plt
   from scipy.optimize import curve_fit
   from pathlib import Path
   
   # CI Decay Analysis
   batch_dir = Path('results/kinetics/ci_decay')
   
   def exp_decay(t, C0, tau):
       return C0 * np.exp(-t / tau)
   
   # Load all CI trajectories
   ci_trajectories = []
   for i in range(1, 51):
       df = pd.read_csv(batch_dir / f'run_{i:03d}.csv')
       ci_trajectories.append(df)
   
   # Average trajectory for fitting
   avg_time = ci_trajectories[0]['time'].values
   avg_ci = np.mean([df['CI_Protein'].values for df in ci_trajectories], axis=0)
   
   # Fit exponential decay
   popt, _ = curve_fit(exp_decay, avg_time, avg_ci, p0=[50, 10])
   C0, tau = popt
   half_life_ci = tau * np.log(2)
   
   print(f"CI half-life: {half_life_ci:.2f} units (expected: 10±3)")
   
   # Plot with confidence bands
   plt.figure(figsize=(10, 6))
   std_ci = np.std([df['CI_Protein'].values for df in ci_trajectories], axis=0)
   plt.fill_between(avg_time, avg_ci - std_ci, avg_ci + std_ci, alpha=0.3, color='blue')
   plt.plot(avg_time, avg_ci, 'b-', linewidth=2, label=f'CI (t₁/₂={half_life_ci:.1f})')
   plt.plot(avg_time, exp_decay(avg_time, *popt), 'r--', label='Exponential fit')
   plt.xlabel('Time (simulation units)')
   plt.ylabel('CI Protein Level')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.savefig('figure4_ci_decay_batch.png', dpi=300)
   
   # Repeat for Cro decay
   batch_dir = Path('results/kinetics/cro_decay')
   # ... (similar analysis for Cro)
   ```

---

## Experiment 4: Autoregulation Effect (With Batch Mode)

### Goal
Compare CI dynamics WITH vs WITHOUT autoregulation (positive feedback) using automated batch replication.

### Interactive Steps

1. **Model WITH Autoregulation** (current model.shy):
   
   **Mark Objects**:
   - Right-click `CI_Dimer` → **"📊 Mark for Recording"**
   
   **Set Initial Conditions**:
   ```
   CI_Gene = 1
   Cro_Gene = 1
   All proteins = 0
   ```
   
   **Configure Batch Mode**:
   - Settings → **BATCH MODE (EXPERIMENT REPLICATION)**
   - ✓ **Enable Batch Mode**
   - **Replicates:** 100
   - **Output:** `results/autoregulation/with_feedback/`
   
   **Run Batch**:
   - Duration: 200 time units
   - CI_Transcription rate includes autoregulation: `0.1 * (1 + 0.5 * CI_Dimer)`
   - Click **Run**

2. **Model WITHOUT Autoregulation**:
   
   **Modify Transition Rate**:
   - Right-click `CI_Transcription` transition
   - Properties → Rate: Change to constant `0.1` (remove CI_Dimer dependency)
   - Save model as `model_no_autoreg.shy`
   
   **Configure Batch Mode**:
   - **Replicates:** 100
   - **Output:** `results/autoregulation/no_feedback/`
   
   **Run Batch**:
   - Same initial conditions
   - Duration: 200 time units
   - Click **Run**

3. **Data Collection** (automated by batch mode):
   - Each batch folder contains 100 trajectories
   - Summary statistics in `summary.json`

4. **Comparison Analysis**:
   ```python
   import pandas as pd
   import numpy as np
   import matplotlib.pyplot as plt
   from pathlib import Path
   
   # Load WITH feedback trajectories
   batch_with = Path('results/autoregulation/with_feedback')
   traj_with = [pd.read_csv(batch_with / f'run_{i:03d}.csv') for i in range(1, 101)]
   
   # Load WITHOUT feedback trajectories
   batch_without = Path('results/autoregulation/no_feedback')
   traj_without = [pd.read_csv(batch_without / f'run_{i:03d}.csv') for i in range(1, 101)]
   
   # Calculate steady-state (average t=150-200)
   def steady_state(trajectories):
       ss_values = []
       for df in trajectories:
           ss_window = df[df['time'] >= 150]['CI_Dimer']
           ss_values.append(ss_window.mean())
       return np.mean(ss_values), np.std(ss_values)
   
   ss_with, std_with = steady_state(traj_with)
   ss_without, std_without = steady_state(traj_without)
   
   # Calculate response time (t when CI_Dimer reaches 90% of steady-state)
   def response_time(trajectories, ss_target):
       t90_values = []
       for df in trajectories:
           threshold = 0.9 * ss_target
           try:
               t90 = df[df['CI_Dimer'] >= threshold]['time'].iloc[0]
               t90_values.append(t90)
           except:
               pass
       return np.mean(t90_values), np.std(t90_values)
   
   t90_with, t90_std_with = response_time(traj_with, ss_with)
   t90_without, t90_std_without = response_time(traj_without, ss_without)
   
   # Calculate coefficient of variation
   cv_with = std_with / ss_with
   cv_without = std_without / ss_without
   
   # Print results
   print("WITH Autoregulation:")
   print(f"  Steady-state: {ss_with:.1f} ± {std_with:.1f} (CV={cv_with:.3f})")
   print(f"  Response time (t90): {t90_with:.1f} ± {t90_std_with:.1f} units")
   
   print("\nWITHOUT Autoregulation:")
   print(f"  Steady-state: {ss_without:.1f} ± {std_without:.1f} (CV={cv_without:.3f})")
   print(f"  Response time (t90): {t90_without:.1f} ± {t90_std_without:.1f} units")
   
   print(f"\nComparison:")
   print(f"  Steady-state increase: {ss_with / ss_without:.2f}×")
   print(f"  Response speedup: {t90_without / t90_with:.2f}×")
   print(f"  Noise reduction: {(1 - cv_with/cv_without)*100:.1f}%")
   
   # Plot comparison
   fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
   
   # Panel A: Example trajectories
   for i in range(20):  # Plot 20 random trajectories
       ax1.plot(traj_with[i]['time'], traj_with[i]['CI_Dimer'], 
                'b-', alpha=0.3, linewidth=0.5)
       ax2.plot(traj_without[i]['time'], traj_without[i]['CI_Dimer'], 
                'r-', alpha=0.3, linewidth=0.5)
   
   ax1.set_title('WITH Autoregulation')
   ax1.set_xlabel('Time (units)')
   ax1.set_ylabel('CI Dimer Level')
   ax1.grid(True, alpha=0.3)
   
   ax2.set_title('WITHOUT Autoregulation')
   ax2.set_xlabel('Time (units)')
   ax2.set_ylabel('CI Dimer Level')
   ax2.grid(True, alpha=0.3)
   
   plt.tight_layout()
   plt.savefig('figure5_autoregulation_comparison_batch.png', dpi=300)
   plt.show()
   ```

---

## Experiment 5: Performance Benchmarks (With Batch Mode)

### Goal
Measure actual computational speedup: Exact SSA vs Tau-Leaping using batch mode execution.

### Interactive Steps

1. **Exact SSA Benchmark**:
   
   **Configure Algorithm**:
   - Settings → **STOCHASTIC ACCELERATION**
   - ☐ **Disable "Enable τ-Leaping"** (uses exact SSA)
   
   **Configure Batch Mode**:
   - Settings → **BATCH MODE (EXPERIMENT REPLICATION)**
   - ✓ **Enable Batch Mode**
   - **Replicates:** 10 (sufficient for benchmarking)
   - **Output:** `results/benchmark/exact_ssa/`
   
   **Set Initial Conditions**:
   ```
   CI_Gene = 1
   Cro_Gene = 1
   All proteins = 0
   ```
   
   **Run Batch**:
   - Duration: 200 time units
   - Click **Run**
   - **Record wall-clock time** from progress dialog (e.g., "Elapsed: 174.3s")

2. **Tau-Leaping Benchmark**:
   
   **Configure Algorithm**:
   - Settings → **STOCHASTIC ACCELERATION**
   - ✓ **Enable "Enable τ-Leaping"**
   - **Epsilon (ε):** 0.03 (default)
   - ☐ **"Use parallel execution"** (single-threaded first)
   
   **Configure Batch Mode**:
   - **Replicates:** 10 (same as SSA)
   - **Output:** `results/benchmark/tau_leaping/`
   
   **Run Batch**:
   - Same initial conditions
   - Duration: 200 time units
   - Click **Run**
   - **Record wall-clock time** (e.g., "Elapsed: 3.1s")

3. **Parallel Tau-Leaping Benchmark**:
   
   **Configure Algorithm**:
   - ✓ **Enable "Enable τ-Leaping"**
   - ✓ **Enable "Use parallel execution"**
   
   **Configure Batch Mode**:
   - **Replicates:** 10
   - **Output:** `results/benchmark/parallel_tau/`
   
   **Run Batch**:
   - Same conditions
   - Click **Run**
   - **Record wall-clock time** (e.g., "Elapsed: 0.9s")

4. **Calculate Speedup**:
   ```python
   # Example timings (replace with actual measurements)
   time_ssa = 174.3        # seconds for 10 replicates
   time_tau = 3.1          # seconds for 10 replicates
   time_parallel = 0.9     # seconds for 10 replicates
   
   speedup_tau = time_ssa / time_tau
   speedup_parallel = time_tau / time_parallel
   speedup_total = time_ssa / time_parallel
   
   print("Performance Results:")
   print(f"  Exact SSA: {time_ssa:.1f}s for 10 runs")
   print(f"  Tau-leaping: {time_tau:.1f}s ({speedup_tau:.1f}× faster)")
   print(f"  Parallel: {time_parallel:.1f}s ({speedup_parallel:.1f}× parallel gain)")
   print(f"  Total speedup: {speedup_total:.1f}× (claim: 20-400×)")
   ```

5. **Validation** (ensure accuracy is maintained):
   ```python
   import pandas as pd
   import numpy as np
   from pathlib import Path
   
   # Load SSA results
   ssa_dir = Path('results/benchmark/exact_ssa')
   ssa_final = []
   for i in range(1, 11):
       df = pd.read_csv(ssa_dir / f'run_{i:03d}.csv')
       ssa_final.append(df.iloc[-1]['CI_Dimer'])
   
   # Load Tau-leaping results
   tau_dir = Path('results/benchmark/tau_leaping')
   tau_final = []
   for i in range(1, 11):
       df = pd.read_csv(tau_dir / f'run_{i:03d}.csv')
       tau_final.append(df.iloc[-1]['CI_Dimer'])
   
   # Compare distributions
   print(f"\nAccuracy Validation:")
   print(f"  SSA mean: {np.mean(ssa_final):.2f} ± {np.std(ssa_final):.2f}")
   print(f"  Tau mean: {np.mean(tau_final):.2f} ± {np.std(tau_final):.2f}")
   print(f"  Difference: {abs(np.mean(ssa_final) - np.mean(tau_final)):.2f} (should be < 5%)")
   ```

---

## Experiment 6: Cooperativity (Hill Coefficient) - With Batch Mode

### Goal
Measure Hill coefficient from dose-response curve (expected: n ≈ 2.0 from 2:1 dimerization stoichiometry).

### Interactive Steps

1. **Test Multiple CI_Protein Initial Levels**:
   - Test levels: 0, 2, 5, 10, 15, 20, 25, 30, 40, 50 molecules
   - 20 replicates per level (stochastic averaging)
   
2. **For Each Initial Level** (10 batch runs):
   
   **Mark Objects**:
   - Right-click `CI_Dimer` → **"📊 Mark for Recording"**
   
   **Set Initial Conditions** (example for CI=10):
   ```
   CI_Protein = 10    # Change this for each level
   CI_Gene = 1
   All else = 0
   ```
   
   **Configure Batch Mode**:
   - Settings → **BATCH MODE (EXPERIMENT REPLICATION)**
   - ✓ **Enable Batch Mode**
   - **Replicates:** 20
   - **Output:** `results/cooperativity/ci_init_10/` (change folder for each level)
   
   **Run Batch**:
   - Duration: 100 time units (equilibration time)
   - Click **Run**
   - Repeat for all 10 CI_Protein levels

3. **Data Collection** (automated):
   - Each batch folder contains 20 trajectories
   - Extract steady-state CI_Dimer (average t=80-100)

4. **Fit Hill Function**:
   ```python
   import pandas as pd
   import numpy as np
   import matplotlib.pyplot as plt
   from scipy.optimize import curve_fit
   from pathlib import Path
   
   # CI_Protein initial levels tested
   ci_levels = [0, 2, 5, 10, 15, 20, 25, 30, 40, 50]
   
   # Collect steady-state CI_Dimer for each level
   dimer_ss_mean = []
   dimer_ss_std = []
   
   for ci_init in ci_levels:
       batch_dir = Path(f'results/cooperativity/ci_init_{ci_init}')
       
       # Load all trajectories for this level
       ss_values = []
       for i in range(1, 21):
           df = pd.read_csv(batch_dir / f'run_{i:03d}.csv')
           # Steady-state = average of last 20 time units
           ss_window = df[df['time'] >= 80]['CI_Dimer']
           ss_values.append(ss_window.mean())
       
       dimer_ss_mean.append(np.mean(ss_values))
       dimer_ss_std.append(np.std(ss_values))
   
   # Hill function: y = ymax * x^n / (Kd^n + x^n)
   def hill(x, n, Kd, max_val):
       return max_val * (x**n) / (Kd**n + x**n)
   
   # Fit to data
   ci_data = np.array(ci_levels)
   dimer_data = np.array(dimer_ss_mean)
   
   popt, pcov = curve_fit(hill, ci_data, dimer_data, 
                          p0=[2.0, 15.0, 20.0],  # Initial guess
                          bounds=([1.0, 1.0, 5.0], [4.0, 50.0, 50.0]))
   
   n, Kd, max_val = popt
   n_err = np.sqrt(pcov[0, 0])
   
   print(f"Hill coefficient: n = {n:.2f} ± {n_err:.2f}")
   print(f"Dissociation constant: Kd = {Kd:.1f} molecules")
   print(f"Maximum dimer level: {max_val:.1f} molecules")
   print(f"Expected: n ≈ 2.0 (from 2:1 dimerization stoichiometry)")
   
   # Plot with fit
   plt.figure(figsize=(10, 6))
   plt.errorbar(ci_levels, dimer_ss_mean, yerr=dimer_ss_std, 
                fmt='o', markersize=8, capsize=5, label='Batch data')
   
   x_fit = np.linspace(0, 50, 200)
   y_fit = hill(x_fit, *popt)
   plt.plot(x_fit, y_fit, 'r-', linewidth=2, 
            label=f'Hill fit: n={n:.2f}, Kd={Kd:.1f}')
   
   plt.xlabel('CI Protein Initial Level')
   plt.ylabel('Steady-State CI Dimer')
   plt.title('Cooperativity: Hill Coefficient from Batch Simulations')
   plt.legend()
   plt.grid(True, alpha=0.3)
   plt.savefig('figure6_hill_coefficient_batch.png', dpi=300)
   plt.show()
   ```

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

## Tips for SHYpn Batch Mode Simulations

### 1. **Marking Strategy**
- **Mark only what you need**: Batch CSV files only contain marked objects
- **For bistability**: Mark state indicators (Lysogenic_State, Lytic_Genes_Active)
- **For kinetics**: Mark protein levels (CI_Protein, Cro_Protein)
- **For dose-response**: Mark final outcome indicators
- **Unmark when done**: Right-click → uncheck to clear recording marks

### 2. **Output Organization**
```
results/
├── bistability/
│   ├── batch_2025-12-13_18-30-45/
│   │   ├── config.json          # Settings + marked objects
│   │   ├── summary.json         # Statistics
│   │   ├── run_001.csv ... run_100.csv
│   └── batch_2025-12-13_19-15-22/
├── uv_dose_response/
│   ├── dose_0/
│   ├── dose_1/
│   └── ...
└── kinetics/
    ├── ci_decay/
    └── cro_decay/
```

### 3. **Batch Mode Best Practices**
- **Small test first**: Run 10 replicates to verify settings before 100
- **Use descriptive folders**: `results/experiment_name/condition/`
- **Check config.json**: Verify recorded_objects matches your marks
- **Monitor progress**: Progress dialog shows ETA and allows graceful cancel
- **Save model first**: Batch settings persist per-document

### 4. **Reproducibility**
- Batch mode uses system time as random seed (different each batch)
- For reproducible results: Set fixed seed in simulation settings (if available)
- Save batch folder path in your lab notebook
- `config.json` stores all simulation parameters

### 5. **Performance Tips**
- **τ-Leaping for large batches**: 50-100× faster than exact SSA
- **Parallel execution**: Enable in STOCHASTIC ACCELERATION for CPU parallelism
- **Close progress dialog**: Runs in background if you close dialog
- **Playback speed**: Set high (1000×) for faster batch execution

### 6. **Data Analysis Workflow**
```python
# Standard batch analysis template
import pandas as pd
import numpy as np
from pathlib import Path

# Load batch results
batch_dir = Path('results/bistability/batch_2025-12-13_18-30-45')

# Load config (verify settings)
import json
with open(batch_dir / 'config.json', 'r') as f:
    config = json.load(f)
print(f"Replicates: {config['replicates']}")
print(f"Recorded: {config['recorded_objects']}")

# Load summary statistics (quick overview)
with open(batch_dir / 'summary.json', 'r') as f:
    summary = json.load(f)
for obj, stats in summary.items():
    print(f"{obj}: mean={stats['mean']:.2f}, std={stats['std']:.2f}")

# Load individual trajectories (detailed analysis)
trajectories = []
for i in range(1, config['replicates'] + 1):
    df = pd.read_csv(batch_dir / f'run_{i:03d}.csv')
    trajectories.append(df)

# Analyze final states
lysogenic_count = sum(df.iloc[-1]['Lysogenic_State'] == 1 
                      for df in trajectories)
print(f"Lysogeny rate: {lysogenic_count/len(trajectories)*100:.1f}%")
```

### 7. **Computational Time Estimates** (Lambda Phage Model)
- **Exact SSA**: ~17 seconds per run → 28 minutes for 100 replicates
- **τ-Leaping (ε=0.03)**: ~0.3 seconds per run → 30 seconds for 100 replicates
- **Parallel τ-Leaping (4 cores)**: ~0.1 seconds per run → 10 seconds for 100 replicates

*Note: Times are approximate and depend on hardware*

---

## Batch Mode vs Manual Workflow Comparison

| Aspect | Manual Workflow (OLD) | Batch Mode (NEW) |
|--------|----------------------|------------------|
| **User effort** | Click "Run" 100 times | Click "Run" once |
| **Time required** | 30 mins (with breaks) | 30 seconds (automated) |
| **Data export** | 100 manual exports | Automatic CSV generation |
| **Organization** | Scattered files | Organized batch folders |
| **Statistics** | Manual calculation | Auto-generated summary.json |
| **Reproducibility** | Manual tracking | Config.json with all settings |
| **Selective recording** | Record everything | Record only marked objects |
| **Error prone** | Easy to lose count | Guaranteed N replicates |
| **Interruption** | Restart from scratch | Resume/cancel gracefully |

### Example: Experiment 1 (Bistability)

**OLD Manual Workflow**:
1. Set initial conditions
2. Click "Run Simulation"
3. Wait 3 seconds
4. Export trajectory as CSV
5. Record outcome in spreadsheet
6. **Repeat steps 2-5 × 100 times** ⏰ 30 minutes
7. Manually aggregate results

**NEW Batch Mode Workflow**:
1. Set initial conditions
2. Mark CI_Dimer and Cro_Dimer for recording
3. Enable Batch Mode: 100 replicates
4. Click "Run Simulation" **once**
5. Get coffee ☕ (30 seconds elapsed)
6. Find organized results in batch folder with statistics

**Time saved: 97%** | **Errors eliminated: 100%** | **Organization: Automatic**

---

## Recommended Workflow

1. **Start with Mock** (already done):
   - Validate experimental design
   - Generate draft figures
   - Identify key metrics

2. **Run Real SHYpn with Batch Mode**:
   - Mark objects for selective recording
   - Configure batch parameters (100 replicates)
   - Run automated experiments (this guide)
   - Analyze organized batch results
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
