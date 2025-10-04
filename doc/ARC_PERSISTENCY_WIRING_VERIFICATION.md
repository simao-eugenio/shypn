# Arc Properties Dialog - Persistency Wiring Verification

## Date: October 4, 2025

## Current Arc Object Properties

From `src/shypn/netobjs/arc.py`:

| Property | Type | Mutable | In UI | Wired to Persistency |
|----------|------|---------|-------|---------------------|
| `id` | int | ❌ Immutable | ❌ No | N/A (system-assigned) |
| `name` | str | ❌ Immutable | ✅ Yes (read-only) | N/A (system-assigned) |
| `source` | Object | ❌ Immutable | ✅ Yes (info display) | N/A (connection) |
| `target` | Object | ❌ Immutable | ✅ Yes (info display) | N/A (connection) |
| `label` | str | ✅ Mutable | ✅ Yes (description_text) | ✅ **WIRED** |
| `weight` | int | ✅ Mutable | ✅ Yes (prop_arc_weight_entry) | ✅ **WIRED** |
| `color` | tuple | ✅ Mutable | ✅ Yes (arc_color_picker) | ✅ **WIRED** |
| `width` | float | ✅ Mutable | ✅ Yes (prop_arc_line_width_spin) | ✅ **WIRED** |
| `control_points` | list | ✅ Mutable | ❌ No | ❌ Not implemented yet |

## UI Fields Status

### Implemented and Wired ✅

1. **Name Field** (`name_entry`)
   - **Source**: `_populate_fields()` line 123-126
   - **Action**: Displays arc.name, set to read-only
   - **Persistency**: N/A (immutable system property)

2. **Description/Label Field** (`description_text`)
   - **Populate**: `_populate_fields()` line 128-132
   - **Apply**: `_apply_changes()` line 186-191
   - **Persistency**: ✅ Updates `arc.label`
   - **Trigger**: Mark dirty + emit signal

3. **Weight Field** (`prop_arc_weight_entry`)
   - **Populate**: `_populate_fields()` line 134-137
   - **Apply**: `_apply_changes()` line 193-199
   - **Persistency**: ✅ Updates `arc.weight`
   - **Validation**: Minimum value 1
   - **Error handling**: Keeps current value on invalid input
   - **Trigger**: Mark dirty + emit signal

4. **Line Width Field** (`prop_arc_line_width_spin`)
   - **Populate**: `_populate_fields()` line 139-142
   - **Apply**: `_apply_changes()` line 201-204
   - **Persistency**: ✅ Updates `arc.width`
   - **Range**: 0.5 - 10.0 (defined in UI adjustment)
   - **Trigger**: Mark dirty + emit signal

5. **Color Picker** (`arc_color_picker`)
   - **Setup**: `_setup_color_picker()` line 96-107
   - **Apply**: `_apply_changes()` line 206-209
   - **Persistency**: ✅ Updates `arc.color`
   - **Options**: 21 predefined colors
   - **Trigger**: Mark dirty + emit signal

6. **Source Info** (`source_info_label`)
   - **Populate**: `_populate_fields()` line 144-151
   - **Action**: Display only (read-only)
   - **Persistency**: N/A (connection property)

7. **Target Info** (`target_info_label`)
   - **Populate**: `_populate_fields()` line 144-151
   - **Action**: Display only (read-only)
   - **Persistency**: N/A (connection property)

### Future Features (In UI but Not Implemented) 🔮

1. **Arc Type Combo** (`prop_arc_type_combo`)
   - **Status**: Widget exists in UI
   - **Options**: Normal, Inhibitor, Test
   - **Arc Property**: Does not exist yet
   - **Action Needed**: Add arc type property to Arc class

2. **Threshold Expression** (`prop_arc_threshold_entry`)
   - **Status**: Widget exists in UI (TextView)
   - **Purpose**: For test arcs with conditions
   - **Arc Property**: Does not exist yet
   - **Action Needed**: Add threshold property to Arc class

## Persistency Flow Verification

### When Dialog Opens:
```
1. create_arc_prop_dialog(arc_obj, ..., persistency_manager)
   ↓
2. ArcPropDialogLoader.__init__()
   ↓
3. _load_ui() - Load UI, wire OK/Cancel buttons
   ↓
4. _setup_color_picker() - Insert color picker widget
   ↓
5. _populate_fields() - Load arc properties into UI
   ↓
6. Dialog displayed to user
```

### When User Clicks OK:
```
1. OK button clicked
   ↓
2. dialog.response(Gtk.ResponseType.OK)
   ↓
3. _on_response() called
   ↓
4. _apply_changes() - Read all fields and update arc object
   │  ├─ label from description_text
   │  ├─ weight from prop_arc_weight_entry (validated ≥1)
   │  ├─ width from prop_arc_line_width_spin
   │  └─ color from color_picker.get_selected_color()
   ↓
5. persistency_manager.mark_dirty() ✅
   ↓
6. emit('properties-changed') ✅
   ↓
7. Canvas redraws with updated arc ✅
   ↓
8. dialog.destroy()
```

### When User Clicks Cancel:
```
1. Cancel button clicked
   ↓
2. dialog.response(Gtk.ResponseType.CANCEL)
   ↓
3. _on_response() called
   ↓
4. Skip _apply_changes()
   ↓
5. Skip mark_dirty()
   ↓
6. Skip emit signal
   ↓
7. dialog.destroy()
```

## Persistency Integration Points

### 1. Mark Document Dirty ✅
```python
# Line 176-178
if self.persistency_manager:
    self.persistency_manager.mark_dirty()
    print(f"[ArcPropDialogLoader] Document marked as dirty")
```
**Status**: ✅ Properly implemented

### 2. Emit Properties Changed Signal ✅
```python
# Line 180-181
self.emit('properties-changed')
print(f"[ArcPropDialogLoader] Properties changed signal emitted")
```
**Status**: ✅ Properly implemented

### 3. Canvas Redraw ✅
```python
# In model_canvas_loader.py:
dialog_loader.connect('properties-changed', self._on_properties_changed)

def _on_properties_changed(self, dialog_loader):
    # Force canvas redraw
    self.drawing_area.queue_draw()
```
**Status**: ✅ Connected in model_canvas_loader

## Validation and Error Handling

### Weight Field Validation ✅
```python
try:
    weight_text = weight_entry.get_text().strip()
    weight_value = int(weight_text) if weight_text else 1
    self.arc_obj.weight = max(1, weight_value)  # Minimum weight is 1
except ValueError:
    print(f"[ArcPropDialogLoader] Invalid weight value, keeping current: {self.arc_obj.weight}")
```
**Features**:
- Empty input defaults to 1
- Negative/zero values clamped to 1
- Non-numeric input keeps current value
- No crash on invalid input

### Line Width Range Constraint ✅
Defined in UI file (line_width_adjustment):
```xml
<property name="lower">0.5</property>
<property name="upper">10</property>
```
**Status**: ✅ Automatically enforced by SpinButton

### Color Validation ✅
- Color picker only returns valid RGB tuples
- Pre-selected colors are all valid
- No manual validation needed

## Testing Checklist

### Basic Functionality ✅
- [x] Dialog opens with current arc values
- [x] Name field is read-only
- [x] Source/Target info displayed correctly
- [x] All editable fields can be modified
- [x] OK button applies changes
- [x] Cancel button discards changes

### Persistency Integration ✅
- [x] Document marked dirty on OK
- [x] Document not marked dirty on Cancel
- [x] Properties-changed signal emitted
- [x] Canvas redraws after changes
- [x] Window title shows asterisk when dirty

### Data Integrity ✅
- [x] Label updates correctly (including empty → None)
- [x] Weight validated (≥1, integer)
- [x] Width updates correctly (float)
- [x] Color updates correctly (RGB tuple)
- [x] Arc object modified in memory
- [x] Changes visible on canvas immediately

### Visual Effects ✅
- [x] Colored arcs show glow effect
- [x] Weight label displays if >1
- [x] Line width changes visible
- [x] Arrowhead rendered in arc color

## Conclusion

### ✅ ALL USER INPUTS ARE PROPERLY WIRED TO PERSISTENCY

**Summary**:
- **4 mutable properties** fully implemented and wired
- **3 immutable/display fields** properly handled
- **Persistency manager** integration complete
- **Signal emission** working correctly
- **Canvas redraw** triggered automatically
- **Validation** in place for numeric inputs
- **Error handling** prevents crashes

**Future Work**:
- Arc Type selection (requires Arc class extension)
- Threshold expression (requires Arc class extension)
- Control points editing (requires UI implementation)

**Status**: ✅ **PRODUCTION READY**

All currently implemented arc properties are properly wired to the persistency system with appropriate validation, error handling, and canvas integration.
