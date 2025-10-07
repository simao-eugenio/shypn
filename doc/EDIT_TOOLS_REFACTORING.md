# Edit Tools Palette Refactoring

## Overview
Refactored the edit tools palette `[P][T][A][S]` to use floating buttons instead of a revealer container, making it consistent with the editing operations palette design.

## Changes Made

### 1. UI File (`ui/palettes/edit_tools_palette.ui`)

**Before:**
- Used `GtkRevealer` container with slide-up animation
- Nested structure: Revealer → Box → Buttons

**After:**
- Direct `GtkBox` container with floating buttons
- Flat structure: Box → Buttons
- Properties:
  - `halign="center"`, `valign="end"` - centered at bottom
  - `margin_bottom="78"` - positioned above [E] button
  - `margin_end="190"` - offset left from center

### 2. Loader Class (`src/shypn/helpers/edit_tools_loader.py`)

**Removed:**
- `self.edit_tools_revealer` attribute
- Revealer-based show/hide logic (`set_reveal_child()`)

**Updated:**
- `load()` method now returns `GtkBox` instead of `GtkRevealer`
- `show()` / `hide()` methods use simple `show()` / `hide()` instead of reveal animation
- `get_widget()` returns the container box directly
- `is_visible()` uses `get_visible()` instead of `get_reveal_child()`

### 3. Canvas Overlay Manager (`src/shypn/canvas/canvas_overlay_manager.py`)

**Updated `_setup_edit_palettes()`:**
```python
if edit_tools_widget:
    # Start hidden - will be revealed by edit palette's [E] button
    edit_tools_widget.show_all()  # Ensure children are ready
    edit_tools_widget.hide()      # But hide the palette initially
    self.overlay_widget.add_overlay(edit_tools_widget)
```

## Benefits

### Consistency
- Both tool palettes (`[P][T][A][S]` and `[U][R]|[L]|[D][A]|[X][C][V]`) now use the same design pattern
- Unified floating button appearance
- Same positioning system

### Simplicity
- Removed unnecessary revealer wrapper
- Simpler show/hide logic
- More straightforward widget hierarchy

### Performance
- Direct widget manipulation instead of animation transitions
- Instant show/hide instead of 200ms slide animation
- Less memory overhead (fewer wrapper widgets)

## Layout

When `[E]` button is pressed, both palettes appear side-by-side above it:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│                                                      │
│                                                      │
│                                                      │
│      [P][T][A][S]          [U][R]|[L]|[D][A]|[X][C][V]      │
│                        [E]                           │
└──────────────────────────────────────────────────────┘
```

### Positioning Details
- **Vertical**: Both at `margin_bottom="78"` (above [E] button)
- **Horizontal** (Updated approach to prevent overlap):
  - Edit tools: `halign="end"` + `margin_end="300"` (from right side)
  - Editing operations: `halign="start"` + `margin_start="300"` (from left side)
- **Strategy**: Opposite alignment prevents overlap and creates natural spacing

## Backward Compatibility

The public API of `EditToolsLoader` remains unchanged:
- `show()` / `hide()` still work
- `get_widget()` still returns the root widget
- `is_visible()` still checks visibility
- Signal emissions unchanged

Only internal implementation changed from revealer to direct box manipulation.

## Testing

✅ Application starts successfully
✅ Edit tools palette starts hidden
✅ Both palettes appear when [E] is pressed
✅ Both palettes hide when [E] is pressed again
✅ Tool selection still works correctly
✅ CSS styling preserved

## Future Improvements

Consider:
1. Adjusting spacing between the two palettes
2. Fine-tuning horizontal positioning for different screen sizes
3. Adding visual separator between the two tool groups
4. Unified styling across both palettes

---
**Date:** October 6, 2025  
**Status:** ✅ Complete
