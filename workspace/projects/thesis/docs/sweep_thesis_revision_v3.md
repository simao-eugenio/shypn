# Thesis-Revision Sweep Protocol — `bacillus_sporulation_v3_thesis.shy`

**Date:** 2026-05-09
**Purpose:** Mine the *current* SHyPN engine + rescaled bacillus model for new
emergent values (ATP commitment threshold, mature-spore timing, commitment→
completion lag) so Chapter 4 of the thesis can be rewritten honestly under
**Route B** (keep the current model, replace the Fujita-2005 anchor numbers with
the values this engine actually produces).

The thesis claims (now obsolete under the rescaled model):

| Claim | Old anchor (Fujita 2005 / mM-scale model) |
|---|---|
| Emergent ATP threshold | 2.21 mM at t = 293.9 min |
| Mature spore appearance | t = 334.2 min |
| Commitment → completion lag | Δt = 40.3 min |

These must be replaced with values measured from the current model:
`workspace/projects/thesis/models/bacillus_sporulation_v3_thesis.shy`
(M₀: Nutrients=100, ATP_pool=5000, ADP_pool=995, GTP_pool=5000,
GDP_pool=995, Spo0A=25, KinA_kinase=10, …; horizon 21 600 s).

---

## What the sweep must produce

For every condition, per replicate, record at minimum:

1. **Full ATP_pool trajectory** at fine resolution (need to locate threshold
   crossing accurately). Set `recording_time_interval = 1.0` (1-second steps
   over 6 h → 21 601 samples per replicate; ≈ 0.5 MB CSV).
2. **First-passage times** for: ATP_pool dropping below
   {1000, 500, 100, 50, 10, 5, 2.21, 1, 0.5, 0.1}; first non-zero of
   {SigmaH, SigmaF, SigmaE, SigmaG, SigmaK, Septum, Forespore, Mother_cell,
   Cortex, Inner_coat, Outer_coat, Mature_spore}.
3. **Endpoint markings** for all 26 places at t = 21 600 s.

Items (2) and (3) are derived in post-processing from item (1) — the engine
just needs the trajectory.

---

## Conditions

Four conditions, factorial over Nutrients only (the upstream driver of the
ATP curve). Other M₀ values stay at the model defaults so we measure how the
emergent threshold and timings respond to substrate availability — the analog
of Fujita 2005's chemostat dilution sweep.

| Condition       | Nutrients M₀ | Biological analog                        |
|-----------------|--------------|------------------------------------------|
| `Baseline`      | 100          | Canonical thesis model M₀                |
| `NutrientRich`  | 300          | Excess substrate — should *delay* threshold crossing |
| `NutrientLow`   | 30           | Mild limitation — earlier crossing       |
| `NutrientStarved` | 10         | Severe limitation — earliest crossing    |

Replicates: **16 per condition** (4 × 16 = 64 sims). Sufficient to estimate
mean ± std on threshold-crossing time without burning the GPU.

Horizon: **21 600 s (6 h)** to match the original chapter timeframe.

Engine: stochastic τ-leaping for discrete transitions, RK4 for the 5
continuous transitions (operator splitting — the default).

---

## Sweep config (`workspace/projects/thesis/sweep_config.json`)

Replace the current `sweep_config.json` (or back it up first) with:

```json
{
  "model_path": "workspace/projects/thesis/models/bacillus_sporulation_v3_thesis.shy",
  "duration": 21600.0,
  "recording_time_interval": 1.0,
  "n_replicates": 16,
  "seed_strategy": "per_replicate",
  "conditions": [
    {
      "name": "Baseline",
      "overrides": { "Nutrients": 100.0 }
    },
    {
      "name": "NutrientRich",
      "overrides": { "Nutrients": 300.0 }
    },
    {
      "name": "NutrientLow",
      "overrides": { "Nutrients": 30.0 }
    },
    {
      "name": "NutrientStarved",
      "overrides": { "Nutrients": 10.0 }
    }
  ]
}
```

> **Note on overrides:** `Nutrients` is a regular place (no parameter-place
> in this model), so the override sets `place.initial_marking` for the
> condition. Engine logs `[override] Nutrients = X (was 100.0 in model)` per
> condition. This is M₀ perturbation, fully legal per HPN rules.

---

## Dispatch from UI

1. Project: **thesis**.
2. Model: `bacillus_sporulation_v3_thesis.shy` (the new file, leave
   `v2.shy` untouched as historical record).
3. Sweep config: the JSON above.
4. **GPU policy: `force`** (4 conditions × 16 reps = 64 sims; pool worker
   count likely ≤ 4, so condition-batch dispatch will route to GPU
   automatically with `auto`. `force` is safer.)
5. Workers: **4** (one per condition; condition-batch mode batches the 16
   reps inside each worker through `runner.run_replicates(n=16)` →
   `GPUHybridEngine`).
6. Output: leave default (`workspace/projects/thesis/experiments/results/run_<ts>/`,
   resolved through the server symlink to `~/data/results/thesis/`).

Expected wall time: ~3–5 min (single Baseline rep takes ~10 s; 64 reps
batched on RTX 5060 Ti should finish well under 5 min including overhead).

---

## Post-run analysis (I will do, after you dispatch)

Write a `dev/analyze_thesis_revision.py` that, given the run dir, produces:

1. **`thesis_revision_endpoint_table.csv`** — per condition, mean ± std of
   endpoint markings for all 26 places.
2. **`thesis_revision_threshold_table.csv`** — per condition, mean ± std of
   first-passage times for ATP_pool ≤ {1000, 500, 100, 50, 10, 5, 1, 0.5,
   0.1}, plus first-appearance times for each of the 12 cascade species.
3. **`thesis_revision_atp_trajectories.pdf`** — overlay of ATP_pool curves
   (16 replicates per condition, faint lines + bold mean), one panel per
   condition, with horizontal markers at the candidate threshold values.
4. **`thesis_revision_cascade_order.csv`** — per condition, modal activation
   order of the 5 sigma factors and 7 structural species; flag inversions.
5. **`thesis_revision_summary.md`** — proposed replacement values for the
   thesis Chapter 4 anchor table:
   - new emergent ATP threshold (the value at which the cascade ignites,
     identified by the inflection point on the mean trajectory or by the
     time at which Spo0A_P first crosses some basin level)
   - new mature_spore appearance time (mean ± std)
   - new commitment → completion lag
   - new ordering of the cascade and any honest violations

These tables are what we feed into the rewrite of `cap_04_validacao_bacillus.tex`.

---

## Acceptance criteria for the dispatch

- All 64 replicates terminate without errors.
- `provenance.json` shows `parameter_sources` recording the Nutrients
  override per condition (proves the sweep value, not the static M₀, was
  the canonical input).
- `engine_stats.truncation_fraction < 0.05` on all replicates (otherwise
  the τ-leaping is over-sampling at low copy and the trajectories aren't
  trustworthy — would force a re-run with smaller `tau_leap_step`).
- ATP_pool trajectory CSVs are present for every replicate at 1-second
  resolution.

If any of these fail, **do not** start the analysis — re-dispatch with the
diagnostics fixed first.
