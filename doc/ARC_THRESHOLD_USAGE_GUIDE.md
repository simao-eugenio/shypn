# Arc Threshold Usage Guide

## Quick Answer

**NO - You do NOT need to set threshold on output arcs!**

Threshold is **ONLY used for INPUT arcs** (Place → Transition).  
Output arcs (Transition → Place) **ALWAYS use weight**, regardless of threshold setting.

---

## How It Works

### Input Arcs (Place → Transition)

**With threshold set:**
```
Place → Transition
Weight: 5
Threshold: 10

Behavior:
- Enablement check: Place must have ≥ 10 tokens
- Token consumption: Consumes 10 tokens (threshold supersedes weight)
```

**Without threshold (default):**
```
Place → Transition
Weight: 5
Threshold: None (or not set)

Behavior:
- Enablement check: Place must have ≥ 5 tokens
- Token consumption: Consumes 5 tokens (uses weight)
```

### Output Arcs (Transition → Place)

**Threshold is IGNORED on output arcs:**
```
Transition → Place
Weight: 5
Threshold: 10  ← IGNORED!

Behavior:
- Token production: Produces 5 tokens (always uses weight)
- Threshold value has NO effect
```

---

## Code Evidence

### Input Arc Processing
From `src/shypn/engine/simulation/controller.py` (lines 1333-1345):
```python
# Remove input tokens
for arc in self.model.arcs:
    if arc.target == transition:
        # Input arc (place → transition)
        place = arc.source
        
        # Get weight/threshold
        tokens_needed = getattr(arc, 'weight', 1)
        if hasattr(arc, 'threshold') and arc.threshold is not None:
            tokens_needed = arc.threshold  # ← Threshold supersedes weight
        
        # Consume tokens
        place.tokens -= tokens_needed
```

### Output Arc Processing
From same file (lines 1357-1362):
```python
# Add output tokens
for arc in self.model.arcs:
    if arc.source == transition:
        # Output arc (transition → place)
        place = arc.target
        tokens_produced = getattr(arc, 'weight', 1)  # ← ALWAYS uses weight
        place.tokens += tokens_produced
```

**Notice:** Output arc code has NO threshold check!

### All Behavior Types

This pattern is consistent across **ALL** transition types:
- **Immediate** (`immediate_behavior.py` line 187): `target_place.set_tokens(... + arc.weight)`
- **Continuous** (`continuous_behavior.py` line 398): `production = arc.weight * actual_flow`
- **Stochastic** (`stochastic_behavior.py` line 403): `amount = arc.weight * burst`
- **Timed** (uses same base logic)

---

## Common Scenarios

### Scenario 1: Basic Arc (Most Common)
```
Place P1 (50 tokens) → Transition T1 → Place P2 (0 tokens)

Input arc:  weight=5, threshold=None
Output arc: weight=5, threshold=None (ignored anyway)

Firing:
- Check: P1 ≥ 5? Yes (50 ≥ 5)
- Consume: P1 loses 5 tokens → P1 = 45
- Produce: P2 gains 5 tokens → P2 = 5

Result: Balanced (5 in = 5 out)
```

### Scenario 2: Input Threshold Higher Than Weight
```
Place P1 (50 tokens) → Transition T1 → Place P2 (0 tokens)

Input arc:  weight=5, threshold=10
Output arc: weight=5, threshold=None (ignored)

Firing:
- Check: P1 ≥ 10? Yes (50 ≥ 10)
- Consume: P1 loses 10 tokens → P1 = 40  ← Uses threshold!
- Produce: P2 gains 5 tokens → P2 = 5    ← Uses weight!

Result: UNBALANCED (10 in, 5 out)
```

**Use case:** Enzyme with high substrate requirement but low product yield

### Scenario 3: Input Threshold Lower Than Weight
```
Place P1 (50 tokens) → Transition T1 → Place P2 (0 tokens)

Input arc:  weight=10, threshold=5
Output arc: weight=10, threshold=None (ignored)

Firing:
- Check: P1 ≥ 5? Yes (50 ≥ 5)
- Consume: P1 loses 5 tokens → P1 = 45   ← Uses threshold!
- Produce: P2 gains 10 tokens → P2 = 10  ← Uses weight!

Result: UNBALANCED (5 in, 10 out) - Creates tokens!
```

**Use case:** Autocatalytic reaction or amplification

### Scenario 4: Multiple Input/Output Arcs
```
P1 (100) → T1 → P3 (0)
P2 (100) ↗    ↘ P4 (0)

Input arcs:
- P1→T1: weight=5, threshold=10
- P2→T1: weight=3, threshold=None

Output arcs:
- T1→P3: weight=5, threshold=999 (ignored!)
- T1→P4: weight=3, threshold=999 (ignored!)

Firing:
- Check: P1 ≥ 10? Yes. P2 ≥ 3? Yes.
- Consume: P1 loses 10 (threshold), P2 loses 3 (weight)
- Produce: P3 gains 5 (weight), P4 gains 3 (weight)

Result: 13 tokens in, 8 tokens out (unbalanced)
```

---

## When to Use Threshold

### Use Case 1: High Activation Threshold
**Biological:** Enzyme requires high substrate concentration to activate, but consumes less

```
Substrate (100) → Enzyme → Product (0)
Input: weight=2, threshold=50  ← "Need 50 to activate, consume 50"
Output: weight=2, threshold=N/A

Meaning: "Only fire when substrate ≥ 50, then consume 50 to produce 2"
```

### Use Case 2: Low Activation Threshold
**Biological:** Enzyme activates easily but consumes more (cooperative binding)

```
Substrate (100) → Enzyme → Product (0)
Input: weight=10, threshold=5  ← "Activate at 5, consume 5"
Output: weight=10, threshold=N/A

Meaning: "Fire when substrate ≥ 5, consume 5 to produce 10"
```

### Use Case 3: Michaelis-Menten Kinetics (Continuous)
For continuous transitions with rate functions:
```python
rate_function = "(Km * S) / (Km + S)"  # Michaelis-Menten

Input: weight=1, threshold=None
Output: weight=1, threshold=None

# Threshold not needed - rate function controls kinetics
# Weight still used: consumption = weight * rate * dt
```

### Use Case 4: Conditional Firing (Boolean Guard)
For conditional enablement, use **transition guards** instead:
```python
transition.guard = "P1 > 50"  # Only fire when P1 > 50

Input: weight=5, threshold=None  # Normal consumption
Output: weight=5, threshold=None  # Normal production
```

---

## Best Practices

### ✅ DO:
1. **Use threshold on input arcs** when you need consumption ≠ weight
2. **Use weight alone** for standard balanced reactions (most common)
3. **Use guards** for complex conditional firing
4. **Document why** you're using threshold (biological meaning)

### ❌ DON'T:
1. **DON'T set threshold on output arcs** - it does nothing!
2. **DON'T assume** threshold affects production - it only affects consumption
3. **DON'T use threshold** when you just need different weights:
   ```
   # Bad: Using threshold
   Input: weight=5, threshold=10
   Output: weight=5
   
   # Good: Just use different weights
   Input: weight=10
   Output: weight=5
   ```

### Design Rule:
**Threshold is for "activation energy" or "minimum substrate" concepts, NOT for stoichiometry!**

For stoichiometry (reaction ratios), use different **weights** on different arcs:
```
# Reaction: 2A + B → 3C

Place A → T: weight=2
Place B → T: weight=1
T → Place C: weight=3
```

---

## Summary Table

| Arc Direction | Attribute | Effect |
|---------------|-----------|--------|
| Place → Transition (input) | `weight` | Default consumption amount |
| Place → Transition (input) | `threshold` | **Supersedes weight** for consumption |
| Transition → Place (output) | `weight` | Production amount |
| Transition → Place (output) | `threshold` | **IGNORED** (no effect) |

---

## Answer to Your Question

> "When I put a threshold on an input arc I must to put the complement on the output?"

**No!** You should:

1. **Set threshold on input arc** if you need consumption ≠ weight
2. **Set weight on output arc** for production amount
3. **DON'T set threshold on output arc** - it has no effect

Example:
```
Input arc:  threshold=10 (consume 10 tokens)
Output arc: weight=5 (produce 5 tokens)
            threshold=??? ← Leave blank or None, it's ignored!
```

The "complement" concept doesn't apply because:
- Input uses: threshold (if set) OR weight (if not set)
- Output uses: weight (always)
- They're independent values

If you want balanced token flow, just make sure:
```
sum(input thresholds or weights) == sum(output weights)
```

But unbalanced flows are valid for modeling:
- Enzyme kinetics (high activation, low yield)
- Autocatalysis (amplification)
- Degradation (consumption without production)
