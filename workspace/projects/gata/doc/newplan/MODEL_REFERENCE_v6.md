# Model Reference: phase3a_spatial_clean_v6.shy

**File:** `workspace/projects/gata/models/phase3a_spatial_clean_v6.shy`  
**Status:** Active — next batch target  
**Predecessor:** `phase3a_spatial_clean_v5.shy`  
**Created:** March 10, 2026  
**Justification analysis:** [LAYER_ANALYSIS_MAR10.md](LAYER_ANALYSIS_MAR10.md)

---

## What Changed From v5

| Component | v5 | v6 | Justification |
|---|---|---|---|
| T11 `Km_self` (GATA1 self-activation) | `/(5+GATA1_Protein_nuc)` | `/(1+GATA1_Protein_nuc)` | Proteins range 0.09–4 mol; Km=5 puts half-sat above observed maximum → feedback structurally disengaged |
| T12 `Km_self` (PU1 self-activation) | `/(5+PU1_Protein_nuc)` | `/(1+PU1_Protein_nuc)` | Same argument |
| P1 `EPO_external` initial | 0.1 | **1.0** | Batch already ran at EPO=1.0; aligning model to experiment |
| P2 `GCSF_external` initial | 0.1 | **1.0** | GCSF=0.1 gives GCSFR_bound<0.3 → PU1 always at 2.7× excess degradation → 0 MYELOID outcomes structurally |

Everything else is unchanged.

---

## Full Initial Conditions (v6)

| Place | ID | Value | Notes |
|---|---|---|---|
| EPO_external | P1 | **1.0** | ← changed from 0.1 |
| GCSF_external | P2 | **1.0** | ← changed from 0.1 |
| EPOR_free | P3 | 49.02 | |
| EPOR_bound | P4 | 0.49 | |
| EPOR_internalized | P5 | 0.49 | |
| GCSFR_free | P6 | 49.06 | |
| GCSFR_bound | P7 | 0.47 | |
| GCSFR_internalized | P8 | 0.47 | |
| GATA1_Gene | P9 | 1.0 | catalytic |
| PU1_Gene | P10 | 1.0 | catalytic |
| GATA1_mRNA_nuc | P11 | 1.0 | |
| PU1_mRNA_nuc | P12 | 1.0 | |
| GATA1_mRNA_cyto | P13 | 2.0 | |
| PU1_mRNA_cyto | P14 | 2.0 | |
| GATA1_Protein_cyto | P15 | 2.0 | |
| PU1_Protein_cyto | P16 | 2.0 | |
| GATA1_Protein_nuc | P17 | 1.0 | fate readout |
| PU1_Protein_nuc | P18 | 1.0 | fate readout |
| ATP | P19 | 3000 | |
| ADP | P20 | 300 | |
| GTP | P21 | 1500 | |
| GDP | P22 | 273 | |
| Pi | P23 | 1000 | |
| pH_cytoplasm | P24 | 7.2 | |
| pH_nucleus | P25 | 7.5 | controls cross-inhibition Km |
| Mg_cytoplasm | P26 | 1.0 | |
| Temperature | P27 | 310.15 | 37°C |
| pGATA1_nuc | P28 | 0.39 | |
| pPU1_nuc | P29 | 0.3806 | |

---

## Key Rate Functions (v6 — only changed transitions shown)

### T11 — GATA1_transcription (adaptive)
```
0.08 * (1 + 0.5*GATA1_Protein_nuc/(1+GATA1_Protein_nuc))
     / (1+(PU1_Protein_nuc/(0.5*10**(0.5*(pH_nucleus-7.5))))**2)
     * (1 + 2*EPOR_bound/(5+EPOR_bound))
     * exp(-7215.0*(1/Temperature-1/310.15))
```

- Basal: 0.08
- Self-activation: max +50% boost, K_half = 1 molecule
- Cross-inhibition: Hill-2, Km pH-dependent (`0.5 × 10^(0.5×(pHn-7.5))` ≈ 0.5 at pH 7.5)
- EPO boost: max +200% at saturation, K_half = 5 molecules EPOR_bound

### T12 — PU1_transcription (adaptive)
```
0.06 * (1 + 0.5*PU1_Protein_nuc/(1+PU1_Protein_nuc))
     / (1+(GATA1_Protein_nuc/(0.5*10**(0.5*(pH_nucleus-7.5))))**2)
     * (1 + 2*GCSFR_bound/(5+GCSFR_bound))
     * exp(-7215.0*(1/Temperature-1/310.15))
```

- Basal: 0.06 (slight structural ERY bias vs GATA1's 0.08)

All other 30 transition rate functions are unchanged from v5.

---

## Autocatalytic Gain at v6 Km_self=1

$$\text{gain}(G) = 0.08 \times 0.5 \times \frac{1}{(1+G)^2}$$

| G (molecules) | Gain | vs δ≈0.075 | Activation factor |
|---|---|---|---|
| 0 | 0.040 | sub-threshold | ×1.000 |
| 1 | 0.010 | low | ×1.250 |
| 2 | 0.004 | low | ×1.333 |
| 4 | 0.0016 | low | ×1.400 |

Gain alone is sub-threshold, but combined with cross-inhibition suppression of PU1 (improving GATA1 net flux) and receptor-mediated degradation protection, the effective bistability emerges dynamically.

---

## Recommended First Batch (v6)

```
Model:     phase3a_spatial_clean_v6.shy
Replicates: 10–20
Duration:  21600 s (6 hr)
Solver:    TauLeaping_SSA
Seed:      vary per replicate
```

Outcome metrics:
- `GATA1_Protein_nuc / PU1_Protein_nuc` ratio at t=21600 s
- Committed ERY: ratio > 1.5 AND GATA1_nuc > 2.0
- Committed MYELOID: ratio < 0.67 AND PU1_nuc > 2.0
- Collapsed: both < 0.5
- Undecided: all others

---

## Predicted Structural Differences From v5

| Metric | v5 (predicted) | v6 (expected) |
|---|---|---|
| GCSFR_bound steady state | 0.04–0.3 | **0.4–2.0** (10× higher ligand) |
| T26 PU1 degradation factor | 2.0–2.7 | **1.4–1.8** (closer to baseline) |
| MYELOID commitment rate | 0% | **>0%** |
| ERY commitment rate | ~20% | ~30–50% |
| Feedback activation at G=1 | ×1.083 | **×1.250** |

---

## Simulation Campaigns (v6)

### Phase G-v4 — EPO*(pH) Shift, Dense Grid, N=100

**Run:** `run_20260314_142742` → SUPERSEDED. Prior incomplete run; logging stopped.

---

### Phase G-v4b — ⚠️ INVALIDATED (2026-03-15)

**Run:** `run_20260315_113546`  
**Status:** ✅ Completed — 21 conditions × 100 replicates = 2100 replicates  
**Date:** 2026-03-15  
**Invalidation reason:** Protocol execution error — **GCSF_external was 0.001 (model default), not 1.1 as specified**. Duration was 7200 s, not 21600 s.

**What happened structurally:**  
At GCSF=0.001, GCSFR_bound ≈ 0.004–0.005 throughout all replicates. T26 PU1-degradation factor remains at maximum (~2.7×). PU1_Protein_nuc is structurally suppressed; myeloid fate is not accessible. This is the exact failure mode documented in Hard-Won Lesson (v5): *"GCSF=0.1 gives GCSFR_bound<0.3 → PU1 always max-degraded."* At GCSF=0.001 (100× below that) the situation is terminal.

**Results (all uninformative for target questions):**

| Outcome | Value |
|---|---|
| ERY fate | 100% in all 21 conditions |
| MYELOID fate | 0% — structurally impossible at this GCSF |
| EPO* | Unresolvable — no P(ERY) < 1.0 at any tested EPO |
| pH effect on GATA1_nuc | Trend present (+7–14%) but Δ/σ = 0.3–0.7 (not significant at N=100) |
| pH → noise | pH↑ increases CV: 19–23% at pH=7.0, 27–32% at pH=8.0 (real mechanistic observation) |
| Steady-state | Not reached — all replicates ran to 7200 s wall time (2 h only); GATA1 still drifting |
| Energy charge | Stable at EC≈0.940 across all conditions — confirms axiom A4 |
| Compression | 7.1× at min_gap=5 s — compressor correctly configured |

**Secondary observations salvageable from this run:**
- pH↑ amplifies stochastic noise (CV%) in GATA1_nuc: mechanistically meaningful, documents pH-noise coupling independent of GCSF
- Energy charge is completely insensitive to both EPO range 0.395–0.46 and pH 7–8 — confirms EC is not a fate proxy
- pGATA1_nuc is non-monotonic with EPO at pH=7.5 (stochastic artifact at N=100, resolution insufficient)
- 7.1× compression with min_gap=5 s is well-calibrated for this model

---

### Phase G-v5 — ⚠️ INVALIDATED (2026-03-15, pre-run analysis)

**Status:** Cancelled before execution.  
**Invalidation reason:** Protocol error in EPO range.

**What went wrong:**  
At GCSF=1.1, the net-flux balance point (EPO*) is ≈ **0.52 mM** (derived from rate function analysis).  
The planned EPO range 0.430–0.451 lies entirely **below** EPO*, where PU1 net flux exceeds GATA1 net flux by 8–11× throughout. Result: structurally MYE-biased all conditions — same failure mode as Phase G-v4b but reversed sign.

**Net flux analysis (GCSF=1.1, receptor kinetics):**

| EPO (mM) | GATA1_net | PU1_net | PU1/GATA1 | Expected |
|---|---|---|---|---|
| 0.43 | 0.0911 | 0.1010 | 1.11× | MYE-biased |
| 0.45 | 0.0932 | 0.1010 | 1.08× | MYE-biased |
| **0.52** | **0.1011** | **0.1010** | **≈1.00×** | **Transition** |
| 0.65 | 0.1082 | 0.1010 | 0.93× | ERY-biased |
| 1.10 | 0.1278 | 0.1010 | 0.79× | ERY-biased |

Method: EPOR_bound = 50×EPO/(10+EPO); GCSFR_bound = 50×1.1/(10.06+1.1) = 4.93; net_flux = basal × t_factor(b)/d_factor(b) where t_factor(b)=1+2b/(5+b), d_factor(b)=1+2(1−b/(0.5+b)).

---

### Phase G-v6 — Corrected EPO*(pH) Sweep — EPO range straddles EPO*

**Status:** 📋 Planned — next run  
**Date:** TBD  
**Fixes from Phase G-v5:**
1. EPO range expanded to **straddle EPO*≈0.52** (previously entire range was below EPO* on MYE side)
2. GCSF_external fixed at **1.1** (must be explicit property override — never rely on model default)
3. Duration **21600 s** (6 h) to allow steady state — not 7200 s
4. N=100 for first corrected run; upgrade to 500 once P(ERY) sigmoid is located

**Net flux prediction (GCSF=1.1 fixed):**

| EPO (mM) | GATA1/PU1 bias | P(ERY) estimate |
|---|---|---|
| 0.30 | PU1 wins (−0.19×) | ~20% |
| 0.40 | PU1 wins (−0.10×) | ~35% |
| 0.47 | PU1 wins (−0.02×) | ~47% |
| **0.52** | **Balanced** | **~50%** |
| 0.57 | GATA1 wins (+0.04×) | ~53% |
| 0.65 | GATA1 wins (+0.07×) | ~59% |
| 0.80 | GATA1 wins (+0.16×) | ~68% |
| 1.10 | GATA1 wins (+0.27×) | ~79% |

**Protocol:**

| Parameter | Values |
|---|---|
| EPO_external (mM) | 0.30, 0.40, 0.47, 0.52, 0.57, 0.65, 0.80, 1.10 (8 values straddling EPO*≈0.52) |
| pH_nucleus | 7.0, 7.5, 8.0 (3 values) |
| GCSF_external (mM) | **1.1 (fixed — MUST be set explicitly as property override, NOT model default)** |
| Replicates / condition | 100 |
| Total replicates | 2400 (8 × 3 × 100) |
| Duration | **21600 s (6 h)** |
| Solver | TauLeaping_SSA |
| Expected wall time | ~14–16 h @ 10 workers |

**Critical pre-run checklist:**
- [ ] Verify `GCSF_external` appears explicitly in the property sweep overrides (not relying on model default)
- [ ] Confirm `final_GCSF_external` ≈ 1.1 in first completed experiment's `mean_final_state.csv`
- [ ] Confirm `final_GCSFR_bound` > 0.3 in at least one replicate (`replicates.csv`)
- [ ] After first ~10 replicates of EPO=0.30 condition: confirm some replicates show MYELOID outcome; if all still ERY → stop, investigate
- [ ] After first ~10 replicates of EPO=1.10 condition: confirm some replicates show ERY outcome; if all still MYE → stop, investigate
- [ ] If all first 10 replicates still give ERY, **stop the sweep** — something is wrong

**Expected outcomes with GCSF=1.1:**
- GCSFR_bound ≈ 0.4–2.0 (vs 0.004 in v4b)
- T26 PU1-degradation factor ≈ 1.4–1.8 (vs ~2.7 in v4b)
- MYELOID outcomes should appear at low EPO end; ERY should dominate at high EPO end
- P(ERY) should form a sigmoidal curve vs EPO → extract EPO*(pH)

**Research questions answered:**
- **RQ-v6-5**: What EPO:GCSF ratio gives >50% ERY?
- **RQ-pH**: Is EPO* shifted across pH 7.0–8.0 by ≥ half the EPO step (≥1.5 mM)?

**Analysis plan:**  
For each pH, fit logistic P(ERY) = 1/(1+exp(-k(EPO−EPO*))) and extract EPO*.  
If the 8-value EPO grid shows all 100% ERY or all 0% ERY (no sigmoid), widen the range before committing to N=500.

**Outcome criteria (unchanged from v6 recommendation):**
- ERY: `GATA1_Protein_nuc / PU1_Protein_nuc` > 1.5 AND `GATA1_Protein_nuc` > 2.0
- MYELOID: ratio < 0.67 AND `PU1_Protein_nuc` > 2.0
- Collapsed: both < 0.5
- Undecided: all others
