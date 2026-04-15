# Manuscript Critique — CBD-AD Neuroprotection Draft

**Date:** 2026-04-15  
**Manuscript:** `workspace/projects/canabidiol/manuscript/main.tex`  
**Assessment scope:** Relevancy, originality, innovation, journal fit  

---

## RELEVANCY — Strong

### What works
- AD + multi-target pharmacology is a high-interest topic across neuroscience, pharmacology, and systems biology journals. The failure of single-target approaches (amyloid antibodies) is front-page science right now.
- CBD is timely: regulatory approvals (Epidiolex), massive public interest, and a growing preclinical evidence base create audience pull.
- The age-dependent efficacy angle directly addresses a clinical pain point (geriatric dosing, translational gap from young-animal models to elderly patients).

### Weaknesses to address
- The manuscript is purely computational with **zero experimental validation**. This limits relevance to wet-lab journals. The "hypothesis generator" framing is honest but reviewers will push back on claims without at least one confirmatory experiment.
- The 6-hour simulation window is a serious translational gap. AD operates on a timescale of years. Reviewers in pharmacology/neurology will question whether acute-phase dynamics say anything meaningful about chronic disease modification.

---

## ORIGINALITY — Moderate-to-Good (with caveats)

### Genuinely original elements
1. **Integration scope** — The claim that no published model connects all 6 CBD targets with 4 AD cascades is likely true and verifiable. This is the paper's strongest originality claim.
2. **Emergent bistability discovery** — The NFkB/PPARγ phase transition is a novel prediction. If validated experimentally, this alone would be a significant contribution.
3. **Dissociated therapeutic windows** — The concept that neuroprotection ≠ anti-inflammation at different dose ranges is clinically useful and non-obvious.

### Originality concerns
- **Rate constants are not from data.** The rate constants (0.1, 0.2, 0.3, 0.15, etc.) appear to be round-number estimates, not derived from measured kinetic parameters (Km, Vmax, kon/koff). A reviewer will immediately ask: "Where do these numbers come from?" The paper currently states parameters are from literature but the actual rate functions use suspiciously round coefficients. This undermines the claim of "first-principles prediction" — the model is better described as a **structurally informed qualitative model with assumed kinetics**.
- **The bistability may be an artifact of parameter choice.** Without a formal bifurcation analysis (nullcline computation, eigenvalue analysis near the transition point), the "emergent phase transition" claim rests entirely on simulation at discrete dose points. A reviewer could argue you simply have a steep Hill-like response that *looks* switch-like at your sampling resolution. Adding a bifurcation diagram or at minimum a finer dose sweep (e.g., 1 µM increments between 40–70 µM) would strengthen this claim substantially.
- **The age model is simplistic.** A single linear coefficient (±2%/year) on 7 transitions is a reasonable starting assumption, but it is not calibrated to any age-stratified biological data. Reviewers will note this is a modeling assumption, not a validated parameterization.

---

## INNOVATION — Moderate

### Innovative aspects
- Using stochastic Petri nets (rather than ODEs) for multi-target pharmacology modeling is relatively uncommon and offers genuine advantages (formal structure, conservation laws, stochastic nucleation).
- The compartment place concept for parametric environmental variables (Age, pH, Temperature) is elegant and enables clean factorial designs.
- The factorial CBD×Age sweep design producing a structured analysis is methodologically sound.

### Innovation gaps
- **No sensitivity/robustness analysis.** The paper reports results at fixed parameter values but does not explore how findings change under parameter uncertainty. A global sensitivity analysis (Sobol indices, Morris screening) is standard practice in systems pharmacology papers. Without it, reviewers cannot assess whether the phase transition, dissociated windows, and age effects are robust or parameter-dependent.
- **No comparison with ODE dynamics.** The paper claims stochastic simulation captures phenomena deterministic models miss, but never demonstrates this by running the same model deterministically and comparing. The CV% values (<0.1% for most endpoints) actually suggest the model is **in the deterministic regime** — stochastic fluctuations are negligible. This undermines the stochastic formalism as a contribution.
- **No figures.** This is a major gap. Journals in biology, pharmacy, and drug discovery are highly visual. The manuscript needs at minimum: (a) a model topology diagram (Petri net graph), (b) dose-response curves showing the phase transition, (c) a heatmap of the CBD×Age factorial, (d) time-course trajectories showing pathway dynamics. Tables alone will not pass editorial screening at most target journals.

---

## JOURNAL FIT ASSESSMENT

| Journal Category | Fit | Reasoning |
|---|---|---|
| **PLOS Computational Biology** | Good | Computational methods audience appreciates formalism + biological application. But needs figures and sensitivity analysis. |
| **CPT: Pharmacometrics & Systems Pharmacology** | Good | Systems pharmacology focus matches well. Would require PBPK calibration discussion and parameter justification. |
| **Frontiers in Pharmacology** | Good | CBD + AD topicality. Accepts computational-only papers. Lower bar for parameter rigor. |
| **Journal of Pharmacology and Experimental Therapeutics** | Poor | Requires experimental data. Purely computational work is rarely accepted. |
| **Alzheimer's & Dementia** | Poor | Clinical audience expects patient data or at minimum animal model validation. |
| **Drug Discovery Today** | Moderate | Accepts perspective/computational pieces, but would need to frame as methodology showcase rather than drug-specific claims. |
| **Bioinformatics** | Moderate | Would focus on SHYpn framework methodology rather than biological claims. |
| **Briefings in Bioinformatics** | Good | Review-like scope, accepts computational frameworks with biological case studies. |

---

## TOP PRIORITY REVISIONS FOR JOURNAL SUBMISSION

1. **Add figures** (non-negotiable for any biology/pharmacy journal):
   - Petri net topology diagram
   - Dose-response curves with the phase transition visually apparent
   - CBD×Age heatmap
   - Time-course trajectories for at least 2-3 conditions

2. **Parameter justification table** — A supplementary table mapping every rate constant to its literature source, measured value, and any scaling applied. Currently the methods describe mechanisms but do not justify the specific numerical coefficients.

3. **Sensitivity analysis** — At minimum a local sensitivity analysis (±20% perturbation on each rate constant, effect on key endpoints). Ideally a global sensitivity analysis.

4. **Bifurcation analysis** — Fine-resolution dose sweep (1 µM increments around the transition zone) and/or nullcline computation to formally characterize the bistability rather than claiming it from 7 data points.

5. **Deterministic vs. stochastic comparison** — Run the ODE version, show whether the phase transition persists, and justify why stochastic simulation adds value given the low CV%.

6. **Soften claims** — Replace "first integrated model" with "to our knowledge, the first." Replace "reveals" with "predicts." Avoid "emergent" without formal mathematical characterization of emergence.

---

## VERDICT

The manuscript has a **publishable core** — the integration scope is genuinely novel, the findings are interesting, and the topic is timely. However, in its current form it reads as a **strong technical report** rather than a polished journal submission. The missing elements (figures, parameter justification, sensitivity analysis, bifurcation characterization) are all addressable without new experiments. After these revisions, the strongest targets would be **PLOS Computational Biology**, **CPT: Pharmacometrics & Systems Pharmacology**, or **Frontiers in Pharmacology**. Pure biology or drug discovery journals would require at least preliminary experimental validation of one key prediction (e.g., the NFkB/PPARγ switch in BV-2 cells).
