"""Sparse Incidence Matrix Implementation.

This module provides a memory-efficient sparse matrix implementation
using dictionaries to store only non-zero entries.

Suitable for:
- Large Petri nets (hundreds to thousands of places/transitions)
- Sparse connectivity (few arcs relative to P×T)
- Memory-constrained environments

Time Complexity:
- build(): O(A) where A = number of arcs
- get_*(): O(1) dictionary lookup
- fire(): O(k) where k = number of arcs connected to transition
"""

from typing import Dict, List, Tuple, Optional
from .base import IncidenceMatrix


class SparseIncidenceMatrix(IncidenceMatrix):
    """Sparse incidence matrix using dictionary storage.
    
    Stores only non-zero entries as (transition_id, place_id) -> weight.
    Memory efficient for large, sparse Petri nets.
    
    Attributes:
        F_minus_dict: Sparse F⁻ matrix {(t_id, p_id): weight}
        F_plus_dict: Sparse F⁺ matrix {(t_id, p_id): weight}
        C_dict: Sparse C matrix {(t_id, p_id): weight}
    """
    
    def __init__(self, document=None):
        """Initialize sparse incidence matrix.
        
        Args:
            document: DocumentModel containing places, transitions, and arcs
        """
        super().__init__(document)
        
        # Sparse storage: (transition_id, place_id) -> weight
        self.F_minus_dict: Dict[Tuple[int, int], int] = {}
        self.F_plus_dict: Dict[Tuple[int, int], int] = {}
        self.C_dict: Dict[Tuple[int, int], int] = {}
    
    def build(self):
        """Build sparse incidence matrix from document.
        
        Extracts places, transitions, and arcs from document and constructs
        the three matrices: F⁻ (input), F⁺ (output), and C (incidence).
        
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
        
        # Clear matrices
        self.F_minus_dict.clear()
        self.F_plus_dict.clear()
        self.C_dict.clear()
        
        # Build matrices from arcs
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
                key = (trans_id, place_id)
                self.F_minus_dict[key] = weight
                self.C_dict[key] = self.C_dict.get(key, 0) - weight
                
            elif not source_is_place and not target_is_transition:
                # Transition → Place (output arc, F⁺)
                trans_id = arc.source.id
                place_id = arc.target.id
                key = (trans_id, place_id)
                self.F_plus_dict[key] = weight
                self.C_dict[key] = self.C_dict.get(key, 0) + weight
            else:
                # Invalid arc (should be caught by Arc constructor validation)
                raise ValueError(
                    f"Invalid arc: {type(arc.source).__name__} → {type(arc.target).__name__}. "
                    f"Expected Place↔Transition connection."
                )
        
        self._built = True
    
    def get_input_weights(self, transition_id: int, place_id: int) -> int:
        """Get F⁻[t,p] - tokens consumed from place by transition.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of input arc (0 if no arc)
        """
        return self.F_minus_dict.get((transition_id, place_id), 0)
    
    def get_output_weights(self, transition_id: int, place_id: int) -> int:
        """Get F⁺[t,p] - tokens produced in place by transition.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of output arc (0 if no arc)
        """
        return self.F_plus_dict.get((transition_id, place_id), 0)
    
    def get_incidence(self, transition_id: int, place_id: int) -> int:
        """Get C[t,p] - net token change when transition fires.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Net token change (positive = production, negative = consumption)
        """
        return self.C_dict.get((transition_id, place_id), 0)
    
    def get_input_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all input arcs for a transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples
        """
        arcs = []
        for (t_id, p_id), weight in self.F_minus_dict.items():
            if t_id == transition_id:
                arcs.append((p_id, weight))
        return arcs
    
    def get_output_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all output arcs for a transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples
        """
        arcs = []
        for (t_id, p_id), weight in self.F_plus_dict.items():
            if t_id == transition_id:
                arcs.append((p_id, weight))
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
        input_arcs = self.get_input_arcs(transition_id)
        
        for place_id, required_tokens in input_arcs:
            current_tokens = marking.get(place_id, 0)
            if current_tokens < required_tokens:
                return False
        
        return True
    
    def fire(self, transition_id: int, marking: Dict[int, int]) -> Dict[int, int]:
        """Fire transition and compute new marking.
        
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
        
        # Copy marking
        new_marking = marking.copy()
        
        # Apply incidence: M' = M + C·σ
        # For each place affected by this transition
        for (t_id, p_id), net_change in self.C_dict.items():
            if t_id == transition_id:
                current = new_marking.get(p_id, 0)
                new_marking[p_id] = current + net_change
        
        return new_marking
    
    def get_nonzero_count(self) -> Dict[str, int]:
        """Get count of non-zero entries in each matrix.
        
        Returns:
            Dictionary with non-zero counts for each matrix
        """
        return {
            'F_minus': len(self.F_minus_dict),
            'F_plus': len(self.F_plus_dict),
            'C': len(self.C_dict),
        }
    
    def get_sparsity(self) -> float:
        """Get sparsity ratio (fraction of zero entries).
        
        Returns:
            Sparsity ratio between 0 and 1 (1 = completely sparse)
        """
        if not self._built:
            return 0.0
        
        total_entries = len(self.transitions) * len(self.places)
        if total_entries == 0:
            return 0.0
        
        nonzero = len(self.C_dict)
        return 1.0 - (nonzero / total_entries)
