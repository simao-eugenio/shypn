# What administered CBD dose maintains intracellular CBD in the working window?

**Source:** combined ingestion of `run_20260421_204933` (157 cond, CBD 0–12 µM) +
`run_20260422_173323` (49 cond, CBD 0–40 µM, Age 75 / 85 only).
**Script:** `workspace/projects/canabidiol/scripts/external_to_intracellular_ec50.py`
**Full report:** [intracellular_ec50_mapping.md](intracellular_ec50_mapping.md)

## 1. Two reference numbers per (Age, pH) cell

For each demographic cell we report **two intracellular CBD targets**:
- **EC50_intra** = intracellular CBD concentration giving half-max neuron-health rescue (`E0 + (Emax−E0)/2`)
- **EC90_intra** = intracellular CBD concentration giving 90 % of max rescue

…and the **administered (set) extracellular dose** required to maintain each, derived from the linear transfer fit `CBD_intracellular_final = k · set_dose` with **k = 0.454** (uniform across the entire grid — the transfer is age- and pH-independent because the mass-balance constants T28/T29/T30/T31 in the model are not modulated by Age or pH).

## 2. Therapeutic-window table (pH 7.4)

| Age | EC50_intra (µM) | EC90_intra (µM) | **set dose @ EC50_intra (µM)** | **set dose @ EC90_intra (µM)** | Hill n |
|---:|---:|---:|---:|---:|---:|
| 55 | 0.35 | 1.15 | **0.77** | **2.55** | 1.83 |
| 65 | 0.92 | 3.92 | **2.02** | **8.64** | 1.51 |
| 75 | 2.17 | 10.85 | **4.77** | **23.92** | 1.36 |
| 85 | 6.25 | 63.87 | **13.77** | **140.79** *(extrapolated)* | 0.95 |

Hill n drops from 1.83 (Age 55) to 0.95 (Age 85) — the dose–response loses cooperativity with age, which dilates the EC50→EC90 window from ~3× (Age 55) to ~10× (Age 85). For Age 85 the 90 % target sits well past the swept ceiling and would require pharmacologically unrealistic exposure.

## 3. Acidosis effect on the maintenance dose (set dose @ EC50_intra)

| Age | pH 6.6 | pH 7.0 | pH 7.4 |
|---:|---:|---:|---:|
| 55 | 0.99 | 0.88 | 0.77 |
| 65 | 3.72 | 2.61 | 2.02 |
| 75 | 7.10 | 5.85 | 4.77 |
| 85 | 42.84 | 23.20 | 13.77 |

Acidosis (pH 6.6 vs 7.4) raises the maintenance dose by ~30 % at younger ages, ~50 % at Age 75, and ~3× at Age 85. The Age-85 / pH-6.6 cell has a wide bootstrap CI on EC50_intra (range 9.2–64.8 µM) — the demographic cell where therapy is least confident.

## 4. Direct answer

The **administered extracellular CBD dose** required to keep intracellular CBD at the half-max neuroprotective level (`EC50_intra`) is:

| Cohort (pH 7.4) | minimum effective set dose | upper protective set dose |
|---|---:|---:|
| Healthy young (Age 55)         | **~0.8 µM**  | ~2.5 µM |
| Mid-life (Age 65)              | **~2.0 µM**  | ~9 µM |
| Mild aging (Age 75)            | **~4.8 µM**  | ~24 µM |
| Advanced aging (Age 85)        | **~14 µM**   | ~140 µM (out of swept range) |

Under acidosis (pH 6.6) all numbers rise ~30–200 %; under alkalosis (pH 7.4) they're at the lower bound shown.

## 5. Mechanistic interpretation of the transfer constant

The transfer is linear with **k = 0.454** intracellular µM per set‐dose µM, identical across all 12 (Age, pH) cells. This is not an empirical coincidence — the model's transport reactions are first-order:
- **T28**: `0.0008 · CBD_extracellular · 2^((T−37)/10)` (uptake)
- **T29**: `0.0003 · CBD_intracellular · 2^((T−37)/10)` (efflux)
- **T30 / T31**: 0.00003 / 0.00005 first-order clearance (extra / intra)
- **T1, T15, T19**: receptor-binding consumption of extracellular CBD

The temperature factor (Temperature = 310.15 K → 37 °C in every condition) is constant across the swept grid, so the steady-state intra/set ratio reduces to a fixed ratio of these rate constants. **k = 0.454 is therefore a model-level invariant**, not a fitted free parameter that could vary between patients in this representation.

This means the **only source of dose-response variation** across the grid is the *intracellular* response curve (Nrf2/Keap1, NFkB, microglia polarisation), not the transport. Modulating dose-need by patient subgroup will therefore require either (a) widening the model to include age/pH-dependent transport (e.g. lowered ATP-driven efflux in older cells, or pH-dependent membrane partitioning) or (b) accepting that the model's age/pH effects are entirely downstream-pharmacodynamic.

## 6. Practical recommendation

For a manuscript stating an "external CBD dose to keep intracellular CBD in the working window", report (pH 7.4 column, EC50_intra → EC90_intra):

- **Age 55:** 0.77 → 2.55 µM administered ⇒ intra 0.35 → 1.15 µM
- **Age 65:** 2.02 → 8.64 µM administered ⇒ intra 0.92 → 3.92 µM
- **Age 75:** 4.77 → 23.92 µM administered ⇒ intra 2.17 → 10.85 µM
- **Age 85:** 13.77 → ~140 µM administered ⇒ intra 6.25 → 63.87 µM (warn: EC90 outside swept range, Hill n < 1)

If the manuscript needs a single defensible dose per cohort, **the EC50_intra column** is the right choice — it sits inside the swept range for every cell (max 13.8 µM admin, well below the 40 µM ceiling of the v3 sweep) and the bootstrap CIs are reasonable.
