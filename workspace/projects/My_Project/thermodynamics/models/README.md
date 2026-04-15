# Models Directory

## Manuscript Models

Core models used in the published manuscript.

### Published Models

1. **bacillus_sporulation_normal.shy**
   - Condition: Normal (ATP 5000 mM)
   - Efficiency: 11.6 mM ATP per spore
   - Spore Yield: 75 mM (100% baseline)
   - Purpose: Baseline sporulation dynamics

2. **bacillus_sporulation_stress.shy**
   - Condition: Stress (ATP 300 mM, 94% depletion)
   - Efficiency: 0.73 mM ATP per spore (16× improvement)
   - Spore Yield: 67 mM (89% of normal)
   - Purpose: Energy-efficient stress response

### Model Format

- **File Type:** .shy (SHYPN model format)
- **Framework:** Hybrid Petri Nets (stochastic + continuous)
- **Features:**
  - Stochastic transitions for regulatory events
  - Continuous sources for metabolic flux
  - Thermodynamic constraints via inhibitor arcs
  - Energy-coupled rate functions

## Archive Directory

Development and testing models, parameter exploration variants.

### Archive Structure

- `archive/base/` - Base model variants and initial implementations
- Additional subdirectories for specific experiments or parameter sweeps

## Model Metadata

**Created:** January 2026
**Software:** SHYPN v1.0
**Python:** 3.x required
**Dependencies:** See main project pyproject.toml

## Usage

```python
from shypn import load_model, simulate

# Load model
model = load_model('models/manuscript/bacillus_sporulation_stress.shy')

# Run simulation
results = simulate(model, duration=180)

# Analyze results
print(f"Final ATP: {results['ATP'][-1]} mM")
print(f"Spore Yield: {results['Spore'][-1]} mM")
```

## Model Development Notes

- View state files (.view_state*.json) store GUI layout preferences
- Models tested with SHYPN hybrid simulator (tau-leaping + continuous integration)
- Thermodynamic validation performed against experimental data
