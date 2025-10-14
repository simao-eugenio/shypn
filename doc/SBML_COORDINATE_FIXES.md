# SBML Coordinate Fixes Summary

**Date**: January 6, 2025  
**Issue**: Spurious and discrepant coordinates in SBML tree layout import  
**Status**: ⚠️ PARTIALLY FIXED - DAG handling reverted due to stretching

## What Was Fixed

### 1. DAG (Multiple Parents) Handling - ⚠️ REVERTED

**Problem**: Tree algorithm only tracked ONE parent, ignoring converging pathways

**Solution Attempted**: 
- Track ALL parents (not just first)
- Post-process to center species among all parents
- Recursively shift descendants to maintain tree structure

**Result**: ❌ **CAUSED EXCESSIVE NETWORK STRETCHING**

**Status**: **REVERTED** - See `doc/SBML_TREE_LAYOUT_REVERT.md` for details

The adjustment and recursive shifting compounded across the network, creating excessive horizontal spreading. User feedback: "all net goes stretched". The simple tree layout (first parent only) is preferred for stability.

**Trade-off**: Converging pathways may not be perfectly centered, but network doesn't stretch excessively.

### 2. Layer-Aware Reaction Positioning ✅

**Problem**: Reactions spanning multiple layers got averaged Y coordinates

**Solution**: Position reactions at layer boundaries, not arbitrary Y values

**Impact**: Reactions now properly aligned between layers ✅

### 3. Dynamic Tree Spacing ✅

**Problem**: Multiple root trees used fixed 200px spacing, causing overlaps with wide trees

**Solution**: Calculate actual tree widths and space dynamically
- Pre-calculate width of each tree
- Space trees: `prev_half_width + 100px gap + curr_half_width`
- Guaranteed minimum 100px separation

**Impact**: No more tree overlaps, even with very wide/narrow trees ✅

### 4. Comprehensive Logging

All fallback/default coordinates now generate warnings so you can identify which objects aren't being positioned correctly:

1. **Species without positions** → `(100.0, 100.0)` - NOW WARNS
2. **Reactions without positions** → `(200.0, 200.0)` - NOW WARNS
3. **Reactions with no connections** → `(400.0, 300.0)` - NOW WARNS
4. **Reactions with missing reactants/products** - NOW WARNS

### Created Diagnostic Tool

**`test_sbml_coordinates.py`** analyzes coordinate distributions:
- Finds outliers (>3 std devs)
- Detects default/fallback coordinates
- Checks for overlaps
- Identifies invalid values (NaN, Inf)

## How to Use

### Import with logging enabled:
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py  # Regular app startup
```

Watch for warnings like:
```
⚠️  Species 'ATP' has no position, using fallback (100.0, 100.0)
⚠️  Reaction 'R_HEX1' missing reactant positions: ['Pi_ext']
⚠️  Reaction 'R_BND' has no valid connections, using fallback position (400.0, 300.0)
```

### Diagnose coordinates:
```bash
python3 test_sbml_coordinates.py your_pathway.xml
```

## Common Issues & Solutions

| Symptom | Cause | Solution |
|---------|-------|----------|
| Species at (100, 100) | Not in dependency graph | Check if isolated; manually reposition |
| Reaction at (200, 200) | Position not calculated | Check reactants/products exist |
| Reaction at (400, 300) | No valid connections | Check SBML model validity |
| Enzyme/cofactor at (100, 100) | Modifier not in stoichiometry | Expected; reposition manually |

## Files Changed

1. `src/shypn/data/pathway/tree_layout.py` - Dynamic tree spacing + validation + warnings (DAG features removed)
2. `src/shypn/data/pathway/pathway_converter.py` - Warnings for missing positions  
3. `test_sbml_coordinates.py` - Coordinate analysis diagnostic tool
4. `test_neighbor_spacing.py` - Neighbor spacing diagnostic tool
5. `doc/SBML_TREE_LAYOUT_COORDINATE_DEBUG.md` - Fallback coordinates documentation
6. `doc/SBML_DISCREPANT_COORDINATES_FIX.md` - Discrepant spacing fixes documentation
7. `doc/SBML_DAG_HANDLING_FIX.md` - DAG handling attempt (now problematic - reverted)
8. `doc/SBML_TREE_LAYOUT_REVERT.md` - **Revert documentation** (stretching issue)

## Backup

Original file with DAG handling preserved: `src/shypn/data/pathway/tree_layout.py.backup`

## Test Results

**Tree Spacing (Before vs After)**:
- Before: Fixed 200px → Trees overlapped with wide branching
- After: Dynamic spacing → 130px gap maintained ✓

**Neighbor Spacing**:
- Min gap: 15px (tight siblings)
- Max gap: 90px (different subtree widths)
- All within expected range ✓

**DAG Handling (REVERTED)**:
- Diamond pathway test: Centering worked perfectly ✓
- Real SBML networks: Excessive stretching ❌
- Result: Simple tree layout preferred for stability

## Next Steps

1. Import your SBML file
2. Check console for warnings
3. Run diagnostic tool if needed
4. Manually reposition any fallback coordinates in UI
5. Report specific cases for further investigation

---

**Key Insight**: "Spurious" coordinates are fallback values used when layout algorithm can't calculate proper positions. Now these are clearly logged so you know which objects need attention.
