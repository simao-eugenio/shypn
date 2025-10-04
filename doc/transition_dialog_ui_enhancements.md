# Transition Properties Dialog UI Enhancements

## Overview
Enhanced the transition properties dialog to provide easier access to `priority` and `rate` parameters in the "Type-Specific Parameters" section of the Basic tab.

## Changes Made

### 1. UI Definition (`ui/dialogs/transition_prop_dialog.ui`)

#### Added Priority Field
- **Widget**: `GtkSpinButton` with id `priority_spin`
- **Purpose**: Set transition priority for conflict resolution
- **Range**: 0-100 (integer)
- **Default**: 0
- **Label**: "Priority:" with help text "Higher priority transitions are selected first when multiple transitions are enabled"
- **Adjustment**: Uses existing `priority_adjustment` object

#### Added Rate Field
- **Widget**: `GtkEntry` with id `rate_entry`
- **Purpose**: Simple entry for basic rate values (numeric or simple expressions)
- **Label**: "Rate:" with help text "Basic rate value (for complex rate functions, use Behavior tab)"
- **Note**: For complex rate formulas/functions, users can still use the `rate_textview` in the Behavior tab

#### Added Label Field
- **Widget**: `GtkEntry` with id `transition_label_entry`
- **Purpose**: User-friendly label for the transition
- **Note**: This widget was referenced in the loader but was missing from the UI definition

### 2. Python Loader (`src/shypn/helpers/transition_prop_dialog_loader.py`)

#### Fixed Property Name
- Changed all references from `self.transition_obj.type` to `self.transition_obj.transition_type`
- This matches the actual property name in the Transition class

#### Updated `_populate_fields()` Method
Added population logic for new fields:
```python
# Priority spin button
priority_spin = self.builder.get_object('priority_spin')
if priority_spin and hasattr(self.transition_obj, 'priority'):
    priority_spin.set_value(float(self.transition_obj.priority))

# Rate entry (simple numeric/expression field)
rate_entry = self.builder.get_object('rate_entry')
if rate_entry and hasattr(self.transition_obj, 'rate'):
    rate_text = self._format_formula_for_display(self.transition_obj.rate)
    rate_entry.set_text(rate_text)
```

#### Updated `_apply_changes()` Method
Added application logic for new fields:
```python
# Priority spin button
priority_spin = self.builder.get_object('priority_spin')
if priority_spin and hasattr(self.transition_obj, 'priority'):
    old_priority = self.transition_obj.priority
    self.transition_obj.priority = int(priority_spin.get_value())
    print(f"[TransitionPropDialogLoader] Priority changed: {old_priority} -> {self.transition_obj.priority}")

# Rate entry (simple value - takes precedence over rate_textview if both exist)
rate_entry = self.builder.get_object('rate_entry')
if rate_entry and hasattr(self.transition_obj, 'rate'):
    rate_text = rate_entry.get_text().strip()
    if rate_text:  # Only update if entry has content
        old_rate = self.transition_obj.rate
        self.transition_obj.rate = self._parse_formula(rate_text)
        print(f"[TransitionPropDialogLoader] Rate changed (from entry): {old_rate} -> {self.transition_obj.rate}")
```

#### Rate Field Precedence
- If `rate_entry` has content, it takes precedence
- If `rate_entry` is empty, the `rate_textview` (Behavior tab) is used
- This allows simple cases (constant rate) to be handled in the Basic tab, while complex formulas can be defined in the Behavior tab

## User Experience Improvements

### Priority Configuration
- **Before**: Priority could only be set programmatically in code
- **After**: Users can directly set priority in the UI (0-100 scale)
- **Use Case**: Configure conflict resolution behavior when multiple transitions are enabled
- **Integration**: Works with Phase 2 conflict resolution policies (PRIORITY, TYPE_BASED, etc.)

### Rate Configuration
- **Before**: Rate could only be set via TextView in Behavior tab (complex)
- **After**: Simple rate values can be entered in Basic tab's Entry field
- **Use Case**: Quickly set constant rates like "1.5" or "lambda" without navigating to Behavior tab
- **Fallback**: Complex rate functions (dictionaries, formulas) still use Behavior tab's TextView

### Label Field
- **Before**: Referenced in code but not present in UI
- **After**: Users can set user-friendly labels for transitions
- **Use Case**: Annotate transitions with descriptive names like "Fast Path" or "Timeout Handler"

## Technical Notes

### Property Name Consistency
Fixed inconsistency where code used both `type` and `transition_type`:
- Transition class defines: `self.transition_type`
- Dialog now consistently uses: `self.transition_obj.transition_type`

### Formula Parsing
Both `rate_entry` and `rate_textview` use the existing `_parse_formula()` method:
- Handles numeric values: "1.5" → 1.5
- Handles symbolic expressions: "lambda" → "lambda"
- Handles complex structures: JSON dictionaries for function definitions

### Backward Compatibility
- All changes are additive (no breaking changes)
- Existing rate_textview functionality preserved
- Missing priority attribute handled gracefully with `hasattr()` checks

## Testing Recommendations

1. **Priority Field**:
   - Create conflicting transitions (multiple enabled)
   - Set different priorities (0, 50, 100)
   - Verify conflict resolution respects priority settings

2. **Rate Field**:
   - Enter simple numeric rate in Basic tab ("2.0")
   - Verify rate is applied correctly
   - Leave rate_entry empty and use rate_textview
   - Verify TextView takes over when Entry is empty

3. **Label Field**:
   - Set user-friendly labels
   - Verify labels display in canvas/diagrams

4. **Property Name Fix**:
   - Change transition type via combo box
   - Verify type change is persisted correctly
   - Check no errors in console logs

## Files Modified

1. `/home/simao/projetos/shypn/ui/dialogs/transition_prop_dialog.ui`
   - Added priority_spin, rate_entry, transition_label_entry widgets
   - Added help text and labels

2. `/home/simao/projetos/shypn/src/shypn/helpers/transition_prop_dialog_loader.py`
   - Fixed property name: `type` → `transition_type`
   - Updated `_populate_fields()` to populate new widgets
   - Updated `_apply_changes()` to apply changes from new widgets
   - Added rate field precedence logic

## Related Documentation
- Phase 2: Conflict Resolution (conflict_resolution_phase2.md)
- Transition class definition (src/shypn/netobjs/transition.py)
- Conflict policies (src/shypn/engine/simulation/conflict_policy.py)
