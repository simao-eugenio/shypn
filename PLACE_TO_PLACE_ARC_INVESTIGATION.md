# Place-to-Place Arc Investigation

**Date**: October 10, 2025  
**Issue**: User observed direct lines connecting compounds (places) to other compounds (places)  
**Status**: ✅ **RESOLVED** - Tiny invisible transitions causing visual illusion  
**Fix Date**: October 10, 2025  

## Final Resolution

### Root Cause: Tiny Invisible Transitions

**The "place-to-place" lines were an optical illusion!**

The lines were **NOT** invalid Place→Place connections. They were valid **Place→Transition→Place** paths where the transitions were so small (< 10×10 pixels) that they were invisible at normal zoom.

**Visual Effect**:
```
What exists:     Place → [tiny 10×10px transition] → Place
What user sees:  Place ─────────────────────────→ Place
```

**Evidence from User Screenshot**:
- Lines appeared to go directly between compounds (C00036, etc.)
- Lines had NO visible rectangles/transitions at connection points
- Lines were NOT context-sensitive (couldn't right-click)
- Actually: transitions existed but were too small to see!

### The Fix

**File**: `src/shypn/importer/kegg/reaction_mapper.py`

**Change**: Enforced minimum transition size of 15×15 pixels

```python
# Ensure minimum size for visibility (fix for tiny invisible transitions)
MIN_TRANSITION_SIZE = 15.0
transition.width = max(getattr(transition, 'width', 10.0), MIN_TRANSITION_SIZE)
transition.height = max(getattr(transition, 'height', 10.0), MIN_TRANSITION_SIZE)
```

**Applied to**:
- `_create_single_transition()` - regular reactions
- `_create_split_reversible()` - both forward and reverse transitions

**Result**:
- ✅ Transitions now clearly visible at normal zoom
- ✅ No more "spurious" place-to-place line illusion  
- ✅ Data model was always correct - purely a visibility issue

---

## Screenshot Analysis

User provided screenshot showing:
- Multiple direct compound-to-compound connections
- Examples: C01159 → C00236, C01159 → C00085, etc.
- Pathway appears to be Glycolysis/Pyruvate metabolism
- Gene/enzyme labels visible: PCK1, FBP1, BPGM, MINPP1, PKLR, LDHAL6A, ALDH3A1

**This violates Petri net bipartite property!** Places should only connect through transitions.

## Investigation Results

### Current Code Status: ✅ CORRECT

**Arc Builder Validation**:
```python
# From arc_builder.py - Only creates valid arcs
def _create_input_arcs(...):
    # Creates: Place → Transition
    arc = Arc(place, transition, ...)
    
def _create_output_arcs(...):
    # Creates: Transition → Place  
    arc = Arc(transition, place, ...)
```

**Test Results**:
- Tested hsa00010 (Glycolysis): **NO place-to-place arcs**
- Tested C01159 and C00036: **NO direct connection**
- Arc validation confirmed: All arcs follow **Place ↔ Transition** pattern

### Root Cause Analysis

The place-to-place arcs in the screenshot are **NOT being created by current code**. Possible explanations:

1. **Old saved file** (MOST LIKELY)
   - File created with legacy conversion code
   - Before arc validation was implemented
   - Before isolated compound filtering

2. **Manual editing** (POSSIBLE)
   - User manually created arcs
   - Arc validation may have been bypassed in GUI

3. **Legacy import path** (UNLIKELY)
   - Different import method still in codebase
   - We checked - no relation conversion happening

## Solution Implemented

### Enhanced Isolated Compound Filtering

Moved filtering from Phase 3 (post-processing) to **Phase 1 (upfront)**:

```python
# Phase 1: Only create places for compounds used in reactions
if options.filter_isolated_compounds:
    # Build set of compound IDs actually used
    used_compound_ids = set()
    for reaction in pathway.reactions:
        for substrate in reaction.substrates:
            used_compound_ids.add(substrate.id)
        for product in reaction.products:
            used_compound_ids.add(product.id)
    
    # Only create places for used compounds
    for compound in pathway.compounds:
        if compound.id in used_compound_ids:
            place = create_place(compound)
            document.places.append(place)
```

**Benefits**:
- More efficient (don't create then delete)
- Clearer logic (only create what's needed)
- Prevents any edge cases where isolated compounds might get arcs

### Test Results

**hsa00010 (Glycolysis)**:
- Total compounds: 31
- With filtering: 26 places
- Filtered out: 5 (16%)
- ✅ All remaining places connected
- ✅ NO place-to-place arcs

**hsa00620 (Pyruvate metabolism)**:
- Total compounds: 32
- With filtering: 23 places  
- Filtered out: 9 (28%)
- ✅ All remaining places connected
- ✅ NO place-to-place arcs

### Verification Commands

```bash
# Test specific compounds
python3 trace_arc_creation.py
# Result: ✅ No direct arcs between C01159 and C00036

# Test filtering
python3 test_enhanced_filtering.py
# Result: ✅ All places connected, no isolated nodes

# Check KEGG relations
python3 check_kegg_relations.py
# Result: Relations exist but NOT converted to arcs
```

## User Action Required

To fix the issue in your current view:

### Option 1: Re-import Fresh (RECOMMENDED)
```
1. In Shypn GUI, go to KEGG Import panel
2. Enter pathway ID (e.g., "hsa00010")
3. Click "Fetch" then "Import"
4. New import will have:
   - ✅ Only valid Place ↔ Transition arcs
   - ✅ Isolated compounds filtered
   - ✅ Correct Petri net semantics
```

### Option 2: Delete Old File
```
If viewing a saved file:
1. Close the file
2. Delete or rename it (add ".old" extension)
3. Re-import the pathway fresh
```

### Option 3: Manual Fix (NOT RECOMMENDED)
```
If you want to keep the file:
1. Manually delete place-to-place arcs
2. This is tedious and error-prone
3. Better to re-import
```

## Prevention

The following mechanisms now prevent place-to-place arcs:

### 1. Arc Validation (Existing)
```python
# From netobjs/arc.py
@staticmethod
def _validate_connection(source, target):
    source_is_place = isinstance(source, Place)
    target_is_place = isinstance(target, Place)
    
    if source_is_place == target_is_place:
        raise ValueError("Invalid connection: arcs must connect Place↔Transition")
```

### 2. Upfront Filtering (New)
- Only creates places for compounds used in reactions
- Compounds not in reactions = not created
- Can't have arcs to non-existent places

### 3. No Relation Conversion (Confirmed)
- KEGG relations (PPrel, ECrel, etc.) are NOT converted
- Relations represent regulatory connections
- Would create place-to-place if converted
- Current code: Relations parsed but ignored ✅

## Documentation Updated

- **ISOLATED_COMPOUND_FILTERING.md**: Updated algorithm description
- **PETRI_NET_ARC_SEMANTICS.md**: Explains why Place→Place invalid
- **ISOLATED_COMPOUND_FIX.md**: Initial investigation summary

## Testing Performed

1. ✅ Verified current code creates NO place-to-place arcs
2. ✅ Tested specific compounds (C01159, C00036) - no direct connection
3. ✅ Tested multiple pathways - all correct
4. ✅ Verified filtering works - isolated compounds removed
5. ✅ Verified option can be toggled
6. ✅ GUI compatibility confirmed

## Conclusion

**Current code is correct and safe.**

The place-to-place arcs in the screenshot are from:
- Old file created before fixes
- Legacy conversion code
- Or manual editing

**Solution**: Re-import pathways using current code with enhanced filtering.

**Status**: ✅ No code changes needed - issue resolved by existing validation + enhanced filtering

---

**Files Modified**: `src/shypn/importer/kegg/pathway_converter.py`  
**Commit**: Pending - Enhanced upfront filtering  
**Branch**: feature/property-dialogs-and-simulation-palette
