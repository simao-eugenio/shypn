# Protocol Q3 — Microglial M1/M2 polarisation under CBD

> **Pairing.** Model: [`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
> (calibrated, post B1+B2+B3+B7).

## Hypothesis

CBD shifts the microglial M1↔M2 equilibrium toward M2 with monotone
dose-response, mediated by `M2_to_M1_polarization` (T17, suppressed
by lower TNFα/Aβ_Oligomer when CBD blocks the cascade) and
`M1_to_M2_resolution` (T18, accelerated by anti-inflammatory tone).
At fixed disease drive, increasing MAINT_DOSE moves the M1/(M1+M2)
ratio from > 0.5 (untreated) toward < 0.1 (saturating CBD), with
**P-invariant** `M1 + M2 = const` preserved at every cell.

## Environment panel

| Place | Value | Units | Notes |
|---|---:|---|---|
| `DISEASE_SEVERITY` | **2.0** | level | populates M1 pool |
| `LOADING_DOSE` | **10** | µM | bolus at t = 0 |
| `MAINT_DOSE` | **swept** | µM | see Viability table |
| `DOSE_INTERVAL` | **21600** | s | 6 h cadence |
| `TEMPERATURE` | 310.15 | K | |
| `AGE` | 72 | y | |
| `PH` | 7.4 | — | |

## Viability panel — sweep plan

**Mode:** Single-axis (`MAINT_DOSE`) • **Replicates:** 30 •
**Duration:** 604800 s (7 d) • **Termination:** time

| Sweep parameter | Path | Values | Cells |
|---|---|---|---:|
| `[param] MAINT_DOSE` | `MAINT_DOSE.initial_marking` | `[0.0, 0.1, 0.5, 1.0, 2.0, 5.0]` | 6 |

**Cells:** 6 + Baseline = 7 • **Total sims:** 7 × 30 = **210**

Long horizon (7 d) lets the polarisation pool reach steady state
under chronic dosing.

## Acceptance criteria

| Quantity | Target | Tolerance |
|---|---|---|
| `M1+M2 conservation` | constant per replicate | ±2 tokens (stochastic noise) |
| `M1/(M1+M2) at MAINT=0` | ≥ 0.40 | −0.10 |
| `M1/(M1+M2) at MAINT=5` | ≤ 0.10 | +0.05 |
| Monotone-decreasing in MAINT | strict | none |
| `Microglia_M2 > Microglia_M1` for MAINT ≥ 0.5 | true | — |

**Cross-check:** the M1 trajectory should track the cytokine load
(TNFα + IL1β); plot M1(t) vs IL1β(t) per replicate; r > 0.7 expected.

## Falsification

- M1+M2 not conserved ⇒ topology bug — extra source/sink on the
  microglia pool. Audit T17/T18 arc weights.
- M1/(M1+M2) flat across MAINT axis ⇒ CBD pathway not coupled to
  polarisation; check `Abeta_activates_IKK` → `IKK_phosphorylates_IkB`
  → `NFkB_p65` → ... → `M2_to_M1_polarization` rate dependency.
- Reversed dose-response (M1 fraction *increases* with CBD) ⇒ sign
  error somewhere in the cascade; fix before any other Q-protocol.

## Wet-lab anchors

- Orihuela et al. 2016 (*Br J Pharmacol*) — microglial polarisation
  states reviewed.
- Martín-Moreno et al. 2011 (APP/PS1 mice) — CBD shifted microglia to
  M2 phenotype in vivo.
- Juknat et al. 2013 (BV-2 transcriptomic) — CBD anti-inflammatory
  signature.

## Manuscript section

New §results-Q3 in [`manuscript/main_v3.tex`](../manuscript/main_v3.tex)
— previously absent (microglia were not a primary endpoint in v3).

## Results

⏸ Pending dispatch.
