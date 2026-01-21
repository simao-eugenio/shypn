# arXiv 2601.04335 - Thermodynamic Constraints in B. subtilis Sporulation

**Published:** January 7, 2026  
**arXiv ID:** [2601.04335](https://arxiv.org/abs/2601.04335)  
**Category:** q-bio.QM (Quantitative Methods)

## Title

**Thermodynamic Constraints Drive Hierarchical Preemption in Cellular Decision-Making: A Hybrid Petri Net Framework with Application to Bacillus subtilis Sporulation**

## Abstract Summary

This paper demonstrates how thermodynamic constraints drive energy-efficient cellular decision-making through hierarchical preemption mechanisms. Using Bacillus subtilis sporulation as a model system, we show that hybrid Petri nets (combining stochastic regulatory transitions with continuous metabolic sources) can predict ATP commitment thresholds within 7% of experimental values. Under severe energy stress (94% ATP depletion), hierarchical preemption achieves 16× ATP efficiency improvement while maintaining 89% spore yield—demonstrating robust crisis management through signal consumption and pathway prioritization.

## Key Contributions

### 1. Hybrid Petri Net Framework
- **Stochastic-Continuous Integration:** Regulatory decisions (stochastic tau-leaping) + metabolic supply (continuous ODE)
- **Thermodynamic Grounding:** Energy availability directly gates pathway commitment
- **Hierarchical Preemption:** Signal consumption creates irreversible commitment points

### 2. Quantitative Validation
- **ATP Threshold Prediction:** 2.38 mM (SHYPN) vs. 2.21 ± 0.18 mM (experimental)
- **Error: 7%** - First computational prediction of sporulation commitment threshold
- **Basin Geometry:** Phase space analysis reveals thermodynamic landscape structure

### 3. Energy Crisis Management
| Condition | ATP Level | Efficiency | Spore Yield | Key Insight |
|-----------|-----------|-----------|-------------|-------------|
| **Normal** | 5000 mM | 11.6 mM/spore | 75 mM (100%) | Baseline metabolism |
| **Stress** | 300 mM (-94%) | 0.73 mM/spore | 67 mM (89%) | **16× efficiency gain** |
| **Crisis** | 1 mM (-99.7%) | Recovery via regen | Maintained | GTP buffer active |

### 4. Theoretical Advances
- **Signal Consumption Semantics:** ATP functions as both metabolite (mass transfer) and signal (regulatory information)
- **Layer-Based Preemption:** Higher regulatory layers control lower metabolic layers through consumption
- **Commitment Irreversibility:** Signal depletion prevents pathway reversal

## Directory Structure

```
26_arXiv_2601-04335/
├── manuscript/
│   └── 2601.04335v1.pdf        # Published manuscript (9 pages)
├── models/
│   ├── bacillus_sporulation_normal.shy          # Normal conditions (ATP = 5000 mM)
│   ├── bacillus_sporulation_normal_hill_n2.shy  # Hill coefficient n=2 variant
│   ├── bacillus_sporulation_stress.shy          # Stress conditions (ATP = 300 mM)
│   └── bacillus_sporulation_stress_hill_n2.shy  # Stress with Hill n=2
├── scripts/
│   ├── generate_thermodynamic_landscape.py  # Figure 1: Phase portrait
│   ├── plot_basin_attraction.py             # Figure 2: ATP threshold analysis
│   ├── plot_decision_cascade.py             # Figure 3: Hierarchical layers
│   └── plot_thermodynamic_landscape.py      # Alternative visualization
├── figures/
│   ├── thermodynamic_landscape.pdf          # Figure 1: Energy landscape
│   ├── bacillus_basin_of_attraction.pdf     # Figure 2: Basin geometry
│   ├── decision_cascade.pdf                 # Figure 3: Layer architecture
│   ├── bacillus_sporulation_stress.pdf      # Figure 4: Stress response
│   └── README.md                            # Figure descriptions
├── data/
│   └── README.md                            # Simulation data policy (large datasets excluded)
└── README.md                                # This file
```

## Quick Start

### View Published Manuscript
```bash
open manuscript/2601.04335v1.pdf
```

### Open Models in SHYpn
```bash
# Normal conditions
shypn models/bacillus_sporulation_normal.shy

# Stress conditions (demonstrates 16× efficiency)
shypn models/bacillus_sporulation_stress.shy
```

### Regenerate Figures
```bash
cd scripts

# ATP threshold analysis (Figure 2)
python plot_basin_attraction.py

# Thermodynamic landscape (Figure 1)
python generate_thermodynamic_landscape.py

# Hierarchical cascade (Figure 3)
python plot_decision_cascade.py
```

## Model Variants

### 1. Normal Conditions (`bacillus_sporulation_normal.shy`)
- **Initial ATP:** 5000 mM (well-fed cells)
- **Efficiency:** 11.6 mM ATP per spore
- **Spore Yield:** 75 mM (100% baseline)
- **Use Case:** Standard sporulation dynamics

### 2. Stress Conditions (`bacillus_sporulation_stress.shy`)
- **Initial ATP:** 300 mM (94% depletion)
- **Efficiency:** 0.73 mM ATP per spore (**16× improvement**)
- **Spore Yield:** 67 mM (89% maintained)
- **Crisis Management:**
  - ATP minimum: 1 mM (99.7% depletion)
  - Recovery via continuous regeneration
  - GTP buffer: +4974 mM (166% increase)

### 3. Hill Coefficient Variants (`*_hill_n2.shy`)
- **Cooperativity:** Hill coefficient n=2 instead of n=4
- **Purpose:** Sensitivity analysis for threshold sharpness
- **Result:** Broader bistability region, similar threshold position

## Key Results

### 1. ATP Commitment Threshold
**Prediction Method:** Basin of attraction boundary analysis
- **SHYPN Model:** 2.38 mM ATP
- **Experimental Data:** 2.21 ± 0.18 mM (Fujita & Losick 2005)
- **Error:** 7% - validates thermodynamic approach

### 2. Energy Efficiency Under Stress
**Normal → Stress Comparison:**
- ATP consumption: -94% (5000 → 300 mM)
- Efficiency gain: **16× better** (11.6 → 0.73 mM/spore)
- Spore yield: -11% (75 → 67 mM) - robust maintenance
- **Interpretation:** Hierarchical preemption prioritizes commitment over growth

### 3. Crisis Management Capacity
**Extreme Depletion (1 mM ATP):**
- System operates at 99.7% depletion
- Continuous ATP regeneration prevents collapse
- GTP accumulation provides alternative energy source
- Demonstrates robustness of hierarchical control

## Biological Significance

### Cellular Decision Architecture
**Four Hierarchical Layers:**
1. **Layer 0 (Metabolic):** ATP/GTP production and sensing
2. **Layer 1 (Integration):** Spo0A phosphorelay (multi-sensor fusion)
3. **Layer 2 (Commitment):** Threshold-based decision (ATP-gated)
4. **Layer 3 (Execution):** Sigma factor cascade (sporulation program)

**Key Mechanism:** Signal consumption at Layer 2 creates irreversible commitment, enabling Layer 2 to preempt Layer 0-1 metabolic processes.

### Evolutionary Implications
- **Energy Crisis Adaptation:** 16× efficiency allows survival under starvation
- **Robust Commitment:** 7% prediction accuracy suggests thermodynamic optimization
- **Fail-Safe Design:** Continuous ATP regeneration prevents catastrophic collapse

## Theoretical Framework

### Signal Hierarchy Theory Extension
This paper extends the signal hierarchy formalism (arXiv 2601.00036) with:
- **Hybrid Dynamics:** Stochastic (regulatory) + Continuous (metabolic)
- **Thermodynamic Constraints:** Energy availability gates commitment
- **Crisis Management:** Hierarchical preemption under extreme depletion

### Relationship to Prior Work
- **arXiv 2512.17106:** Weak independence foundation (parallel execution)
- **arXiv 2512.22415:** Hierarchical preemption concept (lambda phage)
- **arXiv 2601.00036:** Signal hierarchy formalism (unified theory)
- **arXiv 2601.04335 (this work):** Thermodynamic grounding + crisis management

## Experimental Validation

### Fujita & Losick (2005) Comparison
**Reference:** *Genes & Development* 19:2236-2244

**Experimental Observation:**
- Spo0A threshold: ~2 mM ATP for sporulation commitment
- Gradual increase in Spo0A activity with ATP availability

**SHYPN Prediction:**
- ATP threshold: 2.38 mM (basin boundary analysis)
- **Match: 7% error** - first computational prediction

**Validation Significance:**
- Confirms thermodynamic constraint mechanism
- Demonstrates predictive capability of hybrid Petri nets
- Validates signal consumption formalism

## Computational Methods

### Hybrid Simulation
- **Regulatory Transitions:** Tau-leaping (stochastic)
- **Metabolic Supply:** ODE integration (continuous)
- **Coupling:** ATP concentration gates regulatory firing rates

### Basin Analysis
- **Phase Space:** 2D (ATP, Spo0A-P)
- **Boundary Detection:** Nullcline intersection + stability analysis
- **Threshold Calculation:** Critical ATP where basin width → 0

### Parameter Sources
- **Kinetic Rates:** BRENDA, EcoCyc databases
- **Thresholds:** Fitted to experimental commitment curves
- **Stoichiometry:** Mass balance verified

## Citation

```bibtex
@article{simao2026thermodynamic,
  title={Thermodynamic Constraints Drive Hierarchical Preemption in Cellular Decision-Making: A Hybrid Petri Net Framework with Application to \textit{Bacillus subtilis} Sporulation},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={arXiv preprint arXiv:2601.04335},
  year={2026},
  note={Demonstrates 16$\times$ ATP reduction in stress-induced sporulation through hierarchical preemption},
  url={https://arxiv.org/abs/2601.04335}
}
```

## Related Publications

1. **Weak Independence (2512.17106):** Foundation for coupled parallelism
2. **Lambda Phage (2512.22415):** Hierarchical preemption in UV response
3. **Unified Theory (2601.00036):** Signal hierarchy formalism with V. fischeri
4. **This Work (2601.04335):** Thermodynamic constraints + B. subtilis validation

## Software Requirements

- **SHYpn Framework:** Python 3.8+
- **Dependencies:** NumPy, SciPy, Matplotlib, NetworkX
- **Simulator:** Hybrid tau-leaping + ODE solver

## Contact

**Author:** Eugénio Simão  
**Repository:** https://github.com/eugeniosimao/shypn  
**Issues:** Use GitHub issue tracker for questions about reproduction

## License

Code and models: MIT License  
Manuscript: CC BY 4.0 (arXiv)

---

**Last Updated:** January 2026  
**Status:** Published on arXiv
