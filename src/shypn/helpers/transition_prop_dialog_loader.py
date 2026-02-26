"""
Transition Properties Dialog Loader

Loads and manages the Transition properties dialog UI.
Follows project pattern: thin loader with business logic in data layer.
"""
import os
import sys
import numpy as np
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from shypn.helpers.color_picker import setup_color_picker_in_dialog
from shypn.data.validation import ExpressionValidator


class TransitionPropDialogLoader(GObject.GObject):
    """Loader for Transition properties dialog.
    
    This class loads and manages the Transition properties dialog UI from
    transition_prop_dialog.ui. The dialog allows editing Transition attributes
    with context-sensitive fields based on transition type.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, transition_obj, parent_window=None, ui_dir=None,
                 persistency_manager=None, model=None, data_collector=None):
        """Initialize the Transition properties dialog loader.
        
        Args:
            transition_obj: Transition object to edit properties for
            parent_window: Parent window for modal dialog
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/
            persistency_manager: NetObjPersistency instance for marking document dirty
            model: ModelCanvasManager instance for accessing Petri net structure
            data_collector: Optional SimulationDataCollector for runtime diagnostics
        """
        super().__init__()
        
        # Resolve UI path (same pattern as place_prop_dialog_loader)
        if ui_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            ui_dir = os.path.join(project_root, 'ui', 'dialogs')
        
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'transition_prop_dialog.ui')
        self.transition_obj = transition_obj
        self.parent_window = parent_window
        self.persistency_manager = persistency_manager
        self.model = model
        self.data_collector = data_collector
        
        # Widget references
        self.builder = None
        self.dialog = None
        self.color_picker = None
        self.locality_widget = None
        
        # Load and setup
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._update_field_visibility()
        self._update_adaptive_visibility()  # Initial visibility for adaptive box
        self._setup_type_change_handler()
        self._setup_rate_sync()
        self._setup_kinetics_tab()
        self._setup_signal_dependencies_tab()  # Quorum sensing / 13-tuple Bio-PN formalism
    
    def _load_ui(self):
        """Load the Transition properties dialog UI from file."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(
                f"Transition properties dialog UI file not found: {self.ui_path}"
            )
        
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.dialog = self.builder.get_object('transition_properties_dialog')
        
        if self.dialog is None:
            raise ValueError(
                "Object 'transition_properties_dialog' not found in transition_prop_dialog.ui"
            )
        
        # WAYLAND FIX: Do NOT set transient_for here!
        # On Wayland, parent must be realized/mapped before set_transient_for()
        # We'll set it in run() when parent is guaranteed to be ready
        
        self.dialog.connect('response', self._on_response)
    
    def _setup_color_picker(self):
        """Setup and insert the color picker widget into the dialog."""
        current_color = getattr(self.transition_obj, 'border_color', (0.0, 0.0, 0.0))
        
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'transition_color_picker',
            current_color=current_color,
            button_size=28
        )
        
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
    
    def _on_color_selected(self, picker, color_rgb):
        """Handle color selection from picker.
        
        Args:
            picker: ColorPickerRow widget
            color_rgb: Selected RGB tuple (0.0-1.0)
        """
        pass  # Color applied on OK
    
    def _populate_fields(self):
        """Populate dialog fields with current Transition properties."""
        # ID (read-only, managed by IDManager)
        id_entry = self.builder.get_object('id_entry')
        if id_entry and hasattr(self.transition_obj, 'id'):
            id_entry.set_text(str(self.transition_obj.id))
        
        # Name (editable - user-created alias)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            name_entry.set_text(str(self.transition_obj.name))
            # Name is editable - user-created alias
        
        # Label (user-editable)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            label_entry.set_text(
                str(self.transition_obj.label) if self.transition_obj.label else ''
            )
        
        # Compartment (optional - for thermodynamic context)
        compartment_entry = self.builder.get_object('compartment_entry')
        if compartment_entry:
            compartment_value = ''
            # Check attribute first (preferred), then properties dict (legacy)
            if hasattr(self.transition_obj, 'compartment') and self.transition_obj.compartment:
                compartment_value = self.transition_obj.compartment
            elif hasattr(self.transition_obj, 'properties') and isinstance(self.transition_obj.properties, dict):
                compartment_value = self.transition_obj.properties.get('compartment', '')
            compartment_entry.set_text(str(compartment_value))
        
        # Transition type
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3, 'adaptive': 4}
            transition_type = self.transition_obj.transition_type or 'continuous'
            type_combo.set_active(type_map.get(transition_type, 3))
        
        # Adaptive properties
        if hasattr(self.transition_obj, 'properties') and isinstance(self.transition_obj.properties, dict):
            # Adaptive filter
            adaptive_filter_combo = self.builder.get_object('adaptive_filter_combo')
            if adaptive_filter_combo:
                filter_value = self.transition_obj.properties.get('adaptive_filter', 'inputs_only')
                filter_map = {'inputs_only': 0, 'outputs_only': 1, 'all_places': 2}
                adaptive_filter_combo.set_active(filter_map.get(filter_value, 0))
            
            # Volume threshold
            volume_threshold_spin = self.builder.get_object('volume_threshold_spin')
            if volume_threshold_spin:
                threshold_value = self.transition_obj.properties.get('volume_threshold', 1.0)
                volume_threshold_spin.set_value(float(threshold_value))
        
        # Firing policy (replaces priority spinner)
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo and hasattr(self.transition_obj, 'firing_policy'):
            # Map policy names to combobox indices (order: Random, Earliest, Latest, Priority, Race, Age, Preemptive-Priority, Preemptive, Single)
            policy_map = {
                'random': 0,
                'earliest': 1,
                'latest': 2,
                'priority': 3,
                'race': 4,
                'age': 5,
                'preemptive-priority': 6,
                'preemptive': 7,
                'single': 8,
            }
            policy = self.transition_obj.firing_policy or 'race'
            firing_policy_combo.set_active(policy_map.get(policy, 4))
            
            # Connect signal to show/hide priority value field
            firing_policy_combo.connect('changed', self._on_firing_policy_changed)
        
        # Priority value spin button (numeric priority for priority-based policies)
        priority_value_spin = self.builder.get_object('priority_value_spin')
        if priority_value_spin and hasattr(self.transition_obj, 'priority'):
            priority_value_spin.set_value(float(self.transition_obj.priority))
        
        # Show/hide priority value field based on current policy
        self._update_priority_field_visibility()
        
        # Source/Sink checkboxes
        is_source_check = self.builder.get_object('is_source_check')
        if is_source_check and hasattr(self.transition_obj, 'is_source'):
            is_source_check.set_active(self.transition_obj.is_source)
        
        is_sink_check = self.builder.get_object('is_sink_check')
        if is_sink_check and hasattr(self.transition_obj, 'is_sink'):
            is_sink_check.set_active(self.transition_obj.is_sink)
        
        # Rate (simple entry) - also check for rate_function formulas (SBML)
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry:
            rate_value = None
            
            # Priority 1: Check properties['rate_function_display'] (SBML biological names for UI)
            if hasattr(self.transition_obj, 'properties') and 'rate_function_display' in self.transition_obj.properties:
                rate_value = self.transition_obj.properties['rate_function_display']
            
            # Priority 2: Check transition.properties['rate_function'] (SBML formulas stored here)
            elif hasattr(self.transition_obj, 'properties') and 'rate_function' in self.transition_obj.properties:
                rate_value = self.transition_obj.properties['rate_function']
            
            # Priority 3: Fall back to simple rate value
            elif hasattr(self.transition_obj, 'rate') and self.transition_obj.rate is not None:
                rate_value = self.transition_obj.rate
            
            # Set the text if we found something
            if rate_value is not None:
                rate_entry.set_text(str(rate_value))
        
        # Earliest time (for Timed transitions)
        earliest_time_spin = self.builder.get_object('earliest_time_spin')
        if earliest_time_spin:
            earliest_value = None
            # Check top-level attribute first (JSON schema)
            if hasattr(self.transition_obj, 'earliest_time'):
                earliest_value = self.transition_obj.earliest_time
            # Fall back to properties dict
            elif hasattr(self.transition_obj, 'properties'):
                earliest_value = self.transition_obj.properties.get('earliest_time')
            # Set value or default for timed transitions
            if earliest_value is not None:
                earliest_time_spin.set_value(float(earliest_value))
            elif hasattr(self.transition_obj, 'transition_type') and self.transition_obj.transition_type == 'timed':
                earliest_time_spin.set_value(1.0)  # Default 1 second
        
        # Latest time (for Timed transitions)
        latest_time_spin = self.builder.get_object('latest_time_spin')
        if latest_time_spin:
            latest_value = None
            # Check top-level attribute first (JSON schema)
            if hasattr(self.transition_obj, 'latest_time'):
                latest_value = self.transition_obj.latest_time
            # Fall back to properties dict
            elif hasattr(self.transition_obj, 'properties'):
                latest_value = self.transition_obj.properties.get('latest_time')
            # Set value or default for timed transitions
            if latest_value is not None:
                latest_time_spin.set_value(float(latest_value))
            elif hasattr(self.transition_obj, 'transition_type') and self.transition_obj.transition_type == 'timed':
                latest_time_spin.set_value(1.0)  # Default 1 second
        
        # Guard function (TextView)
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            guard_value = self.transition_obj.guard
            if guard_value is not None:
                buffer.set_text(str(guard_value))
        
        # Check for directional rates first (reversible reactions)
        # Backward compatible: try new name first, fall back to old name
        rate_textview = self.builder.get_object('rate_function') or self.builder.get_object('rate_textview')
        rate_reverse_textview = self.builder.get_object('rate_reverse_textview')
        reversible_check = self.builder.get_object('reversible_check')
        
        rate_fwd = getattr(self.transition_obj, 'rate_forward', None)
        rate_rev = getattr(self.transition_obj, 'rate_reverse', None)
        has_directional = bool(rate_fwd or rate_rev)
        
        if has_directional:
            # Populate forward rate in main rate field
            if rate_fwd and rate_textview:
                buffer_fwd = rate_textview.get_buffer()
                buffer_fwd.set_text(str(rate_fwd))
            # Populate reverse rate in reverse field
            if rate_rev and rate_reverse_textview:
                buffer_rev = rate_reverse_textview.get_buffer()
                buffer_rev.set_text(str(rate_rev))
        else:
            # No directional rates - check other rate sources for rate_textview
            if rate_textview:
                buffer = rate_textview.get_buffer()
                rate_func = None
                
                # Priority 1: Check properties['rate_function_display'] (SBML biological names for UI)
                if hasattr(self.transition_obj, 'properties') and 'rate_function_display' in self.transition_obj.properties:
                    rate_func = self.transition_obj.properties['rate_function_display']
                
                # Priority 2: Check transition.properties['rate_function'] (SBML formulas stored here)
                elif hasattr(self.transition_obj, 'properties') and 'rate_function' in self.transition_obj.properties:
                    rate_func = self.transition_obj.properties['rate_function']
                
                # Priority 3: Check top-level rate_function attribute (direct attribute)
                elif hasattr(self.transition_obj, 'rate_function') and self.transition_obj.rate_function:
                    rate_func = self.transition_obj.rate_function
                
                # Priority 4: Check kinetic_metadata.formula (backup for SBML)
                elif hasattr(self.transition_obj, 'kinetic_metadata') and self.transition_obj.kinetic_metadata:
                    if hasattr(self.transition_obj.kinetic_metadata, 'formula'):
                        rate_func = self.transition_obj.kinetic_metadata.formula
                
                # Priority 5: Fall back to simple rate value
                elif hasattr(self.transition_obj, 'rate') and self.transition_obj.rate is not None:
                    rate_func = str(self.transition_obj.rate)
                
                # Set the text if we found something
                if rate_func is not None:
                    buffer.set_text(str(rate_func))
        
        # Set reversible checkbox state
        if reversible_check:
            reversible_check.set_active(has_directional)
            # Connect signal to toggle visibility of reverse rate field
            reversible_check.connect('toggled', self._on_reversible_toggled)
        
        # Update visibility of reverse rate field
        self._update_reversible_fields_visibility()
        
        # Line Width
        width_entry = self.builder.get_object('prop_transition_width_entry')
        if width_entry and hasattr(self.transition_obj, 'border_width'):
            width_entry.set_text(str(self.transition_obj.border_width))
        
        # Rectangle Width
        rect_width_entry = self.builder.get_object('rect_width_entry')
        if rect_width_entry and hasattr(self.transition_obj, 'width'):
            rect_width_entry.set_text(str(self.transition_obj.width))
        
        # Rectangle Height
        rect_height_entry = self.builder.get_object('rect_height_entry')
        if rect_height_entry and hasattr(self.transition_obj, 'height'):
            rect_height_entry.set_text(str(self.transition_obj.height))
        
        # Setup flip orientation button
        flip_button = self.builder.get_object('flip_orientation_button')
        if flip_button:
            flip_button.connect('clicked', self._on_flip_orientation_clicked)
        
        # Update type description
        self._update_type_description()
    
    def _update_field_visibility(self):
        """Update field visibility based on transition type.
        
        Delegates to transition object for business logic.
        """
        editable_fields = self.transition_obj.get_editable_fields()
        
        # Show/hide rate entry
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry:
            rate_entry.set_visible(editable_fields.get('rate', True))
        
        # Show/hide rate function (multi-line)
        # Backward compatible: try new name first, fall back to old name
        rate_textview = self.builder.get_object('rate_function') or self.builder.get_object('rate_textview')
        if rate_textview:
            parent = rate_textview.get_parent()
            if parent:
                parent.set_visible(editable_fields.get('rate_function', True))
        
        # Show/hide firing policy
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo:
            parent = firing_policy_combo.get_parent()
            if parent:
                parent.set_visible(editable_fields.get('firing_policy', True))
        
        # Show/hide timing fields (only for timed transitions)
        is_timed = hasattr(self.transition_obj, 'transition_type') and self.transition_obj.transition_type == 'timed'
        earliest_time_box = self.builder.get_object('earliest_time_box')
        if earliest_time_box:
            earliest_time_box.set_visible(is_timed)
        latest_time_box = self.builder.get_object('latest_time_box')
        if latest_time_box:
            latest_time_box.set_visible(is_timed)
    
    def _update_priority_field_visibility(self):
        """Show/hide priority value field based on selected firing policy."""
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        priority_value_box = self.builder.get_object('priority_value_box')
        
        if firing_policy_combo and priority_value_box:
            active_index = firing_policy_combo.get_active()
            # Show priority field only for: Priority (index 3) or Preemptive-Priority (index 6)
            show_priority = active_index in [3, 6]
            priority_value_box.set_visible(show_priority)
    
    def _on_firing_policy_changed(self, combo):
        """Handle firing policy combo box changes."""
        self._update_priority_field_visibility()
    
    def _on_reversible_toggled(self, checkbox):
        """Handle reversible checkbox toggle."""
        self._update_reversible_fields_visibility()
    
    def _on_flip_orientation_clicked(self, button):
        """Handle flip orientation button click - swap width and height."""
        rect_width_entry = self.builder.get_object('rect_width_entry')
        rect_height_entry = self.builder.get_object('rect_height_entry')
        
        if rect_width_entry and rect_height_entry:
            # Get current values
            width_text = rect_width_entry.get_text().strip()
            height_text = rect_height_entry.get_text().strip()
            
            # Swap them
            rect_width_entry.set_text(height_text)
            rect_height_entry.set_text(width_text)
            
            # Apply immediately to transition object if valid
            try:
                if width_text and height_text:
                    width_val = float(width_text)
                    height_val = float(height_text)
                    
                    # Swap in the transition object
                    if hasattr(self.transition_obj, 'width') and hasattr(self.transition_obj, 'height'):
                        self.transition_obj.width = height_val
                        self.transition_obj.height = width_val
                        
                        # Mark document dirty
                        if self.persistency_manager:
                            self.persistency_manager.mark_dirty()
                        
                        # Trigger canvas redraw immediately
                        if self.model and hasattr(self.model, '_drawing_area') and self.model._drawing_area:
                            self.model._drawing_area.queue_draw()
                        
                        # Emit change signal for other listeners
                        self.emit('properties-changed')
            except ValueError:
                pass  # Invalid values, just swap the text
    
    def _show_error_dialog(self, title, message):
        """Show error dialog with given title and message."""
        error_dialog = Gtk.MessageDialog(
            transient_for=self.dialog,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        error_dialog.format_secondary_text(
            f"{message}\n\nPlease correct the expression before applying."
        )
        error_dialog.run()
        error_dialog.destroy()
    
    def _update_reversible_fields_visibility(self):
        """Show/hide reverse rate field based on reversible checkbox."""
        reversible_check = self.builder.get_object('reversible_check')
        rate_reverse_box = self.builder.get_object('rate_reverse_box')
        
        if reversible_check and rate_reverse_box:
            is_reversible = reversible_check.get_active()
            # Show/hide only the reverse rate field
            # Rate function field always visible (acts as forward rate when reversible)
            rate_reverse_box.set_visible(is_reversible)
    
    def _update_type_description(self):
        """Update type description label based on current type."""
        desc_label = self.builder.get_object('type_description_label')
        if desc_label:
            description = self.transition_obj.get_type_description()
            desc_label.set_text(description)
    
    def _update_adaptive_visibility(self):
        """Show/hide adaptive properties box based on transition type."""
        adaptive_box = self.builder.get_object('adaptive_properties_box')
        if adaptive_box:
            is_adaptive = hasattr(self.transition_obj, 'transition_type') and \
                         self.transition_obj.transition_type == 'adaptive'
            adaptive_box.set_visible(is_adaptive)
    
    def _setup_type_change_handler(self):
        """Setup handler for transition type changes."""
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo:
            type_combo.connect('changed', self._on_type_changed)
    
    def _on_type_changed(self, combo):
        """Handle transition type change - update field visibility."""
        type_list = ['immediate', 'timed', 'stochastic', 'continuous', 'adaptive']
        new_type = type_list[combo.get_active()]
        
        # Update transition object temporarily (not persisted until OK)
        self.transition_obj.transition_type = new_type
        
        # Update UI
        self._update_field_visibility()
        self._update_type_description()
        self._update_adaptive_visibility()
    
    def _setup_rate_sync(self):
        """Setup synchronization between rate function TextView and rate entry."""
        # Backward compatible: try new name first, fall back to old name
        rate_textview = self.builder.get_object('rate_function') or self.builder.get_object('rate_textview')
        rate_entry = self.builder.get_object('rate_entry')
        
        if rate_textview and rate_entry:
            buffer = rate_textview.get_buffer()
            buffer.connect('changed', lambda buf: self._sync_rate_to_entry(buf, rate_entry))
    
    def _validate_rate_function_runtime(self, rate_text):
        """Validate rate function syntax and function calls.
        
        Validates:
        - Python syntax (parentheses, operators, etc.)
        - Function names exist in catalog
        - Function call structure (not parameter count - let Python handle that)
        
        Does NOT validate:
        - Variable names (allows any: P1, S, glucose, ATP, etc.)
        - Parameter values
        - Expression complexity
        
        Args:
            rate_text: Rate function expression string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not rate_text or not rate_text.strip():
            return (True, "")
        
        rate_text = rate_text.strip()
        
        # Try to parse as simple number first
        try:
            float(rate_text)
            return (True, "")  # Valid numeric value
        except ValueError:
            pass  # Not a simple number, continue with expression validation
        
        # Check for basic syntax errors (unmatched parentheses, operators, etc.)
        try:
            compile(rate_text, '<string>', 'eval')
        except SyntaxError as e:
            return (False, f"Syntax error: {e.msg}")
        
        # Validate that function names (if any) exist in the catalog
        try:
            import ast
            import re
            from shypn.engine import function_catalog
            
            # Parse the expression to extract function calls
            tree = ast.parse(rate_text, mode='eval')
            
            # Extract all function names used
            function_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        function_names.add(node.func.id)
            
            # Check if functions exist in catalog or are built-in
            available_functions = set(function_catalog.FUNCTION_CATALOG.keys())
            builtin_functions = {
                'abs', 'min', 'max', 'round', 'int', 'float', 'sum', 'len',
                'sqrt', 'exp', 'log', 'log10', 'log2',
                'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                'sinh', 'cosh', 'tanh', 'ceil', 'floor', 'pow'
            }
            available_functions.update(builtin_functions)
            
            # Check for undefined functions
            undefined_functions = function_names - available_functions
            if undefined_functions:
                return (False, 
                    f"Undefined function(s): {', '.join(sorted(undefined_functions))}\n\n"
                    f"Available functions: {', '.join(sorted(list(function_catalog.FUNCTION_CATALOG.keys())[:10]))}...")
            
            # All checks passed
            return (True, "")
            
        except Exception as e:
            # If we can't parse for validation, accept it (let runtime catch real errors)
            return (True, "")
    
    def _sync_rate_to_entry(self, buffer, rate_entry):
        """Sync rate function TextView to rate entry with preview.
        
        Shows expression preview or simplified value in the entry field.
        """
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True).strip()
        
        if not text:
            rate_entry.set_text('')
            return
        
        # Validate expression
        is_valid, error_msg, parsed = ExpressionValidator.validate_expression(text)
        
        if not is_valid:
            # Show error in entry
            rate_entry.set_text(f'[Error] {error_msg[:30]}...')
            return
        
        # If it's a simple number, show it directly
        if isinstance(parsed, (int, float)):
            rate_entry.set_text(str(parsed))
        else:
            # Show expression indicator
            rate_entry.set_text(f'[Expression] {text[:20]}...')
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            if self._apply_changes():
                if self.persistency_manager:
                    self.persistency_manager.mark_dirty()
                self.emit('properties-changed')
        
        # Don't destroy here - let explicit destroy() method handle it
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Transition object.
        
        REFACTORED (Sprint 2): Extracted helper methods to reduce complexity.
        Original complexity: 60 → New complexity: <15
        
        Returns:
            bool: True if successful, False if validation failed
        """
        try:
            # Apply properties in logical groups
            self._apply_basic_properties()
            self._apply_adaptive_properties()
            self._apply_firing_and_priority()
            self._apply_flags()
            
            # Rate functions require validation
            if not self._apply_rate_functions():
                return False  # Validation failed
            
            # Guard requires validation
            if not self._apply_guard():
                return False  # Validation failed
            
            self._apply_timing_parameters()
            self._apply_visual_properties()
            self._save_kinetic_entry_fields()
            
            return True
            
        except ValueError as e:
            self._show_error_dialog("Validation Error", str(e))
            return False

    def _apply_basic_properties(self):
        """Apply basic transition properties: name, label, compartment, type."""
        # Name (user-editable alias)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            new_name = name_entry.get_text().strip()
            if new_name:
                self.transition_obj.name = new_name
        
        # Label
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry:
            new_label = label_entry.get_text().strip()
            self.transition_obj.label = new_label if new_label else None
        
        # Compartment
        compartment_entry = self.builder.get_object('compartment_entry')
        if compartment_entry:
            compartment_text = compartment_entry.get_text().strip()
            self.transition_obj.compartment = compartment_text if compartment_text else None
        
        # Transition type
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo:
            type_list = ['immediate', 'timed', 'stochastic', 'continuous', 'adaptive']
            self.transition_obj.transition_type = type_list[type_combo.get_active()]

    def _apply_adaptive_properties(self):
        """Apply adaptive transition specific properties."""
        if self.transition_obj.transition_type == 'adaptive':
            if not hasattr(self.transition_obj, 'properties') or not isinstance(self.transition_obj.properties, dict):
                self.transition_obj.properties = {}
            
            # Adaptive filter
            adaptive_filter_combo = self.builder.get_object('adaptive_filter_combo')
            if adaptive_filter_combo:
                filter_list = ['inputs_only', 'outputs_only', 'all_places']
                self.transition_obj.properties['adaptive_filter'] = filter_list[adaptive_filter_combo.get_active()]
            
            # Volume threshold
            volume_threshold_spin = self.builder.get_object('volume_threshold_spin')
            if volume_threshold_spin:
                self.transition_obj.properties['volume_threshold'] = volume_threshold_spin.get_value()

    def _apply_firing_and_priority(self):
        """Apply firing policy and priority settings."""
        # Firing policy
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo:
            policy_list = [
                'random', 'earliest', 'latest', 'priority',
                'race', 'age', 'preemptive-priority',
                'preemptive', 'single',
            ]
            policy_index = firing_policy_combo.get_active()
            if policy_index >= 0:
                self.transition_obj.firing_policy = policy_list[policy_index]
        
        # Priority value
        priority_value_spin = self.builder.get_object('priority_value_spin')
        if priority_value_spin:
            self.transition_obj.priority = int(priority_value_spin.get_value())

    def _apply_flags(self):
        """Apply boolean flags: is_source, is_sink."""
        is_source_check = self.builder.get_object('is_source_check')
        if is_source_check:
            self.transition_obj.is_source = is_source_check.get_active()
        
        is_sink_check = self.builder.get_object('is_sink_check')
        if is_sink_check:
            self.transition_obj.is_sink = is_sink_check.get_active()

    def _apply_rate_functions(self) -> bool:
        """Apply rate functions with validation.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        rate_textview = self.builder.get_object('rate_function') or self.builder.get_object('rate_textview')
        reversible_check = self.builder.get_object('reversible_check')
        
        # Check if using directional rates (reversible)
        if reversible_check and reversible_check.get_active():
            return self._apply_directional_rates(rate_textview)
        elif rate_textview:
            return self._apply_regular_rate(rate_textview)
        
        return True

    def _apply_directional_rates(self, rate_textview) -> bool:
        """Apply forward and reverse rate functions for reversible transitions.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        rate_reverse_textview = self.builder.get_object('rate_reverse_textview')
        
        # Forward rate
        if rate_textview:
            buffer = rate_textview.get_buffer()
            start, end = buffer.get_bounds()
            rate_fwd_text = buffer.get_text(start, end, True).strip()
            
            if rate_fwd_text:
                is_valid, error_msg = self._validate_rate_function_runtime(rate_fwd_text)
                if not is_valid:
                    self._show_error_dialog("Invalid Forward Rate", error_msg)
                    return False
                self.transition_obj.rate_forward = rate_fwd_text
            else:
                # Default for continuous/adaptive
                if self.transition_obj.transition_type in ['continuous', 'adaptive']:
                    self.transition_obj.rate_forward = "1"
                elif 'rate_forward' in self.transition_obj.properties:
                    del self.transition_obj.properties['rate_forward']
        
        # Reverse rate
        if rate_reverse_textview:
            buffer = rate_reverse_textview.get_buffer()
            start, end = buffer.get_bounds()
            rate_rev_text = buffer.get_text(start, end, True).strip()
            
            if rate_rev_text:
                is_valid, error_msg = self._validate_rate_function_runtime(rate_rev_text)
                if not is_valid:
                    self._show_error_dialog("Invalid Reverse Rate", error_msg)
                    return False
                self.transition_obj.rate_reverse = rate_rev_text
            else:
                # Default for continuous/adaptive
                if self.transition_obj.transition_type in ['continuous', 'adaptive']:
                    self.transition_obj.rate_reverse = "1"
                elif 'rate_reverse' in self.transition_obj.properties:
                    del self.transition_obj.properties['rate_reverse']
        
        # Clear regular rate when using directional
        self.transition_obj.rate = None
        if hasattr(self.transition_obj, 'properties'):
            for key in ['rate_function', 'rate_function_display']:
                if key in self.transition_obj.properties:
                    del self.transition_obj.properties[key]
        
        return True

    def _apply_regular_rate(self, rate_textview) -> bool:
        """Apply regular (non-directional) rate function.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        # Clear directional rates
        if hasattr(self.transition_obj, 'properties'):
            for key in ['rate_forward', 'rate_reverse']:
                if key in self.transition_obj.properties:
                    del self.transition_obj.properties[key]
        
        buffer = rate_textview.get_buffer()
        start, end = buffer.get_bounds()
        rate_text = buffer.get_text(start, end, True).strip()
        
        if rate_text:
            # Validate
            is_valid, error_msg = self._validate_rate_function_runtime(rate_text)
            if not is_valid:
                self._show_error_dialog("Invalid Rate Function", error_msg)
                return False
            
            # Save to properties
            if not hasattr(self.transition_obj, 'properties'):
                self.transition_obj.properties = {}
            
            self.transition_obj.properties['rate_function_display'] = rate_text
            self.transition_obj.properties['rate_function'] = rate_text
            self.transition_obj.rate = None
        else:
            # No rate - set default for continuous/adaptive
            if self.transition_obj.transition_type in ['continuous', 'adaptive']:
                if not hasattr(self.transition_obj, 'properties'):
                    self.transition_obj.properties = {}
                self.transition_obj.properties['rate_function_display'] = "1"
                self.transition_obj.properties['rate_function'] = "1"
                self.transition_obj.rate = None
            else:
                # Clear rate_function for other types
                if hasattr(self.transition_obj, 'properties'):
                    for key in ['rate_function', 'rate_function_display']:
                        if key in self.transition_obj.properties:
                            del self.transition_obj.properties[key]
                self.transition_obj.set_rate(None)
        
        return True

    def _apply_guard(self) -> bool:
        """Apply guard expression with validation.
        
        Returns:
            bool: True if successful, False if validation failed
        """
        guard_textview = self.builder.get_object('guard_textview')
        if not guard_textview:
            return True
        
        buffer = guard_textview.get_buffer()
        start, end = buffer.get_bounds()
        guard_text = buffer.get_text(start, end, True).strip()
        
        if guard_text:
            # Validate guard expression
            is_valid, error_msg = self._validate_rate_function_runtime(guard_text)
            if not is_valid:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Invalid Guard Expression"
                )
                error_dialog.format_secondary_text(
                    f"The guard expression cannot be applied:\n\n{error_msg}\n\n"
                    f"Please correct the expression before applying."
                )
                error_dialog.run()
                error_dialog.destroy()
                return False
        
        self.transition_obj.set_guard(guard_text if guard_text else None)
        return True

    def _apply_timing_parameters(self):
        """Apply timing parameters for timed transitions."""
        # Earliest time
        earliest_time_spin = self.builder.get_object('earliest_time_spin')
        if earliest_time_spin:
            earliest_value = earliest_time_spin.get_value()
            self.transition_obj.earliest_time = earliest_value
            if not hasattr(self.transition_obj, 'properties'):
                self.transition_obj.properties = {}
            self.transition_obj.properties['earliest_time'] = earliest_value
        
        # Latest time
        latest_time_spin = self.builder.get_object('latest_time_spin')
        if latest_time_spin:
            latest_value = latest_time_spin.get_value()
            self.transition_obj.latest_time = latest_value
            if not hasattr(self.transition_obj, 'properties'):
                self.transition_obj.properties = {}
            self.transition_obj.properties['latest_time'] = latest_value

    def _apply_visual_properties(self):
        """Apply visual properties: color, border width, rectangle dimensions."""
        # Color
        if self.color_picker:
            selected_color = self.color_picker.get_selected_color()
            self.transition_obj.border_color = selected_color
            self.transition_obj.fill_color = selected_color
        
        # Line width
        width_entry = self.builder.get_object('prop_transition_width_entry')
        if width_entry and hasattr(self.transition_obj, 'border_width'):
            try:
                width_text = width_entry.get_text().strip()
                if width_text:
                    width_value = float(width_text)
                    self.transition_obj.border_width = max(0.5, width_value)
            except ValueError:
                pass
        
        # Rectangle width
        rect_width_entry = self.builder.get_object('rect_width_entry')
        if rect_width_entry and hasattr(self.transition_obj, 'width'):
            try:
                width_text = rect_width_entry.get_text().strip()
                if width_text:
                    width_value = float(width_text)
                    self.transition_obj.width = max(1.0, width_value)
            except ValueError:
                pass
        
        # Rectangle height
        rect_height_entry = self.builder.get_object('rect_height_entry')
        if rect_height_entry and hasattr(self.transition_obj, 'height'):
            try:
                height_text = rect_height_entry.get_text().strip()
                if height_text:
                    height_value = float(height_text)
                    self.transition_obj.height = max(1.0, height_value)
            except ValueError:
                pass

    def _show_error_dialog(self, title: str, message: str):
        """Show an error dialog with given title and message."""
        error_dialog = Gtk.MessageDialog(
            transient_for=self.dialog,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        error_dialog.format_secondary_text(message)
        error_dialog.run()
        error_dialog.destroy()

    
    def run(self):
        """Show the dialog and run it modally.
        
        Returns:
            Response ID from the dialog
        """
        # WAYLAND FIX: Set transient_for HERE, not in __init__!
        # On Wayland, parent must be realized/mapped before set_transient_for()
        # At run() time, parent is guaranteed to be ready
        if self.parent_window:
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
                
                # WAYLAND WORKAROUND: If window is maximized/fullscreen/tiled, wait a bit
                # This gives Wayland compositor time to complete the state transition
                if is_maximized or is_fullscreen or is_tiled:
                    import time
                    time.sleep(0.1)  # 100ms delay to let compositor settle
            
            # CRITICAL WAYLAND FIX: Process pending events before set_transient_for()
            # This ensures the Wayland compositor has processed all widget state changes
            display = Gdk.Display.get_default()
            if display:
                display.sync()  # Wait for all requests to be processed
            
            # Now set transient after compositor is synced
            self.dialog.set_transient_for(self.parent_window)
        
        # WAYLAND FIX: Explicitly show dialog before run() to prevent protocol errors
        # Critical for imported canvases where widget hierarchy is established asynchronously
        # Default canvas works because it's realized when main window shows
        # Imported canvases are created programmatically and dialogs may open before fully ready
        self.dialog.show()
        return self.dialog.run()
    
    def get_dialog(self):
        """Get the dialog widget.
        
        Returns:
            Gtk.Dialog: The dialog widget
        """
        return self.dialog

    def _setup_signal_dependencies_tab(self):
        """Setup signal dependencies tab for quorum sensing / environment-aware transitions.
        
        Displays auto-detected signal places (non-local dependencies from rate function).
        Signal places are detected automatically by parsing the rate function and finding
        place references without arc connections (13-tuple Bio-PN formalism: Ψ: T → 2^P).
        """
        # Skip if no model available
        if not self.model:
            return
        
        try:
            # Get the notebook
            notebook = self.builder.get_object('main_notebook')
            if not notebook:
                return
            
            # Create tab container
            tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            tab_box.set_margin_top(15)
            tab_box.set_margin_bottom(15)
            tab_box.set_margin_left(15)
            tab_box.set_margin_right(15)
            
            # Add description label
            desc_label = Gtk.Label()
            desc_label.set_markup(
                "<b>Signal Dependencies (Quorum Sensing / Non-Local Sensing)</b>\n\n"
                "Signal dependencies are <b>auto-detected</b> from the rate function.\n"
                "A place is a signal dependency if:\n"
                "  • Referenced in the rate function (e.g., <tt>[PlaceName]</tt>)\n"
                "  • <b>NOT</b> connected via an arc (non-local sensing)\n\n"
                "This implements the 13-tuple Bio-PN formalism (Ψ: T → 2<sup>P</sup>)."
            )
            desc_label.set_line_wrap(True)
            desc_label.set_xalign(0)
            tab_box.pack_start(desc_label, False, False, 5)
            
            # Add separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            tab_box.pack_start(separator, False, False, 5)
            
            # Get current signal dependencies (auto-detected by engine)
            current_signals = getattr(self.transition_obj, 'signal_places', [])
            is_env_aware = getattr(self.transition_obj, 'is_environment_aware', False)
            
            # Create info frame
            info_frame = Gtk.Frame()
            info_frame.set_label("Detection Status")
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            info_box.set_margin_top(10)
            info_box.set_margin_bottom(10)
            info_box.set_margin_left(10)
            info_box.set_margin_right(10)
            
            # Environment aware status
            status_label = Gtk.Label()
            if is_env_aware:
                status_label.set_markup(
                    "🟢 <b>Environment-aware:</b> Yes\n"
                    f"<b>Signal dependencies:</b> {len(current_signals)}"
                )
            else:
                status_label.set_markup(
                    "⚪ <b>Environment-aware:</b> No\n"
                    "<b>Signal dependencies:</b> None detected"
                )
            status_label.set_xalign(0)
            info_box.pack_start(status_label, False, False, 0)
            
            info_frame.add(info_box)
            tab_box.pack_start(info_frame, False, False, 5)
            
            # Show detected signal places
            if current_signals:
                scrolled = Gtk.ScrolledWindow()
                scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                scrolled.set_min_content_height(150)
                
                listbox = Gtk.ListBox()
                listbox.set_selection_mode(Gtk.SelectionMode.NONE)
                
                # Add row for each detected signal place
                for place_id in current_signals:
                    # Find place object
                    place = next((p for p in self.model.places if p.id == place_id), None)
                    
                    row = Gtk.ListBoxRow()
                    row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                    row_box.set_margin_top(5)
                    row_box.set_margin_bottom(5)
                    row_box.set_margin_left(10)
                    row_box.set_margin_right(10)
                    
                    # Indicator
                    indicator = Gtk.Label()
                    indicator.set_markup("🔗")
                    row_box.pack_start(indicator, False, False, 0)
                    
                    # Place info
                    if place:
                        place_label = Gtk.Label()
                        place_label.set_markup(f"<b>{place.id}</b>: {place.name}")
                        place_label.set_xalign(0)
                        row_box.pack_start(place_label, True, True, 0)
                    else:
                        # Place not found (might be deleted)
                        place_label = Gtk.Label()
                        place_label.set_markup(f"<b>{place_id}</b>: <i>(not found in model)</i>")
                        place_label.set_xalign(0)
                        row_box.pack_start(place_label, True, True, 0)
                    
                    row.add(row_box)
                    listbox.add(row)
                
                scrolled.add(listbox)
                tab_box.pack_start(scrolled, True, True, 5)
            else:
                # No signals detected
                no_signals_label = Gtk.Label()
                no_signals_label.set_markup(
                    "<i>No signal dependencies detected.\n\n"
                    "Signal dependencies are detected when:\n"
                    "  • The rate function references a place (e.g., <tt>k * [PlaceName]</tt>)\n"
                    "  • That place is NOT connected via an arc\n\n"
                    "Detection happens automatically during simulation.</i>"
                )
                no_signals_label.set_line_wrap(True)
                no_signals_label.set_xalign(0)
                tab_box.pack_start(no_signals_label, True, True, 20)
            
            # Add help/note
            help_label = Gtk.Label()
            help_label.set_markup(
                "<small><b>Note:</b> Signal dependencies are detected and updated automatically by the simulation engine.\n"
                "They persist through save/load cycles. To remove a signal dependency, remove the place reference\n"
                "from the rate function or add an arc connection.</small>"
            )
            help_label.set_line_wrap(True)
            help_label.set_xalign(0)
            tab_box.pack_start(help_label, False, False, 5)
            
            # Create tab label
            tab_label = Gtk.Label(label="Signal Dependencies")
            
            # Add tab to notebook
            notebook.append_page(tab_box, tab_label)
            tab_box.show_all()
            
        except Exception as e:
            # Log error but don't crash the dialog
            import traceback
            print(f"Error setting up signal dependencies tab: {e}")
            traceback.print_exc()
    
    def _setup_kinetics_tab(self):
        """Setup kinetics tab to display kinetic metadata and parameters.
        
        Populates the kinetics tab with:
        - Source information (SBML, BRENDA, SABIO-RK, Heuristic, etc.)
        - Confidence level
        - Rate type (michaelis_menten, mass_action, etc.)
        - Parameters table (name, value, source)
        - BRENDA authentication and fetching
        """
        # Initialize BRENDA client
        self.brenda_client = None
        self.brenda_authenticated = False
        
        # Initialize BRENDA cache manager (for offline/cached data)
        self.brenda_cache_manager = None
        try:
            from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
            from shypn.crossfetch.cache.brenda_cache_manager import BRENDACacheManager
            db = HeuristicDatabase()
            self.brenda_cache_manager = BRENDACacheManager(db)
            import logging
            logging.getLogger(self.__class__.__name__).info("BRENDA cache available for kinetics tab")
        except Exception as e:
            import logging
            logging.getLogger(self.__class__.__name__).warning(f"BRENDA cache unavailable: {e}")
        
        # Setup BRENDA button handlers
        self._setup_brenda_handlers()
        
        # Get widgets
        source_label = self.builder.get_object('kinetics_source_label')
        confidence_label = self.builder.get_object('kinetics_confidence_label')
        rate_type_label = self.builder.get_object('kinetics_rate_type_label')
        treeview = self.builder.get_object('kinetics_parameters_treeview')
        no_data_label = self.builder.get_object('kinetics_no_data_label')
        source_frame = self.builder.get_object('kinetics_source_frame')
        parameters_frame = self.builder.get_object('kinetics_parameters_frame')
        
        # Check for SBML kinetic_metadata OR SABIO-RK/BRENDA/Heuristic enriched metadata
        has_sbml_metadata = hasattr(self.transition_obj, 'kinetic_metadata') and self.transition_obj.kinetic_metadata
        has_enriched_metadata = hasattr(self.transition_obj, 'metadata') and self.transition_obj.metadata and \
                                any(k.endswith('_source') and 
                                    ('enriched' in str(v) or 'heuristic' in str(v))
                                    for k, v in self.transition_obj.metadata.items())
        
        if not has_sbml_metadata and not has_enriched_metadata:
            # No kinetic data - show message
            if no_data_label:
                no_data_label.set_visible(True)
            if source_frame:
                source_frame.set_visible(False)
            if parameters_frame:
                parameters_frame.set_visible(False)
            return
        
        # Hide no-data message
        if no_data_label:
            no_data_label.set_visible(False)
        
        # Determine source and get parameters
        parameters = {}
        source_str = "Unknown"
        confidence_str = ""
        rate_type = ""
        
        if has_sbml_metadata:
            # SBML curated metadata
            metadata = self.transition_obj.kinetic_metadata
            source = getattr(metadata, 'source', 'Unknown')
            source_str = source.value if hasattr(source, 'value') else str(source)
            
            confidence = getattr(metadata, 'confidence', 'Unknown')
            confidence_str = confidence.value if hasattr(confidence, 'value') else str(confidence)
            score = getattr(metadata, 'confidence_score', 0.0)
            confidence_str = f"{confidence_str.upper()} ({score:.2f})"
            
            rate_type = getattr(metadata, 'rate_type', 'N/A')
            parameters = getattr(metadata, 'parameters', {})
        
        elif has_enriched_metadata:
            # SABIO-RK, BRENDA enriched, or KEGG heuristic metadata
            metadata = self.transition_obj.metadata
            
            # Determine source from parameter sources
            sources = set()
            for key, value in metadata.items():
                if key.endswith('_source'):
                    sources.add(str(value))
            
            if 'sabio_rk_enriched' in sources:
                source_str = "SABIO-RK Enriched"
            elif 'brenda_enriched' in sources:
                source_str = "BRENDA Enriched"
            elif 'kegg_heuristic' in sources:
                source_str = "KEGG Heuristic"
            else:
                source_str = "Enriched"
            
            # Extract kinetic parameters (Km, Vmax, Kcat, Ki, etc.)
            param_keys = ['Km', 'Vmax', 'Kcat', 'Ki', 'k_forward', 'k_reverse']
            for key in param_keys:
                if key in metadata and metadata[key] is not None:
                    value = metadata[key]
                    units = metadata.get(f'{key}_units', '')
                    param_source = metadata.get(f'{key}_source', '')
                    # Store as tuple: (value, units, source)
                    parameters[key] = {'value': value, 'units': units, 'source': param_source}
        
        # Populate metadata info
        if source_label:
            source_label.set_text(f"Source: {source_str.upper()}")
        
        if confidence_label:
            if confidence_str:
                confidence_label.set_text(f"Confidence: {confidence_str}")
            else:
                confidence_label.set_text(f"Confidence: N/A")
        
        if rate_type_label:
            if not rate_type and hasattr(self.transition_obj, 'properties'):
                rate_func = self.transition_obj.properties.get('rate_function', '')
                if 'michaelis_menten' in rate_func:
                    rate_type = 'michaelis_menten'
                elif rate_func:
                    rate_type = 'custom'
            rate_type_label.set_text(f"Rate Type: {rate_type if rate_type else 'N/A'}")
        
        # Setup parameters table
        if treeview:
            # Create ListStore: parameter_name (str), value (str), source (str)
            store = Gtk.ListStore(str, str, str)
            
            if parameters:
                # Sort parameters by name for consistent display
                for param_name in sorted(parameters.keys()):
                    param_data = parameters[param_name]
                    
                    # Handle both old format (direct value) and new format (dict)
                    if isinstance(param_data, dict):
                        param_value = param_data.get('value')
                        units = param_data.get('units', '')
                        source = param_data.get('source', '')
                    else:
                        param_value = param_data
                        units = ''
                        source = ''
                    
                    # Format value with scientific notation if very small/large
                    if isinstance(param_value, (int, float)):
                        if abs(param_value) < 0.001 or abs(param_value) > 1000:
                            value_str = f"{param_value:.4e}"
                        else:
                            value_str = f"{param_value:.6g}"
                        if units:
                            value_str = f"{value_str} {units}"
                    else:
                        value_str = str(param_value)
                    
                    store.append([param_name, value_str, source])
            
            # Set model
            treeview.set_model(store)
            
            # Clear existing columns
            for col in treeview.get_columns():
                treeview.remove_column(col)
            
            # Add columns
            # Column 1: Parameter Name
            renderer_name = Gtk.CellRendererText()
            renderer_name.set_property('weight', 700)  # Bold
            column_name = Gtk.TreeViewColumn('Parameter', renderer_name, text=0)
            column_name.set_resizable(True)
            column_name.set_expand(False)
            column_name.set_min_width(100)
            treeview.append_column(column_name)
            
            # Column 2: Value
            renderer_value = Gtk.CellRendererText()
            renderer_value.set_property('family', 'monospace')
            column_value = Gtk.TreeViewColumn('Value', renderer_value, text=1)
            column_value.set_resizable(True)
            column_value.set_expand(True)
            column_value.set_min_width(150)
            treeview.append_column(column_value)
            
            # Column 3: Source
            renderer_source = Gtk.CellRendererText()
            renderer_source.set_property('style', 2)  # Italic
            renderer_source.set_property('foreground', '#666666')
            column_source = Gtk.TreeViewColumn('Source', renderer_source, text=2)
            column_source.set_resizable(True)
            column_source.set_expand(False)
            column_source.set_min_width(120)
            treeview.append_column(column_source)
        
        # Populate manual entry fields from kinetic_metadata.parameters
        self._populate_kinetic_entry_fields()
    
    def _populate_kinetic_entry_fields(self):
        """Populate manual kinetic parameter entry fields from kinetic_metadata.
        
        Reads from transition.kinetic_metadata.parameters dict and populates:
        - activation_energy
        - temperature_coefficient_Q10 (Q10)
        - k_cat
        - K_m (Michaelis constant)
        - k_i (inhibition constant)
        - hill_coefficient
        """
        # Get kinetic metadata
        metadata = None
        if hasattr(self.transition_obj, 'kinetic_metadata'):
            metadata = self.transition_obj.kinetic_metadata
        
        # If no metadata, leave fields empty for new entries
        if not metadata:
            return
        
        # Get parameters dict
        parameters = getattr(metadata, 'parameters', {})
        if not parameters:
            return
        
        # Populate Arrhenius parameters
        activation_energy_entry = self.builder.get_object('activation_energy_entry')
        if activation_energy_entry and 'activation_energy' in parameters:
            value = parameters['activation_energy']
            if isinstance(value, (int, float)):
                activation_energy_entry.set_text(f"{value:.6g}")
        
        q10_entry = self.builder.get_object('q10_entry')
        if q10_entry:
            # Check for Q10 or temperature_coefficient_Q10
            q10_value = parameters.get('Q10') or parameters.get('temperature_coefficient_Q10')
            if q10_value and isinstance(q10_value, (int, float)):
                q10_entry.set_text(f"{q10_value:.6g}")
        
        # Populate Michaelis-Menten parameters
        k_cat_entry = self.builder.get_object('k_cat_entry')
        if k_cat_entry and 'k_cat' in parameters:
            value = parameters['k_cat']
            if isinstance(value, (int, float)):
                k_cat_entry.set_text(f"{value:.6g}")
        
        k_m_entry = self.builder.get_object('k_m_entry')
        if k_m_entry:
            # Check for K_m or Km (case variations)
            km_value = parameters.get('K_m') or parameters.get('Km')
            if km_value and isinstance(km_value, (int, float)):
                k_m_entry.set_text(f"{km_value:.6g}")
        
        k_i_entry = self.builder.get_object('k_i_entry')
        if k_i_entry:
            # Check for K_i, Ki, k_i
            ki_value = parameters.get('K_i') or parameters.get('Ki') or parameters.get('k_i')
            if ki_value and isinstance(ki_value, (int, float)):
                k_i_entry.set_text(f"{ki_value:.6g}")
        
        # Populate Hill coefficient
        hill_entry = self.builder.get_object('hill_coefficient_entry')
        if hill_entry and 'hill_coefficient' in parameters:
            value = parameters['hill_coefficient']
            if isinstance(value, (int, float)):
                hill_entry.set_text(f"{value:.6g}")
    
    def _setup_brenda_handlers(self):
        """Setup BRENDA login/logout/fetch button handlers."""
        # Get widgets
        login_button = self.builder.get_object('brenda_login_button')
        logout_button = self.builder.get_object('brenda_logout_button')
        fetch_button = self.builder.get_object('brenda_fetch_button')
        
        # Connect signals
        if login_button:
            login_button.connect('clicked', self._on_brenda_login_clicked)
        
        if logout_button:
            logout_button.connect('clicked', self._on_brenda_logout_clicked)
        
        if fetch_button:
            fetch_button.connect('clicked', self._on_brenda_fetch_clicked)
    
    def _on_brenda_login_clicked(self, button):
        """Handle BRENDA login button click."""
        # Import dialog
        try:
            from shypn.dialogs.brenda_login_dialog import show_brenda_login_dialog
        except ImportError:
            print("Error: BRENDA login dialog not available")
            return
        
        # Show login dialog
        credentials = show_brenda_login_dialog(parent=self.dialog)
        
        if not credentials:
            return  # User cancelled
        
        email, password = credentials
        
        # Attempt authentication
        try:
            from shypn.data.brenda_soap_client import BRENDAAPIClient, ZEEP_AVAILABLE
            
            if not ZEEP_AVAILABLE:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="ZEEP Library Not Available"
                )
                error_dialog.format_secondary_text(
                    "The zeep library is required for BRENDA API access.\n\n"
                    "Install with: pip install zeep"
                )
                error_dialog.run()
                error_dialog.destroy()
                return
            
            # Create client and authenticate
            self.brenda_client = BRENDAAPIClient()
            
            # Show progress
            status_label = self.builder.get_object('brenda_status_label')
            if status_label:
                status_label.set_text("Status: Authenticating...")
            
            # Authenticate
            success = self.brenda_client.authenticate(email, password)
            
            if success:
                self.brenda_authenticated = True
                self._update_brenda_ui_state()
                
                # Show success message
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="BRENDA Login Successful"
                )
                info_dialog.format_secondary_text(
                    f"Logged in as: {email}\n\n"
                    "You can now fetch kinetic parameters from BRENDA."
                )
                info_dialog.run()
                info_dialog.destroy()
            else:
                self.brenda_authenticated = False
                self._update_brenda_ui_state()
                
                # Show error - likely 403 Forbidden (whitelist required)
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="BRENDA Authentication Failed"
                )
                error_dialog.format_secondary_text(
                    "Could not authenticate with BRENDA (likely 403 Forbidden).\n\n"
                    "BRENDA restricts SOAP API access for security.\n"
                    "You must request whitelist approval:\n\n"
                    "Email: info@brenda-enzymes.org\n"
                    "Subject: 'Request for SOAP API Whitelist Access'\n"
                    "Include: Your BRENDA email, research purpose, institution\n\n"
                    "Check the terminal/log output for detailed instructions."
                )
                error_dialog.run()
                error_dialog.destroy()
        
        except Exception as e:
            self.brenda_authenticated = False
            self._update_brenda_ui_state()
            
            error_msg = str(e)
            
            # Check if this is a 403 Forbidden error
            if "403" in error_msg or "Forbidden" in error_msg:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="BRENDA API Access Restricted (403 Forbidden)"
                )
                error_dialog.format_secondary_text(
                    "BRENDA has blocked automated API access for your account/IP.\n\n"
                    "This is normal - BRENDA requires whitelist approval for SOAP API access.\n\n"
                    "To get access:\n"
                    "• Email: info@brenda-enzymes.org\n"
                    "• Subject: 'Request for SOAP API Whitelist Access'\n"
                    "• Include your BRENDA email, research purpose, and institution\n\n"
                    "BRENDA support typically responds within 1-2 business days.\n"
                    "Periodic re-approval may be needed to maintain access.\n\n"
                    "Check the terminal output for detailed instructions."
                )
            else:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Login Error"
                )
                error_dialog.format_secondary_text(
                    f"An error occurred during login:\n\n{error_msg}\n\n"
                    "Check your internet connection and credentials."
                )
            
            error_dialog.run()
            error_dialog.destroy()
    
    def _on_brenda_logout_clicked(self, button):
        """Handle BRENDA logout button click."""
        self.brenda_client = None
        self.brenda_authenticated = False
        self._update_brenda_ui_state()
    
    def _on_brenda_fetch_clicked(self, button):
        """Handle BRENDA fetch button click with cache support."""
        # Get EC number and organism
        ec_entry = self.builder.get_object('brenda_ec_entry')
        organism_entry = self.builder.get_object('brenda_organism_entry')
        
        if not ec_entry:
            return
        
        ec_number = ec_entry.get_text().strip()
        if not ec_number:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="EC Number Required"
            )
            error_dialog.format_secondary_text(
                "Please enter an EC number to fetch kinetic parameters."
            )
            error_dialog.run()
            error_dialog.destroy()
            return
        
        organism = organism_entry.get_text().strip() if organism_entry else None
        
        # Show progress
        button.set_sensitive(False)
        button.set_label("Checking cache...")
        
        # Try cache first (works even without API access)
        km_stats = None
        kcat_stats = None
        ki_stats = None
        used_cache = False
        
        if self.brenda_cache_manager:
            try:
                km_stats = self.brenda_cache_manager.get_cached_result(
                    self.brenda_cache_manager.build_query_key(ec_number, 'Km', organism)
                )
                kcat_stats = self.brenda_cache_manager.get_cached_result(
                    self.brenda_cache_manager.build_query_key(ec_number, 'Kcat', organism)
                )
                ki_stats = self.brenda_cache_manager.get_cached_result(
                    self.brenda_cache_manager.build_query_key(ec_number, 'Ki', organism)
                )
                
                if km_stats or kcat_stats or ki_stats:
                    used_cache = True
                    import logging
                    logging.getLogger(self.__class__.__name__).info(
                        f"Using cached BRENDA data for EC {ec_number}"
                    )
            except Exception as e:
                import logging
                logging.getLogger(self.__class__.__name__).warning(f"Cache lookup failed: {e}")
        
        # Populate from cache if available
        if used_cache:
            if km_stats:
                k_m_entry = self.builder.get_object('k_m_entry')
                if k_m_entry:
                    k_m_entry.set_text(f"{km_stats['mean_value']:.6g}")
            
            if kcat_stats:
                k_cat_entry = self.builder.get_object('k_cat_entry')
                if k_cat_entry:
                    k_cat_entry.set_text(f"{kcat_stats['mean_value']:.6g}")
            
            if ki_stats:
                k_i_entry = self.builder.get_object('k_i_entry')
                if k_i_entry:
                    k_i_entry.set_text(f"{ki_stats['mean_value']:.6g}")
            
            # Show cache results
            button.set_sensitive(True)
            button.set_label("Fetch from BRENDA")
            
            info_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="✓ Using Cached BRENDA Data"
            )
            
            cache_info = "Using statistical mean values from cached BRENDA data:\n\n"
            if km_stats:
                cache_info += f"• K_m: {km_stats['mean_value']:.3f} (n={km_stats['count']} measurements)\n"
            if kcat_stats:
                cache_info += f"• k_cat: {kcat_stats['mean_value']:.3f} (n={kcat_stats['count']} measurements)\n"
            if ki_stats:
                cache_info += f"• K_i: {ki_stats['mean_value']:.3f} (n={ki_stats['count']} measurements)\n"
            
            # Add last updated timestamp if available
            if km_stats and 'last_updated' in km_stats:
                cache_info += f"\nCached: {km_stats['last_updated'][:10]}"  # Show date only
            
            cache_info += "\n\nNote: Using cached data - no API call needed."
            info_dialog.format_secondary_text(cache_info)
            info_dialog.run()
            info_dialog.destroy()
            return
        
        # Cache miss - query API if authenticated
        if not self.brenda_authenticated or not self.brenda_client:
            button.set_sensitive(True)
            button.set_label("Fetch from BRENDA")
            
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No Cached Data & Not Logged In"
            )
            error_dialog.format_secondary_text(
                f"No cached data found for EC {ec_number}.\n\n"
                "Please login to BRENDA to fetch fresh data from the API."
            )
            error_dialog.run()
            error_dialog.destroy()
            return
        
        button.set_label("Fetching from API...")
        
        try:
            # Fetch K_m values
            km_values = self.brenda_client.get_km_values(ec_number, organism=organism)
            
            # Fetch k_cat values
            kcat_values = self.brenda_client.get_kcat_values(ec_number, organism=organism)
            
            # Fetch K_i values
            ki_values = self.brenda_client.get_ki_values(ec_number, organism=organism)
            
            # Store results in cache for future use
            if self.brenda_cache_manager:
                try:
                    all_results = []
                    
                    # Convert API response to cache format
                    for km in km_values:
                        all_results.append({
                            'ec_number': ec_number,
                            'parameter_type': 'Km',
                            'value': km.get('value', 0.0),
                            'unit': km.get('unit', 'mM'),
                            'substrate': km.get('substrate', ''),
                            'organism': km.get('organism', organism or ''),
                            'literature': km.get('literature', ''),
                            'commentary': km.get('commentary', ''),
                            'quality': km.get('quality', 0.5)
                        })
                    
                    for kcat in kcat_values:
                        all_results.append({
                            'ec_number': ec_number,
                            'parameter_type': 'Kcat',
                            'value': kcat.get('value', 0.0),
                            'unit': kcat.get('unit', 's^-1'),
                            'substrate': kcat.get('substrate', ''),
                            'organism': kcat.get('organism', organism or ''),
                            'literature': kcat.get('literature', ''),
                            'commentary': kcat.get('commentary', ''),
                            'quality': kcat.get('quality', 0.5)
                        })
                    
                    for ki in ki_values:
                        all_results.append({
                            'ec_number': ec_number,
                            'parameter_type': 'Ki',
                            'value': ki.get('value', 0.0),
                            'unit': ki.get('unit', 'mM'),
                            'substrate': ki.get('substrate', ''),
                            'organism': ki.get('organism', organism or ''),
                            'literature': ki.get('literature', ''),
                            'commentary': ki.get('commentary', ''),
                            'quality': ki.get('quality', 0.5)
                        })
                    
                    # Store in cache
                    if all_results:
                        inserted = self.brenda_cache_manager.store_raw_data_batch(all_results)
                        import logging
                        logging.getLogger(self.__class__.__name__).info(
                            f"Cached {inserted} BRENDA results for EC {ec_number}"
                        )
                        
                        # Calculate statistics for future cache hits
                        from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
                        db = HeuristicDatabase()
                        if km_values:
                            db.calculate_brenda_statistics(ec_number, 'Km', organism)
                        if kcat_values:
                            db.calculate_brenda_statistics(ec_number, 'Kcat', organism)
                        if ki_values:
                            db.calculate_brenda_statistics(ec_number, 'Ki', organism)
                
                except Exception as e:
                    import logging
                    logging.getLogger(self.__class__.__name__).warning(
                        f"Failed to cache BRENDA results: {e}"
                    )
            
            # Populate fields with first result (user can refine with organism filter)
            if km_values and len(km_values) > 0:
                k_m_entry = self.builder.get_object('k_m_entry')
                if k_m_entry:
                    # Use first K_m value
                    k_m_entry.set_text(f"{km_values[0]['value']:.6g}")
            
            if kcat_values and len(kcat_values) > 0:
                k_cat_entry = self.builder.get_object('k_cat_entry')
                if k_cat_entry:
                    k_cat_entry.set_text(f"{kcat_values[0]['value']:.6g}")
            
            if ki_values and len(ki_values) > 0:
                k_i_entry = self.builder.get_object('k_i_entry')
                if k_i_entry:
                    k_i_entry.set_text(f"{ki_values[0]['value']:.6g}")
            
            # Show results summary
            total_results = len(km_values) + len(kcat_values) + len(ki_values)
            
            if total_results > 0:
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="↻ BRENDA Data Retrieved from API"
                )
                cache_note = ""
                if self.brenda_cache_manager:
                    cache_note = "\n\n✓ Results have been cached for future use."
                
                info_dialog.format_secondary_text(
                    f"Successfully fetched kinetic parameters:\n\n"
                    f"• K_m values: {len(km_values)}\n"
                    f"• k_cat values: {len(kcat_values)}\n"
                    f"• K_i values: {len(ki_values)}\n\n"
                    f"First values have been auto-filled. Refine with organism filter for specific data."
                    f"{cache_note}"
                )
                info_dialog.run()
                info_dialog.destroy()
            else:
                warning_dialog = Gtk.MessageDialog(
                    transient_for=self.dialog,
                    modal=True,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="No Data Found"
                )
                warning_dialog.format_secondary_text(
                    f"No kinetic parameters found for EC {ec_number}\n\n"
                    f"This may be because:\n"
                    f"• The EC number is invalid or obsolete\n"
                    f"• BRENDA has no data for this enzyme\n"
                    f"• The organism filter excluded all results"
                )
                warning_dialog.run()
                warning_dialog.destroy()
        
        except Exception as e:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Fetch Error"
            )
            error_dialog.format_secondary_text(
                f"An error occurred while fetching data:\n\n{str(e)}"
            )
            error_dialog.run()
            error_dialog.destroy()
        
        finally:
            # Restore button
            button.set_sensitive(True)
            button.set_label("Fetch from BRENDA")
    
    def _update_brenda_ui_state(self):
        """Update BRENDA UI widgets based on authentication state."""
        # Get widgets
        status_label = self.builder.get_object('brenda_status_label')
        login_button = self.builder.get_object('brenda_login_button')
        logout_button = self.builder.get_object('brenda_logout_button')
        fetch_button = self.builder.get_object('brenda_fetch_button')
        
        if self.brenda_authenticated:
            # Logged in state
            if status_label:
                email = self.brenda_client.credentials.email if self.brenda_client else "unknown"
                status_label.set_markup(f"<b>Status: Logged in</b> ({email})")
            
            if login_button:
                login_button.set_visible(False)
            
            if logout_button:
                logout_button.set_visible(True)
            
            if fetch_button:
                fetch_button.set_sensitive(True)
        else:
            # Logged out state
            if status_label:
                status_label.set_text("Status: Not logged in")
            
            if login_button:
                login_button.set_visible(True)
            
            if logout_button:
                logout_button.set_visible(False)
            
            if fetch_button:
                fetch_button.set_sensitive(False)
    
    def _save_kinetic_entry_fields(self):
        """Save kinetic parameters from manual entry fields to kinetic_metadata.
        
        Creates or updates ManualKineticMetadata with parameters from:
        - activation_energy
        - temperature_coefficient_Q10 (Q10)
        - k_cat
        - K_m
        - k_i
        - hill_coefficient
        
        Only saves non-empty fields. Creates ManualKineticMetadata if no 
        metadata exists, or updates existing metadata's parameters dict.
        """
        # Import ManualKineticMetadata here to avoid circular imports
        try:
            from shypn.data.kinetics.kinetic_metadata import ManualKineticMetadata
        except ImportError:
            # Kinetics module not available, skip
            return
        
        # Collect parameter values from entry widgets
        parameters_to_save = {}
        
        # Arrhenius parameters
        activation_energy_entry = self.builder.get_object('activation_energy_entry')
        if activation_energy_entry:
            value_text = activation_energy_entry.get_text().strip()
            if value_text:
                try:
                    value = float(value_text)
                    parameters_to_save['activation_energy'] = value
                except ValueError:
                    pass  # Invalid number, skip
        
        q10_entry = self.builder.get_object('q10_entry')
        if q10_entry:
            value_text = q10_entry.get_text().strip()
            if value_text:
                try:
                    value = float(value_text)
                    parameters_to_save['temperature_coefficient_Q10'] = value
                    parameters_to_save['Q10'] = value  # Save both keys for compatibility
                except ValueError:
                    pass
        
        # Michaelis-Menten parameters
        k_cat_entry = self.builder.get_object('k_cat_entry')
        if k_cat_entry:
            value_text = k_cat_entry.get_text().strip()
            if value_text:
                try:
                    value = float(value_text)
                    parameters_to_save['k_cat'] = value
                except ValueError:
                    pass
        
        k_m_entry = self.builder.get_object('k_m_entry')
        if k_m_entry:
            value_text = k_m_entry.get_text().strip()
            if value_text:
                try:
                    value = float(value_text)
                    parameters_to_save['K_m'] = value
                    parameters_to_save['Km'] = value  # Save both keys for compatibility
                except ValueError:
                    pass
        
        k_i_entry = self.builder.get_object('k_i_entry')
        if k_i_entry:
            value_text = k_i_entry.get_text().strip()
            if value_text:
                try:
                    value = float(value_text)
                    parameters_to_save['K_i'] = value
                    parameters_to_save['Ki'] = value  # Save both keys for compatibility
                except ValueError:
                    pass
        
        # Hill coefficient
        hill_entry = self.builder.get_object('hill_coefficient_entry')
        if hill_entry:
            value_text = hill_entry.get_text().strip()
            if value_text:
                try:
                    value = float(value_text)
                    parameters_to_save['hill_coefficient'] = value
                except ValueError:
                    pass
        
        # Only proceed if at least one parameter was entered
        if not parameters_to_save:
            return
        
        # Get or create kinetic_metadata
        if not hasattr(self.transition_obj, 'kinetic_metadata') or self.transition_obj.kinetic_metadata is None:
            # Create new ManualKineticMetadata
            self.transition_obj.kinetic_metadata = ManualKineticMetadata(
                rate_type='custom',
                formula='',
                parameters=parameters_to_save
            )
        else:
            # Update existing metadata
            # If it's not ManualKineticMetadata and not locked, convert it
            metadata = self.transition_obj.kinetic_metadata
            
            # Check if metadata should be preserved (SBML, locked, etc.)
            from shypn.data.kinetics.kinetic_metadata import KineticMetadata
            if KineticMetadata.should_preserve(metadata):
                # Don't overwrite - could warn user here
                print(f"Warning: Kinetic metadata for transition {self.transition_obj.id} is locked or from SBML. Manual edits not saved.")
                return
            
            # Safe to update - merge parameters
            if not hasattr(metadata, 'parameters') or metadata.parameters is None:
                metadata.parameters = {}
            
            metadata.parameters.update(parameters_to_save)
            
            # Mark as manually edited
            metadata.manually_edited = True
            
            # If metadata wasn't already manual, upgrade its confidence
            if metadata.source.value != 'manual':
                from shypn.data.kinetics.kinetic_metadata import KineticSource, ConfidenceLevel
                metadata.source = KineticSource.MANUAL
                metadata.confidence = ConfidenceLevel.HIGH
                metadata.confidence_score = 0.95
    
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
        self.locality_widget = None
        self.builder = None
        self.transition_obj = None
        self.parent_window = None
        self.persistency_manager = None
        self.model = None
        self.data_collector = None


# Factory function for backward compatibility
def create_transition_prop_dialog(transition_obj, parent_window=None, ui_dir=None,
                                   persistency_manager=None, model=None, data_collector=None):
    """Factory function to create a Transition properties dialog loader.
    
    Args:
        transition_obj: Transition object to edit properties for
        parent_window: Parent window for modal dialog
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/
        persistency_manager: NetObjPersistency instance for marking document dirty
        model: ModelCanvasManager instance for accessing Petri net structure
        data_collector: Optional SimulationDataCollector for runtime diagnostics
    
    Returns:
        TransitionPropDialogLoader: Configured dialog loader instance
    """
    return TransitionPropDialogLoader(
        transition_obj,
        parent_window=parent_window,
        ui_dir=ui_dir,
        persistency_manager=persistency_manager,
        model=model,
        data_collector=data_collector
    )
