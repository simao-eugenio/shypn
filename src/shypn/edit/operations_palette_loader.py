#!/usr/bin/env python3
"""Operations Palette Loader - Minimal loader for OperationsPalette."""

import os
import sys
from shypn.edit.operations_palette import OperationsPalette

try:
    from gi.repository import Gtk
except ImportError as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


class OperationsPaletteLoader:
    """Minimal loader for operations palette.
    
    Responsibilities:
    - Load UI file
    - Extract widgets
    - Instantiate OperationsPalette
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
            OperationsPalette: Configured palette instance
        """
        # Load UI file
        ui_file = self._get_ui_path()
        if not os.path.exists(ui_file):
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_file)
        
        # Get widgets
        revealer = self.builder.get_object('operations_revealer')
        container = self.builder.get_object('operations_container')
        
        buttons = {
            'select': self.builder.get_object('btn_select'),
            'lasso': self.builder.get_object('btn_lasso'),
            'undo': self.builder.get_object('btn_undo'),
            'redo': self.builder.get_object('btn_redo')
        }
        
        # Create palette instance
        self.palette = OperationsPalette()
        self.palette.set_revealer(revealer)
        self.palette.set_container(container)
        self.palette.setup_buttons(buttons)
        self.palette.connect_signals()
        self.palette.apply_styling()
        
        return self.palette
    
    def _get_ui_path(self):
        """Get full path to UI file.
        
        Returns:
            str: Absolute path to edit_operations_palette_new.ui
        """
        # This file is in src/shypn/edit/
        # Go up to repo root, then into ui/palettes/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        ui_path = os.path.join(base_dir, 'ui', 'palettes', 'edit_operations_palette_new.ui')
        return ui_path
    
    def get_palette(self):
        """Get the palette instance.
        
        Returns:
            OperationsPalette: The palette instance or None
        """
        return self.palette


def create_operations_palette():
    """Convenience function to create and load operations palette.
    
    Returns:
        OperationsPalette: Loaded palette instance
    """
    loader = OperationsPaletteLoader()
    return loader.load()
