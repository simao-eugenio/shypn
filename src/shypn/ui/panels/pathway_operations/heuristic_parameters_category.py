"""
Heuristic Parameters Category UI

Type-aware parameter inference UI for Pathway Operations panel.

Author: Shypn Development Team
Date: November 2025
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import logging
from typing import Optional, Dict, Any

from .base_pathway_category import BasePathwayCategory
from shypn.crossfetch.controllers import HeuristicParametersController
from shypn.crossfetch.models.transition_types import (
    ContinuousParameters,
    StochasticParameters,
    TimedParameters,
    ImmediateParameters
)


class HeuristicParametersCategory(BasePathwayCategory):
    """UI category for heuristic parameter inference.
    
    Follows the CategoryFrame architecture:
    - Inherits from BasePathwayCategory
    - Implements _build_content() to create UI
    - Minimal UI code, controller handles business logic
    - Wayland-safe (no window creation in __init__)
    """
    
    def __init__(self, model_canvas_loader=None):
        """Initialize UI category.
        
        Args:
            model_canvas_loader: Reference to model canvas loader
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_canvas_loader = model_canvas_loader
        
        # Initialize controller
        self.controller = HeuristicParametersController(model_canvas_loader)
        
        # Initialize base category (will call _build_content)
        super().__init__(category_name="HEURISTIC PARAMETERS", expanded=False)
    
    def _build_content(self):
        """Build the UI components.
        
        Returns:
            Gtk.Widget: The content widget for this category
        """
        # Main container
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_start(10)
        content_box.set_margin_end(10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        
        # Description
        desc = Gtk.Label()
        desc.set_text("Intelligent parameter defaults based on transition type and biological context")
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        desc.get_style_context().add_class('dim-label')
        content_box.pack_start(desc, False, False, 0)
        
        # Analyze button
        self.analyze_button = Gtk.Button(label="Analyze & Infer Parameters")
        self.analyze_button.connect('clicked', self._on_analyze_clicked)
        content_box.pack_start(self.analyze_button, False, False, 0)
        
        # Results view
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        results_scroll.set_min_content_height(200)
        
        # TreeView for results
        # Column order: Selected, ID, Type, Vmax, Km, Kcat, Lambda, Delay, Priority, Confidence, Result object
        self.results_store = Gtk.ListStore(
            bool,      # 0: Selected
            str,       # 1: Transition ID
            str,       # 2: Type
            str,       # 3: Vmax
            str,       # 4: Km
            str,       # 5: Kcat
            str,       # 6: Lambda
            str,       # 7: Delay
            str,       # 8: Priority
            str,       # 9: Confidence
            object     # 10: InferenceResult object
        )
        
        self.results_tree = Gtk.TreeView(model=self.results_store)
        self.results_tree.set_headers_visible(True)
        
        # Selected column with checkbox
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.set_activatable(True)
        renderer_toggle.connect('toggled', self._on_selection_toggled)
        
        # Create column with clickable header
        column_select = Gtk.TreeViewColumn("☐", renderer_toggle, active=0)
        column_select.set_fixed_width(40)
        column_select.set_clickable(True)
        column_select.connect('clicked', self._on_header_column_clicked)
        
        # Store selection state for header toggle
        self._all_selected = False
        
        self.results_tree.append_column(column_select)
        
        # Store reference to column for updating header label
        self.select_column = column_select
        
        # Define columns with widths
        columns = [
            ("ID", 1, 100),
            ("Type", 2, 90),
            ("Vmax", 3, 80),
            ("Km", 4, 80),
            ("Kcat", 5, 80),
            ("Lambda", 6, 80),
            ("Delay", 7, 80),
            ("Priority", 8, 70),
            ("Confidence", 9, 100)
        ]
        
        for title, col_id, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_fixed_width(width)
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            self.results_tree.append_column(column)
        
        results_scroll.add(self.results_tree)
        content_box.pack_start(results_scroll, True, True, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.apply_selected_button = Gtk.Button(label="Apply Selected")
        self.apply_selected_button.connect('clicked', self._on_apply_selected)
        self.apply_selected_button.set_sensitive(False)
        action_box.pack_start(self.apply_selected_button, True, True, 0)
        
        content_box.pack_start(action_box, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.get_style_context().add_class('dim-label')
        content_box.pack_start(self.status_label, False, False, 0)
        
        # Show all widgets
        content_box.show_all()
        
        return content_box
    
    def _on_analyze_clicked(self, button):
        """Handle analyze button click."""
        self.analyze_button.set_sensitive(False)
        self.status_label.set_text("Analyzing model and inferring parameters...")
        
        # Run analysis in background (to avoid blocking UI)
        GLib.idle_add(self._do_analysis)
    
    def _do_analysis(self):
        """Perform analysis (called from idle handler)."""
        try:
            # Analyze model with generic organism (heuristics don't use it)
            results = self.controller.analyze_model(organism="generic")
            
            # Clear previous results
            self.results_store.clear()
            
            # Populate results
            total = 0
            for type_key, type_results in results.items():
                for result in type_results:
                    params = result.parameters
                    
                    # Confidence display
                    confidence_pct = int(params.confidence_score * 100)
                    stars = "⭐" * (confidence_pct // 20)
                    conf_str = f"{confidence_pct}% {stars}"
                    
                    # Extract type-specific parameters
                    vmax = ""
                    km = ""
                    kcat = ""
                    lambda_val = ""
                    delay = ""
                    priority = ""
                    
                    if isinstance(params, ContinuousParameters):
                        if params.vmax is not None:
                            vmax = f"{params.vmax:.4g}"
                        if params.km is not None:
                            km = f"{params.km:.4g}"
                        if params.kcat is not None:
                            kcat = f"{params.kcat:.4g}"
                    elif isinstance(params, StochasticParameters):
                        if params.lambda_param is not None:
                            lambda_val = f"{params.lambda_param:.4g}"
                    elif isinstance(params, TimedParameters):
                        if params.delay is not None:
                            delay = f"{params.delay:.4g} {params.time_unit}"
                    elif isinstance(params, ImmediateParameters):
                        priority = str(params.priority)
                    
                    # Append row: Selected, ID, Type, Vmax, Km, Kcat, Lambda, Delay, Priority, Confidence, Result
                    self.results_store.append([
                        False,  # Not selected by default
                        result.transition_id,
                        params.transition_type.value.capitalize(),
                        vmax,
                        km,
                        kcat,
                        lambda_val,
                        delay,
                        priority,
                        conf_str,
                        result  # Store result object for later use
                    ])
                    total += 1
            
            # Update status
            self.status_label.set_text(f"Found {total} transitions")
            
            # Reset header and buttons
            self._all_selected = False
            self.select_column.set_title("☐")  # Unchecked
            self.apply_selected_button.set_sensitive(False)  # No selection yet
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.status_label.set_text(f"Error: {str(e)}")
        finally:
            self.analyze_button.set_sensitive(True)
        
        return False  # Don't repeat
    
    def _on_selection_toggled(self, renderer, path):
        """Handle selection checkbox toggle.
        
        Args:
            renderer: CellRendererToggle
            path: Tree path string
        """
        # Toggle the selected state
        iter = self.results_store.get_iter(path)
        current_value = self.results_store.get_value(iter, 0)
        new_value = not current_value
        self.results_store.set_value(iter, 0, new_value)
        
        self.logger.debug(f"Toggled row {path}: {current_value} → {new_value}")
        
        # Update button sensitivity based on selection
        has_selection = False
        all_selected = True
        total_rows = 0
        iter = self.results_store.get_iter_first()
        while iter:
            total_rows += 1
            selected = self.results_store.get_value(iter, 0)
            if selected:
                has_selection = True
            else:
                all_selected = False
            iter = self.results_store.iter_next(iter)
        
        # Update header label based on selection state
        if all_selected and total_rows > 0:
            self.select_column.set_title("☑")  # All checked
            self._all_selected = True
        elif has_selection:
            self.select_column.set_title("☒")  # Some checked (indeterminate)
            self._all_selected = False
        else:
            self.select_column.set_title("☐")  # None checked
            self._all_selected = False
        
        self.logger.debug(f"Has selection: {has_selection}")
        self.apply_selected_button.set_sensitive(has_selection)
    
    def _on_header_column_clicked(self, column):
        """Handle header column click (select/deselect all).
        
        Args:
            column: The TreeViewColumn that was clicked
        """
        # Toggle selection state
        self._all_selected = not self._all_selected
        
        self.logger.info(f"Header column clicked: select_all={self._all_selected}")
        
        # Update all checkboxes
        iter = self.results_store.get_iter_first()
        count = 0
        while iter:
            self.results_store.set_value(iter, 0, self._all_selected)
            count += 1
            iter = self.results_store.iter_next(iter)
        
        self.logger.info(f"Updated {count} rows to selected={self._all_selected}")
        
        # Update header label
        if self._all_selected:
            column.set_title("☑")  # Checked
        else:
            column.set_title("☐")  # Unchecked
        
        # Update apply selected button
        self.apply_selected_button.set_sensitive(self._all_selected)
    
    def _on_row_activated(self, treeview, path, column):
        """Handle row activation (double-click).
        
        Args:
            treeview: TreeView widget
            path: Tree path
            column: Column
        """
        # Show parameter details in dialog
        model = treeview.get_model()
        iter = model.get_iter(path)
        result = model.get_value(iter, 10)  # InferenceResult object at column 10
        
        self._show_parameter_details(result)
    
    def _show_parameter_details(self, result):
        """Show parameter details dialog.
        
        Args:
            result: InferenceResult object
        """
        # Get parent window (Wayland-safe)
        parent = self.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
        
        dialog = Gtk.MessageDialog(
            parent=parent,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            text=f"Parameters for {result.transition_id}"
        )
        
        # Format parameter details
        params = result.parameters
        details = []
        
        details.append(f"Type: {params.transition_type.value}")
        details.append(f"Semantics: {params.biological_semantics.value}")
        details.append(f"Confidence: {int(params.confidence_score * 100)}%")
        
        # Type-specific parameters
        param_dict = params.to_dict().get('parameters', {})
        if param_dict:
            details.append("\nParameters:")
            for key, value in param_dict.items():
                if value is not None:
                    details.append(f"  {key}: {value}")
        
        dialog.format_secondary_text("\n".join(details))
        dialog.run()
        dialog.destroy()
    
    def _on_apply_selected(self, button):
        """Handle apply selected button click."""
        print("=" * 60)
        print("=" * 60)
        self.logger.info("=" * 60)
        self.logger.info("[APPLY] Apply Selected button clicked!")
        self.logger.info("=" * 60)
        
        applied_count = 0
        total_rows = 0
        selected_count = 0
        
        # Iterate all rows and apply selected ones
        iter = self.results_store.get_iter_first()
        while iter:
            total_rows += 1
            selected = self.results_store.get_value(iter, 0)  # Checkbox state
            
            self.logger.debug(f"Row {total_rows}: selected={selected}")
            
            if selected:
                selected_count += 1
                result = self.results_store.get_value(iter, 10)  # InferenceResult object at column 10
                
                self.logger.info(f"Applying parameters to {result.transition_id}")
                
                # Apply parameters
                success = self.controller.apply_parameters(
                    result.transition_id,
                    result.parameters.to_dict()
                )
                
                if success:
                    applied_count += 1
                    self.logger.info(f"Successfully applied to {result.transition_id}")
                else:
                    self.logger.warning(f"Failed to apply to {result.transition_id}")
            
            iter = self.results_store.iter_next(iter)
        
        self.logger.info(f"Total rows: {total_rows}, Selected: {selected_count}, Applied: {applied_count}")
        
        # CRITICAL: Reset simulation state after applying parameters
        # This clears cached behaviors that might have old parameter values
        # See: CANVAS_STATE_ISSUES_COMPARISON.md for historical context
        if applied_count > 0:
            self._reset_simulation_after_parameter_changes()
            self.status_label.set_text(f"Applied parameters to {applied_count} transition(s)")
        else:
            if selected_count > 0:
                self.status_label.set_text(f"Failed to apply {selected_count} selected transition(s)")
            else:
                self.status_label.set_text("No transitions selected")
    
    def _reset_simulation_after_parameter_changes(self):
        """Reset simulation to initial state after applying parameter changes.
        
        CRITICAL for correct simulation behavior:
        When parameters are applied to transitions, the simulation controller's
        behavior cache contains old TransitionBehavior instances with old parameter
        values. If we don't reset the simulation, these cached behaviors continue
        to be used, causing transitions to fire incorrectly or not at all.
        
        This is the same root cause as:
        - Behavior Cache Bug (commit 864ae92) - transitions not firing after reload
        - Canvas Freeze Bug (commit df037a6) - canvas frozen after save/reload
        - Comprehensive Reset (commit be02ff5) - stale state across model loads
        
        See: CANVAS_STATE_ISSUES_COMPARISON.md for detailed analysis.
        
        The fix: Call controller.reset() which clears behavior cache AND resets
        place tokens to initial marking, ensuring a clean slate for testing the
        new parameter values.
        """
        try:
            self.logger.info("[RESET] Starting simulation reset after parameter changes...")
            
            # Get current document and canvas manager
            if not self.model_canvas_loader:
                self.logger.error("[RESET] FAILED: No canvas loader available for simulation reset")
                return
            
            self.logger.info(f"[RESET] Canvas loader found: {type(self.model_canvas_loader).__name__}")
            
            drawing_area = self.model_canvas_loader.get_current_document()
            
            if not drawing_area:
                self.logger.error("[RESET] FAILED: No active document for simulation reset")
                return
            
            self.logger.info(f"[RESET] Drawing area found: {drawing_area}")
            
            # Find simulation controller for this drawing area
            if hasattr(self.model_canvas_loader, 'simulation_controllers'):
                self.logger.info(f"[RESET] simulation_controllers attribute exists")
                self.logger.info(f"[RESET] Available controllers: {list(self.model_canvas_loader.simulation_controllers.keys())}")
                
                if drawing_area in self.model_canvas_loader.simulation_controllers:
                    controller = self.model_canvas_loader.simulation_controllers[drawing_area]
                    self.logger.info(f"[RESET] Simulation controller found: {type(controller).__name__}")
                    self.logger.info(f"[RESET] Controller state - Running: {controller.is_running if hasattr(controller, 'is_running') else 'N/A'}")
                    
                    # Get the canvas manager
                    canvas_manager = self.model_canvas_loader.canvas_managers.get(drawing_area)
                    
                    if canvas_manager:
                        self.logger.info(f"[RESET] Canvas manager found: {type(canvas_manager).__name__}")
                        # CRITICAL: Use reset_for_new_model() instead of reset()
                        # This recreates the model adapter and clears ALL caches
                        # After applying parameters, the transition objects have changed
                        # and we need to rebuild the entire simulation state
                        controller.reset_for_new_model(canvas_manager)
                        
                        print(f"[RESET] Transition IDs in controller.model: {[t.id for t in controller.model.transitions[:5]]}")  # First 5
                        self.logger.info("[RESET] ✅ SUCCESS: Simulation fully reset (model adapter recreated)")
                        
                        # DO NOT auto-start simulation after reset
                        # User should manually press "Run" button to start simulation
                        # Auto-starting causes conflicts with manual Run button
                        self.logger.info("[RESET] Ready for simulation (user should press Run to start)")
                    else:
                        self.logger.warning("[RESET] Canvas manager not found, using fallback reset")
                        # Fallback to basic reset if we can't get canvas_manager
                        controller.reset()
                        self.logger.info("[RESET] ✅ SUCCESS: Simulation reset to initial state")
                    
                    # Refresh canvas to show reset token values
                    if drawing_area:
                        drawing_area.queue_draw()
                        self.logger.info("[RESET] Canvas refreshed")
                else:
                    self.logger.warning("[RESET] FAILED: No simulation controller for current document")
            else:
                self.logger.error("[RESET] FAILED: Canvas loader has no simulation_controllers attribute")
                
        except Exception as e:
            self.logger.error(f"Error resetting simulation after parameter changes: {e}", exc_info=True)

