# SHYpn CLI Tools

Professional command-line tools for stochastic Petri net simulation, validation, and analysis.

## Recent Updates (v0.5.0)

- ✅ **Enhanced SBML Import** - Smart handling of assignment rules and reversible reactions
- ✅ **Thermodynamic Validation** - Gibbs free energy validation (v0.4.0)
- ✅ **τ-Leaping Support** - Approximate stochastic simulation with Skellam distribution (v0.3.0)
- ✅ **Assignment Rule Options** - Three modes for handling algebraic constraints

## Installation

```bash
# Install from source
cd /path/to/shypn
pip install -e .

# After installation, CLI commands are available
shypn-run-replicates --help
shypn-batch-replicates --help
```

## Tool Categories

### 🧪 Experimental Tools (`cli/experimental/`)

Tools for large-scale validation experiments:

- **`shypn-setup-experiment`** - Initialize experiment directory structure
- **`shypn-run-replicates`** - Run n stochastic replicates for a single model
- **`shypn-batch-replicates`** - Batch process multiple models with replicates
- **`shypn-benchmark-timing`** - Measure execution time and compute speedup
- **`shypn-validate-equivalence`** - Statistical validation (MAE, CV, KS test)
- **`shypn-analyze-dependency-impact`** - Correlate speedup with dependencies
- **`shypn-plot-validation`** - Generate validation visualizations
- **`shypn-plot-speedup`** - Generate speedup analysis plots
- **`shypn-generate-report`** - Aggregate results into comprehensive report

See [experimental/README.md](experimental/README.md) for detailed documentation.

### 📊 Data Tools (`cli/data/`)

Tools for acquiring model data:

- **`shypn-fetch-biomodels`** - Download models from BioModels database
- **`shypn-fetch-kegg`** - Download KEGG pathways
- **`shypn-convert-sbml`** - Batch SBML to SHYpn conversion

### 🔍 Analysis Tools (`cli/analysis/`)

Tools for analyzing Petri net models:

- **`shypn-classify-dependencies`** - Classify transition dependencies
- **`shypn-validate-topology`** - Validate Petri net topology correctness
- **`shypn-validate-sbml`** - Validate SBML conversion fidelity
- **`shypn-analyze-complexity`** - Compute model complexity metrics

### 📈 Visualization Tools (`cli/visualization/`)

Tools for generating publication-quality figures:

- **`shypn-plot-speedup-dist`** - Speedup distribution plots
- **`shypn-plot-dependencies`** - Dependency distribution visualizations
- **`shypn-export-figures`** - Export figures in multiple formats

## Quick Start

### Run 1000 replicates on a single model

```bash
shypn-run-replicates \
    --model examples/glycolysis.xml \
    --replicates 1000 \
    --duration 100.0 \
    --output results/glycolysis/
```

### Validate parallel vs sequential equivalence

```bash
shypn-validate-equivalence \
    --parallel results/glycolysis/parallel_trajectories.csv \
    --sequential results/glycolysis/sequential_trajectories.csv \
    --output results/glycolysis/validation_report.md
```

### Batch process multiple models

```bash
shypn-batch-replicates \
    --models model_list.csv \
    --replicates 1000 \
    --output results/batch/ \
    --checkpoint results/batch/progress.json
```

### Full experimental pipeline

```bash
# 1. Setup experiment
shypn-setup-experiment \
    --name tau_leaping_validation \
    --models model_list.csv \
    --output experiments/tau_leaping/

# 2. Run batch replicates
shypn-batch-replicates \
    --models experiments/tau_leaping/models/model_list.csv \
    --replicates 1000 \
    --output experiments/tau_leaping/data/replicates/

# 3. Validate equivalence for all models
for model_id in $(cat experiments/tau_leaping/models/model_list.csv | tail -n +2 | cut -d',' -f1); do
    shypn-validate-equivalence \
        --parallel experiments/tau_leaping/data/replicates/${model_id}/parallel_trajectories.csv \
        --sequential experiments/tau_leaping/data/replicates/${model_id}/sequential_trajectories.csv \
        --output experiments/tau_leaping/validation/${model_id}_validation.json
done

# 4. Generate final report
shypn-generate-report \
    --experiment experiments/tau_leaping/ \
    --output experiments/tau_leaping/reports/FINAL_REPORT.md
```

## Tool Standards

All CLI tools follow these conventions:

- **Consistent arguments**: `--model`, `--models`, `--output`, `--help`
- **Progress tracking**: Uses `tqdm` for long-running operations
- **Error handling**: Graceful error messages, non-zero exit codes
- **Logging**: All operations logged to `<output>/experiment.log`
- **Checkpointing**: Long operations support resume capability
- **Documentation**: Comprehensive `--help` with examples

## Development vs Production

**CLI Tools (`cli/`)**: Production-quality, user-facing, tested, versioned, installable

**Utility Scripts (`scripts/`)**: Development-only, quick debugging, not installed

See [../scripts/README.md](../scripts/README.md) for development utilities.

## Examples

See [../examples/](../examples/) for complete usage examples:

- `examples/basic_simulation.py` - Simple simulation workflow
- `examples/batch_processing.py` - Batch processing multiple models
- `examples/custom_analysis.py` - Custom analysis using CLI tools

## Documentation

- [Experimental Toolkit Guide](experimental/README.md)
- [Data Tools Guide](data/README.md)
- [Analysis Tools Guide](analysis/README.md)
- [Visualization Tools Guide](visualization/README.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/simao-eugenio/shypn/issues
- Documentation: https://shypn.readthedocs.io/

## License

MIT License - See [../LICENSE](../LICENSE) for details.
