# Canabidiol-AD protocols — index

One self-contained markdown per protocol, paired with the exact model
file used. Convention: `P<id>__<model_version>.md` (early protocols)
and `Q<n>__<model_tag>.md` (biological-question protocols against the
calibrated model).

## Active suite — calibrated model (post B1+B2+B3+B7)

All five biological-question protocols below pair with
[`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
as validated by `run_20260507_151546`. Dispatch from the Viability
panel in the UI.

| Question | Topic | Sims | File |
|---|---|---:|---|
| Q1 | CBD IC₅₀ on NFκB activation | 270 | [Q1__cal.md](Q1__cal.md) |
| Q2 | Aβ aggregation as stochastic bistable switch | 600 | [Q2__cal.md](Q2__cal.md) |
| Q3 | Microglial M1/M2 polarisation under CBD | 210 | [Q3__cal.md](Q3__cal.md) |
| Q4 | Inflammation–neuroprotection dissociation (ADAPT-style) | 510 | [Q4__cal.md](Q4__cal.md) |
| Q5 | Age-dependent CBD mechanism switch | 750 | [Q5__cal.md](Q5__cal.md) |

**Total budget:** 2340 simulations across the five protocols.

**Recommended dispatch order:** Q1 → Q3 → Q4 → Q2 → Q5.
Q1 establishes IC₅₀ for the inflammatory arm; Q3 confirms the
M1/M2 coupling; Q4 is the headline therapeutic-window factorial;
Q2 (high-replicate, drug-free) tests intrinsic bistability;
Q5 closes with the age axis (largest budget, deepest analysis).

## Archived suite — pre-calibration

| Protocol | Model | Sims | Status | File |
|---|---|---:|---|---|
| P1 — Pulse-maintenance factorial | `v3` | 5760 | ⚠ ARCHIVED (pre-fix engine + pre-Pattern-A) | [P1__v3.md](P1__v3.md) |
| P2 — Withdrawal challenge | `v3_p2` | 1080 | ⚠ PARKED (re-pair vs `v3_p8`) | [P2__v3.md](P2__v3.md) |
| P3 — Late rescue | `v3` (needs `_p3` variant) | 1350 | ⚠ PARKED (re-spec vs `v3_p8`) | [P3__v3.md](P3__v3.md) |
| P4′ — Lock-in bifurcation map | `v4_p4` | 2700 | ⚠ ARCHIVED (pre-fix engine + pre-Pattern-A) | [P4__v4_p4.md](P4__v4_p4.md) |
| P5 — Acute kinetic capture | `v3` (needs `_p5` variant) | 360 | ⚠ PARKED (re-spec vs `v3_p8`) | [P5__v3.md](P5__v3.md) |
| P6 — Disease-installation calibration | `v3_p6` | 210 + 30 | ⚠ ARCHIVED (pre-fix engine + pre-Pattern-A) | [P6__v3_p6.md](P6__v3_p6.md) |
| P7 — Healthy baseline / no-intervention homeostasis | `v3_p8` | 50 | ✅ READY (first post-fix protocol) | [P7__v3_p8.md](P7__v3_p8.md) |

**Re-run roadmap (post engine + Pattern-A migration):** see
[`../docs/recon_post_engine_fix_2026-04-27.md`](../docs/recon_post_engine_fix_2026-04-27.md)
for queued P1′ / P4′′ / P6′ rerun specs and new P8 (Pattern-A
self-test) and P9 (temperature dose-response) proposals.

**Recommended order** (per `docs/event_protocol_v3.md` §10): P6 → P5 → P2 → P3 → P1 → P4.

The shared chapters — disease-install spec (`evt_install_*` × 14),
parameter-place conventions, dispatch cheatsheet, analysis contrasts
— remain in [`docs/event_protocol_v3.md`](../docs/event_protocol_v3.md).
Each per-protocol file above is self-contained for sweep dispatch and
results, but cross-references the shared chapters for background.

## Per-protocol model variants

To keep each protocol pure (one paired model file, no sweep-time
suppression of model events), we derive `_p<id>` variants from
`v3` by zeroing the parameter places that drive events not used in
that protocol:

| Variant | Origin | Changes vs `v3` | Purpose |
|---|---|---|---|
| `v4_p4` | v3 minus `evt_maint_{1,2,3}` | Single-bolus only | P4 |
| `v3_p6` | v3 with `LOADING_DOSE=0`, `MAINT_DOSE=0`, `DOSE_INTERVAL=1e9` | Drug-free | P6 |
| `v3_p2` | v3 with `MAINT_DOSE=0`, `DOSE_INTERVAL=1e9`, +`evt_washout` | No scheduled redose; withdrawal at `t = 5400 s` | P2 |
| `v3_p3` | v3 minus `evt_load` and `evt_maint_*`, plus `RESCUE_DELAY` (TBD) | Late-rescue only | P3 |
| `v3_p5` | v3 with `MAINT_DOSE=0`, `DOSE_INTERVAL=1e9` (TBD) | Acute single-bolus | P5 |
| `v3_p8` | v3 rebalanced — neurotoxicity ROS/TNFα → test arcs; baseline M1→M2 + Plaque_Clearance terms; `is_environment_aware` stripped; chronic-dose defaults (LOADING=10, MAINT=5, INTERVAL=86400) | Healthy baseline / no-intervention homeostasis | P7 |

---

## Sweep suite — recommended dispatch sequence (2026-04-28)

Post engine-fix + Pattern-A migration, the result base is being
re-established from a clean foundation. Each phase **gates** the next
— do not run phase _n+1_ until phase _n_ acceptance criteria pass.
All dispatches authored from the Viability panel; the per-phase
**Output tier** below is the recommended setting in the new tier
ComboBox (beside Duration).

### Phase 0 — Healthy gating (~50 sims, ~1 MB at G2)

**Protocol:** P7 — `v3_p8` healthy homeostasis, 50 reps × 86400 s, single
condition (`Disease_Severity = 0`, `LOADING_DOSE = 0`, `MAINT_DOSE = 0`).

**Event compliance audit (2026-04-28):** with the three knobs above
zeroed, the following hold in `cbd_ad_neuroprotection_v3_p8.shy`:

| Event group | n | Expression | Effect at P7 settings |
|---|---:|---|---|
| `evt_install_*` | 14 | `target + DISEASE_SEVERITY * δ` | **no-op** (DSev = 0) |
| `evt_load` | 1 | `CBD_extracellular + LOADING_DOSE` | **no-op** (LD = 0) |
| `evt_maint_{1,2,3}` | 3 | `… + MAINT_DOSE` | **no-op** (MD = 0) |
| `evt_apply_thermodynamics` | 1 | seeds ◇ `Temperature_factor`, `Age_factor`, `pH_acidosis`, `pH_neutrality` from ▢ at `t < 1e-9` | **fires** — legal Pattern-A bridge ▢ → event → ◇ → Φ |

→ 18 / 19 events are zero-mass; only the thermodynamics seeder does
work, exactly as P7 §"Acceptance criteria" requires. Object-net is
exercised in pure homeostasis mode.

**Output tier:** **G2** (endpoint stats only — sufficient for the
12-marker acceptance table).

**Gate decision:** if any acceptance marker fails ⇒ patch `v3_p8` →
`v3_p9` before any further protocol; do not proceed to Phase 1.

### Phase 1 — Healthy environment envelope (~810 sims at G2 ≈ 50 KB)

**Protocol:** **P8** (new — to author after P7 passes) — `v3_p8` ×
`Disease_Severity = 0` × `Temperature ∈ {300, 305, 310.15, 315, 320}` ×
`Age ∈ {30, 60, 75, 85}` × `pH ∈ {6.5, 7.0, 7.4, 7.8}`, 30 reps × 4 h.

Validates the Pattern-A bridge (▢ → event → ◇ → Φ) reproduces the
modulation that hard-coded `Q10` / `Temperature` / `pH` / `Age`
symbols used to do in pre-`v3_p7` rate strings, **without** a disease
cascade. This is the canonical *long healthy baseline* across
physiological variation.

**Output tier:** **G2** (endpoint envelope across the grid).

### Phase 2 — Disease-installation calibration (~210 sims at G3)

**Protocol:** **P6′** (rerun of P6 against `v3_p8`) — `LOADING_DOSE = 0`,
`MAINT_DOSE = 0`, `Disease_Severity ∈ {0, 0.5, 1, 1.5, 2, 2.5, 3}`,
30 reps × 4 h.

Tests monotonicity of DSev → plaque / NFkB / NH dose-response under
the corrected engine. Picks the canonical "moderate disease" severity
for downstream Phase 3 dispatches. Resolves Q4 in the recon doc
(P1 finding F2: Sev contributed only ~3 % of NH variance pre-fix).

**Output tier:** **G3** (per-step trajectories — needed to see the
disease cascade ignition kinetics, not just endpoints).

### Phase 3 — Therapeutic dose-response on diseased state

**Protocol:** **P1′ (slim rerun)** — `v3_p8` × DSev (3 levels chosen
from P6′) × `LOADING_DOSE` (5 levels) × `MAINT_DOSE` (3 levels) × Age
(3 levels), 30 reps × 4 h. ≈ 4320 sims at G3.

Optionally split into:
- **P9** — Temperature × Dose for the thermodynamic story (~720 sims)
- **P4′′** — Bifurcation refine for the lock-in story (~2700 sims at
  60 reps × 4 h)

**Output tier:** **G3** for the headline factorial; **G2** for the
exploratory grids.

### Cumulative budget

| Phase | Sims | Approx wall (4 workers) | Disk |
|---|---:|---|---|
| 0 — P7 | 50 | ~10 min | ~1 MB |
| 1 — P8 | 810 | ~3 h | ~50 KB |
| 2 — P6′ | 210 | ~1 h | ~3 GB |
| 3 — P1′ slim | 4320 | ~24 h | ~60 GB |

Phase-3 disk dominates because of G3 trajectory storage; revisit tier
choice once Phase-2 has shown which conditions actually need
trajectory granularity.

### Operator notes

- **All dispatches go through the Viability panel.** The Output Tier
  ComboBox is beside Duration on the Simulation Settings row.
- The model's `evt_apply_thermodynamics` MUST keep firing across all
  phases — it is the **only** legal channel by which ▢ parameter
  places (`Temperature`, `Age`, `pH`) influence biology rates. A
  failure to fire silently neutralises every environmental sweep.
- `output_tier` is omitted from `sweep_config.json` when equal to the
  default `G3`; explicit `"output": {"tier": "G2"}` blocks are
  emitted only when the operator picks a non-default in the UI.
- Do **not** edit the canonical `v3_p8.shy` between Phase 0 and Phase
  3 — the dispatcher captures `model_snapshot.shy` per run, but
  cross-phase comparisons require a stable model SHA.
