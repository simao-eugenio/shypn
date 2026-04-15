# Signal Hierarchy Paper Timeline

**Start Date:** December 22, 2025  
**Target Submission:** March 2026 (10 weeks)

---

## Week 1: Foundation (Dec 22-28) ✓ COMPLETED

**Status:** Phase 0 Complete + Phase 1 Planning Done

**Completed:**
- [x] Directory structure created
- [x] Abstract v0.2 finalized (information flow focus)
- [x] Extended outline v2 created (information flow → compartmentalization)
- [x] Theory framework established (signal hierarchy + information bottlenecks)
- [x] Experimental validation (2 batches: UV depleted vs active)
- [x] Attractor plots generated (proof of concept)
- [x] Detailed implementation plan created (7-compartment model)

**Key Results:**
- Batch batch_20251224_163233 (UV depleted): 47% CI / 38% Cro / 15% undecided
- Batch batch_20251224_170509 (UV active): 3% CI / 95% Cro / 2% undecided
- Demonstrated: Signal strength controls bistability (UV → lytic bias)

**Next:** Begin Phase 1 implementation (hierarchical model)

---

## Week 2: Hierarchical Model Implementation (Dec 29 - Jan 4)

**Deliverables:**
- [ ] lambda_signal_hierarchy_v2.shy (7-compartment model)
- [ ] Layer 0: DNA damage sensor (Compartment 1A) 
- [ ] Layer 1: Signal integration (Compartments 2A, 2B)
- [ ] Layer 2: CI-Cro decision core (Compartment 3) [extend existing]
- [ ] Layer 3: Effector modules (Compartments 4A, 4B)
- [ ] Visual coding: Compartment boundaries, signal places
- [ ] Behavioral validation: 100 replicates, chi-square test

**Tasks:**
- Implement Steps 1-8 from HIERARCHICAL_IMPLEMENTATION_PLAN.md
- Add CII integration module
- Add CI cleavage mechanism (RecA-dependent)
- Add Int/Lysis effector modules
- Test compartment independence
- Calculate mutual information between layers

**Goal:** Functional 7-compartment hierarchical model with information flow quantification

---

## Week 3: Information Flow Analysis (Jan 5-11)

**Deliverables:**
- [ ] Theory section complete (sections 2.1-2.4)
- [ ] Figure 1 generated (publication quality)
- [ ] Formal definitions validated

**Tasks:**
- Write Definition 1 (signal places)
- Write Definition 2 (arc semantics)
- Document refactoring procedure (5 steps)
- Describe architectural patterns (3 patterns)
- Generate Figure 1 (Python/LaTeX)

**Goal:** Solid mathematical foundation

---

## Week 3: Lambda Case Study (Jan 5-11)

**Deliverables:**
- [ ] Methods section complete (sections 3.1-3.3)
- [ ] Figure 2 generated (model comparison)
- [ ] Equations typeset

**Tasks:**
- Document lambda phage model (12 places, 17 transitions)
- Show original rate functions (Equations 1-2)
- Show refactored rate functions (Equations 3-4)
- Detail refactoring procedure (applied to lambda)
- Generate Figure 2 (before/after diagrams)

**Goal:** Concrete demonstration of theory

---

## Week 4: Validation (Jan 12-18)

**Deliverables:**
- [ ] Simulation data collected (200 replicates total)
- [ ] Statistical analysis complete
- [ ] Results section drafted (sections 4.1-4.4)
- [ ] Figure 3 generated (validation plots)

**Tasks:**
- Run refactored model (100 replicates)
- Compare with original (chi-square, KS tests)
- Document behavioral equivalence
- Show architectural advantages
- Generate Figure 3 (distributions, time courses, phase portrait)

**Goal:** Proof of correctness

---

## Week 5: Generalization (Jan 19-25)

**Deliverables:**
- [ ] Additional examples documented (quorum sensing, metabolism)
- [ ] Generalization section drafted (section 5)
- [ ] Figure 4 generated (example diagrams)

**Tasks:**
- Document quorum sensing refactoring
- Create metabolic integration example
- Show compartmentalization pattern
- Generate Figure 4 (3 panels)

**Goal:** Demonstrate broad applicability

---

## Week 6: Discussion (Jan 26 - Feb 1)

**Deliverables:**
- [ ] Discussion section complete (section 6)
- [ ] Comparison to prior work detailed
- [ ] Limitations acknowledged
- [ ] Future work outlined

**Tasks:**
- Compare to SBML qualifiers
- Compare to BioNetGen
- Discuss advantages (4 points)
- Discuss limitations (4 points)
- Propose future research directions

**Goal:** Position work in context

---

## Week 7: Polish & Review (Feb 2-8)

**Deliverables:**
- [ ] Complete draft (all sections)
- [ ] Conclusion written
- [ ] References compiled
- [ ] Supplementary materials prepared

**Tasks:**
- Write conclusion (0.5 pages)
- Compile bibliography (BibTeX)
- Create supplementary document
- Internal consistency check
- Grammar and style editing

**Goal:** Submission-ready draft

---

## Week 8: Internal Review (Feb 9-15)

**Deliverables:**
- [ ] Revised draft (incorporating feedback)
- [ ] All figures finalized
- [ ] Supplementary complete

**Tasks:**
- Self-review (check all claims)
- Peer review (if available)
- Address feedback
- Final figure adjustments
- Proofread entire manuscript

**Goal:** High-quality manuscript

---

## Week 9: Submission Prep (Feb 16-22)

**Deliverables:**
- [ ] Journal selected
- [ ] Manuscript formatted per guidelines
- [ ] Cover letter written
- [ ] Author information prepared

**Tasks:**
- Choose journal (PLOS Comp Bio vs Bioinformatics)
- Format manuscript (template, style)
- Write cover letter
- Prepare author contributions
- Prepare data availability statement

**Goal:** Ready to submit

---

## Week 10: Submission (Feb 23 - Mar 1)

**Deliverables:**
- [ ] Manuscript submitted
- [ ] Confirmation received

**Tasks:**
- Upload manuscript
- Upload figures
- Upload supplementary materials
- Submit through journal portal
- Confirm submission

**Goal:** Paper under review!

---

## Milestones

- **Week 2:** Theory foundation solid ✓
- **Week 4:** Validation complete ✓
- **Week 6:** Full draft exists ✓
- **Week 8:** Ready for submission ✓
- **Week 10:** Submitted! ✓

---

## Contingency

**If behind schedule:**
- Skip metabolic example (keep quorum sensing only)
- Simplify Figure 4 (2 panels instead of 3)
- Move advanced theory to supplementary

**If ahead of schedule:**
- Add more examples (MAPK cascade)
- Create video abstract
- Prepare preprint for bioRxiv

---

## Success Criteria

**Minimum:**
- Theory formally defined ✓
- Lambda phage validated ✓
- One additional example ✓
- Submitted to Q1 journal ✓

**Target:**
- Three examples validated ✓
- Published in PLOS Comp Bio ✓
- Cited in future work ✓

**Stretch:**
- Featured article ✓
- Community adoption ✓
- Software integration (KEGG, BioModels) ✓
