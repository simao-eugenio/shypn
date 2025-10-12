# Tab Label with File Operations Integration

**Status**: ✅ IMPLEMENTATION COMPLETE  
**Date**: 2025-10-11  
**Feature**: Enhanced tab labels with file icon, filename.shy, and close button  
**Integration**: Connected to file operations (save/load/dirty state)  

---

## Overview

Enhanced the canvas notebook tabs to display:
- **File type icon** 📄 (document icon)
- **Filename with .shy extension** (e.g., "default.shy", "mymodel.shy")
- **Modification indicator** (asterisk "*" for unsaved changes)
- **Close button** (X) to close individual tabs

### Visual Pattern

```
[📄 icon] <filename.shy> (X)
[📄 icon] <filename.shy*> (X)  ← asterisk indicates unsaved changes
```

### Examples

```
[📄] default.shy (X)        ← New unsaved document
[📄] default.shy* (X)       ← Modified unsaved document
[📄] mymodel.shy (X)        ← Saved document
[📄] mymodel.shy* (X)       ← Saved document with changes
[📄] complex_net.shy (X)    ← Long names are ellipsized
```

---

## Implementation Details

### File Modified

**`src/shypn/helpers/model_canvas_loader.py`** (+120 lines)

### New Methods

#### 1. `_create_tab_label(filename, is_modified)`

Creates a tab label widget with icon, filename, and close button.

**Features**:
- Adds document icon using GTK stock icon 'text-x-generic'
- Automatically appends `.shy` extension if not present
- Uses `default.shy` for unnamed documents
- Ellipsizes long filenames (max 20 characters)
- Shows asterisk (*) for modified documents
- Returns tuple: `(tab_box, label_widget, close_button)`

**Code**:
```python
def _create_tab_label(self, filename='default', is_modified=False):
    """Create a tab label with file icon, filename, and close button."""
    tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    
    # File type icon (document icon for Petri nets)
    file_icon = Gtk.Image.new_from_icon_name('text-x-generic', Gtk.IconSize.MENU)
    tab_box.pack_start(file_icon, False, False, 0)
    
    # Use 'default.shy' if no filename provided
    if not filename or filename == 'default':
        filename = 'default.shy'
    elif not filename.endswith('.shy'):
        filename = f"{filename}.shy"
    
    # Filename label with ellipsize for long names
    display_name = f"{filename}{'*' if is_modified else ''}"
    tab_label = Gtk.Label(label=display_name)
    tab_label.set_ellipsize(3)  # Pango.EllipsizeMode.END
    tab_label.set_max_width_chars(20)
    tab_box.pack_start(tab_label, True, True, 0)
    
    # Close button (X)
    close_button = Gtk.Button()
    close_button.set_relief(Gtk.ReliefStyle.NONE)
    close_button.set_focus_on_click(False)
    close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
    close_button.set_image(close_icon)
    tab_box.pack_start(close_button, False, False, 0)
    
    return (tab_box, tab_label, close_button)
```

#### 2. `_update_tab_label(page_widget, filename, is_modified)`

Updates an existing tab label with new filename and modification state.

**Features**:
- Finds label widget in tab box hierarchy
- Updates text to show filename.shy with optional asterisk
- Maintains ellipsization and styling

**Code**:
```python
def _update_tab_label(self, page_widget, filename='default', is_modified=False):
    """Update tab label for a page with new filename and modification state."""
    tab_widget = self.notebook.get_tab_label(page_widget)
    if not tab_widget or not isinstance(tab_widget, Gtk.Box):
        return
    
    # Use 'default.shy' if no filename provided
    if not filename or filename == 'default':
        filename = 'default.shy'
    elif not filename.endswith('.shy'):
        filename = f"{filename}.shy"
    
    # Find the label in the tab box (it's the second child after icon)
    children = tab_widget.get_children()
    if len(children) >= 2:
        label = children[1]  # Index 1 is the label (after icon)
        if isinstance(label, Gtk.Label):
            display_name = f"{filename}{'*' if is_modified else ''}"
            label.set_text(display_name)
```

#### 3. `_on_file_operation_completed(filepath, is_save)`

Handles file save/load operations to update tab label.

**Features**:
- Extracts filename from full path
- Ensures .shy extension is present
- Updates tab label (no asterisk after save/load)
- Updates canvas manager's internal filename (without extension)

**Triggered by**:
- `persistency.on_file_saved` callback
- `persistency.on_file_loaded` callback

**Code**:
```python
def _on_file_operation_completed(self, filepath, is_save=True):
    """Handle file save/load completion to update tab label."""
    if not filepath:
        return
    
    # Extract filename with .shy extension
    filename = os.path.basename(filepath)
    if not filename.endswith('.shy'):
        base = os.path.splitext(filename)[0]
        filename = f"{base}.shy"
    
    # Get current page and update label
    current_page_num = self.notebook.get_current_page()
    if current_page_num < 0:
        return
    
    current_page = self.notebook.get_nth_page(current_page_num)
    self._update_tab_label(current_page, filename, is_modified=False)
    
    # Update canvas manager's filename (without extension)
    drawing_area = self._get_drawing_area_from_page(current_page)
    if drawing_area and drawing_area in self.canvas_managers:
        manager = self.canvas_managers[drawing_area]
        base_filename = os.path.splitext(filename)[0]
        manager.filename = base_filename
```

#### 4. `_on_dirty_state_changed(is_dirty)`

Handles dirty state changes to show/hide modification indicator.

**Features**:
- Adds asterisk (*) when document becomes dirty
- Removes asterisk when document is saved

**Triggered by**:
- `persistency.on_dirty_changed` callback
- User edits (add/remove/modify objects)

**Code**:
```python
def _on_dirty_state_changed(self, is_dirty):
    """Handle dirty state change to update tab label modification indicator."""
    current_page_num = self.notebook.get_current_page()
    if current_page_num < 0:
        return
    
    current_page = self.notebook.get_nth_page(current_page_num)
    drawing_area = self._get_drawing_area_from_page(current_page)
    
    if drawing_area and drawing_area in self.canvas_managers:
        manager = self.canvas_managers[drawing_area]
        base_filename = manager.filename if hasattr(manager, 'filename') else 'default'
        
        # Update tab label with modification indicator (asterisk)
        self._update_tab_label(current_page, base_filename, is_modified=is_dirty)
```

#### 5. `_get_drawing_area_from_page(page_widget)`

Helper to extract drawing area from notebook page widget hierarchy.

**Code**:
```python
def _get_drawing_area_from_page(self, page_widget):
    """Extract drawing area from a notebook page widget."""
    if isinstance(page_widget, Gtk.Overlay):
        scrolled = page_widget.get_child()
        if isinstance(scrolled, Gtk.ScrolledWindow):
            drawing_area = scrolled.get_child()
            if hasattr(drawing_area, 'get_child'):
                drawing_area = drawing_area.get_child()
            return drawing_area
    return None
```

---

## Integration with Persistency Manager

### Modified Method: `set_persistency_manager(persistency)`

Enhanced to wrap persistency callbacks and connect them to tab label updates.

**Callbacks Wrapped**:

1. **`on_file_saved`** → Calls `_on_file_operation_completed(filepath, is_save=True)`
2. **`on_file_loaded`** → Calls `_on_file_operation_completed(filepath, is_save=False)`
3. **`on_dirty_changed`** → Calls `_on_dirty_state_changed(is_dirty)`

**Implementation**:
```python
def set_persistency_manager(self, persistency):
    """Set the persistency manager for file operations integration."""
    self.persistency = persistency
    
    # Connect to persistency callbacks to update tab labels
    if hasattr(persistency, 'on_file_saved'):
        original_on_file_saved = persistency.on_file_saved
        def on_file_saved_wrapper(filepath):
            self._on_file_operation_completed(filepath, is_save=True)
            if original_on_file_saved:
                original_on_file_saved(filepath)
        persistency.on_file_saved = on_file_saved_wrapper
    
    if hasattr(persistency, 'on_file_loaded'):
        original_on_file_loaded = persistency.on_file_loaded
        def on_file_loaded_wrapper(filepath, document):
            self._on_file_operation_completed(filepath, is_save=False)
            if original_on_file_loaded:
                original_on_file_loaded(filepath, document)
        persistency.on_file_loaded = on_file_loaded_wrapper
    
    if hasattr(persistency, 'on_dirty_changed'):
        original_on_dirty_changed = persistency.on_dirty_changed
        def on_dirty_changed_wrapper(is_dirty):
            self._on_dirty_state_changed(is_dirty)
            if original_on_dirty_changed:
                original_on_dirty_changed(is_dirty)
        persistency.on_dirty_changed = on_dirty_changed_wrapper
```

**Pattern**: Decorator pattern to preserve existing callbacks while adding tab label updates

---

## User Interaction Flow

### Scenario 1: New Document

```
User Action                  Tab Label
============                 ===========
App starts                → [📄] default.shy (X)
User adds place          → [📄] default.shy* (X)
User saves as "net1"     → [📄] net1.shy (X)
```

### Scenario 2: Open Existing File

```
User Action                  Tab Label
============                 ===========
User opens "model.shy"   → [📄] model.shy (X)
User adds transition     → [📄] model.shy* (X)
User saves               → [📄] model.shy (X)
```

### Scenario 3: Multiple Tabs

```
Tab 1: [📄] default.shy* (X)
Tab 2: [📄] network1.shy (X)
Tab 3: [📄] complex_system.shy* (X)
```

### Scenario 4: Long Filename

```
Before: very_long_petri_net_model_name.shy
After:  [📄] very_long_petri_n... (X)
                        ↑ ellipsized at 20 chars
```

---

## Benefits

### 1. **Visual Clarity** ✅
- File icon immediately identifies document type
- .shy extension visible at all times
- Asterisk clearly shows unsaved changes

### 2. **User Confidence** ✅
- Always know which file is open
- Never lose track of unsaved changes
- Close button per tab (no need for menu)

### 3. **Professional Look** ✅
- Matches IDE standards (VS Code, Sublime, etc.)
- Consistent with GTK3 design patterns
- Clean, uncluttered appearance

### 4. **Maintainability** ✅
- Centralized tab label creation logic
- Easy to update (change icon, styling, etc.)
- Testable (methods return widgets)

---

## Technical Details

### GTK3 Widgets Used

| Widget | Purpose |
|--------|---------|
| `Gtk.Box` | Container for tab label elements |
| `Gtk.Image` | File type icon (text-x-generic) |
| `Gtk.Label` | Filename display with ellipsization |
| `Gtk.Button` | Close button (X) |

### Icon Names

- **Document icon**: `text-x-generic` (standard GTK stock icon)
- **Close icon**: `window-close-symbolic` (symbolic variant for better theming)

### Ellipsization

- **Mode**: `Pango.EllipsizeMode.END` (value 3)
- **Max chars**: 20 characters
- **Behavior**: "very_long_name.shy" → "very_long_name..."

---

## Testing Scenarios

### Test 1: Default Document

1. Launch Shypn
2. **Expected**: Tab shows `[📄] default.shy (X)`
3. Add a place
4. **Expected**: Tab shows `[📄] default.shy* (X)`

### Test 2: Save As

1. Create document with objects
2. Tab shows: `[📄] default.shy* (X)`
3. File → Save As → "mynet"
4. **Expected**: Tab shows `[📄] mynet.shy (X)` (no asterisk)

### Test 3: Open File

1. File → Open → "testnet.shy"
2. **Expected**: Tab shows `[📄] testnet.shy (X)`
3. Modify document
4. **Expected**: Tab shows `[📄] testnet.shy* (X)`

### Test 4: Multiple Tabs

1. Open 3 documents
2. **Expected**: Each tab shows correct filename
3. Modify tab 2
4. **Expected**: Only tab 2 shows asterisk
5. Save tab 2
6. **Expected**: Tab 2 asterisk disappears

### Test 5: Close Tab

1. Open document
2. Modify (tab shows asterisk)
3. Click (X) button
4. **Expected**: "Unsaved changes" dialog appears
5. Choose "Don't Save"
6. **Expected**: Tab closes

### Test 6: Long Filename

1. Save as "very_long_petri_net_model_name"
2. **Expected**: Tab shows ellipsized name with "..."
3. Hover over tab
4. **Expected**: Tooltip shows full filename (GTK default)

---

## Future Enhancements

### Priority: Medium

1. **Custom Icons by File State**
   - Green dot: Saved, no changes
   - Orange dot: Modified
   - Red dot: Error/invalid

2. **Tooltip on Hover**
   - Show full path to file
   - Show modification timestamp
   - Show object count

3. **Drag & Drop Reordering**
   - Allow user to reorder tabs
   - Persist tab order in workspace state

### Priority: Low

4. **Tab Context Menu**
   - Right-click → Close
   - Right-click → Close Others
   - Right-click → Close All
   - Right-click → Reveal in File Explorer

5. **Color Coding**
   - Different icon colors for different projects
   - Custom colors per document type

---

## Code Locations

### Primary File
- `src/shypn/helpers/model_canvas_loader.py`

### Key Methods
- Lines ~87-120: `_create_tab_label()`
- Lines ~121-145: `_update_tab_label()`
- Lines ~1710-1780: `set_persistency_manager()` with callback wrappers
- Lines ~1750-1775: `_on_file_operation_completed()`
- Lines ~1777-1795: `_on_dirty_state_changed()`
- Lines ~1797-1810: `_get_drawing_area_from_page()`

### Modified Sections
- Lines ~124-129: Updated `load()` to use new tab label creator
- Lines ~275-283: Updated `add_document()` to use new tab label creator

---

## Dependencies

### GTK3 Modules
```python
from gi.repository import Gtk, Gdk
```

### Internal Modules
```python
from shypn.file.netobj_persistency import NetObjPersistency  # For callbacks
from shypn.data.model_canvas_manager import ModelCanvasManager  # For filename
```

---

## Verification Commands

```bash
# Check for syntax errors
python3 -m py_compile src/shypn/helpers/model_canvas_loader.py

# Run application
python3 src/shypn.py

# Check git status
git status --short
```

---

## Conclusion

Successfully implemented professional tab labels with:
- ✅ File type icon
- ✅ Filename with .shy extension  
- ✅ Modification indicator (asterisk)
- ✅ Close button per tab
- ✅ Integration with file operations
- ✅ Automatic updates on save/load/dirty state

The feature enhances user experience by providing clear visual feedback about document state and making file management more intuitive.

**Status**: Ready for commit and user testing! 🚀
