#!/usr/bin/env python3
"""Reaction (Transition) analyzer for simulation data.

Calculates activity metrics for each transition based on firing data.
"""
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class ActivityStatus(Enum):
    """Reaction activity classification."""
    INACTIVE = "Inactive"      # Never fired
    LOW = "Low"               # Fired < 10 times
    ACTIVE = "Active"         # Fired >= 10 times
    HIGH = "High"             # Fired > 100 times


@dataclass
class ReactionMetrics:
    """Metrics for a single reaction (transition)."""
    
    transition_id: str
    transition_name: str
    transition_type: str = "stochastic"
    firing_count: int = 0
    average_rate: float = 0.0      # firings per time unit
    total_flux: int = 0            # total tokens processed
    contribution: float = 0.0       # percentage of total network flux
    status: ActivityStatus = ActivityStatus.INACTIVE


class ReactionAnalyzer:
    """Analyze transition (reaction) data from simulation."""
    
    def __init__(self, data_collector):
        """Initialize analyzer.
        
        Args:
            data_collector: DataCollector instance with recorded data
        """
        self.data_collector = data_collector
        # Store model reference for accessing arcs
        self.model = data_collector.model if hasattr(data_collector, 'model') else None
        
    def analyze_all_reactions(self, duration: float) -> List[ReactionMetrics]:
        """Analyze all transitions and return metrics.
        
        Args:
            duration: Simulation duration in time units
            
        Returns:
            List of ReactionMetrics for each transition
        """
        results = []
        total_flux = 0
        
        # First pass: calculate individual metrics and total flux
        for transition in self.data_collector.model.transitions:
            metrics = self._analyze_transition(transition, duration)
            results.append(metrics)
            total_flux += metrics.total_flux
            
        # Second pass: calculate contribution percentages
        if total_flux > 0:
            for metrics in results:
                metrics.contribution = (metrics.total_flux / total_flux) * 100.0
                
        return results
        
    def _analyze_transition(self, transition, duration: float) -> ReactionMetrics:
        """Analyze a single transition.
        
        Args:
            transition: Transition instance
            duration: Simulation duration
            
        Returns:
            ReactionMetrics for the transition
        """
        metrics = ReactionMetrics(
            transition_id=transition.id,
            transition_name=transition.label or transition.id,
            transition_type=self._get_transition_type(transition)
        )
        
        time_points, firing_series = self.data_collector.get_transition_series(transition.id)
        
        if not firing_series:
            # No data collected - use current firing_count if available
            metrics.firing_count = getattr(transition, 'firing_count', 0)
        else:
            metrics.firing_count = firing_series[-1]  # Final cumulative count
            
        # Calculate average rate
        if duration > 0:
            metrics.average_rate = metrics.firing_count / duration
            
        # Calculate total flux (tokens processed)
        # For simplicity: flux = firing_count * output_tokens_per_firing
        # Get output arcs from model (transition → place)
        output_arcs = [arc for arc in self.model.arcs 
                      if hasattr(arc, 'source') and arc.source == transition]
        tokens_per_firing = sum(arc.weight for arc in output_arcs) if output_arcs else 1
        metrics.total_flux = metrics.firing_count * tokens_per_firing
        
        # Classify activity status
        metrics.status = self._classify_activity(metrics.firing_count)
            
        return metrics
        
    def _get_transition_type(self, transition) -> str:
        """Get transition type.
        
        Args:
            transition: Transition instance
            
        Returns:
            Type as string ("stochastic" or "continuous")
        """
        if hasattr(transition, 'transition_type'):
            # transition_type is already a string, not an enum
            transition_type = transition.transition_type
            if isinstance(transition_type, str):
                return transition_type
            # Fallback: if it's an enum, get its value
            return str(transition_type.value)
        return "stochastic"
        
    def _classify_activity(self, firing_count: int) -> ActivityStatus:
        """Classify activity based on firing count.
        
        Args:
            firing_count: Total number of firings
            
        Returns:
            ActivityStatus classification
        """
        if firing_count == 0:
            return ActivityStatus.INACTIVE
        elif firing_count < 10:
            return ActivityStatus.LOW
        elif firing_count > 100:
            return ActivityStatus.HIGH
        else:
            return ActivityStatus.ACTIVE
