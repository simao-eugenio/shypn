#!/usr/bin/env python3
"""Parameter Sweep Builder - UI for configuring batch parameter exploration.

Allows users to define parameter ranges for automated testing:
- Select parameter type (Place Markings, Transition Rates, Arc Weights)
- Choose specific parameter to vary
- Define range specification (Linear, List, Percentage)
- Preview experiment count before generation

Author: Simão Eugénio
Date: December 7, 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class ParameterSweepBuilder(Gtk.Box):
    """Widget for configuring parameter sweeps.
    
    Features:
    - Parameter type and name selection
    - Three range specification modes
    - Preview of experiment count
    - Generate button to create snapshots
    """
    
    def __init__(self):
        """Initialize parameter sweep builder."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # State
        self.parameter_type = 'places'  # Default: 'places', 'transitions', 'arcs'
        self.parameter_name = None
        self.parameter_values = []
        self._param_name_to_id = {}  # Mapping for name to ID resolution
        
        # Callbacks
        self.on_generate_callback = None
        self.on_clear_callback = None
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build parameter sweep configuration UI."""
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Parameter Sweep Configuration</b>")
        title_label.set_xalign(0)
        self.pack_start(title_label, False, False, 0)
        
        # === PARAMETER SELECTION ===
        selection_frame = Gtk.Frame()
        selection_frame.set_label("Parameter Selection")
        selection_frame.set_margin_top(6)
        
        selection_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        selection_box.set_margin_start(12)
        selection_box.set_margin_end(12)
        selection_box.set_margin_top(6)
        selection_box.set_margin_bottom(6)
        
        # Parameter Type
        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        type_label = Gtk.Label(label="Type:")
        type_label.set_size_request(100, -1)
        type_label.set_xalign(0)
        type_box.pack_start(type_label, False, False, 0)
        
        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append("places", "Place Markings")
        self.type_combo.append("transitions", "Transition Rates")
        self.type_combo.append("arcs", "Arc Weights")
        self.type_combo.set_active(0)
        self.type_combo.connect("changed", self._on_type_changed)
        type_box.pack_start(self.type_combo, True, True, 0)
        
        selection_box.pack_start(type_box, False, False, 0)
        
        # Parameter Name
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_label = Gtk.Label(label="Parameter:")
        name_label.set_size_request(100, -1)
        name_label.set_xalign(0)
        name_box.pack_start(name_label, False, False, 0)
        
        self.name_combo = Gtk.ComboBoxText()
        self.name_combo.set_tooltip_text("Load a model with subnet parameters to see available parameters")
        name_box.pack_start(self.name_combo, True, True, 0)
        
        selection_box.pack_start(name_box, False, False, 0)
        
        selection_frame.add(selection_box)
        self.pack_start(selection_frame, False, False, 0)
        
        # === RANGE SPECIFICATION ===
        range_frame = Gtk.Frame()
        range_frame.set_label("Range Specification")
        range_frame.set_margin_top(6)
        
        range_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        range_box.set_margin_start(12)
        range_box.set_margin_end(12)
        range_box.set_margin_top(6)
        range_box.set_margin_bottom(6)
        
        # Radio buttons for range type
        self.linear_radio = Gtk.RadioButton(label="Linear Range")
        range_box.pack_start(self.linear_radio, False, False, 0)
        
        # Linear range inputs
        linear_grid = Gtk.Grid()
        linear_grid.set_column_spacing(6)
        linear_grid.set_row_spacing(6)
        linear_grid.set_margin_start(24)
        
        linear_grid.attach(Gtk.Label(label="Start:", xalign=0), 0, 0, 1, 1)
        self.start_entry = Gtk.Entry()
        self.start_entry.set_text("0.1")
        self.start_entry.set_width_chars(10)
        linear_grid.attach(self.start_entry, 1, 0, 1, 1)
        
        linear_grid.attach(Gtk.Label(label="Stop:", xalign=0), 2, 0, 1, 1)
        self.stop_entry = Gtk.Entry()
        self.stop_entry.set_text("1.0")
        self.stop_entry.set_width_chars(10)
        linear_grid.attach(self.stop_entry, 3, 0, 1, 1)
        
        linear_grid.attach(Gtk.Label(label="Step:", xalign=0), 4, 0, 1, 1)
        self.step_entry = Gtk.Entry()
        self.step_entry.set_text("0.1")
        self.step_entry.set_width_chars(10)
        linear_grid.attach(self.step_entry, 5, 0, 1, 1)
        
        range_box.pack_start(linear_grid, False, False, 0)
        
        # List values radio
        self.list_radio = Gtk.RadioButton(group=self.linear_radio, label="Value List")
        range_box.pack_start(self.list_radio, False, False, 0)
        
        # List values input
        list_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        list_box.set_margin_start(24)
        self.list_entry = Gtk.Entry()
        self.list_entry.set_placeholder_text("e.g., 0.1, 0.5, 1.0, 2.0")
        list_box.pack_start(self.list_entry, True, True, 0)
        range_box.pack_start(list_box, False, False, 0)
        
        # Percentage variation radio
        self.percent_radio = Gtk.RadioButton(group=self.linear_radio, label="Percentage Variation")
        range_box.pack_start(self.percent_radio, False, False, 0)
        
        # Percentage inputs
        percent_grid = Gtk.Grid()
        percent_grid.set_column_spacing(6)
        percent_grid.set_row_spacing(6)
        percent_grid.set_margin_start(24)
        
        percent_grid.attach(Gtk.Label(label="Baseline ±", xalign=0), 0, 0, 1, 1)
        self.percent_entry = Gtk.Entry()
        self.percent_entry.set_text("20")
        self.percent_entry.set_width_chars(6)
        percent_grid.attach(self.percent_entry, 1, 0, 1, 1)
        
        percent_grid.attach(Gtk.Label(label="% (", xalign=0), 2, 0, 1, 1)
        self.percent_steps_entry = Gtk.Entry()
        self.percent_steps_entry.set_text("5")
        self.percent_steps_entry.set_width_chars(4)
        percent_grid.attach(self.percent_steps_entry, 3, 0, 1, 1)
        
        percent_grid.attach(Gtk.Label(label="steps )", xalign=0), 4, 0, 1, 1)
        
        range_box.pack_start(percent_grid, False, False, 0)
        
        range_frame.add(range_box)
        self.pack_start(range_frame, False, False, 0)
        
        # === SIMULATION SETTINGS ===
        sim_frame = Gtk.Frame()
        sim_frame.set_label("Simulation Settings")
        sim_frame.set_margin_top(6)
        
        sim_box = Gtk.Grid()
        sim_box.set_column_spacing(6)
        sim_box.set_row_spacing(6)
        sim_box.set_margin_start(12)
        sim_box.set_margin_end(12)
        sim_box.set_margin_top(6)
        sim_box.set_margin_bottom(6)
        
        sim_box.attach(Gtk.Label(label="Replicates:", xalign=0), 0, 0, 1, 1)
        self.replicates_entry = Gtk.Entry()
        self.replicates_entry.set_text("500")
        self.replicates_entry.set_width_chars(8)
        sim_box.attach(self.replicates_entry, 1, 0, 1, 1)
        
        sim_box.attach(Gtk.Label(label="Duration:", xalign=0), 2, 0, 1, 1)
        self.duration_entry = Gtk.Entry()
        self.duration_entry.set_text("100.0")
        self.duration_entry.set_width_chars(8)
        self.duration_entry.set_tooltip_text("Maximum simulation time (can stop earlier if condition met)")
        sim_box.attach(self.duration_entry, 3, 0, 1, 1)
        
        # Termination condition
        sim_box.attach(Gtk.Label(label="Stop condition:", xalign=0), 0, 1, 1, 1)
        self.termination_combo = Gtk.ComboBoxText()
        self.termination_combo.append("time_only", "Time limit only")
        self.termination_combo.append("deadlock", "Deadlock or time limit")
        self.termination_combo.append("steady_state", "Steady state or time limit")
        self.termination_combo.set_active_id("deadlock")
        self.termination_combo.set_tooltip_text("When to stop the simulation")
        sim_box.attach(self.termination_combo, 1, 1, 3, 1)
        
        sim_frame.add(sim_box)
        self.pack_start(sim_frame, False, False, 0)
        
        # === PREVIEW AND ACTIONS ===
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_margin_top(6)
        
        # Preview button
        preview_button = Gtk.Button(label="Preview")
        preview_button.connect("clicked", self._on_preview_clicked)
        action_box.pack_start(preview_button, False, False, 0)
        
        # Preview label
        self.preview_label = Gtk.Label()
        self.preview_label.set_markup("<i>Configure parameters and click Preview</i>")
        self.preview_label.set_xalign(0)
        action_box.pack_start(self.preview_label, True, True, 0)
        
        # Generate button
        self.generate_button = Gtk.Button(label="Generate Experiments")
        self.generate_button.set_sensitive(False)
        self.generate_button.connect("clicked", self._on_generate_clicked)
        action_box.pack_end(self.generate_button, False, False, 0)
        
        # Clear button
        clear_button = Gtk.Button(label="Clear")
        clear_button.connect("clicked", self._on_clear_clicked)
        action_box.pack_end(clear_button, False, False, 0)
        
        self.pack_start(action_box, False, False, 0)
    
    def _on_type_changed(self, combo):
        """Handle parameter type change."""
        self.parameter_type = combo.get_active_id()
        # Note: Parameter list will be populated by category's refresh_parameters()
        # when it detects the type change
    
    def _on_preview_clicked(self, button):
        """Preview experiment count based on current configuration."""
        try:
            values = self._compute_parameter_values()
            count = len(values)
            
            if count > 0:
                self.preview_label.set_markup(
                    f"<b>Preview:</b> {count} experiments will be generated"
                )
                self.generate_button.set_sensitive(True)
            else:
                self.preview_label.set_markup(
                    "<span foreground='red'>Error: No valid parameter values</span>"
                )
                self.generate_button.set_sensitive(False)
                
        except Exception as e:
            self.preview_label.set_markup(
                f"<span foreground='red'>Error: {str(e)}</span>"
            )
            self.generate_button.set_sensitive(False)
    
    def _on_generate_clicked(self, button):
        """Generate experiment snapshots."""
        if self.on_generate_callback:
            try:
                # Ensure parameter_type is set
                if self.parameter_type is None:
                    self.parameter_type = self.type_combo.get_active_id()
                    if self.parameter_type is None:
                        raise ValueError("Please select a parameter type")
                
                # Get parameter ID (internal key) from combo
                param_id = self.name_combo.get_active_id()
                param_name = self.name_combo.get_active_text()  # Display name for labels
                
                if not param_id or param_id == "none" or not param_name or param_name.startswith("("):
                    raise ValueError("Please select a parameter from the dropdown")
                
                values = self._compute_parameter_values()
                if not values:
                    raise ValueError("No parameter values to generate. Check range configuration.")
                
                config = {
                    'parameter_type': self.parameter_type,
                    'parameter_id': param_id,  # Internal ID for matching
                    'parameter_name': param_name,  # Display name for labels
                    'values': values,
                    'replicates': int(self.replicates_entry.get_text()),
                    'duration': float(self.duration_entry.get_text()),
                    'termination_condition': self.termination_combo.get_active_id()
                }
                self.on_generate_callback(config)
            except Exception as e:
                self.preview_label.set_markup(
                    f"<span foreground='red'>Generation failed: {str(e)}</span>"
                )
    
    def _on_clear_clicked(self, button):
        """Clear all inputs and notify parent to clear queue."""
        self.start_entry.set_text("0.1")
        self.stop_entry.set_text("1.0")
        self.step_entry.set_text("0.1")
        self.list_entry.set_text("")
        self.percent_entry.set_text("20")
        self.percent_steps_entry.set_text("5")
        self.replicates_entry.set_text("500")
        self.duration_entry.set_text("100.0")
        self.termination_combo.set_active_id("deadlock")
        self.preview_label.set_markup("<i>Configure parameters and click Preview</i>")
        self.generate_button.set_sensitive(False)
        
        # Notify parent to clear the experiment queue
        if self.on_clear_callback:
            self.on_clear_callback()
    
    def _compute_parameter_values(self):
        """Compute parameter values based on selected mode.
        
        Returns:
            list: List of parameter values to test
        """
        if self.linear_radio.get_active():
            # Linear range (supports both increasing and decreasing)
            start = float(self.start_entry.get_text())
            stop = float(self.stop_entry.get_text())
            step = float(self.step_entry.get_text())
            
            if step <= 0:
                raise ValueError("Step must be positive")
            if start == stop:
                raise ValueError("Start and stop must be different")
            
            values = []
            
            # Determine direction
            if start < stop:
                # Increasing range
                current = start
                while current <= stop:
                    values.append(current)
                    current += step
            else:
                # Decreasing range (e.g., NAD 2mM → 0mM)
                current = start
                while current >= stop:
                    values.append(current)
                    current -= step
            
            return values
            
        elif self.list_radio.get_active():
            # Value list
            text = self.list_entry.get_text().strip()
            if not text:
                raise ValueError("Value list is empty")
            
            values = [float(v.strip()) for v in text.split(',')]
            return values
            
        elif self.percent_radio.get_active():
            # Percentage variation (needs baseline value from current model)
            # For now, use a default baseline of 1.0
            baseline = 1.0
            percent = float(self.percent_entry.get_text())
            steps = int(self.percent_steps_entry.get_text())
            
            if steps <= 0:
                raise ValueError("Steps must be positive")
            
            # Generate values: baseline * (1 ± percent/100)
            min_val = baseline * (1 - percent / 100)
            max_val = baseline * (1 + percent / 100)
            
            if steps == 1:
                return [baseline]
            
            step_size = (max_val - min_val) / (steps - 1)
            values = [min_val + i * step_size for i in range(steps)]
            return values
        
        return []
    
    def set_available_parameters(self, parameter_type, parameters):
        """Set available parameters for selection.
        
        Args:
            parameter_type: Type of parameters ('places', 'transitions', 'arcs')
            parameters: List of (name, id) tuples or parameter names (for backward compatibility)
        """
        # Clear existing
        self.name_combo.remove_all()
        
        # Store ID mapping for later retrieval
        self._param_name_to_id = {}
        
        # Add new parameters
        for param in parameters:
            if isinstance(param, tuple) and len(param) == 2:
                # New format: (name, id) tuple
                name, param_id = param
                self.name_combo.append(param_id, name)  # Store ID as key, display name
                self._param_name_to_id[name] = param_id
            else:
                # Old format: just name/ID (backward compatibility)
                self.name_combo.append(param, param)
                self._param_name_to_id[param] = param
        
        # Select first if available
        if parameters:
            self.name_combo.set_active(0)
        else:
            # Show placeholder if no parameters
            self.name_combo.append("none", "(No parameters available)")
            self.name_combo.set_active(0)
    
    def set_generate_callback(self, callback):
        """Set callback for generate button.
        
        Args:
            callback: Function to call when generate is clicked
        """
        self.on_generate_callback = callback
    
    def set_clear_callback(self, callback):
        """Set callback for clear button.
        
        Args:
            callback: Function to call when clear is clicked
        """
        self.on_clear_callback = callback
    
    def _calculate_experiment_count(self):
        """Calculate number of experiments based on current configuration.
        
        Returns:
            int: Number of experiments that will be generated
        """
        try:
            values = self._compute_parameter_values()
            return len(values)
        except:
            return 0
    
    def prefill_parameter(self, param_type, param_id, param_name, current_value):
        """Pre-fill sweep builder with parameter from right-click context menu.
        
        Intelligently predicts range, replicates, and duration based on parameter type
        and current value.
        
        Args:
            param_type: 'place', 'transition', or 'arc'
            param_id: Parameter ID
            param_name: Parameter display name
            current_value: Current parameter value
        """
        # Map param_type to combo box format
        type_map = {
            'place': 'places',
            'transition': 'transitions',
            'arc': 'arcs'
        }
        
        # Set parameter type
        combo_type = type_map.get(param_type, 'places')
        self.type_combo.set_active_id(combo_type)
        
        # Try to select the parameter in name combo
        # The name_combo uses param_id as key
        self.name_combo.set_active_id(param_id)
        
        # === INTELLIGENT PREDICTION LOGIC ===
        
        # Predict range based on parameter type and value
        if param_type == 'place':
            # Place markings: typically integers, often represent molecule counts
            if current_value == 0:
                min_val, max_val, steps = 0, 100, 11
            elif current_value <= 10:
                min_val, max_val, steps = 0, current_value * 2, 11
            elif current_value <= 100:
                min_val, max_val, steps = current_value * 0.5, current_value * 1.5, 11
            else:
                min_val, max_val, steps = current_value * 0.7, current_value * 1.3, 11
                
        elif param_type == 'transition':
            # Transition rates: typically small floats (0.1-10 range)
            if current_value == 0:
                min_val, max_val, steps = 0, 5.0, 11
            elif current_value < 1.0:
                min_val, max_val, steps = current_value * 0.1, current_value * 10, 11
            else:
                min_val, max_val, steps = current_value * 0.2, current_value * 5, 11
                
        elif param_type == 'arc':
            # Arc weights: typically small integers (1-5 range)
            if current_value <= 1:
                min_val, max_val, steps = 1, 5, 5
            else:
                min_val, max_val, steps = 1, current_value * 2, min(current_value * 2, 10)
        else:
            # Fallback
            min_val, max_val, steps = 0, 100, 11
        
        # Predict replicates based on sweep size and parameter type
        # More replicates for stochastic systems, fewer for deterministic explorations
        total_experiments = steps
        if total_experiments <= 5:
            replicates = 100  # Few experiments → more replicates each
        elif total_experiments <= 10:
            replicates = 50   # Standard sweep → moderate replicates
        else:
            replicates = 30   # Large sweep → fewer replicates to save time
        
        # Further adjust by parameter type
        if param_type == 'place' and current_value < 20:
            # Low molecule counts → more stochasticity → more replicates
            replicates = min(replicates * 2, 200)
        elif param_type == 'transition' and current_value < 0.5:
            # Slow reactions → longer to equilibrate → more replicates
            replicates = min(replicates * 1.5, 150)
        
        # Predict duration based on parameter values and type
        if param_type == 'place':
            # Duration scales with initial marking (more molecules → longer to equilibrate)
            if current_value == 0:
                duration = 50.0
            elif current_value < 10:
                duration = 30.0
            elif current_value < 100:
                duration = 50.0
            else:
                duration = 100.0
                
        elif param_type == 'transition':
            # Duration inversely scales with rate (slower reactions → longer simulation)
            if current_value == 0:
                duration = 100.0
            elif current_value < 0.1:
                duration = 500.0  # Very slow reaction
            elif current_value < 1.0:
                duration = 200.0  # Slow reaction
            elif current_value < 10:
                duration = 50.0   # Fast reaction
            else:
                duration = 20.0   # Very fast reaction
                
        elif param_type == 'arc':
            # Arc weights affect stoichiometry → moderate duration
            duration = 50.0
        else:
            duration = 100.0
        
        # === APPLY PREDICTIONS TO UI ===
        
        # Set to linear mode
        self.linear_radio.set_active(True)
        
        # Fill range values in linear mode entries
        self.start_entry.set_text(f"{min_val:.2f}" if isinstance(min_val, float) else str(int(min_val)))
        self.stop_entry.set_text(f"{max_val:.2f}" if isinstance(max_val, float) else str(int(max_val)))
        
        # Calculate step size from min, max, and steps
        if steps > 1:
            step_size = (max_val - min_val) / (steps - 1)
            self.step_entry.set_text(f"{step_size:.3f}" if isinstance(step_size, float) else str(int(step_size)))
        else:
            self.step_entry.set_text("1")
        
        # Set simulation settings
        self.replicates_entry.set_text(str(int(replicates)))
        self.duration_entry.set_text(f"{duration:.1f}")
        
        # Update preview to show expected experiment count
        try:
            count = self._calculate_experiment_count()
            if count > 0:
                self.preview_label.set_markup(
                    f"<span foreground='blue'>Ready: {count} experiments will be generated</span>"
                )
            else:
                self.preview_label.set_markup(
                    "<i>Configure parameters and click Preview</i>"
                )
        except Exception as e:
            # Silently ignore preview calculation errors
            print(f"[PREFILL] Preview calculation failed: {e}")
