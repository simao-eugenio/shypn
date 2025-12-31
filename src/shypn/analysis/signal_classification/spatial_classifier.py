#!/usr/bin/env python3
"""Spatial Signal Classifier - Detects SPATIAL signal places.

SPATIAL signals represent compartmental organization and diffusion constraints
that apply universally across conditions. They encode spatial information
rather than temporal dynamics.

Characteristics:
- Names: membrane, compartment, volume, diffusion, gradient
- Topology: Connected to transport/diffusion transitions
- Dynamics: Saturate identically in all conditions (orthogonal constraints)
- Behavior: Universal spatial constraints independent of metabolic state

Author: Simão Eugénio
Date: December 31, 2025
"""

from typing import Set, List
from .base_classifier import BaseSignalClassifier


class SpatialSignalClassifier(BaseSignalClassifier):
    """Classifier for SPATIAL signal places.
    
    Detects places representing spatial organization, compartmentalization,
    and diffusion constraints.
    
    Example:
        classifier = SpatialSignalClassifier(model)
        is_spatial, confidence, breakdown = classifier.classify(membrane_place)
    """
    
    def get_signal_type(self) -> str:
        """Return signal type identifier."""
        return 'SPATIAL'
    
    def get_lexical_patterns(self) -> List[str]:
        """Return regex patterns for spatial-related place names."""
        return [
            r'\bmembrane\b',
            r'\bcompartment\b',
            r'\bvolume\b',
            r'\bdiffusion\b',
            r'\bgradient\b',
            r'\bcytoplasm\b',
            r'\bextracellular\b',
            r'\bperiplasm\b',
            r'\bnucleus\b',
            r'\bmitochondria\b',
            r'\bendoplasmic.*reticulum\b',
            r'\bER\b',
            r'\bgolgi\b',
            r'\blysosome\b',
            r'\bvesicle\b',
            r'\btransport\b',
            r'\blocalization\b',
            r'\bcell.*wall\b',
        ]
    
    def get_biochemical_indicators(self) -> Set[str]:
        """Return spatial/compartmental indicators."""
        return {
            'MEMBRANE',
            'CYTOPLASM',
            'EXTRACELLULAR',
            'PERIPLASM',
            'NUCLEUS',
            'MITOCHONDRIA',
            'ER',
            'GOLGI',
            'VOLUME',
            'SURFACE',
            'COMPARTMENT',
        }
    
    def analyze_topology(self, place) -> float:
        """Analyze topology: spatial places connected to transport transitions.
        
        Spatial places typically:
        - Are involved in transport/diffusion reactions
        - Have moderate connectivity (fewer than energy hubs)
        - May be constant (fixed volume/area)
        
        Args:
            place: Place object to analyze
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Check if place has fixed/constant value
        if hasattr(place, 'tokens') and hasattr(place, 'constant'):
            if getattr(place, 'constant', False):
                return 0.8  # Constant compartment size is strong indicator
        
        # Count transport-related transitions
        transport_related = 0
        
        for arc in self.model.arcs:
            transition = None
            
            if arc.source == place:
                transition = arc.target
            elif arc.target == place:
                transition = arc.source
            
            if transition and hasattr(transition, 'name'):
                trans_name = transition.name.lower()
                
                # Check for transport/diffusion keywords
                if any(keyword in trans_name for keyword in [
                    'transport', 'diffusion', 'import', 'export',
                    'secretion', 'uptake', 'efflux', 'influx'
                ]):
                    transport_related += 1
        
        if transport_related >= 2:
            return 0.9  # Strong spatial signal
        elif transport_related >= 1:
            return 0.6  # Moderate evidence
        
        return 0.0
    
    def analyze_dynamics(self, place, rate_functions: List[str]) -> float:
        """Analyze dynamics: spatial constraints are often constant terms.
        
        Spatial signals typically:
        - Appear as fixed scaling factors (volume normalization)
        - Show up in transport rate equations
        - Are context-independent (same across conditions)
        
        Args:
            place: Place object
            rate_functions: Rate functions referencing this place
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not rate_functions:
            return 0.0
        
        place_name = place.name
        
        # Check for division (normalization): "rate / VOLUME"
        normalization_count = 0
        for rate_func in rate_functions:
            if f'/ {place_name}' in rate_func or f'/{place_name}' in rate_func:
                normalization_count += 1
        
        if normalization_count >= 2:
            return 1.0  # Strong evidence of spatial normalization
        elif normalization_count >= 1:
            return 0.7
        
        # Spatial signals often appear in simple multiplicative form
        # (less complex than regulatory)
        simple_appearance = sum(
            1 for rf in rate_functions
            if place_name in rf and '(' not in rf.split(place_name)[1][:10]
        )
        
        if simple_appearance >= 1:
            return 0.5
        
        return 0.0
