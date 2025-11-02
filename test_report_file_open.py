#!/usr/bin/env python3
"""Test Report panel file open flow."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

print("=" * 80)
print("TESTING REPORT PANEL FILE OPEN FLOW")
print("=" * 80)

# Import the required modules
from shypn.helpers.model_canvas_loader import ModelCanvasLoader
from shypn.helpers.report_panel_loader import ReportPanelLoader

def test_file_open_flow():
    """Test the file open flow."""
    
    # Step 1: Create window
    print("\n[TEST] Step 1: Creating window...")
    window = Gtk.Window()
    window.set_default_size(800, 600)
    window.set_title("Report Panel File Open Test")
    
    # Step 2: Create model canvas loader
    print("[TEST] Step 2: Creating model_canvas_loader...")
    notebook = Gtk.Notebook()
    model_canvas_loader = ModelCanvasLoader(notebook=notebook)
    
    # Step 3: Create report panel
    print("[TEST] Step 3: Creating report_panel_loader...")
    report_panel_loader = ReportPanelLoader(project=None, model_canvas=model_canvas_loader)
    report_panel_loader.load()
    
    # Step 4: Add panels to window
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(notebook, True, True, 0)
    box.pack_end(report_panel_loader.panel, False, False, 0)
    report_panel_loader.panel.set_size_request(400, -1)
    
    window.add(box)
    window.show_all()
    
    # Step 5: Simulate file open - create a new document first
    print("\n[TEST] Step 5: Creating new document (simulating file open)...")
    def delayed_test():
        print("[TEST] Creating new canvas...")
        drawing_area = model_canvas_loader.create_new_canvas()
        print(f"[TEST] Drawing area created: {drawing_area}")
        
        # Get the manager
        manager = model_canvas_loader.get_current_model()
        print(f"[TEST] Current manager: {manager}")
        
        if manager and hasattr(manager, 'model'):
            print(f"[TEST] Manager has model: {manager.model}")
            print(f"[TEST] Model type: {type(manager.model)}")
            
            # Manually trigger the file opened event
            print("\n[TEST] Simulating on_file_opened event...")
            report_panel_loader.panel.on_file_opened("/test/path.shypn")
        
        return False
    
    GLib.timeout_add(500, delayed_test)
    
    # Close after 3 seconds
    def auto_close():
        print("\n[TEST] Test complete, closing...")
        Gtk.main_quit()
        return False
    
    GLib.timeout_add(3000, auto_close)
    
    print("[TEST] Starting GTK main loop...")
    Gtk.main()
    print("[TEST] Test finished")

if __name__ == '__main__':
    test_file_open_flow()
