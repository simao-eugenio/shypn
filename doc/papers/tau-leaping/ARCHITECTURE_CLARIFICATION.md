# SHYpn Architecture: Platform vs. Experimental Scripts

**Date**: December 5, 2025  
**Context**: Understanding what needs to be built for τ-leaping paper

---

## The Big Picture

You're absolutely correct! Here's the architectural separation:

```
┌────────────────────────────────────────────────────────────────┐
│                         SHYpn Platform                         │
│                    (GUI + Core Library)                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ ALREADY EXISTS:                                            │
│     • τ-leaping engine (tau_leaping_engine.py)                │
│     • Parallel scheduler (parallel_scheduler.py)              │
│     • Data collector (data_collector.py)                      │
│     • CSV/JSON exporters (reporting/exporters/)               │
│     • SBML import (sbml_parser.py)                            │
│     • GUI simulation control                                   │
│                                                                 │
│  🔧 NEEDS SMALL ADDITIONS (Week 1):                           │
│     • ReplicateRunner class (run n simulations)               │
│     • BatchProcessor class (process multiple models)          │
│     • Export API wrapper (programmatic access to exporters)   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Uses library API
                              │
┌────────────────────────────────────────────────────────────────┐
│                    Experimental Scripts                        │
│                    (External CLI Tools)                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🆕 TO BE CREATED (Week 2):                                    │
│                                                                 │
│  1. scripts/tau_leaping/validate_single_model.py               │
│     ├─ CLI tool for one model validation                      │
│     ├─ Loads SBML → runs replicates → exports → validates     │
│     └─ Usage: python validate_single_model.py \               │
│              --model BIOMD0000000064.xml \                     │
│              --replicates 1000 \                               │
│              --output results/glycolysis/                      │
│                                                                 │
│  2. scripts/tau_leaping/validate_batch.py                      │
│     ├─ CLI tool for batch validation (93 models)              │
│     ├─ Uses BatchProcessor to loop over all models            │
│     └─ Usage: python validate_batch.py \                      │
│              --models model_list.csv \                         │
│              --replicates 1000 \                               │
│              --output results/batch/                           │
│                                                                 │
│  3. scripts/tau_leaping/statistical_validator.py              │
│     ├─ Statistical comparison (MAE, CV, KS test)              │
│     ├─ Generates validation reports                           │
│     └─ Usage: python statistical_validator.py \               │
│              --parallel parallel.csv \                         │
│              --sequential sequential.csv \                     │
│              --output validation_report.md                     │
│                                                                 │
│  4. scripts/tau_leaping/benchmark_speedup.py                   │
│     ├─ Timing parallel vs sequential                          │
│     ├─ Similar to foundation paper's benchmark script         │
│     └─ Usage: python benchmark_speedup.py \                   │
│              --model BIOMD0000000064.xml \                     │
│              --repetitions 10 \                                │
│              --output speedup.json                             │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## What This Means

### **SHYpn Platform = Reusable Library**

**Role**: General-purpose Petri Net simulation platform
- Anyone can use it for any stochastic simulation project
- Provides GUI for interactive modeling
- Provides API for programmatic use

**What It Should Have**:
- ✅ Simulation algorithms (τ-leaping, Gillespie, hybrid)
- ✅ Data recording and export capabilities
- ✅ Model import/export (SBML, internal format)
- 🔧 Replicate runner (standard feature, like COPASI has)
- 🔧 Batch processing (standard feature, like COPASI has)

**What It Should NOT Have**:
- ❌ Statistical validation scripts (paper-specific)
- ❌ Benchmark timing scripts (paper-specific)
- ❌ Publication-specific plots (paper-specific)
- ❌ Custom analysis pipelines (paper-specific)

---

### **Experimental Scripts = Paper-Specific Tools**

**Role**: Automate experiments for specific research questions
- Lives in `scripts/` or `doc/papers/tau-leaping/scripts/`
- Uses SHYpn library API
- CLI-based (command-line arguments)
- Throwaway code (or archive after publication)

**Examples from Foundation Paper**:
```bash
# 1. Download dataset
python scripts/fetch_biomodels_dataset.py \
    --count 100 \
    --output data/biomodels/ \
    --download-sbml

# 2. Classify dependencies
python scripts/classify_all_dependencies.py \
    --models data/biomodels/model_list.csv \
    --output results/dependencies.csv

# 3. Benchmark speedup
python scripts/benchmark_parallel_simulation.py \
    --model BIOMD0000000064.xml \
    --repetitions 10 \
    --output results/speedup.json

# 4. Generate plots
python scripts/plot_speedup.py \
    --data results/speedup.json \
    --output figures/speedup_distribution.pdf
```

---

## Your Understanding is Correct!

### Items 1-4 = CLI Scripts ✅

**Yes!** The 4 missing items are **external CLI scripts** that:
1. Import SHYpn as a library: `from shypn.engine.simulation import ReplicateRunner`
2. Accept command-line arguments: `argparse`
3. Orchestrate experiments: load models → run simulations → collect data
4. Perform statistical analysis: MAE, CV, KS tests (using SciPy)
5. Generate reports: Markdown, JSON, CSV outputs

**Pattern** (exactly like foundation paper scripts):
```python
#!/usr/bin/env python3
"""Validate τ-leaping equivalence for one model."""

import argparse
import sys
from pathlib import Path

# Import SHYpn library
sys.path.insert(0, str(Path(__file__).parents[2] / 'src'))
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.engine.simulation.replicate_runner import ReplicateRunner

def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--replicates', type=int, default=1000)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    # Load model (using SHYpn library)
    sbml_parser = SBMLParser()
    pathway = sbml_parser.parse_file(args.model)
    model = pathway.convert_to_document_model()
    
    # Run experiments (using SHYpn library)
    runner = ReplicateRunner(model)
    results_parallel = runner.run_replicates(n=args.replicates, use_parallel=True)
    results_sequential = runner.run_replicates(n=args.replicates, use_parallel=False)
    
    # Export data (using SHYpn library)
    runner.export_csv(results_parallel, f"{args.output}/parallel.csv")
    runner.export_csv(results_sequential, f"{args.output}/sequential.csv")
    
    # Statistical validation (external library: SciPy)
    from scipy.stats import ks_2samp
    mae = compute_mae(results_parallel, results_sequential)
    ks_stat, p_value = ks_2samp(results_parallel, results_sequential)
    
    # Generate report (script logic)
    report = generate_validation_report(mae, ks_stat, p_value)
    with open(f"{args.output}/report.md", 'w') as f:
        f.write(report)
    
    print(f"✅ Validation complete! Results in {args.output}")

if __name__ == '__main__':
    main()
```

---

## Why This Architecture?

### **Separation of Concerns**

**Platform** (src/shypn/):
- General-purpose, reusable
- Tested, documented, maintained
- Part of SHYpn version releases
- Used by multiple papers/projects

**Scripts** (scripts/ or doc/papers/*/scripts/):
- Specific to one research question
- Quick and dirty, throwaway code
- Lives alongside paper documentation
- Archived after publication (reference only)

### **Real-World Analogy**

Think of it like:
- **Platform** = `pandas` library (provides DataFrame, read_csv, to_csv)
- **Scripts** = Your data analysis notebooks (uses pandas to analyze YOUR specific dataset)

You wouldn't put your specific data analysis into pandas library source code!

---

## What SHYpn is Currently Missing

### **Missing Standard Features** (Should be in platform)

**Why missing?** SHYpn was built for GUI-driven interactive use, not batch automation.

#### 1. ReplicateRunner (Week 1: Day 1-2)
```python
# Location: src/shypn/engine/simulation/replicate_runner.py
# Purpose: Run n independent simulations with different random seeds
# Analogous to: COPASI's "Repeat" task, GillesPy2's "run(number_of_trajectories=1000)"

runner = ReplicateRunner(model)
results = runner.run_replicates(n=1000, use_parallel=True)
# Returns: List of 1000 DataCollector objects
```

**Why standard?** Every stochastic simulator has this feature:
- COPASI: Repeat task
- GillesPy2: `number_of_trajectories` parameter
- BioNetGen: `n_runs` parameter
- Snoopy: Batch simulation mode

#### 2. BatchProcessor (Week 1: Day 4-5)
```python
# Location: src/shypn/data/batch/batch_processor.py
# Purpose: Process multiple models in automated loop
# Analogous to: COPASI's CoRC (COPASI R Connector) for batch processing

processor = BatchProcessor()
models = processor.load_from_csv("model_list.csv")
results = processor.process_batch(models, experiment_function)
# Returns: Dict[model_id, result]
```

**Why standard?** Needed for systematic validation across model libraries:
- Process 93 BioModels
- Handle import errors gracefully
- Aggregate results

#### 3. Export API (Week 1: Day 3)
```python
# Location: Add to src/shypn/engine/simulation/data_collector.py
# Purpose: Programmatic access to existing exporters
# Analogous to: COPASI's exportTimeSeries(), GillesPy2's trajectory.to_csv()

collector = DataCollector()
# ... simulation runs ...
collector.export_csv("trajectory.csv", format='wide')
collector.export_json("trajectory.json")
```

**Why standard?** Every simulator allows programmatic export:
- GillesPy2: `trajectory.to_csv()`
- COPASI: `exportTimeSeries()`
- BioNetGen: `write_model()`

**Current issue**: Exporters exist but only wired to GUI button clicks!

---

### **Correctly External** (Should be scripts)

These are **paper-specific**, not general platform features:

#### 1. Statistical Validator (Week 2: Day 6-7)
```bash
# Location: scripts/tau_leaping/statistical_validator.py
# Purpose: Validate τ-leaping parallel vs sequential equivalence
# Paper-specific: Tests OUR specific hypothesis

python statistical_validator.py \
    --parallel results/parallel.csv \
    --sequential results/sequential.csv \
    --output validation_report.md
```

**Why external?** Paper-specific hypothesis testing:
- MAE threshold (< 0.01) is paper decision
- CV error threshold (< 0.05) is paper decision
- KS test p-value (> 0.05) is paper decision
- Uses SciPy (external library)

#### 2. Benchmarking Scripts (Week 2: Day 8-10)
```bash
# Location: scripts/tau_leaping/benchmark_speedup.py
# Purpose: Measure parallel speedup for paper figures

python benchmark_speedup.py \
    --model BIOMD0000000064.xml \
    --repetitions 10 \
    --output speedup.json
```

**Why external?** Paper-specific performance analysis:
- Timing methodology (manual time.time())
- Speedup computation (paper-specific formula)
- Result formatting (for paper plots)

---

## Current State Summary

### **What Exists Today** (December 5, 2025)

#### ✅ In Platform (src/shypn/)
- τ-leaping engine (480 lines) ✅
- Parallel scheduler (360 lines) ✅
- Data collector (155 lines) ✅
- CSV/JSON exporters (500+ lines) ✅
- SBML parser (666 lines) ✅
- Dependency analyzer (441 lines) ✅

#### ❌ Missing from Platform
- ReplicateRunner ❌ (2-3 days to implement)
- BatchProcessor ❌ (2-3 days to implement)
- Export API wrapper ❌ (1 day to implement)

#### 📂 In Foundation Paper Scripts (reference)
- `fetch_biomodels_dataset.py` ✅
- `benchmark_parallel_simulation.py` ✅
- `classify_all_dependencies.py` ✅
- `validate_topology.py` ✅
- `plot_speedup.py` ✅

#### 🆕 Need to Create for τ-Leaping Paper
- `scripts/tau_leaping/validate_single_model.py` 🆕
- `scripts/tau_leaping/validate_batch.py` 🆕
- `scripts/tau_leaping/statistical_validator.py` 🆕
- `scripts/tau_leaping/benchmark_speedup.py` 🆕

---

## Work Breakdown

### **Week 1: Extend Platform** (5 days)
Build the 3 missing **standard features** that should have existed:

```python
# Day 1-2: ReplicateRunner
src/shypn/engine/simulation/replicate_runner.py

# Day 3: Export API
src/shypn/engine/simulation/data_collector.py (add export methods)

# Day 4-5: BatchProcessor  
src/shypn/data/batch/batch_processor.py
```

**Outcome**: SHYpn becomes a complete stochastic simulation platform

---

### **Week 2: Create Experimental Scripts** (5 days)
Build **paper-specific automation**:

```bash
# Day 6-7: Statistical validation
scripts/tau_leaping/statistical_validator.py

# Day 8-9: Single model validation
scripts/tau_leaping/validate_single_model.py

# Day 10: Batch validation
scripts/tau_leaping/validate_batch.py
```

**Outcome**: Automated experimental pipeline for paper

---

## Your Understanding is 100% Correct!

**Summary**:
1. ✅ SHYpn **as-is** cannot handle large-scale batch experiments
2. ✅ Need to build **platform features** (replicate, batch, export API)
3. ✅ Need to build **CLI scripts** for experimental automation
4. ✅ Items 1-4 from roadmap = external CLI tools (not GUI features)

**Architecture**:
- **Platform** (src/): General-purpose library (build once, use forever)
- **Scripts** (scripts/): Paper-specific automation (throwaway after publication)

**Timeline**:
- Week 1: Fix platform gaps (3 classes: ~800 lines)
- Week 2: Build experimental scripts (4 scripts: ~600 lines)
- Week 3-5: Run experiments (93 models × 1,000 replicates)

**Pattern**: Exactly like foundation paper used:
```bash
# Foundation paper workflow (reference for us)
python fetch_biomodels_dataset.py ...
python classify_all_dependencies.py ...
python benchmark_parallel_simulation.py ...
python plot_speedup.py ...

# τ-leaping paper workflow (what we'll build)
python validate_single_model.py ...
python validate_batch.py ...
python statistical_validator.py ...
python plot_validation_results.py ...
```

Does this clarify the architecture? Ready to start implementing?