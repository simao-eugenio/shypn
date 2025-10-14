# Layout Experiments Summary - October 14, 2025

## Status: WORK IN PROGRESS (Set Aside)

This document summarizes the hierarchical layout experiments that were attempted but are being set aside for later investigation.

---

## Git References

- **Commit:** `20a1d00` - "WIP: Layout experiments - setting aside for later"
- **Branch:** `feature/property-dialogs-and-simulation-palette`
- **Backup Branch:** `backup/layout-experiments-20251014`
- **Tag:** `v0.1.0-experimental`

To restore this state later:
```bash
git checkout backup/layout-experiments-20251014
# or
git checkout v0.1.0-experimental
```

---

## Objective

Apply hierarchical layout to ALL imported SBML pathways with:
1. Tree/forest structure (roots at top, descendants below)
2. Children centered under parents
3. Bounded canvas width (no coordinate stretching)
4. Straight arcs only (no curved arcs)

---

## What Was Attempted

### 1. **Hierarchical Layout Priority** ✅ DONE
- Modified `pathway_postprocessor.py` to ALWAYS use hierarchical layout first
- Removed cross-reference layout priority
- Result: All imports now use hierarchical layout

### 2. **Bounded Canvas Width** ✅ DONE
- Added `max_canvas_width = 1200.0` constraint in `hierarchical_layout.py`
- Adaptive spacing when layers exceed max width
- Result: No more infinitely wide layouts

### 3. **Coordinate Normalization** ✅ DONE
- Added `_normalize_coordinates()` method with 50px margins
- Ensures all coordinates are positive
- Extensive debug logging of coordinate ranges
- Result: Negative coordinates eliminated at layout stage

### 4. **Disabled Layout Optimizer** ✅ DONE
- Skip LayoutOptimizer for hierarchical layouts in `sbml_import_panel.py`
- Skip ArcRouter for hierarchical layouts
- Result: Post-processing doesn't corrupt hierarchical layouts

### 5. **Forced Straight Arcs** ✅ DONE
- Disabled `_auto_convert_parallel_arcs_to_curved()` in `model_canvas_manager.py`
- Force `is_curved = False` on all arcs during import
- Result: All arcs render as straight lines

### 6. **Tree Layout Algorithm** ❌ ATTEMPTED (Complex)
Attempted to position children under parents:
- Built parent-child relationship maps from reactions
- Tried to center children under parent average position
- Handled multiple parents (common in biochemical pathways)
- Result: TOO COMPLEX - biochemical pathways have multiple products/reactants

### 7. **Simple Fixed Layout** ✅ IMPLEMENTED (Final)
Reverted to simple approach:
- Fixed vertical spacing (150px between layers)
- Even horizontal distribution within each layer
- Centered at X=600, max width 1200px
- Result: Clean, predictable layout

---

## The Persistent Issue: SPURIOUS COORDINATES

### Problem
Despite all fixes, coordinates show as INCORRECT when displayed:
- **Expected:** `(383.7, 600.0)` 
- **Actual Display:** `(-2988.7, 4705.5)`

### What We Know
1. ✅ Hierarchical layout produces CORRECT coordinates
2. ✅ Normalization ensures all positive coordinates
3. ✅ Converter receives CORRECT coordinates
4. ❌ Manager/Display shows WRONG coordinates

### Debug Logging Added
Comprehensive coordinate tracking throughout pipeline:
- `🔍 HIERARCHICAL LAYOUT COORDINATES BEFORE NORMALIZATION`
- `🔍 CONVERTER INPUT (pathway.positions)`
- `🔍 AFTER CONVERTER`
- `🔍 BEFORE CANVAS LOADING`
- `🔍 AFTER list() COPY`
- `🔍 IMMEDIATELY AFTER LOADING`

### Theories (Unconfirmed)
1. **Viewport Transform?** - Some coordinate system conversion happening
2. **Property Getter?** - Place.x/Place.y might be computed properties
3. **Observer Pattern?** - `_notify_observers()` might trigger recalculation
4. **Cairo Transform?** - Rendering transform being applied to stored coordinates

### What Didn't Work
- Disabling curved arcs (not the cause)
- Normalizing coordinates (they were already correct)
- Skipping layout optimizer (it wasn't running)
- Tree centering algorithm (too complex for biochemical graphs)

---

## Files Modified

### Core Layout Changes
- `src/shypn/data/pathway/hierarchical_layout.py`
  - Tree algorithm attempted (lines 225-380)
  - Reverted to simple fixed layout
  - Added extensive debug logging

- `src/shypn/data/pathway/pathway_postprocessor.py`
  - Changed layout priority to hierarchical-first
  - Removed cross-reference priority

### Import Pipeline Changes
- `src/shypn/helpers/sbml_import_panel.py`
  - Skip enhancements for hierarchical layouts
  - Force straight arcs on load
  - Added 5 debug checkpoints

- `src/shypn/data/pathway/pathway_converter.py`
  - Added coordinate input logging
  - No algorithmic changes

### Arc Management Changes
- `src/shypn/data/model_canvas_manager.py`
  - Disabled `_auto_convert_parallel_arcs_to_curved()`
  - Prevents automatic arc curving

### CrossFetch Changes
- `src/shypn/crossfetch/sbml_enricher.py`
- `src/shypn/data/pathway/sbml_layout_resolver.py`
  - Removed from import workflow (computationally intractable)
  - Code preserved for future direct KEGG imports

### UI Changes
- `ui/panels/pathway_panel.ui`
  - Enrichment checkbox disabled

---

## Documentation Added

New documents created:
- `doc/CROSSFETCH_REMOVAL_DECISION.md`
- `doc/HIERARCHICAL_LAYOUT_FIX_COORDINATE_BOUNDS.md`
- `doc/crossfetch/BUG_FIX_HIERARCHICAL_LAYOUT_OVERWRITE.md`
- `doc/crossfetch/COORDINATE_ENRICHMENT_COMPLETE.md`
- `doc/crossfetch/COORDINATE_ENRICHMENT_PHASE5_LAYOUT_RESOLVER.md`
- `doc/crossfetch/KEGG_PATHWAY_DISCOVERY.md`
- `doc/crossfetch/QUICK_TEST_GUIDE.md`
- `doc/crossfetch/TESTING_NOTE_BIOMD0000000001.md`

---

## Test Cases Used

- **BIOMD0000000001** (12 places) - Small, simple pathway
- **BIOMD0000000002** (13 places) - Showed coordinate stretching
- **BIOMD0000000061** (25 places) - Worst case, most spurious coordinates
- **BIOMD0000000428** (31 places) - Large pathway test

---

## Next Steps (When Resumed)

### Investigation Priorities

1. **Find Coordinate Corruption Point**
   - Run app with full debug logging
   - Identify where coordinates change from (383.7, 600.0) to (-2988.7, 4705.5)
   - Check if it's during rendering, property access, or observer notification

2. **Check for Coordinate Transforms**
   - Search for `world_to_screen()`, `screen_to_world()` usage
   - Check Cairo transform stack
   - Verify no unintended coordinate system conversions

3. **Verify Place Object Integrity**
   - Confirm Place.x and Place.y are simple attributes (not properties)
   - Check if any setters or getters modify coordinates
   - Verify object identity (same object throughout pipeline)

4. **Test Simpler Pathways**
   - Try manually creating small pathway (2-3 places)
   - Check if issue is specific to SBML import
   - Test with .shypn file save/load

### Possible Solutions

1. **If it's a transform issue:**
   - Remove or fix the transform
   - Store coordinates in screen space instead of world space

2. **If it's a property issue:**
   - Make x/y pure attributes
   - Remove any computed coordinate logic

3. **If it's an observer issue:**
   - Disable observers during import
   - Batch notify after all objects loaded

4. **Alternative Approach:**
   - Use existing SBML layout coordinates (if available)
   - Skip hierarchical layout for pathways with valid coordinates
   - Only apply hierarchical layout to coordinate-less pathways

---

## How to Restore and Continue

```bash
# Check out the experimental state
git checkout backup/layout-experiments-20251014

# Or restore to feature branch (current state)
git checkout feature/property-dialogs-and-simulation-palette

# View commit details
git show 20a1d00

# Create new branch for continued work
git checkout -b feature/fix-hierarchical-coordinates
```

---

## Lessons Learned

1. **Tree layouts are complex for biochemical graphs** - Multiple parents/products make simple tree centering difficult

2. **Debug logging is essential** - The extensive logging added will be helpful for future investigation

3. **Coordinate corruption happens late in pipeline** - The layout and converter produce correct coordinates; issue is in display/manager

4. **Simple is better** - Fixed layer-based layout is more predictable than tree centering

5. **Git protection is important** - Backup branches and tags preserve experimental work

---

## References

- Topological Sort (Kahn's Algorithm): Used for layer assignment
- Tree Layout Algorithms: Reingold-Tilford, Walker's algorithm (not implemented)
- SBML Layout Extension: Coordinate system specification
- Cairo Graphics: Coordinate transform stack

---

## Contact

For questions about this work:
- Commit: 20a1d00
- Branch: backup/layout-experiments-20251014
- Date: October 14, 2025
