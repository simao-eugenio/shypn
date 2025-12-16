# Mock Data vs Real Simulation: Lambda Phage Bistability

## Executive Summary

The "strange" appearance of real simulation plots compared to paper/mock data results from:
1. **Protein consumption by state indicators** (drops to 0 after decision)
2. **Very low protein levels** (max 3 vs expected 25 dimers)
3. **High undecided rate** (54% never reach stable state)
4. **Parameter mismatch** between mock (hand-tuned for visualization) and real (biochemical estimates)

---

## Mock Data Approach (experiments/run_bistability.py)

### Generation Method
```python
# Pre-determined outcome
outcome = np.random.choice(['lysogenic', 'lytic'], p=[0.52, 0.48])

# Smooth sigmoid transitions
if outcome == 'lysogenic':
    CI  = 2 * sigmoid(time - decision_time) ** 2 * 25  # Peaks at 25
    Cro = 1 * sigmoid(-(time - decision_time)) ** 2 * 5  # Stays at 5
    lysogenic_state = 1.0  # After decision_time
```

### Characteristics
- **Outcome**: Pre-determined (52% lysogenic, 48% lytic)
- **Decision time**: Normal(35, 12) time units
- **Protein dynamics**: Sigmoid rise → **plateau at high levels**
- **CI_Dimer peak**: 25 (lysogenic) or 5 (lytic)
- **Cro_Dimer peak**: 5 (lysogenic) or 25 (lytic)
- **Visual**: Clean curves, proteins stay elevated → **elegant plots**

---

## Real Simulation Data (SHYpn Batch Mode)

### Generation Method
- Gillespie SSA / Tau-Leaping stochastic simulation
- Outcome **emergent** from molecular race (not pre-determined)
- Proteins compete based on transcription/translation/decay rates
- State indicator transitions (T11, T12) **consume protein tokens**

### Observed Results (batch_20251214_104400)

| Metric | Mock Data | Real Data | Status |
|--------|-----------|-----------|---------|
| Lysogenic rate | 52% | 29% | ⚠️ Too low |
| Lytic rate | 48% | 17% | ⚠️ Too low |
| Undecided rate | 0% | **54%** | ❌ Very high |
| Decision time | 35 ± 12 units | 117 ± 49 units | ⚠️ Much slower |
| Max CI_Dimer | 25 | **3.0** | ❌ Too low |
| Mean CI_Dimer | ~15 | **0.5** | ❌ Too low |
| Max Cro_Dimer | 25 | **3.0** | ❌ Too low |
| Mean Cro_Dimer | ~10 | **0.6** | ❌ Too low |
| Protein after decision | Plateau | **Drops to 0** | ⚠️ Different |

### Key Difference: Protein Consumption

**Model implementation:**
```
Establish_Lysogeny (T11):
  CI_Dimer --[normal arc]--> T11 --> Lysogenic_State
  
  Effect: CONSUMES CI_Dimer when firing
  Result: CI_Dimer drops to 0 after lysogeny established
```

This is **biologically reasonable** (irreversible differentiation) but creates **visually different plots** than papers where state indicators use test arcs.

---

## Why Real Data Looks "Strange"

### 1. Protein Collapse After Decision
- Mock: Proteins plateau at 25 (sigmoid to constant)
- Real: **Proteins drop to 0** (consumed by T11/T12)
- Result: Trajectories show brief peak then collapse → looks "broken"

### 2. Extremely Low Protein Levels
- Expected from mock/literature: CI_Dimer peaks at 15-25
- Observed in real simulation: CI_Dimer peaks at **3.0** (mean 0.5)
- **10× lower than expected!**
- Suggests:
  - Transcription rates too slow
  - Translation rates too slow
  - Decay rates too fast
  - Dimerization inefficient
  - ATP/Energy limiting

### 3. High Undecided Rate (54%)
- Most runs never fire T11 or T12
- Proteins stay too low to trigger state transitions
- Possible causes:
  - Simulation duration too short (200 units)
  - Initial conditions (all proteins = 0) → slow start
  - Rate constants not tuned for bistability
  - Stochastic extinction of both pathways
  - Threshold for T11/T12 firing not reached

### 4. Slow Decision Time
- Mock: 35 ± 12 time units
- Real: 117 ± 49 time units (3× slower!)
- Only 46/100 runs made decision within 200 time units
- Suggests system dynamics are much slower than expected

---

## Root Cause Analysis

### Parameter Mismatch Hypothesis

**Mock data parameters** (hand-tuned for nice visualizations):
```python
# Designed to produce paper-quality plots
ci_peak = 25  # High levels
decision_time_mean = 35  # Fast decision
bistability_ratio = 0.52  # Perfect 50/50 split
```

**Real simulation parameters** (biochemical estimates):
```python
# From model.shy
CI_Transcription = 0.1 * (1 + 0.5 * CI_Dimer)
CI_Translation = 0.5 * CI_mRNA
CI_Dimerization = 0.005 * CI_Protein  # Very slow!
CI_Protein_Decay = 0.05 * CI_Protein
```

**Critical observation**: Dimerization rate = **0.005** is very slow
- At CI_Protein = 10, dimerization rate = 0.05 events/time unit
- Takes ~20 time units to create one dimer from 10 monomers
- This bottleneck limits protein accumulation

### Initial Conditions Issue

Current: `CI_Gene=1, Cro_Gene=1, all proteins=0`
- System starts from **complete silence**
- Takes time to accumulate mRNA → protein → dimers
- Stochastic fluctuations can extinguish pathways early

Suggested: Add small initial seeds
- `CI_Protein = 2, Cro_Protein = 2`
- Gives competition a "head start"
- More likely to reach decision within 200 time units

---

## Comparison Table

| Aspect | Mock Data | Real Data | Explanation |
|--------|-----------|-----------|-------------|
| **Purpose** | Demonstration, visualization | Scientific validation | Mock for UI development, real for research |
| **Outcome** | Pre-determined (coin flip) | Emergent (molecular race) | Mock guarantees 50/50, real depends on dynamics |
| **Protein levels** | High (25 dimers) | Low (3 dimers max) | Parameter mismatch |
| **Decision time** | Fast (35 units) | Slow (117 units) | Rate constants differ |
| **Completion rate** | 100% | 46% | Real simulation too short or too slow |
| **Protein fate** | Plateau (sigmoid) | Drop to 0 (consumed) | Model design choice |
| **Plots** | Elegant curves | Noisy, collapsed | Mock designed for aesthetics |
| **Stochasticity** | Added noise only | True molecular noise | Real captures low-copy fluctuations |
| **Calibration** | Hand-tuned for visualization | Biochemical estimates | Mock prioritizes appearance |

---

## Recommendations

### Option 1: Model Architecture Change (Test Arcs)

**Current** (consuming):
```
CI_Dimer --[normal]--> Establish_Lysogeny --> Lysogenic_State
```

**Alternative** (non-consuming):
```
CI_Dimer --[test]---> Establish_Lysogeny --> Lysogenic_State
                ↑
            Threshold: CI_Dimer ≥ 10
```

**Effect**: Proteins stay elevated, plots look like paper/mock data

**Biological trade-off**: 
- ✅ Proteins plateau (paper-like)
- ❌ Less biologically realistic (no commitment cost)

### Option 2: Parameter Tuning

Increase production/dimerization rates:
```python
# Current
CI_Dimerization = 0.005 * CI_Protein

# Suggested
CI_Dimerization = 0.05 * CI_Protein  # 10× faster

# Current
CI_Transcription = 0.1 * (1 + 0.5 * CI_Dimer)

# Suggested
CI_Transcription = 0.5 * (1 + 0.5 * CI_Dimer)  # 5× faster
```

**Effect**: Higher protein levels, faster decisions, more decided outcomes

### Option 3: Initial Conditions

Add protein seeds:
```python
# Current
CI_Protein = 0
Cro_Protein = 0

# Suggested
CI_Protein = 2
Cro_Protein = 2
```

**Effect**: Faster startup, more competition, lower undecided rate

### Option 4: Longer Simulation

```python
# Current
duration = 200 time units

# Suggested
duration = 500 time units
```

**Effect**: Give slow dynamics time to reach decision
**Trade-off**: 2.5× longer computation

### Option 5: Plot State Indicators Instead

Instead of plotting CI_Dimer/Cro_Dimer (which collapse), plot:
- P9 (Lytic_Genes_Active): 0 or 1
- P10 (Lysogenic_State): 0 or 1

**Effect**: Shows commitment decision clearly
**Trade-off**: Loses protein dynamics information

---

## Validation Experiments

To diagnose which fix is needed:

### Test 1: Check if longer time helps
```bash
# Run batch with duration=500
# Expected: Undecided rate should drop
```

### Test 2: Check if initial seeds help
```bash
# Set CI_Protein=2, Cro_Protein=2
# Expected: Faster decisions, higher protein peaks
```

### Test 3: Check if dimerization is bottleneck
```bash
# Change CI_Dimerization rate from 0.005 to 0.05
# Expected: 10× higher dimer levels
```

### Test 4: Compare with literature
- Lambda phage CI levels: ~100-200 molecules in lysogenic state
- Model shows: ~0-3 dimers
- **Mismatch suggests fundamental parameter scaling issue**

---

## Conclusion

The real simulation data is **scientifically valid but visually different** from mock data because:

1. **Mock data is designed for visualization** (pre-determined outcomes, smooth curves, high levels)
2. **Real data reflects actual dynamics** (emergent, stochastic, parameter-dependent)
3. **Parameter mismatch**: Real rates produce 10× lower protein levels than mock/literature
4. **Model design**: Protein consumption after decision creates collapsed trajectories

**Recommended immediate action**:
1. Increase dimerization rate from 0.005 to 0.05 (10×)
2. Add initial protein seeds (CI_Protein=2, Cro_Protein=2)
3. Increase simulation duration to 500 time units
4. Rerun batch and check if undecided rate drops below 20%

This should bring real simulation closer to expected behavior while maintaining biological accuracy.
