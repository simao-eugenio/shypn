# Lambda Phage Plotting Guide

## Quick Start: From UI Batch Mode to Publication Figures

**IMPORTANT**: To preserve the paper results in `22_Lambda_Phage_Switch/`, run all experiments in your working directory:
```bash
# Copy model to working directory
cp workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/model.shy \
   workspace/projects/My_Project/simulations/
```

### 1. Generate Data with SHYpn UI
```bash
# Launch SHYpn
cd /home/simao/projetos/shypn
source .venv/bin/activate
python src/shypn.py
```

1. Load `workspace/projects/My_Project/simulations/model.shy` (working copy)
2. Set initial conditions
3. Right-click objects → **📊 Mark for Recording**
4. Settings → Enable **Batch Mode** → 100 replicates
5. Choose output: `workspace/projects/My_Project/simulations/results/`
6. Click **Run** once
7. Results saved to `workspace/projects/My_Project/simulations/results/batch_YYYYMMDD_HHMMSS/`

### 2. Quick Visualization (5 Standard Plots)
```bash
# From project root
python examples/plot_batch_results.py "workspace/projects/My_Project/simulations/results/batch_YYYYMMDD_HHMMSS"
```

Generates:
- `batch_all_trajectories.png` - All trajectories overlay
- `batch_mean_std.png` - Mean ± standard deviation
- `batch_comparison.png` - Compare all objects
- `batch_heatmap.png` - Time × replicate heatmap
- `batch_final_states.png` - Final value histogram

### 3. Custom Publication Figure (Bistability Example)
```bash
# From project root
cd /home/simao/projetos/shypn
python workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/analyze_batch_bistability.py \
       "workspace/projects/My_Project/simulations/results/batch_YYYYMMDD_HHMMSS"
```

Generates:
- `figure2_bistability_validation.png` - 4-panel figure with:
  * (A) Stochastic trajectories colored by outcome
  * (B) Decision statistics vs literature
  * (C) Phase portrait (CI vs Cro)
  * (D) Final state distribution

---

## Directory Structure

**Paper Results (READ-ONLY - preserved)**:
```
22_Lambda_Phage_Switch/
├── model.shy                           # Original SHYpn model
├── INTERACTIVE_REPRODUCTION_GUIDE.md   # Detailed guide for all experiments
├── README_PLOTTING.md                  # This file
├── analyze_batch_bistability.py        # Analysis script
│
├── experiments/                        # Mock data generators (for design)
│   ├── run_bistability.py
│   ├── run_uv_dose.py
│   └── ...
│
└── results/                            # Original paper results (preserved)
    ├── figure2_bistability_validation.png
    ├── figure3_uv_dose_response.png
    └── ...
```

**Your Working Directory (for experiments)**:
```
My_Project/simulations/
├── model.shy                           # Copy of lambda phage model
│
└── results/                            # Your batch results
    ├── batch_20251213_215254/         # Example batch
    │   ├── run_001.csv                # Time, CI_Dimer, Cro_Dimer, etc.
    │   ├── run_002.csv
    │   ├── ...
    │   ├── run_100.csv
    │   ├── config.json                # Simulation settings
    │   └── summary.json               # Statistics
    ├── figure2_bistability_validation.png  # Your figures
    ├── figure3_uv_dose_response.png
    └── ...
```

---

## Two Types of Scripts

### Mock Data Scripts (`experiments/run_*.py`)
- **Purpose**: Experimental design and figure prototyping
- **Input**: None (generates synthetic data)
- **Output**: Mock figures for validation
- **When to use**: Before running real simulations

### Analysis Scripts (`analyze_batch_*.py`)
- **Purpose**: Create publication figures from real data
- **Input**: Batch CSV results from SHYpn UI
- **Output**: Publication-ready figures
- **When to use**: After running UI Batch Mode

---

## Complete Workflow Example

### Experiment 1: Bistability

#### Step 1: Generate Data (SHYpn UI)
1. Open `workspace/projects/My_Project/simulations/model.shy` in SHYpn
2. Set initial conditions:
   ```
   CI_Gene = 1
   Cro_Gene = 1
   All proteins = 0
   DNA_Damage = 0
   ```
3. Mark for recording:
   - Right-click `CI_Dimer` → 📊 Mark for Recording
   - Right-click `Cro_Dimer` → 📊 Mark for Recording
   - Right-click `Lysogenic_State` → 📊 Mark for Recording
   - Right-click `Lytic_Genes_Active` → 📊 Mark for Recording
4. Settings:
   - Expand **BATCH MODE**
   - ✓ Enable Batch Mode
   - Replicates: 100
   - Duration: 200 time units
   - Output: `workspace/projects/My_Project/simulations/results/bistability/`
5. Click **Run** → Wait ~30 seconds
6. Results saved to `workspace/projects/My_Project/simulations/results/bistability/batch_YYYYMMDD_HHMMSS/`

#### Step 2: Quick Visualization
```bash
python examples/plot_batch_results.py "workspace/projects/My_Project/simulations/results/bistability/batch_20251213_215254"
```

Output:
```
Loading batch results from: workspace/projects/My_Project/simulations/results/bistability/batch_20251213_215254
Loaded 100 replicates
Available objects: ['CI_Dimer', 'Cro_Dimer', 'Lysogenic_State', 'Lytic_Genes_Active']

1. Plotting all trajectories... ✓
2. Plotting mean ± std... ✓
3. Comparing multiple objects... ✓
4. Creating heatmap... ✓
5. Analyzing final states... ✓

=== Summary Statistics ===
Successful replicates: 100/100

Final values:
  CI_Dimer:
    Mean: 25.43
    Std:  12.67
  Lysogenic_State:
    Mean: 0.62 (62% lysogeny)
    Std:  0.49
```

#### Step 3: Custom Publication Figure
```bash
python workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/analyze_batch_bistability.py \
       "workspace/projects/My_Project/simulations/results/bistability/batch_20251213_215254"
```

Output:
```
=== Bistability Analysis ===
Lysogenic: 62/100 (62.0%)
Lytic:     38/100 (38.0%)
Undecided: 0/100 (0.0%)

Expected (Arkin 1998): ~50% lysogenic, ~50% lytic

✓ Figure saved: workspace/projects/My_Project/simulations/results/figure2_bistability_validation.png
```

---

## Tips

### Directory Organization
- **Paper results**: Keep `22_Lambda_Phage_Switch/` unchanged (read-only reference)
- **Your experiments**: Use `My_Project/simulations/` for all new runs
- **Backup**: Original model and results preserved for comparison

### Efficient Batch Runs
- **Performance**: Batch mode runs 50-100× faster than manual
- **Recording**: Only mark essential objects (reduces file size)
- **Duration**: Match literature simulation times
- **Replicates**: 100 is standard for stochastic experiments

### Analysis Best Practices
- Use `plot_batch_results.py` for quick validation
- Create custom scripts for publication figures
- Compare with literature expectations
- Save figures as PNG (300 dpi) for publications

### Common Issues
- **Missing objects**: Check which objects were marked for recording in config.json
- **Short trajectories**: Increase duration in simulation settings
- **High variance**: Increase number of replicates
- **Slow execution**: Reduce recording_interval or use stochastic acceleration

---

## Need Help?

- **Full guide**: See `INTERACTIVE_REPRODUCTION_GUIDE.md`
- **Tool reference**: `examples/plot_batch_results.py --help`
- **Example script**: `analyze_batch_bistability.py` (template for custom analysis)
