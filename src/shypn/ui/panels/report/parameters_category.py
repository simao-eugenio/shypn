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
        super().__init__(name, parent_panel)
        self.controller = None
        # Track which controllers have callbacks registered to avoid re-registration
        self._registered_controllers = set()
        self._build_content()
    
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
        
        self.controller = controller
        
        # Register callback for simulation complete (only once per controller)
        if controller and id(controller) not in self._registered_controllers:
            print(f"[SET_CONTROLLER] Registering on_simulation_complete callback (FIRST TIME)")
            # Use GLib.idle_add to ensure UI update happens on main thread
            from gi.repository import GLib
            # CRITICAL: We need to refresh ONLY if this specific controller is still active
            # when the callback fires. Don't capture self.controller (which changes on tab switch).
            # Instead, check at callback time if this controller is still the active one.
            def on_complete():
                # Only refresh if this controller is still the active one
                if self.controller is controller:
                    print(f"[CALLBACK] Controller {id(controller)} matches active controller, refreshing")
                    GLib.idle_add(self._refresh_simulation_data)
                else:
                    print(f"[CALLBACK] Controller {id(controller)} no longer active (current: {id(self.controller) if self.controller else 'None'}), skipping refresh")
            
            controller.on_simulation_complete = on_complete
            self._registered_controllers.add(id(controller))
            print(f"[SET_CONTROLLER] Callback registered successfully (controller added to registry)")
        elif controller:
            print(f"[SET_CONTROLLER] Callback already registered for this controller (skipping re-registration)")
            
    def _refresh_simulation_data(self):
        """Refresh simulation data tables."""
        print("[DEBUG_TABLES] _refresh_simulation_data called")
        print(f"[DEBUG_TABLES] Controller ID: {id(self.controller) if self.controller else 'None'}")
        
        if not self.controller:
            print("[DEBUG_TABLES] ❌ No controller")
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
            
        if not self.controller.data_collector:
            print("[DEBUG_TABLES] ❌ No data_collector")
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
            
        data_collector = self.controller.data_collector
        print(f"[DEBUG_TABLES] data_collector = {data_collector}")
        print(f"[DEBUG_TABLES] data_collector ID: {id(data_collector)}")
        print(f"[DEBUG_TABLES] is_collecting: {data_collector.is_collecting}")
        
        # Check if we have collected data
        has_data = data_collector.has_data()
        print(f"[DEBUG_TABLES] has_data() = {has_data}")
        print(f"[DEBUG_TABLES] time_points length: {len(data_collector.time_points)}")
        print(f"[DEBUG_TABLES] place_data keys: {list(data_collector.place_data.keys())}")
        print(f"[DEBUG_TABLES] transition_data keys: {list(data_collector.transition_data.keys())}")
        
        # Check transition firing counts
        for t_id, firing_series in data_collector.transition_data.items():
            print(f"[DEBUG_TABLES] Transition {t_id}: firing_series length={len(firing_series)}")
            if firing_series:
                print(f"[DEBUG_TABLES]   First 5 values: {firing_series[:5]}")
                print(f"[DEBUG_TABLES]   Last 5 values: {firing_series[-5:]}")
                print(f"[DEBUG_TABLES]   Final count: {firing_series[-1]}")
        
        if not has_data:
            print("[DEBUG_TABLES] ❌ No data collected")
            self.simulation_status_label.set_markup(
                "<i>No simulation data available. Run a simulation to see results.</i>"
            )
            self.species_table.clear()
            self.reaction_table.clear()
            return
        
        # Get duration (use actual simulation time, not target duration)
        # controller.time = actual elapsed simulation time
        # settings.duration = user's target duration (might not be reached yet if stopped early)
        duration = self.controller.time
        print(f"[DEBUG_TABLES] duration (actual simulation time) = {duration}")
        print(f"[DEBUG_TABLES] settings.duration (target) = {self.controller.settings.duration}")
        
        # Update Summary section with simulation metadata
        print("[DEBUG_TABLES] About to call _update_summary...")
        try:
            self._update_summary(duration, data_collector)
            print("[DEBUG_TABLES] _update_summary completed successfully")
        except Exception as e:
            print(f"[DEBUG_TABLES] ⚠️  Error updating summary: {e}")
            import traceback
            traceback.print_exc()
        print("[DEBUG_TABLES] After _update_summary call")
        
        # Show first few data points for debugging
        if len(data_collector.time_points) > 0:
            print(f"[DEBUG_TABLES] First 5 time points: {data_collector.time_points[:5]}")
            print(f"[DEBUG_TABLES] Last 5 time points: {data_collector.time_points[-5:]}")
            print(f"[DEBUG_TABLES] Total time points: {len(data_collector.time_points)}")
            
            # Show place data sample
            for place_id in list(data_collector.place_data.keys())[:2]:  # First 2 places
                place_values = data_collector.place_data[place_id]
                if place_values:
                    print(f"[DEBUG_TABLES] Place {place_id}: first={place_values[0]}, last={place_values[-1]}, len={len(place_values)}")
                else:
                    print(f"[DEBUG_TABLES] Place {place_id}: EMPTY!")
            
            # Show transition data sample
            for trans_id in list(data_collector.transition_data.keys())[:2]:  # First 2 transitions
                trans_values = data_collector.transition_data[trans_id]
                if trans_values:
                    print(f"[DEBUG_TABLES] Transition {trans_id}: first={trans_values[0]}, last={trans_values[-1]}, len={len(trans_values)}")
                else:
                    print(f"[DEBUG_TABLES] Transition {trans_id}: EMPTY!")
        else:
            print(f"[DEBUG_TABLES] ⚠️  time_points list is EMPTY!")
        
        # Analyze species
        from shypn.engine.simulation.analysis import SpeciesAnalyzer, ReactionAnalyzer
        
        print("[DEBUG_TABLES] Analyzing species...")
        try:
            species_analyzer = SpeciesAnalyzer(data_collector)
            species_metrics = species_analyzer.analyze_all_species(duration)
            print(f"[DEBUG_TABLES] Got {len(species_metrics)} species metrics")
            
            # Show first metric sample
            if species_metrics:
                sample = species_metrics[0]
                print(f"[DEBUG_TABLES] Sample species metric: {sample.place_name}, init={sample.initial_tokens}, final={sample.final_tokens}, min={sample.min_tokens}, max={sample.max_tokens}")
            
            self.species_table.populate(species_metrics)
            print("[DEBUG_TABLES] Species table populated")
        except Exception as e:
            print(f"[DEBUG_TABLES] ❌ Error analyzing species: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Analyze reactions
        print("[DEBUG_TABLES] Analyzing reactions...")
        try:
            reaction_analyzer = ReactionAnalyzer(data_collector)
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
        num_time_points = len(data_collector.time_points)
        
        self.simulation_status_label.set_markup(
            f"<i>Analyzed {num_species} species and {num_reactions} reactions "
            f"over {num_time_points} time points (duration: {duration:.2f}s)</i>"
        )
    
    def _update_summary(self, duration: float, data_collector):
        """Update Summary section with simulation metadata.
        
        Args:
            duration: Actual simulation duration in seconds
            data_collector: DataCollector instance with simulation data
        """
        try:
            from datetime import datetime
            
            print("[SUMMARY] Starting summary update...")
            
            # Get simulation timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[SUMMARY] Timestamp: {timestamp}")
            
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
            
            # Get simulation settings
            settings = self.controller.settings if self.controller else None
            print(f"[SUMMARY] Settings: {settings}")
            
            time_step = getattr(settings, 'time_step', 0.0) if settings else 0.0
            target_duration = getattr(settings, 'duration', None) if settings else None
            time_scale = getattr(settings, 'time_scale', 1.0) if settings else 1.0
            
            # Format target duration string (handle None case)
            if target_duration is None:
                target_duration_str = "Not set"
            else:
                target_duration_str = f"{target_duration:.2f} s"
            
            print(f"[SUMMARY] Parameters: dt={time_step}, target={target_duration}, scale={time_scale}")
            
            # Get data statistics
            num_time_points = len(data_collector.time_points)
            total_steps = num_time_points - 1 if num_time_points > 0 else 0
            print(f"[SUMMARY] Data points: {num_time_points}, steps: {total_steps}")
            
            # Calculate total firings
            total_firings = 0
            for firing_series in data_collector.transition_data.values():
                if firing_series:
                    total_firings += firing_series[-1]
            print(f"[SUMMARY] Total firings: {total_firings}")
            
            # Build summary text
            if duration > 0:
                avg_rate = total_firings / duration
                summary_text = f"""<b>Simulation Summary</b>

<b>Date/Time:</b> {timestamp}
<b>Model:</b> {model_name}
<b>Network Size:</b> {num_places} places, {num_transitions} transitions

<b>Simulation Parameters:</b>
  • Time Step (dt): {time_step:.4f} s
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

<b>Date/Time:</b> {timestamp}
<b>Model:</b> {model_name}
<b>Network Size:</b> {num_places} places, {num_transitions} transitions

<b>Simulation Parameters:</b>
  • Time Step (dt): {time_step:.4f} s
  • Target Duration: {target_duration_str}
  • Total Steps: {total_steps}
  
<b>Activity Summary:</b>
  • Time Points Recorded: {num_time_points}
  • Total Transition Firings: {total_firings}"""
            
            print("[SUMMARY] Setting markup...")
            self.summary_label.set_markup(summary_text)
            print("[SUMMARY] Summary updated successfully")
            
        except Exception as e:
            # If summary update fails, don't block table population
            print(f"[SUMMARY] Error updating summary: {e}")
            import traceback
            traceback.print_exc()
            self.summary_label.set_markup("<i>Error generating summary</i>")
