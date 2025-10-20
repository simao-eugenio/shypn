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
from shypn.utils.arc_transform import is_inhibitor, convert_to_inhibitor, convert_to_normal

class ArcPropDialogLoader(GObject.GObject):
    """Loader for Arc properties dialog.
    
    This class loads and manages the Arc properties dialog UI from
    arc_prop_dialog.ui. The dialog allows editing Arc attributes
    such as weight, label, and other properties.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    __gsignals__ = {'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, arc_obj, parent_window=None, ui_dir: str=None, persistency_manager=None, model=None):
        """Initialize the Arc properties dialog loader.
        
        Args:
            arc_obj: Arc object to edit properties for.
            parent_window: Parent window for modal dialog.
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
            persistency_manager: NetObjPersistency instance for marking document dirty
            model: PetriNetModel instance for topology analysis (optional)
        """
        super().__init__()
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'arc_prop_dialog.ui')
        self.arc_obj = arc_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        self.model = model
        self.builder = None
        self.dialog = None
        self.color_picker = None
        self.topology_loader = None
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._setup_topology_tab()

    def _load_ui(self):
        """Load the Arc properties dialog UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Arc properties dialog UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('arc_properties_dialog')
        if self.dialog is None:
            raise ValueError("Object 'arc_properties_dialog' not found in arc_prop_dialog.ui")
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        ok_button = self.builder.get_object('ok_button')
        cancel_button = self.builder.get_object('cancel_button')
        if ok_button:
            ok_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.OK))
        if cancel_button:
            cancel_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.CANCEL))
        self.dialog.connect('response', self._on_response)

    def _setup_color_picker(self):
        """Setup color picker widget for arc color selection."""
        current_color = getattr(self.arc_obj, 'color', (0.0, 0.0, 0.0))
        self.color_picker = setup_color_picker_in_dialog(self.builder, 'arc_color_picker', current_color=current_color, button_size=28)
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)

    def _on_color_selected(self, color_picker, color_rgb):
        """Handle color selection from color picker.
        
        Args:
            color_picker: ColorPickerRow instance
            color_rgb: Selected color as RGB tuple (0.0-1.0)
        """

    def _replace_arc_in_model(self):
        """Replace the old arc with the transformed arc in the model.
        
        This method finds the old arc in the model's arc list and replaces it
        with the new transformed arc object (self.arc_obj).
        """
        # Check if arc has a manager reference
        if hasattr(self.arc_obj, '_manager') and self.arc_obj._manager:
            manager = self.arc_obj._manager
            # Find and replace in manager's arc list
            if hasattr(manager, 'arcs'):
                for i, arc in enumerate(manager.arcs):
                    if arc.id == self.arc_obj.id:
                        manager.arcs[i] = self.arc_obj
                        break
        
        # Notify that the arc was transformed (for redrawing, etc.)
        if hasattr(self.arc_obj, 'on_changed') and self.arc_obj.on_changed:
            self.arc_obj.on_changed(self.arc_obj, 'type_transformed')

    def _populate_fields(self):
        """Populate dialog fields with current Arc properties."""
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.arc_obj, 'name'):
            name_entry.set_text(str(self.arc_obj.name))
            name_entry.set_editable(False)
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.arc_obj, 'label'):
            buffer = description_text.get_buffer()
            label_text = str(self.arc_obj.label) if self.arc_obj.label else ''
            buffer.set_text(label_text)
        weight_entry = self.builder.get_object('prop_arc_weight_entry')
        if weight_entry and hasattr(self.arc_obj, 'weight'):
            weight_entry.set_text(str(self.arc_obj.weight))
        line_width_spin = self.builder.get_object('prop_arc_line_width_spin')
        if line_width_spin and hasattr(self.arc_obj, 'width'):
            line_width_spin.set_value(float(self.arc_obj.width))
        
        # Set arc type combo
        type_combo = self.builder.get_object('prop_arc_type_combo')
        if type_combo:
            # Determine current arc type
            # 0 = Normal, 1 = Inhibitor, 2 = Test
            if is_inhibitor(self.arc_obj):
                type_combo.set_active(1)  # Inhibitor
            else:
                type_combo.set_active(0)  # Normal
            # TODO: Add Test arc detection when Test arc class is implemented
        
        threshold_textview = self.builder.get_object('prop_arc_threshold_entry')
        if threshold_textview and hasattr(self.arc_obj, 'threshold'):
            buffer = threshold_textview.get_buffer()
            threshold_text = self._format_threshold_for_display(self.arc_obj.threshold)
            buffer.set_text(threshold_text)
        source_info = self.builder.get_object('source_info_label')
        target_info = self.builder.get_object('target_info_label')
        if source_info and hasattr(self.arc_obj, 'source'):
            source_name = getattr(self.arc_obj.source, 'name', 'Unknown')
            source_info.set_text(f'Source: {source_name}')
        if target_info and hasattr(self.arc_obj, 'target'):
            target_name = getattr(self.arc_obj.target, 'name', 'Unknown')
            target_info.set_text(f'Target: {target_name}')

    def _format_threshold_for_display(self, threshold):
        """Format threshold value for display in UI TextView.
        
        Args:
            threshold: Can be None, dict, number, or string
        
        Returns:
            String representation for display
        """
        if threshold is None:
            return ''
        elif isinstance(threshold, dict):
            return json.dumps(threshold, indent=2)
        elif isinstance(threshold, (int, float)):
            return str(threshold)
        else:
            return str(threshold)

    def _parse_threshold(self, text):
        """Parse threshold text from UI into appropriate format.
        
        Supports multiple formats:
            pass
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
        try:
            if '.' in text:
                return float(text)
            else:
                return int(text)
        except ValueError:
            pass
        if text.startswith('{') and text.endswith('}'):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, dict):
                    return parsed
            except (ValueError, SyntaxError) as e:
                pass
        return text

    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            self.emit('properties-changed')
        # Don't destroy here - let explicit destroy() method handle it

    def _apply_changes(self):
        """Apply changes from dialog fields to Arc object.
        
        Note: Arc type changes require transformation which creates a new arc object.
        The caller should check if the arc object reference changed and update accordingly.
        """
        # Check if arc type needs to change
        type_combo = self.builder.get_object('prop_arc_type_combo')
        if type_combo:
            new_type_index = type_combo.get_active()
            # 0 = Normal, 1 = Inhibitor, 2 = Test
            current_is_inhibitor = is_inhibitor(self.arc_obj)
            
            if new_type_index == 0 and current_is_inhibitor:
                # Convert from Inhibitor to Normal
                self.arc_obj = convert_to_normal(self.arc_obj)
                self._replace_arc_in_model()
            elif new_type_index == 1 and not current_is_inhibitor:
                # Convert from Normal to Inhibitor
                try:
                    self.arc_obj = convert_to_inhibitor(self.arc_obj)
                    self._replace_arc_in_model()
                except ValueError as e:
                    # Show error dialog if conversion invalid (e.g., Transition → Place)
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self.dialog,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Cannot convert to Inhibitor Arc"
                    )
                    error_dialog.format_secondary_text(str(e))
                    error_dialog.run()
                    error_dialog.destroy()
                    return  # Don't apply other changes
            # TODO: Add Test arc conversion when Test arc class is implemented
        
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.arc_obj, 'label'):
            buffer = description_text.get_buffer()
            start, end = buffer.get_bounds()
            label_text = buffer.get_text(start, end, True).strip()
            self.arc_obj.label = label_text if label_text else None
        weight_entry = self.builder.get_object('prop_arc_weight_entry')
        if weight_entry and hasattr(self.arc_obj, 'weight'):
            try:
                weight_text = weight_entry.get_text().strip()
                weight_value = int(weight_text) if weight_text else 1
                old_weight = self.arc_obj.weight
                self.arc_obj.weight = max(1, weight_value)
            except ValueError:
                pass
        line_width_spin = self.builder.get_object('prop_arc_line_width_spin')
        if line_width_spin and hasattr(self.arc_obj, 'width'):
            old_width = self.arc_obj.width
            self.arc_obj.width = float(line_width_spin.get_value())
        if self.color_picker and hasattr(self.arc_obj, 'color'):
            old_color = self.arc_obj.color
            selected_color = self.color_picker.get_selected_color()
            self.arc_obj.color = selected_color
        threshold_textview = self.builder.get_object('prop_arc_threshold_entry')
        if threshold_textview and hasattr(self.arc_obj, 'threshold'):
            buffer = threshold_textview.get_buffer()
            start, end = buffer.get_bounds()
            threshold_text = buffer.get_text(start, end, True).strip()
            old_threshold = self.arc_obj.threshold
            self.arc_obj.threshold = self._parse_threshold(threshold_text)

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
    
    def _setup_topology_tab(self):
        """Setup topology information tab using ArcTopologyTabLoader.
        
        Loads the topology tab from XML and populates it with analysis
        for this arc (if model is available).
        """
        # Skip if no model available
        if not self.model:
            return
        
        try:
            from shypn.ui.topology_tab_loader import ArcTopologyTabLoader
            
            # Create topology tab loader
            self.topology_loader = ArcTopologyTabLoader(
                model=self.model,
                element_id=self.arc_obj.id
            )
            
            # Populate with analysis
            self.topology_loader.populate()
            
            # Get the topology widget
            topology_widget = self.topology_loader.get_root_widget()
            
            # Get the topology tab container and add the widget
            container = self.builder.get_object('topology_tab_container')
            if container and topology_widget:
                container.pack_start(topology_widget, True, True, 0)
                topology_widget.show_all()
        
        except ImportError as e:
            # Topology module not available - silently skip
            print(f"Topology tab not available: {e}")
        except Exception as e:
            # Any other error - log but don't crash the dialog
            print(f"Error setting up topology tab: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def destroy(self):
        """Destroy dialog and clean up all widget references.
        
        This ensures proper cleanup to prevent orphaned widgets that can
        cause Wayland focus issues and application crashes.
        """
        # Clean up topology loader first
        if self.topology_loader:
            self.topology_loader.destroy()
            self.topology_loader = None
        
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        
        # Clean up widget references to prevent memory leaks
        self.color_picker = None
        self.builder = None
        self.arc_obj = None
        self.parent_window = None
        self.persistency_manager = None

def create_arc_prop_dialog(arc_obj, parent_window=None, ui_dir: str=None, persistency_manager=None, model=None):
    """Factory function to create an Arc properties dialog loader.
    
    Args:
        arc_obj: Arc object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
        model: PetriNetModel instance for topology analysis (optional)
    
    Returns:
        ArcPropDialogLoader: Configured dialog loader instance.
    """
    return ArcPropDialogLoader(arc_obj, parent_window=parent_window, ui_dir=ui_dir, 
                               persistency_manager=persistency_manager, model=model)