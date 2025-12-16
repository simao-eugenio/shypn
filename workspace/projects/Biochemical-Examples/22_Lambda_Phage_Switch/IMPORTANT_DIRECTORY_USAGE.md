# ⚠️ IMPORTANT: Directory Usage for Lambda Phage Experiments

## Summary

**This directory (`22_Lambda_Phage_Switch/`) contains PAPER RESULTS - do NOT modify!**

**Run all your experiments in**: `workspace/projects/My_Project/simulations/`

---

## Why This Matters

The `22_Lambda_Phage_Switch/` directory contains:
- Original model used for paper figures
- Published results in `results/` folder
- Reference figures (`figure2_bistability_validation.png`, etc.)
- Mock data generation scripts for validation

**These must remain unchanged** to ensure reproducibility and comparison with literature.

---

## Setup Your Working Directory

### One-Time Setup

```bash
# From project root
cd /home/simao/projetos/shypn

# Copy model to your working directory
cp workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/model.shy \
   workspace/projects/My_Project/simulations/

# Create results directory
mkdir -p workspace/projects/My_Project/simulations/results
```

---

## Running Experiments

### 1. Load Working Copy in SHYpn

```bash
# Launch SHYpn
python src/shypn.py

# In GUI: File → Open
workspace/projects/My_Project/simulations/model.shy  # ← Your working copy
```

### 2. Configure Batch Mode Output

In Simulation Settings:
- **Output directory**: `workspace/projects/My_Project/simulations/results/`
- This keeps your results separate from paper results

### 3. Run Batch Simulations

All batch output goes to:
```
workspace/projects/My_Project/simulations/results/
├── batch_20251214_101234/
├── batch_20251214_102456/
└── ...
```

---

## Analysis Scripts

### Quick Visualization

```bash
# From project root - works with any batch directory
python examples/plot_batch_results.py \
       "workspace/projects/My_Project/simulations/results/batch_YYYYMMDD_HHMMSS"
```

### Custom Publication Figures

```bash
# From project root - analysis script from paper directory
python workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/analyze_batch_bistability.py \
       "workspace/projects/My_Project/simulations/results/batch_YYYYMMDD_HHMMSS"
```

**Figure saved to**: `workspace/projects/My_Project/simulations/results/figure2_bistability_validation.png`

---

## Directory Structure

```
workspace/projects/
│
├── Biochemical-Examples/22_Lambda_Phage_Switch/  ← PAPER (READ-ONLY)
│   ├── model.shy                                  Original model
│   ├── analyze_batch_bistability.py               Analysis scripts
│   ├── INTERACTIVE_REPRODUCTION_GUIDE.md          Full guide
│   ├── README_PLOTTING.md                         Quick start
│   │
│   ├── experiments/                               Mock data generators
│   │   ├── run_bistability.py
│   │   └── ...
│   │
│   └── results/                                   Published results
│       ├── figure2_bistability_validation.png
│       └── ...
│
└── My_Project/simulations/                        ← YOUR WORKING DIRECTORY
    ├── model.shy                                   Copy for experiments
    │
    └── results/                                    Your batch results
        ├── batch_20251214_101234/
        │   ├── run_001.csv
        │   ├── run_002.csv
        │   └── ...
        ├── figure2_bistability_validation.png      Your figures
        └── ...
```

---

## Benefits of This Approach

✅ **Preserves paper results** - Original data untouched  
✅ **Easy comparison** - Compare your results with published figures  
✅ **Clean organization** - Clear separation between reference and experiments  
✅ **Version control friendly** - Changes only in your working directory  
✅ **Reproducibility** - Original model always available  

---

## Quick Reference

| Task | Directory |
|------|-----------|
| Load model in SHYpn | `My_Project/simulations/model.shy` |
| Batch output location | `My_Project/simulations/results/` |
| Your experiment results | `My_Project/simulations/results/batch_*/` |
| Reference paper figures | `22_Lambda_Phage_Switch/results/` |
| Analysis scripts | `22_Lambda_Phage_Switch/analyze_*.py` |
| Original model (reference) | `22_Lambda_Phage_Switch/model.shy` |

---

## Questions?

See the full guides:
- [INTERACTIVE_REPRODUCTION_GUIDE.md](INTERACTIVE_REPRODUCTION_GUIDE.md) - Complete workflow for all experiments
- [README_PLOTTING.md](README_PLOTTING.md) - Quick start for plotting
