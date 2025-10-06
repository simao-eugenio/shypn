# Inhibitor Arc Simulation Logic - Living Systems Semantics

## Overview

**IMPORTANT**: SHYPN uses **"living systems" semantics** for inhibitor arcs, NOT the classical manufacturing/discrete event semantics. This reflects the cooperative nature of biological and organic systems where **no component should be subjected to starvation**.

Inhibitor arcs in SHYPN implement a **cooperation principle**: a place can only provide resources to a transition if it has **surplus above a threshold**, preventing the place from being depleted below a safe reserve level.

### Flexible Threshold System

Arc objects in SHYPN support multiple threshold specification methods:
1. **Simple Numeric** (via `weight` property): Fixed integer value (e.g., `weight=5`)
2. **Expression** (via `threshold` property): Dynamic formula (e.g., `"P1.tokens * 0.3"`)
3. **Function** (via `threshold` property): Complex logic (e.g., `{"type": "function", "formula": "..."}`)

This enables both simple cooperation models and sophisticated adaptive thresholds.

## SHYPN Living Systems Semantics

### Inhibitor Arc Behavior (SHYPN - Cooperation Model)
```
Place P1 ====○ [weight=5]====> Transition T1

Enabling condition: P1.tokens >= 5  (place has SURPLUS)
Effect on firing: Consumes tokens from P1 (like normal arc)
Protection: T1 disabled when P1.tokens < 5 (prevents starvation)
```

**Key Principle**: "Only give when you have enough to spare - protect your reserves"

### Comparison with Classical Semantics

| Aspect | Classical (Manufacturing) | SHYPN (Living Systems) |
|--------|--------------------------|------------------------|
| **Philosophy** | Zero-testing, overflow prevention | Cooperation, starvation prevention |
| **Enabling** | `tokens < weight` → ENABLED | `tokens >= weight` → ENABLED |
| **Logic** | "Enable when place is LOW" | "Enable when place has SURPLUS" |
| **Token Transfer** | NO consumption | YES - consumes like normal arc |
| **Use Case** | Mutex, exclusion, deadlock prevention | Resource management, cooperation, sustainability |
| **Semantics** | "Place must be (nearly) empty" | "Place must have reserves" |

## Petri Net Semantics - SHYPN Model

### Normal Arc Behavior (unchanged)
```
Place P1 ----[weight=2]----> Transition T1

Enabling condition: P1.tokens >= 2
Effect on firing: Consumes 2 tokens from P1
```

### Inhibitor Arc Behavior (SHYPN Living Systems)
```
Place P1 ====○ [weight=5]====> Transition T1

Enabling condition: P1.tokens >= 5  (SURPLUS requirement)
Effect on firing: Consumes tokens from P1 (like normal arc)
Starvation protection: Transition stops when P1.tokens < 5
```

## Example Scenario: Cooperation System

```
Producer → P1 (tokens=10) ====○[threshold=5]====> T1 → Consumer → P2

Step 1: 10 >= 5 → T1 ENABLED → fires (weight=1) → P1 = 9
Step 2:  9 >= 5 → T1 ENABLED → fires (weight=1) → P1 = 8
Step 3:  8 >= 5 → T1 ENABLED → fires (weight=1) → P1 = 7
Step 4:  7 >= 5 → T1 ENABLED → fires (weight=1) → P1 = 6
Step 5:  6 >= 5 → T1 ENABLED → fires (weight=1) → P1 = 5
Step 6:  5 >= 5 → T1 ENABLED → fires (weight=1) → P1 = 4
Step 7:  4 < 5  → T1 DISABLED (P1 protected from starvation!)
```

**Result**: P1 maintains a reserve of 4 tokens. It won't give more until it has surplus again.

## Organic Life Analogy

Think of this like organisms sharing resources:

```
Food Storage (P1) ====○[survival_reserve=100]====> Sharing (T1) → Community (P2)

- If storage >= 100: Share food (transition enabled)
- If storage < 100: Stop sharing (protect survival reserve)
```

No one starves because each component maintains its minimum viable level.

## Current Implementation Status

### ✅ Completed
- **Arc Classes**: `InhibitorArc` and `CurvedInhibitorArc` classes implemented
- **Visual Rendering**: Hollow circle marker at target end
- **Direction Validation**: Only allows Place→Transition connections
- **Context Menu**: Can convert normal ↔ inhibitor
- **Arc Type Property**: `arc.arc_type` returns "normal" or "inhibitor"
- **Persistence**: Saves/loads as `type: "inhibitor_arc"` in .shy files

### ❌ Missing - Simulation Integration

The **inhibitor logic is NOT yet integrated** into the simulation engine. Currently:
- Inhibitor arcs are **skipped** in enablement checks (see `transition_behavior.py:146`)
- They are **treated as normal arcs** in token counting
- Transitions fire **incorrectly** when inhibitor conditions are violated

## Where to Integrate

### 1. Transition Behavior Base Class (`src/shypn/engine/transition_behavior.py`)

**File**: `src/shypn/engine/transition_behavior.py`  
**Method**: `_check_enablement_manual()` (lines 137-161)

**Current Code** (INCORRECT):
```python
def _check_enablement_manual(self) -> bool:
    """Manual enablement check (fallback if model doesn't provide method)."""
    input_arcs = self.get_input_arcs()
    
    for arc in input_arcs:
        # Skip inhibitor arcs
        kind = getattr(arc, 'kind', getattr(arc, 'properties', {}).get('kind', 'normal'))
        if kind != 'normal':
            continue  # ❌ WRONG: Just skips them!
        
        # Check sufficient tokens
        source_place = arc.source
        if source_place.tokens < arc.weight:
            return False
    
    return True
```

**Correct Logic** (SHYPN LIVING SYSTEMS SEMANTICS):
```python
def _check_enablement_manual(self) -> bool:
    """Manual enablement check with inhibitor arc support (living systems semantics).
    
    SHYPN uses cooperation semantics for inhibitor arcs:
    - Normal arc: source.tokens >= weight (standard enabling)
    - Inhibitor arc: source.tokens >= weight (surplus required - cooperation)
    
    Both consume tokens, but inhibitor prevents starvation by requiring surplus.
    """
    from shypn.netobjs.inhibitor_arc import InhibitorArc
    
    input_arcs = self.get_input_arcs()
    
    for arc in input_arcs:
        source_place = arc.source
        if source_place is None:
            return False
        
        # LIVING SYSTEMS SEMANTICS:
        # Both normal and inhibitor arcs check tokens >= weight
        # The difference is semantic (normal=need, inhibitor=surplus/cooperation)
        if source_place.tokens < arc.weight:
            return False  # Insufficient tokens (normal) or no surplus (inhibitor)
    
    return True
```

### 2. Token Transfer Logic

**CRITICAL**: In SHYPN living systems semantics, inhibitor arcs **DO consume tokens** (like normal arcs). The difference is in the **enabling semantics** (cooperation principle), not in token transfer.

**File**: Each behavior class (`immediate_behavior.py`, `timed_behavior.py`, etc.)  
**Method**: `fire()` method

**Current Logic** (needs no change for input arcs):
```python
def fire(self, input_arcs, output_arcs):
    # Consume tokens from ALL input places (including inhibitor arcs)
    for arc in input_arcs:
        arc.source.remove_tokens(arc.weight)  # ✓ CORRECT for SHYPN!
    
    # Produce tokens to output places
    for arc in output_arcs:
        arc.target.add_tokens(arc.weight)
```

**Important Note**: Since inhibitor arcs are **Place→Transition only**, they should never appear in `output_arcs`. But for safety, we should still skip them:

## Implementation Plan

### Phase 1: Fix Enablement Checking ✅ PRIORITY

**File**: `src/shypn/engine/transition_behavior.py`

1. Import `InhibitorArc` at the top
2. Modify `_check_enablement_manual()` to check inhibitor condition
3. Update docstring to explain inhibitor logic
4. Add test cases

**Code Changes**:
```python
# At top of file
from shypn.netobjs.inhibitor_arc import InhibitorArc

# In _check_enablement_manual() method
for arc in input_arcs:
    source_place = arc.source
    if source_place is None:
        return False
    
    if isinstance(arc, InhibitorArc):
        # Inhibitor: transition enabled only if place has FEWER than weight tokens
        if source_place.tokens >= arc.weight:
            return False  # Transition is inhibited
    else:
        # Normal: transition enabled only if place has at least weight tokens
        if source_place.tokens < arc.weight:
            return False  # Insufficient tokens
```

### Phase 2: Fix Token Transfer

**Files**: 
- `src/shypn/engine/immediate_behavior.py`
- `src/shypn/engine/timed_behavior.py`
- `src/shypn/engine/stochastic_behavior.py`
- `src/shypn/engine/continuous_behavior.py`

1. Import `InhibitorArc` in each behavior file
2. Modify `fire()` method to skip inhibitor arcs in token consumption
3. Modify `fire()` method to skip inhibitor arcs in token production (safety)
4. Update firing details/logs to note inhibitor arcs

**Code Pattern** (apply to all 4 behavior files):
```python
from shypn.netobjs.inhibitor_arc import InhibitorArc

def fire(self, input_arcs, output_arcs):
    consumed = {}
    produced = {}
    
    # Consume from input places (skip inhibitors)
    for arc in input_arcs:
        if not isinstance(arc, InhibitorArc):
            arc.source.remove_tokens(arc.weight)
            consumed[arc.source.id] = arc.weight
    
    # Produce to output places (skip inhibitors)
    for arc in output_arcs:
        if not isinstance(arc, InhibitorArc):
            arc.target.add_tokens(arc.weight)
            produced[arc.target.id] = arc.weight
    
    return True, {
        'consumed': consumed,
        'produced': produced,
        'transition_id': self.transition.id
    }
```

### Phase 3: Testing

**Test Scenarios**:

1. **Basic Inhibition**
   ```
   P1 (tokens=0) ===○===> T1
   Expected: T1 enabled (place empty)
   ```

2. **Inhibition Active**
   ```
   P1 (tokens=5) ===○[weight=3]===> T1
   Expected: T1 disabled (tokens >= weight)
   ```

3. **Inhibition Boundary**
   ```
   P1 (tokens=2) ===○[weight=3]===> T1
   Expected: T1 enabled (tokens < weight)
   ```

4. **Mixed Arcs**
   ```
   P1 (tokens=5) ----[weight=2]----> T1
   P2 (tokens=3) ====○[weight=5]====> T1
   Expected: T1 enabled (P1 sufficient, P2 not inhibiting)
   ```

5. **No Token Consumption**
   ```
   P1 (tokens=0) ===○===> T1 ----> P2
   Fire T1
   Expected: P1 still has 0 tokens (no consumption from inhibitor)
   ```

## Important Notes

### 1. Token Transfer in Living Systems Semantics
In SHYPN, inhibitor arcs **DO consume tokens** (unlike classical semantics). They implement cooperation where resources are shared when surplus exists.

### 2. Direction Restriction
Inhibitor arcs **MUST** be Place→Transition. This is enforced in:
- `InhibitorArc._validate_connection()` - raises ValueError
- `arc_transform.convert_to_inhibitor()` - raises ValueError

### 3. Flexible Threshold Specification

SHYPN supports three methods for specifying thresholds:

#### Method 1: Simple Numeric (weight property)
```python
arc.weight = 5  # Fixed threshold
# Transition enabled when: source.tokens >= 5
# Token consumption: 5 per firing
```

#### Method 2: Expression (threshold property)
```python
arc.weight = 1  # Used for consumption
arc.threshold = "P1.tokens * 0.3"  # SUPERSEDES weight=1 for enablement!
# Transition enabled when: source.tokens >= (P1.tokens * 0.3)
# Token consumption: 1 per firing (weight)
# Evaluated at runtime during enablement check
```

#### Method 3: Function/Formula (threshold property)
```python
arc.weight = 1  # Used for consumption
arc.threshold = {
    "type": "function",
    "formula": "lambda P1, P2: (P1.tokens + P2.tokens) / 2"
}
# SUPERSEDES weight=1 for enablement!
# Complex logic with multiple dependencies
```

#### Threshold Evaluation Priority

**CRITICAL**: When `threshold` is set, it **SUPERSEDES** `weight` for enablement checking!

1. If `arc.threshold` is set → evaluate expression/function for enablement
2. Otherwise → use `arc.weight` (simple numeric)
3. `arc.weight` is ALWAYS used for token consumption amount

This enables:
- **Simple models**: Fixed thresholds (`weight=5`)
- **Adaptive systems**: Dynamic thresholds that **supersede** default `weight=1` (`threshold="P1.tokens * 0.5"`)
- **Complex cooperation**: Multi-factor formulas that **override** simple weight

#### Example: Adaptive Cooperation
```python
# Energy sharing system with adaptive reserve requirement
energy_storage = Place(id=1, name="Energy", tokens=100)
consumer = Transition(id=1, name="ShareEnergy", behavior="immediate")

# Threshold adapts: require 50% reserve when system is stressed
arc = InhibitorArc(
    source=energy_storage,
    target=consumer,
    weight=1,  # Consume 1 unit per firing
)
arc.threshold = "P1.tokens * 0.5"  # SUPERSEDES weight=1 for enablement!

# Result: As energy depletes, threshold OVERRIDES the weight=1:
# tokens=100 → threshold=50 (not 1!) → can share 50 units
# tokens=60  → threshold=30 (not 1!) → can share 30 units  
# tokens=30  → threshold=15 (not 1!) → can share 15 units
# 
# Note: Consumption is always 1 (weight), but enablement uses threshold!
```
- Arc properties dialog - should validate before conversion

### 3. Weight Semantics
For inhibitor arcs, weight means:
- **Threshold**: Place must have **strictly less than** weight tokens
- **Zero-testing**: Use weight=1 to test if place is empty
- **General**: Use weight=N to test if place has fewer than N tokens

### 4. Continuous Transitions
For continuous transitions, inhibitor arcs should:
- Enable flow when `place.tokens < weight`
- Disable flow when `place.tokens >= weight`
- Still no token consumption from the inhibitor arc itself

## Visual Indicators (Already Implemented)

- **Hollow Circle**: Drawn at target (transition) end
- **Same Line Style**: Uses same color/width as normal arcs
- **Context Menu**: Shows "Convert to Normal Arc" option
- **Properties Dialog**: Shows arc type as "Inhibitor"

## Summary

**Current Status**: Inhibitor arcs exist as visual/structural elements but have **NO simulation effect**.

**Required Changes**:
1. ✅ Fix enablement check to respect inhibitor condition (reversed logic)
2. ✅ Fix token transfer to skip inhibitor arcs (no consumption/production)
3. ✅ Test all transition types (immediate, timed, stochastic, continuous)

**Impact**: Small, localized changes to 5 files:
- 1 base class (`transition_behavior.py`)
- 4 behavior classes (one per transition type)

**Complexity**: Low - just need to check `isinstance(arc, InhibitorArc)` and apply reversed logic.
