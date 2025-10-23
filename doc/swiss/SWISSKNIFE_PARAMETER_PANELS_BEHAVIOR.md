# SwissKnifePalette - Parameter Panels Behavior

**Date:** October 22, 2025  
**Status:** Architecture Confirmed  
**Key Principle:** **Constant Height Main Palette + Dismissible Parameter Panels Above**

---

## Core Architecture Principle

### ✅ CONFIRMED BEHAVIOR

1. **Main palette (categories + sub-palettes) = CONSTANT HEIGHT (114px)**
   - Never changes size
   - Always same height regardless of category
   - Always visible at canvas bottom

2. **Parameter panels (micro-panels) = ABOVE main palette**
   - Slide UP from below main palette
   - Appear ABOVE sub-palettes (not inside)
   - Can be **dismissed/retracted** (toggle on/off)
   - Do NOT affect main palette height

---

## Visual Behavior

### State 1: Only Main Palette (No Parameters)
```
┌─────────────────────────────────────────────┐
│              CANVAS (full visibility)       │
│                                             │
│                                             │
│                                             │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ SwissKnifePalette (114px CONSTANT)      │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ [P][T][A][S][L]  (Edit 50px)        │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ [Edit] [Simulate] [Layout]          │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
Height: 114px (constant)
Canvas occluded: 114px
```

### State 2: Simulate Palette (No Settings Panel)
```
┌─────────────────────────────────────────────┐
│              CANVAS (full visibility)       │
│                                             │
│                                             │
│                                             │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ SwissKnifePalette (114px CONSTANT) ✅    │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ [Step][Reset][Play][⚙️]  (50px) ✅   │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ [Edit] [Simulate] [Layout]          │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
Height: 114px (still constant!) ✅
Canvas occluded: 114px (unchanged)
```

### State 3: Simulate + Settings Panel REVEALED
```
┌─────────────────────────────────────────────┐
│              CANVAS                         │
│                                             │
│                                             │
│ ┌─────────────────────────────────────────┐ │ ← ABOVE main palette
│ │ ⚙️ Simulation Settings (micro-panel)     │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ │
│ │ Time Scale:    [════════░░] 1.0x        │ │
│ │ Progress:      [████████░░] 80%         │ │
│ │ Token Speed:   [══════░░░░] 0.6x        │ │
│ │ Visualization: [✓] Smooth               │ │
│ │                                         │ │
│ │ [Dismiss] or click [⚙️] again to hide   │ │
│ └─────────────────────────────────────────┘ │ ← Slides UP/DOWN
│ ▲ Parameter panel ABOVE main palette       │
│ ┌─────────────────────────────────────────┐ │
│ │ SwissKnifePalette (114px CONSTANT) ✅    │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ [Step][Reset][Play][⚙️]  (50px)      │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ [Edit] [Simulate] [Layout]          │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
Main palette height: 114px (STILL constant!) ✅
Parameter panel: Variable height ABOVE
Canvas occluded: 114px + [panel height above]
```

---

## Parameter Panel Properties

### Simulation Settings Micro-Panel

**Contents:**
1. **Time Scale Slider**
   - Controls simulation speed (0.1x to 5.0x)
   - Real-time adjustment
   - Default: 1.0x

2. **Progress Visualizer**
   - Shows simulation progress (0-100%)
   - Token flow visualization
   - Current step count

3. **Token Speed Slider**
   - Controls animation speed (0.1x to 2.0x)
   - Visual flow rate
   - Default: 0.6x

4. **Visualization Options**
   - [ ] Smooth transitions
   - [ ] Show token count
   - [ ] Highlight active paths

**Behavior:**
- **Reveal:** Click [⚙️] button → panel slides UP (400ms animation)
- **Dismiss:** Click [⚙️] again → panel slides DOWN (400ms animation)
- **Auto-dismiss:** Switch to different category → panel auto-hides
- **Position:** Always ABOVE main palette, never inside sub-palette

---

## User Interaction Flow

### Scenario: User Wants to Adjust Simulation Speed

```
Step 1: User opens Simulate palette
  Action: Click [Simulate] category button
  Result: Sub-palette reveals [Step][Reset][Play][⚙️]
  Height: 114px ✅

Step 2: User clicks settings button
  Action: Click [⚙️] button
  Result: Settings panel slides UP above sub-palette
  Height: 114px main + [panel above] ✅

Step 3: User adjusts time scale
  Action: Drag slider to 2.0x
  Result: Simulation speed changes immediately
  Height: Still 114px main + [panel above] ✅

Step 4: User dismisses panel
  Action: Click [⚙️] button again (toggle)
  Result: Settings panel slides DOWN and disappears
  Height: 114px ✅

Step 5: User switches to Edit
  Action: Click [Edit] category button
  Result: Settings panel auto-hides (if still open)
          Edit sub-palette reveals
  Height: 114px ✅ (constant throughout!)
```

---

## Technical Implementation

### Widget Hierarchy (Vertical Stack)

```
SwissKnifePalette Container (Gtk.Box VERTICAL)
│
├─ 1. parameter_panel_revealer (TOP)
│   │   GtkRevealer
│   │   transition_type: SLIDE_UP
│   │   transition_duration: 400ms
│   │   reveal_child: False (hidden by default)
│   │
│   └─ [Dynamic parameter panel widget]
│       ├─ simulation_settings_panel
│       ├─ layout_algorithm_panel (future)
│       ├─ analysis_options_panel (future)
│       └─ transform_settings_panel (future)
│
├─ 2. sub_palette_area (MIDDLE)
│   │   Gtk.Box
│   │   size_request: (-1, 50px) ← FIXED HEIGHT
│   │
│   ├─ edit_revealer (50px)
│   ├─ simulate_revealer (50px)
│   └─ layout_revealer (50px)
│
└─ 3. category_box (BOTTOM)
    │   Gtk.Box
    │   height: 44px fixed
    │
    └─ [Edit] [Simulate] [Layout] buttons
```

### Parameter Panel Manager API

```python
class ParameterPanelManager:
    """Manages dismissible parameter panels above sub-palettes."""
    
    def register_parameter_panel(self, tool_id: str, 
                                 panel_factory: Callable):
        """Register panel factory for a tool.
        
        Args:
            tool_id: Unique identifier (e.g., 'simulate_settings')
            panel_factory: Function that creates panel widget
        """
        self.panel_registry[tool_id] = panel_factory
    
    def show_panel(self, tool_id: str):
        """Reveal parameter panel with slide UP animation."""
        panel = self.panel_registry[tool_id]()  # Build fresh
        self.parameter_panel_revealer.add(panel)
        self.parameter_panel_revealer.set_reveal_child(True)
    
    def hide_panel(self):
        """Dismiss parameter panel with slide DOWN animation."""
        self.parameter_panel_revealer.set_reveal_child(False)
        GLib.timeout_add(400, self._remove_and_destroy_panel)
    
    def toggle_panel(self, tool_id: str):
        """Toggle panel visibility (reveal/dismiss)."""
        if self.active_tool_id == tool_id:
            self.hide_panel()  # Dismiss
        else:
            self.show_panel(tool_id)  # Reveal
```

### SimulateToolsPaletteLoader Integration

```python
class SimulateToolsPaletteLoader:
    """Simulation controls (refactored - NO internal settings)."""
    
    def __init__(self, model):
        self.model = model
        # Build ONLY simulation controls
        self.controls = self._create_controls()  # [Step][Reset][Play][⚙️]
        # NO settings_revealer - removed!
    
    def _create_controls(self):
        """Create simulation control buttons (50px height)."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Step button
        step_btn = Gtk.Button(label="Step")
        step_btn.connect('clicked', self._on_step_clicked)
        box.pack_start(step_btn, False, False, 0)
        
        # Reset button
        reset_btn = Gtk.Button(label="Reset")
        reset_btn.connect('clicked', self._on_reset_clicked)
        box.pack_start(reset_btn, False, False, 0)
        
        # Play button
        play_btn = Gtk.Button(label="Play")
        play_btn.connect('clicked', self._on_play_clicked)
        box.pack_start(play_btn, False, False, 0)
        
        # Settings button → triggers ParameterPanelManager
        settings_btn = Gtk.Button(label="⚙️")
        settings_btn.connect('clicked', self._on_settings_clicked)
        box.pack_start(settings_btn, False, False, 0)
        
        return box
    
    def _on_settings_clicked(self, button):
        """Settings button clicked → toggle parameter panel."""
        # Emit signal to trigger ParameterPanelManager
        self.emit('settings-requested')
    
    def create_settings_panel(self) -> Gtk.Widget:
        """Factory method for parameter panel (called by manager).
        
        Returns:
            Gtk.Widget: Fresh settings panel widget
        """
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.set_margin_start(12)
        panel.set_margin_end(12)
        panel.set_margin_top(12)
        panel.set_margin_bottom(12)
        
        # Time scale slider
        time_scale_label = Gtk.Label(label="Time Scale:")
        time_scale_slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.1, 5.0, 0.1
        )
        time_scale_slider.set_value(1.0)
        panel.pack_start(time_scale_label, False, False, 0)
        panel.pack_start(time_scale_slider, False, False, 0)
        
        # Progress bar
        progress_label = Gtk.Label(label="Progress:")
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_fraction(0.0)
        panel.pack_start(progress_label, False, False, 0)
        panel.pack_start(progress_bar, False, False, 0)
        
        # Token speed slider
        token_speed_label = Gtk.Label(label="Token Speed:")
        token_speed_slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.1, 2.0, 0.1
        )
        token_speed_slider.set_value(0.6)
        panel.pack_start(token_speed_label, False, False, 0)
        panel.pack_start(token_speed_slider, False, False, 0)
        
        # Visualization options
        viz_label = Gtk.Label(label="Visualization:")
        smooth_check = Gtk.CheckButton(label="Smooth transitions")
        smooth_check.set_active(True)
        panel.pack_start(viz_label, False, False, 0)
        panel.pack_start(smooth_check, False, False, 0)
        
        return panel
```

### Wiring in SwissKnifePalette

```python
class SwissKnifePalette(GObject.GObject):
    """Main palette coordinator."""
    
    def _register_default_sub_palettes(self, mode, model, tool_registry):
        """Register sub-palettes for specified mode."""
        
        # ... other sub-palettes ...
        
        # Simulate sub-palette
        simulate_loader = SimulateToolsPaletteLoader(model)
        
        # Register parameter panel factory
        self.parameter_panel_manager.register_parameter_panel(
            'simulate_settings',
            simulate_loader.create_settings_panel  # Factory function
        )
        
        # Wire settings button
        simulate_loader.connect('settings-requested', 
                               self._on_settings_requested)
    
    def _on_settings_requested(self, loader):
        """Handle settings button click from simulate loader."""
        self.parameter_panel_manager.toggle_panel('simulate_settings')
```

---

## Universal Pattern for All Tools

### Any Tool Can Use This Pattern

**Example: Layout Algorithm Parameters**

```python
class LayoutToolsSubPalette:
    """Layout tools with algorithm parameters."""
    
    def __init__(self):
        self.controls = self._create_controls()
    
    def _create_controls(self):
        """Layout tool buttons + settings."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Auto layout button
        auto_btn = Gtk.Button(label="Auto")
        box.pack_start(auto_btn, False, False, 0)
        
        # Hierarchical layout button
        hier_btn = Gtk.Button(label="Hier")
        box.pack_start(hier_btn, False, False, 0)
        
        # Force-directed layout button
        force_btn = Gtk.Button(label="Force")
        box.pack_start(force_btn, False, False, 0)
        
        # Algorithm settings button
        settings_btn = Gtk.Button(label="⚙️")
        settings_btn.connect('clicked', lambda b: 
            self.emit('settings-requested'))
        box.pack_start(settings_btn, False, False, 0)
        
        return box
    
    def create_settings_panel(self) -> Gtk.Widget:
        """Factory for layout algorithm parameters."""
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Node spacing slider
        spacing_slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 10, 200, 10
        )
        panel.pack_start(Gtk.Label(label="Node Spacing:"), False, False, 0)
        panel.pack_start(spacing_slider, False, False, 0)
        
        # Layout direction
        direction_combo = Gtk.ComboBoxText()
        direction_combo.append_text("Top-Down")
        direction_combo.append_text("Left-Right")
        panel.pack_start(Gtk.Label(label="Direction:"), False, False, 0)
        panel.pack_start(direction_combo, False, False, 0)
        
        return panel
```

**Same pattern, different content!**

---

## Key Benefits

### 1. Constant Canvas Space ✅
- Main palette: **114px always**
- No jumping when switching categories
- Predictable interface

### 2. Dismissible Parameters ✅
- User controls when to show settings
- Parameters don't clutter interface
- Quick toggle on/off

### 3. Universal Pattern ✅
- Any tool can add parameter panel
- Consistent user experience
- Easy to extend

### 4. Wayland Safe ✅
- All widgets in same overlay context
- No reparenting operations
- Panels built fresh each time

### 5. Space Efficient ✅
- Parameters only visible when needed
- Main palette minimal footprint
- More canvas workspace

---

## Summary

### ✅ CONFIRMED Architecture

**Main Palette:**
- Height: **114px constant** (never changes)
- Position: Canvas bottom (center aligned)
- Contains: Category buttons + sub-palettes (all 50px)

**Parameter Panels (Micro-Panels):**
- Position: **ABOVE main palette** (slides UP/DOWN)
- Behavior: **Dismissible** (toggle reveal/hide)
- Trigger: Click [⚙️] settings button
- Auto-hide: When switching categories
- Height: Variable (content-dependent)

**Result:**
- Main palette height: Constant 114px ✅
- Canvas visibility: Predictable and stable ✅
- User experience: Clean and efficient ✅
- Wayland safety: 100% safe (no reparenting) ✅

**This is the universal pattern for all tools needing parameter settings!** 🎯
