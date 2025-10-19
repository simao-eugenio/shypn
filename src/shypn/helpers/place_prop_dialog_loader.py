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
    __gsignals__ = {'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, place_obj, parent_window=None, ui_dir: str=None, persistency_manager=None, model=None):
        """Initialize the Place properties dialog loader.
        
        Args:
            place_obj: Place object to edit properties for.
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
        self.ui_path = os.path.join(ui_dir, 'place_prop_dialog.ui')
        self.place_obj = place_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        self.model = model
        self.builder = None
        self.dialog = None
        self.color_picker = None
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._setup_topology_tab()

    def _load_ui(self):
        """Load the Place properties dialog UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Place properties dialog UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('place_properties_dialog')
        if self.dialog is None:
            raise ValueError("Object 'place_properties_dialog' not found in place_prop_dialog.ui")
        if self.parent_window:
            self.dialog.set_transient_for(self.parent_window)
        self.dialog.connect('response', self._on_response)

    def _setup_color_picker(self):
        """Setup and insert the color picker widget into the dialog."""
        current_color = getattr(self.place_obj, 'border_color', (0.0, 0.0, 0.0))
        self.color_picker = setup_color_picker_in_dialog(self.builder, 'place_color_picker', current_color=current_color, button_size=28)
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)

    def _on_color_selected(self, picker, color_rgb):
        """Handle color selection from picker.
        
        Args:
            picker: ColorPickerRow widget
            color_rgb: Selected RGB tuple (0.0-1.0)
        """
        r, g, b = color_rgb

    def _populate_fields(self):
        """Populate dialog fields with current Place properties."""
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.place_obj, 'name'):
            name_entry.set_text(str(self.place_obj.name))
            name_entry.set_editable(False)
            name_entry.set_can_focus(False)
        tokens_entry = self.builder.get_object('prop_place_tokens_entry')
        if tokens_entry and hasattr(self.place_obj, 'tokens'):
            tokens_entry.set_text(str(self.place_obj.tokens))
        radius_entry = self.builder.get_object('prop_place_radius_entry')
        if radius_entry and hasattr(self.place_obj, 'radius'):
            radius_entry.set_text(str(self.place_obj.radius))
        capacity_entry = self.builder.get_object('prop_place_capacity_entry')
        if capacity_entry and hasattr(self.place_obj, 'capacity'):
            capacity_value = self.place_obj.capacity
            if capacity_value == float('inf'):
                capacity_entry.set_text('inf')
            else:
                capacity_entry.set_text(str(int(capacity_value)))
        width_entry = self.builder.get_object('prop_place_width_entry')
        if width_entry and hasattr(self.place_obj, 'border_width'):
            width_entry.set_text(str(self.place_obj.border_width))
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
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            self.emit('properties-changed')
        # Don't destroy here - let explicit destroy() method handle it

    def _apply_changes(self):
        """Apply changes from dialog fields to Place object."""
        tokens_entry = self.builder.get_object('prop_place_tokens_entry')
        if tokens_entry and hasattr(self.place_obj, 'tokens'):
            try:
                tokens_text = tokens_entry.get_text().strip()
                if tokens_text:
                    if '.' in tokens_text:
                        tokens_value = float(tokens_text)
                    else:
                        tokens_value = int(tokens_text)
                    self.place_obj.tokens = max(0, tokens_value)
                    self.place_obj.initial_marking = self.place_obj.tokens
            except ValueError as e:
                pass
        radius_entry = self.builder.get_object('prop_place_radius_entry')
        if radius_entry and hasattr(self.place_obj, 'radius'):
            try:
                radius_text = radius_entry.get_text().strip()
                if radius_text:
                    radius_value = float(radius_text)
                    self.place_obj.radius = max(1.0, radius_value)
            except ValueError as e:
                pass
        capacity_entry = self.builder.get_object('prop_place_capacity_entry')
        if capacity_entry and hasattr(self.place_obj, 'capacity'):
            try:
                capacity_text = capacity_entry.get_text().strip().lower()
                if capacity_text:
                    if capacity_text == 'inf' or capacity_text == 'infinity':
                        self.place_obj.capacity = float('inf')
                    else:
                        capacity_value = int(capacity_text)
                        self.place_obj.capacity = max(1, capacity_value)
            except ValueError as e:
                pass
        width_entry = self.builder.get_object('prop_place_width_entry')
        if width_entry and hasattr(self.place_obj, 'border_width'):
            try:
                width_text = width_entry.get_text().strip()
                if width_text:
                    width_value = float(width_text)
                    self.place_obj.border_width = max(0.5, width_value)
            except ValueError as e:
                pass
        if self.color_picker and hasattr(self.place_obj, 'border_color'):
            selected_color = self.color_picker.get_selected_color()
            self.place_obj.border_color = selected_color
            r, g, b = selected_color
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.place_obj, 'label'):
            buffer = description_text.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            new_description = buffer.get_text(start_iter, end_iter, True).strip()
            self.place_obj.label = new_description if new_description else None

    def _setup_topology_tab(self):
        """Setup topology information tab.
        
        Populates the topology tab with cycle and P-invariant information
        for this place (if model is available).
        """
        # Skip if no model available
        if not self.model:
            return
        
        try:
            from shypn.topology.graph import CycleAnalyzer
            from shypn.topology.structural import PInvariantAnalyzer
            
            # Get topology labels
            cycles_label = self.builder.get_object('topology_cycles_label')
            p_inv_label = self.builder.get_object('topology_p_invariants_label')
            
            # Analyze cycles
            if cycles_label:
                try:
                    cycle_analyzer = CycleAnalyzer(self.model)
                    place_cycles = cycle_analyzer.find_cycles_containing_node(self.place_obj.id)
                    
                    if place_cycles:
                        text = f"Part of {len(place_cycles)} cycle(s):\n\n"
                        for i, cycle in enumerate(place_cycles[:5], 1):
                            names = ' → '.join(cycle['names'][:10])
                            if len(cycle['names']) > 10:
                                names += ' ...'
                            text += f"{i}. {names}\n"
                            text += f"   Length: {cycle['length']}, Type: {cycle['type']}\n\n"
                        if len(place_cycles) > 5:
                            text += f"... and {len(place_cycles) - 5} more cycle(s)\n"
                        cycles_label.set_text(text.strip())
                    else:
                        cycles_label.set_text("Not part of any cycles")
                except Exception as e:
                    cycles_label.set_text(f"Analysis error: {str(e)}")
            
            # Analyze P-invariants
            if p_inv_label:
                try:
                    p_inv_analyzer = PInvariantAnalyzer(self.model)
                    place_invariants = p_inv_analyzer.find_invariants_containing_place(self.place_obj.id)
                    
                    if place_invariants:
                        text = f"In {len(place_invariants)} P-invariant(s):\n\n"
                        for i, inv in enumerate(place_invariants[:5], 1):
                            text += f"{i}. {inv['sum_expression']}\n"
                            text += f"   Conserved value: {inv['conserved_value']}\n\n"
                        if len(place_invariants) > 5:
                            text += f"... and {len(place_invariants) - 5} more invariant(s)\n"
                        p_inv_label.set_text(text.strip())
                    else:
                        p_inv_label.set_text("Not in any P-invariants")
                except Exception as e:
                    p_inv_label.set_text(f"Analysis error: {str(e)}")
        
        except ImportError:
            # Topology module not available - silently skip
            pass

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
    
    def destroy(self):
        """Destroy dialog and clean up all widget references.
        
        This ensures proper cleanup to prevent orphaned widgets that can
        cause Wayland focus issues and application crashes.
        """
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        
        # Clean up widget references to prevent memory leaks
        self.color_picker = None
        self.builder = None
        self.place_obj = None
        self.parent_window = None
        self.persistency_manager = None

def create_place_prop_dialog(place_obj, parent_window=None, ui_dir: str=None, persistency_manager=None, model=None):
    """Factory function to create a Place properties dialog loader.
    
    Args:
        place_obj: Place object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
        model: PetriNetModel instance for topology analysis (optional)
    
    Returns:
        PlacePropDialogLoader: Configured dialog loader instance.
    """
    return PlacePropDialogLoader(place_obj, parent_window=parent_window, ui_dir=ui_dir, 
                                  persistency_manager=persistency_manager, model=model)