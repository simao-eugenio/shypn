#!/usr/bin/env python3
"""Diagnostic tools for Petri net analysis.

This module provides diagnostic tools for analyzing Petri net structure
and behavior, including locality detection and analysis.

Locality Concept:
    A locality represents a Place-Transition-Place pattern in a Petri net,
    consisting of a central transition with its connected input and output places.
    This concept is useful for analyzing independent subsystems and token flow.

Example:
    from shypn.diagnostic import LocalityDetector, LocalityInfoWidget
    
    # Detect locality for a transition
    detector = LocalityDetector(model)
    locality = detector.get_locality_for_transition(transition)
    
    # Display in UI
    widget = LocalityInfoWidget(model)
    widget.set_transition(transition)
"""

from .locality_detector import LocalityDetector, Locality
from .locality_analyzer import LocalityAnalyzer
from .locality_info_widget import LocalityInfoWidget
from .locality_runtime import LocalityRuntimeAnalyzer

__all__ = [
    'LocalityDetector',
    'Locality',
    'LocalityAnalyzer',
    'LocalityInfoWidget',
    'LocalityRuntimeAnalyzer',
]
