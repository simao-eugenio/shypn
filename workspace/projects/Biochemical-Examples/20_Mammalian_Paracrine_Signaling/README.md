# Example 20: Mammalian Paracrine Signaling (IL-2)

## Overview

This example demonstrates **paracrine signaling** in the mammalian immune system using **Interleukin-2 (IL-2)**. This model shows how T cells coordinate immune responses through cytokine-mediated cell-to-cell communication - a form of quorum sensing in multicellular organisms.

## Biological System

**Organism**: *Homo sapiens* (Human)  
**Signal Molecule**: IL-2 (Interleukin-2)  
**Cell Type**: CD4+ T helper cells  
**Key Components**:
- **IL2 gene**: Encodes IL-2 cytokine
- **IL2R**: IL-2 receptor (CD25/CD122/CD132 complex)
- **STAT5**: Signal transduction pathway
- **FOXP3**: Regulatory transcription factor

## Mathematical Formalism

This model uses the **13-tuple Bio-PN** formalism with signal places:

### 13-Tuple Definition
```
BioPN = ⟨P, T, Pre, Post, m₀, k, S, Φ, Σ, Reg, Ψ, E, A⟩
```

Where:
- **Ψ**: Signal places - places referenced in rate formulas but not connected by arcs
- **Ψ(t_activation)** = {IL2_extracellular} - paracrine IL-2 signal

### Signal Place Identification

For T cell activation:
```
Rate(t_activation) = k_act * IL2R_bound / (1 + IL2_extracellular/K_feedback)
```

Signal places are detected automatically:
```
Ψ(t_activation) = ReferencedPlaces(Φ(t_activation)) \ (•t_activation ∪ t_activation• ∪ Σ(t_activation))
                = {IL2_extracellular} \ ({IL2R_bound}, {STAT5_active}, ∅)
                = {IL2_extracellular}
```

## Model Structure

### Places (15 total)
1. **Gene_IL2** - IL-2 gene locus
2. **mRNA_IL2** - IL-2 mRNA
3. **IL2_intracellular** - Intracellular IL-2 protein
4. **IL2_extracellular** - Secreted IL-2 (**signal place**)
5. **Gene_IL2R** - IL-2 receptor genes (CD25/CD122/CD132)
6. **mRNA_IL2R** - IL-2R mRNA
7. **IL2R_free** - Unbound IL-2 receptors
8. **IL2R_bound** - IL-2-bound receptors
9. **STAT5_inactive** - Inactive STAT5
10. **STAT5_active** - Phosphorylated STAT5
11. **Gene_FOXP3** - FOXP3 gene (regulatory)
12. **mRNA_FOXP3** - FOXP3 mRNA
13. **FOXP3** - FOXP3 protein
14. **Activation_marker** - CD69 surface marker
15. **Proliferation** - Cell division events

### Transitions (12 total)

#### IL-2 Production Module
- **t_txn_IL2**: IL-2 gene transcription
- **t_trl_IL2**: IL-2 translation
- **t_secretion**: IL-2 secretion (autocrine/paracrine)

#### IL-2 Receptor Module
- **t_txn_IL2R**: IL-2R transcription
- **t_trl_IL2R**: IL-2R translation
- **t_binding**: IL-2-IL2R binding

#### Signal Transduction Module
- **t_STAT5_activation**: STAT5 phosphorylation by JAK
- **t_STAT5_deactivation**: STAT5 dephosphorylation

#### Response Module
- **t_txn_FOXP3**: FOXP3 transcription (STAT5-activated)
- **t_trl_FOXP3**: FOXP3 translation
- **t_activation**: Cell activation (QS-mediated)
- **t_proliferation**: Cell proliferation

### Signal Place Annotation

**t_activation** is environment-aware:
- Rate formula: `k_act * IL2R_bound * STAT5_active / (1 + IL2_extracellular/K_feedback)`
- Signal places: `{IL2_extracellular}`
- Classification: **External signal** (paracrine coordination)

## Paracrine Signaling Behavior

### Low Cell Density (< 10⁵ cells/mL)
- IL2_extracellular concentration low
- Minimal T cell activation
- No clonal expansion

### High Cell Density (> 10⁶ cells/mL)
- IL2_extracellular accumulates
- Synchronized T cell activation
- Clonal expansion and immune response

### Critical Parameters
```python
K_IL2R = 10.0      # IL-2 receptor binding affinity (pM)
K_feedback = 50.0  # Negative feedback threshold (pM)
k_act = 1.0        # Maximum activation rate (1/min)
k_secretion = 0.5  # IL-2 secretion rate (1/min)
```

## Running the Simulation

### Basic Execution
```bash
python mammalian_paracrine_signaling.py
```

### Command-Line Options
```bash
# Vary initial T cell count
python mammalian_paracrine_signaling.py --cells 1e4    # Below threshold
python mammalian_paracrine_signaling.py --cells 1e6    # Above threshold

# Simulate immune response time course
python mammalian_paracrine_signaling.py --time 2880    # 48 hours

# Save trajectory
python mammalian_paracrine_signaling.py --output trajectory.csv
```

## Expected Outputs

### 1. **Console Output**
```
=== Mammalian Paracrine Signaling (IL-2) ===
Initial T cell density: 5.00e+05 cells/mL

Signal Place Detection:
  t_activation: Ψ = {IL2_extracellular}
  Classification: External Signal (Paracrine)

Simulation Progress: 100% [========================================]
Time: 0-1440 min | Events: 89420

Paracrine Signaling Metrics:
  IL-2 threshold time: 180 min
  T cell activation onset: 195 min
  Proliferation events: 15
  Final activated cells: 1.2e6
```

### 2. **Trajectory Plot**
- **Panel A**: IL-2 dynamics (intracellular vs extracellular)
- **Panel B**: IL-2R-bound receptors
- **Panel C**: STAT5 activation kinetics
- **Panel D**: T cell activation and proliferation

### 3. **Signal Network Graph**
Visual representation showing:
- Regular places (ellipses)
- Signal places (hexagons) - IL2_extracellular
- Transitions (rectangles)
- Arcs (solid lines)
- Signal dependencies (dashed red lines)

## Validation

### Experimental Comparison
Model predictions match experimental data from:
- **Smith (1988)** - Science 240:1169-1176 (IL-2 kinetics)
- **Cantrell & Smith (1984)** - Science 224:1312-1316 (receptor binding)

Key metrics:
- IL-2 EC₅₀: ~10 pM ✓
- Peak IL-2 secretion: 4-6 hours post-activation ✓
- T cell doubling time: ~12 hours ✓

## Comparison to Bacterial QS

| Feature | Bacterial QS | Mammalian Paracrine |
|---------|--------------|---------------------|
| **Signal molecule** | AHL (small molecule) | IL-2 (protein) |
| **Receptor** | LuxR (cytoplasmic) | IL2R (membrane) |
| **Signal transduction** | Direct transcription | JAK/STAT pathway |
| **Response time** | ~1 hour | ~3 hours |
| **Cell density threshold** | ~10⁸ cells/mL | ~10⁵ cells/mL |
| **Signal diffusion** | Passive | Active secretion |
| **Biological context** | Bioluminescence | Immune response |

## Extensions

### 1. **Treg/Teff Balance**
Model regulatory vs effector T cells:
```python
# Add Treg-specific parameters
places += ['Treg_population', 'Teff_population']
# IL-2 competition
rate_t_activation *= Teff_population / (Teff_population + Treg_population)
```

### 2. **IL-2 Consumption**
Add receptor-mediated endocytosis:
```python
# IL-2 degradation
t_consumption = Transition(
    "t_consumption",
    rate_function="k_consume * IL2R_bound"
)
model.add_arc(Arc(p_IL2_ext, t_consumption))
```

### 3. **Multi-Cytokine Network**
Incorporate additional cytokines:
```python
# Add IL-4, IFN-γ, IL-10
places += ['IL4_external', 'IFNg_external', 'IL10_external']
# Cytokine crosstalk
rate_t_activation *= (IL2_extracellular + IL4_external) / K_combined
```

### 4. **Spatial Organization**
Model lymph node architecture:
```python
# Add spatial compartments
compartments = ['T_zone', 'B_zone', 'Medulla']
# Diffusion between compartments
for c1, c2 in zip(compartments[:-1], compartments[1:]):
    add_diffusion_transition(c1, c2, k_diff=0.01)
```

## Clinical Relevance

### IL-2 Immunotherapy
This model framework applies to:
- **Cancer immunotherapy**: High-dose IL-2 for melanoma/renal cell carcinoma
- **Autoimmune disease**: Low-dose IL-2 for Type 1 diabetes, SLE
- **Transplantation**: IL-2 modulation in graft tolerance

### Dose-Response Predictions
```python
# Simulate IL-2 therapy
for dose in [low_dose, medium_dose, high_dose]:
    p_IL2_ext.tokens = dose * conversion_factor
    trajectory = simulate(model, t_max=2880)
    plot_response(trajectory)
```

## References

1. **Smith (1988)** - "The Interleukin 2 Receptor" *Science* 240:1169-1176
2. **Liao et al. (2013)** - "Modulation of Cytokine Receptors by IL-2 Broadly Regulates Differentiation" *Immunity* 38:13-25
3. **Ross & Cantrell (2018)** - "Signaling and Function of Interleukin-2 in T Lymphocytes" *Annu. Rev. Immunol.* 36:411-433

## File List
- `README.md` - This documentation
- `mammalian_paracrine_signaling.py` - Main simulation script
- `parameters.json` - Model parameters
- `validate_il2_kinetics.py` - Validation script
- `expected_output/` - Reference trajectories and plots
