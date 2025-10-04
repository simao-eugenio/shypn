"""
Place Properties Dialog Loader

Loads and manages the Place properties dialog UI.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class PlacePropDialogLoader(GObject.GObject):
    """Loader for Place properties dialog.
    
    This class loads and manages the Place properties dialog UI from
    place_prop_dialog.ui. The dialog allows editing Place attributes
    such as name, initial marking, and other properties.
    """
    
    def __init__(self, place_obj, parent_window=None, ui_dir: str = None):
        """Initialize the Place properties dialog loader.
        
        Args:
            place_obj: Place object to edit properties for.
            parent_window: Parent window for modal dialog.
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
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
        
        # Widget references
        self.builder = None
        self.dialog = None
        
        # Load UI
        self._load_ui()
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
    
    def _populate_fields(self):
        """Populate dialog fields with current Place properties."""
        # Get widget references (these will depend on the actual UI structure)
        # For now, we'll handle common Place properties
        
        # Name field
        name_entry = self.builder.get_object('place_name_entry')
        if name_entry and hasattr(self.place_obj, 'name'):
            name_entry.set_text(str(self.place_obj.name))
        
        # Initial marking field
        marking_spin = self.builder.get_object('place_marking_spin')
        if marking_spin and hasattr(self.place_obj, 'marking'):
            marking_spin.set_value(float(self.place_obj.marking))
        
        # Label field
        label_entry = self.builder.get_object('place_label_entry')
        if label_entry and hasattr(self.place_obj, 'label'):
            label_entry.set_text(str(self.place_obj.label) if self.place_obj.label else '')
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
        
        dialog.destroy()
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Place object."""
        # Name field
        name_entry = self.builder.get_object('place_name_entry')
        if name_entry:
            new_name = name_entry.get_text().strip()
            if new_name and hasattr(self.place_obj, 'name'):
                self.place_obj.name = new_name
        
        # Initial marking field
        marking_spin = self.builder.get_object('place_marking_spin')
        if marking_spin and hasattr(self.place_obj, 'marking'):
            self.place_obj.marking = int(marking_spin.get_value())
        
        # Label field
        label_entry = self.builder.get_object('place_label_entry')
        if label_entry and hasattr(self.place_obj, 'label'):
            new_label = label_entry.get_text().strip()
            self.place_obj.label = new_label if new_label else None
        
        print(f"[PlacePropDialogLoader] Applied changes to Place: {self.place_obj.name}")
    
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
def create_place_prop_dialog(place_obj, parent_window=None, ui_dir: str = None):
    """Factory function to create a Place properties dialog loader.
    
    Args:
        place_obj: Place object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
    
    Returns:
        PlacePropDialogLoader: Configured dialog loader instance.
    """
    return PlacePropDialogLoader(place_obj, parent_window=parent_window, ui_dir=ui_dir)
