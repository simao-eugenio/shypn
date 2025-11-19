# Example 07: Upper Glycolysis Mini-Pathway

## Overview
Demonstrates pathway connectivity and **reversible reactions** using the first three steps of glycolysis:
1. **Hexokinase (T1)**: Glucose + ATP → G6P + ADP
2. **Phosphoglucose Isomerase (T2)**: G6P ⇌ F6P (reversible)
3. **Phosphofructokinase (T3)**: F6P + ATP → F-1,6-BP + ADP

## Key Features

### Reversible Transition (T2 - PGI)
Uses **directional rate functions** to make reversible behavior explicit:

```json
{
  "id": "T2",
  "name": "PGI",
  "rate_forward": "0.41 * G6P",
  "rate_reverse": "0.14 * F6P"
}
```

**Net Rate Calculation:**
```
net_rate = rate_forward - rate_reverse
net_rate = 0.41 * G6P - 0.14 * F6P
```

**Flow Direction:**
- When `net_rate > 0`: Forward flow (G6P → F6P)
- When `net_rate < 0`: Reverse flow (F6P → G6P)
- When `net_rate = 0`: Equilibrium state

**Equilibrium:**
```
At equilibrium: 0.41 * [G6P] = 0.14 * [F6P]
Therefore: [G6P]/[F6P] = 0.14/0.41 = 0.341
Or: [F6P]/[G6P] = 2.93
```

### Arc Structure for Reversible Transitions
T2 has only **forward arcs** (P2→T2→P3):
- **A5**: P2 (G6P) → T2
- **A6**: T2 → P3 (F6P)

The engine automatically handles reverse flow when rate < 0:
- Consumes from P3 (via A6 reversed)
- Produces to P2 (via A5 reversed)

## Initial Conditions
| Place | Compound | Concentration |
|-------|----------|---------------|
| P1 | Glucose | 5.0 mM |
| P2 | G6P | 0.1 mM |
| P3 | F6P | 0.05 mM |
| P4 | F-1,6-BP | 0.01 mM |
| P5 | ATP | 3.0 mM |
| P6 | ADP | 0.5 mM |

## Expected Behavior

### Time Evolution (0-30 seconds)
1. **Glucose (P1)**: Decreases as consumed by T1
   - 5.0 → 4.8 → 4.5 mM
2. **G6P (P2)**: Increases initially, then stabilizes
   - 0.1 → 0.2 → 0.25 mM
3. **F6P (P3)**: Increases slowly ✓
   - 0.05 → 0.06 → 0.08 mM
4. **F-1,6-BP (P4)**: Increases as pathway flows
   - 0.01 → 0.015 → 0.03 mM

### Rate Analysis at t=0
```
T1 (HK) rate = 0.124 * (5.0/5.1) * (3.0/3.4) = 0.107 mM/s
T2 (PGI):
  - Forward rate = 0.41 * 0.1 = 0.041 mM/s
  - Reverse rate = 0.14 * 0.05 = 0.007 mM/s
  - Net rate = 0.041 - 0.007 = 0.034 mM/s (FORWARD)
T3 (PFK) rate = 0.094 * (0.05/0.15) * (3.0/3.05) = 0.031 mM/s
```

### Steady State Expectations
- **G6P/F6P ratio**: Approaches ~2.93 (equilibrium constant)
- **Pathway flux**: Limited by slowest step (likely T3 at low F6P)
- **ATP depletion**: Slows all reactions as ATP decreases

## Directional Rates vs Combined Rate

### Old Format (Combined)
```json
{
  "rate": "0.41 * G6P - 0.14 * F6P"
}
```
✗ Less clear which direction is forward
✗ Hard to identify individual rate constants
✗ Reversibility is implicit

### New Format (Directional)
```json
{
  "rate_forward": "0.41 * G6P",
  "rate_reverse": "0.14 * F6P"
}
```
✓ Explicit forward and reverse directions
✓ Clear rate constants (k_f = 0.41, k_r = 0.14)
✓ Better for teaching and documentation
✓ Compatible with both formats

## Usage
1. Load model in SHyPN
2. Set playback speed to 0.1x - 1.0x
3. Run simulation for 30-60 seconds
4. Observe:
   - P3 (F6P) should **increase** (not decrease)
   - G6P/F6P ratio approaches 2.93
   - Smooth continuous flow through pathway

## Educational Value
- **Pathway Connectivity**: How metabolites flow through sequential reactions
- **Reversible Reactions**: Bidirectional flux based on concentration gradients
- **Equilibrium Dynamics**: System approaches thermodynamic equilibrium
- **Rate Constants**: How k_forward and k_reverse determine equilibrium ratio

## References
- Hexokinase: KEGG EC 2.7.1.1
- Phosphoglucose Isomerase: KEGG EC 5.3.1.9
- Phosphofructokinase: KEGG EC 2.7.1.11
