#!/usr/bin/env python3
"""Dynamic Analyses category for Report Panel.

Displays kinetic parameters, enrichments, and simulation data.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
import json
from datetime import datetime
from pathlib import Path

from .base_category import BaseReportCategory
from .widgets import SpeciesConcentrationTable, ReactionActivityTable
from shypn.helpers.batch_results_saver import BatchResultsSaver
from shypn.data.project_models import get_project_manager


class DynamicAnalysesCategory(BaseReportCategory):
    """Dynamic Analyses report category.
    
    Displays:
    - Kinetic parameters summary (Km, Kcat, Ki, Vmax)
    - Applied enrichments (BRENDA, SABIO-RK)
    - Parameter sources and citations
    - Simulation results (future)
    - Sub-expanders for detailed data
    """
    
    def __init__(self, name='Dynamic Analyses', parent_panel=None):
        """Initialize the Dynamic Analyses category.
        
        Args:
            name: Category name to display in header
            parent_panel: Parent ReportPanel instance
        """
        self.title = name
        self.parent_panel = parent_panel
        self.controller = None
        self.model_canvas = None
        self.project = None
        # Track which controllers have callbacks registered to avoid re-registration
        self._registered_controllers = set()
        # Track pending idle_add refresh to prevent stale updates
        self._pending_refresh_id = None
        # Generation counter to reject stale updates
        self._refresh_generation = 0
        # Track selected reaction for auto-refresh after simulation
        self._selected_transition = None
        self._selected_locality = None
        
        # Create category frame
        from shypn.ui.category_frame import CategoryFrame
        self.category_frame = CategoryFrame(
            title=self.title,
            expanded=False
        )
        
        # Build content
        content_widget = self._build_content()
        if content_widget:
            content_widget.show_all()
            self.category_frame.set_content(content_widget)
    
    def _build_content(self):
        """Build dynamic analyses content: Summary first, then sub-expanders."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # === SUMMARY SECTION (Always visible when category is open) ===
        summary_frame = Gtk.Frame()
        summary_frame.set_label("Summary")
        summary_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        summary_box.set_margin_start(12)
        summary_box.set_margin_end(12)
        summary_box.set_margin_top(6)
        summary_box.set_margin_bottom(6)
        
        self.summary_label = Gtk.Label()
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        self.summary_label.set_markup("<i>No simulation or experimental data available</i>")
        summary_box.pack_start(self.summary_label, False, False, 0)
        
        summary_frame.add(summary_box)
        box.pack_start(summary_frame, False, False, 0)
        
        # Sub-expander: Simulation Results (NEW - with tables)
        self.simulation_expander = Gtk.Expander(label="📊 Simulation Data")
        self.simulation_expander.set_expanded(False)
        
        # Create simulation data container
        sim_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        sim_box.set_margin_start(12)
        sim_box.set_margin_end(12)
        sim_box.set_margin_top(12)
        sim_box.set_margin_bottom(12)
        
        # Status label
        self.simulation_status_label = Gtk.Label()
        self.simulation_status_label.set_xalign(0)
        self.simulation_status_label.set_line_wrap(True)
        self.simulation_status_label.set_markup("<i>No simulation data available. Run a simulation to see results.</i>")
        sim_box.pack_start(self.simulation_status_label, False, False, 0)
        
        # Species Concentration Table
        species_label = Gtk.Label()
        species_label.set_markup("<b>Species Concentration</b>")
        species_label.set_xalign(0)
        sim_box.pack_start(species_label, False, False, 0)
        
        self.species_table = SpeciesConcentrationTable()
        self.species_table.set_size_request(-1, 200)
        sim_box.pack_start(self.species_table, True, True, 0)
        
        # Reaction Activity Table
        reaction_label = Gtk.Label()
        reaction_label.set_markup("<b>Reaction Activity</b>")
        reaction_label.set_xalign(0)
        sim_box.pack_start(reaction_label, False, False, 0)
        
        self.reaction_table = ReactionActivityTable()
        self.reaction_table.set_size_request(-1, 200)
        sim_box.pack_start(self.reaction_table, True, True, 0)
        
        # Reaction Selected Table (NEW - shows SUMMARY locality data for selected reaction)
        reaction_selected_label = Gtk.Label()
        reaction_selected_label.set_markup("<b>Reaction Selected</b>")
        reaction_selected_label.set_xalign(0)
        sim_box.pack_start(reaction_selected_label, False, False, 6)
        
        # Create scrolled window for reaction selected table
        selected_scroll = Gtk.ScrolledWindow()
        selected_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        selected_scroll.set_size_request(-1, 150)  # Smaller - summary data only
        
        # Create table with SUMMARY columns: Component, ID, Name, Initial, Final, Min, Max, Avg, Info
        self.reaction_selected_store = Gtk.ListStore(str, str, str, str, str, str, str, str, str)
        self.reaction_selected_table = Gtk.TreeView(model=self.reaction_selected_store)
        self.reaction_selected_table.set_enable_search(True)
        self.reaction_selected_table.set_search_column(1)  # Search by ID
        self.reaction_selected_table.set_grid_lines(Gtk.TreeViewGridLines.NONE)  # Remove all grid lines
        
        # Add columns for summary view
        columns = [
            ("Component", 0, 100),  # "Transition", "Input Place", "Output Place"
            ("ID", 1, 80),
            ("Name", 2, 120),
            ("Initial", 3, 80),
            ("Final", 4, 80),
            ("Min", 5, 80),
            ("Max", 6, 80),
            ("Average", 7, 80),
            ("Info", 8, 120)  # Extra info (firings, rates, etc.)
        ]
        
        for title, col_id, min_width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_resizable(True)
            column.set_sort_column_id(col_id)
            column.set_min_width(min_width)
            self.reaction_selected_table.append_column(column)
        
        selected_scroll.add(self.reaction_selected_table)
        sim_box.pack_start(selected_scroll, True, True, 0)
        
        # Status label for reaction selected (initially shows "awaiting selection")
        self.reaction_selected_status = Gtk.Label()
        self.reaction_selected_status.set_xalign(0)
        self.reaction_selected_status.set_line_wrap(True)
        self.reaction_selected_status.set_markup("<i>No reactions selected. Select one or more reactions from Analyses panel to see locality simulation data.</i>")
        sim_box.pack_start(self.reaction_selected_status, False, False, 0)
        
        self.simulation_expander.add(sim_box)
        box.pack_start(self.simulation_expander, True, True, 0)
        
        # Initial populate
        self.refresh()
        
        return box
    
    def _create_summary_grid(self):
        """Create grid for parameter counts."""
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        
        # Labels
        self.total_label = Gtk.Label(label="0")
        self.km_label = Gtk.Label(label="0")
        self.kcat_label = Gtk.Label(label="0")
        self.ki_label = Gtk.Label(label="0")
        self.vmax_label = Gtk.Label(label="0")
        
        for label in [self.total_label, self.km_label, self.kcat_label, self.ki_label, self.vmax_label]:
            label.set_xalign(0)
        
        # Add to grid
        grid.attach(Gtk.Label(label="Total Parameters:"), 0, 0, 1, 1)
        grid.attach(self.total_label, 1, 0, 1, 1)
        
        grid.attach(Gtk.Label(label="Km (substrate affinity):"), 0, 1, 1, 1)
        grid.attach(self.km_label, 1, 1, 1, 1)
        
        grid.attach(Gtk.Label(label="Kcat (turnover number):"), 0, 2, 1, 1)
        grid.attach(self.kcat_label, 1, 2, 1, 1)
        
        grid.attach(Gtk.Label(label="Ki (inhibition constant):"), 0, 3, 1, 1)
        grid.attach(self.ki_label, 1, 3, 1, 1)
        
        grid.attach(Gtk.Label(label="Vmax (maximum velocity):"), 0, 4, 1, 1)
        grid.attach(self.vmax_label, 1, 4, 1, 1)
        
        return grid
    
    def refresh(self):
        """Refresh dynamic analyses data with experimental and simulation summary."""
        # Refresh simulation data tables
        self._refresh_simulation_data()
        
        # Build comprehensive experimental summary
        summary_lines = []
        
        # 1. Model Information
        if self.model_canvas and hasattr(self.model_canvas, 'model'):
            model = self.model_canvas.model
            num_places = len(model.places) if hasattr(model, 'places') else 0
            num_transitions = len(model.transitions) if hasattr(model, 'transitions') else 0
            summary_lines.append(f"<b>Model:</b> {num_places} species, {num_transitions} reactions")
        
        # 2. Organism & Pathway Information
        if self.project and hasattr(self.project, 'pathways'):
            pathways = self.project.pathways.list_pathways()
            if pathways:
                pass
                # Get unique organisms
                organisms = set()
                for pathway in pathways:
                    if hasattr(pathway, 'source_organism') and pathway.source_organism:
                        organisms.add(pathway.source_organism)
                
                if organisms:
                    summary_lines.append(f"<b>Organism(s):</b> {', '.join(organisms)}")
                
                # Count enrichments
                total_enrichments = sum(len(p.enrichments) for p in pathways if hasattr(p, 'enrichments'))
                if total_enrichments > 0:
                    summary_lines.append(f"<b>Enrichments Applied:</b> {total_enrichments} from BRENDA/SABIO-RK")
        
        # 3. Kinetic Parameters Summary
        if self.model_canvas and hasattr(self.model_canvas, 'model'):
            model = self.model_canvas.model
            kinetic_count = 0
            has_mm = 0
            has_ma = 0
            
            for transition in model.transitions:
                if hasattr(transition, 'rate_function') and transition.rate_function:
                    kinetic_count += 1
                    rate_func = transition.rate_function.lower()
                    if 'michaelis' in rate_func or 'km' in rate_func:
                        has_mm += 1
                    elif 'mass' in rate_func or 'action' in rate_func:
                        has_ma += 1
            
            if kinetic_count > 0:
                summary_lines.append(f"<b>Kinetic Parameters:</b> {kinetic_count} reactions with kinetics")
                if has_mm > 0:
                    summary_lines.append(f"  • Michaelis-Menten: {has_mm}")
                if has_ma > 0:
                    summary_lines.append(f"  • Mass Action: {has_ma}")
        
        # 4. Simulation Status
        if self.controller and self.controller.data_collector:
            data_collector = self.controller.data_collector
            if data_collector.has_data():
                duration = self.controller.settings.duration or 0.0
                num_time_points = len(data_collector.time_points)
                summary_lines.append(f"<b>Simulation:</b> {duration:.2f}s duration, {num_time_points} time points collected")
        
        # Set summary text
        if summary_lines:
            self.summary_label.set_markup('\n'.join(summary_lines))
        else:
            self.summary_label.set_markup("<i>No simulation or experimental data available</i>")
    
    def get_structured_data(self):
        """Get structured dynamic analyses data for document generation.
        
        Returns:
            dict: Dynamic analyses data with keys:
                - title: 'Dynamic Analyses'
                - has_data: Boolean
                - model_info: dict with species/reactions counts
                - organisms: list of organism names
                - enrichments_count: int
                - simulation_parameters: dict with simulation settings
                - simulation_data: dict with species and reactions data tables
        """
        if not self.model_canvas and not self.project:
            return {
                'title': 'Dynamic Analyses',
                'has_data': False,
                'summary': 'No data available'
            }
        
        # Extract model info
        model_info = {}
        if self.model_canvas and hasattr(self.model_canvas, 'model'):
            model = self.model_canvas.model
            model_info = {
                'num_places': len(model.places) if hasattr(model, 'places') else 0,
                'num_transitions': len(model.transitions) if hasattr(model, 'transitions') else 0
            }
        
        # Extract organism and enrichment info
        organisms = []
        enrichments_count = 0
        if self.project and hasattr(self.project, 'pathways'):
            pathways = self.project.pathways.list_pathways()
            organisms_set = set()
            for pathway in pathways:
                if hasattr(pathway, 'source_organism') and pathway.source_organism:
                    organisms_set.add(pathway.source_organism)
            organisms = list(organisms_set)
            enrichments_count = sum(len(p.enrichments) for p in pathways if hasattr(p, 'enrichments'))
        
        # Extract simulation parameters from stored data
        simulation_parameters = {}
        
        # Get report_data from the current document's overlay_manager
        report_data = None
        if hasattr(self, 'parent_panel') and self.parent_panel:
            model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
            if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                # Find which drawing_area has this controller
                if self.controller:
                    for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                        if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller is self.controller:
                            if hasattr(overlay_manager, 'report_data'):
                                report_data = overlay_manager.report_data
                            break
        
        if report_data and report_data.has_simulation_data():
            sim_data = report_data.last_simulation_data
            metadata = sim_data.get('metadata', {})
            
            # Calculate statistics
            num_time_points = len(sim_data.get('time_points', []))
            total_steps = num_time_points - 1 if num_time_points > 0 else 0
            
            # Calculate total firings
            total_firings = 0
            for firing_series in sim_data.get('transition_data', {}).values():
                if firing_series:
                    # firing_series is list of (time, count) tuples
                    last_entry = firing_series[-1]
                    if isinstance(last_entry, tuple):
                        total_firings += last_entry[1]  # Extract count from (time, count)
                    else:
                        total_firings += last_entry  # Fallback for raw values
            
            duration = metadata.get('duration', 0)
            avg_rate = total_firings / duration if duration > 0 else 0
            
            simulation_parameters = {
                'timestamp': metadata.get('timestamp', ''),
                'time_step': metadata.get('time_step'),
                'target_duration': metadata.get('target_duration'),
                'actual_duration': duration,
                'time_scale': metadata.get('time_scale', 1.0),
                'num_time_points': num_time_points,
                'total_steps': total_steps,
                'total_firings': total_firings,
                'avg_firing_rate': avg_rate
            }
        
        # Extract simulation data if available
        simulation_data = {
            'species': [],
            'reactions': []
        }
        
        if self.species_table and hasattr(self.species_table, 'store'):
            for row in self.species_table.store:
                simulation_data['species'].append({
                    'name': row[0],
                    'id': row[1],
                    'initial': row[2],
                    'final': row[3],
                    'min': row[4],
                    'max': row[5],
                    'avg': row[6]
                })
        
        if self.reaction_table and hasattr(self.reaction_table, 'store'):
            for row in self.reaction_table.store:
                simulation_data['reactions'].append({
                    'name': row[0],
                    'id': row[1],
                    'avg_rate': row[2],
                    'total_firings': row[3],
                    'status': row[4]
                })
        
        # Extract reaction selected data (locality summary)
        if self.reaction_selected_store:
            simulation_data['reactions_selected'] = []
            for row in self.reaction_selected_store:
                simulation_data['reactions_selected'].append({
                    'component': row[0],
                    'id': row[1],
                    'name': row[2],
                    'initial': row[3],
                    'final': row[4],
                    'min': row[5],
                    'max': row[6],
                    'average': row[7],
                    'info': row[8]
                })
        
        return {
            'title': 'Dynamic Analyses',
            'has_data': bool(model_info or organisms or enrichments_count > 0 or simulation_data['species'] or simulation_parameters),
            'model_info': model_info,
            'organisms': organisms,
            'enrichments_count': enrichments_count,
            'simulation_parameters': simulation_parameters,
            'simulation_data': simulation_data
        }
    
    def export_to_text(self):
        """Export as plain text."""
        if not self.project:
            return "# DYNAMIC ANALYSES\n\nNo project loaded\n"
        
        text = [
            "# DYNAMIC ANALYSES",
            "",
            "## Summary"
        ]
        
        # Get summary text (remove markup)
        import re
        summary_text = self.summary_label.get_text()
        # Remove markup tags
        summary_text = re.sub(r'<[^>]+>', '', summary_text)
        text.append(summary_text)
        text.append("")
        
        # Include simulation data if available
        if self.simulation_expander.get_expanded():
            text.append("## Simulation Data")
            text.append("")
            text.append("### Species Concentration")
            text.append("(Table data - export feature to be implemented)")
            text.append("")
            text.append("### Reaction Activity")
            text.append("(Table data - export feature to be implemented)")
            text.append("")
        
        return "\n".join(text)
    
    def set_dynamic_analyses_panel(self, panel):
        """Set reference to Dynamic Analyses Panel for data integration.
        
        Args:
            panel: DynamicAnalysesPanel instance
        """
        self.dynamic_analyses_panel = panel
    
    def set_pathway_operations_panel(self, panel):
        """Set reference to Pathway Operations Panel for pathway data.
        
        This allows the report to display information about imported pathways
        (KEGG, SBML, BioModels) including their enrichments and metadata.
        
        Args:
            panel: PathwayOperationsPanel instance
        """
        self.pathway_operations_panel = panel
        
    def set_controller(self, controller):
        """Set simulation controller reference.
        
        Args:
            controller: SimulationController instance
        """
        # Cancel any pending refresh from previous controller
        if self._pending_refresh_id is not None:
            from gi.repository import GLib
            GLib.source_remove(self._pending_refresh_id)
            self._pending_refresh_id = None
        
        # Increment generation to invalidate any in-flight refreshes
        self._refresh_generation += 1
        current_generation = self._refresh_generation
        
        # Store the old controller before updating
        old_controller = self.controller
        self.controller = controller
        
        # Immediately refresh to show this document's data
        # This reads from the document's stored data, not from the controller's live data_collector
        self._refresh_simulation_data(generation=current_generation)
        
        # Register callback for simulation complete
        # IMPORTANT: Only register the callback ONCE per controller to avoid overwriting
        # Check if this controller already has our callback registered
        if controller and id(controller) not in self._registered_controllers:
            # Use GLib.idle_add to ensure UI update happens on main thread
            from gi.repository import GLib
            # CRITICAL: Capture controller by value (not self.controller which changes)
            # At callback time, check if this specific controller is still the active one
            captured_controller = controller
            
            # CRITICAL: Preserve any existing callback (e.g., from Viability Panel)
            # Create a combined callback that calls both
            existing_callback = getattr(controller, 'on_simulation_complete', None)
            
            def on_complete():
                # MULTI-DOCUMENT FIX: Capture data to document's report_data
                # Get the drawing_area for this controller from model_canvas_loader
                if hasattr(self, 'parent_panel') and self.parent_panel:
                    model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
                    if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                        # Find which drawing_area has this controller
                        for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                            if hasattr(overlay_manager, 'simulation_controller'):
                                if overlay_manager.simulation_controller is captured_controller:
                                    # Capture simulation data to document's report_data
                                    if hasattr(overlay_manager, 'report_data'):
                                        overlay_manager.report_data.capture_simulation_results(captured_controller)
                                    break
                
                # Auto-save simulation data to project folder
                try:
                    # Get simulation data from controller's data_collector
                    if hasattr(captured_controller, 'data_collector'):
                        dc = captured_controller.data_collector
                        if dc and dc.has_data():
                            sim_data = {
                                'time_points': dc.time_points,
                                'place_data': dc.place_data,
                                'transition_data': dc.transition_data,
                                'model': captured_controller.model,
                                'metadata': {},
                                'accounting_report': None
                            }
                            
                            # Get accounting report if available
                            if hasattr(captured_controller, 'get_accounting_report'):
                                sim_data['accounting_report'] = captured_controller.get_accounting_report()
                            
                            # Auto-save DISABLED - was causing UI freeze
                            # Results remain in Report Panel for manual export if needed
                            # self._auto_save_simulation(sim_data)
                except Exception as e:
                    print(f"Error during simulation auto-save: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Only refresh UI if this captured controller is still the active one
                if self.controller is captured_controller:
                    # Capture the current generation when callback fires
                    callback_generation = self._refresh_generation
                    self._pending_refresh_id = GLib.idle_add(lambda: self._refresh_and_clear_pending(callback_generation))
                
                # Call any existing callback that was registered before us (e.g., Viability Panel)
                if existing_callback and callable(existing_callback):
                    try:
                        existing_callback()
                    except Exception as e:
                        pass  # Silently ignore errors in chained callbacks
            
            # Set the combined callback on this controller
            controller.on_simulation_complete = on_complete
            self._registered_controllers.add(id(controller))
    
    def _refresh_and_clear_pending(self, generation):
        """Helper to refresh and clear pending ID. Returns False to remove from idle.
        
        Args:
            generation: The refresh generation this callback belongs to
        """
        self._pending_refresh_id = None
        
        # Check if this refresh is still valid
        if generation == self._refresh_generation:
            self._refresh_simulation_data(generation=generation)
        
        return False  # Remove from idle queue
            
    def _refresh_simulation_data(self, generation=None):
        """Refresh simulation data tables.
        
        Args:
            generation: Optional generation number to validate this refresh is still current
        """
        # Check generation if provided
        if generation is not None and generation != self._refresh_generation:
            return
        
        # Store the controller we're about to use
        refresh_controller = self.controller
        refresh_controller_id = id(refresh_controller) if refresh_controller else None
        
        if not self.controller:
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
        
        # MULTI-DOCUMENT FIX: Get data from document's report_data snapshot, not live data_collector
        # This ensures each tab shows its own stored data, not the currently active controller's data
        report_data = None
        if hasattr(self, 'parent_panel') and self.parent_panel:
            model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
            if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                # Find which drawing_area has this controller
                for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                    if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller is refresh_controller:
                        if hasattr(overlay_manager, 'report_data'):
                            report_data = overlay_manager.report_data
                        break
        
        # Check if we have stored simulation data for this document
        if not report_data:
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
        
        if not report_data.has_simulation_data():
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
        
        # Get the stored simulation data (snapshot, not live)
        sim_data = report_data.last_simulation_data
        
        # CRITICAL: Convert tuple format to raw values for analyzers
        # The stored data has (time, value) tuples, but analyzers expect raw values
        # Create temporary data structures with just the values
        place_data_raw = {}
        for place_id, series in sim_data['place_data'].items():
            # Extract values from (time, tokens) tuples
            place_data_raw[place_id] = [entry[1] if isinstance(entry, tuple) else entry for entry in series]
        
        transition_data_raw = {}
        for trans_id, series in sim_data['transition_data'].items():
            # Extract values from (time, count) tuples
            transition_data_raw[trans_id] = [entry[1] if isinstance(entry, tuple) else entry for entry in series]
        
        # Create a temporary data structure that mimics data_collector format
        class TempDataCollector:
            def __init__(self, time_points, place_data, transition_data, model):
                self.time_points = time_points
                self.place_data = place_data
                self.transition_data = transition_data
                self.model = model  # Access to model for places/transitions
            
            def get_place_series(self, place_id):
                return self.time_points, self.place_data.get(place_id, [])
            
            def get_transition_series(self, transition_id):
                return self.time_points, self.transition_data.get(transition_id, [])
        
        temp_collector = TempDataCollector(
            sim_data['time_points'],
            place_data_raw,
            transition_data_raw,
            self.controller.model  # Pass model for analyzer access
        )
        # print(f"[DEBUG_TABLES] Retrieved stored simulation data")
        # print(f"[DEBUG_TABLES] time_points length: {len(sim_data['time_points'])}")
        # print(f"[DEBUG_TABLES] place_data keys: {list(sim_data['place_data'].keys())}")
        # print(f"[DEBUG_TABLES] transition_data keys: {list(sim_data['transition_data'].keys())}")
        
        # Get model name for verification
        model_name = "Unknown"
        if hasattr(self.controller, 'model') and self.controller.model:
            model_name = getattr(self.controller.model, 'name', 
                               getattr(self.controller.model, 'id', 'Untitled'))
        # print(f"[DEBUG_TABLES] ⚡ REFRESHING DATA FOR MODEL: {model_name}")
        
        # Check transition firing counts from stored data
        for t_id, firing_series in sim_data['transition_data'].items():
            pass
            # print(f"[DEBUG_TABLES] Transition {t_id}: firing_series length={len(firing_series)}")
            if firing_series:
                pass
                # print(f"[DEBUG_TABLES]   First 5 values: {firing_series[:5]}")
                # print(f"[DEBUG_TABLES]   Last 5 values: {firing_series[-5:]}")
                # print(f"[DEBUG_TABLES]   Final count: {firing_series[-1]}")
        
        # Get duration from stored metadata
        duration = sim_data['metadata'].get('duration', 0)
        # print(f"[DEBUG_TABLES] duration (from stored metadata) = {duration}")
        
        # Update Summary section with simulation metadata from stored data
        # print("[DEBUG_TABLES] About to call _update_summary...")
        try:
            self._update_summary(duration, sim_data)
            # print("[DEBUG_TABLES] _update_summary completed successfully")
        except Exception as e:
            pass
            # print(f"[DEBUG_TABLES] ⚠️  Error updating summary: {e}")
            import traceback
            traceback.print_exc()
        # print("[DEBUG_TABLES] After _update_summary call")
        
        # Show first few data points for debugging
        if len(sim_data['time_points']) > 0:
            pass
            # print(f"[DEBUG_TABLES] First 5 time points: {sim_data['time_points'][:5]}")
            # print(f"[DEBUG_TABLES] Last 5 time points: {sim_data['time_points'][-5:]}")
            # print(f"[DEBUG_TABLES] Total time points: {len(sim_data['time_points'])}")
            
            # Show place data sample
            for place_id in list(sim_data['place_data'].keys())[:2]:  # First 2 places
                place_values = sim_data['place_data'][place_id]
                if place_values:
                    pass
                    # print(f"[DEBUG_TABLES] Place {place_id}: first={place_values[0]}, last={place_values[-1]}, len={len(place_values)}")
                else:
                    pass
                    # print(f"[DEBUG_TABLES] Place {place_id}: EMPTY!")
            
            # Show transition data sample
            for trans_id in list(sim_data['transition_data'].keys())[:2]:  # First 2 transitions
                trans_values = sim_data['transition_data'][trans_id]
                if trans_values:
                    pass
                    # print(f"[DEBUG_TABLES] Transition {trans_id}: first={trans_values[0]}, last={trans_values[-1]}, len={len(trans_values)}")
                else:
                    pass
                    # print(f"[DEBUG_TABLES] Transition {trans_id}: EMPTY!")
        else:
            pass
            # print(f"[DEBUG_TABLES] ⚠️  time_points list is EMPTY!")
        
        # Analyze species
        from shypn.engine.simulation.analysis import SpeciesAnalyzer, ReactionAnalyzer
        
        # CRITICAL: Check if controller changed during analysis
        if self.controller is not refresh_controller:
            pass
            # print(f"[DEBUG_TABLES] ⚠️  Controller changed during analysis (was {refresh_controller_id}, now {id(self.controller)}), aborting")
            return
        
        # print("[DEBUG_TABLES] Analyzing species...")
        try:
            # Use the temp_collector that has raw values (tuples already unpacked)
            species_analyzer = SpeciesAnalyzer(temp_collector)
            species_metrics = species_analyzer.analyze_all_species(duration)
            # print(f"[DEBUG_TABLES] Got {len(species_metrics)} species metrics")
            
            # Show first metric sample
            if species_metrics:
                sample = species_metrics[0]
                # print(f"[DEBUG_TABLES] Sample species metric: {sample.place_name}, init={sample.initial_tokens}, final={sample.final_tokens}, min={sample.min_tokens}, max={sample.max_tokens}")
            
            self.species_table.populate(species_metrics)
            # print("[DEBUG_TABLES] Species table populated")
            
            # Check again before continuing
            if self.controller is not refresh_controller:
                pass
                # print(f"[DEBUG_TABLES] ⚠️  Controller changed after species analysis, aborting")
                return
        except Exception as e:
            pass
            # print(f"[DEBUG_TABLES] ❌ Error analyzing species: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Analyze reactions
        # print("[DEBUG_TABLES] Analyzing reactions...")
        try:
            reaction_analyzer = ReactionAnalyzer(temp_collector)
            reaction_metrics = reaction_analyzer.analyze_all_reactions(duration)
            # print(f"[DEBUG_TABLES] Got {len(reaction_metrics)} reaction metrics")
            
            # Show first metric sample
            if reaction_metrics:
                sample = reaction_metrics[0]
                # print(f"[DEBUG_TABLES] Sample reaction metric: {sample.transition_name}, firings={sample.firing_count}, rate={sample.average_rate}, status={sample.status}")
            
            self.reaction_table.populate(reaction_metrics)
            # print("[DEBUG_TABLES] Reaction table populated")
        except Exception as e:
            pass
            # print(f"[DEBUG_TABLES] ❌ Error analyzing reactions: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Update status
        num_species = len(species_metrics)
        num_reactions = len(reaction_metrics)
        num_time_points = len(sim_data['time_points'])
        
        self.simulation_status_label.set_markup(
            f"<i>Analyzed {num_species} species and {num_reactions} reactions "
            f"over {num_time_points} time points (duration: {duration:.2f}s)</i>"
        )
        
        # Auto-expand the simulation data expander when data is available
        if not self.simulation_expander.get_expanded():
            pass
            # print("[DEBUG_TABLES] Auto-expanding simulation data section")
            self.simulation_expander.set_expanded(True)
        
        # Auto-expand the category itself when data arrives
        if hasattr(self, 'category_frame') and self.category_frame:
            if not self.category_frame.expanded:
                pass
                # print("[DEBUG_TABLES] Auto-expanding Dynamic Analyses category")
                self.category_frame.set_expanded(True)
        
        # Notify export toolbar that simulation data is available
        if self.parent_panel and hasattr(self.parent_panel, 'export_toolbar'):
            self.parent_panel.export_toolbar.update_simulation_data_availability(True)
        
        # Ensure all widgets are visible and properly rendered
        self.summary_label.show()
        self.simulation_status_label.show()
        self.species_table.show_all()
        self.reaction_table.show_all()
        self.simulation_expander.show_all()
        
        # CRITICAL: Always refresh Reaction Selected table after simulation completes
        # This table queries TransitionRatePanel.selected_objects directly, so we don't 
        # need to check _selected_transition/_selected_locality (which are deprecated)
        try:
            self._populate_reaction_selected_table()
        except Exception as e:
            import traceback
            traceback.print_exc()
        
        # Force a redraw of the parent widget to ensure visibility
        if hasattr(self, 'category_frame') and self.category_frame:
            self.category_frame.queue_draw()
        
        # print("[DEBUG_TABLES] All widgets shown and expanders expanded")
    
    def _update_summary(self, duration: float, sim_data: dict):
        """Update Summary section with simulation metadata.
        
        Args:
            duration: Actual simulation duration in seconds
            sim_data: Dictionary with stored simulation data
        """
        try:
            from datetime import datetime
            
            
            # Get simulation timestamp from stored metadata
            timestamp_str = sim_data['metadata'].get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Get model info
            model = self.controller.model if self.controller else None
            
            model_name = "Unknown"
            num_places = 0
            num_transitions = 0
            
            if model:
                model_name = getattr(model, 'name', getattr(model, 'id', 'Untitled Model'))
                
                num_places = len(getattr(model, 'places', []))
                num_transitions = len(getattr(model, 'transitions', []))
            
            # Get simulation settings from stored metadata
            metadata = sim_data['metadata']
            time_step = metadata.get('time_step')
            target_duration = metadata.get('target_duration')
            time_scale = metadata.get('time_scale', 1.0)
            
            # Format target duration string (handle None case)
            if target_duration is None:
                target_duration_str = "Not set"
            else:
                target_duration_str = f"{target_duration:.2f} s"
            
            
            # Get data statistics from stored data
            num_time_points = len(sim_data['time_points'])
            total_steps = num_time_points - 1 if num_time_points > 0 else 0
            
            # Calculate total firings from stored data
            total_firings = 0
            for firing_series in sim_data['transition_data'].values():
                if firing_series:
                    # firing_series is list of (time, count) tuples
                    # Extract the count value from the last tuple
                    last_entry = firing_series[-1]
                    if isinstance(last_entry, tuple):
                        total_firings += last_entry[1]  # Extract count from (time, count)
                    else:
                        total_firings += last_entry  # Fallback for raw values
            
            # Format time_step (handle None case)
            if time_step is None or time_step == 0.0:
                time_step_str = "Not set"
            else:
                time_step_str = f"{time_step:.4f} s"
            
            # Build summary text
            if duration > 0:
                avg_rate = total_firings / duration
                summary_text = f"""<b>Simulation Summary</b>

<b>Date/Time:</b> {timestamp_str}
<b>Model:</b> {model_name}
<b>Network Size:</b> {num_places} places, {num_transitions} transitions

<b>Simulation Parameters:</b>
  • Time Step (dt): {time_step_str}
  • Target Duration: {target_duration_str}
  • Actual Duration: {duration:.2f} s
  • Time Scale: {time_scale:.1f}x
  • Total Steps: {total_steps}
  
<b>Activity Summary:</b>
  • Time Points Recorded: {num_time_points}
  • Total Transition Firings: {total_firings}
  • Average Firing Rate: {avg_rate:.2f} firings/s"""
            else:
                summary_text = f"""<b>Simulation Summary</b>

<b>Date/Time:</b> {timestamp_str}
<b>Model:</b> {model_name}
<b>Network Size:</b> {num_places} places, {num_transitions} transitions

<b>Simulation Parameters:</b>
  • Time Step (dt): {time_step_str}
  • Target Duration: {target_duration_str}
  • Total Steps: {total_steps}
  
<b>Activity Summary:</b>
  • Time Points Recorded: {num_time_points}
  • Total Transition Firings: {total_firings}"""
            
            self.summary_label.set_markup(summary_text)
            self.summary_label.show()  # Ensure label is visible
            
        except Exception as e:
            pass
            # If summary update fails, don't block table population
            import traceback
            traceback.print_exc()
            self.summary_label.set_markup("<i>Error generating summary</i>")
            self.summary_label.show()  # Show error message
    
    def get_widget(self):
        """Get the category frame widget.
        
        Returns:
            CategoryFrame: The category widget to add to parent container
        """
        return self.category_frame
    
    def set_project(self, project):
        """Set project reference.
        
        Args:
            project: Project instance
        """
        self.project = project
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas reference and update controller.
        
        This is called during tab switching to update the category with the
        current document's model manager. We also need to update the controller
        to match the current document.
        
        Args:
            model_canvas: ModelCanvas instance (ModelCanvasManager)
        """
        self.model_canvas = model_canvas
        
        # CRITICAL: Also update controller when model_canvas changes (e.g., tab switching)
        # The controller must match the current document to show correct simulation data
        if hasattr(self, 'parent_panel') and self.parent_panel:
            model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
            if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                # Find the overlay_manager for the current document
                current_da = model_canvas_loader.get_current_document() if hasattr(model_canvas_loader, 'get_current_document') else None
                if current_da:
                    overlay_manager = model_canvas_loader.overlay_managers.get(current_da)
                    if overlay_manager and hasattr(overlay_manager, 'simulation_controller'):
                        # Update controller to match the current document
                        new_controller = overlay_manager.simulation_controller
                        if new_controller != self.controller:
                            # Controller changed - update it but DON'T register callback
                            # (callback is already registered during initial set_controller call)
                            self.controller = new_controller
                            # NOTE: Don't call _refresh_simulation_data() here
                            # refresh_all() will be called by ReportPanel right after this
    
    def set_selected_reaction(self, transition, locality):
        """Set the selected reaction and populate the locality simulation data table.
        
        Called from Analyses panel when a transition is selected for analysis.
        Shows time-series data for the selected locality (input places → transition → output places).
        
        Args:
            transition: The selected transition object
            locality: LocalityData object with input_places and output_places lists
        """
        
        # Store selection in BOTH instance variables (for immediate use) AND document's report_data (for persistence)
        self._selected_transition = transition
        self._selected_locality = locality
        
        # Store in document's report_data for persistence across tab switches
        if hasattr(self, 'parent_panel') and self.parent_panel:
            model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
            if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                    if hasattr(overlay_manager, 'report_data'):
                        overlay_manager.report_data.selected_transition = transition
                        overlay_manager.report_data.selected_locality = locality
                        break
        
        if not transition or not locality:
            # Clear table and show "awaiting selection" message
            self.reaction_selected_store.clear()
            self.reaction_selected_status.set_markup(
                "<i>No reactions selected. Select one or more reactions from Analyses panel to see locality simulation data.</i>"
            )
            self.reaction_selected_status.show()
            return
        
        # Try to populate with existing data
        self._populate_reaction_selected_table()
    
    def _populate_reaction_selected_table(self):
        """Populate the Reaction Selected table with transition from Analyses panel.
        
        Instead of storing selection separately, we query the TransitionRatePanel
        (Analyses panel) to get the currently selected transition, just like it
        does for plotting. This ensures consistency with the Global Canvas State Lifecycle.
        
        This method can be called:
        1. When transition is selected (via set_selected_reaction callback)
        2. When simulation completes (via _refresh_simulation_data)
        3. When switching tabs (via refresh) - will check Analyses panel state
        """
        # Get the PER-DOCUMENT TransitionRatePanel from analyses_panel_loader
        # NOT from right_panel_loader (which is global)
        transition_panel = None
        if hasattr(self, 'parent_panel') and self.parent_panel:
            model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
            
            if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers') and self.controller:
                # Find the drawing_area for the current controller
                for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                    if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller is self.controller:
                        # Get the per-document analyses panel
                        if hasattr(overlay_manager, 'analyses_panel_loader') and overlay_manager.analyses_panel_loader:
                            analyses_panel_loader = overlay_manager.analyses_panel_loader
                            if hasattr(analyses_panel_loader, 'panel') and analyses_panel_loader.panel:
                                analyses_panel = analyses_panel_loader.panel
                                # Get the transitions category panel
                                if hasattr(analyses_panel, 'transitions_category') and analyses_panel.transitions_category:
                                    transition_panel = analyses_panel.transitions_category.panel
                        break
        
        if not transition_panel:
            # DON'T clear the table! Just show message
            self.reaction_selected_status.set_markup(
                "<i>No reactions selected. Select one or more reactions from Analyses panel to see locality simulation data.</i>"
            )
            self.reaction_selected_status.show()
            return
        
        # Check if there are any selected transitions in the Analyses panel
        if not hasattr(transition_panel, 'selected_objects') or not transition_panel.selected_objects:
            # DON'T clear the table! Just show message
            self.reaction_selected_status.set_markup(
                "<i>No reactions selected. Select one or more reactions from Analyses panel to see locality simulation data.</i>"
            )
            self.reaction_selected_status.show()
            return
        
        # Use ALL selected transitions (multi-selection support)
        selected_transitions = list(transition_panel.selected_objects)
        
        # Detect locality for each transition
        from shypn.diagnostic import LocalityDetector
        detector = None
        if hasattr(transition_panel, '_model_manager') and transition_panel._model_manager:
            detector = LocalityDetector(transition_panel._model_manager)
        
        if not detector:
            self.reaction_selected_status.set_markup(
                "<i>Cannot detect localities: no model manager available.</i>"
            )
            self.reaction_selected_status.show()
            return
        
        # Build list of (transition, locality) pairs for valid localities
        valid_selections = []
        invalid_count = 0
        for transition in selected_transitions:
            locality = detector.get_locality_for_transition(transition)
            if locality and locality.is_valid:
                valid_selections.append((transition, locality))
            else:
                invalid_count += 1
        
        if not valid_selections:
            # All selected transitions lack valid locality
            self.reaction_selected_status.set_markup(
                f"<i>None of the {len(selected_transitions)} selected transition(s) have valid localities (need input → transition → output).</i>"
            )
            self.reaction_selected_status.show()
            return
        
        
        # Get simulation data from THIS document's report_data
        # Search through overlay_managers to find which drawing_area has the current controller
        report_data = None
        if self.controller and hasattr(self, 'parent_panel') and self.parent_panel:
            model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
            if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                # Find which drawing_area has this controller
                for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                    if hasattr(overlay_manager, 'simulation_controller'):
                        if overlay_manager.simulation_controller is self.controller:
                            if hasattr(overlay_manager, 'report_data'):
                                report_data = overlay_manager.report_data
                                break
                            else:
                                break
        
        if not report_data:
            self.reaction_selected_store.clear()
            self.reaction_selected_status.set_markup(
                "<i>No simulation data available.</i>"
            )
            self.reaction_selected_status.show()
            return
        
        if not report_data or not report_data.has_simulation_data():
            self.reaction_selected_store.clear()
            self.reaction_selected_status.set_markup(
                f"<i>No simulation data for selected reaction(s). Run a simulation first.</i>"
            )
            self.reaction_selected_status.show()
            return
        
        
        # Get stored simulation data
        sim_data = report_data.last_simulation_data
        time_points = sim_data['time_points']
        
        # CRITICAL: Extract values from (time, value) tuples
        # The stored data has tuples, but we need raw values for calculations
        place_data_raw = {}
        for place_id, series in sim_data['place_data'].items():
            # Extract token values from (time, tokens) tuples
            place_data_raw[place_id] = [entry[1] if isinstance(entry, tuple) else entry for entry in series]
        
        transition_data_raw = {}
        for trans_id, series in sim_data['transition_data'].items():
            # Extract count values from (time, count) tuples
            transition_data_raw[trans_id] = [entry[1] if isinstance(entry, tuple) else entry for entry in series]
        
        place_data = place_data_raw
        transition_data = transition_data_raw
        
        
        # Clear and populate table with SUMMARY statistics for ALL selected reactions
        self.reaction_selected_store.clear()
        
        # Helper function to calculate statistics
        def calc_stats(data_series):
            """Calculate min, max, average from a data series."""
            if not data_series:
                return 0, 0, 0
            return min(data_series), max(data_series), sum(data_series) / len(data_series)
        
        # Track totals for summary
        total_transitions = 0
        total_input_places = 0
        total_output_places = 0
        
        # Process each valid transition/locality pair
        for idx, (transition, locality) in enumerate(valid_selections):
            # Add TRANSITION row
            trans_id = transition.id
            trans_name = getattr(transition, 'name', trans_id) or trans_id
            if trans_id in transition_data and transition_data[trans_id]:
                firings_series = transition_data[trans_id]
                total_firings = sum(firings_series)
                min_firings, max_firings, avg_firings = calc_stats(firings_series)
                duration = time_points[-1] - time_points[0] if len(time_points) > 1 else 1
                avg_rate = total_firings / duration if duration > 0 else 0
                
                self.reaction_selected_store.append([
                    "Transition",
                    trans_id,
                    trans_name,
                    "-",  # Initial (N/A for transitions)
                    "-",  # Final (N/A for transitions)
                    f"{min_firings:.0f}",
                    f"{max_firings:.0f}",
                    f"{avg_firings:.2f}",
                    f"{total_firings:.0f} firings ({avg_rate:.2f}/s)"
                ])
                total_transitions += 1
            
            # Add INPUT PLACE rows
            for place in locality.input_places:
                place_id = place.id
                place_name = getattr(place, 'name', place_id) or place_id
                if place_id in place_data and place_data[place_id]:
                    tokens_series = place_data[place_id]
                    initial = tokens_series[0] if tokens_series else 0
                    final = tokens_series[-1] if tokens_series else 0
                    min_tokens, max_tokens, avg_tokens = calc_stats(tokens_series)
                    consumed = initial - final
                    duration = time_points[-1] - time_points[0] if len(time_points) > 1 else 1
                    consumption_rate = consumed / duration if duration > 0 else 0
                    
                    self.reaction_selected_store.append([
                        "Input Place",
                        place_id,
                        place_name,
                        f"{initial:.2f}",
                        f"{final:.2f}",
                        f"{min_tokens:.2f}",
                        f"{max_tokens:.2f}",
                        f"{avg_tokens:.2f}",
                        f"Consumed: {consumed:.2f} ({consumption_rate:.2f}/s)"
                    ])
                    total_input_places += 1
            
            # Add OUTPUT PLACE rows
            for place in locality.output_places:
                place_id = place.id
                place_name = getattr(place, 'name', place_id) or place_id
                if place_id in place_data and place_data[place_id]:
                    tokens_series = place_data[place_id]
                    initial = tokens_series[0] if tokens_series else 0
                    final = tokens_series[-1] if tokens_series else 0
                    min_tokens, max_tokens, avg_tokens = calc_stats(tokens_series)
                    produced = final - initial
                    duration = time_points[-1] - time_points[0] if len(time_points) > 1 else 1
                    production_rate = produced / duration if duration > 0 else 0
                    
                    self.reaction_selected_store.append([
                        "Output Place",
                        place_id,
                        place_name,
                        f"{initial:.2f}",
                        f"{final:.2f}",
                        f"{min_tokens:.2f}",
                        f"{max_tokens:.2f}",
                        f"{avg_tokens:.2f}",
                        f"Produced: {produced:.2f} ({production_rate:.2f}/s)"
                    ])
                    total_output_places += 1
        
        # Update status based on number of reactions
        num_selected = len(valid_selections)
        if num_selected == 1:
            # Single reaction: show specific details
            transition, locality = valid_selections[0]
            num_inputs = len(locality.input_places)
            num_outputs = len(locality.output_places)
            status_text = (
                f"<i>Summary for <b>{transition.id}</b>: "
                f"1 transition, {num_inputs} input place(s), {num_outputs} output place(s)</i>"
            )
        else:
            # Multiple reactions: show aggregate summary
            status_text = (
                f"<i>Summary for <b>{num_selected} reactions</b>: "
                f"{total_transitions} transition(s), {total_input_places} input place(s), {total_output_places} output place(s)</i>"
            )
        
        # Add note if some selections were invalid
        if invalid_count > 0:
            status_text = status_text.replace("</i>", f" ({invalid_count} invalid)</i>")
        
        self.reaction_selected_status.set_markup(status_text)
        self.reaction_selected_status.show()
    
    def add_experiment_result(self, name, result):
        """Add an experiment result to the report.
        
        Args:
            name: Experiment name
            result: Result dictionary with trajectories and statistics
        """
        # Update summary to include experiment info
        current_summary = self.summary_label.get_label()
        
        # Extract statistics
        stats = result.get('statistics', {})
        n_reps = stats.get('n_replicates', 0)
        duration = stats.get('duration', 0.0)
        elapsed = stats.get('elapsed_time', 0.0)
        
        # Build experiment summary text
        exp_text = (
            f"\n\n<b>Experiment Added:</b> {name}\n"
            f"  • Replicates: {n_reps}\n"
            f"  • Duration: {duration:.2f}s\n"
            f"  • Execution time: {elapsed:.2f}s\n"
            f"  • Trajectories: {len(result.get('trajectories', []))}"
        )
        
        # Append to existing summary
        if "No simulation or experimental data available" in current_summary:
            # Replace placeholder with experiment data
            self.summary_label.set_markup(
                f"<b>Experiment Results</b>\n{exp_text.strip()}"
            )
        else:
            # Append to existing data
            self.summary_label.set_markup(current_summary + exp_text)
        
        # Update simulation status to show experiment was added
        if hasattr(self, 'simulation_status_label'):
            self.simulation_status_label.set_markup(
                f"<span foreground='green'>✓ Experiment '{name}' added to report</span>\n"
                f"<i>Showing {n_reps} replicates with {duration:.2f}s duration</i>"
            )
    
    def clear_all(self):
        """Clear all tables, textviews, and labels when document is closed."""
        # Clear summary label
        if hasattr(self, 'summary_label'):
            self.summary_label.set_markup("<i>No simulation or experimental data available</i>")
        
        # Clear simulation status
        if hasattr(self, 'simulation_status_label'):
            self.simulation_status_label.set_markup("<i>No simulation data available. Run a simulation to see results.</i>")
        
        # Clear species table
        if hasattr(self, 'species_table') and hasattr(self.species_table, 'clear'):
            self.species_table.clear()
        
        # Clear reaction table
        if hasattr(self, 'reaction_table') and hasattr(self.reaction_table, 'clear'):
            self.reaction_table.clear()
        
        # Clear reaction selected table
        if hasattr(self, 'reaction_selected_store'):
            self.reaction_selected_store.clear()
        
        # Clear reaction selected status
        if hasattr(self, 'reaction_selected_status'):
            self.reaction_selected_status.set_markup("<i>No reactions selected. Select one or more reactions from Analyses panel to see locality simulation data.</i>")
    
    def _auto_save_simulation(self, sim_data: dict):
        """Auto-save simulation results to project folder.
        
        Args:
            sim_data: Simulation data dict from _get_simulation_data()
        """
        try:
            # Get project folder
            project_folder = self._get_project_folder()
            if not project_folder:
                print("Warning: No project folder found, skipping auto-save")
                return
            
            # Create subfolder for simulations
            simulations_folder = os.path.join(project_folder, 'simulations')
            os.makedirs(simulations_folder, exist_ok=True)
            
            # Generate timestamp-based folder name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_name = "simulation"
            if sim_data.get('model'):
                model_name = getattr(sim_data['model'], 'name', 
                                   getattr(sim_data['model'], 'id', 'simulation'))
            
            # Use short folder name: {model_name}_{timestamp}
            folder_name = f"{model_name}_{timestamp}"
            simulation_folder = os.path.join(simulations_folder, folder_name)
            os.makedirs(simulation_folder, exist_ok=True)
            
            # Save simulation configuration
            config = {
                'model_name': model_name,
                'timestamp': timestamp,
                'metadata': sim_data.get('metadata', {}),
                'simulation_type': 'report_panel'
            }
            
            config_path = os.path.join(simulation_folder, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Export time-series data (wide format CSV)
            csv_path = os.path.join(simulation_folder, 'trajectories.csv')
            from shypn.reporting.exporters import CSVSimulationExporter
            accounting_data = sim_data.get('accounting_report')
            exporter = CSVSimulationExporter(sim_data, sim_data.get('metadata', {}), accounting_data)
            exporter.export_timeseries_wide(csv_path)
            
            # Export summary statistics
            stats_path = os.path.join(simulation_folder, 'statistics.csv')
            exporter.export_summary_statistics(stats_path)
            
            # Export full data as JSON
            json_path = os.path.join(simulation_folder, 'simulation_data.json')
            from shypn.reporting.exporters import JSONSimulationExporter
            json_exporter = JSONSimulationExporter(sim_data, sim_data.get('metadata', {}), sim_data.get('model'))
            json_exporter.export(
                json_path,
                include_metadata=True,
                include_timeseries=True,
                include_statistics=True
            )
            
            # Save metadata.txt for human readability
            metadata_path = os.path.join(simulation_folder, 'metadata.txt')
            with open(metadata_path, 'w') as f:
                f.write(f"Simulation Auto-Save\n")
                f.write(f"{'=' * 50}\n\n")
                f.write(f"Model: {model_name}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Simulation Type: Report Panel\n\n")
                
                metadata_dict = sim_data.get('metadata', {})
                if metadata_dict:
                    f.write("Simulation Parameters:\n")
                    for key, value in metadata_dict.items():
                        f.write(f"  {key}: {value}\n")
                
                f.write(f"\nFiles Saved:\n")
                f.write(f"  - trajectories.csv: Time-series data (wide format)\n")
                f.write(f"  - statistics.csv: Summary statistics\n")
                f.write(f"  - simulation_data.json: Full simulation data\n")
                f.write(f"  - config.json: Simulation configuration\n")
            
            print(f"✓ Simulation auto-saved to: {simulation_folder}")
            
        except Exception as e:
            print(f"Error in simulation auto-save: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_project_folder(self):
        """Get the project folder for auto-saving.
        
        Returns:
            str: Absolute path to project folder, or None if not found
        """
        try:
            # Try 1: Get from project manager
            project_manager = get_project_manager()
            if project_manager and hasattr(project_manager, 'project') and project_manager.project:
                project = project_manager.project
                if hasattr(project, 'folder_path') and project.folder_path:
                    return project.folder_path
            
            # Try 2: Get from model filepath
            if self.controller and hasattr(self.controller, 'model'):
                model = self.controller.model
                if model and hasattr(model, 'filepath') and model.filepath:
                    model_path = Path(model.filepath)
                    if model_path.exists():
                        # Go up to project root (assuming model is in project/models/ or similar)
                        parent = model_path.parent
                        while parent != parent.parent:
                            if (parent / 'models').exists() or (parent / 'data').exists():
                                return str(parent)
                            parent = parent.parent
            
            # Try 3: Fallback to workspace folder
            if 'SHYPN_WORKSPACE' in os.environ:
                return os.environ['SHYPN_WORKSPACE']
            
            print("Warning: Could not determine project folder for auto-save")
            return None
            
        except Exception as e:
            print(f"Error getting project folder: {e}")
            return None
