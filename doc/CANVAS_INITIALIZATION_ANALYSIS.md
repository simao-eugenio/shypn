# Canvas Document Creation & Initialization Analysis

**Date**: 2025-11-01  
**Issue**: Pan/zoom/edit not working after save/reload  
**Root Cause**: Inconsistent canvas initialization across different entry points

## Problem Statement

Canvas documents can be created through multiple entry points, each with slightly different initialization sequences. This creates a **"breadcrumbs" problem** where some paths properly initialize all required state while others skip critical steps, leading to broken canvas functionality.

## Entry Points Map

### 1. **Application Startup** (Default Tab)
**Path**: `main.py` → `model_canvas_loader.load()` → `_setup_canvas_manager()`

**Flow**:
```python
# model_canvas_loader.py:__init__() → load()
builder = Gtk.Builder.new_from_file(ui_path)
notebook = builder.get_object('canvas_notebook')
page = notebook.get_nth_page(0)  # Default tab from .ui file
drawing_area = extract_drawing_area_from_page(page)
self._setup_canvas_manager(drawing_area, overlay_box, overlay_widget)
```

**Initialization Steps**:
1. ✅ Creates `ModelCanvasManager`
2. ✅ Sets redraw callback
3. ✅ Sets `_suppress_callbacks = True`
4. ✅ Wires `on_dirty_changed` callback
5. ✅ Loads DPI settings
6. ✅ Loads view state from file
7. ✅ Calls `manager.create_new_document()`
8. ✅ Connects 'draw' event: `drawing_area.connect('draw', on_draw_wrapper)`
9. ✅ **Calls `_setup_event_controllers()`** ← **CRITICAL**
10. ✅ Creates `CanvasOverlayManager`
11. ✅ Connects palette signals
12. ✅ Calls `_setup_edit_palettes()`
13. ✅ Sets `_suppress_callbacks = False`

**Result**: ✅ Fully functional canvas

---

### 2. **File → New**
**Path**: Menu → `_on_file_new()` → `add_document()`

**Flow**:
```python
# file_explorer_panel.py:_on_file_new()
self.canvas_loader.add_document(replace_empty_default=False)

# model_canvas_loader.py:add_document()
overlay, drawing_area = create_widgets_from_template()
self._setup_canvas_manager(drawing_area, overlay_box, overlay_widget, filename)
```

**Initialization Steps**:
- Same as startup path - calls `_setup_canvas_manager()` fully

**Result**: ✅ Fully functional canvas

---

### 3. **File → Open** (New Tab)
**Path**: Menu → `_open_file_from_path()` → `add_document()` → `load_objects()`

**Flow**:
```python
# file_explorer_panel.py:_load_document_into_canvas()
document = DocumentModel.load_from_file(filepath)

# Create new tab
page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
manager = self.canvas_loader.get_canvas_manager(drawing_area)

# Load objects
manager.load_objects(places, transitions, arcs)
manager.document_controller.set_change_callback(manager._on_object_changed)
manager.set_filepath(filepath)
manager.mark_clean()
```

**Initialization Steps**:
1. ✅ Calls `add_document()` which calls `_setup_canvas_manager()`
2. ✅ All event controllers set up
3. ✅ `load_objects()` adds objects
4. ✅ Sets change callback
5. ✅ Restores view state
6. ✅ Sets filepath and marks clean

**Result**: ✅ Fully functional canvas

---

### 4. **File → Open** (Tab Reuse) ⚠️ **PROBLEM PATH**
**Path**: Menu → `_open_file_from_path()` → **REUSES existing tab** → `load_objects()`

**Flow**:
```python
# file_explorer_panel.py:_load_document_into_canvas()
document = DocumentModel.load_from_file(filepath)

# Check if can reuse current tab
current_page = self.canvas_loader.notebook.get_current_page()
page_widget = self.canvas_loader.notebook.get_nth_page(current_page)
drawing_area = self.canvas_loader._get_drawing_area_from_page(page_widget)
manager = self.canvas_loader.get_canvas_manager(drawing_area)

# Reuse if empty
if is_empty and is_default_name and is_clean:
    pass  # ⚠️ REUSE - NO add_document() call!

# Load objects directly into existing manager
manager.load_objects(places, transitions, arcs)
manager.document_controller.set_change_callback(manager._on_object_changed)
manager.set_filepath(filepath)
manager.mark_clean()
```

**Initialization Steps**:
1. ❌ **SKIPS** `add_document()`
2. ❌ **SKIPS** `_setup_canvas_manager()`
3. ✅ Event controllers already exist (from startup)
4. ✅ `load_objects()` adds objects
5. ✅ Sets change callback
6. ⚠️ **BUT**: Manager state might be stale
7. ⚠️ **BUT**: `_suppress_callbacks` might still be True
8. ⚠️ **BUT**: No call to `create_new_document()` to reset state

**Result**: ⚠️ **PARTIAL INITIALIZATION** - event handlers exist but manager state not properly reset

---

### 5. **Import KEGG** (New Tab)
**Path**: KEGG panel → `_on_kegg_import_complete()` → `add_document()` → `load_objects()`

**Flow**:
```python
# kegg_category.py:_on_kegg_import_complete()
document_model = create_from_kegg(pathway_data)

# Create new tab
page_index, drawing_area = canvas_loader.add_document(filename=base_name)
canvas_manager = canvas_loader.get_canvas_manager(drawing_area)

# Load objects
canvas_manager.load_objects(places, transitions, arcs)
canvas_manager.document_controller.set_change_callback(canvas_manager._on_object_changed)
canvas_manager.set_filepath(saved_filepath)
canvas_manager.mark_clean()
canvas_manager.mark_as_imported(base_name)
canvas_manager.fit_to_page(padding_percent=15, deferred=True)
```

**Initialization Steps**:
- Same as "File → Open (New Tab)" - fully initializes via `add_document()`

**Result**: ✅ Fully functional canvas

---

### 6. **Import KEGG** (Tab Reuse) ⚠️ **PROBLEM PATH**
**Path**: KEGG panel → `_on_kegg_import_complete()` → **REUSES tab** → `load_objects()`

**Flow**:
```python
# kegg_category.py:_on_kegg_import_complete()
# Check if can reuse current empty tab
current_page = canvas_loader.notebook.get_current_page()
page_widget = canvas_loader.notebook.get_nth_page(current_page)
drawing_area = canvas_loader._get_drawing_area_from_page(page_widget)
manager = canvas_loader.get_canvas_manager(drawing_area)

if is_empty and is_default_name and is_clean:
    canvas_manager = manager  # ⚠️ REUSE - NO add_document() call!

# Load objects directly
canvas_manager.load_objects(places, transitions, arcs)
canvas_manager.document_controller.set_change_callback(canvas_manager._on_object_changed)
canvas_manager.set_filepath(saved_filepath)
canvas_manager.mark_clean()
```

**Initialization Steps**:
- Same issues as "File → Open (Tab Reuse)"

**Result**: ⚠️ **PARTIAL INITIALIZATION**

---

### 7. **Import SBML** (New Tab / Tab Reuse)
**Path**: SBML panel → `_on_sbml_import_complete()` → Similar to KEGG

**Result**: Same pattern as KEGG - works for new tab, partial init for reused tab

---

## Critical Initialization Components

### Components That MUST Be Initialized

1. **ModelCanvasManager Instance**
   - `canvas_width`, `canvas_height`
   - `filename`
   - `zoom`, `pan_x`, `pan_y`
   - `_initial_pan_set`
   - `places`, `transitions`, `arcs` lists
   - `_suppress_callbacks` flag

2. **Event State Dictionaries** (in `model_canvas_loader`)
   - `_drag_state[drawing_area]`
   - `_arc_state[drawing_area]`
   - `_click_state[drawing_area]`
   - `_lasso_state[drawing_area]`

3. **GTK Event Handlers** (connected to `drawing_area`)
   - `'draw'` → `on_draw_wrapper()`
   - `'button-press-event'` → `_on_button_press()`
   - `'button-release-event'` → `_on_button_release()`
   - `'motion-notify-event'` → `_on_motion_notify()`
   - `'scroll-event'` → `_on_scroll_event()`
   - `'key-press-event'` → `_on_key_press_event()`

4. **Callbacks**
   - `manager.set_redraw_callback()` → `drawing_area.queue_draw()`
   - `manager.on_dirty_changed` → tab label update
   - `manager.document_controller.set_change_callback()` → dirty tracking

5. **Overlay System**
   - `CanvasOverlayManager` instance
   - Palette signal connections
   - Tool change handlers
   - Simulation handlers

6. **Document State**
   - `manager.create_new_document()` for new/empty
   - `manager.load_objects()` for file/import
   - `manager.set_filepath()`
   - `manager.mark_clean()`

### What Gets Initialized Where

| Component | Startup | New Tab | New File Load | Tab Reuse Load | Import New | Import Reuse |
|-----------|---------|---------|---------------|----------------|------------|--------------|
| Manager instance | ✅ | ✅ | ✅ | ♻️ Reused | ✅ | ♻️ Reused |
| Event state dicts | ✅ | ✅ | ✅ | ♻️ Reused | ✅ | ♻️ Reused |
| GTK event handlers | ✅ | ✅ | ✅ | ♻️ Reused | ✅ | ♻️ Reused |
| Redraw callback | ✅ | ✅ | ✅ | ♻️ Reused | ✅ | ♻️ Reused |
| Dirty callback | ✅ | ✅ | ✅ | ♻️ Reused | ✅ | ♻️ Reused |
| Overlay system | ✅ | ✅ | ✅ | ♻️ Reused | ✅ | ♻️ Reused |
| `create_new_document()` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `_suppress_callbacks` reset | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Objects cleared | N/A | N/A | ❌ | ❌ | ❌ | ❌ |
| `load_objects()` | N/A | N/A | ✅ | ✅ | ✅ | ✅ |
| Change callback set | N/A | N/A | ✅ | ✅ | ✅ | ✅ |

**Legend**:
- ✅ = Properly initialized
- ❌ = Not done
- ♻️ = Reused from previous initialization
- N/A = Not applicable

---

## The Bug

### Symptom
After saving a file with catalysts (test arcs) and reopening it, **pan/zoom/edit stop working**.

### Root Cause Analysis

When File → Open reuses an empty default tab:

1. **Reused State Dictionaries**: `_drag_state`, `_arc_state`, etc. are reused from startup
2. **No Manager Reset**: `create_new_document()` is NOT called, so:
   - `_suppress_callbacks` might still be True
   - `zoom`, `pan_x`, `pan_y` not reset to defaults
   - `_initial_pan_set` not reset
   - `modified`, `created_at`, `modified_at` not reset
3. **No Object Clearing**: `load_objects()` **APPENDS** to existing lists (but they're empty, so OK)
4. **Stale Manager State**: The manager retains state from its `create_new_document()` call at startup, not reflecting the loaded file's state

### Why Pan/Zoom Breaks

The most likely culprit: **`_suppress_callbacks` flag is still True** from a previous operation.

Looking at `_setup_canvas_manager()`:
```python
manager._suppress_callbacks = True  # Line 565
# ... setup code ...
manager._suppress_callbacks = False  # Line 664 (only if overlay_box exists!)
```

**BUG**: If `overlay_box` is None, `_suppress_callbacks` is NEVER set back to False!

When tab is reused and we don't call `_setup_canvas_manager()` again, this flag stays True, blocking all interactions.

---

## The Fix

### Principle
**Every canvas document load MUST go through a canonical initialization sequence, regardless of entry point.**

### Strategy

#### Option 1: Always Call `_setup_canvas_manager()` on Reuse ❌
**Problem**: This creates a NEW manager, losing the existing GTK event handler connections

#### Option 2: Extract "Reset Manager State" Function ✅
**Best approach**: Create a method that resets manager state without recreating it

```python
def _reset_manager_for_load(self, manager, filename):
    """Reset manager state before loading objects from file.
    
    This prepares an existing manager to receive a loaded document,
    resetting all state flags and counters to clean slate.
    
    Must be called BEFORE load_objects() when reusing a tab.
    """
    # Reset document state
    manager.filename = filename
    manager.modified = False
    manager.created_at = datetime.now()
    manager.modified_at = None
    
    # Reset view state (will be overridden by saved view_state if exists)
    manager.zoom = 1.0
    manager.pan_x = 0.0
    manager.pan_y = 0.0
    manager._initial_pan_set = False
    
    # CRITICAL: Ensure callbacks are enabled
    manager._suppress_callbacks = False
    
    # Clear any existing objects (paranoid - should be empty)
    manager.places.clear()
    manager.transitions.clear()
    manager.arcs.clear()
    
    # Reset ID counters
    manager.document_controller._next_place_id = 1
    manager.document_controller._next_transition_id = 1
    manager.document_controller._next_arc_id = 1
    
    # Mark as clean (will be loaded)
    manager.mark_clean()
```

#### Option 3: Always Create New Tab, Never Reuse ❌
**Problem**: Poor UX - user ends up with many empty tabs

### Recommended Solution

**Two-Phase Initialization**:

1. **Phase 1: Canvas Setup** (done once per drawing_area)
   - Create manager
   - Connect GTK event handlers
   - Initialize state dictionaries
   - Set up overlays
   - Set up palettes

2. **Phase 2: Document Load** (done every time objects are loaded)
   - Reset manager state
   - Clear existing objects
   - Load new objects
   - Set callbacks
   - Restore view state
   - Mark clean

Modify `_load_document_into_canvas()`:

```python
def _load_document_into_canvas(self, document, filepath: str):
    # ... existing code to check reuse ...
    
    if can_reuse_tab:
        # Reuse tab - but RESET state first
        self.canvas_loader._reset_manager_for_load(manager, base_name)
    else:
        # Create new tab - full initialization
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
    
    # Now load objects (works for both paths)
    manager.load_objects(places, transitions, arcs)
    # ... rest of loading code ...
```

---

## Action Items

1. ✅ Create `_reset_manager_for_load()` method
2. ✅ Call it in File → Open tab reuse path
3. ✅ Call it in KEGG import tab reuse path
4. ✅ Call it in SBML import tab reuse path
5. ✅ Verify `_suppress_callbacks` is always set to False after setup
6. ✅ Add safety check in `_setup_canvas_manager()` to always set `_suppress_callbacks = False`
7. ✅ Test all entry points:
   - Startup default tab
   - File → New
   - File → Open (new tab)
   - File → Open (reuse tab) ← **Primary test case**
   - Import KEGG (new tab)
   - Import KEGG (reuse tab)
   - Import SBML (new tab)
   - Import SBML (reuse tab)

---

## Testing Checklist

For EACH entry point, verify:
- [ ] Pan works (middle-click drag)
- [ ] Zoom works (scroll wheel)
- [ ] Select works (click objects)
- [ ] Edit works (move objects)
- [ ] Tool palette responds
- [ ] Simulation palette responds
- [ ] Save/load preserves state
- [ ] Tab label shows asterisk on edit
- [ ] No console errors

**Critical test case** (user's bug):
1. Open project
2. Import KEGG hsa00010
3. Convert arcs to test arcs (catalysts)
4. Save as hsa00010_test.shy
5. Close tab
6. File → Open hsa00010_test.shy (will reuse default empty tab)
7. **Verify**: Pan/zoom/edit all work ✅
