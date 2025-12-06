# Foundation Paper Scripts - ARCHIVED

**⚠️ Scripts Moved**: The experimental scripts from this directory have been migrated to the main CLI toolkit.

## New Locations

The production-quality tools from foundation paper are now in:

| Old Location | New Location | Installable Command |
|--------------|--------------|---------------------|
| `fetch_biomodels_dataset.py` | `cli/data/fetch_biomodels.py` | `shypn-fetch-biomodels` |
| `classify_all_dependencies.py` | `cli/analysis/classify_dependencies.py` | `shypn-classify-dependencies` |
| `validate_topology.py` | `cli/analysis/validate_topology.py` | `shypn-validate-topology` |
| `validate_sbml_conversion.py` | `cli/analysis/validate_sbml_conversion.py` | `shypn-validate-sbml` |
| `plot_speedup.py` | `cli/visualization/plot_speedup.py` | `shypn-plot-speedup` |
| `benchmark_parallel_simulation.py` | `cli/experimental/` (reference) | TBD |

## Why the Move?

1. **Reusability**: Tools are now available for all papers and users
2. **Maintainability**: Single source of truth for experimental tools
3. **Installability**: Tools are now pip-installable CLI commands
4. **Documentation**: Centralized documentation in `cli/README.md`

## Using the New Tools

```bash
# Install SHYpn with CLI tools
pip install -e /path/to/shypn

# Use installed commands
shypn-fetch-biomodels --count 100 --output data/
shypn-classify-dependencies --models list.csv --output results/
shypn-validate-topology --models list.csv --output validation/
```

## Original Workflow (ARCHIVED)

The original orchestration script remains as reference:

```bash
# See: run_all_experiments.sh (archived)
bash run_all_experiments.sh
```

But new experiments should use the CLI toolkit:

```bash
# See: ../../tau-leaping/EXPERIMENTAL_TOOLKIT_DESIGN.md
shypn-setup-experiment --name my_exp --models list.csv --output exp/
shypn-batch-replicates --models exp/models/list.csv --output exp/data/
shypn-generate-report --experiment-dir exp/ --output exp/reports/
```

## Documentation

- **CLI Tools**: See [../../../cli/README.md](../../../cli/README.md)
- **Experimental Toolkit**: See [../../../cli/experimental/README.md](../../../cli/experimental/README.md)
- **Repository Structure**: See [../../tau-leaping/REPOSITORY_STRUCTURE_PLAN.md](../../tau-leaping/REPOSITORY_STRUCTURE_PLAN.md)

---

**Date of Migration**: December 5, 2025  
**Reason**: Centralize reusable experimental tools for all papers
