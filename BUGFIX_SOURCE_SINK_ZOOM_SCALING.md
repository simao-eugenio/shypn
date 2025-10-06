# Bug Fix: Source/Sink Indicators Now Scale With Zoom

## Issue Description

**Problem**: Source/sink arrow indicators on transitions did not scale with zoom level - they stayed constant size on screen regardless of zoom.

**User Report**: "little arcs source/sink indicators do not scale with zoom"

**Expected Behavior**: Indicators should grow/shrink proportionally with the transition as you zoom in/out

**Actual Behavior (Before Fix)**: Indicators remained constant screen size, appearing disconnected from transitions at different zoom levels

## Root Cause Analysis

The source/sink marker rendering code was using **zoom compensation** to keep indicators at constant screen size:

```python
# INCORRECT (before fix):
arrow_length = 20.0 / zoom  # Dividing by zoom keeps screen size constant
arrow_head_size = 6.0 / zoom
line_width = 2.0 / zoom
```

This approach makes sense for UI elements like selection handles that should always be visible at the same size. However, for **visual indicators that are part of the object**, they should scale with the object they're attached to.

### Why Zoom Compensation Was Used

The original implementation followed the pattern used for other screen-space elements:
- Selection boxes and handles
- Font sizes for labels
- Line widths for borders

These all use `/ zoom` to maintain constant screen size.

### Why It Should NOT Be Used Here

Source/sink indicators are **semantic markers** attached to the transition, not UI chrome. They should:
1. **Grow with the transition** when zooming in (to remain visible and proportional)
2. **Shrink with the transition** when zooming out (to not overwhelm the view)
3. **Maintain visual relationship** with the transition rectangle

## The Fix

**Solution**: Remove zoom compensation to make indicators scale in world space:

```python
# CORRECT (after fix):
arrow_length = 20.0  # World space units
arrow_head_size = 6.0  # World space units  
line_width = 2.0  # World space units
```

### Code Changes

**File**: `src/shypn/netobjs/transition.py`

**Method**: `_render_source_sink_markers()`

**Lines Modified**: 139-141

#### Before (Incorrect - Screen Space):
```python
def _render_source_sink_markers(self, cr, x: float, y: float, width: float, height: float, zoom: float = 1.0):
    """Render source/sink markers on the transition.
    
    Source transitions get an incoming arrow from the left (or top if vertical).
    Sink transitions get an outgoing arrow to the right (or bottom if vertical).
    
    Args:
        cr: Cairo context
        x, y: Center position (world coords)
        width, height: Rectangle dimensions (already swapped if vertical)
        zoom: Current zoom level for size compensation
    """
    arrow_length = 20.0 / zoom  # Length of arrow
    arrow_head_size = 6.0 / zoom  # Size of arrow head
    line_width = 2.0 / zoom  # Line width for arrow
```

#### After (Correct - World Space):
```python
def _render_source_sink_markers(self, cr, x: float, y: float, width: float, height: float, zoom: float = 1.0):
    """Render source/sink markers on the transition.
    
    Source transitions get an incoming arrow from the left (or top if vertical).
    Sink transitions get an outgoing arrow to the right (or bottom if vertical).
    
    Args:
        cr: Cairo context
        x, y: Center position (world coords)
        width, height: Rectangle dimensions (already swapped if vertical)
        zoom: Current zoom level (not used - markers scale with zoom)
    """
    # Markers scale with zoom (world space) to match transition size
    arrow_length = 20.0  # Length of arrow in world units
    arrow_head_size = 6.0  # Size of arrow head in world units
    line_width = 2.0  # Line width for arrow in world units
```

## Impact Assessment

### What Changed

**Visual Behavior**:
- **Zoom In (2x)**: Indicators are now 2x larger (was: same size)
- **Zoom Out (0.5x)**: Indicators are now 0.5x smaller (was: same size)
- **Default (1x)**: No change (20px arrow length remains 20px)

**Proportions**:
- Indicators now maintain constant **proportional** size relative to transitions
- Default indicator size (20px arrow) works well with default transition size (60x40)
- Ratio: ~33% of transition width

### What Stays The Same

- Indicator positions (attached to transition edges)
- Indicator colors (matches border color or black)
- Indicator shapes (arrows with filled heads)
- Source/sink semantics (source = incoming, sink = outgoing)

## Comparison: Screen Space vs World Space

### Screen Space Elements (Use `/ zoom`)

Elements that should remain constant size regardless of zoom:

```python
# Selection handles
handle_size = 8.0 / zoom  # Always 8 pixels on screen

# UI font sizes  
font_size = 12.0 / zoom  # Always readable

# Thin borders for precise selection
line_width = 1.0 / zoom  # Always 1 pixel thin
```

**Examples**: Selection boxes, resize handles, UI buttons, tooltips

### World Space Elements (No zoom compensation)

Elements that should scale with objects:

```python
# Source/sink indicators (NOW FIXED)
arrow_length = 20.0  # Scales with transition

# Transition rectangles
width = 60.0  # Scales with zoom
height = 40.0  # Scales with zoom

# Arc weights
weight_value = 3  # Rendered text scales with zoom
```

**Examples**: Petri net objects (places, transitions, arcs), labels, markers, weights

## Visual Examples

### Before Fix (Screen Space)

```
Zoom 0.5x:                 Zoom 1x:                  Zoom 2x:
[→|▯]  (tiny box,          [→|▯]  (normal,           [→|    ▯    ]  (big box,
        normal arrow)               normal arrow)                     normal arrow)
        
Arrow appears             Arrow matches             Arrow appears too small
too large                 transition                relative to transition
```

### After Fix (World Space)

```
Zoom 0.5x:                 Zoom 1x:                  Zoom 2x:
[→|▯]  (tiny box,          [→|▯]  (normal,          [→→| ▯ ]  (big box,
        tiny arrow)                normal arrow)              big arrow)
        
Arrow scales              Arrow matches             Arrow scales
proportionally            transition                proportionally
```

## Testing

### Manual Test Cases

1. **Default Zoom (1.0)**:
   - Create transition, set as source
   - Verify arrow is visible and proportional (~1/3 of transition width)

2. **Zoom In (2.0)**:
   - Zoom in 2x
   - Verify arrow grows proportionally with transition
   - Arrow should still be ~1/3 of transition width

3. **Zoom Out (0.5)**:
   - Zoom out to 0.5x
   - Verify arrow shrinks proportionally with transition
   - Arrow should remain visible and proportional

4. **Vertical Transitions**:
   - Rotate transition to vertical
   - Verify arrow points downward into top edge
   - Test at multiple zoom levels

5. **Sink Markers**:
   - Create sink transition
   - Verify outgoing arrow scales correctly
   - Test at multiple zoom levels

6. **Both Source and Sink**:
   - Set transition as both source and sink
   - Verify both arrows scale correctly
   - Should have incoming and outgoing arrows

### Visual Verification

At each zoom level, verify:
- ✅ Arrow length is proportional to transition size
- ✅ Arrow head size matches arrow shaft
- ✅ Line width is appropriate (not too thick/thin)
- ✅ Arrows touch transition edges correctly
- ✅ No gaps or overlaps between arrow and transition

## Related Changes

### Files Modified

- `src/shypn/netobjs/transition.py` - Removed zoom compensation from marker rendering

### No Changes Needed

- **UI Files**: No changes (properties dialog unchanged)
- **Model Files**: No changes (is_source/is_sink still boolean properties)
- **Simulation**: No changes (source/sink behavior unchanged)
- **Serialization**: No changes (saving/loading unchanged)

## Design Rationale

### Why World Space Is Correct

**Semantic Attachment**: Indicators are properties OF the transition, not UI decorations

**Visual Hierarchy**: Indicators should "zoom with" the thing they're indicating

**Consistency**: Other object properties (labels, weights) scale with zoom

**User Expectation**: When you zoom in to see detail, you want to see indicator detail too

### When Screen Space Would Be Wrong

If indicators stayed constant screen size:
- **Zoom In**: Arrows would look disconnected from huge transitions
- **Zoom Out**: Arrows would obscure tiny transitions
- **Proportions**: Visual relationship would break at different zooms

## Alternative Approaches Considered

### 1. Hybrid Scaling (Rejected)

Use partial zoom compensation: `arrow_length = 20.0 / sqrt(zoom)`

**Pros**: Gentler scaling
**Cons**: Complex, non-linear, inconsistent with other objects

### 2. Configurable Scaling (Rejected)

Add preference for screen/world space indicators

**Pros**: User choice
**Cons**: Unnecessary complexity, world space is objectively better

### 3. Adaptive Sizing (Rejected)

Different sizes at different zoom levels: `if zoom > 2: arrow_length = 15 else: 20`

**Pros**: Fine-tuned appearance
**Cons**: Discontinuous jumps, maintenance burden

## Best Practices

### When to Use Zoom Compensation

Use `/ zoom` for:
- ✅ UI controls (buttons, handles, scrollbars)
- ✅ Selection indicators (selection boxes, resize handles)
- ✅ Cursor feedback (crosshairs, snap indicators)
- ✅ Grid lines (remain visible at all zooms)
- ✅ Minimum line widths (readability)

### When NOT to Use Zoom Compensation

Don't use `/ zoom` for:
- ✅ Object geometry (shapes, sizes)
- ✅ Object properties (markers, decorations)
- ✅ Labels and text (when part of object)
- ✅ Semantic indicators (source/sink arrows)
- ✅ Arc weights and multipliers

## Status

✅ **FIXED**: Source/sink indicators now scale with zoom  
✅ **VERIFIED**: Code compiles without errors  
⏳ **TESTING**: User should verify visual behavior at different zoom levels  

## Files Modified

- `src/shypn/netobjs/transition.py` - Removed zoom compensation from `_render_source_sink_markers()`

## Priority

**MEDIUM** - Visual consistency issue, affects user experience but not functionality

## Version

Fixed in: feature/property-dialogs-and-simulation-palette branch  
Date: 2025-10-06
