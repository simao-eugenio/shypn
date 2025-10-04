"""Place Rate Analysis Panel.

This module provides the PlaceRatePanel class for plotting place token
consumption/production rates in real-time during simulation.

This is a SEPARATE MODULE - not implemented in loaders!
Loaders only instantiate this panel and attach it to the UI.
"""
from typing import List, Tuple, Any

from shypn.analyses.plot_panel import AnalysisPlotPanel


class PlaceRatePanel(AnalysisPlotPanel):
    """Panel for plotting place token consumption/production rates.
    
    This panel displays the rate of token change (d(tokens)/dt) for selected places
    over simulation time. The rate calculation uses a sliding time window to provide
    smooth, meaningful values.
    
    Rate interpretation:
    - Positive rate: Token production (tokens being added to place)
    - Negative rate: Token consumption (tokens being removed from place)
    - Zero rate: Stable state (no net token change)
    
    The plot includes a zero reference line to clearly distinguish consumption
    from production.
    
    Attributes:
        time_window: Time window for rate calculation (default: 0.1s)
    
    Example:
        # Create panel (in right_panel_loader or similar)
        place_panel = PlaceRatePanel(data_collector)
        
        # Add places for analysis
        place_panel.add_object(place1)
        place_panel.add_object(place2)
        
        # Panel automatically updates during simulation
    """
    
    def __init__(self, data_collector):
        """Initialize the place rate analysis panel.
        
        Args:
            data_collector: SimulationDataCollector instance
        """
        super().__init__('place', data_collector)
        
        # Time window for rate calculation (100ms default)
        self.time_window = 0.1  # seconds
        
        print("[PlaceRatePanel] Initialized place rate analysis panel")
    
    def _get_rate_data(self, place_id: Any) -> List[Tuple[float, float]]:
        """Calculate token rate data for a place.
        
        Computes d(tokens)/dt using the configured time window.
        Uses RateCalculator utility for consistent rate computation.
        
        Args:
            place_id: ID of the place
            
        Returns:
            List of (time, rate) tuples where rate is in tokens/second
        """
        # Get raw token count data from collector
        raw_data = self.data_collector.get_place_data(place_id)
        
        if len(raw_data) < 2:
            return []
        
        # Calculate rate at each time point using time series method
        rate_series = self.rate_calculator.calculate_token_rate_series(
            raw_data,
            time_window=self.time_window,
            sample_interval=0.01  # Sample every 10ms for smooth plot
        )
        
        return rate_series
    
    def _get_ylabel(self) -> str:
        """Get Y-axis label for token rate plot.
        
        Returns:
            str: Y-axis label
        """
        return 'Token Rate (tokens/s)'
    
    def _get_title(self) -> str:
        """Get plot title for token rate plot.
        
        Returns:
            str: Plot title
        """
        return 'Place Token Consumption/Production Rate'
    
    def set_time_window(self, window: float):
        """Set the time window for rate calculation.
        
        Larger windows provide smoother rates but less responsiveness.
        Smaller windows show rapid changes but may be noisier.
        
        Args:
            window: Time window in seconds (e.g., 0.1 = 100ms)
        """
        if window <= 0:
            print(f"[PlaceRatePanel] Invalid time window: {window}, must be > 0")
            return
        
        self.time_window = window
        self.needs_update = True
        print(f"[PlaceRatePanel] Set time window to {window}s")
