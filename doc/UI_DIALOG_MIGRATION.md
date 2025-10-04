# Property Dialog UI Files Migration

## Summary
Copied and renamed property dialog UI files from legacy resources to the new ui/dialogs directory structure.

## Files Migrated

| Source (legacy) | Destination (new) | Size | Purpose |
|----------------|-------------------|------|---------|
| `legacy/shypnpy/ui/resources/arc.ui` | `ui/dialogs/arc_prop_dialog.ui` | 29 KB | Arc properties dialog |
| `legacy/shypnpy/ui/resources/place.ui` | `ui/dialogs/place_prop_dialog.ui` | 20 KB | Place properties dialog |
| `legacy/shypnpy/ui/resources/transition_enhanced.ui` | `ui/dialogs/transition_prop_dialog.ui` | 36 KB | Transition properties dialog |

## Naming Convention

Files were renamed to follow a consistent naming pattern:
- **Pattern**: `{object_type}_prop_dialog.ui`
- **Consistency**: All property dialog UI files now have the `_prop_dialog` suffix
- **Clarity**: The naming clearly indicates these are property dialogs, not the objects themselves

## Directory Structure

```
ui/
└── dialogs/
    ├── arc_prop_dialog.ui          # Arc properties (weight, type)
    ├── place_prop_dialog.ui         # Place properties (name, marking, capacity)
    └── transition_prop_dialog.ui    # Transition properties (name, priority, timing)
```

## Next Steps

To use these UI files in the application:

1. **Create dialog loaders** in `src/shypn/ui/dialogs/`:
   ```python
   # arc_prop_dialog.py
   # place_prop_dialog.py
   # transition_prop_dialog.py
   ```

2. **Load UI with Gtk.Builder**:
   ```python
   builder = Gtk.Builder()
   builder.add_from_file('ui/dialogs/arc_prop_dialog.ui')
   dialog = builder.get_object('arc_dialog')
   ```

3. **Wire up signals** and connect to object properties

4. **Integrate with context menus** in model_canvas_loader.py

## Benefits

✓ **Centralized location**: All dialog UI files in one place  
✓ **Consistent naming**: Easy to identify property dialogs  
✓ **Clean separation**: UI definitions separate from code  
✓ **Ready for integration**: Files ready to be loaded by dialog controllers  
✓ **Version control**: Easier to track changes to UI definitions

## Date
October 3, 2025
