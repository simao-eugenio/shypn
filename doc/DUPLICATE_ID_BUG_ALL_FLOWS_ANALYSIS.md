# Duplicate ID Bug - Cross-Flow Impact Analysis

## Executive Summary

The duplicate ID bug discovered in SBML import has been analyzed across all file loading and object creation flows in the application. This document summarizes which flows are affected and what actions are needed.

## The Bug

When loading .shy files, the `DocumentModel.from_dict()` method was not updating ID counters (`_next_place_id`, `_next_transition_id`, `_next_arc_id`). This caused newly created objects to reuse existing IDs, leading to phantom values in simulation.

## Status by Flow

### ✅ FIXED: SBML Import

**Status:** Fixed on October 27, 2025

**How it works:**
- SBMLParser → PathwayData
- PathwayConverter → DocumentModel
  - Uses `document.create_place(x, y)` ✓
  - Uses `document.create_transition(x, y)` ✓
  - Uses `document.create_arc(source, target)` ✓
- `document.save_to_file()` → Saves as .shy JSON
- `document.load_from_file()` → `from_dict()` ✓ Updates counters

**Fix Applied:** `document.from_dict()` now updates `_next_*_id` counters after loading

**Files Modified:**
- `src/shypn/data/canvas/document_model.py` (lines 409-479)

---

### ⚠️ POTENTIALLY VULNERABLE: KEGG Import

**Status:** Mostly safe but uses non-standard ID assignment

**How it works:**
- KEGGAPIClient → KGML XML
- KGMLParser → KEGGPathway
- PathwayConverter → DocumentModel
  - `CompoundMapper.create_place()` → `Place(x, y, place_id, place_name)` ⚠️
    - Directly constructs Place with `place_id = f"P{entry.id}"`
    - KEGG entry IDs are typically 3-4 digits (P100, P141, etc.)
  - `ReactionMapper.create_transitions()` → `Transition(x, y, transition_id, ...)` ⚠️
    - Uses internal counter `self.transition_counter`
  - Appends directly: `document.places.append(place)` ⚠️
    - **BYPASSES** `document.create_place()`!

**Risk Analysis:**

**Q: Will duplicate IDs occur?**
A: UNLIKELY but POSSIBLE
- KEGG entry IDs are typically high numbers (100+)
- After loading, `from_dict()` sets counters to max + 1
- Collision only if KEGG has low IDs (P1, P2) AND user creates new objects

**Q: Is this a problem now?**
A: MOSTLY SAFE because:
- ✓ KEGG entry IDs are typically 3-4 digits
- ✓ `from_dict()` fix updates counters correctly after loading
- ✗ But manual ID assignment bypasses safety checks
- ✗ Architectural inconsistency - other flows use `document.create_*()`

**Recommendation:** Refactor KEGG to use `document.create_*()` methods (Low priority)

**Files to Review:**
- `src/shypn/importer/kegg/compound_mapper.py` (line 72-97)
- `src/shypn/importer/kegg/reaction_mapper.py` (line 73-91)

---

### ✅ SAFE: Interactive Drawing (Canvas Tools)

**Status:** Safe - uses proper ID management

**How it works:**
- User clicks [P] or [T] tool
- `_on_button_press()` → `manager.add_place(world_x, world_y)`
- `DocumentCanvas.add_place()` → `self.document.create_place(x, y)` ✓
- Auto-assigns sequential IDs from `_next_place_id` ✓

**Files:**
- `src/shypn/data/canvas/document_canvas.py` (line 270-320)
- `src/shypn/helpers/model_canvas_loader.py` (line 1323+)

---

### ✅ SAFE: File Save / Save-As

**Status:** Safe - only serialization, no ID assignment

**How it works:**
- `document.save_to_file(filepath)`
- `document.to_dict()` serializes existing objects
- No new objects created
- IDs preserved as-is

**Risk:** None

---

### ✅ FIXED: File Open / Load

**Status:** Fixed on October 27, 2025

**How it works:**
- `DocumentModel.load_from_file(filepath)`
- `from_dict(json_data)`
- Restores places, transitions, arcs
- ✓ Updates `_next_*_id` counters to `max + 1`

**Fix Applied:** Same fix as SBML flow

---

### ❓ UNKNOWN: Copy/Paste (if implemented)

**Status:** Needs investigation

**Potential issue:**
- If copy preserves IDs → DUPLICATE IDs when pasting
- Should use `document.create_*()` to get new IDs

**Action:** Check if copy/paste is implemented and review

---

### ❓ UNKNOWN: Undo/Redo (if implemented)

**Status:** Needs investigation

**Potential issue:**
- If undo/redo restores objects by ID → Could break
- Need to ensure IDs are unique and stable

**Action:** Check if undo/redo is implemented and review

---

## Summary Table

| Flow | Status | Risk | Action Needed |
|------|--------|------|---------------|
| SBML Import | ✅ Fixed | None | None |
| KEGG Import | ⚠️ Mostly Safe | Low | Refactor (low priority) |
| Interactive Drawing | ✅ Safe | None | None |
| File Save/Save-As | ✅ Safe | None | None |
| File Open/Load | ✅ Fixed | None | None |
| Copy/Paste | ❓ Unknown | Unknown | Investigate |
| Undo/Redo | ❓ Unknown | Unknown | Investigate |

---

## Recommendations

### 1. KEGG Import Refactoring (Low Priority)

**Why:** Architectural consistency and future-proofing

**Changes:**
```python
# OLD (compound_mapper.py line 97):
place = Place(x, y, place_id, place_name, label=label)
document.places.append(place)

# NEW:
place = document.create_place(x, y, label=label)
place.metadata['kegg_id'] = entry.name
place.metadata['kegg_entry_id'] = entry.id
```

**Benefits:**
- Consistency with SBML and interactive drawing
- Eliminates manual ID management
- Safer for future changes
- Better maintainability

**Files to modify:**
- `src/shypn/importer/kegg/compound_mapper.py`
- `src/shypn/importer/kegg/reaction_mapper.py`
- `src/shypn/importer/kegg/pathway_converter.py`

### 2. Add ID Uniqueness Validation (Medium Priority)

**Why:** Catch duplicate ID bugs early

**Add to DocumentModel:**
```python
def _validate_unique_id(self, id: str, obj_type: str):
    """Validate that ID is unique."""
    if obj_type == 'place':
        if any(p.id == id for p in self.places):
            raise ValueError(f"Duplicate place ID: {id}")
    # Similar for transitions and arcs
```

**Benefits:**
- Prevents silent duplicate ID bugs
- Helps catch issues during development
- Provides clear error messages

### 3. Document ID Management Policy (High Priority)

**Create coding standards document:**

**✅ DO:**
- ALWAYS use `document.create_place(x, y)` for new places
- ALWAYS use `document.create_transition(x, y)` for new transitions
- ALWAYS use `document.create_arc(source, target)` for new arcs
- Let DocumentModel manage ID assignment

**❌ DON'T:**
- NEVER manually construct `Place(x, y, id, name)` and append
- NEVER manually construct `Transition(x, y, id, name)` and append
- NEVER reuse IDs from loaded files
- NEVER bypass `document.create_*()` methods

**Update:**
- Development guidelines
- Code review checklist
- KEGG importer to follow policy

---

## Testing Recommendations

### Regression Tests

1. **Test SBML load + manual create:**
   ```python
   doc = DocumentModel.load_from_file('sbml_model.shy')  # Has places 1-25
   new_place = doc.create_place(100, 100)
   assert int(new_place.id) == 26  # Should be next sequential ID
   ```

2. **Test KEGG load + manual create:**
   ```python
   doc = DocumentModel.load_from_file('kegg_model.shy')  # Has places P100-P200
   new_place = doc.create_place(100, 100)
   assert int(new_place.id) == 201  # Should be max + 1
   ```

3. **Test mixed operations:**
   ```python
   doc = DocumentModel()
   p1 = doc.create_place(100, 100)  # ID 1
   p2 = doc.create_place(200, 100)  # ID 2
   doc.save_to_file('test.shy')
   
   doc2 = DocumentModel.load_from_file('test.shy')
   p3 = doc2.create_place(300, 100)  # Should be ID 3, not 1!
   assert int(p3.id) == 3
   ```

### Integration Tests

- Load SBML model → Simulate → Verify no phantom values
- Load KEGG model → Add manual place → Simulate → Verify no phantom values
- Create objects interactively → Save → Load → Create more → Verify unique IDs

---

## Related Documents

- `doc/DUPLICATE_ID_BUG_FIX.md` - Original bug fix documentation
- `doc/SBML_COMPLETE_FLOW_ANALYSIS.md` - Complete SBML flow analysis
- `test_duplicate_id_fix.py` - Automated test for the fix

---

## Date

October 27, 2025

## Branch

File-Open-SBML-Health
