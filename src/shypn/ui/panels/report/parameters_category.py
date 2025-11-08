#!/usr/bin/env python3
"""Dynamic Analyses category for Report Panel.

Displays kinetic parameters, enrichments, and simulation data.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .base_category import BaseReportCategory
from .widgets import SpeciesConcentrationTable, ReactionActivityTable


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
        print(f"[SET_CONTROLLER] Setting controller: {controller}")
        print(f"[SET_CONTROLLER] Controller ID: {id(controller) if controller else 'None'}")
        print(f"[SET_CONTROLLER] Controller has data_collector: {hasattr(controller, 'data_collector') if controller else False}")
        
        if controller and hasattr(controller, 'data_collector'):
            print(f"[SET_CONTROLLER] data_collector: {controller.data_collector}")
            print(f"[SET_CONTROLLER] data_collector ID: {id(controller.data_collector) if controller.data_collector else 'None'}")
        
        # Cancel any pending refresh from previous controller
        if self._pending_refresh_id is not None:
            from gi.repository import GLib
            print(f"[SET_CONTROLLER] Cancelling pending refresh {self._pending_refresh_id}")
            GLib.source_remove(self._pending_refresh_id)
            self._pending_refresh_id = None
        
        # Increment generation to invalidate any in-flight refreshes
        self._refresh_generation += 1
        current_generation = self._refresh_generation
        print(f"[SET_CONTROLLER] New refresh generation: {current_generation}")
        
        # Store the old controller before updating
        old_controller = self.controller
        self.controller = controller
        
        # Immediately refresh to show this document's data
        # This reads from the document's stored data, not from the controller's live data_collector
        print(f"[SET_CONTROLLER] Refreshing to show document data")
        self._refresh_simulation_data(generation=current_generation)
        
        # Register callback for simulation complete
        # IMPORTANT: Only register the callback ONCE per controller to avoid overwriting
        # Check if this controller already has our callback registered
        if controller and id(controller) not in self._registered_controllers:
            print(f"[SET_CONTROLLER] Registering NEW on_simulation_complete callback for controller {id(controller)}")
            # Use GLib.idle_add to ensure UI update happens on main thread
            from gi.repository import GLib
            # CRITICAL: Capture controller by value (not self.controller which changes)
            # At callback time, check if this specific controller is still the active one
            captured_controller = controller
            def on_complete():
                print(f"[CALLBACK] Simulation complete for controller {id(captured_controller)}")
                
                # MULTI-DOCUMENT FIX: Capture data to document's report_data
                # Get the drawing_area for this controller from model_canvas_loader
                if hasattr(self, 'parent_panel') and self.parent_panel:
                    model_canvas_loader = getattr(self.parent_panel, 'model_canvas_loader', None)
                    if model_canvas_loader and hasattr(model_canvas_loader, 'overlay_managers'):
                        # Find which drawing_area has this controller
                        for drawing_area, overlay_manager in model_canvas_loader.overlay_managers.items():
                            if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller is captured_controller:
                                print(f"[CALLBACK] Found drawing_area for controller: {id(drawing_area)}")
                                # Capture simulation data to document's report_data
                                if hasattr(overlay_manager, 'report_data'):
                                    print(f"[CALLBACK] Capturing simulation data to document report_data")
                                    overlay_manager.report_data.capture_simulation_results(captured_controller)
                                break
                
                # Only refresh UI if this captured controller is still the active one
                if self.controller is captured_controller:
                    print(f"[CALLBACK] Controller {id(captured_controller)} matches active controller, refreshing UI")
                    # Capture the current generation when callback fires
                    callback_generation = self._refresh_generation
                    self._pending_refresh_id = GLib.idle_add(lambda: self._refresh_and_clear_pending(callback_generation))
                else:
                    print(f"[CALLBACK] Controller {id(captured_controller)} no longer active (current: {id(self.controller) if self.controller else 'None'}), data captured but not refreshing UI")
            
            # Set the callback on this controller
            controller.on_simulation_complete = on_complete
            self._registered_controllers.add(id(controller))
            print(f"[SET_CONTROLLER] Callback registered successfully")
        elif controller:
            print(f"[SET_CONTROLLER] Controller {id(controller)} already has callback registered, skipping")
    
    def _refresh_and_clear_pending(self, generation):
        """Helper to refresh and clear pending ID. Returns False to remove from idle.
        
        Args:
            generation: The refresh generation this callback belongs to
        """
        self._pending_refresh_id = None
        
        # Check if this refresh is still valid
        if generation == self._refresh_generation:
            print(f"[REFRESH] Generation {generation} matches current, proceeding with refresh")
            self._refresh_simulation_data(generation=generation)
        else:
            print(f"[REFRESH] Generation {generation} is stale (current: {self._refresh_generation}), skipping refresh")
        
        return False  # Remove from idle queue
            
    def _refresh_simulation_data(self, generation=None):
        """Refresh simulation data tables.
        
        Args:
            generation: Optional generation number to validate this refresh is still current
        """
        # Check generation if provided
        if generation is not None and generation != self._refresh_generation:
            print(f"[DEBUG_TABLES] Refresh generation {generation} is stale (current: {self._refresh_generation}), aborting")
            return
        
        print("[DEBUG_TABLES] _refresh_simulation_data called")
        if generation is not None:
            print(f"[DEBUG_TABLES] Refresh generation: {generation}")
        print(f"[DEBUG_TABLES] self.controller: {self.controller}")
        print(f"[DEBUG_TABLES] Controller ID: {id(self.controller) if self.controller else 'None'}")
        
        # Store the controller we're about to use
        refresh_controller = self.controller
        refresh_controller_id = id(refresh_controller) if refresh_controller else None
        
        if not self.controller:
            print("[DEBUG_TABLES] ❌ No controller")
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
                        print(f"[DEBUG_TABLES] Found drawing_area for controller: {id(drawing_area)}")
                        if hasattr(overlay_manager, 'report_data'):
                            report_data = overlay_manager.report_data
                            print(f"[DEBUG_TABLES] Using document's report_data: {id(report_data)}")
                        break
        
        # Check if we have stored simulation data for this document
        if not report_data or not report_data.has_simulation_data():
            print("[DEBUG_TABLES] ❌ No stored simulation data for this document")
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
        
        # Get the stored simulation data (snapshot, not live)
        sim_data = report_data.last_simulation_data
        print(f"[DEBUG_TABLES] Retrieved stored simulation data")
        print(f"[DEBUG_TABLES] time_points length: {len(sim_data['time_points'])}")
        print(f"[DEBUG_TABLES] place_data keys: {list(sim_data['place_data'].keys())}")
        print(f"[DEBUG_TABLES] transition_data keys: {list(sim_data['transition_data'].keys())}")
        
        # Get model name for verification
        model_name = "Unknown"
        if hasattr(self.controller, 'model') and self.controller.model:
            model_name = getattr(self.controller.model, 'name', 
                               getattr(self.controller.model, 'id', 'Untitled'))
        print(f"[DEBUG_TABLES] ⚡ REFRESHING DATA FOR MODEL: {model_name}")
        
        # Check transition firing counts from stored data
        for t_id, firing_series in sim_data['transition_data'].items():
            print(f"[DEBUG_TABLES] Transition {t_id}: firing_series length={len(firing_series)}")
            if firing_series:
                print(f"[DEBUG_TABLES]   First 5 values: {firing_series[:5]}")
                print(f"[DEBUG_TABLES]   Last 5 values: {firing_series[-5:]}")
                print(f"[DEBUG_TABLES]   Final count: {firing_series[-1]}")
        
        # Get duration from stored metadata
        duration = sim_data['metadata'].get('duration', 0)
        print(f"[DEBUG_TABLES] duration (from stored metadata) = {duration}")
        
        # Update Summary section with simulation metadata from stored data
        print("[DEBUG_TABLES] About to call _update_summary...")
        try:
            self._update_summary(duration, sim_data)
            print("[DEBUG_TABLES] _update_summary completed successfully")
        except Exception as e:
            print(f"[DEBUG_TABLES] ⚠️  Error updating summary: {e}")
            import traceback
            traceback.print_exc()
        print("[DEBUG_TABLES] After _update_summary call")
        
        # Show first few data points for debugging
        if len(sim_data['time_points']) > 0:
            print(f"[DEBUG_TABLES] First 5 time points: {sim_data['time_points'][:5]}")
            print(f"[DEBUG_TABLES] Last 5 time points: {sim_data['time_points'][-5:]}")
            print(f"[DEBUG_TABLES] Total time points: {len(sim_data['time_points'])}")
            
            # Show place data sample
            for place_id in list(sim_data['place_data'].keys())[:2]:  # First 2 places
                place_values = sim_data['place_data'][place_id]
                if place_values:
                    print(f"[DEBUG_TABLES] Place {place_id}: first={place_values[0]}, last={place_values[-1]}, len={len(place_values)}")
                else:
                    print(f"[DEBUG_TABLES] Place {place_id}: EMPTY!")
            
            # Show transition data sample
            for trans_id in list(sim_data['transition_data'].keys())[:2]:  # First 2 transitions
                trans_values = sim_data['transition_data'][trans_id]
                if trans_values:
                    print(f"[DEBUG_TABLES] Transition {trans_id}: first={trans_values[0]}, last={trans_values[-1]}, len={len(trans_values)}")
                else:
                    print(f"[DEBUG_TABLES] Transition {trans_id}: EMPTY!")
        else:
            print(f"[DEBUG_TABLES] ⚠️  time_points list is EMPTY!")
        
        # Analyze species
        from shypn.engine.simulation.analysis import SpeciesAnalyzer, ReactionAnalyzer
        
        # CRITICAL: Check if controller changed during analysis
        if self.controller is not refresh_controller:
            print(f"[DEBUG_TABLES] ⚠️  Controller changed during analysis (was {refresh_controller_id}, now {id(self.controller)}), aborting")
            return
        
        print("[DEBUG_TABLES] Analyzing species...")
        try:
            # Create a temporary data collector wrapper that provides stored data
            # but still has access to the model for analyzers
            class DataCollectorSnapshot:
                """Wrapper that provides stored simulation data with model access."""
                def __init__(self, sim_data, controller):
                    self.time_points = sim_data['time_points']
                    self.place_data = sim_data['place_data']
                    self.transition_data = sim_data['transition_data']
                    self.model = controller.model  # Access to model for places/transitions
                
                def get_place_series(self, place_id):
                    """Get time series for a place."""
                    return self.time_points, self.place_data.get(place_id, [])
                
                def get_transition_series(self, transition_id):
                    """Get time series for a transition."""
                    return self.time_points, self.transition_data.get(transition_id, [])
            
            data_snapshot = DataCollectorSnapshot(sim_data, self.controller)
            
            species_analyzer = SpeciesAnalyzer(data_snapshot)
            species_metrics = species_analyzer.analyze_all_species(duration)
            print(f"[DEBUG_TABLES] Got {len(species_metrics)} species metrics")
            
            # Show first metric sample
            if species_metrics:
                sample = species_metrics[0]
                print(f"[DEBUG_TABLES] Sample species metric: {sample.place_name}, init={sample.initial_tokens}, final={sample.final_tokens}, min={sample.min_tokens}, max={sample.max_tokens}")
            
            self.species_table.populate(species_metrics)
            print("[DEBUG_TABLES] Species table populated")
            
            # Check again before continuing
            if self.controller is not refresh_controller:
                print(f"[DEBUG_TABLES] ⚠️  Controller changed after species analysis, aborting")
                return
        except Exception as e:
            print(f"[DEBUG_TABLES] ❌ Error analyzing species: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Analyze reactions
        print("[DEBUG_TABLES] Analyzing reactions...")
        try:
            reaction_analyzer = ReactionAnalyzer(data_snapshot)
            reaction_metrics = reaction_analyzer.analyze_all_reactions(duration)
            print(f"[DEBUG_TABLES] Got {len(reaction_metrics)} reaction metrics")
            
            # Show first metric sample
            if reaction_metrics:
                sample = reaction_metrics[0]
                print(f"[DEBUG_TABLES] Sample reaction metric: {sample.transition_name}, firings={sample.firing_count}, rate={sample.average_rate}, status={sample.status}")
            
            self.reaction_table.populate(reaction_metrics)
            print("[DEBUG_TABLES] Reaction table populated")
        except Exception as e:
            print(f"[DEBUG_TABLES] ❌ Error analyzing reactions: {e}")
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
            print("[DEBUG_TABLES] Auto-expanding simulation data section")
            self.simulation_expander.set_expanded(True)
        
        # Auto-expand the category itself when data arrives
        if hasattr(self, 'category_frame') and self.category_frame:
            if not self.category_frame.expanded:
                print("[DEBUG_TABLES] Auto-expanding Dynamic Analyses category")
                self.category_frame.set_expanded(True)
        
        # Ensure all widgets are visible and properly rendered
        self.summary_label.show()
        self.simulation_status_label.show()
        self.species_table.show_all()
        self.reaction_table.show_all()
        self.simulation_expander.show_all()
        
        # Force a redraw of the parent widget to ensure visibility
        if hasattr(self, 'category_frame') and self.category_frame:
            self.category_frame.queue_draw()
        
        print("[DEBUG_TABLES] All widgets shown and expanders expanded")
    
    def _update_summary(self, duration: float, sim_data: dict):
        """Update Summary section with simulation metadata.
        
        Args:
            duration: Actual simulation duration in seconds
            sim_data: Dictionary with stored simulation data
        """
        try:
            from datetime import datetime
            
            print("[SUMMARY] Starting summary update...")
            
            # Get simulation timestamp from stored metadata
            timestamp_str = sim_data['metadata'].get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"[SUMMARY] Timestamp: {timestamp_str}")
            
            # Get model info
            model = self.controller.model if self.controller else None
            print(f"[SUMMARY] Model: {model}")
            
            model_name = "Unknown"
            num_places = 0
            num_transitions = 0
            
            if model:
                model_name = getattr(model, 'name', getattr(model, 'id', 'Untitled Model'))
                print(f"[SUMMARY] Model name: {model_name}")
                
                num_places = len(getattr(model, 'places', []))
                num_transitions = len(getattr(model, 'transitions', []))
                print(f"[SUMMARY] Network size: {num_places} places, {num_transitions} transitions")
            
            # Get simulation settings from stored metadata
            metadata = sim_data['metadata']
            time_step = metadata.get('time_step', 0.0)
            target_duration = metadata.get('target_duration')
            time_scale = metadata.get('time_scale', 1.0)
            
            # Format target duration string (handle None case)
            if target_duration is None:
                target_duration_str = "Not set"
            else:
                target_duration_str = f"{target_duration:.2f} s"
            
            print(f"[SUMMARY] Parameters: dt={time_step}, target={target_duration}, scale={time_scale}")
            
            # Get data statistics from stored data
            num_time_points = len(sim_data['time_points'])
            total_steps = num_time_points - 1 if num_time_points > 0 else 0
            print(f"[SUMMARY] Data points: {num_time_points}, steps: {total_steps}")
            
            # Calculate total firings from stored data
            total_firings = 0
            for firing_series in sim_data['transition_data'].values():
                if firing_series:
                    total_firings += firing_series[-1]
            print(f"[SUMMARY] Total firings: {total_firings}")
            
            # Format time_step (handle None case)
            if time_step is None:
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
            
            print("[SUMMARY] Setting markup...")
            self.summary_label.set_markup(summary_text)
            self.summary_label.show()  # Ensure label is visible
            print("[SUMMARY] Summary updated successfully")
            
        except Exception as e:
            # If summary update fails, don't block table population
            print(f"[SUMMARY] Error updating summary: {e}")
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
        """Set model canvas reference.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
