# MAPK Cascade Computational Modes

Demonstrates Signal Hierarchical Petri Nets (SHYPN) framework capturing four computational modes in ERK MAPK cascades through unified feedback architectures.

## Manuscript

**Title:** Signal Hierarchical Petri Nets Capture Emergent Nonlinear Dynamics in MAPK Cascades

**Status:** Publication-ready (5.0/5 stars)

**Target:** PLoS Computational Biology

**Location:** `manuscript/manuscript_capabilities_biology_first.tex` (12 pages, 680KB PDF)

## Computational Modes

Four emergent behaviors from single cascade architecture with tuned feedback:

| Mode | α (PP2A) | β (MKP) | α/β Ratio | Key Metric |
|------|----------|---------|-----------|------------|
| **Bistability** | 15.0 | 1.0 | 15.0 | 577× state separation |
| **Excitability** | 1.0 | 15.0 | 0.067 | 500× all-or-nothing amplification |
| **Oscillations** | 0.2 | 20.0 | 0.01 | 20 cycles/min sustained |
| **Adaptation** | 0.15 | 200.0 | 0.001 | 96.4% adaptation, 98.8% efficiency |

- **α (positive feedback):** ERK-PP → PP2A degradation (autocatalytic)
- **β (negative feedback):** ERK-PP → MKP synthesis (Hill kinetics)

## Directory Structure

```
mapk/
├── manuscript/          # LaTeX sources and compiled PDF
├── models/
│   ├── manuscript/      # 4 core .shy models (one per mode)
│   └── archive/         # 14 development models (tuning, testing)
├── figures/
│   ├── manuscript/      # 6 PDFs used in paper (Figures 1-6)
│   └── archive/         # 21 development figures (PNGs, intermediates)
├── data/
│   ├── manuscript/      # 9 CSVs used for manuscript figures
│   └── archive/         # 12 experimental/tuning CSVs
├── scripts/             # 9 Python scripts for figure generation
└── doc/
    ├── experiments/     # 8 experiment logs (chronological)
    ├── protocols/       # 5 parameter guides & simulation protocols
    └── *.md            # 5 technical documentation files
```

## Key Files

### Models (manuscript/)
- `erk_cascade_stress.shy` - Bistability (Fig 1)
- `erk_cascade_excitability_phasecontrol.shy` - Excitability (Fig 2)
- `erk_cascade_oscillation_timed.shy` - Oscillations (Fig 3)
- `erk_cascade_adaptation.shy` - Adaptation (Fig 4)

### Figures (manuscript/)
- `mapk_basin_of_attraction.pdf` - Bistability hysteresis (Fig 1)
- `mapk_excitability.pdf` - All-or-nothing spikes (Fig 2)
- `mapk_oscillations_timed.pdf` - Sustained oscillations (Fig 3)
- `adaptation_spike_timecourse.pdf` - Near-perfect adaptation (Fig 4)
- `cascade_activation_timecourse.pdf` - Raf→MEK→ERK timing (Fig 5)
- `erk_cascade_adaptation.pdf` - Architecture diagram (Fig 6)

### Scripts
- `generate_excitability_figure.py` - Figure 2 (dose-response)
- `generate_oscillations_figure.py` - Figure 3 (time series)
- `generate_adaptation_figure.py` - Figure 4 (adaptation dynamics)
- `generate_cascade_activation_figure.py` - Figure 5 (cascade timing)
- `plot_adaptation_spike.py` - Alternative adaptation visualization

## Reproduction

1. **Run simulations:** Open models in SHYPN GUI, simulate with specified parameters
2. **Generate figures:** Run scripts from `scripts/` directory
3. **Compile manuscript:** `cd manuscript && pdflatex manuscript_capabilities_biology_first.tex`

## Dependencies

- SHYPN platform (Signal Hierarchical Petri Nets)
- Python 3.x with pandas, numpy, matplotlib
- LaTeX with standard packages

## Publication Timeline

- ✅ Manuscript refinement complete (Jan 2026)
- ✅ Parameter validation complete
- ⏳ arXiv preprint submission (pending)
- ⏳ PLoS Comp Biol submission (after arXiv)

## Citation

```
Eugenio, S., et al. (2026). Signal Hierarchical Petri Nets Capture 
Emergent Nonlinear Dynamics in MAPK Cascades. In preparation for 
PLoS Computational Biology.
```

## Contact

For questions about models or reproduction: simao.eugenio@[institution]
