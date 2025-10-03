# Legacy Grid and Zoom Analysis - Complete Relationship

## Overview

Comprehensive analysis of how zoom, objects, and grid scaling are related in the legacy ShyPN code.

**Date**: October 3, 2025  
**Discovery**: Legacy uses **TWO DIFFERENT GRID APPROACHES** in different versions!

---

## Critical Discovery: Two Grid Systems

### System 1: Device-Space Grid (validate_ui.py - Current Production)

**Location**: `legacy/shypnpy/interface/validate_ui.py` lines 5820-5970

**Key Insight**: Grid is drawn in **DEVICE SPACE** (screen coordinates), NOT world space!

#### Grid Drawing Approach

```python
def _on_draw_area(self, widget, cr):
    # Clear background
    cr.set_source_rgba(1,1,1,1)
    cr.rectangle(0,0,alloc_w,alloc_h)
    cr.fill()
    
    # ===== GRID IN DEVICE SPACE (before transform) =====
    # Calculate grid spacing based on DPI
    dpi = screen.get_resolution() or 96.0
    px_per_mm = dpi / 25.4
    base_minor = 1.0 * px_per_mm  # 1mm logical spacing
    major_every = 5
    
    # Convert world spacing to device spacing
    minor_spacing_world = base_minor
    minor_spacing_device = max(1, minor_spacing_world * scale)
    
    # Calculate phase shift for panning effect
    phase_x = (pan_x * scale) % minor_spacing_device
    phase_y = (pan_y * scale) % minor_spacing_device
    
    # Draw grid lines in device space
    for i in range(-1, lines_x):
        idx = base_index_x + i
        x_px = -phase_x + i * minor_spacing_device
        
        if idx % major_every == 0:
            cr.set_source_rgba(*major_rgba)  # Major line
            cr.set_line_width(1)
        else:
            cr.set_source_rgba(*minor_rgba)  # Minor line
            cr.set_line_width(0.5)
        
        cr.move_to(x_px + 0.5, 0)
        cr.line_to(x_px + 0.5, alloc_h)
        cr.stroke()
    
    # Similar for horizontal lines...
    
    # ===== OBJECTS IN WORLD SPACE (after transform) =====
    cr.save()
    cr.translate(pan_x * scale, pan_y * scale)
    cr.scale(scale, scale)
    
    # Draw objects in world coordinates
    self._draw_objects(cr, scale)
    
    cr.restore()
```

#### Key Characteristics

1. **Grid Base Spacing**: 1mm in physical units (DPI-based)
   - `px_per_mm = dpi / 25.4`
   - `base_minor = 1.0 * px_per_mm`

2. **Grid Scales with Zoom**:
   - `minor_spacing_device = minor_spacing_world * scale`
   - As zoom increases, grid spacing increases
   - Grid lines always drawn in device space

3. **Grid "Follows" Pan via Phase Shift**:
   - `phase_x = (pan_x * scale) % minor_spacing_device`
   - Grid doesn't actually move, it shifts phase to simulate movement
   - Creates illusion of infinite grid

4. **Major vs Minor Lines**:
   - Every 5th line is a major line (darker, 1px)
   - Minor lines are lighter (0.5px)
   - Major line pattern: `idx % 5 == 0`

5. **Grid Position Formula**:
   ```python
   base_index_x = int(math.floor(pan_x / minor_spacing_world))
   x_px = -phase_x + i * minor_spacing_device
   ```

---

### System 2: World-Space Grid (deprecated/shypn.py - Old Version)

**Location**: `legacy/shypnpy/deprecated/shypn.py` lines 10257-10287

#### Grid Drawing Approach

```python
def render_grid(self, ctx, widget):
    """Render grid lines on the drawing area, panned with canvas_offset"""
    allocation = widget.get_allocation()
    width = allocation.width
    height = allocation.height
    
    ctx.set_source_rgba(0.8, 0.8, 0.8, 0.5)
    ctx.set_line_width(1.0)
    
    # Calculate offset for grid lines
    offset_x = self.canvas_offset_x % self.grid_size
    offset_y = self.canvas_offset_y % self.grid_size
    
    # Draw vertical lines
    x = -offset_x
    while x <= width:
        ctx.move_to(x, 0)
        ctx.line_to(x, height)
        x += self.grid_size
    
    # Draw horizontal lines
    y = -offset_y
    while y <= height:
        ctx.move_to(0, y)
        ctx.line_to(width, y)
        y += self.grid_size
    
    ctx.stroke()
```

#### Key Characteristics

1. **Simple Fixed Spacing**: `self.grid_size` (probably pixel-based)
2. **Panned via Modulo**: `offset = canvas_offset % grid_size`
3. **Device Space**: Drawn before any transforms
4. **No Zoom Scaling**: Grid spacing doesn't change with zoom

---

## Production System Analysis (validate_ui.py)

### Grid-Zoom-Object Relationship

```
┌─────────────────────────────────────────────────────┐
│                  DEVICE SPACE                        │
│  ┌────────────────────────────────────────────┐    │
│  │        GRID (DPI-based, phase-shifted)     │    │
│  │   • Spacing = 1mm * zoom                   │    │
│  │   • Position = phase shift via pan         │    │
│  │   • Lines = 0.5px (minor), 1px (major)     │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │   WORLD SPACE (Cairo transform applied)     │    │
│  │                                              │    │
│  │   cr.translate(pan_x * scale, pan_y * scale) │    │
│  │   cr.scale(scale, scale)                     │    │
│  │                                              │    │
│  │   ┌──────────────────────────────────┐      │    │
│  │   │         OBJECTS                   │      │    │
│  │   │   • Positions in world coords     │      │    │
│  │   │   • Scaled automatically          │      │    │
│  │   │   • Line widths compensated       │      │    │
│  │   └──────────────────────────────────┘      │    │
│  │                                              │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Mathematical Relationship

#### Grid Spacing Calculation

```python
# Base spacing (physical units)
dpi = 96.0  # Screen DPI
px_per_mm = dpi / 25.4  # ≈ 3.78 pixels per mm
base_minor = 1.0 * px_per_mm  # ≈ 3.78px (1mm in logical space)

# At different zoom levels:
# zoom = 1.0:  minor_spacing_device = 3.78px
# zoom = 2.0:  minor_spacing_device = 7.56px  
# zoom = 0.5:  minor_spacing_device = 1.89px
```

#### Phase Shift for Pan Illusion

```python
# Pan creates phase shift in grid
pan_x = 100.0  # World coordinate
scale = 2.0
minor_spacing_device = base_minor * scale

phase_x = (pan_x * scale) % minor_spacing_device
# = (100 * 2.0) % 7.56
# = 200 % 7.56
# = 4.56px

# Grid line positions:
x_px = -phase_x + i * minor_spacing_device
# = -4.56 + 0 * 7.56 = -4.56px  (off-screen left)
# = -4.56 + 1 * 7.56 = 3.0px
# = -4.56 + 2 * 7.56 = 10.56px
# = -4.56 + 3 * 7.56 = 18.12px
# ...
```

#### Major Line Pattern

```python
# Major line every 5th line
base_index_x = int(math.floor(pan_x / minor_spacing_world))
# = int(math.floor(100.0 / 3.78))
# = int(26.46)
# = 26

# For grid line i:
idx = base_index_x + i
# i=0: idx=26, 26%5=1 → minor
# i=1: idx=27, 27%5=2 → minor
# i=2: idx=28, 28%5=3 → minor
# i=3: idx=29, 29%5=4 → minor
# i=4: idx=30, 30%5=0 → MAJOR!
```

---

## Comparison: Legacy vs Current Implementation

### Legacy System (validate_ui.py)

| Aspect | Implementation |
|--------|---------------|
| **Grid Space** | Device space (before Cairo transform) |
| **Grid Spacing** | DPI-based (1mm physical), scales with zoom |
| **Grid Movement** | Phase shift simulation (modulo arithmetic) |
| **Major Lines** | Every 5th line, darker color |
| **Line Widths** | 0.5px (minor), 1px (major) - constant |
| **Object Space** | World space (after Cairo transform) |
| **Relationship** | Grid "attached" to screen, objects move behind it |

### Current Implementation (BEFORE Analysis)

| Aspect | Implementation |
|--------|---------------|
| **Grid Space** | World space (inside Cairo transform) |
| **Grid Spacing** | Fixed (50px), adaptive levels |
| **Grid Movement** | Actual movement with pan |
| **Major Lines** | None (all lines equal) |
| **Line Widths** | 1px compensated - constant |
| **Object Space** | World space (same as grid) |
| **Relationship** | Grid moves with objects |

---

## Key Differences

### 1. Grid Coordinate System

**Legacy**: Grid in device space, objects in world space  
**Current**: Grid AND objects in world space

**Impact**: 
- Legacy: Grid visually stable, objects pan/zoom behind it
- Current: Grid and objects pan/zoom together

### 2. Grid Spacing Source

**Legacy**: Physical units (1mm based on screen DPI)  
**Current**: Arbitrary units (50px)

**Impact**:
- Legacy: Consistent physical size across displays
- Current: Pixel-based, varies by display

### 3. Grid Movement

**Legacy**: Phase shift creates panning illusion  
**Current**: Actual coordinate transformation

**Impact**:
- Legacy: More complex math, but stable visual reference
- Current: Simpler, but grid moves with content

### 4. Major/Minor Lines

**Legacy**: Two-tier system (major every 5th line)  
**Current**: Single tier (all lines equal)

**Impact**:
- Legacy: Better visual hierarchy
- Current: Simpler, but less structure

---

## Which Approach is Correct?

### Production Legacy Uses Device-Space Grid

The **validate_ui.py** (current production) uses:
- ✅ Grid in device space (stable reference)
- ✅ DPI-based spacing (physical units)
- ✅ Phase shift for pan illusion
- ✅ Major/minor line distinction

### Why Device-Space Grid?

1. **Visual Stability**: Grid provides stable reference frame
2. **Performance**: Grid doesn't need to be recalculated on pan
3. **Physical Consistency**: 1mm grid regardless of zoom
4. **Professional Feel**: Engineering/CAD-style behavior

### Why World-Space Grid?

1. **Conceptual Simplicity**: Grid is "in the world"
2. **Code Simplicity**: No phase shift calculations
3. **Unified Space**: Grid and objects in same coordinate system

---

## Recommendation

Based on the legacy analysis, there are **TWO VALID APPROACHES**:

### Option A: Device-Space Grid (Legacy Production Style)

**Pros**:
- ✅ Matches production legacy behavior
- ✅ Grid provides stable visual reference
- ✅ DPI-based spacing (professional)
- ✅ Major/minor lines (better hierarchy)

**Cons**:
- ❌ More complex implementation
- ❌ Phase shift math required
- ❌ Grid and objects in different spaces

**Use Case**: Professional CAD/engineering-style application

### Option B: World-Space Grid (Our Current Style)

**Pros**:
- ✅ Simpler implementation
- ✅ Grid and objects unified
- ✅ Natural scaling behavior
- ✅ Easier to understand

**Cons**:
- ❌ Doesn't match production legacy
- ❌ Grid moves with objects (less stable)
- ❌ No major/minor distinction

**Use Case**: Simpler editing application, diagram tools

---

## Implementation Strategy

### Current Situation

We implemented **Option B** (world-space grid) assuming the legacy used world-space. Now we know the legacy uses **Option A** (device-space grid).

### Decision Point

**Question**: Should we match the production legacy exactly, or keep our simpler approach?

### Arguments for Each

#### Keep World-Space Grid (Our Current)

**Rationale**:
- Our implementation is correct and working
- Simpler code is easier to maintain
- Grid scaling with objects is intuitive
- User requested "grid must scale with objects" ✅

**Evidence**: User said "grid must scale in conjunction with net objects" - this matches our world-space approach!

#### Switch to Device-Space Grid (Legacy Match)

**Rationale**:
- Matches production legacy exactly
- More professional behavior
- DPI-based spacing (physical units)
- Major/minor lines improve usability

**Evidence**: Legacy production code uses this approach.

---

## User Request Analysis

**User said**: "grid must scale in conjunction with net objects"

**Interpretation**:
- "scale in conjunction" = scale together
- "with net objects" = same scaling behavior

**This matches**: World-space grid (our current implementation) ✅

**Legacy production**: Device-space grid DOES scale with zoom, but provides stable reference frame.

### Subtle Difference

**World-Space Grid**: Grid spacing scales, grid moves with pan  
**Device-Space Grid**: Grid spacing scales, grid phase-shifts with pan

Both scale with zoom, but behave differently on pan!

---

## Recommended Action

### Short Term: Keep World-Space Grid

**Rationale**:
1. User explicitly requested grid to "scale in conjunction with objects" ✅
2. Current implementation works correctly
3. Simpler code is easier to maintain
4. Grid scaling with zoom is implemented ✅

### Enhancements to Current System

1. **Add DPI-Based Spacing** (optional)
   ```python
   dpi = screen.get_resolution() or 96.0
   px_per_mm = dpi / 25.4
   BASE_GRID_SPACING = 5.0 * px_per_mm  # 5mm instead of 50px
   ```

2. **Add Major/Minor Lines** (recommended)
   ```python
   MAJOR_EVERY = 5
   
   if (grid_index % MAJOR_EVERY) == 0:
       cr.set_source_rgba(0.65, 0.65, 0.68, 1.0)  # Major
       cr.set_line_width(1.0 / zoom)
   else:
       cr.set_source_rgba(0.85, 0.85, 0.88, 1.0)  # Minor
       cr.set_line_width(0.5 / zoom)
   ```

3. **Improve Adaptive Spacing** (current is good)
   - Keep existing adaptive spacing logic
   - Maybe adjust thresholds based on DPI

### Long Term: Consider Device-Space Grid

If users request more CAD-like behavior:
- Grid as stable reference frame
- Phase-shift pan illusion
- DPI-based physical spacing

---

## Code Comparison

### Legacy Device-Space Grid

```python
# DEVICE SPACE GRID (legacy production)
def _on_draw(self, widget, cr):
    # Background
    cr.set_source_rgba(1,1,1,1)
    cr.paint()
    
    # Grid in device space
    dpi = screen.get_resolution() or 96.0
    px_per_mm = dpi / 25.4
    base_minor = 1.0 * px_per_mm
    minor_spacing_world = base_minor
    minor_spacing_device = max(1, minor_spacing_world * scale)
    phase_x = (pan_x * scale) % minor_spacing_device
    
    for i in range(-1, lines_x):
        idx = base_index_x + i
        x_px = -phase_x + i * minor_spacing_device
        
        if idx % 5 == 0:
            cr.set_source_rgba(0.65, 0.65, 0.68, 1.0)
            cr.set_line_width(1)
        else:
            cr.set_source_rgba(0.85, 0.85, 0.88, 1.0)
            cr.set_line_width(0.5)
        
        cr.move_to(x_px + 0.5, 0)
        cr.line_to(x_px + 0.5, alloc_h)
        cr.stroke()
    
    # Objects in world space
    cr.save()
    cr.translate(pan_x * scale, pan_y * scale)
    cr.scale(scale, scale)
    draw_objects(cr, scale)
    cr.restore()
```

### Current World-Space Grid

```python
# WORLD SPACE GRID (our current)
def _on_draw(self, drawing_area, cr, width, height, manager):
    # Background
    cr.set_source_rgb(1.0, 1.0, 1.0)
    cr.paint()
    
    # World space transform
    cr.save()
    cr.translate(manager.pan_x * manager.zoom, manager.pan_y * manager.zoom)
    cr.scale(manager.zoom, manager.zoom)
    
    # Grid in world space
    manager.draw_grid(cr)
    
    # Objects in world space
    for obj in manager.get_all_objects():
        obj.render(cr, zoom=manager.zoom)
    
    cr.restore()

def draw_grid(self, cr):
    grid_spacing = self.get_grid_spacing()
    min_x, min_y, max_x, max_y = self.get_visible_bounds()
    
    start_x = math.floor(min_x / grid_spacing) * grid_spacing
    start_y = math.floor(min_y / grid_spacing) * grid_spacing
    
    cr.set_source_rgba(0.7, 0.7, 0.7, 0.6)
    cr.set_line_width(1.0 / self.zoom)
    
    # Vertical lines
    x = start_x
    while x <= max_x:
        cr.move_to(x, min_y)
        cr.line_to(x, max_y)
        x += grid_spacing
    
    # Horizontal lines
    y = start_y
    while y <= max_y:
        cr.move_to(min_x, y)
        cr.line_to(max_x, y)
        y += grid_spacing
    
    cr.stroke()
```

---

## Summary

### Key Findings

1. **Legacy uses DEVICE-SPACE grid** (not world-space)
2. **Grid spacing is DPI-based** (1mm physical units)
3. **Grid has major/minor lines** (every 5th is major)
4. **Grid uses phase shift** for pan illusion
5. **Objects use world-space** (separate from grid)

### Current Implementation

1. **We use WORLD-SPACE grid** ✅
2. **Grid scales with zoom** ✅
3. **Grid moves with pan** ✅
4. **No major/minor distinction** ⚠️
5. **Pixel-based spacing** (not DPI-based) ⚠️

### User Request Satisfied

**User**: "grid must scale in conjunction with net objects"  
**Our Implementation**: Grid and objects both in world space, scale together ✅

**Verdict**: ✅ **CORRECT** - Our world-space grid matches user intent!

---

## Next Steps

### Immediate (Recommended)

1. ✅ **Keep world-space grid** - matches user request
2. ⚠️ **Add major/minor lines** - improves usability
3. ⚠️ **Add DPI-based spacing** - professional appearance

### Optional (Advanced)

4. Add toggle for device-space vs world-space grid
5. Add grid style options (CAD-style, simple, etc.)
6. Implement snap-to-grid functionality

---

## Conclusion

Our **world-space grid implementation is CORRECT** for the user's stated requirement: "grid must scale in conjunction with net objects."

The legacy production code uses a more sophisticated device-space grid with phase shifting, but that's a **different design choice**, not a requirement.

**Recommendation**: Keep our current world-space grid, optionally enhance with major/minor lines and DPI-based spacing.
