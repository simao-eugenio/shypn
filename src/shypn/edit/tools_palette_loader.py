#!/usr/bin/env python3
"""Tools Palette Loader - Minimal loader for ToolsPalette."""

import os
import sys
from shypn.edit.tools_palette import ToolsPalette

try:
    from gi.repository import Gtk
except ImportError as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


class ToolsPaletteLoader:
    """Minimal loader for tools palette.
    
    Responsibilities:
    - Load UI file
    - Extract widgets
    - Instantiate ToolsPalette
    - Wire widgets to palette
    
    The palette itself handles all business logic.
    """
    
    def __init__(self):
        """Initialize the loader."""
        self.palette = None
        self.builder = None
    
    def load(self):
        """Load UI and create palette instance.
        
        Returns:
            ToolsPalette: Configured palette instance
        """
        # Load UI file
        ui_file = self._get_ui_path()
        if not os.path.exists(ui_file):
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_file)
        
        # Get widgets
        revealer = self.builder.get_object('tools_revealer')
        container = self.builder.get_object('tools_container')
        
        buttons = {
            'place': self.builder.get_object('btn_place'),
            'transition': self.builder.get_object('btn_transition'),
            'arc': self.builder.get_object('btn_arc')
        }
        
        # Create palette instance
        self.palette = ToolsPalette()
        self.palette.set_revealer(revealer)
        self.palette.set_container(container)
        self.palette.setup_buttons(buttons)
        self.palette.connect_signals()
        self.palette.apply_styling()
        
        return self.palette
    
    def _get_ui_path(self):
        """Get full path to UI file.
        
        Returns:
            str: Absolute path to edit_tools_palette.ui
        """
        # This file is in src/shypn/edit/
        # Go up to repo root, then into ui/palettes/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        ui_path = os.path.join(base_dir, 'ui', 'palettes', 'edit_tools_palette.ui')
        return ui_path
    
    def get_palette(self):
        """Get the palette instance.
        
        Returns:
            ToolsPalette: The palette instance or None
        """
        return self.palette


def create_tools_palette():
    """Convenience function to create and load tools palette.
    
    Returns:
        ToolsPalette: Loaded palette instance
    """
    loader = ToolsPaletteLoader()
    return loader.load()
