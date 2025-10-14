# Production Integration Plan: Settings Sub-Palette

## Executive Summary

We have developed a **new inline settings panel** as a sub-palette of the SwissKnife palette. This replaces the modal dialog approach with an integrated UI that follows the SwissKnife architecture pattern.

**Goal**: Safely integrate the new settings sub-palette into production while preserving all existing functionality, names, and signals.

---

## 1. Current Production Architecture Analysis

### 1.1 Canvas Overlay Structure

**Location**: `src/shypn/helpers/model_canvas_loader.py` (lines 400-500)

```python
# Current hierarchy:
Gtk.Overlay (overlay_widget)
  └── GtkDrawingArea (canvas)
  └── Gtk.Overlay children:
       ├── SwissKnifePalette (bottom-center, 20px from bottom)
       ├── Old ToolsPalette (hidden, backward compat)
       ├── Old OperationsPalette (hidden, backward compat)
       └── Other palettes (zoom, mode, etc.)
```

**SwissKnifePalette positioning**:
```python
swissknife_widget = swissknife_palette.get_widget()
swissknife_widget.set_halign(Gtk.Align.CENTER)
swissknife_widget.set_valign(Gtk.Align.END)
swissknife_widget.set_margin_bottom(20)  # 20px from bottom
overlay_widget.add_overlay(swissknife_widget)
```

### 1.2 Signal Flow

**File**: `src/shypn/helpers/model_canvas_loader.py` (lines 438-447)

```python
# SwissKnifePalette signals wired to canvas loader:
swissknife_palette.connect('tool-activated', ...)
swissknife_palette.connect('mode-change-requested', ...)
swissknife_palette.connect('simulation-step-executed', ...)
swissknife_palette.connect('simulation-reset-executed', ...)
swissknife_palette.connect('simulation-settings-changed', ...)

# Stored reference for mode switching:
self.overlay_managers[drawing_area].swissknife_palette = swissknife_palette
```

### 1.3 SimulateToolsPaletteLoader Integration

**File**: `src/shypn/helpers/swissknife_palette.py`

The simulate category uses a **widget palette** pattern:
- `SimulateToolsPaletteLoader` is instantiated as a widget palette
- Its UI (simulate_tools_revealer) is loaded from `ui/palettes/simulate/simulate_tools_palette.ui`
- It's added to SwissKnife's `sub_palette_area` as a child of `simulate_revealer`

**Current Settings Dialog** (`src/shypn/helpers/simulate_tools_palette_loader.py` line 425):
```python
def _on_settings_clicked(self, button):
    """Opens modal dialog from shypn.dialogs.simulation_settings_dialog"""
    # Shows modal dialog, pauses simulation if running
    # Returns to update duration/progress displays
    # Emits 'settings-changed' signal
```

### 1.4 UI File Locations

**Current Production**:
- `ui/palettes/simulate/simulate_tools_palette.ui` - Simulate palette with [R][P][S][T][⚙] buttons
- `src/shypn/dialogs/simulation_settings_dialog.py` - Modal settings dialog (will be replaced)

**Dev/Prototype**:
- `src/shypn/dev/settings_sub_palette_testbed/settings_palette_prototype.ui` - New settings UI
- `src/shypn/dev/settings_sub_palette_testbed/test_app_with_swissknife.py` - Testbed code

---

## 2. Integration Strategy

### 2.1 Phased Approach

**Phase 1: Backup & Preparation** (30 min)
- Backup current production files
- Create `.back` versions of files to be modified
- Document current state

**Phase 2: UI File Migration** (15 min)
- Move settings UI to proper location
- Update file references

**Phase 3: Code Integration** (1-2 hours)
- Modify `simulate_tools_palette_loader.py`
- Update SwissKnifePalette to accommodate settings revealer
- Wire signals and callbacks

**Phase 4: Testing & Validation** (1 hour)
- Functional testing of all controls
- Signal flow verification
- Edge case testing

**Phase 5: Cleanup** (30 min)
- Remove old dialog code
- Clean up debug statements
- Update documentation

---

## 3. File-by-File Integration Plan

### 3.1 UI File Migration

**ACTION**: Move and rename settings UI file

**Source**: 
```
src/shypn/dev/settings_sub_palette_testbed/settings_palette_prototype.ui
```

**Destination**:
```
ui/palettes/simulate/settings_sub_palette.ui
```

**Changes needed in UI file**:
1. Remove `simulate_tools_revealer` (duplicate from simulate_tools_palette.ui)
2. Keep only `settings_revealer` and its children
3. Ensure all widget IDs are unique and production-ready

---

### 3.2 SimulateToolsPaletteLoader Modification

**FILE**: `src/shypn/helpers/simulate_tools_palette_loader.py`

**BACKUP**: Create `simulate_tools_palette_loader.py.back`

#### 3.2.1 Add Settings UI Loading

**Location**: After line ~110 (after buttons are loaded)

**Add**:
```python
# ============================================================
# Settings Sub-Palette Integration
# ============================================================
# Load settings UI (inline revealer instead of modal dialog)
settings_ui_path = os.path.join(
    os.path.dirname(__file__), '..', '..', 'ui', 'palettes', 
    'simulate', 'settings_sub_palette.ui'
)

if os.path.exists(settings_ui_path):
    settings_builder = Gtk.Builder()
    settings_builder.add_from_file(settings_ui_path)
    
    # Get settings revealer
    self.settings_revealer = settings_builder.get_object('settings_revealer')
    
    if self.settings_revealer:
        # Get child widgets for control access
        self.speed_0_1x_button = settings_builder.get_object('speed_0_1x_button')
        self.speed_1x_button = settings_builder.get_object('speed_1x_button')
        self.speed_10x_button = settings_builder.get_object('speed_10x_button')
        self.speed_60x_button = settings_builder.get_object('speed_60x_button')
        self.time_scale_spin = settings_builder.get_object('time_scale_spin')
        self.settings_apply_button = settings_builder.get_object('settings_apply_button')
        self.settings_reset_button = settings_builder.get_object('settings_reset_button')
        
        # Wire up control handlers
        self._wire_settings_controls(settings_builder)
        
        # Initially hidden
        self.settings_revealer.set_reveal_child(False)
        GLib.idle_add(lambda: self.settings_revealer.set_reveal_child(False))
    else:
        print("⚠️ Settings revealer not found in UI file", file=sys.stderr)
        self.settings_revealer = None
else:
    print(f"⚠️ Settings UI file not found: {settings_ui_path}", file=sys.stderr)
    self.settings_revealer = None
```

#### 3.2.2 Modify Settings Button Handler

**Location**: Replace `_on_settings_clicked()` method (line ~425)

**BACKUP THE OLD CODE**:
```python
def _on_settings_clicked_MODAL_DIALOG(self, button):
    """OLD VERSION - Opens modal dialog (backed up for reference)"""
    # ... existing modal dialog code ...
```

**NEW VERSION**:
```python
def _on_settings_clicked(self, button):
    """Handle Settings button click - toggle inline settings panel.
    
    New behavior: Toggles settings revealer instead of opening modal dialog.
    Settings panel slides up from simulate palette with smooth animation.
    """
    if self.settings_revealer is None:
        # Fallback to old modal dialog if settings UI not loaded
        print("⚠️ Settings panel not available, falling back to modal dialog")
        return self._on_settings_clicked_MODAL_DIALOG(button)
    
    # Toggle settings revealer
    new_state = not self.settings_revealer.get_reveal_child()
    self.settings_revealer.set_reveal_child(new_state)
    
    if new_state:
        # Opening: Make visible first, then reveal
        self.settings_revealer.set_visible(True)
        self.settings_revealer.show_all()
        # Sync current settings to UI
        self._sync_settings_to_ui()
    else:
        # Closing: Start hide animation, set invisible after completion
        GLib.timeout_add(550, lambda: self.settings_revealer.set_visible(False))
```

#### 3.2.3 Add Settings Control Wiring

**Add new method**:
```python
def _wire_settings_controls(self, builder):
    """Wire settings panel controls to simulation settings.
    
    Connects all UI controls (speed presets, spin button, etc.) to
    simulation settings with proper validation and callbacks.
    """
    # Speed preset buttons - exclusive toggle group
    speed_buttons = [
        (self.speed_0_1x_button, 0.1),
        (self.speed_1x_button, 1.0),
        (self.speed_10x_button, 10.0),
        (self.speed_60x_button, 60.0),
    ]
    
    def on_speed_preset_clicked(clicked_button, speed_value):
        """Handle speed preset button click - exclusive toggle."""
        if clicked_button.get_active():
            # Deactivate other buttons
            for btn, _ in speed_buttons:
                if btn != clicked_button and btn.get_active():
                    btn.set_active(False)
            # Apply speed
            if self.simulation:
                self.simulation.settings.time_scale = speed_value
                self.time_scale_spin.set_value(speed_value)
                self.emit('settings-changed')
    
    # Connect speed preset buttons
    for btn, speed in speed_buttons:
        if btn:
            btn.connect('clicked', on_speed_preset_clicked, speed)
    
    # Custom speed spin button
    if self.time_scale_spin:
        def on_time_scale_changed(spin):
            """Handle custom time scale change."""
            # Deactivate all preset buttons
            for btn, _ in speed_buttons:
                if btn and btn.get_active():
                    btn.set_active(False)
            # Apply custom speed
            if self.simulation:
                self.simulation.settings.time_scale = spin.get_value()
                self.emit('settings-changed')
        
        self.time_scale_spin.connect('value-changed', on_time_scale_changed)
    
    # Apply button
    if self.settings_apply_button:
        def on_apply_clicked(button):
            """Apply settings and close panel."""
            # Settings already applied via live updates
            self.settings_revealer.set_reveal_child(False)
            GLib.timeout_add(550, lambda: self.settings_revealer.set_visible(False))
            self.emit('settings-changed')
        
        self.settings_apply_button.connect('clicked', on_apply_clicked)
    
    # Reset button
    if self.settings_reset_button:
        def on_reset_clicked(button):
            """Reset settings to defaults."""
            if self.simulation:
                self.simulation.settings.reset_to_defaults()
                self._sync_settings_to_ui()
                self.emit('settings-changed')
        
        self.settings_reset_button.connect('clicked', on_reset_clicked)

def _sync_settings_to_ui(self):
    """Synchronize current simulation settings to UI controls."""
    if not self.simulation:
        return
    
    time_scale = self.simulation.settings.time_scale
    
    # Update spin button
    if self.time_scale_spin:
        self.time_scale_spin.set_value(time_scale)
    
    # Update preset buttons
    preset_map = {
        0.1: self.speed_0_1x_button,
        1.0: self.speed_1x_button,
        10.0: self.speed_10x_button,
        60.0: self.speed_60x_button,
    }
    
    # Deactivate all first
    for btn in preset_map.values():
        if btn and btn.get_active():
            btn.set_active(False)
    
    # Activate matching preset
    if time_scale in preset_map:
        btn = preset_map[time_scale]
        if btn:
            btn.set_active(True)
```

---

### 3.3 SwissKnifePalette Integration

**FILE**: `src/shypn/helpers/swissknife_palette.py`

**BACKUP**: Create `swissknife_palette.py.back`

**CHANGES**: The SwissKnifePalette already supports widget palettes through its `sub_palette_area` VBox. **No changes needed** - the settings revealer is loaded and integrated by `SimulateToolsPaletteLoader`.

**Verification point**: Check that `sub_palette_area.pack_end()` is available for adding settings revealer.

---

### 3.4 CSS Styling

**FILE**: Create new file `ui/palettes/simulate/settings_sub_palette.css`

**Content**: Extract CSS from test_app_with_swissknife.py (lines 85-207)

**Integration**: Load CSS in SimulateToolsPaletteLoader:
```python
# Load settings CSS
css_path = os.path.join(
    os.path.dirname(settings_ui_path), 
    'settings_sub_palette.css'
)
if os.path.exists(css_path):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(css_path)
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen, css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
```

---

## 4. Signal Preservation

### 4.1 Existing Signals (MUST PRESERVE)

**From SimulateToolsPaletteLoader**:
- `settings-changed` - Emitted when simulation settings change
- `step-executed` - Forwarded from simulation
- `reset-executed` - Forwarded from simulation

**Wiring in model_canvas_loader.py** (KEEP AS-IS):
```python
# These connections remain unchanged:
swissknife_palette.connect('simulation-settings-changed', ...)
```

### 4.2 New Internal Behavior

**Settings button (`_on_settings_clicked`)**:
- **OLD**: Opens modal dialog, pauses simulation, returns after close
- **NEW**: Toggles inline revealer, keeps simulation state, live updates

**No signal changes** - settings-changed still emitted, just triggered by different UI controls.

---

## 5. Testing Checklist

### 5.1 Functional Tests

- [ ] Settings button toggles panel (open/close)
- [ ] Speed preset buttons work (0.1x, 1x, 10x, 60x)
- [ ] Custom speed spin button works
- [ ] Only one preset active at a time
- [ ] Custom spin deactivates presets
- [ ] Conflict policy dropdown works
- [ ] Reset button restores defaults
- [ ] Apply button closes panel
- [ ] Settings persist during simulation
- [ ] Panel slides up smoothly (500ms animation)
- [ ] Panel hides after close animation

### 5.2 Integration Tests

- [ ] Settings panel appears above simulate palette
- [ ] Switching to Edit category hides settings
- [ ] Switching back to Simulate preserves settings state
- [ ] Running simulation updates with new settings
- [ ] Stopping simulation preserves settings
- [ ] Resetting simulation preserves settings
- [ ] Window resize doesn't affect panel positioning

### 5.3 Signal Tests

- [ ] `settings-changed` emitted on speed change
- [ ] `settings-changed` emitted on Apply click
- [ ] `settings-changed` emitted on Reset click
- [ ] Data collector receives settings updates
- [ ] Matplotlib plots update with new time scale

### 5.4 Edge Cases

- [ ] Rapid clicking settings button
- [ ] Changing settings while simulation running
- [ ] Switching tabs while settings open
- [ ] Opening/closing during animation
- [ ] Settings with no simulation loaded

---

## 6. Rollback Plan

### 6.1 Backup Files Created

Before integration:
```
simulate_tools_palette_loader.py.back
swissknife_palette.py.back (if modified)
simulation_settings_dialog.py.back (before removal)
```

### 6.2 Rollback Steps

If integration fails:
1. Stop application
2. Restore `.back` files:
   ```bash
   cd src/shypn/helpers/
   cp simulate_tools_palette_loader.py.back simulate_tools_palette_loader.py
   ```
3. Remove new UI file:
   ```bash
   rm ui/palettes/simulate/settings_sub_palette.ui
   ```
4. Restart application - falls back to modal dialog

---

## 7. File Naming Conventions

### 7.1 Production Files (NEW)

```
ui/palettes/simulate/
  ├── simulate_tools_palette.ui           (existing - unchanged)
  ├── settings_sub_palette.ui             (NEW - settings panel)
  └── settings_sub_palette.css            (NEW - settings styles)

src/shypn/helpers/
  └── simulate_tools_palette_loader.py     (MODIFIED - settings integration)
```

### 7.2 Backup Files (CREATED BEFORE MODIFICATION)

```
src/shypn/helpers/
  └── simulate_tools_palette_loader.py.back

src/shypn/dialogs/
  └── simulation_settings_dialog.py.back   (before removal)
```

### 7.3 Dev Files (ARCHIVED AFTER INTEGRATION)

```
src/shypn/dev/settings_sub_palette_testbed/
  ├── test_app_with_swissknife.py         (keep for reference)
  ├── settings_palette_prototype.ui        (MIGRATED to production)
  └── mock_simulation.py                   (keep for testing)
```

---

## 8. Timeline Estimate

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1 | Backup & Preparation | 30 min | None |
| 2 | UI File Migration | 15 min | Phase 1 |
| 3 | Code Integration | 1-2 hours | Phase 2 |
| 4 | Testing & Validation | 1 hour | Phase 3 |
| 5 | Cleanup | 30 min | Phase 4 |
| **TOTAL** | | **3-4 hours** | |

---

## 9. Success Criteria

✅ **Integration Successful When**:
1. Settings button opens inline panel (not modal dialog)
2. All settings controls functional
3. Settings persist across simulation states
4. All existing signals still emitted
5. No regression in simulate palette functionality
6. Panel animation smooth (500ms slide-up)
7. Panel hides when switching categories
8. Zero console errors during normal operation

---

## 10. Post-Integration Tasks

### 10.1 Documentation Updates

- [ ] Update `CHANGELOG.md` - Note modal dialog → inline panel change
- [ ] Update user documentation - New settings UI workflow
- [ ] Document signal flow in code comments

### 10.2 Code Cleanup

- [ ] Remove old modal dialog code (after 1 week of stable operation)
- [ ] Remove testbed files from dev/ (archive separately)
- [ ] Remove debug print statements
- [ ] Update docstrings

### 10.3 Future Enhancements

- [ ] Add keyboard shortcuts (Ctrl+, for settings)
- [ ] Add more simulation settings (dt, conflict policy UI)
- [ ] Animate settings controls (fade-in on reveal)
- [ ] Add settings presets (save/load configurations)

---

## 11. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Settings revealer breaks layout | Low | Medium | Testbed validation complete |
| Signal flow disrupted | Low | High | Preserve existing signal names |
| Animation performance issues | Low | Low | Already tested in testbed |
| Backward compatibility break | Medium | High | Keep `.back` files, fallback to modal |
| CSS conflicts | Low | Low | Scoped CSS classes |

---

## 12. Key Decisions & Rationale

### 12.1 Why Inline Panel vs Modal Dialog?

**Advantages**:
- ✅ Follows SwissKnife architecture pattern
- ✅ Non-intrusive (can keep working while open)
- ✅ Better visual hierarchy
- ✅ Faster access (no dialog open/close)
- ✅ Modern UI pattern (Gmail, Slack, etc.)

**Disadvantages**:
- ❌ More complex integration
- ❌ Takes up vertical space
- ❌ Slightly more code to maintain

**Decision**: Inline panel wins - better UX and consistency with app architecture.

### 12.2 Why Widget Palette Pattern?

The settings revealer is loaded and managed by `SimulateToolsPaletteLoader` as part of its UI, following the **widget palette pattern** already established in SwissKnifePalette.

**This means**:
- Settings revealer is a child of simulate palette
- Managed lifecycle tied to simulate palette
- Natural integration with sub_palette_area
- Consistent with production architecture

---

## 13. Next Steps

### 13.1 Immediate Actions (Today)

1. ✅ Review this plan with user
2. ⏳ Get approval to proceed
3. ⏳ Execute Phase 1 (Backup)
4. ⏳ Execute Phase 2 (UI Migration)

### 13.2 Tomorrow

1. Execute Phase 3 (Code Integration)
2. Execute Phase 4 (Testing)
3. Execute Phase 5 (Cleanup)

### 13.3 Next Week

1. Monitor for issues
2. Gather user feedback
3. Execute post-integration tasks
4. Plan future enhancements

---

**Document Version**: 1.0  
**Date**: October 11, 2025  
**Author**: GitHub Copilot  
**Status**: ✅ READY FOR REVIEW AND APPROVAL
