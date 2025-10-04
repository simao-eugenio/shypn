# Save Dialog and TreeView Refinements

**Date:** October 4, 2025  
**Status:** ✅ Implemented and Tested

## Overview

Two UI/UX refinements were implemented to improve the user experience:

1. **Save Dialog Behavior**: File chooser now always opens for documents with "default" filename
2. **TreeView Styling**: Applied modern CSS styling to the file explorer TreeView

---

## Refinement 1: Save Dialog for Default Filename

### Problem

When a document had filename "default", clicking Save would NOT show the file chooser dialog if the persistency manager had a `current_filepath` set from a previous save operation. This could lead to:

```
1. User opens "mymodel.shy" → filepath = "mymodel.shy"
2. User clears canvas → filename = "default", but filepath still = "mymodel.shy"
3. User draws new objects
4. User clicks Save → Overwrites mymodel.shy without prompting! ❌
```

### Solution

Modified `save_document()` to accept an optional `filename` parameter and check if it equals "default". When the filename is "default", the file chooser is ALWAYS shown, regardless of whether a filepath exists.

**Files Modified:**

1. **src/shypn/file/netobj_persistency.py**:
   ```python
   def save_document(self, document, save_as: bool = False, filename: Optional[str] = None) -> bool:
       """Save document to file.
       
       Behavior:
       - If filename is "default": ALWAYS show file chooser (even with existing filepath)
       - If document has a filepath AND save_as=False AND filename != "default": Save directly
       - If document has NO filepath OR save_as=True: Show file chooser dialog
       """
       # Check if we need to prompt for filename
       # ALWAYS prompt if filename is "default" (unsaved document state)
       needs_prompt = save_as or not self.has_filepath() or (filename == "default")
       
       if needs_prompt:
           filepath = self._show_save_dialog()
           # ... rest of logic
   ```

2. **src/shypn.py**:
   ```python
   def on_save_document(button):
       """Save current document to file."""
       # ... get manager ...
       
       # Save using persistency manager
       # Pass filename to check if it's "default" (always prompt in that case)
       persistency.save_document(manager.document, save_as=False, filename=manager.filename)
   ```

### Expected Behavior

**New Document Save:**
```
1. App starts → filename="default", filepath=None
2. User draws objects
3. User clicks Save → File chooser opens with "default.shy" ✓
4. User enters "newmodel" → Saves as "newmodel.shy" ✓
```

**Clear Canvas and Save:**
```
1. User has "mymodel.shy" open → filename="mymodel", filepath="mymodel.shy"
2. User clears canvas → filename="default", filepath=None
3. User draws new objects
4. User clicks Save → File chooser opens with "default.shy" ✓
5. User can save with new name without overwriting old file ✓
```

**Normal Save (Non-Default):**
```
1. User has "mymodel.shy" open → filename="mymodel", filepath="mymodel.shy"
2. User modifies objects
3. User clicks Save → Saves directly to "mymodel.shy" (no dialog) ✓
```

---

## Refinement 2: TreeView CSS Styling

### Problem

The file explorer TreeView had default GTK3 styling which looked basic and didn't provide good visual feedback for user interactions.

### Solution

Applied custom CSS styling to the TreeView to provide:
- Modern, clean appearance
- Better hover feedback
- Clear selection highlighting
- Improved cell padding and spacing
- Styled headers
- Colored expander arrows for tree hierarchy

**File Modified:**

**src/shypn/ui/panels/file_explorer_panel.py**:

Added `_apply_tree_view_css()` method called from `_configure_tree_view()`:

```python
def _apply_tree_view_css(self):
    """Apply CSS styling to improve TreeView appearance."""
    css_provider = Gtk.CssProvider()
    
    # Modern, clean TreeView styling
    css = b"""
    /* File explorer TreeView styling */
    treeview {
        background-color: #fafafa;
        color: #2e3436;
    }
    
    /* Selected row */
    treeview.view:selected {
        background-color: #4a90d9;
        color: #ffffff;
    }
    
    /* Hover effect */
    treeview.view:hover {
        background-color: #e8e8e8;
    }
    
    /* Cell padding and spacing */
    treeview.view cell {
        padding-top: 4px;
        padding-bottom: 4px;
        padding-left: 6px;
        padding-right: 6px;
    }
    
    /* ... more styling ... */
    """
    
    css_provider.load_from_data(css)
    style_context = self.tree_view.get_style_context()
    style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
```

### Visual Improvements

| Element | Before | After |
|---------|--------|-------|
| **Background** | Default gray | Light clean #fafafa |
| **Selected row** | Light blue | Bold blue #4a90d9 with white text |
| **Hover** | None | Subtle gray #e8e8e8 |
| **Cell padding** | Minimal | 4px vertical, 6px horizontal |
| **Headers** | Basic | Bold with background #e8e8e8 |
| **Expanders** | Black | Gray #5a5a5a, blue on hover #2a76c6 |

### User Experience

Users now get:
1. **Clear feedback** on which file/folder is being hovered
2. **Obvious selection** with high-contrast blue highlighting
3. **Better readability** with improved padding and spacing
4. **Professional appearance** matching modern file browsers

---

## Testing Checklist

✅ **Save Dialog Behavior:**
- [x] New document save shows file chooser with "default.shy"
- [x] Clear canvas resets filename to "default"
- [x] Save after clear canvas shows file chooser (doesn't overwrite old file)
- [x] Normal save (non-default filename) saves directly without dialog
- [x] Warning shown if user tries to save as "default.shy"

✅ **TreeView Styling:**
- [x] TreeView has light clean background
- [x] Hover shows subtle gray highlight
- [x] Selection shows bold blue highlight with white text
- [x] Cell padding provides comfortable spacing
- [x] Headers are styled with bold text
- [x] Expander arrows change color on hover

---

## Implementation Notes

### Design Decisions

1. **Default Filename Check**: Using `filename == "default"` is reliable because:
   - "default" is the canonical unsaved document state
   - Set consistently across all operations (new document, clear canvas)
   - Easy to understand and maintain

2. **CSS Application**: Using `Gtk.CssProvider` with `STYLE_PROVIDER_PRIORITY_APPLICATION`:
   - Overrides default GTK3 theme
   - Consistent across different user themes
   - Can be customized per widget (only affects file explorer TreeView)

3. **Error Handling**: Both refinements include graceful error handling:
   - Optional filename parameter defaults to None (backward compatible)
   - CSS loading wrapped in try-except (application continues if CSS fails)

### Related Components

These refinements integrate with:
- **NetObjPersistency**: File save/load operations
- **ModelCanvasManager**: Document state and filename
- **ModelCanvasLoader**: Canvas operations (clear canvas)
- **FileExplorerPanel**: File browser UI

### Future Enhancements

Potential improvements:
1. Add user preference for TreeView theme (light/dark)
2. Add keyboard shortcut indication in save dialog
3. Add file type icons for different extensions
4. Add file size and modification date columns (optional)

---

## Code Changes Summary

**Files Modified:**
1. `src/shypn/file/netobj_persistency.py` - Added filename parameter to save_document()
2. `src/shypn.py` - Pass manager.filename to save_document()
3. `src/shypn/ui/panels/file_explorer_panel.py` - Added _apply_tree_view_css() method

**Lines Changed:** ~70 lines total
**Complexity:** Low (focused refinements)
**Risk:** Low (well-isolated changes)

---

## Related Documentation

- `SAVE_OPERATION_FLOW.md` - Complete save operation documentation
- `DEFAULT_FILENAME_NORMALIZATION.md` - Default filename behavior
- `FILE_EXTENSION_SHY.md` - File extension change to .shy

---

**Status:** ✅ **Both refinements implemented and tested successfully**
