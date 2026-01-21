# Data Directory - arXiv 2601.04335

This directory contains references to simulation data used in the manuscript. Following repository guidelines, large datasets are **not included** in version control.

## Simulation Data Policy

**Excluded from Repository:**
- Raw simulation trajectories (batch results)
- Stochastic ensemble datasets
- Intermediate analysis files
- Large-scale parameter sweeps

**Reason:** Simulation datasets can exceed 50 MB. These can be regenerated using the scripts provided in `../scripts/`.

## Reproducing Simulation Data

### Required Software
- SHYpn framework (Python 3.8+)
- NumPy, SciPy, Matplotlib
- Hybrid simulator (tau-leaping for stochastic + ODE for continuous)

### Generating Thermodynamic Landscape Data

```bash
cd ../scripts
python generate_thermodynamic_landscape.py
```

**Output:**
- `thermodynamic_landscape.pdf` (Figure 1 in manuscript)
- CSV data files with basin geometry

### Generating Basin of Attraction Data

```bash
python plot_basin_attraction.py
```

**Output:**
- `bacillus_basin_of_attraction.pdf` (Figure 2)
- ATP threshold calculations (2.38 mM predicted)

### Generating Decision Cascade Figure

```bash
python plot_decision_cascade.py
```

**Output:**
- `decision_cascade.pdf` (Figure 3)
- Hierarchical layer visualization

### Stress Condition Simulations

**Normal Conditions (ATP = 5000 mM):**
```python
from shypn import load_model
model = load_model('../models/bacillus_sporulation_normal.shy')
# Run simulation with provided initial conditions
```

**Stress Conditions (ATP = 300 mM, 94% depletion):**
```python
model = load_model('../models/bacillus_sporulation_stress.shy')
# Demonstrates 16× ATP efficiency improvement
```

## Key Results

| Condition | ATP Level | Efficiency | Spore Yield | ATP per Spore |
|-----------|-----------|-----------|-------------|---------------|
| **Normal** | 5000 mM | 11.6 mM/spore | 75 mM (100%) | 11.6 mM |
| **Stress** | 300 mM | 0.73 mM/spore | 67 mM (89%) | 0.73 mM |
| **Improvement** | -94% | **16× better** | -11% | **16× less** |

**Crisis Management:**
- ATP minimum: 1 mM (99.7% depletion)
- Recovery via continuous regeneration
- GTP buffer: +4974 mM (166% increase)

## Experimental Validation

**ATP Threshold Prediction:**
- SHYPN model: 2.38 mM
- Experimental (Fujita & Losick 2005): 2.21 ± 0.18 mM
- **Error: 7%** - demonstrates predictive capability

## Contact

For questions about data reproduction or simulation protocols:
- Open an issue in the SHYpn GitHub repository
- Refer to manuscript Section 4 (Materials and Methods)
