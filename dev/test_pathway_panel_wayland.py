#!/usr/bin/env python3
"""Test Pathway Panel for Wayland issues.

This script loads ONLY the Pathway panel to isolate Wayland Error 71 issues.
Tests attach/detach/float operations in a minimal environment.

NEW: Tests unified UI with radio buttons (External/Local) and normalized tabs.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.pathway_panel_loader import create_pathway_panel


class TestWindow(Gtk.ApplicationWindow):
    """Minimal test window for Pathway panel."""
    
    def __init__(self, app):
        super().__init__(application=app, title="Pathway Panel Wayland Test")
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
        title.set_markup("<big><b>Pathway Panel Wayland Test</b></big>")
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
        
        # Load Pathway Panel
        print("[TEST] Loading Pathway panel...")
        self.pathway_panel = create_pathway_panel()
        # Note: parent_window is set via attach_to() call
        
        # Initially attach the panel
        print("[TEST] Attaching panel...")
        self.pathway_panel.attach_to(left_container, self)
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
        
        # NEW: Tab and Radio Button Tests
        ui_label = Gtk.Label()
        ui_label.set_markup("<b>UI Interaction Tests:</b>")
        ui_label.set_xalign(0)
        button_box.pack_start(ui_label, False, False, 0)
        
        self.tab_cycle_button = Gtk.Button(label="📑 Cycle Tabs (KEGG→SBML→BRENDA)")
        self.tab_cycle_button.connect('clicked', self.on_tab_cycle)
        button_box.pack_start(self.tab_cycle_button, False, False, 0)
        
        self.radio_toggle_button = Gtk.Button(label="🔘 Toggle Radio Buttons")
        self.radio_toggle_button.connect('clicked', self.on_radio_toggle)
        button_box.pack_start(self.radio_toggle_button, False, False, 0)
        
        self.stress_ui_button = Gtk.Button(label="⚡ Stress UI (tabs+radios)")
        self.stress_ui_button.connect('clicked', self.on_stress_ui)
        button_box.pack_start(self.stress_ui_button, False, False, 0)
        
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
            self.pathway_panel.unattach()
            self.panel_attached = False
            button.set_label("🔗 Attach Panel")
            self.status_label.set_markup("<i>Status: Panel detached</i>")
        else:
            print("[TEST] Attaching panel...")
            self.pathway_panel.attach_to(self.left_container, self)
            self.panel_attached = True
            button.set_label("🔗 Detach Panel")
            self.status_label.set_markup("<i>Status: Panel attached</i>")
        print("[TEST] ========== Toggle Complete ==========\n")
    
    def on_float(self, button):
        """Float the panel."""
        print("\n[TEST] ========== Float Panel ==========")
        self.pathway_panel.float(self)
        self.panel_attached = False
        self.attach_button.set_label("🔗 Attach Panel")
        self.status_label.set_markup("<i>Status: Panel floating</i>")
        print("[TEST] ========== Float Complete ==========\n")
    
    def on_hide(self, button):
        """Hide the panel."""
        print("\n[TEST] ========== Hide Panel ==========")
        self.pathway_panel.hide()
        self.status_label.set_markup("<i>Status: Panel hidden</i>")
        print("[TEST] ========== Hide Complete ==========\n")
    
    def on_show(self, button):
        """Show the panel (re-attach if needed)."""
        print("\n[TEST] ========== Show Panel ==========")
        if not self.panel_attached:
            self.pathway_panel.attach_to(self.left_container, self)
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
                self.pathway_panel.unattach()
                self.panel_attached = False
            else:
                self.pathway_panel.attach_to(self.left_container, self)
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
                    self.pathway_panel.attach_to(self.left_container, self)
                    self.panel_attached = True
                state[0] = 'hide'
            else:
                print(f"[TEST] Cycle {count[0]}/{max_cycles} - Hide...")
                self.pathway_panel.hide()
                state[0] = 'attach'
            
            return True
        
        # Schedule cycles with 150ms delay between each operation
        GLib.timeout_add(150, do_cycle)
    
    def on_tab_cycle(self, button):
        """Cycle through tabs to test notebook switching."""
        print("\n[TEST] ========== TAB CYCLE TEST START ==========")
        button.set_sensitive(False)
        self.status_label.set_markup("<i>Status: <b>Cycling through tabs...</b></i>")
        
        # Get notebook from pathway panel
        notebook = self.pathway_panel.builder.get_object('pathway_notebook')
        if not notebook:
            print("[TEST] ERROR: Could not find pathway_notebook!")
            button.set_sensitive(True)
            return
        
        count = [0]
        max_cycles = 3
        num_pages = notebook.get_n_pages()
        
        def do_tab_switch():
            if count[0] >= max_cycles * num_pages:
                button.set_sensitive(True)
                self.status_label.set_markup(f"<i>Status: Tab cycle complete ({max_cycles} cycles)</i>")
                print(f"[TEST] ========== TAB CYCLE TEST COMPLETE ==========\n")
                return False
            
            page_index = count[0] % num_pages
            page = notebook.get_nth_page(page_index)
            tab_label = notebook.get_tab_label_text(page) if page else "Unknown"
            
            print(f"[TEST] Switching to tab {page_index}: {tab_label}")
            notebook.set_current_page(page_index)
            count[0] += 1
            
            return True
        
        # Schedule tab switches with 300ms delay
        GLib.timeout_add(300, do_tab_switch)
    
    def on_radio_toggle(self, button):
        """Toggle radio buttons between External/Local on all tabs."""
        print("\n[TEST] ========== RADIO BUTTON TOGGLE TEST ==========")
        button.set_sensitive(False)
        self.status_label.set_markup("<i>Status: <b>Toggling radio buttons...</b></i>")
        
        # Get radio buttons for all tabs
        builder = self.pathway_panel.builder
        radio_pairs = [
            ('kegg_external_radio', 'kegg_local_radio', 'KEGG'),
            ('sbml_external_radio', 'sbml_local_radio', 'SBML'),
            ('brenda_external_radio', 'brenda_local_radio', 'BRENDA')
        ]
        
        count = [0]
        max_toggles = 10
        
        def do_toggle():
            if count[0] >= max_toggles:
                button.set_sensitive(True)
                self.status_label.set_markup(f"<i>Status: Radio toggle complete ({max_toggles} toggles)</i>")
                print(f"[TEST] ========== RADIO TOGGLE TEST COMPLETE ==========\n")
                return False
            
            count[0] += 1
            
            # Toggle all radio buttons
            for external_id, local_id, tab_name in radio_pairs:
                external_radio = builder.get_object(external_id)
                local_radio = builder.get_object(local_id)
                
                if external_radio and local_radio:
                    # Toggle: if external is active, activate local
                    if external_radio.get_active():
                        print(f"[TEST] {tab_name}: External → Local")
                        local_radio.set_active(True)
                    else:
                        print(f"[TEST] {tab_name}: Local → External")
                        external_radio.set_active(True)
            
            return True
        
        # Schedule toggles with 200ms delay
        GLib.timeout_add(200, do_toggle)
    
    def on_stress_ui(self, button):
        """Stress test: rapidly cycle tabs AND toggle radios."""
        print("\n[TEST] ========== UI STRESS TEST START ==========")
        button.set_sensitive(False)
        self.status_label.set_markup("<i>Status: <b>Running UI stress test...</b></i>")
        
        # Get notebook and radio buttons
        notebook = self.pathway_panel.builder.get_object('pathway_notebook')
        builder = self.pathway_panel.builder
        radio_pairs = [
            ('kegg_external_radio', 'kegg_local_radio'),
            ('sbml_external_radio', 'sbml_local_radio'),
            ('brenda_external_radio', 'brenda_local_radio')
        ]
        
        if not notebook:
            print("[TEST] ERROR: Could not find pathway_notebook!")
            button.set_sensitive(True)
            return
        
        count = [0]
        max_operations = 30
        num_pages = notebook.get_n_pages()
        
        def do_stress_operation():
            if count[0] >= max_operations:
                button.set_sensitive(True)
                self.status_label.set_markup(f"<i>Status: UI stress test complete ({max_operations} ops)</i>")
                print(f"[TEST] ========== UI STRESS TEST COMPLETE ==========\n")
                return False
            
            count[0] += 1
            operation = count[0] % 2
            
            if operation == 0:
                # Switch tab
                page_index = (count[0] // 2) % num_pages
                page = notebook.get_nth_page(page_index)
                tab_label = notebook.get_tab_label_text(page) if page else "Unknown"
                print(f"[TEST] Op {count[0]}: Switch to tab {tab_label}")
                notebook.set_current_page(page_index)
            else:
                # Toggle radios on current tab
                current_page = notebook.get_current_page()
                if current_page < len(radio_pairs):
                    external_id, local_id = radio_pairs[current_page]
                    external_radio = builder.get_object(external_id)
                    local_radio = builder.get_object(local_id)
                    
                    if external_radio and local_radio:
                        if external_radio.get_active():
                            print(f"[TEST] Op {count[0]}: Toggle radio External → Local")
                            local_radio.set_active(True)
                        else:
                            print(f"[TEST] Op {count[0]}: Toggle radio Local → External")
                            external_radio.set_active(True)
            
            return True
        
        # Schedule operations with 100ms delay (rapid!)
        GLib.timeout_add(100, do_stress_operation)


class TestApplication(Gtk.Application):
    """Test application."""
    
    def __init__(self):
        super().__init__(application_id='org.shypn.test.pathwaypanel')
    
    def do_activate(self):
        """Activate the application."""
        win = TestWindow(self)
        win.show_all()


def main():
    """Run the test application."""
    print("=" * 70)
    print("Pathway Panel Wayland Test - UNIFIED UI VERSION")
    print("=" * 70)
    print("Tests:")
    print("  • Attach/Detach operations")
    print("  • Float/Hide/Show operations")
    print("  • Tab switching (KEGG, SBML, BRENDA)")
    print("  • Radio button toggling (External/Local)")
    print("  • UI stress tests (combined operations)")
    print()
    print("Watch for: Gdk-Message: Error 71 (Protocol error)")
    print("=" * 70)
    print()
    
    app = TestApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
