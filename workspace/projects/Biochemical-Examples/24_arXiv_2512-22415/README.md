# arXiv:2512.22415 - Hierarchical Preemption in Lambda Phage Decision-Making

**Authors:** Eugênio Simão  
**Submitted:** December 28, 2024  
**Status:** Published on arXiv  

## Paper Content

This directory contains all data, models, figures, and scripts related to the arXiv preprint:

> **Hierarchical Preemption: A Novel Information-Theoretic Control Mechanism in Lambda Phage Decision-Making**  
> Eugênio Simão (UFSC)  
> arXiv:2512.22415 [q-bio.QM]  
> https://arxiv.org/abs/2512.22415

## Directory Structure

```
24_arXiv_2512-22415/
├── README.md                          # This file
├── manuscript/                        # Published manuscript
│   └── 2512.22415v1.pdf              # arXiv PDF
├── models/                            # Lambda phage bistable switch models
│   ├── lambda_symmetric_bistable.shy      # ZERO rate symmetry (bistable)
│   ├── lambda_symmetric_UV.shy            # ZERO + UV stress (lytic bias)
│   └── lambda_balanced_UV.shy             # BALANCED + UV (CI vulnerable)
├── figures/                           # Figures from the paper
│   ├── outcome_distributions.pdf      # Figure 1: Lysogenic vs lytic outcomes
│   ├── scatter_plots.pdf              # Figure 2: CI-Cro state space
│   ├── time_courses.pdf               # Figure 3: Representative trajectories
│   ├── rate_symmetry.pdf              # Figure 4: Transcription rate comparison
│   └── summary_bars.pdf               # Figure 5: Outcome percentages
├── scripts/                           # Analysis and figure generation scripts
│   └── generate_paper_figures.py      # Reproduces all figures from batch results
└── data/                              # Simulation results
    └── batch_results/                 # Stochastic simulation data (100 replicates each)
        ├── zero_no_uv/               # Symmetric, no stress → bistability
        ├── zero_with_uv/             # Symmetric + UV → lytic bias
        └── balanced_with_uv/         # Balanced + UV → CI vulnerable
```

## Key Findings

- **Hierarchical preemption** mechanism discovered in lambda phage CI-Cro switch
- **Bistability** with ZERO rate symmetry (42% lysogenic, 48% lytic)
- **UV stress** shifts outcome to 4% lysogenic, 86% lytic via RecA cleavage
- **Information-theoretic control** distinguishes regulatory coupling from conflict

## Model Architecture

- **12 places**: Genes (CI_gene, Cro_gene), mRNAs, proteins, dimers, RecA system
- **17 transitions**: Transcription, translation, dimerization, degradation, RecA cleavage
- **Regulatory structure**: CI and Cro mutually inhibit transcription (hierarchical preemption)

## Reproducibility

### Generate All Figures
```bash
python scripts/generate_paper_figures.py
```

This script reads from `data/batch_results/` and generates all 5 figures.

### Run Simulations
```bash
# Load each model and run 100 stochastic replicates
shypn models/lambda_symmetric_bistable.shy
shypn models/lambda_symmetric_UV.shy  
shypn models/lambda_balanced_UV.shy
```

## Citations

If you use this work, please cite:

```bibtex
@article{simao2024hierarchical,
  title={Hierarchical Preemption: A Novel Information-Theoretic Control Mechanism in Lambda Phage Decision-Making},
  author={Sim{\~a}o, Eug{\^e}nio},
  journal={arXiv preprint arXiv:2512.22415},
  year={2024}
}
```

## Contact

Eugênio Simão  
Universidade Federal de Santa Catarina (UFSC)  
eugenio.simao@ufsc.br
