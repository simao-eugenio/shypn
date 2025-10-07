# Floating Buttons Wiring Status

## Overview
This document details the implementation status of the 7 floating buttons that appear when pressing [E] in edit mode.

## Button Layout
```
[P] [T] [A]    GAP    [S] [L]    GAP    [U] [R]
 Tools Group         Selection      Operations
```

## Implementation Status

### ✅ FULLY IMPLEMENTED: Tool Buttons (P, T, A, S)

#### [P] Place Button
- **Status**: ✅ **FULLY WORKING**
- **Functionality**: Creates places on canvas
- **Wiring**: 
  - Calls `canvas_manager.set_tool('place')`
  - Toggle button with mutual exclusion
  - Emits 'tool-changed' signal
- **Test**: Click [P], then click on canvas - should create places

#### [T] Transition Button
- **Status**: ✅ **FULLY WORKING**
- **Functionality**: Creates transitions on canvas
- **Wiring**:
  - Calls `canvas_manager.set_tool('transition')`
  - Toggle button with mutual exclusion
  - Emits 'tool-changed' signal
- **Test**: Click [T], then click on canvas - should create transitions

#### [A] Arc Button
- **Status**: ✅ **FULLY WORKING**
- **Functionality**: Creates arcs between objects
- **Wiring**:
  - Calls `canvas_manager.set_tool('arc')`
  - Toggle button with mutual exclusion
  - Emits 'tool-changed' signal
- **Test**: Click [A], then click source object, then target - should create arc

#### [S] Select Button
- **Status**: ✅ **FULLY WORKING**
- **Functionality**: Activates rectangle selection mode
- **Wiring**:
  - Calls `canvas_manager.clear_tool()` (returns to pan/select mode)
  - Calls `edit_operations.activate_select_mode()`
  - Toggle button with mutual exclusion
- **Test**: Click [S], then drag on canvas - should create selection rectangle

---

### ⚠️ PARTIALLY IMPLEMENTED: Selection Tools

#### [L] Lasso Button
- **Status**: ⚠️ **CODE EXISTS, NEEDS CANVAS INTEGRATION**
- **Current Implementation**:
  - ✅ Button click handler (`_on_lasso_clicked`)
  - ✅ Calls `edit_operations.activate_lasso_mode()`
  - ✅ LassoSelector class exists with full implementation
  - ❌ **NOT CONNECTED TO CANVAS MOUSE EVENTS**
  
- **What Works**:
  - Button clicks and logs activation
  - Lasso selector instance is created
  - Has rendering and point-in-polygon algorithms
  
- **What's Missing**:
  - Canvas mouse event handlers don't trigger lasso drawing
  - Need to wire lasso selector to canvas button-press/motion/release events
  - Need to integrate lasso rendering into canvas draw cycle
  
- **Required Integration** (in canvas event handlers):
  ```python
  # On mouse button press
  if lasso_mode_active:
      lasso_selector.start_lasso(world_x, world_y)
  
  # On mouse motion (dragging)
  if lasso_mode_active and dragging:
      lasso_selector.add_point(world_x, world_y)
      queue_draw()  # Redraw to show lasso path
  
  # On mouse button release
  if lasso_mode_active:
      lasso_selector.finish_lasso()  # Selects objects inside
      queue_draw()
  
  # In draw callback
  if lasso_selector and lasso_selector.is_active:
      lasso_selector.render_lasso(cr, zoom)
  ```

- **Files to Modify**:
  - `src/shypn/canvas/model_canvas_loader.py` or similar canvas event handler
  - Add lasso mode checking in mouse event handlers
  - Add lasso rendering in draw callback

---

### ⚠️ PARTIALLY IMPLEMENTED: Operation Buttons

#### [U] Undo Button
- **Status**: ⚠️ **CODE EXISTS, NEEDS OPERATION TRACKING**
- **Current Implementation**:
  - ✅ Button click handler (`_on_undo_clicked`)
  - ✅ Calls `edit_operations.undo()`
  - ✅ Button sensitivity updates based on undo stack state
  - ✅ EditOperations has undo/redo stack structure
  - ❌ **OPERATIONS NOT BEING PUSHED TO UNDO STACK**
  
- **What Works**:
  - Button clicks and logs "Undo triggered"
  - Undo stack exists and has push/pop logic
  - Button is disabled when stack is empty (correct state)
  
- **What's Missing**:
  - Canvas operations (create place, transition, arc, delete) don't push to undo stack
  - Need to create Operation classes for each action
  - Need to call `edit_operations.push_operation(operation)` after each action
  
- **Required Implementation**:
  ```python
  # Example: CreatePlaceOperation
  class CreatePlaceOperation:
      def __init__(self, canvas_manager, place):
          self.canvas_manager = canvas_manager
          self.place = place
          self.place_data = {...}  # Store place state
      
      def undo(self):
          self.canvas_manager.remove_place(self.place)
      
      def redo(self):
          self.canvas_manager.add_place_from_data(self.place_data)
  
  # After creating a place:
  operation = CreatePlaceOperation(canvas_manager, new_place)
  edit_operations.push_operation(operation)
  ```

- **Operations to Implement**:
  - `CreatePlaceOperation`
  - `CreateTransitionOperation`
  - `CreateArcOperation`
  - `DeleteObjectOperation`
  - `MoveObjectOperation`
  - `ModifyPropertyOperation`

- **Files to Modify**:
  - `src/shypn/edit/operations/` (new folder)
  - Create operation classes for each action type
  - Modify canvas manager methods to push operations
  - `src/shypn/data/model_canvas_manager.py` - add operation tracking

#### [R] Redo Button
- **Status**: ⚠️ **SAME AS UNDO - NEEDS OPERATION TRACKING**
- **Current Implementation**:
  - ✅ Button click handler (`_on_redo_clicked`)
  - ✅ Calls `edit_operations.redo()`
  - ✅ Button sensitivity updates based on redo stack state
  - ✅ Redo stack cleared when new operation added (correct behavior)
  - ❌ **OPERATIONS NOT BEING PUSHED TO UNDO STACK**
  
- **What Works**: Same as Undo
- **What's Missing**: Same as Undo
- **Required Implementation**: Same as Undo (operations work for both)

---

## Current File Structure

### Fully Implemented Files
- ✅ `src/shypn/helpers/floating_buttons_manager.py` - Button creation and click handlers
- ✅ `src/shypn/canvas/canvas_overlay_manager.py` - Button overlay management
- ✅ `src/shypn/helpers/edit_palette_loader.py` - [E] button toggle control
- ✅ `src/shypn/edit/edit_operations.py` - Operation stack structure
- ✅ `src/shypn/edit/lasso_selector.py` - Lasso algorithm implementation

### Files Needing Modification
- ⚠️ **Canvas event handlers** - Add lasso mode support
- ⚠️ **Canvas manager methods** - Add operation tracking
- ❌ **Operation classes** - Need to be created

---

## Testing Checklist

### Currently Working (Test These)
- [ ] Press [E] - buttons appear
- [ ] Click [P] - place tool activates
- [ ] Click on canvas with [P] active - place is created
- [ ] Click [T] - transition tool activates
- [ ] Click on canvas with [T] active - transition is created
- [ ] Click [A] - arc tool activates
- [ ] Click source then target with [A] active - arc is created
- [ ] Click [S] - select mode activates
- [ ] Drag on canvas with [S] active - selection rectangle appears

### Not Yet Working (Expected Behavior)
- [ ] Click [L] - lasso mode activates (logs, but no visual feedback)
- [ ] Drag on canvas with [L] active - lasso path draws (NOT IMPLEMENTED)
- [ ] Release mouse with lasso - objects inside are selected (NOT IMPLEMENTED)
- [ ] Create object, click [U] - object is removed (NOT IMPLEMENTED - stack empty)
- [ ] Click [U] then [R] - object reappears (NOT IMPLEMENTED - stack empty)
- [ ] [U] and [R] buttons enable/disable based on history (PARTIALLY - always disabled currently)

---

## Next Steps (Priority Order)

### Priority 1: Undo/Redo Operations ⭐ MOST IMPORTANT
**Why**: Undo/Redo is critical functionality and affects all editing operations

1. Create operation class hierarchy:
   ```
   src/shypn/edit/operations/
   ├── __init__.py
   ├── base_operation.py (abstract base)
   ├── create_place_operation.py
   ├── create_transition_operation.py
   ├── create_arc_operation.py
   ├── delete_object_operation.py
   └── move_object_operation.py
   ```

2. Modify `ModelCanvasManager` methods:
   - `add_place()` - push CreatePlaceOperation
   - `add_transition()` - push CreateTransitionOperation
   - `add_arc()` - push CreateArcOperation
   - `delete_object()` - push DeleteObjectOperation
   - Any move/modify methods - push appropriate operations

3. Wire EditOperations to each canvas:
   - Ensure each canvas has reference to its edit_operations
   - Operations pushed immediately after action completes

4. Test workflow:
   - Create place → [U] button enables
   - Click [U] → place disappears, [R] button enables
   - Click [R] → place reappears, [U] button enables

### Priority 2: Lasso Selection Integration
**Why**: Useful feature but less critical than undo/redo

1. Modify canvas mouse event handlers:
   - Add lasso mode check in button-press-event
   - Add lasso drawing in motion-notify-event
   - Add lasso finish in button-release-event

2. Add lasso rendering:
   - Call `lasso_selector.render_lasso(cr, zoom)` in draw callback
   - Only when lasso is active

3. Test workflow:
   - Click [L] → mode activates
   - Drag on canvas → blue dashed path follows mouse
   - Release → objects inside path are selected

### Priority 3: Polish and Refinement
1. Add keyboard shortcuts:
   - Ctrl+Z for Undo
   - Ctrl+Shift+Z for Redo
   - Escape to cancel lasso/tools

2. Add visual feedback:
   - Highlight active tool button
   - Show cursor changes for each tool
   - Toast notifications for operations

3. Add more operations:
   - Group/ungroup
   - Duplicate
   - Align tools

---

## Summary

**Working Now**: P, T, A, S buttons (4/7 = 57%)
**Needs Canvas Integration**: L button (1/7 = 14%)  
**Needs Operation System**: U, R buttons (2/7 = 29%)

**Total Implementation**: ~60% complete (buttons exist and click, but some need system integration)

**Blocking Issues**:
1. ❌ No operation classes created yet → U/R always disabled
2. ❌ Canvas doesn't track lasso mode → L clicks but doesn't draw

**Recommendation**: Implement undo/redo operations first (Priority 1), then lasso integration (Priority 2).
