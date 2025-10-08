#!/usr/bin/env python3
"""Edit Palette Loader - Zoom-Style [E] Button to Toggle Tools.

This module provides a floating edit palette with zoom-style appearance that overlays
the canvas at the bottom-center. It provides a single [E] toggle button in a styled
purple gradient container with space for future expansion (3 button positions: [ ][E][ ]).

The palette integrates with the Edit Tools palette to provide
tool selection for Petri net object creation (Places, Transitions, Arcs).
"""
import os
import sys
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject, Pango
except Exception as e:
    print('ERROR: GTK3 not available in edit_palette_loader:', e, file=sys.stderr)
    sys.exit(1)


class EditPaletteLoader(GObject.GObject):
    """Manager for the zoom-style edit palette with [E] button in styled container."""
    
    __gsignals__ = {
        'tools-toggled': (GObject.SignalFlags.RUN_FIRST, None, (bool,))
    }
    
    def __init__(self, ui_path=None):
        """Initialize the edit palette loader.
        
        Args:
            ui_path: Optional path to edit_palette.ui. If None, auto-detects location.
        """
        super().__init__()
        
        # Auto-detect UI path using Path (like mode palette)
        if ui_path is None:
            self.ui_path = Path(__file__).parent.parent.parent.parent / 'ui' / 'palettes' / 'edit_palette.ui'
        else:
            self.ui_path = Path(ui_path)
        
        self.builder = Gtk.Builder()
        
        # Widget references
        self.edit_palette_container = None    # Outer container
        self.edit_control = None              # Inner styled box (purple gradient)
        self.edit_placeholder_left = None     # Left placeholder [ ]
        self.edit_placeholder_right = None    # Right placeholder [ ]
        self.edit_toggle_button = None        # [E] button (center)
        
        # Styling
        self.css_provider = None
        self.target_height = 24  # Dynamic font-based sizing
        
        # Palette loaders to control
        self.tools_palette_loader = None              # OLD: Deprecated - for backwards compatibility
        self.editing_operations_palette_loader = None # OLD: Deprecated - for backwards compatibility
        self.combined_tools_palette_loader = None     # OLD: Unified combined tools palette (container-based)
        self.floating_buttons_manager = None          # OLD: Individual floating buttons (no container)
        
        # NEW: Two separate palette instances (transparent containers)
        self.tools_palette = None                     # ToolsPalette instance [P][T][A]
        self.operations_palette = None                # OperationsPalette instance [S][L][U][R]
        
    
    def load(self):
        """Load the edit palette UI, apply zoom-style styling, and return the widget.
        
        Returns:
            Gtk.Box: The edit palette container widget.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If required widgets not found in UI file.
        """
        # Validate UI file exists
        if not self.ui_path.exists():
            raise FileNotFoundError(f"Edit palette UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder.add_from_file(str(self.ui_path))
        
        # Extract widgets
        self.edit_palette_container = self.builder.get_object('edit_palette_container')
        self.edit_control = self.builder.get_object('edit_control')
        self.edit_placeholder_left = self.builder.get_object('edit_placeholder_left')
        self.edit_placeholder_right = self.builder.get_object('edit_placeholder_right')
        self.edit_toggle_button = self.builder.get_object('edit_toggle_button')
        
        if self.edit_palette_container is None:
            raise ValueError("Object 'edit_palette_container' not found in edit_palette.ui")
        
        if self.edit_toggle_button is None:
            raise ValueError("Object 'edit_toggle_button' not found in edit_palette.ui")
        
        # Calculate dynamic sizing based on font metrics
        self._calculate_target_size()
        
        # Apply zoom-style CSS styling (purple container + green button)
        self._apply_css()
        
        # Connect button signal
        self.edit_toggle_button.connect('toggled', self._on_edit_toggled)
        
        
        return self.edit_palette_container
    
    def _calculate_target_size(self):
        """Calculate dynamic button size based on font metrics (1.3× 'W' height).
        
        This ensures buttons scale properly with different font sizes and DPI settings.
        Minimum size is 24px for usability.
        """
        try:
            # Create temporary label to measure font
            temp_label = Gtk.Label(label="W")
            temp_label.show()
            
            # Get Pango layout and measure character height
            layout = temp_label.get_layout()
            if layout:
                _, logical_rect = layout.get_pixel_extents()
                w_height = logical_rect.height
                self.target_height = max(int(w_height * 1.3), 24)  # Minimum 24px
            else:
                self.target_height = 24  # Fallback
        except Exception as e:
            self.target_height = 24
        
    
    def _apply_css(self):
        """Apply zoom-style CSS with purple gradient container and green button.
        
        The purple gradient container (#667eea → #764ba2) matches the mode and zoom palettes.
        The green button gradient (#2ecc71 → #27ae60) preserves edit mode brand identity.
        """
        css = f"""
        /* Purple gradient container (match mode/zoom palettes) */
        .edit-palette {{
            background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
            border: 2px solid #5568d3;
            border-radius: 8px;
            padding: 3px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }}
        
        /* [E] Toggle Button - Green gradient (preserve green theme) */
        .edit-button {{
            background: linear-gradient(to bottom, #2ecc71 0%, #27ae60 100%);
            border: 2px solid #229954;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            color: white;
            min-width: {self.target_height}px;
            min-height: {self.target_height}px;
            padding: 0;
            margin: 0;
            transition: all 200ms ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .edit-button:hover {{
            background: linear-gradient(to bottom, #27ae60 0%, #229954 100%);
            border-color: #1e8449;
            color: white;
            box-shadow: 0 0 8px rgba(46, 204, 113, 0.6);
        }}
        
        .edit-button:active {{
            background: linear-gradient(to bottom, #229954 0%, #1e8449 100%);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        /* Checked state (tools visible) - darker green with inset shadow */
        .edit-button:checked {{
            background: linear-gradient(to bottom, #27ae60, #1e8449);
            border: 2px solid #186a3b;
            color: white;
            font-weight: bold;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }}
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
    
    def set_edit_palettes(self, tools_palette, operations_palette):
        """Set the two edit palettes for show/hide control.
        
        Args:
            tools_palette: ToolsPalette instance [P][T][A]
            operations_palette: OperationsPalette instance [S][L][U][R]
        """
        self.tools_palette = tools_palette
        self.operations_palette = operations_palette
    
    def set_floating_buttons_manager(self, manager):
        """Set the floating buttons manager for show/hide control (DEPRECATED)."""
        self.floating_buttons_manager = manager
    
    def set_combined_tools_palette_loader(self, combined_tools_palette_loader):
        """Set the combined tools palette loader (DEPRECATED - use set_edit_palettes)."""
        self.combined_tools_palette_loader = combined_tools_palette_loader
    
    def set_tools_palette_loader(self, tools_loader):
        """Set the edit tools palette loader to control.
        
        DEPRECATED: Use set_combined_tools_palette_loader() instead.
        Kept for backwards compatibility.
        
        Args:
            tools_loader: EditToolsLoader instance.
        """
        self.tools_palette_loader = tools_loader
    
    def set_editing_operations_palette_loader(self, editing_ops_loader):
        """Set the editing operations palette loader to control.
        
        DEPRECATED: Use set_combined_tools_palette_loader() instead.
        Kept for backwards compatibility.
        
        Args:
            editing_ops_loader: EditingOperationsPaletteLoader instance.
        """
        self.editing_operations_palette_loader = editing_ops_loader
    
    # ==================== Event Handlers ====================
    
    def _on_edit_toggled(self, toggle_button):
        """Handle edit button toggle - show/hide tools palette.
        
        Args:
            toggle_button: GtkToggleButton that was toggled.
        """
        is_active = toggle_button.get_active()
        
        # NEW: Control both palettes (transparent containers)
        if self.tools_palette and self.operations_palette:
            if is_active:
                self.tools_palette.show()
                self.operations_palette.show()
            else:
                self.tools_palette.hide()
                self.operations_palette.hide()
        
        # OLD: Control floating buttons manager (individual buttons, no container)
        elif self.floating_buttons_manager:
            if is_active:
                self.floating_buttons_manager.show_all()
            else:
                self.floating_buttons_manager.hide_all()
        
        # OLDER: Control combined tools palette (container-based)
        elif self.combined_tools_palette_loader:
            if is_active:
                self.combined_tools_palette_loader.show()
            else:
                self.combined_tools_palette_loader.hide()
        
        # OLDEST: For backwards compatibility, also control separate palettes if set
        elif self.tools_palette_loader or self.editing_operations_palette_loader:
            # Toggle the edit tools palette visibility
            if self.tools_palette_loader:
                if is_active:
                    self.tools_palette_loader.show()
                else:
                    self.tools_palette_loader.hide()
            
            # Toggle the editing operations palette visibility
            if self.editing_operations_palette_loader:
                if is_active:
                    self.editing_operations_palette_loader.show()
                else:
                    self.editing_operations_palette_loader.hide()
        
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
