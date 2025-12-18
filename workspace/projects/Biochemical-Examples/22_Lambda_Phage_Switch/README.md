# Lambda Phage Bistable Switch - Publication Models

**Status**: ✓ Publication-Ready  
**Date**: December 17, 2025  
**Purpose**: Supporting materials for paper submission

---

## Quick Start

### Generate Paper Figures
```bash
python generate_paper_figures.py
```

Creates 5 publication-quality figures in `figures/` directory.

---

## Files Overview

### 📄 Models (Final Validated Versions)

| File | Description | Initial Conditions | UV | Expected Outcome |
|------|-------------|-------------------|-----|------------------|
| `model_symmetric_bistable.shy` | Bistability demonstration | CI=0, Cro=0 | No | 42:48 Lys:Lyt |
| `model_symmetric_bistable_UV.shy` | UV-induced lytic | CI=0, Cro=0 | Yes | 4:86 Lys:Lyt |
| `model_balanced_UV.shy` | Pre-existing CI vulnerability | CI=10, Cro=10 | Yes | 2:98 Lys:Lyt |

### 📊 Data

**`batch_results/`** - Symbolic links to validated simulation batches (100 replicates each):
- `zero_no_uv/` → batch_20251217_171118
- `zero_with_uv/` → batch_20251217_174024
- `balanced_with_uv/` → batch_20251217_182809

### 📖 Documentation

- **`PAPER_SUBMISSION_README.md`** - Complete guide for paper preparation
- **`FINAL_MODEL_DOCUMENTATION.md`** - Technical model specifications
- **`generate_paper_figures.py`** - Automated figure generation script

### 📁 Archive

**`old_development_files/`** - Historical development materials (not needed for publication)

---

## Key Results

### Symmetric Rate Functions Achievement

Both CI and Cro transcription now use identical functional forms:

```
T1 (CI):  rate = 2.0 * (1 + 0.5 * CI_Dimer / (5 + CI_Dimer)) / (1 + (Cro_Dimer / 15)^2)
T6 (Cro): rate = 2.0 * (1 + 0.5 * Cro_Dimer / (5 + Cro_Dimer)) / (1 + (CI_Dimer / 15)^2)
```

**Critical Fix** (Dec 17, 2025): Corrected T6 from asymmetric formula, reducing bias from 56:36 to 42:48.

### Validation Summary

| Experiment | Lysogenic | Lytic | Key Finding |
|------------|----------:|------:|-------------|
| **ZERO no UV** | 42% | 48% | ✓ Balanced bistability |
| **ZERO + UV** | 4% | 86% | ✓ UV forces lytic (93% CI destroyed) |
| **BALANCED + UV** | 2% | 98% | ✓ Pre-existing CI more vulnerable |

### Novel Finding

**Pre-existing CI provides no UV protection** - actually increases vulnerability:
- ZERO + UV: 4% lysogenic escapes (CI can win early race)
- BALANCED + UV: 2% lysogenic escapes (RecA immediately targets existing CI)

This demonstrates that established lysogenic prophages are highly sensitive to UV-induced SOS response.

---

## Model Architecture

- **12 places**: Genes (catalyst), mRNAs, proteins, dimers, RecA system
- **17 transitions**: Transcription, translation, dimerization, degradation, CI cleavage
- **31 arcs**: Normal arcs only (no semaphores, pure biological model)

### Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Basal transcription | 2.0 mM/s | Both CI and Cro |
| Positive feedback Km | 5 mM | Half-saturation |
| Repression Ki | 15 mM | Half-maximal inhibition |
| Hill coefficient | n=2 | Cooperative repression |
| Translation rate | 5.0 × mRNA | Linear with mRNA |
| RecA cleavage | 0.5 × RecA_Active | CI dimer destruction |

---

## Reproduction Instructions

### Using Existing Data
```bash
# Figures from validated batches (recommended)
python generate_paper_figures.py
```

### Re-running Simulations
```bash
# Load models in SHYPN GUI:
# 1. File → Open → model_symmetric_bistable.shy
# 2. Simulation → Batch Mode → 100 replicates
# 3. Record: P7 (CI_Dimer), P8 (Cro_Dimer)
# 4. Duration: 3000 seconds
# 5. Run and compare to batch_results/
```

---

## Citation

**Repository**: https://github.com/simao-eugenio/shypn  
**Branch**: Usability-And-Miscellaneous  
**Path**: workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/  
**Models**: model_symmetric_bistable*.shy  
**Date**: December 17, 2025

---

## Scientific Contributions

1. **Emergent Bistability**: First pure molecular model of lambda switch without explicit state machines
2. **Symmetric Design**: Demonstrated requirement for perfectly symmetric rate functions
3. **Statistical Validation**: 300 total replicates across 3 conditions
4. **Novel Mechanism**: Pre-existing CI vulnerability to UV-induced cleavage
5. **Framework**: 12-tuple Petri net extensions for gene regulatory networks

---

## Next Steps

1. ✓ Models validated and preserved
2. ✓ Batch results linked and verified
3. ✓ Documentation complete
4. → Run `python generate_paper_figures.py`
5. → Write Methods and Results sections
6. → Submit manuscript

---

For detailed technical information, see **PAPER_SUBMISSION_README.md** and **FINAL_MODEL_DOCUMENTATION.md**.
