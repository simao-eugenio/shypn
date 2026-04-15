# Key References for Signal Hierarchy Paper

---

## Foundation (Must Cite)

**1. Weak Independence Paper (Our Previous Work)**
- Simão, E. (2025). Weak Independence and Coupled Parallelism in Biological Petri Nets. arXiv:2512.17106
- **Why:** Establishes 12-tuple formalism, weak independence theory
- **Section:** Introduction (prior work), Methods (formalism)

**2. Lambda Phage Biology**
- Ptashne, M. (2004). *A Genetic Switch: Phage Lambda Revisited*. Cold Spring Harbor Laboratory Press
- **Why:** Canonical reference for lambda lysogeny decision
- **Section:** Introduction, Methods (biological background)

---

## Bio-PN Formalism

**3. Original Petri Net Application to Biology**
- Reddy, V. N., Mavrovouniotis, M. L., & Liebman, M. N. (1993). Petri net representations in metabolic pathways. *ISMB*, 1, 328-336
- **Why:** First application of Petri nets to metabolism
- **Section:** Introduction (historical context)

**4. Bio-PN Extensions**
- Hardy, S., & Robillard, P. N. (2004). Modeling and simulation of molecular biology systems using Petri nets. *Journal of Bioinformatics and Computational Biology*, 2(04), 595-613
- **Why:** Extended Bio-PN formalism
- **Section:** Introduction (prior work)

**5. Qualitative Petri Nets**
- Gilbert, D., & Heiner, M. (2006). From Petri nets to differential equations. *Natural Computing*, 5(3), 255-270
- **Why:** Bridges qualitative/quantitative modeling
- **Section:** Discussion (comparison)

---

## Regulatory Networks

**6. Lambda Phage Modeling**
- Arkin, A., Ross, J., & McAdams, H. H. (1998). Stochastic kinetic analysis of developmental pathway bifurcation in phage lambda-infected *Escherichia coli* cells. *Genetics*, 149(4), 1633-1648
- **Why:** Stochastic model of lambda decision
- **Section:** Methods (prior lambda models)

**7. Gene Regulatory Networks**
- Chaouiya, C. (2007). Petri net modelling of biological networks. *Briefings in Bioinformatics*, 8(4), 210-219
- **Why:** Gene regulation in Petri nets
- **Section:** Introduction, Discussion

---

## SBML and Standards

**8. SBML**
- Hucka, M., et al. (2003). The systems biology markup language (SBML). *Bioinformatics*, 19(4), 524-531
- **Why:** Standard format comparison
- **Section:** Discussion (comparison to SBML qualifiers)

**9. SBML Qualifiers**
- Le Novère, N., et al. (2009). The Systems Biology Graphical Notation. *Nature Biotechnology*, 27(8), 735-741
- **Why:** Visual annotation standards
- **Section:** Discussion (our approach vs SBGN)

---

## Stochastic Simulation

**10. Gillespie Algorithm**
- Gillespie, D. T. (1977). Exact stochastic simulation of coupled chemical reactions. *The Journal of Physical Chemistry*, 81(25), 2340-2361
- **Why:** Simulation algorithm used
- **Section:** Methods (simulation protocol)

**11. Tau-Leaping**
- Gillespie, D. T. (2001). Approximate accelerated stochastic simulation of chemically reacting systems. *The Journal of Chemical Physics*, 115(4), 1716-1733
- **Why:** Approximate method we use
- **Section:** Methods (tau-leaping details)

---

## Modularity and Architecture

**12. Modular Systems Biology**
- Hartwell, L. H., Hopfield, J. J., Leibler, S., & Murray, A. W. (1999). From molecular to modular cell biology. *Nature*, 402(6761), C47-C52
- **Why:** Modularity principle in biology
- **Section:** Introduction, Discussion (modular architecture)

**13. Signal Transduction**
- Kholodenko, B. N. (2006). Cell-signalling dynamics in time and space. *Nature Reviews Molecular Cell Biology*, 7(3), 165-176
- **Why:** Information flow in biological systems
- **Section:** Theory (signal vs material distinction)

---

## Quorum Sensing (Additional Example)

**14. Bacterial Communication**
- Miller, M. B., & Bassler, B. L. (2001). Quorum sensing in bacteria. *Annual Reviews in Microbiology*, 55(1), 165-199
- **Why:** Quorum sensing as signal-based coordination
- **Section:** Generalization (quorum sensing example)

**15. V. fischeri**
- Fuqua, W. C., Winans, S. C., & Greenberg, E. P. (1994). Quorum sensing in bacteria. *Journal of Bacteriology*, 176(2), 269
- **Why:** Specific organism for example
- **Section:** Generalization

---

## Compartmentalization

**16. Spatial Modeling**
- Meier-Schellersheim, M., Fraser, I. D., & Klauschen, F. (2009). Multiscale modeling for biologists. *Wiley Interdisciplinary Reviews: Systems Biology and Medicine*, 1(1), 4-14
- **Why:** Spatial/compartmental modeling
- **Section:** Generalization (compartment example)

---

## Software Tools

**17. SHYpn (Our Tool)**
- Simão, E. (2025). SHYpn: Stochastic Hybrid Petri Nets for Systems Biology. GitHub repository
- **Why:** Implementation platform
- **Section:** Methods (software), Data Availability

**18. COPASI**
- Hoops, S., et al. (2006). COPASI—a COmplex PAthway SImulator. *Bioinformatics*, 22(24), 3067-3074
- **Why:** Comparison tool
- **Section:** Discussion (other software)

**19. Cell Designer**
- Funahashi, A., et al. (2003). CellDesigner. *Biosilico*, 1(5), 159-162
- **Why:** Visual modeling tool comparison
- **Section:** Discussion

---

## Statistics

**20. Chi-square Test**
- Pearson, K. (1900). On the criterion that a given system of deviations. *Philosophical Magazine*, 50(302), 157-175
- **Why:** Statistical validation method
- **Section:** Methods (statistical tests)

---

## BibTeX Entries

Save to `manuscript/references.bib`:

```bibtex
@article{simao2025weak,
  title={Weak Independence and Coupled Parallelism in Biological Petri Nets},
  author={Sim{\~a}o, Eug{\'e}nio},
  journal={arXiv preprint arXiv:2512.17106},
  year={2025}
}

@book{ptashne2004genetic,
  title={A genetic switch: phage lambda revisited},
  author={Ptashne, Mark},
  year={2004},
  publisher={Cold Spring Harbor Laboratory Press}
}

@inproceedings{reddy1993petri,
  title={Petri net representations in metabolic pathways},
  author={Reddy, Venkatramana N and Mavrovouniotis, Michael L and Liebman, Michael N},
  booktitle={ISMB},
  volume={1},
  pages={328--336},
  year={1993}
}

@article{gillespie1977exact,
  title={Exact stochastic simulation of coupled chemical reactions},
  author={Gillespie, Daniel T},
  journal={The journal of physical chemistry},
  volume={81},
  number={25},
  pages={2340--2361},
  year={1977}
}

// ... (additional entries)
```

---

## Citation Strategy

**Introduction:**
- 5-7 citations (Bio-PN history, lambda phage, modularity)

**Theory:**
- 2-3 citations (formalism foundations)

**Methods:**
- 4-5 citations (lambda biology, simulation algorithms)

**Results:**
- 1-2 citations (statistical tests)

**Discussion:**
- 6-8 citations (SBML, tools, future work)

**Total target:** 20-25 references (typical for methods paper)

---

## TODO

- [ ] Obtain full PDFs for all references
- [ ] Create complete BibTeX file
- [ ] Verify citation accuracy
- [ ] Add DOIs where available
- [ ] Check journal requirements (citation style)
