# File Browser Context Menu - Feature Documentation

## Overview

The file browser now includes a comprehensive context menu triggered by right-clicking on any file or folder in the tree view. The menu provides quick access to common file operations organized into logical sections.

## Menu Structure

The context menu is organized into 5 sections:

### 1. Open Section
- **Open** - Opens the selected file (sets as current file, ready for future editor integration)

### 2. Create Section
- **New Folder** - Creates a new folder in the current directory

### 3. Clipboard Operations Section
- **Cut** - Marks the file/folder for moving (clipboard operation)
- **Copy** - Marks the file/folder for copying (clipboard operation)
- **Paste** - Pastes the cut/copied item to the selected location
- **Duplicate** - Creates a copy of the selected item with "_copy" suffix

### 4. Modification Section
- **Rename** - Opens dialog to rename the selected file/folder
- **Delete** - Deletes the selected file/folder (with confirmation for non-empty folders)

### 5. View Section
- **Refresh** - Refreshes the file list to show any external changes
- **Properties** - Shows detailed information about the selected file/folder

## Features

### Smart Clipboard Operations

#### Copy & Paste
```
1. Right-click on file/folder → Copy
2. Right-click on destination folder → Paste
3. Item is copied with automatic naming (file.txt → file_1.txt if exists)
```

#### Cut & Paste (Move)
```
1. Right-click on file/folder → Cut
2. Right-click on destination folder → Paste
3. Item is moved to destination
4. Clipboard is cleared after successful move
```

#### Duplicate
```
1. Right-click on file/folder → Duplicate
2. Creates copy in same location (file.txt → file_copy.txt)
3. Auto-increments if duplicates exist (file_copy2.txt, file_copy3.txt, etc.)
```

### Visual Feedback

The operations provide clear console feedback:
- 📋 **Copy**: Shows copied item name
- ✂️ **Cut**: Shows cut item name
- ✓ **Success**: Confirms successful operations
- ✗ **Error**: Shows error messages when operations fail
- 🔄 **Refresh**: Indicates list refresh
- → **Open**: Shows opened file path

### Automatic Conflict Resolution

When pasting or duplicating files, the system automatically:
1. Checks if destination name already exists
2. Generates unique name with numeric suffix (_1, _2, etc.)
3. Preserves file extension
4. Handles both files and folders

### Context-Aware Operations

- **Open**: Only available for files (not folders)
- **Paste**: Only enabled when clipboard has content
- **Duplicate**: Works on both files and folders
- **Cut/Copy**: Preserves directory structure when pasting folders

## Implementation Details

### UI Definition (left_panel.ui)
```xml
<menu id="file_browser_context_menu">
  <section><!-- Open --></section>
  <section><!-- New Folder --></section>
  <section><!-- Cut, Copy, Paste, Duplicate --></section>
  <section><!-- Rename, Delete --></section>
  <section><!-- Refresh, Properties --></section>
</menu>
```

### Action System
- Uses `Gio.SimpleActionGroup` for menu actions
- Actions prefixed with "file." namespace
- Connected through `file_explorer_panel.py` controller

### State Management
```python
# Tracks selected item
self.selected_item_path: Optional[str]
self.selected_item_name: Optional[str]
self.selected_item_is_dir: bool

# Tracks clipboard state
self.clipboard_path: Optional[str]
self.clipboard_operation: Optional[str]  # 'cut' or 'copy'
```

## Usage Examples

### Creating a New Folder
1. Right-click anywhere in the file list
2. Select "New Folder"
3. Enter folder name in dialog
4. Click "Create"

### Moving Files (Cut/Paste)
1. Right-click on file to move
2. Select "Cut" (✂️ Cut: filename.txt)
3. Navigate to destination or right-click on destination folder
4. Right-click and select "Paste"
5. File is moved to new location

### Copying Files
1. Right-click on file to copy
2. Select "Copy" (📋 Copied: filename.txt)
3. Right-click on destination
4. Select "Paste"
5. File is copied (original remains, copy created)

### Quick Duplicate
1. Right-click on file
2. Select "Duplicate"
3. Copy appears immediately with "_copy" suffix

### Renaming Items
1. Right-click on file/folder
2. Select "Rename"
3. Enter new name (without path)
4. Click "Rename"

### Viewing Properties
1. Right-click on file/folder
2. Select "Properties"
3. View size, type, modified date, permissions

## Testing

Comprehensive test suite available in `scripts/test_context_menu.py`:
- Tests all clipboard operations (copy, cut, paste)
- Tests duplicate functionality
- Tests open and refresh operations
- Verifies automatic naming and conflict resolution
- Includes cleanup routines

Run tests:
```bash
python3 scripts/test_context_menu.py
```

## Future Enhancements

Potential additions:
1. **Open With...** - Choose application to open file
2. **Copy Path** - Copy file path to system clipboard
3. **Show in File Manager** - Open system file manager at location
4. **Compress/Extract** - Archive operations for folders
5. **Sort By** - Quick sorting options in context menu
6. **Filter** - Show/hide specific file types
7. **Keyboard Shortcuts** - Ctrl+C, Ctrl+X, Ctrl+V support
8. **Drag & Drop** - Visual drag and drop support
9. **Multi-Select** - Operations on multiple items
10. **Undo/Redo** - Undo recent file operations

## Integration with Editor

The "Open" action is ready for integration with the document management system:
```python
def _on_open_action(self, action, parameter):
    """Handle 'Open' context menu action."""
    if self.selected_item_path and not self.selected_item_is_dir:
        self.set_current_file(self.selected_item_path)
        # TODO: Integrate with document management to open in editor
```

When document management is implemented, this should:
1. Load file content
2. Open in new or existing tab
3. Set tab title to filename
4. Track file association with document
5. Enable auto-save functionality
