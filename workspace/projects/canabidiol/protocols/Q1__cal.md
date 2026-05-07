# Protocol Q1 — CBD IC₅₀ on NFκB activation

> **Pairing.** Model: [`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
> (calibrated, post **B1+B2+B3+B7**: NADPH/NADP+ capacity=∞;
> TNFa→Cytokine_Degradation re-typed `normal`; per-cytokine
> first-order degradation transitions T50–T52; new
> `NFkB_dephosphorylation` (T53) closing the IκB cycle.)
> Validated `run_20260507_151546`: NH=91, NFkB_p65≈0.13,
> cytokines O(10⁻²), microglia M2-dominant.

## Hypothesis

CBD inhibits NFκB p65 activation with a half-maximal inhibitory
concentration in the **0.05 – 1 µM** maintenance-dose range, monotone
across the full sweep, consistent with Kozela 2010 (BV-2 microglia
IC₅₀ ≈ 1 µM) and Esposito 2006 (PC12 NFκB significant at 1 µM).
The mechanism is the PPARγ ⊣ NFκB arm
(`PPARg_inhibits_NFkB`, T9) gated by `CBD_activates_PPARg` (T10).

## Environment panel — parameter places

| Place | Value | Units | Notes |
|---|---:|---|---|
| `DISEASE_SEVERITY` | **1.0** | level | mid-disease driver (avoids cusp at 2; produces clear NFκB ignition without saturating) |
| `LOADING_DOSE` | **10** | µM | standard bolus at t = 0 |
| `MAINT_DOSE` | **swept** | µM | see Viability table |
| `DOSE_INTERVAL` | **21600** | s | 6 h cadence (matches v3 manuscript convention) |
| `TEMPERATURE` | 310.15 | K | physiological |
| `AGE` | 72 | y | adult cohort |
| `PH` | 7.4 | — | normoxic |

## Viability panel — sweep plan

**Mode:** Single-axis (`MAINT_DOSE`) • **Replicates:** 30 •
**Duration:** 86400 s (24 h) • **Termination:** time

| Sweep parameter | Path | Values | Cells |
|---|---|---|---:|
| `[param] MAINT_DOSE` | `MAINT_DOSE.initial_marking` | `[0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]` | 8 |

**Cells:** 8 + Baseline = 9 • **Total sims:** 9 × 30 = **270**

The grid spans three decades (0.05 → 5 µM) with a tighter low-end to
locate IC₅₀; 24 h is sufficient for NFκB to reach steady state under
LOADING_DOSE alone (PK half-life ≈ minutes) without committing to a
7-day chronic-dosing horizon.

## Acceptance criteria

Endpoint mean NFκB_p65 over 30 replicates per cell:

| Cell | Target | Tolerance |
|---|---|---|
| `MAINT_DOSE = 0` | ≥ 5 (clear NFκB ignition under DSEV=1) | −2 |
| `MAINT_DOSE = 5` | ≤ 0.5 (saturating suppression) | +0.3 |
| **Monotone-decreasing in MAINT_DOSE** | strict | none — single inversion fails Q1 |
| Hill IC₅₀ fit | located in (0, 1] µM | report 95 % CI |

**Conservation check:** `Microglia_M1 + Microglia_M2 = const` (±2)
across all cells.

## Falsification

- If NFκB_p65 = 0 at every cell ⇒ disease cascade not igniting at
  DSEV=1 (Q1 ↔ Q3 coupling broken; check `Abeta_activates_IKK` and
  `IKK_phosphorylates_IkB` firings).
- If NFκB_p65 monotone but plateau is high (> 5) at MAINT_DOSE = 5 ⇒
  CBD→PPARγ→NFκB arm under-powered (T10 rate constant) — patch model.
- If response is bistable (bimodal endpoint distribution) ⇒ note as
  Q1-bonus finding; deserves higher-replicate refinement.

## Wet-lab anchors

- Kozela et al. 2010 (BV-2 microglia, LPS-stimulated; CBD IC₅₀ ≈ 1 µM
  on NFκB DNA-binding).
- Esposito et al. 2006 (PC12; significant NFκB suppression at 1 µM).
- Juknat et al. 2013 (BV-2 transcriptomic confirmation).

## Manuscript section

Replaces former `Q1-final` / `Q5-final` content in
[`manuscript/main_v3.tex`](../manuscript/main_v3.tex) §results-Q1.

## Results

⏸ Pending dispatch.
