"""
Transition Properties Dialog Loader

Loads and manages the Transition properties dialog UI.
"""

import os
import json
import ast
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from shypn.helpers.color_picker import setup_color_picker_in_dialog


class TransitionPropDialogLoader(GObject.GObject):
    """Loader for Transition properties dialog.
    
    This class loads and manages the Transition properties dialog from
    transition_prop_dialog.ui. The dialog allows editing Transition attributes
    such as name, label, and other properties.
    
    Signals:
        properties-changed: Emitted when properties are changed and applied
    """
    
    __gsignals__ = {
        'properties-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, transition_obj, parent_window=None, ui_dir: str = None, persistency_manager=None, model=None, data_collector=None):
        """Initialize the Transition properties dialog loader.
        
        Args:
            transition_obj: Transition object to edit properties for.
            parent_window: Parent window for modal dialog.
            ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
            persistency_manager: NetObjPersistency instance for marking document dirty
            model: ModelCanvasManager instance for accessing Petri net structure
            data_collector: Optional SimulationDataCollector for runtime diagnostics
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
        self.persistency_manager = persistency_manager
        self.model = model
        self.data_collector = data_collector
        
        # Widget references
        self.builder = None
        self.dialog = None
        self.color_picker = None
        self.locality_widget = None
        
        # Load UI
        self._load_ui()
        self._setup_color_picker()
        self._populate_fields()
        self._setup_locality_widget()
    
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
        
        # Wire OK and Cancel buttons
        ok_button = self.builder.get_object('ok_button')
        cancel_button = self.builder.get_object('cancel_button')
        
        if ok_button:
            ok_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.OK))
        if cancel_button:
            cancel_button.connect('clicked', lambda btn: self.dialog.response(Gtk.ResponseType.CANCEL))
        
        # Connect signals
        self.dialog.connect('response', self._on_response)
        
    
    def _setup_color_picker(self):
        """Setup color picker in the dialog."""
        # Get initial color (border_color for transitions)
        initial_color = getattr(self.transition_obj, 'border_color', (0.0, 0.0, 0.0))
        
        # Setup color picker using helper function
        self.color_picker = setup_color_picker_in_dialog(
            self.builder,
            'transition_color_picker',
            current_color=initial_color,
            button_size=28
        )
        
        # Connect to color selection signal if picker was created
        if self.color_picker:
            self.color_picker.connect('color-selected', self._on_color_selected)
    
    def _on_color_selected(self, picker, color_rgb):
        """Callback when color is selected.
        
        Args:
            picker: The ColorPickerRow widget
            color_rgb: Selected color as RGB tuple (0.0-1.0)
        """
    
    def _format_formula_for_display(self, formula):
        """Format formula value for display in UI TextView.
        
        Supports guard/rate formulas which can be:
            pass
        - None → empty string
        - dict → JSON formatted
        - number → string representation
        - expression string → as-is
        
        Args:
            formula: Can be None, dict, number, or string
        
        Returns:
            String representation for display
        """
        if formula is None:
            return ""
        elif isinstance(formula, dict):
            # Format dict as JSON for readability
            return json.dumps(formula, indent=2)
        elif isinstance(formula, (int, float)):
            return str(formula)
        else:
            # Already a string (expression)
            return str(formula)
    
    def _parse_formula(self, text):
        """Parse formula text from UI into appropriate format.
        
        Supports multiple formats:
            pass
        - Empty string → None
        - Number string → numeric value
        - Dictionary string → parsed dict
        - Expression string → kept as string
        
        Args:
            text: Raw text from TextView
        
        Returns:
            Parsed value (None, number, dict, or string)
        """
        text = text.strip()
        
        if not text:
            return None
        
        # Try to parse as number first
        try:
            # Try integer
            if '.' not in text:
                return int(text)
            # Try float
            return float(text)
        except ValueError:
            pass
        
        # Try to parse as dict (JSON or Python dict literal)
        if text.startswith('{') and text.endswith('}'):
            try:
                # Try ast.literal_eval for Python dict syntax
                return ast.literal_eval(text)
            except (ValueError, SyntaxError):
                try:
                    # Try JSON parsing
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass
        
        # Return as string (expression)
        return text
    
    def _populate_fields(self):
        """Populate dialog fields with current Transition properties."""
        # Get widget references
        
        # Name field (read-only system-assigned identifier)
        name_entry = self.builder.get_object('name_entry')
        if name_entry and hasattr(self.transition_obj, 'name'):
            name_entry.set_text(str(self.transition_obj.name))
            name_entry.set_editable(False)  # Read-only
        
        # Label field (optional user-editable text)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            label_entry.set_text(str(self.transition_obj.label) if self.transition_obj.label else '')
        
        # Transition type combo box
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            transition_type = self.transition_obj.transition_type if self.transition_obj.transition_type else 'continuous'
            # Map type to combo index: immediate=0, timed=1, stochastic=2, continuous=3
            type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3}
            index = type_map.get(transition_type, 3)  # Default to continuous
            type_combo.set_active(index)
        
        # Priority spin button
        priority_spin = self.builder.get_object('priority_spin')
        if priority_spin and hasattr(self.transition_obj, 'priority'):
            priority_spin.set_value(float(self.transition_obj.priority))
        
        # Firing policy combo box
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo and hasattr(self.transition_obj, 'firing_policy'):
            # Map policy to combo index: earliest=0, latest=1
            policy_map = {'earliest': 0, 'latest': 1}
            policy = self.transition_obj.firing_policy
            index = policy_map.get(policy, 0)  # Default to earliest
            firing_policy_combo.set_active(index)
        
        # Source checkbox
        is_source_check = self.builder.get_object('is_source_check')
        if is_source_check and hasattr(self.transition_obj, 'is_source'):
            is_source_check.set_active(self.transition_obj.is_source)
        
        # Sink checkbox
        is_sink_check = self.builder.get_object('is_sink_check')
        if is_sink_check and hasattr(self.transition_obj, 'is_sink'):
            is_sink_check.set_active(self.transition_obj.is_sink)
        
        # Rate entry (simple numeric/expression field)
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry and hasattr(self.transition_obj, 'rate'):
            # For continuous transitions, try to load from properties['rate_function'] first
            rate_value = self.transition_obj.rate
            if self.transition_obj.transition_type == 'continuous':
                if hasattr(self.transition_obj, 'properties') and self.transition_obj.properties:
                    rate_func = self.transition_obj.properties.get('rate_function')
                    if rate_func:
                        rate_value = rate_func
            
            rate_text = self._format_formula_for_display(rate_value)
            rate_entry.set_text(rate_text)
        
        # Guard function (TextView) - format as JSON if dict
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            
            # Try to load from properties['guard_function'] first if it exists
            guard_value = self.transition_obj.guard
            if hasattr(self.transition_obj, 'properties') and self.transition_obj.properties:
                guard_func = self.transition_obj.properties.get('guard_function')
                if guard_func is not None:
                    guard_value = guard_func
            
            guard_text = self._format_formula_for_display(guard_value)
            buffer.set_text(guard_text)
        
        # Rate function (TextView) - format as JSON if dict
        rate_textview = self.builder.get_object('rate_textview')
        if rate_textview and hasattr(self.transition_obj, 'rate'):
            buffer = rate_textview.get_buffer()
            
            # For continuous transitions, try to load from properties['rate_function'] first
            rate_value = self.transition_obj.rate
            if self.transition_obj.transition_type == 'continuous':
                if hasattr(self.transition_obj, 'properties') and self.transition_obj.properties:
                    rate_func = self.transition_obj.properties.get('rate_function')
                    if rate_func:
                        rate_value = rate_func
            
            rate_text = self._format_formula_for_display(rate_value)
            buffer.set_text(rate_text)
    
    def _setup_locality_widget(self):
        """Setup locality information widget in diagnostics tab."""
        # Get locality container from UI file
        locality_container = self.builder.get_object('locality_info_container')
        
        if locality_container and self.model:
            # Clear existing children
            for child in locality_container.get_children():
                locality_container.remove(child)
            
            # Import locality widget
            from shypn.diagnostic import LocalityInfoWidget
            
            # Create and add locality widget
            self.locality_widget = LocalityInfoWidget(self.model)
            self.locality_widget.set_transition(self.transition_obj)
            
            # Wire data collector for runtime diagnostics if available
            if self.data_collector:
                self.locality_widget.set_data_collector(self.data_collector)
            
            locality_container.pack_start(self.locality_widget, True, True, 0)
            locality_container.show_all()
            
        elif not locality_container:
            pass
        elif not self.model:
    
            pass
    def _on_response(self, dialog, response_id):
        """Handle dialog response (OK/Cancel).
        
        Args:
            dialog: The dialog widget.
            response_id: Response ID (OK, Cancel, etc.)
        """
        if response_id == Gtk.ResponseType.OK:
            self._apply_changes()
            
            # Mark document as dirty if persistency manager is available
            if self.persistency_manager:
                self.persistency_manager.mark_dirty()
            
            # Emit signal to notify observers (for canvas redraw)
            self.emit('properties-changed')
        
        dialog.destroy()
    
    def _apply_changes(self):
        """Apply changes from dialog fields to Transition object."""
        # Name field is read-only (immutable), so we skip it
        
        # Label field (optional user-editable text)
        label_entry = self.builder.get_object('transition_label_entry')
        if label_entry and hasattr(self.transition_obj, 'label'):
            new_label = label_entry.get_text().strip()
            self.transition_obj.label = new_label if new_label else None
        
        # Transition type combo box
        type_combo = self.builder.get_object('prop_transition_type_combo')
        if type_combo and hasattr(self.transition_obj, 'transition_type'):
            type_index = type_combo.get_active()
            # Map index to type: 0=immediate, 1=timed, 2=stochastic, 3=continuous
            type_list = ['immediate', 'timed', 'stochastic', 'continuous']
            if 0 <= type_index < len(type_list):
                old_type = self.transition_obj.transition_type
                self.transition_obj.transition_type = type_list[type_index]
        
        # Priority spin button
        priority_spin = self.builder.get_object('priority_spin')
        if priority_spin and hasattr(self.transition_obj, 'priority'):
            old_priority = self.transition_obj.priority
            self.transition_obj.priority = int(priority_spin.get_value())
        
        # Firing policy combo box
        firing_policy_combo = self.builder.get_object('firing_policy_combo')
        if firing_policy_combo and hasattr(self.transition_obj, 'firing_policy'):
            # Map index to policy: 0=earliest, 1=latest
            policy_list = ['earliest', 'latest']
            policy_index = firing_policy_combo.get_active()
            if policy_index >= 0:
                self.transition_obj.firing_policy = policy_list[policy_index]
        
        # Source checkbox
        is_source_check = self.builder.get_object('is_source_check')
        if is_source_check and hasattr(self.transition_obj, 'is_source'):
            self.transition_obj.is_source = is_source_check.get_active()
        
        # Sink checkbox
        is_sink_check = self.builder.get_object('is_sink_check')
        if is_sink_check and hasattr(self.transition_obj, 'is_sink'):
            self.transition_obj.is_sink = is_sink_check.get_active()
        
        # Rate entry (simple value - takes precedence over rate_textview if both exist)
        rate_entry = self.builder.get_object('rate_entry')
        if rate_entry and hasattr(self.transition_obj, 'rate'):
            rate_text = rate_entry.get_text().strip()
            if rate_text:  # Only update if entry has content
                old_rate = self.transition_obj.rate
                parsed_rate = self._parse_formula(rate_text)
                self.transition_obj.rate = parsed_rate
                
                # CRITICAL: For continuous transitions, also store in properties['rate_function']
                # This is what ContinuousBehavior reads!
                if self.transition_obj.transition_type == 'continuous':
                    if not hasattr(self.transition_obj, 'properties') or self.transition_obj.properties is None:
                        self.transition_obj.properties = {}
                    # Store the string expression for continuous behavior
                    self.transition_obj.properties['rate_function'] = rate_text
                
        
        # Guard function (TextView) - parse with formula parser
        guard_textview = self.builder.get_object('guard_textview')
        if guard_textview and hasattr(self.transition_obj, 'guard'):
            buffer = guard_textview.get_buffer()
            start, end = buffer.get_bounds()
            guard_text = buffer.get_text(start, end, True)
            old_guard = self.transition_obj.guard
            parsed_guard = self._parse_formula(guard_text)
            self.transition_obj.guard = parsed_guard
            
            # Store in properties['guard_function'] for evaluation
            if not hasattr(self.transition_obj, 'properties') or self.transition_obj.properties is None:
                self.transition_obj.properties = {}
            # Store the string expression for dynamic evaluation
            self.transition_obj.properties['guard_function'] = guard_text
            
        
        # Rate function (TextView) - parse with formula parser (only if rate_entry is empty)
        rate_textview = self.builder.get_object('rate_textview')
        rate_entry = self.builder.get_object('rate_entry')
        # Only use TextView if entry doesn't have content
        if rate_textview and hasattr(self.transition_obj, 'rate'):
            rate_entry_text = rate_entry.get_text().strip() if rate_entry else ""
            if not rate_entry_text:  # Entry is empty, use TextView
                buffer = rate_textview.get_buffer()
                start, end = buffer.get_bounds()
                rate_text = buffer.get_text(start, end, True)
                old_rate = self.transition_obj.rate
                parsed_rate = self._parse_formula(rate_text)
                self.transition_obj.rate = parsed_rate
                
                # CRITICAL: For continuous transitions, also store in properties['rate_function']
                if self.transition_obj.transition_type == 'continuous':
                    if not hasattr(self.transition_obj, 'properties') or self.transition_obj.properties is None:
                        self.transition_obj.properties = {}
                    # Store the string expression for continuous behavior
                    self.transition_obj.properties['rate_function'] = rate_text.strip()
                
        
        # Color from color picker
        if self.color_picker and hasattr(self.transition_obj, 'border_color'):
            old_color = self.transition_obj.border_color
            selected_color = self.color_picker.get_selected_color()
            self.transition_obj.border_color = selected_color
        
        # Also update fill_color to match border_color for consistency
        if self.color_picker and hasattr(self.transition_obj, 'fill_color'):
            self.transition_obj.fill_color = self.transition_obj.border_color
        
    
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
def create_transition_prop_dialog(transition_obj, parent_window=None, ui_dir: str = None, persistency_manager=None, model=None, data_collector=None):
    """Factory function to create a Transition properties dialog loader.
    
    Args:
        transition_obj: Transition object to edit properties for.
        parent_window: Parent window for modal dialog.
        ui_dir: Directory containing UI files. Defaults to project ui/dialogs/.
        persistency_manager: NetObjPersistency instance for marking document dirty
        model: ModelCanvasManager instance for accessing Petri net structure
        data_collector: Optional SimulationDataCollector for runtime diagnostics
    
    Returns:
        TransitionPropDialogLoader: Configured dialog loader instance.
    """
    return TransitionPropDialogLoader(transition_obj, parent_window=parent_window, ui_dir=ui_dir, persistency_manager=persistency_manager, model=model, data_collector=data_collector)
