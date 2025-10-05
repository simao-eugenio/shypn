"""
Place Properties Dialog Loader

Loads and manages the Place properties dialog UI.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from shypn.helpers.color_picker import setup_color_picker_in_dialog


class PlacePropDialogLoader(GObject.GObject):
    """Loader for Place properties dialog.
    
    This class loads and manages the Place properties dialog UI from
    place_prop_dialog.ui. The dialog allows editing Place attributes
    such as name, initial marking, and other properties.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, place_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
        """Initialize the Place properties dialog loader.
        
        Args:
            place_obj: Place object to edit properties for.
            parent_window: Parent window for modal dialog.
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
            persistency_manager: NetObjPersistency instance for marking document dirty
        """
        super().__init__()
        
        # Determine UI directory
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'place_prop_dialog.ui')
        self.place_obj = place_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        
        # Widget references
        self.builder = None
        self.dialog = None
        self.color_picker = None  # Will be created and inserted into dialog
        
        # Load UI
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
    
    def _load_ui(self):
        """Load the Place properties dialog UI from file."""
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Place properties dialog UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract main dialog widget
        self.dialog = self.builder.get_object('place_properties_dialog')
        
        if self.dialog is None:
            raise ValueError("Object 'place_properties_dialog' not found in place_prop_dialog.ui")
        
        # Set parent window if provided
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        
        # Connect signals
        self.dialog.connect('response', self._on_response)
        
        print(f"[PlacePropDialogLoader] UI loaded successfully from {self.ui_path}")
    
    def _setup_color_picker(self):
        """Setup and insert the color picker widget into the dialog."""
        # Get current border color from place object
        current_color = getattr(self.place_obj, 'border_color', (0.0, 0.0, 0.0))
        
        # Use helper function to setup color picker
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'place_color_picker',
            current_color=current_color,
            button_size=28
        )
        
        # Connect to color selection signal if picker was created
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
    
    def _on_color_selected(self, picker, color_rgb):
        """Handle color selection from picker.
        
        Args:
            picker: ColorPickerRow widget
            color_rgb: Selected RGB tuple (0.0-1.0)
        """
        r, g, b = color_rgb
        print(f"[PlacePropDialogLoader] Color selected: RGB({r:.2f}, {g:.2f}, {b:.2f})")
    
    def _populate_fields(self):
        """Populate dialog fields with current Place properties."""
        # Name field (read-only, system-assigned)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.place_obj, 'name'):
            name_entry.set_text(str(self.place_obj.name))
            name_entry.set_editable(False)  # Name is immutable
            name_entry.set_can_focus(False)
        
        # Tokens field (Entry widget)
        tokens_entry = self.builder.get_object('prop_place_tokens_entry')
        if tokens_entry and hasattr(self.place_obj, 'tokens'):
            tokens_entry.set_text(str(self.place_obj.tokens))
        
        # Radius field (Entry widget)
        radius_entry = self.builder.get_object('prop_place_radius_entry')
        if radius_entry and hasattr(self.place_obj, 'radius'):
            radius_entry.set_text(str(self.place_obj.radius))
        
        # Description field (TextView)
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.place_obj, 'label'):
            buffer = description_text.get_buffer()
            buffer.set_text(str(self.place_obj.label) if self.place_obj.label else '')
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            
            # Mark document as dirty if persistency manager is available
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
                print(f"[PlacePropDialogLoader] Document marked as dirty")
            
            # Emit signal to notify observers (for canvas redraw)
            self.emit('properties-changed')
        
        dialog.destroy()
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Place object."""
        # Name field is read-only (immutable, system-assigned) - skip it
        
        # Tokens field (Entry widget - parse as float/int)
        tokens_entry = self.builder.get_object('prop_place_tokens_entry')
        if tokens_entry and hasattr(self.place_obj, 'tokens'):
            try:
                tokens_text = tokens_entry.get_text().strip()
                if tokens_text:
                    # Try parsing as int first, then float
                    if '.' in tokens_text:
                        tokens_value = float(tokens_text)
                    else:
                        tokens_value = int(tokens_text)
                    self.place_obj.tokens = max(0, tokens_value)  # Ensure non-negative
                    # Also update initial_marking so reset works correctly
                    self.place_obj.initial_marking = self.place_obj.tokens
                    print(f"[PlacePropDialogLoader] Set tokens and initial_marking to {self.place_obj.tokens}")
            except ValueError as e:
                print(f"[PlacePropDialogLoader] Invalid tokens value: {tokens_text}, error: {e}")
        
        # Radius field (Entry widget - parse as float)
        radius_entry = self.builder.get_object('prop_place_radius_entry')
        if radius_entry and hasattr(self.place_obj, 'radius'):
            try:
                radius_text = radius_entry.get_text().strip()
                if radius_text:
                    radius_value = float(radius_text)
                    self.place_obj.radius = max(1.0, radius_value)  # Ensure positive
                    print(f"[PlacePropDialogLoader] Set radius to {self.place_obj.radius}")
            except ValueError as e:
                print(f"[PlacePropDialogLoader] Invalid radius value: {radius_text}, error: {e}")
        
        # Border color from color picker
        if self.color_picker and hasattr(self.place_obj, 'border_color'):
            selected_color = self.color_picker.get_selected_color()
            self.place_obj.border_color = selected_color
            r, g, b = selected_color
            print(f"[PlacePropDialogLoader] Set border_color to ({r:.2f}, {g:.2f}, {b:.2f})")
        
        # Description field (TextView) - maps to label property
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.place_obj, 'label'):
            buffer = description_text.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            new_description = buffer.get_text(start_iter, end_iter, True).strip()
            self.place_obj.label = new_description if new_description else None
        
        print(f"[PlacePropDialogLoader] Applied changes to Place: {self.place_obj.name}, tokens={self.place_obj.tokens}")
    
    def run(self):
        """Show the dialog and run it modally.
        
        Returns:
            Response ID from the dialog.
        """
        return self.dialog.run()
    
    def get_dialog(self):
        """Get the dialog widget.
        
        Returns:
            Gtk.Dialog: The dialog widget.
        """
        return self.dialog


# Factory function for convenience
def create_place_prop_dialog(place_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
    """Factory function to create a Place properties dialog loader.
    
    Args:
        place_obj: Place object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
    
    Returns:
        PlacePropDialogLoader: Configured dialog loader instance.
    """
    return PlacePropDialogLoader(place_obj, parent_window=parent_window, ui_dir=ui_dir, persistency_manager=persistency_manager)
