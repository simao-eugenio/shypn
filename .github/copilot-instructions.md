# SHyPN — workspace instructions for AI agents

These rules apply to **every** Copilot/agent session in this workspace
(local dev box and remote GPU server). The git repo is shared between
both sides, so any agent that follows these rules produces identical
filesystem layouts on both machines.

## Canonical per-project layout (STRICT)

For every project under `workspace/projects/<project_name>/`:

| Path                                              | Purpose                                                                |
|---------------------------------------------------|------------------------------------------------------------------------|
| `workspace/projects/<name>/models/`               | `.shy` model files (versioned)                                         |
| `workspace/projects/<name>/experiments/results/`  | **All** sweep / simulation outputs (`run_YYYYMMDD_HHMMSS/` dirs)       |
| `workspace/projects/<name>/scripts/`              | **All** analysis & auxiliary scripts (server-side or client-side)      |
| `workspace/projects/<name>/figures/`              | Generated plots, manuscript figures                                    |
| `workspace/projects/<name>/manuscript/`           | LaTeX / markdown for the write-up                                      |
| `workspace/projects/<name>/metadata/`             | Curated reference data, experimental constants, citations              |
| `workspace/projects/<name>/docs/`                 | Project-specific notes, design docs                                    |
| `workspace/projects/<name>/sweep_config.json`     | Sweep dispatch configuration                                           |

The path is **derived from the opened project**. The CLI computes
`output_dir = <project>/experiments/results/` automatically — agents
must never override this with a custom location unless explicitly
asked.

### Rules

1. **Sweep results MUST go to `<project>/experiments/results/`.**
   - Default CLI invocation:
     ```
     python -m shypn.cli.sweep \
         --project workspace/projects/<name> \
         --sweep   workspace/projects/<name>/sweep_config.json \
         --workers 4 --verbose
     ```
     The CLI resolves the output dir to `<project>/experiments/results/`
     automatically. **Never pass `--output` unless the user explicitly
     asks for a custom location.**
   - On the **remote GPU server**, `<project>/experiments/results/` is
     a **symlink** to the HDD store using the same project name:
     ```
     workspace/projects/<name>/experiments/results
         → /home/simao/data/results/<name>/
     ```
     The agent never sees the HDD path — it always writes to the
     in-tree path; the kernel resolves the symlink. SSD is preserved
     for source code, models, and small artefacts.
   - Do **not** write sweep output to `~/data/...`, `/tmp/...`,
     `<project>/results/` (deprecated short form), workspace root, or
     any path outside `<project>/experiments/results/`.

2. **Analysis & auxiliary scripts MUST go to `<project>/scripts/`.**
   - Includes server-side analysis (dose-response summarisers,
     trajectory inspectors), client-side helpers, model-patching
     scripts, one-off CLI utilities **specific to a project**.
   - Do **not** drop project scripts into `/tmp/`, the workspace root,
     `dev/`, `archive/`, or `tools/`.
   - If a script is genuinely *cross-project* (a generic tool), it
     belongs in `tools/` or `scripts/` at the repo root and must accept
     the target project path as an argument.

3. **Server symlink convention (one-time operator setup per project).**
   When a new project is created, the operator runs once on the server:
   ```bash
   PROJ=<name>
   mkdir -p /home/simao/data/results/$PROJ
   mkdir -p ~/shypn/workspace/projects/$PROJ/experiments
   ln -sfn /home/simao/data/results/$PROJ \
           ~/shypn/workspace/projects/$PROJ/experiments/results
   ```
   The agent never creates this symlink — it just writes to
   `<project>/experiments/results/` and the kernel resolves it.
   Local (client) machine has no symlink: results land directly on the
   project directory and stay small (used for inspection / plotting).

4. **Never inline-overwrite the canonical model file from a script.**
   Patching scripts in `<project>/scripts/` either save a new versioned
   file (`model_v2.shy`) or perform an in-memory dispatch only.

## Git workflow (recap)

- `private` remote → `git@github.com:simao-eugenio/shypn-dev.git`
- `public`  remote → `git@github.com:simao-eugenio/shypn.git`
- Active branch: `Usability-and-enhancements`
- Server alias: `remote-gpu` → `simao@150.162.232.36`, repo at `~/shypn/`
- Server venv: `~/shypn/.venv/` (CuPy 14.0.1, CUDA 12.9, RTX 5060 Ti)
- **Code sync (engine, scripts, configs)**: still operator-driven —
  commit → `git push private` → SSH `git pull private --ff-only`.
- **Model sync (`.shy` files)**: handled automatically by
  `RemoteSweepDispatcher` (hybrid model — see next section). Agents
  must NOT manually `scp` `.shy` files unless the dispatcher path
  is genuinely unavailable.

## Programmatic `.shy` patching — property scope rules (STRICT)

When editing `.shy` files outside the GUI (multi_replace, jq, scripts),
agents MUST respect the **loader scope** for every field. The loaders
in `src/shypn/netobjs/{place,transition,arc,signal_flow_arc}.py` and
`src/shypn/data/canvas/document_model.py` decide where a JSON key is
read from. Writing to the wrong scope is a silent no-op — the file
saves cleanly, the next save round-trips, and the engine ignores it.

### Loader-derived scope table (audited 2026-04-28 from `*.from_dict()`)

#### Transition (`transition.py::Transition.from_dict`)

| Field                                                                   | Read from                  | Notes                                                                 |
|-------------------------------------------------------------------------|----------------------------|-----------------------------------------------------------------------|
| `id`, `name`, `x`, `y`, `width`, `height`, `label`, `horizontal`        | top-level **only**         | constructor args                                                      |
| `enabled`, `fill_color`, `border_color`, `border_width`                 | top-level **only**         |                                                                       |
| `transition_type`, `priority`, `firing_policy`, `guard`                 | top-level **only**         |                                                                       |
| `is_source`, `is_sink`                                                  | top-level **only**         |                                                                       |
| `earliest_time`, `latest_time` (TPN window)                             | top-level **only**         |                                                                       |
| `signal_places`, `is_environment_aware`, `module_id`, `compartment`     | top-level **only**         |                                                                       |
| `kinetic_metadata`, `metadata`                                          | top-level **only**         |                                                                       |
| `adaptive_filter`, `volume_threshold`, `prefer_continuous`              | top-level **then** `properties` | top-level wins; properties is legacy fallback                  |
| **`rate_function`**                                                     | **`properties` only**      | top-level `rate_function` migrated **iff** `properties.rate_function` absent; once present, top-level edits are ignored |
| `rate_forward`, `rate_reverse`                                          | **`properties` only**      | same migration rule as `rate_function`                                |
| `rate` (deprecated numeric)                                             | top-level → migrated to `properties.rate_function` | only if no `rate_function` exists                |
| `formula`                                                               | top-level **only**         | legacy                                                                |

#### Place (`place.py::Place.from_dict`)

| Field                                                                              | Read from                  | Notes                                                |
|------------------------------------------------------------------------------------|----------------------------|------------------------------------------------------|
| `id`, `name`, `x`, `y`, `radius`, `label`                                          | top-level **only**         |                                                      |
| `initial_marking` (or legacy `marking`)                                            | top-level **only**         | **see `tokens` vs `initial_marking` policy below** — `tokens` in a saved file is a corruption signature, NEVER a value source |
| `is_catalyst`, `is_signal_place`, `is_energy_place`                                | top-level **only**         |                                                      |
| `is_compartment_place`, `is_regulatory_place`                                      | top-level **only**         |                                                      |
| `is_parameter_place`, `parameter_kind`, `parameter_units`                          | top-level **only**         |                                                      |
| `capacity`, `border_color`, `border_width`                                         | top-level **only**         |                                                      |
| `diffusion_coefficient`, `gradient_vector`, `neighbor_compartments`,`spatial_position` | top-level **only**     |                                                      |
| `boundary_type`                                                                    | top-level **only**         |                                                      |
| `compartment`, `metadata`                                                          | top-level **only**         |                                                      |
| `signal_type`                                                                      | top-level **then** `properties` | top-level wins                                  |
| `compartment_volume`                                                               | top-level **then** `properties` | top-level wins                                  |
| `properties` (passthrough dict for thermodynamic / custom data)                    | `properties` **only**      | not interpreted by the loader; engine reads ad-hoc   |

#### Arc (`arc.py::Arc.from_dict`)

| Field                                                                              | Read from                  | Notes                                                |
|------------------------------------------------------------------------------------|----------------------------|------------------------------------------------------|
| `id`, `name`, `arc_type`                                                           | top-level **only**         | `arc_type` selects the **subclass** (TestArc, SignalFlowArc, …) |
| `source_id`, `target_id`, `source_type`, `target_type`                             | top-level **only**         | `*_type` inferred from ID prefix if missing          |
| `weight`, `threshold`, `color`, `width`, `control_points`                          | top-level **only**         |                                                      |
| `properties` dict on arcs                                                          | **NOT READ by loader**     | the loader never deserializes `arc["properties"]`. Edits there are ignored at load. The engine's *runtime* fallback chain `kind ?? properties.kind ?? arc_type` is irrelevant once `arc_type` selects the right subclass. |

##### SignalFlowArc / CurvedSignalFlowArc additional fields

| Field                                                                              | Read from                  | Notes                                                |
|------------------------------------------------------------------------------------|----------------------------|------------------------------------------------------|
| `michaelis_K`, `hill_n`, `suppression_epsilon` (Γ tuple)                           | top-level **only**         | default 0, 1, 0                                      |
| `activation_energy`, `reference_temperature` (Arrhenius)                           | top-level **only**         | default 0, 298.15                                    |

#### DocumentModel (`document_model.py::DocumentModel.from_dict`)

| Field                                                                              | Read from                  | Notes                                                |
|------------------------------------------------------------------------------------|----------------------------|------------------------------------------------------|
| `places`, `transitions`, `arcs`, `modules`, `events`                               | top-level **only**         | lists at root                                        |
| `view_state`, `thermodynamic_settings`, `compound_mappings`, `metadata`            | top-level **only**         |                                                      |

### `tokens` vs `initial_marking` policy on places (STRICT)

Recurring trap (audited 2026-04-30, run_20260430_154220 zero-variance
sweep): a programmatic patch wrote `place["tokens"] = X` thinking it
would change the basal value. The loader read `initial_marking` (still
0), the engine started M_0 at 0, and the entire MAINT_DOSE sweep was a
silent no-op despite Layer-D provenance reporting the override applied.

Canonical policy:

* **`initial_marking`** is the **only** marking field the loader reads
  to populate $M_0$. It is the **basal value of the object-net** at
  design time, the static reference of the model.
* **`tokens`** is **transient runtime state** — the live value at a
  place during a session. It is used by interactive editing to poke
  values mid-run. **It is NEVER persisted to a `.shy` file.**
* On save (`Place.to_dict`), `tokens` is dropped. If
  `tokens != initial_marking` the writer logs a WARNING (the GUI
  surfaces this divergence pre-save via a Promote/Discard/Cancel
  dialog).
* On load (`Place.from_dict`), the presence of a `tokens` key with
  `tokens != initial_marking` is the **signature of a wrong-scope
  programmatic patch** (legacy or corrupted file). The loader uses
  `initial_marking` and logs a WARNING; in-memory `place.tokens` is
  reconciled to `place.initial_marking`.
* **Programmatic writers MUST use the canonical helper** —
  `shypn.netobjs.patch.set_place_value(model, name_or_id, value)` —
  which writes top-level `initial_marking`, mirrors `marking`, and
  strips any stale `tokens` key. **Do NOT write `place["tokens"] = X`
  in jq scripts, multi_replace, or anywhere else.**
* GUI flow: when the modeller wants to persist a runtime change, the
  pre-save dialog promotes `initial_marking := tokens` (with explicit
  consent — never silent). This is the *only* legal path for
  runtime → basal promotion.

Quick patch idiom:
```python
from shypn.netobjs.patch import patch_shy_file
patch_shy_file(
    "workspace/projects/<proj>/models/<file>.shy",
    {"LOADING_DOSE": 10.0, "MAINT_DOSE": 5.0},
)
# .shy.bak written, file rewritten with initial_marking set, tokens stripped
```

### Decision rule for any patch

Before editing field `F` on object `O`:

1. **Look up `F` in the table above.** If unlisted, grep `from_dict()`
   for the source class — *do not guess*.
2. **Apply at the loader's read scope.** Mirror to the alternate scope
   only when the table's "Notes" column says it's a fallback (e.g.
   `signal_type` should be set top-level; properties mirror is optional).
3. **Run the roundtrip assertion** below before saving.
4. **Never write to a scope the loader ignores** (e.g.
   `arc["properties"]`, `transition["rate_function"]` when
   `properties.rate_function` exists). These are silent no-ops.

### Boilerplate validation snippet (mandatory in every patch script)

```python
# After json.dumps and write, re-read and assert at the loader's read scope.
m2 = json.loads(path.read_text())

# 1. Rate-function patches (properties-only)
t = next(t for t in m2['transitions'] if t['name'] == NAME)
assert t['properties']['rate_function'] == NEW_RATE, \
    f"rate_function did not land in properties on {NAME}"

# 2. Arc retyping (top-level + clear properties.kind)
a = next(a for a in m2['arcs'] if a['id'] == ARC_ID)
assert a['arc_type'] == NEW_TYPE
assert a.get('properties', {}).get('kind') in (None, NEW_TYPE), \
    f"stale properties.kind on arc {ARC_ID} disagrees with arc_type"

# 3. New transition added (must have id starting 'T', properties dict)
new_t = next(t for t in m2['transitions'] if t['id'] == NEW_TID)
assert new_t['transition_type'] in ('continuous', 'stochastic', 'immediate', 'timed', 'adaptive')
if new_t['transition_type'] in ('continuous', 'adaptive'):
    assert new_t['properties'].get('rate_function'), \
        "continuous/adaptive transition needs properties.rate_function"

# 4. New arc added (top-level fields complete; do NOT add properties)
new_a = next(a for a in m2['arcs'] if a['id'] == NEW_AID)
for k in ('id', 'arc_type', 'source_id', 'target_id', 'weight'):
    assert k in new_a, f"new arc missing top-level {k}"
```

### Operational rules

- **`color` is GUI-only but identifies arc class on the canvas.** Update
  it together with `arc_type`:
  - `normal` → `[0.0, 0.0, 0.0]` (black)
  - `test` → `[0.0, 0.0, 1.0]` (blue)
  - `signal_flow` → `[0.7, 0.7, 0.7]` (light grey)
  - `inhibitor` → `[1.0, 0.0, 0.0]` (red)

- **The running engine reads from the in-memory model, not from disk.**
  After a programmatic patch the GUI/CLI must reload the model
  (File → Open, or restart `python src/shypn.py`) before the next
  simulation. Newer `.shy` mtime is **not** sufficient evidence — only
  changed firing counts / endpoint markers confirm the engine saw it.
  Agents that patch a model and request a re-run MUST tell the
  operator explicitly to reload the model first.

- **Skipping the roundtrip check is how the third-round P7 sweep ran
  against a stale model and reported zero T28 firings (2026-04-26),
  and how the v3_p9 GSH-floor patch silently produced ROS=17 instead
  of ROS=0 (2026-04-28).**

## Hybrid sync model (sweep dispatch)

As of April 2026 the dispatcher uses a **git + SCP hybrid**:

1. **Git remains canonical** for engine code, CLI, scripts, and
   long-term model history. Operators still commit/push/pull as before.
2. **SCP delivers the `.shy` model at every dispatch** — the dispatcher
   uploads `<project>/models/<file>.shy` to the matching server path
   right after `sweep_config.json`. This eliminates the "stale model"
   class of bugs where local edits silently no-op on the server.
3. **Provenance is captured per dispatch**:
   - `provenance.json` (sibling of `sweep_config.json`) records client
     + server git HEAD, branch, dirty flag, dirty paths, model sha256,
     config sha256, hostnames, dispatch timestamp.
   - The CLI sweep_runner snapshots `model_snapshot.shy` and
     `provenance.json` into each `run_<ts>/` directory, so every run
     is **independently reconstructible** regardless of subsequent
     edits or commits.
4. **Non-blocking warnings** (logged + emitted to UI as `⚠`) when:
   client tree dirty, server tree dirty, or client/server git HEADs
   diverge. These do not abort the dispatch — interactive science
   needs the escape hatch.

Run-dir contents (each `run_<ts>/`):
```
run_<ts>/
  config.json             ← exported sweep config used by the run
  model_snapshot.shy      ← exact bytes the worker loaded
  provenance.json         ← git context + sha256 of model + config
  summary.csv
  resource_usage.json
  condition_<name>/...    ← per-condition replicates + statistics
```

Agents debugging a "wrong result" sweep: always check `provenance.json`
first to confirm which model bytes / which engine SHAs actually ran.

## CLI cheatsheet

```bash
# Dispatch sweep (writes to <project>/experiments/results/run_<timestamp>/)
python -m shypn.cli.sweep \
    --project workspace/projects/<name> \
    --sweep   workspace/projects/<name>/sweep_config.json \
    --workers 4 --verbose

# Override output explicitly (RARE — only on user request)
python -m shypn.cli.sweep --project … --sweep … --output <abs-or-rel-path>
```

## Engine facts

- τ-leaping is the only stochastic engine (`use_tau_leaping=True` is
  baked in; the setter is a no-op).
- GPU path: `cupy` backend → `GPUHybridEngine` for ODE+stochastic models.
  Decline reasons logged at `WARNING` level by `replicate_runner.py`.
- Per-condition resource metrics land in `summary.csv` and
  `resource_usage.json` inside each run dir.

### Low-copy / sub-µM caveats (audit 2026-04-29)

Reference: [`doc/engine_stability_audit.md`](../doc/engine_stability_audit.md).
Seven failure modes (F1–F7) characterised; phased remediation S1–S7.
Phase A (S4 + S5 + S7) implemented in this commit; **S1, S2, S3, S6
NOT YET IMPLEMENTED** — agents must remain alert to these traps when
debugging low-copy results.

- **F1 — silent adaptive mode default:** an `adaptive` transition
  whose connected places lack `compartment_volume` falls back to
  `'continuous' if prefer_continuous else 'stochastic'` *without*
  raising. Always set `compartment_volume` on at least one input place
  for adaptive transitions, or prepare to be surprised by the default.
- **F3 — Poisson over-sampling is silently truncated.** When sampled
  firings exceed `floor((M − θ) / W)` they are clamped without error.
  S4 now exposes this:
  - `TauLeapingEngine.stats['requested_firings']`,
    `['truncated_firings']`, `['truncation_events']`.
  - Each replicate result dict carries `engine_stats` with
    `truncation_fraction = truncated / requested`.
  - Replicate-level warning fires when `truncation_fraction > 5 %`
    (`RuntimeWarning` in chunked path; printed line in main runner).
  - **A high truncation fraction is the canonical signature of low-copy
    bias.** Always check it before trusting a sweep at sub-µM
    concentrations.
- **F4 — Skellam reversibility detector is permissive.** Triggers on
  `' - '` substring + `kf_*` / `kr_*` naming. Rate strings of the form
  `k * (A - K_eq)` or `0.1 * X / (50 + X) - 0.05 * Y` will be
  misclassified as reversible and sampled with **2× variance**.
  Inspect the engine log for `Detected reversible:` lines on any
  unfamiliar model.
- **F5 — operator-split cascade lag.** Per `dt`: continuous flow →
  stochastic τ-leap → finalize. Continuous transitions read the
  *start-of-step* marking; stochastic transitions read the
  post-continuous marking. A `stochastic → continuous` chain therefore
  carries a **one-step lag per cascade level**. Invisible at high
  copy / fast equilibration; severe at low copy.
- **F7 — coarse data-collector decimation hides transients.** Default
  `recording_time_interval = 0.05 s`; a 4-day horizon retains <100
  recorded points. Use S5 to capture transients:
  `RecordingConfig(adaptive_tau_threshold=1e-3)` force-records every
  step whose engine `τ < 1 ms` (transient regime), while leaving
  coarse decimation intact during equilibrium phases.

When a sweep returns bit-identical downstream values across a
substrate gradient, suspect F1 + F5 + F7 *before* re-checking the
topology.

## Formalism (13-tuple Bio-PN, Simão 2025)

Reference: `manuscript/main_plos_one.tex`. Full audit:
`doc/FORMALISM_AUDIT_2025.md`. Latest reconciliation commit: `e20f4911`
("Formalism recon: PreemptionCheck + θ_eff fixes + JIT removal").

**Tuple:** `SPN = (P, T, F, W, M₀, Φ, C, F_t, Ψ, F_s, W_s, λ, θ)`

| Symbol | Meaning |
|--------|---------|
| `Ψ ⊆ P` | Signal places — modeller-designated, any place may be in Ψ. **Not** a structural type; `is_signal_place` is just a flag. |
| `F_s ⊆ (Ψ×T) ∪ (T×Ψ)` | Signal flow arcs — **consumptive** (like normal arcs). NOT read-only. |
| `F_t` | Test arcs — **non-consuming** presence check (Δ = 0 on firing). |
| `W_s` | Signal arc weight ∈ R⁺ (validated > 0 in `SignalFlowArc.__init__`). |
| `θ(t)` | Basin floor per transition (from Γ = (K, n, ε) tuple). |
| `τ_t` | Test arc sensing threshold (≥ 0, default 0). |

**Enablement (all four must hold):**
```
Enabled(t,M) ≡ NormalEnabled(t,M)
             ∧ TestEnabled(t,M)
             ∧ SignalEnabled(t,M)        — M(p_s) ≥ θ(t) + W_s((p_s,t))
             ∧ PreemptionCheck(t,M)      — single-layer, non-recursive
```

**Firing rule:** `M'(p) = M(p) + Δ_normal(p,t) + Δ_signal(p,t)` (test
arcs Δ = 0; **inhibitor arcs Δ = 0** — they are non-consuming
presence-absence checks per classical PN semantics; SHyPN extends only
the threshold *evaluation* — `θ` may be a runtime expression — never
the consumption semantics).

**Consumption semantics by arc type (single source of truth:
`Arc.consumes_tokens()`):**

| Arc type                                             | Consumes? | Override site                       |
|------------------------------------------------------|-----------|-------------------------------------|
| `normal`                                             | yes       | `Arc.consumes_tokens()` default     |
| `signal_flow` (incl. `curved_signal_flow_arc`)       | yes       | `SignalFlowArc.consumes_tokens()`   |
| `test`                                               | **no**    | `TestArc.consumes_tokens()`         |
| `inhibitor`                                          | **no**    | `InhibitorArc.consumes_tokens()`    |
| `curved_inhibitor_arc`                               | **no**    | `CurvedInhibitorArc.consumes_tokens()` |

The base `Arc.consumes_tokens()` ALSO recognises the string
`'inhibitor' in arc_type` so plain `Arc` instances loaded from a `.shy`
file (with `_arc_type_override = 'inhibitor'` /
`'curved_inhibitor_arc'`) yield the correct answer regardless of
subclass instantiation.

**Dual arc case** (signal place in both `F` and `F_s`):
```
M'(p_s) = M(p_s) − W((p_s,t)) − W_s((p_s,t)) + W((t,p_s)) + W_s((t,p_s))
```

### Implementation invariants — DO NOT regress

1. **θ_eff is a basin floor, not a per-firing cost.**
   - Burst of `n` firings requires `M(p_s) ≥ θ + n·W_s` (not `n·(θ + W_s)`).
   - τ-leaping `_calculate_max_firings`: `floor((M − θ) / W_s)`.
   - Continuous `_apply_flow_to_arcs`: `spendable = max(0, tokens − θ)`.

2. **Signal flow arcs consume tokens.** Do not skip them in consumption
   loops; do not document them as "read-only" or "without mass transfer".

3. **Test AND inhibitor arcs are non-consuming.** Both `arc_type='test'`
   and any `'inhibitor' in arc_type` (`inhibitor`,
   `curved_inhibitor_arc`, future variants) skip the consumption phase
   in every behavior (`fire()` / `_fire_transition_multiple()` /
   `_apply_flow_to_arcs()`). The single source of truth is
   `arc.consumes_tokens()` — call it; do not re-derive the rule
   inline. Also: τ-leaping `_calculate_max_firings` must skip
   non-consuming arcs (failing to skip a `curved_inhibitor_arc` whose
   source starts at 0 silently caps `max_firings = 0` and freezes the
   transition forever — bug audit 2026-05-08, bacillus_sporulation_v2).

4. **PreemptionCheck is single-layer and non-recursive.** Lives in
   `TransitionBehavior._check_preemption()`; called from every
   `can_fire()` (immediate, stochastic, continuous, timed). Vacuously
   true for Layer-0 transitions (no signal predecessors).

5. **Inhibitor arcs invert enablement, do NOT consume.** Predicate:
   `M(p) ≥ θ_eff(arc) → disabled`. SHyPN extension over classical PN:
   `θ_eff` may be a runtime expression
   (e.g. `"4800 + 0.5 * ADP_pool"`) rather than a static integer. Mass
   transfer on firing is **always zero** (Murata 1989, ISO/IEC 15909,
   GreatSPN, Snoopy convention). The `weight` attribute on an
   inhibitor arc is irrelevant to firing semantics — only `threshold`
   matters. Pinned by `tests/test_inhibitor_non_consumption.py` and
   `tests/test_classical_arc_semantics.py`.

6. **Reversible reactions** use Skellam sampler (Poisson(fwd) − Poisson(rev)).

7. **Arc-type selection is not interchangeable (modeller rule, see
   [`AGENT_RULES.md` §8](../doc/pn_formalism/AGENT_RULES.md)).**
   Picking the wrong arc type is silent — model loads, runs, gives
   wrong numbers. Decision table:

   | Source-place role                         | Cascade-gated? | Arc type      |
   |-------------------------------------------|----------------|---------------|
   | Substrate (consumed)                      | no             | `normal`      |
   | Catalyst / regulator presence (read only) | no             | `test`        |
   | Inhibitor (presence disables)             | no             | `inhibitor`   |
   | Regulatory signal in a hierarchy          | **yes**        | `signal_flow` |

   The four canonical mistakes:

   - **M1 — Catalyst as `normal`** → catalyst drains in seconds,
     transition starves itself. (e.g. ROS oxidising Keap1 must be
     `test`, never `normal`.)
   - **M2 — Basal turnover/degradation as `signal_flow`** → opts the
     sink into `PreemptionCheck`; engine silently disables it
     whenever any upstream signal producer of the same place is
     disabled, deadlocking the cycle. (e.g. `Nrf2_degradation` input
     arc must be `normal`, not `signal_flow`.)
   - **M3 — Substrate as `test`** → mass never leaves; downstream
     products materialise from nowhere.
   - **M4 — Inhibitor as `normal`/`test`** → consumes the inhibitor
     or makes its presence required (opposite of intent).

   Use `signal_flow` **only** when all three hold: (a) source is a ⬡
   signal place (`is_signal_place=true`, non-spatial), (b) the
   transition genuinely participates in a layered cascade and *should*
   be gated by `PreemptionCheck`, (c) mass transfer of the signal
   token is biologically meaningful. Otherwise pick `test` (sense
   without consuming) or `normal` (consume without cascade gating).

   The Phase-0 4-day audit (2026-04-29) traced an apparent "engine
   regression" to model-side M1 + M2 misuse on Keap1↔Nrf2 cycle —
   ROS-as-substrate (M1) drained ROS to 0; signal_flow on Nrf2
   turnover (M2) deadlocked the cycle via PreemptionCheck. **Always
   suspect arc-type selection before suspecting the engine.**

### Open gap

- **C1 — Multi-layer signal hierarchy:** the current single-layer
  `PreemptionCheck` is correct per the formalism but does not propagate
  beyond direct signal predecessors. Multi-layer enforcement requires
  the signal hierarchy layer-assignment infrastructure in the simulation
  context (not yet wired in).

## Experiment plan vs object-net (STRICT, 2026-04-25)

**READ FIRST every session that touches Φ / events / place-type flags:**
[`doc/pn_formalism/AGENT_RULES.md`](../doc/pn_formalism/AGENT_RULES.md)
— canonical four-carrier table (○ ⬡ ◇ ▢), Pattern A discipline,
audit codes C1–C12, and the workflow checklist.

Long-form derivation: [`doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md`](../doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md).
Per Simão 2025 §"Connected vs. Remote Information Access".

A `.shy` file bundles **two architecturally separate artifacts**:

1. **Object-net** — biology. Reusable. Dynamics emerge **entirely** from
   its own topology (places, transitions, arcs, intrinsic Φ over its
   own places).
2. **Experiment plan** — parameter places (`is_parameter_place=True`)
   + events. Run-specific. Encodes the protocol.

Parameter places (`Disease_Severity`, `Age`, `Temperature`, `pH`,
dose knobs) belong to **neither** $G_E = (P, T, F)$ nor
$G_s = (\Psi, F_s)$. They render as **rounded squares ▢** on the
canvas (vs. circle ○ for biological, hexagon ⬡ for signal).

### Forbidden patterns

- Parameter-place name appearing in any **object-net** rate function
  $\Phi$ (even though remote sensing is formally legal, biology rates
  must not depend on experiment metadata — breaks reusability).
- $F$, $F_s$, or $F_t$ arcs to/from parameter places.
- Parameter places listed in any object-net transition's `signal_places`.
- `is_environment_aware=True` flag and hard-coded `Q10` / `Temperature`
  / `pH` / `Age` / `DSev` symbols inside object-net rate strings —
  these are parameter-place backdoors.

### The only legal bridge: events

Events read parameter-place values and apply discrete interventions
(set marking, add/remove tokens) to biological places at scheduled
times. Example: `evt_install_disease` reads `DSev`, sets
`Aβ_Monomer := DSev * 5.0` once at $t=0$.

### Pattern A discipline — events MUST NOT do stateful algebra

Events are discrete protocol interventions, not a back-channel for
continuous dynamics. The only legal RHS in an event assignment
`target := expr` is one whose variable references are a subset of
`{target} ∪ {parameter places ▢}`. Examples:

```
✓  Aβ_Monomer        := Aβ_Monomer + Disease_Severity * 0.125
✓  CBD_extracellular := CBD_extracellular + LOADING_DOSE
✓  target            := f(▢, …▢)
✗  Aβ_Monomer        := Aβ_Monomer * NFkB_p65 * 0.01    (RHS reads ○)
✗  k_polym_eff       := k_polym_eff + dt * (Aβ - Aβ_eq) (Euler in disguise)
```

If a quantity changes during a run, it must change because
**transitions fire** — not because an event computes the change.
Audit code **C12** flags any event whose RHS references a non-target
state place (○, ⬡, ◇).

The "▢ + event → ◇ → Φ" bridge is legal **only** at $t=0$ or at a
discrete protocol step (the heater switches on); for time-varying
environmental quantities, promote to a regular ○ with its own
producing/consuming transitions and put the algebra inside Φ.

### One concept ↔ one carrier (no semantic mirroring)

A conceptual quantity (`Age`, `Temperature`, `pH`, `Disease_Severity`,
`k_polym_eff`, …) is represented by **exactly one** carrier. The four
legal carriers are mutually exclusive per concept:

1. **Pure parameter place ▢** — no arcs, never in any $\Phi$. Read by
   events only.
2. **Biological signal place ⬡** — in $\Psi$, has $F_s$ arcs,
   participates in `PreemptionCheck` and the layered hierarchy
   $\lambda$. May also be referenced in $\Phi$.
3. **Spatial signal place ◇** — in $\Psi$ but flagged
   `signal_type == SignalType.SPATIAL`. **No $F_s$ arcs.** Excluded
   from `PreemptionCheck` and from POSet layering. Read remotely by
   $\Phi$ from many transitions; written by events. The canonical home
   for event-fed kinetic / environmental scalars
   (`k_aggregation_eff`, `Temperature_factor`, `O2_level`, …).
4. **Remote-sensed regular place ○** — referenced by name in $\Phi$;
   has its own dynamics through $F$ arcs.

Forbidden: two carriers for the same concept (e.g. ⬡ `Age` *and* ▢
`Age_param`). Sweeping `X.initial_marking` of a topology-coupled
place is **legal** — initial-condition perturbation of $M_0$, not a
superposition violation. If you want to make a topology place
sweepable, sweep `initial_marking` directly; do not add a parameter
mirror.

### Remote sensing requires topology membership (regular places only)

A **regular ○** place's name may appear inside any $\Phi$ only if it
has at least one $F$, $F_s$, or $F_t$ arc, or is the producer/consumer
of the transition under that rate. A circle ○ with zero arcs that
appears in a rate string is a backdoor — fix by adding the missing
arc, or by reclassifying as ◇ (spatial signal) when the value is an
event-fed scalar shared by many rates, or as ▢ when it is read by
events only.

Signal places (⬡ and ◇) are exempt from the arc requirement: $\Psi$
membership itself declares "informational state, designed to be read
by many transitions." Forcing a $F_t$ arc per reader to a single hub
would create visual hairballs without adding semantics.

Canonical bridge for protocol-driven kinetics — **▢ + event → ◇ → $\Phi$**:

1. Keep protocol metadata as ▢ (e.g. `Temperature = 310.15 K`).
2. Add a spatial signal place ◇ for the kinetic scalar
   (e.g. `k_polym_eff`, `is_signal_place=true`,
   `signal_type=SPATIAL`, no $F_s$ arcs).
3. Reference the ◇ place — **not** the parameter — inside $\Phi$
   (e.g. `rate = k_polym_eff * Aβ_Monomer**2`).
4. Add an event that reads ▢ and writes ◇ at $t = 0$ (or on demand):
   `evt_apply_thermodynamics: k_polym_eff := k_base * Q10**((Temperature-310)/10)`.

The biology stays generic; only the event encodes the protocol. The
audit code **C9 — disconnected remote sensing** flags only **regular
○** places referenced in $\Phi$ with zero arcs; ⬡/◇ are exempt by
design.

### Diagnostic consequence

If the object-net does not exhibit a desired behaviour (e.g. healthy
fixed point at `NH=100` when initialised healthy with no events firing),
the **topology is wrong** — add sinks, clearance arcs, rebalance
reactions, or add the missing $F_s$ with the right $\theta$. **Never**
patch via parameter-place multipliers or rate-function shortcuts.

### Sweep ↔ model superposition rule

When a sweep targets an experiment-plan object (parameter-place value
or event field), the **sweep value is canonical for that dispatch**
and the model's static value is **suppressed**.

Required:
- Engine logs `[override] X = sweep_value (was static_value in model)`.
- Provenance records `parameter_sources: {X: "sweep" | "model_default"}`
  per condition.
- Validator emits notice on redundant override (sweep == static default).
- Baseline cell named `ModelDefaults` to avoid confusion with swept
  conditions.

Exception: superposition allowed only when it demonstrably reduces
simulation complexity (e.g. nested factorial sharing a fixed level)
and is declared explicitly in sweep config:
`"superposition_intent": "complexity_reduction"`. Without explicit
declaration, superposition is treated as a configuration smell.
