"""Transition Rate Analysis Panel.

This module provides the TransitionRatePanel class for plotting transition
firing rates in real-time during simulation.

This is a SEPARATE MODULE - not implemented in loaders!
Loaders only instantiate this panel and attach it to the UI.
"""
from typing import List, Tuple, Any

from shypn.analyses.plot_panel import AnalysisPlotPanel


class TransitionRatePanel(AnalysisPlotPanel):
    """Panel for plotting transition firing rates.
    
    This panel displays the firing rate (firings per unit time) for selected
    transitions over simulation time. The rate is calculated using a sliding
    time window to count firing events.
    
    Rate interpretation:
    - High rate: Transition firing frequently
    - Low rate: Transition firing occasionally
    - Zero rate: Transition not firing (may be disabled or in conflict)
    
    The firing rate is measured in Hz (firings per second) and uses a 1-second
    time window by default for meaningful frequency measurements.
    
    Attributes:
        time_window: Time window for rate calculation (default: 1.0s)
    
    Example:
        # Create panel (in right_panel_loader or similar)
        transition_panel = TransitionRatePanel(data_collector)
        
        # Add transitions for analysis
        transition_panel.add_object(transition1)
        transition_panel.add_object(transition2)
        
        # Panel automatically updates during simulation
    """
    
    def __init__(self, data_collector):
        """Initialize the transition rate analysis panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        super().__init__('transition', data_collector)
        
        # Time window for rate calculation (1 second default for frequency)
        self.time_window = 1.0  # seconds
        
        print("[TransitionRatePanel] Initialized transition rate analysis panel")
    
    def _get_rate_data(self, transition_id: Any) -> List[Tuple[float, float]]:
        """Calculate firing rate data for a transition.
        
        Computes firings/time using the configured time window.
        Uses RateCalculator utility for consistent rate computation.
        
        Args:
            transition_id: ID of the transition
            
        Returns:
            List of (time, rate) tuples where rate is in firings/second (Hz)
        """
        # Get raw firing event data from collector
        raw_events = self.data_collector.get_transition_data(transition_id)
        
        if not raw_events:
            return []
        
        # Extract firing times (filter out non-firing events)
        firing_times = [t for t, event_type, _ in raw_events 
                       if event_type == 'fired']
        
        if len(firing_times) < 1:
            return []
        
        # Calculate firing rate time series
        rate_series = self.rate_calculator.calculate_firing_rate_series(
            firing_times,
            time_window=self.time_window,
            sample_interval=0.1  # Sample every 100ms
        )
        
        return rate_series
    
    def _get_ylabel(self) -> str:
        """Get Y-axis label for firing rate plot.
        
        Returns:
            str: Y-axis label
        """
        return 'Firing Rate (firings/s)'
    
    def _get_title(self) -> str:
        """Get plot title for firing rate plot.
        
        Returns:
            str: Plot title
        """
        return 'Transition Firing Rate'
    
    def set_time_window(self, window: float):
        """Set the time window for rate calculation.
        
        Larger windows provide smoother rates and better frequency measurement.
        Smaller windows show rapid changes but may be noisier.
        
        For firing rates, 1.0s is recommended for meaningful Hz measurements.
        
        Args:
            window: Time window in seconds (e.g., 1.0 = 1 second)
        """
        if window <= 0:
            print(f"[TransitionRatePanel] Invalid time window: {window}, must be > 0")
            return
        
        self.time_window = window
        self.needs_update = True
        print(f"[TransitionRatePanel] Set time window to {window}s")
    
    def wire_search_ui(self, entry, search_btn, result_label, model):
        """Wire search UI controls to transition search functionality.
        
        This method connects the search entry, buttons, and result label from
        the right panel UI to the SearchHandler for finding transitions to add to analysis.
        
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
            
            # Import SearchHandler
            from shypn.analyses import SearchHandler
            
            # Perform search
            results = SearchHandler.search_transitions(self.search_model, query)
            self.search_results = results
            
            # Display results
            if results:
                summary = SearchHandler.format_result_summary(results, 'transition')
                self.search_result_label.set_text(summary)
                print(f"[TransitionRatePanel] Search found {len(results)} transitions")
                
                # If exactly one result, add it automatically
                if len(results) == 1:
                    self.add_object(results[0])
                    self.search_result_label.set_text(f"✓ Added {results[0].name} to analysis")
            else:
                self.search_result_label.set_text(f"✗ No transitions found for '{query}'")

        
        search_btn.connect('clicked', on_search_clicked)
        
        # Allow Enter key in search entry
        def on_entry_activate(entry):
            on_search_clicked(search_btn)
        
        entry.connect('activate', on_entry_activate)
        
        print("[TransitionRatePanel] Search UI wired successfully")
