#!/usr/bin/env python3
"""
Color Picker Helper

Provides a one-line scrollable color picker widget for property dialogs.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject


class ColorPickerRow(Gtk.ScrolledWindow):
    """A scrollable row of color buttons for quick color selection.
    
    Displays a horizontal row of predefined colors that users can select.
    Emits 'color-selected' signal when a color is chosen.
    
    Signals:
        color-selected: Emitted when a color button is clicked (color_rgb tuple)
    """
    
    __gsignals__ = {
        'color-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }
    
    # Predefined color palette (RGB tuples 0.0-1.0)
    COLORS = [
        # Basics
        (0.0, 0.0, 0.0),       # Black
        (1.0, 1.0, 1.0),       # White
        (0.5, 0.5, 0.5),       # Gray
        
        # Primary
        (1.0, 0.0, 0.0),       # Red
        (0.0, 1.0, 0.0),       # Green
        (0.0, 0.0, 1.0),       # Blue
        
        # Secondary
        (1.0, 1.0, 0.0),       # Yellow
        (1.0, 0.0, 1.0),       # Magenta
        (0.0, 1.0, 1.0),       # Cyan
        
        # Warm colors
        (1.0, 0.5, 0.0),       # Orange
        (1.0, 0.75, 0.0),      # Gold
        (0.8, 0.4, 0.0),       # Brown
        
        # Cool colors
        (0.0, 0.5, 1.0),       # Sky Blue
        (0.5, 0.0, 1.0),       # Purple
        (0.0, 0.8, 0.6),       # Teal
        
        # Pastels
        (1.0, 0.8, 0.8),       # Pink
        (0.8, 1.0, 0.8),       # Light Green
        (0.8, 0.8, 1.0),       # Lavender
        
        # Earth tones
        (0.6, 0.4, 0.2),       # Dark Brown
        (0.4, 0.6, 0.3),       # Olive
        (0.7, 0.5, 0.3),       # Tan
    ]
    
    def __init__(self, current_color=None, button_size=32):
        """Initialize the color picker row.
        
        Args:
            current_color: Currently selected color (RGB tuple 0.0-1.0)
            button_size: Size of each color button in pixels (default: 32)
        """
        super().__init__()
        
        self.button_size = button_size
        self.current_color = current_color or (0.0, 0.0, 0.0)
        self.color_buttons = []
        self.selected_box = None  # Track currently selected EventBox
        
        # Configure scrolled window
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.set_min_content_height(button_size + 10)
        self.set_max_content_height(button_size + 10)
        
        # Create horizontal box for color buttons (no spacing or margins)
        self.color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.color_box.set_margin_top(0)
        self.color_box.set_margin_bottom(0)
        self.color_box.set_margin_left(0)
        self.color_box.set_margin_right(0)
        
        # Add color buttons
        self._create_color_buttons()
        
        # Add to scrolled window
        self.add(self.color_box)
        self.show_all()
    
    def _create_color_buttons(self):
        """Create color buttons for each predefined color."""
        for color_rgb in self.COLORS:
            button = self._create_color_button(color_rgb)
            self.color_buttons.append(button)
            self.color_box.pack_start(button, False, False, 0)
    
    def _create_color_button(self, color_rgb):
        """Create a single color button.
        
        Args:
            color_rgb: RGB tuple (0.0-1.0)
            
        Returns:
            Gtk.EventBox: Configured color button (using EventBox for tighter spacing)
        """
        # Use EventBox instead of Button for no spacing
        event_box = Gtk.EventBox()
        event_box.set_size_request(self.button_size, self.button_size)
        
        # Create drawing area for color display (full size, no padding)
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_size_request(self.button_size, self.button_size)
        drawing_area.connect('draw', self._on_draw_color, color_rgb)
        
        event_box.add(drawing_area)
        event_box.connect('button-press-event', lambda w, e: self._on_color_clicked(w, color_rgb))
        
        # Add tooltip with RGB values
        r, g, b = color_rgb
        tooltip = f"RGB: ({int(r*255)}, {int(g*255)}, {int(b*255)})"
        event_box.set_tooltip_text(tooltip)
        
        # Store reference for selection tracking
        if self._colors_match(color_rgb, self.current_color):
            # Mark as selected by storing in instance variable
            self.selected_box = event_box
        
        return event_box
    
    def _on_draw_color(self, widget, cr, color_rgb):
        """Draw the color preview in the button.
        
        Args:
            widget: DrawingArea widget
            cr: Cairo context
            color_rgb: RGB tuple (0.0-1.0)
        """
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Check if this is the selected color
        event_box = widget.get_parent()
        is_selected = event_box == self.selected_box
        
        # Fill with color
        cr.set_source_rgb(*color_rgb)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        # Draw border (thicker for selected)
        if is_selected:
            # Selected: thicker border
            cr.set_source_rgb(0.2, 0.2, 0.2)
            cr.set_line_width(3)
            cr.rectangle(1.5, 1.5, width - 3, height - 3)
        else:
            # Unselected: thin border
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.set_line_width(1)
            cr.rectangle(0.5, 0.5, width - 1, height - 1)
        cr.stroke()
        
        return False
    
    def _on_color_clicked(self, event_box, color_rgb):
        """Handle color button click.
        
        Args:
            event_box: Clicked EventBox
            color_rgb: RGB tuple (0.0-1.0)
        """
        # Update current color
        self.current_color = color_rgb
        self.selected_box = event_box
        
        # Force redraw of all color buttons to update selection indicator
        for box in self.color_buttons:
            child = box.get_child()
            if child:
                child.queue_draw()
        
        # Emit signal
        self.emit('color-selected', color_rgb)
    
    def _colors_match(self, color1, color2, tolerance=0.01):
        """Check if two colors match within tolerance.
        
        Args:
            color1: First RGB tuple
            color2: Second RGB tuple
            tolerance: Maximum difference per channel
            
        Returns:
            bool: True if colors match
        """
        return all(abs(c1 - c2) < tolerance for c1, c2 in zip(color1, color2))
    
    def get_selected_color(self):
        """Get the currently selected color.
        
        Returns:
            tuple: RGB tuple (0.0-1.0)
        """
        return self.current_color
    
    def set_selected_color(self, color_rgb):
        """Set the currently selected color.
        
        Args:
            color_rgb: RGB tuple (0.0-1.0)
        """
        self.current_color = color_rgb
        
        # Update button relief
        for button in self.color_buttons:
            button.set_relief(Gtk.ReliefStyle.NONE)
        
        # Find and highlight matching button
        for i, color in enumerate(self.COLORS):
            if self._colors_match(color, color_rgb):
                self.color_buttons[i].set_relief(Gtk.ReliefStyle.NORMAL)
                break


def create_color_picker(current_color=None, button_size=32):
    """Factory function to create a color picker row.
    
    Args:
        current_color: Currently selected color (RGB tuple 0.0-1.0)
        button_size: Size of each color button in pixels (default: 32)
        
    Returns:
        ColorPickerRow: Configured color picker widget
    """
    return ColorPickerRow(current_color=current_color, button_size=button_size)


def setup_color_picker_in_dialog(builder, container_id, current_color=None, button_size=28):
    """Helper function to setup color picker in any dialog.
    
    This function integrates a color picker into a dialog by:
    1. Finding the container widget by ID
    2. Removing any placeholder content
    3. Creating and inserting the color picker
    
    Usage in dialog loaders:
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'place_color_picker',  # Container ID from UI file
            current_color=self.obj.border_color
        )
        
        # Later, to get selected color:
        selected_color = self.color_picker.get_selected_color()
    
    Args:
        builder: Gtk.Builder instance with loaded UI
        container_id: ID of the container widget (usually a GtkBox)
        current_color: Currently selected color (RGB tuple 0.0-1.0)
        button_size: Size of each color button in pixels (default: 28)
        
    Returns:
        ColorPickerRow: The created color picker widget, or None if container not found
    """
    # Get the container box where color picker should be inserted
    color_container = builder.get_object(container_id)
    if not color_container:
        print(f"[ColorPicker] Warning: Container '{container_id}' not found in dialog")
        return None
    
    # Remove placeholder content (labels, etc.)
    for child in color_container.get_children():
        color_container.remove(child)
    
    # Create color picker with current color
    color_picker = create_color_picker(current_color=current_color, button_size=button_size)
    
    # Add to container
    color_container.pack_start(color_picker, True, True, 0)
    color_container.show_all()
    
    print(f"[ColorPicker] Inserted into '{container_id}' with color {current_color}")
    
    return color_picker


# Test function for standalone execution
if __name__ == '__main__':
    def on_color_selected(picker, color_rgb):
        r, g, b = color_rgb
        print(f"Selected color: RGB({r:.2f}, {g:.2f}, {b:.2f}) = ({int(r*255)}, {int(g*255)}, {int(b*255)})")
    
    window = Gtk.Window(title="Color Picker Test")
    window.set_default_size(600, 100)
    window.connect('destroy', Gtk.main_quit)
    
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)
    box.set_margin_left(10)
    box.set_margin_right(10)
    
    label = Gtk.Label(label="Select a color:")
    box.pack_start(label, False, False, 0)
    
    # Create color picker with red as initial color
    picker = create_color_picker(current_color=(1.0, 0.0, 0.0))
    picker.connect('color-selected', on_color_selected)
    box.pack_start(picker, False, False, 0)
    
    window.add(box)
    window.show_all()
    
    Gtk.main()
