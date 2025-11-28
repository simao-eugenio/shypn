#!/usr/bin/env python3
"""Test File Panel for Wayland issues.

This script loads ONLY the File panel to isolate Wayland Error 71 issues.
Tests attach/detach/float operations in a minimal environment.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.left_panel_loader import create_left_panel


class TestWindow(Gtk.ApplicationWindow):
    """Minimal test window for File panel."""
    
    def __init__(self, app):
        super().__init__(application=app, title="File Panel Wayland Test")
        self.set_default_size(1000, 600)
        
        # Create main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(main_box)
        
        # Left side: Container for panel (when attached)
        left_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        left_container.set_size_request(300, -1)
        main_box.pack_start(left_container, False, True, 0)
        
        # Right side: Test controls
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        control_box.set_margin_start(10)
        control_box.set_margin_end(10)
        control_box.set_margin_top(10)
        control_box.set_margin_bottom(10)
        main_box.pack_start(control_box, True, True, 0)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>File Panel Wayland Test</b></big>")
        control_box.pack_start(title, False, False, 0)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<small>Watch terminal for Wayland errors while clicking buttons.\n"
            "Look for: <tt>Error 71 (Protocol error)</tt></small>"
        )
        instructions.set_line_wrap(True)
        control_box.pack_start(instructions, False, False, 0)
        
        # Separator
        control_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Load File Panel
        print("[TEST] Loading File panel...")
        self.file_panel = create_left_panel()
        # Note: parent_window is set via attach_to() call
        
        # Initially attach the panel
        print("[TEST] Attaching panel...")
        self.file_panel.attach_to(left_container, self)
        self.panel_attached = True
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        control_box.pack_start(button_box, False, False, 0)
        
        # Attach/Detach button
        self.attach_button = Gtk.Button(label="🔗 Detach Panel")
        self.attach_button.connect('clicked', self.on_toggle_attach)
        button_box.pack_start(self.attach_button, False, False, 0)
        
        # Float button
        self.float_button = Gtk.Button(label="🎈 Float Panel")
        self.float_button.connect('clicked', self.on_float)
        button_box.pack_start(self.float_button, False, False, 0)
        
        # Hide button
        self.hide_button = Gtk.Button(label="👁 Hide Panel")
        self.hide_button.connect('clicked', self.on_hide)
        button_box.pack_start(self.hide_button, False, False, 0)
        
        # Show button
        self.show_button = Gtk.Button(label="👁 Show Panel")
        self.show_button.connect('clicked', self.on_show)
        button_box.pack_start(self.show_button, False, False, 0)
        
        # Separator
        button_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Rapid toggle test
        rapid_label = Gtk.Label()
        rapid_label.set_markup("<b>Stress Tests:</b>")
        rapid_label.set_xalign(0)
        button_box.pack_start(rapid_label, False, False, 0)
        
        self.rapid_button = Gtk.Button(label="⚡ Rapid Toggle (10x)")
        self.rapid_button.connect('clicked', self.on_rapid_toggle)
        button_box.pack_start(self.rapid_button, False, False, 0)
        
        self.cycle_button = Gtk.Button(label="🔄 Attach/Hide Cycle (20x)")
        self.cycle_button.connect('clicked', self.on_cycle_test)
        button_box.pack_start(self.cycle_button, False, False, 0)
        
        # Separator
        button_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Status: Panel attached</i>")
        self.status_label.set_xalign(0)
        self.status_label.set_line_wrap(True)
        control_box.pack_start(self.status_label, False, False, 0)
        
        # Console output
        console_label = Gtk.Label()
        console_label.set_markup("<b>Console Output:</b>")
        console_label.set_xalign(0)
        control_box.pack_start(console_label, False, False, 5)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(-1, 200)
        scrolled.set_vexpand(True)
        control_box.pack_start(scrolled, True, True, 0)
        
        self.console_view = Gtk.TextView()
        self.console_view.set_editable(False)
        self.console_view.set_monospace(True)
        scrolled.add(self.console_view)
        
        # Store container reference
        self.left_container = left_container
        
        print("[TEST] Test window ready!")
        
    def on_toggle_attach(self, button):
        """Toggle attach/detach state."""
        print("\n[TEST] ========== Toggle Attach/Detach ==========")
        if self.panel_attached:
            print("[TEST] Detaching panel...")
            self.file_panel.unattach()
            self.panel_attached = False
            button.set_label("🔗 Attach Panel")
            self.status_label.set_markup("<i>Status: Panel detached</i>")
        else:
            print("[TEST] Attaching panel...")
            self.file_panel.attach_to(self.left_container, self)
            self.panel_attached = True
            button.set_label("🔗 Detach Panel")
            self.status_label.set_markup("<i>Status: Panel attached</i>")
        print("[TEST] ========== Toggle Complete ==========\n")
    
    def on_float(self, button):
        """Float the panel."""
        print("\n[TEST] ========== Float Panel ==========")
        self.file_panel.float(self)
        self.panel_attached = False
        self.attach_button.set_label("🔗 Attach Panel")
        self.status_label.set_markup("<i>Status: Panel floating</i>")
        print("[TEST] ========== Float Complete ==========\n")
    
    def on_hide(self, button):
        """Hide the panel."""
        print("\n[TEST] ========== Hide Panel ==========")
        self.file_panel.hide()
        self.status_label.set_markup("<i>Status: Panel hidden</i>")
        print("[TEST] ========== Hide Complete ==========\n")
    
    def on_show(self, button):
        """Show the panel (re-attach if needed)."""
        print("\n[TEST] ========== Show Panel ==========")
        if not self.panel_attached:
            self.file_panel.attach_to(self.left_container, self)
            self.panel_attached = True
            self.attach_button.set_label("🔗 Detach Panel")
        self.status_label.set_markup("<i>Status: Panel attached/visible</i>")
        print("[TEST] ========== Show Complete ==========\n")
    
    def on_rapid_toggle(self, button):
        """Rapid toggle test - attach/detach 10 times."""
        print("\n[TEST] ========== RAPID TOGGLE TEST START ==========")
        button.set_sensitive(False)
        self.status_label.set_markup("<i>Status: <b>Running rapid toggle test...</b></i>")
        
        count = [0]
        max_toggles = 10
        
        def do_toggle():
            if count[0] >= max_toggles:
                button.set_sensitive(True)
                self.status_label.set_markup(f"<i>Status: Rapid toggle test complete ({max_toggles} cycles)</i>")
                print(f"[TEST] ========== RAPID TOGGLE TEST COMPLETE ({max_toggles} cycles) ==========\n")
                return False
            
            count[0] += 1
            print(f"[TEST] Rapid toggle {count[0]}/{max_toggles}...")
            
            if self.panel_attached:
                self.file_panel.unattach()
                self.panel_attached = False
            else:
                self.file_panel.attach_to(self.left_container, self)
                self.panel_attached = True
            
            return True
        
        # Schedule toggles with 100ms delay between each
        GLib.timeout_add(100, do_toggle)
    
    def on_cycle_test(self, button):
        """Cycle test - attach then hide repeatedly."""
        print("\n[TEST] ========== ATTACH/HIDE CYCLE TEST START ==========")
        button.set_sensitive(False)
        self.status_label.set_markup("<i>Status: <b>Running attach/hide cycle test...</b></i>")
        
        count = [0]
        max_cycles = 20
        state = ['attach']  # 'attach' or 'hide'
        
        def do_cycle():
            if count[0] >= max_cycles:
                button.set_sensitive(True)
                self.status_label.set_markup(f"<i>Status: Cycle test complete ({max_cycles} cycles)</i>")
                print(f"[TEST] ========== CYCLE TEST COMPLETE ({max_cycles} cycles) ==========\n")
                return False
            
            if state[0] == 'attach':
                count[0] += 1
                print(f"[TEST] Cycle {count[0]}/{max_cycles} - Attach...")
                if not self.panel_attached:
                    self.file_panel.attach_to(self.left_container, self)
                    self.panel_attached = True
                state[0] = 'hide'
            else:
                print(f"[TEST] Cycle {count[0]}/{max_cycles} - Hide...")
                self.file_panel.hide()
                state[0] = 'attach'
            
            return True
        
        # Schedule cycles with 150ms delay between each operation
        GLib.timeout_add(150, do_cycle)


class TestApplication(Gtk.Application):
    """Test application."""
    
    def __init__(self):
        super().__init__(application_id='org.shypn.test.filepanel')
    
    def do_activate(self):
        """Activate the application."""
        win = TestWindow(self)
        win.show_all()


def main():
    """Run the test application."""
    print("=" * 70)
    print("File Panel Wayland Test")
    print("=" * 70)
    print("Watch for: Gdk-Message: Error 71 (Protocol error)")
    print("=" * 70)
    print()
    
    app = TestApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
