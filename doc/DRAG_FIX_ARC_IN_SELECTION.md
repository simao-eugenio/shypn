# Fix for Drag Not Working When Arc in Selection

**Date**: October 3, 2025  
**Issue**: Group doesn't drag when there's an arc in the selected group  
**Status**: ✅ FIXED

## Problem

When selecting multiple objects including an arc (via rectangle selection or Ctrl+click), trying to drag the group would fail silently - nothing would move.

### Scenario:
1. User creates Place P1, Transition T1, and Arc A1 connecting them
2. User selects all three (rectangle selection)
3. User clicks on P1 or T1 to drag the group
4. Nothing moves ✗

### Root Cause:

**Arcs don't have `.x` and `.y` coordinates!**

- **Place/Transition**: Have `.x` and `.y` attributes (world coordinates)
- **Arc**: Has `.source` and `.target` references (follows endpoints)

The `DragController` tries to:
1. Store initial positions: `self._initial_positions[id(obj)] = (obj.x, obj.y)`
2. Update positions: `obj.x = new_x; obj.y = new_y`

When an Arc is in the list, accessing `obj.x` and `obj.y` **fails** (AttributeError or returns None), causing the drag to silently fail.

**Code Flow**:
```
Click on selected P1 (with P1, T1, A1 all selected)
  ↓
get_selected_objects() → returns [P1, T1, A1]
  ↓
start_drag([P1, T1, A1], x, y)
  ↓
DragController stores initial positions
  for P1: (p1.x, p1.y) ✓
  for T1: (t1.x, t1.y) ✓
  for A1: (a1.x, a1.y) ✗ Arc doesn't have x,y!
  ↓
Drag initialization FAILS silently
  ↓
update_drag() does nothing
  ↓
Objects don't move ✗
```

## Solution

### Filter Out Non-Draggable Objects

In `SelectionManager.start_drag()`, filter the selected objects to only include draggable types (Places and Transitions):

```python
def start_drag(self, clicked_obj, screen_x: float, screen_y: float, manager):
    """Start dragging selected objects if clicking on a selected object."""
    if clicked_obj and clicked_obj.selected:
        self.__init_drag_controller()
        selected_objs = self.get_selected_objects(manager)
        
        # Filter to only draggable objects (Places and Transitions)
        # Arcs don't have x,y coordinates - they follow their source/target
        from shypn.netobjs.place import Place
        from shypn.netobjs.transition import Transition
        draggable_objs = [obj for obj in selected_objs 
                        if isinstance(obj, (Place, Transition))]
        
        # Debug output
        print(f"DEBUG start_drag: selected_objs count={len(selected_objs)}, draggable count={len(draggable_objs)}")
        
        # Only start drag if there are draggable objects
        if draggable_objs:
            self._drag_controller.start_drag(draggable_objs, screen_x, screen_y)
            return True
    return False
```

**Location**: `src/shypn/edit/selection_manager.py`, `start_drag()` method (~line 233)

### Why This Works:

1. **Arcs are excluded** from the drag operation
2. **Places and Transitions** are dragged normally
3. **Arcs automatically follow** their source/target when those move
4. **Arc rendering** updates automatically (arcs reference source/target objects)

### Arc Position Updates:

Arcs don't need explicit position updates because:
- Arc stores references: `self.source` and `self.target`
- Arc rendering calculates positions: `start_x = self.source.x`, `start_y = self.source.y`
- When Place/Transition moves, arc endpoints update automatically
- No need to drag arcs explicitly!

## Files Modified

1. **`src/shypn/edit/selection_manager.py`**
   - Added filtering in `start_drag()` to exclude arcs
   - Only Places and Transitions are passed to DragController
   - Lines modified: ~10 lines

## Testing

### Test Case 1: Place + Transition + Arc (All Selected)
1. Create P1, T1, and Arc A1: P1 → T1
2. Rectangle select all three (P1, T1, A1 selected)
3. Click on P1 and drag
4. ✅ EXPECTED: P1 and T1 move together
5. ✅ EXPECTED: A1 (arc) follows automatically (endpoints update)
6. ✅ EXPECTED: Arc arrow remains connected to P1 and T1

### Test Case 2: Multiple Objects with Multiple Arcs
1. Create: P1, P2, T1, T2
2. Create arcs: A1: P1→T1, A2: T1→P2, A3: P2→T2
3. Rectangle select all (6 objects: 2 places, 2 transitions, 3 arcs)
4. Click on any place/transition and drag
5. ✅ EXPECTED: All 4 nodes (P1, P2, T1, T2) move together
6. ✅ EXPECTED: All 3 arcs follow automatically
7. ✅ EXPECTED: Network structure preserved

### Test Case 3: Only Arc Selected
1. Create P1, T1, A1: P1→T1
2. Click only on arc A1 (arc selected, P1 and T1 not selected)
3. Try to drag arc
4. ✅ EXPECTED: Nothing happens (can't drag arc alone)
5. ℹ️ NOTE: This is correct behavior - arcs don't have independent position

### Test Case 4: Place Without Arc
1. Create P1 (no arcs)
2. Select P1
3. Drag P1
4. ✅ EXPECTED: Works normally (no arcs to worry about)

## Debug Output

When dragging with arcs in selection, you'll see:

```
DEBUG start_drag: clicked=P1
DEBUG start_drag: selected_objs count=3, draggable count=2
DEBUG start_drag: IDs=[139876543210, 139876543211]
DEBUG start_drag: names=['P1', 'T1']
DEBUG DragController.start_drag: Received 2 objects, IDs=[139876543210, 139876543211]
```

**Key observations**:
- `selected_objs count=3` (includes arc)
- `draggable count=2` (excludes arc)
- Only 2 objects passed to DragController
- Arc A1 not in the list

## Design Rationale

### Why Not Make Arcs Draggable?

**Option 1: Add x,y to Arcs** (❌ Bad)
- Arc position is derived from source/target
- Adding x,y would create redundancy and inconsistency
- Would need to sync arc position with endpoints constantly

**Option 2: Give Arcs Special Drag Handling** (❌ Complex)
- Would need to detect when arc is dragged
- Would need to move both source and target
- Conflicts with existing drag of individual nodes

**Option 3: Filter Out Arcs from Drag** (✅ Best)
- Simple and clean
- Arcs follow automatically
- No redundant data
- Preserves single responsibility

### Arc Selection vs Dragging:

**Arcs CAN be selected** (for deletion, property editing, etc.)
- Select arc → show properties
- Select arc → delete with Del key
- Select arc → change color/weight

**Arcs CANNOT be dragged independently**
- Arc has no position of its own
- Arc position = function(source.x, source.y, target.x, target.y)
- Dragging arc would be ambiguous (move source? target? both?)

**Dragging nodes with arcs selected**:
- Nodes move → arcs follow automatically
- Arc selection state preserved
- Network topology preserved

## Object Type Hierarchy

```
PetriNetObject (base)
  ├─ Place (has x, y) → DRAGGABLE ✓
  ├─ Transition (has x, y) → DRAGGABLE ✓
  └─ Arc (has source, target) → NOT DRAGGABLE ✗
```

**Draggable**: Objects with independent position (x, y coordinates)
**Non-Draggable**: Objects with derived position (follows other objects)

## Related Functionality

### Selection Works for All Objects:
- ✅ Select Place
- ✅ Select Transition
- ✅ Select Arc
- ✅ Multi-select any combination

### Drag Only Works for Positioned Objects:
- ✅ Drag Place
- ✅ Drag Transition  
- ✅ Drag multiple Places/Transitions
- ❌ Drag Arc (filtered out)

### Rectangle Selection Behavior:
- Selects ALL objects in rectangle (including arcs) ✓
- Dragging moves only Places/Transitions ✓
- Arcs follow automatically ✓
- Network connectivity preserved ✓

## Future Enhancements

### Control Point Dragging (Future):
For arcs with control points (curved arcs), could implement:
- Drag control points individually
- Reshape arc curve
- Keep endpoints fixed

This would be a DIFFERENT operation from node dragging:
- Drag node → move node, arc follows
- Drag arc control point → reshape arc, endpoints fixed

---

**Summary**: Fixed drag failure when arcs in selection by filtering out arcs from draggable objects list. Places and Transitions drag normally, arcs follow automatically by referencing their source/target.
