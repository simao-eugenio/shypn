"""Rate Calculator Utilities.

This module provides utility functions for calculating rates from raw simulation data:
- Token consumption/production rate (d(tokens)/dt) for places
- Transition firing rate (firings/time) for transitions

The calculator supports:
- Configurable time windows for rate calculation
- Moving average smoothing for noisy data
- Handling of edge cases (insufficient data, zero time windows)
"""
from typing import List, Tuple


class RateCalculator:
    """Utility class for calculating rates from simulation data.
    
    This class provides static methods for computing:
    1. Token rate: Change in token count per unit time (d(tokens)/dt)
       - Positive rate indicates token production
       - Negative rate indicates token consumption
       
    2. Firing rate: Number of transition firings per unit time
       - Measured in firings/second (Hz)
       - Uses a sliding time window for smoothing
    
    All methods are static and stateless - no instance needed.
    
    Example:
        # Calculate token rate for a place
        rate = RateCalculator.calculate_token_rate(
            [(0.0, 10), (0.1, 12), (0.2, 15)],
            time_window=0.1
        )  # Returns rate at t=0.2
        
        # Calculate firing rate for a transition
        firing_times = [0.1, 0.3, 0.5, 0.6, 0.8]
        rate = RateCalculator.calculate_firing_rate(
            firing_times,
            current_time=1.0,
            time_window=1.0
        )  # Returns 5.0 firings/s
    """
    
    @staticmethod
    def calculate_token_rate(data_points: List[Tuple[float, int]], 
                            time_window: float = 0.1) -> float:
        """Calculate token consumption/production rate from place data.
        
        The rate is calculated as:
            rate = Δtokens / Δtime
        
        where Δtokens and Δtime are computed over the most recent data points
        within the time window.
        
        Args:
            data_points: List of (time, tokens) tuples in chronological order
            time_window: Time window for rate calculation in seconds (default: 0.1s)
            
        Returns:
            Token rate in tokens/second. Returns 0.0 if insufficient data.
            Positive values indicate token production.
            Negative values indicate token consumption.
            
        Example:
            data = [(0.0, 10), (0.1, 10), (0.2, 12), (0.3, 15)]
            rate = RateCalculator.calculate_token_rate(data, time_window=0.1)
            # At t=0.3: (15-12)/(0.3-0.2) = 30 tokens/s (production)
        """
        if len(data_points) < 2:
            return 0.0
        
        # Get current time (last data point)
        current_time = data_points[-1][0]
        
        # Find all points within the time window
        recent_points = [(t, tokens) for t, tokens in data_points 
                        if current_time - t <= time_window]
        
        if len(recent_points) < 2:
            return 0.0
        
        # Calculate rate using first and last points in window
        dt = recent_points[-1][0] - recent_points[0][0]
        dtokens = recent_points[-1][1] - recent_points[0][1]
        
        return dtokens / dt if dt > 0 else 0.0
    
    @staticmethod
    def calculate_firing_rate(event_times: List[float],
                             current_time: float,
                             time_window: float = 1.0) -> float:
        """Calculate transition firing rate from firing events.
        
        The rate is calculated as:
            rate = number_of_firings / time_window
        
        where number_of_firings is the count of firing events within the time window
        ending at current_time.
        
        Args:
            event_times: List of firing event timestamps
            current_time: Current simulation time (end of time window)
            time_window: Time window for rate calculation in seconds (default: 1.0s)
            
        Returns:
            Firing rate in firings/second. Returns 0.0 if no firings in window.
            
        Example:
            firing_times = [0.1, 0.3, 0.5, 0.6, 0.8, 1.0]
            rate = RateCalculator.calculate_firing_rate(
                firing_times,
                current_time=1.0,
                time_window=1.0
            )
            # Returns 6.0 firings/s (6 firings in 1.0s window)
        """
        if not event_times:
            return 0.0
        
        # Count firings within time window
        recent_firings = [t for t in event_times 
                         if current_time - t <= time_window and t <= current_time]
        
        return len(recent_firings) / time_window
    
    @staticmethod
    def moving_average(rates: List[float], window_size: int = 5) -> List[float]:
        """Apply moving average smoothing to rate data.
        
        This reduces noise in rate calculations by averaging over a window of recent values.
        Uses a simple moving average (SMA) algorithm.
        
        Args:
            rates: List of rate values to smooth
            window_size: Number of points to average (default: 5)
            
        Returns:
            List of smoothed rate values (same length as input)
            
        Example:
            raw_rates = [1.0, 5.0, 2.0, 4.0, 3.0]
            smoothed = RateCalculator.moving_average(raw_rates, window_size=3)
            # Returns: [1.0, 3.0, 2.67, 3.67, 3.0]
        """
        if len(rates) < window_size:
            return rates.copy()
        
        smoothed = []
        for i in range(len(rates)):
            # Determine the window start (don't go below index 0)
            start = max(0, i - window_size + 1)
            # Get the window of values
            window = rates[start:i+1]
            # Calculate average
            smoothed.append(sum(window) / len(window))
        
        return smoothed
    
    @staticmethod
    def calculate_token_rate_series(data_points: List[Tuple[float, int]], 
                                   time_window: float = 0.1,
                                   sample_interval: float = 0.01) -> List[Tuple[float, float]]:
        """Calculate a time series of token rates.
        
        This is a convenience method that calculates the token rate at multiple time points,
        useful for generating plot data.
        
        Args:
            data_points: List of (time, tokens) tuples
            time_window: Time window for each rate calculation
            sample_interval: Time interval between rate samples
            
        Returns:
            List of (time, rate) tuples
            
        Example:
            data = [(0.0, 10), (0.1, 12), (0.2, 15), (0.3, 14)]
            rate_series = RateCalculator.calculate_token_rate_series(
                data,
                time_window=0.1,
                sample_interval=0.1
            )
            # Returns: [(0.1, 20.0), (0.2, 30.0), (0.3, -10.0)]
        """
        if len(data_points) < 2:
            return []
        
        rate_series = []
        
        # Start from the second data point (need at least 2 points for rate)
        for i in range(1, len(data_points)):
            time = data_points[i][0]
            
            # Get data up to this point
            data_up_to_now = data_points[:i+1]
            
            # Calculate rate at this time
            rate = RateCalculator.calculate_token_rate(data_up_to_now, time_window)
            
            rate_series.append((time, rate))
        
        return rate_series
    
    @staticmethod
    def calculate_firing_rate_series(event_times: List[float],
                                    time_window: float = 1.0,
                                    sample_interval: float = 0.1) -> List[Tuple[float, float]]:
        """Calculate a time series of firing rates.
        
        This is a convenience method that calculates the firing rate at multiple time points,
        useful for generating plot data.
        
        Args:
            event_times: List of firing event timestamps
            time_window: Time window for each rate calculation
            sample_interval: Time interval between rate samples
            
        Returns:
            List of (time, rate) tuples
            
        Example:
            firing_times = [0.1, 0.3, 0.5, 0.6, 0.8]
            rate_series = RateCalculator.calculate_firing_rate_series(
                firing_times,
                time_window=1.0,
                sample_interval=0.2
            )
            # Returns rates sampled every 0.2s
        """
        if not event_times:
            return []
        
        rate_series = []
        
        start_time = event_times[0]
        end_time = event_times[-1]
        
        # Sample at regular intervals
        current_time = start_time
        while current_time <= end_time:
            rate = RateCalculator.calculate_firing_rate(
                event_times,
                current_time,
                time_window
            )
            rate_series.append((current_time, rate))
            current_time += sample_interval
        
        # Add final point at end_time if not already sampled
        if rate_series and rate_series[-1][0] < end_time:
            rate = RateCalculator.calculate_firing_rate(
                event_times,
                end_time,
                time_window
            )
            rate_series.append((end_time, rate))
        
        return rate_series
