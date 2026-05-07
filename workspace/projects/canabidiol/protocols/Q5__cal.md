# Protocol Q5 — Age-dependent CBD mechanism switch

> **Pairing.** Model: [`models/canabidiol-q1-testable-pk-energy.shy`](../models/canabidiol-q1-testable-pk-energy.shy)
> (calibrated, post B1+B2+B3+B7).

## Hypothesis

CBD's **dominant neuroprotective mechanism shifts with age** — anti-
inflammatory (PPARγ ⊣ NFκB arm) in younger cohorts; antioxidant
(Nrf2 / HO-1 / SOD / GSH arm) in older cohorts. The shift is driven
by the spatial signal `Age_factor` (◇), set by
`evt_apply_thermodynamics` from the ▢ `AGE` parameter, which
multiplies several Φ rates including `Basal_ROS_Production` (T14)
and `Antioxidant_Scavenging` (T13). EC₅₀ for NH rescue rises with
age; the partial-correlation between MAINT and `NFkB_p65`
suppression weakens, while the partial-correlation between MAINT
and `Glutathione` retention strengthens.

## Environment panel

| Place | Value | Units | Notes |
|---|---:|---|---|
| `DISEASE_SEVERITY` | **2.0** | level | clear cascade ignition without saturating |
| `LOADING_DOSE` | **10** | µM | bolus at t = 0 |
| `MAINT_DOSE` | **swept** | µM | dose-response axis |
| `DOSE_INTERVAL` | **21600** | s | 6 h cadence |
| `TEMPERATURE` | 310.15 | K | |
| `AGE` | **swept** | y | mechanism-switch axis |
| `PH` | 7.4 | — | |

## Viability panel — sweep plan

**Mode:** Factorial • **Replicates:** 30 • **Duration:** 604800 s
(7 d) • **Termination:** time

| Sweep parameter | Path | Values | Cells |
|---|---|---|---:|
| `[param] AGE` | `AGE.initial_marking` | `[30, 60, 75, 85]` | 4 |
| `[param] MAINT_DOSE` | `MAINT_DOSE.initial_marking` | `[0.0, 0.1, 0.5, 1.0, 2.0, 5.0]` | 6 |

**Cells:** 24 + Baseline = 25 • **Total sims:** 25 × 30 = **750**

## Acceptance criteria

For each AGE row, compute Hill-fit EC₅₀ (NH vs MAINT_DOSE) and
partial Pearson correlations on the per-replicate endpoint table:

| Quantity | Target |
|---|---|
| `EC₅₀(NH)` monotone-increasing in AGE | strict |
| `EC₅₀(AGE=85) / EC₅₀(AGE=30) ≥ 2` | dose ratio (in vivo evidence ≈ 3) |
| `partial_corr(MAINT, NFkB \| Aβ, ROS) at AGE=30` | < at AGE=85 |
| `partial_corr(MAINT, GSH \| Aβ, NFkB) at AGE=85` | > at AGE=30 |
| `Glutathione` endpoint at MAINT=5 | non-increasing in AGE (Rahimifard 2017) |

**Conservation check:** `Microglia_M1 + M2` constant within each
replicate.

## Falsification

- EC₅₀ flat across AGE ⇒ Pattern-A bridge for `Age_factor` not
  reaching the relevant Φ rates; verify
  `evt_apply_thermodynamics` fires and that `Age_factor` appears
  in T13 / T14 / T20 rate strings.
- `Glutathione` endpoint independent of AGE ⇒ Nrf2 arm not
  age-coupled; missing `Age_factor` term in
  `Nrf2_ARE_transcription` or `Glutathione_Reductase`.
- Mechanism-shift partial correlations equal across AGE ⇒ the two
  CBD arms are not differentially age-modulated; finding null,
  manuscript reports as such.

## Wet-lab anchors

- Zhang et al. 2015 — Nrf2 activity declines with age.
- Rahimifard et al. 2017 — GSH synthesis ↓ 20–30 % between age 50
  and 80.
- Cassano et al. 2020 (*Front Pharmacol*) — CBD age-dependent
  efficacy review.

## Manuscript section

New §results-Q5 in [`manuscript/main_v3.tex`](../manuscript/main_v3.tex)
— previously absent (age was not a swept axis in the v3 manuscript
sweeps).

## Results

⏸ Pending dispatch.
