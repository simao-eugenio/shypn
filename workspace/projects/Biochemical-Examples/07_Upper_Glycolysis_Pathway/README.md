# Example 07: Upper Glycolysis Mini-Pathway

**Phase 3: Integration - Complete Pathways**

## Biological Context

The first three steps of glycolysis form the "preparatory phase" where glucose is phosphorylated twice and then split:

1. **Hexokinase (HK)**: Glucose + ATP → Glucose-6-phosphate + ADP
2. **Phosphoglucose Isomerase (PGI)**: G6P ⇌ Fructose-6-phosphate  
3. **Phosphofructokinase-1 (PFK)**: F6P + ATP → Fructose-1,6-bisphosphate + ADP

This mini-pathway demonstrates:
- **Sequential enzyme reactions** with shared intermediates
- **Metabolite channeling** (G6P flows from HK to PGI to PFK)
- **Energy investment** (2 ATP consumed in preparatory phase)
- **Pathway flux** analysis and steady-state behavior

## Learning Objectives

### Biochemistry
- Understand the preparatory phase of glycolysis
- Recognize the "energy investment" of 2 ATP molecules
- See how intermediates connect sequential reactions
- Observe pathway flux and metabolite pool sizes

### Petri Net Modeling
- **Graph connectivity**: Places shared between multiple transitions
- **Pathway topology**: Linear chain with cofactor cycles (ATP/ADP)
- **P-invariants**: Conservation laws (ATP + ADP = constant)
- **Flux analysis**: Steady-state flow through pathway
- **Source/sink analysis**: Glucose source, F-1,6-BP sink

## Model Structure

### Places (Metabolites)
1. **Glucose** (5 mM) - Blood glucose concentration
2. **G6P** (Glucose-6-phosphate, 0.1 mM) - Branch point to pentose phosphate pathway
3. **F6P** (Fructose-6-phosphate, 0.05 mM) - Precursor to F-1,6-BP
4. **F-1,6-BP** (Fructose-1,6-bisphosphate, 0.01 mM) - Product of preparatory phase
5. **ATP** (3 mM) - Energy currency
6. **ADP** (0.5 mM) - Energy depleted form

### Transitions (Enzymes)
1. **Hexokinase**: First committed step, traps glucose in cell
2. **PGI**: Rapid equilibrium, reversible isomerization
3. **PFK-1**: Rate-limiting step, major regulatory point

### Kinetic Parameters

All parameters from validated biochemical literature:

**Hexokinase (HK)**:
- Vmax = 0.124 mM/s
- Km(Glucose) = 0.1 mM
- Km(ATP) = 0.4 mM

**Phosphoglucose Isomerase (PGI)**:
- k_forward = 0.41 s⁻¹  
- k_reverse = 0.14 s⁻¹
- Keq = 0.34 (favors G6P)

**Phosphofructokinase-1 (PFK)**:
- Vmax = 0.094 mM/s
- Km(F6P) = 0.1 mM
- Km(ATP) = 0.05 mM

## Expected Behavior

### Initial Phase (t = 0-10s)
- **Glucose** decreases steadily as HK consumes it
- **G6P** accumulates initially (HK faster than PGI)
- **F6P** rises slowly (PGI equilibrium favors G6P)
- **F-1,6-BP** accumulates as pathway product
- **ATP** decreases (2 ATP per glucose)
- **ADP** increases correspondingly

### Steady State (t > 30s)
- Intermediate concentrations stabilize
- Flux = limiting rate (usually PFK, rate-limiting step)
- ATP/ADP ratio reaches quasi-steady state
- Pathway demonstrates "metabolite channeling"

### Key Observations
1. **G6P pool larger than F6P** (PGI equilibrium constant = 0.34)
2. **PFK is rate-limiting** (lowest Vmax among the three)
3. **ATP depletion** shows energy investment phase
4. **Smooth flux** through all three steps at steady state

## Topology Features to Explore

### Conservation Laws (P-invariants)
- **Adenine nucleotide**: ATP + ADP = 3.5 mM (constant)
- **Hexose phosphates**: G6P + F6P + F-1,6-BP (sum varies with consumption)

### Graph Properties
- **Type**: Linear pathway with cofactor cycles
- **Source**: Glucose (external input)
- **Sink**: F-1,6-BP (feeds into lower glycolysis)
- **Cycles**: ATP ⇄ ADP (cofactor regeneration)

### Pathway Analysis
- **Flux**: Measure steady-state flow rate through pathway
- **Bottleneck**: Identify rate-limiting step (PFK)
- **Accumulation**: Observe which intermediates build up (G6P > F6P)

## Validation Checklist

- [ ] Glucose decreases over time
- [ ] G6P accumulates to higher level than F6P (Keq = 0.34)
- [ ] F-1,6-BP increases steadily
- [ ] ATP decreases by ~2× the F-1,6-BP produced
- [ ] Steady-state flux through all steps converges to PFK rate
- [ ] No deadlocks or spurious equilibria
- [ ] P-invariant for ATP + ADP conserved

## References

1. **Berg, J.M., Tymoczko, J.L., Stryer, L.** (2012). *Biochemistry*, 7th ed. W.H. Freeman. Chapter 16: Glycolysis.

2. **Newsholme, E.A., Crabtree, B.** (1986). Maximum catalytic activity of some key enzymes in provision of physiologically useful information about metabolic fluxes. *J Exp Biol* 115:305-324.

3. **Teusink, B., et al.** (2000). Can yeast glycolysis be understood in terms of in vitro kinetics of the constituent enzymes? Testing biochemistry. *Eur J Biochem* 267:5313-5329.

## Next Steps

After mastering this example:
- Proceed to **Example 08**: Regulatory motifs (ATP/AMP energy sensing)
- Explore how energy charge coordinates PFK and PK
- Build toward **Example 09**: Complete 10-step glycolysis pathway

---
*Part of the SHYpn Biochemical Examples - Progressive Learning Series*
