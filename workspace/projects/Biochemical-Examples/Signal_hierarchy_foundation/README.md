# Signal Hierarchy Theory for Biological Petri Nets

**Foundation Manuscript - Submitted to PLOS Computational Biology (January 2026)**

## Overview
This directory contains the complete manuscript and figures for:

> **"Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics of Hierarchical Regulatory Control"**
> 
> Eugênio Simão  
> Department of Informatics and Statistics  
> Federal University of Santa Catarina (UFSC), Brazil

## Contents
- **`manuscript/`** - PLOS-formatted LaTeX source + compiled PDF (20 pages)
- **`figures/`** - Publication figures (PDF/PNG) + generation script
- **`supplementary/`** - Cover letter for PLOS submission
- **`scripts/`** - Compilation automation

## Key Contributions
1. **Signal Hierarchy Theory** - Formal semantics for hierarchical regulatory control
2. **Signal Flow Arcs** - Consumption-based information channels (vs test arcs)
3. **Hierarchical Layers** - Multi-scale organization with preemption mechanisms
4. **Quantitative Validation** - B. subtilis ATP threshold: 2.38 mM predicted vs 2.21±0.18 mM experimental (7% error)

## Quick Compilation
```bash
cd manuscript
pdflatex main_plos.tex
bibtex main_plos
pdflatex main_plos.tex
pdflatex main_plos.tex

# Or use script
cd ../scripts && ./compile_manuscript.sh
```

## Manuscript Structure
**Single-file LaTeX document** (`main_plos.tex`, 204 lines):
- Abstract (280 words)
- Keywords (9 terms)
- Author Summary (185 words)
- Introduction - Biological motivation for signal hierarchy
- Background - Classical Petri nets, Bio-PNs, expressiveness gap
- Signal Hierarchy Theory - Signal places, flow arcs, hierarchical layers
- Weak Independence - Computational foundation for parallel execution
- Unified Formalism - Integration with Bio-PN
- Validation - B. subtilis sporulation (ATP-gated decision)
- Discussion - Theoretical significance, limitations
- Conclusion - Broader implications

## Figures
- **Figure 1** (`decision_cascade.pdf`) - Signal hierarchy schematic
- **Figure 2** (`bacillus_atp_threshold.pdf`) - ATP threshold prediction (main result)

## Citation
```bibtex
@article{simao2026signal,
  title={Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics of Hierarchical Regulatory Control},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={PLOS Computational Biology},
  year={2026},
  note={Submitted January 2026}
}
```

## Related Work
- **Weak Independence Theory**: [arXiv:2512.17106](https://arxiv.org/abs/2512.17106)
- **SHYPN Software**: https://github.com/simao-eugenio/shypn (MIT License)
- **Biochemical Examples**: See examples 01-22 in parent directory

## Data Availability
All analysis and modeling performed using SHYPN software (open-source).  
Model files available upon request. Code repository: github.com/simao-eugenio/shypn

## License
- **Manuscript**: CC-BY 4.0 (PLOS standard)
- **Software**: MIT License
- **Figures**: CC-BY 4.0

## Contact
Eugênio Simão  
eugenio.simao@posgrad.ufsc.br
