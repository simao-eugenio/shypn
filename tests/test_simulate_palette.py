#!/usr/bin/env python3
"""Test script to verify simulation palette loads correctly."""

import sys
import os
from pathlib import Path

# Add src to Python path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / 'src'))

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except ImportError as e:
    print(f"ERROR: Cannot import GTK: {e}")
    sys.exit(1)

# Try to import the simulation palette loader
try:
    from shypn.helpers.simulate_palette_loader import (
        create_simulate_palette,
        create_simulate_tools_palette
    )
    print("✓ Successfully imported simulation palette loaders")
except ImportError as e:
    print(f"✗ Failed to import simulation palette loaders: {e}")
    sys.exit(1)

# Test creating the palettes
def test_palettes():
    """Test creating palette instances."""
    print("\nTesting palette creation...")
    
    try:
        # Create simulation tools palette
        simulate_tools_palette = create_simulate_tools_palette()
        print("✓ Created simulation tools palette")
        
        # Get widget
        tools_widget = simulate_tools_palette.get_widget()
        if tools_widget:
            print("✓ Got tools widget")
        else:
            print("✗ Tools widget is None")
            return False
        
        # Check buttons
        run_btn = simulate_tools_palette.get_run_button()
        stop_btn = simulate_tools_palette.get_stop_button()
        reset_btn = simulate_tools_palette.get_reset_button()
        
        if run_btn and stop_btn and reset_btn:
            print("✓ All tool buttons found")
        else:
            print(f"✗ Missing buttons: run={run_btn is not None}, stop={stop_btn is not None}, reset={reset_btn is not None}")
            return False
        
        # Create simulation palette
        simulate_palette = create_simulate_palette()
        print("✓ Created simulation palette")
        
        # Get widget
        palette_widget = simulate_palette.get_widget()
        if palette_widget:
            print("✓ Got palette widget")
        else:
            print("✗ Palette widget is None")
            return False
        
        # Check toggle button
        toggle_btn = simulate_palette.get_toggle_button()
        if toggle_btn:
            print("✓ Toggle button found")
        else:
            print("✗ Toggle button not found")
            return False
        
        # Link palettes
        simulate_palette.set_tools_palette_loader(simulate_tools_palette)
        print("✓ Linked palettes together")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_palettes()
    sys.exit(0 if success else 1)
