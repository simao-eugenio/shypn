# ARCHITECTURAL ANALYSIS: Canvas and Simulation Initialization Paths

## Date
October 15, 2025

## Critical Issue Identified

**User Alert**: "it must not have two ways for establishing canvas, simulation states, signaling and controls, they have to use the same path code"

**Current Problem**: Different initialization paths for:
1. Manually created canvases (File → New)
2. Imported canvases (SBML/KEGG import)
3. Loaded canvases (File → Open)

This leads to:
- ❌ Different behavior between manual and imported models
- ❌ Bugs that only appear in one path
- ❌ Difficult maintenance and debugging
- ❌ Inconsistent state initialization

## Current Architecture Analysis

### Path 1: Manual Canvas Creation (New Document)

**Sequence**:
```
User: File → New (or initial startup)
  ↓
ModelCanvasLoader.load()
  ↓
ModelCanvasLoader.add_document(filename="default")
  ├─> Create widgets (overlay, scrolled, drawing_area)
  ├─> Create tab label
  ├─> Add page to notebook
  └─> _setup_canvas_manager(drawing_area, filename="default")
      ├─> Create ModelCanvasManager(filename="default")
      ├─> manager.create_new_document(filename="default")  ← EMPTY model created
      ├─> Wire up event handlers
      ├─> Setup overlay manager
      └─> _setup_edit_palettes(overlay_widget, manager, ...)
          └─> Create SwissKnifePalette(mode='edit', model=manager)
              └─> SimulateToolsPaletteLoader(model=manager)
                  └─> SimulationController(model=manager)  ← With EMPTY model
                      ├─> ModelAdapter(manager)
                      ├─> behavior_cache = {}
                      ├─> transition_states = {}
                      └─> manager.register_observer(self._on_model_changed)

User: Adds places/transitions via UI
  ↓
manager.add_place(x, y)
  ├─> document_controller.add_place(...)
  ├─> manager._notify_observers('created', place)
  │   └─> SimulationController._on_model_changed('created', place)
  │       └─> model_adapter.invalidate_caches()  ← Cache invalidated
  └─> manager.mark_dirty()

User: Run Simulation
  ↓
SimulationController.step()
  ├─> _simulation_started = True  ← First step sets flag
  ├─> _update_enablement_states()  ← Initializes all behaviors
  │   ├─> For each transition:
  │   │   ├─> behavior = _get_behavior(transition)  ← Creates behavior if needed
  │   │   │   ├─> Check if _simulation_started  ← FALSE during first step!
  │   │   │   └─> Don't initialize enablement yet
  │   │   └─> set_enablement_time(self.time)  ← Proper initialization
  │   └─> ...
  └─> Fire transitions...
```

**Result**: ✓ Works correctly (after our fixes)

### Path 2: Imported Canvas Creation (SBML/KEGG)

**Sequence**:
```
User: Import → SBML → Fetch/Parse
  ↓
sbml_import_panel._quick_load_to_canvas()
  ├─> Convert pathway to DocumentModel
  └─> model_canvas.add_document(filename=pathway_name)
      ├─> Create widgets
      ├─> _setup_canvas_manager(drawing_area, filename=pathway_name)
      │   ├─> Create ModelCanvasManager(filename=pathway_name)
      │   ├─> manager.create_new_document(filename=pathway_name)  ← EMPTY model
      │   └─> _setup_edit_palettes(...)
      │       └─> SwissKnifePalette → SimulationController(EMPTY model)
      │           ├─> time = 0.0
      │           ├─> _simulation_started = False
      │           └─> register_observer() ✓
      └─> Return (page_index, drawing_area)
  
  ↓ Back in sbml_import_panel._quick_load_to_canvas()
  
  ├─> manager = model_canvas.get_canvas_manager(drawing_area)
  ├─> manager.places = list(document_model.places)  ← Objects loaded AFTER
  ├─> manager.transitions = list(document_model.transitions)
  ├─> manager.arcs = list(document_model.arcs)
  ├─> manager.document_controller.set_change_callback(...)
  └─> For each object:
      └─> manager._notify_observers('created', obj)
          └─> SimulationController._on_model_changed('created', obj)
              └─> model_adapter.invalidate_caches()  ← Cache invalidated ✓

User: Run Simulation
  ↓
SimulationController.step()
  ├─> _simulation_started = True  ← First step sets flag
  ├─> _update_enablement_states()
  │   ├─> For each imported transition:
  │   │   ├─> behavior = _get_behavior(transition)
  │   │   │   ├─> Behavior not in cache yet
  │   │   │   ├─> Create behavior
  │   │   │   ├─> Check if _simulation_started
  │   │   │   │   └─> TRUE now! (set at step start)
  │   │   │   └─> Initialize enablement with current time ✓
  │   │   └─> set_enablement_time() also called from _update_enablement_states
  │   └─> ...
  └─> Fire transitions...
```

**Result**: ✓ Should work (after our fixes), but TIMING ISSUE!

### Path 3: Loaded Canvas (File → Open)

**Sequence** (similar to import, but deserializes from JSON):
```
User: File → Open
  ↓
file_explorer_panel.load_document()
  ├─> Deserialize DocumentModel from JSON
  └─> Similar to import path...
```

**Result**: ✓ Same as import path

## Problems Identified

### Problem 1: Timing Race Condition

**Issue**: `_simulation_started` flag is set at the START of `step()`, but behaviors might be created DURING `_update_enablement_states()` which happens AFTER the flag is set.

**Sequence**:
```
step() called:
  1. _simulation_started = True  ← Flag set
  2. _update_enablement_states() called
     3. For transition T1:
        4. behavior = _get_behavior(T1)
           5. Behavior not in cache
           6. Create new behavior
           7. Check if _simulation_started  ← TRUE!
           8. Initialize enablement with current time
        9. set_enablement_time() called AGAIN from _update_enablement_states
           10. For stochastic: samples NEW delay, overwriting step 8!
```

**Result**: Stochastic transitions get enablement set TWICE during first step!

### Problem 2: Dual Initialization Logic

**Current Code**:
1. `_get_behavior()` initializes enablement if `_simulation_started` is True
2. `_update_enablement_states()` ALSO initializes enablement

**This creates**:
- Redundant initialization
- Potential for double-sampling in stochastic transitions
- Complex logic that's hard to maintain

### Problem 3: Different Object Loading Methods

**Manual creation**:
```python
manager.add_place(x, y)
  → document_controller.add_place(x, y)
  → Returns place object
  → Adds to manager.places automatically
  → Notifies observers automatically
```

**Import/Load**:
```python
manager.places = list(document_model.places)  ← Direct assignment
manager.transitions = list(document_model.transitions)
manager.arcs = list(document_model.arcs)
  → No automatic notification
  → Must manually call _notify_observers() for each
```

**Problem**: Two different mechanisms for adding objects!

## Root Cause

**FUNDAMENTAL DESIGN ISSUE**: The system was designed for manual object creation (one at a time via UI), but import/load operations bypass this mechanism by directly assigning lists.

## Unified Solution Design

### Principle: Single Responsibility

**Rule**: All object additions MUST go through the same code path:
- Manual creation → `manager.add_place()`
- Import → Use `manager.add_place()` for each imported place
- Load → Use `manager.add_place()` for each loaded place

### Principle: Lazy Initialization

**Rule**: Behaviors should ONLY be initialized by `_update_enablement_states()`, never by `_get_behavior()`.

**Rationale**:
- Single point of initialization
- Consistent timing
- No double-initialization
- Clear separation: creation vs initialization

### Principle: Observer Pattern Consistency

**Rule**: Objects notify observers automatically when added, regardless of how they're added.

## Implementation Plan

### Phase 1: Remove Dual Initialization ✓ IN PROGRESS

**Change**: Remove enablement initialization from `_get_behavior()`

**Status**: Currently using `_simulation_started` flag, but this creates race condition

**Fix**: Remove ALL initialization from `_get_behavior()`, rely entirely on `_update_enablement_states()`

### Phase 2: Unify Object Loading

**Change**: Create unified loading method in ModelCanvasManager

**New Method**:
```python
def load_objects(self, places, transitions, arcs):
    """Load objects into the model (for import/deserialize operations).
    
    This method ensures all objects are added through the proper channels
    with automatic observer notification.
    
    Args:
        places: List of Place objects to add
        transitions: List of Transition objects to add
        arcs: List of Arc objects to add
    """
    # Add places (triggers notifications automatically)
    for place in places:
        # Use internal add without creation (object already exists)
        self.places.append(place)
        self._notify_observers('created', place)
    
    # Add transitions
    for transition in transitions:
        self.transitions.append(transition)
        self._notify_observers('created', transition)
    
    # Add arcs
    for arc in arcs:
        self.arcs.append(arc)
        arc._manager = self  # Set manager reference
        self._notify_observers('created', arc)
    
    # Update ID counters
    if places:
        self._next_place_id = max(p.id for p in self.places) + 1
    if transitions:
        self._next_transition_id = max(t.id for t in self.transitions) + 1
    if arcs:
        self._next_arc_id = max(a.id for a in self.arcs) + 1
    
    # Mark dirty for redraw
    self.mark_dirty()
```

**Update All Import/Load Code**:
```python
# OLD (direct assignment):
manager.places = list(document_model.places)
manager.transitions = list(document_model.transitions)
manager.arcs = list(document_model.arcs)
# Manual notification loop...

# NEW (unified method):
manager.load_objects(
    places=document_model.places,
    transitions=document_model.transitions,
    arcs=document_model.arcs
)
```

### Phase 3: Simplify Behavior Creation

**Change**: Make `_get_behavior()` pure creation, no initialization

```python
def _get_behavior(self, transition):
    """Get or create behavior instance for a transition.
    
    IMPORTANT: This method ONLY creates behaviors, it does NOT initialize
    their enablement state. Initialization is handled by _update_enablement_states().
    """
    if transition.id in self.behavior_cache:
        cached_behavior = self.behavior_cache[transition.id]
        cached_type = cached_behavior.get_type_name()
        current_type = getattr(transition, 'transition_type', 'continuous')
        
        # Type name mapping
        type_name_map = {
            'Immediate': 'immediate',
            'Timed (TPN)': 'timed',
            'Stochastic (FSPN)': 'stochastic',
            'Continuous (SHPN)': 'continuous'
        }
        cached_type_normalized = type_name_map.get(cached_type, cached_type.lower())
        
        if cached_type_normalized != current_type:
            # Type changed, invalidate and recreate
            if hasattr(cached_behavior, 'clear_enablement'):
                cached_behavior.clear_enablement()
            del self.behavior_cache[transition.id]
            if transition.id in self.transition_states:
                del self.transition_states[transition.id]
    
    if transition.id not in self.behavior_cache:
        # Create behavior (no initialization here!)
        behavior = behavior_factory.create_behavior(transition, self.model_adapter)
        self.behavior_cache[transition.id] = behavior
        # That's it! Let _update_enablement_states() handle initialization
    
    return self.behavior_cache[transition.id]
```

**Rationale**:
- Single responsibility: creation only
- Initialization happens in _update_enablement_states()
- No timing issues
- No double initialization
- Works the same for manual and imported models

## Testing Strategy

### Test 1: Manual Creation
```
1. Create new canvas
2. Add places and transitions manually
3. Run simulation
4. Verify: All types work ✓
```

### Test 2: SBML Import
```
1. Import SBML model
2. Run simulation immediately
3. Verify: All types work ✓
4. Switch some transition types
5. Run simulation again
6. Verify: Type switching works ✓
```

### Test 3: File Load
```
1. Load saved .shypn file
2. Run simulation
3. Verify: All types work ✓
```

### Test 4: Mixed Operations
```
1. Import SBML model
2. Add more transitions manually
3. Run simulation
4. Verify: Both imported and manual work ✓
```

## Benefits of Unified Approach

### ✅ Single Code Path
- All object additions use same mechanism
- Easier to maintain
- Fewer bugs

### ✅ Consistent Behavior
- Manual and imported models behave identically
- No special cases

### ✅ Simpler Logic
- One initialization point (_update_enablement_states)
- Clear separation of concerns

### ✅ Easier Debugging
- Single point to add logging
- Single point to fix issues

### ✅ Better Architecture
- Follows Single Responsibility Principle
- Proper separation: creation vs initialization
- Observer pattern used consistently

## Implementation Priority

1. **HIGH**: Remove initialization from `_get_behavior()` ← Fixes timing issue
2. **MEDIUM**: Create `load_objects()` method in ModelCanvasManager
3. **MEDIUM**: Update SBML import to use `load_objects()`
4. **MEDIUM**: Update KEGG import to use `load_objects()`
5. **MEDIUM**: Update file loading to use `load_objects()`
6. **LOW**: Add comprehensive logging for debugging

## Conclusion

The current dual-path architecture is a source of bugs and complexity. By unifying the code paths and clarifying responsibilities (creation vs initialization), we achieve:

- ✅ Simpler, more maintainable code
- ✅ Consistent behavior across all scenarios
- ✅ Fewer edge cases and timing issues
- ✅ Better adherence to design principles

**Next Steps**: Implement Phase 1 (remove dual initialization) immediately to fix the timing race condition.
