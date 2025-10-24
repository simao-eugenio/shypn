#!/usr/bin/env python3
"""
Test that Analyses Panel is properly initialized on first model load.

This test verifies that the data_collector wiring happens during initial
model creation, not just on tab switches.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_analyses_panel_initialization():
    """Test that analyses panel gets data_collector on first model load."""
    
    print("\n" + "="*70)
    print("TEST: Analyses Panel Initialization on First Model Load")
    print("="*70 + "\n")
    
    # Import after path is set
    from shypn.helpers.model_canvas_loader import ModelCanvasLoader
    from shypn.helpers.right_panel_loader import create_right_panel
    
    # Create main window
    window = Gtk.Window(title="Analyses Panel Init Test")
    window.set_default_size(800, 600)
    
    # Create right panel
    print("1. Creating right panel...")
    right_panel_loader = create_right_panel()
    print(f"   ✓ Right panel created")
    print(f"   - Has context_menu_handler: {hasattr(right_panel_loader, 'context_menu_handler')}")
    print(f"   - context_menu_handler is not None: {right_panel_loader.context_menu_handler is not None if hasattr(right_panel_loader, 'context_menu_handler') else False}")
    
    # Check initial state (should have handler but no panels yet)
    print(f"\n2. Initial state (before model load):")
    print(f"   - Has data_collector attr: {hasattr(right_panel_loader, 'data_collector')}")
    print(f"   - data_collector is None: {right_panel_loader.data_collector is None if hasattr(right_panel_loader, 'data_collector') else 'N/A'}")
    print(f"   - Has transition_panel attr: {hasattr(right_panel_loader, 'transition_panel')}")
    print(f"   - transition_panel is None: {right_panel_loader.transition_panel is None if hasattr(right_panel_loader, 'transition_panel') else 'N/A'}")
    
    # Create notebook for canvas
    notebook = Gtk.Notebook()
    
    # Create model canvas loader
    print(f"\n3. Creating model canvas loader...")
    model_canvas_loader = ModelCanvasLoader(
        notebook=notebook,
        parent_window=window,
        right_panel_loader=right_panel_loader
    )
    print(f"   ✓ Model canvas loader created")
    
    # Create first model (this should trigger data_collector wiring)
    print(f"\n4. Creating first model canvas...")
    drawing_area = model_canvas_loader.create_new_document()
    print(f"   ✓ Canvas created: {drawing_area}")
    
    # Check if overlay_managers has the swissknife_palette
    print(f"\n5. Checking swissknife_palette creation:")
    if drawing_area in model_canvas_loader.overlay_managers:
        overlay_manager = model_canvas_loader.overlay_managers[drawing_area]
        print(f"   ✓ Overlay manager exists for drawing_area")
        
        if hasattr(overlay_manager, 'swissknife_palette'):
            print(f"   ✓ swissknife_palette exists")
            swissknife = overlay_manager.swissknife_palette
            
            if hasattr(swissknife, 'widget_palette_instances'):
                print(f"   ✓ widget_palette_instances exists")
                simulate_palette = swissknife.widget_palette_instances.get('simulate')
                
                if simulate_palette:
                    print(f"   ✓ simulate palette found: {type(simulate_palette).__name__}")
                    
                    if hasattr(simulate_palette, 'data_collector'):
                        data_collector = simulate_palette.data_collector
                        print(f"   ✓ data_collector exists: {type(data_collector).__name__}")
                        print(f"   - data_collector is not None: {data_collector is not None}")
                    else:
                        print(f"   ✗ simulate palette has no data_collector attribute")
                else:
                    print(f"   ✗ No simulate palette in widget_palette_instances")
            else:
                print(f"   ✗ swissknife_palette has no widget_palette_instances")
        else:
            print(f"   ✗ Overlay manager has no swissknife_palette")
    else:
        print(f"   ✗ No overlay manager for drawing_area")
    
    # Check if right_panel_loader got the data_collector
    print(f"\n6. Checking right_panel_loader after model creation:")
    print(f"   - Has data_collector attr: {hasattr(right_panel_loader, 'data_collector')}")
    
    if hasattr(right_panel_loader, 'data_collector'):
        data_collector = right_panel_loader.data_collector
        print(f"   - data_collector is not None: {data_collector is not None}")
        
        if data_collector is not None:
            print(f"   ✓ data_collector type: {type(data_collector).__name__}")
    
    # Check if panels were created
    print(f"\n7. Checking analysis panels:")
    print(f"   - Has transition_panel attr: {hasattr(right_panel_loader, 'transition_panel')}")
    
    if hasattr(right_panel_loader, 'transition_panel'):
        panel = right_panel_loader.transition_panel
        print(f"   - transition_panel is not None: {panel is not None}")
        
        if panel is not None:
            print(f"   ✓ transition_panel type: {type(panel).__name__}")
            print(f"   - Panel has objects_listbox: {hasattr(panel, 'objects_listbox')}")
            print(f"   - Panel has figure: {hasattr(panel, 'figure')}")
            print(f"   - Panel has canvas: {hasattr(panel, 'canvas')}")
    
    print(f"   - Has place_panel attr: {hasattr(right_panel_loader, 'place_panel')}")
    
    if hasattr(right_panel_loader, 'place_panel'):
        panel = right_panel_loader.place_panel
        print(f"   - place_panel is not None: {panel is not None}")
        
        if panel is not None:
            print(f"   ✓ place_panel type: {type(panel).__name__}")
    
    # Final verdict
    print(f"\n" + "="*70)
    
    if (hasattr(right_panel_loader, 'data_collector') and 
        right_panel_loader.data_collector is not None and
        hasattr(right_panel_loader, 'transition_panel') and
        right_panel_loader.transition_panel is not None and
        hasattr(right_panel_loader, 'place_panel') and
        right_panel_loader.place_panel is not None):
        print("✅ SUCCESS: Analyses Panel is fully initialized!")
        print("   - data_collector: Set ✓")
        print("   - transition_panel: Created ✓")
        print("   - place_panel: Created ✓")
        print("   - UI widgets: Available ✓")
        print("\nThe Analyses Panel should now be visible and functional.")
        success = True
    else:
        print("❌ FAILURE: Analyses Panel is not properly initialized")
        print("   - data_collector: " + ("Set ✓" if hasattr(right_panel_loader, 'data_collector') and right_panel_loader.data_collector is not None else "Not set ✗"))
        print("   - transition_panel: " + ("Created ✓" if hasattr(right_panel_loader, 'transition_panel') and right_panel_loader.transition_panel is not None else "Not created ✗"))
        print("   - place_panel: " + ("Created ✓" if hasattr(right_panel_loader, 'place_panel') and right_panel_loader.place_panel is not None else "Not created ✗"))
        print("\nThe Analyses Panel will NOT be visible.")
        success = False
    
    print("="*70 + "\n")
    
    return success

if __name__ == '__main__':
    success = test_analyses_panel_initialization()
    sys.exit(0 if success else 1)
