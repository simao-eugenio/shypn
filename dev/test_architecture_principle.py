#!/usr/bin/env python3
"""Test the CORE ARCHITECTURAL PRINCIPLE: Main window as a "hanger".

PRINCIPLE TO TEST:
- Main window = HANGER (empty GtkApplicationWindow)
- Panels = Independent GtkWindow instances that get "hanged" (attached/detached)
- Master Palette = ??? (What should it be?)
  
OPTIONS TO TEST:
1. Master Palette as GtkWindow (hanged like panels)
2. Master Palette as native widget in main window
3. Master Palette as GtkPopover
4. Master Palette as GtkHeaderBar toolbar

WAYLAND COMPATIBILITY:
- Which approach is Wayland Error 71 free?
- Can we attach/detach multiple GtkWindows without issues?
- Does the "hanger" pattern work reliably?

EXPECTED OUTCOME:
- Identify which widgets can be "hanged" safely
- Validate that independent windows work with Wayland
- Confirm attach/detach mechanism is sound
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk


class IndependentPanel:
    """Represents a panel as an independent GtkWindow that can be hanged."""
    
    def __init__(self, name, color, main_window=None, has_heavy_stuff=False):
        """Create an independent panel window."""
        print(f"[PANEL] Creating independent panel: {name} (heavy_stuff={has_heavy_stuff})")
        
        self.name = name
        self.main_window = main_window
        self.has_heavy_stuff = has_heavy_stuff
        
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title(f"{name} Panel (Independent)")
        self.window.set_default_size(300, 500)
        self.window.set_decorated(True)
        
        # Panel content
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content.set_margin_start(10)
        self.content.set_margin_end(10)
        self.content.set_margin_top(10)
        self.content.set_margin_bottom(10)
        
        # Visual indicator
        self.content.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(*color)
        )
        
        # Header
        label = Gtk.Label()
        label.set_markup(f"<big><b>{name} Panel</b></big>\n\n"
                        f"I am an independent GtkWindow\n"
                        f"that can be 'hanged' on the main window")
        label.set_line_wrap(True)
        self.content.pack_start(label, False, False, 0)
        
        # State indicator
        self.state_label = Gtk.Label()
        self.state_label.set_markup("<b>State:</b> <i>Floating</i>")
        self.content.pack_start(self.state_label, False, False, 0)
        
        # Add heavy stuff if requested
        if has_heavy_stuff:
            self._add_heavy_stuff()
        
        self.window.add(self.content)
        
        self.is_hanged = False
        self.parent_container = None
        
        self._update_state_label()
    
    def _add_heavy_stuff(self):
        """Add complex interactive widgets."""
        print(f"[PANEL] Adding heavy stuff to {self.name}...")
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content.pack_start(separator, False, False, 5)
        
        heavy_label = Gtk.Label()
        heavy_label.set_markup("<b>🔧 HEAVY OPERATIONS</b>")
        self.content.pack_start(heavy_label, False, False, 0)
        
        # File Chooser Button
        file_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        file_label = Gtk.Label(label="Select a file:")
        file_label.set_xalign(0)
        file_section.pack_start(file_label, False, False, 0)
        
        self.file_chooser_button = Gtk.FileChooserButton(
            title="Select a File",
            action=Gtk.FileChooserAction.OPEN
        )
        self.file_chooser_button.connect('file-set', self._on_file_selected)
        file_section.pack_start(self.file_chooser_button, False, False, 0)
        self.content.pack_start(file_section, False, False, 0)
        
        # Dialog Buttons
        dialog_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Info Dialog
        info_btn = Gtk.Button(label="📋 Open Info Dialog")
        info_btn.connect('clicked', self._on_open_info_dialog)
        dialog_box.pack_start(info_btn, False, False, 0)
        
        # Question Dialog
        question_btn = Gtk.Button(label="❓ Open Question Dialog")
        question_btn.connect('clicked', self._on_open_question_dialog)
        dialog_box.pack_start(question_btn, False, False, 0)
        
        # File Chooser Dialog
        open_file_btn = Gtk.Button(label="📂 Open File Dialog")
        open_file_btn.connect('clicked', self._on_open_file_dialog)
        dialog_box.pack_start(open_file_btn, False, False, 0)
        
        # Save File Dialog
        save_file_btn = Gtk.Button(label="💾 Save File Dialog")
        save_file_btn.connect('clicked', self._on_save_file_dialog)
        dialog_box.pack_start(save_file_btn, False, False, 0)
        
        # Color Chooser Dialog
        color_btn = Gtk.Button(label="🎨 Choose Color Dialog")
        color_btn.connect('clicked', self._on_choose_color_dialog)
        dialog_box.pack_start(color_btn, False, False, 0)
        
        self.content.pack_start(dialog_box, False, False, 0)
        
        # Interaction with Main Hanger
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content.pack_start(separator2, False, False, 5)
        
        interact_label = Gtk.Label()
        interact_label.set_markup("<b>🔗 MAIN HANGER INTERACTION</b>")
        self.content.pack_start(interact_label, False, False, 0)
        
        interact_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Send message to main window
        send_btn = Gtk.Button(label="📤 Send Message to Hanger")
        send_btn.connect('clicked', self._on_send_message)
        interact_box.pack_start(send_btn, False, False, 0)
        
        # Trigger action in main window
        action_btn = Gtk.Button(label="⚡ Trigger Hanger Action")
        action_btn.connect('clicked', self._on_trigger_action)
        interact_box.pack_start(action_btn, False, False, 0)
        
        # Get info from main window
        info_from_main_btn = Gtk.Button(label="📥 Get Info from Hanger")
        info_from_main_btn.connect('clicked', self._on_get_info_from_main)
        interact_box.pack_start(info_from_main_btn, False, False, 0)
        
        self.content.pack_start(interact_box, False, False, 0)
        
        # Message display area
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.content.pack_start(separator3, False, False, 5)
        
        msg_label = Gtk.Label(label="Messages:")
        msg_label.set_xalign(0)
        self.content.pack_start(msg_label, False, False, 0)
        
        # Scrolled window for messages
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(-1, 100)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.message_buffer = Gtk.TextBuffer()
        self.message_view = Gtk.TextView(buffer=self.message_buffer)
        self.message_view.set_editable(False)
        self.message_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.message_view)
        
        self.content.pack_start(scrolled, True, True, 0)
        
        self._log_message(f"{self.name} panel initialized with heavy stuff")
    
    def _get_parent_window(self):
        """Get the appropriate parent window for dialogs."""
        if self.is_hanged and self.main_window:
            return self.main_window
        else:
            return self.window
    
    def _log_message(self, message):
        """Log a message to the message buffer."""
        if hasattr(self, 'message_buffer'):
            end_iter = self.message_buffer.get_end_iter()
            self.message_buffer.insert(end_iter, f"[{self.name}] {message}\n")
            print(f"[PANEL-MSG] {self.name}: {message}")
    
    def _on_file_selected(self, widget):
        """Handle file selection from FileChooserButton."""
        filename = widget.get_filename()
        state = "HANGED" if self.is_hanged else "FLOATING"
        self._log_message(f"File selected ({state}): {filename}")
    
    def _on_open_info_dialog(self, button):
        """Open an info dialog."""
        state = "hanged on main window" if self.is_hanged else "floating independently"
        parent = self._get_parent_window()
        
        self._log_message(f"Opening info dialog (parent: {parent.get_title()})")
        
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f"{self.name} Panel Info"
        )
        dialog.format_secondary_text(
            f"This panel is currently {state}.\n\n"
            f"Dialogs are parented to: {parent.get_title()}\n"
            f"This ensures proper behavior in both states!"
        )
        
        response = dialog.run()
        self._log_message(f"Info dialog closed (response: {response})")
        dialog.destroy()
    
    def _on_open_question_dialog(self, button):
        """Open a question dialog."""
        parent = self._get_parent_window()
        
        self._log_message(f"Opening question dialog")
        
        dialog = Gtk.MessageDialog(
            transient_for=parent,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Test Question"
        )
        dialog.format_secondary_text(
            f"Panel state: {'HANGED' if self.is_hanged else 'FLOATING'}\n\n"
            f"Does this dialog work correctly?"
        )
        
        response = dialog.run()
        answer = "YES" if response == Gtk.ResponseType.YES else "NO"
        self._log_message(f"Question answered: {answer}")
        dialog.destroy()
    
    def _on_open_file_dialog(self, button):
        """Open a file chooser dialog."""
        parent = self._get_parent_window()
        
        self._log_message(f"Opening file chooser dialog")
        
        dialog = Gtk.FileChooserDialog(
            title="Open File",
            parent=parent,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self._log_message(f"File opened: {filename}")
        else:
            self._log_message(f"File dialog cancelled")
        
        dialog.destroy()
    
    def _on_save_file_dialog(self, button):
        """Open a save file dialog."""
        parent = self._get_parent_window()
        
        self._log_message(f"Opening save file dialog")
        
        dialog = Gtk.FileChooserDialog(
            title="Save File",
            parent=parent,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name("test_file.txt")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self._log_message(f"File saved: {filename}")
        else:
            self._log_message(f"Save dialog cancelled")
        
        dialog.destroy()
    
    def _on_choose_color_dialog(self, button):
        """Open a color chooser dialog."""
        parent = self._get_parent_window()
        
        self._log_message(f"Opening color chooser dialog")
        
        dialog = Gtk.ColorChooserDialog(
            title="Choose Color",
            parent=parent
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            color = dialog.get_rgba()
            self._log_message(f"Color chosen: R={color.red:.2f} G={color.green:.2f} B={color.blue:.2f}")
        else:
            self._log_message(f"Color dialog cancelled")
        
        dialog.destroy()
    
    def _on_send_message(self, button):
        """Send a message to main window."""
        state = "HANGED" if self.is_hanged else "FLOATING"
        self._log_message(f"Sending message to hanger (state: {state})")
        
        if self.main_window:
            self.main_window.receive_message_from_panel(self.name, f"Hello from {state} panel!")
        else:
            self._log_message("ERROR: No main window reference!")
    
    def _on_trigger_action(self, button):
        """Trigger an action in main window."""
        self._log_message(f"Triggering action in hanger")
        
        if self.main_window:
            self.main_window.panel_triggered_action(self.name)
        else:
            self._log_message("ERROR: No main window reference!")
    
    def _on_get_info_from_main(self, button):
        """Get info from main window."""
        self._log_message(f"Requesting info from hanger")
        
        if self.main_window:
            info = self.main_window.get_info_for_panel(self.name)
            self._log_message(f"Received info: {info}")
        else:
            self._log_message("ERROR: No main window reference!")
    
    def _update_state_label(self):
        """Update the state indicator label."""
        if hasattr(self, 'state_label'):
            state = "HANGED" if self.is_hanged else "FLOATING"
            parent = "Main Window" if self.is_hanged else "Independent Window"
            self.state_label.set_markup(f"<b>State:</b> <i>{state}</i> | <b>Parent:</b> <i>{parent}</i>")
    
    def hang_on(self, container):
        """Hang this panel on a container (attach)."""
        print(f"[PANEL] Hanging {self.name} on container...")
        
        if self.is_hanged:
            print(f"[PANEL] {self.name} already hanged, just showing")
            if not self.content.get_visible():
                self.content.show_all()
            return
        
        # Hide independent window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Hang content on container
        container.pack_start(self.content, True, True, 0)
        self.content.show_all()
        
        self.is_hanged = True
        self.parent_container = container
        self._update_state_label()
        
        if self.has_heavy_stuff:
            self._log_message(f"Panel hanged on main window")
        
        print(f"[PANEL] {self.name} hanged successfully")
    
    def hide(self):
        """Hide the panel (keep hanged but invisible)."""
        print(f"[PANEL] Hiding {self.name} panel...")
        
        if self.is_hanged and self.parent_container:
            # Hide content while keeping it hanged
            self.content.set_no_show_all(True)  # Prevent show_all from revealing it
            self.content.hide()
            if self.has_heavy_stuff:
                self._log_message(f"Panel hidden (still hanged)")
            print(f"[PANEL] {self.name} hidden (still hanged)")
        else:
            # Hide floating window
            self.window.hide()
            if self.has_heavy_stuff:
                self._log_message(f"Panel window hidden")
            print(f"[PANEL] {self.name} window hidden")
    
    def show(self):
        """Show the panel (reveal if hanged, show window if floating)."""
        print(f"[PANEL] Showing {self.name} panel...")
        
        if self.is_hanged and self.parent_container:
            # Re-enable show_all and show content (reveal)
            self.content.set_no_show_all(False)
            self.content.show_all()
            if self.has_heavy_stuff:
                self._log_message(f"Panel revealed")
            print(f"[PANEL] {self.name} revealed (hanged)")
        else:
            # Show floating window
            self.window.show_all()
            if self.has_heavy_stuff:
                self._log_message(f"Panel window shown")
            print(f"[PANEL] {self.name} window shown")
    
    def detach(self):
        """Detach from container and restore as independent window."""
        print(f"[PANEL] Detaching {self.name} from hanger...")
        
        if not self.is_hanged:
            print(f"[PANEL] {self.name} already detached")
            return
        
        # Remove from container
        if self.parent_container:
            self.parent_container.remove(self.content)
        
        # Return content to independent window
        self.window.add(self.content)
        self.window.show_all()
        
        self.is_hanged = False
        self.parent_container = None
        self._update_state_label()
        
        if self.has_heavy_stuff:
            self._log_message(f"Panel detached to floating window")
        
        print(f"[PANEL] {self.name} detached successfully")
    
    def float_as_window(self):
        """Show as floating independent window."""
        print(f"[PANEL] Floating {self.name} as independent window...")
        if not self.is_hanged:
            self.window.show_all()
        else:
            print(f"[PANEL] {self.name} is hanged, use detach() first")


class MasterPaletteOption1:
    """Master Palette as independent GtkWindow (like panels)."""
    
    def __init__(self):
        print("[MP-OPT1] Creating Master Palette as independent GtkWindow...")
        
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Master Palette (Independent Window)")
        self.window.set_default_size(200, 400)
        self.window.set_decorated(True)
        
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.set_margin_start(5)
        self.content.set_margin_end(5)
        self.content.set_margin_top(5)
        self.content.set_margin_bottom(5)
        
        label = Gtk.Label(label="Master Palette\n(Independent Window)")
        self.content.pack_start(label, False, False, 0)
        
        # Store buttons for external access
        self.buttons = {}
        
        # Buttons
        for name in ['Files', 'Pathways', 'Analyses', 'Topology']:
            btn = Gtk.ToggleButton(label=name)
            btn.set_size_request(48, 48)
            self.buttons[name.lower()] = btn
            self.content.pack_start(btn, False, False, 0)
        
        self.window.add(self.content)
        
        self.is_hanged = False
        self.parent_container = None
        self.callbacks = {}
    
    def connect(self, signal_name, callback):
        """Connect a callback to a button signal."""
        if signal_name in self.buttons:
            self.callbacks[signal_name] = callback
            self.buttons[signal_name].connect('toggled', lambda btn: callback(btn.get_active()))
            print(f"[MP-OPT1] Connected callback for '{signal_name}' button")
    
    def hang_on(self, container):
        """Hang palette on container."""
        print("[MP-OPT1] Hanging Master Palette on container...")
        
        if self.is_hanged:
            return
        
        self.window.hide()
        self.window.remove(self.content)
        
        container.pack_start(self.content, False, False, 0)
        self.content.show_all()
        
        self.is_hanged = True
        self.parent_container = container
        print("[MP-OPT1] Master Palette hanged")


class MasterPaletteOption2:
    """Master Palette as native widget (no independent window)."""
    
    def __init__(self):
        print("[MP-OPT2] Creating Master Palette as native widget...")
        
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.set_margin_start(5)
        self.content.set_margin_end(5)
        self.content.set_margin_top(5)
        self.content.set_margin_bottom(5)
        
        # Background
        self.content.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0.9, 0.9, 0.9, 1.0)
        )
        
        label = Gtk.Label(label="Master Palette\n(Native Widget)")
        self.content.pack_start(label, False, False, 0)
        
        # Store buttons for external access
        self.buttons = {}
        
        # Buttons
        for name in ['Files', 'Pathways', 'Analyses', 'Topology']:
            btn = Gtk.ToggleButton(label=name)
            btn.set_size_request(48, 48)
            self.buttons[name.lower()] = btn
            self.content.pack_start(btn, False, False, 0)
        
        self.callbacks = {}
    
    def connect(self, signal_name, callback):
        """Connect a callback to a button signal."""
        if signal_name in self.buttons:
            self.callbacks[signal_name] = callback
            self.buttons[signal_name].connect('toggled', lambda btn: callback(btn.get_active()))
            print(f"[MP-OPT2] Connected callback for '{signal_name}' button")
    
    def get_widget(self):
        """Get the widget to pack directly."""
        return self.content


class TestWindow(Gtk.ApplicationWindow):
    """Main window as HANGER - tests different hanging strategies."""
    
    def __init__(self, app, test_mode):
        super().__init__(application=app, title=f"Architecture Test - {test_mode}")
        self.set_default_size(1400, 700)
        
        self.test_mode = test_mode
        self.panel_messages = []
        
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Title area
        title = Gtk.Label()
        title.set_markup(f"<big><b>ARCHITECTURE PRINCIPLE TEST: {test_mode}</b></big>\n"
                        f"<small>Main window = HANGER. Everything else can be attached/detached.</small>")
        title.set_margin_top(10)
        title.set_margin_bottom(10)
        main_box.pack_start(title, False, False, 0)
        
        # Hanger area (horizontal: left slot, content area, right slot)
        hanger = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.pack_start(hanger, True, True, 0)
        
        # LEFT SLOT: For Master Palette (if hanged)
        self.left_slot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.left_slot.set_size_request(0, -1)  # Start collapsed
        hanger.pack_start(self.left_slot, False, False, 0)
        
        # CONTENT AREA: For panels
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        hanger.pack_start(content_paned, True, True, 0)
        
        # Panel slot 1
        self.panel_slot1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.panel_slot1.set_size_request(0, -1)
        content_paned.pack1(self.panel_slot1, False, False)
        
        # Canvas area
        canvas = Gtk.Label(label="CANVAS AREA\n(Drawing area)")
        canvas.set_vexpand(True)
        canvas.set_hexpand(True)
        canvas.override_background_color(
            Gtk.StateFlags.NORMAL,
            Gdk.RGBA(0.95, 0.95, 0.95, 1.0)
        )
        content_paned.pack2(canvas, True, False)
        
        # RIGHT SLOT: Reserved
        self.right_slot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.right_slot.set_size_request(0, -1)
        hanger.pack_start(self.right_slot, False, False, 0)
        
        # Control panel
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls.set_margin_start(10)
        controls.set_margin_end(10)
        controls.set_margin_top(10)
        controls.set_margin_bottom(10)
        main_box.pack_start(controls, False, False, 0)
        
        # Hanger message area
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(separator, False, False, 0)
        
        msg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        msg_box.set_margin_start(10)
        msg_box.set_margin_end(10)
        msg_box.set_margin_top(5)
        msg_box.set_margin_bottom(5)
        
        msg_label = Gtk.Label(label="Hanger Messages:")
        msg_label.set_xalign(0)
        msg_box.pack_start(msg_label, False, False, 0)
        
        self.hanger_message_label = Gtk.Label()
        self.hanger_message_label.set_markup("<i>No messages yet</i>")
        self.hanger_message_label.set_line_wrap(True)
        self.hanger_message_label.set_xalign(0)
        msg_box.pack_start(self.hanger_message_label, False, False, 0)
        
        main_box.pack_start(msg_box, False, False, 0)
        
        # Create test subjects based on mode
        self.setup_test_mode(controls)
        
        print(f"[TEST] Architecture test ready: {test_mode}")
    
    def receive_message_from_panel(self, panel_name, message):
        """Receive a message from a panel."""
        print(f"[HANGER] Message from {panel_name}: {message}")
        self.panel_messages.append(f"{panel_name}: {message}")
        self._update_hanger_messages()
    
    def panel_triggered_action(self, panel_name):
        """Handle action triggered by a panel."""
        print(f"[HANGER] Action triggered by {panel_name}")
        
        # Show a dialog from the main window
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Hanger Action Triggered"
        )
        dialog.format_secondary_text(
            f"The {panel_name} panel triggered an action in the main hanger!\n\n"
            f"This demonstrates two-way communication between panels and hanger."
        )
        dialog.run()
        dialog.destroy()
        
        self.panel_messages.append(f"{panel_name} triggered action → Hanger responded")
        self._update_hanger_messages()
    
    def get_info_for_panel(self, panel_name):
        """Provide info to a panel."""
        print(f"[HANGER] Info requested by {panel_name}")
        
        info = {
            "hanger_title": self.get_title(),
            "hanger_size": self.get_size(),
            "total_panels": len([p for p in [getattr(self, 'panel1', None), 
                                              getattr(self, 'panel2', None)] if p]),
            "messages_received": len(self.panel_messages)
        }
        
        self.panel_messages.append(f"{panel_name} requested info → Hanger provided")
        self._update_hanger_messages()
        
        return info
    
    def _update_hanger_messages(self):
        """Update the hanger message display."""
        if len(self.panel_messages) == 0:
            self.hanger_message_label.set_markup("<i>No messages yet</i>")
        else:
            # Show last 3 messages
            recent = self.panel_messages[-3:]
            text = "\n".join(f"• {msg}" for msg in recent)
            if len(self.panel_messages) > 3:
                text = f"<small>(showing last 3 of {len(self.panel_messages)})</small>\n" + text
            self.hanger_message_label.set_markup(text)
    
    def setup_test_mode(self, controls):
        """Setup test based on selected mode."""
        
        if self.test_mode == "MODE 1: Palette as Independent Window":
            self.setup_mode1(controls)
        elif self.test_mode == "MODE 2: Palette as Native Widget":
            self.setup_mode2(controls)
        elif self.test_mode == "MODE 3: Everything as Independent Windows":
            self.setup_mode3(controls)
    
    def setup_mode1(self, controls):
        """Test Master Palette as independent window (hanged)."""
        print("\n[TEST] === MODE 1: Master Palette as Independent Window ===")
        
        # Create Master Palette as independent window
        self.master_palette = MasterPaletteOption1()
        
        # Create a HEAVY panel with dialogs and interactions
        self.panel1 = IndependentPanel("Files", (0.8, 0.9, 1.0, 1.0), 
                                       main_window=self, has_heavy_stuff=True)
        
        # Hang panel on startup but HIDE it
        self.panel1.hang_on(self.panel_slot1)
        self.panel1.content.set_no_show_all(True)  # Prevent show_all from revealing it
        self.panel1.hide()  # Start hidden
        print("[TEST] Files panel hanged but HIDDEN on startup")
        
        # Wire Master Palette Files button to REVEAL/HIDE panel
        def on_files_toggled(active):
            print(f"[MP] Files button toggled: {active}")
            if active:
                print("[MP] → REVEALING Files panel...")
                if not self.panel1.is_hanged:
                    self.panel1.hang_on(self.panel_slot1)
                self.panel1.show()
            else:
                print("[MP] → HIDING Files panel...")
                self.panel1.hide()
        
        self.master_palette.connect('files', on_files_toggled)
        
        # Buttons
        btn1 = Gtk.Button(label="Hang Master Palette")
        btn1.connect('clicked', lambda b: self.master_palette.hang_on(self.left_slot))
        controls.pack_start(btn1, False, False, 0)
        
        btn2 = Gtk.Button(label="Manual: Show Files")
        btn2.connect('clicked', lambda b: (
            self.panel1.show(),
            self.master_palette.buttons['files'].set_active(True)
        ))
        controls.pack_start(btn2, False, False, 0)
        
        btn3 = Gtk.Button(label="Manual: Hide Files")
        btn3.connect('clicked', lambda b: (
            self.panel1.hide(),
            self.master_palette.buttons['files'].set_active(False)
        ))
        controls.pack_start(btn3, False, False, 0)
        
        btn4 = Gtk.Button(label="⚡ Rapid Test (10x)")
        btn4.connect('clicked', self.rapid_test_mode1)
        controls.pack_start(btn4, False, False, 0)
        
        # Auto-hang Master Palette but leave panel hidden
        GLib.timeout_add(1000, lambda: (
            print("\n[TEST] AUTO-HANGING Master Palette..."),
            self.master_palette.hang_on(self.left_slot),
            print("[TEST] Click 'Files' button to REVEAL panel"),
            False
        ))
    
    def setup_mode2(self, controls):
        """Test Master Palette as native widget (no window)."""
        print("\n[TEST] === MODE 2: Master Palette as Native Widget ===")
        
        # Create Master Palette as native widget
        self.master_palette = MasterPaletteOption2()
        self.left_slot.pack_start(self.master_palette.get_widget(), False, False, 0)
        
        # Create a HEAVY panel with dialogs and interactions
        self.panel1 = IndependentPanel("Files", (0.8, 0.9, 1.0, 1.0),
                                       main_window=self, has_heavy_stuff=True)
        
        # Hang panel on startup but HIDE it (button will reveal it)
        self.panel1.hang_on(self.panel_slot1)
        self.panel1.content.set_no_show_all(True)  # Prevent show_all from revealing it
        self.panel1.hide()  # Start hidden
        print("[TEST] Files panel hanged but HIDDEN on startup")
        
        # Wire Master Palette Files button to REVEAL/HIDE Files panel
        def on_files_toggled(active):
            print(f"\n[MP] ========== FILES BUTTON CLICKED ==========")
            print(f"[MP] Button state: {'PRESSED (ON)' if active else 'RELEASED (OFF)'}")
            if active:
                print("[MP] → REVEALING Files panel (sliding to the right)...")
                # First ensure it's hanged
                if not self.panel1.is_hanged:
                    self.panel1.hang_on(self.panel_slot1)
                # Then show it (reveal)
                self.panel1.show()
                print("[MP] ✓ Files panel REVEALED")
            else:
                print("[MP] → HIDING Files panel...")
                self.panel1.hide()
                print("[MP] ✓ Files panel HIDDEN")
            print(f"[MP] ==========================================\n")
        
        self.master_palette.connect('files', on_files_toggled)
        
        # Buttons
        btn1 = Gtk.Button(label="Manual: Show Files Panel")
        btn1.connect('clicked', lambda b: (
            self.panel1.show(),
            self.master_palette.buttons['files'].set_active(True)
        ))
        controls.pack_start(btn1, False, False, 0)
        
        btn2 = Gtk.Button(label="Manual: Hide Files Panel")
        btn2.connect('clicked', lambda b: (
            self.panel1.hide(),
            self.master_palette.buttons['files'].set_active(False)
        ))
        controls.pack_start(btn2, False, False, 0)
        
        btn3 = Gtk.Button(label="⚡ Rapid Test (10x)")
        btn3.connect('clicked', self.rapid_test_mode2)
        controls.pack_start(btn3, False, False, 0)
        
        # Don't auto-activate - let user click Files button to reveal
        print("[TEST] Click 'Files' button in Master Palette to REVEAL panel")
    
    def setup_mode3(self, controls):
        """Test everything as independent windows."""
        print("\n[TEST] === MODE 3: Everything as Independent Windows ===")
        
        # Master Palette as independent window (not hanged initially)
        self.master_palette = MasterPaletteOption1()
        
        # Multiple panels - one HEAVY with dialogs, one simple
        self.panel1 = IndependentPanel("Files", (0.8, 0.9, 1.0, 1.0),
                                       main_window=self, has_heavy_stuff=True)
        self.panel2 = IndependentPanel("Pathways", (0.9, 1.0, 0.8, 1.0),
                                       main_window=self, has_heavy_stuff=False)
        
        # Wire Master Palette Files button
        def on_files_toggled(active):
            print(f"[MP] Files button toggled: {active}")
            if active:
                print("[MP] → Hanging Files panel...")
                self.panel1.hang_on(self.panel_slot1)
            else:
                print("[MP] → Detaching Files panel...")
                self.panel1.detach()
        
        self.master_palette.connect('files', on_files_toggled)
        
        # Buttons
        btn1 = Gtk.Button(label="Show MP as Window")
        btn1.connect('clicked', lambda b: self.master_palette.window.show_all())
        controls.pack_start(btn1, False, False, 0)
        
        btn2 = Gtk.Button(label="Hang MP on Main")
        btn2.connect('clicked', lambda b: self.master_palette.hang_on(self.left_slot))
        controls.pack_start(btn2, False, False, 0)
        
        btn3 = Gtk.Button(label="Show Files (Heavy)")
        btn3.connect('clicked', lambda b: self.panel1.float_as_window())
        controls.pack_start(btn3, False, False, 0)
        
        btn4 = Gtk.Button(label="Manual: Toggle Files via MP")
        btn4.connect('clicked', lambda b: self.master_palette.buttons['files'].set_active(
            not self.master_palette.buttons['files'].get_active()
        ))
        controls.pack_start(btn4, False, False, 0)
        
        btn5 = Gtk.Button(label="Show Pathways (Simple)")
        btn5.connect('clicked', lambda b: self.panel2.float_as_window())
        controls.pack_start(btn5, False, False, 0)
        
        btn6 = Gtk.Button(label="⚡ Rapid Test All (10x)")
        btn6.connect('clicked', self.rapid_test_mode3)
        controls.pack_start(btn6, False, False, 0)
        
        # Auto-show all as windows after 1 second
        GLib.timeout_add(1000, lambda: (
            print("\n[TEST] AUTO-SHOWING Master Palette and panels as independent windows..."),
            self.master_palette.window.show_all(),
            self.panel1.float_as_window(),
            self.panel2.float_as_window(),
            False
        ))
    
    def rapid_test_mode1(self, button):
        """Rapid attach/detach test for Mode 1 using Master Palette."""
        print("\n[TEST] ========== RAPID TEST MODE 1 START ==========")
        button.set_sensitive(False)
        
        count = [0]
        max_cycles = 10
        
        def do_cycle():
            if count[0] >= max_cycles:
                button.set_sensitive(True)
                print(f"[TEST] ========== RAPID TEST COMPLETE ({max_cycles} cycles) ==========\n")
                return False
            
            count[0] += 1
            # Toggle via Master Palette button
            is_active = self.master_palette.buttons['files'].get_active()
            print(f"[TEST] Cycle {count[0]}/{max_cycles} - Toggling Files button to {not is_active}...")
            self.master_palette.buttons['files'].set_active(not is_active)
            
            return True
        
        GLib.timeout_add(300, do_cycle)
    
    def rapid_test_mode2(self, button):
        """Rapid attach/detach test for Mode 2 using Master Palette."""
        print("\n[TEST] ========== RAPID TEST MODE 2 START ==========")
        button.set_sensitive(False)
        
        count = [0]
        max_cycles = 10
        
        def do_cycle():
            if count[0] >= max_cycles:
                button.set_sensitive(True)
                print(f"[TEST] ========== RAPID TEST COMPLETE ({max_cycles} cycles) ==========\n")
                return False
            
            count[0] += 1
            # Toggle via Master Palette button
            is_active = self.master_palette.buttons['files'].get_active()
            print(f"[TEST] Cycle {count[0]}/{max_cycles} - Toggling Files button to {not is_active}...")
            self.master_palette.buttons['files'].set_active(not is_active)
            
            return True
        
        GLib.timeout_add(300, do_cycle)
    
    def rapid_test_mode3(self, button):
        """Rapid hang/detach test for Mode 3."""
        print("\n[TEST] ========== RAPID TEST MODE 3 START ==========")
        button.set_sensitive(False)
        
        count = [0]
        max_cycles = 10
        
        def do_cycle():
            if count[0] >= max_cycles:
                button.set_sensitive(True)
                print(f"[TEST] ========== RAPID TEST COMPLETE ({max_cycles} cycles) ==========\n")
                return False
            
            count[0] += 1
            
            # Cycle: hang both → detach both → hang both...
            if count[0] % 2 == 1:
                print(f"[TEST] Cycle {count[0]}/{max_cycles} - Hanging all...")
                self.master_palette.hang_on(self.left_slot)
                self.panel1.hang_on(self.panel_slot1)
            else:
                print(f"[TEST] Cycle {count[0]}/{max_cycles} - Detaching all...")
                self.panel1.detach()
                # Note: Can't detach MP back to window in current implementation
            
            return True
        
        GLib.timeout_add(300, do_cycle)


class TestApplication(Gtk.Application):
    """Test application with mode selection."""
    
    def __init__(self, test_mode):
        super().__init__(application_id='org.shypn.test.architecture')
        self.test_mode = test_mode
    
    def do_activate(self):
        """Activate the application."""
        win = TestWindow(self, self.test_mode)
        win.show_all()


def main():
    """Run the test application."""
    print("=" * 80)
    print("ARCHITECTURE PRINCIPLE TEST")
    print("=" * 80)
    print("\nCONCEPT: Main window = HANGER (empty container)")
    print("         Panels = Independent GtkWindows that 'hang' on the hanger")
    print("         Master Palette = ??? (What should it be?)")
    print("\nTEST MODES:")
    print("  1) Master Palette as Independent Window (hanged like panels)")
    print("  2) Master Palette as Native Widget (no window)")
    print("  3) Everything as Independent Windows (full flexibility)")
    print("\nWATCH FOR: Gdk-Message: Error 71 (Protocol error)")
    print("=" * 80)
    
    # Select mode
    if len(sys.argv) > 1:
        mode_num = sys.argv[1]
    else:
        print("\nUsage: ./test_architecture_principle.py [1|2|3]")
        print("Running all modes sequentially...\n")
        mode_num = "2"  # Default to Mode 2 (most likely correct)
    
    modes = {
        "1": "MODE 1: Palette as Independent Window",
        "2": "MODE 2: Palette as Native Widget",
        "3": "MODE 3: Everything as Independent Windows"
    }
    
    test_mode = modes.get(mode_num, modes["2"])
    print(f"\n>>> TESTING: {test_mode}\n")
    
    app = TestApplication(test_mode)
    return app.run([])


if __name__ == '__main__':
    sys.exit(main())
