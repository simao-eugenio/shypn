# Viability Panel Canvas State Lifecycle Analysis

## Problem Statement

The Viability Panel is **per-document** (one instance per canvas/tab), but its selection and coloring methods interact with a **global canvas state** that changes when users switch tabs. This creates timing and state management issues.

## Current Architecture

### Per-Document Design
```
Canvas Tab 1 → Drawing Area 1 → Viability Panel Instance 1
Canvas Tab 2 → Drawing Area 2 → Viability Panel Instance 2
Canvas Tab 3 → Drawing Area 3 → Viability Panel Instance 3
```

Each viability panel instance:
- Has its own `selected_localities` dictionary
- Has its own `_locality_objects` dictionary (stores IDs)
- Has its own UI state (listbox, expanders, etc.)

### Global Canvas State
```
ModelCanvasLoader:
  - get_current_document() → returns currently visible drawing_area
  - canvas_managers[drawing_area] → ModelCanvasManager with places/transitions/arcs
  - overlay_managers[drawing_area] → OverlayManager with viability_panel_loader
```

## Critical Methods Analysis

### 1. `add_object_for_analysis(obj)` - Context Menu Entry Point

**Called From:** Context menu handler when user right-clicks transition

**Current Implementation:**
```python
def add_object_for_analysis(self, obj):
    # PROBLEM: obj is from CURRENT canvas when right-clicked
    # But this panel instance might belong to a DIFFERENT canvas!
    
    obj.border_color = color_rgb  # ← Colors object from current canvas
    obj.fill_color = color_rgb
    
    self._trigger_canvas_redraw()  # ← Redraws current canvas
    
    self.investigate_transition(obj.id)  # ← Adds to THIS panel's list
```

**Issue:** 
- When user right-clicks on Canvas Tab 1, the context menu gets the viability panel for Tab 1
- The `obj` parameter is from Tab 1's model
- This SHOULD work correctly... **BUT**...

### 2. `investigate_transition(transition_id)` - Add to List

**Current Implementation:**
```python
def investigate_transition(self, transition_id: str):
    # Get KB from _get_kb()
    kb = self._get_kb()
    
    # Get transition from KB
    transition = kb.transitions.get(transition_id)
    
    # Add to list
    self._add_transition_to_list(transition)
```

**_get_kb() Implementation:**
```python
def _get_kb(self):
    if not self.model_canvas:
        return None
    
    # PROBLEM: This gets KB for CURRENT document, not THIS panel's document!
    return self.model_canvas.get_current_knowledge_base()
```

**Issue:**
- `self.model_canvas` points to the **global** ModelCanvasLoader
- `get_current_knowledge_base()` returns KB for **currently visible tab**
- If user switches tabs quickly, this panel might access the WRONG KB!

### 3. `_add_transition_to_list(transition)` - Color and Add

**Current Implementation:**
```python
def _add_transition_to_list(self, transition):
    # PROBLEM: Gets current model, not THIS panel's model!
    model = self._get_current_model()
    
    # Find transition object in model
    for t in model.transitions:
        if t.id == transition.transition_id:
            transition_obj = t
            break
    
    # Color the locality
    self._color_transition(transition_obj)
    for place in diagnostic_locality.input_places:
        self._color_locality_place(place)
    # ... etc
    
    # Store IDs for later clearing
    self._locality_objects[transition_id] = locality_ids
```

**_get_current_model() Implementation:**
```python
def _get_current_model(self):
    if not self.model_canvas:
        return None
    
    # PROBLEM: Gets CURRENT document's model, not THIS panel's!
    drawing_area = self.model_canvas.get_current_document()
    
    # Get model from drawing_area
    if hasattr(drawing_area, 'document_model'):
        return drawing_area.document_model
```

**Issue:**
- This method always gets the **currently visible tab's model**
- If user switches tabs during operation, colors wrong document!

### 4. `_remove_transition_from_list(transition_id)` - Clear Colors

**Current Implementation:**
```python
def _remove_transition_from_list(self, transition_id):
    # PROBLEM: Gets current model to reset colors
    model = self._get_current_model()
    
    locality_ids = self._locality_objects.get(transition_id)
    
    # Find objects by ID in current model
    for t_obj in model.transitions:
        if t_obj.id == transition_id:
            # Reset colors
            t_obj.border_color = Transition.DEFAULT_BORDER_COLOR
```

**Issue:**
- Stored IDs are from **this panel's document**
- But `_get_current_model()` gets **currently visible document**
- If user switched tabs, this tries to reset colors in the WRONG document!

### 5. `_on_clear_all_clicked()` - Clear All Colors

**Same Issue:** Uses `_get_current_model()` which might return wrong document

### 6. `_trigger_canvas_redraw()` - Redraw Canvas

**Current Implementation:**
```python
def _trigger_canvas_redraw(self):
    # Gets CURRENT canvas manager
    canvas_manager = self._get_canvas_manager()
    
    if canvas_manager:
        canvas_manager.mark_needs_redraw()
    
    # Gets CURRENT drawing area
    drawing_area = self.model_canvas.get_current_document()
    if drawing_area:
        drawing_area.queue_draw()
```

**Issue:**
- Always redraws **currently visible canvas**
- If user switched tabs, redraws the WRONG canvas!

## Root Cause

All methods use **global accessors** that return state for the **currently visible tab**:
- `self.model_canvas.get_current_document()` → current tab's drawing area
- `self.model_canvas.get_current_knowledge_base()` → current tab's KB
- `self._get_current_model()` → current tab's model
- `self._get_canvas_manager()` → current tab's canvas manager

But each viability panel instance is **bound to a specific document**, not the current one!

## Solution Architecture

### Store Document Identity

Each viability panel instance should store its own document identity:

```python
class ViabilityPanel(Gtk.Box):
    def __init__(self, model=None, model_canvas=None):
        # ... existing code ...
        
        # Store THIS panel's document identity
        self.drawing_area = None  # Set via set_drawing_area()
        self.model = None
        self.model_canvas = model_canvas  # Global ModelCanvasLoader for access
```

### Replace Global Accessors with Document-Specific Accessors

#### Option A: Store Direct References (Simpler)

```python
def set_drawing_area(self, drawing_area):
    """Set THIS panel's drawing area."""
    self.drawing_area = drawing_area
    
    # Get and cache references to THIS document's resources
    if self.model_canvas and drawing_area:
        overlay_manager = self.model_canvas.overlay_managers.get(drawing_area)
        if overlay_manager:
            # Cache canvas manager for THIS document
            self._canvas_manager = overlay_manager.canvas_manager
            
            # Cache model for THIS document
            if hasattr(overlay_manager.canvas_manager, 'to_document_model'):
                self._document_model = overlay_manager.canvas_manager.to_document_model()

def _get_this_panel_model(self):
    """Get the model for THIS panel's document (not current tab)."""
    if hasattr(self, '_document_model') and self._document_model:
        return self._document_model
    
    # Fallback: look up via drawing_area
    if self.drawing_area and self.model_canvas:
        overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
        if overlay_manager and hasattr(overlay_manager, 'canvas_manager'):
            manager = overlay_manager.canvas_manager
            if hasattr(manager, 'to_document_model'):
                return manager.to_document_model()
    
    return None

def _get_this_panel_kb(self):
    """Get the KB for THIS panel's document (not current tab)."""
    if self.drawing_area and self.model_canvas:
        return self.model_canvas.knowledge_bases.get(self.drawing_area)
    return None

def _get_this_panel_canvas_manager(self):
    """Get the canvas manager for THIS panel's document."""
    if hasattr(self, '_canvas_manager') and self._canvas_manager:
        return self._canvas_manager
    
    if self.drawing_area and self.model_canvas:
        overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
        if overlay_manager:
            return overlay_manager.canvas_manager
    
    return None
```

#### Option B: Always Look Up Via drawing_area (More Dynamic)

```python
def _get_this_panel_model(self):
    """Get the model for THIS panel's document."""
    if not self.drawing_area or not self.model_canvas:
        print("[Viability] Warning: No drawing_area set for this panel")
        return None
    
    overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
    if overlay_manager and hasattr(overlay_manager, 'canvas_manager'):
        manager = overlay_manager.canvas_manager
        if hasattr(manager, 'to_document_model'):
            return manager.to_document_model()
    
    return None
```

### Update All Methods

Replace all calls to:
- `self._get_current_model()` → `self._get_this_panel_model()`
- `self._get_kb()` → `self._get_this_panel_kb()`
- `self._get_canvas_manager()` → `self._get_this_panel_canvas_manager()`

### Update Redraw Method

```python
def _trigger_canvas_redraw(self):
    """Trigger canvas redraw for THIS panel's document."""
    # Get canvas manager for THIS panel's document
    canvas_manager = self._get_this_panel_canvas_manager()
    if canvas_manager and hasattr(canvas_manager, 'mark_needs_redraw'):
        canvas_manager.mark_needs_redraw()
    
    # Queue draw for THIS panel's drawing area
    if self.drawing_area and hasattr(self.drawing_area, 'queue_draw'):
        self.drawing_area.queue_draw()
```

## Implementation Priority

### Phase 1: Add Document-Specific Accessors ✅ CRITICAL
1. Add `_get_this_panel_model()`
2. Add `_get_this_panel_kb()`
3. Add `_get_this_panel_canvas_manager()`

### Phase 2: Update All Method Calls ✅ CRITICAL
1. Replace in `investigate_transition()`
2. Replace in `_add_transition_to_list()`
3. Replace in `_remove_transition_from_list()`
4. Replace in `_on_clear_all_clicked()`
5. Replace in `_trigger_canvas_redraw()`
6. Replace in all other methods that access model/KB

### Phase 3: Verify Initialization ✅ CRITICAL
1. Ensure `set_drawing_area()` is called during panel creation
2. Verify in `_setup_edit_palettes()` in model_canvas_loader.py

### Phase 4: Add Safety Checks
1. Add warnings when drawing_area is None
2. Add error handling for missing resources

## Test Scenarios

### Scenario 1: Single Tab Operation
1. Create interactive model on default tab
2. Right-click transition → "Add to Viability Analysis"
3. **Expected:** Transition and locality are colored purple
4. **Verify:** Colors are in correct document

### Scenario 2: Multi-Tab with Tab Switch
1. Create model on Tab 1, add transition T1 to viability
2. Switch to Tab 2
3. Switch back to Tab 1
4. Click "Clear All" on Tab 1's viability panel
5. **Expected:** T1's colors reset in Tab 1 only
6. **Verify:** Tab 2 is unaffected

### Scenario 3: Multi-Tab Simultaneous
1. Tab 1: Add T1 to viability (purple)
2. Tab 2: Add T2 to viability (purple)
3. Switch between tabs
4. **Expected:** Each tab shows its own colored localities
5. **Verify:** Colors don't leak between tabs

### Scenario 4: Context Menu from Wrong Tab
1. Tab 1 viability panel is showing (but Tab 2 is active canvas)
2. Right-click on Tab 2's transition
3. **Expected:** Transition is added to Tab 2's viability panel
4. **Verify:** Tab 1's panel is unaffected

## Current Status

**Problem Identified:** ✅
- All methods use global "current" accessors
- Panel is per-document but accesses global state

**Solution Designed:** ✅
- Add document-specific accessors
- Store drawing_area in panel
- Look up resources via drawing_area, not "current"

**Implementation:** 🚧 IN PROGRESS
- Need to create new accessor methods
- Need to replace all method calls
- Need to verify initialization

**Testing:** ⏳ PENDING
- After implementation
