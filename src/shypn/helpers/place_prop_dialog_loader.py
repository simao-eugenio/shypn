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
from typing import Dict, Any
from shypn.helpers.color_picker import setup_color_picker_in_dialog
from shypn.thermodynamics.compound_mapper import CompoundMapper

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
            model: PetriNetModel instance (optional, for future use)
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
        self._setup_signal_handlers()
        self._setup_thermodynamic_handlers()
        self._populate_fields()
        self._populate_spatial_properties()
        self._populate_thermodynamic_properties()
        self._populate_parameter_properties()

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
            # Show initial_marking (design-time baseline), not post-simulation tokens
            initial_val = getattr(self.place_obj, 'initial_marking', self.place_obj.tokens)
            tokens_entry.set_text(str(initial_val))
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
            self._save_thermodynamic_properties()  # Save thermodynamic properties
            self._save_parameter_properties()  # Save parameter-place properties
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
                    new_tokens = max(0, tokens_value)
                    # Update both the design-time baseline and the runtime value.
                    # The dialog always shows initial_marking (set in _populate_fields),
                    # so whatever the user types here IS the new initial marking.
                    self.place_obj.initial_marking = new_tokens
                    self.place_obj.tokens = new_tokens
            except ValueError as e:
                self.logger.debug(f"Invalid tokens value: {e}")
                pass
        radius_entry = self.builder.get_object('prop_place_radius_entry')
        if radius_entry and hasattr(self.place_obj, 'radius'):
            try:
                radius_text = radius_entry.get_text().strip()
                if radius_text:
                    radius_value = float(radius_text)
                    self.place_obj.radius = max(1.0, radius_value)
            except ValueError as e:
                self.logger.debug(f"Invalid radius value: {e}")
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
                self.logger.debug(f"Invalid capacity value: {e}")
                pass
        width_entry = self.builder.get_object('prop_place_width_entry')
        if width_entry and hasattr(self.place_obj, 'border_width'):
            try:
                width_text = width_entry.get_text().strip()
                if width_text:
                    width_value = float(width_text)
                    self.place_obj.border_width = max(0.5, width_value)
            except ValueError as e:
                self.logger.debug(f"Invalid border width value: {e}")
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
                # Apply signal place visual schema: hexagon + blue border
                self.place_obj.shape = 'hexagon'
            else:
                # Clear signal type and restore default circle shape
                self.place_obj.signal_type = None
                self.place_obj.shape = 'circle'

            # Always sync border color via ColorSchemaManager so the visual
            # immediately reflects the new is_signal_place state
            from shypn.utils.color_schema_manager import ColorSchemaManager
            ColorSchemaManager.reset_place_color(self.place_obj)

            # Trigger redraw so the place border color updates immediately
            if hasattr(self.place_obj, '_manager') and self.place_obj._manager:
                self.place_obj._manager.mark_needs_redraw()

        # AUTOMATIC ARC TRANSFORMATION: When place becomes signal place
        # Convert all connected arcs to signal flow arcs (formalism requirement)
        if not was_signal_place and self.place_obj.is_signal_place:
            self._convert_connected_arcs_to_signal_flow()

        # Notify listeners that this place was modified (e.g. EnvironmentPanel)
        try:
            from shypn.events import EventBus
            from shypn.core.document_id import doc_id
            drawing_area = None
            if hasattr(self.place_obj, '_manager') and self.place_obj._manager:
                drawing_area = getattr(self.place_obj._manager, '_drawing_area', None)
            if drawing_area is not None:
                EventBus.emit('model.place.modified',
                              {'object': self.place_obj, 'object_id': self.place_obj.id},
                              document_id=doc_id(drawing_area))
        except Exception:
            pass

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
        converted = False
        for old_arc in connected_arcs:
            try:
                new_arc = convert_to_signal_flow(old_arc)
                # Only replace if conversion created a different arc
                if new_arc is not old_arc:
                    manager.replace_arc(old_arc, new_arc)
                    converted = True
            except ValueError:
                # Conversion failed — skip silently
                pass

        # Trigger visual redraw so the new arc colors are shown immediately
        if converted:
            manager.mark_needs_redraw()

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
        
        # Module/Compartment ID (prioritize compartment attribute)
        module_entry = self.builder.get_object('module_id_entry')
        if module_entry:
            display_value = ''
            # Check compartment first (preferred), then module_id (fallback)
            if hasattr(self.place_obj, 'compartment') and self.place_obj.compartment:
                display_value = self.place_obj.compartment
            elif hasattr(self.place_obj, 'module_id') and self.place_obj.module_id:
                display_value = self.place_obj.module_id
            if display_value:
                module_entry.set_text(display_value)
        
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
        
        # Module/Compartment ID (save to compartment attribute)
        module_entry = self.builder.get_object('module_id_entry')
        if module_entry:
            text = module_entry.get_text().strip()
            if text:
                # Save to compartment attribute (primary location)
                self.place_obj.compartment = text
            else:
                # Clear compartment if empty
                self.place_obj.compartment = None
        
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

    # ------------------------------------------------------------------
    # Parameter-place tab (exogenous experimental constants)
    # ------------------------------------------------------------------
    def _populate_parameter_properties(self):
        """Populate the Parameter tab from the place object."""
        checkbox = self.builder.get_object('parameter_place_checkbox')
        if checkbox is not None:
            checkbox.set_active(bool(getattr(self.place_obj, 'is_parameter_place', False)))

        kind_combo = self.builder.get_object('parameter_kind_combo')
        if kind_combo is not None:
            kind = getattr(self.place_obj, 'parameter_kind', None) or ''
            entry = kind_combo.get_child()
            if entry is not None and hasattr(entry, 'set_text'):
                entry.set_text(str(kind))

        units_entry = self.builder.get_object('parameter_units_entry')
        if units_entry is not None:
            units = getattr(self.place_obj, 'parameter_units', None) or ''
            units_entry.set_text(str(units))

    def _save_parameter_properties(self):
        """Save the Parameter tab to the place object."""
        checkbox = self.builder.get_object('parameter_place_checkbox')
        if checkbox is not None:
            self.place_obj.is_parameter_place = bool(checkbox.get_active())

        kind_combo = self.builder.get_object('parameter_kind_combo')
        if kind_combo is not None:
            entry = kind_combo.get_child()
            text = entry.get_text().strip() if entry is not None and hasattr(entry, 'get_text') else ''
            self.place_obj.parameter_kind = text or None

        units_entry = self.builder.get_object('parameter_units_entry')
        if units_entry is not None:
            text = units_entry.get_text().strip()
            self.place_obj.parameter_units = text or None

        # Refresh border colour to reflect the new flag state.
        try:
            from shypn.utils.color_schema_manager import ColorSchemaManager
            ColorSchemaManager.reset_place_color(self.place_obj)
            if hasattr(self.place_obj, '_manager') and self.place_obj._manager:
                self.place_obj._manager.mark_needs_redraw()
        except Exception as e:
            logger.debug(f"Could not refresh place colour after parameter edit: {e}")

    def _setup_thermodynamic_handlers(self):
        """Setup thermodynamic tab button handlers."""
        # Fetch from Database button
        fetch_button = self.builder.get_object('thermo_fetch_button')
        if fetch_button:
            fetch_button.connect('clicked', self._on_fetch_thermodynamic_clicked)
        
        # Clear All button
        clear_button = self.builder.get_object('thermo_clear_button')
        if clear_button:
            clear_button.connect('clicked', self._on_clear_thermodynamic_clicked)
        
        # Search by Name button
        search_button = self.builder.get_object('thermo_search_button')
        if search_button:
            search_button.connect('clicked', self._on_search_by_name_clicked)
        
        # Import CSV button
        import_csv_button = self.builder.get_object('thermo_import_csv_button')
        if import_csv_button:
            import_csv_button.connect('clicked', self._on_import_csv_clicked)
        
        # Export CSV button
        export_csv_button = self.builder.get_object('thermo_export_csv_button')
        if export_csv_button:
            export_csv_button.connect('clicked', self._on_export_csv_clicked)
        
        # Bidirectional compound ID ↔ name suggestion
        # When compound_id changes, suggest place name
        compound_entry = self.builder.get_object('thermo_compound_id_entry')
        if compound_entry:
            compound_entry.connect('changed', self._on_compound_id_changed)
        
        # When place name changes, suggest compound_id
        name_entry = self.builder.get_object('name_entry')
        if name_entry:
            # Only connect if not already connected (avoid duplicate handlers)
            if not hasattr(self, '_name_handler_connected'):
                name_entry.connect('changed', self._on_place_name_changed)
                self._name_handler_connected = True
    
    def _populate_thermodynamic_properties(self):
        """Populate thermodynamic properties from place.properties['thermodynamics']."""
        thermo_data = self.place_obj.properties.get('thermodynamics', {})
        
        if not thermo_data:
            # No thermodynamic data, leave fields empty
            return
        
        # Compound ID
        compound_entry = self.builder.get_object('thermo_compound_id_entry')
        if compound_entry and 'compound_id' in thermo_data:
            compound_entry.set_text(str(thermo_data['compound_id']))
        
        # Compound Name (read-only label)
        compound_name_label = self.builder.get_object('thermo_compound_name_label')
        if compound_name_label and 'compound_name' in thermo_data:
            compound_name_label.set_text(str(thermo_data['compound_name']))
        
        # ΔGf° (Delta G formation)
        dg_entry = self.builder.get_object('thermo_delta_g_entry')
        if dg_entry and 'delta_g_formation' in thermo_data:
            dg_value = thermo_data['delta_g_formation']
            if dg_value is not None:
                dg_entry.set_text(f"{dg_value:.2f}")
        
        # Charge
        charge_spin = self.builder.get_object('thermo_charge_spin')
        if charge_spin and 'charge' in thermo_data:
            charge_value = thermo_data.get('charge', 0)
            charge_spin.set_value(float(charge_value))
        
        # #Protons
        n_protons_spin = self.builder.get_object('thermo_n_protons_spin')
        if n_protons_spin and 'n_protons' in thermo_data:
            n_protons_value = thermo_data.get('n_protons', 0)
            n_protons_spin.set_value(float(n_protons_value))
        
        # pKa values (comma-separated)
        pka_entry = self.builder.get_object('thermo_pka_entry')
        if pka_entry and 'pKa_values' in thermo_data:
            pka_list = thermo_data['pKa_values']
            if pka_list and isinstance(pka_list, list):
                pka_text = ', '.join(str(x) for x in pka_list)
                pka_entry.set_text(pka_text)
        
        # Data source
        source_combo = self.builder.get_object('thermo_source_combo')
        if source_combo and 'source' in thermo_data:
            source_value = thermo_data['source'].lower()
            source_map = {
                'none': 0,
                'manual': 1,
                'manual entry': 1,
                'equilibrator': 2,
                'brenda': 3
            }
            index = source_map.get(source_value, 0)
            source_combo.set_active(index)
        
        # Conditions: pH, temperature, ionic strength
        conditions = thermo_data.get('conditions', {})
        
        # pH
        ph_spin = self.builder.get_object('thermo_ph_spin')
        if ph_spin:
            ph_value = conditions.get('pH', 7.0)
            ph_spin.set_value(float(ph_value))
        
        # Temperature
        temp_spin = self.builder.get_object('thermo_temperature_spin')
        if temp_spin:
            temp_value = conditions.get('temperature', 298.15)
            temp_spin.set_value(float(temp_value))
        
        # Ionic Strength
        ionic_spin = self.builder.get_object('thermo_ionic_strength_spin')
        if ionic_spin:
            ionic_value = conditions.get('ionic_strength', 0.1)
            ionic_spin.set_value(float(ionic_value))
    
    def _save_thermodynamic_properties(self):
        """Save thermodynamic properties from UI to place.properties['thermodynamics']."""
        thermo_data = {}
        
        # Compound ID
        compound_entry = self.builder.get_object('thermo_compound_id_entry')
        if compound_entry:
            compound_id = compound_entry.get_text().strip()
            if compound_id:
                thermo_data['compound_id'] = compound_id
        
        # Compound Name (from label, preserves fetched name)
        compound_name_label = self.builder.get_object('thermo_compound_name_label')
        if compound_name_label:
            compound_name = compound_name_label.get_text().strip()
            if compound_name and compound_name != '-':
                thermo_data['compound_name'] = compound_name
        
        # ΔGf°
        dg_entry = self.builder.get_object('thermo_delta_g_entry')
        if dg_entry:
            dg_text = dg_entry.get_text().strip()
            if dg_text:
                try:
                    thermo_data['delta_g_formation'] = float(dg_text)
                except ValueError:
                    logger.warning(f"Invalid ΔGf° value: {dg_text}")
        
        # Charge
        charge_spin = self.builder.get_object('thermo_charge_spin')
        if charge_spin:
            thermo_data['charge'] = int(charge_spin.get_value())
        
        # #Protons
        n_protons_spin = self.builder.get_object('thermo_n_protons_spin')
        if n_protons_spin:
            thermo_data['n_protons'] = int(n_protons_spin.get_value())
        
        # pKa values (parse comma-separated)
        pka_entry = self.builder.get_object('thermo_pka_entry')
        if pka_entry:
            pka_text = pka_entry.get_text().strip()
            if pka_text:
                try:
                    # Parse comma-separated pKa values
                    pka_values = [float(x.strip()) for x in pka_text.split(',') if x.strip()]
                    if pka_values:
                        thermo_data['pKa_values'] = pka_values
                except ValueError:
                    logger.warning(f"Invalid pKa values: {pka_text}")
        
        # Data source
        source_combo = self.builder.get_object('thermo_source_combo')
        if source_combo:
            active_id = source_combo.get_active_id()
            if active_id and active_id != 'none':
                thermo_data['source'] = active_id
        
        # Conditions: pH, temperature, ionic strength
        conditions = {}
        
        # pH
        ph_spin = self.builder.get_object('thermo_ph_spin')
        if ph_spin:
            conditions['pH'] = ph_spin.get_value()
        
        # Temperature
        temp_spin = self.builder.get_object('thermo_temperature_spin')
        if temp_spin:
            conditions['temperature'] = temp_spin.get_value()
        
        # Ionic Strength
        ionic_spin = self.builder.get_object('thermo_ionic_strength_spin')
        if ionic_spin:
            conditions['ionic_strength'] = ionic_spin.get_value()
        
        if conditions:
            thermo_data['conditions'] = conditions
        
        # Save to place.properties (only if there's data)
        if thermo_data:
            self.place_obj.properties['thermodynamics'] = thermo_data
        elif 'thermodynamics' in self.place_obj.properties:
            # Clear if all fields empty
            del self.place_obj.properties['thermodynamics']
    
    def _on_fetch_thermodynamic_clicked(self, button):
        """Handle 'Fetch from Database' button click.
        
        Lookup strategy:
        1. Check local SQLite cache (fast, offline)
        2. If not found, suggest fetching from remote API
        3. Cache remote results for future use
        """
        compound_entry = self.builder.get_object('thermo_compound_id_entry')
        if not compound_entry:
            return
        
        compound_id = compound_entry.get_text().strip().upper()
        if not compound_id:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Compound ID Required"
            )
            error_dialog.format_secondary_text(
                "Please enter a compound ID (e.g., C00002, CHEBI:15422) before fetching data."
            )
            error_dialog.run()
            error_dialog.destroy()
            return
        
        # Get pH, temperature, ionic strength from spinners
        ph = 7.0
        temperature = 298.15
        ionic_strength = 0.1
        
        ph_spin = self.builder.get_object('thermo_ph_spin')
        if ph_spin:
            ph = ph_spin.get_value()
        
        temp_spin = self.builder.get_object('thermo_temperature_spin')
        if temp_spin:
            temperature = temp_spin.get_value()
        
        ionic_spin = self.builder.get_object('thermo_ionic_strength_spin')
        if ionic_spin:
            ionic_strength = ionic_spin.get_value()
        
        # Show spinner and disable button
        spinner = self.builder.get_object('thermo_fetch_spinner')
        if spinner:
            spinner.set_visible(True)
            spinner.start()
        button.set_sensitive(False)
        
        try:
            # Import database module
            from shypn.thermodynamics.compound_database import CompoundDatabase
            
            # Create database instance
            db = CompoundDatabase()
            
            # Determine source (default to eQuilibrator)
            source_combo = self.builder.get_object('thermo_source_combo')
            source = 'equilibrator'  # Default
            if source_combo:
                active_id = source_combo.get_active_id()
                if active_id in ['equilibrator', 'brenda']:
                    source = active_id
            
            # STEP 1: Check local SQLite cache first
            data = db.get_compound(compound_id)
            
            if data:
                # Found in local cache - populate immediately
                self._populate_fetched_data(data, from_cache=True)
                
                # Show success message
                success_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Data Retrieved from Cache"
                )
                success_dialog.format_secondary_text(
                    f"Thermodynamic data for {data.get('compound_name', compound_id)} "
                    f"retrieved from local cache.\n\n"
                    f"Source: {data.get('source', 'unknown')}\n"
                    f"Cached: {data.get('fetch_date', 'unknown')}"
                )
                success_dialog.run()
                success_dialog.destroy()
            
            else:
                # STEP 2: Not in cache - suggest fetching from remote
                fetch_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    flags=0,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Compound Not Found in Local Database"
                )
                fetch_dialog.format_secondary_text(
                    f"Compound '{compound_id}' not found in local cache.\n\n"
                    f"Would you like to fetch data from {source.title()} API?\n\n"
                    f"Note: This requires internet connection and may take a few seconds.\n"
                    f"Retrieved data will be cached locally for future use."
                )
                response = fetch_dialog.run()
                fetch_dialog.destroy()
                
                if response == Gtk.ResponseType.YES:
                    # STEP 3: Fetch from remote API with conditions
                    try:
                        data = db.fetch_remote(compound_id, source=source)
                        
                        if data:
                            # Cache the results
                            db.cache_compound(data)
                            
                            # Populate fields
                            self._populate_fetched_data(data, from_cache=False)
                            
                            # Show success message
                            success_dialog = Gtk.MessageDialog(
                                transient_for=self.dialog,
                                flags=0,
                                message_type=Gtk.MessageType.INFO,
                                buttons=Gtk.ButtonsType.OK,
                                text="Data Fetched Successfully"
                            )
                            success_dialog.format_secondary_text(
                                f"Thermodynamic data for {data.get('compound_name', compound_id)} "
                                f"retrieved from {source.title()} and cached locally."
                            )
                            success_dialog.run()
                            success_dialog.destroy()
                        else:
                            # Remote fetch returned nothing
                            error_dialog = Gtk.MessageDialog(
                                transient_for=self.dialog,
                                flags=0,
                                message_type=Gtk.MessageType.WARNING,
                                buttons=Gtk.ButtonsType.OK,
                                text="Compound Not Found"
                            )
                            error_dialog.format_secondary_text(
                                f"Compound '{compound_id}' not found in {source.title()}.\n\n"
                                f"Please verify the ID or enter data manually."
                            )
                            error_dialog.run()
                            error_dialog.destroy()
                    
                    except NotImplementedError:
                        # Week 3: Remote fetch not yet implemented
                        info_dialog = Gtk.MessageDialog(
                            transient_for=self.dialog,
                            flags=0,
                            message_type=Gtk.MessageType.INFO,
                            buttons=Gtk.ButtonsType.OK,
                            text="Remote Fetch Coming Soon"
                        )
                        info_dialog.format_secondary_text(
                            "Remote API fetching will be implemented in Week 3.\n\n"
                            "For now, please enter thermodynamic data manually."
                        )
                        info_dialog.run()
                        info_dialog.destroy()
        
        except Exception as e:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Failed to Fetch Data"
            )
            error_dialog.format_secondary_text(
                f"Could not retrieve thermodynamic data: {str(e)}\n\n"
                "Please check the compound ID and try again, or enter data manually."
            )
            error_dialog.run()
            error_dialog.destroy()
        
        finally:
            # Hide spinner and re-enable button
            if spinner:
                spinner.stop()
                spinner.set_visible(False)
            button.set_sensitive(True)
    
    def _populate_fetched_data(self, data: Dict[str, Any], from_cache: bool = False):
        """Populate thermodynamic fields from fetched data.
        
        Args:
            data: Compound data dictionary
            from_cache: Whether data came from local cache
        """
        # Compound name
        compound_name_label = self.builder.get_object('thermo_compound_name_label')
        if compound_name_label and 'compound_name' in data:
            compound_name_label.set_text(data['compound_name'])
        
        # ΔGf°
        dg_entry = self.builder.get_object('thermo_delta_g_entry')
        if dg_entry and data.get('delta_g_formation') is not None:
            dg_entry.set_text(f"{data['delta_g_formation']:.2f}")
        
        # Charge
        charge_spin = self.builder.get_object('thermo_charge_spin')
        if charge_spin and 'charge' in data:
            charge_spin.set_value(float(data['charge']))
        
        # #Protons
        n_protons_spin = self.builder.get_object('thermo_n_protons_spin')
        if n_protons_spin and 'n_protons' in data:
            n_protons_spin.set_value(float(data['n_protons']))
        
        # pKa values
        pka_entry = self.builder.get_object('thermo_pka_entry')
        if pka_entry and 'pKa_values' in data and data['pKa_values']:
            if isinstance(data['pKa_values'], list):
                pka_text = ', '.join(str(x) for x in data['pKa_values'])
                pka_entry.set_text(pka_text)
        
        # Data source
        source_combo = self.builder.get_object('thermo_source_combo')
        if source_combo and 'source' in data:
            source_value = data['source'].lower()
            source_map = {
                'manual': 1,
                'equilibrator': 2,
                'brenda': 3,
                'mapper': 1  # Treat mapper as manual
            }
            index = source_map.get(source_value, 0)
            source_combo.set_active(index)
    
    def _on_clear_thermodynamic_clicked(self, button):
        """Handle 'Clear All' button click.
        
        Clears all thermodynamic properties fields.
        """
        # Clear all entry fields
        compound_entry = self.builder.get_object('thermo_compound_id_entry')
        if compound_entry:
            compound_entry.set_text('')
        
        compound_name_label = self.builder.get_object('thermo_compound_name_label')
        if compound_name_label:
            compound_name_label.set_text('-')
        
        dg_entry = self.builder.get_object('thermo_delta_g_entry')
        if dg_entry:
            dg_entry.set_text('')
        
        charge_spin = self.builder.get_object('thermo_charge_spin')
        if charge_spin:
            charge_spin.set_value(0)
        
        n_protons_spin = self.builder.get_object('thermo_n_protons_spin')
        if n_protons_spin:
            n_protons_spin.set_value(0)
        
        pka_entry = self.builder.get_object('thermo_pka_entry')
        if pka_entry:
            pka_entry.set_text('')
        
        source_combo = self.builder.get_object('thermo_source_combo')
        if source_combo:
            source_combo.set_active(0)  # None
        
        # Reset conditions to defaults
        ph_spin = self.builder.get_object('thermo_ph_spin')
        if ph_spin:
            ph_spin.set_value(7.0)  # Default pH
        
        temp_spin = self.builder.get_object('thermo_temperature_spin')
        if temp_spin:
            temp_spin.set_value(298.15)  # Default temperature (25°C)
        
        ionic_spin = self.builder.get_object('thermo_ionic_strength_spin')
        if ionic_spin:
            ionic_spin.set_value(0.1)  # Default ionic strength
        
        # Clear search field
        search_entry = self.builder.get_object('thermo_search_name_entry')
        if search_entry:
            search_entry.set_text('')
    
    def _on_compound_id_changed(self, entry):
        """Handle compound ID field changes.
        
        When user types a compound ID (e.g., 'C00002'), automatically:
        1. Look up the compound name ('ATP')
        2. Populate the compound_name label
        3. Suggest updating the place name field
        
        This provides name → ID bidirectional mapping.
        """
        compound_id = entry.get_text().strip().upper()
        
        if not compound_id:
            # Clear compound name label
            compound_name_label = self.builder.get_object('thermo_compound_name_label')
            if compound_name_label:
                compound_name_label.set_text('-')
            return
        
        # Look up compound name
        compound_name = CompoundMapper.id_to_name(compound_id)
        
        if compound_name:
            # Update compound name label
            compound_name_label = self.builder.get_object('thermo_compound_name_label')
            if compound_name_label:
                compound_name_label.set_text(compound_name)
            
            # Suggest updating place name (only if current name is default/empty)
            name_entry = self.builder.get_object('name_entry')
            if name_entry:
                current_name = name_entry.get_text().strip()
                # Only auto-fill if name is empty or looks like default ID (P1, P2, etc.)
                if not current_name or (current_name.startswith('P') and current_name[1:].isdigit()):
                    # Temporarily block name_changed handler to avoid recursion
                    with self._block_handler(name_entry, 'changed'):
                        name_entry.set_text(compound_name)
                        # Change text color to indicate it's a suggestion
                        name_entry.set_icon_from_icon_name(
                            Gtk.EntryIconPosition.SECONDARY,
                            'dialog-information-symbolic'
                        )
                        name_entry.set_icon_tooltip_text(
                            Gtk.EntryIconPosition.SECONDARY,
                            f'Suggestion from compound ID {compound_id}'
                        )
    
    def _on_place_name_changed(self, entry):
        """Handle place name field changes.
        
        When user types a compound name (e.g., 'ATP'), automatically:
        1. Look up the compound ID ('C00002')
        2. Suggest populating the compound_id field
        
        This provides ID → name bidirectional mapping.
        """
        place_name = entry.get_text().strip()
        
        if not place_name or len(place_name) < 2:
            return
        
        # Look up compound ID
        compound_id = CompoundMapper.name_to_id(place_name)
        
        if compound_id:
            # Get current compound_id entry
            compound_entry = self.builder.get_object('thermo_compound_id_entry')
            if compound_entry:
                current_id = compound_entry.get_text().strip()
                
                # Only auto-fill if compound_id is empty
                if not current_id:
                    # Temporarily block compound_id_changed handler to avoid recursion
                    with self._block_handler(compound_entry, 'changed'):
                        compound_entry.set_text(compound_id)
                        # Add visual indicator
                        compound_entry.set_icon_from_icon_name(
                            Gtk.EntryIconPosition.SECONDARY,
                            'dialog-information-symbolic'
                        )
                        compound_entry.set_icon_tooltip_text(
                            Gtk.EntryIconPosition.SECONDARY,
                            f'Suggestion from place name "{place_name}"'
                        )
                    
                    # Also populate compound name label
                    compound_name_label = self.builder.get_object('thermo_compound_name_label')
                    if compound_name_label:
                        compound_name_label.set_text(place_name)
    
    def _block_handler(self, widget, signal):
        """Context manager to temporarily block signal handler.
        
        Prevents infinite recursion when programmatically changing fields.
        
        Usage:
            with self._block_handler(entry, 'changed'):
                entry.set_text('new value')  # Won't trigger changed signal
        """
        from contextlib import contextmanager
        
        @contextmanager
        def blocker():
            # Block all handlers for this signal
            GObject.signal_handlers_block_matched(
                widget,
                GObject.SignalMatchType.FUNC,
                0, 0, None, None, None
            )
            try:
                yield
            finally:
                # Unblock
                GObject.signal_handlers_unblock_matched(
                    widget,
                    GObject.SignalMatchType.FUNC,
                    0, 0, None, None, None
                )
        
        return blocker()
    
    def _on_search_by_name_clicked(self, button):
        """Handle 'Search' button click for compound name search.
        
        Search equilibrator database by compound name (e.g., 'ATP', 'Glucose')
        and populate the compound ID field with the result.
        """
        search_entry = self.builder.get_object('thermo_search_name_entry')
        if not search_entry:
            return
        
        search_name = search_entry.get_text().strip()
        if not search_name:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Search Name Required"
            )
            error_dialog.format_secondary_text(
                "Please enter a compound name (e.g., ATP, Glucose, NADH) to search."
            )
            error_dialog.run()
            error_dialog.destroy()
            return
        
        try:
            # First try compound mapper for quick lookup
            from shypn.thermodynamics.compound_mapper import CompoundMapper
            compound_id = CompoundMapper.name_to_id(search_name)
            
            if compound_id:
                # Found in local mapper - populate compound ID field
                compound_entry = self.builder.get_object('thermo_compound_id_entry')
                if compound_entry:
                    compound_entry.set_text(compound_id)
                
                # Show success message
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Compound Found"
                )
                info_dialog.format_secondary_text(
                    f"Found '{search_name}' → {compound_id}\n\n"
                    f"Compound ID has been populated. Click 'Fetch from Database' to retrieve thermodynamic data."
                )
                info_dialog.run()
                info_dialog.destroy()
            else:
                # Not found in local mapper - suggest manual entry
                not_found_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="Compound Not Found in Local Database"
                )
                not_found_dialog.format_secondary_text(
                    f"'{search_name}' not found in the local compound mapper.\n\n"
                    f"Try variations (e.g., 'ATP' vs 'Adenosine triphosphate') or enter the compound ID manually.\n\n"
                    f"Supported IDs: KEGG (Cxxxxx), ChEBI (CHEBI:xxxxx)"
                )
                not_found_dialog.run()
                not_found_dialog.destroy()
        
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Search Error"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
    
    def _on_import_csv_clicked(self, button):
        """Handle 'Import from CSV' button click.
        
        Allows bulk import of thermodynamic data from a CSV file.
        CSV format: compound_id, compound_name, delta_g_formation, charge, n_protons, pKa_values
        """
        # Create file chooser dialog
        chooser = Gtk.FileChooserDialog(
            title="Import Thermodynamic Data from CSV",
            parent=self.dialog,
            action=Gtk.FileChooserAction.OPEN
        )
        chooser.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add CSV filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        chooser.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        chooser.add_filter(all_filter)
        
        # Root to active project if one is open
        try:
            from shypn.data.project_models import get_project_manager
            pm = get_project_manager()
            if pm.current_project and pm.current_project.base_path:
                chooser.set_current_folder(pm.current_project.base_path)
        except (ImportError, AttributeError):
            pass
        
        response = chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()
        
        if response != Gtk.ResponseType.OK or not filename:
            return
        
        try:
            # Import CSV
            import csv
            from shypn.thermodynamics.compound_database import CompoundDatabase
            
            db = CompoundDatabase()
            imported_count = 0
            errors = []
            
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    try:
                        # Parse CSV row
                        compound_id = row.get('compound_id', '').strip()
                        if not compound_id:
                            errors.append(f"Row {row_num}: Missing compound_id")
                            continue
                        
                        # Build compound data dict
                        data = {
                            'compound_id': compound_id,
                            'compound_name': row.get('compound_name', '').strip() or compound_id,
                            'delta_g_formation': None,
                            'charge': 0,
                            'n_protons': 0,
                            'pKa_values': [],
                            'source': 'CSV Import',
                            'fetch_date': None
                        }
                        
                        # Parse numeric fields
                        if 'delta_g_formation' in row and row['delta_g_formation'].strip():
                            try:
                                data['delta_g_formation'] = float(row['delta_g_formation'])
                            except ValueError:
                                errors.append(f"Row {row_num}: Invalid delta_g_formation")
                        
                        if 'charge' in row and row['charge'].strip():
                            try:
                                data['charge'] = int(row['charge'])
                            except ValueError:
                                errors.append(f"Row {row_num}: Invalid charge")
                        
                        if 'n_protons' in row and row['n_protons'].strip():
                            try:
                                data['n_protons'] = int(row['n_protons'])
                            except ValueError:
                                errors.append(f"Row {row_num}: Invalid n_protons")
                        
                        if 'pKa_values' in row and row['pKa_values'].strip():
                            try:
                                pka_str = row['pKa_values'].strip()
                                # Handle JSON array format: "[6.5, 4.0, 2.0]" or comma-separated: "6.5, 4.0, 2.0"
                                if pka_str.startswith('[') and pka_str.endswith(']'):
                                    # JSON array format
                                    import json
                                    data['pKa_values'] = json.loads(pka_str)
                                else:
                                    # Comma-separated format
                                    data['pKa_values'] = [float(x.strip()) for x in pka_str.split(',') if x.strip()]
                            except (ValueError, json.JSONDecodeError) as e:
                                errors.append(f"Row {row_num}: Invalid pKa_values - {e}")
                        
                        # Cache the compound
                        db.cache_compound(data)
                        imported_count += 1
                    
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
            
            # Show results
            result_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.INFO if not errors else Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=f"Import Complete: {imported_count} compounds imported"
            )
            
            if errors:
                error_summary = '\n'.join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_summary += f'\n... and {len(errors) - 10} more errors'
                result_dialog.format_secondary_text(
                    f"Encountered {len(errors)} errors:\n\n{error_summary}"
                )
            else:
                result_dialog.format_secondary_text(
                    "All compounds were successfully imported and cached."
                )
            
            result_dialog.run()
            result_dialog.destroy()
        
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Import Failed"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
    
    def _on_export_csv_clicked(self, button):
        """Handle 'Export to CSV' button click.
        
        Exports all cached thermodynamic data to a CSV file.
        """
        # Create file chooser dialog for saving
        chooser = Gtk.FileChooserDialog(
            title="Export Thermodynamic Data to CSV",
            parent=self.dialog,
            action=Gtk.FileChooserAction.SAVE
        )
        chooser.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        chooser.set_do_overwrite_confirmation(True)
        chooser.set_current_name("thermodynamic_data.csv")
        
        # Add CSV filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        chooser.add_filter(csv_filter)
        
        # Root to active project if one is open
        try:
            from shypn.data.project_models import get_project_manager
            pm = get_project_manager()
            if pm.current_project and pm.current_project.base_path:
                chooser.set_current_folder(pm.current_project.base_path)
        except (ImportError, AttributeError):
            pass
        
        response = chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()
        
        if response != Gtk.ResponseType.OK or not filename:
            return
        
        try:
            # Export to CSV
            import csv
            from shypn.thermodynamics.compound_database import CompoundDatabase
            
            db = CompoundDatabase()
            
            # Get all cached compounds
            compounds = db.get_all_cached()
            
            if not compounds:
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="No Data to Export"
                )
                info_dialog.format_secondary_text(
                    "The thermodynamic cache is empty. Fetch some compounds first."
                )
                info_dialog.run()
                info_dialog.destroy()
                return
            
            # Write CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['compound_id', 'compound_name', 'delta_g_formation', 
                             'charge', 'n_protons', 'pKa_values', 'source', 'fetch_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for compound in compounds:
                    # Format pKa values as comma-separated string
                    pka_str = ','.join(str(x) for x in compound.get('pKa_values', []))
                    
                    writer.writerow({
                        'compound_id': compound.get('compound_id', ''),
                        'compound_name': compound.get('compound_name', ''),
                        'delta_g_formation': compound.get('delta_g_formation', ''),
                        'charge': compound.get('charge', 0),
                        'n_protons': compound.get('n_protons', 0),
                        'pKa_values': pka_str,
                        'source': compound.get('source', ''),
                        'fetch_date': compound.get('fetch_date', '')
                    })
            
            # Show success message
            success_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Export Complete: {len(compounds)} compounds exported"
            )
            success_dialog.format_secondary_text(
                f"Thermodynamic data exported to:\n{filename}"
            )
            success_dialog.run()
            success_dialog.destroy()
        
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Export Failed"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()

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
        model: PetriNetModel instance (optional, for future use)
    
    Returns:
        PlacePropDialogLoader: Configured dialog loader instance.
    """
    return PlacePropDialogLoader(place_obj, parent_window=parent_window, ui_dir=ui_dir, 
                                  persistency_manager=persistency_manager, model=model)