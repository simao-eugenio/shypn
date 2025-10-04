"""
Arc Properties Dialog Loader

Loads and manages the Arc properties dialog UI.
"""

import os
import json
import ast
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from shypn.helpers.color_picker import setup_color_picker_in_dialog


class ArcPropDialogLoader(GObject.GObject):
    """Loader for Arc properties dialog.
    
    This class loads and manages the Arc properties dialog UI from
    arc_prop_dialog.ui. The dialog allows editing Arc attributes
    such as weight, label, and other properties.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, arc_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
        """Initialize the Arc properties dialog loader.
        
        Args:
            arc_obj: Arc object to edit properties for.
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
        self.ui_path = os.path.join(ui_dir, 'arc_prop_dialog.ui')
        self.arc_obj = arc_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        
        # Widget references
        self.builder = None
        self.dialog = None
        self.color_picker = None
        
        # Load UI
        self._load_ui()
        self._setup_color_picker()
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
        
        # Wire OK/Cancel buttons
        ok_button = self.builder.get_object('ok_button')
        cancel_button = self.builder.get_object('cancel_button')
        
        if ok_button:
            ok_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.OK))
        if cancel_button:
            cancel_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.CANCEL))
        
        # Connect signals
        self.dialog.connect('response', self._on_response)
        
        print(f"[ArcPropDialogLoader] UI loaded successfully from {self.ui_path}")
    
    def _setup_color_picker(self):
        """Setup color picker widget for arc color selection."""
        current_color = getattr(self.arc_obj, 'color', (0.0, 0.0, 0.0))
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'arc_color_picker',
            current_color=current_color,
            button_size=28
        )
        
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
            print("[ArcPropDialogLoader] Color picker setup complete")
    
    def _on_color_selected(self, color_picker, color_rgb):
        """Handle color selection from color picker.
        
        Args:
            color_picker: ColorPickerRow instance
            color_rgb: Selected color as RGB tuple (0.0-1.0)
        """
        print(f"[ArcPropDialogLoader] Color selected: {color_rgb}")
    
    def _populate_fields(self):
        """Populate dialog fields with current Arc properties."""
        # Name field (read-only)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.arc_obj, 'name'):
            name_entry.set_text(str(self.arc_obj.name))
            name_entry.set_editable(False)  # Name is immutable
        
        # Description/Label field (TextView)
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.arc_obj, 'label'):
            buffer = description_text.get_buffer()
            label_text = str(self.arc_obj.label) if self.arc_obj.label else ''
            buffer.set_text(label_text)
        
        # Weight field
        weight_entry = self.builder.get_object('prop_arc_weight_entry')
        if weight_entry and hasattr(self.arc_obj, 'weight'):
            weight_entry.set_text(str(self.arc_obj.weight))
        
        # Line width field
        line_width_spin = self.builder.get_object('prop_arc_line_width_spin')
        if line_width_spin and hasattr(self.arc_obj, 'width'):
            line_width_spin.set_value(float(self.arc_obj.width))
        
        # Threshold field (TextView)
        threshold_textview = self.builder.get_object('prop_arc_threshold_entry')
        if threshold_textview and hasattr(self.arc_obj, 'threshold'):
            buffer = threshold_textview.get_buffer()
            threshold_text = self._format_threshold_for_display(self.arc_obj.threshold)
            buffer.set_text(threshold_text)
        
        # Source/Target info labels (read-only)
        source_info = self.builder.get_object('source_info_label')
        target_info = self.builder.get_object('target_info_label')
        
        if source_info and hasattr(self.arc_obj, 'source'):
            source_name = getattr(self.arc_obj.source, 'name', 'Unknown')
            source_info.set_text(f"Source: {source_name}")
        
        if target_info and hasattr(self.arc_obj, 'target'):
            target_name = getattr(self.arc_obj.target, 'name', 'Unknown')
            target_info.set_text(f"Target: {target_name}")
    
    def _format_threshold_for_display(self, threshold):
        """Format threshold value for display in UI TextView.
        
        Args:
            threshold: Can be None, dict, number, or string
        
        Returns:
            String representation for display
        """
        if threshold is None:
            return ""
        elif isinstance(threshold, dict):
            # Format dict as JSON for readability
            return json.dumps(threshold, indent=2)
        elif isinstance(threshold, (int, float)):
            return str(threshold)
        else:
            # Already a string
            return str(threshold)
    
    def _parse_threshold(self, text):
        """Parse threshold text from UI into appropriate format.
        
        Supports multiple formats:
        - Empty string → None
        - Number string → numeric value
        - Dictionary string → parsed dict
        - Expression string → kept as string
        
        Args:
            text: Raw text from TextView
        
        Returns:
            Parsed threshold (None, number, dict, or string)
        """
        text = text.strip()
        if not text:
            return None
        
        # Try to parse as number
        try:
            # Check if it's a float
            if '.' in text:
                return float(text)
            else:
                return int(text)
        except ValueError:
            pass
        
        # Try to parse as dictionary (using ast.literal_eval for safety)
        if text.startswith('{') and text.endswith('}'):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, dict):
                    return parsed
            except (ValueError, SyntaxError) as e:
                print(f"[ArcPropDialogLoader] Warning: Could not parse threshold as dict: {e}")
        
        # Keep as string expression (will be evaluated at runtime)
        return text
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        print(f"[ArcPropDialogLoader] Dialog response: {response_id}")
        
        if response_id == Gtk.ResponseType.OK:
            print(f"[ArcPropDialogLoader] OK clicked, applying changes...")
            self._apply_changes()
            
            # Mark document as dirty if persistency manager is available
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
                print(f"[ArcPropDialogLoader] Document marked as dirty")
            
            # Emit signal to notify observers (for canvas redraw)
            self.emit('properties-changed')
            print(f"[ArcPropDialogLoader] Properties changed signal emitted")
        else:
            print(f"[ArcPropDialogLoader] Dialog cancelled or closed")
        
        print(f"[ArcPropDialogLoader] Destroying dialog...")
        dialog.destroy()
        print(f"[ArcPropDialogLoader] Dialog destroyed")
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Arc object."""
        print(f"[ArcPropDialogLoader] _apply_changes called - Arc ID: {id(self.arc_obj)}")
        
        # Description/Label field (TextView)
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.arc_obj, 'label'):
            buffer = description_text.get_buffer()
            start, end = buffer.get_bounds()
            label_text = buffer.get_text(start, end, True).strip()
            self.arc_obj.label = label_text if label_text else None
            print(f"[ArcPropDialogLoader] Label set to: {self.arc_obj.label}")
        
        # Weight field
        weight_entry = self.builder.get_object('prop_arc_weight_entry')
        if weight_entry and hasattr(self.arc_obj, 'weight'):
            try:
                weight_text = weight_entry.get_text().strip()
                weight_value = int(weight_text) if weight_text else 1
                old_weight = self.arc_obj.weight
                self.arc_obj.weight = max(1, weight_value)  # Minimum weight is 1
                print(f"[ArcPropDialogLoader] Weight changed: {old_weight} -> {self.arc_obj.weight}")
            except ValueError:
                print(f"[ArcPropDialogLoader] Invalid weight value, keeping current: {self.arc_obj.weight}")
        
        # Line width field
        line_width_spin = self.builder.get_object('prop_arc_line_width_spin')
        if line_width_spin and hasattr(self.arc_obj, 'width'):
            old_width = self.arc_obj.width
            self.arc_obj.width = float(line_width_spin.get_value())
            print(f"[ArcPropDialogLoader] Width changed: {old_width} -> {self.arc_obj.width}")
        
        # Color from color picker
        if self.color_picker and hasattr(self.arc_obj, 'color'):
            old_color = self.arc_obj.color
            selected_color = self.color_picker.get_selected_color()
            self.arc_obj.color = selected_color
            print(f"[ArcPropDialogLoader] Color changed: {old_color} -> {self.arc_obj.color}")
        
        # Threshold field (TextView)
        threshold_textview = self.builder.get_object('prop_arc_threshold_entry')
        if threshold_textview and hasattr(self.arc_obj, 'threshold'):
            buffer = threshold_textview.get_buffer()
            start, end = buffer.get_bounds()
            threshold_text = buffer.get_text(start, end, True).strip()
            old_threshold = self.arc_obj.threshold
            self.arc_obj.threshold = self._parse_threshold(threshold_text)
            print(f"[ArcPropDialogLoader] Threshold changed: {old_threshold} -> {self.arc_obj.threshold}")
        
        print(f"[ArcPropDialogLoader] Applied changes complete - Arc: weight={self.arc_obj.weight}, " 
              f"width={self.arc_obj.width}, color={self.arc_obj.color}, label={self.arc_obj.label}, "
              f"threshold={self.arc_obj.threshold}")
    
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
def create_arc_prop_dialog(arc_obj, parent_window=None, ui_dir: str = None, persistency_manager=None):
    """Factory function to create an Arc properties dialog loader.
    
    Args:
        arc_obj: Arc object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
    
    Returns:
        ArcPropDialogLoader: Configured dialog loader instance.
    """
    return ArcPropDialogLoader(arc_obj, parent_window=parent_window, ui_dir=ui_dir, persistency_manager=persistency_manager)
