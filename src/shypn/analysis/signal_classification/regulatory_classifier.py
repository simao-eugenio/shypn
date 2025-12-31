#!/usr/bin/env python3
"""Regulatory Signal Classifier - Detects REGULATORY signal places.

REGULATORY signals are upper-layer decision variables (transcription factors,
signaling proteins) that integrate constraints from lower layers (energy,
spatial, quorum) and exhibit threshold behavior for ON/OFF decisions.

Characteristics:
- Names: transcription factor, TF, protein, kinase, repressor, activator
- Topology: Affected by many signals, control few targets (convergent)
- Dynamics: Hill functions, threshold activation, ultrasensitivity
- Behavior: Binary decision-making with large ON/OFF ratios

Author: Simão Eugénio
Date: December 31, 2025
"""

from typing import Set, List
from .base_classifier import BaseSignalClassifier


class RegulatorySignalClassifier(BaseSignalClassifier):
    """Classifier for REGULATORY signal places.
    
    Detects places representing regulatory decision variables that
    integrate multiple signals and exhibit threshold behavior.
    
    Example:
        classifier = RegulatorySignalClassifier(model)
        is_regulatory, confidence, breakdown = classifier.classify(tf_place)
    """
    
    def get_signal_type(self) -> str:
        """Return signal type identifier."""
        return 'REGULATORY'
    
    def get_lexical_patterns(self) -> List[str]:
        """Return regex patterns for regulatory-related place names."""
        return [
            r'\bTF\b',
            r'\btranscription.*factor\b',
            r'\bactivator\b',
            r'\brepressor\b',
            r'\bkinase\b',
            r'\bphosphatase\b',
            r'\bsignal.*protein\b',
            r'\bregulator\b',
            r'\bsensor\b',
            r'\breceptor\b',
            r'\bresponse.*regulator\b',
            r'\bLuxR\b',
            r'\bLuxI\b',
            r'\bCRP\b',
            r'\bFNR\b',
            r'\bArcA\b',
            r'\bLacI\b',
            r'\bp53\b',
            r'\bNF-?kB\b',
        ]
    
    def get_biochemical_indicators(self) -> Set[str]:
        """Return regulatory protein/TF names."""
        return {
            'TF',
            'LUXR',
            'LUXI',
            'CRP',
            'FNR',
            'ARCA',
            'LACI',
            'P53',
            'NFKB',
            'ACTIVATOR',
            'REPRESSOR',
            'KINASE',
            'PHOSPHATASE',
        }
    
    def analyze_topology(self, place) -> float:
        """Analyze topology: regulatory places show convergent integration.
        
        Regulatory places typically:
        - Are influenced by multiple upstream signals (high in-degree)
        - Control few downstream targets (low out-degree)
        - Serve as decision points (convergent topology)
        
        Args:
            place: Place object to analyze
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Count how many transitions this place influences
        influences_count = 0
        # Count how many transitions affect this place
        influenced_by_count = 0
        
        for arc in self.model.arcs:
            if arc.source == place:
                # Place influences transition
                influences_count += 1
            elif arc.target == place:
                # Transition affects place
                influenced_by_count += 1
        
        # Regulatory topology: high in-degree, moderate out-degree
        if influenced_by_count >= 3 and 1 <= influences_count <= 5:
            # Strong convergent pattern
            return 1.0
        elif influenced_by_count >= 2 and influences_count >= 1:
            # Moderate convergent pattern
            return 0.7
        
        # Check for test/inhibitor arcs (regulatory function)
        regulatory_arcs = 0
        for arc in self.model.arcs:
            if arc.source == place:
                if hasattr(arc, 'arc_type') and arc.arc_type in ['test', 'inhibitor']:
                    regulatory_arcs += 1
        
        if regulatory_arcs >= 2:
            return 0.8  # Strong regulatory role
        elif regulatory_arcs >= 1:
            return 0.5
        
        return 0.0
    
    def analyze_dynamics(self, place, rate_functions: List[str]) -> float:
        """Analyze dynamics: regulatory places exhibit threshold behavior.
        
        Regulatory signals typically:
        - Use Hill functions (cooperativity, ultrasensitivity)
        - Show steep activation curves
        - Have high Hill coefficients (n >= 2)
        - Appear in logical combinations (AND/OR gates)
        
        Args:
            place: Place object
            rate_functions: Rate functions referencing this place
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not rate_functions:
            return 0.0
        
        place_name = place.name
        
        hill_coefficient_count = 0
        steep_threshold_count = 0
        logical_gate_count = 0
        
        for rate_func in rate_functions:
            # Hill function with coefficient: "TF^2", "TF**3", "pow(TF, 4)"
            if f'{place_name}^' in rate_func or f'{place_name}**' in rate_func:
                # Extract exponent
                import re
                match = re.search(rf'{place_name}\^?(\*\*)?(\d+)', rate_func)
                if match:
                    exponent = int(match.group(2))
                    if exponent >= 2:
                        hill_coefficient_count += 1
            
            # Steep threshold: division by Michaelis constant
            if f'{place_name} / (' in rate_func and '+ ' in rate_func:
                steep_threshold_count += 1
            
            # Logical combinations: "*" (AND) or "+" (OR) with other signals
            if ' * ' in rate_func and place_name in rate_func:
                # Check if combined with other places
                other_places = self._extract_place_references(rate_func)
                if len(other_places) >= 2:
                    logical_gate_count += 1
        
        # Score based on regulatory patterns
        if hill_coefficient_count >= 1:
            return 1.0  # Strong evidence (ultrasensitivity)
        elif steep_threshold_count >= 2:
            return 0.9  # Multiple threshold activations
        elif logical_gate_count >= 1:
            return 0.8  # Signal integration
        elif steep_threshold_count >= 1:
            return 0.6  # Single threshold
        
        return 0.0
