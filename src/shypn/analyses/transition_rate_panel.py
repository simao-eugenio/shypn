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
