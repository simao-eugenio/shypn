#!/usr/bin/env python3
"""Data Collector for simulation time-series recording.

Collects place tokens and transition firing counts at each simulation step.
"""
from typing import Dict, List, Tuple, Optional


class DataCollector:
    """Collects time-series data during simulation.
    
    Records:
    - Time points (list of floats)
    - Place tokens at each time point (dict: place_id -> list of token counts)
    - Transition firings at each time point (dict: transition_id -> cumulative count)
    
    Thread-safe for single-threaded GTK event loop.
    """
    
    def __init__(self, model):
        """Initialize data collector.
        
        Args:
            model: DocumentModel instance with places and transitions
        """
        self.model = model
        self.time_points: List[float] = []
        self.place_data: Dict[str, List[int]] = {}
        self.transition_data: Dict[str, List[int]] = {}
        self.is_collecting: bool = False
        
    def start_collection(self):
        """Initialize data structures and start collecting."""
        self.time_points = []
        
        # Initialize place data with empty lists
        self.place_data = {p.id: [] for p in self.model.places}
        
        # Initialize transition data with empty lists
        self.transition_data = {t.id: [] for t in self.model.transitions}
        
        self.is_collecting = True
        print(f"[NEW_DC] start_collection() called - initialized for {len(self.place_data)} places, {len(self.transition_data)} transitions")
        
    def record_state(self, current_time: float):
        """Record current state at given time point.
        
        Args:
            current_time: Current simulation time
        """
        if not self.is_collecting:
            return
        
        step_num = len(self.time_points) + 1
        if step_num <= 3:
            print(f"[NEW_DC] record_state() step {step_num} at time {current_time:.4f}")
            
        self.time_points.append(current_time)
        
        # Record place tokens
        for place in self.model.places:
            tokens = place.tokens
            self.place_data[place.id].append(tokens)
            
        # Record transition firing counts (cumulative)
        for transition in self.model.transitions:
            count = getattr(transition, 'firing_count', 0)
            self.transition_data[transition.id].append(count)
    
    def stop_collection(self):
        """Stop collecting data."""
        self.is_collecting = False
        print(f"[NEW_DC] stop_collection() - collected {len(self.time_points)} time points")
        
    def clear(self):
        """Clear all collected data."""
        self.time_points.clear()
        self.place_data.clear()
        self.transition_data.clear()
        self.is_collecting = False
        
    def get_place_series(self, place_id: str) -> Tuple[List[float], List[int]]:
        """Get time-series for a specific place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Tuple of (time_points, token_counts)
        """
        return self.time_points.copy(), self.place_data.get(place_id, []).copy()
        
    def get_transition_series(self, transition_id: str) -> Tuple[List[float], List[int]]:
        """Get time-series for a specific transition.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Tuple of (time_points, firing_counts)
        """
        return self.time_points.copy(), self.transition_data.get(transition_id, []).copy()
        
    def has_data(self) -> bool:
        """Check if any data has been collected.
        
        Returns:
            True if data is available, False otherwise
        """
        return len(self.time_points) > 0
