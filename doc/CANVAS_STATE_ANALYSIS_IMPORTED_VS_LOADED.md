# Canvas State Analysis: Automatically Imported vs Loaded Canvases

## Problem Statement

Property dialogs (especially transition dialogs) crash with Wayland Error 71 on **automatically created canvases** (KEGG/SBML imports), but work fine on:
- Manually created canvases (File → New)
- File-loaded canvases (File → Open)

This suggests a state initialization difference between import paths and manual/load paths.

---

## Canvas Creation Paths

### Path 1: Manual Canvas Creation (File → New)
**Location**: `src/shypn/helpers/model_canvas_loader.py`

```python
def add_document(self, filename=None):
    # Line ~541
    self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)
```

**Flow**:
```
1. add_document() creates new tab
2. _setup_canvas_manager() initializes:
   - ModelCanvasManager with filename
   - manager.create_new_document(filename)
   - Overlay manager and palettes
   - _setup_edit_palettes() wires SwissKnifePalette
3. Empty canvas ready for manual editing
```

**State**:
- `manager._is_imported = False` (default)
- `manager.filepath = None` (not set)
- `manager.filename = "default"` or custom
- `manager._is_dirty = False`
- **Objects loaded**: NONE (empty canvas)

---

### Path 2: File → Open (Load from .shy file)
**Location**: `src/shypn/helpers/file_explorer_panel.py`

```python
def _load_document_into_canvas(self, document, filepath):
    # Line ~1815
    page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
    manager = self.canvas_loader.get_canvas_manager(drawing_area)
    
    # Load objects using UNIFIED PATH
    manager.load_objects(
        places=document.places,
        transitions=document.transitions,
        arcs=document.arcs
    )
    
    # CRITICAL: Set change callback
    manager.document_controller.set_change_callback(manager._on_object_changed)
    
    # Restore view state
    if hasattr(document, 'view_state') and document.view_state:
        manager.zoom = document.view_state.get('zoom', 1.0)
        manager.pan_x = document.view_state.get('pan_x', 0.0)
        manager.pan_y = document.view_state.get('pan_y', 0.0)
        manager._initial_pan_set = True
    
    # Fit to page
    manager.fit_to_page(padding_percent=15, deferred=True, 
                        horizontal_offset_percent=30, vertical_offset_percent=10)
    
    # PHASE 1: Set per-document file state
    manager.set_filepath(filepath)  # ✅ Sets filepath
    manager.mark_clean()            # ✅ Marks as clean (just loaded)
```

**State**:
- `manager._is_imported = False` (default)
- `manager.filepath = "/full/path/to/file.shy"` ✅ **SET**
- `manager.filename = "file"` (from filepath)
- `manager._is_dirty = False` (marked clean)
- **Objects loaded**: Via `manager.load_objects()` ✅
- **Change callback**: Set ✅

---

### Path 3: KEGG Import (Automatic creation)
**Location**: `src/shypn/helpers/kegg_import_panel.py`

```python
def _on_import_complete(self, document_model):
    # Line ~423
    page_index, drawing_area = self.model_canvas.add_document(filename=pathway_name)
    manager = self.model_canvas.get_canvas_manager(drawing_area)
    
    # Load objects using UNIFIED PATH
    manager.load_objects(
        places=document_model.places,
        transitions=document_model.transitions,
        arcs=document_model.arcs
    )
    
    # Set change callback
    manager.document_controller.set_change_callback(manager._on_object_changed)
    
    # Fit to page
    manager.fit_to_page(padding_percent=15, deferred=True, 
                       horizontal_offset_percent=30, vertical_offset_percent=10)
    
    # Trigger redraw
    drawing_area.queue_draw()
    
    # Mark as imported
    manager.mark_as_imported(pathway_name)  # ✅ Sets _is_imported = True
    
    # ❌ NO set_filepath() call
    # ❌ NO mark_clean() call
```

**State**:
- `manager._is_imported = True` ✅ **MARKED AS IMPORTED**
- `manager.filepath = None` ❌ **NOT SET**
- `manager.filename = "pathway_name"` (descriptive name)
- `manager._is_dirty = False` (default, but should be marked?)
- **Objects loaded**: Via `manager.load_objects()` ✅
- **Change callback**: Set ✅

---

### Path 4: SBML Import (Automatic creation)
**Location**: `src/shypn/helpers/sbml_import_panel.py`

```python
def _on_load_complete(self, document_model, pathway_name):
    # Line ~702
    page_index, drawing_area = self.model_canvas.add_document(filename=pathway_name)
    manager = self.model_canvas.get_canvas_manager(drawing_area)
    
    # Load objects using UNIFIED PATH
    manager.load_objects(
        places=document_model.places,
        transitions=document_model.transitions,
        arcs=document_model.arcs
    )
    
    # Set change callback
    manager.document_controller.set_change_callback(manager._on_object_changed)
    
    # Fit to page
    manager.fit_to_page(padding_percent=15, deferred=True, 
                       horizontal_offset_percent=30, vertical_offset_percent=10)
    
    # Trigger redraw
    drawing_area.queue_draw()
    
    # Mark as imported
    manager.mark_as_imported(pathway_name)
    
    # ❌ NO set_filepath() call
    # ❌ NO mark_clean() call
```

**State**:
- `manager._is_imported = True` ✅ **MARKED AS IMPORTED**
- `manager.filepath = None` ❌ **NOT SET**
- `manager.filename = "pathway_name"` (descriptive name)
- `manager._is_dirty = False` (default)
- **Objects loaded**: Via `manager.load_objects()` ✅
- **Change callback**: Set ✅

---

## State Comparison Table

| State Property | Manual (New) | File Load | KEGG Import | SBML Import |
|----------------|-------------|-----------|-------------|-------------|
| `_is_imported` | `False` | `False` | `True` ✅ | `True` ✅ |
| `filepath` | `None` | `"/path/file.shy"` ✅ | `None` ❌ | `None` ❌ |
| `filename` | `"default"` | `"file"` | `"pathway"` | `"pathway"` |
| `_is_dirty` | `False` | `False` (marked) | `False` (default) | `False` (default) |
| **Objects loaded** | None | Via `load_objects()` | Via `load_objects()` | Via `load_objects()` |
| **Change callback** | Set | Set ✅ | Set ✅ | Set ✅ |
| **Filepath set** | No | Yes ✅ | No ❌ | No ❌ |
| **Mark clean** | No | Yes ✅ | No ❌ | No ❌ |

---

## Critical Differences

### ❌ Missing: `set_filepath()` Call

**File Load Path** (WORKS):
```python
manager.set_filepath(filepath)  # Sets manager.filepath = "/full/path/to/file.shy"
```

**Import Paths** (CRASHES):
```python
# NO set_filepath() call
# manager.filepath remains None
```

### ❌ Missing: `mark_clean()` Call

**File Load Path** (WORKS):
```python
manager.mark_clean()  # Sets _is_dirty = False, triggers callback
```

**Import Paths** (CRASHES):
```python
# NO mark_clean() call
# _is_dirty remains at default False but callback not triggered
```

---

## Hypothesis: Dialog Creation Dependency on Filepath

### Property Dialog Initialization Chain

When opening a transition property dialog:

```python
# src/shypn/helpers/model_canvas_loader.py:2920
def _on_object_properties(self, obj, manager, drawing_area):
    # Check for data_collector from simulate palette
    if drawing_area in self.overlay_managers:
        overlay_manager = self.overlay_managers[drawing_area]
        if hasattr(overlay_manager, 'swissknife_palette'):
            swissknife = overlay_manager.swissknife_palette
            
            # Try to get simulate_tools from registry
            if hasattr(swissknife, 'registry'):
                simulate_tools = swissknife.registry.widget_palette_instances.get('simulate')
                if simulate_tools:
                    data_collector = simulate_tools.data_collector
    
    # Create dialog
    dialog_loader = create_transition_prop_dialog(
        obj, 
        parent_window=self.parent_window,
        persistency_manager=self.persistency,
        model=manager,
        data_collector=data_collector  # ⚠️ May be None
    )
```

### Potential Issue: SwissKnife Palette State

The SwissKnifePalette is created in `_setup_edit_palettes()`:

```python
# Line ~715
swissknife_palette = SwissKnifePalette(
    mode='edit',
    model=canvas_manager,
    tool_registry=tool_registry
)
```

**Question**: Does the palette initialization depend on canvas state?

---

## Testing Hypothesis

### Test 1: Add set_filepath() to Import Paths

**KEGG Import** (`kegg_import_panel.py:~475`):
```python
# After mark_as_imported()
manager.mark_as_imported(pathway_name)

# ADD THIS:
if self.project:
    # Set a temporary filepath so canvas isn't "unsaved"
    temp_path = os.path.join(self.project.pathways_dir, f"{pathway_name}.shy")
    manager.set_filepath(temp_path)
```

**SBML Import** (`sbml_import_panel.py:~730`):
```python
# After mark_as_imported()
manager.mark_as_imported(pathway_name)

# ADD THIS:
if self.project:
    temp_path = os.path.join(self.project.pathways_dir, f"{pathway_name}.shy")
    manager.set_filepath(temp_path)
```

### Test 2: Add mark_clean() to Import Paths

**KEGG Import** (`kegg_import_panel.py:~475`):
```python
# After mark_as_imported()
manager.mark_as_imported(pathway_name)

# ADD THIS:
manager.mark_clean()  # Explicitly mark as clean (no unsaved changes yet)
```

**SBML Import** (`sbml_import_panel.py:~730`):
```python
# After mark_as_imported()
manager.mark_as_imported(pathway_name)

# ADD THIS:
manager.mark_clean()
```

---

## Alternative Hypothesis: Palette Registry State

### SwissKnife Palette Architecture

The SwissKnifePalette uses a registry to store widget palettes:

```python
# swissknife_palette_new.py
class SwissKnifePalette:
    def __init__(self, mode='edit', model=None, tool_registry=None):
        self.registry = WidgetPaletteRegistry()
        
        # Register simulate palette
        if mode == 'edit':
            simulate_loader = SimulateToolsPaletteLoader(model)
            self.registry.register('simulate', simulate_loader)
```

**Question**: Is the simulate_loader initialization affected by canvas state?

---

## Potential Root Causes

### 1. Missing Filepath Breaks Dialog Parent Chain
- Dialog creation may check `manager.filepath` to determine parent window
- If `filepath is None`, parent window validation fails
- Wayland rejects dialog without proper parent

### 2. Missing mark_clean() Leaves Dirty State Inconsistent
- Dialog initialization may check `manager._is_dirty` state
- Inconsistent dirty state causes widget hierarchy issues
- Wayland detects orphaned widget and crashes

### 3. SwissKnife Palette Not Fully Initialized
- Simulate palette loader may need canvas metadata
- Without filepath, palette initialization incomplete
- Dialog tries to access incomplete palette state → crash

### 4. Overlay Manager State Mismatch
- Overlay manager created same way for all paths
- But registry state may differ based on canvas metadata
- Import paths don't trigger some initialization callback

---

## Recommended Fix Priority

### Priority 1: Add set_filepath() and mark_clean()
**Impact**: Low risk, high potential
**Rationale**: Matches the working file load path exactly

```python
# In both KEGG and SBML import completion handlers:
manager.mark_as_imported(pathway_name)
manager.mark_clean()  # ✅ NEW

# Only if project exists:
if self.project:
    temp_path = os.path.join(self.project.pathways_dir, f"{pathway_name}.shy")
    manager.set_filepath(temp_path)  # ✅ NEW
```

### Priority 2: Debug Palette Initialization
**Impact**: Medium risk, medium potential
**Rationale**: Log palette state to see if registry incomplete

```python
# After loading objects, before fit_to_page:
print(f"[DEBUG] Overlay manager: {self.model_canvas.overlay_managers.get(drawing_area)}")
if drawing_area in self.model_canvas.overlay_managers:
    om = self.model_canvas.overlay_managers[drawing_area]
    print(f"[DEBUG] Has swissknife: {hasattr(om, 'swissknife_palette')}")
    if hasattr(om, 'swissknife_palette'):
        sk = om.swissknife_palette
        print(f"[DEBUG] Has registry: {hasattr(sk, 'registry')}")
        if hasattr(sk, 'registry'):
            print(f"[DEBUG] Registry palettes: {list(sk.registry.widget_palette_instances.keys())}")
```

### Priority 3: Verify Drawing Area Registry
**Impact**: High risk, low probability
**Rationale**: Nuclear option - check if drawing_area key mismatch

---

## Next Steps

1. ✅ **Document analysis complete**
2. ⏳ **Implement Priority 1 fix** (add filepath + mark_clean)
3. ⏳ **Test on KEGG import**
4. ⏳ **Test on SBML import**
5. ⏳ **If still crashes, proceed to Priority 2 debug logging**

---

**Status**: Analysis Complete  
**Date**: October 26, 2025  
**Priority**: HIGH - Blocks property dialog functionality on imports
