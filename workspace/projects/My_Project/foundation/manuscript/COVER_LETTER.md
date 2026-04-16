# Cover Letter for PLOS Computational Biology

---

**Date:** January 19, 2026

**To:** Editor-in-Chief  
PLOS Computational Biology

**Subject:** Submission of Manuscript - "Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics of Hierarchical Regulatory Control"

---

Dear Editor,

I am pleased to submit our manuscript entitled **"Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics of Hierarchical Regulatory Control"** for consideration as a Research Article in PLOS Computational Biology.

## Manuscript Summary

This work introduces a novel theoretical framework addressing a fundamental limitation in biological Petri net theory: the inability to model regulatory signal consumption during cellular decision-making. While classical test arcs represent non-consuming catalytic reads, many biological regulatory signals are consumed during decision processes (e.g., growth factor depletion, CI repressor binding, ATP expenditure), making decisions irreversible and enabling hierarchical pathway preemption.

**Key Contributions:**

1. **Theoretical Innovation**: We extend Bio-PN formalism with signal places (information channels) and signal flow arcs (consumption semantics), providing formal definitions for hierarchical layer assignment and preemption mechanisms. This bridges the expressiveness gap between metabolic mass transfer and regulatory information flow within unified modeling frameworks.

2. **Proof-of-Concept Validation**: Application to *Bacillus subtilis* sporulation demonstrates the formalism's predictive capability. Signal hierarchy analysis computes ATP commitment threshold at 2.38 mM, matching experimental measurements (2.21 ± 0.18 mM, 7% error)—a quantitative prediction inexpressible in classical Bio-PN lacking consumption semantics.

3. **Novel Analytical Capabilities**: The formalism enables previously inexpressible analyses: (i) quantitative threshold determination for energy-gated decisions, (ii) basin of attraction geometry quantification for commitment reliability, and (iii) formal distinction between irreversible commitment (signal consumption) and reversible regulation (test arcs).

## Significance and Impact

This work provides mathematical foundation for a new class of systems biology analyses with applications in:
- **Synthetic Biology**: Designing robust decision circuits with formal commitment guarantees
- **Drug Discovery**: Identifying ATP-dependent control points for therapeutic targeting
- **Precision Medicine**: Predicting cellular responses to metabolic interventions

The formalism addresses a recognized gap in computational systems biology—existing frameworks separate metabolism from regulation, coupled only through informal parameter dependencies. Our unified approach treats energy status (ATP) simultaneously as metabolite and regulatory signal, enabling bidirectional analysis of metabolic-regulatory coupling.

## Why PLOS Computational Biology?

This manuscript is ideally suited for PLOS Computational Biology for several reasons:

1. **Theoretical Rigor with Biological Relevance**: The work combines formal mathematical definitions with biological motivation and experimental validation, aligning with PLOS CompBiol's emphasis on computational methods addressing biological questions.

2. **Broad Interdisciplinary Impact**: The formalism bridges Petri net theory, systems biology, and metabolic engineering, serving diverse communities from theoretical computer science to experimental biology.

3. **Open Science Commitment**: All code and data are publicly available (GitHub: https://github.com/simao-eugenio/shypn, MIT license). This aligns with PLOS's open access and reproducibility values.

4. **Accessible Presentation**: The manuscript includes a non-technical Author Summary tailored for PLOS's broad readership, making theoretical concepts accessible to biologists while maintaining mathematical rigor for computational scientists.

## Originality and Ethics Statement

I confirm that:
- This manuscript presents original research not previously published
- The work is not currently under consideration at any other journal
- All authors have approved the manuscript and agree to its submission
- No external funding was received for this work
- There are no competing interests to declare
- All experimental data cited are from published literature (properly attributed)

## Suggested Reviewers

We respectfully suggest the following experts as potential reviewers (no conflicts of interest):

1. **Dr. Monika Heiner**  
   Brandenburg University of Technology, Germany  
   Email: monika.heiner@b-tu.de  
   *Expertise: Biological Petri nets, model checking, systems biology*

2. **Dr. David Gilbert**  
   Brunel University London, UK  
   Email: david.gilbert@brunel.ac.uk  
   *Expertise: Petri net formalism, computational systems biology*

3. **Dr. Claudine Chaouiya**  
   Aix-Marseille Université, France  
   Email: claudine.chaouiya@univ-amu.fr  
   *Expertise: Qualitative Petri net modeling, regulatory networks*

4. **Dr. Franco Blanchini**  
   University of Udine, Italy  
   Email: blanchini@uniud.it  
   *Expertise: Dynamical systems, Lyapunov functions, network stability*

5. **Dr. Matthew Johnston**  
   San José State University, USA  
   Email: matthew.johnston@sjsu.edu  
   *Expertise: Chemical reaction networks, mathematical biology*

## Supporting Materials

The submission includes:
- Main manuscript (20 pages, LaTeX format)
- Figure 1: Energy-gated metabolic switch (illustrative model)
- Figure 2: ATP commitment threshold in *B. subtilis* (quantitative validation)
- Table 1: 13-tuple formalism components
- Table 2: Comparison with related frameworks
- References (24 citations)
- Source code repository (GitHub, MIT license)

All materials comply with PLOS formatting guidelines and data availability requirements.

## Additional Comments

This manuscript represents the theoretical foundation for signal hierarchical Petri nets, with one detailed illustrative application (*B. subtilis* sporulation). We acknowledge this limited scope in a comprehensive Limitations section, noting that broader validation across diverse biological systems remains future work. This honest framing reflects our commitment to scientific integrity and realistic assessment of current contributions.

The formalism has generated interest within the Petri net and systems biology communities, and we believe PLOS Computational Biology's broad readership will appreciate both its theoretical rigor and practical applicability.

Thank you for considering our manuscript. I look forward to your response and am happy to provide any additional information required.

---

**Sincerely,**

**Eugênio Simão, Ph.D.**  
Assistant Professor  
Department of Computer Science  
Universidade Federal de Santa Catarina (UFSC)  
Araranguá, Santa Catarina, 88906-072, Brazil  
Email: eugenio.simao@ufsc.br  
ORCID: [to be provided]

---

**Manuscript Details:**
- **Title:** Signal Hierarchy Theory for Biological Petri Nets: Formal Semantics of Hierarchical Regulatory Control
- **Type:** Research Article
- **Word Count:** ~7,500 (main text)
- **Figures:** 2
- **Tables:** 2
- **References:** 24
- **Suggested Section:** Theory and Methods (or Computational Theory)
