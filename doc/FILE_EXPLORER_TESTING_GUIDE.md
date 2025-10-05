# File Explorer Integration - Testing Guide

**Date:** October 4, 2025  
**Implementation Status:** ✅ Complete - Ready for Testing  

---

## Prerequisites

Before testing, ensure GTK3 and dependencies are installed:

```bash
# Ubuntu/Debian
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Or via pip (if system packages not available)
pip3 install PyGObject
```

---

## Running the Application

```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

---

## Test Scenarios

### Test 1: Current File Display Updates on Save

**Steps:**
1. Launch application
2. Create a new document (click "New" button)
3. Add some places/transitions to the canvas
4. Click "Save" button
5. Enter filename (e.g., "test_model.json")
6. Select models directory
7. Click Save

**Expected Results:**
- ✅ File saved successfully
- ✅ Current file display in left panel shows: "test_model.json"
- ✅ File appears in file explorer tree
- ✅ No asterisk (file is clean)

---

### Test 2: Current File Display Updates on Open (Toolbar)

**Steps:**
1. Launch application
2. Click "Open" button in toolbar
3. Select an existing .json file from models directory
4. Click Open

**Expected Results:**
- ✅ File loaded into new canvas tab
- ✅ Current file display shows: "filename.json"
- ✅ Tab label shows filename
- ✅ Canvas shows loaded Petri net objects
- ✅ No asterisk (file is clean)

---

### Test 3: Double-Click Opens File

**Steps:**
1. Launch application
2. Look at file explorer tree in left panel
3. Double-click a .json file in the tree

**Expected Results:**
- ✅ File loaded into new canvas tab
- ✅ Current file display updates to show filename
- ✅ Canvas shows loaded Petri net objects
- ✅ No asterisk (file is clean)

---

### Test 4: Context Menu Open

**Steps:**
1. Launch application
2. Right-click a .json file in file explorer tree
3. Select "Open" from context menu

**Expected Results:**
- ✅ File loaded into new canvas tab
- ✅ Current file display updates
- ✅ Canvas shows loaded objects

---

### Test 5: Context Menu Validates File Type

**Steps:**
1. Create a non-JSON file in models directory:
   ```bash
   echo "test" > models/test.txt
   ```
2. Launch application
3. Right-click the test.txt file
4. Select "Open"

**Expected Results:**
- ✅ Error message shown: "Can only open .json Petri net files"
- ✅ File NOT opened
- ✅ Current file display unchanged

---

### Test 6: Dirty State Indicator

**Steps:**
1. Launch application
2. Open an existing file (any method)
3. Current file display shows: "filename.json"
4. Make a change (add a place, move an object, etc.)
5. Observe current file display
6. Click "Save" button
7. Observe current file display again

**Expected Results:**
- ✅ After change: Display shows "filename.json *" (with asterisk)
- ✅ After save: Display shows "filename.json" (no asterisk)

---

### Test 7: Save As Updates Display

**Steps:**
1. Launch application
2. Open an existing file
3. Make some changes
4. Click "Save As" button
5. Enter new filename (e.g., "test_copy.json")
6. Click Save

**Expected Results:**
- ✅ File saved with new name
- ✅ Current file display updates to: "test_copy.json"
- ✅ New file appears in file explorer tree
- ✅ No asterisk (file is clean)

---

### Test 8: New Document

**Steps:**
1. Launch application (already has a document)
2. Make changes to current document (adds dirty state)
3. Click "New" button

**Expected Results:**
- ✅ Unsaved changes dialog appears
- ✅ If "Discard": New tab created, current file display clears or shows "untitled"
- ✅ If "Cancel": No new tab, stays on current document

---

### Test 9: File Explorer Operations Still Work

**Steps:**
1. Launch application
2. Test file explorer operations:
   - Right-click → "New Folder"
   - Right-click file → "Rename"
   - Right-click file → "Copy"
   - Right-click folder → "Paste"
   - Right-click file → "Delete"
   - Right-click file → "Properties"

**Expected Results:**
- ✅ All operations work as before
- ✅ No interference with file open operations
- ✅ Tree refreshes after operations

---

### Test 10: Multiple Files in Subdirectories

**Steps:**
1. Create subdirectory structure:
   ```bash
   mkdir -p models/project1
   mkdir -p models/project2
   ```
2. Save files in different directories
3. Navigate between directories in file explorer
4. Open files from different directories

**Expected Results:**
- ✅ Can navigate into subdirectories
- ✅ Can open files from any subdirectory
- ✅ Current file display shows relative path (e.g., "project1/model.json")
- ✅ Double-click and context menu work in subdirectories

---

### Test 11: File Tree Refreshes After Save

**Steps:**
1. Launch application
2. Create new document
3. Add some objects
4. Click "Save"
5. Enter new filename
6. Save to models directory
7. Look at file explorer tree

**Expected Results:**
- ✅ New file appears in tree immediately
- ✅ Tree shows correct filename
- ✅ Can immediately double-click the new file to re-open it

---

### Test 12: Switching Between Tabs

**Steps:**
1. Launch application
2. Open file A
3. Open file B (new tab)
4. Open file C (new tab)
5. Click between tabs

**Expected Results:**
- ✅ Current file display updates to show current tab's filename
- ✅ Dirty state indicator (asterisk) reflects current tab's state
- ✅ Each tab maintains its own state

**Note:** This test may reveal that current file display doesn't update on tab switch. If so, that's a known limitation - the callback only updates on save/load, not on tab switching. This would be an enhancement for the future.

---

## Common Issues and Solutions

### Issue: Current File Display Shows Stale Data
**Solution:** This was the problem we fixed! Ensure:
- `file_explorer.set_persistency_manager(persistency)` is called in shypn.py
- Callbacks are wired correctly

### Issue: Context Menu "Open" Doesn't Work
**Solution:** Ensure:
- `file_explorer.on_file_open_requested` callback is set in shypn.py
- File is a .json file

### Issue: Dirty State Indicator Doesn't Appear
**Solution:** Ensure:
- `_on_dirty_changed_callback` is wired in FileExplorerPanel
- `persistency.mark_dirty()` is called when document changes
- This might require additional wiring in canvas manager

### Issue: Double-Click Does Nothing
**Solution:** Check:
- `_on_row_activated` handler is connected
- `on_file_open_requested` callback is set
- Console for error messages

---

## Verification Checklist

After running all tests:

- [ ] ✅ Current file display always accurate
- [ ] ✅ Dirty state indicator works (asterisk)
- [ ] ✅ Toolbar Open button works
- [ ] ✅ Double-click opens files
- [ ] ✅ Context menu Open works
- [ ] ✅ Context menu validates file type
- [ ] ✅ Save updates display
- [ ] ✅ Save As updates display
- [ ] ✅ New document clears/updates display
- [ ] ✅ File tree refreshes after save
- [ ] ✅ Subdirectories work
- [ ] ✅ File explorer operations still work

---

## Known Limitations

1. **Tab Switching:** Current file display may not update when switching between tabs (only updates on save/load operations). This would require additional integration with the tab management system.

2. **Dirty State Propagation:** The dirty state must be propagated from canvas operations to persistency manager. This might require:
   - Calling `persistency.mark_dirty()` from canvas manager when objects are modified
   - Wiring canvas change events to persistency

3. **Auto-Highlight in Tree:** Currently doesn't highlight the opened file in the tree view. This is an enhancement for the future.

---

## Next Steps If Tests Fail

### If current file display doesn't update:
1. Check console for errors
2. Verify `set_persistency_manager()` is called
3. Add debug prints in callback methods
4. Check callback is actually being invoked

### If dirty state doesn't work:
1. Check if `mark_dirty()` is being called
2. Verify `on_dirty_changed` callback is wired
3. Add debug print in `_on_dirty_changed_callback`
4. May need to wire canvas operations to call `mark_dirty()`

### If context menu open doesn't work:
1. Check file extension (.json)
2. Verify `on_file_open_requested` callback is set
3. Check for exceptions in console
4. Add debug print in callback handler

---

## Debug Mode

To enable debug output, add print statements at key points:

```python
# In FileExplorerPanel._on_file_saved_callback
def _on_file_saved_callback(self, filepath):
    print(f"[DEBUG] File saved callback: {filepath}")
    self.set_current_file(filepath)
    self._load_current_directory()

# In FileExplorerPanel._on_dirty_changed_callback  
def _on_dirty_changed_callback(self, is_dirty):
    print(f"[DEBUG] Dirty state changed: {is_dirty}")
    # ... rest of method

# In shypn.py on_file_open_requested
def on_file_open_requested(filepath):
    print(f"[DEBUG] File open requested: {filepath}")
    try:
        # ... rest of method
```

This will show in console when callbacks are invoked.

---

## Success Criteria

Integration is successful if:

✅ All 12 test scenarios pass  
✅ Current file display always accurate  
✅ Dirty state indicator works  
✅ Multiple ways to open files work  
✅ File explorer operations unchanged  
✅ No regression in existing functionality  

---

## Conclusion

This comprehensive testing guide covers all aspects of the file explorer integration. Follow the test scenarios in order, verify expected results, and use the debugging tips if issues arise.

**Happy Testing!** 🎉

---

**Testing Guide Version:** 1.0  
**Date:** October 4, 2025  
**Status:** Ready for Manual Testing
