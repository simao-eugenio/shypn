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
    
    def __init__(self, data_collector, place_panel=None):
        """Initialize the transition behavior analysis panel.
        
        Args:
            data_collector: SimulationDataCollector instance
            place_panel: Optional PlaceRatePanel instance for locality plotting
        """
        super().__init__('transition', data_collector)
        
        # Locality plotting support
        self._locality_places = {}  # Maps transition_id -> {input_places, output_places}
        self._place_panel = place_panel  # Reference to PlaceRatePanel for adding locality places
    
    def set_place_panel(self, place_panel):
        """Set the PlaceRatePanel reference for locality plotting.
        
        This allows setting the reference after initialization, which is useful
        when panels are created independently.
        
        Args:
            place_panel: PlaceRatePanel instance
        """
        self._place_panel = place_panel
    
    def add_object(self, obj):
        """Add a transition to the selected list for plotting.
        
        Overrides parent to use full list rebuild instead of incremental add,
        because we need to show locality places under each transition.
        
        Args:
            obj: Transition object to add
        """
        if any((o.id == obj.id for o in self.selected_objects)):
            return
        
        # Get the color that will be assigned to this object
        index = len(self.selected_objects)
        color_hex = self._get_color(index)
        
        # Convert hex color to RGB tuple for Cairo rendering
        import matplotlib.colors as mcolors
        color_rgb = mcolors.hex2color(color_hex)
        
        # Set both border and fill color to match the plot color
        obj.border_color = color_rgb
        obj.fill_color = color_rgb
        
        # Trigger object's on_changed callback to notify the canvas
        if hasattr(obj, 'on_changed') and obj.on_changed:
            obj.on_changed()
        
        self.selected_objects.append(obj)
        # Use full rebuild to show locality places in UI list
        self._update_objects_list()
        self.needs_update = True
        
        # Trigger canvas redraw to show the new colors
        if self._model_manager:
            self._model_manager.mark_needs_redraw()
    
    def _get_rate_data(self, transition_id: Any) -> List[Tuple[float, float]]:
        """Get behavior-specific data for a transition.
        
        The data plotted depends on transition type:
        - Continuous enzymatic (Hill, M-M): (concentration, rate) - substrate concentration vs reaction rate
        - Continuous time-based: (time, rate) - time vs rate value
        - Discrete (immediate/timed/stochastic): (time, cumulative_count)
        
        Args:
            transition_id: ID of the transition
            
        Returns:
            List of (x, y) tuples where x is time or concentration depending on function type
        """
        DEBUG_PLOT_DATA = False  # Disable verbose logging
        
        # Safety check: return empty if no data collector
        if not self.data_collector:
            return []
        
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
            # CONTINUOUS TRANSITION: Check if enzymatic function (needs concentration on X-axis)
            # Get the transition object to check its rate function
            transition_obj = None
            for obj in self.selected_objects:
                if obj.id == transition_id:
                    transition_obj = obj
                    break
            
            # Detect if this is an enzymatic function
            is_enzymatic = False
            input_place_id = None
            if transition_obj:
                rate_func = None
                if hasattr(transition_obj, 'properties') and transition_obj.properties:
                    rate_func = transition_obj.properties.get('rate_function') or transition_obj.properties.get('rate_function_display')
                if not rate_func:
                    rate_func = str(getattr(transition_obj, 'rate', ''))
                
                if rate_func and rate_func != 'None':
                    func_type, params = self._detect_rate_function_type(rate_func)
                    is_enzymatic = func_type in ['hill_equation', 'michaelis_menten']
                    
                    # Get the input place (substrate) for concentration lookup
                    # Since transition doesn't have model reference, extract place name from rate function
                    if is_enzymatic:
                        # Extract place name from rate function (e.g., "P1" from "hill_equation(P1, ...)")
                        import re
                        place_match = re.search(r'\(([A-Za-z_]\w*)', rate_func)
                        if place_match:
                            place_name = place_match.group(1)
                            
                            # Try to find this place in the data_collector's tracked places
                            # The place ID might be the place name or an object ID
                            # We'll try to match by looking at all tracked places
                            for tracked_place_id in self.data_collector.place_data.keys():
                                # Use the first place with data as substrate concentration source
                                # TODO: Better matching - for now use first available
                                input_place_id = tracked_place_id
                                break
            
            rate_series = []
            
            # For enzymatic functions, we need to match times with place concentrations
            if is_enzymatic and input_place_id:
                # Get place token history
                place_history = self.data_collector.get_place_data(input_place_id)
                
                # Create a time -> concentration lookup
                time_to_concentration = {}
                for place_time, tokens in place_history:
                    time_to_concentration[place_time] = tokens
                
                # Match transition rates with substrate concentrations at those times
                for time, event_type, details in raw_events:
                    if event_type == 'fired' and details and isinstance(details, dict):
                        rate = details.get('rate', 0.0)
                        
                        # Find the closest concentration measurement
                        concentration = time_to_concentration.get(time)
                        if concentration is None and place_history:
                            # Interpolate or use closest time point
                            closest_time = min(time_to_concentration.keys(), 
                                             key=lambda t: abs(t - time))
                            concentration = time_to_concentration[closest_time]
                        
                        if concentration is not None:
                            rate_series.append((concentration, rate))
            else:
                if DEBUG_PLOT_DATA:
                    pass
                # For time-based functions, use time as X-axis
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
            
            return cumulative_series
    
    def _get_ylabel(self) -> str:
        """Get Y-axis label for transition plot.
        
        The label depends on rate function type:
        - Hill equation: "Fraction Bound"
        - Michaelis-Menten: "Reaction Rate (v)"
        - Sigmoid: "Fraction Bound"
        - Continuous (other): "Rate (tokens/s)"
        - Discrete: "Cumulative Firings"
        
        Returns:
            str: Y-axis label
        """
        if not self.selected_objects:
            return 'Value'
        
        # Check if we have any continuous transitions with specific rate functions
        has_continuous = False
        has_discrete = False
        func_type = None
        
        for obj in self.selected_objects:
            raw_events = self.data_collector.get_transition_data(obj.id)
            if raw_events and len(raw_events) > 0:
                details = raw_events[0][2]
                if isinstance(details, dict) and 'rate' in details:
                    has_continuous = True
                    # Detect function type for label
                    if func_type is None:  # Use first object's function type
                        rate_func = None
                        if hasattr(obj, 'properties') and obj.properties:
                            rate_func = obj.properties.get('rate_function') or obj.properties.get('rate_function_display')
                        if not rate_func:
                            rate_func = str(getattr(obj, 'rate', ''))
                        if rate_func and rate_func != 'None':
                            func_type, _ = self._detect_rate_function_type(rate_func)
                else:
                    has_discrete = True
        
        if has_continuous and not has_discrete:
            # Return function-specific label
            if func_type == 'hill_equation':
                return 'Fraction Bound'
            elif func_type == 'michaelis_menten':
                return 'Reaction Rate (v)'
            elif func_type == 'sigmoid':
                return 'Fraction Bound'
            else:
                return 'Rate (tokens/s)'
        elif has_discrete and not has_continuous:
            return 'Cumulative Firings'
        else:
            return 'Value'  # Mixed types
    
    def _get_title(self) -> str:
        """Get plot title for transition plot.
        
        Shows function name and parameters if applicable.
        
        Returns:
            str: Plot title with function name and parameters
        """
        if not self.selected_objects:
            return 'Transition Behavior Evolution'
        
        # If single selection with specific rate function, show function details
        if len(self.selected_objects) == 1:
            obj = list(self.selected_objects)[0]
            rate_func = None
            if hasattr(obj, 'properties') and obj.properties:
                rate_func = obj.properties.get('rate_function') or obj.properties.get('rate_function_display')
            if not rate_func:
                rate_func = str(getattr(obj, 'rate', ''))
            
            if rate_func and rate_func != 'None':
                func_type, params = self._detect_rate_function_type(rate_func)
                
                if func_type == 'hill_equation':
                    vmax = params.get('vmax', '?')
                    kd = params.get('kd', '?')
                    n = params.get('n', '?')
                    return f'Hill Equation (vmax={vmax}, Kd={kd}, n={n})'
                elif func_type == 'michaelis_menten':
                    vmax = params.get('vmax', '?')
                    km = params.get('km', '?')
                    return f'Michaelis-Menten (vmax={vmax}, Km={km})'
                elif func_type == 'sigmoid':
                    center = params.get('center', '?')
                    steepness = params.get('steepness', '?')
                    return f'Sigmoid (center={center}, k={steepness})'
                elif func_type == 'exponential':
                    rate = params.get('rate', '?')
                    return f'Exponential (rate={rate})'
        
        return 'Transition Behavior Evolution'
    
    def _format_plot(self):
        """Format the plot with labels, grid, legend, and smart Y-axis and X-axis scaling.
        
        Overrides parent to add:
        - Concentration-based X-axis for enzymatic functions
        - Source/sink-aware Y-axis scaling
        - Rate function type-aware X-axis scaling (Hill, Michaelis-Menten, Sigmoid, etc.)
        - Annotations for key parameters (Kd, Km, center points)
        """
        # Call parent formatting first
        super()._format_plot()
        
        # Update X-axis label for enzymatic functions (Hill, Michaelis-Menten)
        if self.selected_objects:
            for obj in self.selected_objects:
                rate_func = None
                if hasattr(obj, 'properties') and obj.properties:
                    rate_func = obj.properties.get('rate_function') or obj.properties.get('rate_function_display')
                if not rate_func:
                    rate_func = str(getattr(obj, 'rate', ''))
                
                if rate_func and rate_func != 'None':
                    func_type, _ = self._detect_rate_function_type(rate_func)
                    if func_type in ['hill_equation', 'michaelis_menten']:
                        self.axes.set_xlabel('Concentration', fontsize=11)
                        break  # Only need to set once
        
        # Apply smart Y-axis scaling if not auto-scale
        if not self.auto_scale and self.selected_objects:
            self._apply_smart_ylim_scaling()
        
        # Apply rate function-aware X-axis scaling and annotations
        self._apply_rate_function_adjustments()
    
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
    
    def _apply_rate_function_adjustments(self):
        """Apply intelligent X-axis scaling and annotations based on rate function type.
        
        Detects rate function types (Hill, Michaelis-Menten, Sigmoid, etc.) from
        transition properties and adjusts plot accordingly:
        - Hill equation: X-axis 0 to 4×Kd, show Kd marker
        - Michaelis-Menten: X-axis 0 to 4×Km, show Km marker
        - Sigmoid: X-axis 0 to 2×center, show inflection point
        - Exponential: Extended X-axis for full curve visualization
        """
        import re
        
        # Only apply to continuous transitions with rate functions
        for obj in self.selected_objects:
            if getattr(obj, 'transition_type', '') != 'continuous':
                continue
            
            # Get rate function from properties
            rate_func = None
            if hasattr(obj, 'properties') and obj.properties:
                rate_func = obj.properties.get('rate_function') or obj.properties.get('rate_function_display')
            
            if not rate_func:
                # Try the rate attribute as fallback
                rate_func = str(getattr(obj, 'rate', ''))
            
            if not rate_func or rate_func == 'None':
                continue
            
            # Detect function type and extract parameters
            func_type, params = self._detect_rate_function_type(rate_func)
            
            if func_type == 'hill_equation':
                self._adjust_for_hill_equation(params, obj)
            elif func_type == 'michaelis_menten':
                self._adjust_for_michaelis_menten(params, obj)
            elif func_type == 'sigmoid':
                self._adjust_for_sigmoid(params, obj)
            elif func_type == 'exponential':
                self._adjust_for_exponential(params, obj)
    
    def _detect_rate_function_type(self, rate_func_str):
        """Detect the type of rate function and extract parameters.
        
        Args:
            rate_func_str: Rate function string from transition properties
            
        Returns:
            tuple: (function_type, parameters_dict)
                function_type: 'hill_equation', 'michaelis_menten', 'sigmoid', 'exponential', or 'unknown'
                parameters_dict: Extracted parameters like {'vmax': 10, 'kd': 5, 'n': 2}
        """
        import re
        
        rate_func_str = str(rate_func_str).strip()
        
        # Hill equation: hill_equation(P1, vmax=10, kd=5, n=2)
        if 'hill_equation' in rate_func_str:
            params = {}
            # Extract vmax
            vmax_match = re.search(r'vmax\s*=\s*([\d.]+)', rate_func_str)
            if vmax_match:
                params['vmax'] = float(vmax_match.group(1))
            # Extract kd
            kd_match = re.search(r'kd\s*=\s*([\d.]+)', rate_func_str)
            if kd_match:
                params['kd'] = float(kd_match.group(1))
            # Extract n (Hill coefficient)
            n_match = re.search(r'n\s*=\s*([\d.]+)', rate_func_str)
            if n_match:
                params['n'] = float(n_match.group(1))
            
            return ('hill_equation', params)
        
        # Michaelis-Menten: michaelis_menten(P1, vmax=10, km=5)
        elif 'michaelis_menten' in rate_func_str:
            params = {}
            # Extract vmax
            vmax_match = re.search(r'vmax\s*=\s*([\d.]+)', rate_func_str)
            if vmax_match:
                params['vmax'] = float(vmax_match.group(1))
            # Extract km
            km_match = re.search(r'km\s*=\s*([\d.]+)', rate_func_str)
            if km_match:
                params['km'] = float(km_match.group(1))
            
            return ('michaelis_menten', params)
        
        # Sigmoid: sigmoid(t, 10, 0.5)
        elif 'sigmoid' in rate_func_str:
            params = {}
            # Extract center and steepness from sigmoid(t, center, steepness)
            sig_match = re.search(r'sigmoid\s*\([^,]+,\s*([\d.]+)\s*,\s*([\d.]+)\)', rate_func_str)
            if sig_match:
                params['center'] = float(sig_match.group(1))
                params['steepness'] = float(sig_match.group(2))
            
            return ('sigmoid', params)
        
        # Exponential: math.exp(0.1 * t) or exp(...)
        elif 'exp(' in rate_func_str or 'math.exp' in rate_func_str:
            params = {}
            # Try to extract the rate coefficient
            exp_match = re.search(r'exp\s*\(\s*([-+]?[\d.]+)\s*\*', rate_func_str)
            if exp_match:
                params['rate'] = float(exp_match.group(1))
                params['decay'] = params['rate'] < 0
            
            return ('exponential', params)
        
        return ('unknown', {})
    
    def _adjust_for_hill_equation(self, params, transition_obj):
        """Adjust plot for Hill equation: X-axis 0 to 4×Kd, show Kd marker.
        
        Args:
            params: Dict with 'vmax', 'kd', 'n' parameters
            transition_obj: Transition object
        """
        if 'kd' not in params:
            return
        
        kd = params['kd']
        vmax = params.get('vmax', 10.0)
        
        # Set X-axis range: 0 to 4×Kd (shows full sigmoid curve)
        xlim = self.axes.get_xlim()
        suggested_xmax = 4.0 * kd
        
        # Only adjust if current range is much larger (don't shrink if user zoomed in)
        if xlim[1] > suggested_xmax * 1.5 or xlim[1] < suggested_xmax * 0.5:
            self.axes.set_xlim(0, suggested_xmax)
        
        # Add vertical line at Kd (half-maximal response point)
        self.axes.axvline(x=kd, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
        
        # Add annotation
        y_pos = vmax / 2.0  # Half-maximal point
        self.axes.annotate(f'Kd = {kd}', 
                          xy=(kd, y_pos), 
                          xytext=(kd + kd * 0.2, y_pos),
                          fontsize=9, 
                          color='gray',
                          arrowprops=dict(arrowstyle='->', color='gray', lw=0.5))
    
    def _adjust_for_michaelis_menten(self, params, transition_obj):
        """Adjust plot for Michaelis-Menten: X-axis 0 to 4×Km, show Km marker.
        
        Args:
            params: Dict with 'vmax', 'km' parameters
            transition_obj: Transition object
        """
        if 'km' not in params:
            return
        
        km = params['km']
        vmax = params.get('vmax', 10.0)
        
        # Set X-axis range: 0 to 4×Km (shows saturation)
        xlim = self.axes.get_xlim()
        suggested_xmax = 4.0 * km
        
        if xlim[1] > suggested_xmax * 1.5 or xlim[1] < suggested_xmax * 0.5:
            self.axes.set_xlim(0, suggested_xmax)
        
        # Add vertical line at Km (V = Vmax/2 point)
        self.axes.axvline(x=km, color='orange', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
        
        # Add annotation
        y_pos = vmax / 2.0
        self.axes.annotate(f'Km = {km}', 
                          xy=(km, y_pos), 
                          xytext=(km + km * 0.2, y_pos),
                          fontsize=9, 
                          color='orange',
                          arrowprops=dict(arrowstyle='->', color='orange', lw=0.5))
    
    def _adjust_for_sigmoid(self, params, transition_obj):
        """Adjust plot for Sigmoid: X-axis 0 to 2×center, show inflection point.
        
        Args:
            params: Dict with 'center', 'steepness' parameters
            transition_obj: Transition object
        """
        if 'center' not in params:
            return
        
        center = params['center']
        
        # Set X-axis range: 0 to 2×center (shows full S-curve)
        xlim = self.axes.get_xlim()
        suggested_xmax = 2.0 * center
        
        if xlim[1] > suggested_xmax * 1.5 or xlim[1] < suggested_xmax * 0.5:
            self.axes.set_xlim(0, suggested_xmax)
        
        # Add vertical line at center (inflection point)
        self.axes.axvline(x=center, color='purple', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
        
        # Add annotation
        ylim = self.axes.get_ylim()
        y_pos = (ylim[0] + ylim[1]) / 2.0
        self.axes.annotate(f'Center = {center}', 
                          xy=(center, y_pos), 
                          xytext=(center + center * 0.1, y_pos),
                          fontsize=9, 
                          color='purple',
                          arrowprops=dict(arrowstyle='->', color='purple', lw=0.5))
    
    def _adjust_for_exponential(self, params, transition_obj):
        """Adjust plot for Exponential: Extended X-axis for full curve.
        
        Args:
            params: Dict with 'rate', 'decay' parameters
            transition_obj: Transition object
        """
        # For exponential, extend X-axis to show full behavior
        # Growth: show enough range to see exponential rise
        # Decay: show enough range to see decay to near-zero
        
        xlim = self.axes.get_xlim()
        
        if 'rate' in params:
            rate = abs(params['rate'])
            # Time constant: τ = 1/rate
            if rate > 0:
                time_constant = 1.0 / rate
                # Show 5 time constants (99% of change)
                suggested_xmax = 5.0 * time_constant
                
                if xlim[1] > suggested_xmax * 1.5 or xlim[1] < suggested_xmax * 0.5:
                    self.axes.set_xlim(0, suggested_xmax)
    
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
        
        This stores the locality places and actually adds them to the PlaceRatePanel
        so they can be plotted together with the transition, showing the complete 
        P-T-P pattern.
        
        Args:
            transition: Transition object
            locality: Locality object with input/output places
        """
        if not locality.is_valid:
            print(f"[TransitionRatePanel] Locality for {transition.name} is not valid")
            return
        
        print(f"[TransitionRatePanel] Adding locality for {transition.name}")
        print(f"  Input places: {[p.name for p in locality.input_places]}")
        print(f"  Output places: {[p.name for p in locality.output_places]}")
        print(f"  Place panel: {self._place_panel}")
        
        # Store locality information
        self._locality_places[transition.id] = {
            'input_places': list(locality.input_places),
            'output_places': list(locality.output_places),
            'transition': transition
        }
        
        # Actually add the locality places to the PlaceRatePanel for plotting
        if self._place_panel is not None:
            print(f"[TransitionRatePanel] Adding {locality.place_count} places to place panel")
            # Add input places
            for place in locality.input_places:
                self._place_panel.add_object(place)
                print(f"  Added input place: {place.name}")
            
            # Add output places
            for place in locality.output_places:
                self._place_panel.add_object(place)
                print(f"  Added output place: {place.name}")
        else:
            print("[TransitionRatePanel] WARNING: Place panel is None, cannot add locality places!")
        
        # Update the UI list to show locality places under the transition
        self._update_objects_list()
        
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
    
    def update_plot(self, force_full_redraw=False):
        """Update the plot with current data including locality places.
        
        Overrides parent method to add locality place plotting.
        
        Args:
            force_full_redraw: If True, force a full redraw even if object list hasn't changed.
                              Used when properties change to re-apply adjustments.
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
        # BUT still apply rate function adjustments for proper axis scaling
        if not has_any_data:
            self._show_waiting_state()
            # Apply rate function adjustments even without data
            # This ensures axis scaling is correct when data starts appearing
            self._apply_rate_function_adjustments()
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
