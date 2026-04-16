# MAPK Simulation Data

CSV files containing time series data from SHYPN simulations of MAPK cascade models.

## Manuscript Data (9 CSVs)

Simulation outputs used to generate manuscript figures. All referenced by scripts in `../scripts/`:

### Bistability (1 file)
- **simulation_data_stress.csv**
  - Model: erk_cascade_stress.shy
  - Duration: 300s steady-state
  - Used for: Figure 1 (basin of attraction)
  - Key columns: Time, ERK_PP, Growth_Factor

### Excitability (6 files)
- **simulation_data_basal_tunned.csv** - 0 nM GF (basal activity)
- **simulation_data_subthreshold_50nM.csv** - 5 nM GF (below threshold)
- **simulation_data_dose_20nM_tuned.csv** - 20 nM GF (suprathreshold)
- **simulation_data_dose_40nM_tuned.csv** - 40 nM GF
- **simulation_data_dose_60nM_tuned.csv** - 60 nM GF
- **simulation_data_dose_80nM_tuned.csv** - 80 nM GF (maximum)
  - Model: erk_cascade_excitability_phasecontrol.shy
  - Duration: 120s per dose
  - Used for: Figure 2 (dose-response curve)
  - Script: `generate_excitability_figure.py`
  - Key finding: Sharp threshold at 10 nM, constant 505 nM spike amplitude above

### Oscillations (1 file)
- **simulation_data_oscillation.csv**
  - Model: erk_cascade_oscillation_timed.shy
  - Duration: 180s (54 complete cycles)
  - Used for: Figure 3 (sustained oscillations)
  - Scripts: `generate_oscillations_figure.py`, `plot_oscillations.py`
  - Key finding: 20.2 oscillations/min, period 2.98±0.30s

### Adaptation (1 file)
- **simulation_data_adaptation_new.csv**
  - Model: erk_cascade_adaptation.shy
  - Duration: 180s with 10s GF pulse at t=50s
  - Used for: Figures 4 (adaptation) and 5 (cascade timing)
  - Scripts: `generate_adaptation_figure.py`, `plot_adaptation_spike.py`, `generate_cascade_activation_figure.py`
  - Key finding: 96.4% adaptation (976 nM peak → 36 nM steady, baseline 0.3 nM)

## Archive Data (12 CSVs)

Experimental and intermediate simulation data from parameter tuning and model development:

### Excitability Development (8 files)
Pre-tuning and unoptimized versions:
- **simulation_data_excitability.csv** - Early excitability attempt (pre-phase control)
- **simulation_data_basal.csv** - Untuned basal activity
- **simulation_data_dose_20nM.csv** - Untuned 20 nM (before optimization)
- **simulation_data_dose_40nM.csv** - Untuned 40 nM
- **simulation_data_dose_60nM.csv** - Untuned 60 nM
- **simulation_data_dose_80nM.csv** - Untuned 80 nM
- **simulation_data_tunned.csv** - Generic tuning test (unclear purpose)
- **simulation_data_new.csv** - Generic test data

### Adaptation Development (2 files)
Earlier adaptation experiments:
- **simulation_data_adaptation.csv** - Initial adaptation attempt (insufficient)
- **simulation_data_adaptation_doubt.csv** - Parameter validation test
  - Referenced in: `analyze_adaptation_criteria.py` (debugging script)

### Test Files (2 files)
- **simulation_data.csv** - Generic base cascade test
- **simulation_data_test_pulse.csv** - Pulse stimulus testing

## Data Format

All CSV files follow SHYPN standard format:

```csv
Time (s),ERK_PP (mM),MEK_P (mM),Raf_P (mM),Growth_Factor (mM),MKP (mM),PP2A (mM),...
0.0,0.0003,0.01,0.02,0.0,0.5,1.0,...
0.1,0.0005,0.012,0.025,10.0,0.51,0.98,...
```

**Note:** Concentrations in **mM**. Scripts convert to nM for plotting (× 1000).

## Script Dependencies

Scripts automatically resolve paths using:
```python
data_file = Path(__file__).parent.parent / "data" / "manuscript" / "filename.csv"
```

All manuscript scripts verified to use correct `data/manuscript/` paths (Jan 2026).

## Regenerating Data

To regenerate manuscript data:

1. Open model in SHYPN GUI
2. Configure simulation parameters (see `../doc/protocols/`)
3. Run simulation with specified duration
4. Export to CSV: File → Export Data → simulation_data_[mode].csv
5. Move to `data/manuscript/` directory
6. Run corresponding script from `../scripts/`

## Data Validation

All manuscript CSVs validated against:
- Published MAPK dynamics (response times, amplitudes)
- Thermodynamic constraints (ΔG validation)
- Manuscript Table 1 parameters
- Figure generation scripts (no errors)

**Last validation:** January 12, 2026
