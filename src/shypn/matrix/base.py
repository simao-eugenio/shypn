"""Base class for Petri Net Incidence Matrix.

This module defines the abstract interface for incidence matrix implementations.
All concrete implementations must inherit from IncidenceMatrix.

Petri Net Theory:
    A Petri net is defined as PN = (P, T, F, W, M₀) where:
    - P: Set of places
    - T: Set of transitions
    - F: Flow relation F ⊆ (P × T) ∪ (T × P)
    - W: Weight function W: F → ℕ⁺
    - M₀: Initial marking M₀: P → ℕ

Incidence Matrix:
    The incidence matrix C is defined as:
    C = F⁺ - F⁻
    
    Where:
    - F⁺[t,p] = weight of arc from transition t to place p (output)
    - F⁻[t,p] = weight of arc from place p to transition t (input)
    - C[t,p] = net token change in place p when transition t fires
    
    State Equation:
    M' = M + C·σ
    where σ is the firing vector (which transitions fire and how many times)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Set
import numpy as np


class IncidenceMatrix(ABC):
    """Abstract base class for Petri Net incidence matrix.
    
    This class defines the interface for incidence matrix implementations.
    Subclasses must implement matrix construction and query methods.
    
    Attributes:
        document: DocumentModel containing the Petri net
        places: Ordered list of places
        transitions: Ordered list of transitions
        place_index: Mapping from place ID to matrix row index
        transition_index: Mapping from transition ID to matrix column index
    """
    
    def __init__(self, document=None):
        """Initialize incidence matrix.
        
        Args:
            document: DocumentModel containing places, transitions, and arcs
        """
        self.document = document
        self.places: List = []
        self.transitions: List = []
        self.place_index: Dict[int, int] = {}
        self.transition_index: Dict[int, int] = {}
        
        # Matrices (to be initialized by subclasses)
        self._F_minus = None  # Input matrix F⁻ (consumption)
        self._F_plus = None   # Output matrix F⁺ (production)
        self._C = None        # Incidence matrix C = F⁺ - F⁻
        
        self._built = False
    
    @abstractmethod
    def build(self):
        """Build the incidence matrix from document.
        
        This method must:
        1. Extract places and transitions from document
        2. Create index mappings
        3. Build F⁻ (input) matrix
        4. Build F⁺ (output) matrix
        5. Compute C = F⁺ - F⁻
        
        Raises:
            ValueError: If document is None or invalid
        """
        pass
    
    @abstractmethod
    def get_input_weights(self, transition_id: int, place_id: int) -> int:
        """Get F⁻[t,p] - tokens consumed from place p by transition t.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of arc from place to transition (0 if no arc)
        """
        pass
    
    @abstractmethod
    def get_output_weights(self, transition_id: int, place_id: int) -> int:
        """Get F⁺[t,p] - tokens produced in place p by transition t.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of arc from transition to place (0 if no arc)
        """
        pass
    
    @abstractmethod
    def get_incidence(self, transition_id: int, place_id: int) -> int:
        """Get C[t,p] - net token change in place p when transition t fires.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Net token change (positive = production, negative = consumption)
        """
        pass
    
    @abstractmethod
    def get_input_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all input arcs for a transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples for all input arcs
        """
        pass
    
    @abstractmethod
    def get_output_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all output arcs for a transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples for all output arcs
        """
        pass
    
    @abstractmethod
    def is_enabled(self, transition_id: int, marking: Dict[int, int]) -> bool:
        """Check if transition is enabled under given marking.
        
        A transition is enabled if all input places have sufficient tokens.
        
        Args:
            transition_id: Transition ID
            marking: Current marking (place_id -> token_count)
            
        Returns:
            True if transition is enabled, False otherwise
        """
        pass
    
    @abstractmethod
    def fire(self, transition_id: int, marking: Dict[int, int]) -> Dict[int, int]:
        """Fire a transition and compute new marking.
        
        Implements the state equation: M' = M + C·σ (where σ[t] = 1)
        
        Args:
            transition_id: Transition ID to fire
            marking: Current marking (place_id -> token_count)
            
        Returns:
            New marking after firing
            
        Raises:
            ValueError: If transition is not enabled
        """
        pass
    
    def get_marking_vector(self, marking: Dict[int, int]) -> np.ndarray:
        """Convert marking dict to vector.
        
        Args:
            marking: Marking as dict (place_id -> token_count)
            
        Returns:
            Marking as numpy vector (ordered by place_index)
        """
        vector = np.zeros(len(self.places), dtype=int)
        for place_id, tokens in marking.items():
            if place_id in self.place_index:
                idx = self.place_index[place_id]
                vector[idx] = tokens
        return vector
    
    def get_marking_dict(self, vector: np.ndarray) -> Dict[int, int]:
        """Convert marking vector to dict.
        
        Args:
            vector: Marking as numpy vector
            
        Returns:
            Marking as dict (place_id -> token_count)
        """
        marking = {}
        for place in self.places:
            idx = self.place_index[place.id]
            marking[place.id] = int(vector[idx])
        return marking
    
    def validate_bipartite(self) -> Tuple[bool, List[str]]:
        """Validate that the Petri net satisfies bipartite property.
        
        Checks that:
        1. All arcs connect Place↔Transition only
        2. No Place→Place arcs exist
        3. No Transition→Transition arcs exist
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        if not self._built:
            return False, ["Matrix not built yet"]
        
        errors = []
        
        # Check F⁻: All arcs should be Place → Transition
        for t_idx, transition in enumerate(self.transitions):
            input_arcs = self.get_input_arcs(transition.id)
            for place_id, weight in input_arcs:
                if weight > 0:
                    place = self._get_place_by_id(place_id)
                    if not place:
                        errors.append(f"Input arc from unknown place {place_id} to transition {transition.name}")
        
        # Check F⁺: All arcs should be Transition → Place
        for t_idx, transition in enumerate(self.transitions):
            output_arcs = self.get_output_arcs(transition.id)
            for place_id, weight in output_arcs:
                if weight > 0:
                    place = self._get_place_by_id(place_id)
                    if not place:
                        errors.append(f"Output arc from transition {transition.name} to unknown place {place_id}")
        
        return len(errors) == 0, errors
    
    def _get_place_by_id(self, place_id: int):
        """Get place object by ID."""
        for place in self.places:
            if place.id == place_id:
                return place
        return None
    
    def _get_transition_by_id(self, transition_id: int):
        """Get transition object by ID."""
        for transition in self.transitions:
            if transition.id == transition_id:
                return transition
        return None
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get matrix dimensions.
        
        Returns:
            Tuple of (num_transitions, num_places)
        """
        return len(self.transitions), len(self.places)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get matrix statistics.
        
        Returns:
            Dictionary with matrix statistics
        """
        if not self._built:
            return {
                'built': False,
                'places': 0,
                'transitions': 0,
                'arcs': 0,
            }
        
        # Count non-zero entries in matrices
        input_arcs = sum(1 for t in self.transitions for p, w in self.get_input_arcs(t.id) if w > 0)
        output_arcs = sum(1 for t in self.transitions for p, w in self.get_output_arcs(t.id) if w > 0)
        
        return {
            'built': True,
            'places': len(self.places),
            'transitions': len(self.transitions),
            'input_arcs': input_arcs,
            'output_arcs': output_arcs,
            'total_arcs': input_arcs + output_arcs,
        }
    
    def __repr__(self) -> str:
        """String representation of matrix."""
        stats = self.get_statistics()
        if not stats['built']:
            return f"<{self.__class__.__name__}(not built)>"
        
        return (f"<{self.__class__.__name__}("
                f"P={stats['places']}, "
                f"T={stats['transitions']}, "
                f"arcs={stats['total_arcs']})>")
