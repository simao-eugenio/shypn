"""Transition Behavior Analysis Panel.

This module provides the TransitionRatePanel class for plotting transition-specific
behavior characteristics in real-time during simulation.

This is a SEPARATE MODULE - not implemented in loaders!
Loaders only instantiate this panel and attach it to the UI.
"""
from typing import List, Tuple, Any

from shypn.analyses.plot_panel import AnalysisPlotPanel


class TransitionRatePanel(AnalysisPlotPanel):
    """Panel for plotting transition behavior characteristics over time.
    
    This panel adapts its visualization based on transition type:
    
        pass
    **Continuous Transitions (SHPN)**:
        pass
    - Plots the **rate function value** over time
    - Shows actual behavior curves (sigmoid, exponential, linear, etc.)
    - Y-axis: Rate (tokens/s) - the instantaneous flow rate
    - Visualizes: r(t) = f(M(t), t) where M(t) is marking, t is time
    
    **Discrete Transitions (Immediate/Timed/Stochastic)**:
        pass
    - Plots the **cumulative firing count** over time
    - Shows total activity accumulation
    - Y-axis: Cumulative Firings - total number of firings
    - Visualizes: Step functions showing firing events
    
    Plot interpretation by transition type:
    
        pass
    **Continuous** (rate function):
        pass
    - Sigmoid curve: Logistic growth/saturation behavior
    - Exponential: Unlimited growth or decay
    - Linear: Constant rate flow
    - Flat line: Rate = 0 (no flow, transition disabled)
    
    **Immediate** (cumulative):
        pass
    - Vertical steps: Instant firings when enabled
    - Steep slope: High firing frequency
    
    **Timed** (cumulative):
        pass
    - Regular staircase: Fixed interval firings
    - Constant slope: Deterministic periodic behavior
    
    **Stochastic** (cumulative):
        pass
    - Irregular staircase: Random interval firings
    - Variable slope: Exponentially distributed delays
    
    Attributes:
        (inherited from AnalysisPlotPanel)
    
    Example:
        # Create panel (in right_panel_loader or similar)
        transition_panel = TransitionRatePanel(data_collector)
        
        # Add transitions for analysis
        transition_panel.add_object(continuous_transition)  # Shows rate curve
        transition_panel.add_object(stochastic_transition)  # Shows cumulative count
        
        # Panel automatically adapts visualization per transition type
    """
    
    def __init__(self, data_collector):
        """Initialize the transition behavior analysis panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        super().__init__('transition', data_collector)
        
        # Locality plotting support
        self._locality_places = {}  # Maps transition_id -> {input_places, output_places}
        
    
    def _get_rate_data(self, transition_id: Any) -> List[Tuple[float, float]]:
        """Get behavior-specific data for a transition.
        
        The data plotted depends on transition type:
            pass
        - Continuous: Rate function value over time (shows sigmoid, exponential curves, etc.)
        - Discrete (immediate/timed/stochastic): Cumulative firing count
        
        Args:
            transition_id: ID of the transition
            
        Returns:
            List of (time, value) tuples where value depends on transition type
        """
        DEBUG_PLOT_DATA = False  # Disable verbose logging
        
        # Get raw firing event data from collector
        raw_events = self.data_collector.get_transition_data(transition_id)
        
        if not raw_events:
            if DEBUG_PLOT_DATA:
                pass
            return []
        
        # Determine transition type by checking if details contain 'rate' field
        # Continuous transitions store their rate in details
        has_rate_data = False
        if len(raw_events) > 0 and raw_events[0][2] is not None:
            details = raw_events[0][2]
            if isinstance(details, dict) and 'rate' in details:
                has_rate_data = True
        
        if has_rate_data:
            # CONTINUOUS TRANSITION: Plot rate function value over time
            if DEBUG_PLOT_DATA:
            
                pass
            rate_series = []
            for time, event_type, details in raw_events:
                if event_type == 'fired' and details and isinstance(details, dict):
                    rate = details.get('rate', 0.0)
                    rate_series.append((time, rate))
            
            if DEBUG_PLOT_DATA and rate_series:
            
                pass
            return rate_series
        else:
            # DISCRETE TRANSITION: Plot cumulative firing count
            if DEBUG_PLOT_DATA:
            
                pass
            firing_times = [t for t, event_type, _ in raw_events 
                           if event_type == 'fired']
            
            if len(firing_times) < 1:
                if DEBUG_PLOT_DATA:
                    pass
                return []
            
            # Convert to cumulative count series
            cumulative_series = []
            
            # Start at time 0 with count 0
            if firing_times[0] > 0:
                cumulative_series.append((0.0, 0))
            
            # Add each firing event with its cumulative count
            for i, time in enumerate(firing_times):
                count = i + 1  # Cumulative count (1-indexed)
                cumulative_series.append((time, count))
            
            if DEBUG_PLOT_DATA:
            
                pass
            return cumulative_series
    
    def _get_ylabel(self) -> str:
        """Get Y-axis label for transition plot.
        
        The label depends on transition types being plotted:
            pass
        - If only continuous: "Rate (flow/s)"
        - If only discrete: "Cumulative Firings"
        - If mixed: "Value" (generic)
        
        Returns:
            str: Y-axis label
        """
        if not self.selected_objects:
            return 'Value'
        
        # Check if we have any continuous transitions
        has_continuous = False
        has_discrete = False
        
        for obj in self.selected_objects:
            raw_events = self.data_collector.get_transition_data(obj.id)
            if raw_events and len(raw_events) > 0:
                details = raw_events[0][2]
                if isinstance(details, dict) and 'rate' in details:
                    has_continuous = True
                else:
                    has_discrete = True
        
        if has_continuous and not has_discrete:
            return 'Rate (tokens/s)'
        elif has_discrete and not has_continuous:
            return 'Cumulative Firings'
        else:
            return 'Value'  # Mixed types
    
    def _get_title(self) -> str:
        """Get plot title for transition plot.
        
        Returns:
            str: Plot title
        """
        return 'Transition Behavior Evolution'
    
    def _format_plot(self):
        """Format the plot with labels, grid, legend, and smart Y-axis scaling.
        
        Overrides parent to add source/sink-aware Y-axis scaling:
        - Source transitions: Generous upper margin for unbounded growth
        - Sink transitions: Lower bound at 0 for bounded decrease
        - Mixed/normal: Balanced margins
        """
        # Call parent formatting first
        super()._format_plot()
        
        # Apply smart Y-axis scaling if not auto-scale
        if not self.auto_scale and self.selected_objects:
            self._apply_smart_ylim_scaling()
    
    def _apply_smart_ylim_scaling(self):
        """Apply smart Y-axis limits based on transition types.
        
        Different transitions need different scaling:
        - Source: Unbounded growth (generous upper margin +50%)
        - Sink: Bounded to zero (lower limit at 0)
        - Normal: Balanced margins (±10%)
        """
        ylim = self.axes.get_ylim()
        y_range = ylim[1] - ylim[0]
        
        if y_range <= 0:
            return
        
        # Detect if we have source or sink transitions
        has_source = False
        has_sink = False
        
        for obj in self.selected_objects:
            is_source = getattr(obj, 'is_source', False)
            is_sink = getattr(obj, 'is_sink', False)
            
            if is_source:
                has_source = True
            if is_sink:
                has_sink = True
        
        # Apply appropriate margins based on transition types
        if has_source and not has_sink:
            # SOURCE: Generous upper margin for token generation
            new_lower = max(0, ylim[0] - y_range * 0.1)  # Small lower margin
            new_upper = ylim[1] + y_range * 0.5  # 50% upper margin
            self.axes.set_ylim(new_lower, new_upper)
            
        elif has_sink and not has_source:
            # SINK: Bottom at zero, modest upper margin
            new_lower = 0  # Sinks converge to zero
            new_upper = ylim[1] + y_range * 0.2  # 20% upper margin
            self.axes.set_ylim(new_lower, new_upper)
            
        elif has_source and has_sink:
            # MIXED: Balanced margins
            new_lower = max(0, ylim[0] - y_range * 0.2)
            new_upper = ylim[1] + y_range * 0.3
            self.axes.set_ylim(new_lower, new_upper)
            
        else:
            # NORMAL: Standard margins
            new_lower = ylim[0] - y_range * 0.1
            new_upper = ylim[1] + y_range * 0.1
            self.axes.set_ylim(new_lower, new_upper)
    
    def wire_search_ui(self, entry, search_btn, result_label, model):
        """Wire search UI controls to transition search functionality.
        
        This method connects the search entry, buttons, and result label from
        the right panel UI to the SearchHandler for finding transitions to add to analysis.
        
        When a transition is found, it automatically detects and adds its entire locality
        (transition + all connected input/output places) to the plot.
        
        Args:
            entry: GtkEntry for search input
            search_btn: GtkButton for triggering search
            result_label: GtkLabel for displaying search results
            model: ModelCanvasManager instance to search
        """
        self.search_entry = entry
        self.search_result_label = result_label
        self.search_model = model
        self.search_results = []  # Store current search results
        
        # Connect search button
        def on_search_clicked(button):
            query = self.search_entry.get_text().strip()
            if not query:
                self.search_result_label.set_text("⚠ Enter search text")
                return
            
            # Check if model is available
            if not self.search_model:
                self.search_result_label.set_text("⚠ No model loaded. Open or create a Petri net first.")
                return
            
            # Import SearchHandler and LocalityDetector
            from shypn.analyses import SearchHandler
            from shypn.diagnostic import LocalityDetector
            
            # Perform transition search
            results = SearchHandler.search_transitions(self.search_model, query)
            self.search_results = results
            
            # Display results
            if results:
                summary = SearchHandler.format_result_summary(results, 'transition')
                self.search_result_label.set_text(summary)
                
                # If exactly one result, add it with its locality automatically
                if len(results) == 1:
                    transition = results[0]
                    
                    # Detect locality for this transition
                    detector = LocalityDetector(self.search_model)
                    locality = detector.get_locality_for_transition(transition)
                    
                    # Add transition to plot
                    self.add_object(transition)
                    
                    # Add locality places if valid
                    if locality.is_valid:
                        self.add_locality_places(transition, locality)
                        place_count = locality.place_count
                        self.search_result_label.set_text(
                            f"✓ Added {transition.name} with locality ({place_count} places)"
                        )
                    else:
                        self.search_result_label.set_text(f"✓ Added {transition.name} to analysis")
            else:
                self.search_result_label.set_text(f"✗ No transitions found for '{query}'")

        
        search_btn.connect('clicked', on_search_clicked)
        
        # Allow Enter key in search entry
        def on_entry_activate(entry):
            on_search_clicked(search_btn)
        
        entry.connect('activate', on_entry_activate)
        
    
    def add_locality_places(self, transition, locality):
        """Add locality places for a transition to plot with it.
        
        This stores the locality places so they can be plotted
        together with the transition, showing the complete P-T-P pattern.
        
        Args:
            transition: Transition object
            locality: Locality object with input/output places
        """
        self._locality_places[transition.id] = {
            'input_places': list(locality.input_places),
            'output_places': list(locality.output_places),
            'transition': transition
        }
        
        
        # Trigger plot update
        self.needs_update = True
    
    def _update_objects_list(self):
        """Update the UI list of selected objects with locality information.
        
        Overrides parent method to show transition and all its locality places.
        """
        
        # Import GTK here to avoid issues
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        import matplotlib.colors as mcolors
        
        # Clear existing list
        for child in self.objects_listbox.get_children():
            self.objects_listbox.remove(child)
        
        # Add rows for each selected object
        if not self.selected_objects:
            # Show empty message
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="No objects selected")
            label.get_style_context().add_class('dim-label')
            row.add(label)
            self.objects_listbox.add(row)
        else:
            for i, obj in enumerate(self.selected_objects):
                color = self._get_color(i)
                obj_name = getattr(obj, 'name', f'Transition{obj.id}')
                transition_type = getattr(obj, 'transition_type', 'continuous')
                
                # Check source/sink status
                is_source = getattr(obj, 'is_source', False)
                is_sink = getattr(obj, 'is_sink', False)
                
                # Short type names for compact display
                type_abbrev = {
                    'immediate': 'IMM',
                    'timed': 'TIM',
                    'stochastic': 'STO',
                    'continuous': 'CON'
                }.get(transition_type, transition_type[:3].upper())
                
                # Add source/sink indicator
                if is_source:
                    type_abbrev += '+SRC'
                elif is_sink:
                    type_abbrev += '+SNK'
                
                # Add transition row
                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                hbox.set_margin_start(6)
                hbox.set_margin_end(6)
                hbox.set_margin_top(3)
                hbox.set_margin_bottom(3)
                
                # Color indicator
                color_box = Gtk.DrawingArea()
                color_box.set_size_request(20, 20)
                color_box.connect('draw', self._draw_color_box, color)
                hbox.pack_start(color_box, False, False, 0)
                
                # Transition label
                label_text = f"{obj_name} [{type_abbrev}] (T{obj.id})"
                label = Gtk.Label(label=label_text)
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                
                # Remove button
                remove_btn = Gtk.Button(label="✕")
                remove_btn.set_relief(Gtk.ReliefStyle.NONE)
                remove_btn.connect('clicked', self._on_remove_clicked, obj)
                hbox.pack_start(remove_btn, False, False, 0)
                
                row.add(hbox)
                self.objects_listbox.add(row)
                
                # Add locality places if available
                if obj.id in self._locality_places:
                    locality_data = self._locality_places[obj.id]
                    
                    # For source: Only show output places
                    if is_source:
                        for place in locality_data['output_places']:
                            self._add_locality_place_row_to_list(
                                place, color, "→ Output:", is_output=True
                            )
                    # For sink: Only show input places
                    elif is_sink:
                        for place in locality_data['input_places']:
                            self._add_locality_place_row_to_list(
                                place, color, "← Input:", is_output=False
                            )
                    # For normal: Show both input and output places
                    else:
                        # Add input places
                        for place in locality_data['input_places']:
                            self._add_locality_place_row_to_list(
                                place, color, "← Input:", is_output=False
                            )
                        # Add output places
                        for place in locality_data['output_places']:
                            self._add_locality_place_row_to_list(
                                place, color, "→ Output:", is_output=True
                            )
        
        self.objects_listbox.show_all()
    
    def _add_locality_place_row_to_list(self, place, color, label_prefix, is_output):
        """Add a locality place row to the objects list.
        
        Args:
            place: Place object to add
            color: Color hex string for the parent transition
            label_prefix: Prefix string like "← Input:" or "→ Output:"
            is_output: True if this is an output place, False if input
        """
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        import matplotlib.colors as mcolors
        
        place_row = Gtk.ListBoxRow()
        place_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        place_hbox.set_margin_start(40)  # Indent to show hierarchy
        place_hbox.set_margin_end(6)
        place_hbox.set_margin_top(1)
        place_hbox.set_margin_bottom(1)
        
        # Color box for place (lighter for input, darker for output)
        place_color_box = Gtk.DrawingArea()
        place_color_box.set_size_request(16, 16)
        rgb = mcolors.hex2color(color)
        
        if is_output:
            # Darker color for output places
            modified_rgb = tuple(max(0.0, c - 0.2) for c in rgb)
        else:
            # Lighter color for input places
            modified_rgb = tuple(min(1.0, c + 0.2) for c in rgb)
        
        modified_color = mcolors.rgb2hex(modified_rgb)
        place_color_box.connect('draw', self._draw_color_box, modified_color)
        place_hbox.pack_start(place_color_box, False, False, 0)
        
        # Place label
        place_name = getattr(place, 'name', f'Place{place.id}')
        tokens = getattr(place, 'tokens', 0)
        place_label = Gtk.Label(label=f"{label_prefix} {place_name} ({tokens} tokens)")
        place_label.set_xalign(0)
        place_label.get_style_context().add_class('dim-label')
        place_hbox.pack_start(place_label, True, True, 0)
        
        place_row.add(place_hbox)
        self.objects_listbox.add(place_row)
    
    def _show_waiting_state(self):
        """Show message when objects are selected but simulation hasn't started."""
        # Build message with locality information
        message_lines = ['Objects ready for analysis:', '']
        
        for i, obj in enumerate(self.selected_objects):
            obj_name = getattr(obj, 'name', f'Transition{obj.id}')
            transition_type = getattr(obj, 'transition_type', 'continuous')
            type_abbrev = {
                'immediate': 'IMM',
                'timed': 'TIM',
                'stochastic': 'STO',
                'continuous': 'CON'
            }.get(transition_type, transition_type[:3].upper())
            
            # Check locality
            if obj.id in self._locality_places:
                locality_data = self._locality_places[obj.id]
                n_inputs = len(locality_data['input_places'])
                n_outputs = len(locality_data['output_places'])
                message_lines.append(f"• {obj_name} [{type_abbrev}]")
                message_lines.append(f"  with locality: {n_inputs} inputs → {n_outputs} outputs")
            else:
                message_lines.append(f"• {obj_name} [{type_abbrev}]")
        
        message_lines.append('')
        message_lines.append('▶ Start simulation to see plots')
        
        message = '\n'.join(message_lines)
        
        self.axes.text(0.5, 0.5, message,
                      ha='center', va='center',
                      transform=self.axes.transAxes,
                      fontsize=11, color='#555',
                      family='monospace')
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.canvas.draw()
    
    def update_plot(self):
        """Update the plot with current data including locality places.
        
        Overrides parent method to add locality place plotting.
        """
        DEBUG_UPDATE_PLOT = False  # Disable verbose logging
        
        if DEBUG_UPDATE_PLOT:
        
            pass
        self.axes.clear()
        
        # Clear secondary Y-axis for places if it exists
        if hasattr(self, '_places_axes'):
            self._places_axes.clear()
            self._places_axes.set_ylabel('Place Tokens', color='gray', fontsize=10)
            self._places_axes.tick_params(axis='y', labelcolor='gray')
        
        if not self.selected_objects:
            if DEBUG_UPDATE_PLOT:
                pass
            self._show_empty_state()
            return
        
        # Check if we have any data at all
        has_any_data = False
        for obj in self.selected_objects:
            if self._get_rate_data(obj.id):
                has_any_data = True
                break
        
        # If no data yet, show waiting message with locality info
        if not has_any_data:
            self._show_waiting_state()
            return
        
        # Plot rate for each selected transition
        for i, obj in enumerate(self.selected_objects):
            if DEBUG_UPDATE_PLOT:
                obj_name = getattr(obj, 'name', f'transition{obj.id}')
            
            rate_data = self._get_rate_data(obj.id)
            
            if rate_data:
                times = [t for t, r in rate_data]
                rates = [r for t, r in rate_data]
                
                color = self._get_color(i)
                obj_name = getattr(obj, 'name', f'Transition{obj.id}')
                
                # Include type in legend
                transition_type = getattr(obj, 'transition_type', 'continuous')
                type_abbrev = {
                    'immediate': 'IMM',
                    'timed': 'TIM',
                    'stochastic': 'STO',
                    'continuous': 'CON'
                }.get(transition_type, transition_type[:3].upper())
                legend_label = f'{obj_name} [{type_abbrev}]'
                
                self.axes.plot(times, rates,
                              label=legend_label,
                              color=color,
                              linewidth=2.5,
                              zorder=10)  # Transitions on top
                
                # Plot locality places if available
                if obj.id in self._locality_places:
                    self._plot_locality_places(obj.id, color, DEBUG_UPDATE_PLOT)
        
        self._format_plot()
        self.canvas.draw()
    
    def _plot_locality_places(self, transition_id, base_color, debug=False):
        """Plot input and output places for a transition's locality.
        
        Uses a secondary Y-axis (right side) for place token counts to avoid
        scale domination issues when token counts are much larger than rates.
        
        Args:
            transition_id: ID of the transition
            base_color: Base color for the transition (used to derive place colors)
            debug: Enable debug logging
        """
        locality_data = self._locality_places[transition_id]
        transition = locality_data['transition']
        
        # Import here to avoid circular dependency
        import matplotlib.colors as mcolors
        
        # Create secondary Y-axis for places if it doesn't exist yet
        if not hasattr(self, '_places_axes'):
            self._places_axes = self.axes.twinx()
            self._places_axes.set_ylabel('Place Tokens', color='gray', fontsize=10)
            self._places_axes.tick_params(axis='y', labelcolor='gray')
            if debug:
        
                pass
        # Convert hex color to RGB for manipulation
        rgb = mcolors.hex2color(base_color)
        
        # Plot input places (dashed lines, slightly lighter) on secondary axis
        for i, place in enumerate(locality_data['input_places']):
            # Get place token data from data collector
            place_data = self.data_collector.get_place_data(place.id)
            
            if place_data:
                # Place data format: (time, tokens) - only 2 values
                times = [t for t, tokens in place_data]
                tokens = [tok for t, tok in place_data]
                
                # Lighten the color for input places
                lighter_rgb = tuple(min(1.0, c + 0.2) for c in rgb)
                lighter_hex = mcolors.rgb2hex(lighter_rgb)
                
                place_name = getattr(place, 'name', f'P{place.id}')
                self._places_axes.plot(times, tokens,
                             linestyle='--',
                             linewidth=1.5,
                             alpha=0.7,
                             color=lighter_hex,
                             label=f'  ↓ {place_name} (input)',
                             zorder=5)  # Behind transitions
                
                if debug:
        
                    pass
        # Plot output places (dotted lines, slightly darker) on secondary axis
        for i, place in enumerate(locality_data['output_places']):
            # Get place token data from data collector
            place_data = self.data_collector.get_place_data(place.id)
            
            if place_data:
                # Place data format: (time, tokens) - only 2 values
                times = [t for t, tokens in place_data]
                tokens = [tok for t, tok in place_data]
                
                # Darken the color for output places
                darker_rgb = tuple(max(0.0, c - 0.2) for c in rgb)
                darker_hex = mcolors.rgb2hex(darker_rgb)
                
                place_name = getattr(place, 'name', f'P{place.id}')
                self._places_axes.plot(times, tokens,
                             linestyle=':',
                             linewidth=1.5,
                             alpha=0.7,
                             color=darker_hex,
                             label=f'  ↑ {place_name} (output)',
                             zorder=5)  # Behind transitions
                
                if debug:
    
                    pass
    def _format_plot(self):
        """Format the plot with labels, grid, and combined legend from both axes.
        
        Overrides parent method to handle dual Y-axes for transitions and places.
        """
        # Call parent formatting for main axis
        super()._format_plot()
        
        # If we have a secondary axis for places, combine legends
        if hasattr(self, '_places_axes') and self.show_legend and self.selected_objects:
            # Get handles and labels from both axes
            handles1, labels1 = self.axes.get_legend_handles_labels()
            handles2, labels2 = self._places_axes.get_legend_handles_labels()
            
            # Combine them
            if handles1 or handles2:
                # Remove any existing legends first
                if self.axes.get_legend():
                    self.axes.get_legend().remove()
                if self._places_axes.get_legend():
                    self._places_axes.get_legend().remove()
                
                # Create combined legend on the main axes
                self.axes.legend(handles1 + handles2, labels1 + labels2, 
                               loc='best', fontsize=9)
