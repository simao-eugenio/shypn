"""
Arc Properties Dialog Loader

Loads and manages the Arc properties dialog UI.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class ArcPropDialogLoader(GObject.GObject):
    """Loader for Arc properties dialog.
    
    This class loads and manages the Arc properties dialog UI from
    arc_prop_dialog.ui. The dialog allows editing Arc attributes
    such as weight, label, and other properties.
    """
    
    def __init__(self, arc_obj, parent_window=None, ui_dir: str = None):
        """Initialize the Arc properties dialog loader.
        
        Args:
            arc_obj: Arc object to edit properties for.
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
        self.ui_path = os.path.join(ui_dir, 'arc_prop_dialog.ui')
        self.arc_obj = arc_obj
        self.parent_window = parent_window
        
        # Widget references
        self.builder = None
        self.dialog = None
        
        # Load UI
        self._load_ui()
        self._populate_fields()
    
    def _load_ui(self):
        """Load the Arc properties dialog UI from file."""
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Arc properties dialog UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract main dialog widget
        self.dialog = self.builder.get_object('arc_properties_dialog')
        
        if self.dialog is None:
            raise ValueError("Object 'arc_properties_dialog' not found in arc_prop_dialog.ui")
        
        # Set parent window if provided
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        
        # Connect signals
        self.dialog.connect('response', self._on_response)
        
        print(f"[ArcPropDialogLoader] UI loaded successfully from {self.ui_path}")
    
    def _populate_fields(self):
        """Populate dialog fields with current Arc properties."""
        # Get widget references (these will depend on the actual UI structure)
        
        # Weight field
        weight_spin = self.builder.get_object('arc_weight_spin')
        if weight_spin and hasattr(self.arc_obj, 'weight'):
            weight_spin.set_value(float(self.arc_obj.weight))
        
        # Label field
        label_entry = self.builder.get_object('arc_label_entry')
        if label_entry and hasattr(self.arc_obj, 'label'):
            label_entry.set_text(str(self.arc_obj.label) if self.arc_obj.label else '')
    
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
        """Apply changes from dialog fields to Arc object."""
        # Weight field
        weight_spin = self.builder.get_object('arc_weight_spin')
        if weight_spin and hasattr(self.arc_obj, 'weight'):
            self.arc_obj.weight = int(weight_spin.get_value())
        
        # Label field
        label_entry = self.builder.get_object('arc_label_entry')
        if label_entry and hasattr(self.arc_obj, 'label'):
            new_label = label_entry.get_text().strip()
            self.arc_obj.label = new_label if new_label else None
        
        print(f"[ArcPropDialogLoader] Applied changes to Arc")
    
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
def create_arc_prop_dialog(arc_obj, parent_window=None, ui_dir: str = None):
    """Factory function to create an Arc properties dialog loader.
    
    Args:
        arc_obj: Arc object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
    
    Returns:
        ArcPropDialogLoader: Configured dialog loader instance.
    """
    return ArcPropDialogLoader(arc_obj, parent_window=parent_window, ui_dir=ui_dir)
