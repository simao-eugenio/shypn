# Coordinate System Documentation

## Overview

This document defines the coordinate system conventions used throughout the Shypn Petri Net editor application.

## Mathematical Coordinate System (Conceptual Model)

**For all design discussions, documentation, and mathematical reasoning**, we use the **Cartesian coordinate system**:

```
      Y ↑
        |
        |
        |
        |
(0,0)---+--------→ X
```

### Properties:
- **Origin**: (0, 0) at the **lower-left corner**
- **First Quadrant**: All coordinates are positive (X ≥ 0, Y ≥ 0)
- **X-axis**: Grows to the **right** (positive direction →)
- **Y-axis**: Grows **upward** (positive direction ↑)
- **Units**: Logical units (pixels in world space)

### Rationale:
- Matches mathematical conventions
- Aligns with engineering diagrams
- Intuitive for "vertical growth" = increasing Y
- Natural for tree layouts where "descendants" are at higher Y values

## Graphics Coordinate System (Implementation)

**For actual rendering with Cairo/GTK**, the implementation uses **graphics coordinates**:

```
(0,0)---+--------→ X
        |
        |
        |
        ↓ Y
```

### Properties:
- **Origin**: (0, 0) at the **top-left corner**
- **X-axis**: Grows to the **right** (same as mathematical)
- **Y-axis**: Grows **downward** (opposite of mathematical)
- **Units**: Screen pixels (after zoom/pan transforms)

### Implementation Details:
- Cairo graphics library uses top-left origin
- GTK widgets use top-left origin
- All rendering code operates in this coordinate system

## Coordinate System Mapping

### No Transformation Needed

**Important**: Despite the conceptual difference, **no Y-axis flipping is implemented** in the code. The system directly uses graphics coordinates for all calculations and rendering.

### Why This Works:

1. **Relative Positioning**: Tree layouts and other algorithms calculate relative positions (parent → child), not absolute screen positions
2. **Consistent Interpretation**: "Child below parent" means:
   - Mathematically: child.y > parent.y (higher Y value)
   - In graphics coords: child.y > parent.y (lower on screen)
   - Both use the same calculation: `child.y = parent.y + spacing`

3. **Visual Equivalence**: The visual result is identical whether you think:
   - "Tree grows downward on screen" (graphics interpretation)
   - "Tree grows to higher Y values" (mathematical interpretation)

## Usage Guidelines

### In Documentation:
- Use **Cartesian (mathematical) coordinates** when describing concepts
- Example: "Species B is positioned at Y=250, which is below (descended from) species A at Y=100"
- Interpretation: Higher Y value = descended = further in pathway

### In Code:
- Use **graphics coordinates** directly
- Comment with mathematical interpretation when helpful
- Example:
  ```python
  # Child Y increases (descends in tree / higher in Cartesian space)
  child_y = parent_y + vertical_spacing
  ```

### In Tree Layout:
- "Vertical descent" means **increasing Y values**
- "Horizontal spread" means **X offset from parent**
- Angles are measured from vertical (Y-axis)
- Positive angles → spread right (positive X)
- Negative angles → spread left (negative X)

## File-Specific Coordinate Usage

### `src/shypn/data/pathway/tree_layout.py`
- **Implementation**: Graphics coordinates (Y increases downward)
- **Comments**: Mathematical interpretation (Y growth = descent/progression)
- **Angles**: Measured from vertical axis
- **Key formula**: `x_offset = vertical_distance × tan(angle)`

### `src/shypn/data/model_canvas_manager.py`
- **Implementation**: Graphics coordinates (standard Cairo)
- **Transformations**: Zoom and pan applied to graphics coordinates
- **Grid**: Rendered in graphics coordinate space

### `src/shypn/netobjs/place.py`, `transition.py`, `arc.py`
- **Storage**: Positions stored as (x, y) in graphics coordinates
- **Rendering**: Direct use of stored coordinates with Cairo

### `src/shypn/data/pathway/hierarchical_layout.py`
- **Implementation**: Graphics coordinates
- **Tree integration**: Calls tree_layout with graphics coordinates
- **Post-processing**: No coordinate transformation

## Summary

| Aspect | Mathematical (Documentation) | Graphics (Implementation) |
|--------|------------------------------|---------------------------|
| Origin | Lower-left (0,0) | Top-left (0,0) |
| X Growth | Right → | Right → |
| Y Growth | Upward ↑ | Downward ↓ |
| First Quadrant | X≥0, Y≥0 | X≥0, Y≥0 |
| Used In | Docs, discussions, design | All code, rendering |
| Transformation | None required | Native Cairo/GTK |

## Best Practices

1. **Document with Cartesian thinking**: "Tree descends to higher Y values"
2. **Implement with graphics reality**: `child.y = parent.y + spacing` (increases downward)
3. **Comment for clarity**: Explain both perspectives when helpful
4. **Test visually**: Verify that increasing Y produces expected visual descent
5. **Maintain consistency**: Don't mix interpretations within single code section

---

**Last Updated**: October 12, 2025  
**Version**: 1.0  
**Applies To**: Shypn v0.1.0+
