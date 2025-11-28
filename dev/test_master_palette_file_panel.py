#!/usr/bin/env python3
"""Test MasterPalette + File Panel interaction for Wayland issues.

This script tests the interaction between MasterPalette button clicks
and File panel attach/detach operations to isolate Wayland Error 71.

Includes REAL file operations (Open/Save/New) to test FileChooser dialogs.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.left_panel_loader import create_left_panel
from shypn.ui.master_palette import MasterPalette
from shypn.file.netobj_persistency import NetObjPersistency


class TestWindow(Gtk.ApplicationWindow):
    """Minimal test window with MasterPalette + File panel."""
    
    def __init__(self, app):
        super().__init__(application=app, title="MasterPalette + File Panel Test")
        self.set_default_size(1200, 700)
        
        # Create main layout (vertical: palette on top, paned below)
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Create Master Palette
        print("[TEST] Creating MasterPalette...")
        self.master_palette = MasterPalette()
        palette_widget = self.master_palette.get_widget()
        main_vbox.pack_start(palette_widget, False, False, 0)
        
        # Create paned (left dock + canvas area)
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_vbox.pack_start(self.paned, True, True, 0)
        
        # Left dock area (for panels)
        self.left_dock = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.left_dock.set_size_request(0, -1)  # Start collapsed
        self.paned.pack1(self.left_dock, False, False)
        
        # Canvas area placeholder
        canvas_placeholder = Gtk.Label(label="Canvas Area\n\n(Click 'Files' button in palette above)")
        canvas_placeholder.set_vexpand(True)
        canvas_placeholder.set_hexpand(True)
        self.paned.pack2(canvas_placeholder, True, False)
        
        # Create File panel
        print("[TEST] Loading File panel...")
        self.file_panel = create_left_panel()
        
        # Create persistency manager for REAL file operations
        print("[TEST] Creating NetObjPersistency for file operations...")
        self.persistency = NetObjPersistency(parent_window=self)
        
        # Wire persistency to file panel (enables REAL Open/Save/SaveAs)
        if hasattr(self.file_panel, 'file_explorer'):
            self.file_panel.file_explorer.set_persistency_manager(self.persistency)
            self.file_panel.file_explorer.set_parent_window(self)
            print("[TEST] File panel wired with REAL file operations!")
        
        # Set up MasterPalette callbacks
        print("[TEST] Wiring MasterPalette callbacks...")
        
        def on_files_clicked(active):
            """Handle Files button from MasterPalette."""
            print(f"\n[TEST] ===== FILES BUTTON: active={active} =====")
            if active:
                print("[TEST] Attaching File panel...")
                self.file_panel.attach_to(self.left_dock, parent_window=self)
                # Expand paned to show panel
                self.paned.set_position(300)
                print("[TEST] File panel attached, paned expanded to 300")
            else:
                print("[TEST] Hiding File panel...")
                self.file_panel.hide()
                # Collapse paned
                self.paned.set_position(0)
                print("[TEST] File panel hidden, paned collapsed")
            print(f"[TEST] ===== FILES BUTTON COMPLETE =====\n")
        
        def on_pathways_clicked(active):
            """Handle Pathways button (not implemented in this test)."""
            print(f"[TEST] Pathways button: active={active} (not implemented)")
        
        def on_analyses_clicked(active):
            """Handle Analyses button (not implemented in this test)."""
            print(f"[TEST] Analyses button: active={active} (not implemented)")
        
        def on_topology_clicked(active):
            """Handle Topology button (not implemented in this test)."""
            print(f"[TEST] Topology button: active={active} (not implemented)")
        
        # Connect MasterPalette callbacks
        self.master_palette.connect('files', on_files_clicked)
        self.master_palette.connect('pathways', on_pathways_clicked)
        self.master_palette.connect('analyses', on_analyses_clicked)
        self.master_palette.connect('topology', on_topology_clicked)
        
        # Status area
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_start(10)
        status_box.set_margin_end(10)
        status_box.set_margin_top(5)
        status_box.set_margin_bottom(5)
        main_vbox.pack_start(status_box, False, False, 0)
        
        status_label = Gtk.Label()
        status_label.set_markup(
            "<small><b>Test Instructions:</b> "
            "1) Click 'Files' in palette above to attach panel. "
            "2) Use file operations (Open/Save/New) to test FileChooser. "
            "3) Click 'Files' again to detach. "
            "4) Watch terminal for Wayland errors.</small>"
        )
        status_label.set_line_wrap(True)
        status_label.set_xalign(0)
        status_box.pack_start(status_label, True, True, 0)
        
        # Test buttons
        test_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        status_box.pack_start(test_button_box, False, False, 0)
        
        rapid_test_btn = Gtk.Button(label="⚡ Rapid Toggle (10x)")
        rapid_test_btn.connect('clicked', self.on_rapid_toggle)
        test_button_box.pack_start(rapid_test_btn, False, False, 0)
        
        print("[TEST] Test window ready!")
        print("[TEST] Click 'Files' button to attach panel")
        
        # Auto-click Files button after 1 second (for automated testing)
        def auto_click_files():
            print("\n[TEST] AUTO-CLICKING Files button...")
            self.master_palette.set_active('files', True)
            print("[TEST] Files button clicked programmatically\n")
            return False
        
        GLib.timeout_add(1000, auto_click_files)
        
    def on_rapid_toggle(self, button):
        """Rapid toggle test via MasterPalette."""
        print("\n[TEST] ========== RAPID TOGGLE TEST START ==========")
        button.set_sensitive(False)
        
        count = [0]
        max_toggles = 10
        
        def do_toggle():
            if count[0] >= max_toggles:
                button.set_sensitive(True)
                print(f"[TEST] ========== RAPID TOGGLE TEST COMPLETE ({max_toggles} cycles) ==========\n")
                return False
            
            count[0] += 1
            is_active = self.master_palette.buttons['files'].get_active()
            print(f"[TEST] Rapid toggle {count[0]}/{max_toggles} - Setting files to {not is_active}...")
            
            # Toggle via MasterPalette (simulates user clicking button)
            self.master_palette.set_active('files', not is_active)
            
            return True
        
        # Schedule toggles with 200ms delay
        GLib.timeout_add(200, do_toggle)


class TestApplication(Gtk.Application):
    """Test application."""
    
    def __init__(self):
        super().__init__(application_id='org.shypn.test.masterpalette')
    
    def do_activate(self):
        """Activate the application."""
        win = TestWindow(self)
        win.show_all()


def main():
    """Run the test application."""
    print("=" * 70)
    print("MasterPalette + File Panel Wayland Test")
    print("=" * 70)
    print("Watch for: Gdk-Message: Error 71 (Protocol error)")
    print("This test includes:")
    print("  - MasterPalette button handling")
    print("  - File panel attach/detach via palette")
    print("  - REAL file operations (Open/Save/New)")
    print("  - FileChooser dialog testing")
    print("=" * 70)
    print()
    
    app = TestApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
