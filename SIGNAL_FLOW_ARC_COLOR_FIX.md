# SignalFlowArc Color Fix

## Problem Summary

After enrichment, some SignalFlowArc instances were displaying with black color (0.0, 0.0, 0.0) instead of the correct light gray color (0.7, 0.7, 0.7).

## Root Cause

The issue occurred due to a serialization/deserialization problem:

1. **Creation**: SignalFlowArc instances were correctly created with light gray color set in `__init__`
2. **Serialization**: When saved to .shypn files, the base Arc.to_dict() method was used, which saved whatever color was currently set
3. **Deserialization**: Arc.from_dict() would:
   - Correctly create a SignalFlowArc instance based on `arc_type: "signal_flow"`
   - SignalFlowArc.__init__() would set `self.color = (0.7, 0.7, 0.7)`
   - But then Arc.from_dict() would **overwrite** the color if `"color"` existed in saved data
   - If the saved file had `"color": [0.0, 0.0, 0.0]`, it would override the correct light gray

## Files Modified

### 1. src/shypn/netobjs/signal_flow_arc.py

**Added `to_dict()` method:**

```python
def to_dict(self) -> dict:
    """Serialize signal flow arc to dictionary for persistence.
    
    Returns:
        dict: Dictionary containing all arc properties with arc_type='signal_flow'
    """
    data = super().to_dict()
    # Ensure color is always the correct light gray for signal flow arcs
    # This prevents black color from being saved and restored
    data['color'] = list(self.DEFAULT_COLOR)
    return data
```

**Why this fixes the issue:**
- Overrides the base Arc.to_dict() to always save the correct light gray color
- Ensures that even if the color was temporarily changed, it saves with the correct value
- On deserialization, Arc.from_dict() will restore the light gray color from saved data

## Verification

### Test Created: test_signal_flow_arc_color.py

Tests the complete save/load cycle:
1. ✓ Creates SignalFlowArc with light gray color
2. ✓ Serializes to dict with correct color
3. ✓ Saves to JSON file
4. ✓ Loads from JSON file
5. ✓ Deserializes back to SignalFlowArc with correct color

**Test Result:** All tests passed ✓

### Utility Script: fix_signal_flow_arc_colors.py

Created a utility script to fix any existing .shypn files with incorrect black SignalFlowArcs:

```bash
# Dry run (preview changes)
python fix_signal_flow_arc_colors.py --dry-run

# Fix all files in workspace/ and test_output/
python fix_signal_flow_arc_colors.py

# Fix specific directory
python fix_signal_flow_arc_colors.py /path/to/models/
```

## Related Code Already Correct

### 1. Enrichment (stoichiometry.py)
Already creates SignalFlowArc instances correctly:
```python
if getattr(place, 'is_signal_place', False):
    arc = SignalFlowArc(
        source=place,
        target=transition,
        id=arc_id,
        name=arc_id,
        weight=substrate.coefficient
    )
```

### 2. Arc Transformation (arc_transform.py)
Already handles color correctly when converting to signal flow:
```python
# Copy all properties (except color - use SignalFlowArc's light gray DEFAULT_COLOR)
# new_arc.color is already set to (0.7, 0.7, 0.7) by SignalFlowArc.__init__
new_arc.width = arc.width
```

### 3. Deserialization (arc.py)
Correctly creates SignalFlowArc subclass:
```python
elif arc_type == 'signal_flow':
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    arc_class = SignalFlowArc
```

## Impact

- **Minimal code change**: Single method override in SignalFlowArc
- **No breaking changes**: Backward compatible with existing code
- **Future-proof**: All new SignalFlowArcs will save with correct color
- **Self-healing**: On next save, any models with black SignalFlowArcs will be fixed

## Testing Recommendations

1. **Unit test passed**: test_signal_flow_arc_color.py ✓
2. **Enrichment workflow**: Enrich a KEGG model and verify all signal flow arcs are light gray
3. **Save/load cycle**: Save enriched model, reload, verify colors persist
4. **Arc conversion**: Convert regular arc to signal flow via properties dialog, verify light gray

## No Files Need Fixing

Scanned workspace/ directory - no existing files have black SignalFlowArcs yet, so no retroactive fixes needed.

## Resolution Status

✓ **FIXED** - SignalFlowArc color inconsistency resolved
✓ **TESTED** - Serialization/deserialization cycle verified
✓ **DOCUMENTED** - Fix explanation and testing guidelines provided
