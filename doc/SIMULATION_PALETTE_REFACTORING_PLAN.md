# Simulation Palette Refactoring Plan

**Date**: 2025-10-08  
**Goal**: Add Settings button to simulation palette and implement essential timing features  
**Branch**: feature/property-dialogs-and-simulation-palette

---

## Executive Summary

### Current State
```
[R] [P] [S] [T]    ← 4 buttons only, hardcoded dt=0.1
```

### Target State
```
┌─ Simulation Controls ──────────────────────────┐
│  [R] [P] [S] [T] [⚙]                          │
│                                                 │
│  Duration: [___60___] [seconds ▼]              │
│  Progress: ████████████░░░░░░░░░░ 60% (12.5s)  │
└─────────────────────────────────────────────────┘
```

**⚙ Settings Button** → Opens dialog for advanced configuration

---

## Phase 1: UI Refactoring (Priority: HIGH)

### 1.1 Update `simulate_tools_palette.ui`

**Add to existing button row**:
```xml
<!-- Settings Button [⚙] -->
<child>
  <object class="GtkButton" id="settings_simulation_button">
    <property name="visible">True</property>
    <property name="label">⚙</property>
    <property name="tooltip-text">Simulation Settings</property>
    <property name="width-request">40</property>
    <property name="height-request">40</property>
    <style>
      <class name="sim-tool-button"/>
      <class name="settings-button"/>
    </style>
  </object>
</child>
```

**Add duration controls (new row below buttons)**:
```xml
<!-- Duration Controls Row -->
<child>
  <object class="GtkBox" id="duration_controls_box">
    <property name="visible">True</property>
    <property name="orientation">horizontal</property>
    <property name="spacing">6</property>
    <property name="margin">6</property>
    
    <!-- Duration Label -->
    <child>
      <object class="GtkLabel" id="duration_label">
        <property name="visible">True</property>
        <property name="label">Duration:</property>
      </object>
    </child>
    
    <!-- Duration Entry -->
    <child>
      <object class="GtkEntry" id="duration_entry">
        <property name="visible">True</property>
        <property name="text">60</property>
        <property name="width-chars">8</property>
        <property name="tooltip-text">Simulation duration</property>
      </object>
    </child>
    
    <!-- Time Units Dropdown -->
    <child>
      <object class="GtkComboBoxText" id="time_units_combo">
        <property name="visible">True</property>
        <property name="active">1</property> <!-- Default: seconds -->
        <items>
          <item>milliseconds</item>
          <item>seconds</item>
          <item>minutes</item>
          <item>hours</item>
          <item>days</item>
        </items>
      </object>
    </child>
  </object>
</child>
```

**Add progress bar (third row)**:
```xml
<!-- Progress Bar Row -->
<child>
  <object class="GtkBox" id="progress_box">
    <property name="visible">True</property>
    <property name="orientation">vertical</property>
    <property name="spacing">3</property>
    <property name="margin">6</property>
    
    <!-- Progress Bar -->
    <child>
      <object class="GtkProgressBar" id="simulation_progress_bar">
        <property name="visible">True</property>
        <property name="show-text">True</property>
        <property name="text">Ready</property>
        <property name="fraction">0.0</property>
      </object>
    </child>
    
    <!-- Time Display Label -->
    <child>
      <object class="GtkLabel" id="time_display_label">
        <property name="visible">True</property>
        <property name="label">Time: 0.0 / 60.0 s</property>
        <property name="xalign">0</property>
        <style>
          <class name="dim-label"/>
        </style>
      </object>
    </child>
  </object>
</child>
```

**Layout Changes**:
- Change `simulate_tools_container` orientation to **vertical**
- Keep button row horizontal (nested box)
- Duration controls below buttons
- Progress bar at bottom

**Estimated Effort**: 2 hours

---

### 1.2 Create `simulation_settings.ui` Dialog

**New File**: `ui/dialogs/simulation_settings.ui`

**Dialog Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="3.0"/>
  
  <object class="GtkDialog" id="simulation_settings_dialog">
    <property name="title">Simulation Settings</property>
    <property name="modal">True</property>
    <property name="width-request">400</property>
    <property name="height-request">300</property>
    
    <child internal-child="vbox">
      <object class="GtkBox">
        <property name="orientation">vertical</property>
        <property name="spacing">12</property>
        <property name="margin">12</property>
        
        <!-- Time Step Section -->
        <child>
          <object class="GtkFrame">
            <property name="label">Time Step Configuration</property>
            <child>
              <object class="GtkBox">
                <property name="orientation">vertical</property>
                <property name="spacing">6</property>
                <property name="margin">10</property>
                
                <!-- Automatic Radio -->
                <child>
                  <object class="GtkRadioButton" id="dt_auto_radio">
                    <property name="label">Automatic (Recommended)</property>
                    <property name="active">True</property>
                    <property name="tooltip-text">dt = duration / 1000</property>
                  </object>
                </child>
                
                <!-- Manual Radio + Entry -->
                <child>
                  <object class="GtkBox">
                    <property name="orientation">horizontal</property>
                    <property name="spacing">6</property>
                    
                    <child>
                      <object class="GtkRadioButton" id="dt_manual_radio">
                        <property name="label">Manual:</property>
                        <property name="group">dt_auto_radio</property>
                      </object>
                    </child>
                    
                    <child>
                      <object class="GtkEntry" id="dt_manual_entry">
                        <property name="text">0.1</property>
                        <property name="width-chars">8</property>
                        <property name="sensitive">False</property>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
          </object>
        </child>
        
        <!-- Time Scale Section -->
        <child>
          <object class="GtkFrame">
            <property name="label">Time Scale (Advanced)</property>
            <child>
              <object class="GtkBox">
                <property name="orientation">horizontal</property>
                <property name="spacing">6</property>
                <property name="margin">10</property>
                
                <child>
                  <object class="GtkLabel">
                    <property name="label">Scale Factor:</property>
                  </object>
                </child>
                
                <child>
                  <object class="GtkEntry" id="time_scale_entry">
                    <property name="text">1.0</property>
                    <property name="width-chars">8</property>
                    <property name="tooltip-text">1.0 = real-time, 1000 = compressed</property>
                  </object>
                </child>
                
                <child>
                  <object class="GtkLabel">
                    <property name="label">(1.0 = real-time)</property>
                    <style>
                      <class name="dim-label"/>
                    </style>
                  </object>
                </child>
              </object>
            </child>
          </object>
        </child>
        
        <!-- Conflict Resolution Section -->
        <child>
          <object class="GtkFrame">
            <property name="label">Conflict Resolution</property>
            <child>
              <object class="GtkBox">
                <property name="orientation">horizontal</property>
                <property name="spacing">6</property>
                <property name="margin">10</property>
                
                <child>
                  <object class="GtkLabel">
                    <property name="label">Policy:</property>
                  </object>
                </child>
                
                <child>
                  <object class="GtkComboBoxText" id="conflict_policy_combo">
                    <property name="active">0</property>
                    <items>
                      <item>Random</item>
                      <item>Priority</item>
                      <item>Round Robin</item>
                    </items>
                  </object>
                </child>
              </object>
            </child>
          </object>
        </child>
        
      </object>
    </child>
    
    <!-- Dialog Buttons -->
    <child internal-child="action_area">
      <object class="GtkButtonBox">
        <child>
          <object class="GtkButton" id="cancel_button">
            <property name="label">Cancel</property>
          </object>
        </child>
        <child>
          <object class="GtkButton" id="ok_button">
            <property name="label">OK</property>
            <property name="can-default">True</property>
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>
```

**Estimated Effort**: 3 hours

---

## Phase 2: Backend Enhancement (Priority: HIGH)

### 2.1 Enhance `SimulationController`

**File**: `src/shypn/engine/simulation/controller.py`

**Add Properties** (after line 119: `self.time = 0.0`):
```python
# Time abstraction properties
self.time_units = "seconds"      # User-specified: ms, s, min, hr, days
self.duration = None             # Max simulation time (in time_units)
self.time_scale = 1.0            # Real-world scale factor (future use)
self.dt_auto = True              # Auto-compute time step
self.dt_manual = 0.1             # User-specified time step (if not auto)
```

**Add Method** (after `__init__`):
```python
def get_effective_dt(self) -> float:
    """Get effective time step (auto-computed or manual).
    
    Returns:
        float: Time step for simulation
    """
    if self.dt_auto:
        if self.duration and self.duration > 0:
            # Auto: duration / 1000 steps
            return self.duration / 1000.0
        else:
            return 0.1  # Fallback
    else:
        return self.dt_manual

def set_duration(self, duration: float, time_units: str = "seconds"):
    """Set simulation duration and time units.
    
    Args:
        duration: Duration value
        time_units: Time units (milliseconds, seconds, minutes, hours, days)
    """
    self.duration = duration
    self.time_units = time_units

def get_progress(self) -> float:
    """Get simulation progress as fraction [0.0, 1.0].
    
    Returns:
        float: Progress (0.0 = start, 1.0 = complete)
    """
    if self.duration and self.duration > 0:
        return min(self.time / self.duration, 1.0)
    else:
        return 0.0  # Unknown duration
```

**Modify `run()` Method** (line 477):
```python
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    """Run the simulation continuously.
    
    Args:
        time_step: Time increment per step (None = use effective dt)
        max_steps: Maximum steps to execute (None = use duration)
    
    Returns:
        bool: True if started successfully
    """
    if self._running:
        return False
    
    # Use effective dt if not specified
    if time_step is None:
        time_step = self.get_effective_dt()
    
    # Calculate max_steps from duration if not specified
    if max_steps is None and self.duration:
        max_steps = int(self.duration / time_step) + 1
    
    self._running = True
    self._stop_requested = False
    self._time_step = time_step
    self._max_steps = max_steps
    self._step_count = 0
    
    # ... rest of existing code ...
```

**Modify `step()` Method** - Add duration check (after line 372: `self.time += time_step`):
```python
self.time += time_step

# Check duration-based stopping
if self.duration and self.time >= self.duration:
    return False  # Simulation complete
```

**Estimated Effort**: 2 hours

---

### 2.2 Create Time Utilities

**New File**: `src/shypn/utils/time_utils.py`

```python
"""Time unit conversion and formatting utilities."""

TIME_UNITS = {
    'milliseconds': 0.001,
    'seconds': 1.0,
    'minutes': 60.0,
    'hours': 3600.0,
    'days': 86400.0
}

def convert_to_seconds(value: float, units: str) -> float:
    """Convert time value to seconds.
    
    Args:
        value: Time value
        units: Time units (milliseconds, seconds, minutes, hours, days)
    
    Returns:
        float: Time in seconds
    """
    if units not in TIME_UNITS:
        raise ValueError(f"Unknown time unit: {units}")
    return value * TIME_UNITS[units]

def convert_from_seconds(value_seconds: float, target_units: str) -> float:
    """Convert seconds to target time units.
    
    Args:
        value_seconds: Time in seconds
        target_units: Target time units
    
    Returns:
        float: Time in target units
    """
    if target_units not in TIME_UNITS:
        raise ValueError(f"Unknown time unit: {target_units}")
    return value_seconds / TIME_UNITS[target_units]

def auto_select_display_units(duration_seconds: float) -> str:
    """Auto-select appropriate display units based on duration.
    
    Args:
        duration_seconds: Duration in seconds
    
    Returns:
        str: Best units for display (ms, s, min, hr, days)
    """
    if duration_seconds < 1.0:
        return 'milliseconds'
    elif duration_seconds < 60:
        return 'seconds'
    elif duration_seconds < 3600:
        return 'minutes'
    elif duration_seconds < 86400:
        return 'hours'
    else:
        return 'days'

def format_time_display(time_seconds: float, units: str) -> str:
    """Format time value for display.
    
    Args:
        time_seconds: Time in seconds
        units: Display units
    
    Returns:
        str: Formatted string (e.g., "12.5 s", "2.3 min")
    """
    value = convert_from_seconds(time_seconds, units)
    
    # Choose precision based on magnitude
    if value < 1:
        return f"{value:.3f}"
    elif value < 10:
        return f"{value:.2f}"
    elif value < 100:
        return f"{value:.1f}"
    else:
        return f"{value:.0f}"

def get_time_units_abbreviation(units: str) -> str:
    """Get abbreviation for time units.
    
    Args:
        units: Time units (full name)
    
    Returns:
        str: Abbreviation (ms, s, min, hr, d)
    """
    abbrev = {
        'milliseconds': 'ms',
        'seconds': 's',
        'minutes': 'min',
        'hours': 'hr',
        'days': 'd'
    }
    return abbrev.get(units, units)
```

**Estimated Effort**: 1 hour

---

### 2.3 Create Settings Dialog Manager

**New File**: `src/shypn/helpers/simulation_settings_dialog.py`

```python
"""Simulation Settings Dialog Manager."""
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from shypn.engine.simulation.conflict import ConflictResolutionPolicy

class SimulationSettingsDialog:
    """Manager for simulation settings dialog."""
    
    def __init__(self, simulation_controller, parent_window=None):
        """Initialize settings dialog.
        
        Args:
            simulation_controller: SimulationController instance
            parent_window: Parent window for modal dialog
        """
        self.controller = simulation_controller
        self.parent_window = parent_window
        
        # Load UI
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        ui_path = os.path.join(project_root, 'ui', 'dialogs', 'simulation_settings.ui')
        
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Settings UI not found: {ui_path}")
        
        self.builder = Gtk.Builder.new_from_file(ui_path)
        self.dialog = self.builder.get_object('simulation_settings_dialog')
        
        if parent_window:
            self.dialog.set_transient_for(parent_window)
        
        # Get widgets
        self.dt_auto_radio = self.builder.get_object('dt_auto_radio')
        self.dt_manual_radio = self.builder.get_object('dt_manual_radio')
        self.dt_manual_entry = self.builder.get_object('dt_manual_entry')
        self.time_scale_entry = self.builder.get_object('time_scale_entry')
        self.conflict_policy_combo = self.builder.get_object('conflict_policy_combo')
        
        # Connect signals
        self.dt_manual_radio.connect('toggled', self._on_manual_dt_toggled)
        
        # Load current settings
        self._load_settings()
    
    def _load_settings(self):
        """Load current settings from controller."""
        # Time step
        if self.controller.dt_auto:
            self.dt_auto_radio.set_active(True)
        else:
            self.dt_manual_radio.set_active(True)
            self.dt_manual_entry.set_sensitive(True)
        
        self.dt_manual_entry.set_text(str(self.controller.dt_manual))
        
        # Time scale
        self.time_scale_entry.set_text(str(self.controller.time_scale))
        
        # Conflict policy
        policy_map = {
            ConflictResolutionPolicy.RANDOM: 0,
            ConflictResolutionPolicy.PRIORITY: 1,
            ConflictResolutionPolicy.ROUND_ROBIN: 2
        }
        index = policy_map.get(self.controller.conflict_policy, 0)
        self.conflict_policy_combo.set_active(index)
    
    def _on_manual_dt_toggled(self, button):
        """Handle manual dt radio toggle."""
        is_manual = self.dt_manual_radio.get_active()
        self.dt_manual_entry.set_sensitive(is_manual)
    
    def run(self):
        """Show dialog and wait for response.
        
        Returns:
            Gtk.ResponseType: Dialog response
        """
        response = self.dialog.run()
        return response
    
    def apply_settings(self):
        """Apply settings from dialog to controller."""
        # Time step
        self.controller.dt_auto = self.dt_auto_radio.get_active()
        
        try:
            dt_manual = float(self.dt_manual_entry.get_text())
            if dt_manual > 0:
                self.controller.dt_manual = dt_manual
            else:
                raise ValueError("Time step must be positive")
        except ValueError as e:
            print(f"Invalid time step: {e}")
        
        # Time scale
        try:
            time_scale = float(self.time_scale_entry.get_text())
            if time_scale > 0:
                self.controller.time_scale = time_scale
            else:
                raise ValueError("Time scale must be positive")
        except ValueError as e:
            print(f"Invalid time scale: {e}")
        
        # Conflict policy
        policy_index = self.conflict_policy_combo.get_active()
        policy_map = [
            ConflictResolutionPolicy.RANDOM,
            ConflictResolutionPolicy.PRIORITY,
            ConflictResolutionPolicy.ROUND_ROBIN
        ]
        if 0 <= policy_index < len(policy_map):
            self.controller.set_conflict_policy(policy_map[policy_index])
    
    def destroy(self):
        """Destroy the dialog."""
        self.dialog.destroy()
```

**Estimated Effort**: 2 hours

---

## Phase 3: Update Palette Loader (Priority: HIGH)

### 3.1 Modify `SimulateToolsPaletteLoader`

**File**: `src/shypn/helpers/simulate_tools_palette_loader.py`

**Import additions** (top of file):
```python
from shypn.utils.time_utils import convert_to_seconds, format_time_display, get_time_units_abbreviation
from shypn.helpers.simulation_settings_dialog import SimulationSettingsDialog
```

**Add properties** (after line 60: `self.reset_button = None`):
```python
self.settings_button = None
self.duration_entry = None
self.time_units_combo = None
self.progress_bar = None
self.time_display_label = None
self.parent_window = None  # For settings dialog
```

**Update `_load_ui()` method** (after line 77):
```python
self.settings_button = self.builder.get_object('settings_simulation_button')
self.duration_entry = self.builder.get_object('duration_entry')
self.time_units_combo = self.builder.get_object('time_units_combo')
self.progress_bar = self.builder.get_object('simulation_progress_bar')
self.time_display_label = self.builder.get_object('time_display_label')

# Connect new signals
if self.settings_button:
    self.settings_button.connect('clicked', self._on_settings_clicked)

if self.duration_entry:
    self.duration_entry.connect('changed', self._on_duration_changed)

if self.time_units_combo:
    self.time_units_combo.connect('changed', self._on_time_units_changed)
```

**Add new handlers**:
```python
def set_parent_window(self, parent_window):
    """Set parent window for modal dialogs.
    
    Args:
        parent_window: GtkWindow instance
    """
    self.parent_window = parent_window

def _on_settings_clicked(self, button):
    """Handle Settings button click - open settings dialog."""
    if not self.simulation:
        print("Warning: No simulation controller available")
        return
    
    try:
        dialog = SimulationSettingsDialog(self.simulation, self.parent_window)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            dialog.apply_settings()
            print("Settings applied successfully")
        
        dialog.destroy()
    except Exception as e:
        print(f"Error opening settings dialog: {e}")

def _on_duration_changed(self, entry):
    """Handle duration entry change."""
    if not self.simulation:
        return
    
    try:
        duration = float(entry.get_text())
        time_units = self.time_units_combo.get_active_text()
        
        if duration > 0:
            self.simulation.set_duration(duration, time_units)
            self._update_time_display()
    except ValueError:
        pass  # Invalid number, ignore

def _on_time_units_changed(self, combo):
    """Handle time units combo change."""
    if not self.simulation:
        return
    
    try:
        duration_text = self.duration_entry.get_text()
        if duration_text:
            duration = float(duration_text)
            time_units = combo.get_active_text()
            self.simulation.set_duration(duration, time_units)
            self._update_time_display()
    except ValueError:
        pass

def _update_time_display(self):
    """Update progress bar and time display label."""
    if not self.simulation or not self.progress_bar:
        return
    
    current_time = self.simulation.time
    duration = self.simulation.duration
    time_units = self.simulation.time_units
    
    if duration and duration > 0:
        # Update progress bar
        progress = self.simulation.get_progress()
        self.progress_bar.set_fraction(progress)
        
        # Format progress text
        percent = int(progress * 100)
        current_formatted = format_time_display(current_time, time_units)
        self.progress_bar.set_text(f"{percent}% ({current_formatted})")
        
        # Update time display label
        duration_formatted = format_time_display(duration, time_units)
        abbrev = get_time_units_abbreviation(time_units)
        self.time_display_label.set_text(
            f"Time: {current_formatted} / {duration_formatted} {abbrev}"
        )
    else:
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("No duration set")
        self.time_display_label.set_text(f"Time: {current_time:.1f}")
```

**Modify `_on_run_clicked`** (replace hardcoded dt=0.1):
```python
def _on_run_clicked(self, button):
    """Handle Run button click - start continuous simulation."""
    if not self.simulation:
        print("Warning: No simulation controller available")
        return
    
    # Use effective dt (auto or manual)
    self.simulation.run()  # No time_step parameter = use effective dt
    self.run_button.set_sensitive(False)
    self.stop_button.set_sensitive(True)
```

**Modify `_on_step_clicked`** (replace hardcoded dt=0.1):
```python
def _on_step_clicked(self, button):
    """Handle Step button click - execute one step."""
    if not self.simulation:
        return
    
    dt = self.simulation.get_effective_dt()
    success = self.simulation.step(time_step=dt)
    
    if success:
        self.emit('step-executed', self.simulation.time)
        self._update_time_display()
    else:
        # Simulation ended
        self.run_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
```

**Modify `_on_simulation_step`** listener (add progress update):
```python
def _on_simulation_step(self, controller, time):
    """Called after each simulation step."""
    self._update_time_display()
```

**Estimated Effort**: 3 hours

---

## Phase 4: Testing & Validation (Priority: MEDIUM)

### 4.1 Create Test File

**New File**: `tests/test_simulation_timing.py`

```python
"""Tests for simulation timing features."""
import unittest
from shypn.engine.simulation.controller import SimulationController
from shypn.utils.time_utils import convert_to_seconds, format_time_display

class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = []
        self.transitions = []
        self.arcs = []

class TestSimulationTiming(unittest.TestCase):
    """Test simulation timing features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.model = MockModel()
        self.controller = SimulationController(self.model)
    
    def test_default_values(self):
        """Test default time abstraction values."""
        self.assertEqual(self.controller.time_units, "seconds")
        self.assertIsNone(self.controller.duration)
        self.assertEqual(self.controller.time_scale, 1.0)
        self.assertTrue(self.controller.dt_auto)
        self.assertEqual(self.controller.dt_manual, 0.1)
    
    def test_set_duration(self):
        """Test setting duration."""
        self.controller.set_duration(60.0, "seconds")
        self.assertEqual(self.controller.duration, 60.0)
        self.assertEqual(self.controller.time_units, "seconds")
    
    def test_auto_dt_calculation(self):
        """Test automatic dt calculation."""
        self.controller.set_duration(100.0, "seconds")
        dt = self.controller.get_effective_dt()
        self.assertAlmostEqual(dt, 0.1, places=3)  # 100 / 1000
    
    def test_manual_dt(self):
        """Test manual dt override."""
        self.controller.dt_auto = False
        self.controller.dt_manual = 0.05
        dt = self.controller.get_effective_dt()
        self.assertEqual(dt, 0.05)
    
    def test_progress_tracking(self):
        """Test progress calculation."""
        self.controller.set_duration(100.0, "seconds")
        self.controller.time = 0.0
        self.assertEqual(self.controller.get_progress(), 0.0)
        
        self.controller.time = 50.0
        self.assertAlmostEqual(self.controller.get_progress(), 0.5)
        
        self.controller.time = 100.0
        self.assertEqual(self.controller.get_progress(), 1.0)
        
        # Over duration
        self.controller.time = 150.0
        self.assertEqual(self.controller.get_progress(), 1.0)  # Clamped
    
    def test_time_unit_conversion(self):
        """Test time unit conversions."""
        self.assertAlmostEqual(convert_to_seconds(1000, "milliseconds"), 1.0)
        self.assertAlmostEqual(convert_to_seconds(1, "minutes"), 60.0)
        self.assertAlmostEqual(convert_to_seconds(1, "hours"), 3600.0)
    
    def test_time_formatting(self):
        """Test time display formatting."""
        formatted = format_time_display(12.5, "seconds")
        self.assertIsInstance(formatted, str)
        self.assertIn("12", formatted)

if __name__ == "__main__":
    unittest.main()
```

**Estimated Effort**: 2 hours

---

## Implementation Timeline

### Week 1: Core Features
| Day | Task | Hours | Status |
|-----|------|-------|--------|
| Day 1 | Update simulate_tools_palette.ui | 2 | ⏳ |
| Day 1 | Create time_utils.py | 1 | ⏳ |
| Day 2 | Enhance SimulationController | 2 | ⏳ |
| Day 2 | Update SimulateToolsPaletteLoader | 3 | ⏳ |
| Day 3 | Testing and bugfixes | 3 | ⏳ |
| **Total** | **Core Features** | **11 hours** | **⏳** |

### Week 2: Settings Dialog
| Day | Task | Hours | Status |
|-----|------|-------|--------|
| Day 4 | Create simulation_settings.ui | 3 | ⏳ |
| Day 5 | Create simulation_settings_dialog.py | 2 | ⏳ |
| Day 5 | Wire settings button | 1 | ⏳ |
| Day 6 | Testing and documentation | 2 | ⏳ |
| **Total** | **Settings Dialog** | **8 hours** | **⏳** |

**Grand Total**: ~19 hours (~2.5 days of focused work)

---

## Testing Checklist

### Functional Tests
- [ ] Duration entry accepts valid numbers
- [ ] Time units dropdown changes correctly
- [ ] Auto dt calculation: `dt = duration / 1000`
- [ ] Manual dt override works
- [ ] Progress bar updates during simulation
- [ ] Time display shows correct format
- [ ] Settings button opens dialog
- [ ] Settings dialog saves changes
- [ ] Simulation stops at duration
- [ ] Reset clears progress bar

### Edge Cases
- [ ] Duration = 0 (should use fallback dt)
- [ ] Very small duration (0.001 s)
- [ ] Very large duration (86400 s = 1 day)
- [ ] Invalid input in entries (non-numbers)
- [ ] Run without setting duration
- [ ] Change duration during simulation
- [ ] Close settings dialog without saving

### Visual Tests
- [ ] Buttons layout correctly
- [ ] Progress bar visible and updates
- [ ] Time display readable
- [ ] Settings dialog looks good
- [ ] Tooltips show correct information

---

## Documentation Updates

### Files to Update
1. **README.md**: Mention new simulation timing features
2. **User Guide**: Add section on simulation settings
3. **Developer Docs**: Document new APIs

### New Documentation
1. **USER_GUIDE_SIMULATION.md**: How to use simulation controls
2. **API_SIMULATION_CONTROLLER.md**: Developer reference

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ Settings button appears in palette
- ✅ Duration and time units can be set
- ✅ Auto dt calculation works
- ✅ Progress bar shows simulation progress
- ✅ Settings dialog opens and saves

### Full Feature Set
- ✅ All MVP features
- ✅ Manual dt override
- ✅ Time scale factor (future use)
- ✅ Conflict policy in settings
- ✅ Comprehensive tests
- ✅ User documentation

---

## Migration Notes

### Backwards Compatibility
- Old code using `simulation.run(time_step=0.1)` still works
- New code can omit `time_step` parameter
- Default behavior unchanged (dt=0.1 if no duration set)

### Breaking Changes
- None (all changes are additive)

---

## Future Enhancements (Post-MVP)

### Phase 5: Visualization (Future)
- [ ] PlotFormatter for auto-scaling time axis
- [ ] Visualization resampling
- [ ] Export plots with correct time units

### Phase 6: Advanced Features (Future)
- [ ] Adaptive time stepping (RK45, LSODA)
- [ ] Configuration presets
- [ ] Time scale transformation

---

## Summary

**Current**: [R][P][S][T] with hardcoded dt=0.1  
**Target**: [R][P][S][T][⚙] + Duration + Progress + Settings Dialog  
**Effort**: ~19 hours (~2.5 days)  
**Complexity**: Medium (mostly UI + plumbing, minimal algorithm changes)  
**Risk**: Low (additive changes, backwards compatible)

**Key Benefits**:
1. ✅ Users can set simulation duration
2. ✅ Auto-computed time step (sensible defaults)
3. ✅ Progress feedback (users see completion %)
4. ✅ Settings dialog for power users
5. ✅ Foundation for future visualization features

**Next Steps**:
1. Start with Phase 1.1: Update `simulate_tools_palette.ui`
2. Then Phase 2.2: Create `time_utils.py` (no dependencies)
3. Then Phase 2.1: Enhance `SimulationController`
4. Then Phase 3.1: Wire up palette loader
5. Test and iterate

**Ready to implement?** 🚀
