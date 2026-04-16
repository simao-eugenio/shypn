"""Test script to check progress bar visibility in simulation tools palette."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.helpers.simulate_tools_palette_loader import SimulateToolsPaletteLoader

def test_progress_bar():
    """Test if progress bar widget is loaded and visible."""
    
    # Create palette loader WITHOUT setting simulation (to test basic loading)
    ui_dir = os.path.join(os.path.dirname(__file__), '..', 'ui')
    palette_loader = SimulateToolsPaletteLoader(ui_dir)
    
    # Check if progress bar exists
    print(f"Progress bar widget: {palette_loader.progress_bar}")
    print(f"Progress bar type: {type(palette_loader.progress_bar)}")
    
    if palette_loader.progress_bar:
        print(f"Progress bar visible: {palette_loader.progress_bar.get_visible()}")
        print(f"Progress bar parent: {palette_loader.progress_bar.get_parent()}")
        print(f"Progress bar mapped: {palette_loader.progress_bar.get_mapped()}")
        print(f"Progress bar realized: {palette_loader.progress_bar.get_realized()}")
        
        # Check parent hierarchy
        widget = palette_loader.progress_bar
        level = 0
        while widget:
            print(f"  Level {level}: {type(widget).__name__} visible={widget.get_visible()}")
            widget = widget.get_parent()
            level += 1
            if level > 10:  # Safety limit
                break
    else:
        print("❌ Progress bar widget is None!")
    
    # Check time label too
    print(f"\nTime display label: {palette_loader.time_display_label}")
    if palette_loader.time_display_label:
        print(f"Time label visible: {palette_loader.time_display_label.get_visible()}")
        print(f"Time label parent: {palette_loader.time_display_label.get_parent()}")
    
    # Check the container
    print(f"\nWidget container: {palette_loader.widget_container}")
    if palette_loader.widget_container:
        print(f"Container type: {type(palette_loader.widget_container).__name__}")
        print(f"Container visible: {palette_loader.widget_container.get_visible()}")
        
        # List children
        if hasattr(palette_loader.widget_container, 'get_children'):
            children = palette_loader.widget_container.get_children()
            print(f"Container has {len(children)} children:")
            for i, child in enumerate(children):
                print(f"  {i}: {type(child).__name__} visible={child.get_visible()}")

if __name__ == '__main__':
    test_progress_bar()
