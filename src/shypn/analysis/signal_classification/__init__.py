#!/usr/bin/env python3
"""Signal Type Classification - Automated detection of signal types in Bio-PNs.

This package implements automated classification of signal places according to
the Extended Bio-PN 13-tuple formalism. Signal types represent different roles
in hierarchical biological information flow:

- ENERGY: Lowest-layer orchestrators (ATP, NADH, energy metabolites)
- SPATIAL: Universal constraints (membrane, compartment, diffusion)
- QUORUM: Weakly independent context (autoinducer accumulation)
- REGULATORY: Decision variables (transcription factors, thresholds)

Usage:
    from shypn.analysis.signal_classification import SignalClassifierManager
    
    classifier = SignalClassifierManager(model)
    classifications = classifier.classify_all_signals()
    
    for place_name, signal_type in classifications.items():
        print(f"{place_name}: {signal_type}")

Architecture:
    - base_classifier.py: Abstract base class for all classifiers
    - energy_classifier.py: ENERGY signal detection
    - spatial_classifier.py: SPATIAL signal detection
    - quorum_classifier.py: QUORUM signal detection
    - regulatory_classifier.py: REGULATORY signal detection
    - classifier_manager.py: Orchestrates all classifiers

See Also:
    - doc/SIGNAL_CLASSIFICATION.md: Detailed documentation
    - tests/signal_classification/: Test suite
"""

from .base_classifier import BaseSignalClassifier
from .energy_classifier import EnergySignalClassifier
from .spatial_classifier import SpatialSignalClassifier
from .quorum_classifier import QuorumSignalClassifier
from .regulatory_classifier import RegulatorySignalClassifier
from .classifier_manager import SignalClassifierManager

__all__ = [
    'BaseSignalClassifier',
    'EnergySignalClassifier',
    'SpatialSignalClassifier',
    'QuorumSignalClassifier',
    'RegulatorySignalClassifier',
    'SignalClassifierManager',
]
