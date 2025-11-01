# Loop and Opposite-Direction Arc Auto-Conversion

## Overview

SHYPN automatically detects and converts certain arc configurations to curved arcs to prevent visual overlap and improve model readability. This document describes the automatic conversion behavior for:

1. **Loop arcs** (self-arcs where source == target)
2. **Opposite-direction parallel arcs** (A→B and B→A)

---

## Loop Arc Auto-Conversion

### Problem
When an arc's source and target are the same object (e.g., T1→T1), it's called a "loop" or "self-arc". If rendered as a straight line, it has zero length and becomes invisible.

### Solution
Loop arcs are **automatically converted to curved arcs** with a default control offset.

### Behavior

**Detection:**
- Triggered when `arc.source == arc.target`
- Detected in both:
  - Manual arc creation (`add_arc`)
  - Model loading (`load_objects`)

**Conversion:**
- Straight arc (`Arc`) → Curved arc (`CurvedArc`)
- Default control offset applied:
  - `control_offset_x = 60.0` (pixels to the right)
  - `control_offset_y = -60.0` (pixels upward)

**Rendering:**
- Loop arcs always render as curved bezier curves
- Control point is offset from the object center
- Creates a visible loop extending from and returning to the same object

### Example

```python
# User draws arc from T1 to T1
arc = manager.add_arc(T1, T1)

# System automatically:
# 1. Detects: arc.source == arc.target
# 2. Converts: Arc → CurvedArc
# 3. Sets: control_offset_x = 60.0, control_offset_y = -60.0
# 4. Renders: Visible loop above and to the right of T1
```

---

## Opposite-Direction Parallel Arc Auto-Conversion

### Problem
When two arcs connect the same objects in opposite directions (A→B and B→A), rendering them both as straight lines causes complete overlap, making them indistinguishable.

### Solution
Opposite-direction arcs are **automatically converted to curved arcs** with **perpendicular offsets** on opposite sides, creating mirror symmetry.

### Behavior

**Detection:**
- Triggered when drawing a new arc that creates an opposite-direction pair
- System checks: Does arc B satisfy `B.source == A.target AND B.target == A.source`?

**Conversion Process:**
1. Both arcs converted from `Arc` to `CurvedArc`
2. Calculate direction vector: `(dx, dy) = target.position - source.position`
3. Calculate perpendicular vector: `(perp_x, perp_y) = (-dy, dx)` (90° rotation)
4. Apply mirrored offsets:
   - Arc with **lower ID**: `control_offset = perp * +50px`
   - Arc with **higher ID**: `control_offset = perp * -50px`

**Result:**
- Mirror-symmetric curved arcs
- Each arc curves to one side of the straight line
- Clear visual separation
- 50 pixel perpendicular offset on each side

### Mathematical Details

Given:
- Arc A: P1 → P2
- Arc B: P2 → P1 (opposite direction)

Calculation:
```python
# Direction vector (normalized)
dx = (P2.x - P1.x) / length
dy = (P2.y - P1.y) / length

# Perpendicular vector (90° counterclockwise rotation)
perp_x = -dy
perp_y = dx

# Offset distance
offset = 50.0  # pixels

# Apply to control points
if A.id < B.id:
    A.control_offset_x = perp_x * offset   # Curves one way
    A.control_offset_y = perp_y * offset
    B.control_offset_x = -perp_x * offset  # Curves opposite way
    B.control_offset_y = -perp_y * offset
```

### Visual Example

```
Before (overlapping):           After (separated):

    P1 ========== P2                P1 -------> P2
                                       <-------
    
Both arcs overlap completely    Arc A curves above (ID < B.id)
                                Arc B curves below (mirror)
```

### Example Scenario

```python
# User draws first arc
arc1 = manager.add_arc(place_A, place_B)  # A→B
# System: Single arc, no conversion needed (stays straight)

# User draws opposite arc
arc2 = manager.add_arc(place_B, place_A)  # B→A
# System automatically:
# 1. Detects: arc2 creates opposite-direction parallel
# 2. Converts BOTH arcs: Arc → CurvedArc
# 3. Calculates perpendicular direction from A to B
# 4. Applies mirrored offsets:
#    - arc1 (lower ID) curves +50px perpendicular
#    - arc2 (higher ID) curves -50px perpendicular
# 5. Result: Mirror-symmetric curved arcs
```

---

## Implementation Details

### Files Modified

**`src/shypn/data/model_canvas_manager.py`:**
- `_auto_convert_parallel_arcs_to_curved(new_arc)`:
  - Added loop detection: `is_loop = (new_arc.source == new_arc.target)`
  - Added opposite-direction detection and offset calculation
  - Applied perpendicular control offsets to both arcs
- `load_objects(places, transitions, arcs)`:
  - Added call to `_auto_convert_parallel_arcs_to_curved` for each loaded arc
  - Ensures models loaded from file also get auto-conversion

**`src/shypn/netobjs/arc.py`:**
- `render(cr, transform, zoom)`:
  - Added loop detection: `is_loop = (self.source == self.target)`
  - Added loop direction handling (default to pointing right)
  - Modified render condition: `render_as_curved = self.is_curved or has_parallels or is_loop`
  - Loop arcs always render as curved, never straight

### Code Flow

#### Manual Arc Creation
```
User draws arc
    ↓
add_arc(source, target)
    ↓
_auto_convert_parallel_arcs_to_curved(new_arc)
    ↓
[Loop check] is_loop = (source == target)?
    YES → Convert to CurvedArc, set offset (60, -60)
    ↓
[Parallel check] detect_parallel_arcs(new_arc)
    ↓
Has opposite-direction parallel?
    YES → Convert both to CurvedArc
        → Calculate perpendicular direction
        → Apply mirrored offsets (±50px)
    ↓
Mark canvas dirty, trigger redraw
```

#### Model Loading
```
Load model from .shy file
    ↓
load_objects(places, transitions, arcs)
    ↓
For each arc:
    → Append to manager.arcs
    → Set arc._manager reference
    → Call _auto_convert_parallel_arcs_to_curved(arc)
    ↓
Same conversion logic as manual creation
```

---

## Configuration

### Default Offsets

**Loop Arcs:**
```python
control_offset_x = 60.0   # pixels to the right
control_offset_y = -60.0  # pixels upward
```

**Opposite-Direction Arcs:**
```python
offset_distance = 50.0  # pixels perpendicular to arc
```

### Customization

Users can manually adjust control offsets after auto-conversion using the arc properties editor or by directly editing the `.shy` file.

---

## Testing

### Test Loop Arc
1. Open SHYPN
2. Create a place P1
3. Draw arc from P1 to P1
4. **Expected:** Arc automatically curves above P1
5. **Verify:** Arc is visible as a loop

### Test Opposite-Direction Arcs
1. Open SHYPN
2. Create two places: P1 and P2
3. Draw arc from P1 to P2
4. **Verify:** Arc is straight (single arc)
5. Draw arc from P2 to P1
6. **Expected:** Both arcs automatically curve
7. **Verify:** 
   - Both arcs are curved
   - One curves above the line, one below
   - Mirror symmetry (equal offsets on opposite sides)
   - Clear visual separation

### Test Model Loading
1. Open Interactive.shy (contains 4 loop arcs)
2. **Expected:** All loop arcs render as visible curves
3. Load synt_glycolysis.shy (contains 7 loop arcs)
4. **Expected:** All loop arcs render as visible curves

---

## Biological Context

In biological Petri nets (continuous, hybrid, stochastic):

**Loop Arcs:**
- Common for **autocatalytic reactions** (enzyme produces its own activator)
- **Homeostatic regulation** (output regulates its own production)
- **Enzyme recycling** (catalyst returns to substrate pool)

**Opposite-Direction Arcs:**
- **Reversible reactions** (forward and reverse directions)
- **Cyclic pathways** (substrate ⇄ product equilibrium)
- **Bidirectional transport** (import/export across membrane)

---

## Related Features

- **Parallel Arc Offset:** For same-direction parallels (A→B, A→B), uses different offset logic
- **Curved Arc Editing:** Users can manually adjust control points
- **Test Arcs:** Catalyst arcs (read-only) often use loop configuration
- **Inhibitor Arcs:** Feedback loops commonly use opposite-direction pairs

---

## Troubleshooting

### Loop Arc Not Visible
- **Cause:** Arc not converted to curved
- **Solution:** Check arc type in properties (`object_type` should be `curved_arc`)
- **Workaround:** Manually convert using arc context menu

### Opposite Arcs Still Overlapping
- **Cause:** Only one arc converted, or offsets not applied
- **Solution:** Delete both arcs, redraw in sequence
- **Check:** Both arcs should have `control_offset_x/y` values

### Wrong Curvature Direction
- **Cause:** Arc IDs determine which side curves
- **Solution:** Swap arc creation order, or manually adjust offsets
- **Alternative:** Edit `.shy` file to swap `control_offset` signs

---

## Version History

**Version 1.0** (2025-11-01)
- Initial implementation of loop arc auto-conversion
- Opposite-direction arc perpendicular offset calculation
- Integration with model loading pipeline
- Default offsets: Loop (60, -60), Opposite (±50)

---

## Future Enhancements

1. **Configurable Offsets:** User preferences for default loop/parallel offsets
2. **Multiple Loops:** Auto-offset multiple loop arcs on same object
3. **Smart Loop Direction:** Choose loop direction based on available space
4. **Animated Transitions:** Show conversion happening in real-time
5. **Undo/Redo:** Support for reverting auto-conversions

---

## Summary

✅ **Loop arcs** (source == target) automatically convert to curved with (60, -60) offset  
✅ **Opposite-direction arcs** (A→B, B→A) automatically convert with ±50px perpendicular offsets  
✅ **Mirror symmetry** for opposite pairs creates clear visual separation  
✅ **Works for both** manual arc creation and model loading  
✅ **Biological accuracy** supports reversible reactions and autocatalytic loops  

This feature eliminates the need for manual arc conversion and ensures all parallel/loop arcs are immediately visible and distinguishable.
