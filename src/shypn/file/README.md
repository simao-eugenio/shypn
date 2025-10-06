# File Operations and Persistence

This directory handles file operations, document persistence, and file system integration for Petri Net models.

## Core Modules

### `netobj_persistency.py`
**Document Persistence Layer**

Manages saving and loading of Petri Net documents:
- **Save Operations**: Save, Save As, Auto-save
- **Load Operations**: Open file, recent files
- **JSON Serialization**: Convert document to/from JSON
- **File Format Versioning**: Support multiple file format versions
- **Migration**: Upgrade old file formats to current version
- **Validation**: Verify file integrity on load
- **Error Handling**: Handle corrupted or invalid files

**Key Functions:**
```python
save_document(document, filepath)
load_document(filepath) -> DocumentModel
save_as(document, new_filepath)
auto_save(document)
```

**File Format:**
```json
{
  "version": "2.0",
  "metadata": {
    "created": "2025-10-05T10:30:00",
    "modified": "2025-10-05T14:20:00",
    "author": "user",
    "description": "Manufacturing system model"
  },
  "places": [...],
  "transitions": [...],
  "arcs": [...]
}
```

**Persistence Features:**
- **Dirty Flag Management**: Track unsaved changes
- **Modification Timestamps**: Record when document was last modified
- **Backup Creation**: Optional backup before overwrite
- **Atomic Saves**: Ensure file integrity during save
- **File Locking**: Prevent concurrent modifications

**View State Persistence:**
- Saves view state (pan, zoom) to `.shy.view` file alongside document
- Automatically loaded when document reopens
- Format: `{"pan_x": 100, "pan_y": 50, "zoom": 1.5}`
- Ensures user returns to last working position

### `explorer.py`
**File Explorer Integration**

Integrates with the file system and file operations panel:
- **File Browser**: Navigate file system
- **Recent Files**: Track recently opened documents
- **File Operations**: New, Open, Save, Save As, Close
- **Directory Management**: Working directory tracking
- **File Filtering**: Show only `.shy` files
- **Quick Access**: Favorite directories, bookmarks

**Features:**
- **Drag and Drop**: Drag files to open
- **Keyboard Shortcuts**: Ctrl+O (open), Ctrl+S (save)
- **Context Menu**: Right-click file operations
- **Preview**: Show file metadata without opening

## File Operations Flow

### New Document
```python
1. Create new DocumentModel with default name
2. Initialize empty places, transitions, arcs lists
3. Set default view state (zoom=1.0, pan=(0,0))
4. Add new tab to canvas
5. Mark as unsaved (no filepath yet)
```

### Open Document
```python
1. Show file chooser dialog (.shy filter)
2. Load JSON from selected file
3. Deserialize document (places, transitions, arcs)
4. Load view state from .shy.view if exists
5. Restore view position and zoom
6. Add tab with filename
7. Mark as saved (filepath set)
```

### Save Document
```python
1. If no filepath, prompt for Save As
2. Serialize document to JSON
3. Write to file atomically
4. Save view state to .shy.view
5. Update modification timestamp
6. Clear dirty flag
7. Update recent files list
```

### Save As Document
```python
1. Show file chooser dialog with save mode
2. Validate new filepath (.shy extension)
3. Check if file exists (prompt overwrite)
4. Perform save operation to new path
5. Update document filepath
6. Update tab label with new name
```

### Close Document
```python
1. Check dirty flag
2. If unsaved, prompt: Save / Don't Save / Cancel
3. If save chosen, perform save operation
4. Remove tab from canvas
5. Clear document from memory
```

## File Format Versions

### Version 2.0 (Current)
- Full support for all arc types (normal, inhibitor, curved)
- View state in separate .shy.view file
- Token persistence (marking and initial_marking)
- Transition types (immediate, timed, stochastic, continuous)
- Color and styling properties

### Version 1.0 (Legacy)
- Basic places, transitions, arcs
- No curved arcs
- No view state persistence
- Automatic migration to 2.0 on load

### Migration Strategy
```python
if file_version == "1.0":
    migrate_to_2_0(document)
    # Add default values for new properties
    # Convert old arc format to new format
    # Set default view state
```

## Error Handling

### File Not Found
```python
try:
    document = load_document(filepath)
except FileNotFoundError:
    show_error("File not found: {filepath}")
    remove_from_recent_files(filepath)
```

### Corrupted File
```python
try:
    document = load_document(filepath)
except JSONDecodeError:
    show_error("File is corrupted or invalid")
    offer_recover_backup()
```

### Permission Denied
```python
try:
    save_document(document, filepath)
except PermissionError:
    show_error("Cannot save: Permission denied")
    offer_save_as_different_location()
```

## Recent Files Management

**Storage:**
- Stored in user config: `~/.config/shypn/recent_files.json`
- Maximum 10 recent files
- Includes filepath and last opened timestamp

**Operations:**
- Add to recent on successful open
- Remove from recent if file no longer exists
- Clear recent files list
- Pin favorite files

## Integration with UI

### File Operations Panel (Left Panel)
- New document button
- Open file button
- Save button (enabled when dirty)
- Save As button
- Recent files list
- File explorer tree view

### Menu Bar
- File menu with all operations
- Keyboard shortcuts
- Recent files submenu

### Tab Context Menu
- Save Tab
- Save Tab As
- Close Tab
- Close Other Tabs
- Close All Tabs

## Auto-save Feature

**Configuration:**
- Interval: 5 minutes (configurable)
- Location: Temporary directory
- Recovery: On crash, offer to recover
- Format: Same as regular save

**Auto-save Flow:**
```python
every 5 minutes:
    for each open document:
        if document.is_dirty:
            auto_save(document, temp_location)
            store_recovery_info()
```

## Import Patterns

```python
from shypn.file.netobj_persistency import (
    save_document,
    load_document,
    save_as,
    PersistencyManager
)
from shypn.file.explorer import FileExplorer
```

## File System Structure

```
~/Documents/petri_nets/
├── model1.shy           # Main document file
├── model1.shy.view      # View state (auto-generated)
├── model2.shy
├── model2.shy.view
└── backup/
    ├── model1.shy.bak
    └── model2.shy.bak
```

## Configuration

**Preferences:**
- Auto-save enabled/disabled
- Auto-save interval
- Backup location
- Default save directory
- Recent files count
- File format version (save format)

## Performance Considerations

- **Lazy Loading**: Load file only when tab activated
- **Streaming Save**: Write large files incrementally
- **Background Save**: Auto-save in background thread
- **Compression**: Optional gzip compression for large models
- **Incremental Save**: Save only changed objects (future)

## Security Considerations

- **File Validation**: Verify JSON structure before parsing
- **Path Sanitization**: Prevent directory traversal attacks
- **Safe Deserialization**: Validate object types and values
- **Backup Integrity**: Verify backups are valid
