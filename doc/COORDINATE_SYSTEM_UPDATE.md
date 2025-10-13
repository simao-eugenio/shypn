# Coordinate System Documentation Update

**Date**: October 12, 2025  
**Author**: Shypn Development Team  
**Status**: Complete

## Overview

This document tracks the comprehensive update to document the coordinate system conventions used throughout the Shypn codebase. The update clarifies the distinction between **conceptual/mathematical coordinates** (Cartesian) and **implementation coordinates** (graphics).

## Coordinate System Summary

### Conceptual Model (Documentation)
- **Origin**: Lower-left corner (0, 0)
- **X-axis**: Grows right →
- **Y-axis**: Grows upward ↑
- **Usage**: All design discussions, documentation, mathematical reasoning

### Implementation (Code)
- **Origin**: Top-left corner (0, 0)
- **X-axis**: Grows right → (same as conceptual)
- **Y-axis**: Grows downward ↓ (opposite of conceptual)
- **Usage**: All rendering code, Cairo graphics, GTK widgets

### Key Insight
**No coordinate transformation is needed** because:
1. Relative positioning works identically in both systems
2. `child.y = parent.y + spacing` creates visual descent in both interpretations
3. Higher Y values = descended child (consistent in both systems)

## Files Updated

### 1. Core Documentation

#### `doc/COORDINATE_SYSTEM.md` ✅ NEW
Comprehensive reference document covering:
- Mathematical coordinate system (Cartesian)
- Graphics coordinate system (Cairo/GTK)
- Mapping and equivalence explanation
- Usage guidelines for documentation vs code
- File-specific coordinate usage
- Best practices
- Summary table

### 2. Source Code Headers

#### `src/shypn/data/pathway/tree_layout.py` ✅ UPDATED
**Changes**:
- Added coordinate system section to module docstring
- Reference to `doc/COORDINATE_SYSTEM.md`
- Clarified "Y increases = visual descent = pathway progression"

**Line 1-29**: Updated module header with:
```python
Coordinate System:
- Conceptually: Cartesian coordinates with origin at lower-left, Y grows upward
- Implementation: Graphics coordinates with origin at top-left, Y grows downward
- See doc/COORDINATE_SYSTEM.md for complete details
- In this file: Y increases = visual descent = pathway progression
```

#### `src/shypn/data/pathway/hierarchical_layout.py` ✅ UPDATED
**Changes**:
- Added coordinate system section to module docstring
- Reference to `doc/COORDINATE_SYSTEM.md`
- Clarified "Increasing Y values = visual descent = pathway flow"

**Line 1-29**: Updated module header

#### `src/shypn/data/pathway/pathway_data.py` ✅ UPDATED
**Changes**:
- Added coordinate system note to module docstring
- Clarified position data storage format
- Reference to `doc/COORDINATE_SYSTEM.md`

**Line 1-11**: Updated module header with:
```python
Coordinate System Note:
- Position data stored as (x, y) tuples use graphics coordinates
- Origin at top-left, Y increases downward (standard Cairo/GTK)
- Conceptually represents Cartesian space (see doc/COORDINATE_SYSTEM.md)
- Higher Y values = further descended in pathway hierarchy
```

#### `src/shypn/data/model_canvas_manager.py` ✅ UPDATED
**Changes**:
- Added coordinate system section to module docstring
- Clarified Cairo/GTK standard usage
- Reference to `doc/COORDINATE_SYSTEM.md`

**Line 1-21**: Updated module header

### 3. Code Comments

#### `src/shypn/data/pathway/tree_layout.py` ✅ ENHANCED
**Location**: Lines 387-394 (child Y position calculation)

**Added detailed comment**:
```python
# COORDINATE SYSTEM NOTE:
# - Graphics: Y increases downward (Cairo/GTK standard)
# - Conceptual: Y growth = pathway descent/progression
# - child_y > parent_y means "child is below parent" visually
# - child_y > parent_y means "child at higher Y value" mathematically
# Both interpretations are consistent: increasing Y = descended child
```

**Location**: Lines 427-439 (angle-based positioning)

**Added comprehensive comment**:
```python
# COORDINATE SYSTEM: Tree layout in 2D space
# - Vertical axis (Y): Tree depth/hierarchy (parent → child)
#   * Y increases downward (graphics) = Y increases (Cartesian)
#   * Both mean: child has higher Y value than parent
# - Horizontal axis (X): Sibling spreading (left ← parent → right)
#   * Negative angles → spread left (smaller X)
#   * Positive angles → spread right (larger X)
# - Formula: x_offset = vertical_distance × tan(angle_from_vertical)
#   * Angle measured from vertical (Y-axis)
#   * Result: horizontal displacement from parent
```

### 4. Project Documentation

#### `README.md` ✅ UPDATED
**Changes**:
- Added `COORDINATE_SYSTEM.md` to documentation index
- Reorganized documentation section with subsections
- Added prominent note about coordinate system conventions

**Section "Documentation"**: 
- Created "Core Documentation" subsection
- `COORDINATE_SYSTEM.md` listed first in core docs
- Added note at end explaining Cartesian vs graphics coordinate usage

## Implementation Details

### No Code Logic Changes
**Important**: This update is **documentation-only**. No algorithms or calculations were modified. The code already correctly implements graphics coordinates; this update only clarifies the conceptual framework.

### Files with Coordinate System References

| File | Type | Update |
|------|------|--------|
| `doc/COORDINATE_SYSTEM.md` | Documentation | Created (new file) |
| `doc/COORDINATE_SYSTEM_UPDATE.md` | Documentation | Created (this file) |
| `README.md` | Documentation | Updated (added reference) |
| `tree_layout.py` | Source | Updated (header + comments) |
| `hierarchical_layout.py` | Source | Updated (header) |
| `pathway_data.py` | Source | Updated (header) |
| `model_canvas_manager.py` | Source | Updated (header) |

### Files WITHOUT Updates (Use Coordinates Implicitly)

These files use coordinates but don't need explicit coordinate system documentation:
- `src/shypn/netobjs/place.py` - Stores (x, y) positions
- `src/shypn/netobjs/transition.py` - Stores (x, y) positions
- `src/shypn/netobjs/arc.py` - Uses endpoint positions
- `src/shypn/data/pathway/pathway_postprocessor.py` - Passes through positions
- All rendering code in `src/shypn/canvas/` - Uses Cairo directly

## Verification

### Documentation Consistency
✅ All pathway-related files now reference `doc/COORDINATE_SYSTEM.md`  
✅ Module docstrings clarify coordinate system usage  
✅ In-code comments explain coordinate system at key calculation points  
✅ README.md provides high-level overview with documentation link

### Code Correctness
✅ No algorithm changes (documentation-only update)  
✅ Existing tests continue to pass  
✅ Visual output unchanged  
✅ Tree layout produces correct steep descent (as tested)

## Usage Guidelines

### For Developers
1. **Read `doc/COORDINATE_SYSTEM.md`** first when working with positioning
2. **Think in Cartesian** when designing or discussing algorithms
3. **Implement in graphics coords** directly (no transformation needed)
4. **Comment for clarity** when coordinate interpretation matters

### For Documentation Writers
1. **Use Cartesian terminology**: "Y increases", "higher Y value", "descended"
2. **Avoid confusion**: Don't say "downward" (ambiguous in Cartesian thinking)
3. **Be explicit**: When needed, specify "visual descent" vs "Y-value increase"
4. **Reference main doc**: Link to `COORDINATE_SYSTEM.md` for details

### For Code Reviewers
1. **Check docstrings** in new positioning code
2. **Verify comments** at key calculation points
3. **Ensure consistency** with established conventions
4. **Request clarification** if coordinate usage is ambiguous

## Future Work

### Potential Enhancements
- Add coordinate system diagram to `COORDINATE_SYSTEM.md`
- Create visual examples showing Cartesian vs graphics interpretation
- Add coordinate system section to contributor guidelines
- Consider helper functions with descriptive names (e.g., `descend_to_child_level()`)

### Documentation Maintenance
- Update coordinate system docs when adding new layout algorithms
- Ensure new positioning code includes coordinate system comments
- Keep `COORDINATE_SYSTEM.md` as authoritative reference

## Testing

### Validation Tests
```bash
# Verify tree layout still produces steep descent
cd /home/simao/projetos/shypn
python3 test_vertical_tree_spacing.py

# Verify real pathway layout
python3 test_real_sbml_tree.py

# Run all pathway tests
./test_arc_transformations.sh
```

### Visual Verification
1. Load SBML pathway (e.g., BIOMD0000000001)
2. Verify tree grows visually downward (increasing Y)
3. Verify siblings spread horizontally (left and right)
4. Verify steep vertical descent angle

## Summary

This comprehensive update documents the coordinate system conventions used throughout Shypn:

✅ **Created** `doc/COORDINATE_SYSTEM.md` - Authoritative reference  
✅ **Updated** 4 source files with coordinate system headers  
✅ **Enhanced** 2 code sections with detailed coordinate comments  
✅ **Updated** `README.md` with coordinate system reference  
✅ **Zero** changes to algorithms or logic (documentation-only)  
✅ **Maintained** all existing tests and functionality  

**Result**: Developers now have clear guidance on coordinate system usage, distinguishing between conceptual Cartesian thinking and implementation graphics coordinates.

---

**Approved by**: Development Team  
**Date**: October 12, 2025  
**Version**: 1.0
