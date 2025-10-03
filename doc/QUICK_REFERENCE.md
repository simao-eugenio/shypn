# Quick Reference: Legacy Rendering Changes

## At a Glance

| Object | Property | Before | After | Reason |
|--------|----------|--------|-------|--------|
| Place | Fill | White | None (hollow) | Classic Petri net style |
| Place | Border width | 2.0px | 3.0px | Better visibility |
| Place | Tokens | Dots | Text (Arial 14pt) | Clearer display |
| Transition | Border width | 1.0px | 3.0px | Better visibility |
| Arc | Arrowhead style | Filled triangle | Two lines | Legacy style |
| Arc | Arrowhead size | 10px | 15px | More visible |
| Arc | Arrowhead angle | 30° (π/6) | 36° (π/5) | Legacy standard |
| Arc | Weight font | Sans 11pt | Arial 12pt Bold | Better readability |
| Arc | Weight background | None | White 0.8 alpha | Text clarity |
| InhibitorArc | Marker style | Circle outline | White fill + ring | Legacy style |

## Code Constants Changed

### place.py
```python
# REMOVED
DEFAULT_COLOR = (1.0, 1.0, 1.0)  # White fill

# CHANGED
DEFAULT_BORDER_WIDTH = 2.0  →  DEFAULT_BORDER_WIDTH = 3.0
```

### transition.py
```python
# CHANGED
DEFAULT_BORDER_WIDTH = 1.0  →  DEFAULT_BORDER_WIDTH = 3.0
```

### arc.py
```python
# CHANGED (arrowhead angle)
arrow_angle = math.pi / 6  →  arrow_angle = math.pi / 5

# CHANGED (weight font)
cr.select_font_face("Sans", 0, 1)  →  cr.select_font_face("Arial", 0, 1)
cr.set_font_size(11)  →  cr.set_font_size(12)

# ADDED (weight background)
cr.rectangle(...)
cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
cr.fill()
```

### inhibitor_arc.py
```python
# CHANGED (method name)
def _draw_arrowhead(...)  →  def _render_arrowhead(...)

# CHANGED (marker style)
# Before: Simple stroke
cr.arc(...)
cr.stroke()

# After: White fill + colored ring
cr.arc(...)
cr.set_source_rgb(1.0, 1.0, 1.0)
cr.fill_preserve()
cr.set_source_rgb(*self.color)
cr.stroke()
```

## Rendering Method Changes

### Place.render()
```python
# BEFORE
cr.arc(screen_x, screen_y, self.radius, 0, 2 * math.pi)
cr.set_source_rgb(*self.fill_color)
cr.fill_preserve()
cr.set_source_rgb(*self.border_color)
cr.stroke()

# AFTER (hollow circles)
cr.arc(screen_x, screen_y, self.radius, 0, 2 * math.pi)
cr.set_source_rgb(*self.border_color)
cr.set_line_width(self.border_width)
cr.stroke()  # No fill!
```

### Arc._render_arrowhead()
```python
# BEFORE (filled triangle)
cr.move_to(x, y)
cr.line_to(left_x, left_y)
cr.line_to(right_x, right_y)
cr.close_path()
cr.fill()

# AFTER (two lines)
cr.move_to(x, y)
cr.line_to(left_x, left_y)
cr.stroke()
cr.move_to(x, y)
cr.line_to(right_x, right_y)
cr.stroke()
```

## Visual Checklist

When testing rendering, verify:

- [ ] **Places are hollow** - You should see through them to the background
- [ ] **Lines are thick** - 3.0px is clearly visible, not thin
- [ ] **Arrowheads are V-shaped** - Two lines meeting at tip, not filled
- [ ] **Weight has white box** - Text sits on semi-transparent white background
- [ ] **Tokens show as numbers** - "2" or "3", not individual dots
- [ ] **Inhibitor marker is white** - Circle has white interior with colored edge

## Common Issues

### Places still look filled?
- Check: `render()` should use `stroke()` only, not `fill_preserve()`
- Check: No `self.fill_color` assignment in `__init__()`

### Lines too thin?
- Check: All `DEFAULT_BORDER_WIDTH` and `DEFAULT_WIDTH` are 3.0

### Arrowheads still triangular?
- Check: `_render_arrowhead()` draws two separate `line_to()` + `stroke()` calls

### Weight text hard to read?
- Check: White background rectangle is drawn before text
- Check: Font is "Arial" 12pt Bold

### Inhibitor marker wrong?
- Check: Method name is `_render_arrowhead` (not `_draw_arrowhead`)
- Check: Uses `fill_preserve()` pattern

## Testing Command

```bash
cd /home/simao/projetos/shypn
python tests/test_legacy_rendering.py
```

Visual window will open showing all object types with correct rendering.
