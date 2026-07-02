# Q1 — Acute CBD dose-response (24 h, mild AD)

**Run:** `run_20260430_174814` (server: `~/shypn/workspace/projects/canabidiol/experiments/results/`)
**Date:** 2026-04-30
**Model:** `canabidiol-q1-testable.shy` (post place-marking-policy fix, commit `d3bba080`)
**Engine:** GPUHybridEngine + τ-leaping (CuPy 14.0.1, RTX 5060 Ti)

## Protocol

| Field | Value |
|---|---|
| Swept axis | `MAINT_DOSE` (P36, parameter place ▢) |
| Sweep values | `{0, 0.5, 1, 2, 5, 15}` µM |
| Baseline cell | `MAINT_DOSE = 5` (model default) |
| Fixed | `DISEASE_SEVERITY = 0.5` (mild AD installed via events) |
| Fixed | `LOADING_DOSE = 10` µM (single bolus at t = 0) |
| Fixed | `DOSE_INTERVAL = 21600` s (6 h spacing → maintenance doses at 6 h, 12 h, 18 h) |
| Duration | 86 400 s (24 h) |
| Replicates | 30 per condition |
| Termination | deadlock |
| τ-leaping ε | 0.03, max τ = 0.1 s |
| Seed base | 42 |

**Doses delivered per condition** = 1 loading + 3 maintenance = 10 + 3·D µM total.

## Provenance

- `P36.initial_marking`: prior=5.0 → fixed_override applied per condition (Layer-D verified).
- DSEV=0.5 install events (`evt_install_Abeta_*`, `evt_install_Microglia_M1`, etc.) all trigger at t > 0.01 s.
- `model_snapshot.shy` + `provenance.json` saved per run dir; `tokens` key cleanly absent (post-fix).
- Baseline cell numerically identical to `MAINT_DOSE_eq_5` → confirms fixed_override pipeline is faithful.

## Endpoint biology (mean of 30 replicates @ 24 h)

| MAINT_DOSE (µM) | CBD_intra | CBD_Absorption_firings | NFkB_p65 | Microglia_M1 | Microglia_M2 | Neuron_Health |
|---:|---:|---:|---:|---:|---:|---:|
| **0**    | 0.27 | 138 | **1.22** | **6.27** | 41.2 | 70.8 |
| **0.5**  | 0.51 | 147 | 0.61     | 2.47     | 45.0 | 68.7 |
| **1**    | 0.76 | 156 | 0.36     | 1.47     | 46.0 | 69.9 |
| **2**    | 1.25 | 174 | 0.14     | 0.93     | 46.6 | 70.2 |
| **5**    | 2.73 | 228 | **0**    | 0.50     | 47.0 | 71.3 |
| **15**   | 7.67 | 407 | **0**    | 0.50     | 47.0 | 70.3 |

Other endpoints flat across the sweep:
- `Abeta_Monomer ≈ 0.51`, `Abeta_Oligomer = 0`, `Abeta_Plaque = 0`
- `ROS ≈ 17.38`, `Glutathione ≈ 56.35`

## Findings

### F1 — Clean monotonic CBD anti-inflammatory dose-response
NFkB_p65 declines smoothly from 1.22 (untreated) to 0 (saturated):
1.22 → 0.61 → 0.36 → 0.14 → 0 → 0.
**Estimated NFkB IC₅₀ ≈ 0.5 µM** (dose at which NFkB drops to ~50% of untreated value).
Hill-like saturation curve, fully consistent with receptor-mediated CB1/CB2/PPARγ pharmacology.

### F2 — Microglial M1↔M2 polarization mirrors NFkB
M1 collapses 6.27 → 0.50 (12.5× reduction); M2 modestly rises 41.2 → 47.0.
**Estimated M1 IC₅₀ ≈ 0.5–1 µM** — same potency window as NFkB, consistent with NFkB-driven M1 polarization in the model topology.

### F3 — Saturation at MAINT_DOSE ≥ 5 µM
NFkB and M1 hit their floor (0 and 0.50) at 5 µM; the 15 µM arm gives **no further inflammatory benefit** but triples intracellular CBD load (2.73 → 7.67). Diminishing returns / potential toxicity zone. **MAINT_DOSE = 5 µM is the therapeutic plateau.**

### F4 — CBD absorption is dose-linear
Absorption firings grow 138 → 407 (∝ total dose delivered: 10 + 3·D).
Intracellular CBD scales linearly with maintenance dose: `CBD_intra ≈ 0.27 + 0.49·D`.
No PK saturation observed in the tested range.

### F5 — Aβ pool unaffected on the 24 h horizon
Aβ_Monomer flat at ~0.51; Oligomer/Plaque both 0. Either:
- Aβ aggregation kinetics are slower than 24 h (likely), or
- the install_disease events install monomer only at this DSEV.

**Q1 (acute pharmacology) is the wrong question for amyloid clearance** — needs the multi-day Q2 horizon to populate Oligomer/Plaque pools.

### F6 — Neuron_Health robust over 24 h
Variation 68.7–71.3 (~3.7%) is noise-level. Substrate too short and DSEV=0.5 too mild to perturb neurons in 24 h. Neuroprotection endpoint requires Q2 (7 d) or higher DSEV.

### F7 — ROS / Glutathione dose-insensitive (open issue)
Both flat (ROS ≈ 17.38, GSH ≈ 56.35) across the entire sweep. The redox subnet is **decoupled from CBD action under this protocol**. Either:
- CBD has no arc into the ROS subnet in the current topology (model gap), or
- the ROS input is dominated by a non-CBD-modulated source (basal generator).

**Diagnostic action:** trace ROS-producing transitions in `canabidiol-q1-testable.shy`; confirm whether CBD has any signal/test arc into the redox subnet. Suspect M1 antioxidant pathway is missing or wired to wrong place.

## Acceptance criteria for Q1

| Criterion | Status |
|---|---|
| CBD reduces NFkB activation | ✅ 1.22 → 0 across the range |
| CBD shifts microglia M1 → M2 | ✅ 12.5× M1 reduction, mild M2 increase |
| Dose-response monotonic & saturable | ✅ Hill-like, IC₅₀ ≈ 0.5 µM |
| MAINT_DOSE = 5 µM is therapeutic plateau | ✅ confirmed (matches design intent) |
| Aβ load reduced by CBD | ⚠️ **Defer to Q2** (24 h too short for Aβ dynamics) |
| ROS/GSH modulated by CBD | ❌ **Open** (topology audit required) |

## Engine / refactor sanity

- 30/30 replicates × 7 conditions, 0 errors.
- Layer A guardrail, Layer B fixed_overrides, Layer C UI collision detector, Layer D provenance — all clean.
- Place marking persistence policy (commit `d3bba080`) verified: `tokens` absent in saved snapshot; `MAINT_DOSE_final` matches `initial_marking` for all replicates.

## Recommended follow-ups

1. **Q2 — Chronic 7-day** (NEXT): same axis `MAINT_DOSE ∈ {0, 0.5, 1, 2, 5, 15}` µM, duration = 604 800 s (7 d), DSEV=0.5. Endpoints of interest: `Abeta_Oligomer`, `Abeta_Plaque`, `Neuron_Health`, sustained M1/M2 ratio.
2. **Q3 — Disease-severity sweep**: fix `MAINT_DOSE = 5` µM, sweep `DISEASE_SEVERITY ∈ {0, 0.5, 1, 2, 3}`, duration = 86 400 s. Tests dose-disease interaction.
3. **Topology audit (open issue F7)**: trace ROS subnet in `.shy`, confirm CBD → antioxidant arcs exist. If absent, this is a model gap, not a sweep failure.
