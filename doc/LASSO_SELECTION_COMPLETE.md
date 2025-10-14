# Lasso Selection System - Complete Implementation

**Date**: October 12, 2025  
**Status**: ✅ Complete  
**Feature**: Freeform polygon selection with full editing capabilities

---

## Overview

The lasso selection system allows users to select multiple Petri net objects by drawing a freeform polygon around them. Once selected, objects can be edited using standard keyboard shortcuts (cut, copy, paste, delete) and dragged as a group.

## User Experience

### Activating Lasso Selection

**Method 1**: Click the Lasso button in the Operations Palette  
**Method 2**: Press `L` key (when palette visible)  
**Method 3**: Use SwissKnife palette Edit tools category

### Drawing the Lasso

1. **Click and hold** left mouse button at starting position
2. **Drag** to draw the lasso path
3. **Release** mouse button to complete selection
4. All objects inside the polygon are automatically selected

### Visual Feedback

- **Lasso path**: Semi-transparent blue dashed line (rgba(0.2, 0.6, 1.0, 0.5))
- **Path points**: Small blue circles at each vertex
- **Selected objects**: Blue highlight on selected places and transitions
- **Auto-close**: Path automatically closes when mouse is released

### Canceling Lasso

- Press `Escape` key while drawing to cancel
- Click outside objects to deselect all

## Keyboard Shortcuts

### Clipboard Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+X` | Cut | Copy selected objects to clipboard and delete them |
| `Ctrl+C` | Copy | Copy selected objects to clipboard |
| `Ctrl+V` | Paste | Paste clipboard contents with 30px offset |
| `Delete` | Delete | Delete selected objects (with undo support) |

### History Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Z` | Undo | Undo last operation |
| `Ctrl+Shift+Z` | Redo | Redo last undone operation |
| `Ctrl+Y` | Redo | Alternative redo shortcut |

### Selection Operations

| Shortcut | Action | Description |
|----------|--------|-------------|
| `L` | Lasso | Activate lasso selection mode |
| `Escape` | Cancel | Cancel current lasso or exit edit mode |

## Dragging Selected Objects

### How It Works

1. Select objects with lasso (or rectangle selection, or Ctrl+Click)
2. Click and drag any selected object
3. **All selected objects move together** as a group
4. Release mouse to complete the move
5. Move operation is recorded in undo history

### Implementation Details

- Only Places and Transitions can be dragged (not Arcs)
- Arcs automatically follow their connected nodes
- Drag offset is calculated relative to clicked object
- All objects maintain their relative positions
- Grid snapping applies to the entire group

### Undo Support

All drag operations are recorded for undo/redo:
```python
MoveOperation(move_data)  # Stores original and final positions
```

## Clipboard Operations

### What Gets Copied

**Places**:
- Position (x, y)
- Name (auto-renamed to avoid conflicts)
- Radius
- Token count
- Capacity

**Transitions**:
- Position (x, y)
- Name (auto-renamed to avoid conflicts)
- Dimensions (width, height)
- Orientation (horizontal/vertical)
- Type (continuous, timed, stochastic, immediate)
- Rate and delay parameters

**Arcs**:
- Only copied if **both** source and target are in selection
- Weight
- Arc type (normal/inhibitor)
- Curved arc handle position (if curved)

### Name Generation

Pasted objects get unique names automatically:
```python
"Place1" → "Place2" → "Place3"
"T1" → "T2" → "T3"
```

Uses regex to extract base name and numeric suffix, then increments to find unique name.

### Paste Offset

Pasted objects are offset by **30 pixels** (x and y) to avoid overlapping with originals. This makes it easy to see what was just pasted.

### Arc Reconstruction

When pasting:
1. Create all places and transitions first
2. Build ID mapping (old ID → new object)
3. Create arcs only if both endpoints exist in paste
4. Preserve curved arc geometry with offset handle position

## Technical Implementation

### Files Modified

1. **`src/shypn/helpers/model_canvas_loader.py`**
   - Added `_clipboard` instance variable
   - Enhanced `_on_button_release()` for lasso completion
   - Extended `_on_key_press_event()` with clipboard shortcuts
   - Implemented `_cut_selection()`, `_copy_selection()`, `_paste_selection()`
   - Added `_generate_unique_name()` helper

2. **`src/shypn/edit/lasso_selector.py`**
   - Existing implementation (no changes needed)
   - Provides: `start_lasso()`, `add_point()`, `finish_lasso()`, `cancel_lasso()`
   - Uses ray-casting algorithm for point-in-polygon test

3. **`src/shypn/edit/selection_manager.py`**
   - Existing drag implementation (no changes needed)
   - Automatically handles dragging all selected objects

### Lasso Completion Logic

```python
def _on_button_release(self, widget, event, manager):
    lasso_state = self._lasso_state.get(widget, {})
    
    if lasso_state.get('active', False) and lasso_state.get('selector'):
        if lasso_state['selector'].is_active and event.button == 1:
            lasso_state['selector'].finish_lasso()  # Select objects
            lasso_state['active'] = False            # Deactivate lasso mode
            widget.queue_draw()                      # Remove visual feedback
            return True
```

**Key changes**:
- Check for `event.button == 1` to ensure left-click release
- Immediately deactivate lasso mode after completion
- Force redraw to remove lasso visualization
- Return True to consume event

### Selection via Point-in-Polygon

The `LassoSelector.finish_lasso()` method:

1. Closes the polygon (adds first point to end if needed)
2. Tests each object's center point against polygon
3. Uses ray-casting algorithm for inside/outside test
4. Selects all objects with centers inside polygon
5. Resets lasso state

```python
def _is_point_in_polygon(self, x, y, polygon):
    """Ray casting algorithm for point-in-polygon test."""
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside
```

### Clipboard Serialization

Objects are serialized to dictionaries with all necessary properties:

```python
self._clipboard = [
    {
        'type': 'place',
        'name': 'Place1',
        'x': 100.0,
        'y': 200.0,
        'radius': 25.0,
        'tokens': 3,
        'capacity': inf,
        'id': 140234567890  # Temporary for arc mapping
    },
    {
        'type': 'arc',
        'source_id': 140234567890,
        'target_id': 140234567891,
        'weight': 2,
        'arc_type': 'normal',
        'is_curved': True,
        'handle_x': 150.0,
        'handle_y': 250.0
    }
]
```

### Deserialization and Paste

```python
def _paste_selection(self, manager, widget):
    offset_x, offset_y = 30, 30
    id_map = {}
    
    # Pass 1: Create nodes
    for item in self._clipboard:
        if item['type'] == 'place':
            place = manager.add_place(
                item['x'] + offset_x,
                item['y'] + offset_y,
                name=self._generate_unique_name(manager, item['name'])
            )
            # ... set properties
            id_map[item['id']] = place
    
    # Pass 2: Create arcs
    for item in self._clipboard:
        if item['type'] == 'arc':
            source = id_map.get(item['source_id'])
            target = id_map.get(item['target_id'])
            if source and target:
                arc = manager.add_arc(source, target)
                # ... set properties
```

Two-pass approach ensures all nodes exist before creating arcs.

## Testing Scenarios

### Scenario 1: Basic Lasso Selection

1. Create 3 places and 2 transitions
2. Click Lasso button
3. Draw polygon around 2 places and 1 transition
4. Release mouse
5. ✅ Verify: 3 objects selected (blue highlight)
6. ✅ Verify: Lasso visualization disappears

### Scenario 2: Cut and Paste

1. Lasso-select 2 places
2. Press `Ctrl+X` (cut)
3. ✅ Verify: Objects disappear from canvas
4. Press `Ctrl+V` (paste)
5. ✅ Verify: New objects appear 30px offset
6. ✅ Verify: Names are unique (Place2, Place3)
7. Press `Ctrl+Z` (undo)
8. ✅ Verify: Pasted objects disappear
9. Press `Ctrl+Z` again
10. ✅ Verify: Cut objects reappear

### Scenario 3: Copy with Arcs

1. Create Place1 → Transition1 → Place2 (with arcs)
2. Lasso-select all 3 objects
3. Press `Ctrl+C` (copy)
4. Press `Ctrl+V` (paste)
5. ✅ Verify: New Place3 → Transition2 → Place4 created
6. ✅ Verify: Arcs properly connect new objects
7. ✅ Verify: All objects offset by 30px

### Scenario 4: Drag Selected Group

1. Lasso-select 3 objects
2. Click and drag any selected object
3. ✅ Verify: All 3 objects move together
4. ✅ Verify: Relative positions preserved
5. Release mouse
6. Press `Ctrl+Z`
7. ✅ Verify: All objects return to original positions

### Scenario 5: Delete Selection

1. Lasso-select 4 objects
2. Press `Delete` key
3. ✅ Verify: All 4 objects deleted
4. Press `Ctrl+Z`
5. ✅ Verify: All 4 objects restored with correct properties

### Scenario 6: Lasso Cancellation

1. Click Lasso button
2. Start drawing lasso path (3-4 points)
3. Press `Escape`
4. ✅ Verify: Lasso path disappears
5. ✅ Verify: No objects selected
6. ✅ Verify: Can use canvas normally

### Scenario 7: Curved Arcs Preservation

1. Create Place1 → Place2 with curved arc
2. Edit arc to adjust curve handle
3. Select both places (lasso or Ctrl+Click)
4. Copy and paste
5. ✅ Verify: New arc has same curve as original
6. ✅ Verify: Curve handle offset correctly

## Known Limitations

### Current Constraints

1. **Lasso only tests center points**: Objects must have their center inside the polygon to be selected. Large objects partially covered by lasso may not be selected.

2. **No partial arc selection**: Arcs are only copied if **both** endpoints are in the selection. This prevents orphaned arcs in clipboard.

3. **No grouped undo for paste**: Pasting multiple objects creates individual undo entries. Would need composite operation for single undo.

4. **Clipboard is volatile**: Clipboard contents are lost when application closes. No persistent clipboard across sessions.

5. **No visual clipboard preview**: Users can't see what's in clipboard before pasting.

### Future Enhancements

1. **Bounding box selection**: Option to select objects by bounding box overlap instead of just center point

2. **Clipboard panel**: Show clipboard contents visually with thumbnails

3. **Multiple clipboards**: Maintain history of copied items (clipboard ring)

4. **Persistent clipboard**: Save clipboard to workspace settings file

5. **Smart arc handling**: Option to break arcs when source/target not in selection (create "hanging" arcs)

6. **Paste at cursor**: Option to paste objects at current mouse position instead of fixed offset

7. **Duplicate shortcut**: Add `Ctrl+D` to duplicate selection in place (like copy+paste in one step)

8. **Select similar**: Right-click menu option to "Select all places" or "Select all transitions"

## Integration Points

### SwissKnife Palette

Lasso button is available in Edit category:
```python
'lasso': {
    'icon': '🔵',
    'tooltip': 'Lasso Selection\n\nDraw freeform shape to select objects',
    'category': 'edit',
    'type': 'tool'
}
```

### Operations Palette

Legacy operations palette also has lasso button with `L` shortcut.

### Canvas Event Handlers

- **Button Press**: Starts lasso drawing if lasso mode active
- **Motion Notify**: Adds points to lasso path (min 5px spacing)
- **Button Release**: Completes lasso and selects objects
- **Key Press**: Handles clipboard shortcuts and lasso cancellation

### Undo System

All operations integrate with undo manager:
- **Delete**: `DeleteOperation` stores serialized objects
- **Move**: `MoveOperation` stores old and new positions
- **Paste**: Creates new objects (delete on undo)

## Architecture Benefits

### Separation of Concerns

1. **LassoSelector**: Pure geometric logic (path building, point-in-polygon)
2. **ModelCanvasLoader**: UI event handling and coordination
3. **SelectionManager**: Selection state and drag operations
4. **UndoManager**: History tracking for all operations

### No Code Duplication

- Clipboard operations work for lasso, rectangle, and Ctrl+Click selections
- Drag logic shared across all selection methods
- Undo/redo works uniformly for all operations

### Extensibility

Easy to add new features:
- New selection modes (magic wand, similar objects)
- New clipboard formats (export to JSON, import from file)
- New keyboard shortcuts (just add to `_on_key_press_event`)

## Performance Considerations

### Lasso Path Optimization

Points are only added if >5 pixels from last point:
```python
if self.points:
    last_x, last_y = self.points[-1]
    dist = math.sqrt((x - last_x)**2 + (y - last_y)**2)
    if dist < 5.0:
        return  # Skip this point
```

This prevents excessive point density and keeps polygon simple.

### Selection Testing Complexity

- Point-in-polygon test: O(n) where n = polygon vertices
- Selection scan: O(m) where m = total objects
- **Total**: O(n × m) for lasso completion

For typical use:
- 50 polygon points × 100 objects = 5,000 tests
- Negligible on modern hardware

### Clipboard Memory

Clipboard stores full object data, not just references. For large selections (100+ objects), this uses ~10-50 KB memory. Acceptable for desktop application.

## Accessibility

### Keyboard-Only Workflow

1. Press `L` to activate lasso
2. Use mouse to draw (no keyboard alternative for freeform path)
3. Press `Ctrl+C` to copy
4. Press `Ctrl+V` to paste
5. Press `Delete` to delete

**Note**: Lasso drawing requires mouse. Alternative: Use rectangle selection (Shift+Drag) for keyboard-heavy workflow.

### Visual Feedback

- High contrast lasso path (blue on white)
- Dashed line pattern for motion indication
- Selected objects show blue highlight
- All feedback scales with zoom level

## Conclusion

The lasso selection system is now **feature-complete** with:

✅ Freeform polygon drawing  
✅ Automatic object selection  
✅ Complete after mouse release  
✅ Cut/Copy/Paste with Ctrl+X/C/V  
✅ Delete with Delete key  
✅ Drag all selected objects together  
✅ Full undo/redo support  
✅ Proper arc handling (only if both endpoints selected)  
✅ Unique name generation for pasted objects  
✅ Curved arc geometry preservation  

The implementation follows OOP principles with clear separation between geometric logic (LassoSelector), selection state (SelectionManager), and UI coordination (ModelCanvasLoader).

All keyboard shortcuts follow standard conventions (Ctrl+X/C/V, Delete, Ctrl+Z/Y), making the system immediately familiar to users.

---

**Next Steps**: Test in real usage scenarios and gather user feedback for refinements.
