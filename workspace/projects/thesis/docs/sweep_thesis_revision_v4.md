# v4 thesis sweep — protocol

## Purpose

Validate the two topology fixes and exercise the formalism extensions
introduced in `bacillus_sporulation_v4_thesis.shy`:

1. **Mass conservation** of the adenylate pool (ADP arcs to ATP regen
   transitions retyped `test → signal_flow`, weight 0.5 → 40).
2. **σ factor degradation** (5 new `T_Sigma{H,F,E,G,K}_decay`
   continuous transitions with `signal_flow` consumption arcs).
3. **Parameter places ▢ → event → spatial signals ◇ → Φ** bridge.
   Sweeping `Initial_Nutrients` ▢ now drives `Nutrients` ⬡ at $t=0$
   through `evt_apply_initial_nutrients`; sweeping `Temperature_K` ▢
   modulates `Source_ATP_regen` rate via `k_thermo_factor` ◇ and the
   Q10 law inside `evt_init_kinetics`.

## Model

- **File**: `workspace/projects/thesis/models/bacillus_sporulation_v4_thesis.shy`
- **Carriers**:
  - 26 ⬡ signal places (biology — unchanged from v3)
  - 3 ◇ spatial signal places: `k_ATP_target`, `k_sigma_decay`,
    `k_thermo_factor` (kinetic scalars; read by Φ remotely; written by
    events)
  - 4 ▢ parameter places: `Initial_Nutrients`, `Temperature_K`,
    `ATP_setpoint`, `Sigma_halflife_min` (read by events only; never
    in any Φ)
- **Events**:
  - `evt_init_kinetics` (priority 10, `t > 0`): populates the 3 ◇
    places from the 3 kinetic ▢ parameters via Q10 / half-life laws.
  - `evt_apply_initial_nutrients` (priority 5, `t > 0`):
    `Nutrients := Initial_Nutrients`.

## Sweep design — 3-axis factorial, single dispatch

| Axis | Knob (▢ → event → ◇ → Φ) | Levels | Probes |
|---|---|---|---|
| **A. Dose-response** | `Initial_Nutrients` ▢ → `Nutrients` ⬡ | `{10, 100, 300}` | basin-floor reproducibility vs v3 `run_20260509_125201` |
| **B. Q10 thermal** | `Temperature_K` ▢ → `k_thermo_factor` ◇ → `Source_ATP_regen.rate` | `{310.15, 320.15}` (Δ=+10 K) | Q10=2 ⇒ ATP regen flux should ~double, basin floor should shift |
| **C. Sigma decay** | `Sigma_halflife_min` ▢ → `k_sigma_decay` ◇ → `T_Sigma*_decay.rate` | `{30, 120, 600}` min | 120 = v3-default anchor; 20× decay-rate spread overall ⇒ σE steady-state should differ by ~20× between extremes |

**Cartesian product**: 3 × 2 × 3 = **18 conditions × 16 replicates = 288 runs**, dispatched as a single sweep. With `--workers ≤ 18` the dispatcher will run condition-batch GPU mode on `remote-gpu`.

This is a true multi-axis factorial — every (Nut, T, t½) combination is sampled, so axis interactions surface naturally:
- **A × B**: does the basin floor shift correctly with temperature *at every* nutrient level, or does the Q10 effect saturate at low nutrients?
- **A × C**: does fast σ decay rescue the abundance-driven sterility (Nut=300, σ accumulation in v3 → 14 800)?
- **B × C × A**: 3-way interaction — at high T + fast decay + low Nut, does the cell still commit?

## Dispatch

```bash
python -m shypn.cli.sweep \
    --project workspace/projects/thesis \
    --sweep   workspace/projects/thesis/sweep_config_v4.json \
    --workers 12 --verbose
```

(`--workers 18` matches the 18 conditions for clean GPU condition-batch mode; drop to 8–12 if VRAM is tight.)

Or from the GUI sweep panel: select `sweep_config_v4.json` and dispatch to `remote-gpu`. The dispatcher will SCP `bacillus_sporulation_v4_thesis.shy` along with the config and produce `provenance.json`.

## Acceptance criteria

| Code | Test | Threshold |
|---|---|---|
| **F1** | Mass conservation: $\|\text{ATP}+\text{ADP} - 5995\| / 5995$ at $t=21600$ | < 5 % in every condition (v3 had +630 %) |
| **F2** | σE saturation: max(`SigmaE`) reaches a peak before $t=200$ min, declines by $t=360$ | `fraction_kept` < 70 % at endpoint |
| **F3** | Bridge wiring: mean(`Nutrients` @ $t=1$ min) | within ±2 of `Initial_Nutrients` value per condition |
| **F4** | Thermal forcing: mean(ATP @ T=320.15) − mean(ATP @ T=310.15), held at fixed (Nut, t½) | basin floor shifts upward, ratio of ATP_regen flux ≈ 2.0 ± 0.2 (Q10 law) |
| **F5** | Decay scaling: σE steady-state(`t½=600`) / σE steady-state(`t½=30`), held at fixed (Nut, T) | ≈ 20 ± 5 |
| **F6** | Reproducibility: ATP basin floor across `Nut={10, 100, 300}` at (T=310.15, t½=120) — the v3-comparable slice | 2.24 ± 0.21 mM (matches v3 deep-analysis A) |
| **F7** | Interaction A×C: Mature_spore yield at (Nut=300, t½=30) vs (Nut=300, t½=600) | fast decay should *increase* spore yield by relieving σE accumulation lock-in observed in v3 |

If F1 passes, the v3 deep-analysis E warning is resolved and the v3
basin-floor result is structurally vindicated (it was real, not an
artifact of the +37 k token leak).

If F1 fails, investigate `Source_ATP_regen` — the 1:40 stoichiometry
might need re-balancing (e.g. one ADP per actual ATP token, with
weight 1:1 instead of 40:40).

## Analysis

Reuse the existing scripts on the new run dir:

```bash
python3 workspace/projects/thesis/scripts/analyze_thesis_revision_v3.py \
    --run workspace/projects/thesis/experiments/results/run_<v4_timestamp>

python3 workspace/projects/thesis/scripts/deep_analysis_v3.py \
    --run workspace/projects/thesis/experiments/results/run_<v4_timestamp>
```

Both scripts read the same statistics.json schema and will produce the
same 4 + 8 tables. Compare side-by-side with v3 outputs:

- `analysis/thesis_revision_v3/endpoint_table.csv`
- `analysis/thesis_revision_v3/atp_threshold_table.csv`

The diff is the v3-vs-v4 evidence for the topology fixes.

## What this sweep does NOT cover

- Multi-axis factorial (e.g. `Initial_Nutrients × Temperature_K`).
  Defer until Block A passes the acceptance criteria.
- Spore-yield bimodality reproduction at sub-µM resolution.
  Defer to a high-replicate (n≥64) follow-up if F6 holds.
- Long-horizon (>6 h) post-sporulation dynamics. The new σ decay
  topology makes this newly meaningful, but increases wall time ~5×.
