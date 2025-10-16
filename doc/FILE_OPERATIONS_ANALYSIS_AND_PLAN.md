# File Operations Analysis and Fix Plan

**Date**: 2025-10-15  
**Scope**: Comprehensive review of file operations (save, save-as, new, open, delete, rename, etc.)  
**Goal**: Identify all issues and create systematic fix plan

---

## Executive Summary

The file operations system has **multiple architectural issues** causing broken or inconsistent behavior across:
- Save/Save-As operations
- File tree context menu operations  
- Document lifecycle management
- Dirty state tracking across multiple tabs
- Integration between components (FileExplorerPanel ↔ NetObjPersistency ↔ ModelCanvasLoader)

**Critical Finding**: The system has a **single persistency manager** tracking state for **multiple document tabs**, causing state confusion and incorrect behavior.

---

## Architecture Overview

### Components

1. **NetObjPersistency** (`src/shypn/file/netobj_persistency.py`)
   - Responsibilities: File I/O, dirty state tracking, file dialogs
   - Current Design: **SINGLETON** instance managing ONE filepath and ONE dirty state
   - Problem: ❌ Cannot track multiple open documents correctly

2. **FileExplorerPanel** (`src/shypn/helpers/file_explorer_panel.py`)
   - Responsibilities: File browser UI, tree view, context menu
   - Methods: `save_current_document()`, `save_current_document_as()`, `open_document()`, `new_document()`
   - Problem: ❌ Calls persistency methods that don't know which tab is active

3. **ModelCanvasLoader** (`src/shypn/helpers/model_canvas_loader.py`)
   - Responsibilities: Multi-document tab management, canvas lifecycle
   - Has: Multiple tabs, each with separate ModelCanvasManager
   - Problem: ❌ No per-document persistency state tracking

4. **ModelCanvasManager** (`src/shypn/data/model_canvas_manager.py`)
   - Responsibilities: Single document's canvas state, objects, viewport
   - Has: `filename`, `is_default_filename()`, `is_modified()` flag
   - Problem: ⚠️ Has partial state but not fully integrated with persistency

### Current Data Flow (BROKEN)

```
User clicks Save
    ↓
FileExplorerPanel.save_current_document()
    ↓
Gets current drawing_area from canvas_loader
    ↓
Gets ModelCanvasManager from drawing_area
    ↓
Converts manager to DocumentModel
    ↓
Calls persistency.save_document(document, save_as=False, is_default_filename=manager.is_default_filename())
    ↓
NetObjPersistency saves to self.current_filepath
    ↓
❌ PROBLEM: If user switches tabs before saving, wrong document gets saved
❌ PROBLEM: Other tabs' dirty states don't update correctly
❌ PROBLEM: File tree doesn't refresh after save
```

---

## Issues Catalog

### 🔴 Critical Issues (Broken Functionality)

#### Issue 1: Single Persistency Manager for Multiple Documents
**Severity**: Critical  
**Impact**: Data loss, incorrect saves

**Problem**:
- Application has ONE `NetObjPersistency` instance
- This instance tracks ONE `current_filepath` and ONE `is_dirty` flag
- But application supports MULTIPLE open documents (tabs)
- When user switches tabs, persistency state doesn't update

**Example Failure Scenario**:
1. User opens `model_a.shy` in tab 1
2. User creates new document in tab 2 (filename="default")
3. User modifies objects in tab 2
4. User switches to tab 1
5. User clicks Save → **SAVES TAB 1 TO TAB 2's "DEFAULT" PATH**
6. Result: ❌ Data loss, confusion, wrong file overwritten

**Root Cause**: Architectural - persistency should be per-document, not global

---

#### Issue 2: Dirty State Confusion
**Severity**: Critical  
**Impact**: Users lose work, incorrect save prompts

**Problem**:
- `NetObjPersistency.is_dirty` is a single boolean
- Multiple documents can be dirty simultaneously
- Switching tabs doesn't update `is_dirty` to match new tab's state
- Tab asterisks (*) show incorrect state

**Example Failure Scenario**:
1. User modifies tab 1 (should be dirty)
2. User switches to clean tab 2
3. Persistency still shows dirty=True (from tab 1)
4. User closes app → prompted to save tab 2 (which is clean!)
5. Or worse: User modifies tab 2, switches to tab 1, saves → tab 2 changes lost

**Root Cause**: Global dirty flag doesn't match multi-document reality

---

#### Issue 3: Save Operation Doesn't Know Which Document
**Severity**: Critical  
**Impact**: Wrong document saved, data corruption

**Problem**:
- `save_current_document()` gets current tab's manager
- But calls `persistency.save_document()` which uses `persistency.current_filepath`
- If filepath is from different tab, wrong association happens

**Code Evidence**:
```python
# file_explorer_panel.py line ~925
def save_current_document(self):
    drawing_area = self.canvas_loader.get_current_document()
    manager = self.canvas_loader.get_canvas_manager(drawing_area)
    document = manager.to_document_model()
    
    # ❌ This uses persistency's global state, not manager's state!
    self.persistency.save_document(document, save_as=False, 
                                   is_default_filename=manager.is_default_filename())
```

**What Should Happen**:
Each manager should track its own filepath and dirty state, persistency should just do I/O.

---

#### Issue 4: File Tree Context Menu Broken
**Severity**: High  
**Impact**: Users can't manage files from tree

**Problem**: Context menu operations incomplete/broken:

**Working**:
- ✅ Rename (shows dialog, calls `explorer.rename_item()`)
- ✅ Delete (shows confirmation, calls `explorer.delete_item()`)
- ✅ Properties (shows info dialog)
- ✅ New Folder (creates folder)

**Broken**:
- ❌ **Open** - No handler for `_on_context_open_clicked`
- ❌ **New File** - No handler for `_on_context_new_file_clicked`
- ❌ Copy/Paste - Implemented but never wired to context menu
- ❌ Tree doesn't refresh after operations

**Code Evidence**:
```python
# file_explorer_panel.py line ~148
menu_items = [
    ('Open', self._on_context_open_clicked),      # ❌ Method doesn't exist
    ('New File', self._on_context_new_file_clicked),  # ❌ Method doesn't exist
    ...
]
```

---

#### Issue 5: Save-As Doesn't Update Tab Label
**Severity**: Medium  
**Impact**: UI confusion

**Problem**:
- User does Save-As to rename document
- File saves correctly
- But tab label still shows old name
- User must close/reopen tab to see correct name

**Root Cause**: `save_current_document_as()` doesn't call `canvas_loader.update_current_tab_label()`

---

#### Issue 6: New Document Creates Wrong State
**Severity**: Medium  
**Impact**: Confusing UX, save prompts when shouldn't

**Problem**:
- `new_document()` creates tab with default filename
- Should mark as "pristine" (no prompt on close)
- Currently marks as dirty or doesn't track correctly
- Closing empty new tab prompts for save

**Root Cause**: New tab initialization doesn't set clean state correctly

---

### 🟡 Medium Issues (Degraded UX)

#### Issue 7: Double-Click Opens in Wrong Tab
**Severity**: Medium  
**Impact**: Users see document in unexpected location

**Problem**:
- Double-clicking .shy file in tree opens document
- Always creates NEW tab (correct)
- But if many tabs open, hard to find which is new
- No visual indication of "just opened"

**Suggestion**: Flash new tab or auto-switch to it

---

#### Issue 8: File Tree Doesn't Auto-Refresh
**Severity**: Medium  
**Impact**: Stale view after operations

**Problem**:
- After save, tree doesn't update to show new file
- After delete, tree still shows deleted file (until manual refresh)
- After rename, tree shows old name

**Partially Implemented**:
```python
# file_explorer_panel.py line ~1126
def _on_file_saved_callback(self, filepath: str):
    self.set_current_file(filepath)
    self._load_current_directory()  # ✅ Refreshes tree
```

**But**: Only works if callback is wired correctly (needs verification)

---

#### Issue 9: No Confirmation on Overwrite (Save)
**Severity**: Low-Medium  
**Impact**: Accidental overwrites

**Problem**:
- Save (not Save-As) directly overwrites file
- No "Are you sure?" confirmation
- Standard behavior but some users want safety net

**Suggestion**: Optional setting for "confirm on save"

---

#### Issue 10: Delete Only Works on Empty Folders
**Severity**: Low  
**Impact**: Users can't clean up directories

**Problem**:
- Delete shows message "Only empty folders can be deleted"
- Users must manually empty folder first
- Tedious for nested structures

**Suggestion**: Offer "Delete folder and all contents?" option

---

### 🟢 Minor Issues (Polish)

#### Issue 11: Context Menu Position
**Severity**: Low  
**Impact**: Cosmetic

**Problem**: Context menu may appear off-screen on edge right-clicks

**Solution**: Calculate position to keep on-screen

---

#### Issue 12: No Keyboard Shortcuts in Tree
**Severity**: Low  
**Impact**: Power user efficiency

**Missing Shortcuts**:
- F2 → Rename
- Delete → Delete file
- Ctrl+C → Copy
- Ctrl+V → Paste
- Ctrl+N → New file

---

## Proposed Architecture (Multi-Document Support)

### Design Principle: Per-Document State

**Current (BROKEN)**:
```
Application
    └── ONE NetObjPersistency (filepath, is_dirty)
            ↓ confusion
    └── ModelCanvasLoader
            └── Tab 1 (ModelCanvasManager)
            └── Tab 2 (ModelCanvasManager)
            └── Tab 3 (ModelCanvasManager)
```

**Proposed (FIXED)**:
```
Application
    └── ModelCanvasLoader
            └── Tab 1
                    └── ModelCanvasManager (has objects, viewport)
                    └── DocumentState (filepath, is_dirty, persistency ref)
            └── Tab 2
                    └── ModelCanvasManager
                    └── DocumentState
            └── Tab 3
                    └── ModelCanvasManager
                    └── DocumentState
    
    └── NetObjPersistency (STATELESS I/O service)
            - Only methods: save_to_file(path, doc), load_from_file(path)
            - NO current_filepath
            - NO is_dirty tracking
```

### Alternative: Document State in Manager

**Even Simpler**:
```python
class ModelCanvasManager:
    def __init__(self):
        # Existing...
        self.places = []
        self.transitions = []
        self.arcs = []
        self.filename = "default"
        
        # ADD: File state
        self.filepath = None  # Full path to saved file (None if unsaved)
        self.is_dirty = False  # Has unsaved changes
    
    def mark_dirty(self):
        """Mark document as having unsaved changes."""
        if not self.is_dirty:
            self.is_dirty = True
            # Notify tab to update label with asterisk
            if self.on_dirty_changed:
                self.on_dirty_changed(True)
    
    def mark_clean(self):
        """Mark document as saved."""
        if self.is_dirty:
            self.is_dirty = False
            if self.on_dirty_changed:
                self.on_dirty_changed(False)
    
    def is_default_filename(self):
        """Check if using default/unsaved filename."""
        return self.filepath is None or self.filename == "default"
```

**Benefits**:
- ✅ Each manager owns its own state
- ✅ No confusion when switching tabs
- ✅ Canvas operations (add/delete objects) directly call `manager.mark_dirty()`
- ✅ Save operation: `persistency.save_to_file(manager.filepath, document)` then `manager.mark_clean()`
- ✅ Simple, obvious ownership

---

## Fix Plan (Phased Approach)

### Phase 1: Fix Critical Per-Document State (Priority 1)

**Goal**: Each document tracks its own filepath and dirty state

**Tasks**:
1. **Add state fields to ModelCanvasManager**
   - Add: `self.filepath = None`
   - Add: `self.is_dirty = False`
   - Add: `self.on_dirty_changed` callback
   - Add methods: `mark_dirty()`, `mark_clean()`, `set_filepath(path)`

2. **Wire object changes to mark_dirty()**
   - In `_on_object_changed()`: call `self.mark_dirty()`
   - In canvas operations (add/delete/modify): call `mark_dirty()`

3. **Update save operations**
   - `save_current_document()`:
     ```python
     manager = self.canvas_loader.get_canvas_manager(drawing_area)
     document = manager.to_document_model()
     
     # Use manager's state, not global persistency state
     if manager.is_default_filename():
         # Show save dialog
         filepath = persistency.show_save_dialog()
         if filepath:
             persistency.save_to_file(filepath, document)
             manager.set_filepath(filepath)
             manager.mark_clean()
     else:
         # Direct save
         persistency.save_to_file(manager.filepath, document)
         manager.mark_clean()
     ```

4. **Update tab labels**
   - Wire `manager.on_dirty_changed` to update tab label with asterisk
   - On save: update tab label with new filename

5. **Test multi-document scenario**
   - Open 3 documents
   - Modify tab 1 → verify asterisk appears
   - Switch to tab 2 → verify no asterisk (unless also modified)
   - Save tab 1 → verify asterisk disappears
   - Close app → verify only dirty tabs prompt for save

**Files to Modify**:
- `src/shypn/data/model_canvas_manager.py` - Add state fields and methods
- `src/shypn/helpers/file_explorer_panel.py` - Update save operations
- `src/shypn/helpers/model_canvas_loader.py` - Wire dirty callbacks to tabs
- `src/shypn/file/netobj_persistency.py` - Remove global state (or make optional)

**Estimated Effort**: 4-6 hours

---

### Phase 2: Fix File Tree Context Menu (Priority 2)

**Goal**: All context menu operations work correctly

**Tasks**:
1. **Add missing Open handler**
   ```python
   def _on_context_open_clicked(self, menu_item):
       """Open selected file in new tab."""
       if self.selected_item_path and not self.selected_item_is_dir:
           if self.selected_item_path.endswith('.shy'):
               self._open_file_from_path(self.selected_item_path)
   ```

2. **Add missing New File handler**
   ```python
   def _on_context_new_file_clicked(self, menu_item):
       """Create new .shy file in current directory."""
       self._show_new_file_dialog()
   
   def _show_new_file_dialog(self):
       """Show dialog to create new .shy file."""
       # Similar to _show_new_folder_dialog but creates file
       # Creates empty DocumentModel and saves to chosen name
   ```

3. **Wire Copy/Paste to context menu**
   - Currently `_on_copy_action` and `_on_paste_action` exist but unused
   - Add "Copy" and "Paste" menu items
   - Wire to existing handlers

4. **Add tree refresh after operations**
   - After delete: `self._load_current_directory()`
   - After rename: `self._load_current_directory()`
   - After create: `self._load_current_directory()`

5. **Test all context menu operations**
   - Right-click file → Open → should open in new tab
   - Right-click folder → New File → should create file
   - Right-click file → Delete → should delete and refresh
   - Right-click file → Rename → should rename and refresh

**Files to Modify**:
- `src/shypn/helpers/file_explorer_panel.py` - Add handlers, wire menu

**Estimated Effort**: 2-3 hours

---

### Phase 3: Improve Delete and Rename (Priority 3)

**Goal**: Better UX for file management

**Tasks**:
1. **Recursive folder delete**
   - Update `_show_delete_confirmation()` for folders
   - Add checkbox: "☑ Delete folder and all contents"
   - If checked: use `shutil.rmtree()`
   - If unchecked: check if empty first (current behavior)

2. **Prevent deleting/renaming open files**
   - Before delete: check if file is open in any tab
   - Show error: "Cannot delete '{filename}' - file is currently open. Please close it first."
   - Same for rename

3. **Auto-close tab on delete**
   - Alternative: If file is open, offer "Close tab and delete file?"
   - On Yes: close tab, then delete file

4. **Rename updates open tab**
   - If renamed file is open in tab, update tab label
   - Update manager's filepath

**Files to Modify**:
- `src/shypn/helpers/file_explorer_panel.py` - Update delete/rename logic
- `src/shypn/helpers/model_canvas_loader.py` - Add method to check if file is open

**Estimated Effort**: 2-3 hours

---

### Phase 4: Polish and Edge Cases (Priority 4)

**Goal**: Handle edge cases and improve UX

**Tasks**:
1. **Save-As updates tab label**
   ```python
   def save_current_document_as(self):
       # ... existing save dialog code ...
       if filepath:
           persistency.save_to_file(filepath, document)
           manager.set_filepath(filepath)
           manager.mark_clean()
           
           # UPDATE: Set tab label to new filename
           filename = os.path.basename(filepath)
           self.canvas_loader.update_current_tab_label(filename, is_modified=False)
   ```

2. **New document pristine state**
   ```python
   def new_document(self):
       # ... existing code ...
       page_index, drawing_area = self.canvas_loader.add_document()
       manager = self.canvas_loader.get_canvas_manager(drawing_area)
       manager.filepath = None
       manager.mark_clean()  # NEW EMPTY DOCUMENT IS CLEAN
   ```

3. **Flash new tab on open**
   - When opening file, briefly highlight new tab
   - Or auto-switch to new tab
   - Helps user find where file opened

4. **Keyboard shortcuts**
   - Add key-press handler to tree view
   - F2 → Rename
   - Delete → Delete
   - Enter → Open

5. **Context menu positioning**
   - Calculate to keep menu on-screen

**Files to Modify**:
- `src/shypn/helpers/file_explorer_panel.py` - Add keyboard handler, positioning
- Various - Small UX improvements

**Estimated Effort**: 2-4 hours

---

## Testing Plan

### Test Suite 1: Multi-Document State

| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| 1.1 | Open doc A, modify, switch to doc B | Doc A shows *, doc B shows no * |
| 1.2 | Open doc A, modify, save | Doc A saves correctly, * disappears |
| 1.3 | Open doc A, modify, switch to doc B, save B | B saves correctly, A still dirty |
| 1.4 | Create new doc, close immediately | No save prompt (pristine) |
| 1.5 | Create new doc, modify, close | Save prompt appears |
| 1.6 | Open 3 docs, modify all, close app | Prompt for each dirty doc in sequence |

### Test Suite 2: Save Operations

| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| 2.1 | Create new doc, click Save | Save dialog appears |
| 2.2 | Open doc, modify, click Save | Saves directly, no dialog |
| 2.3 | Open doc, modify, click Save As | Save dialog appears with current name |
| 2.4 | Import SBML, click Save | Save dialog appears (suggested name = model ID) |
| 2.5 | Open doc, save, modify, close | Prompt to save changes |

### Test Suite 3: Context Menu

| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| 3.1 | Right-click .shy file → Open | File opens in new tab |
| 3.2 | Right-click folder → New File | Dialog appears, file created |
| 3.3 | Right-click file → Delete | Confirmation appears, file deleted, tree refreshes |
| 3.4 | Right-click file → Rename | Dialog appears, file renamed, tree refreshes |
| 3.5 | Right-click file → Copy, right-click folder → Paste | File copied to folder |

### Test Suite 4: Edge Cases

| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| 4.1 | Open doc, delete from tree | Error: "File is open" |
| 4.2 | Open doc, rename from tree | Tab label updates, manager filepath updates |
| 4.3 | Save as "default.shy" | Warning dialog appears |
| 4.4 | Open non-existent file | Error message, no crash |
| 4.5 | Save to read-only location | Error message, no crash |

---

## Priority Matrix

| Phase | Priority | Risk | Effort | Impact |
|-------|----------|------|--------|--------|
| Phase 1: Per-Doc State | 🔴 Critical | High | 6h | Fixes data loss |
| Phase 2: Context Menu | 🟡 High | Low | 3h | Restores functionality |
| Phase 3: Delete/Rename | 🟢 Medium | Low | 3h | Improves UX |
| Phase 4: Polish | 🔵 Low | Low | 4h | Nice to have |

**Recommended Order**: Phase 1 → Phase 2 → Phase 3 → Phase 4

---

## Success Criteria

✅ **Phase 1 Complete When**:
- Each document tracks own filepath and dirty state
- Tab asterisks update correctly when switching tabs
- Save operations work on correct document
- Multi-document save-on-close works correctly
- No data loss scenarios remain

✅ **Phase 2 Complete When**:
- All context menu items work
- Tree refreshes after operations
- Can open files from tree
- Can create new files from tree

✅ **Phase 3 Complete When**:
- Can delete non-empty folders (with confirmation)
- Cannot delete/rename open files (or get proper warning)
- Rename updates open tabs

✅ **Phase 4 Complete When**:
- All edge cases handled gracefully
- Keyboard shortcuts work
- UX polish complete

---

## Notes for Implementation

### Critical Decision Point

**Question**: Should we keep `NetObjPersistency` class at all?

**Option A: Keep It (Refactored)**
- Make it a stateless I/O service
- Methods: `save_to_file(path, doc)`, `load_from_file(path)`, `show_save_dialog()`, `show_open_dialog()`
- State lives in `ModelCanvasManager`
- Pro: Centralizes file I/O logic
- Pro: Handles dialogs in one place

**Option B: Eliminate It**
- Move I/O directly to `DocumentModel.save_to_file()` and `DocumentModel.load_from_file()`
- Move dialogs to FileExplorerPanel
- State lives in ModelCanvasManager
- Pro: Simpler architecture
- Con: Duplicates dialog code if needed elsewhere

**Recommendation**: Option A - Keep refactored NetObjPersistency as I/O service

---

## Conclusion

The file operations system has fundamental architectural issues due to **single global state** managing **multiple documents**. The fix requires:

1. **Moving state ownership** from global to per-document (ModelCanvasManager)
2. **Refactoring NetObjPersistency** to be a stateless service
3. **Fixing broken context menu** handlers
4. **Improving UX** for delete, rename, and edge cases

**Estimated Total Effort**: 12-16 hours across 4 phases

**Risk Assessment**: 
- Phase 1 is high-risk (core architecture change) but essential
- Phases 2-4 are low-risk incremental improvements

**Next Steps**:
1. Review this analysis with user
2. Get approval for Phase 1 approach
3. Begin implementation with Phase 1
4. Test thoroughly before proceeding to Phase 2
