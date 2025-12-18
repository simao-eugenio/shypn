# Example 19: Bacterial Quorum Sensing (*V. fischeri*)

## Overview

This example demonstrates **quorum sensing** (QS) in *Vibrio fischeri*, the bioluminescent bacterium that forms a symbiotic relationship with the Hawaiian bobtail squid. The model shows how bacteria coordinate bioluminescence production using the **LuxI/LuxR** autoinducer system.

## Biological System

**Organism**: *Vibrio fischeri*  
**Signal Molecule**: 3-oxo-C6-HSL (N-3-oxohexanoyl-L-homoserine lactone)  
**Key Components**:
- **LuxI**: Autoinducer synthase enzyme
- **LuxR**: Transcriptional activator (receptor)
- **AHL**: Autoinducer signal molecule (3-oxo-C6-HSL)
- **LuxAB**: Luciferase enzyme complex

## Mathematical Formalism

This model uses the **13-tuple Bio-PN** formalism with signal places:

### 13-Tuple Definition
```
BioPN = ⟨P, T, Pre, Post, m₀, k, S, Φ, Σ, Reg, Ψ, E, A⟩
```

Where:
- **Ψ**: Signal places - places referenced in rate formulas but not connected by arcs
- **Ψ(t_luxAB)** = {AHL_external} - external autoinducer signal

### Signal Place Identification

For the bioluminescence transition:
```
Rate(t_luxAB) = k_lux * LuxR_AHL / (1 + AHL_external/K_inhibit)
```

Signal places are detected automatically:
```
Ψ(t_luxAB) = ReferencedPlaces(Φ(t_luxAB)) \ (•t_luxAB ∪ t_luxAB• ∪ Σ(t_luxAB))
            = {AHL_external} \ ({LuxR_AHL}, {LuxAB}, ∅)
            = {AHL_external}
```

## Model Structure

### Places (13 total)
1. **Gene_luxI** - luxI gene (copy number)
2. **mRNA_luxI** - luxI mRNA
3. **LuxI** - LuxI synthase enzyme
4. **Gene_luxR** - luxR gene
5. **mRNA_luxR** - luxR mRNA
6. **LuxR** - LuxR receptor (inactive)
7. **AHL_internal** - Intracellular autoinducer
8. **AHL_external** - Extracellular autoinducer (**signal place**)
9. **LuxR_AHL** - Active LuxR-AHL complex
10. **Gene_luxAB** - luxAB operon
11. **mRNA_luxAB** - luxAB mRNA
12. **LuxAB** - Luciferase enzyme
13. **Light** - Bioluminescence output

### Transitions (10 total)

#### LuxI Module (Autoinducer Synthesis)
- **t_txn_luxI**: Transcription of luxI
- **t_trl_luxI**: Translation of LuxI
- **t_synth_AHL**: AHL synthesis by LuxI
- **t_export_AHL**: AHL export (diffusion)

#### LuxR Module (Signal Reception)
- **t_txn_luxR**: Transcription of luxR
- **t_trl_luxR**: Translation of LuxR
- **t_binding**: LuxR-AHL complex formation

#### LuxAB Module (Bioluminescence)
- **t_txn_luxAB**: Transcription of luxAB (QS-activated)
- **t_trl_luxAB**: Translation of luciferase
- **t_light**: Light emission

### Signal Place Annotation

**t_txn_luxAB** is environment-aware:
- Rate formula: `k_lux * LuxR_AHL / (1 + AHL_external/K_inhibit)`
- Signal places: `{AHL_external}`
- Classification: **External signal** (population-level coordination)

## Quorum Sensing Behavior

### Low Cell Density (< 10⁷ cells/mL)
- AHL_external concentration low
- No activation of luxAB operon
- No bioluminescence

### High Cell Density (> 10⁹ cells/mL)
- AHL_external accumulates
- LuxR-AHL activates luxAB transcription
- Synchronized bioluminescence across population

### Critical Parameters
```python
K_luxR = 1e-9      # LuxR-AHL binding affinity (M)
K_inhibit = 1e-8   # External AHL inhibition constant (M)
k_lux = 50.0       # Maximum luxAB transcription rate (molecules/min)
k_export = 0.1     # AHL diffusion rate (1/min)
```

## Running the Simulation

### Basic Execution
```bash
python vfischeri_quorum_sensing.py
```

### Command-Line Options
```bash
# Vary initial cell density
python vfischeri_quorum_sensing.py --cells 1e6    # Below quorum
python vfischeri_quorum_sensing.py --cells 1e10   # Above quorum

# Longer simulation
python vfischeri_quorum_sensing.py --time 1000

# Save trajectory
python vfischeri_quorum_sensing.py --output trajectory.csv
```

## Expected Outputs

### 1. **Console Output**
```
=== V. fischeri Quorum Sensing Model ===
Initial cell density: 1.00e+08 cells/mL

Signal Place Detection:
  t_txn_luxAB: Ψ = {AHL_external}
  Classification: External Signal

Simulation Progress: 100% [========================================]
Time: 0-600 min | Events: 45230

Quorum Sensing Metrics:
  AHL threshold time: 342 min
  Bioluminescence onset: 358 min
  Max light output: 8.2e5 photons/s
```

### 2. **Trajectory Plot**
- **Panel A**: AHL dynamics (internal vs external)
- **Panel B**: LuxR-AHL complex formation
- **Panel C**: Bioluminescence (Light output)
- **Panel D**: Phase portrait (AHL vs Light)

### 3. **Signal Network Graph**
Visual representation showing:
- Regular places (ellipses)
- Signal places (hexagons)
- Transitions (rectangles)
- Arcs (solid lines)
- Signal dependencies (dashed red lines)

## Validation

### Experimental Comparison
Model predictions match experimental data from:
- **Nealson et al. (1970)** - J. Bacteriol. 104:313-322
- **Eberhard et al. (1981)** - Arch. Microbiol. 130:59-68

Key metrics:
- Quorum threshold: ~10⁸ cells/mL ✓
- AHL EC₅₀: ~10 nM ✓
- Response time: ~1 hour ✓

## Extensions

### 1. **Population Heterogeneity**
Add cell-to-cell variability:
```python
# Distribute LuxI expression levels
luxI_expression ~ LogNormal(μ=10, σ=0.5)
```

### 2. **Squid Host Environment**
Model symbiotic light organ:
```python
# Add host factors
places += ['Host_Mucus', 'O2_Gradient']
# Oxygen-dependent bioluminescence
rate_t_light *= O2_Gradient / (K_O2 + O2_Gradient)
```

### 3. **Multi-Species QS**
Incorporate crosstalk with other species:
```python
# Add AI-2 (universal QS signal)
places += ['AI2_external']
# Dual QS control
rate_t_luxAB *= (LuxR_AHL + LuxS_AI2) / K_combined
```

## References

1. **Waters & Bassler (2005)** - "Quorum Sensing: Cell-to-Cell Communication in Bacteria" *Annu. Rev. Cell Dev. Biol.* 21:319-346
2. **Lupp & Ruby (2005)** - "*Vibrio fischeri* Uses Two Quorum-Sensing Systems" *J. Bacteriol.* 187:6676-6684
3. **Pérez & Hagen (2010)** - "Heterogeneous Response to a Quorum-Sensing Signal" *mBio* 1:e00109-10

## File List
- `README.md` - This documentation
- `vfischeri_quorum_sensing.py` - Main simulation script
- `parameters.json` - Model parameters
- `validate_quorum_threshold.py` - Validation script
- `expected_output/` - Reference trajectories and plots
