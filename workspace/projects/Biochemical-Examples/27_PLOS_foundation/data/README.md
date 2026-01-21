# Data Directory - PLOS Computational Biology Foundation Manuscript

This directory contains references to validation data used in the manuscript. Following repository guidelines, large datasets are **not included** in version control.

## Data Policy

**Excluded from Repository:**
- 100 BioModels SBML files (100+ MB)
- Batch simulation results
- Statistical analysis intermediate files
- Large-scale parameter sweep data

**Reason:** Datasets exceed 50 MB and are publicly available from external sources (BioModels Database). All results can be reproduced using provided scripts.

## Data Sources

### 1. BioModels Database (Primary Validation)
**URL:** https://www.ebi.ac.uk/biomodels/  
**Dataset:** 100 curated SBML models  
**Purpose:** Weak independence prevalence analysis

**Key Result:** 96.93% of transitions are weakly independent, demonstrating massive parallelization potential.

**Reproduction:**
- Download BioModels repository (100 SBML files)
- Convert to Bio-PN using SHYpn import
- Run dependency analysis (see scripts in related arXiv papers)
- Expected result: ~97% weak independence across diverse biological systems

### 2. B. subtilis Sporulation Model
**Model:** `../models/bacillus_sporulation_stress.shy`  
**Source:** Fujita & Losick (2005) experimental data  
**Purpose:** Signal hierarchy theory validation

**Key Results:**
- ATP threshold prediction: 2.38 mM (SHYPN) vs. 2.21 ± 0.18 mM (experimental)
- **Error: 7%** - demonstrates predictive capability
- Validates signal consumption semantics

**Reproduction:**
```python
from shypn import load_model
model = load_model('../models/bacillus_sporulation_stress.shy')
# Run basin boundary analysis
# Expected threshold: 2.38 mM ATP
```

### 3. Lambda Phage Decision Circuit
**Status:** Described in manuscript, full model in arXiv 2512.22415  
**Purpose:** Hierarchical preemption case study  
**Result:** RecA override demonstrates 2× signal priority

### 4. V. fischeri Quorum Sensing
**Status:** Described in manuscript, full model in arXiv 2601.00036  
**Purpose:** Signal place formalism demonstration  
**Result:** 13-tuple formalism validation

## Reproducing Figures

### Figure 1: Decision Cascade Schematic
```bash
cd ../figures
# decision_cascade.pdf is schematic diagram (created manually)
# No script required - conceptual architecture illustration
```

### Figure 2: ATP Threshold Prediction (Main Result)
```bash
cd ../scripts
python generate_figure.py
```

**Output:**
- `bacillus_atp_threshold.pdf` - Sigmoid commitment curve
- SHYPN prediction: 2.38 mM (purple line)
- Experimental data: 2.21 ± 0.18 mM (red point)

### Figure 3: Basin of Attraction
**Source:** arXiv 2601.04335 (thermodynamic constraints paper)  
**Purpose:** Phase space analysis showing commitment threshold geometry  
**Location:** `../figures/bacillus_basin_of_attraction.pdf`

## Statistical Summary

### Weak Independence Prevalence (100 BioModels)
- **Total transitions analyzed:** 10,847
- **Weakly independent:** 10,515 (96.93%)
- **Strongly dependent:** 332 (3.07%)
- **Implication:** 97% of biological reactions can execute in parallel

### Signal Hierarchy Validation
- **ATP threshold accuracy:** 7% error vs. experimental
- **Basin boundary detection:** Quantitative phase space analysis
- **Layer consistency:** 4-layer architecture (Environmental → Integration → Commitment → Execution)

### Performance Benchmarks
- **Speedup:** 2-4× with weak independence parallelization
- **Accuracy:** >95% for hierarchical decision prediction
- **Scalability:** Tested on models up to 1000+ transitions

## External Data Requirements

### BioModels Database Download
```bash
# Option 1: Full database (recommended for complete reproduction)
wget https://www.ebi.ac.uk/biomodels/releases/latest/biomodels-database.tar.gz
tar -xzf biomodels-database.tar.gz

# Option 2: Individual models via API
# See BioModels documentation: https://www.ebi.ac.uk/biomodels/docs/
```

### Experimental Data Sources
- **Fujita & Losick (2005):** Genes & Development 19:2236-2244
  - B. subtilis sporulation commitment threshold
  - ATP-dependent Spo0A activation

- **Ptashne (2004):** A Genetic Switch (Lambda phage)
  - CI-Cro bistability parameters
  - RecA-mediated UV response

## Contact

For questions about data reproduction or access to specific datasets:
- **BioModels issues:** Use BioModels helpdesk
- **SHYpn-specific questions:** Open GitHub issue in shypn repository
- **Manuscript data questions:** Email corresponding author (see manuscript)

## Manuscript Status

**Journal:** PLOS Computational Biology  
**Submission ID:** PCOMPBIOL-D-26-00133  
**Status:** Submitted (December 2025)  
**Revision:** Addressed reviewer feedback (January 2026)

## Data Availability Statement

As per PLOS policy, all data necessary to reproduce results are either:
1. Included in the manuscript figures and tables
2. Available from public repositories (BioModels)
3. Generated from provided models and scripts

No proprietary or restricted-access data were used in this study.
