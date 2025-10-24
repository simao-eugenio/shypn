#!/usr/bin/env python3
"""Test Pathway Panel UI Elements (Unified Interface).

Focused test for:
- Tab notebook (KEGG, SBML, BRENDA)
- Radio buttons (External/Local) on each tab
- Dynamic box visibility toggling
- Browse button functionality

Minimal test to verify the normalized UI works correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.helpers.pathway_panel_loader import create_pathway_panel


class UITestWindow(Gtk.Window):
    """Test window for UI element verification."""
    
    def __init__(self):
        super().__init__(title="Pathway Panel UI Elements Test")
        self.set_default_size(800, 700)
        
        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        self.add(vbox)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>Pathway Panel - Unified UI Test</b></big>")
        vbox.pack_start(title, False, False, 0)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<small>Verify that the unified UI elements work correctly:\n"
            "1. All three tabs visible (KEGG, SBML, BRENDA)\n"
            "2. Radio buttons toggle External/Local boxes\n"
            "3. Action buttons respond correctly</small>"
        )
        instructions.set_line_wrap(True)
        vbox.pack_start(instructions, False, False, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 5)
        
        # Load pathway panel
        print("[UI_TEST] Loading Pathway panel...")
        self.pathway_panel = create_pathway_panel()
        
        # Create container and attach
        panel_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pathway_panel.attach_to(panel_container, self)
        vbox.pack_start(panel_container, True, True, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 5)
        
        # Test controls
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vbox.pack_start(control_box, False, False, 0)
        
        # Widget verification section
        verify_button = Gtk.Button(label="🔍 Verify All Widgets")
        verify_button.connect('clicked', self.on_verify_widgets)
        control_box.pack_start(verify_button, False, False, 0)
        
        test_radios_button = Gtk.Button(label="🔘 Test Radio Buttons")
        test_radios_button.connect('clicked', self.on_test_radios)
        control_box.pack_start(test_radios_button, False, False, 0)
        
        test_tabs_button = Gtk.Button(label="📑 Test Tab Switching")
        test_tabs_button.connect('clicked', self.on_test_tabs)
        control_box.pack_start(test_tabs_button, False, False, 0)
        
        # Results display
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(-1, 150)
        vbox.pack_start(scrolled, False, True, 0)
        
        self.results_view = Gtk.TextView()
        self.results_view.set_editable(False)
        self.results_view.set_monospace(True)
        self.results_buffer = self.results_view.get_buffer()
        scrolled.add(self.results_view)
        
        print("[UI_TEST] Test window ready!")
        
        # Auto-verify on startup
        GLib.timeout_add(500, self.on_verify_widgets, None)
    
    def log(self, message):
        """Log message to results view."""
        end_iter = self.results_buffer.get_end_iter()
        self.results_buffer.insert(end_iter, message + "\n")
        print(f"[UI_TEST] {message}")
    
    def on_verify_widgets(self, button):
        """Verify all UI widgets exist and are properly configured."""
        self.results_buffer.set_text("")  # Clear
        self.log("========== WIDGET VERIFICATION ==========")
        
        builder = self.pathway_panel.builder
        
        # Check notebook
        notebook = builder.get_object('pathway_notebook')
        if notebook:
            num_pages = notebook.get_n_pages()
            self.log(f"✓ Notebook found: {num_pages} pages")
            
            # List all tabs
            for i in range(num_pages):
                page = notebook.get_nth_page(i)
                tab_label = notebook.get_tab_label_text(page) if page else "Unknown"
                self.log(f"  Tab {i}: {tab_label}")
        else:
            self.log("✗ ERROR: Notebook not found!")
        
        # Check KEGG tab widgets
        self.log("\n--- KEGG Tab ---")
        kegg_widgets = {
            'kegg_external_radio': 'External radio',
            'kegg_local_radio': 'Local radio',
            'kegg_external_box': 'External box',
            'kegg_local_box': 'Local box',
            'pathway_id_entry': 'Pathway ID entry',
            'organism_combo': 'Organism combo',
            'kegg_file_entry': 'File entry',
            'kegg_browse_button': 'Browse button',
            'kegg_import_button': 'Import button'
        }
        self.verify_widgets(builder, kegg_widgets)
        
        # Check SBML tab widgets
        self.log("\n--- SBML Tab ---")
        sbml_widgets = {
            'sbml_external_radio': 'External radio',
            'sbml_local_radio': 'Local radio',
            'sbml_external_box': 'External box',
            'sbml_local_box': 'Local box',
            'biomodels_id_entry': 'BioModels ID entry',
            'sbml_file_entry': 'File entry',
            'sbml_browse_button': 'Browse button',
            'sbml_import_button': 'Import button'
        }
        self.verify_widgets(builder, sbml_widgets)
        
        # Check BRENDA tab widgets
        self.log("\n--- BRENDA Tab ---")
        brenda_widgets = {
            'brenda_external_radio': 'External radio',
            'brenda_local_radio': 'Local radio',
            'brenda_external_box': 'External box',
            'brenda_local_box': 'Local box',
            'brenda_credentials_status': 'Credentials status',
            'brenda_configure_button': 'Configure button',
            'ec_number_entry': 'EC number entry',
            'brenda_organism_combo': 'Organism combo',
            'brenda_file_entry': 'File entry',
            'brenda_browse_button': 'Browse button',
            'brenda_enrich_button': 'Enrich button'
        }
        self.verify_widgets(builder, brenda_widgets)
        
        self.log("\n========== VERIFICATION COMPLETE ==========")
    
    def verify_widgets(self, builder, widget_dict):
        """Verify a dict of widgets."""
        for widget_id, description in widget_dict.items():
            widget = builder.get_object(widget_id)
            if widget:
                status = "visible" if widget.get_visible() else "hidden"
                self.log(f"  ✓ {description}: {status}")
            else:
                self.log(f"  ✗ {description}: NOT FOUND!")
    
    def on_test_radios(self, button):
        """Test radio button toggling."""
        self.results_buffer.set_text("")  # Clear
        self.log("========== RADIO BUTTON TEST ==========")
        
        builder = self.pathway_panel.builder
        
        # Test each tab
        for tab_name, external_id, local_id, external_box_id, local_box_id in [
            ('KEGG', 'kegg_external_radio', 'kegg_local_radio', 
             'kegg_external_box', 'kegg_local_box'),
            ('SBML', 'sbml_external_radio', 'sbml_local_radio',
             'sbml_external_box', 'sbml_local_box'),
            ('BRENDA', 'brenda_external_radio', 'brenda_local_radio',
             'brenda_external_box', 'brenda_local_box')
        ]:
            self.log(f"\n--- {tab_name} Tab ---")
            
            external_radio = builder.get_object(external_id)
            local_radio = builder.get_object(local_id)
            external_box = builder.get_object(external_box_id)
            local_box = builder.get_object(local_box_id)
            
            if not all([external_radio, local_radio, external_box, local_box]):
                self.log(f"  ✗ Missing widgets!")
                continue
            
            # Test initial state
            self.log(f"  Initial: External={external_radio.get_active()}, "
                    f"External_box_visible={external_box.get_visible()}")
            
            # Toggle to Local
            self.log(f"  Activating Local radio...")
            local_radio.set_active(True)
            GLib.timeout_add(100, self.check_toggle_result, tab_name, 
                           external_radio, local_radio, external_box, local_box, False)
        
        self.log("\n========== TEST SCHEDULED ==========")
    
    def check_toggle_result(self, tab_name, external_radio, local_radio, 
                           external_box, local_box, expect_external):
        """Check toggle result after signal processing."""
        self.log(f"\n{tab_name} After toggle:")
        self.log(f"  External active: {external_radio.get_active()}")
        self.log(f"  Local active: {local_radio.get_active()}")
        self.log(f"  External box visible: {external_box.get_visible()}")
        self.log(f"  Local box visible: {local_box.get_visible()}")
        
        # Verify visibility matches radio state
        expected_ext_visible = external_radio.get_active()
        expected_local_visible = local_radio.get_active()
        
        if external_box.get_visible() == expected_ext_visible:
            self.log(f"  ✓ External box visibility correct")
        else:
            self.log(f"  ✗ External box visibility WRONG!")
        
        if local_box.get_visible() == expected_local_visible:
            self.log(f"  ✓ Local box visibility correct")
        else:
            self.log(f"  ✗ Local box visibility WRONG!")
        
        return False  # Don't repeat
    
    def on_test_tabs(self, button):
        """Test tab switching."""
        self.results_buffer.set_text("")  # Clear
        self.log("========== TAB SWITCHING TEST ==========")
        
        notebook = self.pathway_panel.builder.get_object('pathway_notebook')
        if not notebook:
            self.log("✗ ERROR: Notebook not found!")
            return
        
        num_pages = notebook.get_n_pages()
        self.log(f"Notebook has {num_pages} pages")
        
        # Switch through all tabs
        for i in range(num_pages):
            page = notebook.get_nth_page(i)
            tab_label = notebook.get_tab_label_text(page) if page else "Unknown"
            
            self.log(f"\nSwitching to page {i}: {tab_label}")
            notebook.set_current_page(i)
            
            # Brief delay to see the switch
            GLib.timeout_add(300 * (i + 1), lambda: None)
        
        self.log("\n========== TEST COMPLETE ==========")


def main():
    """Run the UI test."""
    print("=" * 70)
    print("Pathway Panel - UI Elements Test (Unified Interface)")
    print("=" * 70)
    print()
    
    win = UITestWindow()
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    
    Gtk.main()


if __name__ == '__main__':
    main()
