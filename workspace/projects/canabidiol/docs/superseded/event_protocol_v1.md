# Event Protocol — Cannabidiol Dosing Sweep (v1)

**Project:** `canabidiol`
**Model:** `cbd_ad_neuroprotection_v2.shy`
**Author:** auto-generated from analysis of `run_20260423_012606`
**Date:** 2026-04-23

---

## 1. Motivation

The first event-bearing sweep (`run_20260423_012606`) used a single
washout-then-redose pattern (`t > 5400 → 0`, `t > 7200 → 5`) on a
five-point dose grid with 30 replicates per condition. Endpoint-only
analysis missed the most informative dynamics:

* Acute inflammatory transients (TNFα, IL-1β, NF-κB) collapse within
  the first 30 min and are invisible at `t = 10800 s`.
* CBD intracellular **lags** extracellular by ~30 min and **persists
  ≥4 µM** for one hour after extracellular washout — PPARγ activation
  tracks the intracellular reservoir, not the bolus.
* Plaque dynamics are **non-monotonic**: at Age 55 the system clears
  plaque after `t ≈ 8000 s`; at Age 75 it locks in. The transition is
  a bistable boundary that lives between Age 65 and Age 75.
* The single 5 µM redose at `t = 7200 s` undershoots: extracellular
  decays back to 1.3–3.1 µM within an hour and intracellular never
  re-peaks.

This protocol set is designed to **probe each of those
windows** with the minimum number of carefully chosen factor levels.

---

## 2. Functional concentration window (target)

From the dose–response of `run_20260423_012606`:

| Compartment | Lower bound | Upper bound | Rationale |
|-------------|-------------|-------------|-----------|
| `CBD_extracellular` | **3 µM** | **10 µM** | Saturating neuron rescue; little marginal benefit beyond 10. |
| `CBD_intracellular` | **4 µM** | **8 µM** | PPARγ ≥ 0.7 (clear dose biomarker). |

The model's effective extracellular t<sub>1/2</sub> ≈ 41 model-min.
To stay in [3, 10] µM the inter-dose interval is
$\Delta t \approx 1.74\,t_{1/2} \approx 72$ model-min ≈ 4300 s.

---

## 3. Five protocols (run independently, share the same 30-replicate factorial)

All protocols share:

* `replicates: 30`
* `seed_base: 42`
* `tau_epsilon: 0.03`, `max_tau: 0.1`
* `duration: 14400 s` (4 model-hours; covers a full BID cycle)
* `pH: 7.4` (acidotic case adds noise, see §6)

The Age axis is reduced to **{65, 75, 85}** because Age 55 is too
healthy to exhibit the transitions of interest.

### Protocol P1 — "Pulse maintenance" (BID-mimic)

**Hypothesis:** A loading bolus + small repeats every 4300 s holds
intracellular CBD in [4, 8] µM and **prevents** the lock-in transition
at Age 75.

```yaml
events:
  - id: load
    trigger: "t > 0.1"
    assignments: { CBD_extracellular: "{LOADING}" }
  - id: maint_1
    trigger: "t > 4300"
    assignments: { CBD_extracellular: "CBD_extracellular + {MAINT}" }
  - id: maint_2
    trigger: "t > 8600"
    assignments: { CBD_extracellular: "CBD_extracellular + {MAINT}" }
  - id: maint_3
    trigger: "t > 12900"
    assignments: { CBD_extracellular: "CBD_extracellular + {MAINT}" }

factorial:
  LOADING: [5, 10, 20]      # initial bolus (µM)
  MAINT:   [1, 3, 5]        # top-up bolus (µM)
  Age:     [65, 75, 85]
# total = 27 conditions × 30 reps = 810 replicates
```

**Read-outs (high-resolution snapshots):**
`Neuron_Health, Abeta_Plaque, Microglia_M1, Microglia_M2,
PPARg_active, CBD_intracellular` at
`t ∈ {0, 60, 300, 600, 1200, 1800, 3000, 4300, 4500, 5400, 6000,
8600, 8800, 10000, 12900, 13200, 14400}`.

### Protocol P2 — "Withdrawal challenge" (no rescue)

**Hypothesis:** Without redose, the inflammatory flare and plaque
re-accumulation rate after washout characterise the *withdrawal cost*.
Currently masked by the redose in `run_20260423_012606`.

```yaml
events:
  - id: load
    trigger: "t > 0.1"
    assignments: { CBD_extracellular: "{LOADING}" }
  - id: washout
    trigger: "t > 5400"
    assignments: { CBD_extracellular: "0" }

factorial:
  LOADING: [3, 10, 20]
  Age:     [65, 75, 85]
# 9 conditions × 30 reps
```

**Critical read-outs (to be recorded as time-series):**

| Metric | Window | Why |
|---|---|---|
| `TNFa, IL1b, NFkB_p65` | 5400 – 9000 s | rebound flare |
| `Microglia_M1/M2` ratio | 5400 – 14400 s | polarization swing |
| `Abeta_Oligomer` | 5400 – 14400 s | re-seeding |
| `CBD_intracellular` | 5400 – 14400 s | reservoir decay |
| `Neuron_Health` | full | net cost |

### Protocol P3 — "Late rescue" (post-onset window)

**Hypothesis:** Treatment started *after* inflammation onset still
recovers neuron health if begun before plaque crosses ~30
(`t ≈ 5000 s` at Age 75/85, CBD=0). Establishes the **therapeutic
time window** (analog of clinical "stroke time-to-tPA").

```yaml
events:
  - id: rescue
    trigger: "t > {DELAY}"
    assignments: { CBD_extracellular: "10" }
  - id: maint
    trigger: "t > {DELAY} + 4300"
    assignments: { CBD_extracellular: "CBD_extracellular + 3" }

factorial:
  DELAY: [1800, 3600, 5400, 7200, 9000]   # seconds of untreated disease
  Age:   [65, 75, 85]
# 15 conditions × 30 reps
```

**Read-outs** identical to P2 plus `Abeta_Plaque` peak height and
post-rescue trajectory.

### Protocol P4 — "Lock-in bifurcation map" (fine dose scan)

**Hypothesis:** A bistable boundary exists at Age 75 between
**clearing** and **locked** plaque trajectories. The transition zone
predicted from `run_20260423_012606` is `CBD ∈ [2, 5] µM`. Map it.

```yaml
events: []                  # constant exposure, no events
factorial:
  CBD_extracellular_init: [0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]
  Age: [65, 75, 85]
replicates: 60               # double — to resolve stochastic switching
duration: 14400
# 30 conditions × 60 reps
```

**Read-outs:** full `Abeta_Plaque(t)` trajectory per replicate (not
just mean — the variance/bimodality is the signal). Use
`Neuron_Health(t = 14400)` as a binary classifier (≥80 = rescued,
< 60 = locked).

### Protocol P5 — "Acute kinetic capture" (high time-resolution rerun)

**Hypothesis:** Cytokine and NF-κB transients in `[0, 1800] s` carry
the actual pharmacological signal that endpoint-only data drops.

```yaml
events:
  - id: load
    trigger: "t > 0.1"
    assignments: { CBD_extracellular: "{LOADING}" }

factorial:
  LOADING: [0, 3, 10]
  Age:     [65, 85]
duration: 3600
snapshot_interval: 30        # every 30 s — 120 frames
# 6 conditions × 30 reps
```

**Read-outs:** `TNFa, IL1b, NFkB_p65, Nrf2_free, PPARg_active,
CBD_intracellular` at every snapshot. This is the only protocol that
fully resolves the acute resolution kinetics.

---

## 4. Total cost estimate

| Protocol | Conditions | Reps | Sims | Wall-clock (~700 s/cond) |
|---|---:|---:|---:|---:|
| P1 | 27 | 30 | 810 | ~5.3 h |
| P2 | 9  | 30 | 270 | ~1.8 h |
| P3 | 15 | 30 | 450 | ~3.0 h |
| P4 | 30 | 60 | 1800 | ~12 h |
| P5 | 6  | 30 | 180 | ~0.7 h (shorter duration) |
| **Total** | **87** | – | **3510** | **~22.8 h GPU** |

Run order recommendation: **P5 → P2 → P3 → P1 → P4**.
P5 first (cheap, validates the kinetic story).
P4 last (heaviest, only run if earlier protocols confirm bistability).

---

## 5. Analysis pre-registration

For each protocol the following metrics are committed in advance:

* **Trough CBD_intracellular** over `[0, duration]` — primary PK target.
* **AUC₀–T (Neuron_Health, BDNF)** — therapeutic exposure metric.
* **ΔTNFα, ΔIL-1β** transient peak heights — acute response.
* **M1/M2 trajectory** (slope at t=5400, recovery time after redose).
* **Plaque outcome class** at `t = 14400` (rescued vs locked vs
  intermediate, by Otsu threshold of `Neuron_Health`).
* **Bifurcation probability** (P4 only): for each `CBD_init`, fraction
  of 60 replicates ending in the rescued class.

---

## 6. Deferred / nice-to-have

1. **pH sweep** — drop for now (effect was ~2 % in `run_20260423_012606`).
   Re-add only if P3 reveals interaction with delay-to-rescue.
2. **Per-condition event opt-out** — needed so that Baseline and
   `CBD_init = 0` cells are not contaminated by a protocol's redose.
   Currently events live on the model and apply to all snapshots.
   See `manage_todo_list` item "Capture model.events in automation
   category".
3. **Once-daily vs BID equivalent** — currently P1 covers 4 maintenance
   doses inside 4 h of model time, mimicking BID compressed. A real
   dosing-interval comparison needs longer model durations
   (≥ 24 model-h) and is deferred until after P4.
4. **Stochastic switching transitions** — if P4 shows clear bimodality,
   add a follow-up sweep with `replicates = 200` at the single
   boundary cell.

---

## 7. File handoff

* `sweep_config.json` per protocol → write to
  `workspace/projects/canabidiol/sweep_config.<protocol>.json`.
* Outputs land at
  `workspace/projects/canabidiol/experiments/results/run_<timestamp>/`
  (auto-resolved; do **not** override).
* Analysis scripts (one per protocol) belong in
  `workspace/projects/canabidiol/scripts/`.
* Protocol revisions append a `_v<N>` suffix to **this** file; never
  overwrite v1 in place.
