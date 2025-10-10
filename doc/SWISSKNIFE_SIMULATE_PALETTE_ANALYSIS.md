# SwissKnife Simulation Palette Analysis and Fixes

**Document Status:** Phase 2 Analysis  
**Date:** 2025  
**Related:** SWISSKNIFE_PALETTE_ANALYSIS_AND_FIXES.md (Phase 1 - Edit Tools)

---

## Executive Summary

This document analyzes the simulation tools palette within the SwissKnife unified palette, identifies issues that need fixing, and proposes solutions. This follows the same methodology applied successfully to edit tools (Place, Transition, Arc) in Phase 1.

**Current Status:**
- ✅ **Architecture:** Structurally complete and functional
- ❌ **CRITICAL BUG:** Data collector not connected to right panel - **PLOTTING BROKEN**
- ✅ **Signal Flow:** Properly forwarded through SwissKnifePalette to model_canvas_loader
- ✅ **UI Loading:** UI file loads successfully (confirmed in app_debug.log)
- ⚠️ **Visual Feedback:** Missing active button highlighting, running state indicators
- ⚠️ **Category Button:** Simulate category button needs active state styling
- ⚠️ **Error Feedback:** Need better user notifications for simulation failures
- ⚠️ **State Visibility:** Simulation state not immediately clear to user

**CRITICAL FINDING:** The code attempts to retrieve `data_collector` from `overlay_manager.get_palette('simulate_tools')`, but when using **SwissKnifePalette**, the `SimulateToolsPaletteLoader` is embedded INSIDE `SwissKnifePalette.widget_palette_instances['simulate']`, NOT stored in overlay_manager. This breaks matplotlib plotting entirely.

**Key Finding:** Unlike edit tools (which had critical functional issues), simulation tools are **architecturally sound** but have ONE CRITICAL BUG (data collector disconnected) plus visual feedback gaps.

---

## 1. Architecture Overview

### 1.1 Component Structure

The simulation palette uses a **widget palette pattern** (different from edit tools' simple button pattern):

```
SwissKnifePalette (main unified palette)
  └── Simulate Category Button [S]
       └── SimulateToolsPaletteLoader (widget palette, embedded)
            ├── UI: simulate_tools_palette.ui (GtkGrid layout)
            │   ├── Row 0: Control Buttons [R][P][S][T][⚙]
            │   ├── Row 1: Duration Controls (entry + combo)
            │   ├── Row 2: Progress Bar
            │   └── Row 3: Time Display Label
            │
            ├── SimulationController (owns simulation engine)
            │   ├── SimulationSettings (duration, time_step, units, policies)
            │   ├── Step listeners (data collector, palette updates)
            │   └── State management (running, time, progress)
            │
            └── Signals (forwarded through SwissKnifePalette)
                ├── 'step-executed' (float time)
                ├── 'reset-executed' ()
                └── 'settings-changed' ()
```

**File Locations:**
- Loader: `src/shypn/helpers/simulate_tools_palette_loader.py` (627 lines)
- UI Definition: `ui/simulate/simulate_tools_palette.ui` (240 lines, GtkGrid)
- Integration: `src/shypn/helpers/swissknife_palette.py` (lines 155-222)
- Signal Handlers: `src/shypn/helpers/model_canvas_loader.py` (lines 652-710)

### 1.2 Widget Palette Integration

**How SwissKnife Embeds Simulation Palette:**

```python
# In SwissKnifePalette._create_sub_palette (line 155)
if is_widget_palette and cat_id == 'simulate':
    # Create SimulateToolsPaletteLoader
    widget_palette_instance = SimulateToolsPaletteLoader(model=self.model)
    self.widget_palette_instances[cat_id] = widget_palette_instance
    
    # Forward simulation signals
    widget_palette_instance.connect('step-executed', self._on_simulation_step)
    widget_palette_instance.connect('reset-executed', self._on_simulation_reset)
    widget_palette_instance.connect('settings-changed', self._on_simulation_settings_changed)
    
    # Extract container from loader's revealer
    loader_revealer = widget_palette_instance.get_widget()
    container = widget_palette_instance.simulate_tools_container
    
    # Remove from loader's revealer, add to SwissKnife's revealer
    loader_revealer.remove(container)
    revealer.add(container)  # SwissKnife controls animation
```

**Key Architectural Difference vs. Edit Tools:**
- **Edit tools:** Simple button grid, tools emit 'activated' signal
- **Simulation tools:** Complex embedded widget, palette owns SimulationController, buttons call controller methods directly

### 1.3 Signal Flow Architecture

**Complete Signal Chain:**

```
User clicks [R] button
  ↓
SimulateToolsPaletteLoader._on_run_clicked()
  ↓
SimulationController.run()
  ↓
(on each step) SimulationController → step_listeners
  ↓
SimulateToolsPaletteLoader._on_simulation_step()
  ↓
SimulateToolsPaletteLoader.emit('step-executed', time)
  ↓
SwissKnifePalette._on_simulation_step() [forward signal]
  ↓
SwissKnifePalette.emit('simulation-step-executed', time)
  ↓
ModelCanvasLoader._on_simulation_step()
  ↓
drawing_area.queue_draw()  # Redraw canvas with new token state
```

**Signal Handlers in model_canvas_loader.py:**

```python
# Lines 433-435: Connect SwissKnifePalette signals
swissknife_palette.connect('simulation-step-executed', 
                          self._on_simulation_step, drawing_area)
swissknife_palette.connect('simulation-reset-executed', 
                          self._on_simulation_reset, drawing_area)
swissknife_palette.connect('simulation-settings-changed', 
                          self._on_simulation_settings_changed, drawing_area)

# Lines 669-710: Signal handler implementations
def _on_simulation_step(self, palette, time, drawing_area):
    """Redraw canvas to show updated token state."""
    drawing_area.queue_draw()

def _on_simulation_reset(self, palette):
    """Clear analysis plots and prepare for new data."""
    # Reset matplotlib panels
    if self.right_panel_loader and self.right_panel_loader.place_panel:
        panel.last_data_length.clear()
        panel.needs_update = True

def _on_simulation_settings_changed(self, palette, drawing_area):
    """Handle settings change - redraw canvas."""
    drawing_area.queue_draw()
```

**Assessment:** ✅ **Signal flow is complete and properly forwarded.** No issues found.

---

## 2. Current Implementation Assessment

### 2.1 Functional Completeness ✅

**What Works Correctly:**

1. ✅ **Button Logic:** All buttons (Run, Step, Stop, Reset, Settings) function correctly
2. ✅ **State Machine:** Button sensitivity updates properly based on simulation state
3. ✅ **Duration Controls:** Entry and combo box update settings correctly
4. ✅ **Progress Bar:** Updates with simulation progress (fraction + percentage text)
5. ✅ **Time Display:** Shows current time vs. duration with proper formatting
6. ✅ **Settings Dialog:** Opens and applies settings (duration, time step, policies)
7. ✅ **Signal Emission:** All signals ('step-executed', 'reset-executed', 'settings-changed') emit correctly
8. ✅ **Canvas Redraw:** Drawing area redraws on step to show token changes
9. ✅ **Data Collection:** SimulationDataCollector receives steps for matplotlib plotting
10. ✅ **Error Handling:** Try-catch blocks present for settings dialog, duration parsing

**State Machine (from _update_button_states):**

```python
# IDLE (after reset):     Run✓, Step✓, Stop✗, Reset✗, Settings✓
# RUNNING:                Run✗, Step✗, Stop✓, Reset✗, Settings✗
# PAUSED:                 Run✓, Step✓, Stop✗, Reset✓, Settings✓
# COMPLETED:              Run✗, Step✗, Stop✗, Reset✓, Settings✓
```

**Assessment:** The simulation palette is **architecturally sound and functionally complete**. All core simulation features work as designed. No critical bugs found.

### 2.2 CSS Styling ✅

**Current Styling (in simulate_tools_palette_loader.py, lines 146-269):**

```python
css = '''
    .simulate-tools-palette {
        background: linear-gradient(to bottom, #34495e, #2c3e50);
        border: 2px solid #1a252f;
        border-radius: 8px;
        padding: 6px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    }
    
    .sim-tool-button {
        background: linear-gradient(to bottom, #5d6d7e, #566573);
        border: 2px solid #34495e;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
        color: white;
        min-width: 40px;
        min-height: 40px;
    }
    
    /* Button-specific themes */
    .run-button    { background: linear-gradient(to bottom, #27ae60, #229954); }  /* Green */
    .step-button   { background: linear-gradient(to bottom, #16a085, #138d75); }  /* Cyan */
    .stop-button   { background: linear-gradient(to bottom, #e74c3c, #c0392b); }  /* Red */
    .reset-button  { background: linear-gradient(to bottom, #f39c12, #e67e22); }  /* Orange */
    .settings-button { background: linear-gradient(to bottom, #5d6db9, #4a5899); }  /* Blue */
    
    /* :hover, :active, :disabled states all defined */
'''
```

**Assessment:** ✅ **Comprehensive CSS with button-specific color themes, hover states, active states, and disabled states.** Professional quality styling is already present.

### 2.3 Visual Feedback Gaps ⚠️

**Issues Found:**

**Issue #1: No Active Button Highlighting When Running/Paused**
- **Symptom:** When simulation is running, all buttons look the same (except sensitivity). User can't immediately see which state simulation is in without trying to click buttons.
- **Expected:** Running state should highlight Stop button, Paused state should highlight Run/Step buttons, Completed state should highlight Reset button.
- **Comparison:** Edit tools Phase 1 added blue glow to active tool button. Simulation needs similar state indicators.

**Issue #2: Category Button [S] Not Highlighted When Active**
- **Symptom:** When Simulate sub-palette is open, the [S] category button doesn't show active state.
- **Expected:** Active category button should have `.active` CSS class (blue glow, like edit tools).
- **Root Cause:** SwissKnifePalette properly calls `_activate_category_button()` which adds `.active` class, but CSS for `.active` category button may not be defined or not visible enough.
- **Location:** `swissknife_palette.py` lines 367-375 (`_activate_category_button`, `_deactivate_category_button`)

**Issue #3: No Visual Feedback for Long-Running Operations**
- **Symptom:** When running long simulations, progress bar updates but no indication that simulation is actively running (no spinner, no pulsing, no status text).
- **Expected:** Progress bar could pulse or change color when running, text like "Running..." could appear.

**Issue #4: Error Feedback Not User-Friendly**
- **Symptom:** Errors are printed to console (`print(f"❌ Error opening settings dialog: {e}")`), not shown as dialogs to user.
- **Expected:** Use `Gtk.MessageDialog` like we added for arc creation errors in Phase 1.
- **Location:** `simulate_tools_palette_loader.py` line 451 (settings dialog error handling)

**Issue #5: Duration Entry Invalid Input Handling**
- **Symptom:** Invalid duration input (negative, non-numeric, zero) is silently ignored in `_on_duration_changed` (lines 463-504).
- **Expected:** Show validation error message to user (e.g., "Duration must be a positive number").

**Issue #6: No Confirmation for Simulation Reset**
- **Symptom:** Clicking Reset [T] immediately resets simulation without confirmation, potentially losing data.
- **Expected:** If simulation has progressed significantly, show confirmation dialog: "Reset simulation and lose current data?"

---

## 3. Proposed Fixes

### Fix #0: Connect Data Collector to Right Panel (CRITICAL - PLOTTING BROKEN)

**Goal:** Fix broken matplotlib plotting by connecting SimulateToolsPaletteLoader's data_collector to right_panel_loader.

**Problem Analysis:**

The code in `model_canvas_loader.py` (lines 163-172) attempts to get `data_collector` like this:

```python
# BROKEN CODE - doesn't work with SwissKnifePalette
overlay_manager = self.overlay_managers[drawing_area]
simulate_tools_palette = overlay_manager.get_palette('simulate_tools')  # Returns None!
if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
    data_collector = simulate_tools_palette.data_collector
    self.right_panel_loader.set_data_collector(data_collector)
```

**Why It's Broken:**

When using `CanvasOverlayManager` (OLD system), it stores palettes like:
```python
self.simulate_tools_palette = create_simulate_tools_palette(...)
# Can retrieve with: overlay_manager.get_palette('simulate_tools')
```

But with `SwissKnifePalette` (NEW system), the SimulateToolsPaletteLoader is embedded INSIDE:
```python
# In SwissKnifePalette._create_sub_palette (line 160)
widget_palette_instance = SimulateToolsPaletteLoader(model=self.model)
self.widget_palette_instances[cat_id] = widget_palette_instance  # Stored HERE

# overlay_manager only stores swissknife_palette reference (line 440)
self.overlay_managers[drawing_area].swissknife_palette = swissknife_palette
```

So `overlay_manager.get_palette('simulate_tools')` returns **None** because it's looking in the wrong place!

**Solution:**

**File:** `src/shypn/helpers/model_canvas_loader.py`

**Step 1:** Fix data_collector retrieval in `load_model_canvas` (lines 163-172):

```python
# OLD CODE (lines 163-172):
if self.right_panel_loader and drawing_area:
    # Get simulate_tools_palette from overlay manager
    if drawing_area in self.overlay_managers:
        overlay_manager = self.overlay_managers[drawing_area]
        simulate_tools_palette = overlay_manager.get_palette('simulate_tools')
        if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
            data_collector = simulate_tools_palette.data_collector
            self.right_panel_loader.set_data_collector(data_collector)

# NEW CODE (corrected):
if self.right_panel_loader and drawing_area:
    # Get simulate_tools_palette from SwissKnife widget_palette_instances
    if drawing_area in self.overlay_managers:
        overlay_manager = self.overlay_managers[drawing_area]
        
        # SwissKnifePalette stores SimulateToolsPaletteLoader in widget_palette_instances
        if hasattr(overlay_manager, 'swissknife_palette'):
            swissknife = overlay_manager.swissknife_palette
            if hasattr(swissknife, 'widget_palette_instances'):
                simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
                if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                    data_collector = simulate_tools_palette.data_collector
                    self.right_panel_loader.set_data_collector(data_collector)
                    print(f"[DataCollector] Connected to right panel: {data_collector}")
```

**Step 2:** Fix data_collector retrieval in `_handle_object_double_click` (lines 1930-1936):

```python
# OLD CODE (lines 1930-1936):
data_collector = None
if drawing_area in self.overlay_managers:
    overlay = self.overlay_managers[drawing_area]
    simulate_tools = overlay.get_palette('simulate_tools')
    if simulate_tools and hasattr(simulate_tools, 'data_collector'):
        data_collector = simulate_tools.data_collector

# NEW CODE (corrected):
data_collector = None
if drawing_area in self.overlay_managers:
    overlay = self.overlay_managers[drawing_area]
    
    # Get from SwissKnifePalette widget_palette_instances
    if hasattr(overlay, 'swissknife_palette'):
        swissknife = overlay.swissknife_palette
        if hasattr(swissknife, 'widget_palette_instances'):
            simulate_tools = swissknife.widget_palette_instances.get('simulate')
            if simulate_tools and hasattr(simulate_tools, 'data_collector'):
                data_collector = simulate_tools.data_collector
```

**Expected Result:** 
- Data collector properly connected to right panel
- Matplotlib plots receive simulation data
- Place/Transition panels show token evolution graphs
- Console shows: `[DataCollector] Connected to right panel: <SimulationDataCollector object>`

**Testing:**
1. Load a Petri net
2. Click Simulate [S] button
3. Click Step [P] or Run [R]
4. Click on a Place → Verify right panel shows token evolution plot
5. Click on a Transition → Verify right panel shows firing count plot

---

### Fix #1: Add Active Button State Highlighting

**Goal:** Highlight button corresponding to current simulation state (Running → Stop button, Paused → Run button, etc.)

**Implementation:**

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Step 1:** Add CSS for `.button-state-active` class (lines 146-269, in CSS string):

```python
# Add after .sim-tool-button styles
.sim-tool-button.button-state-active {
    box-shadow: 0 0 12px rgba(52, 152, 219, 0.8),
                0 0 6px rgba(52, 152, 219, 0.6),
                0 2px 4px rgba(0, 0, 0, 0.3);
    border-color: rgba(52, 152, 219, 0.9);
    background: linear-gradient(to bottom, 
                rgba(52, 152, 219, 0.3),
                rgba(41, 128, 185, 0.3)),
                linear-gradient(to bottom, #5d6d7e, #566573);
    background-blend-mode: screen, normal;
}

/* Button-specific active glow colors */
.run-button.button-state-active {
    box-shadow: 0 0 12px rgba(46, 204, 113, 0.8),
                0 0 6px rgba(46, 204, 113, 0.6);
    border-color: rgba(46, 204, 113, 0.9);
}

.stop-button.button-state-active {
    box-shadow: 0 0 12px rgba(231, 76, 60, 0.8),
                0 0 6px rgba(231, 76, 60, 0.6);
    border-color: rgba(231, 76, 60, 0.9);
}

.reset-button.button-state-active {
    box-shadow: 0 0 12px rgba(243, 156, 18, 0.8),
                0 0 6px rgba(243, 156, 18, 0.6);
    border-color: rgba(243, 156, 18, 0.9);
}
```

**Step 2:** Add method to update button highlighting (after `_update_button_states`):

```python
def _update_button_highlighting(self, running=False, completed=False):
    """Update visual highlighting of buttons based on simulation state.
    
    This provides visual feedback beyond just button sensitivity.
    
    Args:
        running: True if simulation is actively running
        completed: True if simulation reached duration limit
    """
    # Clear all highlighting first
    for button in [self.run_button, self.step_button, self.stop_button, 
                   self.reset_button]:
        if button:
            button.get_style_context().remove_class('button-state-active')
    
    # Highlight based on state
    if running:
        # Highlight Stop button (can stop running simulation)
        if self.stop_button:
            self.stop_button.get_style_context().add_class('button-state-active')
    elif completed:
        # Highlight Reset button (needs reset to continue)
        if self.reset_button:
            self.reset_button.get_style_context().add_class('button-state-active')
    # For paused state, no specific button highlighting (all options available)
```

**Step 3:** Call `_update_button_highlighting()` in all state update methods:

```python
# In _on_run_clicked (after self.simulation.run()):
self._update_button_states(running=True)
self._update_button_highlighting(running=True)  # ADD THIS

# In _on_step_clicked (after step or completion):
self._update_button_states(running=False, completed=is_complete)
self._update_button_highlighting(running=False, completed=is_complete)  # ADD THIS

# In _on_stop_clicked (after self.simulation.stop()):
self._update_button_states(running=False)
self._update_button_highlighting(running=False)  # ADD THIS

# In _on_reset_clicked (after self.simulation.reset()):
self._update_button_states(running=False, reset=True)
self._update_button_highlighting(running=False, completed=False)  # ADD THIS
```

**Expected Result:** Buttons glow with colored shadow when they represent the current state, providing immediate visual feedback about simulation status.

---

### Fix #2: Category Button Active State Styling

**Goal:** Make [S] category button visually stand out when Simulate sub-palette is open (matching edit tools behavior).

**Implementation:**

**File:** `src/shypn/helpers/swissknife_palette.py`

**Issue:** The `.active` class is added correctly (lines 367-375), but CSS may not be strong enough or missing.

**Check existing CSS (lines 428-577):**

```python
# In _apply_css method, check if .category-button.active exists
# If missing or weak, enhance it:

.category-button.active {
    background: linear-gradient(to bottom, 
                rgba(52, 152, 219, 0.4),
                rgba(41, 128, 185, 0.4)),
                linear-gradient(to bottom, #5d6d7e, #566573);
    background-blend-mode: screen, normal;
    border-color: rgba(52, 152, 219, 0.9);
    box-shadow: 0 0 12px rgba(52, 152, 219, 0.8),
                0 0 6px rgba(52, 152, 219, 0.6),
                inset 0 2px 4px rgba(52, 152, 219, 0.3),
                0 2px 4px rgba(0, 0, 0, 0.3);
    color: rgba(255, 255, 255, 1.0);
}

.category-button.active:hover {
    background: linear-gradient(to bottom, 
                rgba(52, 152, 219, 0.5),
                rgba(41, 128, 185, 0.5)),
                linear-gradient(to bottom, #6c7a89, #5d6d7e);
    background-blend-mode: screen, normal;
}
```

**Expected Result:** When user clicks [S] button, it glows with blue shadow, making it clear that Simulate sub-palette is active.

---

### Fix #3: Running State Visual Indicator

**Goal:** Add visual indicator when simulation is actively running (progress bar pulsing or color change).

**Implementation:**

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Step 1:** Add CSS for running progress bar (lines 260-266):

```python
.sim-progress-bar.running progress {
    background: linear-gradient(90deg, 
                #27ae60 0%, 
                #2ecc71 50%, 
                #27ae60 100%);
    animation: progress-pulse 2s ease-in-out infinite;
}

@keyframes progress-pulse {
    0%, 100% { opacity: 1.0; }
    50% { opacity: 0.7; }
}
```

**Step 2:** Add progress bar state management (after `_update_button_highlighting`):

```python
def _update_progress_bar_state(self, running=False):
    """Update progress bar visual state.
    
    Args:
        running: True if simulation is actively running
    """
    if not self.progress_bar:
        return
    
    style_context = self.progress_bar.get_style_context()
    
    if running:
        style_context.add_class('running')
        self.progress_bar.set_text("Running...")
    else:
        style_context.remove_class('running')
        # Text updated by _update_progress_display()
```

**Step 3:** Call in state update methods:

```python
# In _on_run_clicked:
self._update_progress_bar_state(running=True)

# In _on_stop_clicked, _on_step_clicked, _on_reset_clicked:
self._update_progress_bar_state(running=False)
```

**Expected Result:** Progress bar pulses with animation when simulation is running, making it obvious that work is happening.

---

### Fix #4: User-Friendly Error Dialogs

**Goal:** Replace console print statements with proper GTK message dialogs.

**Implementation:**

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Step 1:** Add helper method for error dialogs (after `_update_progress_bar_state`):

```python
def _show_error_dialog(self, title, message):
    """Show error dialog to user.
    
    Args:
        title: Dialog title
        message: Error message
    """
    parent = self.simulate_tools_revealer.get_toplevel()
    if not isinstance(parent, Gtk.Window):
        parent = None
    
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()
```

**Step 2:** Replace print statements with dialog calls:

```python
# In _on_settings_clicked (line 451):
# BEFORE:
print(f"❌ Error opening settings dialog: {e}")

# AFTER:
self._show_error_dialog(
    "Settings Error",
    f"Failed to open simulation settings dialog:\n\n{str(e)}"
)

# In _on_duration_changed (add validation error dialog):
# After line 481 (if duration <= 0):
if duration <= 0:
    self._show_error_dialog(
        "Invalid Duration",
        "Duration must be a positive number greater than zero."
    )
    return
```

**Step 3:** Add validation error dialog for non-numeric input:

```python
# In _on_duration_changed, in except block (line 500):
except ValueError:
    self._show_error_dialog(
        "Invalid Input",
        f"Duration must be a valid number.\n\nYou entered: '{duration_text}'"
    )
except AttributeError as e:
    self._show_error_dialog(
        "Configuration Error",
        f"Simulation settings are not properly configured:\n\n{str(e)}"
    )
```

**Expected Result:** Users see clear, professional error messages in dialogs instead of errors being silently printed to console.

---

### Fix #5: Simulation Reset Confirmation

**Goal:** Prompt user for confirmation before resetting if simulation has progressed significantly.

**Implementation:**

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Add method before `_on_reset_clicked`:**

```python
def _confirm_reset(self):
    """Ask user to confirm simulation reset if significant progress exists.
    
    Returns:
        bool: True if user confirmed or no progress to lose, False if cancelled
    """
    # If simulation hasn't started or just started, no confirmation needed
    if self.simulation is None:
        return True
    
    progress = self.simulation.get_progress()
    if progress < 0.1:  # Less than 10% progress
        return True
    
    # Show confirmation dialog
    parent = self.simulate_tools_revealer.get_toplevel()
    if not isinstance(parent, Gtk.Window):
        parent = None
    
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text="Reset Simulation?"
    )
    
    progress_pct = int(progress * 100)
    dialog.format_secondary_text(
        f"Simulation has progressed {progress_pct}% "
        f"({TimeFormatter.format(self.simulation.time, self.simulation.settings.time_units)}).\n\n"
        "Resetting will lose all current simulation data.\n\n"
        "Are you sure you want to reset?"
    )
    
    response = dialog.run()
    dialog.destroy()
    
    return response == Gtk.ResponseType.YES
```

**Modify `_on_reset_clicked`:**

```python
def _on_reset_clicked(self, button):
    """Handle Reset button click - reset to initial marking."""
    if self.simulation is None:
        return
    
    # Ask for confirmation if significant progress exists
    if not self._confirm_reset():
        return  # User cancelled
    
    self.simulation.reset()
    self.emit('reset-executed')
    self._update_progress_display()
    self._update_button_states(running=False, reset=True)
    self._update_button_highlighting(running=False, completed=False)
    self._update_progress_bar_state(running=False)
```

**Expected Result:** User is prompted for confirmation before losing simulation progress, preventing accidental resets.

---

### Fix #6: Settings Button Visual Feedback

**Goal:** Show visual feedback when Settings dialog is open (disable button, show active state).

**Implementation:**

**File:** `src/shypn/helpers/simulate_tools_palette_loader.py`

**Modify `_on_settings_clicked`:**

```python
def _on_settings_clicked(self, button):
    """Handle Settings dialog click - open simulation settings dialog."""
    if self.simulation is None:
        return
    
    # Disable button while dialog is open
    self.settings_button.set_sensitive(False)
    
    # Pause simulation if running
    was_running = self.simulation.is_running()
    if was_running:
        self.simulation.stop()
    
    try:
        from shypn.dialogs.simulation_settings_dialog import show_simulation_settings_dialog
        
        parent = self.simulate_tools_revealer.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
        
        # Show dialog and apply settings
        if show_simulation_settings_dialog(self.simulation.settings, parent):
            # Settings updated successfully
            self._update_duration_display()
            self._update_progress_display()
            self.emit('settings-changed')
            
            if was_running:
                print("⚠️  Simulation was paused to change settings. Click Run to resume.")
    except Exception as e:
        self._show_error_dialog(  # Use new error dialog method
            "Settings Error",
            f"Failed to open simulation settings dialog:\n\n{str(e)}"
        )
    finally:
        # Re-enable button and update states
        self.settings_button.set_sensitive(True)
        self._update_button_states(running=was_running)
        self._update_button_highlighting(running=was_running)
```

**Expected Result:** Settings button is disabled while dialog is open, preventing double-clicks and showing clear state.

---

## 4. Testing Strategy

### 4.1 Visual Feedback Tests

**Test Case 1: Button State Highlighting**
1. Open Simulate palette
2. Click Run [R] → Verify Stop button glows red
3. Click Stop [S] → Verify Stop button stops glowing
4. Run until completion → Verify Reset button glows orange
5. Click Reset [T] → Verify no buttons glow

**Test Case 2: Category Button Active State**
1. Click [S] category button → Verify button glows blue
2. Click [E] category button → Verify [S] stops glowing
3. Click [S] again → Verify [S] glows blue again

**Test Case 3: Running State Visual Indicator**
1. Set duration to 10 seconds
2. Click Run → Verify progress bar says "Running..." and pulses
3. Click Stop → Verify progress bar stops pulsing, shows percentage
4. Click Step → Verify progress bar shows percentage (no pulse)

### 4.2 Error Handling Tests

**Test Case 4: Duration Validation**
1. Enter "-10" in duration → Verify error dialog appears
2. Enter "abc" in duration → Verify error dialog appears
3. Enter "0" in duration → Verify error dialog appears
4. Enter "60" → Verify no error, duration updates

**Test Case 5: Settings Dialog Error**
1. (Manually corrupt settings to trigger error)
2. Click Settings [⚙] → Verify error dialog appears with clear message

**Test Case 6: Reset Confirmation**
1. Run simulation to 50% progress
2. Click Reset [T] → Verify confirmation dialog appears
3. Click "No" → Verify simulation not reset
4. Click Reset [T] again, click "Yes" → Verify simulation resets
5. Click Reset [T] at 0% progress → Verify no confirmation (immediate reset)

### 4.3 Integration Tests

**Test Case 7: Signal Flow**
1. Click Step → Verify canvas redraws (tokens updated)
2. Click Reset → Verify matplotlib plots clear
3. Change duration → Verify settings-changed signal emitted

**Test Case 8: Button State Machine**
1. Verify IDLE state: Run✓, Step✓, Stop✗, Reset✗, Settings✓
2. Click Run → Verify RUNNING state: Run✗, Step✗, Stop✓, Reset✗, Settings✗
3. Click Stop → Verify PAUSED state: Run✓, Step✓, Stop✗, Reset✓, Settings✓
4. Run to completion → Verify COMPLETED state: Run✗, Step✗, Stop✗, Reset✓, Settings✓

### 4.4 Regression Tests

**Test Case 9: Existing Functionality**
1. Verify all buttons still function correctly after fixes
2. Verify progress bar updates correctly
3. Verify time display shows correct format
4. Verify duration controls update settings
5. Verify signals emit correctly

---

## 5. Implementation Summary

### 5.1 Files to Modify

**CRITICAL FIX (Priority 0):**
- `src/shypn/helpers/model_canvas_loader.py`
  - Fix data_collector retrieval in `load_model_canvas()` (lines 163-172)
  - Fix data_collector retrieval in `_handle_object_double_click()` (lines 1930-1936)
  - Change: `overlay_manager.get_palette('simulate_tools')` → `overlay_manager.swissknife_palette.widget_palette_instances.get('simulate')`
  - **Impact:** FIXES BROKEN PLOTTING (matplotlib shows no data)

**Primary File (Visual Feedback):**
- `src/shypn/helpers/simulate_tools_palette_loader.py`
  - Add CSS for `.button-state-active`, `.running` progress bar
  - Add `_update_button_highlighting()` method
  - Add `_update_progress_bar_state()` method
  - Add `_show_error_dialog()` method
  - Add `_confirm_reset()` method
  - Modify `_on_run_clicked()`, `_on_step_clicked()`, `_on_stop_clicked()`, `_on_reset_clicked()`
  - Modify `_on_settings_clicked()` to disable button and use error dialog
  - Modify `_on_duration_changed()` to show validation errors

**Secondary File:**
- `src/shypn/helpers/swissknife_palette.py`
  - Enhance `.category-button.active` CSS (if needed)

### 5.2 Lines of Code Estimate

- **CRITICAL FIX:** ~30 lines (data_collector path corrections)
- CSS additions: ~60 lines
- New methods: ~80 lines (`_update_button_highlighting`, `_update_progress_bar_state`, `_show_error_dialog`, `_confirm_reset`)
- Method modifications: ~30 lines (button click handlers, validation)
- **Total:** ~200 lines

### 5.3 Risk Assessment

**Low Risk Changes:**
- CSS additions (no functional impact)
- Visual feedback methods (additive, no changes to logic)
- Error dialogs (replace prints, improve UX)

**Medium Risk Changes:**
- Reset confirmation (adds conditional logic to reset flow)
- Settings button disable/enable (need to ensure always re-enabled)

**Mitigation:**
- Comprehensive testing of all button states
- Verify signal flow not disrupted
- Test error paths (invalid inputs, exceptions)

---

## 6. Comparison with Phase 1 (Edit Tools)

### 6.1 Similarities

Both phases address **visual feedback and UX polish**:

| Aspect | Phase 1 (Edit Tools) | Phase 2 (Simulation) |
|--------|---------------------|----------------------|
| **Active State Highlighting** | Blue glow on active tool button | Button-specific glow (red/green/orange) on state button |
| **Cursor Feedback** | Tool-specific cursors (crosshair, cell, hand) | N/A (not applicable to simulation) |
| **Visual Validation** | Green/red arc target highlighting | Progress bar pulsing, button glows |
| **Error Dialogs** | Arc creation errors → GTK dialog | Settings/duration errors → GTK dialog |
| **State Visibility** | Active tool clear from button glow | Active simulation state clear from button glow |

### 6.2 Differences

| Aspect | Phase 1 (Edit Tools) | Phase 2 (Simulation) |
|--------|---------------------|----------------------|
| **Architecture** | Simple button grid, tool activation signals | Complex widget palette, embedded controller |
| **Signal Flow** | Tool → SwissKnife → model_canvas_loader | Palette → Controller → Palette → SwissKnife → model_canvas_loader |
| **Functional Issues** | Critical bugs (arc preview, state init, highlighting) | No critical bugs, only UX improvements |
| **Complexity** | Low (buttons + canvas interaction) | High (state machine, progress tracking, dialogs) |
| **CSS Location** | SwissKnifePalette (shared styles) | SimulateToolsPaletteLoader (widget-specific styles) |

### 6.3 Key Insight

**Phase 1** fixed **critical functional problems** that made edit tools hard to use.

**Phase 2** adds **professional polish** to simulation tools that already work correctly. This is about **consistency** and **user experience excellence**, not bug fixes.

---

## 7. Success Criteria

### 7.1 Visual Feedback

- ✅ Button highlighting clearly shows simulation state (Running/Paused/Completed)
- ✅ Category button [S] glows blue when Simulate palette is open
- ✅ Progress bar pulses when simulation is running
- ✅ All visual states are consistent with Phase 1 quality standards

### 7.2 User Experience

- ✅ Error messages appear as clear GTK dialogs (not console prints)
- ✅ Invalid duration input shows helpful validation message
- ✅ Reset confirmation prevents accidental data loss
- ✅ Settings button shows disabled state when dialog is open

### 7.3 Code Quality

- ✅ No regression in existing functionality
- ✅ All signals emit correctly
- ✅ Button state machine works reliably
- ✅ Code is well-commented and maintainable

### 7.4 Testing

- ✅ All test cases pass (visual feedback, error handling, integration, regression)
- ✅ Comprehensive testing document created
- ✅ No critical bugs introduced

---

## 8. Next Steps

1. **Review this analysis** with user to confirm fixes are desired
2. **Implement fixes** in order of priority:
   - High Priority: Fix #1 (button highlighting), Fix #2 (category active state), Fix #4 (error dialogs)
   - Medium Priority: Fix #3 (running indicator), Fix #5 (reset confirmation)
   - Low Priority: Fix #6 (settings button feedback)
3. **Test each fix** using test cases in Section 4
4. **Create implementation summary** document (like SWISSKNIFE_PHASE1_IMPLEMENTATION_COMPLETE.md)
5. **Commit and push** all changes with detailed commit message

---

## 9. Conclusion

The simulation palette has **ONE CRITICAL BUG** (data collector not connected - plotting broken) plus **visual feedback gaps**. 

**CRITICAL BUG:** The code attempts to retrieve `data_collector` using the OLD palette system path (`overlay_manager.get_palette('simulate_tools')`), but SwissKnifePalette stores it differently (`swissknife_palette.widget_palette_instances['simulate']`). This breaks matplotlib plotting entirely - **no plots show data**.

**Fix Priority:**
1. **CRITICAL (Fix #0):** Connect data_collector to right_panel (30 lines, 15 min)
2. **High (Fixes #1-4):** Visual feedback and error handling (150 lines, 2 hours)
3. **Medium (Fixes #5-6):** Reset confirmation and settings feedback (20 lines, 30 min)

The proposed fixes will:
- **RESTORE PLOTTING** (matplotlib will show simulation data again)
- Bring simulation tools up to the same **visual feedback quality** established in Phase 1 for edit tools
- Create a **unified, professional user experience** across the entire SwissKnife palette

**Estimated Effort:** 3-4 hours (vs. Phase 1's 4-5 hours)  
**Risk Level:** Low (additive changes, no core logic modifications except critical data_collector fix)  
**Impact:** Critical (fixes broken feature) + High (significant improvement in user experience and visual consistency)

---

**Document Version:** 1.1 (CORRECTED)  
**Last Updated:** 2025-10-09  
**Author:** GitHub Copilot (AI Assistant)  
**Related Documents:**
- SWISSKNIFE_PALETTE_ANALYSIS_AND_FIXES.md (Phase 1)
- SWISSKNIFE_PHASE1_IMPLEMENTATION_COMPLETE.md (Phase 1 summary)

**REVISION HISTORY:**
- v1.0 (2025-10-09): Initial analysis - incorrectly assumed only visual feedback issues
- v1.1 (2025-10-09): **CORRECTED** - Added Fix #0 for CRITICAL data_collector bug breaking plotting
