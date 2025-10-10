# Spurious Lines to Text Labels - Analysis

**Date**: October 10, 2025  
**Issue**: Blue lines appearing from selected place to arc weight text and place labels

## Problem Description

### Issue 1: Lines from Place to Arc Weight Text
When editing weight text on curved arcs:
1. User selects a Place (P)
2. User edits weight text on arc P→T
3. A blue line appears from P's center to the weight text position
4. Similar to the "spurious arc" issue we previously fixed

### Issue 2: Lines from Place to Place Label Text  
In pathway rendering (KEGG import):
1. Long lines appear in rendered pathways
2. These lines go from Place center to TEXT LABEL of another place
3. Instead of going Place center to Place center
4. Suggests Cairo path state contamination

## Root Cause Analysis

### Hypothesis 1: Cairo Path Not Cleared After Text Rendering

When rendering text in Cairo:
```python
cr.move_to(text_x, text_y)
cr.show_text("label")
```

The `cr.move_to()` call sets the "current point" in Cairo's path. If the path is not explicitly cleared after text rendering, the next `cr.line_to()` or `cr.stroke()` call will draw from that text position.

**Evidence**:
- Lines going **TO** text positions (not FROM)
- Occurs after text editing operations
- Similar pattern to previous "spurious arc" bug

### Hypothesis 2: Missing `cr.new_path()` After Text Operations

In `curved_arc.py`, line 296, we have:
```python
# Ensure clean state for next rendering operation
cr.new_path()
```

This clears the path AFTER arc rendering. However, the `_render_weight_curved()` method also does text rendering:

```python
# Line 397 in curved_arc.py
cr.move_to(text_x, text_y)
cr.set_source_rgb(0, 0, 0)  # Black text
cr.show_text(text)

# Restore context (clear any paths/state)
cr.restore()
```

The `cr.restore()` SHOULD clear the path, but there may be cases where the path persists.

### Hypothesis 3: Place Label Rendering Leaves Path State

In `place.py`, line 140:
```python
def _render_label(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", 0, 0)
    cr.set_font_size(12 / zoom)
    extents = cr.text_extents(self.label)
    cr.move_to(x - extents.width / 2, y + radius + 15 / zoom)
    cr.show_text(self.label)
```

**MISSING**: No `cr.new_path()` after text rendering!

This is the likely culprit. After rendering a place label, the current path point is set to the text position. If the next object rendered starts with `cr.line_to()` or doesn't clear the path, it will draw a line from that text position.

## Similar Issue Found and Fixed Previously

### BUGFIX_SPURIOUS_ARC_ON_DIALOG_CLOSE.md

We previously fixed a similar issue where spurious arcs were created when dialogs closed:

**Problem**: Arc creation state was not cleared, causing lines to be drawn from the last selected place

**Solution**: Added explicit state clearing:
```python
# Clear arc creation state to prevent spurious arc creation
self.arc_creation_source = None
self.arc_creation_temp_line = None
```

**Location**: `src/shypn/helpers/model_canvas_loader.py` lines 1897, 1917, 1984

## Issue Locations

### Primary Suspects

1. **Place label rendering** (`src/shypn/netobjs/place.py`, line 135-141)
   ```python
   def _render_label(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
       cr.set_source_rgb(0, 0, 0)
       cr.select_font_face("Sans", 0, 0)
       cr.set_font_size(12 / zoom)
       extents = cr.text_extents(self.label)
       cr.move_to(x - extents.width / 2, y + radius + 15 / zoom)
       cr.show_text(self.label)
       # MISSING: cr.new_path()
   ```

2. **Place token rendering** (`src/shypn/netobjs/place.py`, line 117-125)
   ```python
   def _render_tokens(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
       # ...
       cr.move_to(text_x, text_y)
       cr.show_text(text)
       cr.fill()
       # MISSING: cr.new_path()
   ```

3. **Curved arc weight rendering** (`src/shypn/netobjs/curved_arc.py`, line 394-400)
   ```python
   # Draw text
   cr.move_to(text_x, text_y)
   cr.set_source_rgb(0, 0, 0)
   cr.show_text(text)
   
   # Restore context (clear any paths/state)
   cr.restore()
   # Should be OK due to cr.restore(), but let's verify
   ```

4. **Arc weight rendering** (`src/shypn/netobjs/arc.py`, line 428-432)
   ```python
   # Draw text
   cr.move_to(text_x, text_y)
   cr.set_source_rgb(0, 0, 0)
   cr.show_text(text)
   
   # Restore context (clear any paths/state)
   cr.restore()
   ```

5. **Inhibitor arc weight rendering** (`src/shypn/netobjs/inhibitor_arc.py`, line 399-403)
   ```python
   # Draw text
   cr.move_to(text_x, text_y)
   cr.set_source_rgb(0, 0, 0)
   cr.show_text(text)
   
   # Restore context (clear any paths/state)
   cr.restore()
   ```

6. **Curved inhibitor arc weight rendering** (`src/shypn/netobjs/curved_inhibitor_arc.py`, line 273-277)
   ```python
   # Draw text
   cr.move_to(text_x, text_y)
   cr.set_source_rgb(0, 0, 0)
   cr.show_text(text)
   
   # Restore context (clear any paths/state)
   cr.restore()
   ```

### Secondary Suspects

7. **Transition label rendering** - Check if similar issue exists

## Solution Strategy

### Fix 1: Add `cr.new_path()` After All Text Rendering

**Priority**: HIGH  
**Rationale**: Defensive programming - ensure path state is always clean

**Locations to fix**:
1. `src/shypn/netobjs/place.py` - After `_render_label()` and `_render_tokens()`
2. Verify all arc weight rendering methods have proper cleanup

**Implementation**:
```python
def _render_label(self, cr, x: float, y: float, radius: float, zoom: float = 1.0):
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", 0, 0)
    cr.set_font_size(12 / zoom)
    extents = cr.text_extents(self.label)
    cr.move_to(x - extents.width / 2, y + radius + 15 / zoom)
    cr.show_text(self.label)
    # Clear path to prevent spurious lines to text position
    cr.new_path()
```

### Fix 2: Verify `cr.save()`/`cr.restore()` Pattern

The arc weight rendering methods use:
```python
cr.save()
# ... rendering ...
cr.restore()
```

This SHOULD clear the path state, but let's verify:
- Check Cairo documentation: Does `cr.restore()` clear current point?
- Add defensive `cr.new_path()` before `cr.restore()` if needed

### Fix 3: Add `cr.new_path()` at Start of Each Render Method

**Alternative**: Instead of cleaning up after text, clear at the start of each render:

```python
def render(self, cr, transform=None, zoom=1.0):
    # Ensure clean state before rendering
    cr.new_path()
    # ... rest of rendering ...
```

**Pros**: More defensive, prevents issues from previous rendering
**Cons**: May mask bugs in other code

## Testing Strategy

### Test 1: Visual Inspection
1. Import KEGG pathway (e.g., glycolysis)
2. Look for long lines going to place labels instead of place centers
3. Check if lines disappear after fix

### Test 2: Arc Weight Editing
1. Create simple net: P1 → T1 → P2
2. Make arc P1→T1 curved
3. Select P1
4. Edit weight on arc P1→T1
5. Check for blue line from P1 to weight text
6. Verify line disappears after fix

### Test 3: Regression Test
1. Ensure existing functionality still works
2. No new visual artifacts
3. Selection still highlights correctly

## Implementation Plan

### Phase 1: Quick Fix (Immediate)
1. ✅ **Analyze issue** - Document root cause
2. ⏳ **Add `cr.new_path()` to Place rendering** - Fix place.py
3. ⏳ **Verify arc weight rendering** - Check all arc classes
4. ⏳ **Test with real pathways** - Glycolysis, etc.

### Phase 2: Comprehensive Fix (With Arc Refactoring)
1. During Phase 1-6 arc geometry refactoring
2. Establish consistent pattern for all rendering
3. Add defensive `cr.new_path()` at strategic points
4. Document best practices

## Related Issues

### Fixed Previously
- **BUGFIX_SPURIOUS_ARC_ON_DIALOG_CLOSE.md** - Similar state contamination issue
- Arc creation state not cleared causing spurious arcs

### Current Issue
- Cairo path state contamination from text rendering
- Lines drawn from text positions instead of object centers

### Pattern
Both issues involve:
1. State not being properly cleared
2. Next operation uses stale state
3. Results in spurious visual artifacts (lines)

## Best Practices Going Forward

### Cairo Rendering Pattern

```python
def render(self, cr, transform=None, zoom=1.0):
    """Safe rendering pattern."""
    # 1. Save state if needed
    cr.save()
    
    # 2. Clear any existing path
    cr.new_path()
    
    # 3. Do rendering
    cr.move_to(x, y)
    cr.line_to(x2, y2)
    cr.stroke()
    
    # 4. Clean up
    cr.new_path()
    
    # 5. Restore if saved
    cr.restore()
```

### Text Rendering Pattern

```python
def _render_text(self, cr, x, y, text):
    """Safe text rendering."""
    cr.save()
    cr.move_to(x, y)
    cr.show_text(text)
    cr.new_path()  # Clear current point after text
    cr.restore()
```

## Priority

**PRIORITY: HIGH**

This issue affects:
- User experience (confusing visual artifacts)
- Debugging (spurious lines make it hard to understand net structure)
- Professional appearance of tool

**Effort**: LOW (simple fix, add `cr.new_path()` calls)

**Risk**: LOW (defensive, can't break existing rendering)

**Recommendation**: Fix immediately before Phase 1 arc geometry refactoring

---

**Next Steps**:
1. Implement Fix 1 (add `cr.new_path()` to place.py)
2. Test with KEGG pathways
3. Verify arc weight editing works correctly
4. Document fix in completion report

**Estimated Time**: 30 minutes to fix, 30 minutes to test

---

**Status**: ANALYZED - Ready for Implementation  
**Assignee**: Ready for immediate fix  
**Due**: Before Phase 1 arc geometry refactoring
