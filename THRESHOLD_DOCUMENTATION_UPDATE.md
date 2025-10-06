# Documentation Update Summary - Threshold Supersedes Weight

## What Changed

Updated all documentation to clarify the **critical behavior**: When `arc.threshold` is set, it **SUPERSEDES** (overrides/replaces) `arc.weight` for enablement checking, NOT adds to it!

## Files Updated

### 1. ✅ `ARC_THRESHOLD_SYSTEM.md`
- Added "Critical Behavior" section with comparison table
- Updated all examples to show superseding behavior
- Clarified: threshold overrides default `weight=1`
- Added "Why This Design?" rationale

### 2. ✅ `INHIBITOR_ARC_SIMULATION_LOGIC.md`
- Updated flexible threshold section
- Emphasized superseding behavior
- Updated adaptive cooperation example
- Clarified consumption vs. enablement

### 3. ✅ `INHIBITOR_ARC_IMPLEMENTATION_COMPLETE.md`
- Updated advanced thresholds section
- Added examples showing superseding
- Highlighted design benefits

### 4. ✅ `THRESHOLD_SUPERSEDES_WEIGHT.md` (NEW!)
- Comprehensive guide on superseding behavior
- Visual summary table
- Three cases explained in detail
- Common pitfalls section
- Real-world examples
- Testing checklist

## Key Concepts Now Documented

### The Rule
```python
if arc.threshold is not None:
    enablement_check = arc.threshold  # SUPERSEDES weight!
else:
    enablement_check = arc.weight     # Fallback

consumption = arc.weight  # ALWAYS uses weight
```

### The Three Cases

| Case | Configuration | Enablement | Consumption |
|------|--------------|------------|-------------|
| 1 | `weight=5`, `threshold=None` | `>= 5` | `5` |
| 2 | `weight=1` (default), `threshold="P1*0.3"` | `>= P1*0.3` **NOT >= 1!** | `1` |
| 3 | `weight=10`, `threshold="P1*0.5"` | `>= P1*0.5` **NOT >= 10!** | `10` |

### Why This Matters

1. **Supersedes default `weight=1`**: When only threshold is set, it completely replaces the default weight for enablement
2. **Separation of concerns**: Different logic for "when to fire" vs "how much to transfer"
3. **Living systems**: Natural pattern of "high reserve requirement + small transfers"
4. **Flexibility**: Can combine any threshold with any consumption amount

### Common Mistake Addressed

**WRONG Assumption:**
```python
arc.weight = 5
arc.threshold = "10"
# "Need 5 + 10 = 15 tokens"  ❌ NO!
```

**CORRECT:**
```python
arc.weight = 5
arc.threshold = "10"
# Enable when: >= 10 (threshold SUPERSEDES!)
# Consume: 5 (weight)
```

## Visual Summary Added

```
┌─────────────────────────────────────────────────────────────┐
│  Property Set          │  Enablement Uses  │  Consumption  │
├────────────────────────┼───────────────────┼───────────────┤
│  weight only           │  weight           │  weight       │
│  threshold only        │  threshold ⚠️     │  weight (1)   │
│  both                  │  threshold ⚠️     │  weight       │
│                                                             │
│  ⚠️  = SUPERSEDES weight!                                   │
└─────────────────────────────────────────────────────────────┘
```

## Examples Added

### Energy Distribution
```python
arc.weight = 5
arc.threshold = "Battery.tokens * 0.2"
# At 100 tokens: enabled at >= 20 (NOT >= 5!), consumes 5
```

### Food Sharing  
```python
arc.weight = 1
arc.threshold = "10"
# Enabled at >= 10 (SUPERSEDES weight=1!), consumes 1
```

### Adaptive Protection
```python
arc.weight = 3
arc.threshold = "Resource.tokens * 0.5"
# At 200 tokens: enabled at >= 100 (NOT >= 3!), consumes 3
```

## Documentation Now Covers

✅ The superseding/override behavior clearly stated
✅ Three distinct cases explained
✅ Common pitfalls and mistakes
✅ Real-world examples with calculations
✅ Visual diagrams and tables
✅ Design rationale
✅ Testing checklist
✅ Backward compatibility explanation

## Next Steps (Implementation)

When implementing the threshold evaluator:

```python
def _check_enablement_manual(self) -> bool:
    for arc in self.get_input_arcs():
        # Determine effective threshold
        if arc.threshold is not None:
            # SUPERSEDES weight!
            effective_threshold = evaluate_threshold(arc.threshold, context)
        else:
            # Fallback to weight
            effective_threshold = arc.weight
        
        # Check enablement
        if source_place.tokens < effective_threshold:
            return False
    
    return True

def fire(self):
    for arc in input_arcs:
        # ALWAYS use weight for consumption (never threshold!)
        arc.source.remove_tokens(arc.weight)
```

## Summary

All documentation now clearly states that `threshold` **SUPERSEDES** `weight` for enablement checking when specified. This critical behavior is explained with:
- Multiple examples
- Visual diagrams
- Common pitfall warnings
- Real-world scenarios
- Design rationale
- Implementation guidance

The key message: **threshold doesn't add to weight, it replaces it for enablement!**
