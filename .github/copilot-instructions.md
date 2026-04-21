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
- Deploy to server: commit → `git push private` → SSH `git pull private --ff-only`
- Server alias: `remote-gpu` → `simao@150.162.232.36`, repo at `~/shypn/`
- Server venv: `~/shypn/.venv/` (CuPy 14.0.1, CUDA 12.9, RTX 5060 Ti)

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
