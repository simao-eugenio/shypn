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

**Firing rule:** `M'(p) = M(p) + Δ_normal(p,t) + Δ_signal(p,t)` (test arcs Δ = 0).

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

3. **Test arcs are the only non-consuming arc type** (`arc_type='test'`).
   All `behavior.fire()` methods must `continue` past test arcs.

4. **PreemptionCheck is single-layer and non-recursive.** Lives in
   `TransitionBehavior._check_preemption()`; called from every
   `can_fire()` (immediate, stochastic, continuous, timed). Vacuously
   true for Layer-0 transitions (no signal predecessors).

5. **Inhibitor arcs invert:** `tokens >= threshold → disabled`.

6. **Reversible reactions** use Skellam sampler (Poisson(fwd) − Poisson(rev)).

### Open gap

- **C1 — Multi-layer signal hierarchy:** the current single-layer
  `PreemptionCheck` is correct per the formalism but does not propagate
  beyond direct signal predecessors. Multi-layer enforcement requires
  the signal hierarchy layer-assignment infrastructure in the simulation
  context (not yet wired in).

## Experiment plan vs object-net (STRICT, 2026-04-25)

Full text: [`doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md`](../doc/pn_formalism/EXPERIMENT_PLAN_VS_OBJECT_NET.md).
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

### One concept ↔ one carrier (no semantic mirroring)

A conceptual quantity (`Age`, `Temperature`, `pH`, `Disease_Severity`,
…) is represented by **exactly one** carrier. The three legal carriers
are mutually exclusive per concept:

1. **Pure parameter place ▢** — no arcs, never in any $\Phi$.
2. **Signal place ⬡** — in $\Psi$, has $F_s$ arcs, participates in
   `PreemptionCheck`. May also be referenced in $\Phi$.
3. **Remote-sensed regular place ○** — referenced by name inside $\Phi$.

Forbidden: two carriers for the same concept (e.g. `Age` signal place
*and* `Age_param` parameter place). Sweeping `X.initial_marking` of a
topology-coupled place is **legal** — it is an initial-condition
perturbation of $M_0$, not a superposition violation. If you find
yourself wanting to add a parameter mirror so a topology place becomes
sweepable, sweep `initial_marking` directly instead.

### Remote sensing requires topology membership

A symbol may appear inside any object-net rate function $\Phi$ only if
the corresponding place has at least one $F$, $F_s$, or $F_t$ arc
(i.e. is part of $G_E$ or $G_s$), or is itself the producer/consumer
of the transition under that rate. A name appearing in a rate string
while the underlying place has **zero arcs of any kind** is a
parameter-place backdoor wearing the wrong glyph.

Canonical bridge for protocol-driven kinetics — **▢ + event → ○ → $\Phi$**:

1. Keep the protocol metadata as a parameter place ▢
   (e.g. `Temperature = 310.15 K`).
2. Add a kinetic regular place ○ (e.g. `k_polym_eff = 1.0`).
3. Reference the kinetic place — **not** the parameter — inside $\Phi$
   (e.g. `rate = k_polym_eff * Aβ_Monomer**2`).
4. Add an event that reads the parameter and writes the kinetic place
   at $t = 0$ (or on demand):
   `evt_apply_thermodynamics: k_polym_eff := k_base * Q10**((Temperature-310)/10)`.

The biology stays generic; only the event encodes the protocol. The
audit code **C9 — disconnected remote sensing** flags violations.

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
