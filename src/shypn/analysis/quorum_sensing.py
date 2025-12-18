#!/usr/bin/env python3
"""Quorum Sensing Detection - Automatic signal place identification.

This module implements signal place detection for the 13-tuple Bio-PN formalism.
Signal places (Ψ: T → 2^P) are non-local dependencies in rate functions that
represent environmental sensing or quorum sensing behavior.

Example:
    rate = "2.0 * AHL / (10 + AHL)"  # AHL not connected by arc → signal place
    
Mathematical Definition:
    Ψ(t) = ReferencedPlaces(Φ(t)) \ (•t ∪ t• ∪ Σ(t))
    
    Where:
    - •t: Input places (consumed)
    - t•: Output places (produced)
    - Σ(t): Regulatory places (test/inhibitor arcs)
    - Ψ(t): Signal places (sensed, non-local) [NEW in 13-tuple]
"""

import re
import logging
from typing import Set, Dict, List


class QuorumSensingDetector:
    """Detector for signal places in rate formulas (quorum sensing)."""
    
    # Math functions and constants to exclude from place detection
    MATH_KEYWORDS = {
        'min', 'max', 'abs', 'exp', 'log', 'log10', 'log2', 'sqrt', 'pow',
        'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
        'asin', 'acos', 'atan', 'atan2',
        'ceil', 'floor', 'round', 'trunc',
        'pi', 'e', 'inf', 'nan',
        'time', 't', 'tau',
        'True', 'False', 'None',
        'and', 'or', 'not', 'in', 'is',
        'if', 'else', 'elif', 'for', 'while',
        'np', 'numpy', 'math'
    }
    
    def __init__(self, model):
        """Initialize detector with model context.
        
        Args:
            model: Model instance with places and arcs
        """
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def detect_signal_places(self, transition, rate_expr: str) -> Set[str]:
        """Detect signal places from rate expression.
        
        Computes: Ψ(t) = Referenced \ (•t ∪ t• ∪ Σ(t))
        
        Args:
            transition: Transition object
            rate_expr: Rate function expression string
        
        Returns:
            set: Place IDs that are signal dependencies (quorum sensing)
        """
        # Extract place references from formula
        referenced_places = self._extract_place_references(rate_expr)
        
        # Get local places (connected by arcs)
        local_places = self._get_local_places(transition)
        
        # Get regulatory places (test/inhibitor arcs)
        regulatory_places = self._get_regulatory_places(transition)
        
        # Signal places = referenced - (local + regulatory)
        signal_places = referenced_places - local_places - regulatory_places
        
        if signal_places:
            self.logger.info(
                f"Detected {len(signal_places)} signal place(s) for transition '{transition.name}': "
                f"{signal_places} (quorum sensing / environmental sensing)"
            )
            
            # Validate signal places exist in model
            self._validate_signal_places(signal_places, transition.name, rate_expr)
        
        return signal_places
    
    def _extract_place_references(self, rate_expr: str) -> Set[str]:
        """Extract place references from rate expression.
        
        Uses regex to find identifiers that match place IDs or names.
        
        Args:
            rate_expr: Rate function expression string
        
        Returns:
            set: Place IDs/names referenced in expression
        """
        # Find all identifiers in formula (alphanumeric + underscore)
        identifiers = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b', rate_expr))
        
        # Remove math functions and constants
        identifiers -= self.MATH_KEYWORDS
        
        # Get places that exist in model
        referenced_places = set()
        if hasattr(self.model, 'places'):
            model_place_ids = set()
            model_place_names = set()
            
            places_iter = (self.model.places.values() if isinstance(self.model.places, dict)
                          else self.model.places)
            
            for place in places_iter:
                if hasattr(place, 'id'):
                    model_place_ids.add(place.id)
                if hasattr(place, 'name') and place.name:
                    model_place_names.add(place.name)
            
            # Check which identifiers are actual places
            for ident in identifiers:
                if ident in model_place_ids or ident in model_place_names:
                    # Find the place object and get its ID
                    for place in places_iter:
                        if (hasattr(place, 'id') and place.id == ident) or \
                           (hasattr(place, 'name') and place.name == ident):
                            referenced_places.add(place.id)
                            break
        
        return referenced_places
    
    def _get_local_places(self, transition) -> Set[str]:
        """Get local places (connected by input/output arcs).
        
        Args:
            transition: Transition object
        
        Returns:
            set: Place IDs connected by arcs (•t ∪ t•)
        """
        local_places = set()
        
        # Get arcs from model
        if not hasattr(self.model, 'arcs'):
            return local_places
        
        arcs_iter = (self.model.arcs.values() if isinstance(self.model.arcs, dict)
                    else self.model.arcs)
        
        for arc in arcs_iter:
            # Input arc: place → transition
            if hasattr(arc, 'target') and arc.target == transition.id:
                if hasattr(arc, 'source'):
                    local_places.add(arc.source)
            
            # Output arc: transition → place
            elif hasattr(arc, 'source') and arc.source == transition.id:
                if hasattr(arc, 'target'):
                    local_places.add(arc.target)
        
        return local_places
    
    def _get_regulatory_places(self, transition) -> Set[str]:
        """Get regulatory places (test/inhibitor arcs).
        
        Args:
            transition: Transition object
        
        Returns:
            set: Place IDs in Σ(t) (regulatory structure)
        """
        regulatory_places = set()
        
        # Get inhibitor arcs from model
        if not hasattr(self.model, 'arcs'):
            return regulatory_places
        
        arcs_iter = (self.model.arcs.values() if isinstance(self.model.arcs, dict)
                    else self.model.arcs)
        
        for arc in arcs_iter:
            # Check if inhibitor/test arc targeting this transition
            if hasattr(arc, 'target') and arc.target == transition.id:
                if hasattr(arc, 'arc_type') and arc.arc_type in ['inhibitor', 'test']:
                    if hasattr(arc, 'source'):
                        regulatory_places.add(arc.source)
        
        return regulatory_places
    
    def _validate_signal_places(self, signal_places: Set[str], 
                                transition_name: str, rate_expr: str):
        """Validate that signal places exist in model.
        
        Args:
            signal_places: Set of place IDs
            transition_name: Name of transition for error messages
            rate_expr: Rate expression for error messages
        """
        if not hasattr(self.model, 'places'):
            return
        
        existing_place_ids = set()
        places_iter = (self.model.places.values() if isinstance(self.model.places, dict)
                      else self.model.places)
        
        for place in places_iter:
            if hasattr(place, 'id'):
                existing_place_ids.add(place.id)
        
        # Check for non-existent signal places
        for signal_id in signal_places:
            if signal_id not in existing_place_ids:
                self.logger.error(
                    f"Transition '{transition_name}' references non-existent signal place '{signal_id}' "
                    f"in rate function: {rate_expr[:80]}..."
                )


def detect_and_annotate_signal_places(model):
    """Detect signal places for all transitions in model.
    
    Updates transition.signal_places and transition.is_environment_aware
    for all transitions with rate formulas.
    
    Args:
        model: Model instance with transitions and places
    
    Returns:
        dict: {transition_id: set(signal_place_ids), ...}
    """
    detector = QuorumSensingDetector(model)
    signal_map = {}
    
    if not hasattr(model, 'transitions'):
        return signal_map
    
    transitions_iter = (model.transitions.values() if isinstance(model.transitions, dict)
                       else model.transitions)
    
    for transition in transitions_iter:
        # Check if transition has rate formula
        rate_expr = None
        
        # Check properties dict
        if hasattr(transition, 'properties') and transition.properties:
            rate_expr = transition.properties.get('rate_function')
        
        # Check rate_function attribute
        if not rate_expr and hasattr(transition, 'rate_function'):
            rate_expr = transition.rate_function
        
        if rate_expr and isinstance(rate_expr, str):
            # Detect signal places
            signal_places = detector.detect_signal_places(transition, rate_expr)
            
            if signal_places:
                # Annotate transition
                transition.signal_places = list(signal_places)
                transition.is_environment_aware = True
                signal_map[transition.id] = signal_places
        else:
            # No rate formula: no signal places
            transition.signal_places = []
            transition.is_environment_aware = False
    
    return signal_map


def get_signal_network(model) -> Dict[str, List[str]]:
    """Get mapping of signal places to transitions that sense them.
    
    Returns the quorum sensing network structure showing which transitions
    respond to which environmental signals.
    
    Args:
        model: Model instance
    
    Returns:
        dict: {"signal_place_id": ["transition_id1", "transition_id2", ...], ...}
    """
    network = {}
    
    if not hasattr(model, 'transitions'):
        return network
    
    transitions_iter = (model.transitions.values() if isinstance(model.transitions, dict)
                       else model.transitions)
    
    for transition in transitions_iter:
        if hasattr(transition, 'signal_places'):
            for signal_id in transition.signal_places:
                if signal_id not in network:
                    network[signal_id] = []
                network[signal_id].append(transition.id)
    
    return network


def classify_quorum_sensing_modules(model) -> List[Dict]:
    """Detect quorum sensing modules in model.
    
    A QS module consists of:
    - Signal place (e.g., AHL)
    - Producer transitions (output arc to signal)
    - Sensor transitions (signal in Ψ)
    
    Args:
        model: Model instance
    
    Returns:
        list: [{"signal_place": id, "producers": [t_ids], "sensors": [t_ids], "type": str}, ...]
    """
    modules = []
    signal_net = get_signal_network(model)
    
    for signal_id, sensor_transitions in signal_net.items():
        # Find producer transitions (have output arc to signal place)
        producers = []
        
        if hasattr(model, 'arcs'):
            arcs_iter = (model.arcs.values() if isinstance(model.arcs, dict)
                        else model.arcs)
            
            for arc in arcs_iter:
                if hasattr(arc, 'target') and arc.target == signal_id:
                    if hasattr(arc, 'source'):
                        producers.append(arc.source)
        
        # Classify module type
        module_type = "unknown"
        if len(producers) > 0 and len(sensor_transitions) > 0:
            # Check if autocrine (same producers and sensors)
            if set(producers) == set(sensor_transitions):
                module_type = "autocrine"
            else:
                module_type = "paracrine"
        elif len(producers) == 0:
            module_type = "external_signal"
        
        module = {
            "signal_place": signal_id,
            "producer_transitions": producers,
            "sensor_transitions": sensor_transitions,
            "module_type": module_type
        }
        
        modules.append(module)
    
    return modules


def mark_signal_places_in_model(model):
    """Mark places as signal places based on detected quorum sensing.
    
    This function:
    1. Detects signal places for all transitions
    2. Marks those places with is_signal_place = True
    3. Enables hexagon rendering in GUI
    
    This should be called after loading a model or when signal place
    detection is triggered by the user.
    
    Args:
        model: Model instance with places and transitions
    
    Returns:
        set: Set of place IDs marked as signal places
    """
    # First detect signal places for all transitions
    signal_map = detect_and_annotate_signal_places(model)
    
    # Collect all unique signal place IDs
    all_signal_places = set()
    for signal_places in signal_map.values():
        all_signal_places.update(signal_places)
    
    # Mark places in model
    if hasattr(model, 'places'):
        places_iter = (model.places.values() if isinstance(model.places, dict)
                      else model.places)
        
        for place in places_iter:
            if hasattr(place, 'id') and place.id in all_signal_places:
                place.is_signal_place = True
    
    logger = logging.getLogger(__name__)
    if all_signal_places:
        logger.info(
            f"Marked {len(all_signal_places)} place(s) as signal places (Ψ): {all_signal_places}"
        )
    
    return all_signal_places
