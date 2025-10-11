# UI Requirements for Time Scale Implementation

**Date**: October 11, 2025  
**Feature**: Playback Speed Control (Time Scale)  
**Related**: Phase 1 of SIMULATION_TIME_SCALING_ANALYSIS.md

---

## Current UI Layout

```
┌─────────────────────────────────────────────────────────┐
│          Simulation Tools Palette (Current)              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Row 0: Control Buttons                                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│  │ R  │ │ P  │ │ S  │ │ T  │ │ ⚙  │                   │
│  │Run │ │Step│ │Stop│ │Rst │ │Set │                   │
│  └────┘ └────┘ └────┘ └────┘ └────┘                   │
│                                                          │
│  Row 1: Duration Controls                               │
│  Duration: [____60____] [seconds ▼]                     │
│                                                          │
│  Row 2: Progress Bar                                    │
│  [████████████░░░░░░░░░░░░░░░░] 45%                    │
│                                                          │
│  Row 3: Time Display                                    │
│  Time: 27.5 / 60.0 s                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Proposed UI Enhancement - Option 1 (RECOMMENDED)

**Add Row 4: Playback Speed Controls**

```
┌─────────────────────────────────────────────────────────┐
│       Simulation Tools Palette (With Time Scale)         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Row 0: Control Buttons                                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│  │ R  │ │ P  │ │ S  │ │ T  │ │ ⚙  │                   │
│  │Run │ │Step│ │Stop│ │Rst │ │Set │                   │
│  └────┘ └────┘ └────┘ └────┘ └────┘                   │
│                                                          │
│  Row 1: Duration Controls                               │
│  Duration: [____60____] [seconds ▼]                     │
│                                                          │
│  Row 2: Progress Bar                                    │
│  [████████████░░░░░░░░░░░░░░░░] 45%                    │
│                                                          │
│  Row 3: Time Display                                    │
│  Model: 27.5 s | Real: 27.5 s | Speed: 1.0x            │
│                                                          │
│  Row 4: Playback Speed  ⭐ NEW                          │
│  Speed: [0.1x] [0.5x] [1x] [10x] [60x] Custom:[__5.0__]│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Widgets to Add**:
1. Label: "Speed:"
2. Toggle buttons: [0.1x] [0.5x] [1x] [10x] [60x] (preset speeds)
3. Label: "Custom:"
4. SpinButton: Range 0.01 to 1000.0, step 0.1, value = 1.0

**Advantages**:
- ✅ Quick access to common speeds (presets)
- ✅ Custom speed for precise control
- ✅ Clear visual separation from duration
- ✅ Intuitive: Higher number = faster playback

**Disadvantages**:
- Takes more vertical space (one more row)
- More widgets to implement

---

## Proposed UI Enhancement - Option 2 (COMPACT)

**Combine with Duration Row**

```
┌─────────────────────────────────────────────────────────┐
│       Simulation Tools Palette (Compact Version)         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Row 0: Control Buttons                                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│  │ R  │ │ P  │ │ S  │ │ T  │ │ ⚙  │                   │
│  │Run │ │Step│ │Stop│ │Rst │ │Set │                   │
│  └────┘ └────┘ └────┘ └────┘ └────┘                   │
│                                                          │
│  Row 1: Duration & Speed Controls  ⭐ MODIFIED          │
│  Duration: [__60__] [sec▼]  Speed: [__1.0x__] [▲][▼]  │
│                                                          │
│  Row 2: Progress Bar                                    │
│  [████████████░░░░░░░░░░░░░░░░] 45%                    │
│                                                          │
│  Row 3: Time Display                                    │
│  Model: 27.5 s | Real: 27.5 s | 1.0x                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Widgets to Add**:
1. Label: "Speed:" (in existing row 1)
2. SpinButton: Range 0.01 to 1000.0, with up/down arrows
3. Label: Shows "x" multiplier

**Advantages**:
- ✅ Compact (no new row)
- ✅ Clean and simple
- ✅ Quick adjustment with spin buttons

**Disadvantages**:
- No preset buttons (need manual entry)
- Row 1 becomes crowded

---

## Proposed UI Enhancement - Option 3 (MINIMAL)

**Settings Dialog Only**

```
┌─────────────────────────────────────────────────────────┐
│          Simulation Tools Palette (Minimal)              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Row 0: Control Buttons                                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│  │ R  │ │ P  │ │ S  │ │ T  │ │ ⚙  │ ⬅ Click for speed │
│  │Run │ │Step│ │Stop│ │Rst │ │Set │                   │
│  └────┘ └────┘ └────┘ └────┘ └────┘                   │
│                                                          │
│  Row 1: Duration Controls                               │
│  Duration: [____60____] [seconds ▼]                     │
│                                                          │
│  Row 2: Progress Bar                                    │
│  [████████████░░░░░░░░░░░░░░░░] 45%                    │
│                                                          │
│  Row 3: Time Display  ⭐ MODIFIED                       │
│  Model: 27.5 s | Real: 27.5 s | Speed: 1.0x            │
│                                                          │
└─────────────────────────────────────────────────────────┘

When user clicks ⚙ Settings button:

┌─────────────────────────────────────────┐
│    Simulation Settings Dialog            │
├─────────────────────────────────────────┤
│                                          │
│  Duration:  [__60__]  [seconds ▼]       │
│                                          │
│  Time Step: [Auto ●] [Manual ○]         │
│             [_0.06_] seconds             │
│                                          │
│  ⭐ NEW                                  │
│  Playback Speed:                         │
│  [0.1x] [0.5x] [1x] [10x] [60x]         │
│  Custom: [____1.0____] x                │
│                                          │
│  Conflict Policy:                        │
│  [Random ▼]                              │
│                                          │
│         [Cancel]  [Apply]                │
└─────────────────────────────────────────┘
```

**Widgets to Add**:
1. In Settings Dialog: "Playback Speed" section
2. Preset buttons + custom spin button
3. Update time display label (existing widget)

**Advantages**:
- ✅ No visual clutter on main palette
- ✅ All settings in one place
- ✅ Minimal implementation

**Disadvantages**:
- Need to open dialog to change speed
- Less discoverable
- Cannot change speed while running (need to stop/restart)

---

## Detailed Widget Specifications

### For Option 1 (Recommended) & Option 2

#### SpinButton: time_scale_spin
```xml
<object class="GtkSpinButton" id="time_scale_spin">
  <property name="visible">True</property>
  <property name="adjustment">time_scale_adjustment</property>
  <property name="digits">2</property>
  <property name="value">1.0</property>
  <property name="tooltip-text">Playback speed multiplier (1.0 = real-time)</property>
  <property name="width-chars">6</property>
  <style>
    <class name="sim-control-spin"/>
  </style>
</object>

<object class="GtkAdjustment" id="time_scale_adjustment">
  <property name="lower">0.01</property>
  <property name="upper">1000.0</property>
  <property name="step-increment">0.1</property>
  <property name="page-increment">1.0</property>
  <property name="value">1.0</property>
</object>
```

#### Toggle Buttons (Option 1 only): Preset Speeds
```xml
<!-- 0.1x Button -->
<object class="GtkToggleButton" id="speed_0_1x_button">
  <property name="visible">True</property>
  <property name="label">0.1x</property>
  <property name="tooltip-text">10x slower (slow motion)</property>
  <property name="width-request">50</property>
  <style>
    <class name="speed-preset-button"/>
  </style>
</object>

<!-- Similar for 0.5x, 1x, 10x, 60x -->
```

#### Label: Speed Display
```xml
<object class="GtkLabel" id="speed_label">
  <property name="visible">True</property>
  <property name="label">Speed:</property>
  <property name="xalign">1</property>
  <style>
    <class name="sim-control-label"/>
  </style>
</object>
```

---

## Updated Time Display Format

### Current
```
Time: 27.5 / 60.0 s
```

### Proposed (All Options)
```
Model: 27.5 s | Real: 27.5 s | Speed: 1.0x
```

**Or shorter version:**
```
27.5s (M) / 27.5s (R) @ 1.0x
```

**Or minimal version:**
```
27.5 / 60.0 s @ 1.0x
```

---

## CSS Styling Requirements

### New CSS Classes Needed

```css
/* Speed preset buttons (Option 1) */
.speed-preset-button {
    background: linear-gradient(to bottom, #5d6d7e, #566573);
    border: 2px solid #34495e;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    color: white;
    min-width: 45px;
    min-height: 30px;
    padding: 2px 4px;
}

.speed-preset-button:checked {
    background: linear-gradient(to bottom, #3498db, #2980b9);
    border-color: #1f5a8b;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.speed-preset-button:hover {
    background: linear-gradient(to bottom, #6c7a89, #5d6d7e);
    border-color: #4a5f7f;
}

/* Speed spin button */
.sim-control-spin {
    background: #34495e;
    color: white;
    border: 2px solid #2c3e50;
    border-radius: 4px;
    font-size: 12px;
    padding: 2px 4px;
}

.sim-control-spin entry {
    background: #2c3e50;
    color: white;
    border: none;
}

.sim-control-spin button {
    background: #566573;
    border: 1px solid #34495e;
}

.sim-control-spin button:hover {
    background: #6c7a89;
}
```

---

## Implementation Complexity Comparison

### Option 1: Full Preset Buttons (RECOMMENDED)
**UI Changes**:
- Add Row 4 to GtkGrid (1 new row)
- Add 1 Label ("Speed:")
- Add 5 ToggleButtons (0.1x, 0.5x, 1x, 10x, 60x)
- Add 1 Label ("Custom:")
- Add 1 SpinButton (custom value)
- Add 1 GtkAdjustment (for SpinButton)
- Update time_display_label format

**Code Changes**:
- `simulate_tools_palette.ui`: ~80 lines XML
- `simulate_tools_palette_loader.py`: ~100 lines Python
  - Get widget references (7 new widgets)
  - Connect 6 signals (5 toggle + 1 spin)
  - Handler: `_on_speed_preset_clicked()`
  - Handler: `_on_speed_custom_changed()`
  - Update: `_update_time_display()` format

**Total**: ~180 lines, **2-3 hours**

---

### Option 2: Compact SpinButton Only
**UI Changes**:
- Modify Row 1 (add to existing)
- Add 1 Label ("Speed:")
- Add 1 SpinButton
- Add 1 GtkAdjustment
- Update time_display_label format

**Code Changes**:
- `simulate_tools_palette.ui`: ~30 lines XML
- `simulate_tools_palette_loader.py`: ~40 lines Python
  - Get widget reference (1 widget)
  - Connect 1 signal
  - Handler: `_on_speed_changed()`
  - Update: `_update_time_display()` format

**Total**: ~70 lines, **1-1.5 hours**

---

### Option 3: Settings Dialog Only
**UI Changes**:
- Modify simulation_settings_dialog.ui
- Add "Playback Speed" section
- Add preset buttons + spin button
- Update time_display_label format (main palette)

**Code Changes**:
- `simulation_settings_dialog.ui`: ~60 lines XML
- `simulation_settings_dialog.py`: ~60 lines Python
  - Get widget references
  - Connect signals
  - Save/load time_scale setting
- `simulate_tools_palette_loader.py`: ~20 lines Python
  - Update: `_update_time_display()` format

**Total**: ~140 lines, **2 hours**

---

## Backend Changes (All Options)

These changes are **identical** for all UI options:

### File: `src/shypn/engine/simulation/controller.py`

**Modify `run()` method** (~line 483):

```python
def run(self, time_step: float = None, max_steps: Optional[int] = None) -> bool:
    """Start continuous simulation execution."""
    # ... existing validation code ...
    
    # ⭐ NEW: Calculate steps per GUI update based on time_scale
    base_gui_interval_s = 0.1  # Fixed 100ms GUI updates
    
    # How much model time should pass per GUI update?
    # time_scale = model_seconds / real_seconds
    model_time_per_gui_update = base_gui_interval_s * self.settings.time_scale
    
    # How many simulation steps needed to cover that model time?
    self._steps_per_callback = max(1, int(model_time_per_gui_update / time_step))
    self._steps_per_callback = min(self._steps_per_callback, 1000)  # Safety cap
    
    # ... rest of existing code ...
```

**Lines changed**: ~10 lines  
**Time**: 30 minutes

---

## Recommended Choice: Option 1

### Why Option 1?

1. **Best UX**: Preset buttons for common speeds (0.1x, 1x, 10x, 60x)
2. **Flexibility**: Custom spin button for precise control
3. **Discoverability**: Speed control always visible
4. **Live adjustment**: Can change speed without reopening dialog
5. **Professional**: Matches video player controls (1x, 2x, etc.)

### Implementation Order

1. **First**: Backend changes (30 min)
2. **Second**: Option 2 (Compact) for testing (1-1.5 hours)
3. **Third**: Upgrade to Option 1 (Full) after testing (1-2 hours)

**Total estimated time**: 3-4 hours for complete implementation

---

## Testing Scenarios

### Test 1: Slow Motion (0.1x)
```
Duration: 10 seconds
Time Scale: 0.1x (10x slower)
Expected: 10 seconds model time takes 100 seconds real time
```

### Test 2: Fast Forward (60x)
```
Duration: 1 hour (3600 seconds)
Time Scale: 60x
Expected: 1 hour model time takes 60 seconds real time
```

### Test 3: Custom Speed (5.5x)
```
Duration: 55 seconds
Time Scale: 5.5x
Expected: 55 seconds model time takes 10 seconds real time
```

### Test 4: Real-time (1.0x)
```
Duration: 30 seconds
Time Scale: 1.0x
Expected: 30 seconds model time takes 30 seconds real time
```

### Test 5: Very Fast (288x) - Your Example
```
Duration: 24 hours (86400 seconds)
Time Scale: 288x
Expected: 24 hours model time takes 300 seconds (5 minutes) real time
```

---

## Files to Modify

### UI Files
1. `ui/simulate/simulate_tools_palette.ui` - Add widgets

### Python Files
1. `src/shypn/helpers/simulate_tools_palette_loader.py` - Widget handling
2. `src/shypn/engine/simulation/controller.py` - Backend logic

### Optional (if adding to settings dialog)
3. `ui/dialogs/simulation_settings_dialog.ui`
4. `src/shypn/dialogs/simulation_settings_dialog.py`

---

## Summary

**Minimum viable UI** (Option 2): 
- 1 SpinButton
- 1 Label
- Update time display format
- **Time: 1-1.5 hours**

**Recommended UI** (Option 1):
- 5 Preset buttons
- 1 SpinButton  
- 2 Labels
- Update time display format
- **Time: 2-3 hours**

**Backend** (all options):
- Modify `SimulationController.run()`
- Use `time_scale` in step calculation
- **Time: 30 minutes**

**Total for full implementation**: **3-4 hours**

---

## Next Steps

1. **Decide** which UI option to implement
2. **Prototype** backend changes first (30 min)
3. **Test** backend with hardcoded time_scale values
4. **Implement** chosen UI option
5. **Test** with all scenarios above
6. **Document** usage in user guide

