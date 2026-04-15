# Thesis Testing Suite

Test scripts for generating empirical results and validation data for thesis and paper.

## Overview

This directory contains comprehensive test suites designed to validate Shypn's capabilities across large datasets of biological models. Results are automatically saved to `doc/thesis/` for inclusion in academic publications.

## Test Suites

### 1. BioModels 100 Test (`test_100_biomodels.py`)

**Purpose**: Validate SBML import robustness across 100 curated models from BioModels Database.

**Metrics Collected**:
- Import success/failure rates
- Species → Place conversion accuracy
- Reactions → Transition conversion accuracy
- Arc type classification (normal, test/catalyst, inhibitor)
- Kinetic parameter extraction rates
- Layout generation quality
- Performance metrics (parse time, layout time)

**Usage**:
```bash
# Test all 100 models
python tests/thesis/test_100_biomodels.py

# Quick test with first 10 models
python tests/thesis/test_100_biomodels.py --limit 10

# Custom output directory
python tests/thesis/test_100_biomodels.py --output-dir /path/to/results
```

**Output**: Results saved to `doc/thesis/sbml_models/`
- `test_results_complete.json` - Full JSON report
- `test_results_report.md` - Human-readable markdown report
- `test_results_intermediate.json` - Checkpoint saves every 10 models

**Model Categories**:
- **Simple (10 models)**: 3-20 species, basic dynamics
- **Medium (30 models)**: 20-50 species, moderate complexity
- **Complex (30 models)**: 50-100 species, multi-pathway systems
- **Very Complex (30 models)**: 100+ species, genome-scale networks

**Key Models**:
- BIOMD0000000001: Edelstein1996 - EPSP (minimal test case)
- BIOMD0000000012: Elowitz2000 - Repressilator (oscillations)
- BIOMD0000000206: Teusink2000 - Yeast glycolysis (metabolism)
- BIOMD0000000010: Kholodenko2000 - MAPK cascade (signaling)

### 2. Future Test Suites

**Planned additions**:
- `test_kegg_pathways.py` - KEGG pathway import validation
- `test_simulation_stability.py` - Numerical stability across models
- `test_parameter_inference.py` - Heuristic parameter quality
- `test_viability_detection.py` - Viability analysis validation
- `test_performance_scaling.py` - Computational complexity analysis

## Results for Thesis

All test results are automatically saved to `doc/thesis/` subdirectories for easy integration into thesis LaTeX documents.

### Expected Thesis Sections

1. **Chapter: SBML Import Validation**
   - Import success rates across model complexity
   - Conversion accuracy metrics
   - Performance analysis

2. **Chapter: Biological Petri Net Formalism**
   - Arc type distribution (normal vs catalyst vs inhibitor)
   - Modifier handling statistics
   - Reversible reaction conversion

3. **Chapter: Parameter Inference**
   - Kinetic parameter extraction rates
   - Heuristic database coverage
   - Parameter assignment quality

4. **Chapter: System Performance**
   - Parse time vs model complexity
   - Layout generation scalability
   - Memory usage profiles

## Running Tests

### Prerequisites

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt
```

### Complete Test Run

```bash
# Run full suite (may take 1-2 hours)
python tests/thesis/test_100_biomodels.py

# Monitor progress
tail -f doc/thesis/sbml_models/test_results_intermediate.json
```

### Quick Validation

```bash
# Test first 10 models (~5 minutes)
python tests/thesis/test_100_biomodels.py --limit 10
```

## Interpreting Results

### Success Metrics

**Target Benchmarks**:
- Import success rate: >95%
- Parse success rate: >98%
- Layout generation: >90%
- Kinetic extraction: >60% (many models lack detailed kinetics)

### Common Issues

1. **Parse failures**: Usually due to SBML version incompatibility
2. **Layout failures**: Complex models with >200 nodes may timeout
3. **Missing kinetics**: Many structural models don't include rate laws

### Quality Indicators

- **Species/Reactions ratio**: Should be ~1.0-2.0 for metabolic networks
- **Arc distribution**: Catalysts should be 10-30% of total arcs
- **Initial tokens**: Should sum to reasonable biological concentrations

## Integration with Thesis

### LaTeX Integration

Results can be directly referenced in thesis:

```latex
\input{../../doc/thesis/sbml_models/tables/summary_statistics.tex}
```

### Figure Generation

Generate plots from results:

```python
import json
import matplotlib.pyplot as plt

with open('doc/thesis/sbml_models/test_results_complete.json') as f:
    data = json.load(f)

# Plot success rate by complexity
# ...
```

## Contributing

When adding new test suites:

1. Follow naming convention: `test_<category>_<description>.py`
2. Save results to `doc/thesis/<category>/`
3. Generate both JSON (machine-readable) and Markdown (human-readable)
4. Include comprehensive docstrings
5. Update this README

## References

- [BioModels Database](https://www.ebi.ac.uk/biomodels/)
- [SBML Specification](http://sbml.org/Documents/Specifications)
- Thesis: Chapter 7 - Validation Through Examples
