# File Explorer Integration Analysis

**Date:** October 4, 2025  
**Context:** Deep analysis of file explorer toolbar buttons, tree view context menu, and integration with NetObjPersistency

---

## Executive Summary

✅ **File Explorer Exists:** Complete file explorer implemented in `src/shypn/ui/panels/file_explorer_panel.py`  
❌ **NOT INTEGRATED:** File explorer toolbar buttons and context menu are NOT connected to NetObjPersistency  
⚠️ **DUPLICATE WIRING:** Main app (`shypn.py`) connects toolbar buttons DIRECTLY to persistency, bypassing file explorer  
🔥 **CRITICAL GAP:** File explorer doesn't know about current open file, save/load operations, or dirty state

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        shypn.py (Main App)                   │
│  - Creates NetObjPersistency                                 │
│  - Connects toolbar buttons DIRECTLY to persistency          │
│  - File explorer not involved in file operations             │
└─────────────────────────────────────────────────────────────┘
         │
         ├───────────────────────────┬───────────────────────┐
         │                           │                       │
         ▼                           ▼                       ▼
┌───────────────────┐   ┌───────────────────────┐   ┌──────────────────┐
│ NetObjPersistency │   │ FileExplorerPanel     │   │ ModelCanvasLoader│
│ (File Operations) │   │ (File Browser)        │   │ (Canvas)         │
│                   │   │                       │   │                  │
│ ✅ Save/Load      │   │ ❌ No integration     │   │ ✅ Document      │
│ ✅ Dirty tracking │   │ ❌ Unaware of files  │   │ ✅ Netobjs       │
│ ✅ Dialogs        │   │ ❌ Buttons unused    │   │                  │
│ ✅ Callbacks      │   │ ❌ Context menu stub │   │                  │
└───────────────────┘   └───────────────────────┘   └──────────────────┘
```

**PROBLEM:** File explorer and persistency don't communicate!

---

## Detailed Findings

### 1. File Explorer Toolbar Buttons

**Location:** `src/shypn/ui/panels/file_explorer_panel.py:118-133`

#### Buttons Defined:
```python
self.new_button = self.builder.get_object('file_new_button')
self.open_button = self.builder.get_object('file_open_button')
self.save_button = self.builder.get_object('file_save_button')
self.save_as_button = self.builder.get_object('file_save_as_button')
self.new_folder_button = self.builder.get_object('file_new_folder_button')
```

#### Current Signal Handlers (Lines 151-158):
```python
if self.new_button:
    self.new_button.connect("clicked", self._on_file_new_clicked)
if self.open_button:
    self.open_button.connect("clicked", self._on_file_open_clicked)
if self.save_button:
    self.save_button.connect("clicked", self._on_file_save_clicked)
if self.save_as_button:
    self.save_as_button.connect("clicked", self._on_file_save_as_clicked)
if self.new_folder_button:
    self.new_folder_button.connect("clicked", self._on_file_new_folder_clicked)
```

#### Handler Implementation Status:

**❌ `_on_file_new_clicked` (Lines 453-462):**
```python
def _on_file_new_clicked(self, button: Gtk.Button):
    """Handle New File button click.
    
    Note: The main application (shypn.py) connects its own handler
    to this button to create new documents. This handler just updates
    the current file display.
    """
    # The main app will handle document creation
    # We just update the display
    # self.set_current_file("untitled.shy")
```
**Status:** STUB - Does nothing, relies on main app override

**❌ `_on_file_open_clicked` (Lines 464-469):**
```python
def _on_file_open_clicked(self, button: Gtk.Button):
    """Handle Open File button click."""
    # TODO: Show file chooser dialog or use selected file from tree
    # For now, use the selected item if it's a file
    if self.selected_item_path and not self.selected_item_is_dir:
        self.set_current_file(self.selected_item_name)
```
**Status:** PARTIAL - Only updates display, doesn't actually load file

**❌ `_on_file_save_clicked` (Lines 471-478):**
```python
def _on_file_save_clicked(self, button: Gtk.Button):
    """Handle Save button click."""
    # TODO: Save current file to disk
    if self.current_opened_file:
        pass
    else:
        pass
```
**Status:** STUB - Does nothing

**❌ `_on_file_save_as_clicked` (Lines 480-484):**
```python
def _on_file_save_as_clicked(self, button: Gtk.Button):
    """Handle Save As button click."""
    # TODO: Show save as dialog
    if self.current_opened_file:
        pass
```
**Status:** STUB - Does nothing

**✅ `_on_file_new_folder_clicked` (Lines 486-489):**
```python
def _on_file_new_folder_clicked(self, button: Gtk.Button):
    """Handle New Folder button click."""
    # Reuse the existing new folder dialog
    self._show_new_folder_dialog()
```
**Status:** WORKING - Creates folders in file explorer

---

### 2. Main App Button Wiring (Overrides File Explorer)

**Location:** `src/shypn.py:96-173`

#### New Document Button (Lines 96-106):
```python
new_doc_button = left_panel_loader.builder.get_object('file_new_button')
if new_doc_button:
    def on_new_document(button):
        """Create a new document tab."""
        if not persistency.check_unsaved_changes():
            return
        
        if persistency.new_document():
            model_canvas_loader.add_document()
    new_doc_button.connect('clicked', on_new_document)
```
**Status:** ✅ Works - Creates new document, checks unsaved changes

#### Save Button (Lines 108-125):
```python
save_button = left_panel_loader.builder.get_object('file_save_button')
if save_button:
    def on_save_document(button):
        """Save current document to file."""
        drawing_area = model_canvas_loader.get_current_document()
        if drawing_area is None:
            print("[Save] No document to save")
            return
        
        manager = model_canvas_loader.get_canvas_manager(drawing_area)
        if manager is None or manager.document is None:
            print("[Save] No document model found")
            return
        
        # Save using persistency manager
        persistency.save_document(manager.document, save_as=False)
    save_button.connect('clicked', on_save_document)
```
**Status:** ✅ Works - Saves current document

#### Open Button (Lines 127-159):
```python
open_button = left_panel_loader.builder.get_object('file_open_button')
if open_button:
    def on_open_document(button):
        """Open document from file."""
        # Load using persistency manager
        document, filepath = persistency.load_document()
        
        if document and filepath:
            # Create new tab with loaded document
            import os
            filename = os.path.basename(filepath)
            base_name = os.path.splitext(filename)[0]
            
            page_index, drawing_area = model_canvas_loader.add_document(filename=base_name)
            
            # Replace the document in the canvas manager
            manager = model_canvas_loader.get_canvas_manager(drawing_area)
            if manager:
                manager.document = document
                
                # Rebuild object lists in manager
                manager.places = list(document.places)
                manager.transitions = list(document.transitions)
                manager.arcs = list(document.arcs)
                
                # Trigger redraw
                drawing_area.queue_draw()
                
                print(f"[Load] Document loaded into new tab: {base_name}")
    open_button.connect('clicked', on_open_document)
```
**Status:** ✅ Works - Opens document in new tab

#### Save As Button (Lines 161-173):
```python
save_as_button = left_panel_loader.builder.get_object('file_save_as_button')
if save_as_button:
    def on_save_as_document(button):
        """Save current document to new file."""
        drawing_area = model_canvas_loader.get_current_document()
        if drawing_area is None:
            print("[Save As] No document to save")
            return
        
        manager = model_canvas_loader.get_canvas_manager(drawing_area)
        if manager is None or manager.document is None:
            print("[Save As] No document model found")
            return
        
        # Save using persistency manager (save_as=True)
        persistency.save_document(manager.document, save_as=True)
    save_as_button.connect('clicked', on_save_as_document)
```
**Status:** ✅ Works - Saves document to new file

**CRITICAL ISSUE:** Main app connects handlers **AFTER** file explorer panel connects its stub handlers!  
**Result:** Main app handlers override file explorer handlers, but file explorer is unaware of operations.

---

### 3. Tree View Context Menu

**Location:** `src/shypn/ui/panels/file_explorer_panel.py:176-206`

#### Context Menu Items:
```python
menu_items = [
    ("Open", self._on_open_clicked),           # ❌ Stub
    ("New Folder", self._on_new_folder_clicked), # ✅ Works
    ("---", None),  # Separator
    ("Cut", self._on_cut_clicked),              # ✅ Works
    ("Copy", self._on_copy_clicked),            # ✅ Works
    ("Paste", self._on_paste_clicked),          # ✅ Works
    ("Duplicate", self._on_duplicate_clicked),  # ✅ Works
    ("---", None),  # Separator
    ("Rename", self._on_rename_clicked),        # ✅ Works
    ("Delete", self._on_delete_clicked),        # ✅ Works
    ("---", None),  # Separator
    ("Refresh", self._on_refresh_clicked),      # ✅ Works
    ("Properties", self._on_properties_clicked), # ✅ Works
]
```

#### Context Menu Handler Status:

**❌ `_on_open_clicked` (Lines 556-561):**
```python
def _on_open_clicked(self, button):
    """Handle 'Open' context menu button."""
    # Menu automatically dismisses in GTK3
    if self.selected_item_path and not self.selected_item_is_dir:
        # Open the file (for now, just set as current file)
        self.set_current_file(self.selected_item_path)
        # TODO: Integrate with document management to actually open file in editor
```
**Status:** STUB - Only updates display, doesn't load file into canvas

**Analysis:** All other context menu items work properly for file system operations (cut/copy/paste/rename/delete/properties), but the critical "Open" action is not integrated with document management.

---

### 4. NetObjPersistency Callbacks (UNUSED)

**Location:** `src/shypn/file/netobj_persistency.py:73-76`

#### Callback Definitions:
```python
# Callbacks for observers
self.on_file_saved: Optional[Callable[[str], None]] = None
self.on_file_loaded: Optional[Callable[[str, any], None]] = None
self.on_dirty_changed: Optional[Callable[[bool], None]] = None
```

#### Callback Invocation Points:

**`on_file_saved` (Line 190-191):**
```python
if self.on_file_saved:
    self.on_file_saved(self.current_filepath)
```

**`on_file_loaded` (Line 242-243):**
```python
if self.on_file_loaded:
    self.on_file_loaded(filepath, document)
```

**CRITICAL GAP:** These callbacks are **NEVER SET** in the main app!  
**Result:** File explorer has no way to know when files are saved/loaded.

---

### 5. Current File Display (Partially Working)

**Location:** `src/shypn/ui/panels/file_explorer_panel.py:79-81`

```python
# Track current opened file (for display in toolbar)
# Set default filename with relative path from models directory
self.current_opened_file: Optional[str] = "models/default.shy"
```

**Widget:** `self.current_file_entry` (Line 130)

**Update Method:** `set_current_file()` (Lines 1117-1156)

**Current Status:**
- ✅ Widget exists and displays filename
- ✅ Method can update display
- ❌ **NEVER CALLED** when files are actually loaded/saved by main app
- ❌ Shows stale "models/default.shy" by default

---

## Integration Gaps Summary

| Component | Feature | Status | Impact |
|-----------|---------|--------|--------|
| **File Explorer Toolbar** | New button | ❌ Stub | Main app overrides |
| **File Explorer Toolbar** | Open button | ❌ Stub | Main app overrides |
| **File Explorer Toolbar** | Save button | ❌ Stub | Main app overrides |
| **File Explorer Toolbar** | Save As button | ❌ Stub | Main app overrides |
| **File Explorer Toolbar** | New Folder button | ✅ Works | Creates folders |
| **Context Menu** | Open | ❌ Stub | Doesn't load into canvas |
| **Context Menu** | Cut/Copy/Paste | ✅ Works | File system ops |
| **Context Menu** | Rename/Delete | ✅ Works | File system ops |
| **Context Menu** | Properties | ✅ Works | Shows file info |
| **NetObjPersistency** | on_file_saved callback | ❌ Not set | File explorer unaware |
| **NetObjPersistency** | on_file_loaded callback | ❌ Not set | File explorer unaware |
| **NetObjPersistency** | on_dirty_changed callback | ❌ Not set | File explorer unaware |
| **Current File Display** | Widget exists | ✅ Works | Shows filename |
| **Current File Display** | Updates on load | ❌ Missing | Shows stale data |
| **Current File Display** | Updates on save | ❌ Missing | Shows stale data |

---

## Root Cause Analysis

### Why File Explorer is Not Integrated:

1. **Historical Development:**
   - File explorer was created BEFORE NetObjPersistency
   - Initially designed as standalone file browser
   - TODO comments indicate planned integration never completed

2. **Architecture Mismatch:**
   - Main app creates persistency manager
   - Main app connects toolbar buttons DIRECTLY
   - File explorer panel has no reference to persistency manager
   - No communication channel between components

3. **Signal Override:**
   - File explorer connects stub handlers first
   - Main app connects real handlers second
   - GTK signals allow multiple handlers, but main app handlers win
   - File explorer handlers execute but do nothing

4. **Missing Callback Wiring:**
   - NetObjPersistency has callback infrastructure
   - Main app never sets callbacks
   - File explorer never receives notifications
   - Current file display shows stale data

---

## Recommended Solutions

### Option A: Proper Integration (Recommended)

**Goal:** Make file explorer aware of persistency operations and update UI accordingly

**Steps:**

1. **Pass persistency reference to file explorer:**
   ```python
   # In shypn.py after creating persistency
   left_panel_loader.set_persistency_manager(persistency)
   ```

2. **Update FileExplorerPanel to accept persistency:**
   ```python
   def set_persistency_manager(self, persistency: NetObjPersistency):
       """Wire file explorer to persistency manager."""
       self.persistency = persistency
       
       # Set callbacks
       persistency.on_file_saved = self._on_file_saved_callback
       persistency.on_file_loaded = self._on_file_loaded_callback
       persistency.on_dirty_changed = self._on_dirty_changed_callback
   ```

3. **Implement callback handlers in FileExplorerPanel:**
   ```python
   def _on_file_saved_callback(self, filepath: str):
       """Update UI when file is saved."""
       self.set_current_file(filepath)
       self.refresh()  # Refresh tree if file was saved
   
   def _on_file_loaded_callback(self, filepath: str, document):
       """Update UI when file is loaded."""
       self.set_current_file(filepath)
       self.refresh()  # Refresh tree if needed
   
   def _on_dirty_changed_callback(self, is_dirty: bool):
       """Update UI when dirty state changes."""
       # Could show asterisk in current file label: "myfile.txt*"
       if self.current_opened_file:
           display = self.current_opened_file
           if is_dirty and not display.endswith('*'):
               display += ' *'
           elif not is_dirty and display.endswith('*'):
               display = display[:-2]
           self.current_file_label.set_text(display)
   ```

4. **Wire file explorer buttons to persistency:**
   ```python
   def _on_file_open_clicked(self, button: Gtk.Button):
       """Handle Open File button click."""
       if not self.persistency:
           return
       
       # Use selected file from tree if available
       if self.selected_item_path and not self.selected_item_is_dir:
           # TODO: Call persistency.load_specific_file(self.selected_item_path)
           pass
       else:
           # Use persistency dialog
           # TODO: Main app will handle this via its handler
           pass
   ```

5. **Update context menu Open action:**
   ```python
   def _on_open_clicked(self, button):
       """Handle 'Open' context menu button."""
       if not self.persistency or not self.selected_item_path:
           return
       
       if not self.selected_item_is_dir:
           # TODO: Need to integrate with main app's document loader
           # For now, just trigger the same flow as toolbar Open button
           pass
   ```

**Benefits:**
- File explorer aware of all file operations
- Current file display always accurate
- Can show dirty state indicator (asterisk)
- Can refresh tree when files are saved
- Context menu "Open" can work properly

**Effort:** Medium (2-3 hours)

---

### Option B: Minimal Fix (Quick Solution)

**Goal:** Just update current file display when files are opened/saved

**Steps:**

1. **Add callbacks in main app (shypn.py):**
   ```python
   # After creating left_panel_loader and persistency
   
   # Get file explorer reference
   file_explorer = left_panel_loader.file_explorer
   
   # Set callbacks
   def on_file_saved(filepath):
       if file_explorer:
           file_explorer.set_current_file(filepath)
   
   def on_file_loaded(filepath, document):
       if file_explorer:
           file_explorer.set_current_file(filepath)
   
   persistency.on_file_saved = on_file_saved
   persistency.on_file_loaded = on_file_loaded
   ```

**Benefits:**
- Quick fix (30 minutes)
- Current file display works
- Minimal code changes

**Limitations:**
- Context menu Open still doesn't work
- No dirty state indicator
- File explorer still isolated

**Effort:** Low (30 minutes)

---

### Option C: Remove Duplicate Handlers (Cleanup)

**Goal:** Remove stub handlers from file explorer, let main app handle everything

**Steps:**

1. **Remove stub handlers from FileExplorerPanel:**
   ```python
   # In _connect_signals(), remove these connections:
   # if self.new_button:
   #     self.new_button.connect("clicked", self._on_file_new_clicked)
   # if self.open_button:
   #     self.open_button.connect("clicked", self._on_file_open_clicked)
   # if self.save_button:
   #     self.save_button.connect("clicked", self._on_file_save_clicked)
   # if self.save_as_button:
   #     self.save_as_button.connect("clicked", self._on_file_save_as_clicked)
   ```

2. **Remove stub handler methods:**
   ```python
   # Delete _on_file_new_clicked
   # Delete _on_file_open_clicked
   # Delete _on_file_save_clicked
   # Delete _on_file_save_as_clicked
   ```

3. **Add comments explaining main app handles these:**
   ```python
   # Note: File operation buttons (New/Open/Save/Save As) are connected
   # in shypn.py main app to integrate with NetObjPersistency and
   # ModelCanvasLoader. Only New Folder button is handled here for
   # file explorer-specific folder creation.
   ```

**Benefits:**
- Clean code, no confusing stubs
- Clear responsibility: main app handles file ops
- Reduced maintenance burden

**Limitations:**
- Doesn't solve integration problems
- Still need to add callbacks for UI updates

**Effort:** Low (15 minutes)

---

## Recommended Action Plan

**Phase 1: Immediate (Option C + Option B)**
1. Remove stub handlers from file explorer (15 min)
2. Add callbacks in main app to update current file display (30 min)
3. Test that current file display updates correctly

**Phase 2: Complete Integration (Option A)**
1. Add `set_persistency_manager()` method to FileExplorerPanel
2. Implement callback handlers in FileExplorerPanel
3. Add dirty state indicator (asterisk) to current file display
4. Wire context menu "Open" to actually load files
5. Test complete integration

**Total Effort:** ~4 hours

---

## Testing Checklist

After implementing fixes:

- [ ] Open file via toolbar button → Current file display updates
- [ ] Save file via toolbar button → Current file display updates
- [ ] Save As to new file → Current file display updates with new filename
- [ ] Double-click file in tree → Opens in canvas AND updates display
- [ ] Context menu "Open" → Opens in canvas AND updates display
- [ ] Make changes → Dirty indicator appears (asterisk)
- [ ] Save file → Dirty indicator disappears
- [ ] New document → Current file display shows "untitled" or clears
- [ ] Close file → Current file display clears
- [ ] Switch tabs (if multiple documents) → Display updates to current tab's file

---

## Code References

### Key Files:
- **Main App:** `src/shypn.py` (Lines 96-173)
- **File Explorer Panel:** `src/shypn/ui/panels/file_explorer_panel.py`
- **NetObjPersistency:** `src/shypn/file/netobj_persistency.py`
- **Left Panel Loader:** `src/shypn/helpers/left_panel_loader.py`

### Key Methods to Modify:
- `FileExplorerPanel.__init__()` - Add persistency parameter
- `FileExplorerPanel.set_persistency_manager()` - NEW: Wire callbacks
- `FileExplorerPanel._on_file_open_clicked()` - Use persistency
- `FileExplorerPanel._on_open_clicked()` - Context menu open
- `main()` in `shypn.py` - Set persistency callbacks

---

## Conclusion

The file explorer and file operations infrastructure are **NOT INTEGRATED**. The file explorer exists as a standalone file browser with no awareness of document operations happening through NetObjPersistency.

**Critical Issues:**
1. ❌ Current file display shows stale data
2. ❌ Context menu "Open" doesn't load files into canvas
3. ❌ No dirty state indicator
4. ❌ File explorer can't refresh when files are saved
5. ❌ Duplicate stub handlers confuse code maintenance

**Recommended:** Implement **Option C + Option B** immediately (45 min), then **Option A** for complete integration (3 hours).

**Priority:** HIGH - Users expect file explorer to show accurate current file and respond to file operations.

---

**Analysis Date:** October 4, 2025  
**Analyst:** GitHub Copilot  
**Review Status:** Ready for implementation
