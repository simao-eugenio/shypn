# Selection and Arc Creation Implementation

## Summary

This document describes the implementation of object selection and arc creation functionality for the Petri net editor.

**Status**: ✅ COMPLETE  
**Date**: October 3, 2025

---

## Features Implemented

### 1. Object Selection (Left-Click)

**Behavior**: When no tool is active, left-clicking an object toggles its selection state.

**Implementation**:
- Modified `_on_button_press` in `model_canvas_loader.py`
- Uses `manager.find_object_at_position(x, y)` for hit testing
- Toggles `object.selected` boolean flag
- Triggers redraw to show selection highlight

**Visual Feedback**:
- Selected objects show blue highlight (implemented in render methods)
- Selection highlight: 4px wider border, semi-transparent blue (0.2, 0.6, 1.0, 0.5)

**Code Example**:
```python
# Left-click: toggle selection
if event.button == 1 and not manager.is_tool_active():
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    clicked_obj = manager.find_object_at_position(world_x, world_y)
    
    if clicked_obj is not None:
        clicked_obj.selected = not clicked_obj.selected
        widget.queue_draw()
```

### 2. Arc Creation (Two-Click with Arc Tool)

**Behavior**: When arc tool is active:
1. First click: Select source object (Place or Transition)
2. Second click: Create arc to target object
3. Click empty space: Reset source

**Implementation**:
- Added `_arc_state` dictionary per drawing area
- Stores `source` object and `cursor_pos` for preview
- Two-click state machine in `_on_button_press`
- Bipartite validation happens in `Arc.__init__`

**Visual Feedback**:
- Orange preview line from source to cursor (0.95, 0.5, 0.1, 0.85 alpha)
- Preview arrowhead at cursor position
- Line starts at source boundary (offset by radius)
- Updates in real-time as mouse moves

**Code Flow**:
```python
# First click: set source
if arc_state['source'] is None:
    arc_state['source'] = clicked_obj
    
# Second click: create arc
else:
    try:
        arc = manager.add_arc(source, target)
        # Bipartite validation in Arc.__init__
    except ValueError as e:
        print(f"Cannot create arc: {e}")
    finally:
        arc_state['source'] = None
```

### 3. Arc Preview Line

**Behavior**: While arc tool is active with source selected, an orange line follows the cursor.

**Implementation**:
- `_draw_arc_preview` method in `model_canvas_loader.py`
- Called from `_on_draw` when conditions met
- Motion handler updates cursor position continuously

**Details**:
- Color: Orange (0.95, 0.5, 0.1) with 0.85 alpha
- Line width: 2.0px
- Arrowhead: 11px length, 6px width (smaller than final arc)
- Start point: Offset by source object radius
- End point: Current cursor position

**Geometry**:
```python
# Calculate direction vector
dx = cursor_x - src_x
dy = cursor_y - src_y
dist = math.sqrt(dx * dx + dy * dy)
ux, uy = dx / dist, dy / dist

# Offset start by source radius
start_x = src_x + ux * src_radius
start_y = src_y + uy * src_radius
```

---

## Files Modified

### 1. `src/shypn/helpers/model_canvas_loader.py`

**Changes**:
- Added `_arc_state` dictionary initialization in `_setup_event_controllers`
- Modified `_on_button_press`:
  * Added arc tool handling (two-click creation)
  * Added selection toggle (when no tool active)
- Modified `_on_motion_notify`:
  * Update cursor position for arc preview
  * Trigger redraw when arc source is set
- Modified `_on_draw`:
  * Call `_draw_arc_preview` when conditions met
- Added `_draw_arc_preview` method:
  * Draws orange preview line from source to cursor
  * Renders arrowhead at cursor position

**Lines Modified**: ~150 lines changed/added

### 2. `doc/SELECTION_AND_ARC_CREATION_ANALYSIS.md` (NEW)

**Content**:
- Comprehensive analysis of legacy selection/arc creation patterns
- Hit testing implementation details
- Coordinate transformation explanations
- Event handling architecture
- Visual feedback specifications
- Implementation strategy for current code

**Length**: ~600 lines

### 3. `doc/SELECTION_AND_ARC_CREATION_IMPLEMENTATION.md` (THIS FILE)

**Content**:
- Summary of implemented features
- Code examples and flow diagrams
- Testing instructions
- Usage guide

---

## Testing Instructions

### Prerequisites
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

### Test 1: Object Selection

**Steps**:
1. Make sure no tool is active (all tool buttons unchecked)
2. Create a place by clicking the [P] button, then click on canvas
3. Create a transition by clicking the [T] button, then click on canvas
4. Deselect tool (click [P] or [T] button again to uncheck)
5. Left-click on the place → Should see blue selection highlight
6. Left-click on the place again → Highlight should disappear
7. Left-click on transition → Should see blue selection highlight
8. Both objects can be selected simultaneously

**Expected Output**:
```
P1 selected
P1 deselected
T1 selected
```

**Visual Check**:
- ✓ Blue highlight appears around selected object (4px wider border)
- ✓ Highlight disappears when object is deselected
- ✓ Multiple objects can be selected simultaneously

### Test 2: Arc Creation (Valid Connection)

**Steps**:
1. Create a place (P1) at position (200, 200)
2. Create a transition (T1) at position (400, 200)
3. Click [A] button to activate arc tool
4. Click on P1 → Should see message "Arc creation: source P1 selected"
5. Move mouse toward T1 → Should see orange preview line following cursor
6. Click on T1 → Should see message "Created A1: P1 → T1"

**Expected Output**:
```
Created P1 at (200.0, 200.0)
Created T1 at (400.0, 200.0)
Arc creation: source P1 selected
Created A1: P1 → T1
```

**Visual Check**:
- ✓ Orange preview line appears from P1 to cursor
- ✓ Preview line starts at P1 boundary (not center)
- ✓ Arrowhead at cursor position
- ✓ Preview disappears after arc is created
- ✓ Final arc appears with proper two-line arrowhead

### Test 3: Arc Creation (Invalid Connection - Bipartite Violation)

**Steps**:
1. Create two places: P1 and P2
2. Click [A] button to activate arc tool
3. Click on P1 → Source selected
4. Click on P2 → Should see error message

**Expected Output**:
```
Arc creation: source P1 selected
Cannot create arc: Invalid connection: Place → Place. Arcs must connect Place↔Transition (bipartite property). Valid connections: Place→Transition or Transition→Place.
```

**Visual Check**:
- ✓ Preview line shows while hovering over P2
- ✓ No arc is created
- ✓ Error message displayed in terminal
- ✓ Arc source is reset (can start new arc)

### Test 4: Arc Creation Reset

**Steps**:
1. Create a place P1
2. Click [A] button to activate arc tool
3. Click on P1 → Source selected
4. Click on empty space → Source should reset

**Expected Output**:
```
Arc creation: source P1 selected
```

**Visual Check**:
- ✓ Preview line disappears when clicking empty space
- ✓ Can start new arc from different source

### Test 5: Preview Line Geometry

**Steps**:
1. Create a place P1 (radius ~20px)
2. Create a transition T1 far away
3. Activate arc tool, click on P1
4. Move cursor toward T1
5. Observe preview line start point

**Visual Check**:
- ✓ Preview line starts at P1 boundary, NOT at center
- ✓ Line direction always points toward cursor
- ✓ Preview arrowhead rotates with cursor movement
- ✓ Orange color (RGB: 0.95, 0.5, 0.1) is visible

### Test 6: Multiple Arcs

**Steps**:
1. Create: P1 → T1 → P2 → T2
2. Create arcs:
   - P1 → T1 (valid)
   - T1 → P2 (valid)
   - P2 → T2 (valid)
   - T2 → P1 (valid, creates cycle)

**Expected Output**:
```
Created A1: P1 → T1
Created A2: T1 → P2
Created A3: P2 → T2
Created A4: T2 → P1
```

**Visual Check**:
- ✓ All four arcs render correctly
- ✓ Arcs render behind places and transitions
- ✓ Arrowheads point in correct directions
- ✓ No visual overlaps or glitches

---

## Usage Guide

### Normal Workflow

**Creating Objects**:
1. Click tool button ([P] for place, [T] for transition)
2. Click on canvas to place object
3. Click tool button again to deselect (or click another tool)

**Selecting Objects**:
1. Make sure no tool is active (all buttons unchecked)
2. Left-click on object to select
3. Left-click again to deselect
4. Multiple objects can be selected simultaneously

**Creating Arcs**:
1. Create some places and transitions
2. Click [A] button to activate arc tool
3. Click on source object (Place or Transition)
4. Watch orange preview line follow cursor
5. Click on target object to create arc
6. Click empty space to reset if needed

**Navigation**:
- Middle-click or right-click + drag: Pan
- Scroll wheel: Zoom in/out
- Shift + left-drag: Pan

### Keyboard Shortcuts (Future)

Planned shortcuts (not yet implemented):
- `P` - Place tool
- `T` - Transition tool
- `A` - Arc tool
- `S` - Select tool
- `Esc` - Deselect current tool

---

## Technical Details

### Hit Testing Algorithm

**Method**: `ModelCanvasManager.find_object_at_position(x, y)`

**Order**:
1. Check transitions (reverse order for top-to-bottom)
2. Check places (reverse order)
3. Arcs not checked (too thin to click easily)

**Geometry**:
- Places: `(x - place.x)² + (y - place.y)² <= radius²`
- Transitions: `place.contains_point(x, y)` (uses rectangle bbox)

### Arc Preview Optimization

**Redraw Triggers**:
- Motion event when arc source is set
- Only redraws when necessary (not on every motion)

**Performance**:
- Preview calculation: O(1) - simple vector math
- No expensive operations in preview rendering
- Smooth animation even with many objects

### State Management

**Arc State Structure**:
```python
_arc_state[drawing_area] = {
    'source': None,        # Source object reference
    'cursor_pos': (0, 0)   # Last cursor (world coords)
}
```

**State Transitions**:
```
None --[click object]--> Source Set --[click target]--> Arc Created --> None
                              |
                              +--[click empty]--> None
```

**Reset Conditions**:
- Arc successfully created
- Click on empty space
- Tool changed (future enhancement)

### Coordinate Spaces

**World Space** (Logical):
- Object positions: `obj.x`, `obj.y`
- Hit testing performed here
- Arc endpoints stored here
- Grid is defined here

**Screen Space** (Device):
- Mouse events: `event.x`, `event.y`
- Rendering coordinates
- Preview line drawn here
- Affected by zoom and pan

**Transformations**:
```python
# Mouse → World
world_x, world_y = manager.screen_to_world(event.x, event.y)

# World → Screen
screen_x, screen_y = manager.world_to_screen(world_x, world_y)
```

---

## Future Enhancements

### Priority: High
- [ ] **Drag selected objects**: Move objects by dragging
- [ ] **Multiple selection**: Ctrl+click to add to selection
- [ ] **Selection box**: Click-drag to select multiple objects
- [ ] **Delete selected**: Delete/Backspace key to remove

### Priority: Medium
- [ ] **Keyboard shortcuts**: P/T/A/S keys for tools
- [ ] **Undo/Redo**: History for all operations
- [ ] **Cut/Copy/Paste**: Clipboard operations
- [ ] **Snap to grid**: Align objects to grid points

### Priority: Low
- [ ] **Tool status bar**: Show current tool in status area
- [ ] **Hover highlighting**: Brighten object on mouse hover
- [ ] **Arc weight editing**: Click arc to change weight
- [ ] **Object properties panel**: Edit labels, colors, etc.

---

## Known Limitations

### Current Constraints

1. **No drag selection**: Objects cannot be moved by dragging yet
2. **No multi-select modifier**: Ctrl+click doesn't add to selection
3. **No keyboard shortcuts**: Must use mouse to select tools
4. **No undo**: Changes are permanent (need undo system)
5. **Arc source visual**: Source object doesn't highlight when selected

### Workarounds

1. **Moving objects**: Delete and recreate at new position
2. **Multiple arcs**: Click tool button between each arc
3. **Wrong arc**: Delete and recreate (no undo yet)

---

## Legacy Comparison

### Matching Legacy Behavior ✓

- ✓ Two-click arc creation
- ✓ Orange preview line (0.95, 0.5, 0.1)
- ✓ Preview arrowhead at cursor
- ✓ Bipartite validation
- ✓ Click empty space to reset
- ✓ Selection toggle on click
- ✓ Hit testing order (T before P)

### Not Yet Implemented

- ⏳ Drag selected objects
- ⏳ Multi-select with Ctrl+click
- ⏳ Selection box (lasso tool)
- ⏳ Hover highlighting
- ⏳ Keyboard tool shortcuts
- ⏳ Undo/redo system

---

## Debugging

### Common Issues

**Q: Preview line doesn't show**
- Check: Is arc tool active? (Button should be checked)
- Check: Did you click a source object first?
- Check: Is source a Place or Transition (not empty space)?

**Q: Cannot create arc**
- Check: Source and target must be different types (P↔T or T↔P)
- Check: Error message in terminal shows reason
- Check: Both source and target must exist

**Q: Selection doesn't work**
- Check: Tool buttons must be unchecked (no active tool)
- Check: Click directly on object (not near it)
- Check: Blue highlight should appear (rendering issue if not)

**Q: Preview line starts at wrong position**
- Check: Should start at object boundary, not center
- Check: Radius calculation might be wrong for your object
- Debug: Print `src_radius` value in `_draw_arc_preview`

### Debug Output

Enable by adding print statements:
```python
# In _on_button_press
print(f"DEBUG: Clicked at world ({world_x:.1f}, {world_y:.1f})")
print(f"DEBUG: Found object: {clicked_obj}")

# In _draw_arc_preview
print(f"DEBUG: Preview from {src_x},{src_y} to {cursor_x},{cursor_y}")
print(f"DEBUG: Source radius: {src_radius:.1f}")
```

---

## Conclusion

Selection and arc creation are now **fully implemented** and match the legacy behavior. The system supports:

- ✅ Object selection with visual feedback
- ✅ Two-click arc creation with preview
- ✅ Bipartite validation
- ✅ Real-time preview line
- ✅ Proper coordinate transformations
- ✅ Hit testing with correct priority

The implementation is ready for use and can be extended with the planned enhancements.
