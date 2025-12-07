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
        
        # Callbacks
        self.on_generate_callback = None
        
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
        sim_box.attach(self.duration_entry, 3, 0, 1, 1)
        
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
                
                # Get parameter name
                param_name = self.name_combo.get_active_text()
                if not param_name or param_name.startswith("("):
                    raise ValueError("Please select a parameter from the dropdown")
                
                values = self._compute_parameter_values()
                if not values:
                    raise ValueError("No parameter values to generate. Check range configuration.")
                
                config = {
                    'parameter_type': self.parameter_type,
                    'parameter_name': param_name,
                    'values': values,
                    'replicates': int(self.replicates_entry.get_text()),
                    'duration': float(self.duration_entry.get_text())
                }
                self.on_generate_callback(config)
            except Exception as e:
                self.preview_label.set_markup(
                    f"<span foreground='red'>Generation failed: {str(e)}</span>"
                )
    
    def _on_clear_clicked(self, button):
        """Clear all inputs."""
        self.start_entry.set_text("0.1")
        self.stop_entry.set_text("1.0")
        self.step_entry.set_text("0.1")
        self.list_entry.set_text("")
        self.percent_entry.set_text("20")
        self.percent_steps_entry.set_text("5")
        self.replicates_entry.set_text("500")
        self.duration_entry.set_text("100.0")
        self.preview_label.set_markup("<i>Configure parameters and click Preview</i>")
        self.generate_button.set_sensitive(False)
    
    def _compute_parameter_values(self):
        """Compute parameter values based on selected mode.
        
        Returns:
            list: List of parameter values to test
        """
        if self.linear_radio.get_active():
            # Linear range
            start = float(self.start_entry.get_text())
            stop = float(self.stop_entry.get_text())
            step = float(self.step_entry.get_text())
            
            if step <= 0:
                raise ValueError("Step must be positive")
            if start >= stop:
                raise ValueError("Start must be less than stop")
            
            values = []
            current = start
            while current <= stop:
                values.append(current)
                current += step
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
            parameters: List of parameter names
        """
        # Clear existing
        self.name_combo.remove_all()
        
        # Add new parameters
        for param in parameters:
            self.name_combo.append(param, param)
        
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
