#!/usr/bin/env python3
"""
Headless test to follow the flow of events for SBML import path.

This test verifies the canvas pre-creation architecture:
1. Canvas is created BEFORE parsing starts
2. Canvas state is initialized immediately
3. Background parsing completes
4. Objects are loaded into pre-created canvas
5. No duplicate canvas creation occurs
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.helpers.model_canvas_loader import create_model_canvas
from shypn.helpers.sbml_import_panel import SBMLImportPanel


class SBMLImportFlowTest:
    """Test harness for SBML import flow."""
    
    def __init__(self):
        self.window = None
        self.model_canvas_loader = None
        self.sbml_panel = None
        self.test_passed = False
        self.test_message = ""
        self.events = []
        
    def log_event(self, event_name, details=""):
        """Log an event in the flow."""
        timestamp = time.time()
        event = f"[{timestamp:.3f}] {event_name}"
        if details:
            event += f": {details}"
        self.events.append(event)
        print(event)
    
    def setup_ui(self):
        """Setup minimal UI for testing."""
        self.log_event("SETUP", "Creating test window")
        
        # Create window
        self.window = Gtk.Window()
        self.window.set_title("SBML Import Flow Test")
        self.window.set_default_size(800, 600)
        self.window.connect('destroy', self.on_destroy)
        
        # Create model canvas loader
        self.log_event("SETUP", "Creating ModelCanvasLoader")
        self.model_canvas_loader = create_model_canvas()
        self.model_canvas_loader.parent_window = self.window
        
        # Create a temporary project directory (but don't need full Project class)
        import tempfile
        self.temp_dir = tempfile.mkdtemp(prefix="sbml_test_")
        self.log_event("SETUP", f"Created temp dir: {self.temp_dir}")
        
        # Load SBML panel UI
        ui_file = os.path.join(os.path.dirname(__file__), 'ui', 'panels', 'pathway_panel.ui')
        self.log_event("SETUP", f"Loading UI from: {ui_file}")
        builder = Gtk.Builder()
        builder.add_from_file(ui_file)
        
        # Create SBML panel (project=None is fine)
        self.log_event("SETUP", "Creating SBMLImportPanel")
        self.sbml_panel = SBMLImportPanel(
            builder=builder,
            model_canvas=self.model_canvas_loader,
            project=None  # Not required for testing canvas pre-creation
        )
        
        # Layout
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self.model_canvas_loader.container, True, True, 0)
        box.pack_start(self.sbml_panel.panel, False, False, 0)
        
        self.window.add(box)
        self.window.show_all()
        
        # Wrap key methods to log events (AFTER panel is created)
        self.wrap_panel_methods()
        
        self.log_event("SETUP", "UI setup complete")
    
    def wrap_panel_methods(self):
        """Wrap SBML panel methods to log events."""
        original_on_load_clicked = self.sbml_panel._on_load_clicked
        original_on_parse_complete = self.sbml_panel._on_parse_complete
        original_on_load_complete = self.sbml_panel._on_load_complete
        
        def wrapped_on_load_clicked(button):
            self.log_event("BUTTON_CLICK", "Load button clicked")
            initial_tab_count = self.model_canvas_loader.notebook.get_n_pages()
            self.log_event("CANVAS_STATE", f"Initial tab count: {initial_tab_count}")
            
            result = original_on_load_clicked(button)
            
            # Check if canvas was pre-created
            post_click_tab_count = self.model_canvas_loader.notebook.get_n_pages()
            self.log_event("CANVAS_STATE", f"Post-click tab count: {post_click_tab_count}")
            
            if post_click_tab_count > initial_tab_count:
                self.log_event("CANVAS_PRE_CREATED", f"✅ Canvas pre-created before parsing!")
                
                # Check if _pending_canvas_info was set
                if hasattr(self.sbml_panel, '_pending_canvas_info') and self.sbml_panel._pending_canvas_info:
                    info = self.sbml_panel._pending_canvas_info
                    self.log_event("CANVAS_INFO", f"Stored: page_index={info.get('page_index')}, "
                                                  f"manager={info.get('manager') is not None}")
                    
                    # Check canvas state initialization
                    manager = info.get('manager')
                    if manager:
                        self.log_event("CANVAS_STATE", f"Canvas marked as imported: {manager.is_imported}")
                        self.log_event("CANVAS_STATE", f"Canvas filepath: {manager.filepath}")
                else:
                    self.log_event("ERROR", "❌ _pending_canvas_info not set after canvas pre-creation!")
            else:
                self.log_event("ERROR", "❌ Canvas NOT pre-created! Tab count unchanged.")
            
            return result
        
        def wrapped_on_parse_complete(result):
            self.log_event("PARSE_COMPLETE", "Background parsing completed")
            self.log_event("PARSE_RESULT", f"Result type: {type(result).__name__}")
            
            return original_on_parse_complete(result)
        
        def wrapped_on_load_complete(document_model):
            self.log_event("LOAD_COMPLETE", "Load completion handler called")
            
            # Check if using pre-created canvas
            if hasattr(self.sbml_panel, '_pending_canvas_info') and self.sbml_panel._pending_canvas_info:
                self.log_event("CANVAS_USAGE", "✅ Using pre-created canvas from _pending_canvas_info")
            else:
                self.log_event("ERROR", "❌ No _pending_canvas_info! Would create duplicate canvas!")
            
            # Count tabs before load complete
            pre_load_tab_count = self.model_canvas_loader.notebook.get_n_pages()
            self.log_event("CANVAS_STATE", f"Tab count before load_complete: {pre_load_tab_count}")
            
            result = original_on_load_complete(document_model)
            
            # Count tabs after load complete
            post_load_tab_count = self.model_canvas_loader.notebook.get_n_pages()
            self.log_event("CANVAS_STATE", f"Tab count after load_complete: {post_load_tab_count}")
            
            if post_load_tab_count == pre_load_tab_count:
                self.log_event("SUCCESS", "✅ No duplicate canvas created!")
                self.test_passed = True
                self.test_message = "SBML import flow correct: canvas pre-created and reused"
            else:
                self.log_event("ERROR", f"❌ Duplicate canvas! Tabs increased from {pre_load_tab_count} to {post_load_tab_count}")
                self.test_message = "FAILED: Duplicate canvas created"
            
            # Verify objects were loaded
            if document_model:
                self.log_event("OBJECTS", f"Loaded {len(document_model.places)} places, "
                                         f"{len(document_model.transitions)} transitions, "
                                         f"{len(document_model.arcs)} arcs")
            
            # Schedule test completion
            GLib.timeout_add(1000, self.finish_test)
            
            return result
        
        # Replace methods
        self.sbml_panel._on_load_clicked = wrapped_on_load_clicked
        self.sbml_panel._on_parse_complete = wrapped_on_parse_complete
        self.sbml_panel._on_load_complete = wrapped_on_load_complete
    
    def run_test(self):
        """Run the test sequence."""
        self.log_event("TEST_START", "Starting SBML import flow test")
        
        # Use a test SBML file if available
        test_files = [
            "examples/sbml/BIOMD0000000001.xml",
            "data/biomodels_test/BIOMD0000000001.xml",
        ]
        
        test_file = None
        for f in test_files:
            full_path = os.path.join(os.path.dirname(__file__), f)
            if os.path.exists(full_path):
                test_file = full_path
                break
        
        if not test_file:
            self.log_event("ERROR", "No test SBML file found! Creating minimal test file...")
            # Create a minimal SBML file for testing
            test_file = os.path.join(self.temp_dir, "test_model.xml")
            minimal_sbml = '''<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="test_model" name="Test Model">
    <listOfCompartments>
      <compartment id="c1" name="Compartment 1" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="s1" name="Species 1" compartment="c1" initialConcentration="10" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="s2" name="Species 2" compartment="c1" initialConcentration="0" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfReactions>
      <reaction id="r1" name="Reaction 1" reversible="false">
        <listOfReactants>
          <speciesReference species="s1" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="s2" stoichiometry="1" constant="true"/>
        </listOfProducts>
      </reaction>
    </listOfReactions>
  </model>
</sbml>'''
            with open(test_file, 'w') as f:
                f.write(minimal_sbml)
            self.log_event("TEST_FILE", f"Created minimal SBML: {test_file}")
        
        self.log_event("TEST_FILE", f"Using test file: {test_file}")
        
        # Set the file path in the panel
        self.sbml_panel.filepath_entry.set_text(test_file)
        self.log_event("UI_STATE", f"Set filepath in entry: {test_file}")
        
        # Schedule button click after UI is stable
        def trigger_load():
            self.log_event("TRIGGER", "Clicking load button programmatically")
            self.sbml_panel.load_button.clicked()
            return False
        
        GLib.timeout_add(500, trigger_load)
    
    def finish_test(self):
        """Finish the test and report results."""
        self.log_event("TEST_END", "Test sequence complete")
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Status: {'✅ PASSED' if self.test_passed else '❌ FAILED'}")
        print(f"Message: {self.test_message}")
        print("\nEvent Timeline:")
        for event in self.events:
            print(f"  {event}")
        print("="*80)
        
        # Clean up and exit
        GLib.timeout_add(500, self.cleanup_and_exit)
        return False
    
    def cleanup_and_exit(self):
        """Clean up resources and exit."""
        self.log_event("CLEANUP", "Cleaning up test resources")
        
        # Clean up temp directory
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.log_event("CLEANUP", f"Removed temp dir: {self.temp_dir}")
        
        # Exit with appropriate code
        exit_code = 0 if self.test_passed else 1
        self.log_event("EXIT", f"Exiting with code {exit_code}")
        
        Gtk.main_quit()
        sys.exit(exit_code)
    
    def on_destroy(self, widget):
        """Handle window destroy."""
        self.log_event("WINDOW", "Window destroyed")
        Gtk.main_quit()


def main():
    """Main test entry point."""
    print("="*80)
    print("SBML Import Flow Test - Canvas Pre-Creation Architecture")
    print("="*80)
    print("\nThis test verifies:")
    print("1. Canvas is created BEFORE parsing starts")
    print("2. Canvas state is initialized immediately")
    print("3. Background parsing completes")
    print("4. Objects are loaded into pre-created canvas")
    print("5. No duplicate canvas creation occurs")
    print("\n" + "="*80 + "\n")
    
    # Create and run test
    test = SBMLImportFlowTest()
    test.setup_ui()
    test.run_test()
    
    # Start GTK main loop
    Gtk.main()


if __name__ == '__main__':
    main()
