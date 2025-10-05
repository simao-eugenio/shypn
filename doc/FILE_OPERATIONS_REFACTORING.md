# File Operations Refactoring - Proper Architecture

**Date:** October 4, 2025  
**Refactoring:** Move file operations from shypn.py to FileExplorerPanel  
**Status:** ✅ Complete

---

## Problem Statement

File operation logic (New, Open, Save, Save As) was incorrectly placed in `shypn.py` (the main application entry point). This violated separation of concerns:

❌ **Before:**
- `shypn.py` directly connected toolbar buttons
- `shypn.py` contained file operation logic
- `shypn.py` accessed canvas managers directly
- File operations scattered across multiple locations

✅ **After:**
- `FileExplorerPanel` owns file operation logic
- `ModelCanvasManager` properly receives filename on creation
- Clean cooperation between FileExplorer, CanvasManager, and Persistency
- `shypn.py` only wires components together

---

## Architecture Changes

### Component Responsibilities

**ModelCanvasManager (Data Layer)**
```python
class ModelCanvasManager:
    def __init__(self, canvas_width, canvas_height, filename="default"):
        self.filename = filename  # ✅ Now properly initialized
    
    def is_default_filename(self) -> bool:
        """Flag indicating document is in unsaved state."""
        return self.filename == "default"
```
- Owns document filename
- Provides `is_default_filename()` flag
- Manages document state (places, transitions, arcs)

**ModelCanvasLoader (UI Controller)**
```python
class ModelCanvasLoader:
    def add_document(self, title=None, filename=None):
        """Add new document tab with specified filename."""
        # Pass filename to manager setup
        self._setup_canvas_manager(drawing, filename=filename)
    
    def _setup_canvas_manager(self, drawing_area, ..., filename=None):
        """Create manager with proper filename."""
        if filename is None:
            filename = "default"
        manager = ModelCanvasManager(..., filename=filename)  # ✅ Proper initialization
```
- Creates document tabs
- Initializes ModelCanvasManager with correct filename
- Manages drawing areas and canvas managers

**FileExplorerPanel (UI Controller + File Operations)**
```python
class FileExplorerPanel:
    def set_canvas_loader(self, canvas_loader):
        """Wire to canvas loader for document operations."""
        self.canvas_loader = canvas_loader
    
    def save_current_document(self):
        """Save using manager's is_default_filename() flag."""
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        self.persistency.save_document(
            manager.document,
            save_as=False,
            is_default_filename=manager.is_default_filename()  # ✅ Flag propagation
        )
    
    def open_document(self):
        """Load file and create tab with correct filename."""
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        # Manager gets initialized with base_name, not "default" ✅
```
- Owns file operation logic (New, Open, Save, Save As)
- Cooperates with ModelCanvasLoader for document access
- Cooperates with NetObjPersistency for file I/O
- Properly uses `is_default_filename()` flag

**shypn.py (Main Application)**
```python
# Wire components together (NO file operation logic)
file_explorer.set_persistency_manager(persistency)
file_explorer.set_canvas_loader(model_canvas_loader)
# Buttons are connected inside FileExplorerPanel ✅
```
- Only wires components together
- No file operation logic
- Clean separation of concerns

---

## Code Changes

### 1. ModelCanvasLoader - Pass Filename to Manager

**File:** `src/shypn/helpers/model_canvas_loader.py`

**add_document() method:**
```python
def add_document(self, title=None, filename=None):
    """Add a new document (tab) to the canvas."""
    # ... create UI widgets ...
    
    # Setup canvas manager for the new drawing area with filename
    self._setup_canvas_manager(drawing, filename=filename)  # ✅ Pass filename
    
    return page_index, drawing
```

**_setup_canvas_manager() method:**
```python
def _setup_canvas_manager(self, drawing_area, overlay_box=None, 
                         overlay_widget=None, filename=None):  # ✅ Accept filename
    """Setup canvas manager and wire up callbacks for a drawing area."""
    
    # Create canvas manager with the specified filename
    if filename is None:
        filename = "default"
    manager = ModelCanvasManager(
        canvas_width=2000, 
        canvas_height=2000, 
        filename=filename  # ✅ Pass to constructor
    )
    self.canvas_managers[drawing_area] = manager
    # ... rest of setup ...
```

### 2. FileExplorerPanel - Add File Operation Methods

**File:** `src/shypn/ui/panels/file_explorer_panel.py`

**Wiring method:**
```python
def set_canvas_loader(self, canvas_loader):
    """Wire file explorer to canvas loader for document operations integration."""
    self.canvas_loader = canvas_loader
```

**File operation methods:**
```python
def save_current_document(self):
    """Save the current document using the persistency manager.
    
    This method properly checks the ModelCanvasManager's is_default_filename()
    flag to determine if a file chooser should be shown.
    """
    drawing_area = self.canvas_loader.get_current_document()
    manager = self.canvas_loader.get_canvas_manager(drawing_area)
    
    # Use is_default_filename() flag ✅
    self.persistency.save_document(
        manager.document,
        save_as=False,
        is_default_filename=manager.is_default_filename()
    )

def open_document(self):
    """Open a document from file using the persistency manager."""
    document, filepath = self.persistency.load_document()
    
    if document and filepath:
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        
        # Add document with correct filename ✅
        page_index, drawing_area = self.canvas_loader.add_document(filename=base_name)
        
        manager = self.canvas_loader.get_canvas_manager(drawing_area)
        manager.document = document
        # ... rebuild object lists ...

def save_current_document_as(self):
    """Save As operation - always shows file chooser."""
    # ... similar logic with save_as=True ...

def new_document(self):
    """Create new document - uses "default" filename."""
    if self.persistency.check_unsaved_changes():
        if self.persistency.new_document():
            self.canvas_loader.add_document()  # Uses "default"
```

**Button connections:**
```python
def _connect_signals(self):
    """Connect widget signals to controller methods."""
    # File operations now handled by FileExplorerPanel itself ✅
    if self.new_button:
        self.new_button.connect("clicked", lambda btn: self.new_document())
    if self.open_button:
        self.open_button.connect("clicked", lambda btn: self.open_document())
    if self.save_button:
        self.save_button.connect("clicked", lambda btn: self.save_current_document())
    if self.save_as_button:
        self.save_as_button.connect("clicked", lambda btn: self.save_current_document_as())
    # ... rest of signals ...
```

### 3. shypn.py - Wire Components Only

**File:** `src/shypn.py`

**Before (100+ lines of file operation logic):**
```python
# ❌ BAD: File operation logic in main app
new_doc_button = left_panel_loader.builder.get_object('file_new_button')
if new_doc_button:
    def on_new_document(button):
        if not persistency.check_unsaved_changes():
            return
        if persistency.new_document():
            model_canvas_loader.add_document()
    new_doc_button.connect('clicked', on_new_document)

# ... 100+ more lines of similar code ...
```

**After (clean wiring only):**
```python
# ✅ GOOD: Only wire components together
file_explorer = left_panel_loader.file_explorer

if file_explorer:
    # Wire persistency manager to file explorer
    file_explorer.set_persistency_manager(persistency)
    
    # Wire canvas loader to file explorer
    file_explorer.set_canvas_loader(model_canvas_loader)
    
    print("[Main] File operations now handled by FileExplorerPanel")
    
    # Only keep double-click handler for file explorer tree
    file_explorer.on_file_open_requested = on_file_open_requested
```

---

## Data Flow

### Save Operation Flow

```
1. User clicks Save button in FileExplorerPanel toolbar
   ↓
2. FileExplorerPanel.save_current_document()
   ├─ Gets current drawing_area from canvas_loader
   └─ Gets manager from canvas_loader
   ↓
3. Check manager.is_default_filename()
   ├─ True (filename="default") → needs_prompt = True
   └─ False (filename="mymodel") → needs_prompt = False
   ↓
4. persistency.save_document(document, save_as=False, is_default_filename=flag)
   ├─ needs_prompt = True → Show file chooser
   └─ needs_prompt = False → Save directly
```

### Open Operation Flow

```
1. User clicks Open button in FileExplorerPanel toolbar
   ↓
2. FileExplorerPanel.open_document()
   └─ Calls persistency.load_document()
   ↓
3. File chooser shown, user selects "mymodel.shy"
   ↓
4. Extract base_name = "mymodel" (without .shy extension)
   ↓
5. canvas_loader.add_document(filename="mymodel")
   ├─ Passes filename to _setup_canvas_manager()
   └─ ModelCanvasManager(filename="mymodel")  ✅
   ↓
6. manager.is_default_filename() returns False  ✅
   ↓
7. Next save will work directly (no file chooser)
```

### New Document Flow

```
1. User clicks New button in FileExplorerPanel toolbar
   ↓
2. FileExplorerPanel.new_document()
   ├─ Checks for unsaved changes
   └─ Calls persistency.new_document()
   ↓
3. canvas_loader.add_document()  (no filename parameter)
   ├─ filename defaults to "default"
   └─ ModelCanvasManager(filename="default")  ✅
   ↓
4. manager.is_default_filename() returns True  ✅
   ↓
5. Next save will show file chooser
```

---

## Benefits

### 1. Proper Separation of Concerns
- `shypn.py` is no longer a "workhorse" - it's a clean entry point
- `FileExplorerPanel` owns file operations (makes sense - it has the file toolbar)
- `ModelCanvasManager` owns document state (makes sense - it's the data layer)

### 2. Correct Flag Propagation
- Filename is set when manager is created
- `is_default_filename()` returns correct value immediately
- Save operations work correctly after loading files

### 3. Better Testability
- File operations can be tested independently in FileExplorerPanel
- No need to test through shypn.py
- MockCanvas Loader and MockPersistency can be injected

### 4. Maintainability
- File operation logic is in one place (FileExplorerPanel)
- Easy to find and modify
- Clear cooperation pattern between components

### 5. Reusability
- FileExplorerPanel can be reused in other applications
- Clean interfaces (set_canvas_loader, set_persistency_manager)
- No tight coupling to shypn.py

---

## Testing

### Manual Testing Completed

✅ **New Document:**
- Click New button → Creates tab with "default" filename
- manager.is_default_filename() → True
- Click Save → File chooser opens

✅ **Open Document:**
- Click Open button → File chooser opens
- Select "mymodel.shy" → Tab created with "mymodel" filename
- manager.is_default_filename() → False
- Click Save → Saves directly (no dialog)

✅ **Save Default:**
- New document with "default" filename
- Click Save → File chooser opens with "default.shy" pre-filled
- Enter "newmodel" → Saves as "newmodel.shy"
- manager.is_default_filename() → False (filename changed)

✅ **Save Normal:**
- Open "test.shy" → filename = "test"
- Modify objects
- Click Save → Saves directly to "test.shy"

✅ **Save As:**
- Any document state
- Click Save As → File chooser always opens
- Can save with new name

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                       shypn.py                          │
│                   (Main Application)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  // Wire components together (NO logic)          │  │
│  │  file_explorer.set_persistency_manager(persist)  │  │
│  │  file_explorer.set_canvas_loader(canvas_loader)  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────┬─────────────────┘
             │                          │
             ▼                          ▼
┌────────────────────────┐  ┌─────────────────────────────┐
│  FileExplorerPanel     │  │   ModelCanvasLoader         │
│  (UI + File Ops)       │  │   (UI Controller)           │
│ ┌──────────────────┐   │  │ ┌───────────────────────┐   │
│ │ save_document()  │───┼──┼▶│ get_canvas_manager()  │   │
│ │ open_document()  │   │  │ │ add_document(filename)│   │
│ │ new_document()   │   │  │ └───────────────────────┘   │
│ └──────────────────┘   │  └─────────────┬───────────────┘
│          │             │                │
│          │ Uses        │                │ Creates
│          ▼             │                ▼
│ ┌──────────────────┐   │  ┌─────────────────────────────┐
│ │ NetObjPersistency│   │  │   ModelCanvasManager        │
│ │ save_document(   │   │  │   (Data Layer)              │
│ │   is_default_    │   │  │ ┌───────────────────────┐   │
│ │   filename)      │   │  │ │ filename: str          │   │
│ └──────────────────┘   │  │ │ is_default_filename()  │   │
└────────────────────────┘  │ └───────────────────────┘   │
                            └─────────────────────────────┘
```

---

## Files Modified

1. **src/shypn/helpers/model_canvas_loader.py**
   - `add_document()`: Pass filename to `_setup_canvas_manager()`
   - `_setup_canvas_manager()`: Accept filename, pass to ModelCanvasManager constructor
   - ~10 lines changed

2. **src/shypn/ui/panels/file_explorer_panel.py**
   - `set_canvas_loader()`: New method to wire canvas loader
   - `save_current_document()`: New method with is_default_filename() flag
   - `open_document()`: New method with proper filename handling
   - `save_current_document_as()`: New method for Save As
   - `new_document()`: New method for New document
   - `_connect_signals()`: Wire toolbar buttons to new methods
   - ~150 lines added

3. **src/shypn.py**
   - Removed ~100 lines of file operation logic
   - Added 2 lines to wire canvas_loader to file_explorer
   - Much cleaner and shorter

**Total:** ~+60 net lines (cleaner architecture)

---

## Related Documentation

- `DEFAULT_FILENAME_FLAG_PATTERN.md` - Flag pattern implementation
- `DEFAULT_FILENAME_NORMALIZATION.md` - Default filename behavior
- `SAVE_OPERATION_FLOW.md` - Save operation documentation

---

**Status:** ✅ **Refactoring complete - proper architecture established**

File operations now properly reside in `FileExplorerPanel`, cooperating cleanly with `ModelCanvasManager` for flag checking and `NetObjPersistency` for file I/O.
