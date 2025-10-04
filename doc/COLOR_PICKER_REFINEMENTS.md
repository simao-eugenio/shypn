# Color Picker Refinements

## Overview
This document describes the refinements made to the color picker component and visual styling for colored net objects.

## Refinements Implemented

### 1. Removed Spacing Between Color Buttons

**Issue**: Color buttons had spacing between them, creating gaps in the color row. GTK buttons have default internal padding and borders that create visual separation.

**Solution**: 
- Set `spacing=0` in the color_box horizontal container
- Removed all margins from the color_box:
  ```python
  self.color_box.set_margin_top(0)
  self.color_box.set_margin_bottom(0)
  self.color_box.set_margin_left(0)
  self.color_box.set_margin_right(0)
  ```
- Ensured `pack_start` uses 0 padding: `pack_start(button, False, False, 0)`
- **Replaced Gtk.Button with Gtk.EventBox** to eliminate internal padding
- **Made DrawingArea full button size** (removed `-4` offset)

**Technical Details**:
- `Gtk.Button` has built-in padding and borders that cannot be fully removed
- `Gtk.EventBox` provides a container without default styling
- Drawing area now fills entire EventBox (no internal padding)
- Colors appear truly side-by-side with no visible gaps

**Result**: Color buttons now appear seamlessly side-by-side creating a continuous color palette row with pattern `color|color|color` instead of `color|space|color|space|color`.

### 2. No CSS Styling Applied to Color Picker Widget

**Design Decision**: Keep the color picker simple and native.

**Implementation**:
- No custom CSS applied to the color picker widget itself
- Selection indication uses Cairo drawing with border thickness
- Selected color: 3px thick dark gray border
- Unselected colors: 1px thin gray border
- EventBox used instead of Button for zero padding

**Result**: 
- Clean, simple appearance
- Native GTK look and feel
- Works consistently across different themes
- Minimal visual distraction - focus on the colors themselves
- No spacing between color squares

### 3. CSS-Like Styling Applied to Colored Net Objects

**Purpose**: Visual enhancement for colored Petri net objects (Places, Transitions, Arcs).

**Implementation**: When objects have non-default colors, they get a subtle glow effect using Cairo rendering.

#### Place Objects (`src/shypn/netobjs/place.py`)

```python
# Add glow effect for colored objects
if self.border_color != self.DEFAULT_BORDER_COLOR:
    # Draw outer glow (subtle shadow effect)
    cr.arc(self.x, self.y, self.radius + 2 / zoom, 0, 2 * math.pi)
    r, g, b = self.border_color
    cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
    cr.set_line_width((self.border_width + 2) / max(zoom, 1e-6))
    cr.stroke()

# Then draw main circle
cr.arc(self.x, self.y, self.radius, 0, 2 * math.pi)
cr.set_source_rgb(*self.border_color)
cr.set_line_width(self.border_width / max(zoom, 1e-6))
cr.stroke()
```

**Effect**:
- Places with colored borders get a 2px outer glow in the same color
- Glow is semi-transparent (30% opacity)
- Makes colored places stand out visually
- Default black borders have no glow

#### Transition Objects (`src/shypn/netobjs/transition.py`)

```python
# Add glow effect for colored objects
if self.border_color != self.DEFAULT_BORDER_COLOR or self.fill_color != self.DEFAULT_COLOR:
    # Draw outer glow (subtle shadow effect)
    cr.rectangle(self.x - half_w - 2 / zoom, self.y - half_h - 2 / zoom, 
                width + 4 / zoom, height + 4 / zoom)
    
    # Use border color for glow if different, otherwise use fill color
    if self.border_color != self.DEFAULT_BORDER_COLOR:
        r, g, b = self.border_color
    else:
        r, g, b = self.fill_color
    
    cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
    cr.set_line_width((self.border_width + 2) / max(zoom, 1e-6))
    cr.stroke()

# Then draw main rectangle
cr.rectangle(self.x - half_w, self.y - half_h, width, height)
cr.set_source_rgb(*self.fill_color)
cr.fill_preserve()
```

**Effect**:
- Transitions with colored borders or fill get a 2px outer glow
- Glow uses border color if available, otherwise fill color
- Semi-transparent (30% opacity)
- Makes colored transitions stand out
- Default black transitions have no glow

#### Arc Objects (`src/shypn/netobjs/arc.py`)

```python
# Add glow effect for colored arcs
if self.color != self.DEFAULT_COLOR:
    # Draw outer glow (subtle shadow effect)
    cr.move_to(start_world_x, start_world_y)
    cr.line_to(end_world_x, end_world_y)
    r, g, b = self.color
    cr.set_source_rgba(r, g, b, 0.3)  # Semi-transparent color
    cr.set_line_width((self.width + 2) / max(zoom, 1e-6))
    cr.stroke()

# Then draw main line
cr.move_to(start_world_x, start_world_y)
cr.line_to(end_world_x, end_world_y)
cr.set_source_rgb(*self.color)
cr.set_line_width(self.width / max(zoom, 1e-6))
cr.stroke()
```

**Effect**:
- Arcs with non-black colors get a 2px wider glow
- Glow is semi-transparent (30% opacity)
- Makes colored arcs more visible and distinct
- Default black arcs have no glow

**Visual Benefits**:
- **Depth perception**: Glow creates visual depth, like CSS box-shadow
- **Color emphasis**: Makes colored objects stand out from default black
- **Professional appearance**: Similar to modern UI design patterns
- **Zoom-aware**: Glow size compensates for zoom level (constant pixel size)
- **Performance**: Minimal overhead, only applies to colored objects

## Code Changes

### Files Modified
1. **src/shypn/helpers/color_picker.py**
   - Modified margins: Set all color_box margins to 0
   - Removed CSS provider setup
   - **Replaced Gtk.Button with Gtk.EventBox** for zero-padding containers
   - **Updated DrawingArea to full button size** (no `-4` offset)
   - Selection indication via Cairo border thickness (3px vs 1px)
   - Added `selected_box` tracking for current selection

2. **src/shypn/netobjs/place.py**
   - Added glow effect rendering for non-default border colors
   - Glow rendered before main circle with semi-transparent outer stroke

3. **src/shypn/netobjs/transition.py**
   - Added glow effect rendering for non-default colors
   - Glow uses border color if available, otherwise fill color

4. **src/shypn/netobjs/arc.py**
   - Added glow effect rendering for non-default colors
   - Glow rendered as wider semi-transparent line before main line

## Visual Behavior

### Color Picker
- **Pattern**: `color|color|color` (no spaces between colors)
- **Unselected colors**: Thin gray border (1px)
- **Selected color**: Thick dark border (3px)
- **No gaps**: Colors appear truly seamless using EventBox containers

### Net Objects with Colors
- **Default colors** (black): No glow effect, standard rendering
- **Custom colors**: 
  - 2px semi-transparent glow around the object
  - Glow uses the same color as the object
  - 30% opacity for subtle effect
  - Creates depth and emphasis

## Usage
No changes required in how other dialogs use the color picker. The refinements are internal to the ColorPickerRow component:

```python
from shypn.helpers.color_picker import setup_color_picker_in_dialog

self.color_picker = setup_color_picker_in_dialog(
    self.builder,
    'container_id',
    current_color=self.obj.border_color,
    button_size=28
)

if self.color_picker:
    self.color_picker.connect('color-selected', self._on_color_selected)
```

## Testing

### Color Picker Testing
1. Open a Place properties dialog
2. Verify color buttons appear with **absolutely no gaps** between them
3. Verify colors form a continuous seamless row: `■■■■■■■` not `■ ■ ■ ■ ■`
4. Click a color button
5. Verify the selected button shows a thicker darker border (3px)
6. Click another color
7. Verify the selection moves to the new button (border thickness changes)

### Net Object Styling Testing
1. Create a Place and open its properties
2. Select a non-black color (e.g., red, blue, green)
3. Apply the changes
4. Verify the Place now has:
   - Colored border
   - Subtle glow effect around it (semi-transparent, same color)
5. Create a Transition and apply a color
6. Verify it also has the glow effect
7. Zoom in/out and verify the glow maintains constant pixel size

## Technical Details

### Button Relief System
Using GTK's native button relief system:
- `Gtk.ReliefStyle.NONE` - Flat, no border
- `Gtk.ReliefStyle.NORMAL` - Raised appearance with border

### Design Philosophy
- Keep it simple and native
- Respect user's GTK theme
- Focus on color content, not fancy styling
- Minimal visual distraction

### Performance
No CSS providers or custom styling, minimal performance overhead.

## Future Enhancements

Possible future improvements:
- Support keyboard navigation (arrow keys)
- Add color name labels (optional)
- Support custom color palettes
- Add color search/filter capability
