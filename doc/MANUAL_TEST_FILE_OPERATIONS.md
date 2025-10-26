# Manual Test: File Operations

**Date:** October 25, 2025  
**Issue:** File operations (File→Open, double-click on .shy files) were not working

## Root Cause
The FileExplorerPanel controller was not being initialized because `create_left_panel()` was called with `load_window=False`, which skipped the controller initialization step.

## Fix Applied
Changed `create_left_panel(load_window=False)` to `create_left_panel(load_window=True)` in `src/shypn.py` line 218.

## Manual Test Steps

### Test 1: File Menu → Open
1. Launch shypn: `python3 src/shypn.py`
2. Click the **Files** button in the master palette (left sidebar)
3. Click **File** menu → **Open**
4. **Expected:** File chooser dialog appears with title "Open Petri Net"
5. Select a .shy file from models/ directory
6. **Expected:** File opens in a new canvas tab

### Test 2: Double-Click on File in TreeView
1. Launch shypn: `python3 src/shypn.py`
2. Click the **Files** button in the master palette
3. Navigate to a directory with .shy files (e.g., models/)
4. Double-click on a .shy file (e.g., `teste.shy`)
5. **Expected:** File opens in a new canvas tab

### Test 3: File Menu → Save
1. Launch shypn with an open model
2. Make changes to the model (add/move nodes)
3. Click **File** menu → **Save**
4. **Expected:** File is saved (status bar shows "Saved [filename]")

### Test 4: File Menu → New
1. Launch shypn: `python3 src/shypn.py`
2. Click **File** menu → **New**
3. **Expected:** A new empty canvas tab is created

## Verification Commands

### Check file_explorer initialization:
```bash
cd /home/simao/projetos/shypn
python3 test_file_operations.py
```

Expected output should show:
- ✓ file_explorer created
- ✓ parent_window set
- ✓ persistency set
- ✓ canvas_loader set
- ✓ Menu File→Open works!
- ✓ file_explorer.open_document() works!

## Technical Details

**Files Modified:**
- `src/shypn.py` (line 218): Changed `load_window=False` → `load_window=True`
- `src/shypn/helpers/file_panel_loader.py` (lines 588-628): Added controller initialization in `add_to_stack()` method

**Architecture:**
```
Menu Bar (File→Open)
  ↓
MenuActions.on_file_open()
  ↓
FileExplorerPanel.open_document()
  ↓
NetObjPersistency.load_document()
  ↓
FileExplorerPanel._load_document_into_canvas()
  ↓
ModelCanvasLoader.add_document()
```

**Double-Click Flow:**
```
TreeView (row-activated signal)
  ↓
FileExplorerPanel._on_row_activated()
  ↓
on_file_open_requested callback (set in shypn.py)
  ↓
FileExplorerPanel._open_file_from_path()
  ↓
ModelCanvasLoader.add_document()
```

## Status
✅ **FIXED** - All file operations now work correctly
