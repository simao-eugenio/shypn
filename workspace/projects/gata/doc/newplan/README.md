# GATA1/PU.1 Toggle — Research Log (newplan)

> **Authoritative evolution record for the GATA model.**  
> Each model version has a dedicated reference + analysis file below.  
> New simulation campaigns must update this file before and after running.

---

## Model Lineage

```
base / v2 / v3
    │  K_inh=8.0, no pPU1, no symmetric FB4
    │  All runs → ERY by symmetry. Myeloid structurally inaccessible.
    ▼
 v4  (Mar 8 2026)
    │  K_i0=1.0, symmetric FB3+FB4, pPU1_nuc place added
    │  Myeloid accessible. New problem: both TFs mutually suppress to ~5 mol
    │  → uncommitted / oscillatory regime dominates all tested conditions
    ▼
 v5  (Mar 9–10 2026)
    │  Km_self=5. Two 6hr batches run:
    │    batch_20260310_123621: EPO=1.0, GCSF=0.1 → 2 ERY, 0 MYELOID, 3 collapse
    │    batch_20260310_151034: EPO=0.0, GCSF=1.0 → 0 ERY, 1 MYELOID, 6 collapse
    │  Both batches: dominant regime is a ~6-min LIMIT CYCLE (not bistability).
    │  Commitment is rare late-stochastic escape from limit cycle.
    │  Root problems: Km_self=5 disengages autocatalytic feedback;
    │  GATA1 basal 0.08 vs PU1 0.06 = 33% structural ERY bias.
    ▼
 v6  (Mar 10 2026)
    │  Km_self: 5 → 1 (feedback engages at 1-4 molecule range)
    │  EPO=GCSF=1.0 (symmetric cytokine challenge)
    │  Phase G-v4b (Mar 15): EPO=0.395–0.46 × pH=7/7.5/8 × N=100 × 7200s
    │    → 100% ERY all conditions: GCSF was 0.001 (model default), not 1.1
    │    → Myeloid pathway structurally disabled; EPO* unresolvable
    │    → Secondary finding: pH↑ increases GATA1 stochastic noise (CV 19→32%)
    │  Phase G-v5 (invalidated, pre-run): EPO range 0.43–0.45 entirely below EPO*≈0.52
    │    → at GCSF=1.1, EPO<EPO* → all MYE-biased by construction (same failure, opposite sign)
    │  Phase G-v6 (Mar 15 2026): EPO 0.30–1.10 × pH 7/7.5/8 × GCSF=1.1 × N=100 × 21600s
    │    → 2400 replicates; 1025 ERY / 1375 MYE; 13/24 conditions genuinely bistable
    │    → EPO* is pH-dependent: 0.615 (pH=7) / 0.610 (pH=7.5) / 0.544 (pH=8)
    │    → Mechanism: pGATA1/pPU1 ratio crosses 1.0 between pH=7.5 and pH=8.0
    │    → Model confirmed stochastic bistable; stochastic commitment window t=100–500s
    │    → NOTE: EPO*(pH) values superseded by G-v7 (G-v6 had non-reproducible anomalies)
    │  Phase G-v7 (Mar 17 2026): EPO 0.52–0.65 × pH 7/7.5/8 × GCSF=1.1 × N=100 × 21600s
    │    → Fine-grid EPO* characterisation near transition
    │    → 2400 replicates; consistent monotone dose-response at all three pH levels
    │    → EPO*(revised): > 0.65 (pH=7) / 0.634 (pH=7.5) / 0.596 (pH=8)
    │    → G-v6 anchors at EPO=0.57/pH=8.0 and EPO=0.65/pH=7.0 were non-reproducible
    │    → pH=7.0 transition not found in range — EPO* > 0.65 µM
    ▼
 v6 (active — Phase G-v7 complete)```

---

## File Index

| File | Model | Date | Contents |
|---|---|---|---|
| [MODEL_REFERENCE_v4.md](MODEL_REFERENCE_v4.md) | v4 | Mar 8 | Places, ICs, rate functions, structural changes from base |
| [RESEARCH_PLAN_V4.md](RESEARCH_PLAN_V4.md) | v4 | Mar 8 | All v4 simulation runs, observations, mechanistic diagnoses |
| [LAYER_ANALYSIS_MAR10.md](LAYER_ANALYSIS_MAR10.md) | v5→v6 | Mar 10 | Full layer + thermodynamic analysis of EPO=1/GCSF=0.1 batch; v6 change rationale |
| [MIRROR_BATCH_ANALYSIS_MAR10.md](MIRROR_BATCH_ANALYSIS_MAR10.md) | v5 | Mar 10 | EPO=0/GCSF=1 mirror batch; limit cycle confirmed; cross-batch comparison |
| [MODEL_REFERENCE_v6.md](MODEL_REFERENCE_v6.md) | v6 | Mar 10–17 | v6 model reference (ICs, transitions, all simulation campaigns through Phase G-v7) |

---

## Hard-Won Lessons (do not repeat these experiments)

| Lesson | Evidence | Model |
|---|---|---|
| `K_inh=8.0` makes myeloid fate structurally inaccessible regardless of EPO/GCSF | All base/v2/v3 runs → ERY | base |
| Symmetric ICs + stochastic TauLeap at ~5 mol/TF → shot-noise dominates ratio signal for hours | v4 run_20260308_102938; ratio flips randomly 318× in 10800 s | v4 |
| Near-attractor ICs do NOT lock fate at 5 molecules: asymmetry erases by t≈1100 s | v4 RQ1-ERY run | v4 |
| Km_self=5 disengages autocatalytic feedback: peak gain=0.008 << δ=0.075 | L5 gain analysis Mar 10 | v5 |
| GCSF=0.1 gives GCSFR_bound≈0.04–0.3 → T26 factor 2.0–2.7 → PU1 always max-degraded | 0/10 MYELOID in EPO=1/GCSF=0.1 batch | v5 |
| With EPO=0: GATA1 net flux always negative (T24_factor=2.0–2.8) → 0/10 ERY structurally | 0/10 ERY in EPO=0/GCSF=1 mirror batch | v5 |
| Energy charge (EC≈0.906) and mRNA pool (~38 tokens) are fate-independent — do not monitor as outcome proxies | 60-window thermodynamic analysis; confirmed in mirror batch | v5 |
| Dominant dynamical regime in v5 is a ~6-min LIMIT CYCLE between near-committed and collapse | 50–60 entry/exit cycles per 6h in ALL 10 mirror-batch reps | v5 |
| Commitment = rare late stochastic escape from limit cycle (h4–h5), not a decision | Rep5/9 in EPO=1 batch; rep8 in mirror batch: all commit after h4 | v5 |
| Stochastic GCSFR_bound/EPOR_bound spike to ~4.0 is the escape mechanism for both directions | Rep8 (MYELOID): GCSFR_b → 3.99 at h4; Reps5,9 (ERY): EPOR_b → 4.0 at h5 | v5 |
| GATA1 basal=0.08 vs PU1=0.06: 33% structural ERY bias → ERY wins 2× over MYELOID in paired experiments | 2/10 ERY (EPO=1) vs 1/10 MYELOID (GCSF=1) at equal cytokine | v5 |
| Receptor kinetics GCSFR ≈ EPOR at equal cytokine concentration (within 5%) | k_eff analysis; confirmed by similar GCSFR_bound/EPOR_bound ranges | v5 |
| **GCSF must be set EXPLICITLY as a property sweep override** — if omitted the model default (0.001) is used, giving GCSFR_bound≈0.005, disabling myeloid fate, yielding 100% ERY across all EPO levels regardless of pH | run_20260315_113546 (Phase G-v4b): 21 conditions × 100 reps = 100% ERY at every tested point | v6 |
| At GCSF=0.001, P(ERY) cannot be used to locate EPO* — the system is always in the ERY basin by construction, not by decision | run_20260315_113546 analysis: GCSFR_bound=0.004–0.005, T26 factor≈2.7 throughout | v6 |
| pH↑ amplifies stochastic noise in GATA1_nuc (CV: 19–23% at pH=7.0 → 27–32% at pH=8.0) — real coupling independent of GCSF; pH effect on mean GATA1 is sub-sigma at N=100 (Δ/σ=0.3–0.7) | run_20260315_113546: detectable trend but not statistically significant at N=100 | v6 |
| **EPO range must straddle EPO*** — at GCSF=1.1, net-flux balance EPO*≈0.52 mM; any EPO sweep entirely below EPO* gives all-MYE by construction (and entirely above gives all-ERY); confirmed by rate-function analysis: EPO=0.43–0.45 vs GCSF=1.1 gives PU1/GATA1=1.08–1.11× throughout | Phase G-v5 pre-run analysis (2026-03-15): EPOR_b=50×EPO/(10+EPO), GCSFR_b=4.93, net_gata1=0.08×t(b)/d(b); transition at EPO≈0.52 | v6 |
| **EPO* is pH-dependent** — higher pH lowers EPO*; G-v7 revised values: EPO*=0.634 (pH=7.5) / 0.596 (pH=8.0) / >0.65 (pH=7.0); G-v6 anomalous results (EPO=0.57/pH=8→95% ERY) were non-reproducible; mechanism is pGATA1/pPU1 phosphorylation ratio | Phase G-v7 run_20260317_135730: consistent monotone dose-response; G-v6 EPO=0.57/pH=8 condition z=−22.9 vs G-v7 | v6 |
| **Stochastic commitment window is t=100–500s** — trajectories are indistinguishable before t≈100s (seed-identical up to that point); stochastic fluctuations in the 100–500s window determine fate; this is 5× later than the t=91s deterministic cascade seen with GCSF=0.001 | Phase G-v6 EPO=0.57/pH=8.0 trajectory analysis: separation 1.3× at t=100s → 352× at t=500s | v6 |

---

## Open Research Questions (v6 era)

| ID | Question | How to test | Status |
|---|---|---|---|
| RQ-v6-1 | Does Km_self=1 break the limit cycle and create stable attractors? | 10-rep 6hr batch on v6 with EPO=GCSF=1.0 | ⬜ pending |
| RQ-v6-2 | Is MYELOID commitment accessible at equal EPO=GCSF=1.0? | Same batch — look for PU1_nuc/GATA1_nuc >1.5 | ⬜ pending |
| RQ-v6-3 | Does the 2:1 ERY:MYELOID bias persist in v6, or does Km_self=1 equalize it? | Compare ERY/MYELOID counts in v6 batch | ⬜ pending |
| RQ-v6-4 | Does the limit cycle period change with Km_self=1? | Count entry/exit cycles in v6 batch trajectories | ⬜ pending |
| RQ-v6-5 | What is EPO*(pH) — the EPO level giving P(ERY)=0.5 per pH level? | **Phase G-v6/G-v7** | ✅ **answered (G-v7 supersedes)** — EPO*=0.634 (pH=7.5) / 0.596 (pH=8.0); pH=7.0 EPO*>0.65 (not found) |
| RQ-pH | Is EPO* detectably shifted across pH 7.0–8.0? | **Phase G-v6/G-v7** | ✅ **answered** — Δ(pH=7.5→8.0)≈−0.038 mM; mechanism pGATA1/pPU1 ratio |
| RQ-pH-noise | Does pH↑ systematically increase GATA1_nuc stochastic noise (CV)? | Phase G-v6 | ✅ **confirmed in bistable conditions** — pH also deepens both attractors; shift in EPO* is the dominant effect |
| RQ-EC | Is energy charge fate-independent in v6? | Phase G-v6 | ✅ **partially revised** — EC lower at pH=8 (0.8708 vs 0.8882) due to pGATA1 flux; not a fate proxy within a given pH |
| RQ-bistable | Is the model stochastic bistable or instructive? | Phase G-v6 | ✅ **answered** — stochastic bistable; 13/24 conditions mixed; bimodal BC>0.88 in all; commitment window t=100–500s |
| RQ-G8-1 | EPO* at pH=7.0 | EPO grid 0.65–0.85; N=200 | ⬜ pending |
| RQ-G8-2 | 95% CI on EPO*(pH=7.5) | Fine grid 0.61–0.67 step 0.005; N=200 | ⬜ pending |
| RQ-G8-3 | 95% CI on EPO*(pH=8.0) | Fine grid 0.57–0.63 step 0.005; N=200 | ⬜ pending |

## v5 Batch Results Summary

| Batch | EPO | GCSF | ERY | MYELOID | Collapse | Undecided | Key finding |
|---|---|---|---|---|---|---|---|
| `batch_20260310_123621` | 1.0 | 0.1 | 2/10 | 0/10 | 3/10 | 5/10 | Receptor noise tipping point; GCSF too low for MYELOID |
| `batch_20260310_151034` | 0.0 | 1.0 | 0/10 | 1/10 | 6/10 | 3/10 | Limit cycle confirmed; 6-min period; EPO=0 → GATA1 always net-negative |

## v6 Batch Results Summary

| Batch | EPO range | GCSF | pH | N | ERY | MYE | Key finding |
|---|---|---|---|---|---|---|---|
| `run_20260315_113546` (Phase G-v4b, INVALIDATED) | 0.395–0.46 | **0.001** | 7/7.5/8 | 2100 | 2100 | 0 | GCSF was model default 0.001; PU1 pathway disabled; 100% ERY structurally |
| `run_20260315_164919` (Phase G-v6) | 0.30–1.10 | **1.1** | 7/7.5/8 | 2400 | 1025 | 1375 | **Stochastic bistable confirmed.** pGATA1/pPU1 ratio is the pH sensor. Commitment window t=100–500s. EPO* values superseded by G-v7. |
| `run_20260317_135730` (Phase G-v7) | 0.52–0.65 | **1.1** | 7/7.5/8 | 2400 | — | — | **Fine-grid EPO* characterisation.** EPO*=0.634/0.596 (pH=7.5/8.0); pH=7.0 EPO*>0.65. G-v6 anchors non-reproducible. |

---

## Architecture-Independent Axioms (hold for any version)

| Axiom | Basis |
|---|---|
| A2: Fate decision is structured at the receptor layer (L1) | EPOR_bound/GCSFR_bound is the first asymmetric signal; downstream layers execute but cannot reverse it |
| A3: Arrhenius T-optimum = 310.15 K | Ea/R values identical across v4–v6 |
| A4: Energy layer is thermodynamically sufficient in all explored conditions | EC ≥ 0.90 in all runs; never limiting |
| A5: mRNA pool is fate-independent | Total mRNA within 10% across ERY/MYELOID/COLLAPSE for same cytokine |
| A6: Commitment threshold must emerge from dynamics, NOT from artificial parameter tuning | User requirement — any "fix" must be justified by what the previous batch was telling us |
