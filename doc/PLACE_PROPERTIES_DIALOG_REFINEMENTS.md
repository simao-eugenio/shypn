# Place Properties Dialog Refinements

## Overview

This document describes the refinements made to the Place properties dialog to properly wire the OK/Cancel buttons, handle data persistence, and display tokens in the place circle.

## Issues Fixed

### 1. Missing OK/Cancel Buttons
**Problem**: Buttons were not appearing in the dialog after initial implementation.

**Root Cause**: Incorrect GTK3 dialog structure - buttons were removed from action area when trying to wire them.

**Solution**: Properly structured the GTK dialog with:
- Buttons defined in the action area's button box
- `<action-widgets>` section mapping buttons to GTK response codes
- Response codes: `-6` for Cancel (GTK_RESPONSE_CANCEL), `-5` for OK (GTK_RESPONSE_OK)

### 2. AttributeError: 'name' property has no setter
**Problem**: Application crashed when clicking OK due to attempting to set read-only `name` property.

```
AttributeError: property 'name' of 'Place' object has no setter
```

**Root Cause**: The `name` property in `PetriNetObject` is immutable (system-assigned), but the dialog was trying to update it.

**Solution**: 
- Made name field read-only in the UI by calling `set_editable(False)`
- Removed name update logic from `_apply_changes()`
- Only update mutable properties: `tokens`, `radius`, and `label`

### 3. Widget ID Mismatches
**Problem**: Dialog loader was looking for wrong widget IDs.

**Mismatches**:
- Looking for `place_name_entry` but UI has `name_entry`
- Looking for `place_marking_spin` (SpinButton) but UI has `prop_place_tokens_entry` (Entry)
- Looking for `place_label_entry` but description is in `description_text` (TextView)

**Solution**: Updated `_populate_fields()` and `_apply_changes()` to use correct widget IDs.

## Implementation Details

### UI File Changes (`place_prop_dialog.ui`)

#### 1. Button Definitions
```xml
<child>
  <object class="GtkButton" id="cancel_button">
    <property name="label">gtk-cancel</property>
    <property name="visible">True</property>
    <property name="can_focus">True</property>
    <property name="receives_default">True</property>
    <property name="use_stock">True</property>
  </object>
  ...
</child>

<child>
  <object class="GtkButton" id="ok_button">
    <property name="label">gtk-ok</property>
    <property name="visible">True</property>
    <property name="can_focus">True</property>
    <property name="receives_default">True</property>
    <property name="can_default">True</property>
    <property name="has_default">True</property>
    <property name="use_stock">True</property>
  </object>
  ...
</child>
```

#### 2. Action Widgets Mapping
```xml
<action-widgets>
  <action-widget response="-6">cancel_button</action-widget>
  <action-widget response="-5">ok_button</action-widget>
</action-widgets>
```

This maps:
- `cancel_button` → `Gtk.ResponseType.CANCEL` (-6)
- `ok_button` → `Gtk.ResponseType.OK` (-5)

### Loader Changes (`place_prop_dialog_loader.py`)

#### 1. Populate Fields - Make Name Read-Only
```python
def _populate_fields(self):
    """Populate dialog fields with current Place properties."""
    # Name field (read-only, system-assigned)
    name_entry = self.builder.get_object('name_entry')
    if name_entry and hasattr(self.place_obj, 'name'):
        name_entry.set_text(str(self.place_obj.name))
        name_entry.set_editable(False)  # Name is immutable
        name_entry.set_can_focus(False)
    
    # Tokens field (Entry widget)
    tokens_entry = self.builder.get_object('prop_place_tokens_entry')
    if tokens_entry and hasattr(self.place_obj, 'tokens'):
        tokens_entry.set_text(str(self.place_obj.tokens))
    
    # Radius field (Entry widget)
    radius_entry = self.builder.get_object('prop_place_radius_entry')
    if radius_entry and hasattr(self.place_obj, 'radius'):
        radius_entry.set_text(str(self.place_obj.radius))
    
    # Description field (TextView)
    description_text = self.builder.get_object('description_text')
    if description_text and hasattr(self.place_obj, 'label'):
        buffer = description_text.get_buffer()
        buffer.set_text(str(self.place_obj.label) if self.place_obj.label else '')
```

#### 2. Apply Changes - Skip Immutable Name
```python
def _apply_changes(self):
    """Apply changes from dialog fields to Place object."""
    # Name field is read-only (immutable, system-assigned) - skip it
    
    # Tokens field (Entry widget - parse as float/int)
    tokens_entry = self.builder.get_object('prop_place_tokens_entry')
    if tokens_entry and hasattr(self.place_obj, 'tokens'):
        try:
            tokens_text = tokens_entry.get_text().strip()
            if tokens_text:
                # Try parsing as int first, then float
                if '.' in tokens_text:
                    tokens_value = float(tokens_text)
                else:
                    tokens_value = int(tokens_text)
                self.place_obj.tokens = max(0, tokens_value)  # Ensure non-negative
                print(f"[PlacePropDialogLoader] Set tokens to {self.place_obj.tokens}")
        except ValueError as e:
            print(f"[PlacePropDialogLoader] Invalid tokens value: {tokens_text}, error: {e}")
    
    # ... radius and description handling ...
```

## Data Flow

### Complete Property Edit Flow

```
1. User right-clicks Place → "Properties"
   ↓
2. ModelCanvasLoader._on_object_properties() creates dialog
   ↓
3. PlacePropDialogLoader.__init__()
   - Loads UI from place_prop_dialog.ui
   - Calls _populate_fields()
   ↓
4. _populate_fields()
   - Sets name field (read-only)
   - Sets tokens field (editable)
   - Sets radius field (editable)
   - Sets description field (editable)
   ↓
5. Dialog.run() - waits for user interaction
   ↓
6. User modifies tokens: 0 → 25
   ↓
7. User clicks OK button
   ↓
8. Dialog emits 'response' signal with response_id = Gtk.ResponseType.OK (-5)
   ↓
9. _on_response(dialog, response_id)
   - Checks if response_id == Gtk.ResponseType.OK
   - Calls _apply_changes()
   ↓
10. _apply_changes()
    - Skips name (read-only)
    - Parses tokens: "25" → int(25)
    - Sets place_obj.tokens = 25
    - Parses radius
    - Sets place_obj.label from description
    ↓
11. Mark document dirty
    - persistency_manager.mark_dirty()
    - Triggers on_dirty_changed callback
    - FileExplorer shows asterisk (*)
    ↓
12. Emit 'properties-changed' signal
    - Signal handler calls drawing_area.queue_draw()
    - Canvas redraws with new token count
    ↓
13. Place.render() draws tokens inside circle
    - If tokens > 0, calls _render_tokens()
    - Displays token count as centered text
    ↓
14. Dialog.destroy()
    - Cleanup and close
```

## Visual Result

### Before Dialog:
```
    ○
    
  (Empty place, no tokens)
```

### After Setting Tokens to 25:
```
    ○
   25
    
  (Place with 25 tokens displayed)
```

### File Explorer:
```
Before: models/mynet.shy
After:  models/mynet.shy (*)  ← Indicates unsaved changes
```

## Testing Performed

### Test 1: Basic Token Setting
1. ✅ Created place P1
2. ✅ Right-clicked → Properties
3. ✅ Dialog opened with OK/Cancel buttons visible
4. ✅ Name field showed "P1" (read-only, grayed out)
5. ✅ Set tokens to 25
6. ✅ Clicked OK
7. ✅ Tokens appeared in place circle
8. ✅ Document marked dirty (*)

**Console Output:**
```
[PlacePropDialogLoader] UI loaded successfully
[PlacePropDialogLoader] Set tokens to 25
[PlacePropDialogLoader] Set radius to 25.0
[PlacePropDialogLoader] Applied changes to Place: P1, tokens=25
[Persistency] Document marked as dirty (has unsaved changes)
[Draw] Rendering 1 objects: 1 places, 0 transitions, 0 arcs
```

### Test 2: Cancel Button
1. ✅ Opened properties
2. ✅ Changed tokens
3. ✅ Clicked Cancel
4. ✅ No changes applied
5. ✅ Document not marked dirty

### Test 3: Invalid Input Handling
1. ✅ Set tokens to "abc" (invalid)
2. ✅ Clicked OK
3. ✅ Console showed error message
4. ✅ No crash, dialog closed gracefully

## Key Design Decisions

### 1. Read-Only Name Field
**Decision**: Make name field non-editable instead of hiding it.

**Rationale**:
- Users need to see the system-assigned name (P1, P2, etc.)
- Visual distinction between system-assigned (read-only) and user-editable properties
- Follows common UI patterns for displaying immutable identifiers

**Implementation**:
```python
name_entry.set_editable(False)
name_entry.set_can_focus(False)
```

### 2. Flexible Token Type (int/float)
**Decision**: Support both integer and floating-point token values.

**Rationale**:
- Petri nets can use both discrete and continuous tokens
- Different modeling approaches may require fractional tokens
- User freedom vs. strict validation

**Implementation**:
```python
if '.' in tokens_text:
    tokens_value = float(tokens_text)
else:
    tokens_value = int(tokens_text)
```

### 3. Entry Widgets Instead of SpinButtons
**Decision**: Use GtkEntry instead of GtkSpinButton for numeric fields.

**Rationale**:
- More flexible input (can paste values)
- Simpler UI file (no adjustment objects needed)
- Better for large ranges
- Manual validation gives more control

### 4. Description Maps to Label
**Decision**: Map "Description" TextView to Place.label property.

**Rationale**:
- Users think of "description" as explanatory text
- Label property stores user-editable text
- Consistent with other properties dialog patterns

## Files Modified

1. **`ui/dialogs/place_prop_dialog.ui`**
   - Added OK/Cancel buttons to action area
   - Added `<action-widgets>` mapping
   - Configured button properties (stock icons, default button)

2. **`src/shypn/helpers/place_prop_dialog_loader.py`**
   - Updated `_populate_fields()` to use correct widget IDs
   - Made name field read-only
   - Updated `_apply_changes()` to skip name property
   - Added proper error handling for invalid numeric inputs
   - Added debug logging for token and radius changes

## Known Limitations

1. **No Input Validation UI**: Invalid inputs show console errors but no user-facing error dialog
2. **No Undo**: Changes are immediately applied with no undo option
3. **No Range Validation**: Accepts any positive number for tokens/radius
4. **Description Length**: No character limit on description field

## Future Enhancements

### Priority 1 - Input Validation
- Add visual validation feedback (red border for invalid input)
- Show error dialog for invalid values
- Prevent dialog from closing with invalid data

### Priority 2 - User Experience
- Add tooltips explaining each field
- Add "Reset" button to restore original values
- Show token count preview in dialog

### Priority 3 - Advanced Features
- Add capacity field (maximum tokens)
- Add color picker for place color
- Support for multiple token types (colored tokens)
- Live preview of changes before applying

## Conclusion

The Place properties dialog now works correctly with:
- ✅ Visible and functional OK/Cancel buttons
- ✅ Proper handling of immutable properties (name)
- ✅ Correct widget ID mappings
- ✅ Token persistence and rendering
- ✅ Document dirty state tracking
- ✅ Canvas redraw after changes

All three main requirements have been met:
1. **OK/Cancel buttons wired** - Buttons respond to clicks and trigger appropriate actions
2. **Data persistence** - Changes are saved to the Place object and document is marked dirty
3. **Tokens displayed** - Token count appears in the place circle after setting
