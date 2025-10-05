#!/usr/bin/env python3
"""Locality Analyzer - Analyze locality properties and behavior.

This module provides analysis tools for locality characteristics,
including token flow, firing patterns, and structural properties.

Example:
    analyzer = LocalityAnalyzer(model)
    analysis = analyzer.analyze_locality(locality)
    
    print(f"Total places: {analysis['place_count']}")
    print(f"Input tokens: {analysis['input_tokens']}")
    print(f"Can fire: {analysis['can_fire']}")
    
    # Get detailed description
    description = analyzer.get_token_flow_description(locality)
    for line in description:
        print(line)
"""

from typing import Dict, List, Any, Tuple
from .locality_detector import Locality, LocalityDetector


class LocalityAnalyzer:
    """Analyzer for locality properties.
    
    Provides methods to analyze locality structure and behavior,
    including token flow patterns, arc weights, and firing potential.
    
    This class performs:
    - Token counting (inputs, outputs, balance)
    - Arc weight calculations
    - Firing potential analysis
    - Token flow descriptions
    
    Attributes:
        model: Reference to PetriNetModel
        detector: LocalityDetector instance for locality detection
    
    Example:
        analyzer = LocalityAnalyzer(model)
        
        # Analyze a locality
        locality = detector.get_locality_for_transition(transition)
        analysis = analyzer.analyze_locality(locality)
        
        print(f"Place count: {analysis['place_count']}")
        print(f"Token balance: {analysis['token_balance']}")
        print(f"Can fire: {analysis['can_fire']}")
        
        # Get detailed flow description
        flow = analyzer.get_token_flow_description(locality)
        print("\n".join(flow))
    """
    
    def __init__(self, model: Any):
        """Initialize analyzer.
        
        Args:
            model: PetriNetModel instance
        """
        self.model = model
        self.detector = LocalityDetector(model)
    
    def analyze_locality(self, locality: Locality) -> Dict[str, Any]:
        """Comprehensive locality analysis.
        
        Performs complete analysis including:
        - Validity check
        - Place and arc counts
        - Token counts (input, output, balance)
        - Arc weight totals
        - Firing potential check
        - Summary text
        
        Args:
            locality: Locality object to analyze
            
        Returns:
            Dict with analysis results containing:
                - is_valid: bool
                - place_count: int
                - input_count: int
                - output_count: int
                - arc_count: int
                - input_tokens: int
                - output_tokens: int
                - token_balance: int (inputs - outputs)
                - total_weight: int
                - can_fire: bool
                - summary: str
        
        Example:
            analysis = analyzer.analyze_locality(locality)
            
            if analysis['is_valid']:
                print(f"Summary: {analysis['summary']}")
                print(f"Tokens: {analysis['input_tokens']} → {analysis['output_tokens']}")
                print(f"Balance: {analysis['token_balance']}")
                print(f"Can fire: {analysis['can_fire']}")
        """
        return {
            'is_valid': locality.is_valid,
            'place_count': locality.place_count,
            'input_count': len(locality.input_places),
            'output_count': len(locality.output_places),
            'arc_count': len(locality.input_arcs) + len(locality.output_arcs),
            'input_tokens': self._count_input_tokens(locality),
            'output_tokens': self._count_output_tokens(locality),
            'token_balance': self._calculate_token_balance(locality),
            'total_weight': self._calculate_total_weight(locality),
            'can_fire': self._check_firing_potential(locality),
            'summary': locality.get_summary()
        }
    
    def _count_input_tokens(self, locality: Locality) -> int:
        """Count total tokens in input places.
        
        Args:
            locality: Locality object
            
        Returns:
            Sum of tokens in all input places
        """
        return sum(place.tokens for place in locality.input_places)
    
    def _count_output_tokens(self, locality: Locality) -> int:
        """Count total tokens in output places.
        
        Args:
            locality: Locality object
            
        Returns:
            Sum of tokens in all output places
        """
        return sum(place.tokens for place in locality.output_places)
    
    def _calculate_token_balance(self, locality: Locality) -> float:
        """Calculate token balance (inputs - outputs).
        
        A positive balance indicates more tokens in input places,
        a negative balance indicates more tokens in output places.
        
        Args:
            locality: Locality object
            
        Returns:
            Token balance (input_tokens - output_tokens)
        """
        return float(self._count_input_tokens(locality) - self._count_output_tokens(locality))
    
    def _calculate_total_weight(self, locality: Locality) -> float:
        """Calculate total arc weight.
        
        Sums the weights of all arcs (input and output) in the locality.
        
        Args:
            locality: Locality object
            
        Returns:
            Sum of all arc weights
        """
        total = 0.0
        for arc in locality.input_arcs + locality.output_arcs:
            total += float(getattr(arc, 'weight', 1))
        return total
    
    def _check_firing_potential(self, locality: Locality) -> bool:
        """Check if transition has potential to fire.
        
        Performs basic firing check:
        - Each input place must have at least as many tokens as the arc weight
        
        Note: This is a simplified check. Full firing rules may include:
        - Guard conditions
        - Inhibitor arcs
        - Priority rules
        
        Args:
            locality: Locality object
            
        Returns:
            True if transition can potentially fire, False otherwise
        """
        # Check if all input places have enough tokens for arc weights
        for arc in locality.input_arcs:
            place = arc.source
            required = getattr(arc, 'weight', 1)
            if place.tokens < required:
                return False
        return True
    
    def get_token_flow_description(self, locality: Locality) -> List[str]:
        """Get detailed token flow description.
        
        Generates human-readable text describing the locality structure
        and token flow, including:
        - Locality name
        - Input flows (place → transition with weights and token counts)
        - Output flows (transition → place with weights and token counts)
        
        Args:
            locality: Locality object
            
        Returns:
            List of strings (lines) describing token flow
            
        Example:
            lines = analyzer.get_token_flow_description(locality)
            for line in lines:
                print(line)
            
            # Output:
            # Locality for T1:
            #
            # Input Flows:
            #   P1 (5 tokens) --[2]--> T1
            #   P2 (3 tokens) --[1]--> T1
            #
            # Output Flows:
            #   T1 --[1]--> P3 (0 tokens)
            #   T1 --[2]--> P4 (1 tokens)
        """
        lines = []
        lines.append(f"Locality for {locality.transition.name}:")
        lines.append("")
        
        # Input flows
        lines.append("Input Flows:")
        if locality.input_arcs:
            for arc in locality.input_arcs:
                place = arc.source
                weight = getattr(arc, 'weight', 1)
                lines.append(f"  {place.name} ({place.tokens} tokens) --[{weight}]--> {locality.transition.name}")
        else:
            lines.append("  (none)")
        
        # Output flows
        lines.append("")
        lines.append("Output Flows:")
        if locality.output_arcs:
            for arc in locality.output_arcs:
                place = arc.target
                weight = getattr(arc, 'weight', 1)
                lines.append(f"  {locality.transition.name} --[{weight}]--> {place.name} ({place.tokens} tokens)")
        else:
            lines.append("  (none)")
        
        return lines
