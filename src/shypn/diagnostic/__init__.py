#!/usr/bin/env python3
"""Diagnostic tools for Petri net analysis.

This module provides diagnostic tools for analyzing Petri net structure
and behavior, including locality detection and analysis.

Locality Concept:
    A locality is a transition-centered neighborhood consisting of its
    connected places via input and/or output arcs.
    
    Locality L(T) = •T ∪ T•  (preset union postset)
    
    Valid Patterns:
    - Normal:   Pn → T → Pm  (n ≥ 1 inputs, m ≥ 1 outputs)
    - Source:   T → Pm       (no inputs, m ≥ 1 outputs) 
    - Sink:     Pn → T       (n ≥ 1 inputs, no outputs)
    - Multiple: T1 → P ← T2  (shared places allowed)
    
    A locality is valid if it has at least ONE connected place.

Example:
    from shypn.diagnostic import LocalityDetector, LocalityInfoWidget
    
    # Detect locality for a transition
    detector = LocalityDetector(model)
    locality = detector.get_locality_for_transition(transition)
    
    if locality.is_valid:
        print(f"{locality.get_summary()}")
    
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
