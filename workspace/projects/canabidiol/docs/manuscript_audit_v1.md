# Manuscript & Model Audit Report v1

**Date:** 2026-04-16  
**Scope:** `main.tex` (manuscript) + `cbd_ad_neuroprotection_v1.shy` (model)  
**Method:** Code inspection, simulation re-runs, conservation law checks, biological plausibility review

---

## Severity Legend

| Level | Meaning |
|-------|---------|
| **CRITICAL** | Biologically absurd or mathematically wrong — must fix before submission |
| **SEVERE** | Model artifact presented as biology — misleads readers |
| **MODERATE** | Unsupported claim or missing caveat — reviewer will flag |
| **MINOR** | Inaccuracy or oversight — fix in revision |

---

## CRITICAL Issues

### C1. NFkB Mass Conservation Violation (Model Bug)

**What:** P8 (NFkB_IkB) + P9 (NFkB_p65) should be conserved at 80 (initial pool). Actual values:

| CBD (µM) | P8 | P9 | Total | Expected |
|-----------|------|-------|-------|----------|
| 0 | 0.00 | 80.00 | **80.00** | 80 ✓ |
| 15 | 5.33 | 94.67 | **100.00** | 80 ✗ |
| 25 | 11.85 | 88.15 | **100.00** | 80 ✗ |
| 45 | 52.14 | 47.86 | **100.00** | 80 ✗ |
| 65 | 99.76 | 0.24 | **100.00** | 80 ✗ |

With capacity removed (P9 cap→∞), CBD=15 gives P9=877 (total=882). The capacity ceiling at 100 *masks* a runaway token creation.

**Root cause:** The ODE C code has correct stoichiometry (d(P8+P9)/dt = 0 verified in generated code), yet the simulation engine produces 25% spurious inflation. The violation persists in both tau-leaping and pure SSA modes. Likely an engine-level interaction between ODE acceleration and capacity enforcement, or double-counting between ODE and propensity system paths. Requires engine-level debugging.

**Impact on manuscript:** Table 1 reports NFkB-p65 = 94.67 at CBD=15 µM — *higher* than the 80.00 at CBD=0. This means low-dose CBD **paradoxically increases** NFkB, which is biologically nonsensical and contradicts the anti-inflammatory narrative. All NFkB-p65 values at CBD>0 are inflated by this bug.

**Fix:** Investigate SHYpn engine token accounting for the T6/T9 loop. Verify that continuous transitions handled by ODE acceleration are NOT also fired by the tau-leaping/propensity system. As a model-level workaround, consider setting P9 capacity = 80 (matching conservation), but this doesn't fix the root cause.

---

### C2. Timescale Conflation — 6 Hours Simulates Decades of Disease

**What:** The model runs for 6 hours (21,600 s) and produces:
- Aβ plaque: 0 → 58,864 in 6 hours (plaques form over **5–20 years** in vivo)
- Neuron Health: 100 → 15.54 (85% neuronal death in 6 hours; AD neurodegeneration takes **5–15 years**)
- All cytokines hit capacity ceiling within **35 seconds** (!)
- ROS hits capacity in **52 seconds**
- γ-Secretase hits capacity in **4 seconds**
- IKK hits capacity in **17 seconds**

**Impact on manuscript:** The Results section presents 6-hour endpoints as if they represent AD pathological steady states. The phrase "acute pharmacodynamic responses" in Limitations is insufficient — the model doesn't capture acute pharmacodynamics either. It compresses years of disease into seconds, making all kinetic parameters biologically meaningless.

**Fix:** Either (a) rescale all rate constants to produce biologically realistic timescales (plaque formation over months-years, neurodegeneration over years), or (b) explicitly reframe the model as a "qualitative topology explorer" that maps pathway interactions without quantitative timescale claims. Option (b) requires rewriting the Experimental Guidance section to remove all time-dependent claims.

---

### C3. Concentration Units Are Arbitrary Tokens, Not Millimolar

**What:** The manuscript uses "mM" throughout but the values are Petri net token counts, not actual millimolar concentrations:

| Species | Model Value | Physiological Value | Discrepancy |
|---------|-------------|-------------------|-------------|
| TNFα | 200 mM | ~0.6 pM (10–100 pg/mL) | 3 × 10¹¹ fold |
| ROS (H₂O₂) | 500 mM | ~1–10 nM | 5 × 10¹⁰ fold |
| BDNF | 100 mM | ~0.04 nM (1–10 ng/mL) | 2.5 × 10⁹ fold |
| Aβ plaque | 58,864 mM | ~10–50 µg/g tissue | Incommensurable |
| NFkB-p65 | 80–100 mM | ~1–10 nM nuclear | ~10¹⁰ fold |

**Impact on manuscript:** Using "mM" implies calibrated biochemical concentrations. Readers and reviewers will immediately note that TNFα at 200 mM is 3.4 kg/L of protein. The Limitations section mentions this briefly ("Petri net marking units") but Tables 1–5 all use "mM" without qualification.

**Fix:** Replace "mM" with "a.u." (arbitrary units) or "tokens" throughout all tables and text. Add explicit statement in Methods that markings represent relative pathway activity levels, not calibrated concentrations.

---

### C4. Age ≥ 75: Complete Neuronal Death in 6 Hours

**What:** At CBD=0, Neuron Health drops to exactly 0.00 at ages 75 and 90 within 6 hours:

| Age | NH (6h) |
|-----|---------|
| 40 | 59.23 |
| 55 | 33.02 |
| 65 | 15.54 |
| 75 | **0.00** |
| 90 | **0.00** |

At age 75, the neurotoxicity rate T20 is amplified by factor (1 + 0.02×10) = 1.2, which is enough to drive NH from 100 to 0 in 6 hours. The neuroprotection transition T21 depends on BDNF (~10⁻⁵ at CBD=0), which is negligible. So T20 is essentially an unopposed drain at rate ~0.01/s.

The miracle recovery: CBD=25 µM restores NH from 0.00 to 99.78 at age 90 (Table 5). This implies **complete regeneration** of destroyed neurons, which is biologically impossible — dead neurons in the adult brain do not regenerate.

**Impact on manuscript:** The claim "CBD rescues neurons across all ages" (Section 3.9, Table 5) implies reversible neurodegeneration, contradicting basic neuroscience. Reviewer will immediately flag NH=0→99.78 as absurd.

**Fix:** Reframe "Neuron_Health" as a damage/repair score rather than neuron count. Add a minimum threshold below which damage is irreversible (e.g., if NH < 10, recovery rate = 0). Or model neurons as non-regenerating (remove the T21 source pathway for severe damage).

---

## SEVERE Issues

### S1. Capacity Ceilings Masquerade as Biological Dynamics

**What:** Many species hit their capacity ceiling within the first minute and stay there for 99.7% of the simulation:

| Species | Time to Ceiling | Ceiling | Duration at Ceiling |
|---------|----------------|---------|-------------------|
| γ-Secretase | 4.3 s | 100 | 99.98% of sim |
| IKK | 17.3 s | 50 | 99.92% |
| TNFα | 34.6 s | 200 | 99.84% |
| GSH | 38.9 s | 200 | 99.82% |
| ROS | 51.8 s | 500 | 99.76% |
| NFkB-p65 | 43.2 s | 80→100* | 99.80% |

*The NFkB value is inflated by the conservation bug (C1).

The "dynamics" reported in the manuscript are not resolved dynamics — they are transitions between capacity-capped steady states. The "phase transition" between CBD 45–65 µM is a switch between two capacity-limited regimes, not a resolved bistable system.

**Impact:** The manuscript claims "emergent phase transition" and "bistability" (Sections 3.2, 4.1). These terms imply resolved dynamical behavior. The actual model behavior is capacity-ceiling switching, which is qualitatively different from genuine bistability (which requires hysteresis at a single parameter value).

**Fix:** (a) Remove or increase capacity limits so dynamics are resolved by rate balance rather than ceiling enforcement. (b) If capacities are retained, explicitly acknowledge that the "phase transition" occurs between capacity-limited states. (c) Replace "bistable switch" with "dose-threshold effect" unless actual hysteresis is demonstrated.

---

### S2. Glutathione Inflates 4× from Source with No Consumption

**What:** GSH (P20) starts at 50 but reaches 200 (capacity) by t=39s. T12 (Nrf2_ARE_transcription, SOURCE) pumps GSH upward. T13 (Antioxidant_Scavenging) reads GSH via test arc (A37) — **it does not consume GSH**. Nothing in the model ever removes GSH tokens.

Result: GSH is effectively a constant at its capacity ceiling (200) from t=39s onward, regardless of ROS levels or disease state.

**Impact:** The antioxidant defense system is not dynamically modeled. GSH acts as a fixed catalyst, not a consumable substrate as in real biochemistry (where oxidized glutathione GSSG depletes the reduced GSH pool).

**Fix:** Add a GSH consumption arc from T13 (antioxidant scavenging should consume GSH proportionally to ROS scavenged). Add GSSG recycling. This creates the biological feedback: high ROS depletes GSH, reducing scavenging capacity.

---

### S3. APP is a Hidden Constant (Never Consumed)

**What:** APP (P4, initial=100) is only connected via test arcs. No transition consumes or produces APP. It stays at exactly 100.0 throughout all simulations. The model treats APP as an infinite substrate pool.

**Impact:** The manuscript describes APP as part of the "Amyloid Cascade" (Table 1, Section 2.2.3) without noting it's a constant. This misrepresents the model's dynamics — APP is a parameter, not a state variable.

**Fix:** Either (a) convert APP to a compartment place and describe it as a parameter, or (b) add APP consumption by γ-secretase (T3) with APP production from the secretory pathway, creating realistic APP turnover. Option (b) is biologically correct: APP processing by secretases depletes the APP pool.

---

### S4. γ-Secretase Hits Capacity Ceiling in 4 Seconds

**What:** T2 (GPR3_activates_gamma_sec) is a SOURCE with rate 0.5 × GPR3 = 25 tokens/s at GPR3=50. No degradation transition exists for γ-Secretase in v1. It hits capacity (100) in 4.3 seconds.

The manuscript claims "GammaSec to 100 (3.3× basal level)" at CBD=0 — this is not a dynamic equilibrium, it's just the capacity ceiling being hit instantly.

**Impact:** The "73% plaque reduction" from GPR3 depletion at CBD=15 is really the difference between γ-Sec at capacity (100) vs. a lower production rate. This is qualitatively correct but quantitatively meaningless.

**Fix:** Add γ-Secretase degradation/turnover (which was done in model v2: T35). Rerun results with v2 model.

---

### S5. NFkB Paradoxically INCREASES at Low CBD Doses

**What:** NFkB-p65 at CBD=15 (94.67) is **higher** than at CBD=0 (80.00). This means low-dose CBD worsens inflammation before the phase transition.

From the conservation analysis, this is likely an artifact of the C1 bug (spurious token creation). But even taking the values at face value, the biological implication is that low-dose CBD is pro-inflammatory — which contradicts all preclinical literature on CBD.

**Impact:** Table 1 shows this clearly but the manuscript doesn't discuss or explain the paradoxical increase. A reviewer will notice immediately.

**Fix:** Fix the conservation bug (C1) first. If the paradox persists after fixing, investigate the rate function topology. If it's a real model behavior, discuss it explicitly and cite supporting or contradicting literature.

---

## MODERATE Issues

### M1. "Bistable Switch" Terminology Is Incorrect

**What:** The manuscript repeatedly uses "bistable switch" and "bistability" (Sections 3.2, 4.1) to describe the NFkB/PPARγ dose-response. True bistability requires:
1. Two stable steady states at the **same** parameter value
2. Hysteresis (the system state depends on history, not just current parameter)

The model shows a dose-dependent transition: at each CBD dose, there is ONE stable state (either inflamed or neuroprotective). There is no parameter region where both states coexist. This is a **dose-threshold effect**, not bistability.

**Fix:** Replace "bistable switch" with "dose-threshold effect" or "sharp phase transition." To claim bistability, demonstrate hysteresis: start from the neuroprotective state, decrease CBD, and show the system stays neuroprotective below the threshold (different from the forward transition point).

---

### M2. "2.6× Dose Shift" Is Endpoint-Specific, Not General

**What:** The manuscript claims "dose recommendations derived from young-animal studies will underestimate requirements for elderly patients by approximately 2.6×" (Section 4.3, repeated in Conclusions).

This 2.6× (65/25 µM) applies specifically to the ROS control endpoint. For plaque reduction, CBD=25 µM is effective across all ages (Table 4). For neuron health, CBD=25 µM achieves >99% recovery at all ages (Table 5). The age-shift is dramatic for ROS but minimal for neuroprotection.

**Fix:** Qualify the 2.6× claim as endpoint-specific: "For oxidative stress control, the effective dose shifts 2.6× between young and elderly cohorts. Neuroprotective doses show minimal age dependence."

---

### M3. Manuscript Describes Model v1 (31T/76A) but v2 Exists (40T/89A)

**What:** The Abstract, Methods, and Conclusions all state "31 transitions, 76 arcs." Model v2 (with turnover, feedback, and homeostatic transitions) has 40 transitions and 89 arcs. The results in the manuscript were generated with v1.

**Fix:** Either (a) rerun all sweeps with v2 and update the manuscript, or (b) note in Methods that v2 addresses the limitations identified in v1 and present both. Option (a) is strongly recommended — v2 fixes several issues in this audit (γ-Sec turnover, GPR3 synthesis, plaque clearance, receptor desensitization).

---

### M4. Plaque "mM" Values Compared to Clinical PET Data (Incommensurable)

**What:** Section 3.6 (Healthy Aging Plaque Context) compares model plaque values (5,886–14,716 "mM") with PET amyloid-positivity rates (25–35%). These quantities are fundamentally incommensurable:
- PET measures standardized uptake value ratios (SUVr) of radiotracers
- The model produces arbitrary token counts
- No calibration exists between the two

**Fix:** Remove the numerical comparison. State qualitatively that CBD=25 µM reduces plaque to a level consistent with healthy aging (relative to untreated disease), without mapping to specific PET values.

---

### M5. Rate Constants Have No Units

**What:** All 31 rate functions use dimensionless constants (k=0.1, 0.2, 0.005, etc.) without specifying units. Since the simulation time is in seconds and concentrations are in tokens, the rate constants have implicit units of s⁻¹ (first-order) or tokens⁻¹·s⁻¹ (second-order). None of this is stated.

**Impact:** Without units, the rate constants cannot be compared to literature values or used for experimental calibration.

**Fix:** Add a statement in Methods: "Rate constants are in arbitrary units calibrated to produce qualitatively correct pathway ordering and relative magnitudes. Absolute rate values are not calibrated to experimental kinetic data."

---

### M6. Neuron "Recovery" Implies Regeneration of Dead Neurons

**What:** Table 5 shows NH going from 0.00 (age 75, CBD=0) to 99.83 (CBD=25). The model treats Neuron_Health as a continuous variable that can increase from 0 via T21 (BDNF_neuroprotection, SOURCE). This implies dead neurons can be fully restored.

In adult brain biology, mature neurons do not regenerate. Neuroprotection can prevent further death but cannot restore already-dead neurons (except in very limited neurogenic niches).

**Fix:** Rename to "Neuron_Viability_Score" and add a floor: once NH drops below a threshold (e.g., 20), the recovery rate decreases exponentially or stops. This models the irreversibility of severe neurodegeneration.

---

## MINOR Issues

### m1. T4 (Abeta_Aggregation) Is the Only Stochastic Transition

The manuscript mentions "stochastic simulation" and "tau-leaping SSA" but 30/31 transitions are continuous (ODE-integrated). Only T4 is stochastic. The model is essentially a deterministic ODE system with one stochastic perturbation. The reported CV < 0.1% confirms this — the system is nearly deterministic.

**Fix:** Acknowledge that the model is primarily ODE-driven with stochastic nucleation. The low CV indicates that stochastic effects are negligible for all endpoints except possibly Aβ aggregation kinetics.

---

### m2. CBD=100 µM Is Suprapharmacological

CBD plasma concentrations in clinical studies (Epidiolex dosing: 5–20 mg/kg/day) reach Cmax ~1–5 µM. The 100 µM upper dose in the model is 20–100× higher than clinically achievable levels. Even 65 µM (the "phase transition") is ~15× above clinical Cmax.

**Fix:** Note in Discussion that the µM doses in the model refer to local tissue/cell culture concentrations, not systemic plasma levels. In vitro studies commonly use 1–100 µM, consistent with the model range. Add a sentence mapping model doses to the in vitro literature range.

---

### m3. Microglia M1+M2 Total = 50 (Fixed Pool) Not Stated

The microglia system conserves M1+M2 = 50 exactly (verified). This means the model assumes a fixed microglial population with no proliferation, recruitment, or death. This is a significant simplification but is never stated.

**Fix:** Add one sentence in Methods: "The total microglial pool (M1+M2=50) is conserved, modeling polarization switching without proliferation or recruitment."

---

### m4. Keap1:Nrf2 + Nrf2_free = 60 (Conservation Not Stated)

Similarly, the Keap1/Nrf2 system conserves total = 60 exactly. This means all Nrf2 is either bound (Keap1:Nrf2) or free — no degradation of free Nrf2 reaches steady state. (T22 exists but doesn't break conservation because it recycles Nrf2 back to Keap1:Nrf2.)

**Fix:** State the conservation in Methods.

---

### m5. Data Availability Links GitHub URL

The Data Availability section links to `https://github.com/simao-eugenio/shypn`. Verify this is the correct and accessible repository before submission.

---

## Summary Table

| ID | Severity | Issue | Section(s) Affected |
|----|----------|-------|-------------------|
| C1 | CRITICAL | NFkB conservation violation (+25%) | Tables 1–3, Sections 3.2–3.8 |
| C2 | CRITICAL | 6-hour timescale simulates decades | All Results, Discussion |
| C3 | CRITICAL | "mM" units are arbitrary tokens | All tables, all sections |
| C4 | CRITICAL | Age≥75: 100% neuron death + miracle recovery | Tables 3, 5; Sections 3.7, 3.9 |
| S1 | SEVERE | Capacity ceilings ≠ biological dynamics | Sections 3.2, 4.1 |
| S2 | SEVERE | GSH inflates 4× with no consumption | Unstated; affects antioxidant results |
| S3 | SEVERE | APP is a hidden constant | Table 1, Section 2.2.3 |
| S4 | SEVERE | γ-Secretase ceiling in 4 seconds | Sections 3.4, 3.5 |
| S5 | SEVERE | NFkB paradoxically increases at CBD=15 | Table 1 |
| M1 | MODERATE | "Bistable" is incorrect terminology | Sections 3.2, 4.1, Conclusions |
| M2 | MODERATE | 2.6× claim is endpoint-specific | Section 4.3, Conclusions |
| M3 | MODERATE | Manuscript describes v1, v2 exists | Abstract, Methods, Conclusions |
| M4 | MODERATE | Plaque vs PET comparison invalid | Section 3.6 |
| M5 | MODERATE | Rate constants have no units | Methods |
| M6 | MODERATE | Neuron "recovery" ≠ regeneration | Table 5, Section 3.9 |
| m1 | MINOR | Model is 97% ODE, not "stochastic" | Methods, Section 3.10 |
| m2 | MINOR | CBD 100 µM is suprapharmacological | Methods |
| m3 | MINOR | Fixed microglial pool not stated | Methods |
| m4 | MINOR | Keap1/Nrf2 conservation not stated | Methods |
| m5 | MINOR | Verify GitHub URL | Data Availability |

---

## Recommended Priority Order

1. **C1** — Fix NFkB conservation (engine-level or model-level workaround)
2. **C3** — Replace "mM" with "a.u." everywhere
3. **C2** — Address timescale: reframe as qualitative topology or rescale rates
4. **C4** — Add irreversibility threshold for neurodegeneration
5. **S1** — Raise/remove capacity ceilings; add proper degradation (most addressed by v2)
6. **S2** — Add GSH consumption to antioxidant scavenging
7. **M1** — Replace "bistable" with "dose-threshold"
8. **M3** — Rerun sweeps with model v2, update manuscript
9. Remaining SEVERE and MODERATE issues as time permits
