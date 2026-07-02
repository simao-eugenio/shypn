# Engine Stability Audit — Low-Copy Regime (sub-µM)

**Date:** 2026-04-29
**Branch:** `Usability-and-enhancements`
**Trigger:** Phase-2 dose-response sweep (`workspace/projects/canabidiol`)
produced bit-identical downstream values across a 2000× substrate sweep.
Topology audit ruled out a structural disconnect (Phase-0 ≡ Phase-2,
0 arcs added/removed). Cause is engine behaviour at low copy / sub-µM,
not the model.

**Scope of audit:** the τ-leaping + Skellam + adaptive
continuous/stochastic switching stack as it operates when the smallest
active species drops below ≈100 molecules per compartment volume.

---

## 1. Failure modes (ranked by suspected impact on Phase-2)

### F1 — Silent default in `AdaptiveHybridBehavior._select_mode`

**File:** [src/shypn/engine/adaptive_hybrid_behavior.py](../src/shypn/engine/adaptive_hybrid_behavior.py#L267-L340)

- Decision rule: `min(molecule_counts) < threshold_molecules` →
  stochastic; otherwise continuous.
- When `place_filter='spatial_only'` (default) and *no* connected place
  carries `compartment_volume`, `analyze_transition` returns
  `reason='no-molecule-counts'` and the mode collapses to
  `'continuous' if prefer_continuous else 'stochastic'`.
- Most modeller-built places have **no** `compartment_volume` (must be
  set explicitly in the property dialog). The mode therefore defaults
  on a flag the modeller may never have touched.
- **No hysteresis.** A transition oscillating around the threshold
  flips mode on every propensity evaluation. `_handle_mode_change`
  *clears stochastic enablement state* on switch-away, restarting the
  per-transition enablement clock and discarding in-flight scheduling.
- Mode is recomputed inside `_evaluate_rate_at_enablement`, so even a
  stable model recomputes the analysis 10⁵–10⁶ times per replicate.

### F2 — Two competing critical-reaction criteria

**File:** [src/shypn/engine/simulation/tau_leaping/leap_selector.py](../src/shypn/engine/simulation/tau_leaping/leap_selector.py#L122-L162)

- Primary (Cao 2006, $N_c$-based):
  $L_j = \min_i \lfloor x_i / v_{ij} \rfloor < n_\text{critical} (=10)$
  → critical. Robust at low copy.
- Fallback (when `arc_table` absent):
  `propensity < critical_threshold` with default **0.01** in
  `simulation/settings.py`. Transitions with propensity 0.1/s
  (e.g. `Abeta_activates_IKK` at `Aβ_Olig=50`) are *never* critical
  → forced into the τ-leaping path even when a single firing changes
  state by O(1).
- The two criteria can give opposite answers for the same transition.
  Which one runs depends on whether the propensity accelerator built —
  for the Phase-2 model the ODE accelerator refused to build (4
  PreemptionCheck guards), so the fallback may have been used.

### F3 — Token-availability bound is not a step-size guard

**File:** [src/shypn/engine/simulation/tau_leaping/leap_selector.py](../src/shypn/engine/simulation/tau_leaping/leap_selector.py#L232-L248)

- `tau ≤ min_tokens / propensity` ensures sampled mean ≤ available
  tokens, but Poisson can sample 2–3× the mean.
- `_calculate_max_firings` then **silently truncates** sampled firings
  exceeding $\lfloor (M - \theta)/W \rfloor$. The truncation is
  invisible to the caller — no statistic counts how often it fires.
- Combined with high propensity at low copy (`Aβ_Mono²` explodes), this
  guarantees regular truncation events, deterministically biasing the
  trajectory.

### F4 — Skellam reversibility detector — false-positive prone

**File:** [src/shypn/engine/simulation/tau_leaping/skellam_sampler.py](../src/shypn/engine/simulation/tau_leaping/skellam_sampler.py#L142-L192)

- Triggers on `' - '` substring + `kf_*` / `kr_*` naming convention.
  Misclassifies:
  - `k * (A - K_eq)` (linear deviation, not reversible).
  - `kf * S - decay * P` where `decay` is not a reverse-rate constant.
- `rsplit(' - ', 1)` (Pattern 2) treats any single ` - ` as reversible,
  ignoring numerator/denominator structure inside Hill / Michaelis
  terms — `0.1 * X / (50 + X) - 0.05 * Y` is parsed as
  forward = `0.1 * X / (50 + X)`, reverse = `0.05 * Y` even though it
  is a single rate law with subtraction.
- A misclassified transition gets two **independent** Poisson draws
  (no enablement coupling), so net flux variance is **2× too large**
  at low copy.

### F5 — Operator-splitting cascade lag

**File:** `src/shypn/engine/simulation/controller.py` (`_finalize_step`
and the hybrid driver around L1740-1810).

- Per `dt`: continuous flow → stochastic τ-leap → finalize. Continuous
  transitions read the **start-of-step** marking; stochastic
  transitions read the *current* (mid-step) marking after continuous
  flow.
- Chains where a stochastic transition produces tokens that a
  continuous transition needs to read
  (`Aβ_Aggregation → Aβ_Oligo → Abeta_activates_IKK`) introduce a
  one-step lag per cascade level — the continuous reader sees the new
  oligomer only on the **next** dt.
- Invisible at high copy / fast equilibration; compounds at low copy
  where each cascade tick depends on the previous step's output.

### F6 — `min_tau` / `max_tau` interaction at extremes

**File:** [src/shypn/engine/simulation/tau_leaping/leap_selector.py](../src/shypn/engine/simulation/tau_leaping/leap_selector.py#L181)

- `tau = max(min_tau, min(tau_unbounded, max_tau))`,
  `min_tau=1e-6 s`, `max_tau=0.1 s`.
- When token-availability forces `tau < min_tau`, tau is *raised* to
  `min_tau` and Poisson is sampled with the original (large)
  propensity → over-shoot → triggers truncation in F3.
- When propensities are uniformly tiny (latent state), tau pins to
  `max_tau` → 100 ms slabs → 4-day horizon ≈ 3.5M steps → data
  collector decimates almost all of them.

### F7 — Coarse data-collector decimation

**File:** `src/shypn/engine/simulation/data_collector.py`
(referenced by `replicate_runner.py`).

- Recorded `statistics.json` for a 4-day run holds ≈100 time points,
  not the 3.5M steps the engine actually computed.
- Transient peaks lasting <1 simulated second — exactly the scale on
  which F3 + F5 produce visible artefacts — are absent from the
  recorded trace but *did happen* inside the engine.
- This is what made the Phase-2 diagnostic look like an architectural
  disconnect when it was transient + decimated.

---

## 2. Phase-2 reconstruction (working hypothesis)

Stacking F1 + F5 + F7:

1. `Abeta_Aggregation` is `transition_type=adaptive` with
   propensity = `0.05 * Aβ_Mono²`. Its input place `Aβ_Monomer` has no
   `compartment_volume` set → F1 silent default → mode pinned to one
   side of the switch (likely *continuous* since `prefer_continuous=True`
   is the project default).
2. At `DSEV=0.5` event injection, `Aβ_Monomer = 0.5 × 5 = 2.5`. In
   continuous mode, instantaneous rate = `0.05 × 2.5² = 0.3125`/s. Over
   one `max_tau=0.1 s` step, flux = 0.031 oligomer.
3. `Abeta_Oligomer_Clearance` (continuous, fast) immediately consumes
   most of it within the same dt. The inter-cascade reader
   `Abeta_activates_IKK` (continuous) sees the *previous* dt's oligomer
   value (F5 lag) → near-zero input → essentially no propagation.
4. Data collector records the trajectory at a coarse interval (F7);
   the brief oligomer transient is invisible.
5. Endpoint readouts equal the **initial markings** because no event
   ever actually shifted the cascade state by a recordable amount.

This explains why the 2000× substrate sweep produced bit-identical
downstream values — the cascade *did* fire, just below the recording
resolution and within a single dt that was instantly drained.

---

## 3. Stabilisation proposals

Ordered by intrusiveness; each row is independently implementable.

| # | Change | Files | Effort | Risk |
|---|--------|-------|--------|------|
| S1 | Make adaptive silent default explicit (raise on missing `compartment_volume`; require explicit `prefer_continuous`) | `adaptive_hybrid_behavior.py`, `spatial_utils.py` | ~1 h | low — surfaces existing silent error |
| S2 | Add hysteresis band + cached-mode interval to `_select_mode` (two thresholds; recompute every $N$ s, not every rate eval) | `adaptive_hybrid_behavior.py` | ~half day | low |
| S3 | Tighten Skellam detector: require both `kf_*` AND `kr_*` symbols AND exactly one *top-level* ` - ` (AST-parsed, not substring) | `skellam_sampler.py` | ~half day | medium — may reclassify existing models; needs validator hook |
| S4 | Surface Poisson-truncation events: counter on `TauLeapingEngine.stats['truncated_firings']`, warn when fraction > 5 % per replicate | `tau_leaping_engine.py` | ~half day | low — observability only |
| S5 | Adaptive trajectory recording: when `tau < min_record_interval` record every step, otherwise decimate | `data_collector.py` | ~1 day | low |
| S6 | Replace operator-splitting with single propensity vector (continuous as Gaussian-limit Poisson inside the same τ-leap draw) | `controller.py`, `tau_leaping_engine.py` | multi-day | high — touches the hybrid driver |
| S7 | Document operator-split lag + low-copy caveats in formalism section of `.github/copilot-instructions.md` | docs only | ~half day | none |

---

## 4. Recommended sequencing

**Phase A (instrumentation, no behavioural change):** S4, S5, S7.
Gives us *visibility* into how often F3 truncates and a recorded
trajectory that does not hide F5 transients. Re-run the Phase-2
diagnostic after this and compare against the current
`workspace/projects/canabidiol/experiments/results/run_*/` data.

**Phase B (low-risk behavioural fixes):** S1, S2.
Removes the silent mode-default trap and stops mode chatter at the
threshold. Re-run Phase-2 dose response.

**Phase C (semantic tightening):** S3.
Requires a model-load-time validator + a one-time pass over existing
`.shy` files to confirm Skellam classifications. Schedule after B
results are inspected.

**Phase D (architectural):** S6.
Only if A–C do not close the dose-response gap. Removes the cascade
lag entirely but reshapes the hybrid driver — defer until the simpler
fixes have been tested.

---

## 5. Probe scripts to write before any code change

To make Phase A measurable rather than anecdotal:

1. `tools/probes/probe_adaptive_mode_pinning.py` — minimal 1-place /
   1-transition model with no `compartment_volume`; logs which mode
   `_select_mode` returns, exercises `prefer_continuous` toggle.
2. `tools/probes/probe_skellam_misclassification.py` — table of rate
   strings (correct reversible, Hill subtraction, deviation form,
   linear loss) → expected classification → actual.
3. `tools/probes/probe_truncation_rate.py` — bimolecular A+A→B at
   `M(A)∈{1,5,25,100,1000}`; reports
   `truncated_firings / total_firings` per copy level once S4 lands.
4. `tools/probes/probe_cascade_lag.py` — three-place chain
   X →ₛₜₒ Y →cont Z; logs Z over time and compares against an
   exact-SSA reference.

Each probe doubles as a unit test once the fix lands.

---

## 6. Open questions

- **Q1.** Is the `compartment_volume` requirement for adaptive
  transitions documented anywhere user-facing? If not, S1 is a
  breaking change for downstream models and needs a deprecation cycle.
- **Q2.** Should Skellam detection be opt-in (modeller marks the
  transition `is_reversible=True`) rather than auto-detected from the
  rate-string syntax? That would eliminate F4 entirely at the cost of
  one extra flag per reversible reaction.
- **Q3.** Is the operator-split order
  (continuous → stochastic → finalize) load-bearing for any existing
  formalism guarantee, or can S6 freely reorder it?

These need answers before scheduling Phase B/C/D.
