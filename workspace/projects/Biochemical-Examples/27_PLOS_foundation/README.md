# PLOS Computational Biology Foundation Manuscript

**Journal:** PLOS Computational Biology  
**Submission ID:** PCOMPBIOL-D-26-00133  
**Status:** Under review (submitted December 2025, revised January 2026)  
**Category:** Methods

## Title

**Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics and Validation**

## Abstract Summary

This manuscript introduces signal hierarchy theory, a formal extension to Biological Petri Nets that distinguishes between metabolic mass transfer (normal arcs) and regulatory information flow (signal flow arcs). The formalism provides consumption semantics for regulatory signals, enabling modeling of irreversible commitment and hierarchical preemption in cellular decision-making. We validate the theory through: (1) weak independence analysis of 100 BioModels (96.93% transitions parallelizable), (2) quantitative ATP threshold prediction for B. subtilis sporulation (7% error vs. experimental), and (3) hierarchical preemption demonstration in lambda phage UV response. The 13-tuple formalism extends classical Bio-PN with signal places, flow arcs, and hierarchical layer assignments, providing complete formal semantics for multi-scale regulatory control.

## Key Contributions

### 1. Weak Independence Theory
**Foundation for parallel execution in biological systems**

- **Definition:** Transitions sharing catalysts but not substrates can execute concurrently
- **Prevalence:** 96.93% of transitions in 100 BioModels are weakly independent
- **Impact:** 2-4× computational speedup through parallelization
- **Significance:** First large-scale empirical study of biological pathway parallelism

**Key Insight:** Most biological reactions share enzymes (catalysis) but not substrates (consumption), enabling massive parallelization unlike traditional concurrent systems.

### 2. Signal Hierarchy Theory
**Novel formalism for regulatory information flow**

- **Signal Places (Ψ):** Information channels distinct from metabolic places
- **Signal Flow Arcs:** Consumption-based information transfer (vs. non-consuming test arcs)
- **Hierarchical Layers (λ):** Multi-scale organization with preemption
- **Commitment Semantics:** Signal depletion creates irreversibility

**Key Innovation:** First Petri net formalism to model signal consumption, bridging gap between metabolic mass transfer and regulatory control.

### 3. Unified 13-Tuple Formalism
**Complete mathematical framework**

Extended Bio-PN definition:
```
N = (P, T, F, Ψ, Fₛ, Fₜ, λ, W, Wₛ, θ, M₀, Φ, C)

P:  Places (metabolites)
T:  Transitions (reactions)
F:  Normal arcs (mass transfer)
Ψ:  Signal places (information channels) ← NEW
Fₛ: Signal flow arcs (consumption) ← NEW
Fₜ: Test arcs (catalysis)
λ:  Layer function (hierarchy) ← NEW
W:  Arc weights (stoichiometry)
Wₛ: Signal arc weights ← NEW
θ:  Transition thresholds ← NEW
M₀: Initial marking
Φ:  Kinetic annotations
C:  Compartments
```

**Arc Taxonomy:**
- **Normal:** Consume tokens (substrates)
- **Test:** Read without consuming (catalysts)
- **Signal Flow:** Consume regulatory signals (commitment)

### 4. Quantitative Validation
**B. subtilis sporulation commitment threshold**

| Metric | SHYPN Prediction | Experimental | Error |
|--------|------------------|--------------|-------|
| **ATP Threshold** | 2.38 mM | 2.21 ± 0.18 mM | **7%** |

**Method:** Basin of attraction boundary analysis in ATP-Spo0A phase space

**Significance:**
- First computational prediction of sporulation commitment threshold
- Validates signal consumption semantics
- Demonstrates dual role of ATP (metabolite + signal)

## Directory Structure

```
27_PLOS_foundation/
├── manuscript/
│   └── main_plos.pdf                  # Submitted manuscript
├── models/
│   └── bacillus_sporulation_stress.shy # B. subtilis validation model
├── scripts/
│   └── generate_figure.py             # Figure 2: ATP threshold plot
├── figures/
│   ├── decision_cascade.pdf           # Figure 1: Hierarchical architecture
│   ├── bacillus_atp_threshold.pdf     # Figure 2: Threshold prediction (MAIN)
│   ├── bacillus_basin_of_attraction.pdf # Figure 3: Phase space analysis
│   └── README.md                      # Figure descriptions
├── data/
│   └── README.md                      # Data policy (BioModels excluded)
└── README.md                          # This file
```

## Quick Start

### View Manuscript
```bash
open manuscript/main_plos.pdf
```

### Open Validation Model
```bash
shypn models/bacillus_sporulation_stress.shy
```

### Regenerate Main Figure (ATP Threshold)
```bash
cd scripts
python generate_figure.py
```

## Manuscript Structure

**Length:** ~15 pages (PLOS format, single-spaced)

**Sections:**
1. **Abstract** (250 words) - Theory focus, quantitative validation
2. **Author Summary** (185 words) - Significance for broader audience
3. **Introduction** (2 pages) - Motivation, gap analysis, contributions
4. **Background** (3 pages) - Classical PN, Bio-PN, recent work
5. **Weak Independence Theory** (3 pages) - Definitions, proofs, BioModels analysis
6. **Signal Hierarchy Theory** (3 pages) - Signal places, flow arcs, layers
7. **Unified Formalism** (2 pages) - 13-tuple definition, arc taxonomy
8. **Validation** (3.5 pages) - B. subtilis (ATP threshold), lambda phage, V. fischeri
9. **Discussion** (1.5 pages) - Significance, comparison, future work
10. **Conclusion** (0.5 pages) - Summary, broader impact

**Figures:**
- Figure 1: Decision cascade architecture (schematic)
- Figure 2: ATP threshold prediction (quantitative validation) ⭐
- Figure 3: Basin of attraction geometry (phase space)

**Tables:**
- Table 1: Weak independence statistics (100 BioModels)
- Table 2: Case study comparisons
- Table 3: Performance benchmarks

## Key Results

### 1. Weak Independence Prevalence
**Dataset:** 100 curated BioModels (diverse biological systems)

| Category | Transitions | Percentage |
|----------|-------------|------------|
| **Weakly Independent** | 10,515 | **96.93%** |
| Strongly Dependent | 332 | 3.07% |
| **Total** | 10,847 | 100% |

**Implications:**
- 97% of biological reactions can execute in parallel
- Computational speedup: 2-4× with weak independence
- Validation across glycolysis, TCA cycle, signaling cascades, gene regulation

### 2. B. subtilis Sporulation Validation
**System:** ATP-dependent commitment to sporulation vs. vegetative growth

**Prediction Method:** Basin boundary analysis
- Phase space: ATP (horizontal) × Spo0A-P (vertical)
- Threshold: Critical ATP where sporulation basin width → 0
- Result: **2.38 mM ATP**

**Experimental Comparison:**
- Fujita & Losick (2005): 2.21 ± 0.18 mM
- **Error: 7%** (within experimental uncertainty)

**Model Details:**
- 13 places (ATP, GTP, Spo0A variants, sigma factors)
- 11 transitions (phosphorylation, dephosphorylation, activation)
- Signal flow arc: ATP consumption at commitment point
- Hybrid dynamics: Stochastic regulatory + continuous metabolic

### 3. Lambda Phage Hierarchical Preemption
**System:** Lysis-lysogeny decision with UV override

**Result:** RecA signal shows **2× priority** over environmental signals
- Layer 1 (UV damage): RecA-mediated CI cleavage
- Layer 2 (Integration): CII protein level
- Layer 3 (Decision): CI vs. Cro bistability

**Validation:** Matches Ptashne (2004) experimental bistability ratios
- Normal: 42:48 lysogenic:lytic
- UV stress: 4:86 (RecA overrides metabolic signals)

### 4. V. fischeri Quorum Sensing
**System:** Population-density-dependent bioluminescence

**Demonstration:** Signal place formalism
- AHL signal acts as information channel
- LuxR activation threshold
- Population-level coordination

**Full details:** See arXiv 2601.00036

## Biological Systems Addressed

### Primary Validation: B. subtilis Sporulation
- **Question:** What ATP level triggers irreversible commitment?
- **Answer:** 2.38 mM (7% error vs. experimental)
- **Mechanism:** Signal consumption creates commitment point

### Case Study 1: Lambda Phage
- **Question:** How does UV damage override metabolic signals?
- **Answer:** Hierarchical preemption (2× priority for RecA)
- **System:** Bistable lysis-lysogeny switch

### Case Study 2: V. fischeri
- **Question:** How do bacteria coordinate at population level?
- **Answer:** Signal place for AHL-mediated communication
- **System:** Quorum sensing bioluminescence

### Large-Scale Analysis: 100 BioModels
- **Question:** How prevalent is weak independence?
- **Answer:** 96.93% across diverse biological pathways
- **Systems:** Glycolysis, TCA, MAPK, gene regulation, cell cycle

## Theoretical Significance

### 1. Fills Expressiveness Gap
**Problem:** Classical Bio-PN cannot model signal consumption

**Prior Work Limitations:**
- Murata (1989): Test arcs for catalysis, but no consumption semantics
- Heiner (2008): Bio-PN formalism, but all regulatory arcs are test arcs
- Aduddell (2024): Inhibitor arcs, still no consumption
- Genovese (2021): Hierarchical PN, but no biological context

**Our Solution:** Signal flow arcs enable consumption-based regulatory control

### 2. Enables New Analyses
**Previously inexpressible:**
- ✅ Quantitative commitment threshold calculation
- ✅ Irreversibility through signal depletion
- ✅ Hierarchical preemption mechanisms
- ✅ Basin of attraction geometry for decisions
- ✅ Distinction between reversible regulation and irreversible commitment

### 3. Bridges Scales
**Multi-level organization:**
- Layer 0: Metabolic reactions (ATP production)
- Layer 1: Signal integration (phosphorelays)
- Layer 2: Commitment decisions (thresholds)
- Layer 3: Execution programs (cascades)

**Coupling:** Higher layers control lower through signal consumption

### 4. Computational Foundation
**Weak independence → parallelization:**
- 96.93% of biological reactions can run concurrently
- 2-4× speedup demonstrated
- Scales to 1000+ transition models

## Comparison with Prior Work

| Feature | Murata 1989 | Heiner 2008 | Aduddell 2024 | This Work |
|---------|-------------|-------------|---------------|-----------|
| **Test Arcs** | ✓ (catalysis) | ✓ (enzymes) | ✓ | ✓ |
| **Inhibitor Arcs** | ✓ | ✓ | ✓ | ✓ |
| **Signal Consumption** | ✗ | ✗ | ✗ | ✓ (NEW) |
| **Hierarchical Layers** | ✗ | ✗ | ✗ | ✓ (NEW) |
| **Weak Independence** | ✗ | ✗ | ✗ | ✓ (NEW) |
| **Quantitative Validation** | Theory only | Qualitative | Theory only | **7% error** |

**Key Advance:** First formalism with consumption semantics for regulatory signals + large-scale empirical validation.

## Submission History

### Initial Submission (December 2025)
- Manuscript submitted to PLOS Computational Biology
- Submission ID: PCOMPBIOL-D-26-00133
- Category: Research Article (Methods)

### Revision (January 2026)
- Addressed reviewer feedback:
  1. Expanded weak independence analysis (100 BioModels)
  2. Added quantitative validation (B. subtilis threshold)
  3. Strengthened comparison with prior work
  4. Clarified arc taxonomy and formal definitions

### Current Status
- **Under review** (awaiting second-round feedback)
- Expected decision: February-March 2026

## Related Publications

This foundation manuscript integrates results from four arXiv papers:

1. **arXiv 2512.17106** - Weak Independence (Lac operon, BioModels analysis)
2. **arXiv 2512.22415** - Hierarchical Preemption (Lambda phage UV response)
3. **arXiv 2601.00036** - Unified Formalism (V. fischeri, 13-tuple definition)
4. **arXiv 2601.04335** - Thermodynamic Constraints (B. subtilis crisis management)

**Relationship:**
- arXiv papers: Focused contributions (single system each)
- PLOS manuscript: Comprehensive theory + validation (100+ systems)

## Data Availability

### Included in Repository
✅ B. subtilis sporulation model (.shy)  
✅ Figure generation scripts  
✅ Published figures (3 PDFs)  
✅ Manuscript PDF

### Excluded (Reproducible from Public Sources)
❌ 100 BioModels SBML files (download from BioModels Database)  
❌ Batch simulation results (regenerate with provided scripts)  
❌ Statistical analysis intermediate files (recalculate from models)

### External Data Sources
- **BioModels Database:** https://www.ebi.ac.uk/biomodels/
- **Experimental data:** Fujita & Losick (2005), Genes Dev 19:2236-2244

## Software Requirements

- **SHYpn Framework:** Python 3.8+
- **Dependencies:** NumPy, SciPy, Matplotlib, NetworkX
- **Simulator:** Hybrid tau-leaping + ODE solver

**Installation:**
```bash
pip install shypn
```

## Reproducibility

### Minimal Reproduction (Figure 2 only)
```bash
cd scripts
python generate_figure.py
# Output: bacillus_atp_threshold.pdf
# Expected: 2.38 mM threshold line + experimental point
# Runtime: < 5 seconds
```

### Full Reproduction (All Figures + Validation)
1. Download 100 BioModels (see `data/README.md`)
2. Run weak independence analysis (scripts in arXiv papers)
3. Regenerate B. subtilis threshold plot
4. Compare with manuscript Table 1 and Figure 2

**Expected Runtime:** 1-2 hours for full reproduction

## Citation

### PLOS Manuscript (Submitted)
```bibtex
@article{simao2026signal,
  title={Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics and Validation},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={PLOS Computational Biology},
  note={Under review. Submission ID: PCOMPBIOL-D-26-00133},
  year={2026}
}
```

### arXiv Preprints (Published)
See individual directories (`23_`, `24_`, `25_`, `26_`) for arXiv-specific citations.

## Contact

**Author:** Eugénio Simão  
**Repository:** https://github.com/eugeniosimao/shypn  
**Issues:** Use GitHub issue tracker for technical questions  
**Manuscript Questions:** Email via PLOS submission system

## Future Work

### Planned Enhancements
- **Chemical database integration:** ΔG° calculations from ChEBI/MetaCyc
- **Stochastic master equation:** Exact solutions for small models
- **GPU acceleration:** Parallel simulation of weakly independent transitions
- **Model checker integration:** Formal verification of hierarchical properties

### Applications
- **Synthetic biology:** Design robust decision circuits with formal guarantees
- **Drug discovery:** Identify ATP-dependent pathway vulnerabilities
- **Systems biology:** Multi-scale model integration (metabolic + regulatory)

## License

**Manuscript:** © 2026 Eugénio Simão (submitted to PLOS Computational Biology)  
**Code and Models:** MIT License  
**Figures:** CC BY 4.0

---

**Last Updated:** January 2026  
**Manuscript Status:** Under review (PLOS Computational Biology)  
**Repository Status:** Complete (ready for GitHub publication)
