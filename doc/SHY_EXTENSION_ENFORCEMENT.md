# .shy Extension Enforcement - Implementation

**Date:** 2025-10-16  
**Status:** ✅ COMPLETE  
**Branch:** feature/property-dialogs-and-simulation-palette

---

## Problem

File operations (Save, Save As, New File) needed to ensure `.shy` extension is always present on filenames, regardless of how users enter the name.

**Issues:**
1. User might forget to type `.shy` extension
2. User might type extension in wrong case (`.SHY`, `.Shy`)
3. Suggested filenames from imports might already have `.shy` (double extension risk)
4. Inconsistent handling across different save operations

**User Request:**
> "when saving, saving-as, if accepted name suggested, certify that .shy it is added to file name suggested, or always do that for any file operations"

---

## Solution

Implemented **robust .shy extension enforcement** with case-insensitive checking and normalization across all file operations.

### Key Improvements

1. **Case-insensitive detection**: Check for `.shy`, `.SHY`, `.Shy`, etc.
2. **Normalization**: Convert any case variant to lowercase `.shy`
3. **No double extensions**: Prevent `filename.shy.shy`
4. **Consistent handling**: Same logic in save dialog and file creation

---

## Implementation Details

### File: `src/shypn/file/netobj_persistency.py`

Modified `_show_save_dialog()` method:

#### 1. Suggested Filename Handling (Lines 329-337)

**Before:**
```python
if self.suggested_filename:
    default_name = f'{self.suggested_filename}.shy'
else:
    default_name = 'default.shy'
```

**After:**
```python
if self.suggested_filename:
    # Ensure suggested filename doesn't already have .shy extension
    suggested = self.suggested_filename
    if suggested.lower().endswith('.shy'):
        default_name = suggested
    else:
        default_name = f'{suggested}.shy'
else:
    default_name = 'default.shy'
```

**Benefit:** Prevents double extensions like `glycolysis.shy.shy`

#### 2. User-Entered Filename Processing (Lines 342-349)

**Before:**
```python
if not filepath.endswith('.shy'):
    filepath += '.shy'
```

**After:**
```python
# Ensure .shy extension is present (case-insensitive check)
if not filepath.lower().endswith('.shy'):
    filepath += '.shy'
elif not filepath.endswith('.shy'):
    # Handle case where user typed .SHY or .Shy - normalize to .shy
    filepath = filepath[:-4] + '.shy'
```

**Benefit:** Handles all case variants and normalizes to lowercase

---

### File: `src/shypn/helpers/file_explorer_panel.py`

Modified `_on_edit_done()` method for inline file creation:

#### New File Creation (Lines 703-709)

**Before:**
```python
if not self.editing_is_folder and (not new_text.endswith('.shy')):
    new_text += '.shy'
```

**After:**
```python
if not self.editing_is_folder:
    # Ensure .shy extension is present (case-insensitive check)
    if not new_text.lower().endswith('.shy'):
        new_text += '.shy'
    elif not new_text.endswith('.shy'):
        # Handle case where user typed .SHY or .Shy - normalize to .shy
        new_text = new_text[:-4] + '.shy'
```

**Benefit:** Same robust handling for inline file creation

---

## Behavior Examples

### Example 1: User Types Filename Without Extension

**Input:** `my_model`  
**Result:** `my_model.shy` ✅

### Example 2: User Types Extension in Lowercase

**Input:** `my_model.shy`  
**Result:** `my_model.shy` ✅ (no change)

### Example 3: User Types Extension in Uppercase

**Input:** `my_model.SHY`  
**Result:** `my_model.shy` ✅ (normalized)

### Example 4: User Types Extension in Mixed Case

**Input:** `my_model.Shy`  
**Result:** `my_model.shy` ✅ (normalized)

### Example 5: Suggested Filename Already Has Extension

**Suggested:** `glycolysis.shy`  
**Dialog shows:** `glycolysis.shy` ✅ (not `glycolysis.shy.shy`)

### Example 6: Suggested Filename Without Extension

**Suggested:** `glycolysis`  
**Dialog shows:** `glycolysis.shy` ✅

---

## Logic Flow

### Save/Save As Dialog

```
User enters filename
       ↓
Check: ends with .shy? (case-insensitive)
       ↓
   ┌───NO───┐           YES
   ↓         ↓            ↓
Add .shy  Normalize  Keep as-is
           to .shy
              ↓
         Final filename
```

### Inline File Creation

```
User types filename in tree
       ↓
Check: is folder?
       ↓
   ┌───NO───┐
   ↓
Check: ends with .shy? (case-insensitive)
       ↓
   ┌───NO───┐           YES
   ↓         ↓            ↓
Add .shy  Normalize  Keep as-is
           to .shy
              ↓
        Create file
```

---

## Testing Scenarios

### Test 1: Save Dialog Without Extension
1. Create new model
2. File → Save
3. Enter filename: `test`
4. **Expected:** File saved as `test.shy`

### Test 2: Save Dialog With Uppercase Extension
1. Create new model
2. File → Save
3. Enter filename: `test.SHY`
4. **Expected:** File saved as `test.shy`

### Test 3: Import With Suggested Name
1. Import SBML model (suggested name: `glycolysis`)
2. File → Save
3. Dialog shows: `glycolysis.shy`
4. Accept default
5. **Expected:** File saved as `glycolysis.shy` (not double extension)

### Test 4: Inline File Creation
1. Right-click in File Explorer
2. Select "New File"
3. Type: `newmodel`
4. **Expected:** File created as `newmodel.shy`

### Test 5: Inline With Uppercase Extension
1. Right-click in File Explorer
2. Select "New File"
3. Type: `newmodel.SHY`
4. **Expected:** File created as `newmodel.shy`

---

## Edge Cases Handled

### Double Extension Prevention

✅ **Scenario:** Suggested filename already has `.shy`  
✅ **Handling:** Check before appending  
✅ **Result:** No `filename.shy.shy`

### Case Sensitivity

✅ **Scenario:** User types `.SHY` or `.Shy`  
✅ **Handling:** Detect case-insensitively, normalize to lowercase  
✅ **Result:** Consistent `.shy` extension

### Empty/Whitespace Names

✅ **Scenario:** User enters only spaces  
✅ **Handling:** `new_text.strip()` catches this  
✅ **Result:** Rejected (handled by existing validation)

### Special Characters

✅ **Scenario:** User types `model?.shy`  
✅ **Handling:** OS/filesystem handles validation  
✅ **Result:** Error from OS (existing behavior preserved)

---

## Benefits

### For Users

✅ **Automatic**: Don't need to remember `.shy` extension  
✅ **Forgiving**: Works with any case variant  
✅ **Predictable**: Always get `.shy` files  
✅ **No confusion**: No double extensions

### For Developers

✅ **Consistent**: Same logic in all file operations  
✅ **Maintainable**: Clear, documented behavior  
✅ **Safe**: Preserves existing validation  
✅ **Robust**: Handles edge cases gracefully

---

## Code Quality

### Principles Applied

1. **DRY (Don't Repeat Yourself)**: Same logic pattern in both files
2. **Defensive Programming**: Check multiple conditions
3. **User-Friendly**: Accept various inputs, normalize output
4. **Clear Intent**: Comments explain the "why"

### Future-Proof

- Easy to extend for other extensions if needed
- Can add more sophisticated filename validation
- Clear separation between detection and normalization

---

## Files Changed

**Modified:**
- `src/shypn/file/netobj_persistency.py`
  - Lines 329-337: Suggested filename handling
  - Lines 342-349: User-entered filename processing

- `src/shypn/helpers/file_explorer_panel.py`
  - Lines 703-709: Inline file creation

**No changes needed in:**
- Import panels (use suggested filename mechanism)
- Canvas loader (handles tab names, not file operations)

---

## Related Features

### Suggested Filename System

The suggested filename mechanism works with this enhancement:

```python
# In import panels (SBML/KEGG)
manager.mark_as_imported(pathway_name)  # Sets suggested filename

# In save dialog
if self.suggested_filename:
    # Now safely handles extension
    default_name = ...
```

### File Explorer Integration

File Explorer inline creation now consistent with save dialogs:
- Same extension detection logic
- Same normalization behavior
- Same user experience

---

## Status

✅ **Implementation Complete**  
✅ **Code Compiled**  
✅ **Consistent Behavior**  
⏳ **Ready for Testing**

---

## Future Enhancements

### Potential Improvements

1. **Multiple Extensions**: Support `.sbml`, `.kgml` in future
2. **Validation**: Warn about special characters
3. **Auto-sanitize**: Replace invalid chars automatically
4. **Extension Registry**: Centralized extension management

**Not needed now** - current implementation handles all .shy requirements.

---

**Last Updated:** 2025-10-16  
**Status:** ✅ COMPLETE
