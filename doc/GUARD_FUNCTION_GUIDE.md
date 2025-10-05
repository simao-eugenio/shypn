# Guard Function Implementation Guide

## Overview

Guards are **enable/disable conditions** for transitions. They determine whether a transition can fire, independent of token availability. Guards are evaluated **before** checking structural enablement (tokens).

## Guard Types Supported

### 1. **Boolean Guard**
Direct boolean value:
```python
True   # Always enabled (explicit)
False  # Always disabled
```

**Use case**: Manually enable/disable transitions during development or testing.

---

### 2. **Numeric Threshold Guard**
Numeric value treated as threshold (> 0 passes):
```python
1      # Passes (> 0)
0.5    # Passes (> 0)
0      # Fails (not > 0)
-1     # Fails (not > 0)
```

**Use case**: Simple on/off switching based on external configuration values.

---

### 3. **Expression Guard**
String expression evaluated with place tokens and time:
```python
# Token-based conditions
"P1 > 5"                    # Fire only when place P1 has more than 5 tokens
"P1 >= 2 and P2 > 0"        # Both conditions must be met
"P1 + P2 < 10"              # Sum constraint

# Time-based conditions
"t > 10"                    # Fire only after time 10
"t >= 5 and t <= 15"        # Time window

# Combined conditions
"P1 > 0 and t > 5"          # Token available AND time passed
"P1 / P2 > 0.5 if P2 > 0 else False"  # Ratio with safety check
```

**Use case**: Dynamic conditions that depend on current system state.

---

### 4. **Function-Based Guard**
Use mathematical functions from the function catalog:
```python
# Sigmoid threshold (smooth 0→1 transition)
"sigmoid(P1, 50, 10) > 0.5"  # Fire when P1 approaches 50 tokens

# Step function
"step(t, 10) > 0"            # Fire after time 10 (step function)

# Hill function (cooperative binding)
"hill(P1, 20, 4) > 0.8"      # Fire when P1 high with cooperativity

# ReLU (threshold with activation)
"relu(P1, 10) > 0"           # Fire only when P1 > 10
```

**Use case**: Biological or chemical reaction models with non-linear behaviors.

---

## How Guards Work

### Evaluation Order
```
1. Guard Evaluation
   ↓ (passes)
2. Structural Enablement Check (tokens)
   ↓ (sufficient)
3. Type-Specific Constraints (timing, etc.)
   ↓ (satisfied)
4. FIRE ✓
```

If guard **fails** at step 1, the transition is immediately disabled regardless of tokens.

### Evaluation Context
Guards are evaluated with:
- **Place tokens**: `P1`, `P2`, `P3`, ... (by place ID)
- **Current time**: `t`
- **Math functions**: `exp`, `log`, `sin`, `cos`, `sqrt`, etc.
- **Function catalog**: `sigmoid`, `hill`, `michaelis_menten`, `relu`, etc.

---

## Practical Examples

### Example 1: Resource Threshold
**Scenario**: Assembly line transition should only fire when buffer has > 20 items.

**Guard**: `P1 > 20`

**Explanation**: Even if structural tokens are available, the transition won't fire until place P1 exceeds 20 tokens.

---

### Example 2: Time Window
**Scenario**: Maintenance transition only allowed between t=100 and t=200.

**Guard**: `t >= 100 and t <= 200`

**Explanation**: Transition disabled outside the time window.

---

### Example 3: Ratio Constraint
**Scenario**: Reaction only proceeds when substrate concentration is at least 2× product concentration.

**Guard**: `P1 >= 2 * P2 if P2 > 0 else True`

**Explanation**: 
- If P2 (product) has tokens, check ratio constraint
- If P2 is empty, allow reaction to proceed

---

### Example 4: Sigmoid Activation
**Scenario**: Gene expression transition activates smoothly as transcription factor (TF) concentration increases.

**Guard**: `sigmoid(P1, 50, 10) > 0.5`

**Explanation**:
- `P1`: TF tokens
- `50`: Midpoint (50% activation at 50 tokens)
- `10`: Steepness
- Transition becomes enabled when sigmoid > 0.5 (~45-55 tokens)

---

### Example 5: Boolean Flag (Development)
**Scenario**: Temporarily disable a transition during debugging.

**Guard**: `False`

**Explanation**: Simple on/off switch, no computation needed.

---

## Persistence Behavior

### Storage Locations
Guards are stored in **two places** for different purposes:

1. **`transition.guard`**: Parsed value (boolean, number, or string)
   - Used for basic storage and display
   - May lose dynamic expression information

2. **`transition.properties['guard_function']`**: Original string expression
   - **Preferred location for evaluation**
   - Preserves exact expression text
   - Used by behavior classes during simulation

### Save/Load Flow
```
Dialog Entry → properties['guard_function'] (string)
            ↓
         transition.guard (parsed value)
            ↓
         File serialization (both saved)
            ↓
         File load (both restored)
            ↓
     Dialog Display (prefers properties['guard_function'])
            ↓
     Simulation Evaluation (uses properties['guard_function'])
```

**Key point**: The system now correctly saves and loads guard expressions, ensuring they persist across sessions.

---

## Implementation Details

### Behavior Class Integration
All transition behavior classes now check guards in their `can_fire()` method:

```python
def can_fire(self) -> Tuple[bool, str]:
    # 1. Check guard first
    guard_passes, guard_reason = self._evaluate_guard()
    if not guard_passes:
        return False, guard_reason  # ← Early return if guard fails
    
    # 2. Check tokens (structural enablement)
    # ...
    
    # 3. Check type-specific constraints
    # ...
    
    return True, "enabled"
```

### Guard Evaluation Method
Base class `TransitionBehavior` provides `_evaluate_guard()`:

```python
def _evaluate_guard(self) -> Tuple[bool, str]:
    # 1. Try properties['guard_function'] first (preferred)
    # 2. Fall back to transition.guard
    # 3. Handle None/empty → always passes
    # 4. Handle boolean → direct value
    # 5. Handle numeric → threshold (> 0)
    # 6. Handle string → safe eval with context
    # 7. Return (passes: bool, reason: str)
```

**Safety**: String expressions are evaluated with restricted namespace (no `__builtins__`), only math functions and place tokens available.

---

## Debugging Guards

### Check Guard Value
Look for these log messages:
```
[TransitionPropDialogLoader] Loading guard function: P1 > 5
[TransitionPropDialogLoader] Guard function stored: P1 > 5
[TransitionBehavior] Guard evaluation error: name 'P3' is not defined
```

### Common Issues

**Issue**: Guard always fails  
**Cause**: Typo in place name (e.g., `P3` doesn't exist)  
**Fix**: Check place IDs, use correct `P1`, `P2`, etc.

**Issue**: Guard expression not persisting  
**Cause**: Old file format without `properties` dict  
**Fix**: Re-save the file (now includes `properties['guard_function']`)

**Issue**: Transition never fires despite tokens  
**Cause**: Guard condition never satisfied  
**Fix**: Check guard expression logic, add debug prints

---

## Comparison: Guard vs Rate

| Aspect | Guard | Rate |
|--------|-------|------|
| **Purpose** | Enable/disable transition | Control firing speed/intensity |
| **Type** | Boolean/threshold/expression | Numeric/expression |
| **Evaluation** | Before token check | During firing |
| **Result** | Pass/fail (boolean) | Numeric value |
| **Use case** | Conditional logic | Dynamics/kinetics |

**Example Combined Use**:
```
Guard: "P1 > 10"              # Only enable when substrate high
Rate:  "sigmoid(P1, 50, 10)"  # Speed increases sigmoidally with substrate
```

This allows **qualitative control** (guard) separate from **quantitative control** (rate).

---

## Testing Guards

### Test Script Template
```python
# Create model with guard
transition.properties = {'guard_function': 'P1 > 5'}

# Test different token states
place.set_tokens(3)
can_fire, reason = behavior.can_fire()
assert not can_fire, "Should fail when P1=3"

place.set_tokens(10)
can_fire, reason = behavior.can_fire()
assert can_fire, "Should pass when P1=10"
```

### Interactive Testing
1. Open transition properties dialog
2. Enter guard expression
3. Click OK/Apply
4. Reopen dialog → verify guard is still there
5. Run simulation → check transition enablement
6. Save file, close app, reopen → verify persistence

---

## Migration Notes

**Old files** (before this fix):
- Guards stored only in `transition.guard`
- May lose expression information on parse
- Will still work but may not persist correctly

**New files** (after this fix):
- Guards stored in both locations
- Full persistence of expressions
- Backward compatible with old files

**Recommendation**: Re-save old files to get new persistence format.

---

## Summary

✅ **Boolean guards**: Direct true/false control  
✅ **Numeric guards**: Threshold-based (> 0)  
✅ **Expression guards**: Dynamic conditions with tokens/time  
✅ **Function guards**: Complex mathematical behaviors  
✅ **Full persistence**: Expressions saved to `properties['guard_function']`  
✅ **Integrated evaluation**: All behavior classes check guards  
✅ **Safe evaluation**: Restricted namespace prevents code injection  

**Guards give you precise control over WHEN transitions can fire, independent of token availability!** 🎯
