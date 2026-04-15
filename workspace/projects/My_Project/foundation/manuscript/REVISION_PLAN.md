# MANUSCRIPT REVISION PLAN
## Reframing from Performance to Biological Insight

**Date:** January 17, 2026  
**Critical Issue:** Manuscript currently emphasizes computational performance (parallelization, speedup) when the primary contribution is **Signal Hierarchy Theory** enabling unified metabolic+regulatory modeling with quantitative biological insights.

---

## CURRENT PROBLEMS

### 1. Title Misemphasis
**Current:** "Signal Hierarchical Petri Nets: A Theory of Weak Independence and Hierarchical Control..."
- Puts weak independence (performance) equal to hierarchical control
- Doesn't highlight the biological unification contribution

**Problem:** Readers expect a computational methods paper, not a biological modeling breakthrough

### 2. Abstract Framing
**Current opening:** "We extend classical Biological Petri Net formalism with two complementary theories: weak independence for concurrent substrate dynamics and signal hierarchy..."

**Problems:**
- Leads with "two complementary theories" (equal weight)
- Emphasizes "2-4× simulation speedup" prominently
- Buries biological insight: "models that bridge molecular mechanisms with cellular decision-making" at the very end

**What's missing:** 
- The revolutionary insight that signal hierarchy **unifies** metabolic and regulatory networks
- Quantitative biological insights: ATP-gated decisions, commitment mechanisms, basin of attraction analysis
- Why this matters for biology, not just computation

### 3. Introduction Structure
**Current order:**
1. Motivation: Starts with "massive substrate-level parallelism" (performance focus)
2. Biological Motivation for Weak Independence (11 lines)
3. Biological Motivation for Signal Hierarchy (9 lines)

**Problem:** Performance is foregrounded, biological unification is secondary

**Current Contributions order:**
1. Weak Independence Theory
2. Signal Hierarchy Theory
3. Unified 13-Tuple Formalism
4. Comprehensive Validation (emphasizes speedup)
5. Open Implementation

**Problem:** Signal hierarchy should be #1 contribution

### 4. Validation Section Emphasis
**Current metrics prominence:**
- "2-4× speedup" mentioned 8 times
- "193× total speedup" highlighted for lambda phage
- Performance results given more space than biological insights

**Biological insights buried:**
- Basin of attraction analysis (Figure 1) - profound cell fate insight
- 16× ATP reduction causing pathway switch - quantitative energy threshold
- >95% decision accuracy vs 50% flat model - hierarchical control necessity
- Commitment finality through signal depletion - irreversible decisions

**Problem:** Reads like a performance paper with biology examples, not a biology paper with performance benefits

### 5. Discussion Framing
**Current Section 7.2 "Practical Impact":**
- Starts with "Simulation performance: 2-4× speedup..."
- Model construction and Applications are secondary

**Problem:** Performance dominates over biological understanding

---

## REQUIRED CHANGES

### PHASE 1: Core Narrative Reframing

#### 1.1 Abstract Rewrite
**NEW STRUCTURE:**
```
[LEAD] Cellular systems require unified models integrating metabolic networks with 
regulatory control to capture quantitative decision-making.

[PROBLEM] Existing Bio-PNs separate metabolism (mass transfer) from regulation 
(test arcs), lacking formal hierarchical information channels.

[SOLUTION] We introduce Signal Hierarchy Theory with formal signal places (Ψ) 
representing information channels distinct from mass transfer. Signal flow arcs 
consume tokens, enabling hierarchical preemption where regulatory layers control 
metabolic pathway commitment.

[INSIGHTS] Case studies reveal: (1) ATP concentration hierarchically gates 
B. subtilis sporulation (16× reduction triggers pathway switch), (2) Basin of 
attraction analysis quantifies cell fate commitment (>95% reliability), 
(3) Lambda phage decision circuits achieve irreversible commitment through 
signal depletion (50% → 95% accuracy improvement).

[FORMALISM] Signal hierarchy integrates with weak independence (distinguishing 
competitive vs. convergent coupling) into unified 13-tuple formalism enabling 
2D computational architecture.

[VALIDATION] Analysis of 100 BioModels demonstrates signal hierarchy prevalence 
(375 signal places across models) and quantitative regulatory insights previously 
inaccessible in Bio-PN formalism.

[IMPACT] This framework enables translational systems biology models bridging 
molecular mechanisms with cellular decision-making, with applications in synthetic 
biology circuit design and therapeutic intervention prediction.
```

**KEY CHANGES:**
- Lead with biological unification problem
- Emphasize quantitative insights (16× ATP, >95% reliability, 50%→95% accuracy)
- Performance (2-4× speedup) becomes a side benefit, not headline
- Signal hierarchy is the hero, weak independence is supporting technology

#### 1.2 Title Revision Options
**OPTION A (Conservative):**
"Signal Hierarchical Petri Nets: A Formal Theory for Unified Metabolic-Regulatory Modeling and Quantitative Cell Fate Analysis"

**OPTION B (Bold):**
"Unified Modeling of Metabolic and Regulatory Networks via Signal Hierarchical Petri Nets: Quantitative Insights into ATP-Gated Cell Fate Decisions"

**OPTION C (Balanced - RECOMMENDED):**
"Signal Hierarchical Petri Nets: Formal Theory Unifying Metabolic and Regulatory Networks for Quantitative Biological Insight"

**Rationale:** Emphasizes:
1. Signal hierarchy (not weak independence)
2. Unification contribution
3. Quantitative biological insight (not performance)

#### 1.3 Introduction Reordering
**NEW STRUCTURE:**

**1.1 Motivation**
Rewrite to lead with **biological challenge:**
- Cellular decisions (sporulation, lysis/lysogeny) require integrated metabolic + regulatory models
- ATP levels control pathway commitment (quantitative threshold)
- Current Bio-PNs separate these: metabolism via mass transfer, regulation via test arcs
- **Gap:** No formal hierarchical information flow with consumption semantics

**1.2 Biological Motivation for Signal Hierarchy** (MOVE UP)
- Stress response, energy status, quorum sensing examples
- Signal depletion during decision-making (CI repressor, growth factors)
- Hierarchical preemption mechanisms
- **This is the main contribution**

**1.3 Biological Motivation for Weak Independence** (MOVE DOWN)
- Enabling technology for signal hierarchy
- Convergent vs. competitive coupling
- Allows metabolic and regulatory pathways to coexist in unified model
- **Reframe:** "To enable signal hierarchy in large-scale models, we address computational correctness..."

**1.4 Contributions** (REORDER)
1. **Signal Hierarchy Theory** - formal information channels, consumption semantics, preemption
2. **Unified 13-Tuple Formalism** - integrates metabolic + regulatory networks
3. **Quantitative Biological Insights** - ATP thresholds, basin of attraction, commitment mechanisms
4. **Weak Independence Theory** - computational correctness for convergent coupling
5. **Comprehensive Validation** - 100 BioModels, 375 signal places, case studies
6. **Open Implementation** - reproducibility

---

### PHASE 2: Section-by-Section Revisions

#### 2.1 Section 3 vs Section 4 - SWAP ORDER?
**CURRENT:** Section 3 = Weak Independence, Section 4 = Signal Hierarchy

**OPTION A: Keep order, add framing**
Add paragraph to Section 3 introduction:
> "Signal hierarchy theory (Section 4) enables unified metabolic-regulatory models. 
> However, such models contain hundreds of concurrent metabolic reactions with 
> convergent coupling. To ensure computational correctness in these large-scale 
> unified models, we first formalize weak independence theory for parallel execution."

**OPTION B: Swap sections (RADICAL)**
- Section 3 = Signal Hierarchy Theory (main contribution)
- Section 4 = Weak Independence Theory (enabling technology)
- Section 5 = Unified Formalism (brings them together)

**RECOMMENDATION:** Option A (keep order but reframe motivation)

#### 2.2 Validation Section (Section 6) - Restructure

**CURRENT PROBLEMS:**
- Performance metrics dominate (speedup numbers everywhere)
- Biological insights are secondary
- Case studies bury the profound findings

**NEW STRUCTURE:**

**6.1 Methodology** (unchanged)

**6.2 Signal Hierarchy: Biological Insights** (RENAME & EXPAND)
Move this BEFORE weak independence results

**Key Changes:**
- Lead with Figure 1 (basin of attraction) - "Cell fate commitment is quantifiable"
- Emphasize 375 signal places across 100 models (40% energy, 27% regulatory)
- Average 2.3 hierarchical layers shows multi-scale organization is universal
- **Add new subsection:** "Quantitative Regulatory Thresholds"
  - ATP concentration ranges for pathway switching
  - Signal depletion kinetics
  - Commitment time measurements

**6.3 Weak Independence: Computational Correctness** (RENAME)
De-emphasize speedup, emphasize correctness:
- 65% weak independence enables unified models to execute correctly
- Statistical equivalence to exact SSA (correctness, not speed)
- Speedup is a side benefit: "As a consequence of parallel correctness, models execute 2-4× faster"

**6.4 Case Study 1: Glycolysis**
**Reframe:** "Metabolic-only network demonstrates convergent coupling prevalence"
- 60% weak independence allows concurrent pathway execution
- **De-emphasize:** Sequential 125ms vs parallel 48ms (move to end)
- **Emphasize:** Biological insight about ATP production superposition

**6.5 Case Study 2: B. subtilis Sporulation** (EXPAND)
This is the crown jewel - expand substantially:

**Add quantitative analysis:**
- ATP threshold: 5000 mM (normal) vs 300 mM (stress) = 16× reduction
- Commitment time: 0.44s in stress conditions (from Figure 2 data)
- Basin of attraction: >95% reliability within each basin
- Phosphorelay cascade: 4 layers (Layer 3 → Layer 0)
- Signal depletion rate: Spo0A-P consumption kinetics
- **NEW:** Phase space trajectory analysis showing collapse to attractors

**Current text problems:**
- Figure captions describe findings but text doesn't analyze them
- "71% weakly independent, 2.8× speedup" - performance dominates
- Missing quantitative interpretation of hierarchical dynamics

**NEW TEXT STRUCTURE:**
```
6.5.1 Model Description (current text)
6.5.2 ATP-Gated Decision Mechanism
  - Quantitative threshold analysis (16× ATP reduction)
  - Figure 1 interpretation: Basin geometry and accessibility
  - Thermodynamic basis for commitment

6.5.3 Hierarchical Cascade Dynamics
  - Figure 2 interpretation: Layer activation sequence
  - Normal pathway: Gradual Spo0A-P-driven commitment (0.2-0.8s)
  - Stress pathway: Rapid bypass (<0.1s commitment)
  - Layer preemption mechanism quantified

6.5.4 Biological Insights
  - Energy status as master regulator (40% of signal places are energy-related)
  - Irreversible commitment through signal depletion
  - Evolutionary advantage of hierarchical control

6.5.5 Computational Notes
  - 71% weak independence enables unified model execution
  - 2.8× parallel speedup as implementation benefit
```

**6.6 Case Study 3: Lambda Phage Decision** (EXPAND)
**Current problem:** "50% → >95% decision accuracy" is buried in 3 lines

**NEW STRUCTURE:**
```
6.6.1 Decision Circuit Architecture
  - Layer 2 (UV signal) → Layer 1 (CI/Cro) → Layer 0 (gene expression)
  - Signal hierarchy necessity for bistable switch

6.6.2 Flat Model Failure Analysis
  - Why 50% accuracy? Ambiguous intermediate states persist
  - Test arcs cannot provide commitment finality
  - Biological implausibility of reversible lysis/lysogeny

6.6.3 Hierarchical Model Success
  - Signal depletion collapses decision space
  - UV consumption → CI degradation → irreversible lytic commitment
  - >95% accuracy matches experimental observations

6.6.4 Quantitative Comparison
  - [NEW TABLE] Flat vs Hierarchical model comparison:
    - Decision time, accuracy, reversibility, biological plausibility

6.6.5 Implications for Synthetic Biology
  - Engineered circuits require signal hierarchy for reliable switching
  - Design principles: signal depletion ensures commitment
```

#### 2.3 Discussion Section (Section 7) - Major Reframing

**7.1 Theoretical Significance** (REORDER)

**NEW PARAGRAPH ORDER:**
1. **Signal hierarchy** (move to first position)
   - **Expand:** "This is the first Bio-PN formalism enabling unified metabolic-regulatory modeling"
   - **Add:** "Traditional approaches separate metabolism (ODE models) from regulation (Boolean networks)"
   - **Add:** "Signal places with consumption semantics bridge this divide formally"

2. **Unified framework** (move up)
   - **Reframe:** Not about 2D computation, about biological unification
   - "Cells do not separate metabolism from regulation—our formalism reflects this reality"

3. **Weak independence** (move down)
   - **Reframe:** "To enable large-scale unified models, we formalize computational correctness..."
   - De-emphasize as supporting theory

**7.2 Practical Impact** (MAJOR REWRITE)

**Current first topic:** "Simulation performance"
**NEW first topic:** "Quantitative Biological Insight"

**NEW STRUCTURE:**
```
7.2.1 Quantitative Biological Insight (NEW - PRIMARY)
Signal hierarchy enables quantitative analysis of regulatory mechanisms:

- ATP threshold quantification: 16× reduction triggers B. subtilis pathway switch
- Basin of attraction geometry: >95% commitment reliability
- Decision finality metrics: 50% → 95% accuracy improvement with hierarchy
- Temporal dynamics: Layer activation sequences reveal regulatory kinetics
- Phase transitions: Commitment points identifiable in state space

These insights were inaccessible in classical Bio-PN formalism lacking formal 
hierarchical information channels. Signal hierarchy makes regulatory control 
measurable and predictable.

7.2.2 Unified Metabolic-Regulatory Modeling (NEW - SECONDARY)
Single formalism encompasses:
- Metabolic networks (mass transfer via normal arcs)
- Regulatory networks (information transfer via signal flow arcs)
- Energy coupling (ATP as both metabolite and signal)

Enables holistic systems biology impossible with separated model types.

7.2.3 Model Construction and Modularity (current text revised)
- Hierarchical layers enable compositional design
- Signal places explicit (not hidden in rate functions)
- Supports iterative refinement

7.2.4 Applications (EXPAND)
Drug discovery: ATP-dependent transporter hierarchies
Synthetic biology: Reliable decision circuits (>95% accuracy design target)
Systems biology: Multi-scale integration with quantitative prediction

7.2.5 Computational Efficiency (DE-EMPHASIZE, move to end)
As implementation benefit, unified models execute 2-4× faster due to weak 
independence correctness. Performance gains enable genome-scale applications 
but are secondary to biological insight contribution.
```

**7.3 Comparison with Related Work**
**Add column to Table 5:** "Unified Modeling"
- Classical PN: --
- Bio-PN: -- (separate metabolism and regulation)
- Categorical: -- (algebraic, not biological)
- Mana: -- (enzyme depletion, not regulatory hierarchy)
- **SHYPN:** ✓ (metabolism + regulation unified via signal hierarchy)

**7.4 Limitations and Future Work**
**Reorder to emphasize signal hierarchy:**
1. Signal identification (current #1) - keep
2. **NEW:** Quantitative threshold determination from experimental data
3. Acyclic hierarchy (current #2) - keep
4. **NEW:** Spatial signal gradients (diffusion-limited hierarchies)
5. Semantic types (current #3) - keep

Remove: "Future directions: Spatial extension, SBML Level 4" (too vague)

**Add:** "Future directions: 
1. Automated threshold learning from time-series data
2. Stochastic signal hierarchy for rare events
3. Spatial signal gradients (reaction-diffusion coupling)
4. Multi-compartment hierarchies (organelle signaling)"

#### 2.4 Conclusion (Section 8) - Reframe

**CURRENT PROBLEMS:**
- First paragraph: "weak independence and signal hierarchy" (equal weight)
- Second paragraph: Emphasizes "65% weak independence, 2-4× speedup"
- Biological insights buried

**NEW STRUCTURE:**
```
[PARAGRAPH 1 - LEAD WITH BIOLOGY]
Cellular systems integrate metabolic and regulatory networks to make quantitative 
decisions under resource constraints. We introduce Signal Hierarchy Theory enabling 
unified Bio-PN models where metabolic pathways (mass transfer) and regulatory 
signals (information transfer) coexist with formal semantics. Signal places (Ψ) 
with consumption semantics capture hierarchical preemption mechanisms essential 
for cell fate commitment and decision finality.

[PARAGRAPH 2 - QUANTITATIVE INSIGHTS]
Validation reveals profound biological insights: ATP concentration gates B. subtilis 
sporulation (16× reduction triggers pathway switch), basin of attraction analysis 
quantifies commitment reliability (>95% within attractors), and lambda phage 
decision circuits demonstrate that signal depletion ensures irreversible commitment 
(50% → 95% accuracy improvement). These quantitative regulatory mechanisms were 
inaccessible in classical Bio-PN formalism.

[PARAGRAPH 3 - UNIFIED FRAMEWORK]
Signal hierarchy integrates with weak independence theory (distinguishing competitive 
from convergent coupling) into a unified 13-tuple formalism. This enables 2D 
computational architecture where metabolic reactions execute correctly in parallel 
while hierarchical signals coordinate system-wide regulation. The framework reflects 
biological reality: cells do not separate metabolism from regulation.

[PARAGRAPH 4 - IMPACT]
This work provides rigorous foundation for translational systems biology. Applications 
span synthetic biology (engineered circuits with >95% reliability), drug discovery 
(ATP-dependent transporter hierarchies), and precision medicine (predictive models 
of cellular decisions under therapeutic intervention). The unified framework bridges 
molecular mechanisms with cellular decision-making at quantitative precision.

[PARAGRAPH 5 - CLOSING]
Signal Hierarchical Petri Nets extend classical theory with biological realism, 
enabling computational models that capture both the molecular detail and regulatory 
control of cellular biochemistry. Open-source implementation ensures reproducibility 
and community adoption for next-generation systems biology.
```

**KEY CHANGES:**
- Lead with cellular decision-making, not formalism
- Quantitative insights foregrounded (16×, >95%, 50%→95%)
- Performance benefits mentioned but not emphasized
- Closes with biological realism, not computational efficiency

---

### PHASE 3: Language and Emphasis Shifts

#### 3.1 Global Find-Replace Reframing

**Throughout manuscript, change emphasis:**

**REDUCE EMPHASIS ON:**
- "simulation speedup" → "computational efficiency benefit"
- "parallel execution" → "correct concurrent execution"
- "2-4× faster" → "maintains correctness with parallel benefit"
- "performance gains" → "implementation advantages"

**INCREASE EMPHASIS ON:**
- "quantitative biological insights"
- "unified metabolic-regulatory modeling"
- "hierarchical preemption mechanisms"
- "signal depletion ensures commitment"
- "ATP-gated decisions"
- "basin of attraction analysis"
- "irreversible cell fate commitment"

#### 3.2 Specific Phrase Changes

**Abstract:**
- "enabling 2-4× simulation speedup" → "enabling correct parallel execution (2-4× faster as implementation benefit)"
- "quantify both performance gains and hierarchical control advantages" → "reveal quantitative hierarchical control mechanisms with computational efficiency as side benefit"

**Introduction:**
- "massive substrate-level parallelism and hierarchical regulatory control" → "hierarchical regulatory control integrating metabolic and signaling networks"

**Validation:**
- Every instance of "speedup: X×" should be preceded by biological insight
- "2.8× parallel speedup" → "71% weakly independent transitions execute correctly in parallel (2.8× faster implementation)"

**Discussion:**
- Section 7.2 title: "Practical Impact" → "Biological and Computational Impact"
- Reorder to put biological insights first

---

## IMPLEMENTATION PLAN

### PRIORITY 1 (CRITICAL - Do First):
1. ✅ Abstract complete rewrite (use NEW STRUCTURE above)
2. ✅ Introduction Section 1.4 Contributions reordering
3. ✅ Introduction Section 1.1 Motivation reframing
4. ✅ Conclusion complete rewrite (use NEW STRUCTURE above)

### PRIORITY 2 (HIGH - Do Next):
5. ✅ Discussion Section 7.1 paragraph reordering
6. ✅ Discussion Section 7.2 complete restructure (add 7.2.1, 7.2.2)
7. ✅ Validation Section 6.5 (B. subtilis) expansion
8. ✅ Validation Section 6.6 (Lambda phage) expansion

### PRIORITY 3 (MEDIUM - Polish):
9. ✅ Section 3 introduction reframing paragraph
10. ✅ Global emphasis shifts (reduce "speedup", increase "insights")
11. ✅ Table 5 add "Unified Modeling" column
12. ✅ Keywords reordering (put biology terms first)

### PRIORITY 4 (OPTIONAL - Consider):
13. ⏸️ Title revision (get feedback first)
14. ⏸️ Swap Section 3 and 4 order (risky, may confuse reviewers)

---

## EXPECTED OUTCOMES

### Before Revision:
- **Perceived as:** Computational methods paper (parallelization algorithm)
- **Main contribution:** Weak independence theory for speedup
- **Secondary contribution:** Signal hierarchy as formalism extension
- **Validation emphasis:** Performance benchmarks

### After Revision:
- **Perceived as:** Biological modeling breakthrough (unified formalism)
- **Main contribution:** Signal hierarchy enabling metabolic+regulatory unification
- **Secondary contribution:** Weak independence ensuring computational correctness
- **Validation emphasis:** Quantitative biological insights (ATP thresholds, commitment)

### Review Impact:
- **Before:** "Nice computational optimization, limited biological novelty"
- **After:** "Profound biological insight, enables new systems biology questions"

### Target Journals Shift:
- **Before:** BMC Bioinformatics (methods focus)
- **After:** PLOS Computational Biology, Cell Systems (biological discovery focus)

---

## RATIONALE SUMMARY

The current manuscript undersells its primary contribution. **Signal Hierarchy Theory** is revolutionary because it:

1. **Unifies two historically separate modeling paradigms:**
   - Metabolic networks (ODE-based, mass transfer)
   - Regulatory networks (Boolean/discrete, information flow)

2. **Enables quantitative analysis of regulatory mechanisms:**
   - ATP thresholds for pathway switching (16× quantified)
   - Commitment reliability (>95% basin convergence)
   - Decision finality (50% → 95% with signal depletion)

3. **Reflects biological reality:**
   - Cells don't separate metabolism and regulation
   - Energy status hierarchically controls pathways
   - Signal depletion ensures irreversible decisions

**Weak independence** is important but **enabling technology**, not the main event. It ensures that unified models with hundreds of reactions can execute correctly. The 2-4× speedup is a nice side benefit, not the contribution.

The revision reframes the narrative to foreground the biological breakthrough while maintaining computational rigor. This positions the work for high-impact biological journals rather than specialized computational venues.

---

## NEXT STEPS

1. Review this plan with author
2. Implement PRIORITY 1 changes (abstract, contributions, conclusion)
3. Validate new narrative flow
4. Implement PRIORITY 2 (discussion, case studies)
5. Polish with PRIORITY 3 (global emphasis)
6. Consider PRIORITY 4 (title, section reordering) based on feedback
7. Recompile and check page count (may expand to 13-14 pages with case study expansion)
8. Final read-through for narrative consistency

---

**Document Status:** READY FOR REVIEW  
**Estimated Revision Time:** 8-12 hours (careful rewriting required)  
**Expected Impact:** Shifts perceived contribution from computational methods to biological discovery
