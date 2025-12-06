# Repository Structure Plan: CLI Tools vs. Utility Scripts

**Date**: December 5, 2025  
**Branch**: `feature/papers-concurrent-transition-types`  
**Purpose**: Organize experimental CLI tools separately from utility scripts

---

## Current Problems

### 1. **Cluttered `scripts/` Directory**
- 70+ miscellaneous scripts (debug, demo, test, helpers)
- No clear organization or categorization
- Hard to find tools for specific purposes
- Mix of:
  - Development utilities (`debug_*.py`, `diagnose_*.py`)
  - Demos (`demo_*.py`)
  - Test generators (`generate_*.py`)
  - Analysis helpers (`analyze_*.py`)

### 2. **Inconsistent Paper Script Organization**
- Foundation paper scripts: `doc/papers/foundation/scripts/`
- Well-organized but isolated from reusable infrastructure
- Future papers would duplicate structure

### 3. **No Clear Distinction**
- What's a "throwaway debug script"?
- What's a "reusable experimental tool"?
- What's a "production CLI command"?

---

## Proposed Structure

```
shypn/
├── cli/                           # 🆕 NEW: Production CLI tools
│   ├── __init__.py
│   ├── README.md                  # User-facing documentation
│   │
│   ├── experimental/              # Experimental validation tools
│   │   ├── __init__.py
│   │   ├── README.md              # How to use experimental toolkit
│   │   │
│   │   ├── setup_experiment.py           # Tool 1: Initialize experiment
│   │   ├── run_replicates.py             # Tool 2: Single model validation
│   │   ├── run_batch_replicates.py       # Tool 3: Batch processing
│   │   ├── benchmark_timing.py           # Tool 4: Timing benchmarks
│   │   ├── validate_equivalence.py       # Tool 5: Statistical validation
│   │   ├── analyze_dependency_impact.py  # Tool 6: Dependency analysis
│   │   ├── plot_validation_results.py    # Tool 7: Validation plots
│   │   ├── plot_speedup_analysis.py      # Tool 8: Speedup plots
│   │   ├── generate_experiment_report.py # Tool 9: Final report
│   │   └── run_full_experiment.sh        # Tool 10: Master orchestrator
│   │
│   ├── data/                      # Data acquisition tools
│   │   ├── __init__.py
│   │   ├── fetch_biomodels.py    # Download BioModels (from foundation)
│   │   ├── fetch_kegg_pathway.py # Download KEGG pathways
│   │   └── convert_sbml.py       # Batch SBML conversion
│   │
│   ├── analysis/                  # Model analysis tools
│   │   ├── __init__.py
│   │   ├── classify_dependencies.py      # Dependency classification
│   │   ├── validate_topology.py          # Topology validation
│   │   ├── validate_sbml_conversion.py   # SBML import validation
│   │   └── analyze_model_complexity.py   # Complexity metrics
│   │
│   └── visualization/             # Plotting tools
│       ├── __init__.py
│       ├── plot_speedup.py        # Speedup visualization
│       ├── plot_dependencies.py   # Dependency distribution
│       └── export_figures.py      # Publication-quality exports
│
├── scripts/                       # Development utilities (existing)
│   ├── README.md                  # Updated: Development tools only
│   ├── debug/                     # 🔄 Reorganize existing scripts
│   │   ├── debug_*.py
│   │   └── diagnose_*.py
│   ├── demo/                      # Demos and examples
│   │   └── demo_*.py
│   ├── test/                      # Test generators
│   │   ├── generate_*.py
│   │   └── test_*.py
│   └── helpers/                   # Miscellaneous helpers
│       ├── check_*.py
│       └── verify_*.py
│
├── doc/
│   └── papers/
│       ├── foundation/
│       │   ├── scripts/           # 🗑️ DEPRECATE: Move to cli/
│       │   │   └── README.md      # "Scripts moved to cli/"
│       │   └── experimental_data/ # Keep data here
│       │
│       └── tau-leaping/
│           ├── RESEARCH_ROADMAP.md
│           ├── experiments/       # Experiment results (generated)
│           └── figures/           # Generated figures
│
└── examples/                      # User-facing examples
    ├── basic_simulation.py
    ├── batch_processing.py        # 🆕 NEW: Using cli/experimental/
    └── custom_analysis.py         # 🆕 NEW: Using cli/analysis/
```

---

## Directory Purposes

### **`cli/` - Production CLI Tools** 🆕 NEW

**Purpose**: User-facing command-line tools for common workflows

**Characteristics**:
- ✅ Production-quality code
- ✅ Comprehensive `--help` documentation
- ✅ Error handling and validation
- ✅ Tested and maintained
- ✅ Versioned (follow SHYpn releases)
- ✅ Installable (via `pip install shypn`)

**Target Users**:
- Researchers running experiments
- Students learning stochastic simulation
- Practitioners validating models

**Examples**:
```bash
# Run 1000 replicates on a model
python -m shypn.cli.experimental.run_replicates \
    --model BIOMD0000000064.xml \
    --replicates 1000 \
    --output results/

# Batch validation
python -m shypn.cli.experimental.run_batch_replicates \
    --models model_list.csv \
    --replicates 1000 \
    --output results/

# Statistical validation
python -m shypn.cli.experimental.validate_equivalence \
    --parallel results/parallel.csv \
    --sequential results/sequential.csv \
    --output validation_report.md
```

---

### **`scripts/` - Development Utilities**

**Purpose**: Internal development, debugging, testing

**Characteristics**:
- ⚠️ Quick-and-dirty code
- ⚠️ Minimal documentation
- ⚠️ May break between versions
- ⚠️ Not installed with package
- ⚠️ For developers only

**Target Users**:
- SHYpn core developers
- Contributors debugging issues
- Temporary testing needs

**Examples**:
```bash
# Debug a specific issue
python scripts/debug/diagnose_simulation_hang.py model.shy

# Generate test model
python scripts/test/generate_galaxy_model.py

# Quick demo
python scripts/demo/demo_sbml_enrichment.py
```

---

### **`doc/papers/*/` - Paper-Specific**

**Purpose**: Paper-specific results, figures, data

**Characteristics**:
- 📄 Documentation and reports
- 📊 Experimental data (CSVs, JSONs)
- 📈 Generated figures
- 📝 Paper drafts
- ❌ No scripts (moved to `cli/`)

**Rationale**: Papers reference stable CLI tools, not custom scripts

---

## Migration Plan

### **Phase 1: Create New Structure** (Day 1)

```bash
# Create new directories
mkdir -p cli/experimental
mkdir -p cli/data
mkdir -p cli/analysis
mkdir -p cli/visualization

# Reorganize scripts/
mkdir -p scripts/debug
mkdir -p scripts/demo
mkdir -p scripts/test
mkdir -p scripts/helpers
```

### **Phase 2: Move Foundation Paper Scripts** (Day 1)

```bash
# Move production tools to cli/
mv doc/papers/foundation/scripts/fetch_biomodels_dataset.py \
   cli/data/fetch_biomodels.py

mv doc/papers/foundation/scripts/classify_all_dependencies.py \
   cli/analysis/classify_dependencies.py

mv doc/papers/foundation/scripts/validate_topology.py \
   cli/analysis/validate_topology.py

mv doc/papers/foundation/scripts/validate_sbml_conversion.py \
   cli/analysis/validate_sbml_conversion.py

mv doc/papers/foundation/scripts/benchmark_parallel_simulation.py \
   cli/experimental/benchmark_parallel_simulation.py  # Reference/legacy

mv doc/papers/foundation/scripts/plot_speedup.py \
   cli/visualization/plot_speedup.py

# Keep orchestration script as reference
mv doc/papers/foundation/scripts/run_all_experiments.sh \
   doc/papers/foundation/run_experiments_ARCHIVE.sh
```

### **Phase 3: Create New τ-Leaping Tools** (Week 2)

```bash
# Create 10 new tools in cli/experimental/
touch cli/experimental/setup_experiment.py
touch cli/experimental/run_replicates.py
touch cli/experimental/run_batch_replicates.py
touch cli/experimental/benchmark_timing.py
touch cli/experimental/validate_equivalence.py
touch cli/experimental/analyze_dependency_impact.py
touch cli/experimental/plot_validation_results.py
touch cli/experimental/plot_speedup_analysis.py
touch cli/experimental/generate_experiment_report.py
touch cli/experimental/run_full_experiment.sh
```

### **Phase 4: Reorganize `scripts/`** (Day 2)

```bash
# Move debug scripts
mv scripts/debug_*.py scripts/debug/
mv scripts/diagnose_*.py scripts/debug/

# Move demos
mv scripts/demo_*.py scripts/demo/

# Move test generators
mv scripts/generate_*.py scripts/test/
mv scripts/test_*.py scripts/test/

# Move helpers
mv scripts/check_*.py scripts/helpers/
mv scripts/verify_*.py scripts/helpers/
mv scripts/analyze_*.py scripts/helpers/
```

### **Phase 5: Update Documentation** (Day 2)

- Update `cli/README.md` with user-facing instructions
- Update `scripts/README.md` clarifying "development only"
- Update `doc/papers/foundation/scripts/README.md` with redirect
- Create examples in `examples/` showing CLI usage

---

## CLI Tool Standards

### **Required Elements**

Every tool in `cli/` must have:

1. **Shebang and encoding**:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
```

2. **Module docstring**:
```python
"""
Tool Name: What it does in one line

Longer description explaining purpose, use cases, and workflow.

Usage:
    python -m shypn.cli.experimental.run_replicates \\
        --model BIOMD0000000064.xml \\
        --replicates 1000 \\
        --output results/

Dependencies:
    - shypn.engine.simulation
    - scipy (for statistical tests)
    - pandas (for data handling)

Author: SHYpn Development Team
License: MIT
Version: 1.0.0
"""
```

3. **Argument parsing with help**:
```python
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run n stochastic replicates for a model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    %(prog)s --model model.xml --replicates 1000 --output results/

    # With custom parameters
    %(prog)s --model model.xml --replicates 1000 \\
             --duration 100.0 --epsilon 0.03 --output results/

For more information, see: https://shypn.readthedocs.io/cli/experimental/
        """
    )
    
    parser.add_argument('--model', required=True, 
                        help='Path to SBML model file')
    parser.add_argument('--replicates', type=int, default=1000,
                        help='Number of replicate simulations (default: 1000)')
    parser.add_argument('--output', required=True,
                        help='Output directory for results')
    parser.add_argument('--version', action='version', 
                        version='%(prog)s 1.0.0')
    
    return parser.parse_args()
```

4. **Error handling**:
```python
def main():
    """Main entry point."""
    args = parse_arguments()
    
    try:
        # Validate inputs
        if not Path(args.model).exists():
            print(f"ERROR: Model file not found: {args.model}", file=sys.stderr)
            sys.exit(1)
        
        # Run tool
        result = run_replicates(args)
        
        # Report success
        print(f"✅ Success! Results saved to {args.output}")
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
```

5. **Progress reporting**:
```python
from tqdm import tqdm

for i in tqdm(range(n_replicates), desc="Running replicates"):
    # Do work
    pass
```

6. **Logging**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(output_dir / 'experiment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"Starting replicates for model: {model_id}")
```

---

## Package Installation

### **Make CLI Tools Installable**

Update `pyproject.toml`:

```toml
[project.scripts]
# Experimental tools
shypn-setup-experiment = "shypn.cli.experimental.setup_experiment:main"
shypn-run-replicates = "shypn.cli.experimental.run_replicates:main"
shypn-batch-replicates = "shypn.cli.experimental.run_batch_replicates:main"
shypn-validate-equivalence = "shypn.cli.experimental.validate_equivalence:main"

# Data tools
shypn-fetch-biomodels = "shypn.cli.data.fetch_biomodels:main"

# Analysis tools
shypn-classify-dependencies = "shypn.cli.analysis.classify_dependencies:main"
shypn-validate-topology = "shypn.cli.analysis.validate_topology:main"

# Visualization tools
shypn-plot-speedup = "shypn.cli.visualization.plot_speedup:main"
```

**After installation**:
```bash
pip install -e .

# Now users can run:
shypn-run-replicates --model model.xml --replicates 1000 --output results/
shypn-batch-replicates --models list.csv --output results/
shypn-validate-equivalence --parallel par.csv --sequential seq.csv
```

---

## Documentation Structure

### **`cli/README.md`**

```markdown
# SHYpn CLI Tools

Command-line tools for experimental validation, analysis, and visualization.

## Installation

```bash
pip install shypn
```

## Experimental Tools

Tools for running large-scale validation experiments.

- `shypn-setup-experiment`: Initialize experiment directory
- `shypn-run-replicates`: Run n replicates for one model
- `shypn-batch-replicates`: Run replicates for multiple models
- `shypn-validate-equivalence`: Statistical validation
- ...

See [experimental/README.md](experimental/README.md) for details.

## Data Tools

- `shypn-fetch-biomodels`: Download BioModels database entries
- ...

## Analysis Tools

- `shypn-classify-dependencies`: Analyze transition dependencies
- `shypn-validate-topology`: Validate Petri net topology
- ...

## Visualization Tools

- `shypn-plot-speedup`: Generate speedup visualizations
- ...
```

### **`cli/experimental/README.md`**

```markdown
# Experimental Validation Toolkit

Complete toolkit for validating stochastic simulation algorithms.

## Workflow

```bash
# 1. Setup experiment
shypn-setup-experiment --name my_experiment --models list.csv --output exp/

# 2. Run batch replicates
shypn-batch-replicates --models exp/models/list.csv --replicates 1000 --output exp/data/

# 3. Validate equivalence
shypn-validate-equivalence --parallel exp/data/par.csv --sequential exp/data/seq.csv

# 4. Generate report
shypn-generate-report --experiment exp/ --output exp/reports/
```

## Tools

### shypn-setup-experiment
[Detailed docs...]

### shypn-run-replicates
[Detailed docs...]

...
```

---

## Benefits of This Structure

### **1. Clear Separation of Concerns**
- ✅ Production tools → `cli/`
- ✅ Development utilities → `scripts/`
- ✅ Paper results → `doc/papers/*/`

### **2. User-Friendly**
- ✅ Easy to discover tools (`shypn-<tab>` autocomplete)
- ✅ Consistent interface (all tools use argparse)
- ✅ Comprehensive help (`--help`)
- ✅ Installable (no manual PATH setup)

### **3. Maintainable**
- ✅ Organized by purpose
- ✅ Easy to find tools
- ✅ Clear quality expectations
- ✅ Version controlled

### **4. Reusable**
- ✅ Foundation paper tools available for τ-leaping paper
- ✅ Future papers can reuse experimental toolkit
- ✅ Community can contribute new tools

### **5. Professional**
- ✅ Follows best practices (e.g., Click, Poetry)
- ✅ Proper packaging (installable via pip)
- ✅ Documentation integrated
- ✅ Testable (cli tools can have unit tests)

---

## Timeline

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Create `cli/` structure | Empty directories with READMEs |
| 1 | Move foundation tools | `cli/data/`, `cli/analysis/`, `cli/visualization/` populated |
| 2 | Reorganize `scripts/` | `scripts/debug/`, `scripts/demo/`, etc. |
| 2 | Update documentation | All READMEs updated |
| 3 | Add to pyproject.toml | CLI tools installable |
| 3 | Create examples | `examples/` showing usage |

**Total**: 3 days to complete reorganization

---

## Next Steps

1. ✅ **Review structure** - Get approval on directory layout
2. ✅ **Phase 1** - Create `cli/` directories
3. ✅ **Phase 2** - Move foundation paper scripts
4. ✅ **Phase 3** - Create τ-leaping tool stubs
5. ✅ **Phase 4** - Reorganize `scripts/`
6. ✅ **Phase 5** - Update all documentation

Ready to start reorganization?
