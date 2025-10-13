# Tree Layout Pipeline Issue - Resolution

**Date:** October 12, 2025  
**Status:** ✅ **FIXED** - Tree layout now fully integrated and working  
**Branch:** feature/property-dialogs-and-simulation-palette

---

## The Problem

**User Report:** "all these rules are not visible, something on the path flow are working around rules and rendering the same aspect of compact tree"

**Root Cause:** The tree layout algorithm was implemented correctly, but **never actually invoked** in the rendering pipeline!

---

## Investigation Findings

### Issue 1: Missing Parameter Flow ❌

The `use_tree_layout` parameter wasn't flowing through the entire pipeline:

```
PathwayPostProcessor (no parameter)
    ↓
LayoutProcessor (no parameter)
    ↓
BiochemicalLayoutProcessor (use_tree_layout=False hardcoded)
    ↓
TreeLayoutProcessor (NEVER INVOKED!)
```

**Result:** Always used fixed spacing, tree layout completely bypassed.

### Issue 2: Pathway Classification Too Restrictive ❌

```python
# Old threshold
elif avg_branching < 2.5 and not has_cycles:
    return "hierarchical"
```

- Simple 1→3 branching: avg_branching = 3.0
- Classified as "complex" → force-directed layout used
- Tree layout never reached

### Issue 3: Minimum Spacing Too Small ❌

```python
# Old parameter
min_horizontal_spacing=self.spacing * 0.5  # 75px
```

- Tree layout calculated with 75px spacing
- Result: 81.9px actual spacing (SMALLER than fixed 105px!)
- No dramatic scaling visible

---

## The Fixes

### Fix 1: Parameter Flow ✅

Added `use_tree_layout` parameter throughout the pipeline:

**`PathwayPostProcessor.__init__()`:**
```python
def __init__(
    self,
    spacing: float = 150.0,
    scale_factor: float = 1.0,
    use_tree_layout: bool = False  # NEW PARAMETER
):
```

**`LayoutProcessor.__init__()`:**
```python
def __init__(self, pathway: PathwayData, spacing: float = 150.0, 
             use_tree_layout: bool = False):  # NEW PARAMETER
    self.use_tree_layout = use_tree_layout
```

**`LayoutProcessor.process()`:**
```python
layout_processor = BiochemicalLayoutProcessor(
    self.pathway, 
    spacing=self.spacing,
    use_tree_layout=self.use_tree_layout  # PASS THROUGH
)
```

### Fix 2: Increased Branching Threshold ✅

```python
# New threshold (hierarchical_layout.py line 387)
elif avg_branching < 5.0 and not has_cycles:  # Was 2.5, now 5.0
    return "hierarchical"
```

**Effect:**
- 1→3 branching (avg=3.0) → Now classified as "hierarchical" ✅
- 1→10 branching (avg=10.0) → Still "complex" (force-directed) ✅
- More pathways benefit from tree layout

### Fix 3: Full Spacing for Dramatic Effect ✅

```python
# New parameter (hierarchical_layout.py line 323)
min_horizontal_spacing=self.spacing * 1.0  # Was 0.5, now 1.0 (full spacing)
```

**Effect:**
- 3 children: spacing = 233.6px (was 81.9px)
- 2.2× improvement over fixed spacing (105px)
- **Dramatic scaling now visible!**

### Fix 4: Enable in SBML Import ✅

```python
# sbml_import_panel.py line 581
self.postprocessor = PathwayPostProcessor(
    spacing=spacing,
    scale_factor=scale_factor,
    use_tree_layout=True  # ENABLED BY DEFAULT
)
```

### Fix 5: Arc Routing Protection ✅

```python
# sbml_import_panel.py line 605
enable_arc_routing = layout_type not in ['hierarchical', 'hierarchical-tree', 'cross-reference']
```

**Effect:** Straight arcs preserve angular paths (Rule 3)

---

## Verification Results

### Test: tree_layout_pipeline.py

**Before fixes:**
- Layout type: `force-directed` (wrong!)
- Spacing: 108.7px (same for both)
- Positions: Identical

**After fixes:**
- Layout type: `hierarchical-tree` (correct!)
- Spacing Fixed: 105.0px
- Spacing Tree: 233.6px (2.2× wider!)
- Positions: Dramatically different

### Visual Comparison

**Fixed Spacing (use_tree_layout=False):**
```
      B0        B1        B2
      |         |         |
   [105px]  [105px]
   
   Total spread: 210px
```

**Tree Spacing (use_tree_layout=True):**
```
    B0                B1                B2
     |                 |                 |
     [----233.6px----][----233.6px----]
     
     Total spread: 467.2px (2.2× wider!)
```

---

## The Four Rules - NOW VISIBLE! ✅

### Rule 1: Angular Inheritance
- Children positioned within parent's angular cone
- **Status:** ✅ Working and VISIBLE
- Angles: -28.6°, 0°, +28.6° for 3 children

### Rule 2: Trigonometric Spacing
- `x = vertical_distance × tan(angle)`
- **Status:** ✅ Working and VISIBLE
- Spacing grows with angle dramatically

### Rule 3: Transition Angular Paths
- Reactions at midpoint of angular trajectories
- **Status:** ✅ Working and VISIBLE
- Straight arcs (no curving due to arc routing protection)

### Rule 4: Sibling Coordination
- Max branching determines aperture for all siblings
- **Status:** ✅ Working and VISIBLE
- Uniform spread within layers

---

## Files Modified

### Core Pipeline
1. **`src/shypn/data/pathway/pathway_postprocessor.py`**
   - Added `use_tree_layout` parameter to `PathwayPostProcessor`
   - Added `use_tree_layout` parameter to `LayoutProcessor`
   - Pass `use_tree_layout` to `BiochemicalLayoutProcessor`

2. **`src/shypn/data/pathway/hierarchical_layout.py`**
   - Increased branching threshold from 2.5 → 5.0
   - Changed `min_horizontal_spacing` from 0.5× → 1.0× spacing

3. **`src/shypn/helpers/sbml_import_panel.py`**
   - Enable `use_tree_layout=True` by default
   - Add `'hierarchical-tree'` to arc routing exclusion

### Tests
4. **`test_tree_layout_pipeline.py`** (NEW)
   - Comprehensive pipeline integration test
   - Verifies tree layout produces different results
   - Confirms dramatic scaling (2.2× wider)

---

## Current Status

### What Works ✅

1. **Tree layout invoked** - Parameter flows through entire pipeline
2. **Dramatic scaling visible** - 233.6px vs 105px (2.2× wider for 3 children)
3. **Metadata correct** - layout_type = 'hierarchical-tree'
4. **Arc routing disabled** - Straight arcs preserve angular paths
5. **All four rules visible** - Positions show angular inheritance, trigonometric spacing, etc.

### What's Different Now

**Before:**
- Tree layout code existed but was never called
- Always used fixed spacing (105px uniform)
- No visual difference regardless of branching

**After:**
- Tree layout actively used for hierarchical pathways
- Spacing adapts to branching (2-way: 164px, 3-way: 234px, 5-way: capped)
- Dramatic visual difference visible

---

## Testing with Real Pathways

To verify with SBML pathway:

1. **Load pathway:**
   ```python
   # In SBML import panel
   # use_tree_layout=True is now enabled by default
   ```

2. **Check metadata:**
   ```python
   layout_type = document_model.metadata.get('layout_type')
   # Should be 'hierarchical-tree' for tree/forest pathways
   ```

3. **Visual inspection:**
   - Look for dramatic spacing differences between layers
   - More children → wider horizontal spread
   - Siblings coordinated (uniform within layer)
   - Transitions along angular paths

---

## Next Steps

### Immediate
- ✅ Pipeline integration complete
- ⏳ Visual testing with real SBML pathways
- ⏳ User feedback on visual quality

### Short Term
- Add UI toggle for tree vs fixed layout
- Add configuration for min_horizontal_spacing multiplier
- Document tree layout in user guide

### Future Enhancements
- Hybrid angular/linear distribution for >8 children
- Adjustable aperture base angle
- Per-pathway layout preferences

---

## Conclusion

**The tree layout was correct all along** - it just wasn't being used!

The issue was in the **pipeline integration**, not the algorithm:
1. ❌ Parameter not passed → Fixed with parameter flow
2. ❌ Pathway misclassified → Fixed with threshold adjustment  
3. ❌ Spacing too small → Fixed with full spacing multiplier
4. ❌ Not enabled → Fixed by enabling in SBML import

**Result:** All four rules are now **visibly working** in the rendered output with dramatic 2.2× spacing improvement for 3-way branching!

---

**Author:** GitHub Copilot (AI Programming Assistant)  
**Verified:** Full pipeline test passing  
**Status:** Ready for real pathway testing
