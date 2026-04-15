# MAPK Figures

Figure files for manuscript and development archive.

## Manuscript Figures (6 PDFs)

Publication-ready figures used in manuscript. All paths referenced in `manuscript/manuscript_capabilities_biology_first.tex`:

### Figure 1: Bistability
- **File:** `mapk_basin_of_attraction.pdf` (160 KB)
- **Model:** erk_cascade_stress.shy
- **Data:** simulation_data_stress.csv
- **Content:** Basin of attraction showing hysteresis, 577× state separation (HIGH: 577 nM, LOW: 1 nM ERK-PP)
- **Caption:** "Bistable MAPK memory with 577-fold state separation"

### Figure 2: Excitability
- **File:** `mapk_excitability.pdf` (48 KB)
- **Model:** erk_cascade_excitability_phasecontrol.shy
- **Data:** 6 CSVs (basal, subthreshold, 20/40/60/80 nM doses)
- **Script:** `generate_excitability_figure.py`
- **Content:** Dose-response curve showing all-or-nothing threshold at 10 nM, 500× amplification
- **Caption:** "Excitable MAPK dynamics with all-or-nothing spikes"

### Figure 3: Oscillations
- **File:** `mapk_oscillations_timed.pdf` (55 KB)
- **Model:** erk_cascade_oscillation_timed.shy
- **Data:** simulation_data_oscillation.csv
- **Script:** `generate_oscillations_figure.py`
- **Content:** Time series showing 54 sustained oscillations over 180s (20.2 cycles/min)
- **Caption:** "Sustained oscillatory MAPK dynamics"

### Figure 4: Adaptation
- **File:** `adaptation_spike_timecourse.pdf` (50 KB)
- **Model:** erk_cascade_adaptation.shy
- **Data:** simulation_data_adaptation_new.csv
- **Script:** `generate_adaptation_figure.py` or `plot_adaptation_spike.py`
- **Content:** Spike to 976 nM at 51s, adaptation to 36 nM by 180s (96.4% adaptation)
- **Caption:** "Adaptive MAPK dynamics with near-perfect adaptation"

### Figure 5: Cascade Timing
- **File:** `cascade_activation_timecourse.pdf` (34 KB)
- **Model:** erk_cascade_adaptation.shy
- **Data:** simulation_data_adaptation_new.csv
- **Script:** `generate_cascade_activation_figure.py`
- **Content:** Raf→MEK→ERK temporal activation sequence
- **Caption:** "Temporal activation sequence showing Raf→MEK→ERK propagation"

### Figure 6: Architecture
- **File:** `erk_cascade_adaptation.pdf` (27 KB)
- **Model:** Network diagram (not simulation output)
- **Content:** MAPK cascade architecture showing feedback loops
- **Caption:** "MAPK cascade architecture with feedback loops"

## Archive Figures (21 files)

Development figures including intermediate analyses, PNG versions, and experimental plots:

### Development PNGs (11 files)
PNG versions of manuscript figures and intermediate analyses:
- `mapk_basin_of_attraction.png` - Bistability PNG version
- `mapk_excitability.png` - Excitability PNG version
- `mapk_oscillations_timed.png` - Oscillations PNG version
- `adaptation_spike_timecourse.png` - Adaptation PNG version
- `cascade_activation_timecourse.png` - Cascade timing PNG version
- `excitability_basal_dynamics.png` - Basal activity analysis
- `excitability_dose_response_curve.png` - Dose-response only
- `excitability_dose_response_timeseries.png` - Full time series
- `excitability_spike_dynamics.png` - Spike shape analysis
- `tuned_model_v7_analysis.png` - Parameter optimization
- `plot.png` - Generic plotting test

### Experimental PDFs (7 files)
Analysis figures from parameter tuning:
- `excitability_analysis_problem.pdf` - Debugging low amplification
- `oscillation_analysis.pdf` - Oscillation parameter sweep
- `oscillation_phase_portrait.pdf` - Phase space analysis
- `oscillation_time_course.pdf` - Old oscillation attempt (pre-timed)
- `phase_control_architecture.pdf` - GF phase control mechanism diagram

### PNG duplicates (3 files)
- `excitability_analysis_problem.png`
- `oscillation_analysis.png`
- `oscillation_phase_portrait.png`
- `oscillation_time_course.png`
- `phase_control_architecture.png`

## Figure Generation

All manuscript figures can be regenerated from `../scripts/`:

```bash
cd ../scripts
python3 generate_excitability_figure.py      # Figure 2
python3 generate_oscillations_figure.py      # Figure 3
python3 generate_adaptation_figure.py        # Figure 4
python3 generate_cascade_activation_figure.py # Figure 5
```

Figures 1 and 6 generated manually (basin of attraction analysis and architecture diagram).

## Manuscript Paths

LaTeX references use relative paths from manuscript/:
```latex
\includegraphics[width=0.9\columnwidth]{../figures/manuscript/mapk_basin_of_attraction.pdf}
```

All paths verified and manuscript compiles successfully (680 KB PDF).

## File Sizes

Manuscript figures total: ~380 KB (compressed PDFs for publication)
Archive figures total: ~2.5 MB (development/analysis)
