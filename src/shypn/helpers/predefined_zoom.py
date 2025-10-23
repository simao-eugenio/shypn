#!/usr/bin/env python3
"""Predefined Zoom Control Palette with Revealer.

This module provides a floating zoom control palette that overlays the canvas
in the bottom-right corner. It provides:
- Zoom in/out buttons (+/-)
- Zoom level display button (toggles inline revealer)
- Predefined zoom levels (25%, 50%, 75%, 100%, 150%, 200%, 400%)
- Fit-to-window option

The palette uses GtkRevealer for stable inline expansion without separate windows.
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Pango
except Exception as e:
    print('ERROR: GTK3 not available in predefined_zoom:', e, file=sys.stderr)
    sys.exit(1)


class PredefinedZoom:
    """Manager for floating zoom control palette with revealer."""
    
    def __init__(self, ui_path=None):
        """Initialize the zoom control palette.
        
        Args:
            ui_path: Optional path to zoom.ui. If None, uses default location.
        """
        if ui_path is None:
            # Default: ui/palettes/zoom.ui
            # This loader file is in: src/shypn/helpers/predefined_zoom.py
            # UI file is in: ui/palettes/zoom.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'palettes', 'zoom.ui')
        
        self.ui_path = ui_path
        self.builder = None
        self.zoom_control_container = None  # Main container with revealer
        self.zoom_control = None  # Main palette box
        self.zoom_revealer = None  # Revealer for zoom options
        self.zoom_display_button = None
        self.zoom_in_button = None
        self.zoom_out_button = None
        
        # Zoom level buttons
        self.zoom_buttons = {}  # {level: button}
        
        # Canvas manager reference (set externally after creation)
        self.canvas_manager = None
        self.drawing_area = None
        self.parent_window = None
        
        # CSS provider for styling
        self.css_provider = None
        
        # Font metrics for sizing
        self.target_height = 28  # Will be calculated from font metrics
    
    def load(self):
        """Load the zoom control UI and return the widget.
        
        Returns:
            Gtk.Box: The zoom control container widget.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If zoom_control_container not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Zoom control UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract widgets
        self.zoom_control_container = self.builder.get_object('zoom_control_container')
        self.zoom_control = self.builder.get_object('zoom_control')
        self.zoom_revealer = self.builder.get_object('zoom_revealer')
        self.zoom_display_button = self.builder.get_object('zoom_display_button')
        self.zoom_in_button = self.builder.get_object('zoom_in_button')
        self.zoom_out_button = self.builder.get_object('zoom_out_button')
        
        if self.zoom_control_container is None:
            raise ValueError("Object 'zoom_control_container' not found in zoom.ui")
        
        # Get zoom level buttons
        self.zoom_buttons = {
            0.25: self.builder.get_object('zoom_25'),
            0.50: self.builder.get_object('zoom_50'),
            0.75: self.builder.get_object('zoom_75'),
            1.0: self.builder.get_object('zoom_100'),
            1.5: self.builder.get_object('zoom_150'),
            2.0: self.builder.get_object('zoom_200'),
            4.0: self.builder.get_object('zoom_400'),
        }
        self.zoom_fit_button = self.builder.get_object('zoom_fit')
        
        # Connect button signals
        if self.zoom_in_button:
            self.zoom_in_button.connect('clicked', self._on_zoom_in_clicked)
        if self.zoom_out_button:
            self.zoom_out_button.connect('clicked', self._on_zoom_out_clicked)
        if self.zoom_display_button:
            self.zoom_display_button.connect('clicked', self._on_display_clicked)
        
        # Connect zoom level buttons
        for level, button in self.zoom_buttons.items():
            if button:
                button.connect('clicked', self._on_zoom_level_clicked, level)
        
        if self.zoom_fit_button:
            self.zoom_fit_button.connect('clicked', self._on_fit_clicked)
        
        # Calculate optimal size based on font metrics
        self._calculate_target_size()
        
        # Apply custom CSS styling
        self._apply_styling()
        
        return self.zoom_control_container
    
    def _calculate_target_size(self):
        """Calculate target button size as 1.3× the height of 'W' character."""
        # Create a temporary label to measure font
        temp_label = Gtk.Label(label="W")
        
        # Get the Pango layout
        layout = temp_label.get_layout()
        if layout:
            # Get pixel extents of the 'W' character
            ink_rect, logical_rect = layout.get_pixel_extents()
            w_height = logical_rect.height
            
            # Calculate target as 1.3× W height
            self.target_height = int(w_height * 1.3)
            
            # Ensure minimum size for usability
            if self.target_height < 24:
                self.target_height = 24
            
        else:
            # Fallback if layout not available
            self.target_height = 28
    
    def _apply_styling(self):
        """Apply custom CSS styling to the zoom palette.
        
        Matches SwissKnifePalette style:
        - Dark blue-gray background (#3d4e6a → #2c3a52)
        - Soft rounded corners (8px)
        - Subtle shadow for floating effect
        - Light gray/white buttons matching Swiss palette
        """
        css = f"""
        /* Main zoom palette container - matches SwissKnifePalette */
        .zoom-palette {{
            background: linear-gradient(to bottom, #3d4e6a 0%, #2c3a52 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25),
                        0 1px 3px rgba(0, 0, 0, 0.15);
        }}
        
        /* Zoom +/- buttons - match Swiss palette button style */
        .zoom-button {{
            background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            color: #3d4e6a;
            min-width: {self.target_height}px;
            min-height: {self.target_height}px;
            padding: 0;
            margin: 0;
            transition: all 150ms ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }}
        
        .zoom-button:hover {{
            background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
            border-color: rgba(255, 255, 255, 0.5);
            color: #2c3a52;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
        }}
        
        .zoom-button:active {{
            background: linear-gradient(to bottom, #e9ecef 0%, #dee2e6 100%);
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
        }}
        
        /* Zoom display button - shows current zoom level */
        .zoom-display {{
            background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            color: #3d4e6a;
            min-width: {int(self.target_height * 2)}px;
            min-height: {self.target_height}px;
            padding: 0 6px;
            margin: 0;
            transition: all 150ms ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }}
        
        .zoom-display:hover {{
            background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
            border-color: rgba(255, 255, 255, 0.5);
            color: #2c3a52;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
        }}
        
        /* Revealer content - expanded zoom options */
        .zoom-revealer-content {{
            background: linear-gradient(to bottom, #3d4e6a 0%, #2c3a52 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 6px;
            margin-top: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25),
                        0 1px 3px rgba(0, 0, 0, 0.15);
        }}
        
        /* Zoom level buttons in revealer */
        .zoom-level-button {{
            background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            color: #3d4e6a;
            min-height: {int(self.target_height * 0.9)}px;
            padding: 4px 10px;
            margin: 2px;
            transition: all 150ms ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }}
        
        .zoom-level-button:hover {{
            background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
            border-color: rgba(255, 255, 255, 0.5);
            color: #2c3a52;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
        }}
        
        .zoom-level-button:active {{
            background: linear-gradient(to bottom, #e9ecef 0%, #dee2e6 100%);
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
        }}
        """
        
        self.css_provider = Gtk.CssProvider()
        # GTK3 uses load_from_data instead of load_from_string
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply to screen (GTK3 uses Screen instead of Display)
        from gi.repository import Gdk
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def set_canvas_manager(self, manager, drawing_area, parent_window=None):
        """Set the canvas manager to control.
        
        Args:
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea to redraw after zoom changes.
            parent_window: Main window (not used in revealer approach).
        """
        self.canvas_manager = manager
        self.drawing_area = drawing_area
        self.parent_window = parent_window
        
        # Update display to show current zoom
        self._update_zoom_display()
    
    # ==================== Event Handlers ====================
    
    def _on_zoom_in_clicked(self, button):
        """Handle zoom in button click."""
        if self.canvas_manager:
            # Get viewport center for zoom
            center_x = self.canvas_manager.viewport_width / 2
            center_y = self.canvas_manager.viewport_height / 2
            self.canvas_manager.zoom_in(center_x, center_y)
            self.canvas_manager.save_view_state_to_file()
            self._update_zoom_display()
            if self.drawing_area:
                self.drawing_area.queue_draw()
    
    def _on_zoom_out_clicked(self, button):
        """Handle zoom out button click."""
        if self.canvas_manager:
            # Get viewport center for zoom
            center_x = self.canvas_manager.viewport_width / 2
            center_y = self.canvas_manager.viewport_height / 2
            self.canvas_manager.zoom_out(center_x, center_y)
            self.canvas_manager.save_view_state_to_file()
            self._update_zoom_display()
            if self.drawing_area:
                self.drawing_area.queue_draw()
    
    def _on_display_clicked(self, button):
        """Handle zoom display button click - toggle revealer visibility."""
        if self.zoom_revealer:
            # Toggle revealer state
            current_state = self.zoom_revealer.get_reveal_child()
            self.zoom_revealer.set_reveal_child(not current_state)
    
    def _on_zoom_level_clicked(self, button, level):
        """Handle predefined zoom level button click from revealer.
        
        Args:
            button: GtkButton that was clicked.
            level: Zoom level (float, e.g., 0.5, 1.0, 2.0).
        """
        if self.canvas_manager:
            # Get viewport center for zoom
            center_x = self.canvas_manager.viewport_width / 2
            center_y = self.canvas_manager.viewport_height / 2
            self.canvas_manager.set_zoom(level, center_x, center_y)
            self.canvas_manager.save_view_state_to_file()
            self._update_zoom_display()
            if self.drawing_area:
                self.drawing_area.queue_draw()
        
        # Close revealer after selection
        if self.zoom_revealer:
            self.zoom_revealer.set_reveal_child(False)
    
    def _on_fit_clicked(self, button):
        """Handle fit-to-window button click.
        
        This would calculate zoom to fit entire canvas in viewport.
        For now, we'll just set to 100%.
        """
        if self.canvas_manager:
            center_x = self.canvas_manager.viewport_width / 2
            center_y = self.canvas_manager.viewport_height / 2
            self.canvas_manager.set_zoom(1.0, center_x, center_y)
            self._update_zoom_display()
            if self.drawing_area:
                self.drawing_area.queue_draw()
        
        # Close revealer
        if self.zoom_revealer:
            self.zoom_revealer.set_reveal_child(False)
    
    def _update_zoom_display(self):
        """Update the zoom display button with current zoom level.
        
        Shows magnitude in format: 1.5× or 100%
        """
        if self.canvas_manager:
            zoom = self.canvas_manager.zoom
            # Format as magnitude (e.g., "1.5×") for better visual clarity
            if zoom == 1.0:
                self.zoom_display_button.set_label("1×")
            elif zoom < 1.0:
                # For zoom < 1, show as magnitude (e.g., 0.5× or 50%)
                self.zoom_display_button.set_label(f"{zoom:.2g}×")
            else:
                # For zoom > 1, show as magnitude (e.g., 1.5× or 2×)
                self.zoom_display_button.set_label(f"{zoom:.3g}×")
        else:
            self.zoom_display_button.set_label("1×")
    
    def update_zoom_display(self):
        """Public method to update zoom display (called externally after zoom changes)."""
        self._update_zoom_display()
    
    def get_widget(self):
        """Get the zoom control container widget.
        
        Returns:
            Gtk.Box: The zoom control container widget, or None if not loaded.
        """
        return self.zoom_control_container


def create_zoom_palette(ui_path=None):
    """Convenience function to create and load the zoom palette.
    
    Args:
        ui_path: Optional path to zoom.ui.
        
    Returns:
        PredefinedZoom: The loaded zoom palette instance.
        
    Example:
        palette = create_zoom_palette()
        widget = palette.load()
        palette.set_canvas_manager(manager, drawing_area)
        # Add widget as overlay to canvas
    """
    palette = PredefinedZoom(ui_path)
    palette.load()
    return palette
