# Implementation Plan: 1:1 Scale Restoration

**Date:** October 3, 2025  
**Branch:** petri-net-objects-editing  
**Related:** INFINITE_CANVAS_SCALING_ANALYSIS.md

---

## Quick Summary

The current implementation has **3 critical mismatches** with legacy at 100% zoom (1:1 scale):

1. **🔴 Place too small:** 25px vs 30px radius (-17%)
2. **🔴 Transition wrong size:** 50×25 vs 44×22 pixels (+14%)
3. **🔴 Grid spacing wrong:** 20px vs 1mm (~3.78px @ 96 DPI)

**Coordinate transformations are CORRECT** ✓ - no changes needed there.

---

## Critical Fixes (Priority 1)

### Fix 1: Place Radius

**File:** `src/shypn/api/place.py`  
**Line:** 19

```python
# BEFORE:
DEFAULT_RADIUS = 25.0

# AFTER:
DEFAULT_RADIUS = 30.0  # Match legacy: 30px radius, 60px diameter
```

**Reason:** At zoom=1.0, Place should be 60px diameter to match legacy.

---

### Fix 2: Transition Dimensions

**File:** `src/shypn/api/transition.py`  
**Lines:** 18-19

```python
# BEFORE:
DEFAULT_WIDTH = 50.0
DEFAULT_HEIGHT = 25.0

# AFTER:
DEFAULT_WIDTH = 44.0   # Match legacy dimensions
DEFAULT_HEIGHT = 22.0  # 2:1 aspect ratio preserved
```

**Reason:** At zoom=1.0, Transition should be 44×22 pixels to match legacy.

---

### Fix 3: Zoom Range

**File:** `src/shypn/data/model_canvas_manager.py`  
**Lines:** 25-26

```python
# BEFORE:
MIN_ZOOM = 0.1   # 10%
MAX_ZOOM = 10.0  # 1000%

# AFTER:
MIN_ZOOM = 0.3  # 30% - matches legacy practical range
MAX_ZOOM = 3.0  # 300% - matches legacy practical range
```

**Reason:** Legacy uses 30%-300% range for practical engineering diagrams.

---

## Important Fixes (Priority 2)

### Fix 4: DPI-Aware Grid Spacing

**File:** `src/shypn/data/model_canvas_manager.py`

**Step 1:** Add DPI support (after line 69):

```python
# DPI detection (defaults to 96.0)
self.screen_dpi = 96.0  # Updated from widget on realize
```

**Step 2:** Add DPI methods (after __init__):

```python
def set_screen_dpi(self, dpi):
    """Update screen DPI from widget.
    
    Args:
        dpi: Screen resolution in dots per inch.
    """
    self.screen_dpi = dpi if dpi and dpi > 0 else 96.0

def get_mm_to_pixels(self):
    """Convert millimeters to pixels based on screen DPI.
    
    Returns:
        Pixels per millimeter (float).
    """
    return self.screen_dpi / 25.4
```

**Step 3:** Update BASE_GRID_SPACING (line 32):

```python
# BEFORE:
BASE_GRID_SPACING = 20  # Base grid spacing at zoom=1.0 (~5mm on 96 DPI screen)

# AFTER:
BASE_GRID_SPACING = 1.0  # 1mm physical spacing (DPI-aware)
```

**Step 4:** Update get_grid_spacing method (lines 444-476):

```python
def get_grid_spacing(self):
    """Calculate grid spacing based on current zoom level.
    
    Returns:
        Grid spacing in world coordinates.
    """
    # Convert base spacing from mm to pixels
    px_per_mm = self.get_mm_to_pixels()
    base_px = self.BASE_GRID_SPACING * px_per_mm  # 1mm → pixels
    
    # Adaptive grid: spacing increases at certain zoom thresholds
    if self.zoom >= 5.0:
        return base_px / 10  # Very fine grid (0.1mm)
    elif self.zoom >= 2.0:
        return base_px / 5   # Fine grid (0.2mm)
    elif self.zoom >= 1.0:
        return base_px / 2   # Medium grid (0.5mm)
    elif self.zoom >= 0.5:
        return base_px       # Normal grid (1mm)
    elif self.zoom >= 0.2:
        return base_px * 2   # Coarse grid (2mm)
    else:
        return base_px * 5   # Very coarse grid (5mm)
```

**Step 5:** Update DPI on widget realization  
**File:** `src/shypn/helpers/model_canvas_loader.py`

Add to class (after existing event handlers):

```python
def _on_realize(self, widget):
    """Update DPI when widget is realized."""
    try:
        screen = widget.get_screen()
        dpi = screen.get_resolution()
        if dpi and dpi > 0:
            self.manager.set_screen_dpi(dpi)
            print(f"Screen DPI: {dpi}")
    except Exception as e:
        print(f"Could not detect DPI: {e}, using default 96.0")
```

Connect signal in `__init__`:

```python
self.drawing_area.connect('realize', self._on_realize)
```

**Reason:** Grid should be 1mm physical spacing at all screen DPIs.

---

### Fix 5: Pan Clamping (Infinite Canvas)

**File:** `src/shypn/data/model_canvas_manager.py`

**Step 1:** Add constant (after line 27):

```python
CANVAS_EXTENT = 10000.0  # Half-extent in logical units (±10,000)
```

**Step 2:** Add pan clamping method (before zoom_by_factor):

```python
def clamp_pan(self):
    """Clamp pan to keep canvas bounds within viewport.
    
    Creates infinite canvas feeling while preventing blank space.
    Grid always fills viewport regardless of pan/zoom.
    """
    extent_x = self.CANVAS_EXTENT
    extent_y = self.CANVAS_EXTENT
    
    # Ensure extent is large enough to cover viewport
    min_half_x = (self.viewport_width / self.zoom) / 2.0
    min_half_y = (self.viewport_height / self.zoom) / 2.0
    extent_x = max(extent_x, min_half_x)
    extent_y = max(extent_y, min_half_y)
    
    # Calculate pan limits
    # Grid bounds: [-extent, +extent] in world space
    # Screen bounds: [0, viewport] in screen space
    # Constraint: grid must fully cover screen
    min_pan_x = (self.viewport_width / self.zoom) - extent_x
    max_pan_x = extent_x
    min_pan_y = (self.viewport_height / self.zoom) - extent_y
    max_pan_y = extent_y
    
    # Clamp pan values
    self.pan_x = max(min_pan_x, min(max_pan_x, self.pan_x))
    self.pan_y = max(min_pan_y, min(max_pan_y, self.pan_y))
```

**Step 3:** Call clamp_pan in zoom_by_factor (at end of method, line ~402):

```python
def zoom_by_factor(self, factor, pointer_x=None, pointer_y=None):
    # ... existing zoom logic ...
    
    # Clamp pan to prevent blank space
    self.clamp_pan()
    
    self._needs_redraw = True
```

**Step 4:** Call clamp_pan after pan operations  
**File:** `src/shypn/helpers/model_canvas_loader.py`

In `_on_motion_notify` (after pan update):

```python
# Update pan
self.manager.pan_x = start_pan_x + delta_world_x
self.manager.pan_y = start_pan_y + delta_world_y

# Clamp to canvas bounds
self.manager.clamp_pan()
```

**Reason:** Matches legacy infinite canvas behavior with bounded extent.

---

## Optional Enhancements (Priority 3)

### Enhancement 1: Initial Pan at Origin

**File:** `src/shypn/data/model_canvas_manager.py`  
**Method:** `set_viewport_size` (lines ~590)

**Option A: Start at origin (match legacy):**

```python
if not self._initial_pan_set and width > 0 and height > 0:
    # Start at logical origin (0, 0)
    self.pan_x = 0.0
    self.pan_y = 0.0
    self._initial_pan_set = True
```

**Option B: Center canvas (current behavior):**

```python
if not self._initial_pan_set and width > 0 and height > 0:
    # Center the canvas
    self.pan_x = -(width / 2) / self.zoom
    self.pan_y = -(height / 2) / self.zoom
    self._initial_pan_set = True
```

**Recommendation:** Keep Option B (centered) for better UX. Users can pan to origin if needed.

---

### Enhancement 2: Zoom Percentage Display

Add to status bar or canvas corner to show current zoom level.

**Example implementation:**

```python
def get_zoom_percentage(self):
    """Get current zoom as percentage string."""
    return f"{int(self.zoom * 100)}%"
```

Display options:
- Status bar: "Zoom: 100%"
- Canvas overlay: Semi-transparent label in corner
- Tooltip on zoom slider

---

## Testing Checklist

After implementing fixes, validate:

### ✓ Object Sizes at 100% Zoom
- [ ] Place diameter measures 60 pixels
- [ ] Transition measures 44×22 pixels
- [ ] Border widths are 3 pixels

### ✓ Grid Spacing at 100% Zoom
- [ ] @ 96 DPI: Grid lines ~3.78 pixels apart
- [ ] @ 120 DPI: Grid lines ~4.72 pixels apart
- [ ] Physical measurement: 1mm spacing with ruler

### ✓ Coordinate Transformations
- [ ] World (100, 100) → Screen (100, 100) @ zoom=1.0, pan=(0,0)
- [ ] Screen (100, 100) → World (100, 100) (round-trip)
- [ ] Pointer-centered zoom preserves point under cursor

### ✓ Zoom Range
- [ ] Min zoom: 30% (MIN_ZOOM = 0.3)
- [ ] Max zoom: 300% (MAX_ZOOM = 3.0)
- [ ] Scroll wheel zooms smoothly

### ✓ Pan Clamping
- [ ] Cannot pan past canvas bounds
- [ ] Grid always fills viewport (no blank space)
- [ ] Smooth panning with right-click drag

### ✓ Visual Consistency
- [ ] Objects maintain size at different zoom levels (zoom compensation)
- [ ] Line widths stay constant (border, arc, grid)
- [ ] Major lines every 5th grid line
- [ ] Colors match legacy (minor: 0.85, major: 0.65)

---

## Implementation Order

1. **Quick wins (5 min):**
   - Fix object sizes (Place, Transition)
   - Fix zoom range

2. **DPI grid (30 min):**
   - Add DPI detection
   - Update grid spacing calculation
   - Test on different DPI displays

3. **Pan clamping (45 min):**
   - Add CANVAS_EXTENT constant
   - Implement clamp_pan method
   - Add clamping to zoom and pan operations

4. **Testing (2 hours):**
   - Run checklist above
   - Visual inspection at multiple zooms
   - Measure with ruler/screen measurement tool
   - Test on different DPI displays

**Total time:** 3-4 hours

---

## Backwards Compatibility

### File Format
No changes to file format - object sizes are stored, not defaults.

### Existing Models
Existing models will render correctly:
- Objects with explicit sizes: unchanged
- Objects using old defaults: will need resizing (manual or script)

### Migration Script (Optional)

If needed, create script to update existing models:

```python
def migrate_object_sizes(model):
    """Update object sizes from old to new defaults."""
    for place in model.places:
        if place.radius == 25.0:  # Old default
            place.radius = 30.0   # New default
    
    for transition in model.transitions:
        if transition.width == 50.0 and transition.height == 25.0:
            transition.width = 44.0
            transition.height = 22.0
```

---

## Summary

**Critical fixes (Priority 1):**
- Object sizes: 3 lines changed
- Zoom range: 2 lines changed

**Important fixes (Priority 2):**
- DPI grid: ~50 lines added/changed
- Pan clamping: ~30 lines added

**Result:**
- ✓ Perfect 1:1 scale at zoom=1.0
- ✓ Matches legacy behavior
- ✓ DPI-aware grid
- ✓ Infinite canvas feeling

**No changes needed:**
- ✓ Coordinate transformations (already correct!)
- ✓ Grid colors and patterns
- ✓ Cairo transform approach

---

**Ready to implement?** Start with Priority 1 fixes (5 minutes), test, then proceed to Priority 2.
