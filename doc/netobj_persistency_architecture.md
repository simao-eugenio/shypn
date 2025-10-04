# NetObjPersistency Architecture - Refactoring Summary

## Overview
Refactored file operations from `ModelCanvasLoader` into dedicated `NetObjPersistency` class following OOP principles and Single Responsibility Principle.

## Date
October 4, 2025

## Problem Statement

**Before refactoring:**
- `ModelCanvasLoader` had mixed responsibilities:
  - UI loading and canvas management (correct)
  - File save/load operations (incorrect - not its responsibility)
  - Dirty state tracking (incorrect - should be with file operations)
- Violation of Single Responsibility Principle
- Loader class doing too much
- Dirty logic scattered across components

**OOP Design Question:**
> "Who should have the ability to do file operations? Loader is a loader, not a file ops specialist."

## Solution: NetObjPersistency Class

Created dedicated `shypn/file/netobj_persistency.py` class that:
- Specializes in file operations
- Manages dirty state tracking
- Cooperates with FileExplorer for file system operations
- Cooperates with DocumentModel for document serialization
- Provides file chooser dialogs
- Handles unsaved changes confirmation

## Architecture Changes

### New Component: NetObjPersistency

**Location:** `src/shypn/file/netobj_persistency.py`

**Responsibilities:**
1. **File Operations:**
   - `save_document(document, save_as=False)` - Save to file
   - `load_document()` - Load from file
   - Returns: `(document, filepath)` tuple

2. **Dirty State Management:**
   - `mark_dirty()` - Mark document as having unsaved changes
   - `mark_clean()` - Mark document as clean
   - `is_dirty` - Property to check dirty state
   - Callbacks: `on_dirty_changed(is_dirty)`

3. **Filepath Management:**
   - `set_filepath(filepath)` - Set current file path
   - `has_filepath()` - Check if document has been saved
   - `get_display_name()` - Get filename for display
   - `get_title()` - Get title with dirty indicator (e.g., "*Untitled")

4. **User Interaction:**
   - `check_unsaved_changes()` - Prompt user before discarding changes
   - `new_document()` - Handle new document creation with unsaved check
   - File chooser dialogs for save/open
   - Success/error message dialogs

5. **Callbacks:**
   - `on_file_saved(filepath)` - Called after successful save
   - `on_file_loaded(filepath, document)` - Called after successful load
   - `on_dirty_changed(is_dirty)` - Called when dirty state changes

**Key Features:**
- Auto-adds `.json` extension on save
- Remembers last used directory
- Overwrite confirmation on save
- File filters (.json files)
- Comprehensive error handling
- Console logging for debugging

### Modified Component: ModelCanvasLoader

**Location:** `src/shypn/helpers/model_canvas_loader.py`

**Removed Methods:**
- ❌ `save_current_document(save_as=False)` - Moved to NetObjPersistency
- ❌ `load_document()` - Moved to NetObjPersistency
- ❌ File Operations section (~200 lines removed)

**Retained Responsibilities:**
- ✅ UI loading (`load()`)
- ✅ Document tab management (`add_document()`)
- ✅ Canvas manager access (`get_canvas_manager()`)
- ✅ Drawing operations (`_on_draw()`)
- ✅ Event handling (`_on_button_press()`, etc.)
- ✅ Context menus (`_show_canvas_context_menu()`)
- ✅ Zoom palette management
- ✅ Edit/Simulate palette management

### Modified Component: Main Application

**Location:** `src/shypn.py`

**Changes:**

1. **Import NetObjPersistency:**
```python
from shypn.file import create_persistency_manager
```

2. **Create persistency manager instance:**
```python
persistency = create_persistency_manager(parent_window=window)
```

3. **Wire file buttons to persistency methods:**

**New Document Button:**
```python
def on_new_document(button):
    """Create a new document tab."""
    # Check for unsaved changes
    if not persistency.check_unsaved_changes():
        return
    
    # Create new document
    if persistency.new_document():
        model_canvas_loader.add_document()
```

**Save Button:**
```python
def on_save_document(button):
    """Save current document to file."""
    drawing_area = model_canvas_loader.get_current_document()
    manager = model_canvas_loader.get_canvas_manager(drawing_area)
    
    # Save using persistency manager
    persistency.save_document(manager.document, save_as=False)
```

**Open Button:**
```python
def on_open_document(button):
    """Open document from file."""
    # Load using persistency manager
    document, filepath = persistency.load_document()
    
    if document and filepath:
        # Create new tab and inject document
        page_index, drawing_area = model_canvas_loader.add_document(...)
        manager = model_canvas_loader.get_canvas_manager(drawing_area)
        manager.document = document
        # Rebuild object lists and redraw
```

**Save As Button:**
```python
def on_save_as_document(button):
    """Save current document to new file."""
    drawing_area = model_canvas_loader.get_current_document()
    manager = model_canvas_loader.get_canvas_manager(drawing_area)
    
    # Save using persistency manager (save_as=True)
    persistency.save_document(manager.document, save_as=True)
```

## Component Responsibilities

### NetObjPersistency
**Role:** File Operations Specialist
- File I/O (save/load)
- Dirty state tracking
- Filepath management
- User dialogs (file chooser, confirmations)
- Error handling
- Cooperates with DocumentModel

### ModelCanvasLoader
**Role:** UI Loader and Canvas Manager
- Load canvas UI
- Manage document tabs
- Handle drawing/rendering
- Process user events
- Manage palettes
- Provide canvas access

### Main Application (shypn.py)
**Role:** Orchestrator
- Create components (loader, persistency)
- Wire buttons to actions
- Coordinate between components
- Pass data between layers

### DocumentModel
**Role:** Data Layer
- Serialize to dict/JSON
- Deserialize from dict/JSON
- Manage netobjs (places, transitions, arcs)
- File format handling

## Benefits

### 1. Single Responsibility Principle ✅
Each class has one clear responsibility:
- NetObjPersistency → File operations
- ModelCanvasLoader → UI/Canvas management
- DocumentModel → Data serialization
- Main app → Coordination

### 2. Separation of Concerns ✅
Clear boundaries between:
- File operations (NetObjPersistency)
- UI operations (ModelCanvasLoader)
- Data operations (DocumentModel)
- Application logic (shypn.py)

### 3. Better Maintainability ✅
- File operations centralized in one place
- Easier to modify save/load behavior
- No need to touch loader for file changes
- Clear code organization

### 4. Proper Dirty State Management ✅
- Dirty state managed by file specialist
- Callbacks for observers (future: window title updates)
- Unsaved changes confirmation
- New document with safety checks

### 5. Easier Testing ✅
- NetObjPersistency can be tested independently
- Mock file dialogs for testing
- No need for full UI setup
- Clear interfaces for testing

### 6. Better Error Handling ✅
- Centralized error handling for file ops
- Consistent error dialogs
- Console logging for debugging
- Graceful degradation

### 7. Future Extensibility ✅
- Easy to add "Recent Files" menu
- Easy to add auto-save functionality
- Easy to add backup/recovery
- Easy to add file format versioning

## File Organization

```
src/shypn/
├── file/
│   ├── __init__.py                    # Exports NetObjPersistency
│   ├── explorer.py                    # File system navigation
│   └── netobj_persistency.py         # File operations (NEW)
├── helpers/
│   ├── model_canvas_loader.py        # UI/Canvas (CLEANED UP)
│   ├── left_panel_loader.py
│   └── right_panel_loader.py
├── data/
│   └── canvas/
│       └── document_model.py         # Data serialization
└── shypn.py                          # Main app (UPDATED)
```

## Testing

### Architecture Tests
**File:** `tests/test_architecture_no_gtk.py`

Tests verify:
- ✅ NetObjPersistency class exists with all methods
- ✅ __init__.py properly exports
- ✅ ModelCanvasLoader cleaned up (no file ops)
- ✅ Main app uses NetObjPersistency
- ✅ Responsibilities properly separated

**Result:** All 5 tests pass! 🎉

### Integration Tests
**File:** `tests/test_file_integration_simple.py`

Tests verify:
- ✅ Document save/load works
- ✅ All properties preserved
- ✅ JSON format valid

**Result:** All tests pass! 🎉

## Usage Example

```python
# Create persistency manager
persistency = create_persistency_manager(parent_window=window)

# Setup callbacks
def on_dirty_changed(is_dirty):
    # Update window title with * indicator
    title = persistency.get_title()
    window.set_title(f"{title} - ShyPN")

persistency.on_dirty_changed = on_dirty_changed

# Save document
document = manager.document
success = persistency.save_document(document, save_as=False)

# Load document
document, filepath = persistency.load_document()
if document:
    # Inject into canvas
    manager.document = document
    manager.places = list(document.places)
    manager.transitions = list(document.transitions)
    manager.arcs = list(document.arcs)

# Check for unsaved changes
if persistency.check_unsaved_changes():
    # Safe to proceed
    pass

# Mark document as modified
persistency.mark_dirty()

# Check dirty state
if persistency.is_dirty:
    print("Document has unsaved changes")
```

## Migration Notes

### Before (Old Architecture)
```python
# In ModelCanvasLoader
def save_current_document(self, save_as=False):
    # 150 lines of file operations
    pass

def load_document(self):
    # 100 lines of file operations
    pass

# In shypn.py
model_canvas_loader.save_current_document()
model_canvas_loader.load_document()
```

### After (New Architecture)
```python
# In NetObjPersistency
def save_document(self, document, save_as=False):
    # Clean, focused implementation
    pass

def load_document(self):
    # Clean, focused implementation
    return document, filepath

# In shypn.py
persistency.save_document(manager.document)
document, filepath = persistency.load_document()
```

## Future Enhancements

With this architecture, we can easily add:

1. **Auto-save:** Timer-based auto-save in NetObjPersistency
2. **Recent Files:** Track recent files in persistency manager
3. **Backup:** Auto-backup before save in NetObjPersistency
4. **File Format Versioning:** Handle different JSON versions
5. **Export/Import:** Additional formats (PNML, XML, etc.)
6. **Cloud Storage:** Upload/download from cloud services
7. **Version Control:** Git integration for models
8. **Collaborative Editing:** Real-time collaboration features

All additions would go in NetObjPersistency, keeping loader clean!

## Conclusion

The refactoring successfully separates file operations into a dedicated `NetObjPersistency` class following OOP best practices. The architecture is now cleaner, more maintainable, and better follows SOLID principles.

**Key Achievement:** Loader is now truly a loader - it loads UI and manages canvas. File operations are handled by a specialist class designed for that purpose.

✅ Architecture refactored successfully!
✅ All tests passing!
✅ Better code organization!
✅ Ready for future enhancements!
