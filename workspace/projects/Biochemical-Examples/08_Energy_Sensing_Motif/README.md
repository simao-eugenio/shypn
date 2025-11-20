# Example 08: Energy Sensing Regulatory Motif

**Phase 3: Integration - Complete Pathways**

## Biological Context

Glycolysis is regulated by cellular **energy charge** (ATP/AMP ratio). Two key regulatory enzymes demonstrate coordinated control:

1. **Phosphofructokinase-1 (PFK)**: The rate-limiting step
   - **Inhibited by high ATP** (energy sufficient, slow down)
   - **Activated by AMP** (energy depleted, speed up)
   - **Activated by F-1,6-BP** (product activation - positive feedback)

2. **Pyruvate Kinase (PK)**: Final ATP-generating step
   - **Inhibited by high ATP** (energy sufficient, slow down)
   - **Activated by F-1,6-BP** (feed-forward activation)

This creates a **feed-forward loop**: F-1,6-BP (product of PFK) activates PK downstream, coordinating the entire pathway.

## Learning Objectives

### Biochemistry
- Understand energy charge sensing (ATP/AMP ratio)
- Recognize feed-forward activation motifs
- See coordinated regulation of multiple enzymes
- Observe how allosteric effectors fine-tune flux

### Petri Net Modeling
- **Activator arcs**: Positive regulatory inputs (not yet implemented - use rate formulas)
- **Multiple inhibitor arcs**: Combined negative regulation
- **Feed-forward loops**: Regulatory motif detection
- **Coordination analysis**: Multiple transitions regulated by same metabolite

## Model Structure

### Places (Metabolites)
1. **F6P** (Fructose-6-phosphate, 0.1 mM) - Substrate for PFK
2. **ATP** (3 mM) - Energy currency and inhibitor
3. **ADP** (0.5 mM) - Low energy signal
4. **AMP** (0.05 mM) - Very low energy signal (activator)
5. **F-1,6-BP** (Fructose-1,6-bisphosphate, 0.01 mM) - PFK product, activates PK
6. **PEP** (Phosphoenolpyruvate, 0.05 mM) - PK substrate
7. **Pyruvate** (0.1 mM) - Final product

### Transitions (Enzymes)
1. **PFK-1** (T1): F6P + ATP → F-1,6-BP + ADP
   - Inhibitor arc: ATP ⊸ PFK-1 (weight = 2.5 mM threshold)
   - Blocked when ATP ≥ 2.5 mM
   
2. **PK** (T2): PEP + ADP → Pyruvate + ATP
   - Inhibitor arc: ATP ⊸ PK (weight = 2.0 mM threshold)
   - Blocked when ATP ≥ 2.0 mM

3. **ATPase** (T3): ATP → (consumed) - SINK transition
   - Simulates basal ATP consumption by cellular processes
   - Constant rate = 0.05 mM/s
   - Allows ATP to decrease, relieving inhibition

### Regulatory Logic

**Simplified Rate Formulas** (for Petri net foundation testing):
```
PFK-1: 0.094 * (F6P / (0.1 + F6P)) * (ATP / (0.05 + ATP))
PK:    0.15 * (PEP / (0.05 + PEP)) * (ADP / (0.5 + ADP))
```

**Inhibitor Arc Semantics**:
- **PFK-1 blocked**: When ATP ≥ 2.5 mM (transition cannot fire)
- **PK blocked**: When ATP ≥ 2.0 mM (transition cannot fire)
- **Both active**: When ATP < 2.0 mM

## Expected Behavior

### Initial State (ATP = 3.0 mM)
- **Both transitions BLOCKED** by inhibitor arcs
- ATP slowly drains via ATPase sink (0.05 mM/s)
- F6P and PEP remain unchanged

### ATP drops below 2.5 mM
- **PFK-1 activates** (inhibition relieved)
- Begins consuming F6P and ATP, producing F-1,6-BP and ADP
- PK still blocked (ATP still ≥ 2.0 mM)

### ATP drops below 2.0 mM
- **Both transitions active**
- Full glycolysis pathway operating
- ATP production by PK now active
- **Result**: Glycolysis accelerates, generates more ATP

### Feed-Forward Activation
- As **F-1,6-BP** accumulates from PFK activity:
  1. Activates PFK itself (positive feedback - amplifies signal)
  2. Activates PK downstream (feed-forward - coordinates pathway)
- **Result**: When upper glycolysis is active, lower glycolysis is primed

### Key Observations
1. **ATP/AMP ratio** acts as master regulator
2. **F-1,6-BP** coordinates PFK and PK (feed-forward loop)
3. **Allosteric control** is faster than transcriptional regulation
4. **Pathway flux** responds dynamically to energy demand

## Regulatory Motif: Feed-Forward Loop

```
     F6P
      ↓
    [PFK] ⊣ ATP
      |    ⊕ AMP
      |    ⊕ F-1,6-BP (positive feedback)
      ↓
   F-1,6-BP ────────┐
      ↓             ↓ (feed-forward activation)
    (...)          [PK] ⊣ ATP
      ↓             ↑
     PEP ──────────┘
      ↓
   Pyruvate
```

**Type**: Coherent feed-forward loop (Type 1)
- F-1,6-BP directly activates PK
- F-1,6-BP indirectly activates PK (via pathway intermediates)
- **Function**: Accelerates response when substrate is abundant

## Topology Features to Explore

### Regulatory Network
- **Inhibitor arcs**: ATP → PFK, ATP → PK (shown as dashed lines with ⊣)
- **Activator logic**: Embedded in rate formulas (AMP, F-1,6-BP)
- **Feed-forward motif**: F-1,6-BP activates both its source (PFK) and downstream target (PK)

### Graph Properties
- **Type**: Linear pathway with multiple regulatory inputs
- **Motif**: Feed-forward loop (F-1,6-BP → PFK, F-1,6-BP → PK)
- **Coordination**: ATP inhibits both PFK and PK
- **Sensitivity**: AMP acts as early warning signal (appears before ATP drops significantly)

## Validation Checklist

- [ ] High ATP (3 mM) inhibits both PFK and PK (slow rates)
- [ ] Low ATP (1 mM) + high AMP (0.5 mM) activates PFK (fast rate)
- [ ] F-1,6-BP accumulation activates PK (feed-forward)
- [ ] Energy charge calculation: ATP/(ATP+ADP+AMP)
- [ ] Coordinated response: both enzymes respond to ATP/AMP
- [ ] Feed-forward loop detected by topology analyzer

## Kinetic Parameters

**PFK-1**:
- Vmax = 0.094 mM/s
- Km(F6P) = 0.1 mM
- Km(ATP) = 0.05 mM
- Ka(AMP) = 0.02 mM (activator constant)
- Ki(ATP) = 0.5 mM (inhibitor constant, high ATP)
- Ka(F-1,6-BP) = 0.01 mM (positive feedback)
- Hill coefficient (ATP) = 2.5 (cooperativity)

**Pyruvate Kinase**:
- Vmax = 0.15 mM/s
- Km(PEP) = 0.05 mM
- Km(ADP) = 0.5 mM
- Ka(F-1,6-BP) = 0.01 mM (feed-forward activation)
- Ki(ATP) = 1.0 mM

## References

1. **Fell, D.A.** (1997). *Understanding the Control of Metabolism*. Portland Press. Chapter 4: Regulation of enzyme activity.

2. **Stryer, L., Berg, J.M., Tymoczko, J.L.** (2012). *Biochemistry*, 7th ed. Chapter 16: Glycolysis and Gluconeogenesis - Regulation section.

3. **Mangan, S., Alon, U.** (2003). Structure and function of the feed-forward loop network motif. *Proc Natl Acad Sci USA* 100:11980-11985.

4. **Shlomi, T., et al.** (2005). Network motifs in integrated cellular networks of transcription-regulation and protein-protein interaction. *Proc Natl Acad Sci USA* 102:1805-1810.

## Next Steps

After mastering this example:
- Understand how energy charge coordinates metabolism
- Recognize feed-forward loops in other pathways
- Proceed to **Example 09**: Complete 10-step glycolysis pathway

---
*Part of the SHYpn Biochemical Examples - Progressive Learning Series*
