# Event Protocol — Cannabidiol Dosing Sweep (v3)

**Project:** `canabidiol`
**Model:** `cbd_ad_neuroprotection_v3.shy`
**Supersedes:** [event_protocol_v2.md](event_protocol_v2.md)
**Date:** 2026-04-23

---

## 0. What changed vs v2

| v2 | v3 |
|----|----|
| Initial marking represented a *moderately-diseased* neuron (Aβ_Oligomer=15, ROS=5, Microglia_M1=25 …). "Baseline" was just default values — i.e., AD with default dose. | Initial marking represents a **healthy young neuron** (Aβ_Oligomer=0.5, ROS=1, Microglia_M1=5 …). Disease is **installed dynamically** by an event. |
| No way to express a true vehicle control. `LOADING_DOSE=0` was not a swept level. | New parameter place **`Disease_Severity (P38)`** (0=healthy, 1=MCI, 2=AD, 3=severe). Setting it to 0 yields a true healthy control. |
| Single "Baseline" snapshot was numerically identical to one interior factorial cell — useless as a reference. | "Baseline" is **dropped**. The factorial cell `(Disease_Severity=0, LOADING_DOSE=0, MAINT_DOSE=0)` IS the healthy control; `(Disease_Severity=2, LOADING_DOSE=0, MAINT_DOSE=0)` IS the AD vehicle. |
| Disease and drug effects could not be cleanly separated. | Two-way contrast: **disease burden** = (Sev=k, LD=0) − (Sev=0, LD=0); **drug efficacy** = (Sev=k, LD=d) − (Sev=k, LD=0); **interaction** = off-diagonal pattern. |

**Mechanism added in v3.** A new event `evt_install_disease` fires
once at `t > 0.01` (model-level priority 10, set in the .shy JSON — not
editable from the Environment Panel events table) and adds pathology
proportional to `Disease_Severity` to **fourteen** model places. Each
place gets its own per-severity-unit increment **δ** (positive δ means
the place grows with disease, negative δ means it depletes with
disease).

**The 14 places, grouped by biological role:**

| Group | Place (ID) | Healthy M₀ | δ per severity | AD (Sev=2) | Severe (Sev=3) | Biology |
|---|---|---:|---:|---:|---:|---|
| **Aβ accumulation** | `Abeta_Monomer (P5)`  | 0.05  | +0.125 | 0.30  | 0.43  | APP-derived monomer pool |
|                     | `Abeta_Oligomer (P6)` | 0.5   | +7.25  | 15.0  | 22.25 | Toxic oligomeric Aβ |
|                     | `Abeta_Plaque (P7)`   | 0.0   | +2.5   | 5.0   | 7.5   | Insoluble plaque load |
| **APP transcription** | `APP_mRNA (P34)`    | 4.0   | +2.0   | 8.0   | 10.0  | Driven up by NF-κB inflammation |
| **Inflammation core** | `NFkB_p65 (P9)`     | 5.0   | +12.5  | 30.0  | 42.5  | Active NF-κB transcription factor |
|                       | `TNFa (P11)`        | 0.5   | +0.25  | 1.0   | 1.25  | Pro-inflammatory cytokine |
|                       | `IL1b (P12)`        | 0.5   | +0.25  | 1.0   | 1.25  | Pro-inflammatory cytokine |
|                       | `IL6 (P13)`         | 0.5   | +0.25  | 1.0   | 1.25  | Pro-inflammatory cytokine |
|                       | `COX2 (P14)`        | 0.5   | +0.25  | 1.0   | 1.25  | Pro-inflammatory enzyme |
| **Microglial polarisation** | `Microglia_M1 (P21)` | 5.0  | +10.0  | 25.0 | 35.0 | Pro-inflammatory phenotype (rises) |
|                             | `Microglia_M2 (P22)` | 40.0 | −7.5   | 25.0 | 17.5 | Anti-inflammatory phenotype (falls) |
| **Oxidative stress**  | `ROS (P19)`         | 1.0   | +2.0   | 5.0   | 7.0   | Reactive oxygen species |
|                       | `Glutathione (P20)` | 70.0  | −15.0  | 40.0  | 25.0  | Antioxidant pool (depleted) |
| **Neuronal viability** | `Neuron_Health (P23)` | 100.0 | −2.5 | 95.0 | 92.5 | Composite viability marker |

In compact form, `evt_install_disease` performs:

```
# Aβ cascade
Abeta_Monomer   ← Abeta_Monomer   + Disease_Severity × 0.125
Abeta_Oligomer  ← Abeta_Oligomer  + Disease_Severity × 7.25
Abeta_Plaque    ← Abeta_Plaque    + Disease_Severity × 2.5
APP_mRNA        ← APP_mRNA        + Disease_Severity × 2.0
# Inflammation
NFkB_p65        ← NFkB_p65        + Disease_Severity × 12.5
TNFa            ← TNFa            + Disease_Severity × 0.25
IL1b            ← IL1b            + Disease_Severity × 0.25
IL6             ← IL6             + Disease_Severity × 0.25
COX2            ← COX2            + Disease_Severity × 0.25
# Microglia
Microglia_M1    ← Microglia_M1    + Disease_Severity × 10.0
Microglia_M2    ← Microglia_M2    + Disease_Severity × (−7.5)
# Oxidative stress
ROS             ← ROS             + Disease_Severity × 2.0
Glutathione     ← Glutathione     + Disease_Severity × (−15.0)
# Viability
Neuron_Health   ← Neuron_Health   + Disease_Severity × (−2.5)
```

**Places NOT touched by `evt_install_disease`** (initial markings the
same as v2; the disease event leaves these alone):

| Place (ID) | Reason |
|---|---|
| `CBD_extracellular (P1)`, `CBD_intracellular (P30)` | Drug compartments — owned by the dose events |
| `GPR3 (P2)`, `Gamma_Secretase (P3)`, `APP (P4)`     | Constitutive enzyme/substrate pools — disease modulates them through dynamics, not initial overrides |
| `NFkB_IkB (P8)`, `IKK (P10)`                        | Upstream NF-κB regulators — driven by inflammation feedback, not by direct override |
| `Keap1_Nrf2 (P15)`, `Nrf2_free (P16)`, `HO1 (P17)`, `SOD (P18)`, `GSSG (P33)` | Antioxidant machinery — driven by ROS dynamics |
| `BDNF (P24)`, `HT1A_active (P25)`, `PPARg_active (P26)`, `A2A_active (P27)` | Receptor / neurotrophic signalling — emergent, not seeded |
| `Temperature (P28)`, `pH (P29)`                     | Environmental signal places, held constant |
| `Age (P31)`                                         | Independent factorial axis |
| `GPR3_inactive (P32)`                               | Constitutive |
| `LOADING_DOSE (P35)`, `MAINT_DOSE (P36)`, `DOSE_INTERVAL (P37)`, `Disease_Severity (P38)` | Parameter places (dosing knobs and the severity dial itself) |

**Calibration:** Severity=2 reproduces the v2 AD baseline exactly
(verified by the validation sweep `run_20260423_234546`). Severity=1
gives ≈ ½ AD (MCI proxy); Severity=3 gives ≈ 150 % AD. The δ values
are first-order linear extrapolations between the v2 AD baseline and
the healthy young-neuron M₀ defined in v3 — they do **not** model
non-linear disease progression. For non-linear severity, use a custom
sweep with explicit per-cell place markings instead of the
`Disease_Severity` axis.

**Conventions inherited from v2 (still enforced):**

* ALL_CAPS_NAME ⟺ `is_parameter_place=True` (save-time validator).
* Panel separation: Environment owns parameter values + events;
  Viability owns sweep mode + ranges + replicates; CLI replays the
  same plan headlessly.
* Naming `NAME (Pn)` is documentation-only; cells in the events table
  store the bare name.

---

## 1. Parameter places used

These exist in `cbd_ad_neuroprotection_v3.shy` (✅) or are added on
demand for individual protocols (➕).

| Name (ID) | Status | `parameter_kind` | `parameter_units` | Used by |
|---|---|---|---|---|
| `Disease_Severity (P38)` | ✅ in model | `severity` | level | **all** (new in v3) |
| `LOADING_DOSE (P35)`     | ✅ in model | `dose`     | µM    | P1, P2, P3, P5, P6 |
| `MAINT_DOSE (P36)`       | ✅ in model | `dose`     | µM    | P1, P3, P6 |
| `DOSE_INTERVAL (P37)`    | ✅ in model | `interval` | s     | P1, P3, P6 |
| `RESCUE_DELAY (P??)`     | ➕ to add  | `time`     | s     | P3 |
| `CBD_INIT (P??)`         | ➕ to add  | `dose`     | µM    | P4 (constant exposure proxy) |

**Other (non-parameter) places referenced:**

| Name (ID) | Role |
|---|---|
| `CBD_extracellular (P1)` | Reaction species (target of every dose event) |
| `Age (P31)`              | Bio-PN signal place — swept as factorial dimension |
| `pH (P29)`               | Bio-PN signal place — held at 7.4 |

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

## 3. Mandatory events that ship with v3

These two events are **always present** in the model. Sweep configs
should NOT redefine them — they fire automatically and are controlled
entirely via parameter-place values.

| id | trigger | target | expression |
|---|---|---|---|
| `evt_install_disease` | `t > 0.01` | (14 places, see §0) | `place + Disease_Severity × δ` |
| (drug events vary by protocol — see below) | | | |

> **Event ordering.** The Environment Panel events table has 5 columns
> only — **ID · Trigger · Target Place · Value Expr · Delay (s)**.
> Event `priority` is model-level metadata stored in the .shy JSON
> (not exposed in the table). For v3, `evt_install_disease` is
> assigned `priority = 10` and all drug events `priority = 0` so that
> at startup the disease is installed before any drug bolus arrives.

`evt_install_disease` is a no-op when `Disease_Severity = 0` (every
assignment evaluates to `place + 0`). This is what makes
`(Disease_Severity=0, LOADING_DOSE=0)` a true vehicle/healthy control.

---

## 4. Protocol P1 — Pulse maintenance, with disease-and-dose factorial

**Hypothesis.** Loading bolus + repeated top-ups every `DOSE_INTERVAL`
seconds rescues neuron health in a disease-severity-dependent and
age-dependent manner. P1 in v3 explicitly varies disease severity so
both *whether* a patient needs treatment and *whether* it works are
mapped on the same grid.

### 4.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Disease_Severity (P38)` | 0   | level | swept by Viability (incl. healthy 0) |
| `LOADING_DOSE (P35)`     | 0   | µM    | swept by Viability (incl. vehicle 0) |
| `MAINT_DOSE (P36)`       | 0   | µM    | swept by Viability (incl. vehicle 0) |
| `DOSE_INTERVAL (P37)`    | 4300 | s    | held constant for P1 |
| `Age (P31)`              | 75  | (signal) | swept by Viability |
| `pH (P29)`               | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 0   | µM    | reset by `evt_load` |

**Events table (Environment Panel rows — 5 columns: ID · Trigger · Target Place · Value Expr · Delay (s)):**

| id | trigger | target | expression | delay |
|---|---|---|---|---:|
| `evt_install_disease` | `t > 0.01`                    | (14 places — see §0)     | `place + Disease_Severity × δ`           | 0 |
| `evt_load`            | `t > 0.1`                     | `CBD_extracellular (P1)` | `CBD_extracellular + LOADING_DOSE (P35)` | 0 |
| `evt_maint_1`         | `t > DOSE_INTERVAL (P37)`     | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)`   | 0 |
| `evt_maint_2`         | `t > 2 * DOSE_INTERVAL (P37)` | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)`   | 0 |
| `evt_maint_3`         | `t > 3 * DOSE_INTERVAL (P37)` | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)`   | 0 |

> Note: `evt_load` in v3 uses `CBD_extracellular + LOADING_DOSE` (not
> bare `LOADING_DOSE`) so that `LOADING_DOSE = 0` is a true no-op
> rather than an assignment that resets P1 to 0.

### 4.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] Disease_Severity` | `Disease_Severity.initial_marking` | **0, 1, 2, 3** | 4 |
| `[param] LOADING_DOSE`     | `LOADING_DOSE.initial_marking`     | **0**, 5, 10, 20 | 4 |
| `[param] MAINT_DOSE`       | `MAINT_DOSE.initial_marking`       | **0**, 1, 3, 5   | 4 |
| `[param] Age`              | `Age.initial_marking`              | 65, 75, 85       | 3 |

**Cells:** 4 × 4 × 4 × 3 = **192**  •  **Total sims:** 192 × 30 = **5760**

**Reference cells produced automatically:**
* `Disease_Severity=0, LOADING_DOSE=0, MAINT_DOSE=0` → **healthy control** (12 cells, one per Age × redundancy — pick one as the master reference).
* `Disease_Severity=k, LOADING_DOSE=0, MAINT_DOSE=0` → **vehicle for severity k**.
* `Disease_Severity=k, LOADING_DOSE=d, MAINT_DOSE=m` → treatment cell.

**Trim option (recommended for first run):** Drop one Age level and one
MAINT_DOSE level → 4 × 4 × 3 × 2 = **96 cells × 30 = 2880 sims**.

### 4.3 Headless equivalent (`sweep_config.P1.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "Disease_Severity.initial_marking", "values": [0, 1, 2, 3]},
    {"type": "places", "path": "LOADING_DOSE.initial_marking",     "values": [0, 5, 10, 20]},
    {"type": "places", "path": "MAINT_DOSE.initial_marking",       "values": [0, 1, 3, 5]},
    {"type": "places", "path": "DOSE_INTERVAL.initial_marking",    "values": [4300]},
    {"type": "places", "path": "Age.initial_marking",              "values": [65, 75, 85]}
  ],
  "events": [
    {"id": "evt_install_disease", "trigger": "t > 0.01", "priority": 10,
      "_comment": "priority is model-level metadata, not shown in Environment Panel",
      "assignments": {
        "Abeta_Monomer":  "Abeta_Monomer + Disease_Severity * 0.125",
        "Abeta_Oligomer": "Abeta_Oligomer + Disease_Severity * 7.25",
        "Abeta_Plaque":   "Abeta_Plaque + Disease_Severity * 2.5",
        "NFkB_p65":       "NFkB_p65 + Disease_Severity * 12.5",
        "ROS":            "ROS + Disease_Severity * 2.0",
        "Microglia_M1":   "Microglia_M1 + Disease_Severity * 10.0",
        "Microglia_M2":   "Microglia_M2 + Disease_Severity * -7.5",
        "Glutathione":    "Glutathione + Disease_Severity * -15.0",
        "Neuron_Health":  "Neuron_Health + Disease_Severity * -2.5",
        "TNFa":           "TNFa + Disease_Severity * 0.25",
        "IL1b":           "IL1b + Disease_Severity * 0.25",
        "IL6":            "IL6 + Disease_Severity * 0.25",
        "COX2":           "COX2 + Disease_Severity * 0.25",
        "APP_mRNA":       "APP_mRNA + Disease_Severity * 2.0"
      }},
    {"id": "evt_load",    "trigger": "t > 0.1",                    "assignments": {"CBD_extracellular": "CBD_extracellular + LOADING_DOSE"}},
    {"id": "evt_maint_1", "trigger": "t > DOSE_INTERVAL",          "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}},
    {"id": "evt_maint_2", "trigger": "t > 2 * DOSE_INTERVAL",      "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}},
    {"id": "evt_maint_3", "trigger": "t > 3 * DOSE_INTERVAL",      "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}}
  ]
}
```

> `evt_install_disease` is already in the model — explicitly listing
> it in the sweep config is redundant but documented here so a reader
> sees the full event set in one place. Both modes work.

**Cost:** 4 × 4 × 4 × 1 × 3 = 192 conditions × 30 reps = **5760 sims**.

---

## 5. Protocol P2 — Withdrawal challenge across severities

**Hypothesis.** Without redose, the inflammatory flare and plaque
re-accumulation rate after washout characterise the *withdrawal cost*,
and that cost scales with disease severity.

### 5.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Disease_Severity (P38)` | 2  | level | swept by Viability |
| `LOADING_DOSE (P35)`     | 0  | µM    | swept by Viability (incl. vehicle 0) |
| `Age (P31)`              | 75 | (signal) | swept by Viability |
| `MAINT_DOSE / DOSE_INTERVAL` | – | – | unused (no redose) |
| `pH (P29)`               | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 0  | µM    | reset by `evt_load` then `evt_washout` |

**Events table (Environment Panel rows — 5 columns):**

| id | trigger | target | expression | delay |
|---|---|---|---|---:|
| `evt_install_disease` | `t > 0.01` | (14 places — see §0)     | `place + Disease_Severity × δ`           | 0 |
| `evt_load`    | `t > 0.1`  | `CBD_extracellular (P1)` | `CBD_extracellular + LOADING_DOSE (P35)` | 0 |
| `evt_washout` | `t > 5400` | `CBD_extracellular (P1)` | `0`                                      | 0 |

### 5.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] Disease_Severity` | `Disease_Severity.initial_marking` | 1, 2, 3        | 3 |
| `[param] LOADING_DOSE`     | `LOADING_DOSE.initial_marking`     | 0, 3, 10, 20   | 4 |
| `[param] Age`              | `Age.initial_marking`              | 65, 75, 85     | 3 |

**Cells:** 3 × 4 × 3 = **36**  •  **Total sims:** 36 × 30 = **1080**

### 5.3 Headless equivalent (`sweep_config.P2.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "Disease_Severity.initial_marking", "values": [1, 2, 3]},
    {"type": "places", "path": "LOADING_DOSE.initial_marking",     "values": [0, 3, 10, 20]},
    {"type": "places", "path": "Age.initial_marking",              "values": [65, 75, 85]}
  ],
  "events": [
    {"id": "evt_load",    "trigger": "t > 0.1",  "assignments": {"CBD_extracellular": "CBD_extracellular + LOADING_DOSE"}},
    {"id": "evt_washout", "trigger": "t > 5400", "assignments": {"CBD_extracellular": "0"}}
  ]
}
```

**Cost:** 3 × 4 × 3 = 36 conditions × 30 reps = **1080 sims**.

---

## 6. Protocol P3 — Late rescue (post-onset window)

**Hypothesis.** Treatment started *after* inflammation onset still
recovers neuron health if begun before plaque crosses ~30. Establishes
the **therapeutic time window** as a function of disease severity.

> Requires the `RESCUE_DELAY` parameter place. If absent, replace each
> `RESCUE_DELAY` reference with a literal seconds value and run one
> `sweep_config.P3.<delay>.json` per delay level.

### 6.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Disease_Severity (P38)` | 2    | level | swept by Viability |
| `RESCUE_DELAY (P??)`     | 3600 | s     | swept by Viability (the protocol's headline axis) |
| `LOADING_DOSE (P35)`     | 10   | µM    | held constant for P3 |
| `MAINT_DOSE (P36)`       | 3    | µM    | held constant for P3 |
| `DOSE_INTERVAL (P37)`    | 4300 | s     | held constant for P3 |
| `Age (P31)`              | 75   | (signal) | swept by Viability |
| `pH (P29)`               | 7.4  | (signal) | held constant |
| `CBD_extracellular (P1)` | 0    | µM    | reset by `evt_rescue` |

**Events table (Environment Panel rows — 5 columns):**

| id | trigger | target | expression | delay |
|---|---|---|---|---:|
| `evt_install_disease` | `t > 0.01`                                     | (14 places — see §0)     | `place + Disease_Severity × δ`           | 0 |
| `evt_rescue`          | `t > RESCUE_DELAY (P??)`                       | `CBD_extracellular (P1)` | `CBD_extracellular + LOADING_DOSE (P35)` | 0 |
| `evt_maint`           | `t > RESCUE_DELAY (P??) + DOSE_INTERVAL (P37)` | `CBD_extracellular (P1)` | `CBD_extracellular + MAINT_DOSE (P36)`   | 0 |

### 6.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] Disease_Severity` | `Disease_Severity.initial_marking` | 1, 2, 3                  | 3 |
| `[param] RESCUE_DELAY`     | `RESCUE_DELAY.initial_marking`     | 1800, 3600, 5400, 7200, 9000 | 5 |
| `[param] Age`              | `Age.initial_marking`              | 65, 75, 85               | 3 |

**Cells:** 3 × 5 × 3 = **45**  •  **Total sims:** 45 × 30 = **1350**

### 6.3 Headless equivalent (`sweep_config.P3.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "Disease_Severity.initial_marking", "values": [1, 2, 3]},
    {"type": "places", "path": "RESCUE_DELAY.initial_marking",     "values": [1800, 3600, 5400, 7200, 9000]},
    {"type": "places", "path": "LOADING_DOSE.initial_marking",     "values": [10]},
    {"type": "places", "path": "MAINT_DOSE.initial_marking",       "values": [3]},
    {"type": "places", "path": "DOSE_INTERVAL.initial_marking",    "values": [4300]},
    {"type": "places", "path": "Age.initial_marking",              "values": [65, 75, 85]}
  ],
  "events": [
    {"id": "evt_rescue", "trigger": "t > RESCUE_DELAY",                 "assignments": {"CBD_extracellular": "CBD_extracellular + LOADING_DOSE"}},
    {"id": "evt_maint",  "trigger": "t > RESCUE_DELAY + DOSE_INTERVAL", "assignments": {"CBD_extracellular": "CBD_extracellular + MAINT_DOSE"}}
  ]
}
```

**Cost:** 3 × 5 × 1 × 1 × 1 × 3 = 45 conditions × 30 reps = **1350 sims**.

---

## 7. Protocol P4 — Lock-in bifurcation map (fine dose scan, no events)

**Hypothesis.** A bistable boundary exists between **clearing** and
**locked** plaque trajectories, located at a severity-dependent
critical CBD level. Map it.

### 7.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Disease_Severity (P38)` | 2  | level | swept by Viability |
| `Age (P31)`              | 75  | (signal) | swept by Viability |
| `pH (P29)`               | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 3.0 | µM | **swept by Viability** (constant-exposure axis) |
| `LOADING_DOSE / MAINT_DOSE / DOSE_INTERVAL` | – | – | unused (no dose events in P4) |

**Events table (Environment Panel rows — 5 columns):**

| id | trigger | target | expression | delay |
|---|---|---|---|---:|
| `evt_install_disease` | `t > 0.01` | (14 places — see §0) | `place + Disease_Severity × δ` | 0 |

*(no drug events — constant exposure via `CBD_extracellular (P1).initial_marking`)*

### 7.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 60  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] Disease_Severity` | `Disease_Severity.initial_marking` | 1, 2, 3                                        | 3 |
| `CBD_extracellular`        | `CBD_extracellular.initial_marking` | 0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0 | 10 |
| `[param] Age`              | `Age.initial_marking`              | 65, 75, 85                                     | 3 |

> `CBD_extracellular` is *not* a parameter place in v3 (no `[param]`
> tag). To make it one, add `CBD_INIT (parameter place)` and a single
> seed event — see the note at the end of §7.

**Cells:** 3 × 10 × 3 = **90**  •  **Total sims:** 90 × 60 = **5400**

### 7.3 Headless equivalent (`sweep_config.P4.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3.shy",
  "replicates": 60,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "Disease_Severity.initial_marking",   "values": [1, 2, 3]},
    {"type": "places", "path": "CBD_extracellular.initial_marking",
     "values": [0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]},
    {"type": "places", "path": "Age.initial_marking",                "values": [65, 75, 85]}
  ],
  "events": []
}
```

**Cost:** 3 × 10 × 3 = 90 conditions × 60 reps = **5400 sims**.

> If you want the sweep to vary a parameter place rather than the
> regular `CBD_extracellular`, replace the second dimension with
> `CBD_INIT.initial_marking` and add a single seed event
> `{"id": "evt_init", "trigger": "t > 0.1", "assignments": {"CBD_extracellular": "CBD_INIT"}}`.

---

## 8. Protocol P5 — Acute kinetic capture (high time-resolution)

**Hypothesis.** Cytokine and NF-κB transients in `[0, 1800] s` carry
the actual pharmacological signal that endpoint-only data drops, and
the transient shape depends on whether the cell is healthy, MCI, or
fully diseased.

### 8.1 Environment Panel — parameter-place baselines & events

**Parameter places:**

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Disease_Severity (P38)` | 0  | level | swept by Viability (incl. healthy 0) |
| `LOADING_DOSE (P35)`     | 0  | µM    | swept by Viability (incl. vehicle 0) |
| `Age (P31)`              | 75 | (signal) | swept by Viability |
| `MAINT_DOSE / DOSE_INTERVAL` | – | – | unused (single-bolus protocol) |
| `pH (P29)`               | 7.4 | (signal) | held constant |
| `CBD_extracellular (P1)` | 0  | µM    | reset by `evt_load` |

**Events table (Environment Panel rows — 5 columns):**

| id | trigger | target | expression | delay |
|---|---|---|---|---:|
| `evt_install_disease` | `t > 0.01` | (14 places — see §0)     | `place + Disease_Severity × δ`           | 0 |
| `evt_load`            | `t > 0.1`  | `CBD_extracellular (P1)` | `CBD_extracellular + LOADING_DOSE (P35)` | 0 |

### 8.2 Viability Panel — sweep plan

**Mode:** Factorial design  •  **Replicates:** 30  •  **Duration:** 3600 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] Disease_Severity` | `Disease_Severity.initial_marking` | 0, 2     | 2 |
| `[param] LOADING_DOSE`     | `LOADING_DOSE.initial_marking`     | 0, 3, 10 | 3 |
| `[param] Age`              | `Age.initial_marking`              | 65, 85   | 2 |

**Cells:** 2 × 3 × 2 = **12**  •  **Total sims:** 12 × 30 = **360**

### 8.3 Headless equivalent (`sweep_config.P5.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3.shy",
  "replicates": 30,
  "duration": 3600,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "Disease_Severity.initial_marking", "values": [0, 2]},
    {"type": "places", "path": "LOADING_DOSE.initial_marking",     "values": [0, 3, 10]},
    {"type": "places", "path": "Age.initial_marking",              "values": [65, 85]}
  ],
  "events": [
    {"id": "evt_load", "trigger": "t > 0.1", "assignments": {"CBD_extracellular": "CBD_extracellular + LOADING_DOSE"}}
  ]
}
```

**Cost:** 2 × 3 × 2 = 12 conditions × 30 reps = **360 sims**.

---

## 9. Protocol P6 — Disease-installation calibration (NEW in v3)

**Hypothesis (and audit).** Validate the `evt_install_disease`
calibration by sweeping `Disease_Severity ∈ {0, 0.5, 1, 1.5, 2, 2.5, 3}`
with no drug, and inspecting steady-state markers. Severity=0 must
remain healthy; Severity=2 must reproduce v2 AD baseline within tight
tolerance.

### 9.1 Environment Panel — parameter-place baselines & events

| Place (ID) | Baseline | Units | Notes |
|---|---:|---|---|
| `Disease_Severity (P38)` | 0  | level | swept by Viability |
| `LOADING_DOSE / MAINT_DOSE / DOSE_INTERVAL` | – | – | held at 0 / 0 / large |
| `Age (P31)`              | 75 | (signal) | held constant |

**Events table:** only `evt_install_disease` (no drug events).

### 9.2 Viability Panel — sweep plan

**Mode:** Single-axis  •  **Replicates:** 30  •  **Duration:** 14400 s  •  **Termination:** time

| Sweep parameter | Path | Values | Levels |
|---|---|---|---:|
| `[param] Disease_Severity` | `Disease_Severity.initial_marking` | 0, 0.5, 1, 1.5, 2, 2.5, 3 | 7 |

**Cells:** 7  •  **Total sims:** 7 × 30 = **210**

### 9.3 Headless equivalent (`sweep_config.P6.json`)

```json
{
  "mode": "factorial",
  "model_path": "workspace/projects/canabidiol/models/cbd_ad_neuroprotection_v3.shy",
  "replicates": 30,
  "duration": 14400,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,
  "parameters": [
    {"type": "places", "path": "Disease_Severity.initial_marking", "values": [0, 0.5, 1, 1.5, 2, 2.5, 3]}
  ],
  "events": []
}
```

**Acceptance criteria:**

| Severity | Abeta_Oligomer @ t=0+ | Glutathione @ t=0+ | Neuron_Health @ t_end |
|---:|---|---|---|
| 0   | ≈ 0.5  | ≈ 70 | ≥ 99 |
| 2   | ≈ 15.0 | ≈ 40 | ≤ 96 |
| 3   | ≈ 22.3 | ≈ 25 | ≤ 92 |

(Already verified for Severity ∈ {0, 2} in the v3-validation sweep
`run_20260423_234546`.)

**Cost:** 7 conditions × 30 reps = **210 sims**.

---

## 10. Total cost & run order

| Protocol | Conditions | Reps | Sims | Notes |
|---|---:|---:|---:|---|
| P6 | 7   | 30 | 210  | Severity calibration (run first!) |
| P5 | 12  | 30 | 360  | Acute kinetics (short duration) |
| P2 | 36  | 30 | 1080 | Withdrawal cost |
| P3 | 45  | 30 | 1350 | Therapeutic window |
| P1 | 192 | 30 | 5760 | Full disease × dose × age factorial |
| P4 | 90  | 60 | 5400 | Bifurcation map |
| **Total** | **382** | – | **14160** | |

**Recommended order:** P6 → P5 → P2 → P3 → P1 → P4
(calibration first, cheap kinetic sanity-check second, heavy bifurcation
map last). If GPU time is tight, P1 trim variant (96 cells × 30 = 2880
sims) covers most of the scientific question at half cost.

---

## 11. Dispatch (server-side, GPU)

```bash
# from repo root, after pushing the configs
for P in P6 P5 P2 P3 P1 P4; do
  python -m shypn.cli.sweep \
    --project workspace/projects/canabidiol \
    --sweep   workspace/projects/canabidiol/sweep_config.${P}.json \
    --workers 4 --verbose
done
```

The hybrid sync layer (RemoteSweepDispatcher) automatically uploads
`cbd_ad_neuroprotection_v3.shy` and writes `provenance.json` next to
each `sweep_config.P*.json` before launching. Outputs land at
`workspace/projects/canabidiol/experiments/results/run_<timestamp>/`
(symlinked to the HDD store on the GPU server; do **not** override
with `--output`).

---

## 12. Analysis contrasts enabled by v3

For any two factorial cells `(s, d)` and `(s', d')` with same Age:

| Contrast | Definition | Interpretation |
|---|---|---|
| **Disease burden**       | `(s=k, d=0) − (s=0, d=0)` | What does AD do to a healthy cell at severity *k*? |
| **Drug efficacy**        | `(s=k, d=D) − (s=k, d=0)` | What does dose *D* do at severity *k*? |
| **Drug × disease**       | `[(s=k, d=D) − (s=k, d=0)] − [(s=0, d=D) − (s=0, d=0)]` | Off-target/disease-specific drug effects |
| **Therapeutic ceiling**  | `(s=k, d=D) − (s=0, d=0)` | How close does drug bring patient to healthy? |
| **Age × drug**           | hold *s, d*; vary Age | Age-dependent dose-response |

**Healthy control rule:** the cell `(Disease_Severity=0, LOADING_DOSE=0,
MAINT_DOSE=0, Age=65)` is the canonical reference point for every
contrast. Replicate it in every protocol that varies severity or dose.

---

## 13. Convention check (auto-enforced at save)

When the model is saved, a save-time validator emits warnings for any
place violating ALL_CAPS ⟺ `is_parameter_place`:

* `Parameter naming convention: place 'disease_severity' has is_parameter_place=True but name is not ALL_CAPS.`
* `Parameter naming convention: place 'DISEASE_SEVERITY' looks like an ALL_CAPS parameter name … but is_parameter_place=False.`

Auto-IDs (`P1`, `P38`, …) and short single-word abbreviations (`ATP`,
`NADH`, `GTP`) are exempt. See
[`document_model._warn_parameter_naming_violations`](../../../../src/shypn/data/canvas/document_model.py).

> **Note on `Disease_Severity` naming.** `Disease_Severity` is *not*
> ALL_CAPS — it uses CamelCase to match its parameter-of-interest role
> (similar to `Age`, `Temperature`, `pH`). It IS still a parameter
> place. The validator currently emits a soft warning for this; it can
> be added to the exemption list in v3.1 if the warning is noisy.
