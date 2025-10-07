# Unsaved Changes Protection

## Overview
The application now checks for unsaved changes before closing to prevent accidental data loss.

## Feature Details

### Window Close (X Button)
When the user clicks the window close button (X), the application:

1. **Iterates through all open document tabs**
2. **Checks each tab for unsaved changes** (dirty flag)
3. **Prompts the user** for each document with unsaved changes:
   - **Save**: Saves the document and continues closing
   - **Close Without Saving**: Discards changes and continues
   - **Cancel**: Cancels the close operation and keeps the window open

### Multiple Tabs
- If you have multiple tabs open with unsaved changes, you'll be prompted for **each dirty tab**
- You can choose to save or discard changes for each document independently
- Clicking "Cancel" on any prompt will stop the close operation

### Save Behavior
- If a document has never been saved (uses "default.shy" filename), the save dialog will prompt for a new filename
- If a document has been saved before, it will be saved to the same location
- If the save operation is cancelled (user cancels the file chooser), the window will not close

## Paths That Check for Unsaved Changes

### ✅ Implemented
1. **Window close (X button)** - Checks all open tabs
2. **Tab close button** - Checks the specific tab being closed (existing feature)
3. **File → New** - Checks current document before creating new (existing feature in canvas loader)
4. **File → Open** - Checks current document before opening new (existing feature in file explorer)

### Implementation Location

**Window Close Handler** (`src/shypn.py`):
```python
def on_window_delete(window, event):
    """Handle window close event.
    
    1. Check for unsaved changes in all open document tabs
    2. Prompt user to save if needed for each dirty document
    3. Save window geometry if closing is allowed
    
    Returns:
        bool: True to prevent closing, False to allow closing
    """
    # Iterates through all notebook pages
    # Prompts for each dirty document
    # Attempts to save if user chooses "Save"
    # Prevents closing if user chooses "Cancel" or save fails
```

**Tab Close Handler** (`src/shypn/helpers/model_canvas_loader.py`):
```python
def close_tab(self, page_num):
    """Close a tab after checking for unsaved changes."""
    # Uses persistency.check_unsaved_changes()
    # Returns False if user cancels
```

**File Operations** (`src/shypn/ui/panels/file_explorer_panel.py` and `model_canvas_loader.py`):
- New document creation checks for unsaved changes
- Opening files checks for unsaved changes
- Uses `persistency.check_unsaved_changes()`

## Dirty State Tracking

The dirty flag is managed by `NetObjPersistency` class:

### When Documents Become Dirty
- Adding objects (places, transitions, arcs)
- Deleting objects
- Moving objects
- Editing object properties
- Any modification to the canvas

### When Documents Become Clean
- After successful save operation
- After creating a new document
- After loading a document

### Integration Points
The dirty flag is set through:
1. **Property dialogs** call `persistency.mark_dirty()` when changes are applied
2. **Canvas operations** call `persistency.mark_dirty()` after modifications
3. **Context menu operations** mark dirty after object deletion/modification

## User Experience

### Example Flow - Closing with Unsaved Changes

1. User has 2 tabs open:
   - Tab 1: "model1.shy" (saved, no changes)
   - Tab 2: "default.shy" (new, has changes)

2. User clicks window close (X)

3. Application skips Tab 1 (no changes)

4. Application shows dialog for Tab 2:
   ```
   Unsaved changes
   
   Document 'default.shy' has unsaved changes.
   Do you want to save before closing?
   
   [Cancel] [Close Without Saving] [Save]
   ```

5. If user clicks "Save":
   - Save dialog appears prompting for filename
   - If save succeeds, window closes
   - If save is cancelled, window stays open

6. If user clicks "Close Without Saving":
   - Changes are discarded
   - Window closes

7. If user clicks "Cancel":
   - Window stays open
   - No changes are lost

## Technical Notes

### Persistency Manager
- One shared instance across all tabs
- Tracks the currently active tab's dirty state
- Must switch tabs before checking dirty state (ensures correct document is checked)

### Tab Switching
The window close handler explicitly switches to each tab before checking:
```python
for page_num in range(num_pages):
    notebook.set_current_page(page_num)
    if persistency and persistency.is_dirty:
        # Prompt user...
```

This ensures the persistency manager is tracking the correct document when checking/saving.

### Save Operation
When user chooses to save:
1. Get the canvas manager for the current tab
2. Generate document model from manager
3. Check if using default filename
4. Call `persistency.save_document()` with proper flags
5. If save fails or is cancelled, prevent window close

## Testing Checklist

- [ ] Close window with no open tabs (should close immediately)
- [ ] Close window with 1 saved tab (should close immediately)
- [ ] Close window with 1 unsaved tab (should prompt)
  - [ ] Click "Save" - should save and close
  - [ ] Click "Close Without Saving" - should discard and close
  - [ ] Click "Cancel" - should keep window open
- [ ] Close window with multiple tabs, some dirty (should prompt for each dirty tab)
- [ ] Click "Save" on new document (should show file chooser)
- [ ] Click "Save" on previously saved document (should save to same location)
- [ ] Cancel save dialog (should keep window open)
- [ ] Close tab with unsaved changes (existing feature, should still work)

## Future Enhancements

Potential improvements:
1. **Show list of all unsaved documents** in a single dialog instead of prompting for each
2. **"Save All"** button to save all dirty documents at once
3. **Visual indicator** on tab labels for dirty state (e.g., asterisk or dot)
4. **Keyboard shortcut** for save (Ctrl+S)
5. **Auto-save** feature with configurable interval

## Related Files

- `src/shypn.py` - Window close handler
- `src/shypn/file/netobj_persistency.py` - Dirty state tracking and save/load operations
- `src/shypn/helpers/model_canvas_loader.py` - Tab management and close tab handler
- `src/shypn/ui/panels/file_explorer_panel.py` - File operations (new, open)

## Summary

The application now provides comprehensive protection against accidental data loss by checking for unsaved changes whenever the window is closed. Users are prompted for each unsaved document and can choose to save, discard, or cancel the operation. This feature integrates with the existing dirty state tracking and save/load infrastructure.
