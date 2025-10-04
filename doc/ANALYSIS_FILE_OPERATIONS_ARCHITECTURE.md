# File Operations Architecture Analysis

## Date
October 4, 2025

## Current State Analysis

### Components and Responsibilities

```
┌────────────────────────────────────────────────────────────────┐
│                         shypn.py                               │
│                    (Main Application)                          │
│                                                                │
│  Creates and wires:                                            │
│  • ModelCanvasLoader (model_canvas_loader)                     │
│  • NetObjPersistency (persistency)                             │
│  • FileExplorerPanel (file_explorer)                           │
│                                                                │
│  Wiring:                                                       │
│  • file_explorer.set_canvas_loader(model_canvas_loader)        │
│  • file_explorer.set_persistency_manager(persistency)          │
│  • file_explorer.on_file_open_requested = callback            │
└────────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ModelCanvas   │  │NetObj        │  │FileExplorer  │
│Loader        │  │Persistency   │  │Panel         │
└──────────────┘  └──────────────┘  └──────────────┘
         │               │               │
         │               │               │
         └───────────────┴───────────────┘
                         │
                         ▼
              File Operations Flow
```

### Current Issues

#### Issue 1: Duplicate File Loading Logic

**Problem:** File loading logic is duplicated in two places:

1. **shypn.py** - `on_file_open_requested` callback (lines 121-174)
2. **FileExplorerPanel** - `_open_file_from_path` method (lines 1468-1501)
   AND `_load_document_into_canvas` method (lines 1503-1541)

**Impact:**
- Code duplication
- Maintenance burden
- Inconsistent behavior
- Different error handling

**Root Cause:** 
The `on_file_open_requested` callback in `shypn.py` was created before FileExplorerPanel had its own file loading methods.

#### Issue 2: Missing Persistency State Updates

**Problem:** `_load_document_into_canvas` in FileExplorerPanel doesn't update persistency state.

**Missing:**
```python
# Should update persistency manager
persistency.set_filepath(filepath)
persistency.mark_clean()
```

**Impact:**
- Persistency manager doesn't know about loaded file
- File operations (Save) won't work correctly
- Dirty tracking is broken

#### Issue 3: Missing ID Counter Sync

**Problem:** `_load_document_into_canvas` doesn't sync ID counters from DocumentModel to ModelCanvasManager.

**Missing:**
```python
# Should sync ID counters
manager._next_place_id = document._next_place_id
manager._next_transition_id = document._next_transition_id
manager._next_arc_id = document._next_arc_id
```

**Impact:**
- New objects might get duplicate IDs
- Conflicts when editing loaded documents

#### Issue 4: Inconsistent Architecture

**Problem:** shypn.py should not contain business logic - it's just a launcher/wiring file.

**Current (Wrong):**
```python
# shypn.py contains 50+ lines of file loading logic
def on_file_open_requested(filepath):
    # Complex loading logic here...
    document = DocumentModel.load_from_file(filepath)
    # Create tab, load objects, update state...
```

**Should be:**
```python
# shypn.py just wires components
file_explorer.on_file_open_requested = on_file_open_requested

def on_file_open_requested(filepath):
    # Delegate to FileExplorerPanel
    file_explorer._open_file_from_path(filepath)
```

## Recommended Architecture

### Principle: Single Responsibility

```
┌─────────────────────────────────────────────────────────────┐
│                         shypn.py                            │
│                      (Launcher Only)                        │
│                                                             │
│  Responsibilities:                                          │
│  • Create components                                        │
│  • Wire components together                                 │
│  • Set up callbacks (simple delegation)                     │
│  • NO business logic                                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FileExplorerPanel                         │
│                  (File Operations Controller)               │
│                                                             │
│  Responsibilities:                                          │
│  • Handle all file operations                               │
│  • Load files into canvas                                   │
│  • Save files from canvas                                   │
│  • Coordinate canvas_loader and persistency                 │
│  • Update UI state                                          │
│                                                             │
│  Methods:                                                   │
│  • _open_file_from_path(filepath)                           │
│  • _load_document_into_canvas(document, filepath)           │
│  • save_current_document()                                  │
│  • save_current_document_as()                               │
│  • open_document()                                          │
│  • new_document()                                           │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         │ Uses                              │ Uses
         ▼                                    ▼
┌──────────────────┐              ┌──────────────────┐
│ModelCanvasLoader │              │NetObjPersistency │
│                  │              │                  │
│ • add_document() │              │ • set_filepath() │
│ • get_manager()  │              │ • mark_clean()   │
│ • etc.           │              │ • save_document()│
└──────────────────┘              └──────────────────┘
```

### Data Flow: Open File Operation

```
1. User Action
   └─> Double-click on file in TreeView
       OR
   └─> Context menu "Open"

2. FileExplorerPanel._on_row_activated() / _on_context_open_clicked()
   └─> Checks if callback exists: if self.on_file_open_requested:
       └─> YES: Calls callback (delegated to shypn.py)
       └─> NO: Falls back to self._open_file_from_path(filepath)

3. shypn.py.on_file_open_requested(filepath)
   └─> Should just delegate: file_explorer._open_file_from_path(filepath)

4. FileExplorerPanel._open_file_from_path(filepath)
   └─> Loads DocumentModel from file
   └─> Calls _load_document_into_canvas(document, filepath)

5. FileExplorerPanel._load_document_into_canvas(document, filepath)
   └─> Creates new canvas tab (model_canvas_loader.add_document())
   └─> Loads objects into ModelCanvasManager
   └─> Syncs ID counters
   └─> Updates persistency state (set_filepath, mark_clean)
   └─> Triggers redraw (queue_draw)
```

## Required Changes

### Change 1: Simplify shypn.py callback

**Before (53 lines of logic):**
```python
def on_file_open_requested(filepath):
    try:
        print(f"[Main] File open requested: {filepath}")
        from shypn.data.canvas.document_model import DocumentModel
        document = DocumentModel.load_from_file(filepath)
        # ... 40 more lines of logic ...
    except Exception as e:
        # ... error handling ...
```

**After (3 lines - just delegation):**
```python
def on_file_open_requested(filepath):
    # Delegate to FileExplorerPanel which has all the file loading logic
    file_explorer._open_file_from_path(filepath)
```

### Change 2: Complete _load_document_into_canvas

**Add missing pieces:**
```python
def _load_document_into_canvas(self, document, filepath: str):
    # ... existing code ...
    
    if manager:
        # Load objects
        manager.places = list(document.places)
        manager.transitions = list(document.transitions)
        manager.arcs = list(document.arcs)
        
        # MISSING: Sync ID counters
        manager._next_place_id = document._next_place_id
        manager._next_transition_id = document._next_transition_id
        manager._next_arc_id = document._next_arc_id
        
        # MISSING: Update persistency state
        if hasattr(self, 'persistency') and self.persistency:
            self.persistency.set_filepath(filepath)
            self.persistency.mark_clean()
        
        # Trigger redraw
        drawing_area.queue_draw()
```

### Change 3: Remove on_file_open_requested fallback

**Current code has fallback:**
```python
if self.on_file_open_requested:
    self.on_file_open_requested(full_path)
else:
    # Fallback: Load file using document operations
    self._open_file_from_path(full_path)
```

**This is redundant** because:
1. shypn.py ALWAYS sets `on_file_open_requested`
2. The callback should just delegate to `_open_file_from_path` anyway
3. Having two paths creates confusion

**Better approach:**
```python
# Always use _open_file_from_path directly
self._open_file_from_path(full_path)
```

## Benefits of Proposed Architecture

### 1. Single Responsibility
- **shypn.py**: Only wiring, no business logic
- **FileExplorerPanel**: All file operations logic

### 2. No Code Duplication
- File loading logic exists in ONE place
- Easier to maintain and test

### 3. Consistent Behavior
- Same code path for all file opening operations
- Consistent error handling
- Consistent state updates

### 4. Better Testability
- Can test FileExplorerPanel independently
- Don't need full app to test file operations

### 5. Clearer Architecture
- Each component has clear responsibilities
- Easier to understand and modify

## Migration Plan

### Step 1: Fix _load_document_into_canvas (CRITICAL)
- Add ID counter sync
- Add persistency state update
- Add better logging

### Step 2: Simplify shypn.py callback
- Replace complex logic with delegation
- Just call `file_explorer._open_file_from_path(filepath)`

### Step 3: Remove fallback path (OPTIONAL)
- Remove `else: _open_file_from_path()` fallback
- Always use callback (which delegates)
- OR: Remove callback and always call `_open_file_from_path` directly

### Step 4: Test thoroughly
- Double-click on file
- Context menu Open
- Verify objects are loaded
- Verify drawing happens
- Verify Save works after loading

## Conclusion

The current architecture has file loading logic split between shypn.py and FileExplorerPanel. This creates duplication, inconsistency, and maintenance issues.

**The fix is simple:**
1. Move ALL file loading logic to FileExplorerPanel
2. Make shypn.py callback just delegate
3. Ensure persistency state is updated
4. Ensure ID counters are synced

This follows the principle that shypn.py is just a launcher/wiring file, while FileExplorerPanel is the controller for all file operations.
