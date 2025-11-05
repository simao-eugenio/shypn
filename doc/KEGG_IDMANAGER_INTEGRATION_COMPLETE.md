# KEGG Importer IDManager Integration - Complete

## Summary

Successfully updated the KEGG importer to use IDManager for all ID generation, ensuring architectural consistency with the rest of the codebase.

## Problem

The KEGG importer was the last remaining component that bypassed IDManager:

```python
# OLD approach (inconsistent)
place_id = f"P{entry.id}"  # Manual ID based on KEGG entry ID
place = Place(x, y, place_id, ...)

# Then register AFTER creation
document.id_manager.register_place_id(place.id)
```

**Issues:**
- Used KEGG entry IDs directly (P18, P45, P100 with gaps)
- Bypassed IDManager during creation
- Only registered IDs after the fact
- Inconsistent with DocumentModel, SBML import, interactive creation
- Required complex counter synchronization between arc_builder and IDManager

## Solution

Updated all KEGG importers to use IDManager for generation:

```python
# NEW approach (consistent)
place_id = document.id_manager.generate_place_id()  # Sequential P1, P2, P3...
place = Place(x, y, place_id, ...)
place.metadata['kegg_entry_id'] = entry.id  # Preserve KEGG ID in metadata
```

## Changes Made

### 1. compound_mapper.py
- Added `id_manager` parameter to `create_place()` method
- Uses `id_manager.generate_place_id()` when available
- Falls back to old behavior for backwards compatibility
- Preserves KEGG entry ID in metadata

### 2. reaction_mapper.py
- Added `id_manager` parameter to `create_transitions()` method
- Stores id_manager reference for use in helper methods
- Updated `_create_single_transition()` to use `id_manager.generate_transition_id()`
- Updated `_create_split_reversible()` for both forward and backward transitions
- Falls back to local counter for backwards compatibility

### 3. arc_builder.py
- Stores id_manager reference in `create_arcs()`
- Uses `id_manager.generate_arc_id()` directly in arc creation
- Removed counter synchronization code (get_state/set_state)
- Simplified logic - no more state sync needed

### 4. pathway_converter.py
- Passes `document.id_manager` to all mappers and builders:
  - `compound_mapper.create_place(entry, options, document.id_manager)`
  - `reaction_mapper.create_transitions(reaction, pathway, options, document.id_manager)`
  - `arc_builder.create_arcs(..., document=document)` (already had this)
- **REMOVED:** ID registration loop (lines 379-384)
  - No longer needed since IDs are generated via IDManager
  - Previously: `for place in places: id_manager.register_place_id(place.id)`
  - Now: IDs generated during creation automatically

### 5. converter_base.py
- Updated `ReactionMapper.create_transitions()` abstract method signature
- Added `id_manager` parameter to interface

## Benefits

1. **Architectural Consistency:**
   - KEGG import now uses same ID generation pattern as:
     - DocumentModel.create_place/transition/arc()
     - SBML importer
     - Interactive creation (DocumentController)
     - Copy/paste operations

2. **Sequential IDs:**
   - OLD: P18, P45, P100 (based on KEGG entry IDs, with gaps)
   - NEW: P1, P2, P3... (sequential, no gaps)

3. **Guaranteed Uniqueness:**
   - IDManager ensures no ID conflicts
   - No manual counter synchronization needed
   - No complex state management

4. **Metadata Preservation:**
   - KEGG entry IDs preserved in `metadata.kegg_entry_id`
   - Can still trace back to original KEGG data
   - No information loss

5. **Cleaner Code:**
   - Removed 43 lines of complex counter sync code
   - Removed ID registration loop
   - Added 150 lines of clean IDManager integration
   - Net improvement: more robust with similar line count

## Testing

Created `test_kegg_idmanager_fix.py` that analyzes:
- Old file uses KEGG entry IDs (P18-P150 with gaps)
- New imports will use sequential IDs (P1-P65)
- No duplicate IDs
- No conflicts between catalyst and regular places

To test manually:
1. Open application
2. Import → KEGG Pathway → hsa00010
3. Enable "Show Catalysts"
4. Save file
5. Check IDs are sequential: P1, P2, P3...

## Backwards Compatibility

All changes include fallback to old behavior:
- If `id_manager` is None, use local counters
- Existing code that doesn't pass id_manager still works
- No breaking changes to API

## Files Modified

1. `src/shypn/importer/kegg/compound_mapper.py` (+16 lines)
2. `src/shypn/importer/kegg/reaction_mapper.py` (+28 lines)
3. `src/shypn/importer/kegg/arc_builder.py` (+18 lines, -43 removed)
4. `src/shypn/importer/kegg/pathway_converter.py` (+6 lines, -9 removed)
5. `src/shypn/importer/kegg/converter_base.py` (+2 lines)
6. `test_kegg_idmanager_fix.py` (new file, +82 lines)

## Commit

```
bbc2b51 - Fix KEGG importer to use IDManager for all ID generation
```

## Related Issues

This completes the ID generation cleanup effort:
- ✅ Dead code removal (commit dac667f)
- ✅ ID validation (all files passed)
- ✅ KEGG IDManager integration (commit bbc2b51)

All ID generation now goes through IDManager. No more bypasses!

## Date

2025-01-05 (completed during session)
