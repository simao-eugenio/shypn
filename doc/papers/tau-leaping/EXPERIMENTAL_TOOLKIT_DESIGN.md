# Experimental Toolkit Design: Large-Scale τ-Leaping Validation

**Date**: December 5, 2025  
**Branch**: `feature/papers-concurrent-transition-types`  
**Purpose**: Complete toolkit for 93-model experimental validation

---

## Design Principles

### 1. **Modularity**: Each tool does ONE thing well
- Unix philosophy: small, composable tools
- Can run individually or chain in pipeline
- Easy to debug and test

### 2. **Standardization**: Common interfaces
- All tools accept `--models` CSV input
- All tools write to `--output` directory
- All tools support `--help` for documentation

### 3. **Reproducibility**: Deterministic behavior
- Fixed random seeds (with override option)
- Version tracking (tool versions, timestamps)
- Complete provenance (input parameters logged)

### 4. **Scalability**: Handle 93 models × 1000 replicates
- Progress tracking (tqdm progress bars)
- Checkpointing (resume failed runs)
- Parallel execution where possible
- Memory-efficient streaming

### 5. **Error Resilience**: Don't crash on bad models
- Try/catch per model
- Log errors but continue processing
- Generate partial results
- Error summary report

---

## Complete Toolkit Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Core Platform                            │
│                      (src/shypn/)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Classes to Build (Week 1):                                    │
│    • ReplicateRunner (run n simulations)                       │
│    • BatchProcessor (process multiple models)                  │
│    • ExportAPI (programmatic data export)                      │
│    • ProgressTracker (unified progress reporting)              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Used by
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Experimental Toolkit                         │
│              (scripts/tau_leaping/)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Data Generation (Week 2)                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 1. setup_experiment.py                                    │ │
│  │    • Create experiment directory structure                │ │
│  │    • Copy model list CSV                                  │ │
│  │    • Initialize configuration                             │ │
│  │    • Generate experiment manifest                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 2. run_replicates.py                                      │ │
│  │    • Run n replicates for ONE model                       │ │
│  │    • Both parallel and sequential modes                   │ │
│  │    • Export trajectories to CSV                           │ │
│  │    • Compute basic statistics                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 3. run_batch_replicates.py                                │ │
│  │    • Run replicates for ALL models in CSV                 │ │
│  │    • Uses BatchProcessor                                  │ │
│  │    • Checkpoint progress (resume capability)              │ │
│  │    • Error handling per model                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 4. benchmark_timing.py                                    │ │
│  │    • Measure execution time (parallel vs sequential)      │ │
│  │    • Compute speedup                                      │ │
│  │    • Export timing data                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Phase 2: Statistical Validation (Week 3)                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 5. validate_equivalence.py                                │ │
│  │    • Load parallel and sequential trajectories            │ │
│  │    • Compute MAE (Mean Absolute Error)                    │ │
│  │    • Compute CV error (Coefficient of Variation)          │ │
│  │    • Kolmogorov-Smirnov test                              │ │
│  │    • Generate validation report                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 6. analyze_dependency_impact.py                           │ │
│  │    • Correlate speedup with dependency ratios             │ │
│  │    • Test hypothesis: speedup ∝ % weakly independent      │ │
│  │    • Regression analysis                                  │ │
│  │    • Generate scatter plots                               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Phase 3: Visualization (Week 3)                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 7. plot_validation_results.py                             │ │
│  │    • Violin plots (distribution comparison)               │ │
│  │    • Heatmaps (MAE across models × species)               │ │
│  │    • Time-series overlay (sample trajectories)            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 8. plot_speedup_analysis.py                               │ │
│  │    • Speedup distribution (box plots)                     │ │
│  │    • Dependency correlation (scatter with regression)     │ │
│  │    • Model complexity impact (size vs speedup)            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Phase 4: Report Generation (Week 3)                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 9. generate_experiment_report.py                          │ │
│  │    • Aggregate all validation results                     │ │
│  │    • Generate markdown report                             │ │
│  │    • Create LaTeX tables                                  │ │
│  │    • Summary statistics                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Pipeline Orchestration (Week 3)                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 10. run_full_experiment.sh                                │ │
│  │     • Master script that runs ALL tools in sequence       │ │
│  │     • Error checking between stages                       │ │
│  │     • Time tracking                                       │ │
│  │     • Final report generation                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Tool Specifications

### **Tool 1: setup_experiment.py**

**Purpose**: Initialize experiment directory with proper structure

**Usage**:
```bash
python setup_experiment.py \
    --name "tau_leaping_validation_93_models" \
    --models ../../foundation/experimental_data/model_list.csv \
    --output experiments/tau_leaping_validation/
```

**Creates Structure**:
```
experiments/tau_leaping_validation/
├── config.json                    # Experiment configuration
├── manifest.json                  # Metadata (date, tools versions)
├── models/
│   └── model_list.csv            # Copy of input model list
├── data/
│   ├── replicates/               # Raw trajectory data
│   │   ├── BIOMD0000000001/
│   │   │   ├── parallel_trajectories.csv
│   │   │   └── sequential_trajectories.csv
│   │   ├── BIOMD0000000002/
│   │   └── ...
│   ├── statistics/               # Computed statistics
│   │   ├── BIOMD0000000001_stats.json
│   │   └── ...
│   └── timing/                   # Timing data
│       ├── BIOMD0000000001_timing.json
│       └── ...
├── validation/
│   ├── BIOMD0000000001_validation.json
│   └── ...
├── figures/
│   ├── violin_plots/
│   ├── heatmaps/
│   └── scatter_plots/
├── reports/
│   ├── validation_summary.md
│   ├── validation_summary.tex    # LaTeX table
│   └── experiment_log.txt
└── checkpoints/
    └── progress.json             # For resuming failed runs
```

**Output**: Prints experiment directory path

---

### **Tool 2: run_replicates.py**

**Purpose**: Run n replicates for a SINGLE model

**Usage**:
```bash
python run_replicates.py \
    --model data/models/BIOMD0000000064.xml \
    --replicates 1000 \
    --duration 100.0 \
    --tau-epsilon 0.03 \
    --output experiments/tau_leaping_validation/data/replicates/BIOMD0000000064/ \
    --mode both  # or 'parallel', 'sequential'
```

**Algorithm**:
```python
def run_replicates_for_model(model_path, n=1000, mode='both'):
    """Run n replicates with both parallel and sequential τ-leaping."""
    
    # 1. Load model
    parser = SBMLParser()
    pathway = parser.parse_file(model_path)
    model = convert_to_document_model(pathway)
    
    # 2. Analyze dependencies
    analyzer = DependencyAnalyzer(model)
    dep_info = analyzer.analyze()
    
    # 3. Run parallel replicates
    if mode in ['both', 'parallel']:
        runner = ReplicateRunner(model)
        parallel_results = runner.run_replicates(
            n=n,
            use_parallel=True,
            use_tau_leaping=True,
            duration=duration,
            epsilon=tau_epsilon,
            seed_base=42
        )
        
        # Export trajectories
        runner.export_trajectories_csv(
            parallel_results,
            output_dir / "parallel_trajectories.csv"
        )
        
        # Compute statistics
        stats_par = runner.compute_statistics(parallel_results)
        save_json(stats_par, output_dir / "parallel_statistics.json")
    
    # 4. Run sequential replicates
    if mode in ['both', 'sequential']:
        runner = ReplicateRunner(model)
        sequential_results = runner.run_replicates(
            n=n,
            use_parallel=False,
            use_tau_leaping=True,
            duration=duration,
            epsilon=tau_epsilon,
            seed_base=42  # Same seeds for comparison!
        )
        
        # Export
        runner.export_trajectories_csv(
            sequential_results,
            output_dir / "sequential_trajectories.csv"
        )
        
        stats_seq = runner.compute_statistics(sequential_results)
        save_json(stats_seq, output_dir / "sequential_statistics.json")
    
    return {
        'model_id': model_id,
        'n_species': len(model.places),
        'n_transitions': len(model.transitions),
        'dependency_info': dep_info,
        'statistics': {'parallel': stats_par, 'sequential': stats_seq}
    }
```

**Output**: 
- `parallel_trajectories.csv`: Wide format (time, species1, species2, ...)
- `sequential_trajectories.csv`: Wide format
- `parallel_statistics.json`: Mean, std, min, max, CV per species
- `sequential_statistics.json`: Same structure
- `metadata.json`: Model info, run parameters

---

### **Tool 3: run_batch_replicates.py**

**Purpose**: Run replicates for ALL models with checkpointing

**Usage**:
```bash
python run_batch_replicates.py \
    --models experiments/tau_leaping_validation/models/model_list.csv \
    --sbml-dir ../../foundation/experimental_data/biomodels_dataset/sbml_files/ \
    --replicates 1000 \
    --duration 100.0 \
    --output experiments/tau_leaping_validation/data/replicates/ \
    --checkpoint experiments/tau_leaping_validation/checkpoints/progress.json \
    --parallel-workers 4  # Process 4 models in parallel
```

**Algorithm**:
```python
def run_batch_replicates(models_csv, sbml_dir, **kwargs):
    """Run replicates for all models with checkpointing."""
    
    # 1. Load model list
    processor = BatchModelProcessor()
    models = processor.load_from_csv(models_csv)
    
    # 2. Load checkpoint (if exists)
    checkpoint = load_checkpoint(kwargs['checkpoint'])
    completed_models = checkpoint.get('completed', [])
    
    # 3. Filter models to process
    models_to_process = [
        (mid, path) for mid, path in models 
        if mid not in completed_models
    ]
    
    print(f"Total models: {len(models)}")
    print(f"Already completed: {len(completed_models)}")
    print(f"Remaining: {len(models_to_process)}")
    
    # 4. Process batch with progress tracking
    from tqdm import tqdm
    
    results = {}
    errors = {}
    
    for model_id, sbml_path in tqdm(models_to_process, desc="Processing models"):
        try:
            # Run replicates for this model
            result = run_replicates_for_model(
                model_path=sbml_dir / sbml_path,
                model_id=model_id,
                n=kwargs['replicates'],
                duration=kwargs['duration'],
                output_dir=kwargs['output'] / model_id,
                mode='both'
            )
            
            results[model_id] = result
            
            # Update checkpoint
            completed_models.append(model_id)
            save_checkpoint({
                'completed': completed_models,
                'last_updated': datetime.now().isoformat()
            }, kwargs['checkpoint'])
            
        except Exception as e:
            print(f"ERROR processing {model_id}: {e}")
            errors[model_id] = str(e)
            
            # Log error but continue
            with open(kwargs['output'] / 'errors.log', 'a') as f:
                f.write(f"{model_id}: {e}\n")
    
    # 5. Generate summary
    summary = {
        'total_models': len(models),
        'successful': len(results),
        'failed': len(errors),
        'completion_rate': len(results) / len(models) * 100
    }
    
    save_json(summary, kwargs['output'] / 'batch_summary.json')
    
    return results, errors
```

**Output**:
- One directory per model in `data/replicates/`
- `batch_summary.json`: Success/failure counts
- `errors.log`: Detailed error messages
- `progress.json`: Checkpoint for resuming

**Key Features**:
- ✅ Resume failed runs (checkpoint every model)
- ✅ Progress bar (tqdm)
- ✅ Error isolation (one model failure doesn't kill batch)
- ✅ Parallel processing (process 4 models at once)

---

### **Tool 4: benchmark_timing.py**

**Purpose**: Measure execution time and compute speedup

**Usage**:
```bash
python benchmark_timing.py \
    --model data/models/BIOMD0000000064.xml \
    --repetitions 10 \
    --duration 100.0 \
    --steps 1000 \
    --output experiments/tau_leaping_validation/data/timing/BIOMD0000000064_timing.json
```

**Algorithm**:
```python
def benchmark_model(model_path, repetitions=10, **kwargs):
    """Benchmark parallel vs sequential timing."""
    
    # 1. Load model
    model = load_model(model_path)
    
    # 2. Benchmark sequential
    times_sequential = []
    for i in range(repetitions):
        controller = SimulationController(model)
        controller.settings.use_parallel = False
        controller.settings.use_tau_leaping = True
        
        start = time.time()
        controller.run(duration=kwargs['duration'], time_step=kwargs['duration']/kwargs['steps'])
        elapsed = time.time() - start
        
        times_sequential.append(elapsed)
    
    # 3. Benchmark parallel
    times_parallel = []
    for i in range(repetitions):
        controller = SimulationController(model)
        controller.settings.use_parallel = True
        controller.settings.use_tau_leaping = True
        
        start = time.time()
        controller.run(duration=kwargs['duration'], time_step=kwargs['duration']/kwargs['steps'])
        elapsed = time.time() - start
        
        times_parallel.append(elapsed)
    
    # 4. Compute statistics
    mean_seq = np.mean(times_sequential)
    mean_par = np.mean(times_parallel)
    speedup = mean_seq / mean_par
    
    return {
        'times_sequential': times_sequential,
        'times_parallel': times_parallel,
        'mean_sequential': mean_seq,
        'mean_parallel': mean_par,
        'speedup': speedup,
        'std_sequential': np.std(times_sequential),
        'std_parallel': np.std(times_parallel)
    }
```

**Output**:
```json
{
  "model_id": "BIOMD0000000064",
  "repetitions": 10,
  "times_sequential": [1.234, 1.245, ...],
  "times_parallel": [0.543, 0.556, ...],
  "mean_sequential": 1.240,
  "mean_parallel": 0.550,
  "speedup": 2.25,
  "std_sequential": 0.012,
  "std_parallel": 0.008
}
```

---

### **Tool 5: validate_equivalence.py**

**Purpose**: Statistical validation of parallel vs sequential equivalence

**Usage**:
```bash
python validate_equivalence.py \
    --parallel experiments/tau_leaping_validation/data/replicates/BIOMD0000000064/parallel_trajectories.csv \
    --sequential experiments/tau_leaping_validation/data/replicates/BIOMD0000000064/sequential_trajectories.csv \
    --output experiments/tau_leaping_validation/validation/BIOMD0000000064_validation.json \
    --alpha 0.05  # Significance level for KS test
```

**Algorithm**:
```python
def validate_equivalence(parallel_csv, sequential_csv, alpha=0.05):
    """Perform statistical validation."""
    
    # 1. Load trajectories
    df_par = pd.read_csv(parallel_csv)
    df_seq = pd.read_csv(sequential_csv)
    
    # 2. Get species columns (exclude 'time' column)
    species = [col for col in df_par.columns if col != 'time']
    
    validation_results = {}
    
    for sp in species:
        # 3. Compute MAE (Mean Absolute Error)
        mean_par = df_par[sp].mean()
        mean_seq = df_seq[sp].mean()
        mae = abs(mean_par - mean_seq)
        
        # 4. Compute CV error (Coefficient of Variation)
        cv_par = df_par[sp].std() / mean_par if mean_par > 0 else 0
        cv_seq = df_seq[sp].std() / mean_seq if mean_seq > 0 else 0
        cv_error = abs(cv_par - cv_seq) / cv_seq if cv_seq > 0 else 0
        
        # 5. Kolmogorov-Smirnov test
        from scipy.stats import ks_2samp
        ks_stat, p_value = ks_2samp(df_par[sp], df_seq[sp])
        
        # 6. Determine if passes
        passes_mae = mae < 0.01 * mean_seq  # 1% threshold
        passes_cv = cv_error < 0.05         # 5% threshold
        passes_ks = p_value > alpha         # Not significantly different
        passes_all = passes_mae and passes_cv and passes_ks
        
        validation_results[sp] = {
            'mean_parallel': mean_par,
            'mean_sequential': mean_seq,
            'mae': mae,
            'cv_parallel': cv_par,
            'cv_sequential': cv_seq,
            'cv_error': cv_error,
            'ks_statistic': ks_stat,
            'ks_pvalue': p_value,
            'passes_mae': passes_mae,
            'passes_cv': passes_cv,
            'passes_ks': passes_ks,
            'passes_validation': passes_all
        }
    
    # 7. Overall summary
    total_species = len(species)
    passed_species = sum(1 for r in validation_results.values() if r['passes_validation'])
    
    summary = {
        'total_species': total_species,
        'passed_species': passed_species,
        'pass_rate': passed_species / total_species * 100,
        'species_results': validation_results
    }
    
    return summary
```

**Output**:
```json
{
  "total_species": 12,
  "passed_species": 12,
  "pass_rate": 100.0,
  "species_results": {
    "Glucose": {
      "mean_parallel": 45.32,
      "mean_sequential": 45.34,
      "mae": 0.02,
      "cv_parallel": 0.145,
      "cv_sequential": 0.147,
      "cv_error": 0.014,
      "ks_statistic": 0.023,
      "ks_pvalue": 0.873,
      "passes_validation": true
    },
    ...
  }
}
```

---

### **Tool 6: analyze_dependency_impact.py**

**Purpose**: Correlate speedup with dependency structure

**Usage**:
```bash
python analyze_dependency_impact.py \
    --timing-dir experiments/tau_leaping_validation/data/timing/ \
    --models experiments/tau_leaping_validation/models/model_list.csv \
    --sbml-dir ../../foundation/experimental_data/biomodels_dataset/sbml_files/ \
    --output experiments/tau_leaping_validation/reports/dependency_analysis.json
```

**Algorithm**:
```python
def analyze_dependency_impact(timing_dir, models_csv, sbml_dir):
    """Correlate speedup with dependency ratios."""
    
    # 1. Load all timing data
    speedups = []
    weak_independence_ratios = []
    model_ids = []
    
    for model_id, sbml_path in load_models(models_csv):
        # Load timing
        timing = load_json(timing_dir / f"{model_id}_timing.json")
        speedup = timing['speedup']
        
        # Analyze dependencies
        model = load_model(sbml_dir / sbml_path)
        analyzer = DependencyAnalyzer(model)
        result = analyzer.analyze()
        
        # Calculate weak independence ratio
        total_pairs = result['statistics']['total_pairs']
        weak_indep = result['statistics']['strongly_independent_count'] + \
                     result['statistics']['convergent_count'] + \
                     result['statistics']['regulatory_count']
        ratio = weak_indep / total_pairs if total_pairs > 0 else 0
        
        speedups.append(speedup)
        weak_independence_ratios.append(ratio)
        model_ids.append(model_id)
    
    # 2. Regression analysis
    from scipy.stats import pearsonr, spearmanr
    from sklearn.linear_model import LinearRegression
    
    X = np.array(weak_independence_ratios).reshape(-1, 1)
    y = np.array(speedups)
    
    # Fit linear model
    reg = LinearRegression()
    reg.fit(X, y)
    
    # Correlation
    pearson_r, pearson_p = pearsonr(weak_independence_ratios, speedups)
    spearman_r, spearman_p = spearmanr(weak_independence_ratios, speedups)
    
    return {
        'models': model_ids,
        'speedups': speedups,
        'weak_independence_ratios': weak_independence_ratios,
        'regression': {
            'slope': reg.coef_[0],
            'intercept': reg.intercept_,
            'r_squared': reg.score(X, y)
        },
        'correlations': {
            'pearson': {'r': pearson_r, 'p': pearson_p},
            'spearman': {'r': spearman_r, 'p': spearman_p}
        }
    }
```

---

### **Tool 7: plot_validation_results.py**

**Purpose**: Generate validation visualizations

**Usage**:
```bash
python plot_validation_results.py \
    --validation-dir experiments/tau_leaping_validation/validation/ \
    --replicates-dir experiments/tau_leaping_validation/data/replicates/ \
    --output experiments/tau_leaping_validation/figures/ \
    --format pdf
```

**Generates**:
1. **Violin plots**: Distribution comparison (parallel vs sequential)
2. **Heatmaps**: MAE across models × species
3. **Trajectory overlays**: Sample time-series for visual inspection
4. **KS test p-value distribution**: Histogram showing equivalence

---

### **Tool 8: plot_speedup_analysis.py**

**Purpose**: Generate speedup visualizations

**Usage**:
```bash
python plot_speedup_analysis.py \
    --timing-dir experiments/tau_leaping_validation/data/timing/ \
    --dependency-analysis experiments/tau_leaping_validation/reports/dependency_analysis.json \
    --output experiments/tau_leaping_validation/figures/ \
    --format pdf
```

**Generates**:
1. **Box plot**: Speedup distribution
2. **Scatter plot**: Speedup vs weak independence ratio (with regression line)
3. **Histogram**: Speedup frequency
4. **Bar chart**: Top 10 models by speedup

---

### **Tool 9: generate_experiment_report.py**

**Purpose**: Aggregate all results into comprehensive report

**Usage**:
```bash
python generate_experiment_report.py \
    --experiment-dir experiments/tau_leaping_validation/ \
    --output experiments/tau_leaping_validation/reports/FINAL_REPORT.md \
    --latex experiments/tau_leaping_validation/reports/tables.tex
```

**Generates**:
- **Markdown report**: Human-readable summary
- **LaTeX tables**: Camera-ready for paper
- **Summary statistics**: Overall validation rates
- **Model-by-model results**: Detailed table

---

### **Tool 10: run_full_experiment.sh**

**Purpose**: Master orchestration script

**Usage**:
```bash
bash run_full_experiment.sh experiments/tau_leaping_validation/
```

**Pipeline**:
```bash
#!/bin/bash
set -e

EXPERIMENT_DIR=$1

echo "=== Phase 1: Setup ==="
python setup_experiment.py \
    --name "tau_leaping_validation_93_models" \
    --models ../../foundation/experimental_data/model_list.csv \
    --output ${EXPERIMENT_DIR}

echo "=== Phase 2: Run Batch Replicates ==="
python run_batch_replicates.py \
    --models ${EXPERIMENT_DIR}/models/model_list.csv \
    --sbml-dir ../../foundation/experimental_data/biomodels_dataset/sbml_files/ \
    --replicates 1000 \
    --output ${EXPERIMENT_DIR}/data/replicates/ \
    --checkpoint ${EXPERIMENT_DIR}/checkpoints/progress.json

echo "=== Phase 3: Benchmark Timing ==="
# Run timing benchmarks for each model
for model_id in $(cat ${EXPERIMENT_DIR}/models/model_list.csv | tail -n +2 | cut -d',' -f1); do
    python benchmark_timing.py \
        --model ${EXPERIMENT_DIR}/models/${model_id}.xml \
        --repetitions 10 \
        --output ${EXPERIMENT_DIR}/data/timing/${model_id}_timing.json
done

echo "=== Phase 4: Validate Equivalence ==="
for model_id in $(cat ${EXPERIMENT_DIR}/models/model_list.csv | tail -n +2 | cut -d',' -f1); do
    python validate_equivalence.py \
        --parallel ${EXPERIMENT_DIR}/data/replicates/${model_id}/parallel_trajectories.csv \
        --sequential ${EXPERIMENT_DIR}/data/replicates/${model_id}/sequential_trajectories.csv \
        --output ${EXPERIMENT_DIR}/validation/${model_id}_validation.json
done

echo "=== Phase 5: Dependency Analysis ==="
python analyze_dependency_impact.py \
    --timing-dir ${EXPERIMENT_DIR}/data/timing/ \
    --models ${EXPERIMENT_DIR}/models/model_list.csv \
    --output ${EXPERIMENT_DIR}/reports/dependency_analysis.json

echo "=== Phase 6: Generate Plots ==="
python plot_validation_results.py \
    --validation-dir ${EXPERIMENT_DIR}/validation/ \
    --output ${EXPERIMENT_DIR}/figures/

python plot_speedup_analysis.py \
    --timing-dir ${EXPERIMENT_DIR}/data/timing/ \
    --dependency-analysis ${EXPERIMENT_DIR}/reports/dependency_analysis.json \
    --output ${EXPERIMENT_DIR}/figures/

echo "=== Phase 7: Generate Final Report ==="
python generate_experiment_report.py \
    --experiment-dir ${EXPERIMENT_DIR} \
    --output ${EXPERIMENT_DIR}/reports/FINAL_REPORT.md \
    --latex ${EXPERIMENT_DIR}/reports/tables.tex

echo "=== COMPLETE ==="
echo "Report: ${EXPERIMENT_DIR}/reports/FINAL_REPORT.md"
echo "Figures: ${EXPERIMENT_DIR}/figures/"
```

---

## Implementation Priority

### **Week 1: Core Platform** (Foundation)
1. ✅ ReplicateRunner (2-3 days)
2. ✅ BatchProcessor (2-3 days)
3. ✅ Export API (1 day)

### **Week 2: Essential Tools** (Minimum Viable Experiment)
4. ✅ setup_experiment.py (1 day)
5. ✅ run_replicates.py (1 day)
6. ✅ run_batch_replicates.py (2 days)
7. ✅ validate_equivalence.py (1 day)

### **Week 3: Analysis & Visualization** (Publication Quality)
8. ✅ benchmark_timing.py (1 day)
9. ✅ analyze_dependency_impact.py (1 day)
10. ✅ plot_validation_results.py (2 days)
11. ✅ plot_speedup_analysis.py (1 day)
12. ✅ generate_experiment_report.py (1 day)
13. ✅ run_full_experiment.sh (1 day)

---

## Success Criteria

### **Correctness**
- ✅ Statistical validation passes for >95% of models
- ✅ MAE < 1% of sequential mean
- ✅ CV error < 5%
- ✅ KS test p-value > 0.05

### **Performance**
- ✅ Speedup > 1.5× for models with >70% weak independence
- ✅ No performance degradation for competitive-heavy models

### **Reproducibility**
- ✅ Fixed random seeds produce identical results
- ✅ Checkpoint system allows resuming failed runs
- ✅ Complete provenance tracking (parameters, versions, timestamps)

### **Scalability**
- ✅ Process 93 models × 1000 replicates in <48 hours
- ✅ Memory usage stays reasonable (<16GB)
- ✅ Parallel processing reduces wall-clock time

---

## Risk Mitigation

### **Risk 1: Computational Time**
- **Issue**: 93 models × 1000 replicates × 2 modes = 186,000 simulations
- **Mitigation**: 
  - Parallel processing (4 models at once)
  - Run on compute cluster if available
  - Checkpoint system allows spreading over multiple days

### **Risk 2: Memory Usage**
- **Issue**: 1000 trajectories × 100 timepoints × 50 species = large data
- **Mitigation**:
  - Stream trajectories to disk (don't hold all in memory)
  - Use memory-mapped arrays for statistics computation
  - Process models one at a time

### **Risk 3: Model Import Failures**
- **Issue**: Some BioModels may have incompatible SBML
- **Mitigation**:
  - Try/catch per model
  - Log errors but continue
  - Generate partial results (e.g., 88/93 models)

### **Risk 4: Statistical Failures**
- **Issue**: Some models may not pass validation
- **Mitigation**:
  - Investigate failures individually
  - Adjust τ-leaping epsilon if needed
  - Document limitations in paper

---

## Estimated Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Platform development | ReplicateRunner, BatchProcessor, Export API |
| 2 | Essential tools | setup, run_replicates, run_batch, validate |
| 3 | Analysis tools | timing, dependency analysis, plotting, reporting |
| 4 | Preliminary run | Test on 10 models, debug issues |
| 5 | Full experiment | Run all 93 models (1,000 replicates each) |
| 6 | Analysis & writing | Generate figures, write paper sections |

**Total**: 6 weeks to publication-ready results

---

## Next Steps

1. ✅ **Review this design** - Get feedback on toolkit architecture
2. ✅ **Start Week 1** - Implement core platform classes
3. ✅ **Create tool templates** - Scaffold all 10 tools with arg parsing
4. ✅ **Test on 1 model** - Validate entire pipeline on single model
5. ✅ **Test on 10 models** - Catch edge cases
6. ✅ **Run full experiment** - 93 models × 1000 replicates

Ready to start implementation?
