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
        self.topology_loader = None
        
        # Load and setup
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._update_field_visibility()
        self._setup_type_change_handler()
        self._setup_rate_sync()
        self._setup_topology_tab()
        self._setup_kinetics_tab()
    
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
        # Name (read-only system identifier)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            name_entry.set_text(str(self.transition_obj.name))
            name_entry.set_editable(False)
            name_entry.set_can_focus(False)
        
        # Label (user-editable)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            label_entry.set_text(
                str(self.transition_obj.label) if self.transition_obj.label else ''
            )
        
        # Transition type
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3}
            transition_type = self.transition_obj.transition_type or 'continuous'
            type_combo.set_active(type_map.get(transition_type, 3))
        
        # Firing policy (replaces priority spinner)
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo and hasattr(self.transition_obj, 'firing_policy'):
            # Map policy names to combobox indices (order: Random, Earliest, Latest, Priority, Race, Age, Preemptive-Priority)
            policy_map = {
                'random': 0,
                'earliest': 1,
                'latest': 2,
                'priority': 3,
                'race': 4,
                'age': 5,
                'preemptive-priority': 6
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
        
        # Directional rates (for reversible reactions) - use rate_textview as forward, add reverse field
        rate_textview = self.builder.get_object('rate_textview')
        rate_reverse_textview = self.builder.get_object('rate_reverse_textview')
        reversible_check = self.builder.get_object('reversible_check')
        
        has_directional = False
        if rate_textview and rate_reverse_textview:
            # Check if transition has directional rates
            rate_fwd = getattr(self.transition_obj, 'rate_forward', None)
            rate_rev = getattr(self.transition_obj, 'rate_reverse', None)
            
            if rate_fwd or rate_rev:
                has_directional = True
                # Forward rate goes in the main rate_textview
                if rate_fwd and rate_textview:
                    buffer_fwd = rate_textview.get_buffer()
                    buffer_fwd.set_text(str(rate_fwd))
                # Reverse rate goes in the reverse field
                if rate_rev:
                    buffer_rev = rate_reverse_textview.get_buffer()
                    buffer_rev.set_text(str(rate_rev))
        
        # Set reversible checkbox state
        if reversible_check:
            reversible_check.set_active(has_directional)
            # Connect signal to toggle visibility of reverse rate field
            reversible_check.connect('toggled', self._on_reversible_toggled)
        
        # Update visibility of reverse rate field
        self._update_reversible_fields_visibility()
        
        # Guard function (TextView)
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            guard_value = self.transition_obj.guard
            if guard_value is not None:
                buffer.set_text(str(guard_value))
        
        # Rate function (TextView) - check multiple sources
        rate_textview = self.builder.get_object('rate_textview')
        if rate_textview:
            buffer = rate_textview.get_buffer()
            rate_func = None
            
            # Priority 1: Check properties['rate_function_display'] (SBML biological names for UI)
            if hasattr(self.transition_obj, 'properties') and 'rate_function_display' in self.transition_obj.properties:
                rate_func = self.transition_obj.properties['rate_function_display']
            
            # Priority 2: Check transition.properties['rate_function'] (SBML formulas stored here)
            elif hasattr(self.transition_obj, 'properties') and 'rate_function' in self.transition_obj.properties:
                rate_func = self.transition_obj.properties['rate_function']
            
            # Priority 3: Check kinetic_metadata.formula (backup for SBML)
            elif hasattr(self.transition_obj, 'kinetic_metadata') and self.transition_obj.kinetic_metadata:
                if hasattr(self.transition_obj.kinetic_metadata, 'formula'):
                    rate_func = self.transition_obj.kinetic_metadata.formula
            
            # Priority 4: Fall back to simple rate value
            elif hasattr(self.transition_obj, 'rate') and self.transition_obj.rate is not None:
                rate_func = str(self.transition_obj.rate)
            
            # Set the text if we found something
            if rate_func is not None:
                buffer.set_text(str(rate_func))
        
        # Line Width
        width_entry = self.builder.get_object('prop_transition_width_entry')
        if width_entry and hasattr(self.transition_obj, 'border_width'):
            width_entry.set_text(str(self.transition_obj.border_width))
        
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
        rate_textview = self.builder.get_object('rate_textview')
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
    
    def _setup_type_change_handler(self):
        """Setup handler for transition type changes."""
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo:
            type_combo.connect('changed', self._on_type_changed)
    
    def _on_type_changed(self, combo):
        """Handle transition type change - update field visibility."""
        type_list = ['immediate', 'timed', 'stochastic', 'continuous']
        new_type = type_list[combo.get_active()]
        
        # Update transition object temporarily (not persisted until OK)
        self.transition_obj.transition_type = new_type
        
        # Update UI
        self._update_field_visibility()
        self._update_type_description()
    
    def _setup_rate_sync(self):
        """Setup synchronization between rate function TextView and rate entry."""
        rate_textview = self.builder.get_object('rate_textview')
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
        
        Returns:
            bool: True if successful, False if validation failed
        """
        try:
            # Label
            label_entry = self.builder.get_object('transition_label_entry')
            if label_entry:
                new_label = label_entry.get_text().strip()
                self.transition_obj.label = new_label if new_label else None
            
            # Transition type
            type_combo = self.builder.get_object('prop_transition_type_combo')
            if type_combo:
                type_list = ['immediate', 'timed', 'stochastic', 'continuous']
                self.transition_obj.transition_type = type_list[type_combo.get_active()]
            
            # Firing policy (replaces priority spinner)
            firing_policy_combo = self.builder.get_object('firing_policy_combo')
            if firing_policy_combo:
                # Policy list order matches combobox: Random, Earliest, Latest, Priority, Race, Age, Preemptive-Priority
                policy_list = [
                    'random',
                    'earliest',
                    'latest',
                    'priority',
                    'race',
                    'age',
                    'preemptive-priority'
                ]
                policy_index = firing_policy_combo.get_active()
                if policy_index >= 0:
                    self.transition_obj.firing_policy = policy_list[policy_index]
            
            # Priority value (numeric)
            priority_value_spin = self.builder.get_object('priority_value_spin')
            if priority_value_spin:
                self.transition_obj.priority = int(priority_value_spin.get_value())
            
            # Source/Sink
            is_source_check = self.builder.get_object('is_source_check')
            if is_source_check:
                self.transition_obj.is_source = is_source_check.get_active()
            
            is_sink_check = self.builder.get_object('is_sink_check')
            if is_sink_check:
                self.transition_obj.is_sink = is_sink_check.get_active()
            
            # Rate function - validate and save to both rate and properties['rate_function']
            rate_textview = self.builder.get_object('rate_textview')
            reversible_check = self.builder.get_object('reversible_check')
            
            # Check if using directional rates
            if reversible_check and reversible_check.get_active():
                # Save directional rates: rate_textview is forward, rate_reverse_textview is reverse
                rate_textview = self.builder.get_object('rate_textview')
                rate_reverse_textview = self.builder.get_object('rate_reverse_textview')
                
                # Forward rate from main rate field
                if rate_textview:
                    buffer = rate_textview.get_buffer()
                    start, end = buffer.get_bounds()
                    rate_fwd_text = buffer.get_text(start, end, True).strip()
                    if rate_fwd_text:
                        # Validate
                        is_valid, error_msg = self._validate_rate_function_runtime(rate_fwd_text)
                        if not is_valid:
                            self._show_error_dialog("Invalid Forward Rate", error_msg)
                            return False
                        self.transition_obj.rate_forward = rate_fwd_text
                    else:
                        if hasattr(self.transition_obj, 'rate_forward'):
                            delattr(self.transition_obj, 'rate_forward')
                
                # Reverse rate from reverse field
                if rate_reverse_textview:
                    buffer = rate_reverse_textview.get_buffer()
                    start, end = buffer.get_bounds()
                    rate_rev_text = buffer.get_text(start, end, True).strip()
                    if rate_rev_text:
                        # Validate
                        is_valid, error_msg = self._validate_rate_function_runtime(rate_rev_text)
                        if not is_valid:
                            self._show_error_dialog("Invalid Reverse Rate", error_msg)
                            return False
                        self.transition_obj.rate_reverse = rate_rev_text
                    else:
                        if hasattr(self.transition_obj, 'rate_reverse'):
                            delattr(self.transition_obj, 'rate_reverse')
                
                # Clear regular rate and properties when using directional
                self.transition_obj.set_rate(None)
                if hasattr(self.transition_obj, 'properties'):
                    if 'rate_function' in self.transition_obj.properties:
                        del self.transition_obj.properties['rate_function']
                    if 'rate_function_display' in self.transition_obj.properties:
                        del self.transition_obj.properties['rate_function_display']
            
            elif rate_textview:
                # Use regular rate function
                # Clear directional rates
                if hasattr(self.transition_obj, 'rate_forward'):
                    delattr(self.transition_obj, 'rate_forward')
                if hasattr(self.transition_obj, 'rate_reverse'):
                    delattr(self.transition_obj, 'rate_reverse')
                
                buffer = rate_textview.get_buffer()
                start, end = buffer.get_bounds()
                rate_text = buffer.get_text(start, end, True).strip()
                
                if rate_text:
                    # Comprehensive validation (syntax + runtime)
                    is_valid, error_msg = self._validate_rate_function_runtime(rate_text)
                    
                    if not is_valid:
                        self._show_error_dialog("Invalid Rate Function", error_msg)
                        return False  # Validation failed, don't apply changes
                    
                    # Save to properties for complex expressions/formulas
                    if not hasattr(self.transition_obj, 'properties'):
                        self.transition_obj.properties = {}
                    
                    # If user edited a formula, it's now considered manual input
                    # Store as both display and computational versions
                    self.transition_obj.properties['rate_function_display'] = rate_text
                    self.transition_obj.properties['rate_function'] = rate_text
                    
                    # Note: For manual edits, user must use P1, P2, P3 notation for simulation
                    # or keep biological names if they want display-only
                    
                    # Also try to set rate (for simple numeric values)
                    self.transition_obj.set_rate(rate_text)
                else:
                    # Clear rate_function if empty
                    if hasattr(self.transition_obj, 'properties'):
                        if 'rate_function' in self.transition_obj.properties:
                            del self.transition_obj.properties['rate_function']
                        if 'rate_function_display' in self.transition_obj.properties:
                            del self.transition_obj.properties['rate_function_display']
                    self.transition_obj.set_rate(None)
            
            # Guard - validate and apply
            guard_textview = self.builder.get_object('guard_textview')
            if guard_textview:
                buffer = guard_textview.get_buffer()
                start, end = buffer.get_bounds()
                guard_text = buffer.get_text(start, end, True).strip()
                
                if guard_text:
                    # Validate the guard expression before applying (same validation as rate)
                    is_valid, error_msg = self._validate_rate_function_runtime(guard_text)
                    
                    if not is_valid:
                        # Show error dialog and refuse to apply
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
                        return False  # Validation failed, don't apply changes
                
                self.transition_obj.set_guard(guard_text if guard_text else None)
            
            # Color from picker
            if self.color_picker:
                selected_color = self.color_picker.get_selected_color()
                self.transition_obj.border_color = selected_color
                self.transition_obj.fill_color = selected_color
            
            # Line Width
            width_entry = self.builder.get_object('prop_transition_width_entry')
            if width_entry and hasattr(self.transition_obj, 'border_width'):
                try:
                    width_text = width_entry.get_text().strip()
                    if width_text:
                        width_value = float(width_text)
                        self.transition_obj.border_width = max(0.5, width_value)
                except ValueError:
                    pass  # Keep current value if invalid
            
            return True
            
        except ValueError as e:
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.dialog,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Validation Error"
            )
            error_dialog.format_secondary_text(str(e))
            error_dialog.run()
            error_dialog.destroy()
            return False
    
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
    
    def _setup_topology_tab(self):
        """Setup topology information tab using TransitionTopologyTabLoader.
        
        Loads the topology tab from XML and populates it with analysis
        for this transition (if model is available).
        """
        # Skip if no model available
        if not self.model:
            return
        
        try:
            from shypn.ui.topology_tab_loader import TransitionTopologyTabLoader
            
            # Create topology tab loader with parent_window for Wayland compatibility
            self.topology_loader = TransitionTopologyTabLoader(
                model=self.model,
                element_id=self.transition_obj.id,
                parent_window=self.parent_window  # Pass parent for dialog creation
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
                if hasattr(self.topology_loader, 'cycles_label'):
                    self.topology_loader.cycles_label.set_markup(
                        "<i>Topology analysis available.\n"
                        "Click 'Analyze' button to run analysis.</i>"
                    )
        
        except ImportError:
            # Topology module not available - silently skip
            pass
        except Exception:
            # Any other error - log but don't crash the dialog
            pass
    
    def _setup_kinetics_tab(self):
        """Setup kinetics tab to display kinetic metadata and parameters.
        
        Populates the kinetics tab with:
        - Source information (SBML, BRENDA, SABIO-RK, Heuristic, etc.)
        - Confidence level
        - Rate type (michaelis_menten, mass_action, etc.)
        - Parameters table (name, value, source)
        """
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
