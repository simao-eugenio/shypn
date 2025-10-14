# Control Model Validation - Quick Start Guide

**Goal**: Validate Shypn simulation accuracy using established control models  
**Time**: 1 hour to run first validation  
**Model**: Repressilator (simplest, clearest)

---

## 5-Minute Overview

✅ **YES**, validated control pathway models exist!  
✅ **BioModels Database** has 1000+ peer-reviewed models  
✅ **SBML format** imports directly to Shypn  
✅ **Start with**: Repressilator (gene oscillator, 100-min period)  

---

## Quick Start (4 Steps)

### Step 1: Download Model (2 min)
```bash
# Visit: https://www.ebi.ac.uk/biomodels/BIOMD0000000012
# Click: "Download" → "SBML L2V4"
# Save as: repressilator.xml
```

### Step 2: Import to Shypn (1 min)
```
1. Open Shypn
2. File → Import → SBML
3. Select repressilator.xml
4. ✓ Beautiful tree layout appears!
```

### Step 3: Configure Simulation (1 min)
```
Simulation Settings:
- Duration: 200 minutes
- Time Units: Minutes
- Time Step: Auto
- Time Scale: 1.0 (or higher to watch faster)
```

### Step 4: Run & Validate (5 min)
```
1. Click "Start Simulation"
2. Watch proteins oscillate
3. Check: ~100 minute period? ✓
4. Export data for analysis
```

**Success = You see clear oscillations!** 🎉

---

## Expected Result

```
Protein concentrations oscillate like this:

 LacI  ^     /\        /\        /\
       |    /  \      /  \      /  \
     5 |   /    \    /    \    /    \
       |__/______\__/______\__/______\__> Time
       0        100       200       300 min

 TetR oscillates 120° out of phase
 cI oscillates another 120° out of phase
```

**Period**: ~100 minutes (±10% is good!)  
**Shape**: Smooth sinusoidal waves  
**Behavior**: Stable indefinitely  

---

## Validation Checklist

- [ ] Downloaded BIOMD0000000012
- [ ] Imported to Shypn successfully
- [ ] Simulation runs without errors
- [ ] See oscillations in protein levels
- [ ] Period approximately 100 minutes
- [ ] No numerical instabilities
- [ ] Data exported for analysis

**All checked? You've validated Shypn!** ✅

---

## Full Documentation

- **Overview**: `doc/control/README.md`
- **Detailed Plan**: `doc/control/VALIDATION_PLAN.md`
- **Summary**: `doc/control/SUMMARY.md`
- **This Guide**: `doc/control/QUICK_START.md`

---

## Next Models

After Repressilator, try:
1. **Glycolysis** (BIOMD0000000064) - Real metabolism
2. **Calcium** (BIOMD0000000035) - Fast dynamics

---

**Get started in 5 minutes!** 🚀
