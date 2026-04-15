# Signal Partition Theory Paper

**Status:** 🚧 In Development  
**Target Journal:** PLOS Computational Biology / Bioinformatics (Oxford)  
**Expected Submission:** Q1 2026

---

## Paper Information

**Title:** Information Flow Drives Compartmentalization in the Lambda Phage Decision Network: A Signal Hierarchy Approach

**Alternative Title:** Signal Partition Theory: Disentangling Material and Information Flow in Biochemical Petri Nets

**Authors:** Eugénio Simão

**Abstract:** (Draft in `manuscript/abstract.md`)

---

## Directory Structure

```
signal_hierarchy/
├── manuscript/          # Main paper files
│   ├── main.tex         # LaTeX source
│   ├── abstract.md      # Abstract draft
│   ├── sections/        # Individual sections
│   └── references.bib   # Bibliography
│
├── figures/             # Publication figures
│   ├── figure1_theory/
│   ├── figure2_lambda/
│   ├── figure3_validation/
│   ├── figure4_examples/
│   └── scripts/         # Figure generation code
│
├── data/                # Supporting data
│   ├── lambda_phage/    # Case study simulations
│   ├── quorum_sensing/  # Additional example
│   └── statistics/      # Statistical analysis
│
├── models/              # Model files for paper
│   ├── lambda_original.shy
│   ├── lambda_refactored.shy
│   └── comparison_notes.md
│
├── supplementary/       # Supplementary materials
│   ├── additional_examples/
│   ├── extended_theory/
│   └── code_listings/
│
└── submission/          # Journal submission package
    └── (generated before submission)
```

---

## Key Contributions

1. **Theoretical:** Information flow drives compartmentalization (information bottlenecks → functional boundaries)
2. **Architecture:** Hierarchical Lambda phage network (4 layers, environmental sensors → decision core)
3. **Quantification:** ✓ **Mutual information analysis completed (Dec 26, 2025)**
   - CII: 74.3% decision information (proximal integrator)
   - RecA: 43.0% decision information (2.01× hierarchical advantage over environmental signals)
   - Environmental signals (ATP, Metabolic, Cycle): 1-8% each (hierarchical filtering confirmed)
4. **Validation:** ✓ **Hierarchical override experimentally validated**
   - UV damage (RecA>50): 71% lytic (blocks CII lysogenic signal)
   - NO UV (RecA=0): 57% lysogenic (CII drives CI accumulation)
   - Information architecture matches biochemical control flow
5. **Framework:** Signal Partition Theory (P_m ∩ P_s = ∅) as implementation mechanism
6. **Implementation:** SHYpn hierarchical modeling with 200+ replicate validation

---

## Recent Progress (Dec 25-26, 2025)

### ✓ Phase 2 Complete: Hierarchical Signal Integration

**Model**: lambda_hierarchical_v3.shy (23 places, 36 transitions, 65 arcs)

**Key Results**:
- Information flow analysis completed on 200 replicates (100 UV + 100 NO UV)
- RecA hierarchical priority quantified: 2.01× advantage over environmental signals
- CII identified as proximal integrator carrying 74% of decision information
- Environmental signals weak (1-8% each), validating hierarchical filtering
- Attractor landscape visualization created (ΔCI=61.4 mM separation)

**Documentation**:
- [INFORMATION_FLOW_RESULTS.md](INFORMATION_FLOW_RESULTS.md) - Complete mutual information analysis
- [PHASE2_IMPLEMENTATION_PLAN.md](PHASE2_IMPLEMENTATION_PLAN.md) - Model architecture and parameters
- [HIERARCHICAL_IMPLEMENTATION_PROGRESS.md](HIERARCHICAL_IMPLEMENTATION_PROGRESS.md) - Development timeline

**Data**:
- Batch UV: data/results/batch_20251225_235533/ (100 runs, stochastic UV)
- Batch NO UV: data/results/batch_20251226_010448/ (100 runs, RecA=0)
- Model: data/lambda_hierarchical_v3.shy
- Figures: Attractor landscape plot (batch_20251225_235533/attractor_landscape.png)

---

## Timeline

- [x] Reconnaissance & planning (Dec 22, 2025)
- [x] **Phase 1**: Symmetric bistable model with UV (Dec 17, 2025)
- [x] **Phase 2**: Hierarchical signal integration (Dec 25-26, 2025)
  - [x] Build hierarchical model v3 (environmental sensors + CII)
  - [x] Optimize Hill cooperativity parameters (coefficient 3.5, Ki=8/6)
  - [x] Batch simulations (200 replicates: UV + NO UV)
  - [x] Mutual information analysis (RecA 2.01× advantage validated)
  - [x] Attractor landscape visualization
- [ ] Draft Results section (Week 1)
- [ ] Theory section + Figure 1 (hierarchical architecture) (Week 2)
- [ ] Lambda case study + Figures 2-3 (MI analysis, attractors) (Week 3)
- [ ] Additional examples + Figure 4 (optional) (Week 4)
- [ ] Discussion & Conclusion (Week 5-6)
- [ ] Internal review & revision (Week 7-8)
- [ ] Submission preparation (Week 9)
- [ ] Submit to journal (Week 10)

**Current Status**: Phase 2 Complete ✓ - Ready for manuscript writing

---

## References

**Foundation:**
- arXiv:2512.17106 - Weak Independence paper (establishes 12-tuple formalism)
- Lambda Phage Switch models (workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/)
- Signal hierarchy theory (doc/signal_hierarchy/)

**Related Work:**
- Reddy et al. 1993 - Petri net formalism
- Hardy & Robillard 2004 - Bio-PN extensions
- Gilbert & Heiner 2006 - Qualitative/quantitative modeling

---

## Notes

This is a **private development directory** - not tracked in git repository.
