# File Explorer Quick Start Guide

**For immediate implementation when ready**

---

## Checklist Before Starting

- [x] Research completed
- [x] Roadmap defined
- [x] Patterns chosen
- [ ] Ready to code!

---

## Quick Command Reference

### 1. Create New Files
```bash
# Create UI file
touch ui/panels/file_explorer_panel.ui

# Create Python class
touch ui/panels/file_explorer.py

# Create test file
touch tests/test_file_explorer.py
```

### 2. Backup Current Panel
```bash
cd /home/simao/projetos/shypn
cp ui/panels/left_panel.ui ui/panels/left_panel.ui.backup
```

### 3. Test the Implementation
```bash
# Run test script (create this)
python3 scripts/test_file_explorer.py

# Or run main app
python3 src/shypn.py
```

---

## Minimal Working Example (Copy-Paste Ready)

### File: `ui/panels/file_explorer_panel.ui`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- GTK4 File Explorer Panel - Minimal Version -->
<interface>
  <requires lib="gtk" version="4.0"/>

  <object class="GtkWindow" id="file_explorer_window">
    <property name="title">File Explorer</property>
    <property name="default-width">300</property>
    <property name="default-height">500</property>
    
    <child>
      <object class="GtkBox" id="main_container">
        <property name="orientation">vertical</property>
        <property name="spacing">0</property>
        
        <!-- Toolbar will be added programmatically -->
        
        <!-- File view container -->
        <child>
          <object class="GtkScrolledWindow" id="file_view_scroll">
            <property name="vexpand">true</property>
            <!-- TreeView will be added programmatically -->
          </object>
        </child>
        
        <!-- Status bar -->
        <child>
          <object class="GtkLabel" id="status_label">
            <property name="halign">start</property>
            <property name="margin-start">6</property>
            <property name="margin-bottom">6</property>
            <property name="label">Ready</property>
            <attributes>
              <attribute name="scale" value="0.9"/>
            </attributes>
          </object>
        </child>
        
      </object>
    </child>
  </object>
</interface>
```

### File: `ui/panels/file_explorer.py`

```python
#!/usr/bin/env python3
"""
File Explorer Panel for SHYpn
GTK4 file browser with navigation and file operations
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os
from datetime import datetime

class FileExplorerPanel:
    """File explorer panel with tree view"""
    
    def __init__(self, ui_file=None, base_path=None):
        """Initialize file explorer
        
        Args:
            ui_file: Path to UI file (optional)
            base_path: Starting directory (default: home)
        """
        # Set initial path
        self.current_path = base_path or os.path.expanduser("~")
        self.history_back = []
        self.history_forward = []
        
        # Load UI if provided
        if ui_file:
            self.builder = Gtk.Builder()
            self.builder.add_from_file(ui_file)
            self.window = self.builder.get_object("file_explorer_window")
            self.main_container = self.builder.get_object("main_container")
            self.file_view_scroll = self.builder.get_object("file_view_scroll")
            self.status_label = self.builder.get_object("status_label")
        else:
            # Create manually if no UI file
            self._create_ui()
        
        # Create components
        self._create_toolbar()
        self._create_tree_view()
        
        # Load initial directory
        self.navigate_to(self.current_path)
    
    def _create_ui(self):
        """Create UI manually (fallback)"""
        self.window = Gtk.Window()
        self.window.set_title("File Explorer")
        self.window.set_default_size(300, 500)
        
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.set_child(self.main_container)
        
        self.file_view_scroll = Gtk.ScrolledWindow()
        self.file_view_scroll.set_vexpand(True)
        self.main_container.append(self.file_view_scroll)
        
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_margin_start(6)
        self.status_label.set_margin_bottom(6)
        self.main_container.append(self.status_label)
    
    def _create_toolbar(self):
        """Create navigation toolbar"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        
        # Back button
        self.back_btn = Gtk.Button(icon_name="go-previous-symbolic")
        self.back_btn.set_tooltip_text("Go back")
        self.back_btn.connect("clicked", lambda b: self.go_back())
        self.back_btn.set_sensitive(False)
        toolbar.append(self.back_btn)
        
        # Forward button
        self.forward_btn = Gtk.Button(icon_name="go-next-symbolic")
        self.forward_btn.set_tooltip_text("Go forward")
        self.forward_btn.connect("clicked", lambda b: self.go_forward())
        self.forward_btn.set_sensitive(False)
        toolbar.append(self.forward_btn)
        
        # Up button
        up_btn = Gtk.Button(icon_name="go-up-symbolic")
        up_btn.set_tooltip_text("Go to parent directory")
        up_btn.connect("clicked", lambda b: self.go_up())
        toolbar.append(up_btn)
        
        # Home button
        home_btn = Gtk.Button(icon_name="go-home-symbolic")
        home_btn.set_tooltip_text("Go to home directory")
        home_btn.connect("clicked", lambda b: self.navigate_to(os.path.expanduser("~")))
        toolbar.append(home_btn)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Refresh button
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Refresh")
        refresh_btn.connect("clicked", lambda b: self.refresh())
        toolbar.append(refresh_btn)
        
        # Insert at top of container
        self.main_container.prepend(toolbar)
    
    def _create_tree_view(self):
        """Create tree view for files"""
        # Create store: icon(str), name(str), path(str), is_dir(bool), size(str), modified(str)
        self.store = Gtk.ListStore(str, str, str, bool, str, str)
        
        # Create tree view
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_headers_visible(True)
        
        # Name column (icon + text)
        name_col = Gtk.TreeViewColumn("Name")
        
        icon_renderer = Gtk.CellRendererPixbuf()
        name_col.pack_start(icon_renderer, False)
        name_col.add_attribute(icon_renderer, "icon-name", 0)
        
        text_renderer = Gtk.CellRendererText()
        name_col.pack_start(text_renderer, True)
        name_col.add_attribute(text_renderer, "text", 1)
        name_col.set_expand(True)
        name_col.set_sort_column_id(1)
        
        self.tree_view.append_column(name_col)
        
        # Size column
        size_col = Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=4)
        size_col.set_sort_column_id(4)
        self.tree_view.append_column(size_col)
        
        # Modified column
        mod_col = Gtk.TreeViewColumn("Modified", Gtk.CellRendererText(), text=5)
        mod_col.set_sort_column_id(5)
        self.tree_view.append_column(mod_col)
        
        # Connect signals
        self.tree_view.connect("row-activated", self._on_row_activated)
        
        # Add to scrolled window
        self.file_view_scroll.set_child(self.tree_view)
    
    def navigate_to(self, path):
        """Navigate to directory"""
        if not os.path.isdir(path):
            return
        
        # Update history
        if self.current_path and self.current_path != path:
            self.history_back.append(self.current_path)
            self.history_forward.clear()
            self.back_btn.set_sensitive(True)
            self.forward_btn.set_sensitive(False)
        
        self.current_path = path
        self._load_directory()
    
    def _load_directory(self):
        """Load directory contents"""
        self.store.clear()
        
        try:
            entries = os.listdir(self.current_path)
            
            dirs = []
            files = []
            
            for entry in entries:
                if entry.startswith('.'):  # Skip hidden
                    continue
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
                self.store.append([
                    "folder-symbolic",
                    dirname,
                    full_path,
                    True,
                    "",
                    self._get_mod_time(full_path)
                ])
            
            # Add files
            for filename in files:
                full_path = os.path.join(self.current_path, filename)
                icon = self._get_file_icon(filename)
                size = self._format_size(os.path.getsize(full_path))
                self.store.append([
                    icon,
                    filename,
                    full_path,
                    False,
                    size,
                    self._get_mod_time(full_path)
                ])
            
            # Update status
            self.status_label.set_text(f"{len(dirs)} folders, {len(files)} files | {self.current_path}")
            
        except PermissionError:
            self.status_label.set_text("Permission denied")
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click"""
        iter = self.store.get_iter(path)
        is_dir = self.store[iter][3]
        full_path = self.store[iter][2]
        
        if is_dir:
            self.navigate_to(full_path)
        else:
            print(f"Open file: {full_path}")
    
    def go_back(self):
        """Go to previous directory"""
        if self.history_back:
            self.history_forward.append(self.current_path)
            path = self.history_back.pop()
            self.current_path = path
            self._load_directory()
            
            self.forward_btn.set_sensitive(True)
            self.back_btn.set_sensitive(len(self.history_back) > 0)
    
    def go_forward(self):
        """Go to next directory in history"""
        if self.history_forward:
            self.history_back.append(self.current_path)
            path = self.history_forward.pop()
            self.current_path = path
            self._load_directory()
            
            self.back_btn.set_sensitive(True)
            self.forward_btn.set_sensitive(len(self.history_forward) > 0)
    
    def go_up(self):
        """Go to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.navigate_to(parent)
    
    def refresh(self):
        """Refresh current directory"""
        self._load_directory()
    
    def _get_file_icon(self, filename):
        """Get icon for file"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.json': 'text-x-generic-symbolic',
            '.pn': 'text-x-generic-symbolic',
            '.py': 'text-x-python-symbolic',
            '.txt': 'text-x-generic-symbolic',
            '.md': 'text-x-generic-symbolic',
        }
        return icons.get(ext, 'text-x-generic-symbolic')
    
    def _format_size(self, size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.0f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _get_mod_time(self, path):
        """Get modification time"""
        try:
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return ""
    
    def show(self):
        """Show window"""
        self.window.present()


def main():
    """Test the file explorer"""
    app = Gtk.Application(application_id="dev.shypn.file_explorer_test")
    
    def on_activate(app):
        explorer = FileExplorerPanel()
        explorer.window.set_application(app)
        explorer.show()
    
    app.connect("activate", on_activate)
    app.run(None)


if __name__ == "__main__":
    main()
```

### File: `scripts/test_file_explorer.py`

```python
#!/usr/bin/env python3
"""Test script for file explorer"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.panels.file_explorer import FileExplorerPanel
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

def main():
    print("File Explorer Test")
    print("=" * 50)
    
    app = Gtk.Application(application_id="dev.shypn.file_explorer_test")
    
    def on_activate(app):
        # Create explorer starting at project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        explorer = FileExplorerPanel(base_path=project_root)
        explorer.window.set_application(app)
        explorer.show()
        
        print(f"✓ File explorer started")
        print(f"✓ Current path: {explorer.current_path}")
    
    app.connect("activate", on_activate)
    return app.run(None)

if __name__ == "__main__":
    sys.exit(main())
```

---

## Implementation Steps (Copy This Order)

### Step 1: Create Files
```bash
cd /home/simao/projetos/shypn

# Create Python class
cat > ui/panels/file_explorer.py << 'EOF'
[Paste the file_explorer.py code from above]
EOF

# Create test script
cat > scripts/test_file_explorer.py << 'EOF'
[Paste the test_file_explorer.py code from above]
EOF

# Make test executable
chmod +x scripts/test_file_explorer.py
```

### Step 2: Test It
```bash
# Run the test
python3 scripts/test_file_explorer.py
```

### Step 3: Verify Features
- [ ] Window opens
- [ ] Shows folders and files
- [ ] Can navigate by double-clicking folders
- [ ] Back/Forward/Up buttons work
- [ ] Status bar shows file count

### Step 4: Integrate with Main App
Once working standalone, integrate into main application:
1. Import in main window
2. Replace left_panel with file_explorer
3. Connect signals for file opening
4. Add to dock/undock system

---

## Troubleshooting

### Issue: "Module not found"
```bash
# Make sure you're in project root
cd /home/simao/projetos/shypn

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Issue: "UI file not found"
```bash
# Use absolute path
import os
UI_FILE = os.path.join(os.path.dirname(__file__), 'file_explorer_panel.ui')
```

### Issue: "No icons showing"
```bash
# Check GTK theme
gsettings get org.gnome.desktop.interface icon-theme

# Test icon names
python3 -c "from gi.repository import Gtk; print(Gtk.IconTheme.get_default().has_icon('folder-symbolic'))"
```

---

## What to Expect

### On First Run:
1. Window opens showing file explorer
2. Lists folders and files in current directory
3. Toolbar with navigation buttons
4. Status bar with file count

### What Works:
- ✅ Browse directories
- ✅ Navigate back/forward/up
- ✅ Double-click folders to enter
- ✅ View file sizes and dates
- ✅ Sort by columns

### What's Missing (for Phase 2):
- ⚠️ Right-click menu
- ⚠️ Create/delete/rename
- ⚠️ Recent files
- ⚠️ Search
- ⚠️ Custom icons

---

## Next Steps After Testing

1. **If it works**: Proceed to Phase 2 (file operations)
2. **If issues**: Debug and fix basic functionality first
3. **When stable**: Integrate into main application
4. **Then add**: Additional features from roadmap

---

## Quick Reference Commands

```bash
# Test standalone
python3 scripts/test_file_explorer.py

# Test in main app
python3 src/shypn.py

# Check for errors
python3 -m py_compile ui/panels/file_explorer.py

# Format code
python3 -m black ui/panels/file_explorer.py

# Run with debug
GTK_DEBUG=interactive python3 scripts/test_file_explorer.py
```

---

**Status**: Ready to Copy-Paste and Test! 🚀  
**Estimated Time**: 30-60 minutes to get basic version working  
**Next**: Run test script and verify functionality
