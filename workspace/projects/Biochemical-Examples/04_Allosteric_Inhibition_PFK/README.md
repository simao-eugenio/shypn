# Example 4: Allosteric Inhibition - Phosphofructokinase (PFK)

## Biological Context

Phosphofructokinase (PFK) is a key regulatory enzyme in glycolysis that catalyzes the phosphorylation of fructose 6-phosphate (F6P) to fructose 1,6-bisphosphate (F1,6BP). This is the committed step of glycolysis and a major control point.

**Allosteric Regulation**: High ATP levels signal sufficient energy, inhibiting PFK to prevent unnecessary glucose breakdown. This is classic negative feedback regulation.

## Biochemical Reaction

```
F6P + ATP → F1,6BP + ADP
```

**Enzyme**: Phosphofructokinase (EC 2.7.1.11)  
**KEGG Reaction**: R00756  
**Regulation**: ATP acts as allosteric inhibitor (binds regulatory site, not active site)

## Model Components

### Places (5)
1. **P1 - F6P** (2.0 mM): Substrate - fructose 6-phosphate
2. **P2 - ATP** (4.0 mM): Substrate - provides phosphate group
3. **P3 - F1,6BP** (0.1 mM): Product - fructose 1,6-bisphosphate
4. **P4 - ADP** (1.0 mM): Product - adenosine diphosphate
5. **P5 - ATP_high** (6.0 mM): Allosteric inhibitor - represents high ATP concentration

### Transitions (1)
- **T1 - PFK**: Phosphofructokinase enzyme

### Arcs (5)
- **A1**: P1 (F6P) → T1 - Substrate consumption
- **A2**: P2 (ATP) → T1 - Substrate consumption
- **A3**: T1 → P3 (F1,6BP) - Product formation
- **A4**: T1 → P4 (ADP) - Product formation
- **A5**: P5 (ATP_high) ⊣ T1 - **Inhibitor arc** (Ki = 4 mM)
  - SHYPN semantics: Transition **disabled** when `ATP_high >= 4 mM`
  - **Biological significance**: High ATP (≥4 mM) inhibits PFK (negative feedback)
  - Initial state: 6 mM ATP_high → **enzyme is inhibited** (6 ≥ 4)

## Rate Expression

```
rate = (0.8 * F6P * ATP / (1.0 + F6P + ATP)) / (1.0 + (ATP_high / 2.0)^4)
```

**Components**:
- Numerator: Michaelis-Menten kinetics for two substrates
- Denominator: Hill equation with coefficient 4 (cooperative inhibition)
- Ki = 2.0 mM (half-maximal inhibition constant in the rate formula)
- **Inhibitor arc threshold = 4 mM** (complete enzyme shutdown at high ATP)

## Simulation Behavior

**Expected Dynamics:**
- PFK converts F6P + ATP → F1,6BP + ADP
- **Rate decreases** as ATP_high (P5) increases (allosteric inhibition)
- Hill coefficient = 4 (cooperative inhibition)
- **Inhibitor threshold (Ki = 4 mM)**: When ATP_high ≥ 4 mM, transition becomes DISABLED
- At physiological ATP (6 mM), the enzyme is significantly inhibited

**Key Observable:**
- The **rate plot** shows reaction slowing as ATP accumulates
- Demonstrates **negative feedback regulation**
- **Try decreasing P5 (ATP_high) below 4 mM** → reaction should resume
- **Try increasing P5 above 4 mM** → reaction should stop completely

### Topology Analysis

**Structural**:
- **Paths**: P1 → T1 → P3, P2 → T1 → P4
- **Hubs**: T1 is a convergent hub (2 inputs, 2 outputs)

**Behavioral** (should be enabled with continuous model fix):
- **Boundedness**: Continuous model, tokens represent concentrations
- **Liveness**: T1 enabled when F6P and ATP available

**Biological**:
- **Regulatory Structure**: Should detect **inhibitor arc** A5 as regulatory connection
- **Dependency**: No transition pairs (only 1 transition)

## Key Learning Points

1. **Arc Types**: Demonstrates **inhibitor arc** (red with circle endpoint)
2. **Allosteric Regulation**: Enzyme activity modulated without affecting substrate binding
3. **Cooperative Inhibition**: Hill coefficient = 4 shows strong cooperativity
4. **Negative Feedback**: Product of pathway (ATP) inhibits upstream enzyme
5. **Energy Homeostasis**: Prevents ATP waste when energy is abundant

## Metadata

**Compounds**:
- F6P: KEGG C00085, ChEBI 16084
- ATP: KEGG C00002, ChEBI 15422
- F1,6BP: KEGG C00354, ChEBI 16905
- ADP: KEGG C00008, ChEBI 16761

**Enzyme**:
- EC: 2.7.1.11
- KEGG Enzyme: K00850
- Name: 6-phosphofructokinase

## References

- Berg JM, Tymoczko JL, Stryer L. (2002) Biochemistry. 5th edition. Section 16.2: The Glycolytic Pathway Is Tightly Controlled.
- KEGG REACTION: R00756
- Enzyme Commission: EC 2.7.1.11
