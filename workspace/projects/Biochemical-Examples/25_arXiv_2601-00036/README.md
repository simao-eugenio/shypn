# arXiv:2601.00036 - Unifying Weak Independence and Signal Hierarchy Theory

**Authors:** Eugênio Simão  
**Submitted:** January 1, 2025  
**Status:** Published on arXiv  

## Paper Content

This directory contains all data, models, figures, and scripts related to the arXiv preprint:

> **Unifying Weak Independence and Signal Hierarchy Theory: Extended Biological Petri Net Formalism with Application to Vibrio fischeri Quorum Sensing**  
> Eugênio Simão (UFSC)  
> arXiv:2601.00036 [q-bio.QM]  
> https://arxiv.org/abs/2601.00036

## Directory Structure

```
25_arXiv_2601-00036/
├── README.md                          # This file
├── manuscript/                        # Published manuscript
│   └── 2601.00036v1.pdf              # arXiv PDF
├── models/                            # Vibrio fischeri quorum sensing model
│   └── vfischeri_quorum_sensing.shy  # Complete QS model with signal places
├── figures/                           # Figures from the paper
│   └── README.md                      # Figure descriptions
├── scripts/                           # Model creation and analysis scripts
│   ├── vfischeri_quorum_sensing.py   # Model builder and simulation
│   └── parameters.json                # Model parameters
└── data/                              # Simulation results
    └── README.md                      # Data policy + instructions
```

## Key Findings

- **Unified formalism** integrating weak independence + signal hierarchy
- **13-tuple** Bio-PN definition with signal places (Ψ)
- **Vibrio fischeri** quorum sensing as validation example
- **Signal place detection** identifies AHL_external as environmental signal

## Theoretical Contributions

### 1. Extended 13-Tuple Formalism
```
BioPN = ⟨P, T, Pre, Post, m₀, k, S, Φ, Σ, Reg, Ψ, E, A⟩
```

Where **Ψ** (signal places) are places referenced in rate functions but not connected by arcs.

### 2. Signal Place Classification
- **Internal signals**: ATP, ADP, NAD, metabolic regulators
- **External signals**: AHL, hormones, paracrine signals
- **Hybrid signals**: Ca²⁺, cAMP (dual role)

### 3. Integration with Weak Independence
- Signal places do NOT create dependencies
- Enables parallel execution despite shared regulatory signals
- Distinguishes information flow from mass transfer

## Model Architecture

**Vibrio fischeri Quorum Sensing:**
- **13 places**: LuxI/LuxR genes, mRNAs, proteins, AHL (internal/external), bioluminescence
- **10 transitions**: Transcription, translation, AHL synthesis/export, binding, light emission
- **Signal place**: AHL_external (referenced in luxAB rate formula, no arc connection)

## Reproducibility

### Run Quorum Sensing Simulation
```bash
python scripts/vfischeri_quorum_sensing.py \
    --cells 1e8 \
    --time 600 \
    --trajectories 5 \
    --output results/
```

### Analyze Signal Places
```bash
# Model automatically detects signal places in rate formulas
# Example output:
#   t_txn_luxAB: Ψ = {AHL_external}
#   Classification: External Signal
```

## Citations

If you use this work, please cite:

```bibtex
@article{simao2025unifying,
  title={Unifying Weak Independence and Signal Hierarchy Theory: Extended Biological Petri Net Formalism with Application to Vibrio fischeri Quorum Sensing},
  author={Sim{\~a}o, Eug{\^e}nio},
  journal={arXiv preprint arXiv:2601.00036},
  year={2025}
}
```

## Related Papers

This work builds on two previous arXiv papers:
1. **arXiv:2512.17106** - Weak Independence theory
2. **arXiv:2512.22415** - Signal Hierarchy theory (lambda phage)

## Contact

Eugênio Simão  
Universidade Federal de Santa Catarina (UFSC)  
eugenio.simao@ufsc.br
