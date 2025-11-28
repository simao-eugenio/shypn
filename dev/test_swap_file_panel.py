#!/usr/bin/env python3
"""Test: Swap production file panel with simple test panel.

This test proves whether the Error 71 is caused by the file panel's
complex signaling/structure vs the simple test panel that works fine.

Expected Result:
- If simple panel works → Production file panel signaling is the cause
- If simple panel fails → GtkStack/architecture issue
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Import the working simple panel from test_gtkstack_principle
class SimpleFilePanel(Gtk.Box):
    """Simplified file panel based on test_gtkstack_principle.py HeavyPanel.
    
    This panel WORKS without Error 71 in the skeleton tests.
    We'll use it to replace the production file panel temporarily.
    """
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_size_request(300, -1)
        
        # Panel window (for compatibility with attach/detach API)
        self.window = Gtk.Window(title="Simple File Panel")
        self.content = self  # The box itself is the content
        
        # State tracking (for compatibility)
        self.is_attached = False
        self.parent_container = None
        self.parent_window = None
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build simple panel UI with file operations."""
        
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(10)
        header.set_margin_end(10)
        
        title = Gtk.Label()
        title.set_markup("<b>Simple File Panel</b>")
        title.set_halign(Gtk.Align.START)
        header.pack_start(title, True, True, 0)
        
        self.pack_start(header, False, False, 0)
        
        # === FILE OPERATIONS ===
        ops_frame = Gtk.Frame(label="File Operations")
        ops_frame.set_margin_start(10)
        ops_frame.set_margin_end(10)
        ops_frame.set_margin_bottom(10)
        
        ops_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        ops_box.set_margin_top(10)
        ops_box.set_margin_bottom(10)
        ops_box.set_margin_start(10)
        ops_box.set_margin_end(10)
        
        # New button
        new_btn = Gtk.Button(label="New")
        new_btn.connect('clicked', self._on_new_clicked)
        ops_box.pack_start(new_btn, False, False, 0)
        
        # Open button (FileChooser)
        open_btn = Gtk.Button(label="Open")
        open_btn.connect('clicked', self._on_open_clicked)
        ops_box.pack_start(open_btn, False, False, 0)
        
        # Save button (FileChooser)
        save_btn = Gtk.Button(label="Save")
        save_btn.connect('clicked', self._on_save_clicked)
        ops_box.pack_start(save_btn, False, False, 0)
        
        # Save As button (FileChooser)
        save_as_btn = Gtk.Button(label="Save As")
        save_as_btn.connect('clicked', self._on_save_as_clicked)
        ops_box.pack_start(save_as_btn, False, False, 0)
        
        ops_frame.add(ops_box)
        self.pack_start(ops_frame, False, False, 0)
        
        # === FILE BROWSER (Simple TreeView) ===
        browser_frame = Gtk.Frame(label="File Browser")
        browser_frame.set_margin_start(10)
        browser_frame.set_margin_end(10)
        browser_frame.set_margin_bottom(10)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 300)
        
        # Simple TreeView with dummy data
        self.file_store = Gtk.ListStore(str, str)
        self.file_store.append(["📄", "example1.shy"])
        self.file_store.append(["📄", "example2.shy"])
        self.file_store.append(["📄", "example3.shy"])
        self.file_store.append(["📁", "subfolder/"])
        
        self.tree_view = Gtk.TreeView(model=self.file_store)
        
        # Icon column
        icon_renderer = Gtk.CellRendererText()
        icon_column = Gtk.TreeViewColumn("", icon_renderer, text=0)
        self.tree_view.append_column(icon_column)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Name", name_renderer, text=1)
        self.tree_view.append_column(name_column)
        
        scrolled.add(self.tree_view)
        browser_frame.add(scrolled)
        self.pack_start(browser_frame, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="Simple panel loaded - Click buttons to test")
        self.status_label.set_margin_top(5)
        self.status_label.set_margin_bottom(5)
        self.pack_start(self.status_label, False, False, 0)
    
    def _on_new_clicked(self, button):
        """Handle New button."""
        print("[SIMPLE] New clicked - showing info dialog")
        self.status_label.set_text("New document created")
        
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="New Document"
        )
        dialog.format_secondary_text("New document created successfully!")
        dialog.run()
        dialog.destroy()
    
    def _on_open_clicked(self, button):
        """Handle Open button - uses FileChooserDialog."""
        print("[SIMPLE] Open clicked - showing FileChooser")
        
        dialog = Gtk.FileChooserDialog(
            title="Open File (Simple Panel)",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add filter
        filter_shy = Gtk.FileFilter()
        filter_shy.set_name("SHYpn files (*.shy)")
        filter_shy.add_pattern("*.shy")
        dialog.add_filter(filter_shy)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.status_label.set_text(f"Opened: {os.path.basename(filename)}")
            print(f"[SIMPLE] File opened: {filename}")
        else:
            self.status_label.set_text("Open cancelled")
            print("[SIMPLE] Open cancelled")
        
        dialog.destroy()
    
    def _on_save_clicked(self, button):
        """Handle Save button - uses FileChooserDialog."""
        print("[SIMPLE] Save clicked - showing FileChooser")
        
        dialog = Gtk.FileChooserDialog(
            title="Save File (Simple Panel)",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        
        # Add filter
        filter_shy = Gtk.FileFilter()
        filter_shy.set_name("SHYpn files (*.shy)")
        filter_shy.add_pattern("*.shy")
        dialog.add_filter(filter_shy)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.status_label.set_text(f"Saved: {os.path.basename(filename)}")
            print(f"[SIMPLE] File saved: {filename}")
        else:
            self.status_label.set_text("Save cancelled")
            print("[SIMPLE] Save cancelled")
        
        dialog.destroy()
    
    def _on_save_as_clicked(self, button):
        """Handle Save As button."""
        self._on_save_clicked(button)  # Same as Save for this test
    
    # ===================================================================
    # Compatibility methods for panel loader API
    # ===================================================================
    
    def add_to_stack(self, stack, container, panel_name='files'):
        """Add panel to GtkStack (compatibility method)."""
        print(f"[SIMPLE] add_to_stack() called for '{panel_name}'")
        
        # Remove from window if attached
        if self.content.get_parent() == self.window:
            self.window.remove(self.content)
        elif self.content.get_parent():
            self.content.get_parent().remove(self.content)
        
        # Add to container
        container.add(self.content)
        
        # Store references
        self.is_attached = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
        # Hide window
        self.window.hide()
        
        print(f"[SIMPLE] Panel added to stack container")
    
    def show_in_stack(self):
        """Show panel in GtkStack."""
        print(f"[SIMPLE] show_in_stack() called")
        
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        if self.content:
            self.content.show_all()
        
        if self.parent_container:
            self.parent_container.set_visible(True)
        
        print(f"[SIMPLE] Panel now visible in stack")
    
    def hide_in_stack(self):
        """Hide panel in GtkStack."""
        print(f"[SIMPLE] hide_in_stack() called")
        if self.content:
            self.content.set_visible(False)


def run_test():
    """Run the swap test with production shypn.py."""
    print("=" * 70)
    print("SWAP TEST: Replace production file panel with simple test panel")
    print("=" * 70)
    print()
    print("This test will:")
    print("  1. Load the production shypn.py")
    print("  2. Replace left_panel_loader with SimpleFilePanel")
    print("  3. Run Master Palette with the simple panel")
    print("  4. Test file operations (Open/Save)")
    print()
    print("Expected result:")
    print("  - If NO Error 71 → Production file panel is the cause")
    print("  - If Error 71 occurs → GtkStack/architecture issue")
    print("=" * 70)
    print()
    
    # Import production shypn module
    from shypn import create_application
    
    # Monkey-patch: Replace left_panel_loader creation
    import shypn.helpers.left_panel_loader as left_panel_module
    
    original_create = left_panel_module.create_left_panel
    
    def create_simple_panel(*args, **kwargs):
        """Create simple panel instead of production panel."""
        print("[SWAP] Creating SimpleFilePanel instead of production panel...")
        return SimpleFilePanel()
    
    left_panel_module.create_left_panel = create_simple_panel
    
    print("[SWAP] Monkey-patch applied - SimpleFilePanel will be used")
    print("[SWAP] Starting production shypn.py...")
    print()
    
    # Run production app
    app = create_application()
    sys.exit(app.run(sys.argv))


if __name__ == '__main__':
    run_test()
