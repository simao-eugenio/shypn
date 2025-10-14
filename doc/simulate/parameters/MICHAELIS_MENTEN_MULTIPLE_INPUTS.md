# Michaelis-Menten with Multiple Input Places

**Date**: October 13, 2025  
**Question**: "How do transitions formulate Michaelis-Menten when there is more than one input place?"

---

## Quick Answer

When a transition has **multiple input places**, you can reference them **all by name** in the rate function:

```python
# Single substrate (typical Michaelis-Menten)
rate_function = "michaelis_menten(P1, 10, 5)"

# Multiple substrates - you can:
# 1. Use only the primary substrate (first reactant)
rate_function = "michaelis_menten(P1, 10, 5)"  # Ignores P2

# 2. Use a product/sum of substrates
rate_function = "michaelis_menten(P1 * P2, 10, 5)"  # Combined concentration

# 3. Use sequential Michaelis-Menten
rate_function = "michaelis_menten(P1, 10, 5) * (P2 / (P2 + 2))"  # Two-step kinetics

# 4. Use competitive inhibition
rate_function = "competitive_inhibition(P1, P2, 10, 5, 2)"  # P2 is inhibitor
```

All place tokens are available as `P1`, `P2`, `P3`, etc. in the rate function expression.

---

## How Rate Function Evaluation Works

### Context Building

**File**: `src/shypn/engine/continuous_behavior.py:125-145`

```python
def evaluate_rate(places: Dict[int, Any], time: float) -> float:
    """Evaluate rate function with place tokens."""
    
    # Build evaluation context
    context = {
        'time': time,
        't': time,
        'min': min,
        'max': max,
        'abs': abs,
        'math': math,
        'np': np,
    }
    
    # Add all catalog functions (michaelis_menten, mass_action, etc.)
    context.update(FUNCTION_CATALOG)
    
    # Add place tokens as P1, P2, P3, ...
    for place_id, place in places.items():
        context[f'P{place_id}'] = place.tokens  # ← ALL places available!
    
    # Evaluate expression
    result = eval(rate_function, {"__builtins__": {}}, context)
    return float(result)
```

**Key Point**: ALL input places (and actually all places in the model) are available as `P{id}` variables in the rate function expression.

---

## Example Scenarios

### Scenario 1: Simple Enzyme-Substrate (Single Input)

```
Network:
  P1 (Substrate) → T1 → P2 (Product)
  
Michaelis-Menten:
  rate_function = "michaelis_menten(P1, 10, 5)"
  
Evaluation:
  context = {'P1': 20, 'P2': 5, 'time': 0.0, ...}
  rate = michaelis_menten(20, 10, 5)  # Uses P1 tokens
       = 10 * 20 / (5 + 20)
       = 200 / 25
       = 8.0
```

---

### Scenario 2: Two Substrates - Product Kinetics

```
Network:
  P1 (SubstrateA) ─┐
                   ├─→ T1 → P3 (Product)
  P2 (SubstrateB) ─┘
  
Bi-substrate Michaelis-Menten (product):
  rate_function = "michaelis_menten(P1 * P2, 10, 5)"
  
Evaluation:
  context = {'P1': 10, 'P2': 8, 'P3': 0, ...}
  combined_substrate = P1 * P2 = 10 * 8 = 80
  rate = michaelis_menten(80, 10, 5)
       = 10 * 80 / (5 + 80)
       = 800 / 85
       = 9.41
  
Explanation:
  - Treats [A]*[B] as effective substrate concentration
  - Common for reactions requiring both substrates simultaneously
  - Example: ATP + Glucose → ADP + Glucose-6-P (hexokinase)
```

---

### Scenario 3: Sequential Michaelis-Menten (Ping-Pong)

```
Network:
  P1 (SubstrateA) ─┐
                   ├─→ T1 → P4 (ProductA + ProductB)
  P2 (SubstrateB) ─┘
  P3 (Enzyme)
  
Sequential kinetics (ordered bi-bi):
  rate_function = "michaelis_menten(P1, 10, 5) * michaelis_menten(P2, 8, 3)"
  
Evaluation:
  context = {'P1': 15, 'P2': 12, 'P3': 5, ...}
  rate_A = michaelis_menten(15, 10, 5) = 10 * 15 / 20 = 7.5
  rate_B = michaelis_menten(12, 8, 3) = 8 * 12 / 15 = 6.4
  rate = rate_A * rate_B = 7.5 * 6.4 = 48.0
  
Explanation:
  - Two substrates bind sequentially to enzyme
  - Each substrate has its own Km
  - Overall rate depends on both saturations
  - Example: Transaminase reactions
```

---

### Scenario 4: Competitive Inhibition

```
Network:
  P1 (Substrate) ──┐
                   ├─→ T1 → P3 (Product)
  P2 (Inhibitor) ──┘ (doesn't consume, just binds)
  
Competitive inhibition:
  rate_function = "competitive_inhibition(P1, P2, 10, 5, 2)"
  
Evaluation:
  context = {'P1': 20, 'P2': 8, 'P3': 0, ...}
  Km_apparent = Km * (1 + [I]/Ki) = 5 * (1 + 8/2) = 5 * 5 = 25
  rate = Vmax * [S] / (Km_apparent + [S])
       = 10 * 20 / (25 + 20)
       = 200 / 45
       = 4.44
  
Explanation:
  - Inhibitor competes for active site
  - Increases apparent Km (requires more substrate)
  - Vmax unchanged
  - Example: Drug inhibition of enzymes
```

---

### Scenario 5: Allosteric Regulation (Hill Equation)

```
Network:
  P1 (Substrate) ──┐
                   ├─→ T1 → P3 (Product)
  P2 (Activator) ──┘
  
Hill kinetics with activation:
  rate_function = "hill_equation(P1, 10, 5, 2) * (1 + 0.5 * P2)"
  
Evaluation:
  context = {'P1': 10, 'P2': 4, ...}
  base_rate = hill_equation(10, 10, 5, 2)
            = 10 * 10^2 / (5^2 + 10^2)
            = 10 * 100 / 125
            = 8.0
  activation_factor = 1 + 0.5 * 4 = 3.0
  rate = 8.0 * 3.0 = 24.0
  
Explanation:
  - Substrate binds cooperatively (Hill coefficient n=2)
  - Activator enhances rate proportionally
  - Example: Phosphofructokinase (PFK) in glycolysis
```

---

## Common Patterns

### Pattern 1: Primary Substrate Only
**Use Case**: One substrate dominates, others are cofactors or always saturated

```python
rate_function = "michaelis_menten(P1, Vmax, Km)"
```

### Pattern 2: Product of Concentrations
**Use Case**: Both substrates required simultaneously (ternary complex)

```python
rate_function = "michaelis_menten(P1 * P2, Vmax, Km)"
```

### Pattern 3: Minimum of Saturations
**Use Case**: Either substrate can be limiting (random bi-bi)

```python
rate_function = "Vmax * min(P1/(Km1+P1), P2/(Km2+P2))"
```

### Pattern 4: Product of Saturations
**Use Case**: Sequential binding (ordered bi-bi)

```python
rate_function = "Vmax * (P1/(Km1+P1)) * (P2/(Km2+P2))"
```

### Pattern 5: Explicit Multi-Substrate Kinetics
**Use Case**: Full bi-substrate Michaelis-Menten

```python
rate_function = "Vmax * P1 * P2 / ((Km1*P2 + Km2*P1) + P1*P2 + Km1*Km2)"
```

---

## SBML Import Behavior

### Current Implementation (Single Substrate)

**File**: `src/shypn/data/pathway/pathway_converter.py:269-291`

```python
def _setup_michaelis_menten(self, transition, reaction, kinetic):
    """Setup Michaelis-Menten kinetics with rate_function."""
    
    # Find substrate place (first reactant)
    if reaction.reactants:
        substrate_species_id = reaction.reactants[0][0]  # First reactant only
        substrate_place = self.species_to_place.get(substrate_species_id)
        if substrate_place:
            substrate_place_ref = substrate_place.name
    
    # Build rate function
    rate_func = f"michaelis_menten({substrate_place_ref}, {vmax}, {km})"
    transition.properties['rate_function'] = rate_func
```

**Limitation**: Only uses **first reactant** as substrate, ignores additional reactants.

---

## Enhancement Options

### Option 1: Detect Multi-Substrate Reactions

```python
def _setup_michaelis_menten(self, transition, reaction, kinetic):
    """Setup Michaelis-Menten kinetics with rate_function."""
    
    vmax = kinetic.parameters.get("Vmax", 1.0)
    km = kinetic.parameters.get("Km", 1.0)
    
    if len(reaction.reactants) == 1:
        # Single substrate - standard MM
        substrate = self.species_to_place.get(reaction.reactants[0][0]).name
        rate_func = f"michaelis_menten({substrate}, {vmax}, {km})"
    
    elif len(reaction.reactants) == 2:
        # Two substrates - product kinetics (common assumption)
        s1 = self.species_to_place.get(reaction.reactants[0][0]).name
        s2 = self.species_to_place.get(reaction.reactants[1][0]).name
        rate_func = f"michaelis_menten({s1} * {s2}, {vmax}, {km})"
        self.logger.info(f"    Using product kinetics for bi-substrate reaction")
    
    else:
        # 3+ substrates - use first only, log warning
        substrate = self.species_to_place.get(reaction.reactants[0][0]).name
        rate_func = f"michaelis_menten({substrate}, {vmax}, {km})"
        self.logger.warning(f"    Multi-substrate reaction, using first substrate only")
    
    transition.properties['rate_function'] = rate_func
```

### Option 2: User-Configurable Multi-Substrate Mode

Add to SBML import dialog:
```
Multi-substrate Michaelis-Menten:
  [ ] Product (A*B)          ← Default for most metabolic reactions
  [ ] Sequential (MM(A)*MM(B)) ← For ordered mechanisms
  [ ] Primary only (A)        ← Ignore secondary substrates
```

### Option 3: Detect from SBML Kinetic Formula

If SBML has formula `Vmax * A * B / (Km + A*B)`, detect multi-substrate and preserve structure.

---

## Manual Editing

Users can **always manually edit** the rate function in the properties dialog:

```
Properties Dialog → Rate Function (Advanced) tab:

┌─────────────────────────────────────────┐
│ Rate Function Expression:               │
│                                          │
│ michaelis_menten(P1 * P2, 10.0, 5.0)   │ ← Edit to combine substrates
│                                          │
│ Available places: P1, P2, P3            │
│ Available functions: michaelis_menten,  │
│   competitive_inhibition, hill_equation │
└─────────────────────────────────────────┘
```

---

## Real-World Examples

### Example 1: Hexokinase (Two Substrates)

```
Reaction: Glucose + ATP → Glucose-6-P + ADP

Network:
  P1 (Glucose) ──┐
                 ├─→ T1 → P3 (Glucose-6-P)
  P2 (ATP) ──────┘       └─→ P4 (ADP)

Rate Function Options:

# Option A: Product kinetics (common for random bi-bi)
rate_function = "michaelis_menten(P1 * P2, 175, 0.1)"

# Option B: Sequential (ordered bi-bi)
rate_function = "michaelis_menten(P1, 175, 0.1) * (P2 / (P2 + 0.4))"

# Option C: Full bi-substrate
rate_function = "175 * P1 * P2 / ((0.1*P2 + 0.4*P1) + P1*P2 + 0.04)"
```

### Example 2: Lactate Dehydrogenase (With Cofactor)

```
Reaction: Pyruvate + NADH + H+ → Lactate + NAD+

Network:
  P1 (Pyruvate) ──┐
                  ├─→ T1 → P3 (Lactate)
  P2 (NADH) ──────┘       └─→ P4 (NAD+)

Rate Function:
# NADH is cofactor, often saturated
rate_function = "michaelis_menten(P1, 200, 0.2) * (P2 / (P2 + 0.05))"

# Or if NADH can be limiting:
rate_function = "200 * min(P1/(0.2+P1), P2/(0.05+P2))"
```

### Example 3: Phosphofructokinase (Allosteric Regulation)

```
Reaction: Fructose-6-P + ATP → Fructose-1,6-BP + ADP
Regulation: Activated by AMP, Inhibited by ATP

Network:
  P1 (Fructose-6-P) ──┐
  P2 (ATP) ───────────┤
                      ├─→ T1 → P3 (Fructose-1,6-BP)
  P3 (AMP) ───────────┘       └─→ P4 (ADP)

Rate Function:
# Cooperative substrate binding + allosteric regulation
rate_function = """
hill_equation(P1, 100, 0.1, 4) *     # Substrate cooperativity (n=4)
(P2 / (P2 + 0.5)) *                   # ATP as substrate
(1 + 2*P3) /                          # AMP activation
(1 + 0.5*P2)                          # ATP inhibition
"""
```

---

## Summary

### How It Works

1. ✅ **All places available**: Every place's tokens accessible as `P{id}` in rate expressions
2. ✅ **Flexible composition**: Can reference multiple places in any mathematical expression
3. ✅ **Function catalog**: Use `michaelis_menten()`, `competitive_inhibition()`, etc.
4. ✅ **User editable**: Properties dialog allows full customization

### Current SBML Import

- Uses **first reactant only** as substrate
- Works correctly for single-substrate enzymes
- May need enhancement for multi-substrate reactions

### Recommendations

**For Users**:
- Single substrate reactions: Import handles automatically ✅
- Multi-substrate reactions: Edit rate function after import to combine substrates

**For Developers**:
- Consider enhancement to detect and handle bi-substrate reactions
- Add configuration option for multi-substrate kinetics mode
- Document patterns for common biochemical mechanisms

---

## See Also

- `src/shypn/engine/function_catalog.py` - Available kinetic functions
- `src/shypn/engine/continuous_behavior.py` - Rate function evaluation
- `doc/simulate/SBML_KINETIC_LAW_ENHANCEMENTS.md` - Import enhancements overview
