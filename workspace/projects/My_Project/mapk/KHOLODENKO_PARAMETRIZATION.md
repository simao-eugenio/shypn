# Kholodenko LOW State Parametrization

## Objective
Test if the original **adaptation model architecture** (with phase pulse control) can reproduce Kholodenko's LOW state (~4% ERK-PP activation) through **parametrization only**, without topological changes.

## Model Architecture (Unchanged)
- **Base:** erk_cascade_adaptation.shy
- **15 places:** Growth_Factor, Raf, MEK, ERK, ERK_Nuclear, PP2A, MKP, ATP, ADP, + pulse control places
- **22 transitions:** Activation, phosphorylation, dephosphorylation, nuclear import/export, feedback regulation, **timed pulse control**
- **48 arcs:** Same topology as adaptation model
- **Key feature:** Phase pulse (Start_Pulse, End_Pulse) for temporal control

## Parameter Changes

### 1. Positive Feedback (α parameter) - PP2A Degradation
**Original (Adaptation - Perfect Adaptation):**
```
rate = 0.01 * PP2A * (1 + 0.15 * (ERK_PP^4 / (120^4 + ERK_PP^4)))
α = 0.15 (minimal positive feedback)
```

**Kholodenko Parametrization (LOW state):**
```
rate = 0.01 * PP2A
α = 0.0 (ZERO positive feedback)
```

**Rationale:** Complete elimination of autocatalytic loop. PP2A degradation is now ERK-independent, preventing any positive feedback.

---

### 2. Negative Feedback (β parameter) - MKP Synthesis
**Original (Adaptation - Perfect Adaptation):**
```
rate = 0.01 * (1 + 200.0 * (ERK_PP^2 / (10^2 + ERK_PP^2)))
β = 200.0 (very strong negative feedback for adaptation)
```

**Kholodenko Parametrization (LOW state):**
```
rate = 0.05 + 5.0 * (ERK_PP^4 / (20^4 + ERK_PP^4))
β = 5.0 (moderate negative feedback)
```

**Rationale:** Reduce extreme negative feedback from adaptation regime. Moderate MKP induction ensures signal attenuation without perfect adaptation.

---

### 3. PP2A Basal Synthesis
**Original (Adaptation):**
```
rate = 0.08
```

**Kholodenko Parametrization:**
```
rate = 0.3
```

**Rationale:** Increase baseline phosphatase to ensure dephosphorylation dominates, favoring LOW state.

---

### 4. Pulse Timing (Timed Transitions)
**Original (Adaptation):**
```
Start_Pulse: earliest_time = 10.0s, latest_time = 10.0s
End_Pulse: earliest_time = 10.0s, latest_time = 10.0s
Duration: Very short pulse (~0-20s adaptive response)
```

**Kholodenko Parametrization:**
```
Start_Pulse: earliest_time = 10.0s, latest_time = 10.0s (unchanged)
End_Pulse: earliest_time = 180.0s, latest_time = 180.0s
Duration: 170s sustained signal (match Kholodenko simulation)
```

**Rationale:** Kholodenko used sustained stimulation. Extend pulse duration from adaptation's brief transient to prolonged 3-minute signal for steady-state comparison.

---

### 5. Feedforward Pathway (GF→MKP)
**Original (Adaptation):**
```
rate = 29.0 * (Growth_Factor^2 / (0.1^2 + Growth_Factor^2))
```

**Kholodenko Parametrization:**
```
rate = 0.0 (DISABLED)
```

**Rationale:** Kholodenko had no direct feedforward from growth factor to phosphatase. Disable this adaptation-specific pathway to match classical cascade topology.

---

## Feedback Ratio Analysis

### Original Adaptation Model
```
α/β = 0.15 / 200.0 = 0.00075
```
- **Regime:** Perfect adaptation (α/β ≪ 0.01)
- **Predicted state:** Transient response returns to baseline
- **Mechanism:** Incoherent feedforward loop (GF → ERK + GF → MKP) causes adaptation

### Kholodenko Parametrization
```
α/β = 0.0 / 5.0 = 0.0
```
- **Regime:** Pure negative feedback (α = 0)
- **Predicted state:** LOW (~4-10% ERK-PP activation)
- **Mechanism:** Negative feedback dominates, sustained low-level response

---

## Expected Behavior

### Adaptation Model (erk_cascade_adaptation.shy)
- **Pattern:** Brief ERK-PP spike → return to baseline despite sustained GF
- **Peak ERK-PP:** ~300-400 nM (transient)
- **Final ERK-PP:** ~10-20 nM (adapted back to baseline)
- **PP2A level:** Stable (~8-10 nM)
- **MKP level:** High (~100-200 nM) - feedforward + feedback induction
- **Regime:** Perfect adaptation via incoherent feedforward loop

### Kholodenko Parametrization (erk_cascade_kholodenko_parametrized.shy)
- **Pattern:** Gradual rise → sustained plateau
- **Final ERK-PP:** ~25-40 nM (4-7% activation)
- **PP2A level:** High (~25-40 nM) - protected from degradation
- **MKP level:** Moderate (~30-50 nM) - feedback only, no feedforward
- **Regime:** LOW attractor (phosphatases dominate)

### BIOMD0000000010 (Imported Kholodenko)
- **Final ERK-PP:** ~12.7 nM (4.2% activation)
- **Product feedback:** ERK-PP inhibits MAPKKK activation
- **Mechanism:** Negative feedback at cascade input

---

## Validation Strategy

### Step 1: Simulate Kholodenko Parametrization
```bash
# Load erk_cascade_kholodenko_parametrized.shy in SHYPN
# Simulate for 180s (match Kholodenko duration)
# Export to CSV
```

### Step 2: Compare Three Models
| Metric | Adaptation | Kholodenko Param | BIOMD0000000010 |
|--------|------------|------------------|-----------------|
| Final ERK-PP (nM) | 10-20 | ? | 12.7 |
| ERK-PP (%) | ~3% | ? | 4.2% |
| PP2A (nM) | 8-10 | ? | N/A |
| MKP (nM) | 100-200 | ? | N/A |
| α/β ratio | 0.00075 | 0.0 | N/A |
| Computational mode | Adaptation | Neg. Feedback | Ultrasensitivity |
| Pulse duration | 10s | 170s | Sustained |
| Feedforward | Yes (GF→MKP) | No | No |

### Step 3: Quantify Parametric Flexibility
- **Hypothesis:** Same topology + different parameters = different computational modes
- **Test:** Does Kholodenko param produce ~4-12 nM ERK-PP (LOW state)?
- **If YES:** Model architecture is parametrically flexible (validate design)
- **If NO:** Topology matters more than parameters (need structural changes)

---

## Key Insight

This experiment tests a fundamental question:

> **Can a single network topology produce multiple computational behaviors (bistability, adaptation, oscillation) through parametrization alone?**

**Your manuscript claims YES** (4 computational modes from one cascade). This validation will:
1. Confirm that LOW state is accessible from HIGH state topology
2. Show that feedback balance (α/β) determines computational mode
3. Validate that your model generalizes beyond bistability

**If successful:** Your model architecture is more general than Kholodenko's, reproducing his LOW state as a special case of your feedback-tunable cascade.

---

## Biological Interpretation

### Kholodenko 2000 Mechanism
- **Ultrasensitivity:** Distributive dual phosphorylation creates switch-like response
- **Feedback:** Negative (product inhibits MAPKKK)
- **Result:** Signal attenuation, LOW state

### Your Model Mechanism (Kholodenko Params)
- **Ultrasensitivity:** Same dual phosphorylation cascade
- **Feedback:** Dominant negative (ERK-PP → MKP synthesis)
- **Result:** Signal attenuation, LOW state

**Convergent mechanism:** Different feedback implementations (upstream inhibition vs downstream phosphatase induction) produce same LOW state phenotype.

---

## Next Steps

1. ✅ Created `erk_cascade_kholodenko_parametrized.shy`
2. ⏳ Simulate in SHYPN (180s duration)
3. ⏳ Export CSV and analyze final ERK-PP%
4. ⏳ Compare to BIOMD0000000010 and kolodenko_mapk_bistability.csv
5. ⏳ Update comparison script for 3-way analysis
6. ⏳ Document in manuscript: "Parametric Flexibility" section

---

## Files Created

- **Model:** `workspace/projects/My_Project/mapk/models/manuscript/erk_cascade_kholodenko_parametrized.shy`
- **Documentation:** `workspace/projects/My_Project/mapk/KHOLODENKO_PARAMETRIZATION.md` (this file)
- **Comparison script:** `workspace/projects/My_Project/simulations/compare_kholodenko_models.py`
