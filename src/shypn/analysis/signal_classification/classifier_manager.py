#!/usr/bin/env python3
"""Signal Classifier Manager - Orchestrates all signal type classifiers.

This module provides the main interface for automated signal classification.
It coordinates the four specialized classifiers (Energy, Spatial, Quorum,
Regulatory) and resolves conflicts when multiple classifiers match.

Usage:
    manager = SignalClassifierManager(model)
    
    # Classify all signal places
    results = manager.classify_all_signals()
    
    # Classify specific place
    signal_type, confidence = manager.classify_place(place)
    
    # Apply classifications to model
    manager.apply_classifications()

Author: Simão Eugénio
Date: December 31, 2025
"""

from typing import Dict, Tuple, Optional, List
import logging

from .base_classifier import BaseSignalClassifier
from .energy_classifier import EnergySignalClassifier
from .spatial_classifier import SpatialSignalClassifier
from .quorum_classifier import QuorumSignalClassifier
from .regulatory_classifier import RegulatorySignalClassifier


class SignalClassifierManager:
    """Manager for automated signal type classification.
    
    Coordinates multiple specialized classifiers and handles conflicts
    when a place matches multiple signal types.
    
    Attributes:
        model: Bio-PN model instance
        classifiers: List of specialized classifiers
        confidence_threshold: Minimum confidence for classification
    """
    
    def __init__(self, model, confidence_threshold: float = 0.5):
        """Initialize classifier manager.
        
        Args:
            model: Bio-PN model with places and transitions
            confidence_threshold: Minimum confidence score (0.0-1.0)
        """
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize all specialized classifiers
        self.classifiers: List[BaseSignalClassifier] = [
            EnergySignalClassifier(model, confidence_threshold),
            SpatialSignalClassifier(model, confidence_threshold),
            QuorumSignalClassifier(model, confidence_threshold),
            RegulatorySignalClassifier(model, confidence_threshold),
        ]
        
        self.logger.info(
            f"Initialized SignalClassifierManager with {len(self.classifiers)} "
            f"classifiers (threshold={confidence_threshold})"
        )
    
    def classify_place(self, place) -> Tuple[Optional[str], float, Dict]:
        """Classify a single place.
        
        Args:
            place: Place object to classify
            
        Returns:
            Tuple of (signal_type, confidence, details)
            - signal_type: 'ENERGY', 'SPATIAL', 'QUORUM', 'REGULATORY', or None
            - confidence: Overall confidence score
            - details: Dict with per-classifier results
        """
        results = {}
        
        # Run all classifiers
        for classifier in self.classifiers:
            signal_type = classifier.get_signal_type()
            is_match, confidence, breakdown = classifier.classify(place)
            
            results[signal_type] = {
                'is_match': is_match,
                'confidence': confidence,
                'breakdown': breakdown,
            }
        
        # Find classifier with highest confidence
        best_match = None
        best_confidence = 0.0
        
        for signal_type, result in results.items():
            if result['is_match'] and result['confidence'] > best_confidence:
                best_match = signal_type
                best_confidence = result['confidence']
        
        # Handle conflicts (multiple matches)
        if best_match:
            matches = [
                st for st, res in results.items()
                if res['is_match']
            ]
            
            if len(matches) > 1:
                self.logger.warning(
                    f"Place '{place.name}' matches multiple signal types: {matches}. "
                    f"Selected '{best_match}' with confidence {best_confidence:.2f}"
                )
        
        return best_match, best_confidence, results
    
    def classify_all_signals(self, 
                             signal_places_only: bool = True) -> Dict[str, Tuple[str, float]]:
        """Classify all places in the model.
        
        Args:
            signal_places_only: If True, only classify places marked as signals
            
        Returns:
            Dict mapping place names to (signal_type, confidence)
        """
        classifications = {}
        
        for place in self.model.places:
            # Skip if not a signal place (unless classifying all)
            if signal_places_only:
                # Check both 'is_signal' and 'is_signal_place' attributes
                is_signal = getattr(place, 'is_signal', False) or getattr(place, 'is_signal_place', False)
                if not is_signal:
                    continue
            
            signal_type, confidence, _ = self.classify_place(place)
            
            if signal_type:
                classifications[place.name] = (signal_type, confidence)
                self.logger.info(
                    f"Classified '{place.name}' as {signal_type} "
                    f"(confidence: {confidence:.2f})"
                )
        
        return classifications
    
    def apply_classifications(self, 
                             classifications: Optional[Dict[str, Tuple[str, float]]] = None,
                             overwrite: bool = False) -> int:
        """Apply signal type classifications to model places.
        
        Args:
            classifications: Dict from classify_all_signals(), or None to recompute
            overwrite: If True, overwrite existing signal_type values
            
        Returns:
            Number of places classified
        """
        if classifications is None:
            classifications = self.classify_all_signals()
        
        count = 0
        
        for place in self.model.places:
            if place.name in classifications:
                signal_type, confidence = classifications[place.name]
                
                # Check if already classified
                existing_type = getattr(place, 'signal_type', None)
                
                if existing_type and not overwrite:
                    self.logger.debug(
                        f"Skipping '{place.name}': already has signal_type='{existing_type}'"
                    )
                    continue
                
                # Apply classification
                place.signal_type = signal_type
                count += 1
                
                self.logger.info(
                    f"Set '{place.name}'.signal_type = '{signal_type}' "
                    f"(confidence: {confidence:.2f})"
                )
        
        self.logger.info(f"Applied {count} signal type classifications")
        return count
    
    def get_classification_report(self) -> str:
        """Generate human-readable classification report.
        
        Returns:
            Formatted string with classification statistics
        """
        classifications = self.classify_all_signals(signal_places_only=False)
        
        # Group by signal type
        by_type = {}
        for place_name, (signal_type, confidence) in classifications.items():
            if signal_type not in by_type:
                by_type[signal_type] = []
            by_type[signal_type].append((place_name, confidence))
        
        # Build report
        lines = [
            "=" * 60,
            "Signal Type Classification Report",
            "=" * 60,
            f"Total places classified: {len(classifications)}",
            "",
        ]
        
        for signal_type in ['ENERGY', 'SPATIAL', 'QUORUM', 'REGULATORY']:
            if signal_type in by_type:
                places = by_type[signal_type]
                lines.append(f"{signal_type} Signals ({len(places)}):")
                
                for place_name, confidence in sorted(places, key=lambda x: -x[1]):
                    lines.append(f"  - {place_name}: {confidence:.2f}")
                
                lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def validate_classifications(self) -> Dict[str, List[str]]:
        """Validate classifications and identify potential issues.
        
        Returns:
            Dict mapping issue types to lists of place names
        """
        issues = {
            'low_confidence': [],
            'no_matches': [],
            'ambiguous': [],
        }
        
        for place in self.model.places:
            if not getattr(place, 'is_signal', False):
                continue
            
            signal_type, confidence, details = self.classify_place(place)
            
            if signal_type is None:
                issues['no_matches'].append(place.name)
            elif confidence < 0.6:
                issues['low_confidence'].append(place.name)
            
            # Check for ambiguity (multiple classifiers with similar scores)
            matches = [
                (st, res['confidence'])
                for st, res in details.items()
                if res['is_match']
            ]
            
            if len(matches) >= 2:
                sorted_matches = sorted(matches, key=lambda x: -x[1])
                if len(sorted_matches) >= 2:
                    best = sorted_matches[0][1]
                    second = sorted_matches[1][1]
                    
                    if best - second < 0.1:  # Very close scores
                        issues['ambiguous'].append(place.name)
        
        return issues
