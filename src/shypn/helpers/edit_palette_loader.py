#!/usr/bin/env python3
"""Edit Palette Loader - [E] Button to Toggle Tools.

This module provides a floating edit palette that overlays the canvas
in the top-left corner. It provides a single [E] button that toggles
the visibility of the Edit Tools palette.

The palette integrates with the Edit Tools palette to provide
tool selection for Petri net object creation (Places, Transitions, Arcs).
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject
except Exception as e:
    print('ERROR: GTK3 not available in edit_palette_loader:', e, file=sys.stderr)
    sys.exit(1)


class EditPaletteLoader(GObject.GObject):
    """Manager for the floating edit palette with [E] button."""
    
    __gsignals__ = {
        'tools-toggled': (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }
    
    def __init__(self, ui_path=None):
        """Initialize the edit palette loader.
        
        Args:
            ui_path: Optional path to edit_palette.ui. If None, uses default location.
        """
        super().__init__()
        
        if ui_path is None:
            # Default: ui/palettes/edit_palette.ui
            # This loader file is in: src/shypn/helpers/edit_palette_loader.py
            # UI file is in: ui/palettes/edit_palette.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'palettes', 'edit_palette.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.edit_palette_container = None  # Main container
        self.edit_toggle_button = None  # [E] button
        
        # Edit tools palette reference (set externally)
        self.tools_palette_loader = None
        
        # CSS provider for styling
        self.css_provider = None
    
    def load(self):
        """Load the edit palette UI and return the widget.
        
        Returns:
            Gtk.Box: The edit palette container widget.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If edit_palette_container not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Edit palette UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract widgets
        self.edit_palette_container = self.builder.get_object('edit_palette_container')
        self.edit_toggle_button = self.builder.get_object('edit_toggle_button')
        
        if self.edit_palette_container is None:
            raise ValueError("Object 'edit_palette_container' not found in edit_palette.ui")
        
        if self.edit_toggle_button is None:
            raise ValueError("Object 'edit_toggle_button' not found in edit_palette.ui")
        
        # Connect button signal
        self.edit_toggle_button.connect('toggled', self._on_edit_toggled)
        
        # Apply custom CSS styling
        self._apply_styling()
        
        return self.edit_palette_container
    
    def _apply_styling(self):
        """Apply custom CSS styling to the edit palette."""
        css = """
        .edit-button {
            background: linear-gradient(to bottom, #2ecc71, #27ae60);
            border: 2px solid #229954;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            min-width: 36px;
            min-height: 36px;
            padding: 0;
            margin: 0;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3),
                        0 1px 3px rgba(0, 0, 0, 0.2);
        }
        
        .edit-button:hover {
            background: linear-gradient(to bottom, #27ae60, #229954);
            box-shadow: 0 4px 8px rgba(46, 204, 113, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .edit-button:active,
        .edit-button:checked {
            background: linear-gradient(to bottom, #229954, #1e8449);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .edit-button:checked {
            border-color: #1e8449;
        }
        """
        
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply to screen
        from gi.repository import Gdk
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def set_tools_palette_loader(self, tools_loader):
        """Set the edit tools palette loader to control.
        
        Args:
            tools_loader: EditToolsLoader instance.
        """
        self.tools_palette_loader = tools_loader
    
    # ==================== Event Handlers ====================
    
    def _on_edit_toggled(self, toggle_button):
        """Handle edit button toggle - show/hide tools palette.
        
        Args:
            toggle_button: GtkToggleButton that was toggled.
        """
        is_active = toggle_button.get_active()
        
        # Toggle the tools palette visibility
        if self.tools_palette_loader:
            if is_active:
                self.tools_palette_loader.show()
            else:
                self.tools_palette_loader.hide()
        
        # Emit signal for external listeners
        self.emit('tools-toggled', is_active)
    
    # ==================== Public API ====================
    
    def get_widget(self):
        """Get the edit palette container widget.
        
        Returns:
            Gtk.Box: The edit palette container widget, or None if not loaded.
        """
        return self.edit_palette_container
    
    def is_tools_visible(self):
        """Check if the edit tools palette is currently visible.
        
        Returns:
            bool: True if tools palette is visible, False otherwise.
        """
        if self.edit_toggle_button:
            return self.edit_toggle_button.get_active()
        return False
    
    def set_tools_visible(self, visible):
        """Programmatically set tools palette visibility.
        
        Args:
            visible: Boolean, True to show tools palette, False to hide.
        """
        if self.edit_toggle_button:
            self.edit_toggle_button.set_active(visible)


def create_edit_palette(ui_path=None):
    """Convenience function to create and load the edit palette.
    
    Args:
        ui_path: Optional path to edit_palette.ui.
        
    Returns:
        EditPaletteLoader: The loaded edit palette instance.
        
    Example:
        palette = create_edit_palette()
        widget = palette.load()
        palette.set_tools_palette_loader(tools_loader)
        # Add widget as overlay to canvas
    """
    palette = EditPaletteLoader(ui_path)
    palette.load()
    return palette
