"""
Transition Properties Dialog Loader

Loads and manages the Transition properties dialog UI.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class TransitionPropDialogLoader(GObject.GObject):
    """Loader for Transition properties dialog.
    
    This class loads and manages the Transition properties dialog UI from
    transition_prop_dialog.ui. The dialog allows editing Transition attributes
    such as name, label, and other properties.
    """
    
    def __init__(self, transition_obj, parent_window=None, ui_dir: str = None):
        """Initialize the Transition properties dialog loader.
        
        Args:
            transition_obj: Transition object to edit properties for.
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
        self.ui_path = os.path.join(ui_dir, 'transition_prop_dialog.ui')
        self.transition_obj = transition_obj
        self.parent_window = parent_window
        
        # Widget references
        self.builder = None
        self.dialog = None
        
        # Load UI
        self._load_ui()
        self._populate_fields()
    
    def _load_ui(self):
        """Load the Transition properties dialog UI from file."""
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Transition properties dialog UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract main dialog widget
        self.dialog = self.builder.get_object('transition_properties_dialog')
        
        if self.dialog is None:
            raise ValueError("Object 'transition_properties_dialog' not found in transition_prop_dialog.ui")
        
        # Set parent window if provided
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        
        # Connect signals
        self.dialog.connect('response', self._on_response)
        
        print(f"[TransitionPropDialogLoader] UI loaded successfully from {self.ui_path}")
    
    def _populate_fields(self):
        """Populate dialog fields with current Transition properties."""
        # Get widget references (these will depend on the actual UI structure)
        
        # Name field
        name_entry = self.builder.get_object('transition_name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            name_entry.set_text(str(self.transition_obj.name))
        
        # Label field
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            label_entry.set_text(str(self.transition_obj.label) if self.transition_obj.label else '')
    
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
        """Apply changes from dialog fields to Transition object."""
        # Name field
        name_entry = self.builder.get_object('transition_name_entry')
        if name_entry:
            new_name = name_entry.get_text().strip()
            if new_name and hasattr(self.transition_obj, 'name'):
                self.transition_obj.name = new_name
        
        # Label field
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            new_label = label_entry.get_text().strip()
            self.transition_obj.label = new_label if new_label else None
        
        print(f"[TransitionPropDialogLoader] Applied changes to Transition: {self.transition_obj.name}")
    
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
def create_transition_prop_dialog(transition_obj, parent_window=None, ui_dir: str = None):
    """Factory function to create a Transition properties dialog loader.
    
    Args:
        transition_obj: Transition object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
    
    Returns:
        TransitionPropDialogLoader: Configured dialog loader instance.
    """
    return TransitionPropDialogLoader(transition_obj, parent_window=parent_window, ui_dir=ui_dir)
