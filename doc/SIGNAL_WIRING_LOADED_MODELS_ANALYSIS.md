# Signal Wiring Analysis for Loaded Models

**Date:** October 15, 2025  
**Issue:** Network objects (transitions) do not respond to system signals when loaded from files or imported from KEGG, but work correctly in new files.

## Problem Summary

When models are loaded into the canvas (via file loading, KEGG import), the network objects are not properly registered with the SimulationController's observer system. This causes:
- Transitions not firing during simulation
- Behavior cache not being updated when objects are modified
- Model adapter caches becoming stale

## Root Cause Analysis

### Architecture Overview

The SimulationController uses an observer pattern to track model changes:

```python
class SimulationController:
    def __init__(self, model):
        # Register to observe model changes
        if hasattr(model, 'register_observer'):
            model.register_observer(self._on_model_changed)
```

The controller's `_on_model_changed()` method responds to events:
- `'created'`: New objects added
- `'deleted'`: Objects removed
- `'modified'`: Objects changed
- `'transformed'`: Arc type changes

### Current Loading Paths

#### 1. **File Loading** (`file_explorer_panel.py:_load_document_into_canvas`)
```python
# ❌ PROBLEM: Does NOT notify observers
manager.places = list(document.places)
manager.transitions = list(document.transitions)
manager.arcs = list(document.arcs)
# Missing: observer notifications
```

#### 2. **KEGG Import** (`kegg_import_panel.py:_import_pathway_background`)
```python
# ❌ PROBLEM: Does NOT notify observers
manager.places = list(document_model.places)
manager.transitions = list(document_model.transitions)
manager.arcs = list(document_model.arcs)
# Missing: observer notifications
```

#### 3. **SBML Import** (`sbml_import_panel.py:_on_load_clicked`)
```python
# ✅ CORRECT: Does notify observers
manager.places = list(document_model.places)
manager.transitions = list(document_model.transitions)
manager.arcs = list(document_model.arcs)

# Notify observers that model structure has changed
if hasattr(manager, '_notify_observers'):
    for place in manager.places:
        manager._notify_observers('created', place)
    for transition in manager.transitions:
        manager._notify_observers('created', transition)
    for arc in manager.arcs:
        manager._notify_observers('created', arc)
```

### Why This Matters

The SimulationController needs to know about loaded objects to:

1. **Initialize Transition States**: Track enablement times and scheduled firing times
2. **Invalidate Caches**: Clear behavior cache when objects change
3. **Update Model Adapter**: Rebuild place/transition/arc dictionaries after structure changes

Without observer notifications, the SimulationController operates on stale data.

## Solution

### Fix 1: File Loading (`file_explorer_panel.py`)

Add observer notifications after loading objects:

```python
# Restore objects
manager.places = list(document.places)
manager.transitions = list(document.transitions)
manager.arcs = list(document.arcs)
manager._next_place_id = document._next_place_id
manager._next_transition_id = document._next_transition_id
manager._next_arc_id = document._next_arc_id

# Ensure arc references are properly set
manager.ensure_arc_references()

# Notify observers that model structure has changed
if hasattr(manager, '_notify_observers'):
    for place in manager.places:
        manager._notify_observers('created', place)
    for transition in manager.transitions:
        manager._notify_observers('created', transition)
    for arc in manager.arcs:
        manager._notify_observers('created', arc)

# Mark as dirty to ensure redraw
manager.mark_dirty()
```

### Fix 2: KEGG Import (`kegg_import_panel.py`)

Add observer notifications after loading objects:

```python
# Load the document model into the manager
manager.places = list(document_model.places)
manager.transitions = list(document_model.transitions)
manager.arcs = list(document_model.arcs)

# Update ID counters
manager._next_place_id = document_model._next_place_id
manager._next_transition_id = document_model._next_transition_id
manager._next_arc_id = document_model._next_arc_id

# Mark as imported so "Save" triggers "Save As" behavior
manager.mark_as_imported(pathway_name)

# Ensure arc references are properly set
manager.ensure_arc_references()

# Notify observers that model structure has changed
if hasattr(manager, '_notify_observers'):
    for place in manager.places:
        manager._notify_observers('created', place)
    for transition in manager.transitions:
        manager._notify_observers('created', transition)
    for arc in manager.arcs:
        manager._notify_observers('created', arc)

# Mark as dirty to ensure redraw
manager.mark_dirty()
```

## Implementation Order

1. ✅ Fix file loading path (most critical - affects all saved models)
2. ✅ Fix KEGG import path (affects biochemical pathway imports)
3. ✅ Verify SBML import still works correctly (already has notifications)
4. ✅ Test all three loading scenarios to ensure transitions fire correctly

## Testing Strategy

### Test Case 1: File Loading
1. Create a new model with places, transitions, and arcs
2. Add tokens to places
3. Save the model
4. Close and reopen the application
5. Load the saved model
6. Enter simulation mode
7. ✅ Verify transitions can fire when enabled

### Test Case 2: KEGG Import
1. Import a KEGG pathway (e.g., "hsa00010" - Glycolysis)
2. Add tokens to input places
3. Enter simulation mode
4. ✅ Verify transitions can fire when enabled

### Test Case 3: SBML Import
1. Import an SBML model
2. Add tokens to input places
3. Enter simulation mode
4. ✅ Verify transitions can fire when enabled (should already work)

## Expected Outcomes

After applying fixes:
- ✅ Loaded models will have working simulation (transitions fire correctly)
- ✅ Imported pathways (KEGG, SBML) will have working simulation
- ✅ Behavior cache will be properly invalidated on model changes
- ✅ Model adapter caches will be refreshed when needed
- ✅ All network objects will respond to system signals consistently

## Related Files

- `/home/simao/projetos/shypn/src/shypn/helpers/file_explorer_panel.py` (lines 1040-1074)
- `/home/simao/projetos/shypn/src/shypn/helpers/kegg_import_panel.py` (lines 270-314)
- `/home/simao/projetos/shypn/src/shypn/helpers/sbml_import_panel.py` (lines 470-540) ✅ Already correct
- `/home/simao/projetos/shypn/src/shypn/engine/simulation/controller.py` (SimulationController observer registration)
- `/home/simao/projetos/shypn/src/shypn/data/model_canvas_manager.py` (ModelCanvasManager observer system)
