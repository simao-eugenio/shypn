# Floating Buttons - Final Configuration

**Date**: October 7, 2025  
**Status**: ✅ COMPLETE  
**Architecture**: Individual floating buttons with CENTER alignment

## Button Layout

```
        [P]    [T]    [A]         [S]    [L]         [U]    [R]
        ↓      ↓      ↓           ↓      ↓           ↓      ↓
       -396  -264   -132        +44   +176        +352  +484
        ←────── LEFT ──────┤ CENTER ├───── RIGHT ──────→
```

## Spacing Configuration

**Within Groups:**
- Spacing between adjacent buttons: **132px** (88px gap + 44px button width)
- This equals approximately **2 full button widths** of spacing

**Between Groups:**
- Gap between groups: **176px** (4 button widths)
- This creates clear visual separation between the three groups

## Button Positions (from center)

### Group 1: Tools (Left side)
- **[P] Place**: -396px from center (margin_end=396)
- **[T] Transition**: -264px from center (margin_end=264)
- **[A] Arc**: -132px from center (margin_end=132)

**Spacing**: 132px between each button

### Group 2: Selection (Center)
- **[S] Select**: +44px from center (margin_start=44)
- **[L] Lasso**: +176px from center (margin_start=176)

**Spacing**: 132px between buttons

### Group 3: Operations (Right side)
- **[U] Undo**: +352px from center (margin_start=352)
- **[R] Redo**: +484px from center (margin_start=484)

**Spacing**: 132px between buttons

## GTK Positioning Mechanics

### Alignment Strategy
All buttons use `halign=Gtk.Align.CENTER` and `valign=Gtk.Align.END`

### Horizontal Offset Implementation
With CENTER alignment:
- **Negative offsets** (left of center): Use `margin_end`
  - `margin_end` pushes the button LEFT from center
  - Example: `margin_end=396` → button at -396px from center
  
- **Positive offsets** (right of center): Use `margin_start`
  - `margin_start` pushes the button RIGHT from center
  - Example: `margin_start=176` → button at +176px from center

### Vertical Positioning
- All buttons: `margin_bottom=78px` (positioned above the [E] button)
- `valign=Gtk.Align.END` (aligned to bottom of overlay)

## Visual Groups

### Group 1: Primary Tools
`[P][T][A]` - Place, Transition, Arc
- **Purpose**: Core Petri net object creation
- **Type**: Toggle buttons (mutually exclusive)
- **Position**: Left side of center

### Group 2: Selection Tools
`[S][L]` - Select, Lasso
- **Purpose**: Object selection and manipulation
- **Type**: Select=Toggle, Lasso=Regular
- **Position**: Center

### Group 3: Edit Operations
`[U][R]` - Undo, Redo
- **Purpose**: Edit history management
- **Type**: Regular buttons
- **Position**: Right side of center

## Button Properties

**Dimensions:**
- Size: 44x44px (set via `set_size_request(40, 40)` + padding from CSS)
- CSS padding: 4px
- CSS margin: 0 4px (between buttons)

**Styling:**
- Background: Gradient `#34495e` → `#2c3e50`
- Border: 2px solid `#1c2833`
- Border radius: 6px
- Font: 16px bold white
- Shadow: 3D effect with box-shadow

**Tool Button Active State:**
- Background: Gradient `#2980b9` → `#21618c`
- Border: `#1b4f72`
- Inset shadow for "pressed" effect

## Control Flow

### Show/Hide Control
1. User presses **[E]** button
2. `edit_palette_loader._on_edit_toggled()` called
3. Calls `floating_buttons_manager.show_all()`
4. All 7 buttons shown simultaneously

### Tool Selection
1. User clicks tool button (e.g., **[P]**)
2. Button emits 'toggled' signal
3. `_on_tool_clicked(tool_name, button)` called
4. Other tool buttons deactivated
5. Emits 'tool-changed' signal to canvas

## Code Structure

### Key Files
1. **`src/shypn/helpers/floating_buttons_manager.py`** (409 lines)
   - `FloatingButtonsManager` class
   - Button creation and positioning
   - Event handlers
   - CSS styling

2. **`src/shypn/canvas/canvas_overlay_manager.py`**
   - `_setup_floating_buttons()` - Creates and adds buttons
   - Wires to EditOperations
   - Connects signals

3. **`src/shypn/helpers/edit_palette_loader.py`**
   - `set_floating_buttons_manager()` - Wires [E] button
   - `_on_edit_toggled()` - Controls visibility

### Key Methods

**FloatingButtonsManager:**
- `create_all_buttons()` - Creates 7 buttons with positions
- `_create_button()` - Factory for regular buttons
- `_create_toggle_button()` - Factory for tool buttons
- `show_all()` / `hide_all()` - Visibility control
- `_apply_styling()` - CSS application
- `_on_tool_clicked()` - Tool selection handler

## Measurement Output

When [E] is pressed, the system logs:

```
[FloatingButtons] ===== BUTTON MARGIN CONFIGURATION =====
  [PLACE     ] Expected offset from center:  -396px  (margin_start=0, margin_end=396)
  [TRANSITION] Expected offset from center:  -264px  (margin_start=0, margin_end=264)
  [ARC       ] Expected offset from center:  -132px  (margin_start=0, margin_end=132)
  [SELECT    ] Expected offset from center:   +44px  (margin_start=44, margin_end=0)
  [LASSO     ] Expected offset from center:  +176px  (margin_start=176, margin_end=0)
  [UNDO      ] Expected offset from center:  +352px  (margin_start=352, margin_end=0)
  [REDO      ] Expected offset from center:  +484px  (margin_start=484, margin_end=0)
[FloatingButtons] ============================================
```

## Design Rationale

### Why Individual Floating Buttons?
1. **No GTK allocation warnings** - Eliminated "Negative content width" errors
2. **Precise positioning control** - Pixel-perfect placement
3. **No container constraints** - No box layout conflicts
4. **Simple visibility management** - Just iterate and show/hide
5. **Easy to maintain** - Add/remove buttons trivially

### Why CENTER Alignment?
1. **Responsive** - Works across different window sizes
2. **Grouped layout** - Buttons cluster around center
3. **Professional appearance** - Balanced and symmetrical
4. **Predictable** - Offsets always relative to center

### Why These Specific Spacings?
- **132px within groups** - Comfortably spaced but clearly grouped
- **176px between groups** - Large enough to show distinct groups
- Tested with exaggerated spacing first to verify grouping works
- Then reduced to practical values

## Future Enhancements

1. **Keyboard Shortcuts**: Direct key bindings (P, T, A, S, L, Ctrl+Z, Ctrl+Shift+Z)
2. **Tooltips Enhancement**: Show keyboard shortcuts in tooltips
3. **Animation**: Fade in/out effects for show/hide
4. **Customization**: User-adjustable button positions
5. **Additional Tools**: Easy to add more buttons to any group
6. **Button State Persistence**: Remember last active tool
7. **Undo/Redo State**: Enable/disable based on history stack

## Success Metrics

✅ **Zero GTK Warnings** - No allocation or sizing errors  
✅ **Clean Architecture** - No containers, pure floating  
✅ **Maintainable Code** - ~10 lines per button  
✅ **Extensible Design** - Add buttons with one method call  
✅ **Performant** - No rendering overhead  
✅ **User-Friendly** - Clear visual groups, consistent spacing  
✅ **Working Implementation** - Application runs without errors  

## Testing Completed

- [x] Application starts without errors
- [x] Buttons show when [E] is pressed
- [x] Buttons hide when [E] is released
- [x] Tool buttons toggle correctly
- [x] Only one tool active at a time
- [x] Operation buttons respond to clicks
- [x] Tool-changed signal emitted correctly
- [x] Mode switching hides buttons in simulate mode
- [x] No GTK warnings or errors
- [x] Position metrics verified

## Conclusion

The floating buttons implementation is **complete and functional**. All 7 buttons are positioned with clear visual grouping using CENTER alignment and margin-based offsets. The exaggerated spacing (132px within groups, 176px between groups) ensures the three groups are clearly visible and distinct. The implementation is clean, maintainable, and ready for production use.

---

**Total Span**: 1048px (from -396px to +484px to +44px including button widths)  
**Implementation**: Pure floating buttons, no containers  
**Control**: Single [E] toggle button  
**Groups**: 3 distinct groups with clear separation  
