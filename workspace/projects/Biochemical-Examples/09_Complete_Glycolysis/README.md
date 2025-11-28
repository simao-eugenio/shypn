# Example 09: Complete Glycolysis Pathway (10 Steps)

**Phase 4: Complete Metabolic Pathways**

## Biological Context

Glycolysis is the central metabolic pathway that converts glucose (6-carbon) into two pyruvate molecules (3-carbon), producing:
- **2 ATP net** (4 produced - 2 consumed)
- **2 NADH** (reducing equivalents)

The pathway has **three regulatory steps** with irreversible enzymes:
1. **Hexokinase (HK)**: Glucose → G6P (commits glucose to metabolism)
2. **Phosphofructokinase-1 (PFK)**: F6P → F-1,6-BP (rate-limiting step, main regulation)
3. **Pyruvate Kinase (PK)**: PEP → Pyruvate (final ATP generation)

## Learning Objectives

### Biochemistry
- Complete 10-step pathway with precise stoichiometry
- Energy investment phase (steps 1-5): Consumes 2 ATP
- Energy payoff phase (steps 6-10): Produces 4 ATP + 2 NADH
- Understand substrate channeling and pathway flux
- Recognize regulatory checkpoints

### Petri Net Modeling
- **Large-scale network**: 10 transitions, 13 metabolites
- **Reversible reactions**: Steps 2, 7, 8, 9 are near-equilibrium
- **Irreversible regulation**: Steps 1, 3, 10 (inhibitor arcs)
- **Multiple cofactors**: ATP, ADP, NAD+, NADH
- **Source/sink**: Glucose input, Pyruvate output

## Model Structure

### Places (Metabolites) - Normalized Concentrations

**Substrates & Products:**
1. **Glucose** (5.0 mM) - Input substrate via source transition
2. **G6P** (Glucose-6-phosphate, 0.8 mM)
3. **F6P** (Fructose-6-phosphate, 0.2 mM)
4. **F-1,6-BP** (Fructose-1,6-bisphosphate, 0.05 mM)
5. **DHAP** (Dihydroxyacetone phosphate, 0.03 mM)
6. **G3P** (Glyceraldehyde-3-phosphate, 0.03 mM)
7. **1,3-BPG** (1,3-Bisphosphoglycerate, 0.01 mM)
8. **3-PG** (3-Phosphoglycerate, 0.15 mM)
9. **2-PG** (2-Phosphoglycerate, 0.05 mM)
10. **PEP** (Phosphoenolpyruvate, 0.03 mM)
11. **Pyruvate** (0.2 mM) - Output via sink transition

**Cofactors:**
12. **ATP** (2.5 mM) - Energy currency
13. **ADP** (0.5 mM) - Phosphate acceptor
14. **NAD+** (0.5 mM) - Oxidizing agent
15. **NADH** (0.05 mM) - Reducing equivalent

### Transitions (Enzymes)

**Source:**
- **T0**: Glucose Source → Glucose (rate = 0.1 mM/s)

**Energy Investment Phase (2 ATP consumed):**
1. **T1 - HK** (Hexokinase): Glucose + ATP → G6P + ADP
   - Inhibitor: G6P ⊸ T1 (weight = 2.0 mM) - Product inhibition
   - Rate: `0.1 * (Glucose / (0.1 + Glucose)) * (ATP / (0.1 + ATP))`

2. **T2 - PGI** (Phosphoglucose Isomerase): G6P ⇌ F6P (reversible)
   - Forward rate: `0.5 * (G6P / (0.3 + G6P))`
   - Reverse rate: `0.5 * (F6P / (0.1 + F6P))`

3. **T3 - PFK** (Phosphofructokinase-1): F6P + ATP → F-1,6-BP + ADP
   - Inhibitor: ATP ⊸ T3 (weight = 3.0 mM) - ATP inhibition
   - Rate: `0.094 * (F6P / (0.1 + F6P)) * (ATP / (0.05 + ATP))`

4. **T4 - Aldolase**: F-1,6-BP → DHAP + G3P
   - Rate: `0.08 * (F16BP / (0.04 + F16BP))`

5. **T5 - TPI** (Triose Phosphate Isomerase): DHAP ⇌ G3P (reversible)
   - Forward rate: `0.8 * (DHAP / (0.02 + DHAP))`
   - Reverse rate: `0.8 * (G3P / (0.02 + G3P))`

**Energy Payoff Phase (4 ATP + 2 NADH produced):**

6. **T6 - GAPDH** (Glyceraldehyde-3-P Dehydrogenase): G3P + NAD+ → 1,3-BPG + NADH
   - Rate: `0.2 * (G3P / (0.01 + G3P)) * (NAD / (0.2 + NAD))`

7. **T7 - PGK** (Phosphoglycerate Kinase): 1,3-BPG + ADP ⇌ 3-PG + ATP (reversible)
   - Forward rate: `0.3 * (BPG13 / (0.005 + BPG13)) * (ADP / (0.2 + ADP))`
   - Reverse rate: `0.3 * (PG3 / (0.1 + PG3)) * (ATP / (1.0 + ATP))`

8. **T8 - PGM** (Phosphoglycerate Mutase): 3-PG ⇌ 2-PG (reversible)
   - Forward rate: `0.4 * (PG3 / (0.1 + PG3))`
   - Reverse rate: `0.4 * (PG2 / (0.03 + PG2))`

9. **T9 - Enolase**: 2-PG ⇌ PEP (reversible)
   - Forward rate: `0.15 * (PG2 / (0.03 + PG2))`
   - Reverse rate: `0.15 * (PEP / (0.02 + PEP))`

10. **T10 - PK** (Pyruvate Kinase): PEP + ADP → Pyruvate + ATP
    - Inhibitor: ATP ⊸ T10 (weight = 3.5 mM) - ATP inhibition
    - Rate: `0.15 * (PEP / (0.02 + PEP)) * (ADP / (0.2 + ADP))`

**Sink:**
- **T11**: Pyruvate → Pyruvate Sink (rate = 0.05 mM/s)

## Stoichiometry Summary

**Overall Reaction:**
```
Glucose + 2 NAD+ + 2 ADP + 2 Pi → 2 Pyruvate + 2 NADH + 2 ATP + 2 H2O
```

**ATP Balance:**
- Investment: -2 ATP (steps 1, 3)
- Payoff: +4 ATP (steps 7, 10, each produces 2 ATP because of 2 G3P)
- **Net: +2 ATP**

**Redox Balance:**
- Produces: +2 NADH (step 6, produces 2 because of 2 G3P)

## Expected Behavior

### Initial State
- Glucose = 5.0 mM (high, from source)
- ATP = 2.5 mM (moderate, PFK not inhibited)
- All intermediates at physiological concentrations

### Steady-State Flow
1. **Glucose enters** via source (T0)
2. **Investment phase** (T1-T5): Consumes ATP, accumulates F-1,6-BP
3. **Aldolase splits** F-1,6-BP into 2 trioses (DHAP, G3P)
4. **TPI equilibrates** DHAP ⇌ G3P
5. **Payoff phase** (T6-T10): Produces ATP and NADH
6. **Pyruvate exits** via sink (T11)

### Regulatory Checkpoints

**High ATP (>3.0 mM):**
- PFK blocked (ATP ≥ 3.0) → Glycolysis slows
- PK blocked (ATP ≥ 3.5) → Final step inhibited
- Energy charge high, pathway feedback inhibited

**Low ATP (<2.0 mM):**
- All checkpoints open
- Maximum glycolytic flux
- Rapid ATP regeneration

**Product Inhibition:**
- High G6P (≥2.0 mM) blocks HK → Prevents excessive glucose uptake

## Validation Checklist

- [ ] Glucose consumption matches pyruvate production (1:2 ratio)
- [ ] ATP net production = +2 per glucose
- [ ] NADH production = +2 per glucose
- [ ] Reversible reactions reach equilibrium ratios
- [ ] PFK inhibition at high ATP (>3.0 mM)
- [ ] PK inhibition at high ATP (>3.5 mM)
- [ ] HK product inhibition by G6P (>2.0 mM)
- [ ] Steady-state concentrations stable

## Kinetic Parameters

All rates simplified for Petri net foundation testing:
- Vmax values: 0.08-0.8 mM/s (adjusted for flux balance)
- Km values: 0.01-0.3 mM (physiological range)
- Reversible reactions: Keq encoded in forward/reverse rate ratios

## References

1. **Berg, J.M., Tymoczko, J.L., Stryer, L.** (2012). *Biochemistry*, 7th ed. Chapter 16: Glycolysis.

2. **Garrett, R.H., Grisham, C.M.** (2013). *Biochemistry*, 5th ed. Chapter 18: Glycolysis.

3. **Teusink, B., et al.** (2000). Can yeast glycolysis be understood in terms of in vitro kinetics? *FEBS Letters* 476:118-121.

4. **Mulukutla, B.C., et al.** (2015). Glucose metabolism in mammalian cell culture: New insights for tweaking vintage pathways. *Trends Biotechnol* 33:476-488.

## Next Steps

After mastering this example:
- Understand complete pathway dynamics and flux control
- Proceed to **Example 10**: Glycolysis + TCA Cycle integration
- Explore pathway branching in **Example 11**: Pentose Phosphate Pathway

---
*Part of the SHYpn Biochemical Examples - Progressive Learning Series*
