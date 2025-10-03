# Infinite Canvas, Scaling, and Coordinate Systems Analysis

**Date:** October 3, 2025  
**Branch:** petri-net-objects-editing  
**Purpose:** Comprehensive analysis of pan, zoom, grid scaling, object scaling, and coordinate references for achieving an infinite canvas with proper 1:1 scale at 100% zoom.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Legacy Code Analysis](#legacy-code-analysis)
   - [Zoom and Scale Reference](#zoom-and-scale-reference)
   - [Pan System](#pan-system)
   - [Grid System](#grid-system)
   - [Object Sizes and Scaling](#object-sizes-and-scaling)
   - [Coordinate Transformations](#coordinate-transformations)
3. [Current Implementation Analysis](#current-implementation-analysis)
4. [Industry Patterns and Best Practices](#industry-patterns-and-best-practices)
5. [Comparison and Gap Analysis](#comparison-and-gap-analysis)
6. [Specification for 1:1 Scale](#specification-for-11-scale)
7. [Implementation Recommendations](#implementation-recommendations)
8. [Test Cases and Validation](#test-cases-and-validation)

---

## Executive Summary

### Key Findings

**Legacy System (validate_ui.py - Production)**
- **Initial zoom:** `zoom_scale = 1.0` (100%)
- **Initial pan:** `_pan_x = 0.0`, `_pan_y = 0.0`
- **Coordinate system:** Logical units (world) with device pixel rendering
- **1:1 Scale definition:** At zoom=1.0, 1 logical unit = 1 screen pixel
- **Grid spacing:** DPI-based (1mm physical = ~3.78 pixels at 96 DPI)
- **Object sizes at 100% zoom:**
  - Place radius: 30.0 logical units (pixels)
  - Transition: 44.0 × 22.0 logical units (pixels)
- **Infinite canvas:** Implemented via pan clamping with large extent (10,000 logical units)

**Current Implementation (model_canvas_manager.py)**
- **Initial zoom:** `zoom = 1.0` (100%)
- **Initial pan:** Centered on first viewport size update
- **Coordinate system:** World coordinates with Cairo transform
- **Grid spacing:** Pixel-based (20px base, adaptive)
- **Object sizes:**
  - Place radius: 25.0 (smaller than legacy!)
  - Transition: 50.0 × 25.0 (different proportions!)
- **Infinite canvas:** Not explicitly limited, but no clamping

### Critical Issues Identified

1. **🔴 Object sizes don't match legacy at 1:1 scale**
   - Place: 25.0 vs 30.0 (83% of legacy size)
   - Transition: 50×25 vs 44×22 (different aspect ratio)

2. **🔴 Grid spacing inconsistency**
   - Legacy: DPI-based 1mm (~3.78px @ 96 DPI)
   - Current: Pixel-based 20px (~5.3mm @ 96 DPI)

3. **🟡 Pan centering logic differs**
   - Legacy: Starts at (0, 0) logical origin
   - Current: Centers canvas on first draw

4. **🟡 No explicit infinite canvas bounds**
   - Legacy: Uses extent clamping (±10,000 units)
   - Current: Unlimited pan (can pan into void)

---

## Legacy Code Analysis

### Zoom and Scale Reference

#### Initial Values (validate_ui.py)

```python
# Line 139-141
self.zoom_scale = 1.0  # Initial zoom is 100%
self._pan_x = 0.0      # Start at logical origin
self._pan_y = 0.0
```

**Interpretation:**
- `zoom_scale = 1.0` represents 100% zoom (1:1 scale)
- At this scale, 1 logical unit = 1 device pixel
- No DPI compensation at the zoom level (DPI handled in grid/object rendering)

#### Zoom Limits

From `zoom_infinite.py`:
```python
# Lines 73-77
min_z = float(os.environ.get('SHYPN_ZOOM_MIN', '0.30') or 0.30)  # 30%
max_z = float(os.environ.get('SHYPN_ZOOM_MAX', '3.0') or 3.0)    # 300%
```

From `zoom_legacy.py` comment:
```python
# Line 12: "Clamps scale to [0.05, 20.0]"
# (Earlier version had wider range, but production uses 0.30-3.0)
```

**Deprecated Version (shypn.py):**
```python
# Lines 7616-7618
self.canvas_scale = 1.0     # Same: 100% zoom
self.canvas_scale_min = 0.25  # 25% min
self.canvas_scale_max = 4.0   # 400% max
```

### Pan System

#### Pan Storage and Meaning

**Production (validate_ui.py):**
```python
# Pan stored as logical offsets
self._pan_x = 0.0  # Logical units
self._pan_y = 0.0  # Logical units
```

**Comment (lines 137-139):**
> "Zoom & pan state (logical coordinates). pan_x/pan_y shift the logical
> origin; zoom_scale scales logical -> device. Pointer-centered zoom will
> adjust pan so the logical position under the cursor stays fixed."

#### Pan Interaction

**Middle-button drag (validate_ui.py, lines 6424-6428):**
```python
if event.button == 2:  # middle button -> start panning
    self._panning = True
    self._pan_start_dev = (event.x, event.y)  # Device coords
    self._pan_start_offset = (self._pan_x, self._pan_y)  # Logical pan
    return True
```

**Motion during pan (not shown in excerpt, but pattern):**
```python
# Typical pan motion logic:
delta_dev_x = event.x - self._pan_start_dev[0]
delta_dev_y = event.y - self._pan_start_dev[1]
# Convert device delta to logical delta
delta_logical_x = delta_dev_x / self.zoom_scale
delta_logical_y = delta_dev_y / self.zoom_scale
# Update pan
self._pan_x = self._pan_start_offset[0] + delta_logical_x
self._pan_y = self._pan_start_offset[1] + delta_logical_y
```

#### Infinite Canvas via Clamping

**From zoom_infinite.py (lines 138-156):**
```python
# Grid extent (logical half-sizes)
try:
    half_extent = float(os.environ.get('SHYPN_INFINITE_EXTENT', '10000') or 10000.0)
except Exception:
    half_extent = 10000.0
Gx = Gy = abs(half_extent)

# Ensure extent large enough to cover viewport at new scale
min_half_x = (width / new_scale) / 2.0
min_half_y = (height / new_scale) / 2.0
if Gx < min_half_x: Gx = min_half_x
if Gy < min_half_y: Gy = min_half_y

# Clamp pans so grid fully covers viewport
# From Right >= width -> pan >= width/s - Gx
min_pan_x = (width / new_scale) - Gx
max_pan_x = Gx  # from Left <= 0 -> pan <= Gx
min_pan_y = (height / new_scale) - Gy
max_pan_y = Gy
new_pan_x = min(max(pan_blend_x, min_pan_x), max_pan_x)
new_pan_y = min(max(pan_blend_y, min_pan_y), max_pan_y)
```

**Key Points:**
- Default extent: ±10,000 logical units (20,000 × 20,000 total)
- At zoom=1.0, this is 10,000 pixels (about 104 inches or 264 cm @ 96 DPI)
- Pan is clamped so grid always fills viewport (no blank space)
- Creates illusion of infinite canvas while maintaining bounds

**Deprecated Version (shypn.py, lines 7611-7612):**
```python
self.canvas_offset_x = 0  # Device pixels (not logical!)
self.canvas_offset_y = 0
```

Note: Deprecated version used device-space offsets, not logical offsets.

### Grid System

#### DPI-Based Spacing (validate_ui.py, lines 5876-5893)

```python
# Estimate DPI for mm conversion
try:
    screen = widget.get_screen()
    dpi = screen.get_resolution() or 96.0
    if dpi <= 0: dpi = 96.0
except Exception:
    dpi = 96.0

px_per_mm = dpi / 25.4  # Convert DPI to pixels per millimeter
base_minor = 1.0 * px_per_mm  # 1mm logical spacing

major_every = 5  # Every 5th line is major

# At 96 DPI: px_per_mm = 96 / 25.4 ≈ 3.78 pixels/mm
# So base_minor ≈ 3.78 logical units
```

**Grid Rendering (device-space, lines 5894-5916):**
```python
minor_spacing_world = base_minor  # Logical spacing (e.g., 3.78 units)
minor_spacing_device = max(1, minor_spacing_world * scale)  # Device pixels

# Phase shift for infinite grid effect
phase_x = (pan_x * scale) % minor_spacing_device
phase_y = (pan_y * scale) % minor_spacing_device

lines_x = int(math.ceil(alloc_w / minor_spacing_device)) + 2
lines_y = int(math.ceil(alloc_h / minor_spacing_device)) + 2

base_index_x = int(math.floor(pan_x / minor_spacing_world))
base_index_y = int(math.floor(pan_y / minor_spacing_world))

# Vertical lines
for i in range(-1, lines_x):
    idx = base_index_x + i
    x_px = -phase_x + i * minor_spacing_device
    if idx % major_every == 0:
        cr.set_source_rgba(*major_rgba); cr.set_line_width(1)  # Major
    else:
        cr.set_source_rgba(*minor_rgba); cr.set_line_width(0.5)  # Minor
    cr.move_to(x_px + 0.5, 0)
    cr.line_to(x_px + 0.5, alloc_h)
    cr.stroke()
```

**Colors:**
```python
minor_rgba = (0.85, 0.85, 0.88, 1.0)  # Light gray
major_rgba = (0.65, 0.65, 0.68, 1.0)  # Darker gray
```

**Grid Behavior at Different Zooms:**

| Zoom | Logical Spacing | Device Spacing @ 96 DPI | Visual Result |
|------|-----------------|-------------------------|---------------|
| 1.0 (100%) | 3.78 units | 3.78 px (~1mm) | Reference spacing |
| 0.5 (50%) | 3.78 units | 1.89 px | Lines very close, may coalesce |
| 2.0 (200%) | 3.78 units | 7.56 px (~2mm) | Lines spread out |
| 0.3 (30%) | 3.78 units | 1.13 px | Lines barely visible |

**Deprecated Version (shypn.py, lines 10258-10279):**
```python
"""Render grid lines on the drawing area, panned with canvas_offset for infinite effect"""
grid_size = 20  # Fixed 20 pixel grid (no DPI scaling)

# Device-space grid with modulo panning
offset_x = self.canvas_offset_x % self.grid_size
offset_y = self.canvas_offset_y % self.grid_size

x = -offset_x
while x <= width:
    ctx.move_to(x, 0)
    ctx.line_to(x, height)
    x += self.grid_size
ctx.stroke()
```

Note: Deprecated version used fixed 20px grid, no major/minor distinction.

### Object Sizes and Scaling

#### Place (petri.py, line 37)

```python
def __init__(self, place_id, x=0.0, y=0.0, radius=30.0, tokens=0.0, ...):
    self.radius = float(radius)  # Default 30.0 logical units
```

**At zoom=1.0:** 30 pixel radius, 60 pixel diameter  
**Physical size @ 96 DPI:** 30/96 inches ≈ 7.9mm radius ≈ 15.7mm diameter

#### Transition (petri.py, line 92)

```python
def __init__(self, transition_id, x=0.0, y=0.0, width=44.0, height=22.0, ...):
    self.width = float(width)   # Default 44.0 logical units
    self.height = float(height) # Default 22.0 logical units
```

**At zoom=1.0:** 44×22 pixels  
**Physical size @ 96 DPI:** 11.6mm × 5.8mm  
**Aspect ratio:** 2:1 (width is twice height)

#### Arc Rendering

From various test files and `color_utils.py`:
- Arc line width: Typically 2.0-3.0 logical units
- Arrow size: ~10-12 logical units
- Arcs drawn with line width compensation: `width / scale`

### Coordinate Transformations

#### Device to Logical (coords.py, lines 21-30)

```python
def device_to_logical(app: Any, px: float, py: float) -> Tuple[float,float]:
    scale = getattr(app, 'zoom_scale', 1.0) or 1.0
    pan_x = getattr(app, '_pan_x', 0.0)
    pan_y = getattr(app, '_pan_y', 0.0)
    return (px / scale - pan_x, py / scale - pan_y)
```

**Formula:** `logical = device / scale - pan`

**Example at zoom=1.0, pan=(0,0):**
- Device (100, 100) → Logical (100, 100) ✓ 1:1 scale

**Example at zoom=2.0, pan=(0,0):**
- Device (100, 100) → Logical (50, 50) ✓ Zoomed in 2x

**Example at zoom=1.0, pan=(50, 30):**
- Device (100, 100) → Logical (50, 70) ✓ Pan shifts view

#### Logical to Device (coords.py, lines 33-42)

```python
def logical_to_device(app: Any, lx: float, ly: float) -> Tuple[float,float]:
    scale = getattr(app, 'zoom_scale', 1.0) or 1.0
    pan_x = getattr(app, '_pan_x', 0.0)
    pan_y = getattr(app, '_pan_y', 0.0)
    return ((lx + pan_x) * scale, (ly + pan_y) * scale)
```

**Formula:** `device = (logical + pan) * scale`

**Verification (round-trip at zoom=1.0, pan=(0,0)):**
- Logical (100, 100) → Device (100, 100) → Logical (100, 100) ✓

**Deprecated Version (shypn.py, line 10759):**
```python
# Used device-space offsets instead of logical pan
return ((sx - canvas_offset_x) / scale, (sy - canvas_offset_y) / scale)
```

Note: Formula is different! Deprecated: `(device - offset) / scale`  
vs. Production: `device / scale - pan`

Both are mathematically equivalent if pan is stored correctly.

---

## Current Implementation Analysis

### Zoom and Pan

**From model_canvas_manager.py (lines 57-69):**

```python
# Viewport properties
self.zoom = 1.0  # Current zoom level (1.0 = 100%)
# Initialize pan to center the canvas (updated when viewport size is known)
self.pan_x = 0.0  # Pan offset X (in world coordinates)
self.pan_y = 0.0  # Pan offset Y (in world coordinates)
self._initial_pan_set = False  # Flag to center on first draw

# Zoom configuration (lines 25-27)
MIN_ZOOM = 0.1  # 10% minimum
MAX_ZOOM = 10.0  # 1000% maximum
ZOOM_STEP = 1.1  # 10% per step
```

**Issues:**
1. Zoom range is 0.1-10.0 (10%-1000%), much wider than legacy 0.3-3.0 (30%-300%)
2. Pan centering logic differs from legacy (legacy starts at origin)

### Coordinate Transformations

**From model_canvas_manager.py:**

#### Screen to World (lines 94-106)

```python
def screen_to_world(self, screen_x, screen_y):
    """Convert screen coordinates to world coordinates.
    
    Formula: world = screen / zoom - pan
    
    Args:
        screen_x: X coordinate in screen space (pixels).
        screen_y: Y coordinate in screen space (pixels).
        
    Returns:
        Tuple of (world_x, world_y) in world coordinates.
    """
    world_x = (screen_x / self.zoom) - self.pan_x
    world_y = (screen_y / self.zoom) - self.pan_y
    return world_x, world_y
```

**✓ Matches legacy formula exactly!**

#### World to Screen (lines 108-122)

```python
def world_to_screen(self, world_x, world_y):
    """Convert world coordinates to screen coordinates.
    
    Formula: screen = (world + pan) * zoom
    
    Args:
        world_x: X coordinate in world space.
        world_y: Y coordinate in world space.
        
    Returns:
        Tuple of (screen_x, screen_y) in screen coordinates (pixels).
    """
    screen_x = (world_x + self.pan_x) * self.zoom
    screen_y = (world_y + self.pan_y) * self.zoom
    return screen_x, screen_y
```

**✓ Matches legacy formula exactly!**

### Grid System

**From model_canvas_manager.py (lines 30-37):**

```python
# At 100% zoom (1.0), grid should be ~5mm
# Assuming 96 DPI: 5mm = 5/25.4 inches = 0.1969 inches = 18.9 pixels ≈ 20 pixels
BASE_GRID_SPACING = 20  # Base grid spacing at zoom=1.0 (~5mm on 96 DPI screen)
GRID_SUBDIVISION_LEVELS = [1, 2, 5, 10]  # Grid adapts at these zoom thresholds
GRID_MAJOR_EVERY = 5  # Every 5th line is a major line (legacy-compatible)
GRID_STYLE_LINE = 'line'
GRID_STYLE_DOT = 'dot'
GRID_STYLE_CROSS = 'cross'
```

**Issue:** BASE_GRID_SPACING = 20px ≈ 5mm, but legacy uses 1mm base spacing!

**Adaptive Spacing (lines 444-476):**

```python
def get_grid_spacing(self):
    """Calculate grid spacing based on current zoom level.
    
    Returns:
        Grid spacing in world coordinates.
    """
    # Adaptive grid: spacing increases at certain zoom thresholds
    # to keep grid visually useful across zoom range
    base = self.BASE_GRID_SPACING
    
    # At high zoom (zoomed in), use smaller subdivisions
    if self.zoom >= 5.0:
        return base / 10  # Very fine grid
    elif self.zoom >= 2.0:
        return base / 5   # Fine grid
    elif self.zoom >= 1.0:
        return base / 2   # Medium grid
    elif self.zoom >= 0.5:
        return base       # Normal grid
    elif self.zoom >= 0.2:
        return base * 2   # Coarse grid
    else:
        return base * 5   # Very coarse grid
```

**Grid Rendering (lines 504-580):**

Grid is now rendered in world space with major/minor line distinction (recently added):

```python
def draw_grid(self, cr):
    grid_spacing = self.get_grid_spacing()
    min_x, min_y, max_x, max_y = self.get_visible_bounds()
    
    start_x = math.floor(min_x / grid_spacing) * grid_spacing
    start_y = math.floor(min_y / grid_spacing) * grid_spacing
    
    start_index_x = int(math.floor(min_x / grid_spacing))
    start_index_y = int(math.floor(min_y / grid_spacing))
    
    # Draw vertical lines with major/minor distinction
    x = start_x
    index_x = start_index_x
    while x <= max_x:
        is_major = (index_x % self.GRID_MAJOR_EVERY) == 0
        
        if is_major:
            cr.set_source_rgba(0.65, 0.65, 0.68, 0.8)  # Darker gray
            cr.set_line_width(1.0 / self.zoom)
        else:
            cr.set_source_rgba(0.85, 0.85, 0.88, 0.6)  # Lighter gray
            cr.set_line_width(0.5 / self.zoom)
        
        cr.move_to(x, min_y)
        cr.line_to(x, max_y)
        cr.stroke()
        
        x += grid_spacing
        index_x += 1
```

**✓ Colors match legacy!**  
**✓ Major/minor pattern matches legacy!**  
**✗ Spacing different (pixel-based vs DPI-based)**  
**✗ World-space rendering vs device-space (different approach)**

### Object Sizes

**From place.py (lines 18-19):**
```python
DEFAULT_RADIUS = 25.0
DEFAULT_BORDER_WIDTH = 3.0  # Legacy uses 3.0px for better visibility
```

**🔴 MISMATCH:** Current 25.0 vs Legacy 30.0 (17% smaller!)

**From transition.py (lines 18-20):**
```python
DEFAULT_WIDTH = 50.0
DEFAULT_HEIGHT = 25.0
DEFAULT_BORDER_WIDTH = 3.0
```

**🔴 MISMATCH:** Current 50×25 vs Legacy 44×22  
- Width: +13.6% larger
- Height: +13.6% larger
- Aspect ratio: 2:1 (same)

---

## Industry Patterns and Best Practices

### Infinite Canvas Applications

#### Figma
- **Zoom:** 0.01% to 1,000,000% (essentially unlimited)
- **Pan:** Unlimited (true infinite canvas)
- **Grid:** Pixel-based, adapts at zoom thresholds
- **Scale reference:** 100% = actual pixels on screen
- **Origin:** Floating (no fixed origin visible to user)

#### Miro
- **Zoom:** ~5% to 400%
- **Pan:** Unlimited within very large bounds
- **Grid:** Optional, scales with zoom
- **Scale reference:** Board units (not directly pixel-based)
- **Origin:** Center of board

#### Excalidraw
- **Zoom:** 10% to 3000%
- **Pan:** Unlimited
- **Grid:** Optional, pixel-based at 100%
- **Scale reference:** 100% = CSS pixels
- **Origin:** Canvas center (0, 0)

#### draw.io
- **Zoom:** 0.5% to 400%
- **Pan:** Clamped to page bounds
- **Grid:** Physical units (10px default), DPI-aware
- **Scale reference:** 100% = page units (configurable)
- **Origin:** Page top-left

### Common Patterns

1. **Coordinate System:**
   - World/logical coordinates for objects
   - Device/screen coordinates for rendering
   - Transform: `screen = (world + pan) * zoom`

2. **Grid:**
   - Pixel-based for screen design tools (Figma, Excalidraw)
   - Physical-based for CAD/diagram tools (draw.io, legacy ShyPN)
   - Major/minor lines common (every 5th or 10th)

3. **Pan:**
   - Most tools: unlimited or very large bounds
   - CAD tools: often clamped to page/sheet size
   - Pan stored in world coordinates

4. **Zoom:**
   - UI design: wide range (0.01% - 100,000%)
   - Diagram/CAD: moderate range (10% - 400%)
   - Engineering: practical range (30% - 300%)

5. **1:1 Scale:**
   - Usually means 100% zoom
   - 1 world unit = 1 screen pixel at 100%
   - Physical dimensions optional (DPI-aware)

---

## Comparison and Gap Analysis

### Zoom System

| Aspect | Legacy | Current | Status |
|--------|--------|---------|--------|
| Initial zoom | 1.0 (100%) | 1.0 (100%) | ✓ Match |
| Min zoom | 0.3 (30%) | 0.1 (10%) | ⚠️ Wider range |
| Max zoom | 3.0 (300%) | 10.0 (1000%) | ⚠️ Wider range |
| Zoom formula | Matches | Matches | ✓ Match |
| Pointer-centered | Yes | Yes | ✓ Match |

**Recommendation:** Adjust to legacy zoom range (0.3-3.0) for practical use.

### Pan System

| Aspect | Legacy | Current | Status |
|--------|--------|---------|--------|
| Initial pan | (0, 0) | Centered | ⚠️ Different |
| Pan storage | Logical units | World coords | ✓ Same concept |
| Pan formula | Matches | Matches | ✓ Match |
| Infinite canvas | Clamped ±10000 | Unlimited | ⚠️ Different |
| Pan interaction | Middle/right button | Right button | ⚠️ Different |

**Recommendation:** 
- Keep world-space pan (matches legacy logical units)
- Consider adding extent clamping for infinite canvas feel
- Initial pan: start at (0,0) or make configurable

### Grid System

| Aspect | Legacy | Current | Status |
|--------|--------|---------|--------|
| Base spacing @ 100% | 1mm (~3.78px @ 96 DPI) | 20px (~5.3mm) | ✗ Different |
| DPI-aware | Yes | No | ✗ Missing |
| Major/minor lines | Yes (every 5th) | Yes (every 5th) | ✓ Match |
| Colors | (0.85, 0.65) | (0.85, 0.65) | ✓ Match |
| Line widths | 0.5px, 1px | 0.5/zoom, 1/zoom | ⚠️ Compensated |
| Rendering | Device-space | World-space | ⚠️ Different approach |

**Recommendation:** 
- Add DPI-aware grid spacing option
- Keep world-space rendering (cleaner code, scales with objects)
- Adjust BASE_GRID_SPACING to match legacy physical size

### Object Sizes

| Object | Legacy @ 100% | Current | Difference | Status |
|--------|---------------|---------|------------|--------|
| Place radius | 30.0px | 25.0px | -17% | ✗ Too small |
| Transition width | 44.0px | 50.0px | +14% | ✗ Too large |
| Transition height | 22.0px | 25.0px | +14% | ✗ Too large |
| Border width | 3.0px | 3.0px | 0% | ✓ Match |

**Physical sizes @ 96 DPI:**

| Object | Legacy | Current | Status |
|--------|--------|---------|--------|
| Place diameter | 15.7mm | 13.1mm | ✗ Smaller |
| Transition | 11.6×5.8mm | 13.1×6.5mm | ✗ Different |

**Recommendation:** Adjust object default sizes to match legacy exactly.

### Coordinate Transformations

| Formula | Legacy | Current | Status |
|---------|--------|---------|--------|
| device_to_logical | `px/scale - pan` | `screen/zoom - pan` | ✓ Match |
| logical_to_device | `(lx+pan)*scale` | `(world+pan)*zoom` | ✓ Match |
| Variable names | scale, pan_x/y | zoom, pan_x/y | ✓ Equivalent |

**Status:** ✓ Perfect match! No changes needed.

---

## Specification for 1:1 Scale

### Definition

**At zoom = 1.0 (100% zoom):**
1. **Coordinate mapping:** 1 world unit = 1 screen pixel
2. **Object sizes:** Match legacy defaults exactly
3. **Grid spacing:** 1mm physical spacing (DPI-aware)
4. **Line widths:** Compensated to maintain visual size
5. **Transform:** `screen = (world + pan) * zoom`

### World Coordinate System

```
            Y-axis (up in world space)
                  ^
                  |
                  |
                  |
(0,0) -----------+-----------> X-axis (right in world space)
origin           |
                 |
                 |
```

**Properties:**
- Origin: (0, 0) in world space
- Units: Logical units (1 unit = 1 pixel @ 100% zoom)
- Range: Practically unlimited (±1 million units)
- Objects positioned in world space

### Screen Coordinate System

```
(0,0) ---------------> X-axis (right on screen)
  |
  |
  |
  v
Y-axis (down on screen)
```

**Properties:**
- Origin: Top-left of viewport
- Units: Device pixels
- Range: Viewport dimensions (e.g., 1920×1080)
- Rendering in screen space after transform

### Transformation Formulas

#### Forward: World → Screen
```python
screen_x = (world_x + pan_x) * zoom
screen_y = (world_y + pan_y) * zoom
```

#### Inverse: Screen → World
```python
world_x = (screen_x / zoom) - pan_x
world_y = (screen_y / zoom) - pan_y
```

#### Verification (100% zoom, no pan)
```
World (100, 200) → Screen (100, 200) ✓
Screen (50, 75) → World (50, 75) ✓
```

#### Verification (200% zoom, no pan)
```
World (100, 200) → Screen (200, 400) ✓ (2x larger)
Screen (200, 400) → World (100, 200) ✓
```

#### Verification (100% zoom, pan=(50, 30))
```
World (100, 200) → Screen (150, 230) ✓ (shifted)
Screen (150, 230) → World (100, 200) ✓
```

### Object Sizes at 1:1 Scale

| Object | Size (logical units) | Size (pixels @ 100%) | Physical (@ 96 DPI) |
|--------|----------------------|----------------------|---------------------|
| Place | radius = 30.0 | 60px diameter | 15.9mm diameter |
| Transition | 44.0 × 22.0 | 44×22 pixels | 11.6 × 5.8 mm |
| Arc line | width = 3.0 | 3px | 0.8mm |
| Arc arrow | size ≈ 12.0 | ~12px | ~3.2mm |
| Text | size = 12.0 | 12pt font | 12pt |

### Grid at 1:1 Scale

**DPI-aware spacing:**
```python
dpi = screen.get_resolution() or 96.0
px_per_mm = dpi / 25.4
base_spacing = 1.0 * px_per_mm  # 1mm physical

# At 96 DPI: 3.78 logical units ≈ 1mm
# At 120 DPI: 4.72 logical units ≈ 1mm
# At 144 DPI: 5.67 logical units ≈ 1mm
```

**Grid lines:**
- Minor lines: Every 1mm (light gray, 0.5px width)
- Major lines: Every 5mm (dark gray, 1px width)
- Line width compensated: `width / zoom`

**Grid @ different zooms:**

| Zoom | Logical Spacing | Device Spacing @ 96 DPI | Lines per 100px |
|------|-----------------|-------------------------|-----------------|
| 0.3 (30%) | 3.78 units | 1.13px | ~88 lines |
| 0.5 (50%) | 3.78 units | 1.89px | ~53 lines |
| 1.0 (100%) | 3.78 units | 3.78px | ~26 lines |
| 2.0 (200%) | 3.78 units | 7.56px | ~13 lines |
| 3.0 (300%) | 3.78 units | 11.34px | ~9 lines |

### Infinite Canvas Bounds

**Recommended extent:**
- Half-extent: 10,000 logical units (matches legacy)
- Total canvas: 20,000 × 20,000 logical units
- At 100% zoom: 20,000 × 20,000 pixels (≈ 13 feet @ 96 DPI)

**Pan clamping:**
```python
# Ensure grid always fills viewport
min_pan_x = (viewport_width / zoom) - extent_x
max_pan_x = extent_x
min_pan_y = (viewport_height / zoom) - extent_y
max_pan_y = extent_y

pan_x = clamp(pan_x, min_pan_x, max_pan_x)
pan_y = clamp(pan_y, min_pan_y, max_pan_y)
```

---

## Implementation Recommendations

### Priority 1: Object Size Corrections

**File:** `src/shypn/api/place.py`
```python
# Change line 19:
DEFAULT_RADIUS = 30.0  # Was 25.0, restore legacy size
```

**File:** `src/shypn/api/transition.py`
```python
# Change lines 18-19:
DEFAULT_WIDTH = 44.0   # Was 50.0, restore legacy size
DEFAULT_HEIGHT = 22.0  # Was 25.0, restore legacy size
```

**Impact:** ✓ Objects will match legacy size at 100% zoom

### Priority 2: Zoom Range Adjustment

**File:** `src/shypn/data/model_canvas_manager.py`
```python
# Change lines 25-26:
MIN_ZOOM = 0.3  # Was 0.1, match legacy practical range
MAX_ZOOM = 3.0  # Was 10.0, match legacy practical range
```

**Impact:** ✓ Zoom range matches legacy (30%-300%)

### Priority 3: DPI-Aware Grid Spacing

**File:** `src/shypn/data/model_canvas_manager.py`

Add DPI detection:
```python
def __init__(self, ...):
    # ... existing code ...
    
    # DPI detection (fallback to 96.0)
    self.screen_dpi = 96.0  # Will be updated from widget
    
def set_screen_dpi(self, dpi):
    """Update DPI from screen/widget."""
    self.screen_dpi = dpi if dpi > 0 else 96.0
    
def get_mm_to_pixels(self):
    """Convert millimeters to pixels based on screen DPI."""
    return self.screen_dpi / 25.4
```

Update grid spacing:
```python
# Change line 32:
BASE_GRID_SPACING = 1.0  # 1mm physical spacing (was 20px)

def get_grid_spacing(self):
    """Calculate grid spacing based on zoom and DPI."""
    px_per_mm = self.get_mm_to_pixels()
    base_mm = self.BASE_GRID_SPACING  # 1mm
    base_px = base_mm * px_per_mm
    
    # Adaptive grid...
    # (Keep existing adaptive logic, but use base_px instead of 20)
```

**File:** `src/shypn/helpers/model_canvas_loader.py`

Update DPI on widget realization:
```python
def _on_realize(self, widget):
    """Called when widget is realized."""
    try:
        screen = widget.get_screen()
        dpi = screen.get_resolution()
        if dpi and dpi > 0:
            self.manager.set_screen_dpi(dpi)
    except Exception:
        pass  # Use default 96.0
```

**Impact:** ✓ Grid spacing will be 1mm physical at all DPIs

### Priority 4: Initial Pan at Origin

**File:** `src/shypn/data/model_canvas_manager.py`

```python
def set_viewport_size(self, width, height):
    """Update viewport size when widget is resized."""
    self.viewport_width = width
    self.viewport_height = height
    
    # OPTION A: Start at origin (match legacy)
    if not self._initial_pan_set and width > 0 and height > 0:
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._initial_pan_set = True
    
    # OPTION B: Center canvas (current behavior)
    # if not self._initial_pan_set and width > 0 and height > 0:
    #     self.pan_x = -(width / 2) / self.zoom
    #     self.pan_y = -(height / 2) / self.zoom
    #     self._initial_pan_set = True
    
    self._needs_redraw = True
```

**Decision needed:** Origin vs centered start?

### Priority 5: Infinite Canvas Extent

**File:** `src/shypn/data/model_canvas_manager.py`

Add extent configuration:
```python
# Add after line 27:
CANVAS_EXTENT = 10000.0  # Half-extent in logical units (±10000)
```

Add pan clamping:
```python
def clamp_pan(self):
    """Clamp pan so canvas bounds always fill viewport."""
    extent_x = self.CANVAS_EXTENT
    extent_y = self.CANVAS_EXTENT
    
    # Ensure extent covers viewport
    min_half_x = (self.viewport_width / self.zoom) / 2.0
    min_half_y = (self.viewport_height / self.zoom) / 2.0
    extent_x = max(extent_x, min_half_x)
    extent_y = max(extent_y, min_half_y)
    
    # Clamp pan
    min_pan_x = (self.viewport_width / self.zoom) - extent_x
    max_pan_x = extent_x
    min_pan_y = (self.viewport_height / self.zoom) - extent_y
    max_pan_y = extent_y
    
    self.pan_x = max(min_pan_x, min(max_pan_x, self.pan_x))
    self.pan_y = max(min_pan_y, min(max_pan_y, self.pan_y))

def zoom_by_factor(self, factor, pointer_x=None, pointer_y=None):
    # ... existing zoom logic ...
    
    # Add at end:
    self.clamp_pan()
```

**Impact:** ✓ Canvas feels infinite but bounded

### Optional: Zoom Percentage Display

Add to status bar or canvas overlay:
```python
def get_zoom_percentage(self):
    """Get zoom as percentage string."""
    return f"{int(self.zoom * 100)}%"
```

Display in UI:
- Status bar: "Zoom: 100%"
- Canvas overlay: Semi-transparent "100%" in corner
- Matches legacy behavior

---

## Test Cases and Validation

### Test 1: 1:1 Scale Verification

**Setup:** Zoom = 1.0, Pan = (0, 0)

**Test cases:**
1. Create Place at world (100, 100)
   - Expected screen position: (100, 100) ✓
   - Expected size: 60px diameter ✓
2. Create Transition at world (200, 150)
   - Expected screen position: (200, 150) ✓
   - Expected size: 44×22 pixels ✓
3. Grid line at world x=0
   - Expected screen position: x=0 ✓
   - Expected spacing: 3.78px @ 96 DPI ✓

### Test 2: Zoom Behavior

**Test at zoom = 2.0 (200%):**
1. Place at world (100, 100)
   - Expected screen: (200, 200) ✓
   - Expected size: 120px diameter ✓
2. Grid spacing
   - Expected: 7.56px @ 96 DPI ✓

**Test at zoom = 0.5 (50%):**
1. Place at world (100, 100)
   - Expected screen: (50, 50) ✓
   - Expected size: 30px diameter ✓
2. Grid spacing
   - Expected: 1.89px @ 96 DPI ✓

### Test 3: Pan Behavior

**Setup:** Zoom = 1.0, Pan = (50, 30)

1. World (100, 100) → Screen (150, 130) ✓
2. Screen (150, 130) → World (100, 100) ✓
3. Grid origin shifts by (50, 30) screen pixels ✓

### Test 4: Coordinate Round-Trip

**For all combinations:**
- Zoom: [0.3, 0.5, 1.0, 2.0, 3.0]
- Pan: [(0,0), (50,30), (-100,-50)]
- Points: [(0,0), (100,100), (500,300)]

**Verify:**
```python
world → screen → world == original_world
```

### Test 5: Infinite Canvas Bounds

1. Pan far right: pan_x should clamp to max_pan_x
2. Pan far left: pan_x should clamp to min_pan_x
3. Pan far up: pan_y should clamp to min_pan_y
4. Pan far down: pan_y should clamp to max_pan_y
5. Grid should always fill viewport (no blank space)

### Test 6: DPI Scaling

**Test on different DPI displays:**
- 96 DPI: Grid 3.78px spacing ✓
- 120 DPI: Grid 4.72px spacing ✓
- 144 DPI: Grid 5.67px spacing ✓
- Physical ruler: 1mm spacing matches ✓

### Test 7: Object Size Consistency

**At zoom = 1.0:**
- Measure Place diameter with ruler: 15.7mm @ 96 DPI ✓
- Measure Transition: 11.6 × 5.8 mm @ 96 DPI ✓

**At zoom = 2.0:**
- Measure Place diameter: 31.4mm @ 96 DPI ✓
- Measure Transition: 23.2 × 11.6 mm @ 96 DPI ✓

### Test 8: Line Width Compensation

**At all zoom levels:**
- Border lines maintain 3px visual width ✓
- Arc lines maintain 2-3px visual width ✓
- Grid lines maintain 0.5px / 1px visual width ✓

---

## Summary

### Critical Fixes Required

1. **Object sizes** (Place: 25→30, Transition: 50×25→44×22)
2. **Zoom range** (0.1-10.0 → 0.3-3.0)
3. **Grid spacing** (20px → 1mm DPI-aware)

### Nice-to-Have Enhancements

1. DPI detection and scaling
2. Pan clamping for infinite canvas feel
3. Initial pan at origin option
4. Zoom percentage display

### No Changes Needed

1. ✓ Coordinate transformation formulas
2. ✓ Grid major/minor colors
3. ✓ Grid major/minor pattern (every 5th)
4. ✓ Border widths

### Implementation Effort

- **Priority 1-2 (object sizes, zoom range):** 5 minutes
- **Priority 3 (DPI grid):** 30 minutes
- **Priority 4-5 (pan, extent):** 45 minutes
- **Testing and validation:** 2 hours
- **Total:** ~3-4 hours

---

**End of Analysis Document**
