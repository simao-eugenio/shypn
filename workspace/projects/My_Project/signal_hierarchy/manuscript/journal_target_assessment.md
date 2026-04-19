# Journal Target Assessment: Signal Hierarchical Petri Nets

**Date:** 2026-04-19  
**Manuscript:** "Signal Hierarchical Petri Nets: Formal Semantics of Hierarchical Regulatory Control of Biological Systems"  
**Author:** Eugênio Simão, UFSC Araranguá

---

## Manuscript Profile

| Dimension | Characterization |
|-----------|-----------------|
| **Type** | Formal theory + biological validation |
| **Core** | 13-tuple extension of Bio-PN; two structural theorems (acyclicity, preemption) |
| **Validation** | B. subtilis ATP threshold: 2.38 mM predicted vs 2.21±0.18 mM experimental (7% error, zero fitted parameters) |
| **Additional cases** | Lambda phage (7%), MAPK (9%), yeast cell cycle (10%) |
| **Domains** | Mathematical biology, Petri net theory, systems biology, formal methods |
| **Author** | Single author (E. Simão, UFSC) |
| **Length** | ~1000 lines LaTeX, heavy on proofs and formal definitions |

---

## Assessment by Publisher

### 1. Royal Society — J. R. Soc. Interface (BEST FIT)

| Criterion | Score |
|-----------|-------|
| Scope alignment | **Excellent** — "cross-disciplinary research at the interface between physical and life sciences"; biomathematics with biological validation is core mission |
| Paper type fit | **Excellent** — accepts theory papers with empirical validation; proof-heavy content welcome |
| APC | **FREE** (Subscribe to Open 2026) |
| Format | Format-free initial submission; ≤200 words abstract (current is ~300, needs trimming) |
| IF | 3.5 |
| Single-author precedent | Yes — mathematical biology papers regularly single-authored |

**Verdict**: Top target. The paper embodies exactly what JRSI publishes: rigorous mathematical formalism applied to biological questions with quantitative validation. The proof style, theorem-driven structure, and biological case study map perfectly to JRSI's biomathematics niche. FREE APC via S2O 2026 eliminates cost.

**Adaptations needed**:
- Trim abstract to ≤200 words
- Remove PLOS-specific sections (Author Summary, Data Availability as separate section)
- Convert to Vancouver references (numbered)
- Consider reducing some proof redundancy (the paper repeats the B. subtilis computation ~4 times)

---

### 2. PLOS Computational Biology

| Criterion | Score |
|-----------|-------|
| Scope alignment | **Good** — computational methods for biological problems |
| Paper type fit | **Moderate** — prefers methods with software/implementation emphasis; heavy formalism less common |
| APC | ~$2,541 (NOT covered by CAPES agreement) |
| Format | Already formatted for PLOS |
| IF | 4.3 |

**Verdict**: Reasonable fit but expensive and slightly misaligned. PLOS Comp Bio favors papers demonstrating computational pipelines/tools more than pure formalism with proofs. The paper is already formatted for PLOS, but the $2,541 APC with no CAPES coverage is a significant disadvantage vs. JRSI's free publication.

---

### 3. IEEE/ACM Transactions on Computational Biology and Bioinformatics (TCBB)

| Criterion | Score |
|-----------|-------|
| Scope alignment | **Moderate** — favors algorithms, databases, tools over formal proofs |
| Paper type fit | **Weak** — proof-heavy theorem-driven papers uncommon in TCBB |
| APC | CAPES-covered |
| IF | 3.7 |

**Verdict**: Poor fit for THIS paper. TCBB suits the SHYPN *tool paper* (the CBD manuscript's #2 target) but not a formalism/theory paper. TCBB readers expect algorithmic contributions and benchmarks, not Petri net structural theorems.

---

### 4. Mathematical Biosciences (Elsevier)

| Criterion | Score |
|-----------|-------|
| Scope alignment | **Excellent** — "mathematical methods in biosciences" |
| Paper type fit | **Excellent** — theorem + proof + biological application is their bread-and-butter |
| APC | ~$3,340 (Elsevier standard); CAPES/CAPES-PRINT may have Elsevier agreement |
| IF | 3.9 |

**Verdict**: Strongest pure-scope match in the literature. If Elsevier APC is covered by CAPES, this would rival JRSI. Verify UFSC Elsevier agreement status.

---

### 5. Bulletin of Mathematical Biology (Springer)

| Criterion | Score |
|-----------|-------|
| Scope alignment | **Excellent** — official journal of the Society for Mathematical Biology |
| Paper type fit | **Good** — accepts formal + applied |
| APC | ~$2,890 (Springer); check CAPES Springer agreement |
| IF | 3.5 |

**Verdict**: Strong alternative if Springer is CAPES-covered. Same IF as JRSI but with APC cost.

---

## Recommendation Ranking

| Rank | Journal | IF | APC | Rationale |
|------|---------|-----|-----|-----------|
| **#1** | **J. R. Soc. Interface** | 3.5 | **FREE** | Perfect scope match + zero cost + format-free submission |
| #2 | Mathematical Biosciences | 3.9 | ~$3,340? | Best scope match if APC covered |
| #3 | PLOS Comp Bio | 4.3 | ~$2,541 | Higher IF but expensive and less formalism-friendly |
| #4 | Bull. Math. Biology | 3.5 | ~$2,890? | Good fit, check Springer/CAPES agreement |
| #5 | PLOS ONE | 3.7 | ~$1,931 | Current target; undervalues theoretical contribution |

---

## Key Insight: PLOS ONE Undervalues This Work

PLOS ONE accepts "technically sound" science regardless of novelty/impact. This paper has **high theoretical novelty** (new formalism, proven theorems, closed-form threshold prediction replacing EXPSPACE-complete analysis) that PLOS ONE's broad-scope model doesn't reward. JRSI or Math Biosciences would contextualize the contribution properly among their biomathematics readership.

---

## Two-Paper Strategy Update

| Paper | Best Target | Backup |
|-------|-------------|--------|
| CBD neuroprotection (computational biology) | JRSI | IEEE TCBB |
| Signal Hierarchy (formalism/theory) | **JRSI** | Math Biosciences |
| SHYPN tool (software) | IEEE TCBB | SoftwareX |

**Conflict note**: Both the CBD paper and this Signal Hierarchy paper target JRSI as #1. You can submit both simultaneously (different manuscripts), but consider whether the Signal Hierarchy paper should cite the CBD paper or vice versa for cross-referencing. Alternatively, submit Signal Hierarchy to JRSI first (it's the more foundational paper), then reference it in the CBD paper.
