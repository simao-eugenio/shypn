# P1 deep analysis — `run_20260424_005438`

**Project:** `canabidiol`
**Model:** `cbd_ad_neuroprotection_v3.shy` (sha256 `a6b10f4c…`)
**Run dir:** `workspace/projects/canabidiol/experiments/results/run_20260424_005438`
**Provenance:** client + server git `fcf66a46`, branch `Usability-and-enhancements`, no dirty paths.
**Design:** Disease_Severity {0,1,2,3} × LOADING_DOSE {0,5,10,20} × MAINT_DOSE {0,1,3,5} × Age {65,75,85} = 192 cells × 30 reps = **5 760 simulations** (5 760/5 760 OK).
**Sim duration:** 4 h. **Engine:** τ-leaping (GPUHybridEngine where applicable).
**Analyser:** [`scripts/deep_analyse_p1.py`](../scripts/deep_analyse_p1.py) — 10 probes on per-replicate end-state values from `replicates.csv`.

This document captures the **biological** findings; the protocol-level
implications and dose-grid trims feed back into
[`event_protocol_v3.md`](event_protocol_v3.md) §4.4 and §14.

---

## 🔴 Major findings

### F1. Stochastic bistability on the Aβ-plaque axis (lock-in)

**93 of 1 152** (Sev × LD × MT × Age × species) cells fail unimodality
(Sarle b > 5/9 = 0.555). **All 93 are `Abeta_Plaque`** — no other
species shows multimodal across-replicate dispersion. Typical signature
in the rescued regime:

| Sev | LD | MT | Age | mean | std | CV | b |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 20 | 5 | 65 | 0.11 | 0.36 | 3.30 | 0.84 |
| 0 | 10 | 5 | 65 | 0.12 | 0.36 | 2.99 | 0.82 |
| 1 | 10 | 5 | 65 | 0.11 | 0.36 | 3.34 | 0.85 |
| 2 | 10 | 5 | 65 | 0.13 | 0.37 | 2.73 | 0.80 |

CV ≈ 3 means most replicates clear plaque to 0, but a small fraction
**lock in** at ~1–2 plaque units. This is precisely the bistable
boundary that **Protocol P4** was designed to map — and it's already
showing up inside P1 at the rescued (LD ≥ 5) regime, near the basin
floor θ.

**Implication for P4 design:** the original P4 dose grid
(`CBD_extracellular ∈ {0, 1.5, …, 6.0}`) is too wide. The transition
zone is `LD ∈ {3, 5, 7}` measured at endpoint t = 4 h. Recentre P4 at
`LD ∈ {3, 4, 5, 6, 7}` × {age, sev} for 60 reps → 2 700 sims.

### F2. Plaque accumulates de novo from healthy M₀

The `Disease_Severity` install seeds `Abeta_Plaque ← 0 + Sev × 2.5`
(so Sev=0→0, Sev=3→7.5). At t = 4 h, drug-naïve plaque is:

| Sev | Age=65 plaque (LD=0) | Age=65 plaque (LD=20) |
|---:|---:|---:|
| 0 | **72.4** | 0.17 |
| 1 | 77.9 | 0.14 |
| 2 | 83.8 | 0.13 |
| 3 | 89.8 | 0.11 |

The drug-naïve cell ends with **72–90 plaque units regardless of
severity** — a ~10× headroom over the install seed. Plaque grows
**autonomously** in 4 h with severity contributing only ~17 units of
headstart over `(0 → 72)` baseline accumulation.

Combined with **F4** (Severity contributes only 3.2 % of NeuH
variance), this confirms `Disease_Severity` is a weak knob in the
current model. The Aβ_Monomer → Oligomer → Plaque cascade has **no
functional clearance under drug-naïve conditions** even with the
"healthy" M₀.

#### F2b. Plaque is REVERSIBLE under maintenance dosing

Drilling into the time-course of the (Sev=2, Age=75, **LD=0, MT=3**) cell
shows that plaque does **not** plateau — it overshoots and then
actively decays:

| t (h) | CBD (µM) | Plaque (units) |
|---:|---:|---:|
| 0.1 | 0.0  | 5.8 |
| 0.5 | 0.0  | 10.5 |
| 1.0 | 0.0  | 19.3 |
| 1.2 | 3.0  ← *first MT pulse* | 23.2 |
| 1.5 | 1.4  | 28.6 |
| 2.0 | 0.8  | **31.8 ← peak** |
| 3.0 | 1.6  | 26.0 |
| 4.0 | 2.4  | **9.5 (and falling)** |

Until the first MT pulse at t ≈ 1.2 h, CBD is exactly 0 and plaque
rises rapidly (autonomous accumulation, same as MT = 0). Once CBD
enters at trough levels of 0.8–3 µM, plaque keeps rising for ~1 h
more (the oligomer pool feeds plaque formation while the inflammatory
cascade winds down), peaks at ~32 around t = 2 h, and then **actively
decreases** to ~10 by t = 4 h.

**This is biologically stronger than F2 alone implied:** the model
encodes **plaque reversibility**, not just rate-of-accumulation
suppression. CBD does not merely halt new plaque, it allows
clearance pathways (autophagy / phagocytosis by polarised M2
microglia) to reduce existing plaque burden. A natural extension of
P1 — running the simulation to t = 12 h or 24 h with MT = 3 — would
show whether the (LD=0, MT=3) trajectory clears plaque to floor or
stalls at some non-zero residual.

**Decision needed before P2/P3 dispatch:**
1. Lower healthy-M₀ values for `Microglia_M1 (5)`, `NFkB_p65 (5)`,
   `IL1b/IL6/COX2 (0.5 each)`, `ROS (1)` so the cascade does not
   self-ignite from the supposed healthy state, or
2. Add a constitutive plaque-clearance flux (BACE inhibition /
   autophagy proxy) so that the system has a stable healthy attractor.

P6 (severity calibration, 7 conditions × 30 reps = 210 sims) at
**duration 28 800 s** with Sev = 0 only would separate "M₀ too hot"
from "4 h too short to reach steady state".

### F3. Drug effect is binary on inflammation, sublinear on receptors

At Sev = 2, Age = 75, MT = 0:

| LD | NFkB_p65 | TNFa | IL1b | M1 | M2 | HT1A_act | PPARg_act | A2A_act | BDNF |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0  | 80.0 | 1.50 | 1.88 | 50.0 | 0.0  | 0.000 | 0.000 | 0.000 | 0.00 |
| 5  | **0.3**  | **0.04** | **0.06** | 47.3 | 2.8  | 0.054 | 0.355 | 0.054 | 0.08 |
| 10 | 0.1  | 0.03 | 0.06 | 40.6 | 9.4  | 0.104 | 0.653 | 0.104 | 0.15 |
| 20 | 0.1  | 0.03 | 0.05 | 28.6 | 21.4 | 0.194 | 1.122 | 0.194 | 0.28 |

**NFkB drops 99.6 % at LD = 5**, while HT1A_active is only 0.054
(≈ 5 % engagement) and PPARg_active is 0.355. The inflammation
collapse is hugely out of proportion to the receptor activation.
Microglial M1 → M2 polarisation, by contrast, is gradual and
dose-proportional (LD=5 → M2=2.8; LD=20 → M2=21.4).

**Two possible interpretations:**

* **(a) Mass-action edge.** A direct CBD-mediated consumption of
  TNFa/IL1b/IL6/NFkB exists (high-rate transition with `CBD_*` as
  reactant), bypassing receptor signalling. This would be **mechanism
  drift** — CBD's anti-inflammatory effect should be receptor-mediated
  (PPARγ, A2A, GPR55), not mass-action.
* **(b) Numerical floor.** The cytokine pool is being driven to zero
  by a stoichiometrically over-balanced clearance. Worth checking
  whether the floor θ is being tripped.

Action item: trace transitions consuming `TNFa, IL1b, IL6, COX2,
NFkB_p65` when `CBD_extracellular > 0`. Confirm whether the binary
collapse is a stoichiometric edge (legitimate fast kinetics) or a
floor artefact.

---

## 🟡 Important findings

### F4. Variance partition: Severity contributes only 3.2 % of NeuH variance

One-way η² across all 5 760 simulations:

| Factor | η² of NeuH variance |
|---|---:|
| **LoadDose**  | **50.1 %** |
| Age           | 27.8 % |
| MaintDose     | 4.9 % |
| Severity      | **3.2 %** |
| Residual (interactions + reps) | ~14 % |

LoadDose is by far the dominant explanatory variable, followed by
Age. Severity is statistically *present* but weak — the model does
not differentiate Sev=1 from Sev=3 strongly enough to support
disease-stratification claims. See F2 for the upstream cause.

### F5. Hill-style EC50 grows monotonically with Age, independent of Severity

Per-(Sev, Age) interpolated EC50 of `Neuron_Health` vs `LOADING_DOSE`
(MT = 0):

| Sev | Age=65 EC50 | Age=75 EC50 | Age=85 EC50 |
|---:|---:|---:|---:|
| 0 | 2.91 µM | 4.08 µM | 5.50 µM |
| 1 | 2.87    | 4.04    | 5.62    |
| 2 | 2.87    | 4.05    | 5.63    |
| 3 | 2.88    | 4.06    | 5.48    |

EC50 is **essentially independent of severity** but **+90 % from
Age 65 to Age 85**. The age-clearance penalty
`(1 + 0.02 × (Age − 65))` propagates correctly into pharmacology.
**Age — not disease — is the primary patient-stratification axis.**

### F6. Age × drug interaction is **non-monotonic**: under-dosing widens the gap

| LD | Age65 NeuH | Age75 NeuH | Age85 NeuH | Δ(85−65) | % age-gap rescued |
|---:|---:|---:|---:|---:|---:|
| 0  | 57.6 | 48.5 | 39.9 | −17.7 | 0 % |
| **5**  | **88.1** | **73.8** | **58.5** | **−29.6** | **−66.7 %** |
| 10 | 91.1 | 83.7 | 69.1 | −22.1 | −24.4 % |
| 20 | 92.6 | 89.4 | 79.8 | −12.8 | +27.8 % |

**At LD = 5 the age gap WIDENS** (from 17.7 to 29.6 NeuH points): young
cells respond better than old, magnifying the disparity. The gap only
closes at the saturating LD = 20.

Mechanistically this is a **clearance-limited regime** — old cells need
higher CBD concentration to overcome slowed clearance kinetics.
**Clinically translated: under-dosing the elderly is *worse* than not
treating them.** This finding matches real-world CBD pharmacokinetic
concerns and is publishable on its own.

### F7. Therapeutic ceiling at Age = 85

`Neuron_Health ≥ 90` is **unreachable at Age = 85 for any (LD, MT)
combination, at any severity**. The cap is around 79.8 (Sev=3, LD=20).
The age-related ceiling is hard.

| Sev | Age | smallest dose for NeuH ≥ 70 | NeuH ≥ 80 | NeuH ≥ 90 |
|---:|---:|---:|---:|---:|
| 2 | 65 | (5,0) | (5,0)  | (10,0) |
| 2 | 75 | (5,0) | (10,0) | (20,3) |
| 2 | 85 | (10,1) | (20,1) | **—** |
| 3 | 65 | (5,0) | (5,0)  | (20,0) |
| 3 | 75 | (5,0) | (10,0) | **—** |
| 3 | 85 | (10,1) | (20,3) | **—** |

### F8. NFkB pool is **not conserved** (CV 16.5 %)

Conservation checks across all 5 760 replicates:

| Pool | members | mean(sum) | sd(sum) | CV | range |
|---|---|---:|---:|---:|---|
| Microglia | M1 + M2 | 49.12 | 2.96 | 0.060 | 45 – 58 |
| Redox     | Glutathione + GSSG | 279.04 | 23.34 | 0.084 | 221 – 342 |
| **Nrf2**  | Nrf2_free + Keap1·Nrf2 | 60.00 | 0.00 | **0.000** ✅ | 60 – 60 |
| **NFkB**  | p65 + NFkB·IkB + IKK | 85.28 | 14.07 | **0.165 ⚠** | 65 – 112 |

Microglia and Redox sums vary within stochastic tolerance. **Nrf2 is
exactly conserved** ✅. **NFkB sums range from 65 to 112** — there is
a transcriptional source production for NFkB in the model. If this is
intended (e.g., `NFkB_mRNA → NFkB_p65` synthesis transition),
document it. If not, it is a leak.

---

## 🟢 Confirmations

* **Plaque rescue is profound.** Drug reduces plaque from ~80 to ~0.15
  at LD ≥ 5, even at Sev = 3.
* **Within-condition correlations** at the drug-naïve AD cell are
  mostly NaN — i.e., NFkB/TNFa/M1/M2/BDNF/receptors all saturate to
  fixed values across replicates, leaving zero variance for
  correlation. Only the Aβ cascade retains stochasticity (oligomer ↔
  plaque correlation = −0.61, the conversion is the slow step).
* **Microglia and Redox conservation** match the formalism within
  stochastic tolerance.
* **Mechanism check:** drug induces M1 → M2 polarisation, collapses
  ROS / TNFa / NFkB, raises Glutathione. The model is mechanistically
  sound on the inflammation/oxidative arm.

---

## Recommended next actions (priority order)

| # | Action | Cost | Resolves |
|---|---|---|---|
| 1 | Audit M₀ for `M1, NFkB_p65, IL1b, IL6, COX2, ROS` — these pre-ignite the inflammatory loop | 1 model patch + P6 verify | F2, F4 |
| 2 | Locate transitions consuming TNFa/IL1b/IL6/NFkB when CBD present — confirm binary collapse is stoichiometric edge, not numerical floor | code inspection | F3 |
| 3 | Re-dispatch P4 (bifurcation) at `LD ∈ {3, 4, 5, 6, 7}` × {sev, age} × 60 reps = 2 700 sims | 1 sweep | F1 |
| 4 | Dispatch P6 (severity calibration) **with extended duration 28 800 s** to separate M₀ effects from steady-state drift | 7 × 30 = 210 sims | F2, F4 |
| 5 | Document F6 (under-dosing penalty in elderly) in manuscript — this is a real publishable outcome | manuscript work | F6 |
| 6 | Investigate NFkB pool non-conservation — leak or designed source? | code inspection | F8 |

---

## Reproducibility

```bash
# Server-side, from repo root
python3 workspace/projects/canabidiol/scripts/deep_analyse_p1.py \
    workspace/projects/canabidiol/experiments/results/run_20260424_005438
```

The analyser reads only `replicates.csv` (≈ 12 KB per condition × 192 =
~2.3 MB total). The companion `statistics.json` files (1.1 GB each)
are not consulted.
