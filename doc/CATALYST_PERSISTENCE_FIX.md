# Catalyst Persistence Fix

**Date:** November 2, 2025  
**Issue:** Catalyst layout flattening after file load  
**Status:** ✅ FIXED

## Problem

When a KEGG pathway with catalysts enabled was saved and later opened (via File→Open or double-click), the hierarchical layout would flatten again, showing all enzyme places at layer 0 instead of maintaining the proper catalyst layout.

### User Report

> "I opened by double click on a file and flattened hierarchy appears again"

## Root Cause

The `is_catalyst` attribute was being set during KEGG import but **was not being persisted** when the file was saved:

1. **During KEGG Import** (`src/shypn/importer/kegg/pathway_converter.py`):
   - Enzyme places marked with `place.is_catalyst = True` ✅
   - Hierarchical layout algorithm respects this flag ✅
   - Clean layered layout displayed ✅

2. **During File Save** (`src/shypn/netobjs/place.py`):
   - `Place.to_dict()` did **NOT** include `is_catalyst` in serialization ❌
   - Flag lost when file saved ❌

3. **During File Load** (`src/shypn/netobjs/place.py`):
   - `Place.from_dict()` had no way to restore the flag ❌
   - All catalyst places treated as regular places ❌
   - Layout algorithm sees them as layer 0 sources ❌
   - **Hierarchy flattened** ❌

## Solution

Added persistence for the `is_catalyst` attribute in the Place class:

### Changes to `src/shypn/netobjs/place.py`

**1. Save the flag in `to_dict()`:**

```python
def to_dict(self) -> dict:
    data = super().to_dict()
    data.update({
        "object_type": "place",
        "x": self.x,
        "y": self.y,
        # ... other properties ...
        "is_catalyst": getattr(self, 'is_catalyst', False)  # ← ADDED
    })
    return data
```

**2. Restore the flag in `from_dict()`:**

```python
@classmethod
def from_dict(cls, data: dict) -> 'Place':
    place = cls(...)
    
    # Restore optional properties
    if "marking" in data:
        place.tokens = data["marking"]
    # ...
    
    # Restore catalyst flag (for hierarchical layout) ← ADDED
    place.is_catalyst = data.get("is_catalyst", False)
    
    return place
```

## Impact

### Before Fix

```
File → Import KEGG Pathway (with catalysts enabled)
  ↓
Clean hierarchical layout (catalysts at input layer)
  ↓
File → Save
  ↓
File → Open (or double-click)
  ↓
❌ FLATTENED LAYOUT - All catalysts at layer 0!
```

### After Fix

```
File → Import KEGG Pathway (with catalysts enabled)
  ↓
Clean hierarchical layout (catalysts at input layer)
  ↓
File → Save (is_catalyst flag saved!)
  ↓
File → Open (or double-click)
  ↓
✅ CLEAN LAYOUT PRESERVED - Catalysts maintain proper positioning!
```

## Backward Compatibility

- Old `.shy` files without `is_catalyst` field: Default to `False` (no catalysts)
- No breaking changes for existing files
- Future saves will include the flag

## Testing

**Test file:** `test_catalyst_persistence.py`

**Run:** `python3 test_catalyst_persistence.py`

**Verifies:**
1. `is_catalyst` flag is saved in `to_dict()`
2. `is_catalyst` flag is restored in `from_dict()`
3. Non-catalyst places default to `False`
4. Catalyst places maintain `True` value

**Expected output:**
```
✅ TEST PASSED!
   is_catalyst flag correctly saved and restored
   Catalyst places will maintain proper layout when file is opened
```

## Manual Verification

1. Import a KEGG pathway with catalysts enabled
2. Verify clean hierarchical layout
3. Save the file: File → Save
4. Close and reopen the file: File → Open
5. **Expected:** Layout remains clean (no flattening)
6. **Before fix:** Layout would flatten with catalysts at layer 0
7. **After fix:** Layout maintains proper catalyst positioning

## Related Documentation

- `doc/CATALYST_LAYOUT_FIX.md` - Original layout algorithm fix (excludes catalysts from layer 0)
- `doc/CATALYST_VISIBILITY_GUIDE.md` - User guide for catalyst feature
- `doc/CATALYST_GLOBAL_IMPACT_ANALYSIS.md` - Comprehensive catalyst feature analysis

## Commits

- **cb86810:** `fix: Persist is_catalyst flag in Place serialization`
- **9ca7d8a:** `test: Add test for is_catalyst persistence`

## Summary

The `is_catalyst` attribute is now properly persisted in `.shy` files, ensuring that catalyst places maintain their special layout treatment across save/load cycles. This completes the catalyst layout feature by making it persistent, not just a runtime behavior during import.

**Fix Status:** ✅ Complete  
**Testing:** ✅ Automated test added  
**Documentation:** ✅ Complete
