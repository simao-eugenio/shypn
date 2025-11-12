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
        
        # Current investigation
        self.current_investigation = None
        self.current_view = None  # SubnetView or InvestigationView
        # Current investigation
        self.current_investigation = None
        self.current_view = None  # SubnetView or InvestigationView
        
        # Build panel UI
        self._build_header()
        self._build_content()
        
        # Show all widgets
        self.show_all()
    
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
        self.float_button.set_label("⬈")
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
        
        # === SECTION 2: SUBNET PARAMETERS EXPANDER (NEW) ===
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
        
        self.subnet_expander.add(self.subnet_notebook)
        main_box.pack_start(self.subnet_expander, False, False, 0)
        
        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(10)
        main_box.pack_start(sep2, False, False, 0)
        
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
    
    def _get_current_model(self):
        """Get the current model dynamically from overlay manager.
        
        Returns:
            Model instance or None
        """
        # Try cached model first
        if self.model:
            return self.model
        
        # Try to get from model_canvas and drawing_area
        if self.model_canvas and hasattr(self, 'drawing_area') and self.drawing_area:
            overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
            if overlay_manager and hasattr(overlay_manager, 'model'):
                self.model = overlay_manager.model
                print(f"[VIABILITY_PANEL] Got model from overlay_manager: {len(self.model.transitions) if self.model else 0} transitions")
                return self.model
        
        # Try to get from model_canvas directly (fallback)
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_model'):
            self.model = self.model_canvas.get_current_model()
            if self.model:
                print(f"[VIABILITY_PANEL] Got model from model_canvas: {len(self.model.transitions)} transitions")
                return self.model
        
        print(f"[VIABILITY_PANEL] WARNING: Could not get current model")
        return None
    
    def investigate_transition(self, transition_id: str):
        """Add a transition to the localities list for later diagnosis.
        
        Called from right-click context menu: "Add to Viability Analysis"
        
        Args:
            transition_id: ID of transition to add
        """
        print(f"[VIABILITY_PANEL] investigate_transition called with: {transition_id}")
        
        # Check if already in list
        if transition_id in self.selected_localities:
            self._show_feedback(f"Transition {transition_id} already in list", "warning")
            return
        
        # Get KB
        kb = self._get_kb()
        if not kb:
            print("[VIABILITY_PANEL] ERROR: No knowledge base available")
            self._show_error("No knowledge base available")
            return
        
        # Check if KB is populated, if not try to populate it
        if not kb.transitions:
            print("[VIABILITY_PANEL] KB is empty, attempting to populate from model...")
            if self._populate_kb_from_model(kb):
                print(f"[VIABILITY_PANEL] KB populated: {len(kb.transitions)} transitions, {len(kb.places)} places")
            else:
                print("[VIABILITY_PANEL] ERROR: Failed to populate KB from model")
                return
        
        # Get transition from KB
        transition = kb.transitions.get(transition_id)
        if not transition:
            print(f"[VIABILITY_PANEL] ERROR: Transition {transition_id} not found in KB")
            self._show_error(f"Transition {transition_id} not found")
            return
        
        print(f"[VIABILITY_PANEL] Transition found: {transition}")
        
        # Add to list
        self._add_transition_to_list(transition)
        
        # Enable diagnose button
        self.diagnose_button.set_sensitive(True)
        
        self._show_feedback(f"Added {transition_id} to analysis list", "info")
    
    def _add_transition_to_list(self, transition):
        """Add a transition to the localities list (matching plot panel style).
        
        Adds transition as main row, then input/output places as indented child rows,
        exactly like the dynamic analyses plot panel shows transitions with localities.
        
        Args:
            transition: TransitionKnowledge object
        """
        print(f"[VIABILITY_PANEL] _add_transition_to_list called for: {transition.transition_id}")
        
        # Get current model dynamically
        model = self._get_current_model()
        if not model:
            print(f"[VIABILITY_PANEL] ERROR: No model available")
            self._show_error("No model loaded")
            return
        
        print(f"[VIABILITY_PANEL] Model available: {len(model.transitions)} transitions, {len(model.arcs)} arcs")
        
        # Get transition object from model
        transition_obj = None
        for t in model.transitions:
            if t.id == transition.transition_id:
                transition_obj = t
                break
        
        if not transition_obj:
            print(f"[VIABILITY_PANEL] ERROR: Transition {transition.transition_id} not found in model")
            return
        
        print(f"[VIABILITY_PANEL] Found transition object: {transition_obj.id}")
        
        # Use LocalityDetector to get locality (same as plot panel)
        from shypn.diagnostic import LocalityDetector
        locality_detector = LocalityDetector(model)
        diagnostic_locality = locality_detector.get_locality_for_transition(transition_obj)
        
        print(f"[VIABILITY_PANEL] Detected locality for {transition.transition_id}: {len(diagnostic_locality.input_places)} inputs, {len(diagnostic_locality.output_places)} outputs")
        
        # Convert diagnostic Locality (objects) to investigation Locality (IDs)
        from .investigation import Locality
        locality = Locality(
            transition_id=transition.transition_id,
            input_places=[p.id for p in diagnostic_locality.input_places],
            output_places=[p.id for p in diagnostic_locality.output_places],
            input_arcs=[a.id for a in diagnostic_locality.input_arcs],
            output_arcs=[a.id for a in diagnostic_locality.output_arcs]
        )
        
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
        checkbox.transition_id = transition.transition_id  # Store as Python attribute
        transition_hbox.pack_start(checkbox, False, False, 0)
        
        # Transition label (ID and optional label)
        label_text = transition.transition_id
        if transition.label:
            label_text = f"{transition.transition_id} ({transition.label})"
        
        transition_label = Gtk.Label(label=label_text)
        transition_label.set_xalign(0)
        transition_hbox.pack_start(transition_label, True, True, 0)
        
        # Remove button
        remove_btn = Gtk.Button(label="✕")
        remove_btn.set_relief(Gtk.ReliefStyle.NONE)
        remove_btn.connect("clicked", lambda w: self._remove_transition_from_list(transition.transition_id))
        transition_hbox.pack_start(remove_btn, False, False, 0)
        
        transition_row.add(transition_hbox)
        self.localities_listbox.add(transition_row)
        
        # === INPUT PLACES (INDENTED ROWS) ===
        for place_id in locality.input_places:
            # Get place object from model
            place_obj = None
            for p in model.places:
                if p.id == place_id:
                    place_obj = p
                    break
            if place_obj:
                self._add_locality_place_row_to_list(place_obj, "← Input:")
        
        # === OUTPUT PLACES (INDENTED ROWS) ===
        for place_id in locality.output_places:
            # Get place object from model
            place_obj = None
            for p in model.places:
                if p.id == place_id:
                    place_obj = p
                    break
            if place_obj:
                self._add_locality_place_row_to_list(place_obj, "→ Output:")
        
        # Show all new widgets
        self.localities_listbox.show_all()
        
        # Track in dict (store locality too)
        self.selected_localities[transition.transition_id] = {
            'row': transition_row,
            'checkbox': checkbox,
            'transition': transition,
            'locality': locality
        }
        
        # Refresh subnet parameters display
        self._refresh_subnet_parameters()
        
        # Show
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
        self.localities_listbox.remove(data['row'])
        del self.selected_localities[transition_id]
        
        # Refresh subnet parameters display
        self._refresh_subnet_parameters()
        
        # Disable diagnose button if list is empty
        if not self.selected_localities:
            self.diagnose_button.set_sensitive(False)
    
    def _build_locality_from_transition(self, transition, kb):
        """Build a Locality object from a transition by querying the model directly.
        
        Args:
            transition: TransitionKnowledge object
            kb: ModelKnowledgeBase (kept for compatibility but not used)
            
        Returns:
            Locality object with IDs (not objects)
        """
        from .investigation import Locality
        
        # Get input/output arcs from MODEL (not KB)
        input_place_ids = []
        output_place_ids = []
        input_arc_ids = []
        output_arc_ids = []
        
        # Query arcs directly from model
        if not self.model:
            print(f"[VIABILITY_PANEL] WARNING: No model available to query arcs")
            return Locality(
                transition_id=transition.transition_id,
                input_places=[],
                output_places=[],
                input_arcs=[],
                output_arcs=[]
            )
        
        print(f"[VIABILITY_PANEL] Model has {len(self.model.arcs)} arcs, looking for arcs of transition {transition.transition_id}")
        
        # Iterate through model arcs
        for arc in self.model.arcs:
            # Check if arc connects to this transition
            # Arc.source and Arc.target are Place/Transition objects
            source_id = arc.source.id if hasattr(arc.source, 'id') else str(arc.source)
            target_id = arc.target.id if hasattr(arc.target, 'id') else str(arc.target)
            arc_id = arc.id if hasattr(arc, 'id') else f"arc_{source_id}_{target_id}"
            
            # Debug: Print first 5 arcs to see what we're working with
            if len(input_arc_ids) + len(output_arc_ids) < 5:
                print(f"[VIABILITY_PANEL]   Checking arc {arc_id}: {source_id} -> {target_id}")
                print(f"[VIABILITY_PANEL]     source type: {type(arc.source).__name__}, target type: {type(arc.target).__name__}")
            
            # Determine arc type
            from shypn.netobjs import Place, Transition
            source_is_place = isinstance(arc.source, Place)
            target_is_transition = isinstance(arc.target, Transition)
            source_is_transition = isinstance(arc.source, Transition)
            target_is_place = isinstance(arc.target, Place)
            
            if source_is_place and target_is_transition and target_id == transition.transition_id:
                # Place → Transition (INPUT)
                input_arc_ids.append(arc_id)
                input_place_ids.append(source_id)
                print(f"[VIABILITY_PANEL]   ✓ Found INPUT arc {arc_id} from place {source_id}")
            elif source_is_transition and target_is_place and source_id == transition.transition_id:
                # Transition → Place (OUTPUT)
                output_arc_ids.append(arc_id)
                output_place_ids.append(target_id)
                print(f"[VIABILITY_PANEL]   ✓ Found OUTPUT arc {arc_id} to place {target_id}")
        
        # Create locality with string IDs
        locality = Locality(
            transition_id=transition.transition_id,
            input_places=input_place_ids,
            output_places=output_place_ids,
            input_arcs=input_arc_ids,
            output_arcs=output_arc_ids
        )
        
        print(f"[VIABILITY_PANEL] Built locality: {len(input_place_ids)} inputs, {len(output_place_ids)} outputs")
        return locality
    
    def _refresh_subnet_parameters(self):
        """Refresh subnet parameters tables based on selected localities."""
        print(f"[VIABILITY_PANEL] _refresh_subnet_parameters called")
        
        # Clear all stores
        self.places_store.clear()
        self.transitions_store.clear()
        self.arcs_store.clear()
        
        # Get current model dynamically
        model = self._get_current_model()
        if not model:
            print(f"[VIABILITY_PANEL] No model available")
            return
        
        # Collect all unique place IDs, transition IDs, and arc IDs from localities
        all_place_ids = set()
        all_transition_ids = set()
        all_arc_ids = set()
        
        print(f"[VIABILITY_PANEL] Processing {len(self.selected_localities)} localities")
        
        for transition_id, data in self.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                print(f"[VIABILITY_PANEL]   WARNING: No locality for transition {transition_id}")
                continue
            
            print(f"[VIABILITY_PANEL]   Locality {transition_id}: {len(locality.input_places)} inputs, {len(locality.output_places)} outputs, {len(locality.input_arcs)} input arcs, {len(locality.output_arcs)} output arcs")
            
            # Add transition ID
            all_transition_ids.add(locality.transition_id)
            
            # Add place IDs
            all_place_ids.update(locality.input_places)
            all_place_ids.update(locality.output_places)
            
            # Add arc IDs
            all_arc_ids.update(locality.input_arcs)
            all_arc_ids.update(locality.output_arcs)
        
        print(f"[VIABILITY_PANEL] Collected: {len(all_place_ids)} places, {len(all_transition_ids)} transitions, {len(all_arc_ids)} arcs")
        
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
        
        print(f"[VIABILITY_PANEL] Refreshed subnet parameters: {len(self.places_store)} places, {len(self.transitions_store)} transitions, {len(self.arcs_store)} arcs")
    
    # === EDITING CALLBACKS ===
    
    def _on_place_marking_edited(self, widget, path, new_text, store):
        """Handle place marking edit."""
        try:
            new_marking = int(new_text)
            place_id = store[path][0]
            
            # Update store
            store[path][2] = new_marking
            
            # Update model
            for place in self.model.places:
                if place.id == place_id:
                    place.marking = new_marking
                    print(f"[VIABILITY_PANEL] Updated {place_id} marking to {new_marking}")
                    break
        except ValueError:
            print(f"[VIABILITY_PANEL] Invalid marking value: {new_text}")
    
    def _on_transition_rate_edited(self, widget, path, new_text, store):
        """Handle transition rate edit."""
        try:
            new_rate = float(new_text)
            transition_id = store[path][0]
            
            # Update store
            store[path][2] = new_rate
            
            # Update model
            for transition in self.model.transitions:
                if transition.id == transition_id:
                    transition.rate = new_rate
                    print(f"[VIABILITY_PANEL] Updated {transition_id} rate to {new_rate}")
                    break
        except ValueError:
            print(f"[VIABILITY_PANEL] Invalid rate value: {new_text}")
    
    def _on_transition_formula_edited(self, widget, path, new_text, store):
        """Handle transition formula edit."""
        transition_id = store[path][0]
        
        # Update store
        store[path][3] = new_text
        
        # Update model
        for transition in self.model.transitions:
            if transition.id == transition_id:
                transition.formula = new_text
                print(f"[VIABILITY_PANEL] Updated {transition_id} formula to: {new_text}")
                break
    
    def _on_arc_weight_edited(self, widget, path, new_text, store):
        """Handle arc weight edit."""
        try:
            new_weight = int(new_text)
            arc_id = store[path][0]
            
            # Update store
            store[path][3] = new_weight
            
            # Update model
            for arc in self.model.arcs:
                if arc.id == arc_id:
                    arc.weight = new_weight
                    print(f"[VIABILITY_PANEL] Updated {arc_id} weight to {new_weight}")
                    break
        except ValueError:
            print(f"[VIABILITY_PANEL] Invalid weight value: {new_text}")
    
    def _run_analysis_pipeline(self, transition):
        """Run the full analysis pipeline on a transition.
        
        Args:
            transition: TransitionKnowledge object
        
        Returns:
            List of Issue objects
        """
        print(f"[VIABILITY_PANEL] Running analysis pipeline for: {transition.transition_id}")
        
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
            print(f"[VIABILITY_PANEL] ERROR: No model available for analysis")
            return [], []
        
        # Get transition object from model
        transition_obj = None
        for t in model.transitions:
            if t.id == transition.transition_id:
                transition_obj = t
                break
        
        if not transition_obj:
            print(f"[VIABILITY_PANEL] ERROR: Transition {transition.transition_id} not found in model")
            return [], []
        
        # Use LocalityDetector to get locality (same approach as _add_transition_to_list)
        from shypn.diagnostic import LocalityDetector
        locality_detector = LocalityDetector(model)
        diagnostic_locality = locality_detector.get_locality_for_transition(transition_obj)
        
        # Convert diagnostic Locality (objects) to investigation Locality (IDs)
        from .investigation import Locality
        locality = Locality(
            transition_id=transition.transition_id,
            input_places=[p.id for p in diagnostic_locality.input_places],
            output_places=[p.id for p in diagnostic_locality.output_places],
            input_arcs=[a.id for a in diagnostic_locality.input_arcs],
            output_arcs=[a.id for a in diagnostic_locality.output_arcs]
        )
        
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
            print(f"[VIABILITY_PANEL] Level 1 (Locality): {len(locality_issues)} issues")
            if locality_issues:
                for issue in locality_issues:
                    print(f"  - {issue.category}: {issue.message[:60]}...")
        except Exception as e:
            print(f"[VIABILITY_PANEL] ERROR in locality analysis: {e}")
            import traceback
            traceback.print_exc()
        
        # Level 2: Dependency Analysis (requires context of nearby transitions)
        # TODO: Implement when subnet building is ready
        
        # Level 3: Boundary Analysis
        try:
            boundary_issues = boundary_analyzer.analyze(context)
            all_issues.extend(boundary_issues)
            print(f"[VIABILITY_PANEL] Level 3 (Boundary): {len(boundary_issues)} issues")
        except Exception as e:
            print(f"[VIABILITY_PANEL] ERROR in boundary analysis: {e}")
            import traceback
            traceback.print_exc()
        
        # Level 4: Conservation Analysis
        try:
            conservation_issues = conservation_analyzer.analyze(context)
            all_issues.extend(conservation_issues)
            print(f"[VIABILITY_PANEL] Level 4 (Conservation): {len(conservation_issues)} issues")
        except Exception as e:
            print(f"[VIABILITY_PANEL] ERROR in conservation analysis: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[VIABILITY_PANEL] Total issues found: {len(all_issues)}")
        return all_issues
    
    def _generate_suggestions_from_issues(self, issues, transition):
        """Generate suggestions from issues.
        
        Args:
            issues: List of Issue objects
            transition: TransitionKnowledge object
        
        Returns:
            List of Suggestion objects
        """
        print(f"[VIABILITY_PANEL] Generating suggestions for {len(issues)} issues")
        
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
                
                print(f"[VIABILITY_PANEL] Issue '{issue.message[:40]}...' -> {analyzer_name} -> {len(suggestions)} suggestions")
                all_suggestions.extend(suggestions)
            except Exception as e:
                print(f"[VIABILITY_PANEL] ERROR generating suggestions for issue: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"[VIABILITY_PANEL] Generated {len(all_suggestions)} suggestions")
        return all_suggestions
    
    def _OLD_investigate_transition(self, transition_id: str):
        """OLD METHOD - kept for reference during refactoring.
        
        Called from right-click context menu: "Add to Viability Analysis"
        
        Args:
            transition_id: ID of transition to investigate
        """
        print(f"[VIABILITY_PANEL] investigate_transition called with: {transition_id}")
        
        # Get KB
        kb = self._get_kb()
        if not kb:
            print("[VIABILITY_PANEL] ERROR: No knowledge base available")
            self._show_error("No knowledge base available")
            return
        
        print(f"[VIABILITY_PANEL] KB found: {kb}")
        
        # Check if KB is populated, if not try to populate it
        if not kb.transitions:
            print("[VIABILITY_PANEL] KB is empty, attempting to populate from model...")
            if self._populate_kb_from_model(kb):
                print(f="[VIABILITY_PANEL] KB populated: {len(kb.transitions)} transitions, {len(kb.places)} places")
            else:
                print("[VIABILITY_PANEL] ERROR: Failed to populate KB from model")
                return
        else:
            print(f"[VIABILITY_PANEL] KB already populated: {len(kb.transitions)} transitions")
        
        # Initialize data puller
        self.data_puller = DataPuller(kb, simulation=self._get_simulation())
        cached_puller = CachedDataPuller(self.data_puller, self.data_cache)
        
        # Initialize fix system
        self.fix_applier = FixApplier(kb)
        self.fix_predictor = FixPredictor(kb)
        
        # Build subnet around transition - using old SubnetBuilder for now
        # TODO: Replace with new simplified builder when ready
        try:
            # For now, create a simple single-locality subnet
            from .investigation import Locality, Subnet
            
            print(f"[VIABILITY_PANEL] Looking for transition: {transition_id}")
            print(f="[VIABILITY_PANEL] KB type: {type(kb)}")
            print(f"[VIABILITY_PANEL] KB has transitions attr: {hasattr(kb, 'transitions')}")
            
            # Get transition - try multiple ways
            transition = None
            if hasattr(kb, 'transitions'):
                print(f"[VIABILITY_PANEL] KB.transitions type: {type(kb.transitions)}")
                if isinstance(kb.transitions, dict):
                    print(f"[VIABILITY_PANEL] Available transitions: {list(kb.transitions.keys())[:10]}")
                    transition = kb.transitions.get(transition_id)
                    print(f"[VIABILITY_PANEL] Transition lookup result: {transition}")
                else:
                    print(f"[VIABILITY_PANEL] KB.transitions is not a dict, trying as attribute")
                    transition = getattr(kb.transitions, transition_id, None)
            else:
                print(f"[VIABILITY_PANEL] KB has no transitions attribute!")
            
            if not transition:
                print(f="[VIABILITY_PANEL] ERROR: Transition {transition_id} not found in KB")
                # Don't show error dialog for now, just print and return
                print(f"[VIABILITY_PANEL] This may be because KB structure is different than expected")
                return
            
            print(f"[VIABILITY_PANEL] Transition found: {transition}")
            print(f="[VIABILITY_PANEL] Transition type: {type(transition)}")
            
            # Get input/output arcs from KB (TransitionKnowledge stores arc IDs in inputs/outputs lists)
            input_arcs = []
            output_arcs = []
            input_places = []
            output_places = []
            
            # Query arcs from KB - look for arcs targeting this transition (inputs)
            for arc_id, arc in kb.arcs.items():
                if arc.arc_type == "place_to_transition" and arc.target_id == transition_id:
                    input_arcs.append(arc_id)
                    input_places.append(arc.source_id)
                elif arc.arc_type == "transition_to_place" and arc.source_id == transition_id:
                    output_arcs.append(arc_id)
                    output_places.append(arc.target_id)
            
            print(f"[VIABILITY_PANEL] Input arcs: {input_arcs}")
            print(f"[VIABILITY_PANEL] Output arcs: {output_arcs}")
            print(f"[VIABILITY_PANEL] Input places: {input_places}")
            print(f"[VIABILITY_PANEL] Output places: {output_places}")
            
            # Build locality
            locality = Locality(
                transition_id=transition_id,
                input_places=input_places,
                output_places=output_places,
                input_arcs=input_arcs,
                output_arcs=output_arcs
            )
            
            # Build simple subnet
            subnet = Subnet(
                transitions={transition_id},
                places=set(locality.input_places + locality.output_places),
                arcs=set(locality.input_arcs + locality.output_arcs)
            )
            subnet.localities = [locality]  # Add localities attribute
            
        except Exception as e:
            self._show_error(f"Failed to build subnet: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Run multi-level analysis - First collect all Issues
        all_issues = []
        
        # Get simulation data as dict (or None if not available)
        sim_controller = self._get_simulation()
        sim_data = None
        if sim_controller:
            # TODO: Extract simulation data dict from controller
            # For now, pass None to avoid errors
            sim_data = None
        
        # Build analysis context
        context = {
            'transition': transition,
            'locality': locality,
            'subnet': subnet,
            'kb': kb,
            'sim_data': sim_data  # Pass None for now instead of controller
        }
        
        # STEP 1: Run analyzers to collect Issues
        try:
            locality_issues = self.locality_analyzer.analyze(context) if locality else []
            all_issues.extend(locality_issues)
            print(f"[VIABILITY_PANEL] Locality analysis: {len(locality_issues)} issues")
        except Exception as e:
            print(f"Locality analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            dependency_issues = self.dependency_analyzer.analyze(context)
            all_issues.extend(dependency_issues)
            print(f"[VIABILITY_PANEL] Dependency analysis: {len(dependency_issues)} issues")
        except Exception as e:
            print(f"Dependency analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            boundary_issues = self.boundary_analyzer.analyze(context)
            all_issues.extend(boundary_issues)
            print(f"[VIABILITY_PANEL] Boundary analysis: {len(boundary_issues)} issues")
        except Exception as e:
            print(f"Boundary analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            conservation_issues = self.conservation_analyzer.analyze(context)
            all_issues.extend(conservation_issues)
            print(f"[VIABILITY_PANEL] Conservation analysis: {len(conservation_issues)} issues")
        except Exception as e:
            print(f"Conservation analysis failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[VIABILITY_PANEL] Total issues found: {len(all_issues)}")
        
        # STEP 2: Generate Suggestions from Issues
        all_suggestions = []
        
        try:
            locality_suggestions = self.locality_analyzer.generate_suggestions(all_issues, context)
            all_suggestions.extend(locality_suggestions)
            print(f"[VIABILITY_PANEL] Locality suggestions: {len(locality_suggestions)}")
        except Exception as e:
            print(f"Failed to generate locality suggestions: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            dependency_suggestions = self.dependency_analyzer.generate_suggestions(all_issues, context)
            all_suggestions.extend(dependency_suggestions)
            print(f"[VIABILITY_PANEL] Dependency suggestions: {len(dependency_suggestions)}")
        except Exception as e:
            print(f"Failed to generate dependency suggestions: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            boundary_suggestions = self.boundary_analyzer.generate_suggestions(all_issues, context)
            all_suggestions.extend(boundary_suggestions)
            print(f"[VIABILITY_PANEL] Boundary suggestions: {len(boundary_suggestions)}")
        except Exception as e:
            print(f"Failed to generate boundary suggestions: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            conservation_suggestions = self.conservation_analyzer.generate_suggestions(all_issues, context)
            all_suggestions.extend(conservation_suggestions)
            print(f"[VIABILITY_PANEL] Conservation suggestions: {len(conservation_suggestions)}")
        except Exception as e:
            print(f"Failed to generate conservation suggestions: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[VIABILITY_PANEL] Total suggestions generated: {len(all_suggestions)}")
        
        # Sequence fixes
        try:
            fix_sequence = self.fix_sequencer.sequence(all_suggestions) if all_suggestions else None
        except Exception as e:
            print(f"Fix sequencing failed: {e}")
            fix_sequence = None
        
        # Create investigation
        from .investigation import Investigation
        self.current_investigation = Investigation(
            root_transition_id=transition_id,
            subnet=subnet,
            suggestions=all_suggestions,
            fix_sequence=fix_sequence
        )
        
        print(f"[VIABILITY_PANEL] Investigation created: {self.current_investigation}")
        print(f"[VIABILITY_PANEL] Suggestions count: {len(all_suggestions)}")
        
        # Build and show UI
        self._show_investigation_view()
    
    def _show_investigation_view(self):
        """Show investigation results in UI."""
        print(f"[VIABILITY_PANEL] _show_investigation_view called")
        
        if not self.current_investigation:
            print("[VIABILITY_PANEL] ERROR: No current investigation!")
            return
        
        print(f"[VIABILITY_PANEL] Current investigation: {self.current_investigation}")
        print(f"[VIABILITY_PANEL] Subnet localities: {len(self.current_investigation.subnet.localities) if hasattr(self.current_investigation.subnet, 'localities') else 0}")
        
        # Remove empty state
        if self.empty_label in self.content_box.get_children():
            print("[VIABILITY_PANEL] Removing empty state label")
            self.content_box.remove(self.empty_label)
        
        # Remove old view if exists
        if self.current_view and self.current_view in self.content_box.get_children():
            print("[VIABILITY_PANEL] Removing old view")
            self.content_box.remove(self.current_view)
        
        # FOR NOW: Always use simple fallback view since Investigation dataclass
        # structure doesn't match what InvestigationView/SubnetView expect
        print("[VIABILITY_PANEL] Using simple fallback view")
        self.current_view = self._create_simple_results_view()
        
        print(f"[VIABILITY_PANEL] View created: {type(self.current_view)}")
        print(f"[VIABILITY_PANEL] content_box children before add: {len(self.content_box.get_children())}")
        
        self.content_box.pack_start(self.current_view, True, True, 0)
        
        print(f"[VIABILITY_PANEL] content_box children after add: {len(self.content_box.get_children())}")
        print("[VIABILITY_PANEL] Calling show_all()...")
        
        # Make everything visible
        self.current_view.show_all()
        self.content_box.show_all()
        self.scrolled_window.show_all()
        self.show_all()
        
        # Force queue draw
        self.queue_draw()
        self.content_box.queue_draw()
        self.scrolled_window.queue_draw()
        
        # Check visibility
        print(f"[VIABILITY_PANEL] Current view visible: {self.current_view.get_visible()}")
        print(f"[VIABILITY_PANEL] Content box visible: {self.content_box.get_visible()}")
        print(f"[VIABILITY_PANEL] Scrolled window visible: {self.scrolled_window.get_visible()}")
        print(f"[VIABILITY_PANEL] Panel visible: {self.get_visible()}")
        
        print("[VIABILITY_PANEL] UI update complete")
    
    def _create_simple_results_view(self):
        """Create simple fallback view showing investigation results.
        
        Returns:
            Gtk.Box with simple text results
        """
        print("[VIABILITY_PANEL] _create_simple_results_view called")
        print(f"[VIABILITY_PANEL] Investigation: {self.current_investigation}")
        print(f"[VIABILITY_PANEL] Suggestions: {len(self.current_investigation.suggestions) if self.current_investigation else 0}")
        
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
            warnings_label.set_markup(f"<b>⚠ Warnings:</b>")
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
        """Get current knowledge base.
        
        Returns:
            Knowledge base or None
        """
        if self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            return self.model_canvas.get_current_knowledge_base()
        return None
    
    def _populate_kb_from_model(self, kb):
        """Populate KB from current model if empty.
        
        Args:
            kb: Knowledge base instance to populate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current model
            model = None
            if self.model_canvas:
                model = self.model_canvas
            elif self.model:
                model = self.model
            
            if not model:
                print("[VIABILITY_PANEL] No model available to populate KB")
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
                print("[VIABILITY_PANEL] No transitions found in model")
                return False
            
            # Populate KB
            print(f"[VIABILITY_PANEL] Populating KB with {len(places_data)} places, {len(transitions_data)} transitions, {len(arcs_data)} arcs")
            kb.update_topology_structural(places_data, transitions_data, arcs_data)
            
            return True
            
        except Exception as e:
            print(f"[VIABILITY_PANEL] Failed to populate KB: {e}")
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
        print("[VIABILITY_PANEL] _on_diagnose_clicked called")
        
        # Get checked transitions
        checked_transitions = []
        for transition_id, data in self.selected_localities.items():
            checkbox = data['checkbox']
            if checkbox.get_active():
                checked_transitions.append(data['transition'])
        
        if not checked_transitions:
            self._show_feedback("No transitions selected for diagnosis", "warning")
            return
        
        print(f"[VIABILITY_PANEL] Diagnosing {len(checked_transitions)} transitions")
        
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
            print(f"[VIABILITY_PANEL] Analyzing transition: {transition.transition_id}")
            
            # Run analysis levels
            issues = self._run_analysis_pipeline(transition)
            total_issues += len(issues)
            
            # Generate suggestions from issues
            suggestions = self._generate_suggestions_from_issues(issues, transition)
            
            # Categorize suggestions
            print(f"[VIABILITY_PANEL] Categorizing {len(suggestions)} suggestions for transition {transition.transition_id}")
            for suggestion in suggestions:
                category = suggestion.category.lower()
                print(f"[VIABILITY_PANEL]   Suggestion category: '{category}' (raw: '{suggestion.category}')")
                if category in all_suggestions_by_category:
                    all_suggestions_by_category[category].append(suggestion)
                    print(f"[VIABILITY_PANEL]     Added to {category}")
                else:
                    print(f"[VIABILITY_PANEL]     WARNING: Unknown category '{category}', skipping")
        
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
        
        Removes all transitions from the localities list.
        """
        print("[VIABILITY_PANEL] _on_clear_all_clicked called")
        
        # Clear localities list
        for row in list(self.localities_listbox.get_children()):
            self.localities_listbox.remove(row)
        
        self.selected_localities.clear()
        
        # Disable diagnose button
        self.diagnose_button.set_sensitive(False)
        
        # Clear results
        self._clear_results()
        
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
        """Add object for analysis (compatibility).
        
        Args:
            obj: Place or Transition object
        """
        print(f"[VIABILITY_PANEL] add_object_for_analysis called with: {obj}")
        from shypn.netobjs import Transition
        
        if isinstance(obj, Transition):
            print(f"[VIABILITY_PANEL] Object is Transition, calling investigate_transition({obj.id})")
            self.investigate_transition(obj.id)
        else:
            print(f"[VIABILITY_PANEL] Object is not a Transition: {type(obj)}")
    
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
                print(f"[VIABILITY_PANEL] Model updated: {len(self.model.transitions) if self.model else 0} transitions")
    
    def set_drawing_area(self, drawing_area):
        """Set drawing area and update model.
        
        Args:
            drawing_area: Gtk.DrawingArea widget
        """
        self.drawing_area = drawing_area
        
        # Update model reference from drawing area's overlay manager
        if self.model_canvas and self.drawing_area:
            overlay_manager = self.model_canvas.overlay_managers.get(self.drawing_area)
            if overlay_manager and hasattr(overlay_manager, 'model'):
                self.model = overlay_manager.model
                print(f"[VIABILITY_PANEL] Model updated via set_drawing_area: {len(self.model.transitions) if self.model else 0} transitions")
    
    def refresh_all(self):
        """Refresh all (compatibility - now no-op)."""
        pass
    
    def get_knowledge_base(self):
        """Get knowledge base (compatibility).
        
        Returns:
            ModelKnowledgeBase or None
        """
        return self._get_kb()

