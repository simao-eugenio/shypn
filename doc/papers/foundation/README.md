# Foundation Paper: Weak Independence in Biological Petri Nets

This directory contains the **first paper** that establishes the theoretical foundation for the Shypn project.

## Paper Details

**Title**: Weak Independence in Biological Petri Nets: Formalizing Non-Conflicting Coupling for Parallel Continuous Simulation

**Status**: Submitted for publication (November 2025)

**Key Contributions**:
1. Flexibilized classical Petri Net strong independence for biological reality
2. Three coupling modes: Competitive, Convergent, Regulatory
3. 12-tuple Bio-PN extension with regulatory arcs (Σ) and dependency classification (Δ)
4. Enables parallel execution of continuous (ODE) transitions
5. Validated on 100 BioModels: 65% weakly independent transitions, 2-4× speedup

## Theoretical Foundation

**Origin**: Petri Net formalism (Petri 1962, Murata 1989, Chaouiya 2007)

**Mathematical Definition**:
Two transitions τ₁ and τ₂ are weakly independent iff:
```
Input(τ₁) ∩ Input(τ₂) = ∅
```

**Biological Coupling Modes**:
- **Convergent**: Multiple producers of same metabolite (rates add via superposition)
- **Regulatory**: Shared catalysts (read-only access via test arcs)
- **Competitive**: Shared input substrates (sequential execution required)

## Files

### Main Paper (Springer LNCS Format)
- `weak_independence_biopn.tex` - LaTeX source
- `weak_independence_biopn.pdf` - Compiled PDF

### Bioinformatics Format Versions
- `weak_independence_biopn_bioinformatics.tex` - Adapted for Bioinformatics journal
- `weak_independence_biopn_bioinformatics.pdf` - Version 1 (563KB)
- `weak_independence_biopn_bioinformatics_v2.tex` - Revised version
- `weak_independence_biopn_bioinformatics_v2.pdf` - Version 2 (402KB)

### LaTeX Class Files
- `llncs.cls` - Springer LNCS document class
- `llncsdoc.pdf` - LNCS documentation
- `llncsdoc.tex` - LNCS documentation source
- `splncs04.bst` - Bibliography style for LNCS

## Relationship to Second Paper

This paper provides the theoretical foundation that is **extended** in the second paper:

**First Paper** (this directory):
- Weak independence for **continuous** transitions (ODE)
- Parallel execution within continuous subsystems

**Second Paper** (../bioinformatics/):
- Extends weak independence to **hybrid** systems (continuous + stochastic)
- Gibson-inspired parallel τ-leaping
- Fractional catalyst enablement
- Application to gene regulatory networks

## Citation

When citing this work:

```bibtex
@article{eugenio2024weak,
  title={Weak Independence in Biological Petri Nets: Formalizing Non-Conflicting 
         Coupling for Parallel Continuous Simulation},
  author={Eug{\'e}nio, Sim{\~a}o},
  journal={[Submitted for publication]},
  year={2025},
  month={November}
}
```

## Future Work Mentioned

From the paper's conclusion:
> "Extension to stochastic transitions is possible..."

This future work is realized in the second paper (`../bioinformatics/paper.tex`).
