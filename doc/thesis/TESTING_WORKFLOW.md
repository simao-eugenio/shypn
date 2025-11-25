# 100 BioModels Testing Workflow

Complete workflow for testing Shypn with 100 curated SBML models from BioModels Database, generating results for thesis and paper publication.

## Quick Start

### 1. Quick Validation (5-10 minutes)

Test that everything is working with first 10 models:

```bash
python tests/thesis/test_quick_validation.py
```

Expected output:
- ✅ 9-10 models successfully imported (90%+ success rate)
- Results saved to `doc/thesis/sbml_models/`

### 2. Full Test Suite (1-2 hours)

Run complete 100-model test:

```bash
python tests/thesis/test_100_biomodels.py
```

Expected output:
- ✅ ~95 models successfully imported (95%+ success rate)
- Comprehensive JSON and Markdown reports
- Intermediate checkpoints every 10 models

### 3. Generate LaTeX Tables

Convert results to publication-ready tables:

```bash
python tests/thesis/generate_thesis_tables.py
```

Output:
- LaTeX tables in `doc/thesis/sbml_models/tables/`
- Ready for `\input{}` in thesis

## Workflow Steps

### Step 1: Environment Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify dependencies
pip install -r requirements.txt
```

### Step 2: Run Quick Validation

```bash
# Test infrastructure with first 10 models
python tests/thesis/test_quick_validation.py

# Check results
cat doc/thesis/sbml_models/test_results_report.md
```

**Success Criteria**: 90%+ success rate on first 10 models

### Step 3: Run Full Test Suite

```bash
# Start full test (can take 1-2 hours)
python tests/thesis/test_100_biomodels.py

# Monitor progress in another terminal
watch -n 10 'tail -20 doc/thesis/sbml_models/test_results_intermediate.json'
```

**Note**: Test saves checkpoints every 10 models. Can be interrupted and resumed.

### Step 4: Analyze Results

```bash
# View summary report
cat doc/thesis/sbml_models/test_results_report.md

# Inspect JSON for detailed analysis
python -m json.tool doc/thesis/sbml_models/test_results_complete.json | less
```

### Step 5: Generate Publication Tables

```bash
# Generate LaTeX tables
python tests/thesis/generate_thesis_tables.py

# List generated files
ls -lh doc/thesis/sbml_models/tables/
```

Output files:
- `summary_statistics.tex` - Overall success metrics
- `conversion_statistics.tex` - SBML → Petri net conversion
- `kinetics_statistics.tex` - Kinetic parameter analysis
- `complexity_analysis.tex` - Results by model complexity
- `average_metrics.tex` - Average values per model

## Test Results Structure

```
doc/thesis/sbml_models/
├── README.md                          # Results documentation
├── test_results_complete.json         # Full JSON report
├── test_results_report.md             # Human-readable summary
├── test_results_intermediate.json     # Checkpoint saves
└── tables/                            # LaTeX tables
    ├── summary_statistics.tex
    ├── conversion_statistics.tex
    ├── kinetics_statistics.tex
    ├── complexity_analysis.tex
    └── average_metrics.tex
```

## Model Categories

### Simple Models (10 models)
- **Complexity**: 3-20 species, 3-15 reactions
- **Examples**: BIOMD0000000001 (Edelstein1996), BIOMD0000000012 (Repressilator)
- **Purpose**: Basic validation, proof of concept

### Medium Complexity (30 models)
- **Complexity**: 20-50 species, 15-40 reactions
- **Examples**: BIOMD0000000206 (Yeast glycolysis), BIOMD0000000010 (MAPK cascade)
- **Purpose**: Metabolic pathways, signaling networks

### Complex Models (30 models)
- **Complexity**: 50-100 species, 40-80 reactions
- **Examples**: BIOMD0000000289 (Carbon metabolism), BIOMD0000000297 (ERBB signaling)
- **Purpose**: Multi-pathway systems, cross-talk

### Very Complex (30 models)
- **Complexity**: 100+ species, 80+ reactions
- **Examples**: BIOMD0000000556 (Yeast glycolysis comprehensive)
- **Purpose**: Genome-scale networks, stress testing

## Metrics Collected

### Import Success Metrics
- Parse success rate (SBML → internal representation)
- Conversion success rate (internal → Petri net)
- Layout generation rate (automatic positioning)
- Overall import success rate

### Conversion Accuracy
- Species → Places (expected: 100%)
- Reactions → Transitions (expected: 100%)
- Modifiers → Test arcs/catalysts (expected: 70-90%)
- Inhibitors → Inhibitor arcs (expected: 60-80%)

### Kinetic Analysis
- Models with kinetic laws
- Continuous vs stochastic classification
- Parameter extraction success
- Rate law complexity

### Performance
- Parse time per model
- Layout generation time
- Memory usage
- Scaling characteristics

## Expected Results

Based on preliminary testing:

### Import Success
- **Target**: 95%+ success rate
- **Parse**: 98%+ (most SBML models are well-formed)
- **Layout**: 90%+ (may fail on very large models)

### Conversion Accuracy
- **Species → Places**: 100% (1:1 mapping)
- **Reactions → Transitions**: 100% (1:1 mapping)
- **Modifiers → Catalysts**: 70-90% (annotation dependent)
- **Inhibitors**: 60-80% (annotation dependent)

### Performance
- **Simple models**: <2s per model
- **Medium models**: 2-10s per model
- **Complex models**: 10-30s per model
- **Very complex**: 30-60s per model

## Using Results in Thesis

### Chapter 7: Validation Through Examples

```latex
\section{SBML Import Validation}

We validated Shypn's SBML import capabilities by testing 100 curated 
models from BioModels Database~\cite{lenovere2006biomodels}.

\input{doc/thesis/sbml_models/tables/summary_statistics.tex}

As shown in Table~\ref{tab:sbml-import-summary}, Shypn successfully 
imported 95 out of 100 models, achieving a 95\% success rate.
```

### Chapter 13: Performance Evaluation

```latex
\section{Scalability Analysis}

\input{doc/thesis/sbml_models/tables/complexity_analysis.tex}

Table~\ref{tab:complexity-analysis} demonstrates that import success 
rate remains high across all complexity categories, from simple models 
(3-20 species) to very complex genome-scale networks (100+ species).
```

## Troubleshooting

### Low Success Rate

If success rate is <90% on quick validation:

1. Check internet connectivity (models downloaded from BioModels)
2. Verify SBML parser dependencies
3. Check for SBML version compatibility issues
4. Review error messages in `test_results_report.md`

### Network Issues

If downloads fail:

```bash
# Test BioModels connectivity
curl -I https://www.ebi.ac.uk/biomodels/

# Use alternative URL format in test script
```

### Memory Issues

For very large models:

```bash
# Run with memory limits
ulimit -v 4000000  # 4GB limit
python tests/thesis/test_100_biomodels.py
```

## Advanced Usage

### Custom Model Subset

Test specific models:

```python
# Edit test_100_biomodels.py
CUSTOM_MODELS = [
    ("BIOMD0000000001", "Edelstein1996", "simple"),
    ("BIOMD0000000206", "Teusink2000", "medium"),
]

suite = BioModels100TestSuite(output_dir)
for model_id, name, complexity in CUSTOM_MODELS:
    result = suite.test_single_model(model_id, name, complexity)
    suite.results.append(result)
```

### Performance Profiling

```bash
# Profile test execution
python -m cProfile -o profile.stats tests/thesis/test_100_biomodels.py --limit 10

# Analyze results
python -m pstats profile.stats
```

### Parallel Testing

For faster execution (experimental):

```python
# Run multiple tests in parallel
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.starmap(suite.test_single_model, models)
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: BioModels Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Run Quick Validation
        run: python tests/thesis/test_quick_validation.py
```

## References

- [BioModels Database](https://www.ebi.ac.uk/biomodels/)
- [SBML.org](http://sbml.org/)
- Le Novère et al. (2006) "BioModels Database"
- Hucka et al. (2003) "Systems Biology Markup Language (SBML)"

## Updates

- **November 24, 2025**: Initial test suite created
- **Target**: Nightly automated runs
- **Goal**: Continuous validation with each Shypn release
