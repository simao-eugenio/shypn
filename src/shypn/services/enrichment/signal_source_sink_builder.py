#!/usr/bin/env python3
"""Signal Source/Sink Network Builder.

Creates minimal source and sink transitions for signal places to maintain
proper signal flow in hierarchical Bio-PN models.

Signal places (Ψ) are consumed by transitions via SignalFlowArcs, so they need:
- Source transitions: Generate signal tokens (signal production/regeneration)
- Sink transitions: Consume excess signal tokens (signal clearance/degradation)

This module provides Phase 3 enrichment for KEGG models after:
- Phase 1: Stoichiometry enrichment (missing compounds/arcs)
- Phase 2: Hill inhibition extraction (inhibitor arcs)
- Phase 3: Signal source/sink network (this module)

Design Principles:
- Minimal network: One source, one sink per signal place
- Clear naming: ATP_source, ATP_sink for easy identification
- Metadata tracking: Mark transitions as source/sink for rendering
- Rate inference: Use physiological ranges for signals

References:
- Signal Hierarchy Theory (Simão 2025)
- doc/signal_hierarchy/SIGNAL_HIERARCHY_THEORY.md
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc


@dataclass
class SignalSourceSinkStats:
    """Statistics for signal source/sink enrichment."""
    signal_places_processed: int = 0
    sources_added: int = 0
    sinks_added: int = 0
    arcs_added: int = 0


class SignalSourceSinkBuilder:
    """Builder for signal source/sink transitions.
    
    Analyzes signal places and creates:
    - Source transitions: Produce signal tokens (for signal regeneration)
    - Sink transitions: Consume signal tokens (for signal clearance)
    
    Example:
        >>> builder = SignalSourceSinkBuilder()
        >>> stats = builder.build_signal_network(document, signal_places)
        >>> print(f"Added {stats.sources_added} sources, {stats.sinks_added} sinks")
    """
    
    def __init__(self):
        """Initialize builder."""
        self.logger = logging.getLogger(__name__)
    
    def build_signal_network(
        self,
        document,
        signal_places: Optional[List[Place]] = None
    ) -> SignalSourceSinkStats:
        """Build source/sink network for all signal places.
        
        Args:
            document: DocumentModel with places, transitions, arcs
            signal_places: List of signal places (if None, auto-detect)
        
        Returns:
            SignalSourceSinkStats with counts
        """
        stats = SignalSourceSinkStats()
        
        # Auto-detect signal places if not provided
        if signal_places is None:
            signal_places = self._detect_signal_places(document)
        
        self.logger.info(f"Building signal network for {len(signal_places)} signal places")
        
        for place in signal_places:
            stats.signal_places_processed += 1
            
            # Check if place has SignalFlowArcs (consuming arcs)
            # Only places with consuming arcs need source/sink
            if not self._has_signal_flow_arcs(document, place):
                self.logger.debug(
                    f"Skipping {place.label or place.name}: Only connected by TestArcs (non-consuming)"
                )
                continue
            
            # Check if already has source/sink
            has_source, has_sink = self._check_existing_source_sink(document, place)
            
            # Add source if needed
            if not has_source:
                source_transition, source_arc = self._create_source(document, place)
                if source_transition and source_arc:
                    stats.sources_added += 1
                    stats.arcs_added += 1
                    self.logger.info(f"Added source for {place.label or place.name}: {source_transition.name}")
            
            # Add sink if needed
            if not has_sink:
                sink_transition, sink_arc = self._create_sink(document, place)
                if sink_transition and sink_arc:
                    stats.sinks_added += 1
                    stats.arcs_added += 1
                    self.logger.info(f"Added sink for {place.label or place.name}: {sink_transition.name}")
        
        self.logger.info(
            f"Signal network complete: {stats.sources_added} sources, "
            f"{stats.sinks_added} sinks, {stats.arcs_added} arcs"
        )
        
        return stats
    
    def _detect_signal_places(self, document) -> List[Place]:
        """Detect all signal places in document.
        
        Args:
            document: DocumentModel
        
        Returns:
            List of signal places
        """
        signal_places = []
        
        for place in document.places:
            if getattr(place, 'is_signal_place', False):
                signal_places.append(place)
        
        return signal_places
    
    def _has_signal_flow_arcs(self, document, place: Place) -> bool:
        """Check if place has any SignalFlowArcs (consuming arcs).
        
        Signal places connected only by TestArcs don't consume tokens,
        so they don't need source/sink transitions.
        
        Args:
            document: DocumentModel
            place: Signal place to check
        
        Returns:
            True if has at least one SignalFlowArc, False otherwise
        """
        from shypn.netobjs.signal_flow_arc import SignalFlowArc
        
        for arc in document.arcs:
            # Check if arc connects to this place
            if arc.source == place or arc.target == place:
                # Check if it's a SignalFlowArc (consuming)
                if isinstance(arc, SignalFlowArc):
                    return True
        
        return False
    
    def _check_existing_source_sink(
        self,
        document,
        place: Place
    ) -> Tuple[bool, bool]:
        """Check if place already has source/sink transitions.
        
        Args:
            document: DocumentModel
            place: Signal place to check
        
        Returns:
            Tuple of (has_source, has_sink)
        """
        has_source = False
        has_sink = False
        
        # Check incoming arcs (from transitions = sources)
        for arc in document.arcs:
            if arc.target == place:
                # Transition → Place (potential source)
                source_obj = arc.source
                if isinstance(source_obj, Transition):
                    # Check if marked as source
                    if getattr(source_obj, 'is_source', False):
                        has_source = True
                    # Or check if has no inputs (pure source)
                    elif not self._has_input_arcs(document, source_obj):
                        has_source = True
        
        # Check outgoing arcs (to transitions = sinks)
        for arc in document.arcs:
            if arc.source == place:
                # Place → Transition (potential sink)
                target_obj = arc.target
                if isinstance(target_obj, Transition):
                    # Check if marked as sink
                    if getattr(target_obj, 'is_sink', False):
                        has_sink = True
                    # Or check if has no outputs (pure sink)
                    elif not self._has_output_arcs(document, target_obj):
                        has_sink = True
        
        return has_source, has_sink
    
    def _has_input_arcs(self, document, transition: Transition) -> bool:
        """Check if transition has input arcs (Place → Transition).
        
        Args:
            document: DocumentModel
            transition: Transition to check
        
        Returns:
            True if has at least one input arc
        """
        for arc in document.arcs:
            if arc.target == transition and isinstance(arc.source, Place):
                return True
        return False
    
    def _has_output_arcs(self, document, transition: Transition) -> bool:
        """Check if transition has output arcs (Transition → Place).
        
        Args:
            document: DocumentModel
            transition: Transition to check
        
        Returns:
            True if has at least one output arc
        """
        for arc in document.arcs:
            if arc.source == transition and isinstance(arc.target, Place):
                return True
        return False
    
    def _create_source(
        self,
        document,
        place: Place
    ) -> Tuple[Optional[Transition], Optional[Arc]]:
        """Create source transition for signal place.
        
        Source transition:
        - Produces signal tokens
        - No input arcs (pure source)
        - Marked with is_source=True
        - Named: {place_label}_source
        
        Args:
            document: DocumentModel
            place: Signal place
        
        Returns:
            Tuple of (transition, arc) or (None, None) on failure
        """
        try:
            # Generate unique IDs
            transition_id = document.document_controller.id_manager.generate_transition_id()
            arc_id = document.document_controller.id_manager.generate_arc_id()
            
            # Create transition name and label
            place_label = place.label or place.name
            transition_name = f"{place_label}_source"
            
            # Position: Above and to the left of the signal place
            offset_x = -60
            offset_y = -60
            transition_x = place.x + offset_x
            transition_y = place.y + offset_y
            
            # Create source transition
            transition = Transition(
                x=transition_x,
                y=transition_y,
                id=transition_id,
                name=transition_id,
                label=transition_name,
                width=50,
                height=20
            )
            
            # Mark as source
            transition.is_source = True
            transition.behavior_type = 'stochastic'  # Poisson process for signal generation
            
            # Estimate rate based on signal type
            rate = self._estimate_source_rate(place)
            if hasattr(transition, 'properties') and transition.properties is None:
                transition.properties = {}
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['rate'] = rate
            
            # Add metadata
            if not hasattr(transition, 'metadata'):
                transition.metadata = {}
            transition.metadata['signal_source_for'] = place.id
            transition.metadata['generated_by'] = 'signal_source_sink_builder'
            transition.metadata['purpose'] = 'signal_regeneration'
            
            # Create arc: Transition → Place (use SignalFlowArc for signal places)
            from shypn.netobjs.signal_flow_arc import SignalFlowArc
            arc = SignalFlowArc(
                source=transition,
                target=place,
                id=arc_id,
                name=arc_id,
                weight=1.0
            )
            
            # Add to document (append directly to lists)
            document.transitions.append(transition)
            document.arcs.append(arc)
            
            return transition, arc
            
        except Exception as e:
            self.logger.error(f"Failed to create source for {place.name}: {e}")
            return None, None
    
    def _create_sink(
        self,
        document,
        place: Place
    ) -> Tuple[Optional[Transition], Optional[Arc]]:
        """Create sink transition for signal place.
        
        Sink transition:
        - Consumes signal tokens
        - No output arcs (pure sink)
        - Marked with is_sink=True
        - Named: {place_label}_sink
        
        Args:
            document: DocumentModel
            place: Signal place
        
        Returns:
            Tuple of (transition, arc) or (None, None) on failure
        """
        try:
            # Generate unique IDs
            transition_id = document.document_controller.id_manager.generate_transition_id()
            arc_id = document.document_controller.id_manager.generate_arc_id()
            
            # Create transition name and label
            place_label = place.label or place.name
            transition_name = f"{place_label}_sink"
            
            # Position: Below and to the right of the signal place
            offset_x = 60
            offset_y = 60
            transition_x = place.x + offset_x
            transition_y = place.y + offset_y
            
            # Create sink transition
            transition = Transition(
                x=transition_x,
                y=transition_y,
                id=transition_id,
                name=transition_id,
                label=transition_name,
                width=50,
                height=20
            )
            
            # Mark as sink
            transition.is_sink = True
            transition.behavior_type = 'stochastic'  # First-order degradation
            
            # Estimate rate based on signal type
            rate = self._estimate_sink_rate(place)
            if hasattr(transition, 'properties') and transition.properties is None:
                transition.properties = {}
            if not hasattr(transition, 'properties'):
                transition.properties = {}
            transition.properties['rate'] = rate
            
            # Add metadata
            if not hasattr(transition, 'metadata'):
                transition.metadata = {}
            transition.metadata['signal_sink_for'] = place.id
            transition.metadata['generated_by'] = 'signal_source_sink_builder'
            transition.metadata['purpose'] = 'signal_clearance'
            
            # Create arc: Place → Transition (use SignalFlowArc since it's a signal place)
            from shypn.netobjs.signal_flow_arc import SignalFlowArc
            arc = SignalFlowArc(
                source=place,
                target=transition,
                id=arc_id,
                name=arc_id,
                weight=1.0
            )
            
            # Add to document (append directly to lists)
            document.transitions.append(transition)
            document.arcs.append(arc)
            
            return transition, arc
            
        except Exception as e:
            self.logger.error(f"Failed to create sink for {place.name}: {e}")
            return None, None
    
    def _estimate_source_rate(self, place: Place) -> float:
        """Estimate source rate based on signal type.
        
        Args:
            place: Signal place
        
        Returns:
            Estimated rate constant
        """
        # Check signal type
        signal_type = getattr(place, 'signal_type', None)
        
        # Energy signals (ATP, NADH, etc.) - fast regeneration
        if signal_type and 'energy' in str(signal_type).lower():
            return 1.0  # High rate for energy metabolites
        
        # Regulatory signals - moderate
        if signal_type and 'regulatory' in str(signal_type).lower():
            return 0.5
        
        # Quorum sensing - slow
        if signal_type and 'quorum' in str(signal_type).lower():
            return 0.1
        
        # Default: moderate rate
        return 0.5
    
    def _estimate_sink_rate(self, place: Place) -> float:
        """Estimate sink rate based on signal type.
        
        Args:
            place: Signal place
        
        Returns:
            Estimated rate constant
        """
        # Check signal type
        signal_type = getattr(place, 'signal_type', None)
        
        # Energy signals - moderate clearance (recycled)
        if signal_type and 'energy' in str(signal_type).lower():
            return 0.5
        
        # Regulatory signals - fast clearance (active degradation)
        if signal_type and 'regulatory' in str(signal_type).lower():
            return 0.8
        
        # Quorum sensing - slow clearance (diffusion)
        if signal_type and 'quorum' in str(signal_type).lower():
            return 0.2
        
        # Default: moderate rate
        return 0.5
