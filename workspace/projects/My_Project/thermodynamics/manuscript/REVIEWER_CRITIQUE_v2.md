# Second Reviewer Critique - Final Manuscript
**Document:** thermodynamic_hierarchy_petri_nets_review.tex  
**Date:** Continuation from first review cycle  
**Status:** Final polish before submission

---

## MAJOR ISSUES

### 1. **Abstract Claims vs. Results Disconnect** (Lines 1-30)
**Issue:** Abstract states "16× better ATP economy" but this language implies thermodynamic efficiency improvement, when Results/Discussion clarify this is actually **reduced ATP consumption** (skipping regulatory overhead), not improved energy coupling.

**Recommendation:** Revise abstract to say "16-fold reduction in ATP consumption" or "16× ATP economy" (defined explicitly as cost reduction, not efficiency improvement). Add one sentence clarifying this reflects bypassing regulatory layers.

**Specific text (line ~15):** "achieving 16-fold better ATP economy (0.73 vs 11.6 mM ATP/spore)"
→ Change to: "achieving 16-fold reduction in ATP consumption (0.73 vs 11.6 mM ATP/spore) by bypassing regulatory overhead"

---

### 2. **Incomplete Reversibility Discussion** (Lines 520-535)
**Issue:** Section 3.5 claims "thermodynamic irreversibility" prevents reversal post-commitment, citing entropy production and barrier asymmetry. However:
- No quantitative calculation of reverse barrier height $\Delta G^\ddagger_{\text{rev}}$
- No explanation of WHY reverse barrier is higher (mechanistically)
- Missing: Are autocatalytic loops (SigmaE) sufficient, or is protein degradation required?

**Recommendation:** Either provide quantitative reverse barrier analysis or soften claims to "kinetic irreversibility on experimental timescale (60 s)" rather than absolute thermodynamic irreversibility.

**Critical gap:** If ATP regenerates to 893 mM (line 523), why doesn't this reverse SigmaF? Is it because SigmaF protein is stable (no degradation), making reversal kinetically slow rather than thermodynamically forbidden?

---

### 3. **Free Energy Landscape Methodology Concerns** (Lines 255-270)
**Issue:** Equation 8 reconstructs $G(\text{ATP}, \xi) = -k_B T \ln P(\text{ATP}, \xi)$ from trajectory sampling. Several problems:

**Problem A:** How many trajectories sampled? n=10 replicates insufficient for rare regions of phase space.

**Problem B:** Ergodicity assumption explicitly stated (line 745) but not validated. What's the correlation time? Trajectory length vs. decorrelation?

**Problem C:** Text says "not an equilibrium thermodynamic potential" (line 266)—this is correct, but then calling it "free energy" is misleading. It's a **potential of mean force (PMF)**, not a true Gibbs free energy.

**Recommendation:** 
1. Rename to "effective energy landscape" or "potential of mean force"
2. Add Methods subsection on sampling statistics (trajectory count, convergence checks)
3. Show landscape is converged (e.g., compare n=5 vs n=10 replicates)

---

### 4. **Statistical Validation Incomplete** (Table 1, Lines 440-470)
**Issue:** Table 1 reports n=10 replicates with mean±SD, but:

**Missing:** 
- No test for normality (Shapiro-Wilk) before using t-test
- CV=150% for ATP (line 470) suggests non-normal distribution → should use non-parametric test (Mann-Whitney U)
- p-values reported as "p<0.05" or "ns" → provide exact values
- Effect sizes not reported (Cohen's d, confidence intervals)

**Recommendation:** 
1. Add normality test results to Table 1 caption
2. Report exact p-values (e.g., p=0.042, not p<0.05)
3. Add effect sizes for significant differences
4. If distributions non-normal, use Mann-Whitney U test instead of t-test

---

### 5. **ATP as "Signal" vs. "Substrate" Conflation** (Lines 575-610, Discussion)
**Issue:** Discussion (Section 4.3) claims "ATP functions as a hierarchical signal" but never clearly distinguishes:
- ATP as information carrier (signal hierarchy theory)
- ATP as thermodynamic resource (mass-action kinetics)

**Critical ambiguity:** Is ATP concentration the **signal** (like cAMP in eukaryotes), or does ATP merely modulate reaction rates through mass-action $r \propto [\text{ATP}]$? These are mechanistically different.

**Lines 585-595:** "ATP operates simultaneously as (1) thermodynamic resource and (2) hierarchical signal" → This is the core claim but needs mechanistic clarity:
- Does the cell *sense* ATP concentration via dedicated sensors (like AMPK)?
- Or is "signal" just a metaphor for mass-action kinetic effects?

**Recommendation:** Add 1-2 sentences distinguishing:
1. **Mechanistic signal:** Requires dedicated ATP sensors (e.g., AMPK-like kinases)
2. **Thermodynamic constraint:** ATP modulates rates via $r_t \propto [\text{ATP}]^n$ in rate law (Eq. 2)

Clarify which mechanism operates in *B. subtilis* sporulation (likely the latter).

---

### 6. **Entropy Production Calculation Oversimplified** (Lines 330-380)
**Issue:** Equation 11 calculates environmental entropy from ATP hydrolysis heat:
$$\Delta S_{\text{env}} = \sum \frac{\Delta H_{\text{rxn}}}{T}$$

**Problems:**
- Assumes all ATP hydrolysis goes to heat (100% dissipation) → ignores work done (conformational changes, phosphorylation)
- Uses standard enthalpy $\Delta H^\circ = -30.5$ kJ/mol → should use condition-dependent $\Delta H$ (depends on pH, Mg²⁺, ionic strength)
- Ignores entropy production from GTP hydrolysis, protein synthesis, other reactions

**Specific concern (line 355):** "873 mM ATP consumed" → Is this total cellular ATP, or only sporulation-specific ATP? If total, then includes basal metabolism (growth, maintenance), inflating entropy calculation.

**Recommendation:**
1. Clarify ATP consumption is **sporulation-specific** (subtract basal metabolism control)
2. Add caveat: "Entropy calculation assumes complete dissipation; actual work coupling may reduce values by 30-50%"
3. Consider including GTP contribution (Table 1 shows GTP dynamics)

---

## MODERATE ISSUES

### 7. **Commitment Coordinate Definition Poorly Justified** (Lines 255-262)
**Issue:** Choice of $\xi = [\text{SigmaF}] + [\text{Forespore}]$ as commitment coordinate justified by three reasons (lines 257-260), but:
- SigmaF is Layer 3, Forespore is product → These are at different hierarchy levels, why sum them?
- Why not include SigmaE (Layer 4) which is the actual commitment step?
- "Robustness analysis (not shown)" → This is critical, should be shown in Supplementary Material

**Recommendation:** Either:
1. Show robustness analysis as supplementary figure
2. Use simpler coordinate: $\xi = [\text{SigmaE}]$ (the actual commitment marker)
3. Provide equation for alternative weighting and show landscape is invariant

---

### 8. **"Hierarchical Preemption" Term Never Defined** (Throughout)
**Issue:** Paper uses "hierarchical preemption" ~20 times but never explicitly defines it. From context it means "lower layers activating before higher layers" but this inverts standard hierarchy terminology where Layer 0 is "top" (master regulator).

**Recommendation:** Add definition in Introduction (after line 90):
> "We define **hierarchical preemption** as the phenomenon where lower signaling layers (distal to master regulator) activate before higher layers when thermodynamic constraints block the canonical top-down cascade."

---

### 9. **Figure Quality and Captions** (Figures 1-3)
**Issue:** Figure captions inadequate:

**Figure 1 (line 205):** "Hybrid Petri net model...stress conditions" → Should specify what visual elements mean (circles=places, bars=transitions, arrows=arcs). Readers unfamiliar with Petri nets will be lost.

**Figure 2 (line 415):** "Representative trajectory from n=10 replicates" → Which replicate? Mean trajectory? Why not show all 10 with confidence intervals?

**Figure 3 (line 445):** Same issue—show all replicates, not just one.

**Recommendation:** 
1. Add Petri net notation primer to Figure 1 caption
2. Show mean±SD trajectories in Figures 2-3 (all 10 replicates as thin lines, mean as bold)
3. Add panel labels (A, B, C) if figures have multiple parts

---

### 10. **Missing Sensitivity Analysis** (Methods, Lines 100-350)
**Issue:** Model has many parameters:
- Rate constants $k_t$ (line 145)
- Hill coefficients $n=1$ or $n=2$ (line 150)
- ATP homeostasis threshold 4800 mM (line 175)
- Michaelis constants $K_M$ (unstated)

**No sensitivity analysis provided.** How robust are results to parameter uncertainty?

**Critical parameters:** 
- What if $n=1.5$ instead of $n=2$? Still get 99.6% suppression?
- What if ATP threshold is 4000 or 6000 mM?

**Recommendation:** Add Supplementary Table showing:
1. Parameter ranges tested
2. Effect on key outputs (spore yield, ATP economy, layer sequence)
3. Identify most sensitive parameters

---

### 11. **ATP Regeneration Mechanism Underspecified** (Lines 170-195)
**Issue:** Equation 5 models ATP regeneration with rate:
$$r_{\text{ATP-regen}} = k_{\text{regen}} \cdot [\text{Nutrients}] \cdot \frac{[\text{ADP}]}{K_M + [\text{ADP}]}$$

**Problems:**
- What is $k_{\text{regen}}$ value? Not stated.
- How is "Nutrients" defined? Glucose? Mixed carbon sources?
- Line 180: "GTP regeneration follows analogous kinetics" → No equation provided for GTP.
- Nutrients deplete (line 215: "nutrient-depletion" transition) but no rate constant given.

**Recommendation:** Add table of all kinetic parameters with values and literature sources.

---

### 12. **"Stress Pathway" Misnomer** (Throughout)
**Issue:** Paper calls low-ATP condition "stress pathway" but:
- This implies a dedicated alternative pathway (like bacterial stringent response)
- Actually it's just **constraint-based filtering** of the same network
- No dedicated stress genes, sensors, or regulatory rewiring

**This is a terminological issue that may confuse readers** expecting a programmed stress response (like SOS, heat shock).

**Recommendation:** Consider alternative terms:
- "Low-ATP trajectory" (neutral, descriptive)
- "Constraint-driven pathway" (emphasizes mechanism)
- "Thermodynamically filtered pathway"

Or keep "stress pathway" but add clarifying sentence (line 95): "We use 'stress pathway' to denote the thermodynamically accessible trajectory under energy depletion, not a dedicated regulatory program."

---

## MINOR ISSUES

### 13. **Notation Inconsistencies**
- Line 130: $\bullet t$ (input places) vs. line 145: $\bullet p$ (output transitions) → Define notation clearly in one place
- Line 270: $\xi^*$ defined but never used
- Line 280: $\xi_{\text{committed}}$ used but never defined (what threshold?)

### 14. **Citation Formatting**
- Line 750: "López et al. (2009)" but bibliography shows López (2009)—check all multi-author citations
- Line 765: "Berg et al. (2009)" same issue
- Use consistent citation style (natbib package OK, but check author counts)

### 15. **Typos and Grammar**
- Line 200: "Forespore, Mother\_cell" → Remove underscore in main text (keep in code)
- Line 275: "trajectory sampling" → Should be "ensemble sampling" (more accurate)
- Line 520: "766 transition firings" → Capitalize "Transition" if referring to Petri net elements

### 16. **Acronyms**
- Line 720: "FBA" introduced without definition → Add "(flux balance analysis)" on first use
- Line 725: "RK4" → Define as "4th-order Runge-Kutta" on first use (line 195 OK)

---

## PRESENTATION ISSUES

### 17. **Results Section Organization** (Lines 385-525)
**Issue:** Results jump between topics without clear transitions:
- Section 3.1: Layer activation sequence
- Section 3.2: Free energy landscape
- Section 3.3: Basin of attraction
- Section 3.4: Quantitative metrics
- Section 3.5: Mechanism

**Recommendation:** Reorganize for logical flow:
1. Quantitative metrics (Table 1) **first** → Establishes what happened
2. Layer sequence → Shows mechanism
3. Thermodynamic analysis (landscape, basins) → Explains why
4. Constraint-based selection → Unifying principle

### 18. **Discussion Too Speculative** (Lines 625-675)
**Issue:** Section 4.5 "Predictive Framework" makes four predictions but:
- Prediction 1 (1 mM ATP critical) is post-hoc (observed in results, not predicted)
- Prediction 2 (knockout phenotypes) reasonable but vague ("will not prevent" → quantify expected spore yield)
- Prediction 3 (temperature dependence) good, testable
- Prediction 4 (intermediate ATP) most interesting but underdeveloped → Why bistability? Show phase diagram.

**Recommendation:** 
- Move Prediction 1 to Results (it's an observation)
- Expand Prediction 4 with phase diagram (ATP vs. pathway probability)
- Add Prediction 5: Time-resolved single-cell ATP imaging should show bimodal distribution at intermediate ATP

---

## CRITICAL EXPERIMENTS NEEDED

### 19. **Experimental Validation Section is Weak** (Lines 685-735)
**Issue:** Section 4.6 lists experiments needed but doesn't prioritize or explain feasibility:

**Which is most critical?** All five experiments would take 2-3 years. Prioritize:
1. **ATP dynamics** (single-cell imaging) → Direct test of central claim
2. **Hierarchical preemption** (sigma factor reporters) → Validates sequence inversion
3. ATP economy, knockout phenotypes, temperature → Supporting evidence

**Feasibility:** Single-cell ATP imaging exists (Berg et al., 2009 cited) → Why not collaborate to do this **now**?

**Recommendation:** Reframe Section 4.6:
- State this is computational work requiring validation
- Prioritize experiments by testability (1-2 years) vs. long-term (5+ years)
- Suggest specific collaborators or methods

---

## STRENGTHS TO PRESERVE

1. **Statistical validation with n=10 replicates** (Table 1) is rigorous—keep this.
2. **Thermodynamic framework integration** (ΔG-ATP, entropy) is novel and well-executed.
3. **Hybrid Petri net formalism** clearly presented with equations (Section 2.1).
4. **Quantitative predictions** (Section 4.5) are testable.
5. **Honest limitations** (Section 4.6) acknowledges computational nature.

---

## RECOMMENDED REVISIONS PRIORITY

### **MUST FIX (before acceptance):**
1. Issue #1: Abstract claims (economy vs. efficiency)
2. Issue #3: Free energy landscape terminology (PMF vs. free energy)
3. Issue #5: ATP signal vs. substrate clarification
4. Issue #11: Parameter table with all rate constants

### **SHOULD FIX (strengthen paper):**
5. Issue #2: Reversibility discussion (soften claims or quantify)
6. Issue #4: Statistical tests (normality, exact p-values)
7. Issue #7: Commitment coordinate justification (show robustness)
8. Issue #10: Sensitivity analysis (supplementary)

### **NICE TO HAVE (improve clarity):**
9. Issue #8: Define "hierarchical preemption" explicitly
10. Issue #9: Improve figure captions (mean±SD trajectories)
11. Issue #17: Reorganize Results section
12. Issue #19: Prioritize experiments in validation section

---

## OVERALL ASSESSMENT

**Strengths:** Rigorous computational study with novel thermodynamic framework, statistical validation, and clear testable predictions. Hybrid Petri net formalism is appropriate and well-executed.

**Weaknesses:** Some overclaims (thermodynamic irreversibility), missing methods details (parameters, sensitivity), and terminology issues (economy vs. efficiency, signal vs. substrate, "stress pathway").

**Recommendation:** **MAJOR REVISION** → Address 4 "MUST FIX" issues, then **ACCEPT**.

**Estimated revision time:** 1-2 weeks (mostly clarifications, no new simulations needed).

---

## SPECIFIC LINE-BY-LINE EDITS

### Abstract (Lines 1-30)
**Line 15:** "16-fold better ATP economy"  
→ **Change to:** "16-fold reduction in ATP consumption"

**Line 18:** Add after "0.73 vs 11.6 mM ATP/spore"  
→ **Insert:** "reflecting bypass of regulatory overhead rather than improved energy coupling"

### Methods (Lines 100-350)
**After line 195:** Add new subsection:
```
\subsubsection{Model Parameters}
[Insert table with all k_t, K_M, n values and literature sources]
```

**Line 260:** "Robustness analysis (not shown)"  
→ **Change to:** "Robustness analysis (Supplementary Figure S1)" [Create supplementary]

**Line 266:** "not an equilibrium thermodynamic potential"  
→ **Change to:** "represents a potential of mean force (PMF), not a true Gibbs free energy"

### Results (Lines 385-525)
**Line 415:** "Representative trajectory from n=10 replicates"  
→ **Change to:** "Mean trajectory ± SD from n=10 replicates (individual replicates shown as thin lines)"

**Line 470:** "p<0.05" and "ns"  
→ **Change to:** exact p-values "p=0.042" and "p=0.18"

**Line 525:** "thermodynamic irreversibility"  
→ **Soften to:** "kinetic irreversibility on the 60 s experimental timescale"

### Discussion (Lines 530-680)
**After line 575:** Add clarification:
> "ATP concentration modulates reaction rates through mass-action kinetics ($r \propto [\text{ATP}]^n$) rather than through dedicated ATP sensors (like AMPK in eukaryotes). We use 'signal' to denote ATP's role as an information carrier in this thermodynamic sense."

**Line 625:** Move "1 mM ATP critical minimum" from Prediction 1 to Results (it's observed, not predicted)

### Conclusions (Lines 740-780)
**Line 755:** "16-fold better ATP economy"  
→ **Change to:** "16-fold reduction in ATP consumption"

---

**END OF CRITIQUE**

**Total issues identified:** 19 (6 major, 6 moderate, 7 minor)  
**Estimated revision effort:** Moderate (1-2 weeks)  
**Recommendation:** Address major issues, then paper is acceptable for publication.
