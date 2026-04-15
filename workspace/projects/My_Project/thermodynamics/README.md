# Thermodynamic Constraints in Cellular Decision-Making

Demonstrates how thermodynamic constraints drive energy-efficient cellular decision-making in Bacillus subtilis sporulation using hybrid Petri nets (stochastic-continuous models).

## Manuscript

**Title:** Thermodynamic Constraints Drive Hierarchical Preemption in Cellular Decision-Making: A Hybrid Petri Net Framework with Application to Bacillus subtilis Sporulation

**Status:** Published on arXiv (January 7, 2026)

**arXiv ID:** [Add arXiv ID when available]

**Location:** `manuscript/thermodynamic_hierarchy_petri_nets.tex` (9 pages)

## Key Findings

| Condition | ATP Level | Efficiency | Spore Yield | Key Metric |
|-----------|-----------|----------|-------------|------------|
| **Normal** | 5000 mM | 11.6 mM/spore | 75 mM (100%) | Baseline efficiency |
| **Stress** | 300 mM (94% depletion) | 0.73 mM/spore | 67 mM (89%) | 16× efficiency gain |

- **Crisis Management:** ATP drops to 1 mM (99.7% depletion) but recovers via continuous regeneration
- **Energy Buffer:** GTP accumulation (+4974 mM, 166% increase) provides alternative energy source
- **Hybrid Dynamics:** Stochastic regulatory transitions + continuous metabolic sources

## Directory Structure

```
thermodynamics/
├── manuscript/          # LaTeX sources and published PDF (DO NOT MODIFY)
│   ├── thermodynamic_hierarchy_petri_nets.tex  # Main manuscript
│   ├── *.pdf           # Published figures (3 PDFs)
│   ├── arxiv_submission.txt  # arXiv metadata
│   ├── sections/       # Future: individual sections (if needed)
│   ├── tables/         # Future: data tables
│   ├── references/     # Future: bibliography management
│   └── supplementary/  # Future: supplementary materials
├── models/
│   ├── manuscript/     # 2 core .shy models (normal + stress conditions)
│   └── archive/        # Development/testing models
│       └── base/       # Base model variants
├── figures/
│   ├── [3 PDFs]       # Published figures (thermodynamic landscape, basin of attraction, stress)
│   └── archive/        # Development/intermediate figures
├── data/               # Simulation data and analysis results
│   └── archive/        # Experimental/tuning data
├── scripts/            # 4 Python scripts for figure generation
│   ├── generate_thermodynamic_landscape.py
│   ├── plot_basin_attraction.py
│   ├── plot_decision_cascade.py
│   └── plot_thermodynamic_landscape.py
└── doc/
    ├── experiments/    # Chronological experiment logs
    └── protocols/      # Parameter guides & simulation protocols
```

## Key Files

**Published Manuscript:**
- `manuscript/thermodynamic_hierarchy_petri_nets.tex` - Main LaTeX source
- `manuscript/thermodynamic_hierarchy_petri_nets.pdf` - Published PDF

**Models:**
- `models/manuscript/bacillus_sporulation_normal.shy` - Normal conditions (ATP 5000 mM)
- `models/manuscript/bacillus_sporulation_stress.shy` - Stress conditions (ATP 300 mM)

**Figures:**
- `figures/thermodynamic_landscape.pdf` - Energy landscape visualization
- `figures/bacillus_basin_of_attraction.pdf` - Basin of attraction analysis
- `figures/bacillus_sporulation_stress.pdf` - Stress response dynamics

**Analysis Scripts:**
- `scripts/generate_thermodynamic_landscape.py` - Generate energy landscapes
- `scripts/plot_basin_attraction.py` - Analyze attractor basins
- `scripts/plot_thermodynamic_landscape.py` - Visualize thermodynamic constraints

## Framework: Hybrid Petri Nets

**Stochastic Transitions:** Regulatory events (gene activation, signaling)
**Continuous Sources:** Metabolic flux (ATP regeneration, nutrient availability)
**Thermodynamic Constraints:** Inhibitor arcs, energy-coupled rate functions

## Citation

```bibtex
@article{simao2026thermodynamic,
  title={Thermodynamic Constraints Drive Hierarchical Preemption in Cellular Decision-Making: 
         A Hybrid Petri Net Framework with Application to Bacillus subtilis Sporulation},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={arXiv preprint arXiv:[ID]},
  year={2026}
}
```

## Related Projects

- **MAPK Cascade:** Signal Hierarchical Petri Nets capturing emergent nonlinear dynamics
- **Signal Hierarchy:** Framework for hierarchical signal processing with thermodynamic orchestration

## Status

✓ Manuscript published on arXiv (January 7, 2026)
✓ Models and data available in repository
✓ Figure generation scripts documented
⏳ Awaiting arXiv DOI assignment
⏳ Journal submission pending
