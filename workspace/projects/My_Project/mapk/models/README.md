# MAPK Models

Signal Hierarchical Petri Net (.shy) models demonstrating four computational modes in ERK MAPK cascades.

## Manuscript Models (4 files)

Core models used in manuscript figures. Each demonstrates one computational mode:

### 1. erk_cascade_stress.shy - Bistability (Figure 1)
- **Parameters:** α=15.0, β=1.0, α/β=15.0
- **Mechanism:** Strong positive feedback (PP2A degradation) dominates
- **Behavior:** Hysteresis with 577× HIGH/LOW state separation
- **Modified:** Jan 8, 11:29

### 2. erk_cascade_excitability_phasecontrol.shy - Excitability (Figure 2)
- **Parameters:** α=1.0, β=15.0, α/β=0.067
- **Mechanism:** Balanced feedback + GF phase control for sharp threshold
- **Behavior:** All-or-nothing 500× amplification above 10 nM threshold
- **Modified:** Jan 8, 11:30

### 3. erk_cascade_oscillation_timed.shy - Oscillations (Figure 3)
- **Parameters:** α=0.2, β=20.0, α/β=0.01
- **Mechanism:** Strong negative feedback with timed transition delay (5s)
- **Behavior:** Sustained 20.2 cycles/min, 54 cycles over 180s
- **Modified:** Jan 11, 16:38 (most recent - timed transitions added)

### 4. erk_cascade_adaptation.shy - Adaptation (Figure 4)
- **Parameters:** α=0.15, β=200.0, α/β=0.001
- **Mechanism:** Dual-pathway feedback (ERK-PP→MKP slow + GF→MKP fast)
- **Behavior:** 96.4% adaptation, 98.8% thermodynamic efficiency
- **Modified:** Jan 9, 21:56

## Archive Models (14 files)

Development, tuning, and testing models organized by purpose:

### archive/excitability/ (8 files)
Dose-response experiments and basal activity tuning:
- `erk_cascade_excitability.shy` - Initial version (pre-phase control)
- `erk_cascade_excitability_basal.shy` - Basal activity testing
- `erk_cascade_excitability_basal_tuned.shy` - Optimized basal (0 nM dose)
- `erk_cascade_excitability_subthreshold_50nM.shy` - Subthreshold response (5 nM)
- `erk_cascade_excitability_dose_20nM_tuned.csv` - Dose-response 20 nM
- `erk_cascade_excitability_dose_40nM_tuned.csv` - Dose-response 40 nM
- `erk_cascade_excitability_dose_60nM_tuned.csv` - Dose-response 60 nM
- `erk_cascade_excitability_dose_80nM_tuned.csv` - Dose-response 80 nM

### archive/oscillations/ (1 file)
Pre-timed transition version (failed to sustain oscillations):
- `erk_cascade_oscillation.shy` - Old version without timed delays

### archive/base/ (5 files)
Base cascade, test circuits, and development models:
- `erk_cascade.shy` - Base three-tier cascade (no feedback)
- `erk_cascade_normal.shy` - Standard version with basic feedback
- `ptp_timed.shy` - Timed transition test (phosphatase)
- `test_pulse_circuit.shy` - Pulse stimulus testing circuit
- `test_timed_transition.shy` - Timed transition debugging

## Model Architecture

All models share the same base three-tier cascade:

```
Growth Factor (GF) → Raf → Raf-P
                      ↓
                    MEK → MEK-P
                      ↓
                    ERK → ERK-P → ERK-PP
                      ↑           ↑
                     MKP ←←←←←←←←←  (negative feedback)
                      ↓
                    PP2A          (dephosphorylation)
                      ↑
                   ERK-PP ←←←←←←  (positive feedback - degradation)
```

### Feedback Tuning

Mode selection via α/β ratio:
- **α (positive):** ERK-PP drives PP2A degradation (autocatalytic)
- **β (negative):** ERK-PP drives MKP synthesis (Hill kinetics, n=2, Kd=10 nM)

| Mode | α | β | α/β | Condition |
|------|---|---|-----|-----------|
| Bistability | 15.0 | 1.0 | 15.0 | α/β > 2 |
| Excitability | 1.0 | 15.0 | 0.067 | α ≈ β |
| Oscillations | 0.2 | 20.0 | 0.01 | α/β < 0.2, timed delay |
| Adaptation | 0.15 | 200.0 | 0.001 | α/β ≈ 0, dual-pathway |

## Signal Hierarchy Features

All models use SHYPN-specific features:
- **Signal places:** GF acts non-locally on Raf activation rate
- **Thermodynamic validation:** Compound mappings to KEGG validate ΔG consistency
- **Hybrid simulation:** Tau-leaping (Skellam) for stochastic reactions
- **Phase control (excitability):** GF signal modulates MKP inhibition timing

## Usage

1. Open model in SHYPN platform
2. Run simulation with specified duration:
   - Bistability: 300s (steady-state comparison)
   - Excitability: 120s (dose-response)
   - Oscillations: 180s (54 cycles)
   - Adaptation: 180s (10s pulse at t=50s)
3. Export CSV for figure generation (see ../scripts/)

## Validation

All manuscript models validated against:
- Manuscript Table 1 parameters (corrected Jan 2026)
- Published MAPK dynamics literature
- Thermodynamic feasibility (ΔG validation)
