# Factorial Sweep Protocol — CBD-AD Neuroprotection Model v2

**Date:** 2026-04-19  
**Model:** `cbd_ad_neuroprotection_v2.shy` (34 places, 45 transitions, ~100 arcs)  
**Engine:** Hybrid tau-leaping (7 stochastic + 37 continuous + 1 adaptive transitions)  
**Version:** shypn 2.6.1 (commit f4e6b495)  
**Server:** Antares (32 cores, RTX 5060 Ti) — simao@150.162.232.36  

---

## 1. Design: 4-Factor Factorial

| Factor | Levels | Values | Rationale |
|--------|--------|--------|-----------|
| **CBD dose** (P1) | 8 | 0, 15, 25, 35, 50, 65, 85, 100 | Captures phase transition zone (45–65 µM), low-dose neuronal rescue (15–25), saturation (85–100). Finer grid in transition zone vs v1 sweep. |
| **Age** (P25) | 4 | 55, 65, 75, 85 | Age factor `(1 + 0.02*(Age-65))` ranges 0.8→1.4. Covers pre-senior through very elderly. Audit flags age-dependent efficacy shift. |
| **pH** (P29) | 3 | 7.4, 7.0, 6.6 | 7.4=physiological, 7.0=current default, 6.6=AD acidosis. Affects aggregation (T4, T5), inflammation (T17, T20), antioxidant kinetics (T13). |
| **Temperature** (P28) | 2 | 310.15 (37°C), 312.15 (39°C) | Normal vs fever/neuroinflammation. Q10 dormant at 37°C — 39°C activates it across 16 transitions. |

**Total conditions:** 8 × 4 × 3 × 2 = **192 snapshots**

---

## 2. Simulation Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Duration** | 21,600 s (6 h) | Consistent with all previous runs; captures acute pharmacodynamics |
| **Replicates** | 30 | Robust mean/CI; feasible on 32 cores |
| **tau_epsilon** | 0.03 | Same as cross-validated runs (verified consistent across 3 paths) |
| **max_tau** | 0.1 | Same as previous |
| **Termination** | deadlock | Same as previous |
| **Seed base** | 42 | Reproducibility |

---

## 3. Estimated Runtime

- 192 conditions × 30 replicates = **5,760 total simulations**
- Each replicate ≈ 8.9 s (from run_20260419_110229 baseline: `mean_elapsed_time=8.86`)
- With 32 cores at 75% cap (24 effective): ~5,760 × 8.9 / 24 ≈ **2,136 s ≈ 36 min**
- With overhead (snapshot setup, result writing): estimate **~45–60 min total**

---

## 4. Factor Levels Detail

### 4.1 CBD Dose (P1: CBD_extracellular initial marking)

| Level | P1 Value | Expected Regime |
|-------|----------|-----------------|
| 0 | 0.0 | Untreated AD baseline |
| 15 | 15.0 | Low-dose: GPR3 depletion + BDNF rescue, no inflammation control |
| 25 | 25.0 | Moderate-low: plaque normalization to healthy-aging range |
| 35 | 35.0 | Pre-transition zone |
| 50 | 50.0 | Mid-transition: partial NFkB suppression |
| 65 | 65.0 | Post-transition: full neuroprotection (97% of max benefit) |
| 85 | 85.0 | Saturation check |
| 100 | 100.0 | Maximum dose (reference) |

### 4.2 Age (P25: Age place marking)

| Level | P25 Value | Age Factor | Effect |
|-------|-----------|------------|--------|
| 55 | 55.0 | 0.80 | Pre-senior: enhanced clearance, reduced vulnerability |
| 65 | 65.0 | 1.00 | Reference (neutral) |
| 75 | 75.0 | 1.20 | Elderly: impaired clearance, increased Aβ production |
| 85 | 85.0 | 1.40 | Very elderly: severe impairment |

Affects: T3 (Aβ production ↑), T13 (antioxidant scavenging ↓), T17 (M2→M1 ↑), T18 (M1→M2 ↓), T20 (neurotoxicity ↑), T24 (oligomer clearance ↓), T25 (monomer clearance ↓), T39 (plaque clearance ↓)

### 4.3 pH (P29: pH place marking)

| Level | P29 Value | Context |
|-------|-----------|---------|
| 7.4 | 7.4 | Physiological (healthy brain extracellular) |
| 7.0 | 7.0 | Current default (mild acidosis) |
| 6.6 | 6.6 | AD-associated acidosis |

Affects: T4 (Aβ aggregation: `1 + 0.5*(7.0-pH)`), T5 (plaque formation: `1 + 0.3*(7.0-pH)`), T13 (antioxidant: `1 - 0.3*abs(pH-7.4)`), T17 (M2→M1: `1 + 0.3*(7.0-pH)`), T20 (neurotoxicity: `1 + 0.4*(7.0-pH)`)

### 4.4 Temperature (P28: Temperature place marking, in Kelvin)

| Level | P28 Value | Celsius | Q10 Factor |
|-------|-----------|---------|------------|
| 310.15 | 310.15 | 37°C | 1.00 (baseline — Q10 dormant) |
| 312.15 | 312.15 | 39°C | 1.15 (2^0.2) — fever/neuroinflammation |

Affects: 16 transitions via `2**((T_celsius-37)/10)` Q10 terms

---

## 5. Snapshot Naming Convention

Format: `CBD{dose}_Age{age}_pH{ph}_T{temp_C}`

Examples:
- `CBD0_Age65_pH7.0_T37` — Untreated AD baseline, default conditions
- `CBD50_Age75_pH6.6_T39` — Mid-dose, elderly, acidotic, febrile (worst case)
- `CBD100_Age55_pH7.4_T37` — Max dose, young, physiological (best case)

---

## 6. Key Biomarker Endpoints

### Primary (manuscript Table 1 candidates)

| # | Place | ID | What It Measures |
|---|-------|----|------------------|
| 1 | Glutathione | P20 | Antioxidant capacity (validated marker: ~510 post-fix) |
| 2 | NFkB_p65 | P9 | Inflammation switch (phase transition marker) |
| 3 | Neuron_Health | P23 | Neuroprotection endpoint |
| 4 | Abeta_Oligomer | P6 | Toxic amyloid species |
| 5 | ROS | P11 | Oxidative stress |

### Secondary

| # | Place | ID | What It Measures |
|---|-------|----|------------------|
| 6 | TNFa | P3 | Pro-inflammatory cytokine |
| 7 | IL1b | P4 | Pro-inflammatory cytokine |
| 8 | IL6 | P5 | Pro-inflammatory cytokine |
| 9 | COX2 | P14 | Inflammatory mediator |
| 10 | Microglia_M1 | P21 | Pro-inflammatory polarization |
| 11 | Microglia_M2 | P22 | Anti-inflammatory polarization |
| 12 | HO1 | P17 | Nrf2-driven antioxidant enzyme |
| 13 | SOD | P18 | Superoxide dismutase |
| 14 | PPARg_active | P26 | CBD's anti-inflammatory effector |
| 15 | GSSG | P27 | Oxidized glutathione (redox ratio) |
| 16 | Abeta_Plaque | P7 | Plaque burden |
| 17 | BDNF | P24 | Neurotrophic factor |
| 18 | Nrf2_free | P16 | Antioxidant transcription factor |

---

## 7. Scientific Questions This Design Answers

### 7.1 CBD Dose-Response (Primary)
- Is the NFkB phase transition at 45–65 µM confirmed in v2 with corrected arc weights?
- What is the precise EC50 for each endpoint?
- Are the "two therapeutic windows" (neuronal rescue ≥15 µM, inflammation resolution ≥65 µM) preserved?

### 7.2 Age × CBD Interaction
- Does age shift the therapeutic threshold upward? (Predicted: elderly need higher CBD dose)
- At Age=85, is CBD=100 still sufficient for full neuroprotection?
- Is there an age beyond which CBD cannot fully protect neurons?

### 7.3 pH × CBD Interaction
- Does AD acidosis (pH 6.6) worsen outcomes independently of CBD dose?
- Does acidosis shift the phase transition boundary?
- Is the Aβ aggregation rate (T4) sensitive to pH at physiological vs acidotic conditions?

### 7.4 Temperature Effects
- Does fever (39°C) accelerate disease progression via Q10?
- Does fever change the CBD dose needed for neuroprotection?
- Is the Q10 effect uniform or does it preferentially accelerate certain pathways?

### 7.5 Multi-Factor Interactions
- Worst case: CBD=0, Age=85, pH=6.6, T=39°C — how severe is untreated AD?
- Best case: CBD=100, Age=55, pH=7.4, T=37°C — is there a floor effect?
- Does the combination of Age=85 + pH=6.6 create a synergistic worsening that CBD cannot overcome?

---

## 8. Analysis Plan (Post-Sweep)

1. **Dose-response curves** — Each endpoint vs CBD dose, faceted by Age/pH/Temperature
2. **Phase transition mapping** — NFkB_p65 surface plot (CBD × Age), identifying transition boundary
3. **ANOVA / factorial analysis** — Main effects and interactions for primary endpoints
4. **Therapeutic window identification** — For each Age/pH/T combination, find minimum CBD for:
   - Neuron_Health > 95% (neuronal rescue)
   - NFkB_p65 < 1.0 (inflammation resolution)
   - ROS < 0.5 (oxidative stress control)
5. **Worst-case analysis** — Identify conditions where CBD=100 is insufficient
6. **Sensitivity ranking** — Which factor (Age, pH, T) has the largest effect on each endpoint?

---

## 9. Cross-Validation Reference

This protocol builds on verified simulation consistency (2026-04-19):

| Source | Glutathione | ROS | HO1 | SOD | Deviation |
|--------|-------------|-----|-----|-----|-----------|
| Snapshot (1 run) | 515.73 | 0.096 | 157.66 | 101.57 | — |
| Batch (15 rep) | 512.80 | 0.095 | 163.49 | 106.01 | 1–5% |
| Remote VP (50 rep) | 510.01 | 0.095 | 164.47 | 107.37 | 1–5% |

All paths consistent. A34=0.1 (Nrf2→Glutathione) correctly preserved in all code paths.

---

## 10. Prerequisites Checklist

- [x] shypn 2.6.1 deployed on server (commit f4e6b495)
- [x] Arc weight fix verified (A34=0.1)
- [x] 3-way cross-validation passed
- [x] SSH hardening applied (MaxStartups, ClientAlive)
- [x] Server git remote switched to SSH (deploy key added)
- [x] End-to-end test sweep validated (run_20260420_132707, 6 conditions × 30 rep)
- [x] **Baseline markings revised** — mid-stage AD (see §11 below)
- [ ] Verify UI supports >3 sweep dimensions in factorial design
- [ ] Create all 192 snapshots in Viability Panel
- [ ] Launch sweep on remote server
- [ ] Monitor progress and collect results

---

## 11. Baseline Marking Revision (2026-04-20)

### 11.1 Motivation

End-to-end test sweep (run_20260420_132707) revealed the original "healthy brain"
baseline produces a **binary switch** instead of a graded dose-response:
- Any CBD ≥15 µM gives FULL PROTECTION (prevents pathology from ever starting)
- No dose differentiation possible in the 15–100 µM range

See: `baseline_marking_review_v2.md` for full analysis.

### 11.2 New Default: Mid-Stage AD Brain

Initial markings now represent ~35–55% progression toward end-stage untreated AD.
The system has established inflammation and amyloid burden that CBD must reverse/halt.

**Key changes:**
- Abeta_Oligomer: 0 → **15** (existing toxic burden)
- NFkB_p65: 0 → **30** (active inflammation, transition zone)
- NFkB_IkB: 80 → **50** (partially depleted)
- Microglia M1/M2: 5/45 → **25/25** (50% polarized)
- Neuron_Health: 100 → **95** (early loss)
- Glutathione: 50 → **40** (AD-depleted)
- CBD_extracellular: 100 → **0** (untreated default; sweep sets dose)

All P-invariants preserved (NFkB=80, Microglia=50, Keap1/Nrf2=60, GSH/GSSG=50).

### 11.3 Revised CBD Factor Levels

Given the shift from prevention→treatment, finer sampling in the low-dose
region is critical. The original 0–15 µM gap was where the binary switch lived.

| Level | P1 Value | Expected Regime |
|-------|----------|-----------------|
| 0 | 0.0 | Untreated mid-stage AD (progression continues) |
| 5 | 5.0 | Sub-threshold: minimal modulation |
| 10 | 10.0 | Low-dose: partial receptor engagement |
| 15 | 15.0 | Low-dose: GPR3 effect begins |
| 25 | 25.0 | Moderate: partial NFkB suppression |
| 35 | 35.0 | Pre-transition zone |
| 50 | 50.0 | Mid-transition: expected phase boundary |
| 65 | 65.0 | Post-transition: full suppression? |
| 85 | 85.0 | Saturation check |
| 100 | 100.0 | Maximum dose (reference) |

**New total conditions:** 10 × 4 × 3 × 2 = **240 snapshots**

### 11.4 Open Calibration Issues (post-sweep)

1. **ROS paradox** — ROS decreases in untreated AD (Nrf2 overcompensation). Needs rate tuning.
2. **Microglial commitment** — M1 polarization completes in <5 min (too fast).
3. **BDNF collapse** — Half-life unrealistically short (seconds vs hours).
