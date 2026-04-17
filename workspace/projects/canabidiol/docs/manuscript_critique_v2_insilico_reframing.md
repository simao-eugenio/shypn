# Manuscript Critique v2 — In Silico Lab Reframing

**Date:** 2026-04-15  
**Manuscript:** `workspace/projects/canabidiol/manuscript/main.tex`  
**Framing:** SHYpn as in silico laboratory for rationalizing wet-lab experiments  

---

## RELEVANCY — Very Strong

### Strengths under in silico lab framing
- Integration of 6 CBD targets × 4 AD cascades in a single executable model directly answers: "Which experiments should we prioritize?" A wet lab testing 7 CBD doses × 5 ages × multiple biomarkers faces combinatorial explosion. The model's 300-simulation factorial design maps this landscape computationally in hours, identifying the 3–4 conditions worth testing experimentally.
- Dissociated therapeutic windows prediction (neuroprotection at 25 µM vs. inflammation resolution at 65 µM) prevents wasted experiments. Without this, a lab might test CBD at a single dose and measure a composite endpoint, getting ambiguous results. Model says: "Test low and high doses separately, measure neuroprotection and inflammation independently."
- Age-dependent efficacy shift directly informs experimental design: don't extrapolate from young-animal models to elderly patients without adjusting dose expectations. Saves entire animal study cohorts from underdosing.
- 6-hour simulation window is appropriate for guiding acute pharmacodynamic experiments (cell culture, brain slice, acute dosing in animals). Model doesn't claim chronic disease modification — it guides the first round of experiments.

### Previous concern recontextualized
- "No experimental validation" is not a weakness — an in silico lab precedes experiments by definition. Requiring validation before publication would be circular. Manuscript must make this philosophy explicit.

---

## ORIGINALITY — Good

### Strengthened claims
1. **Integration scope** — No published in silico model provides pre-experimental landscape of CBD multi-target interactions with AD cascades. Genuinely novel as experimental planning tool.
2. **Phase transition prediction** — Specific, testable directive: "Titrate CBD between 40–70 µM in BV-2 cells, measure NFkB-p65 — expect a switch, not a gradient." Saves labs from unnecessary dose-response curves outside the transition zone.
3. **Dissociated windows prediction** — Translates to: "Design assay panel measuring neuronal viability AND inflammatory markers independently. Single composite endpoint will mask the dissociation."

### Concerns that persist (less severe)
- **Round-number rate constants** — For qualitative predictions (phase transition exists, windows dissociated, age shifts threshold), exact kinetics matter less than topology and feedback structure. Sensitivity analysis should confirm robustness to parameter uncertainty.
- **Bistability characterization** — Finer dose sweep (1 µM increments) still recommended to give experimentalists a precise concentration range.
- **Age model simplicity** — Linear ±2%/year is reasonable first-pass for guiding young vs. old comparison experiments.

---

## INNOVATION — Good-to-Strong

### Reframed as experimental design rationalization
- Factorial design is innovative as in silico experimental planning — 20 conditions × 15 replicates computationally identifies the most informative experimental conditions.
- Compartment places enable rapid "what-if" screening (older patient? lower pH?) that would take months in wet lab.
- Three testable predictions should be promoted to structured experimental guidance section.

### Innovation gaps reframed
- **Sensitivity analysis** — Question becomes "do experimental recommendations change if parameters are ±20–30% off?" Tells experimentalist how much to trust computational guidance.
- **ODE vs. stochastic comparison** — "Does formalism choice change experimental recommendations?" Worth showing but less critical.
- **Figures** — Non-negotiable for communicating experimental guidance visually.

---

## JOURNAL FIT — Reassessed

| Journal | Fit | Reasoning |
|---|---|---|
| **PLOS Computational Biology** | Very Good | Computational methods for biological insight. In silico lab framing native. |
| **CPT: Pharmacometrics & Systems Pharmacology** | Very Good | Core audience uses models to guide drug development. |
| **Frontiers in Pharmacology** | Very Good | Computational pharmacology section. CBD + AD topicality. |
| **J. Chemical Information and Modeling** | Good | Computational models guiding drug discovery. |
| **Briefings in Bioinformatics** | Good | Systems-level modeling case studies. |
| **Comput. Struct. Biotechnology Journal** | Good | Open access, translational computational biology. |
| **Drug Discovery Today** | Good | Perspective format for in silico rationalization. |
| **Frontiers in Aging Neuroscience** | Moderate-Good | Age-dependent efficacy angle. |

---

## TOP PRIORITY REVISIONS

1. **Reframe Introduction/Discussion as in silico laboratory work** — State philosophy: computational modeling precedes and rationalizes wet-lab experiments, reducing combinatorial search space.
2. **Add Experimental Guidance section** — Map predictions to specific protocols, expected outcomes, refutation criteria, effort saved.
3. **Add figures** (deferred but non-negotiable for submission).
4. **Sensitivity analysis as "robustness of experimental guidance"** — Do recommendations change if parameters are ±20–30% off?
5. **Soften absolute claims, strengthen guidance claims** — "predicts" not "reveals"; "to our knowledge" qualifiers; "pre-experimental landscape mapping."
6. **Parameter justification** — Reframed as order-of-magnitude estimates sufficient for topology-driven qualitative predictions.

---

## VERDICT

Under in silico laboratory framing, publishability threshold is lower than initially assessed. Paper is not claiming biological truths but mapping a landscape telling experimentalists where to look first. After revisions (reframing, experimental guidance section, figures, sensitivity analysis), strong candidate for PLOS Computational Biology, CPT: Pharmacometrics & Systems Pharmacology, or Frontiers in Pharmacology.
