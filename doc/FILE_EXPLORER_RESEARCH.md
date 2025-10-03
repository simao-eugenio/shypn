# GTK4 File Explorer Research & Implementation Guide

**Date**: October 2, 2025  
**Purpose**: Research and design guide for refactoring the left panel into a full file explorer  
**Target**: Transform `ui/panels/left_panel.ui` into a comprehensive file browser

---

## Current State Analysis

### Existing Left Panel (`ui/panels/left_panel.ui`)

**Current Structure** (73 lines):
```
GtkWindow: left_panel_window
└── GtkBox: left_panel_content
    ├── Header Box
    │   ├── GtkLabel: "File Operations"
    │   ├── GtkButton: new_document_button
    │   └── GtkToggleButton: float_button
    ├── GtkSeparator
    └── GtkListBox: file_operations_list (empty)
```

**Status**: Basic structure, no actual file browsing functionality

### Legacy Implementation (`legacy/shypnpy/interface/shypn.ui`)

**Legacy Structure** (GTK3):
```
Notebook with tabs:
├── Explorer Tab
│   ├── Toolbar (New, Up, Refresh buttons)
│   ├── GtkTreeView: file_browser_view
│   └── GtkEntry: file_new_entry (hidden, for inline creation)
└── Recents Tab
    └── GtkListBox: file_panel_recent_list
```

**Key Features**:
- Tree view for hierarchical file display
- Toolbar with actions (New, Navigate Up, Refresh)
- Inline file creation/rename
- Recent files tab
- Headers clickable for sorting

---

## GTK4 File Explorer Patterns

### Pattern 1: GtkListView + GtkDirectoryList (Modern GTK4)

**Best For**: Modern file browsers with custom rendering  
**GTK Version**: 4.0+  
**Complexity**: Medium-High

**Structure**:
```xml
<object class="GtkScrolledWindow">
  <property name="child">
    <object class="GtkColumnView" id="file_column_view">
      <!-- Columns defined programmatically -->
    </object>
  </property>
</object>
```

**Python Implementation**:
```python
from gi.repository import Gtk, Gio

class FileExplorer:
    def __init__(self):
        # GtkDirectoryList provides file system integration
        self.dir_list = Gtk.DirectoryList.new(
            attributes="standard::*",
            file=Gio.File.new_for_path("/home/user")
        )
        
        # GtkColumnView for multi-column display
        self.column_view = Gtk.ColumnView.new(self.dir_list)
        
        # Add columns
        self._add_name_column()
        self._add_size_column()
        self._add_modified_column()
    
    def _add_name_column(self):
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_name_setup)
        factory.connect("bind", self._on_name_bind)
        
        column = Gtk.ColumnViewColumn.new("Name", factory)
        column.set_expand(True)
        self.column_view.append_column(column)
    
    def _on_name_setup(self, factory, list_item):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image()
        label = Gtk.Label(xalign=0)
        box.append(icon)
        box.append(label)
        list_item.set_child(box)
    
    def _on_name_bind(self, factory, list_item):
        file_info = list_item.get_item()
        box = list_item.get_child()
        icon = box.get_first_child()
        label = icon.get_next_sibling()
        
        # Set icon based on file type
        if file_info.get_file_type() == Gio.FileType.DIRECTORY:
            icon.set_from_icon_name("folder-symbolic")
        else:
            icon.set_from_icon_name("text-x-generic-symbolic")
        
        label.set_text(file_info.get_display_name())
```

**Advantages**:
- ✅ Native GTK4 API
- ✅ Automatic file system monitoring
- ✅ Efficient for large directories
- ✅ Modern list/column views
- ✅ Built-in sorting and filtering

**Disadvantages**:
- ⚠️ More complex setup
- ⚠️ Requires GTK 4.6+ for full features
- ⚠️ More Python code needed

---

### Pattern 2: GtkTreeView (Classic, GTK3 Compatible)

**Best For**: Hierarchical file trees with expand/collapse  
**GTK Version**: 3.0+ (still works in GTK4)  
**Complexity**: Medium

**Structure**:
```xml
<object class="GtkScrolledWindow">
  <property name="child">
    <object class="GtkTreeView" id="file_tree_view">
      <property name="headers-visible">true</property>
      <property name="enable-tree-lines">true</property>
      <property name="show-expanders">true</property>
    </object>
  </property>
</object>
```

**Python Implementation**:
```python
from gi.repository import Gtk, GdkPixbuf, Gio
import os

class FileTreeExplorer:
    def __init__(self):
        # Create tree store: [icon, name, path, is_directory, size, modified]
        self.store = Gtk.TreeStore(
            GdkPixbuf.Pixbuf,  # Icon
            str,               # Display name
            str,               # Full path
            bool,              # Is directory
            str,               # Size (formatted)
            str                # Modified date
        )
        
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_headers_visible(True)
        self.tree_view.set_enable_tree_lines(True)
        
        # Add columns
        self._add_columns()
        
        # Connect signals
        self.tree_view.connect("row-expanded", self._on_row_expanded)
        self.tree_view.connect("row-activated", self._on_row_activated)
    
    def _add_columns(self):
        # Name column with icon
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_text = Gtk.CellRendererText()
        
        column = Gtk.TreeViewColumn("Name")
        column.pack_start(renderer_pixbuf, False)
        column.pack_start(renderer_text, True)
        column.add_attribute(renderer_pixbuf, "pixbuf", 0)
        column.add_attribute(renderer_text, "text", 1)
        column.set_sort_column_id(1)
        column.set_expand(True)
        self.tree_view.append_column(column)
        
        # Size column
        column = Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=4)
        column.set_sort_column_id(4)
        self.tree_view.append_column(column)
        
        # Modified column
        column = Gtk.TreeViewColumn("Modified", Gtk.CellRendererText(), text=5)
        column.set_sort_column_id(5)
        self.tree_view.append_column(column)
    
    def populate_directory(self, path, parent_iter=None):
        """Populate a directory in the tree"""
        try:
            entries = sorted(os.listdir(path))
            
            # Separate directories and files
            dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
            
            # Add directories first
            for dirname in dirs:
                full_path = os.path.join(path, dirname)
                icon = self._get_icon("folder")
                iter = self.store.append(parent_iter, [
                    icon,
                    dirname,
                    full_path,
                    True,
                    "",
                    self._get_modified_time(full_path)
                ])
                # Add dummy child to show expander
                self.store.append(iter, [None, "", "", False, "", ""])
            
            # Add files
            for filename in files:
                full_path = os.path.join(path, filename)
                icon = self._get_icon_for_file(filename)
                size = self._format_size(os.path.getsize(full_path))
                self.store.append(parent_iter, [
                    icon,
                    filename,
                    full_path,
                    False,
                    size,
                    self._get_modified_time(full_path)
                ])
        except PermissionError:
            pass
    
    def _on_row_expanded(self, tree_view, iter, path):
        """Lazy load directory contents when expanded"""
        # Remove dummy child
        child_iter = self.store.iter_children(iter)
        if child_iter and self.store.get_value(child_iter, 1) == "":
            self.store.remove(child_iter)
        
        # Load actual contents
        dir_path = self.store.get_value(iter, 2)
        self.populate_directory(dir_path, iter)
```

**Advantages**:
- ✅ Hierarchical display (tree structure)
- ✅ Familiar API (GTK3 compatible)
- ✅ Lazy loading support
- ✅ Built-in sorting
- ✅ Expandable/collapsible nodes

**Disadvantages**:
- ⚠️ Older API (may be deprecated in future GTK)
- ⚠️ Manual file system monitoring needed
- ⚠️ More code for file info display

---

### Pattern 3: Hybrid Approach (Recommended)

**Best For**: Balancing modern GTK4 with proven patterns  
**Complexity**: Medium

Combine GtkColumnView (modern) with classic file management patterns:

```xml
<object class="GtkBox" orientation="vertical">
  <!-- Breadcrumb/Path Bar -->
  <child>
    <object class="GtkBox" id="path_bar">
      <property name="spacing">6</property>
      <!-- Path buttons added dynamically -->
    </object>
  </child>
  
  <!-- Toolbar -->
  <child>
    <object class="GtkBox" id="toolbar">
      <child>
        <object class="GtkButton" id="go_back_button">
          <property name="icon-name">go-previous-symbolic</property>
        </object>
      </child>
      <child>
        <object class="GtkButton" id="go_forward_button">
          <property name="icon-name">go-next-symbolic</property>
        </object>
      </child>
      <child>
        <object class="GtkButton" id="go_up_button">
          <property name="icon-name">go-up-symbolic</property>
        </object>
      </child>
      <child>
        <object class="GtkButton" id="refresh_button">
          <property name="icon-name">view-refresh-symbolic</property>
        </object>
      </child>
      <child>
        <object class="GtkButton" id="new_folder_button">
          <property name="icon-name">folder-new-symbolic</property>
        </object>
      </child>
    </object>
  </child>
  
  <!-- File View -->
  <child>
    <object class="GtkScrolledWindow">
      <property name="vexpand">true</property>
      <property name="child">
        <object class="GtkColumnView" id="file_column_view">
          <!-- Columns configured programmatically -->
        </object>
      </property>
    </object>
  </child>
  
  <!-- Status Bar -->
  <child>
    <object class="GtkLabel" id="status_label">
      <property name="halign">start</property>
      <property name="margin-start">6</property>
      <property name="margin-bottom">6</property>
      <attributes>
        <attribute name="scale" value="0.9"/>
      </attributes>
    </object>
  </child>
</object>
```

---

## Reference Implementations

### 1. GNOME Files (Nautilus)
- **Language**: C + GTK4
- **Repository**: https://gitlab.gnome.org/GNOME/nautilus
- **Key Features**:
  - Multiple view modes (list, grid, tree)
  - Breadcrumb navigation
  - Search integration
  - File operations (copy, paste, delete)
  - Context menus

**Relevant Files**:
- `src/nautilus-files-view.c` - Main file view
- `src/nautilus-list-view.c` - List view implementation
- `src/nautilus-toolbar.c` - Navigation toolbar

### 2. PyGObject GT
- **Repository**: https://github.com/Taiko2k/GTK4PythonTutorial
- **Relevant Examples**:
  - `file_browser.py` - Basic file browser with GtkTreeView
  - `list_view_example.py` - GtkListView with custom cells

### 3. GTK4 Documentation Examples
- **URL**: https://docs.gtk.org/gtk4/
- **Relevant Classes**:
  - `GtkDirectoryList` - File system model
  - `GtkColumnView` - Modern multi-column view
  - `GtkListView` - Simple list view
  - `GtkFileChooser` - Built-in file chooser (for reference)

### 4. Visual Studio Code File Explorer (for inspiration)
- **Features to emulate**:
  - Compact tree view
  - Inline file creation/rename
  - Context menu on right-click
  - File type icons
  - Collapse/expand folders
  - Breadcrumb navigation

---

## Recommended Architecture for SHYpn

### Design Goals
1. **Modern GTK4** - Use latest APIs where practical
2. **Hierarchical Display** - Show directory structure
3. **File Operations** - New, rename, delete, move
4. **Project Integration** - Open/save Petri net files
5. **Recent Files** - Quick access to recent projects
6. **Search/Filter** - Find files quickly

### Proposed Structure

```
FileExplorerPanel (Python Class)
├── UI Components (GTK4)
│   ├── PathBar (breadcrumb navigation)
│   ├── Toolbar (back, forward, up, refresh, new)
│   ├── FileView (GtkColumnView or GtkTreeView)
│   ├── ContextMenu (right-click actions)
│   └── StatusBar (file count, selected items)
│
├── Data Layer
│   ├── FileSystemModel (directory monitoring)
│   ├── RecentFilesManager (track opened files)
│   └── FileTypeRegistry (icons, handlers)
│
└── Operations
    ├── Navigation (browse, go back/forward/up)
    ├── FileOps (create, rename, delete, move)
    ├── Search (filter by name/type)
    └── Integration (open in app, drag-drop)
```

---

## Implementation Recommendations

### Phase 1: Basic File Browser (Priority: HIGH)
**Goal**: Display directory contents with navigation

**Tasks**:
1. Choose view widget (GtkTreeView recommended for start)
2. Create toolbar with navigation buttons
3. Implement directory loading and display
4. Add breadcrumb/path bar
5. Handle double-click to navigate

**Estimated Complexity**: 2-3 days

### Phase 2: File Operations (Priority: MEDIUM)
**Goal**: Create, rename, delete files/folders

**Tasks**:
1. Context menu on right-click
2. New file/folder dialogs
3. Inline rename functionality
4. Delete with confirmation
5. File system monitoring (auto-refresh)

**Estimated Complexity**: 2-3 days

### Phase 3: Advanced Features (Priority: LOW)
**Goal**: Enhanced user experience

**Tasks**:
1. Recent files tab/section
2. Search/filter functionality
3. File type icons
4. Drag-and-drop support
5. Bookmarks/favorites
6. Multiple selection

**Estimated Complexity**: 3-4 days

---

## Code Examples for Quick Start

### Example 1: Basic File Browser Setup (GtkTreeView)

```python
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib
import os
from datetime import datetime

class FileExplorerPanel:
    def __init__(self, builder, base_path=None):
        self.builder = builder
        self.current_path = base_path or os.path.expanduser("~")
        self.history_back = []
        self.history_forward = []
        
        # Get UI elements
        self.container = builder.get_object("file_explorer_container")
        
        # Create components
        self._create_toolbar()
        self._create_file_view()
        self._create_status_bar()
        
        # Load initial directory
        self.navigate_to(self.current_path)
    
    def _create_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        
        # Back button
        self.back_button = Gtk.Button(icon_name="go-previous-symbolic")
        self.back_button.set_tooltip_text("Go back")
        self.back_button.connect("clicked", self._on_back_clicked)
        self.back_button.set_sensitive(False)
        toolbar.append(self.back_button)
        
        # Forward button
        self.forward_button = Gtk.Button(icon_name="go-next-symbolic")
        self.forward_button.set_tooltip_text("Go forward")
        self.forward_button.connect("clicked", self._on_forward_clicked)
        self.forward_button.set_sensitive(False)
        toolbar.append(self.forward_button)
        
        # Up button
        up_button = Gtk.Button(icon_name="go-up-symbolic")
        up_button.set_tooltip_text("Go to parent directory")
        up_button.connect("clicked", self._on_up_clicked)
        toolbar.append(up_button)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(sep)
        
        # Refresh button
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        toolbar.append(refresh_button)
        
        # New folder button
        new_folder_button = Gtk.Button(icon_name="folder-new-symbolic")
        new_folder_button.set_tooltip_text("New folder")
        new_folder_button.connect("clicked", self._on_new_folder_clicked)
        toolbar.append(new_folder_button)
        
        self.container.append(toolbar)
    
    def _create_file_view(self):
        # Create tree store
        # Columns: icon_name(str), name(str), path(str), is_dir(bool), size(str), modified(str)
        self.store = Gtk.TreeStore(str, str, str, bool, str, str)
        
        # Create tree view
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_headers_visible(True)
        self.tree_view.set_enable_tree_lines(True)
        
        # Name column (with icon)
        name_column = Gtk.TreeViewColumn("Name")
        
        icon_renderer = Gtk.CellRendererPixbuf()
        name_column.pack_start(icon_renderer, False)
        name_column.add_attribute(icon_renderer, "icon-name", 0)
        
        text_renderer = Gtk.CellRendererText()
        name_column.pack_start(text_renderer, True)
        name_column.add_attribute(text_renderer, "text", 1)
        name_column.set_expand(True)
        name_column.set_sort_column_id(1)
        
        self.tree_view.append_column(name_column)
        
        # Size column
        size_column = Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=4)
        size_column.set_sort_column_id(4)
        self.tree_view.append_column(size_column)
        
        # Modified column
        modified_column = Gtk.TreeViewColumn("Modified", Gtk.CellRendererText(), text=5)
        modified_column.set_sort_column_id(5)
        self.tree_view.append_column(modified_column)
        
        # Connect signals
        self.tree_view.connect("row-activated", self._on_row_activated)
        
        # Wrap in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.tree_view)
        
        self.container.append(scrolled)
    
    def _create_status_bar(self):
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_margin_start(6)
        self.status_label.set_margin_bottom(6)
        
        self.container.append(self.status_label)
    
    def navigate_to(self, path):
        """Navigate to a directory"""
        if not os.path.isdir(path):
            return
        
        # Update history
        if self.current_path and self.current_path != path:
            self.history_back.append(self.current_path)
            self.history_forward.clear()
            self.back_button.set_sensitive(True)
            self.forward_button.set_sensitive(False)
        
        self.current_path = path
        self._load_directory()
    
    def _load_directory(self):
        """Load directory contents into tree view"""
        self.store.clear()
        
        try:
            entries = os.listdir(self.current_path)
            
            # Separate dirs and files
            dirs = []
            files = []
            
            for entry in entries:
                full_path = os.path.join(self.current_path, entry)
                if os.path.isdir(full_path):
                    dirs.append(entry)
                else:
                    files.append(entry)
            
            # Sort
            dirs.sort(key=str.lower)
            files.sort(key=str.lower)
            
            # Add directories
            for dirname in dirs:
                full_path = os.path.join(self.current_path, dirname)
                self.store.append(None, [
                    "folder-symbolic",
                    dirname,
                    full_path,
                    True,
                    "",
                    self._get_modified_time(full_path)
                ])
            
            # Add files
            for filename in files:
                full_path = os.path.join(self.current_path, filename)
                icon = self._get_file_icon(filename)
                size = self._format_size(os.path.getsize(full_path))
                self.store.append(None, [
                    icon,
                    filename,
                    full_path,
                    False,
                    size,
                    self._get_modified_time(full_path)
                ])
            
            # Update status
            total = len(dirs) + len(files)
            self.status_label.set_text(f"{len(dirs)} folders, {len(files)} files")
            
        except PermissionError:
            self.status_label.set_text("Permission denied")
    
    def _get_file_icon(self, filename):
        """Get icon name based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        icon_map = {
            '.json': 'text-x-generic-symbolic',
            '.py': 'text-x-python-symbolic',
            '.txt': 'text-x-generic-symbolic',
            '.pdf': 'x-office-document-symbolic',
            '.png': 'image-x-generic-symbolic',
            '.jpg': 'image-x-generic-symbolic',
            '.jpeg': 'image-x-generic-symbolic',
        }
        
        return icon_map.get(ext, 'text-x-generic-symbolic')
    
    def _format_size(self, size):
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _get_modified_time(self, path):
        """Get formatted modification time"""
        try:
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return ""
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click on row"""
        iter = self.store.get_iter(path)
        is_dir = self.store.get_value(iter, 3)
        full_path = self.store.get_value(iter, 2)
        
        if is_dir:
            self.navigate_to(full_path)
        else:
            # Open file in application
            print(f"Open file: {full_path}")
    
    def _on_back_clicked(self, button):
        if self.history_back:
            self.history_forward.append(self.current_path)
            path = self.history_back.pop()
            self.current_path = path
            self._load_directory()
            
            self.forward_button.set_sensitive(True)
            self.back_button.set_sensitive(len(self.history_back) > 0)
    
    def _on_forward_clicked(self, button):
        if self.history_forward:
            self.history_back.append(self.current_path)
            path = self.history_forward.pop()
            self.current_path = path
            self._load_directory()
            
            self.back_button.set_sensitive(True)
            self.forward_button.set_sensitive(len(self.history_forward) > 0)
    
    def _on_up_clicked(self, button):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.navigate_to(parent)
    
    def _on_refresh_clicked(self, button):
        self._load_directory()
    
    def _on_new_folder_clicked(self, button):
        # Show dialog for new folder name
        print("Create new folder")
```

### Example 2: UI File Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- GTK4 File Explorer Panel -->
<interface>
  <requires lib="gtk" version="4.0"/>

  <object class="GtkWindow" id="file_explorer_window">
    <property name="title">File Explorer</property>
    <property name="default-width">300</property>
    <property name="default-height">500</property>
    
    <child>
      <object class="GtkBox" id="file_explorer_container">
        <property name="orientation">vertical</property>
        <property name="spacing">0</property>
        
        <!-- Components will be added programmatically:
             - Toolbar
             - File view (TreeView or ColumnView)
             - Status bar
        -->
        
      </object>
    </child>
  </object>
</interface>
```

---

## Decision Matrix

| Criteria | GtkTreeView | GtkColumnView | Hybrid |
|----------|-------------|---------------|--------|
| **GTK4 Native** | ⚠️ Legacy | ✅ Yes | ✅ Yes |
| **Hierarchical** | ✅ Native | ⚠️ Manual | ✅ Yes |
| **Learning Curve** | Low | High | Medium |
| **Future-proof** | ⚠️ No | ✅ Yes | ✅ Yes |
| **Code Complexity** | Medium | High | Medium-High |
| **File Monitoring** | Manual | ✅ Built-in | ✅ Built-in |
| **Performance** | Good | ✅ Excellent | ✅ Excellent |
| **Recommendation** | **Good for Phase 1** | Better for Phase 2 | **Best overall** |

---

## Next Steps

### For Today's Session:
1. ✅ Review this research document
2. Choose implementation pattern (recommend: GtkTreeView for Phase 1)
3. Create UI file structure
4. Implement basic file browser class
5. Test with sample directory

### For Future Sessions:
1. Add file operations (create, delete, rename)
2. Implement context menus
3. Add recent files functionality
4. Integrate with main application
5. Add search/filter capabilities

---

## References & Resources

### Documentation
- **GTK4 Documentation**: https://docs.gtk.org/gtk4/
- **GtkTreeView Guide**: https://docs.gtk.org/gtk4/class.TreeView.html
- **GtkColumnView Guide**: https://docs.gtk.org/gtk4/class.ColumnView.html
- **GtkDirectoryList**: https://docs.gtk.org/gtk4/class.DirectoryList.html

### Tutorials
- **PyGObject Tutorial**: https://pygobject.readthedocs.io/
- **GTK4 Python Examples**: https://github.com/Taiko2k/GTK4PythonTutorial

### Inspiration
- **GNOME Files**: https://gitlab.gnome.org/GNOME/nautilus
- **Thunar (XFCE)**: https://gitlab.xfce.org/xfce/thunar
- **VS Code Explorer**: https://github.com/microsoft/vscode

---

**Status**: Research Complete ✅  
**Ready for Implementation**: Yes  
**Recommended Approach**: Start with GtkTreeView (Pattern 2), migrate to Hybrid (Pattern 3) later
