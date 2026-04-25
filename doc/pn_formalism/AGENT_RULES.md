# Agent rules — formalism + events refactoring (canonical)

> **Read this file at the start of every agent session that touches**
> **transition rates Φ, events, or place-type flags.**
>
> This file is git-tracked under `doc/pn_formalism/` so it survives
> across machines (client + server) and across agent memory resets.
> The repo memory tier (`/memories/repo/`) keeps a pointer back here.
> The copilot instructions (`.github/copilot-instructions.md`) cite
> the rules in condensed form; this file is the single source of
> truth that the auditor implements.

Authoritative sibling docs:
- `EXPERIMENT_PLAN_VS_OBJECT_NET.md` — long-form derivation, §1–§8.
- `SHPN_FORMALISM_CANONICAL.md` — the 13-tuple Bio-PN definition.

Authoritative implementation:
- Auditor: `workspace/projects/canabidiol/scripts/audit_formalism_compliance.py`
- Engine enforcement:
  - `src/shypn/engine/transition_behavior.py` — PreemptionCheck skips ◇.
  - `src/shypn/topology/behavioral/exploration/transition_partitioner.py` — POSet skips ◇.
  - `src/shypn/netobjs/place.py` — `_is_spatial_carrier()` + diamond glyph.
  - `src/shypn/helpers/place_prop_dialog_loader.py` — mutual exclusivity, ◇ skips F_s auto-conversion.

---

## 1. Four place carriers (mutually exclusive per concept)

| Glyph | Flag(s)                                        | Read by Φ?      | In cascade? | Role                                |
|-------|------------------------------------------------|-----------------|-------------|-------------------------------------|
| ○     | (none — regular place)                         | yes (with arc)  | n/a         | biology, mass-balanced              |
| ⬡     | `is_signal_place=true`, `signal_type ≠ SPATIAL`| yes             | **YES**     | biological commitment / hierarchy   |
| ◇     | `is_signal_place=true`, `signal_type = SPATIAL`| yes             | **NO**      | event-fed kinetic / env scalar      |
| ▢     | `is_parameter_place=true`                      | **NO**          | NO          | protocol metadata, event-only       |

**Mutual exclusivity** (one concept ↔ one carrier) is enforced in the
place-properties dialog and at audit time (codes C8 + dialog
`_apply_changes` / `_save_parameter_properties`).

---

## 2. Three legal sensing channels into Φ

| Channel | Source carrier | Mechanism                              |
|---------|----------------|----------------------------------------|
| F (consumptive)   | ○         | substrate / product arc                |
| F_s (consumptive, hierarchical) | ⬡ | signal flow arc, gates cascade |
| F_t (non-consumptive)           | ○ ⬡ | test arc, presence sensing      |
| Φ (remote sensing)              | ○ ⬡ ◇ | name appears in rate string     |

Φ may **never** read ▢. Audit code **C1** flags any ▢ name appearing
in any Φ.

For ○ remote sensing, the place must have ≥1 arc of any type (audit
**C9**); ⬡ and ◇ are exempt because Ψ membership itself declares
"informational state, designed to be read by many transitions".

---

## 3. Pattern A discipline — events are NOT ODE integrators

Events are **discrete protocol interventions**. They may:

- read parameter places ▢,
- set / add / remove tokens at scheduled times.

The **only** legal RHS in an event assignment `target := expr` is one
whose Name references are a subset of:

```
{target} ∪ {parameter places ▢}
```

| Form                                                  | Verdict   | Why                                 |
|-------------------------------------------------------|-----------|-------------------------------------|
| `Aβ_Monomer := Aβ_Monomer + Disease_Severity * 0.125` | ✓ legal   | self-additive, ▢ on RHS             |
| `CBD_extracellular := CBD_extracellular + LOADING_DOSE` | ✓ legal | self-additive, ▢ on RHS             |
| `target := constant`                                  | ✓ legal   | trivial set                         |
| `target := f(▢, …▢)`                                  | ✓ legal   | parameter-only RHS                  |
| `Aβ_Monomer := Aβ_Monomer * NFkB_p65 * 0.01`          | ✗ C12     | RHS reads ○ NFkB_p65 (state)        |
| `k_polym_eff := k_polym_eff + dt * (Aβ - Aβ_eq)`      | ✗ C12     | Euler integrator in disguise        |
| `NFkB_p65 := max(NFkB_p65, IκB)`                      | ✗ C12     | RHS reads non-target state place    |

**If a quantity drifts during a run, it must drift because transitions
fire.** Move the algebra into Φ; if the quantity needs its own
dynamics, give it producer/consumer transitions.

### Consequence for the spatial signal place ◇

The bridge `▢ + event → ◇ → Φ` is legal **only**:

- at $t = 0$ (install protocol kinetic constants), or
- at a discrete protocol step ("heater switches on at $t = 600\,\text{s}$").

For time-varying environmental quantities, promote to a regular ○
with its own producing/consuming transitions; put the temperature /
pH / Arrhenius algebra inside Φ:

```
T_polym.rate = k_base * exp(-Ea / (R * Temperature)) * Aβ²
                                    ↑ ○ Temperature, has arcs, evolves by topology
```

The event's role then reduces to setting `M₀(Temperature)` from a ▢
`Initial_Temperature` constant at $t = 0$.

---

## 4. Audit codes (run before every commit touching .shy / Φ / events)

Implemented in `workspace/projects/canabidiol/scripts/audit_formalism_compliance.py`.
Exit code 0 = compliant, 1 = at least one violation.

| Code | Severity | Meaning                                                                 |
|------|----------|-------------------------------------------------------------------------|
| C1   | error    | ▢ name appears in any Φ                                                 |
| C2   | error    | F / F_s / F_t arc touches ▢                                             |
| C3   | error    | ▢ listed in any transition's `signal_places`                            |
| C4   | error    | `is_environment_aware=True` anywhere                                    |
| C5   | error    | hard-coded env symbol in Φ (Q10, Temperature, pH, Age, DSev, …)         |
| C6   | info     | events that read ▢ — reported, never fails                              |
| C7   | error    | truly orphan place (no arcs, not in Φ, not ▢)                           |
| C8   | error    | semantic mirror — ▢ name shares stem with topology place                |
| C9   | error    | regular ○ referenced in Φ with zero arcs (signal places exempt)         |
| C10  | error    | ◇ has F_s arc (forbidden — ◇ excluded from cascade)                     |
| C11  | error    | ◇ neither read in Φ nor written by event (inert)                        |
| C12  | error    | event RHS references a non-target state place (Pattern A breach)        |

---

## 5. Workflow checklist for any agent edit

A session that edits Φ, events, place-type flags, or arc types MUST:

1. **Re-read this file** (`AGENT_RULES.md`) and
   `EXPERIMENT_PLAN_VS_OBJECT_NET.md` §5 if unsure of any rule.
2. **Make the edit** in the .shy file or the source.
3. **Run the auditor**:
   ```bash
   python3 workspace/projects/canabidiol/scripts/audit_formalism_compliance.py
   ```
4. **Land only when** the auditor reports `ALL MODELS COMPLIANT ✓`.
5. **Commit + push to `private`** + `ssh remote-gpu git pull
   --ff-only` so client and server stay in lockstep.

Repo-memory pointer: `/memories/repo/formalism_carriers_and_audit.md`
holds a one-screen digest with a back-pointer to this file. The
git-tracked copy here is the source of truth; the memory file is just
an auto-loaded breadcrumb for new agent sessions.

---

## 6. Analysis eligibility (Viability / structural / liveness)

Three orthogonal layers of variation exist in a shypn experiment.
Each lives at a different layer; **only the dynamic layer is visible
to structural / Viability analysis**.

| Layer                               | Mechanism            | What varies                              | Where it lives          | Visible to Viability? |
|-------------------------------------|----------------------|------------------------------------------|-------------------------|-----------------------|
| Protocol (inter-trajectory)         | sweep                | ▢ `initial_marking`, event field values  | `sweep_config.json`     | ✗ — collapses to a constant per run |
| Discrete intervention (intra)       | events               | ○ ⬡ ◇ markings at scheduled $t$          | experiment plan (Φ_e)   | ✗ — discontinuous jumps, not flow   |
| Dynamic execution (intra)           | transitions firing   | ○ ⬡ markings via $F$, $F_s$              | object-net $G_E ∪ G_s$  | ✓ — the *only* analyzed layer       |

**Rule.** Viability / P-T-invariant / liveness / reachability analysis
operates over $G_E ∪ G_s$ only. ▢ has no rows in the incidence matrix
(no $F$, $F_s$, $F_t$ arcs by construction) — it is **structurally
invisible** to the dynamic subnet. ◇ also lacks $F_s$ arcs and is
excluded from the cascade hierarchy, but it does appear in Φ; treat
its inclusion in Viability as a soft case (panel currently omits it
via the same locality test that omits ▢).

**Sweep nuance.** Sweeps do vary ▢ across conditions, but the
variation occurs *between* trajectories, not *during* one. Inside any
single trajectory the ▢ is a constant (or is read once by an event to
seed biology). There is therefore no dynamic for Viability to analyze
on ▢. Highlighting ▢ in the Viability Places table would be a
category error — it would advertise structural coupling that does not
exist.

UI consequence — Viability panel filter (`viability_panel.py`):

- Include: places with ≥1 incident $F$, $F_s$, or $F_t$ arc inside
  the active locality (i.e. members of $G_E ∪ G_s$).
- Exclude: `is_parameter_place=True` (▢) — protocol layer.
- Exclude: places referenced only by events with no arcs — protocol
  layer (event-only sinks/sources are interventions, not dynamics).
- Stale flags such as `is_compartment_place` MUST NOT pull a place
  back into the table; the locality + arc test is canonical.

---

## 7. Change log

- **2026-04-25**: Initial canonical version. Captures the
  four-carrier model (○ ⬡ ◇ ▢), Pattern A discipline, and audit
  codes C1–C12. Created in response to the spatial signal place
  split + Pattern A discipline refinement landed in commits
  `2480d5bd`, `76ac57b3`, `7165f059`, `567c76da`.
- **2026-04-25**: Added §6 "Analysis eligibility" codifying the
  three-layer variation model (protocol / event / dynamic) and the
  rule that Viability operates over $G_E ∪ G_s$ only. Triggered by
  the P6 sweep field-test where the panel auto-selected
  Temperature/pH/Age via a stale `is_compartment_place` flag —
  resolved by panel filter cleanup + `cbd_ad_neuroprotection_v3_p7.shy`
  Pattern A migration (4 ◇ spatial signal places +
  `evt_apply_thermodynamics`).
