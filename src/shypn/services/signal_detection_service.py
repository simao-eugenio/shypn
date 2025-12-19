#!/usr/bin/env python3
"""Signal Place Detection Service.

Service for identifying signal place candidates in Petri net models.

This service supports both:
- SBML auto-import (detect signals from modifier patterns)
- Manual/interactive creation (suggest signal candidates in user models)

Architecture follows SBMLKineticsIntegrationService pattern:
- Object-oriented: Works with Place/Transition objects directly
- Strategy pattern: Multiple detection heuristics
- Non-destructive: Suggests candidates, doesn't force conversion
- Thin service layer: Delegates to detection algorithms

Design Principles:
- Object references (not IDs)
- Confidence scoring for suggestions
- Configurable detection strategies
- Separation of concerns: Service orchestrates, algorithms detect
"""

from typing import List, Dict, Tuple, Set, Optional
from enum import Enum
import logging

from shypn.netobjs.place import Place, SignalType
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc


class DetectionStrategy(Enum):
    """Signal detection strategies."""
    MODIFIER_ONLY = "modifier_only"      # Places with no arc connections (highest confidence)
    ENERGY_METABOLITE = "energy"         # ATP, ADP, NADH, etc.
    REGULATORY_FACTOR = "regulatory"     # Transcription factors, signaling proteins
    SPATIAL_MARKER = "spatial"           # Compartment-specific markers
    EXISTING_SIGNAL_REF = "signal_ref"   # Already referenced in transition.signal_places


class SignalDetectionService:
    """Service for detecting signal place candidates.
    
    Uses multiple heuristic strategies to identify places that should be
    converted to signal places (Ψ) for modular architecture.
    
    Supports both SBML auto-detection and manual model analysis.
    """
    
    def __init__(self):
        """Initialize the service."""
        self.logger = logging.getLogger(__name__)
    
    def detect_signals(
        self,
        places: List[Place],
        transitions: List[Transition],
        arcs: List[Arc],
        strategies: Optional[List[DetectionStrategy]] = None
    ) -> Dict[Place, Tuple[SignalType, float]]:
        """Detect signal place candidates using multiple strategies.
        
        Args:
            places: List of Place objects to analyze
            transitions: List of Transition objects (for context)
            arcs: List of Arc objects (to detect connectivity)
            strategies: Detection strategies to use (None = all)
        
        Returns:
            Dict mapping Place → (suggested SignalType, confidence 0-1)
            
        Note:
            Higher confidence scores override lower ones for same place.
            Confidence interpretation:
            - 0.95+: Very high (modifier-only, explicit signal refs)
            - 0.80+: High (energy metabolites)
            - 0.70+: Medium (regulatory factors)
            - 0.60+: Low (spatial markers)
        """
        if strategies is None:
            strategies = list(DetectionStrategy)
        
        candidates: Dict[Place, Tuple[SignalType, float]] = {}
        
        # Strategy 1: Modifier-only (highest confidence)
        if DetectionStrategy.MODIFIER_ONLY in strategies:
            modifier_only = self._detect_modifier_only(places, arcs)
            for place in modifier_only:
                # Default to QUORUM for modifier-only (most common case)
                candidates[place] = (SignalType.QUORUM, 0.95)
                self.logger.debug(f"Detected modifier-only signal: {place.name}")
        
        # Strategy 2: Existing signal references (highest confidence)
        if DetectionStrategy.EXISTING_SIGNAL_REF in strategies:
            signal_refs = self._detect_existing_signal_refs(places, transitions)
            for place in signal_refs:
                if place not in candidates:  # Don't override modifier-only
                    candidates[place] = (SignalType.REGULATORY, 0.95)
                    self.logger.debug(f"Detected existing signal ref: {place.name}")
        
        # Strategy 3: Energy metabolites
        if DetectionStrategy.ENERGY_METABOLITE in strategies:
            energy_places = self._detect_energy_metabolites(places)
            for place in energy_places:
                if place not in candidates:  # Don't override higher confidence
                    candidates[place] = (SignalType.ENERGY, 0.80)
                    self.logger.debug(f"Detected energy metabolite: {place.name}")
        
        # Strategy 4: Regulatory factors
        if DetectionStrategy.REGULATORY_FACTOR in strategies:
            regulatory = self._detect_regulatory_factors(places)
            for place in regulatory:
                if place not in candidates:
                    candidates[place] = (SignalType.REGULATORY, 0.70)
                    self.logger.debug(f"Detected regulatory factor: {place.name}")
        
        # Strategy 5: Spatial markers (lowest confidence)
        if DetectionStrategy.SPATIAL_MARKER in strategies:
            spatial = self._detect_spatial_markers(places)
            for place in spatial:
                if place not in candidates:
                    candidates[place] = (SignalType.SPATIAL, 0.60)
                    self.logger.debug(f"Detected spatial marker: {place.name}")
        
        self.logger.info(
            f"Signal detection complete: {len(candidates)} candidates found "
            f"from {len(places)} places"
        )
        
        return candidates
    
    def _detect_modifier_only(self, places: List[Place], arcs: List[Arc]) -> List[Place]:
        """Detect places with no arc connections (modifier-only pattern).
        
        These are places that influence reactions (via rate formulas) but
        don't have direct arc connections. Classic signal place pattern.
        
        Args:
            places: List of Place objects
            arcs: List of Arc objects
        
        Returns:
            List of places with no arc connections
        """
        # Build set of places that have at least one arc connection
        places_with_arcs: Set[Place] = set()
        
        for arc in arcs:
            # Check source
            if isinstance(arc.source, Place):
                places_with_arcs.add(arc.source)
            # Check target
            if isinstance(arc.target, Place):
                places_with_arcs.add(arc.target)
        
        # Places without arcs are modifier-only candidates
        modifier_only = [p for p in places if p not in places_with_arcs]
        
        return modifier_only
    
    def _detect_existing_signal_refs(
        self,
        places: List[Place],
        transitions: List[Transition]
    ) -> List[Place]:
        """Detect places already referenced in transition.signal_places.
        
        These are explicitly marked as signals in the formalism.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
        
        Returns:
            List of places referenced as signals
        """
        # Build place ID → Place object lookup
        place_by_id = {p.id: p for p in places}
        
        # Find all places referenced in signal_places lists
        signal_place_ids: Set[str] = set()
        for transition in transitions:
            if hasattr(transition, 'signal_places') and transition.signal_places:
                signal_place_ids.update(transition.signal_places)
        
        # Convert IDs back to Place objects
        signal_places = []
        for place_id in signal_place_ids:
            if place_id in place_by_id:
                signal_places.append(place_by_id[place_id])
        
        return signal_places
    
    def _detect_energy_metabolites(self, places: List[Place]) -> List[Place]:
        """Detect energy metabolites by name pattern matching.
        
        Common energy currencies: ATP, ADP, AMP, GTP, NADH, NADPH, FADH2
        
        Args:
            places: List of Place objects
        
        Returns:
            List of places matching energy metabolite patterns
        """
        # Energy metabolite keywords (uppercase for case-insensitive matching)
        energy_keywords = [
            'ATP', 'ADP', 'AMP', 'cAMP',
            'GTP', 'GDP', 'GMP', 'cGMP',
            'NADH', 'NAD+', 'NAD', 'NADPH', 'NADP+', 'NADP',
            'FADH2', 'FADH', 'FAD',
            'CoA', 'Coenzyme A',
            'Pi', 'PPi', 'Phosphate'
        ]
        
        energy_places = []
        for place in places:
            # Check label (user-visible name)
            label_upper = place.label.upper()
            if any(kw in label_upper for kw in energy_keywords):
                energy_places.append(place)
                continue
            
            # Check name (system identifier)
            name_upper = place.name.upper()
            if any(kw in name_upper for kw in energy_keywords):
                energy_places.append(place)
        
        return energy_places
    
    def _detect_regulatory_factors(self, places: List[Place]) -> List[Place]:
        """Detect regulatory factors by name pattern matching.
        
        Transcription factors, signaling proteins, hormones, etc.
        
        Args:
            places: List of Place objects
        
        Returns:
            List of places matching regulatory factor patterns
        """
        # Regulatory factor keywords
        regulatory_keywords = [
            'TF', 'transcription factor',
            'kinase', 'phosphatase',
            'activator', 'repressor', 'inhibitor',
            'hormone', 'cytokine', 'growth factor',
            'receptor', 'ligand',
            'cAMP', 'cGMP',  # Secondary messengers
            'Ca2+', 'calcium'  # Calcium signaling
        ]
        
        regulatory_places = []
        for place in places:
            label_lower = place.label.lower()
            name_lower = place.name.lower()
            
            # Check both label and name
            if any(kw.lower() in label_lower or kw.lower() in name_lower 
                   for kw in regulatory_keywords):
                regulatory_places.append(place)
        
        return regulatory_places
    
    def _detect_spatial_markers(self, places: List[Place]) -> List[Place]:
        """Detect spatial/compartment markers.
        
        Places indicating location or compartment identity.
        
        Args:
            places: List of Place objects
        
        Returns:
            List of places matching spatial marker patterns
        """
        # Spatial/compartment keywords
        spatial_keywords = [
            'location', 'position', 'compartment',
            'cytoplasm', 'nucleus', 'mitochondria', 'membrane',
            'extracellular', 'intracellular',
            'marker', 'flag'
        ]
        
        spatial_places = []
        for place in places:
            label_lower = place.label.lower()
            name_lower = place.name.lower()
            
            if any(kw in label_lower or kw in name_lower for kw in spatial_keywords):
                spatial_places.append(place)
        
        return spatial_places
    
    def apply_signal_suggestions(
        self,
        suggestions: Dict[Place, Tuple[SignalType, float]],
        confidence_threshold: float = 0.75,
        auto_apply: bool = False
    ) -> int:
        """Apply signal type suggestions to places.
        
        Args:
            suggestions: Dict from detect_signals() output
            confidence_threshold: Minimum confidence to apply (0-1)
            auto_apply: If True, automatically set is_signal_place=True
        
        Returns:
            Number of places modified
            
        Note:
            If auto_apply=False, only sets signal_type (for review).
            If auto_apply=True, also sets is_signal_place=True.
        """
        applied_count = 0
        
        for place, (signal_type, confidence) in suggestions.items():
            if confidence >= confidence_threshold:
                place.signal_type = signal_type
                
                if auto_apply:
                    place.is_signal_place = True
                
                applied_count += 1
                self.logger.info(
                    f"Applied signal type {signal_type.value} to {place.name} "
                    f"(confidence: {confidence:.2f})"
                )
        
        return applied_count
    
    def get_detection_report(
        self,
        suggestions: Dict[Place, Tuple[SignalType, float]]
    ) -> str:
        """Generate human-readable detection report.
        
        Args:
            suggestions: Dict from detect_signals() output
        
        Returns:
            Formatted text report
        """
        if not suggestions:
            return "No signal place candidates detected."
        
        # Group by signal type
        by_type: Dict[SignalType, List[Tuple[Place, float]]] = {}
        for place, (signal_type, confidence) in suggestions.items():
            if signal_type not in by_type:
                by_type[signal_type] = []
            by_type[signal_type].append((place, confidence))
        
        # Build report
        lines = [f"Signal Place Detection Report ({len(suggestions)} candidates)"]
        lines.append("=" * 60)
        
        for signal_type in SignalType:
            if signal_type in by_type:
                places_conf = by_type[signal_type]
                places_conf.sort(key=lambda x: x[1], reverse=True)  # Sort by confidence
                
                lines.append(f"\n{signal_type.value.upper()} ({len(places_conf)} places):")
                for place, confidence in places_conf:
                    lines.append(f"  - {place.name} ({place.label}): {confidence:.2%}")
        
        return "\n".join(lines)
