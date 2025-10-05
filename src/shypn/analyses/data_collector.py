"""Simulation Data Collector.

This module provides the SimulationDataCollector class which collects raw time-series data
from Petri net simulations for subsequent rate analysis and plotting.

Data collected:
    - Place token counts at each simulation step
    - Transition firing events (timestamp, event type)

The data is stored in memory-efficient structures optimized for rate calculations.
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any


class SimulationDataCollector:
    """Collects raw simulation data for rate-based analysis.
    
    This class acts as a step listener for the simulation controller, capturing:
    - Place token counts over time for rate calculations (d(tokens)/dt)
    - Transition firing events for firing rate calculations (firings/time)
    
    The collector implements automatic data management to prevent unbounded memory growth:
    - Maximum data points limit per object
    - Automatic downsampling when threshold is exceeded
    
    Attributes:
        place_data: Dictionary mapping place_id to list of (time, tokens) tuples
        transition_data: Dictionary mapping transition_id to list of (time, event_type, details) tuples
        max_data_points: Maximum number of data points to keep per object
        downsample_threshold: Threshold at which downsampling is triggered
    
    Example:
        collector = SimulationDataCollector()
        controller.add_step_listener(collector.on_simulation_step)
        controller.data_collector = collector  # For transition firing notifications
        
        # After simulation runs, access data:
        place_history = collector.place_data[place_id]  # [(time, tokens), ...]
        firing_events = collector.transition_data[trans_id]  # [(time, 'fired', None), ...]
    """
    
    def __init__(self, max_data_points: int = 10000, downsample_threshold: int = 8000):
        """Initialize the data collector.
        
        Args:
            max_data_points: Maximum number of data points to keep per object
            downsample_threshold: Trigger downsampling when this many points are reached
        """
        # Place data: {place_id: [(time, tokens), ...]}
        self.place_data: Dict[Any, List[Tuple[float, int]]] = defaultdict(list)
        
        # Transition data: {transition_id: [(time, event_type, details), ...]}
        self.transition_data: Dict[Any, List[Tuple[float, str, Any]]] = defaultdict(list)
        
        # Configuration
        self.max_data_points = max_data_points
        self.downsample_threshold = downsample_threshold
        
        # Statistics
        self.step_count = 0
        self.total_firings = 0
    
    def on_simulation_step(self, controller, time: float):
        """Collect data on each simulation step.
        
        This method is called by the simulation controller after each step.
        It records the current token count for all places.
        
        Args:
            controller: The simulation controller instance
            time: Current simulation time
        """
        self.step_count += 1
        
        DEBUG_DATA_COLLECTOR = False  # Set to True for detailed logging
        
        # Collect place token counts
        for place in controller.model.places:
            data = self.place_data[place.id]
            data.append((time, place.tokens))
            
            if DEBUG_DATA_COLLECTOR and self.step_count <= 5:
                print(f"[DataCollector] Step {self.step_count}: P{place.id} = {place.tokens} tokens at t={time:.3f}s")
            
            # Downsample if threshold exceeded
            if len(data) > self.downsample_threshold:
                self._downsample_place_data(place.id)
    
    def on_transition_fired(self, transition, time: float, details: Any = None):
        """Record a transition firing event.
        
        This method should be called by the simulation controller when a transition fires.
        
        Args:
            transition: The transition that fired
            time: Time of the firing event
            details: Optional additional details about the firing
        """
        self.total_firings += 1
        
        data = self.transition_data[transition.id]
        data.append((time, 'fired', details))
        
        # Downsample if threshold exceeded
        if len(data) > self.downsample_threshold:
            self._downsample_transition_data(transition.id)
    
    def _downsample_place_data(self, place_id: Any):
        """Downsample place data by keeping every 2nd point.
        
        Args:
            place_id: ID of the place to downsample
        """
        data = self.place_data[place_id]
        
        # Keep first point, then every 2nd point, then last point
        if len(data) > 2:
            downsampled = [data[0]]  # Keep first
            downsampled.extend(data[1:-1:2])  # Every 2nd point (skip first and last)
            downsampled.append(data[-1])  # Keep last
            self.place_data[place_id] = downsampled
    
    def _downsample_transition_data(self, transition_id: Any):
        """Downsample transition data by keeping every 2nd firing event.
        
        Args:
            transition_id: ID of the transition to downsample
        """
        data = self.transition_data[transition_id]
        
        # Keep first event, then every 2nd event, then last event
        if len(data) > 2:
            downsampled = [data[0]]  # Keep first
            downsampled.extend(data[1:-1:2])  # Every 2nd event
            downsampled.append(data[-1])  # Keep last
            self.transition_data[transition_id] = downsampled
    
    def clear(self):
        """Clear all collected data."""
        self.place_data.clear()
        self.transition_data.clear()
        self.step_count = 0
        self.total_firings = 0
    
    def clear_place(self, place_id: Any):
        """Clear data for a specific place.
        
        Args:
            place_id: ID of the place to clear
        """
        if place_id in self.place_data:
            del self.place_data[place_id]
    
    def clear_transition(self, transition_id: Any):
        """Clear data for a specific transition.
        
        Args:
            transition_id: ID of the transition to clear
        """
        if transition_id in self.transition_data:
            del self.transition_data[transition_id]
    
    def get_place_data(self, place_id: Any) -> List[Tuple[float, int]]:
        """Get the data for a specific place.
        
        Args:
            place_id: ID of the place
            
        Returns:
            List of (time, tokens) tuples, or empty list if place not found
        """
        return self.place_data.get(place_id, [])
    
    def get_transition_data(self, transition_id: Any) -> List[Tuple[float, str, Any]]:
        """Get the data for a specific transition.
        
        Args:
            transition_id: ID of the transition
            
        Returns:
            List of (time, event_type, details) tuples, or empty list if transition not found
        """
        return self.transition_data.get(transition_id, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with statistics about the collected data
        """
        return {
            'step_count': self.step_count,
            'total_firings': self.total_firings,
            'places_tracked': len(self.place_data),
            'transitions_tracked': len(self.transition_data),
            'total_place_points': sum(len(data) for data in self.place_data.values()),
            'total_transition_events': sum(len(data) for data in self.transition_data.values()),
        }
