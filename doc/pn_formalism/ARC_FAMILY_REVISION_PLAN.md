# Arc Family Revision Plan

## Problem Analysis

### Current Issues

1. **Incorrect Geometry**: Arcs are drawn from center-to-center of objects, but actual dimensions don't account for perimeter intersection
2. **Hidden Extremities Workaround**: Visual appearance is achieved by hiding arc endpoints, but the underlying geometry is wrong
3. **Wrong Construction Order**: Arc dimensions calculated before perimeter clipping instead of after
4. **Legacy Auto-Curved Opposites**: Automatic conversion of parallel arcs to curved is from legacy code and should be removed
5. **Non-selectable Long Arcs**: Long arcs aren't clickable/selectable, likely due to incorrect geometry calculations
6. **Parser Confusion**: KEGG parser may be creating spurious visual lines (place-to-place relations) that are NOT Arc objects but pure graphical lines

### Root Cause

The arc rendering pipeline calculates geometry in the wrong order:
```
CURRENT (WRONG):
1. Calculate center-to-center line
2. Draw line
3. Draw arrow at endpoint
4. Visual workaround to hide extremities

CORRECT:
1. Calculate center-to-center direction
2. Find perimeter intersection points (actual start/end)
3. Calculate true arc dimensions
4. Draw line from perimeter to perimeter
5. Draw arrow at perimeter endpoint
```

---

## Proposed Solution

### Phase 0: KEGG Parser Investigation & Cleanup

**CRITICAL FIRST STEP**: Before refactoring arc geometry, we must ensure the parser isn't creating spurious visual elements.

#### 0.1 Investigation: Spurious Lines

**Hypothesis**: KEGG parser may be rendering place-to-place KEGG relations as pure graphical lines (not Arc objects).

**Evidence**:
- User reports lines that are NOT selectable
- Lines do NOT respond to context menu
- These lines don't inherit from Arc API
- Analysis shows data model has valid arcs only, but GUI shows extra lines

**Investigation Steps**:
1. Check if KEGG relations (PPrel, ECrel, GErel, PCrel) are being visualized
2. Search for any Cairo drawing code outside of Arc.render()
3. Check if KEGG graphics elements (type="line") are being drawn
4. Verify no legacy rendering code creates place-to-place lines

**Files to Inspect**:
- `src/shypn/importer/kegg/kgml_parser.py` - Does it parse relations?
- `src/shypn/importer/kegg/pathway_converter.py` - Does it render relations?
- `src/shypn/helpers/model_canvas_loader.py` - Any extra drawing in `_on_draw()`?
- `src/shypn/helpers/kegg_import_panel.py` - Does import add visual elements?

#### 0.2 Parser Cleanup

**Goal**: Ensure parser only creates valid Petri net objects (Places, Transitions, Arcs).

**Rules**:
1. **KEGG Relations** → DO NOT render as lines
   - Relations (PPrel, ECrel, etc.) are metadata, not arcs
   - Parser should store relations for future use but NOT visualize
   
2. **KEGG Graphics (type="line")** → DO NOT render
   - Graphics elements are visual hints, not model elements
   - Ignore line graphics from KGML file
   
3. **Only Reactions** → Create Arcs
   - Arcs only created from KEGG reactions (substrate/product)
   - All arcs must be Place↔Transition (bipartite property)

**Implementation**:
```python
# In pathway_converter.py
def convert(self, pathway: KEGGPathway, options: ConversionOptions) -> DocumentModel:
    # ONLY create arcs from reactions
    for reaction in pathway.reactions:
        arcs = self.arc_builder.create_arcs(...)
    
    # DO NOT process pathway.relations
    # DO NOT visualize KEGG graphics lines
    # DO NOT create place-to-place connections
    
    return document
```

#### 0.3 Verification Tests

**Create Test**: `test_kegg_parser_no_spurious_lines.py`
```python
def test_parser_creates_only_valid_arcs():
    """Ensure parser creates NO place-to-place arcs."""
    pathway = parse_kegg_file("hsa00010.xml")
    document = convert_pathway(pathway)
    
    # Verify NO place-to-place arcs
    for arc in document.arcs:
        assert not (is_place(arc.source) and is_place(arc.target))
    
def test_parser_ignores_relations():
    """Ensure KEGG relations are NOT converted to arcs."""
    pathway = parse_kegg_file("hsa00010.xml")
    assert len(pathway.relations) > 0  # File has relations
    
    document = convert_pathway(pathway)
    # Number of arcs should match reactions only, not relations
    expected_arcs = count_reaction_arcs(pathway.reactions)
    assert len(document.arcs) == expected_arcs
```

**Expected Result**: All tests pass, confirming parser creates only valid Petri net arcs.

---

### Phase 1: Arc Geometry Refactoring

#### 1.1 Core Geometry Calculation

**New Method: `calculate_arc_geometry()`**
```python
def calculate_arc_geometry(self) -> ArcGeometry:
    """Calculate true arc geometry with perimeter clipping.
    
    Returns:
        ArcGeometry with:
        - start_point: (x, y) on source perimeter
        - end_point: (x, y) on target perimeter  
        - direction: normalized direction vector
        - length: actual arc length
        - control_points: for curved arcs
    """
```

**Implementation Steps:**
1. Get source/target center positions
2. Calculate direction vector (center to center)
3. Find intersection with source object perimeter (start point)
4. Find intersection with target object perimeter (end point)
5. Calculate actual arc length (perimeter to perimeter)
6. For curved arcs: calculate control points based on perimeter points

#### 1.2 Perimeter Intersection

**New Module: `src/shypn/utils/geometry.py`**
```python
def find_perimeter_intersection(
    obj: Union[Place, Transition],
    center_x: float,
    center_y: float,
    direction_x: float,
    direction_y: float
) -> tuple[float, float]:
    """Find where a ray from center intersects object perimeter.
    
    Args:
        obj: Place or Transition object
        center_x, center_y: Object center
        direction_x, direction_y: Normalized direction vector
        
    Returns:
        (x, y): Intersection point on perimeter
    """
```

**Implementations:**
- **Circle (Place)**: Ray-circle intersection
- **Rectangle (Transition)**: Ray-rectangle intersection (4 edges)

#### 1.3 Arc Rendering Pipeline

**New Order:**
```python
def render(self, cr, transform=None, zoom=1.0):
    # 1. Calculate geometry (perimeter-to-perimeter)
    geometry = self.calculate_arc_geometry()
    
    # 2. Apply parallel arc offset (if needed)
    if self.has_parallel_arcs():
        geometry = self.apply_parallel_offset(geometry)
    
    # 3. Draw line (start_point to end_point)
    if self.is_curved:
        self.draw_curved_line(cr, geometry, zoom)
    else:
        self.draw_straight_line(cr, geometry, zoom)
    
    # 4. Draw arrowhead at end_point
    self.draw_arrowhead(cr, geometry.end_point, geometry.direction, zoom)
    
    # 5. Draw weight label (if > 1)
    if self.weight > 1:
        self.draw_weight_label(cr, geometry, zoom)
```

---

### Phase 2: Remove Legacy Features

#### 2.1 Remove Auto-Curved Parallel Arcs

**Files to Modify:**
- `src/shypn/data/model_canvas_manager.py`
  - Remove `_auto_convert_parallel_arcs_to_curved()`
  - Remove automatic curved conversion in `add_arc()`
  
**Replacement:**
- User manually transforms arcs to curved via context menu
- Parallel arcs remain straight with visual offset

#### 2.2 Simplify Parallel Arc Detection

**Keep:**
- `detect_parallel_arcs()` - needed for visual offset
- `calculate_arc_offset()` - needed for spacing

**Remove:**
- Automatic curve conversion logic
- CurvedArc auto-creation on parallel detection

---

### Phase 3: Arc Transformation System

#### 3.1 Manual Arc Transformation

**User Workflow:**
1. User draws arc (always straight initially)
2. User right-clicks → "Transform to Curved"
3. Arc becomes curved with editable control handle
4. User can draw opposite arc
5. User manually curves opposite arc if desired

**Implementation:**
- Keep existing transformation handlers
- Remove automatic triggering
- Add menu option: "Transform Arc → Curved/Straight"

#### 3.2 Arc Types Hierarchy

```
Arc (base class)
├── Properties: source, target, weight, color, width
├── calculate_arc_geometry() → perimeter-clipped geometry
└── render() → geometry-based rendering

User-created arcs are always Arc (straight)
User transforms to curved via TransformationHandler
```

---

### Phase 4: Fix Hit Detection

#### 4.1 Geometry-Based Hit Detection

**Current Problem:**
```python
# contains_point() uses center-to-center geometry
src_x, src_y = self.source.x, self.source.y  # CENTER
tgt_x, tgt_y = self.target.x, self.target.y  # CENTER
# Distance calculation wrong for long arcs!
```

**Fix:**
```python
def contains_point(self, x: float, y: float) -> bool:
    # 1. Get actual arc geometry (perimeter-clipped)
    geometry = self.calculate_arc_geometry()
    
    # 2. Use actual start/end points for hit detection
    start_x, start_y = geometry.start_point
    end_x, end_y = geometry.end_point
    
    # 3. Distance calculation now correct
    # ... existing distance logic ...
```

This will fix the "non-selectable long arcs" issue!

---

## Implementation Plan

### Step 0: KEGG Parser Investigation (Week 0 - PRIORITY)
- [ ] **Investigate spurious lines issue**
  - [ ] Check if KEGG relations are being rendered
  - [ ] Check if KEGG graphics lines are being drawn
  - [ ] Search for Cairo drawing outside Arc.render()
  - [ ] Verify _on_draw() only calls obj.render() for valid objects
  
- [ ] **Parser cleanup**
  - [ ] Ensure pathway_converter.py ignores relations
  - [ ] Ensure no graphics "line" elements are rendered
  - [ ] Verify only reactions create arcs
  - [ ] Add validation: NO place-to-place arcs allowed
  
- [ ] **Create verification tests**
  - [ ] `test_kegg_parser_no_spurious_lines.py`
  - [ ] Test that parser creates only valid Place↔Transition arcs
  - [ ] Test that relations count ≠ arcs count
  - [ ] Test on multiple KEGG pathways (hsa00010, hsa00020, hsa00030)

### Step 1: Core Geometry (Week 1)
- [ ] Create `geometry.py` utility module
- [ ] Implement `find_perimeter_intersection()` for circles
- [ ] Implement `find_perimeter_intersection()` for rectangles
- [ ] Add unit tests for perimeter intersection

### Step 2: Arc Geometry Refactoring (Week 1-2)
- [ ] Add `calculate_arc_geometry()` to Arc class
- [ ] Define `ArcGeometry` dataclass/namedtuple
- [ ] Update `render()` to use geometry
- [ ] Update `contains_point()` to use geometry

### Step 3: Remove Legacy Features (Week 2)
- [ ] Remove `_auto_convert_parallel_arcs_to_curved()`
- [ ] Remove automatic curve conversion in `add_arc()`
- [ ] Test that parallel arcs still get visual offset
- [ ] Update documentation

### Step 4: Testing & Validation (Week 2-3)
- [ ] Test arc rendering with new geometry
- [ ] Test arc selection (especially long arcs)
- [ ] Test parallel arc offset without auto-curving
- [ ] Test manual arc transformation
- [ ] Test on real KEGG pathways (hsa00010, hsa00020)
- [ ] **Verify NO spurious lines appear after parser cleanup**

### Step 5: Documentation (Week 3)
- [ ] Update arc rendering documentation
- [ ] Document new geometry calculation
- [ ] Add user guide for manual arc transformation
- [ ] Create migration guide for existing pathways
- [ ] **Document parser rules: only reactions → arcs**

---

## Benefits

### 1. Correct Geometry
- ✅ Arcs drawn from perimeter to perimeter
- ✅ Accurate arc length calculations
- ✅ No visual workarounds needed
- ✅ Proper dimensions for all arc types

### 2. Selectable Long Arcs
- ✅ Hit detection uses actual geometry
- ✅ Long arcs become clickable/selectable
- ✅ Context menu works for all arcs

### 3. Cleaner Code
- ✅ Remove legacy auto-curved parallel logic
- ✅ Single rendering pipeline
- ✅ Geometry calculation separated from rendering
- ✅ Better maintainability

### 4. Better User Control
- ✅ User decides when to curve arcs
- ✅ More predictable behavior
- ✅ Easier to understand workflow

---

## Risks & Mitigation

### Risk 1: Breaking Existing Pathways
**Impact**: Saved `.shy` files may render differently
**Mitigation**:
- Implement backward compatibility layer
- Add migration tool for old files
- Version field in file format

### Risk 2: Performance Impact
**Impact**: Perimeter calculations on every render
**Mitigation**:
- Cache geometry calculations
- Only recalculate when positions change
- Use dirty flags

### Risk 3: Complex Geometry Edge Cases
**Impact**: Edge cases in perimeter intersection
**Mitigation**:
- Comprehensive unit tests
- Fallback to center points if intersection fails
- Logging for debugging

---

## File Changes Summary

### New Files
- `src/shypn/utils/geometry.py` - Perimeter intersection utilities
- `tests/test_arc_geometry.py` - Geometry unit tests
- `tests/test_kegg_parser_no_spurious_lines.py` - **Parser validation tests**
- `ARC_GEOMETRY_MIGRATION_GUIDE.md` - Migration documentation

### Modified Files
- `src/shypn/netobjs/arc.py` - Add `calculate_arc_geometry()`, update `render()` and `contains_point()`
- `src/shypn/data/model_canvas_manager.py` - Remove auto-curved parallel logic
- `src/shypn/netobjs/place.py` - Add perimeter intersection support
- `src/shypn/netobjs/transition.py` - Add perimeter intersection support
- `src/shypn/importer/kegg/pathway_converter.py` - **Verify no relation rendering**
- `src/shypn/importer/kegg/kgml_parser.py` - **Verify no graphics line rendering**

### Removed Code
- `_auto_convert_parallel_arcs_to_curved()` method
- Automatic curved arc conversion in `add_arc()`
- Legacy workarounds for arc extremities

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 0: Parser Investigation** | **3 days** | **No spurious lines from parser** |
| Phase 1: Core Geometry | 1 week | Working perimeter intersection |
| Phase 2: Remove Legacy | 3 days | Clean parallel arc code |
| Phase 3: Arc Transform | 2 days | Manual transformation only |
| Phase 4: Hit Detection | 2 days | Selectable long arcs |
| Phase 5: Testing | 1 week | All tests passing |
| Phase 6: Documentation | 2 days | Complete docs |

**Total: ~3.5 weeks** (includes parser investigation)

---

## Success Criteria

- [ ] **KEGG parser creates NO spurious place-to-place lines**
- [ ] **KEGG relations are NOT rendered as visual lines**
- [ ] All arcs render from perimeter to perimeter
- [ ] Long arcs (>500px) are selectable
- [ ] Context menu works on all arcs
- [ ] No automatic curved arc conversion
- [ ] Parallel arcs have visual offset but remain straight
- [ ] User can manually transform any arc to curved
- [ ] All existing tests pass
- [ ] Performance not degraded (< 5% slower)

---

## Next Steps

1. **PRIORITY: Phase 0** - Investigate spurious lines from KEGG parser
2. **Review this plan** - Get stakeholder approval
3. **Create feature branch** - `feature/arc-geometry-refactor`
4. **Implement Phase 0** - Parser cleanup FIRST
5. **Then Phase 1** - Start with geometry utilities after parser is clean
6. **Incremental testing** - Test after each phase
7. **Commit frequently** - Small, atomic commits
8. **Document changes** - Update docs as we go

---

## Questions for Discussion

1. **KEGG Relations**: Should we store them in the model for future use, or completely ignore them during parsing?
2. Should we support **backward compatibility** for old `.shy` files, or require re-import?
3. Do we want to **cache geometry** calculations, or recalculate on every render?
4. Should perimeter intersection be **exact** (mathematically precise) or **approximate** (faster)?
5. What should happen if perimeter intersection **fails** (degenerate case)?
6. **Graphics elements**: Should KEGG graphics (colors, shapes) be preserved as metadata even if lines are ignored?

---

## Conclusion

This revision will:
1. **FIRST**: Investigate and eliminate spurious place-to-place lines from KEGG parser
2. Fix the fundamental geometric issues with arcs (perimeter-based rendering)
3. Make long arcs selectable with correct hit detection
4. Remove legacy auto-curved logic
5. Give users full control over arc appearance

The implementation starts with **Phase 0 (Parser Investigation)** as the highest priority, since spurious lines affect usability immediately. After confirming the parser is clean, we proceed with geometry refactoring.

**Priority**: **CRITICAL** - Phase 0 must be done first (non-selectable spurious lines)
**Complexity**: MEDIUM - Requires geometry calculations but no algorithmic complexity
**Risk**: LOW - Changes are localized, backward compatibility possible
