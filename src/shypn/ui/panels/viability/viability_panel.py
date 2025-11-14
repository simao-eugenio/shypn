#!/usr/bin/env python3
"""Viability Assistant Panel - Intelligent Model Improvement Suggester.

REFACTORED ARCHITECTURE (Phase 7):
- NO reactive observers (pull-based data access)
- Thin orchestrator connecting UI components to analyzers
- User-triggered investigation workflow
- Full Apply/Preview/Undo support

WORKFLOW:
1. User right-clicks transition → "Add to Viability Analysis"
2. Panel pulls KB/sim data on-demand
3. Subnet builder validates connectivity
4. Multi-level analyzers generate suggestions
5. UI displays in SubnetView with Apply/Preview/Undo

COMPONENTS:
- DataPuller: Pull KB/sim data on-demand (no observers)
- SubnetBuilder: Build connected subnets
- Analyzers: LocalityAnalyzer, DependencyAnalyzer, BoundaryAnalyzer, ConservationAnalyzer
- FixSystem: FixSequencer, FixApplier, FixPredictor
- UI: SubnetView (multi-level), InvestigationView (single locality)

Author: Simão Eugénio
Date: November 12, 2025 (Refactored)
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, GLib, Pango

from .data.data_puller import DataPuller
from .data.data_cache import CachedDataPuller, DataCache
from .subnet_builder import SubnetBuilder
from .investigation import Investigation
from .analysis import LocalityAnalyzer, DependencyAnalyzer, BoundaryAnalyzer, ConservationAnalyzer
from .fixes import FixSequencer, FixApplier, FixPredictor
from .ui.subnet_view import SubnetView
from .ui.investigation_view import InvestigationView
from .experiment_manager import ExperimentManager
from .subnet_simulator import SubnetSimulator
from .ui.simulation_control_toolbar import SimulationControlToolbar


class ViabilityPanel(Gtk.Box):
    """Viability Assistant Panel - REFACTORED.
    
    NEW Architecture (Phase 7):
    - Thin orchestrator (no business logic)
    - Pull-based data access (no reactive observers)
    - User-triggered workflow only
    - Connects UI components to analyzers and fix system
    """
    
    def __init__(self, model=None, model_canvas=None):
        """Initialize viability assistant panel.
        
        Args:
            model: ShypnModel instance (optional, can be set later)
            model_canvas: ModelCanvas instance for accessing current model and KB
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.model = model
        self.model_canvas = model_canvas
        self.drawing_area = None  # Will be set via set_drawing_area()
        self.topology_panel = None
        self.analyses_panel = None
        
        # Data layer (pull-based)
        self.data_puller = None
        self.data_cache = DataCache(default_ttl=60.0)
        
        # Analysis components
        self.subnet_builder = SubnetBuilder()
        self.locality_analyzer = LocalityAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.boundary_analyzer = BoundaryAnalyzer()
        self.conservation_analyzer = ConservationAnalyzer()
        
        # Fix system
        self.fix_sequencer = FixSequencer()
        self.fix_applier = None  # Created when KB available
        self.fix_predictor = None  # Created when KB available
        
        # Simulation components (NEW)
        self.experiment_manager = ExperimentManager()
        self.subnet_simulator = SubnetSimulator(self)
        
        # Current investigation
        self.current_investigation = None
        self.current_view = None  # SubnetView or InvestigationView
        
        # Locality tracking for coloring
        self._locality_objects = {}
        
        # Track current drawing area to detect document switches
        self._current_drawing_area_id = None
        
        # Build panel UI
        self._build_header()
        self._build_content()
        
        # Don't call show_all() here - panel will be shown after being packed into container
        # (matches Report panel pattern)
    
    def _build_header(self):
        """Build panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.set_size_request(-1, 48)
        header_box.set_margin_start(10)
        header_box.set_margin_end(10)
        
        # Title label (left)
        header_label = Gtk.Label()
        header_label.set_markup("<b>VIABILITY</b>")
        header_label.set_halign(Gtk.Align.START)
        header_label.set_valign(Gtk.Align.CENTER)
        header_label.set_tooltip_text("Model viability analysis and suggestions")
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button (right)
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("Detach")
        self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)
        self.float_button.set_valign(Gtk.Align.CENTER)
        header_box.pack_end(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
    
    def _build_content(self):
        """Build main content area with localities list and results."""
        # Main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # === SECTION 1: SELECTED LOCALITIES LIST ===
        localities_frame = Gtk.Frame()
        localities_frame.set_label("Selected Localities")
        localities_frame.set_margin_start(10)
        localities_frame.set_margin_end(10)
        localities_frame.set_margin_top(10)
        
        localities_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        localities_box.set_margin_start(10)
        localities_box.set_margin_end(10)
        localities_box.set_margin_top(10)
        localities_box.set_margin_bottom(10)
        
        # Scrolled window for localities list
        localities_scroll = Gtk.ScrolledWindow()
        localities_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        localities_scroll.set_size_request(-1, 120)
        
        # ListBox for localities
        self.localities_listbox = Gtk.ListBox()
        self.localities_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        localities_scroll.add(self.localities_listbox)
        
        # Empty state for list
        self.localities_empty_label = Gtk.Label()
        self.localities_empty_label.set_markup(
            "<i>No localities selected</i>\n\n"
            "Right-click a transition and select\n"
            "<b>Add to Viability Analysis</b>"
        )
        self.localities_empty_label.set_justify(Gtk.Justification.CENTER)
        self.localities_listbox.set_placeholder(self.localities_empty_label)
        
        localities_box.pack_start(localities_scroll, True, True, 0)
        
        # Buttons row
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        buttons_box.set_margin_top(5)
        
        self.diagnose_button = Gtk.Button(label="Diagnose Selected")
        self.diagnose_button.connect("clicked", self._on_diagnose_clicked)
        self.diagnose_button.set_sensitive(False)
        buttons_box.pack_start(self.diagnose_button, True, True, 0)
        
        clear_button = Gtk.Button(label="Clear All")
        clear_button.connect("clicked", self._on_clear_all_clicked)
        buttons_box.pack_start(clear_button, False, False, 0)
        
        localities_box.pack_start(buttons_box, False, False, 0)
        localities_frame.add(localities_box)
        main_box.pack_start(localities_frame, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(10)
        main_box.pack_start(sep, False, False, 0)
        
        # === SIMULATION CONTROLS (NEW) ===
        self.simulation_toolbar = SimulationControlToolbar()
        main_box.pack_start(self.simulation_toolbar, False, False, 0)
        
        # Connect simulation control signals
        self.simulation_toolbar.run_button.connect("clicked", self._on_run_simulation)
        self.simulation_toolbar.step_button.connect("clicked", self._on_step_simulation)
        self.simulation_toolbar.pause_button.connect("clicked", self._on_pause_simulation)
        self.simulation_toolbar.stop_button.connect("clicked", self._on_stop_simulation)
        self.simulation_toolbar.reset_button.connect("clicked", self._on_reset_simulation)
        
        # Connect experiment management signals
        self.simulation_toolbar.add_exp_button.connect("clicked", self._on_add_experiment)
        self.simulation_toolbar.copy_exp_button.connect("clicked", self._on_copy_experiment)
        self.simulation_toolbar.save_exp_button.connect("clicked", self._on_save_experiments)
        self.simulation_toolbar.load_exp_button.connect("clicked", self._on_load_experiments)
        self.simulation_toolbar.experiment_combo.connect("changed", self._on_experiment_changed)
        
        # === SECTION 2: SUBNET PARAMETERS EXPANDER ===
        self.subnet_expander = Gtk.Expander()
        self.subnet_expander.set_expanded(True)
        self.subnet_expander.set_margin_start(10)
        self.subnet_expander.set_margin_end(10)
        self.subnet_expander.set_margin_top(10)
        
        subnet_label = Gtk.Label()
        subnet_label.set_xalign(0)
        subnet_label.set_markup("<b>SUBNET PARAMETERS</b>")
        self.subnet_expander.set_label_widget(subnet_label)
        
        # Subnet parameters notebook (tabs for Places, Transitions, Arcs)
        self.subnet_notebook = Gtk.Notebook()
        self.subnet_notebook.set_margin_start(12)
        self.subnet_notebook.set_margin_top(6)
        self.subnet_notebook.set_margin_bottom(6)
        
        # Places tab with editable TreeView
        places_scroll = Gtk.ScrolledWindow()
        places_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        places_scroll.set_size_request(-1, 200)
        
        self.places_treeview, self.places_store = self._create_places_treeview()
        places_scroll.add(self.places_treeview)
        self.subnet_notebook.append_page(places_scroll, Gtk.Label(label="Places"))
        
        # Transitions tab with editable TreeView
        transitions_scroll = Gtk.ScrolledWindow()
        transitions_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        transitions_scroll.set_size_request(-1, 200)
        
        self.transitions_treeview, self.transitions_store = self._create_transitions_treeview()
        transitions_scroll.add(self.transitions_treeview)
        self.subnet_notebook.append_page(transitions_scroll, Gtk.Label(label="Transitions"))
        
        # Arcs tab with editable TreeView
        arcs_scroll = Gtk.ScrolledWindow()
        arcs_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        arcs_scroll.set_size_request(-1, 200)
        
        self.arcs_treeview, self.arcs_store = self._create_arcs_treeview()
        arcs_scroll.add(self.arcs_treeview)
        self.subnet_notebook.append_page(arcs_scroll, Gtk.Label(label="Arcs"))
        
        # Results tab with simulation results (NEW)
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        results_scroll.set_size_request(-1, 200)
        
        self.results_treeview, self.results_store = self._create_results_treeview()
        results_scroll.add(self.results_treeview)
        self.subnet_notebook.append_page(results_scroll, Gtk.Label(label="Results"))
        
        self.subnet_expander.add(self.subnet_notebook)
        main_box.pack_start(self.subnet_expander, False, False, 0)
        
        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(10)
        main_box.pack_start(sep2, False, False, 0)
        
        # === DIAGNOSTICS LOG (NEW) ===
        self.diagnostics_expander = Gtk.Expander()
        self.diagnostics_expander.set_expanded(True)
        self.diagnostics_expander.set_margin_start(10)
        self.diagnostics_expander.set_margin_end(10)
        self.diagnostics_expander.set_margin_top(10)
        
        diag_label = Gtk.Label()
        diag_label.set_xalign(0)
        diag_label.set_markup("<b>SIMULATION LOG</b>")
        self.diagnostics_expander.set_label_widget(diag_label)
        
        diag_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        diag_box.set_margin_start(12)
        diag_box.set_margin_top(6)
        diag_box.set_margin_bottom(6)
        
        # Scrolled TextView for log
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_size_request(-1, 150)
        log_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.diagnostics_textview = Gtk.TextView()
        self.diagnostics_textview.set_editable(False)
        self.diagnostics_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.diagnostics_textview.set_monospace(True)
        self.diagnostics_textbuffer = self.diagnostics_textview.get_buffer()
        log_scroll.add(self.diagnostics_textview)
        diag_box.pack_start(log_scroll, True, True, 0)
        
        # Clear log button
        clear_log_btn = Gtk.Button(label="Clear Log")
        clear_log_btn.connect("clicked", self._on_clear_diagnostics_log)
        diag_box.pack_start(clear_log_btn, False, False, 0)
        
        self.diagnostics_expander.add(diag_box)
        main_box.pack_start(self.diagnostics_expander, False, False, 0)
        
        # Separator
        sep3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep3.set_margin_top(10)
        main_box.pack_start(sep3, False, False, 0)
        
        # === SECTION 3: DIAGNOSIS SUMMARY EXPANDER ===
        self.summary_expander = Gtk.Expander()
        self.summary_expander.set_expanded(False)
        self.summary_expander.set_margin_start(10)
        self.summary_expander.set_margin_end(10)
        self.summary_expander.set_margin_top(10)
        
        summary_label = Gtk.Label()
        summary_label.set_xalign(0)
        summary_label.set_markup("<b>DIAGNOSIS SUMMARY</b>")
        self.summary_expander.set_label_widget(summary_label)
        
        # Summary content
        self.summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.summary_box.set_margin_start(12)
        self.summary_box.set_margin_top(6)
        self.summary_box.set_margin_bottom(6)
        
        summary_placeholder = Gtk.Label(label="Run diagnosis to see summary")
        summary_placeholder.set_xalign(0)
        summary_placeholder.get_style_context().add_class("dim-label")
        self.summary_box.pack_start(summary_placeholder, False, False, 0)
        
        self.summary_expander.add(self.summary_box)
        main_box.pack_start(self.summary_expander, False, False, 0)
        
        # === SECTION 4: STRUCTURAL SUGGESTIONS EXPANDER ===
        self.structural_expander = Gtk.Expander()
        self.structural_expander.set_expanded(False)
        self.structural_expander.set_margin_start(10)
        self.structural_expander.set_margin_end(10)
        self.structural_expander.set_margin_top(6)
        
        structural_label = Gtk.Label()
        structural_label.set_xalign(0)
        structural_label.set_markup("<b>STRUCTURAL SUGGESTIONS</b>")
        self.structural_expander.set_label_widget(structural_label)
        
        # Structural content - TreeView
        structural_scroll = Gtk.ScrolledWindow()
        structural_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        structural_scroll.set_size_request(-1, 200)
        structural_scroll.set_margin_start(12)
        structural_scroll.set_margin_top(6)
        structural_scroll.set_margin_bottom(6)
        
        self.structural_treeview, self.structural_store = self._create_suggestions_treeview()
        structural_scroll.add(self.structural_treeview)
        self.structural_expander.add(structural_scroll)
        main_box.pack_start(self.structural_expander, False, False, 0)
        
        # === SECTION 5: BIOLOGICAL SUGGESTIONS EXPANDER ===
        self.biological_expander = Gtk.Expander()
        self.biological_expander.set_expanded(False)
        self.biological_expander.set_margin_start(10)
        self.biological_expander.set_margin_end(10)
        self.biological_expander.set_margin_top(6)
        
        biological_label = Gtk.Label()
        biological_label.set_xalign(0)
        biological_label.set_markup("<b>BIOLOGICAL SUGGESTIONS</b>")
        self.biological_expander.set_label_widget(biological_label)
        
        # Biological content - TreeView
        biological_scroll = Gtk.ScrolledWindow()
        biological_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        biological_scroll.set_size_request(-1, 200)
        biological_scroll.set_margin_start(12)
        biological_scroll.set_margin_top(6)
        biological_scroll.set_margin_bottom(6)
        
        self.biological_treeview, self.biological_store = self._create_suggestions_treeview()
        biological_scroll.add(self.biological_treeview)
        self.biological_expander.add(biological_scroll)
        main_box.pack_start(self.biological_expander, False, False, 0)
        
        # === SECTION 6: KINETIC SUGGESTIONS EXPANDER ===
        self.kinetic_expander = Gtk.Expander()
        self.kinetic_expander.set_expanded(False)
        self.kinetic_expander.set_margin_start(10)
        self.kinetic_expander.set_margin_end(10)
        self.kinetic_expander.set_margin_top(6)
        self.kinetic_expander.set_margin_bottom(10)
        
        kinetic_label = Gtk.Label()
        kinetic_label.set_xalign(0)
        kinetic_label.set_markup("<b>KINETIC SUGGESTIONS</b>")
        self.kinetic_expander.set_label_widget(kinetic_label)
        
        # Kinetic content - TreeView
        kinetic_scroll = Gtk.ScrolledWindow()
        kinetic_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        kinetic_scroll.set_size_request(-1, 200)
        kinetic_scroll.set_margin_start(12)
        kinetic_scroll.set_margin_top(6)
        kinetic_scroll.set_margin_bottom(6)
        
        self.kinetic_treeview, self.kinetic_store = self._create_suggestions_treeview()
        kinetic_scroll.add(self.kinetic_treeview)
        self.kinetic_expander.add(kinetic_scroll)
        main_box.pack_start(self.kinetic_expander, False, False, 0)
        
        # Add main box to scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.add(main_box)
        
        self.pack_start(self.scrolled_window, True, True, 0)
        
        # Track selected localities
        self.selected_localities = {}  # {transition_id: {'row': GtkListBoxRow, 'checkbox': GtkCheckButton, 'transition': TransitionKnowledge}}
    
    def _create_suggestions_treeview(self):
        """Create TreeView for displaying suggestions.
        
        Columns: Priority, Issue, Suggestion, Confidence
        
        Returns:
            tuple: (TreeView, ListStore)
        """
        # Create ListStore: priority (str), issue (str), suggestion (str), confidence (str)
        store = Gtk.ListStore(str, str, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        treeview.set_search_column(2)  # Search in suggestion column
        
        # Column 0: Priority
        renderer_priority = Gtk.CellRendererText()
        column_priority = Gtk.TreeViewColumn("Priority", renderer_priority, text=0)
        column_priority.set_resizable(True)
        column_priority.set_sort_column_id(0)
        column_priority.set_min_width(80)
        treeview.append_column(column_priority)
        
        # Column 1: Issue
        renderer_issue = Gtk.CellRendererText()
        renderer_issue.set_property("wrap-mode", Pango.WrapMode.WORD)
        renderer_issue.set_property("wrap-width", 200)
        column_issue = Gtk.TreeViewColumn("Issue", renderer_issue, text=1)
        column_issue.set_resizable(True)
        column_issue.set_sort_column_id(1)
        column_issue.set_expand(True)
        column_issue.set_min_width(200)
        treeview.append_column(column_issue)
        
        # Column 2: Suggestion
        renderer_suggestion = Gtk.CellRendererText()
        renderer_suggestion.set_property("wrap-mode", Pango.WrapMode.WORD)
        renderer_suggestion.set_property("wrap-width", 300)
        column_suggestion = Gtk.TreeViewColumn("Suggestion", renderer_suggestion, text=2)
        column_suggestion.set_resizable(True)
        column_suggestion.set_sort_column_id(2)
        column_suggestion.set_expand(True)
        column_suggestion.set_min_width(300)
        treeview.append_column(column_suggestion)
        
        # Column 3: Confidence
        renderer_confidence = Gtk.CellRendererText()
        column_confidence = Gtk.TreeViewColumn("Confidence", renderer_confidence, text=3)
        column_confidence.set_resizable(True)
        column_confidence.set_sort_column_id(3)
        column_confidence.set_min_width(100)
        treeview.append_column(column_confidence)
        
        return treeview, store
    
    def _create_places_treeview(self):
        """Create TreeView for editing place parameters.
        
        Columns: ID, Name, Marking (editable), Type, Label
        """
        # Create ListStore: id, name, marking (int, editable), type, label
        store = Gtk.ListStore(str, str, int, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        treeview.set_search_column(1)
        
        # Column 0: ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=0)
        column_id.set_resizable(True)
        column_id.set_min_width(60)
        treeview.append_column(column_id)
        
        # Column 1: Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Name", renderer_name, text=1)
        column_name.set_resizable(True)
        column_name.set_min_width(100)
        treeview.append_column(column_name)
        
        # Column 2: Marking (EDITABLE)
        renderer_marking = Gtk.CellRendererText()
        renderer_marking.set_property("editable", True)
        renderer_marking.connect("edited", self._on_place_marking_edited, store)
        column_marking = Gtk.TreeViewColumn("Marking", renderer_marking, text=2)
        column_marking.set_resizable(True)
        column_marking.set_min_width(80)
        treeview.append_column(column_marking)
        
        # Column 3: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=3)
        column_type.set_resizable(True)
        column_type.set_min_width(100)
        treeview.append_column(column_type)
        
        # Column 4: Label
        renderer_label = Gtk.CellRendererText()
        column_label = Gtk.TreeViewColumn("Label", renderer_label, text=4)
        column_label.set_resizable(True)
        column_label.set_expand(True)
        column_label.set_min_width(150)
        treeview.append_column(column_label)
        
        return treeview, store
    
    def _create_transitions_treeview(self):
        """Create TreeView for editing transition parameters.
        
        Columns: ID, Name, Rate (editable), Formula (editable), Type, Label
        """
        # Create ListStore: id, name, rate (float, editable), formula (str, editable), type, label
        store = Gtk.ListStore(str, str, float, str, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        treeview.set_search_column(1)
        
        # Column 0: ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=0)
        column_id.set_resizable(True)
        column_id.set_min_width(60)
        treeview.append_column(column_id)
        
        # Column 1: Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Name", renderer_name, text=1)
        column_name.set_resizable(True)
        column_name.set_min_width(100)
        treeview.append_column(column_name)
        
        # Column 2: Rate (EDITABLE)
        renderer_rate = Gtk.CellRendererText()
        renderer_rate.set_property("editable", True)
        renderer_rate.connect("edited", self._on_transition_rate_edited, store)
        column_rate = Gtk.TreeViewColumn("Rate", renderer_rate, text=2)
        column_rate.set_resizable(True)
        column_rate.set_min_width(80)
        treeview.append_column(column_rate)
        
        # Column 3: Formula (EDITABLE)
        renderer_formula = Gtk.CellRendererText()
        renderer_formula.set_property("editable", True)
        renderer_formula.connect("edited", self._on_transition_formula_edited, store)
        column_formula = Gtk.TreeViewColumn("Formula", renderer_formula, text=3)
        column_formula.set_resizable(True)
        column_formula.set_expand(True)
        column_formula.set_min_width(200)
        treeview.append_column(column_formula)
        
        # Column 4: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=4)
        column_type.set_resizable(True)
        column_type.set_min_width(100)
        treeview.append_column(column_type)
        
        # Column 5: Label
        renderer_label = Gtk.CellRendererText()
        column_label = Gtk.TreeViewColumn("Label", renderer_label, text=5)
        column_label.set_resizable(True)
        column_label.set_min_width(150)
        treeview.append_column(column_label)
        
        return treeview, store
    
    def _create_arcs_treeview(self):
        """Create TreeView for editing arc parameters.
        
        Columns: ID, From, To, Weight (editable), Type
        """
        # Create ListStore: id, from_id, to_id, weight (int, editable), arc_type
        store = Gtk.ListStore(str, str, str, int, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        
        # Column 0: ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=0)
        column_id.set_resizable(True)
        column_id.set_min_width(80)
        treeview.append_column(column_id)
        
        # Column 1: From
        renderer_from = Gtk.CellRendererText()
        column_from = Gtk.TreeViewColumn("From", renderer_from, text=1)
        column_from.set_resizable(True)
        column_from.set_min_width(100)
        treeview.append_column(column_from)
        
        # Column 2: To
        renderer_to = Gtk.CellRendererText()
        column_to = Gtk.TreeViewColumn("To", renderer_to, text=2)
        column_to.set_resizable(True)
        column_to.set_min_width(100)
        treeview.append_column(column_to)
        
        # Column 3: Weight (EDITABLE)
        renderer_weight = Gtk.CellRendererText()
        renderer_weight.set_property("editable", True)
        renderer_weight.connect("edited", self._on_arc_weight_edited, store)
        column_weight = Gtk.TreeViewColumn("Weight", renderer_weight, text=3)
        column_weight.set_resizable(True)
        column_weight.set_min_width(80)
        treeview.append_column(column_weight)
        
        # Column 4: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=4)
        column_type.set_resizable(True)
        column_type.set_expand(True)
        column_type.set_min_width(150)
        treeview.append_column(column_type)
        
        return treeview, store
    
    def _create_results_treeview(self):
        """Create TreeView for simulation results display.
        
        Columns: Element, Initial, Final, Change, Notes
        """
        # Create ListStore: element, initial, final, change, notes
        store = Gtk.ListStore(str, str, str, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(False)
        
        # Column 0: Element
        renderer_elem = Gtk.CellRendererText()
        column_elem = Gtk.TreeViewColumn("Element", renderer_elem, text=0)
        column_elem.set_resizable(True)
        column_elem.set_min_width(150)
        treeview.append_column(column_elem)
        
        # Column 1: Initial
        renderer_init = Gtk.CellRendererText()
        column_init = Gtk.TreeViewColumn("Initial", renderer_init, text=1)
        column_init.set_resizable(True)
        column_init.set_min_width(80)
        treeview.append_column(column_init)
        
        # Column 2: Final
        renderer_final = Gtk.CellRendererText()
        column_final = Gtk.TreeViewColumn("Final", renderer_final, text=2)
        column_final.set_resizable(True)
        column_final.set_min_width(80)
        treeview.append_column(column_final)
        
        # Column 3: Change
        renderer_change = Gtk.CellRendererText()
        column_change = Gtk.TreeViewColumn("Change", renderer_change, text=3)
        column_change.set_resizable(True)
        column_change.set_min_width(80)
        treeview.append_column(column_change)
        
        # Column 4: Notes
        renderer_notes = Gtk.CellRendererText()
        column_notes = Gtk.TreeViewColumn("Notes", renderer_notes, text=4)
        column_notes.set_resizable(True)
        column_notes.set_expand(True)
        column_notes.set_min_width(200)
        treeview.append_column(column_notes)
        
        return treeview, store
    
    def _get_current_model(self):
        """Get THIS panel's canvas manager (which contains the actual rendered objects).
        
        CRITICAL: Returns the canvas manager, NOT a DocumentModel!
        The canvas manager contains the ACTUAL objects being rendered (self.places, self.transitions, self.arcs).
        Calling to_document_model() creates NEW copies and resets colors, so we must work with the manager directly.
        
        IMPORTANT: This method now returns the canvas manager for THIS panel's document,
        not the globally active document. This prevents cross-document state issues.
        
        Returns:
            ModelCanvasManager instance (with .places, .transitions, .arcs attributes) or None
        """
        if not hasattr(self, 'model_canvas') or not self.model_canvas:
            return None
        
        # Use THIS panel's drawing area, not the current one
        if not hasattr(self, 'drawing_area') or not self.drawing_area:
            # FALLBACK: If drawing_area not set, try to get current document
            # This provides backward compatibility for panels created before fix
            try:
                drawing_area = self.model_canvas.get_current_document()
                if drawing_area:
                    # Automatically set it for future calls
                    self.drawing_area = drawing_area
                else:
                    return None
            except:
                return None
        
        drawing_area = self.drawing_area
        
        try:
            # Get canvas manager for THIS panel's document
            # CRITICAL: Return the manager itself, NOT to_document_model()!
            # The manager contains the actual objects being rendered
            if hasattr(self.model_canvas, 'canvas_managers'):
                manager = self.model_canvas.canvas_managers.get(drawing_area)
                if manager:
                    return manager
        except:
            pass
        
        return None
    
    def _get_canvas_manager(self):
        """Get THIS panel's canvas manager (not the currently visible tab).
        
        IMPORTANT: This method now returns the canvas manager for THIS panel's
        document, not the globally active document.
        
        Returns:
            ModelCanvasManager instance or None
        """
        if not hasattr(self, 'model_canvas') or not self.model_canvas:
            return None
        
        # Use THIS panel's drawing area
        if not hasattr(self, 'drawing_area') or not self.drawing_area:
            # FALLBACK: Try to set drawing_area from current document
            try:
                drawing_area = self.model_canvas.get_current_document()
                if drawing_area:
                    self.drawing_area = drawing_area
                else:
                    return None
            except:
                return None
        
        drawing_area = self.drawing_area
        
        try:
            # Get canvas manager for THIS panel's document
            if hasattr(self.model_canvas, 'canvas_managers'):
                return self.model_canvas.canvas_managers.get(self.drawing_area)
        except:
            pass
        
        return None
    
    def _trigger_canvas_redraw(self):
        """Trigger canvas redraw for THIS panel's document.
        
        IMPORTANT: This redraws THIS panel's canvas, not the currently visible one.
        """
        # Get canvas manager for THIS panel and trigger redraw
        canvas_manager = self._get_canvas_manager()
        if canvas_manager and hasattr(canvas_manager, 'mark_needs_redraw'):
            canvas_manager.mark_needs_redraw()
        
        # Queue draw on THIS panel's drawing area
        if hasattr(self, 'drawing_area') and self.drawing_area:
            if hasattr(self.drawing_area, 'queue_draw'):
                self.drawing_area.queue_draw()
    
    def investigate_transition(self, transition_id: str):
        """Add a transition to the localities list for later diagnosis.
        
        Called from right-click context menu: "Add to Viability Analysis"
        Gets transition and locality directly from the model, not from KB.
        
        Args:
            transition_id: ID of transition to add
        """
        print(f"[VIABILITY_INVESTIGATE] 🔍 Adding {transition_id} to panel {id(self)}, drawing_area={id(self.drawing_area) if self.drawing_area else 'None'}")
        print(f"[VIABILITY_INVESTIGATE] 📋 Current localities: {list(self.selected_localities.keys())}")
        
        # Check if already in list
        if transition_id in self.selected_localities:
            self._show_feedback(f"Transition {transition_id} already in list", "warning")
            return
        
        # Get model directly
        model = self._get_current_model()
        if not model:
            self._show_error("No model available")
            return
        
        # Get transition from model
        transition_obj = None
        for t in model.transitions:
            if t.id == transition_id:
                transition_obj = t
                break
        
        if not transition_obj:
            self._show_error(f"Transition {transition_id} not found")
            return
        
        # Add to list (pass the model object, not KB object)
        self._add_transition_to_list(transition_obj)
        
        # Enable diagnose button
        self.diagnose_button.set_sensitive(True)
        
        self._show_feedback(f"Added {transition_id} to analysis list", "info")
    
    def _get_viability_color(self):
        """Get the viability purple color as RGB tuple.
        
        Returns:
            tuple: RGB color tuple (0-1 range)
        """
        import matplotlib.colors as mcolors
        viability_color_hex = '#9b59b6'  # Purple to distinguish from plot panel
        return mcolors.hex2color(viability_color_hex)
    
    def _color_locality_place(self, place_obj):
        """Color a locality place with viability purple border.
        
        Args:
            place_obj: Place object to color
        """
        color_rgb = self._get_viability_color()
        
        # Set border color
        place_obj.border_color = color_rgb
    
    def _color_transition(self, transition_obj):
        """Color a transition with viability purple border and fill.
        
        Args:
            transition_obj: Transition object to color
        """
        color_rgb = self._get_viability_color()
        
        # Set border and fill color
        transition_obj.border_color = color_rgb
        transition_obj.fill_color = color_rgb
    
    def _color_arc(self, arc_obj):
        """Color an arc with viability purple.
        
        Args:
            arc_obj: Arc object to color
        """
        color_rgb = self._get_viability_color()
        
        # Set arc color
        arc_obj.color = color_rgb
    
    def _add_transition_to_list(self, transition_obj):
        """Add a transition to the localities list (matching plot panel style).
        
        Adds transition as main row, then input/output places as indented child rows,
        exactly like the dynamic analyses plot panel shows transitions with localities.
        
        Args:
            transition_obj: Transition object from the model (not KB)
        """
        # Get current model dynamically
        model = self._get_current_model()
        if not model:
            self._show_error("No model loaded")
            return
        
        # Use LocalityDetector to get locality (same as plot panel)
        from shypn.diagnostic import LocalityDetector
        locality_detector = LocalityDetector(model)
        locality = locality_detector.get_locality_for_transition(transition_obj)
        
        # === COLOR ALL LOCALITY OBJECTS FIRST ===
        
        # Color transition
        self._color_transition(transition_obj)
        
        # Color input places
        for place_obj in locality.input_places:
            self._color_locality_place(place_obj)
        
        # Color output places
        for place_obj in locality.output_places:
            self._color_locality_place(place_obj)
        
        # Color input arcs
        for arc_obj in locality.input_arcs:
            self._color_arc(arc_obj)
        
        # Color output arcs
        for arc_obj in locality.output_arcs:
            self._color_arc(arc_obj)
        
        # Trigger single canvas redraw after coloring all locality objects
        self._trigger_canvas_redraw()
        
        # Store locality for this transition
        self._locality_objects[transition_obj.id] = locality
        
        # === MAIN TRANSITION ROW ===
        transition_row = Gtk.ListBoxRow()
        transition_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        transition_hbox.set_margin_start(6)
        transition_hbox.set_margin_end(6)
        transition_hbox.set_margin_top(3)
        transition_hbox.set_margin_bottom(3)
        
        # Checkbox (store transition_id as Python attribute, not GTK data)
        checkbox = Gtk.CheckButton()
        checkbox.set_active(True)
        checkbox.transition_id = transition_obj.id  # Store as Python attribute
        transition_hbox.pack_start(checkbox, False, False, 0)
        
        # Transition label (ID and optional label)
        label_text = transition_obj.id
        if hasattr(transition_obj, 'label') and transition_obj.label:
            label_text = f"{transition_obj.id} ({transition_obj.label})"
        
        transition_label = Gtk.Label(label=label_text)
        transition_label.set_xalign(0)
        transition_hbox.pack_start(transition_label, True, True, 0)
        
        # Remove button
        remove_btn = Gtk.Button(label="Remove")
        remove_btn.set_relief(Gtk.ReliefStyle.NONE)
        remove_btn.connect("clicked", lambda w: self._remove_transition_from_list(transition_obj.id))
        transition_hbox.pack_start(remove_btn, False, False, 0)
        
        transition_row.add(transition_hbox)
        self.localities_listbox.add(transition_row)
        
        # === INPUT PLACES (INDENTED ROWS) ===
        for place_obj in locality.input_places:
            self._add_locality_place_row_to_list(place_obj, "Input:")
        
        # === OUTPUT PLACES (INDENTED ROWS) ===
        for place_obj in locality.output_places:
            self._add_locality_place_row_to_list(place_obj, "Output:")
        
        # Show all new widgets (only if panel is packed)
        if self.get_parent() is not None:
            self.localities_listbox.show_all()
        
        # Track in dict (store locality IDs for cross-document safety)
        self.selected_localities[transition_obj.id] = {
            'row': transition_row,
            'checkbox': checkbox,
            'transition': transition_obj,
            'locality': locality
        }
        
        # Trigger canvas redraw to show colored elements
        self._trigger_canvas_redraw()
        
        # Refresh subnet parameters display
        self._refresh_subnet_parameters()
        
        # Show (only if panel is packed)
        if self.get_parent() is not None:
            self.localities_listbox.show_all()
    
    def _add_locality_place_row_to_list(self, place, label_prefix):
        """Add a locality place row to the objects list.
        
        Args:
            place: Place object to add
            label_prefix: Prefix string like "← Input:" or "→ Output:"
        """
        place_row = Gtk.ListBoxRow()
        place_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        place_hbox.set_margin_start(40)  # Indent to show hierarchy
        place_hbox.set_margin_end(6)
        place_hbox.set_margin_top(1)
        place_hbox.set_margin_bottom(1)
        
        # Checkbox for place (checked by default)
        place_checkbox = Gtk.CheckButton()
        place_checkbox.set_active(True)
        place_checkbox.place_id = place.id  # Store as Python attribute
        place_hbox.pack_start(place_checkbox, False, False, 0)
        
        # Place label
        place_name = place.name if hasattr(place, 'name') else place.id
        place_label_text = f"{label_prefix} {place_name}"
        
        # Add marking/tokens if available
        if hasattr(place, 'marking'):
            place_label_text += f" ({place.marking} tokens)"
        elif hasattr(place, 'tokens'):
            place_label_text += f" ({place.tokens} tokens)"
        
        place_label = Gtk.Label()
        place_label.set_markup(f"<small>{place_label_text}</small>")
        place_label.set_xalign(0)
        place_hbox.pack_start(place_label, True, True, 0)
        
        place_row.add(place_hbox)
        place_row.set_selectable(False)  # Places not selectable
        self.localities_listbox.add(place_row)
    
    def _remove_transition_from_list(self, transition_id):
        """Remove a transition from the localities list.
        
        Args:
            transition_id: ID of transition to remove
        """
        if transition_id not in self.selected_localities:
            return
        
        data = self.selected_localities[transition_id]
        
        # Reset colors - fetch objects from CURRENT model
        from shypn.netobjs import Place, Transition, Arc
        
        # Get current model to fetch fresh object references
        model = self._get_current_model()
        if not model:
            return
        
        locality_obj = self._locality_objects.get(transition_id)
        if locality_obj:
            # Reset transition color
            locality_obj.transition.border_color = Transition.DEFAULT_BORDER_COLOR
            locality_obj.transition.fill_color = Transition.DEFAULT_COLOR
            
            # Reset input place colors
            for p_obj in locality_obj.input_places:
                p_obj.border_color = Place.DEFAULT_BORDER_COLOR
            
            # Reset output place colors
            for p_obj in locality_obj.output_places:
                p_obj.border_color = Place.DEFAULT_BORDER_COLOR
            
            # Reset input arc colors
            for a_obj in locality_obj.input_arcs:
                a_obj.color = Arc.DEFAULT_COLOR
            
            # Reset output arc colors
            for a_obj in locality_obj.output_arcs:
                a_obj.color = Arc.DEFAULT_COLOR
        
        # Remove from tracking and UI
        if transition_id in self._locality_objects:
            del self._locality_objects[transition_id]
        self.localities_listbox.remove(data['row'])
        del self.selected_localities[transition_id]
        
        # Trigger canvas redraw
        self._trigger_canvas_redraw()
        
        # Refresh subnet parameters display
        self._refresh_subnet_parameters()
        
        # Disable diagnose button if list is empty
        if not self.selected_localities:
            self.diagnose_button.set_sensitive(False)
    
    def _refresh_subnet_parameters(self):
        """Refresh subnet parameters tables based on selected localities."""
        # Clear all stores
        self.places_store.clear()
        self.transitions_store.clear()
        self.arcs_store.clear()
        
        # Get current model dynamically
        model = self._get_current_model()
        if not model:
            return
        
        # Collect all unique place IDs, transition IDs, and arc IDs from localities
        all_place_ids = set()
        all_transition_ids = set()
        all_arc_ids = set()
        
        for transition_id, data in self.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            
            # Add transition ID
            all_transition_ids.add(locality.transition_id)
            
            # Add place IDs
            all_place_ids.update(locality.input_places)
            all_place_ids.update(locality.output_places)
            
            # Add arc IDs
            all_arc_ids.update(locality.input_arcs)
            all_arc_ids.update(locality.output_arcs)
        
        # Populate Places table
        for place in model.places:
            if place.id not in all_place_ids:
                continue
            place_obj = place
            place_type = "Source" if hasattr(place_obj, 'is_source') and place_obj.is_source else "Normal"
            label = place_obj.label if hasattr(place_obj, 'label') else ""
            marking = place_obj.marking if hasattr(place_obj, 'marking') else 0
            self.places_store.append([
                place_obj.id,
                place_obj.name if hasattr(place_obj, 'name') else place_obj.id,
                marking,
                place_type,
                label
            ])
        
        # Populate Transitions table
        for transition in model.transitions:
            if transition.id in all_transition_ids:
                rate = transition.rate if hasattr(transition, 'rate') else 1.0
                formula = transition.formula if hasattr(transition, 'formula') else ""
                trans_type = transition.transition_type if hasattr(transition, 'transition_type') else "continuous"
                label = transition.label if hasattr(transition, 'label') else ""
                self.transitions_store.append([
                    transition.id,
                    transition.name if hasattr(transition, 'name') else transition.id,
                    rate,
                    formula,
                    trans_type,
                    label
                ])
        
        # Populate Arcs table
        for arc in model.arcs:
            if arc.id not in all_arc_ids:
                continue
            from shypn.netobjs import Place
            source_id = arc.source.id if hasattr(arc.source, 'id') else str(arc.source)
            target_id = arc.target.id if hasattr(arc.target, 'id') else str(arc.target)
            arc_type = "Place→Transition" if isinstance(arc.source, Place) else "Transition→Place"
            weight = arc.weight if hasattr(arc, 'weight') else 1
            self.arcs_store.append([
                arc.id,
                source_id,
                target_id,
                weight,
                arc_type
            ])
    
    # === EDITING CALLBACKS ===
    
    def _on_place_marking_edited(self, widget, path, new_text, store):
        """Handle place marking edit."""
        try:
            new_marking = int(new_text)
            place_id = store[path][0]
            
            # Update store
            store[path][2] = new_marking
            
            # Update model
            model = self._get_current_model()
            if model:
                for place in model.places:
                    if place.id == place_id:
                        place.marking = new_marking
                        break
        except ValueError:
            pass
    
    def _on_transition_rate_edited(self, widget, path, new_text, store):
        """Handle transition rate edit."""
        try:
            new_rate = float(new_text)
            transition_id = store[path][0]
            
            # Update store
            store[path][2] = new_rate
            
            # Update model
            model = self._get_current_model()
            if model:
                for transition in model.transitions:
                    if transition.id == transition_id:
                        transition.rate = new_rate
                        break
        except ValueError:
            pass
    
    def _on_transition_formula_edited(self, widget, path, new_text, store):
        """Handle transition formula edit."""
        transition_id = store[path][0]
        
        # Update store
        store[path][3] = new_text
        
        # Update model
        model = self._get_current_model()
        if model:
            for transition in model.transitions:
                if transition.id == transition_id:
                    transition.formula = new_text
                    break
    
    def _on_arc_weight_edited(self, widget, path, new_text, store):
        """Handle arc weight edit."""
        try:
            new_weight = int(new_text)
            arc_id = store[path][0]
            
            # Update store
            store[path][3] = new_weight
            
            # Update model
            model = self._get_current_model()
            if model:
                for arc in model.arcs:
                    if arc.id == arc_id:
                        arc.weight = new_weight
                        break
        except ValueError:
            pass
    
    def _run_analysis_pipeline(self, transition):
        """Run the full analysis pipeline on a transition.
        
        Args:
            transition: TransitionKnowledge object
        
        Returns:
            List of Issue objects
        """
        # Initialize data puller if needed
        if not hasattr(self, 'data_puller') or self.data_puller is None:
            kb = self._get_kb()
            self.data_puller = DataPuller(kb, simulation=self._get_simulation())
        
        cached_puller = CachedDataPuller(self.data_puller, self.data_cache)
        
        # Initialize analyzers (no parameters)
        locality_analyzer = LocalityAnalyzer()
        dependency_analyzer = DependencyAnalyzer()
        boundary_analyzer = BoundaryAnalyzer()
        conservation_analyzer = ConservationAnalyzer()
        
        # Build context for analysis
        kb = self._get_kb()
        sim_data = cached_puller.get_simulation_data() if hasattr(cached_puller, 'get_simulation_data') else None
        
        # Get current model dynamically
        model = self._get_current_model()
        if not model:
            return [], []
        
        # Get transition object from model
        transition_obj = None
        for t in model.transitions:
            if t.id == transition.transition_id:
                transition_obj = t
                break
        
        if not transition_obj:
            return [], []
        
        # Use LocalityDetector to get locality (same approach as _add_transition_to_list)
        from shypn.diagnostic import LocalityDetector
        locality_detector = LocalityDetector(model)
        locality = locality_detector.get_locality_for_transition(transition_obj)
        
        context = {
            'transition': transition,
            'locality': locality,
            'kb': kb,
            'sim_data': sim_data,
            'data_puller': cached_puller
        }
        
        all_issues = []
        
        # Level 1: Locality Analysis
        try:
            locality_issues = locality_analyzer.analyze(context)
            all_issues.extend(locality_issues)
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
        
        # Level 2: Dependency Analysis (requires context of nearby transitions)
        # TODO: Implement when subnet building is ready
        
        # Level 3: Boundary Analysis
        try:
            boundary_issues = boundary_analyzer.analyze(context)
            all_issues.extend(boundary_issues)
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
        
        # Level 4: Conservation Analysis
        try:
            conservation_issues = conservation_analyzer.analyze(context)
            all_issues.extend(conservation_issues)
        except Exception as e:
            import traceback
            traceback.print_exc()
        return all_issues
    
    def _generate_suggestions_from_issues(self, issues, transition):
        """Generate suggestions from issues.
        
        Args:
            issues: List of Issue objects
            transition: TransitionKnowledge object
        
        Returns:
            List of Suggestion objects
        """
        
        # Initialize data puller if needed
        if not hasattr(self, 'data_puller') or self.data_puller is None:
            kb = self._get_kb()
            self.data_puller = DataPuller(kb, simulation=self._get_simulation())
        
        cached_puller = CachedDataPuller(self.data_puller, self.data_cache)
        
        # Use analyzers to generate suggestions (no data_puller parameter)
        locality_analyzer = LocalityAnalyzer()
        boundary_analyzer = BoundaryAnalyzer()
        conservation_analyzer = ConservationAnalyzer()
        
        # Build context
        kb = self._get_kb()
        sim_data = cached_puller.get_simulation_data() if hasattr(cached_puller, 'get_simulation_data') else None
        
        context = {
            'transition': transition,
            'kb': kb,
            'sim_data': sim_data,
            'data_puller': cached_puller
        }
        
        all_suggestions = []
        
        # Group issues by type/analyzer
        for issue in issues:
            try:
                # Determine which analyzer to use based on issue category
                analyzer_name = None
                if 'locality' in issue.message.lower() or 'structural' in issue.category.lower():
                    analyzer_name = 'locality'
                    suggestions = locality_analyzer.generate_suggestions([issue], context)
                elif 'boundary' in issue.message.lower():
                    analyzer_name = 'boundary'
                    suggestions = boundary_analyzer.generate_suggestions([issue], context)
                elif 'conservation' in issue.message.lower():
                    analyzer_name = 'conservation'
                    suggestions = conservation_analyzer.generate_suggestions([issue], context)
                else:
                    # Default to locality analyzer
                    analyzer_name = 'locality (default)'
                    suggestions = locality_analyzer.generate_suggestions([issue], context)
                all_suggestions.extend(suggestions)
            except Exception as e:
                import traceback
                traceback.print_exc()
        
        return all_suggestions
    
    def _show_investigation_view(self):
        """Show investigation results in UI."""
        
        if not self.current_investigation:
            return
        
        # Remove empty state
        if self.empty_label in self.content_box.get_children():
            self.content_box.remove(self.empty_label)
        
        # Remove old view if exists
        if self.current_view and self.current_view in self.content_box.get_children():
            self.content_box.remove(self.current_view)
        
        # FOR NOW: Always use simple fallback view since Investigation dataclass
        # structure doesn't match what InvestigationView/SubnetView expect
        self.current_view = self._create_simple_results_view()
        
        self.content_box.pack_start(self.current_view, True, True, 0)
        
        # Make everything visible (only if panel is packed)
        if self.get_parent() is not None:
            self.current_view.show_all()
            self.content_box.show_all()
            self.scrolled_window.show_all()
            self.show_all()
        
        # Force queue draw
        self.queue_draw()
        self.content_box.queue_draw()
        self.scrolled_window.queue_draw()
        
        # Check visibility
    
    def _create_simple_results_view(self):
        """Create simple fallback view showing investigation results.
        
        Returns:
            Gtk.Box with simple text results
        """
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Title
        title = Gtk.Label()
        title.set_markup(f"<b>Investigation: {self.current_investigation.root_transition_id}</b>")
        title.set_halign(Gtk.Align.START)
        box.pack_start(title, False, False, 0)
        
        # Subnet info
        subnet_info = Gtk.Label()
        subnet_info.set_markup(
            f"<small>Transitions: {len(self.current_investigation.subnet.transitions)}, "
            f"Places: {len(self.current_investigation.subnet.places)}</small>"
        )
        subnet_info.set_halign(Gtk.Align.START)
        box.pack_start(subnet_info, False, False, 0)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 5)
        
        # Suggestions
        suggestions_label = Gtk.Label()
        suggestions_label.set_markup(f"<b>Suggestions ({len(self.current_investigation.suggestions)})</b>")
        suggestions_label.set_halign(Gtk.Align.START)
        box.pack_start(suggestions_label, False, False, 0)
        
        if not self.current_investigation.suggestions:
            no_suggestions = Gtk.Label()
            no_suggestions.set_markup("<i>No suggestions generated</i>")
            no_suggestions.set_halign(Gtk.Align.START)
            box.pack_start(no_suggestions, False, False, 0)
        else:
            # Scrolled window for suggestions
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_vexpand(True)
            
            suggestions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            
            for i, suggestion in enumerate(self.current_investigation.suggestions, 1):
                suggestion_frame = Gtk.Frame()
                suggestion_frame.set_margin_bottom(5)
                
                suggestion_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                suggestion_content.set_margin_start(10)
                suggestion_content.set_margin_end(10)
                suggestion_content.set_margin_top(10)
                suggestion_content.set_margin_bottom(10)
                
                # Suggestion header
                header = Gtk.Label()
                header.set_markup(f"<b>{i}. {suggestion.action}</b>")
                header.set_halign(Gtk.Align.START)
                header.set_line_wrap(True)
                suggestion_content.pack_start(header, False, False, 0)
                
                # Category and target (handle both old and new Suggestion formats)
                info = Gtk.Label()
                target = getattr(suggestion, 'target_element_id', None) or suggestion.parameters.get('transition_id', 'N/A')
                info.set_markup(
                    f"<small>Category: {suggestion.category} | "
                    f"Target: {target}</small>"
                )
                info.set_halign(Gtk.Align.START)
                suggestion_content.pack_start(info, False, False, 0)
                
                # Impact/Message (handle both formats)
                impact_text = getattr(suggestion, 'impact', None) or getattr(suggestion, 'message', 'No description')
                impact = Gtk.Label()
                impact.set_markup(f"<i>{impact_text}</i>")
                impact.set_halign(Gtk.Align.START)
                impact.set_line_wrap(True)
                suggestion_content.pack_start(impact, False, False, 0)
                
                # Buttons
                button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                button_box.set_margin_top(5)
                
                apply_btn = Gtk.Button(label="Apply")
                apply_btn.connect("clicked", lambda w, s=suggestion: self._on_apply_fix(s))
                button_box.pack_start(apply_btn, False, False, 0)
                
                preview_btn = Gtk.Button(label="Preview")
                preview_btn.connect("clicked", lambda w, s=suggestion: self._on_preview_fix(s))
                button_box.pack_start(preview_btn, False, False, 0)
                
                suggestion_content.pack_start(button_box, False, False, 0)
                
                suggestion_frame.add(suggestion_content)
                suggestions_box.pack_start(suggestion_frame, False, False, 0)
            
            scrolled.add(suggestions_box)
            box.pack_start(scrolled, True, True, 0)
        
        return box
    
    def _on_apply_fix(self, suggestion):
        """Apply a fix suggestion.
        
        Args:
            suggestion: Suggestion to apply
        """
        try:
            applied_fix = self.fix_applier.apply(suggestion)
            
            # Invalidate cache after model change
            self.data_cache.invalidate_pattern('*')
            
            # Update UI
            if self.current_view:
                self.current_view.mark_applied(suggestion.id if hasattr(suggestion, 'id') else None)
            
            # Show success feedback
            self._show_feedback(f"Applied: {suggestion.action}", "success")
            
        except Exception as e:
            self._show_error(f"Failed to apply fix: {e}")
    
    def _on_preview_fix(self, suggestion):
        """Preview a fix suggestion.
        
        Args:
            suggestion: Suggestion to preview
        """
        try:
            prediction = self.fix_predictor.predict(suggestion)
            
            # Show prediction dialog
            self._show_prediction_dialog(prediction)
            
        except Exception as e:
            self._show_error(f"Failed to preview fix: {e}")
    
    def _on_revert_fix(self, applied_fix):
        """Revert an applied fix.
        
        Args:
            applied_fix: AppliedFix to revert
        """
        try:
            self.fix_applier.revert(applied_fix)
            
            # Invalidate cache
            self.data_cache.invalidate_pattern('*')
            
            # Update UI
            if self.current_view:
                self.current_view.mark_reverted(applied_fix)
            
            # Show success feedback
            self._show_feedback("Fix reverted", "info")
            
        except Exception as e:
            self._show_error(f"Failed to revert fix: {e}")
    
    def _show_prediction_dialog(self, prediction):
        """Show fix prediction dialog.
        
        Args:
            prediction: FixPrediction object
        """
        # Get proper window parent
        parent = None
        toplevel = self.get_toplevel()
        if toplevel and isinstance(toplevel, Gtk.Window):
            parent = toplevel
        
        dialog = Gtk.Dialog(
            title="Fix Preview",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.set_default_size(500, 400)
        
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        
        # Impact level
        impact_label = Gtk.Label()
        impact_label.set_markup(f"<b>Impact:</b> {prediction.impact_level.value}")
        impact_label.set_halign(Gtk.Align.START)
        content.pack_start(impact_label, False, False, 0)
        
        # Risk level
        risk_label = Gtk.Label()
        risk_label.set_markup(f"<b>Risk:</b> {prediction.risk_level}")
        risk_label.set_halign(Gtk.Align.START)
        content.pack_start(risk_label, False, False, 0)
        
        # Changes
        changes_label = Gtk.Label()
        changes_label.set_markup(f"<b>Changes:</b>")
        changes_label.set_halign(Gtk.Align.START)
        content.pack_start(changes_label, False, False, 0)
        
        # Create scrolled view for changes
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        changes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        for change in prediction.get_all_changes():
            change_label = Gtk.Label()
            change_label.set_markup(f"• {change.description}")
            change_label.set_halign(Gtk.Align.START)
            change_label.set_line_wrap(True)
            changes_box.pack_start(change_label, False, False, 0)
        
        scrolled.add(changes_box)
        content.pack_start(scrolled, True, True, 0)
        
        # Warnings
        if prediction.has_warnings():
            warnings_label = Gtk.Label()
            warnings_label.set_markup(f"<b>Warnings:</b>")
            warnings_label.set_halign(Gtk.Align.START)
            content.pack_start(warnings_label, False, False, 0)
            
            for warning in prediction.warnings:
                warning_label = Gtk.Label()
                warning_label.set_markup(f"• {warning}")
                warning_label.set_halign(Gtk.Align.START)
                warning_label.set_line_wrap(True)
                changes_box.pack_start(warning_label, False, False, 0)
        
        # Buttons
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        
        content.show_all()
        dialog.run()
        dialog.destroy()
    
    def _show_feedback(self, message: str, level: str = "info"):
        """Show feedback message to user.
        
        Args:
            message: Message to show
            level: "info", "success", "warning", "error"
        """
        # TODO: Implement proper feedback UI (toast/notification)
        print(f"[{level.upper()}] {message}")
    
    def _show_error(self, message: str):
        """Show error message.
        
        Args:
            message: Error message
        """
        print(f"[VIABILITY_PANEL ERROR] {message}")
        
        # Get proper window parent
        parent = None
        toplevel = self.get_toplevel()
        if toplevel and isinstance(toplevel, Gtk.Window):
            parent = toplevel
        
        # Show as warning dialog instead of error (less alarming during development)
        dialog = Gtk.MessageDialog(
            parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text="Viability Analysis Issue"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _get_kb(self):
        """Get THIS panel's knowledge base (not the currently visible tab).
        
        IMPORTANT: This returns the KB for THIS panel's document,
        not the globally active document.
        
        Returns:
            ModelKnowledgeBase instance or None
        """
        if not hasattr(self, 'model_canvas') or not self.model_canvas:
            return None
        
        # Use THIS panel's drawing area to get the correct KB
        if not hasattr(self, 'drawing_area') or not self.drawing_area:
            # FALLBACK: Try to set drawing_area from current document
            try:
                drawing_area = self.model_canvas.get_current_document()
                if drawing_area:
                    self.drawing_area = drawing_area
                else:
                    return None
            except:
                return None
        
        drawing_area = self.drawing_area
        
        try:
            # Get KB for THIS panel's document
            if hasattr(self.model_canvas, 'knowledge_bases'):
                return self.model_canvas.knowledge_bases.get(self.drawing_area)
        except:
            pass
        
        return None
    
    def _populate_kb_from_model(self, kb):
        """Populate KB from current model if empty.
        
        Args:
            kb: Knowledge base instance to populate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current model using the proper accessor
            model = self._get_current_model()
            
            if not model:
                return False
            
            # Extract data from model
            places_data = []
            transitions_data = []
            arcs_data = []
            
            # Places
            if hasattr(model, 'places') and model.places:
                places_data = [p for p in model.places if p]
            
            # Transitions
            if hasattr(model, 'transitions') and model.transitions:
                transitions_data = [t for t in model.transitions if t]
            
            # Arcs
            if hasattr(model, 'arcs') and model.arcs:
                arcs_data = [a for a in model.arcs if a]
            
            if not transitions_data:
                return False
            
            # Populate KB
            kb.update_topology_structural(places_data, transitions_data, arcs_data)
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def _get_simulation(self):
        """Get current simulation instance.
        
        Returns:
            Simulation or None
        """
        # Try to get simulation from model_canvas
        if not self.model_canvas or not hasattr(self, 'drawing_area'):
            return None
        
        controller = self.model_canvas.simulation_controllers.get(self.drawing_area)
        return controller if controller else None
    
    # === Compatibility methods for existing interface ===
    
    def set_topology_panel(self, topology_panel):
        """Set reference to topology panel (compatibility).
        
        Args:
            topology_panel: TopologyPanel instance
        """
        self.topology_panel = topology_panel
    
    def set_analyses_panel(self, analyses_panel):
        """Set reference to analyses panel (compatibility).
        
        Args:
            analyses_panel: AnalysesPanel instance
        """
        self.analyses_panel = analyses_panel
    
    def analyze_locality_for_transition(self, transition_id):
        """Analyze locality for transition (compatibility).
        
        Redirects to new investigate_transition method.
        
        Args:
            transition_id: ID of the transition to analyze
        """
        self.investigate_transition(transition_id)
    
    def on_transition_selected(self, transition, locality):
        """Old interface for transition selection (compatibility).
        
        Args:
            transition: Transition object
            locality: Locality object
        """
        if hasattr(transition, 'id'):
            self.investigate_transition(transition.id)
    
    def _on_diagnose_clicked(self, button):
        """Handle 'Diagnose Selected' button click.
        
        Runs analysis on all checked transitions in the localities list.
        """
        # Get checked transitions
        checked_transitions = []
        for transition_id, data in self.selected_localities.items():
            checkbox = data['checkbox']
            if checkbox.get_active():
                checked_transitions.append(data['transition'])
        
        if not checked_transitions:
            self._show_feedback("No transitions selected for diagnosis", "warning")
            return
        
        # Clear previous results
        self._clear_results()
        
        # Run analysis on each transition
        all_suggestions_by_category = {
            'structural': [],
            'biological': [],
            'kinetic': []
        }
        
        total_issues = 0
        
        for transition in checked_transitions:
            # Run analysis levels
            issues = self._run_analysis_pipeline(transition)
            total_issues += len(issues)
            
            # Generate suggestions from issues
            suggestions = self._generate_suggestions_from_issues(issues, transition)
            
            # Categorize suggestions
            for suggestion in suggestions:
                category = suggestion.category.lower()
                if category in all_suggestions_by_category:
                    all_suggestions_by_category[category].append(suggestion)
        
        # Populate summary
        self._populate_summary(total_issues, all_suggestions_by_category, len(checked_transitions))
        
        # Populate category TreeViews
        self._populate_suggestions_treeview(self.structural_store, all_suggestions_by_category['structural'])
        self._populate_suggestions_treeview(self.biological_store, all_suggestions_by_category['biological'])
        self._populate_suggestions_treeview(self.kinetic_store, all_suggestions_by_category['kinetic'])
        
        # Expand summary expander
        self.summary_expander.set_expanded(True)
        
        # Expand category with most suggestions
        max_category = max(all_suggestions_by_category.items(), key=lambda x: len(x[1]))
        if max_category[1]:  # If there are suggestions
            if max_category[0] == 'structural':
                self.structural_expander.set_expanded(True)
            elif max_category[0] == 'biological':
                self.biological_expander.set_expanded(True)
            elif max_category[0] == 'kinetic':
                self.kinetic_expander.set_expanded(True)
        
        self._show_feedback(f"Diagnosis complete: {total_issues} issues, {sum(len(s) for s in all_suggestions_by_category.values())} suggestions", "info")
    
    def _on_clear_all_clicked(self, button):
        """Handle 'Clear All' button click.
        
        Clears all localities and resets the entire panel state.
        """
        # Reset colors - fetch objects from CURRENT model
        from shypn.netobjs import Place, Transition, Arc
        
        print("[Viability] Clearing all localities and resetting colors...")
        
        # Get current model to fetch fresh object references
        model = self._get_current_model()
        if not model:
            print("[Viability] Warning: No current model when clearing all")
        else:
            for transition_id in self.selected_localities.keys():
                locality_ids = self._locality_objects.get(transition_id)
                if not locality_ids:
                    continue
                
                print(f"  Resetting colors for {transition_id}:")
                
                # Reset transition color
                print(f"    - Transition: {locality_ids.transition.id}")
                locality_ids.transition.border_color = Transition.DEFAULT_BORDER_COLOR
                locality_ids.transition.fill_color = Transition.DEFAULT_COLOR
                
                # Reset input place colors
                for p_obj in locality_ids.input_places:
                    print(f"    - Input place: {p_obj.id}")
                    p_obj.border_color = Place.DEFAULT_BORDER_COLOR
                
                # Reset output place colors
                for p_obj in locality_ids.output_places:
                    print(f"    - Output place: {p_obj.id}")
                    p_obj.border_color = Place.DEFAULT_BORDER_COLOR
                
                # Reset input arc colors
                for arc_obj in locality_ids.input_arcs:
                    print(f"    - Input arc: {arc_obj.id}")
                
                # Reset output arc colors
                for arc_obj in locality_ids.output_arcs:
                    print(f"    - Output arc: {arc_obj.id}")
        
        print("[Viability] All colors reset")
        
        # Clear localities list
        for row in list(self.localities_listbox.get_children()):
            self.localities_listbox.remove(row)
        
        self.selected_localities.clear()
        self._locality_objects.clear()
        
        # Clear subnet parameters tables
        self.places_store.clear()
        self.transitions_store.clear()
        self.arcs_store.clear()
        
        # Clear simulation results
        self.results_store.clear()
        
        # Clear diagnostics log
        self.diagnostics_textbuffer.set_text("")
        
        # Reset simulator
        if self.subnet_simulator.is_initialized():
            self.subnet_simulator.reset()
        
        # Reset toolbar status
        self.simulation_toolbar.set_status("Ready", "ready")
        self.simulation_toolbar.set_running_state(False)
        
        # Disable diagnose button
        self.diagnose_button.set_sensitive(False)
        
        # Clear results
        self._clear_results()
        
        # Trigger canvas redraw to show reset colors
        self._trigger_canvas_redraw()
        
        self._show_feedback("All localities cleared", "info")
    
    def _clear_results(self):
        """Clear all results from summary and suggestion TreeViews."""
        # Clear stores
        self.structural_store.clear()
        self.biological_store.clear()
        self.kinetic_store.clear()
        
        # Clear summary (rebuild placeholder)
        for child in list(self.summary_box.get_children()):
            self.summary_box.remove(child)
        
        summary_placeholder = Gtk.Label(label="Run diagnosis to see summary")
        summary_placeholder.set_xalign(0)
        summary_placeholder.get_style_context().add_class("dim-label")
        self.summary_box.pack_start(summary_placeholder, False, False, 0)
        if self.get_parent() is not None:
            self.summary_box.show_all()
        
        # Collapse all expanders
        self.summary_expander.set_expanded(False)
        self.structural_expander.set_expanded(False)
        self.biological_expander.set_expanded(False)
        self.kinetic_expander.set_expanded(False)
    
    def _populate_summary(self, total_issues, suggestions_by_category, num_transitions):
        """Populate diagnosis summary section.
        
        Args:
            total_issues: Total number of issues found
            suggestions_by_category: Dict of suggestions by category
            num_transitions: Number of transitions analyzed
        """
        # Clear existing content
        for child in list(self.summary_box.get_children()):
            self.summary_box.remove(child)
        
        # Timestamp
        from datetime import datetime
        timestamp_label = Gtk.Label()
        timestamp_label.set_markup(f"<small><i>Diagnosed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i></small>")
        timestamp_label.set_xalign(0)
        timestamp_label.set_margin_bottom(6)
        self.summary_box.pack_start(timestamp_label, False, False, 0)
        
        # Stats
        stats_label = Gtk.Label()
        stats_label.set_markup(
            f"<b>Analyzed:</b> {num_transitions} transition(s)\n"
            f"<b>Issues Found:</b> {total_issues}\n"
            f"<b>Suggestions:</b> {sum(len(s) for s in suggestions_by_category.values())}"
        )
        stats_label.set_xalign(0)
        stats_label.set_margin_bottom(10)
        self.summary_box.pack_start(stats_label, False, False, 0)
        
        # Health bars (simplified - just counts for now)
        structural_count = len(suggestions_by_category.get('structural', []))
        biological_count = len(suggestions_by_category.get('biological', []))
        kinetic_count = len(suggestions_by_category.get('kinetic', []))
        
        health_grid = Gtk.Grid()
        health_grid.set_column_spacing(10)
        health_grid.set_row_spacing(6)
        
        # Structural
        structural_label = Gtk.Label(label="Structural:")
        structural_label.set_xalign(0)
        health_grid.attach(structural_label, 0, 0, 1, 1)
        structural_count_label = Gtk.Label(label=f"{structural_count} suggestion(s)")
        structural_count_label.set_xalign(0)
        health_grid.attach(structural_count_label, 1, 0, 1, 1)
        
        # Biological
        biological_label = Gtk.Label(label="Biological:")
        biological_label.set_xalign(0)
        health_grid.attach(biological_label, 0, 1, 1, 1)
        biological_count_label = Gtk.Label(label=f"{biological_count} suggestion(s)")
        biological_count_label.set_xalign(0)
        health_grid.attach(biological_count_label, 1, 1, 1, 1)
        
        # Kinetic
        kinetic_label = Gtk.Label(label="Kinetic:")
        kinetic_label.set_xalign(0)
        health_grid.attach(kinetic_label, 0, 2, 1, 1)
        kinetic_count_label = Gtk.Label(label=f"{kinetic_count} suggestion(s)")
        kinetic_count_label.set_xalign(0)
        health_grid.attach(kinetic_count_label, 1, 2, 1, 1)
        
        self.summary_box.pack_start(health_grid, False, False, 0)
        if self.get_parent() is not None:
            self.summary_box.show_all()
    
    def _populate_suggestions_treeview(self, store, suggestions):
        """Populate a suggestions TreeView with data.
        
        Args:
            store: Gtk.ListStore to populate
            suggestions: List of Suggestion objects
        """
        store.clear()
        
        for suggestion in suggestions:
            # Extract fields (handle both old and new formats)
            priority = getattr(suggestion, 'priority', 'Medium')
            issue = getattr(suggestion, 'issue_summary', suggestion.action)
            suggestion_text = getattr(suggestion, 'impact', getattr(suggestion, 'message', suggestion.action))
            confidence = getattr(suggestion, 'confidence', 'N/A')
            
            store.append([str(priority), str(issue), str(suggestion_text), str(confidence)])
    
    def add_object_for_analysis(self, obj):
        """Add object for analysis with visual highlight.
        
        This is called from the context menu "Add to Viability Analysis".
        It delegates to investigate_transition which handles:
        - KB lookup
        - Locality detection
        - Full locality coloring (transition + places + arcs)
        - Adding to UI list
        
        Args:
            obj: Place or Transition object
        """
        from shypn.netobjs import Transition, Place
        
        if isinstance(obj, Transition):
            # Add to viability panel - this handles ALL coloring (transition + locality)
            self.investigate_transition(obj.id)
    
    def set_model(self, model):
        """Update model reference (compatibility).
        
        Args:
            model: ShypnModel instance
        """
        self.model = model
    
    def set_model_canvas(self, model_canvas):
        """Update model_canvas reference and model.
        
        Args:
            model_canvas: ModelCanvasLoader instance
        """
        self.model_canvas = model_canvas
        
        # Update model reference from current drawing area
        if self.model_canvas and hasattr(self, 'drawing_area') and self.drawing_area:
            overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
            if overlay_manager and hasattr(overlay_manager, 'model'):
                self.model = overlay_manager.model
    
    def set_drawing_area(self, drawing_area):
        """Set drawing area and update model.
        
        Called when this panel becomes active due to tab switching.
        Refreshes the panel to show data for the newly active document.
        
        Args:
            drawing_area: Gtk.DrawingArea widget
        """
        # Detect if this is a different document (new tab or tab switch)
        new_drawing_area_id = id(drawing_area) if drawing_area else None
        is_new_document = (new_drawing_area_id != self._current_drawing_area_id)
        
        # Store previous drawing area for comparison
        prev_drawing_area_id = self._current_drawing_area_id
        
        self.drawing_area = drawing_area
        self._current_drawing_area_id = new_drawing_area_id
        
        # Update model reference from drawing area's overlay manager
        if self.model_canvas and self.drawing_area:
            overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
            if overlay_manager and hasattr(overlay_manager, 'model'):
                self.model = overlay_manager.model
        
        # If this is a new document, clear all panel data
        if is_new_document:
            print(f"[VIABILITY_PANEL] 🆕 New document detected, clearing panel")
            self._clear_panel_for_new_document()
        
        # CRITICAL: Always refresh when switching documents (even between existing tabs)
        # This ensures the UI shows THIS document's data, not stale data from previous tab
        print(f"[VIABILITY_PANEL] 🔄 Tab switch: drawing_area {prev_drawing_area_id} → {new_drawing_area_id}")
        self.refresh_all()
    
    def _clear_panel_for_new_document(self):
        """Clear all panel data when switching to a new/different document.
        
        This ensures the panel starts fresh for each document, preventing
        data from previous documents from being displayed.
        """
        print(f"[VIABILITY_CLEAR] 🧹 Clearing panel data for new document")
        
        # Clear selected localities
        self.selected_localities.clear()
        self._locality_objects.clear()
        
        # Clear localities ListBox
        for row in list(self.localities_listbox.get_children()):
            self.localities_listbox.remove(row)
        
        # Clear subnet parameters tables
        if hasattr(self, 'places_store') and self.places_store:
            self.places_store.clear()
        if hasattr(self, 'transitions_store') and self.transitions_store:
            self.transitions_store.clear()
        if hasattr(self, 'arcs_store') and self.arcs_store:
            self.arcs_store.clear()
        if hasattr(self, 'subnet_params_store') and self.subnet_params_store:
            self.subnet_params_store.clear()
        if hasattr(self, 'subnet_io_store') and self.subnet_io_store:
            self.subnet_io_store.clear()
        
        # Clear suggestions stores
        if hasattr(self, 'structural_store') and self.structural_store:
            self.structural_store.clear()
        if hasattr(self, 'biological_store') and self.biological_store:
            self.biological_store.clear()
        if hasattr(self, 'kinetic_store') and self.kinetic_store:
            self.kinetic_store.clear()
        
        # Clear investigation
        self.current_investigation = None
        self.current_view = None
        
        print(f"[VIABILITY_CLEAR] ✅ Panel cleared")
    
    def refresh_all(self):
        """Refresh all panel data to match current document.
        
        Called when tab switches to update displayed data.
        This ensures the panel shows the correct document's viability state.
        """
        try:
            print(f"[VIABILITY_REFRESH] 🔄 Refreshing panel for drawing_area {id(self.drawing_area) if self.drawing_area else 'None'}")
            print(f"[VIABILITY_REFRESH] 📋 Selected localities: {list(self.selected_localities.keys())}")
            
            # Refresh localities ListBox to show THIS document's selections
            self._refresh_localities_list()
            
            # Refresh subnet parameters tables from current localities
            self._refresh_subnet_parameters()
            
            # Update UI state
            self._update_ui_state()
            
            print(f"[VIABILITY_REFRESH] ✅ Refresh complete")
        except Exception as e:
            print(f"[VIABILITY_REFRESH] ⚠️ Error refreshing panel: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_localities_list(self):
        """Rebuild localities ListBox to match THIS document's selected_localities.
        
        Called on tab switch to ensure the UI shows the correct document's selections.
        """
        print(f"[VIABILITY_REFRESH_LIST] 🔧 Rebuilding localities list, {len(self.selected_localities)} transitions")
        
        # Clear all existing rows from ListBox
        for row in list(self.localities_listbox.get_children()):
            self.localities_listbox.remove(row)
        
        # Get current model
        model = self._get_current_model()
        if not model:
            return
        
        # Rebuild ListBox from selected_localities dict
        # Need to recreate rows because they were removed from previous document's panel
        for transition_id, data in list(self.selected_localities.items()):
            # Get transition object from current model
            transition_obj = None
            for t in model.transitions:
                if t.id == transition_id:
                    transition_obj = t
                    break
            
            if not transition_obj:
                # Transition doesn't exist in this document, remove from dict
                del self.selected_localities[transition_id]
                if transition_id in self._locality_objects:
                    del self._locality_objects[transition_id]
                continue
            
            # Get locality from _locality_objects
            locality_ids = self._locality_objects.get(transition_id)
            if not locality_ids:
                continue
            
            # Recreate transition row
            transition_row = Gtk.ListBoxRow()
            transition_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            transition_hbox.set_margin_start(6)
            transition_hbox.set_margin_end(6)
            transition_hbox.set_margin_top(3)
            transition_hbox.set_margin_bottom(3)
            
            # Checkbox
            checkbox = Gtk.CheckButton()
            checkbox.set_active(True)
            checkbox.transition_id = transition_obj.id
            transition_hbox.pack_start(checkbox, False, False, 0)
            
            # Transition label
            label_text = transition_obj.id
            if hasattr(transition_obj, 'label') and transition_obj.label:
                label_text = f"{transition_obj.id} ({transition_obj.label})"
            
            transition_label = Gtk.Label(label=label_text)
            transition_label.set_xalign(0)
            transition_hbox.pack_start(transition_label, True, True, 0)
            
            # Remove button
            remove_btn = Gtk.Button(label="Remove")
            remove_btn.set_relief(Gtk.ReliefStyle.NONE)
            remove_btn.connect("clicked", lambda w, tid=transition_id: self._remove_transition_from_list(tid))
            transition_hbox.pack_start(remove_btn, False, False, 0)
            
            transition_row.add(transition_hbox)
            self.localities_listbox.add(transition_row)
            
            # Update selected_localities with new row and checkbox references
            self.selected_localities[transition_id]['row'] = transition_row
            self.selected_localities[transition_id]['checkbox'] = checkbox
            
            # Add input places
            for place_obj in locality_ids.input_places:
                self._add_locality_place_row_to_list(place_obj, "← Input:")
            
            # Add output places
            for place_obj in locality_ids.output_places:
                self._add_locality_place_row_to_list(place_obj, "→ Output:")
        
        # Only show widgets if panel is already packed into a container
        # If panel has no parent, it means it hasn't been added to the UI yet
        # and calling show_all() will cause GTK realize errors
        if self.get_parent() is not None:
            self.localities_listbox.show_all()
    
    def _refresh_subnet_parameters(self):
        """Refresh subnet parameters tables from current selected localities."""
        try:
            # Clear existing data
            self.places_store.clear()
            self.transitions_store.clear()
            self.arcs_store.clear()
        except Exception as e:
            print(f"[VIABILITY_REFRESH] ⚠️ Error clearing stores: {e}")
            return
        
        # Rebuild from current localities
        canvas_manager = self._get_canvas_manager()
        if not canvas_manager:
            return
        
        # Collect all places, transitions, and arcs from selected localities
        all_place_ids = set()
        all_transition_ids = set()
        all_arc_ids = set()
        
        for transition_id, locality_obj in self._locality_objects.items():
            # Places
            for place_obj in locality_obj.input_places:
                all_place_ids.add(place_obj.id)
            for place_obj in locality_obj.output_places:
                all_place_ids.add(place_obj.id)
            
            # Transitions
            all_transition_ids.add(locality_obj.transition.id)
            
            # Arcs
            for arc_obj in locality_obj.input_arcs:
                all_arc_ids.add(arc_obj.id)
            for arc_obj in locality_obj.output_arcs:
                all_arc_ids.add(arc_obj.id)
        
        # Populate places table
        for place_id in sorted(all_place_ids):
            for place in canvas_manager.places:
                if place.id == place_id:
                    place_type = "Source" if (hasattr(place, 'is_source') and place.is_source) else "Normal"
                    label = place.label if hasattr(place, 'label') else ""
                    marking = place.marking if hasattr(place, 'marking') else (place.initial_marking if hasattr(place, 'initial_marking') else 0)
                    self.places_store.append([
                        place.id,
                        place.name or place.id,
                        marking,
                        place_type,
                        label
                    ])
                    break
        
        # Populate transitions table
        for transition_id in sorted(all_transition_ids):
            for transition in canvas_manager.transitions:
                if transition.id == transition_id:
                    rate = getattr(transition, 'rate', 1.0)
                    formula = getattr(transition, 'formula', getattr(transition, 'rate_formula', ''))
                    trans_type = getattr(transition, 'transition_type', 'continuous')
                    label = getattr(transition, 'label', '')
                    self.transitions_store.append([
                        transition.id,
                        transition.name or transition.id,
                        rate,
                        formula,
                        trans_type,
                        label
                    ])
                    break
        
        # Populate arcs table
        for arc_id in sorted(all_arc_ids):
            for arc in canvas_manager.arcs:
                if arc.id == arc_id:
                    from shypn.netobjs import Place
                    source_id = arc.source.id if hasattr(arc.source, 'id') else str(arc.source)
                    target_id = arc.target.id if hasattr(arc.target, 'id') else str(arc.target)
                    arc_type = "Place→Transition" if isinstance(arc.source, Place) else "Transition→Place"
                    weight = arc.weight if hasattr(arc, 'weight') else 1
                    self.arcs_store.append([
                        arc.id,
                        source_id,
                        target_id,
                        weight,
                        arc_type
                    ])
                    break
    
    def _update_ui_state(self):
        """Update UI state based on current selections."""
        has_localities = len(self.selected_localities) > 0
        self.diagnose_button.set_sensitive(has_localities)
    
    def get_knowledge_base(self):
        """Get knowledge base (compatibility).
        
        Returns:
            ModelKnowledgeBase or None
        """
        return self._get_kb()
    
    # ========================================================================
    # SIMULATION CONTROL CALLBACKS (NEW)
    # ========================================================================
    
    def _append_diagnostics_log(self, message):
        """Add timestamped message to diagnostics log.
        
        Args:
            message: Log message text
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"{timestamp} - {message}\n"
        
        self.diagnostics_textbuffer.insert(
            self.diagnostics_textbuffer.get_end_iter(),
            full_message
        )
        
        # Auto-scroll to bottom
        mark = self.diagnostics_textbuffer.create_mark(
            None,
            self.diagnostics_textbuffer.get_end_iter(),
            False
        )
        self.diagnostics_textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
    
    def _on_clear_diagnostics_log(self, button):
        """Clear diagnostics log."""
        self.diagnostics_textbuffer.set_text("")
    
    def _on_run_simulation(self, button):
        """Run simulation to completion."""
        # 1. Initialize simulator
        if not self.subnet_simulator.initialize_simulation():
            self._append_diagnostics_log("✗ Failed to initialize simulation (no subnet selected)")
            return
        
        self._append_diagnostics_log("▶ Simulation started")
        self.simulation_toolbar.set_status("Running...", "running")
        self.simulation_toolbar.set_running_state(True)
        
        # 2. Get settings
        settings = self.simulation_toolbar.get_simulation_settings()
        max_time = settings['max_time']
        max_steps = settings['max_steps']
        
        # 3. Run simulation
        results = self.subnet_simulator.run_to_completion(
            max_time=max_time,
            max_steps=max_steps,
            log_callback=self._append_diagnostics_log
        )
        
        # 4. Update results display
        self._update_results_display(results)
        
        # 5. Update status
        status_type = "success" if "✓" in results.viability_status else "error"
        self.simulation_toolbar.set_status(results.viability_status, status_type)
        self.simulation_toolbar.set_running_state(False)
        
        self._append_diagnostics_log(
            f"Completed in {results.execution_time:.2f}s real time "
            f"({results.step_count} steps, t={results.sim_time:.2f}s sim time)"
        )
    
    def _on_step_simulation(self, button):
        """Execute single firing event."""
        # 1. Initialize if needed
        if not self.subnet_simulator.is_initialized():
            if not self.subnet_simulator.initialize_simulation():
                self._append_diagnostics_log("✗ Failed to initialize (no subnet selected)")
                return
            self._append_diagnostics_log("⏭ Step mode started")
        
        # 2. Execute step
        step_info = self.subnet_simulator.step()
        
        if not step_info:
            self._append_diagnostics_log("✗ Step failed")
            return
        
        # 3. Log step
        if step_info['deadlocked']:
            self._append_diagnostics_log("✗ Deadlock - no enabled transitions")
            self.simulation_toolbar.set_status("Deadlocked", "error")
        else:
            trans_id = step_info['fired_transition']
            changes_str = ", ".join([
                f"{pid}: {old}→{new}"
                for pid, (old, new) in step_info['marking_changes'].items()
            ])
            # One-line log including fired transition, changes, and full markings
            try:
                markings_list = ", ".join([
                    f"{pid}={self.subnet_simulator.state.current_markings.get(pid, 0)}"
                    for pid in sorted(self.subnet_simulator.state.current_markings.keys())
                ])
                self._append_diagnostics_log(
                    f"Step {self.subnet_simulator.state.step_count}: "
                    f"{trans_id} fired ({changes_str}) | Markings: {markings_list}"
                )
            except Exception:
                self._append_diagnostics_log(
                    f"Step {self.subnet_simulator.state.step_count}: "
                    f"{trans_id} fired ({changes_str})"
                )
            
            # Update live markings in Places tab
            self._update_live_markings()
            
            # Update status
            enabled_count = len(step_info['enabled_transitions'])
            self.simulation_toolbar.set_status(
                f"Step {self.subnet_simulator.state.step_count} "
                f"(t={self.subnet_simulator.state.time:.2f}s, {enabled_count} enabled)",
                "running"
            )
    
    def _on_pause_simulation(self, button):
        """Pause running simulation."""
        if self.subnet_simulator.state:
            self.subnet_simulator.pause()
            self._append_diagnostics_log("⏸ Paused")
            self.simulation_toolbar.set_status("Paused", "paused")
    
    def _on_stop_simulation(self, button):
        """Stop and reset simulation."""
        if self.subnet_simulator.state:
            self.subnet_simulator.stop()
        self.subnet_simulator.reset()
        self._append_diagnostics_log("⏹ Stopped and reset")
        self.simulation_toolbar.set_status("Ready", "ready")
        self.simulation_toolbar.set_running_state(False)
        self.results_store.clear()
    
    def _on_reset_simulation(self, button):
        """Reset simulation to initial state."""
        self.subnet_simulator.reset()
        self._append_diagnostics_log("↻ Reset to initial state")
        self.simulation_toolbar.set_status("Ready", "ready")
        self.results_store.clear()
        
        # Restore initial markings in Places tab
        if self.subnet_simulator.initial_markings:
            for row in self.places_store:
                place_id = row[0]
                if place_id in self.subnet_simulator.initial_markings:
                    row[2] = self.subnet_simulator.initial_markings[place_id]
    
    def _update_results_display(self, results):
        """Populate Results tab with simulation outcomes.
        
        Args:
            results: SimulationResults instance
        """
        self.results_store.clear()
        
        # Header
        self.results_store.append([
            "=== SIMULATION RESULTS ===",
            "", "", "", f"Status: {results.viability_status}"
        ])
        
        # Place markings section
        self.results_store.append(["", "", "", "", ""])
        self.results_store.append(["PLACE MARKINGS", "Initial", "Final", "Δ", ""])
        
        for place_id, final_marking in sorted(results.final_markings.items()):
            # Get initial marking
            initial = self.subnet_simulator.initial_markings.get(place_id, 0)
            delta = final_marking - initial
            delta_str = f"+{delta}" if delta > 0 else str(delta) if delta != 0 else "0"
            
            self.results_store.append([
                f"  {place_id}",
                str(initial),
                str(final_marking),
                delta_str,
                ""
            ])
        
        # Transition firings section
        self.results_store.append(["", "", "", "", ""])
        self.results_store.append(["TRANSITION FIRINGS", "Count", "Flux", "", ""])
        
        for trans_id, count in sorted(results.firing_counts.items()):
            flux = results.fluxes.get(trans_id, 0)
            flux_str = f"{flux:.3f} /s" if flux > 0 else "0"
            
            self.results_store.append([
                f"  {trans_id}",
                str(count),
                flux_str,
                "",
                f"{count} firings"
            ])
        
        # Viability section
        self.results_store.append(["", "", "", "", ""])
        self.results_store.append([
            "VIABILITY",
            "", "", "",
            results.viability_status
        ])
        
        if results.unbounded_places:
            self.results_store.append([
                "  Unbounded places:",
                "", "", "",
                ", ".join(results.unbounded_places)
            ])
        
        # Performance
        self.results_store.append(["", "", "", "", ""])
        self.results_store.append([
            "PERFORMANCE",
            "", "", "",
            f"Real: {results.execution_time:.3f}s, Sim: {results.sim_time:.2f}s, Steps: {results.step_count}"
        ])
        
        # Switch to Results tab
        self.subnet_notebook.set_current_page(3)  # Tab index 3 (0=Places, 1=Transitions, 2=Arcs, 3=Results)
    
    def _update_live_markings(self):
        """Update Places tab with current simulation markings (live view)."""
        if not self.subnet_simulator.state:
            return
        
        for row in self.places_store:
            place_id = row[0]
            current_marking = self.subnet_simulator.state.current_markings.get(place_id)
            if current_marking is not None:
                row[2] = current_marking  # Column 2 = marking
    
    def _on_add_experiment(self, button):
        """Create new experiment snapshot."""
        snapshot = self.experiment_manager.add_snapshot()
        
        # Capture current TreeView values
        snapshot.capture_from_treeviews(
            self.places_store,
            self.transitions_store,
            self.arcs_store
        )
        
        # Add to combo
        self.simulation_toolbar.add_experiment_to_combo(snapshot.name)
        
        self._append_diagnostics_log(f"✓ Created experiment: {snapshot.name}")
    
    def _on_copy_experiment(self, button):
        """Duplicate current experiment."""
        active_index = self.simulation_toolbar.get_active_experiment_index()
        snapshot = self.experiment_manager.copy_snapshot(active_index)
        
        if snapshot:
            self.simulation_toolbar.add_experiment_to_combo(snapshot.name)
            self._append_diagnostics_log(f"✓ Copied experiment: {snapshot.name}")
        else:
            self._append_diagnostics_log("⚠ No experiment to copy")
    
    def _on_save_experiments(self, button):
        """Export experiments to JSON file."""
        if not self.experiment_manager.snapshots:
            self._append_diagnostics_log("⚠ No experiments to save")
            return
        
        dialog = Gtk.FileChooserDialog(
            title="Save Experiments",
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name("viability_experiments.json")
        
        # Add JSON filter
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            if not filepath.endswith('.json'):
                filepath += '.json'
            
            try:
                self.experiment_manager.export_to_json(filepath)
                self._append_diagnostics_log(f"💾 Saved experiments to {filepath}")
            except Exception as e:
                self._append_diagnostics_log(f"✗ Save failed: {e}")
        
        dialog.destroy()
    
    def _on_load_experiments(self, button):
        """Import experiments from JSON file."""
        dialog = Gtk.FileChooserDialog(
            title="Load Experiments",
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add JSON filter
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            
            try:
                if self.experiment_manager.import_from_json(filepath):
                    # Rebuild combo
                    names = self.experiment_manager.get_snapshot_names()
                    self.simulation_toolbar.populate_experiment_combo(names)
                    
                    self._append_diagnostics_log(f"📂 Loaded {len(names)} experiments from {filepath}")
                else:
                    self._append_diagnostics_log(f"✗ Load failed: Invalid file format")
            except Exception as e:
                self._append_diagnostics_log(f"✗ Load failed: {e}")
        
        dialog.destroy()
    
    def _on_experiment_changed(self, combo):
        """Switch between experiment snapshots."""
        index = combo.get_active()
        if index < 0:
            return
        
        snapshot = self.experiment_manager.switch_to(index)
        
        if snapshot:
            # Apply snapshot values to TreeViews
            snapshot.apply_to_treeviews(
                self.places_store,
                self.transitions_store,
                self.arcs_store
            )
            
            self._append_diagnostics_log(f"Switched to: {snapshot.name}")
