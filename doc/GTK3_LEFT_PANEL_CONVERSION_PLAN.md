# GTK3 Left Panel (File Explorer) Conversion Plan

## Status: Skeleton converted ✅ | Content needs conversion ❌

The dockable architecture is working in GTK3, but the **internal content** of the left panel (File Explorer) still needs conversion.

---

## 🎯 Current State Analysis

### What Works (Skeleton)
- ✅ Panel window loads
- ✅ Panel can attach/detach
- ✅ Panel shows/hides via toggle button
- ✅ Basic container structure exists

### What's Missing/Broken (Content)
- ❌ TreeView for file browsing doesn't exist in UI
- ❌ Event handlers use GTK4 EventControllers
- ❌ Context menu uses Window+ListBox (workaround), not proper Gtk.Menu
- ❌ File operations not functional

---

## 📋 Conversion Tasks

### **Task 1: Add TreeView to left_panel.ui**

**Current State:**
```xml
<child>
  <object class="GtkListBox" id="file_operations_list">
    <property name="vexpand">True</property>
    <property name="selection-mode">none</property>
    <!-- File operation items will be added programmatically -->
  </object>
</child>
```

**Target State (GTK3):**
```xml
<child>
  <object class="GtkScrolledWindow" id="file_browser_scroll">
    <property name="visible">True</property>
    <property name="hexpand">True</property>
    <property name="vexpand">True</property>
    <property name="hscrollbar-policy">automatic</property>
    <property name="vscrollbar-policy">automatic</property>
    <child>
      <object class="GtkTreeView" id="file_browser_tree">
        <property name="visible">True</property>
        <property name="headers-visible">False</property>
        <property name="enable-tree-lines">True</property>
        <property name="show-expanders">True</property>
        <property name="enable-search">True</property>
        <property name="search-column">0</property>
      </object>
    </child>
  </object>
</child>
```

**What This Adds:**
- Hierarchical tree view for folders/files
- Scroll bars for navigation
- Expanders for folder collapse/expand
- Search functionality

---

### **Task 2: Convert Event Handlers (GTK4 → GTK3)**

**File:** `src/shypn/ui/panels/file_explorer_panel.py`

#### 2.1 Right-Click Context Menu (Lines ~335-340)

**Current (GTK4):**
```python
# Approach 1: GestureClick on TreeView
gesture_click = Gtk.GestureClick.new()
gesture_click.set_button(3)  # Right mouse button
gesture_click.connect('pressed', self._on_tree_view_right_click)
self.tree_view.add_controller(gesture_click)
```

**Target (GTK3):**
```python
# GTK3: Direct button-press-event signal
self.tree_view.connect('button-press-event', self._on_tree_view_button_press)

def _on_tree_view_button_press(self, widget, event):
    """Handle button press on TreeView (GTK3)."""
    if event.button == 3:  # Right-click
        # Get path at cursor position
        path_info = widget.get_path_at_pos(int(event.x), int(event.y))
        if path_info:
            path, column, cell_x, cell_y = path_info
            widget.set_cursor(path)  # Select the row
            self._show_context_menu(event)
        return True
    return False
```

#### 2.2 Keyboard Events (Lines ~350-352)

**Current (GTK4):**
```python
key_controller = Gtk.EventControllerKey.new()
key_controller.connect('key-pressed', self._on_tree_view_key_pressed)
self.tree_view.add_controller(key_controller)
```

**Target (GTK3):**
```python
# GTK3: Direct key-press-event signal
self.tree_view.connect('key-press-event', self._on_tree_view_key_press)

def _on_tree_view_key_press(self, widget, event):
    """Handle key press on TreeView (GTK3)."""
    if event.keyval == Gdk.KEY_Return:
        # Enter key - open selected item
        selection = widget.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            self._on_row_activated(widget, model.get_path(tree_iter), None)
        return True
    elif event.keyval == Gdk.KEY_Delete:
        # Delete key - delete selected item
        self._on_delete_clicked()
        return True
    return False
```

#### 2.3 Outside Click Detection (Lines ~355-359)

**Current (GTK4):**
```python
outside_click = Gtk.GestureClick.new()
outside_click.set_button(1)  # Left click
outside_click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
outside_click.connect('pressed', self._on_outside_click)
self.scrolled_window.add_controller(outside_click)
```

**Target (GTK3):**
```python
# GTK3: button-press-event with focus tracking
self.scrolled_window.connect('button-press-event', self._on_scrolled_window_click)

def _on_scrolled_window_click(self, widget, event):
    """Handle clicks in scrolled window area (GTK3)."""
    if event.button == 1:  # Left click
        # Check if click was outside TreeView bounds
        # Used to dismiss context menu if open
        if self.context_menu and self.context_menu.get_visible():
            self.context_menu.hide()
    return False
```

---

### **Task 3: Convert Context Menu (Window+ListBox → Gtk.Menu)**

**This is THE CRITICAL TASK!** The whole reason we're converting to GTK3 is that GTK4 popovers don't dismiss properly.

**File:** `src/shypn/ui/panels/file_explorer_panel.py` Lines ~182-254

#### Current Approach (Workaround):
```python
def _setup_context_menu(self):
    """Setup context menu as simple floating window with ListBox."""
    self.context_menu = Gtk.Window()
    self.context_menu.set_decorated(False)
    self.context_menu.set_resizable(False)
    self.context_menu.set_modal(False)
    
    listbox = Gtk.ListBox()
    # ... add items ...
    self.context_menu.add(listbox)
```

#### Target Approach (GTK3 Gtk.Menu):
```python
def _setup_context_menu(self):
    """Setup context menu using GTK3 Gtk.Menu."""
    self.context_menu = Gtk.Menu()
    
    # Add menu items
    menu_items = [
        ("Open", self._on_open_clicked),
        ("New Folder", self._on_new_folder_clicked),
        (None, None),  # Separator
        ("Cut", self._on_cut_clicked),
        ("Copy", self._on_copy_clicked),
        ("Paste", self._on_paste_clicked),
        ("Duplicate", self._on_duplicate_clicked),
        (None, None),  # Separator
        ("Rename", self._on_rename_clicked),
        ("Delete", self._on_delete_clicked),
        (None, None),  # Separator
        ("Refresh", self._on_refresh_clicked),
        ("Properties", self._on_properties_clicked),
    ]
    
    for label, callback in menu_items:
        if label is None:
            # Add separator
            item = Gtk.SeparatorMenuItem()
        else:
            item = Gtk.MenuItem(label=label)
            if callback:
                item.connect('activate', lambda w, cb=callback: cb())
        
        item.show()
        self.context_menu.append(item)
    
    print("✓ Context menu configured (GTK3 Gtk.Menu)")

def _show_context_menu(self, event):
    """Show context menu at mouse position (GTK3)."""
    self.context_menu.popup_at_pointer(event)
    # Or for older GTK3: self.context_menu.popup(None, None, None, None, event.button, event.time)
```

**Expected Behavior:**
- ✅ Menu appears on right-click
- ✅ **Menu dismisses on Escape key** (GTK3 handles this automatically!)
- ✅ **Menu dismisses on click outside** (GTK3 handles this automatically!)
- ✅ Menu dismisses after selecting an action

**This is what we couldn't achieve in GTK4!**

---

### **Task 4: Audit for Remaining GTK4 Patterns**

Search file_explorer_panel.py for:

#### Patterns to Find and Fix:

| GTK4 Pattern | GTK3 Replacement | Status |
|--------------|------------------|--------|
| `widget.add_css_class()` | `widget.get_style_context().add_class()` | ✅ Done |
| `widget.remove_css_class()` | `widget.get_style_context().remove_class()` | ✅ Done |
| `listbox.append(row)` | `listbox.add(row)` | ✅ Done |
| `row.set_child(widget)` | `row.add(widget)` | ✅ Done |
| `window.set_child(widget)` | `window.add(widget)` | ✅ Done |
| `css_provider.load_from_string()` | `css_provider.load_from_data(css.encode())` | ✅ Done |
| `Gtk.EventControllerKey` | `widget.connect('key-press-event')` | ❌ TODO |
| `Gtk.GestureClick` | `widget.connect('button-press-event')` | ❌ TODO |
| `widget.add_controller()` | Remove (use connect instead) | ❌ TODO |

---

### **Task 5: Testing Checklist**

After conversion, test these scenarios:

#### Basic TreeView:
- [ ] TreeView displays in the panel
- [ ] Files and folders are visible
- [ ] Icons appear next to items
- [ ] Folders can be expanded/collapsed
- [ ] Double-click opens files (triggers row-activated)

#### Context Menu (THE CRITICAL TEST):
- [ ] Right-click on file shows context menu
- [ ] Right-click on folder shows context menu  
- [ ] **Escape key dismisses menu** ← Main test!
- [ ] **Click outside dismisses menu** ← Main test!
- [ ] Selecting action dismisses menu
- [ ] Menu appears at cursor position

#### File Operations:
- [ ] Open action works
- [ ] New Folder creates folder
- [ ] Cut/Copy/Paste work
- [ ] Duplicate creates copy
- [ ] Rename shows dialog
- [ ] Delete removes item
- [ ] Refresh reloads tree
- [ ] Properties shows dialog

---

## 🔧 Implementation Order

1. **Start with Task 1** (Add TreeView to UI) - Foundation
2. **Then Task 2** (Convert event handlers) - Make it interactive
3. **Then Task 3** (Convert to Gtk.Menu) - THE GOAL: fix dismiss!
4. **Then Task 4** (Audit for GTK4 patterns) - Clean up
5. **Finally Task 5** (Test everything) - Verify success

---

## 🎯 Success Criteria

The conversion is successful when:

1. ✅ TreeView displays file hierarchy
2. ✅ Right-click shows context menu
3. ✅ **Context menu dismisses with Escape key**
4. ✅ **Context menu dismisses with click outside**
5. ✅ All file operations work
6. ✅ No GTK4 APIs remain in code

**The dismissal behavior is THE primary goal** - this was impossible in GTK4 on WSL+Wayland!

---

## 📝 Notes

- Keep the existing FileExplorer API (business logic) unchanged
- Only convert the UI layer (GTK bindings)
- TreeView is already a GTK3 widget, so it should work well
- Gtk.Menu in GTK3 is mature and reliable (10+ years)
- Test on WSL2+WSLg to verify the dismiss issue is fixed

