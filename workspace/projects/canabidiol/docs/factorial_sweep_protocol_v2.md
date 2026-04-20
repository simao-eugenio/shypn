# Factorial Sweep Protocol — CBD-AD Neuroprotection Model v2

**Date:** 2026-04-20 (revised from 2026-04-19)  
**Model:** `cbd_ad_neuroprotection_v2.shy` (34 places, 45 transitions, ~100 arcs)  
**Engine:** Hybrid tau-leaping (7 stochastic + 37 continuous + 1 adaptive transitions)  
**Version:** shypn 2.6.1 (commit f4e6b495)  
**Server:** Antares (32 cores, RTX 5060 Ti) — simao@150.162.232.36  
**Baseline:** Mid-stage AD (revised 2026-04-20, see §11)  
**Key finding:** Anti-inflammatory (EC50 < 1 µM) and neuroprotective (caps ~94%) responses dissociate — factorial probes their interaction under Age/pH/T modulation.  

---

## 1. Design: 4-Factor Factorial

| Factor | Levels | Values | Rationale |
|--------|--------|--------|-----------|
| **CBD dose** (P1) | 8 | 0, 1, 2, 4, 6, 8, 12, 15 | Anti-inflammatory saturates at ~1 µM; antioxidant axis (GSH/HO1/SOD EC50 ≈ 4–8 µM) is dose-graded. Focus on the range where neuroprotection outcome diverges from inflammation resolution. Confirmed by run_20260420_143905. |
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
- Each replicate ≈ 8.9 s (from run_20260420_143905: `mean_elapsed_time≈8.9`)
- With 6 workers (memory-safe cap): ~5,760 × 8.9 / 6 ≈ **8,544 s ≈ 2.4 h**
- Validated: test sweeps (run_20260420_132707: 6×30; run_20260420_143905: 10×30)

---

## 4. Factor Levels Detail

### 4.1 CBD Dose (P1: CBD_extracellular initial marking)

*Revised 2026-04-20 based on run_20260420_143905 (10-level fine sweep, mid-stage AD markings).*

**Key observation:** Two CBD mechanisms have different dose-response profiles:
- **Anti-inflammatory** (NFkB, Oligomer clearance, M1→M2): EC50 < 1 µM — essentially binary (on/off)
- **Antioxidant** (GSH, ROS, HO1, SOD): EC50 ≈ 4–8 µM — graded, dose-proportional

The **interaction** between these two is the scientific focus: inflammation resolution alone
(CBD ≥ 1 µM) only achieves ~94% neuron retention — the remaining gap depends on
antioxidant dose-response AND environmental modifiers (Age, pH, Temperature).

| Level | P1 Value | Mechanism Status |
|-------|----------|------------------|
| 0 | 0.0 | Both off: untreated mid-stage AD |
| 1 | 1.0 | Anti-inflammatory ON (EC50), antioxidant minimal |
| 2 | 2.0 | Anti-inflammatory saturated, antioxidant sub-EC50 |
| 4 | 4.0 | Antioxidant ~50% EC50: GSH beginning to respond |
| 6 | 6.0 | Antioxidant approaching EC50: ROS reduction begins |
| 8 | 8.0 | Antioxidant at EC50: HO1/SOD half-maximal |
| 12 | 12.0 | Antioxidant above EC50: near-saturation |
| 15 | 15.0 | Both saturated: maximum achievable protection |

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
- `CBD8_Age75_pH6.6_T39` — Antioxidant EC50, elderly, acidotic, febrile (stress test)
- `CBD15_Age55_pH7.4_T37` — Max dose, young, physiological (best case)

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

### 7.1 Dissociation Between Anti-Inflammatory and Neuroprotective Effects
- At what CBD dose does anti-inflammatory benefit (NFkB → 0) fully translate to neuronal rescue (Neuron > 95%)?
- What closes the 6% gap between inflammation resolution (~94% neuron) and full protection?
- Is the antioxidant axis (GSH/HO1/SOD, EC50 ≈ 4–8 µM) the bridge between inflammation control and neuroprotection?

### 7.2 Age × CBD Interaction (Modulates the Gap)
- Does age widen the dissociation? (Predicted: elderly = inflammation resolved but neurons still die)
- At Age=85, does the antioxidant EC50 shift rightward (needing higher CBD for same GSH)?
- Is there an age threshold where even CBD=15 cannot close the gap?

### 7.3 pH × CBD Interaction (Modulates Both Arms)
- Does AD acidosis (pH 6.6) impair antioxidant efficacy (T13 pH-dependent)?
- Does acidosis accelerate Aβ re-aggregation even when inflammation is suppressed?
- At pH 6.6 + CBD=1 (inflammation only): is neuron loss accelerated vs pH 7.4?

### 7.4 Temperature Effects (Q10 Preferentially Accelerates Damage)
- Does fever (39°C) preferentially accelerate neurotoxicity (T20) vs CBD protective pathways?
- Does Q10 widen the anti-inflammatory/neuroprotective dissociation?
- Combined: Age=85 + T=39°C + CBD=8 — does antioxidant EC50 shift make protection impossible?

### 7.5 Interaction Design: When Does Protection Fail?
- **Translational failure zone**: conditions where NFkB=0 but Neuron < 90% (resolved inflammation ≠ rescue)
- **Synergistic harm**: Age=85 + pH=6.6 + T=39°C — is untreated progression faster than in default conditions?
- **Minimum effective combination**: for each Age/pH/T, what is the minimum CBD that achieves Neuron > 95%?
- **Ceiling effect**: is there ANY condition where CBD=15 is insufficient? (factorial's key question)

---

## 8. Analysis Plan (Post-Sweep)

1. **Dissociation quantification** — For each condition: Δ = (NFkB suppression %) − (Neuron recovery %). Map Δ across factor space.
2. **Interaction surfaces** — Neuron_Health surface: CBD × Age (faceted by pH, T). Identify where the gap opens.
3. **ANOVA / factorial analysis** — Main effects AND 2-way/3-way interactions for:
   - Neuron_Health (primary outcome)
   - Δ_dissociation = (1 − NFkB/80) − (Neuron/95) as interaction metric
4. **Antioxidant bridge analysis** — Correlation between GSH/HO1/SOD level and Neuron_Health, controlling for NFkB. Does antioxidant dose close the gap?
5. **Minimum effective dose (MED) table** — For each Age/pH/T combination:
   - MED for NFkB < 1 (anti-inflammatory)
   - MED for Neuron > 95% (full protection)
   - Gap between the two MEDs = "antioxidant requirement"
6. **Failure conditions** — Enumerate all Age/pH/T combinations where CBD=15 is insufficient for Neuron > 95%
7. **Sensitivity ranking** — Partial η² for each factor and interaction on Neuron_Health

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
- [ ] Create all 192 snapshots (8 CBD × 4 Age × 3 pH × 2 Temp)
- [ ] Launch sweep on remote server
- [ ] Monitor progress and collect results
- [ ] Run interaction-focused analysis (§8)

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

### 11.3 Revised CBD Factor Levels (Final — based on run_20260420_143905)

The 10-level fine sweep (0,1,2,4,6,8,10,12,14,15 µM) revealed:
- Anti-inflammatory EC50 < 1 µM (NFkB: 80→0.15 at CBD=1)
- Antioxidant EC50 ≈ 4–8 µM (GSH: 109→121 linearly across range)
- Neuroprotection caps at ~94% (never reaches 95% even at CBD=15)

The factorial uses 8 levels focused on the **antioxidant dose-response** range,
where interactions with Age/pH/T are expected to modulate the outcome:

| Level | P1 Value | Mechanism Status |
|-------|----------|------------------|
| 0 | 0.0 | Both off: untreated mid-stage AD |
| 1 | 1.0 | Anti-inflammatory ON, antioxidant minimal |
| 2 | 2.0 | Anti-inflammatory saturated, antioxidant sub-EC50 |
| 4 | 4.0 | Antioxidant ~50% EC50 |
| 6 | 6.0 | Antioxidant approaching EC50 |
| 8 | 8.0 | Antioxidant at EC50 |
| 12 | 12.0 | Antioxidant above EC50 |
| 15 | 15.0 | Both saturated |

**Final total conditions:** 8 × 4 × 3 × 2 = **192 snapshots**

### 11.4 Open Calibration Issues (post-sweep)

1. **ROS paradox** — ROS decreases in untreated AD (Nrf2 overcompensation). Needs rate tuning.
2. **Microglial commitment** — M1 polarization completes in <5 min (too fast).
3. **BDNF collapse** — Half-life unrealistically short (seconds vs hours).
