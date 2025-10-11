# Settings Sub-Palette Refactoring Plan

**Date**: October 11, 2025  
**Feature**: Convert Settings Button to Expandable Sub-Palette  
**Related**: Phase 1 Time Scale Implementation  
**Priority**: MEDIUM (enables cleaner time scale UI)

---

## Overview

Currently, the Settings [⚙] button opens a modal dialog. This plan refactors it to reveal a sub-palette (similar to SwissKnife pattern) that slides out from the main simulation palette. This provides:

1. **Better UX**: Non-modal, inline settings adjustment
2. **Live Preview**: See changes in real-time without closing dialog
3. **Consistent Pattern**: Matches existing SwissKnife palette behavior
4. **Natural Home**: Perfect place for time scale controls
5. **Discoverable**: Settings visible when palette expanded

---

## Current Architecture

### Main Palette Structure
```
┌─────────────────────────────────────────────────────────┐
│          Simulation Tools Palette (Current)              │
├─────────────────────────────────────────────────────────┤
│  Row 0: [R] [P] [S] [T] [⚙]                             │
│  Row 1: Duration: [60] [seconds ▼]                      │
│  Row 2: [===========Progress===========]                │
│  Row 3: Time: 0.0 / 60.0 s                              │
└─────────────────────────────────────────────────────────┘
                          ↓
                    [⚙] Click opens
                          ↓
          ┌───────────────────────────┐
          │ Simulation Settings Dialog│
          ├───────────────────────────┤
          │ Duration: [60] [sec ▼]    │
          │ Time Step: [Auto/Manual]  │
          │ Conflict: [Random ▼]      │
          │                           │
          │      [Cancel] [Apply]     │
          └───────────────────────────┘
```

### Reference: SwissKnife Pattern
```
Main Canvas
    └── GtkOverlay
        ├── Drawing Area (canvas)
        ├── SwissKnife Button [🔧]
        │   └── GtkRevealer (tools_revealer)
        │       └── GtkFrame (tools_frame)
        │           └── GtkBox (tools_container)
        │               ├── [P] Place
        │               ├── [T] Transition
        │               └── [A] Arc
        └── Simulate Palette [S]
            └── GtkRevealer (simulate_tools_revealer)
                └── GtkGrid (simulate_tools_container)
                    └── Rows 0-3 (current)
```

---

## Proposed Architecture

### New Nested Revealer Structure

```
Main Canvas
    └── GtkOverlay
        └── Simulate Palette [S]
            └── GtkRevealer (simulate_tools_revealer)
                └── GtkGrid (simulate_tools_container)
                    ├── Row 0: [R] [P] [S] [T] [⚙↕]  ⬅ Toggle button
                    ├── Row 1: Duration: [60] [sec ▼]
                    ├── Row 2: [========Progress========]
                    ├── Row 3: Time: 0.0 / 60.0 s
                    └── Row 4: ⭐ NEW SETTINGS SUB-PALETTE
                        └── GtkRevealer (settings_revealer) ⬅ NEW
                            └── GtkGrid (settings_container) ⬅ NEW
                                ├── Row 0: Time Step: [Auto ●] [Manual ○] [0.06] s
                                ├── Row 1: ⭐ Speed: [0.1x] [1x] [10x] [60x] Custom:[5.0]
                                ├── Row 2: Conflict Policy: [Random ▼]
                                └── Row 3: [Apply] [Reset to Defaults]
```

### Visual Mockup: Collapsed State (Same as Current)
```
┌─────────────────────────────────────────────────────────┐
│          Simulation Tools Palette                        │
├─────────────────────────────────────────────────────────┤
│  Row 0: [R] [P] [S] [T] [⚙↕]  ⬅ Settings collapsed      │
│  Row 1: Duration: [60] [seconds ▼]                      │
│  Row 2: [===========Progress===========]                │
│  Row 3: Time: 0.0 / 60.0 s                              │
└─────────────────────────────────────────────────────────┘
```

### Visual Mockup: Expanded State (NEW)
```
┌─────────────────────────────────────────────────────────┐
│          Simulation Tools Palette                        │
├─────────────────────────────────────────────────────────┤
│  Row 0: [R] [P] [S] [T] [⚙↕]  ⬅ Settings expanded       │
│  Row 1: Duration: [60] [seconds ▼]                      │
│  Row 2: [===========Progress===========]                │
│  Row 3: Time: 0.0 / 60.0 s                              │
├─────────────────────────────────────────────────────────┤
│  ╔═══════════════════════════════════════════════════╗ │
│  ║        🔽 SETTINGS SUB-PALETTE 🔽                 ║ │
│  ╠═══════════════════════════════════════════════════╣ │
│  ║ Time Step: [●Auto] [○Manual] [_0.06_] s          ║ │
│  ║                                                    ║ │
│  ║ Playback Speed: (⭐ NEW FEATURE)                  ║ │
│  ║ [0.1x] [0.5x] [1x] [10x] [60x] Custom:[__5.0__] ║ │
│  ║                                                    ║ │
│  ║ Conflict Policy: [Random ▼]                       ║ │
│  ║                                                    ║ │
│  ║         [Apply Changes] [Reset to Defaults]       ║ │
│  ╚═══════════════════════════════════════════════════╝ │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Phase 1: Convert Settings Button to Toggle (1-2 hours)

#### 1.1 Update UI File: `simulate_tools_palette.ui`

**Change 1**: Convert Settings Button to ToggleButton
```xml
<!-- OLD: Regular button -->
<object class="GtkButton" id="settings_simulation_button">
  <property name="visible">True</property>
  <property name="label">⚙</property>
  <property name="tooltip-text">Simulation Settings - Configure duration, time step, and policies</property>
  ...
</object>

<!-- NEW: Toggle button with different icon states -->
<object class="GtkToggleButton" id="settings_simulation_button">
  <property name="visible">True</property>
  <property name="label">⚙</property> <!-- Or ⚙↕ / ⚙↓ when expanded -->
  <property name="tooltip-text">Settings - Show/hide advanced configuration</property>
  <property name="active">False</property>
  <property name="width-request">40</property>
  <property name="height-request">40</property>
  <style>
    <class name="sim-tool-button"/>
    <class name="settings-toggle-button"/> <!-- NEW CSS class -->
  </style>
</object>
```

**Change 2**: Add Row 4 with Nested Revealer
```xml
<!-- Row 4: Settings Sub-Palette (NEW) -->
<child>
  <object class="GtkRevealer" id="settings_revealer">
    <property name="visible">True</property>
    <property name="reveal-child">False</property>
    <property name="transition-type">slide-down</property>
    <property name="transition-duration">300</property>
    <property name="halign">fill</property>
    <property name="hexpand">True</property>
    
    <child>
      <object class="GtkFrame" id="settings_frame">
        <property name="visible">True</property>
        <property name="shadow-type">in</property>
        <style>
          <class name="settings-sub-palette-frame"/>
        </style>
        
        <child>
          <object class="GtkGrid" id="settings_container">
            <property name="visible">True</property>
            <property name="row-spacing">8</property>
            <property name="column-spacing">6</property>
            <property name="margin">12</property>
            <property name="halign">fill</property>
            <style>
              <class name="settings-sub-palette"/>
            </style>
            
            <!-- Settings content goes here (Phase 2) -->
            
          </object>
        </child>
      </object>
    </child>
  </object>
  <packing>
    <property name="left-attach">0</property>
    <property name="top-attach">4</property>
    <property name="width">5</property> <!-- Span all columns -->
  </packing>
</child>
```

#### 1.2 Update Loader: `simulate_tools_palette_loader.py`

**Change 1**: Add new widget references
```python
def _load_ui(self):
    """Load the simulate tools palette UI from file."""
    # ... existing code ...
    
    # Get settings button (now a toggle)
    self.settings_button = self.builder.get_object('settings_simulation_button')
    
    # ⭐ NEW: Get settings sub-palette widgets
    self.settings_revealer = self.builder.get_object('settings_revealer')
    self.settings_container = self.builder.get_object('settings_container')
    
    if not self.settings_revealer:
        raise ValueError("Object 'settings_revealer' not found in simulate_tools_palette.ui")
    
    # ... rest of existing code ...
```

**Change 2**: Replace dialog handler with toggle handler
```python
# OLD: Opens modal dialog
def _on_settings_clicked(self, button):
    """Handle Settings dialog click - open simulation settings dialog."""
    # ... 40 lines of dialog handling ...

# NEW: Toggle sub-palette
def _on_settings_toggled(self, toggle_button):
    """Handle Settings toggle - show/hide settings sub-palette.
    
    Args:
        toggle_button: The settings toggle button
    """
    is_active = toggle_button.get_active()
    
    if is_active:
        # Expand settings sub-palette
        self.settings_revealer.set_reveal_child(True)
        
        # Optional: Pause simulation while editing settings
        self._was_running_before_settings = self.simulation.is_running()
        if self._was_running_before_settings:
            self.simulation.stop()
            self._update_button_states(running=False)
    else:
        # Collapse settings sub-palette
        self.settings_revealer.set_reveal_child(False)
        
        # Optional: Resume simulation if it was running
        if hasattr(self, '_was_running_before_settings') and self._was_running_before_settings:
            self.simulation.run()
            self._update_button_states(running=True)
            self._was_running_before_settings = False

# Update signal connection
def _load_ui(self):
    # ... existing code ...
    
    # OLD:
    # self.settings_button.connect('clicked', self._on_settings_clicked)
    
    # NEW:
    self.settings_button.connect('toggled', self._on_settings_toggled)
```

**Change 3**: Update CSS styling
```python
def _apply_styling(self):
    """Apply custom CSS styling to the simulation tools palette."""
    css = '''
    /* ... existing CSS ... */
    
    /* Settings toggle button - special state when active */
    .settings-toggle-button:checked {
        background: linear-gradient(to bottom, #6c7dc9, #5d6db9);
        border-color: #4a5899;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Settings sub-palette frame */
    .settings-sub-palette-frame {
        background: linear-gradient(to bottom, #273746, #212f3c);
        border: 2px solid #1a252f;
        border-radius: 6px;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    
    /* Settings sub-palette container */
    .settings-sub-palette {
        background: transparent;
    }
    
    /* Settings section label */
    .settings-section-label {
        color: #85929e;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Settings control label */
    .settings-control-label {
        color: #d5d8dc;
        font-size: 11px;
        font-weight: bold;
    }
    '''
    # ... rest of CSS application ...
```

**Estimated Time**: 1-2 hours  
**Files Modified**: 2 files (UI + loader)  
**Lines Changed**: ~150 lines

---

### Phase 2: Populate Settings Sub-Palette (2-3 hours)

#### 2.1 Add Settings Widgets to `settings_container`

**Layout**:
```xml
<object class="GtkGrid" id="settings_container">
  <property name="visible">True</property>
  <property name="row-spacing">8</property>
  <property name="column-spacing">6</property>
  <property name="margin">12</property>
  
  <!-- Row 0: Time Step Controls -->
  
  <!-- Time Step Label -->
  <child>
    <object class="GtkLabel" id="time_step_label">
      <property name="visible">True</property>
      <property name="label">Time Step:</property>
      <property name="xalign">1</property>
      <style>
        <class name="settings-control-label"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">0</property>
      <property name="top-attach">0</property>
    </packing>
  </child>
  
  <!-- Auto Radio Button -->
  <child>
    <object class="GtkRadioButton" id="dt_auto_radio">
      <property name="visible">True</property>
      <property name="label">Auto</property>
      <property name="active">True</property>
      <property name="tooltip-text">Automatic time step calculation</property>
      <style>
        <class name="settings-radio"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">1</property>
      <property name="top-attach">0</property>
    </packing>
  </child>
  
  <!-- Manual Radio Button -->
  <child>
    <object class="GtkRadioButton" id="dt_manual_radio">
      <property name="visible">True</property>
      <property name="label">Manual</property>
      <property name="group">dt_auto_radio</property>
      <property name="tooltip-text">Manual time step entry</property>
      <style>
        <class name="settings-radio"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">2</property>
      <property name="top-attach">0</property>
    </packing>
  </child>
  
  <!-- Manual Time Step Entry -->
  <child>
    <object class="GtkEntry" id="dt_manual_entry">
      <property name="visible">True</property>
      <property name="text">0.06</property>
      <property name="width-chars">6</property>
      <property name="sensitive">False</property> <!-- Enabled when Manual selected -->
      <property name="tooltip-text">Manual time step (seconds)</property>
      <style>
        <class name="settings-entry"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">3</property>
      <property name="top-attach">0</property>
    </packing>
  </child>
  
  <!-- Time Step Unit Label -->
  <child>
    <object class="GtkLabel" id="dt_unit_label">
      <property name="visible">True</property>
      <property name="label">s</property>
      <property name="xalign">0</property>
      <style>
        <class name="settings-unit-label"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">4</property>
      <property name="top-attach">0</property>
    </packing>
  </child>
  
  <!-- Row 1: Separator -->
  <child>
    <object class="GtkSeparator" id="settings_separator_1">
      <property name="visible">True</property>
      <property name="orientation">horizontal</property>
    </object>
    <packing>
      <property name="left-attach">0</property>
      <property name="top-attach">1</property>
      <property name="width">5</property>
    </packing>
  </child>
  
  <!-- Row 2: Playback Speed (⭐ NEW TIME SCALE FEATURE) -->
  
  <!-- Speed Label -->
  <child>
    <object class="GtkLabel" id="speed_label">
      <property name="visible">True</property>
      <property name="label">Speed:</property>
      <property name="xalign">1</property>
      <style>
        <class name="settings-control-label"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">0</property>
      <property name="top-attach">2</property>
    </packing>
  </child>
  
  <!-- Speed Preset Buttons Container -->
  <child>
    <object class="GtkBox" id="speed_presets_box">
      <property name="visible">True</property>
      <property name="orientation">horizontal</property>
      <property name="spacing">2</property>
      
      <!-- 0.1x Button -->
      <child>
        <object class="GtkToggleButton" id="speed_0_1x_button">
          <property name="visible">True</property>
          <property name="label">0.1x</property>
          <property name="tooltip-text">10x slower (slow motion)</property>
          <property name="width-request">45</property>
          <style>
            <class name="speed-preset-button"/>
          </style>
        </object>
      </child>
      
      <!-- 0.5x Button -->
      <child>
        <object class="GtkToggleButton" id="speed_0_5x_button">
          <property name="visible">True</property>
          <property name="label">0.5x</property>
          <property name="tooltip-text">2x slower</property>
          <property name="width-request">45</property>
          <style>
            <class name="speed-preset-button"/>
          </style>
        </object>
      </child>
      
      <!-- 1x Button (Default) -->
      <child>
        <object class="GtkToggleButton" id="speed_1x_button">
          <property name="visible">True</property>
          <property name="label">1x</property>
          <property name="active">True</property> <!-- Default -->
          <property name="tooltip-text">Real-time (1:1)</property>
          <property name="width-request">45</property>
          <style>
            <class name="speed-preset-button"/>
          </style>
        </object>
      </child>
      
      <!-- 10x Button -->
      <child>
        <object class="GtkToggleButton" id="speed_10x_button">
          <property name="visible">True</property>
          <property name="label">10x</property>
          <property name="tooltip-text">10x faster</property>
          <property name="width-request">45</property>
          <style>
            <class name="speed-preset-button"/>
          </style>
        </object>
      </child>
      
      <!-- 60x Button -->
      <child>
        <object class="GtkToggleButton" id="speed_60x_button">
          <property name="visible">True</property>
          <property name="label">60x</property>
          <property name="tooltip-text">1 hour in 1 minute</property>
          <property name="width-request">45</property>
          <style>
            <class name="speed-preset-button"/>
          </style>
        </object>
      </child>
      
    </object>
    <packing>
      <property name="left-attach">1</property>
      <property name="top-attach">2</property>
      <property name="width">2</property>
    </packing>
  </child>
  
  <!-- Custom Speed Label -->
  <child>
    <object class="GtkLabel" id="custom_speed_label">
      <property name="visible">True</property>
      <property name="label">Custom:</property>
      <property name="xalign">1</property>
      <style>
        <class name="settings-control-label"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">3</property>
      <property name="top-attach">2</property>
    </packing>
  </child>
  
  <!-- Custom Speed Spin Button -->
  <child>
    <object class="GtkSpinButton" id="time_scale_spin">
      <property name="visible">True</property>
      <property name="adjustment">time_scale_adjustment</property>
      <property name="digits">2</property>
      <property name="value">1.0</property>
      <property name="tooltip-text">Custom playback speed multiplier</property>
      <property name="width-chars">6</property>
      <style>
        <class name="settings-spin"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">4</property>
      <property name="top-attach">2</property>
    </packing>
  </child>
  
  <!-- Row 3: Separator -->
  <child>
    <object class="GtkSeparator" id="settings_separator_2">
      <property name="visible">True</property>
      <property name="orientation">horizontal</property>
    </object>
    <packing>
      <property name="left-attach">0</property>
      <property name="top-attach">3</property>
      <property name="width">5</property>
    </packing>
  </child>
  
  <!-- Row 4: Conflict Policy -->
  
  <!-- Conflict Policy Label -->
  <child>
    <object class="GtkLabel" id="conflict_policy_label">
      <property name="visible">True</property>
      <property name="label">Conflict:</property>
      <property name="xalign">1</property>
      <style>
        <class name="settings-control-label"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">0</property>
      <property name="top-attach">4</property>
    </packing>
  </child>
  
  <!-- Conflict Policy Combo -->
  <child>
    <object class="GtkComboBoxText" id="conflict_policy_combo">
      <property name="visible">True</property>
      <property name="active">0</property> <!-- Default: Random -->
      <property name="halign">fill</property>
      <style>
        <class name="settings-combo"/>
      </style>
      <items>
        <item>Random</item>
        <item>Oldest</item>
        <item>Youngest</item>
        <item>Priority</item>
      </items>
    </object>
    <packing>
      <property name="left-attach">1</property>
      <property name="top-attach">4</property>
      <property name="width">2</property>
    </packing>
  </child>
  
  <!-- Row 5: Action Buttons -->
  
  <!-- Apply Button -->
  <child>
    <object class="GtkButton" id="settings_apply_button">
      <property name="visible">True</property>
      <property name="label">Apply Changes</property>
      <property name="tooltip-text">Apply settings and close panel</property>
      <property name="halign">end</property>
      <style>
        <class name="settings-apply-button"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">3</property>
      <property name="top-attach">5</property>
      <property name="width">2</property>
    </packing>
  </child>
  
  <!-- Reset Button -->
  <child>
    <object class="GtkButton" id="settings_reset_button">
      <property name="visible">True</property>
      <property name="label">Reset to Defaults</property>
      <property name="tooltip-text">Reset all settings to defaults</property>
      <property name="halign">start</property>
      <style>
        <class name="settings-reset-button"/>
      </style>
    </object>
    <packing>
      <property name="left-attach">0</property>
      <property name="top-attach">5</property>
      <property name="width">2</property>
    </packing>
  </child>
  
</object>

<!-- Adjustment for Time Scale Spin Button -->
<object class="GtkAdjustment" id="time_scale_adjustment">
  <property name="lower">0.01</property>
  <property name="upper">1000.0</property>
  <property name="step-increment">0.1</property>
  <property name="page-increment">1.0</property>
  <property name="value">1.0</property>
</object>
```

**Estimated Time**: 2 hours (UI XML only)  
**Lines Added**: ~300 lines

---

#### 2.2 Wire Settings Controls in Loader

```python
class SimulateToolsPaletteLoader(GObject.GObject):
    
    def _load_ui(self):
        """Load the simulate tools palette UI from file."""
        # ... existing widget references ...
        
        # ⭐ NEW: Get settings sub-palette widgets
        self.settings_revealer = self.builder.get_object('settings_revealer')
        self.settings_container = self.builder.get_object('settings_container')
        
        # Time Step controls
        self.dt_auto_radio = self.builder.get_object('dt_auto_radio')
        self.dt_manual_radio = self.builder.get_object('dt_manual_radio')
        self.dt_manual_entry = self.builder.get_object('dt_manual_entry')
        
        # Speed controls (⭐ NEW)
        self.speed_0_1x_button = self.builder.get_object('speed_0_1x_button')
        self.speed_0_5x_button = self.builder.get_object('speed_0_5x_button')
        self.speed_1x_button = self.builder.get_object('speed_1x_button')
        self.speed_10x_button = self.builder.get_object('speed_10x_button')
        self.speed_60x_button = self.builder.get_object('speed_60x_button')
        self.time_scale_spin = self.builder.get_object('time_scale_spin')
        
        # Conflict policy
        self.conflict_policy_combo = self.builder.get_object('conflict_policy_combo')
        
        # Action buttons
        self.settings_apply_button = self.builder.get_object('settings_apply_button')
        self.settings_reset_button = self.builder.get_object('settings_reset_button')
        
        # Connect signals
        self._connect_settings_signals()
    
    def _connect_settings_signals(self):
        """Connect settings sub-palette widget signals."""
        # Time Step
        if self.dt_auto_radio:
            self.dt_auto_radio.connect('toggled', self._on_dt_mode_changed)
        if self.dt_manual_radio:
            self.dt_manual_radio.connect('toggled', self._on_dt_mode_changed)
        if self.dt_manual_entry:
            self.dt_manual_entry.connect('changed', self._on_dt_manual_changed)
        
        # Speed presets (⭐ NEW)
        speed_buttons = [
            (self.speed_0_1x_button, 0.1),
            (self.speed_0_5x_button, 0.5),
            (self.speed_1x_button, 1.0),
            (self.speed_10x_button, 10.0),
            (self.speed_60x_button, 60.0)
        ]
        for button, value in speed_buttons:
            if button:
                button.connect('toggled', self._on_speed_preset_toggled, value)
        
        # Custom speed
        if self.time_scale_spin:
            self.time_scale_spin.connect('value-changed', self._on_time_scale_changed)
        
        # Conflict policy
        if self.conflict_policy_combo:
            self.conflict_policy_combo.connect('changed', self._on_conflict_policy_changed)
        
        # Action buttons
        if self.settings_apply_button:
            self.settings_apply_button.connect('clicked', self._on_settings_apply_clicked)
        if self.settings_reset_button:
            self.settings_reset_button.connect('clicked', self._on_settings_reset_clicked)
    
    # ─────────────────────────────────────────────────────────────────
    # Time Step Handlers
    # ─────────────────────────────────────────────────────────────────
    
    def _on_dt_mode_changed(self, radio_button):
        """Handle time step mode change (Auto/Manual)."""
        if not radio_button.get_active():
            return
        
        is_manual = self.dt_manual_radio.get_active()
        
        # Enable/disable manual entry
        if self.dt_manual_entry:
            self.dt_manual_entry.set_sensitive(is_manual)
        
        # Update simulation settings
        if self.simulation:
            if is_manual:
                # Read manual dt value
                try:
                    dt = float(self.dt_manual_entry.get_text())
                    self.simulation.settings.dt_manual = dt
                except ValueError:
                    pass  # Invalid input, keep current
            else:
                # Use auto mode
                self.simulation.settings.dt_manual = None
    
    def _on_dt_manual_changed(self, entry):
        """Handle manual time step entry change."""
        if not self.dt_manual_radio.get_active():
            return
        
        try:
            dt = float(entry.get_text().strip())
            if dt > 0 and self.simulation:
                self.simulation.settings.dt_manual = dt
        except ValueError:
            pass  # Invalid input, ignore
    
    # ─────────────────────────────────────────────────────────────────
    # Speed (Time Scale) Handlers (⭐ NEW)
    # ─────────────────────────────────────────────────────────────────
    
    def _on_speed_preset_toggled(self, toggle_button, speed_value):
        """Handle speed preset button toggle.
        
        Args:
            toggle_button: The preset button that was toggled
            speed_value: The speed multiplier (0.1, 0.5, 1.0, 10.0, 60.0)
        """
        if not toggle_button.get_active():
            return
        
        # Uncheck other preset buttons (radio behavior)
        speed_buttons = [
            self.speed_0_1x_button,
            self.speed_0_5x_button,
            self.speed_1x_button,
            self.speed_10x_button,
            self.speed_60x_button
        ]
        for btn in speed_buttons:
            if btn and btn != toggle_button:
                btn.set_active(False)
        
        # Update spin button
        if self.time_scale_spin:
            self.time_scale_spin.set_value(speed_value)
        
        # Update simulation settings
        if self.simulation:
            self.simulation.settings.time_scale = speed_value
            
            # If simulation is running, restart with new speed
            if self.simulation.is_running():
                self.simulation.stop()
                self.simulation.run()
    
    def _on_time_scale_changed(self, spin_button):
        """Handle custom time scale spin button change."""
        value = spin_button.get_value()
        
        # Uncheck all preset buttons (custom speed active)
        speed_buttons = [
            self.speed_0_1x_button,
            self.speed_0_5x_button,
            self.speed_1x_button,
            self.speed_10x_button,
            self.speed_60x_button
        ]
        for btn in speed_buttons:
            if btn:
                btn.set_active(False)
        
        # Update simulation settings
        if self.simulation:
            self.simulation.settings.time_scale = value
            
            # If simulation is running, restart with new speed
            if self.simulation.is_running():
                self.simulation.stop()
                self.simulation.run()
    
    # ─────────────────────────────────────────────────────────────────
    # Conflict Policy Handler
    # ─────────────────────────────────────────────────────────────────
    
    def _on_conflict_policy_changed(self, combo):
        """Handle conflict policy combo change."""
        if not self.simulation:
            return
        
        policy_str = combo.get_active_text()
        if policy_str:
            # Map UI strings to ConflictResolutionPolicy enum
            from shypn.engine.simulation.settings import ConflictResolutionPolicy
            
            policy_map = {
                'Random': ConflictResolutionPolicy.RANDOM,
                'Oldest': ConflictResolutionPolicy.OLDEST,
                'Youngest': ConflictResolutionPolicy.YOUNGEST,
                'Priority': ConflictResolutionPolicy.PRIORITY
            }
            
            if policy_str in policy_map:
                self.simulation.settings.conflict_policy = policy_map[policy_str]
    
    # ─────────────────────────────────────────────────────────────────
    # Action Button Handlers
    # ─────────────────────────────────────────────────────────────────
    
    def _on_settings_apply_clicked(self, button):
        """Handle Apply button click - apply settings and close panel."""
        # Settings are applied in real-time via handlers above
        # Just close the sub-palette
        if self.settings_button:
            self.settings_button.set_active(False)  # Triggers _on_settings_toggled
        
        # Emit settings-changed signal for data collector/matplotlib
        self.emit('settings-changed')
    
    def _on_settings_reset_clicked(self, button):
        """Handle Reset button click - reset all settings to defaults."""
        if not self.simulation:
            return
        
        # Reset to default values
        self.simulation.settings.reset_to_defaults()
        
        # Update UI to reflect defaults
        self._load_settings_into_ui()
        
        # Emit settings-changed signal
        self.emit('settings-changed')
    
    def _load_settings_into_ui(self):
        """Load current settings into UI widgets."""
        if not self.simulation:
            return
        
        settings = self.simulation.settings
        
        # Time Step
        if settings.dt_manual is None:
            self.dt_auto_radio.set_active(True)
            self.dt_manual_entry.set_sensitive(False)
        else:
            self.dt_manual_radio.set_active(True)
            self.dt_manual_entry.set_text(str(settings.dt_manual))
            self.dt_manual_entry.set_sensitive(True)
        
        # Time Scale (⭐ NEW)
        time_scale = settings.time_scale
        self.time_scale_spin.set_value(time_scale)
        
        # Check matching preset button
        preset_map = {
            0.1: self.speed_0_1x_button,
            0.5: self.speed_0_5x_button,
            1.0: self.speed_1x_button,
            10.0: self.speed_10x_button,
            60.0: self.speed_60x_button
        }
        
        # Uncheck all first
        for btn in preset_map.values():
            if btn:
                btn.set_active(False)
        
        # Check matching preset (if any)
        if time_scale in preset_map:
            preset_map[time_scale].set_active(True)
        
        # Conflict Policy
        policy_str = settings.conflict_policy.name.capitalize()
        for i, item in enumerate(['Random', 'Oldest', 'Youngest', 'Priority']):
            if item.upper() == settings.conflict_policy.name:
                self.conflict_policy_combo.set_active(i)
                break
```

**Estimated Time**: 3 hours (Python wiring)  
**Lines Added**: ~250 lines

---

### Phase 3: Backend Integration (30 minutes)

**File**: `src/shypn/engine/simulation/controller.py`

**Change**: Use `time_scale` in `run()` method

```python
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    """Start continuous simulation execution."""
    # ... existing validation code ...
    
    # ⭐ NEW: Calculate steps per GUI update based on time_scale
    base_gui_interval_s = 0.1  # Fixed 100ms GUI updates
    
    # How much model time should pass per GUI update?
    # time_scale = model_seconds / real_seconds
    # Example: time_scale=60 means 60 model seconds per 1 real second
    model_time_per_gui_update = base_gui_interval_s * self.settings.time_scale
    
    # How many simulation steps needed to cover that model time?
    self._steps_per_callback = max(1, int(model_time_per_gui_update / time_step))
    
    # Safety cap to prevent GUI freeze
    self._steps_per_callback = min(self._steps_per_callback, 1000)
    
    # ... rest of existing code ...
```

**Estimated Time**: 30 minutes  
**Lines Changed**: ~10 lines

---

### Phase 4: Enhanced Time Display (30 minutes)

**Update** `_update_progress_display()` to show real-time vs model time:

```python
def _update_progress_display(self):
    """Update progress bar and time display label."""
    if not self.progress_bar or not self.time_display_label:
        return
    
    if self.simulation is None:
        return
    
    settings = self.simulation.settings
    
    # ... existing progress bar code ...
    
    # ⭐ NEW: Enhanced time display with speed indication
    if settings.duration:
        duration_seconds = settings.get_duration_seconds()
        
        # Format model time
        model_text = TimeFormatter.format(
            self.simulation.time,
            settings.time_units,
            include_unit=True
        )
        
        # Format duration
        duration_text = TimeFormatter.format(
            duration_seconds,
            settings.time_units,
            include_unit=True
        )
        
        # Show speed if not 1.0x
        if abs(settings.time_scale - 1.0) > 0.01:
            speed_text = f" @ {settings.time_scale:.1f}x"
        else:
            speed_text = ""
        
        self.time_display_label.set_text(f"Time: {model_text} / {duration_text}{speed_text}")
    else:
        # No duration set
        time_text = TimeFormatter.format(
            self.simulation.time,
            TimeUnits.SECONDS,
            include_unit=True
        )
        self.time_display_label.set_text(f"Time: {time_text}")
```

**Estimated Time**: 30 minutes  
**Lines Changed**: ~20 lines

---

## Testing Plan

### Test 1: Sub-Palette Toggle
1. Click [S] to show simulation palette
2. Click [⚙] to expand settings
3. **Expected**: Settings sub-palette slides down smoothly (300ms)
4. Click [⚙] again to collapse
5. **Expected**: Settings sub-palette slides up and disappears

### Test 2: Settings Persistence
1. Expand settings sub-palette
2. Change time step to Manual: 0.05s
3. Change speed to 10x
4. Change conflict policy to Priority
5. Click [Apply]
6. Collapse and re-expand settings
7. **Expected**: All settings retained

### Test 3: Live Speed Adjustment
1. Run simulation at 1x speed
2. Expand settings while running
3. Click [10x] preset button
4. **Expected**: Simulation speeds up immediately
5. Enter custom value: 5.5x
6. **Expected**: Simulation adjusts to 5.5x

### Test 4: Preset Button Behavior
1. Expand settings
2. Click each preset button: [0.1x] [0.5x] [1x] [10x] [60x]
3. **Expected**: Only one button active at a time (radio behavior)
4. **Expected**: Custom spin reflects clicked value
5. Enter custom value in spin
6. **Expected**: All preset buttons uncheck

### Test 5: Reset to Defaults
1. Change all settings to non-default values
2. Click [Reset to Defaults]
3. **Expected**: 
   - Time Step: Auto
   - Speed: 1.0x (1x button checked)
   - Conflict: Random

### Test 6: Time Display Enhancement
1. Run simulation at 1.0x
2. **Expected**: "Time: 27.5s / 60.0s"
3. Change to 10x
4. **Expected**: "Time: 27.5s / 60.0s @ 10.0x"
5. Change to 60x
6. **Expected**: "Time: 27.5s / 60.0s @ 60.0x"

---

## Implementation Order

### Iteration 1: Basic Toggle (Day 1)
1. ✅ Convert Settings button to ToggleButton
2. ✅ Add empty settings_revealer to Row 4
3. ✅ Wire toggle handler (expand/collapse)
4. ✅ Test basic toggle behavior
5. ✅ Commit: "Add settings sub-palette toggle mechanism"

**Time**: 1-2 hours

### Iteration 2: Populate Settings (Day 1-2)
1. ✅ Add Time Step controls to settings_container
2. ✅ Add Conflict Policy combo
3. ✅ Add Apply/Reset buttons
4. ✅ Wire all non-speed handlers
5. ✅ Test existing settings adjustment
6. ✅ Commit: "Populate settings sub-palette with Time Step and Conflict Policy"

**Time**: 2-3 hours

### Iteration 3: Add Time Scale (Day 2)
1. ✅ Add Speed preset buttons to settings_container
2. ✅ Add custom speed spin button
3. ✅ Wire speed handlers
4. ✅ Update backend controller to use time_scale
5. ✅ Test speed adjustment
6. ✅ Commit: "Add playback speed controls (time scale)"

**Time**: 2-3 hours

### Iteration 4: Enhanced Display (Day 2)
1. ✅ Update time display to show speed
2. ✅ Test display at various speeds
3. ✅ Commit: "Enhance time display with speed indication"

**Time**: 30 minutes

---

## Total Estimated Time

| Phase | Description | Time |
|-------|-------------|------|
| Phase 1 | Toggle button + empty revealer | 1-2 hours |
| Phase 2 | Populate settings widgets | 2-3 hours |
| Phase 2.5 | Wire Python handlers | 2-3 hours |
| Phase 3 | Backend integration (time_scale) | 30 min |
| Phase 4 | Enhanced time display | 30 min |
| **TOTAL** | **Complete implementation** | **6-9 hours** |

**Spread over 2 days**: 3-4 hours per day

---

## Benefits of Sub-Palette Approach

### ✅ Advantages

1. **Non-Modal**: Can adjust settings while observing simulation
2. **Live Preview**: See effects immediately without Apply/Cancel
3. **Consistent Pattern**: Matches SwissKnife and other palettes
4. **Discoverable**: Settings always visible when palette expanded
5. **Natural Home**: Perfect place for time scale controls
6. **Keyboard Friendly**: Can Tab through controls
7. **No Dialog Management**: No separate window to track
8. **Less Code**: Reuses existing palette infrastructure

### ❌ Disadvantages (Minor)

1. **Vertical Space**: Takes more screen space when expanded
   - **Mitigation**: Collapse when not needed (same as SwissKnife)
2. **Mobile/Small Screens**: May be cramped
   - **Mitigation**: Scrollable if needed (future enhancement)

---

## Alternative: Keep Dialog + Add Sub-Palette

**Hybrid Approach**:
- [⚙] Left-click: Toggle sub-palette (common settings)
- [⚙] Right-click: Open full settings dialog (advanced settings)

**Sub-palette contains** (frequently adjusted):
- Time Scale presets + custom
- Time Step (Auto/Manual)

**Dialog contains** (rarely adjusted):
- Conflict Policy
- Advanced stochastic settings
- Animation settings
- Logging/export settings

**Benefit**: Best of both worlds (quick access + full control)  
**Cost**: More complexity, two UI systems to maintain

---

## Recommended Approach

**Go with Sub-Palette Only** (Iterations 1-4 above)

**Rationale**:
1. Simulation settings are few enough to fit in sub-palette
2. Consistent with SwissKnife pattern (users already familiar)
3. Less code to maintain (no dialog)
4. Better UX for common case (adjust speed while running)
5. Can always add dialog later if needed

---

## Files to Modify

### UI Files (1 file)
- `/ui/simulate/simulate_tools_palette.ui` - Add Row 4 with nested revealer

### Python Files (1 file)
- `/src/shypn/helpers/simulate_tools_palette_loader.py` - Wire settings controls

### Backend Files (1 file)
- `/src/shypn/engine/simulation/controller.py` - Use time_scale property

### Documentation Files (Update after implementation)
- `/doc/time/SIMULATION_TIME_SCALING_ANALYSIS.md` - Mark Phase 1 complete
- `/doc/time/UI_REQUIREMENTS_TIME_SCALE.md` - Add "Implemented" section

**Total**: 3 files modified

---

## Next Steps After This Plan

1. **Review**: User approves sub-palette approach
2. **Implement**: Follow iteration order (4 commits over 2 days)
3. **Test**: Run all 6 test scenarios
4. **Document**: Update analysis documents
5. **Phase 2**: Consider real-time tracking (model vs real time)

