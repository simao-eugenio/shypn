#!/usr/bin/env python3
"""Quick test for mode palette loader."""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Try importing the mode palette loader
try:
    from ui.palettes.mode.mode_palette_loader import ModePaletteLoader
    print("✓ ModePaletteLoader imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ModePaletteLoader: {e}")
    sys.exit(1)

# Try instantiating (requires GTK)
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject
    
    palette = ModePaletteLoader()
    print("✓ ModePaletteLoader instantiated successfully")
    print(f"  Current mode: {palette.current_mode}")
    print(f"  Widget type: {type(palette.get_widget())}")
    
except Exception as e:
    print(f"✗ Failed to instantiate ModePaletteLoader: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed!")
