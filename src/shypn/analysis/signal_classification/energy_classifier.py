#!/usr/bin/env python3
"""Energy Signal Classifier - Detects ENERGY signal places.

ENERGY signals are lowest-layer orchestrators that control synthesis capacity
and metabolic flux. They represent cellular energy state (ATP/ADP ratio,
NADH/NAD+ ratio, electron transport chain status).

Characteristics:
- Names: ATP, ADP, NADH, NAD+, GTP, energy, charge, phosphate
- Topology: Produced/consumed by many transitions (hub nodes)
- Dynamics: Affect rate functions multiplicatively (capacity control)
- Behavior: Saturation causes system-wide slowdown

Author: Simão Eugénio
Date: December 31, 2025
"""

from typing import Set, List
from .base_classifier import BaseSignalClassifier


class EnergySignalClassifier(BaseSignalClassifier):
    """Classifier for ENERGY signal places.
    
    Detects places representing cellular energy state that orchestrate
    metabolic flux capacity across the network.
    
    Example:
        classifier = EnergySignalClassifier(model)
        is_energy, confidence, breakdown = classifier.classify(atp_place)
    """
    
    def get_signal_type(self) -> str:
        """Return signal type identifier."""
        return 'ENERGY'
    
    def get_lexical_patterns(self) -> List[str]:
        """Return regex patterns for energy-related place names."""
        return [
            r'\bATP\b',
            r'\bADP\b',
            r'\bAMP\b',
            r'\bNADH\b',
            r'\bNAD\+?\b',
            r'\bNADPH\b',
            r'\bNADP\+?\b',
            r'\bGTP\b',
            r'\bGDP\b',
            r'\benergy\b',
            r'\bcharge\b',
            r'\bphosphate\b',
            r'\bPi\b',
            r'\bPPi\b',
            r'\belectron\b',
            r'\bproton.*gradient\b',
            r'\bATP.*ADP.*ratio\b',
        ]
    
    def get_biochemical_indicators(self) -> Set[str]:
        """Return standard energy compound names."""
        return {
            'ATP', 'ADP', 'AMP',
            'NADH', 'NAD', 'NAD+',
            'NADPH', 'NADP', 'NADP+',
            'GTP', 'GDP', 'GMP',
            'CoA', 'Acetyl-CoA',
            'Pi', 'PPi',
            'H+', 'PROTON',
        }
    
    def analyze_topology(self, place) -> float:
        """Analyze topology: energy places are highly connected hubs.
        
        Energy places typically:
        - Have high degree (connected to many transitions)
        - Are produced AND consumed (bidirectional flow)
        - Appear in multiple pathways
        
        Args:
            place: Place object to analyze
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Count transitions that consume this place
        consuming_transitions = 0
        producing_transitions = 0
        
        for arc in self.model.arcs:
            if arc.source == place:  # Place → Transition (consumption)
                consuming_transitions += 1
            elif arc.target == place:  # Transition → Place (production)
                producing_transitions += 1
        
        total_connections = consuming_transitions + producing_transitions
        
        # Energy places typically have >5 connections
        # and are both produced and consumed
        if total_connections >= 5 and consuming_transitions > 0 and producing_transitions > 0:
            # High connectivity score
            connectivity_score = min(1.0, total_connections / 10.0)
            
            # Bidirectional bonus
            bidirectional_score = 0.5
            
            return (connectivity_score + bidirectional_score) / 2.0
        
        elif total_connections >= 3:
            return 0.5  # Moderate connectivity
        
        return 0.0
    
    def analyze_dynamics(self, place, rate_functions: List[str]) -> float:
        """Analyze dynamics: energy places appear as multiplicative factors.
        
        Energy signals typically appear as capacity multipliers:
        - rate = k * ATP * substrate (mass action)
        - rate = k * (NADH / (Km + NADH)) (Michaelis-Menten)
        - Catalog: michaelis_menten with ATP as modifier
        
        Args:
            place: Place object
            rate_functions: Rate functions referencing this place
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not rate_functions:
            return 0.0
        
        multiplicative_count = 0
        saturation_count = 0
        michaelis_menten_count = 0
        
        place_name = place.name
        
        for rate_func in rate_functions:
            # Check for multiplicative appearance: "* ATP" or "ATP *"
            if f'* {place_name}' in rate_func or f'{place_name} *' in rate_func:
                multiplicative_count += 1
            
            # Check for saturation kinetics: "ATP / (K + ATP)"
            if f'{place_name} / (' in rate_func and f'+ {place_name}' in rate_func:
                saturation_count += 1
            
            # Check for Michaelis-Menten pattern from catalog
            if 'Vmax' in rate_func and 'Km' in rate_func and place_name in rate_func:
                michaelis_menten_count += 1
        
        # Score based on pattern frequency
        if multiplicative_count >= 2 or michaelis_menten_count >= 1:
            return 1.0  # Strong evidence
        elif multiplicative_count >= 1 or saturation_count >= 1:
            return 0.7  # Moderate evidence
        
        return 0.0
