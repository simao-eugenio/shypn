"""
Place Properties Dialog Loader

Loads and manages the Place properties dialog UI.
"""
import os
import logging
logger = logging.getLogger(__name__)
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
        self.topology_loader = None
        self._load_ui()
        self._setup_color_picker()
        self._setup_signal_handlers()
        self._populate_fields()
        self._populate_spatial_properties()
        self._setup_topology_tab()

    def _load_ui(self):
        """Load the Place properties dialog UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Place properties dialog UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('place_properties_dialog')
        if self.dialog is None:
            raise ValueError("Object 'place_properties_dialog' not found in place_prop_dialog.ui")
        
        # WAYLAND FIX: Do NOT set transient_for here!
        # On Wayland, parent must be realized/mapped before set_transient_for()
        # We'll set it in run() when parent is guaranteed to be ready
        
        self.dialog.connect('response', self._on_response)

    def _setup_color_picker(self):
        """Setup and insert the color picker widget into the dialog."""
        current_color = getattr(self.place_obj, 'border_color', (0.0, 0.0, 0.0))
        self.color_picker = setup_color_picker_in_dialog(self.builder, 'place_color_picker', current_color=current_color, button_size=28)
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
    
    def _setup_signal_handlers(self):
        """Setup signal place checkbox and combo handlers."""
        signal_checkbox = self.builder.get_object('signal_place_checkbox')
        if signal_checkbox:
            signal_checkbox.connect('toggled', self._on_signal_checkbox_toggled)

    def _on_color_selected(self, picker, color_rgb):
        """Handle color selection from picker.
        
        Args:
            picker: ColorPickerRow widget
            color_rgb: Selected RGB tuple (0.0-1.0)
        """
        r, g, b = color_rgb
    
    def _on_signal_checkbox_toggled(self, checkbox):
        """Handle signal place checkbox toggle.
        
        Args:
            checkbox: The signal place checkbox widget
        """
        is_active = checkbox.get_active()
        signal_type_combo = self.builder.get_object('signal_type_combo')
        if signal_type_combo:
            signal_type_combo.set_sensitive(is_active)

    def _populate_fields(self):
        """Populate dialog fields with current Place properties."""
        # ID (read-only, managed by IDManager)
        id_entry = self.builder.get_object('id_entry')
        if id_entry and hasattr(self.place_obj, 'id'):
            id_entry.set_text(str(self.place_obj.id))
        
        # Name (editable - user-created alias)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.place_obj, 'name'):
            name_entry.set_text(str(self.place_obj.name))
            # Name is editable - user-created alias
        tokens_entry = self.builder.get_object('prop_place_tokens_entry')
        if tokens_entry and hasattr(self.place_obj, 'tokens'):
            tokens_entry.set_text(str(self.place_obj.tokens))
        radius_entry = self.builder.get_object('prop_place_radius_entry')
        if radius_entry and hasattr(self.place_obj, 'radius'):
            radius_entry.set_text(str(self.place_obj.radius))
        capacity_entry = self.builder.get_object('prop_place_capacity_entry')
        if capacity_entry and hasattr(self.place_obj, 'capacity'):
            capacity_value = self.place_obj.capacity
            if capacity_value is None:
                capacity_entry.set_text('')
            elif capacity_value == float('inf'):
                capacity_entry.set_text('inf')
            elif isinstance(capacity_value, str) and capacity_value.lower() in ('infinity', 'inf'):
                capacity_entry.set_text('inf')
            else:
                try:
                    capacity_entry.set_text(str(int(capacity_value)))
                except (ValueError, TypeError):
                    capacity_entry.set_text('inf')
        width_entry = self.builder.get_object('prop_place_width_entry')
        if width_entry and hasattr(self.place_obj, 'border_width'):
            width_entry.set_text(str(self.place_obj.border_width))
        description_text = self.builder.get_object('description_text')
        if description_text and hasattr(self.place_obj, 'label'):
            buffer = description_text.get_buffer()
            buffer.set_text(str(self.place_obj.label) if self.place_obj.label else '')
        
        # Signal place properties
        signal_checkbox = self.builder.get_object('signal_place_checkbox')
        if signal_checkbox:
            is_signal = getattr(self.place_obj, 'is_signal_place', False)
            signal_checkbox.set_active(is_signal)
            
        signal_type_combo = self.builder.get_object('signal_type_combo')
        if signal_type_combo:
            signal_type = getattr(self.place_obj, 'signal_type', None)
            if signal_type:
                # Map signal type to combo box index
                # Handle both SignalType enum and string values
                if isinstance(signal_type, str):
                    type_str = signal_type
                else:
                    # SignalType enum - get value
                    type_str = signal_type.value if hasattr(signal_type, 'value') else str(signal_type)
                
                type_map = {
                    'energy': 0,
                    'regulatory': 1,
                    'quorum': 2,
                    'spatial': 3
                }
                idx = type_map.get(type_str, 0)
                signal_type_combo.set_active(idx)
            else:
                signal_type_combo.set_active(0)  # Default to energy
            
            # Enable/disable based on checkbox
            signal_type_combo.set_sensitive(getattr(self.place_obj, 'is_signal_place', False))

    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            self._save_spatial_properties()  # Save spatial properties
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            self.emit('properties-changed')
        # Don't destroy here - let explicit destroy() method handle it

    def _apply_changes(self):
        """Apply changes from dialog fields to Place object."""
        # Track signal place status BEFORE changes
        was_signal_place = getattr(self.place_obj, 'is_signal_place', False)
        
        # Name (user-editable alias)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.place_obj, 'name'):
            new_name = name_entry.get_text().strip()
            if new_name:  # Only update if non-empty
                self.place_obj.name = new_name
        
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
        
        # Signal place properties
        signal_checkbox = self.builder.get_object('signal_place_checkbox')
        if signal_checkbox:
            is_signal = signal_checkbox.get_active()
            self.place_obj.is_signal_place = is_signal
            
            # If enabling signal place, set signal type
            if is_signal:
                signal_type_combo = self.builder.get_object('signal_type_combo')
                if signal_type_combo:
                    from shypn.netobjs.signal_type import SignalType
                    active_idx = signal_type_combo.get_active()
                    type_map = [SignalType.ENERGY, SignalType.REGULATORY, SignalType.QUORUM, SignalType.SPATIAL]
                    if 0 <= active_idx < len(type_map):
                        self.place_obj.signal_type = type_map[active_idx]
                    else:
                        self.place_obj.signal_type = SignalType.ENERGY  # Default
            else:
                # Clear signal type when unchecked
                self.place_obj.signal_type = None
        
        # AUTOMATIC ARC TRANSFORMATION: When place becomes signal place
        # Convert all connected arcs to signal flow arcs (formalism requirement)
        if not was_signal_place and self.place_obj.is_signal_place:
            self._convert_connected_arcs_to_signal_flow()
    
    def _convert_connected_arcs_to_signal_flow(self):
        """Convert all arcs connected to this place to signal flow arcs.
        
        Called automatically when a place becomes a signal place.
        According to the formalism, signal places require signal flow arcs.
        """
        if not hasattr(self.place_obj, '_manager') or not self.place_obj._manager:
            return  # No manager, can't access arcs
        
        manager = self.place_obj._manager
        from shypn.utils.arc_transform import convert_to_signal_flow
        
        # Find all arcs connected to this place
        connected_arcs = []
        for arc in manager.arcs:
            if arc.source == self.place_obj or arc.target == self.place_obj:
                connected_arcs.append(arc)
        
        # Convert each arc to signal flow
        for old_arc in connected_arcs:
            try:
                new_arc = convert_to_signal_flow(old_arc)
                # Only replace if conversion created a different arc
                if new_arc is not old_arc:
                    manager.replace_arc(old_arc, new_arc)
            except ValueError:
                # Conversion failed (e.g., arc doesn't connect to signal place)
                # This shouldn't happen since we're converting arcs connected to a signal place
                pass

    def _setup_topology_tab(self):
        """Setup topology information tab using PlaceTopologyTabLoader.
        
        Loads the topology tab from XML and populates it with analysis
        for this place (if model is available).
        """
        # Skip if no model available
        if not self.model:
            return
        
        try:
            from shypn.ui.topology_tab_loader import PlaceTopologyTabLoader
            
            # Create topology tab loader
            self.topology_loader = PlaceTopologyTabLoader(
                model=self.model,
                element_id=self.place_obj.id
            )
            
            # NOTE: Do NOT call populate() here - it can hang on large models!
            # CycleAnalyzer uses nx.simple_cycles() which has exponential complexity.
            # For complex models (e.g., Glycolysis with 60 nodes), this can freeze
            # the application indefinitely.
            # TODO: Implement lazy loading - populate when user switches to Topology tab
            # self.topology_loader.populate()  # ❌ REMOVED - causes freeze
            
            # Get the topology widget
            topology_widget = self.topology_loader.get_root_widget()
            
            # Get the topology tab container and add the widget
            container = self.builder.get_object('topology_tab_container')
            if container and topology_widget:
                container.pack_start(topology_widget, True, True, 0)
                topology_widget.show_all()
                
                # Show "Click to analyze" message in topology tab
                # This lets user know the tab is available but not yet populated
                if hasattr(self.topology_loader, 'cycles_label'):
                    self.topology_loader.cycles_label.set_markup(
                        "<i>Topology analysis available.\n"
                        "Click 'Analyze' button to run analysis.</i>"
                    )
        
        except ImportError as e:
            # Topology module not available - silently skip (debug only)
            logger.debug(f"Topology tab not available: {e}")
        except Exception as e:
            # Log exception with traceback but do not crash dialog
            logger.exception(f"Error setting up topology tab: {type(e).__name__}: {e}")
    
    def _populate_spatial_properties(self):
        """Populate spatial properties fields from place object."""
        # Compartment volume
        volume_entry = self.builder.get_object('compartment_volume_entry')
        if volume_entry and hasattr(self.place_obj, 'compartment_volume'):
            if self.place_obj.compartment_volume is not None:
                volume_entry.set_text(str(self.place_obj.compartment_volume))
        
        # Diffusion coefficient
        diff_entry = self.builder.get_object('diffusion_coefficient_entry')
        if diff_entry and hasattr(self.place_obj, 'diffusion_coefficient'):
            if self.place_obj.diffusion_coefficient is not None:
                diff_entry.set_text(str(self.place_obj.diffusion_coefficient))
        
        # Boundary type
        boundary_combo = self.builder.get_object('boundary_type_combo')
        if boundary_combo and hasattr(self.place_obj, 'boundary_type'):
            from shypn.netobjs.place import BoundaryType
            boundary_map = {
                None: 0,
                BoundaryType.PERMEABLE: 1,
                BoundaryType.SELECTIVE: 2,
                BoundaryType.IMPERMEABLE: 3
            }
            current_index = boundary_map.get(self.place_obj.boundary_type, 0)
            boundary_combo.set_active(current_index)
        
        # Module ID
        module_entry = self.builder.get_object('module_id_entry')
        if module_entry and hasattr(self.place_obj, 'module_id'):
            if self.place_obj.module_id:
                module_entry.set_text(self.place_obj.module_id)
        
        # Gradient vector
        if hasattr(self.place_obj, 'gradient_vector') and self.place_obj.gradient_vector:
            if len(self.place_obj.gradient_vector) >= 3:
                dx, dy, dz = self.place_obj.gradient_vector[:3]
                dx_entry = self.builder.get_object('gradient_vector_dx_entry')
                dy_entry = self.builder.get_object('gradient_vector_dy_entry')
                dz_entry = self.builder.get_object('gradient_vector_dz_entry')
                if dx_entry: dx_entry.set_text(str(dx))
                if dy_entry: dy_entry.set_text(str(dy))
                if dz_entry: dz_entry.set_text(str(dz))
        
        # Spatial position
        if hasattr(self.place_obj, 'spatial_position') and self.place_obj.spatial_position:
            if len(self.place_obj.spatial_position) >= 3:
                x, y, z = self.place_obj.spatial_position[:3]
                x_entry = self.builder.get_object('spatial_position_x_entry')
                y_entry = self.builder.get_object('spatial_position_y_entry')
                z_entry = self.builder.get_object('spatial_position_z_entry')
                if x_entry: x_entry.set_text(str(x))
                if y_entry: y_entry.set_text(str(y))
                if z_entry: z_entry.set_text(str(z))
        
        # Neighbor compartments
        if hasattr(self.place_obj, 'neighbor_compartments') and self.place_obj.neighbor_compartments:
            textview = self.builder.get_object('neighbor_compartments_textview')
            if textview:
                buffer = textview.get_buffer()
                buffer.set_text('\n'.join(self.place_obj.neighbor_compartments))
    
    def _save_spatial_properties(self):
        """Save spatial properties from UI to place object."""
        # Compartment volume
        volume_entry = self.builder.get_object('compartment_volume_entry')
        if volume_entry:
            text = volume_entry.get_text().strip()
            try:
                self.place_obj.compartment_volume = float(text) if text else None
            except ValueError:
                self.place_obj.compartment_volume = None
        
        # Diffusion coefficient
        diff_entry = self.builder.get_object('diffusion_coefficient_entry')
        if diff_entry:
            text = diff_entry.get_text().strip()
            try:
                self.place_obj.diffusion_coefficient = float(text) if text else None
            except ValueError:
                self.place_obj.diffusion_coefficient = None
        
        # Boundary type
        boundary_combo = self.builder.get_object('boundary_type_combo')
        if boundary_combo:
            from shypn.netobjs.place import BoundaryType
            boundary_list = [None, BoundaryType.PERMEABLE, BoundaryType.SELECTIVE, BoundaryType.IMPERMEABLE]
            selected_index = boundary_combo.get_active()
            selected_value = boundary_list[selected_index]
            self.place_obj.boundary_type = selected_value
        
        # Module ID
        module_entry = self.builder.get_object('module_id_entry')
        if module_entry:
            text = module_entry.get_text().strip()
            self.place_obj.module_id = text if text else None
        
        # Gradient vector
        dx_entry = self.builder.get_object('gradient_vector_dx_entry')
        dy_entry = self.builder.get_object('gradient_vector_dy_entry')
        dz_entry = self.builder.get_object('gradient_vector_dz_entry')
        if dx_entry and dy_entry and dz_entry:
            dx = dx_entry.get_text().strip()
            dy = dy_entry.get_text().strip()
            dz = dz_entry.get_text().strip()
            if dx and dy and dz:
                try:
                    self.place_obj.gradient_vector = [float(dx), float(dy), float(dz)]
                except ValueError:
                    self.place_obj.gradient_vector = None
            else:
                self.place_obj.gradient_vector = None
        
        # Spatial position
        x_entry = self.builder.get_object('spatial_position_x_entry')
        y_entry = self.builder.get_object('spatial_position_y_entry')
        z_entry = self.builder.get_object('spatial_position_z_entry')
        if x_entry and y_entry and z_entry:
            x = x_entry.get_text().strip()
            y = y_entry.get_text().strip()
            z = z_entry.get_text().strip()
            if x and y and z:
                try:
                    self.place_obj.spatial_position = [float(x), float(y), float(z)]
                except ValueError:
                    self.place_obj.spatial_position = None
            else:
                self.place_obj.spatial_position = None
        
        # Neighbor compartments
        textview = self.builder.get_object('neighbor_compartments_textview')
        if textview:
            buffer = textview.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            if text.strip():
                # Split by newlines and filter empty lines
                neighbors = [line.strip() for line in text.split('\n') if line.strip()]
                self.place_obj.neighbor_compartments = neighbors if neighbors else []
            else:
                self.place_obj.neighbor_compartments = []

    def run(self):
        """Show the dialog and run it modally.
        
        Returns:
            Response ID from the dialog.
        """
        # WAYLAND FIX: Set transient_for HERE, not in __init__!
        # On Wayland, parent must be realized/mapped before set_transient_for()
        # At run() time, parent is guaranteed to be ready
        if self.parent_window:
            # CRITICAL WAYLAND CHECK: Ensure parent is MAPPED before setting transient
            parent_mapped = self.parent_window.get_mapped()
            parent_realized = self.parent_window.get_realized()
            
            logger.debug(f"[DIALOG WAYLAND] Parent window mapped: {parent_mapped}, realized: {parent_realized}")
            
            if not parent_mapped:
                logger.warning("[DIALOG WAYLAND] Parent window not mapped; may trigger protocol warnings")
            
            # CRITICAL WAYLAND FIX: Check window state (maximized, fullscreen, etc.)
            # Error 71 occurs when dialogs are opened while window is in transition
            import gi
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk
            
            window = self.parent_window.get_window()
            if window:
                state = window.get_state()
                is_maximized = bool(state & Gdk.WindowState.MAXIMIZED)
                is_fullscreen = bool(state & Gdk.WindowState.FULLSCREEN)
                is_tiled = bool(state & Gdk.WindowState.TILED)
                
                logger.debug(f"[DIALOG WAYLAND] Window state: maximized={is_maximized}, fullscreen={is_fullscreen}, tiled={is_tiled}")
                
                # WAYLAND WORKAROUND: If window is maximized/fullscreen/tiled, wait a bit
                # This gives Wayland compositor time to complete the state transition
                if is_maximized or is_fullscreen or is_tiled:
                    logger.debug("[DIALOG WAYLAND] Window in special state; delaying transient assignment 100ms")
                    from gi.repository import GLib
                    import time
                    time.sleep(0.1)  # 100ms delay to let compositor settle
            
            # CRITICAL WAYLAND FIX: Process pending events before set_transient_for()
            # This ensures the Wayland compositor has processed all widget state changes
            display = Gdk.Display.get_default()
            if display:
                display.sync()  # Wait for all requests to be processed
                logger.debug("[DIALOG WAYLAND] Display sync completed")
            
            # Now set transient after compositor is synced
            self.dialog.set_transient_for(self.parent_window)
            logger.debug("[DIALOG WAYLAND] set_transient_for completed")
        
        # WAYLAND FIX: Explicitly show dialog before run() to prevent protocol errors
        # Critical for imported canvases where widget hierarchy is established asynchronously
        # Default canvas works because it's realized when main window shows
        # Imported canvases are created programmatically and dialogs may open before fully ready
        self.dialog.show()
        logger.debug("[DIALOG WAYLAND] dialog.show() completed; entering run() loop")
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