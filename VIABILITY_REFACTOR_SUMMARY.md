# Viability Panel Refactor Summary

**Date**: November 10, 2025  
**Status**: In Progress

## Changes Requested

1. ✅ Refactor combo box to capture transition and places like plot list
2. ✅ Replace "Analyze All" button with "Run Full Diagnose"
3. ✅ Remove "ASSISTANT" from panel title
4. ⏳ Add "Repair" button per category to apply all suggestions
5. ⏳ Display suggestions as table format in categories
6. ✅ Remove Health Score display
7. ✅ Remove "Undo Last" button
8. ✅ Remove "Apply All" button

---

## Completed Changes

### 1. ✅ Removed "ASSISTANT" from Panel Title
**File**: `viability_panel.py` line ~91  
**Change**: `"VIABILITY ASSISTANT"` → `"VIABILITY"`

### 2. ✅ Button Renamed: "Analyze All" → "Run Full Diagnose"
**File**: `viability_panel.py` line ~96  
**Change**: Button label and tooltip updated

### 3. ✅ Removed Health Score Display
**File**: `diagnosis_category.py` lines ~103-117  
**Removed**:
- Health score frame
- Health label widget
- Health calculation logic

### 4. ✅ Removed "Undo Last" Button
**File**: `base_category.py` lines ~174-177  
**Removed**:
- Undo button widget
- Undo button click handler connection
- Undo functionality

### 5. ✅ Removed "Apply All Fixes" Button
**File**: `diagnosis_category.py` lines ~124-127  
**Removed**:
- Batch operation button
- Apply all click handler connection

---

## Pending Changes

### 1. ⏳ Refactor Combo Box (Complex)

**Current State**: ComboBoxText with string IDs  
**Target State**: TreeView/ListBox with transition objects and localities

**Implementation Plan**:
- Replace `Gtk.ComboBoxText` with `Gtk.TreeView` + `Gtk.ListStore`
- Store columns: [Transition ID, Transition Name, Transition Object, Locality Object]
- On selection: Access full transition and locality objects
- Similar pattern to Report Panel's reaction table

**Files to Modify**:
- `diagnosis_category.py` - Replace locality_combo
- Add selection handler that captures transition+locality objects

### 2. ⏳ Add "Repair" Button Per Category

**Implementation Plan**:
- Add "Repair Selected" button to each category header
- Button only enabled when category is expanded and has suggestions
- Clicking applies all suggestions in that category
- Show confirmation dialog before applying

**Files to Modify**:
- `base_category.py` - Add repair button to `_create_action_buttons()`
- Connect to new `_on_repair_clicked()` method

### 3. ⏳ Display Suggestions as Table

**Current State**: ListBox with custom rows  
**Target State**: TreeView with columns

**Table Columns**:
- Icon (confidence-based: 💡/⚠️/🔴)
- Title
- Description
- Confidence (%)
- Actions (Apply button per row)

**Implementation Plan**:
- Replace `Gtk.ListBox` with `Gtk.TreeView`
- Create `Gtk.ListStore` with columns: [Icon, Title, Description, Confidence, SuggestionDict]
- Add cell renderer for "Apply" button in Actions column
- Handle row selection and apply button clicks

**Files to Modify**:
- `base_category.py` - `_display_issues()` method
- Each category's `_create_issue_row()` method

---

## Testing Checklist

After completing pending changes:

- [ ] Test combo box captures transition and locality correctly
- [ ] Test "Run Full Diagnose" button generates suggestions
- [ ] Test "Repair" button applies all suggestions in category
- [ ] Test table displays all suggestion data correctly
- [ ] Test Apply button per row works
- [ ] Test confirmation dialogs appear before applying
- [ ] Test UI remains responsive during operations
- [ ] Verify no crashes or errors

---

## Implementation Notes

### Combo Box Refactor Details

The combo box needs to store full objects, not just strings. Pattern to follow:

```python
# Instead of:
self.locality_combo = Gtk.ComboBoxText()
self.locality_combo.append_text("T1 - Reaction Name")

# Use:
# ListStore: [str: trans_id, str: trans_name, object: transition, object: locality]
self.locality_store = Gtk.ListStore(str, str, object, object)
self.locality_view = Gtk.TreeView(model=self.locality_store)

# On selection:
selection = self.locality_view.get_selection()
model, tree_iter = selection.get_selected()
if tree_iter:
    transition_obj = model[tree_iter][2]  # Get transition object
    locality_obj = model[tree_iter][3]    # Get locality object
```

### Table Format Details

Each category should display suggestions in a table with these columns:

| Icon | Title | Description | Confidence | Actions |
|------|-------|-------------|------------|---------|
| 💡   | Add initial tokens... | Transition T6 never... | 80% | [Apply] |
| ⚠️   | Map place P17... | Place lacks compound... | 60% | [Apply] |

---

## Files Modified

1. `viability_panel.py` - Title and button changes
2. `diagnosis_category.py` - Removed health score and apply all
3. `base_category.py` - Removed undo last button

## Next Steps

1. Implement combo box refactor (transition + locality capture)
2. Add "Repair" button to category headers
3. Convert suggestion display from ListBox to TreeView table
4. Test all functionality end-to-end
5. Update documentation

---

**Estimated Time Remaining**: 2-3 hours for pending changes
