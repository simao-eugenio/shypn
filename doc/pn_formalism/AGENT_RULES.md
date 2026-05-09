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
- **2026-04-29**: Added §8 "Arc-type selection rules for modellers"
  after the Phase-0 4-day audit revealed silent regulatory deadlock
  in `canabidiol-phase-0.shy` caused by misuse of `signal_flow` on
  basal turnover transitions (T22 `Nrf2_degradation` preempted by
  T11 `ROS_releases_Nrf2` because both cycled through the same Ψ
  carrier P16 with `signal_flow` arcs, and T11 itself was disabled
  once ROS drained). Companion bug: catalysts (e.g. ROS oxidising
  Keap1) were attached via `normal` arcs and consumed.

---

## 8. Arc-type selection rules for modellers (STRICT, 2026-04-29)

The four arc types are not interchangeable. Picking the wrong type
either silently breaks mass balance, silently disables a transition
through `PreemptionCheck`, or silently consumes a catalyst. None of
these failure modes raises an error — the model loads, runs, and
produces wrong numbers.

### 8.1 Decision table

For every arc you draw, answer **two** questions: what is the
**physical role** of the source place in the reaction, and does
this transition need to be **gated by the upstream regulatory
cascade**?

| Physical role of source place                              | Cascade-gated? | Arc type        | Engine effect                                           |
|------------------------------------------------------------|----------------|-----------------|---------------------------------------------------------|
| **Substrate** (consumed, mass leaves)                      | no             | `normal`        | debits source by `weight × flow`                        |
| **Catalyst / regulator presence** (read but not consumed)  | no             | `test`          | requires `M(p) ≥ τ_t`; Δ = 0 on firing                  |
| **Inhibitor** (presence disables, **read but not consumed**) | no           | `inhibitor`     | `M(p) ≥ θ_eff ⇒ disabled`; **Δ = 0 on firing** (classical PN, Murata 1989). SHyPN extends only the *threshold evaluation* — `θ_eff` may be a runtime expression (e.g. `"4800 + 0.5 * ADP_pool"`). The `weight` attribute is irrelevant. |
| **Regulatory signal**, transition belongs to a hierarchy   | **yes**        | `signal_flow`   | debits source AND triggers `PreemptionCheck` on upstream signal producers |

Same table for output arcs:

| Physical role of target place                              | Arc type      |
|------------------------------------------------------------|---------------|
| Product (mass arrives)                                     | `normal`      |
| Regulatory signal *produced* into a downstream cascade     | `signal_flow` |
| (Test and inhibitor arcs are input-only)                   | —             |

### 8.2 The four canonical mistakes

#### M1 — Catalyst attached as `normal`

A catalyst is consumed every firing → species drains in seconds, the
transition starves itself, and downstream rates collapse to zero.
Symptoms: a reactant pool the modeller "knows" is catalytic goes to
zero almost immediately; numerical results look like the catalyst
was never there.

> **Rule M1.** If the species is biologically a catalyst, cofactor,
> enzyme, or signal that *triggers* the reaction without being
> stoichiometrically consumed, use `test`. Never `normal`.

#### M2 — Basal turnover/degradation attached as `signal_flow`

A degradation/turnover/clearance transition exists to drain a pool
unconditionally — proteasomal degradation, dilution, washout,
metabolism. Wiring its input arc as `signal_flow` opts the
transition into `PreemptionCheck`: the engine then disables it
whenever any upstream `signal_flow` producer of the same place is
itself disabled, which is almost always not what you want for a
basal sink.

> **Rule M2.** Basal turnover, degradation, and clearance
> transitions MUST use `normal` input arcs. They are not
> regulatory; they have no upstream cascade. Reserve `signal_flow`
> for transitions that genuinely participate in a layered signaling
> cascade.

#### M3 — Substrate attached as `test`

A test arc never debits — the transition appears to fire but mass
doesn't move. Symptoms: a substrate's pool grows or stays flat
despite the rate function being non-zero; downstream products
appear from "nowhere".

> **Rule M3.** Anything physically consumed by the reaction must be
> `normal` (or `signal_flow` only when the cascade gating is
> intentional).

#### M4 — Inhibitor attached as `normal` or `test`

Wiring an inhibitor as `normal` consumes it on every firing of a
reaction it is supposed to block. Wiring as `test` makes its
presence a *requirement* (opposite of intent).

> **Rule M4.** Negative regulation = `inhibitor`. The arc fires only
> while `M(p) < threshold`.

### 8.3 When to use `signal_flow`

Use `signal_flow` only when **all** of the following are true:

1. The source place is a designated regulatory signal (`is_signal_place=true`,
   non-spatial — i.e. a ⬡ carrier, **not** ◇).
2. You want this transition's enablement to be gated by the
   `PreemptionCheck`: i.e. it should **not** fire while the upstream
   producer of that signal is itself disabled.
3. Mass transfer of the signal token is biologically meaningful in
   the cascade (the signal "is consumed" by being read into the
   downstream layer).

If any of (1)–(3) is false, use `test` (sense without consuming) or
`normal` (consume without cascade gating). When in doubt, use `test`
for a regulator and `normal` for a substrate; promote to
`signal_flow` only when you explicitly want the cascade interlock.

### 8.4 The deadlock pattern to memorise

```
T_release : Keap1_Nrf2 + ROS  ─signal_flow→  Nrf2_free        (Φ depends on ROS)
T_turnover: Nrf2_free         ─signal_flow→  Keap1_Nrf2       (constant rate)
```

Both transitions touch the same Ψ carrier `Nrf2_free` via
`signal_flow`. As soon as `ROS → 0` drives `T_release` below its
enablement threshold, `T_turnover`'s `PreemptionCheck` fires (because
its only upstream signal producer is now disabled) and it freezes.
The cycle deadlocks at `Keap1_Nrf2 = 0, Nrf2_free = pool`.

**Fix.** `T_turnover` is basal degradation, not a signal. Its input
arc must be `normal`. After the fix, T_turnover runs unconditionally
and the cycle reaches its true steady state.

### 8.5 Modeller checklist for every transition

1. List each input place. For each, classify role
   (substrate / catalyst / inhibitor / regulatory-signal).
2. Pick arc type from §8.1.
3. If you chose `signal_flow`, justify all three conditions in §8.3
   in a comment in the model metadata or the audit script. If you
   cannot justify one, downgrade to `normal` or `test`.
4. List each output place. Almost always `normal`. Only use
   `signal_flow` when emitting into a downstream cascade with
   intentional preemption coordination.
5. Confirm catalysts use `test`, not `normal` (Rule M1).
6. Confirm degradation/turnover uses `normal` inputs, not
   `signal_flow` (Rule M2).

### 8.6 Audit support (planned)

The auditor will gain new codes (target: next commit):

| Code | Severity | Meaning                                                                                |
|------|----------|----------------------------------------------------------------------------------------|
| C13  | warning  | continuous transition with **only** `signal_flow` input arcs — deadlock risk via PreemptionCheck |
| C14  | warning  | place flagged as catalyst in metadata but attached via `normal` input arc (Rule M1 candidate) |
| C15  | info     | basal sink transition (single input, no output, name matches `*_degradation/_turnover/_clearance/_metabolism`) using `signal_flow` input — Rule M2 candidate |


---

## 9. Property scope discipline — object-net vs experiment-plan (STRICT, 2026-05-04)

A `.shy` carries two architecturally separate artifacts (see §1 of
`EXPERIMENT_PLAN_VS_OBJECT_NET.md`). **Every numeric / textual
property on every object lives in exactly ONE of them.** Cross-scope
duplication is the canonical source of label-vs-value drift,
preset-vs-▢ mismatch, and "wrong number quoted in the manuscript"
bugs (audited 2026-05-04 on `canabidiol-q1-testable.shy`).

### 9.1 Scope assignment (definitive)

**Object-net (intrinsic, reusable across runs):**

| Object   | Intrinsic property                                                                  |
|----------|-------------------------------------------------------------------------------------|
| ○ / ⬡    | `compartment_volume`, top-level `compartment`, `properties.thermodynamics.charge`, `properties.thermodynamics.n_protons`, `metadata.{kegg_id,formula,mw,gene_symbol,…}`, `metadata.hierarchy_layer` |
| transition | `transition_type`, `properties.rate_function` (the *form*), arc topology, `kinetic_metadata` (literature Km, Vmax, kcat) |
| arc      | `arc_type`, `weight` (stoichiometry), `michaelis_K`, `hill_n`, `suppression_epsilon` |

**Experiment plan (exogenous, per-run):**

| Object | Exogenous property                                                                    |
|--------|---------------------------------------------------------------------------------------|
| ▢      | `initial_marking` (TEMPERATURE, PH, AGE, DOSE, INTERVAL, DISEASE_SEVERITY, …)         |
| ◇      | `initial_marking` (Q10 factor, pH factor, age factor — written by events from ▢)      |
| events | All assignments (`evt_apply_thermodynamics`, `evt_install_disease`, `evt_dose_*`)     |
| top-level `thermodynamic_settings` | `temperature`, `ph`, `ionic_strength`, `tolerance`, `enable_validation`, `preset` — **the THERMODYNAMIC REFERENCE STATE** for ΔG° tabulation; not the physiological state |
| top-level `view_state`             | UI defaults for this dispatch                                            |
| top-level `metadata`               | Run-level provenance                                                     |

### 9.2 The single rule

> A quantity must live in exactly **ONE** scope. If the same concept
> appears in both, the **experiment-plan scope is canonical** and the
> object-net scope must be **derived** from it (via event at $t=0$),
> not duplicated.

Corollaries:

- **▢ TEMPERATURE / PH / AGE are PHYSIOLOGICAL** (e.g. 310.15 K, 7.4).
- **`thermodynamic_settings.temperature / .ph` are the REFERENCE state**
  used to derive ΔG° lookups (e.g. 298.15 K, 7.0; preset
  `biochemical_standard`).
- These are **two different concepts** — keep both, but document the
  distinction in the model README. They MUST NOT be confused as
  redundant copies of the same number.
- The **▢ → ◇ → Φ** bridge (via `evt_apply_thermodynamics`) is what
  converts physiological ▢ into kinetic factors (Q10, pH factor) that
  multiply rates derived at the reference state.

### 9.3 Forbidden patterns (enforced at audit)

| # | Pattern                                                              | Why wrong                                                |
|---|----------------------------------------------------------------------|----------------------------------------------------------|
| P1 | `properties.thermodynamics` block on a ▢ parameter place             | ▢ has no chemistry (no charge, no n_protons). Noise.    |
| P2 | `properties.thermodynamics.conditions` on ○/⬡ equal verbatim to global `thermodynamic_settings` | Redundant; clutter; mask local overrides |
| P3 | Place `label` text disagreeing with `initial_marking` value          | Manuscript-misquote trap                                 |
| P4 | Top-level `compartment` on some places, `metadata.compartment` on others (split) | Loader reads top-level only; routing inconsistent |
| P5 | `kinetic_metadata` populated on some transitions, absent on others, with no documented rationale | Half-filled metadata is worse than uniformly absent |
| P6 | Sweep config overriding an object-net property (rate_function string, arc weight, kinetic_metadata) | Object-net is reusable invariant; sweep targets experiment-plan only |
| P7 | Rate function Φ referencing a ▢ parameter place by name              | Object-net must not depend on experiment metadata; route through ◇ instead |
| P8 | Event RHS computing kinetics from a non-target ○/⬡ state place       | Pattern A violation (see §3); audit code C12             |

### 9.4 Cleanup workflow (when audit finds violations)

1. **Decide the canonical scope** for each concept. Default: protocol
   metadata → ▢; reference thermodynamics → top-level
   `thermodynamic_settings`; chemistry per molecule → metabolite ○ only.
2. **Strip wrong-scope copies** (P1, P2 above).
3. **Regenerate labels from values** (P3) — never edit a label without
   editing the value through it.
4. **Promote `metadata.compartment` → top-level `compartment`** uniformly
   (P4).
5. **Either populate `kinetic_metadata` for all parameterised
   transitions, or drop the field everywhere** (P5).
6. **Sweep configs target only experiment-plan keys** (P6).
7. **Remove ▢ names from Φ; route via ◇ + `evt_apply_thermodynamics`**
   (P7).
8. **Refactor offending events to Pattern A** (P8) — see §3.

### 9.5 Audit codes (planned)

| Code | Severity | Meaning                                                                |
|------|----------|------------------------------------------------------------------------|
| C16  | warning  | ▢ parameter place carries a `properties.thermodynamics` block (P1)     |
| C17  | info     | ○/⬡ has `properties.thermodynamics.conditions` equal to global (P2)    |
| C18  | warning  | place `label` numeric token disagrees with `initial_marking` (P3)      |
| C19  | warning  | inconsistent compartment-field location across places (P4)             |
| C20  | info     | partial `kinetic_metadata` coverage on transitions (P5)                |
