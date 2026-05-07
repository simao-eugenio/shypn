# Protocol Q2 — Aβ aggregation as stochastic bistable switch

> **Pairing.** Model: [`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
> (calibrated, post B1+B2+B3+B7).

## Hypothesis

Under disease drive and **no CBD**, individual replicates partition
into two outcome basins at the Aβ_Oligomer / Aβ_Plaque axis:

- **Clear basin** — Aβ_Oligomer endpoint < 5, Plaque < 1.
- **Lock-in basin** — Aβ_Oligomer endpoint > 30, Plaque > 5.

The bimodal split arises from the self-amplifying `Abeta_Aggregation`
transition (rate ∝ Aβ_Monomer²) racing against first-order
clearance pathways (`Abeta_Monomer_Clearance`,
`Abeta_Oligomer_Clearance`, `Plaque_Clearance`). Bistability is a
function of the temperature × age co-incidence: visible only at
`TEMPERATURE ≥ 310 K AND AGE ≥ 75 y` per the v2 phase-1 envelope.

## Environment panel

| Place | Value | Units | Notes |
|---|---:|---|---|
| `DISEASE_SEVERITY` | **2.0** | level | severe-enough drive to populate both basins |
| `LOADING_DOSE` | **0** | µM | drug-free arm — exposes intrinsic switch |
| `MAINT_DOSE` | **0** | µM |  |
| `DOSE_INTERVAL` | 1e9 | s | |
| `TEMPERATURE` | **swept** | K | crosses bistability threshold |
| `AGE` | **swept** | y | crosses bistability threshold |
| `PH` | 7.4 | — | |

## Viability panel — sweep plan

**Mode:** Factorial • **Replicates:** 60 (high — needed to resolve
basin populations) • **Duration:** 604800 s (7 d) •
**Termination:** time

| Sweep parameter | Path | Values | Cells |
|---|---|---|---:|
| `[param] TEMPERATURE` | `TEMPERATURE.initial_marking` | `[305, 310.15, 315]` | 3 |
| `[param] AGE` | `AGE.initial_marking` | `[60, 75, 85]` | 3 |

**Cells:** 9 + Baseline = 10 • **Total sims:** 10 × 60 = **600**

Long horizon (7 d) lets the slow plaque-clearance arm equilibrate;
60 reps/cell give ≥ 95 % power to distinguish a 70/30 split from a
50/50 null.

## Acceptance criteria

For each cell, fit a 2-component Gaussian mixture to the per-replicate
Aβ_Oligomer endpoint:

| Quantity | Target |
|---|---|
| Bimodality coefficient (BC) | ≥ 0.55 in at least the (T=315, AGE=85) cell |
| Coefficient of variation (CV) | ≥ 1.0 in the same cell |
| Basin separation | ≥ 5σ between the two component means |
| Monotonicity of `P(lock-in)` | non-decreasing in TEMPERATURE and in AGE |

**Conservation check:** `Aβ_Monomer + Aβ_Oligomer + Aβ_Plaque` total
mass non-decreasing in time within each replicate
(`APP_Translation` is the source).

## Falsification

- Unimodal endpoint distribution at every cell ⇒ aggregation is
  *not* bistable in the calibrated model — finding null, requires
  manuscript update.
- Lock-in basin populated even at `(T=305, AGE=60)` ⇒ aggregation
  threshold is too low; rate constant on `Abeta_Aggregation`
  needs reduction.
- No T × AGE interaction (factorial decomposition shows no
  synergy) ⇒ the v2 phenomenology was a thermodynamic artefact of
  the previous engine bug.

## Wet-lab anchors

- Knowles et al. 2009 (*Science*) — single-molecule binary outcomes
  in Aβ aggregation kinetics.
- Hellstrand et al. 2010 (*ACS Chem Neurosci*) — nucleation-dependent
  stochastic onset.
- Törnquist et al. 2018 (*Chem Commun*) — secondary nucleation and
  binary fate.

## Manuscript section

Replaces the former Q4r-final §F-NEW-1 "bistable ROS cusp" headline
finding in [`manuscript/main_v3.tex`](../manuscript/main_v3.tex)
§results-Q4r — re-anchored on Aβ_Oligomer (the original wet-lab
literature anchor) instead of ROS.

## Results

⏸ Pending dispatch.
