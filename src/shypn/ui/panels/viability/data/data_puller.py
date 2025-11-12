"""Data puller for on-demand KB and simulation data.

This module pulls data from the knowledge base and simulation
on-demand, without any reactive observers or automatic updates.
"""
from typing import Optional, Set, List, Dict, Any
from dataclasses import dataclass


@dataclass
class SimulationSnapshot:
    """Snapshot of simulation state at a point in time."""
    time: float
    place_tokens: Dict[str, float]  # place_id -> token count
    transition_firings: Dict[str, int]  # transition_id -> fire count
    arc_flows: Dict[str, float]  # arc_id -> flow amount


class DataPuller:
    """Pull data from KB and simulation on-demand."""
    
    def __init__(self, kb, simulation=None):
        """Initialize data puller.
        
        Args:
            kb: Knowledge base instance
            simulation: Optional simulation instance
        """
        self.kb = kb
        self.simulation = simulation
    
    def get_transition(self, transition_id: str):
        """Get transition by ID.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Transition object or None
        """
        return self.kb.transitions.get(transition_id)
    
    def get_place(self, place_id: str):
        """Get place by ID.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Place object or None
        """
        return self.kb.places.get(place_id)
    
    def get_arc(self, arc_id: str):
        """Get arc by ID.
        
        Args:
            arc_id: Arc identifier
            
        Returns:
            Arc object or None
        """
        return self.kb.arcs.get(arc_id)
    
    def get_input_arcs(self, transition_id: str) -> List:
        """Get all input arcs for a transition.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            List of input arc objects
        """
        transition = self.get_transition(transition_id)
        if not transition:
            return []
        
        return [
            self.kb.arcs[arc_id]
            for arc_id in transition.inputs
            if arc_id in self.kb.arcs
        ]
    
    def get_output_arcs(self, transition_id: str) -> List:
        """Get all output arcs for a transition.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            List of output arc objects
        """
        transition = self.get_transition(transition_id)
        if not transition:
            return []
        
        return [
            self.kb.arcs[arc_id]
            for arc_id in transition.outputs
            if arc_id in self.kb.arcs
        ]
    
    def get_place_inputs(self, place_id: str) -> List:
        """Get all arcs that produce tokens in a place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            List of input arc objects
        """
        place = self.get_place(place_id)
        if not place:
            return []
        
        return [
            self.kb.arcs[arc_id]
            for arc_id in place.inputs
            if arc_id in self.kb.arcs
        ]
    
    def get_place_outputs(self, place_id: str) -> List:
        """Get all arcs that consume tokens from a place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            List of output arc objects
        """
        place = self.get_place(place_id)
        if not place:
            return []
        
        return [
            self.kb.arcs[arc_id]
            for arc_id in place.outputs
            if arc_id in self.kb.arcs
        ]
    
    def get_connected_transitions(self, place_id: str) -> Set[str]:
        """Get all transitions connected to a place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Set of transition IDs
        """
        transitions = set()
        
        # Get transitions that produce tokens in this place
        for arc in self.get_place_inputs(place_id):
            if hasattr(arc, 'source') and arc.source in self.kb.transitions:
                transitions.add(arc.source)
        
        # Get transitions that consume tokens from this place
        for arc in self.get_place_outputs(place_id):
            if hasattr(arc, 'target') and arc.target in self.kb.transitions:
                transitions.add(arc.target)
        
        return transitions
    
    def get_connected_places(self, transition_id: str) -> Set[str]:
        """Get all places connected to a transition.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Set of place IDs
        """
        places = set()
        
        # Get input places
        for arc in self.get_input_arcs(transition_id):
            if hasattr(arc, 'source') and arc.source in self.kb.places:
                places.add(arc.source)
        
        # Get output places
        for arc in self.get_output_arcs(transition_id):
            if hasattr(arc, 'target') and arc.target in self.kb.places:
                places.add(arc.target)
        
        return places
    
    def get_all_transitions(self) -> List[str]:
        """Get all transition IDs.
        
        Returns:
            List of transition IDs
        """
        return list(self.kb.transitions.keys())
    
    def get_all_places(self) -> List[str]:
        """Get all place IDs.
        
        Returns:
            List of place IDs
        """
        return list(self.kb.places.keys())
    
    def get_all_arcs(self) -> List[str]:
        """Get all arc IDs.
        
        Returns:
            List of arc IDs
        """
        return list(self.kb.arcs.keys())
    
    def has_simulation(self) -> bool:
        """Check if simulation is available.
        
        Returns:
            True if simulation instance exists
        """
        return self.simulation is not None
    
    def get_current_tokens(self, place_id: str) -> Optional[float]:
        """Get current token count in a place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Token count or None if simulation unavailable
        """
        if not self.has_simulation():
            return None
        
        # Try to get from simulation state
        if hasattr(self.simulation, 'state') and hasattr(self.simulation.state, 'marking'):
            return self.simulation.state.marking.get(place_id, 0.0)
        
        return None
    
    def get_firing_count(self, transition_id: str) -> Optional[int]:
        """Get number of times a transition has fired.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Fire count or None if simulation unavailable
        """
        if not self.has_simulation():
            return None
        
        # Try to get from simulation statistics
        if hasattr(self.simulation, 'statistics'):
            firings = getattr(self.simulation.statistics, 'firings', {})
            return firings.get(transition_id, 0)
        
        return None
    
    def get_simulation_time(self) -> Optional[float]:
        """Get current simulation time.
        
        Returns:
            Current time or None if simulation unavailable
        """
        if not self.has_simulation():
            return None
        
        if hasattr(self.simulation, 'current_time'):
            return self.simulation.current_time
        
        if hasattr(self.simulation, 'state') and hasattr(self.simulation.state, 'time'):
            return self.simulation.state.time
        
        return None
    
    def take_snapshot(self) -> Optional[SimulationSnapshot]:
        """Take snapshot of current simulation state.
        
        Returns:
            SimulationSnapshot or None if simulation unavailable
        """
        if not self.has_simulation():
            return None
        
        current_time = self.get_simulation_time() or 0.0
        
        # Collect place tokens
        place_tokens = {}
        for place_id in self.get_all_places():
            tokens = self.get_current_tokens(place_id)
            if tokens is not None:
                place_tokens[place_id] = tokens
        
        # Collect transition firings
        transition_firings = {}
        for transition_id in self.get_all_transitions():
            firings = self.get_firing_count(transition_id)
            if firings is not None:
                transition_firings[transition_id] = firings
        
        # For now, arc flows are not tracked
        arc_flows = {}
        
        return SimulationSnapshot(
            time=current_time,
            place_tokens=place_tokens,
            transition_firings=transition_firings,
            arc_flows=arc_flows
        )
    
    def get_transition_rate(self, transition_id: str) -> Optional[float]:
        """Get transition rate.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Rate value or None if not found
        """
        transition = self.get_transition(transition_id)
        if not transition:
            return None
        
        return getattr(transition, 'rate', None)
    
    def get_arc_weight(self, arc_id: str) -> Optional[float]:
        """Get arc weight.
        
        Args:
            arc_id: Arc identifier
            
        Returns:
            Weight value or None if not found
        """
        arc = self.get_arc(arc_id)
        if not arc:
            return None
        
        return getattr(arc, 'weight', 1.0)
    
    def get_compound_mapping(self, place_id: str) -> Optional[str]:
        """Get KEGG compound ID for a place.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Compound ID or None
        """
        place = self.get_place(place_id)
        if not place:
            return None
        
        return getattr(place, 'compound_id', None)
    
    def get_reaction_mapping(self, transition_id: str) -> Optional[str]:
        """Get KEGG reaction ID for a transition.
        
        Args:
            transition_id: Transition identifier
            
        Returns:
            Reaction ID or None
        """
        transition = self.get_transition(transition_id)
        if not transition:
            return None
        
        return getattr(transition, 'reaction_id', None)
