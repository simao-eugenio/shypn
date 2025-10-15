# Keyboard Shortcuts Guide - Selection Operations

## Date
October 15, 2025

## Overview

All keyboard shortcuts work on **selected objects**. First select objects using:
- **Click**: Select single object
- **Ctrl+Click**: Add/remove from selection
- **Rectangle drag**: Select all inside rectangle
- **Ctrl+Rectangle**: Add all inside rectangle to selection
- **Lasso drag**: Select all inside lasso polygon
- **Ctrl+Lasso**: Add all inside lasso to selection

Then use these keyboard shortcuts:

## Delete (DEL)

**Key**: `Delete` or `Numpad Delete`

**Action**: Deletes all selected objects

**Implementation** (`_on_key_press_event`, line ~1404):
```python
# Delete key - delete selected objects
if event.keyval == Gdk.KEY_Delete or event.keyval == Gdk.KEY_KP_Delete:
    selected = manager.selection_manager.get_selected_objects()
    if selected:
        # 1. Store data for undo
        delete_data = []
        for obj in selected:
            delete_data.append(manager.serialize_object_for_undo(obj))
        
        # 2. Delete all selected objects
        for obj in selected:
            manager.delete_object(obj)
        
        # 3. Push to undo stack (Ctrl+Z will restore)
        if hasattr(manager, 'undo_manager') and delete_data:
            manager.undo_manager.push(DeleteOperation(delete_data, manager))
        
        widget.queue_draw()
        return True
```

**Features**:
- ✅ Deletes places, transitions, and arcs
- ✅ Supports undo (Ctrl+Z restores deleted objects)
- ✅ Works with all selection methods
- ✅ Arcs connected to deleted nodes are automatically removed

---

## Copy (Ctrl+C)

**Key**: `Ctrl+C`

**Action**: Copies selected objects to internal clipboard

**Implementation** (`_copy_selection`, line ~2596):
```python
def _copy_selection(self, manager):
    """Copy selected objects to clipboard."""
    selected = manager.selection_manager.get_selected_objects()
    if not selected:
        return
    
    self._clipboard = []
    
    # Separate objects by type
    places = [obj for obj in selected if isinstance(obj, Place)]
    transitions = [obj for obj in selected if isinstance(obj, Transition)]
    arcs = [obj for obj in selected if isinstance(obj, Arc)]
    
    # Serialize places
    for place in places:
        self._clipboard.append({
            'type': 'place',
            'name': place.name,
            'x': place.x,
            'y': place.y,
            'radius': place.radius,
            'tokens': place.tokens,
            'capacity': place.capacity,
            'id': id(place)  # For arc reconstruction
        })
    
    # Serialize transitions
    for transition in transitions:
        self._clipboard.append({
            'type': 'transition',
            'name': transition.name,
            'x': transition.x,
            'y': transition.y,
            'width': transition.width,
            'height': transition.height,
            'horizontal': transition.horizontal,
            'transition_type': transition.transition_type,
            'rate': transition.rate,
            'delay': transition.delay,
            'id': id(transition)  # For arc reconstruction
        })
    
    # Serialize arcs (only if BOTH endpoints are selected)
    for arc in arcs:
        if arc.source in selected and arc.target in selected:
            arc_data = {
                'type': 'arc',
                'source_id': id(arc.source),
                'target_id': id(arc.target),
                'weight': arc.weight,
                'arc_type': arc.arc_type
            }
            
            # Handle curved arcs
            if hasattr(arc, 'is_curved') and arc.is_curved:
                arc_data['is_curved'] = True
                arc_data['handle_x'] = arc.handle_x
                arc_data['handle_y'] = arc.handle_y
            
            self._clipboard.append(arc_data)
```

**Features**:
- ✅ Copies places with tokens and capacity
- ✅ Copies transitions with all properties (type, rate, delay)
- ✅ Copies arcs only if **both endpoints are selected**
- ✅ Preserves curved arc geometry
- ✅ Preserves arc types (normal, inhibitor)
- ✅ Original objects remain unchanged

**Smart Arc Handling**:
If you select a place connected to multiple arcs but don't select the other endpoints, only the place is copied (arcs are excluded). This prevents creating dangling arcs.

---

## Cut (Ctrl+X)

**Key**: `Ctrl+X`

**Action**: Copies selected objects to clipboard, then deletes them

**Implementation** (`_cut_selection`, line ~2567):
```python
def _cut_selection(self, manager, widget):
    """Cut selected objects to clipboard."""
    # 1. First copy to clipboard
    self._copy_selection(manager)
    
    # 2. Then delete selected objects
    selected = manager.selection_manager.get_selected_objects()
    if selected:
        # Store delete data for undo
        delete_data = []
        for obj in selected:
            delete_data.append(manager.serialize_object_for_undo(obj))
        
        # Delete all selected objects
        for obj in selected:
            manager.delete_object(obj)
        
        # Push to undo stack
        if hasattr(manager, 'undo_manager') and delete_data:
            manager.undo_manager.push(DeleteOperation(delete_data, manager))
        
        widget.queue_draw()
```

**Features**:
- ✅ Combines copy + delete
- ✅ Supports undo (Ctrl+Z restores cut objects)
- ✅ Objects go to clipboard for pasting
- ✅ Original objects are removed

---

## Paste (Ctrl+V)

**Key**: `Ctrl+V`

**Action**: Pastes clipboard objects **at pointer position**

**Implementation** (`_paste_selection`, line ~2662):
```python
def _paste_selection(self, manager, widget, pointer_x=None, pointer_y=None):
    """Paste objects from clipboard at pointer position."""
    if not self._clipboard:
        return
    
    # Calculate clipboard bounding box center
    items_with_pos = [item for item in self._clipboard if 'x' in item and 'y' in item]
    clipboard_min_x = min(item['x'] for item in items_with_pos)
    clipboard_max_x = max(item['x'] for item in items_with_pos)
    clipboard_min_y = min(item['y'] for item in items_with_pos)
    clipboard_max_y = max(item['y'] for item in items_with_pos)
    clipboard_center_x = (clipboard_min_x + clipboard_max_x) / 2
    clipboard_center_y = (clipboard_min_y + clipboard_max_y) / 2
    
    # Get paste position (last pointer position tracked in motion events)
    if pointer_x is None or pointer_y is None:
        screen_center_x = manager.viewport_width / 2
        screen_center_y = manager.viewport_height / 2
        pointer_x, pointer_y = manager.screen_to_world(screen_center_x, screen_center_y)
    
    # Calculate offset to center clipboard at pointer
    offset_x = pointer_x - clipboard_center_x
    offset_y = pointer_y - clipboard_center_y
    
    # Clear current selection
    manager.clear_all_selections()
    
    # Map old IDs to new objects (for arc reconstruction)
    id_map = {}
    
    # Create places and transitions first
    for item in self._clipboard:
        if item['type'] == 'place':
            place = manager.add_place(
                item['x'] + offset_x,  # Apply offset
                item['y'] + offset_y,
                name=self._generate_unique_name(manager, item['name'])
            )
            place.tokens = item['tokens']
            place.capacity = item['capacity']
            place.radius = item['radius']
            id_map[item['id']] = place
            
            # Auto-select pasted objects
            place.selected = True
            manager.selection_manager.select(place, multi=True, manager=manager)
        
        elif item['type'] == 'transition':
            transition = manager.add_transition(
                item['x'] + offset_x,  # Apply offset
                item['y'] + offset_y,
                name=self._generate_unique_name(manager, item['name'])
            )
            transition.horizontal = item['horizontal']
            transition.width = item['width']
            transition.height = item['height']
            transition.transition_type = item['transition_type']
            transition.rate = item['rate']
            transition.delay = item['delay']
            id_map[item['id']] = transition
            
            # Auto-select pasted objects
            transition.selected = True
            manager.selection_manager.select(transition, multi=True, manager=manager)
    
    # Create arcs after all nodes exist
    for item in self._clipboard:
        if item['type'] == 'arc':
            source = id_map.get(item['source_id'])
            target = id_map.get(item['target_id'])
            
            if source and target:
                arc = manager.add_arc(source, target)
                arc.weight = item['weight']
                
                # Restore arc type
                if item.get('arc_type') == 'inhibitor':
                    from shypn.utils.arc_transform import convert_to_inhibitor
                    new_arc = convert_to_inhibitor(arc)
                    manager.replace_arc(arc, new_arc)
                    arc = new_arc
                
                # Restore curved arc geometry
                if item.get('is_curved'):
                    arc.is_curved = True
                    arc.handle_x = item['handle_x'] + offset_x
                    arc.handle_y = item['handle_y'] + offset_y
```

**Features**:
- ✅ **Pastes at pointer position** (not fixed offset!)
- ✅ Clipboard center is placed at pointer location
- ✅ Relative positions preserved
- ✅ New objects automatically selected (ready for immediate move)
- ✅ Names automatically made unique (P1 → P1_copy, etc.)
- ✅ Can paste multiple times from same clipboard
- ✅ Arc connections preserved
- ✅ Curved arc geometry preserved

**Pointer Tracking** (line ~1302):
```python
# Motion notify handler tracks pointer constantly
def _on_motion_notify(self, widget, event, manager):
    world_x, world_y = manager.screen_to_world(event.x, event.y)
    # Store last known pointer position for paste
    self._last_pointer_world_x = world_x
    self._last_pointer_world_y = world_y
    # ... rest of motion handling
```

**Smart Positioning**:
- Pointer position tracked in every motion event
- When you press Ctrl+V, objects appear where pointer is
- If no pointer data, uses canvas center (fallback)

---

## Workflow Examples

### Example 1: Copy a Subnet
```
1. Lasso or rectangle-select multiple places and transitions
2. Press Ctrl+C (copies to clipboard)
3. Move pointer to destination area
4. Press Ctrl+V (pastes centered at pointer)
5. Result: New subnet at pointer position, automatically selected
```

### Example 2: Move Objects to Another Area
```
1. Select objects (click, rectangle, or lasso)
2. Press Ctrl+X (cuts to clipboard, deletes originals)
3. Move pointer to new location
4. Press Ctrl+V (pastes at new location)
5. Result: Objects moved, preserving relative positions
```

### Example 3: Duplicate and Modify
```
1. Select transition with connected places
2. Press Ctrl+C (copies subnet)
3. Move pointer nearby
4. Press Ctrl+V (pastes at pointer)
5. Pasted objects already selected → can immediately drag to fine-tune position
6. Press Ctrl+V again → pastes another copy at current pointer position
```

### Example 4: Delete Selected
```
1. Multi-select objects (Ctrl+Click, rectangle, or lasso)
2. Press Delete
3. Objects removed (Ctrl+Z to undo if needed)
```

---

## Keyboard Shortcut Summary

| Key | Action | Objects | Undo Support |
|-----|--------|---------|--------------|
| **Delete** | Delete selected objects | All selected | ✅ Yes |
| **Ctrl+C** | Copy to clipboard | All selected | N/A (non-destructive) |
| **Ctrl+X** | Cut to clipboard | All selected | ✅ Yes |
| **Ctrl+V** | Paste at pointer | From clipboard | ❌ No (use Delete on pasted) |
| **Ctrl+Z** | Undo last operation | Last operation | N/A (undo itself) |
| **Ctrl+Y** or **Ctrl+Shift+Z** | Redo operation | Last undone | N/A (redo itself) |

---

## Additional Keyboard Shortcuts

### Escape (ESC)
- Cancel active lasso selection
- Cancel active transformation
- Cancel drag operation
- Exit edit mode
- Close context menu

### Selection Modifiers
- **No modifier**: Single select (clears previous)
- **Ctrl**: Multi-select (add/remove from selection)

---

## Technical Details

### Clipboard Implementation
- Internal clipboard (`self._clipboard`) stores serialized objects
- Not connected to system clipboard (OS copy/paste)
- Clipboard persists until application closes
- Can paste same content multiple times

### Undo System Integration
- Delete operations: ✅ Fully undoable
- Cut operations: ✅ Fully undoable (reconstructs deleted objects)
- Paste operations: ❌ Not directly undoable (delete pasted objects manually)
- Move operations: ✅ Undoable (through drag system)

### Arc Handling
- Arcs only copied if **both source and target are selected**
- Prevents dangling arcs in clipboard
- Arc connections rebuilt using ID mapping during paste
- Curved arc handles adjusted by same offset as endpoints

### Name Generation
- Pasted objects get unique names automatically
- Pattern: `original_name_copy`, `original_name_copy2`, etc.
- Prevents name collisions in model

### Pointer Position Tracking
- Updated on every motion event (`_on_motion_notify`)
- Stored in world coordinates (not screen coordinates)
- Used for context-aware paste positioning
- Fallback to canvas center if no pointer data

---

## Files Involved

**Main Implementation**:
- `src/shypn/helpers/model_canvas_loader.py`
  - `_on_key_press_event()` - Keyboard event handling (line ~1390)
  - `_copy_selection()` - Copy implementation (line ~2596)
  - `_cut_selection()` - Cut implementation (line ~2567)
  - `_paste_selection()` - Paste implementation (line ~2662)
  - `_on_motion_notify()` - Pointer tracking (line ~1290)

**Supporting Modules**:
- `src/shypn/edit/selection_manager.py` - Selection state management
- `src/shypn/edit/undo_operations.py` - DeleteOperation for undo
- `src/shypn/netobjs.py` - Place, Transition, Arc classes
- `src/shypn/utils/arc_transform.py` - Arc type conversion

---

## Implementation Quality

✅ **Complete feature set**
✅ **Smart arc handling** (only copy when both endpoints selected)
✅ **Pointer-aware paste** (pastes where you point)
✅ **Undo support** (delete and cut operations)
✅ **Auto-selection** (pasted objects ready for immediate adjustment)
✅ **Name uniqueness** (automatic name conflict resolution)
✅ **Geometry preservation** (curved arcs, relative positions)
✅ **Type preservation** (arc types, transition properties)

---

## Result

The keyboard shortcuts provide a **complete, professional editing experience**:
- Natural copy/cut/paste workflow
- Smart clipboard with arc intelligence
- Pointer-aware positioning (major UX improvement)
- Full undo support for destructive operations
- Preserves all object properties and relationships
