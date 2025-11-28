#!/usr/bin/env python3
"""GtkStack Principle Validation Test.

CRITICAL TEST: Validate GtkStack works with Wayland WITHOUT Error 71.

This test validates:
1. GtkStack with multiple heavy panels
2. Rapid switching between stack children
3. set_no_show_all() with stack children
4. Complex widgets in stack (FileChoosers, dialogs, ScrolledWindows)
5. Master Palette button control of stack visibility

MUST PASS before implementing production Master Palette architecture.

Author: Simão Eugénio
Date: 2025-10-22
"""

import sys
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject

# Test configuration
TEST_RAPID_CYCLES = 100  # Number of rapid switch cycles
TEST_TIMEOUT = 120  # Seconds before auto-exit (success)


class HeavyPanel(Gtk.Box):
    """Heavy panel with complex widgets (FileChoosers, dialogs, ScrolledWindows).
    
    This simulates a real production panel to validate GtkStack behavior.
    """
    
    def __init__(self, panel_name, panel_color):
        """Initialize heavy panel.
        
        Args:
            panel_name: Panel identifier (e.g., 'Files', 'Pathways')
            panel_color: Background color for visual identification
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.panel_name = panel_name
        self.panel_color = panel_color
        
        # Set background color for visual identification
        self.set_size_request(300, -1)
        
        # Message log (initialize BEFORE building UI)
        self.messages = []
        
        # Build panel UI
        self._build_ui()
    
    def _build_ui(self):
        """Build panel UI with heavy widgets."""
        
        # === HEADER ===
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(10)
        header.set_margin_end(10)
        
        # Panel title
        title = Gtk.Label()
        title.set_markup(f"<b>{self.panel_name} Panel</b>")
        title.set_halign(Gtk.Align.START)
        header.pack_start(title, True, True, 0)
        
        # Color indicator
        color_box = Gtk.Box()
        color_box.set_size_request(20, 20)
        color_box.override_background_color(
            Gtk.StateFlags.NORMAL,
            self._parse_color(self.panel_color)
        )
        header.pack_end(color_box, False, False, 0)
        
        self.pack_start(header, False, False, 0)
        
        # === FILE CHOOSER BUTTON ===
        chooser_frame = Gtk.Frame(label="File Chooser Widget")
        chooser_frame.set_margin_start(10)
        chooser_frame.set_margin_end(10)
        chooser_frame.set_margin_bottom(10)
        
        chooser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        chooser_box.set_margin_top(10)
        chooser_box.set_margin_bottom(10)
        chooser_box.set_margin_start(10)
        chooser_box.set_margin_end(10)
        
        # FileChooserButton (HEAVY WIDGET - can cause Wayland issues)
        self.file_chooser = Gtk.FileChooserButton(title=f"Choose File ({self.panel_name})")
        self.file_chooser.set_action(Gtk.FileChooserAction.OPEN)
        chooser_box.pack_start(self.file_chooser, False, False, 0)
        
        chooser_frame.add(chooser_box)
        self.pack_start(chooser_frame, False, False, 0)
        
        # === DIALOG BUTTONS ===
        dialogs_frame = Gtk.Frame(label="Dialog Triggers")
        dialogs_frame.set_margin_start(10)
        dialogs_frame.set_margin_end(10)
        dialogs_frame.set_margin_bottom(10)
        
        dialogs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        dialogs_box.set_margin_top(10)
        dialogs_box.set_margin_bottom(10)
        dialogs_box.set_margin_start(10)
        dialogs_box.set_margin_end(10)
        
        # Info dialog button
        info_btn = Gtk.Button(label="Info Dialog")
        info_btn.connect('clicked', self._on_info_dialog)
        dialogs_box.pack_start(info_btn, False, False, 0)
        
        # Question dialog button
        question_btn = Gtk.Button(label="Question Dialog")
        question_btn.connect('clicked', self._on_question_dialog)
        dialogs_box.pack_start(question_btn, False, False, 0)
        
        # File Open dialog button
        file_open_btn = Gtk.Button(label="File Open Dialog")
        file_open_btn.connect('clicked', self._on_file_open_dialog)
        dialogs_box.pack_start(file_open_btn, False, False, 0)
        
        # File Save dialog button
        file_save_btn = Gtk.Button(label="File Save Dialog")
        file_save_btn.connect('clicked', self._on_file_save_dialog)
        dialogs_box.pack_start(file_save_btn, False, False, 0)
        
        # Color Chooser dialog button
        color_btn = Gtk.Button(label="Color Chooser Dialog")
        color_btn.connect('clicked', self._on_color_dialog)
        dialogs_box.pack_start(color_btn, False, False, 0)
        
        dialogs_frame.add(dialogs_box)
        self.pack_start(dialogs_frame, False, False, 0)
        
        # === MESSAGE LOG (ScrolledWindow - HEAVY WIDGET) ===
        log_frame = Gtk.Frame(label="Message Log")
        log_frame.set_margin_start(10)
        log_frame.set_margin_end(10)
        log_frame.set_margin_bottom(10)
        
        # ScrolledWindow (HEAVY WIDGET - can cause issues in stack)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        # TextView
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_buffer = self.log_view.get_buffer()
        
        scrolled.add(self.log_view)
        log_frame.add(scrolled)
        self.pack_start(log_frame, True, True, 0)
        
        # Initial log message
        self.log_message(f"{self.panel_name} panel initialized")
    
    def _parse_color(self, color_str):
        """Parse color string to Gdk.RGBA."""
        from gi.repository import Gdk
        rgba = Gdk.RGBA()
        rgba.parse(color_str)
        return rgba
    
    def log_message(self, message):
        """Add message to log."""
        self.messages.append(message)
        
        # Update TextView
        current_text = self.log_buffer.get_text(
            self.log_buffer.get_start_iter(),
            self.log_buffer.get_end_iter(),
            False
        )
        
        if current_text:
            new_text = current_text + "\n" + message
        else:
            new_text = message
        
        self.log_buffer.set_text(new_text)
        
        # Scroll to end
        end_iter = self.log_buffer.get_end_iter()
        self.log_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
    
    def _on_info_dialog(self, button):
        """Show info dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f"Info from {self.panel_name}"
        )
        dialog.format_secondary_text(f"This is an info dialog triggered from {self.panel_name} panel.")
        dialog.run()
        dialog.destroy()
        self.log_message("Info dialog closed")
    
    def _on_question_dialog(self, button):
        """Show question dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Question from {self.panel_name}"
        )
        dialog.format_secondary_text("Do you like this panel?")
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.log_message("User answered: YES")
        else:
            self.log_message("User answered: NO")
    
    def _on_file_open_dialog(self, button):
        """Show file open dialog."""
        dialog = Gtk.FileChooserDialog(
            title=f"Open File ({self.panel_name})",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.log_message(f"File selected: {filename}")
        else:
            self.log_message("File selection cancelled")
        
        dialog.destroy()
    
    def _on_file_save_dialog(self, button):
        """Show file save dialog."""
        dialog = Gtk.FileChooserDialog(
            title=f"Save File ({self.panel_name})",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.log_message(f"File to save: {filename}")
        else:
            self.log_message("Save cancelled")
        
        dialog.destroy()
    
    def _on_color_dialog(self, button):
        """Show color chooser dialog."""
        dialog = Gtk.ColorChooserDialog(
            title=f"Choose Color ({self.panel_name})",
            parent=self.get_toplevel()
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            color = dialog.get_rgba()
            self.log_message(f"Color selected: {color.to_string()}")
        else:
            self.log_message("Color selection cancelled")
        
        dialog.destroy()


class MasterPalette(Gtk.Box):
    """Master Palette - vertical toolbar with toggle buttons."""
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        self.set_size_request(48, -1)
        
        # Panel definitions
        self.panels = [
            ('files', 'Files', '📁'),
            ('pathways', 'Pathways', '🗺️'),
            ('analyses', 'Analyses', '📊'),
            ('topology', 'Topology', '🔷'),
        ]
        
        # Create buttons
        self.buttons = {}
        for panel_name, label, emoji in self.panels:
            btn = Gtk.ToggleButton(label=emoji)
            btn.set_size_request(48, 48)
            btn.set_tooltip_text(label)
            
            # Store panel name as data
            btn.panel_name = panel_name
            
            self.buttons[panel_name] = btn
            self.pack_start(btn, False, False, 2)


class TestWindow(Gtk.Window):
    """Main test window with GtkStack validation."""
    
    def __init__(self):
        super().__init__(title="GtkStack Principle Validation")
        
        self.set_default_size(800, 600)
        
        # Tracking
        self.current_panel = None
        self.switch_count = 0
        self.test_phase = "interactive"  # 'interactive' or 'automated'
        
        # Build UI
        self._build_ui()
        
        # Connect signals
        self.connect('destroy', Gtk.main_quit)
        
        # Auto-exit timer (success if no crash)
        GLib.timeout_add_seconds(TEST_TIMEOUT, self._on_timeout)
        
        print(f"[TEST] GtkStack validation started")
        print(f"[TEST] Will auto-exit in {TEST_TIMEOUT}s if no crash (SUCCESS)")
    
    def _build_ui(self):
        """Build test window UI."""
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # === MASTER PALETTE (LEFT - 48px) ===
        self.master_palette = MasterPalette()
        main_box.pack_start(self.master_palette, False, False, 0)
        
        # Connect button signals
        for panel_name, btn in self.master_palette.buttons.items():
            btn.connect('toggled', self._on_panel_button_toggled)
        
        # === LEFT DOCK AREA (GtkStack) ===
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.stack.set_visible(False)  # Start hidden
        main_box.pack_start(self.stack, False, False, 0)
        
        # Create 4 heavy panels
        self.panels = {
            'files': HeavyPanel('Files', '#e3f2fd'),
            'pathways': HeavyPanel('Pathways', '#f3e5f5'),
            'analyses': HeavyPanel('Analyses', '#e8f5e9'),
            'topology': HeavyPanel('Topology', '#fff3e0'),
        }
        
        # Add panels to stack
        for panel_name, panel in self.panels.items():
            self.stack.add_named(panel, panel_name)
            
            # CRITICAL: set_no_show_all to prevent auto-reveal
            panel.set_no_show_all(True)
            panel.hide()
        
        # === CANVAS (RIGHT - EXPANDS) ===
        canvas_frame = Gtk.Frame(label="Canvas Area (Main Content)")
        canvas_frame.set_margin_top(10)
        canvas_frame.set_margin_bottom(10)
        canvas_frame.set_margin_start(10)
        canvas_frame.set_margin_end(10)
        
        canvas_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        canvas_box.set_size_request(400, -1)
        
        # Test controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        controls_box.set_margin_top(20)
        controls_box.set_margin_bottom(20)
        controls_box.set_margin_start(20)
        controls_box.set_margin_end(20)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b>GtkStack Validation Test</b>")
        controls_box.pack_start(title, False, False, 0)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<span size='small'>"
            "1. Click Master Palette buttons to switch panels\n"
            "2. Test dialogs and FileChoosers in each panel\n"
            "3. Run automated rapid switching test\n"
            "4. Watch for Wayland Error 71\n\n"
            f"Auto-exit in {TEST_TIMEOUT}s = SUCCESS ✅"
            "</span>"
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        instructions.set_halign(Gtk.Align.START)
        controls_box.pack_start(instructions, False, False, 0)
        
        # Switch counter
        self.counter_label = Gtk.Label()
        self.counter_label.set_markup(f"<b>Switches: {self.switch_count}</b>")
        controls_box.pack_start(self.counter_label, False, False, 10)
        
        # Automated test button
        auto_test_btn = Gtk.Button(label=f"Run Automated Test ({TEST_RAPID_CYCLES} rapid switches)")
        auto_test_btn.connect('clicked', self._on_automated_test)
        controls_box.pack_start(auto_test_btn, False, False, 0)
        
        # Float panel test button
        float_test_btn = Gtk.Button(label="Test Panel Float/Detach")
        float_test_btn.connect('clicked', self._on_float_test)
        controls_box.pack_start(float_test_btn, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<span color='blue'>Status: Interactive Testing</span>")
        controls_box.pack_start(self.status_label, False, False, 0)
        
        canvas_box.pack_start(controls_box, False, False, 0)
        canvas_frame.add(canvas_box)
        main_box.pack_start(canvas_frame, True, True, 0)
        
        # Add to window
        self.add(main_box)
    
    def _on_panel_button_toggled(self, button):
        """Handle Master Palette button toggle."""
        panel_name = button.panel_name
        active = button.get_active()
        
        if active:
            # EXCLUSIVE: Deactivate all other buttons
            for name, btn in self.master_palette.buttons.items():
                if name != panel_name and btn.get_active():
                    btn.set_active(False)
            
            # Show selected panel
            self._show_panel(panel_name)
        else:
            # Hide panel
            self._hide_panel(panel_name)
    
    def _show_panel(self, panel_name):
        """Show panel in GtkStack."""
        panel = self.panels[panel_name]
        
        # Make stack visible
        self.stack.set_visible(True)
        
        # Set active child
        self.stack.set_visible_child_name(panel_name)
        
        # Allow panel to be shown
        panel.set_no_show_all(False)
        panel.show_all()
        
        # Update tracking
        self.current_panel = panel_name
        self.switch_count += 1
        self.counter_label.set_markup(f"<b>Switches: {self.switch_count}</b>")
        
        # Log to panel
        panel.log_message(f"Panel shown (switch #{self.switch_count})")
        
        print(f"[TEST] Switched to panel: {panel_name} (switch #{self.switch_count})")
    
    def _hide_panel(self, panel_name):
        """Hide panel in GtkStack."""
        panel = self.panels[panel_name]
        
        # Hide panel content
        panel.set_no_show_all(True)
        panel.hide()
        
        # Hide stack if no panels visible
        self.stack.set_visible(False)
        
        # Update tracking
        self.current_panel = None
        
        # Log to panel
        panel.log_message("Panel hidden")
        
        print(f"[TEST] Hidden panel: {panel_name}")
    
    def _on_automated_test(self, button):
        """Run automated rapid switching test."""
        print(f"[TEST] Starting automated test: {TEST_RAPID_CYCLES} rapid switches")
        
        self.test_phase = "automated"
        self.status_label.set_markup("<span color='orange'>Status: Automated Testing...</span>")
        
        # Start automated switching
        self._automated_switch_cycle(0)
    
    def _automated_switch_cycle(self, cycle):
        """Perform one automated switch cycle."""
        if cycle >= TEST_RAPID_CYCLES:
            # Test complete
            print(f"[TEST] Automated test COMPLETE: {TEST_RAPID_CYCLES} switches")
            self.status_label.set_markup("<span color='green'>Status: Automated Test PASSED ✅</span>")
            self.test_phase = "interactive"
            return False  # Stop
        
        # Get panel sequence
        panel_names = list(self.panels.keys())
        panel_index = cycle % len(panel_names)
        panel_name = panel_names[panel_index]
        
        # Activate button (which triggers panel show)
        btn = self.master_palette.buttons[panel_name]
        btn.set_active(True)
        
        # Schedule next cycle
        GLib.timeout_add(50, self._automated_switch_cycle, cycle + 1)
        
        return False  # Don't repeat (next cycle scheduled explicitly)
    
    def _on_float_test(self, button):
        """Test panel float/detach functionality.
        
        This tests the critical feature: panels can float as independent windows
        and be re-attached to the stack.
        """
        print(f"[TEST] Starting float/detach test...")
        self.status_label.set_markup("<span color='orange'>Status: Testing Float/Detach...</span>")
        
        # Test sequence:
        # 1. Show Files panel in stack
        # 2. Detach from stack (float as window)
        # 3. Re-attach to stack
        # 4. Hide panel
        
        self._float_test_sequence(0)
    
    def _float_test_sequence(self, step):
        """Execute float test sequence."""
        
        if step == 0:
            # Step 1: Show Files panel in stack
            print(f"[TEST] Float test step 1: Show Files panel in stack")
            self.master_palette.buttons['files'].set_active(True)
            GLib.timeout_add(500, self._float_test_sequence, 1)
            
        elif step == 1:
            # Step 2: Detach from stack (create floating window)
            print(f"[TEST] Float test step 2: Detach Files panel (float as window)")
            
            # Get Files panel
            files_panel = self.panels['files']
            
            # Create floating window for panel
            self.float_window = Gtk.Window(title="Files Panel (Floating)")
            self.float_window.set_default_size(400, 500)
            self.float_window.set_transient_for(self)
            
            # Remove panel from stack
            parent = files_panel.get_parent()
            if parent:
                parent.remove(files_panel)
            
            # Add to floating window
            self.float_window.add(files_panel)
            self.float_window.show_all()
            
            # Hide stack
            self.stack.set_visible(False)
            
            # Deactivate button
            self.master_palette.buttons['files'].set_active(False)
            
            files_panel.log_message("Panel DETACHED - floating as window")
            
            GLib.timeout_add(1000, self._float_test_sequence, 2)
            
        elif step == 2:
            # Step 3: Re-attach to stack
            print(f"[TEST] Float test step 3: Re-attach Files panel to stack")
            
            # Get Files panel
            files_panel = self.panels['files']
            
            # Remove from floating window
            self.float_window.remove(files_panel)
            self.float_window.destroy()
            self.float_window = None
            
            # Add back to stack
            self.stack.add_named(files_panel, 'files')
            
            # Show in stack
            self.master_palette.buttons['files'].set_active(True)
            
            files_panel.log_message("Panel RE-ATTACHED - back in stack")
            
            GLib.timeout_add(1000, self._float_test_sequence, 3)
            
        elif step == 3:
            # Step 4: Hide panel
            print(f"[TEST] Float test step 4: Hide Files panel")
            self.master_palette.buttons['files'].set_active(False)
            
            GLib.timeout_add(500, self._float_test_sequence, 4)
            
        elif step == 4:
            # Test complete
            print(f"[TEST] Float/Detach test COMPLETE")
            self.status_label.set_markup("<span color='green'>Status: Float/Detach Test PASSED ✅</span>")
            return False
        
        return False
    
    def _on_timeout(self):
        """Auto-exit after timeout (success)."""
        print(f"\n{'='*60}")
        print(f"[TEST] SUCCESS: No crash after {TEST_TIMEOUT}s")
        print(f"[TEST] Total switches: {self.switch_count}")
        print(f"[TEST] Wayland Error 71: NOT DETECTED ✅")
        print(f"{'='*60}\n")
        
        Gtk.main_quit()
        return False


def main():
    """Run GtkStack validation test."""
    
    print("\n" + "="*60)
    print("GtkStack Principle Validation Test")
    print("="*60)
    print("\nTesting:")
    print("  1. GtkStack with 4 heavy panels")
    print("  2. Rapid switching between panels")
    print("  3. set_no_show_all() with stack children")
    print("  4. FileChoosers, dialogs, ScrolledWindows in stack")
    print("  5. Master Palette control of stack visibility")
    print("\nCritical Success Criteria:")
    print("  ✅ NO Wayland Error 71")
    print("  ✅ Smooth panel switching")
    print("  ✅ Panels start hidden")
    print("  ✅ Exclusive panel visibility")
    print(f"\nAuto-exit in {TEST_TIMEOUT}s = SUCCESS\n")
    print("="*60 + "\n")
    
    # Create window
    window = TestWindow()
    window.show_all()
    
    # Hide stack initially (show_all() would reveal it)
    window.stack.set_visible(False)
    for panel in window.panels.values():
        panel.hide()
    
    # Run
    try:
        Gtk.main()
        sys.exit(0)  # Success
    except KeyboardInterrupt:
        print("\n[TEST] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[TEST] FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
