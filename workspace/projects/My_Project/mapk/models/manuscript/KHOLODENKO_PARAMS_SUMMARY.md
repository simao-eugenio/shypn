# Kholodenko Parametrization - Summary

## ✅ Completed

Created **erk_cascade_kholodenko_parametrized.shy** from adaptation model base.

### Key Parameter Changes:

1. **PP2A Degradation (Positive Feedback α):**
   - Adaptation: `0.01 * PP2A * (1 + 0.15 * (ERK_PP^4 / (120^4 + ERK_PP^4)))`
   - Kholodenko: `0.01 * PP2A` 
   - **Change:** α = 0.15 → 0.0 (eliminated positive feedback)

2. **MKP Synthesis (Negative Feedback β):**
   - Adaptation: `0.01 * (1 + 200.0 * (ERK_PP^2 / (10^2 + ERK_PP^2)))`
   - Kholodenko: `0.05 + 5.0 * (ERK_PP^4 / (20^4 + ERK_PP^4))`
   - **Change:** β = 200 → 5.0 (reduced from perfect adaptation to moderate negative feedback)

3. **PP2A Synthesis:**
   - Adaptation: `0.08`
   - Kholodenko: `0.3`
   - **Change:** 3.75x increase for high phosphatase baseline

4. **Pulse Duration:**
   - Adaptation: End_Pulse at 10s (brief transient)
   - Kholodenko: End_Pulse at 180s (sustained signal)
   - **Change:** 170s pulse duration (match Kholodenko simulation)

5. **Feedforward Pathway (GF→MKP):**
   - Adaptation: `29.0 * (Growth_Factor^2 / (0.1^2 + Growth_Factor^2))`
   - Kholodenko: `0.0`
   - **Change:** Disabled (not present in Kholodenko model)

### Feedback Ratio:
- **Adaptation:** α/β = 0.00075 (perfect adaptation regime)
- **Kholodenko:** α/β = 0.0 (pure negative feedback, no positive)

### Files:
- **Model:** `workspace/projects/My_Project/mapk/models/manuscript/erk_cascade_kholodenko_parametrized.shy`
- **Documentation:** `workspace/projects/My_Project/mapk/KHOLODENKO_PARAMETRIZATION.md`

## Next Step: Simulate & Compare

Load the model in SHYPN and run 180s simulation to see if it reproduces Kholodenko's ~4% ERK-PP LOW state!
