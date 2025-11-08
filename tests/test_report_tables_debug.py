#!/usr/bin/env python3
"""Debug script to test Report Panel table population.

This script:
1. Loads a model
2. Runs a simulation
3. Checks if the Report Panel tables are populated
4. Prints detailed debug information
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

def test_report_tables():
    """Test Report Panel table population."""
    
    print("=" * 80)
    print("REPORT PANEL TABLE POPULATION DEBUG TEST")
    print("=" * 80)
    
    # Import after path setup
    from shypn.helpers.model_canvas_loader import ModelCanvasLoader
    from shypn.helpers.report_panel_loader import ReportPanelLoader
    
    # Create model canvas
    model_canvas_loader = ModelCanvasLoader()
    model_canvas_loader.load()
    
    # Create report panel
    report_panel_loader = ReportPanelLoader(project=None, model_canvas=model_canvas_loader)
    report_panel_loader.load()
    
    # Store reference (this is what shypn.py does)
    model_canvas_loader.report_panel_loader = report_panel_loader
    
    # Load a test model
    test_model_path = os.path.join(
        os.path.dirname(__file__), '..', 'workspace', 'projects', 
        'Interactive', 'models', 'hsa00010_source.shy'
    )
    
    if not os.path.exists(test_model_path):
        print(f"ERROR: Test model not found at {test_model_path}")
        return False
    
    print(f"\n1. Loading model: {test_model_path}")
    model_canvas_loader.load_model(test_model_path)
    
    # Get the current canvas and controller
    drawing_area = model_canvas_loader.get_current_document()
    controller = model_canvas_loader.get_canvas_controller(drawing_area)
    
    print(f"\n2. Controller check:")
    print(f"   - Controller: {controller}")
    print(f"   - Has data_collector: {hasattr(controller, 'data_collector')}")
    if hasattr(controller, 'data_collector'):
        print(f"   - Data collector: {controller.data_collector}")
    
    # Set controller on report panel
    print(f"\n3. Setting controller on Report Panel...")
    report_panel_loader.panel.set_controller(controller)
    
    # Check if controller was set
    print(f"\n4. Checking Report Panel state:")
    for category in report_panel_loader.panel.categories:
        from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
        if isinstance(category, DynamicAnalysesCategory):
            print(f"   - Found DynamicAnalysesCategory")
            print(f"   - Category.controller: {category.controller}")
            print(f"   - Same controller: {category.controller is controller}")
            break
    
    # Run simulation
    print(f"\n5. Running simulation...")
    controller.settings.duration = 100.0
    controller.settings.time_step = 0.006
    
    # Create a flag to check if callback was called
    callback_called = [False]
    
    def on_simulation_done():
        callback_called[0] = True
        print(f"\n6. Simulation complete callback triggered!")
        
        # Check data collector
        print(f"\n7. Checking NEW data collector:")
        if controller.data_collector:
            dc = controller.data_collector
            print(f"   - has_data(): {dc.has_data()}")
            if dc.has_data():
                print(f"   - Time points: {len(dc.time_points)}")
                print(f"   - Places tracked: {len(dc.place_data)}")
                print(f"   - Transitions tracked: {len(dc.transition_data)}")
        
        # Check if report panel callback was triggered
        print(f"\n8. Checking Report Panel refresh:")
        print(f"   - Report panel should have called _refresh_simulation_data()")
        
        Gtk.main_quit()
    
    # Set our callback
    original_callback = controller.on_simulation_complete
    controller.on_simulation_complete = on_simulation_done
    
    # Start simulation
    controller.run()
    
    # Run GTK main loop for a bit
    print(f"   - Starting simulation (will run for ~3 seconds)...")
    GLib.timeout_add(3000, Gtk.main_quit)  # Stop after 3 seconds
    Gtk.main()
    
    # Stop simulation
    if controller.is_running:
        controller.stop()
    
    print(f"\n9. Final results:")
    print(f"   - Callback was called: {callback_called[0]}")
    
    if not callback_called[0]:
        print(f"   ERROR: Simulation complete callback was NOT called!")
        return False
    
    print(f"\n10. SUCCESS: Tables should be populated")
    print(f"    Check the Report Panel → DYNAMIC ANALYSES → Simulation Data")
    
    return True

if __name__ == '__main__':
    success = test_report_tables()
    sys.exit(0 if success else 1)
