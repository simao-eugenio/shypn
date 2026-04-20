# Baseline Marking Review — CBD-AD Neuroprotection Model v2

**Date:** 2026-04-20  
**Context:** Post end-to-end sweep analysis (run_20260420_132707)  
**Status:** IMPLEMENTED — markings updated in model file  

---

## 1. Problem Statement

The 6-condition CBD dose sweep (0, 15, 35, 55, 100 µM × 30 replicates) revealed
a **binary switch** rather than a graded dose-response:

- CBD=0: Full pathology (NFkB=80, M1=100%, Neuron_Health=76)
- CBD≥15: Full protection (NFkB≈0, M2>94%, Neuron_Health≥98)

**Root cause:** The v2 model starts from a **healthy brain** with zero amyloid,
zero inflammation, and zero cytokines. Any CBD dose ≥15 µM blocks pathology
before it ever establishes — the system never reaches the regime where
dose-dependent differences can manifest.

---

## 2. Evidence from Time-Series Analysis

### 2.1 Untreated (CBD=0) Kinetics

| Biomarker | Time to 50% final | Time to 90% final | Observation |
|-----------|-------------------|--------------------|-------------|
| Microglia_M1 | ~4 min | ~18 min | Ultra-fast commitment |
| NFkB_p65 | 53 min | 1.72 h | Moderate |
| Abeta_Oligomer | 1.51 h | ~4 h | Slow accumulation |
| Neuron_Health | ~4 h | ~6 h | Gradual drain |

### 2.2 CBD=15 (Lowest Dose) Kinetics

- NFkB_p65: Spikes to 1.05 at t=128s, then collapses → CBD blocks before cascade establishes
- Final Abeta_Oligomer: 0.26 (vs 34.3 untreated) — essentially zero pathology

### 2.3 Paradoxical Dynamics

- **ROS decreases** from 10 → 0.68 even without CBD (Nrf2 overcompensation)
- **Glutathione increases** from 50 → 175 without CBD (unbounded antioxidant production)
- These are biologically implausible for AD — flagged as a separate calibration issue

---

## 3. Diagnosis

The initial markings represent a **prevention scenario** (healthy brain + CBD):
- Amyloid: P5=0, P6=0, P7=0 (no burden)
- Inflammation: P9=0, P11-P14=0 (no active inflammation)
- Microglia: M1=5, M2=45 (90% anti-inflammatory)
- Neurons: P23=100 (fully intact)

For a meaningful dose-response, the model must represent **established mid-stage AD**
where CBD must modulate/reverse ongoing pathology.

---

## 4. Solution: Mid-Stage AD Initial Markings

Values derived from the CBD=0 untreated time-series at ~35-55% progression toward
end-stage, with adjustments for biological plausibility.

### 4.1 Changed Markings

| PID | Place | Old (v2) | New | % toward end-stage | Rationale |
|-----|-------|----------|-----|-------------------|-----------|
| P1 | CBD_extracellular | 100.0 | **0.0** | — | Sweep parameter; default=untreated |
| P3 | Gamma_Secretase | 30.0 | **50.0** | 56% | GPR3-driven elevation |
| P4 | APP | 100.0 | **90.0** | 55% | Slightly consumed |
| P5 | Abeta_Monomer | 0.0 | **0.3** | 97% | Rapid-turnover steady state |
| P6 | Abeta_Oligomer | 0.0 | **15.0** | 44% | Significant toxic burden |
| P7 | Abeta_Plaque | 0.0 | **5.0** | 15% | Established (irreversible) plaques |
| P8 | NFkB_IkB | 80.0 | **50.0** | 38% | Partially depleted |
| P9 | NFkB_p65 | 0.0 | **30.0** | 38% | Active inflammation (TRANSITION ZONE) |
| P10 | IKK | 10.0 | **15.0** | 42% | Elevated kinase |
| P11 | TNFa | 0.0 | **1.0** | 56% | Pro-inflammatory cytokine present |
| P12 | IL1b | 0.0 | **1.0** | 45% | Pro-inflammatory cytokine present |
| P13 | IL6 | 0.0 | **1.0** | 45% | Pro-inflammatory cytokine present |
| P14 | COX2 | 0.0 | **1.0** | 45% | Inflammatory mediator present |
| P15 | Keap1_Nrf2 | 60.0 | **55.0** | 96% | Near final |
| P16 | Nrf2_free | 0.0 | **5.0** | 96% | Partial antioxidant activation |
| P17 | HO1 | 0.0 | **30.0** | 66% | Partially induced enzyme |
| P18 | SOD | 5.0 | **20.0** | 60% | Partially induced |
| P19 | ROS | 10.0 | **5.0** | 54% | Elevated (above final, model has ROS paradox) |
| P20 | Glutathione | 50.0 | **40.0** | −8% | AD-depleted antioxidant |
| P21 | Microglia_M1 | 5.0 | **25.0** | 44% | 50% polarized |
| P22 | Microglia_M2 | 45.0 | **25.0** | 44% | 50% remaining |
| P23 | Neuron_Health | 100.0 | **95.0** | 21% | Early neuronal loss |
| P24 | BDNF | 10.0 | **5.0** | 50% | Reduced neurotrophic support |
| P33 | GSSG | 0.0 | **10.0** | 67% | Elevated oxidized glutathione |
| P34 | APP_mRNA | 10.0 | **8.0** | 49% | Partially downregulated |

### 4.2 Conservation Laws (P-invariants preserved)

| Conserved quantity | Sum | Status |
|---|---|---|
| NFkB: IkB + p65 | 50 + 30 = **80** ✓ | Preserved |
| Microglia: M1 + M2 | 25 + 25 = **50** ✓ | Preserved |
| Keap1_Nrf2 + Nrf2_free | 55 + 5 = **60** ✓ | Preserved |
| Glutathione + GSSG | 40 + 10 = **50** ✓ | Preserved |

---

## 5. Expected Impact on Sweep Results

With mid-stage AD markings:
1. **CBD must reverse established inflammation** — higher doses needed for NFkB resolution
2. **Existing amyloid burden persists** — CBD can reduce production but not clear existing oligomers/plaques
3. **Microglial re-polarization** — M1→M2 reversal requires active PPARγ signaling (dose-dependent)
4. **Neuronal rescue window narrows** — some damage already done
5. **The 45–65 µM phase transition** should now be detectable as intermediate doses partially suppress but cannot fully reverse the cascade

---

## 6. Open Issues

### 6.1 ROS/Glutathione Paradox
The Nrf2 antioxidant axis overcompensates even without CBD — ROS drops to 0.68 and
GSH rises to 175. In real AD, oxidative stress overwhelms the antioxidant system.
This suggests the ROS production rate from Aβ/inflammation is too weak relative
to Nrf2-driven scavenging. **Requires rate constant calibration.**

### 6.2 Microglial Commitment Speed
Microglia commit to M1 in <5 minutes (5→50), which is unrealistically fast.
The M1/M2 switching transitions may need slower rate constants to create a
meaningful window for CBD intervention.

### 6.3 BDNF Collapse
BDNF drops from 10 to 0 within seconds. The degradation or consumption rate
is likely too high — in reality, BDNF has a half-life of hours in tissue.
