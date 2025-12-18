# Directory Organization Summary

**Status**: ✓ Organized for Paper Submission  
**Date**: December 17, 2025

---

## Current Structure

```
22_Lambda_Phage_Switch/
│
├── 📄 Models (Publication Versions)
│   ├── model_symmetric_bistable.shy       ← ZERO, no UV (bistability test)
│   ├── model_symmetric_bistable_UV.shy    ← ZERO + UV (lytic bias)
│   └── model_balanced_UV.shy              ← BALANCED + UV (CI vulnerability)
│
├── 📊 Data (Validated Batches)
│   └── batch_results/
│       ├── zero_no_uv/        → 100 replicates: 42:48 Lys:Lyt
│       ├── zero_with_uv/      → 100 replicates: 4:86 Lys:Lyt
│       └── balanced_with_uv/  → 100 replicates: 2:98 Lys:Lyt
│
├── 📖 Documentation (Essential)
│   ├── README.md                          ← START HERE
│   ├── PAPER_SUBMISSION_README.md         ← Complete submission guide
│   └── FINAL_MODEL_DOCUMENTATION.md       ← Technical specifications
│
├── 🎨 Figure Generation
│   └── generate_paper_figures.py          ← Automated figure creation
│
└── 🗄️ Archive (Can Delete)
    └── old_development_files/             ← 15 historical items
        └── README_ARCHIVE.md              ← Deletion instructions

```

---

## Quick Actions

### 1. Generate Figures for Paper
```bash
python generate_paper_figures.py
```

### 2. Read Documentation
```bash
# Quick overview
cat README.md

# Complete submission guide
cat PAPER_SUBMISSION_README.md

# Technical details
cat FINAL_MODEL_DOCUMENTATION.md
```

### 3. Clean Up (Optional)
```bash
# Remove old development files (15 items)
rm -rf old_development_files/
```

---

## File Status

### ✓ Keep (7 files + 2 directories)

**Models:**
- model_symmetric_bistable.shy (29K)
- model_symmetric_bistable_UV.shy (29K)
- model_balanced_UV.shy (29K)

**Documentation:**
- README.md (4.6K) - Project overview
- PAPER_SUBMISSION_README.md (7.9K) - Submission guide
- FINAL_MODEL_DOCUMENTATION.md (7.7K) - Technical specs

**Script:**
- generate_paper_figures.py (16K) - Figure generator

**Data:**
- batch_results/ - Links to validated simulation data

---

### 🗑️ Archive (15 files - can delete)

Located in `old_development_files/`:

**Development docs (9 files):**
- BATCH_MODE_BUG_FIX.md
- EXPERIMENTAL_PLAN.md
- FINAL_SESSION_REPORT.md
- IMPORTANT_DIRECTORY_USAGE.md
- INTERACTIVE_REPRODUCTION_GUIDE.md
- MOCK_VS_REAL_DATA_COMPARISON.md
- PROGRESS_SUMMARY.md
- README_PLOTTING.md
- README_development_history.md

**Superseded models (2 files):**
- model.shy (pre-symmetry, 56:36 bias)
- model.shy.backup

**Old scripts (1 file):**
- analyze_batch_bistability.py

**Old data (2 directories):**
- experiments/
- results/

**Total size**: ~400KB (negligible)

---

## What Changed

### Moved to Archive
- ✓ Old README → old_development_files/README_development_history.md
- ✓ All development documentation
- ✓ Superseded models and scripts
- ✓ Early experimental data

### Created New
- ✓ Clean README.md (publication-focused)
- ✓ PAPER_SUBMISSION_README.md (complete guide)
- ✓ old_development_files/README_ARCHIVE.md (deletion instructions)

### Preserved
- ✓ All validated models
- ✓ All batch result links
- ✓ Figure generation script
- ✓ Technical documentation

---

## Disk Space

```
Publication files:  ~180 KB (7 files + documentation)
Batch data:         Symlinks (no space, points to My_Project)
Archive:            ~400 KB (15 items in old_development_files/)
Total:              ~580 KB
```

After deleting archive: **~180 KB** (minimal footprint)

---

## Next Steps

1. ✓ Directory organized
2. ✓ Old files archived
3. → Generate figures: `python generate_paper_figures.py`
4. → Review documentation
5. → Write paper
6. → (Optional) Delete old_development_files/ after paper acceptance

---

**Status**: Publication directory is clean and ready ✓
