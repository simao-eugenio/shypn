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

╔════════════════════════════════════════════════════════════════════════════╗
║ ARCHITECTURE NOTE: This class is intentionally large (2900+ lines)        ║
║                                                                            ║
║ REASON: Orchestrates complex viability analysis workflow with multiple    ║
║         analysis types, batch execution, result browsing, and progress    ║
║         tracking. Panel state management requires centralized control     ║
║         due to pseudo-MDI architecture constraints.                       ║
║                                                                            ║
║ ⚠️  DO NOT SPLIT: Panel visibility/focus management from controller       ║
║ ⚠️  DO NOT SPLIT: UI state from analysis orchestration                    ║
║ ⚠️  DO NOT SPLIT: Progress tracking into separate class                   ║
║                                                                            ║
║ SAFE REFACTORINGS:                                                        ║
║ ✅ Extract analysis algorithms (LocalityAnalyzer is stateless)             ║
║ ✅ Extract batch coordination logic (BatchExecutor already exists)         ║
║ ✅ Create value objects (AnalysisRequest, BatchConfig, ResultSet)          ║
║ ✅ Emit events via EventBus ('analysis.started', 'analysis.completed')     ║
║ ✅ Extract result rendering to pure functions                              ║
║                                                                            ║
║ SEE: doc/ADR-004-viability-panel-complexity.md (when created)             ║
╚════════════════════════════════════════════════════════════════════════════╝

Author: Simão Eugénio
Date: November 12, 2025 (Refactored)
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, GLib, Pango
import re

from shypn.utils.safe_eval import safe_eval_numeric
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
from .ui.subnet_parameters_view import SubnetParametersView

# Phase 2.2 Extracted Analyzers
from .analyzers import ViabilityAnalyzer, AnalysisResult

# Phase 6 Sprint 16 — locality model-assembly service
from .locality_controller import LocalityController


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
        
        # Subnet model (complete DocumentModel created from localities)
        self.subnet_model = None

        # Locality model-assembly service (GTK-free)
        self._locality_ctrl = LocalityController(
            get_canvas_manager=self._get_canvas_manager,
            get_current_model=self._get_current_model,
        )

        # Track current drawing area to detect document switches
        self._current_drawing_area_id = None
        
        # Build panel UI
        self._build_header()
        self._build_content()
        
        # Don't call show_all() here - panel will be shown after being packed into container
        # (matches Report panel pattern)
    
    # ==================== UI Construction ====================
    
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
        # Tooltip disabled - only show tooltips on canvas network objects
        # header_label.set_tooltip_text("Model viability analysis and suggestions")
        header_box.pack_start(header_label, True, True, 0)
        
        # Float button (right) - match Topology/Analyses icon and style
        self.float_button = Gtk.ToggleButton()
        self.float_button.set_label("⬈")
        # Tooltip disabled - only show tooltips on canvas network objects
        # self.float_button.set_tooltip_text("Detach panel to floating window")
        self.float_button.set_relief(Gtk.ReliefStyle.NONE)  # Flat button
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
        
        # FUTURE ENHANCEMENT: Automatic diagnostics (currently disabled - user detects failures manually)
        # self.diagnose_button = Gtk.Button(label="Diagnose Selected")
        # self.diagnose_button.connect("clicked", self._on_diagnose_clicked)
        # self.diagnose_button.set_sensitive(False)
        # buttons_box.pack_start(self.diagnose_button, True, True, 0)
        
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
        
        # === INTERACTIVE TESTING SECTION LABEL ===
        interactive_label = Gtk.Label()
        interactive_label.set_markup(
            "<b>INTERACTIVE TESTING</b>\n"
            "<span size='small'>For Petri net debugging: step-by-step execution, pause/resume, deadlock investigation</span>"
        )
        interactive_label.set_halign(Gtk.Align.START)
        interactive_label.set_margin_start(10)
        interactive_label.set_margin_top(10)
        interactive_label.set_margin_bottom(5)
        main_box.pack_start(interactive_label, False, False, 0)
        
        # === SIMULATION CONTROLS (NEW) ===
        self.simulation_toolbar = SimulationControlToolbar()
        main_box.pack_start(self.simulation_toolbar, False, False, 0)
        
        # Connect simulation control signals
        self.simulation_toolbar.run_button.connect("clicked", self._on_run_simulation)
        self.simulation_toolbar.step_button.connect("clicked", self._on_step_simulation)
        self.simulation_toolbar.pause_button.connect("clicked", self._on_pause_simulation)
        self.simulation_toolbar.stop_button.connect("clicked", self._on_stop_simulation)
        self.simulation_toolbar.reset_button.connect("clicked", self._on_reset_simulation)
        
        # Removed experiment management connections - buttons removed from toolbar
        # Auto-sync handles baseline updates automatically
        
        # === SECTION 2: SUBNET PARAMETERS EXPANDER ===
        self.subnet_params_view = SubnetParametersView()
        main_box.pack_start(self.subnet_params_view, False, False, 0)
        
        # Connect edit callbacks to viability panel methods
        self.subnet_params_view.on_place_marking_edited = self._on_place_marking_edited
        self.subnet_params_view.on_transition_rate_edited = self._on_transition_rate_edited
        self.subnet_params_view.on_transition_formula_edited = self._on_transition_formula_edited
        self.subnet_params_view.on_arc_weight_edited = self._on_arc_weight_edited
        self.subnet_params_view.on_create_sweep_from_place = self._on_create_sweep_from_place
        self.subnet_params_view.on_create_sweep_from_transition = self._on_create_sweep_from_transition
        self.subnet_params_view.on_create_sweep_from_arc = self._on_create_sweep_from_arc
        
        # Store references to TreeViews and stores for backward compatibility
        self.places_treeview = self.subnet_params_view.places_treeview
        self.places_store = self.subnet_params_view.places_store
        self.transitions_treeview = self.subnet_params_view.transitions_treeview
        self.transitions_store = self.subnet_params_view.transitions_store
        self.arcs_treeview = self.subnet_params_view.arcs_treeview
        self.arcs_store = self.subnet_params_view.arcs_store
        self.results_treeview = self.subnet_params_view.results_treeview
        self.results_store = self.subnet_params_view.results_store
        self.subnet_notebook = self.subnet_params_view.subnet_notebook
        
        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_margin_top(10)
        main_box.pack_start(sep2, False, False, 0)
        
        # === DIAGNOSTICS LOG (NEW) ===
        self.diagnostics_expander = Gtk.Expander()
        self.diagnostics_expander.set_expanded(False)  # Start collapsed
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
        self.diagnostics_textview.set_wrap_mode(Pango.WrapMode.WORD)
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
        
        # === SECTION 7: INVESTIGATION RESULTS CONTAINER ===
        # Dedicated container managed by _show_investigation_view.
        # This isolates dynamic results from the static sections above.
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.content_box.set_margin_start(10)
        self.content_box.set_margin_end(10)
        self.content_box.set_margin_top(6)
        self.content_box.set_margin_bottom(10)

        # Empty-state placeholder for results container
        self.empty_label = Gtk.Label()
        self.empty_label.set_markup("<i>Run a diagnosis to see investigation results here</i>")
        self.empty_label.set_justify(Gtk.Justification.CENTER)
        self.content_box.pack_start(self.empty_label, False, False, 0)

        # Add results container to main layout
        main_box.pack_start(self.content_box, False, False, 0)
        
        # === AUTOMATED EXPERIMENTATION SECTION LABEL ===
        sep4 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep4.set_margin_top(15)
        sep4.set_margin_bottom(5)
        main_box.pack_start(sep4, False, False, 0)
        
        automation_label = Gtk.Label()
        automation_label.set_markup(
            "<b>AUTOMATED EXPERIMENTATION</b>\n"
            "<span size='small'>Batch parameter sweeps, parallel execution, statistical analysis, sensitivity analysis</span>"
        )
        automation_label.set_halign(Gtk.Align.START)
        automation_label.set_margin_start(10)
        automation_label.set_margin_bottom(5)
        main_box.pack_start(automation_label, False, False, 0)
        
        # === SECTION 8: EXPERIMENT AUTOMATION CATEGORY (NEW) ===
        from .automation import ExperimentAutomationCategory
        
        self.automation_category = ExperimentAutomationCategory(
            model_canvas=self.model_canvas,
            experiment_manager=self.experiment_manager,
            expanded=True  # Expanded by default - primary workflow
        )
        self.automation_category.set_parent_panel(self)
        
        # Add to main layout
        main_box.pack_start(self.automation_category.get_widget(), False, False, 0)
        
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
    
    # TreeView creation methods moved to SubnetParametersView class
    # Keeping _create_suggestions_treeview here as it's for investigation view
    
    # ==================== Model and Canvas Access ====================
    
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
            except (AttributeError, TypeError) as e:
                self.logger.debug(f"Cannot access model_canvas document: {e}")
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
        except (AttributeError, TypeError, KeyError) as e:
            # Canvas manager not available or invalid drawing_area
            self.logger.debug(f"Cannot access canvas manager: {e}")
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
            except (AttributeError, TypeError) as e:
                self.logger.debug(f"Cannot access model_canvas document in fallback: {e}")
                return None
        
        drawing_area = self.drawing_area
        
        try:
            # Get canvas manager for THIS panel's document
            if hasattr(self.model_canvas, 'canvas_managers'):
                return self.model_canvas.canvas_managers.get(self.drawing_area)
        except (AttributeError, TypeError, KeyError) as e:
            # Canvas manager not available
            self.logger.debug(f"Cannot access canvas manager in fallback: {e}")
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
        # self.diagnose_button.set_sensitive(True)  # Disabled - button removed
        
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
    
    def _detect_formula_referenced_places(self, transition_obj):
        """Detect places referenced in transition rate formula.

        Delegates to LocalityController.
        """
        return self._locality_ctrl.detect_formula_referenced_places(transition_obj)
    
    def _extract_place_ids_from_formula(self, formula: str, model, transition_id=None):
        """Extract place objects referenced in a formula.

        Delegates to LocalityController.
        """
        return self._locality_ctrl.extract_place_ids_from_formula(
            formula, model, self.selected_localities, transition_id
        )
    
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
        
        # Note: Formula-referenced places will be detected later in _refresh_subnet_parameters()
        # when we have access to the full model context and rate_function attribute
        
        # === COLOR ALL LOCALITY OBJECTS FIRST ===
        
        # Color transition
        self._color_transition(transition_obj)
        
        # Color input places
        for place_obj in locality.input_places:
            self._color_locality_place(place_obj)
        
        # Color output places
        for place_obj in locality.output_places:
            self._color_locality_place(place_obj)
        
        # Color catalyst places (from test arcs - enzymes/cofactors)
        for place_obj in locality.catalyst_places:
            self._color_locality_place(place_obj)
        
        # Note: Formula-referenced places will be colored later when detected
        
        # Color input arcs
        for arc_obj in locality.input_arcs:
            self._color_arc(arc_obj)
        
        # Color output arcs
        for arc_obj in locality.output_arcs:
            self._color_arc(arc_obj)
        
        # Color catalyst arcs (test arcs - non-consuming)
        for arc_obj in locality.catalyst_arcs:
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
        
        # === CATALYST PLACES (INDENTED ROWS) ===
        for place_obj in locality.catalyst_places:
            self._add_locality_place_row_to_list(place_obj, "Catalyst:")
        
        # Note: Formula-referenced places will be added later when detected
        
        # Show all new widgets (only if panel is packed)
        if self.get_parent() is not None:
            self.localities_listbox.show_all()
        
        # Track in dict (store locality IDs for cross-document safety)
        self.selected_localities[transition_obj.id] = {
            'row': transition_row,
            'checkbox': checkbox,
            'transition': transition_obj,
            'locality': locality,
            'formula_places': []  # Will be populated later when formulas are detected
        }
        
        # Trigger canvas redraw to show colored elements
        self._trigger_canvas_redraw()
        
        # Refresh subnet parameters display
        self._refresh_subnet_parameters()
        
        # Create/update subnet model immediately
        self._create_subnet_model()
        
        # Auto-sync baseline snapshot when localities change
        if hasattr(self, 'experiment_manager'):
            em = self.experiment_manager
            
            # Ensure baseline snapshot exists
            if not em.snapshots:
                from shypn.ui.panels.viability.experiment_manager import ExperimentSnapshot
                baseline = ExperimentSnapshot("Baseline")
                em.snapshots.append(baseline)
                em.active_index = 0
            
            # Sync baseline from current stores
            em.sync_baseline_from_tables(
                self.places_store,
                self.transitions_store,
                self.arcs_store
            )
        
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
        
        # Add tokens if available
        if hasattr(place, 'tokens'):
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
            from shypn.utils.color_schema_manager import ColorSchemaManager
            
            # Reset transition color
            ColorSchemaManager.reset_transition_colors(locality_obj.transition)
            
            # Reset input place colors
            for p_obj in locality_obj.input_places:
                ColorSchemaManager.reset_place_color(p_obj)
            
            # Reset output place colors
            for p_obj in locality_obj.output_places:
                ColorSchemaManager.reset_place_color(p_obj)
            
            # Reset catalyst place colors
            for p_obj in locality_obj.catalyst_places:
                ColorSchemaManager.reset_place_color(p_obj)
            
            # Reset formula-referenced place colors
            formula_places = data.get('formula_places', [])
            for p_obj in formula_places:
                ColorSchemaManager.reset_place_color(p_obj)
            
            # Reset input arc colors
            for a_obj in locality_obj.input_arcs:
                ColorSchemaManager.reset_arc_color(a_obj)
            
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
        
        # Recreate subnet model
        if self.selected_localities:
            self._create_subnet_model()
        else:
            # Clear subnet model if no localities
            self.subnet_model = None
        
        # Disable diagnose button if list is empty
        if not self.selected_localities:
            self.diagnose_button.set_sensitive(False)
    
    # ==================== Parameter Table Management ====================
    
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
        
        # PRE-PROCESS: Detect formula-referenced places for all transitions FIRST
        # This must happen before collecting place IDs
        for transition_id, data in self.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            
            transition_obj = locality.transition
            
            # Check if transition has a formula in properties dict
            formula = None
            if hasattr(transition_obj, 'properties') and isinstance(transition_obj.properties, dict):
                formula = transition_obj.properties.get('rate_function') or transition_obj.properties.get('rate_function_display')
            
            if formula and isinstance(formula, str) and formula.strip():
                formula_places = self._extract_place_ids_from_formula(formula, model, transition_id)
                if formula_places:
                    data['formula_places'] = formula_places
                else:
                    data['formula_places'] = []
            else:
                data['formula_places'] = []
        
        # Collect all unique place IDs, transition IDs, and arc IDs from localities
        all_place_ids = set()
        all_transition_ids = set()
        all_arc_ids = set()
        
        for transition_id, data in self.selected_localities.items():
            locality = data.get('locality')
            if not locality:
                continue
            
            # Add transition ID
            all_transition_ids.add(locality.transition.id)
            
            # Add place IDs (extract IDs from place objects)
            all_place_ids.update(p.id for p in locality.input_places)
            all_place_ids.update(p.id for p in locality.output_places)
            all_place_ids.update(p.id for p in locality.catalyst_places)  # Include catalyst/enzyme places
            
            # Add formula-referenced place IDs
            formula_places = data.get('formula_places', [])
            all_place_ids.update(p.id for p in formula_places)
            
            # Add arc IDs (extract IDs from arc objects)
            all_arc_ids.update(a.id for a in locality.input_arcs)
            all_arc_ids.update(a.id for a in locality.output_arcs)
            all_arc_ids.update(a.id for a in locality.catalyst_arcs)  # Include test arcs (non-consuming)
        
        # SPECIAL CASE: If no localities selected, show entire model
        show_all_places = len(self.selected_localities) == 0
        
        # Populate Places table
        for place in model.places:
            # If localities selected: only show places in those localities
            # If no localities: show all places (entire model)
            if not show_all_places and place.id not in all_place_ids:
                continue
            place_obj = place
            place_type = "Source" if hasattr(place_obj, 'is_source') and place_obj.is_source else "Normal"
            label = place_obj.label if hasattr(place_obj, 'label') else ""
            # CRITICAL: Use initial_marking (static baseline) not tokens (transient state)
            # tokens may be mid-simulation or stale; initial_marking is the design-time value
            # This ensures viability experiments use the correct baseline parameters
            marking = place_obj.initial_marking if hasattr(place_obj, 'initial_marking') else (
                place_obj.tokens if hasattr(place_obj, 'tokens') else 0
            )
            
            self.places_store.append([
                place_obj.id,
                place_obj.name if hasattr(place_obj, 'name') else place_obj.id,
                marking,
                place_type,
                label,
                "white",  # Background color (unused when background_set=False)
                False  # Background set (False = no background)
            ])
        
        # Populate Transitions table
        for transition in model.transitions:
            if transition.id in all_transition_ids:
                rate = transition.rate if hasattr(transition, 'rate') else 1.0
                # Check rate_function in properties dict (where formulas/expressions are actually stored)
                formula = ""
                if hasattr(transition, 'properties') and isinstance(transition.properties, dict):
                    formula = transition.properties.get('rate_function', '') or transition.properties.get('rate_function_display', '')
                
                # Handle case where rate might be a string formula
                if isinstance(rate, str):
                    # If rate is a string formula, move it to formula column and set numeric rate to 0
                    if not formula:  # Only if formula column is empty
                        formula = rate
                    rate = 0.0
                else:
                    try:
                        rate = float(rate)
                    except (ValueError, TypeError):
                        rate = 1.0
                
                trans_type = transition.transition_type if hasattr(transition, 'transition_type') else "continuous"
                label = transition.label if hasattr(transition, 'label') else ""
                self.transitions_store.append([
                    transition.id,
                    transition.name if hasattr(transition, 'name') else transition.id,
                    rate,
                    formula,
                    trans_type,
                    label,
                    "white",  # Background color (unused when background_set=False)
                    False  # Background set (False = no background)
                ])
                
                # Detect formula-referenced places NOW that we have the formula
                if formula and isinstance(formula, str) and formula.strip():
                    formula_places = self._extract_place_ids_from_formula(formula, model, transition.id)
                    if formula_places:
                        # Update selected_localities with formula places
                        if transition.id in self.selected_localities:
                            self.selected_localities[transition.id]['formula_places'] = formula_places
                            # Color the formula places using the standard coloring method
                            for place in formula_places:
                                self._color_locality_place(place)
                            # Trigger canvas redraw to show the new colors
                            self._trigger_canvas_redraw()
                            
                            # Add UI rows for formula places in the localities listbox
                            # Find the transition's row to insert after it
                            transition_row = self.selected_localities[transition.id].get('row')
                            if transition_row:
                                # Get all children to find where to insert
                                children = self.localities_listbox.get_children()
                                insert_index = -1
                                for i, child in enumerate(children):
                                    if child == transition_row:
                                        insert_index = i + 1
                                        # Skip existing place rows (input/output/catalyst)
                                        while insert_index < len(children):
                                            next_child = children[insert_index]
                                            # Check if it's a place row (indented)
                                            hbox = next_child.get_child()
                                            if hbox and hbox.get_margin_start() > 10:
                                                insert_index += 1
                                            else:
                                                break
                                        break
                                
                                # Add formula place rows at the correct position
                                for place in formula_places:
                                    place_row = Gtk.ListBoxRow()
                                    place_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                                    place_hbox.set_margin_start(40)  # Indent like other places
                                    place_hbox.set_margin_end(6)
                                    place_hbox.set_margin_top(1)
                                    place_hbox.set_margin_bottom(1)
                                    
                                    # Checkbox
                                    place_checkbox = Gtk.CheckButton()
                                    place_checkbox.set_active(True)
                                    place_checkbox.place_id = place.id
                                    place_hbox.pack_start(place_checkbox, False, False, 0)
                                    
                                    # Label with formula prefix
                                    place_label_text = f"Formula: {place.id}"
                                    if hasattr(place, 'label') and place.label:
                                        place_label_text += f" ({place.label})"
                                    place_label = Gtk.Label(label=place_label_text)
                                    place_label.set_xalign(0)
                                    place_hbox.pack_start(place_label, True, True, 0)
                                    
                                    place_row.add(place_hbox)
                                    self.localities_listbox.insert(place_row, insert_index)
                                    insert_index += 1
                                
                                # Show new rows
                                self.localities_listbox.show_all()
        
        
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
                arc_type,
                "white",  # Background color (unused when background_set=False)
                False  # Background set (False = no background)
            ])
        
        # Notify automation category that subnet parameters are updated
        # Call synchronously (not idle_add) to ensure parameters refreshed before auto-sync
        if hasattr(self, 'automation_category') and self.automation_category:
            self.automation_category.refresh_parameters()
    
    def _create_subnet_model(self):
        """Build a DocumentModel from the current selected localities.

        Delegates to LocalityController; stores result in ``self.subnet_model``.
        Environment events are copied from the full canvas model so all
        simulation paths (inline, batch, replicate) evaluate scheduled events.
        """
        model = self._locality_ctrl.create_subnet_model(self.selected_localities)
        # Copy environment events from the full document model so that every
        # simulation run on this subnet is aware of the user-defined event schedule.
        base_model = self._get_current_model()
        model.events = list(getattr(base_model, 'events', []) or []) if base_model is not None else []
        self.subnet_model = model
        return model
    
    def _add_formula_referenced_places(self, transitions, places_set):
        """Add formula-referenced places to the subnet place set.

        Delegates to LocalityController.
        """
        self._locality_ctrl.add_formula_referenced_places(transitions, places_set)
    
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
                        place.tokens = new_marking
                        place.initial_marking = new_marking
                        break
            
            # Auto-sync baseline to automation (no manual sync needed)
            self._auto_sync_baseline_to_automation()
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
            
            # Auto-sync baseline to automation (no manual sync needed)
            self._auto_sync_baseline_to_automation()
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
        
        # Auto-sync baseline to automation (no manual sync needed)
        self._auto_sync_baseline_to_automation()
    
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
            
            # Auto-sync baseline to automation (no manual sync needed)
            self._auto_sync_baseline_to_automation()
        except ValueError:
            pass
    
    # ==================== Result Display and Visualization ====================
    
    def _show_investigation_view(self):
        """Show investigation results in UI."""
        
        if not self.current_investigation:
            return
        
        # Safety: ensure results container exists
        if not hasattr(self, 'content_box') or self.content_box is None:
            return
        if not hasattr(self, 'empty_label'):
            self.empty_label = None
        
        # Remove empty state
        if self.empty_label and self.empty_label in self.content_box.get_children():
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
    
    def _show_error(self, message: str):
        """Show error message.
        
        Args:
            message: Error message
        """
        
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
    
    # ==================== Knowledge Base Management ====================
    
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
            except (AttributeError, TypeError) as e:
                self.logger.debug(f"Cannot access model_canvas document for KB: {e}")
                return None
        
        drawing_area = self.drawing_area
        
        try:
            # Get KB for THIS panel's document
            if hasattr(self.model_canvas, 'knowledge_bases'):
                return self.model_canvas.knowledge_bases.get(self.drawing_area)
        except (AttributeError, TypeError, KeyError) as e:
            # Knowledge base not available
            self.logger.debug(f"Cannot access knowledge base: {e}")
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
    
    # ==================== Button Event Handlers ====================
    
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
            # Phase 2.2: Use extracted ViabilityAnalyzer
            model = self._get_current_model()
            kb = self._get_kb()
            simulation = self._get_simulation()
            
            analyzer = ViabilityAnalyzer(model, kb=kb, simulation=simulation, data_cache=self.data_cache)
            result = analyzer.analyze(transition, mode='standard', generate_suggestions=True)
            
            issues = result.issues
            total_issues += len(issues)
            suggestions = result.suggestions
            
            # Categorize suggestions
            for suggestion in suggestions:
                category = suggestion.category.lower()
                if category in all_suggestions_by_category:
                    all_suggestions_by_category[category].append(suggestion)
        
        # Populate summary
        self._populate_summary(total_issues, all_suggestions_by_category, len(checked_transitions))
        
        # REMOVED: Category TreeViews (structural/biological/kinetic suggestions)
        # These sections have been removed from the UI
        
        self._show_feedback(f"Diagnosis complete: {total_issues} issues, {sum(len(s) for s in all_suggestions_by_category.values())} suggestions", "info")
    
    def _on_clear_all_clicked(self, button):
        """Handle 'Clear All' button click.
        
        Clears all localities and resets the entire panel state.
        """
        # Reset colors - fetch objects from CURRENT model
        from shypn.netobjs import Place, Transition, Arc
        
        # Get current model to fetch fresh object references
        model = self._get_current_model()
        if not model:
            pass
        else:
            for transition_id in self.selected_localities.keys():
                locality_ids = self._locality_objects.get(transition_id)
                if not locality_ids:
                    continue
                
                from shypn.utils.color_schema_manager import ColorSchemaManager
                
                # Reset transition color
                ColorSchemaManager.reset_transition_colors(locality_ids.transition)
                
                # Reset input place colors
                for p_obj in locality_ids.input_places:
                    ColorSchemaManager.reset_place_color(p_obj)
                
                # Reset output place colors
                for p_obj in locality_ids.output_places:
                    ColorSchemaManager.reset_place_color(p_obj)
                
                # Reset catalyst place colors
                for p_obj in locality_ids.catalyst_places:
                    ColorSchemaManager.reset_place_color(p_obj)
                
                # Reset input arc colors
                for arc_obj in locality_ids.input_arcs:
                    ColorSchemaManager.reset_arc_color(arc_obj)
                
                # Reset output arc colors
                for arc_obj in locality_ids.output_arcs:
                    ColorSchemaManager.reset_arc_color(arc_obj)
                
                # Reset catalyst arc colors
                for arc_obj in locality_ids.catalyst_arcs:
                    arc_obj.color = Arc.DEFAULT_COLOR
            
            # Trigger canvas redraw to show color changes
            self._trigger_canvas_redraw()
        
        
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
        
        # Disable diagnose button (if enabled in future)
        # if hasattr(self, 'diagnose_button'):
        #     self.diagnose_button.set_sensitive(False)
        
        # Clear results
        self._clear_results()
        
        # Trigger canvas redraw to show reset colors
        self._trigger_canvas_redraw()
        
        self._show_feedback("All localities cleared", "info")
    
    def _clear_results(self):
        """Clear all results (simplified - removed sections no longer exist)."""
        # REMOVED: structural_store, biological_store, kinetic_store
        # REMOVED: summary_box, summary_expander
        # These sections have been removed from the UI
        pass
    
    def _populate_summary(self, total_issues, suggestions_by_category, num_transitions):
        """Populate diagnosis summary section (REMOVED - UI section no longer exists).
        
        Args:
            total_issues: Total number of issues found
            suggestions_by_category: Dict of suggestions by category
            num_transitions: Number of transitions analyzed
        """
        # REMOVED: This method previously populated the Diagnosis Summary expander
        # which has been removed from the UI. Keeping stub for backward compatibility.
        pass
    
    def _populate_suggestions_treeview(self, store, suggestions):
        """Populate a suggestions TreeView with data (REMOVED - UI sections no longer exist).
        
        Args:
            store: Gtk.ListStore to populate
            suggestions: List of Suggestion objects
        """
        # REMOVED: This method previously populated suggestion TreeViews for
        # structural/biological/kinetic categories which have been removed.
        # Keeping stub for backward compatibility.
        pass
    
    # ==================== External Panel Integration ====================
    
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
            import logging
            logging.getLogger(__name__).debug("[VIABILITY_PANEL] New document detected, clearing panel")
            self._clear_panel_for_new_document()
        
        # CRITICAL: Always refresh when switching documents (even between existing tabs)
        # This ensures the UI shows THIS document's data, not stale data from previous tab
        import logging
        logging.getLogger(__name__).debug(f"[VIABILITY_PANEL] Tab switch: drawing_area {prev_drawing_area_id} → {new_drawing_area_id}")
        self.refresh_all()
    
    def _clear_panel_for_new_document(self):
        """Clear all panel data when switching to a new/different document.
        
        This ensures the panel starts fresh for each document, preventing
        data from previous documents from being displayed.
        """
        import logging
        logging.getLogger(__name__).debug("[VIABILITY_CLEAR] Clearing panel data for new document")
        
        # Reset colors before clearing (in case previous document had colored objects)
        from shypn.netobjs import Place, Transition, Arc
        model = self._get_current_model()
        if model:
            for transition_id in self.selected_localities.keys():
                locality_ids = self._locality_objects.get(transition_id)
                if not locality_ids:
                    continue
                
                # Reset all locality colors
                from shypn.utils.color_schema_manager import ColorSchemaManager
                
                ColorSchemaManager.reset_transition_colors(locality_ids.transition)
                
                for p_obj in locality_ids.input_places:
                    ColorSchemaManager.reset_place_color(p_obj)
                for p_obj in locality_ids.output_places:
                    p_obj.border_color = Place.DEFAULT_BORDER_COLOR
                for p_obj in locality_ids.catalyst_places:
                    p_obj.border_color = Place.DEFAULT_BORDER_COLOR
                
                for arc_obj in locality_ids.input_arcs:
                    arc_obj.color = Arc.DEFAULT_COLOR
                for arc_obj in locality_ids.output_arcs:
                    arc_obj.color = Arc.DEFAULT_COLOR
                for arc_obj in locality_ids.catalyst_arcs:
                    arc_obj.color = Arc.DEFAULT_COLOR
            
            self._trigger_canvas_redraw()
        
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
        
        # REMOVED: Clear suggestions stores (structural/biological/kinetic)
        # These sections have been removed from the UI
        
        # Clear investigation
        self.current_investigation = None
        self.current_view = None
        
        import logging
        logging.getLogger(__name__).debug("[VIABILITY_CLEAR] Panel cleared")
    
    # ==================== Panel Refresh and State Management ====================
    
    def refresh_all(self):
        """Refresh all panel data to match current document.
        
        Called when tab switches to update displayed data.
        This ensures the panel shows the correct document's viability state.
        """
        try:
            import logging
            lg = logging.getLogger(__name__)
            lg.debug(f"[VIABILITY_REFRESH] Refreshing panel for drawing_area {id(self.drawing_area) if self.drawing_area else 'None'}")
            lg.debug(f"[VIABILITY_REFRESH] Selected localities: {list(self.selected_localities.keys())}")
            
            # Refresh localities ListBox to show THIS document's selections
            self._refresh_localities_list()
            
            # Refresh subnet parameters tables from current localities
            self._refresh_subnet_parameters()
            
            # Update UI state
            self._update_ui_state()
            
            import logging
            logging.getLogger(__name__).debug("[VIABILITY_REFRESH] Refresh complete")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[VIABILITY_REFRESH] Error refreshing panel: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_localities_list(self):
        """Rebuild localities ListBox to match THIS document's selected_localities.
        
        Called on tab switch to ensure the UI shows the correct document's selections.
        """
        import logging
        logging.getLogger(__name__).debug(f"[VIABILITY_REFRESH_LIST] Rebuilding localities list, {len(self.selected_localities)} transitions")
        
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
        
        # Recreate subnet model after rebuilding localities list
        if self.selected_localities:
            self._create_subnet_model()
        else:
            self.subnet_model = None
    
    def _update_ui_state(self):
        """Update UI state based on current selections."""
        has_localities = len(self.selected_localities) > 0
        # self.diagnose_button.set_sensitive(has_localities)  # Disabled - button removed
    
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
    
    # ==================== Simulation Control Integration ====================
    
    def _on_clear_diagnostics_log(self, button):
        """Clear diagnostics log."""
        self.diagnostics_textbuffer.set_text("")
    
    def _on_run_simulation(self, button):
        """Run simulation to completion."""
        # Refresh subnet parameters from current model to ensure simulation uses latest values
        self._refresh_subnet_parameters()
        
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
            # Refresh subnet parameters from current model before initializing
            self._refresh_subnet_parameters()
            
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
        # Refresh subnet parameters from current model to ensure TreeViews are up-to-date
        self._refresh_subnet_parameters()
        
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
    
    # REMOVED: Save/Load experiment buttons
    # def _on_save_experiments(self, button):
    #     """Export experiments to JSON file."""
    #     ...
    
    # def _on_load_experiments(self, button):
    #     """Import experiments from JSON file."""
    #     ...
    
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
            
            # Update visual indicators if this is a sweep snapshot
            if snapshot.swept_parameter:
                self.update_sweep_indicators(
                    snapshot.swept_parameter['type'],
                    snapshot.swept_parameter['id']
                )
            else:
                # Clear indicators if this is baseline
                self._clear_sweep_indicators()
            
            self._append_diagnostics_log(f"Switched to: {snapshot.name}")
    
    def _auto_sync_baseline_to_automation(self):
        """Automatically sync baseline to automation after parameter edits.
        
        Silently updates automation baseline when user edits subnet parameters.
        No confirmation needed - this is background synchronization.
        """
        if not hasattr(self, 'experiment_manager'):
            return
        
        # Silently sync baseline from current tables
        if hasattr(self.experiment_manager, 'sync_baseline_from_tables'):
            self.experiment_manager.sync_baseline_from_tables(
                self.places_store,
                self.transitions_store,
                self.arcs_store
            )
    
    def _on_sync_baseline(self, button):
        """Sync automation baseline from current table values."""
        if not hasattr(self, 'experiment_manager'):
            return
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Sync Baseline to Automation?"
        )
        dialog.format_secondary_text(
            "This will update the automation baseline with current table values.\n"
            "Any existing experiment sweeps will use these new baseline values.\n\n"
            "Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Sync baseline from current tables
            self.experiment_manager.sync_baseline_from_tables(
                self.places_store,
                self.transitions_store,
                self.arcs_store
            )
            
            # Hide warning
            self.simulation_toolbar.show_stale_baseline_warning(False)
            
            # Clear sweep indicators
            self._clear_sweep_indicators()
            
            self._append_diagnostics_log("✓ Baseline synced to automation")
    
    def update_sweep_indicators(self, swept_param_type, swept_param_id):
        """Highlight the swept parameter row in the appropriate table.
        
        Args:
            swept_param_type: 'place', 'transition', or 'arc'
            swept_param_id: ID of the swept parameter
        """
        # Delegate to SubnetParametersView
        # Convert type names to plural for consistency
        type_mapping = {
            'place': 'places',
            'transition': 'transitions',
            'arc': 'arcs'
        }
        plural_type = type_mapping.get(swept_param_type, swept_param_type)
        self.subnet_params_view.update_sweep_indicators(plural_type, swept_param_id)
    
    # ==================== Batch Sweep Operations ====================
    
    def _clear_sweep_indicators(self):
        """Reset all row backgrounds to white."""
        # Delegate to SubnetParametersView
        self.subnet_params_view.clear_sweep_indicators()
    
    # Context menu handlers moved to SubnetParametersView class
    # These stub methods exist for backward compatibility but delegate to SubnetParametersView
        """Handle right-click on places table to show context menu."""
        if event.button == 3:  # Right-click
            # Get clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path, column, cell_x, cell_y = path_info
            treeview.get_selection().select_path(path)
            
            # Get place data from row
            tree_iter = self.places_store.get_iter(path)
            place_id = self.places_store.get_value(tree_iter, 0)
            place_name = self.places_store.get_value(tree_iter, 1)
            current_marking = self.places_store.get_value(tree_iter, 2)
            
            # Create context menu
            menu = Gtk.Menu()
            
            sweep_item = Gtk.MenuItem(label=f"⇄ Create Sweep for '{place_name}'")
            sweep_item.connect("activate", self._on_create_sweep_from_place, 
                             place_id, place_name, current_marking)
            menu.append(sweep_item)
            
            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)
            return True
        
        return False
    
    def _on_transitions_table_button_press(self, treeview, event):
        """Handle right-click on transitions table to show context menu."""
        if event.button == 3:  # Right-click
            # Get clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path, column, cell_x, cell_y = path_info
            treeview.get_selection().select_path(path)
            
            # Get transition data from row
            tree_iter = self.transitions_store.get_iter(path)
            trans_id = self.transitions_store.get_value(tree_iter, 0)
            trans_name = self.transitions_store.get_value(tree_iter, 1)
            current_rate = self.transitions_store.get_value(tree_iter, 2)
            
            # Create context menu
            menu = Gtk.Menu()
            
            sweep_item = Gtk.MenuItem(label=f"⇄ Create Sweep for '{trans_name}'")
            sweep_item.connect("activate", self._on_create_sweep_from_transition,
                             trans_id, trans_name, current_rate)
            menu.append(sweep_item)
            
            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)
            return True
        
        return False
    
    def _on_arcs_table_button_press(self, treeview, event):
        """Handle right-click on arcs table to show context menu."""
        if event.button == 3:  # Right-click
            # Get clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path, column, cell_x, cell_y = path_info
            treeview.get_selection().select_path(path)
            
            # Get arc data from row
            tree_iter = self.arcs_store.get_iter(path)
            arc_id = self.arcs_store.get_value(tree_iter, 0)
            from_id = self.arcs_store.get_value(tree_iter, 1)
            to_id = self.arcs_store.get_value(tree_iter, 2)
            current_weight = self.arcs_store.get_value(tree_iter, 3)
            
            # Create context menu
            menu = Gtk.Menu()
            
            arc_label = f"{from_id} → {to_id}"
            sweep_item = Gtk.MenuItem(label=f"⇄ Create Sweep for '{arc_label}'")
            sweep_item.connect("activate", self._on_create_sweep_from_arc,
                             arc_id, arc_label, current_weight)
            menu.append(sweep_item)
            
            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)
            return True
        
        return False
    
    def _on_create_sweep_from_place(self, menu_item, place_id, place_name, current_value):
        """Create sweep from right-clicked place parameter."""
        if not hasattr(self, 'automation_category') or not self.automation_category:
            return
        
        # Expand automation section
        self.automation_category.category_frame.set_expanded(True)
        
        # Pre-fill sweep builder with place info
        if hasattr(self.automation_category, 'sweep_builder'):
            self.automation_category.sweep_builder.prefill_parameter(
                param_type='place',
                param_id=place_id,
                param_name=place_name,
                current_value=current_value
            )
    
    def _on_create_sweep_from_transition(self, menu_item, trans_id, trans_name, current_value):
        """Create sweep from right-clicked transition parameter."""
        if not hasattr(self, 'automation_category') or not self.automation_category:
            return
        
        # Expand automation section
        self.automation_category.category_frame.set_expanded(True)
        
        # Evaluate formula to get numeric value for prediction
        evaluated_value = current_value
        if isinstance(current_value, str):
            try:
                # Build context with current place markings
                context = {}
                for place in self.canvas.model.places:
                    context[place.id] = place.tokens
                    if hasattr(place, 'name') and place.name:
                        context[place.name] = place.tokens
                
                # Safely evaluate the formula (replaces eval() for security)
                evaluated_value = safe_eval_numeric(current_value, context, default_on_error=1.0)
            except (ValueError, TypeError, AttributeError) as e:
                # If evaluation fails, try to extract numeric coefficient
                self.logger.debug(f"Formula evaluation failed, extracting coefficient: {e}")
                import re
                match = re.match(r'^([\d.]+)', current_value.strip())
                if match:
                    evaluated_value = float(match.group(1))
                else:
                    evaluated_value = 1.0  # Fallback
        
        # Pre-fill sweep builder with transition info
        if hasattr(self.automation_category, 'sweep_builder'):
            self.automation_category.sweep_builder.prefill_parameter(
                param_type='transition',
                param_id=trans_id,
                param_name=trans_name,
                current_value=evaluated_value
            )
    
    def _on_create_sweep_from_arc(self, menu_item, arc_id, arc_label, current_value):
        """Create sweep from right-clicked arc parameter."""
        if not hasattr(self, 'automation_category') or not self.automation_category:
            return
        
        # Expand automation section
        self.automation_category.category_frame.set_expanded(True)
        
        # Pre-fill sweep builder with arc info
        if hasattr(self.automation_category, 'sweep_builder'):
            self.automation_category.sweep_builder.prefill_parameter(
                param_type='arc',
                param_id=arc_id,
                param_name=arc_label,
                current_value=current_value
            )


