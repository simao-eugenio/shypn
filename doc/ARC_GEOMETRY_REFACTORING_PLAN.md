# Arc Geometry Refactoring - Phase 1-6 Plan

**Start Date**: 2025-10-10  
**Estimated Duration**: 3-4 weeks  
**Status**: Phase 1 - Starting

---

## Overview

Refactor arc geometry system to use **perimeter-to-perimeter** calculations instead of center-to-center. This will provide:
- ✓ Accurate arc endpoints on object boundaries
- ✓ Correct hit detection along entire arc path
- ✓ Proper handling of curved arcs
- ✓ Support for different object shapes (circles, rectangles, polygons)

---

## Current Problems

### Issue 1: Center-to-Center Geometry
**Current Behavior**: Arcs calculated from place/transition centers
**Problem**: Arc endpoints don't align with object edges
**Impact**: Visual misalignment, confusing to users

### Issue 2: Hit Detection
**Current Behavior**: Uses bounding box or simple distance checks
**Problem**: Doesn't follow actual arc path, especially for curves
**Impact**: Hard to select arcs, accidental selections

### Issue 3: Curved Arc Handling
**Current Behavior**: Curves may not account for object shapes
**Problem**: Bezier control points calculated without boundary intersection
**Impact**: Curves may penetrate objects or miss edges

---

## Phased Implementation Plan

### Phase 1: Analysis & Foundation (Days 1-2) ← **WE ARE HERE**

**Objective**: Understand current architecture and create test infrastructure

**Tasks**:
1. ✓ Create this planning document
2. ⚠️ Analyze current arc geometry code
3. ⚠️ Document existing arc types and their behavior
4. ⚠️ Create comprehensive test cases
5. ⚠️ Set up visual test harness for interactive testing

**Deliverables**:
- Architecture analysis document
- Test suite with visual validation
- Baseline "before" screenshots

**Testing**: You draw test cases, I analyze current behavior

---

### Phase 2: Perimeter Intersection Mathematics (Days 3-5)

**Objective**: Implement boundary intersection for all shape types

**Tasks**:
1. Create `geometry_utils.py` module with intersection functions
2. Implement circle-to-line intersection
3. Implement rectangle-to-line intersection  
4. Implement polygon-to-line intersection (for custom shapes)
5. Add unit tests for each intersection type

**Deliverables**:
- `src/shypn/utils/geometry_utils.py`
- Unit tests for intersection calculations
- Visual validation of intersection points

**Testing**: You draw arcs between various shapes, verify endpoints

---

### Phase 3: Straight Arc Refactoring (Days 6-9)

**Objective**: Refactor straight arcs to use perimeter-to-perimeter

**Tasks**:
1. Modify `Arc` class to use intersection calculations
2. Update arc rendering to start/end at boundaries
3. Fix arc serialization/deserialization
4. Update hit detection for straight arcs
5. Regression test all existing models

**Deliverables**:
- Refactored `Arc` class
- Updated rendering code
- All existing models still work

**Testing**: You load existing models, verify arcs render correctly

---

### Phase 4: Curved Arc Refactoring (Days 10-14)

**Objective**: Refactor curved arcs with proper boundary handling

**Tasks**:
1. Modify `CurvedArc` class for perimeter intersections
2. Recalculate Bezier control points based on boundaries
3. Update curved arc rendering
4. Fix hit detection along Bezier curve
5. Handle arc curvature parameter correctly

**Deliverables**:
- Refactored `CurvedArc` class
- Accurate Bezier rendering
- Curve hit detection working

**Testing**: You draw curved arcs, adjust curvature, verify behavior

---

### Phase 5: Hit Detection System (Days 15-18)

**Objective**: Implement accurate hit detection for all arc types

**Tasks**:
1. Create `arc_hit_detection.py` module
2. Implement point-to-line distance for straight arcs
3. Implement point-to-bezier distance for curved arcs
4. Add tolerance zone for easier selection
5. Optimize hit detection performance

**Deliverables**:
- Robust hit detection system
- Performance benchmarks
- Visual feedback for hit zones

**Testing**: You try selecting arcs in various positions

---

### Phase 6: Integration & Polish (Days 19-21)

**Objective**: Integrate all changes and polish the system

**Tasks**:
1. Update all arc transformation handlers
2. Fix arc creation/editing workflows
3. Update arc properties dialog
4. Performance optimization
5. Comprehensive regression testing
6. Documentation updates

**Deliverables**:
- Fully integrated system
- Updated documentation
- Performance report
- Complete test coverage

**Testing**: Full workflow testing - create, edit, transform, save, load

---

## Phase 1 - Detailed Task List

### Task 1.1: Analyze Current Arc Architecture ← **STARTING HERE**

Let me examine the current arc implementation:

**Files to analyze**:
- `src/shypn/netobjs/arc.py` - Straight arc class
- `src/shypn/netobjs/curved_arc.py` - Curved arc class
- Arc rendering methods
- Arc hit detection methods

**Questions to answer**:
1. How are arc endpoints currently calculated?
2. What geometry information do Place/Transition provide?
3. How is rendering done (Cairo paths)?
4. What's the current hit detection algorithm?
5. How are arcs serialized/deserialized?

Let me start by examining the code...

---

## Interactive Testing Protocol

For each phase, we'll follow this protocol:

### 1. You Draw
- Create test cases in the application
- Try different configurations
- Screenshot interesting cases

### 2. I Analyze
- Check console output
- Examine geometry calculations
- Identify issues

### 3. I Fix
- Make code changes
- Run unit tests
- Commit changes

### 4. You Test
- Verify the fix works
- Report "works" or "doesn't work"
- If doesn't work, we iterate

### 5. Move to Next
- Once confirmed working, proceed to next task
- Document what was fixed

---

## Success Criteria

### Phase 1 Success:
- [ ] All arc types documented
- [ ] Current behavior understood
- [ ] Test cases defined
- [ ] Visual test harness working

### Phase 2 Success:
- [ ] All intersection types implemented
- [ ] Unit tests passing
- [ ] Visual validation confirms accuracy

### Phase 3 Success:
- [ ] Straight arcs use perimeter intersections
- [ ] All existing models load correctly
- [ ] Arc endpoints align with object edges

### Phase 4 Success:
- [ ] Curved arcs use perimeter intersections
- [ ] Curvature adjustment works correctly
- [ ] Curves don't penetrate objects

### Phase 5 Success:
- [ ] Arc selection works accurately
- [ ] No false positives/negatives
- [ ] Performance is acceptable

### Phase 6 Success:
- [ ] All features integrated and working
- [ ] No regressions
- [ ] Documentation complete
- [ ] Code reviewed and optimized

---

## Risk Management

### Risk 1: Breaking Existing Models
**Mitigation**: 
- Maintain backward compatibility
- Convert old format to new on load
- Keep extensive test suite

### Risk 2: Performance Degradation
**Mitigation**:
- Benchmark before changes
- Optimize hot paths
- Use caching where appropriate

### Risk 3: Complex Edge Cases
**Mitigation**:
- Test each shape combination
- Handle degenerate cases gracefully
- Add fallback behavior

### Risk 4: Timeline Slip
**Mitigation**:
- Break work into small testable chunks
- Prioritize core functionality
- Defer polish if needed

---

## Next Steps

**Immediate Action**: Begin Task 1.1 - Analyze current arc architecture

I will now examine the current arc code and document how it works...
