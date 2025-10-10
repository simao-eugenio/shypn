"""Matrix Manager - Integration layer for incidence matrix in simulation.

This module provides integration between the incidence matrix module
and the existing ModelCanvasManager/SimulationController architecture.

The MatrixManager:
- Maintains incidence matrix synchronized with document model
- Provides matrix-based queries for simulation
- Offers validation and structural analysis
- Bridges between list-based and matrix-based representations

Usage:
    # In ModelCanvasManager or SimulationController
    matrix_manager = MatrixManager(canvas_manager.document)
    
    # Query matrix
    if matrix_manager.is_enabled(transition_id, current_marking):
        new_marking = matrix_manager.fire(transition_id, current_marking)
"""

from typing import Dict, List, Tuple, Optional
import logging

from shypn.matrix.loader import load_matrix
from shypn.matrix.base import IncidenceMatrix


logger = logging.getLogger(__name__)


class MatrixManager:
    """Manages incidence matrix integration with simulation system.
    
    This class acts as a bridge between the incidence matrix module
    and the existing canvas/simulation architecture.
    
    Attributes:
        matrix: IncidenceMatrix instance (sparse or dense)
        document: DocumentModel reference
        auto_rebuild: If True, rebuilds matrix when document changes
    """
    
    def __init__(self, document=None, implementation='auto', auto_rebuild=True):
        """Initialize matrix manager.
        
        Args:
            document: DocumentModel containing Petri net
            implementation: 'auto', 'sparse', or 'dense'
            auto_rebuild: Automatically rebuild on document changes
        """
        self.document = document
        self.implementation = implementation
        self.auto_rebuild = auto_rebuild
        self.matrix: Optional[IncidenceMatrix] = None
        self._last_build_hash = None
        
        if document is not None:
            self.build()
    
    def build(self, force=False):
        """Build or rebuild the incidence matrix.
        
        Args:
            force: Force rebuild even if document hasn't changed
            
        Returns:
            bool: True if matrix was (re)built, False if skipped
        """
        if self.document is None:
            logger.warning("Cannot build matrix: no document set")
            return False
        
        # Check if rebuild needed
        current_hash = self._compute_document_hash()
        if not force and current_hash == self._last_build_hash:
            logger.debug("Matrix build skipped: document unchanged")
            return False
        
        try:
            # Build matrix
            self.matrix = load_matrix(
                self.document,
                implementation=self.implementation,
                auto_build=True
            )
            
            self._last_build_hash = current_hash
            
            # Log statistics
            stats = self.matrix.get_statistics()
            logger.info(f"Matrix built: {stats['places']} places, "
                       f"{stats['transitions']} transitions, "
                       f"{stats['total_arcs']} arcs")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to build matrix: {e}")
            self.matrix = None
            return False
    
    def _compute_document_hash(self) -> int:
        """Compute hash of document structure for change detection.
        
        Returns:
            Hash value representing document structure
        """
        if self.document is None:
            return 0
        
        # Simple hash based on counts and IDs
        place_ids = tuple(sorted(p.id for p in self.document.places))
        trans_ids = tuple(sorted(t.id for t in self.document.transitions))
        arc_ids = tuple(sorted(a.id for a in self.document.arcs))
        
        return hash((place_ids, trans_ids, arc_ids))
    
    def set_document(self, document):
        """Set document and rebuild matrix.
        
        Args:
            document: New DocumentModel
        """
        self.document = document
        self._last_build_hash = None
        self.build()
    
    def invalidate(self):
        """Invalidate matrix (force rebuild on next use)."""
        self._last_build_hash = None
    
    def ensure_built(self):
        """Ensure matrix is built (build if necessary)."""
        if self.matrix is None or (self.auto_rebuild and self._last_build_hash != self._compute_document_hash()):
            self.build()
    
    # ========== Matrix Query Methods (delegation) ==========
    
    def get_input_weights(self, transition_id: int, place_id: int) -> int:
        """Get tokens consumed from place by transition.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of input arc (0 if no arc)
        """
        self.ensure_built()
        if self.matrix is None:
            return 0
        return self.matrix.get_input_weights(transition_id, place_id)
    
    def get_output_weights(self, transition_id: int, place_id: int) -> int:
        """Get tokens produced in place by transition.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Weight of output arc (0 if no arc)
        """
        self.ensure_built()
        if self.matrix is None:
            return 0
        return self.matrix.get_output_weights(transition_id, place_id)
    
    def get_incidence(self, transition_id: int, place_id: int) -> int:
        """Get net token change when transition fires.
        
        Args:
            transition_id: Transition ID
            place_id: Place ID
            
        Returns:
            Net token change
        """
        self.ensure_built()
        if self.matrix is None:
            return 0
        return self.matrix.get_incidence(transition_id, place_id)
    
    def get_input_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all input arcs for transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples
        """
        self.ensure_built()
        if self.matrix is None:
            return []
        return self.matrix.get_input_arcs(transition_id)
    
    def get_output_arcs(self, transition_id: int) -> List[Tuple[int, int]]:
        """Get all output arcs for transition.
        
        Args:
            transition_id: Transition ID
            
        Returns:
            List of (place_id, weight) tuples
        """
        self.ensure_built()
        if self.matrix is None:
            return []
        return self.matrix.get_output_arcs(transition_id)
    
    # ========== Simulation Support Methods ==========
    
    def is_enabled(self, transition_id: int, marking: Dict[int, int]) -> bool:
        """Check if transition is enabled under given marking.
        
        This is the core enabling check using formal Petri net semantics.
        
        Args:
            transition_id: Transition ID to check
            marking: Current marking (place_id -> token_count)
            
        Returns:
            True if transition is enabled, False otherwise
        """
        self.ensure_built()
        if self.matrix is None:
            return False
        return self.matrix.is_enabled(transition_id, marking)
    
    def fire(self, transition_id: int, marking: Dict[int, int]) -> Dict[int, int]:
        """Fire transition and compute new marking.
        
        Uses state equation: M' = M + C·σ
        
        Args:
            transition_id: Transition ID to fire
            marking: Current marking (place_id -> token_count)
            
        Returns:
            New marking after firing
            
        Raises:
            ValueError: If transition not enabled
        """
        self.ensure_built()
        if self.matrix is None:
            raise ValueError("Matrix not built")
        return self.matrix.fire(transition_id, marking)
    
    def get_marking_from_document(self) -> Dict[int, int]:
        """Extract current marking from document places.
        
        Returns:
            Marking dict (place_id -> token_count)
        """
        if self.document is None:
            return {}
        
        marking = {}
        for place in self.document.places:
            marking[place.id] = place.tokens
        return marking
    
    def apply_marking_to_document(self, marking: Dict[int, int]):
        """Apply marking to document places (update token counts).
        
        Args:
            marking: Marking dict (place_id -> token_count)
        """
        if self.document is None:
            return
        
        for place in self.document.places:
            if place.id in marking:
                place.tokens = marking[place.id]
    
    def get_enabled_transitions(self, marking: Optional[Dict[int, int]] = None) -> List[int]:
        """Get list of enabled transition IDs.
        
        Args:
            marking: Marking to check (None = use document marking)
            
        Returns:
            List of enabled transition IDs
        """
        self.ensure_built()
        if self.matrix is None:
            return []
        
        if marking is None:
            marking = self.get_marking_from_document()
        
        enabled = []
        for transition in self.matrix.transitions:
            if self.matrix.is_enabled(transition.id, marking):
                enabled.append(transition.id)
        
        return enabled
    
    # ========== Validation and Analysis Methods ==========
    
    def validate_bipartite(self) -> Tuple[bool, List[str]]:
        """Validate bipartite property of Petri net.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        self.ensure_built()
        if self.matrix is None:
            return False, ["Matrix not built"]
        return self.matrix.validate_bipartite()
    
    def get_statistics(self) -> Dict[str, int]:
        """Get matrix statistics.
        
        Returns:
            Dictionary with statistics
        """
        self.ensure_built()
        if self.matrix is None:
            return {'built': False}
        return self.matrix.get_statistics()
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get matrix dimensions (transitions, places).
        
        Returns:
            Tuple of (num_transitions, num_places)
        """
        self.ensure_built()
        if self.matrix is None:
            return (0, 0)
        return self.matrix.get_dimensions()
    
    def __repr__(self) -> str:
        """String representation."""
        if self.matrix is None:
            return "<MatrixManager(not built)>"
        
        stats = self.get_statistics()
        return (f"<MatrixManager("
                f"P={stats['places']}, "
                f"T={stats['transitions']}, "
                f"arcs={stats['total_arcs']}, "
                f"impl={self.matrix.__class__.__name__})>")
