# Bacillus sporulation v2 — first remote sweep probe

Purpose: validate the sweep + GPU dispatch pipeline end-to-end on the
thesis model **before** committing to a full thesis-figure sweep.

Reference single-run anchor (deterministic baseline):
`workspace/projects/thesis/data/bacillus_sporulation_v2.csv`
(6 h sim, 21 602 rows, Mature_spore = 53 at endpoint, full cascade
ignites — confirms post-C1 engine fix).

---

## Probe design (smallest useful sweep)

| Field | Value | Rationale |
|---|---|---|
| Parameter | `Nutrients.initial_marking` | Primary sporulation trigger; default 10 → starvation. |
| Values | `[10, 100, 1000]` | 3 conditions: starved, intermediate, replete. |
| Replicates per condition | `8` | Enough for endpoint mean ± SD; small enough that the probe finishes fast. |
| Duration | `21600` s (6 h) | Matches the validated single-run horizon. |
| Termination | `time` | |
| `tau_epsilon` | `0.03` | Engine default. |
| `max_tau` | `0.1` | Engine default. |
| `seed_base` | `42` | Reproducibility. |
| Fixed overrides | none | Take all other initial markings from the model. |
| Events | none | Model has none. |

Total work: 3 conditions × 8 reps × 6 h = 24 simulations.

Expected wall time on `remote-gpu`:
- With `--use-gpu auto` and `--workers 1` → condition-batch (8 reps
  per GPU dispatch) → < 2 min total (canabidiol Q1 anchor: 4 reps × 60 s
  in 1.3 s).
- Without GPU (flat-dispatch, many CPU workers) → ~5 min.

---

## sweep_config.json (drop into `workspace/projects/thesis/`)

```json
{
  "mode": "single",
  "model_path": "models/bacillus_sporulation_v2.shy",
  "replicates": 8,
  "duration": 21600,
  "termination": "time",
  "seed_base": 42,
  "tau_epsilon": 0.03,
  "max_tau": 0.1,

  "parameter": {
    "type": "places",
    "path": "Nutrients.initial_marking",
    "values": [10, 100, 1000]
  },

  "fixed_overrides": {},
  "events": []
}
```

---

## How to dispatch from the UI

1. Open `workspace/projects/thesis` in the GUI; load
   `models/bacillus_sporulation_v2.shy`.
2. Open the **Sweep / Experiment** panel.
3. Either:
   - **Load** the `sweep_config.json` written above, OR
   - Configure interactively: parameter `Nutrients.initial_marking`,
     values `10, 100, 1000`, replicates 8, duration 21 600 s.
4. Set dispatch target:
   - **Server:** `remote-gpu` (alias of `simao@150.162.232.36`).
   - **Workers:** `1` (lets `--use-gpu auto` route via condition-batch
     to the GPU; with > 1 worker the dispatcher falls back to flat
     CPU dispatch when workers > n_conditions).
   - **GPU policy:** `auto` (or leave at default).
5. Press **Dispatch**. The dispatcher will:
   - SCP the `.shy` model to the server (always; hybrid sync model).
   - Write `sweep_config.json` and `provenance.json` to the run dir.
   - Snapshot `model_snapshot.shy` per run.
   - Run the sweep; results land in
     `workspace/projects/thesis/experiments/results/run_<ts>/`.

If the UI does not yet expose `--use-gpu` as a control, the equivalent
CLI invocation that the dispatcher should issue is:

```bash
ssh remote-gpu "cd ~/shypn && source .venv/bin/activate && \
  python -m shypn.cli.sweep \
    --project workspace/projects/thesis \
    --sweep   workspace/projects/thesis/sweep_config.json \
    --workers 1 --use-gpu auto --verbose"
```

Expected banner lines on stdout:
```
GPU policy: auto → condition-batch (workers=1 ≤ conditions=3; R=8 reps batched on GPU)
[condition-batch] 3 cond × 8 reps = 3 work units, pool=1
```

---

## Validation checks after the run completes

Open `experiments/results/run_<ts>/`:

1. `summary.csv` — should have 3 rows (one per Nutrients value), each
   reporting Mean ± SD of every place at the endpoint.
2. `provenance.json` — confirm
   `parameter_sources["Nutrients.initial_marking"] == "sweep"` and the
   model sha256 matches the in-tree `models/bacillus_sporulation_v2.shy`.
3. `condition_Nutrients.initial_marking=10/statistics.json` —
   Mature_spore mean should be **non-zero** (cascade ignited under
   starvation), comparable to the deterministic anchor (Mature_spore
   ≈ 53 at 6 h).
4. `condition_Nutrients.initial_marking=1000/statistics.json` —
   Mature_spore should be **near zero** (high nutrients suppress
   sporulation; this is the biological control).
5. `resource_usage.json` — `gpu.avg_sm` should be > 0 % (GPU was
   actually used). Note: short runs may show 0–5 % only because
   nvidia-smi sampling at 500 ms misses the burst.

If conditions 10 and 1000 produce the **same** Mature_spore distribution,
suspect either:
- Sweep override didn't land (check `provenance.json`
  `parameter_sources`).
- F1/F5/F7 low-copy bias from
  `.github/copilot-instructions.md` "Low-copy / sub-µM caveats" — but
  Nutrients is in the 10 → 1000 range, well above the trap.

---

## After the probe passes

Promote to thesis-figure scale:
- Larger Nutrients gradient: `[5, 10, 25, 50, 100, 250, 500, 1000]`.
- 30 reps per condition (matches canabidiol thesis convention).
- Possibly 2D factorial: `Nutrients × KinA_kinase` (5 × 5 grid).

Capture the sweep config used for the figure under
`workspace/projects/thesis/sweep_config.<figure_id>.json` so the
manuscript can cite the exact dispatch.
