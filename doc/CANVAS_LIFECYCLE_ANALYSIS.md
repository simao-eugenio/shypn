# Canvas Lifecycle and Multi-Document Architecture Analysis

## Overview

This document analyzes the complete lifecycle of canvas documents in ShyPN, identifying all creation paths, state transitions, and wiring points for the Analyses Panel data_collector integration.

## Canvas Creation Scenarios

### 1. Startup Default Canvas
**Path:** `shypn.py:main()` → `create_model_canvas()` → `ModelCanvasLoader.load()`

```python
# shypn.py line ~151
model_canvas_loader = create_model_canvas()

# model_canvas_loader.py line ~103
def load(self):
    # Load UI file with default canvas defined in model_canvas.ui
    self.notebook.get_n_pages()  # Returns 1 (default canvas exists)
    
    # Line ~161
    self._setup_canvas_manager(drawing_area, overlay_box, overlay_widget)
```

**Timing Issue:**
- Canvas created BEFORE `right_panel_loader` exists
- `right_panel_loader` created at shypn.py line ~255
- Wiring happens at line ~374 via `wire_existing_canvases_to_right_panel()`

**Current State:** ❌ NOT WIRED - `wire_existing_canvases_to_right_panel()` not finding data_collector

---

### 2. File → New
**Path:** Menu action → `menu_actions.py` → `model_canvas_loader.add_document()`

```python
# menu_actions.py
def on_file_new(self, action, param):
    self.model_canvas_loader.add_document(filename=None, replace_empty_default=True)

# model_canvas_loader.py line ~460
def add_document(self, title=None, filename=None, replace_empty_default=True):
    # Line ~541: Create new tab
    self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)
```

**Timing:** ✅ `right_panel_loader` exists, wiring code in `_setup_edit_palettes()` executes

**Current State:** ✅ WORKING - data_collector wired successfully

---

### 3. File → Open
**Path:** Menu action → `file_explorer_panel.py` → SBML parser → canvas population

```python
# file_explorer_panel.py
def _open_file_in_canvas(self, file_path):
    # Opens .shy file and populates canvas
    # Does this create new document or use existing?
```

**Question:** Does File → Open call `add_document()` or populate existing canvas?

**Current State:** ⚠️ UNKNOWN - Need to trace file opening flow

---

### 4. Import SBML
**Path:** File menu → `sbml_import_panel.py` → Parser → Canvas creation

```python
# Import flow needs investigation
# Does it call add_document()? 
# Or directly manipulate canvas?
```

**Current State:** ⚠️ UNKNOWN - Need to trace SBML import flow

---

### 5. Import KEGG Pathway
**Path:** Pathway panel → KEGG fetch → Parser → Canvas creation

```python
# KEGG import flow needs investigation  
```

**Current State:** ⚠️ UNKNOWN - Need to trace KEGG import flow

---

## Canvas Setup Flow

### Complete Setup Chain

```
_setup_canvas_manager()
  ├─ Create ModelCanvasManager
  ├─ Wire callbacks (draw, dirty state)
  ├─ Create CanvasOverlayManager
  │   ├─ Create mode buttons [S] [E] [DEBUG]
  │   ├─ Create zoom control
  │   └─ Connect signals
  ├─ Store in self.overlay_managers[drawing_area]
  └─ _setup_edit_palettes()  ← DATA COLLECTOR WIRING POINT
      ├─ Create PaletteManager
      ├─ Create SwissKnifePalette
      │   └─ Create SimulateToolsPaletteLoader
      │       └─ Create SimulationDataCollector ← THE DATA WE NEED
      ├─ Connect palette signals
      └─ [WIRING CODE] Wire data_collector to right_panel_loader
          └─ IF right_panel_loader exists:
              └─ right_panel_loader.set_data_collector(data_collector)
```

### Wiring Code Location

**File:** `model_canvas_loader.py` line ~817-835

```python
# At END of _setup_edit_palettes()
if self.right_panel_loader and drawing_area in self.overlay_managers:
    overlay_manager = self.overlay_managers[drawing_area]
    if hasattr(overlay_manager, 'swissknife_palette'):
        swissknife = overlay_manager.swissknife_palette
        if hasattr(swissknife, 'registry'):
            simulate_tools_palette = swissknife.registry.get_widget_palette_instance('simulate')
            if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                data_collector = simulate_tools_palette.data_collector
                self.right_panel_loader.set_data_collector(data_collector)
```

**Problem:** This only works if `self.right_panel_loader` already exists!

---

## Initialization Order Issue

### Current Sequence (shypn.py)

```
1. Line ~151: model_canvas_loader = create_model_canvas()
   └─ Calls load() which sets up DEFAULT CANVAS
   └─ Calls _setup_canvas_manager() → _setup_edit_palettes()
   └─ BUT right_panel_loader is None! ❌

2. Line ~255: right_panel_loader = create_right_panel()
   └─ Creates panels (now always created, even without data_collector) ✅

3. Line ~369: model_canvas_loader.set_right_panel_loader(right_panel_loader)
   └─ Sets the reference

4. Line ~374: model_canvas_loader.wire_existing_canvases_to_right_panel()
   └─ Should retroactively wire startup canvas
   └─ BUT is it working? ❌ NO OUTPUT SEEN
```

### Why `wire_existing_canvases_to_right_panel()` Fails

**Hypothesis 1: overlay_managers not populated**
```python
for drawing_area, overlay_manager in self.overlay_managers.items():
```
- If `self.overlay_managers` is empty, loop doesn't run
- Need to verify: Is startup canvas added to `overlay_managers`?

**Hypothesis 2: swissknife_palette not created yet**
- SwissKnifePalette might be created lazily
- Or created but not yet in overlay_manager

**Hypothesis 3: data_collector not created at startup**
- SimulationDataCollector might only be created when needed
- Or created but not yet in simulate_tools_palette

---

## Investigation Required

### 1. Verify overlay_managers Population

**Check:** Is startup canvas added to `self.overlay_managers`?

**Location:** `_setup_canvas_manager()` line ~618
```python
self.overlay_managers[drawing_area] = overlay_manager
```

**Test:**
```python
def wire_existing_canvases_to_right_panel(self):
    print(f"overlay_managers keys: {list(self.overlay_managers.keys())}")
    print(f"overlay_managers count: {len(self.overlay_managers)}")
```

---

### 2. Verify SwissKnifePalette Creation Timing

**Check:** Is SwissKnifePalette created immediately in `_setup_edit_palettes()`?

**Location:** `_setup_edit_palettes()` line ~703
```python
swissknife_palette = SwissKnifePalette(...)
overlay_manager.swissknife_palette = swissknife_palette
```

**Test:**
```python
# In wire_existing_canvases_to_right_panel()
for drawing_area, overlay_manager in self.overlay_managers.items():
    print(f"Has swissknife: {hasattr(overlay_manager, 'swissknife_palette')}")
    if hasattr(overlay_manager, 'swissknife_palette'):
        print(f"Swissknife: {overlay_manager.swissknife_palette}")
```

---

### 3. Verify Data Collector Creation

**Check:** Is SimulationDataCollector created immediately?

**Location:** Need to trace SwissKnifePalette → SimulateToolsPaletteLoader → data_collector

**Test:**
```python
# Check if data_collector exists
simulate_tools = swissknife.registry.get_widget_palette_instance('simulate')
print(f"SimulateTools: {simulate_tools}")
print(f"Has data_collector: {hasattr(simulate_tools, 'data_collector')}")
if hasattr(simulate_tools, 'data_collector'):
    print(f"Data collector: {simulate_tools.data_collector}")
```

---

## Alternative Solutions

### Solution A: Lazy Wiring on First Use
Instead of wiring at startup, wire when user first adds an object to analysis:

```python
# In context_menu_handler.py
def add_to_analysis(self, obj):
    # Check if data_collector is wired
    if self.transition_panel.data_collector is None:
        # Wire it now
        self._wire_data_collector()
    
    self.transition_panel.add_object(obj)
```

**Pros:** Works regardless of initialization order
**Cons:** More complex, delayed wiring

---

### Solution B: Event-Based Wiring
Emit a signal when data_collector is created, right_panel subscribes:

```python
# SwissKnifePalette emits signal when ready
self.emit('data-collector-ready', data_collector)

# RightPanelLoader subscribes
swissknife.connect('data-collector-ready', self._on_data_collector_ready)
```

**Pros:** Clean, decoupled
**Cons:** Requires signal infrastructure

---

### Solution C: Deferred Wiring with GLib.idle_add
Wire after GTK main loop starts:

```python
# In shypn.py after setting right_panel_loader
GLib.idle_add(model_canvas_loader.wire_existing_canvases_to_right_panel)
```

**Pros:** Ensures all widgets are fully initialized
**Cons:** Timing still uncertain

---

### Solution D: Explicit Wiring in Tab Switch Handler
Always wire when tab becomes active:

```python
# In _on_notebook_page_changed()
def _on_notebook_page_changed(self, notebook, page, page_num):
    # Get drawing area for this page
    drawing_area = self._get_drawing_area_from_page(page)
    
    # Wire data_collector for this canvas
    self._wire_data_collector_for_canvas(drawing_area)
```

**Pros:** Simple, works for all scenarios
**Cons:** Redundant wiring on every tab switch

---

## Recommended Approach

### Hybrid: Deferred + Tab Switch

1. **Startup:** Use GLib.idle_add for deferred wiring
2. **Tab Switch:** Always ensure current tab is wired
3. **File Operations:** Explicit wiring in add_document()

```python
# shypn.py
model_canvas_loader.set_right_panel_loader(right_panel_loader)
GLib.idle_add(model_canvas_loader.wire_existing_canvases_to_right_panel)

# model_canvas_loader.py
def _on_notebook_page_changed(self, notebook, page, page_num):
    # ... existing code ...
    self._ensure_current_canvas_wired()

def _ensure_current_canvas_wired(self):
    """Ensure current canvas has data_collector wired to right panel."""
    if not self.right_panel_loader:
        return
    
    current_page_num = self.notebook.get_current_page()
    current_page = self.notebook.get_nth_page(current_page_num)
    drawing_area = self._get_drawing_area_from_page(current_page)
    
    if drawing_area and drawing_area in self.overlay_managers:
        overlay_manager = self.overlay_managers[drawing_area]
        # ... wire data_collector ...
```

---

## Next Steps

1. **Add comprehensive debug logging** to trace:
   - overlay_managers population
   - SwissKnifePalette creation
   - data_collector availability
   - Wiring attempts and results

2. **Test all canvas creation scenarios:**
   - Startup default canvas
   - File → New
   - File → Open
   - Import SBML
   - Import KEGG

3. **Implement hybrid wiring solution**

4. **Create test suite** for canvas lifecycle

5. **Document final architecture** in this file

---

## Current Status

- ✅ Panels created at startup (always)
- ✅ File → New wiring works
- ❌ Startup canvas wiring FAILS (no output from wire_existing_canvases)
- ⚠️ Other creation scenarios UNKNOWN

## Investigation Priority

**IMMEDIATE:** Why is `wire_existing_canvases_to_right_panel()` producing no output?
- Is it being called?
- Is overlay_managers empty?
- Is swissknife_palette missing?
- Is data_collector not created yet?

Add aggressive logging to find out!
