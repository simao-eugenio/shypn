# CRITICAL: Threshold Supersedes Weight

## Key Rule

**When `arc.threshold` is set, it SUPERSEDES `arc.weight` for enablement checking!**

## The Three Cases

### Case 1: Only Weight (Traditional Petri Nets)

```python
arc = InhibitorArc(source=place, target=transition, weight=5)
arc.threshold = None  # Not set
```

**Result:**
- ✅ Enablement check: `place.tokens >= 5` (uses weight)
- ✅ Token consumption: `5` tokens (uses weight)
- Weight serves **dual purpose**

---

### Case 2: Only Threshold (Supersedes Default Weight=1!)

```python
arc = InhibitorArc(source=place, target=transition)  # weight=1 by default
arc.threshold = "P1.tokens * 0.3"
```

**Result:**
- ✅ Enablement check: `place.tokens >= (P1.tokens * 0.3)` ← **NOT >= 1 !!!**
- ✅ Token consumption: `1` token (uses weight)
- Threshold **OVERRIDES** the default weight=1 for enablement
- Weight only used for consumption

**Common Mistake:**
```python
# WRONG assumption:
# "threshold will be added to weight=1"
# NO! Threshold REPLACES weight for enablement!

# If P1.tokens = 100:
# threshold = 30 (not 1!)
# Transition enabled when: tokens >= 30 (not >= 1!)
```

---

### Case 3: Both Weight and Threshold (Threshold Supersedes!)

```python
arc = InhibitorArc(source=place, target=transition, weight=10)
arc.threshold = "P1.tokens * 0.5"
```

**Result:**
- ✅ Enablement check: `place.tokens >= (P1.tokens * 0.5)` ← **NOT >= 10 !!!**
- ✅ Token consumption: `10` tokens (uses weight)
- Threshold **SUPERSEDES** weight=10 for enablement
- Weight only used for consumption
- **Separates enablement logic from consumption amount**

**Example:**
```python
# If P1.tokens = 100:
# threshold = 50 (not 10!)
# Transition enabled when: tokens >= 50
# But consumes: 10 tokens per firing
# 
# This allows: "Need 50 in reserve, but only transfer 10 at a time"
```

## Visual Summary

```
┌─────────────────────────────────────────────────────────────┐
│                   ARC THRESHOLD BEHAVIOR                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Property Set          │  Enablement Uses  │  Consumption  │
│  ─────────────────────────────────────────────────────────  │
│  weight only           │  weight           │  weight       │
│  threshold only        │  threshold ⚠️     │  weight (1)   │
│  both                  │  threshold ⚠️     │  weight       │
│                                                             │
│  ⚠️  = SUPERSEDES weight!                                   │
└─────────────────────────────────────────────────────────────┘
```

## Why This Design?

### 1. **Backward Compatibility**
Existing models using only `weight` work unchanged.

### 2. **Separation of Concerns**
- **Enablement**: "When should this transition fire?"
- **Consumption**: "How much should be transferred?"
- These can be different!

### 3. **Living Systems Modeling**
Natural pattern: "Maintain large reserves but transfer small amounts"

```python
# Example: Blood system
arc.weight = 1           # Transfer 1 unit at a time (gentle)
arc.threshold = "Blood.tokens * 0.7"  # But need 70% reserve (safe)
```

### 4. **Flexibility Without Complexity**
Simple cases stay simple, complex cases are possible.

## Real-World Examples

### Example 1: Energy Distribution
```python
battery = Place(tokens=100)
distribute = Transition()
arc = InhibitorArc(battery, distribute, weight=5)
arc.threshold = "Battery.tokens * 0.2"  # Keep 20% reserve

# At 100 tokens:
#   threshold = 20 (NOT 5!)
#   Can fire when >= 20
#   Consumes 5 per firing
#   Result: Can fire 16 times (100-20)/5
```

### Example 2: Food Sharing
```python
storage = Place(tokens=50)
share = Transition()
arc = InhibitorArc(storage, share, weight=1)
arc.threshold = "10"  # Fixed reserve (string expression)

# threshold = 10 (SUPERSEDES weight=1!)
# Can fire when >= 10
# Consumes 1 per firing
# Result: Can fire 40 times (50-10)/1
```

### Example 3: Adaptive Protection
```python
resource = Place(tokens=200)
consume = Transition()
arc = InhibitorArc(resource, consume, weight=3)
arc.threshold = "Resource.tokens * 0.5"  # 50% reserve

# At 200 tokens:
#   threshold = 100 (NOT 3!)
#   Can fire when >= 100
#   Consumes 3 per firing
#   Result: Can fire 33 times (200-100)/3
```

## Common Pitfalls

### ❌ Pitfall 1: Assuming Threshold Adds to Weight
```python
arc.weight = 5
arc.threshold = "10"

# WRONG: "Need 5 + 10 = 15 tokens"
# RIGHT: "Need 10 tokens (threshold REPLACES weight for enablement)"
```

### ❌ Pitfall 2: Forgetting Default Weight=1
```python
arc = InhibitorArc(p, t)  # weight=1 by default!
arc.threshold = "P1.tokens * 0.3"

# WRONG: "threshold is added to nothing"
# RIGHT: "threshold SUPERSEDES weight=1 (which still exists for consumption)"
```

### ❌ Pitfall 3: Expecting Threshold to Affect Consumption
```python
arc.weight = 10
arc.threshold = "5"

# WRONG: "Consumes 5 tokens"
# RIGHT: "Consumes 10 tokens (weight), enabled at threshold 5"
```

## Testing Checklist

- [ ] Test Case 1: Only weight → uses weight for both
- [ ] Test Case 2: Only threshold → threshold for enablement, weight=1 for consumption
- [ ] Test Case 3: Both → threshold for enablement, weight for consumption
- [ ] Test Case 4: Verify threshold SUPERSEDES weight (not adds to it)
- [ ] Test Case 5: Verify consumption always uses weight (never threshold)

## Summary

**Remember:**
1. `threshold` **SUPERSEDES** `weight` for enablement (doesn't add to it!)
2. `weight` is **ALWAYS** used for consumption
3. Default `weight=1` still exists when only threshold is set
4. This enables: "high threshold + low consumption" patterns
5. Perfect for living systems: "maintain reserves, transfer slowly"

---

**Golden Rule:** 
```
if arc.threshold is not None:
    enablement_uses = arc.threshold  # SUPERSEDES!
else:
    enablement_uses = arc.weight     # Fallback
    
consumption_uses = arc.weight  # ALWAYS
```
