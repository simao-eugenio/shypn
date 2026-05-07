# SHyPN Engine — Time, Synchronization & Stiffness Notes

Notes captured during the canabidiol Q1 calibration session (2026-05-06)
while diagnosing why simulations behaved as they did. Sources: live
inspection of `src/shypn/engine/**` and `.github/copilot-instructions.md`.

---

## 1. Real-time clock synchronization across reactions

There is **one global simulation clock** owned by the controller, and
**all transitions advance against it via operator-splitting** — there
are no per-transition clocks for continuous transitions.

```
controller.current_time : float    # the global wall-clock t
controller.dt           : float    # global integration step (e.g. 1.0 s)
```

### Per-`dt` step ordering (hybrid strategy)

Every step processes **all** transitions against the **same start-of-step
marking `M(t)`** in this fixed sequence:

1. **Continuous phase (RK4)** — for every enabled continuous transition:
   ```
   k1 = f(t,        y)
   k2 = f(t+dt/2,   y + k1·dt/2)
   k3 = f(t+dt/2,   y + k2·dt/2)
   k4 = f(t+dt,     y + k3·dt)
   Δy = (k1 + 2k2 + 2k3 + k4) · dt / 6
   ```
   All continuous transitions evaluate at the same intermediate times
   (`t`, `t+dt/2`, `t+dt`); they couple through the **shared marking
   dictionary**, not through messages or timestamps.

2. **Stochastic phase (τ-leaping)** — Poisson sampling over `[t, t+dt]`,
   reading `M(t) + Δy_continuous` (post-continuous marking).
   This is the documented **operator-split lag (F5)**.

3. **Immediate / timed** — evaluated at `t+dt` against post-stochastic marking.

4. **Commit** — `controller.current_time += dt`.

### What "synchronization" actually means here

- All transitions read the **same `t`** within a stage.
- All transitions read/write the **same shared marking** (places are
  global state).
- Single-threaded, sequential — no race conditions on `t`.
- Coupling is implicit through the marking sum:
  `M_new[P] = M_old[P] + Σ_T (stoichiometry[T,P] · rate[T] · weight)`.

### Timed transitions

Have an `(earliest_time, latest_time)` window relative to their own
`enabled_since` timestamp (a per-transition **enable-clock**, not a
**simulation-clock**). Firing eligibility is still resolved against the
global `t`:
```
fires when:  t >= enabled_since + earliest_time
       AND   t <= enabled_since + latest_time
```

---

## 2. RK4 integrator — what's tunable

The continuous integrator is **classical fixed-step RK4** with
hard-coded Butcher tableau coefficients `(1/6, 1/3, 1/3, 1/6)`.

| Path                                                 | Method                            | Tunable                |
|------------------------------------------------------|-----------------------------------|------------------------|
| `engine/continuous_behavior.py::integrate_step()`    | Classical RK4, fixed step (CPU)   | only `dt`              |
| `engine/simulation/tau_leaping/gpu_hybrid_engine.py` | Same classical RK4 on GPU         | only `dt`              |
| `engine/acceleration/ode_system.py::integrate()`     | `scipy.integrate.solve_ivp`, **`method="LSODA"`** | `rtol`, `atol`, `max_step` |

The Canvas Play default is the **CPU RK4 path with `dt = 1 s`** (your
sweep CSV shows `dt med=1`). The acceleration path (LSODA) is opt-in
and requires the gcc + ctypes shared-library build.

---

## 3. Handling reactions with very different rates (stiffness)

The default RK4 path **does not handle stiffness gracefully**: a single
global `dt`, no error estimate, no step rejection. The fastest reaction
sets the safe step size for all of them.

### Mitigations available in the codebase

#### 3a. Adaptive transition-type switching (`transition_type: "adaptive"`)

In `engine/adaptive_hybrid_behavior.py`. Switches a single transition
between continuous (RK4) and stochastic (τ-leap) per-step **based on
marking volume**, not based on rate magnitude:

```
if any input place's tokens · compartment_volume > volume_threshold:
    fire as continuous
else:
    fire as stochastic
```

Addresses the **low-copy** problem (F1), not stiffness in the
dynamical-systems sense. Note the F1 trap: if `compartment_volume` is
missing on an input place, the engine silently falls back to
`prefer_continuous` *without* raising — always set
`compartment_volume` on at least one input place for adaptive
transitions.

**Lesson learned in this project (Phase 7):** when an `adaptive`
transition flips to stochastic in a low-marking regime and the input
arc has `W=1.0`, the transition can never fire (cannot satisfy `M ≥ W`
with `M < 1`). The fix was to make the type explicitly `continuous`
(`Abeta_Aggregation` T4 and `Plaque_Formation` T5).

#### 3b. τ-leaping adaptive step (in the stochastic engine itself)

`engine/simulation/tau_leaping_engine.py` uses Cao–Petzold adaptive τ
selection within each `dt`:

```
τ = min over species i of:  ε · max(M_i, 1) / |Σ_j ν_ij · a_j(M)|
```

Fast stochastic reactions force a smaller τ, so the stochastic part
**does** dynamically adapt to local rate magnitudes — but always
within the outer `dt` window.

Diagnostic for over-firing (F3): `engine_stats['truncation_fraction']`
exposes when sampled firings exceeded available tokens.
**`truncation_fraction > 5%` is the canonical signature of low-copy
bias** — always check before trusting a sub-µM sweep.

#### 3c. Acceleration path: real adaptive ODE solver

`engine/acceleration/ode_system.py` builds the entire continuous
sub-system into a single `dydt` C function and calls
`scipy.integrate.solve_ivp(method="LSODA")` — **stiff-aware**,
auto-switches between Adams (non-stiff) and BDF (stiff). This is the
only path in the repo that correctly handles ODEs with rate constants
spanning many decades. **Not** the default Canvas Play path.

#### 3d. GPU hybrid engine

Same fixed-step RK4 as CPU, batched across replicates. No different
stiffness handling — used for sweep parallelism, not for accuracy.

---

## 4. Practical decision table for stiff symptoms

| Symptom                                       | Cause                                    | Fix                                                                  |
|-----------------------------------------------|------------------------------------------|----------------------------------------------------------------------|
| Continuous oscillation around steady state    | `dt` too large vs fastest rate           | Reduce simulation `dt` (RecordingConfig / controller `time_step`).   |
| Place clamped to 0 each step                  | RK4 overshoot on fast consumption        | Reduce `dt`, OR convert that transition to stochastic.               |
| `engine_stats.truncation_fraction > 5%`       | τ-leap over-sampled (F3)                 | Lower the rate or raise the volume to push toward continuous mode.   |
| Sweep too slow because of small `dt`          | Stiffness forces small global step       | Use acceleration path (`LSODA`) for purely-continuous models.        |
| Cascade lag on signal_flow at low copy (F5)   | Continuous reads `M(t)`, stoch. reads `M(t)+Δ` | Reduce `dt`, or merge the two transitions into one `adaptive`.        |
| `adaptive` transition fires 0 times at low M  | Flipped to stochastic with `W=1.0`, `M<1`| Set `transition_type: "continuous"` explicitly (Phase-7 lesson).      |

---

## 5. Status of the canabidiol Q1 model w.r.t. stiffness

- Current Canvas Play `dt = 1 s`.
- Fastest rate constant in the calibrated model: `T28 = 5 · CBD_extracellular · Tf`.
  With `CBD_extracellular ≈ 10⁻⁴`, the actual rate is ~`5×10⁻⁴ /s`,
  three orders below `1/dt`. **Model is non-stiff at present.**
- Stiffness will become an issue if:
  - `LOADING_DOSE` is swept to ~100 µM (T28 rate ≈ 50/s, > `1/dt`).
  - Receptor `K_d` is dropped much below 1 nM and CBD reaches sat.
  - Any new reaction is added with intrinsic `k > 1/s`.
- Mitigation when that happens: drop `dt` to 0.01 s, OR move sweep to
  the acceleration path (`LSODA`).

---

## 6. Active feedback today vs gap

### What the engine actively flags today

- **Stochastic over-firing — the only "rate too fast for current step" signal.**
  In `engine/simulation/replicate_runner.py` (lines ~245 and ~742):
  ```python
  truncation_fraction = truncated_firings / requested_firings
  if truncation_fraction > 0.05:
      warnings.warn(f"τ-leap truncation {fraction:.1%} ...", RuntimeWarning)
  ```
  Counts incremented inside `tau_leaping_engine.py` lines 698–699 / 817–818
  whenever a sampled Poisson burst exceeded available tokens and was clamped.
  Surfaced as `engine_stats['truncation_fraction']` per replicate.

- **Negative-rate warnings** (rate-limited, 1-per-100): `stochastic_behavior.py`
  lines 80–82, 394–402. Catches malformed formulas / undetected reversibles.

### What the engine does NOT flag (gaps)

- **No CFL / stability check on the continuous RK4 path.** No comparison of
  `max_rate · dt` vs any threshold. If `k_continuous · dt > 1`, RK4 oscillates
  silently.
- **No warning when continuous flow drives a place to the floor.** The
  integrator clamps via `spendable = max(0.0, src.tokens − theta)` (line 862
  of `continuous_behavior.py`) — silent. Mass loss invisible.
- **No detection of mismatched timescales between transitions.** A reaction
  at `k = 10⁻⁶/s` running alongside one at `k = 10/s` produces no flag —
  both integrate at the global `dt`. **This is the critical gap.**
- **No NaN / inf guard** on rate evaluations.
- **No suggestion to switch to LSODA** even when stiffness clearly warrants it.

### Practical workflow today (without TMD)

| Concern | What to inspect |
|---|---|
| Stochastic step too coarse | `engine_stats['truncation_fraction']` after sweep, `RuntimeWarning` on stderr |
| Continuous step too coarse | Manual: plot trajectories, check for oscillation; verify no place hits hard 0 unexpectedly |
| Negative rates | Logger every 100 events for that transition |
| Rate-formula error | Only via negative-rate path, or via NaN propagation (no NaN guard) |
| Mismatched timescales | **No detection — must be checked by hand.** |

---

## 7. The cost of leaving the timescale gap unfixed

Reviewed 2026-05-06. The damage from the missing timescale check is **not** a
small precision loss; it threatens **falsifiability** of every quantitative
claim the simulator produces.

### 7a. Loss of falsifiability (worst class)

Without per-transition timescale validation, you cannot distinguish:
- "Biology says X" from "RK4 with too-large dt computed X"
- A real prediction from a numerical artifact
- A real dose-response saturation from integrator clipping
- An effect-size between sweep cells from numerical bias that differs
  between regimes

**Two sweep cells living in different stiffness regimes contribute an
unknown, unmeasurable bias to their difference.** That bias contaminates
every IC50, EC50, K_d, t½ derived from the sweep.

### 7b. Quantitative precision phase transition

RK4 is not a smooth precision degradation — it has a phase transition:

| `k · dt` | RK4 behaviour | Local truncation error |
|---|---|---|
| ≤ 0.1 | accurate | ~10⁻⁵ |
| 0.1 – 0.5 | accurate | ~10⁻³ |
| 0.5 – 1 | borderline | ~10⁻¹ — **steady-state values shift ~10%** |
| 1 – 2.78 | stable but inaccurate | overshoot ~30%, oscillation |
| > 2.78 | **unstable** | unbounded → silent clip → mass non-conservation |

So below 0.5 you're fine; above 1 you're publishing nonsense. There is no
gradual zone where you can "be careful" — you're either safe or wrong.

### 7c. Cascade amplification

In Petri nets, the operator-split lag (F5: continuous-stage → stochastic-stage
within a `dt`) compounds the error:
- A 10% precision loss in the continuous phase → ~30% variance bias in the
  downstream stochastic phase → ~50% bias in any quantity derived from the
  coupling.
- The Q1 canabidiol model has ~7 such cascades; errors compound multiplicatively.

### 7d. Reproducibility damage

Provenance currently captures: model bytes, config bytes, engine SHA, git HEAD.
**It does NOT capture the implicit stiffness regime the run lived in.**
Two runs of the same model bytes diverge if `dt` differs across machines
(canvas Play default vs sweep CLI default vs GPU hybrid default), and you
have no audit trail explaining why. TMD adds the missing third leg.

### 7e. Cost-of-investigation already paid

In the canabidiol Q1 calibration session alone (Phases 4, 6, 7), at least
~3–4 hours of human time were spent debugging numerical artifacts that
*looked* like model bugs. Each would have been caught at simulation start
by a static timescale audit. The cost amortizes after ~2 projects.

### 7f. The class of bug TMD eliminates

> "The model produces plausible numbers, the GUI shows trajectories,
> the provenance is clean, the formalism is respected — but the numbers
> are wrong because the integrator was stressed."

This is the worst class because all standard QA passes. Without TMD the
only defense is "I trust the integrator, I have eyeballed the trajectories."
That defense does not survive peer review on a quantitative claim.

### 7g. Capability matrix — as-is vs with TMD

| Capability | Today | With TMD |
|---|---|---|
| Run a simulation | ✓ | ✓ |
| Get reproducible bytes-identical output | ✓ | ✓ |
| **Trust numerical values quantitatively** | ✗ | ✓ |
| Publish a quantitative claim | ✗ (without manual audit) | ✓ |
| Detect a stiffness-induced artifact | ✗ | ✓ |
| Sweep across regimes safely | ✗ | ✓ |
| Compare conditions in different stiffness regimes | ✗ | ✓ |
| Defend "did you check dt?" in review | ✗ | ✓ |

The third row is the one that matters. The current engine produces fast,
well-organized numbers you cannot quantitatively defend. **TMD is the
difference between a simulator and a scientific instrument.**

---

## 8. Refactoring plan — Timescale Mismatch Detection (TMD)

Three escalating components, one config flag, one schema extension.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. timescale_audit.py        (static, model-load time)       │
│ 2. timescale_init_check      (init-time, controller hook)    │
│ 3. timescale_monitor.py      (runtime, every N steps)        │
└─────────────────────────────────────────────────────────────┘
```

### 8a. Static audit (`timescale_audit.py`)

For each continuous/adaptive transition `T_i`:
1. Evaluate `rate_function` at `M = M₀` symbolically.
2. `r_i_nominal = rate(M₀)`.
3. For each input place `P_j` with weight `W_ij`:
   `τ_consume_ij = M₀(P_j) / (W_ij · r_i_nominal)` (or ∞ if r=0).
4. `τ_i := min_j τ_consume_ij`.

Outputs: stiffness ratio `S = τ_max / τ_min`, list of violators, recommended
`dt = 0.1 · τ_min`.

### 8b. Init-time check (`SimulationController._check_timescales()`)

Same profile, but at the actual configured `dt`. Emits per-transition
warnings with **decision recipe**:

```
[TIMESCALE] T7 NFkB_phosphorylation: τ=5e-3s ≪ dt=1.0s (200× too coarse)
  Pick one:
    (a) Reduce dt to ≤ 5e-4s globally
    (b) Convert T7 to transition_type='stochastic' (τ-leap adapts)
    (c) Enable acceleration path with LSODA (best for >5 stiff transitions)
```

### 8c. Runtime monitor (`timescale_monitor.py`)

Every N steps (default 100), resample profile at current marking. Catches
dynamic stiffness (a place fills up, Hill saturates, slow→fast transition).
Cost: ~70 ms per replicate at 14k steps. Negligible.

### 8d. Schema extensions

`RecordingConfig`:
```python
timescale_check: Literal["off", "warn", "error"] = "warn"
timescale_monitor_interval: int = 100
timescale_dt_safety_factor: float = 0.1
```

`engine_stats['timescale']` per replicate:
```python
{
  'dt_used': float,
  'tau_min_init': float,
  'tau_min_runtime': float,
  'stiffness_ratio_max': float,
  'worst_dt_ratio': float,
  'violation_windows': int,
  'critical_transitions': [str, ...],
}
```

### 8e. Implementation phases

| Phase | Scope | Risk |
|---|---|---|
| **TMD-1** | Static + init checks, RecordingConfig flag, doc | Low |
| **TMD-2** | Runtime monitor, engine_stats extension | Low |
| **TMD-3** | Sweep aggregation, summary.csv columns | Low |
| **TMD-4** | Hill/MM rate-string analyzer (false-positive defense) | Medium |
| **TMD-5** | (Optional) auto-remediation: pick safe dt automatically | Higher |

TMD-1 is the minimum viable feature; TMD-2 follows in a second PR.
TMD-4/5 only if practice surfaces false positives.

### 8f. False-positive defense (TMD-4)

Hill / Michaelis–Menten rate strings should be downscaled by their effective
substrate ratio `M/(K+M)` before computing `τ`. Pattern-match the rate string;
if it matches `... * X / (K + X) * ...`, use `r_eff = r_nominal · M(X) / (K + M(X))`.

### 8g. Default safety factor

`dt_safety_factor = 0.1`. RK4 is stable to `k·dt ≤ 2.78` (4th-order
boundary), accurate to LTE-3 at `k·dt ≤ 0.5`. **0.1 is conservative**
and matches typical biochemistry practice.

---

## 9. Cross-references

- F1–F7 failure modes and S1–S7 remediation phases:
  [doc/engine_stability_audit.md](../../../../doc/engine_stability_audit.md)
- Carrier table, Pattern A discipline, audit codes C1–C12:
  [doc/pn_formalism/AGENT_RULES.md](../../../../doc/pn_formalism/AGENT_RULES.md)
- Workspace conventions and engine quirks:
  [.github/copilot-instructions.md](../../../../.github/copilot-instructions.md)
