# Experimental Validation Toolkit

Complete toolkit for validating stochastic simulation algorithms at scale.

## Overview

This toolkit enables large-scale validation experiments for stochastic simulation methods. It provides tools to:

1. Run thousands of simulation replicates
2. Compare different simulation algorithms (e.g., parallel vs sequential τ-leaping)
3. Perform statistical validation (MAE, CV, Kolmogorov-Smirnov tests)
4. Analyze dependency impact on performance
5. Generate publication-quality reports and figures

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. setup_experiment.py                                      │
│    Initialize experiment directory structure                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. run_batch_replicates.py                                  │
│    Run n replicates for all models (parallel + sequential)  │
│    • Checkpointing for resume capability                    │
│    • Progress tracking                                       │
│    • Error isolation per model                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. benchmark_timing.py                                      │
│    Measure execution time and compute speedup               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. validate_equivalence.py                                  │
│    Statistical validation for each model                    │
│    • Mean Absolute Error (MAE)                              │
│    • Coefficient of Variation error (CV)                    │
│    • Kolmogorov-Smirnov test                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. analyze_dependency_impact.py                             │
│    Correlate speedup with dependency structure              │
│    • Regression analysis                                    │
│    • Correlation tests                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Visualization                                            │
│    • plot_validation_results.py                             │
│    • plot_speedup_analysis.py                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. generate_experiment_report.py                            │
│    Aggregate all results into comprehensive report          │
│    • Markdown report                                        │
│    • LaTeX tables                                           │
└─────────────────────────────────────────────────────────────┘
```

## Tools

### 1. setup_experiment.py

Initialize experiment directory with proper structure.

**Usage**:
```bash
python -m shypn.cli.experimental.setup_experiment \
    --name "tau_leaping_validation_93_models" \
    --models ../../doc/papers/foundation/experimental_data/model_list.csv \
    --output experiments/tau_leaping_validation/
```

**Creates**:
```
experiments/tau_leaping_validation/
├── config.json
├── models/
├── data/
│   ├── replicates/
│   ├── statistics/
│   └── timing/
├── validation/
├── figures/
├── reports/
└── checkpoints/
```

---

### 2. run_replicates.py

Run n stochastic replicates for a SINGLE model.

**Usage**:
```bash
python -m shypn.cli.experimental.run_replicates \
    --model data/models/BIOMD0000000064.xml \
    --replicates 1000 \
    --duration 100.0 \
    --output results/BIOMD0000000064/ \
    --mode both  # or 'parallel', 'sequential'
```

**Output**:
- `parallel_trajectories.csv` - Parallel mode trajectories
- `sequential_trajectories.csv` - Sequential mode trajectories
- `parallel_statistics.json` - Mean, std, CV per species
- `sequential_statistics.json` - Same structure
- `metadata.json` - Model info and run parameters

---

### 3. run_batch_replicates.py

Run replicates for ALL models with checkpointing.

**Usage**:
```bash
python -m shypn.cli.experimental.run_batch_replicates \
    --models experiments/tau_leaping/models/model_list.csv \
    --sbml-dir ../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/ \
    --replicates 1000 \
    --duration 100.0 \
    --output experiments/tau_leaping/data/replicates/ \
    --checkpoint experiments/tau_leaping/checkpoints/progress.json \
    --parallel-workers 4
```

**Features**:
- ✅ Checkpoint every model (resume failed runs)
- ✅ Progress bar (tqdm)
- ✅ Error isolation (one failure doesn't kill batch)
- ✅ Parallel processing (process N models at once)

---

### 4. benchmark_timing.py

Measure execution time and compute speedup.

**Usage**:
```bash
python -m shypn.cli.experimental.benchmark_timing \
    --model data/models/BIOMD0000000064.xml \
    --repetitions 10 \
    --duration 100.0 \
    --output experiments/tau_leaping/data/timing/BIOMD0000000064_timing.json
```

**Output**: JSON with timing statistics and speedup

---

### 5. validate_equivalence.py

Statistical validation of parallel vs sequential equivalence.

**Usage**:
```bash
python -m shypn.cli.experimental.validate_equivalence \
    --parallel experiments/tau_leaping/data/replicates/BIOMD0000000064/parallel_trajectories.csv \
    --sequential experiments/tau_leaping/data/replicates/BIOMD0000000064/sequential_trajectories.csv \
    --output experiments/tau_leaping/validation/BIOMD0000000064_validation.json \
    --alpha 0.05
```

**Tests**:
- **MAE** (Mean Absolute Error): `|mean_par - mean_seq|` < 1% threshold
- **CV Error**: `|CV_par - CV_seq| / CV_seq` < 5% threshold
- **KS Test**: Kolmogorov-Smirnov p-value > 0.05 (not significantly different)

---

### 6. analyze_dependency_impact.py

Correlate speedup with dependency structure.

**Usage**:
```bash
python -m shypn.cli.experimental.analyze_dependency_impact \
    --timing-dir experiments/tau_leaping/data/timing/ \
    --models experiments/tau_leaping/models/model_list.csv \
    --sbml-dir ../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/ \
    --output experiments/tau_leaping/reports/dependency_analysis.json
```

**Output**: Regression analysis, correlation coefficients

---

### 7. plot_validation_results.py

Generate validation visualizations.

**Usage**:
```bash
python -m shypn.cli.experimental.plot_validation_results \
    --validation-dir experiments/tau_leaping/validation/ \
    --replicates-dir experiments/tau_leaping/data/replicates/ \
    --output experiments/tau_leaping/figures/ \
    --format pdf
```

**Generates**:
- Violin plots (distribution comparison)
- Heatmaps (MAE across models × species)
- Trajectory overlays (sample time-series)
- KS test p-value distribution

---

### 8. plot_speedup_analysis.py

Generate speedup visualizations.

**Usage**:
```bash
python -m shypn.cli.experimental.plot_speedup_analysis \
    --timing-dir experiments/tau_leaping/data/timing/ \
    --dependency-analysis experiments/tau_leaping/reports/dependency_analysis.json \
    --output experiments/tau_leaping/figures/ \
    --format pdf
```

**Generates**:
- Box plot (speedup distribution)
- Scatter plot (speedup vs weak independence ratio)
- Histogram (speedup frequency)
- Bar chart (top 10 models by speedup)

---

### 9. generate_experiment_report.py

Aggregate all results into comprehensive report.

**Usage**:
```bash
python -m shypn.cli.experimental.generate_experiment_report \
    --experiment-dir experiments/tau_leaping/ \
    --output experiments/tau_leaping/reports/FINAL_REPORT.md \
    --latex experiments/tau_leaping/reports/tables.tex
```

**Generates**:
- Markdown report (human-readable summary)
- LaTeX tables (camera-ready for paper)
- Summary statistics (overall validation rates)

---

### 10. run_full_experiment.sh

Master orchestration script that runs entire pipeline.

**Usage**:
```bash
bash run_full_experiment.sh experiments/tau_leaping_validation/
```

## Example: Complete Validation Workflow

```bash
# Step 1: Setup
shypn-setup-experiment \
    --name "tau_leaping_validation_93_models" \
    --models model_list.csv \
    --output exp/

# Step 2: Run batch replicates (this takes ~24-48 hours)
shypn-batch-replicates \
    --models exp/models/model_list.csv \
    --sbml-dir biomodels_sbml/ \
    --replicates 1000 \
    --output exp/data/replicates/ \
    --checkpoint exp/checkpoints/progress.json

# Step 3: Benchmark timing
for model_id in $(cat exp/models/model_list.csv | tail -n +2 | cut -d',' -f1); do
    shypn-benchmark-timing \
        --model biomodels_sbml/${model_id}.xml \
        --repetitions 10 \
        --output exp/data/timing/${model_id}_timing.json
done

# Step 4: Validate equivalence
for model_id in $(cat exp/models/model_list.csv | tail -n +2 | cut -d',' -f1); do
    shypn-validate-equivalence \
        --parallel exp/data/replicates/${model_id}/parallel_trajectories.csv \
        --sequential exp/data/replicates/${model_id}/sequential_trajectories.csv \
        --output exp/validation/${model_id}_validation.json
done

# Step 5: Dependency analysis
shypn-analyze-dependency-impact \
    --timing-dir exp/data/timing/ \
    --models exp/models/model_list.csv \
    --output exp/reports/dependency_analysis.json

# Step 6: Generate plots
shypn-plot-validation --validation-dir exp/validation/ --output exp/figures/
shypn-plot-speedup --timing-dir exp/data/timing/ --output exp/figures/

# Step 7: Generate final report
shypn-generate-report \
    --experiment-dir exp/ \
    --output exp/reports/FINAL_REPORT.md \
    --latex exp/reports/tables.tex
```

## Success Criteria

### Statistical Validation
- ✅ MAE < 1% of sequential mean
- ✅ CV error < 5%
- ✅ KS test p-value > 0.05
- ✅ >95% of models pass validation

### Performance
- ✅ Speedup > 1.5× for models with >70% weak independence
- ✅ No degradation for competitive-heavy models

### Reproducibility
- ✅ Fixed random seeds produce identical results
- ✅ Complete provenance tracking

## Implementation Status

| Tool | Status | Priority |
|------|--------|----------|
| setup_experiment.py | 🔜 To implement | Week 2 |
| run_replicates.py | 🔜 To implement | Week 2 |
| run_batch_replicates.py | 🔜 To implement | Week 2 |
| benchmark_timing.py | 🔜 To implement | Week 2 |
| validate_equivalence.py | 🔜 To implement | Week 2 |
| analyze_dependency_impact.py | 🔜 To implement | Week 3 |
| plot_validation_results.py | 🔜 To implement | Week 3 |
| plot_speedup_analysis.py | 🔜 To implement | Week 3 |
| generate_experiment_report.py | 🔜 To implement | Week 3 |
| run_full_experiment.sh | 🔜 To implement | Week 3 |

## Dependencies

Platform requirements (Week 1):
- `ReplicateRunner` class (run n simulations)
- `BatchProcessor` class (process multiple models)
- Export API (programmatic data export)

Python packages:
- `scipy` (statistical tests)
- `pandas` (data handling)
- `numpy` (numerical computations)
- `matplotlib` (plotting)
- `tqdm` (progress bars)

## Support

For issues or questions about the experimental toolkit:
- See main [CLI README](../README.md)
- Check [EXPERIMENTAL_TOOLKIT_DESIGN.md](../../doc/papers/tau-leaping/EXPERIMENTAL_TOOLKIT_DESIGN.md)
