#!/usr/bin/env python3
"""Species (Place) analyzer for simulation data.

Calculates metrics for each place based on collected time-series data.
"""
from typing import List, Optional
import statistics
from dataclasses import dataclass


@dataclass
class SpeciesMetrics:
    """Metrics for a single species (place)."""
    
    place_id: str
    place_name: str
    place_color: str = "#000000"
    initial_tokens: int = 0
    final_tokens: int = 0
    min_tokens: int = 0
    max_tokens: int = 0
    avg_tokens: float = 0.0
    total_change: int = 0
    change_rate: float = 0.0  # tokens per time unit


class SpeciesAnalyzer:
    """Analyze place (species) data from simulation."""
    
    def __init__(self, data_collector):
        """Initialize analyzer.
        
        Args:
            data_collector: DataCollector instance with recorded data
        """
        self.data_collector = data_collector
        
    def analyze_all_species(self, duration: float) -> List[SpeciesMetrics]:
        """Analyze all places and return metrics.
        
        Args:
            duration: Simulation duration in time units
            
        Returns:
            List of SpeciesMetrics for each place
        """
        results = []
        
        for place in self.data_collector.model.places:
            metrics = self._analyze_place(place, duration)
            results.append(metrics)
            
        return results
        
    def _analyze_place(self, place, duration: float) -> SpeciesMetrics:
        """Analyze a single place.
        
        Args:
            place: Place instance
            duration: Simulation duration
            
        Returns:
            SpeciesMetrics for the place
        """
        metrics = SpeciesMetrics(
            place_id=place.id,
            place_name=place.label or place.id,
            place_color=self._get_place_color(place)
        )
        
        time_points, token_series = self.data_collector.get_place_series(place.id)
        
        if not token_series:
            # No data collected - use current state
            metrics.initial_tokens = place.tokens
            metrics.final_tokens = place.tokens
            metrics.min_tokens = place.tokens
            metrics.max_tokens = place.tokens
            metrics.avg_tokens = float(place.tokens)
            return metrics
            
        # Calculate metrics from time-series
        metrics.initial_tokens = token_series[0]
        metrics.final_tokens = token_series[-1]
        metrics.min_tokens = min(token_series)
        metrics.max_tokens = max(token_series)
        metrics.avg_tokens = statistics.mean(token_series)
        metrics.total_change = metrics.final_tokens - metrics.initial_tokens
        
        if duration > 0:
            metrics.change_rate = metrics.total_change / duration
            
        return metrics
        
    def _get_place_color(self, place) -> str:
        """Get place color for display.
        
        Args:
            place: Place instance
            
        Returns:
            Color as hex string (e.g., "#FF0000")
        """
        if hasattr(place, 'color') and place.color:
            return place.color
        return "#000000"
