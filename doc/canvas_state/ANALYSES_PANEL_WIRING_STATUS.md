# Analyses Panel Wiring Status - Startup Canvas Issue

## Current Status: INVESTIGATION NEEDED

**Date:** October 24, 2025  
**Issue:** Analyses Panel plotting works for File → New scenario but NOT for startup default canvas  
**Symptom:** Panel shows "No places/transition selected" on startup canvas even after adding items

---

## Problem Summary

### What Works ✅
- **Panel Creation:** All widgets (listbox, clear button, matplotlib canvas) are now visible at startup
- **Context Menu:** "Add to Analysis" option appears and items are added to the list
- **File → New Scenario:** Creating P-T-P and adding to analysis works perfectly - plot appears

### What Doesn't Work ❌
- **Startup Canvas:** On the default canvas that exists at app launch (before File → New):
  - Items appear in the analysis list
  - But plot shows "No places/transition selected"
  - This means `data_collector` is not wired to the right panel

---

## Root Cause Analysis

### The Initialization Order Problem

```
Timeline of app initialization:
1. Line 151 (shypn.py): model_canvas_loader.load() called
   └─ Creates startup default canvas
   └─ Calls _setup_edit_palettes() 
      └─ Creates SwissKnifePalette with SimulateToolsPaletteLoader
      └─ Wiring code checks: if self.right_panel_loader...
         └─ right_panel_loader is None! ❌ No wiring happens

2. Line 255 (shypn.py): right_panel_loader created

3. Line 374 (shypn.py): model_canvas_loader.set_right_panel_loader() called

4. Line 378 (shypn.py): model_canvas_loader.wire_existing_canvases_to_right_panel() called
   └─ SHOULD wire the startup canvas retroactively
   └─ Current status: Unknown if this is executing
```

### The Architecture Issue

The app uses a **multi-canvas document architecture** where data_collector must be wired for EACH canvas:

**Canvas Creation Scenarios:**
1. **Startup Default Canvas** - Created BEFORE right_panel_loader exists ❌
2. **File → New** - Created AFTER right_panel_loader exists ✅
3. **File → Open** - Status unknown ⚠️
4. **Import SBML** - Status unknown ⚠️
5. **Import KEGG** - Status unknown ⚠️

---

## Implementation Details

### Wiring Locations in Code

#### Location 1: _setup_edit_palettes() (model_canvas_loader.py ~815-840)
**When:** Called for EVERY canvas creation  
**Status:** ✅ Works for File → New  
**Code Path:**
```python
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

**Issue:** For startup canvas, `self.right_panel_loader` is None when this runs.

#### Location 2: _on_notebook_page_changed() (model_canvas_loader.py ~213-228)
**When:** Called on tab switches  
**Status:** ✅ Recently fixed to use `registry` path (was using old `widget_palette_instances`)  
**Code Path:** Same as Location 1

**Recent Fix:** Changed from:
```python
simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
```
To:
```python
simulate_tools_palette = swissknife.registry.get_widget_palette_instance('simulate')
```

#### Location 3: wire_existing_canvases_to_right_panel() (model_canvas_loader.py ~2374)
**When:** Called once after both loaders initialized (shypn.py line 381)  
**Status:** ❓ Unknown - debug output not appearing  
**Strategy:** Triggers `_on_notebook_page_changed()` for current page

**Current Implementation:**
```python
def wire_existing_canvases_to_right_panel(self):
    """Retroactively wire startup canvas by triggering page changed handler."""
    if not self.right_panel_loader:
        return
    
    current_page_num = self.notebook.get_current_page()
    current_page = self.notebook.get_nth_page(current_page_num)
    self._on_notebook_page_changed(self.notebook, current_page, current_page_num)
```

---

## Debug Investigation Status

### Debug Output Added
- ✅ Added extensive print statements in `wire_existing_canvases_to_right_panel()`
- ✅ Added print statements in `set_data_collector()` 
- ✅ Added print statements in `_on_notebook_page_changed()`
- ✅ Added exception handling in shypn.py wiring call

### Debug Results
- ❌ **No debug output visible** when running with grep filters
- ❌ **No debug files created** when writing to disk
- ⚠️ **Possible causes:**
  1. Output buffering issues
  2. Code path not executing
  3. Exception being thrown and caught silently
  4. GTK event loop timing issues

### What We Tried
1. File writes to `/tmp/` - directory not accessible
2. File writes to project directory - files not created
3. Print statements to stderr - no output visible in grep
4. Background process execution - app doesn't reach on_activate()

---

## Code Changes Made

### Files Modified

#### 1. right_panel_loader.py
**Line 94:** ALWAYS create panels (removed data_collector check)
```python
# OLD: if self.data_collector is not None:
# NEW: Always call _setup_plotting_panels()
self._setup_plotting_panels()
```

**Line 237-252:** Simplified set_data_collector() to update existing panels
```python
def set_data_collector(self, data_collector):
    self.data_collector = data_collector
    # Update existing panels (created at startup with None data_collector)
    if self.place_panel:
        self.place_panel.data_collector = data_collector
    if self.transition_panel:
        self.transition_panel.data_collector = data_collector
    if self.diagnostics_panel:
        self.diagnostics_panel.set_data_collector(data_collector)
```

#### 2. model_canvas_loader.py
**Line 225:** Fixed _on_notebook_page_changed() to use registry
```python
# OLD: simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
# NEW: simulate_tools_palette = swissknife.registry.get_widget_palette_instance('simulate')
```

**Lines 2374-2402:** Added wire_existing_canvases_to_right_panel()
```python
def wire_existing_canvases_to_right_panel(self):
    """Retroactively wire startup canvas."""
    if not self.right_panel_loader:
        return
    current_page_num = self.notebook.get_current_page()
    current_page = self.notebook.get_nth_page(current_page_num)
    self._on_notebook_page_changed(self.notebook, current_page, current_page_num)
```

**Lines 815-840:** Updated _setup_edit_palettes() wiring to use registry
- Already was using registry path for File → New (working)

#### 3. plot_panel.py, transition_rate_panel.py, place_rate_panel.py
Added safety checks for None data_collector:
```python
if not self.data_collector:
    return []  # or return True for periodic updates
```

#### 4. shypn.py
**Lines 84-90:** Added debug marker at on_activate() start
**Lines 377-387:** Added try-except around wire_existing_canvases_to_right_panel() call

---

## Next Steps - TODO

### Immediate Investigation Needed
1. **Verify wire_existing_canvases_to_right_panel() is being called**
   - Run app from terminal: `python3 src/shypn.py 2>&1 | grep -E "\[SHYPN\]|\[MODEL_CANVAS\]|\[RIGHT_PANEL\]"`
   - Look for debug messages during startup
   - If no messages appear, investigate why on_activate() isn't reaching line 381

2. **If function IS called but not working:**
   - Check if `swissknife.registry` exists at that point
   - Check if `data_collector` is created yet at startup time
   - May need deferred wiring with GLib.idle_add()

3. **If function is NOT called:**
   - Check for exceptions in initialization
   - Verify app is using correct entry point
   - Check if there's an early return or exception before line 381

### Alternative Solutions to Consider

#### Option A: Deferred Wiring with GLib.idle_add()
```python
# In shypn.py after initialization
GLib.idle_add(model_canvas_loader.wire_existing_canvases_to_right_panel)
```
**Pros:** Ensures GTK loop is fully started  
**Cons:** Adds delay, timing uncertainty

#### Option B: Wire on First Tab Switch
```python
# In _on_notebook_page_changed()
if not self._startup_wiring_done:
    self._startup_wiring_done = True
    # Force wiring for current canvas
```
**Pros:** Reliable, happens when canvas is definitely ready  
**Cons:** Requires manual tab switch to trigger (unless we emit fake switch)

#### Option C: Lazy Wiring on Context Menu
```python
# In context_menu_handler when "Add to Analysis" clicked
if not self.right_panel_loader.data_collector:
    # Wire now, on demand
```
**Pros:** Guaranteed to wire before first use  
**Cons:** Reactive rather than proactive

#### Option D: Emit Fake Tab Switch Event
```python
# After wire_existing_canvases_to_right_panel() call
self.notebook.emit('switch-page', current_page, current_page_num)
```
**Pros:** Uses GTK's signal mechanism  
**Cons:** May cause side effects

---

## Testing Checklist

### Scenarios to Test After Fix

- [ ] **Startup Canvas (PRIMARY ISSUE)**
  - Launch app
  - Create P-T-P on default canvas
  - Add to analysis
  - Click simulate
  - **Expected:** Plot appears

- [ ] **File → New (WORKING)**
  - File → New
  - Create P-T-P
  - Add to analysis
  - Click simulate
  - **Expected:** Plot appears ✅

- [ ] **File → Open**
  - Open existing .shypn file
  - Add transition to analysis
  - Click simulate
  - **Expected:** Plot appears

- [ ] **Import SBML**
  - Import SBML model
  - Add transition to analysis
  - Click simulate
  - **Expected:** Plot appears

- [ ] **Import KEGG**
  - Import KEGG pathway
  - Add transition to analysis
  - Click simulate
  - **Expected:** Plot appears

- [ ] **Tab Switching**
  - Create multiple documents
  - Add items to analysis
  - Switch tabs
  - **Expected:** Plot updates correctly

---

## Technical Notes

### SwissKnifePalette Architecture
- Uses `swissknife_palette_new.py` (not old version)
- Has `registry` attribute (SubPaletteRegistry instance)
- Registry stores widget_palette_instances (like SimulateToolsPaletteLoader)
- Access path: `swissknife.registry.get_widget_palette_instance('simulate')`

### Data Collector Lifecycle
1. Created in SimulateToolsPaletteLoader.__init__()
2. Stored as simulate_tools_palette.data_collector
3. Must be wired to right_panel_loader.set_data_collector()
4. Timing: Created with SwissKnifePalette during _setup_edit_palettes()

### Why File → New Works
When File → New creates a canvas:
1. right_panel_loader already exists
2. _setup_edit_palettes() wiring code executes
3. Check `if self.right_panel_loader` passes ✅
4. data_collector is wired immediately

### Why Startup Canvas Fails
When startup canvas is created:
1. right_panel_loader doesn't exist yet
2. _setup_edit_palettes() wiring code executes
3. Check `if self.right_panel_loader` fails ❌
4. No wiring happens
5. Retroactive wiring should fix this... but status unknown

---

## Related Documentation

- **doc/CANVAS_LIFECYCLE_ANALYSIS.md** - Comprehensive analysis of multi-canvas architecture
- **doc/ANALYSES_PANEL_PERFORMANCE_COMPLETE.md** - Panel creation fixes
- **doc/ANALYSES_SOURCE_SINK_COMPLETE.md** - Source/sink analysis implementation

---

## Contact/Resume Point

**Where we left off:**
- All wiring code is in place and looks correct
- Debug output not appearing - can't verify execution
- Need to run app from terminal with visible output to see debug messages
- User will test with: `python3 src/shypn.py 2>&1 | grep -E "\[SHYPN\]|\[MODEL_CANVAS\]|\[RIGHT_PANEL\]"`

**Key Question to Answer:**
Is `wire_existing_canvases_to_right_panel()` being called at all? If yes, why isn't it wiring? If no, why not?

**Most Likely Solutions:**
1. If not being called: Fix exception or early return in on_activate()
2. If being called but not working: Use GLib.idle_add() for deferred wiring
3. If timing issue: Emit fake tab switch event after initialization
