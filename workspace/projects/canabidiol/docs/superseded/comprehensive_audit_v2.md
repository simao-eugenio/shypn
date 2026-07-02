# Comprehensive Audit Report v2 — CBD-AD Neuroprotection Model & Manuscript

**Date:** 2026-04-16  
**Scope:** Model v1 (31P/31T/76A), Model v2 (31P/40T/89A), sweep results (run_20260414_153806), manuscript (main.tex)  
**Method:** ODE-only simulation (dt=0.1, 6h), tau-leaping sweep data inspection, topology analysis, biological literature cross-check  
**Conservation fix:** RHS-clamping approach applied (C1 from audit v1 is RESOLVED)

---

## Severity Legend

| Level | Meaning |
|-------|---------|
| **CRITICAL** | Biologically absurd or structurally broken — must fix before any claims |
| **SEVERE** | Model artifact masquerading as biology — misleads interpretation |
| **MODERATE** | Unsupported claim or missing feedback — reviewer will flag |
| **MINOR** | Inaccuracy or missing caveat — fix in revision |

---

## CRITICAL Issues

### C1. ~~NFkB Conservation Violation~~ — RESOLVED ✓

The RHS-clamping fix in `_generate_c()` resolves the mass drift. Post-fix ODE validation:
- NFkB (P8+P9) = 80.000000 (error = 0.0)
- Keap1/Nrf2 (P15+P16) = 60.000000 (error = 0.0)
- Microglia (P21+P22) = 50.000000 (error = 0.0)

**Status:** FIXED. But all sweep results (run_20260414_*) pre-date this fix and must be re-run.

---

### C2. T4 (Abeta_Aggregation) Is Stochastic — ODE Bypasses the Entire Amyloid Cascade

**What:** T4 (Abeta_Aggregation: monomer → oligomer) is `type=stochastic`. The ODE accelerator only handles `type=continuous` transitions. Result:

- **In pure ODE runs:** Abeta_Oligomer = 0 forever. Abeta_Plaque = 0 forever. The entire amyloid pathology never manifests.
- **In tau-leaping sweeps:** T4 fires stochastically, producing oligomers. But T4's rate = `0.05 * Abeta_Monomer² * Q10 * (1 + 0.5*(7.0 - pH))`, which is a second-order reaction. At Abeta_Monomer=500 (the ceiling), rate = 0.05 × 250000 = 12,500 tokens/step — an absurdly fast nucleation rate.

**Impact:** The split between stochastic T4 and continuous everything else means the model behaves fundamentally differently depending on the simulation mode. ODE-only results show zero amyloid pathology. This inconsistency is not acknowledged in the manuscript.

**Biological reality:** Aβ aggregation is indeed stochastic (nucleation-dependent), but the rate constant (0.05 µM⁻¹s⁻¹ for second-order nucleation) is far too fast. Physiological Aβ42 aggregation half-times are hours to days at µM concentrations in vitro, years in vivo.

---

### C3. Abeta_Monomer Accumulates to 424 (or 500 at cap) with No Effective Clearance

**What:** T3 (Abeta_Production) is a SOURCE: `rate = 0.3 * Gamma_Secretase * Q10 * age_factor`. At GammaSec=32.5 (CBD=100 steady state), this produces ~9.75 tokens/s. The only clearance is T25: `rate = 0.01 * Abeta_Monomer / age_factor` — which at steady state gives 0.01 × 424 = 4.24 tokens/s. The monomer hits ~424 tokens (ODE) or 500 (capacity in sweep).

**Biological reality:** Brain Aβ monomer concentrations are ~1–10 nM (0.001–0.01 µM). The model produces concentrations 10,000–100,000× higher than physiological values, even in abstract token units the ratio of production to clearance is unbalanced.

**Impact:** The enormous monomer pool feeds the quadratic aggregation rate (T4), causing explosive oligomer formation in tau-leaping mode. In ODE mode, it just sits there doing nothing since T4 is stochastic.

---

### C4. GPR3 Depleted to Zero in <60 Seconds — Irreversible Binary Switch

**What:** T1 rate = `0.1 * CBD_extracellular * GPR3`. At CBD=100, GPR3=50: initial rate = 500 tokens/s. GPR3 goes from 50 → 0 almost instantly (<10s). In v1 there is no GPR3 resynthesis.

- V2 adds T38 (GPR3_Basal_Synthesis): `rate = 0.005 * (50 - GPR3) * (GPR3 < 50)`, but this is too slow (max 0.25 tokens/s) to compete with T1's depletion rate.

**Biological reality:** GPR3 is a constitutively active GPCR. CBD acts as an inverse agonist, reducing its constitutive activity — it does NOT destroy or deplete GPR3 protein. GPR3 receptor internalization/downregulation occurs on timescales of hours, not seconds, and is partial (typically 30–60% reduction), not complete.

**Impact:** The model treats GPR3 inverse agonism as complete irreversible receptor destruction. This makes all CBD doses (even 15 µM) produce identical GPR3=0, γ-Sec≈32.5 outcomes. The manuscript's "GPR3 as most sensitive target" claim (Section 3.4) is an artifact of this binary switch.

---

### C5. Signal Places Accumulate Without Bound Until Capacity

**What:** Several signal places act as integrators with no degradation, hitting their capacity ceiling almost instantly and staying there:

| Signal Place | Rate of Production | Degradation | Time to Ceiling |
|---|---|---|---|
| HT1A_active (P25) | 0.15 × CBD_ext = 15/s | None in v1 | ~3 s |
| A2A_active (P27) | 0.12 × CBD_ext = 12/s | None in v1 | ~4 s |
| PPARg_active (P26) | 0.2 × CBD_int | None in v1 | Slower (~300s), depends on PK |
| Nrf2_free (P16) | from T11 | T22: 0.1 × Nrf2_free | Reaches ~13 (dynamic balance) ✓ |

HT1A_active and A2A_active saturate at their capacity (50) within seconds at any CBD dose. V2 adds very slow desensitization (T33: 0.0001 × HT1A, T34: 0.000065 × A2A), but these rates are negligible (half-life ~7000s and ~10000s respectively — the ceiling is hit and maintained).

**Biological reality:** GPCR activation involves rapid desensitization (minutes), receptor internalization (minutes to hours), and resensitization. The model's signal places lack this fundamental feedback.

**Impact:** Because HT1A and A2A saturate immediately at ALL non-zero CBD doses, they provide identical downstream signaling regardless of dose. BDNF production (via T16: 0.3 × HT1A_active = 15 tokens/s) hits capacity (100) in seconds. M1→M2 polarization (via T18, which reads A2A_active and PPARg_active) also saturates. The "dissociated therapeutic windows" finding is partly an artifact of this binary on/off behavior.

---

### C6. Concentration Scale: Everything at mM Is Biologically Absurd

**What:** (Carried over from audit v1 as C3, but elevated to CRITICAL after deeper analysis)

| Species | Model Steady State | Physiological Range | Scale Error |
|---|---|---|---|
| TNFα | 200 tokens ("mM") | 0.1–600 pg/mL ≈ 6–35 fM | ~10¹³× |
| IL-1β | 200 tokens | 0.1–100 pg/mL ≈ 6–6000 fM | ~10¹¹× |
| BDNF | 100 tokens | 1–50 ng/mL ≈ 0.04–2 nM | ~10⁸× |
| ROS (as H₂O₂) | 500 tokens | 1–100 nM physiological | ~10⁹× |
| Aβ plaque | 58,864 tokens | Not a concentration | N/A |
| NFkB-p65 (nuclear) | 80 tokens | ~1–50 nM | ~10⁷× |

The manuscript's Limitations section acknowledges this ("Petri net marking units") but all tables use "mM" labels.

**Impact:** Using "mM" destroys credibility. The fix is straightforward: use "a.u." or "tokens" as units and never reference real concentrations. However, the deeper issue is that rate constants calibrated against arbitrary token units cannot produce biologically meaningful dose-response relationships. The EC50 predictions (45–65 µM CBD for the phase transition) have no connection to real pharmacology.

---

## SEVERE Issues

### S1. Capacity Ceilings Are the Primary Dynamical Feature

**What:** The model's "dynamics" are dominated by species hitting capacity ceilings:

| Species | Time to Capacity | % of Simulation at Cap |
|---|---|---|
| γ-Secretase (CBD=0) | <10 s | 99.95% |
| HT1A_active | <5 s | 99.98% |
| A2A_active | <5 s | 99.98% |
| TNFα, IL-1β, IL-6 | <60 s | 99.7% |
| COX2 | <60 s | 99.7% |
| HO1, SOD | <60 s | 99.7% |
| Glutathione | <60 s | 99.7% |
| BDNF (any CBD>0) | <60 s | 99.7% |
| ROS (CBD=0) | <60 s | 99.7% |

The "phase transition" between CBD 45–65 µM is really a switch between two sets of capacity ceilings, not a resolved dynamical transition. The manuscript's "bistability" claim requires coexistence of two stable states at the same parameter — what the model shows is simply two different capacity-limited regimes at different CBD doses.

**Fix:** Remove all capacity limits (or set to very large values). Let dynamics be governed by rate balance, not artificial ceilings. Then re-evaluate whether any genuine bistable behavior exists.

---

### S2. Glutathione, HO1, SOD Have No Consumption — Infinite Antioxidant Capacity

**What:**
- T12 (Nrf2_ARE_transcription) is a SOURCE for HO1, SOD, and Glutathione
- T13 (Antioxidant_Scavenging) uses test arcs (A35, A36, A37) for SOD, HO1, GSH — they are **read but never consumed**
- Result: All three antioxidants accumulate to capacity and stay there forever

**Biological reality:**
- Glutathione (GSH) is oxidized to GSSG during ROS scavenging. GSH:GSSG ratio is a key redox marker
- HO-1 and SOD enzymes turn over with half-lives of 6–24 hours
- V2 adds T36 (HO1_Degradation) and T37 (SOD_Degradation), but not GSH consumption

**Impact:** The antioxidant defense system is not dynamically modeled. ROS scavenging is effectively infinite once Nrf2 activates ARE transcription. The model cannot predict conditions where antioxidant defenses are overwhelmed — a key feature of AD oxidative stress.

---

### S3. IKK_Dephosphorylation (T27) Fails C Transpilation — IKK Has No Effective Ceiling Control in ODE Mode

**What:** T27 rate = `0.008 * (IKK - 10) * (IKK > 10)` — the comparison operator `(IKK > 10)` cannot be transpiled to C. The ODE system sets T27's rate to 0.

- In ODE mode: IKK only has T8 (Abeta_activates_IKK: 0.1 × Abeta_Oligomer) as input, and T6 (IKK reads via test arc — not consumed). Since Abeta_Oligomer=0 in ODE mode (C2 above), IKK stays at exactly 10.0.
- In tau-leaping: T27 fires properly, but IKK is also uncontrolled because T8 adds IKK without saturation. IKK hits capacity (50) quickly.

**Impact:** The entire NFkB activation pathway (IKK → NFkB-p65) operates differently in ODE vs tau-leaping mode due to this transpilation failure.

**Fix:** Replace the comparison operator with a smooth approximation: `0.008 * max(IKK - 10, 0)` or use a steep sigmoid: `0.008 * (IKK - 10) / (1 + exp(-10*(IKK - 10)))`.

---

### S4. Neurotoxicity (T20) Is Product of Three Michaelis-Menten Terms — Vanishes When Any Factor Is Zero

**What:** T20 = `0.01 * (Abeta_Oligomer/(10+Abeta_Oligomer)) * (ROS/(15+ROS)) * (TNFα/(10+TNFα)) * Q10 * pH_factor * age_factor`

This is a product (AND gate), meaning if ANY ONE of {Abeta_Oligomer, ROS, TNFα} is zero, neurotoxicity = 0 regardless of the other two.

- In ODE mode: Abeta_Oligomer = 0 forever (C2) → T20 rate = 0 → Neuron_Health stays at 100 forever
- In tau-leaping with CBD>0: TNFα can drop to ~7 → T20 ≈ 0.01 × (Oligomer/(10+Oligomer)) × (ROS/(15+ROS)) × (7/(10+7)) × ... ≈ tiny
- In tau-leaping with CBD=0: All three saturate → T20 ≈ 0.01 × 0.97 × 0.97 × 0.95 × ... ≈ 0.009 tokens/s

**Impact:** Neurotoxicity is effectively all-or-nothing. At CBD=0 it's 0.009 tokens/s (drains NH=100 in ~3 hours). At any CBD>0, reducing ANY one of the three factors to near zero effectively eliminates neurotoxicity. This is why even CBD=15 µM gives NH=99.85 — the AND-gate architecture makes neuroprotection trivially easy.

**Biological reality:** Neurotoxicity has multiple independent pathways. Aβ oligomers cause synaptotoxicity independently of ROS. TNFα causes neuronal apoptosis independently of amyloid. The product formulation is biologically incorrect — it should be a sum or weighted combination.

---

### S5. Timescale Compression — 6 Hours Models Years of Disease

**What:** (Carried from audit v1 C2)
- Aβ plaque: 0 → 58,864 in 6 hours (real: 5–20 years)
- Neuronal death: 100 → 15 in 6 hours (real: 5–15 years)
- All cytokines saturate in <60 seconds
- All drug targets saturate in <60 seconds

The model compresses decades of disease into hours, making timescale claims in the manuscript (6-hour protocols, "acute pharmacodynamic responses") misleading.

---

## MODERATE Issues

### M1. "Bistable Switch" Terminology Is Incorrect

True bistability requires two stable states at the SAME parameter value (hysteresis). The model shows a dose-threshold effect: at each CBD dose there is one steady state. No hysteresis has been demonstrated. Replace "bistable switch" with "dose-threshold transition" throughout the manuscript.

### M2. All Sweep Results Must Be Re-Run

The conservation fix (RHS clamping + max_step) changes ODE dynamics. All sweep data (run_20260414_*) was generated before this fix. NFkB values, all downstream endpoints, and phase transition boundaries may shift.

### M3. Missing CBD Target: CB1/CB2 Cannabinoid Receptors

CBD has documented activity at CB1 and CB2 receptors (inverse agonist at CB1, partial agonist at CB2). These are arguably more established than GPR3 or A2A for AD-relevant effects. Their omission should be explicitly justified.

### M4. "mM" Units Throughout All Tables

Tables 1–6 all label concentrations as "mM". Even with the Limitations caveat, this is misleading. Use "tokens" or "a.u." (arbitrary units).

### M5. Neuron_Health "Recovery" from Zero Is Biologically Impossible

At CBD=0, Age≥75: NH=0.00. Then CBD=25 "restores" NH to 99.78. This implies dead neurons regenerating, which is biologically impossible. Neuron_Health needs a damage irreversibility threshold.

### M6. Two-Compartment PK Rates Are Arbitrary

The manuscript claims PK parameters are "consistent with preclinical CBD pharmacokinetic data in the linear regime" but:
- Absorption rate 0.0008 s⁻¹ → half-life ~14 min. CBD oral absorption half-life is 1–3 hours.
- The steady-state intracellular/extracellular ratio of 2.62 is claimed but at t=6h, CBD_ext=18.4 and CBD_int=48.3 → ratio=2.62. This is a model output, not validated against data.
- CBD brain:plasma ratio in animal studies is typically 3–10× depending on formulation and species.

### M7. Second-Order Aggregation Rate Produces Explosive Kinetics

T4 rate = `0.05 * Abeta_Monomer²` — at monomer=500, rate = 12,500 tokens/s. This is explosive. In vitro Aβ42 aggregation with nucleation takes hours at 10–50 µM concentrations. The rate constant is orders of magnitude too fast, even for abstract tokens.

---

## MINOR Issues

### m1. T27 Comparison Operator Breaks ODE Mode

`(IKK > 10)` cannot be transpiled to C. Use `_heaviside(IKK - 10)` or smooth sigmoid.

### m2. pH=7.0 Is Not Physiological

The model uses pH=7.0. Brain extracellular pH is 7.2–7.4. Intracellular pH is 7.0–7.2. AD pathology involves acidosis to pH 6.6–7.0. The default should be 7.4 (physiological) with AD conditions modeled as lowered pH.

### m3. Temperature Q10 Is Always 1.0 at Default Settings

With T=310.15 K → T_celsius = 37°C → Q10 = 2^((37-37)/10) = 1.0. The Q10 mechanism is present but dormant at default conditions. It only matters for hypothermia/fever scenarios not explored in the current sweep.

### m4. APP Initial Marking = 100 Has No Physiological Basis

APP is a test-arc constant (never consumed, never produced). Its value is irrelevant since it's only read. It could be 1 or 1000 with identical results. But the manuscript lists it in the "Amyloid Cascade" module as if it's a dynamic variable.

### m5. BDNF_Turnover (T26) Has Very Low Rate

T26 rate = 0.005 × BDNF. At BDNF=100, turnover = 0.5 tokens/s. Production via T16 = 0.3 × HT1A_active = 15 tokens/s. Production >> turnover, so BDNF saturates at capacity. The turnover mechanism is essentially negligible.

---

## Summary

| Severity | Count | Key Theme |
|----------|-------|-----------|
| CRITICAL | 6 (1 resolved) | Conservation (fixed), stochastic/ODE gap, monomer accumulation, GPR3 binary switch, signal place saturation, unit absurdity |
| SEVERE | 5 | Capacity ceilings as dynamics, infinite antioxidants, IKK transpile failure, neurotoxicity AND-gate, timescale compression |
| MODERATE | 7 | Bistability terminology, stale sweep data, missing CB1/CB2, mM units, neuron recovery from zero, arbitrary PK, explosive aggregation |
| MINOR | 5 | T27 operator, pH default, dormant Q10, APP constant, BDNF turnover negligible |

---

## Priority Action Plan

### Phase 1: Engine & Re-run (Immediate)
1. ✅ Conservation fix (RHS clamping) — DONE
2. Fix T27 transpilation (replace `(IKK > 10)` with smooth heaviside)
3. Re-run all sweeps with the conservation fix

### Phase 2: Model Structure (Critical)
4. Remove all capacity ceilings (or set very high) — let rate balance determine steady states
5. Convert T4 to continuous (or provide continuous fallback for ODE mode)
6. Add GSH consumption in T13; add GSH recycling (GSSG → GSH)
7. Change GPR3 depletion to GPR3 inactivation (partial, reversible, with recycling)
8. Remodel neurotoxicity T20 as sum of independent pathways, not product
9. Add receptor desensitization for HT1A, A2A, PPARg (use v2 rates but make them faster)

### Phase 3: Manuscript (After model fixes)
10. Replace "mM" with "a.u." throughout
11. Replace "bistable switch" with "dose-threshold transition"
12. Add irreversibility threshold for Neuron_Health
13. Justify pH=7.0, discuss CB1/CB2 omission
14. Re-evaluate all three "actionable predictions" against fixed model behavior
