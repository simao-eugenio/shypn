# Canabidiol-AD protocols — index

One self-contained markdown per protocol, paired with the exact model
file used. Convention: `P<id>__<model_version>.md`.

| Protocol | Model | Sims | Status | File |
|---|---|---:|---|---|
| P1 — Pulse-maintenance factorial | `v3` | 5760 | ✅ run_20260424_005438 | [P1__v3.md](P1__v3.md) |
| P2 — Withdrawal challenge | `v3_p2` | 1080 | ⏸ model ready, awaiting dispatch | [P2__v3.md](P2__v3.md) |
| P3 — Late rescue | `v3` (needs `_p3` variant + `RESCUE_DELAY`) | 1350 | ⏸ pending model | [P3__v3.md](P3__v3.md) |
| P4′ — Lock-in bifurcation map | `v4_p4` | 2700 | ✅ run_20260424_165603 | [P4__v4_p4.md](P4__v4_p4.md) |
| P5 — Acute kinetic capture | `v3` (needs `_p5` variant) | 360 | ⏸ pending model | [P5__v3.md](P5__v3.md) |
| P6 — Disease-installation calibration | `v3_p6` | 210 + 30 | ⏳ in progress | [P6__v3_p6.md](P6__v3_p6.md) |

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
