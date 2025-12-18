# Old Development Files - Archive

This directory contains historical development materials that are **NOT needed for paper submission**.

## Contents

### Development Documentation (Archive Only)
- `BATCH_MODE_BUG_FIX.md` - Bug fix history (Dec 14-17, 2025)
- `EXPERIMENTAL_PLAN.md` - Early experimental design notes
- `FINAL_SESSION_REPORT.md` - Development session summary
- `IMPORTANT_DIRECTORY_USAGE.md` - Directory structure notes
- `INTERACTIVE_REPRODUCTION_GUIDE.md` - Early reproduction guide
- `MOCK_VS_REAL_DATA_COMPARISON.md` - Testing validation
- `PROGRESS_SUMMARY.md` - Development progress tracking
- `README_PLOTTING.md` - Old plotting documentation
- `README_development_history.md` - Original README describing technical development

### Old Models (Superseded)
- `model.shy` - Pre-symmetry model with 56:36 bias
- `model.shy.backup` - Backup of original model

### Old Scripts (Superseded)
- `analyze_batch_bistability.py` - Replaced by `generate_paper_figures.py`

### Old Data (Superseded)
- `experiments/` - Early experimental runs
- `results/` - Early batch results (before final validation)

## Status

**SAFE TO DELETE**: All files in this directory

The parent directory contains only publication-ready materials:
- ✓ `model_symmetric_bistable*.shy` - Validated models
- ✓ `batch_results/` - Final validated data (100 replicates × 3 conditions)
- ✓ `generate_paper_figures.py` - Current figure generation script
- ✓ `PAPER_SUBMISSION_README.md` - Complete submission guide
- ✓ `FINAL_MODEL_DOCUMENTATION.md` - Technical specifications
- ✓ `README.md` - Clean project overview

## Deletion Instructions

If you want to permanently remove these archived files:

```bash
cd /home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch
rm -rf old_development_files/
```

**Note**: This action is irreversible. However, all critical information has been:
1. Incorporated into current documentation
2. Superseded by validated models and data
3. Preserved in git history (if committed)

## Historical Value

These files document the development process including:
- Bug discovery and fixes (asymmetric rates, batch mode GUI)
- Model evolution (semaphores → pure biological)
- Validation iterations

Keep them if you want to show the research process, but they are not needed for publication.

---

**Recommendation**: Delete after paper acceptance, or keep as supplementary development history.
