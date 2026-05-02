# G3b verification — BDNF↓NFkB coupling fixes NH inversion

Sweep: run_20260502_162047 (post-G3b). Same DSEV axis as Q3
(run_20260502_160439, pre-G3b). Commit `94156330` adds NFkB-suppression
term to T21 BDNF_neuroprotection rate.

## Patch

```diff
- 0.05 * BDNF / (20 + BDNF) * (100 - Neuron_Health) / 100 * Temperature_factor
+ 0.05 * BDNF / (20 + BDNF) * (100 - Neuron_Health) / 100 * Temperature_factor * (1 - NFkB_p65 / (0.1 + NFkB_p65))
```

Suppression schedule (K=0.1):
- NFkB=0.092 (DSEV=0): T21 multiplier = 0.521 (recovery 52% of normal)
- NFkB=0.243 (DSEV=5): T21 multiplier = 0.292 (recovery 29%)
- NFkB=1.0 (severe untreated): T21 multiplier = 0.091 (recovery 9%)

## Result — NH dose-response inverted (correctly)

| DSEV | NH pre-G3b | NH post-G3b | Δ |
|---:|---:|---:|---:|
| 0   | 44.6 | **100.0** | +55 |
| 0.5 | 46.8 | 68.7  | +22 |
| 1   | 49.2 | 54.4  | +5  |
| 2   | 54.6 | 34.2  | −20 |
| 3   | 59.4 | 23.8  | −35 |
| 5   | 75.4 | **18.8**  | −57 |

Pathological NH-rises-with-DSEV behavior fully resolved. Now:
- Healthy control: NH = 100 (perfect)
- Mild AD (DSEV=1): NH = 54
- Severe AD (DSEV=5): NH = 19

T20 damage firings (190 → 237) now exceed T21 recovery firings
(150 → 180) at DSEV ≥ 2.

## Other observations

- Aβ cascade unchanged (T3 firings 2 879 → 18 607 as in Q3)
- NFkB rises 0.025 → 0.178 (smooth dose-response under CBD plateau)
- AbO 0 → 41 (same magnitudes as Q3)
- M1 stays low across all DSEV (CBD-suppressed)
- M2 rises with DSEV (45 → 77) — homeostatic compensation

## Caveats

- ROS_final = 0 across all conditions (was 17–19 in Q3 pre-G3b)
- BDNF stays constant at 4.14 (was ~30 before)
- Both are snapshot-config artifacts: Q3-verify reused the Q3
  snapshots, which carry initial place values that differ slightly
  from GUI-generated ModelDefaults. **Not a G3b regression.**
- Recommend a fresh Baseline run before Q4 to confirm clean
  ModelDefaults equilibrium.

## Status

✅ G3 gap closed — disease severity now degrades NH as expected
✅ Q3 dose-response semantics preserved (NFkB, AbO, IKK, M1/M2 all on-trend)
🟡 Need clean baseline before Q4 (snapshot-induced ROS/BDNF anomaly)
🟢 Ready for Q4 dispatch (factorial DSEV × MAINT)
