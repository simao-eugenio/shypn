# arXiv:2512.17106 - Weak Independence and Coupled Parallelism in Biological Petri Nets

**Authors:** Eugênio Simão  
**Submitted:** December 23, 2024  
**Status:** Published on arXiv  

## Paper Content

This directory contains all data, models, figures, and scripts related to the arXiv preprint:

> **Weak Independence Theory and Parallelism in Extended Biological Petri Nets**  
> Eugênio Simão (UFSC)  
> arXiv:2512.17106 [q-bio.QM]  
> https://arxiv.org/abs/2512.17106

## Directory Structure

```
23_arXiv_2512-17106/
├── README.md                    # This file
├── manuscript/                  # Published manuscript
│   └── 2512.17106v1.pdf        # arXiv PDF
├── models/                      # Biological Petri net models used in paper
│   └── lac_operon.shy          # Lac operon example (Figure 2)
├── figures/                     # Figures from the paper
│   ├── lac_operon.pdf          # Figure 2: Lac operon regulatory structure
│   └── speedup_plot.pdf        # Figure 3: Performance speedup results
├── scripts/                     # Analysis scripts
│   └── classify_all_dependencies.py  # BioModels dependency analysis (Table 3)
└── data/                        # Experimental data
    └── biomodels_analysis/      # 100 BioModels classification results
        └── classification_results.csv
```

## Key Findings

- **96.93% weakly independent** transition pairs across 100 BioModels
- **1,775 species, 2,234 reactions** analyzed
- **2.6× speedup** on 30% of models using parallel tau-leaping

## Reproducibility

### BioModels Analysis
```bash
# Run dependency classification on 100 BioModels
python scripts/classify_all_dependencies.py
```

### Lac Operon Example
```bash
# Load and analyze the lac operon model
shypn models/lac_operon.shy
```

## Citations

If you use this work, please cite:

```bibtex
@article{simao2024weak,
  title={Weak Independence Theory and Parallelism in Extended Biological Petri Nets},
  author={Sim{\~a}o, Eug{\^e}nio},
  journal={arXiv preprint arXiv:2512.17106},
  year={2024}
}
```

## Contact

Eugênio Simão  
Universidade Federal de Santa Catarina (UFSC)  
eugenio.simao@ufsc.br
