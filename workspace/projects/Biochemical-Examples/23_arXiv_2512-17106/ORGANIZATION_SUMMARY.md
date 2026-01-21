# Organization Summary: arXiv 2512.17106

✅ **Complete** - All materials from published arXiv paper organized

## Directory Structure

```
23_arXiv_2512-17106/
├── README.md                          # Main documentation
├── ORGANIZATION_SUMMARY.md            # This file
├── manuscript/
│   └── 2512.17106v1.pdf              # ✓ Published PDF
├── models/
│   └── lac_operon.shy                 # ✓ Figure 2 example model
├── figures/
│   ├── lac_operon.pdf                 # ✓ Figure 2 from paper
│   └── speedup_plot.pdf               # ✓ Figure 3 from paper
├── scripts/
│   └── classify_all_dependencies.py   # ✓ BioModels analysis (Table 3)
└── data/
    └── biomodels_analysis/
        └── README.md                  # ✓ Data policy + instructions
```

## What's Included

### ✓ Manuscript
- Published PDF: `manuscript/2512.17106v1.pdf`
- arXiv link: https://arxiv.org/abs/2512.17106

### ✓ Models  
- `models/lac_operon.shy` - Lac operon example from Figure 2
- **Note:** 100 BioModels NOT included (external dataset, 100+ MB)

### ✓ Figures
- `figures/lac_operon.pdf` - Figure 2: Regulatory structure
- `figures/speedup_plot.pdf` - Figure 3: Performance results

### ✓ Scripts
- `scripts/classify_all_dependencies.py` - Reproduces Table 3 results
  - Analyzes transition dependencies across BioModels
  - Classifies: strongly independent, convergent, regulatory, competitive
  - Generates statistics for paper

### ✓ Data
- `data/biomodels_analysis/README.md` - Instructions for reproducing analysis
- **BioModels SBML files NOT included** (download from https://www.ebi.ac.uk/biomodels/)

## Reproducibility

All analysis scripts and models are included to reproduce paper results.

### Run BioModels Analysis
```bash
# Download BioModels from EBI (BIOMD 1-100, 200-299, 300-399, 400-499)
# Then run:
python scripts/classify_all_dependencies.py \
    --sbml-dir /path/to/biomodels \
    --output data/biomodels_analysis/results.csv
```

### Analyze Lac Operon Model
```bash
shypn models/lac_operon.shy
```

## Key Results (from paper)

- **96.93% weakly independent** transitions (can execute in parallel)
- **1,775 species, 2,234 reactions** across 100 models
- **2.6× speedup** on 30% of models

## Publication Info

**Title:** Weak Independence Theory and Parallelism in Extended Biological Petri Nets  
**Author:** Eugênio Simão (UFSC)  
**Published:** December 23, 2024  
**arXiv:** 2512.17106 [q-bio.QM]  
**DOI:** https://doi.org/10.48550/arXiv.2512.17106
