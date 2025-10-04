# Debug: File Operations Not Showing File Chooser

## Issue Report

**User Report:** "only file open it is launching the file chooser, no other file operations does, the flag file default name it is not working among others file operation"

**Expected Behavior:**
- Save, New, Save As operations should show file chooser for documents with "default" filename
- `is_default_filename()` flag should control whether file chooser appears

**Current Problem:**
- Only Open operation shows file chooser
- Save, New, Save As buttons appear to not work

## Diagnostic Steps Taken

### 1. Verified Flag Logic ✅

Created test script `test_file_operations_flow.py` which confirms:
- `is_default_filename()` returns `True` for filename="default" 
- `is_default_filename()` returns `False` for custom filenames
- Persistency save logic correctly evaluates: `needs_prompt = save_as or not has_filepath() or is_default_filename`

**Result:** The flag logic itself is correct.

### 2. Added Debug Logging 🔍

Added comprehensive debug logging to trace execution flow:

#### In `file_explorer_panel.py`:

**`save_current_document()` method:**
```python
print("[FileExplorer] save_current_document() called")
print(f"[FileExplorer] Manager filename: '{manager.filename}'")
print(f"[FileExplorer] is_default_filename(): {manager.is_default_filename()}")
print(f"[FileExplorer] Calling save_document with is_default_filename={manager.is_default_filename()}")
```

**`new_document()` method:**
```python
print("[FileExplorer] new_document() called")
print("[FileExplorer] User cancelled new document")  # if cancelled
print("[FileExplorer] Creating new document tab with default filename")  # if proceeding
```

**`save_current_document_as()` method:**
```python
print("[FileExplorer] save_current_document_as() called")
print(f"[FileExplorer] Current filename: '{manager.filename}'")
print("[FileExplorer] Calling save_document with save_as=True")
```

#### In `netobj_persistency.py` (`save_document()` method):

```python
print(f"[Persistency] save_document() called with save_as={save_as}, is_default_filename={is_default_filename}")
print(f"[Persistency] Current filepath: {self.current_filepath}")
print(f"[Persistency] has_filepath(): {self.has_filepath()}")
print(f"[Persistency] needs_prompt = {needs_prompt} (...)")
print("[Persistency] Showing file chooser dialog")  # if needs_prompt=True
print(f"[Persistency] Saving directly to: {self.current_filepath}")  # if needs_prompt=False
```

## Testing Instructions

### How to Test

1. **Run the application:**
   ```bash
   cd /home/simao/projetos/shypn
   /usr/bin/python3 src/shypn.py
   ```

2. **Test Save Operation:**
   - Application starts with a default document (filename="default")
   - Click the **Save** button in the file explorer toolbar
   - **Watch the terminal output**

3. **Expected Debug Output (if working correctly):**
   ```
   [FileExplorer] save_current_document() called
   [FileExplorer] Manager filename: 'default'
   [FileExplorer] is_default_filename(): True
   [FileExplorer] Calling save_document with is_default_filename=True
   [Persistency] save_document() called with save_as=False, is_default_filename=True
   [Persistency] Current filepath: None
   [Persistency] has_filepath(): False
   [Persistency] needs_prompt = True (...)
   [Persistency] Showing file chooser dialog
   ```

4. **Test New Operation:**
   - Click the **New** button
   - **Watch the terminal output**

5. **Test Save As Operation:**
   - Click the **Save As** button
   - **Watch the terminal output**

## Diagnostic Scenarios

### Scenario A: No Debug Output at All

**Symptom:** Clicking Save/New/Save As produces NO console output

**Diagnosis:** Button connections not working

**Possible Causes:**
1. Buttons don't exist in UI file (check `ui/panels/left_panel.ui`)
2. Button IDs don't match (check `_get_widgets()` in `file_explorer_panel.py`)
3. Signal connections failed silently

**Fix:**
- Verify button IDs in `left_panel.ui` match: `file_save_button`, `file_new_button`, `file_save_as_button`
- Check `_connect_signals()` method for proper connections

### Scenario B: Debug Output Shows Method Called But Wrong Values

**Symptom:** See `[FileExplorer] save_current_document() called` but:
- `manager.filename` is NOT 'default'
- `is_default_filename()` returns `False` when it should be `True`

**Diagnosis:** Manager initialization problem

**Possible Causes:**
1. Initial document not created with "default" filename
2. Canvas loader not passing filename correctly
3. Manager state corrupted

**Fix:**
- Check `model_canvas_loader.py` `load()` method - initial document setup
- Check `_setup_canvas_manager()` - verify filename parameter handling
- Verify `add_document()` passes filename correctly

### Scenario B: Debug Output Shows Correct Values But No File Chooser

**Symptom:** Console shows:
```
[Persistency] needs_prompt = True
[Persistency] Showing file chooser dialog
```
But no file chooser appears

**Diagnosis:** GTK file chooser issue

**Possible Causes:**
1. Dialog creation fails silently
2. Parent window not set correctly
3. GTK threading issue

**Fix:**
- Check `_show_save_dialog()` in `netobj_persistency.py`
- Verify parent window is set
- Add try/except with error reporting

### Scenario D: Wiring Not Complete

**Symptom:** Error messages like:
```
[FileExplorer] Error: Canvas loader not wired
[FileExplorer] Error: Persistency manager not wired
```

**Diagnosis:** Component wiring failed

**Possible Causes:**
1. `set_canvas_loader()` or `set_persistency_manager()` not called
2. Called too late or on wrong instance
3. Exception during wiring

**Fix:**
- Check `shypn.py` wiring section (around line 100-120)
- Verify `file_explorer = left_panel_loader.file_explorer` gets correct instance
- Ensure wiring happens before window shows

## Architecture Verification

### Current Architecture (Should Be):

```
shypn.py (Launcher)
  └─> Creates components
  └─> Wires components:
      file_explorer.set_persistency_manager(persistency)
      file_explorer.set_canvas_loader(model_canvas_loader)
  
FileExplorerPanel (File Operations Controller)
  ├─> save_current_document()
  │   └─> Calls persistency.save_document(is_default_filename=manager.is_default_filename())
  ├─> new_document()
  │   └─> Calls persistency.new_document() + canvas_loader.add_document()
  └─> save_current_document_as()
      └─> Calls persistency.save_document(save_as=True)

ModelCanvasManager (State Management)
  ├─> filename: str (set on initialization)
  └─> is_default_filename() -> bool

NetObjPersistency (File I/O)
  └─> save_document(document, save_as, is_default_filename)
      └─> needs_prompt = save_as OR not has_filepath() OR is_default_filename
```

### Button Connections (Should Be in `_connect_signals()`):

```python
self.new_button.connect("clicked", lambda btn: self.new_document())
self.open_button.connect("clicked", lambda btn: self.open_document())
self.save_button.connect("clicked", lambda btn: self.save_current_document())
self.save_as_button.connect("clicked", lambda btn: self.save_current_document_as())
```

## Code Changes Made

### Files Modified:

1. **`src/shypn/ui/panels/file_explorer_panel.py`**
   - Added debug logging to `save_current_document()`
   - Added debug logging to `new_document()`
   - Added debug logging to `save_current_document_as()`

2. **`src/shypn/file/netobj_persistency.py`**
   - Added debug logging to `save_document()` method

3. **Created:** `test_file_operations_flow.py` 
   - Standalone test to verify flag logic

### No Logic Changes

**Important:** Only debug logging was added. No functional logic was changed.
- All architectural patterns remain the same
- Button connections unchanged
- Flag logic unchanged
- Wiring unchanged

## Next Steps

1. **Run the application and test** - Click Save/New/Save As buttons
2. **Capture console output** - Copy ALL console output showing debug messages
3. **Identify the scenario** - Match output to diagnostic scenarios above
4. **Apply appropriate fix** - Based on which scenario matches

## Expected Resolution Timeline

Once console output is provided:
- **Scenario A (no output)**: Button connection fix - 15 minutes
- **Scenario B (wrong values)**: Manager initialization fix - 30 minutes  
- **Scenario C (correct values, no dialog)**: GTK dialog fix - 45 minutes
- **Scenario D (wiring issue)**: Quick wire fix - 10 minutes

## Cleanup After Fix

Once the issue is resolved and file operations work correctly:
1. Remove all debug `print()` statements
2. Test all operations again (save, new, open, save as)
3. Document the root cause and fix
4. Update architecture documentation if needed

---

**Status:** ⏳ Awaiting test run and console output to diagnose issue
**Blocker:** Cannot interact with running GUI to test buttons directly
**Resolution:** User must run app, click buttons, and report console output
