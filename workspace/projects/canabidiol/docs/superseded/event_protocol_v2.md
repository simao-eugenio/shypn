# Event Protocol — Cannabidiol Dosing Sweep (v2)

**Project:** `canabidiol`
**Model:** `cbd_ad_neuroprotection_v2.shy`
**Supersedes:** [event_protocol_v1.md](event_protocol_v1.md)
**Date:** 2026-04-23

---

## 0. What changed vs v1

| v1 | v2 |
|----|----|
| Templated `{LOADING}` / `{MAINT}` placeholders inline in events. | **Parameter places** (`LOADING_DOSE`, `MAINT_DOSE`, `DOSE_INTERVAL`) referenced **by name** in event expressions. |
| Factorial dimensions named ad-hoc (`LOADING`, `MAINT`). | Factorial dimensions are **paths to actual model objects** (`LOADING_DOSE.initial_marking`, …). |
| No machine-readable sweep file shown. | Full `sweep_config.<protocol>.json` for each protocol (drop-in for `python -m shypn.cli.sweep`). |
| One events block per hypothesis. | Events laid out **row-by-row** (id, trigger, target, expression) so each row maps 1:1 to an `Events` table row in the Environment Panel. |
| Single monolithic JSON per protocol. | **Per-protocol panel split:** each protocol now lists *Environment Panel* baselines (parameter-place values + events) and *Viability Panel* sweep plan (which parameters get value lists, replicates, duration). The headless `sweep_config.<P>.json` is the same plan re-expressed for `python -m shypn.cli.sweep`. |

**Panel responsibilities (enforced by GUI):**

| Panel | Owns | What goes here |
|---|---|---|
| **Environment** | Parameter-place baseline values, Events table | The §x.1 block of every protocol |
| **Viability**   | Sweep mode (single/factorial), parameter value lists, replicates, duration, termination, queue, Run / Run Remote | The §x.2 block of every protocol |
| **CLI**         | Headless replay of the same plan | The §x.3 JSON (drop-in for `python -m shypn.cli.sweep`) |

**Convention enforced (see `_warn_parameter_naming_violations`):**
ALL_CAPS_NAME ⟺ `is_parameter_place=True`. Expressions reference these
names directly; the simulator resolves them to the place's current
marking at trigger evaluation time.

---

## 1. Parameter places used

These must exist in the model with `is_parameter_place=True`. Three are
already in `cbd_ad_neuroprotection_v2.shy`. The rest are to be added
(one-time, before running the protocol). Throughout this document the
notation `NAME (Pn)` pairs the human-readable place name with its
model ID for unambiguous reference.

| Name (ID) | Status | `parameter_kind` | `parameter_units` | Used by |
|---|---|---|---|---|
| `LOADING_DOSE (P35)`  | ✅ in model  | `dose`     | µM | P1, P2, P3, P5 |
| `MAINT_DOSE (P36)`    | ✅ in model  | `dose`     | µM | P1, P3 |
| `DOSE_INTERVAL (P37)` | ✅ in model  | `interval` | s  | P1, P3 |
| `RESCUE_DELAY (P??)`  | ➕ to add   | `time`     | s  | P3 |
| `CBD_INIT (P??)`      | ➕ to add   | `dose`     | µM | P4 (constant exposure proxy via `initial_marking`) |

**Other (non-parameter) places referenced by events / sweeps:**

| Name (ID) | Role |
|---|---|
| `CBD_extracellular (P1)` | Reaction species (target of every dose event) |
| `Age (P31)` | Bio-PN signal place — swept as factorial dimension |
| `pH (P29)`  | Bio-PN signal place — held at 7.4 |

> If `RESCUE_DELAY` and `CBD_INIT` are missing, add them as standard
> parameter places (gray border, `is_parameter_place=True`) before
> running P3 / P4 — or substitute their roles by directly sweeping
> `CBD_extracellular.initial_marking` (a regular place) in P4 and
> hard-coding the delay grid into the trigger expressions in P3.

---

## 2. Shared simulation parameters

| Field | Value |
|---|---|
| `mode` | `factorial` |
| `replicates` | 30 (P4 = 60) |
| `seed_base` | 42 |
| `tau_epsilon` | 0.03 |
| `max_tau` | 0.1 |
| `duration` | 14400 s (P5 = 3600 s) |
| `termination` | `time` |
| `pH` (initial_marking of `pH` place) | 7.4 |

---

## 3. Protocol P1 — Pulse maintenance (BID-mimic)

**Hypothesis.** A loading bolus + repeated top-ups every `DOSE_INTERVAL`
seconds holds `CBD_intracellular` in [4, 8] µM and prevents the lock-in
transition at Age 75.

### 3.1 Environment Panel — parameter-place baselines & events

**Parameter places (baseline values; the sweep overrides whichever ones it varies):**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `LOADING_DOSE (P35)`  | 10  | µM | swept by Viability |
| `MAINT_DOSE (P36)`    | 3   | µM | swept by Viability |
| `DOSE_INTERVAL (P37)` | 4300 | s | held constant for P1 |
| `Age (P31)`           | 75  | (signal) | swept by Viability |
| `pH (P29)`            | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 0 | µM | reset by `evt_load` |

**Events table (row-per-row → Environment Panel rows):**

| id | trigger | target | expression |
|---|---|---|---|
| `evt_load`    | `t > 0.1`                    | `CBD_extracellular (P1)` | `LOADING_DOSE (P35)` |
| `evt_maint_1` | `t > DOSE_INTERVAL (P37)`            | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)` |
| `evt_maint_2` | `t > 2 * DOSE_INTERVAL (P37)`        | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)` |
| `evt_maint_3` | `t > 3 * DOSE_INTERVAL (P37)`        | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)` |

> The `(Pn)` suffix is **documentation only** — the actual cell value
> stored in the events table is the bare name (`CBD_extracellular`,
> `LOADING_DOSE`, …). The simulator resolves names to places at
> trigger-evaluation time.

### 3.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter (dropdown label) | Path | Values | Levels |
|---|---|---|---:|
| `[param] LOADING_DOSE`  | `LOADING_DOSE.initial_marking`  | 5, 10, 20 | 3 |
| `[param] MAINT_DOSE`    | `MAINT_DOSE.initial_marking`    | 1, 3, 5   | 3 |
| `[param] Age`           | `Age.initial_marking`           | 65, 75, 85 | 3 |

**Cells:** 3 × 3 × 3 = **27**  •  **Total sims:** 27 × 30 = **810**

### 3.3 Headless equivalent (`sweep_config.P1.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v2.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "LOADING_DOSE.initial_marking",   "values": [5, 10, 20]},
    {"type": "places", "path": "MAINT_DOSE.initial_marking",     "values": [1, 3, 5]},
    {"type": "places", "path": "DOSE_INTERVAL.initial_marking",  "values": [4300]},
    {"type": "places", "path": "Age.initial_marking",            "values": [65, 75, 85]}
  ],
  "events": [
    {"id": "evt_load",    "trigger": "t > 0.1",                    "assignments": {"CBD_extracellular": "LOADING_DOSE"}},
    {"id": "evt_maint_1", "trigger": "t > DOSE_INTERVAL",          "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}},
    {"id": "evt_maint_2", "trigger": "t > 2 * DOSE_INTERVAL",      "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}},
    {"id": "evt_maint_3", "trigger": "t > 3 * DOSE_INTERVAL",      "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}}
  ]
}
```

**Cost:** 3 × 3 × 1 × 3 = 27 conditions × 30 reps = **810 sims**.

---

## 4. Protocol P2 — Withdrawal challenge

**Hypothesis.** Without redose, the inflammatory flare and plaque
re-accumulation rate after washout characterise the *withdrawal cost*
masked by v1's redose.

### 4.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `LOADING_DOSE (P35)` | 10  | µM | swept by Viability |
| `Age (P31)`          | 75  | (signal) | swept by Viability |
| `MAINT_DOSE (P36)`   | 0   | µM | unused (no redose) |
| `DOSE_INTERVAL (P37)`| 4300 | s | unused (no redose) |
| `pH (P29)`           | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 0 | µM | reset by `evt_load` then `evt_washout` |

**Events table:**

| id | trigger | target | expression |
|---|---|---|---|
| `evt_load`    | `t > 0.1`    | `CBD_extracellular (P1)` | `LOADING_DOSE (P35)` |
| `evt_washout` | `t > 5400`   | `CBD_extracellular (P1)` | `0` |

### 4.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] LOADING_DOSE` | `LOADING_DOSE.initial_marking` | 3, 10, 20  | 3 |
| `[param] Age`          | `Age.initial_marking`          | 65, 75, 85 | 3 |

**Cells:** 3 × 3 = **9**  •  **Total sims:** 9 × 30 = **270**

### 4.3 Headless equivalent (`sweep_config.P2.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v2.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "LOADING_DOSE.initial_marking", "values": [3, 10, 20]},
    {"type": "places", "path": "Age.initial_marking",          "values": [65, 75, 85]}
  ],
  "events": [
    {"id": "evt_load",    "trigger": "t > 0.1",  "assignments": {"CBD_extracellular": "LOADING_DOSE"}},
    {"id": "evt_washout", "trigger": "t > 5400", "assignments": {"CBD_extracellular": "0"}}
  ]
}
```

**Cost:** 3 × 3 = 9 conditions × 30 reps = **270 sims**.

---

## 5. Protocol P3 — Late rescue (post-onset window)

**Hypothesis.** Treatment started *after* inflammation onset still
recovers neuron health if begun before plaque crosses ~30. Establishes
the **therapeutic time window**.

> Requires the `RESCUE_DELAY` parameter place. If absent, replace each
> `RESCUE_DELAY` reference with a literal seconds value and run one
> `sweep_config.P3.<delay>.json` per delay level.

### 5.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `RESCUE_DELAY (P??)`  | 3600 | s  | swept by Viability (the protocol's headline axis) |
| `LOADING_DOSE (P35)`  | 10   | µM | held constant for P3 |
| `MAINT_DOSE (P36)`    | 3    | µM | held constant for P3 |
| `DOSE_INTERVAL (P37)` | 4300 | s  | held constant for P3 |
| `Age (P31)`           | 75   | (signal) | swept by Viability |
| `pH (P29)`            | 7.4  | (signal) | held constant |
| `CBD_extracellular (P1)` | 0  | µM | reset by `evt_rescue` |

**Events table:**

| id | trigger | target | expression |
|---|---|---|---|
| `evt_rescue` | `t > RESCUE_DELAY (P??)`                       | `CBD_extracellular (P1)` | `LOADING_DOSE (P35)` |
| `evt_maint`  | `t > RESCUE_DELAY (P??) + DOSE_INTERVAL (P37)` | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)` |

### 5.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] RESCUE_DELAY` | `RESCUE_DELAY.initial_marking` | 1800, 3600, 5400, 7200, 9000 | 5 |
| `[param] Age`          | `Age.initial_marking`          | 65, 75, 85                   | 3 |

**Cells:** 5 × 3 = **15**  •  **Total sims:** 15 × 30 = **450**

### 5.3 Headless equivalent (`sweep_config.P3.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v2.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "RESCUE_DELAY.initial_marking",   "values": [1800, 3600, 5400, 7200, 9000]},
    {"type": "places", "path": "LOADING_DOSE.initial_marking",   "values": [10]},
    {"type": "places", "path": "MAINT_DOSE.initial_marking",     "values": [3]},
    {"type": "places", "path": "DOSE_INTERVAL.initial_marking",  "values": [4300]},
    {"type": "places", "path": "Age.initial_marking",            "values": [65, 75, 85]}
  ],
  "events": [
    {"id": "evt_rescue", "trigger": "t > RESCUE_DELAY",                 "assignments": {"CBD_extracellular": "LOADING_DOSE"}},
    {"id": "evt_maint",  "trigger": "t > RESCUE_DELAY + DOSE_INTERVAL", "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}}
  ]
}
```

**Cost:** 5 × 1 × 1 × 1 × 3 = 15 conditions × 30 reps = **450 sims**.

---

## 6. Protocol P4 — Lock-in bifurcation map (fine dose scan, no events)

**Hypothesis.** A bistable boundary exists at Age 75 between
**clearing** and **locked** plaque trajectories. Map it.

### 6.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Age (P31)`           | 75  | (signal) | swept by Viability |
| `pH (P29)`            | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 3.0 | µM | **swept by Viability** (constant-exposure axis) |
| `LOADING_DOSE / MAINT_DOSE / DOSE_INTERVAL` | – | – | unused (no dose events in P4) |

**Events table:** *(none — constant exposure via `CBD_extracellular (P1).initial_marking`)*

### 6.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 60  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `CBD_extracellular`  | `CBD_extracellular.initial_marking` | 0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0 | 10 |
| `[param] Age`        | `Age.initial_marking`               | 65, 75, 85 | 3 |

> `CBD_extracellular` is *not* a parameter place in v2 (no `[param]`
> tag). To make it one, add `CBD_INIT (parameter place)` and a single
> seed event — see the note at the end of §6.

**Cells:** 10 × 3 = **30**  •  **Total sims:** 30 × 60 = **1800**

### 6.3 Headless equivalent (`sweep_config.P4.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v2.shy",
  "replicates": 60,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "CBD_extracellular.initial_marking",
     "values": [0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]},
    {"type": "places", "path": "Age.initial_marking", "values": [65, 75, 85]}
  ],
  "events": []
}
```

**Cost:** 10 × 3 = 30 conditions × 60 reps = **1800 sims**.

> If you want the sweep to vary a parameter place rather than the
> regular `CBD_extracellular`, replace the first dimension with
> `CBD_INIT.initial_marking` and add a single seed event
> `{"id": "evt_init", "trigger": "t > 0.1", "assignments": {"CBD_extracellular": "CBD_INIT"}}`.

---

## 7. Protocol P5 — Acute kinetic capture (high time-resolution)

**Hypothesis.** Cytokine and NF-κB transients in `[0, 1800] s` carry
the actual pharmacological signal that endpoint-only data drops.

### 7.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `LOADING_DOSE (P35)`  | 10  | µM | swept by Viability (incl. 0 µM control) |
| `Age (P31)`           | 75  | (signal) | swept by Viability |
| `MAINT_DOSE / DOSE_INTERVAL` | – | – | unused (single-bolus protocol) |
| `pH (P29)`            | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 0 | µM | reset by `evt_load` |

**Events table:**

| id | trigger | target | expression |
|---|---|---|---|
| `evt_load` | `t > 0.1` | `CBD_extracellular (P1)` | `LOADING_DOSE (P35)` |

### 7.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 3600 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] LOADING_DOSE` | `LOADING_DOSE.initial_marking` | 0, 3, 10 | 3 |
| `[param] Age`          | `Age.initial_marking`          | 65, 85   | 2 |

**Cells:** 3 × 2 = **6**  •  **Total sims:** 6 × 30 = **180**

### 7.3 Headless equivalent (`sweep_config.P5.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v2.shy",
  "replicates": 30,
  "duration": 3600,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "LOADING_DOSE.initial_marking", "values": [0, 3, 10]},
    {"type": "places", "path": "Age.initial_marking",          "values": [65, 85]}
  ],
  "events": [
    {"id": "evt_load", "trigger": "t > 0.1", "assignments": {"CBD_extracellular": "LOADING_DOSE"}}
  ]
}
```

**Cost:** 3 × 2 = 6 conditions × 30 reps = **180 sims**.

---

## 8. Total cost & run order

| Protocol | Conditions | Reps | Sims | Notes |
|---|---:|---:|---:|---|
| P1 | 27 | 30 | 810 | BID maintenance |
| P2 | 9  | 30 | 270 | Withdrawal cost |
| P3 | 15 | 30 | 450 | Therapeutic window |
| P4 | 30 | 60 | 1800 | Bifurcation map |
| P5 | 6  | 30 | 180 | Acute kinetics (short duration) |
| **Total** | **87** | – | **3510** | |

**Recommended order:** P5 → P2 → P3 → P1 → P4
(cheap kinetic sanity-check first; heavy bifurcation map last).

---

## 9. Dispatch (server-side, GPU)

```bash
# from repo root, after pushing the configs and running git pull on the server
for P in P5 P2 P3 P1 P4; do
  python -m shypn.cli.sweep \
    --project workspace/projects/canabidiol \
    --sweep   workspace/projects/canabidiol/sweep_config.${P}.json \
    --workers 4 --verbose
done
```

Outputs land at
`workspace/projects/canabidiol/experiments/results/run_<timestamp>/`
(symlinked to the HDD store on the GPU server; do **not** override
with `--output`).

---

## 10. Convention check (auto-enforced at save)

When the model is saved, a save-time validator emits warnings for any
place violating ALL_CAPS ⟺ `is_parameter_place`:

* `Parameter naming convention: place 'loading_dose' has is_parameter_place=True but name is not ALL_CAPS.`
* `Parameter naming convention: place 'MAINT_DOSE' looks like an ALL_CAPS parameter name … but is_parameter_place=False.`

Auto-IDs (`P1`, `P35`, …) and short single-word abbreviations (`ATP`,
`NADH`, `GTP`) are exempt. See
[`document_model._warn_parameter_naming_violations`](../../../../src/shypn/data/canvas/document_model.py).
