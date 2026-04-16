# Test Fixtures

This directory contains test fixtures used by various test suites.

## Structure

### sbml_models/
SBML test models for multi-compartment and modular Bio-PN validation.

**Files:**
- **bacterial_quorum_sensing_BIOMD0000000002.xml** - Bacterial quorum sensing model (multi-cellular compartments)
- **circadian_clock_BIOMD0000000171.xml** - Circadian clock model
- **simple_two_compartment.xml** - Simple two-compartment test case
- **yeast_glycolysis_BIOMD0000000064.xml** - Teusink et al. (2000) yeast glycolysis model (cytoplasm/mitochondria)

**Documentation:**
- **README.md** - Multi-compartment SBML test models documentation
- **PHASE14_TEST_REPORT.md** - Phase 14 testing report

**Related Test:**
- `tests/sbml/test_multicompartment_models.py` - Validation script for these models

### test_outputs/
Example test outputs and artifacts for reference.

**Files:**
- **continuous_recording_test.png** - Continuous simulation recording plot
- **continuous_test_output.txt** - Continuous test console output
- **test_publication.html** - Publication format test report
- **test_summary.html** - Summary test report  
- **test_technical.html** - Technical test report

**Purpose:** Reference outputs to verify test behavior and regression testing

### Root Level Fixtures
- **BIOMD0000000001.xml** - BioModels reference model
- **Edelstein1996 - EPSP ACh event.shy** - Edelstein 1996 model
- **Hynne2001_Glycolysis.shy** - Hynne 2001 glycolysis model
- **teste.shy** - Generic test model

## Organization History

- **December 31, 2025**: Moved from root `/test_models/` and `/test_output/` directories
- Organized under proper test fixtures structure for clarity
- SBML models grouped together for multi-compartment testing
- Test outputs preserved as reference artifacts

## Usage

Import fixtures in tests:

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
SBML_MODELS = FIXTURES_DIR / 'sbml_models'

# Load a test model
model_path = SBML_MODELS / 'yeast_glycolysis_BIOMD0000000064.xml'
```

## Adding New Fixtures

Place new test fixtures in appropriate subdirectories:
- SBML files → `sbml_models/`
- Test outputs → `test_outputs/`
- General models → root `fixtures/`
