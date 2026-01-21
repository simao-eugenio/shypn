# Organization Summary: arXiv 2512.22415

✅ **Complete** - All materials from published arXiv paper organized

## Directory Structure

```
24_arXiv_2512-22415/
├── README.md                          # Main documentation
├── ORGANIZATION_SUMMARY.md            # This file
├── manuscript/
│   └── 2512.22415v1.pdf              # ✓ Published PDF
├── models/
│   ├── lambda_symmetric_bistable.shy  # ✓ ZERO symmetry (bistable)
│   ├── lambda_symmetric_UV.shy        # ✓ ZERO + UV (lytic bias)
│   └── lambda_balanced_UV.shy         # ✓ BALANCED + UV (CI vulnerable)
├── figures/
│   └── README.md                      # ✓ Figure descriptions + generation instructions
├── scripts/
│   └── generate_paper_figures.py      # ✓ Reproduces all 5 figures
└── data/
    └── README.md                      # ✓ Simulation data policy + instructions
```

## What's Included

### ✓ Manuscript
- Published PDF: `manuscript/2512.22415v1.pdf`
- arXiv link: https://arxiv.org/abs/2512.22415

### ✓ Models (3 variants)
- `models/lambda_symmetric_bistable.shy` - ZERO rate symmetry, no UV stress
- `models/lambda_symmetric_UV.shy` - ZERO + UV stress (RecA cleavage)
- `models/lambda_balanced_UV.shy` - BALANCED rates + UV stress
- **All models ready to run** in SHYpn

### ✓ Scripts
- `scripts/generate_paper_figures.py` - Reproduces all 5 paper figures
  - Reads from batch simulation results
  - Generates outcome distributions, scatter plots, time courses, etc.
  - Produces publication-quality PDFs

### ✓ Documentation
- `data/README.md` - Simulation data structure and reproduction instructions
- `figures/README.md` - Figure descriptions and generation instructions
- **Simulation data NOT included** (50+ MB, can be regenerated from models)

## Reproducibility

All models and scripts are included to reproduce paper results.

### Run Simulations
```bash
# Generate 100 stochastic replicates for each condition
shypn models/lambda_symmetric_bistable.shy --batch 100 --output data/batch_results/zero_no_uv/
shypn models/lambda_symmetric_UV.shy --batch 100 --output data/batch_results/zero_with_uv/
shypn models/lambda_balanced_UV.shy --batch 100 --output data/batch_results/balanced_with_uv/
```

### Generate Figures
```bash
python scripts/generate_paper_figures.py
```

## Key Results (from paper)

- **Hierarchical preemption** mechanism in CI-Cro switch
- **Bistability**: 42% lysogenic, 48% lytic (symmetric rates, no UV)
- **UV stress**: Shifts to 4% lysogenic, 86% lytic (RecA cleavage)
- **Information-theoretic control** distinguishes regulatory coupling from conflict

## Model Architecture

- **12 places**: CI_gene, Cro_gene, mRNAs, proteins, dimers, RecA system
- **17 transitions**: Transcription, translation, dimerization, degradation, RecA cleavage
- **31 arcs**: Regulatory structure (CI and Cro mutually inhibit transcription)

## Publication Info

**Title:** Hierarchical Preemption: A Novel Information-Theoretic Control Mechanism in Lambda Phage Decision-Making  
**Author:** Eugênio Simão (UFSC)  
**Published:** December 28, 2024  
**arXiv:** 2512.22415 [q-bio.QM]  
**DOI:** https://doi.org/10.48550/arXiv.2512.22415
