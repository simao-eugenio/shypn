# SBML Tree Layout - Discrepant Coordinate Fixes

**Date**: October 12, 2025  
**Issue**: Places and transitions getting discrepant coordinates from neighbors  
**Status**: ✅ Fixed - Dynamic tree spacing + validation added

## Problem

During SBML import with tree layout, some objects had coordinates that were inconsistent with their neighbors:
- Objects in same layer with vastly different spacing
- Trees overlapping when they should be separated
- Occasional extreme coordinates (e.g., x=2000 when neighbors at x=400)

## Root Causes Identified

### 1. Fixed Tree Spacing (FIXED)
**Problem**: Multiple root trees used fixed 200px spacing regardless of tree width

**Example**:
- Tree 1 width: 500px (spans x=150 to x=650)
- Tree 2 starts at: x=400 + 200 = x=600
- **OVERLAP**: Tree 1 extends to 650, Tree 2 starts at 600!

**Fix**: Calculate actual tree widths and space dynamically
```python
# OLD
tree_spacing = 200.0  # Fixed
tree_offset += tree_spacing

# NEW
tree_widths = [self._calculate_subtree_width(root) for root in roots]
tree_offset += prev_half_width + min_tree_gap + curr_half_width
```

### 2. Missing Validation (FIXED)
**Problem**: No warnings when coordinates become extreme

**Fix**: Added validation for unreasonable coordinates
```python
if child.x < -1000 or child.x > 10000:
    self.logger.warning(
        f"Unusual X coordinate for '{child.species_id}': {child.x:.1f}"
    )
```

### 3. Subtree Width Calculation
**Status**: ✓ Verified correct

The recursive subtree width calculation is working correctly:
- Leaf nodes: `min_horizontal_spacing`
- Parent nodes: sum of children's widths
- Properly accounts for entire descendant tree

## Fixes Applied

### Fix 1: Dynamic Tree Spacing

**File**: `src/shypn/data/pathway/tree_layout.py`  
**Method**: `_position_trees()`

**Changes**:
1. Pre-calculate width of each tree using `_calculate_subtree_width()`
2. Space trees based on actual widths with minimum gap
3. First tree centered at canvas center
4. Subsequent trees offset by: `prev_half_width + gap + curr_half_width`

**Benefits**:
- No tree overlap regardless of branching complexity
- Consistent minimum gap (100px) between trees
- Scales correctly for forests with many trees

### Fix 2: Coordinate Validation

**File**: `src/shypn/data/pathway/tree_layout.py`  
**Method**: `_position_subtree()`

**Changes**:
- Added validation for X coordinates outside reasonable range (-1000 to 10000)
- Logs warning with diagnostic info (parent position, child width)
- Helps identify calculation errors early

### Fix 3: Debug Logging

**File**: `src/shypn/data/pathway/tree_layout.py`  
**Method**: `_position_trees()`

**Changes**:
- Log calculated width for each tree
- Enables debugging of width calculation issues

## Testing

### Test 1: Wide + Narrow Trees

**Setup**: Tree 1 (very wide) + Tree 2 (narrow)

**Results**:
```
Tree 1 (wide): X range: 190.0 to 610.0 (width: 420.0)
Tree 2 (narrow): X range: 740.0 to 770.0 (width: 30.0)
Gap between trees: 130.0 pixels
✓ Good spacing between trees
```

**Before fix**: Gap would be ~10px (potential overlap)  
**After fix**: Gap is 130px (comfortable separation)

### Test 2: Asymmetric Branching

**Setup**: Root with 3 children having [4, 2, 3] grandchildren

**Results**:
```
Layer Y≈320: 9 objects
  Gaps: min=15.0, max=60.0, avg=25.3, stdev=19.2
```

**Analysis**: Variable spacing is CORRECT - children with more descendants need more space

### Test 3: Neighbor Spacing Analysis

**Tool**: `test_neighbor_spacing.py`

**Checks**:
- Gaps between neighbors in same layer
- Statistical outliers (>2σ from mean)
- Extreme gaps (>3σ overall)

**Result**: ✓ No discrepant spacing found

## Understanding Tree Layout Spacing

### Why Gaps Vary

Tree layout creates **variable spacing** by design:

```
    Root
   / | \
  A  B  C
 /|  |  |\
...  .  ...

A has 3 children → needs more width
B has 1 child   → needs less width
C has 2 children → needs medium width
```

**Spacing between A and B** < **Spacing between B and C** if A is wider

This is **correct behavior**, not a bug!

### When Spacing is Wrong

Problematic spacing:
- ❌ Trees overlapping
- ❌ Gaps > 500px between siblings
- ❌ Coordinates outside canvas (x < 0 or x > 5000)
- ❌ Objects at same layer with one at x=100, another at x=2000

Normal variation:
- ✓ Gaps 15-90px between siblings (different subtree widths)
- ✓ Closer spacing in dense areas
- ✓ Wider spacing where branching occurs

## Diagnostic Tools

### Tool 1: Coordinate Analysis
**File**: `test_sbml_coordinates.py`

**Usage**:
```bash
python3 test_sbml_coordinates.py your_file.xml
```

**Checks**: NaN, Inf, outliers, defaults, overlaps

### Tool 2: Neighbor Spacing Analysis
**File**: `test_neighbor_spacing.py`

**Usage**:
```bash
python3 test_neighbor_spacing.py
```

**Checks**: Gaps between neighbors, statistical analysis, discrepancies

### Tool 3: App Logging
**Enable**: Run app normally, check console

**Watches for**:
- Tree width calculations
- Unusual X coordinates
- Missing positions
- Fallback coordinates

## How to Verify Fix

### Step 1: Import SBML File
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
# File → Import SBML → Select your file
```

### Step 2: Check Console Logs
Look for:
- ✓ Tree width calculations: `Tree 'X' calculated width: 450.0px`
- ⚠️ Unusual coordinates: `Unusual X coordinate for 'species_5': 2500.0`
- ⚠️ Missing positions: `Species 'X' has no position, using fallback`

### Step 3: Visual Inspection
- Objects in same layer should have consistent spacing patterns
- Trees should be clearly separated
- No objects far off canvas

### Step 4: Run Diagnostics
```bash
# Full coordinate analysis
python3 test_sbml_coordinates.py your_file.xml

# Neighbor spacing analysis
python3 test_neighbor_spacing.py
```

## Expected Behavior After Fix

### Multiple Trees
- **Before**: Fixed 200px spacing → possible overlaps with wide trees
- **After**: Dynamic spacing based on tree width → guaranteed 100px minimum gap

### Coordinate Validation
- **Before**: Silent errors, extreme coordinates undetected
- **After**: Warnings logged for coordinates outside reasonable range

### Debug Information
- **Before**: Limited visibility into layout decisions
- **After**: Tree widths logged, easier to diagnose issues

## Files Modified

1. **`src/shypn/data/pathway/tree_layout.py`**
   - `_position_trees()`: Dynamic tree spacing based on calculated widths
   - `_position_subtree()`: Coordinate validation
   - Added debug logging for tree widths

2. **`test_neighbor_spacing.py`** (new)
   - Analyzes gaps between neighbors in same layer
   - Detects statistical outliers
   - Reports overall spacing statistics

## Related Issues

### Issue: "Gaps too small"
**Cause**: Minimum spacing (`min_horizontal_spacing`) set to 150px  
**Solution**: Can increase in hierarchical_layout.py line ~332:
```python
min_horizontal_spacing=200.0  # Increase from 150.0
```

### Issue: "Trees too far apart"
**Cause**: Minimum gap (`min_tree_gap`) set to 100px  
**Solution**: Can decrease in tree_layout.py line ~351:
```python
min_tree_gap = 50.0  # Decrease from 100.0
```

### Issue: "Coordinates still weird"
**Possible causes**:
1. Species not in any reaction → gets fallback (100, 100)
2. Reaction with no connections → gets fallback (400, 300)
3. Circular dependencies → topological sort breaks
4. Very wide trees → coordinates may go beyond typical canvas

**Diagnosis**: Check console warnings, run diagnostic tools

## Summary

### Problems Fixed
✅ Dynamic tree spacing prevents overlaps  
✅ Coordinate validation catches extreme values  
✅ Debug logging shows tree width calculations  
✅ Comprehensive test tools added

### Key Improvements
- Trees properly separated regardless of width
- Early warning for coordinate calculation errors
- Better diagnostic capabilities
- Verified correct subtree width algorithm

### Next Steps
1. Import your SBML files
2. Check for new warning messages
3. Run diagnostic tools if spacing looks wrong
4. Report specific cases for further tuning

---

**Status**: Fixes complete and tested  
**Confidence**: High - verified with multiple test scenarios  
**Impact**: Eliminates tree overlap and provides better diagnostics
