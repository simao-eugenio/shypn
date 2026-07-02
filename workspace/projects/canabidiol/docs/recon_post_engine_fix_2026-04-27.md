# Recon — docs & protocols after engine + Pattern-A migration (2026-04-27)

## 1. Timeline of structural changes (engine + model)

| When | Change | Effect on existing data |
|---|---|---|
| `e20f4911` | Engine: PreemptionCheck rewrite + θ_eff basin-floor fix + JIT removal | All sweeps run **before** this commit have wrong signal-arc semantics |
| `92527ad3` | Pattern A migration **v3 → v3_p7** | Adds ◇ spatial-signal places (`Temperature_factor`, `Age_factor`, `pH_acidosis`, `pH_neutrality`); strips `is_environment_aware`. Models v1/v2/v3/v3_p6/v3_p2/v4_p4 are obsolete topology |
| `722d10cd` | v3_p7: normalise `signal_type` casing | Cosmetic but required for the runtime carrier classifier |
| **uncommitted (today)** | v3_p8 model: rebalance + healthy baseline + chronic dosing defaults | Only v3_p8 has the formalism-clean event/parameter design audited 2026-04-26 |
| **uncommitted (today)** | Engine: 4 signal_flow consumption fixes + stochastic floor() gate fix in `stochastic_behavior.py`, `continuous_behavior.py`, `tau_leaping_engine.py` | All sweeps run before today have stochastic transitions silently blocked at sub-mM concentrations |

## 2. Protocol / data inventory

| Protocol | Pinned model | Latest run | Model still current? | Engine fix applied? | Verdict |
|---|---|---|---|---|---|
| **P1** | `v3` | `run_20260424_005438` (5760 sims) | ❌ pre-Pattern-A | ❌ pre-fix | **Stale** — F1–F8 findings *qualitatively* useful, *quantitatively* unsafe |
| **P2** | `v3_p2` | (never dispatched) | ❌ obsolete | n/a | Re-pair model first |
| **P3** | `v3_p3` (TBD) | — | model never built | n/a | Pending |
| **P4′** | `v4_p4` | `run_20260424_165603` (2700 sims) | ❌ pre-Pattern-A | ❌ pre-fix | **Stale** — bifurcation map needs rerun |
| **P5** | `v3_p5` (TBD) | — | model never built | n/a | Pending |
| **P6** | `v3_p6` | `run_20260425_154907` (8 cells × 30 reps) | ❌ pre-Pattern-A (38 places, 0 ▢ flags) | ❌ pre-fix | **Stale** — disease calibration must rerun against v3_p8 |
| **P7** | `v3_p8` | (never dispatched) | ✅ current | ✅ if dispatched now | **Ready** — first protocol that will produce trustworthy data |

The GUI `simulation_data.csv` analysed 2026-04-26 was a pre-fix GUI run against the new v3_p8 model — explains why `Nrf2_degradation` regressed to 0 firings (continuous signal_flow consumption was buggy in that engine snapshot).

## 3. Document corpus — currency map

### Still valid (model-independent)

- `cbd_drug_discovery_recon.md`
- `cbd_vs_alzheimer_comparison.md`
- `intracellular_ec50_mapping.md`
- `dose_to_maintain_intracellular_cbd.md`
- `literature_validation.md`
- `journal_target_assessment.md`
- `innovation_analysis.md`
- `event_protocol_v3.md` — δ-table is structural, re-validated by v3_p8 audit

### Stale but salvageable (re-run required, framework intact)

- `factorial_sweep_protocol_v2.md`
- `p1_deep_analysis_run_20260424_005438.md` — F1–F8 directional, numerics need re-confirmation
- `mining_report_run_20260421_204933.md` (+ v2/v3)
- `mining_synthesis_v2_vs_v3.md`
- `dynamical_analysis_v1.md`
- `scientific_assessment_v1.md`

### Obsolete → moved to `docs/superseded/`

- `event_protocol_v1.md`
- `event_protocol_v2.md`
- `manuscript_critique_v1.md`
- `manuscript_audit_v1.md`
- `manuscript_critique_v2_insilico_reframing.md`
- `comprehensive_audit_v2.md`
- `baseline_marking_review_v2.md`

## 4. Open scientific questions (post-refactor)

| # | Question | Why it matters |
|---|---|---|
| Q1 | Is the v3_p8 healthy baseline self-stable over 24 h with all event multipliers at zero? | Precondition for every comparative study. P7 tests this. |
| Q2 | Does the Pattern A bridge (▢ → event → ◇ → Φ) reproduce the old `is_environment_aware`/hard-coded-Q10 modulation? | Validates the entire migration. If yes, v3 P1/P4/P6 *qualitative* conclusions transfer. |
| Q3 | Where is the bifurcation boundary for plaque lock-in under v3_p8 + corrected stochastic gate? | P4′ found 93/1152 lock-in cells — probably under-counted by the buggy gate. |
| Q4 | Is `Disease_Severity` dose-response monotone for NH/NFkB/ROS/plaque post-fix? | F2 (Sev=3 % of NH variance) was anomalous → P6 was made to investigate. |
| Q5 | Does CBD efficacy ceiling at LD ≈ 10 still hold post-fix? | P1 F6 drives all dosing recommendations. |
| Q6 | Does Age dominate Severity 2:1 post-fix? | P1 F4 finding; underpins the "age is the strongest determinant" story. |
| Q7 | What is the temperature/Q10 sensitivity of the network with ◇ `Temperature_factor` as the canonical bridge? | Never swept directly. |
| Q8 | Does `evt_apply_thermodynamics` (trigger string `"0.0"`) actually fire? | If not, T/pH/Age effects are silently neutralised. Cheapest test first. |

## 5. Proposed protocol roadmap

| # | Name | Model | Sweep | Reps × Dur | Sims | Answers |
|---|---|---|---|---|---|---|
| **P7** existing | Healthy baseline | `v3_p8` | DSev=0 only | 50 × 24 h | 50 | Q1 |
| **P8** new | Pattern-A self-test | `v3_p8` | TEMP × AGE × PH × DSev=0 | 30 × 4 h | 810 | Q2, Q7, Q8 |
| **P6′** rerun | Disease calibration | `v3_p8` | DSev ∈ {0…3 step 0.5} | 30 × 4 h | 210 | Q4 |
| **P1′** rerun (slim) | Dose × disease (post-fix) | `v3_p8` | DSev × LD × MT × Age | 30 × 4 h | 4320 | Q5, Q6 |
| **P4′′** rerun | Bifurcation refine | `v4_p8` (derive from p8) | LD × DSev × Age | 60 × 4 h | 2700 | Q3 |
| **P9** new | Temperature dose-response | `v3_p8` | TEMP × DSev × LD | 30 × 4 h | 720 | Q7 |

Total ~8800 sims to fully re-establish the result base on a clean foundation.

## 6. Action sequence

1. Commit pending engine fixes — pin engine SHA in subsequent provenance.
2. Commit `v3_p8` model — pin model sha256 in provenance.
3. Verify Q8 (`evt_apply_thermodynamics` actually fires) — quick standalone script.
4. Dispatch P7 — gates everything else.
5. Author P8 + P9 protocol files following the `P<id>__<model>.md` convention.
