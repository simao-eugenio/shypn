# Palette Positioning and Mode Switching - Implementation Complete

**Date**: October 7, 2025  
**Status**: ✅ Complete

## Summary

Successfully implemented proper positioning of edit tools palettes with 80px gap and fixed mode switching behavior.

## Changes Made

### 1. Palette Positioning (80px Gap)

**Problem**: Both palettes were using CENTER alignment, causing them to overlap at the screen center.

**Solution**: Used FILL alignment with absolute margins to position palettes independently.

**Implementation** (`src/shypn/helpers/model_canvas_loader.py`):
```python
# Tools palette (148px wide): positioned at x=749
tools_revealer.set_margin_start(749)
tools_revealer.set_margin_end(1023)
tools_revealer.set_hexpand(False)
position=(Gtk.Align.FILL, Gtk.Align.END)

# Operations palette (194px wide): positioned at x=977 (749 + 148 + 80)
operations_revealer.set_margin_start(977)
operations_revealer.set_margin_end(749)
operations_revealer.set_hexpand(False)
position=(Gtk.Align.FILL, Gtk.Align.END)
```

**Result**: 
- Tools palette: 148px wide, starts at x=749
- Gap: 80px (from x=897 to x=977)
- Operations palette: 194px wide, starts at x=977
- Total virtual width: 422px, centered at screen center (960px on 1920px display)

### 2. Initial Mode State

**Problem**: Application was showing Simulation mode on startup instead of Edit mode.

**Root Cause**: `overlay_widget.show_all()` was recursively showing all children, including the [S] button that we had explicitly hidden.

**Solution** (`src/shypn/helpers/model_canvas_loader.py`):
```python
# Call show_all() first
overlay_widget.show_all()

# Then explicitly hide [S] button AFTER show_all()
if overlay_manager.simulate_palette:
    sim_widget = overlay_manager.simulate_palette.get_widget()
    if sim_widget:
        sim_widget.hide()
```

Also set initial visibility in `canvas_overlay_manager.py`:
```python
def _setup_simulate_palettes(self):
    # ...
    if simulate_tools_widget:
        self.overlay_widget.add_overlay(simulate_tools_widget)
        simulate_tools_widget.hide()  # Start hidden
    
    if simulate_widget:
        self.overlay_widget.add_overlay(simulate_widget)
        simulate_widget.hide()  # Start hidden ([S] button)
```

### 3. Mode Button Visual Feedback

**Problem**: Buttons used `set_sensitive(False)` to show active mode, but disabled buttons look inactive (grayed out).

**Solution**: Use CSS class `active-mode` to highlight the active mode button.

**Implementation** (`src/ui/palettes/mode/mode_palette_loader.py`):
```python
def update_button_states(self):
    edit_context = self.edit_button.get_style_context()
    sim_context = self.sim_button.get_style_context()
    
    if self.current_mode == 'edit':
        edit_context.add_class('active-mode')
        sim_context.remove_class('active-mode')
    else:
        edit_context.remove_class('active-mode')
        sim_context.add_class('active-mode')

# CSS styling
.mode-button.active-mode {
    background: linear-gradient(to bottom, #3498db, #2980b9);
    border: 2px solid #2471a3;
    font-weight: bold;
    color: white;
    box-shadow: inset 0 1px 3px rgba(255, 255, 255, 0.3),
                0 2px 4px rgba(0, 0, 0, 0.3);
}
```

### 4. Mode Switching Behavior

**Enhancement**: Ensure tool palettes from previous mode are closed when switching modes.

**Implementation** (`src/shypn/helpers/model_canvas_loader.py`):
```python
def _on_mode_changed(self, mode_palette, mode, drawing_area, *args):
    if mode == 'edit':
        # 1. Show [E] button, hide [S] button
        # 2. Reset [E] button to OFF state
        # 3. Hide simulation palettes
        overlay_manager.edit_palette.set_tools_visible(False)
        
    elif mode == 'sim':
        # 1. Hide [E] button, show [S] button
        # 2. Reset [S] button to OFF state
        # 3. Hide edit palettes
        overlay_manager.simulate_palette.set_tools_visible(False)
        palette_manager.hide_all()
```

## Final State

### On Startup:
- ✅ **[Edit] button**: Highlighted as active (blue gradient)
- ✅ **[Sim] button**: Normal appearance (inactive)
- ✅ **[E] button**: Visible at bottom-center
- ✅ **[S] button**: Hidden
- ✅ **Edit palettes**: Hidden (toggle with [E] button)
- ✅ **Sim palettes**: Hidden

### When [Sim] clicked:
- ✅ **[Sim] button**: Becomes highlighted (active)
- ✅ **[Edit] button**: Returns to normal (inactive)
- ✅ **[E] button**: Hidden
- ✅ **[S] button**: Shown at bottom-center
- ✅ **Edit palettes**: Automatically hidden
- ✅ **[E] toggle**: Reset to OFF

### When [Edit] clicked:
- ✅ **[Edit] button**: Becomes highlighted (active)
- ✅ **[Sim] button**: Returns to normal (inactive)
- ✅ **[S] button**: Hidden
- ✅ **[E] button**: Shown at bottom-center
- ✅ **Sim palettes**: Automatically hidden
- ✅ **[S] toggle**: Reset to OFF

### Palette Layout:
```
                      Screen Center (960px)
                            ↓
    [P][T][A]  ← 80px gap →  [S][L][U][R]
    ↑                                     ↑
  x=749                                x=1171
  width=148px                          width=194px
  
  Virtual combined palette: 422px wide, centered over [E] button
```

## Files Modified

1. `src/shypn/helpers/model_canvas_loader.py`
   - Fixed palette positioning with FILL alignment
   - Fixed initial state visibility
   - Enhanced mode switching to close tool palettes
   - Added explicit [S] button hide after show_all()

2. `src/shypn/canvas/canvas_overlay_manager.py`
   - Set simulate palettes to hidden by default

3. `src/ui/palettes/mode/mode_palette_loader.py`
   - Changed from set_sensitive() to CSS class highlighting
   - Added active-mode CSS styling
   - Improved visual feedback

4. `src/shypn/edit/palette_manager.py`
   - Added reference_widget parameter for future relative positioning

## Architecture

```
ModelCanvasLoader
├── CanvasOverlayManager
│   ├── [Edit] Mode Button (bottom-left) ← CSS highlighted when active
│   ├── [Sim] Mode Button (bottom-left) ← CSS highlighted when active
│   ├── [E] Toggle Button (bottom-center) ← Shown in Edit mode
│   └── [S] Toggle Button (bottom-center) ← Shown in Sim mode
│
└── PaletteManager
    ├── ToolsPalette [P][T][A] ← FILL aligned, margin_start=749
    └── OperationsPalette [S][L][U][R] ← FILL aligned, margin_start=977
```

## Testing

- ✅ Startup in Edit mode with correct visual state
- ✅ 80px gap between palettes visible
- ✅ Mode switching hides previous mode's palettes
- ✅ Toggle buttons ([E]/[S]) reset when switching modes
- ✅ CSS highlighting shows active mode clearly

## Notes

- FILL alignment with absolute margins used for precise positioning
- Assumes 1920px screen width (standard desktop)
- For different screen sizes, margins would need to be calculated dynamically
- show_all() timing critical: must hide [S] button AFTER show_all() call
