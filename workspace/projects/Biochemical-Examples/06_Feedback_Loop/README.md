# Example 6: Feedback Loop - Threonine to Isoleucine Biosynthesis

## Biological Context

The biosynthesis of isoleucine from threonine is a classic example of **end-product feedback inhibition**. The final product (isoleucine) inhibits the first committed enzyme (threonine deaminase) to prevent overproduction. This is a fundamental regulatory mechanism in amino acid biosynthesis.

**Feedback Inhibition**: The end product of a metabolic pathway inhibits an enzyme acting early in the pathway, creating a negative feedback loop.

## Biochemical Pathway

```
Threonine → α-Ketobutyrate → α-Aceto-α-hydroxybutyrate 
    → α,β-Dihydroxyisovalerate → Isoleucine
    
Isoleucine ⊣ Threonine Deaminase (feedback inhibition)
```

**Organisms**: E. coli, other bacteria  
**Location**: Cytoplasm  
**Regulation**: Classic feedback inhibition loop

## Model Components

### Places (5)
1. **P1 - Threonine** (5.0 mM): Starting substrate
2. **P2 - α-Ketobutyrate** (0.5 mM): First intermediate
3. **P3 - α-Aceto-α-hydroxybutyrate** (0.3 mM): Second intermediate
4. **P4 - α,β-Dihydroxyisovalerate** (0.2 mM): Third intermediate
5. **P5 - Isoleucine** (0.1 mM): End product (orange border, acts as inhibitor)

### Transitions (4)
- **T1 - Threonine Deaminase**: First committed step (feedback regulated)
- **T2 - Acetohydroxyacid Synthase**: Second step
- **T3 - Acetohydroxyacid Isomeroreductase**: Third step
- **T4 - Dihydroxyacid Dehydratase**: Final step (simplified)

### Arcs (9)
- **A1**: P1 → T1 - Threonine consumption
- **A2**: T1 → P2 - α-Ketobutyrate production
- **A3**: P2 → T3 - Intermediate consumption
- **A4**: T2 → P3 - Intermediate production
- **A5**: P3 → T3 - Intermediate consumption
- **A6**: T3 → P4 - Intermediate production
- **A7**: P4 → T4 - Intermediate consumption
- **A8**: T4 → P5 - Isoleucine production
- **A9**: P5 ⊣ T1 - **Inhibitor arc** - feedback inhibition (red circle endpoint)

## Rate Expressions

**T1 (Threonine Deaminase - REGULATED)**:
```
rate = (0.8 * Threonine / (0.5 + Threonine)) / (1.0 + (Isoleucine / 0.05)^2.5)
```
- Michaelis-Menten kinetics with feedback inhibition
- Ki = 0.05 mM (very sensitive to isoleucine)
- Hill coefficient = 2.5 (cooperative inhibition)

**T2, T3, T4 (Downstream enzymes)**:
- Simple Michaelis-Menten kinetics
- No regulation (constitutively active)

## Expected Behavior

### Simulation (200s duration)
- **Initial phase**: Rapid isoleucine synthesis from threonine pool
- **Accumulation**: Isoleucine concentration increases
- **Feedback kicks in**: T1 activity decreases as isoleucine rises
- **Steady state**: Balanced production matching cellular needs
- **Long path**: Intermediates show sequential buildup and depletion

### Topology Analysis

**Structural**:
- **Paths**: Linear pathway P1 → T1 → P2 → T2 → P3 → T3 → P4 → T4 → P5
- **Cycles**: Feedback loop P5 ⊣ T1 (inhibitor arc creates regulatory cycle)
- **Critical path**: 4 transitions in sequence

**Behavioral**:
- **Boundedness**: Continuous model
- **Cycles**: Should detect feedback cycle via inhibitor arc

**Biological**:
- **Regulatory Structure**: Should detect **inhibitor arc A9** as regulatory connection
- **Classification**: All transition pairs Independent (no shared substrates)
- **Pathway length**: 4-step sequential conversion

## Key Learning Points

1. **Feedback Inhibition**: Classic negative feedback regulation mechanism
2. **Pathway Control**: First committed enzyme is typical regulatory point
3. **Multi-step Pathways**: Sequential transformations with intermediates
4. **Inhibitor Arcs**: Red circle endpoint indicates inhibition relationship
5. **Metabolic Economy**: Prevents wasteful overproduction of amino acids
6. **Regulatory Cycles**: Topology analysis should detect feedback loop

## Metadata

**Compounds**:
- Threonine: KEGG C00188, ChEBI 26986
- α-Ketobutyrate: KEGG C00109, ChEBI 16763
- α-Aceto-α-hydroxybutyrate: KEGG C06006, ChEBI 15830
- α,β-Dihydroxyisovalerate: KEGG C04039, ChEBI 16304
- Isoleucine: KEGG C00407, ChEBI 17191

**Enzymes**:
- T1: Threonine deaminase (EC 4.3.1.19, K01754)
- T2: Acetohydroxyacid synthase (EC 2.2.1.6, K01652)
- T3: Acetohydroxyacid isomeroreductase (EC 1.1.1.86, K00053)
- T4: Dihydroxyacid dehydratase (EC 4.2.1.9, K01687)

## References

- Umbarger HE. (1956) Evidence for a negative-feedback mechanism in the biosynthesis of isoleucine. Science 123(3202):848.
- KEGG Pathway: Valine, leucine and isoleucine biosynthesis (map00290)
- Berg JM, Tymoczko JL, Stryer L. (2002) Biochemistry. 5th edition. Section 24.3: Amino Acid Biosynthesis Is Regulated by Feedback Inhibition.
