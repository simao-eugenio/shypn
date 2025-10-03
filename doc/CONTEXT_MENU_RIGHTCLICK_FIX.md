# Context Menu Right-Click Fix

## Issue
The context menu was only appearing when right-clicking directly on a file or folder row. Right-clicking on empty space in the file browser did not trigger the menu.

## Root Cause
The `_on_tree_view_right_click()` handler had this logic:
```python
result = self.tree_view.get_path_at_pos(int(x), int(y))

if result is not None:
    # ... show context menu
    # BUT: Only when clicking on a row!
```

When clicking on empty space, `get_path_at_pos()` returns `None`, and the menu was never shown.

## Solution
Modified the handler to support clicking anywhere:

```python
result = self.tree_view.get_path_at_pos(int(x), int(y))

if result is not None:
    # Clicked on a row - select that item
    path, column, cell_x, cell_y = result
    iter = self.store.get_iter(path)
    self.selected_item_name = self.store.get_value(iter, 1)
    self.selected_item_path = self.store.get_value(iter, 2)
    self.selected_item_is_dir = self.store.get_value(iter, 3)
else:
    # Clicked on empty space - use current directory
    self.selected_item_name = os.path.basename(self.explorer.current_path)
    self.selected_item_path = self.explorer.current_path
    self.selected_item_is_dir = True

# Show context menu at click position (always!)
rect = Gtk.Rectangle()
rect.x = int(x)
rect.y = int(y)
rect.width = 1
rect.height = 1

self.context_menu.set_pointing_to(rect)
self.context_menu.popup()
```

## Behavior Changes

### Before Fix
```
Right-click on file/folder → ✓ Context menu appears
Right-click on empty space  → ✗ Nothing happens
```

### After Fix
```
Right-click on file/folder → ✓ Context menu appears (item operations)
Right-click on empty space  → ✓ Context menu appears (directory operations)
```

## Use Cases Enabled

### Right-Click on Empty Space
When you right-click on empty space, the context menu now appears with the **current directory** selected as the target. This enables:

1. **New Folder** - Create new folder in current directory
2. **Paste** - Paste cut/copied items into current directory
3. **Refresh** - Refresh current directory view
4. **Properties** - View properties of current directory

### Right-Click on File/Folder
When you right-click on a specific file or folder, all operations work on that item:

1. **Open** - Open the file
2. **Cut/Copy** - Cut or copy the item
3. **Duplicate** - Duplicate the item
4. **Rename** - Rename the item
5. **Delete** - Delete the item
6. **Properties** - View item properties

## Context-Aware Operations

Some operations behave differently based on what's selected:

### Paste Operation
```python
# Determine destination directory
if self.selected_item_is_dir:
    dest_dir = self.selected_item_path  # Paste INTO selected folder
else:
    dest_dir = self.explorer.current_path  # Paste INTO current directory
```

### Open Operation
```python
if self.selected_item_path and not self.selected_item_is_dir:
    # Only open files, not folders
    self.set_current_file(self.selected_item_path)
```

## Benefits

1. **More Intuitive** - Matches behavior of standard file managers (Windows Explorer, Nautilus, Finder)
2. **Easier New Folder Creation** - Don't need to right-click on specific items
3. **Better Paste Target** - Can paste directly into current directory
4. **Consistent UX** - Context menu always available

## Testing

Verified with test script `scripts/test_right_click.py`:
```
✓ Empty space click handled correctly
✓ Context menu object exists
✓ Menu appears on any right-click
✓ Current directory used as target for empty space clicks
```

## File Modified
- `src/shypn/ui/panels/file_explorer_panel.py`
  - Method: `_on_tree_view_right_click()`
  - Lines: ~530-560

## Common Workflows Now Supported

### Create Folder in Empty Directory
```
1. Right-click anywhere in file browser
2. Select "New Folder"
3. Enter name → Done!
```

### Paste Into Current Directory
```
1. Right-click file → Copy
2. Navigate to destination
3. Right-click empty space → Paste
4. File appears in current directory
```

### Quick Directory Operations
```
Right-click empty space for:
- New Folder
- Paste clipboard contents
- Refresh view
- View directory properties
```

## Notes

- Empty space clicks set `selected_item_is_dir = True` (always a directory)
- Empty space clicks set `selected_item_path` to current directory
- This allows all directory-appropriate operations
- File-specific operations (like Open) naturally don't apply
