# Arc Threshold Investigation

## Summary

**YES, threshold DOES supersede weight when present.**

## Current Implementation

### Arc Attribute
- All arcs have a `threshold` attribute (defined in `arc.py` line 53)
- Default value: `None`
- Can be: `None`, numeric value, dict, or expression

### Usage in Simulation

In `src/shypn/engine/simulation/controller.py`, there are **two locations** where threshold supersedes weight:

#### Location 1: Lines 1207-1210 (Token Check)
```python
# Get weight/threshold
tokens_needed = getattr(arc, 'weight', 1)
if hasattr(arc, 'threshold') and arc.threshold is not None:
    tokens_needed = arc.threshold

# Check sufficient tokens
if place.tokens < tokens_needed:
    return False  # Not enough tokens
```

#### Location 2: Lines 1333-1339 (Token Consumption)
```python
# Get weight/threshold
tokens_needed = getattr(arc, 'weight', 1)
if hasattr(arc, 'threshold') and arc.threshold is not None:
    tokens_needed = arc.threshold

# Safety check (should not fail after validation)
if place.tokens < tokens_needed:
    raise RuntimeError(...)

place.tokens -= tokens_needed
```

### Key Behavior

1. **Default:** Uses `arc.weight` for token consumption/production
2. **Override:** If `arc.threshold` is not `None`, uses `threshold` instead
3. **Token Check:** Threshold controls how many tokens are required from input places
4. **Token Consumption:** Threshold controls how many tokens are consumed on firing

### Important Notes

⚠️ **CRITICAL ISSUE:** Threshold only affects **INPUT arcs** (token consumption)

Looking at line 1355-1359:
```python
# Add output tokens
for arc in self.model.arcs:
    if arc.source == transition:
        # Output arc (transition → place)
        place = arc.target
        tokens_produced = getattr(arc, 'weight', 1)  # ← ALWAYS uses weight!
        place.tokens += tokens_produced
```

**Output arcs ALWAYS use `weight`, never `threshold`!**

This creates an asymmetry:
- Input arc with threshold=10, weight=5: Consumes 10 tokens
- Output arc with threshold=10, weight=5: Produces 5 tokens

### Persistence Issue

**✅ FIXED: Threshold is now saved to file!**

**Previous behavior:** Threshold was NOT saved in `arc.py` `to_dict()` method

**Fixed in commit:** Added threshold to serialization in `arc.py`:
```python
data.update({
    "object_type": "arc",
    "arc_type": "normal",
    "source_id": self.source.id,
    "source_type": "place" if isinstance(self.source, Place) else "transition",
    "target_id": self.target.id,
    "target_type": "place" if isinstance(self.target, Place) else "transition",
    "weight": self.weight,
    "threshold": self.threshold,  # ← NOW SAVED!
    "color": list(self.color),
    "width": self.width,
    "control_points": self.control_points
})
```

And restored in `from_dict()`:
```python
if "threshold" in data:
    arc.threshold = data["threshold"]  # ← NOW RESTORED!
```

**Result:** Threshold values now persist across save/load cycles! ✅

**Tested:** All arc types (Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc) inherit the fix via `super().to_dict()`

### UI Support

Arc properties dialog (`arc_prop_dialog_loader.py`) DOES support threshold:
- Line 143-146: Loads threshold into UI
- Line 305-311: Saves threshold from UI to arc object
- Has `_format_threshold_for_display()` method
- Has `_parse_threshold()` method

So users CAN set threshold values via the dialog, but they won't persist across save/load.

## Problems Identified

### ✅ Problem 1: FIXED - Threshold Not Persisted
**Status:** RESOLVED
- ✅ Threshold now saved in `to_dict()`
- ✅ Threshold now restored in `from_dict()`
- ✅ Works for all arc types (Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc)
- ✅ Tested with numeric values and None
- **Impact:** User data now preserved across save/load

### Problem 2: Asymmetric Behavior
**Status:** OPEN (by design, needs documentation)
- **Input arcs:** Use threshold if present (supersedes weight)
- **Output arcs:** Always use weight (ignores threshold)
- **Impact:** Can create token imbalances

### Problem 3: No Validation
**Status:** OPEN
- No check that threshold makes sense for arc direction
- No warning that output arcs ignore threshold
- No validation that threshold >= weight or vice versa

### Problem 4: Rendering
**Status:** OPEN
- Arc label shows `weight` (line 449)
- Even if `threshold` is set and active
- **Impact:** Visual confusion - displayed value doesn't match behavior

## Recommendations

### Option 1: Fully Implement Threshold (Symmetric)
1. Use threshold for BOTH input and output arcs
2. Save threshold in `to_dict()` / restore in `from_dict()`
3. Render threshold instead of weight when present
4. Document the distinction between weight and threshold

### Option 2: Remove Threshold (Simplify)
1. Remove threshold attribute entirely
2. Use only weight for all arcs
3. Simplify simulation logic
4. Remove threshold UI fields

### Option 3: Restrict Threshold to Input Arcs
1. Keep current behavior (input only)
2. Add validation: error if threshold set on output arc
3. Save/load threshold properly
4. Document clearly: "Threshold only applies to input arcs"
5. Show threshold in label for input arcs

### Option 4: Make Threshold Formula-Only
Threshold seems designed for **conditional firing** (e.g., "fire only when P1 > 50"):
1. Keep threshold but make it boolean/conditional
2. Use weight for token quantities
3. Use threshold for enablement conditions
4. This matches the name better ("threshold" = condition, not quantity)

## Usage Context

Based on code comments, threshold appears intended for:
- **Formula-based conditions**: `arc.threshold` as expression
- **Dynamic enablement**: Check condition before firing
- **Advanced modeling**: Beyond simple token counting

Example use case:
```python
arc.weight = 5        # Consume/produce 5 tokens
arc.threshold = "P1 > 100"  # But only if P1 has 100+ tokens
```

But current implementation treats threshold as a **quantity**, not a **condition**.

## Conclusion

**Current behavior is:**
1. ✅ Threshold supersedes weight for input arcs
2. ❌ Threshold ignored for output arcs (by design - needs documentation)
3. ✅ **FIXED:** Threshold now saved to file and restored on load
4. ❌ UI shows weight, not active threshold value

**Remaining Recommendations:**
1. Document asymmetric behavior (threshold only affects input arcs)
2. Add validation warning if threshold set on output arc
3. Update arc rendering to show threshold when active
4. Add tooltip/help text explaining threshold vs weight

**Recent Fix (Current Session):**
- ✅ Added threshold to `Arc.to_dict()` serialization
- ✅ Added threshold to `Arc.from_dict()` deserialization
- ✅ All arc subclasses inherit the fix via `super()`
- ✅ Tested with numeric values and None
- ✅ Verified with test script: `test_threshold_persistence.py`
