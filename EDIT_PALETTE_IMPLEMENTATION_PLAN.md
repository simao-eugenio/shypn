# Edit Palette Implementation Plan

## Date: October 6, 2025

## Overview

Create a new **floating, overlayed editing palette** that is revealed/hidden by an `[E] Edit` button. This palette will contain editing-specific operations and be completely decoupled from the object creation tools `[P][T][A]` palette.

---

## Goals

1. **Separate Concerns**: Decouple editing operations from object creation
2. **Floating UI**: Revealer-based overlay that doesn't occupy fixed space
3. **Quick Access**: Keyboard shortcuts for power users
4. **Extensible**: Easy to add new editing operations
5. **Clean Architecture**: Separate UI files and code modules

---

## Architecture

### Directory Structure

```
shypn/
├── ui/
│   └── palettes/
│       ├── edit_palette.ui          # NEW: GTK UI definition
│       ├── tools_palette.ui         # EXISTING: [P][T][A] creation tools
│       └── simulation_palette.ui    # EXISTING: Simulation controls
│
├── src/shypn/
│   ├── edit/
│   │   ├── __init__.py
│   │   ├── edit_palette_loader.py   # NEW: Load and manage edit palette
│   │   ├── edit_operations.py       # NEW: Undo/Redo/Lasso operations
│   │   ├── lasso_selector.py        # NEW: Lasso selection logic
│   │   └── transformation/          # EXISTING: Transform handlers
│   │       ├── handle_detector.py
│   │       └── arc_transform_handler.py
│   │
│   └── helpers/
│       ├── model_canvas_loader.py   # MODIFY: Integrate edit palette
│       └── tools_palette_loader.py  # MODIFY: Remove [S] select
│
└── doc/
    └── EDIT_PALETTE_IMPLEMENTATION.md  # This file
```

---

## Component Design

### 1. Edit Palette UI (`ui/palettes/edit_palette.ui`)

**Layout**: Vertical revealer with toolbar buttons

```
┌─────────────────────────┐
│  [E] Edit               │  ← Toggle button (reveals/hides)
├─────────────────────────┤
│  ┌───────────────────┐  │
│  │ Revealer Content  │  │  ← Animated slide-in/out
│  │                   │  │
│  │  [S] Select       │  │
│  │  [U] Undo         │  │
│  │  [R] Redo         │  │
│  │  [L] Lasso        │  │
│  │  ───────────────  │  │
│  │  [D] Duplicate    │  │
│  │  [G] Group        │  │
│  │  [A] Align        │  │
│  │  ───────────────  │  │
│  │  [X] Cut          │  │
│  │  [C] Copy         │  │
│  │  [V] Paste        │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

**Properties**:
- **Position**: Floating overlay (using GtkOverlay or GtkRevealer)
- **Animation**: Slide from right/left edge
- **Default State**: Hidden (revealed by [E] button)
- **Style**: Consistent with existing palettes

**GTK Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <object class="GtkBox" id="edit_palette_root">
    <property name="orientation">vertical</property>
    <property name="spacing">4</property>
    
    <!-- Toggle Button -->
    <child>
      <object class="GtkToggleButton" id="edit_toggle_button">
        <property name="label">[E] Edit</property>
        <property name="tooltip-text">Toggle Edit Palette (E)</property>
      </object>
    </child>
    
    <!-- Revealer -->
    <child>
      <object class="GtkRevealer" id="edit_revealer">
        <property name="reveal-child">false</property>
        <property name="transition-type">slide-down</property>
        
        <child>
          <object class="GtkBox" id="edit_buttons_box">
            <property name="orientation">vertical</property>
            <property name="spacing">2</property>
            
            <!-- Selection Tools -->
            <child>
              <object class="GtkButton" id="btn_select">
                <property name="label">[S] Select</property>
              </object>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_lasso">
                <property name="label">[L] Lasso</property>
              </object>
            </child>
            
            <!-- History Operations -->
            <child>
              <object class="GtkSeparator"/>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_undo">
                <property name="label">[U] Undo</property>
                <property name="sensitive">false</property>
              </object>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_redo">
                <property name="label">[R] Redo</property>
                <property name="sensitive">false</property>
              </object>
            </child>
            
            <!-- Object Operations -->
            <child>
              <object class="GtkSeparator"/>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_duplicate">
                <property name="label">[D] Duplicate</property>
              </object>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_group">
                <property name="label">[G] Group</property>
              </object>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_align">
                <property name="label">[A] Align</property>
              </object>
            </child>
            
            <!-- Clipboard -->
            <child>
              <object class="GtkSeparator"/>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_cut">
                <property name="label">[X] Cut</property>
              </object>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_copy">
                <property name="label">[C] Copy</property>
              </object>
            </child>
            
            <child>
              <object class="GtkButton" id="btn_paste">
                <property name="label">[V] Paste</property>
              </object>
            </child>
            
          </object>
        </child>
      </object>
    </child>
    
  </object>
</interface>
```

---

### 2. Edit Palette Loader (`src/shypn/edit/edit_palette_loader.py`)

**Responsibilities**:
- Load edit_palette.ui file
- Connect button signals to operations
- Manage revealer state (open/close)
- Handle keyboard shortcuts
- Update button states (enabled/disabled)

**Class Design**:

```python
#!/usr/bin/env python3
"""Edit Palette Loader - Manages the floating edit operations palette."""

from gi.repository import Gtk, Gdk
import os


class EditPaletteLoader:
    """Manages the edit operations palette UI and interactions.
    
    The edit palette provides quick access to editing operations:
    - Selection modes (select, lasso)
    - History (undo, redo)
    - Object operations (duplicate, group, align)
    - Clipboard (cut, copy, paste)
    
    The palette is revealed/hidden by clicking the [E] Edit toggle button
    or pressing the 'E' keyboard shortcut.
    """
    
    def __init__(self, parent_window=None):
        """Initialize the edit palette loader.
        
        Args:
            parent_window: Parent GTK window (for modals/dialogs)
        """
        self.parent_window = parent_window
        self.builder = None
        self.revealer = None
        self.toggle_button = None
        self.is_revealed = False
        
        # Button references
        self.btn_select = None
        self.btn_lasso = None
        self.btn_undo = None
        self.btn_redo = None
        self.btn_duplicate = None
        self.btn_group = None
        self.btn_align = None
        self.btn_cut = None
        self.btn_copy = None
        self.btn_paste = None
        
        # Operations manager (will be set later)
        self.edit_operations = None
        
    def load_palette(self):
        """Load the edit palette UI from .ui file.
        
        Returns:
            GtkBox: Root widget of the edit palette
        """
        self.builder = Gtk.Builder()
        ui_path = os.path.join(
            os.path.dirname(__file__), 
            '../../ui/palettes/edit_palette.ui'
        )
        self.builder.add_from_file(ui_path)
        
        # Get widget references
        root = self.builder.get_object('edit_palette_root')
        self.revealer = self.builder.get_object('edit_revealer')
        self.toggle_button = self.builder.get_object('edit_toggle_button')
        
        # Get button references
        self.btn_select = self.builder.get_object('btn_select')
        self.btn_lasso = self.builder.get_object('btn_lasso')
        self.btn_undo = self.builder.get_object('btn_undo')
        self.btn_redo = self.builder.get_object('btn_redo')
        self.btn_duplicate = self.builder.get_object('btn_duplicate')
        self.btn_group = self.builder.get_object('btn_group')
        self.btn_align = self.builder.get_object('btn_align')
        self.btn_cut = self.builder.get_object('btn_cut')
        self.btn_copy = self.builder.get_object('btn_copy')
        self.btn_paste = self.builder.get_object('btn_paste')
        
        # Connect signals
        self._connect_signals()
        
        return root
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Toggle button
        self.toggle_button.connect('toggled', self._on_toggle)
        
        # Selection tools
        self.btn_select.connect('clicked', self._on_select_clicked)
        self.btn_lasso.connect('clicked', self._on_lasso_clicked)
        
        # History
        self.btn_undo.connect('clicked', self._on_undo_clicked)
        self.btn_redo.connect('clicked', self._on_redo_clicked)
        
        # Object operations
        self.btn_duplicate.connect('clicked', self._on_duplicate_clicked)
        self.btn_group.connect('clicked', self._on_group_clicked)
        self.btn_align.connect('clicked', self._on_align_clicked)
        
        # Clipboard
        self.btn_cut.connect('clicked', self._on_cut_clicked)
        self.btn_copy.connect('clicked', self._on_copy_clicked)
        self.btn_paste.connect('clicked', self._on_paste_clicked)
    
    def set_edit_operations(self, edit_operations):
        """Set the edit operations manager.
        
        Args:
            edit_operations: EditOperations instance
        """
        self.edit_operations = edit_operations
    
    def toggle_reveal(self):
        """Toggle the revealer open/closed."""
        self.is_revealed = not self.is_revealed
        self.revealer.set_reveal_child(self.is_revealed)
        self.toggle_button.set_active(self.is_revealed)
    
    def _on_toggle(self, button):
        """Handle toggle button clicked."""
        self.is_revealed = button.get_active()
        self.revealer.set_reveal_child(self.is_revealed)
    
    # Selection Tools
    def _on_select_clicked(self, button):
        """Handle [S] Select clicked."""
        if self.edit_operations:
            self.edit_operations.activate_select_mode()
    
    def _on_lasso_clicked(self, button):
        """Handle [L] Lasso clicked."""
        if self.edit_operations:
            self.edit_operations.activate_lasso_mode()
    
    # History Operations
    def _on_undo_clicked(self, button):
        """Handle [U] Undo clicked."""
        if self.edit_operations:
            self.edit_operations.undo()
    
    def _on_redo_clicked(self, button):
        """Handle [R] Redo clicked."""
        if self.edit_operations:
            self.edit_operations.redo()
    
    # Object Operations
    def _on_duplicate_clicked(self, button):
        """Handle [D] Duplicate clicked."""
        if self.edit_operations:
            self.edit_operations.duplicate_selection()
    
    def _on_group_clicked(self, button):
        """Handle [G] Group clicked."""
        if self.edit_operations:
            self.edit_operations.group_selection()
    
    def _on_align_clicked(self, button):
        """Handle [A] Align clicked."""
        if self.edit_operations:
            self.edit_operations.show_align_dialog()
    
    # Clipboard Operations
    def _on_cut_clicked(self, button):
        """Handle [X] Cut clicked."""
        if self.edit_operations:
            self.edit_operations.cut()
    
    def _on_copy_clicked(self, button):
        """Handle [C] Copy clicked."""
        if self.edit_operations:
            self.edit_operations.copy()
    
    def _on_paste_clicked(self, button):
        """Handle [V] Paste clicked."""
        if self.edit_operations:
            self.edit_operations.paste()
    
    def update_button_states(self, undo_available, redo_available, has_selection):
        """Update enabled/disabled state of buttons.
        
        Args:
            undo_available: bool - Can undo
            redo_available: bool - Can redo
            has_selection: bool - Objects are selected
        """
        self.btn_undo.set_sensitive(undo_available)
        self.btn_redo.set_sensitive(redo_available)
        
        # Selection-dependent operations
        self.btn_duplicate.set_sensitive(has_selection)
        self.btn_group.set_sensitive(has_selection)
        self.btn_align.set_sensitive(has_selection)
        self.btn_cut.set_sensitive(has_selection)
        self.btn_copy.set_sensitive(has_selection)
    
    def handle_key_press(self, event):
        """Handle keyboard shortcuts.
        
        Args:
            event: GdkEventKey
            
        Returns:
            bool: True if handled, False otherwise
        """
        key = event.keyval
        
        # E - Toggle palette
        if key == Gdk.KEY_e or key == Gdk.KEY_E:
            self.toggle_reveal()
            return True
        
        # Only process shortcuts if palette is revealed
        if not self.is_revealed:
            return False
        
        # Selection tools
        if key == Gdk.KEY_s or key == Gdk.KEY_S:
            self._on_select_clicked(None)
            return True
        
        if key == Gdk.KEY_l or key == Gdk.KEY_L:
            self._on_lasso_clicked(None)
            return True
        
        # History
        if key == Gdk.KEY_u or key == Gdk.KEY_U:
            self._on_undo_clicked(None)
            return True
        
        if key == Gdk.KEY_r or key == Gdk.KEY_R:
            self._on_redo_clicked(None)
            return True
        
        # Object operations
        if key == Gdk.KEY_d or key == Gdk.KEY_D:
            self._on_duplicate_clicked(None)
            return True
        
        if key == Gdk.KEY_g or key == Gdk.KEY_G:
            self._on_group_clicked(None)
            return True
        
        if key == Gdk.KEY_a or key == Gdk.KEY_A:
            self._on_align_clicked(None)
            return True
        
        # Clipboard
        if key == Gdk.KEY_x or key == Gdk.KEY_X:
            self._on_cut_clicked(None)
            return True
        
        if key == Gdk.KEY_c or key == Gdk.KEY_C:
            self._on_copy_clicked(None)
            return True
        
        if key == Gdk.KEY_v or key == Gdk.KEY_V:
            self._on_paste_clicked(None)
            return True
        
        return False
```

---

### 3. Edit Operations Manager (`src/shypn/edit/edit_operations.py`)

**Responsibilities**:
- Implement undo/redo functionality
- Manage clipboard operations
- Handle lasso selection
- Coordinate object operations (duplicate, group, align)

**Class Design**:

```python
#!/usr/bin/env python3
"""Edit Operations - Core editing operations (undo, redo, clipboard, etc.)."""


class EditOperations:
    """Manages editing operations for the canvas.
    
    Provides:
    - Undo/Redo history management
    - Clipboard operations (cut, copy, paste)
    - Selection modes (rectangle, lasso)
    - Object operations (duplicate, group, align)
    """
    
    def __init__(self, canvas_manager):
        """Initialize edit operations.
        
        Args:
            canvas_manager: ModelCanvasManager instance
        """
        self.canvas_manager = canvas_manager
        
        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_levels = 50
        
        # Clipboard
        self.clipboard = []
        
        # Selection mode
        self.selection_mode = 'rectangle'  # or 'lasso'
        
        # Lasso selector (created on demand)
        self.lasso_selector = None
    
    # Selection Modes
    def activate_select_mode(self):
        """Activate normal rectangle selection mode."""
        self.selection_mode = 'rectangle'
        # Deactivate any tool
        if self.canvas_manager.is_tool_active():
            self.canvas_manager.set_tool('select')
    
    def activate_lasso_mode(self):
        """Activate lasso selection mode."""
        from shypn.edit.lasso_selector import LassoSelector
        self.selection_mode = 'lasso'
        if not self.lasso_selector:
            self.lasso_selector = LassoSelector(self.canvas_manager)
        # TODO: Implement lasso activation
    
    # History Operations
    def undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            return
        
        operation = self.undo_stack.pop()
        self.redo_stack.append(operation)
        
        # Apply reverse operation
        operation.undo()
        
        # Update button states
        self._update_history_state()
    
    def redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            return
        
        operation = self.redo_stack.pop()
        self.undo_stack.append(operation)
        
        # Apply forward operation
        operation.redo()
        
        # Update button states
        self._update_history_state()
    
    def push_operation(self, operation):
        """Add an operation to the undo stack.
        
        Args:
            operation: Operation instance with undo/redo methods
        """
        self.undo_stack.append(operation)
        self.redo_stack.clear()  # Clear redo when new operation added
        
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)
        
        self._update_history_state()
    
    def can_undo(self):
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if redo is available."""
        return len(self.redo_stack) > 0
    
    def _update_history_state(self):
        """Update UI button states based on history."""
        # TODO: Notify palette loader to update button states
        pass
    
    # Clipboard Operations
    def cut(self):
        """Cut selected objects to clipboard."""
        self.copy()
        # Delete selected objects
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        for obj in selected:
            self.canvas_manager.delete_object(obj)
    
    def copy(self):
        """Copy selected objects to clipboard."""
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        self.clipboard = [self._serialize_object(obj) for obj in selected]
    
    def paste(self):
        """Paste objects from clipboard."""
        if not self.clipboard:
            return
        
        # Paste with offset to avoid exact overlap
        offset_x, offset_y = 20, 20
        
        for obj_data in self.clipboard:
            new_obj = self._deserialize_object(obj_data)
            new_obj.x += offset_x
            new_obj.y += offset_y
            # Add to canvas
            # TODO: Implement object creation from data
    
    def _serialize_object(self, obj):
        """Serialize object to dict for clipboard.
        
        Args:
            obj: PetriNetObject instance
            
        Returns:
            dict: Serialized object data
        """
        # TODO: Implement serialization
        return {'type': type(obj).__name__, 'data': {}}
    
    def _deserialize_object(self, obj_data):
        """Deserialize object from dict.
        
        Args:
            obj_data: dict with object data
            
        Returns:
            PetriNetObject: Recreated object
        """
        # TODO: Implement deserialization
        pass
    
    # Object Operations
    def duplicate_selection(self):
        """Duplicate selected objects."""
        selected = self.canvas_manager.selection_manager.get_selected_objects()
        # TODO: Implement duplication with offset
    
    def group_selection(self):
        """Group selected objects."""
        # TODO: Implement grouping (future feature)
        pass
    
    def show_align_dialog(self):
        """Show alignment dialog for selected objects."""
        # TODO: Implement alignment dialog
        pass
```

---

### 4. Lasso Selector (`src/shypn/edit/lasso_selector.py`)

**Responsibilities**:
- Track lasso path drawing
- Determine objects inside lasso polygon
- Visual feedback during lasso drawing

```python
#!/usr/bin/env python3
"""Lasso Selector - Freeform selection using lasso polygon."""

import math


class LassoSelector:
    """Implements lasso (freeform polygon) selection.
    
    User clicks and drags to draw a freeform path. When released,
    all objects inside the polygon are selected.
    """
    
    def __init__(self, canvas_manager):
        """Initialize lasso selector.
        
        Args:
            canvas_manager: ModelCanvasManager instance
        """
        self.canvas_manager = canvas_manager
        self.points = []  # List of (x, y) points in lasso path
        self.is_active = False
    
    def start_lasso(self, x, y):
        """Start drawing lasso at position.
        
        Args:
            x, y: Starting position (world coordinates)
        """
        self.is_active = True
        self.points = [(x, y)]
    
    def add_point(self, x, y):
        """Add point to lasso path.
        
        Args:
            x, y: Point position (world coordinates)
        """
        if not self.is_active:
            return
        self.points.append((x, y))
    
    def finish_lasso(self):
        """Finish lasso and select objects inside."""
        if not self.is_active or len(self.points) < 3:
            self.is_active = False
            self.points = []
            return
        
        # Close the polygon
        self.points.append(self.points[0])
        
        # Find objects inside polygon
        selected = []
        for obj in self.canvas_manager.get_all_objects():
            if self._is_point_in_polygon(obj.x, obj.y, self.points):
                selected.append(obj)
        
        # Update selection
        self.canvas_manager.selection_manager.clear_selection()
        for obj in selected:
            self.canvas_manager.selection_manager.select(obj, multi=True, manager=self.canvas_manager)
        
        # Reset
        self.is_active = False
        self.points = []
    
    def cancel_lasso(self):
        """Cancel lasso selection."""
        self.is_active = False
        self.points = []
    
    def render_lasso(self, cr):
        """Render lasso path on canvas.
        
        Args:
            cr: Cairo context
        """
        if not self.is_active or len(self.points) < 2:
            return
        
        cr.save()
        
        # Draw lasso path
        cr.set_source_rgba(0.2, 0.6, 1.0, 0.5)  # Blue semi-transparent
        cr.set_line_width(2.0)
        cr.set_dash([5, 5])
        
        cr.move_to(self.points[0][0], self.points[0][1])
        for x, y in self.points[1:]:
            cr.line_to(x, y)
        
        cr.stroke()
        cr.restore()
    
    def _is_point_in_polygon(self, x, y, polygon):
        """Check if point is inside polygon using ray casting.
        
        Args:
            x, y: Point coordinates
            polygon: List of (x, y) tuples defining polygon
            
        Returns:
            bool: True if point is inside polygon
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
```

---

## Integration Plan

### Phase 1: Create UI and Basic Structure

**Tasks**:
1. ✅ Create `ui/palettes/edit_palette.ui`
2. ✅ Create `src/shypn/edit/edit_palette_loader.py`
3. ✅ Create `src/shypn/edit/edit_operations.py`
4. ✅ Create `src/shypn/edit/lasso_selector.py`
5. ✅ Update `src/shypn/edit/__init__.py` with exports

**Expected Outcome**:
- Edit palette UI loads and displays
- Toggle button works (show/hide)
- Buttons are clickable (no-op handlers)

### Phase 2: Integrate with Canvas

**Tasks**:
1. Modify `model_canvas_loader.py` to create edit palette
2. Add edit palette to canvas layout (overlay)
3. Connect keyboard shortcut handler
4. Wire up `EditOperations` to `ModelCanvasManager`

**Code Changes in `model_canvas_loader.py`**:

```python
# In __init__:
from shypn.edit.edit_palette_loader import EditPaletteLoader
from shypn.edit.edit_operations import EditOperations

self.edit_palette_loader = EditPaletteLoader(parent_window=self.parent_window)
self.edit_operations = {}  # per canvas

# In create_drawing_area_with_tools:
# Create edit operations manager
edit_ops = EditOperations(manager)
self.edit_operations[drawing_area] = edit_ops

# Create edit palette
edit_palette = self.edit_palette_loader.load_palette()
edit_palette_loader.set_edit_operations(edit_ops)

# Add to overlay (on top of canvas)
overlay = Gtk.Overlay()
overlay.add(drawing_area)  # Base layer
overlay.add_overlay(edit_palette)  # Floating layer

# Connect keyboard handler
drawing_area.connect('key-press-event', self._on_edit_palette_key_press)

def _on_edit_palette_key_press(self, widget, event):
    return self.edit_palette_loader.handle_key_press(event)
```

### Phase 3: Migrate [S] Select from Tools Palette

**Tasks**:
1. Remove [S] button from `tools_palette.ui`
2. Remove select tool activation from `tools_palette_loader.py`
3. Update [S] handler to use edit palette's select mode
4. Ensure default mode is "select" when no tool active

**Code Changes**:
```python
# tools_palette_loader.py
# Remove:
# - btn_select widget
# - _on_select_clicked handler
# - 'S' key handling

# model_canvas_loader.py
# Update default mode handling:
def _get_current_mode(self, manager):
    if manager.is_tool_active():
        return manager.get_tool()
    else:
        return 'select'  # Default to select mode
```

### Phase 4: Implement Core Operations

**Priority Order**:
1. **[S] Select** - Activate normal selection mode
2. **[L] Lasso** - Freeform selection
3. **[D] Duplicate** - Duplicate selected objects
4. **[C] Copy / [V] Paste** - Clipboard operations
5. **[U] Undo / [R] Redo** - History management
6. **[G] Group** - Grouping (future)
7. **[A] Align** - Alignment tools (future)

### Phase 5: Polish and Test

**Tasks**:
- Add tooltips to all buttons
- Test keyboard shortcuts
- Test revealer animation
- Ensure button states update correctly
- Handle edge cases (empty selection, etc.)
- Add user documentation

---

## Keyboard Shortcuts

### Primary Shortcut
- **E** - Toggle Edit Palette (show/hide)

### When Palette is Revealed
- **S** - Select mode (rectangle selection)
- **L** - Lasso mode (freeform selection)
- **U** - Undo
- **R** - Redo
- **D** - Duplicate selection
- **G** - Group selection
- **A** - Align selection
- **X** - Cut
- **C** - Copy
- **V** - Paste

**Note**: Standard Ctrl+Z/Ctrl+Y for undo/redo should also work.

---

## Visual Design

### Positioning Options

**Option 1: Right Edge Overlay**
```
┌─────────────────────────────────┬──────┐
│                                 │ [E]  │
│       Canvas                    │  ▼   │
│                                 │ [S]  │
│                                 │ [U]  │
│                                 │ [R]  │
│                                 │ [L]  │
│                                 │  ──  │
│                                 │ [D]  │
└─────────────────────────────────┴──────┘
```

**Option 2: Floating Window**
```
┌───────────────────────────────────────┐
│                                       │
│  ┌──────┐    Canvas                  │
│  │ [E]  │                            │
│  │  ▼   │                            │
│  │ [S]  │                            │
│  │ [U]  │                            │
│  │ [R]  │                            │
│  └──────┘                            │
│                                       │
└───────────────────────────────────────┘
```

**Recommendation**: Right edge overlay (consistent with existing palettes)

---

## Future Enhancements

### Additional Operations
- **Rotate** - Rotate selected objects
- **Scale** - Scale selected objects
- **Distribute** - Distribute objects evenly
- **Bring to Front / Send to Back** - Z-order control
- **Lock/Unlock** - Prevent accidental editing
- **Hide/Show** - Temporarily hide objects

### Advanced Features
- **Macro Recording** - Record and replay edit sequences
- **Custom Shortcuts** - User-definable keyboard shortcuts
- **Quick Actions** - Right-click menu shortcuts
- **Batch Operations** - Apply operation to all selected

---

## Testing Strategy

### Unit Tests
- `test_edit_palette_loader.py` - UI loading and button connections
- `test_edit_operations.py` - Undo/redo stack, clipboard
- `test_lasso_selector.py` - Polygon selection algorithm

### Integration Tests
- `test_edit_palette_integration.py` - Full workflow tests
  - Toggle palette
  - Execute operations
  - Keyboard shortcuts
  - Button state updates

### Manual Testing Checklist
- [ ] Edit palette loads without errors
- [ ] Toggle button shows/hides revealer
- [ ] 'E' key toggles palette
- [ ] All buttons are clickable
- [ ] Keyboard shortcuts work
- [ ] Button states update correctly
- [ ] Select mode activates
- [ ] Lasso drawing works
- [ ] Undo/redo functions
- [ ] Clipboard operations work
- [ ] No conflicts with existing shortcuts

---

## Migration Notes

### Breaking Changes
- **[S] Select** moves from tools palette to edit palette
- Users must press **[E]** first to access selection tools
- Or use **E, S** keyboard sequence

### Backward Compatibility
- Existing files load normally
- No changes to file format
- No changes to core editing logic

### User Communication
- Update user manual
- Add tooltip: "Press [E] to open Edit Palette"
- Consider showing edit palette on first launch
- Add "What's New" dialog explaining change

---

## Success Criteria

✅ **Must Have**:
- Edit palette loads and displays correctly
- Toggle button reveals/hides palette
- [S] Select migrated from tools palette
- [E] keyboard shortcut works
- Basic operations functional (Select, Duplicate, Copy/Paste)

✅ **Should Have**:
- Undo/Redo implemented
- Lasso selection working
- Button states update dynamically
- Keyboard shortcuts for all operations

✅ **Nice to Have**:
- Smooth revealer animation
- Visual feedback for active mode
- Tooltips with keyboard hints
- Align and Group operations

---

## Timeline Estimate

### Phase 1: UI & Structure (1-2 days)
- Create UI files
- Create Python modules
- Basic loading and display

### Phase 2: Integration (1 day)
- Wire up to canvas
- Connect keyboard handling
- Position in layout

### Phase 3: Migration (0.5 day)
- Remove [S] from tools palette
- Update default mode logic
- Test selection still works

### Phase 4: Operations (2-3 days)
- Implement Select/Lasso
- Implement Duplicate/Copy/Paste
- Implement Undo/Redo
- Test each operation

### Phase 5: Polish (1 day)
- Add tooltips
- Refine animations
- Handle edge cases
- Final testing

**Total: 5.5-7.5 days** (approximately 1-1.5 weeks)

---

## Conclusion

This implementation plan provides a clean separation between object creation tools ([P][T][A]) and editing operations (select, undo, clipboard, etc.). The floating, revealer-based palette keeps the UI clean while providing quick access to editing features through keyboard shortcuts.

The modular design allows for easy extension with additional editing operations in the future, and the dedicated `src/shypn/edit/` directory provides a clear home for all editing-related code.

**Next Step**: Begin Phase 1 - Create UI and basic structure.
