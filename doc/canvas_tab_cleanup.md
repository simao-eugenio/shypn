# Canvas Tab Cleanup - Removed Filename Display

## Changes Made

### Issue
The canvas notebook tabs were displaying an editable filename entry showing "default.shy", which was unnecessary and cluttered the interface.

### Solution
Removed all filename tracking and editable tab label functionality from the canvas, replacing it with empty tab labels.

## Files Modified

### `src/shypn/helpers/model_canvas_loader.py`

#### 1. Removed Filename Tracking Dictionary
**Before:**
```python
self.document_filenames = {}  # {drawing_area: filename_without_extension}
```

**After:**
```python
# Removed - no filename tracking needed
```

#### 2. Simplified Initial Tab Label
**Before:**
```python
# Update initial tab label to editable format [default.shy]
if drawing_area:
    tab_label = self._create_editable_tab_label("default", drawing_area)
    self.notebook.set_tab_label(page, tab_label)
    self.document_filenames[drawing_area] = "default"
    tab_label.get_style_context().add_class("active-tab")
```

**After:**
```python
# Set tab label to empty (no filename display)
if drawing_area:
    # Create simple empty label for tab
    tab_label = Gtk.Label(label="")
    self.notebook.set_tab_label(page, tab_label)
    tab_label.show()
```

#### 3. Removed Editable Tab Label Methods
Completely removed the following methods and their implementations (~150 lines):
- `_create_editable_tab_label()` - Created editable filename entry with .shy extension
- `_on_filename_changed()` - Handled filename updates
- All associated CSS styling for tab entries

#### 4. Simplified Page Changed Handler
**Before:**
```python
def _on_notebook_page_changed(self, notebook, page, page_num):
    # Remove active-tab class from all tabs
    for i in range(notebook.get_n_pages()):
        tab_widget = notebook.get_tab_label(notebook.get_nth_page(i))
        if tab_widget:
            tab_widget.get_style_context().remove_class("active-tab")
    
    # Add active-tab class to the current tab
    current_tab = notebook.get_tab_label(page)
    if current_tab:
        current_tab.get_style_context().add_class("active-tab")
```

**After:**
```python
def _on_notebook_page_changed(self, notebook, page, page_num):
    """Handle notebook page switch."""
    # Simple page change handler - no special styling needed
    pass
```

#### 5. Simplified add_document() Method
**Before:**
```python
# Create editable tab label [filename.shy]
tab_label = self._create_editable_tab_label(filename, drawing)

# Store filename
self.document_filenames[drawing] = filename

print(f"✓ Added document: [{filename}.shy] (page {page_index})")
```

**After:**
```python
# Create simple empty tab label (no filename display)
tab_label = Gtk.Label(label="")

print(f"✓ Added document (page {page_index})")
```

#### 6. Fixed GTK3 DrawingArea Size
**Before (GTK4 code):**
```python
drawing.set_content_width(2000)
drawing.set_content_height(2000)
```

**After (GTK3 compatible):**
```python
# GTK3: Use set_size_request instead of set_content_width/height
drawing.set_size_request(2000, 2000)
```

#### 7. Removed Filename Parameter from Canvas Manager
**Before:**
```python
manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000, filename=filename)
validation = manager.create_new_document(filename)
```

**After:**
```python
# Create canvas manager for this drawing area (no filename needed)
manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000)
validation = manager.create_new_document()
```

## Code Removed

### Editable Tab Label CSS (~70 lines)
- `.tab-container` styling
- `.tab-filename-entry` styling with white background
- `.tab-filename-entry.final-name` for transparent background
- `.tab-filename-entry:focus` styling
- `.tab-filename-entry selection` styling
- `.tab-extension-label` for .shy extension

### Editable Tab Label Widget Creation (~50 lines)
- Filename entry creation
- Extension label creation
- Focus event handlers
- Change signal connections
- Width calculation logic

### Filename Change Handler (~30 lines)
- Extension removal logic
- Filename storage
- Width adjustment
- CSS class toggling
- Modified document marking

## Result

### Before:
- Tab showed: `[default    .shy]` (editable entry)
- Tab styling changed on focus
- Complex CSS for entry fields
- Filename tracking throughout codebase
- GTK4 methods causing errors

### After:
- ✅ Tab is empty (clean interface)
- ✅ No filename tracking needed
- ✅ ~200 lines of code removed
- ✅ Simplified architecture
- ✅ GTK3 compatible methods
- ✅ No CSS complexity
- ✅ Faster load times

## Benefits

1. **Cleaner Interface**: Empty tabs are less cluttered
2. **Simplified Code**: Removed 200+ lines of complexity
3. **Better Performance**: Less CSS processing and event handling
4. **GTK3 Compliance**: Fixed GTK4 methods that were causing errors
5. **Maintainability**: Less code to maintain and debug
6. **Focus on Canvas**: UI emphasizes the drawing area, not file management

## Testing

Verified:
- ✅ Application starts successfully
- ✅ Initial tab is empty
- ✅ Canvas renders correctly
- ✅ No filename display anywhere
- ✅ Tab switching works
- ✅ No console errors related to tab labels
- ✅ GTK3 DrawingArea size properly set

## Notes

- The UI file (`ui/canvas/model_canvas.ui`) already had a simple label "Model 1" which was being replaced by the code
- Now the code creates an empty label instead, resulting in a clean tab
- File management should be handled separately from the canvas display
- Canvas focus is now purely on the drawing functionality
