# SBML Tree Layout - DAG Handling Fix

**Date**: October 12, 2025  
**Issue**: Discrepant coordinates due to converging pathways (DAG structure)  
**Status**: ✅ Fixed - Multiple parent handling + descendant shifting

## Problem Analysis from Image

Looking at the attached image, several critical issues were identified:

### Visual Symptoms
1. **Horizontal misalignment** (red arrows): Objects shifted far from expected positions
2. **Converging reactions misplaced**: Species with multiple incoming pathways positioned incorrectly  
3. **Descendant misalignment**: Children of repositioned nodes not following parent
4. **Reaction positioning errors**: Reactions spanning multiple layers at wrong Y coordinates

### Root Cause: DAG vs Tree Structure

**The Fundamental Issue**: Biochemical pathways are **DAGs** (Directed Acyclic Graphs), NOT trees!

```
DAG (Biochemical Pathway):          Tree (Algorithm Assumption):
       A    B                              A
        \  /                                \
         C         ← C has 2 parents         C
        / \                                 / \
       D   E                               D   E
```

**Problem**: Tree algorithm only tracks ONE parent per node!

When the algorithm encountered:
```python
A.add_child(C)  # C.parent = A
B.add_child(C)  # C.parent = B (overwrites A!)
```

Result: C positioned under B only, ignoring A completely!

## Fixes Applied

### Fix 1: Multiple Parent Tracking

**File**: `tree_layout.py` - `_build_trees()`

**Changes**:
```python
# OLD: Blindly overwrote parent
for child_id in children_ids:
    node.add_child(nodes[child_id])  # Last parent wins!

# NEW: Track all parents
if child_node.parent is not None:
    # Already has parent - track additional parents
    multiple_parents[child_id].append(species_id)
    # Don't add as tree child (keeps first parent)
else:
    # First parent - add normally
    node.add_child(child_node)
```

**Benefit**: All parents tracked, logged for debugging

### Fix 2: Multiple Parent Position Adjustment

**File**: `tree_layout.py` - `_adjust_multiple_parent_positions()`

**New Method**: Post-processes tree to center nodes among ALL parents

**Algorithm**:
1. Build reverse graph (child → [parents])
2. For each node with multiple parents:
   - Calculate center X of all parent X coordinates
   - Move node to center position
   - Log adjustment for debugging

**Example**:
```
Parent A at x=400
Parent B at x=600
Child C initially at x=400 (under A only)
Adjusted to x=500 (centered between A and B) ✓
```

### Fix 3: Recursive Descendant Shifting

**File**: `tree_layout.py` - `_shift_descendants()`

**New Method**: When parent moves, shift ALL descendants to maintain tree structure

**Algorithm**:
```python
def _shift_descendants(node, dx, positions):
    for child in node.children:
        child.x += dx  # Shift child by same amount
        _shift_descendants(child, dx, positions)  # Recurse
```

**Example**:
```
Before:     After shift by +50:
  C (400)     C (450)
 / \         / \
D   E       D   E
385 415     435 465
```

###Fix 4: Layer-Aware Reaction Positioning

**File**: `tree_layout.py` - `_position_reactions()`

**Problem**: Reactions with reactants from different layers got averaged Y

**OLD**:
```python
reaction_y = (reactant_y + product_y) / 2  # Wrong if spanning layers!
```

**NEW**:
```python
# Find min/max Y among all reactants and products
all_y_coords = [y for reactants] + [y for products]
min_y = min(all_y_coords)
max_y = max(all_y_coords)

# If span multiple layers, use midpoint between extremes
if max_y - min_y < spacing * 0.5:
    reaction_y = reactant_y + spacing / 2  # Same layer
else:
    reaction_y = (min_y + max_y) / 2  # Multiple layers
```

**Benefit**: Reactions positioned at layer boundaries, not arbitrary Y values

## Test Results

### Test: Diamond Pathway
```
Structure:
  s1   s2    ← Layer 0 (sources)
   \   /
    s3       ← Layer 1 (converging point)
   /  \
  s4  s5     ← Layer 2 (products)
```

**Before Fix**:
```
s1: x=400
s2: x=545
s3: x=400  ❌ (under s1 only, ignoring s2!)
s4: x=385  ❌ (wrong relative to s3)
s5: x=415  ❌ (wrong relative to s3)
```

**After Fix**:
```
s1: x=400.0
s2: x=545.0
s3: x=472.5  ✓ (centered between 400 and 545)
s4: x=457.5  ✓ (properly centered under s3)
s5: x=487.5  ✓ (properly centered under s3)
```

### Verification
```python
✓ s3 centered: True (expected 472.5, got 472.5)
✓ s4/s5 centered under s3: True
```

## Technical Details

### TreeNode Enhancement
Added `metadata` dictionary to store additional info:
```python
class TreeNode:
    def __init__(self, species_id, layer):
        # ... existing fields ...
        self.metadata: Dict = {}  # NEW
```

Usage:
```python
node.metadata = {'additional_parents': [parent1_id, parent2_id, ...]}
```

### Processing Flow
```
1. Build tree (tracks first parent only)
   ↓
2. Track additional parents in metadata
   ↓
3. Position tree normally (using first parent)
   ↓
4. Adjust multi-parent nodes to center among ALL parents
   ↓
5. Recursively shift descendants to maintain structure
```

### Debug Logging
Now logs:
```
DEBUG: Species 's3' has multiple parents: s1, s2
DEBUG: Adjusted 's3' X position: 400.0 → 472.5 (centered among 2 parents)
```

## Impact on Different Pathway Types

### Linear Pathways
**No change** - Single parent per node, works as before

### Branching (Diverging)
**No change** - Single parent, multiple children, works as before

### Converging Pathways
**✅ FIXED** - Multiple parents now properly centered

### Diamond/Complex Networks
**✅ FIXED** - Both converging and diverging handled correctly

### Cycles
**Partial** - Tree algorithm breaks cycles at arbitrary point, one connection ignored
**Future**: Implement cycle detection and circular layout

## Known Limitations

### 1. Cycles Still Problematic
Tree algorithm must break cycles. The break point is arbitrary (depends on topological sort order).

**Example**:
```
A → B → C
    ↑___↓
    (cycle)
```
One edge will be ignored in tree building.

**Workaround**: Ensure SBML has no cycles, or they'll be broken unpredictably

### 2. Complex Convergence
Very complex convergence (e.g., 5+ parents) may create crowded layouts.

**Workaround**: Manual repositioning after import, or adjust `min_horizontal_spacing`

### 3. Layer Assignment
Topological sort may assign species to sub-optimal layers in complex networks.

**Workaround**: Use force-directed layout for very complex pathways

## Files Modified

1. **`src/shypn/data/pathway/tree_layout.py`**:
   - `TreeNode.__init__()`: Added `metadata` field
   - `_build_trees()`: Multiple parent tracking
   - `_position_trees()`: Call adjustment after positioning
   - `_adjust_multiple_parent_positions()`: New method
   - `_shift_descendants()`: New method
   - `_position_reactions()`: Layer-aware Y positioning

## How to Verify Fix

### Visual Inspection
After importing SBML:
1. Look for converging pathways (multiple species → one species)
2. Verify middle species is **centered** between parents
3. Verify descendants are **centered** under repositioned parents
4. Verify reactions are at **layer boundaries**, not arbitrary Y values

### Debug Logging
Enable debug logging to see adjustments:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Look for:
```
DEBUG: Species 'X' has multiple parents: A, B, C
DEBUG: Adjusted 'X' X position: 300.0 → 450.0 (centered among 3 parents)
```

### Programmatic Test
```python
# After import, check converging species
s1_x = positions['parent1'][0]
s2_x = positions['parent2'][0]
child_x = positions['child'][0]

expected = (s1_x + s2_x) / 2
assert abs(child_x - expected) < 1.0, "Child not centered!"
```

## Comparison: Before vs After

| Issue | Before | After |
|-------|--------|-------|
| Multiple parents | ❌ Only last parent used | ✅ Centered among all |
| Descendant alignment | ❌ Broken when parent moves | ✅ Maintained via shifting |
| Reaction Y position | ❌ Averaged (wrong for multi-layer) | ✅ Layer-aware |
| Debug visibility | ❌ Silent issues | ✅ Logged adjustments |

## Related Documentation

- `doc/SBML_TREE_LAYOUT_COORDINATE_DEBUG.md` - Fallback coordinates
- `doc/SBML_DISCREPANT_COORDINATES_FIX.md` - Tree spacing fixes
- `SBML_COORDINATE_FIXES.md` - Quick reference

## Future Enhancements

### Priority 1: Cycle Detection
- Detect cycles explicitly
- Choose optimal edge to break
- Use different arc type for broken edges

### Priority 2: Complex Convergence Handling
- Special layout for nodes with 5+ parents
- Fan-in/fan-out optimization
- Better spacing algorithms

### Priority 3: Hybrid Layouts
- Tree for main pathway
- Force-directed for complex regions
- User-specified layout hints

---

**Status**: Core DAG handling complete and tested  
**Confidence**: High - verified with diamond pathway test  
**Impact**: Fixes majority of coordinate discrepancies in converging pathways
