# Protocol Q1 — CBD IC₅₀ on NFκB activation

> **Pairing.** Model: [`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
> (calibrated, post **B1+B2+B3+B7 + Calibration v2 (C1+C2+C4)**:
> NADPH/NADP+ capacity=∞; TNFa→Cytokine_Degradation re-typed `normal`;
> per-cytokine first-order degradation transitions T50–T52;
> `NFkB_dephosphorylation` (T53) k=1e-3/s (IκB rebind t½ ≈ 12 min,
> Hoffmann 2002); `Antioxidant_Scavenging` split into SOD/HO1 (T13)
> + GSH (T54) so SOD baseline does not double-charge GSH consumption;
> `NFkB_p65 → APP_Transcription` arc converted from `signal_flow`
> w=0.01 to `test` arc (NFκB is a transcription factor, not a substrate).
> Conservation post-patch: NFκB pool = 55 (no leaks); GSH+GSSG = 80
> (residual +0.02 source via `Nrf2_ARE_transcription`, accepted as
> coarse-grained de novo synthesis term — see C3 in audit).

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
| `DOSE_INTERVAL` | **3600** | s | 1 h cadence — sustains plasma > 0.5 µM throughout (PK t½ ≈ 17 min); 6 h cadence allows full washout between doses, masking dose-response |
| `TEMPERATURE` | 310.15 | K | physiological |
| `AGE` | 72 | y | adult cohort |
| `PH` | 7.4 | — | normoxic |

## Viability panel — sweep plan

**Mode:** Single-axis (`MAINT_DOSE`) • **Replicates:** 30 •
**Duration:** 14400 s (4 h) • **Termination:** time •
**Recording tier:** G3 (per-step capture of the active PK window)

| Sweep parameter | Path | Values | Cells |
|---|---|---|---:|
| `[param] MAINT_DOSE` | `MAINT_DOSE.initial_marking` | `[0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]` | 8 |

**Cells:** 8 + Baseline = 9 • **Total sims:** 9 × 30 = **270**

The grid spans three decades (0.05 → 5 µM) with a tighter low-end to
locate IC₅₀. **Horizon revised from 24 h → 4 h** based on
`run_20260507_161636` trajectory analysis: CBD plasma t½ ≈ 17 min, so
at 24 h the network endpoint observes only the dead PK tail and is
flat across MAINT (B3-amplified loss of dose-response). At 4 h with
DOSE_INTERVAL=1 h, plasma sustains 0.5 – 3 µM through 4 maintenance
pulses, and recording at the τ-leap step granularity preserves the
NFκB transient-decay envelope (post-C4 t½ ≈ 12 min) where the IC₅₀
separation is observable.

## Acceptance criteria

Readout = mean NFκB_p65 trajectory over 30 replicates per cell,
integrated AUC over t ∈ [60 s, 14400 s] (skips initial install
transient).

| Cell | Target | Tolerance |
|---|---|---|
| `MAINT_DOSE = 0` | AUC ≥ 5 µM·s × 14340 s (sustained NFκB drive under DSEV=1) | −30 % |
| `MAINT_DOSE = 5` | AUC ≤ 30 % of MAINT=0 baseline | — |
| **Monotone-decreasing AUC in MAINT_DOSE** | strict | none — single inversion fails Q1 |
| Hill IC₅₀ fit on AUC | located in (0, 1] µM | report 95 % CI |

**Conservation checks (must hold in EVERY trajectory, all cells):**
- `Microglia_M1 + Microglia_M2 = 45` (±2)
- `NFkB_p65 + NFkB_IkB = 55` (±1)
- `NADPH + NADP_plus = 110` (±1)
- `Glutathione + GSSG ≥ 60` throughout 4 h (post-C1 fix; was
  dropping to 0.93 within 10 min pre-fix)

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
