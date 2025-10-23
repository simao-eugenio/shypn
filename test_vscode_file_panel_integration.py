#!/usr/bin/env python3
"""Test VS Code-style File Panel integration.

Tests:
1. Panel loads correctly
2. Float/attach/detach operations work
3. Category expansion (exclusive behavior)
4. Inline file operations (new file, new folder, rename)
5. Keyboard shortcuts (F2, Del, Ctrl+C/X/V)
6. Context menu operations
7. Integration with main window (file chooser parent)
8. GtkStack integration (show/hide in stack)

This mimics the main app's panel management to verify all features work.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.left_panel_loader_vscode import LeftPanelLoaderVSCode


class TestBedWindow(Gtk.Window):
    """Test bed window for VS Code-style File panel.
    
    Simulates main app environment:
    - Main window with panels
    - GtkStack for docked panels
    - Float/attach/detach operations
    - Master palette integration (simulated)
    """
    
    def __init__(self):
        super().__init__(title="VS Code File Panel Test Bed")
        
        self.set_default_size(900, 600)
        self.connect('destroy', Gtk.main_quit)
        
        # Panel state
        self.panel_is_floating = False
        
        # Build UI
        self._build_ui()
        
        # Load VS Code-style File panel
        self._load_file_panel()
        
        # Show test instructions
        self._show_instructions()
    
    def _build_ui(self):
        """Build test bed UI structure."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Test controls toolbar
        toolbar = self._build_toolbar()
        main_box.pack_start(toolbar, False, False, 0)
        
        # Separator
        main_box.pack_start(Gtk.Separator(), False, False, 0)
        
        # Content area with paned
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(300)
        main_box.pack_start(self.paned, True, True, 0)
        
        # Left side: GtkStack for docked panel
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Panel container label
        panel_label = Gtk.Label()
        panel_label.set_markup("<b>File Panel (Docked)</b>")
        panel_label.set_margin_top(6)
        panel_label.set_margin_bottom(6)
        left_box.pack_start(panel_label, False, False, 0)
        
        # GtkStack for panel content
        self.panel_stack = Gtk.Stack()
        self.panel_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        left_box.pack_start(self.panel_stack, True, True, 0)
        
        self.paned.pack1(left_box, True, False)
        
        # Right side: Canvas placeholder
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        canvas_label = Gtk.Label()
        canvas_label.set_markup("<b>Canvas Area</b>\n\n<small>(Main app content would go here)</small>")
        canvas_label.set_valign(Gtk.Align.CENTER)
        right_box.pack_start(canvas_label, True, True, 0)
        
        self.paned.pack2(right_box, True, True)
        
        # Status bar
        self.status_bar = Gtk.Label()
        self.status_bar.set_markup("<i>Ready - Use toolbar buttons to test panel operations</i>")
        self.status_bar.set_margin_top(3)
        self.status_bar.set_margin_bottom(3)
        main_box.pack_start(Gtk.Separator(), False, False, 0)
        main_box.pack_start(self.status_bar, False, False, 0)
    
    def _build_toolbar(self):
        """Build test controls toolbar."""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(6)
        toolbar.set_margin_end(6)
        toolbar.set_margin_top(6)
        toolbar.set_margin_bottom(6)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b>Test Controls:</b>")
        toolbar.pack_start(title, False, False, 0)
        
        # Float/Attach button
        self.float_button = Gtk.Button(label="Float Panel")
        self.float_button.connect('clicked', self._on_float_clicked)
        toolbar.pack_start(self.float_button, False, False, 0)
        
        # Show/Hide button
        self.show_hide_button = Gtk.Button(label="Hide Panel")
        self.show_hide_button.connect('clicked', self._on_show_hide_clicked)
        toolbar.pack_start(self.show_hide_button, False, False, 0)
        
        # Expand category buttons
        toolbar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        
        files_btn = Gtk.Button(label="Expand FILES")
        files_btn.connect('clicked', lambda b: self._expand_category(0))
        toolbar.pack_start(files_btn, False, False, 0)
        
        info_btn = Gtk.Button(label="Expand PROJECT INFO")
        info_btn.connect('clicked', lambda b: self._expand_category(1))
        toolbar.pack_start(info_btn, False, False, 0)
        
        actions_btn = Gtk.Button(label="Expand PROJECT ACTIONS")
        actions_btn.connect('clicked', lambda b: self._expand_category(2))
        toolbar.pack_start(actions_btn, False, False, 0)
        
        # Test file operations
        toolbar.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)
        
        new_file_btn = Gtk.Button(label="Test: New File")
        new_file_btn.connect('clicked', lambda b: self._test_new_file())
        toolbar.pack_start(new_file_btn, False, False, 0)
        
        new_folder_btn = Gtk.Button(label="Test: New Folder")
        new_folder_btn.connect('clicked', lambda b: self._test_new_folder())
        toolbar.pack_start(new_folder_btn, False, False, 0)
        
        return toolbar
    
    def _load_file_panel(self):
        """Load VS Code-style File panel."""
        try:
            # Create loader
            self.panel_loader = LeftPanelLoaderVSCode()
            
            # Load panel
            panel_window = self.panel_loader.load()
            
            # Set parent window for dialogs
            self.panel_loader.set_parent_window(self)
            
            # Add to stack (docked mode)
            self.panel_loader.add_to_stack(self.panel_stack, panel_name='files')
            
            # Show panel in stack
            self.panel_loader.show_in_stack()
            
            self._update_status("✓ File panel loaded successfully")
            
        except Exception as e:
            self._update_status(f"✗ Failed to load panel: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_float_clicked(self, button):
        """Toggle float/attach panel."""
        if not self.panel_is_floating:
            # Float panel
            self._float_panel()
            self.float_button.set_label("Attach Panel")
            self.panel_is_floating = True
            self._update_status("✓ Panel floated to separate window")
        else:
            # Attach panel
            self._attach_panel()
            self.float_button.set_label("Float Panel")
            self.panel_is_floating = False
            self._update_status("✓ Panel attached to main window")
    
    def _float_panel(self):
        """Float panel to separate window."""
        if not self.panel_loader:
            return
        
        # Remove content from stack
        content = self.panel_loader.content
        if content and content.get_parent():
            content.get_parent().remove(content)
        
        # Add content back to panel window
        if self.panel_loader.window and content:
            self.panel_loader.window.add(content)
            self.panel_loader.window.set_transient_for(self)
            self.panel_loader.window.show_all()
    
    def _attach_panel(self):
        """Attach panel back to main window."""
        if not self.panel_loader:
            return
        
        # Hide panel window
        if self.panel_loader.window:
            self.panel_loader.window.hide()
        
        # Remove content from window
        content = self.panel_loader.content
        if content and content.get_parent() == self.panel_loader.window:
            self.panel_loader.window.remove(content)
        
        # Add back to stack
        self.panel_loader.add_to_stack(self.panel_stack, panel_name='files')
        self.panel_loader.show_in_stack()
    
    def _on_show_hide_clicked(self, button):
        """Toggle panel visibility."""
        if not self.panel_loader:
            return
        
        # Check current visibility
        if self.panel_is_floating:
            # Toggle window visibility
            if self.panel_loader.window.get_visible():
                self.panel_loader.window.hide()
                self.show_hide_button.set_label("Show Panel")
                self._update_status("✓ Panel hidden")
            else:
                self.panel_loader.window.show_all()
                self.show_hide_button.set_label("Hide Panel")
                self._update_status("✓ Panel shown")
        else:
            # Toggle stack visibility
            if self.panel_stack.get_visible():
                self.panel_loader.hide_in_stack()
                self.show_hide_button.set_label("Show Panel")
                self._update_status("✓ Panel hidden in stack")
            else:
                self.panel_loader.show_in_stack()
                self.show_hide_button.set_label("Hide Panel")
                self._update_status("✓ Panel shown in stack")
    
    def _expand_category(self, index):
        """Expand a specific category (test exclusive expansion)."""
        if not self.panel_loader or not self.panel_loader.categories:
            return
        
        if 0 <= index < len(self.panel_loader.categories):
            category = self.panel_loader.categories[index]
            category.set_expanded(True)
            self._update_status(f"✓ Expanded category: {category.title}")
    
    def _test_new_file(self):
        """Test new file creation with inline editing."""
        if self.panel_loader and self.panel_loader.file_explorer:
            self.panel_loader._on_new_file_clicked()
            self._update_status("✓ New file creation started (inline editing)")
    
    def _test_new_folder(self):
        """Test new folder creation with inline editing."""
        if self.panel_loader and self.panel_loader.file_explorer:
            self.panel_loader._on_new_folder_clicked()
            self._update_status("✓ New folder creation started (inline editing)")
    
    def _update_status(self, message):
        """Update status bar."""
        self.status_bar.set_markup(f"<i>{message}</i>")
        print(f"[STATUS] {message}", file=sys.stderr)
    
    def _show_instructions(self):
        """Show test instructions in console."""
        print("\n" + "="*70)
        print("VS CODE FILE PANEL TEST BED")
        print("="*70)
        print("\nTEST CONTROLS:")
        print("  • Float Panel → Detaches panel to separate window")
        print("  • Attach Panel → Re-attaches panel to main window")
        print("  • Show/Hide Panel → Toggles panel visibility")
        print("  • Expand [Category] → Tests exclusive expansion")
        print("  • Test: New File → Creates file with inline editing")
        print("  • Test: New Folder → Creates folder with inline editing")
        print("\nFILE OPERATIONS (in file tree):")
        print("  • Double-click file → Opens file")
        print("  • Right-click → Context menu")
        print("  • F2 → Rename (inline)")
        print("  • Delete → Delete file/folder")
        print("  • Ctrl+C/X/V → Copy/Cut/Paste")
        print("  • Ctrl+N → New file (inline)")
        print("  • Ctrl+Shift+N → New folder (inline)")
        print("\nCATEGORY EXPANSION:")
        print("  • Click category header → Expands/collapses")
        print("  • Only ONE category expanded at a time (exclusive)")
        print("\nEXPECTED BEHAVIOR:")
        print("  ✓ Panel should float/attach smoothly")
        print("  ✓ All file operations use inline editing (no dialogs)")
        print("  ✓ Keyboard shortcuts work")
        print("  ✓ Context menu shows all operations")
        print("  ✓ Categories expand/collapse exclusively")
        print("  ✓ Parent window set correctly for file choosers")
        print("="*70 + "\n")


def main():
    """Run test bed."""
    test_window = TestBedWindow()
    test_window.show_all()
    
    # Run GTK main loop
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\n[TEST] Interrupted by user")
        return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
