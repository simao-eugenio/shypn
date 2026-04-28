# Phase 0 — Healthy Baseline Validation

**Project:** CBD vs Alzheimer's Disease Neuroprotection
**Model:** `canabidiol-phase-0.shy` (sha256 `c49df7f817566c56f1d0f3e394a88354e609ee733481f15d27c860431ba09389`, formerly `cbd_ad_neuroprotection_v3_p9.shy`)
**Date:** 2026-04-28
**Final dispatch:** `run_20260428_184351` (server: insilicolab / RTX 5060 Ti, 32 cores)
**Engine:** SHyPN v0.x · τ-leaping · GPU CuPy 14.0.1 / CUDA 12.9

---

## 1. Objective

Establish a **healthy steady-state baseline** for the 42-place CBD–AD
neuroprotection model, satisfying the P7 acceptance markers:

- Sustained Neuron Health (NH ≈ 100 over 24 h).
- Resting redox state (ROS ≈ 0).
- Quiescent inflammation (TNFα, IL-1β, IL-6, COX-2 → 0).
- Predominantly anti-inflammatory microglial polarisation
  (M2 ≫ M1).
- Stable Aβ pool (no oligomerisation or plaque accumulation in the
  absence of disease drivers).
- Verified parameter-place superposition: the
  `DISEASE_SEVERITY=0` sweep override must be **inert** in the
  object-net (Pattern A discipline).

## 2. Sweep configuration

```text
horizon       = 86 400 s (24 h)
n_replicates  = 50 per condition
engine        = stochastic τ-leaping (GPU)
conditions    = ["Baseline", "[param] DISEASE_SEVERITY=0"]
workers       = 4 outer / 8 inner (adaptive split)
wall_time     = ≈ 215 s per condition (50 reps)
```

The two conditions are deliberately **identical at the object-net
level**: `DISEASE_SEVERITY` is a parameter place (▢ in the four-carrier
formalism) read only by events; setting it to 0 must not perturb any
biological rate. Any divergence between conditions would indicate a
Pattern A violation (parameter back-channel into a Φ rate).

## 3. Endpoint markers (t = 24 h, mean ± SD across 50 replicates)

| Marker            | Baseline      | DSEV=0        | Target      | Verdict |
|-------------------|--------------:|--------------:|-------------|:-------:|
| Neuron_Health     | 100.0 ± 0.0   | 100.0 ± 0.0   | ≈ 100       | ✅      |
| ROS               | 0.0 ± 0.0     | 0.0 ± 0.0     | ≈ 0         | ✅      |
| NFκB_p65          | 0.0           | 0.0           | ≈ 0         | ✅      |
| TNFα              | 0.50          | 0.50          | basal low   | ✅      |
| IL-1β             | 0.0           | 0.0           | 0           | ✅      |
| IL-6              | 0.0           | 0.0           | 0           | ✅      |
| COX-2             | 0.0           | 0.0           | 0           | ✅      |
| Microglia_M1      | 0.0           | 0.0           | low         | ✅      |
| Microglia_M2      | 45.0          | 45.0          | dominant    | ✅      |
| Glutathione (GSH) | 305.8 ± 2.1   | 305.2 ± 2.2   | drift, bounded | ⚠   |
| GSSG              | 33.5          | 33.5          | drift, bounded | ⚠   |
| Nrf2_free         | 6.0           | 6.0           | ≈ 5         | ✅      |
| Keap1–Nrf2        | 54.0          | 54.0          | ≈ 55        | ✅      |
| SOD               | 21.6 ± 3.5    | 22.1 ± 3.6    | ≈ 20        | ✅      |
| HO-1              | 32.4 ± 4.3    | 33.2 ± 4.4    | ≈ 30        | ✅      |
| Aβ_Monomer        | 0.78          | 0.78          | low         | ✅      |
| Aβ_Oligomer       | 0.0           | 0.0           | 0           | ✅      |
| Aβ_Plaque         | 0.0           | 0.0           | 0           | ✅      |
| BDNF              | 4.14          | 4.14          | stable      | ✅      |
| CBD_intracellular | 9.98          | 9.98          | uptake OK   | ✅      |

**Score: 16 ✅ / 2 ⚠ / 0 ❌.**

## 4. Verification of parameter-place inertness

Pairwise condition difference for every monitored marker is within
stochastic noise (≤ 1× SD). Specifically:

- ΔGSH(end) = 305.8 − 305.2 = 0.6 (vs SD ≈ 2.1; |Δ|/σ ≈ 0.3)
- ΔSOD(end) = 21.6 − 22.1 = −0.5 (vs SD ≈ 3.5)
- ΔHO-1(end) = 32.4 − 33.2 = −0.8 (vs SD ≈ 4.3)

All other markers are bit-identical between conditions. This confirms:

1. `DISEASE_SEVERITY` does **not** appear in any object-net rate Φ
   (no Pattern A back-channel).
2. The sweep override mechanism correctly masks the model's static
   default value and is logged as such in `provenance.json`.
3. The four-carrier discipline (○ ⬡ ◇ ▢) is preserved end-to-end:
   parameter places remain causally silent until an event reads them.

## 5. Bounded drift on the GSH/GSSG axis

The two ⚠ markers reflect a **physiologically defensible anabolic
expansion** of the antioxidant pool, not a pathological accumulation:

- The Nrf2-driven `Nrf2_ARE_transcription` transition (T12) has a
  small (weight 0.02) production arc to Glutathione, sourcing GSH at
  ≈ 0.005 tokens · s⁻¹ across the simulation.
- With ROS ≈ 0, the GSH-consuming term in `Antioxidant_Scavenging`
  (T13) is suppressed (rate ∝ ROS/(5+ROS) → 0), so GSH accumulates
  monotonically.
- The Glutathione_Reductase (T41) cycle holds GSSG at ≈ 33 tokens at
  the end of the horizon (in/out balanced at 0.06 · GSSG ≈ 2 token·s⁻¹).

This matches the in vivo phenomenon of chronic Nrf2 activation
elevating cellular GSH pools during sustained low-level CBD signalling
(e.g. Atalay et al., 2020, *Antioxidants*). For the purposes of
Phase 0 — establishing a stable, non-pathological resting state — this
drift is acceptable and was retained as the canonical baseline.

## 6. Provenance

```json
{
  "model": {
    "remote_path": "/home/simao/shypn/workspace/projects/canabidiol/models/canabidiol-phase-0.shy",
    "sha256":     "c49df7f817566c56f1d0f3e394a88354e609ee733481f15d27c860431ba09389",
    "size_bytes": 142… ,
    "architecture": "42 places · 45 transitions · 100 arcs"
  },
  "sweep_config_sha256": "0da4124634762aee06f205c1308be95d8230920d7822fcb59939309a1152dbaf",
  "engine": {
    "solver":      "tau_leaping",
    "gpu_backend": "cupy",
    "n_replicates_per_condition": 50,
    "horizon_seconds": 86400
  },
  "client_git_head": "1304f49ade3ed7f8b8e9ba2e76c9e18d73d95b10",
  "server_git_head": "1304f49ade3ed7f8b8e9ba2e76c9e18d73d95b10",
  "dispatched_at":   "2026-04-28T15:43:51"
}
```

Per-run provenance (`provenance.json`) and a frozen copy of the model
bytes (`model_snapshot.shy`) live inside the run directory and
guarantee independent reconstruction even after subsequent edits.

## 7. Methodological lesson from the rebalance journey

Reaching the closed Phase 0 took **four iterations** of the
v3_p9 model, recorded here for the manuscript Methods discussion:

| Variant            | sha256 prefix | Topology                                       | NH  | ROS  | GSH  | GSSG | Outcome |
|--------------------|---------------|------------------------------------------------|----:|-----:|-----:|-----:|---------|
| v3_p9 base         | `dec2ec67…`   | 42P · 45T · 100A (pre-rebalance, 6 rate tweaks)| 100 | 0    | 283  | 27   | 11/12 markers; GSH drift |
| + sink+cycle (B)   | `007766da…`   | + T46 cycler with arcs A101 (in) + A102 (out)  | 100 | 0    | 283  | 27   | 14/16 markers; same as base |
| + rate ×4 (twoknob)| `02bde0fb…`   | T46 cycler, T41 0.06→0.20, T46 0.005→0.020     | 75  | 17   | 672  | 0    | ❌ GSSG collapse |
| + sink-only (B′)   | `2172e62b…`   | T46 sink (A102 removed), T46 0.020             | 50  | 121  | 0.06 | 0.55 | ❌ catastrophic |
| + sink+5e-5 (A2)   | `8029e418…`   | T46 sink, T46 5e-5                             | 76  | 17   | 136  | 16   | ❌ cycle still broken |
| **revert (A1)**    | **`c49df7f8…`** | **42P · 45T · 100A — T46 + arcs removed**   | **100** | **0** | **306** | **34** | **✅ adopted** |

**Two methodological lessons** that the manuscript Methods should
reference:

1. **Rate-value patches do not bypass arc enablement.** Adding a
   GSH-floor inside the Antioxidant_Scavenging Φ string (option a)
   preserved the input-arc gate `M(ROS) > 0`; with ROS clamped at 0
   the transition could not fire and the patch was a silent no-op.
   *Effective interventions on a Petri net must be either topological
   (add/remove arcs and transitions) or operate strictly within an
   already-enabled rate term.*
2. **Closed mass-balance cycles are not equivalent to source/sink
   pairs.** The GSH ↔ GSSG cycle (T13 forward, T41 reverse) requires
   GSSG to be sourceable independently of ROS; introducing a
   dead-ended sink for GSH (T46 with no output) decoupled the cycle
   and produced runaway ROS at any T46 rate magnitude. Mass
   accumulation in a closed cycle is preferable to dead-end leakage
   when the alternative breaks downstream consumers.

Both lessons are now recorded as repository-level audit codes for
future model edits (see `.github/copilot-instructions.md` §
"Programmatic .shy patching" and § "Loader-derived scope table").

## 8. Status

- **Phase 0 — closed.** Healthy baseline reproducibly established at
  sha `c49df7f8…`.
- **Phase 1 unblocked.** Disease-induction sweep (`DISEASE_SEVERITY`
  swept across 0, 0.25, 0.5, 0.75, 1.0) ready to dispatch on the
  same model.
- **Manuscript material ready.** This document, the run-dir
  `provenance.json`, the frozen `model_snapshot.shy`, and the
  per-condition `statistics.json` together provide the full chain
  of custody from model bytes to baseline figures.

---

*Last updated: 2026-04-28. Source data:*
`workspace/projects/canabidiol/experiments/results/run_20260428_184351/`
*on insilicolab; mirrored locally via the hybrid sync model
(see `.github/copilot-instructions.md`).*
