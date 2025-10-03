"""
Legacy Rendering Analysis and Migration Plan
=============================================

## Key Findings from Legacy Renderer

### 1. Place Rendering (render_place)

**Legacy Approach:**
- **Hollow circles** (no fill, stroke only)
- **Line width: 3.0px** (thicker than current 2.0px)
- **Default color: Black border** `(0.0, 0.0, 0.0)`
- **Selection: Brighten color by +0.3** 
- **Hover: Brighten color by +0.15**
- **Token count rendering**: Centered text with Arial 14pt
- **Alpha transparency**: Supported via properties

**Current Implementation:**
- ✗ **White-filled circles** (not hollow!)
- ✗ **Line width: 2.0px** (thinner)
- ✓ Black border color
- ✗ No selection/hover states
- ✗ No token count rendering
- ✗ No alpha transparency

### 2. Transition Rendering (render_transition)

**Legacy Approach:**
- **Black fill** `(0.0, 0.0, 0.0)` + **colored border**
- **Line width: 3.0px** (or custom)
- **fill_preserve pattern**: Fill first, then stroke border
- **Selection**: Brighten border +0.3, width = 4.0px
- **Hover**: Brighten border +0.15
- **Timed transitions**: Visual feedback (green/orange/dashed)
- **Alpha transparency**: Supported

**Current Implementation:**
- ✓ Black fill
- ✗ **Line width: 1.0px** (too thin!)
- ✗ No fill_preserve pattern (may cause issues)
- ✗ No selection/hover states
- ✗ No timed transition feedback
- ✗ No alpha transparency

### 3. Arc Rendering (render_arc)

**Legacy Approach:**
- **Line width: 3.0px** (customizable)
- **Arrowhead: 15px length**, angle `π/5`
- **Two-line arrowhead**: Separate lines, not filled triangle
- **Inhibitor marker**: White-filled circle with colored ring, radius 6-12px
- **Parallel arc detection**: Curved arcs when opposite arc exists
- **Weight text**: Bold Arial 12pt with white background
- **Selection**: Brighten +0.4, double width
- **Hover**: Brighten +0.2, width * 1.4

**Current Implementation:**
- ✓ Line width: 3.0px (correct)
- ✗ **Arrowhead: Filled triangle** (not two lines!)
- ✗ **Arrowhead size: 10.0px** (smaller than legacy 15px)
- ✗ **Angle: π/6** (wider than legacy π/5)
- ✗ No inhibitor marker implementation
- ✗ No parallel arc detection
- ✗ No weight text rendering
- ✗ No selection/hover states

### 4. Helper Methods

**Legacy provides:**
- `get_element_color()`: Custom color support via properties dict
- `get_element_alpha()`: Transparency support
- `get_connection_point()`: Proper boundary intersection for circles and rectangles
- `render_arrowhead()`: Two-line arrowhead, not filled
- `render_inhibitor_marker()`: White-filled circle with colored ring
- `render_arc_weight()`: Weight text with background
- `render_tokens_count()`: Token count display with Arial font

**Current has:**
- ✗ No color customization
- ✗ No alpha transparency
- ✓ Basic `_get_boundary_point()` (similar to get_connection_point)
- ✗ Different arrowhead style (filled triangle)
- ✗ InhibitorArc exists but no marker rendering
- ✗ No weight rendering
- ✗ No token rendering

## Critical Differences

### Place: Hollow vs Filled

**Legacy:** Hollow circle (stroke only)
```python
ctx.arc(place.x, place.y, radius, 0, 2 * math.pi)
ctx.set_source_rgba(*border_color, alpha)
ctx.set_line_width(3.0)
ctx.stroke()  # Stroke only, no fill!
```

**Current:** Filled + stroked
```python
cr.arc(screen_x, screen_y, self.radius, 0, 2 * math.pi)
cr.set_source_rgb(*self.fill_color)  # White fill
cr.fill_preserve()
cr.set_source_rgb(*self.border_color)
cr.set_line_width(self.border_width)
cr.stroke()
```

**Fix:** Remove fill, use stroke only with 3.0px width

### Transition: fill_preserve Pattern

**Legacy:** Black fill + colored border
```python
ctx.rectangle(x, y, width, height)
ctx.set_source_rgba(0, 0, 0, alpha)  # Black
ctx.fill_preserve()  # Fill but keep path
ctx.set_source_rgba(*border_color, alpha)
ctx.set_line_width(3.0)
ctx.stroke()  # Stroke the preserved path
```

**Current:** Black fill + black border (no fill_preserve)
```python
cr.rectangle(x, y, self.width, self.height)
cr.set_source_rgb(*self.fill_color)
cr.fill()  # Fill destroys path!
cr.set_source_rgb(*self.border_color)
cr.set_line_width(1.0)
cr.stroke()  # May not work if path destroyed
```

**Fix:** Use fill_preserve, increase line width to 3.0px

### Arc: Arrowhead Style

**Legacy:** Two-line arrowhead
```python
arrow_length = 15
arrow_angle = math.pi / 5
# Calculate two wing points
ctx.set_line_width(2)
ctx.move_to(end_x, end_y)
ctx.line_to(arrow_x1, arrow_y1)  # Left wing
ctx.move_to(end_x, end_y)
ctx.line_to(arrow_x2, arrow_y2)  # Right wing
ctx.stroke()
```

**Current:** Filled triangle
```python
ARROW_SIZE = 15.0
angle = math.pi / 6
# Calculate three points
cr.move_to(tip_x, tip_y)
cr.line_to(left_x, left_y)
cr.line_to(right_x, right_y)
cr.close_path()
cr.fill()  # Filled triangle
```

**Fix:** Use two-line style or keep filled but match legacy size/angle

### Arc: Weight Text Rendering

**Legacy:** Comprehensive weight rendering
```python
def render_arc_weight(ctx, arc, start_x, start_y, end_x, end_y, ctrl_x=None, ctrl_y=None):
    if arc.weight <= 1:
        return
    
    # Set font
    ctx.select_font_face("Arial", FONT_SLANT_NORMAL, FONT_WEIGHT_BOLD)
    ctx.set_font_size(12)
    
    # Calculate position (midpoint + perpendicular offset)
    # ... positioning logic ...
    
    # Draw white background
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.8)
    ctx.rectangle(bg_x, bg_y, bg_width, bg_height)
    ctx.fill()
    
    # Draw text
    ctx.set_source_rgba(*color, alpha)
    ctx.move_to(text_x, text_y)
    ctx.show_text(weight_text)
```

**Current:** No weight rendering at all!

**Fix:** Add complete weight rendering method

## Migration Strategy

### Phase 1: Fix Critical Visual Issues
1. **Place**: Change to hollow (stroke only), width 3.0px
2. **Transition**: Use fill_preserve, width 3.0px  
3. **Arc**: Match arrowhead style (two-line or adjust filled)

### Phase 2: Add Missing Features
4. **Token rendering**: Add to Place
5. **Weight rendering**: Add to Arc
6. **InhibitorArc marker**: Implement white-filled circle

### Phase 3: Add Interactive States (Future)
7. Selection highlighting
8. Hover effects
9. Custom colors via properties
10. Alpha transparency

## Specific Code Changes Needed

### src/shypn/api/place.py

```python
# BEFORE (current - WRONG):
cr.arc(screen_x, screen_y, self.radius, 0, 2 * math.pi)
cr.set_source_rgb(*self.fill_color)  # White
cr.fill_preserve()
cr.set_source_rgb(*self.border_color)
cr.set_line_width(self.border_width)  # 2.0
cr.stroke()

# AFTER (legacy style - CORRECT):
cr.arc(screen_x, screen_y, self.radius, 0, 2 * math.pi)
cr.set_source_rgb(*self.border_color)  # Black
cr.set_line_width(3.0)  # Thicker
cr.stroke()  # Stroke only, no fill!

# THEN add token rendering
if self.tokens > 0:
    self._render_tokens(cr, screen_x, screen_y)
```

### src/shypn/api/transition.py

```python
# BEFORE (current - may have issues):
cr.rectangle(x, y, self.width, self.height)
cr.set_source_rgb(*self.fill_color)
cr.fill()  # Path destroyed!
cr.set_source_rgb(*self.border_color)
cr.set_line_width(1.0)  # Too thin
cr.stroke()

# AFTER (legacy style - CORRECT):
cr.rectangle(x, y, self.width, self.height)
cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)  # Black fill
cr.fill_preserve()  # Keep path!
cr.set_source_rgb(*self.border_color)  # Black border
cr.set_line_width(3.0)  # Thicker
cr.stroke()
```

### src/shypn/api/arc.py

```python
# BEFORE (current arrowhead):
ARROW_SIZE = 15.0
# Filled triangle with angle π/6

# AFTER (legacy style):
ARROW_LENGTH = 15  # Same
ARROW_ANGLE = math.pi / 5  # Narrower angle

def _render_arrowhead(self, cr, end_x, end_y, dx, dy):
    # Two-line arrowhead (legacy style)
    arrow_x1 = end_x - self.ARROW_LENGTH * (dx * math.cos(self.ARROW_ANGLE) + dy * math.sin(self.ARROW_ANGLE))
    arrow_y1 = end_y - self.ARROW_LENGTH * (dy * math.cos(self.ARROW_ANGLE) - dx * math.sin(self.ARROW_ANGLE))
    arrow_x2 = end_x - self.ARROW_LENGTH * (dx * math.cos(self.ARROW_ANGLE) - dy * math.sin(self.ARROW_ANGLE))
    arrow_y2 = end_y - self.ARROW_LENGTH * (dy * math.cos(self.ARROW_ANGLE) + dx * math.sin(self.ARROW_ANGLE))
    
    cr.set_line_width(2.0)
    cr.move_to(end_x, end_y)
    cr.line_to(arrow_x1, arrow_y1)
    cr.move_to(end_x, end_y)
    cr.line_to(arrow_x2, arrow_y2)
    cr.stroke()

# ADD weight rendering method:
def _render_weight(self, cr, start_x, start_y, end_x, end_y):
    if self.weight <= 1:
        return
    # ... implementation from legacy ...
```

### src/shypn/api/inhibitor_arc.py

```python
def _draw_arrowhead(self, cr, x1, y1, x2, y2):
    # Use legacy inhibitor marker rendering
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-6:
        return
    
    dx /= length
    dy /= length
    
    # White-filled circle with colored ring
    visible_radius = max(8, 6 * 1.5)
    
    # White background (hides line end)
    cr.set_source_rgb(1.0, 1.0, 1.0)
    cr.arc(x2, y2, visible_radius + 1, 0, 2 * math.pi)
    cr.fill()
    
    # Colored ring
    cr.set_source_rgb(*self.color)
    cr.set_line_width(max(2.5, visible_radius * 0.25))
    cr.arc(x2, y2, visible_radius, 0, 2 * math.pi)
    cr.stroke()
```

## Summary

**Hollow Places**: Most critical - current filled circles look wrong
**Thicker Lines**: 3.0px everywhere, not 2.0 or 1.0
**fill_preserve**: Essential for transitions
**Token Rendering**: Nice to have but not critical for arcs to show
**Weight Rendering**: Important for clarity
**Arrowhead Style**: Minor difference, either style works

**Priority:**
1. Fix Place (hollow, 3.0px)
2. Fix Transition (fill_preserve, 3.0px)
3. Fix Arc arrowhead size/angle
4. Add weight rendering
5. Add token rendering
6. Add InhibitorArc marker
"""
