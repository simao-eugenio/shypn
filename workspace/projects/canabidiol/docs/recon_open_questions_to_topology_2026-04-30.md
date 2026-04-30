# CBD–AD recon: open questions → wet-lab anchors → minimal Petri-net pathways

**Date:** 2026-04-30
**Context:** After three rounds of "guess-and-see" patches on
`canabidiol-phase-0-v2.shy` failed to recover dose-response, the
structural audit revealed cascade depth = 1 and cosmetic `signal_flow`
usage. This recon re-anchors model design in **wet-lab observables that
v1/v2 reproduced** so any deviation in v3 is direct topological
evidence.

## A. Principle

`literature_validation.md` (v1: 30P/31T/76A; v2: 34P/45T) reproduced
**8 of 10 wet-lab observables at HIGH or VERY HIGH concordance**. The
v3 line (Pattern-A migration → phase-0 → phase-2) preserved healthy
fixed-point stability but **lost the dose-response signal**: phase-2's
5×5 (DSEV × MAINT_DOSE) sweep at 4 days produced bit-identical
downstream values across a 2000× Aβ amplitude range and ≤1 NH unit of
CBD rescue (`phase_2_dose_response_validation.md`). That is direct
topological evidence: whatever generated the v1/v2 dose-response is
*missing or silenced* in v3.

The recon question is symmetric:

> For each wet-lab-validated finding (or known open question), what is
> the **minimal Petri-net subgraph** that produced (or would produce)
> the observation, and where does v3-phase-0-v2 stand on that subgraph?

## B. CBD molecular targets relevant to AD

(`cbd_drug_discovery_recon.md`)

| Target            | Effect      | Present in v3-phase-0-v2? |
|-------------------|-------------|---------------------------|
| GPR3 (inv. ag.)   | ↓ γ-secretase → ↓ Aβ production | **Missing**. v1 had T1 `0.1·CBD_ext·GPR3` driving the 73% plaque reduction at low dose. v3 has no GPR3 place. |
| PPARγ             | ↓ NFκB p65 (ubiquitination) | Partial. PPARγ ↓ NFκB exists; no PPARγ place — collapsed into NFκB-direct rate. |
| Nrf2 / Keap1      | ↑ ARE → HO-1, SOD, GSH | ✅ present (T11 dual ROS + CBD term in v1; preserved in v3). |
| 5-HT1A → BDNF     | Neurotrophic | Partial. BDNF place exists; the 5-HT1A → BDNF arc that gave v1 NH=99.85 at CBD=15 µM is **flattened** into a constant. |
| A2A → M2          | Polarisation | ✅ present (M1↔M2 conserved pair). |
| CB1 NAM, CB2, GPR55, TRPV1/A1/M8, FAAH | Anxiolytic / pain / Ca²⁺ | Out of scope (not AD-driving). |

## C. Open questions × wet-lab anchors × minimal pathway × v3 status

| # | Open question | Wet-lab anchor | Minimal Petri-net pathway | v3-phase-0-v2 status |
|---|---|---|---|---|
| **Q1** | IC₅₀ of CBD on NFκB activation? | Kozela 2010 (BV-2 microglia, IC₅₀ ≈ 1 µM); Esposito 2006 (PC12, sig. at 1 µM). v1 reproduced sharp threshold at CBD≈1. | `CBD_intra` ─[test/Φ]→ `T_PPARg_inhibits_NFkB` ⊣ `NFkB_p65`; PPARγ as ⬡ signal place; rate `0.3·PPARγ·NFkB_p65` with PPARγ activated by `0.2·CBD_intra`. **Two transitions, three places.** | **Broken.** Phase-2 sweep gave NFκB endpoint = 0 at every cell. NFκB never ignites because Aβ install events are sub-threshold (no cascade); the downstream PPARγ→NFκB arc is dynamically dead. |
| **Q2** | Is Aβ aggregation a stochastic bistable switch (clear vs lock-in)? | Knowles 2009 (*Science*), Hellstrand 2010, Törnquist 2018 — single-molecule binary outcomes. v2 reproduced bistability (BC ≤ 0.95, CV ≤ 1.53). | `Aβ_Mono` ─[normal w=2]→ `T_Aggregation` (adaptive, rate `k·Aβ_Mono²`) ─[normal]→ `Aβ_Olig`; clearance arc `Aβ_Olig` ─[normal]→ ∅ first-order. **Self-amplifying nonlinear consumption.** | **Topologically present** but functionally inert under phase-2 events. Phase-1 envelope showed Aβ-Olig fires only when `T ≥ 310 K AND Age ≥ 75 y` simultaneously — i.e. requires temperature-amplified trigger, not a one-shot Aβ-Mono jolt. The phase-2 install events bypass this co-incidence. |
| **Q3** | Does microglial M1/M2 polarisation behave as a bistable switch under CBD? | Orihuela 2016; Martín-Moreno 2011 (APP/PS1 mice, CBD shifted to M2); Juknat 2013. | `M1` + `M2` = const (P-invariant); `T_M1_to_M2` rate = `k·CBD_intra·M1`; `T_M2_to_M1` rate = `k'·NFκB·M2`. **Two competing transitions sharing two places.** | ✅ Present in v3 but inactive — both NFκB and CBD effects quenched by Q1/Q2 failures upstream. M1+M2 conservation holds. |
| **Q4** | Is the inflammation→neuroprotection link dissociable? (ADAPT-style negative result) | **VERY HIGH concordance.** ADAPT 2007 + INTREPAD 2019: NSAIDs reduced inflammatory biomarkers, no cognitive benefit. v2 reproduced 88% dissociation (84/96 cells: NFκB<1, NH<95). | Two parallel arms feeding `Neuron_Health`: arm 1 = `NFκB → cytokines → ─[normal]→ NH`, arm 2 = `ROS → ─[normal]→ NH`. Each arm has its **own** clearance pathway; CBD inhibits both at different doses. **NH must have ≥2 independent destruction routes.** | **Partially present**: ROS→NH and inflammation→NH both exist as inputs. But because phase-2 has neither inflammation nor ROS firing, the dissociation is untestable. The *topology* is OK; the *driver events* are silent. |
| **Q5** | Does CBD efficacy shift from anti-inflammatory (young) to antioxidant (old) with age? | Zhang 2015: Nrf2 activity ↓ with age. Rahimifard 2017: GSH synthesis ↓20–30% age 50→80. v2 produced 88/12 → 35/65 split, EC₅₀ 0.57→1.63. | `Age_factor` (◇ spatial) ─[Φ-read]→ rate of `T_Nrf2_basal_synthesis`. Multiplicative coupling: `rate = k·CBD_intra·(1 + α·Age_factor)` for Nrf2 arm; `rate = k'·CBD_intra/(K + Age_factor·M)` for NFκB arm. **Two rate-modulation points sharing one ◇ place.** | ✅ Pattern-A bridge for `Age_factor` works (slope 0.020/y). But because the two CBD action arms are not both *active* in phase-2, the age-dependent mechanism switch cannot be detected. |
| **Q6** | Why inverted-U dose-response in vivo? | `cbd_drug_discovery_recon.md` open issue #6; Atalay 2020. | (a) CBD ─[test]→ inhibits its own influx (substrate inhibition); (b) `CBD_intra` saturable consumption (CYP3A4); (c) high-dose CBD activates a counter-regulatory ⬡ that inhibits Nrf2. **Minimal: add CYP3A4 metabolism transition with Michaelis Φ.** | **Missing.** v3 has linear PK (`CBD_intra(t) = 9.99 + 3.0·MD`); v1 also linear. Neither model can reproduce inverted-U yet. Known gap. |
| **Q7** | Where does γ-secretase processing occur thermodynamically? Lysosomal vs surface. | Acidic compartment ΔG shift (`innovation_analysis.md` §4.3). pH=4.5 endosome favours proton-coupled cleavage. | `APP` ─[normal]→ `T_gamma_sec_endosome` (rate `k·APP·H_concentration`) ─[normal]→ `Aβ_Mono`; `pH_acidosis` ◇ as Φ rate-multiplier. **Two compartments via separate rates, not separate places.** | **Missing.** v3 has APP-less direct Aβ_Mono pool. The pH bridge exists but no APP→Aβ transition references it. |
| **Q8** | Is there a thermodynamic barrier to Aβ disaggregation? | Knowles 2009; ΔG_aggregation ≈ −40 kJ/mol → K_eq ≈ 10⁷ effectively irreversible. | One-way `Aβ_Olig → Aβ_Plaque` arc with **no reverse arc**; trap analysis on `{Aβ_Olig, Aβ_Plaque}`. **Topology = trap.** | ✅ Present. v3-phase-0-v2 has Aβ_Plaque as bounded trap; never empties. Correct topology, just dynamically unreached. |
| **Q9** | Does temperature × age synergy affect neuroprotection? | Predicted by phase-1 envelope (`phase_1_envelope_validation.md` §5.4): ∂NH/∂T = −0.125 at age 30, −0.889 at age 85 (7× amplification). Heat-vulnerability-of-elderly is canonical clinical observation. | `Temperature_factor` ◇ + `Age_factor` ◇ both multiply the same `T_ROS_production` Φ rate (`k·T_factor·Age_factor`). **One shared rate, two ◇ inputs.** | ✅ Reproduced in phase-1 — one of the model's *successes*. |
| **Q10** | What is the residual neuroprotection axis (the 1.64-NH gap)? | v2 finding: max NH=93.36 even at CBD=15. Cheng 2014, Iuvone 2004 list PPARγ direct anti-apoptosis, BDNF/neurogenesis, Aβ phagocytosis, A2A. | Add `BDNF` ─[normal]→ `T_neurogenesis` ─[normal]→ `Neuron_Health` with rate `k·BDNF·CBD_intra`. **One place + one transition.** | **Partial.** BDNF place exists in v3 with constant value (4.86 in phase-1, 1.54 in phase-2 control). Not driving NH. |

## D. Where v3 broke what v2 had

The v3-phase-0-v2 model was built to enforce four-carrier (○ ⬡ ◇ ▢) +
Pattern A. Migration **succeeded structurally** (formalism is clean,
healthy baseline at sha `c49df7f8` reproduced 16/18 markers,
`phase_0_baseline_validation.md`) but **lost three working v1/v2
elements**:

1. **GPR3 → γ-secretase → Aβ_Monomer cascade** (v1 T1: `0.1·CBD_ext·GPR3`).
   v1 derived 73% plaque reduction at CBD=15 µM from this single arc.
   v3 collapsed APP/GPR3 into a constant Aβ_Mono pool — phase-2 events
   now have to *install* Aβ as a discrete jolt that clears too fast.
2. **PPARγ as a free-floating intermediate.** v1 had a discrete PPARγ
   place (T10: `0.2·CBD_intra` activating it; T9: `0.3·PPARγ·NFκB`).
   v3 uses a direct `CBD_intra ─[test]→ T_PPARg_inhibits_NFkB` with
   PPARγ collapsed into the rate constant. This removed the only
   place where `PreemptionCheck` had teeth (cascade depth = 1).
3. **A self-sustaining diseased fixed point.** v1/v2 had Aβ_Mono
   initial_marking high enough that aggregation ran continuously.
   v3-phase-2 zeroed Aβ_Mono and uses events to install pathology at
   deltas (0.125 token / DSEV unit) below homeostatic clearance.
   Result: bit-identical downstream across 2000× sweep.

## E. Recommended topology actions, ranked by which open question they answer

| Priority | Action | Answers |
|---|---|---|
| **P1** | Restore `GPR3` (○) and `gamma_secretase` (○) places + `T_GPR3_inv_ag` (CBD inhibits GPR3, `test`-arc to gate γ-sec). Initialise `Aβ_Monomer` ≥ 5 tokens so the cascade self-sustains. | Q1, Q2, Q4, Q6 (downstream) |
| **P2** | Restore `PPARγ` (⬡) as a free signal place between CBD and NFκB. *Also* gives `PreemptionCheck` a real layer (cascade depth ≥ 2). | Q1, Q3 (M1/M2 needs NFκB) |
| **P3** | Add `T_CBD_metabolism_CYP3A4` saturable Φ to break linearity. Test inverted-U. | Q6 |
| **P4** | Add `APP` ○ + endosomal/surface γ-sec branch reading `pH_acidosis` ◇. | Q7 |
| **P5** | Add BDNF→NH neurogenesis arc with `k·BDNF·CBD_intra` rate. | Q10 |
| **P6** | Re-enable phase-2 disease installation by *raising Aβ_Mono initial marking* per DSEV (event seeds the pool to `5·DSEV`), **not** by injecting 0.125-token jolts. | Reactivates Q2/Q3/Q4 dose-response. |

## F. Diagnostic principle going forward

Before any topology change is committed, predict which row in table C
it will move and check the matching wet-lab anchor. **No edit should
be motivated by "the run looks wrong" alone**; every edit must restore
or test a row in the open-question table. Conversely, no row should be
marked "fixed" without a sweep cell that empirically reproduces the
wet-lab number to within stated tolerance.

This converts the model edit loop from "guess and see" into
**anchor → minimal-pathway → sweep → concordance check** — the
workflow that produced v1/v2's 8/10 HIGH-concordance score.

## G. First refactor target

Q1 (NFκB IC₅₀ ≈ 1 µM, the strongest single anchor). Build a minimal
patch script that adds `PPARγ` (⬡) + the two transitions, raises
`Aβ_Monomer.initial_marking` to 5, and runs a single-axis CBD sweep
at fixed (T=310, Age=75, pH=7.4, DSEV=0.5). **Acceptance criterion:**
`NFκB(CBD=0) > 50 AND NFκB(CBD=1) < 5`. If that passes, the v1/v2
IC₅₀ result is recovered; if not, the new model has a different break
point we can isolate before adding Q4–Q10 elements.
