#!/usr/bin/env python3
"""Manual test for File Panel - Test ALL buttons and operations.

This script opens the File panel and provides manual test controls to verify:
1. All toolbar buttons (New, Open, Save, Save As, New Folder)
2. All navigation buttons (Back, Forward, Up, Home)
3. TreeView operations (click, double-click, context menu)
4. Panel attach/detach operations

Usage:
    python3 dev/test_file_panel_manual.py
    
Then click buttons in the GUI to test each operation.
Watch terminal for detailed logs and Error 71.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from shypn.helpers.left_panel_loader import create_left_panel
from shypn.ui.master_palette import MasterPalette


class FilePanelManualTest:
    """Manual test harness for File Panel."""
    
    def __init__(self):
        """Initialize test window."""
        # Create main window
        self.window = Gtk.Window(title="File Panel Manual Test - Click ALL Buttons")
        self.window.set_default_size(900, 700)
        self.window.connect('destroy', Gtk.main_quit)
        
        # Create main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(main_box)
        
        # ===================================================================
        # TEST INSTRUCTIONS PANEL (TOP)
        # ===================================================================
        
        instructions_frame = Gtk.Frame(label="📋 Test Instructions")
        instructions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        instructions_box.set_margin_top(10)
        instructions_box.set_margin_bottom(10)
        instructions_box.set_margin_start(10)
        instructions_box.set_margin_end(10)
        instructions_frame.add(instructions_box)
        
        inst_label = Gtk.Label()
        inst_label.set_markup(
            "<b>TEST ALL FILE PANEL BUTTONS:</b>\n"
            "1. Click <b>New</b> button (should open FileChooser)\n"
            "2. Click <b>Open</b> button (should open FileChooser)\n"
            "3. Click <b>Save</b> button (should open FileChooser)\n"
            "4. Click <b>Save As</b> button (should open FileChooser)\n"
            "5. Click <b>New Folder</b> button (should open dialog)\n"
            "6. Click <b>Back/Forward/Up/Home</b> navigation buttons\n"
            "7. Click files in TreeView (single and double-click)\n"
            "8. Right-click files for context menu\n"
            "9. <b>⚠️  CRITICAL: Click Float/Attach toggle button multiple times!</b>\n"
            "10. Watch terminal for 'Error 71' messages"
        )
        inst_label.set_line_wrap(True)
        inst_label.set_xalign(0)
        instructions_box.pack_start(inst_label, False, False, 0)
        
        main_box.pack_start(instructions_frame, False, False, 10)
        
        # ===================================================================
        # CONTROL PANEL (MIDDLE)
        # ===================================================================
        
        control_frame = Gtk.Frame(label="🎮 Test Controls")
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        control_box.set_margin_top(10)
        control_box.set_margin_bottom(10)
        control_box.set_margin_start(10)
        control_box.set_margin_end(10)
        control_frame.add(control_box)
        
        # Status label
        self.status_label = Gtk.Label(label="Status: Ready")
        self.status_label.set_xalign(0)
        control_box.pack_start(self.status_label, True, True, 0)
        
        # Quit button
        quit_btn = Gtk.Button(label="Quit Test")
        quit_btn.connect('clicked', lambda w: Gtk.main_quit())
        control_box.pack_start(quit_btn, False, False, 0)
        
        main_box.pack_start(control_frame, False, False, 0)
        
        # ===================================================================
        # FILE PANEL CONTAINER (BOTTOM)
        # ===================================================================
        
        panel_frame = Gtk.Frame(label="📁 File Panel Under Test")
        self.panel_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        panel_frame.add(self.panel_container)
        
        main_box.pack_start(panel_frame, True, True, 10)
        
        # ===================================================================
        # LOAD FILE PANEL
        # ===================================================================
        
        print("=" * 80)
        print("FILE PANEL MANUAL TEST - Starting")
        print("=" * 80)
        
        try:
            print("[TEST] Creating File panel loader...")
            self.left_panel_loader = create_left_panel()
            
            # Set parent window for dialogs
            print("[TEST] Setting parent window for FileChooser dialogs...")
            if self.left_panel_loader.file_explorer:
                self.left_panel_loader.file_explorer.set_parent_window(self.window)
            
            # Attach panel
            print("[TEST] Attaching File panel to container...")
            self.left_panel_loader.attach_to(self.panel_container, parent_window=self.window)
            
            # Log all file explorer buttons
            if self.left_panel_loader.file_explorer:
                fe = self.left_panel_loader.file_explorer
                print("[TEST] File Explorer buttons available:")
                print(f"  - New button: {fe.new_button}")
                print(f"  - Open button: {fe.open_button}")
                print(f"  - Save button: {fe.save_button}")
                print(f"  - Save As button: {fe.save_as_button}")
                print(f"  - New Folder button: {fe.new_folder_button}")
                print(f"  - Back button: {fe.back_button}")
                print(f"  - Forward button: {fe.forward_button}")
                print(f"  - Up button: {fe.up_button}")
                print(f"  - Home button: {fe.home_button}")
                
                # Wrap button handlers to log clicks
                self._instrument_buttons()
            
            # CRITICAL: Also instrument the float/attach toggle button!
            if self.left_panel_loader.float_button:
                print(f"[TEST] Float button: {self.left_panel_loader.float_button}")
                self.left_panel_loader.float_button.connect('toggled', self._on_float_toggled)
            
            self.update_status("✅ File Panel loaded - Click buttons to test")
            print("[TEST] File Panel loaded successfully")
            print("[TEST] ⚠️  IMPORTANT: Click the Float/Attach button to test!")

            
        except Exception as e:
            print(f"[TEST ERROR] Failed to load File panel: {e}")
            import traceback
            traceback.print_exc()
            self.update_status(f"❌ Error: {e}")
    
    def _instrument_buttons(self):
        """Add logging to all button click handlers."""
        fe = self.left_panel_loader.file_explorer
        
        # Wrap each button's clicked signal
        if fe.new_button:
            fe.new_button.connect('clicked', self._on_button_clicked, "New")
        if fe.open_button:
            fe.open_button.connect('clicked', self._on_button_clicked, "Open")
        if fe.save_button:
            fe.save_button.connect('clicked', self._on_button_clicked, "Save")
        if fe.save_as_button:
            fe.save_as_button.connect('clicked', self._on_button_clicked, "Save As")
        if fe.new_folder_button:
            fe.new_folder_button.connect('clicked', self._on_button_clicked, "New Folder")
        if fe.back_button:
            fe.back_button.connect('clicked', self._on_button_clicked, "Back")
        if fe.forward_button:
            fe.forward_button.connect('clicked', self._on_button_clicked, "Forward")
        if fe.up_button:
            fe.up_button.connect('clicked', self._on_button_clicked, "Up")
        if fe.home_button:
            fe.home_button.connect('clicked', self._on_button_clicked, "Home")
    
    def _on_button_clicked(self, button, button_name):
        """Log button clicks."""
        print(f"[BUTTON CLICK] {button_name} button clicked")
        self.update_status(f"🖱️ {button_name} button clicked")
        # Don't stop propagation - let normal handler run
    
    def _on_float_toggled(self, toggle_button):
        """Log float button toggles - THIS IS THE CRITICAL TEST!"""
        is_active = toggle_button.get_active()
        print(f"{'='*80}")
        print(f"[FLOAT TOGGLE] Button toggled to: {is_active}")
        if is_active:
            print(f"[FLOAT TOGGLE] Panel should FLOAT (detach from container)")
            self.update_status("🔄 FLOATING panel...")
        else:
            print(f"[FLOAT TOGGLE] Panel should ATTACH (embed in container)")
            self.update_status("🔄 ATTACHING panel...")
        print(f"[FLOAT TOGGLE] Watch for Error 71 after this operation!")
        print(f"{'='*80}")
        # Don't stop propagation - let normal handler run

    
    def update_status(self, message):
        """Update status label."""
        self.status_label.set_text(f"Status: {message}")
        print(f"[STATUS] {message}")
    
    def run(self):
        """Show window and start GTK main loop."""
        self.window.show_all()
        print("[TEST] Window shown - Start testing buttons!")
        print("=" * 80)
        Gtk.main()


if __name__ == '__main__':
    print("File Panel Manual Test")
    print("Watch this terminal for Error 71 and button logs")
    print()
    
    test = FilePanelManualTest()
    test.run()
