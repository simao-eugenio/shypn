# Example 5: Competitive Inhibition - Succinate Dehydrogenase

## Biological Context

Succinate dehydrogenase (SDH) is a TCA cycle enzyme that catalyzes the oxidation of succinate to fumarate. Malonate is a classic competitive inhibitor - it structurally resembles succinate and competes for the enzyme's active site but cannot be converted to product.

**Competitive Inhibition**: Inhibitor and substrate compete for the same binding site. Increasing substrate concentration can overcome inhibition.

## Biochemical Reaction

```
Succinate + FAD → Fumarate + FADH₂  (productive)
Malonate + SDH ⇌ SDH-Malonate       (non-productive)
```

**Enzyme**: Succinate dehydrogenase (EC 1.3.5.1)  
**KEGG Reaction**: R02164  
**Inhibitor**: Malonate (structural analog of succinate)

## Model Components

### Places (5)
1. **P1 - Succinate** (3.0 mM): Substrate
2. **P2 - Malonate** (2.0 mM): Competitive inhibitor
3. **P3 - SDH** (0.01 mM): Enzyme catalyst (green border, `is_catalyst: true`)
4. **P4 - Fumarate** (0.1 mM): Product
5. **P5 - Blocked** (0.0 mM): Tracking place for inhibitor binding events

### Transitions (2)
- **T1 - Productive**: Succinate → Fumarate (productive catalysis)
- **T2 - Inhibited**: Malonate binding (non-productive, blocks enzyme)

### Arcs (7)
- **A1**: P1 (Succinate) → T1 - Substrate consumption
- **A2**: P3 (SDH) → T1 - **Catalyst arc** (enzyme used)
- **A3**: T1 → P3 (SDH) - **Catalyst arc** (enzyme returned)
- **A4**: T1 → P4 (Fumarate) - Product formation
- **A5**: P2 (Malonate) → T2 - Inhibitor consumption
- **A6**: P3 (SDH) → T2 - **Catalyst arc** (enzyme bound)
- **A7**: T2 → P5 (Blocked) - Tracking output

## Rate Expressions

**T1 (Productive)**:
```
rate = 0.5 * Succinate * SDH / (0.5 + Succinate)
```
- Vmax = 0.5 × [SDH]
- Km = 0.5 mM

**T2 (Inhibited)**:
```
rate = 0.8 * Malonate * SDH / (0.3 + Malonate)
```
- Higher affinity (Km = 0.3 mM) reflects malonate's stronger binding
- Faster rate constant reflects competitive advantage

## Expected Behavior

### Simulation (100s duration)
- **Competition**: T1 and T2 compete for available SDH enzyme
- **Enzyme depletion**: As malonate binds SDH, less enzyme available for succinate
- **Reduced productivity**: Fumarate production slows as inhibition increases
- **Steady state**: Balance between productive and inhibited enzyme forms

### Topology Analysis

**Structural**:
- **Paths**: P1 → T1 → P4 (productive), P2 → T2 → P5 (inhibited)
- **Hubs**: P3 (SDH) is critical hub connecting both transitions

**Behavioral**:
- **Boundedness**: Continuous model
- **Fairness**: T1 and T2 compete for P3 (SDH)

**Biological**:
- **Dependency**: Should detect **Competitive** relationship between T1 and T2
  - Both transitions share P3 (SDH) as **input catalyst**
  - This creates resource competition
- **Classification**: (T1, T2) → Competitive, shared catalyst P3

## Key Learning Points

1. **Catalyst Arcs**: Demonstrates bidirectional catalyst arcs (green, loop pattern)
2. **Resource Competition**: Two transitions competing for shared enzyme
3. **Competitive Inhibition Mechanism**: Inhibitor blocks active site
4. **Topology Detection**: Biological analyzer should identify competitive relationship
5. **Enzyme Kinetics**: Higher affinity inhibitor reduces substrate turnover

## Metadata

**Compounds**:
- Succinate: KEGG C00042, ChEBI 30031
- Malonate: KEGG C00383, ChEBI 30794
- Fumarate: KEGG C00122, ChEBI 18012

**Enzyme**:
- EC: 1.3.5.1
- KEGG Enzyme: K00239
- Name: Succinate dehydrogenase
- Complex: Mitochondrial Complex II

## References

- Berg JM, Tymoczko JL, Stryer L. (2002) Biochemistry. 5th edition. Section 8.5: Enzymes Can Be Inhibited by Specific Molecules.
- KEGG REACTION: R02164
- Classic example in enzymology textbooks
