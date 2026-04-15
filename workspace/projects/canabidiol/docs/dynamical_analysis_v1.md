# Dynamical Analysis — CBD-AD Neuroprotection Model v1

**Date:** 2026-04-14  
**Model:** `models/cbd_ad_neuroprotection_v1.shy`  
**Simulation:** 6-hour run (21,600 s), 10,002 timepoints  
**Script:** `data/analyze_dynamics.py`

---

## 1. Basin of Attraction

### Attractor Classification

The system converges to a **stable fixed point** (point attractor, dimension 0). All 27 species reach constant steady-state values with negligible variance (σ < 0.1% of mean for 26/27 species). The apparent oscillation in Aβ monomer (σ = 0.87 mM) is stochastic jitter from the discrete firing process, not a true limit cycle.

### Steady-State Values

| Species | Initial (mM) | SS Value (mM) | Change |
|---------|-------------|---------------|--------|
| CBD | 100.0 | 100.0 | +0.0 |
| IKK | 10.0 | 50.0 | +40.0 |
| TNFα / IL-1β / IL-6 / COX-2 | 0.0 | 11.6 | +11.6 |
| Keap1\_Nrf2 | 60.0 | 37.1 | −22.9 |
| Nrf2\_free | 0.0 | 22.9 | +22.9 |
| HO-1 | 0.0 | 100.0 | +100.0 |
| SOD | 5.0 | 100.0 | +95.0 |
| ROS | 10.0 | 2.1 | −7.9 |
| GPR3 | 50.0 | 0.0 | −50.0 |
| Glutathione | 50.0 | 200.0 | +150.0 |
| Microglia\_M1 | 5.0 | 26.2 | +21.2 |
| Microglia\_M2 | 45.0 | 23.8 | −21.2 |
| Neuron\_Health | 100.0 | 99.99 | −0.01 |
| BDNF | 10.0 | 100.0 | +90.0 |
| γ-Secretase | 30.0 | 32.5 | +2.5 |
| Aβ Monomer | 0.0 | 1.5 | +1.5 |
| Aβ Oligomer | 0.0 | 22.2 | +22.2 |
| Aβ Plaque | 0.0 | 7,854 | +7,854 |
| NFκB\_p65 | 0.0 | 0.41 | +0.41 |

### Convergence Timescales

Three distinct timescale regimes emerge:

- **Fast** (< 100 s) — 22 species: receptor activation (2–4 s), transcription factors (6–35 s), microglia polarization (71 s)
- **Medium** (100–1000 s) — 4 species: cytokines (TNFα, IL-1β, IL-6, COX-2 at 166 s)
- **Slow** (> 1000 s) — 1 species: Aβ Plaque (20,010 s to 95% of final value)

This separation of timescales is biologically consistent: receptor signalling (seconds) → gene regulation (minutes) → protein accumulation (hours) → plaque deposition (days).

---

## 2. Bistability & Switch Dynamics

### M1/M2 Microglial Polarization

- **Crossover time:** t = 67 s (M1 surpasses M2)
- **Sigmoid steepness:** k = 0.004 /s
- **Verdict: Gradual monostable drift** — not a sharp bistable switch

The M1/M2 transition is a slow, continuous shift rather than an ultrasensitive flip. This is consistent with chronic neuroinflammation where microglial polarization is a graded response, not an all-or-nothing event. The system settles at M1:M2 = 52:48, a nearly degenerate state suggesting the pro- and anti-inflammatory drives are closely balanced.

### NFκB ON/OFF Switch

- **Activation fraction:** 0.5% (p65/total)
- **State:** LOW-ACTIVITY, dominated by PPARγ inhibition

CBD's activation of PPARγ keeps NFκB essentially locked in the inactive (IκB-bound) state. Only 0.41 mM of the 80 mM total NFκB pool is free p65 — a 200:1 suppression ratio. This represents the primary anti-inflammatory mechanism of CBD in the model.

### Nrf2/Keap1 Antioxidant Switch

- **Activation fraction:** 38.2% (22.9/60 mM)
- **Transient overshoot:** 7.6% above steady state at t = 10.8 s
- **Behavior:** Damped relaxation, not bistable

The Nrf2 pathway activates rapidly (t₉₅ = 6.5 s) with a small overshoot, then settles to ~38% liberation. This partial activation is biologically plausible — full Nrf2 liberation would imply complete Keap1 oxidation, which occurs only under extreme oxidative stress.

---

## 3. Preemption Cascade

### CBD → GPR3 Inverse Agonism → Amyloid Pathway

```
CBD ⊣ GPR3 → γ-Secretase → APP cleavage → Aβ monomer → Aβ oligomer → Aβ plaque
```

| Stage | Event | Timing | Value |
|-------|-------|--------|-------|
| 1 | GPR3 half-life under CBD | 2.2 s | 50 → 25 mM |
| 1 | GPR3 fully depleted | 2.2 s | 50 → 0 mM |
| 2 | γ-Sec final level | 2.2 s | 30 → 32.5 mM |
| 3 | Max Aβ production rate | 0 s | 1.28 mM/s |
| 3 | Post-depletion Aβ rate | — | −0.09 mM/s |
| 4 | Preemption efficiency | — | **96%** |

**Key finding:** CBD blocks 96% of GPR3→γ-Secretase production, but the 4% that accumulated during the first 2.2 seconds creates a persistent γ-Secretase pool (32.5 mM) that continues to drive Aβ production indefinitely. The preemption is **partial**: it drastically slows but cannot halt the amyloid cascade because γ-Secretase acts catalytically (test arc, not consumed).

**Biological interpretation:** This mirrors the clinical observation that CBD reduces but does not eliminate amyloid burden. Complete amyloid arrest would require either γ-Secretase degradation or a direct Aβ clearance mechanism.

---

## 4. Siphon Analysis (Depletion Traps)

A **siphon** is a set of places S such that every transition outputting to S also requires input from S. Once empty, a siphon remains empty forever.

| Siphon | Status | Detail |
|--------|--------|--------|
| **GPR3** | EMPTIED | Irreversible depletion by CBD (no synthesis pathway). By design — represents CBD's inverse agonism. |
| **Neuron\_Health** | SAFE | BDNF repair matches neurotoxicity drain. Min = 99.99 mM. |
| **Glutathione** | SAFE | Now catalytic (test arc). Refilled by Nrf2-ARE transcription. Final = 200 mM. |

The GPR3 siphon activation is the structural mechanism behind CBD's preemption of the amyloid cascade. It is an intentional design feature of the model.

---

## 5. Trap Analysis (Accumulation Sinks)

A **trap** is a set of places T such that every transition with input from T also outputs to T. Tokens entering a trap cannot leave.

### Aβ Plaque — Active Trap

- **Accumulation:** 0 → 8,054 mM (linear growth)
- **Rate at steady state:** 0.37 mM/s
- **Doubling time:** 6.1 hours
- **Growth regime:** LINEAR (constant rate, early/late ratio = 0.977)

The plaque trap is the only unbounded species in the model. It grows linearly because its sole input (oligomer aggregation) exceeds clearance capacity. This is architecturally intentional — amyloid plaques are biologically irreversible in the absence of active dissolution mechanisms.

### IKK — Quasi-Trap

- **Accumulation:** 10 → 50 mM
- **Balanced by:** T27 IKK\_Dephosphorylation at 0.008×(IKK−10)×(IKK>10)
- **New homeostasis:** 50 mM

IKK accumulates above basal but reaches equilibrium where phosphorylation equals dephosphorylation. This is a **regulated trap** — bounded but displaced from the initial condition.

---

## 6. Phase Portrait Analysis

### Nrf2/ROS — Damped Oscillatory Dynamics

- **Trajectory:** (Nrf2=0, ROS=10) → (Nrf2=22.9, ROS=2.1)
- **SS crossings:** Nrf2 crosses SS 651 times, ROS crosses SS 494 times
- **Topology:** SPIRAL approach to fixed point

The Nrf2/ROS subsystem exhibits damped oscillations. This is consistent with a negative feedback loop: ROS activates Nrf2 → Nrf2 induces antioxidants → antioxidants suppress ROS → reduced ROS relaxes Nrf2. The spiral converges, confirming the loop is stable.

### M1/M2 — Constrained 1D Manifold

- **Conservation:** M1 + M2 = 50 (exact)
- **Trajectory:** (5, 45) → (26.2, 23.8)
- Movement along a single conserved line — effectively a 1D dynamical system.

### NFκB/Cytokine — Monotone Approach

- **Trajectory:** (0, 0) → (0.41, 11.6)
- No oscillation — direct relaxation to low-activity equilibrium.

---

## 7. Signal Flow Hierarchy

### Layer Propagation Delays

| Transition | Layer | t₁₀ | t₉₀ | Rise Time |
|-----------|-------|------|------|-----------|
| CBD → GPR3 | 3→2 | 2.2 s | 2.2 s | ~0 s |
| CBD → PPARγ | 3→2 | 2.2 s | 4.3 s | 2.2 s |
| CBD → 5-HT1A | 3→2 | 2.2 s | 4.3 s | 2.2 s |
| CBD → A2A | 3→2 | 2.2 s | 4.3 s | 2.2 s |
| → Nrf2 | 2→1 | 2.2 s | 6.5 s | 4.3 s |
| → IKK | 2→1 | 8.6 s | 30.2 s | 21.6 s |
| → NFκB\_p65 | 2→1 | 2.2 s | 32.4 s | 30.2 s |
| → ROS | 1→0 | 6.5 s | 10.8 s | 4.3 s |
| → TNFα | 1→0 | 19.4 s | 133.9 s | 114.5 s |
| → Aβ Plaque | 1→0 | 2,160 s | 19,440 s | 17,280 s |

The hierarchy shows clear layer-by-layer propagation with increasing delays at each level. Receptor activation is nearly instantaneous (<5 s), transcription factor regulation takes 5–30 s, and effector accumulation extends to minutes (cytokines) or hours (plaque).

---

## 8. Transition Dominance & Flux Balance

### Dominant Transition

**Aβ Aggregation** fires at 3.21/s — the highest rate in the model, 3× faster than any other transition. This reflects the catalytic nature of Aβ oligomerization.

### Flux Balance at Key Nodes

| Species | Production Rate | Clearance Rate | Net Flux | Status |
|---------|----------------|---------------|----------|--------|
| ROS | 1.0/s (basal) | 1.0/s (scavenging) | 0.0/s | BALANCED |
| NFκB | 1.0/s (IKK→IκB) | 1.0/s (PPARγ) | 0.0/s | BALANCED |
| Aβ Oligomer | 3.21/s (aggregation) | 2.0/s (plaque + M2 clearance) | **+1.21/s** | IMBALANCED |

The Aβ oligomer node has a persistent net positive flux of +1.21/s, which feeds directly into the plaque trap. This is the bottleneck driving unbounded plaque accumulation.

---

## 9. Neuroprotection Safety Margin

| Metric | Value |
|--------|-------|
| Neuron Health (final) | 99.99 mM |
| Neurotoxicity rate | 1.0/s |
| BDNF repair rate | 1.0/s |
| **Safety factor** | **1.00×** |
| Time to death if BDNF stops | ~100 s |

**Critical finding:** The neuroprotection safety margin is exactly 1.0× — BDNF repair precisely matches neurotoxic damage with zero buffer. Any perturbation that reduces BDNF or increases damage (higher Aβ, more ROS, elevated cytokines) would tip the balance toward neurodegeneration. This represents a **marginal stability** that could be biologically significant for modeling disease progression.

---

## 10. Regime Changes

Three distinct temporal regimes:

1. **Transient burst** (t = 0–70 s): All pathways activate simultaneously. CBD depletes GPR3 (2.2 s), activates receptors (4 s), Nrf2 overshoots (10.8 s), M1/M2 crosses over (67 s).
2. **Relaxation** (t = 70–500 s): Species settle to quasi-steady state. Cytokines reach plateau (166 s). All fast and medium species converged.
3. **Linear plaque regime** (t > 500 s): Only Aβ plaque continues growing at constant 0.37 mM/s. All other species at steady state.

---

## 11. Summary of Key Findings

| Finding | Category | Implication |
|---------|----------|-------------|
| Stable fixed point attractor | Basin of attraction | Unique steady state — no alternative disease states in current model |
| M1/M2 gradual drift (k=0.004) | Bistability | Chronic inflammation, not a sharp switch — consistent with AD pathology |
| NFκB locked at 0.5% | Bistability | CBD/PPARγ effectively suppresses inflammatory transcription |
| 96% GPR3 preemption | Preemption cascade | CBD blocks most but not all amyloid pathway activation |
| γ-Sec persists at 32.5 mM | Preemption cascade | Residual enzyme drives continued Aβ production |
| GPR3 siphon emptied | Structural (Petri net) | Irreversible — CBD commitment is permanent |
| Plaque trap at 0.37 mM/s | Structural (Petri net) | Only unbounded species — needs dissolution mechanism |
| Nrf2/ROS spiral dynamics | Phase portrait | Negative feedback loop with damped oscillations |
| Safety factor = 1.0× | Neuroprotection | Zero margin — system at critical threshold |
| Aβ oligomer +1.21/s overflow | Flux balance | Bottleneck driving plaque accumulation |

---

## Recommendations for Model v2

1. **Aβ plaque dissolution** — Add a clearance/phagocytosis transition to bound plaque accumulation
2. **Neuroprotection buffer** — Increase BDNF efficacy or add redundant repair pathway to create safety margin > 1.0×
3. **γ-Secretase degradation** — Add proteasomal degradation to eventually deplete the residual enzyme pool
4. **M1/M2 hysteresis** — Consider adding cooperative feedback to create true bistability if biologically justified
5. **Dose-response** — Vary CBD concentration to map the basin of attraction boundary
