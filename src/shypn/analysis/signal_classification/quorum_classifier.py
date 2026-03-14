#!/usr/bin/env python3
"""Quorum Signal Classifier - Detects QUORUM signal places.

QUORUM signals represent cell-cell communication molecules (autoinducers)
that accumulate independently of cellular energy state. They enable
population-level coordination (quorum sensing).

Characteristics:
- Names: AHL, AI-2, autoinducer, pheromone, quorum
- Topology: Self-production loops, extracellular accumulation
- Dynamics: Accumulate despite energy depletion (weak independence)
- Behavior: Context signals that integrate at regulatory layer

Author: Simão Eugénio
Date: December 31, 2025
"""

from typing import Set, List
from .base_classifier import BaseSignalClassifier


class QuorumSignalClassifier(BaseSignalClassifier):
    """Classifier for QUORUM signal places.
    
    Detects places representing quorum sensing molecules and other
    weakly independent context signals.
    
    Example:
        classifier = QuorumSignalClassifier(model)
        is_quorum, confidence, breakdown = classifier.classify(ahl_place)
    """
    
    def get_signal_type(self) -> str:
        """Return signal type identifier."""
        return 'QUORUM'
    
    def get_lexical_patterns(self) -> List[str]:
        """Return regex patterns for quorum-related place names."""
        return [
            r'\bAHL\b',
            r'\bAI-?2\b',
            r'\bautoinducer\b',
            r'\bquorum\b',
            r'\bpheromone\b',
            r'\bsignal.*molecule\b',
            r'\b3OC6HSL\b',
            r'\b3OC12HSL\b',
            r'\bC4HSL\b',
            r'\bHSL\b',
            r'\bLuxI\b',
            r'\bLuxR\b',
            r'\bAinS\b',
            r'\bLasI\b',
            r'\bRhlI\b',
            r'\bQS\b',
        ]
    
    def get_biochemical_indicators(self) -> Set[str]:
        """Return quorum sensing compound names."""
        return {
            'AHL',
            'AI2',
            'AI-2',
            '3OC6HSL',
            '3OC12HSL',
            'C4HSL',
            'HSL',
            'AUTOINDUCER',
            'QS',
            'PHEROMONE',
        }
    
    def analyze_topology(self, place) -> float:
        """Analyze topology: quorum signals have characteristic production patterns.
        
        Quorum places typically:
        - Have self-production loops (positive feedback)
        - Are produced by dedicated synthase transitions
        - Accumulate extracellularly
        - Are sensed by regulatory transitions
        
        Args:
            place: Place object to analyze
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Check for positive feedback loops
        # (place influences transitions that produce it)
        has_positive_feedback = False
        
        for arc in self.model.arcs:
            if arc.target == place:  # Transition → Place (production)
                producing_transition = arc.source
                
                # Check if this place also influences the producing transition
                for influence_arc in self.model.arcs:
                    if (influence_arc.source == place and 
                        influence_arc.target == producing_transition):
                        
                        # Found self-production loop
                        has_positive_feedback = True
                        break
        
        if has_positive_feedback:
            return 0.9  # Strong indicator of quorum sensing
        
        # Check for extracellular location (via name or constant accumulation)
        if any(keyword in place.name.lower() for keyword in ['external', 'extra', 'out']):
            return 0.7
        
        # Quorum signals typically have moderate degree
        # (not as high as energy, not as low as specialized metabolites)
        connections = sum(
            1 for arc in self.model.arcs
            if arc.source == place or arc.target == place
        )
        
        if 2 <= connections <= 6:
            return 0.5  # Moderate connectivity is typical
        
        return 0.0
    
    def analyze_dynamics(self, place, rate_functions: List[str]) -> float:
        """Analyze dynamics: quorum signals show accumulation patterns.
        
        Quorum signals typically:
        - Appear in Hill-type regulatory functions
        - Show threshold activation
        - Are produced proportionally to cell density
        
        Args:
            place: Place object
            rate_functions: Rate functions referencing this place
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not rate_functions:
            return 0.0
        
        place_name = place.name
        
        # Check for Hill-type regulation: "AHL^n / (K^n + AHL^n)"
        hill_count = 0
        threshold_count = 0
        
        for rate_func in rate_functions:
            # Hill function pattern
            if (f'{place_name}^' in rate_func or 
                f'{place_name}**' in rate_func or
                f'pow({place_name}' in rate_func):
                hill_count += 1
            
            # Threshold activation: if place > threshold
            if (f'{place_name} >' in rate_func or 
                f'{place_name} <' in rate_func or
                '/ (K' in rate_func):
                threshold_count += 1
        
        # Strong evidence of regulatory use (typical for quorum signals)
        if hill_count >= 1:
            return 1.0
        elif threshold_count >= 1:
            return 0.8
        
        # Weak independence: appears in many rate functions but not as critical metabolite
        if len(rate_functions) >= 3:
            return 0.6
        
        return 0.0
