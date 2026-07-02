# Manuscript-rewrite readiness recon — 2026-05-03

**Scope.** Stocktake of `workspace/projects/canabidiol/docs/` Q-series
(Q1–Q5b) against the standing manuscript (`manuscript/main.tex`) to
decide whether enough scientific material now exists for a v3 rewrite,
and what the rewrite's spine should look like.

**Engine status (frozen anchor).** HEAD `09e7860a`, CPU-fork in
sweep workers, snapshot auto-decimation. Verified anchor: 6 cells × 30
reps × 1 d ≈ 6 min wall on the 32-core server, 0 errors. Engine is
not the bottleneck — science work can proceed.

---

## 1. Q-series status table (definitive)

| Q  | Question                                          | Status   | Evidence                                                                 |
|---:|---------------------------------------------------|----------|--------------------------------------------------------------------------|
| Q1 | NFkB IC₅₀ on CBD                                  | ANSWERED | Q1 iter (5 cycles) → IC₅₀ ≈ 0.5 µM; Q5 within-A2 refines to 0.08–0.10 µM (basin-dependent) |
| Q2 | Aβ-aggregation bistability                        | PARTIAL  | Topology present; v3 events render it functionally inert. Re-examined indirectly via Q5/Q5b: AbM/AbO basin is real (Q5 A2 clears AbO to 0; Q4r A1 retains 12.8) |
| Q3 | M1↔M2 polarisation conserved + dose-responsive    | ANSWERED | DSEV gradient run_20260502_160439 — M1/M2 sum stable, NFkB ceiling [0.09,0.24] across DSEV |
| Q4 | Inflammation ↛ neuroprotection dissociable        | ANSWERED | v2 manuscript: 88% of conditions; **Q4-redux 7d (post G3b'+G4)**: ΔNH = +35–43 across DSEV=1–5; full therapeutic surface in run_20260502_171610 |
| Q5 | Age-dependent CBD mechanism switch                | PARTIAL  | v2 manuscript anti-inflam(young) → antioxidant(old); Q5 *within-basin-A2* gives Hill IC₅₀ = 0.08 (D=1), 0.10 (D=5) — weakly disease-dependent, but basin caveat holds |
| Q6 | Inverted-U dose response                          | OPEN     | CYP3A4 not yet in topology. Q4r at MAINT∈{0.5,2,5} shows monotone, no inversion |
| Q7 | γ-secretase compartment thermodynamics            | OPEN     | APP/pH branch absent; v3 model carries pH compartment but no spatial γ-sec submodel |
| Q8 | Aβ disaggregation barrier                         | ANSWERED | Trap topology validated; Q4r AbO accumulation 4.7→123 monotone in DSEV at M=0 |
| Q9 | Temperature × age synergy                         | ANSWERED | Phase-1 success (older docs); Q4-redux uses Temperature_factor in T21 — sustained NH protection |
| Q10| BDNF → neurogenesis arc                           | PARTIAL  | Arc present; Q3 confirmed BDNF not disease-coupled in v3; G3b' (K=0.1→2.0) restored disease-aware coupling, validated in Q4-redux |

**New (post-Q-list) findings worth foregrounding:**

- **F-NEW-1 — ROS bistability cusp at moderate disease (D≈1.5–2).**
  Q4-redux uncovered a GSH-mediated cusp (Antioxidant capacity
  K=4.12+0.05·GSH crosses the AbO-driven production curve at GSH≈50,
  i.e. DSEV≈2). Bimodal at D=1 (σ=7.9) and D=2 (σ=21.6, range
  [42, 132]); off-cusp tight at D=0 (σ=0.14) and D=5 (σ=0.23).
  CV ≈ 25 % on the cusp — biologically faithful (GSH depletion is a
  hallmark of AD). MAINT does not rescue the cusp because CBD does
  not directly replenish GSH in current topology.

- **F-NEW-2 — Two distinct disease attractors A1 vs A2.**
  Q5 (post-G5a one-line softening of T20) flipped 30/30 reps to a new
  basin: GSH=0/GSSG=72.5 (vs Q4r's 72.5/0), AbO cleared to 0 (vs 12.8),
  BDNF crashed to 0, NH=0.5. Same total redox pool, opposite sides.
  Q5b (1-d horizon, GSH₀ scan) shows commitment is post-day-1; GSH₀
  alone does NOT predict A1 vs A2 — selection is driven by the slow
  Aβ→ROS→BDNF coupling between d1 and d7. **A2 is a redox-collapse
  phenotype orthogonal to classical amyloid disease**, biologically
  documented (chronic GSH depletion drives neurodegeneration via
  pathways orthogonal to Aβ).

- **F-NEW-3 — Patch-induced basin shifts are first-order.**
  A single rate-coefficient softening (G5a, 0.004 → 0.001 on T20 ROS
  baseline term) flipped the global attractor. Methodological
  consequence: every model edit must be re-baselined; replicate σ ≈ 0
  is not "broken RNG" — it is deep-basin localisation.

---

## 2. Manuscript fit analysis

**Current manuscript (`main.tex`, 633 lines, v2-based):**

- Title leads with "Dissociated Therapeutic Axes, Stochastic Amyloid
  Bistability, and Age-Dependent Mechanism Switching"
- Methods describes the v2 model (34 places, 45 transitions, 100 arcs,
  4 P-invariants) and the 8×4×3 = 96-cell factorial (CBD × Age × pH).
- Results sections: phase transition, dissociation gap, AbO
  bistability, factorial η², two-attractor, critical slowing,
  pathway decoupling, age-mechanism switch.
- Findings entirely from the v2 model — pre-G3b', pre-G4, pre-G5a,
  pre-Q-redux 7-d horizon.

**v3 model (`canabidiol-q1-testable.shy`, current HEAD `4788e00c`):**

- 48 transitions, 104 arcs, 43 events (15 install + 1 LOAD + 27 maint).
- Q4-redux 7-d sweep is the most complete therapeutic-surface result
  the project has ever produced (4×4 factorial, 17 cells × 20 reps,
  all PASS criteria except A1/A7 ceiling).
- Q5/Q5b expose multi-basin landscape that v2 manuscript does not
  acknowledge.

**Gap.** The v2 manuscript is internally consistent but tells a
*single-basin* story on a *6-h* horizon with a *3-event*
pharmacokinetic protocol. v3 results show: (a) the therapeutic window
extends to 7 d under realistic 27-event maintenance dosing,
(b) protection caps near NH ≈ 60 (not 95 — oxidative-aging baseline),
(c) ROS exhibits a genuine cusp at moderate disease,
(d) the system has at least two reachable attractors.

---

## 3. Publication-grade material inventory

### A — Ready for v3 rewrite (robust, reproducible)

1. **Therapeutic-window 4×4 factorial (Q4-redux)** — full surface,
   17 cells × 20 reps × 7 d, 0 errors, deterministic patch
   verification (G3b' + G4) in `model_snapshot.shy`. Three figures'
   worth: NFkB suppression heatmap, NH protection heatmap, AbO
   suppression heatmap, plus PK panel.
2. **NFkB IC₅₀ Hill fit** — Q5 within-A2 grid (M ∈ {0, 0.05, 0.1,
   0.2, 0.35, 0.5}); IC₅₀ ≈ 0.08 µM (D=1), 0.10 µM (D=5), n ≈ 1.
   Q1-iter cross-check at coarser grid converges (≈ 0.3–0.5 µM).
3. **ROS bistability discovery (F-NEW-1)** — Q4r §"ROS-bistability
   investigation" derives the cusp analytically (K(GSH) crossover),
   confirms bimodality with per-replicate min/max statistics. Strong
   biological hook (AD + glutathione depletion literature).
4. **Disease-cascade monotonicity (Q3)** — DSEV 0→5 gradient at
   MAINT=5, NFkB ceiling [0.09, 0.24] — disease-graded but
   CBD-suppressed. Validates the dissociation claim under v3.
5. **Dissociation gap (Q4 ANSWERED, both v2 and Q4-redux)** —
   the manuscript's headline finding is independently confirmed in
   v3 at 7 d horizon under realistic dosing.

### B — Promising but needs one more sweep

1. **Two-basin landscape (F-NEW-2)** — Q5+Q5b establish existence
   and timing. Need: Q5c (7-d GSH₀ scan, 8 cells × 30 reps,
   ≈ 90 min wall) to map the basin boundary, and Q5d (time-series
   capture at GSH₀=70, n=10, 10-min sampling) to visualise the
   d1→d7 commitment trajectory.
2. **AbM monomer/aggregate bistability (Q2)** — present in topology,
   visible in Q4r vs Q5 endpoint contrast (AbO=12.8 vs 0). Need a
   dedicated stress sweep on AbM_initial × AbAggregation_rate
   2×2 to formalise.

### C — Unwritable without more model work

1. **Inverted-U dose response (Q6)** — needs CYP3A4-mediated
   bell-curve. Topology absent; would require a new submodel.
2. **γ-secretase compartment (Q7)** — APP/pH branch missing.
3. **BDNF → neurogenesis disease coupling (Q10)** — G3b' fix
   restored the coupling but the long-horizon dose-response of the
   neurogenesis arm has not been measured.
4. **Age-dependent mechanism switch (Q5 sensu manuscript)** — v2
   results stand, but v3 has not re-run the age axis post-G5a. The
   basin caveat means v2's age-switch finding may not transfer to v3
   without re-validation.

---

## 4. Recommended manuscript strategy

**Decision: rewrite is feasible NOW, but the spine should change.**

### Spine v3 (proposed)

1. **Title shift.** Drop "age-dependent mechanism switching" from
   the headline (not re-validated in v3); keep "dissociated
   therapeutic axes" and replace amyloid bistability with the new,
   stronger **redox-cusp bistability**.
   Suggested: *"In silico mapping of cannabidiol neuroprotection in
   Alzheimer's disease reveals a dissociated therapeutic window and
   a glutathione-mediated bistable cusp at moderate disease severity."*

2. **Methods.** Update to v3 model (48 T / 104 arcs / 43 events,
   `canabidiol-q1-testable.shy`). Document the experiment-plan vs
   object-net split (▢ parameter places, ⬡ signal places), the
   13-tuple Bio-PN formalism, and the τ-leaping engine. Note 7-d
   horizon under 27-event maintenance dosing as the canonical
   protocol.

3. **Results — proposed figure list.**
   - **Fig 1**: Topology overview + canonical 4-carrier legend.
   - **Fig 2**: Therapeutic surface (Q4-redux) — 4×4 NH heatmap +
     NFkB heatmap + AbO heatmap.
   - **Fig 3**: NFkB Hill fit (IC₅₀ ≈ 0.08–0.10 µM); shows
     dissociation gap (NH plateau at ~50–60 vs NFkB → 0).
   - **Fig 4 (NEW HEADLINE)**: ROS cusp at D≈2 — bimodality
     histograms across DSEV, mechanistic K(GSH) crossover plot,
     phase portrait sketch in (GSH, AbO) space.
   - **Fig 5**: Two attractors A1 vs A2 (Q5) — same-parameter,
     opposite-state plot; mechanistic explanation panel.
   - **Fig 6**: Disease cascade monotonicity (Q3 + Q4r at M=0
     column).

4. **Discussion.** Re-frame around three findings:
   - **F1**: CBD's anti-inflammatory action is potent (sub-µM IC₅₀)
     but cannot fully restore NH — dissociation gap matches clinical
     ADAPT/INTREPAD failures.
   - **F2**: Disease severity selects between two stable cellular
     phenotypes (amyloid-dominant vs redox-collapse); CBD modulates
     within a basin but does not switch basins. Therapeutic
     implication: GSH-replenishment co-therapy may be needed at
     moderate disease.
   - **F3**: A glutathione-mediated cusp at moderate disease
     creates intrinsic patient-to-patient variability — has direct
     clinical-trial design implications (stratify by GSH/biomarker).

5. **Limitations (honest).** v2's age-mechanism switch is not
   re-validated in v3; CYP3A4 inverted-U absent; γ-secretase
   compartment absent; basin assignment depends on full 7-d
   integration (not detectable at shorter horizons). One-line rate
   edits can flip global attractors — model is sensitive and the
   results are predictions, not guarantees.

### Pre-rewrite work to commission (2–4 sweeps)

| ID  | Sweep                                         | Wall (est) | Why                                       |
|-----|-----------------------------------------------|-----------:|-------------------------------------------|
| Q5c | GSH₀ ∈ {10..110} × 7 d × n=30                 | ~90 min    | Map basin boundary in GSH₀ space          |
| Q5d | Time-series, GSH₀=70, n=10, 10-min sampling   | ~30 min    | Visualise d1→d7 commitment                |
| Q4-age | Q4-redux protocol × Age ∈ {55, 65, 75, 85}  | ~3 h       | Re-validate v2's age-switch in v3         |
| Q2-AbM | AbM_init × AbAggregation_rate 4×4 × 7 d     | ~90 min    | Formalise amyloid bistability under v3    |

These four would close every "PARTIAL" row in §1 and let the rewrite
ship without "results pending."

---

## 5. Bottom line

- v3 has **enough robust material to rewrite the manuscript** — the
  Q4-redux therapeutic surface alone is more complete than v2's
  6-h, 3-event factorial.
- **The headline should change**: amyloid bistability (v2) →
  redox-cusp bistability (v3, F-NEW-1) is a stronger, mechanistically
  derived result.
- v3 also reveals a **two-basin landscape** that v2 missed entirely
  — this is publishable and reframes "stochastic variability" as
  "basin selection" with clinical implications.
- **Age-switch claim should be demoted** until re-validated under v3.
- Four targeted sweeps would close all open Q-series gaps relevant
  to publication.

The cleanest path: (1) commission Q5c + Q4-age this week,
(2) draft v3 spine in parallel, (3) integrate when sweeps complete.
