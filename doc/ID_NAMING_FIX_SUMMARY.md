# ID Naming Convention Fix - Complete Summary

## Problem Overview

**Symptoms:**
- Transitions like T3, T4, T35 only fired once then stopped
- Arc references were broken (arc pointing to "35" couldn't find transition "T35")
- Simulation failures after creating elements interactively

**Root Cause:**
Interactive element creation (`create_place()`, `create_transition()`, `create_arc()`) was generating **numeric IDs** instead of **string IDs with prefixes**.

```python
# WRONG (old code):
place_id = self._next_place_id  # Returns 101 (integer)
place = Place(..., id=101, ...)  # Numeric ID

# CORRECT (new code):
place_id = f"P{self._next_place_id}"  # Returns "P101" (string)
place = Place(..., id="P101", ...)  # String ID with prefix
```

## Complete Solution

### 1. Fixed ID Generation (`document_model.py`)

**Lines 60-109**: All three creation methods now generate string IDs:

```python
# Places
place_id = f"P{self._next_place_id}"     # "P1", "P2", "P3", ...
place_name = place_id
place = Place(..., id=place_id, ...)

# Transitions
transition_id = f"T{self._next_transition_id}"  # "T1", "T2", "T3", ...
transition_name = transition_id
transition = Transition(..., id=transition_id, ...)

# Arcs
arc_id = f"A{self._next_arc_id}"        # "A1", "A2", "A3", ...
arc_name = arc_id
arc = Arc(..., id=arc_id, ...)
```

### 2. Fixed Deserialization (`document_model.py`)

**Lines 437-478**: Counter extraction now handles prefixed string IDs:

```python
# OLD (failed on "P101"):
place_id_int = int(place.id)  # ValueError on "P101"

# NEW (works with both "P101" and "101"):
id_str = str(place.id).lstrip('P')  # Remove P prefix
place_id_int = int(id_str)  # Extract 101
```

### 3. Created Centralized ID Manager (`id_manager.py`)

**NEW FILE**: Provides utilities for consistent ID handling:

```python
from shypn.data.canvas.id_manager import IDManager

manager = IDManager()

# Generate IDs
place_id = manager.generate_place_id()  # "P1"
transition_id = manager.generate_transition_id()  # "T1"
arc_id = manager.generate_arc_id()  # "A1"

# Normalize existing IDs
normalized = IDManager.normalize_place_id(101)  # "P101"
normalized = IDManager.normalize_place_id("101")  # "P101"
normalized = IDManager.normalize_place_id("P101")  # "P101"

# Extract numeric parts
numeric = IDManager.extract_numeric_id("P101", 'P')  # 101
numeric = IDManager.extract_numeric_id("101", 'P')  # 101
```

## How IDs Work Now

### ID Format Convention

| Object Type | Prefix | Example IDs | Counter |
|-------------|--------|-------------|---------|
| Place       | P      | P1, P2, P101 | `_next_place_id` |
| Transition  | T      | T1, T35, T39 | `_next_transition_id` |
| Arc         | A      | A1, A113, A117 | `_next_arc_id` |

### ID Flow

1. **Creation** (Interactive drawing):
   ```python
   place = document.create_place(x, y)
   # place.id = "P1" (string with prefix)
   ```

2. **Serialization** (Save to .shy file):
   ```json
   {
     "places": [
       {"id": "P1", "name": "P1", "x": 100, "y": 100}
     ]
   }
   ```

3. **Deserialization** (Load from .shy file):
   ```python
   place = Place.from_dict({"id": "P1", ...})
   # Extract counter: "P1" → 1
   _next_place_id = max(1) + 1 = 2
   ```

4. **Arc References**:
   ```json
   {
     "id": "A5",
     "source_id": "P101",  // String reference
     "target_id": "T3"      // String reference
   }
   ```

## Files Affected

### Core Files Modified
- ✅ `src/shypn/data/canvas/document_model.py` - ID generation and deserialization
- ✅ `src/shypn/data/canvas/id_manager.py` - New centralized ID utilities

### Verified Correct (No Changes Needed)
- ✅ `src/shypn/importer/kegg/compound_mapper.py` - Already uses `f"P{entry.id}"`
- ✅ `src/shypn/importer/kegg/reaction_mapper.py` - Already uses `f"T{counter}"`
- ✅ `src/shypn/importer/kegg/arc_builder.py` - Already uses `f"A{counter}"`
- ✅ `src/shypn/importer/kegg/pathway_converter.py` - All Places use prefixed IDs

## Fix Tool

The `fix_id_naming_conventions.py` script can repair old files:

```bash
# Fix a single file
python3 fix_id_naming_conventions.py workspace/projects/Interactive/models/hsa00010.shy

# Scan workspace recursively
python3 fix_id_naming_conventions.py workspace/ --recursive

# Check only (no modifications)
python3 fix_id_naming_conventions.py model.shy --check-only
```

**What it does:**
1. Scans for numeric IDs without prefixes (e.g., "35", "101", "113")
2. Adds proper prefixes (e.g., "35" → "T35", "101" → "P101")
3. Updates all arc references (`source_id`, `target_id`)
4. Creates backup file (`.shy.backup`)

## User Action Required

### For Existing Projects

**Option 1: Re-import from KEGG (Recommended)**
```bash
1. Close ShyPN application
2. Delete: workspace/projects/Interactive/models/hsa00010.shy
3. Start ShyPN
4. Open Projects → Interactive
5. Import → KEGG → hsa00010
6. Save
```

**Option 2: Fix Existing File**
```bash
# Close ShyPN first!
python3 fix_id_naming_conventions.py workspace/projects/Interactive/models/hsa00010.shy

# Then restart ShyPN and reload the model
```

### For Future Work

All new models created after this fix will automatically have proper IDs. No action needed!

## Testing Checklist

- [x] Interactive element creation generates string IDs
- [x] KEGG import generates string IDs  
- [x] Models load correctly from .shy files
- [x] Counter extraction works with prefixed IDs
- [x] Arc references use string IDs
- [x] Simulation works after parameter application
- [ ] User tests: Create T35 interactively → Save → Reload → Verify ID is "T35"
- [ ] User tests: Import KEGG → Create transitions → Save → Reload → Run simulation

## Prevention

### Code Review Guidelines

When adding new model creation code, always:

1. **Generate string IDs with prefixes:**
   ```python
   # CORRECT
   place_id = f"P{counter}"
   transition_id = f"T{counter}"
   arc_id = f"A{counter}"
   
   # WRONG
   place_id = counter  # Numeric!
   ```

2. **Use object references, not ID strings:**
   ```python
   # CORRECT
   arc = Arc(source=place_obj, target=transition_obj, ...)
   
   # AVOID (but if necessary, use strings)
   arc_data = {"source_id": "P101", "target_id": "T3"}  # Strings!
   ```

3. **Extract numeric parts carefully:**
   ```python
   # Use IDManager utility
   numeric = IDManager.extract_numeric_id(id_value, prefix)
   
   # Or handle manually
   numeric = int(str(id_value).lstrip('P'))
   ```

### Future Refactoring

The centralized `IDManager` is ready for adoption:

```python
# Current (document_model.py)
place_id = f"P{self._next_place_id}"
self._next_place_id += 1

# Future (after refactoring)
place_id = self.id_manager.generate_place_id()
```

This will further ensure consistency across all code paths.

## Related Files

- `ID_NAMING_CONVENTION_FIX.md` - Original fix documentation
- `fix_id_naming_conventions.py` - Repair tool for old files
- `src/shypn/data/canvas/id_manager.py` - Centralized ID utilities

## Commits

- `64a435e` - Created fix tool and documentation
- `bf999b4` - Fixed ID generation and deserialization (THIS FIX)

## Contact

If you encounter ID-related issues after this fix, please report:
1. The specific operation that failed
2. Whether the model was created before or after this fix
3. The model file (attach .shy file if possible)
4. Output of: `python3 fix_id_naming_conventions.py your_model.shy --check-only`
