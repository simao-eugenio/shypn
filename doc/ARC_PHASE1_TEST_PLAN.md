# Arc Geometry Phase 1 - Test Plan

**Date**: 2025-10-10  
**Phase**: 1 - Analysis & Foundation  
**Status**: Ready for Interactive Testing

---

## Summary of Current Implementation

### ✅ What's Already Working

1. **Perimeter-to-Perimeter Calculations**  
   ✓ Ray-circle intersection for Places
   ✓ Ray-rectangle intersection for Transitions
   ✓ Boundary points calculated correctly

2. **Curved Arc Support**  
   ✓ Quadratic Bezier curves
   ✓ Control point calculation
   ✓ Mirror symmetry for opposite arcs

3. **Hit Detection**  
   ✓ Point-to-line distance for straight arcs
   ✓ Sampled distance for curved arcs
   ✓ Parallel arc offset handling

### ⚠️ Known Issues to Test

1. **Parallel Arc Offset Issue**  
   - Offset applied to centers, then boundary calculated
   - Should: Calculate boundary first, then apply offset
   - **Impact**: Parallel arcs may not align perfectly with edges

2. **Curved Arc Boundary Calculation**  
   - Uses iterative sampling to find boundary intersection
   - May be imprecise for very curved arcs
   - **Impact**: Arrow tip may not touch object edge exactly

3. **Hit Detection for Curved Arcs**  
   - Uses 20-sample points
   - May miss clicks on tightly curved sections
   - **Impact**: Hard to select very curved arcs

4. **Arrowhead Direction on Curves**  
   - Uses simple approximation (control_point → end_point)
   - Not true tangent to curve
   - **Impact**: Arrow may point slightly wrong direction

---

## Interactive Test Cases

### Test Set 1: Straight Arcs - Basic Geometry

**Purpose**: Verify perimeter-to-perimeter works for straight arcs

#### Test 1.1: Place to Transition (Horizontal)
```
Action: Create Place at (100, 100), Transition at (300, 100)
        Create arc from Place to Transition
Expected: Arc starts at right edge of Place circle
          Arc ends at left edge of Transition rectangle
Test:    Measure visually - should align perfectly
```

#### Test 1.2: Place to Transition (Vertical)
```
Action: Create Place at (100, 100), Transition at (100, 300)
        Create arc from Place to Transition
Expected: Arc starts at bottom edge of Place
          Arc ends at top edge of Transition
Test:    Measure visually
```

#### Test 1.3: Place to Transition (Diagonal)
```
Action: Create Place at (100, 100), Transition at (300, 250)
        Create arc from Place to Transition
Expected: Arc tangent to both objects at correct angle
Test:    No gap or overlap visible
```

#### Test 1.4: Different Sized Objects
```
Action: Create small Place (radius 20), large Transition (80x40)
        Create arc between them
Expected: Arc endpoints scale correctly with object size
Test:    Try various size combinations
```

---

### Test Set 2: Parallel Arcs

**Purpose**: Test parallel arc offset behavior

#### Test 2.1: Simple Parallel Arcs (Same Direction)
```
Action: Create Place P1 at (100, 100), Place P2 at (300, 100)
        Create arc A1: P1 → P2
        Create arc A2: P1 → P2 (parallel)
Expected: Two arcs side-by-side, evenly spaced
          Both start/end at circle edges
Test:    Check spacing is uniform
         Verify no overlap
```

#### Test 2.2: Opposite Arcs
```
Action: Create Place P1, Place P2
        Create arc A1: P1 → P2
        Create arc A2: P2 → P1 (opposite direction)
Expected: Arcs curve away from each other (mirror symmetry)
          Both touch object edges correctly
Test:    Measure symmetry visually
         Check for gaps at endpoints
```

#### Test 2.3: Multiple Parallel Arcs
```
Action: Create 4 arcs all from P1 → P2
Expected: All 4 arcs evenly spaced
          Outermost arcs visible
          All touch edges
Test:    Count visible arcs
         Check edge alignment
```

---

### Test Set 3: Curved Arcs

**Purpose**: Test Bezier curve rendering and boundary intersection

#### Test 3.1: Simple Curved Arc
```
Action: Create Place P1, Place P2 (horizontal)
        Create curved arc P1 → P2
Expected: Smooth curve between objects
          Arc starts/ends at object edges
          Arrowhead points along curve tangent
Test:    Visual smoothness
         Edge alignment
         Arrow direction
```

#### Test 3.2: Adjust Curvature
```
Action: Create curved arc
        Adjust curvature parameter (if available)
Expected: Curve depth changes
          Endpoints stay on edges
          No penetration into objects
Test:    Try various curvature values
         Check boundary intersection
```

#### Test 3.3: Tightly Curved Arc
```
Action: Create objects close together
        Create curved arc with high curvature
Expected: Tight curve without penetrating objects
          Endpoints still on edges
Test:    Visual inspection for penetration
```

#### Test 3.4: Curved Arc Between Different Shapes
```
Action: Curved arc from Place (circle) to Transition (rectangle)
Expected: Both endpoints correctly calculated
          Curve smooth
Test:    Try both directions (P→T and T→P)
```

---

### Test Set 4: Hit Detection

**Purpose**: Test arc selection accuracy

#### Test 4.1: Click on Straight Arc
```
Action: Create straight arc
        Click directly on arc line
Expected: Arc selects
Test:    Try clicking at various points along arc
         Try clicking slightly off (should still select with tolerance)
```

#### Test 4.2: Click on Curved Arc
```
Action: Create curved arc
        Click on curve (various points)
Expected: Arc selects
Test:    Click at: start, middle, end, apex of curve
         All should select the arc
```

#### Test 4.3: Click Near But Not On Arc
```
Action: Create arc
        Click 15 pixels away from arc
Expected: Arc does NOT select
Test:    Verify tolerance distance is appropriate
```

#### Test 4.4: Parallel Arc Selection
```
Action: Create 3 parallel arcs
        Click on middle arc
Expected: Only middle arc selects (not neighbors)
Test:    Verify correct arc selected
         Try clicking between arcs (should select nearest)
```

---

### Test Set 5: Edge Cases

**Purpose**: Test degenerate and unusual cases

#### Test 5.1: Very Short Arc
```
Action: Create objects very close (10 pixels apart)
        Create arc
Expected: Arc still renders (even if tiny)
          No crash or error
Test:    Check rendering
         Check selection
```

#### Test 5.2: Overlapping Objects
```
Action: Create overlapping Place and Transition
        Try to create arc
Expected: Arc handles gracefully
          Or error message if invalid
Test:    Document behavior
```

#### Test 5.3: Self-Loop
```
Action: Try to create arc from object to itself
Expected: System prevents (bipartite requirement)
          Or shows error
Test:    Verify validation
```

#### Test 5.4: Very Large Object
```
Action: Create huge Transition (500x500)
        Create arc to small Place
Expected: Arc endpoints calculated correctly
          Rendering works at all zoom levels
Test:    Try various zoom levels
```

---

## Testing Protocol

### For Each Test:

1. **DRAW**: Create the test case in the application
2. **OBSERVE**: Note what happens
3. **MEASURE**: Check alignment, spacing, angles
4. **INTERACT**: Try selecting, moving, editing
5. **REPORT**: Tell me one of:
   - ✅ "Works correctly" - describe what you see
   - ⚠️ "Works but has issue" - describe the issue
   - ❌ "Doesn't work" - describe what's wrong

### What to Look For:

**Visual Inspection**:
- Arc endpoints align with object edges (no gaps)
- Arcs don't penetrate objects
- Parallel arcs have even spacing
- Curves are smooth
- Arrowheads point in correct direction

**Interaction**:
- Clicking on arc selects it
- Can't accidentally select wrong arc
- Selection highlight visible
- Handles respond correctly

**Edge Cases**:
- No crashes
- Graceful degradation
- Error messages if needed

---

## Expected Issues We'll Find

Based on code analysis, I expect we'll discover:

1. **Parallel arc offset** - Endpoints may not be perfectly aligned when arcs are offset
2. **Curved arc endpoints** - Iterative sampling may be imprecise
3. **Arrowhead direction** - May not be perfect tangent on curves
4. **Hit detection on tight curves** - May miss some clicks

These are normal and expected. We'll fix them in later phases!

---

## Next Steps After Phase 1

Once we complete testing, we'll:

1. Document all findings
2. Prioritize issues by severity
3. Plan Phase 2 fixes
4. Start with highest priority items

---

## Let's Begin!

**Start with Test Set 1.1**: Create a horizontal Place-to-Transition arc and tell me what you see!

Screenshot if possible, or just describe:
- Do the endpoints align with the edges?
- Any gaps visible?
- Does it look correct?
