# Context Menu File Operations

## Overview

The TreeView context menu (right-click menu) in the File Explorer Panel has been enhanced with comprehensive file operations organized into logical groups.

## Menu Structure

The context menu is organized into 4 functional groups:

### Group 1: File Operations
- **Open** - Opens selected .shy file in canvas
- **New File** - Creates new .shy file with inline editing
- **New Folder** - Creates new folder with inline editing
- **Save** - Saves current document
- **Save As...** - Saves current document with new name

### Group 2: File Modifications
- **Rename** - Renames selected file/folder
- **Delete** - Deletes selected file/folder
- **Duplicate** - Creates a copy of selected file/folder

### Group 3: Editing Operations
- **Cut** - Cuts selected file/folder to clipboard
- **Copy** - Copies selected file/folder to clipboard
- **Paste** - Pastes from clipboard to current location

### Group 4: View Operations
- **Refresh** - Reloads directory contents
- **Properties** - Shows file/folder properties

## Inline Editing Feature

### New File/Folder Creation

When you select **New File** or **New Folder** from the context menu:

1. A new editable row appears in the tree at the appropriate location:
   - If a folder is selected: inside that folder
   - If a file is selected: in the same directory
   - If empty space is clicked: in current directory

2. The row has an editable text field where you type the name

3. Keyboard behavior:
   - **Enter** - Confirms and creates the file/folder
   - **Escape** - Cancels and removes the temporary row

4. Automatic handling:
   - New files automatically get `.shy` extension if not provided
   - Duplicate names are prevented
   - Invalid names show error messages

### Example Workflow

**Creating a new Petri net file:**
```
1. Right-click in the tree view
2. Select "New File"
3. An editable row appears with "new_file.shy"
4. Type your desired name (e.g., "my_model")
5. Press Enter
6. File "my_model.shy" is created with minimal JSON structure
```

**Creating a new folder:**
```
1. Right-click in the tree view
2. Select "New Folder"
3. An editable row appears with "New Folder"
4. Type your desired folder name
5. Press Enter
6. Folder is created in the file system
```

## Integration with Existing Code

### File Operations Flow

The context menu items are connected to the existing file operation methods:

```
Context Menu Item          →  Handler Method                 →  Integration
─────────────────────────────────────────────────────────────────────────────
Open                       →  _on_context_open_clicked       →  open_document()
New File                   →  _on_context_new_file_clicked   →  Inline edit + DocumentModel
New Folder                 →  _on_context_new_folder_clicked →  Inline edit + os.makedirs()
Save                       →  _on_context_save_clicked       →  save_current_document()
Save As...                 →  _on_context_save_as_clicked    →  save_current_document_as()
```

### Architecture Integration

```
User Action (Right-click)
    ↓
FileExplorerPanel
    ├─ Context Menu Display
    ├─ Item Selection
    └─ Handler Invocation
        ↓
Inline Editing (for New File/Folder)
    ├─ Temporary TreeStore row
    ├─ Editable CellRendererText
    └─ User input
        ↓
File System Operation
    ├─ DocumentModel.save_to_file() (for .shy files)
    ├─ os.makedirs() (for folders)
    └─ Validation
        ↓
Canvas Integration (for file operations)
    ├─ ModelCanvasLoader
    ├─ NetObjPersistency
    └─ ModelCanvasManager
```

## Technical Implementation

### TreeView Configuration

```python
# Text renderer is made editable only when needed
text_renderer = Gtk.CellRendererText()
text_renderer.set_property("editable", False)  # Default: not editable
text_renderer.connect("edited", self._on_cell_edited)
text_renderer.connect("editing-canceled", self._on_cell_editing_canceled)
```

### Inline Edit State Management

```python
# When starting inline edit, store context:
self.editing_iter = new_iter           # TreeIter being edited
self.editing_parent_dir = parent_dir   # Where to create file/folder
self.editing_is_folder = False/True    # Type of item being created

# Make renderer editable temporarily
self.text_renderer.set_property("editable", True)

# Trigger edit mode
self.tree_view.set_cursor(tree_path, column, True)
```

### File Creation with DocumentModel

When creating a new .shy file through inline editing:

```python
def _on_cell_edited(self, renderer, path, new_text):
    # ... validation ...
    
    if not self.editing_is_folder:
        # Create empty .shy file with minimal JSON structure
        from shypn.data.canvas.document_model import DocumentModel
        doc = DocumentModel()
        doc.save_to_file(full_path)
```

This creates a proper JSON file that can be opened in the canvas:

```json
{
  "places": [],
  "transitions": [],
  "arcs": []
}
```

## Context-Aware Behavior

### Right-Click on File
- **Open** - Opens the file (if .shy)
- **Rename/Delete/Duplicate** - Acts on that file
- **New File/Folder** - Creates in same directory

### Right-Click on Folder
- **Open** - Navigates into folder
- **Rename/Delete/Duplicate** - Acts on that folder
- **New File/Folder** - Creates inside that folder

### Right-Click on Empty Space
- **New File/Folder** - Creates in current directory
- Other operations disabled or act on current directory

## Error Handling

The context menu operations include comprehensive error handling:

1. **Duplicate Names**: "'{name}' already exists"
2. **Invalid File Types**: "Can only open .shy Petri net files"
3. **Empty Names**: Silently cancels and removes temporary row
4. **File System Errors**: Shows error message via `explorer.on_error()`

## User Experience Improvements

### Visual Feedback
- Menu items show clear action names
- Separators organize items into logical groups
- Icons show file/folder type during inline editing
- Cursor automatically positioned in editable field

### Keyboard Shortcuts (future enhancement)
The menu structure supports adding keyboard shortcuts:
- Ctrl+N - New File
- Ctrl+Shift+N - New Folder
- Ctrl+S - Save
- Ctrl+Shift+S - Save As
- F2 - Rename
- Delete - Delete

## Testing Checklist

- [ ] Right-click on file shows all menu items
- [ ] Right-click on folder shows all menu items
- [ ] Right-click on empty space shows creation items
- [ ] New File creates .shy file with inline editing
- [ ] New Folder creates folder with inline editing
- [ ] Escape cancels inline editing
- [ ] Enter confirms inline editing
- [ ] Duplicate names are prevented
- [ ] Invalid names show errors
- [ ] Open loads file in canvas
- [ ] Save saves current document
- [ ] Save As prompts for new name
- [ ] Cut/Copy/Paste work correctly
- [ ] Rename updates file name
- [ ] Delete removes file/folder
- [ ] Refresh updates tree view

## Future Enhancements

1. **Drag and Drop**: Drag files/folders to move them
2. **Multi-Select**: Select multiple items for batch operations
3. **Undo/Redo**: Undo file operations
4. **Templates**: Create new files from templates
5. **Properties Dialog**: Enhanced file properties with metadata
6. **Search**: Quick search/filter in tree view
