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
from shypn.utils.safe_eval import safe_eval_numeric
from shypn.ui.panels.viability.automation.gtk_widgets import SearchableComboBox as _SearchableComboBox


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
        
        # Factorial design state
        self.design_mode = 'single'  # 'single' or 'factorial'
        self.factorial_parameters = []  # List of selected parameters for factorial
        
        # Reference to viability panel for accessing model state
        self.viability_panel = None
        
        # Reference to parent automation category for refresh
        self.parent_category = None
        
        # Flag to prevent recursive prefill
        self._in_prefill = False
        
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
        
        # === DESIGN MODE SELECTION ===
        mode_frame = Gtk.Frame()
        mode_frame.set_label("Design Mode")
        mode_frame.set_margin_top(6)
        
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        mode_box.set_margin_start(12)
        mode_box.set_margin_end(12)
        mode_box.set_margin_top(6)
        mode_box.set_margin_bottom(6)
        
        self.single_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Single Parameter Sweep")
        self.single_radio.set_tooltip_text("Vary one parameter at a time")
        self.single_radio.connect("toggled", self._on_design_mode_changed)
        mode_box.pack_start(self.single_radio, False, False, 0)
        
        self.factorial_radio = Gtk.RadioButton.new_with_label_from_widget(self.single_radio, "Factorial Design")
        self.factorial_radio.set_tooltip_text("Vary multiple parameters simultaneously (creates all combinations)")
        self.factorial_radio.connect("toggled", self._on_design_mode_changed)
        mode_box.pack_start(self.factorial_radio, False, False, 0)
        
        mode_frame.add(mode_box)
        self.pack_start(mode_frame, False, False, 0)
        
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
        self.type_box = type_box  # Store reference for show/hide
        
        # === SINGLE PARAMETER MODE UI ===
        self.single_param_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Parameter selector with Add button
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name_label = Gtk.Label(label="Parameter:")
        name_label.set_size_request(100, -1)
        name_label.set_xalign(0)
        name_box.pack_start(name_label, False, False, 0)
        
        self.name_combo = _SearchableComboBox(
            tooltip_text="Load a model with subnet parameters to see available parameters"
        )
        name_box.pack_start(self.name_combo, True, True, 0)
        
        add_single_button = Gtk.Button(label="Add")
        add_single_button.connect("clicked", self._on_single_set_parameter_clicked)
        name_box.pack_start(add_single_button, False, False, 0)
        
        self.single_param_box.pack_start(name_box, False, False, 0)
        
        # TreeView for selected parameter
        scroll_single = Gtk.ScrolledWindow()
        scroll_single.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_single.set_min_content_height(80)
        
        self.single_list = Gtk.ListStore(str, str, str, object)  # name, type, id, range_config
        self.single_view = Gtk.TreeView(model=self.single_list)
        self.single_view.set_headers_visible(True)
        
        col_name_single = Gtk.TreeViewColumn("Parameter", Gtk.CellRendererText(), text=0)
        col_name_single.set_resizable(True)
        self.single_view.append_column(col_name_single)
        
        col_type_single = Gtk.TreeViewColumn("Type", Gtk.CellRendererText(), text=1)
        col_type_single.set_resizable(True)
        self.single_view.append_column(col_type_single)
        
        # Add Range column
        renderer_range_single = Gtk.CellRendererText()
        renderer_range_single.set_property("foreground", "#0066CC")
        col_range_single = Gtk.TreeViewColumn("Range", renderer_range_single)
        col_range_single.set_cell_data_func(renderer_range_single, self._format_range_column)
        col_range_single.set_resizable(True)
        self.single_view.append_column(col_range_single)
        
        scroll_single.add(self.single_view)
        self.single_param_box.pack_start(scroll_single, True, True, 0)
        
        # Button box for Edit Range and Remove
        button_box_single = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.single_edit_range_button = Gtk.Button(label="Edit Range...")
        self.single_edit_range_button.connect("clicked", self._on_single_edit_range_clicked)
        button_box_single.pack_start(self.single_edit_range_button, False, False, 0)
        
        single_remove_button = Gtk.Button(label="Remove Selected")
        single_remove_button.connect("clicked", self._on_single_remove_clicked)
        button_box_single.pack_start(single_remove_button, False, False, 0)
        
        self.single_param_box.pack_start(button_box_single, False, False, 0)
        
        selection_box.pack_start(self.single_param_box, True, True, 0)
        
        # === FACTORIAL PARAMETER MODE UI ===
        self.factorial_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Add label for clarity
        factorial_label = Gtk.Label(label="Add parameters to factorial design:")
        factorial_label.set_xalign(0)
        self.factorial_box.pack_start(factorial_label, False, False, 0)
        
        # Add parameter combo with label
        add_param_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        param_label = Gtk.Label(label="Parameter:")
        param_label.set_size_request(100, -1)
        param_label.set_xalign(0)
        add_param_box.pack_start(param_label, False, False, 0)
        
        self.factorial_add_combo = _SearchableComboBox(
            tooltip_text="Select parameter to add to factorial design"
        )
        add_param_box.pack_start(self.factorial_add_combo, True, True, 0)
        
        add_button = Gtk.Button(label="Add")
        add_button.connect("clicked", self._on_factorial_add_clicked)
        add_param_box.pack_start(add_button, False, False, 0)
        
        self.factorial_box.pack_start(add_param_box, False, False, 0)
        
        # List of selected parameters
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(80)
        
        self.factorial_list = Gtk.ListStore(str, str, str, object)  # name, type, id, range_config
        self.factorial_view = Gtk.TreeView(model=self.factorial_list)
        self.factorial_view.set_headers_visible(True)
        
        col_name = Gtk.TreeViewColumn("Parameter", Gtk.CellRendererText(), text=0)
        col_name.set_resizable(True)
        self.factorial_view.append_column(col_name)
        
        col_type = Gtk.TreeViewColumn("Type", Gtk.CellRendererText(), text=1)
        col_type.set_resizable(True)
        self.factorial_view.append_column(col_type)
        
        # Add Range column showing summary of range configuration
        renderer_range = Gtk.CellRendererText()
        renderer_range.set_property("foreground", "#0066CC")
        col_range = Gtk.TreeViewColumn("Range", renderer_range)
        col_range.set_cell_data_func(renderer_range, self._format_range_column)
        col_range.set_resizable(True)
        self.factorial_view.append_column(col_range)
        
        scroll.add(self.factorial_view)
        self.factorial_box.pack_start(scroll, True, True, 0)
        
        # Button box for Edit Range and Remove
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        edit_range_button = Gtk.Button(label="Edit Range...")
        edit_range_button.connect("clicked", self._on_factorial_edit_range_clicked)
        button_box.pack_start(edit_range_button, False, False, 0)
        
        remove_button = Gtk.Button(label="Remove Selected")
        remove_button.connect("clicked", self._on_factorial_remove_clicked)
        button_box.pack_start(remove_button, False, False, 0)
        
        self.factorial_box.pack_start(button_box, False, False, 0)
        
        selection_box.pack_start(self.factorial_box, True, True, 0)
        self.factorial_box.set_no_show_all(True)
        self.factorial_box.hide()
        
        selection_frame.add(selection_box)
        self.pack_start(selection_frame, False, False, 0)
        
        # === SIMULATION SETTINGS ===
        sim_frame = Gtk.Frame()
        sim_frame.set_label("Simulation Settings")
        sim_frame.set_margin_top(6)

        sim_outer_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sim_outer_vbox.set_margin_start(12)
        sim_outer_vbox.set_margin_end(12)
        sim_outer_vbox.set_margin_top(6)
        sim_outer_vbox.set_margin_bottom(6)

        # ── Top row: global run parameters (Replicates, Duration, Stop condition) ──
        top_grid = Gtk.Grid()
        top_grid.set_column_spacing(6)
        top_grid.set_row_spacing(4)

        top_grid.attach(Gtk.Label(label="Replicates:", xalign=0), 0, 0, 1, 1)
        self.replicates_entry = Gtk.Entry()
        self.replicates_entry.set_text("3")
        self.replicates_entry.set_width_chars(8)
        top_grid.attach(self.replicates_entry, 1, 0, 1, 1)

        top_grid.attach(Gtk.Label(label="Duration (s):", xalign=0), 2, 0, 1, 1)
        self.duration_entry = Gtk.Entry()
        self.duration_entry.set_text("60.0")
        self.duration_entry.set_width_chars(8)
        self.duration_entry.set_tooltip_text("Maximum simulation time in seconds (can stop earlier if condition met)")
        top_grid.attach(self.duration_entry, 3, 0, 1, 1)

        top_grid.attach(Gtk.Label(label="Stop condition:", xalign=0), 0, 1, 1, 1)
        self.termination_combo = Gtk.ComboBoxText()
        self.termination_combo.append("time_only", "Time limit only")
        self.termination_combo.append("deadlock", "Deadlock or time limit")
        self.termination_combo.append("steady_state", "Steady state or time limit")
        self.termination_combo.set_active_id("deadlock")
        self.termination_combo.set_tooltip_text("When to stop the simulation")
        top_grid.attach(self.termination_combo, 1, 1, 3, 1)

        sim_outer_vbox.pack_start(top_grid, False, False, 0)

        # Separator between global params and solver/compressor subgroups
        sim_outer_vbox.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 2
        )

        # ── Bottom row: two side-by-side sub-groups ──────────────────────────────
        subgroups_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        # ── Left sub-group: Time Step / Solver ───────────────────────
        solver_frame = Gtk.Frame()
        solver_frame.set_label("Time Step / Solver")

        solver_grid = Gtk.Grid()
        solver_grid.set_column_spacing(6)
        solver_grid.set_row_spacing(6)
        solver_grid.set_margin_start(8)
        solver_grid.set_margin_end(8)
        solver_grid.set_margin_top(4)
        solver_grid.set_margin_bottom(4)

        # Row 0: Time step — Auto / Manual radio + manual entry
        solver_grid.attach(Gtk.Label(label="Time step:", xalign=0), 0, 0, 1, 1)
        dt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.sweep_dt_auto_radio = Gtk.RadioButton.new_with_label(None, "Auto")
        self.sweep_dt_manual_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.sweep_dt_auto_radio, "Manual"
        )
        self.sweep_dt_auto_radio.set_active(True)
        self.sweep_dt_auto_radio.set_tooltip_text("Automatically compute time step from model kinetics")
        self.sweep_dt_manual_radio.set_tooltip_text("Use a fixed time step (override auto calculation)")
        self.sweep_dt_auto_radio.connect("toggled", self._on_sweep_dt_mode_changed)
        self.sweep_dt_manual_radio.connect("toggled", self._on_sweep_dt_mode_changed)
        dt_box.pack_start(self.sweep_dt_auto_radio, False, False, 0)
        dt_box.pack_start(self.sweep_dt_manual_radio, False, False, 0)
        solver_grid.attach(dt_box, 1, 0, 1, 1)
        self.sweep_dt_manual_entry = Gtk.Entry()
        self.sweep_dt_manual_entry.set_text("0.01")
        self.sweep_dt_manual_entry.set_width_chars(8)
        self.sweep_dt_manual_entry.set_sensitive(False)
        self.sweep_dt_manual_entry.set_tooltip_text("Fixed time step in seconds (smaller = more accurate, slower)")
        solver_grid.attach(self.sweep_dt_manual_entry, 2, 0, 1, 1)
        solver_grid.attach(Gtk.Label(label="s", xalign=0), 3, 0, 1, 1)

        # Row 1: τ-Leaping accuracy ε
        tau_label = Gtk.Label(label="τ-Leaping ε:", xalign=0)
        tau_label.set_tooltip_text(
            "τ-leaping is always enabled in this engine; only the accuracy bound ε can be tuned."
        )
        solver_grid.attach(tau_label, 0, 1, 1, 1)
        self.sweep_tau_epsilon_entry = Gtk.Entry()
        self.sweep_tau_epsilon_entry.set_text("0.03")
        self.sweep_tau_epsilon_entry.set_width_chars(8)
        self.sweep_tau_epsilon_entry.set_tooltip_text(
            "τ-leaping accuracy bound ε (0.01 = accurate/slow, 0.10 = fast/approximate).\n"
            "Primary accuracy control for both hybrid and pure-stochastic models.\n"
            "Applied at simulation start; changing it mid-run has no effect."
        )
        solver_grid.attach(self.sweep_tau_epsilon_entry, 1, 1, 2, 1)

        # Row 2: max τ
        solver_grid.attach(Gtk.Label(label="max τ:", xalign=0), 0, 2, 1, 1)
        self.sweep_max_tau_entry = Gtk.Entry()
        self.sweep_max_tau_entry.set_text("0.1")
        self.sweep_max_tau_entry.set_width_chars(8)
        self.sweep_max_tau_entry.set_tooltip_text(
            "Maximum leap size for τ-leaping.\n"
            "Only effective for pure-stochastic subnets (all transitions are stochastic/adaptive).\n"
            "In hybrid models (mixed transition types) τ is automatically clamped to dt each step,\n"
            "so this value has no effect — use the Time Step control instead."
        )
        solver_grid.attach(self.sweep_max_tau_entry, 1, 2, 2, 1)

        # Row 3: Random seed
        solver_grid.attach(Gtk.Label(label="Seed:", xalign=0), 0, 3, 1, 1)
        self.sweep_seed_entry = Gtk.Entry()
        self.sweep_seed_entry.set_text("42")
        self.sweep_seed_entry.set_width_chars(8)
        self.sweep_seed_entry.set_tooltip_text(
            "Base random seed for reproducibility (each replicate uses seed + replicate_id)"
        )
        solver_grid.attach(self.sweep_seed_entry, 1, 3, 2, 1)

        solver_frame.add(solver_grid)
        subgroups_hbox.pack_start(solver_frame, True, True, 0)

        # ── Right sub-group: Trajectory Compressor ───────────────────
        comp_frame = Gtk.Frame()
        comp_frame.set_label("Trajectory Compressor")

        comp_grid = Gtk.Grid()
        comp_grid.set_column_spacing(6)
        comp_grid.set_row_spacing(6)
        comp_grid.set_margin_start(8)
        comp_grid.set_margin_end(8)
        comp_grid.set_margin_top(4)
        comp_grid.set_margin_bottom(4)

        comp_grid.attach(Gtk.Label(label="δ-filter ε:", xalign=0), 0, 0, 1, 1)
        self.sweep_compressor_epsilon_entry = Gtk.Entry()
        self.sweep_compressor_epsilon_entry.set_text("0.02")
        self.sweep_compressor_epsilon_entry.set_width_chars(8)
        self.sweep_compressor_epsilon_entry.set_tooltip_text(
            "Normalised-change threshold (0.01–0.10).\n"
            "A time-point is kept whenever any channel changes by more than\n"
            "ε × (1 + range).  Lower = more points, higher fidelity.\n"
            "Default 0.02 (2%)."
        )
        comp_grid.attach(self.sweep_compressor_epsilon_entry, 1, 0, 1, 1)

        comp_grid.attach(Gtk.Label(label="min gap:", xalign=0), 0, 1, 1, 1)
        self.sweep_compressor_min_gap_entry = Gtk.Entry()
        self.sweep_compressor_min_gap_entry.set_text("5.0")
        self.sweep_compressor_min_gap_entry.set_width_chars(8)
        self.sweep_compressor_min_gap_entry.set_tooltip_text(
            "Minimum interval (s) between kept points (0 = disabled).\n"
            "For SSA / Gillespie data: set to 5–10× the raw time-step to prevent\n"
            "fast-transient species (nuclear mRNAs, GTP/GDP) from defeating\n"
            "compression.  E.g. raw step ≈ 0.36 s → min gap = 1.8 s gives\n"
            "~15–20× compression vs ~2.5× without this floor."
        )
        comp_grid.attach(self.sweep_compressor_min_gap_entry, 1, 1, 1, 1)
        comp_grid.attach(Gtk.Label(label="s", xalign=0), 2, 1, 1, 1)

        comp_grid.attach(Gtk.Label(label="max gap:", xalign=0), 0, 2, 1, 1)
        self.sweep_compressor_max_gap_entry = Gtk.Entry()
        self.sweep_compressor_max_gap_entry.set_text("300.0")
        self.sweep_compressor_max_gap_entry.set_width_chars(8)
        self.sweep_compressor_max_gap_entry.set_tooltip_text(
            "Heartbeat interval (s): unconditionally keep a point when no point\n"
            "has been kept for this many seconds.  Prevents silent stretches from\n"
            "being dropped entirely.  Default 300 s (5 min)."
        )
        comp_grid.attach(self.sweep_compressor_max_gap_entry, 1, 2, 1, 1)
        comp_grid.attach(Gtk.Label(label="s", xalign=0), 2, 2, 1, 1)

        comp_frame.add(comp_grid)
        subgroups_hbox.pack_start(comp_frame, True, True, 0)

        sim_outer_vbox.pack_start(subgroups_hbox, False, False, 0)
        sim_frame.add(sim_outer_vbox)
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
        
        # Initialize visibility: single mode is default
        self.design_mode = 'single'
        self.single_param_box.show_all()  # Ensure all widgets in single mode are visible initially
        self.single_edit_range_button.show()  # Explicitly show the button
    
    def _on_sweep_dt_mode_changed(self, radio):
        """Enable or disable the manual dt entry based on radio selection."""
        if not radio.get_active():
            return
        is_manual = (radio == self.sweep_dt_manual_radio)
        self.sweep_dt_manual_entry.set_sensitive(is_manual)

    def _on_type_changed(self, combo):
        """Handle parameter type change."""
        old_type = self.parameter_type
        self.parameter_type = combo.get_active_id()
        # Note: Parameter list will be populated by category's refresh_parameters()
        # when it detects the type change
    
    def _on_single_set_parameter_clicked(self, button):
        """Add/update parameter in single parameter mode."""
        param_id = self.name_combo.get_active_id()
        param_name = self.name_combo.get_active_text()
        
        if not param_id or param_id == "none" or not param_name or param_name.startswith("("):
            return
        
        # Clear existing parameter (single mode only has one parameter)
        self.single_list.clear()
        
        # Detect parameter type from ID prefix
        if param_id.startswith('T'):
            param_type = 'transitions'
        elif param_id.startswith('A'):
            param_type = 'arcs'
        elif param_id.startswith('P'):
            param_type = 'places'
        else:
            param_type = self.parameter_type  # Fallback to dropdown
        
        type_display = {"places": "Place", "transitions": "Transition", "arcs": "Arc"}.get(param_type, param_type)
        
        # Default range config
        default_range = {
            'mode': 'linear',
            'start': 0.1,
            'stop': 1.0,
            'step': 0.1,
            'list_values': '',
            'percent': 20.0,
            'percent_steps': 5,
            'baseline': 1.0
        }
        
        self.single_list.append([param_name, type_display, param_id, default_range])
    
    def _on_single_remove_clicked(self, button):
        """Remove parameter from single parameter list."""
        self.single_list.clear()
    
    def _on_design_mode_changed(self, radio):
        """Handle design mode change between single and factorial."""
        if not radio.get_active():
            return
        
        if self.single_radio.get_active():
            self.design_mode = 'single'
            self.type_box.show()  # Show type selector in single mode
            self.single_param_box.show_all()  # Use show_all() to show all children including button
            self.factorial_box.hide()
            self.factorial_box.set_no_show_all(True)  # Prevent accidental showing
            
            # Trigger parameter refresh to load selected type parameters in single mode
            if hasattr(self, 'parent_category') and self.parent_category:
                self.parent_category.refresh_parameters()
        else:
            self.design_mode = 'factorial'
            self.type_box.show()  # Keep type selector visible in factorial mode
            self.single_param_box.hide()
            # Unset no_show_all flag to allow showing
            self.factorial_box.set_no_show_all(False)
            self.factorial_box.show_all()  # show_all() to display all children
            
            # Trigger parameter refresh to load selected type parameters in factorial mode
            if hasattr(self, 'parent_category') and self.parent_category:
                self.parent_category.refresh_parameters()
    
    def _on_factorial_add_clicked(self, button):
        """Add parameter to factorial design."""
        param_id = self.factorial_add_combo.get_active_id()
        param_name = self.factorial_add_combo.get_active_text()
        
        if not param_id or param_id == "none":
            return
        
        # Check if already added
        for row in self.factorial_list:
            if row[2] == param_id:  # Check ID column
                return
        
        # Check limit (max 3 parameters for factorial)
        if len(self.factorial_list) >= 3:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Maximum 3 parameters for factorial design"
            )
            dialog.format_secondary_text("Factorial designs become very large with >3 parameters. For more parameters, consider fractional factorial designs or sequential optimization.")
            dialog.run()
            dialog.destroy()
            return
        
        # Detect parameter type from ID prefix
        if param_id.startswith('T'):
            param_type = 'transitions'
        elif param_id.startswith('A'):
            param_type = 'arcs'
        elif param_id.startswith('P'):
            param_type = 'places'
        else:
            param_type = self.parameter_type  # Fallback to dropdown
        
        type_display = {"places": "Place", "transitions": "Transition", "arcs": "Arc"}.get(param_type, param_type)
        
        # Default range config: linear 0.1 to 1.0, step 0.1 (10 values)
        default_range = {
            'mode': 'linear',
            'start': 0.1,
            'stop': 1.0,
            'step': 0.1,
            'list_values': '',
            'percent': 20.0,
            'percent_steps': 5,
            'baseline': 1.0
        }
        
        self.factorial_list.append([param_name, type_display, param_id, default_range])
        
        # Update preview
        self._update_factorial_preview()
    
    def _on_factorial_remove_clicked(self, button):
        """Remove selected parameter from factorial design."""
        selection = self.factorial_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            model.remove(tree_iter)
            self._update_factorial_preview()
    
    def _update_factorial_preview(self):
        """Update preview for factorial design with example combinations."""
        if len(self.factorial_list) == 0:
            self.preview_label.set_markup("<i>Add 2-3 parameters for factorial design</i>")
            self.generate_button.set_sensitive(False)
            return
        
        try:
            # Calculate experiment count per parameter
            total = 1
            param_info = []
            
            for row in self.factorial_list:
                param_name = row[0]
                range_config = row[3]
                
                # Compute values for this parameter's specific range
                values = self._compute_parameter_values_from_config(range_config)
                param_info.append({
                    'name': param_name,
                    'count': len(values),
                    'values': values
                })
                total *= len(values)
            
            # Build preview with multiplication and examples
            counts_str = " × ".join([str(p['count']) for p in param_info])
            preview_text = f"<span foreground='blue'><b>{counts_str} = {total} experiments</b></span>"
            
            # Add example combinations (first 3)
            if total > 0:
                import itertools
                param_values = [p['values'] for p in param_info]
                combinations = list(itertools.product(*param_values))
                
                examples = []
                for i, combo in enumerate(combinations[:3]):
                    parts = [f"{param_info[j]['name'][:15]}={combo[j]:.3g}" for j in range(len(combo))]
                    examples.append(", ".join(parts))
                
                if examples:
                    preview_text += "\n<span foreground='#666' size='small'>Examples:\n" + "\n".join(examples)
                    if total > 3:
                        preview_text += f"\n... ({total - 3} more)"
                    preview_text += "</span>"
            
            self.preview_label.set_markup(preview_text)
            self.generate_button.set_sensitive(total > 0 and total <= 500)
            
            if total > 500:
                self.preview_label.set_markup(
                    f"<span foreground='red'>Too many experiments ({total}). Reduce parameter ranges or values.</span>"
                )
        
        except Exception as e:
            self.preview_label.set_markup(f"<span foreground='red'>Error: {str(e)}</span>")
            self.generate_button.set_sensitive(False)
    
    def _on_name_changed(self, combo):
        """Handle parameter name selection - auto-predict range and settings."""
        # Prevent recursion when prefill_parameter changes the combo
        if self._in_prefill:
            return
            
        param_id = combo.get_active_id()
        param_name = combo.get_active_text()
        
        if not param_id or not param_name or param_id == "none":
            return
        
        # Get current value from the viability panel's tables
        if not hasattr(self, 'viability_panel') or self.viability_panel is None:
            return
        
        try:
            current_value = None
            param_type = self.parameter_type  # 'places', 'transitions', or 'arcs'
            
            # Get current value from appropriate table
            if param_type == 'places':
                # Search places table
                for row in self.viability_panel.places_store:
                    if row[0] == param_id:  # Column 0 is ID
                        current_value = row[2]  # Column 2 is marking
                        break
                        
            elif param_type == 'transitions':
                # Search transitions table
                for row in self.viability_panel.transitions_store:
                    if row[0] == param_id:  # Column 0 is ID
                        current_value = row[2]  # Column 2 is rate
                        break
                        
            elif param_type == 'arcs':
                # Search arcs table
                for row in self.viability_panel.arcs_store:
                    if row[0] == param_id:  # Column 0 is ID
                        current_value = row[3]  # Column 3 is weight
                        break
            
            if current_value is not None:
                # Evaluate if it's a formula
                evaluated_value = current_value
                if isinstance(current_value, str):
                    try:
                        # Build context with current place markings
                        context = {}
                        for place in self.viability_panel.canvas.model.places:
                            context[place.id] = place.tokens
                            if hasattr(place, 'name') and place.name:
                                context[place.name] = place.tokens
                        
                        # Safely evaluate the formula (replaces eval() for security)
                        evaluated_value = safe_eval_numeric(current_value, context, default_on_error=1.0)
                    except (ValueError, TypeError, AttributeError) as e:
                        # If evaluation fails, try to parse as float
                        import logging
                        logging.getLogger(__name__).debug(f"Formula evaluation failed: {e}")
                        try:
                            evaluated_value = float(current_value)
                        except (ValueError, TypeError):
                            evaluated_value = 1.0
                
                # Trigger prefill with evaluated value (but skip the combo updates)
                # Map param_type to singular form for prefill_parameter
                type_map = {'places': 'place', 'transitions': 'transition', 'arcs': 'arc'}
                singular_type = type_map.get(param_type, 'place')
                
                self._apply_prediction(singular_type, evaluated_value)
                
        except Exception as e:
            self.logger.debug(f"Failed to apply prediction for {param_type}: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_preview_clicked(self, button):
        """Preview experiment count and estimated execution time."""
        try:
            # Check factorial design requirements
            if self.design_mode == 'factorial' and len(self.factorial_list) < 2:
                self.preview_label.set_markup(
                    "<span foreground='orange'><b>Factorial Design:</b> Add at least 2 parameters to the list below</span>"
                )
                self.generate_button.set_sensitive(False)
                return
            
            values = self._compute_parameter_values()
            count = len(values)
            
            if count > 0:
                # Calculate estimated execution time
                time_estimate = self._calculate_time_estimate(count)
                
                # Format the preview message
                preview_msg = f"<b>Preview:</b> {count} experiments will be generated"
                if time_estimate:
                    preview_msg += f" | <b>Estimated time:</b> {time_estimate}"
                
                self.preview_label.set_markup(preview_msg)
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
    
    def _calculate_time_estimate(self, experiment_count):
        """Calculate estimated execution time for experiments.

        Uses actual wall-clock timing from previously completed experiments to
        calibrate the per-replicate cost.  Falls back to a step-count heuristic
        when no history is available.

        Args:
            experiment_count: Number of experiments to run

        Returns:
            str: Formatted time estimate (e.g., "2h 15m") or None if cannot calculate
        """
        import math
        import os

        try:
            replicates = int(self.replicates_entry.get_text().strip() or "3")
            duration = float(self.duration_entry.get_text().strip() or "60.0")

            # -- Parallel mode flag ------------------------------------------------
            use_parallel = False
            if (hasattr(self, 'parent_category') and self.parent_category and
                    hasattr(self.parent_category, 'queue_view') and
                    self.parent_category.queue_view):
                queue_view = self.parent_category.queue_view
                if hasattr(queue_view, 'parallel_checkbox'):
                    use_parallel = queue_view.parallel_checkbox.get_active()

            # -- Calibrated cost per replicate from completed results ---------------
            secs_per_rep = self._calibrated_secs_per_replicate()
            calibrated = secs_per_rep is not None

            # -- Fallback: step-count heuristic ------------------------------------
            if secs_per_rep is None:
                # In auto-dt / tau-leaping mode the engine always targets
                # DEFAULT_STEPS_TARGET steps regardless of simulated duration.
                # Using duration directly would over-predict dramatically for long runs.
                DEFAULT_STEPS_TARGET = 10_000
                dt_is_auto = not (hasattr(self, 'sweep_dt_manual_radio') and
                                  self.sweep_dt_manual_radio.get_active())
                if dt_is_auto:
                    n_steps = DEFAULT_STEPS_TARGET
                else:
                    try:
                        dt_manual = float(
                            self.sweep_dt_manual_entry.get_text().strip() or "0.01"
                        )
                        n_steps = (
                            int(duration / dt_manual) if dt_manual > 0
                            else DEFAULT_STEPS_TARGET
                        )
                    except (ValueError, AttributeError):
                        n_steps = DEFAULT_STEPS_TARGET

                # Empirical s/step from a single 60 s benchmark (conservative upper bound)
                cost_per_step = 0.01446 if use_parallel else 0.00496
                secs_per_rep = n_steps * cost_per_step

            # -- Total time --------------------------------------------------------
            time_per_experiment = replicates * secs_per_rep

            if use_parallel:
                # Each batch runs min(cpu_cores, experiments) jobs simultaneously.
                cpu_cores = os.cpu_count() or 4
                batches = math.ceil(experiment_count / cpu_cores)
                total_seconds = batches * time_per_experiment
            else:
                total_seconds = experiment_count * time_per_experiment

            # -- Format ------------------------------------------------------------
            suffix = "" if calibrated else " (est.)"

            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)

            if hours > 0:
                formatted = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            elif minutes > 0:
                if seconds > 30:
                    minutes += 1
                formatted = f"{minutes}m"
            else:
                formatted = f"{seconds}s"

            return formatted + suffix

        except Exception:
            return None

    def _calibrated_secs_per_replicate(self):
        """Return mean wall-clock seconds per replicate from recent completed results.

        Looks at the last 20 successful experiments stored in the parent category's
        batch executor.  Returns None when no usable timing data is available.
        """
        try:
            executor = (
                self.parent_category.batch_executor
                if (hasattr(self, 'parent_category') and self.parent_category and
                    hasattr(self.parent_category, 'batch_executor'))
                else None
            )
            if executor is None:
                return None

            results = getattr(executor, 'results', {})
            if not results:
                return None

            samples = []
            for result in list(results.values())[-20:]:   # use at most last 20
                elapsed = result.get('elapsed_time', 0.0)
                n_reps = result.get('n_replicates', 0) or 0
                if elapsed > 0 and n_reps > 0:
                    samples.append(elapsed / n_reps)

            return sum(samples) / len(samples) if samples else None
        except Exception:
            return None
    
    def _on_generate_clicked(self, button):
        """Generate experiment snapshots."""
        if self.on_generate_callback:
            try:
                if self.design_mode == 'factorial':
                    self._generate_factorial_experiments()
                else:
                    self._generate_single_parameter_experiments()
            except Exception as e:
                self.preview_label.set_markup(
                    f"<span foreground='red'>Generation failed: {str(e)}</span>"
                )
    
    def _generate_single_parameter_experiments(self):
        """Generate single parameter sweep experiments using TreeView."""
        # Get parameter from TreeView
        if len(self.single_list) == 0:
            raise ValueError("Please add a parameter using 'Add' button")
        
        tree_iter = self.single_list.get_iter_first()
        if not tree_iter:
            raise ValueError("Please add a parameter using 'Add' button")
        
        param_name = self.single_list.get_value(tree_iter, 0)
        param_type_display = self.single_list.get_value(tree_iter, 1)
        param_id = self.single_list.get_value(tree_iter, 2)
        range_config = self.single_list.get_value(tree_iter, 3)
        
        # Convert type display back to parameter_type
        type_map = {"Place": "places", "Transition": "transitions", "Arc": "arcs"}
        parameter_type = type_map.get(param_type_display, "places")
        
        values = self._compute_parameter_values_from_config(range_config)
        if not values:
            raise ValueError("No parameter values to generate. Check range configuration.")
        
        config = {
            'parameter_type': parameter_type,
            'parameter_id': param_id,  # Internal ID for matching
            'parameter_name': param_name,  # Display name for labels
            'values': values,
            'replicates': int(self.replicates_entry.get_text()),
            'duration': float(self.duration_entry.get_text()),
            'termination_condition': self.termination_combo.get_active_id(),
        }
        
        self.on_generate_callback(config)
    
    def _generate_factorial_experiments(self):
        """Generate factorial design experiments."""
        if len(self.factorial_list) < 2:
            raise ValueError("Factorial design requires at least 2 parameters. Please add more parameters to the list.")
        
        # Collect all parameters and their values
        parameters = []
        for row in self.factorial_list:
            param_name = row[0]
            param_type = row[1].lower() + "s"  # "Place" -> "places"
            param_id = row[2]
            range_config = row[3]
            
            # Get parameter values from its specific range configuration
            values = self._compute_parameter_values_from_config(range_config)
            if not values:
                raise ValueError(f"No values computed for {param_name}")
            
            parameters.append({
                'name': param_name,
                'type': param_type,
                'id': param_id,
                'values': values
            })
        
        # Generate factorial grid
        import itertools
        param_combinations = list(itertools.product(*[p['values'] for p in parameters]))
        
        # Create experiments for each combination
        factorial_config = {
            'design_type': 'factorial',
            'parameters': parameters,
            'combinations': param_combinations,
            'replicates': int(self.replicates_entry.get_text()),
            'duration': float(self.duration_entry.get_text()),
            'termination_condition': self.termination_combo.get_active_id(),
        }
        
        self.on_generate_callback(factorial_config)
    
    def _on_clear_clicked(self, button):
        """Clear all inputs and notify parent to clear queue."""
        # Clear single parameter list
        self.single_list.clear()
        
        self.replicates_entry.set_text("3")
        self.duration_entry.set_text("60.0")
        self.termination_combo.set_active_id("deadlock")
        self.preview_label.set_markup("<i>Configure parameters and click Preview</i>")
        self.generate_button.set_sensitive(False)
        
        # Notify parent to clear the experiment queue
        if self.on_clear_callback:
            self.on_clear_callback()
    
    def _compute_parameter_values(self):
        """Compute parameter values based on selected mode.
        
        Returns:
            list: List of parameter values (single mode) or combinations (factorial mode)
        """
        if self.design_mode == 'factorial':
            # For factorial design, return all combinations
            if len(self.factorial_list) < 2:
                return []

            # Collect all parameters and their values
            all_param_values = []
            try:
                for row in self.factorial_list:
                    range_config = row[3]
                    values = self._compute_parameter_values_from_config(range_config)
                    if not values:
                        return []  # If any parameter has no values, can't create combinations
                    all_param_values.append(values)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return []

            # Generate factorial combinations
            import itertools
            combinations = list(itertools.product(*all_param_values))
            return combinations
        else:
            # Single parameter mode - get config from TreeView
            if len(self.single_list) == 0:
                return []
            
            tree_iter = self.single_list.get_iter_first()
            if tree_iter:
                range_config = self.single_list.get_value(tree_iter, 3)
                try:
                    return self._compute_parameter_values_from_config(range_config)
                except Exception as e:
                    print(f"Error computing parameter values: {e}")
                    import traceback
                    traceback.print_exc()
                    return []
            
            return []
    

    def _on_single_edit_range_clicked(self, button):
        """Open dialog to edit range configuration for single parameter mode."""
        # Get selected parameter from TreeView
        selection = self.single_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if not tree_iter:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No parameter selected"
            )
            dialog.format_secondary_text("Please add a parameter using 'Add' button first.")
            dialog.run()
            dialog.destroy()
            return
        
        param_name = model.get_value(tree_iter, 0)
        current_config = model.get_value(tree_iter, 3)
        
        # Open range configuration dialog
        new_config = self._show_range_config_dialog(param_name, current_config)
        
        if new_config:
            # Update the range configuration in the TreeView
            model.set_value(tree_iter, 3, new_config)
    
    def _compute_parameter_values_from_config(self, config):
        """Compute parameter values from a range configuration dict.
        
        Args:
            config: Dictionary with keys: mode, start, stop, step, list_values, percent, percent_steps, baseline
            
        Returns:
            list: List of parameter values
        """
        mode = config.get('mode', 'linear')
        
        if mode == 'linear':
            start = config['start']
            stop = config['stop']
            step = config['step']
            
            if step <= 0:
                raise ValueError("Step must be positive")
            if start == stop:
                raise ValueError("Start and stop must be different")
            
            values = []
            if start < stop:
                current = start
                while current <= stop:
                    values.append(current)
                    current += step
            else:
                current = start
                while current >= stop:
                    values.append(current)
                    current -= step
            
            return values
            
        elif mode == 'list':
            text = config.get('list_values', '').strip()
            if not text:
                raise ValueError("Value list is empty")
            # Accept comma, semicolon, or whitespace as separators.
            # Also strip trailing punctuation (e.g. stray periods) from each token.
            import re
            raw_tokens = re.split(r'[,;\s]+', text)
            values = []
            for token in raw_tokens:
                token = token.strip().strip('"\'').strip().rstrip('.,;')
                if token:
                    try:
                        values.append(float(token))
                    except ValueError:
                        raise ValueError(
                            f"Could not convert '{token}' to a number. "
                            "Use commas to separate values (e.g. 0.1, 0.3, 0.5)."
                        )
            if not values:
                raise ValueError("Value list is empty after parsing")
            return values
            
        elif mode == 'percent':
            baseline = config.get('baseline', 1.0)
            percent = config.get('percent', 20.0)
            steps = config.get('percent_steps', 5)
            
            if steps <= 0:
                raise ValueError("Steps must be positive")
            
            min_val = baseline * (1 - percent / 100)
            max_val = baseline * (1 + percent / 100)
            
            if steps == 1:
                return [baseline]
            
            step_size = (max_val - min_val) / (steps - 1)
            values = [min_val + i * step_size for i in range(steps)]
            return values
        
        return []
    
    def _format_range_column(self, column, cell, model, iter, data):
        """Format the range column to show a summary of the range configuration."""
        range_config = model.get_value(iter, 3)
        if not range_config:
            cell.set_property('text', 'Not configured')
            return
        
        mode = range_config.get('mode', 'linear')
        
        try:
            values = self._compute_parameter_values_from_config(range_config)
            n = len(values)
            
            if mode == 'linear':
                start = range_config['start']
                stop = range_config['stop']
                cell.set_property('text', f"{start:.3g} to {stop:.3g} ({n} values)")
            elif mode == 'list':
                if n <= 4:
                    vals_str = ', '.join([f"{v:.3g}" for v in values])
                    cell.set_property('text', vals_str)
                else:
                    cell.set_property('text', f"{values[0]:.3g}, {values[1]:.3g}, ... ({n} values)")
            elif mode == 'percent':
                baseline = range_config.get('baseline', 1.0)
                percent = range_config.get('percent', 20.0)
                cell.set_property('text', f"{baseline:.3g} ± {percent}% ({n} values)")
            else:
                cell.set_property('text', f"{n} values")
        except Exception as e:
            cell.set_property('text', f'Error: {str(e)[:30]}')
    
    def _on_factorial_edit_range_clicked(self, button):
        """Open dialog to edit range configuration for selected parameter."""
        selection = self.factorial_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if not tree_iter:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No parameter selected"
            )
            dialog.format_secondary_text("Please select a parameter from the list to edit its range.")
            dialog.run()
            dialog.destroy()
            return
        
        param_name = model.get_value(tree_iter, 0)
        current_config = model.get_value(tree_iter, 3)
        
        # Open range configuration dialog
        new_config = self._show_range_config_dialog(param_name, current_config)
        
        if new_config:
            # Update the range configuration
            model.set_value(tree_iter, 3, new_config)
            # Update preview
            self._update_factorial_preview()
    
    def _show_range_config_dialog(self, param_name, current_config):
        """Show dialog to configure range for a parameter.
        
        Returns:
            dict or None: New configuration dict or None if cancelled
        """
        dialog = Gtk.Dialog(
            title=f"Configure Range: {param_name}",
            transient_for=self.get_toplevel(),
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(400, 300)
        
        content = dialog.get_content_area()
        content.set_spacing(12)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        # Radio buttons for mode
        linear_radio = Gtk.RadioButton(label="Linear Range")
        content.pack_start(linear_radio, False, False, 0)
        
        # Linear range inputs
        linear_grid = Gtk.Grid()
        linear_grid.set_column_spacing(6)
        linear_grid.set_row_spacing(6)
        linear_grid.set_margin_start(24)
        
        linear_grid.attach(Gtk.Label(label="Start:", xalign=0), 0, 0, 1, 1)
        start_entry = Gtk.Entry()
        start_entry.set_text(str(current_config.get('start', 0.1)))
        start_entry.set_width_chars(10)
        linear_grid.attach(start_entry, 1, 0, 1, 1)
        
        linear_grid.attach(Gtk.Label(label="Stop:", xalign=0), 2, 0, 1, 1)
        stop_entry = Gtk.Entry()
        stop_entry.set_text(str(current_config.get('stop', 1.0)))
        stop_entry.set_width_chars(10)
        linear_grid.attach(stop_entry, 3, 0, 1, 1)
        
        linear_grid.attach(Gtk.Label(label="Step:", xalign=0), 4, 0, 1, 1)
        step_entry = Gtk.Entry()
        step_entry.set_text(str(current_config.get('step', 0.1)))
        step_entry.set_width_chars(10)
        linear_grid.attach(step_entry, 5, 0, 1, 1)
        
        content.pack_start(linear_grid, False, False, 0)
        
        # List values radio
        list_radio = Gtk.RadioButton(group=linear_radio, label="Value List")
        content.pack_start(list_radio, False, False, 0)
        
        # List values input
        list_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        list_box.set_margin_start(24)
        list_entry = Gtk.Entry()
        list_entry.set_placeholder_text("e.g., 0.1, 0.5, 1.0, 2.0")
        list_entry.set_text(current_config.get('list_values', ''))
        list_box.pack_start(list_entry, True, True, 0)
        content.pack_start(list_box, False, False, 0)
        
        # Percentage variation radio
        percent_radio = Gtk.RadioButton(group=linear_radio, label="Percentage Variation")
        content.pack_start(percent_radio, False, False, 0)
        
        # Percentage inputs
        percent_grid = Gtk.Grid()
        percent_grid.set_column_spacing(6)
        percent_grid.set_row_spacing(6)
        percent_grid.set_margin_start(24)
        
        percent_grid.attach(Gtk.Label(label="Baseline:", xalign=0), 0, 0, 1, 1)
        baseline_entry = Gtk.Entry()
        baseline_entry.set_text(str(current_config.get('baseline', 1.0)))
        baseline_entry.set_width_chars(8)
        percent_grid.attach(baseline_entry, 1, 0, 1, 1)
        
        percent_grid.attach(Gtk.Label(label="±", xalign=0), 2, 0, 1, 1)
        percent_entry = Gtk.Entry()
        percent_entry.set_text(str(current_config.get('percent', 20.0)))
        percent_entry.set_width_chars(6)
        percent_grid.attach(percent_entry, 3, 0, 1, 1)
        percent_grid.attach(Gtk.Label(label="%", xalign=0), 4, 0, 1, 1)
        
        percent_grid.attach(Gtk.Label(label="Steps:", xalign=0), 0, 1, 1, 1)
        percent_steps_entry = Gtk.Entry()
        percent_steps_entry.set_text(str(current_config.get('percent_steps', 5)))
        percent_steps_entry.set_width_chars(6)
        percent_grid.attach(percent_steps_entry, 1, 1, 1, 1)
        
        content.pack_start(percent_grid, False, False, 0)
        
        # Set active radio based on current mode
        mode = current_config.get('mode', 'linear')
        if mode == 'list':
            list_radio.set_active(True)
        elif mode == 'percent':
            percent_radio.set_active(True)
        else:
            linear_radio.set_active(True)
        
        dialog.show_all()
        response = dialog.run()
        
        result = None
        if response == Gtk.ResponseType.OK:
            # Build new config based on selected mode
            if linear_radio.get_active():
                result = {
                    'mode': 'linear',
                    'start': float(start_entry.get_text()),
                    'stop': float(stop_entry.get_text()),
                    'step': float(step_entry.get_text()),
                    'list_values': current_config.get('list_values', ''),
                    'percent': current_config.get('percent', 20.0),
                    'percent_steps': current_config.get('percent_steps', 5),
                    'baseline': current_config.get('baseline', 1.0)
                }
            elif list_radio.get_active():
                result = {
                    'mode': 'list',
                    'list_values': list_entry.get_text(),
                    'start': current_config.get('start', 0.1),
                    'stop': current_config.get('stop', 1.0),
                    'step': current_config.get('step', 0.1),
                    'percent': current_config.get('percent', 20.0),
                    'percent_steps': current_config.get('percent_steps', 5),
                    'baseline': current_config.get('baseline', 1.0)
                }
            elif percent_radio.get_active():
                result = {
                    'mode': 'percent',
                    'baseline': float(baseline_entry.get_text()),
                    'percent': float(percent_entry.get_text()),
                    'percent_steps': int(percent_steps_entry.get_text()),
                    'start': current_config.get('start', 0.1),
                    'stop': current_config.get('stop', 1.0),
                    'step': current_config.get('step', 0.1),
                    'list_values': current_config.get('list_values', '')
                }
        
        dialog.destroy()
        return result
    
    def set_available_parameters(self, parameter_type, parameters):
        """Set available parameters for selection.
        
        Args:
            parameter_type: Type of parameters ('places', 'transitions', 'arcs', 'all')
            parameters: List of (name, id) tuples or parameter names (for backward compatibility)
        """
        # Clear existing
        self.name_combo.remove_all()
        self.factorial_add_combo.remove_all()
        
        # Store ID mapping for later retrieval
        self._param_name_to_id = {}
        
        # Add new parameters
        for param in parameters:
            if isinstance(param, tuple) and len(param) == 2:
                # New format: (name, id) tuple
                name, param_id = param
                self.name_combo.append(param_id, name)  # Store ID as key, display name
                self.factorial_add_combo.append(param_id, name)
                self._param_name_to_id[name] = param_id
            else:
                # Old format: just name/ID (backward compatibility)
                self.name_combo.append(param, param)
                self.factorial_add_combo.append(param, param)
                self._param_name_to_id[param] = param
        
        # Select first if available
        if parameters:
            self.name_combo.set_active(0)
            self.factorial_add_combo.set_active(0)
        else:
            # Show placeholder if no parameters
            placeholder_msg = "(Load subnet via right-click transition)" if parameter_type == 'all' else "(No parameters available)"
            self.name_combo.append("none", placeholder_msg)
            self.name_combo.set_active(0)
            self.factorial_add_combo.append("none", placeholder_msg)
            self.factorial_add_combo.set_active(0)
    
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
        except (ValueError, AttributeError, KeyError) as e:
            # Parameter value computation failed
            import logging
            logging.getLogger(__name__).debug(f"Experiment count calculation failed: {e}")
            return 0
    
    def _apply_prediction(self, param_type, numeric_value):
        """Apply intelligent prediction to Range and Simulation fields without changing combos.
        
        Args:
            param_type: 'place', 'transition', or 'arc'
            numeric_value: Evaluated numeric value for prediction
        """
        try:
            # Predict range based on parameter type and value
            if param_type == 'place':
                # Place markings: typically integers, often represent molecule counts
                if numeric_value == 0:
                    min_val, max_val, steps = 0, 100, 11
                elif numeric_value <= 10:
                    min_val, max_val, steps = 0, numeric_value * 2, 11
                elif numeric_value <= 100:
                    min_val, max_val, steps = numeric_value * 0.5, numeric_value * 1.5, 11
                else:
                    min_val, max_val, steps = numeric_value * 0.7, numeric_value * 1.3, 11
                    
            elif param_type == 'transition':
                # Transition rates: typically small floats (0.1-10 range)
                if numeric_value == 0:
                    min_val, max_val, steps = 0, 5.0, 11
                elif numeric_value < 1.0:
                    min_val, max_val, steps = numeric_value * 0.1, numeric_value * 10, 11
                else:
                    min_val, max_val, steps = numeric_value * 0.2, numeric_value * 5, 11
                    
            elif param_type == 'arc':
                # Arc weights: typically small integers (1-5 range)
                if numeric_value <= 1:
                    min_val, max_val, steps = 1, 5, 5
                else:
                    min_val, max_val, steps = 1, numeric_value * 2, min(int(numeric_value * 2), 10)
            else:
                # Fallback
                min_val, max_val, steps = 0, 100, 11
            
            # Predict replicates
            total_experiments = steps
            if total_experiments <= 5:
                replicates = 100
            elif total_experiments <= 10:
                replicates = 50
            else:
                replicates = 30
            
            # Adjust by parameter type
            if param_type == 'place' and numeric_value < 20:
                replicates = min(replicates * 2, 200)
            elif param_type == 'transition' and numeric_value < 0.5:
                replicates = min(replicates * 1.5, 150)
            
            # Predict duration (proportional to consumption time)
            if param_type == 'place':
                # Duration ~= tokens to consume (assuming rate ~1.0)
                # Add margin for observation
                if numeric_value == 0:
                    duration = 20.0
                else:
                    duration = max(20.0, numeric_value * 1.2)
                    
            elif param_type == 'transition':
                # Duration inversely proportional to rate
                # Slower rates need more time to show effect
                if numeric_value == 0:
                    duration = 100.0
                elif numeric_value < 0.1:
                    duration = 500.0
                elif numeric_value < 1.0:
                    duration = 200.0
                elif numeric_value < 10:
                    duration = 50.0
                else:
                    duration = 20.0
                    
            elif param_type == 'arc':
                # Arc weights affect rate, use moderate duration
                duration = 50.0
            else:
                duration = 100.0
            
            # === APPLY TO UI ===
            
            # Set to linear mode
            self.linear_radio.set_active(True)
            
            # Fill range values
            self.start_entry.set_text(f"{min_val:.2f}" if isinstance(min_val, float) else str(int(min_val)))
            self.stop_entry.set_text(f"{max_val:.2f}" if isinstance(max_val, float) else str(int(max_val)))
            
            # Calculate step size
            if steps > 1:
                step_size = (max_val - min_val) / (steps - 1)
                self.step_entry.set_text(f"{step_size:.3f}" if isinstance(step_size, float) else str(int(step_size)))
            else:
                self.step_entry.set_text("1")
            
            # Set simulation settings
            self.replicates_entry.set_text(str(int(replicates)))
            self.duration_entry.set_text(f"{duration:.1f}")
            
            # Update preview
            try:
                count = self._calculate_experiment_count()
                if count > 0:
                    self.preview_label.set_markup(
                        f"<span foreground='blue'>Ready: {count} experiments will be generated</span>"
                    )
            except (ValueError, AttributeError) as e:
                # Preview update failed, not critical
                import logging
                logging.getLogger(__name__).debug(f"Preview update failed: {e}")
                pass
                
        except Exception as e:
            self.logger.debug(f"Failed to update preview after value changes: {e}")
    
    def prefill_parameter(self, param_type, param_id, param_name, current_value):
        """Pre-fill sweep builder with parameter from right-click context menu.
        
        Intelligently predicts range, replicates, and duration based on parameter type
        and current value.
        
        Args:
            param_type: 'place', 'transition', or 'arc'
            param_id: Parameter ID
            param_name: Parameter display name
            current_value: Current parameter value (should be numeric)
        """
        self._in_prefill = True
        try:
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
            
            # Convert to numeric
            try:
                numeric_value = float(current_value)
            except (ValueError, TypeError):
                numeric_value = 1.0 if param_type == 'transition' else 10.0
            
            # Apply the prediction
            self._apply_prediction(param_type, numeric_value)
                
        finally:
            self._in_prefill = False

