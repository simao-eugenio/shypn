"""Dense Incidence Matrix Implementation.

This module provides a dense matrix implementation using NumPy arrays.

Suitable for:
- Small to medium Petri nets (dozens of places/transitions)
- Dense connectivity (many arcs)
- When matrix operations (multiplication, linear algebra) are needed

Time Complexity:
- build(): O(P×T + A) where P=places, T=transitions, A=arcs
- get_*(): O(1) array indexing
- fire(): O(P) vector operation

Note: Uses more memory than sparse implementation but provides
faster matrix operations through NumPy vectorization.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from .base import IncidenceMatrix


class DenseIncidenceMatrix(IncidenceMatrix):
    """Dense incidence matrix using NumPy arrays.
    
    Stores matrices as 2D NumPy arrays (transitions × places).
    Efficient for small/medium nets and matrix operations.
    
    Attributes:
        F_minus: Dense F⁻ matrix (T×P numpy array)
        F_plus: Dense F⁺ matrix (T×P numpy array)
        C: Dense incidence matrix (T×P numpy array)
    """
    
    def __init__(self, document=None):
        """Initialize dense incidence matrix.
        
        Args:
            document: DocumentModel containing places, transitions, and arcs
        """
        super().__init__(document)
        
        # Dense NumPy arrays: shape = (num_transitions, num_places)
        self.F_minus: Optional[np.ndarray] = None
        self.F_plus: Optional[np.ndarray] = None
        self.C: Optional[np.ndarray] = None
    
    def build(self):
        """Build dense incidence matrix from document.
        
        Creates NumPy arrays and populates them from document arcs.
        
        Raises:
            ValueError: If document is None or has no places/transitions
        """
        if self.document is None:
            raise ValueError("Cannot build matrix: document is None")
        
        # Extract and index places
        self.places = list(self.document.places)
        if not self.places:
            raise ValueError("Cannot build matrix: document has no places")
        
        self.place_index = {place.id: idx for idx, place in enumerate(self.places)}
        
        # Extract and index transitions
        self.transitions = list(self.document.transitions)
        if not self.transitions:
            raise ValueError("Cannot build matrix: document has no transitions")
        
        self.transition_index = {trans.id: idx for idx, trans in enumerate(self.transitions)}
        
        # Initialize matrices with zeros
        num_transitions = len(self.transitions)
        num_places = len(self.places)
        
        self.F_minus = np.zeros((num_transitions, num_places), dtype=int)
        self.F_plus = np.zeros((num_transitions, num_places), dtype=int)
        
        # Populate matrices from arcs
        from shypn.netobjs import Place, Transition
        
        for arc in self.document.arcs:
            weight = arc.weight
            
            # Determine arc direction
            source_is_place = isinstance(arc.source, Place)
            target_is_transition = isinstance(arc.target, Transition)
            
            if source_is_place and target_is_transition:
                # Place → Transition (input arc, F⁻)
                place_id = arc.source.id
                trans_id = arc.target.id
                
                if place_id not in self.place_index:
                    raise ValueError(f"Place {place_id} not found in place_index")
                if trans_id not in self.transition_index:
                    raise ValueError(f"Transition {trans_id} not found in transition_index")
                
                p_idx = self.place_index[place_id]
                t_idx = self.transition_index[trans_id]
                self.F_minus[t_idx, p_idx] = weight
                
            elif not source_is_place and not target_is_transition:
                # Transition → Place (output arc, F⁺)
                trans_id = arc.source.id
                place_id = arc.target.id
                
                if place_id not in self.place_index:
                    raise ValueError(f"Place {place_id} not found in place_index")
                if trans_id not in self.transition_index:
                    raise ValueError(f"Transition {trans_id} not found in transition_index")
                
                p_idx = self.place_index[place_id]
                t_idx = self.transition_index[trans_id]
                self.F_plus[t_idx, p_idx] = weight
            else:
                # Invalid arc (should be caught by Arc constructor validation)
                raise ValueError(
                    f"Invalid arc: {type(arc.source).__name__} → {type(arc.target).__name__}. "
                    f"Expected Place↔Transition connection."
                )
        
        # Compute incidence matrix: C = F⁺ - F⁻
        self.C = self.F_plus - self.F_minus
        
        self._built = True
    
    def get_input_weights(self, transition_id: int, place_id: int) -> int:
        """Get F⁻[t,p] - tokens consumed from place by transition.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of input arc (0 if no arc)
        """
        if not self._built:
            return 0
        
        if transition_id not in self.transition_index or place_id not in self.place_index:
            return 0
        
        t_idx = self.transition_index[transition_id]
        p_idx = self.place_index[place_id]
        return int(self.F_minus[t_idx, p_idx])
    
    def get_output_weights(self, transition_id: int, place_id: int) -> int:
        """Get F⁺[t,p] - tokens produced in place by transition.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of output arc (0 if no arc)
        """
        if not self._built:
            return 0
        
        if transition_id not in self.transition_index or place_id not in self.place_index:
            return 0
        
        t_idx = self.transition_index[transition_id]
        p_idx = self.place_index[place_id]
        return int(self.F_plus[t_idx, p_idx])
    
    def get_incidence(self, transition_id: int, place_id: int) -> int:
        """Get C[t,p] - net token change when transition fires.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Net token change (positive = production, negative = consumption)
        """
        if not self._built:
            return 0
        
        if transition_id not in self.transition_index or place_id not in self.place_index:
            return 0
        
        t_idx = self.transition_index[transition_id]
        p_idx = self.place_index[place_id]
        return int(self.C[t_idx, p_idx])
    
    def get_input_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all input arcs for a transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples
        """
        if not self._built or transition_id not in self.transition_index:
            return []
        
        t_idx = self.transition_index[transition_id]
        arcs = []
        
        for place in self.places:
            p_idx = self.place_index[place.id]
            weight = int(self.F_minus[t_idx, p_idx])
            if weight > 0:
                arcs.append((place.id, weight))
        
        return arcs
    
    def get_output_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all output arcs for a transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples
        """
        if not self._built or transition_id not in self.transition_index:
            return []
        
        t_idx = self.transition_index[transition_id]
        arcs = []
        
        for place in self.places:
            p_idx = self.place_index[place.id]
            weight = int(self.F_plus[t_idx, p_idx])
            if weight > 0:
                arcs.append((place.id, weight))
        
        return arcs
    
    def is_enabled(self, transition_id: int, marking: Dict[int, int]) -> bool:
        """Check if transition is enabled under given marking.
        
        A transition is enabled if all input places have sufficient tokens.
        
        Args:
            transition_id: Transition ID
            marking: Current marking (place_id -> token_count)
            
        Returns:
            True if transition is enabled, False otherwise
        """
        if not self._built or transition_id not in self.transition_index:
            return False
        
        input_arcs = self.get_input_arcs(transition_id)
        
        for place_id, required_tokens in input_arcs:
            current_tokens = marking.get(place_id, 0)
            if current_tokens < required_tokens:
                return False
        
        return True
    
    def fire(self, transition_id: int, marking: Dict[int, int]) -> Dict[int, int]:
        """Fire transition and compute new marking using vectorized operation.
        
        Implements: M' = M + C·σ where σ[t] = 1
        
        Args:
            transition_id: Transition ID to fire
            marking: Current marking (place_id -> token_count)
            
        Returns:
            New marking after firing
            
        Raises:
            ValueError: If transition is not enabled
        """
        if not self.is_enabled(transition_id, marking):
            transition = self._get_transition_by_id(transition_id)
            trans_name = transition.name if transition else str(transition_id)
            raise ValueError(f"Transition {trans_name} is not enabled")
        
        # Convert marking to vector
        marking_vector = self.get_marking_vector(marking)
        
        # Get incidence row for this transition
        t_idx = self.transition_index[transition_id]
        incidence_row = self.C[t_idx, :]
        
        # Apply state equation: M' = M + C·σ
        new_marking_vector = marking_vector + incidence_row
        
        # Convert back to dict
        return self.get_marking_dict(new_marking_vector)
    
    def get_matrix_array(self, matrix_type: str = 'C') -> np.ndarray:
        """Get matrix as NumPy array.
        
        Args:
            matrix_type: 'C' for incidence, 'F-' for input, 'F+' for output
            
        Returns:
            NumPy array of requested matrix
            
        Raises:
            ValueError: If matrix type invalid or matrix not built
        """
        if not self._built:
            raise ValueError("Matrix not built yet")
        
        if matrix_type == 'C':
            return self.C.copy()
        elif matrix_type == 'F-' or matrix_type == 'F_minus':
            return self.F_minus.copy()
        elif matrix_type == 'F+' or matrix_type == 'F_plus':
            return self.F_plus.copy()
        else:
            raise ValueError(f"Invalid matrix type: {matrix_type}. Use 'C', 'F-', or 'F+'")
    
    def compute_invariants(self) -> Dict[str, List]:
        """Compute P-invariants and T-invariants.
        
        P-invariants: Non-negative integer vectors y such that y^T·C = 0
        T-invariants: Non-negative integer vectors x such that C·x = 0
        
        Returns:
            Dictionary with 'p_invariants' and 't_invariants' lists
            
        Note: This is a placeholder. Full implementation requires
        linear algebra algorithms (e.g., solving homogeneous systems).
        """
        if not self._built:
            return {'p_invariants': [], 't_invariants': []}
        
        # TODO: Implement invariant computation
        # This requires solving y^T·C = 0 and C·x = 0
        # Can use null space computation from scipy.linalg
        
        return {
            'p_invariants': [],
            't_invariants': [],
            'note': 'Invariant computation not yet implemented'
        }
