# Spurious Lines Investigation - Summary

**Date**: October 10, 2025  
**Status**: 🔍 **ACTIVE INVESTIGATION** - Root cause not yet confirmed  
**Priority**: HIGH - Visual display bug affecting pathway readability

## Issue Description

**Symptoms:**
- Long straight lines appearing in GUI connecting distant compounds
- Lines are **NOT selectable** (no context menu, cannot click)
- Lines **persist** across save/load cycles
- Lines appear **immediately after import**, before any user interaction
- Lines span across the entire pathway diagram

**Example**: User sees visual chain C00036 → C01159 → C00118 → C00668 → PDHA1  
But data shows these are NOT directly connected!

## Investigation Results

### ✅ What We've Confirmed

1. **Data model is 100% CORRECT**
   - No place-to-place arcs in saved files
   - No transition-to-transition arcs  
   - All arcs follow valid Place ↔ Transition pattern
   - Verified with multiple diagnostic scripts

2. **Arc objects are correct**
   - 73 arcs total in test pathway
   - All have valid source/target references
   - No duplicate arc IDs
   - No invalid arc types

3. **Transitions are adequately sized**
   - After fix: minimum 15×15 pixels
   - All 34 transitions > 150 sq px
   - Transitions are visible at normal zoom

4. **Not KEGG relations**
   - KEGG relations parsed but NOT converted to arcs
   - No relation rendering code found

5. **Example compound C00036**
   - Has only **1 arc** in data (to PCK1 transition)
   - But user sees **multiple lines** in GUI
   - **Proves**: Lines are rendering artifacts, not data objects

### 🐛 Bugs Found So Far

1. **Duplicate `get_all_objects()` method** (FIXED)
   - Two method definitions in ModelCanvasManager
   - Second definition overwrote first
   - Could cause inconsistent object ordering
   - **Status**: Fixed in commit 1402789

2. **Transition size too small** (FIXED)
   - Original size: ~10×10 pixels (invisible)
   - Fixed: Minimum 15×15 pixels
   - **Status**: Fixed in commit 0a4f1df

### ❓ Current Hypothesis

Based on the screenshot showing **long straight lines** spanning the pathway:

**Theory**: Arcs are being drawn with **cached/old endpoint positions** that don't update when layout moves objects.

**Evidence:**
- Lines appear to connect to where objects *would have been* at KEGG original positions
- Lines persist after layout operations
- Lines span unreasonably long distances (300-1000+ pixels)
- Data shows correct short-distance connections

**Possible causes:**
1. **Arc rendering** uses old cached positions instead of live object positions
2. **Layout operation** creates temporary visual arcs that aren't cleaned up
3. **Import process** creates visual elements at KEGG positions that persist
4. **Cairo rendering state** not properly reset between frames

## Diagnostic Scripts Created

All in project root:

1. `diagnose_all_spurious_lines.py` - Comprehensive diagnostic
2. `check_arc_endpoints.py` - Verify arc source/target
3. `check_specific_chain.py` - Analyze compound chains
4. `visualize_connections.py` - ASCII visualization of connections
5. `check_kegg_relations_rendering.py` - Check KEGG relations
6. `debug_arc_rendering.py` - Add logging to Arc.render()

## Next Steps

### Immediate Actions (User Testing)

1. **Test arc selection:**
   ```
   - Click on a spurious line
   - Does it select? (Should: NO - confirmed not selectable)
   - Does it have properties?
   ```

2. **Test zoom behavior:**
   ```
   - Zoom in to 400-500%
   - Do spurious lines change? Scale properly?
   - Do they originate from exact object centers?
   ```

3. **Test fresh import:**
   ```
   - Import pathway
   - Take screenshot BEFORE layout
   - Apply layout
   - Take screenshot AFTER layout
   - Compare line positions
   ```

### Code Investigation

1. **Add debug logging to Arc.render():**
   ```python
   # In arc.py, render() method
   print(f"Rendering {self.id}: ({self.source.x}, {self.source.y}) → ({self.target.x}, {self.target.y})")
   ```

2. **Check if arcs store old positions:**
   ```bash
   grep -r "start_x\|end_x\|_x\|_y" src/shypn/netobjs/arc.py
   ```

3. **Check layout code for temporary arcs:**
   ```bash
   grep -r "add_arc\|create_arc" src/shypn/edit/graph_layout/
   ```

4. **Check if rendering state persists:**
   ```python
   # In model_canvas_loader.py, _on_draw()
   # Add at start:
   print(f"Drawing frame: {len(manager.arcs)} arcs")
   ```

### Potential Fixes

**If arcs use cached positions:**
```python
# Add to Arc class
def invalidate_cache(self):
    """Clear any cached rendering data."""
    if hasattr(self, '_cached_path'):
        del self._cached_path
```

**If layout creates ghost arcs:**
```python
# In layout engines, ensure cleanup:
def apply_layout(self, ...):
    try:
        # ... layout code ...
    finally:
        # Clear any temporary visual elements
        manager.clear_temp_visuals()
```

**If import creates visual elements:**
```python
# In kegg_import_panel.py, after import:
manager.arcs = list(document_model.arcs)  # Ensure fresh list
manager.clear_rendering_cache()  # Clear any visual state
```

## Files Modified

### Core Fixes

1. **src/shypn/importer/kegg/reaction_mapper.py**
   - Added minimum transition size (15×15 pixels)
   - Both single and split reversible transitions

2. **src/shypn/data/model_canvas_manager.py**
   - Removed duplicate `get_all_objects()` method

### Documentation

1. **SPURIOUS_LINES_DEBUG_GUIDE.md** - Debugging guide
2. **PLACE_TO_PLACE_ARC_INVESTIGATION.md** - Investigation log (updated)

## Test Data

**File**: `workspace/projects/diagnose_all_spurious.shypn.shyn`
- 26 places
- 34 transitions  
- 73 arcs (all valid)
- Shows spurious lines in GUI
- Data is correct

## Commits

- `0a4f1df` - fix: enforce minimum transition size (15×15px)
- `1402789` - fix: remove duplicate get_all_objects() method
- `859f26b` - refactor: enhance isolated compound filtering

## Status: Awaiting User Feedback

Need user to:
1. Try clicking/selecting spurious lines
2. Test zoom behavior
3. Compare before/after layout screenshots
4. Test with fresh pathway import

Once we understand the exact rendering behavior, we can pinpoint the code responsible and fix it.
