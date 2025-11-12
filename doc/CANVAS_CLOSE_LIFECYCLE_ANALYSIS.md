# Canvas Close Tab Lifecycle Analysis

**Date**: November 11, 2025  
**Issue**: Verify if closing a canvas tab properly follows the Global Canvas State Life Cycle  
**Context**: All new canvases must be created by File→New to normalize initial state

## Current Close Tab Flow

### 1. User Clicks Close Button (X)

**File**: `src/shypn/helpers/model_canvas_loader.py:356`

```python
def _on_tab_close_clicked(self, button, page_widget):
    """Handle tab close button click."""
    page_num = self.notebook.page_num(page_widget)
    if page_num == -1:
        return
    self.close_tab(page_num)
```

### 2. Close Tab Method

**File**: `src/shypn/helpers/model_canvas_loader.py:496`

```python
def close_tab(self, page_num):
    """Close a tab after checking for unsaved changes."""
    
    # 1. Get the drawing area from page widget
    page = self.notebook.get_nth_page(page_num)
    drawing_area = _extract_from_overlay(page)
    
    # 2. Check for unsaved changes via persistency
    if self.persistency and drawing_area:
        manager = self.canvas_managers.get(drawing_area)
        if manager:
            # Switch to tab and check unsaved changes
            if not self.persistency.check_unsaved_changes():
                return False  # User cancelled
    
    # 3. Remove page from notebook
    self.notebook.remove_page(page_num)
    
    # 4. ✅ GLOBAL-SYNC: Destroy canvas in lifecycle system
    if self.lifecycle_adapter and drawing_area:
        try:
            self.lifecycle_adapter.destroy_canvas(drawing_area)
        except Exception as e:
            pass  # Failed to destroy canvas in lifecycle
    
    # 5. Cleanup legacy dictionaries
    if drawing_area in self.canvas_managers:
        del self.canvas_managers[drawing_area]
    if drawing_area in self.simulation_controllers:
        del self.simulation_controllers[drawing_area]
    if drawing_area in self.overlay_managers:
        overlay_manager = self.overlay_managers[drawing_area]
        overlay_manager.cleanup_overlays()
        del self.overlay_managers[drawing_area]
    if drawing_area in self.knowledge_bases:
        del self.knowledge_bases[drawing_area]
    
    # 6. Create default tab if no tabs remain
    if self.notebook.get_n_pages() == 0:
        self.add_document(filename='default')
    
    return True
```

### 3. Lifecycle Manager Destroy

**File**: `src/shypn/canvas/lifecycle/lifecycle_manager.py:389`

```python
def destroy_canvas(self, drawing_area: Gtk.DrawingArea):
    """Cleanup canvas resources (tab closed)."""
    
    context = self.get_context(drawing_area)
    if not context:
        logger.warning("Canvas not registered - nothing to destroy")
        return
    
    logger.info(f"Destroying canvas {context.canvas_id}: {context.display_name}")
    
    # 1. Stop simulation if running
    if context.is_simulation_running:
        context.controller.stop()
    
    # 2. Cleanup palette
    if hasattr(context.palette, 'cleanup'):
        context.palette.cleanup()
    
    # 3. Remove step listeners (prevent callbacks to destroyed objects)
    if hasattr(context.controller, 'step_listeners'):
        context.controller.step_listeners.clear()
    
    # 4. ✅ Delete ID scope for this canvas
    self.id_manager.delete_scope(context.id_scope)
    
    # 5. Remove from registry
    del self.canvas_registry[context.canvas_id]
    
    logger.info(f"✓ Canvas {context.canvas_id} destroyed")
```

## File→New Flow

**File**: `src/shypn/ui/menu_actions.py:43`
```python
def on_file_new(self, action, param):
    """Create a new file/model."""
    if self.file_explorer_panel:
        self.file_explorer_panel.new_document()
```

**File**: `src/shypn/helpers/file_explorer_panel.py:1913`
```python
def new_document(self):
    """Create a new document."""
    # Create new tab directly - no unsaved changes check needed
    # File→New creates additional tab, doesn't close/replace existing ones
    self.canvas_loader.add_document(replace_empty_default=False)
```

**File**: `src/shypn/helpers/model_canvas_loader.py:583`
```python
def add_document(self, title=None, filename=None, replace_empty_default=True):
    """Add a new document (tab) to the canvas."""
    
    # 1. Load canvas tab from UI template
    template_path = 'canvas_tab_template.ui'
    tab_builder = Gtk.Builder.new_from_file(template_path)
    overlay = tab_builder.get_object('canvas_overlay_template')
    drawing = tab_builder.get_object('canvas_drawing_template')
    
    # 2. Create tab label with close button
    tab_box, tab_label, close_button = self._create_tab_label(filename)
    close_button.connect('clicked', self._on_tab_close_clicked, overlay)
    
    # 3. Add to notebook
    page_index = self.notebook.append_page(overlay, tab_box)
    
    # 4. Realize widget for Wayland compatibility
    if not overlay.get_realized():
        overlay.realize()
    
    # 5. ✅ Setup canvas manager (creates lifecycle context)
    self._setup_canvas_manager(drawing, overlay_box, overlay, filename)
    
    # 6. Reset simulation to initial state
    self._ensure_simulation_reset(drawing)
    
    # 7. Switch to new tab
    self.notebook.set_current_page(page_index)
    
    return (page_index, drawing)
```

**File**: `src/shypn/helpers/model_canvas_loader.py:655`
```python
def _setup_canvas_manager(self, drawing_area, overlay_box, overlay_widget, filename):
    """Setup canvas manager and wire up callbacks."""
    
    # 1. ✅ Set ID scope for this canvas BEFORE creating manager
    if self.lifecycle_manager:
        canvas_id = id(drawing_area)
        scope_name = f"canvas_{canvas_id}"
        self.lifecycle_manager.id_manager.set_scope(scope_name)
    
    # 2. Create ModelCanvasManager
    manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000, filename=filename)
    self.canvas_managers[drawing_area] = manager
    
    # 3. Set callbacks...
    # (dirty state, redraw, etc.)
    
    # 4. ✅ Create canvas in lifecycle system
    if self.lifecycle_adapter:
        context = self.lifecycle_adapter.create_canvas(
            drawing_area, 
            manager, 
            file_path=None
        )
    
    # 5. Setup simulation controller...
    # 6. Setup overlay managers (palettes)...
```

## Analysis Results

### ✅ CORRECT: Close Tab Lifecycle

The close tab flow **DOES** properly follow the Global Canvas State Life Cycle:

1. **User closes tab** → `_on_tab_close_clicked()`
2. **Check unsaved** → Shows save dialog if needed
3. **Remove from UI** → `notebook.remove_page()`
4. **✅ Destroy lifecycle** → `lifecycle_adapter.destroy_canvas()`
   - Stops simulation
   - Cleans up palette
   - Clears step listeners
   - **Deletes ID scope** (critical!)
   - Removes from registry
5. **Cleanup legacy** → Delete from old dictionaries
6. **Create default** → If no tabs remain, create new default tab

### ✅ CORRECT: File→New Lifecycle

The File→New flow **DOES** properly initialize canvas through lifecycle:

1. **User clicks File→New** → Menu action
2. **Load UI template** → Consistent widget hierarchy
3. **Create tab** → Add to notebook with close button
4. **✅ Set ID scope** → `id_manager.set_scope(f"canvas_{id}")`
5. **Create manager** → ModelCanvasManager instance
6. **✅ Create lifecycle** → `lifecycle_adapter.create_canvas()`
   - Creates CanvasContext
   - Assigns ID scope
   - Creates controller
   - Registers in canvas_registry
7. **Reset simulation** → Clean initial state
8. **Switch tab** → Show new canvas

### ✅ CORRECT: ID Scope Isolation

Both flows properly manage ID scopes:

- **File→New**: Sets scope → Creates objects → Objects get unique IDs in that scope
- **Close Tab**: Destroys canvas → Deletes scope → Frees ID namespace

This ensures ID isolation between canvases as required.

## Potential Issues

### ⚠️ Issue 1: Default Tab Creation on Last Close

When closing the last tab, a new default tab is created:

```python
if self.notebook.get_n_pages() == 0:
    self.add_document(filename='default')
```

**Question**: Does this follow the "all canvases created by File→New" requirement?

**Answer**: This is a **safety mechanism** to prevent having zero tabs. The default tab is created using `add_document()` which follows the same lifecycle path as File→New.

**Recommendation**: This is acceptable, but consider:
- Adding a flag to track "auto-created default" vs "user-created"
- Consider allowing zero tabs (show splash screen instead)

### ⚠️ Issue 2: Exception Handling in destroy_canvas

```python
if self.lifecycle_adapter and drawing_area:
    try:
        self.lifecycle_adapter.destroy_canvas(drawing_area)
    except Exception as e:
        pass  # Failed to destroy canvas in lifecycle
```

The exception is silently swallowed. This could hide important cleanup errors.

**Recommendation**: Log the exception:
```python
except Exception as e:
    logger.error(f"Failed to destroy canvas {id(drawing_area)}: {e}")
```

### ⚠️ Issue 3: Legacy Cleanup After Lifecycle Destroy

The code cleans up legacy dictionaries **after** lifecycle destroy:

```python
# 4. Destroy lifecycle
lifecycle_adapter.destroy_canvas(drawing_area)

# 5. Cleanup legacy
del self.canvas_managers[drawing_area]
del self.simulation_controllers[drawing_area]
```

**Question**: Should legacy cleanup happen **before** lifecycle destroy?

**Answer**: Current order is correct because:
- Lifecycle destroy might need to access manager/controller
- Legacy cleanup is final cleanup after lifecycle is done

### ✅ Issue 4: Overlay Manager Cleanup

Overlay managers are properly cleaned up:

```python
if drawing_area in self.overlay_managers:
    overlay_manager = self.overlay_managers[drawing_area]
    overlay_manager.cleanup_overlays()
    del self.overlay_managers[drawing_area]
```

This ensures palettes and overlays don't leak.

## Conclusions

### ✅ Correct Lifecycle Flow

The canvas close tab flow **correctly follows** the Global Canvas State Life Cycle:

1. ✅ Checks for unsaved changes
2. ✅ Destroys canvas through lifecycle manager
3. ✅ Deletes ID scope to free namespace
4. ✅ Cleans up all resources (manager, controller, overlays, KB)
5. ✅ Creates default tab if needed (following same lifecycle)

### ✅ File→New Normalization

All canvases are created through a normalized path:

1. ✅ Load from UI template (consistent hierarchy)
2. ✅ Set ID scope before creating objects
3. ✅ Create through lifecycle manager
4. ✅ Reset simulation to clean state

### Recommendations

1. **Add logging to close_tab exception handling**
   ```python
   except Exception as e:
       logger.error(f"Failed to destroy canvas: {e}")
   ```

2. **Consider zero-tab state** (optional)
   - Show splash screen instead of auto-creating default tab
   - Forces user to explicitly create new canvas via File→New

3. **Add lifecycle event logging** (optional)
   - Log when canvases are created/destroyed
   - Helps debug multi-canvas issues

## Summary

**Status**: ✅ **CORRECT**

The canvas close tab functionality **properly integrates** with the Global Canvas State Life Cycle:

- Close button properly destroys canvas through lifecycle manager
- ID scopes are correctly deleted on close
- All resources are cleaned up (manager, controller, overlays, KB)
- Default tab creation follows same lifecycle path as File→New
- No lifecycle bypass detected

The requirement that "all new canvases must be created by File→New to normalize initial state" is **satisfied** because:
1. File→New uses `add_document()` → `_setup_canvas_manager()` → lifecycle
2. Default tab creation also uses `add_document()` → same path
3. Both flows set ID scope, create through lifecycle, and reset simulation

**No changes needed** - the implementation is correct.
