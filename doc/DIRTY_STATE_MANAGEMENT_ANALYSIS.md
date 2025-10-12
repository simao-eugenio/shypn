# Dirty State Management Analysis & Fix Plan

**Date**: October 11, 2025  
**Issue**: Object deletion/transformation doesn't properly trigger dirty state and update dependent systems

---

## Problem Statement

Currently, object **creation** triggers dirty state (`mark_dirty()`) and document modification (`mark_modified()`), but **deletion** and **transformation** operations have gaps:

1. **Deletion Operations**: While they call `mark_dirty()` and `mark_modified()`, they don't propagate changes to:
   - Analysis panels (selected objects list becomes stale)
   - Simulation data structures (behaviors reference deleted objects)
   - UI components (context menus, search results)

2. **Transformation Operations**: Arc type changes don't trigger:
   - Simulation behavior recalculation
   - Analysis panel updates
   - Validation checks

3. **Flow Path Issues**:
   - No notification system for dependent components
   - Analysis panels hold direct object references (become invalid on deletion)
   - No automatic cleanup of stale references

---

## Current Implementation

### What Works ✅

**Object Creation** (`model_canvas_manager.py`):
```python
def add_place(self, x, y, label="", tokens=0):
    place = Place(...)
    self.places.append(place)
    self.mark_modified()  # ✅ Marks document modified
    self.mark_dirty()     # ✅ Marks canvas for redraw
    return place
```

**Object Deletion** (`model_canvas_manager.py`):
```python
def remove_place(self, place):
    if place in self.places:
        # Remove connected arcs
        self.arcs = [arc for arc in self.arcs 
                    if arc.source != place and arc.target != place]
        self.places.remove(place)
        self.mark_modified()  # ✅ Marks document modified
        self.mark_dirty()     # ✅ Marks canvas for redraw
```

### What's Missing ❌

1. **No notification to dependent systems**:
   - Analysis panels still reference deleted objects
   - Simulation controller doesn't clean up behaviors
   - Search results become stale

2. **No validation cascade**:
   - Arcs remain in analysis lists after node deletion
   - Transition behaviors reference deleted places
   - UI elements not updated

3. **Arc transformation not tracked**:
   - Changing arc type doesn't trigger behavior recalculation
   - No validation that new arc type is valid for transition type

---

## Affected Systems

### 1. Analysis Panels

**Issue**: Hold direct object references in `selected_objects` list

**File**: `src/shypn/analyses/plot_panel.py`
```python
class AnalysisPlotPanel:
    def __init__(self, object_type, data_collector):
        self.selected_objects: List[Any] = []  # ❌ Direct references
        
    def add_object(self, obj):
        self.selected_objects.append(obj)  # ❌ Stores reference
```

**Problem**: If object is deleted from model, `selected_objects` contains dangling reference

**Symptoms**:
- List shows deleted objects
- Trying to plot deleted object causes errors
- Remove button references invalid object

### 2. Simulation Controller

**Issue**: Behaviors cache object references

**File**: `src/shypn/engine/simulation/controller.py`
```python
class SimulationController:
    def __init__(self, model):
        self._behaviors = {}  # Maps transition.id → Behavior instance
        self._initialize_behaviors()
```

**Problem**: If place/transition deleted, behaviors reference invalid objects

### 3. Context Menus & UI

**Issue**: Context menu items reference objects that may be deleted

**File**: `src/shypn/analyses/context_menu_handler.py`
```python
def add_analysis_menu_items(self, menu, obj):
    menu_item = Gtk.MenuItem(label=f"Add to Analysis")
    menu_item.connect("activate", lambda w: self._on_add_to_analysis_clicked(obj, panel))
    # ❌ If obj deleted, callback references invalid object
```

---

## Solution Design

### Core Principle: **Event-Driven Notification System**

Add observer pattern to propagate model changes to all dependent systems.

### Architecture

```
ModelCanvasManager
    ↓ notify_observers()
    ↓
    ├─→ Analysis Panels (clean stale references)
    ├─→ Simulation Controller (rebuild behaviors)
    ├─→ Document Manager (mark dirty)
    └─→ UI Components (refresh displays)
```

---

## Implementation Plan

### Phase 1: Add Observer Pattern to ModelCanvasManager ✅

**File**: `src/shypn/data/model_canvas_manager.py`

Add notification system:

```python
class ModelCanvasManager:
    def __init__(self, ...):
        # ... existing code ...
        self._observers = []  # List of observer callbacks
    
    def register_observer(self, callback):
        """Register callback for model changes.
        
        Args:
            callback: Function(event_type, obj) where:
                event_type: 'created' | 'deleted' | 'modified' | 'transformed'
                obj: Affected object (place, transition, arc)
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def unregister_observer(self, callback):
        """Unregister observer callback."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, event_type: str, obj, old_value=None, new_value=None):
        """Notify all observers of a model change.
        
        Args:
            event_type: Type of change ('created', 'deleted', 'modified', 'transformed')
            obj: Affected object
            old_value: Old value (for transformations)
            new_value: New value (for transformations)
        """
        for callback in self._observers:
            try:
                callback(event_type, obj, old_value, new_value)
            except Exception as e:
                print(f"Observer callback error: {e}")
```

Update operations to notify:

```python
def add_place(self, x, y, label="", tokens=0):
    place = Place(...)
    self.places.append(place)
    self.mark_modified()
    self.mark_dirty()
    self._notify_observers('created', place)  # ← ADD THIS
    return place

def remove_place(self, place):
    if place in self.places:
        # Remove connected arcs
        affected_arcs = [arc for arc in self.arcs 
                        if arc.source == place or arc.target == place]
        
        for arc in affected_arcs:
            self._notify_observers('deleted', arc)  # ← Notify arc deletion
        
        self.arcs = [arc for arc in self.arcs 
                    if arc.source != place and arc.target != place]
        
        self.places.remove(place)
        self.mark_modified()
        self.mark_dirty()
        self._notify_observers('deleted', place)  # ← ADD THIS
```

### Phase 2: Update Analysis Panels to Observe Changes ✅

**File**: `src/shypn/analyses/plot_panel.py`

Add cleanup for deleted objects:

```python
class AnalysisPlotPanel(Gtk.Box):
    def __init__(self, object_type, data_collector):
        super().__init__(...)
        # ... existing code ...
        self._cleanup_timer_id = GLib.timeout_add(1000, self._cleanup_stale_objects)
    
    def register_with_model(self, model_manager):
        """Register to observe model changes.
        
        Args:
            model_manager: ModelCanvasManager instance
        """
        self.model_manager = model_manager
        model_manager.register_observer(self._on_model_changed)
    
    def _on_model_changed(self, event_type, obj, old_value=None, new_value=None):
        """Handle model change notifications.
        
        Args:
            event_type: 'created' | 'deleted' | 'modified' | 'transformed'
            obj: Affected object
            old_value: Old value (for transformations)
            new_value: New value (for transformations)
        """
        if event_type == 'deleted':
            # Check if deleted object is in our selection
            if isinstance(obj, (Place, Transition, Arc)):
                self._remove_if_selected(obj)
        
        elif event_type == 'transformed':
            # Arc type changed - might need to update plot
            if isinstance(obj, Arc):
                self._check_arc_transformation(obj, old_value, new_value)
    
    def _remove_if_selected(self, obj):
        """Remove object from selection if it's there.
        
        Args:
            obj: Object that was deleted
        """
        was_selected = any(o.id == obj.id and type(o) == type(obj) 
                          for o in self.selected_objects)
        
        if was_selected:
            self.selected_objects = [o for o in self.selected_objects 
                                    if not (o.id == obj.id and type(o) == type(obj))]
            self.needs_update = True
            self._update_objects_list()
            print(f"Removed deleted {type(obj).__name__} {obj.id} from analysis")
    
    def _cleanup_stale_objects(self):
        """Periodic cleanup of objects no longer in model.
        
        This is a safety net in case notifications are missed.
        """
        if not hasattr(self, 'model_manager'):
            return True  # Continue timer
        
        # Get current valid object IDs from model
        valid_ids = set()
        if self.object_type == 'place':
            valid_ids = {p.id for p in self.model_manager.places}
        elif self.object_type == 'transition':
            valid_ids = {t.id for t in self.model_manager.transitions}
        
        # Remove objects not in model
        original_count = len(self.selected_objects)
        self.selected_objects = [obj for obj in self.selected_objects 
                                if obj.id in valid_ids]
        
        if len(self.selected_objects) < original_count:
            self.needs_update = True
            self._update_objects_list()
            print(f"Cleaned up {original_count - len(self.selected_objects)} stale objects")
        
        return True  # Continue timer
```

### Phase 3: Add Arc Transformation Tracking ✅

**File**: `src/shypn/netobjs/arc.py`

Add property setter with notification:

```python
class Arc:
    def __init__(self, source, target, id, name='', weight=1, kind='normal'):
        # ... existing code ...
        self._kind = kind
        self._manager = None  # Set by manager when added to model
    
    @property
    def kind(self):
        """Get arc kind/type."""
        return self._kind
    
    @kind.setter
    def kind(self, value):
        """Set arc kind/type and notify manager.
        
        Args:
            value: New arc kind ('normal', 'inhibitor', 'reset', 'read')
        """
        if value != self._kind:
            old_value = self._kind
            self._kind = value
            
            # Notify manager if registered
            if hasattr(self, '_manager') and self._manager:
                self._manager._notify_observers('transformed', self, 
                                               old_value, value)
```

**File**: `src/shypn/data/model_canvas_manager.py`

Register manager with arcs:

```python
def add_arc(self, source, target, weight=1, kind='normal'):
    arc = Arc(source, target, self._get_next_arc_id(), weight=weight, kind=kind)
    arc._manager = self  # ← ADD THIS: Register manager
    self.arcs.append(arc)
    self.mark_modified()
    self.mark_dirty()
    self._notify_observers('created', arc)
    return arc
```

### Phase 4: Update Simulation Controller ✅

**File**: `src/shypn/engine/simulation/controller.py`

Add model change handling:

```python
class SimulationController:
    def __init__(self, model):
        # ... existing code ...
        if hasattr(model, 'register_observer'):
            model.register_observer(self._on_model_changed)
    
    def _on_model_changed(self, event_type, obj, old_value=None, new_value=None):
        """Handle model changes during simulation.
        
        Args:
            event_type: 'created' | 'deleted' | 'modified' | 'transformed'
            obj: Affected object
        """
        if event_type == 'deleted':
            if isinstance(obj, Transition) and obj.id in self._behaviors:
                # Remove behavior for deleted transition
                del self._behaviors[obj.id]
                print(f"Removed behavior for deleted transition {obj.id}")
        
        elif event_type == 'transformed':
            if isinstance(obj, Arc):
                # Arc kind changed - rebuild affected behaviors
                affected_transitions = set()
                if hasattr(obj.source, 'id'):
                    affected_transitions.add(obj.source.id)
                if hasattr(obj.target, 'id'):
                    affected_transitions.add(obj.target.id)
                
                for trans_id in affected_transitions:
                    if trans_id in self._behaviors:
                        # Rebuild behavior with new arc configuration
                        transition = self.model.get_transition(trans_id)
                        if transition:
                            self._behaviors[trans_id] = self._create_behavior(transition)
                            print(f"Rebuilt behavior for transition {trans_id} due to arc change")
```

---

## Testing Plan

### Test 1: Analysis Panel Object Deletion

**Setup**:
1. Add transition T1 to analysis panel
2. Plot shows T1 data
3. Delete T1 from canvas

**Expected**:
- ✅ T1 automatically removed from analysis list
- ✅ Plot updates without T1
- ✅ No errors in console

### Test 2: Arc Transformation

**Setup**:
1. Create model with place P1 → transition T1
2. Start simulation
3. Change arc kind from 'normal' to 'inhibitor'

**Expected**:
- ✅ Simulation behavior recalculates
- ✅ T1 behavior respects new arc type
- ✅ Analysis plots update correctly

### Test 3: Cascading Deletion

**Setup**:
1. Create chain: P1 → T1 → P2 → T2 → P3
2. Add T1, T2 to analysis
3. Delete P2 (middle place)

**Expected**:
- ✅ Arcs connected to P2 deleted automatically
- ✅ T1 and T2 remain in analysis (still valid)
- ✅ Simulation handles missing connections gracefully

### Test 4: Rapid Deletions

**Setup**:
1. Add 10 transitions to analysis
2. Rapidly delete all 10 from canvas
3. Check analysis panel

**Expected**:
- ✅ All transitions removed from analysis within 1 second
- ✅ Panel shows "No objects selected"
- ✅ No memory leaks or dangling references

---

## Benefits

1. **Data Integrity**: Analysis panels never show deleted objects
2. **Robustness**: Simulation handles model changes gracefully
3. **User Experience**: UI updates automatically without manual refresh
4. **Maintainability**: Centralized notification system
5. **Extensibility**: Easy to add new observers (e.g., property panels, validation)

---

## Migration Notes

**Backward Compatibility**: ✅ Fully backward compatible

- Old code continues to work (observers are optional)
- No breaking changes to existing APIs
- Gradual migration: components opt-in to observation

**Performance**: Minimal overhead

- Observer callbacks are simple and fast
- Cleanup timer runs only once per second
- No impact on rendering or simulation performance

---

## Next Steps

1. ✅ Implement observer pattern in ModelCanvasManager
2. ✅ Update analysis panels to observe changes
3. ✅ Add arc transformation tracking
4. ✅ Update simulation controller
5. Test with realistic models
6. Document new observer API for future components

---

**Status**: Ready for implementation  
**Risk Level**: Low (backward compatible, opt-in)  
**Effort**: ~3-4 hours  
**Impact**: High (solves data integrity issues)
