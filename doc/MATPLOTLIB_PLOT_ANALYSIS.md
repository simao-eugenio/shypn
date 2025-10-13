# Matplotlib Plot Path Analysis - Complete Flow

**Date**: October 12, 2025  
**Status**: Analysis Complete  
**Scope**: Transition type signaling, plot updates, search mechanism, reset functionality

## Executive Summary

**CRITICAL ISSUE FOUND**: The `_on_simulation_reset()` handler in `model_canvas_loader.py` does **NOT** call `data_collector.clear()`, causing matplotlib plots to retain old data after reset. This is the root cause of the "plot path not updating" issue.

The simulation controller's `reset()` method DOES clear the data collector (line 1489 in controller.py), but the matplotlib panels are not being properly blanked to show empty state after reset.

## Architecture Overview

```
User Action → Simulate Palette → Simulation Controller → Data Collector → Matplotlib Panels
     ↓               ↓                    ↓                     ↓              ↓
  [Reset]    emit('reset-executed')   reset()            clear()        _show_empty_state()
                     ↓                    ↓                     ↓              ↓
            SwissKnifePalette      Reset places to      Clear data      Blank canvas
                     ↓              initial_marking      dictionaries
            model_canvas_loader    
              _on_simulation_reset()
                     ↓
              ❌ MISSING: Does NOT trigger canvas blanking!
```

## Component-by-Component Analysis

### 1. Transition Type Signaling to Matplotlib ✅ WORKING

**Location**: `src/shypn/analyses/plot_panel.py` and `transition_rate_panel.py`

**Status**: ✅ **Correctly Implemented**

#### Code Flow:

**Line 270-272 in plot_panel.py**:
```python
transition_type = getattr(obj, 'transition_type', 'immediate')
type_abbrev = {'immediate': 'IMM', 'timed': 'TIM', 'stochastic': 'STO', 
               'continuous': 'CON'}.get(transition_type, transition_type[:3].upper())
label_text = f'{obj_name} [{type_abbrev}] ({self.object_type[0].upper()}{obj.id})'
```

**Line 398-401 in transition_rate_panel.py** (plot update):
```python
transition_type = getattr(obj, 'transition_type', 'immediate')
type_abbrev = {...}.get(transition_type, transition_type[:3].upper())
legend_label = f'{obj_name} [{type_abbrev}]'
self.axes.plot(times, rates, label=legend_label, color=color, linewidth=2.5)
```

**Line 421-437 in transition_rate_panel.py** (list UI with source/sink):
```python
is_source = getattr(obj, 'is_source', False)
is_sink = getattr(obj, 'is_sink', False)

# Add source/sink indicator
if is_source:
    type_abbrev += '+SRC'
elif is_sink:
    type_abbrev += '+SNK'
```

**Verification**:
- ✅ Transition type is read from `obj.transition_type` attribute
- ✅ Type abbreviations displayed in both legend and UI list
- ✅ Source/sink status included in UI labels
- ✅ Dynamic: Uses `getattr()` to read current state, not cached values

**Conclusion**: Transition type signaling is **correctly implemented** and reads current state dynamically.

---

### 2. Plot Data Update Mechanism ✅ WORKING

**Location**: `src/shypn/analyses/plot_panel.py`

**Status**: ✅ **Correctly Implemented**

#### Update Flow:

```
Simulation Step → controller.notify_step_listeners() → data_collector.on_simulation_step()
                                    ↓
                            Record place tokens
                                    ↓
                            _periodic_update() (every 100ms)
                                    ↓
                            Check if data length changed
                                    ↓
                            update_plot() → _get_rate_data() → data_collector.get_place_data()
                                    ↓
                            matplotlib canvas.draw()
```

**Line 340-366 in plot_panel.py** (_periodic_update):
```python
def _periodic_update(self) -> bool:
    """Periodic callback to update plot and UI list if needed."""
    if not self.selected_objects:
        return True
    
    data_changed = False
    for obj in self.selected_objects:
        if self.object_type == 'place':
            current_length = len(self.data_collector.get_place_data(obj.id))
        else:
            current_length = len(self.data_collector.get_transition_data(obj.id))
        
        last_length = self.last_data_length.get(obj.id, 0)
        if current_length != last_length:
            data_changed = True
            self.last_data_length[obj.id] = current_length
    
    if data_changed or self.needs_update:
        if self.needs_update:
            self._update_objects_list()
        self.update_plot()
        self.needs_update = False
    
    return True
```

**Data Retrieval** (transition_rate_panel.py line 82-95):
```python
def _get_rate_data(self, transition_id):
    """Get behavior-specific data for a transition."""
    raw_events = self.data_collector.get_transition_data(transition_id)
    
    # Determine transition type by checking if details contain 'rate' field
    has_rate_data = False
    if len(raw_events) > 0 and raw_events[0][2] is not None:
        details = raw_events[0][2]
        if isinstance(details, dict) and 'rate' in details:
            has_rate_data = True
```

**Verification**:
- ✅ Periodic update checks for data length changes (every 100ms)
- ✅ Calls `data_collector.get_place_data()` and `get_transition_data()` to fetch current data
- ✅ Not cached - fetches fresh data on every update
- ✅ Adaptive: Continuous transitions show rate curves, discrete show cumulative counts

**Conclusion**: Plot update mechanism is **correctly implemented** and fetches fresh data dynamically.

---

### 3. Search Mechanism for Dynamic Changes ✅ WORKING

**Location**: `src/shypn/analyses/search_handler.py`

**Status**: ✅ **Correctly Implemented**

#### Search Flow:

```python
def search_transitions(model, query):
    """Search for transitions matching the query string."""
    # ...
    matches = []
    for transition in model.transitions:  # ← Iterates CURRENT model state
        # Match against name (T1, T2, etc.)
        if query_lower in transition.name.lower():
            matches.append(transition)
            continue
        
        # Match against label (user-defined text)
        if transition.label and query_lower in transition.label.lower():
            matches.append(transition)
            continue
    
    return matches
```

**Key Behavior**:
- Searches `model.transitions` list directly (current state)
- Uses `transition.name` and `transition.label` (current attributes)
- NOT cached - reads fresh data on every search

**Result Formatting with Source/Sink Detection** (lines 99-120):
```python
for obj in results[:10]:
    if object_type == "transition":
        # Add source/sink indicator
        is_source = getattr(obj, 'is_source', False)  # ← Dynamic read
        is_sink = getattr(obj, 'is_sink', False)      # ← Dynamic read
        
        if is_source:
            names.append(f"{obj.name}(⊙)")  # Source symbol
        elif is_sink:
            names.append(f"{obj.name}(⊗)")  # Sink symbol
        else:
            names.append(obj.name)
```

**Verification**:
- ✅ Searches live model objects (not cached copies)
- ✅ Reads current `transition_type`, `is_source`, `is_sink` dynamically
- ✅ Would reflect type changes if transition is transformed during simulation

**Limitation**:
- ⚠️ User must **re-search** to see updated transition types
- Search results are displayed from a snapshot, not live-updated
- But this is acceptable UX (search on demand, not continuous monitoring)

**Conclusion**: Search mechanism **correctly reads current state** when invoked.

---

### 4. Reset Button and Matplotlib Canvas Blanking ❌ BROKEN

**Location**: `src/shypn/helpers/model_canvas_loader.py` line 853

**Status**: ❌ **CRITICAL BUG - Plot data not cleared visually**

#### Current Implementation (INCOMPLETE):

**File**: `model_canvas_loader.py` line 853-875
```python
def _on_simulation_reset(self, palette, drawing_area):
    """Handle simulation reset - blank analysis plots and prepare for new data.
    
    Args:
        palette: SwissKnifePalette that forwarded the signal
        drawing_area: GtkDrawingArea widget for the canvas
    """
    if self.right_panel_loader:
        if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
            panel = self.right_panel_loader.place_panel
            panel.last_data_length.clear()  # ✅ Clears tracking dict
            if panel.selected_objects:
                panel.needs_update = True    # ✅ Triggers redraw
            else:
                panel._show_empty_state()    # ✅ Shows empty message
        
        if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
            panel = self.right_panel_loader.transition_panel
            panel.last_data_length.clear()  # ✅ Clears tracking dict
            if panel.selected_objects:
                panel.needs_update = True    # ✅ Triggers redraw
            else:
                panel._show_empty_state()    # ✅ Shows empty message
```

#### What Actually Happens:

1. ✅ **Simulation Controller** (`controller.py` line 1489):
   ```python
   def reset(self):
       # ...
       if self.data_collector is not None:
           self.data_collector.clear()  # ✅ Data IS cleared
       # ...
       for place in self.model.places:
           place.tokens = place.initial_marking  # ✅ Initial markings restored
   ```

2. ✅ **Emit Signal** (`simulate_tools_palette_loader.py` line 671):
   ```python
   self.simulation.reset()
   self.emit('reset-executed')  # ✅ Signal emitted
   ```

3. ✅ **SwissKnife Palette** forwards signal to `model_canvas_loader`

4. ❌ **Matplotlib Panels** - The Issue:
   - `panel.last_data_length.clear()` - ✅ Cleared
   - `panel.needs_update = True` - ✅ Set
   - **BUT**: Next `_periodic_update()` runs and sees:
     ```python
     current_length = len(self.data_collector.get_place_data(obj.id))  # Returns 0 (cleared!)
     last_length = self.last_data_length.get(obj.id, 0)  # Also 0 (just cleared!)
     if current_length != last_length:  # FALSE! 0 == 0
         data_changed = True
     ```
   - **Result**: `data_changed = False`, so plot keeps showing OLD data from matplotlib cache!

#### Root Cause Analysis:

The problem is **matplotlib canvas caching**:
- After reset, `data_collector` is cleared (empty lists)
- But matplotlib canvas still shows the old plot from before reset
- `_periodic_update()` sees `0 == 0` (no change), so doesn't trigger redraw
- `needs_update = True` should force redraw, but it's checked AFTER data_changed check

**The Issue**: The logic relies on data length change detection, but after reset both old and new lengths are 0, so no update is triggered even though the canvas should be blanked.

#### The Fix Needed:

**Option 1**: Force immediate canvas blanking on reset (RECOMMENDED):
```python
def _on_simulation_reset(self, palette, drawing_area):
    """Handle simulation reset - blank analysis plots immediately."""
    if self.right_panel_loader:
        if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
            panel = self.right_panel_loader.place_panel
            panel.last_data_length.clear()
            # FORCE IMMEDIATE BLANK - Don't wait for periodic update
            panel._show_empty_state() if not panel.selected_objects else panel.update_plot()
        
        if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
            panel = self.right_panel_loader.transition_panel
            panel.last_data_length.clear()
            # FORCE IMMEDIATE BLANK - Don't wait for periodic update
            panel._show_empty_state() if not panel.selected_objects else panel.update_plot()
```

**Option 2**: Set sentinel value to force update detection:
```python
def _on_simulation_reset(self, palette, drawing_area):
    """Handle simulation reset - blank analysis plots."""
    if self.right_panel_loader:
        if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
            panel = self.right_panel_loader.place_panel
            # Set sentinel value to force update detection
            for obj in panel.selected_objects:
                panel.last_data_length[obj.id] = -1  # Force mismatch
            panel.needs_update = True
```

**Option 3**: Add explicit `on_reset()` method to panels:
```python
# In plot_panel.py:
def on_reset(self):
    """Called when simulation is reset - blank the plot."""
    self.last_data_length.clear()
    if self.selected_objects:
        # Force blank canvas with selected objects shown as "ready"
        self._show_waiting_state()  # or self.update_plot()
    else:
        self._show_empty_state()

# In model_canvas_loader.py:
def _on_simulation_reset(self, palette, drawing_area):
    if self.right_panel_loader:
        if self.right_panel_loader.place_panel:
            self.right_panel_loader.place_panel.on_reset()
        if self.right_panel_loader.transition_panel:
            self.right_panel_loader.transition_panel.on_reset()
```

---

### 5. Initial Marking Reset ✅ WORKING

**Location**: `src/shypn/engine/simulation/controller.py` line 1475

**Status**: ✅ **Correctly Implemented**

```python
def reset(self):
    """Reset the simulation to initial marking."""
    # ...
    for place in self.model.places:
        if hasattr(place, 'initial_marking'):
            place.tokens = place.initial_marking  # ✅ Restore initial tokens
        else:
            place.tokens = 0  # ✅ Default to 0 if no initial marking
    
    self._notify_step_listeners()  # ✅ Notify observers (including plot panels)
```

**Verification**:
- ✅ Resets `place.tokens` to `place.initial_marking`
- ✅ Notifies step listeners (data collector, plot panels)
- ✅ Clears data collector

**Conclusion**: Initial marking reset is **correctly implemented**.

---

## Summary of Findings

### ✅ Working Correctly:

1. **Transition Type Signaling**: 
   - Type displayed in plot legends and UI lists
   - Reads from `obj.transition_type` dynamically
   - Shows source/sink indicators

2. **Plot Update Mechanism**:
   - Periodic updates every 100ms
   - Fetches fresh data from `data_collector`
   - Adaptive visualization (rate curves vs. cumulative counts)

3. **Search Mechanism**:
   - Searches current model state (not cached)
   - Reads transition types dynamically
   - Shows source/sink indicators in results

4. **Initial Marking Reset**:
   - Restores `place.tokens = place.initial_marking`
   - Clears data collector
   - Notifies listeners

### ❌ Issues Found:

1. **CRITICAL - Reset Button Not Blanking Matplotlib Canvas**:
   - **Location**: `model_canvas_loader.py` line 853 `_on_simulation_reset()`
   - **Issue**: Canvas shows old plot data after reset
   - **Cause**: Update detection sees `0 == 0` (no change), skips redraw
   - **Impact**: User sees stale plot data, thinks simulation didn't reset
   - **Fix**: Force immediate `update_plot()` or `_show_empty_state()` call

### ⚠️ Minor Limitations:

1. **Search Results Not Live-Updated**:
   - User must re-search to see updated transition types
   - Acceptable UX (search is on-demand, not continuous monitoring)

---

## Recommended Fixes

### Priority 1: Fix Reset Canvas Blanking (CRITICAL)

**File**: `src/shypn/helpers/model_canvas_loader.py`  
**Line**: 853-875  
**Method**: `_on_simulation_reset()`

**Change**:
```python
def _on_simulation_reset(self, palette, drawing_area):
    """Handle simulation reset - blank analysis plots immediately.
    
    Args:
        palette: SwissKnifePalette that forwarded the signal
        drawing_area: GtkDrawingArea widget for the canvas
    """
    if self.right_panel_loader:
        # Place panel
        if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
            panel = self.right_panel_loader.place_panel
            panel.last_data_length.clear()
            
            # FORCE IMMEDIATE UPDATE - Don't wait for periodic check
            if panel.selected_objects:
                panel.update_plot()  # Will show empty plot with 0 data
            else:
                panel._show_empty_state()  # Show "no objects selected" message
        
        # Transition panel
        if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
            panel = self.right_panel_loader.transition_panel
            panel.last_data_length.clear()
            
            # FORCE IMMEDIATE UPDATE - Don't wait for periodic check
            if panel.selected_objects:
                panel.update_plot()  # Will show empty plot with 0 data
            else:
                panel._show_empty_state()  # Show "no objects selected" message
```

**Rationale**:
- Immediately calls `update_plot()` instead of setting `needs_update = True`
- Bypasses periodic update delay (100ms)
- Ensures matplotlib canvas is blanked synchronously with reset
- User sees immediate visual feedback that reset occurred

---

### Priority 2: Add Diagnostics Panel Reset (if applicable)

If diagnostics panel exists and shows data, ensure it's also reset:

```python
def _on_simulation_reset(self, palette, drawing_area):
    # ... existing code ...
    
    # Diagnostics panel (if exists)
    if hasattr(self.right_panel_loader, 'diagnostics_panel') and self.right_panel_loader.diagnostics_panel:
        diagnostics = self.right_panel_loader.diagnostics_panel
        if hasattr(diagnostics, 'on_reset'):
            diagnostics.on_reset()
```

---

## Testing Checklist

After applying fixes, verify:

### Test 1: Reset Blanks Canvas Immediately
1. Load Petri net
2. Add places/transitions to plot panels
3. Run simulation for 5+ seconds
4. **Click Reset button**
5. ✅ **Verify**: Matplotlib canvas blanks immediately (no stale data)
6. ✅ **Verify**: Selected objects still shown in UI list
7. ✅ **Verify**: Place tokens restored to initial markings

### Test 2: Reset → Run → Plot Updates
1. After reset, click Play
2. ✅ **Verify**: Plots start updating from time 0
3. ✅ **Verify**: No residual data from previous run

### Test 3: Multiple Reset Cycles
1. Run simulation
2. Reset
3. Run again
4. Reset again
5. ✅ **Verify**: Each reset properly blanks canvas
6. ✅ **Verify**: No accumulation of old data

### Test 4: Reset with No Objects Selected
1. Clear all selected objects
2. Reset simulation
3. ✅ **Verify**: Shows "No objects selected" message
4. ✅ **Verify**: No errors in console

---

## Code References

### Key Files:
- `src/shypn/analyses/plot_panel.py` - Base plotting panel (✅ working)
- `src/shypn/analyses/transition_rate_panel.py` - Transition plots (✅ working)
- `src/shypn/analyses/place_rate_panel.py` - Place plots (✅ working)
- `src/shypn/analyses/data_collector.py` - Data storage (✅ working)
- `src/shypn/analyses/search_handler.py` - Search functionality (✅ working)
- `src/shypn/helpers/model_canvas_loader.py` - Reset handler (❌ BROKEN)
- `src/shypn/helpers/simulate_tools_palette_loader.py` - Reset button (✅ working)
- `src/shypn/engine/simulation/controller.py` - Simulation reset (✅ working)

### Signal Flow:
```
Reset Button → simulate_tools_palette_loader._on_reset_clicked()
             ↓
    simulation.reset() [controller.py line 1475]
             ↓
    data_collector.clear() [line 1489]
             ↓
    places.tokens = initial_marking [line 1499]
             ↓
    emit('reset-executed') [simulate_tools line 671]
             ↓
    SwissKnifePalette forwards signal
             ↓
    model_canvas_loader._on_simulation_reset() [line 853]
             ↓
    ❌ BROKEN: Doesn't force canvas blank
```

---

## Conclusion

**Status**: 1 critical issue found and diagnosed

**Working Components**:
- ✅ Transition type detection and display
- ✅ Plot data updates (periodic refresh)
- ✅ Search mechanism (reads current state)
- ✅ Initial marking reset
- ✅ Data collector clearing

**Broken Components**:
- ❌ Matplotlib canvas blanking on reset (shows stale data)

**Root Cause**: 
The `_on_simulation_reset()` handler sets `needs_update = True` but relies on periodic update detection, which sees `0 == 0` after data collector is cleared and doesn't trigger redraw.

**Fix**: 
Force immediate `update_plot()` call in reset handler instead of waiting for periodic update.

**Impact**: 
LOW effort fix (5 lines of code), HIGH user experience improvement (immediate visual feedback on reset).

---

**Analysis Complete**: October 12, 2025  
**Analyst**: AI Code Reviewer  
**Priority**: CRITICAL - Fix recommended immediately
