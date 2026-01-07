# KEGG Import Category Collapse Analysis

## Problem Statement
When KEGG import completes and auto-loads the model to canvas, the Pathway Operations panel categories collapse unexpectedly.

## Import Flow Trace

### 1. Import Button Click
**File:** `kegg_category.py:_on_import_button_clicked()`
- User clicks "Save to Project" button
- Starts import thread
- Category is **EXPANDED** (user is interacting with it)

### 2. Import Thread Completes
**File:** `kegg_category.py:_on_import_thread_complete()`
- Line ~950-1050: Auto-load sequence begins
- Creates new canvas tab via `canvas_loader.add_document()`
- Loads objects to canvas via `canvas_manager.load_objects()`

### 3. Report Panel Refresh (FIRST TRIGGER)
**File:** `kegg_category.py` Line ~1032-1045
```python
GLib.idle_add(refresh_report_panel)
```

Inside `refresh_report_panel()`:
- Line ~1040: `report_panel_loader.panel.set_controller(simulation_controller)`
- Line ~1048: `report_panel_loader.panel.on_file_opened(shypn_path)`

### 4. Report Panel `on_file_opened()` (SECOND TRIGGER)
**File:** `report_panel.py:on_file_opened()` Line ~746-777

```python
def delayed_refresh():
    current_manager = self.model_canvas_loader.get_current_model()
    if current_manager:
        for category in self.categories:
            if hasattr(category, 'set_model_canvas'):
                category.set_model_canvas(current_manager)  # ⚠️ THIS CALL!
        self.refresh_all()
```

**Problem:** This calls `set_model_canvas()` on ALL Report Panel categories after 100ms delay!

### 5. Pathway Operations Panel Update (THIRD TRIGGER)  
**File:** `model_canvas_loader.py:_setup_edit_palettes()` Line ~2366

When setting up panels for new canvas:
```python
if hasattr(self.overlay_managers[drawing_area], 'pathway_panel_loader'):
    pathway_loader = self.overlay_managers[drawing_area].pathway_panel_loader
    if pathway_loader and hasattr(pathway_loader, 'panel') and pathway_loader.panel:
        report_panel_loader.panel.set_pathway_operations_panel(pathway_loader.panel)
```

But more critically, when canvas is created:
**File:** `pathway_operations_panel.py:__init__()` Line ~134
```python
if model_canvas:
    self.set_model_canvas(model_canvas)
```

### 6. PathwayOperationsPanel `set_model_canvas()` (FOURTH TRIGGER)
**File:** `pathway_operations_panel.py:set_model_canvas()` Line ~251-267

```python
def set_model_canvas(self, model_canvas):
    self.model_canvas = model_canvas
    
    # Propagate to all categories
    self.kegg_category.set_model_canvas(model_canvas)  # ⚠️ THIS CALL!
    self.sbml_category.set_model_canvas(model_canvas)
    self.bigg_category.set_model_canvas(model_canvas)
    # ... all other categories
```

### 7. KEGGCategory `set_model_canvas()` (COLLAPSE POINT!)
**File:** `kegg_category.py:set_model_canvas()` Line ~205-217

```python
def set_model_canvas(self, model_canvas):
    super().set_model_canvas(model_canvas)
    
    # Store current expanded state before refresh
    was_expanded = self.expanded
    
    # Trigger tab switch handling and metadata refresh
    self.on_tab_switched()  # ⚠️ Calls refresh_metadata_inspector()
    
    # Restore expanded state if it was expanded
    if was_expanded:
        self.set_expanded(True)  # ⚠️ BUT TIMING IS CRITICAL!
```

## Root Cause Analysis

### The Collapse Mechanism

The issue is a **timing race condition** with multiple `set_model_canvas()` calls:

1. **During Import (User Context)**
   - KEGG category is expanded (user clicked "Save to Project")
   - `self.expanded = True`

2. **Report Panel Delayed Refresh (100ms delay)**
   - Line ~777: `GLib.timeout_add(100, delayed_refresh)`
   - This eventually calls `kegg_category.set_model_canvas()`

3. **CategoryFrame Behavior**
   - When `set_expanded(True)` is called, it updates visibility
   - But if another `set_expanded()` or initialization happens immediately after, it can reset

4. **The Race**
   ```
   Time 0ms:    Import completes
   Time 1ms:    GLib.idle_add(refresh_report_panel) scheduled
   Time 2ms:    refresh_report_panel() executes
   Time 3ms:    report_panel.on_file_opened() called
   Time 103ms:  delayed_refresh() executes  ← RACE POINT!
   Time 104ms:  set_model_canvas() on all Pathway Operation categories
   Time 105ms:  on_tab_switched() → refresh_metadata_inspector()
   Time 106ms:  set_expanded(True) attempts to restore
   Time 107ms:  BUT another set_model_canvas() might be pending!
   ```

### Multiple `set_model_canvas()` Cascades

The problem is **cascading `set_model_canvas()` calls**:

1. First cascade: Report Panel categories get updated
2. Second cascade: Pathway Operations categories get updated via `pathway_operations_panel.set_model_canvas()`
3. Each cascade triggers `on_tab_switched()` which might interfere with expansion state

## Solutions

### Current Fix (Incomplete)
**File:** `kegg_category.py:set_model_canvas()`
```python
was_expanded = self.expanded
self.on_tab_switched()
if was_expanded:
    self.set_expanded(True)
```

**Problem:** This only helps if there's a single `set_model_canvas()` call. Multiple cascading calls will still collapse the category.

### Proposed Solutions

#### Option 1: Prevent Cascade (Recommended)
**Don't call `set_model_canvas()` on Pathway Operations from Report Panel**

The Report Panel's `on_file_opened()` should ONLY update its own categories, not trigger updates on unrelated panels.

**File:** `report_panel.py:on_file_opened()`
- Remove or guard the `set_model_canvas()` call to non-Report categories
- Pathway Operations already has its own mechanisms to detect canvas changes

#### Option 2: Defer Expansion Restoration
Instead of immediately restoring, schedule it for later:

```python
def set_model_canvas(self, model_canvas):
    super().set_model_canvas(model_canvas)
    was_expanded = self.expanded
    self.on_tab_switched()
    
    # Defer restoration to ensure it happens AFTER all cascades
    if was_expanded:
        from gi.repository import GLib
        def restore_expansion():
            self.set_expanded(True)
            return False  # Don't repeat
        GLib.timeout_add(200, restore_expansion)  # 200ms after last cascade
```

#### Option 3: Lock Expansion State During Import
Add a flag to prevent collapse during active import:

```python
class KEGGCategory:
    def __init__(self, ...):
        self._import_in_progress = False
        self._locked_expansion_state = None
    
    def _on_import_button_clicked(self):
        self._import_in_progress = True
        self._locked_expansion_state = self.expanded
        # ... import logic ...
    
    def set_expanded(self, expanded):
        # During import, prevent external collapse
        if self._import_in_progress and self._locked_expansion_state:
            expanded = self._locked_expansion_state
        super().set_expanded(expanded)
    
    def _on_import_thread_complete(self):
        # ... after all cascades complete ...
        def unlock_and_restore():
            self._import_in_progress = False
            if self._locked_expansion_state:
                self.set_expanded(True)
            self._locked_expansion_state = None
            return False
        GLib.timeout_add(300, unlock_and_restore)
```

## Key Insights

1. **Multiple Panels Share Canvas**: Report Panel, Pathway Operations, Topology, etc. all react to canvas changes
2. **Cascade Effect**: Each panel's `set_model_canvas()` can trigger updates in child panels
3. **GTK Event Loop**: `GLib.idle_add()` and `GLib.timeout_add()` create timing dependencies
4. **CategoryFrame State**: The `expanded` attribute is fragile during rapid updates

## Recommended Fix

**Implement Option 3 (Lock Expansion State)**

This is the most robust solution because:
- Prevents ANY external collapse during import
- Survives multiple `set_model_canvas()` cascades
- Explicitly restores state after all processing completes
- No risk of timing races

The lock ensures the category stays expanded from the moment the user clicks "Save to Project" until the final metadata expander expansion at the end of the import pipeline.
