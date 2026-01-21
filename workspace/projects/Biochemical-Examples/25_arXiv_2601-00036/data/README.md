# Vibrio fischeri Quorum Sensing Data

This directory contains simulation results for the V. fischeri quorum sensing model.

## Expected Results

### Low Cell Density (< 10⁷ cells/mL)
- **AHL_external**: Remains low (~100 molecules)
- **LuxR-AHL**: Minimal complex formation
- **Bioluminescence**: Off (< 10 photons)
- **Interpretation**: Below quorum threshold

### High Cell Density (> 10⁹ cells/mL)
- **AHL_external**: Accumulates (> 1000 molecules)
- **LuxR-AHL**: Saturates receptors
- **Bioluminescence**: On (> 10⁵ photons)
- **Interpretation**: Above quorum threshold, synchronized activation

### Key Metrics
- **Threshold crossing time**: ~300-400 min (depends on cell density)
- **Bioluminescence onset**: ~20 min after threshold
- **Max light output**: 10⁵-10⁶ photons/s

## Data Not Included

Simulation trajectories are **not included** because:
- Generated on-demand from model
- File size varies with number of trajectories
- Easy to regenerate using scripts

## Reproducing Results

### Single Trajectory
```bash
cd ..
python scripts/vfischeri_quorum_sensing.py \
    --cells 1e8 \
    --time 600 \
    --output data/single_trajectory/
```

### Multiple Trajectories (Population Heterogeneity)
```bash
python scripts/vfischeri_quorum_sensing.py \
    --cells 1e8 \
    --time 600 \
    --trajectories 10 \
    --output data/population_study/
```

### Cell Density Scan
```bash
# Low density (no QS activation)
python scripts/vfischeri_quorum_sensing.py --cells 1e6 --time 600

# Medium density (threshold crossing)
python scripts/vfischeri_quorum_sensing.py --cells 1e8 --time 600

# High density (immediate activation)
python scripts/vfischeri_quorum_sensing.py --cells 1e10 --time 600
```

## Output Files

Running the script generates:
- **trajectories.json**: Time series data (AHL, LuxR-AHL, Light, etc.)
- **quorum_sensing_dynamics.png**: 4-panel plot (AHL, complex, light, phase portrait)
- **metrics.txt**: Threshold times and statistics

## Signal Place Detection

The model automatically identifies signal places:
```
Signal Place Detection:
  t_txn_luxAB: Ψ = {AHL_external}
  Classification: External Signal
  
Analysis: AHL_external is referenced in the luxAB rate formula
but has no arc connections to t_txn_luxAB → it's a signal place
(information transfer without mass transfer).
```

This demonstrates the unified formalism where:
- **Signal places (Ψ)** enable information-based regulation
- **Weak independence** preserved (no dependency created)
- **Hierarchy** emerges from signal-mediated control
