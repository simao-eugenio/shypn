# Keyboard Shortcuts - Save Operations Fix

**Date**: October 16, 2025  
**Status**: ✅ Complete  
**Issue**: Ctrl+S and Ctrl+Shift+S keyboard shortcuts were not working to save files

## Problem

While the UI tooltips showed "Save File (Ctrl+S)" and "Save As... (Ctrl+Shift+S)", these keyboard shortcuts were **not actually implemented**. Users could only save files by:
- Clicking the Save button in the File Explorer panel
- Using the context menu "Save" option

This is inconsistent with standard desktop application behavior and reduces productivity.

## Root Cause

The `_on_key_press_event()` handler in `model_canvas_loader.py` implemented several keyboard shortcuts:
- ✅ Delete key
- ✅ Ctrl+X (cut)
- ✅ Ctrl+C (copy)
- ✅ Ctrl+V (paste)
- ✅ Ctrl+Z (undo - placeholder)
- ✅ Ctrl+Shift+Z / Ctrl+Y (redo - placeholder)
- ✅ Escape (cancel operations)

But **Ctrl+S** and **Ctrl+Shift+S** were missing entirely.

Additionally, the `ModelCanvasLoader` class didn't have a reference to the `FileExplorerPanel` instance, which contains the `save_current_document()` and `save_current_document_as()` methods.

## Solution

### Phase 1: Add Keyboard Shortcut Handlers

Added Ctrl+S and Ctrl+Shift+S handlers to `_on_key_press_event()`:

```python
# Save (Ctrl+S) - check both lowercase and uppercase
if is_ctrl and not is_shift and (event.keyval == Gdk.KEY_s or event.keyval == Gdk.KEY_S):
    # Trigger save for current document
    if hasattr(self, 'file_explorer_panel') and self.file_explorer_panel:
        self.file_explorer_panel.save_current_document()
        return True

# Save As (Ctrl+Shift+S) - check both lowercase and uppercase
if is_ctrl and is_shift and (event.keyval == Gdk.KEY_s or event.keyval == Gdk.KEY_S):
    # Trigger save as for current document
    if hasattr(self, 'file_explorer_panel') and self.file_explorer_panel:
        self.file_explorer_panel.save_current_document_as()
        return True
```

**Location**: `src/shypn/helpers/model_canvas_loader.py` lines 1558-1571

### Phase 2: Wire FileExplorerPanel Reference

Added `set_file_explorer_panel()` method to `ModelCanvasLoader`:

```python
def set_file_explorer_panel(self, file_explorer_panel):
    """Set the file explorer panel for keyboard shortcut integration.
    
    This allows keyboard shortcuts (Ctrl+S, Ctrl+Shift+S) to trigger
    save operations through the file explorer panel.
    
    Args:
        file_explorer_panel: FileExplorerPanel instance from main application
    """
    self.file_explorer_panel = file_explorer_panel
```

**Location**: `src/shypn/helpers/model_canvas_loader.py` lines 2240-2250

### Phase 3: Connect in Main Application

Wired the file explorer panel to canvas loader in main application startup:

```python
# Wire file explorer panel to canvas loader
# This allows keyboard shortcuts (Ctrl+S, Ctrl+Shift+S) to trigger save operations
if file_explorer:
    model_canvas_loader.set_file_explorer_panel(file_explorer)
```

**Location**: `src/shypn.py` lines 226-229

## Implementation Details

### Keyboard Event Flow

1. User presses Ctrl+S or Ctrl+Shift+S while canvas has focus
2. `_on_key_press_event()` in `ModelCanvasLoader` receives event
3. Handler checks for Ctrl modifier and 's'/'S' key
4. Handler calls `file_explorer_panel.save_current_document()` or `save_current_document_as()`
5. FileExplorerPanel delegates to current tab's persistency manager
6. Save operation executes with full file operations logic (see FILE_OPERATIONS_PHASE1_IMPLEMENTATION.md)

### Save Operation Behavior

**Ctrl+S (Save)**:
- If document has filepath → save directly to that file
- If document is "default" or imported (no filepath) → show save dialog
- Updates tab label (removes asterisk if dirty)
- Marks manager as clean

**Ctrl+Shift+S (Save As)**:
- Always shows save dialog with new filename
- Saves to new location
- Updates tab label with new filename
- Marks manager as clean

### Case Handling

Both lowercase and uppercase keys are handled to ensure compatibility with different keyboard layouts and Caps Lock states:
- `Gdk.KEY_s` (lowercase 's')
- `Gdk.KEY_S` (uppercase 'S')

This matches the pattern used for other shortcuts (Ctrl+C, Ctrl+V, etc.).

## Files Modified

1. **src/shypn/helpers/model_canvas_loader.py**
   - Added Ctrl+S and Ctrl+Shift+S handlers in `_on_key_press_event()` (lines 1558-1571)
   - Added `set_file_explorer_panel()` method (lines 2240-2250)

2. **src/shypn.py**
   - Wired file_explorer_panel to model_canvas_loader (lines 226-229)

## Testing Checklist

### Basic Save (Ctrl+S)

- [ ] New document → Ctrl+S → shows save dialog
- [ ] Imported SBML → Ctrl+S → shows save dialog (no prior .shy path)
- [ ] Existing .shy file → modify → Ctrl+S → saves directly
- [ ] After save → verify asterisk disappears from tab label
- [ ] Multiple tabs → verify Ctrl+S saves only current tab

### Save As (Ctrl+Shift+S)

- [ ] New document → Ctrl+Shift+S → shows save dialog
- [ ] Existing file → Ctrl+Shift+S → shows save dialog with current name
- [ ] Save with new name → verify tab label updates
- [ ] Save to same location → verify replaces file

### Multi-Document Scenarios

- [ ] Tab 1 dirty → Tab 2 clean → Ctrl+S in Tab 1 → only Tab 1 saves
- [ ] Switch tabs → Ctrl+S in each → verify correct document saved
- [ ] Tab 1 save as → verify Tab 1 filename changes, Tab 2 unchanged

### Edge Cases

- [ ] Caps Lock ON → Ctrl+S → still works (uppercase 'S' handled)
- [ ] Shift+Ctrl+S → works (order doesn't matter)
- [ ] Ctrl+Alt+S → doesn't trigger (only Ctrl modifier)
- [ ] Empty canvas → Ctrl+S → shows save dialog (saves empty document)

## Consistency with Other Shortcuts

This implementation follows the same pattern as existing shortcuts:

| Shortcut | Action | Files Modified |
|----------|--------|---------------|
| Delete | Delete selected objects | ✅ Already implemented |
| Ctrl+X | Cut | ✅ Already implemented |
| Ctrl+C | Copy | ✅ Already implemented |
| Ctrl+V | Paste at pointer | ✅ Already implemented |
| Ctrl+Z | Undo (placeholder) | ✅ Already implemented |
| Ctrl+Shift+Z | Redo (placeholder) | ✅ Already implemented |
| Escape | Cancel operations | ✅ Already implemented |
| **Ctrl+S** | **Save** | **✅ NEW** |
| **Ctrl+Shift+S** | **Save As** | **✅ NEW** |

## Benefits

1. **Standard UX**: Matches behavior of all major desktop applications
2. **Productivity**: Faster save workflow without reaching for mouse
3. **Muscle Memory**: Users expect Ctrl+S to work
4. **Consistency**: Aligns with other implemented shortcuts
5. **Discoverability**: Tooltips already mentioned these shortcuts

## Future Enhancements

### Additional Shortcuts to Consider

- **Ctrl+N**: New document (currently only via File menu)
- **Ctrl+O**: Open file (currently only via File panel)
- **Ctrl+W**: Close current tab
- **Ctrl+Tab**: Switch to next tab
- **Ctrl+Shift+Tab**: Switch to previous tab
- **Ctrl+A**: Select all objects
- **Ctrl+D**: Duplicate selection

### Undo/Redo Implementation

Currently Ctrl+Z and Ctrl+Shift+Z are placeholders. When undo/redo system is implemented, these will work automatically.

## Related Documentation

- **FILE_OPERATIONS_PHASE1_IMPLEMENTATION.md**: Per-document state and save operations
- **EMPTY_DEFAULT_TAB_REPLACEMENT.md**: Tab management behavior
- **SHY_EXTENSION_ENFORCEMENT.md**: Extension handling in save dialogs

## Verification

✅ Application compiles successfully  
✅ Application launches without errors  
⏳ Awaiting user testing of keyboard shortcuts

## Commit Message

```
Add Ctrl+S and Ctrl+Shift+S keyboard shortcuts for save operations

- Added keyboard shortcut handlers in _on_key_press_event()
- Added set_file_explorer_panel() method to ModelCanvasLoader
- Wired file_explorer_panel reference in main application
- Supports both lowercase and uppercase keys (Caps Lock compatible)
- Ctrl+S: Save current document (shows dialog if no filepath)
- Ctrl+Shift+S: Save As (always shows dialog)
- Matches standard desktop application behavior
- Files: model_canvas_loader.py, shypn.py
```
