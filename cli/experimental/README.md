# Experimental CLI Tools for τ-Leaping Validation

This directory contains command-line tools for validating the τ-leaping algorithm implementation (Paper 2).

## Overview

These tools provide a complete experimental workflow for comparing τ-leaping with Gillespie SSA:
- **Validation**: Compare algorithm equivalence
- **Benchmarking**: Measure performance and speedup
- **Analysis**: Examine model structure and dependencies
- **Visualization**: Generate publication-quality plots
- **Reporting**: Compile comprehensive experiment reports

## Installation

Tools require ShyPN with the experimental validation infrastructure:

```bash
# Ensure you're in the cli/experimental directory
cd cli/experimental

# All tools use relative imports - run from this directory
```

## Quick Start

### Single Model Validation

```bash
# Validate τ-leaping vs Gillespie (10 replicates)
./validate_equivalence.py model.xml -n 10 -d 100.0 -o results/

# Benchmark performance
./benchmark_timing.py model.xml -n 100 --compare -o results/

# Analyze dependencies
./analyze_dependency_impact.py model.xml -n 50 -o results/

# Generate report
./generate_experiment_report.py \
  --validation results/validation_results.json \
  --benchmark results/benchmark_results.json \
  --dependency results/dependency_analysis.json \
  -o results/report.md
```

### Batch Processing

```bash
# Create batch CSV
cat > batch.csv << EOF
model_id,model_path
BIOMD0000000001,path/to/BIOMD0000000001.xml
BIOMD0000000004,path/to/BIOMD0000000004.xml
EOF

# Run batch experiment
./run_batch_replicates.py batch.csv -n 100 -d 100.0 -o batch_results/

# Analyze results
./analyze_batch_results.py batch_results/batch_summary.json
```

### Complete Workflow

```bash
# Run the full pipeline
./test_workflow.sh
```

## Tool Reference

### 1. setup_experiment.py
**Purpose**: Interactive experiment setup and configuration

```bash
./setup_experiment.py
```

Creates experiment directory structure and batch CSV files.

### 2. run_replicates.py
**Purpose**: Run replicate simulations on a single model

```bash
./run_replicates.py model.xml -n 100 -d 100.0 -o output/
```

**Options**:
- `-n, --replicates`: Number of replicates (default: 100)
- `-d, --duration`: Simulation duration (default: 100.0)
- `-o, --output`: Output directory (default: replicate_results)
- `--no-tau-leaping`: Use Gillespie SSA instead

**Output**:
- `trajectories.csv`: Time series data (wide or long format)
- `statistics.json`: Mean, std, CV, percentiles

### 3. run_batch_replicates.py
**Purpose**: Process multiple models with replicate simulations

```bash
./run_batch_replicates.py batch.csv -n 100 --parallel -o batch_results/
```

**CSV Format**:
```csv
model_id,model_path
MODEL1,path/to/model1.xml
MODEL2,path/to/model2.xml
```

**Options**:
- `-n, --replicates`: Replicates per model (default: 100)
- `-d, --duration`: Simulation duration (default: 100.0)
- `--parallel`: Use parallel processing
- `-o, --output`: Output directory

**Output**:
- `batch_summary.json`: Complete results for all models
- `successful_models.csv`: List of successful models
- `failed_models.csv`: List of failed models with errors

### 4. validate_equivalence.py
**Purpose**: Compare τ-leaping vs Gillespie SSA for equivalence

```bash
./validate_equivalence.py model.xml -n 100 -d 100.0 -o validation/
```

**Algorithm**:
1. Run n replicates with τ-leaping
2. Run n replicates with Gillespie SSA
3. Compare final means per species
4. Calculate relative difference: |τ - SSA| / |SSA|
5. Determine equivalence (5% tolerance)

**Verdict**:
- ✅ **PASSED**: ≥95% equivalent species
- ⚠️ **WARNING**: ≥90% equivalent species
- ❌ **FAILED**: <90% equivalent species

**Output**: `validation_results.json`

### 5. benchmark_timing.py
**Purpose**: Measure and compare execution times

```bash
./benchmark_timing.py model.xml -n 100 --compare -o benchmark/
```

**Options**:
- `--compare`: Compare τ-leaping with Gillespie SSA

**Output**:
- `benchmark_results.json`: Timing data and speedup factor

### 6. analyze_dependency_impact.py
**Purpose**: Analyze model dependency structure and parallelization potential

```bash
./analyze_dependency_impact.py model.xml -n 50 -o dependency/
```

**Analysis**:
- Counts independent vs dependent transitions
- Calculates independence ratio
- Recommends parallelization potential (HIGH/MODERATE/LOW)

**Output**: `dependency_analysis.json`

### 7. plot_speedup_analysis.py
**Purpose**: Visualize performance benchmark results

```bash
./plot_speedup_analysis.py benchmark_results.json -o speedup.png
```

**Requires**: matplotlib

**Output**: Two-panel figure with execution time comparison and speedup factor

### 8. plot_validation_results.py
**Purpose**: Visualize algorithm equivalence results

```bash
./plot_validation_results.py validation_results.json -o validation.png
```

**Requires**: matplotlib

**Output**: Two-panel figure with mean comparison and relative differences

### 9. generate_experiment_report.py
**Purpose**: Generate comprehensive markdown report

```bash
./generate_experiment_report.py \
  --validation validation_results.json \
  --benchmark benchmark_results.json \
  --dependency dependency_analysis.json \
  -o report.md
```

**Output**: Markdown report with tables, conclusions, and recommendations

### 10. analyze_batch_results.py
**Purpose**: Analyze and summarize batch experiment results

```bash
./analyze_batch_results.py batch_summary.json -o analysis.json
```

**Output**: Summary statistics and model distribution analysis

## Example Workflow

```bash
# 1. Setup experiment
./setup_experiment.py

# 2. Validate equivalence
./validate_equivalence.py model.xml -n 100 -o results/

# 3. Benchmark performance  
./benchmark_timing.py model.xml -n 100 --compare -o results/

# 4. Analyze dependencies
./analyze_dependency_impact.py model.xml -n 50 -o results/

# 5. Generate visualizations
./plot_validation_results.py results/validation_results.json -o results/validation.png
./plot_speedup_analysis.py results/benchmark_results.json -o results/speedup.png

# 6. Compile report
./generate_experiment_report.py \
  --validation results/validation_results.json \
  --benchmark results/benchmark_results.json \
  --dependency results/dependency_analysis.json \
  -o results/report.md
```

## Batch Experiment Example

```bash
# Create batch CSV with 100 BioModels
cat > biomodels_batch.csv << EOF
model_id,model_path
$(for i in $(seq -f "%04g" 1 100); do 
    echo "BIOMD00000000${i#0},../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD00000000${i#0}.xml"
done)
EOF

# Run batch (this may take hours)
./run_batch_replicates.py biomodels_batch.csv -n 100 -d 100.0 --parallel -o biomodels_results/

# Analyze results
./analyze_batch_results.py biomodels_results/batch_summary.json
```

## Validation Criteria

### Equivalence Test
- **Tolerance**: 5% relative difference
- **Success**: ≥95% of species equivalent
- **Warning**: 90-95% of species equivalent
- **Failure**: <90% of species equivalent

### Performance Benchmark
- **Speedup**: Total time ratio (Gillespie / τ-leaping)
- **Expected**: 1.5-3x for medium models (10-50 species)
- **Best case**: >5x for large models (>100 species)

## Troubleshooting

### Import Errors
All tools use `_fix_imports.py` to add `src/` to Python path. Ensure you run from `cli/experimental/` directory.

### SBML Loading Errors
Tools use `_sbml_loader.py` which handles the full pipeline:
- SBMLParser → PathwayPostProcessor → PathwayConverter → DocumentModel

### Simulation Failures
Check model structure:
- Verify all species have initial values
- Check for numerical issues (very large/small values)
- Examine kinetic rate expressions

## Implementation Details

### Architecture
```
CLI Tools (this directory)
├── User Interface Layer
├── Facade Layer (Week 1)
│   ├── ReplicateRunner
│   ├── BatchProcessor
│   └── Export API
└── Core Platform
    ├── SimulationController
    ├── TauLeapingEngine
    └── GillespieSSA
```

### Data Formats

**CSV (Batch Input)**:
```csv
model_id,model_path
BIOMD0000000001,path/to/model.xml
```

**JSON (Results)**:
```json
{
  "model_name": "BIOMD0000000001",
  "n_replicates": 100,
  "species_statistics": {
    "Species1": {
      "mean": [0.0, 1.2, ...],
      "std": [0.0, 0.3, ...],
      "cv": [0.0, 0.25, ...]
    }
  }
}
```

## Testing

### Unit Test
```bash
# Test single model
./validate_equivalence.py \
  ../../doc/papers/foundation/experimental_data/biomodels_dataset/sbml_files/BIOMD0000000001.xml \
  -n 10 -d 50.0 -o test_output/
```

### Integration Test
```bash
# Run complete workflow
./test_workflow.sh
```

### Batch Test
```bash
# Test with 10 models
./run_batch_replicates.py batch_experiment.csv -n 5 -d 50.0 -o test_batch/
./analyze_batch_results.py test_batch/batch_summary.json
```

## Performance Notes

- **Single model**: ~1-10 seconds (100 replicates, 100 time units)
- **Batch (10 models)**: ~1-5 minutes (5 replicates, 50 time units)
- **Large batch (100 models)**: ~30-120 minutes (100 replicates, 100 time units)

## Paper 2 Usage

These tools are designed for the experimental validation section of Paper 2:

1. **Equivalence Validation**: Demonstrate τ-leaping produces equivalent results
2. **Performance Analysis**: Show computational speedup benefits
3. **Scalability Study**: Test across diverse model sizes
4. **Dependency Impact**: Analyze parallelization potential

## Author

Eugênio Simão  
December 2025

## License

Part of the ShyPN project.
