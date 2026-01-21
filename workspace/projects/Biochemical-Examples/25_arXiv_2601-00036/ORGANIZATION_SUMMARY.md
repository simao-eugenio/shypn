# Organization Summary: arXiv 2601.00036

✅ **Complete** - All materials from published arXiv paper organized

## Directory Structure

```
25_arXiv_2601-00036/
├── README.md                          # Main documentation
├── ORGANIZATION_SUMMARY.md            # This file
├── manuscript/
│   └── 2601.00036v1.pdf              # ✓ Published PDF
├── models/
│   └── vfischeri_quorum_sensing.shy   # ✓ V. fischeri QS model
├── figures/
│   └── README.md                      # ✓ Figure descriptions
├── scripts/
│   ├── vfischeri_quorum_sensing.py    # ✓ Model builder + simulator
│   └── parameters.json                # ✓ Model parameters
└── data/
    └── README.md                      # ✓ Data policy + instructions
```

## What's Included

### ✓ Manuscript
- Published PDF: `manuscript/2601.00036v1.pdf`
- arXiv link: https://arxiv.org/abs/2601.00036

### ✓ Model
- `models/vfischeri_quorum_sensing.shy` - Complete V. fischeri quorum sensing model
  - 13 places (genes, mRNAs, proteins, AHL, bioluminescence)
  - 10 transitions (transcription, translation, synthesis, binding)
  - Signal place: AHL_external (demonstrates 13-tuple formalism)

### ✓ Scripts
- `scripts/vfischeri_quorum_sensing.py` - Model creation and simulation
  - Automatic signal place detection
  - Quorum sensing metrics calculation
  - 4-panel dynamics plot generation
- `scripts/parameters.json` - Literature-derived parameters

### ✓ Documentation
- `data/README.md` - Expected results and reproduction instructions
- `figures/README.md` - Figure descriptions and generation
- **Simulation data NOT included** (generated on-demand)

## Reproducibility

All scripts and model are included to reproduce paper results.

### Run Quorum Sensing Simulation
```bash
python scripts/vfischeri_quorum_sensing.py \
    --cells 1e8 \
    --time 600 \
    --trajectories 5 \
    --output data/results/
```

### Analyze Signal Places
The script automatically detects signal places:
```
Signal Place Detection:
  t_txn_luxAB: Ψ = {AHL_external}
  Classification: External Signal
```

### Generate Figures
```bash
# Creates quorum_sensing_dynamics.png and .pdf
python scripts/vfischeri_quorum_sensing.py \
    --cells 1e8 \
    --time 600 \
    --output figures/
```

## Key Contributions (from paper)

**Theoretical:**
- **13-tuple formalism** integrating weak independence + signal hierarchy
- **Signal places (Ψ)** - places in rate formulas without arc connections
- **Unified theory** distinguishing information flow from mass transfer

**Practical:**
- V. fischeri quorum sensing as validation example
- Automatic signal place detection algorithm
- Backward compatible with classical Bio-PN semantics

## Model Highlights

**V. fischeri Quorum Sensing:**
- **LuxI/LuxR system**: AHL synthesis and reception
- **Population-level coordination**: External AHL accumulation
- **Signal place**: AHL_external regulates luxAB without arc connection
- **Weak independence**: Preserved despite shared regulation

## Publication Info

**Title:** Unifying Weak Independence and Signal Hierarchy Theory: Extended Biological Petri Net Formalism with Application to Vibrio fischeri Quorum Sensing  
**Author:** Eugênio Simão (UFSC)  
**Published:** January 1, 2025  
**arXiv:** 2601.00036 [q-bio.QM]  
**DOI:** https://doi.org/10.48550/arXiv.2601.00036

## Related Papers

This work unifies two previous theories:
1. **arXiv:2512.17106** - Weak Independence and Coupled Parallelism
2. **arXiv:2512.22415** - Hierarchical Preemption (lambda phage)
