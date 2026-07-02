# Canabidiol Sweep Parametrics — `canabidiol-q1-testable.shy` (v2)

**Reference model:** [models/canabidiol-q1-testable.shy](../models/canabidiol-q1-testable.shy)
**Formalism status:** ✓ COMPLIANT (audit 2026-05-05, post-refactor commit `6605bd9e`)
**Smoke-validated chronic forcing:** `run_20260505_163211` — Disease_Drive ◇ bridge active, 4.07× Abeta_Production_firings ratio at DSEV=2 vs DSEV=0, 7.8× Neuron_Health damage.

This file is the **canonical reference** for sweep designs. All sweeps run via the Viability Panel → **Run Remote** with the v2 model open in shypn. Operator configures parameters per the tables below.

---

## Cost calibration

Smoke (3 conditions × 3 reps × 24 h) ran in **~12 min wall**.
Linear extrapolation: **~5 sec wall per (replicate × hour-of-sim-time)**.

---

## Sweep 1 — DSEV resolution (validate disease axis)

| Parameter | Values |
|---|---|
| `DISEASE_SEVERITY` | `hy]` |
| `MAINT_DOSE`       | `0` (fixed) |
| `LOADING_DOSE`     | `0` (fixed) |
| `TEMPERATURE`      | `310.15` (fixed) |
| `AGE`              | `75` (fixed) |
| `PH`               | `7.4` (fixed) |
| Replicates         | 30 |
| Duration           | 86 400 s (24 h) |

**Conditions:** 7 × 30 = 210 replicates
**Estimated wall:** ~2 h 20 min
**Headline:** monotone dose-response in `Aβ_Oligomer`, `NFkB_p65`, `Microglia_M1`, **`Neuron_Health` (descending)**.
**PASS:** Spearman ρ ≥ 0.95 (or ≤ −0.95) on all five endpoints across the 7-point ladder.

---

## Sweep 2 — CBD IC50 at fixed mid-disease (Q1)

| Parameter | Values |
|---|---|
| `MAINT_DOSE`       | `[0, 0.5, 1.0, 2.0, 5.0, 15.0]` |
| `DISEASE_SEVERITY` | `0.5` (fixed) |
| `LOADING_DOSE`     | `0` (fixed) |
| `DOSE_INTERVAL`    | `86400` (fixed) |
| Replicates         | 30 |
| Duration           | 14 400 s (4 h) |

**Conditions:** 6 × 30 = 180 replicates
**Estimated wall:** ~20 min
**Headline:** CBD dose-response on `NFkB_p65` endpoint.
**PASS:** `NFkB_p65_endpoint > 50` at CBD=0 AND `< 5` at CBD ≥ 1, monotone in between.
**Anchors:** Kozela 2010 (BV-2, IC50 ~1 µM TNFa); Esposito 2006 (PC12, NFkB sig. at 1 µM).
**Existing config:** [sweep_config.Q1.json](../sweep_config.Q1.json) (panel can reproduce these settings).

---

## Sweep 3 — DSEV × CBD factorial (Q4r — efficacy landscape)

| Parameter | Values |
|---|---|
| `DISEASE_SEVERITY` | `[0.5, 1.0, 2.0]` |
| `MAINT_DOSE`       | `[0, 1.0, 5.0, 15.0]` |
| `LOADING_DOSE`     | `0` (fixed) |
| Replicates         | 30 |
| Duration           | 86 400 s (24 h) |

**Conditions:** 3 × 4 = 12 cells × 30 reps = 360 replicates
**Estimated wall:** ~4 h
**Headline figure:** heatmap of `Neuron_Health_final` over the (DSEV, MAINT_DOSE) plane.
**PASS:** at every DSEV, `Neuron_Health` increases monotonically with `MAINT_DOSE`; at high DSEV the rescue ceiling is set by the model's neurotoxicity floor.
**Existing config:** [sweep_config.Q4r-final.json](../sweep_config.Q4r-final.json).

---

## Sweep 4 — Loading-dose protocol (chronic clinical relevance)

| Parameter | Values |
|---|---|
| `LOADING_DOSE`     | `[0, 5.0, 15.0, 30.0]` |
| `MAINT_DOSE`       | `[0.5, 2.0]` |
| `DISEASE_SEVERITY` | `2.0` (fixed) |
| `DOSE_INTERVAL`    | `86400` (fixed) |
| Replicates         | 30 |
| Duration           | 604 800 s (7 d) |

**Conditions:** 4 × 2 = 8 cells × 30 reps = 240 replicates
**Estimated wall:** **~14 h** ⚠
**Headline:** does a loading dose accelerate steady-state efficacy? Compare `NFkB_p65(t)` and `Neuron_Health(t)` curves under loading vs no-loading at each `MAINT_DOSE`.
**PASS:** with `MAINT_DOSE=0.5`, loading reduces time-to-half-NFkB by ≥ 30 %.
**Note:** dispatch only when the chronic-clinical question is in scope.

---

## Sweep 5 — Environmental sensitivity (validate ◇ bridges)

| Parameter | Values |
|---|---|
| `TEMPERATURE` | `[305, 310.15, 315]` (hypothermia / normal / fever) |
| `AGE`         | `[40, 65, 75, 85]` |
| `PH`          | `[6.8, 7.4]` |
| `DISEASE_SEVERITY` | `1.0` (fixed) |
| `MAINT_DOSE`       | `2.0` (fixed) |
| Replicates         | 15 |
| Duration           | 86 400 s (24 h) |

**Conditions:** 3 × 4 × 2 = 24 cells × 15 reps = 360 replicates
**Estimated wall:** ~4 h
**Purpose:** verifies the four ◇ bridges (`Temperature_factor`, `Age_factor`, `pH_acidosis`, `pH_neutrality`) propagate correctly into rates.
**PASS:** `Aβ_Production_firings` scales as `Temperature_factor × Age_factor` within ±10 %; `NFkB` shows pH_acidosis modulation.
**Status:** diagnostic, not headline. Dispatch for manuscript supplementary.

---

## Recommended order of execution

| Order | Sweep | Wall | Why first/later |
|---|---|---|---|
| 1 | Sweep 1 (DSEV ladder) | ~2 h 20 min | confirms monotone disease axis before any combination work |
| 2 | Sweep 2 (CBD IC50) | ~20 min | quick CBD sanity at chronic mid-disease |
| 3 | Sweep 3 (Q4r factorial) | ~4 h | the headline science figure |
| 4 | Sweep 5 (env sensitivity) | ~4 h | manuscript supplementary |
| 5 | Sweep 4 (loading × maint) | ~14 h | only if clinical-protocol question is in scope |

---

## Operator workflow (Viability Panel → Run Remote)

1. Open [models/canabidiol-q1-testable.shy](../models/canabidiol-q1-testable.shy) in shypn.
2. Open the Viability Panel.
3. Configure the parameters from the chosen sweep table above (sweep variable values, fixed property overrides, replicates, duration).
4. Press **Run Remote**.
5. Provenance check (mandatory): `provenance.json` in the resulting `run_<ts>/` must show
   `model.source_path: …/canabidiol-q1-testable.shy` and a sha256 starting with `25dae348…` (or whatever the current v2 hash is — verify with `sha256sum models/canabidiol-q1-testable.shy`).
   Also confirm `Disease_Drive_final = DISEASE_SEVERITY` per condition (proves the bridge fired).
