# Protocol Q4 — Inflammation–neuroprotection dissociation

> **Pairing.** Model: [`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
> (calibrated, post B1+B2+B3+B7).

## Hypothesis

Suppressing inflammation (low NFκB, low cytokines) is **necessary but
not sufficient** for neuron-health rescue. Cells in which MAINT_DOSE
is sufficient to drive NFκB endpoint < 1 will *not* uniformly recover
Neuron_Health to ≥ 95; a substantial fraction (≥ 30 %) shows
NFκB suppressed AND NH < 95 — the **dissociation phenotype** —
because Neuron_Health has at least two independent destruction
arms (`Neurotoxicity` reads ROS and Aβ_Oligomer separately from
TNFα). This reproduces the canonical ADAPT 2007 / INTREPAD 2019
clinical negative result: NSAIDs lower inflammatory biomarkers,
fail to deliver cognitive benefit.

## Environment panel

| Place | Value | Units | Notes |
|---|---:|---|---|
| `DISEASE_SEVERITY` | **swept** | level | spans untreated → severe |
| `LOADING_DOSE` | **10** | µM | bolus at t = 0 |
| `MAINT_DOSE` | **swept** | µM | spans null → saturating |
| `DOSE_INTERVAL` | **21600** | s | 6 h cadence |
| `TEMPERATURE` | 310.15 | K | |
| `AGE` | 72 | y | |
| `PH` | 7.4 | — | |

## Viability panel — sweep plan

**Mode:** Factorial • **Replicates:** 30 • **Duration:** 604800 s
(7 d) • **Termination:** time

| Sweep parameter | Path | Values | Cells |
|---|---|---|---:|
| `[param] MAINT_DOSE` | `MAINT_DOSE.initial_marking` | `[0.0, 0.5, 2.0, 5.0]` | 4 |
| `[param] DISEASE_SEVERITY` | `DISEASE_SEVERITY.initial_marking` | `[0.0, 1.0, 2.0, 5.0]` | 4 |

**Cells:** 16 + Baseline = 17 • **Total sims:** 17 × 30 = **510**

This is the canonical Q4r grid, retained because the bistable cusp
at DSEV=2 may or may not survive calibration — both outcomes are
findings of interest.

## Acceptance criteria

Per-cell endpoint readouts (mean ± SD over 30 reps):

| Acceptance | Target |
|---|---|
| **A1 — Healthy at saturating CBD:** `NH(DSEV=0, MAINT=5) ≥ 90` | strict |
| **A2 — Untreated cascade monotone in DSEV:** NFκB(MAINT=0) non-decreasing in DSEV | strict |
| **A3 — Therapeutic effect:** `NH(MAINT=5) − NH(MAINT=0) ≥ 10` for DSEV ≥ 1 | strict |
| **A4 — NFκB suppression:** `NFκB(MAINT=5) < NFκB(MAINT=0)/2` at every DSEV | strict |
| **A5 — Plaque monotone:** Aβ_Plaque non-increasing in MAINT, non-decreasing in DSEV | strict |
| **A6 — Saturation tail:** `NH(DSEV=5, MAINT=5) < NH(DSEV=1, MAINT=5)` (residual ceiling) | strict |
| **A7 — Dissociation count:** ≥ 30 % of (DSEV ≥ 1, MAINT ≥ 0.5) cells satisfy `NFκB < 1 ∧ NH < 95` | headline finding |

## Falsification

- A1–A5 fail in any combination ⇒ model not calibrated; do not
  proceed to manuscript update; revisit upstream Q1/Q3 first.
- A7 fails (no dissociation) ⇒ NH is single-arm-driven; either ROS or
  TNFα route is dead. Audit `Neurotoxicity` (T20) input arcs.
- Bistable cusp persists at (DSEV=2, MAINT=2) ⇒ rerun with
  60 reps/cell and report basin populations.

## Wet-lab anchors

- ADAPT Research Group 2007 (*Neurology*) — NSAID prevention trial,
  null cognitive outcome.
- INTREPAD 2019 (*Neurology*) — naproxen prevention trial,
  null cognitive outcome.
- Heneka et al. 2015 (*Lancet Neurol*) — neuroinflammation review,
  dissociability hypothesis.

## Manuscript section

Replaces the entire former Q4r-final section in
[`manuscript/main_v3.tex`](../manuscript/main_v3.tex) §results-Q4r.

## Results

⏸ Pending dispatch.
