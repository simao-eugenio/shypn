# Lambda Phage Experiments

This directory contains experimental scripts for validating the lambda phage Extended Bio-PN model against 60+ years of experimental literature.

## Experiments

### ⭐ Experiment 1: Bistability Statistics
**Script**: `run_bistability.py`  
**Goal**: Validate 50-50% lysogeny-lysis decision  
**Expected**: ~52% lysogeny (matches Arkin 1998)  
**Output**: `figure2_bistability_validation.png`, `bistability_results.json`

```bash
python run_bistability.py
```

### ⭐ Experiment 2: UV-Dose Response  
**Script**: `run_uv_dose.py`  
**Goal**: Reproduce UV-induced prophage induction rates  
**Expected**: 18%/82%/98% for low/medium/high doses (Roberts 1978)  
**Output**: `figure3_uv_dose_response.png`, `uv_dose_results.json`

```bash
python run_uv_dose.py
```

### Experiment 3: Temporal Dynamics (Coming soon)
**Script**: `run_temporal_kinetics.py`  
**Goal**: Validate CI decay and Cro rise kinetics  
**Expected**: CI half-life ~10 units, Cro peak at 30-40 units (Shean 1975)

### Experiment 4: Autoregulation Effect (Coming soon)
**Script**: `run_autoregulation.py`  
**Goal**: Quantify positive feedback contribution  
**Expected**: 2.5× noise reduction, 10× lower escape rate (Ptashne 2004)

### Experiment 5: Cooperativity (Coming soon)
**Script**: `run_cooperativity.py`  
**Goal**: Validate dimerization mechanism  
**Expected**: Hill coefficient n≈2 (Ptashne 2004)

### Experiment 6: Performance Benchmarks (Coming soon)
**Script**: `run_performance.py`  
**Goal**: Quantify computational speedup  
**Expected**: 150× faster than exact SSA

### Experiment 7: Weak Independence (Coming soon)
**Script**: `run_weak_independence.py`  
**Goal**: Characterize concurrent transitions  
**Expected**: 60-70% weakly independent pairs

## Results Directory Structure

```
results/
├── figure2_bistability_validation.png      # 4-panel bistability analysis
├── bistability_results.json                 # Raw trajectory data
├── figure3_uv_dose_response.png            # UV-dose curve with literature comparison
├── uv_dose_results.json                     # Induction rates per dose
├── figure4_temporal_dynamics.png           # CI/Cro kinetics (TODO)
├── figure5_performance_benchmarks.png      # Speedup analysis (TODO)
└── ... (additional results)
```

## Running All Experiments

```bash
# Run experiments in order
python run_bistability.py
python run_uv_dose.py
# python run_temporal_kinetics.py  # TODO
# python run_autoregulation.py     # TODO
# python run_cooperativity.py      # TODO
# python run_performance.py        # TODO
```

## Validation Criteria

✅ **Bistability**: Lysogeny rate 45-55% (Arkin 1998)  
✅ **UV-dose**: 18%/82%/98% induction (Roberts 1978)  
✅ **CI kinetics**: Half-life ~10 units (Shean 1975)  
✅ **Cro kinetics**: Peak at 30-40 units (Shean 1975)  
✅ **Performance**: >20× speedup with <5% error  

## Notes

- All experiments use tau-leaping with epsilon=0.03 (3% error tolerance)
- Random seeds are set for reproducibility
- Simulation times calibrated to match experimental timescales
- Results automatically saved to `../results/` directory
